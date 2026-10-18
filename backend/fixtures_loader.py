import json
import logging
from pathlib import Path
from typing import Any

from graph_db import execute_query, get_graph

logger = logging.getLogger("impactgraph.fixtures_loader")
FIXTURES_PATH = Path(__file__).parent / "fixtures" / "repo_fixtures.json"

_cached_fixtures: dict[str, Any] | None = None


def get_all_fixtures() -> dict[str, Any]:
    """Load and cache repo fixtures from disk."""
    global _cached_fixtures
    if _cached_fixtures is None:
        if FIXTURES_PATH.exists():
            try:
                with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
                    _cached_fixtures = json.load(f)
            except Exception as exc:
                logger.error(f"Failed to load repository fixtures: {exc}")
                _cached_fixtures = {}
        else:
            _cached_fixtures = {}
    return _cached_fixtures


def load_repo_fixture(repo_id: str) -> dict[str, Any] | None:
    """Retrieve fixture data for a specific owner/repo identifier."""
    fixtures = get_all_fixtures()
    return fixtures.get(repo_id.lower())


def seed_graph_if_empty() -> dict[str, Any]:
    """
    Check if the active FalkorDB instance is empty (e.g. fresh cloud database).
    If empty, automatically seeds verified repository structures, multi-hop references,
    and supply-chain dependencies from offline fixtures.
    """
    try:
        check_res = execute_query("MATCH (n) RETURN count(n) AS cnt")
        if check_res and check_res.result_set and check_res.result_set[0][0] > 0:
            logger.info("FalkorDB already contains data; skipping initial fixture seeding.")
            return {"status": "skipped", "reason": "database_not_empty"}
    except Exception as exc:
        logger.warning(f"Could not verify database emptiness: {exc}")
        return {"status": "error", "error": str(exc)}

    fixtures = get_all_fixtures()
    if not fixtures:
        logger.warning("No offline fixtures found to seed.")
        return {"status": "skipped", "reason": "no_fixtures"}

    logger.info("FalkorDB is empty. Seeding verified offline repository graphs...")
    seeded_repos = 0
    seeded_files = 0

    for repo_id, data in fixtures.items():
        try:
            # 1. Merge Repository node
            execute_query(
                """
                MERGE (r:Repository {id: $id})
                ON CREATE SET r.name = $name,
                              r.default_branch = $branch,
                              r.description = $desc,
                              r.html_url = $html_url
                """,
                {
                    "id": repo_id,
                    "name": data["name"],
                    "branch": data.get("default_branch", "master"),
                    "desc": data.get("description", ""),
                    "html_url": data.get("html_url", f"https://github.com/{repo_id}"),
                },
            )

            # 2. Merge Evidence nodes and HAS_EVIDENCE edges
            for path, finfo in data.get("files", {}).items():
                ev_id = f"{repo_id}:{path}"
                execute_query(
                    """
                    MERGE (e:Evidence {source: $src})
                    ON CREATE SET e.id = $id,
                                  e.evidence_type = $type,
                                  e.blob_sha = $sha,
                                  e.content = $content,
                                  e.supporting_lines = $lines
                    WITH e
                    MATCH (r:Repository {id: $repo_id})
                    MERGE (r)-[:HAS_EVIDENCE]->(e)
                    """,
                    {
                        "src": path,
                        "id": ev_id,
                        "type": finfo.get("type", "source_file"),
                        "sha": finfo.get("blob_sha", "sha_cached"),
                        "content": finfo.get("content", ""),
                        "lines": finfo.get("supporting_lines", ""),
                        "repo_id": repo_id,
                    },
                )
                seeded_files += 1

            # 3. Merge REFERENCES edges
            for ref in data.get("references", []):
                execute_query(
                    """
                    MATCH (e1:Evidence {source: $src1})
                    MATCH (e2:Evidence {source: $src2})
                    MERGE (e1)-[r:REFERENCES {type: $rtype}]->(e2)
                    """,
                    {
                        "src1": ref["source"],
                        "src2": ref["target"],
                        "rtype": ref.get("type", "invoked_script"),
                    },
                )

            # 4. Merge Dependency nodes and USES_DEPENDENCY edges
            for dep in data.get("dependencies", []):
                dep_name = dep["name"]
                dep_type = dep.get("type", "module")
                dep_id = f"{dep_type}:{dep_name}"
                execute_query(
                    """
                    MERGE (d:Dependency {id: $did})
                    ON CREATE SET d.name = $name, d.type = $type
                    WITH d
                    MATCH (e:Evidence {source: $src})
                    MERGE (e)-[:USES_DEPENDENCY]->(d)
                    """,
                    {
                        "did": dep_id,
                        "name": dep_name,
                        "type": dep_type,
                        "src": dep["source"],
                    },
                )

            seeded_repos += 1
        except Exception as exc:
            logger.error(f"Error seeding fixture repository {repo_id}: {exc}")

    # Seed baseline investigation memory for FastAPI
    try:
        execute_query(
            """
            MATCH (r:Repository {id: 'fastapi/fastapi'})
            MERGE (c:Claim {id: 'claim-fastapi-docs'})
            ON CREATE SET c.text = 'This project uses GitHub Actions to automate its documentation build.',
                          c.verdict = 'supported'
            MERGE (r)-[:HAS_CLAIM]->(c)
            MERGE (i:Investigation {id: 'investigation-baseline-fastapi'})
            ON CREATE SET i.status = 'completed',
                          i.verdict = 'supported',
                          i.rationale = 'The repository configures automated documentation building via GitHub Actions workflow .github/workflows/build-docs.yml.',
                          i.timestamp = '2026-10-18T12:00:00Z',
                          i.evaluation_mode = 'deterministic_rule_engine',
                          i.runtime_execution_verified = true
            MERGE (i)-[:EVALUATED]->(c)
            WITH i
            MATCH (e:Evidence {source: '.github/workflows/build-docs.yml'})
            MERGE (i)-[:USED_EVIDENCE]->(e)
            """
        )
    except Exception as exc:
        logger.warning(f"Failed to seed baseline investigation: {exc}")

    logger.info(f"Seeded {seeded_repos} repositories ({seeded_files} files) into FalkorDB.")
    return {
        "status": "seeded",
        "repositories_count": seeded_repos,
        "files_count": seeded_files,
    }
