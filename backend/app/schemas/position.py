from datetime import datetime

from pydantic import BaseModel


class PositionCreate(BaseModel):
    title: str
    department: str = ""
    jd_text: str
    core_competencies: str = ""
    preferences: str = ""


class PositionUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    jd_text: str | None = None
    core_competencies: str | None = None
    preferences: str | None = None
    status: str | None = None


class PositionResponse(BaseModel):
    id: int
    title: str
    department: str
    jd_text: str
    core_competencies: str
    preferences: str
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0

    model_config = {"from_attributes": True}
