# Interview Assistant Phase 1: Foundation & Pre-Interview Preparation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core backend and minimal frontend for the pre-interview preparation workflow — from resume upload through matching scores to interview question generation.

**Architecture:** Python FastAPI backend with SQLite database, serving a React frontend. Resume files are parsed locally, PII is masked before any LLM call, and an OpenAI-compatible gateway handles AI analysis. Frontend is a SPA communicating via REST API.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, SQLite, PyMuPDF, python-docx, OpenAI SDK, React 18, TypeScript, Vite, Tailwind CSS 4, React Router 7

---

## File Structure

```
interview/
├── backend/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app + CORS + router mounting
│   │   ├── config.py                # Pydantic Settings
│   │   ├── database.py              # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── __init__.py          # Base + re-exports
│   │   │   ├── position.py          # Position table
│   │   │   ├── candidate.py         # Candidate table
│   │   │   └── resume_match.py      # ResumeMatch table
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── position.py          # Position request/response schemas
│   │   │   ├── candidate.py         # Candidate schemas
│   │   │   └── resume_match.py      # Match score schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── positions.py         # /api/positions CRUD
│   │   │   ├── candidates.py        # /api/candidates + resume upload
│   │   │   └── matches.py           # /api/matches + question generation
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── pii_masking.py       # PII detection & masking
│   │       ├── resume_parser.py     # PDF/Word parsing
│   │       ├── llm_client.py        # OpenAI-compatible client
│   │       ├── matching.py          # Resume-JD matching scorer
│   │       └── question_gen.py      # Interview question generator
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # Shared fixtures (db session, client)
│       ├── test_pii_masking.py
│       ├── test_resume_parser.py
│       ├── test_llm_client.py
│       ├── test_matching.py
│       ├── test_question_gen.py
│       ├── test_api_positions.py
│       ├── test_api_candidates.py
│       └── test_api_matches.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── postcss.config.js
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css                # Tailwind imports
│       ├── api/
│       │   └── client.ts            # Typed API client
│       ├── components/
│       │   ├── Layout.tsx            # App shell with sidebar
│       │   └── ScoreBadge.tsx        # Reusable score display
│       └── pages/
│           ├── PositionList.tsx      # Position CRUD page
│           ├── PositionDetail.tsx    # Single position + candidates
│           ├── CandidateDetail.tsx   # Match scores + questions
│           └── InterviewPrep.tsx     # Question list management
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

---

### Task 1: Project Scaffolding — Backend

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/yinjun/interview
git init
```

Create `.gitignore`:

```gitignore
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.env
*.db
*.sqlite
node_modules/
frontend/dist/
.venv/
venv/
.superpowers/
```

- [ ] **Step 2: Create backend dependency files**

`backend/requirements.txt`:

```
fastapi==0.115.12
uvicorn[standard]==0.34.2
sqlalchemy==2.0.40
pydantic==2.11.1
pydantic-settings==2.8.1
python-multipart==0.0.20
openai==1.75.0
pymupdf==1.25.5
python-docx==1.1.2
httpx==0.28.1
pytest==8.3.5
pytest-asyncio==0.26.0
```

`backend/pyproject.toml`:

```toml
[project]
name = "interview-assistant"
version = "0.1.0"
description = "Local interview assistant with AI-powered resume matching and real-time assistance"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 3: Create config module**

`backend/app/__init__.py`: empty file

`backend/app/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./interview.db"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_fast: str = "gpt-4o-mini"
    openai_model_strong: str = "gpt-4o"
    upload_dir: str = "./uploads"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "INTERVIEW_", "env_file": ".env"}


settings = Settings()
```

- [ ] **Step 4: Create FastAPI app entry point**

`backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Interview Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 5: Create test fixtures**

`backend/tests/__init__.py`: empty file

`backend/tests/conftest.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd /Users/yinjun/interview/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run: `python -c "from app.main import app; print(app.title)"`
Expected: `Interview Assistant`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: project scaffolding with FastAPI backend"
```

---

### Task 2: Database Models & Session

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/position.py`
- Create: `backend/app/models/candidate.py`
- Create: `backend/app/models/resume_match.py`

- [ ] **Step 1: Create database module**

`backend/app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 2: Create Position model**

`backend/app/models/position.py`:

```python
import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PositionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    PAUSED = "paused"


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    department: Mapped[str] = mapped_column(String(100), default="")
    jd_text: Mapped[str] = mapped_column(Text)
    core_competencies: Mapped[str] = mapped_column(Text, default="")
    preferences: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[PositionStatus] = mapped_column(
        Enum(PositionStatus), default=PositionStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="position")
```

- [ ] **Step 3: Create Candidate model**

`backend/app/models/candidate.py`:

```python
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    codename: Mapped[str] = mapped_column(String(50))
    resume_file_path: Mapped[str] = mapped_column(String(500), default="")
    resume_raw_text: Mapped[str] = mapped_column(Text, default="")
    resume_sanitized_text: Mapped[str] = mapped_column(Text, default="")
    structured_info: Mapped[str] = mapped_column(Text, default="{}")
    pii_mapping: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    position: Mapped["Position"] = relationship(back_populates="candidates")
    match: Mapped["ResumeMatch | None"] = relationship(
        back_populates="candidate", uselist=False
    )
```

- [ ] **Step 4: Create ResumeMatch model**

`backend/app/models/resume_match.py`:

```python
from datetime import datetime

from sqlalchemy import Integer, Float, Text, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResumeMatch(Base):
    __tablename__ = "resume_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), unique=True
    )
    experience_score: Mapped[float] = mapped_column(Float, default=0)
    experience_note: Mapped[str] = mapped_column(Text, default="")
    industry_score: Mapped[float] = mapped_column(Float, default=0)
    industry_note: Mapped[str] = mapped_column(Text, default="")
    competency_score: Mapped[float] = mapped_column(Float, default=0)
    competency_note: Mapped[str] = mapped_column(Text, default="")
    potential_score: Mapped[float] = mapped_column(Float, default=0)
    potential_note: Mapped[str] = mapped_column(Text, default="")
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(
        String(20), default="pending"
    )
    highlights: Mapped[str] = mapped_column(Text, default="[]")
    risks: Mapped[str] = mapped_column(Text, default="[]")
    questions: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="match")
```

- [ ] **Step 5: Create models __init__ and wire up**

`backend/app/models/__init__.py`:

```python
from app.database import Base
from app.models.position import Position, PositionStatus
from app.models.candidate import Candidate
from app.models.resume_match import ResumeMatch

__all__ = ["Base", "Position", "PositionStatus", "Candidate", "ResumeMatch"]
```

Update `backend/app/main.py` — add table creation at startup:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base

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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: Verify models load correctly**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
python -c "from app.models import Position, Candidate, ResumeMatch; print('Models loaded OK')"
```

Expected: `Models loaded OK`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: database models for Position, Candidate, ResumeMatch"
```

---

### Task 3: PII Masking Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/pii_masking.py`
- Create: `backend/tests/test_pii_masking.py`

