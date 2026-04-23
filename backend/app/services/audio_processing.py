"""Audio preprocessing, VAD, and speaker identification.

- SileroVAD: speech/silence detection via sherpa-onnx
- SpeakerIdentifier: voice embedding based speaker clustering
- AudioPreprocessor: normalization and DC offset removal
"""

import numpy as np


class SileroVAD:
    """Silero VAD wrapper using sherpa-onnx for accurate speech detection."""

    _instance = None

    def __init__(self, model_path: str, sample_rate: int = 16000):
        import sherpa_onnx

        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = model_path
        config.silero_vad.min_silence_duration = 1.0
        config.silero_vad.min_speech_duration = 0.5
        config.silero_vad.threshold = 0.45
        config.silero_vad.window_size = 512
        config.sample_rate = sample_rate
        config.num_threads = 2
        config.provider = "cpu"

        self._vad = sherpa_onnx.VoiceActivityDetector(
            config, buffer_size_in_seconds=120
        )
        self._sample_rate = sample_rate
        print(f"[SileroVAD] Model loaded from {model_path}", flush=True)

    @classmethod
    def get_instance(cls, model_path: str, sample_rate: int = 16000):
        if cls._instance is None:
            cls._instance = cls(model_path, sample_rate)
        return cls._instance

    def process(self, audio: np.ndarray) -> list[np.ndarray]:
        """Feed audio and return completed speech segments."""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        window = 512
        i = 0
        while i + window <= len(audio):
            self._vad.accept_waveform(audio[i : i + window])
            i += window

        segments = []
        while not self._vad.empty():
            seg = self._vad.front
            samples = np.array(seg.samples, dtype=np.float32)
            segments.append(samples)
            self._vad.pop()

        return segments

    def is_speech(self, audio: np.ndarray) -> bool:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > 0.005


