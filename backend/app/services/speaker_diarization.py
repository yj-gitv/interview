import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    speaker: str  # "interviewer" or "candidate"
    start: float
    end: float
    confidence: float


class VoiceprintDiarizer:
    """Two-speaker diarizer using spectral voiceprint features.

    Extracts pitch (via autocorrelation) and spectral centroid from each
    speech segment, then clusters into two speakers using online k-means
    with 2 centroids.  The first detected speaker is labeled "interviewer".
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._centroids: list[np.ndarray | None] = [None, None]
        self._counts = [0, 0]
        self._labels = ["interviewer", "candidate"]
        self._turn_count = 0

    @staticmethod
    def _spectral_centroid(frame: np.ndarray, sample_rate: int) -> float:
        magnitude = np.abs(np.fft.rfft(frame))
        freqs = np.fft.rfftfreq(len(frame), d=1.0 / sample_rate)
        total = magnitude.sum()
        if total < 1e-10:
            return 0.0
        return float(np.sum(freqs * magnitude) / total)

    @staticmethod
    def _estimate_pitch(frame: np.ndarray, sample_rate: int) -> float:
        """Estimate fundamental frequency via autocorrelation."""
        frame = frame - np.mean(frame)
        if np.max(np.abs(frame)) < 1e-6:
            return 0.0
        corr = np.correlate(frame, frame, mode="full")
        corr = corr[len(corr) // 2:]
        min_lag = sample_rate // 500  # 500 Hz upper bound
        max_lag = sample_rate // 60   # 60 Hz lower bound
        if max_lag >= len(corr):
            max_lag = len(corr) - 1
        if min_lag >= max_lag:
            return 0.0
        region = corr[min_lag:max_lag]
        if len(region) == 0:
            return 0.0
        peak = int(np.argmax(region)) + min_lag
        if peak == 0:
            return 0.0
        return float(sample_rate / peak)

    def _extract_features(self, audio: np.ndarray) -> np.ndarray:
        """Return a 3-dim feature vector: [pitch, spectral_centroid, zcr]."""
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < 1e-5 or len(audio) < self.sample_rate // 10:
            return np.array([0.0, 0.0, 0.0])

        frame_len = min(len(audio), self.sample_rate)  # up to 1 s
        mid = len(audio) // 2
        start = max(0, mid - frame_len // 2)
        frame = audio[start:start + frame_len]

        pitch = self._estimate_pitch(frame, self.sample_rate)
        centroid = self._spectral_centroid(frame, self.sample_rate)
        zcr = float(np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame)))

        return np.array([pitch / 500.0, centroid / 4000.0, zcr * 10.0])

    def identify_speaker(self, audio_slice: np.ndarray) -> str:
        """Given an audio slice for one utterance, return speaker label."""
        feat = self._extract_features(audio_slice)
        if np.linalg.norm(feat) < 1e-6:
            return self._labels[0] if self._counts[0] >= self._counts[1] else self._labels[1]

        if self._centroids[0] is None:
            self._centroids[0] = feat.copy()
            self._counts[0] = 1
            return self._labels[0]

        d0 = float(np.linalg.norm(feat - self._centroids[0]))

        if self._centroids[1] is None:
            if d0 > 0.3:
                self._centroids[1] = feat.copy()
                self._counts[1] = 1
                self._turn_count += 1
                return self._labels[1]
            else:
                self._counts[0] += 1
                self._centroids[0] += (feat - self._centroids[0]) / self._counts[0]
                return self._labels[0]

        d1 = float(np.linalg.norm(feat - self._centroids[1]))
        idx = 0 if d0 <= d1 else 1
        self._counts[idx] += 1
        lr = 1.0 / min(self._counts[idx], 50)
        self._centroids[idx] += lr * (feat - self._centroids[idx])

        if idx == 1 and (self._counts[1] == 1 or (self._turn_count > 0 and d1 < d0)):
            self._turn_count += 1

        return self._labels[idx]

    def reset(self):
        self._centroids = [None, None]
        self._counts = [0, 0]
        self._turn_count = 0

    @property
    def turn_count(self) -> int:
        return self._turn_count


# Keep old name as alias for backward compatibility
EnergyDiarizer = VoiceprintDiarizer


class PyAnnoteDiarizer:
    """Speaker diarization using pyannote-audio (optional heavy dependency).

    Requires: pip install pyannote-audio torch
    And a HuggingFace token with access to pyannote models.
    """

    def __init__(self, hf_token: str = ""):
        self._pipeline = None
        self._hf_token = hf_token
        self._available = False
        try:
            from pyannote.audio import Pipeline  # noqa: F401

            self._available = True
        except ImportError:
            logger.warning(
                "pyannote-audio not installed. Install: pip install pyannote-audio torch"
            )

    @property
    def available(self) -> bool:
        return self._available

    def _load_pipeline(self):
        if self._pipeline is not None:
            return
        from pyannote.audio import Pipeline

        self._pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self._hf_token,
        )

    def process_audio(
        self, audio: np.ndarray, sample_rate: int = 16000
    ) -> list[SpeakerSegment]:
        if not self._available:
            return []
        try:
            self._load_pipeline()
            import torch

            waveform = torch.tensor(audio).unsqueeze(0).float()
            input_data = {"waveform": waveform, "sample_rate": sample_rate}
            diarization = self._pipeline(input_data)

            segments = []
            speaker_map = {}
            idx = 0
            for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                if speaker_label not in speaker_map:
                    speaker_map[speaker_label] = (
                        "interviewer" if idx == 0 else "candidate"
                    )
                    idx += 1
                segments.append(
                    SpeakerSegment(
                        speaker=speaker_map.get(speaker_label, "candidate"),
                        start=turn.start,
                        end=turn.end,
                        confidence=0.9,
                    )
                )
            return segments
        except Exception as e:
            logger.error(f"Pyannote diarization error: {e}")
            return []


def create_diarizer(
    method: str = "energy",
    energy_threshold: float = 0.02,
    sample_rate: int = 16000,
    hf_token: str = "",
) -> VoiceprintDiarizer | PyAnnoteDiarizer:
    if method == "pyannote":
        d = PyAnnoteDiarizer(hf_token=hf_token)
        if d.available:
            return d
        logger.warning("Falling back to voiceprint-based diarization")

    return VoiceprintDiarizer(sample_rate=sample_rate)
