UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ImpactGraph — Autonomous Connected Data Agent (FalkorDB)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090d16;
            --surface: #101626;
            --surface-hover: #1b2438;
            --border: #23304a;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --primary-glow: rgba(59, 130, 246, 0.25);
            --falkor-orange: #ff5722;
            --falkor-glow: rgba(255, 87, 34, 0.25);
            --text-main: #f9fafb;
            --text-muted: #94a3b8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --purple: #a855f7;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.5;
            overflow-x: hidden;
        }

        header {
            background: rgba(16, 22, 38, 0.85);
            backdrop-filter: blur(14px);
            border-bottom: 1px solid var(--border);
            padding: 0.85rem 2rem;
            position: sticky;
            top: 0;
            z-index: 50;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo-wrap { display: flex; align-items: center; gap: 0.75rem; }
        .logo-icon {
            width: 42px; height: 42px;
            background: linear-gradient(135deg, var(--primary), var(--falkor-orange));
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-weight: 800; font-size: 1.35rem; color: white;
            box-shadow: 0 0 25px var(--primary-glow);
        }
        .logo-text h1 { font-size: 1.35rem; font-weight: 800; letter-spacing: -0.02em; }
        .logo-text span { font-size: 0.75rem; color: var(--text-muted); display: block; }

        .header-actions { display: flex; align-items: center; gap: 0.75rem; }
        .btn-settings {
            background: #1e293b; border: 1px solid #334155; color: #cbd5e1;
            padding: 0.4rem 0.85rem; border-radius: 8px; font-size: 0.8rem;
            font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 0.4rem;
            transition: all 0.2s;
        }
        .btn-settings:hover { background: #334155; color: white; border-color: var(--primary); }

        .badge {
            font-size: 0.75rem; padding: 0.35rem 0.8rem;
            border-radius: 9999px; font-weight: 600;
            display: inline-flex; align-items: center; gap: 0.4rem;
        }
        .badge-falkordb { background: rgba(255, 87, 34, 0.15); border: 1px solid var(--falkor-orange); color: #ff784e; }
        .badge-track { background: rgba(59, 130, 246, 0.15); border: 1px solid var(--primary); color: #60a5fa; }
        .badge-pulse { width: 8px; height: 8px; background: var(--success); border-radius: 50%; box-shadow: 0 0 10px var(--success); }

        /* Nav Tabs */
        .tabs-nav {
            display: flex; gap: 0.5rem; max-width: 1350px; margin: 1.5rem auto 0;
            padding: 0 1.5rem; border-bottom: 1px solid var(--border);
        }
        .tab-btn {
            background: transparent; border: none; color: var(--text-muted);
            padding: 0.75rem 1.25rem; font-size: 0.9rem; font-weight: 600;
            cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.2s;
        }
        .tab-btn.active { color: #60a5fa; border-bottom-color: var(--primary); }
        .tab-btn:hover:not(.active) { color: white; }

        main { max-width: 1350px; margin: 1.5rem auto 3rem; padding: 0 1.5rem; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .hero { text-align: center; margin-bottom: 2rem; }
        .hero h2 {
            font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em;
            background: linear-gradient(135deg, #ffffff 40%, #94a3b8);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .hero p { color: var(--text-muted); font-size: 1.05rem; max-width: 820px; margin: 0 auto; }

        .stats-strip {
            display: flex; gap: 1.5rem; background: var(--surface);
            border: 1px solid var(--border); border-radius: 12px;
            padding: 0.85rem 1.5rem; margin-bottom: 2rem; font-size: 0.85rem;
            color: var(--text-muted); justify-content: center; flex-wrap: wrap;
        }
        .stat-value { font-weight: 700; color: var(--text-main); }

        .grid-layout { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 2rem; margin-bottom: 2rem; }
        @media (max-width: 1000px) { .grid-layout { grid-template-columns: 1fr; } }

        .card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; padding: 1.6rem;
            box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
        }
        .card-title {
            font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem;
            display: flex; align-items: center; justify-content: space-between;
        }

        .form-group { margin-bottom: 1.25rem; }
        label { display: block; font-size: 0.85rem; font-weight: 600; color: #d1d5db; margin-bottom: 0.4rem; }
        .repo-inputs { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
        input[type="text"], textarea, select {
            width: 100%; background: #090e1a; border: 1px solid var(--border);
            border-radius: 8px; padding: 0.7rem 0.85rem; color: white;
            font-size: 0.9rem; font-family: inherit; transition: all 0.2s;
        }
        input[type="text"]:focus, textarea:focus, select:focus {
            outline: none; border-color: var(--primary); box-shadow: 0 0 10px var(--primary-glow);
        }
        textarea { resize: vertical; min-height: 85px; }

        .presets { margin-top: 0.75rem; }
        .presets-label { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.4rem; display: block; }
        .preset-btn {
            background: #172136; border: 1px solid #2d3e5e; color: #cbd5e1;
            padding: 0.35rem 0.65rem; border-radius: 6px; font-size: 0.78rem;
            cursor: pointer; margin-right: 0.4rem; margin-bottom: 0.4rem; transition: all 0.15s;
        }
        .preset-btn:hover { background: #233352; color: white; border-color: var(--primary); }

        .btn-submit {
            width: 100%; background: linear-gradient(135deg, var(--primary), #1d4ed8);
            border: none; color: white; padding: 0.9rem; border-radius: 10px;
            font-weight: 700; font-size: 1.05rem; cursor: pointer;
            box-shadow: 0 4px 18px var(--primary-glow); transition: all 0.2s;
            display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-top: 1rem;
        }
        .btn-submit:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 24px rgba(59, 130, 246, 0.4); }
        .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

        /* ReAct Trace Visualizer */
        .trace-container { display: flex; flex-direction: column; gap: 0.75rem; max-height: 420px; overflow-y: auto; padding-right: 0.5rem; }
        .trace-step {
            background: #090e1a; border: 1px solid var(--border); border-radius: 10px;
            padding: 0.85rem 1rem; font-size: 0.85rem; transition: all 0.3s;
        }
        .trace-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.35rem; }
        .trace-pill {
            font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
            padding: 0.18rem 0.55rem; border-radius: 5px;
        }
        .trace-thought { color: #94a3b8; font-style: italic; margin-bottom: 0.3rem; }
        .trace-action { color: #38bdf8; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; margin-bottom: 0.2rem; }
        .trace-obs { color: #34d399; font-size: 0.82rem; }

        /* Graph Canvas Container */
        .graph-viz-card { margin-bottom: 2rem; background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.6rem; }
        .canvas-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
        .canvas-wrap {
            position: relative; width: 100%; height: 460px;
            background: radial-gradient(circle at center, #111a2e 0%, #060911 100%);
            border: 1px solid #1e293b; border-radius: 10px; overflow: hidden;
            cursor: grab;
        }
        .canvas-wrap:active { cursor: grabbing; }
        canvas { width: 100%; height: 100%; display: block; }
        .graph-legend {
            display: flex; gap: 1.25rem; margin-top: 0.75rem; font-size: 0.78rem;
            color: var(--text-muted); justify-content: center; flex-wrap: wrap;
        }
        .legend-item { display: flex; align-items: center; gap: 0.4rem; }
        .legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }

        /* Results Display */
        .results-section { display: none; margin-top: 2rem; }
        .verdict-banner {
            padding: 1.4rem 1.6rem; border-radius: 14px; margin-bottom: 1.5rem;
            display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
        }
        .verdict-supported { background: rgba(16, 185, 129, 0.12); border: 1px solid var(--success); }
        .verdict-partially_supported { background: rgba(245, 158, 11, 0.12); border: 1px solid var(--warning); }
        .verdict-contradicted { background: rgba(239, 68, 68, 0.12); border: 1px solid var(--danger); }
        .verdict-insufficient_evidence { background: rgba(6, 182, 212, 0.12); border: 1px solid var(--info); }

        .verdict-title { font-size: 1.45rem; font-weight: 800; display: flex; align-items: center; gap: 0.5rem; }
        .verdict-pill {
            padding: 0.3rem 0.85rem; border-radius: 9999px;
            font-size: 0.82rem; font-weight: 700; text-transform: uppercase;
        }
        .pill-supported { background: var(--success); color: black; }
        .pill-partially_supported { background: var(--warning); color: black; }
        .pill-contradicted { background: var(--danger); color: white; }
        .pill-insufficient_evidence { background: var(--info); color: black; }

        .rationale-box {
            font-size: 1.02rem; color: #e2e8f0; margin-bottom: 1.5rem;
            background: #090e1a; padding: 1.1rem 1.35rem; border-radius: 10px;
            border-left: 4px solid var(--primary);
        }

        .graph-paths-box {
            background: #090e1a; border: 1px solid #1e293b;
            border-radius: 10px; padding: 1.1rem 1.35rem; margin-bottom: 1.5rem;
        }
        .graph-path-tag {
            display: inline-block; background: #172136; border: 1px solid #2d3e5e;
            color: #38bdf8; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
            padding: 0.35rem 0.65rem; border-radius: 6px; margin: 0.3rem 0.3rem 0.3rem 0;
        }

        .evidence-card {
            background: #090e1a; border: 1px solid var(--border);
            border-radius: 10px; margin-bottom: 1rem; overflow: hidden;
        }
        .evidence-header {
            padding: 0.85rem 1.1rem; background: #141c2e; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
            font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
        }
        .btn-view-code {
            background: #1e293b; border: 1px solid #334155; color: #38bdf8;
            padding: 0.25rem 0.6rem; border-radius: 5px; font-size: 0.78rem;
            cursor: pointer; transition: all 0.15s;
        }
        .btn-view-code:hover { background: #334155; color: white; }

        .evidence-body {
            padding: 1rem 1.1rem; font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem; line-height: 1.6; background: #060911; overflow-x: auto;
        }
        .code-line.highlight {
            color: #38bdf8; background: rgba(56, 189, 248, 0.1);
            border-left: 3px solid #38bdf8; padding-left: 0.5rem; font-weight: 500;
        }

        .limitations-box {
            background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.25);
            border-radius: 10px; padding: 1.1rem; margin-top: 1.5rem; font-size: 0.85rem; color: #fbbf24;
        }

        /* Slide-Out Code Drawer */
        .drawer-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px);
            z-index: 100; display: none;
        }
        .drawer {
            position: fixed; top: 0; right: -650px; width: 620px; max-width: 90vw; height: 100vh;
            background: #090e1a; border-left: 1px solid var(--border);
            z-index: 101; display: flex; flex-direction: column; transition: right 0.3s ease-out;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
        }
        .drawer.open { right: 0; }
        .drawer-header {
            padding: 1.25rem 1.5rem; background: #101626; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .drawer-body {
            flex: 1; padding: 1.25rem 1.5rem; overflow-y: auto;
            font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; line-height: 1.6;
        }
        .code-table { width: 100%; border-collapse: collapse; }
        .code-table td { padding: 0.1rem 0.5rem; vertical-align: top; }
        .code-line-no { color: #475569; user-select: none; text-align: right; width: 40px; }
        .code-line-text { white-space: pre-wrap; word-break: break-all; }
        .code-line-highlighted { background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-weight: 600; }

        /* Settings Modal */
        .modal {
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 520px; max-width: 92vw; background: var(--surface); border: 1px solid var(--border);
            border-radius: 14px; padding: 2rem; z-index: 105; display: none;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
        }

        /* Centrality & Cypher Tables */
        .data-table { width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.85rem; }
        .data-table th, .data-table td { padding: 0.6rem 0.85rem; text-align: left; border-bottom: 1px solid #1e293b; }
        .data-table th { color: #94a3b8; font-weight: 600; background: #0c1220; }

        footer {
            text-align: center; padding: 3rem; color: var(--text-muted);
            font-size: 0.85rem; border-top: 1px solid var(--border); margin-top: 5rem;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-wrap">
            <div class="logo-icon">⚡</div>
            <div class="logo-text">
                <h1>ImpactGraph</h1>
                <span>Autonomous Connected Data Agent Powered by FalkorDB</span>
            </div>
        </div>
        <div class="header-actions">
            <button class="btn-settings" onclick="openSettingsModal()">
                ⚙️ <span id="llmIndicatorText">LLM Settings</span>
            </button>
            <div class="badge badge-falkordb">
                <span class="badge-pulse"></span> FalkorDB Engine
            </div>
            <div class="badge badge-track">
                Track: Agents That Act on Connected Data
            </div>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <div class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab('tab-investigate')">🚀 Autonomous Agent</button>
        <button class="tab-btn" onclick="switchTab('tab-blast')">💥 Blast Radius & Impact</button>
        <button class="tab-btn" onclick="switchTab('tab-supply')">🛡️ Supply Chain Audit</button>
        <button class="tab-btn" onclick="switchTab('tab-cypher')">💻 Cypher Console</button>
        <button class="tab-btn" onclick="switchTab('tab-mcp')">🔌 MCP Tools & Playground</button>
        <button class="tab-btn" onclick="switchTab('tab-centrality')">📊 Architecture Hubs</button>
    </div>

    <main>
        <!-- TAB 1: Autonomous Agent Investigation -->
        <div id="tab-investigate" class="tab-content active">
            <div class="hero">
                <h2>Autonomous Multi-Hop Graph Investigation</h2>
                <p>Decomposes claims into verifiable checkpoints, traverses multi-hop edges in FalkorDB, validates live CI runtime telemetry, and cites verified source lines.</p>
            </div>

            <div id="statsStrip" class="stats-strip">
                <div>Graph: <span id="statGraphName" class="stat-value">ImpactGraph</span></div>
                <div>FalkorDB Nodes: <span id="statNodes" class="stat-value">...</span></div>
                <div>Connected Relationships: <span id="statEdges" class="stat-value">...</span></div>
                <div>Active Reasoning Engine: <span id="statEngine" class="stat-value" style="color:#60a5fa;">Deterministic + LLM Hybrid</span></div>
            </div>

            <!-- Interactive Force-Directed Graph -->
            <div class="graph-viz-card">
                <div class="canvas-toolbar">
                    <span class="card-title" style="margin: 0;">FalkorDB Connected Evidence Subgraph</span>
                    <div>
                        <button class="btn-view-code" onclick="resetGraphPhysics()">Reset Layout</button>
                        <button class="btn-view-code" onclick="loadSubgraph(document.getElementById('ownerInput').value + '/' + document.getElementById('repoInput').value)">Reload Graph</button>
                    </div>
                </div>
                <div class="canvas-wrap" id="canvasWrap">
                    <canvas id="graphCanvas"></canvas>
                </div>
                <div class="graph-legend">
                    <div class="legend-item"><span class="legend-dot" style="background: #a855f7;"></span> Repository</div>
                    <div class="legend-item"><span class="legend-dot" style="background: #3b82f6;"></span> Workflow / Config</div>
                    <div class="legend-item"><span class="legend-dot" style="background: #10b981;"></span> Script / Source</div>
                    <div class="legend-item"><span class="legend-dot" style="background: #f59e0b;"></span> Dependency / Action</div>
                    <div class="legend-item"><span class="legend-dot" style="background: #ef4444; border: 2px solid white;"></span> Traversed by Agent</div>
                </div>
            </div>

            <div class="grid-layout">
                <!-- Left: Form -->
                <div class="card">
                    <div class="card-title">
                        <span>Launch Investigation</span>
                        <span style="font-size: 0.75rem; color: var(--text-muted);">Self-Healing Ingestion</span>
                    </div>
                    <form id="investigateForm">
                        <div class="form-group">
                            <label>Public GitHub Repository</label>
                            <div class="repo-inputs">
                                <input type="text" id="ownerInput" placeholder="owner" value="fastapi" required>
                                <input type="text" id="repoInput" placeholder="repo" value="fastapi" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Claim to Investigate</label>
                            <textarea id="claimInput" required>This project uses GitHub Actions to automate its documentation build.</textarea>
                        </div>

                        <div class="presets">
                            <span class="presets-label">Evaluation Test Presets:</span>
                            <button type="button" class="preset-btn" onclick="setPreset('fastapi', 'fastapi', 'This project uses GitHub Actions to automate its documentation build.')">FastAPI Docs Build (Supported)</button>
                            <button type="button" class="preset-btn" onclick="setPreset('fastapi', 'fastapi', 'This project runs pre-commit hooks to automate repository maintenance.')">FastAPI Pre-commit (Supported)</button>
                            <button type="button" class="preset-btn" onclick="setPreset('pallets', 'flask', 'Flask uses GitHub Actions for continuous integration testing.')">Flask CI Testing (pallets/flask)</button>
                            <button type="button" class="preset-btn" onclick="setPreset('fastapi', 'fastapi', 'This project uses CircleCI for Docker container deployment.')">FastAPI CircleCI (Contradicted / Insufficient)</button>
                        </div>

                        <button type="submit" id="submitBtn" class="btn-submit">
                            <span id="btnIcon">⚡</span> <span id="btnText">Launch Autonomous Agent</span>
                        </button>
                    </form>
                </div>

                <!-- Right: ReAct Trace -->
                <div class="card">
                    <div class="card-title">
                        <span>Autonomous ReAct Trace</span>
                        <span id="liveStatusPill" class="badge" style="background:#172136; color:#94a3b8;">Idle</span>
                    </div>
                    <div id="traceContainer" class="trace-container">
                        <p style="color: var(--text-muted); font-size: 0.85rem; font-style: italic;">
                            Click "Launch Autonomous Agent" to watch the agent execute Thought ➔ Action ➔ Observation cycles across FalkorDB.
                        </p>
                    </div>

                    <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border);">
                        <label style="font-size: 0.8rem;">Recall Historical Investigation by ID:</label>
                        <div style="display: flex; gap: 0.5rem; margin-top: 0.3rem;">
                            <input type="text" id="lookupIdInput" placeholder="investigation-..." style="padding: 0.4rem 0.6rem; font-size: 0.8rem;">
                            <button type="button" class="preset-btn" style="margin: 0;" onclick="lookupInvestigation()">Recall</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Results Section -->
            <div id="resultsSection" class="results-section">
                <div id="verdictBanner" class="verdict-banner">
                    <div>
                        <div class="verdict-title">
                            <span id="verdictIcon">✅</span>
                            <span>Verdict: <span id="verdictText">Supported</span></span>
                            <span id="verdictPill" class="verdict-pill pill-supported">SUPPORTED</span>
                        </div>
                        <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.35rem;">
                            Investigation ID: <span id="resInvestigationId" style="font-family: monospace; color: white;">...</span> |
                            Mode: <span id="resMode" style="color: #60a5fa;">...</span>
                        </div>
                    </div>
                    <div>
                        <span id="runtimeVerifiedBadge" class="badge"></span>
                    </div>
                </div>

                <div class="card" style="margin-bottom: 1.5rem;">
                    <div class="card-title">Explainable Agent Rationale</div>
                    <div id="rationaleText" class="rationale-box">...</div>

                    <div id="subclaimsContainer" style="margin-bottom: 1rem;">
                        <label>Verified Subclaims & Checkpoints:</label>
                        <ul id="subclaimsList" style="margin-left: 1.25rem; font-size: 0.88rem; color: #cbd5e1;"></ul>
                    </div>

                    <div class="card-title" style="margin-top: 1.5rem;">FalkorDB Multi-Hop Traversal Chains</div>
                    <div id="graphPathsContainer" class="graph-paths-box">
                        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.5rem;">The agent traversed these exact multi-hop edge paths in FalkorDB to substantiate its verdict:</p>
                        <div id="graphPathsList"></div>
                    </div>

                    <div class="card-title">Supporting Evidence & Exact Line Citations</div>
                    <div id="evidenceList"></div>

                    <div id="limitationsBox" class="limitations-box">
                        <strong>Investigation Scope & Limitations:</strong>
                        <ul id="limitationsList" style="margin-left: 1.25rem; margin-top: 0.4rem;"></ul>
                    </div>

                    <!-- Conversational Drill-Down Follow-Up -->
                    <div style="margin-top: 1.5rem; padding: 1.25rem; background: #0b1329; border: 1px solid #1e3a8a; border-radius: 12px;">
                        <div class="card-title" style="color: #60a5fa; margin-bottom: 0.4rem;">
                            <span>💬 Conversational Drill-Down (Ask FalkorDB Agent)</span>
                            <span style="font-size:0.75rem; color:#94a3b8; font-weight:normal;">Multi-Hop Graph Context</span>
                        </div>
                        <p style="font-size:0.82rem; color:#94a3b8; margin-bottom:0.75rem;">
                            Have questions about why certain files were cited, how paths connect, or component dependencies? Ask the agent directly:
                        </p>
                        <div style="display:flex; gap:0.5rem; margin-bottom:0.6rem;">
                            <input type="text" id="drillDownQuery" placeholder="e.g. Why does build-docs.yml reference scripts/docs.py?" style="flex:1;">
                            <button type="button" class="btn-submit" style="width:auto; padding:0.6rem 1.25rem; margin:0;" onclick="submitDrillDown()">Ask Agent</button>
                        </div>
                        <div class="presets">
                            <span class="presets-label">Quick Inquiries:</span>
                            <button type="button" class="preset-btn" onclick="setDrillDownQuestion('Why does build-docs.yml reference scripts/docs.py?')">Why docs reference?</button>
                            <button type="button" class="preset-btn" onclick="setDrillDownQuestion('What dependencies are shared between test workflows?')">Shared test dependencies?</button>
                            <button type="button" class="preset-btn" onclick="setDrillDownQuestion('What is the shortest path between docs and tests?')">Docs to tests path?</button>
                        </div>
                        <div id="drillDownAnswerBox" style="display:none; margin-top:1rem; padding:1rem; background:#070d19; border-radius:8px; border-left:3px solid #3b82f6;">
                            <div style="font-size:0.75rem; color:#60a5fa; font-weight:700; margin-bottom:0.35rem;" id="drillDownSource">Agent Response:</div>
                            <div id="drillDownAnswerText" style="font-size:0.9rem; line-height:1.5; color:#f1f5f9;">...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: Blast Radius & Cascading Impact Engine -->
        <div id="tab-blast" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span>💥 Architectural Blast Radius & Cascading Impact Engine</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #f87171;">FalkorDB Path Propagation</span>
                </div>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.25rem;">
                    Know what breaks before merging changes. ImpactGraph queries FalkorDB to trace downstream workflows, tests, and dependent source files that rely on any given file or component.
                </p>
                <div style="display:grid; grid-template-columns: 2fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                    <div>
                        <label>Target File or Component to Analyze:</label>
                        <input type="text" id="blastTargetInput" value="scripts/docs.py" placeholder="e.g. scripts/docs.py or src/flask/testing.py">
                    </div>
                    <div style="display:flex; align-items:flex-end;">
                        <button class="btn-submit" style="margin:0; height:42px; width:100%;" onclick="runBlastRadiusAnalysis()">⚡ Calculate Blast Radius</button>
                    </div>
                </div>
                <div class="presets" style="margin-bottom:1.25rem;">
                    <span class="presets-label">Preset Components to Test:</span>
                    <button type="button" class="preset-btn" onclick="setBlastTarget('scripts/docs.py')">fastapi: scripts/docs.py</button>
                    <button type="button" class="preset-btn" onclick="setBlastTarget('.github/workflows/build-docs.yml')">fastapi: build-docs.yml</button>
                    <button type="button" class="preset-btn" onclick="setBlastTarget('src/flask/testing.py')">flask: src/flask/testing.py</button>
                    <button type="button" class="preset-btn" onclick="setBlastTarget('.github/workflows/tests.yaml')">flask: tests.yaml</button>
                </div>

                <!-- Blast Radius Results -->
                <div id="blastResults" style="display:none; margin-top:1.5rem;">
                    <div id="blastSeverityBanner" style="padding:1rem 1.25rem; border-radius:10px; margin-bottom:1.25rem; display:flex; justify-content:space-between; align-items:center; background:#1e1b4b; border:1px solid #4338ca;">
                        <div>
                            <span style="font-size:1.15rem; font-weight:800;" id="blastSeverityTitle">CRITICAL IMPACT</span>
                            <div style="font-size:0.82rem; margin-top:0.25rem; color:#cbd5e1;" id="blastSeverityDesc">Modifying this component impacts core CI pipelines and automated tests.</div>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:1.8rem; font-weight:900; color:#38bdf8;" id="blastScore">0</span>
                            <div style="font-size:0.7rem; color:#94a3b8; text-transform:uppercase;">Impact Score</div>
                        </div>
                    </div>

                    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:1rem; margin-bottom:1.5rem;">
                        <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                            <div style="font-size:0.75rem; color:#94a3b8;">Impacted Workflows</div>
                            <div style="font-size:1.4rem; font-weight:700; color:#ef4444;" id="blastWfCount">0</div>
                        </div>
                        <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                            <div style="font-size:0.75rem; color:#94a3b8;">Impacted Test Suites</div>
                            <div style="font-size:1.4rem; font-weight:700; color:#f59e0b;" id="blastTestCount">0</div>
                        </div>
                        <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                            <div style="font-size:0.75rem; color:#94a3b8;">Dependent Source Files</div>
                            <div style="font-size:1.4rem; font-weight:700; color:#38bdf8;" id="blastFilesCount">0</div>
                        </div>
                        <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                            <div style="font-size:0.75rem; color:#94a3b8;">External Dependencies</div>
                            <div style="font-size:1.4rem; font-weight:700; color:#a855f7;" id="blastDepsCount">0</div>
                        </div>
                    </div>

                    <div>
                        <div class="card-title">Cascading Propagation Chains in FalkorDB</div>
                        <div id="blastChainsList" style="display:flex; flex-direction:column; gap:0.5rem; max-height:280px; overflow-y:auto;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 3: Supply Chain & DevSecOps Audit -->
        <div id="tab-supply" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span>🛡️ Supply Chain & GitHub Actions Security Audit</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399;">DevSecOps Graph Intelligence</span>
                </div>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.25rem;">
                    ImpactGraph evaluates all external GitHub Actions and dependencies in FalkorDB, detecting floating branch tags, outdated action versions, and unpinned dependencies across CI pipelines.
                </p>

                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.25rem;">
                    <div style="display:flex; gap:1rem; align-items:center;">
                        <span style="font-size:0.9rem; font-weight:600;">Repository Security Posture:</span>
                        <span id="supplyPostureBadge" class="badge" style="background:rgba(16, 185, 129, 0.2); color:#34d399; font-size:0.85rem; padding:0.3rem 0.8rem;">STRONG</span>
                    </div>
                    <button class="btn-view-code" onclick="loadSupplyChainAudit()">🔄 Refresh Audit</button>
                </div>

                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1rem; margin-bottom:1.5rem;">
                    <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Total Audited Dependencies</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#38bdf8;" id="supplyTotalCount">...</div>
                    </div>
                    <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Immutable SHA Pinned (Hardened)</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#10b981;" id="supplyPinnedCount">...</div>
                    </div>
                    <div style="background:#090e1a; padding:1rem; border-radius:8px; border:1px solid var(--border);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Unpinned / Floating Tags (Risk)</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#f59e0b;" id="supplyUnpinnedCount">...</div>
                    </div>
                </div>

                <div style="max-height: 420px; overflow-y: auto;">
                    <table class="data-table" id="supplyTable">
                        <thead>
                            <tr>
                                <th>Action / Dependency</th>
                                <th>Security Risk Assessment</th>
                                <th>Workflows Using It</th>
                                <th>Referencing Files</th>
                            </tr>
                        </thead>
                        <tbody id="supplyBody"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TAB 4: Cypher Console -->
        <div id="tab-cypher" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span>FalkorDB Interactive Cypher Console</span>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">Direct parameterized query execution</span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Run custom Cypher queries directly against the FalkorDB graph engine.
                </p>
                <div class="form-group">
                    <label>Cypher Query:</label>
                    <textarea id="cypherInput" style="min-height: 100px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">MATCH (e:Evidence)-[r:REFERENCES]->(ref:Evidence) RETURN e.source, type(r), ref.source LIMIT 10</textarea>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap;">
                    <button class="btn-view-code" onclick="setCypherQuery('MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence) RETURN r.id, count(e) AS file_count')">Repository Files</button>
                    <button class="btn-view-code" onclick="setCypherQuery('MATCH (e:Evidence)-[r:REFERENCES]->(ref:Evidence) RETURN e.source, type(r), ref.source LIMIT 10')">Cross-File References</button>
                    <button class="btn-view-code" onclick="setCypherQuery('MATCH (e:Evidence)-[:USES_DEPENDENCY]->(d:Dependency) RETURN e.source, d.name, d.type LIMIT 10')">Dependencies</button>
                    <button class="btn-view-code" onclick="setCypherQuery('MATCH (r:Repository)-[:HAS_CLAIM]->(c)<-[:EVALUATED]-(i) RETURN r.id, c.text, i.verdict, i.timestamp LIMIT 10')">Session Memory</button>
                </div>
                <button class="btn-submit" style="width: auto; padding: 0.6rem 1.5rem;" onclick="runCypherQuery()">Execute Cypher</button>

                <div id="cypherResultsWrap" style="margin-top: 1.5rem; display: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <span style="font-size: 0.85rem; font-weight: 600;">Query Results:</span>
                            <div style="display: flex; background: #0f172a; padding: 2px; border-radius: 6px; border: 1px solid var(--border);">
                                <button id="btnCypherViewTable" class="btn-view-code" style="padding: 0.25rem 0.75rem; font-size: 0.75rem; background: #1e293b; color: #38bdf8;" onclick="toggleCypherView('table')">📋 Table View</button>
                                <button id="btnCypherViewGraph" class="btn-view-code" style="padding: 0.25rem 0.75rem; font-size: 0.75rem; background: transparent; color: #94a3b8;" onclick="toggleCypherView('graph')">🕸️ Visual Graph Canvas</button>
                            </div>
                        </div>
                        <span id="cypherElapsed" style="font-size: 0.75rem; color: #38bdf8; font-family: monospace;"></span>
                    </div>

                    <!-- Table View Container -->
                    <div id="cypherTableContainer" style="max-height: 380px; overflow-y: auto; overflow-x: auto;">
                        <table class="data-table" id="cypherTable">
                            <thead id="cypherThead"></thead>
                            <tbody id="cypherTbody"></tbody>
                        </table>
                    </div>

                    <!-- Visual Graph Canvas Container -->
                    <div id="cypherGraphContainer" style="display: none; position: relative;">
                        <canvas id="cypherCanvas" width="900" height="420" style="width: 100%; height: 420px; background: #070c18; border-radius: 8px; border: 1px solid var(--border); display: block;"></canvas>
                        <div style="position: absolute; top: 12px; right: 12px; display: flex; gap: 0.5rem; font-size: 0.75rem; flex-wrap: wrap;">
                            <span style="background: rgba(15,23,42,0.85); padding: 0.25rem 0.6rem; border-radius: 4px; border: 1px solid var(--border); color: #cbd5e1;">
                                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981; margin-right:4px;"></span>Evidence / File
                            </span>
                            <span style="background: rgba(15,23,42,0.85); padding: 0.25rem 0.6rem; border-radius: 4px; border: 1px solid var(--border); color: #cbd5e1;">
                                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#f59e0b; margin-right:4px;"></span>Dependency
                            </span>
                            <span style="background: rgba(15,23,42,0.85); padding: 0.25rem 0.6rem; border-radius: 4px; border: 1px solid var(--border); color: #cbd5e1;">
                                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#3b82f6; margin-right:4px;"></span>Workflow
                            </span>
                            <span style="background: rgba(15,23,42,0.85); padding: 0.25rem 0.6rem; border-radius: 4px; border: 1px solid var(--border); color: #cbd5e1;">
                                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#a855f7; margin-right:4px;"></span>Repository
                            </span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; font-size: 0.75rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">
                            <span id="cypherGraphLegendText">Generated from live FalkorDB Cypher query. Drag canvas to pan, scroll to zoom.</span>
                            <button class="btn-view-code" style="padding: 0.2rem 0.5rem; font-size: 0.7rem;" onclick="resetCypherGraphView()">Center Graph</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 5: MCP Tools & Live Playground -->
        <div id="tab-mcp" class="tab-content">
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-title">
                    <span>🔌 Model Context Protocol (MCP) Live Playground</span>
                    <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">JSON-RPC 2.0 Client Runner</span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Test and verify any of ImpactGraph's 10 MCP tools live in the browser using the official JSON-RPC 2.0 protocol.
                </p>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.25rem;">
                    <!-- Playground Runner Form -->
                    <div style="background:#090e1a; padding:1.25rem; border-radius:10px; border:1px solid var(--border);">
                        <div class="form-group">
                            <label>Select MCP Tool:</label>
                            <select id="mcpToolSelect" onchange="onMCPToolSelectChange()">
                                <option value="graph_blast_radius">graph_blast_radius (Impact Propagation)</option>
                                <option value="graph_supply_chain_audit">graph_supply_chain_audit (DevSecOps Audit)</option>
                                <option value="agent_drill_down_chat">agent_drill_down_chat (Conversational Q&A)</option>
                                <option value="graph_centrality">graph_centrality (Degree Centrality Hubs)</option>
                                <option value="graph_traverse_neighborhood">graph_traverse_neighborhood (Multi-Hop)</option>
                                <option value="graph_shortest_path">graph_shortest_path (Shortest Path)</option>
                                <option value="graph_memory_recall">graph_memory_recall (Cross-Session Memory)</option>
                                <option value="graph_query">graph_query (Direct Cypher Runner)</option>
                                <option value="graph_get_subgraph">graph_get_subgraph (Visual Subgraph)</option>
                                <option value="agent_investigate_claim">agent_investigate_claim (Autonomous Agent)</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>JSON Arguments:</label>
                            <textarea id="mcpToolArgs" style="font-family:'JetBrains Mono'; font-size:0.8rem; min-height:120px;">{
  "repository": "fastapi/fastapi",
  "target_source": "scripts/docs.py"
}</textarea>
                        </div>

                        <button class="btn-submit" style="margin:0; width:100%;" onclick="runMCPPlayground()">▶ Send MCP JSON-RPC Request</button>
                    </div>

                    <!-- Playground Response Display -->
                    <div style="background:#090e1a; padding:1.25rem; border-radius:10px; border:1px solid var(--border); display:flex; flex-direction:column;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:0.5rem;">
                            <span style="font-size:0.8rem; font-weight:600; color:#94a3b8;">JSON-RPC 2.0 Response:</span>
                            <span id="mcpPlaygroundElapsed" style="font-size:0.75rem; color:#34d399; font-family:monospace;"></span>
                        </div>
                        <pre id="mcpPlaygroundResponse" style="flex:1; background:#040711; padding:0.75rem; border-radius:6px; color:#38bdf8; font-size:0.75rem; overflow:auto; max-height:240px; margin:0;">// Select a tool and click 'Send MCP JSON-RPC Request' to test.</pre>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">
                    <span>Registered MCP Tool Manifest (10 Tools)</span>
                    <span style="font-size:0.75rem; color:var(--text-muted);">Standard tools/list Endpoint</span>
                </div>
                <div id="mcpToolsList"></div>
            </div>
        </div>

        <!-- TAB 4: Architecture Centrality -->
        <div id="tab-centrality" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span>FalkorDB Architecture Centrality Hubs</span>
                    <span style="font-size: 0.75rem; color: var(--text-muted);">Graph Degree & Bottleneck Analysis</span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                    Graph algorithms query FalkorDB to discover the highest-impact architectural files and automation hubs in the repository.
                </p>
                <div style="max-height: 450px; overflow-y: auto;">
                    <table class="data-table" id="centralityTable">
                        <thead>
                            <tr>
                                <th>File / Component</th>
                                <th>Type</th>
                                <th>In-Degree</th>
                                <th>Out-Degree</th>
                                <th>Dependencies</th>
                                <th>Centrality Score</th>
                            </tr>
                        </thead>
                        <tbody id="centralityBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </main>

    <!-- Slide-Out Code Drawer -->
    <div class="drawer-overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
    <div class="drawer" id="codeDrawer">
        <div class="drawer-header">
            <div>
                <span id="drawerFilePath" style="font-weight: 700; color: #38bdf8; font-size: 0.95rem;">File Preview</span>
                <div id="drawerSha" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">SHA: ...</div>
            </div>
            <button class="btn-view-code" onclick="closeDrawer()">✕ Close</button>
        </div>
        <div class="drawer-body" id="drawerBody">
            <p style="color: var(--text-muted);">Loading file contents from FalkorDB...</p>
        </div>
    </div>

    <!-- LLM Settings Modal -->
    <div class="drawer-overlay" id="modalOverlay" onclick="closeSettingsModal()"></div>
    <div class="modal" id="settingsModal">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
            <h3 style="font-size: 1.2rem; font-weight: 800;">LLM Provider Settings</h3>
            <button class="btn-view-code" onclick="closeSettingsModal()">✕</button>
        </div>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 1rem;">
            Configure Google Gemini, OpenRouter, or OpenAI credentials for live reasoning synthesis. If left empty, ImpactGraph seamlessly runs its deterministic rule engine with zero API keys required.
        </p>
        <div class="form-group">
            <label>Provider Type:</label>
            <select id="modalProvider" onchange="onProviderChange()">
                <option value="gemini" selected>Google Gemini (API Key from AI Studio)</option>
                <option value="openrouter">OpenRouter (https://openrouter.ai/api/v1)</option>
                <option value="openai">OpenAI (https://api.openai.com/v1)</option>
            </select>
        </div>
        <div class="form-group">
            <label>API Key:</label>
            <input type="text" id="modalApiKey" placeholder="AIzaSy... or sk-or-v1-... or sk-...">
        </div>
        <div class="form-group">
            <label>Model Identifier:</label>
            <input type="text" id="modalModel" placeholder="e.g. gemini-3.8-flash or nvidia/nemotron-3.5-lightning:free" value="gemini-3.8-flash">
        </div>
        <button class="btn-submit" onclick="saveLLMSettings()">Save Configuration</button>
    </div>

    <footer>
        <p><strong>ImpactGraph 2.0</strong> — Built for WeMakeDevs × FalkorDB Graph Hacks (Track: Agents That Act on Connected Data)</p>
        <p style="margin-top: 0.35rem; color: #64748b;">Powered by FalkorDB Graph Engine, Model Context Protocol (MCP), and Multi-Hop ReAct Reasoning</p>
    </footer>

    <script>
        // Tab switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');

            const currentRepo = document.getElementById('ownerInput').value + '/' + document.getElementById('repoInput').value;
            if (tabId === 'tab-mcp') loadMCPTools();
            if (tabId === 'tab-centrality') fetchCentrality(currentRepo);
            if (tabId === 'tab-blast') runBlastRadiusAnalysis();
            if (tabId === 'tab-supply') loadSupplyChainAudit();
        }

        // Graph Canvas Simulation & Zoom/Pan
        let graphNodes = [];
        let graphEdges = [];
        let traversedNodeIds = new Set();
        const canvas = document.getElementById('graphCanvas');
        const ctx = canvas.getContext('2d');
        let zoom = 1;
        let panX = 0;
        let panY = 0;
        let isDragging = false;
        let startX, startY;

        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
            drawGraph();
        }
        window.addEventListener('resize', resizeCanvas);

        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            const factor = e.deltaY < 0 ? 1.1 : 0.9;
            zoom *= factor;
            zoom = Math.max(0.4, Math.min(3, zoom));
            drawGraph();
        });

        canvas.addEventListener('mousedown', e => {
            isDragging = true;
            startX = e.clientX - panX;
            startY = e.clientY - panY;
        });
        window.addEventListener('mousemove', e => {
            if (isDragging) {
                panX = e.clientX - startX;
                panY = e.clientY - startY;
                drawGraph();
            }
        });
        window.addEventListener('mouseup', () => { isDragging = false; });

        // Node Click Handler
        canvas.addEventListener('click', e => {
            const rect = canvas.getBoundingClientRect();
            const clickX = (e.clientX - rect.left - panX) / zoom;
            const clickY = (e.clientY - rect.top - panY) / zoom;

            for (const n of graphNodes) {
                const dx = clickX - n.x;
                const dy = clickY - n.y;
                if (Math.sqrt(dx * dx + dy * dy) < 18) {
                    if (n.source) {
                        openDrawerWithContent(n.source, document.getElementById('ownerInput').value + '/' + document.getElementById('repoInput').value);
                    }
                    break;
                }
            }
        });

        async function loadSubgraph(repo) {
            try {
                const res = await fetch('/graph/subgraph?repository=' + encodeURIComponent(repo));
                if (res.ok) {
                    const data = await res.json();
                    initGraphPhysics(data.nodes || [], data.edges || []);
                }
            } catch (err) { console.error(err); }
        }

        function resetGraphPhysics() {
            panX = 0; panY = 0; zoom = 1;
            loadSubgraph(document.getElementById('ownerInput').value + '/' + document.getElementById('repoInput').value);
        }

        function initGraphPhysics(nodes, edges) {
            const width = canvas.width || 600;
            const height = canvas.height || 460;

            graphNodes = nodes.map((n, i) => {
                const angle = (i / nodes.length) * Math.PI * 2;
                const radius = Math.min(width, height) * 0.35;
                return {
                    ...n,
                    x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 60,
                    y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 60,
                };
            });
            graphEdges = edges;

            // Simple relaxation
            for (let step = 0; step < 40; step++) {
                for (let i = 0; i < graphNodes.length; i++) {
                    for (let j = i + 1; j < graphNodes.length; j++) {
                        const dx = graphNodes[j].x - graphNodes[i].x;
                        const dy = graphNodes[j].y - graphNodes[i].y;
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                        if (dist < 150) {
                            const force = (150 - dist) * 0.02;
                            graphNodes[i].x -= (dx / dist) * force;
                            graphNodes[i].y -= (dy / dist) * force;
                            graphNodes[j].x += (dx / dist) * force;
                            graphNodes[j].y += (dy / dist) * force;
                        }
                    }
                }
            }
            drawGraph();
        }

        function drawGraph() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            ctx.translate(panX, panY);
            ctx.scale(zoom, zoom);

            // Draw edges
            const nodeMap = new Map(graphNodes.map(n => [n.id, n]));
            graphEdges.forEach(e => {
                const s = nodeMap.get(e.source);
                const t = nodeMap.get(e.target);
                if (s && t) {
                    ctx.beginPath();
                    ctx.moveTo(s.x, s.y);
                    ctx.lineTo(t.x, t.y);

                    const isTraversed = (traversedNodeIds.has(s.id) || (s.source && Array.from(traversedNodeIds).some(x => x.includes(s.source)))) &&
                                        (traversedNodeIds.has(t.id) || (t.source && Array.from(traversedNodeIds).some(x => x.includes(t.source))));

                    if (isTraversed) {
                        ctx.strokeStyle = '#ef4444';
                        ctx.lineWidth = 2.8;
                    } else if (e.type === 'REFERENCES') {
                        ctx.strokeStyle = '#38bdf8';
                        ctx.lineWidth = 1.8;
                    } else if (e.type === 'USES_DEPENDENCY') {
                        ctx.strokeStyle = '#f59e0b';
                        ctx.lineWidth = 1.2;
                    } else {
                        ctx.strokeStyle = '#23304a';
                        ctx.lineWidth = 1;
                    }
                    ctx.stroke();
                }
            });

            // Draw nodes
            graphNodes.forEach(n => {
                ctx.beginPath();
                const isTraversed = traversedNodeIds.has(n.id) || (n.source && Array.from(traversedNodeIds).some(t => t.includes(n.source)));
                const radius = n.type === 'repository' ? 14 : (isTraversed ? 11 : 8);
                ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);

                if (n.type === 'repository') ctx.fillStyle = '#a855f7';
                else if (n.type === 'workflow') ctx.fillStyle = '#3b82f6';
                else if (n.group === 'dependency') ctx.fillStyle = '#f59e0b';
                else ctx.fillStyle = '#10b981';

                ctx.fill();

                if (isTraversed) {
                    ctx.strokeStyle = '#ef4444';
                    ctx.lineWidth = 3.5;
                    ctx.stroke();
                } else {
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }

                // Label
                ctx.fillStyle = '#cbd5e1';
                ctx.font = '10px JetBrains Mono';
                const label = (n.label || '').split('/').pop();
                ctx.fillText(label.slice(0, 18), n.x + 13, n.y + 3);
            });

            ctx.restore();
        }

        // Drawer
        async function openDrawerWithContent(source, repo, supportingLines = '') {
            document.getElementById('drawerOverlay').style.display = 'block';
            const drawer = document.getElementById('codeDrawer');
            drawer.classList.add('open');
            document.getElementById('drawerFilePath').textContent = source;

            const body = document.getElementById('drawerBody');
            body.innerHTML = '<p style="color:#94a3b8;">Fetching decoded source blob from FalkorDB...</p>';

            const lineSet = new Set((supportingLines || '').split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n)));

            try {
                const res = await fetch(`/api/evidence/content?repository=${encodeURIComponent(repo)}&source=${encodeURIComponent(source)}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('drawerSha').textContent = 'SHA: ' + (data.sha || 'N/A') + (data.from_cache ? ' (Cached in FalkorDB)' : ' (Live Fetch)');

                    const lines = (data.content || '').split('\\n');
                    let tableHtml = '<table class="code-table">';
                    lines.forEach((l, idx) => {
                        const lineNo = idx + 1;
                        const isHit = lineSet.has(lineNo);
                        tableHtml += `
                            <tr class="${isHit ? 'code-line-highlighted' : ''}">
                                <td class="code-line-no">${lineNo}</td>
                                <td class="code-line-text">${escapeHtml(l)}</td>
                            </tr>
                        `;
                    });
                    tableHtml += '</table>';
                    body.innerHTML = tableHtml;
                } else {
                    body.innerHTML = '<p style="color:#ef4444;">Unable to fetch file content.</p>';
                }
            } catch (err) {
                body.innerHTML = '<p style="color:#ef4444;">Error: ' + err + '</p>';
            }
        }

        function closeDrawer() {
            document.getElementById('drawerOverlay').style.display = 'none';
            document.getElementById('codeDrawer').classList.remove('open');
        }

        function escapeHtml(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        // Settings Modal
        function openSettingsModal() {
            document.getElementById('modalOverlay').style.display = 'block';
            document.getElementById('settingsModal').style.display = 'block';
        }
        function closeSettingsModal() {
            document.getElementById('modalOverlay').style.display = 'none';
            document.getElementById('settingsModal').style.display = 'none';
        }

        function onProviderChange() {
            const provider = document.getElementById('modalProvider').value;
            const modelInput = document.getElementById('modalModel');
            if (provider === 'gemini') {
                modelInput.value = 'gemini-3.8-flash';
            } else if (provider === 'openrouter') {
                modelInput.value = 'nvidia/nemotron-3.5-lightning:free';
            } else {
                modelInput.value = 'gpt-4o-mini';
            }
        }

        async function saveLLMSettings() {
            const apiKey = document.getElementById('modalApiKey').value.trim();
            const model = document.getElementById('modalModel').value.trim();
            const provider = document.getElementById('modalProvider').value;

            try {
                const res = await fetch('/api/llm/configure', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        api_key: apiKey,
                        model: model,
                        provider: provider,
                        is_openrouter: provider === 'openrouter'
                    })
                });
                if (res.ok) {
                    const data = await res.json();
                    const mName = (data.model || '').split('/').pop();
                    document.getElementById('llmIndicatorText').textContent = 'LLM: ' + mName;
                    document.getElementById('statEngine').textContent = data.provider.toUpperCase() + ' (' + mName + ')';
                    closeSettingsModal();
                    alert("LLM Provider Configured: " + data.provider + " (" + data.model + ")");
                }
            } catch (err) {
                alert("Settings failed: " + err);
            }
        }

        // Cypher Console
        // Cypher Console
        let cypherGraphNodes = [];
        let cypherGraphEdges = [];
        let cypherPanX = 0, cypherPanY = 0, cypherZoom = 1;
        let cypherIsDragging = false, cypherStartX = 0, cypherStartY = 0;

        function setCypherQuery(q) {
            document.getElementById('cypherInput').value = q;
        }

        function toggleCypherView(view) {
            const btnTable = document.getElementById('btnCypherViewTable');
            const btnGraph = document.getElementById('btnCypherViewGraph');
            const tableContainer = document.getElementById('cypherTableContainer');
            const graphContainer = document.getElementById('cypherGraphContainer');

            if (view === 'graph') {
                btnGraph.style.background = '#1e293b';
                btnGraph.style.color = '#38bdf8';
                btnTable.style.background = 'transparent';
                btnTable.style.color = '#94a3b8';
                tableContainer.style.display = 'none';
                graphContainer.style.display = 'block';
                resizeCypherCanvas();
                drawCypherGraph();
            } else {
                btnTable.style.background = '#1e293b';
                btnTable.style.color = '#38bdf8';
                btnGraph.style.background = 'transparent';
                btnGraph.style.color = '#94a3b8';
                tableContainer.style.display = 'block';
                graphContainer.style.display = 'none';
            }
        }

        function resetCypherGraphView() {
            cypherPanX = 0; cypherPanY = 0; cypherZoom = 1;
            drawCypherGraph();
        }

        function inferCypherNodeType(val) {
            const v = String(val).toLowerCase();
            if (v.includes('.yml') || v.includes('.yaml')) return 'workflow';
            if (v.includes('.py') || v.includes('.ts') || v.includes('.js') || v.includes('.toml') || v.includes('.md')) return 'evidence';
            if (v.includes('/') && !v.includes('.')) return 'repository';
            if (v.includes('@') || v.includes('action') || v.length <= 15) return 'dependency';
            return 'evidence';
        }

        function initCypherGraphPhysics(nodes, edges) {
            const cCanvas = document.getElementById('cypherCanvas');
            const width = cCanvas.width || 800;
            const height = cCanvas.height || 420;

            cypherGraphNodes = nodes.map((n, i) => {
                const angle = (i / Math.max(1, nodes.length)) * Math.PI * 2;
                const radius = Math.min(width, height) * 0.32;
                return {
                    ...n,
                    x: width / 2 + Math.cos(angle) * radius + (Math.random() - 0.5) * 40,
                    y: height / 2 + Math.sin(angle) * radius + (Math.random() - 0.5) * 40,
                };
            });
            cypherGraphEdges = edges;

            // Relaxation simulation
            for (let step = 0; step < 45; step++) {
                for (let i = 0; i < cypherGraphNodes.length; i++) {
                    for (let j = i + 1; j < cypherGraphNodes.length; j++) {
                        const dx = cypherGraphNodes[j].x - cypherGraphNodes[i].x;
                        const dy = cypherGraphNodes[j].y - cypherGraphNodes[i].y;
                        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                        if (dist < 160) {
                            const force = (160 - dist) * 0.025;
                            cypherGraphNodes[i].x -= (dx / dist) * force;
                            cypherGraphNodes[i].y -= (dy / dist) * force;
                            cypherGraphNodes[j].x += (dx / dist) * force;
                            cypherGraphNodes[j].y += (dy / dist) * force;
                        }
                    }
                }
            }
            drawCypherGraph();
        }

        function drawCypherGraph() {
            const cCanvas = document.getElementById('cypherCanvas');
            if (!cCanvas) return;
            const cCtx = cCanvas.getContext('2d');
            cCtx.clearRect(0, 0, cCanvas.width, cCanvas.height);
            cCtx.save();
            cCtx.translate(cypherPanX, cypherPanY);
            cCtx.scale(cypherZoom, cypherZoom);

            const nodeMap = new Map(cypherGraphNodes.map(n => [n.id, n]));

            // Draw edges with arrowheads
            cypherGraphEdges.forEach(e => {
                const s = nodeMap.get(e.source);
                const t = nodeMap.get(e.target);
                if (s && t) {
                    cCtx.beginPath();
                    cCtx.moveTo(s.x, s.y);
                    cCtx.lineTo(t.x, t.y);

                    if (e.type && e.type.includes('REFERENCE')) {
                        cCtx.strokeStyle = '#38bdf8';
                        cCtx.lineWidth = 1.8;
                    } else if (e.type && e.type.includes('DEPENDENCY')) {
                        cCtx.strokeStyle = '#f59e0b';
                        cCtx.lineWidth = 1.5;
                    } else {
                        cCtx.strokeStyle = '#334155';
                        cCtx.lineWidth = 1.2;
                    }
                    cCtx.stroke();

                    // Edge label if space permits
                    if (e.type && cypherGraphEdges.length < 15) {
                        const mx = (s.x + t.x) / 2;
                        const my = (s.y + t.y) / 2;
                        cCtx.fillStyle = '#64748b';
                        cCtx.font = '9px JetBrains Mono';
                        cCtx.fillText(e.type, mx - 15, my - 4);
                    }
                }
            });

            // Draw nodes
            cypherGraphNodes.forEach(n => {
                cCtx.beginPath();
                const radius = n.type === 'repository' ? 14 : 9;
                cCtx.arc(n.x, n.y, radius, 0, Math.PI * 2);

                if (n.type === 'repository') cCtx.fillStyle = '#a855f7';
                else if (n.type === 'workflow') cCtx.fillStyle = '#3b82f6';
                else if (n.type === 'dependency') cCtx.fillStyle = '#f59e0b';
                else cCtx.fillStyle = '#10b981';

                cCtx.fill();
                cCtx.strokeStyle = '#ffffff';
                cCtx.lineWidth = 1.2;
                cCtx.stroke();

                // Text label
                cCtx.fillStyle = '#e2e8f0';
                cCtx.font = '10px JetBrains Mono';
                const label = (n.label || '').split('/').pop();
                cCtx.fillText(label.slice(0, 20), n.x + 12, n.y + 4);
            });

            cCtx.restore();
        }

        function resizeCypherCanvas() {
            const cCanvas = document.getElementById('cypherCanvas');
            if (cCanvas && cCanvas.parentElement) {
                cCanvas.width = cCanvas.parentElement.clientWidth || 900;
                cCanvas.height = 420;
            }
        }

        // Setup mouse listeners for Cypher Canvas
        window.addEventListener('DOMContentLoaded', () => {
            const cCanvas = document.getElementById('cypherCanvas');
            if (!cCanvas) return;
            cCanvas.addEventListener('mousedown', e => {
                cypherIsDragging = true;
                cypherStartX = e.clientX - cypherPanX;
                cypherStartY = e.clientY - cypherPanY;
            });
            window.addEventListener('mousemove', e => {
                if (cypherIsDragging) {
                    cypherPanX = e.clientX - cypherStartX;
                    cypherPanY = e.clientY - cypherStartY;
                    drawCypherGraph();
                }
            });
            window.addEventListener('mouseup', () => { cypherIsDragging = false; });
            cCanvas.addEventListener('wheel', e => {
                e.preventDefault();
                const factor = e.deltaY < 0 ? 1.1 : 0.9;
                cypherZoom = Math.min(Math.max(0.4, cypherZoom * factor), 2.5);
                drawCypherGraph();
            });
        });

        async function runCypherQuery() {
            const cypher = document.getElementById('cypherInput').value.trim();
            if (!cypher) return;

            try {
                const res = await fetch('/api/cypher/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cypher })
                });
                const data = await res.json();
                const wrap = document.getElementById('cypherResultsWrap');
                wrap.style.display = 'block';
                document.getElementById('cypherElapsed').textContent = `${data.elapsed_ms} ms`;

                const thead = document.getElementById('cypherThead');
                const tbody = document.getElementById('cypherTbody');
                thead.innerHTML = ''; tbody.innerHTML = '';

                if (!data.success) {
                    tbody.innerHTML = `<tr><td style="color:#ef4444;" colspan="5">Error: ${data.error}</td></tr>`;
                    return;
                }

                // Headers
                const headers = (data.header || []).map(h => Array.isArray(h) ? h[1] : h);
                let headHtml = '<tr>';
                headers.forEach(h => { headHtml += `<th>${h}</th>`; });
                headHtml += '</tr>';
                thead.innerHTML = headHtml;

                // Rows
                (data.result_set || []).forEach(row => {
                    let trHtml = '<tr>';
                    row.forEach(val => {
                        trHtml += `<td style="font-family:'JetBrains Mono';">${escapeHtml(String(val))}</td>`;
                    });
                    trHtml += '</tr>';
                    tbody.innerHTML += trHtml;
                });

                if (data.result_set.length === 0) {
                    tbody.innerHTML = '<tr><td style="color:#94a3b8;" colspan="5">Query returned 0 rows.</td></tr>';
                }

                // Dynamic Visual Graph Extraction
                const nodesMap = new Map();
                const edgesList = [];
                const colCount = headers.length;

                data.result_set.forEach(row => {
                    if (colCount >= 2) {
                        const srcVal = String(row[0] || '').trim();
                        const tgtVal = colCount >= 3 ? String(row[2] || '').trim() : String(row[1] || '').trim();
                        const relType = colCount >= 3 ? String(row[1] || '').trim() : 'CONNECTED';

                        if (srcVal && tgtVal && isNaN(Number(srcVal)) && isNaN(Number(tgtVal)) && !srcVal.startsWith('[') && !tgtVal.startsWith('[')) {
                            if (!nodesMap.has(srcVal)) {
                                nodesMap.set(srcVal, { id: srcVal, label: srcVal, type: inferCypherNodeType(srcVal) });
                            }
                            if (!nodesMap.has(tgtVal)) {
                                nodesMap.set(tgtVal, { id: tgtVal, label: tgtVal, type: inferCypherNodeType(tgtVal) });
                            }
                            edgesList.push({ source: srcVal, target: tgtVal, type: relType });
                        }
                    }
                });

                const btnGraph = document.getElementById('btnCypherViewGraph');
                if (edgesList.length > 0) {
                    btnGraph.textContent = `🕸️ Visual Graph Canvas (${edgesList.length} edges)`;
                    btnGraph.style.borderColor = '#38bdf8';
                    initCypherGraphPhysics(Array.from(nodesMap.values()), edgesList);
                    document.getElementById('cypherGraphLegendText').textContent =
                        `Visualized ${nodesMap.size} nodes and ${edgesList.length} connected edges directly from your Cypher result.`;
                    // Automatically switch to graph view for relationship queries!
                    toggleCypherView('graph');
                } else {
                    btnGraph.textContent = `🕸️ Visual Graph Canvas (0 edges)`;
                    btnGraph.style.borderColor = 'var(--border)';
                    toggleCypherView('table');
                }
            } catch (err) { alert("Cypher query error: " + err); }
        }

        // MCP Tools Explorer
        async function loadMCPTools() {
            const listWrap = document.getElementById('mcpToolsList');
            listWrap.innerHTML = '<p style="color:#94a3b8;">Loading Model Context Protocol tool catalog...</p>';

            try {
                const res = await fetch('/mcp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'tools/list' })
                });
                const data = await res.json();
                const tools = data.result.tools || [];
                listWrap.innerHTML = '';

                tools.forEach(t => {
                    const div = document.createElement('div');
                    div.className = 'evidence-card';
                    div.innerHTML = `
                        <div class="evidence-header">
                            <span style="color:#38bdf8; font-weight:700;">tool: ${t.name}</span>
                            <span style="font-size:0.75rem; color:#94a3b8;">MCP JSON-RPC 2.0</span>
                        </div>
                        <div class="evidence-body">
                            <p style="color:#cbd5e1; margin-bottom:0.4rem;">${t.description}</p>
                            <pre style="color:#64748b; font-size:0.75rem;">${JSON.stringify(t.inputSchema, null, 2)}</pre>
                        </div>
                    `;
                    listWrap.appendChild(div);
                });
            } catch (err) {
                listWrap.innerHTML = '<p style="color:#ef4444;">Failed to load MCP tools: ' + err + '</p>';
            }
        }

        // Investigation Form Submission
        document.getElementById('investigateForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const owner = document.getElementById('ownerInput').value.trim();
            const repo = document.getElementById('repoInput').value.trim();
            const claim = document.getElementById('claimInput').value.trim();

            const submitBtn = document.getElementById('submitBtn');
            const btnText = document.getElementById('btnText');
            submitBtn.disabled = true;
            btnText.textContent = "Agent Investigating...";

            document.getElementById('resultsSection').style.display = 'none';
            const traceBox = document.getElementById('traceContainer');
            traceBox.innerHTML = '';

            const livePill = document.getElementById('liveStatusPill');
            livePill.textContent = "Autonomous Loop Active";
            livePill.style.background = 'rgba(59, 130, 246, 0.2)';
            livePill.style.color = '#60a5fa';

            try {
                const res = await fetch('/agent/investigate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ owner, repo, claim })
                });

                if (!res.ok) {
                    const err = await res.json();
                    alert("Investigation Error: " + (err.detail || "Request failed"));
                    return;
                }

                const data = await res.json();

                // Animate ReAct Trace
                const trace = data.agent_trace || [];
                for (let i = 0; i < trace.length; i++) {
                    const step = trace[i];
                    const div = document.createElement('div');
                    div.className = 'trace-step';
                    div.innerHTML = `
                        <div class="trace-header">
                            <span class="trace-pill" style="background:#172136; color:#38bdf8;">Step ${step.step}: ${step.phase}</span>
                            <span style="font-size:0.75rem; color:#64748b; font-family:'JetBrains Mono';">${step.action}</span>
                        </div>
                        <div class="trace-thought">💭 Thought: ${step.thought}</div>
                        <div class="trace-obs">👁️ Observation: ${step.observation}</div>
                    `;
                    traceBox.appendChild(div);
                    traceBox.scrollTop = traceBox.scrollHeight;
                    await new Promise(r => setTimeout(r, 200));
                }

                // Highlight traversed nodes
                traversedNodeIds.clear();
                (data.evidence || []).forEach(ev => traversedNodeIds.add(ev.source));
                (data.traversal_chains || []).forEach(ch => {
                    ch.split(' -[:').forEach(part => traversedNodeIds.add(part.replace(/REFERENCES|USES_DEPENDENCY|]->/g, '').trim()));
                });
                drawGraph();

                renderReport(data);
                fetchStats();
                fetchCentrality(`${owner}/${repo}`);

                livePill.textContent = "Completed";
                livePill.style.background = 'rgba(16, 185, 129, 0.2)';
                livePill.style.color = '#34d399';

            } catch (err) {
                alert("Agent loop error: " + err);
            } finally {
                submitBtn.disabled = false;
                btnText.textContent = "Launch Autonomous Agent";
            }
        });

        function renderReport(data) {
            const section = document.getElementById('resultsSection');
            section.style.display = 'block';
            section.scrollIntoView({ behavior: 'smooth' });

            const banner = document.getElementById('verdictBanner');
            const vText = document.getElementById('verdictText');
            const vPill = document.getElementById('verdictPill');
            const vIcon = document.getElementById('verdictIcon');

            const verdict = data.verdict || "needs_review";
            vText.textContent = verdict.replace(/_/g, ' ').toUpperCase();
            vPill.textContent = verdict.toUpperCase();
            vPill.className = "verdict-pill pill-" + verdict;
            banner.className = "verdict-banner verdict-" + verdict;

            if (verdict === 'supported') vIcon.textContent = "✅";
            else if (verdict === 'partially_supported') vIcon.textContent = "⚠️";
            else if (verdict === 'contradicted') vIcon.textContent = "❌";
            else vIcon.textContent = "🔍";

            document.getElementById('resInvestigationId').textContent = data.investigation_id;
            document.getElementById('resMode').textContent = data.evaluation_mode || "deterministic_rule_engine";

            // Runtime verification badge
            const rBadge = document.getElementById('runtimeVerifiedBadge');
            if (data.runtime_execution_verified) {
                rBadge.style.display = 'inline-flex';
                rBadge.style.background = 'rgba(16, 185, 129, 0.2)';
                rBadge.style.border = '1px solid var(--success)';
                rBadge.style.color = '#34d399';
                rBadge.textContent = "⚡ Runtime Execution Verified (GitHub Actions)";
            } else {
                rBadge.style.display = 'inline-flex';
                rBadge.style.background = 'rgba(245, 158, 11, 0.15)';
                rBadge.style.border = '1px solid var(--warning)';
                rBadge.style.color = '#fbbf24';
                rBadge.textContent = "ℹ️ Configuration Level (Live Run Unverified)";
            }

            document.getElementById('rationaleText').textContent = data.rationale || "No rationale recorded.";

            // Subclaims
            const subList = document.getElementById('subclaimsList');
            subList.innerHTML = "";
            (data.subclaims_verified || []).forEach(sc => {
                const li = document.createElement('li');
                li.textContent = sc;
                subList.appendChild(li);
            });
            if (!data.subclaims_verified || data.subclaims_verified.length === 0) {
                subList.innerHTML = "<li>No subclaims isolated.</li>";
            }

            // Multi-Hop Traversal Chains
            const gpList = document.getElementById('graphPathsList');
            gpList.innerHTML = "";
            const chains = data.traversal_chains || data.traversed_paths || [];
            if (chains.length > 0) {
                chains.slice(0, 8).forEach(p => {
                    const tag = document.createElement('span');
                    tag.className = 'graph-path-tag';
                    tag.textContent = p;
                    gpList.appendChild(tag);
                });
            } else {
                gpList.innerHTML = "<span style='font-size:0.8rem; color:var(--text-muted);'>Direct repository file match.</span>";
            }

            // Evidence Cards with View Code button
            const evList = document.getElementById('evidenceList');
            evList.innerHTML = "";
            (data.evidence || []).forEach(ev => {
                const card = document.createElement('div');
                card.className = "evidence-card";
                card.innerHTML = `
                    <div class="evidence-header">
                        <span>📄 ${ev.source}</span>
                        <div>
                            <span style="color: #60a5fa; margin-right: 0.75rem;">Lines: ${ev.supporting_lines || "Config"}</span>
                            <button class="btn-view-code" onclick="openDrawerWithContent('${ev.source}', '${data.repository}', '${ev.supporting_lines || ''}')">View Source</button>
                        </div>
                    </div>
                    <div class="evidence-body">
                        <div style="color: #64748b; margin-bottom: 0.5rem;">Git Blob SHA: ${ev.blob_sha}</div>
                        <div class="code-line highlight">Verified lines cited: ${ev.supporting_lines || "File configuration matches claim"}</div>
                    </div>
                `;
                evList.appendChild(card);
            });

            // Limitations
            const limList = document.getElementById('limitationsList');
            limList.innerHTML = "";
            (data.limitations || []).forEach(lim => {
                const li = document.createElement('li');
                li.textContent = lim;
                limList.appendChild(li);
            });
        }

        // Stats & Centrality
        async function fetchStats() {
            try {
                const res = await fetch('/graph/stats');
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('statNodes').textContent = data.node_count || '0';
                    document.getElementById('statEdges').textContent = data.relationship_count || '0';
                }
                const llmRes = await fetch('/api/llm/status');
                if (llmRes.ok) {
                    const ldata = await llmRes.json();
                    if (ldata.active) {
                        const mName = (ldata.model || '').split('/').pop();
                        document.getElementById('llmIndicatorText').textContent = 'LLM: ' + mName;
                        document.getElementById('statEngine').textContent = (ldata.provider || 'LLM').toUpperCase() + ' (' + mName + ')';
                    } else {
                        document.getElementById('statEngine').textContent = 'Deterministic Rule Engine (Zero Keys)';
                    }
                }
            } catch (err) { console.error(err); }
        }

        async function fetchCentrality(repo) {
            try {
                const res = await fetch('/graph/centrality?repository=' + encodeURIComponent(repo));
                if (res.ok) {
                    const data = await res.json();
                    const tbody = document.getElementById('centralityBody');
                    tbody.innerHTML = '';
                    (data.central_components || []).forEach(c => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="font-family:'JetBrains Mono'; color:#38bdf8;">${c.source}</td>
                            <td><span style="color:#94a3b8;">${c.type}</span></td>
                            <td>${c.in_degree}</td>
                            <td>${c.out_degree}</td>
                            <td>${c.dependency_count}</td>
                            <td><strong>${c.centrality_score}</strong></td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (err) { console.error(err); }
        }

        function setPreset(owner, repo, claim) {
            document.getElementById('ownerInput').value = owner;
            document.getElementById('repoInput').value = repo;
            document.getElementById('claimInput').value = claim;
        }

        // Conversational Drill-Down
        function setDrillDownQuestion(q) {
            document.getElementById('drillDownQuery').value = q;
        }

        async function submitDrillDown() {
            const query = document.getElementById('drillDownQuery').value.trim();
            if (!query) return;

            const owner = document.getElementById('ownerInput').value.trim();
            const repo = document.getElementById('repoInput').value.trim();
            const repository = `${owner}/${repo}`;

            const box = document.getElementById('drillDownAnswerBox');
            const txt = document.getElementById('drillDownAnswerText');
            const src = document.getElementById('drillDownSource');
            box.style.display = 'block';
            txt.textContent = 'Agent traversing FalkorDB graph context and querying reasoning model...';

            try {
                const res = await fetch('/api/chat/drill-down', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repository, query })
                });
                if (res.ok) {
                    const data = await res.json();
                    src.textContent = `Agent Response (Grounding: ${data.source}):`;
                    txt.textContent = data.answer || 'No answer generated.';
                } else {
                    txt.textContent = 'Failed to get answer from agent.';
                }
            } catch (err) {
                txt.textContent = 'Error: ' + err;
            }
        }

        // Blast Radius & Cascading Impact
        function setBlastTarget(target) {
            document.getElementById('blastTargetInput').value = target;
            runBlastRadiusAnalysis();
        }

        async function runBlastRadiusAnalysis() {
            const owner = document.getElementById('ownerInput').value.trim();
            const repo = document.getElementById('repoInput').value.trim();
            const repository = `${owner}/${repo}`;
            const source = document.getElementById('blastTargetInput').value.trim();
            if (!source) return;

            const resDiv = document.getElementById('blastResults');
            resDiv.style.display = 'block';

            try {
                const res = await fetch(`/api/graph/blast-radius?repository=${encodeURIComponent(repository)}&source=${encodeURIComponent(source)}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('blastScore').textContent = data.severity_score;
                    document.getElementById('blastWfCount').textContent = data.affected_workflows.length;
                    document.getElementById('blastTestCount').textContent = data.affected_tests.length;
                    document.getElementById('blastFilesCount').textContent = data.affected_files.length;
                    document.getElementById('blastDepsCount').textContent = data.external_dependencies.length;

                    const title = document.getElementById('blastSeverityTitle');
                    const desc = document.getElementById('blastSeverityDesc');
                    const banner = document.getElementById('blastSeverityBanner');

                    title.textContent = data.severity_level + ' BLAST RADIUS';
                    if (data.severity_level === 'CRITICAL') {
                        banner.style.background = '#450a0a';
                        banner.style.borderColor = '#ef4444';
                        desc.textContent = `Directly breaks ${data.affected_workflows.length} core CI/CD workflows and automated test suites.`;
                    } else if (data.severity_level === 'HIGH') {
                        banner.style.background = '#422006';
                        banner.style.borderColor = '#f59e0b';
                        desc.textContent = `Impacts multiple dependent source modules and tests.`;
                    } else {
                        banner.style.background = '#064e3b';
                        banner.style.borderColor = '#10b981';
                        desc.textContent = `Isolated file with minimal cascading risk across the repository.`;
                    }

                    const chainsList = document.getElementById('blastChainsList');
                    chainsList.innerHTML = '';
                    if (data.propagation_chains && data.propagation_chains.length > 0) {
                        data.propagation_chains.forEach(ch => {
                            const d = document.createElement('div');
                            d.style.fontFamily = "'JetBrains Mono', monospace";
                            d.style.fontSize = "0.82rem";
                            d.style.padding = "0.5rem 0.75rem";
                            d.style.background = "#090e1a";
                            d.style.border = "1px solid var(--border)";
                            d.style.borderRadius = "6px";
                            d.style.color = "#38bdf8";
                            d.textContent = ch;
                            chainsList.appendChild(d);
                        });
                    } else {
                        chainsList.innerHTML = '<span style="color:#94a3b8; font-size:0.85rem;">No cascading dependent chains found in FalkorDB for this file.</span>';
                    }
                }
            } catch (err) {
                console.error(err);
            }
        }

        // Supply Chain Security Audit
        async function loadSupplyChainAudit() {
            const owner = document.getElementById('ownerInput').value.trim();
            const repo = document.getElementById('repoInput').value.trim();
            const repository = `${owner}/${repo}`;

            try {
                const res = await fetch(`/api/graph/supply-chain?repository=${encodeURIComponent(repository)}`);
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('supplyTotalCount').textContent = data.total_dependencies;
                    document.getElementById('supplyPinnedCount').textContent = data.pinned_sha_count;
                    document.getElementById('supplyUnpinnedCount').textContent = data.unpinned_count;

                    const badge = document.getElementById('supplyPostureBadge');
                    badge.textContent = data.security_posture;
                    if (data.security_posture === 'STRONG') {
                        badge.style.background = 'rgba(16, 185, 129, 0.2)';
                        badge.style.color = '#34d399';
                        badge.style.border = '1px solid #10b981';
                    } else {
                        badge.style.background = 'rgba(245, 158, 11, 0.2)';
                        badge.style.color = '#fbbf24';
                        badge.style.border = '1px solid #f59e0b';
                    }

                    const tbody = document.getElementById('supplyBody');
                    tbody.innerHTML = '';
                    (data.dependencies || []).forEach(dep => {
                        const tr = document.createElement('tr');
                        const riskColor = dep.risk_level.includes('CRITICAL') ? '#ef4444' : (dep.risk_level.includes('MEDIUM') ? '#f59e0b' : '#10b981');
                        tr.innerHTML = `
                            <td style="font-family:'JetBrains Mono'; color:#38bdf8; font-weight:600;">${escapeHtml(dep.name)}</td>
                            <td><span style="color:${riskColor}; font-weight:600; font-size:0.8rem;">${escapeHtml(dep.risk_level)}</span></td>
                            <td><span style="font-weight:700;">${dep.used_in.length}</span> workflow(s)</td>
                            <td style="font-size:0.75rem; color:#94a3b8; font-family:'JetBrains Mono';">${escapeHtml(dep.used_in.slice(0, 3).join(', '))}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            } catch (err) {
                console.error(err);
            }
        }

        // MCP Playground
        const MCP_TOOL_DEFAULTS = {
            "graph_blast_radius": { "repository": "fastapi/fastapi", "target_source": "scripts/docs.py" },
            "graph_supply_chain_audit": { "repository": "pallets/flask" },
            "agent_drill_down_chat": { "repository": "fastapi/fastapi", "query": "Why does build-docs.yml reference scripts/docs.py?" },
            "graph_centrality": { "repository": "fastapi/fastapi" },
            "graph_traverse_neighborhood": { "start_source": ".github/workflows/build-docs.yml", "max_hops": 2 },
            "graph_shortest_path": { "source_path": ".github/workflows/build-docs.yml", "target_path": "tests/test_local_docs.py" },
            "graph_memory_recall": { "repository": "fastapi/fastapi", "query": "documentation build" },
            "graph_query": { "cypher": "MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence) RETURN r.id, count(e) LIMIT 5", "params": {} },
            "graph_get_subgraph": { "repository": "fastapi/fastapi", "max_nodes": 30 },
            "agent_investigate_claim": { "owner": "fastapi", "repo": "fastapi", "claim": "This project uses GitHub Actions to automate its documentation build." }
        };

        function onMCPToolSelectChange() {
            const sel = document.getElementById('mcpToolSelect').value;
            const defArgs = MCP_TOOL_DEFAULTS[sel] || {};
            document.getElementById('mcpToolArgs').value = JSON.stringify(defArgs, null, 2);
        }

        async function runMCPPlayground() {
            const toolName = document.getElementById('mcpToolSelect').value;
            let args = {};
            try {
                args = JSON.parse(document.getElementById('mcpToolArgs').value);
            } catch (err) {
                alert("Invalid JSON in arguments: " + err);
                return;
            }

            const t0 = performance.now();
            const resBox = document.getElementById('mcpPlaygroundResponse');
            resBox.textContent = "Executing tool via MCP JSON-RPC 2.0 protocol...";

            try {
                const res = await fetch('/mcp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        id: Date.now(),
                        method: "tools/call",
                        params: {
                            name: toolName,
                            arguments: args
                        }
                    })
                });
                const elapsed = (performance.now() - t0).toFixed(1);
                document.getElementById('mcpPlaygroundElapsed').textContent = `${elapsed} ms`;
                const data = await res.json();
                resBox.textContent = JSON.stringify(data, null, 2);
            } catch (err) {
                resBox.textContent = "Error executing MCP tool: " + err;
            }
        }


        fetchStats();
        resizeCanvas();
        loadSubgraph('fastapi/fastapi');
        fetchCentrality('fastapi/fastapi');
    </script>
</body>
</html>
"""
