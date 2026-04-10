# Interview Assistant Phase 2: Real-Time Interview & Summary

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build real-time interview assistance (audio capture, live transcription, AI analysis) and post-interview summary with PDF export, completing the core interview workflow.

**Architecture:** Extend the existing FastAPI backend with WebSocket support for real-time transcription. Audio is captured via sounddevice (BlackHole virtual audio), transcribed locally by faster-whisper, and analyzed by LLM for real-time suggestions. Frontend adds a three-panel interview UI with WebSocket client. Post-interview summaries are generated via LLM and exportable as PDF.

**Tech Stack:** Existing stack + sounddevice, faster-whisper, numpy, fpdf2, WebSocket (built into FastAPI)

---

## File Structure

```
backend/
├── requirements.txt                    # Add: sounddevice, faster-whisper, numpy, fpdf2
├── app/
│   ├── main.py                         # Add: WebSocket route, interview router
│   ├── config.py                       # Add: whisper model config, audio config
│   ├── models/
│   │   ├── __init__.py                 # Add: new model exports
│   │   ├── interview.py                # NEW: Interview table
│   │   ├── transcript.py               # NEW: Transcript segments table
│   │   ├── evaluation.py               # NEW: Answer evaluations table
│   │   └── summary.py                  # NEW: Interview summary table
│   ├── schemas/
│   │   ├── interview.py                # NEW: Interview request/response schemas
│   │   └── summary.py                  # NEW: Summary schemas
│   ├── routers/
│   │   ├── interviews.py               # NEW: Interview CRUD + start/stop
│   │   └── summaries.py                # NEW: Summary generation + PDF export
│   └── services/
│       ├── audio_capture.py            # NEW: BlackHole audio capture via sounddevice
│       ├── transcription.py            # NEW: faster-whisper transcription
│       ├── realtime_analysis.py        # NEW: Real-time LLM analysis (question tracking, suggestions)
│       ├── interview_manager.py        # NEW: Orchestrates audio→transcription→analysis→WebSocket
│       ├── summary_gen.py              # NEW: Post-interview summary generation
│       └── pdf_export.py              # NEW: PDF report generation
├── tests/
│   ├── test_models_interview.py        # NEW: Interview model tests
│   ├── test_transcription.py           # NEW: Transcription service tests
│   ├── test_realtime_analysis.py       # NEW: Real-time analysis tests
│   ├── test_summary_gen.py             # NEW: Summary generation tests
│   ├── test_pdf_export.py              # NEW: PDF export tests
│   ├── test_api_interviews.py          # NEW: Interview API tests
│   └── test_api_summaries.py           # NEW: Summary API tests
frontend/
├── src/
│   ├── App.tsx                         # Add: interview routes
│   ├── api/client.ts                   # Add: interview & summary API + WebSocket
│   ├── components/
│   │   └── Layout.tsx                  # Add: interview nav item
│   └── pages/
│       ├── InterviewLive.tsx           # NEW: Three-panel real-time interview UI
│       ├── InterviewHistory.tsx        # NEW: Interview history list
│       └── InterviewSummary.tsx        # NEW: Post-interview summary view
```

---

### Task 1: Add Phase 2 Dependencies

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Update requirements.txt**

`backend/requirements.txt` — append these lines at the end:

```
sounddevice==0.5.1
numpy==2.2.4
faster-whisper==1.1.1
fpdf2==2.8.3
```

- [ ] **Step 2: Add config for audio and whisper**

Add to `backend/app/config.py` inside the `Settings` class, after the existing fields:

```python
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    audio_sample_rate: int = 16000
    audio_chunk_seconds: float = 3.0
    audio_device_name: str = "BlackHole 2ch"
```

- [ ] **Step 3: Install new dependencies**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
pip install sounddevice==0.5.1 numpy==2.2.4 faster-whisper==1.1.1 fpdf2==2.8.3
```

- [ ] **Step 4: Verify imports**

```bash
python -c "import sounddevice; import numpy; import faster_whisper; import fpdf; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add Phase 2 dependencies (audio, whisper, PDF)"
```

---

### Task 2: Interview & Related Database Models

**Files:**
- Create: `backend/app/models/interview.py`
- Create: `backend/app/models/transcript.py`
- Create: `backend/app/models/evaluation.py`
- Create: `backend/app/models/summary.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create Interview model**

`backend/app/models/interview.py`:

```python
import enum
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus), default=InterviewStatus.SCHEDULED
    )
    questions_json: Mapped[str] = mapped_column(
        String, default="[]"
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    position: Mapped["Position"] = relationship()
    candidate: Mapped["Candidate"] = relationship()
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="interview", order_by="Transcript.timestamp"
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="interview"
    )
    summary: Mapped["Summary | None"] = relationship(
        back_populates="interview", uselist=False
    )
```

- [ ] **Step 2: Create Transcript model**

`backend/app/models/transcript.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    speaker: Mapped[str] = mapped_column(String(20))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    sanitized_text: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[float] = mapped_column(Float, default=0.0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    interview: Mapped["Interview"] = relationship(back_populates="transcripts")
```

- [ ] **Step 3: Create Evaluation model**

`backend/app/models/evaluation.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    question_index: Mapped[int] = mapped_column(Integer, default=-1)
    question_text: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[str] = mapped_column(String(20), default="pending")
    ai_comment: Mapped[str] = mapped_column(Text, default="")
    interviewer_note: Mapped[str] = mapped_column(Text, default="")
    expression_score: Mapped[float] = mapped_column(Float, default=0)
    case_richness_score: Mapped[float] = mapped_column(Float, default=0)
    depth_score: Mapped[float] = mapped_column(Float, default=0)
    self_awareness_score: Mapped[float] = mapped_column(Float, default=0)
    enthusiasm_score: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    interview: Mapped["Interview"] = relationship(back_populates="evaluations")
```

- [ ] **Step 4: Create Summary model**

`backend/app/models/summary.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id"), unique=True
    )
    candidate_overview: Mapped[str] = mapped_column(Text, default="")
    expression_score: Mapped[float] = mapped_column(Float, default=0)
    case_richness_score: Mapped[float] = mapped_column(Float, default=0)
    depth_score: Mapped[float] = mapped_column(Float, default=0)
    self_awareness_score: Mapped[float] = mapped_column(Float, default=0)
    enthusiasm_score: Mapped[float] = mapped_column(Float, default=0)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    concerns: Mapped[str] = mapped_column(Text, default="[]")
    jd_alignment: Mapped[str] = mapped_column(Text, default="[]")
    recommendation: Mapped[str] = mapped_column(String(20), default="pending")
    recommendation_reason: Mapped[str] = mapped_column(Text, default="")
    next_steps: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    interview: Mapped["Interview"] = relationship(back_populates="summary")
```

- [ ] **Step 5: Update models __init__.py**

Replace `backend/app/models/__init__.py`:

