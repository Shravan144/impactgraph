
from investigation import (
    InvestigationRequest,
    collect_candidates,
    inspect_candidates,
    store_investigation,
)


request = InvestigationRequest(
    owner="fastapi",
    repo="fastapi",
    claim=(
        "This project uses GitHub Actions "
        "to automate its documentation build."
    ),
)

print("1. Finding candidate evidence...")
candidates = collect_candidates(request)
print(f"Candidates found: {len(candidates['candidates'])}")

print("\n2. Inspecting source files...")
investigation = inspect_candidates(candidates)
print(f"Evidence retrieved: {investigation['evidence_count']}")

print("\n3. Saving finding to FalkorDB...")
report = store_investigation(investigation)

print("\nInvestigation result:")
print(report)
