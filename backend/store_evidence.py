
from falkordb import FalkorDB

from ingest_github import fetch_repository, fetch_file_tree
from select_files import select_candidate_files
from fetch_evidence import fetch_file_content


MAX_FILES_TO_ATTEMPT = 10
MAX_FILES_TO_STORE = 5


def store_repository_evidence(owner: str, repo: str) -> None:
    """Fetch a small sample of files and store their metadata in FalkorDB."""

    repository = fetch_repository(owner, repo)

    tree = fetch_file_tree(
        owner,
        repo,
        repository["default_branch"],
    )

    candidates = select_candidate_files(tree)

    db = FalkorDB(host="localhost", port=6379)
    graph = db.select_graph("ImpactGraph")

    repo_id = repository["full_name"].lower()

    repository_query = """
    MERGE (r:Repository {id: $repo_id})
    SET r.name = $name,
        r.url = $url,
        r.default_branch = $branch
    RETURN r.id
    """

    graph.query(
        repository_query,
        params={
            "repo_id": repo_id,
            "name": repository["full_name"],
            "url": repository["html_url"],
            "branch": repository["default_branch"],
        },
    )

    attempted = 0
    stored = 0

    for file in candidates:
        if stored >= MAX_FILES_TO_STORE:
            break

        if attempted >= MAX_FILES_TO_ATTEMPT:
            break

        attempted += 1

        try:
            evidence = fetch_file_content(owner, repo, file)

            if evidence is None:
                continue

            evidence_id = (
                f"{repo_id}:{evidence['path']}:{evidence['sha']}"
            )

            evidence_query = """
            MERGE (e:Evidence {id: $evidence_id})
            SET e.source = $path,
                e.evidence_type = 'source_file',
                e.blob_sha = $sha,
                e.size = $size

            WITH e
            MATCH (r:Repository {id: $repo_id})
            MERGE (r)-[:HAS_EVIDENCE]->(e)

            RETURN e.id
            """

            graph.query(
                evidence_query,
                params={
                    "evidence_id": evidence_id,
                    "path": evidence["path"],
                    "sha": evidence["sha"],
                    "size": evidence["size"],
                    "repo_id": repo_id,
                },
            )

            print(f"Stored evidence: {evidence['path']}")
            stored += 1

        except Exception as exc:
            print(f"Could not store {file['path']}: {exc}")

    print(f"\nRepository: {repository['full_name']}")
    print(f"Files attempted: {attempted}")
    print(f"Evidence records stored: {stored}")


if __name__ == "__main__":
    store_repository_evidence("fastapi", "fastapi")
