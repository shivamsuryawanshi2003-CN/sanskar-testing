from __future__ import annotations

import json
import math
import re
import time
from copy import deepcopy
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

from talent_intelligence.services.llm_shared.common import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
    _chat_completions_create_with_retry,
    _extract_response_text,
    enforce_min_llm_latency,
    openai_key_available,
)

NON_RESUME_MESSAGE = "The uploaded document does not look like a complete resume because core ATS sections are missing."


def _ensure_list(items: list[str], *, fallback: str) -> list[str]:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    return cleaned or [fallback]


def _extract_target_keywords(job_description: str, role: str) -> list[str]:
    pool = f"{role or ''}\n{job_description or ''}".lower()
    raw_tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+.#/-]{2,}", pool)
    stop = {
        "with", "that", "this", "from", "into", "your", "have", "will", "team", "work", "years",
        "year", "must", "nice", "good", "ability", "strong", "using", "build", "design", "their",
        "about", "they", "them", "role", "job", "description", "required", "preferred", "experience",
        "skills", "skill", "responsibilities", "responsibility", "support", "across", "including", "within",
        "can", "candidate", "candidates", "clearly", "deliver", "results", "ideal", "demonstrates",
        "measurable", "impact", "execution", "documentation", "habits", "prior", "roles", "consistent",
    }
    ranked: dict[str, int] = {}
    for token in raw_tokens:
        if token in stop or len(token) < 3:
            continue
        ranked[token] = ranked.get(token, 0) + 1
    return [token for token, _ in sorted(ranked.items(), key=lambda item: (-item[1], item[0]))[:18]]


def _estimate_alignment(analysis: dict[str, Any], resume_text: str, mode: str, role: str = "", job_description: str = "") -> dict[str, Any]:
    lower_resume = (resume_text or "").lower()
    target_keywords = _extract_target_keywords(job_description, role)
    matched_keywords = [kw for kw in target_keywords if kw in lower_resume]
    match_ratio = round((len(matched_keywords) / len(target_keywords)) * 100) if target_keywords else 0
    base_breakdown = analysis.get("Score_Breakdown") or {}
    resume_health = analysis.get("Resume_Health") or {}
    return {
        "target_keywords": target_keywords,
        "matched_keywords": matched_keywords,
        "missing_keywords": [kw for kw in target_keywords if kw not in lower_resume][:12],
        "keyword_match_ratio": match_ratio,
        "mode": mode,
        "base_breakdown": base_breakdown,
        "resume_health": resume_health,
        "base_score": int(analysis.get("ATS_Score", 0) or 0),
    }


