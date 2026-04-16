import asyncio
import dataclasses
import hashlib
import json
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal
from app.models.candidate import Candidate
from app.models.position import Position
from app.models.resume_match import ResumeMatch
from app.services.matching import MatchingService
from app.services.pii_masking import PIIMasker, extract_name_from_resume, mask_display_name
from app.services.question_gen import QuestionGenService
from app.services.resume_parser import ResumeParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


def _candidate_display_name(c: Candidate) -> str:
    if c.name:
        return f"{c.codename}（{mask_display_name(c.name)}）"
    return c.codename

def _next_codename(db: Session) -> str:
    """Generate next codename based on existing candidates in DB."""
    from sqlalchemy import func as sa_func
    count = db.query(sa_func.count(Candidate.id)).scalar() or 0
    idx = count + 1
    if idx <= 26:
        label = chr(64 + idx)
    else:
        label = str(idx)
    return f"候选人{label}"


async def _auto_score_and_generate(candidate_id: int, position_id: int) -> None:
    """Upload 后自动在后台执行评分 + 问题生成。"""
    db = SessionLocal()
    try:
        candidate = db.get(Candidate, candidate_id)
        position = db.get(Position, position_id)
        if not candidate or not position:
            return

        matching_svc = MatchingService()
        result = await matching_svc.match(
            jd_text=position.jd_text,
            resume_text=candidate.resume_sanitized_text,
            preferences=position.preferences,
        )

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
        logger.info("Auto-scored candidate %d: %.0f", candidate_id, result.overall_score)

        question_svc = QuestionGenService()
        question_set = await question_svc.generate(
            jd_text=position.jd_text,
            resume_text=candidate.resume_sanitized_text,
            match_highlights=result.highlights,
            match_risks=result.risks,
            preferences=position.preferences,
        )
        match.questions = json.dumps(
            dataclasses.asdict(question_set), ensure_ascii=False
        )
        db.commit()
        logger.info("Auto-generated questions for candidate %d", candidate_id)
    except Exception:
        logger.exception("Auto-score failed for candidate %d", candidate_id)
    finally:
        db.close()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    position_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_ext = (
        file.filename.rsplit(".", 1)[-1]
        if file.filename and "." in file.filename
        else "bin"
    )
    saved_name = f"{uuid.uuid4().hex}.{file_ext}"
    save_path = os.path.join(settings.upload_dir, saved_name)

    with open(save_path, "wb") as f:
        f.write(file.file.read())

    parser = ResumeParser()
    try:
        result = parser.parse(save_path)
    except ValueError as e:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail=str(e))

    # Dedup: check if same resume already exists for this position
    text_hash = hashlib.sha256(result.raw_text.encode()).hexdigest()
    existing = (
        db.query(Candidate)
        .filter(Candidate.position_id == position_id)
        .all()
    )
    for c in existing:
        existing_hash = hashlib.sha256(c.resume_raw_text.encode()).hexdigest()
        if existing_hash == text_hash:
            os.remove(save_path)
            return {
                "id": c.id,
                "position_id": c.position_id,
                "codename": c.codename,
                "display_name": _candidate_display_name(c),
                "resume_file_path": c.resume_file_path,
                "structured_info": c.structured_info,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "has_match": c.match is not None,
                "duplicate": True,
            }

    codename = _next_codename(db)
    real_name = extract_name_from_resume(result.raw_text, file.filename or "")
    masker = PIIMasker(codename=codename)
    known = [real_name] if real_name else None
    sanitized = masker.mask(result.raw_text, known_names=known)

    candidate = Candidate(
        position_id=position_id,
        codename=codename,
        name=real_name,
        resume_file_path=save_path,
        resume_raw_text=result.raw_text,
        resume_sanitized_text=sanitized,
        pii_mapping=json.dumps(masker.get_mapping(), ensure_ascii=False),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    asyncio.create_task(_auto_score_and_generate(candidate.id, position_id))

    return {
        "id": candidate.id,
        "position_id": candidate.position_id,
        "codename": candidate.codename,
        "display_name": _candidate_display_name(candidate),
        "resume_file_path": candidate.resume_file_path,
        "structured_info": candidate.structured_info,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "has_match": False,
    }


@router.get("")
def list_candidates(
    position_id: int = Query(...),
    db: Session = Depends(get_db),
):
    candidates = (
        db.query(Candidate)
        .filter(Candidate.position_id == position_id)
        .order_by(Candidate.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "position_id": c.position_id,
            "codename": c.codename,
            "display_name": _candidate_display_name(c),
            "resume_file_path": c.resume_file_path,
            "structured_info": c.structured_info,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "has_match": c.match is not None,
        }
        for c in candidates
    ]


@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {
        "id": candidate.id,
        "position_id": candidate.position_id,
        "codename": candidate.codename,
        "display_name": _candidate_display_name(candidate),
        "resume_file_path": candidate.resume_file_path,
        "resume_sanitized_text": candidate.resume_sanitized_text,
        "structured_info": candidate.structured_info,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "has_match": candidate.match is not None,
    }
