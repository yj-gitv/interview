import dataclasses
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.position import Position
from app.models.resume_match import ResumeMatch
from app.services.matching import MatchingService
from app.services.question_gen import QuestionGenService

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.post("/{candidate_id}/score")
async def trigger_matching(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    position = db.get(Position, candidate.position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    service = MatchingService()
    result = await service.match(
        jd_text=position.jd_text,
        resume_text=candidate.resume_sanitized_text,
        preferences=position.preferences,
    )

    existing = (
        db.query(ResumeMatch).filter(ResumeMatch.candidate_id == candidate_id).first()
    )
    if existing:
        db.delete(existing)
        db.flush()

    match = ResumeMatch(
        candidate_id=candidate_id,
        experience_score=result.experience_score,
        experience_note=result.experience_note,
        industry_score=result.industry_score,
        industry_note=result.industry_note,
        competency_score=result.competency_score,
        competency_note=result.competency_note,
        potential_score=result.potential_score,
        potential_note=result.potential_note,
        overall_score=result.overall_score,
        recommendation=result.recommendation,
        highlights=json.dumps(result.highlights, ensure_ascii=False),
        risks=json.dumps(result.risks, ensure_ascii=False),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return _match_to_dict(match)


@router.post("/{candidate_id}/questions")
async def generate_questions(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    position = db.get(Position, candidate.position_id)
    match = (
        db.query(ResumeMatch).filter(ResumeMatch.candidate_id == candidate_id).first()
    )

    highlights = json.loads(match.highlights) if match else []
    risks = json.loads(match.risks) if match else []

    service = QuestionGenService()
    question_set = await service.generate(
        jd_text=position.jd_text,
        resume_text=candidate.resume_sanitized_text,
        match_highlights=highlights,
        match_risks=risks,
        preferences=position.preferences,
    )

    questions_json = json.dumps(
        dataclasses.asdict(question_set), ensure_ascii=False
    )

    if match:
        match.questions = questions_json
        db.commit()
        db.refresh(match)

    return json.loads(questions_json)


@router.get("/{candidate_id}")
def get_match(candidate_id: int, db: Session = Depends(get_db)):
    match = (
        db.query(ResumeMatch).filter(ResumeMatch.candidate_id == candidate_id).first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _match_to_dict(match)


def _match_to_dict(match: ResumeMatch) -> dict:
    return {
        "id": match.id,
        "candidate_id": match.candidate_id,
        "experience_score": match.experience_score,
        "experience_note": match.experience_note,
        "industry_score": match.industry_score,
        "industry_note": match.industry_note,
        "competency_score": match.competency_score,
        "competency_note": match.competency_note,
        "potential_score": match.potential_score,
        "potential_note": match.potential_note,
        "overall_score": match.overall_score,
        "recommendation": match.recommendation,
        "highlights": match.highlights,
        "risks": match.risks,
        "questions": match.questions,
        "created_at": match.created_at.isoformat() if match.created_at else None,
    }
