"""Re-exports for backward compatibility.

Service layout under ``talent_intelligence.services``:

- ``ats`` — ATS-only (general)
- ``with_role`` — catalog role, no pasted JD
- ``with_jd`` — pasted JD only
- ``llm_shared`` — prompts + shared OpenAI helpers
"""

from .ats import llm_general_score_only
from .llm_shared.common import (
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    OPENAI_TIMEOUT_SECONDS,
    llm_batch_insights,
    llm_ping,
    llm_policy,
)
from .with_jd import llm_with_jd_full_analysis
from .with_role import llm_with_role_full_analysis

__all__ = [
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "OPENAI_TIMEOUT_SECONDS",
    "llm_batch_insights",
    "llm_general_score_only",
    "llm_ping",
    "llm_policy",
    "llm_with_jd_full_analysis",
    "llm_with_role_full_analysis",
]
