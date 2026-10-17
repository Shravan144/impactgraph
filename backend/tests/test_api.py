
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


def test_create_investigation(monkeypatch):
    expected_result = {
        "investigation_id": "investigation-test-new",
        "repository": "fastapi/fastapi",
        "claim": "The project automates documentation builds",
        "verdict": "needs_review",
        "evidence_count": 1,
        "limitations": ["Evidence requires human review."],
    }

    def fake_collect_candidates(request):
        assert request.owner == "fastapi"
        assert request.repo == "fastapi"
        return {"candidates": []}

    def fake_inspect_candidates(candidates):
        return {
            "investigation_id": "investigation-test-new",
            "repository": "fastapi/fastapi",
            "claim": "The project automates documentation builds",
            "evidence": [{"source": "workflow.yml"}],
            "evidence_count": 1,
        }

    def fake_store_investigation(investigation):
        return expected_result

    monkeypatch.setattr(
        main, "collect_candidates", fake_collect_candidates
    )
    monkeypatch.setattr(
        main, "inspect_candidates", fake_inspect_candidates
    )
    monkeypatch.setattr(
        main, "store_investigation", fake_store_investigation
    )

    response = client.post(
        "/investigations",
        json={
            "owner": "fastapi",
            "repo": "fastapi",
            "claim": "The project automates documentation builds",
        },
    )

    assert response.status_code == 200
    assert response.json() == expected_result
