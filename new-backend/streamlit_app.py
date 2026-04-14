# AI assisted development
"""Jobra.ai — ATS UI (Streamlit): resume upload and three analysis modes."""

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
from talent_intelligence.schemas.analysis import AnalyzeResponse  # noqa: E402

DEFAULT_API = os.getenv("TALENT_API_URL", "http://127.0.0.1:8000").rstrip("/")

# Top-level keys from the API schema (used to render in a stable order and catch extras).
_RESPONSE_FIELD_NAMES = tuple(AnalyzeResponse.model_fields.keys())


def _roles_options() -> list[tuple[str, str]]:
    """(label, id) sorted by id."""
    rows = sorted(ROLES.values(), key=lambda r: (str(r["id"]).lower(), str(r["title"]).lower()))
    return [(f"{r['id']} — {r['title']}", str(r["id"])) for r in rows]


def _post_file(endpoint: str, files: dict, data: dict | None, label: str, lines: list[str]) -> requests.Response:
    """Show st.status steps when available (Streamlit ≥1.33), else spinner."""
    if hasattr(st, "status"):
        with st.status(label, expanded=True) as s:
            s.markdown("**Status** · Processing your resume…")
            s.markdown("**Endpoint**")
            s.code(f"POST {endpoint}", language="http")
            for line in lines:
                s.markdown(line)
            r = requests.post(endpoint, files=files, data=data or {}, timeout=300)
            state = "complete" if r.ok else "error"
            if hasattr(s, "update"):
                s.update(label=f"Done · HTTP {r.status_code}", state=state)
            return r
    with st.spinner(label):
        return requests.post(endpoint, files=files, data=data or {}, timeout=300)


def _pct(val: object) -> str:
    try:
        return f"{int(round(float(val)))}%"
    except (TypeError, ValueError):
        return "0%"


def _render_analysis_result(data: dict) -> None:
    """Display every field returned by the API, including unknown top-level keys."""
    st.subheader("Results")

    # ATS score (always prominent when present)
    if "ATS_Score" in data:
        score = data.get("ATS_Score")
        try:
            st.metric("ATS score", f"{int(score)} / 100" if score is not None else "—")
        except (TypeError, ValueError):
            st.metric("ATS score", str(score) if score is not None else "—")

    if "Summary" in data:
        st.markdown("**Summary**")
        summary = (data.get("Summary") or "").strip()
        st.write(summary if summary else "—")

    if "Resume_Health" in data:
        rh = data.get("Resume_Health")
        st.markdown("**Resume health**")
        if isinstance(rh, dict) and rh:
            cols = st.columns(min(len(rh), 5) or 1)
            for i, (k, v) in enumerate(rh.items()):
                cols[i % len(cols)].metric(str(k).replace("_", " "), str(v))
        elif rh:
            st.write(rh)
        else:
            st.caption("—")

    if "Score_Breakdown" in data:
        bd = data.get("Score_Breakdown")
        st.markdown("**Score breakdown**")
        if isinstance(bd, dict) and bd:
            keys = list(bd.keys())
            n = len(keys)
            cols = st.columns(min(n, 6) or 1)
            for i, k in enumerate(keys):
                cols[i % len(cols)].metric(str(k), _pct(bd.get(k)))
        else:
            st.caption("—")

    if "Achievements_or_Certifications" in data:
        st.markdown("**Achievements / certifications**")
        ach = data.get("Achievements_or_Certifications") or []
        if ach:
            for line in ach:
                st.markdown(f"- {line}")
        else:
            st.caption("—")

    if "Resume_Strength" in data:
        st.markdown("**Resume strengths**")
        rs = data.get("Resume_Strength") or []
        if rs:
            for line in rs:
                st.markdown(f"- {line}")
        else:
            st.caption("—")

    if "Key_Skills" in data:
        st.markdown("**Key skills**")
        ks = data.get("Key_Skills") or []
        st.write(", ".join(str(x) for x in ks) if ks else "—")

    if "Suggestions_for_Improvement" in data:
        st.markdown("**Suggestions for improvement**")
        sug = data.get("Suggestions_for_Improvement") or []
        if sug:
            for line in sug:
                st.markdown(f"- {line}")
        else:
            st.caption("—")

    if "Missing_Keywords" in data:
        st.markdown("**Missing keywords**")
        mk = data.get("Missing_Keywords") or []
        if mk:
            for line in mk:
                st.markdown(f"- {line}")
        else:
            st.caption("—")

    if "Repeated_Word_Frequency" in data:
        st.markdown("**Repeated word frequency**")
        rwf = data.get("Repeated_Word_Frequency")
        if isinstance(rwf, dict):
            st.caption("Word → count (stylistic repetition).")
            st.json(rwf if rwf else {})
        elif rwf is not None:
            st.write(rwf)
        else:
            st.caption("—")

    if "Word_Replacement_Suggestions" in data:
        st.markdown("**Word replacement suggestions**")
        wrs = data.get("Word_Replacement_Suggestions") or []
        if wrs:
            for block in wrs:
                st.markdown(str(block).replace("\n", "\n\n"))
        else:
            st.caption("—")

    # Any other top-level fields (forward-compatible)
    extra = {k: v for k, v in data.items() if k not in set(_RESPONSE_FIELD_NAMES)}
    if extra:
        st.markdown("**Additional fields**")
        st.json(extra)

    with st.expander("Raw JSON (full response)"):
        st.json(data)


