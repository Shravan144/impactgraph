import logging
from typing import Any

from graph_algorithms import (
    recall_cross_session_memory,
    traverse_multihop_neighborhood,
    compute_component_centrality,
)
from claim_matcher import extract_keywords, find_candidate_evidence
from investigate_claim import inspect_candidate
from ingest_github import fetch_workflow_runs
from evaluator import evaluate_investigation
from store_evidence import ensure_repository_ingested
from finding_store import save_finding

logger = logging.getLogger("impactgraph.agent_loop")


def run_autonomous_investigation_loop(
    owner: str,
    repo: str,
    claim: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Autonomous Multi-Hop ReAct Agent Loop:
    Executes a structured Thought -> Action -> Observation cycle powered by FalkorDB connected data.
    """
    repository = f"{owner}/{repo}".lower()
    investigation_id = f"investigation-{import_uuid()}"
    claim_keywords = extract_keywords(claim)

    trace: list[dict[str, Any]] = []

    # Step 1: Cross-Session Memory Recall
    trace.append({
        "step": 1,
        "phase": "Memory Recall",
        "thought": f"Querying FalkorDB cross-session graph memory for previously verified facts or investigations on '{repository}'...",
        "action": "recall_cross_session_memory",
    })
    memories = recall_cross_session_memory(repository, claim_keywords)
    if memories and memories[0].get("relevance_score", 0) > 0:
        top_mem = memories[0]
        obs = f"Recalled previous investigation ({top_mem['investigation_id']}) with verdict '{top_mem['verdict']}' on claim: '{top_mem['claim_text']}'."
    else:
        obs = f"No previous investigations matching '{claim}' found in FalkorDB memory. Starting fresh exploration."
    trace[-1]["observation"] = obs

    # Step 2: Ensure Graph Ingestion & Cache Check
    trace.append({
        "step": 2,
        "phase": "Graph Ingestion",
        "thought": f"Ensuring repository structure and cross-file references for '{repository}' are indexed in FalkorDB...",
        "action": "ensure_repository_ingested",
    })
    try:
        ingest_res = ensure_repository_ingested(owner, repo, claim_focus=claim, force_refresh=force_refresh)
        trace[-1]["observation"] = f"Repository graph ready in FalkorDB (status: {ingest_res.get('status', 'ingested')})."
    except Exception as exc:
        trace[-1]["observation"] = f"FalkorDB ingestion check: {exc}"

    # Step 3: Graph Candidate Discovery
    trace.append({
        "step": 3,
        "phase": "Candidate Discovery",
        "thought": f"Searching FalkorDB for evidence candidates matching claim keywords: {list(claim_keywords)[:6]}...",
        "action": "find_candidate_evidence",
    })
    candidates = find_candidate_evidence(claim, limit=4, repository_filter=repository)
    trace[-1]["observation"] = f"Identified {len(candidates)} candidate files in FalkorDB. Top candidate: '{candidates[0]['source'] if candidates else 'None'}'."

    # Step 4: Multi-Hop Traversal (Following connections)
    traversal_chains = []
    if candidates:
        top_source = candidates[0]["source"]
        trace.append({
            "step": 4,
            "phase": "Multi-Hop Traversal",
            "thought": f"Executing multi-hop graph traversal from '{top_source}' across [:REFERENCES] and [:USES_DEPENDENCY] edges in FalkorDB...",
            "action": "traverse_multihop_neighborhood",
        })
        traversal_chains = traverse_multihop_neighborhood(top_source, max_hops=3)
        code_refs = [c["chain"] for c in traversal_chains if c["type"] == "code_reference_chain"]
        dep_refs = [c["chain"] for c in traversal_chains if c["type"] == "dependency_chain"]
        trace[-1]["observation"] = (
            f"Traversed {len(traversal_chains)} connected paths. "
            f"Code references: {len(code_refs)}, Dependencies: {len(dep_refs)}. "
            f"Primary chain: '{code_refs[0] if code_refs else (dep_refs[0] if dep_refs else 'Direct file')}'."
        )

    # Step 5: Source Code Inspection & Line Citation Validation
    trace.append({
        "step": 5,
        "phase": "Evidence Inspection",
        "thought": "Retrieving raw Git blobs and validating exact line citations against source code...",
        "action": "inspect_source_lines",
    })
    inspected_evidence = []
    for c in candidates:
        inspected = inspect_candidate(c, claim=claim)
        if inspected:
            inspected["connected_paths"] = c.get("connected_paths", [])
            inspected_evidence.append(inspected)
    total_cited = sum(len(e.get("relevant_lines", [])) for e in inspected_evidence)
    trace[-1]["observation"] = f"Extracted and validated {total_cited} exact line citations across {len(inspected_evidence)} evidence files."

    # Step 6: Runtime Execution Telemetry
    trace.append({
        "step": 6,
        "phase": "Runtime Verification",
        "thought": "Querying GitHub Actions telemetry to verify live run execution vs source configuration...",
        "action": "fetch_workflow_runs",
    })
    top_wf = None
    for e in inspected_evidence:
        if ".github/workflows/" in e.get("path", ""):
            top_wf = e["path"].split("/")[-1]
            break
    runtime_info = fetch_workflow_runs(owner, repo, top_wf) if top_wf else {"verified": False, "reason": "No workflow file identified."}
    trace[-1]["observation"] = runtime_info.get("reason", "Runtime execution status queried.")

    # Step 7: Structured Verdict Synthesis & Persistence
    trace.append({
        "step": 7,
        "phase": "Verdict Synthesis & Storage",
        "thought": "Evaluating all verified subclaims and connected graph paths into a structured verdict, and storing in FalkorDB...",
        "action": "evaluate_and_store",
    })
    eval_result = evaluate_investigation(claim, repository, inspected_evidence)
    verdict = eval_result["verdict"]
    rationale = eval_result["rationale"]

    claim_id = f"claim-{investigation_id}"
    save_finding(
        investigation_id=investigation_id,
        repository=repository,
        claim_id=claim_id,
        claim_text=claim,
        verdict=verdict,
        evidence=eval_result.get("evidence", []),
        limitations=eval_result.get("limitations", []),
        rationale=rationale,
        subclaims_verified=eval_result.get("subclaims_verified", []),
        runtime_execution_verified=eval_result.get("runtime_execution_verified", False),
        evaluation_mode=eval_result.get("evaluation_mode", "deterministic_rule_engine"),
    )
    trace[-1]["observation"] = f"Verdict: {verdict.upper()}. Finding persisted to FalkorDB."

    return {
        "investigation_id": investigation_id,
        "repository": repository,
        "claim": claim,
        "verdict": verdict,
        "rationale": rationale,
        "evidence_count": len(eval_result.get("evidence", [])),
        "evidence": eval_result.get("evidence", []),
        "subclaims_verified": eval_result.get("subclaims_verified", []),
        "limitations": eval_result.get("limitations", []),
        "runtime_execution_verified": eval_result.get("runtime_execution_verified", False),
        "traversal_chains": [c["chain"] for c in traversal_chains[:6]],
        "agent_trace": trace,
        "evaluation_mode": eval_result.get("evaluation_mode", "deterministic_rule_engine"),
    }


def import_uuid() -> str:
    from uuid import uuid4
    return uuid4().hex[:12]
