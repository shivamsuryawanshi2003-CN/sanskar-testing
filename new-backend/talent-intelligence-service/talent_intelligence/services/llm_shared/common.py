# AI assisted development
"""Shared OpenAI client helpers, response normalization, and ancillary LLM entrypoints."""

import json
import os
import re
import time

from dotenv import load_dotenv
from openai import OpenAI

from .prompt import PROMPT_BATCH_INSIGHTS_JSON

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or ""
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_TIMEOUT_SECONDS = 300

# OPENAI_MODE / OPENAI_MODEL must be the model id string (e.g. gpt-4o-mini). If unset or invalid,
# the API returns 400: "Invalid type for 'model': expected a string, but got an object instead."
_DEFAULT_OPENAI_MODEL = "gpt-5-nano"


def _resolve_openai_model_name() -> str:
    raw = os.getenv("OPENAI_MODE") or os.getenv("OPENAI_MODEL")
    if raw is None:
        return _DEFAULT_OPENAI_MODEL
    if not isinstance(raw, str):
        if isinstance(raw, dict):
            for key in ("model", "id", "name", "deployment"):
                v = raw.get(key)
                if v is not None and str(v).strip():
                    return str(v).strip()
        return str(raw).strip() or _DEFAULT_OPENAI_MODEL
    s = raw.strip()
    if not s:
        return _DEFAULT_OPENAI_MODEL
    if s.startswith("{") and s.endswith("}"):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                for key in ("model", "id", "name", "deployment"):
                    v = parsed.get(key)
                    if v is not None and str(v).strip():
                        return str(v).strip()
        except json.JSONDecodeError:
            pass
    return s


OPENAI_MODEL = _resolve_openai_model_name()


def _extract_retry_seconds_from_error(err_text: str) -> float:
    match = re.search(r"try again in\s+(\d+)\s*s", err_text.lower())
    if match:
        return float(match.group(1))
    return 0.0


def _responses_create_with_retry(
    *,
    client: OpenAI,
    model: str | object,
    input_payload: list[dict] | str,
    store: bool = False,
    max_retries: int = 4,
):
    if isinstance(model, str) and model.strip():
        model_name = model.strip()
    else:
        model_name = _resolve_openai_model_name()
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return client.responses.create(
                model=model_name,
                input=input_payload,
                store=store,
            )
        except Exception as exc:
            last_exc = exc
            message = str(exc)
            is_rate_limit = ("429" in message) or ("rate limit" in message.lower())
            if (not is_rate_limit) or (attempt >= max_retries):
                break
            hinted_wait = _extract_retry_seconds_from_error(message)
            backoff_wait = float(2**attempt)
            time.sleep(max(hinted_wait, backoff_wait))
    raise ValueError(f"OpenAI request failed: {last_exc}") from last_exc


def _extract_response_text(response) -> str:
    text = (response.output_text or "").strip()
    if text:
        return text
    try:
        return str(response.output[0].content[0].text).strip()
    except Exception:
        return ""


def _parse_json_text(text: str) -> dict:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def _int_0_100(val: object, default: int = 0) -> int:
    if val is None:
        return default
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        try:
            return max(0, min(100, int(round(float(val)))))
        except (TypeError, ValueError):
            return default
    s = str(val).strip().rstrip("%")
    try:
        return max(0, min(100, int(round(float(s)))))
    except (TypeError, ValueError):
        return default


def _coerce_missing_keywords(val: object) -> list[str]:
    """Model may return a list of strings or a dict (SUMMARY/SKILLS/EXPERIENCE/PROJECTS)."""
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, dict):
        order = ("SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS")
        out: list[str] = []
        for k in order:
            if k in val and val[k] not in (None, "", 0):
                s = str(val[k]).strip()
                if s:
                    out.append(s)
        for k, v in val.items():
            if k in order:
                continue
            if v not in (None, "", 0):
                s = str(v).strip()
                if s and s not in out:
                    out.append(s)
        return out
    if val is None:
        return []
    s = str(val).strip()
    return [s] if s else []


