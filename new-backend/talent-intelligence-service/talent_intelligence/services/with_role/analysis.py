"""Full ATS analysis with catalog role only (no pasted JD): /analyse/with-role."""

from openai import OpenAI

from ..llm_shared.common import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
    _extract_response_text,
    _normalize_full_analysis_payload,
    _parse_json_text,
    _responses_create_with_retry,
)
from ..llm_shared.prompt import PROMPT_SECTION_2_ATS_WITH_ROLE


def llm_with_role_full_analysis(
    *,
    resume_text: str,
    role: str,
    role_summary: str,
    additional_context: str,
    role_keywords: list[str],
) -> dict:
    if not OPENAI_API_KEY.strip():
        raise ValueError("OPENAI_API_KEY is missing.")

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=OPENAI_TIMEOUT_SECONDS,
    )
    prompt = f"""
Role: {role}
Role Context: {role_summary[:1400]}
Role Keywords: {", ".join(role_keywords[:24])}
Resume Text:
{resume_text[:3200]}
Additional Resume Context:
{additional_context[:1200] if additional_context else "not provided"}
""".strip()
    system_prompt = PROMPT_SECTION_2_ATS_WITH_ROLE
    response = _responses_create_with_retry(
        client=client,
        model=OPENAI_MODEL,
        input_payload=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
        ],
        store=False,
    )
    text = _extract_response_text(response)
    if not text:
        raise ValueError("OpenAI returned empty with-role payload.")
    try:
        parsed = _parse_json_text(text)
    except Exception as exc:
        raise ValueError(f"OpenAI returned non-JSON with-role payload: {text[:220]}") from exc

    return _normalize_full_analysis_payload(parsed)
