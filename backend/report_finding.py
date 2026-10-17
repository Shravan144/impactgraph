
import json

from falkordb import FalkorDB


def generate_report(investigation_id: str) -> dict:
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    query = """
    MATCH (i:Investigation {id: $investigation_id})
          -[:EVALUATED]->(c:Claim)
    OPTIONAL MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
    RETURN i.id AS investigation_id,
           i.verdict AS verdict,
           i.limitations AS limitations,
           c.text AS claim,
           e.source AS source,
           e.blob_sha AS blob_sha,
           e.supporting_lines AS supporting_lines
    """

    result = graph.query(
        query,
        params={"investigation_id": investigation_id},
    )

    if not result.result_set:
        raise ValueError(
            f"No investigation found for {investigation_id}"
        )

    first_row = result.result_set[0]

    evidence = []
    for row in result.result_set:
        if row[4] is not None:
            evidence.append({
                "source": row[4],
                "blob_sha": row[5],
                "supporting_lines": row[6],
            })

    limitations = first_row[2] or []

    return {
        "investigation_id": first_row[0],
        "claim": first_row[3],
        "verdict": first_row[1],
        "evidence": evidence,
        "limitations": limitations,
        "runtime_execution_verified": False,
    }


if __name__ == "__main__":
    report = generate_report("investigation-ce2abbf58303")
    print(json.dumps(report, indent=2))
