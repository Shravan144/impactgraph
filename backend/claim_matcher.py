
import re
from pathlib import PurePosixPath

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
    """Rank candidate evidence by simple path-based signals."""

    keywords = extract_keywords(claim)
    path = source.lower()
    filename = PurePosixPath(path).name.lower()

    score = 0

    for keyword in keywords:
        if keyword in path:
            score += 3

    if "workflow" in keywords and ".github/workflows/" in path:
        score += 5

    if "test" in keywords and (
        "test" in filename or "/tests/" in path
    ):
        score += 3

    if "documentation" in keywords or "docs" in keywords:
        if "docs" in path or "readme" in filename:
            score += 3

    return score


def find_candidate_evidence(claim: str, limit: int = 10) -> list[dict]:
    """Find and rank stored evidence files for a claim."""

    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    query = """
    MATCH (r:Repository)-[:HAS_EVIDENCE]->(e:Evidence)
    RETURN r.name AS repository,
           e.source AS source,
           e.blob_sha AS blob_sha,
           e.size AS size
    """

    result = graph.query(query)

    candidates = []

    for row in result.result_set:
        repository, source, blob_sha, size = row

        score = score_evidence(claim, source or "")

        if score > 0:
            candidates.append({
                "repository": repository,
                "source": source,
                "blob_sha": blob_sha,
                "size": size,
                "score": score,
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
        print(f"\nScore: {item['score']}")
        print(f"Repository: {item['repository']}")
        print(f"File: {item['source']}")
        print(f"Blob SHA: {item['blob_sha']}")