st.set_page_config(page_title="Jobra.ai · ATS", page_icon="📄", layout="centered")

st.title("Jobra.ai · ATS score")
st.caption(
    "Upload your resume, choose how to analyze it, then run **Analyze**. "
    "**With JD** and **With role** use the role catalog; **Resume only** calls the general path (no role/JD), "
    "including optional `without_jd` engines."
)

if "api_base" not in st.session_state:
    st.session_state.api_base = DEFAULT_API

with st.sidebar:
    api_base = st.text_input("API URL", key="api_base").rstrip("/")
    st.divider()
    st.subheader("Activity")
    lr = st.session_state.get("last_run")
    if lr:
        st.code(lr.get("one_liner", ""), language="http")
        st.caption(lr.get("detail", ""))
    else:
        st.caption("No request yet — upload a resume and run Analyze.")

uploaded_file = st.file_uploader("Resume (PDF or DOCX)", type=["pdf", "docx"])

mode = st.radio(
    "How should we analyze your resume?",
    options=[
        "with_jd",
        "with_role",
        "resume_only",
    ],
    format_func=lambda x: {
        "with_jd": "With job description — paste JD, get ATS score (`/analyse/with-jd`)",
        "with_role": "With role — pick a catalog role, get ATS score (`/analyse/with-role`)",
        "resume_only": "Resume only — no JD or role (`/analyse/general`, without-JD engines)",
    }[x],
    horizontal=False,
)

role_options = _roles_options()
labels = ["—"] + [x[0] for x in role_options]
id_by_label = {"—": ""} | {x[0]: x[1] for x in role_options}

job_description = ""
additional_context = ""
role_id = ""
wjd_engine = "default"

if mode in ("with_jd", "with_role"):
    st.subheader("Role")
    st.caption("Pick the catalog role used for matching (required for this mode).")
    role_pick = st.selectbox(
        "Job role",
        labels,
        help="Roles from the service catalog. Scroll the list to find yours.",
        key="role_select",
    )
    role_id = id_by_label.get(role_pick, "")

if mode == "with_jd":
    st.subheader("Job description")
    job_description = st.text_area(
        "Paste the job description",
        height=160,
        placeholder="Required for this mode — full JD text improves ATS alignment.",
        key="jd_text",
    )
    additional_context = st.text_area(
        "Extra context (optional)",
        height=80,
        placeholder="Projects, tools, notes…",
        key="jd_extra",
    )

if mode == "with_role":
    st.caption("Optional JD uses the same scoring depth as **With JD** when provided.")
    job_description = st.text_area(
        "Job description (optional)",
        height=120,
        placeholder="Leave empty for role-only scoring; paste a JD to align like With JD.",
        key="role_jd",
    )
    additional_context = st.text_area(
        "Extra context (optional)",
        height=80,
        placeholder="Projects, tools, notes…",
        key="role_extra",
    )

