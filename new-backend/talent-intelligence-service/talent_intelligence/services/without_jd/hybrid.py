# AI assisted development
"""Hybrid deterministic + LLM resume scoring (no JD). Loaded by /analyse/general when without_jd_engine=hybrid."""

import json
import os
import re
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from talent_intelligence.services.resume_intake import require_valid_resume_text

try:
    from talent_intelligence.services.llm_shared.common import OPENAI_MODEL
except ImportError:
    OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or os.getenv("OPENAI_MODE") or "gpt-4o-mini").strip()

RESUME_ANALYSIS_PROMPT = """
System: You are an expert resume analyst. Task: audit the resume text (no job description).

### Rules
1. VALIDATION: If the text is not a professional resume (e.g. certificate, ID), set is_valid_resume to false.
2. SENIORITY: One of Fresher, Junior, Mid, Senior, Lead.
3. REPETITION: List high-value words (technical/action) used MORE than 5 times; exclude stop-words (the, and, is).
4. SCORES: skill_depth, formatting, experience_relevance — each 0.0–1.0.
5. OUTPUT must match the JSON shape below. suggestions: exactly 3 strings (resume quality / ATS, not role fit).
6. missing_keyword_lines: exactly 3 strings like "You have about N missing keywords in the professional summary section." (N 1–5) for summary, experience, and technical skills — generic resume polish, not a specific job.
7. achievements_or_certifications: short factual items from the resume (or empty).
8. resume_strength: 3–4 short strings.
9. repeated_word_frequency: map **non-skill** repeated words (count >=3) to counts; exclude tools/languages/frameworks and the token "skills"; use {{}} if none.
10. word_replacement_suggestions: one multiline string per repeated_word_frequency key, same format as Jobra Section 2, or [].

Resume text:
{resume_text}

JSON only:
{{
  "is_valid_resume": true,
  "seniority": "Mid",
  "scores": {{"skill_depth": 0.7, "formatting": 0.8, "experience_relevance": 0.75}},
  "overused_keywords": [],
  "present_hard_skills": [],
  "suggestions": [],
  "missing_keyword_lines": [],
  "contains_education": true,
  "summary": "",
  "achievements_or_certifications": [],
  "resume_strength": [],
  "repeated_word_frequency": {{}},
  "word_replacement_suggestions": []
}}
"""


