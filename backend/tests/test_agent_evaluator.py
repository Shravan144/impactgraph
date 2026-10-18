from evaluator import (
    decompose_claim,
    validate_line_citations,
    evaluate_deterministically,
)


def test_claim_decomposition_documentation():
    claim = "This project uses GitHub Actions to automate its documentation build."
    decomp = decompose_claim(claim)

    assert decomp["category"] == "documentation_automation"
    assert len(decomp["subclaims"]) >= 3
    assertions = [sc["assertion"] for sc in decomp["subclaims"]]
    assert any("GitHub Actions" in a for a in assertions)
    assert any("documentation" in a for a in assertions)


def test_claim_decomposition_testing():
    claim = "The project implements unit tests using pytest."
    decomp = decompose_claim(claim)

    assert decomp["category"] == "testing"
    assert len(decomp["subclaims"]) >= 1


def test_validate_line_citations_filters_invalid_lines():
    mock_content = "line 1: name: Build Docs\nline 2: on: push\nline 3: run: ./scripts/docs.py\n"
    evidence_list = [
        {
            "source": "workflow.yml",
            "blob_sha": "sha123",
            "content": mock_content,
            "relevant_lines": [
                {"line": 1, "text": "line 1: name: Build Docs"},
                {"line": 3, "text": "line 3: run: ./scripts/docs.py"},
                {"line": 99, "text": "hallucinated line"},  # Out of bounds!
            ],
        }
    ]

    validated = validate_line_citations(evidence_list)
    assert len(validated) == 1
    # Line 99 must be removed
    assert len(validated[0]["relevant_lines"]) == 2
    assert validated[0]["supporting_lines"] == "1, 3"


def test_evaluate_deterministically_supported():
    claim = "This project uses GitHub Actions to automate its documentation build."
    evidence_list = [
        {
            "source": ".github/workflows/build-docs.yml",
            "blob_sha": "abc123",
            "relevant_lines": [
                {"line": 2, "text": "on: push"},
                {"line": 15, "text": "run: uv run ./scripts/docs.py build"},
            ],
            "connected_paths": [".github/workflows/build-docs.yml -[:REFERENCES]-> scripts/docs.py"],
            "score": 35,
        }
    ]
    runtime_info = {"verified": False, "reason": "Runtime execution unverified"}

    result = evaluate_deterministically(claim, "fastapi/fastapi", evidence_list, runtime_info)
    assert result["verdict"] == "supported"
    assert "build-docs.yml" in result["rationale"]
    assert len(result["subclaims_verified"]) >= 2
    assert any("runtime execution has not been verified" in lim.lower() for lim in result["limitations"])


def test_evaluate_deterministically_insufficient_evidence():
    claim = "This project uses Kubernetes Helm charts for cluster orchestration."
    runtime_info = {"verified": False}

    result = evaluate_deterministically(claim, "fastapi/fastapi", [], runtime_info)
    assert result["verdict"] == "insufficient_evidence"
    assert "Lack of evidence in the inspected sample does not inherently prove the claim is false" in result["rationale"]