- [ ] **Step 1: Write failing tests for PII masking**

`backend/app/services/__init__.py`: empty file

`backend/tests/test_pii_masking.py`:

```python
from app.services.pii_masking import PIIMasker


class TestPhoneNumber:
    def test_masks_chinese_mobile(self):
        masker = PIIMasker()
        text = "我的手机号是13812345678，请联系我"
        result = masker.mask(text)
        assert "13812345678" not in result
        assert "[手机号已移除]" in result

    def test_masks_phone_with_dashes(self):
        masker = PIIMasker()
        text = "电话：138-1234-5678"
        result = masker.mask(text)
        assert "138-1234-5678" not in result


class TestEmail:
    def test_masks_email(self):
        masker = PIIMasker()
        text = "邮箱：zhangsan@example.com"
        result = masker.mask(text)
        assert "zhangsan@example.com" not in result
        assert "[邮箱已移除]" in result


class TestIDCard:
    def test_masks_18_digit_id(self):
        masker = PIIMasker()
        text = "身份证号：110101199001011234"
        result = masker.mask(text)
        assert "110101199001011234" not in result
        assert "[身份证号已移除]" in result

    def test_masks_id_with_x(self):
        masker = PIIMasker()
        text = "身份证 11010119900101123X"
        result = masker.mask(text)
        assert "11010119900101123X" not in result


class TestName:
    def test_replaces_name_with_codename(self):
        masker = PIIMasker(codename="候选人A")
        text = "张三在2020年加入阿里巴巴"
        result = masker.mask(text, known_names=["张三"])
        assert "张三" not in result
        assert "候选人A" in result
        assert "阿里巴巴" in result

    def test_preserves_company_names(self):
        masker = PIIMasker()
        text = "在腾讯工作了5年，后来去了字节跳动"
        result = masker.mask(text)
        assert "腾讯" in result
        assert "字节跳动" in result


class TestAddress:
    def test_masks_address_pattern(self):
        masker = PIIMasker()
        text = "住址：北京市朝阳区建国路88号"
        result = masker.mask(text)
        assert "建国路88号" not in result
        assert "[地址已移除]" in result


class TestMappingTable:
    def test_returns_mapping(self):
        masker = PIIMasker(codename="候选人A")
        text = "张三的手机号13812345678"
        result = masker.mask(text, known_names=["张三"])
        mapping = masker.get_mapping()
        assert "张三" in str(mapping)
        assert "13812345678" in str(mapping)

    def test_restore_from_mapping(self):
        masker = PIIMasker(codename="候选人A")
        original = "张三的手机号13812345678"
        masked = masker.mask(original, known_names=["张三"])
        restored = masker.restore(masked)
        assert "张三" in restored
        assert "13812345678" in restored
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
pytest tests/test_pii_masking.py -v
```

Expected: All tests FAIL (module not found)

- [ ] **Step 3: Implement PII masking service**

`backend/app/services/pii_masking.py`:

```python
import re
from dataclasses import dataclass, field


@dataclass
class PIIMasker:
    codename: str = "候选人"
    _mapping: dict[str, str] = field(default_factory=dict)
    _reverse_mapping: dict[str, str] = field(default_factory=dict)

    PHONE_PATTERN = re.compile(
        r"1[3-9]\d[\-\s]?\d{4}[\-\s]?\d{4}"
    )
    EMAIL_PATTERN = re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    )
    ID_CARD_PATTERN = re.compile(
        r"\d{17}[\dXx]"
    )
    ADDRESS_PATTERN = re.compile(
        r"(?:住址|地址|家庭住址)[：:]\s*\S+"
    )

    def _record(self, original: str, replacement: str) -> str:
        self._mapping[original] = replacement
        self._reverse_mapping[replacement] = original
        return replacement

    def mask(self, text: str, known_names: list[str] | None = None) -> str:
        result = text

        for name in (known_names or []):
            replacement = self._record(name, self.codename)
            result = result.replace(name, replacement)

        def replace_phone(m: re.Match) -> str:
            return self._record(m.group(), "[手机号已移除]")

        def replace_email(m: re.Match) -> str:
            return self._record(m.group(), "[邮箱已移除]")

        def replace_id(m: re.Match) -> str:
            return self._record(m.group(), "[身份证号已移除]")

        result = self.PHONE_PATTERN.sub(replace_phone, result)
        result = self.EMAIL_PATTERN.sub(replace_email, result)
        result = self.ID_CARD_PATTERN.sub(replace_id, result)

        def replace_address(m: re.Match) -> str:
            return self._record(m.group(), "[地址已移除]")

        result = self.ADDRESS_PATTERN.sub(replace_address, result)

        return result

    def get_mapping(self) -> dict[str, str]:
        return dict(self._mapping)

    def restore(self, masked_text: str) -> str:
        result = masked_text
        for replacement, original in self._reverse_mapping.items():
            result = result.replace(replacement, original)
        return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_pii_masking.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: PII masking service with regex-based detection"
```

---

### Task 4: Resume Parsing Service

**Files:**
- Create: `backend/app/services/resume_parser.py`
- Create: `backend/tests/test_resume_parser.py`
- Create: `backend/tests/fixtures/` (test resume files)

- [ ] **Step 1: Create test fixture files**

Create a minimal test PDF and DOCX programmatically in conftest. Add to `backend/tests/conftest.py`:

```python
import os
import tempfile

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal PDF for testing."""
    import fitz  # PyMuPDF
    pdf_path = tmp_path / "resume.pdf"
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "张三\n"
        "手机：13812345678\n"
        "邮箱：zhangsan@example.com\n\n"
        "工作经历\n"
        "2020-2023 阿里巴巴 产品经理\n"
        "负责电商平台用户增长策略，DAU从500万提升至800万\n\n"
        "2018-2020 腾讯 产品运营\n"
        "负责微信支付商户运营\n\n"
        "教育背景\n"
        "2014-2018 北京大学 计算机科学与技术 本科\n\n"
        "技能\n"
        "数据分析、用户研究、项目管理、SQL、Python"
    )
    page.insert_text((72, 72), text, fontname="china-s", fontsize=11)
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


@pytest.fixture
def sample_docx(tmp_path):
    """Create a minimal DOCX for testing."""
    from docx import Document
    docx_path = tmp_path / "resume.docx"
    doc = Document()
    doc.add_heading("李四", level=1)
    doc.add_paragraph("手机：13900001111")
    doc.add_paragraph("邮箱：lisi@example.com")
    doc.add_heading("工作经历", level=2)
    doc.add_paragraph("2021-2023 字节跳动 运营经理")
    doc.add_paragraph("负责抖音电商直播运营，GMV同比增长200%")
    doc.add_heading("教育背景", level=2)
    doc.add_paragraph("2017-2021 清华大学 工商管理 本科")
    doc.save(str(docx_path))
    return str(docx_path)
```

- [ ] **Step 2: Write failing tests for resume parser**

