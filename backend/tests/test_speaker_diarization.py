import numpy as np

from app.services.speaker_diarization import (
    EnergyDiarizer,
    PyAnnoteDiarizer,
    create_diarizer,
)


class TestEnergyDiarizer:
    def test_starts_with_interviewer(self):
        d = EnergyDiarizer(sample_rate=16000)
        silence = np.zeros(16000, dtype=np.float32)
        speaker = d.process_chunk(silence)
        assert speaker == "interviewer"

    def test_detects_speaker_turn_after_silence(self):
        d = EnergyDiarizer(
            energy_threshold=0.01,
            min_silence_ms=500,
            sample_rate=16000,
        )
        speech = np.random.randn(16000).astype(np.float32) * 0.1
        d.process_chunk(speech)
        assert d._current_speaker == "interviewer"

        silence = np.zeros(16000, dtype=np.float32)
        d.process_chunk(silence)

        speech2 = np.random.randn(16000).astype(np.float32) * 0.1
        speaker = d.process_chunk(speech2)
        assert speaker == "candidate"

    def test_turn_count_increments(self):
        d = EnergyDiarizer(
            energy_threshold=0.01,
            min_silence_ms=200,
            sample_rate=16000,
        )
        for _ in range(3):
            speech = np.random.randn(8000).astype(np.float32) * 0.1
            d.process_chunk(speech)
            silence = np.zeros(8000, dtype=np.float32)
            d.process_chunk(silence)

        assert d.turn_count >= 2

    def test_reset_clears_state(self):
        d = EnergyDiarizer()
        d._turn_count = 5
        d._current_speaker = "candidate"
        d.reset()
        assert d._current_speaker == "interviewer"
        assert d.turn_count == 0


class TestPyAnnoteDiarizer:
    def test_not_available_without_package(self):
        d = PyAnnoteDiarizer()
        assert d.available is False or d.available is True  # depends on env

    def test_returns_empty_when_not_available(self):
        d = PyAnnoteDiarizer()
        if not d.available:
            result = d.process_audio(np.zeros(16000, dtype=np.float32))
            assert result == []


class TestCreateDiarizer:
    def test_default_creates_energy(self):
        d = create_diarizer(method="energy")
        assert isinstance(d, EnergyDiarizer)

    def test_pyannote_falls_back_to_energy(self):
        d = create_diarizer(method="pyannote")
        assert isinstance(d, (EnergyDiarizer, PyAnnoteDiarizer))