if mode == "resume_only":
    st.subheader("ATS engine (general / without-JD)")
    wjd_engine = st.selectbox(
        "Engine",
        ["default", "pure_llm", "hybrid"],
        index=0,
        format_func=lambda x: {
            "default": "Default — OpenAI Responses API",
            "pure_llm": "Pure LLM — services.without_jd.llm",
            "hybrid": "Hybrid — services.without_jd.hybrid",
        }[x],
        help="Used only for **Resume only** → `POST /analyse/general`.",
    )

st.divider()
analyze = st.button("Analyze", type="primary", use_container_width=True)

if not analyze:
    st.stop()

if uploaded_file is None:
    st.error("Upload a resume first.")
    st.stop()

base = api_base
files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
fn = uploaded_file.name

try:
    if mode == "resume_only":
        mode_label = "general"
        endpoint = f"{base}/analyse/general"
        lines = [
            "**Mode:** resume only (no role, no JD)",
            f"**Engine:** `{wjd_engine}`",
            f"**File:** `{fn}`",
        ]
        r = _post_file(
            endpoint,
            files,
            {"without_jd_engine": wjd_engine},
            "Processing: general ATS…",
            lines,
        )

    elif mode == "with_role":
        if not (role_id or "").strip():
            st.error("Choose a **Job role** (not “—”).")
            st.stop()
        mode_label = "with-role"
        endpoint = f"{base}/analyse/with-role"
        jd = (job_description or "").strip()
        lines = [
            "**Mode:** with role",
            f"**Role id:** `{role_id}`",
            f"**JD:** {'yes (' + str(len(jd)) + ' chars)' if jd else 'no'}",
            f"**Extra context:** {'yes' if (additional_context or '').strip() else 'no'}",
            f"**File:** `{fn}`",
        ]
        r = _post_file(
            endpoint,
            files,
            {
                "role": role_id,
                "job_description": jd,
                "additional_context": additional_context or "",
            },
            "Processing: with role…",
            lines,
        )

    else:
        if not (role_id or "").strip():
            st.error("Choose a **Job role** for With JD.")
            st.stop()
        if not (job_description or "").strip():
            st.error("Add a **Job description** for With JD.")
            st.stop()
        mode_label = "with-jd"
        endpoint = f"{base}/analyse/with-jd"
        lines = [
            "**Mode:** with JD",
            f"**Role id:** `{role_id}`",
            f"**JD length:** {len(job_description)} characters",
            f"**File:** `{fn}`",
        ]
        r = _post_file(
            endpoint,
            files,
            {
                "role": role_id,
                "job_description": job_description,
                "additional_context": additional_context or "",
            },
            "Processing: with JD…",
            lines,
        )
except requests.RequestException as exc:
    st.error(str(exc))
    st.stop()

with st.container(border=True):
    st.markdown("**Last request**")
    st.code(f"POST {endpoint}\n→ HTTP {r.status_code}", language="http")
    bits = [f"mode `{mode_label}`", f"file `{fn}`"]
    if mode_label == "general":
        bits.append(f"engine `{wjd_engine}`")
    if role_id:
        bits.append(f"role `{role_id}`")
    st.caption(" · ".join(bits))

host_path = endpoint.split("://", 1)[-1] if "://" in endpoint else endpoint
st.session_state["last_run"] = {
    "one_liner": f"POST {host_path}  {r.status_code}",
    "detail": " · ".join(bits),
}

if r.status_code >= 400:
    st.error(f"{r.status_code}: {r.text[:1500]}")
    st.stop()

data = r.json()

if mode_label == "general":
    st.caption(f"Engine: **{wjd_engine}** (without-JD path on the API).")

st.download_button(
    "Download JSON",
    json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"),
    file_name=f"ats-{mode_label}.json",
    mime="application/json",
)

_render_analysis_result(data)
