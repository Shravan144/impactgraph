
from ingest_github import fetch_repository, fetch_file_tree


MAX_FILE_SIZE = 200_000

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "coverage",
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".go", ".rs", ".cpp", ".c",
    ".cs", ".php", ".rb", ".swift", ".kt",
}

IMPORTANT_FILENAMES = {
    "readme.md",
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "pom.xml",
    "cargo.toml",
    "go.mod",
    "dockerfile",
}


def select_candidate_files(files: list[dict]) -> list[dict]:
    """Select useful repository files for initial evidence inspection."""

    selected = []

    for file in files:
        if file["type"] != "blob":
            continue

        path = file["path"]
        parts = path.lower().split("/")
        filename = parts[-1]

        if any(part in IGNORED_DIRS for part in parts[:-1]):
            continue

        if file.get("size") is not None and file["size"] > MAX_FILE_SIZE:
            continue

        is_source = any(
            filename.endswith(ext) for ext in SOURCE_EXTENSIONS
        )

        is_test = (
            filename.startswith("test_")
            or filename.endswith("_test.py")
            or "/tests/" in f"/{path.lower()}/"
            or "/test/" in f"/{path.lower()}/"
        )

        is_important = (
            filename in IMPORTANT_FILENAMES
            or filename.startswith("readme.")
            or (
                path.lower().startswith(".github/workflows/")
                and filename.endswith((".yml", ".yaml"))
            )
        )

        if is_source or is_test or is_important:
            selected.append(file)

    return selected


if __name__ == "__main__":
    owner = "fastapi"
    repo = "fastapi"

    repository = fetch_repository(owner, repo)
    files = fetch_file_tree(
        owner,
        repo,
        repository["default_branch"],
    )

    candidates = select_candidate_files(files)

    print(f"Repository: {repository['full_name']}")
    print(f"Total tree entries: {len(files)}")
    print(f"Candidate files: {len(candidates)}")
    print("\nFirst 30 candidates:")

    for file in candidates[:30]:
        print(f"{file.get('size', '?'):>8} bytes  {file['path']}")
