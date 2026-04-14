# JobraAI Backend

Resume **ATS (Applicant Tracking System) analysis** for Jobra.ai: a **FastAPI** service that scores resumes via the **OpenAI** API, plus an optional **Streamlit** UI for manual testing.

## Current state (overview)

- **API** lives under `talent-intelligence-service/talent_intelligence/`. All analysis routes use **multipart** upload (PDF or DOCX).
- **Role-aware** flows use a **catalog** of roles (`talent_intelligence/config/roles.json`) for titles, skills, and built-in role context.
- **Scoring logic** is split by use case:
  - **General** — no role; several engines (default OpenAI path, optional `pure_llm` / `hybrid` in `services/without_jd/`). All routes share **extract + resume validity** via `services/resume_intake.py`.
  - **With role** — catalog role + resume; **`job_description` is optional**. If provided, scoring matches the “with JD” path.
  - **With JD** — catalog role + **required** pasted job description + resume (same LLM path as with-role when JD is present).
- **Shared LLM plumbing** — prompts and OpenAI helpers in `services/llm_shared/`; role-only analysis in `services/with_role/`; role+JD in `services/with_jd/`. `services/analyzer.py` picks the branch from `AnalyzeRequest` (empty vs non-empty `job_description`).
- **Streamlit** — `streamlit_app.py` at repo root calls the same HTTP API (`TALENT_API_URL`, default `http://127.0.0.1:8000`).

Interactive API docs: `/docs` and `/redoc` when the server is running.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/analyse/general` | ATS score without a catalog role |
| `POST` | `/analyse/with-role` | Role + resume; |
| `POST` | `/analyse/with-jd` | **required** `job_description` + resume |

## Repository layout (high level)

```
JobraAI-Backend/
├── README.md
├── streamlit_app.py              # Optional UI for ATS / with-role / with-jd
└── talent-intelligence-service/
    ├── requirements.txt
    └── talent_intelligence/
        ├── main.py               # FastAPI app, CORS
        ├── api/routes/ats/       # general, with_role, with_jd, common
        ├── config/               # roles catalog
        ├── schemas/              # Pydantic request/response models
        └── services/
            ├── analyzer.py       # Orchestrates role + JD vs role-only LLM calls
            ├── llm_service.py    # Exports LLM entrypoints
            ├── llm_shared/       # Prompts + OpenAI utilities
            ├── with_role/        # Role-only full analysis
            ├── with_jd/          # Role + pasted JD full analysis
            └── without_jd/       # Pure LLM + hybrid engines for /analyse/general (package: services/without_jd)
```

## Configuration

Set at least:

| Variable | Role |
|----------|------|
| `OPENAI_API_KEY` | Required for LLM calls |
| `OPENAI_MODE` or `OPENAI_MODEL` | Model id **string** (e.g. `gpt-4o`, `gpt-4o-mini`). If unset, defaults to `gpt-4o-mini`. Must not be JSON or YAML—only the model name. |

Optional:

| Variable | Role |
|----------|------|
| `CORS_ORIGINS` | Comma-separated origins; if unset, `*` is used |
| `MAX_UPLOAD_SIZE_MB` | Upload limit (default `10`) |

For the Streamlit app: `TALENT_API_URL` (base URL of the API, no trailing slash required by the app’s `.rstrip("/")`).

Use a `.env` file in the working directory if you rely on `python-dotenv` (loaded in shared LLM code).

## Run locally

**API** (from `talent-intelligence-service`):

```bash
pip install -r requirements.txt
uvicorn talent_intelligence.main:app --reload --host 0.0.0.0 --port 8000
```

**Streamlit** (from repository root, with API already running):

```bash
pip install -r talent-intelligence-service/requirements.txt
streamlit run streamlit_app.py
```

## Tech stack

- **Python**, **FastAPI**, **Uvicorn**, **Pydantic**
- **OpenAI** (Responses / chat-style flows per `llm_shared` and route handlers)
- **pdfplumber** / **python-docx** for resume text extraction
- **Streamlit** + **requests** for the demo UI
