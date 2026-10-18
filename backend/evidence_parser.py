import re
from pathlib import PurePosixPath
from typing import Any


def extract_references_and_deps(
    path: str,
    content: str,
    known_repo_paths: set[str],
) -> dict[str, list[dict[str, Any]]]:
    """
    Extract cross-file references and external dependencies from a file's content.
    Returns:
        {
            "references": [{"target_path": str, "type": "script" | "import"}],
            "dependencies": [{"name": str, "type": "action" | "package" | "tool"}]
        }
    """
    references: list[dict[str, Any]] = []
    dependencies: list[dict[str, Any]] = []

    posix_path = PurePosixPath(path.lower())
    is_workflow = (
        posix_path.is_relative_to(".github/workflows")
        if hasattr(posix_path, "is_relative_to")
        else str(posix_path).startswith(".github/workflows")
    ) or path.endswith((".yml", ".yaml"))

    is_python = path.endswith(".py")

    # 1. GitHub Actions Workflows
    if is_workflow:
        # Extract actions dependencies, e.g. "uses: actions/checkout@v4"
        action_matches = re.findall(
            r"uses:\s*([a-zA-Z0-9_\-\.\/]+@[a-zA-Z0-9_\-\.]+)",
            content,
            re.IGNORECASE,
        )
        for action in set(action_matches):
            dependencies.append({
                "name": action.strip(),
                "type": "github_action",
            })

        # Extract tools mentioned in run steps, e.g. "mkdocs", "pytest", "sphinx", "uv"
        tools = {"mkdocs", "sphinx", "pytest", "uv", "pip", "ruff", "mypy", "docker"}
        for tool in tools:
            if re.search(rf"\b{tool}\b", content, re.IGNORECASE):
                dependencies.append({
                    "name": tool,
                    "type": "tool",
                })

        # Extract referenced repository files (e.g. scripts/docs.py, ./scripts/docs.py)
        for repo_file in known_repo_paths:
            if repo_file == path:
                continue
            # Check for direct mention or with leading ./ or /
            file_name = PurePosixPath(repo_file).name
            patterns = [
                re.escape(repo_file),
                re.escape(f"./{repo_file}"),
                rf"\b{re.escape(file_name)}\b",
            ]
            for pattern in patterns:
                if re.search(pattern, content):
                    references.append({
                        "target_path": repo_file,
                        "type": "invoked_script",
                    })
                    break

    # 2. Python Files
    elif is_python:
        # Extract import statements
        import_matches = re.findall(
            r"^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))",
            content,
            re.MULTILINE,
        )
        for imp1, imp2 in import_matches:
            module = (imp1 or imp2).split(".")[0]
            if module:
                dependencies.append({
                    "name": module,
                    "type": "python_module",
                })

        # Check references to other python files in repo
        for repo_file in known_repo_paths:
            if repo_file.endswith(".py") and repo_file != path:
                mod_name = PurePosixPath(repo_file).stem
                if re.search(rf"\bimport\s+{mod_name}\b|\bfrom\s+[\.\w]*{mod_name}\b", content):
                    references.append({
                        "target_path": repo_file,
                        "type": "imported_module",
                    })

    # Deduplicate
    unique_refs = []
    seen_refs = set()
    for ref in references:
        key = (ref["target_path"], ref["type"])
        if key not in seen_refs:
            seen_refs.add(key)
            unique_refs.append(ref)

    unique_deps = []
    seen_deps = set()
    for dep in dependencies:
        key = (dep["name"], dep["type"])
        if key not in seen_deps:
            seen_deps.add(key)
            unique_deps.append(dep)

    return {
        "references": unique_refs,
        "dependencies": unique_deps,
    }
