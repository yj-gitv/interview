import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeakerSegment:
    speaker: str  # "interviewer" or "candidate"
    start: float
    end: float
    confidence: float


class SideDiarizer:
    """Voiceprint clustering within one audio side (mic or system).

    Extracts spectral features from each utterance and clusters into
    up to `max_speakers` using online k-means.  Returns an integer
    sub-speaker index (0, 1, 2 …).
    """

    def __init__(self, sample_rate: int = 16000, max_speakers: int = 4):
        self.sample_rate = sample_rate
        self.max_speakers = max_speakers
        self._centroids: list[np.ndarray | None] = [None] * max_speakers
        self._counts = [0] * max_speakers
        self._num_active = 0

    @staticmethod
    def _spectral_centroid(frame: np.ndarray, sr: int) -> float:
        mag = np.abs(np.fft.rfft(frame))
        freqs = np.fft.rfftfreq(len(frame), d=1.0 / sr)
        total = mag.sum()
        if total < 1e-10:
            return 0.0
        return float(np.sum(freqs * mag) / total)

    @staticmethod
    def _estimate_pitch(frame: np.ndarray, sr: int) -> float:
        frame = frame - np.mean(frame)
        if np.max(np.abs(frame)) < 1e-6:
            return 0.0
        corr = np.correlate(frame, frame, mode="full")
        corr = corr[len(corr) // 2 :]
        min_lag = sr // 500
        max_lag = min(sr // 60, len(corr) - 1)
        if min_lag >= max_lag:
            return 0.0
        region = corr[min_lag:max_lag]
        if len(region) == 0:
            return 0.0
        peak = int(np.argmax(region)) + min_lag
        return float(sr / peak) if peak > 0 else 0.0

    def _extract(self, audio: np.ndarray) -> np.ndarray:
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < 1e-5 or len(audio) < self.sample_rate // 10:
            return np.zeros(3)
        frame_len = min(len(audio), self.sample_rate)
        mid = len(audio) // 2
        start = max(0, mid - frame_len // 2)
        frame = audio[start : start + frame_len]
        pitch = self._estimate_pitch(frame, self.sample_rate)
        centroid = self._spectral_centroid(frame, self.sample_rate)
        zcr = float(np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame)))
        return np.array([pitch / 500.0, centroid / 4000.0, zcr * 10.0])

    def identify(self, audio_slice: np.ndarray) -> int:
        feat = self._extract(audio_slice)
        if np.linalg.norm(feat) < 1e-6:
            return 0

        if self._num_active == 0:
            self._centroids[0] = feat.copy()
            self._counts[0] = 1
            self._num_active = 1
            return 0

        dists = []
        for i in range(self._num_active):
            d = float(np.linalg.norm(feat - self._centroids[i]))
            dists.append(d)

        min_idx = int(np.argmin(dists))
        min_dist = dists[min_idx]

        if min_dist > 0.35 and self._num_active < self.max_speakers:
            idx = self._num_active
            self._centroids[idx] = feat.copy()
            self._counts[idx] = 1
            self._num_active += 1
            return idx

        self._counts[min_idx] += 1
        lr = 1.0 / min(self._counts[min_idx], 50)
        self._centroids[min_idx] += lr * (feat - self._centroids[min_idx])
        return min_idx


class HybridDiarizer:
    """Two-layer speaker identification.

    Layer 1 — source tag: 'interviewer' side vs 'candidate' side
    Layer 2 — voiceprint: sub-speaker within each side

    Produces labels like:
      interviewer, interviewer_2, interviewer_3 …
      candidate,   candidate_2,   candidate_3 …

    For single-mic / in-person mode (no source tag), all audio
    goes through one SideDiarizer and speakers are numbered by
    detection order: first = interviewer, second = candidate, etc.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._sides: dict[str, SideDiarizer] = {}
        self._single = SideDiarizer(sample_rate=sample_rate)
        self._single_labels = ["interviewer", "candidate", "speaker_3", "speaker_4"]

    def _get_side(self, side: str) -> SideDiarizer:
        if side not in self._sides:
            self._sides[side] = SideDiarizer(sample_rate=self.sample_rate)
        return self._sides[side]

    def identify(self, audio_slice: np.ndarray, source_tag: str | None = None) -> str:
        if source_tag and source_tag in ("interviewer", "candidate"):
            diarizer = self._get_side(source_tag)
            sub = diarizer.identify(audio_slice)
            if sub == 0:
                return source_tag
            return f"{source_tag}_{sub + 1}"

        sub = self._single.identify(audio_slice)
        if sub < len(self._single_labels):
            return self._single_labels[sub]
        return f"speaker_{sub + 1}"

    def reset(self):
        self._sides.clear()
        self._single = SideDiarizer(sample_rate=self.sample_rate)
