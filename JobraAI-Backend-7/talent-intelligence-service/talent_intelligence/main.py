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
| POST | `/analyse/with-role` | Resume + selected role |
| POST | `/analyse/with-jd` | Resume + **required** job description |
"""

_origins_raw = (os.getenv("CORS_ORIGINS") or "").strip()
# Browsers treat http://localhost:3001 and http://127.0.0.1:8000 as cross-origin.
# A bare "*" often fails in practice when combined with redirects, errors, or PNA checks,
# so default dev mode allows local frontends on any port via regex.
_allow_origin_regex: str | None
if _origins_raw:
    _allow_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()]
    if _allow_origins == ["*"]:
        _allow_origin_regex = None
    else:
        _allow_origin_regex = (os.getenv("CORS_ORIGIN_REGEX") or "").strip() or None
else:
    _allow_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    _allow_origin_regex = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"

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
    allow_origin_regex=_allow_origin_regex,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_private_network=True,
)

app.include_router(api_router)
