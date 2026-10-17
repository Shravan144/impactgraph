
import json

from falkordb import FalkorDB


def generate_report(investigation_id: str) -> dict:
    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    query = """
    MATCH (i:Investigation {id: $investigation_id})
          -[:EVALUATED]->(c:Claim)
    MATCH (c)-[:SUPPORTED_BY]->(e:Evidence)
    RETURN i.id AS investigation_id,
           i.verdict AS verdict,
           i.limitation AS limitation,
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
            f"No evidence-backed finding found for {investigation_id}"
        )

    row = result.result_set[0]

    return {
        "investigation_id": row[0],
        "claim": row[3],
        "verdict": row[1],
        "evidence": [
            {
                "source": row[4],
                "blob_sha": row[5],
                "supporting_lines": row[6],
            }
        ],
        "limitations": [row[2]] if row[2] else [],
        "runtime_execution_verified": False,
    }


if __name__ == "__main__":
    report = generate_report("investigation-docs-build-001")
    print(json.dumps(report, indent=2))
