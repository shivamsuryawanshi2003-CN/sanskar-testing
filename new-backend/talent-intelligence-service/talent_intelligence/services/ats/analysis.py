# AI assisted development
"""ATS-only analysis (no role, no JD): /analyse/general."""

from openai import OpenAI

from ..resume_intake import require_valid_resume_text
from ..llm_shared.common import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
    _extract_response_text,
    _normalize_general_ats_payload,
    _parse_json_text,
    _responses_create_with_retry,
)
from ..llm_shared.prompt import PROMPT_SECTION_1_ATS_ONLY


def llm_general_score_only(*, resume_text: str) -> dict:
    require_valid_resume_text(resume_text)
    if not OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is missing.")
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )
    system_prompt = PROMPT_SECTION_1_ATS_ONLY
    user_prompt = f"Resume Text:\n{resume_text[:3200]}"
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
        raise ValueError("OpenAI returned empty general ATS payload.")
    try:
        parsed = _parse_json_text(text)
    except Exception as exc:
        raise ValueError(f"OpenAI returned non-JSON general ATS payload: {text[:220]}") from exc

    return _normalize_general_ats_payload(parsed)