`backend/tests/test_resume_parser.py`:

```python
import pytest

from app.services.resume_parser import ResumeParser


class TestPDFParsing:
    def test_extracts_text_from_pdf(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert result.raw_text != ""
        assert "产品经理" in result.raw_text

    def test_extracts_filename(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert result.file_name == "resume.pdf"


class TestDOCXParsing:
    def test_extracts_text_from_docx(self, sample_docx):
        parser = ResumeParser()
        result = parser.parse(sample_docx)
        assert result.raw_text != ""
        assert "运营经理" in result.raw_text


class TestUnsupportedFormat:
    def test_raises_for_unsupported(self, tmp_path):
        txt_path = tmp_path / "resume.txt"
        txt_path.write_text("some text")
        parser = ResumeParser()
        with pytest.raises(ValueError, match="Unsupported"):
            parser.parse(str(txt_path))


class TestParseResult:
    def test_result_has_required_fields(self, sample_pdf):
        parser = ResumeParser()
        result = parser.parse(sample_pdf)
        assert hasattr(result, "raw_text")
        assert hasattr(result, "file_name")
        assert hasattr(result, "file_type")
        assert result.file_type == "pdf"
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_resume_parser.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 4: Implement resume parser**

`backend/app/services/resume_parser.py`:

```python
import os
from dataclasses import dataclass


@dataclass
class ParseResult:
    raw_text: str
    file_name: str
    file_type: str


class ResumeParser:
    SUPPORTED_TYPES = {"pdf", "docx"}

    def parse(self, file_path: str) -> ParseResult:
        file_name = os.path.basename(file_path)
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

        if ext not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported file type: .{ext}. Supported: {self.SUPPORTED_TYPES}"
            )

        if ext == "pdf":
            text = self._parse_pdf(file_path)
        else:
            text = self._parse_docx(file_path)

        return ParseResult(raw_text=text, file_name=file_name, file_type=ext)

    def _parse_pdf(self, file_path: str) -> str:
        import fitz

        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n".join(pages).strip()

    def _parse_docx(self, file_path: str) -> str:
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_resume_parser.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: resume parser supporting PDF and DOCX"
```

---

### Task 5: LLM Client Service

**Files:**
- Create: `backend/app/services/llm_client.py`
- Create: `backend/tests/test_llm_client.py`

- [ ] **Step 1: Write failing tests for LLM client**

`backend/tests/test_llm_client.py`:

```python
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.llm_client import LLMClient


