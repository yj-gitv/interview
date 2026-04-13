import os
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.data_cleanup import cleanup_old_data

router = APIRouter(prefix="/api/settings", tags=["settings"])

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _read_env() -> dict[str, str]:
    env = {}
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _write_env(env: dict[str, str]):
    lines = []
    for k, v in env.items():
        lines.append(f'{k}="{v}"')
    _ENV_FILE.write_text("\n".join(lines) + "\n")


def _mask_url(url: str) -> str:
    if not url:
        return ""
    if len(url) <= 20:
        return url[:6] + "***"
    return url[:20] + "***"


@router.get("")
def get_settings():
    return {
        "auto_cleanup_enabled": settings.auto_cleanup_enabled,
        "auto_cleanup_days": settings.auto_cleanup_days,
        "whisper_model": settings.whisper_model,
        "audio_device_name": settings.audio_device_name,
        "dingtalk_webhook_url": _mask_url(settings.dingtalk_webhook_url),
        "feishu_webhook_url": _mask_url(settings.feishu_webhook_url),
        "openai_base_url": settings.openai_base_url,
        "openai_api_key_set": bool(settings.openai_api_key),
    }


class WebhookUpdate(BaseModel):
    dingtalk_webhook_url: str | None = None
    feishu_webhook_url: str | None = None


@router.put("/webhooks")
def update_webhooks(body: WebhookUpdate):
    env = _read_env()

    if body.dingtalk_webhook_url is not None:
        env["INTERVIEW_DINGTALK_WEBHOOK_URL"] = body.dingtalk_webhook_url
        settings.dingtalk_webhook_url = body.dingtalk_webhook_url

    if body.feishu_webhook_url is not None:
        env["INTERVIEW_FEISHU_WEBHOOK_URL"] = body.feishu_webhook_url
        settings.feishu_webhook_url = body.feishu_webhook_url

    _write_env(env)

    return {
        "dingtalk_webhook_url": _mask_url(settings.dingtalk_webhook_url),
        "feishu_webhook_url": _mask_url(settings.feishu_webhook_url),
    }


@router.post("/cleanup")
def run_cleanup(days: int = Query(default=90), db: Session = Depends(get_db)):
    result = cleanup_old_data(db, days=days)
    return result
