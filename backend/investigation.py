
from uuid import uuid4
from investigate_claim import inspect_candidate

from claim_matcher import find_candidate_evidence
from pydantic import BaseModel, Field
from finding_store import save_finding


class InvestigationRequest(BaseModel):
    owner: str = Field(
        min_length=1,
        description="GitHub repository owner",
    )
    repo: str = Field(
        min_length=1,
        description="GitHub repository name",
    )
    claim: str = Field(
        min_length=10,
        description="Claim to investigate",
    )


class InvestigationResult(BaseModel):
    investigation_id: str
    repository: str
    claim: str
    verdict: str
    evidence_count: int
    limitations: list[str]


def collect_candidates(
    request: InvestigationRequest,
    limit: int = 3,
) -> dict:
    """Find candidate evidence for a repository claim."""

    investigation_id = f"investigation-{uuid4().hex[:12]}"

    candidates = find_candidate_evidence(
        request.claim,
        limit=limit,
    )

    # Keep only candidates belonging to the requested repository.
    requested_repository = (
        f"{request.owner}/{request.repo}"
    ).lower()

    candidates = [
        candidate
        for candidate in candidates
        if candidate["repository"].lower()
        == requested_repository
    ]

    return {
        "investigation_id": investigation_id,
        "repository": requested_repository,
        "claim": request.claim,
        "candidates": candidates,
    }


def inspect_candidates(
    investigation: dict,
) -> dict:
    """Retrieve source content for the selected candidates."""

    inspected_evidence = []

    for candidate in investigation["candidates"]:
        try:
            evidence = inspect_candidate(candidate)

            if evidence is None:
                continue

            inspected_evidence.append({
                "source": evidence["path"],
                "blob_sha": evidence["sha"],
                "relevant_lines": evidence["relevant_lines"],
            })

        except Exception as exc:
            print(
                f"Could not inspect "
                f"{candidate['source']}: {exc}"
            )

    return {
        "investigation_id": investigation["investigation_id"],
        "repository": investigation["repository"],
        "claim": investigation["claim"],
        "evidence": inspected_evidence,
        "evidence_count": len(inspected_evidence),
    }


def store_investigation(
    investigation: dict,
) -> dict:
    """Store retrieved evidence for human review."""

    evidence = []

    for item in investigation["evidence"]:
        lines = item.get("relevant_lines", [])

        supporting_lines = ", ".join(
            str(line["line"]) for line in lines
        )

        evidence.append({
            "source": item["source"],
            "blob_sha": item["blob_sha"],
            "supporting_lines": supporting_lines,
        })

    if not evidence:
        raise ValueError(
            "No evidence was retrieved; nothing to store."
        )

    claim_id = (
        f"claim-{investigation['investigation_id']}"
    )

    limitations = [
        "Evidence requires human review.",
        "Successful runtime execution has not been verified.",
    ]

    save_finding(
        investigation_id=investigation["investigation_id"],
        repository=investigation["repository"],
        claim_id=claim_id,
        claim_text=investigation["claim"],
        verdict="needs_review",
        evidence=evidence,
        limitations=limitations,
    )

    return {
        "investigation_id": investigation["investigation_id"],
        "repository": investigation["repository"],
        "claim": investigation["claim"],
        "verdict": "needs_review",
        "evidence_count": len(evidence),
        "limitations": limitations,
    }
