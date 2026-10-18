import logging
from typing import Any
from falkordb import FalkorDB
import config

logger = logging.getLogger("impactgraph.graph_db")

_db_instance: FalkorDB | None = None


def get_falkordb() -> FalkorDB:
    """Get or initialize the FalkorDB client connection (supports local or FalkorDB Cloud)."""
    global _db_instance
    if _db_instance is None:
        if config.FALKORDB_URL:
            _db_instance = FalkorDB.from_url(config.FALKORDB_URL)
        else:
            kwargs = {
                "host": config.FALKORDB_HOST,
                "port": config.FALKORDB_PORT,
            }
            if config.FALKORDB_USERNAME:
                kwargs["username"] = config.FALKORDB_USERNAME
            if config.FALKORDB_PASSWORD:
                kwargs["password"] = config.FALKORDB_PASSWORD
            if config.FALKORDB_SSL:
                kwargs["ssl"] = True
            _db_instance = FalkorDB(**kwargs)
    return _db_instance


def get_graph(graph_name: str | None = None):
    """Select the active graph in FalkorDB."""
    db = get_falkordb()
    name = graph_name or config.FALKORDB_GRAPH
    return db.select_graph(name)


def execute_query(query: str, params: dict[str, Any] | None = None):
    """Execute a parameterized Cypher query with safe fallback."""
    graph = get_graph()
    try:
        return graph.query(query, params=params or {})
    except Exception as exc:
        logger.error(f"FalkorDB query failed: {exc} | Query: {query} | Params: {params}")
        raise


def check_db_health() -> bool:
    """Check whether FalkorDB is reachable and responsive."""
    try:
        res = execute_query("RETURN 1 AS ping")
        return bool(res and res.result_set and res.result_set[0][0] == 1)
    except Exception:
        return False


def get_graph_stats() -> dict[str, Any]:
    """Retrieve node and relationship statistics from FalkorDB."""
    try:
        nodes_res = execute_query("MATCH (n) RETURN count(n) AS node_count")
        node_count = nodes_res.result_set[0][0] if nodes_res.result_set else 0

        rels_res = execute_query("MATCH ()-[r]->() RETURN count(r) AS rel_count")
        rel_count = rels_res.result_set[0][0] if rels_res.result_set else 0

        labels_res = execute_query("CALL db.labels()")
        labels = [row[0] for row in labels_res.result_set] if labels_res.result_set else []

        types_res = execute_query("CALL db.relationshipTypes()")
        rel_types = [row[0] for row in types_res.result_set] if types_res.result_set else []

        return {
            "status": "connected",
            "node_count": node_count,
            "relationship_count": rel_count,
            "labels": labels,
            "relationship_types": rel_types,
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "node_count": 0,
            "relationship_count": 0,
            "labels": [],
            "relationship_types": [],
        }
