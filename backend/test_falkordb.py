
from falkordb import FalkorDB

db = FalkorDB(host="localhost", port=6379)

graph = db.select_graph("ImpactGraph")

result = graph.query("RETURN 1 AS number")

print(result.result_set)
