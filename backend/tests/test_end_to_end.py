from fastapi.testclient import TestClient
import main
from investigation import InvestigationRequest, store_investigation

client = TestClient(main.app)


def test_end_to_end_investigation_and_retrieval(monkeypatch):
    """Test full pipeline: POST investigation -> saved in FalkorDB -> GET report."""

    mock_candidates = {
        "investigation_id": "investigation-e2e-test",
        "repository": "fastapi/fastapi",
        "claim": "This project uses GitHub Actions to automate its documentation build.",
        "candidates": [
            {
                "repository": "fastapi/fastapi",
                "source": ".github/workflows/build-docs.yml",
                "blob_sha": "a5e6af6d066af41303c4a710c668a8c0d5d986a8",
                "size": 1500,
                "score": 45,
                "connected_paths": [".github/workflows/build-docs.yml -[:REFERENCES]-> scripts/docs.py"],
                "content": "name: Build Docs\non: [push]\njobs:\n  docs:\n    steps:\n      - run: uv run ./scripts/docs.py build-lang\n",
            }
        ],
    }

    # Run inspection
    inspected = main.inspect_candidates(mock_candidates)
    assert inspected["evidence_count"] == 1
    assert inspected["evidence"][0]["source"] == ".github/workflows/build-docs.yml"

    # Store investigation (which evaluates and saves in FalkorDB)
    report = store_investigation(inspected)
    assert report["investigation_id"] == "investigation-e2e-test"
    assert report["verdict"] == "supported"
    assert "build-docs.yml" in report["rationale"]

    # Now retrieve it back via GET /investigations/{id}
    response = client.get("/investigations/investigation-e2e-test")
    assert response.status_code == 200
    retrieved = response.json()
    assert retrieved["investigation_id"] == "investigation-e2e-test"
    assert retrieved["verdict"] == "supported"
    assert len(retrieved["evidence"]) >= 1


def test_ui_endpoint_returns_html():
    response = client.get("/ui")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "ImpactGraph" in response.text
    assert "FalkorDB" in response.text


def test_graph_stats_endpoint():
    response = client.get("/graph/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["node_count"] > 0
