import enum
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus), default=InterviewStatus.SCHEDULED
    )
    questions_json: Mapped[str] = mapped_column(String, default="[]")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    position: Mapped["Position"] = relationship()
    candidate: Mapped["Candidate"] = relationship()
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="interview", order_by="Transcript.timestamp"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="interview"
    )
    summary: Mapped["Summary | None"] = relationship(
        back_populates="interview", uselist=False
    )
