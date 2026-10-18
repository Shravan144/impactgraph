import base64
import logging
import httpx
from ingest_github import GITHUB_API, get_github_headers
import config

logger = logging.getLogger("impactgraph.fetch_evidence")
MAX_CONTENT_SIZE = config.MAX_FILE_SIZE


def fetch_raw_content(owner: str, repo: str, path: str, branch: str = "master") -> str | None:
    """Fallback fetch via raw.githubusercontent.com which avoids REST API rate limits."""
    clean_path = path.lstrip("/")
    branches = [branch]
    if "master" not in branches:
        branches.append("master")
    if "main" not in branches:
        branches.append("main")

    for br in branches:
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{clean_path}"
        try:
            response = httpx.get(
                url,
                headers={"User-Agent": "ImpactGraph-Agent"},
                timeout=4.0,
                follow_redirects=True,
            )
            if response.status_code == 200:
                return response.text
        except Exception:
            continue
    return None


def fetch_file_content(
    owner: str,
    repo: str,
    file: dict,
) -> dict | None:
    """Fetch one small GitHub file blob without executing its contents."""

    if file.get("type") != "blob":
        return None

    size = file.get("size")
    if size is not None and (size <= 0 or size > MAX_CONTENT_SIZE):
        return None

    path = file.get("path", "")
    sha = file.get("sha")

    # 1. Try official GitHub REST Blobs API if token is provided or available
    if sha and config.GITHUB_TOKEN:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/git/blobs/{sha}"
        try:
            response = httpx.get(
                url,
                headers=get_github_headers(),
                timeout=5.0,
                follow_redirects=True,
            )
            if response.status_code == 200:
                blob = response.json()
                if blob.get("encoding") == "base64":
                    encoded_content = "".join(blob["content"].split())
                    content_bytes = base64.b64decode(encoded_content, validate=True)
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        content = content_bytes.decode("latin-1", errors="replace")
                    return {
                        "path": path,
                        "sha": sha,
                        "size": len(content_bytes),
                        "content": content,
                    }
        except Exception as exc:
            logger.debug(f"GitHub Blobs API fetch failed for {path}: {exc}")

    # 2. Resilient Fast Fallback: raw.githubusercontent.com
    if path:
        raw_text = fetch_raw_content(owner, repo, path)
        if raw_text is not None:
            return {
                "path": path,
                "sha": sha or "raw_fallback_sha",
                "size": len(raw_text.encode("utf-8")),
                "content": raw_text,
            }

    return None


def fetch_file_by_path(
    owner: str,
    repo: str,
    path: str,
    branch: str = "master",
) -> dict | None:
    """Fetch file content directly by repository relative path."""
    raw = fetch_raw_content(owner, repo, path, branch=branch)
    if raw is not None:
        return {
            "path": path,
            "sha": "raw_sha",
            "size": len(raw.encode("utf-8")),
            "content": raw,
        }
    return None
