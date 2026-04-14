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
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    def _ensure_model(self):
        if self._model is None:
            self._model = WhisperModel(
                self.model_size,
                device=self._device,
                compute_type=self._compute_type,
            )

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: str = "zh",
    ) -> list[TranscriptSegment]:
        self._ensure_model()

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        if np.max(np.abs(audio)) > 1.0:
            audio = audio / 32768.0

        segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=5,
            best_of=3,
            temperature=0.0,
            condition_on_previous_text=True,
            initial_prompt="以下是一段面试对话的实时转录，使用简体中文。",
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200,
            ),
            no_speech_threshold=0.5,
            log_prob_threshold=-0.8,
        )

        results = []
        for seg in segments:
            text = seg.text.strip()
            if text and seg.no_speech_prob < 0.7:
                results.append(TranscriptSegment(
                    text=text, start=seg.start, end=seg.end
                ))
        return results
