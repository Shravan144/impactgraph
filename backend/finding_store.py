import datetime
from graph_db import execute_query


def save_finding(
    investigation_id: str,
    repository: str,
    claim_id: str,
    claim_text: str,
    verdict: str,
    evidence: list[dict],
    limitations: list[str],
    rationale: str = "",
    subclaims_verified: list[str] | None = None,
    runtime_execution_verified: bool = False,
    evaluation_mode: str = "deterministic_rule_engine",
) -> None:
    """Save an investigation, verdict, and evidence relationships in FalkorDB."""

    owner_repo = repository.lower()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    investigation_query = """
    MERGE (r:Repository {id: $repository})
    MERGE (c:Claim {id: $claim_id})
    SET c.text = $claim_text,
        c.verdict = $verdict

    MERGE (i:Investigation {id: $investigation_id})
    SET i.status = 'completed',
        i.verdict = $verdict,
        i.rationale = $rationale,
        i.limitations = $limitations,
        i.subclaims_verified = $subclaims_verified,
        i.runtime_execution_verified = $runtime_execution_verified,
        i.evaluation_mode = $evaluation_mode,
        i.timestamp = $timestamp

    MERGE (r)-[:HAS_CLAIM]->(c)
    MERGE (i)-[:EVALUATED]->(c)

    RETURN i.id
    """

    execute_query(
        investigation_query,
        params={
            "repository": owner_repo,
            "claim_id": claim_id,
            "claim_text": claim_text,
            "investigation_id": investigation_id,
            "verdict": verdict,
            "rationale": rationale,
            "limitations": limitations or [],
            "subclaims_verified": subclaims_verified or [],
            "runtime_execution_verified": runtime_execution_verified,
            "evaluation_mode": evaluation_mode,
            "timestamp": timestamp,
        },
    )

    for item in evidence:
        source = item.get("source") or item.get("path")
        blob_sha = item.get("blob_sha") or item.get("sha") or "unknown_sha"
        supporting_lines = item.get("supporting_lines", "")

        evidence_id = f"{owner_repo}:{source}:{blob_sha}"

        # Choose relationship based on verdict
        rel_type = "CONTRADICTED_BY" if verdict == "contradicted" else "SUPPORTED_BY"

        evidence_query = f"""
        MERGE (e:Evidence {{id: $evidence_id}})
        SET e.source = $source,
            e.blob_sha = $blob_sha,
            e.supporting_lines = $supporting_lines

        WITH e
        MATCH (c:Claim {{id: $claim_id}})
        MATCH (i:Investigation {{id: $investigation_id}})

        MERGE (c)-[:{rel_type}]->(e)
        MERGE (i)-[:USED_EVIDENCE]->(e)

        RETURN e.id
        """

        execute_query(
            evidence_query,
            params={
                "evidence_id": evidence_id,
                "source": source,
                "blob_sha": blob_sha,
                "supporting_lines": supporting_lines,
                "claim_id": claim_id,
                "investigation_id": investigation_id,
            },
        )

        # Store traversed connected paths if present
        for conn_path in item.get("connected_paths", []):
            if "-[:REFERENCES]->" in conn_path:
                target_src = conn_path.split("-[:REFERENCES]->")[-1].strip()
                traversal_query = """
                MATCH (e_tgt:Evidence {source: $target_src})
                MATCH (i:Investigation {id: $investigation_id})
                MERGE (i)-[:TRAVERSED_PATH]->(e_tgt)
                """
                try:
                    execute_query(
                        traversal_query,
                        params={
                            "target_src": target_src,
                            "investigation_id": investigation_id,
                        },
                    )
                except Exception:
                    pass
