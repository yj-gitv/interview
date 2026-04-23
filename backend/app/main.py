import json
import os
import asyncio
import logging

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine, SessionLocal
from app.models import Base
from app.routers.candidates import router as candidates_router
from app.routers.comparison import router as comparison_router
from app.routers.interviews import router as interviews_router
from app.routers.matches import router as matches_router
from app.routers.positions import router as positions_router
from app.routers.summaries import router as summaries_router
from app.routers.settings_api import router as settings_router

app = FastAPI(title="Interview Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _migrate_candidate_name_column()


def _migrate_candidate_name_column():
    """Add 'name' column to candidates table if missing, then backfill from resume text."""
    from app.services.pii_masking import extract_name_from_resume

    db = SessionLocal()
    try:
        cols = [
            row[1] for row in db.execute(text("PRAGMA table_info(candidates)"))
        ]
        if "name" not in cols:
            db.execute(text("ALTER TABLE candidates ADD COLUMN name VARCHAR(100) DEFAULT ''"))
            db.commit()
            logger.info("Migration: added 'name' column to candidates table")

        rows = db.execute(
            text("SELECT id, resume_raw_text, resume_file_path, name FROM candidates")
        ).fetchall()
        for row in rows:
            cid, raw_text, file_path, existing_name = row
            if existing_name:
                continue
            import os
            original_filename = os.path.basename(file_path) if file_path else ""
            name = extract_name_from_resume(raw_text or "", original_filename)
            if name:
                db.execute(
                    text("UPDATE candidates SET name = :name WHERE id = :id"),
                    {"name": name, "id": cid},
                )
        db.commit()
        logger.info("Migration: backfilled candidate names")
    except Exception:
        logger.exception("Migration failed for candidate name column")
        db.rollback()
    finally:
        db.close()


app.include_router(positions_router)
app.include_router(candidates_router)
app.include_router(matches_router)
app.include_router(interviews_router)
app.include_router(summaries_router)
app.include_router(comparison_router)
app.include_router(settings_router)


@app.get("/api/health")
def health_check():
    from app.database import is_encrypted

    try:
        from app.database import SessionLocal

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "encrypted": is_encrypted(),
    }


@app.websocket("/ws/interview/{interview_id}")
async def websocket_interview(websocket: WebSocket, interview_id: int):
    from app.services import interview_manager

    await websocket.accept()

    session = interview_manager.get_session(interview_id)
    if not session:
        await websocket.send_text(json.dumps({
            "type": "error", "message": "Session not found"
        }))
        await websocket.close()
        return

    interview_manager.add_websocket(session, websocket)

    msg_count = 0
    try:
        while True:
            message = await websocket.receive()
            msg_count += 1
            if msg_count <= 3 or msg_count % 100 == 0:
                msg_type = "bytes" if ("bytes" in message and message["bytes"]) else "text"
                msg_len = len(message.get("bytes", b"") or b"") if msg_type == "bytes" else len(message.get("text", "") or "")
                print(f"[ws] msg#{msg_count} type={msg_type} len={msg_len}", flush=True)

            if "bytes" in message and message["bytes"]:
                raw = message["bytes"]
                source_tag = None
                # Tagged frame: 1 tag byte + N*4 float32 bytes → total % 4 == 1
                if len(raw) > 4 and len(raw) % 4 == 1 and raw[0] in (0x01, 0x02):
                    source_tag = "interviewer" if raw[0] == 0x01 else "candidate"
                    raw = raw[1:]
                if len(raw) % 4 != 0:
                    continue
                audio_data = np.frombuffer(raw, dtype=np.float32)
                if session._audio_queue and session._running:
                    session._audio_queue.put_nowait((source_tag, audio_data))
                    amp = float(np.max(np.abs(audio_data)))
                    if amp > 0.001:
                        print(f"[ws] audio src={source_tag} samples={len(audio_data)} amp={amp:.4f}", flush=True)
                continue

            data = message.get("text", "")
            if not data:
                continue
            msg = json.loads(data)

            if msg.get("type") == "manual_input":
                await interview_manager.handle_manual_input(
                    session,
                    speaker=msg.get("speaker", "candidate"),
                    text=msg.get("text", ""),
                )
            elif msg.get("type") == "switch_question":
                session.current_question_index = msg.get("index", 0)
                await interview_manager.broadcast(session, {
                    "type": "question_switched",
                    "current_question_index": session.current_question_index,
                })
            elif msg.get("type") == "start_audio":
                asyncio.create_task(interview_manager.start_audio(session))
                asyncio.create_task(interview_manager.process_audio_loop(session))
            elif msg.get("type") == "start_browser_audio":
                session._running = True
                print("[ws] start_browser_audio received, launching process_audio_loop", flush=True)
                asyncio.create_task(interview_manager.process_audio_loop(session))
                await interview_manager.broadcast(session, {
                    "type": "browser_audio_ready",
                    "message": "后端已就绪，开始接收浏览器音频",
                })
    except WebSocketDisconnect:
        session._running = False
        interview_manager.remove_websocket(session, websocket)


# --------------- SPA static file serving (standalone mode) ---------------
_static_dir = os.environ.get("INTERVIEW_STATIC_DIR", os.path.join(os.getcwd(), "static"))

if os.path.isdir(_static_dir):
    _assets_dir = os.path.join(_static_dir, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(_static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_static_dir, "index.html"))