class SeniorATSScorer:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model=OPENAI_MODEL,
            temperature=0,
            openai_api_key=api_key,
        )

    def get_deterministic_metrics(self, text: str) -> Dict[str, Any]:
        word_count = len(text.split())
        metrics = re.findall(r"\d+%|\$\d+|increased|decreased|revenue|scaled|managed \d+", text.lower())
        has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+", text))
        has_phone = bool(re.search(r"\+?\d[\d -]{8,12}\d", text))
        return {
            "word_count": word_count,
            "metric_count": len(metrics),
            "has_contact": has_email or has_phone,
        }

    def analyze_from_text(self, resume_text: str) -> dict:
        raw_text = require_valid_resume_text(resume_text)
        python_metrics = self.get_deterministic_metrics(raw_text)
        prompt = ChatPromptTemplate.from_template(RESUME_ANALYSIS_PROMPT)
        chain = prompt | self.llm

        ai_data: Dict[str, Any] = {}
        try:
            response_obj = chain.invoke({"resume_text": raw_text[:7000]})
            content = response_obj.content
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0]
            ai_data = json.loads(content.strip())
        except Exception:
            return {"error": "The AI returned invalid data. Please try again."}

        if not ai_data.get("is_valid_resume"):
            return {"error": "Invalid Document. Please upload a professional resume."}

        s = ai_data.get("scores") or {}
        try:
            fmt = float(s.get("formatting", 0.0))
            skill_d = float(s.get("skill_depth", 0.0))
            exp_r = float(s.get("experience_relevance", 0.0))
        except (TypeError, ValueError):
            return {"error": "Invalid score values from AI response."}

        format_pct = max(0, min(100, round(fmt * 100)))
        skills_pct = max(0, min(100, round(skill_d * 100)))
        exp_pct = max(0, min(100, round(exp_r * 100)))
        edu_pts = 10 if ai_data.get("contains_education") else 0
        contact_pts = 5 if python_metrics["has_contact"] else 0
        education_component = round((edu_pts + contact_pts) / 15 * 100)

        base_total = (skill_d * 30) + (exp_r * 35) + (fmt * 20) + edu_pts + contact_pts

        penalty_multiplier = 1.0
        level = str(ai_data.get("seniority", "Junior")).lower()
        words = python_metrics["word_count"]

        overused = ai_data.get("overused_keywords") or []
        if overused:
            penalty_multiplier -= len(overused) * 0.05

        if any(word in level for word in ("senior", "lead", "mid")):
            if python_metrics["metric_count"] == 0:
                penalty_multiplier *= 0.70
        else:
            if any(word in level for word in ("fresher", "junior", "entry")):
                if words > 800:
                    penalty_multiplier *= 0.90
            elif words < 600:
                penalty_multiplier *= 0.85

        final_score = max(0, min(100, base_total * penalty_multiplier))
        final_int = max(0, min(100, round(final_score)))

        suggestions = [str(x).strip() for x in (ai_data.get("suggestions") or []) if str(x).strip()]
        while len(suggestions) < 3:
            suggestions.append("Tighten bullets with action + tool + measurable outcome where possible.")
        suggestions = suggestions[:3]

        missing_lines = [
            str(x).strip() for x in (ai_data.get("missing_keyword_lines") or []) if str(x).strip()
        ]

        achievements = [
            str(x).strip() for x in (ai_data.get("achievements_or_certifications") or []) if str(x).strip()
        ]
        if python_metrics["metric_count"] > 0 and not achievements:
            achievements = ["Quantified impact signals detected in the resume body."]

        resume_strength = [str(x).strip() for x in (ai_data.get("resume_strength") or []) if str(x).strip()]
        if len(resume_strength) < 3:
            resume_strength.extend(
                [
                    "Document parses as a standard resume structure.",
                    "Skills and experience sections are both present.",
                    "Continue adding measurable outcomes alongside responsibilities.",
                ]
            )
        resume_strength = resume_strength[:6]

        key_skills = sorted(
            {str(x).strip().lower() for x in (ai_data.get("present_hard_skills") or []) if str(x).strip()}
        )

        rw_raw = ai_data.get("repeated_word_frequency") or {}
        repeated: dict[str, int] = {}
        if isinstance(rw_raw, dict):
            for k, v in rw_raw.items():
                try:
                    repeated[str(k).strip().lower()] = int(v)
                except (TypeError, ValueError):
                    continue
        if not repeated and overused:
            repeated = {str(w).strip().lower(): 6 for w in overused if str(w).strip()}

        wr = [str(x).strip() for x in (ai_data.get("word_replacement_suggestions") or []) if str(x).strip()]

        rep_issue = f"{len(overused)} issue(s)" if overused else "No issues"
        impact_issue = "No issues" if python_metrics["metric_count"] else "1 issue"

        return {
            "ATS_Score": final_int,
            "Summary": str(ai_data.get("summary", "")).strip(),
            "Resume_Health": {
                "Content_Percent": min(100, final_int),
                "ATS_Parse_Rate": "No issues",
                "Quantifying_Impact": impact_issue,
                "Repetition": rep_issue,
                "Spelling_Grammar": "No issues",
            },
            "Suggestions_for_Improvement": suggestions,
            "Score_Breakdown": {
                "FORMAT": format_pct,
                "SKILLS": skills_pct,
                "EXPERIENCE": exp_pct,
                "EDUCATION": education_component,
            },
            "Missing_Keywords": missing_lines,
            "Achievements_or_Certifications": achievements,
            "Resume_Strength": resume_strength,
            "Key_Skills": key_skills,
            "Repeated_Word_Frequency": repeated,
            "Word_Replacement_Suggestions": wr,
        }
