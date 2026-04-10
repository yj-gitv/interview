import io
from unittest.mock import patch, AsyncMock

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
