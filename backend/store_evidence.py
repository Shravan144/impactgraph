import logging
from graph_db import execute_query
from ingest_github import fetch_repository, fetch_file_tree
from select_files import select_candidate_files
from fetch_evidence import fetch_file_content
from evidence_parser import extract_references_and_deps
import config

logger = logging.getLogger("impactgraph.store_evidence")

MAX_FILES_TO_ATTEMPT = 25
MAX_FILES_TO_STORE = 15


def ensure_repository_ingested(
    owner: str,
    repo: str,
    claim_focus: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """
    Ensure the repository and its evidence graph are loaded in FalkorDB.
    If already present and force_refresh is False, return cached status immediately.
    """
    repo_id = f"{owner}/{repo}".lower()

    if not force_refresh:
        try:
            check_query = """
            MATCH (r:Repository {id: $repo_id})-[:HAS_EVIDENCE]->(e:Evidence)
            RETURN count(e) AS evidence_count
            """
            res = execute_query(check_query, {"repo_id": repo_id})
            if res.result_set and res.result_set[0][0] > 0:
                return {
                    "repository": repo_id,
                    "status": "cached",
                    "evidence_count": res.result_set[0][0],
                }
        except Exception as exc:
            logger.warning(f"Error checking cached repository in FalkorDB: {exc}")

    return store_repository_evidence(owner, repo, claim_focus)


def store_repository_evidence(
    owner: str,
    repo: str,
    claim_focus: str | None = None,
) -> dict:
    """
    Fetch repository files, parse cross-file references & dependencies,
    and construct the connected evidence graph in FalkorDB.
    """
    repository = fetch_repository(owner, repo)
    default_branch = repository["default_branch"]

    tree = fetch_file_tree(owner, repo, default_branch)
    tree_path_map = {item["path"]: item for item in tree if item["type"] == "blob"}
    known_repo_paths = set(tree_path_map.keys())

    candidates = select_candidate_files(tree)

    # If claim_focus is provided, prioritize files that match keywords in the claim
    if claim_focus:
        from claim_matcher import score_evidence
        candidates.sort(
            key=lambda f: score_evidence(claim_focus, f["path"]),
            reverse=True,
        )

    repo_id = repository["full_name"].lower()

    # 1. Upsert Repository node
    repository_query = """
    MERGE (r:Repository {id: $repo_id})
    SET r.name = $name,
        r.url = $url,
        r.default_branch = $branch,
        r.description = $description
    RETURN r.id
    """
    execute_query(
        repository_query,
        params={
            "repo_id": repo_id,
            "name": repository["full_name"],
            "url": repository["html_url"],
            "branch": default_branch,
            "description": repository.get("description") or "",
        },
    )

    attempted = 0
    stored = 0
    stored_evidence_map: dict[str, str] = {}  # path -> evidence_id
    parsed_evidence: list[dict] = []

    # 2. Fetch and store primary candidate files
    for file in candidates:
        if stored >= MAX_FILES_TO_STORE or attempted >= MAX_FILES_TO_ATTEMPT:
            break

        attempted += 1

        try:
            evidence = fetch_file_content(owner, repo, file)
            if evidence is None:
                continue

            path = evidence["path"]
            sha = evidence["sha"]
            size = evidence["size"]
            content = evidence["content"]
            evidence_id = f"{repo_id}:{path}:{sha}"

            evidence_type = "workflow" if ".github/workflows" in path else (
                "test" if "test" in path.lower() else (
                    "manifest" if any(path.endswith(m) for m in ["requirements.txt", "pyproject.toml", "package.json"]) else "source_file"
                )
            )

            # Store Evidence node with content for high-performance in-graph retrieval
            evidence_query = """
            MERGE (e:Evidence {id: $evidence_id})
            SET e.source = $path,
                e.evidence_type = $evidence_type,
                e.blob_sha = $sha,
                e.size = $size,
                e.content = $content

            WITH e
            MATCH (r:Repository {id: $repo_id})
            MERGE (r)-[:HAS_EVIDENCE]->(e)
            RETURN e.id
            """
            execute_query(
                evidence_query,
                params={
                    "evidence_id": evidence_id,
                    "path": path,
                    "evidence_type": evidence_type,
                    "sha": sha,
                    "size": size,
                    "content": content[:50000],  # Store up to 50KB in graph
                    "repo_id": repo_id,
                },
            )

            stored_evidence_map[path] = evidence_id
            stored += 1

            # Parse references & dependencies
            parsed = extract_references_and_deps(path, content, known_repo_paths)
            parsed_evidence.append({
                "source_path": path,
                "evidence_id": evidence_id,
                "parsed": parsed,
            })

        except Exception as exc:
            logger.warning(f"Could not store {file.get('path')}: {exc}")

    # 3. Store dependencies and cross-file references
    deps_stored = 0
    refs_stored = 0

    for item in parsed_evidence:
        src_ev_id = item["evidence_id"]
        parsed = item["parsed"]

        # Store dependencies
        for dep in parsed.get("dependencies", []):
            dep_id = f"{repo_id}:dep:{dep['name']}"
            dep_query = """
            MERGE (d:Dependency {id: $dep_id})
            SET d.name = $dep_name,
                d.type = $dep_type

            WITH d
            MATCH (e:Evidence {id: $evidence_id})
            MERGE (e)-[:USES_DEPENDENCY]->(d)
            RETURN d.id
            """
            try:
                execute_query(
                    dep_query,
                    params={
                        "dep_id": dep_id,
                        "dep_name": dep["name"],
                        "dep_type": dep["type"],
                        "evidence_id": src_ev_id,
                    },
                )
                deps_stored += 1
            except Exception as exc:
                logger.warning(f"Failed to link dependency {dep['name']}: {exc}")

        # Store cross-file references
        for ref in parsed.get("references", []):
            target_path = ref["target_path"]
            # If target file is not yet stored as evidence, attempt to fetch and store it!
            if target_path not in stored_evidence_map and target_path in tree_path_map:
                try:
                    target_file = tree_path_map[target_path]
                    target_content = fetch_file_content(owner, repo, target_file)
                    if target_content:
                        tgt_sha = target_content["sha"]
                        tgt_size = target_content["size"]
                        tgt_content = target_content["content"]
                        tgt_ev_id = f"{repo_id}:{target_path}:{tgt_sha}"

                        execute_query(
                            """
                            MERGE (e:Evidence {id: $evidence_id})
                            SET e.source = $path,
                                e.evidence_type = 'referenced_script',
                                e.blob_sha = $sha,
                                e.size = $size,
                                e.content = $content

                            WITH e
                            MATCH (r:Repository {id: $repo_id})
                            MERGE (r)-[:HAS_EVIDENCE]->(e)
                            RETURN e.id
                            """,
                            params={
                                "evidence_id": tgt_ev_id,
                                "path": target_path,
                                "sha": tgt_sha,
                                "size": tgt_size,
                                "content": tgt_content[:50000],
                                "repo_id": repo_id,
                            },
                        )
                        stored_evidence_map[target_path] = tgt_ev_id
                        stored += 1
                except Exception as exc:
                    logger.warning(f"Could not fetch referenced file {target_path}: {exc}")

            # Link the cross-file reference in FalkorDB
            if target_path in stored_evidence_map:
                tgt_ev_id = stored_evidence_map[target_path]
                ref_query = """
                MATCH (e1:Evidence {id: $src_id})
                MATCH (e2:Evidence {id: $tgt_id})
                MERGE (e1)-[:REFERENCES {type: $ref_type}]->(e2)
                RETURN e1.id, e2.id
                """
                try:
                    execute_query(
                        ref_query,
                        params={
                            "src_id": src_ev_id,
                            "tgt_id": tgt_ev_id,
                            "ref_type": ref["type"],
                        },
                    )
                    refs_stored += 1
                except Exception as exc:
                    logger.warning(f"Failed to link reference {src_ev_id} -> {tgt_ev_id}: {exc}")

    return {
        "repository": repo_id,
        "files_stored": stored,
        "dependencies_stored": deps_stored,
        "references_created": refs_stored,
    }


if __name__ == "__main__":
    result = ensure_repository_ingested("fastapi", "fastapi", "documentation build")
    print(f"Store result: {result}")
