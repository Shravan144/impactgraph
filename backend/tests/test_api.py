
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_investigation_report(monkeypatch):
    expected_report = {
        "investigation_id": "investigation-test",
        "claim": "Example claim",
        "verdict": "supported_at_configuration_level",
        "evidence": [
            {
                "source": "workflow.yml",
                "blob_sha": "abc123",
                "supporting_lines": "1-5",
            }
        ],
        "limitations": ["Runtime execution not verified"],
        "runtime_execution_verified": False,
    }

    def fake_generate_report(investigation_id):
        assert investigation_id == "investigation-test"
        return expected_report

    monkeypatch.setattr(
        main,
        "generate_report",
        fake_generate_report,
    )

    response = client.get(
        "/investigations/investigation-test"
    )

    assert response.status_code == 200
    assert response.json() == expected_report


def test_investigation_not_found(monkeypatch):
    def fake_generate_report(investigation_id):
        raise ValueError("Investigation not found")

    monkeypatch.setattr(
        main,
        "generate_report",
        fake_generate_report,
    )

    response = client.get(
        "/investigations/does-not-exist"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Investigation not found"
