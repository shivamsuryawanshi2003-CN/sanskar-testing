"""JD-aware ATS analysis: /analyse/with-jd."""

from ..heuristics import analyze_resume_heuristically


def llm_with_jd_full_analysis(
    *,
    resume_text: str,
    job_description: str,
    additional_context: str,
) -> dict:
    return analyze_resume_heuristically(
        resume_text=resume_text,
        job_description=job_description,
        additional_context=additional_context,
    )
