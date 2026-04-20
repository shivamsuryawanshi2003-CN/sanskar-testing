# JobraAI Backend

Resume ATS analysis backend for Jobra.ai. The project now focuses only on the active talent-intelligence flow and supports both:

- Deterministic ATS scoring for `General`, `With role`, and `With JD`
- Hybrid analysis output: code-driven scoring + optional LLM-enriched sectioned insights when `OPENAI_API_KEY` is configured
- OpenAI-backed structured resume upgrade output when `OPENAI_API_KEY` is configured

## API modes

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/analyse/general` | ATS scan without role context |
| `POST` | `/analyse/with-role` | Resume analysis against a selected role |
| `POST` | `/analyse/with-jd` | Resume analysis against a pasted JD only |
| `POST` | `/analyse/upgrade` | Structured resume upgrade output |

Scoring notes:

- `General` is capped below top targeted-match scores.
- `With role` and `With JD` use stricter keyword, section, impact, and formatting checks.
- ATS scores are hard-capped at `90` to avoid unrealistic `100/100` outputs.

## Project layout

```text
JobraAI-Backend/
├── app.py
├── streamlit_app.py
├── requirements.txt
└── talent-intelligence-service/
    ├── requirements.txt
    └── talent_intelligence/
        ├── main.py
        ├── api/
        ├── config/
        ├── schemas/
        └── services/
            ├── analyzer.py
            ├── heuristics.py
            ├── llm_shared/
            ├── suggestion.py
            ├── with_jd/
            └── with_role/
```

## Configuration

Required only for model-backed analysis:

- `OPENAI_API_KEY`

Keep the key outside the repository and inject it at runtime through your deployment environment or local shell.

Optional:

- `OPENAI_MODEL` or `OPENAI_MODE`
- `OPENAI_TEMPERATURE`
- `CORS_ORIGINS` (comma-separated; use `*` for all origins). If unset, local dev is allowed for `http://localhost` / `http://127.0.0.1` / `http://[::1]` on any port via a built-in regex.
- `CORS_ORIGIN_REGEX` (optional; only when `CORS_ORIGINS` is set and not `*`)
- `MAX_UPLOAD_SIZE_MB` (defaults to `10`)
- `TALENT_API_URL`

The ATS scoring flows do not depend on the API key anymore, which keeps the scoring logic stable and reduces hallucination. The key is still useful for resume-upgrade generation.

## Run locally

API:

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Streamlit:

```bash
streamlit run streamlit_app.py
```

## Batch test many resumes

You can run a whole folder of resumes without manually uploading them:

```bash
.venv/bin/python scripts/batch_test_resumes.py ./resumes --mode general --output batch-results.csv
```

Role-based batch test:

```bash
.venv/bin/python scripts/batch_test_resumes.py ./resumes --mode with-role --role "Data Analyst" --output batch-role-results.csv
```

JD-based batch test:

```bash
.venv/bin/python scripts/batch_test_resumes.py ./resumes --mode with-jd --jd-file jd.txt --output batch-jd-results.csv
```

Optional flags:

- `--recursive` to scan nested folders
- `--additional-context "..."` for extra context
- `--save-json` to store full JSON response per resume

The script runs the FastAPI app in-process using `TestClient`, so you do not need to start `uvicorn` first.


## Recent changes

- Hard upload limit aligned to **10 MB** in both API and Streamlit UI.
- Added `Detailed_Analysis` and `Improvement_Roadmap` to make the output more sectioned and future-suggestion friendly.
- Added score calibration so results are less inflated compared with common ATS checkers that emphasize keyword matching, parse quality, measurable impact, and standard section structure.
- Preserved deterministic scoring as the source of truth while allowing optional LLM enrichment for section narratives.


## Notes in this build
- Resume upload limit defaults to 20 MB.
- Non-resume uploads now return only a single ATS warning line in the UI.
- Role catalog expanded to 80+ roles.
- When OPENAI_API_KEY is configured, the hybrid layer uses the chat completions path and works with gpt-3.5-turbo for stronger calibration and structured sections.
