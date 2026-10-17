
from falkordb import FalkorDB


db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("ImpactGraph")

repo_id = "fastapi/fastapi"
claim_id = "claim-docs-build"
investigation_id = "investigation-docs-build-001"
evidence_id = (
    "fastapi/fastapi:"
    ".github/workflows/build-docs.yml:"
    "a5e6af6d066af41303c4a710c668a8c0d5d986a8"
)

claim_text = (
    "This project uses GitHub Actions "
    "to automate its documentation build."
)

query = """
MERGE (c:Claim {id: $claim_id})
SET c.text = $claim_text,
    c.claim_type = 'workflow_configuration'

MERGE (i:Investigation {id: $investigation_id})
SET i.status = 'completed',
    i.verdict = 'supported_at_configuration_level',
    i.limitation = 'Successful runtime execution not verified'

MERGE (r:Repository {id: $repo_id})

WITH c, i, r
MATCH (e:Evidence {id: $evidence_id})

MERGE (r)-[:HAS_CLAIM]->(c)
MERGE (i)-[:EVALUATED]->(c)
MERGE (c)-[:SUPPORTED_BY]->(e)
MERGE (i)-[:USED_EVIDENCE]->(e)

SET e.evidence_role = 'documentation_build_workflow',
    e.supporting_lines = '1-6, 28-36, 102-115'

RETURN c.id, i.verdict, e.source, e.blob_sha
"""

result = graph.query(
    query,
    params={
        "claim_id": claim_id,
        "claim_text": claim_text,
        "investigation_id": investigation_id,
        "repo_id": repo_id,
        "evidence_id": evidence_id,
    },
)

for row in result.result_set:
    print(f"Claim ID: {row[0]}")
    print(f"Verdict: {row[1]}")
    print(f"Evidence file: {row[2]}")
    print(f"Blob SHA: {row[3]}")
