# tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app
import time

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_plan_and_retrieve_and_delete():
    payload = {
        "wall": {"width": 1.0, "height": 1.0, "brush_width": 0.05, "resolution": 0.02, "obstacles": []},
        "name": "test_plan"
    }
    r = client.post("/api/plan", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "id" in body
    trid = body["id"]
    time.sleep(0.1)
    g = client.get(f"/api/trajectory/{trid}")
    assert g.status_code == 200
    gj = g.json()
    assert "waypoints" in gj and isinstance(gj["waypoints"], list)
    d = client.delete(f"/api/trajectory/{trid}")
    assert d.status_code == 200
    assert d.json()["deleted"] >= 1

def test_query_list():
    r = client.get("/api/trajectories")
    assert r.status_code == 200
    j = r.json()
    assert "results" in j

def test_plan_with_obstacle():
    payload = {
        "wall": {
            "width": 1.0, "height": 1.0, "brush_width": 0.05, "resolution": 0.02,
            "obstacles": [{"x":0.2, "y":0.2, "w":0.1, "h":0.1}]
        },
        "name": "test_plan_obst"
    }
    r = client.post("/api/plan", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "id" in body
    trid = body["id"]
    g = client.get(f"/api/trajectory/{trid}")
    assert g.status_code == 200
    gj = g.json()
    assert isinstance(gj.get("obstacles", []), list)
    # cleanup
    d = client.delete(f"/api/trajectory/{trid}")
    assert d.status_code == 200
