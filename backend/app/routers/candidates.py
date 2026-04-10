import json
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.candidate import Candidate
from app.models.position import Position
from app.services.pii_masking import PIIMasker
from app.services.resume_parser import ResumeParser

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

_codename_counter = 0


def _next_codename() -> str:
    global _codename_counter
    _codename_counter += 1
    return f"候选人{chr(64 + _codename_counter)}"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_resume(
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

    codename = _next_codename()
    masker = PIIMasker(codename=codename)
    sanitized = masker.mask(result.raw_text)

    candidate = Candidate(
        position_id=position_id,
        codename=codename,
        resume_file_path=save_path,
        resume_raw_text=result.raw_text,
        resume_sanitized_text=sanitized,
        pii_mapping=json.dumps(masker.get_mapping(), ensure_ascii=False),
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "id": candidate.id,
        "position_id": candidate.position_id,
        "codename": candidate.codename,
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
        "resume_file_path": candidate.resume_file_path,
        "resume_sanitized_text": candidate.resume_sanitized_text,
        "structured_info": candidate.structured_info,
        "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
        "has_match": candidate.match is not None,
    }
