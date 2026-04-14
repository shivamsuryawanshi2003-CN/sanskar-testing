"""Full ATS analysis with catalog role + pasted job description: /analyse/with-jd."""

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
from ..llm_shared.prompt import PROMPT_SECTION_3_ATS_WITH_JD_BODY, PROMPT_SECTION_3_ATS_WITH_JD_SYSTEM


def llm_with_jd_full_analysis(
    *,
    resume_text: str,
    role: str,
    role_summary: str,
    job_description: str,
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
    role_block = f"""### ROLE (selected from catalog)
Role: {role}
Role Context: {role_summary[:1400]}
Role Keywords: {", ".join(role_keywords[:24])}
"""
    body = (
        PROMPT_SECTION_3_ATS_WITH_JD_BODY.replace("__JOB_DESCRIPTION__", job_description[:2200])
        .replace("__RESUME_TEXT__", resume_text[:3200])
    )
    prompt = f"""{role_block}

{body}

Additional Resume Context:
{additional_context[:1200] if additional_context else "not provided"}
""".strip()
    system_prompt = PROMPT_SECTION_3_ATS_WITH_JD_SYSTEM
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
        raise ValueError("OpenAI returned empty with-jd payload.")
    try:
        parsed = _parse_json_text(text)
    except Exception as exc:
        raise ValueError(f"OpenAI returned non-JSON with-jd payload: {text[:220]}") from exc

    if isinstance(parsed, dict) and parsed.get("error") and "ATS_Score" not in parsed:
        raise ValueError(str(parsed["error"]))

    return _normalize_full_analysis_payload(parsed)
