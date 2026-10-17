
from falkordb import FalkorDB


def save_finding(
    investigation_id: str,
    repository: str,
    claim_id: str,
    claim_text: str,
    verdict: str,
    evidence: list[dict],
    limitations: list[str],
) -> None:
    """Save an investigation and its evidence relationships."""

    if not evidence:
        raise ValueError(
            "Cannot save a finding without evidence."
        )

    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    owner_repo = repository.lower()

    graph.query(
        """
        MERGE (r:Repository {id: $repository})
        MERGE (c:Claim {id: $claim_id})
        SET c.text = $claim_text

        MERGE (i:Investigation {id: $investigation_id})
        SET i.status = 'completed',
            i.verdict = $verdict,
            i.limitations = $limitations

        MERGE (r)-[:HAS_CLAIM]->(c)
        MERGE (i)-[:EVALUATED]->(c)

        RETURN i.id
        """,
        params={
            "repository": owner_repo,
            "claim_id": claim_id,
            "claim_text": claim_text,
            "investigation_id": investigation_id,
            "verdict": verdict,
            "limitations": limitations,
        },
    )

    for item in evidence:
        evidence_id = (
            f"{owner_repo}:{item['source']}:{item['blob_sha']}"
        )

        graph.query(
            """
            MERGE (e:Evidence {id: $evidence_id})
            SET e.source = $source,
                e.blob_sha = $blob_sha,
                e.supporting_lines = $supporting_lines

            WITH e
            MATCH (c:Claim {id: $claim_id})
            MATCH (i:Investigation {id: $investigation_id})

            MERGE (c)-[:SUPPORTED_BY]->(e)
            MERGE (i)-[:USED_EVIDENCE]->(e)

            RETURN e.id
            """,
            params={
                "evidence_id": evidence_id,
                "source": item["source"],
                "blob_sha": item["blob_sha"],
                "supporting_lines": item.get(
                    "supporting_lines", ""
                ),
                "claim_id": claim_id,
                "investigation_id": investigation_id,
            },
        )
