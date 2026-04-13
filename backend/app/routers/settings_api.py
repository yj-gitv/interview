from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.data_cleanup import cleanup_old_data

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    return {
        "auto_cleanup_enabled": settings.auto_cleanup_enabled,
        "auto_cleanup_days": settings.auto_cleanup_days,
        "whisper_model": settings.whisper_model,
        "audio_device_name": settings.audio_device_name,
    }


@router.post("/cleanup")
def run_cleanup(days: int = Query(default=90), db: Session = Depends(get_db)):
    result = cleanup_old_data(db, days=days)
    return result
