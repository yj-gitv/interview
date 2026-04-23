import json
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.interview import Interview
from app.models.transcript import Transcript
from app.models.summary import Summary
from app.services.summary_gen import SummaryGenService
from app.services.pdf_export import PDFExportService
from app.services.webhook_push import push_interview_result
from app.services.pii_masking import mask_display_name

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.post("/{interview_id}/generate")
async def generate_summary(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    transcripts = (
        db.query(Transcript)
        .filter(Transcript.interview_id == interview_id)
        .order_by(Transcript.timestamp)
        .all()
    )
    transcript_text = "\n".join(
        f"{t.speaker}: {t.sanitized_text}" for t in transcripts
    )

    if not transcript_text:
        from app.services import interview_manager
        session = interview_manager.get_session(interview_id)
        if session:
            transcript_text = "\n".join(session.transcript_lines)

    jd_text = interview.position.jd_text if interview.position else ""
    resume_text = interview.candidate.resume_sanitized_text if interview.candidate else ""
    preferences = interview.position.preferences if interview.position else ""

    match_data = None
    if interview.candidate and interview.candidate.match:
        m = interview.candidate.match
        match_data = {
            "overall_score": m.overall_score,
            "highlights": json.loads(m.highlights) if m.highlights else [],
            "risks": json.loads(m.risks) if m.risks else [],
        }

    service = SummaryGenService()
    result = await service.generate(
        transcript=transcript_text or "(No transcript available)",
        jd_text=jd_text,
        resume_text=resume_text,
        match_data=match_data,
        preferences=preferences,
    )

    existing = db.query(Summary).filter(Summary.interview_id == interview_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    summary = Summary(
        interview_id=interview_id,
        candidate_overview=result.candidate_overview,
        expression_score=result.expression_score,
        case_richness_score=result.case_richness_score,
        depth_score=result.depth_score,
        self_awareness_score=result.self_awareness_score,
        enthusiasm_score=result.enthusiasm_score,
        overall_score=result.overall_score,
        highlights=json.dumps(result.highlights, ensure_ascii=False),
        concerns=json.dumps(result.concerns, ensure_ascii=False),
        jd_alignment=json.dumps(result.jd_alignment, ensure_ascii=False),
        recommendation=result.recommendation,
        recommendation_reason=result.recommendation_reason,
        next_steps=result.next_steps,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return _summary_to_dict(summary)


@router.get("/{interview_id}")
def get_summary(interview_id: int, db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(
        Summary.interview_id == interview_id
    ).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return _summary_to_dict(summary)


@router.get("/{interview_id}/pdf")
def export_pdf(interview_id: int, db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(
        Summary.interview_id == interview_id
    ).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    interview = db.get(Interview, interview_id)
    candidate = interview.candidate if interview else None
    codename = candidate.codename if candidate else "Unknown"
    display = f"{codename}（{mask_display_name(candidate.name)}）" if candidate and candidate.name else codename
    position_title = interview.position.title if interview and interview.position else "Unknown"
    interview_date = (
        interview.started_at.strftime("%Y-%m-%d") if interview and interview.started_at
        else interview.created_at.strftime("%Y-%m-%d") if interview and interview.created_at
        else "N/A"
    )
    duration_min = (interview.duration_seconds // 60) if interview else 0

    transcripts = (
        db.query(Transcript)
        .filter(Transcript.interview_id == interview_id)
        .order_by(Transcript.timestamp)
        .all()
    )
    transcript_lines = [
        {"speaker": t.speaker, "sanitized_text": t.sanitized_text, "timestamp": t.timestamp}
        for t in transcripts
    ]

    os.makedirs("./exports", exist_ok=True)
    pdf_path = f"./exports/interview_{interview_id}_summary.pdf"

    service = PDFExportService()
    service.export(
        output_path=pdf_path,
        candidate_codename=display,
        position_title=position_title,
        interview_date=interview_date,
        duration_minutes=duration_min,
        candidate_overview=summary.candidate_overview,
        scores={
            "表达清晰度": summary.expression_score,
            "案例丰富度": summary.case_richness_score,
            "思维深度": summary.depth_score,
            "自我认知": summary.self_awareness_score,
            "岗位热情": summary.enthusiasm_score,
            "综合评分": summary.overall_score,
        },
        highlights=json.loads(summary.highlights),
        concerns=json.loads(summary.concerns),
        jd_alignment=json.loads(summary.jd_alignment),
        recommendation=summary.recommendation,
        recommendation_reason=summary.recommendation_reason,
        next_steps=summary.next_steps,
        transcript_lines=transcript_lines if transcript_lines else None,
    )

    summary.pdf_path = pdf_path
    db.commit()

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{display}_{position_title}_面试总结.pdf",
    )


@router.post("/{interview_id}/push")
async def push_summary(interview_id: int, base_url: str = "", db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(
        Summary.interview_id == interview_id
    ).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    interview = db.get(Interview, interview_id)
    candidate = interview.candidate if interview else None
    codename = candidate.codename if candidate else "Unknown"
    push_name = f"{codename}（{mask_display_name(candidate.name)}）" if candidate and candidate.name else codename
    position_title = interview.position.title if interview and interview.position else "Unknown"

    summary_url = ""
    if base_url:
        summary_url = f"{base_url.rstrip('/')}/interviews/{interview_id}/summary"

    result = await push_interview_result(
        candidate_codename=push_name,
        position_title=position_title,
        recommendation=summary.recommendation,
        summary_text=summary.candidate_overview,
        summary_url=summary_url,
    )
    return {"pushed": result}


def _summary_to_dict(summary: Summary) -> dict:
    return {
        "id": summary.id,
        "interview_id": summary.interview_id,
        "candidate_overview": summary.candidate_overview,
        "expression_score": summary.expression_score,
        "case_richness_score": summary.case_richness_score,
        "depth_score": summary.depth_score,
        "self_awareness_score": summary.self_awareness_score,
        "enthusiasm_score": summary.enthusiasm_score,
        "overall_score": summary.overall_score,
        "highlights": summary.highlights,
        "concerns": summary.concerns,
        "jd_alignment": summary.jd_alignment,
        "recommendation": summary.recommendation,
        "recommendation_reason": summary.recommendation_reason,
        "next_steps": summary.next_steps,
        "pdf_path": summary.pdf_path,
        "created_at": summary.created_at.isoformat() if summary.created_at else None,
    }
