"""Audio preprocessing and VAD (Voice Activity Detection).

- SileroVAD: wraps sherpa-onnx VoiceActivityDetector for speech/silence detection
- AudioPreprocessor: normalization, DC offset removal, noise gate
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
        """Feed audio and return list of complete speech segments detected so far.

        Each returned segment is a numpy float32 array containing one
        utterance. Returns empty list if no complete segments yet.
        """
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
        """Quick check: does this chunk contain speech above threshold?"""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > 0.005


class AudioPreprocessor:
    """Audio normalization and cleanup."""

    @staticmethod
    def process(audio: np.ndarray) -> np.ndarray:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # DC offset removal
        audio = audio - np.mean(audio)

        # Peak normalization to -3dB (0.707) ¡ª boosts quiet mic audio
        peak = np.max(np.abs(audio))
        if peak > 0.001:
            audio = audio * (0.707 / peak)

        np.clip(audio, -1.0, 1.0, out=audio)

        return audio
