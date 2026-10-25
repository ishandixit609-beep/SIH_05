from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.api.audit import router as audit_router
from app.api.applications import router as applications_router
from app.api.findings import router as findings_router
from app.api.rules import router as rules_router
from app.api.documents import router as documents_router
from app.api.others import router as others_router
from app.api.institution import router as institution_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SATYAPAN Scrutiny Backend",
    version="1.0.0",
    description="Backend API for AICTE Application Scrutiny (SIH26261 / PS5)",
    lifespan=lifespan,
)

# CORS setup for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from pathlib import Path
from fastapi.responses import FileResponse

ACCOMPLISHMENTS_FILE = Path(__file__).resolve().parent.parent / "ACCOMPLISHMENTS.md"
SUMMARY_FILE = Path(__file__).resolve().parent.parent.parent / "CODING_RUN_SUMMARY.md"


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "satyapan-backend"}


@app.get("/api/download/summary")
@app.get("/api/summary.md")
async def download_summary():
    file_path = SUMMARY_FILE if SUMMARY_FILE.exists() else ACCOMPLISHMENTS_FILE
    if file_path.exists():
        return FileResponse(
            str(file_path),
            media_type="text/markdown",
            filename="CODING_RUN_SUMMARY.md",
        )
    return {"detail": "Summary file not found"}


@app.get("/api/download/accomplishments")
@app.get("/api/accomplishments.md")
async def download_accomplishments():
    if ACCOMPLISHMENTS_FILE.exists():
        return FileResponse(
            str(ACCOMPLISHMENTS_FILE),
            media_type="text/markdown",
            filename="SATYAPAN_ACCOMPLISHMENTS.md",
        )
    return {"detail": "Accomplishments file not found"}


# Mount all routers under /api as required by the API contract
app.include_router(audit_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(findings_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(others_router, prefix="/api")
app.include_router(institution_router, prefix="/api")

# Also mount documents router without prefix for direct document fetches if any
app.include_router(documents_router)
