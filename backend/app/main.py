import json
import asyncio
import logging

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers.candidates import router as candidates_router
from app.routers.comparison import router as comparison_router
from app.routers.interviews import router as interviews_router
from app.routers.matches import router as matches_router
from app.routers.positions import router as positions_router
from app.routers.summaries import router as summaries_router
from app.routers.settings_api import router as settings_router

app = FastAPI(title="Interview Assistant", version="0.1.0")

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

    try:
        while True:
            message = await websocket.receive()

            if "bytes" in message and message["bytes"]:
                raw = message["bytes"]
                speaker = "candidate"
                if len(raw) > 4 and raw[0] in (0x01, 0x02):
                    speaker = "interviewer" if raw[0] == 0x01 else "candidate"
                    raw = raw[1:]
                audio_data = np.frombuffer(raw, dtype=np.float32)
                if session._audio_queue and session._running:
                    session._audio_queue.put_nowait((speaker, audio_data))
                    print(f"[ws] Queued audio ({speaker}): {len(audio_data)} samples, max_amp={float(np.max(np.abs(audio_data))):.4f}", flush=True)
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
