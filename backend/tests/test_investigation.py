
from investigation import (
    InvestigationRequest,
    collect_candidates,
    inspect_candidates,
)


def test_collect_candidates_filters_repository(monkeypatch):
    def fake_find_candidate_evidence(claim, limit):
        assert claim == "The project automates documentation builds"
        assert limit == 3

        return [
            {
                "repository": "fastapi/fastapi",
                "source": "workflow.yml",
                "blob_sha": "abc123",
                "size": 100,
                "score": 5,
            },
            {
                "repository": "other/project",
                "source": "other.yml",
                "blob_sha": "def456",
                "size": 200,
                "score": 4,
            },
        ]

    monkeypatch.setattr(
        "investigation.find_candidate_evidence",
        fake_find_candidate_evidence,
    )

    request = InvestigationRequest(
        owner="fastapi",
        repo="fastapi",
        claim="The project automates documentation builds",
    )

    result = collect_candidates(request)

    assert result["repository"] == "fastapi/fastapi"
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["source"] == "workflow.yml"
    assert result["investigation_id"].startswith("investigation-")


def test_inspect_candidates_returns_evidence(monkeypatch):
    def fake_inspect_candidate(candidate):
        return {
            "path": candidate["source"],
            "sha": candidate["blob_sha"],
            "size": 100,
            "relevant_lines": [
                {"line": 5, "text": "Build documentation"}
            ],
        }

    monkeypatch.setattr(
        "investigation.inspect_candidate",
        fake_inspect_candidate,
    )

    investigation = {
        "investigation_id": "investigation-test",
        "repository": "fastapi/fastapi",
        "claim": "The project automates documentation builds",
        "candidates": [
            {
                "repository": "fastapi/fastapi",
                "source": "workflow.yml",
                "blob_sha": "abc123",
                "size": 100,
                "score": 5,
            }
        ],
    }

    result = inspect_candidates(investigation)

    assert result["evidence_count"] == 1
    assert result["evidence"][0]["source"] == "workflow.yml"
    assert result["evidence"][0]["relevant_lines"][0]["line"] == 5
