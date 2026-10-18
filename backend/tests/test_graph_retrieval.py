from graph_db import get_graph_stats, check_db_health, execute_query
from evidence_parser import extract_references_and_deps


def test_falkordb_connectivity_and_stats():
    assert check_db_health() is True
    stats = get_graph_stats()
    assert stats["status"] == "connected"
    assert stats["node_count"] > 0
    assert "Repository" in stats["labels"]
    assert "Evidence" in stats["labels"]
    assert "REFERENCES" in stats["relationship_types"] or "HAS_EVIDENCE" in stats["relationship_types"]


def test_evidence_parser_extracts_workflow_script_reference():
    content = """
    name: Build Docs
    on: [push]
    jobs:
      docs:
        steps:
          - uses: actions/checkout@v4
          - uses: actions/upload-artifact@v4
          - run: uv run ./scripts/docs.py build-lang
    """
    known_paths = {"scripts/docs.py", "README.md", "pyproject.toml"}
    parsed = extract_references_and_deps(".github/workflows/build-docs.yml", content, known_paths)

    # Check referenced script
    refs = [r["target_path"] for r in parsed["references"]]
    assert "scripts/docs.py" in refs

    # Check dependencies
    dep_names = [d["name"] for d in parsed["dependencies"]]
    assert "actions/checkout@v4" in dep_names
    assert "actions/upload-artifact@v4" in dep_names
    assert "uv" in dep_names


def test_parameterized_graph_query_execution():
    res = execute_query("RETURN $test_val AS val", {"test_val": 42})
    assert res.result_set[0][0] == 42
