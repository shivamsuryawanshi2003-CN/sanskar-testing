# AI assisted development
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from talent_intelligence.schemas.analysis import NoRoleScoreResponse
from talent_intelligence.services.llm_service import llm_general_score_only
from talent_intelligence.services.hybrid_analysis import enhance_analysis_payload
from talent_intelligence.services.response_formatter import build_contract_response
from talent_intelligence.services.resume_extract import ResumeExtractError, extract_resume_text

from .common import MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, logger

router = APIRouter()


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = (file.filename or "").strip()
    lower = filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx resume files are accepted.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max size is {MAX_UPLOAD_SIZE_MB} MB.")
    return filename, data


def _to_response(llm_payload: dict, resume_text: str) -> NoRoleScoreResponse:
    llm_payload = enhance_analysis_payload(analysis=llm_payload, resume_text=resume_text, mode="general")
    breakdown = llm_payload.get("Score_Breakdown", {}) or {}
    ats = int(llm_payload.get("ATS_Score", 0))
    raw_missing = llm_payload.get("Missing_Keywords")
    return build_contract_response({
        "ATS_Score": ats,
        "Summary": str(llm_payload.get("Summary", "")).strip(),
        "Resume_Health": llm_payload.get("Resume_Health") or {},
        "Suggestions_for_Improvement": [str(x).strip() for x in (llm_payload.get("Suggestions_for_Improvement") or []) if str(x).strip()],
        "Score_Breakdown": {
            "FORMAT": int(breakdown.get("FORMAT", 0) or 0),
            "SKILLS": int(breakdown.get("SKILLS", 0) or 0),
            "EXPERIENCE": int(breakdown.get("EXPERIENCE", 0) or 0),
            "COMPLETENESS": int((breakdown.get("EDUCATION", 0) or 0)),
        },
        "Missing_Keywords": raw_missing if isinstance(raw_missing, (list, dict)) else [],
        "Missing_Keyword_List": [str(x).strip() for x in (llm_payload.get("Missing_Keyword_List") or []) if str(x).strip()],
        "Achievements_or_Certifications": [str(x).strip() for x in (llm_payload.get("Achievements_or_Certifications") or []) if str(x).strip()],
        "Resume_Strength": [str(x).strip() for x in (llm_payload.get("Resume_Strength") or []) if str(x).strip()],
        "Key_Skills": [str(x).strip() for x in (llm_payload.get("Key_Skills") or []) if str(x).strip()],
        "Repeated_Word_Frequency": llm_payload.get("Repeated_Word_Frequency") or {},
        "Word_Replacement_Suggestions": [str(x).strip() for x in (llm_payload.get("Word_Replacement_Suggestions") or []) if str(x).strip()],
        "Resume_Positioning": llm_payload.get("Resume_Positioning"),
        "Resume_Health_Label": llm_payload.get("Resume_Health_Label"),
        "Overused_Keywords_Count": llm_payload.get("Overused_Keywords_Count"),
    })


@router.post(
    "/analyse/general",
    response_model=NoRoleScoreResponse,
    summary="Upload resume and check ATS score without role or JD",
    response_description="Deterministic ATS score without role or JD.",
)
async def analyse_general(
    file: UploadFile = File(None, description="Resume file (.pdf or .docx only). Optional if resume_text provided."),
    resume_text: str = Form(None, description="Resume text. If provided, file is ignored."),
    without_jd_engine: str = Form(
        "default",
        description="Deprecated. The API now uses a single deterministic ATS engine.",
    ),
) -> NoRoleScoreResponse:
    try:
        if resume_text and resume_text.strip():
            clean_text = resume_text.strip()
            return _to_response(llm_general_score_only(resume_text=clean_text), clean_text)

        if file is None:
            raise HTTPException(status_code=422, detail="Either file or resume_text must be provided.")

        filename, raw = await _read_upload(file)
        try:
            extracted_text = extract_resume_text(filename, raw)
        except ResumeExtractError as exc:
            logger.warning("Resume extraction failed for file '%s': %s", filename, str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return _to_response(llm_general_score_only(resume_text=extracted_text), extracted_text)
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Validation failed in /analyse/general: %s", str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /analyse/general: %s", str(exc))
        raise HTTPException(status_code=500, detail="Unable to process resume analysis right now.") from exc
