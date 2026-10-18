import json
from mcp_server import handle_json_rpc, MCP_TOOLS


def test_mcp_initialize():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {},
    }
    resp = handle_json_rpc(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "impactgraph-mcp"


def test_mcp_tools_list():
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    resp = handle_json_rpc(req)
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]

    assert "graph_query" in tool_names
    assert "graph_traverse_neighborhood" in tool_names
    assert "graph_shortest_path" in tool_names
    assert "graph_centrality" in tool_names
    assert "graph_memory_recall" in tool_names
    assert "agent_investigate_claim" in tool_names


def test_mcp_tools_call_centrality():
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "graph_centrality",
            "arguments": {"repository": "fastapi/fastapi"},
        },
    }
    resp = handle_json_rpc(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 3
    content_text = resp["result"]["content"][0]["text"]
    parsed = json.loads(content_text)
    assert "central_components" in parsed
    assert len(parsed["central_components"]) > 0


def test_mcp_tools_call_neighborhood():
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "graph_traverse_neighborhood",
            "arguments": {
                "start_source": ".github/workflows/build-docs.yml",
                "max_hops": 2,
            },
        },
    }
    resp = handle_json_rpc(req)
    content_text = resp["result"]["content"][0]["text"]
    parsed = json.loads(content_text)
    assert "chains" in parsed
    assert parsed["count"] > 0


def test_mcp_tools_call_blast_radius():
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "graph_blast_radius",
            "arguments": {
                "repository": "fastapi/fastapi",
                "target_source": "scripts/docs.py",
            },
        },
    }
    resp = handle_json_rpc(req)
    content_text = resp["result"]["content"][0]["text"]
    parsed = json.loads(content_text)
    assert parsed["target_source"] == "scripts/docs.py"
    assert parsed["severity_score"] > 0
    assert len(parsed["affected_workflows"]) > 0


def test_mcp_tools_call_supply_chain():
    req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "graph_supply_chain_audit",
            "arguments": {
                "repository": "pallets/flask",
            },
        },
    }
    resp = handle_json_rpc(req)
    content_text = resp["result"]["content"][0]["text"]
    parsed = json.loads(content_text)
    assert "security_posture" in parsed
    assert parsed["total_dependencies"] > 0

