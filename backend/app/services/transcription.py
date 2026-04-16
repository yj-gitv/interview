"""Speech recognition services.

- SherpaRecognizer: streaming Paraformer for real-time drafts
- SenseVoiceRecognizer: offline SenseVoice for high-accuracy finals
- SherpaPunctuation: CT-Transformer punctuation restoration
"""

import os
import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float


class SherpaRecognizer:
    """Singleton streaming recognizer for real-time drafts."""

    _instance = None

    def __init__(self, model_dir: str):
        import sherpa_onnx

        self._recognizer = sherpa_onnx.OnlineRecognizer.from_paraformer(
            encoder=os.path.join(model_dir, "encoder.int8.onnx"),
            decoder=os.path.join(model_dir, "decoder.int8.onnx"),
            tokens=os.path.join(model_dir, "tokens.txt"),
            num_threads=4,
            sample_rate=16000,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu",
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=1.5,
            rule2_min_trailing_silence=1.0,
            rule3_min_utterance_length=20,
        )
        print(f"[SherpaRecognizer] Streaming model loaded from {model_dir}", flush=True)

    @classmethod
    def get_instance(cls, model_dir: str):
        if cls._instance is None:
            cls._instance = cls(model_dir)
        return cls._instance

    def create_stream(self):
        return self._recognizer.create_stream()

    def feed_and_decode(self, stream, audio: np.ndarray, sample_rate: int = 16000):
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        stream.accept_waveform(sample_rate, audio)
        while self._recognizer.is_ready(stream):
            self._recognizer.decode_stream(stream)

    def get_text(self, stream) -> str:
        result = self._recognizer.get_result(stream)
        if isinstance(result, str):
            return result.strip()
        return getattr(result, "text", str(result)).strip()

    def is_endpoint(self, stream) -> bool:
        return self._recognizer.is_endpoint(stream)

    def reset(self, stream):
        self._recognizer.reset(stream)


class SenseVoiceRecognizer:
    """Singleton offline recognizer using SenseVoice for high-accuracy finals."""

    _instance = None

    def __init__(self, model_path: str, tokens_path: str):
        import sherpa_onnx

        self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=model_path,
            tokens=tokens_path,
            num_threads=4,
            provider="cpu",
            language="zh",
            use_itn=True,
        )
        print(f"[SenseVoiceRecognizer] Offline model loaded from {model_path}", flush=True)

    @classmethod
    def get_instance(cls, model_path: str, tokens_path: str):
        if cls._instance is None:
            cls._instance = cls(model_path, tokens_path)
        return cls._instance

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe an audio segment. CPU-bound, run in executor."""
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        stream = self._recognizer.create_stream()
        stream.accept_waveform(sample_rate, audio)
        self._recognizer.decode_stream(stream)
        result = stream.result
        if isinstance(result, str):
            return result.strip()
        return getattr(result, "text", str(result)).strip()


class SherpaPunctuation:
    """Singleton offline punctuation restorer using CT-Transformer."""

    _instance = None

    def __init__(self, model_path: str):
        import sherpa_onnx

        config = sherpa_onnx.OfflinePunctuationConfig(
            model=sherpa_onnx.OfflinePunctuationModelConfig(
                ct_transformer=model_path,
                num_threads=2,
                provider="cpu",
            ),
        )
        self._punct = sherpa_onnx.OfflinePunctuation(config)
        print(f"[SherpaPunctuation] Model loaded from {model_path}", flush=True)

    @classmethod
    def get_instance(cls, model_path: str):
        if cls._instance is None:
            cls._instance = cls(model_path)
        return cls._instance

    def add_punctuation(self, text: str) -> str:
        if not text:
            return text
        return self._punct.add_punctuation(text)
