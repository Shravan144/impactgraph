
import base64

import httpx

from ingest_github import fetch_repository, fetch_file_tree
from select_files import select_candidate_files


GITHUB_API = "https://api.github.com"
MAX_CONTENT_SIZE = 200_000
MAX_FILES_TO_FETCH = 5
MAX_FILES_TO_ATTEMPT = 10


def fetch_file_content(
    owner: str,
    repo: str,
    file: dict,
) -> dict | None:
    """Fetch one small GitHub file without executing its contents."""

    if file["type"] != "blob":
        return None

    size = file.get("size")

    if size is None or size <= 0 or size > MAX_CONTENT_SIZE:
        return None

    sha = file.get("sha")

    if not sha:
        return None

    url = f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs/{sha}"

    response = httpx.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=20.0,
    )
    response.raise_for_status()

    blob = response.json()

    if blob.get("encoding") != "base64":
        raise ValueError(f"Unexpected encoding for {file['path']}")

    encoded_content = "".join(blob["content"].split())
    content_bytes = base64.b64decode(encoded_content, validate=True)

    # GitHub's blob size is the size of the original file.
    if len(content_bytes) != size:
        raise ValueError(f"Size mismatch for {file['path']}")

    try:
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None

    return {
        "path": file["path"],
        "sha": sha,
        "size": size,
        "content": content,
    }



if __name__ == "__main__":
    owner = "fastapi"
    repo = "fastapi"

    repository = fetch_repository(owner, repo)
    tree = fetch_file_tree(
        owner,
        repo,
        repository["default_branch"],
    )

    candidates = select_candidate_files(tree)

    fetched = 0
    attempted = 0

    for file in candidates:
        if fetched >= MAX_FILES_TO_FETCH:
            break

        if attempted >= MAX_FILES_TO_ATTEMPT:
            break

        attempted += 1

        try:
            evidence = fetch_file_content(owner, repo, file)

            if evidence is None:
                continue

            print(f"\nFile: {evidence['path']}")
            print(f"Git blob SHA: {evidence['sha']}")
            print(f"Size: {evidence['size']} bytes")
            print("Content preview:")
            print(evidence["content"][:500])

            fetched += 1

        except (httpx.HTTPError, ValueError) as exc:
            print(f"Could not fetch {file['path']}: {exc}")

    print(f"\nAttempted: {attempted}")
    print(f"Successfully fetched: {fetched}")
