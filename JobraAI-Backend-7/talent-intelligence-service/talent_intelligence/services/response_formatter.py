from __future__ import annotations

import re
from typing import Any

from talent_intelligence.schemas.analysis import AnalyzeResponse, ResumeHealthBlock

NON_RESUME_MESSAGE = "The uploaded document does not look like a complete resume because core ATS sections are missing."

_SECTION_KEYS = ("SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS")


def _extract_issue_count(value: object) -> int:
    text = str(value or "").strip().lower()
    if not text or text == "no issues":
        return 0
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else 1


def _normalize_score(value: object, fallback: int = 0) -> int:
    try:
        if isinstance(value, str):
            value = value.replace('%', '').strip()
        return max(0, min(100, int(round(float(value)))))
    except Exception:
        return max(0, min(100, int(fallback)))


def _safe_nonnegative_int(value: object, *, fallback: int) -> int:
    """Coerce LLM/heuristic quirks without raising (avoids 500 on /analyse/*)."""
    try:
        if value is None or value == "":
            return fallback
        return max(0, int(round(float(value))))
    except (TypeError, ValueError):
        return fallback


def _score_breakdown(raw: object, resume_health: dict[str, Any] | None = None) -> dict[str, str]:
    raw = raw if isinstance(raw, dict) else {}
    fmt = _normalize_score(raw.get('FORMAT', 0))
    skills = _normalize_score(raw.get('SKILLS', 0))
    experience = _normalize_score(raw.get('EXPERIENCE', 0))
    if 'COMPLETENESS' in raw:
        completeness = _normalize_score(raw.get('COMPLETENESS', 0))
    else:
        content_pct = _normalize_score((resume_health or {}).get('Content_Percent', 0))
        education = _normalize_score(raw.get('EDUCATION', content_pct), content_pct)
        completeness = _normalize_score(round((content_pct * 0.7) + (education * 0.3)))
    return {
        'FORMAT': f'{fmt}%',
        'SKILLS': f'{skills}%',
        'EXPERIENCE': f'{experience}%',
        'COMPLETENESS': f'{completeness}%',
    }


def _missing_keywords(raw: object) -> dict[str, int]:
    out = {k: 0 for k in _SECTION_KEYS}
    if isinstance(raw, dict):
        for key in _SECTION_KEYS:
            out[key] = _normalize_score(raw.get(key, 0))
        return out
    if isinstance(raw, list):
        for item in raw:
            text = str(item).strip()
            lower = text.lower()
            count = _extract_issue_count(text)
            if 'summary' in lower:
                out['SUMMARY'] = count
            elif 'skill' in lower:
                out['SKILLS'] = count
            elif 'project' in lower:
                out['PROJECTS'] = count
            elif 'experience' in lower or 'work experience' in lower:
                out['EXPERIENCE'] = count
        return out
    return out


def _missing_keyword_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item).strip() for item in raw if str(item).strip()]


def _resume_health_label(ats_score: int, breakdown: dict[str, str], resume_health: dict[str, Any]) -> str:
    fmt = _normalize_score(breakdown.get('FORMAT', 0))
    completeness = _normalize_score(breakdown.get('COMPLETENESS', 0))
    content = _normalize_score(resume_health.get('Content_Percent', 50), 50)
    parse_penalty = min(10, 1 * _extract_issue_count(resume_health.get('ATS_Parse_Rate')))
    impact_penalty = min(10, 1 * _extract_issue_count(resume_health.get('Quantifying_Impact')))
    repetition_penalty = min(5, 0.5 * _extract_issue_count(resume_health.get('Repetition')))
    spelling_penalty = min(10, 1 * _extract_issue_count(resume_health.get('Spelling_Grammar')))
    health_index = round((0.50 * ats_score) + (0.15 * fmt) + (0.20 * completeness) + (0.15 * content) - parse_penalty - impact_penalty - repetition_penalty - spelling_penalty)
    health_index = max(20 + int(0.3 * ats_score), health_index)
    # Direct ATS score based label as requested
    if ats_score >= 80:
        label = 'Excellent'
    elif ats_score >= 60:
        label = 'Strong'
    elif ats_score >= 40:
        label = 'Moderate'
    elif ats_score >= 20:
        label = 'Weak'
    else:
        label = 'Critical'
    return label