```python
from app.database import Base
from app.models.position import Position, PositionStatus
from app.models.candidate import Candidate
from app.models.resume_match import ResumeMatch
from app.models.interview import Interview, InterviewStatus
from app.models.transcript import Transcript
from app.models.evaluation import Evaluation
from app.models.summary import Summary

__all__ = [
    "Base",
    "Position",
    "PositionStatus",
    "Candidate",
    "ResumeMatch",
    "Interview",
    "InterviewStatus",
    "Transcript",
    "Evaluation",
    "Summary",
]
```

- [ ] **Step 6: Verify models load**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
python -c "from app.models import Interview, Transcript, Evaluation, Summary; print('Phase 2 models OK')"
```

Expected: `Phase 2 models OK`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: database models for Interview, Transcript, Evaluation, Summary"
```

---

### Task 3: Interview Schemas & CRUD API

**Files:**
- Create: `backend/app/schemas/interview.py`
- Create: `backend/app/schemas/summary.py`
- Create: `backend/app/routers/interviews.py`
- Create: `backend/tests/test_api_interviews.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create interview schemas**

`backend/app/schemas/interview.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class InterviewCreate(BaseModel):
    position_id: int
    candidate_id: int
    questions_json: str = "[]"


class InterviewResponse(BaseModel):
    id: int
    position_id: int
    candidate_id: int
    status: str
    questions_json: str
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int
    created_at: datetime
    candidate_codename: str = ""
    position_title: str = ""
    has_summary: bool = False

    model_config = {"from_attributes": True}
```

`backend/app/schemas/summary.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    id: int
    interview_id: int
    candidate_overview: str
    expression_score: float
    case_richness_score: float
    depth_score: float
    self_awareness_score: float
    enthusiasm_score: float
    overall_score: float
    highlights: str
    concerns: str
    jd_alignment: str
    recommendation: str
    recommendation_reason: str
    next_steps: str
    pdf_path: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Write failing tests for interview API**

`backend/tests/test_api_interviews.py`:

```python
import io
import json

import pytest
from docx import Document


def _setup_position_and_candidate(client) -> tuple[int, int]:
    resp = client.post("/api/positions", json={
        "title": "产品经理", "jd_text": "负责用户增长",
    })
    pid = resp.json()["id"]

    doc = Document()
    doc.add_paragraph("张三 产品经理 3年经验")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    resp = client.post(
        f"/api/candidates/upload?position_id={pid}",
        files={"file": ("r.docx", buf.read(), "application/octet-stream")},
    )
    cid = resp.json()["id"]
    return pid, cid


class TestCreateInterview:
    def test_creates_interview(self, client):
        pid, cid = _setup_position_and_candidate(client)
        questions = json.dumps([{"question": "自我介绍", "purpose": "了解表达"}])
        resp = client.post("/api/interviews", json={
            "position_id": pid,
            "candidate_id": cid,
            "questions_json": questions,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["candidate_id"] == cid


class TestListInterviews:
    def test_lists_by_candidate(self, client):
        pid, cid = _setup_position_and_candidate(client)
        client.post("/api/interviews", json={
            "position_id": pid, "candidate_id": cid,
        })
        resp = client.get(f"/api/interviews?candidate_id={cid}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetInterview:
    def test_gets_by_id(self, client):
        pid, cid = _setup_position_and_candidate(client)
        create_resp = client.post("/api/interviews", json={
            "position_id": pid, "candidate_id": cid,
        })
        iid = create_resp.json()["id"]
        resp = client.get(f"/api/interviews/{iid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == iid

    def test_404_for_missing(self, client):
        resp = client.get("/api/interviews/999")
        assert resp.status_code == 404


class TestStartInterview:
    def test_starts_interview(self, client):
        pid, cid = _setup_position_and_candidate(client)
        create_resp = client.post("/api/interviews", json={
            "position_id": pid, "candidate_id": cid,
        })
        iid = create_resp.json()["id"]
        resp = client.post(f"/api/interviews/{iid}/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"
        assert resp.json()["started_at"] is not None


class TestEndInterview:
    def test_ends_interview(self, client):
        pid, cid = _setup_position_and_candidate(client)
        create_resp = client.post("/api/interviews", json={
            "position_id": pid, "candidate_id": cid,
        })
        iid = create_resp.json()["id"]
        client.post(f"/api/interviews/{iid}/start")
        resp = client.post(f"/api/interviews/{iid}/end")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert resp.json()["ended_at"] is not None
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
pytest tests/test_api_interviews.py -v
```

Expected: FAIL (route not found)

- [ ] **Step 4: Implement interviews router**

`backend/app/routers/interviews.py`:

```python
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interview import Interview, InterviewStatus
from app.models.candidate import Candidate
from app.models.position import Position
from app.schemas.interview import InterviewCreate, InterviewResponse

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("", status_code=status.HTTP_201_CREATED)
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


@router.get("")
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


@router.get("/{interview_id}")
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return _to_response(interview)


@router.post("/{interview_id}/start")
def start_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    interview.status = InterviewStatus.IN_PROGRESS
    interview.started_at = datetime.now()
    db.commit()
    db.refresh(interview)
    return _to_response(interview)


@router.post("/{interview_id}/end")
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


def _to_response(interview: Interview) -> dict:
    return {
        "id": interview.id,
        "position_id": interview.position_id,
        "candidate_id": interview.candidate_id,
        "status": interview.status.value,
        "questions_json": interview.questions_json,
        "started_at": interview.started_at.isoformat() if interview.started_at else None,
        "ended_at": interview.ended_at.isoformat() if interview.ended_at else None,
        "duration_seconds": interview.duration_seconds,
        "created_at": interview.created_at.isoformat() if interview.created_at else None,
        "candidate_codename": interview.candidate.codename if interview.candidate else "",
        "position_title": interview.position.title if interview.position else "",
        "has_summary": interview.summary is not None,
    }
```

- [ ] **Step 5: Mount router in main.py**

Add to `backend/app/main.py` after existing router imports:

```python
from app.routers.interviews import router as interviews_router
```

Add after existing `app.include_router` calls:

```python
app.include_router(interviews_router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_api_interviews.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: interview CRUD API with start/end lifecycle"
```

---

### Task 4: Transcription Service (faster-whisper)

**Files:**
- Create: `backend/app/services/transcription.py`
- Create: `backend/tests/test_transcription.py`

- [ ] **Step 1: Write failing tests for transcription**

`backend/tests/test_transcription.py`:

```python
import numpy as np
import pytest

from app.services.transcription import TranscriptionService, TranscriptSegment


class TestTranscriptSegment:
    def test_segment_fields(self):
        seg = TranscriptSegment(text="你好", start=0.0, end=1.5)
        assert seg.text == "你好"
        assert seg.start == 0.0
        assert seg.end == 1.5


class TestTranscriptionService:
    def test_creates_with_config(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        assert service.model_size == "tiny"

    def test_transcribe_silence_returns_empty(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        silence = np.zeros(16000, dtype=np.float32)
        segments = service.transcribe(silence, sample_rate=16000)
        assert isinstance(segments, list)

    def test_transcribe_accepts_numpy_array(self):
        service = TranscriptionService(
            model_size="tiny",
            device="cpu",
            compute_type="int8",
        )
        audio = np.random.randn(16000).astype(np.float32) * 0.01
        segments = service.transcribe(audio, sample_rate=16000)
        assert isinstance(segments, list)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_transcription.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Implement transcription service**

`backend/app/services/transcription.py`:

```python
from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float


