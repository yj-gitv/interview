from datetime import datetime

from sqlalchemy import Float, Text, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResumeMatch(Base):
    __tablename__ = "resume_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), unique=True
    )
    experience_score: Mapped[float] = mapped_column(Float, default=0)
    experience_note: Mapped[str] = mapped_column(Text, default="")
    industry_score: Mapped[float] = mapped_column(Float, default=0)
    industry_note: Mapped[str] = mapped_column(Text, default="")
    competency_score: Mapped[float] = mapped_column(Float, default=0)
    competency_note: Mapped[str] = mapped_column(Text, default="")
    potential_score: Mapped[float] = mapped_column(Float, default=0)
    potential_note: Mapped[str] = mapped_column(Text, default="")
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(
        String(20), default="pending"
    )
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    risks: Mapped[str] = mapped_column(Text, default="[]")
    questions: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="match")
