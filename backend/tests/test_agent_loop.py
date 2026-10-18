from agent_loop import run_autonomous_investigation_loop


def test_autonomous_investigation_loop_produces_explainable_trace():
    claim = "This project uses GitHub Actions to automate its documentation build."
    result = run_autonomous_investigation_loop("fastapi", "fastapi", claim)

    assert result["verdict"] in ["supported", "partially_supported"]
    assert result["repository"] == "fastapi/fastapi"
    assert result["evidence_count"] > 0

    trace = result["agent_trace"]
    assert len(trace) >= 6

    # Verify key ReAct phases are present in order
    phases = [s["phase"] for s in trace]
    assert "Memory Recall" in phases
    assert "Candidate Discovery" in phases
    assert "Multi-Hop Traversal" in phases
    assert "Evidence Inspection" in phases
    assert "Verdict Synthesis & Storage" in phases

    for step in trace:
        assert "thought" in step and len(step["thought"]) > 5
        assert "action" in step and len(step["action"]) > 3
        assert "observation" in step and len(step["observation"]) > 5
