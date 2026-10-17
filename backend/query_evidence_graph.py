
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)
graph = db.select_graph("ImpactGraph")

query = """
MATCH (c:Claim {id: 'claim-001'})
      -[:SUPPORTED_BY]->
      (e:Evidence {id: 'evidence-001'})
RETURN count(*) AS relationship_count
"""

result = graph.query(query)

print("Matching evidence relationships:", result.result_set[0][0])
