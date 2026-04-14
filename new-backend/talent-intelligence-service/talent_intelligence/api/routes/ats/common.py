# AI assisted development
import logging
import os

from fastapi import HTTPException, UploadFile

from talent_intelligence.services.resume_extract import ResumeExtractError, extract_resume_text
from talent_intelligence.services.resume_intake import ResumeValidationError, require_valid_resume_text

logger = logging.getLogger(__name__)
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ANALYZE_RESPONSE_EXAMPLE = {
    "ATS_Score": 38,
    "Summary": "Android-focused developer with internship experience in mobile feature delivery and API integration. Demonstrates UI implementation capability and can improve ATS fit by adding measurable outcomes and Android-specific stack terms.",
    "Resume_Health": {
        "Content_Percent": 55,
        "ATS_Parse_Rate": "No issues",
        "Quantifying_Impact": "1 issue",
        "Repetition": "1 issue",
        "Spelling_Grammar": "3",
    },
    "Suggestions_for_Improvement": [
        "Incorporate Android-focused keywords and competencies (kotlin, android, jetpack, mvvm, rest api, firebase, gradle) into the profile and add a dedicated Skills section to boost ATS relevance.",
        "Reframe internship experience to emphasize Android feature delivery with explicit stack references and outcomes.",
        "Quantify impact by adding Android-relevant metrics such as feature adoption, crash-rate reduction, and API latency improvement.",
    ],
    "Score_Breakdown": {
        "FORMAT": 60,
        "SKILLS": 12,
        "EXPERIENCE": 55,
        "EDUCATION": 70,
    },
    "Missing_Keywords": [
        "You have about 3 missing keywords in the professional summary section.",
        "You have about 4 missing keywords in the work experience section.",
        "You have about 3 missing keywords in the technical skills section.",
    ],
    "Achievements_or_Certifications": ["Completed Android certification program."],
    "Resume_Strength": ["Contains role-relevant terminology.", "Work history evidence detected."],
    "Key_Skills": ["ui"],
    "Repeated_Word_Frequency": {"analyzed": 3, "responsible": 4},
    "Word_Replacement_Suggestions": [
        "3 times: analyzed\ntry replacing with\nexamined\ninvestigated\nscrutinized",
        "4 times: responsible\ntry replacing with\nowned\ndelivered\nimplemented",
    ],
}


async def extract_uploaded_resume(file: UploadFile) -> str:
    filename = (file.filename or "").strip()
    lower = filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx resume files are accepted.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_UPLOAD_SIZE_MB} MB.")
    try:
        text = extract_resume_text(filename, data)
    except ResumeExtractError as exc:
        logger.warning("Resume extraction failed for file '%s': %s", filename, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return require_valid_resume_text(text)
    except ResumeValidationError as exc:
        logger.warning("Resume validation failed for file '%s': %s", filename, exc.message)
        raise HTTPException(status_code=400, detail=exc.message) from exc
