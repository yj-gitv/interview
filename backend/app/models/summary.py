from datetime import datetime

from sqlalchemy import String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id"), unique=True
    )
    candidate_overview: Mapped[str] = mapped_column(Text, default="")
    expression_score: Mapped[float] = mapped_column(Float, default=0)
    case_richness_score: Mapped[float] = mapped_column(Float, default=0)
    depth_score: Mapped[float] = mapped_column(Float, default=0)
    self_awareness_score: Mapped[float] = mapped_column(Float, default=0)
    enthusiasm_score: Mapped[float] = mapped_column(Float, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    concerns: Mapped[str] = mapped_column(Text, default="[]")
    jd_alignment: Mapped[str] = mapped_column(Text, default="[]")
    recommendation: Mapped[str] = mapped_column(String(20), default="pending")
    recommendation_reason: Mapped[str] = mapped_column(Text, default="")
    next_steps: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    interview: Mapped["Interview"] = relationship(back_populates="summary")
