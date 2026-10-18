import logging
import json
import httpx
from typing import Any
from ingest_github import fetch_workflow_runs
import config

logger = logging.getLogger("impactgraph.evaluator")

VALID_VERDICTS = {
    "supported",
    "partially_supported",
    "contradicted",
    "insufficient_evidence",
    "needs_review",
}


def decompose_claim(claim: str) -> dict[str, Any]:
    """Decompose a natural language claim into verifiable subclaims and expected signals."""
    claim_lower = claim.lower()

    subclaims = []
    category = "general"

    if "github action" in claim_lower or "workflow" in claim_lower or "ci" in claim_lower:
        category = "ci_automation"
        subclaims.append({
            "id": "subclaim_1",
            "assertion": "A GitHub Actions workflow configuration exists in .github/workflows/.",
            "target_type": "workflow",
        })
        if "doc" in claim_lower or "documentation" in claim_lower:
            category = "documentation_automation"
            subclaims.append({
                "id": "subclaim_2",
                "assertion": "Workflow triggers on relevant events (e.g., push, pull_request, workflow_dispatch).",
                "target_type": "triggers",
            })
            subclaims.append({
                "id": "subclaim_3",
                "assertion": "Workflow executes a documentation build tool (e.g., mkdocs, sphinx) or custom docs script.",
                "target_type": "build_command",
            })
            subclaims.append({
                "id": "subclaim_4",
                "assertion": "Referenced documentation scripts or dependencies are connected in the repository graph.",
                "target_type": "connected_references",
            })
        elif "test" in claim_lower:
            category = "test_automation"
            subclaims.append({
                "id": "subclaim_2",
                "assertion": "Workflow executes test runner (e.g. pytest, unittest).",
                "target_type": "test_command",
            })
    elif "test" in claim_lower:
        category = "testing"
        subclaims.append({
            "id": "subclaim_1",
            "assertion": "Automated test suites or test files exist in the repository.",
            "target_type": "test_suite",
        })
    elif "auth" in claim_lower or "jwt" in claim_lower:
        category = "authentication"
        subclaims.append({
            "id": "subclaim_1",
            "assertion": "Authentication middleware, security tokens, or JWT handlers are implemented.",
            "target_type": "source_code",
        })
    else:
        subclaims.append({
            "id": "subclaim_1",
            "assertion": f"Source evidence directly substantiates: '{claim}'",
            "target_type": "general_evidence",
        })

    return {
        "category": category,
        "subclaims": subclaims,
    }


def validate_line_citations(evidence_list: list[dict]) -> list[dict]:
    """
    Validate that cited line numbers and snippets actually match
    the underlying source content to prevent hallucinated line citations.
    """
    validated = []
    for ev in evidence_list:
        content = ev.get("content", "")
        lines = content.splitlines() if content else []
        total_lines = len(lines)

        verified_relevant_lines = []
        for rl in ev.get("relevant_lines", []):
            line_no = rl.get("line")
            if isinstance(line_no, int) and 1 <= line_no <= total_lines:
                actual_text = lines[line_no - 1].strip()
                # Verify that the text snippet corresponds to reality
                verified_relevant_lines.append({
                    "line": line_no,
                    "text": actual_text[:240],
                })

        supporting_lines_str = ", ".join(str(l["line"]) for l in verified_relevant_lines)

        validated.append({
            "source": ev.get("source") or ev.get("path"),
            "blob_sha": ev.get("blob_sha") or ev.get("sha"),
            "size": ev.get("size", 0),
            "supporting_lines": supporting_lines_str,
            "relevant_lines": verified_relevant_lines,
            "connected_paths": ev.get("connected_paths", []),
            "content_preview": "\n".join(lines[:30]) if lines else "",
        })
    return validated


