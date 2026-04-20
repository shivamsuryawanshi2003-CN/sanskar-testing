"""ATS-only analysis (no role, no JD): /analyse/general."""

from ..heuristics import analyze_resume_heuristically


def llm_general_score_only(*, resume_text: str) -> dict:
    return analyze_resume_heuristically(resume_text=resume_text)
