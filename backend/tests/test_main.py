from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_insurance_verification_uses_three_sources():
    response = client.post(
        "/api/v1/insurance/verify",
        json={
            "patient_name": "Ada Lovelace",
            "insurance_provider": "Unknown Plan",
            "medication": "Humira",
            "amount": 1250,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["verification_status"] == "review_required"
    assert len(body["verification_sources"]) == 3
    assert body["anomaly_flag"] is True
