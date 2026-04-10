import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd


class AudioCaptureService:
    def __init__(
        self,
        device_name: str = "BlackHole 2ch",
        sample_rate: int = 16000,
        chunk_seconds: float = 3.0,
        on_chunk: Callable[[np.ndarray], None] | None = None,
    ):
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.on_chunk = on_chunk
        self._running = False
        self._thread: threading.Thread | None = None
        self._device_id: int | None = None

    def _find_device(self) -> int | None:
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if self.device_name in d["name"] and d["max_input_channels"] > 0:
                return i
        return None

    def list_devices(self) -> list[dict]:
        devices = sd.query_devices()
        return [
            {"id": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    def start(self):
        self._device_id = self._find_device()
        if self._device_id is None:
            available = [d["name"] for d in self.list_devices()]
            raise RuntimeError(
                f"Audio device '{self.device_name}' not found. "
                f"Available input devices: {available}"
            )
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running

    def _capture_loop(self):
        chunk_size = int(self.sample_rate * self.chunk_seconds)
        try:
            with sd.InputStream(
                device=self._device_id,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_size,
            ) as stream:
                while self._running:
                    audio, _ = stream.read(chunk_size)
                    chunk = audio.flatten()
                    if self.on_chunk and np.max(np.abs(chunk)) > 0.001:
                        self.on_chunk(chunk)
        except Exception as e:
            self._running = False
            raise RuntimeError(f"Audio capture error: {e}") from e