def evaluate_with_llm(
    claim: str,
    repository: str,
    candidate_evidence: list[dict],
) -> dict[str, Any] | None:
    """
    Optional LLM reasoning layer: asks an OpenRouter or OpenAI model to evaluate
    the claim against real evidence with strict schema adherence.
    """
    llm_cfg = config.get_llm_config()
    api_key = llm_cfg.get("api_key")
    if not api_key:
        return None

    base_url = llm_cfg.get("base_url") or "https://openrouter.ai/api/v1"
    model = llm_cfg.get("model") or "meta-llama/llama-3.3-70b-instruct"
    provider = llm_cfg.get("provider", "llm")

    evidence_summary = []
    for ev in candidate_evidence[:3]:
        evidence_summary.append({
            "file": ev.get("source") or ev.get("path"),
            "connected_graph_paths": ev.get("connected_paths", []),
            "relevant_lines": [
                f"L{l['line']}: {l['text']}" for l in ev.get("relevant_lines", [])[:10]
            ],
        })

    prompt = f"""You are ImpactGraph, an evidence-grounded software verification agent.
Repository: {repository}
Claim: "{claim}"

Retrieved Source Evidence from FalkorDB:
{json.dumps(evidence_summary, indent=2)}

Task:
Evaluate whether the evidence supports, partially supports, contradicts, or provides insufficient evidence for the claim.
Only cite evidence that is explicitly present above. Do NOT assume or invent execution history.

Respond ONLY with a JSON object in this format:
{{
    "verdict": "supported" | "partially_supported" | "contradicted" | "insufficient_evidence" | "needs_review",
    "rationale": "Clear, precise explanation citing specific files and connected scripts.",
    "subclaims_verified": ["list of verified subclaims"],
    "limitations": ["list of explicit limitations"]
}}
"""
    try:
        raw_content = ""
        if provider == "gemini":
            url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            }
            response = httpx.post(url, json=payload, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            raw_content = data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            url = f"{base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/shravanb2005/impactgraph",
                "X-Title": "ImpactGraph FalkorDB Agent",
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a rigorous code verification agent. Always output valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
            response = httpx.post(url, headers=headers, json=payload, timeout=45.0)
            response.raise_for_status()
            data = response.json()
            raw_content = data["choices"][0]["message"]["content"]

        parsed = json.loads(raw_content)

        if parsed.get("verdict") in VALID_VERDICTS and parsed.get("rationale"):
            parsed["evaluation_mode"] = f"llm_{provider}_{model.split('/')[-1]}"
            return parsed
    except Exception as exc:
        logger.warning(f"LLM evaluation failed or timed out: {exc}. Falling back to deterministic engine.")

    return None


def evaluate_deterministically(
    claim: str,
    repository: str,
    candidate_evidence: list[dict],
    runtime_verification: dict,
) -> dict[str, Any]:
    """
    Deterministic evidence evaluation engine.
    Inspects exact lines, keywords, and FalkorDB connected paths to form a rigorous verdict.
    """
    if not candidate_evidence:
        return {
            "verdict": "insufficient_evidence",
            "rationale": f"No relevant evidence files were found in repository '{repository}' for the claim: '{claim}'. Note: Lack of evidence in the inspected sample does not inherently prove the claim is false.",
            "subclaims_verified": [],
            "limitations": [
                "No candidate evidence found in inspected repository files.",
                "Successful runtime execution has not been verified.",
            ],
            "evaluation_mode": "deterministic_rule_engine",
        }

    decomp = decompose_claim(claim)
    claim_category = decomp["category"]
    subclaims = decomp["subclaims"]

    top_candidate = candidate_evidence[0]
    top_source = top_candidate.get("source") or top_candidate.get("path") or ""
    top_lines = top_candidate.get("relevant_lines", [])
    connected_paths = top_candidate.get("connected_paths", [])

    subclaims_verified = []
    limitations = []

    # Check for documentation build automation
    if claim_category == "documentation_automation":
        workflow_found = any(".github/workflows/" in (c.get("source") or "") for c in candidate_evidence)
        if workflow_found:
            subclaims_verified.append("GitHub Actions documentation workflow file exists.")

        triggers_found = any(
            any(t in l["text"].lower() for t in ["push:", "pull_request:", "workflow_dispatch:", "schedule:"])
            for c in candidate_evidence for l in c.get("relevant_lines", [])
        )
        if triggers_found:
            subclaims_verified.append("Workflow specifies automated event triggers (e.g. push / pull_request).")

        build_cmd_found = any(
            any(t in l["text"].lower() for t in ["docs.py", "mkdocs", "build docs", "sphinx", "build-docs"])
            for c in candidate_evidence for l in c.get("relevant_lines", [])
        )
        if build_cmd_found:
            subclaims_verified.append("Workflow executes documentation build commands/scripts.")

        # FalkorDB Connected graph check
        has_connected_script = any("REFERENCES" in p and ("docs" in p or ".py" in p) for p in connected_paths)
        if has_connected_script:
            subclaims_verified.append("FalkorDB graph traversal connects workflow to the invoked build script.")

        if workflow_found and build_cmd_found:
            verdict = "supported"
            connected_note = (
                f" Connected graph traversal in FalkorDB links this workflow directly to '{connected_paths[0]}'."
                if connected_paths else ""
            )
            rationale = (
                f"The repository configures automated documentation building via GitHub Actions workflow '{top_source}'. "
                f"Inspected lines confirm execution steps for documentation generation.{connected_note}"
            )
        elif workflow_found:
            verdict = "partially_supported"
            rationale = (
                f"A GitHub Actions workflow '{top_source}' was identified, but explicit documentation build commands were only partially identified."
            )
        else:
            verdict = "insufficient_evidence"
            rationale = "No GitHub Actions workflow configured for documentation build was identified in the inspected files."

    # General CI / workflow claim
    elif claim_category == "ci_automation":
        workflow_found = any(".github/workflows/" in (c.get("source") or "") for c in candidate_evidence)
        if workflow_found:
            subclaims_verified.append("Workflow configuration files identified.")
            verdict = "supported"
            rationale = f"Repository contains automated GitHub Actions workflow: '{top_source}'."
        else:
            verdict = "insufficient_evidence"
            rationale = "No CI workflow files matching the claim were identified."

    # General testing claim
    elif claim_category == "testing":
        test_found = any("test" in (c.get("source") or "").lower() for c in candidate_evidence)
        if test_found:
            subclaims_verified.append("Test suites/configurations identified.")
            verdict = "supported"
            rationale = f"Repository source contains test suite files such as '{top_source}'."
        else:
            verdict = "insufficient_evidence"
            rationale = "No test files matching the claim were found."

    else:
        # Default fallback
        if top_candidate.get("score", 0) >= 15:
            verdict = "supported"
            rationale = f"Candidate evidence '{top_source}' strongly matches the claim keywords and content."
        elif top_candidate.get("score", 0) >= 6:
            verdict = "partially_supported"
            rationale = f"Candidate evidence '{top_source}' partially matches claim keywords."
        else:
            verdict = "insufficient_evidence"
            rationale = "Inspected candidate files do not provide sufficient evidence to evaluate the claim."

    # Runtime verification limitation check
    if runtime_verification.get("verified"):
        run_info = runtime_verification.get("latest_run", {})
        rationale += f" Live runtime execution was confirmed via GitHub Actions: run #{run_info.get('id')} ({run_info.get('conclusion')})."
    else:
        limitations.append("Successful runtime execution has not been verified from live run history.")
        reason = runtime_verification.get("reason")
        if reason and reason != "Successful runtime execution has not been verified from live run history.":
            limitations.append(reason)

    limitations.append("Inspection is bounded to repository source files indexed in FalkorDB.")

    return {
        "verdict": verdict,
        "rationale": rationale,
        "subclaims_verified": subclaims_verified,
        "limitations": limitations,
        "evaluation_mode": "deterministic_rule_engine",
    }


def evaluate_investigation(
    claim: str,
    repository: str,
    candidate_evidence: list[dict],
) -> dict[str, Any]:
    """
    Main evaluation entry point.
    Runs runtime verification, validates line citations, executes LLM or deterministic evaluation,
    and returns a structured, traceable evaluation package.
    """
    validated_evidence = validate_line_citations(candidate_evidence)

    # 1. Scope runtime verification safely
    runtime_info = {"verified": False, "reason": "No workflow identified for runtime verification."}
    if "/" in repository:
        owner, repo = repository.split("/", 1)
        # Find top workflow candidate if applicable
        top_workflow = None
        for ev in validated_evidence:
            src = ev.get("source", "")
            if ".github/workflows/" in src:
                top_workflow = src.split("/")[-1]
                break
        if top_workflow:
            runtime_info = fetch_workflow_runs(owner, repo, top_workflow)

    # 2. Try LLM evaluation first if key is present
    llm_result = evaluate_with_llm(claim, repository, validated_evidence)

    # 3. Use deterministic engine if LLM is unavailable or unconfigured
    if llm_result:
        evaluation = llm_result
        if not runtime_info.get("verified"):
            evaluation["limitations"].append("Successful live runtime execution could not be independently verified.")
    else:
        evaluation = evaluate_deterministically(claim, repository, validated_evidence, runtime_info)

    evaluation["evidence"] = validated_evidence
    evaluation["runtime_execution_verified"] = runtime_info.get("verified", False)
    evaluation["runtime_details"] = runtime_info

    return evaluation
