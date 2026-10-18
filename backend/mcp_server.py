import sys
import json
import logging
from typing import Any

from graph_db import execute_query, get_graph_stats
from graph_algorithms import (
    traverse_multihop_neighborhood,
    find_shortest_path,
    compute_component_centrality,
    recall_cross_session_memory,
    get_evidence_subgraph,
)
from investigation import (
    InvestigationRequest,
    collect_candidates,
    inspect_candidates,
    store_investigation,
)
from claim_matcher import extract_keywords

logger = logging.getLogger("impactgraph.mcp")

# MCP Tool Definitions complying with Model Context Protocol specification
MCP_TOOLS = [
    {
        "name": "graph_query",
        "description": "Execute a parameterized Cypher query on the FalkorDB ImpactGraph database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cypher": {"type": "string", "description": "The Cypher query to execute"},
                "params": {"type": "object", "description": "Query parameters mapping", "default": {}},
            },
            "required": ["cypher"],
        },
    },
    {
        "name": "graph_traverse_neighborhood",
        "description": "Perform multi-hop traversal in FalkorDB from a source file across REFERENCES and USES_DEPENDENCY edges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_source": {"type": "string", "description": "Starting file path (e.g. .github/workflows/build-docs.yml)"},
                "max_hops": {"type": "integer", "description": "Maximum hops to traverse (default 3)", "default": 3},
            },
            "required": ["start_source"],
        },
    },
    {
        "name": "graph_shortest_path",
        "description": "Find the shortest connection path between two repository files/components in FalkorDB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_path": {"type": "string", "description": "Origin file path"},
                "target_path": {"type": "string", "description": "Target file path"},
            },
            "required": ["source_path", "target_path"],
        },
    },
    {
        "name": "graph_centrality",
        "description": "Run graph centrality analysis on a repository in FalkorDB to find key architectural hubs and bottlenecks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Repository identifier (e.g. fastapi/fastapi)"},
            },
            "required": ["repository"],
        },
    },
    {
        "name": "graph_memory_recall",
        "description": "Recall prior verified claims, investigations, and facts across sessions from FalkorDB graph memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Repository identifier (e.g. fastapi/fastapi)"},
                "query": {"type": "string", "description": "Query or claim topic to recall"},
            },
            "required": ["repository", "query"],
        },
    },
    {
        "name": "agent_investigate_claim",
        "description": "Run full autonomous evidence-backed investigation on a repository claim using FalkorDB connected data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "GitHub repository owner"},
                "repo": {"type": "string", "description": "GitHub repository name"},
                "claim": {"type": "string", "description": "Natural language claim to evaluate"},
            },
            "required": ["owner", "repo", "claim"],
        },
    },
    {
        "name": "graph_get_subgraph",
        "description": "Get nodes and edges for visual rendering of repository connected evidence in FalkorDB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Repository identifier (e.g. fastapi/fastapi)"},
                "max_nodes": {"type": "integer", "description": "Maximum nodes to return", "default": 40},
            },
            "required": ["repository"],
        },
    },
]


def handle_tool_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute MCP tool calls against FalkorDB and agent pipeline."""
    try:
        if name == "graph_query":
            cypher = arguments.get("cypher", "")
            params = arguments.get("params", {})
            res = execute_query(cypher, params)
            return {
                "result_set": res.result_set if res else [],
                "header": res.header if res else [],
            }

        elif name == "graph_traverse_neighborhood":
            start_source = arguments["start_source"]
            max_hops = arguments.get("max_hops", 3)
            chains = traverse_multihop_neighborhood(start_source, max_hops=max_hops)
            return {"chains": chains, "count": len(chains)}

        elif name == "graph_shortest_path":
            src = arguments["source_path"]
            tgt = arguments["target_path"]
            paths = find_shortest_path(src, tgt)
            return {"paths": paths, "found": len(paths) > 0}

        elif name == "graph_centrality":
            repo = arguments["repository"]
            central = compute_component_centrality(repo)
            return {"central_components": central}

        elif name == "graph_memory_recall":
            repo = arguments["repository"]
            q = arguments["query"]
            kws = extract_keywords(q)
            memories = recall_cross_session_memory(repo, kws)
            return {"recalled_memories": memories, "count": len(memories)}

        elif name == "agent_investigate_claim":
            owner = arguments["owner"]
            repo = arguments["repo"]
            claim = arguments["claim"]
            req = InvestigationRequest(owner=owner, repo=repo, claim=claim)
            cands = collect_candidates(req)
            inspected = inspect_candidates(cands)
            report = store_investigation(inspected)
            return report

        elif name == "graph_get_subgraph":
            repo = arguments["repository"]
            max_nodes = arguments.get("max_nodes", 40)
            subgraph = get_evidence_subgraph(repo, max_nodes=max_nodes)
            return subgraph

        else:
            return {"error": f"Unknown tool: {name}"}

    except Exception as exc:
        return {"error": str(exc)}


def handle_json_rpc(request_data: dict[str, Any]) -> dict[str, Any]:
    """Standard JSON-RPC 2.0 handler for Model Context Protocol."""
    method = request_data.get("method")
    req_id = request_data.get("id")
    params = request_data.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOLS},
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        result = handle_tool_call(tool_name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
            },
        }

    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "impactgraph-mcp",
                    "version": "1.0.0",
                    "description": "FalkorDB Evidence-Backed Code Graph MCP Server",
                },
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio_server():
    """Run MCP server over stdio for AI assistants (Cursor, Claude Desktop, Antigravity)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_json_rpc(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
