
from talent_intelligence.config.roles import role_config
from talent_intelligence.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from talent_intelligence.services.llm_service import llm_with_jd_full_analysis, llm_with_role_full_analysis
from talent_intelligence.services.hybrid_analysis import enhance_analysis_payload
from talent_intelligence.services.response_formatter import build_contract_response


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


def parse_resume_health(raw: object, *, content_fallback: int) -> dict[str, object]:
    fb = max(0, min(100, int(content_fallback)))
    if not isinstance(raw, dict):
        return {
            "Content_Percent": fb,
            "ATS_Parse_Rate": "No issues",
            "Quantifying_Impact": "No issues",
            "Repetition": "No issues",
            "Spelling_Grammar": "No issues",
        }
    return {
        "Content_Percent": max(0, min(100, int(raw.get("Content_Percent", fb) or fb))),
        "ATS_Parse_Rate": str(raw.get("ATS_Parse_Rate", "No issues")).strip() or "No issues",
        "Quantifying_Impact": str(raw.get("Quantifying_Impact", "No issues")).strip() or "No issues",
        "Repetition": str(raw.get("Repetition", "No issues")).strip() or "No issues",
        "Spelling_Grammar": str(raw.get("Spelling_Grammar", "No issues")).strip() or "No issues",
    }


def analyze_resume(payload: AnalyzeRequest) -> AnalyzeResponse:
    combined_resume_text = payload.resume_text
    if payload.additional_context.strip():
        combined_resume_text = f"{payload.resume_text}\n\nAdditional Context:\n{payload.additional_context.strip()}"

    has_role = bool(payload.role.strip())
    has_jd = bool(payload.job_description.strip())

    if not has_role and not has_jd:
        raise ValueError("Either role or job_description is required for this analysis path.")

    if has_jd:
        llm_full = llm_with_jd_full_analysis(
            resume_text=combined_resume_text,
            job_description=payload.job_description,
            additional_context=payload.additional_context,
        )
    else:
        cfg = role_config(payload.role)
        llm_full = llm_with_role_full_analysis(
            resume_text=combined_resume_text,
            role=cfg["title"],
            role_summary=cfg["jd"],
            additional_context=payload.additional_context,
            role_keywords=cfg["skills"],
        )

    llm_full = enhance_analysis_payload(
        analysis=llm_full,
        resume_text=combined_resume_text,
        mode="jd" if has_jd else "role",
        role=(cfg["title"] if not has_jd else ""),
        job_description=payload.job_description,
    )

    breakdown = llm_full.get("Score_Breakdown", {}) or {}
    ats_score = int(llm_full.get("ATS_Score", 0))
    resume_health = parse_resume_health(llm_full.get("Resume_Health"), content_fallback=ats_score)

    suggestions = [str(x).strip() for x in llm_full.get("Suggestions_for_Improvement", []) if str(x).strip()]
    raw_missing = llm_full.get("Missing_Keywords")
    missing_kw = [str(x).strip() for x in raw_missing if str(x).strip()] if isinstance(raw_missing, list) else []
    missing_kw_list = [str(x).strip() for x in llm_full.get("Missing_Keyword_List", []) if str(x).strip()]

    key_skills = [str(x).strip() for x in llm_full.get("Key_Skills", []) if str(x).strip()]

    repeated_norm = _coerce_repeated_word_frequency(llm_full.get("Repeated_Word_Frequency"))

    word_repl = [str(x).strip() for x in llm_full.get("Word_Replacement_Suggestions", []) if str(x).strip()]

    detailed_analysis = llm_full.get("Detailed_Analysis") or {}
    improvement_roadmap = llm_full.get("Improvement_Roadmap") or {}

    return build_contract_response({
        "ATS_Score": ats_score,
        "Summary": str(llm_full.get("Summary", "")).strip(),
        "Resume_Health": resume_health,
        "Suggestions_for_Improvement": suggestions,
        "Score_Breakdown": {
            "FORMAT": int(breakdown.get("FORMAT", 0)),
            "SKILLS": int(breakdown.get("SKILLS", 0)),
            "EXPERIENCE": int(breakdown.get("EXPERIENCE", 0)),
            "COMPLETENESS": int((breakdown.get("EDUCATION", 0) or 0)),
        },
        "Missing_Keywords": llm_full.get("Missing_Keywords") or missing_kw,
        "Missing_Keyword_List": missing_kw_list,
        "Achievements_or_Certifications": [
            str(x).strip() for x in llm_full.get("Achievements_or_Certifications", []) if str(x).strip()
        ],
        "Resume_Strength": [str(x).strip() for x in llm_full.get("Resume_Strength", []) if str(x).strip()],
        "Key_Skills": key_skills,
        "Repeated_Word_Frequency": {str(k).strip().lower(): int(v) for k, v in repeated_norm.items()},
        "Word_Replacement_Suggestions": word_repl,
        "Resume_Positioning": llm_full.get("Resume_Positioning"),
        "Resume_Health_Label": llm_full.get("Resume_Health_Label"),
        "Overused_Keywords_Count": llm_full.get("Overused_Keywords_Count"),
    })
