"""Pure-LLM resume scoring (no JD). Loaded by /analyse/general when without_jd_engine=pure_llm."""

import json
import os
import sys
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from talent_intelligence.services.resume_intake import load_resume_text_from_bytes, require_valid_resume_text

try:
    from talent_intelligence.services.llm_shared.common import OPENAI_MODEL
except ImportError:
    OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_MODE") or "gpt-4o-mini").strip()

STRICT_LLM_PROMPT = """
You are an advanced AI trained to classify documents and analyze resumes with strict scoring criteria.
You are a precision-focused ATS system: same JSON schema as role-based scoring, but **without** any job description or target role — score overall resume quality and ATS readiness only.

### Resume detection
- A resume typically includes sections like Experience, Education, Skills, Certifications, and Projects.
- If the document does not match a resume structure, return only this plain text (not JSON):
  "This document does not appear to be a resume. No ATS score will be generated."

### Instructions (no JD)
1. ATS_Score 0–100 from structure, clarity, keyword richness, experience depth, education, readability, contact/dates signals, repetition, and grammar.
2. Summary: 4–7 sentences; no bullet characters inside Summary.
3. Score_Breakdown: integers 0–100 for FORMAT, SKILLS, EXPERIENCE, EDUCATION only (no COMPLETENESS key).
4. Missing_Keywords: exactly 3 strings: "You have about N missing keywords in the <section> section." with N 1–5 — describe **section polish** vs a strong generic resume (summary, experience, technical skills), not a specific job.
5. Suggestions_for_Improvement: exactly 3 actionable lines about resume quality and ATS (not role fit).
6. Achievements_or_Certifications, Resume_Strength (3–4 points), Key_Skills (from resume; sort alphabetically).
7. Repeated_Word_Frequency / Word_Replacement_Suggestions: same rules as Jobra Section 2 — non-skill filler repetition only; exclude technical tools and the token "skills".

### Output
Return **only** valid JSON with every key below (no markdown fences):
{{
  "ATS_Score": 0,
  "Summary": "",
  "Resume_Health": {{
    "Content_Percent": 0,
    "ATS_Parse_Rate": "No issues",
    "Quantifying_Impact": "No issues",
    "Repetition": "No issues",
    "Spelling_Grammar": "No issues"
  }},
  "Suggestions_for_Improvement": [],
  "Score_Breakdown": {{"FORMAT": 0, "SKILLS": 0, "EXPERIENCE": 0, "EDUCATION": 0}},
  "Missing_Keywords": [],
  "Achievements_or_Certifications": [],
  "Resume_Strength": [],
  "Key_Skills": [],
  "Repeated_Word_Frequency": {{}},
  "Word_Replacement_Suggestions": []
}}

**Resume Text:**
{resume_text}
"""


class PureLLMScorer:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0,
            openai_api_key=api_key,
        )

    def analyze_resume_text(self, resume_text: str) -> dict:
        text = require_valid_resume_text(resume_text)
        prompt = ChatPromptTemplate.from_template(STRICT_LLM_PROMPT)
        chain = prompt | self.llm

        content = ""
        try:
            response = chain.invoke({"resume_text": text[:8000]})
            content = response.content.strip()

            if "does not appear to be a resume" in content:
                return {"message": content}

            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0].strip()

            return json.loads(content)

        except json.JSONDecodeError:
            return {"error": "AI failed to generate a structured JSON response.", "raw_output": content}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("Set OPENAI_API_KEY in the environment or in a .env file.")
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "resume5.pdf")
    text = load_resume_text_from_bytes(path.name, path.read_bytes())
    scorer = PureLLMScorer(api_key=api_key)
    result = scorer.analyze_resume_text(text)
    print(json.dumps(result, indent=4))
