import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.resume_match import ResumeMatch
from app.models.interview import Interview
from app.models.summary import Summary
from app.services.pii_masking import mask_display_name

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


@router.get("/{position_id}")
def compare_candidates(position_id: int, db: Session = Depends(get_db)):
    candidates = (
        db.query(Candidate)
        .filter(Candidate.position_id == position_id)
        .order_by(Candidate.created_at)
        .all()
    )

    results = []
    for c in candidates:
        match = db.query(ResumeMatch).filter(
            ResumeMatch.candidate_id == c.id
        ).first()

        interview = (
            db.query(Interview)
            .filter(Interview.candidate_id == c.id)
            .order_by(Interview.created_at.desc())
            .first()
        )

        summary = None
        if interview:
            summary = db.query(Summary).filter(
                Summary.interview_id == interview.id
            ).first()

        display_name = f"{c.codename}（{mask_display_name(c.name)}）" if c.name else c.codename
        entry = {
            "candidate_id": c.id,
            "codename": c.codename,
            "display_name": display_name,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "match": None,
            "interview_summary": None,
        }

        if match:
            entry["match"] = {
                "experience_score": match.experience_score,
                "industry_score": match.industry_score,
                "competency_score": match.competency_score,
                "potential_score": match.potential_score,
                "overall_score": match.overall_score,
                "recommendation": match.recommendation,
                "highlights": json.loads(match.highlights) if match.highlights else [],
                "risks": json.loads(match.risks) if match.risks else [],
            }

        if summary:
            entry["interview_summary"] = {
                "expression_score": summary.expression_score,
                "case_richness_score": summary.case_richness_score,
                "depth_score": summary.depth_score,
                "self_awareness_score": summary.self_awareness_score,
                "enthusiasm_score": summary.enthusiasm_score,
                "overall_score": summary.overall_score,
                "recommendation": summary.recommendation,
                "highlights": json.loads(summary.highlights) if summary.highlights else [],
                "concerns": json.loads(summary.concerns) if summary.concerns else [],
            }

        results.append(entry)

    return results
