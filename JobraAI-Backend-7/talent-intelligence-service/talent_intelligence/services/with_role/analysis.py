"""Role-aware ATS analysis: /analyse/with-role."""

from ..heuristics import analyze_resume_heuristically


def llm_with_role_full_analysis(
    *,
    resume_text: str,
    role: str,
    role_summary: str,
    additional_context: str,
    role_keywords: list[str],
) -> dict:
    return analyze_resume_heuristically(
        resume_text=resume_text,
        role_title=role,
        role_keywords=role_keywords,
        role_summary=role_summary,
        additional_context=additional_context,
    )
