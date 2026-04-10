import io
from unittest.mock import AsyncMock, patch

from docx import Document

from app.services.matching import MatchResult


MOCK_MATCH = MatchResult(
    experience_score=82,
    experience_note="Good",
    industry_score=75,
    industry_note="Relevant",
    competency_score=80,
    competency_note="Strong",
    potential_score=70,
    potential_note="Growing",
    overall_score=78,
    recommendation="推荐",
    highlights=["亮点1"],
    risks=["风险1"],
)

MOCK_QUESTIONS = {
    "opening": [
        {
            "question": "Q1",
            "purpose": "P1",
            "good_answer_elements": [],
            "red_flags": [],
        }
    ],
    "experience_verification": [],
    "competency": [],
    "risk_probing": [],
    "culture_fit": [],
}


def _setup_candidate(client) -> tuple[int, int]:
    resp = client.post(
        "/api/positions",
        json={
            "title": "产品经理",
            "jd_text": "负责用户增长",
        },
    )
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
