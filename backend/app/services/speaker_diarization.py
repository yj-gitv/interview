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


class EnergyDiarizer:
    """Lightweight speaker diarization using energy-based silence detection.

    Tracks speaker turns by detecting silence gaps between speech segments.
    Assumes a two-speaker interview scenario where speakers alternate.
    """

    def __init__(
        self,
        energy_threshold: float = 0.02,
        min_silence_ms: int = 800,
        sample_rate: int = 16000,
    ):
        self.energy_threshold = energy_threshold
        self.min_silence_samples = int(sample_rate * min_silence_ms / 1000)
        self.sample_rate = sample_rate
        self._current_speaker = "interviewer"
        self._silence_counter = 0
        self._speech_active = False
        self._turn_count = 0

    def process_chunk(self, audio: np.ndarray) -> str:
        """Process an audio chunk and return the detected speaker.

        Returns "interviewer" or "candidate" based on detected speaker turns.
        """
        frame_size = self.sample_rate // 10  # 100ms frames
        had_speech = False
        silence_frames = 0

        for i in range(0, len(audio), frame_size):
            frame = audio[i : i + frame_size]
            if len(frame) == 0:
                continue
            energy = float(np.sqrt(np.mean(frame**2)))

            if energy > self.energy_threshold:
                if not self._speech_active and self._silence_counter > self.min_silence_samples:
                    self._turn_count += 1
                    self._current_speaker = (
                        "candidate" if self._current_speaker == "interviewer" else "interviewer"
                    )
                self._speech_active = True
                self._silence_counter = 0
                had_speech = True
            else:
                self._silence_counter += len(frame)
                silence_frames += 1

        if not had_speech:
            self._speech_active = False

        return self._current_speaker

    def reset(self):
        self._current_speaker = "interviewer"
        self._silence_counter = 0
        self._speech_active = False
        self._turn_count = 0

    @property
    def turn_count(self) -> int:
        return self._turn_count


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
) -> EnergyDiarizer | PyAnnoteDiarizer:
    if method == "pyannote":
        d = PyAnnoteDiarizer(hf_token=hf_token)
        if d.available:
            return d
        logger.warning("Falling back to energy-based diarization")

    return EnergyDiarizer(
        energy_threshold=energy_threshold,
        sample_rate=sample_rate,
    )
