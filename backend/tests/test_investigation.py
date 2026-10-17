
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


from claim_matcher import score_evidence, score_evidence_content


def test_documentation_build_scores_above_generic_workflow():
    claim = (
        "This project uses GitHub Actions "
        "to automate its documentation build."
    )

    build_docs_content = """
    name: Build Docs
    jobs:
      build-docs:
        steps:
          - uses: actions/checkout@v4
          - name: Build Docs
            run: uv run ./scripts/docs.py build-lang
    """

    generic_workflow_content = """
    name: Bump pre-commit hooks
    jobs:
      update:
        steps:
          - uses: actions/checkout@v4
          - run: pre-commit autoupdate
    """

    build_score = (
        score_evidence(claim, ".github/workflows/build-docs.yml")
        + score_evidence_content(claim, build_docs_content)
    )

    generic_score = (
        score_evidence(
            claim,
            ".github/workflows/bump-pre-commit-hooks.yml",
        )
        + score_evidence_content(claim, generic_workflow_content)
    )

    assert build_score > generic_score
    assert build_score >= 20
