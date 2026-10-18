import logging
from typing import Any
from graph_db import execute_query

logger = logging.getLogger("impactgraph.algorithms")


def get_evidence_subgraph(
    repository: str,
    focus_sources: list[str] | None = None,
    max_nodes: int = 50,
) -> dict[str, list[dict[str, Any]]]:
    """
    Extract a connected subgraph for visualization and multi-hop analysis.
    Returns nodes and edges formatted for interactive graph rendering.
    """
    repo_id = repository.lower()

    # Query nodes
    query_nodes = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)
    OPTIONAL MATCH (e)-[:USES_DEPENDENCY]->(d:Dependency)
    RETURN e.id, e.source, e.evidence_type, e.blob_sha, d.id, d.name, d.type
    LIMIT $max_nodes
    """
    res = execute_query(query_nodes, {"repo_id": repo_id, "max_nodes": max_nodes})

    nodes_map: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    # Add Repository node
    nodes_map[repo_id] = {
        "id": repo_id,
        "label": repo_id,
        "type": "repository",
        "group": "repository",
    }

    for row in res.result_set:
        e_id, e_src, e_type, e_sha, d_id, d_name, d_type = row

        if e_id and e_id not in nodes_map:
            nodes_map[e_id] = {
                "id": e_id,
                "label": e_src,
                "source": e_src,
                "type": e_type or "source_file",
                "sha": e_sha,
                "group": "evidence",
            }
            # Link repo to evidence
            edges.append({
                "source": repo_id,
                "target": e_id,
                "label": "HAS_EVIDENCE",
                "type": "HAS_EVIDENCE",
            })

        if d_id and d_id not in nodes_map:
            nodes_map[d_id] = {
                "id": d_id,
                "label": d_name or d_id,
                "type": d_type or "dependency",
                "group": "dependency",
            }
            edges.append({
                "source": e_id,
                "target": d_id,
                "label": "USES_DEPENDENCY",
                "type": "USES_DEPENDENCY",
            })

    # Query cross-file references between evidence
    query_refs = """
    MATCH (e1:Evidence)-[r:REFERENCES]->(e2:Evidence)
    WHERE e1.id STARTS WITH $prefix
    RETURN e1.id, e2.id, r.type
    """
    ref_res = execute_query(query_refs, {"prefix": f"{repo_id}:"})
    for row in ref_res.result_set:
        src_id, tgt_id, ref_type = row
        if src_id in nodes_map and tgt_id in nodes_map:
            edges.append({
                "source": src_id,
                "target": tgt_id,
                "label": "REFERENCES",
                "type": "REFERENCES",
                "detail": ref_type,
            })

    return {
        "nodes": list(nodes_map.values()),
        "edges": edges,
    }


def find_shortest_path(
    source_path: str,
    target_path: str,
    repository: str | None = None,
) -> list[dict[str, Any]]:
    """
    Find the shortest path between two files or components in the graph.
    Demonstrates multi-hop relationship chains.
    """
    query = """
    MATCH (e1:Evidence {source: $source_path})
    MATCH (e2:Evidence {source: $target_path})
    MATCH p = shortestPath((e1)-[:REFERENCES*1..4]-(e2))
    RETURN [n IN nodes(p) | {source: n.source, id: n.id, type: labels(n)[0]}] AS path_nodes,
           [r IN relationships(p) | type(r)] AS path_rels
    """
    try:
        res = execute_query(query, {"source_path": source_path, "target_path": target_path})
        if res.result_set:
            path_nodes, path_rels = res.result_set[0]
            return [{"nodes": path_nodes, "relationships": path_rels}]
    except Exception as exc:
        logger.debug(f"Shortest path query fallback: {exc}")

    # Fallback to direct connection check
    check_query = """
    MATCH (e1:Evidence {source: $source_path})-[r:REFERENCES]->(e2:Evidence {source: $target_path})
    RETURN e1.source, type(r), e2.source
    """
    res = execute_query(check_query, {"source_path": source_path, "target_path": target_path})
    if res.result_set:
        return [{
            "nodes": [
                {"source": res.result_set[0][0], "type": "Evidence"},
                {"source": res.result_set[0][2], "type": "Evidence"},
            ],
            "relationships": [res.result_set[0][1]],
        }]

    return []


def traverse_multihop_neighborhood(
    start_source: str,
    max_hops: int = 3,
) -> list[dict[str, Any]]:
    """
    Traverse outward from a starting file through [:REFERENCES] and [:USES_DEPENDENCY]
    to discover connected scripts, modules, and external actions up to max_hops away.
    """
    traversal_chains = []

    # 1-hop and 2-hop traversal query
    query = """
    MATCH (e:Evidence {source: $start_source})
    OPTIONAL MATCH (e)-[r1:REFERENCES]->(e2:Evidence)
    OPTIONAL MATCH (e2)-[r2:REFERENCES]->(e3:Evidence)
    OPTIONAL MATCH (e)-[d1:USES_DEPENDENCY]->(dep:Dependency)
    RETURN e.source, e2.source, e3.source, dep.name, dep.type
    """
    res = execute_query(query, {"start_source": start_source})

    for row in res.result_set:
        src, hop1, hop2, dep_name, dep_type = row
        if hop1:
            chain = f"{src} -[:REFERENCES]-> {hop1}"
            if hop2:
                chain += f" -[:REFERENCES]-> {hop2}"
            traversal_chains.append({
                "type": "code_reference_chain",
                "chain": chain,
                "target": hop2 or hop1,
                "depth": 2 if hop2 else 1,
            })
        if dep_name:
            traversal_chains.append({
                "type": "dependency_chain",
                "chain": f"{src} -[:USES_DEPENDENCY]-> {dep_name} ({dep_type})",
                "target": dep_name,
                "depth": 1,
            })

    # Deduplicate chains
    unique_chains = []
    seen = set()
    for item in traversal_chains:
        if item["chain"] not in seen:
            seen.add(item["chain"])
            unique_chains.append(item)

    return unique_chains


def compute_component_centrality(repository: str) -> list[dict[str, Any]]:
    """
    Compute graph centrality (degree centrality / connected hubs)
    to discover the most critical architectural files in the repository.
    """
    repo_id = repository.lower()
    query = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)
    OPTIONAL MATCH (e)-[out_r:REFERENCES]->()
    OPTIONAL MATCH ()-[in_r:REFERENCES]->(e)
    OPTIONAL MATCH (e)-[d:USES_DEPENDENCY]->()
    RETURN e.source AS source,
           e.evidence_type AS type,
           count(DISTINCT out_r) AS out_degree,
           count(DISTINCT in_r) AS in_degree,
           count(DISTINCT d) AS dependency_count,
           (count(DISTINCT out_r) * 2 + count(DISTINCT in_r) * 3 + count(DISTINCT d)) AS centrality_score
    ORDER BY centrality_score DESC
    LIMIT 10
    """
    res = execute_query(query, {"repo_id": repo_id})
    central_components = []
    for row in res.result_set:
        source, ev_type, out_deg, in_deg, dep_cnt, score = row
        if score > 0:
            central_components.append({
                "source": source,
                "type": ev_type,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "dependency_count": dep_cnt,
                "centrality_score": score,
            })
    return central_components


