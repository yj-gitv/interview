from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    codename: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100), default="")
    resume_file_path: Mapped[str] = mapped_column(String(500), default="")
    resume_raw_text: Mapped[str] = mapped_column(Text, default="")
    resume_sanitized_text: Mapped[str] = mapped_column(Text, default="")
    structured_info: Mapped[str] = mapped_column(Text, default="{}")
    pii_mapping: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    position: Mapped["Position"] = relationship(back_populates="candidates")
    match: Mapped["ResumeMatch | None"] = relationship(
        back_populates="candidate", uselist=False
    )
