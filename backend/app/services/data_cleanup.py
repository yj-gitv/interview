import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.candidate import Candidate
from app.models.resume_match import ResumeMatch
from app.models.interview import Interview, InterviewStatus
from app.models.transcript import Transcript
from app.models.evaluation import Evaluation
from app.models.summary import Summary


def cleanup_old_data(db: Session, days: int | None = None) -> dict:
    cutoff_days = days if days is not None else settings.auto_cleanup_days
    cutoff = datetime.now() - timedelta(days=cutoff_days)

    old_interviews = (
        db.query(Interview)
        .filter(
            Interview.status == InterviewStatus.COMPLETED,
            Interview.ended_at < cutoff,
        )
        .all()
    )

    deleted = {
        "interviews": 0,
        "transcripts": 0,
        "evaluations": 0,
        "summaries": 0,
        "candidates": 0,
        "matches": 0,
        "files": [],
    }

    for interview in old_interviews:
        t_count = db.query(Transcript).filter(
            Transcript.interview_id == interview.id
        ).delete()
        deleted["transcripts"] += t_count

        e_count = db.query(Evaluation).filter(
            Evaluation.interview_id == interview.id
        ).delete()
        deleted["evaluations"] += e_count

        s = db.query(Summary).filter(
            Summary.interview_id == interview.id
        ).first()
        if s:
            if s.pdf_path and os.path.exists(s.pdf_path):
                try:
                    os.remove(s.pdf_path)
                    deleted["files"].append(s.pdf_path)
                except OSError:
                    pass
            db.delete(s)
            deleted["summaries"] += 1

        db.delete(interview)
        deleted["interviews"] += 1

    old_candidates = (
        db.query(Candidate)
        .filter(Candidate.created_at < cutoff)
        .all()
    )

    for candidate in old_candidates:
        has_recent_interview = (
            db.query(Interview)
            .filter(
                Interview.candidate_id == candidate.id,
                Interview.created_at >= cutoff,
            )
            .first()
        )
        if has_recent_interview:
            continue

        m_count = db.query(ResumeMatch).filter(
            ResumeMatch.candidate_id == candidate.id
        ).delete()
        deleted["matches"] += m_count

        if candidate.resume_file_path and os.path.exists(candidate.resume_file_path):
            try:
                os.remove(candidate.resume_file_path)
                deleted["files"].append(candidate.resume_file_path)
            except OSError:
                pass

        db.delete(candidate)
        deleted["candidates"] += 1

    db.commit()
    return deleted
