from datetime import datetime

from pydantic import BaseModel


class InterviewCreate(BaseModel):
    position_id: int
    candidate_id: int
    questions_json: str = "[]"


class InterviewResponse(BaseModel):
    id: int
    position_id: int
    candidate_id: int
    status: str
    questions_json: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    candidate_codename: str = ""
    candidate_display_name: str = ""
    position_title: str = ""
    has_summary: bool = False

    model_config = {"from_attributes": True}
