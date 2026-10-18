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


def analyze_blast_radius(repository: str, target_source: str, max_depth: int = 3) -> dict[str, Any]:
    """
    Computes cascading architectural impact and blast radius if target_source is modified or broken.
    Traverses incoming and outgoing REFERENCES and USES_DEPENDENCY edges in FalkorDB.
    """
    repo_id = repository.lower()

    # 1. Downstream Dependents (Who breaks if target changes?)
    downstream_query = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(target:Evidence)
    WHERE target.source = $target_source OR target.source ENDS WITH $target_source
    MATCH (downstream:Evidence)-[ref:REFERENCES]->(target)
    RETURN downstream.source, downstream.evidence_type, type(ref), ref.type
    """
    res_down = execute_query(downstream_query, {"repo_id": repo_id, "target_source": target_source})

    affected_files = []
    affected_workflows = []
    affected_tests = []
    for row in res_down.result_set:
        src, ev_type, r_type, detail = row
        item = {"source": src, "type": ev_type, "reference_type": detail or "code_reference"}
        affected_files.append(item)
        if (src or "").startswith(".github/workflows/"):
            affected_workflows.append(src)
        elif "test" in (src or "").lower():
            affected_tests.append(src)

    # 2. Upstream Dependencies (What does target depend upon?)
    upstream_query = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(target:Evidence)
    WHERE target.source = $target_source OR target.source ENDS WITH $target_source
    OPTIONAL MATCH (target)-[ref:REFERENCES]->(dep:Evidence)
    OPTIONAL MATCH (target)-[:USES_DEPENDENCY]->(d:Dependency)
    RETURN dep.source, dep.evidence_type, d.name, d.type
    """
    res_up = execute_query(upstream_query, {"repo_id": repo_id, "target_source": target_source})

    internal_dependencies = []
    external_dependencies = []
    for row in res_up.result_set:
        dep_src, dep_type, d_name, d_type = row
        if dep_src:
            internal_dependencies.append({"source": dep_src, "type": dep_type})
        if d_name:
            external_dependencies.append({"name": d_name, "type": d_type})

    # Deduplicate
    unique_affected = list({f["source"]: f for f in affected_files}.values())
    unique_internal = list({d["source"]: d for d in internal_dependencies}.values())
    unique_external = list({d["name"]: d for d in external_dependencies}.values())
    unique_workflows = list(set(affected_workflows))
    unique_tests = list(set(affected_tests))

    # Compute severity score
    severity_score = (len(unique_workflows) * 5) + (len(unique_tests) * 3) + (len(unique_affected) * 2) + len(unique_external)
    severity_level = "CRITICAL" if severity_score >= 15 else ("HIGH" if severity_score >= 8 else ("MEDIUM" if severity_score >= 3 else "LOW"))

    propagation_chains = []
    for wf in unique_workflows:
        propagation_chains.append(f"{wf} -> [EXECUTES/REFERENCES] -> {target_source}")
    for t in unique_tests:
        propagation_chains.append(f"{t} -> [TESTS/IMPORTS] -> {target_source}")
    for ext in unique_external:
        propagation_chains.append(f"{target_source} -> [USES] -> {ext.get('name', '')}")

    return {
        "target_source": target_source,
        "repository": repository,
        "severity_score": severity_score,
        "severity_level": severity_level,
        "affected_workflows": unique_workflows,
        "affected_tests": unique_tests,
        "affected_files": unique_affected,
        "internal_dependencies": unique_internal,
        "external_dependencies": unique_external,
        "propagation_chains": propagation_chains,
    }


def audit_supply_chain_security(repository: str) -> dict[str, Any]:
    """
    Performs an automated DevSecOps supply-chain audit across GitHub Actions and dependencies in FalkorDB.
    Identifies unpinned actions, SHA-pinned dependencies, and heavily shared actions.
    """
    repo_id = repository.lower()
    query = """
    MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)-[:USES_DEPENDENCY]->(d:Dependency)
    RETURN e.source, d.name, d.type
    """
    res = execute_query(query, {"repo_id": repo_id})

    action_map = {}
    for row in res.result_set:
        src, dep_name, dep_type = row
        if not dep_name:
            continue
        if dep_name not in action_map:
            action_map[dep_name] = {
                "name": dep_name,
                "type": dep_type,
                "used_in": [],
                "is_pinned_sha": False,
                "version_tag": None,
                "risk_level": "LOW",
            }
        if src not in action_map[dep_name]["used_in"]:
            action_map[dep_name]["used_in"].append(src)

    audited_items = []
    unpinned_count = 0
    pinned_count = 0

    for dep_name, item in action_map.items():
        if "@" in dep_name:
            base, ref = dep_name.split("@", 1)
            item["version_tag"] = ref
            if len(ref) == 40 and all(c in "0123456789abcdefABCDEF" for c in ref):
                item["is_pinned_sha"] = True
                item["risk_level"] = "LOW (SHA Pinned)"
                pinned_count += 1
            elif ref in ("master", "main", "latest"):
                item["is_pinned_sha"] = False
                item["risk_level"] = "CRITICAL (Floating Branch Tag)"
                unpinned_count += 1
            else:
                item["is_pinned_sha"] = False
                item["risk_level"] = "MEDIUM (Version Tag, not immutable SHA)"
                unpinned_count += 1
        else:
            item["risk_level"] = "INFO (CLI/Binary Tool)"

        audited_items.append(item)

    audited_items.sort(key=lambda x: (
        0 if "CRITICAL" in x["risk_level"] else (1 if "MEDIUM" in x["risk_level"] else 2),
        -len(x["used_in"])
    ))

    return {
        "repository": repository,
        "total_dependencies": len(audited_items),
        "pinned_sha_count": pinned_count,
        "unpinned_count": unpinned_count,
        "security_posture": "STRONG" if (pinned_count > unpinned_count) else ("MODERATE" if pinned_count > 0 else "NEEDS_HARDENING"),
        "dependencies": audited_items,
    }


