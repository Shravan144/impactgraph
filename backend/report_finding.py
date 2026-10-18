import json
from graph_db import execute_query


def generate_report(investigation_id: str) -> dict:
    """Retrieve an investigation report and its graph evidence from FalkorDB."""

    query = """
    MATCH (i:Investigation {id: $investigation_id})-[:EVALUATED]->(c:Claim)
    OPTIONAL MATCH (c)-[:SUPPORTED_BY|CONTRADICTED_BY]->(e:Evidence)
    OPTIONAL MATCH (i)-[:TRAVERSED_PATH]->(t:Evidence)
    RETURN i.id AS investigation_id,
           i.verdict AS verdict,
           i.rationale AS rationale,
           i.limitations AS limitations,
           i.subclaims_verified AS subclaims_verified,
           i.runtime_execution_verified AS runtime_execution_verified,
           i.evaluation_mode AS evaluation_mode,
           i.timestamp AS timestamp,
           c.text AS claim,
           e.source AS source,
           e.blob_sha AS blob_sha,
           e.supporting_lines AS supporting_lines,
           t.source AS traversed_source
    """

    result = execute_query(
        query,
        params={"investigation_id": investigation_id},
    )

    if not result.result_set:
        raise ValueError(
            f"No investigation found for {investigation_id}"
        )

    first_row = result.result_set[0]

    evidence_map = {}
    traversed_sources = set()

    for row in result.result_set:
        ev_src = row[9]
        if ev_src is not None and ev_src not in evidence_map:
            evidence_map[ev_src] = {
                "source": ev_src,
                "blob_sha": row[10] or "",
                "supporting_lines": row[11] or "",
            }
        trav_src = row[12]
        if trav_src is not None:
            traversed_sources.add(trav_src)

    limitations = first_row[3] or []
    subclaims = first_row[4] or []
    runtime_verified = bool(first_row[5])

    return {
        "investigation_id": first_row[0],
        "claim": first_row[8],
        "verdict": first_row[1] or "needs_review",
        "rationale": first_row[2] or "",
        "evidence": list(evidence_map.values()),
        "subclaims_verified": subclaims,
        "limitations": limitations,
        "runtime_execution_verified": runtime_verified,
        "traversed_paths": list(traversed_sources),
        "evaluation_mode": first_row[6] or "deterministic_rule_engine",
        "timestamp": first_row[7] or "",
    }


def list_recent_investigations(limit: int = 10) -> list[dict]:
    """Retrieve a summary list of recent investigations."""
    query = """
    MATCH (r:Repository)-[:HAS_CLAIM]->(c:Claim)<-[:EVALUATED]-(i:Investigation)
    WHERE i.timestamp IS NOT NULL
    RETURN i.id, r.id, c.text, i.verdict, i.timestamp, i.runtime_execution_verified
    ORDER BY i.timestamp DESC
    LIMIT $limit
    """
    try:
        result = execute_query(query, params={"limit": limit})
        investigations = []
        for row in result.result_set:
            investigations.append({
                "investigation_id": row[0],
                "repository": row[1],
                "claim": row[2],
                "verdict": row[3],
                "timestamp": row[4],
                "runtime_execution_verified": bool(row[5]),
            })
        return investigations
    except Exception:
        return []


if __name__ == "__main__":
    report = generate_report("investigation-d8584d262ce2")
    print(json.dumps(report, indent=2))
