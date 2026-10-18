import logging
from uuid import uuid4
from pydantic import BaseModel, Field

from investigate_claim import inspect_candidate
from claim_matcher import find_candidate_evidence
from store_evidence import ensure_repository_ingested
from finding_store import save_finding
from evaluator import evaluate_investigation

logger = logging.getLogger("impactgraph.investigation")


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
        min_length=5,
        description="Claim to investigate",
    )
    force_refresh: bool = Field(
        default=False,
        description="Force re-ingesting repository evidence into FalkorDB",
    )


class InvestigationResult(BaseModel):
    investigation_id: str
    repository: str
    claim: str
    verdict: str
    rationale: str | None = None
    evidence_count: int
    limitations: list[str]
    runtime_execution_verified: bool = False


def collect_candidates(
    request: InvestigationRequest,
    limit: int = 3,
) -> dict:
    """Ensure repository graph is ingested and find ranked candidate evidence."""

    investigation_id = f"investigation-{uuid4().hex[:12]}"
    requested_repository = f"{request.owner}/{request.repo}".lower()

    # Step 1: Ensure repository evidence is loaded into FalkorDB
    try:
        ensure_repository_ingested(
            request.owner,
            request.repo,
            claim_focus=request.claim,
            force_refresh=getattr(request, "force_refresh", False),
        )
    except Exception as exc:
        logger.warning(f"Repository graph ingestion encountered an issue: {exc}")

    # Step 2: Query FalkorDB for candidate evidence with graph traversals
    try:
        candidates = find_candidate_evidence(
            request.claim,
            limit=limit,
            repository_filter=requested_repository,
        )
    except TypeError:
        candidates = find_candidate_evidence(
            request.claim,
            limit=limit,
        )

    # Keep only candidates belonging to the requested repository
    candidates = [
        candidate
        for candidate in candidates
        if candidate.get("repository", "").lower()
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
    """Inspect candidate evidence files and extract verified line citations."""

    inspected_evidence = []

    for candidate in investigation["candidates"]:
        try:
            try:
                evidence = inspect_candidate(candidate, claim=investigation.get("claim"))
            except TypeError:
                evidence = inspect_candidate(candidate)

            if evidence is None:
                continue

            inspected_evidence.append({
                "source": evidence["path"],
                "blob_sha": evidence["sha"],
                "size": evidence["size"],
                "relevant_lines": evidence["relevant_lines"],
                "content": evidence.get("content", ""),
                "connected_paths": candidate.get("connected_paths", []),
                "score": candidate.get("score", 0),
            })

        except Exception as exc:
            logger.warning(
                f"Could not inspect {candidate.get('source')}: {exc}"
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
    """Evaluate candidate evidence, synthesize verdict, and persist in FalkorDB."""

    claim = investigation["claim"]
    repository = investigation["repository"]
    investigation_id = investigation["investigation_id"]
    evidence_candidates = investigation.get("evidence", [])

    # Step 3: Run Agent Evaluator (LLM or deterministic engine)
    evaluation = evaluate_investigation(claim, repository, evidence_candidates)

    verdict = evaluation["verdict"]
    rationale = evaluation["rationale"]
    limitations = evaluation["limitations"]
    subclaims_verified = evaluation.get("subclaims_verified", [])
    runtime_verified = evaluation.get("runtime_execution_verified", False)
    evaluation_mode = evaluation.get("evaluation_mode", "deterministic_rule_engine")
    validated_evidence = evaluation.get("evidence", [])

    claim_id = f"claim-{investigation_id}"

    # Step 4: Persist finding and traversed edges in FalkorDB
    save_finding(
        investigation_id=investigation_id,
        repository=repository,
        claim_id=claim_id,
        claim_text=claim,
        verdict=verdict,
        evidence=validated_evidence,
        limitations=limitations,
        rationale=rationale,
        subclaims_verified=subclaims_verified,
        runtime_execution_verified=runtime_verified,
        evaluation_mode=evaluation_mode,
    )

    return {
        "investigation_id": investigation_id,
        "repository": repository,
        "claim": claim,
        "verdict": verdict,
        "rationale": rationale,
        "evidence_count": len(validated_evidence),
        "evidence": [
            {
                "source": e["source"],
                "blob_sha": e["blob_sha"],
                "supporting_lines": e["supporting_lines"],
            }
            for e in validated_evidence
        ],
        "subclaims_verified": subclaims_verified,
        "limitations": limitations,
        "runtime_execution_verified": runtime_verified,
        "evaluation_mode": evaluation_mode,
    }
