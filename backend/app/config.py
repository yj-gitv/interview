from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/interview.db"
    db_encryption_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_fast: str = "gpt-4o-mini"
    openai_model_strong: str = "gpt-4o"
    upload_dir: str = "./uploads"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]
    asr_model_dir: str = "/app/sherpa-onnx-streaming-paraformer-bilingual-zh-en"
    asr_offline_model: str = "/app/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/model.int8.onnx"
    asr_offline_tokens: str = "/app/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17/tokens.txt"
    punct_model_path: str = "/app/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12-int8/model.int8.onnx"
    vad_model_path: str = "/app/silero_vad.onnx"
    speaker_model_path: str = "/app/3dspeaker.onnx"
    audio_sample_rate: int = 16000
    audio_device_name: str = "BlackHole 2ch"
    diarization_enabled: bool = True
    auto_cleanup_enabled: bool = False
    auto_cleanup_days: int = 90
    auto_cleanup_interval_hours: int = 24
    dingtalk_webhook_url: str = ""
    feishu_webhook_url: str = ""

    model_config = {"env_prefix": "INTERVIEW_", "env_file": ".env"}


settings = Settings()
