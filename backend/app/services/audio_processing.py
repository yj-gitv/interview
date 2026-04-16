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

    def __init__(self, model_path: str, similarity_threshold: float = 0.55):
        import sherpa_onnx

        config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(
            model=model_path, num_threads=2, provider="cpu"
        )
        self._extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)
        self._threshold = similarity_threshold
        self._dim = self._extractor.dim
        # profiles[label] = running average embedding
        self._profiles: dict[str, np.ndarray] = {}
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
            # Update running average (exponential moving average, alpha=0.3)
            self._profiles[best_label] = 0.7 * self._profiles[best_label] + 0.3 * emb
            print(f"[SpeakerID] Matched {best_label} (sim={best_sim:.3f})", flush=True)
            return best_label

        # New speaker
        if len(self._profiles) < len(self._labels):
            label = self._labels[self._next_label_idx]
            self._next_label_idx = min(self._next_label_idx + 1, len(self._labels) - 1)
            self._profiles[label] = emb
            print(f"[SpeakerID] New speaker profile: {label} (best_existing_sim={best_sim:.3f})", flush=True)
            return label

        # Already have max profiles, assign to closest
        print(f"[SpeakerID] Forced match {best_label} (sim={best_sim:.3f})", flush=True)
        self._profiles[best_label] = 0.7 * self._profiles[best_label] + 0.3 * emb
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
