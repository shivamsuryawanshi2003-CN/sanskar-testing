# AI assisted development
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from talent_intelligence.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from talent_intelligence.services.analyzer import analyze_resume
from talent_intelligence.services.resume_intake import ResumeValidationError

from .common import ANALYZE_RESPONSE_EXAMPLE, extract_uploaded_resume, logger

router = APIRouter()


@router.post(
    "/analyse/with-jd",
    response_model=AnalyzeResponse,
    summary="Upload resume file and analyze with role plus JD",
    response_description="ATS analysis output in required format",
    responses={
        200: {
            "description": "ATS output format",
            "content": {"application/json": {"example": ANALYZE_RESPONSE_EXAMPLE}},
        }
    },
)
async def analyse_with_jd(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx only)."),
    role: str = Form(..., description="Role ID or role title."),
    job_description: str = Form(..., description="JD text (required for with-jd)."),
    additional_context: str = Form(default="", description="Optional extra resume context."),
) -> AnalyzeResponse:
    if not job_description.strip():
        raise HTTPException(status_code=422, detail="job_description is required for /analyse/with-jd.")
    try:
        resume_text = await extract_uploaded_resume(file)
        payload = AnalyzeRequest(
            resume_text=resume_text,
            role=role,
            job_description=job_description,
            additional_context=additional_context,
        )
        return await run_in_threadpool(analyze_resume, payload)
    except HTTPException:
        raise
    except ResumeValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except ValueError as exc:
        msg = str(exc)
        logger.warning("Business validation failed in /analyse/with-jd: %s", msg)
        # LLM JD validation (invalid / irrelevant job description)
        if "Irrelevant" in msg or "Job Description" in msg or "invalid" in msg.lower():
            raise HTTPException(status_code=400, detail=msg) from exc
        raise HTTPException(status_code=503, detail=msg) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /analyse/with-jd: %s", str(exc))
        raise HTTPException(status_code=500, detail="Unable to process resume analysis right now.") from exc