def _deterministic_sections(*, analysis: dict[str, Any], mode: str, role: str = "", job_description: str = "") -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    score = int(analysis.get("ATS_Score", 0) or 0)
    breakdown = analysis.get("Score_Breakdown") or {}
    resume_health = analysis.get("Resume_Health") or {}
    suggestions = [str(x).strip() for x in (analysis.get("Suggestions_for_Improvement") or []) if str(x).strip()]
    strengths = [str(x).strip() for x in (analysis.get("Resume_Strength") or []) if str(x).strip()]
    raw_missing = analysis.get("Missing_Keyword_List")
    if not isinstance(raw_missing, list):
        raw_missing = analysis.get("Missing_Keywords") if isinstance(analysis.get("Missing_Keywords"), list) else []
    missing = [str(x).strip() for x in raw_missing if str(x).strip()]
    skills = [str(x).strip() for x in (analysis.get("Key_Skills") or []) if str(x).strip()]
    achievements = [str(x).strip() for x in (analysis.get("Achievements_or_Certifications") or []) if str(x).strip()]

    context_line = "General ATS review without a target job context was used."
    if mode == "role" and role.strip():
        context_line = f"Target alignment was measured against the selected role: {role.strip()}."
    elif mode == "jd":
        jd_words = len((job_description or "").split())
        context_line = f"Target alignment was measured against the pasted job description with {jd_words} words of context."

    detailed = {
        "Executive_Snapshot": _ensure_list([
            f"ATS score is {score} out of 100 on the current scoring scale.",
            context_line,
            f"Top strengths: {', '.join(strengths[:3])}." if strengths else "The resume has enough structure to support ATS analysis.",
        ], fallback="ATS evaluation completed."),
        "Parser_and_Format_Risk": _ensure_list([
            f"Content depth rating is {resume_health.get('Content_Percent', 0)} out of 100.",
            f"ATS parse status: {resume_health.get('ATS_Parse_Rate', 'No issues')}.",
            f"Format score: {breakdown.get('FORMAT', 0)} out of 100.",
        ], fallback="Formatting review completed."),
        "Keyword_and_Skills_Coverage": _ensure_list([
            f"Detected core skills: {', '.join(skills[:8])}." if skills else "Only a limited technical skill footprint was detected.",
            missing[0] if missing else "No major keyword gap line was generated.",
            missing[1] if len(missing) > 1 else "Experience keyword coverage can still be improved.",
        ], fallback="Keyword review completed."),
        "Experience_and_Impact": _ensure_list([
            f"Experience score: {breakdown.get('EXPERIENCE', 0)} out of 100.",
            achievements[0] if achievements else "Add one or two quantified outcomes to strengthen recruiter confidence.",
            suggestions[0] if suggestions else "Rewrite key bullets using action, tool, scope, and measurable result.",
        ], fallback="Experience review completed."),
        "Scoring_Weightage": _ensure_list([
            "The final ATS score is calibrated across format quality, skill alignment, evidence in experience, and education completeness.",
            "In targeted modes, keyword-to-evidence alignment should influence the score more strongly than surface-level formatting.",
        ], fallback="Scoring calibration completed."),
    }

    roadmap = {
        "Top_Priority": _ensure_list(suggestions[:3], fallback="Add clearer ATS-friendly section headings and stronger bullet phrasing."),
        "Next_Level_Improvements": _ensure_list(missing[:3], fallback="Add more role-specific and evidence-backed keywords in summary, skills, and experience."),
        "Future_Suggestion_Roots": _ensure_list([
            "bullet_rewrites_ready",
            "keyword_injection_ready",
            "summary_retargeting_ready",
            "achievement_quantification_ready",
        ], fallback="suggestion_pipeline_ready"),
    }
    return detailed, roadmap


