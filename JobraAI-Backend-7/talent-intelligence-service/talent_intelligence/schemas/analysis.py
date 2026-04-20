from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResumeHealthBlock(BaseModel):
    """Structured resume health signals aligned with the web dashboard."""

    Content_Percent: int = 0
    ATS_Parse_Rate: str = "No issues"
    Quantifying_Impact: str = "No issues"
    Repetition: str = "No issues"
    Spelling_Grammar: str = "No issues"

    @field_validator("ATS_Parse_Rate", "Quantifying_Impact", "Repetition", "Spelling_Grammar", mode="before")
    @classmethod
    def _coerce_issue_label(cls, v: Any) -> str:
        if v is None:
            return "No issues"
        s = str(v).strip()
        return s if s else "No issues"


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    role: str = Field(default="", description="Role ID or plain role title for role-based analysis. Leave empty for JD-only mode.")
    job_description: str = Field(default="", description="Pasted job description for JD-aware scoring.")
    additional_context: str = Field(default="", description="Optional extra resume context (projects, achievements, tools, responsibilities).")
    model_config = ConfigDict(json_schema_extra={"example": {"resume_text": "Software Engineer with Python, APIs, and cloud deployment experience...", "role": "Data Analyst", "job_description": ""}})


class AnalyzeResponse(BaseModel):
    ATS_Score: int
    Resume_Positioning: str
    Resume_Health_Label: str
    Resume_Health: ResumeHealthBlock | None = None
    Summary: str
    Suggestions_for_Improvement: list[str] = Field(default_factory=list)
    Score_Breakdown: dict[str, str] = Field(default_factory=dict)
    Missing_Keywords: dict[str, int] = Field(default_factory=dict)
    Missing_Keyword_List: list[str] = Field(default_factory=list)
    Achievements_or_Certifications: list[str] = Field(default_factory=list)
    Resume_Strength: list[str] = Field(default_factory=list)
    Key_Skills: list[str] = Field(default_factory=list)
    Overused_Keywords_Count: int = 0
    Repeated_Word_Frequency: dict[str, int] = Field(default_factory=dict)
    Word_Replacement_Suggestions: list[str] = Field(default_factory=list)
    model_config = ConfigDict(json_schema_extra={"example": {
        "ATS_Score": 78,
        "Resume_Positioning": "Competitive",
        "Resume_Health_Label": "Moderate",
        "Resume_Health": {
            "Content_Percent": 72,
            "ATS_Parse_Rate": "No issues",
            "Quantifying_Impact": "No issues",
            "Repetition": "No issues",
            "Spelling_Grammar": "No issues",
        },
        "Summary": "Your resume showcases a solid foundation in AI engineering with impressive project work and relevant technical skills. The quantifiable impacts of your projects demonstrate your ability to deliver results, which is crucial for standing out in the competitive job market. However, there are minor areas for improvement in formatting and completeness that could enhance its overall effectiveness.",
        "Suggestions_for_Improvement": [
            "Ensure consistent formatting throughout the resume for better readability.",
            "Add a section for relevant coursework or additional certifications to enhance completeness.",
            "Consider quantifying your skills or achievements further where possible."
        ],
        "Score_Breakdown": {"FORMAT": "80%", "SKILLS": "90%", "EXPERIENCE": "85%", "COMPLETENESS": "75%"},
        "Missing_Keywords": {"SUMMARY": 1, "SKILLS": 0, "EXPERIENCE": 0, "PROJECTS": 0},
        "Missing_Keyword_List": ["sql", "tableau"],
        "Achievements_or_Certifications": ["Deep Learning Specialization | IIT Ropar"],
        "Resume_Strength": [
            "Strong technical skills in AI and machine learning.",
            "Impressive project work with quantifiable outcomes.",
            "Clear demonstration of problem-solving abilities."
        ],
        "Key_Skills": ["Python", "SQL", "TensorFlow", "PyTorch", "FastAPI", "NLP", "Docker", "PostgreSQL", "Machine Learning", "AI Engineering", "Streamlit", "LangChain", "RAG", "Data Analysis"],
        "Overused_Keywords_Count": 0,
        "Repeated_Word_Frequency": {},
        "Word_Replacement_Suggestions": []
    }})


class UpgradeSuggestionRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    ats_report: dict[str, object]
    choice_id: int = Field(ge=1, le=3, description="Choice type for upgrade: 1=general, 2=role, 3=JD-only.")
    context_data: str = Field(default="", description="Optional role title or pasted job description when applicable.")


class UpgradeSuggestionResponse(BaseModel):
    Professional_Summary: str
    Work_Experience: list[dict[str, str]]
    Skills: dict[str, list[str]]
    Education: list[str] = Field(default_factory=list)
    Certifications: list[str] = Field(default_factory=list)


class NoRoleScoreResponse(AnalyzeResponse):
    pass
