FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libsndfile1 ffmpeg libportaudio2 curl bzip2 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download streaming Paraformer model (Chinese+English, ~226MB int8)
RUN curl -sL --retry 5 --retry-delay 3 \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-paraformer-bilingual-zh-en.tar.bz2 \
    | tar xj

# Download CT-Transformer punctuation model (Chinese+English, ~63MB int8)
RUN curl -sL --retry 5 --retry-delay 3 \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/punctuation-models/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8.tar.bz2 \
    | tar xj

# Download SenseVoice offline model (Chinese+English, ~70MB int8) for high-accuracy finals
RUN curl -sL --retry 5 --retry-delay 3 \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17.tar.bz2 \
    | tar xj

# Download Silero VAD model (~2MB) for accurate speech/silence detection
RUN curl -sL --retry 5 --retry-delay 3 -o silero_vad.onnx \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx

# Download 3D-Speaker embedding model (~26MB) for speaker identification
RUN curl -sL --retry 5 --retry-delay 3 -o 3dspeaker.onnx \
    https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx

COPY . .

RUN mkdir -p data uploads exports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