def drill_down_graph_chat(repository: str, user_query: str, history: list[dict] | None = None) -> dict[str, Any]:
    """
    Conversational follow-up agent powered by FalkorDB connected graph data and LLM reasoning.
    Understands graph relationships, traces paths, and answers specific user drill-down questions.
    """
    import config
    import httpx
    import json
    from claim_matcher import extract_keywords

    repo_id = repository.lower()
    keywords = extract_keywords(user_query)

    relevant_paths = []
    for kw in list(keywords)[:4]:
        q_src = """
        MATCH (repo:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)
        WHERE toLower(e.source) CONTAINS $kw
        OPTIONAL MATCH (e)-[ref:REFERENCES]->(dep:Evidence)
        OPTIONAL MATCH (e)-[:USES_DEPENDENCY]->(d:Dependency)
        RETURN e.source, dep.source, d.name LIMIT 4
        """
        res = execute_query(q_src, {"repo_id": repo_id, "kw": kw})
        for r in res.result_set:
            e_src, dep_src, d_name = r
            if dep_src:
                relevant_paths.append(f"{e_src} -[:REFERENCES]-> {dep_src}")
            if d_name:
                relevant_paths.append(f"{e_src} -[:USES_DEPENDENCY]-> {d_name}")

    memories = recall_cross_session_memory(repository, keywords)
    centrality = compute_component_centrality(repository)[:3]

    graph_context = {
        "repository": repository,
        "user_query": user_query,
        "connected_paths_in_graph": list(set(relevant_paths))[:8],
        "historical_investigations": [
            {"claim": m["claim_text"], "verdict": m["verdict"]}
            for m in memories[:2]
        ],
        "architectural_hubs": [c["source"] for c in centrality],
    }

    prompt = f"""You are the ImpactGraph AI Pair Programmer & Graph Investigator.
Repository: {repository}
User Question: "{user_query}"

Live FalkorDB Graph Context:
{json.dumps(graph_context, indent=2)}

Answer the user's question clearly and concisely, directly referencing the connected graph nodes, paths, or dependencies from FalkorDB.
If asked about shortest path, impact, or why an action is used, cite the specific relationships.
Output a helpful explanation in 2-4 sentences."""

    llm_cfg = config.get_llm_config()
    api_key = llm_cfg.get("api_key")
    provider = llm_cfg.get("provider", "gemini")
    model = llm_cfg.get("model", "gemini-3.8-flash")
    base_url = llm_cfg.get("base_url")

    if api_key:
        try:
            if provider == "gemini":
                url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = httpx.post(url, json=payload, timeout=45.0)
                if resp.status_code == 200:
                    answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "answer": answer.strip(),
                        "graph_context": graph_context,
                        "source": f"LLM ({provider} - {model})"
                    }
            else:
                url = f"{base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                }
                resp = httpx.post(url, headers=headers, json=payload, timeout=45.0)
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"]
                    return {
                        "answer": answer.strip(),
                        "graph_context": graph_context,
                        "source": f"LLM ({provider} - {model})"
                    }
        except Exception as exc:
            logger.warning(f"Drill-down LLM call failed: {exc}")

    if relevant_paths:
        answer = f"In FalkorDB, the following connected graph relationships were found related to your query: {'; '.join(list(set(relevant_paths))[:4])}."
    else:
        answer = f"In repository '{repository}', architectural hubs include {', '.join(c['source'] for c in centrality)}. No direct cross-file references matched your exact query keywords."

    return {
        "answer": answer,
        "graph_context": graph_context,
        "source": "deterministic_graph_engine"
    }

