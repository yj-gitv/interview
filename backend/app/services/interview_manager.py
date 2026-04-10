import asyncio
import json
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.config import settings
from app.services.transcription import TranscriptionService, TranscriptSegment
from app.services.audio_capture import AudioCaptureService
from app.services.realtime_analysis import RealtimeAnalysisService
from app.services.pii_masking import PIIMasker


@dataclass
class InterviewSession:
    interview_id: int
    questions: list[dict] = field(default_factory=list)
    current_question_index: int = 0
    transcript_lines: list[str] = field(default_factory=list)
    codename: str = "候选人"
    start_time: float = 0.0
    _audio_capture: AudioCaptureService | None = None
    _transcription: TranscriptionService | None = None
    _analysis: RealtimeAnalysisService | None = None
    _masker: PIIMasker | None = None
    _websockets: list[WebSocket] = field(default_factory=list)
    _audio_queue: asyncio.Queue | None = None
    _running: bool = False


_sessions: dict[int, InterviewSession] = {}


def get_session(interview_id: int) -> InterviewSession | None:
    return _sessions.get(interview_id)


async def create_session(
    interview_id: int,
    questions: list[dict],
    codename: str = "候选人",
) -> InterviewSession:
    session = InterviewSession(
        interview_id=interview_id,
        questions=questions,
        codename=codename,
        start_time=time.time(),
    )
    session._audio_queue = asyncio.Queue()
    session._masker = PIIMasker(codename=codename)
    session._analysis = RealtimeAnalysisService()

    try:
        session._transcription = TranscriptionService(
            model_size=settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    except Exception:
        session._transcription = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )

    _sessions[interview_id] = session
    return session


async def start_audio(session: InterviewSession):
    loop = asyncio.get_event_loop()

    def on_chunk(audio_data):
        loop.call_soon_threadsafe(session._audio_queue.put_nowait, audio_data)

    try:
        session._audio_capture = AudioCaptureService(
            device_name=settings.audio_device_name,
            sample_rate=settings.audio_sample_rate,
            chunk_seconds=settings.audio_chunk_seconds,
            on_chunk=on_chunk,
        )
        session._audio_capture.start()
        session._running = True
    except RuntimeError as e:
        await broadcast(session, {
            "type": "error",
            "message": f"音频设备错误: {e}. 请使用手动输入模式。",
        })


async def stop_session(interview_id: int):
    session = _sessions.pop(interview_id, None)
    if session:
        session._running = False
        if session._audio_capture:
            session._audio_capture.stop()


async def process_audio_loop(session: InterviewSession):
    while session._running:
        try:
            audio = await asyncio.wait_for(
                session._audio_queue.get(), timeout=1.0
            )
        except asyncio.TimeoutError:
            continue

        if session._transcription is None:
            continue

        segments = session._transcription.transcribe(audio)
        for seg in segments:
            elapsed = time.time() - session.start_time
            sanitized = session._masker.mask(seg.text) if session._masker else seg.text
            speaker = "candidate"

            line = f"{speaker}: {sanitized}"
            session.transcript_lines.append(line)

            await broadcast(session, {
                "type": "transcript",
                "speaker": speaker,
                "text": sanitized,
                "timestamp": round(elapsed, 1),
            })

        if segments and session._analysis:
            full_transcript = "\n".join(session.transcript_lines[-50:])
            try:
                result = await session._analysis.analyze(
                    transcript_so_far=full_transcript,
                    questions=session.questions,
                    current_question_index=session.current_question_index,
                )
                if result.current_question_index != session.current_question_index:
                    session.current_question_index = result.current_question_index
                await broadcast(session, {
                    "type": "analysis",
                    "current_question_index": result.current_question_index,
                    "elements_checked": result.elements_checked,
                    "follow_up_suggestions": result.follow_up_suggestions,
                    "instant_rating": result.instant_rating,
                    "instant_comment": result.instant_comment,
                })
            except Exception:
                pass


async def handle_manual_input(session: InterviewSession, speaker: str, text: str):
    elapsed = time.time() - session.start_time
    sanitized = session._masker.mask(text) if session._masker else text

    line = f"{speaker}: {sanitized}"
    session.transcript_lines.append(line)

    await broadcast(session, {
        "type": "transcript",
        "speaker": speaker,
        "text": sanitized,
        "timestamp": round(elapsed, 1),
    })

    if session._analysis:
        full_transcript = "\n".join(session.transcript_lines[-50:])
        try:
            result = await session._analysis.analyze(
                transcript_so_far=full_transcript,
                questions=session.questions,
                current_question_index=session.current_question_index,
            )
            if result.current_question_index != session.current_question_index:
                session.current_question_index = result.current_question_index
            await broadcast(session, {
                "type": "analysis",
                "current_question_index": result.current_question_index,
                "elements_checked": result.elements_checked,
                "follow_up_suggestions": result.follow_up_suggestions,
                "instant_rating": result.instant_rating,
                "instant_comment": result.instant_comment,
            })
        except Exception:
            pass


def add_websocket(session: InterviewSession, ws: WebSocket):
    session._websockets.append(ws)


def remove_websocket(session: InterviewSession, ws: WebSocket):
    if ws in session._websockets:
        session._websockets.remove(ws)


async def broadcast(session: InterviewSession, data: dict):
    message = json.dumps(data, ensure_ascii=False)
    disconnected = []
    for ws in session._websockets:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        remove_websocket(session, ws)
