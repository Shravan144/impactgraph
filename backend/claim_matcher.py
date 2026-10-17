
import re
from pathlib import PurePosixPath
from fetch_evidence import fetch_file_content
from falkordb import FalkorDB


def extract_keywords(text: str) -> set[str]:
    """Extract simple, meaningful keywords from a claim."""

    stop_words = {
        "the", "a", "an", "is", "are", "was", "were",
        "this", "that", "it", "and", "or", "to", "of",
        "in", "for", "with", "uses", "use", "using",
        "project", "implements", "implemented",
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

    # Direct keyword matches in the path.
    for keyword in keywords:
        if keyword in path:
            score += 2

    # Stronger signals for documentation build workflows.
    if "documentation" in keywords or "docs" in keywords:
        if "build-docs" in filename or "build_docs" in filename:
            score += 10
        elif "docs" in filename or "documentation" in filename:
            score += 5
        elif ".github/workflows/" in path:
            score += 1

    # Workflow configuration is relevant when automation is claimed.
    if "github" in keywords or "actions" in keywords:
        if ".github/workflows/" in path:
            score += 3

    # Test-related claims get a preference for test files.
    if "test" in keywords:
        if "test" in filename or "/tests/" in path:
            score += 3

    return score



def score_evidence_content(claim: str, content: str) -> int:
    """Score content using claim-specific evidence signals."""

    keywords = extract_keywords(claim)
    text = content.lower()
    score = 0

    # General claim keywords provide weak relevance signals.
    for keyword in keywords:
        if keyword in text:
            score += 1

    # Specific documentation-build signals carry more weight.
    if "documentation" in keywords or "docs" in keywords:
        if "build docs" in text or "build-docs" in text:
            score += 5

        if "docs.py" in text:
            score += 6

        if "mkdocs" in text or "sphinx" in text:
            score += 5

        if "upload-artifact" in text and (
            "docs" in text or "documentation" in text
        ):
            score += 3

    # GitHub Actions signals are useful, but generic syntax
    # alone should not make a file strongly relevant.
    if "actions" in keywords or "github" in keywords:
        if "actions/checkout" in text:
            score += 1

    return score





def find_candidate_evidence(
    claim: str,
    limit: int = 10,
) -> list[dict]:
    """Find and rank stored evidence using paths and file contents."""

    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    query = """
    MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence)
    RETURN r.id AS repository,
           e.source AS source,
           e.blob_sha AS blob_sha,
           e.size AS size
    """

    result = graph.query(query)
    candidates = []

    for row in result.result_set:
        repository, source, blob_sha, size = row

        if not repository or not source or not blob_sha:
            continue

        path_score = score_evidence(claim, source)

        # Skip files with no initial path relevance.
        if path_score <= 0:
            continue

        try:
            owner, repo = repository.split("/", 1)

            file = {
                "type": "blob",
                "path": source,
                "sha": blob_sha,
                "size": size,
            }

            fetched = fetch_file_content(owner, repo, file)

            if fetched is None:
                continue

            content_score = score_evidence_content(
                claim,
                fetched["content"],
            )

        except (ValueError, OSError):
            continue

        candidates.append({
            "repository": repository,
            "source": source,
            "blob_sha": blob_sha,
            "size": size,
            "path_score": path_score,
            "content_score": content_score,
            "score": path_score + content_score,
        })

    candidates.sort(
        key=lambda item: (-item["score"], item["source"])
    )

    return candidates[:limit]



if __name__ == "__main__":
    claim = (
        "This project uses GitHub Actions "
        "to automate its documentation build."
    )

    results = find_candidate_evidence(claim)

    print(f"Claim: {claim}")
    print(f"Candidates found: {len(results)}")

    
    for item in results:
        print(f"\nFile: {item['source']}")
        print(f"  Path score:    {item['path_score']}")
        print(f"  Content score: {item['content_score']}")
        print(f"  Total score:   {item['score']}")
        print(f"  Blob SHA:      {item['blob_sha']}")