class SpeakerIdentifier:
    """Identifies speakers using voice embeddings with online clustering.

    Maintains up to 2 speaker profiles (interviewer + candidate).
    Each new segment is compared against known profiles via cosine similarity.
    """

    def __init__(self, model_path: str, similarity_threshold: float = 0.68):
        import sherpa_onnx

        config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=model_path, num_threads=2, provider="cpu"
        )
        self._extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)
        self._threshold = similarity_threshold
        self._dim = self._extractor.dim
        self._profiles: dict[str, np.ndarray] = {}
        self._profile_counts: dict[str, int] = {}
        self._labels = ["interviewer", "candidate"]
        self._next_label_idx = 0
        print(f"[SpeakerIdentifier] Model loaded, dim={self._dim}, threshold={self._threshold}", flush=True)

    def identify(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Return speaker label for a speech segment."""
        emb = self._extract_embedding(audio, sample_rate)
        if emb is None:
            return self._labels[0] if not self._profiles else list(self._profiles.keys())[0]

        if not self._profiles:
            label = self._labels[self._next_label_idx]
            self._next_label_idx = min(self._next_label_idx + 1, len(self._labels) - 1)
            self._profiles[label] = emb
            self._profile_counts[label] = 1
            print(f"[SpeakerID] New speaker profile: {label}", flush=True)
            return label

        best_label = None
        best_sim = -1.0
        for label, profile in self._profiles.items():
            sim = self._cosine_similarity(emb, profile)
            if sim > best_sim:
                best_sim = sim
                best_label = label

        if best_sim >= self._threshold:
            count = self._profile_counts.get(best_label, 0)
            alpha = 0.1 if count < 5 else 0.2
            self._profiles[best_label] = (1 - alpha) * self._profiles[best_label] + alpha * emb
            self._profile_counts[best_label] = count + 1
            print(f"[SpeakerID] Matched {best_label} (sim={best_sim:.3f}, n={count+1})", flush=True)
            return best_label

        # New speaker ?? only if the distance is clear enough
        if len(self._profiles) < len(self._labels):
            label = self._labels[self._next_label_idx]
            self._next_label_idx = min(self._next_label_idx + 1, len(self._labels) - 1)
            self._profiles[label] = emb
            self._profile_counts[label] = 1
            print(f"[SpeakerID] New speaker profile: {label} (best_existing_sim={best_sim:.3f})", flush=True)
            return label

        # Already have max profiles, assign to closest
        print(f"[SpeakerID] Forced match {best_label} (sim={best_sim:.3f})", flush=True)
        count = self._profile_counts.get(best_label, 0)
        alpha = 0.1 if count < 5 else 0.2
        self._profiles[best_label] = (1 - alpha) * self._profiles[best_label] + alpha * emb
        self._profile_counts[best_label] = count + 1
        return best_label

    def _extract_embedding(self, audio: np.ndarray, sample_rate: int) -> np.ndarray | None:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if len(audio) < sample_rate * 0.3:
            return None
        stream = self._extractor.create_stream()
        stream.accept_waveform(sample_rate, audio)
        if not self._extractor.is_ready(stream):
            return None
        emb = np.array(self._extractor.compute(stream), dtype=np.float32)
        return emb

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm < 1e-8:
            return 0.0
        return float(dot / norm)


class SpeakerRoleResolver:
    """Resolve raw speaker cluster labels to real roles via content heuristics.

    Collects a few final transcripts, scores each cluster by how much it looks
    like an interviewer (asks questions) vs candidate (self-reference, describes
    experience), then picks the best mapping and **locks** it. After locking,
    the mapping never changes �� preventing flip-flopping.

    Works for both onsite mode (cluster labels from voice embeddings) and
    remote mode (cluster labels from audio source tags), because in both cases
    the raw label may not match the real role.
    """

    INTERVIEWER_PATTERNS = (
        "为什么", "怎么", "你的", "是否", "能否", "请问", "请介绍一下",
        "说说", "谈谈", "你觉得", "你认为", "你是怎么",
        "你有", "能不能", "说一下", "你在", "有没有", "了解一下",
        "再给我们", "详细说", "我们公司", "你平时", "你会",
    )
    CANDIDATE_PATTERNS = (
        "我觉得", "我认为", "我之前", "我做过", "我负责", "我不是",
        "我感觉", "我的项目", "我们团队", "我们公司", "我主要",
        "我是", "我的", "我会", "我可以", "我从", "我目前",
        "我当时", "我做的项目", "我用", "就是",
    )

    def __init__(self, min_segments: int = 3, force_after: int = 8):
        self._scores: dict[str, list[float]] = {}
        self._counts: dict[str, int] = {}
        self._mapping: dict[str, str] = {}
        self._locked: bool = False
        self._min_segments = min_segments
        self._force_after = force_after

    @property
    def locked(self) -> bool:
        return self._locked

    @property
    def mapping(self) -> dict[str, str]:
        return dict(self._mapping)

    def map_speaker(self, raw_label: str) -> str:
        """Translate a raw cluster label to the resolved role, if locked."""
        if self._locked:
            return self._mapping.get(raw_label, raw_label)
        return raw_label

    def observe(self, raw_label: str, text: str) -> tuple[str, dict[str, str] | None]:
        """Record a final segment. Returns (mapped_label, swap_mapping).

        swap_mapping is non-None only on the single call that locks the resolver
        AND results in at least one label changing �� signalling the caller to
        apply the swap to past transcripts and notify clients.
        """
        if self._locked:
            return self._mapping.get(raw_label, raw_label), None

        q_score = sum(1.0 for p in self.INTERVIEWER_PATTERNS if p in text)
        q_score += 1.5 if ("?" in text or "？" in text) else 0.0
        s_score = sum(1.0 for p in self.CANDIDATE_PATTERNS if p in text)
        if "我" in text:
            s_score += 0.3

        sc = self._scores.setdefault(raw_label, [0.0, 0.0])
        sc[0] += q_score
        sc[1] += s_score
        self._counts[raw_label] = self._counts.get(raw_label, 0) + 1

        total = sum(self._counts.values())
        heard_both = len(self._counts) >= 2

        if (heard_both and total >= self._min_segments) or total >= self._force_after:
            self._resolve()
            self._locked = True
            if any(k != v for k, v in self._mapping.items()):
                return self._mapping.get(raw_label, raw_label), dict(self._mapping)
            return self._mapping.get(raw_label, raw_label), None

        return raw_label, None

    def _resolve(self):
        labels = list(self._scores.keys())

        if len(labels) == 1:
            only = labels[0]
            q, s = self._scores[only]
            self._mapping[only] = "interviewer" if q >= s else "candidate"
            return

        a, b = labels[0], labels[1]
        sa, sb = self._scores[a], self._scores[b]
        opt_ab = sa[0] + sb[1]
        opt_ba = sa[1] + sb[0]
        if opt_ab >= opt_ba:
            self._mapping[a] = "interviewer"
            self._mapping[b] = "candidate"
        else:
            self._mapping[a] = "candidate"
            self._mapping[b] = "interviewer"


class AudioPreprocessor:
    """Audio normalization and cleanup."""

    @staticmethod
    def process(audio: np.ndarray) -> np.ndarray:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        audio = audio - np.mean(audio)

        peak = np.max(np.abs(audio))
        if peak > 0.001:
            audio = audio * (0.707 / peak)

        np.clip(audio, -1.0, 1.0, out=audio)

        return audio
