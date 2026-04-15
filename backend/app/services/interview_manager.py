import asyncio
import json
import logging
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.config import settings

logger = logging.getLogger(__name__)
from app.database import SessionLocal
from app.models.transcript import Transcript
from app.services.transcription import TranscriptionService, TranscriptSegment
from app.services.audio_capture import AudioCaptureService
from app.services.realtime_analysis import RealtimeAnalysisService
from app.services.pii_masking import PIIMasker
from app.services.speaker_diarization import HybridDiarizer


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
    _diarizer: HybridDiarizer | None = None
    _websockets: list[WebSocket] = field(default_factory=list)
    _audio_queue: asyncio.Queue | None = None
    _running: bool = False


_sessions: dict[int, InterviewSession] = {}


def get_session(interview_id: int) -> InterviewSession | None:
    return _sessions.get(interview_id)


def _persist_transcript(
    interview_id: int,
    speaker: str,
    raw_text: str,
    sanitized_text: str,
    timestamp: float,
    duration: float = 0.0,
):
    db = SessionLocal()
    try:
        t = Transcript(
            interview_id=interview_id,
            speaker=speaker,
            raw_text=raw_text,
            sanitized_text=sanitized_text,
            timestamp=timestamp,
            duration=duration,
        )
        db.add(t)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


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

    session._diarizer = HybridDiarizer(sample_rate=settings.audio_sample_rate)

    _sessions[interview_id] = session
    print(f"[interview_manager] Session created for interview {interview_id} "
          f"(transcription={session._transcription is not None}, "
          f"diarizer={session._diarizer is not None})", flush=True)
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
    session = _sessions.get(interview_id)
    if session:
        session._running = False
        if session._audio_capture:
            session._audio_capture.stop()


def remove_session(interview_id: int):
    _sessions.pop(interview_id, None)


async def process_audio_loop(session: InterviewSession):
    print(f"[audio_loop] Started for interview {session.interview_id}", flush=True)
    loop = asyncio.get_event_loop()

    while session._running:
        try:
            item = await asyncio.wait_for(
                session._audio_queue.get(), timeout=1.0
            )
        except asyncio.TimeoutError:
            continue

        if isinstance(item, tuple):
            source_speaker, audio = item
        else:
            source_speaker, audio = None, item

        if session._transcription is None:
            print("[audio_loop] No transcription service, skipping", flush=True)
            continue

        print(f"[audio_loop] Transcribing {len(audio)} samples (source={source_speaker})…", flush=True)
        try:
            segments = await loop.run_in_executor(
                None, session._transcription.transcribe, audio
            )
        except Exception as e:
            print(f"[audio_loop] Transcription error: {e}", flush=True)
            await broadcast(session, {
                "type": "error",
                "message": f"转录失败: {e}",
            })
            continue

        print(f"[audio_loop] Got {len(segments)} segments", flush=True)
        for seg in segments:
            elapsed = time.time() - session.start_time
            sanitized = session._masker.mask(seg.text) if session._masker else seg.text

            # Two-layer speaker identification:
            # Layer 1: source_tag (interviewer/candidate/None)
            # Layer 2: voiceprint within each side
            source_tag = source_speaker if source_speaker in ("interviewer", "candidate") else None
            if session._diarizer:
                sr = settings.audio_sample_rate
                s_idx = max(0, int(seg.start * sr))
                e_idx = min(len(audio), int(seg.end * sr))
                seg_audio = audio[s_idx:e_idx] if e_idx > s_idx else audio
                speaker = session._diarizer.identify(seg_audio, source_tag=source_tag)
            else:
                speaker = source_speaker or "unknown"

            print(f"[audio_loop] speaker={speaker} (source={source_speaker})", flush=True)
            line = f"{speaker}: {sanitized}"
            session.transcript_lines.append(line)

            _persist_transcript(
                interview_id=session.interview_id,
                speaker=speaker,
                raw_text=seg.text,
                sanitized_text=sanitized,
                timestamp=round(elapsed, 1),
                duration=seg.end - seg.start,
            )

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

    _persist_transcript(
        interview_id=session.interview_id,
        speaker=speaker,
        raw_text=text,
        sanitized_text=sanitized,
        timestamp=round(elapsed, 1),
    )

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
