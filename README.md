# ImpactGraph

**An Evidence-Driven Autonomous AI Investigation Agent Powered by FalkorDB Connected Data**

> **Hackathon Submission:** [Graph Hacks — WeMakeDevs × FalkorDB](https://www.wemakedevs.org/hackathons/falkordb)  
> **Track:** **Agents That Act on Connected Data**  
> **Mandatory Sponsor Technology:** **FalkorDB** (Graph Database & Vector/Graph Traversal Engine)  
> **Live Cloud Deployment:** [https://impactgraph-g0d1.onrender.com/](https://impactgraph-g0d1.onrender.com/)  
> **Cloud Database:** FalkorDB Cloud (`ap-south-1`)  
> **Model Context Protocol (MCP):** Native MCP Server (`/mcp` endpoint and `mcp_server.py`)  
> **Demo Video:** [Watch Demo Video (Placeholder)](https://youtu.be/placeholder-impactgraph-demo)  
> **Interactive Dashboard:** `https://impactgraph-g0d1.onrender.com/` (or local `http://localhost:8000/`)

---

## 1. Executive Summary & Problem Statement

Modern AI coding agents frequently suffer from hallucinations, vague claims, and surface-level keyword matching when reasoning about codebases. Given a claim such as:
> *"This project uses GitHub Actions to automate its documentation build."*

Typical search engines simply find files containing "docs" or "actions". They cannot verify whether:
1. The workflow actually executes a documentation generation command.
2. The workflow connects to an internal build script (`scripts/docs.py`) or external tool (`mkdocs`, `sphinx`).
3. The workflow was actually observed executing successfully in CI history, or merely exists as dormant configuration.
4. Earlier sessions by this or other agents already investigated and verified related capabilities.

**ImpactGraph** solves this by putting the agent's context and reasoning inside **FalkorDB**:
- Ingests public GitHub repositories into a connected property graph.
- Maps multi-hop relationships across workflows, scripts, modules, and external actions.
- Employs an **Autonomous ReAct Agent Loop** (Thought $\to$ Action $\to$ Observation) with FalkorDB graph tools.
- Executes **Graph Algorithms** (Degree Centrality, Shortest Path, Multi-Hop Neighborhoods).
- Implements **Cross-Session Memory** so the agent remembers prior verified facts across runs.
- Provides a native **Model Context Protocol (MCP)** server for universal agent interoperability.
- Verifies exact source line citations against real decoded blobs.
- Validates live runtime execution history via GitHub Actions API.

---

## 2. Why This Fits "Agents That Act on Connected Data"

In ImpactGraph, FalkorDB is **not a passive cache or display store**. It is the central connected knowledge graph that dictates the agent's decision-making:

- **Multi-Hop Traversal:** The agent follows multi-hop reference chains:  
  `(Repository) -> (:HAS_EVIDENCE) -> (Workflow) -> (:REFERENCES) -> (Build Script) -> (:REFERENCES) -> (Helper Module)`
- **Graph Queries & Algorithms as Agent Tools:** Graph traversal, shortest path, and degree centrality are exposed as callable tools that the agent invokes dynamically during its reasoning loop.
- **Tool Selection through Model Context Protocol (MCP):** ImpactGraph exposes a standard MCP JSON-RPC 2.0 server (`mcp_server.py` and `/mcp`) with 7 tools (`graph_query`, `graph_traverse_neighborhood`, `graph_shortest_path`, `graph_centrality`, `graph_memory_recall`, `agent_investigate_claim`, `graph_get_subgraph`).
- **Actions Based on What the Graph Shows:** The agent determines its next investigation action based on whether connected edges exist (e.g. if a workflow references a Python script, it navigates to that script to inspect build commands).
- **Cross-Session Memory:** The agent stores verified capabilities in FalkorDB (`:Fact`, `:Claim`, `:Investigation`) and recalls them in subsequent sessions, demonstrating long-term memory across sessions.
- **Rule 3 Compliance:** If FalkorDB is removed, ImpactGraph cannot perform multi-hop candidate discovery, cannot traverse connected execution scripts, cannot compute architectural centrality, and cannot recall historical session memory. The product runs on the graph.

---

## 3. Architecture & Autonomous ReAct Agent Loop

```mermaid
flowchart TD
    User["User Input: owner / repo / claim"] --> Agent["Autonomous ReAct Agent Loop"]
    
    subgraph FalkorDB_Context_Layer["FalkorDB Context & Memory Layer"]
        Memory["Cross-Session Memory<br/>(:Claim)<-[:EVALUATED]-(:Investigation)"]
        RepoNode["Repository Node<br/>(:Repository)"]
        EvidenceGraph["Evidence Subgraph<br/>(:Evidence)-[:REFERENCES]->(:Evidence)"]
        DepGraph["Dependency Edges<br/>(:Evidence)-[:USES_DEPENDENCY]->(:Dependency)"]
    end
    
    subgraph Agent_Tools["Agent Graph Tools & Algorithms"]
        T1["Tool 1: Memory Recall<br/>(recall_cross_session_memory)"]
        T2["Tool 2: Candidate Discovery<br/>(find_candidate_evidence)"]
        T3["Tool 3: Multi-Hop Traversal<br/>(traverse_multihop_neighborhood)"]
        T4["Tool 4: Line Inspector<br/>(inspect_candidate)"]
        T5["Tool 5: Runtime Scoper<br/>(fetch_workflow_runs)"]
        T6["Tool 6: Centrality Hubs<br/>(compute_component_centrality)"]
    end

    Agent -->|Step 1: Check Memory| T1 --> Memory
    Agent -->|Step 2: Ensure Ingestion| RepoNode
    Agent -->|Step 3: Graph Discovery| T2 --> EvidenceGraph
    Agent -->|Step 4: Traverse Multi-Hop| T3 --> EvidenceGraph
    Agent -->|Step 5: Inspect Exact Lines| T4
    Agent -->|Step 6: Query Telemetry| T5
    Agent -->|Step 7: Persist Finding| FalkorDB_Context_Layer
    Agent --> UI["Interactive Force-Directed UI & MCP Output"]
```

### 7-Step Autonomous ReAct Trace
Each investigation produces an explainable step-by-step trace:
1. **Memory Recall:** Queries FalkorDB to check if prior sessions already investigated related repository claims.
2. **Graph Ingestion:** Verifies or builds the connected property graph in FalkorDB.
3. **Candidate Discovery:** Matches candidate entry points using combined path and keyword signals.
4. **Multi-Hop Traversal:** Traverses `[:REFERENCES]` and `[:USES_DEPENDENCY]` up to 3 hops outward.
5. **Evidence Inspection:** Validates exact source lines in decoded blobs (never hallucinates line numbers).
6. **Runtime Telemetry:** Queries GitHub Actions API (`/actions/workflows/.../runs`) to verify live execution history.
7. **Verdict Synthesis & Memory Storage:** Evaluates subclaims into a structured verdict and writes the audit trail to FalkorDB.

---

## 4. FalkorDB Graph Schema

### Node Labels
- `:Repository`: `id`, `name`, `url`, `default_branch`, `description`
- `:Evidence`: `id`, `source`, `evidence_type`, `blob_sha`, `size`, `content`, `supporting_lines`
- `:Dependency`: `id`, `name`, `type` (`"github_action"`, `"tool"`, `"python_module"`)
- `:Claim`: `id`, `text`, `verdict`
- `:Investigation`: `id`, `status`, `verdict`, `rationale`, `subclaims_verified`, `runtime_execution_verified`, `evaluation_mode`, `timestamp`

### Relationship Types
- `(r:Repository)-[:HAS_EVIDENCE]->(e:Evidence)`
- `(e1:Evidence)-[:REFERENCES {type: 'invoked_script' | 'imported_module'}]->(e2:Evidence)`
- `(e:Evidence)-[:USES_DEPENDENCY]->(d:Dependency)`
- `(r:Repository)-[:HAS_CLAIM]->(c:Claim)`
- `(c:Claim)-[:SUPPORTED_BY]->(e:Evidence)`
- `(c:Claim)-[:CONTRADICTED_BY]->(e:Evidence)`
- `(i:Investigation)-[:EVALUATED]->(c:Claim)`
- `(i:Investigation)-[:USED_EVIDENCE]->(e:Evidence)`
- `(i:Investigation)-[:TRAVERSED_PATH]->(e:Evidence)`

---

### 5. Important Cypher Queries & Graph Algorithms

#### 1. Architectural Blast Radius & Cascading Impact
```cypher
MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(target:Evidence)
WHERE target.source = $target_source
MATCH (downstream:Evidence)-[ref:REFERENCES]->(target)
RETURN downstream.source, downstream.evidence_type, type(ref), ref.type
```

#### 2. Supply Chain & DevSecOps Dependency Exposure
```cypher
MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)-[:USES_DEPENDENCY]->(d:Dependency)
RETURN e.source AS workflow, d.name AS dependency_name, d.type AS dependency_type
```

#### 3. Multi-Hop Neighborhood Traversal (2-Hop & 3-Hop Chains)
```cypher
MATCH (e:Evidence {source: $start_source})
OPTIONAL MATCH (e)-[r1:REFERENCES]->(e2:Evidence)
OPTIONAL MATCH (e2)-[r2:REFERENCES]->(e3:Evidence)
OPTIONAL MATCH (e)-[d1:USES_DEPENDENCY]->(dep:Dependency)
RETURN e.source, e2.source, e3.source, dep.name, dep.type
```

#### 4. Architecture Centrality & Critical Hub Detection
```cypher
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
```

#### 5. Cross-Session Memory Recall
```cypher
MATCH (r:Repository {id: $repo_id})-[:HAS_CLAIM]->(c:Claim)<-[:EVALUATED]-(i:Investigation)
WHERE i.verdict IN ['supported', 'partially_supported', 'contradicted']
RETURN c.id, c.text, i.id, i.verdict, i.rationale, i.runtime_execution_verified, i.timestamp
ORDER BY i.timestamp DESC
LIMIT 5
```

---

## 6. Model Context Protocol (MCP) Integration & Interactive Playground

ImpactGraph natively implements the official **Model Context Protocol (MCP)** specification:

### Exposed MCP Tools (10 Native Tools)
1. `graph_blast_radius`: Compute cascading architectural impact and blast radius if a file/component is modified.
2. `graph_supply_chain_audit`: Perform an automated DevSecOps supply-chain audit across GitHub Actions and dependencies.
3. `agent_drill_down_chat`: Conversational graph-guided reasoning tool answering follow-up questions.
4. `graph_query`: Execute read-only Cypher queries against FalkorDB.
5. `graph_traverse_neighborhood`: Multi-hop radius exploration across references and dependencies.
6. `graph_shortest_path`: Compute shortest relationship paths between files.
7. `graph_centrality`: Detect core architecture hubs and bottlenecks using degree centrality.
8. `graph_memory_recall`: Retrieve prior verified claims across sessions.
9. `agent_investigate_claim`: Run the full autonomous ReAct investigation loop.
10. `graph_get_subgraph`: Retrieve visual node-link data for canvas rendering.

### Connecting via Stdio (Cursor / Claude Desktop / Antigravity)
Add this to your MCP configuration file (`claude_desktop_config.json` or Cursor MCP settings):
```json
{
  "mcpServers": {
    "impactgraph": {
      "command": "python",
      "args": ["d:/project/impactgraph/backend/mcp_server.py"],
      "env": {
        "FALKORDB_HOST": "localhost",
        "FALKORDB_PORT": "6379",
        "FALKORDB_GRAPH": "ImpactGraph"
      }
    }
  }
}
```

Or communicate via HTTP POST JSON-RPC 2.0 at `http://localhost:8000/mcp`.

---

## 7. Real Example Investigation

### Input
- **Repository:** `fastapi/fastapi`
- **Claim:** *"This project uses GitHub Actions to automate its documentation build."*

### Autonomous Investigation Output
```json
{
  "investigation_id": "investigation-92db31555dd0",
  "repository": "fastapi/fastapi",
  "claim": "This project uses GitHub Actions to automate its documentation build.",
  "verdict": "supported",
  "rationale": "The repository configures automated documentation building via GitHub Actions workflow '.github/workflows/build-docs.yml'. Inspected lines confirm execution steps for documentation generation. Connected graph traversal in FalkorDB links this workflow directly to '.github/workflows/build-docs.yml -[:USES_DEPENDENCY]-> uv'. Live runtime execution was confirmed via GitHub Actions: run #39057578930 (success).",
  "evidence_count": 3,
  "subclaims_verified": [
    "GitHub Actions documentation workflow file exists.",
    "Workflow specifies automated event triggers (e.g. push / pull_request).",
    "Workflow executes documentation build commands/scripts.",
    "FalkorDB graph traversal connects workflow to the invoked build script."
  ],
  "runtime_execution_verified": true,
  "evaluation_mode": "deterministic_rule_engine"
}
```

---

## 8. Deployment & Quickstart

### Option A: One-Command Docker Compose (Easiest Local Setup)
Clone the repository and run:
```bash
git clone https://github.com/shravanb2005/impactgraph.git
cd impactgraph
docker compose up --build
```
This automatically spins up both the **FalkorDB** container and the **ImpactGraph Agent backend + UI** on `http://localhost:8000`.

---

### Option B: Local Virtual Environment Setup

#### Step 1: Start FalkorDB
```bash
docker run -p 6379:6379 -p 3000:3000 -it --rm --name impactgraph-db falkordb/falkordb:latest
```

#### Step 2: Setup Environment
```bash
git clone https://github.com/shravanb2005/impactgraph.git
cd impactgraph

python -m venv backend/.venv
# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1
# Linux / macOS:
source backend/.venv/bin/activate

pip install -r backend/requirements.txt
cp .env.example .env
```

#### Step 3: Run the Test Suite (26/26 Passing)
```bash
pytest -o pythonpath=backend backend/tests
```

#### Step 4: Launch ImpactGraph
```bash
python -m uvicorn main:app --app-dir backend --reload --port 8000
```
Open your browser at **`http://localhost:8000`** or **`http://localhost:8000/ui`**!

---

### Option C: Live Cloud Deployment (FalkorDB Cloud + Render)

1. **FalkorDB Cloud**:
   - Create a free database at [FalkorDB Cloud](https://app.falkordb.cloud/).
   - Copy your connection string or Host, Port, and Password.
2. **Render Web Service**:
   - Fork / push this repo to GitHub and connect it to [Render](https://render.com/).
   - Select the included `render.yaml` Blueprint or set:
     - **Build Command:** `pip install -r backend/requirements.txt`
     - **Start Command:** `uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT`
     - **Environment Variables:**
       - `FALKORDB_URL`: Your FalkorDB Cloud URL (e.g. `falkor://username:password@cloud-instance.falkordb.cloud:12345`)
       - `GEMINI_API_KEY`: Google Gemini Key
       - `OPENROUTER_API_KEY`: (Optional) OpenRouter Key

---

## 9. Safety & Scoping Limitations

1. **Zero Execution of Untrusted Code:** ImpactGraph only fetches and inspects text blobs. It never executes arbitrary shell commands, install scripts, or untrusted repository code.
2. **Runtime Verification vs Configuration:** Source configuration in git is explicitly separated from live execution. A workflow file in git is never reported as successful runtime execution unless confirmed via live GitHub Actions API runs.
3. **Insufficiency vs Contradiction:** A missing file or absence of evidence in the inspected sample is categorized as `insufficient_evidence`, not `contradicted`.

---

## 10. AI Coding Assistance Disclosure

AI coding assistance (Google Antigravity / Gemini) was utilized during the development of this hackathon submission for scaffolding, test generation, and architectural pair programming. All architecture, graph queries, evaluation logic, and schemas were reviewed, tested, and verified by the participant.

---

## 11. Hackathon Submission Verification Checklist

- [x] **Track Selected:** Agents That Act on Connected Data
- [x] **Mandatory Technology:** FalkorDB graph engine central to retrieval and reasoning
- [x] **Multi-Hop Reasoning:** Demonstrated with multi-hop reference chains
- [x] **Graph Queries & Algorithms as Tools:** Centrality, Shortest Path, Neighborhood Traversal, Blast Radius, Supply Chain Audit
- [x] **Model Context Protocol (MCP):** Implemented 10 tools via `backend/mcp_server.py`, `/mcp`, and live UI playground
- [x] **Cross-Session Memory:** Stores and recalls prior investigations in FalkorDB
- [x] **Conversational Drill-Down:** Follow-up Q&A grounded in live graph relationships
- [x] **Interactive Dashboard:** Force-directed network canvas, ReAct trace visualizer, and live MCP playground
- [x] **Automated Tests:** 26/26 passing pytest tests
- [x] **Security:** Untrusted code is never executed; secrets excluded via `.env.example`
- [x] **Public Source Code:** Clean repository on GitHub
