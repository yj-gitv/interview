import asyncio
import json
import logging
import time
from dataclasses import dataclass, field

import numpy as np

from fastapi import WebSocket

from app.config import settings

logger = logging.getLogger(__name__)
from app.database import SessionLocal
from app.models.transcript import Transcript
from app.services.transcription import SherpaRecognizer, SenseVoiceRecognizer, SherpaPunctuation
from app.services.audio_processing import SileroVAD, AudioPreprocessor
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
    _analysis: RealtimeAnalysisService | None = None
    _masker: PIIMasker | None = None
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

    _sessions[interview_id] = session
    print(
        f"[interview_manager] Session created for interview {interview_id}",
        flush=True,
    )
    return session


async def start_audio(session: InterviewSession):
    loop = asyncio.get_event_loop()

    def on_chunk(audio_data):
        loop.call_soon_threadsafe(session._audio_queue.put_nowait, audio_data)

    try:
        session._audio_capture = AudioCaptureService(
            device_name=settings.audio_device_name,
            sample_rate=settings.audio_sample_rate,
            chunk_seconds=0.6,
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
    """VAD-driven hybrid ASR: Silero VAD segments speech, SenseVoice transcribes finals,
    streaming Paraformer provides real-time drafts."""
    print(f"[audio_loop] Started for interview {session.interview_id}", flush=True)
    loop = asyncio.get_event_loop()

    recognizer = SherpaRecognizer.get_instance(settings.asr_model_dir)
    print("[audio_loop] SherpaRecognizer (streaming) ready", flush=True)

    offline = SenseVoiceRecognizer.get_instance(
        settings.asr_offline_model, settings.asr_offline_tokens
    )
    print("[audio_loop] SenseVoiceRecognizer (offline) ready", flush=True)

    punctuator = SherpaPunctuation.get_instance(settings.punct_model_path)
    print("[audio_loop] SherpaPunctuation ready", flush=True)

    # Per-source VAD instance + streaming ASR stream + last draft text
    vad_instances: dict[str, SileroVAD] = {}
    stream_states: dict[str, list] = {}  # [asr_stream, last_draft_text]
    onsite_speaker_toggle = False
    preprocessor = AudioPreprocessor()
    chunk_counts: dict[str, int] = {}

    while session._running:
        try:
            item = await asyncio.wait_for(
                session._audio_queue.get(), timeout=1.0
            )
        except asyncio.TimeoutError:
            continue

        try:
            if isinstance(item, tuple):
                source_speaker, audio = item
            else:
                source_speaker, audio = None, item

            tag = source_speaker or "single"
            chunk_counts[tag] = chunk_counts.get(tag, 0) + 1
            if chunk_counts[tag] <= 3:
                amp = float(np.max(np.abs(audio)))
                print(f"[audio_loop] src={tag} chunk#{chunk_counts[tag]} samples={len(audio)} amp={amp:.4f}", flush=True)

            # Initialize per-source VAD and streaming ASR
            if tag not in vad_instances:
                vad_instances[tag] = SileroVAD(settings.vad_model_path)
                stream_states[tag] = [recognizer.create_stream(), ""]
                print(f"[audio_loop] Created VAD+stream for tag={tag}", flush=True)

            vad = vad_instances[tag]
            asr_stream = stream_states[tag][0]
            last_text: str = stream_states[tag][1]

            # Feed RAW audio to streaming recognizer (no preprocessing)
            await loop.run_in_executor(
                None, recognizer.feed_and_decode, asr_stream, audio
            )

            current_text = recognizer.get_text(asr_stream)
            elapsed = time.time() - session.start_time

            if source_speaker in ("interviewer", "candidate"):
                speaker = source_speaker
            elif tag == "single":
                speaker = "candidate" if onsite_speaker_toggle else "interviewer"
            else:
                speaker = "interviewer"

            # Broadcast real-time draft
            if current_text and current_text != last_text:
                sanitized = session._masker.mask(current_text) if session._masker else current_text
                await broadcast(session, {
                    "type": "transcript",
                    "speaker": speaker,
                    "text": sanitized,
                    "timestamp": round(elapsed, 1),
                    "is_final": False,
                })
                stream_states[tag][1] = current_text

            # Feed RAW audio to VAD — it returns complete speech segments
            speech_segments = await loop.run_in_executor(
                None, vad.process, audio
            )

            for seg_audio in speech_segments:
                seg_dur = len(seg_audio) / 16000
                if seg_dur < 0.5:
                    print(f"[audio_loop] Skip short segment: {seg_dur:.2f}s [{tag}]", flush=True)
                    continue

                print(f"[audio_loop] VAD segment [{tag}]: {seg_dur:.1f}s, amp={float(np.max(np.abs(seg_audio))):.3f}", flush=True)

                # Normalize AFTER VAD has cut the segment
                seg_audio = preprocessor.process(seg_audio)

                try:
                    final_text = await loop.run_in_executor(
                        None, offline.transcribe, seg_audio
                    )
                except Exception as e:
                    print(f"[audio_loop] SenseVoice failed: {e}", flush=True)
                    final_text = current_text

                if not final_text or len(final_text.strip()) < 2:
                    continue

                if not any(p in final_text for p in "，。？！、；："):
                    try:
                        final_text = await loop.run_in_executor(
                            None, punctuator.add_punctuation, final_text
                        )
                    except Exception:
                        pass

                if tag == "single":
                    onsite_speaker_toggle = not onsite_speaker_toggle

                sanitized = session._masker.mask(final_text) if session._masker else final_text
                line = f"{speaker}: {sanitized}"
                session.transcript_lines.append(line)
                print(f"[audio_loop] FINAL [{speaker}]: {sanitized}", flush=True)

                _persist_transcript(
                    interview_id=session.interview_id,
                    speaker=speaker,
                    raw_text=final_text,
                    sanitized_text=sanitized,
                    timestamp=round(elapsed, 1),
                )

                await broadcast(session, {
                    "type": "transcript",
                    "speaker": speaker,
                    "text": sanitized,
                    "timestamp": round(elapsed, 1),
                    "is_final": True,
                })

                recognizer.reset(asr_stream)
                stream_states[tag] = [recognizer.create_stream(), ""]

                if session._analysis and len(session.transcript_lines) % 3 == 0:
                    asyncio.create_task(_run_analysis(session))

        except Exception as e:
            print(f"[audio_loop] Error processing chunk: {e}", flush=True)
            import traceback
            traceback.print_exc()

    print(f"[audio_loop] Stopped for interview {session.interview_id}", flush=True)


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
        "is_final": True,
    })

    if session._analysis:
        asyncio.create_task(_run_analysis(session))


async def _run_analysis(session: InterviewSession):
    """Run realtime analysis in background, never blocks audio loop."""
    try:
        full_transcript = "\n".join(session.transcript_lines[-50:])
        print(f"[analysis] Triggering analysis, {len(session.transcript_lines)} lines so far", flush=True)
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
        print(f"[analysis] Success: suggestions={result.follow_up_suggestions}, rating={result.instant_rating}", flush=True)
    except Exception as e:
        print(f"[analysis] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()


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
