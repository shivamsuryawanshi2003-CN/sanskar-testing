# AI assisted development
from pydantic import BaseModel, ConfigDict, Field


class ResumeHealthStrip(BaseModel):
    """Quick-scan row: Content %, ATS parse, impact, repetition, spelling (UI-friendly labels)."""

    Content_Percent: int = Field(ge=0, le=100, description="Content strength 0–100 (display as %).")
    ATS_Parse_Rate: str = Field(description='e.g. "No issues" or "2 issues"')
    Quantifying_Impact: str = Field(description='e.g. "No issues" or "1 issue"')
    Repetition: str = Field(description='e.g. "No issues" or "1 issue"')
    Spelling_Grammar: str = Field(description='e.g. "No issues", "3", or "3 issues"')


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    role: str = Field(min_length=1)
    job_description: str = Field(default="", description="Optional JD text for with-JD scoring.")
    additional_context: str = Field(
        default="",
        description="Optional extra resume context (projects, achievements, tools, responsibilities).",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_text": "Software Engineer with Python, APIs, and cloud deployment experience...",
                "role": "1",
                "job_description": "Looking for Backend Role with API, SQL, and Docker skills.",
            }
        }
    )


class AnalyzeResponse(BaseModel):
    ATS_Score: int
    Summary: str
    Resume_Health: ResumeHealthStrip
    Suggestions_for_Improvement: list[str]
    Score_Breakdown: dict[str, int]
    Missing_Keywords: list[str]
    Achievements_or_Certifications: list[str]
    Resume_Strength: list[str]
    Key_Skills: list[str]
    Repeated_Word_Frequency: dict[str, int] = Field(
        description="Stylistic/filler repetition only (word → count); excludes technical skills, tools, and the token 'skills'.",
    )
    Word_Replacement_Suggestions: list[str] = Field(
        description="Replacement hints aligned with Repeated_Word_Frequency rules (not stack terms).",
    )
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ATS_Score": 74,
                "Summary": "Your profile lines up reasonably well with a backend-focused role: you show solid API and data-layer experience and clear ownership of delivery. The strongest signals are your stack mentions and end-to-end feature work. Gaps are mainly around measurable impact and a few role-specific keywords that ATS parsers expect to see in both summary and experience bullets. Tightening metrics and echoing must-have terms from the role would lift both human scan and parser scores.",
                "Resume_Health": {
                    "Content_Percent": 55,
                    "ATS_Parse_Rate": "No issues",
                    "Quantifying_Impact": "1 issue",
                    "Repetition": "1 issue",
                    "Spelling_Grammar": "3",
                },
                "Suggestions_for_Improvement": [
                    "Add one latency or throughput number to your strongest backend bullet.",
                    "Name Redis and pytest where you actually used them so parsers can match the role.",
                    "Tie each project line to an outcome recruiters can verify.",
                ],
                "Score_Breakdown": {
                    "FORMAT": 80,
                    "SKILLS": 72,
                    "EXPERIENCE": 75,
                    "EDUCATION": 70,
                },
                "Missing_Keywords": [
                    "You have about 2 missing keywords in the professional summary section.",
                    "You have about 3 missing keywords in the work experience section.",
                    "You have about 2 missing keywords in the technical skills section.",
                ],
                "Achievements_or_Certifications": ["Improved API response time by 35%."],
                "Resume_Strength": ["Contains role-relevant terminology.", "Work history evidence detected."],
                "Key_Skills": ["api", "docker", "postgresql", "python", "redis", "sql"],
                "Repeated_Word_Frequency": {"analyzed": 3, "various": 3},
                "Word_Replacement_Suggestions": [
                    "3 times: analyzed\ntry replacing with\nexamined\ninvestigated\nscrutinized",
                    "4 times: various\ntry replacing with\ndiverse\nassorted\nmultiple",
                ],
            }
        }
    )
