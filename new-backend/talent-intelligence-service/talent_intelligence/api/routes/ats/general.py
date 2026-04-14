# AI assisted development
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from talent_intelligence.schemas.analysis import AnalyzeResponse
from talent_intelligence.services.llm_service import llm_general_score_only
from talent_intelligence.services.llm_shared.common import (
    _normalize_full_analysis_payload,
    _normalize_general_ats_payload,
)
from talent_intelligence.services.resume_extract import ResumeExtractError
from talent_intelligence.services.resume_intake import ResumeValidationError, load_resume_text_from_bytes
from talent_intelligence.services.without_jd import PureLLMScorer, SeniorATSScorer

from .common import ANALYZE_RESPONSE_EXAMPLE, MAX_UPLOAD_SIZE_BYTES, MAX_UPLOAD_SIZE_MB, logger

router = APIRouter()


def _to_analyze_response(payload: dict) -> AnalyzeResponse:
    """Normalize LLM/deterministic dict to the same shape as with-role / with-jd."""
    normalized = _normalize_full_analysis_payload(payload)
    return AnalyzeResponse.model_validate(normalized)


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = (file.filename or "").strip()
    lower = filename.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx resume files are accepted.")
    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {MAX_UPLOAD_SIZE_MB} MB.",
        )
    return filename, data


@router.post(
    "/analyse/general",
    response_model=AnalyzeResponse,
    summary="Upload resume and check ATS score without role",
    response_description=(
        "Same JSON shape as /analyse/with-role and /analyse/with-jd. "
        "`without_jd_engine`: default (OpenAI Responses API), pure_llm, hybrid."
    ),
    responses={
        200: {
            "description": "ATS output format (aligned with with-role / with-jd)",
            "content": {"application/json": {"example": ANALYZE_RESPONSE_EXAMPLE}},
        }
    },
)
async def analyse_general(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx only)."),
    without_jd_engine: str = Form(
        "default",
        description=(
            "default | pure_llm | hybrid — pure_llm/hybrid use "
            "`talent_intelligence.services.without_jd` (same extract + validity checks as other routes)."
        ),
    ),
) -> AnalyzeResponse:
    try:
        if without_jd_engine not in ("default", "pure_llm", "hybrid"):
            raise HTTPException(
                status_code=422,
                detail="without_jd_engine must be one of: default, pure_llm, hybrid.",
            )

        filename, raw = await _read_upload(file)

        try:
            resume_text = load_resume_text_from_bytes(filename, raw)
        except ResumeExtractError as exc:
            logger.warning("Resume extraction failed for file '%s': %s", filename, str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ResumeValidationError as exc:
            logger.warning("Resume validation failed for file '%s': %s", filename, exc.message)
            raise HTTPException(status_code=400, detail=exc.message) from exc

        if without_jd_engine == "default":
            llm_payload = llm_general_score_only(resume_text=resume_text)
            normalized = _normalize_general_ats_payload(llm_payload)
            return AnalyzeResponse.model_validate(normalized)

        api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not api_key:
            raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured.")

        if without_jd_engine == "pure_llm":
            scorer = PureLLMScorer(api_key=api_key)
            raw_out = scorer.analyze_resume_text(resume_text)
            if not isinstance(raw_out, dict):
                raise HTTPException(status_code=500, detail="Unexpected without_jd LLM response shape.")
            if raw_out.get("error"):
                raise HTTPException(status_code=400, detail=str(raw_out["error"]))
            if raw_out.get("message") and "does not appear to be a resume" in str(raw_out.get("message", "")):
                raise HTTPException(status_code=400, detail=str(raw_out["message"]))
            return _to_analyze_response(raw_out)

        scorer = SeniorATSScorer(api_key=api_key)
        raw_out = scorer.analyze_from_text(resume_text)
        if not isinstance(raw_out, dict):
            raise HTTPException(status_code=500, detail="Unexpected without_jd hybrid response shape.")
        if raw_out.get("error"):
            raise HTTPException(status_code=400, detail=str(raw_out["error"]))
        return _to_analyze_response(raw_out)

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("LLM validation failed in /analyse/general: %s", str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /analyse/general: %s", str(exc))
        raise HTTPException(status_code=500, detail="Unable to process resume analysis right now.") from exc
