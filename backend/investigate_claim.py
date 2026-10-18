from claim_matcher import find_candidate_evidence, extract_keywords
from fetch_evidence import fetch_file_content


CLAIM = (
    "This project uses GitHub Actions "
    "to automate its documentation build."
)

MAX_CANDIDATES = 3

SIGNAL_TERMS = (
    "name:",
    "on:",
    "push:",
    "pull_request:",
    "workflow_run:",
    "steps:",
    "run:",
    "build",
    "docs",
    "documentation",
    "mkdocs",
    "sphinx",
)


def inspect_candidate(candidate: dict, claim: str | None = None) -> dict | None:
    """Fetch a candidate and extract relevant lines with claim-guided precision."""

    repository = candidate.get("repository", "")
    content = candidate.get("content")

    if not content:
        if "/" not in repository:
            return None
        owner, repo = repository.split("/", 1)
        file = {
            "type": "blob",
            "path": candidate["source"],
            "sha": candidate.get("blob_sha") or candidate.get("sha"),
            "size": candidate.get("size", 1000),
        }
        evidence = fetch_file_content(owner, repo, file)
        if evidence is None:
            return None
        content = evidence["content"]
        sha = evidence["sha"]
        size = evidence["size"]
    else:
        sha = candidate.get("blob_sha") or candidate.get("sha")
        size = candidate.get("size", len(content))

    relevant_lines = []
    content_lines = content.splitlines()

    # If a claim is provided, prioritize lines matching claim-specific keywords
    claim_keywords = extract_keywords(claim) if claim else set()
    specific_keywords = claim_keywords - {"actions", "github", "project", "workflow"}

    for line_number, line in enumerate(content_lines, start=1):
        line_lower = line.lower()
        # High-priority: matches specific claim concepts
        if specific_keywords and any(kw in line_lower for kw in specific_keywords):
            relevant_lines.append({
                "line": line_number,
                "text": line.strip()[:240],
                "priority": "high",
            })
        elif any(term in line_lower for term in SIGNAL_TERMS):
            relevant_lines.append({
                "line": line_number,
                "text": line.strip()[:240],
                "priority": "standard",
            })

    # Sort high priority first, but preserve chronological line order
    sorted_lines = sorted(relevant_lines, key=lambda l: (0 if l["priority"] == "high" else 1, l["line"]))
    final_lines = sorted_lines[:15]
    final_lines.sort(key=lambda l: l["line"])

    return {
        "path": candidate["source"],
        "sha": sha,
        "size": size,
        "relevant_lines": [{"line": l["line"], "text": l["text"]} for l in final_lines],
        "content": content,
    }


if __name__ == "__main__":
    candidates = find_candidate_evidence(
        CLAIM,
        limit=MAX_CANDIDATES,
        repository_filter="fastapi/fastapi",
    )

    print(f"Claim: {CLAIM}")
    print(f"Candidates to inspect: {len(candidates)}")

    for candidate in candidates:
        print(f"\n{'=' * 60}")
        print(f"Candidate: {candidate['source']}")
        print(f"Ranking score: {candidate['score']}")

        try:
            evidence = inspect_candidate(candidate, claim=CLAIM)

            if evidence is None:
                print("No readable text was returned.")
                continue

            print(f"Blob SHA: {evidence['sha']}")
            print(f"Relevant extracted lines: {len(evidence['relevant_lines'])}")
            for l in evidence["relevant_lines"]:
                print(f"  L{l['line']}: {l['text']}")

        except Exception as exc:
            print(f"Inspection failed: {exc}")
