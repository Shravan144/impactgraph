import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from report_finding import generate_report, list_recent_investigations
from graph_db import get_graph_stats, check_db_health, execute_query
from graph_algorithms import get_evidence_subgraph, compute_component_centrality
from mcp_server import handle_json_rpc
from agent_loop import run_autonomous_investigation_loop
from fetch_evidence import fetch_file_by_path
import config
from ui import UI_HTML
from investigation import (
    InvestigationRequest,
    collect_candidates,
    inspect_candidates,
    store_investigation,
)


app = FastAPI(
    title="ImpactGraph API",
    description="Evidence-backed software contribution analysis using FalkorDB",
    version="1.0.0",
)


class EvidenceItem(BaseModel):
    source: str
    blob_sha: str
    supporting_lines: str | None = None


class InvestigationReport(BaseModel):
    investigation_id: str
    claim: str
    verdict: str
    evidence: list[EvidenceItem]
    limitations: list[str]
    runtime_execution_verified: bool
    rationale: str | None = None
    subclaims_verified: list[str] | None = None
    traversed_paths: list[str] | None = None
    evaluation_mode: str | None = None
    timestamp: str | None = None


class LLMConfigureRequest(BaseModel):
    api_key: str
    model: str | None = None
    provider: str = "gemini"
    is_openrouter: bool = False


class CypherQueryRequest(BaseModel):
    cypher: str
    params: dict | None = None


@app.get("/")
def root(request: Request):
    """Serve the interactive UI for web browsers, or API info for JSON clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(UI_HTML)
    return {
        "message": "Welcome to ImpactGraph!",
        "status": "running",
        "hackathon_track": "Agents That Act on Connected Data",
        "database": "FalkorDB",
        "ui_url": "/ui",
        "mcp_endpoint": "/mcp",
    }


@app.get("/ui", response_class=HTMLResponse)
def get_ui():
    """Interactive single-page dashboard for hackathon live demo."""
    return HTMLResponse(UI_HTML)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/graph/stats")
def graph_statistics():
    """Return live node and relationship counts from FalkorDB."""
    return get_graph_stats()


@app.get("/graph/subgraph")
def get_subgraph(repository: str = "fastapi/fastapi", max_nodes: int = 50):
    """Return graph nodes and links for interactive visualization."""
    return get_evidence_subgraph(repository, max_nodes=max_nodes)


@app.get("/graph/centrality")
def get_centrality(repository: str = "fastapi/fastapi"):
    """Return component centrality analysis showing top architectural hubs."""
    return {"central_components": compute_component_centrality(repository)}


@app.get("/api/llm/status")
def get_llm_status():
    """Return current LLM provider status and model."""
    cfg = config.get_llm_config()
    return {
        "active": bool(cfg.get("api_key")),
        "provider": cfg.get("provider"),
        "model": cfg.get("model"),
    }


@app.post("/api/llm/configure")
def configure_llm(req: LLMConfigureRequest):
    """Dynamically set LLM credentials (Gemini/OpenRouter/OpenAI) for live evaluation."""
    provider = req.provider.lower()
    if req.is_openrouter and provider not in ("gemini", "openai"):
        provider = "openrouter"
    config.set_dynamic_llm_config(
        api_key=req.api_key,
        model=req.model,
        provider=provider,
        is_openrouter=req.is_openrouter,
    )
    return {
        "status": "configured",
        "provider": provider,
        "model": req.model or (
            config.GEMINI_MODEL if provider == "gemini" else (
                config.OPENROUTER_MODEL if provider == "openrouter" else config.OPENAI_MODEL
            )
        ),
    }


@app.post("/api/cypher/execute")
def execute_custom_cypher(req: CypherQueryRequest):
    """Interactive Cypher query console runner for FalkorDB."""
    start_time = time.time()
    try:
        res = execute_query(req.cypher, req.params or {})
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": True,
            "elapsed_ms": elapsed_ms,
            "header": res.header if res else [],
            "result_set": res.result_set if res else [],
        }
    except Exception as exc:
        return {
            "success": False,
            "elapsed_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(exc),
        }


@app.get("/api/evidence/content")
def get_evidence_content(repository: str, source: str):
    """Retrieve full cached or fetched source code for file drawer viewer."""
    try:
        # Check FalkorDB cache first
        cached = execute_query(
            "MATCH (e:Evidence {source: $source}) RETURN e.content, e.blob_sha",
            {"source": source},
        )
        if cached.result_set and cached.result_set[0][0]:
            return {
                "source": source,
                "content": cached.result_set[0][0],
                "sha": cached.result_set[0][1],
                "from_cache": True,
            }
        # Fallback fetch
        if "/" in repository:
            owner, repo = repository.split("/", 1)
            fetched = fetch_file_by_path(owner, repo, source)
            if fetched:
                return {
                    "source": source,
                    "content": fetched["content"],
                    "sha": fetched["sha"],
                    "from_cache": False,
                }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=404, detail="File content not found")


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Standard Model Context Protocol (MCP) JSON-RPC 2.0 endpoint."""
    try:
        body = await request.json()
        return handle_json_rpc(body)
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": str(exc)},
        }


@app.get("/investigations", response_model=list[dict])
def get_recent_investigations():
    """List recent investigations stored in FalkorDB."""
    return list_recent_investigations(limit=15)


@app.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationReport,
    response_model_exclude_none=True,
)
def get_investigation_report(investigation_id: str):
    try:
        return generate_report(investigation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/agent/investigate")
def run_autonomous_agent(request: InvestigationRequest):
    """Autonomous ReAct agent loop executing multi-hop graph reasoning with explainable trace."""
    try:
        return run_autonomous_investigation_loop(
            owner=request.owner,
            repo=request.repo,
            claim=request.claim,
            force_refresh=getattr(request, "force_refresh", False),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/investigations")
def create_investigation(request: InvestigationRequest):
    try:
        candidates = collect_candidates(request)
        investigation = inspect_candidates(candidates)
        report = store_investigation(investigation)
        return report

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Investigation failed: {exc}",
        ) from exc
