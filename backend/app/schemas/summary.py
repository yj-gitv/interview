from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    id: int
    interview_id: int
    candidate_overview: str
    expression_score: float
    case_richness_score: float
    depth_score: float
    self_awareness_score: float
    enthusiasm_score: float
    overall_score: float
    highlights: str
    concerns: str
    jd_alignment: str
    recommendation: str
    recommendation_reason: str
    next_steps: str
    pdf_path: str
    created_at: datetime

    model_config = {"from_attributes": True}