def _resume_positioning(ats_score: int) -> str:
    if ats_score >= 75:
        return 'Competitive'
    if ats_score >= 62:
        return 'Promising'
    if ats_score >= 48:
        return 'Developing'
    return 'Needs Improvement'


def _clean_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(x).strip() for x in raw if str(x).strip()]


def _repeated_words(raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        try:
            out[str(k).strip()] = int(v)
        except Exception:
            continue
    return out


def build_contract_response(payload: dict[str, Any]) -> AnalyzeResponse:
    summary = str(payload.get('Summary', '')).strip()
    if summary == NON_RESUME_MESSAGE:
        return AnalyzeResponse(
            ATS_Score=0,
            Resume_Positioning='Needs Improvement',
            Resume_Health_Label='Critical',
            Resume_Health=ResumeHealthBlock(
                Content_Percent=0,
                ATS_Parse_Rate='No issues',
                Quantifying_Impact='No issues',
                Repetition='No issues',
                Spelling_Grammar='No issues',
            ),
            Summary=NON_RESUME_MESSAGE,
            Suggestions_for_Improvement=[],
            Score_Breakdown={'FORMAT': '0%', 'SKILLS': '0%', 'EXPERIENCE': '0%', 'COMPLETENESS': '0%'},
            Missing_Keywords={k: 0 for k in _SECTION_KEYS},
            Missing_Keyword_List=[],
            Achievements_or_Certifications=[],
            Resume_Strength=[],
            Key_Skills=[],
            Overused_Keywords_Count=0,
            Repeated_Word_Frequency={},
            Word_Replacement_Suggestions=[],
        )

    ats = _normalize_score(payload.get('ATS_Score', 0))
    resume_health = payload.get('Resume_Health') if isinstance(payload.get('Resume_Health'), dict) else {}
    breakdown = _score_breakdown(payload.get('Score_Breakdown'), resume_health)
    repeated = _repeated_words(payload.get('Repeated_Word_Frequency'))
    computed_label = _resume_health_label(ats, breakdown, resume_health)
    if isinstance(resume_health, dict):
        try:
            health_block = ResumeHealthBlock.model_validate(resume_health)
        except Exception:
            fb = max(0, min(100, int(resume_health.get("Content_Percent", ats) or ats)))
            health_block = ResumeHealthBlock(Content_Percent=fb)
    else:
        health_block = ResumeHealthBlock(Content_Percent=max(0, min(100, ats)))
    return AnalyzeResponse(
        ATS_Score=ats,
        Resume_Positioning=str(payload.get('Resume_Positioning') or _resume_positioning(ats)).strip(),
        Resume_Health_Label=computed_label,
        Resume_Health=health_block,
        Summary=summary,
        Suggestions_for_Improvement=_clean_list(payload.get('Suggestions_for_Improvement')),
        Score_Breakdown=breakdown,
        Missing_Keywords=_missing_keywords(payload.get('Missing_Keywords')),
        Missing_Keyword_List=_missing_keyword_list(payload.get('Missing_Keyword_List')),
        Achievements_or_Certifications=_clean_list(payload.get('Achievements_or_Certifications')),
        Resume_Strength=_clean_list(payload.get('Resume_Strength')),
        Key_Skills=_clean_list(payload.get('Key_Skills')),
        Overused_Keywords_Count=_safe_nonnegative_int(
            payload.get("Overused_Keywords_Count"),
            fallback=len(repeated),
        ),
        Repeated_Word_Frequency=repeated,
        Word_Replacement_Suggestions=_clean_list(payload.get('Word_Replacement_Suggestions')),
    )
