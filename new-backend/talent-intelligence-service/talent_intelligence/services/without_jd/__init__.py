"""No–job-description ATS engines (pure LLM + hybrid). Used by ``/analyse/general``."""

from .hybrid import SeniorATSScorer
from .llm import PureLLMScorer

__all__ = ["PureLLMScorer", "SeniorATSScorer"]
