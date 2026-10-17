
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("ImpactGraph")

query = """
MERGE (r:Repository {id: 'repo-001'})
SET r.url = 'https://github.com/example/demo-api',
    r.name = 'demo-api'

MERGE (c:Claim {id: 'claim-002'})
SET c.text = 'The project implements JWT authentication',
    c.claim_type = 'implementation'

MERGE (e:Evidence {id: 'evidence-002'})
SET e.source = 'auth_middleware.py',
    e.evidence_type = 'source_file'

MERGE (s:Skill {id: 'skill-001'})
SET s.name = 'API Authentication'

MERGE (i:Investigation {id: 'investigation-001'})
SET i.status = 'completed'

MERGE (r)-[:HAS_CLAIM]->(c)
MERGE (c)-[:SUPPORTED_BY]->(e)
MERGE (e)-[:DEMONSTRATES]->(s)
MERGE (i)-[:EVALUATED]->(c)

RETURN r.name, c.text, e.source, s.name, i.status
"""

result = graph.query(query)

for row in result.result_set:
    print(f"Repository: {row[0]}")
    print(f"Claim: {row[1]}")
    print(f"Evidence: {row[2]}")
    print(f"Skill: {row[3]}")
    print(f"Investigation status: {row[4]}")
