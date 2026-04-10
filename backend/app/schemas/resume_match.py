from datetime import datetime
from pydantic import BaseModel


class MatchScoreResponse(BaseModel):
    id: int
    candidate_id: int
    experience_score: float
    experience_note: str
    industry_score: float
    industry_note: str
    competency_score: float
    competency_note: str
    potential_score: float
    potential_note: str
    overall_score: float
    recommendation: str
    highlights: str
    risks: str
    questions: str
    created_at: datetime

    model_config = {"from_attributes": True}
