from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    question_index: Mapped[int] = mapped_column(Integer, default=-1)
    question_text: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[str] = mapped_column(String(20), default="pending")
    ai_comment: Mapped[str] = mapped_column(Text, default="")
    interviewer_note: Mapped[str] = mapped_column(Text, default="")
    expression_score: Mapped[float] = mapped_column(Float, default=0)
    case_richness_score: Mapped[float] = mapped_column(Float, default=0)
    depth_score: Mapped[float] = mapped_column(Float, default=0)
    self_awareness_score: Mapped[float] = mapped_column(Float, default=0)
    enthusiasm_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    interview: Mapped["Interview"] = relationship(back_populates="evaluations")
