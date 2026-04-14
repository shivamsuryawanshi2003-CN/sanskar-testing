# AI assisted development
from talent_intelligence.config.roles import role_config
from talent_intelligence.schemas.analysis import AnalyzeRequest, AnalyzeResponse, ResumeHealthStrip
from talent_intelligence.services.llm_service import llm_with_jd_full_analysis, llm_with_role_full_analysis
from talent_intelligence.services.resume_intake import require_valid_resume_text


def _coerce_repeated_word_frequency(raw: object) -> dict[str, int]:
    """Normalize API quirks only (dict vs list shapes); counts come from the model."""
    if raw is None:
        return {}
    if isinstance(raw, dict):
        out: dict[str, int] = {}
        for k, v in raw.items():
            try:
                out[str(k).strip()] = int(v)
            except (TypeError, ValueError):
                continue
        return out
    if isinstance(raw, list):
        out: dict[str, int] = {}
        for item in raw:
            if isinstance(item, dict):
                w = item.get("word") or item.get("Word")
                c = item.get("count") or item.get("Count") or item.get("frequency")
                if w is not None and c is not None:
                    try:
                        out[str(w).strip()] = int(c)
                    except (TypeError, ValueError):
                        pass
                else:
                    for k, v in item.items():
                        try:
                            out[str(k).strip()] = int(v)
                        except (TypeError, ValueError):
                            pass
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    out[str(item[0]).strip()] = int(item[1])
                except (TypeError, ValueError):
                    pass
        return out
    return {}


def parse_resume_health(raw: object, *, content_fallback: int) -> ResumeHealthStrip:
    """Map LLM Resume_Health; clamp Content_Percent; use ATS score only if Content_Percent missing."""
    fb = max(0, min(100, int(content_fallback)))
    if not isinstance(raw, dict):
        return ResumeHealthStrip(
            Content_Percent=fb,
            ATS_Parse_Rate="No issues",
            Quantifying_Impact="No issues",
            Repetition="No issues",
            Spelling_Grammar="No issues",
        )

    def _s(key: str, default: str = "No issues") -> str:
        v = raw.get(key)
        if v is None:
            return default
        t = str(v).strip()
        return t if t else default

    cp = raw.get("Content_Percent")
    try:
        content_pct = int(cp) if cp is not None else fb
    except (TypeError, ValueError):
        content_pct = fb
    content_pct = max(0, min(100, content_pct))

    return ResumeHealthStrip(
        Content_Percent=content_pct,
        ATS_Parse_Rate=_s("ATS_Parse_Rate"),
        Quantifying_Impact=_s("Quantifying_Impact"),
        Repetition=_s("Repetition"),
        Spelling_Grammar=_s("Spelling_Grammar"),
    )


def analyze_resume(payload: AnalyzeRequest) -> AnalyzeResponse:
    require_valid_resume_text(payload.resume_text)
    cfg = role_config(payload.role)
    combined_resume_text = payload.resume_text
    if payload.additional_context.strip():
        combined_resume_text = f"{payload.resume_text}\n\nAdditional Context:\n{payload.additional_context.strip()}"

    if payload.job_description.strip():
        llm_full = llm_with_jd_full_analysis(
            resume_text=combined_resume_text,
            role=cfg["title"],
            role_summary=cfg["jd"],
            job_description=payload.job_description,
            additional_context=payload.additional_context,
            role_keywords=cfg["skills"],
        )
    else:
        llm_full = llm_with_role_full_analysis(
            resume_text=combined_resume_text,
            role=cfg["title"],
            role_summary=cfg["jd"],
            additional_context=payload.additional_context,
            role_keywords=cfg["skills"],
        )

    breakdown = llm_full.get("Score_Breakdown", {}) or {}
    ats_score = int(llm_full.get("ATS_Score", 0))
    resume_health = parse_resume_health(llm_full.get("Resume_Health"), content_fallback=ats_score)

    suggestions = [str(x).strip() for x in llm_full.get("Suggestions_for_Improvement", []) if str(x).strip()]
    missing_kw = [str(x).strip() for x in llm_full.get("Missing_Keywords", []) if str(x).strip()]

    key_skills = [str(x).strip() for x in llm_full.get("Key_Skills", []) if str(x).strip()]

    repeated_norm = _coerce_repeated_word_frequency(llm_full.get("Repeated_Word_Frequency"))

    word_repl = [str(x).strip() for x in llm_full.get("Word_Replacement_Suggestions", []) if str(x).strip()]

    return AnalyzeResponse(
        ATS_Score=ats_score,
        Summary=str(llm_full.get("Summary", "")).strip(),
        Resume_Health=resume_health,
        Suggestions_for_Improvement=suggestions,
        Score_Breakdown={
            "FORMAT": int(breakdown.get("FORMAT", 0)),
            "SKILLS": int(breakdown.get("SKILLS", 0)),
            "EXPERIENCE": int(breakdown.get("EXPERIENCE", 0)),
            "EDUCATION": int(breakdown.get("EDUCATION", 0)),
        },
        Missing_Keywords=missing_kw,
        Achievements_or_Certifications=[
            str(x).strip() for x in llm_full.get("Achievements_or_Certifications", []) if str(x).strip()
        ],
        Resume_Strength=[str(x).strip() for x in llm_full.get("Resume_Strength", []) if str(x).strip()],
        Key_Skills=key_skills,
        Repeated_Word_Frequency={str(k).strip().lower(): int(v) for k, v in repeated_norm.items()},
        Word_Replacement_Suggestions=word_repl,
    )
