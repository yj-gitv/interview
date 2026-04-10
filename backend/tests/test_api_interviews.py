import io
import json

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
