import json
import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

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
    return {"status": "ok"}


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
            data = await websocket.receive_text()
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
    except WebSocketDisconnect:
        interview_manager.remove_websocket(session, websocket)
