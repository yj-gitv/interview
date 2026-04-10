from datetime import datetime

from pydantic import BaseModel


class CandidateCreate(BaseModel):
    position_id: int
    codename: str = ""


class CandidateResponse(BaseModel):
    id: int
    position_id: int
    codename: str
    resume_file_path: str
    structured_info: str
    created_at: datetime
    has_match: bool = False

    model_config = {"from_attributes": True}
