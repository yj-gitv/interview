from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float


class TranscriptionService:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model_size = model_size
        self._model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: str = "zh",
    ) -> list[TranscriptSegment]:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        if np.max(np.abs(audio)) > 1.0:
            audio = audio / 32768.0

        segments, _ = self._model.transcribe(
            audio,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        results = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                results.append(TranscriptSegment(
                    text=text, start=seg.start, end=seg.end
                ))
        return results