def _normalize_full_analysis_payload(parsed: object) -> dict:
    """Fill missing keys when the model omits fields (e.g. Score_Breakdown)."""
    if not isinstance(parsed, dict):
        raise ValueError("OpenAI analysis payload is not a JSON object.")

    out = dict(parsed)
    ats = _int_0_100(out.get("ATS_Score"), 0)
    out["ATS_Score"] = ats
    out.setdefault("Summary", "")
    summ = out.get("Summary")
    if isinstance(summ, list):
        out["Summary"] = " ".join(str(x).strip() for x in summ if str(x).strip())
    elif not isinstance(summ, str):
        out["Summary"] = str(out.get("Summary", ""))

    rh = out.get("Resume_Health")
    if not isinstance(rh, dict):
        rh = {}
    rh.setdefault("Content_Percent", ats)
    rh["Content_Percent"] = _int_0_100(rh.get("Content_Percent"), ats)
    rh.setdefault("ATS_Parse_Rate", "No issues")
    rh.setdefault("Quantifying_Impact", "No issues")
    rh.setdefault("Repetition", "No issues")
    rh.setdefault("Spelling_Grammar", "No issues")
    for k in ("ATS_Parse_Rate", "Quantifying_Impact", "Repetition", "Spelling_Grammar"):
        if not str(rh.get(k, "")).strip():
            rh[k] = "No issues"
    out["Resume_Health"] = rh

    out["Missing_Keywords"] = _coerce_missing_keywords(out.get("Missing_Keywords"))

    for list_key in (
        "Suggestions_for_Improvement",
        "Achievements_or_Certifications",
        "Resume_Strength",
        "Key_Skills",
        "Word_Replacement_Suggestions",
    ):
        v = out.get(list_key)
        if isinstance(v, list):
            out[list_key] = [str(x).strip() for x in v if str(x).strip()]
        elif v is None or (isinstance(v, str) and not str(v).strip()):
            out[list_key] = []
        else:
            out[list_key] = [str(v).strip()]

    sb = out.get("Score_Breakdown")
    if not isinstance(sb, dict):
        sb = {}
    edu_src = sb.get("EDUCATION")
    if edu_src is None:
        edu_src = sb.get("COMPLETENESS")
    out["Score_Breakdown"] = {
        "FORMAT": _int_0_100(sb.get("FORMAT"), 0),
        "SKILLS": _int_0_100(sb.get("SKILLS"), 0),
        "EXPERIENCE": _int_0_100(sb.get("EXPERIENCE"), 0),
        "EDUCATION": _int_0_100(edu_src, 0),
    }

    rw = out.get("Repeated_Word_Frequency")
    if not isinstance(rw, dict):
        out["Repeated_Word_Frequency"] = {}
    else:
        clean: dict[str, int] = {}
        for k, v in rw.items():
            try:
                clean[str(k).strip()] = int(v)
            except (TypeError, ValueError):
                continue
        out["Repeated_Word_Frequency"] = clean

    return out


def _normalize_general_ats_payload(parsed: object) -> dict:
    """Fill missing keys for llm_general_score_only responses."""
    if not isinstance(parsed, dict):
        raise ValueError("OpenAI general ATS payload is not a JSON object.")

    out = dict(parsed)
    ats = _int_0_100(out.get("ATS_Score"), 0)
    out["ATS_Score"] = ats
    out.setdefault("Summary", "")
    summ = out.get("Summary")
    if isinstance(summ, list):
        out["Summary"] = " ".join(str(x).strip() for x in summ if str(x).strip())
    elif not isinstance(summ, str):
        out["Summary"] = str(out.get("Summary", ""))

    rh = out.get("Resume_Health")
    if not isinstance(rh, dict):
        rh = {}
    rh.setdefault("Content_Percent", ats)
    rh["Content_Percent"] = _int_0_100(rh.get("Content_Percent"), ats)
    rh.setdefault("ATS_Parse_Rate", "No issues")
    rh.setdefault("Quantifying_Impact", "No issues")
    rh.setdefault("Repetition", "No issues")
    rh.setdefault("Spelling_Grammar", "No issues")
    for k in ("ATS_Parse_Rate", "Quantifying_Impact", "Repetition", "Spelling_Grammar"):
        if not str(rh.get(k, "")).strip():
            rh[k] = "No issues"
    out["Resume_Health"] = rh

    out["Missing_Keywords"] = _coerce_missing_keywords(out.get("Missing_Keywords"))

    for list_key in (
        "Suggestions_for_Improvement",
        "Achievements_or_Certifications",
        "Resume_Strength",
        "Key_Skills",
        "Word_Replacement_Suggestions",
    ):
        v = out.get(list_key)
        if isinstance(v, list):
            out[list_key] = [str(x).strip() for x in v if str(x).strip()]
        elif v is None or (isinstance(v, str) and not str(v).strip()):
            out[list_key] = []
        else:
            out[list_key] = [str(v).strip()]

    sb = out.get("Score_Breakdown")
    if not isinstance(sb, dict):
        sb = {}
    edu_src = sb.get("EDUCATION")
    if edu_src is None:
        edu_src = sb.get("COMPLETENESS")
    out["Score_Breakdown"] = {
        "FORMAT": _int_0_100(sb.get("FORMAT"), 0),
        "SKILLS": _int_0_100(sb.get("SKILLS"), 0),
        "EXPERIENCE": _int_0_100(sb.get("EXPERIENCE"), 0),
        "EDUCATION": _int_0_100(edu_src, 0),
    }

    rw = out.get("Repeated_Word_Frequency")
    if not isinstance(rw, dict):
        out["Repeated_Word_Frequency"] = {}
    else:
        clean_rw: dict[str, int] = {}
        for k, v in rw.items():
            try:
                clean_rw[str(k).strip()] = int(v)
            except (TypeError, ValueError):
                continue
        out["Repeated_Word_Frequency"] = clean_rw

    wr = out.get("Word_Replacement_Suggestions")
    if isinstance(wr, list):
        out["Word_Replacement_Suggestions"] = [str(x).strip() for x in wr if str(x).strip()]
    elif wr is None or (isinstance(wr, str) and not str(wr).strip()):
        out["Word_Replacement_Suggestions"] = []
    else:
        out["Word_Replacement_Suggestions"] = [str(wr).strip()]

    return out


