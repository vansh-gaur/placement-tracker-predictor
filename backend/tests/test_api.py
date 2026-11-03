"""API tests. Uses a temporary SQLite database, never the production one.

The predict test uses a tiny test-only fixture model (20 rows, trained
in the fixture itself). That fixture is not the production model and
is never used for training the production model.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(tempfile.gettempdir(), "placement_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ.setdefault("MODEL_PATH", os.path.join(tempfile.gettempdir(), "placement_test_model.pkl"))

import app as app_module  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    # Fresh database for every test.
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    test_app = app_module.create_app()
    # Tiny fixture model, test-only. It implements the same
    # predict_proba(DataFrame) call shape as the production pipeline,
    # with a simple CGPA-based probability, so the test checks the
    # API validation and response shape without depending on the
    # production model file being present.
    class FixtureModel:
        def predict_proba(self, frame):
            # Deterministic, test-only: higher CGPA -> higher probability.
            cgpa = float(frame["cgpa"].iloc[0])
            prob = max(0.05, min(0.95, (cgpa - 5.0) / 5.0))
            return [[1 - prob, prob]]

    test_app.config["model"] = FixtureModel()
    test_app.config["model_path"] = str(tmp_path / "model.pkl")
    with test_app.test_client() as test_client:
        yield test_client


def auth_headers(client, email="a@test.local"):
    client.post("/api/auth/register", json={"email": email, "password": "password123"})
    response = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_unauthenticated_applications_rejected(client):
    assert client.get("/api/applications").status_code == 401
    assert client.post("/api/applications", json={"company": "X", "role": "Y"}).status_code == 401


def test_register_login_and_crud(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/applications",
        json={"company": "Acme", "role": "SDE", "type": "Job", "status": "Applied"},
        headers=headers,
    )
    assert created.status_code == 201
    app_id = created.get_json()["id"]

    listed = client.get("/api/applications", headers=headers)
    assert len(listed.get_json()) == 1

    updated = client.put(
        f"/api/applications/{app_id}",
        json={"status": "Interview"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.get_json()["status"] == "Interview"

    stats = client.get("/api/stats", headers=headers)
    assert stats.get_json()["total"] == 1

    deleted = client.delete(f"/api/applications/{app_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/applications", headers=headers).get_json() == []


def test_users_only_see_their_own_applications(client):
    headers_a = auth_headers(client, "a@test.local")
    headers_b = auth_headers(client, "b@test.local")
    created = client.post(
        "/api/applications",
        json={"company": "Acme", "role": "SDE"},
        headers=headers_a,
    )
    app_id = created.get_json()["id"]
    # User B must not see, edit, or delete user A's application.
    assert client.get("/api/applications", headers=headers_b).get_json() == []
    assert client.get(f"/api/applications/{app_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/api/applications/{app_id}", headers=headers_b).status_code == 404


def test_predict_validates_and_returns_probability(client):
    response = client.post(
        "/api/predict",
        json={
            "cgpa": 8.5,
            "internships": 2,
            "projects": 3,
            "dsa_score": 85,
            "communication_score": 80,
            "backlogs": 0,
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert 0 <= body["probability"] <= 1
    assert body["band"] in ("Low", "Moderate", "Strong")

    bad = client.post("/api/predict", json={"cgpa": 8.5})
    assert bad.status_code == 400