def _normalize_sections_payload(raw: object) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    if not isinstance(raw, dict):
        raise ValueError("Detailed analysis payload must be a JSON object.")
    detailed = raw.get("Detailed_Analysis") or {}
    roadmap = raw.get("Improvement_Roadmap") or {}
    if not isinstance(detailed, dict) or not isinstance(roadmap, dict):
        raise ValueError("Detailed analysis or roadmap is malformed.")

    def _normalize_map(mapping: dict[str, Any]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for key, value in mapping.items():
            if isinstance(value, list):
                out[str(key)] = [str(x).strip() for x in value if str(x).strip()]
            elif value is None:
                out[str(key)] = []
            else:
                text = str(value).strip()
                out[str(key)] = [text] if text else []
        return out

    return _normalize_map(detailed), _normalize_map(roadmap)


def _clamp(value: Any, lo: int, hi: int, fallback: int) -> int:
    try:
        return max(lo, min(hi, int(round(float(value)))))
    except Exception:
        return fallback


def _smart_format_ceiling(base_analysis: dict[str, Any], resume_text: str, candidate_format: int) -> int:
    resume_health = base_analysis.get("Resume_Health") or {}
    parse_rate = str(resume_health.get("ATS_Parse_Rate", "")).lower()
    quant_rate = str(resume_health.get("Quantifying_Impact", "")).lower()
    line_count = len([line for line in (resume_text or "").splitlines() if line.strip()])
    issue_markers = sum(1 for phrase in (parse_rate, quant_rate) if phrase and phrase != "no issues")
    dynamic_ceiling = 96
    if issue_markers:
        dynamic_ceiling -= 6 * issue_markers
    if line_count < 14:
        dynamic_ceiling -= 8
    if len(resume_text.split()) < 220:
        dynamic_ceiling -= 6
    return min(candidate_format, max(48, dynamic_ceiling))


def _normalize_payload(candidate: object, base: dict[str, Any], mode: str, resume_text: str) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("Enhanced analysis payload must be a JSON object.")
    merged = deepcopy(base)
    base_score = int(base.get("ATS_Score", 0) or 0)
    merged["ATS_Score"] = _clamp(candidate.get("ATS_Score", base_score), 0, 100, base_score)

    summary = str(candidate.get("Summary", base.get("Summary", ""))).strip()
    if summary:
        merged["Summary"] = summary.replace("% / 100", " out of 100")

    for key in ("Suggestions_for_Improvement", "Achievements_or_Certifications", "Resume_Strength", "Key_Skills", "Word_Replacement_Suggestions"):
        val = candidate.get(key)
        if isinstance(val, list):
            merged[key] = [str(x).strip() for x in val if str(x).strip()]
    if isinstance(candidate.get("Missing_Keywords"), dict):
        merged["Missing_Keywords"] = candidate.get("Missing_Keywords")
    elif isinstance(candidate.get("Missing_Keywords"), list):
        merged["Missing_Keywords"] = candidate.get("Missing_Keywords")
    if isinstance(candidate.get("Missing_Keyword_List"), list):
        merged["Missing_Keyword_List"] = [str(x).strip() for x in candidate.get("Missing_Keyword_List") if str(x).strip()]

    repeated = candidate.get("Repeated_Word_Frequency")
    if isinstance(repeated, dict):
        cleaned = {}
        for k, v in repeated.items():
            try:
                cleaned[str(k).strip().lower()] = int(v)
            except Exception:
                pass
        merged["Repeated_Word_Frequency"] = cleaned

    score_breakdown = candidate.get("Score_Breakdown")
    if isinstance(score_breakdown, dict):
        normalized = {}
        base_bd = base.get("Score_Breakdown", {}) or {}
        for k in ("FORMAT", "SKILLS", "EXPERIENCE", "COMPLETENESS", "EDUCATION"):
            fallback = int(base_bd.get(k, 0) or 0)
            if k == "EDUCATION":
                continue
            normalized[k] = _clamp(score_breakdown.get(k, fallback), 0, 100, fallback)
        normalized["FORMAT"] = _smart_format_ceiling(base, resume_text, normalized.get("FORMAT", 0))
        merged["Score_Breakdown"] = normalized

    for key in ("Resume_Positioning", "Resume_Health_Label", "Overused_Keywords_Count"):
        if key in candidate:
            merged[key] = candidate.get(key)
    return merged


def _build_llm_messages(*, analysis: dict[str, Any], resume_text: str, mode: str, role: str, job_description: str) -> tuple[str, str]:
    target_evidence = _estimate_alignment(analysis, resume_text, mode, role=role, job_description=job_description)
    task_map = {
        "general": "Generate a recruiter-grade ATS assessment for the resume alone.",
        "role": "Compare the resume against the selected role and generate a targeted ATS assessment.",
        "jd": "Compare the resume against the pasted job description and generate a strict targeted ATS assessment.",
    }
    system = (
        "You are the primary ATS scoring and resume analysis engine for a paid product. "
        "Generate the final response directly, not a light polish of the deterministic evidence. "
        "Use the deterministic analysis as supporting evidence and confidence checks, but make your own judgment. "
        "In targeted modes, compare the resume against the selected role or pasted JD and reflect that comparison throughout the score, summary, section analysis, and improvement roadmap. "
        "Do not inflate formatting simply because the file is readable. Strong formatting requires clean structure, recruiter readability, and evidence-backed content. "
        "Do not invent any skills, projects, employers, degrees, certifications, or quantified results. "
        "Avoid percent signs in prose; write 'out of 100'. Return valid JSON only."
    )
    response_contract = {
        "ATS_Score": 0,
        "Resume_Positioning": "Competitive | Promising | Developing | Needs Improvement",
        "Resume_Health_Label": "Excellent | Strong | Moderate | Weak | Critical",
        "Summary": "string",
        "Suggestions_for_Improvement": ["string"],
        "Score_Breakdown": {"FORMAT": "0%", "SKILLS": "0%", "EXPERIENCE": "0%", "COMPLETENESS": "0%"},
        "Missing_Keywords": {"SUMMARY": 0, "SKILLS": 0, "EXPERIENCE": 0, "PROJECTS": 0},
        "Missing_Keyword_List": ["string"],
        "Achievements_or_Certifications": ["string"],
        "Resume_Strength": ["string"],
        "Key_Skills": ["string"],
        "Overused_Keywords_Count": 0,
        "Repeated_Word_Frequency": {"string": 0},
        "Word_Replacement_Suggestions": ["string"]
    }
    body = {
        "task": task_map[mode],
        "mode": mode,
        "resume_text": resume_text[:12000],
        "role": role,
        "job_description": job_description[:8000],
        "deterministic_evidence": analysis,
        "target_alignment_evidence": target_evidence,
        "instructions": [
            "Generate the final ATS score yourself using the comparison evidence and resume evidence together.",
            "Assign category scores based on actual evidence strength, not on default assumptions.",
            "If the resume mentions keywords without proof in bullets or projects, keep the score conservative.",
            "Use the exact response contract shape and no extra top-level keys.",
            "In JD and role modes, ATS score and Summary must explicitly reflect the comparison target, matched evidence, missing evidence, and proof quality.",
            "Resume_Health_Label must reflect overall quality, completeness, parser safety, and evidence quality rather than ATS score alone.",
            "Score_Breakdown must use FORMAT, SKILLS, EXPERIENCE, and COMPLETENESS only, with percentage strings like 78%.",
            "Missing_Keywords must be an object with SUMMARY, SKILLS, EXPERIENCE, and PROJECTS integer counts.",
            "Missing_Keyword_List should contain the actual missing target terms when targeted analysis is used.",
            "The Summary should sound like an industry ATS review, concise but clear.",
            "The response should be meaningfully different between general, role, and JD modes when the same resume is scored.",
        ],
        "response_contract": response_contract,
    }
    return system, json.dumps(body, ensure_ascii=False)


def enhance_analysis_payload(*, analysis: dict[str, Any], resume_text: str, mode: str, role: str = "", job_description: str = "") -> dict[str, Any]:
    if str(analysis.get("Summary", "")).strip() == NON_RESUME_MESSAGE:
        return {
            "ATS_Score": 0,
            "Summary": NON_RESUME_MESSAGE,
            "Detailed_Analysis": {},
            "Improvement_Roadmap": {},
            "Resume_Health": analysis.get("Resume_Health") or {
                "Content_Percent": 0,
                "ATS_Parse_Rate": "3 issues",
                "Quantifying_Impact": "1 issue",
                "Repetition": "No issues",
                "Spelling_Grammar": "1 issue",
            },
            "Suggestions_for_Improvement": [],
            "Score_Breakdown": {"FORMAT": 0, "SKILLS": 0, "EXPERIENCE": 0, "EDUCATION": 0},
            "Missing_Keywords": [],
            "Missing_Keyword_List": [],
            "Achievements_or_Certifications": [],
            "Resume_Strength": [],
            "Key_Skills": [],
            "Repeated_Word_Frequency": {},
            "Word_Replacement_Suggestions": [],
        }

    fallback = deepcopy(analysis)
    detailed, roadmap = _deterministic_sections(analysis=analysis, mode=mode, role=role, job_description=job_description)
    fallback["Detailed_Analysis"] = detailed
    fallback["Improvement_Roadmap"] = roadmap

    if not openai_key_available() or OpenAI is None:
        return fallback

    system_message, user_message = _build_llm_messages(analysis=analysis, resume_text=resume_text, mode=mode, role=role, job_description=job_description)
    llm_start = time.perf_counter()
    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, timeout=OPENAI_TIMEOUT_SECONDS)
        response = _chat_completions_create_with_retry(
            client=client,
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2600,
            response_format={"type": "json_object"},
        )
        text = _extract_response_text(response)
        parsed = json.loads(text)
        enforce_min_llm_latency(llm_start)
        return _normalize_payload(parsed, fallback, mode, resume_text)
    except Exception:
        enforce_min_llm_latency(llm_start)
        return fallback


def build_hybrid_sections(*, analysis: dict[str, Any], resume_text: str, mode: str, role: str = "", job_description: str = "") -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    detailed = analysis.get("Detailed_Analysis") or {}
    roadmap = analysis.get("Improvement_Roadmap") or {}
    if detailed or roadmap:
        return detailed, roadmap
    payload = enhance_analysis_payload(analysis=analysis, resume_text=resume_text, mode=mode, role=role, job_description=job_description)
    return payload.get("Detailed_Analysis") or {}, payload.get("Improvement_Roadmap") or {}
