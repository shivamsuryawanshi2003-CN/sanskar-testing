"""Jobra.ai Streamlit client for ATS fetching flows."""

import json
import os
import sys
from pathlib import Path

import requests
import streamlit as st

_root = Path(__file__).resolve().parent
_tis = _root / "talent-intelligence-service"
if str(_tis) not in sys.path:
    sys.path.insert(0, str(_tis))

from talent_intelligence.config.roles import ROLES  # noqa: E402

DEFAULT_API = os.getenv("TALENT_API_URL", "http://127.0.0.1:8004").rstrip("/")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
NON_RESUME_MESSAGE = "The uploaded document does not look like a complete resume because core ATS sections are missing."


def _roles_options() -> list[tuple[str, str]]:
    rows = sorted(ROLES.values(), key=lambda row: (int(row["id"]), str(row["title"]).lower()))
    return [(str(row["title"]), str(row["id"])) for row in rows]


def _render_role_select() -> str:
    options = _roles_options()
    labels = ["—"] + [label for label, _ in options]
    id_by_label = {"—": ""} | {label: role_id for label, role_id in options}
    picked = st.selectbox("Role", labels, help="Choose the target role. Example: Data Analyst")
    return id_by_label.get(picked, "")


def _post_file(endpoint: str, files: dict, data: dict | None, label: str, lines: list[str]) -> requests.Response:
    if hasattr(st, "status"):
        with st.status(label, expanded=True) as status_box:
            status_box.code(f"POST {endpoint}", language="http")
            for line in lines:
                status_box.markdown(line)
            response = requests.post(endpoint, files=files, data=data or {}, timeout=300)
            if hasattr(status_box, "update"):
                status_box.update(label=f"Done · HTTP {response.status_code}", state="complete" if response.ok else "error")
            return response
    with st.spinner(label):
        return requests.post(endpoint, files=files, data=data or {}, timeout=300)


st.set_page_config(page_title="Jobra.ai ATS", page_icon="📄", layout="centered")
st.title("Jobra.ai ATS")

if "api_base" not in st.session_state:
    st.session_state.api_base = DEFAULT_API

with st.sidebar:
    api_base = st.text_input("API URL", key="api_base").rstrip("/")

uploaded_file = st.file_uploader("Resume", type=["pdf", "docx"], help=f"Accepted formats: PDF or DOCX · Max size: {MAX_UPLOAD_MB} MB")
mode = st.radio("Flow", ["With JD", "With role", "General"], horizontal=True)
role_id = ""
job_description = ""
additional_context = st.text_area("Extra context", height=100, placeholder="Optional notes, tools, or project details.")
if mode == "With JD":
    job_description = st.text_area("Job description", height=180, placeholder="Paste the job description here.")
elif mode == "With role":
    role_id = _render_role_select()
submit = st.button("Fetch ATS", type="primary", use_container_width=True)
if not submit:
    st.stop()
if uploaded_file is None:
    st.error("Upload a resume first.")
    st.stop()
if getattr(uploaded_file, "size", 0) > MAX_UPLOAD_MB * 1024 * 1024:
    st.error(f"File too large. Upload a file up to {MAX_UPLOAD_MB} MB.")
    st.stop()

base = api_base
filename = uploaded_file.name
files = {"file": (filename, uploaded_file.getvalue(), "application/octet-stream")}

try:
    if mode == "With JD":
        if not job_description.strip():
            st.error("Paste a job description for the With JD flow.")
            st.stop()
        endpoint = f"{base}/analyse/with-jd"
        request_data = {"job_description": job_description.strip(), "additional_context": additional_context.strip()}
        response = _post_file(endpoint, files, request_data, "Running JD ATS with LLM comparison...", [f"**File:** `{filename}`"])
    elif mode == "With role":
        if not role_id:
            st.error("Choose a role for the With role flow.")
            st.stop()
        endpoint = f"{base}/analyse/with-role"
        request_data = {"role": role_id, "additional_context": additional_context.strip()}
        response = _post_file(endpoint, files, request_data, "Running role ATS with LLM comparison...", [f"**File:** `{filename}`"])
    else:
        endpoint = f"{base}/analyse/general"
        response = _post_file(endpoint, files, {}, "Running general ATS with hybrid scoring...", [f"**File:** `{filename}`"])
except requests.RequestException as exc:
    st.error(str(exc))
    st.stop()

if response.status_code >= 400:
    st.error(f"{response.status_code}: {response.text[:1500]}")
    st.stop()

data = response.json()
if str(data.get("Summary", "")).strip() == NON_RESUME_MESSAGE:
    st.warning(NON_RESUME_MESSAGE)
    st.stop()

st.markdown("### ATS score")
st.markdown(f"## {data.get('ATS_Score', 0)} / 100")
st.markdown("### Resume health")
st.markdown(f"## {data.get('Resume_Health_Label', 'Moderate')}")
if data.get("Summary"):
    st.write(str(data.get("Summary", "")).strip())

st.download_button(
    "Download JSON",
    json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"),
    file_name=f"ats-{mode.lower().replace(' ', '-')}.json",
    mime="application/json",
)

st.markdown("### Details")
breakdown = data.get("Score_Breakdown") or {}
col1, col2, col3, col4 = st.columns(4)
col1.metric("FORMAT", breakdown.get("FORMAT", "0%"))
col2.metric("SKILLS", breakdown.get("SKILLS", "0%"))
col3.metric("EXPERIENCE", breakdown.get("EXPERIENCE", "0%"))
col4.metric("COMPLETENESS", breakdown.get("COMPLETENESS", "0%"))

st.markdown("### Suggestions")
for item in data.get("Suggestions_for_Improvement") or []:
    st.write(item)

st.markdown("### Missing keywords")
st.json(data.get("Missing_Keywords") or {})

st.markdown("### Achievements or certifications")
for item in data.get("Achievements_or_Certifications") or []:
    st.write(item)

st.markdown("### Resume strengths")
for item in data.get("Resume_Strength") or []:
    st.write(item)

st.markdown("### Key skills")
skills = data.get("Key_Skills") or []
if skills:
    st.write(", ".join(skills))

with st.expander("Raw JSON", expanded=False):
    st.json(data)
