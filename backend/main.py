"""Company-OS deployment foundation API (not the complete product)."""

from fastapi import FastAPI

app = FastAPI(
    title="Company-OS API",
    description="Initial connectivity and deployment checks for the Company-OS platform.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "company-os-api", "status": "ok", "stage": "foundation"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"service": "company-os-api", "status": "ok", "stage": "foundation"}
