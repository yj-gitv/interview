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
