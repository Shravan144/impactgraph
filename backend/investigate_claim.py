
from claim_matcher import find_candidate_evidence
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


def inspect_candidate(candidate: dict) -> dict | None:
    """Fetch a candidate and extract relevant lines for review."""

    repository = candidate["repository"]
    owner, repo = repository.split("/", 1)

    file = {
        "type": "blob",
        "path": candidate["source"],
        "sha": candidate["blob_sha"],
        "size": candidate["size"],
    }

    evidence = fetch_file_content(owner, repo, file)

    if evidence is None:
        return None

    relevant_lines = []

    for line_number, line in enumerate(
        evidence["content"].splitlines(), start=1
    ):
        if any(term in line.lower() for term in SIGNAL_TERMS):
            relevant_lines.append({
                "line": line_number,
                "text": line.strip()[:240],
            })

    return {
        "path": evidence["path"],
        "sha": evidence["sha"],
        "size": evidence["size"],
        "relevant_lines": relevant_lines[:12],
        "content": evidence["content"],
    }


if __name__ == "__main__":
    candidates = find_candidate_evidence(
        CLAIM,
        limit=MAX_CANDIDATES,
    )

    print(f"Claim: {CLAIM}")
    print(f"Candidates to inspect: {len(candidates)}")

    for candidate in candidates:
        print(f"\n{'=' * 60}")
        print(f"Candidate: {candidate['source']}")
        print(f"Ranking score: {candidate['score']}")

        try:
            evidence = inspect_candidate(candidate)

            if evidence is None:
                print("No readable text was returned.")
                continue

            print(f"Blob SHA: {evidence['sha']}")
            print("Full workflow content:")

            for line_number, line in enumerate(
                evidence["content"].splitlines(),
                start=1,
            ):

                print(f"L{line_number}: {line}")

        except Exception as exc:
            print(f"Inspection failed: {exc}")
