from fastapi.testclient import TestClient

from app.main import app
from app.schemas import TriageLLMOutput
from tests.helpers import FakeRouter


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "slm_model" in body and "llm_model" in body


def test_triage_endpoint():
    with TestClient(app) as client:
        # echten Router durch Fake ersetzen (kein laufendes Modell nötig)
        app.state.router = FakeRouter(
            {
                TriageLLMOutput: TriageLLMOutput(
                    category="Eskalation",
                    priority=1,
                    deadline_iso="",
                    suggested_folder="Dringend",
                    reasoning="Beschwerde mit rechtlicher Drohung.",
                    confidence=0.81,
                )
            }
        )
        resp = client.post(
            "/triage",
            json={"email": {"from": "buerger@example.de", "subject": "Beschwerde", "body": "..."}},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["category"] == "Eskalation"
    assert data["result"]["priority"] == 1
    assert "model_used" in data
