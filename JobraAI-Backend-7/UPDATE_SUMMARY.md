# JobraAI Backend v5 updates

- Shifted ATS response generation further toward an LLM-first hybrid path.
- Added mode-aware comparison prompting for General, With Role, and With JD flows.
- Included target keyword extraction and comparison evidence in LLM prompts.
- Added configurable minimum LLM response time window via:
  - `MIN_LLM_RESPONSE_SECONDS` (default `10`)
  - `MAX_LLM_RESPONSE_SECONDS` (default `15`)
- Reduced duplicate LLM calls by reusing `Detailed_Analysis` and `Improvement_Roadmap` from the same payload.
- Kept deterministic analysis as fallback evidence, while letting the LLM generate the final narrative structure and calibration when an API key is present.