class TranscriptionService:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model_size = model_size
        self._model = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: str = "zh",
    ) -> list[TranscriptSegment]:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        if np.max(np.abs(audio)) > 1.0:
            audio = audio / 32768.0

        segments, _ = self._model.transcribe(
            audio,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        results = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                results.append(TranscriptSegment(
                    text=text, start=seg.start, end=seg.end
                ))
        return results
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_transcription.py -v
```

Expected: All tests PASS (the tiny model will be auto-downloaded on first run)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: faster-whisper transcription service with VAD"
```

---

### Task 5: Audio Capture Service

**Files:**
- Create: `backend/app/services/audio_capture.py`

- [ ] **Step 1: Implement audio capture service**

`backend/app/services/audio_capture.py`:

```python
import threading
from collections.abc import Callable

import numpy as np
import sounddevice as sd


class AudioCaptureService:
    def __init__(
        self,
        device_name: str = "BlackHole 2ch",
        sample_rate: int = 16000,
        chunk_seconds: float = 3.0,
        on_chunk: Callable[[np.ndarray], None] | None = None,
    ):
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.on_chunk = on_chunk
        self._running = False
        self._thread: threading.Thread | None = None
        self._device_id: int | None = None

    def _find_device(self) -> int | None:
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if self.device_name in d["name"] and d["max_input_channels"] > 0:
                return i
        return None

    def list_devices(self) -> list[dict]:
        devices = sd.query_devices()
        return [
            {"id": i, "name": d["name"], "channels": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    def start(self):
        self._device_id = self._find_device()
        if self._device_id is None:
            available = [d["name"] for d in self.list_devices()]
            raise RuntimeError(
                f"Audio device '{self.device_name}' not found. "
                f"Available input devices: {available}"
            )
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running

    def _capture_loop(self):
        chunk_size = int(self.sample_rate * self.chunk_seconds)
        try:
            with sd.InputStream(
                device=self._device_id,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_size,
            ) as stream:
                while self._running:
                    audio, _ = stream.read(chunk_size)
                    chunk = audio.flatten()
                    if self.on_chunk and np.max(np.abs(chunk)) > 0.001:
                        self.on_chunk(chunk)
        except Exception as e:
            self._running = False
            raise RuntimeError(f"Audio capture error: {e}") from e
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: audio capture service with BlackHole/sounddevice"
```

---

### Task 6: Real-Time Analysis Service

**Files:**
- Create: `backend/app/services/realtime_analysis.py`
- Create: `backend/tests/test_realtime_analysis.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_realtime_analysis.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from app.services.realtime_analysis import RealtimeAnalysisService, AnalysisResult


SAMPLE_QUESTIONS = [
    {"question": "请做自我介绍", "purpose": "了解表达", "good_answer_elements": ["结构清晰"], "red_flags": ["冗长"]},
    {"question": "说说你的项目经验", "purpose": "验证经历", "good_answer_elements": ["STAR法则"], "red_flags": ["无细节"]},
]

MOCK_ANALYSIS = {
    "current_question_index": 0,
    "elements_checked": ["结构清晰"],
    "follow_up_suggestions": ["能否举一个具体的数据指标来说明你的成果？"],
    "instant_rating": "好",
    "instant_comment": "表达清晰有条理",
}


class TestRealtimeAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_returns_result(self):
        service = RealtimeAnalysisService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_ANALYSIS
        ):
            result = await service.analyze(
                transcript_so_far="面试官：请做自我介绍\n候选人：我是张三，有3年产品经理经验...",
                questions=SAMPLE_QUESTIONS,
                current_question_index=0,
            )
            assert isinstance(result, AnalysisResult)
            assert result.current_question_index == 0
            assert len(result.follow_up_suggestions) >= 1

    @pytest.mark.asyncio
    async def test_detects_question_switch(self):
        mock_response = {
            "current_question_index": 1,
            "elements_checked": [],
            "follow_up_suggestions": [],
            "instant_rating": "",
            "instant_comment": "",
        }
        service = RealtimeAnalysisService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await service.analyze(
                transcript_so_far="面试官：说说你的项目经验\n候选人：我之前做过...",
                questions=SAMPLE_QUESTIONS,
                current_question_index=0,
            )
            assert result.current_question_index == 1


class TestAnalysisResult:
    def test_fields(self):
        result = AnalysisResult(**MOCK_ANALYSIS)
        assert result.instant_rating == "好"
        assert "数据指标" in result.follow_up_suggestions[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_realtime_analysis.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement real-time analysis service**

`backend/app/services/realtime_analysis.py`:

```python
from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class AnalysisResult:
    current_question_index: int = -1
    elements_checked: list[str] = field(default_factory=list)
    follow_up_suggestions: list[str] = field(default_factory=list)
    instant_rating: str = ""
    instant_comment: str = ""


REALTIME_SYSTEM_PROMPT = """你是一位面试辅助AI。根据当前面试转录和问题清单，实时分析并提供辅助。

任务：
1. 判断当前正在讨论的问题（通过语义匹配，而非逐字对照）
2. 检查候选人回答中已覆盖的优秀要素
3. 生成追问建议（当回答缺乏具体案例/数据、与简历有出入、过于简短、或出现有价值新话题时）
4. 给出即时评价（好/一般/差）

返回JSON格式：
{
  "current_question_index": number,
  "elements_checked": ["已覆盖的要素"],
  "follow_up_suggestions": ["追问建议1", "追问建议2"],
  "instant_rating": "好/一般/差/空字符串",
  "instant_comment": "一句话评语"
}"""


class RealtimeAnalysisService:
    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._llm

    async def _call_llm(self, prompt: str) -> dict:
        llm = self._get_llm()
        return await llm.chat_json(
            prompt=prompt,
            model=settings.openai_model_fast,
            system=REALTIME_SYSTEM_PROMPT,
        )

    async def analyze(
        self,
        transcript_so_far: str,
        questions: list[dict],
        current_question_index: int = 0,
    ) -> AnalysisResult:
        questions_text = "\n".join(
            f"[{i}] {q.get('question', '')} (考察: {q.get('purpose', '')}; "
            f"优秀要素: {', '.join(q.get('good_answer_elements', []))})"
            for i, q in enumerate(questions)
        )

        prompt = (
            f"## 面试问题清单\n{questions_text}\n\n"
            f"## 当前问题索引: {current_question_index}\n\n"
            f"## 面试转录（最近内容）\n{transcript_so_far[-2000:]}"
        )

        data = await self._call_llm(prompt)
        return AnalysisResult(
            current_question_index=data.get("current_question_index", current_question_index),
            elements_checked=data.get("elements_checked", []),
            follow_up_suggestions=data.get("follow_up_suggestions", []),
            instant_rating=data.get("instant_rating", ""),
            instant_comment=data.get("instant_comment", ""),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_realtime_analysis.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: real-time interview analysis service with LLM"
```

---

### Task 7: Interview Manager & WebSocket

**Files:**
- Create: `backend/app/services/interview_manager.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Implement interview manager**

`backend/app/services/interview_manager.py`:

```python
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
```

- [ ] **Step 2: Add WebSocket endpoint to main.py**

Add these imports at the top of `backend/app/main.py`:

```python
import json
import asyncio

from fastapi import WebSocket, WebSocketDisconnect
```

Add this WebSocket route after the health check endpoint in `backend/app/main.py`:

```python
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
```

- [ ] **Step 3: Add session management endpoints to interviews router**

Append to `backend/app/routers/interviews.py`:

```python
import json as json_module

from app.services import interview_manager


@router.post("/{interview_id}/session")
async def create_session(interview_id: int, db: Session = Depends(get_db)):
    interview = db.get(Interview, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    questions = json_module.loads(interview.questions_json) if interview.questions_json else []
    codename = interview.candidate.codename if interview.candidate else "候选人"

    session = await interview_manager.create_session(
        interview_id=interview_id,
        questions=questions,
        codename=codename,
    )
    return {"status": "session_created", "interview_id": interview_id}


@router.post("/{interview_id}/session/stop")
async def stop_session(interview_id: int):
    await interview_manager.stop_session(interview_id)
    return {"status": "session_stopped"}


@router.get("/{interview_id}/session/status")
async def session_status(interview_id: int):
    session = interview_manager.get_session(interview_id)
    if not session:
        return {"active": False}
    return {
        "active": True,
        "running": session._running,
        "current_question_index": session.current_question_index,
        "transcript_count": len(session.transcript_lines),
    }
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: interview manager with WebSocket real-time communication"
```

---

### Task 8: Summary Generation Service

**Files:**
- Create: `backend/app/services/summary_gen.py`
- Create: `backend/tests/test_summary_gen.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_summary_gen.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from app.services.summary_gen import SummaryGenService, SummaryResult


MOCK_LLM_RESPONSE = {
    "candidate_overview": "候选人具有3年产品经理经验，在用户增长方向有突出表现。",
    "expression_score": 85,
    "case_richness_score": 78,
    "depth_score": 80,
    "self_awareness_score": 72,
    "enthusiasm_score": 88,
    "overall_score": 81,
    "highlights": ["数据驱动思维强", "表达逻辑清晰", "有量化成果"],
    "concerns": ["管理经验不足", "对行业趋势了解有限"],
    "jd_alignment": [
        {"requirement": "用户增长经验", "status": "达成", "note": "有直接DAU提升经验"},
        {"requirement": "团队管理", "status": "部分达成", "note": "带过2人小团队"},
    ],
    "recommendation": "推荐",
    "recommendation_reason": "核心能力与岗位需求匹配度高，虽然管理经验需要培养，但成长潜力好。",
    "next_steps": "建议二面重点考察团队管理能力和跨部门协作经验。",
}


class TestSummaryGenService:
    @pytest.mark.asyncio
    async def test_generates_summary(self):
        service = SummaryGenService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.generate(
                transcript="面试官：请自我介绍\n候选人：我是一名产品经理...",
                jd_text="招聘产品经理",
                resume_text="3年经验",
                match_data={"overall_score": 78, "highlights": ["经验丰富"]},
            )
            assert isinstance(result, SummaryResult)
            assert result.overall_score == 81
            assert result.recommendation == "推荐"
            assert len(result.highlights) >= 1
            assert len(result.jd_alignment) >= 1


class TestSummaryResult:
    def test_fields(self):
        result = SummaryResult(**MOCK_LLM_RESPONSE)
        assert result.candidate_overview != ""
        assert result.expression_score == 85
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_summary_gen.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement summary generation service**

`backend/app/services/summary_gen.py`:

```python
import json
from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class SummaryResult:
    candidate_overview: str = ""
    expression_score: float = 0
    case_richness_score: float = 0
    depth_score: float = 0
    self_awareness_score: float = 0
    enthusiasm_score: float = 0
    overall_score: float = 0
    highlights: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    jd_alignment: list[dict] = field(default_factory=list)
    recommendation: str = "待定"
    recommendation_reason: str = ""
    next_steps: str = ""


SUMMARY_SYSTEM_PROMPT = """你是一位资深HR，需要根据完整面试转录生成结构化面试总结报告。

评估维度（每项0-100分）：
- expression_score: 表达清晰度（逻辑是否清楚、言之有物）
- case_richness_score: 案例丰富度（是否用具体案例支撑观点）
- depth_score: 思维深度（分析问题的层次和全面性）
- self_awareness_score: 自我认知（对自身优劣势的真实认知）
- enthusiasm_score: 岗位热情（对岗位和公司的了解和兴趣）
- overall_score: 综合评分

recommendation 取值：推荐 / 待定 / 不推荐

返回JSON格式：
{
  "candidate_overview": "一段话总结候选人",
  "expression_score": number,
  "case_richness_score": number,
  "depth_score": number,
  "self_awareness_score": number,
  "enthusiasm_score": number,
  "overall_score": number,
  "highlights": ["亮点1", "亮点2", "亮点3"],
  "concerns": ["顾虑点1", "顾虑点2"],
  "jd_alignment": [
    {"requirement": "JD要求项", "status": "达成/部分达成/未达成", "note": "说明"}
  ],
  "recommendation": "推荐/待定/不推荐",
  "recommendation_reason": "推荐理由",
  "next_steps": "后续建议（下一轮重点考察方向）"
}"""


class SummaryGenService:
    def __init__(self, llm_client: LLMClient | None = None):
        self._llm = llm_client

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._llm

    async def _call_llm(self, prompt: str) -> dict:
        llm = self._get_llm()
        return await llm.chat_json(
            prompt=prompt,
            model=settings.openai_model_strong,
            system=SUMMARY_SYSTEM_PROMPT,
        )

    async def generate(
        self,
        transcript: str,
        jd_text: str,
        resume_text: str = "",
        match_data: dict | None = None,
    ) -> SummaryResult:
        prompt = f"## 岗位JD\n{jd_text}\n\n## 完整面试转录\n{transcript}"
        if resume_text:
            prompt += f"\n\n## 候选人简历（脱敏）\n{resume_text}"
        if match_data:
            prompt += f"\n\n## 简历匹配评分\n{json.dumps(match_data, ensure_ascii=False)}"

        data = await self._call_llm(prompt)
        return SummaryResult(
            candidate_overview=data.get("candidate_overview", ""),
            expression_score=data.get("expression_score", 0),
            case_richness_score=data.get("case_richness_score", 0),
            depth_score=data.get("depth_score", 0),
            self_awareness_score=data.get("self_awareness_score", 0),
            enthusiasm_score=data.get("enthusiasm_score", 0),
            overall_score=data.get("overall_score", 0),
            highlights=data.get("highlights", []),
            concerns=data.get("concerns", []),
            jd_alignment=data.get("jd_alignment", []),
            recommendation=data.get("recommendation", "待定"),
            recommendation_reason=data.get("recommendation_reason", ""),
            next_steps=data.get("next_steps", ""),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_summary_gen.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: interview summary generation service"
```

---

### Task 9: PDF Export Service

**Files:**
- Create: `backend/app/services/pdf_export.py`
- Create: `backend/tests/test_pdf_export.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_pdf_export.py`:

```python
import json
import os

import pytest

from app.services.pdf_export import PDFExportService


class TestPDFExport:
    def test_generates_pdf_file(self, tmp_path):
        service = PDFExportService()
        output_path = str(tmp_path / "report.pdf")
        service.export(
            output_path=output_path,
            candidate_codename="候选人A",
            position_title="产品经理",
            interview_date="2026-04-10",
            duration_minutes=45,
            candidate_overview="候选人表现良好，有丰富的产品经验。",
            scores={
                "表达清晰度": 85,
                "案例丰富度": 78,
                "思维深度": 80,
                "自我认知": 72,
                "岗位热情": 88,
                "综合评分": 81,
            },
            highlights=["数据驱动", "表达清晰"],
            concerns=["管理经验不足"],
            jd_alignment=[
                {"requirement": "用户增长", "status": "达成", "note": "有直接经验"},
            ],
            recommendation="推荐",
            recommendation_reason="核心能力匹配度高",
            next_steps="二面重点考察管理能力",
        )
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_pdf_contains_basic_structure(self, tmp_path):
        service = PDFExportService()
        output_path = str(tmp_path / "report.pdf")
        service.export(
            output_path=output_path,
            candidate_codename="候选人B",
            position_title="运营经理",
            interview_date="2026-04-10",
            duration_minutes=30,
            candidate_overview="表现一般。",
            scores={"综合评分": 60},
            highlights=["沟通能力"],
            concerns=[],
            jd_alignment=[],
            recommendation="待定",
            recommendation_reason="需要更多信息",
            next_steps="",
        )
        with open(output_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pdf_export.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement PDF export service**

`backend/app/services/pdf_export.py`:

```python
import os

from fpdf import FPDF


class PDFExportService:
    def __init__(self):
        self._font_path = self._find_cjk_font()

    def _find_cjk_font(self) -> str | None:
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def export(
        self,
        output_path: str,
        candidate_codename: str,
        position_title: str,
        interview_date: str,
        duration_minutes: int,
        candidate_overview: str,
        scores: dict[str, float],
        highlights: list[str],
        concerns: list[str],
        jd_alignment: list[dict],
        recommendation: str,
        recommendation_reason: str,
        next_steps: str,
    ):
        pdf = FPDF()
        pdf.add_page()

        if self._font_path:
            pdf.add_font("CJK", "", self._font_path, uni=True)
            pdf.set_font("CJK", size=18)
        else:
            pdf.set_font("Helvetica", size=18)

        pdf.cell(0, 12, text="Interview Summary Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)

        self._set_body_font(pdf, 11)
        pdf.cell(0, 8, text=f"Candidate: {candidate_codename}  |  Position: {position_title}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, text=f"Date: {interview_date}  |  Duration: {duration_minutes} min  |  Recommendation: {recommendation}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        self._section_header(pdf, "Candidate Overview")
        self._set_body_font(pdf, 10)
        pdf.multi_cell(0, 6, text=candidate_overview)
        pdf.ln(3)

        self._section_header(pdf, "Scores")
        self._set_body_font(pdf, 10)
        for label, score in scores.items():
            pdf.cell(0, 7, text=f"  {label}: {score}/100", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        if highlights:
            self._section_header(pdf, "Highlights")
            self._set_body_font(pdf, 10)
            for h in highlights:
                pdf.cell(0, 7, text=f"  + {h}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        if concerns:
            self._section_header(pdf, "Concerns")
            self._set_body_font(pdf, 10)
            for c in concerns:
                pdf.cell(0, 7, text=f"  - {c}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        if jd_alignment:
            self._section_header(pdf, "JD Alignment")
            self._set_body_font(pdf, 10)
            for item in jd_alignment:
                req = item.get("requirement", "")
                status = item.get("status", "")
                note = item.get("note", "")
                pdf.cell(0, 7, text=f"  [{status}] {req}: {note}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

        self._section_header(pdf, "Recommendation")
        self._set_body_font(pdf, 10)
        pdf.multi_cell(0, 6, text=f"{recommendation}: {recommendation_reason}")
        pdf.ln(3)

        if next_steps:
            self._section_header(pdf, "Next Steps")
            self._set_body_font(pdf, 10)
            pdf.multi_cell(0, 6, text=next_steps)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)

    def _section_header(self, pdf: FPDF, text: str):
        if self._font_path:
            pdf.set_font("CJK", size=13)
        else:
            pdf.set_font("Helvetica", "B", size=13)
        pdf.cell(0, 9, text=text, new_x="LMARGIN", new_y="NEXT")

    def _set_body_font(self, pdf: FPDF, size: int):
        if self._font_path:
            pdf.set_font("CJK", size=size)
        else:
            pdf.set_font("Helvetica", size=size)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_pdf_export.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: PDF export service for interview summary reports"
```

---

### Task 10: Summary API Router

**Files:**
- Create: `backend/app/routers/summaries.py`
- Create: `backend/tests/test_api_summaries.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_api_summaries.py`:

```python
import io
import json
from unittest.mock import patch, AsyncMock

import pytest
from docx import Document

from app.services.summary_gen import SummaryResult


MOCK_SUMMARY = SummaryResult(
    candidate_overview="候选人表现良好",
    expression_score=85,
    case_richness_score=78,
    depth_score=80,
    self_awareness_score=72,
    enthusiasm_score=88,
    overall_score=81,
    highlights=["表达清晰"],
    concerns=["管理经验不足"],
    jd_alignment=[{"requirement": "增长", "status": "达成", "note": "有经验"}],
    recommendation="推荐",
    recommendation_reason="匹配度高",
    next_steps="考察管理能力",
)


def _setup_interview(client) -> int:
    resp = client.post("/api/positions", json={
        "title": "产品经理", "jd_text": "负责用户增长",
    })
    pid = resp.json()["id"]

    doc = Document()
    doc.add_paragraph("张三 产品经理")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    resp = client.post(
        f"/api/candidates/upload?position_id={pid}",
        files={"file": ("r.docx", buf.read(), "application/octet-stream")},
    )
    cid = resp.json()["id"]

    resp = client.post("/api/interviews", json={
        "position_id": pid, "candidate_id": cid,
    })
    return resp.json()["id"]


class TestGenerateSummary:
    @patch("app.routers.summaries.SummaryGenService")
    def test_generates_summary(self, MockService, client):
        mock_svc = MockService.return_value
        mock_svc.generate = AsyncMock(return_value=MOCK_SUMMARY)

        iid = _setup_interview(client)
        resp = client.post(f"/api/summaries/{iid}/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_score"] == 81
        assert data["recommendation"] == "推荐"


class TestGetSummary:
    @patch("app.routers.summaries.SummaryGenService")
    def test_gets_summary(self, MockService, client):
        mock_svc = MockService.return_value
        mock_svc.generate = AsyncMock(return_value=MOCK_SUMMARY)

        iid = _setup_interview(client)
        client.post(f"/api/summaries/{iid}/generate")
        resp = client.get(f"/api/summaries/{iid}")
        assert resp.status_code == 200
        assert resp.json()["overall_score"] == 81
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_summaries.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement summaries router**

`backend/app/routers/summaries.py`:

```python
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


@router.post("/{interview_id}/pdf")
def export_pdf(interview_id: int, db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(
        Summary.interview_id == interview_id
    ).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    interview = db.get(Interview, interview_id)
    codename = interview.candidate.codename if interview and interview.candidate else "Unknown"
    position_title = interview.position.title if interview and interview.position else "Unknown"
    interview_date = (
        interview.started_at.strftime("%Y-%m-%d") if interview and interview.started_at
        else interview.created_at.strftime("%Y-%m-%d") if interview and interview.created_at
        else "N/A"
    )
    duration_min = (interview.duration_seconds // 60) if interview else 0

    os.makedirs("./exports", exist_ok=True)
    pdf_path = f"./exports/interview_{interview_id}_summary.pdf"

    service = PDFExportService()
    service.export(
        output_path=pdf_path,
        candidate_codename=codename,
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
    )

    summary.pdf_path = pdf_path
    db.commit()

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{codename}_{position_title}_面试总结.pdf",
    )


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
```

- [ ] **Step 4: Mount summaries router in main.py**

Add to `backend/app/main.py` after existing router imports:

```python
from app.routers.summaries import router as summaries_router
```

Add after existing `app.include_router` calls:

```python
app.include_router(summaries_router)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api_summaries.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: summary generation and PDF export API endpoints"
```

---

### Task 11: Frontend — API Client & Types Extension

**Files:**
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add interview and summary types/methods to API client**

Add these interfaces and API methods to `frontend/src/api/client.ts` after the existing `QuestionSet` interface:

```typescript
export interface Interview {
  id: number;
  position_id: number;
  candidate_id: number;
  status: string;
  questions_json: string;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number;
  created_at: string;
  candidate_codename: string;
  position_title: string;
  has_summary: boolean;
}

export interface TranscriptEntry {
  id: number;
  speaker: string;
  sanitized_text: string;
  timestamp: number;
  duration: number;
}

export interface InterviewSummary {
  id: number;
  interview_id: number;
  candidate_overview: string;
  expression_score: number;
  case_richness_score: number;
  depth_score: number;
  self_awareness_score: number;
  enthusiasm_score: number;
  overall_score: number;
  highlights: string;
  concerns: string;
  jd_alignment: string;
  recommendation: string;
  recommendation_reason: string;
  next_steps: string;
  pdf_path: string;
  created_at: string;
}

export interface WsTranscript {
  type: "transcript";
  speaker: string;
  text: string;
  timestamp: number;
}

export interface WsAnalysis {
  type: "analysis";
  current_question_index: number;
  elements_checked: string[];
  follow_up_suggestions: string[];
  instant_rating: string;
  instant_comment: string;
}

export type WsMessage = WsTranscript | WsAnalysis | { type: "error"; message: string } | { type: "question_switched"; current_question_index: number };
```

Add to the `api` object after the existing `matches` section:

```typescript
  interviews: {
    list: (candidateId?: number, positionId?: number) => {
      const params = new URLSearchParams();
      if (candidateId) params.set("candidate_id", String(candidateId));
      if (positionId) params.set("position_id", String(positionId));
      return request<Interview[]>(`/interviews?${params}`);
    },
    get: (id: number) => request<Interview>(`/interviews/${id}`),
    create: (data: { position_id: number; candidate_id: number; questions_json?: string }) =>
      request<Interview>("/interviews", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    start: (id: number) =>
      request<Interview>(`/interviews/${id}/start`, { method: "POST" }),
    end: (id: number) =>
      request<Interview>(`/interviews/${id}/end`, { method: "POST" }),
    createSession: (id: number) =>
      request<{ status: string }>(`/interviews/${id}/session`, { method: "POST" }),
    stopSession: (id: number) =>
      request<{ status: string }>(`/interviews/${id}/session/stop`, { method: "POST" }),
    getTranscripts: (id: number) =>
      request<TranscriptEntry[]>(`/interviews/${id}/transcripts`),
  },
  summaries: {
    get: (interviewId: number) =>
      request<InterviewSummary>(`/summaries/${interviewId}`),
    generate: (interviewId: number) =>
      request<InterviewSummary>(`/summaries/${interviewId}/generate`, {
        method: "POST",
      }),
    exportPdf: (interviewId: number) =>
      `${BASE}/summaries/${interviewId}/pdf`,
  },
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: frontend API client with interview and summary types"
```

---

### Task 12: Frontend — Interview Live Page (Three-Panel UI)

**Files:**
- Create: `frontend/src/pages/InterviewLive.tsx`

- [ ] **Step 1: Create the three-panel interview UI**

`frontend/src/pages/InterviewLive.tsx`:

```tsx
import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Interview, WsMessage, QuestionItem } from "../api/client";

interface TranscriptLine {
  speaker: string;
  text: string;
  timestamp: number;
}

interface Suggestion {
  text: string;
  timestamp: number;
  isNew: boolean;
}

export default function InterviewLive() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [questions, setQuestions] = useState<(QuestionItem & { index: number })[]>([]);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [transcripts, setTranscripts] = useState<TranscriptLine[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [elementsChecked, setElementsChecked] = useState<string[]>([]);
  const [instantRating, setInstantRating] = useState("");
  const [instantComment, setInstantComment] = useState("");
  const [connected, setConnected] = useState(false);
  const [audioActive, setAudioActive] = useState(false);
  const [manualText, setManualText] = useState("");
  const [manualSpeaker, setManualSpeaker] = useState<"interviewer" | "candidate">("candidate");
  const [elapsed, setElapsed] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number>();

  useEffect(() => {
    if (!id) return;
    api.interviews.get(Number(id)).then((iv) => {
      setInterview(iv);
      if (iv.questions_json) {
        try {
          const qs = JSON.parse(iv.questions_json);
          const allQs: (QuestionItem & { index: number })[] = [];
          const sections = ["opening", "experience_verification", "competency", "risk_probing", "culture_fit"];
          if (Array.isArray(qs)) {
            qs.forEach((q: QuestionItem, i: number) => allQs.push({ ...q, index: i }));
          } else {
            let idx = 0;
            for (const section of sections) {
              if (qs[section]) {
                for (const q of qs[section]) {
                  allQs.push({ ...q, index: idx++ });
                }
              }
            }
          }
          setQuestions(allQs);
        } catch { /* ignore parse errors */ }
      }
    });
  }, [id]);

  const connectWs = useCallback(() => {
    if (!id) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/interview/${id}`);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data);
      if (msg.type === "transcript") {
        setTranscripts((prev) => [...prev, {
          speaker: msg.speaker,
          text: msg.text,
          timestamp: msg.timestamp,
        }]);
      } else if (msg.type === "analysis") {
        setCurrentQIndex(msg.current_question_index);
        setElementsChecked(msg.elements_checked);
        if (msg.follow_up_suggestions.length > 0) {
          const now = Date.now();
          setSuggestions((prev) => {
            const updated = prev.map((s) => ({ ...s, isNew: false }));
            const newOnes = msg.follow_up_suggestions.map((text) => ({
              text,
              timestamp: now,
              isNew: true,
            }));
            return [...newOnes, ...updated];
          });
        }
        if (msg.instant_rating) setInstantRating(msg.instant_rating);
        if (msg.instant_comment) setInstantComment(msg.instant_comment);
      } else if (msg.type === "question_switched") {
        setCurrentQIndex(msg.current_question_index);
      }
    };
    wsRef.current = ws;
  }, [id]);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcripts]);

  const handleStartInterview = async () => {
    if (!id) return;
    await api.interviews.createSession(Number(id));
    await api.interviews.start(Number(id));
    setInterview((prev) => prev ? { ...prev, status: "in_progress" } : prev);
    connectWs();
    timerRef.current = window.setInterval(() => setElapsed((e) => e + 1), 1000);
  };

  const handleStartAudio = () => {
    wsRef.current?.send(JSON.stringify({ type: "start_audio" }));
    setAudioActive(true);
  };

  const handleEndInterview = async () => {
    if (!id) return;
    if (timerRef.current) clearInterval(timerRef.current);
    await api.interviews.end(Number(id));
    await api.interviews.stopSession(Number(id));
    wsRef.current?.close();
    navigate(`/interviews/${id}/summary`);
  };

  const handleManualInput = () => {
    if (!manualText.trim() || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({
      type: "manual_input",
      speaker: manualSpeaker,
      text: manualText,
    }));
    setManualText("");
  };

  const handleSwitchQuestion = (index: number) => {
    setCurrentQIndex(index);
    wsRef.current?.send(JSON.stringify({ type: "switch_question", index }));
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (!interview) return <div className="text-gray-500">Loading...</div>;

  const ratingColor: Record<string, string> = {
    "好": "text-green-600",
    "一般": "text-yellow-600",
    "差": "text-red-600",
  };

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <span className="font-semibold text-gray-900">{interview.candidate_codename}</span>
          <span className="text-sm text-gray-500">{interview.position_title}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${connected ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
            {connected ? "已连接" : "未连接"}
          </span>
          {audioActive && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 animate-pulse">
              录音中
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-lg text-gray-700">{formatTime(elapsed)}</span>
          {interview.status !== "in_progress" ? (
            <button
              onClick={handleStartInterview}
              className="px-4 py-1.5 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
            >
              开始面试
            </button>
          ) : (
            <>
              {!audioActive && (
                <button
                  onClick={handleStartAudio}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                >
                  启动音频
                </button>
              )}
              <button
                onClick={handleEndInterview}
                className="px-4 py-1.5 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700"
              >
                结束面试
              </button>
            </>
          )}
        </div>
      </div>

      {/* Three-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Transcription */}
        <div className="w-1/3 border-r border-gray-200 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            实时转录
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {transcripts.map((t, i) => (
              <div key={i} className={`text-sm ${t.speaker === "interviewer" ? "text-blue-700" : "text-orange-700"}`}>
                <span className="text-xs text-gray-400 mr-2">{formatTime(Math.round(t.timestamp))}</span>
                <span className="font-medium">{t.speaker === "interviewer" ? "面试官" : "候选人"}:</span>
                {" "}{t.text}
              </div>
            ))}
            <div ref={transcriptEndRef} />
          </div>
          {/* Manual Input */}
          {connected && (
            <div className="border-t border-gray-200 p-2 flex gap-2">
              <select
                value={manualSpeaker}
                onChange={(e) => setManualSpeaker(e.target.value as "interviewer" | "candidate")}
                className="text-xs border border-gray-300 rounded px-1"
              >
                <option value="interviewer">面试官</option>
                <option value="candidate">候选人</option>
              </select>
              <input
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleManualInput()}
                placeholder="手动输入..."
                className="flex-1 text-sm border border-gray-300 rounded px-2 py-1"
              />
              <button
                onClick={handleManualInput}
                className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                发送
              </button>
            </div>
          )}
        </div>

        {/* Center: Question Checklist */}
        <div className="w-1/3 border-r border-gray-200 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            问题清单 & 要素检查
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {questions.map((q, i) => {
              const isCurrent = i === currentQIndex;
              const isPast = i < currentQIndex;
              return (
                <div
                  key={i}
                  onClick={() => handleSwitchQuestion(i)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isCurrent
                      ? "border-blue-400 bg-blue-50 shadow-sm"
                      : isPast
                        ? "border-gray-200 bg-gray-50 opacity-60"
                        : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <p className={`text-sm font-medium ${isCurrent ? "text-blue-900" : "text-gray-700"}`}>
                    {q.question}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{q.purpose}</p>
                  {isCurrent && q.good_answer_elements && (
                    <div className="mt-2 space-y-1">
                      {q.good_answer_elements.map((el, j) => {
                        const checked = elementsChecked.includes(el);
                        return (
                          <div key={j} className="flex items-center gap-1.5">
                            <span className={`text-xs ${checked ? "text-green-600" : "text-gray-400"}`}>
                              {checked ? "✓" : "○"}
                            </span>
                            <span className={`text-xs ${checked ? "text-green-700" : "text-gray-500"}`}>
                              {el}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  {isCurrent && instantRating && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className={`text-xs font-semibold ${ratingColor[instantRating] || "text-gray-600"}`}>
                        {instantRating}
                      </span>
                      {instantComment && (
                        <span className="text-xs text-gray-500">{instantComment}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Suggestions */}
        <div className="w-1/3 flex flex-col bg-white">
          <div className="px-3 py-2 border-b border-gray-100 text-sm font-semibold text-gray-700">
            追问建议
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {suggestions.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                面试开始后，AI 将在此处提供追问建议
              </div>
            ) : (
              suggestions.map((s, i) => (
                <div
                  key={`${s.timestamp}-${i}`}
                  className={`p-3 rounded-lg border transition-all ${
                    s.isNew
                      ? "border-blue-300 bg-blue-50 shadow-sm"
                      : "border-gray-200 bg-gray-50 text-sm opacity-80"
                  }`}
                >
                  <p className={s.isNew ? "text-sm text-blue-900 font-medium" : "text-xs text-gray-600"}>
                    {s.text}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: three-panel real-time interview UI"
```

---

### Task 13: Frontend — Interview Summary Page

**Files:**
- Create: `frontend/src/pages/InterviewSummary.tsx`

- [ ] **Step 1: Create the summary page**

`frontend/src/pages/InterviewSummary.tsx`:

```tsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Interview, InterviewSummary as SummaryType } from "../api/client";
import ScoreBadge from "../components/ScoreBadge";

export default function InterviewSummary() {
  const { id } = useParams<{ id: string }>();
  const [interview, setInterview] = useState<Interview | null>(null);
  const [summary, setSummary] = useState<SummaryType | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!id) return;
    const iid = Number(id);
    api.interviews.get(iid).then(setInterview);
    api.summaries.get(iid).then(setSummary).catch(() => setSummary(null));
  }, [id]);

  const handleGenerate = async () => {
    if (!id) return;
    setGenerating(true);
    try {
      const s = await api.summaries.generate(Number(id));
      setSummary(s);
    } finally {
      setGenerating(false);
    }
  };

  const handleExportPdf = () => {
    if (!id) return;
    window.open(api.summaries.exportPdf(Number(id)), "_blank");
  };

  if (!interview) return <div className="text-gray-500">Loading...</div>;

  const recStyle: Record<string, string> = {
    "推荐": "bg-green-100 text-green-800 border-green-200",
    "待定": "bg-yellow-100 text-yellow-800 border-yellow-200",
    "不推荐": "bg-red-100 text-red-800 border-red-200",
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to={`/candidates/${interview.candidate_id}`} className="text-sm text-blue-600 hover:text-blue-800">
            &larr; 返回候选人
          </Link>
          <h2 className="text-xl font-bold text-gray-900 mt-2">
            面试总结 — {interview.candidate_codename}
          </h2>
          <p className="text-sm text-gray-500">
            {interview.position_title} | {interview.duration_seconds > 0 ? `${Math.round(interview.duration_seconds / 60)} 分钟` : "N/A"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
          >
            {generating ? "生成中..." : summary ? "重新生成" : "生成总结"}
          </button>
          {summary && (
            <button
              onClick={handleExportPdf}
              className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700"
            >
              导出 PDF
            </button>
          )}
        </div>
      </div>

      {summary ? (
        <div className="space-y-6">
          {/* Recommendation Badge */}
          <div className="flex items-center gap-3">
            <span className={`px-4 py-1.5 rounded-full text-sm font-semibold border ${recStyle[summary.recommendation] || "bg-gray-100"}`}>
              {summary.recommendation}
            </span>
          </div>

          {/* Overview */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-2">候选人概要</h3>
            <p className="text-sm text-gray-700">{summary.candidate_overview}</p>
          </div>

          {/* Scores */}
          <div className="grid grid-cols-2 lg:grid-cols-6 gap-3">
            <ScoreBadge score={summary.expression_score} label="表达清晰度" />
            <ScoreBadge score={summary.case_richness_score} label="案例丰富度" />
            <ScoreBadge score={summary.depth_score} label="思维深度" />
            <ScoreBadge score={summary.self_awareness_score} label="自我认知" />
            <ScoreBadge score={summary.enthusiasm_score} label="岗位热情" />
            <ScoreBadge score={summary.overall_score} label="综合评分" />
          </div>

          {/* Highlights & Concerns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="font-medium text-green-800 mb-2">亮点</h4>
              <ul className="text-sm text-green-700 space-y-1">
                {JSON.parse(summary.highlights || "[]").map((h: string, i: number) => (
                  <li key={i}>• {h}</li>
                ))}
              </ul>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <h4 className="font-medium text-red-800 mb-2">顾虑点</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {JSON.parse(summary.concerns || "[]").map((c: string, i: number) => (
                  <li key={i}>• {c}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* JD Alignment */}
          {(() => {
            const alignment = JSON.parse(summary.jd_alignment || "[]");
            if (alignment.length === 0) return null;
            const statusColor: Record<string, string> = {
              "达成": "text-green-700 bg-green-100",
              "部分达成": "text-yellow-700 bg-yellow-100",
              "未达成": "text-red-700 bg-red-100",
            };
            return (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">JD 匹配分析</h3>
                <div className="space-y-2">
                  {alignment.map((item: { requirement: string; status: string; note: string }, i: number) => (
                    <div key={i} className="flex items-start gap-3">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ${statusColor[item.status] || "text-gray-600 bg-gray-100"}`}>
                        {item.status}
                      </span>
                      <div>
                        <span className="text-sm font-medium text-gray-800">{item.requirement}</span>
                        {item.note && <span className="text-sm text-gray-500 ml-2">{item.note}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}

          {/* Recommendation & Next Steps */}
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-2">推荐理由</h3>
            <p className="text-sm text-gray-700">{summary.recommendation_reason}</p>
          </div>

          {summary.next_steps && (
            <div className="bg-blue-50 rounded-xl border border-blue-200 p-5">
              <h3 className="font-semibold text-blue-900 mb-2">后续建议</h3>
              <p className="text-sm text-blue-700">{summary.next_steps}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center text-gray-500">
          <p className="text-lg mb-2">暂无面试总结</p>
          <p className="text-sm">点击「生成总结」基于面试转录自动生成结构化报告</p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: interview summary page with PDF export"
```

---

### Task 14: Frontend — Routes & Navigation Update

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/pages/CandidateDetail.tsx`

- [ ] **Step 1: Update App.tsx with new routes**

Replace `frontend/src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PositionList from "./pages/PositionList";
import PositionDetail from "./pages/PositionDetail";
import CandidateDetail from "./pages/CandidateDetail";
import InterviewLive from "./pages/InterviewLive";
import InterviewSummary from "./pages/InterviewSummary";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PositionList />} />
        <Route path="/positions/:id" element={<PositionDetail />} />
        <Route path="/candidates/:id" element={<CandidateDetail />} />
        <Route path="/interviews/:id/live" element={<InterviewLive />} />
        <Route path="/interviews/:id/summary" element={<InterviewSummary />} />
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 2: Add interview entry points to CandidateDetail.tsx**

Add a new section after the questions section in `frontend/src/pages/CandidateDetail.tsx`. Insert before the final closing `</div>` of the component:

```tsx
      {/* Start Interview */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">面试</h3>
          <button
            onClick={async () => {
              if (!id || !match) return;
              const questionsJson = match.questions || "[]";
              const iv = await api.interviews.create({
                position_id: candidate!.position_id,
                candidate_id: Number(id),
                questions_json: questionsJson,
              });
              window.location.href = `/interviews/${iv.id}/live`;
            }}
            disabled={!match}
            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors"
          >
            开始面试
          </button>
        </div>
      </div>
```

Add the import for `api` if not already present (it should be).

- [ ] **Step 3: Verify frontend builds**

```bash
cd /Users/yinjun/interview/frontend
npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 4: Commit**

```bash
cd /Users/yinjun/interview
git add -A
git commit -m "feat: interview routes, navigation, and candidate detail integration"
```

---

### Task 15: End-to-End Verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 2: Verify frontend builds**

```bash
cd /Users/yinjun/interview/frontend
npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 3: Start backend and verify health**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
sleep 2
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok"}`

- [ ] **Step 4: Commit final state**

```bash
git add -A
git commit -m "chore: Phase 2 complete — real-time interview and summary"
```

---

## Phase 3 Preview (not in this plan)

Phase 3 will cover: SQLCipher encrypted database, auto data cleanup, DingTalk/Feishu webhook integration (resume receiving + summary push), speaker diarization improvements, and candidate comparison views.
