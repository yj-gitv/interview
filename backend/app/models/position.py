import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PositionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    department: Mapped[str] = mapped_column(String(100), default="")
    jd_text: Mapped[str] = mapped_column(Text)
    core_competencies: Mapped[str] = mapped_column(Text, default="")
    preferences: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[PositionStatus] = mapped_column(
        Enum(PositionStatus), default=PositionStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="position")
