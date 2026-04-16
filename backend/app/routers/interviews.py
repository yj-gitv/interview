import json as json_module
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview, InterviewStatus
from app.models.candidate import Candidate
from app.models.position import Position
from app.schemas.interview import InterviewCreate, InterviewResponse
from app.services import interview_manager
from app.services.pii_masking import mask_display_name

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=InterviewResponse)
def create_interview(body: InterviewCreate, db: Session = Depends(get_db)):
    position = db.get(Position, body.position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    candidate = db.get(Candidate, body.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    interview = Interview(
        position_id=body.position_id,
        candidate_id=body.candidate_id,
        questions_json=body.questions_json,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return _to_response(interview)


@router.get("", response_model=list[InterviewResponse])
def list_interviews(
    candidate_id: int | None = Query(None),
    position_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Interview)
    if candidate_id:
        query = query.filter(Interview.candidate_id == candidate_id)
    if position_id:
        query = query.filter(Interview.position_id == position_id)
    interviews = query.order_by(Interview.created_at.desc()).all()
    return [_to_response(i) for i in interviews]


@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return _to_response(interview)


@router.post("/{interview_id}/start", response_model=InterviewResponse)
def start_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    interview.status = InterviewStatus.IN_PROGRESS
    interview.started_at = datetime.now()
    db.commit()
    db.refresh(interview)
    return _to_response(interview)


@router.post("/{interview_id}/end", response_model=InterviewResponse)
def end_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    interview.status = InterviewStatus.COMPLETED
    interview.ended_at = datetime.now()
    if interview.started_at:
        interview.duration_seconds = int(
            (interview.ended_at - interview.started_at).total_seconds()
        )
    db.commit()
    db.refresh(interview)
    return _to_response(interview)


@router.get("/{interview_id}/transcripts")
def get_transcripts(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return [
        {
            "id": t.id,
            "speaker": t.speaker,
            "sanitized_text": t.sanitized_text,
            "timestamp": t.timestamp,
            "duration": t.duration,
        }
        for t in interview.transcripts
    ]


def _candidate_display(candidate: Candidate | None) -> tuple[str, str]:
    if not candidate:
        return "", ""
    codename = candidate.codename
    if candidate.name:
        display = f"{codename}（{mask_display_name(candidate.name)}）"
    else:
        display = codename
    return codename, display


def _to_response(interview: Interview) -> dict:
    codename, display_name = _candidate_display(interview.candidate)
    return {
        "id": interview.id,
        "position_id": interview.position_id,
        "candidate_id": interview.candidate_id,
        "status": interview.status.value,
        "questions_json": interview.questions_json,
        "started_at": interview.started_at,
        "ended_at": interview.ended_at,
        "duration_seconds": interview.duration_seconds,
        "created_at": interview.created_at,
        "candidate_codename": codename,
        "candidate_display_name": display_name,
        "position_title": interview.position.title if interview.position else "",
        "has_summary": interview.summary is not None,
    }


@router.post("/{interview_id}/session")
async def create_interview_session(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    questions_raw = json_module.loads(interview.questions_json) if interview.questions_json else []
    questions = []
    if isinstance(questions_raw, dict):
        for section in ["opening", "experience_verification", "competency", "risk_probing", "culture_fit"]:
            questions.extend(questions_raw.get(section, []))
    elif isinstance(questions_raw, list):
        questions = questions_raw
    codename = interview.candidate.codename if interview.candidate else "候选人"

    await interview_manager.create_session(
        interview_id=interview_id,
        questions=questions,
        codename=codename,
    )
    return {"status": "session_created", "interview_id": interview_id}


@router.post("/{interview_id}/session/stop")
async def stop_interview_session(interview_id: int):
    await interview_manager.stop_session(interview_id)
    return {"status": "session_stopped"}


@router.get("/{interview_id}/session/status")
async def interview_session_status(interview_id: int):
    session = interview_manager.get_session(interview_id)
    if not session:
        return {"active": False}
    return {
        "active": True,
        "running": session._running,
        "current_question_index": session.current_question_index,
        "transcript_count": len(session.transcript_lines),
    }
