
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("ImpactGraph")

query = """
MERGE (c:Claim {id: 'claim-001'})
SET c.text = 'JWT authentication is implemented'

MERGE (e:Evidence {id: 'evidence-001'})
SET e.source = 'auth_middleware.py',
    e.evidence_type = 'source_file'

MERGE (c)-[:SUPPORTED_BY]->(e)

RETURN c.id AS claim_id, e.id AS evidence_id
"""

result = graph.query(query)

for row in result.result_set:
    print(f"Claim: {row[0]} -> Evidence: {row[1]}")
