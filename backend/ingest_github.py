import httpx
import config

GITHUB_API = "https://api.github.com"


def get_github_headers() -> dict[str, str]:
    """Construct request headers including token authorization if available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ImpactGraph-Investigation-Agent",
    }
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    return headers


def fetch_repository(owner: str, repo: str) -> dict:
    """Fetch metadata for a public GitHub repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"

    try:
        response = httpx.get(
            url,
            headers=get_github_headers(),
            timeout=15.0,
            follow_redirects=True,
        )
        if response.status_code == 404:
            raise ValueError(f"Repository '{owner}/{repo}' not found on GitHub.")
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise ValueError(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN in .env for 5,000 requests/hour."
            )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Failed to communicate with GitHub API: {exc}") from exc

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

    try:
        response = httpx.get(
            url,
            headers=get_github_headers(),
            params={"recursive": "1"},
            timeout=30.0,
            follow_redirects=True,
        )
        if response.status_code == 404:
            raise ValueError(f"Git tree for branch '{branch}' in '{owner}/{repo}' not found.")
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise ValueError(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN in .env for 5,000 requests/hour."
            )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"Failed to fetch Git tree from GitHub API: {exc}") from exc

    data = response.json()

    if data.get("truncated"):
        # We can still use the items returned, but we note it.
        pass

    return [
        {
            "path": item["path"],
            "type": item["type"],
            "size": item.get("size"),
            "sha": item.get("sha"),
        }
        for item in data.get("tree", [])
    ]


def fetch_workflow_runs(owner: str, repo: str, workflow_filename: str | None = None) -> dict:
    """Fetch recent GitHub Actions workflow runs to verify runtime execution."""
    if workflow_filename:
        # e.g. "build-docs.yml" or ".github/workflows/build-docs.yml"
        filename = workflow_filename.split("/")[-1]
        url = f"{GITHUB_API}/repos/{owner}/{repo}/actions/workflows/{filename}/runs"
    else:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/actions/runs"

    try:
        response = httpx.get(
            url,
            headers=get_github_headers(),
            params={"per_page": 5},
            timeout=15.0,
            follow_redirects=True,
        )
        if response.status_code in (404, 403):
            return {
                "verified": False,
                "total_runs": 0,
                "latest_run": None,
                "reason": f"GitHub Actions runs endpoint returned status {response.status_code}.",
            }
        response.raise_for_status()
        data = response.json()
        runs = data.get("workflow_runs", [])
        total_count = data.get("total_count", len(runs))

        if not runs:
            return {
                "verified": False,
                "total_runs": 0,
                "latest_run": None,
                "reason": "No public workflow run executions found for this workflow.",
            }

        latest = runs[0]
        status = latest.get("status")  # e.g. "completed"
        conclusion = latest.get("conclusion")  # e.g. "success", "failure"
        is_success = (status == "completed" and conclusion == "success")

        return {
            "verified": is_success,
            "total_runs": total_count,
            "latest_run": {
                "id": latest.get("id"),
                "name": latest.get("name"),
                "status": status,
                "conclusion": conclusion,
                "created_at": latest.get("created_at"),
                "html_url": latest.get("html_url"),
                "head_branch": latest.get("head_branch"),
                "event": latest.get("event"),
            },
            "reason": (
                f"Workflow execution verified: latest run '{latest.get('name')}' finished with {conclusion}."
                if is_success
                else f"Workflow execution not verified: latest status is {status} (conclusion: {conclusion})."
            ),
        }
    except Exception as exc:
        return {
            "verified": False,
            "total_runs": 0,
            "latest_run": None,
            "reason": f"Could not inspect GitHub Actions runtime execution: {exc}",
        }


if __name__ == "__main__":
    owner = "fastapi"
    repo = "fastapi"

    repository = fetch_repository(owner, repo)
    print(f"Repository: {repository['full_name']}")
    runs = fetch_workflow_runs(owner, repo, "build-docs.yml")
    print(f"Workflow runs for build-docs.yml: {runs}")
