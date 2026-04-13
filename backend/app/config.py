from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./interview.db"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_fast: str = "gpt-4o-mini"
    openai_model_strong: str = "gpt-4o"
    upload_dir: str = "./uploads"
    cors_origins: list[str] = ["http://localhost:5173"]
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    audio_sample_rate: int = 16000
    audio_chunk_seconds: float = 3.0
    audio_device_name: str = "BlackHole 2ch"
    auto_cleanup_enabled: bool = False
    auto_cleanup_days: int = 90
    auto_cleanup_interval_hours: int = 24
    dingtalk_webhook_url: str = ""
    feishu_webhook_url: str = ""

    model_config = {"env_prefix": "INTERVIEW_", "env_file": ".env"}


settings = Settings()
