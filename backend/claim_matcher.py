import re
from pathlib import PurePosixPath
from fetch_evidence import fetch_file_content
from graph_db import execute_query


def extract_keywords(text: str) -> set[str]:
    """Extract simple, meaningful keywords from a claim."""
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were",
        "this", "that", "it", "and", "or", "to", "of",
        "in", "for", "with", "uses", "use", "using",
        "project", "implements", "implemented", "automate",
        "automates", "automated",
    }

    words = re.findall(r"[a-zA-Z0-9_+-]+", text.lower())

    return {
        word for word in words
        if len(word) > 2 and word not in stop_words
    }


def score_evidence(claim: str, source: str) -> int:
    """Rank candidate evidence using claim and path signals."""
    keywords = extract_keywords(claim)
    path = source.lower()
    filename = PurePosixPath(path).name.lower()

    score = 0

    # Direct keyword matches in the path
    for keyword in keywords:
        if keyword in path:
            score += 2

    # Documentation build workflows
    if "documentation" in keywords or "docs" in keywords:
        if "build-docs" in filename or "build_docs" in filename:
            score += 10
        elif "docs" in filename or "documentation" in filename:
            score += 5
        elif ".github/workflows/" in path:
            score += 1

    # Workflow configuration is relevant when automation or CI/CD is claimed
    if "github" in keywords or "actions" in keywords or "ci" in keywords or "workflow" in keywords:
        if ".github/workflows/" in path:
            score += 3

    # Test-related claims get a preference for test files
    if "test" in keywords or "tests" in keywords:
        if "test" in filename or "/tests/" in path or "/test/" in path:
            score += 6

    # Docker / container claims
    if "docker" in keywords or "container" in keywords:
        if "dockerfile" in filename or "docker-compose" in filename:
            score += 8

    # Packaging / dependency claims
    if "package" in keywords or "dependencies" in keywords or "install" in keywords:
        if filename in ["pyproject.toml", "requirements.txt", "package.json", "setup.py"]:
            score += 6

    # Auth / security claims
    if "auth" in keywords or "jwt" in keywords or "security" in keywords:
        if "auth" in filename or "security" in filename or "token" in filename:
            score += 6

    return score


def score_evidence_content(claim: str, content: str) -> int:
    """Score content using claim-specific evidence signals."""
    keywords = extract_keywords(claim)
    text = content.lower()
    score = 0

    # General claim keywords provide weak relevance signals
    for keyword in keywords:
        if keyword in text:
            score += 1

    # Documentation-build signals
    if "documentation" in keywords or "docs" in keywords:
        if "build docs" in text or "build-docs" in text:
            score += 5
        if "docs.py" in text:
            score += 6
        if "mkdocs" in text or "sphinx" in text:
            score += 5
        if "upload-artifact" in text and ("docs" in text or "documentation" in text):
            score += 3

    # GitHub Actions signals
    if "actions" in keywords or "github" in keywords:
        if "actions/checkout" in text:
            score += 1
        if "runs-on:" in text or "steps:" in text:
            score += 1

    # Test signals
    if "test" in keywords or "tests" in keywords:
        if "pytest" in text or "unittest" in text or "def test_" in text:
            score += 5

    return score


def find_candidate_evidence(
    claim: str,
    limit: int = 10,
    repository_filter: str | None = None,
) -> list[dict]:
    """
    Find and rank evidence using FalkorDB, combining path score,
    in-graph content signals, and FalkorDB graph traversals (referenced scripts & dependencies).
    """
    if repository_filter:
        query = """
        MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence)
        WHERE r.id = $repository
        RETURN r.id AS repository,
               e.source AS source,
               e.blob_sha AS blob_sha,
               e.size AS size,
               e.content AS content
        """
        params = {"repository": repository_filter.lower()}
    else:
        query = """
        MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence)
        RETURN r.id AS repository,
               e.source AS source,
               e.blob_sha AS blob_sha,
               e.size AS size,
               e.content AS content
        """
        params = {}

    result = execute_query(query, params)

    # Phase 1: Fast in-memory path scoring filter
    ranked_by_path = []
    for row in result.result_set:
        repository = row[0]
        source = row[1]
        blob_sha = row[2]
        size = row[3]
        cached_content = row[4] if len(row) > 4 else None

        if not repository or not source or not blob_sha:
            continue

        path_score = score_evidence(claim, source)
        if path_score <= 0:
            continue

        ranked_by_path.append({
            "repository": repository,
            "source": source,
            "blob_sha": blob_sha,
            "size": size,
            "cached_content": cached_content,
            "path_score": path_score,
        })

    # Sort by path score to evaluate the most relevant files first
    ranked_by_path.sort(key=lambda x: -x["path_score"])
    top_entries = ranked_by_path[:max(limit * 2, 6)]

    # Phase 2: Deep evaluation (content analysis + graph traversal)
    candidates = []
    for entry in top_entries:
        repository = entry["repository"]
        source = entry["source"]
        blob_sha = entry["blob_sha"]
        size = entry["size"]
        path_score = entry["path_score"]
        content = entry["cached_content"]

        if not content:
            try:
                owner, repo = repository.split("/", 1)
                file = {
                    "type": "blob",
                    "path": source,
                    "sha": blob_sha,
                    "size": size,
                }
                fetched = fetch_file_content(owner, repo, file)
                if fetched:
                    content = fetched["content"]
            except Exception:
                pass

        content = content or ""
        content_score = score_evidence_content(claim, content) if content else 0

        # Phase 3: FalkorDB Graph Traversal
        graph_bonus = 0
        connected_paths = []
        try:
            conn_query = """
            MATCH (e:Evidence {source: $source})
            OPTIONAL MATCH (e)-[r:REFERENCES]->(ref:Evidence)
            OPTIONAL MATCH (e)-[:USES_DEPENDENCY]->(dep:Dependency)
            RETURN ref.source, dep.name
            """
            conn_res = execute_query(conn_query, {"source": source})
            for c_row in conn_res.result_set:
                ref_src, dep_name = c_row
                if ref_src:
                    connected_paths.append(f"{source} -[:REFERENCES]-> {ref_src}")
                    ref_score = score_evidence(claim, ref_src)
                    if ref_score > 0:
                        graph_bonus += 4
                if dep_name:
                    connected_paths.append(f"{source} -[:USES_DEPENDENCY]-> {dep_name}")
                    if any(kw in dep_name.lower() for kw in extract_keywords(claim)):
                        graph_bonus += 3
        except Exception:
            pass

        total_score = path_score + content_score + graph_bonus

        candidates.append({
            "repository": repository,
            "source": source,
            "blob_sha": blob_sha,
            "size": size,
            "path_score": path_score,
            "content_score": content_score,
            "graph_bonus": graph_bonus,
            "score": total_score,
            "connected_paths": list(set(connected_paths))[:5],
            "content": content,
        })

    candidates.sort(
        key=lambda item: (-item["score"], item["source"])
    )

    return candidates[:limit]


if __name__ == "__main__":
    claim = "This project uses GitHub Actions to automate its documentation build."
    results = find_candidate_evidence(claim, limit=5, repository_filter="fastapi/fastapi")
    print(f"Candidates found: {len(results)}")
    for c in results:
        print(f"File: {c['source']} | Score: {c['score']} (path: {c['path_score']}, content: {c['content_score']}, graph: {c['graph_bonus']})")
        if c.get("connected_paths"):
            print(f"  Connected graph paths: {c['connected_paths']}")