def llm_batch_insights(
    *,
    resume_text: str,
    role: str,
    role_summary: str,
    job_description: str,
    additional_context: str,
    role_keywords: list[str],
    extracted_skills: list[str],
    job_history: list[str],
    missing_keywords: list[str],
    ats_score: int,
    ats_score_without_jd: int,
    ats_score_with_jd: int,
    score_breakdown: dict[str, int],
    repeated_words: dict[str, int],
) -> dict[str, list[str] | str]:
    if not OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is missing.")

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )
    job_history_text = " | ".join(job_history[:5]) if job_history else "none detected"
    skills_text = ", ".join(extracted_skills[:12]) if extracted_skills else "none detected"
    words_block = ", ".join([f"{w}({c}x)" for w, c in repeated_words.items()]) if repeated_words else "none"
    user_prompt = f"""
Role: {role}
Role Context/JD Blend: {role_summary}
Job Description: {job_description[:1200] if job_description else "not provided"}
Role Skills: {", ".join(role_keywords[:18])}
Extracted Skills: {skills_text}
Job History Signals: {job_history_text}
ATS Score: {ats_score}
ATS Score Without JD: {ats_score_without_jd}
ATS Score With JD: {ats_score_with_jd}
Score Breakdown: FORMAT={score_breakdown.get("FORMAT", 0)}, SKILLS={score_breakdown.get("SKILLS", 0)}, EXPERIENCE={score_breakdown.get("EXPERIENCE", 0)}, EDUCATION={score_breakdown.get("EDUCATION", 0)}
Missing Keywords: {", ".join(missing_keywords[:12]) if missing_keywords else "none"}
Repeated Words: {words_block}
Resume Text:
{resume_text[:2600]}
Additional Resume Context:
{additional_context[:1200] if additional_context else "not provided"}
""".strip()
    system_prompt = PROMPT_BATCH_INSIGHTS_JSON
    response = _responses_create_with_retry(
        client=client,
        model=OPENAI_MODEL,
        input_payload=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        store=False,
    )
    text = _extract_response_text(response)
    if not text:
        raise ValueError("OpenAI returned empty batch insight text.")

    try:
        parsed = _parse_json_text(text)
    except Exception as exc:
        raise ValueError(f"OpenAI returned non-JSON insight payload: {text[:220]}") from exc

    summary = " ".join(str(parsed.get("summary", "")).split())[:420]
    suggestions_raw = parsed.get("suggestions", [])
    suggestions = [str(ln).strip("-* ").strip() for ln in suggestions_raw if str(ln).strip()]
    suggestions = [ln for ln in suggestions if len(ln) >= 8][:8]

    replacements_raw = parsed.get("word_replacements", {}) or {}
    replacement_lines: list[str] = []
    for word, freq in repeated_words.items():
        value = str(replacements_raw.get(word, "")).strip()
        if value:
            replacement_lines.append(f"Replace repeated '{word}' ({freq}x) with: {value}")

    if not summary and not suggestions:
        raise ValueError("OpenAI batch insights payload was empty/invalid.")
    return {
        "summary": summary,
        "suggestions": suggestions,
        "word_replacements": replacement_lines,
    }


def llm_ping() -> dict[str, str]:
    if not OPENAI_API_KEY.strip():
        return {"status": "error", "message": "OPENAI_API_KEY is missing."}
    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            timeout=min(15.0, OPENAI_TIMEOUT_SECONDS),
        )
        response = _responses_create_with_retry(
            client=client,
            model=OPENAI_MODEL,
            input_payload="Reply with exactly: LLM_OK",
            store=False,
            max_retries=0,
        )
        text = _extract_response_text(response)
        return {"status": "ok", "message": text or "LLM responded without text"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def llm_policy() -> dict[str, str]:
    key_loaded = bool(OPENAI_API_KEY.strip())
    return {
        "llm_mode": "strict_no_fallback",
        "suggestions_source": "openai_responses_api_only",
        "hardcoded_suggestions": "disabled",
        "openai_key_loaded": "true" if key_loaded else "false",
        "model": OPENAI_MODEL,
    }
