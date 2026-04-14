"""Jobra.ai Talent Intelligence — resume ATS API (analysis endpoints only)."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talent_intelligence.api.router import api_router

_DESCRIPTION = """
**Three analysis endpoints** (multipart resume upload):

| Method | Path | Use case |
|--------|------|----------|
| POST | `/analyse/general` | ATS score without role |
| POST | `/analyse/with-role` | Role + resume; optional `job_description` (same scoring as with-jd when set) |
| POST | `/analyse/with-jd` | Role + **required** job description + resume |
"""

_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
if _origins_raw:
    _allow_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
else:
    _allow_origins = ["*"]

app = FastAPI(
    title="Jobra.ai Talent Intelligence",
    description=_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "analysis", "description": "Resume upload and ATS analysis."},
    ],
)

_allow_credentials = _allow_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router)
