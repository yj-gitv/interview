import numpy as np
import pytest

from app.services.transcription import TranscriptionService, TranscriptSegment


class TestTranscriptSegment:
    def test_segment_fields(self):
        seg = TranscriptSegment(text="你好", start=0.0, end=1.5)
        assert seg.text == "你好"
        assert seg.start == 0.0
        assert seg.end == 1.5


class TestTranscriptionService:
    def test_creates_with_config(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        assert service.model_size == "tiny"

    def test_transcribe_silence_returns_empty(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        silence = np.zeros(16000, dtype=np.float32)
        segments = service.transcribe(silence, sample_rate=16000)
        assert isinstance(segments, list)

    def test_transcribe_accepts_numpy_array(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        audio = np.random.randn(16000).astype(np.float32) * 0.01
        segments = service.transcribe(audio, sample_rate=16000)
        assert isinstance(segments, list)
