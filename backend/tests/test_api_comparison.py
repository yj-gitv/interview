import io
from unittest.mock import patch, AsyncMock

from docx import Document

from app.services.matching import MatchResult


def _make_docx() -> bytes:
    doc = Document()
    doc.add_paragraph("张三 产品经理")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


MOCK_MATCH = MatchResult(
    experience_score=82, experience_note="Good",
    industry_score=75, industry_note="Relevant",
    competency_score=80, competency_note="Strong",
    potential_score=70, potential_note="Growing",
    overall_score=78, recommendation="推荐",
    highlights=["亮点1"], risks=["风险1"],
)


class TestCompareEndpoint:
    def test_returns_empty_for_no_candidates(self, client):
        resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = resp.json()["id"]
        resp = client.get(f"/api/comparison/{pid}")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_candidates_with_match(self, client):
        resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = resp.json()["id"]

        for _ in range(2):
            client.post(
                f"/api/candidates/upload?position_id={pid}",
                files={"file": ("r.docx", _make_docx(), "application/octet-stream")},
            )

        resp = client.get(f"/api/comparison/{pid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["codename"] != ""
        assert data[0]["match"] is None  # no scoring done yet

    @patch("app.routers.matches.MatchingService")
    def test_includes_match_scores(self, MockService, client):
        mock_svc = MockService.return_value
        mock_svc.match = AsyncMock(return_value=MOCK_MATCH)

        resp = client.post("/api/positions", json={
            "title": "产品经理", "jd_text": "JD",
        })
        pid = resp.json()["id"]
        resp = client.post(
            f"/api/candidates/upload?position_id={pid}",
            files={"file": ("r.docx", _make_docx(), "application/octet-stream")},
        )
        cid = resp.json()["id"]

        client.post(f"/api/matches/{cid}/score")

        resp = client.get(f"/api/comparison/{pid}")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["match"] is not None
        assert data[0]["match"]["overall_score"] == 78