def recall_cross_session_memory(repository: str, keywords: set[str]) -> list[dict[str, Any]]:
    """
    Cross-Session Agent Memory:
    Queries FalkorDB for previously evaluated claims and verified facts
    so the agent remembers past investigations and avoids redundant work.
    """
    repo_id = repository.lower()
    query = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_CLAIM]->(c:Claim)<-[:EVALUATED]-(i:Investigation)
    WHERE i.verdict IN ['supported', 'partially_supported', 'contradicted']
    RETURN c.id, c.text, i.id, i.verdict, i.rationale, i.runtime_execution_verified, i.timestamp
    ORDER BY i.timestamp DESC
    LIMIT 5
    """
    res = execute_query(query, {"repo_id": repo_id})
    memories = []
    for row in res.result_set:
        claim_id, claim_text, inv_id, verdict, rationale, runtime_verified, timestamp = row
        # Check relevance to current keywords
        claim_lower = (claim_text or "").lower()
        relevance = sum(1 for kw in keywords if kw in claim_lower)
        memories.append({
            "claim_id": claim_id,
            "claim_text": claim_text,
            "investigation_id": inv_id,
            "verdict": verdict,
            "rationale": rationale,
            "runtime_execution_verified": bool(runtime_verified),
            "timestamp": timestamp,
            "relevance_score": relevance,
        })

    # Sort memories by relevance score then freshness
    memories.sort(key=lambda m: (-m["relevance_score"], m["timestamp"] or ""))
    return memories