class TestLLMClient:
    def test_creates_with_config(self):
        client = LLMClient(
            api_key="test-key",
            base_url="https://test.com/v1",
        )
        assert client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_chat_returns_text(self):
        client = LLMClient(api_key="test-key", base_url="https://test.com/v1")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello!"))]

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.chat("Say hello", model="gpt-4o-mini")
            assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_json_mode(self):
        json_str = '{"score": 85, "note": "Good match"}'
        client = LLMClient(api_key="test-key", base_url="https://test.com/v1")
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json_str))]

        with patch.object(
            client._client.chat.completions,
            "create",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await client.chat_json(
                "Rate this", model="gpt-4o"
            )
            assert result["score"] == 85
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_llm_client.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement LLM client**

`backend/app/services/llm_client.py`:

```python
import json

from openai import AsyncOpenAI


class LLMClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.3,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        prompt: str,
        model: str,
        system: str = "",
        temperature: float = 0.1,
    ) -> dict:
        messages = []
        sys_msg = (system + "\n\n" if system else "") + "Respond with valid JSON only."
        messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or "{}"
        return json.loads(text)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm_client.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: OpenAI-compatible LLM client with JSON mode"
```

---

### Task 6: Resume Matching Service

**Files:**
- Create: `backend/app/services/matching.py`
- Create: `backend/tests/test_matching.py`

- [ ] **Step 1: Write failing tests for matching**

`backend/tests/test_matching.py`:

```python
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.matching import MatchingService, MatchResult


MOCK_LLM_RESPONSE = {
    "experience_score": 82,
    "experience_note": "3年产品经理经验，用户增长方向匹配度高",
    "industry_score": 75,
    "industry_note": "电商行业背景与目标岗位相关",
    "competency_score": 80,
    "competency_note": "数据分析和用户研究能力突出",
    "potential_score": 70,
    "potential_note": "学习能力强，但管理经验尚浅",
    "overall_score": 78,
    "recommendation": "推荐",
    "highlights": ["DAU提升60%的量化成果", "大厂经历"],
    "risks": ["跳槽频率偏高（2年一换）"],
}


class TestMatchingService:
    @pytest.mark.asyncio
    async def test_returns_match_result(self):
        service = MatchingService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.match(
                jd_text="招聘产品经理，负责用户增长",
                resume_text="3年产品经理经验，负责电商平台用户增长",
                preferences="",
            )
            assert isinstance(result, MatchResult)
            assert result.overall_score == 78
            assert result.recommendation == "推荐"
            assert len(result.highlights) >= 1
            assert len(result.risks) >= 1

    @pytest.mark.asyncio
    async def test_score_dimensions_are_in_range(self):
        service = MatchingService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.match(
                jd_text="JD text",
                resume_text="Resume text",
                preferences="",
            )
            for score in [
                result.experience_score,
                result.industry_score,
                result.competency_score,
                result.potential_score,
                result.overall_score,
            ]:
                assert 0 <= score <= 100


class TestMatchResultStructure:
    def test_match_result_fields(self):
        result = MatchResult(**MOCK_LLM_RESPONSE)
        assert result.experience_score == 82
        assert result.recommendation == "推荐"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_matching.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement matching service**

`backend/app/services/matching.py`:

```python
from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class MatchResult:
    experience_score: float
    experience_note: str
    industry_score: float
    industry_note: str
    competency_score: float
    competency_note: str
    potential_score: float
    potential_note: str
    overall_score: float
    recommendation: str
    highlights: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


MATCH_SYSTEM_PROMPT = """你是一位资深HR，擅长分析简历与岗位匹配度。请根据提供的JD和简历进行多维度评估。

评分标准（每项0-100分）：
- experience_score: 岗位经验匹配度
- industry_score: 行业背景相关性
- competency_score: 核心能力匹配度
- potential_score: 成长潜力评估
- overall_score: 综合推荐指数

recommendation 取值：推荐 / 待定 / 不推荐

返回JSON格式：
{
  "experience_score": number,
  "experience_note": "简短说明",
  "industry_score": number,
  "industry_note": "简短说明",
  "competency_score": number,
  "competency_note": "简短说明",
  "potential_score": number,
  "potential_note": "简短说明",
  "overall_score": number,
  "recommendation": "推荐/待定/不推荐",
  "highlights": ["亮点1", "亮点2"],
  "risks": ["风险1"]
}"""


class MatchingService:
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
            system=MATCH_SYSTEM_PROMPT,
        )

    async def match(
        self,
        jd_text: str,
        resume_text: str,
        preferences: str = "",
    ) -> MatchResult:
        prompt = f"## 岗位JD\n{jd_text}\n\n## 候选人简历（已脱敏）\n{resume_text}"
        if preferences:
            prompt += f"\n\n## 面试官偏好\n{preferences}"

        data = await self._call_llm(prompt)
        return MatchResult(
            experience_score=data.get("experience_score", 0),
            experience_note=data.get("experience_note", ""),
            industry_score=data.get("industry_score", 0),
            industry_note=data.get("industry_note", ""),
            competency_score=data.get("competency_score", 0),
            competency_note=data.get("competency_note", ""),
            potential_score=data.get("potential_score", 0),
            potential_note=data.get("potential_note", ""),
            overall_score=data.get("overall_score", 0),
            recommendation=data.get("recommendation", "待定"),
            highlights=data.get("highlights", []),
            risks=data.get("risks", []),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_matching.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: resume-JD matching service with LLM scoring"
```

---

### Task 7: Question Generation Service

**Files:**
- Create: `backend/app/services/question_gen.py`
- Create: `backend/tests/test_question_gen.py`

- [ ] **Step 1: Write failing tests**

`backend/tests/test_question_gen.py`:

```python
from unittest.mock import AsyncMock, patch

import pytest

from app.services.question_gen import QuestionGenService, QuestionSet, Question


MOCK_LLM_RESPONSE = {
    "opening": [
        {
            "question": "请简单介绍一下你自己和最近这份工作的主要内容？",
            "purpose": "了解表达能力和自我认知",
            "good_answer_elements": ["结构清晰", "重点突出", "与岗位相关"],
            "red_flags": ["冗长散乱", "与简历出入大"],
        }
    ],
    "experience_verification": [
        {
            "question": "你提到DAU从500万提升到800万，能详细说说你具体做了什么吗？",
            "purpose": "验证核心经历真实性和深度",
            "good_answer_elements": ["STAR法则", "量化数据", "个人贡献清晰"],
            "red_flags": ["无法说出细节", "全是团队功劳"],
        }
    ],
    "competency": [
        {
            "question": "如果让你从零开始搭建一个用户增长体系，你会怎么做？",
            "purpose": "考察体系化思维和方法论",
            "good_answer_elements": ["分阶段规划", "数据驱动", "具体落地方案"],
            "red_flags": ["纸上谈兵", "缺乏逻辑"],
        }
    ],
    "risk_probing": [
        {
            "question": "看到你平均两年换一次工作，能说说每次离职的原因吗？",
            "purpose": "了解稳定性和职业规划",
            "good_answer_elements": ["坦诚", "有合理逻辑", "有长期规划"],
            "red_flags": ["甩锅", "回避"],
        }
    ],
    "culture_fit": [
        {
            "question": "你理想中的团队氛围是什么样的？",
            "purpose": "评估团队适配性",
            "good_answer_elements": ["具体描述", "有自知之明"],
            "red_flags": ["假大空"],
        }
    ],
}


class TestQuestionGenService:
    @pytest.mark.asyncio
    async def test_generates_question_set(self):
        service = QuestionGenService()
        with patch.object(
            service, "_call_llm", new_callable=AsyncMock, return_value=MOCK_LLM_RESPONSE
        ):
            result = await service.generate(
                jd_text="招聘产品经理",
                resume_text="3年产品经理经验",
                match_highlights=["DAU提升60%"],
                match_risks=["跳槽频繁"],
                preferences="",
            )
            assert isinstance(result, QuestionSet)
            assert len(result.opening) >= 1
            assert len(result.experience_verification) >= 1
            assert len(result.competency) >= 1
            assert isinstance(result.opening[0], Question)
            assert result.opening[0].question != ""
            assert result.opening[0].purpose != ""


class TestQuestionStructure:
    def test_question_has_all_fields(self):
        q = Question(
            question="测试问题",
            purpose="测试目的",
            good_answer_elements=["要素1"],
            red_flags=["红旗1"],
        )
        assert q.question == "测试问题"
        assert len(q.good_answer_elements) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_question_gen.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement question generation service**

`backend/app/services/question_gen.py`:

```python
from dataclasses import dataclass, field

from app.services.llm_client import LLMClient
from app.config import settings


@dataclass
class Question:
    question: str
    purpose: str
    good_answer_elements: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)


@dataclass
class QuestionSet:
    opening: list[Question] = field(default_factory=list)
    experience_verification: list[Question] = field(default_factory=list)
    competency: list[Question] = field(default_factory=list)
    risk_probing: list[Question] = field(default_factory=list)
    culture_fit: list[Question] = field(default_factory=list)


QUESTION_SYSTEM_PROMPT = """你是一位资深面试官，擅长为非技术岗位（产品、运营、市场、设计等）设计结构化面试问题。

请根据JD、候选人简历、匹配分析结果，生成结构化面试问题清单。每个问题需要包含：
- question: 问题本身
- purpose: 考察目的
- good_answer_elements: 优秀回答应包含的要素（数组）
- red_flags: 红旗信号（数组）

返回JSON格式：
{
  "opening": [1-2个开场问题],
  "experience_verification": [3-5个经历验证问题，用STAR法],
  "competency": [3-5个能力考察问题，情景题为主],
  "risk_probing": [1-3个风险探测问题],
  "culture_fit": [1-2个文化匹配问题]
}"""


def _parse_questions(items: list[dict]) -> list[Question]:
    return [
        Question(
            question=item.get("question", ""),
            purpose=item.get("purpose", ""),
            good_answer_elements=item.get("good_answer_elements", []),
            red_flags=item.get("red_flags", []),
        )
        for item in items
    ]


class QuestionGenService:
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
            system=QUESTION_SYSTEM_PROMPT,
        )

    async def generate(
        self,
        jd_text: str,
        resume_text: str,
        match_highlights: list[str],
        match_risks: list[str],
        preferences: str = "",
    ) -> QuestionSet:
        prompt = (
            f"## 岗位JD\n{jd_text}\n\n"
            f"## 候选人简历（已脱敏）\n{resume_text}\n\n"
            f"## 匹配分析亮点\n" + "\n".join(f"- {h}" for h in match_highlights) + "\n\n"
            f"## 匹配分析风险\n" + "\n".join(f"- {r}" for r in match_risks)
        )
        if preferences:
            prompt += f"\n\n## 面试官关注点\n{preferences}"

        data = await self._call_llm(prompt)
        return QuestionSet(
            opening=_parse_questions(data.get("opening", [])),
            experience_verification=_parse_questions(data.get("experience_verification", [])),
            competency=_parse_questions(data.get("competency", [])),
            risk_probing=_parse_questions(data.get("risk_probing", [])),
            culture_fit=_parse_questions(data.get("culture_fit", [])),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_question_gen.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: interview question generation service"
```

---

### Task 8: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/position.py`
- Create: `backend/app/schemas/candidate.py`
- Create: `backend/app/schemas/resume_match.py`

- [ ] **Step 1: Create position schemas**

`backend/app/schemas/__init__.py`: empty file

`backend/app/schemas/position.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class PositionCreate(BaseModel):
    title: str
    department: str = ""
    jd_text: str
    core_competencies: str = ""
    preferences: str = ""


class PositionUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    jd_text: str | None = None
    core_competencies: str | None = None
    preferences: str | None = None
    status: str | None = None


class PositionResponse(BaseModel):
    id: int
    title: str
    department: str
    jd_text: str
    core_competencies: str
    preferences: str
    status: str
    created_at: datetime
    updated_at: datetime
    candidate_count: int = 0

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create candidate schemas**

`backend/app/schemas/candidate.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class CandidateCreate(BaseModel):
    position_id: int
    codename: str = ""


class CandidateResponse(BaseModel):
    id: int
    position_id: int
    codename: str
    resume_file_path: str
    structured_info: str
    created_at: datetime
    has_match: bool = False

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Create match schemas**

`backend/app/schemas/resume_match.py`:

```python
from datetime import datetime
from pydantic import BaseModel


class MatchScoreResponse(BaseModel):
    id: int
    candidate_id: int
    experience_score: float
    experience_note: str
    industry_score: float
    industry_note: str
    competency_score: float
    competency_note: str
    potential_score: float
    potential_note: str
    overall_score: float
    recommendation: str
    highlights: str
    risks: str
    questions: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: pydantic request/response schemas"
```

---

### Task 9: API Routes — Positions

**Files:**
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/positions.py`
- Create: `backend/tests/test_api_positions.py`

- [ ] **Step 1: Write failing tests for position API**

`backend/app/routers/__init__.py`: empty file

`backend/tests/test_api_positions.py`:

```python
import pytest


class TestCreatePosition:
    def test_creates_position(self, client):
        resp = client.post("/api/positions", json={
            "title": "产品经理",
            "department": "产品部",
            "jd_text": "负责用户增长策略",
            "core_competencies": "数据分析,用户研究",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "产品经理"
        assert data["id"] > 0

    def test_rejects_empty_title(self, client):
        resp = client.post("/api/positions", json={
            "title": "",
            "jd_text": "some JD",
        })
        assert resp.status_code == 422


class TestListPositions:
    def test_lists_positions(self, client):
        client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD1",
        })
        client.post("/api/positions", json={
            "title": "运营经理", "jd_text": "JD2",
        })
        resp = client.get("/api/positions")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_empty_list(self, client):
        resp = client.get("/api/positions")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetPosition:
    def test_gets_by_id(self, client):
        create_resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = create_resp.json()["id"]
        resp = client.get(f"/api/positions/{pid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "产品经理"

    def test_404_for_missing(self, client):
        resp = client.get("/api/positions/999")
        assert resp.status_code == 404


class TestUpdatePosition:
    def test_updates_fields(self, client):
        create_resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = create_resp.json()["id"]
        resp = client.patch(f"/api/positions/{pid}", json={
            "title": "高级产品经理",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "高级产品经理"


class TestDeletePosition:
    def test_deletes_position(self, client):
        create_resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = create_resp.json()["id"]
        resp = client.delete(f"/api/positions/{pid}")
        assert resp.status_code == 204
        assert client.get(f"/api/positions/{pid}").status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_positions.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement positions router**

`backend/app/routers/positions.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.position import Position, PositionStatus
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PositionResponse)
def create_position(body: PositionCreate, db: Session = Depends(get_db)):
    if not body.title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    position = Position(**body.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    return _to_response(position)


@router.get("", response_model=list[PositionResponse])
def list_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).order_by(Position.updated_at.desc()).all()
    return [_to_response(p) for p in positions]


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return _to_response(position)


@router.patch("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int, body: PositionUpdate, db: Session = Depends(get_db)
):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = PositionStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(position, key, value)
    db.commit()
    db.refresh(position)
    return _to_response(position)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    db.delete(position)
    db.commit()


def _to_response(position: Position) -> dict:
    return {
        "id": position.id,
        "title": position.title,
        "department": position.department,
        "jd_text": position.jd_text,
        "core_competencies": position.core_competencies,
        "preferences": position.preferences,
        "status": position.status.value,
        "created_at": position.created_at,
        "updated_at": position.updated_at,
        "candidate_count": len(position.candidates) if position.candidates else 0,
    }
```

Mount the router in `backend/app/main.py` — replace the entire file:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers.positions import router as positions_router

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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_api_positions.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: positions CRUD API endpoints"
```

---

### Task 10: API Routes — Candidates (Upload + Match + Questions)

**Files:**
- Create: `backend/app/routers/candidates.py`
- Create: `backend/app/routers/matches.py`
- Create: `backend/tests/test_api_candidates.py`
- Create: `backend/tests/test_api_matches.py`

- [ ] **Step 1: Write failing tests for candidate API**

`backend/tests/test_api_candidates.py`:

```python
import io
import pytest
from docx import Document


def _create_position(client) -> int:
    resp = client.post("/api/positions", json={
        "title": "产品经理", "jd_text": "负责用户增长",
    })
    return resp.json()["id"]


def _make_docx_bytes() -> bytes:
    doc = Document()
    doc.add_heading("张三", level=1)
    doc.add_paragraph("手机：13812345678")
    doc.add_paragraph("2020-2023 阿里巴巴 产品经理")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


class TestUploadCandidate:
    def test_uploads_resume_and_creates_candidate(self, client):
        pid = _create_position(client)
        docx_bytes = _make_docx_bytes()
        resp = client.post(
            f"/api/candidates/upload?position_id={pid}",
            files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["position_id"] == pid
        assert data["codename"] != ""

    def test_rejects_invalid_position(self, client):
        docx_bytes = _make_docx_bytes()
        resp = client.post(
            "/api/candidates/upload?position_id=999",
            files={"file": ("resume.docx", docx_bytes, "application/octet-stream")},
        )
        assert resp.status_code == 404


class TestListCandidates:
    def test_lists_by_position(self, client):
        pid = _create_position(client)
        docx_bytes = _make_docx_bytes()
        client.post(
            f"/api/candidates/upload?position_id={pid}",
            files={"file": ("r1.docx", docx_bytes, "application/octet-stream")},
        )
        resp = client.get(f"/api/candidates?position_id={pid}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetCandidate:
    def test_gets_by_id(self, client):
        pid = _create_position(client)
        docx_bytes = _make_docx_bytes()
        create_resp = client.post(
            f"/api/candidates/upload?position_id={pid}",
            files={"file": ("r1.docx", docx_bytes, "application/octet-stream")},
        )
        cid = create_resp.json()["id"]
        resp = client.get(f"/api/candidates/{cid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == cid
```

- [ ] **Step 2: Write failing tests for match API**

`backend/tests/test_api_matches.py`:

```python
import io
from unittest.mock import patch, AsyncMock

import pytest
from docx import Document

from app.services.matching import MatchResult


MOCK_MATCH = MatchResult(
    experience_score=82, experience_note="Good",
    industry_score=75, industry_note="Relevant",
    competency_score=80, competency_note="Strong",
    potential_score=70, potential_note="Growing",
    overall_score=78, recommendation="推荐",
    highlights=["亮点1"], risks=["风险1"],
)

MOCK_QUESTIONS = {
    "opening": [{"question": "Q1", "purpose": "P1", "good_answer_elements": [], "red_flags": []}],
    "experience_verification": [],
    "competency": [],
    "risk_probing": [],
    "culture_fit": [],
}


def _setup_candidate(client) -> tuple[int, int]:
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


class TestTriggerMatch:
    @patch("app.routers.matches.MatchingService")
    def test_triggers_matching(self, MockService, client):
        mock_svc = MockService.return_value
        mock_svc.match = AsyncMock(return_value=MOCK_MATCH)

        pid, cid = _setup_candidate(client)
        resp = client.post(f"/api/matches/{cid}/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_score"] == 78
        assert data["recommendation"] == "推荐"


class TestGetMatch:
    @patch("app.routers.matches.MatchingService")
    def test_gets_match(self, MockService, client):
        mock_svc = MockService.return_value
        mock_svc.match = AsyncMock(return_value=MOCK_MATCH)

        _, cid = _setup_candidate(client)
        client.post(f"/api/matches/{cid}/score")

        resp = client.get(f"/api/matches/{cid}")
        assert resp.status_code == 200
        assert resp.json()["overall_score"] == 78
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_api_candidates.py tests/test_api_matches.py -v
```

Expected: FAIL

- [ ] **Step 4: Implement candidates router**

`backend/app/routers/candidates.py`:

```python
import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.position import Position
from app.models.candidate import Candidate
from app.services.resume_parser import ResumeParser
from app.services.pii_masking import PIIMasker

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
    file_ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "bin"
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
```

- [ ] **Step 5: Implement matches router**

`backend/app/routers/matches.py`:

```python
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import Candidate
from app.models.position import Position
from app.models.resume_match import ResumeMatch
from app.services.matching import MatchingService
from app.services.question_gen import QuestionGenService

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.post("/{candidate_id}/score")
async def trigger_matching(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    position = db.get(Position, candidate.position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    service = MatchingService()
    result = await service.match(
        jd_text=position.jd_text,
        resume_text=candidate.resume_sanitized_text,
        preferences=position.preferences,
    )

    existing = db.query(ResumeMatch).filter(
        ResumeMatch.candidate_id == candidate_id
    ).first()
    if existing:
        db.delete(existing)
        db.flush()

    match = ResumeMatch(
        candidate_id=candidate_id,
        experience_score=result.experience_score,
        experience_note=result.experience_note,
        industry_score=result.industry_score,
        industry_note=result.industry_note,
        competency_score=result.competency_score,
        competency_note=result.competency_note,
        potential_score=result.potential_score,
        potential_note=result.potential_note,
        overall_score=result.overall_score,
        recommendation=result.recommendation,
        highlights=json.dumps(result.highlights, ensure_ascii=False),
        risks=json.dumps(result.risks, ensure_ascii=False),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return _match_to_dict(match)


@router.post("/{candidate_id}/questions")
async def generate_questions(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    position = db.get(Position, candidate.position_id)
    match = db.query(ResumeMatch).filter(
        ResumeMatch.candidate_id == candidate_id
    ).first()

    highlights = json.loads(match.highlights) if match else []
    risks = json.loads(match.risks) if match else []

    service = QuestionGenService()
    question_set = await service.generate(
        jd_text=position.jd_text,
        resume_text=candidate.resume_sanitized_text,
        match_highlights=highlights,
        match_risks=risks,
        preferences=position.preferences,
    )

    import dataclasses
    questions_json = json.dumps(dataclasses.asdict(question_set), ensure_ascii=False)

    if match:
        match.questions = questions_json
        db.commit()
        db.refresh(match)

    return json.loads(questions_json)


@router.get("/{candidate_id}")
def get_match(candidate_id: int, db: Session = Depends(get_db)):
    match = db.query(ResumeMatch).filter(
        ResumeMatch.candidate_id == candidate_id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return _match_to_dict(match)


def _match_to_dict(match: ResumeMatch) -> dict:
    return {
        "id": match.id,
        "candidate_id": match.candidate_id,
        "experience_score": match.experience_score,
        "experience_note": match.experience_note,
        "industry_score": match.industry_score,
        "industry_note": match.industry_note,
        "competency_score": match.competency_score,
        "competency_note": match.competency_note,
        "potential_score": match.potential_score,
        "potential_note": match.potential_note,
        "overall_score": match.overall_score,
        "recommendation": match.recommendation,
        "highlights": match.highlights,
        "risks": match.risks,
        "questions": match.questions,
        "created_at": match.created_at.isoformat() if match.created_at else None,
    }
```

Update `backend/app/main.py` to mount new routers:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Base
from app.routers.positions import router as positions_router
from app.routers.candidates import router as candidates_router
from app.routers.matches import router as matches_router

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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
pytest tests/test_api_candidates.py tests/test_api_matches.py -v
```

Expected: All tests PASS

- [ ] **Step 7: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: candidate upload and match scoring API endpoints"
```

---

### Task 11: Frontend Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Initialize frontend project**

```bash
cd /Users/yinjun/interview
mkdir -p frontend/src
```

`frontend/package.json`:

```json
{
  "name": "interview-assistant-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.5.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.7.2",
    "vite": "^6.3.1",
    "@tailwindcss/vite": "^4.1.4",
    "tailwindcss": "^4.1.4"
  }
}
```

- [ ] **Step 2: Create config files**

`frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

`frontend/tsconfig.json`:

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

`frontend/tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["src"]
}
```

`frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 3: Create entry files**

`frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>面试助手</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`frontend/src/index.css`:

```css
@import "tailwindcss";
```

`frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
```

`frontend/src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PositionList from "./pages/PositionList";
import PositionDetail from "./pages/PositionDetail";
import CandidateDetail from "./pages/CandidateDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PositionList />} />
        <Route path="/positions/:id" element={<PositionDetail />} />
        <Route path="/candidates/:id" element={<CandidateDetail />} />
      </Route>
    </Routes>
  );
}
```

- [ ] **Step 4: Install dependencies**

```bash
cd /Users/yinjun/interview/frontend
npm install
```

- [ ] **Step 5: Commit**

```bash
cd /Users/yinjun/interview
git add -A
git commit -m "feat: frontend scaffolding with React, Vite, Tailwind"
```

---

### Task 12: Frontend — Layout & API Client

**Files:**
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/components/ScoreBadge.tsx`

- [ ] **Step 1: Create API client**

`frontend/src/api/client.ts`:

```typescript
const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface Position {
  id: number;
  title: string;
  department: string;
  jd_text: string;
  core_competencies: string;
  preferences: string;
  status: string;
  created_at: string;
  updated_at: string;
  candidate_count: number;
}

export interface Candidate {
  id: number;
  position_id: number;
  codename: string;
  resume_file_path: string;
  structured_info: string;
  created_at: string;
  has_match: boolean;
  resume_sanitized_text?: string;
}

export interface MatchScore {
  id: number;
  candidate_id: number;
  experience_score: number;
  experience_note: string;
  industry_score: number;
  industry_note: string;
  competency_score: number;
  competency_note: string;
  potential_score: number;
  potential_note: string;
  overall_score: number;
  recommendation: string;
  highlights: string;
  risks: string;
  questions: string;
  created_at: string;
}

export interface QuestionItem {
  question: string;
  purpose: string;
  good_answer_elements: string[];
  red_flags: string[];
}

export interface QuestionSet {
  opening: QuestionItem[];
  experience_verification: QuestionItem[];
  competency: QuestionItem[];
  risk_probing: QuestionItem[];
  culture_fit: QuestionItem[];
}

export const api = {
  positions: {
    list: () => request<Position[]>("/positions"),
    get: (id: number) => request<Position>(`/positions/${id}`),
    create: (data: Partial<Position>) =>
      request<Position>("/positions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (id: number, data: Partial<Position>) =>
      request<Position>(`/positions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<void>(`/positions/${id}`, { method: "DELETE" }),
  },
  candidates: {
    list: (positionId: number) =>
      request<Candidate[]>(`/candidates?position_id=${positionId}`),
    get: (id: number) => request<Candidate>(`/candidates/${id}`),
    upload: async (positionId: number, file: File): Promise<Candidate> => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `${BASE}/candidates/upload?position_id=${positionId}`,
        { method: "POST", body: formData }
      );
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      return res.json();
    },
  },
  matches: {
    get: (candidateId: number) =>
      request<MatchScore>(`/matches/${candidateId}`),
    score: (candidateId: number) =>
      request<MatchScore>(`/matches/${candidateId}/score`, { method: "POST" }),
    generateQuestions: (candidateId: number) =>
      request<QuestionSet>(`/matches/${candidateId}/questions`, {
        method: "POST",
      }),
  },
};
```

- [ ] **Step 2: Create Layout component**

`frontend/src/components/Layout.tsx`:

```tsx
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/positions", label: "岗位管理" },
];

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-5 border-b border-gray-200">
          <h1 className="text-lg font-bold text-gray-900">面试助手</h1>
          <p className="text-xs text-gray-500 mt-1">Interview Assistant</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Create ScoreBadge component**

`frontend/src/components/ScoreBadge.tsx`:

```tsx
interface ScoreBadgeProps {
  score: number;
  label: string;
  note?: string;
}

export default function ScoreBadge({ score, label, note }: ScoreBadgeProps) {
  const color =
    score >= 80
      ? "text-green-700 bg-green-50 border-green-200"
      : score >= 60
        ? "text-yellow-700 bg-yellow-50 border-yellow-200"
        : "text-red-700 bg-red-50 border-red-200";

  return (
    <div className={`rounded-lg border p-3 ${color}`}>
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium">{label}</span>
        <span className="text-lg font-bold">{score}</span>
      </div>
      {note && <p className="text-xs mt-1 opacity-80">{note}</p>}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: frontend Layout, API client, and ScoreBadge component"
```

---

### Task 13: Frontend — Position Pages

**Files:**
- Create: `frontend/src/pages/PositionList.tsx`
- Create: `frontend/src/pages/PositionDetail.tsx`

- [ ] **Step 1: Create PositionList page**

`frontend/src/pages/PositionList.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, Position } from "../api/client";

export default function PositionList() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [jdText, setJdText] = useState("");

  useEffect(() => {
    api.positions.list().then(setPositions);
  }, []);

  const handleCreate = async () => {
    if (!title.trim() || !jdText.trim()) return;
    await api.positions.create({ title, department, jd_text: jdText });
    setTitle("");
    setDepartment("");
    setJdText("");
    setShowForm(false);
    const updated = await api.positions.list();
    setPositions(updated);
  };

  const statusLabel: Record<string, string> = {
    open: "招聘中",
    closed: "已关闭",
    paused: "暂停",
  };

  const statusColor: Record<string, string> = {
    open: "bg-green-100 text-green-700",
    closed: "bg-gray-100 text-gray-600",
    paused: "bg-yellow-100 text-yellow-700",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">岗位管理</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? "取消" : "新建岗位"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              岗位名称
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="如：产品经理"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              部门
            </label>
            <input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="如：产品部"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              岗位描述（JD）
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="粘贴完整的岗位描述..."
            />
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
          >
            创建
          </button>
        </div>
      )}

      {positions.length === 0 && !showForm ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-2">暂无岗位</p>
          <p className="text-sm">点击「新建岗位」开始添加</p>
        </div>
      ) : (
        <div className="space-y-3">
          {positions.map((p) => (
            <Link
              key={p.id}
              to={`/positions/${p.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{p.title}</h3>
                  {p.department && (
                    <span className="text-sm text-gray-500">
                      {p.department}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-500">
                    {p.candidate_count} 位候选人
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[p.status] || ""}`}
                  >
                    {statusLabel[p.status] || p.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create PositionDetail page**

`frontend/src/pages/PositionDetail.tsx`:

```tsx
import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Position, Candidate } from "../api/client";

export default function PositionDetail() {
  const { id } = useParams<{ id: string }>();
  const [position, setPosition] = useState<Position | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [uploading, setUploading] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const pid = Number(id);
    const [pos, cands] = await Promise.all([
      api.positions.get(pid),
      api.candidates.list(pid),
    ]);
    setPosition(pos);
    setCandidates(cands);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    setUploading(true);
    try {
      await api.candidates.upload(Number(id), file);
      await load();
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  if (!position) {
    return <div className="text-gray-500">加载中...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <Link
          to="/positions"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          &larr; 返回岗位列表
        </Link>
        <h2 className="text-xl font-bold text-gray-900 mt-2">
          {position.title}
        </h2>
        {position.department && (
          <p className="text-sm text-gray-500">{position.department}</p>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
        <h3 className="font-semibold text-gray-900 mb-2">岗位描述</h3>
        <p className="text-sm text-gray-700 whitespace-pre-wrap">
          {position.jd_text}
        </p>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">
          候选人 ({candidates.length})
        </h3>
        <label
          className={`px-4 py-2 text-sm font-medium rounded-lg cursor-pointer transition-colors ${
            uploading
              ? "bg-gray-300 text-gray-500"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          {uploading ? "上传中..." : "上传简历"}
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>

      {candidates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>暂无候选人</p>
          <p className="text-sm mt-1">上传简历（PDF 或 Word）自动创建候选人</p>
        </div>
      ) : (
        <div className="space-y-3">
          {candidates.map((c) => (
            <Link
              key={c.id}
              to={`/candidates/${c.id}`}
              className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-medium text-gray-900">
                    {c.codename}
                  </span>
                  <span className="text-sm text-gray-500 ml-3">
                    {new Date(c.created_at).toLocaleDateString("zh-CN")}
                  </span>
                </div>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    c.has_match
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {c.has_match ? "已评分" : "待评分"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

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
git commit -m "feat: Position list and detail pages"
```

---

### Task 14: Frontend — Candidate Detail & Question Management

**Files:**
- Create: `frontend/src/pages/CandidateDetail.tsx`

- [ ] **Step 1: Create CandidateDetail page**

`frontend/src/pages/CandidateDetail.tsx`:

```tsx
import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { api, Candidate, MatchScore, QuestionSet } from "../api/client";
import ScoreBadge from "../components/ScoreBadge";

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [match, setMatch] = useState<MatchScore | null>(null);
  const [questions, setQuestions] = useState<QuestionSet | null>(null);
  const [scoring, setScoring] = useState(false);
  const [generatingQ, setGeneratingQ] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    const cid = Number(id);
    const cand = await api.candidates.get(cid);
    setCandidate(cand);
    try {
      const m = await api.matches.get(cid);
      setMatch(m);
      if (m.questions && m.questions !== "[]") {
        setQuestions(JSON.parse(m.questions));
      }
    } catch {
      setMatch(null);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleScore = async () => {
    if (!id) return;
    setScoring(true);
    try {
      const m = await api.matches.score(Number(id));
      setMatch(m);
    } finally {
      setScoring(false);
    }
  };

  const handleGenerateQuestions = async () => {
    if (!id) return;
    setGeneratingQ(true);
    try {
      const qs = await api.matches.generateQuestions(Number(id));
      setQuestions(qs);
    } finally {
      setGeneratingQ(false);
    }
  };

  if (!candidate) {
    return <div className="text-gray-500">加载中...</div>;
  }

  const recLabel: Record<string, string> = {
    推荐: "bg-green-100 text-green-800 border-green-200",
    待定: "bg-yellow-100 text-yellow-800 border-yellow-200",
    不推荐: "bg-red-100 text-red-800 border-red-200",
  };

  const sectionLabels: Record<string, string> = {
    opening: "开场问题",
    experience_verification: "经历验证",
    competency: "能力考察",
    risk_probing: "风险探测",
    culture_fit: "文化匹配",
  };

  return (
    <div>
      <Link
        to={`/positions/${candidate.position_id}`}
        className="text-sm text-blue-600 hover:text-blue-800"
      >
        &larr; 返回岗位
      </Link>
      <h2 className="text-xl font-bold text-gray-900 mt-2">
        {candidate.codename}
      </h2>

      {/* Match Scores */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">匹配评分</h3>
          <button
            onClick={handleScore}
            disabled={scoring}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
          >
            {scoring ? "评分中..." : match ? "重新评分" : "开始评分"}
          </button>
        </div>

        {match ? (
          <div>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
              <ScoreBadge
                score={match.experience_score}
                label="岗位经验"
                note={match.experience_note}
              />
              <ScoreBadge
                score={match.industry_score}
                label="行业背景"
                note={match.industry_note}
              />
              <ScoreBadge
                score={match.competency_score}
                label="核心能力"
                note={match.competency_note}
              />
              <ScoreBadge
                score={match.potential_score}
                label="成长潜力"
                note={match.potential_note}
              />
              <ScoreBadge
                score={match.overall_score}
                label="综合推荐"
                note={match.recommendation}
              />
            </div>

            <div className="flex items-center gap-2 mb-4">
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold border ${recLabel[match.recommendation] || "bg-gray-100"}`}
              >
                {match.recommendation}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">亮点</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  {JSON.parse(match.highlights || "[]").map(
                    (h: string, i: number) => (
                      <li key={i}>• {h}</li>
                    )
                  )}
                </ul>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <h4 className="font-medium text-red-800 mb-2">风险点</h4>
                <ul className="text-sm text-red-700 space-y-1">
                  {JSON.parse(match.risks || "[]").map(
                    (r: string, i: number) => (
                      <li key={i}>• {r}</li>
                    )
                  )}
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500">
            点击「开始评分」进行简历-JD匹配分析
          </div>
        )}
      </div>

      {/* Interview Questions */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">面试问题</h3>
          <button
            onClick={handleGenerateQuestions}
            disabled={generatingQ || !match}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
          >
            {generatingQ
              ? "生成中..."
              : questions
                ? "重新生成"
                : "生成问题"}
          </button>
        </div>

        {questions ? (
          <div className="space-y-6">
            {Object.entries(questions).map(([section, items]) => {
              if (!items || items.length === 0) return null;
              return (
                <div key={section}>
                  <h4 className="font-medium text-gray-800 mb-2">
                    {sectionLabels[section] || section}
                  </h4>
                  <div className="space-y-3">
                    {items.map(
                      (
                        q: {
                          question: string;
                          purpose: string;
                          good_answer_elements: string[];
                          red_flags: string[];
                        },
                        i: number
                      ) => (
                        <div
                          key={i}
                          className="bg-white border border-gray-200 rounded-lg p-4"
                        >
                          <p className="font-medium text-gray-900">
                            {q.question}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            考察目的：{q.purpose}
                          </p>
                          {q.good_answer_elements.length > 0 && (
                            <div className="mt-2">
                              <span className="text-xs text-green-600 font-medium">
                                优秀回答要素：
                              </span>
                              <span className="text-xs text-green-600">
                                {q.good_answer_elements.join("、")}
                              </span>
                            </div>
                          )}
                          {q.red_flags.length > 0 && (
                            <div className="mt-1">
                              <span className="text-xs text-red-600 font-medium">
                                红旗信号：
                              </span>
                              <span className="text-xs text-red-600">
                                {q.red_flags.join("、")}
                              </span>
                            </div>
                          )}
                        </div>
                      )
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl p-8 text-center text-gray-500">
            {match
              ? "点击「生成问题」创建面试问题清单"
              : "请先完成匹配评分，再生成面试问题"}
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify frontend builds**

```bash
cd /Users/yinjun/interview/frontend
npx tsc --noEmit
```

Expected: No errors

- [ ] **Step 3: Commit**

```bash
cd /Users/yinjun/interview
git add -A
git commit -m "feat: Candidate detail page with match scores and question management"
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

- [ ] **Step 2: Start backend server**

```bash
cd /Users/yinjun/interview/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/api/health` returns `{"status":"ok"}`

- [ ] **Step 3: Verify frontend dev server**

```bash
cd /Users/yinjun/interview/frontend
npm run dev
```

Open `http://localhost:5173` — should see the Layout with sidebar and empty position list.

- [ ] **Step 4: Commit final state**

```bash
git add -A
git commit -m "chore: Phase 1 complete — pre-interview preparation workflow"
```

---

## Phase 2 Preview (not in this plan)

Phase 2 will cover: Interview models (Interview, Transcript, Evaluation, Summary), real-time audio capture with BlackHole + faster-whisper, WebSocket transcription, the three-panel real-time interview UI, and interview summary generation with PDF export.
