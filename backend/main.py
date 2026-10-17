
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from report_finding import generate_report


app = FastAPI(
    title="ImpactGraph API",
    description="Evidence-backed software contribution analysis",
    version="0.1.0",
)


class EvidenceItem(BaseModel):
    source: str
    blob_sha: str
    supporting_lines: str | None = None


class InvestigationReport(BaseModel):
    investigation_id: str
    claim: str
    verdict: str
    evidence: list[EvidenceItem]
    limitations: list[str]
    runtime_execution_verified: bool


@app.get("/")
def root():
    return {
        "message": "Welcome to ImpactGraph!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationReport,
)
def get_investigation_report(investigation_id: str):
    try:
        return generate_report(investigation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
