
import httpx


GITHUB_API = "https://api.github.com"


def fetch_repository(owner: str, repo: str) -> dict:
    """Fetch metadata for a public GitHub repository."""

    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    response = httpx.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=15.0,
        follow_redirects=True,
    )
    response.raise_for_status()

    data = response.json()

    return {
        "owner": data["owner"]["login"],
        "name": data["name"],
        "full_name": data["full_name"],
        "description": data.get("description"),
        "default_branch": data["default_branch"],
        "html_url": data["html_url"],
    }


def fetch_file_tree(owner: str, repo: str, branch: str) -> list[dict]:
    """Fetch the paths in a repository's default branch."""

    url = f"{GITHUB_API}/repos/{owner}/{repo}/git/trees/{branch}"

    response = httpx.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        params={"recursive": "1"},
        timeout=30.0,
        follow_redirects=True,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("truncated"):
        raise ValueError(
            "GitHub returned an incomplete file tree. "
            "We should not treat it as a complete inventory."
        )

    return [
        {
            "path": item["path"],
            "type": item["type"],
            "size": item.get("size"),
            "sha": item.get("sha"),
        }
        for item in data["tree"]
    ]


if __name__ == "__main__":
    owner = "fastapi"
    repo = "fastapi"

    repository = fetch_repository(owner, repo)
    files = fetch_file_tree(
        owner,
        repo,
        repository["default_branch"],
    )

    print(f"Repository: {repository['full_name']}")
    print(f"Default branch: {repository['default_branch']}")
    print(f"Total tree entries: {len(files)}")
    print("\nFirst 20 entries:")

    for item in files[:20]:
        print(f"{item['type']:4} {item['path']}")
