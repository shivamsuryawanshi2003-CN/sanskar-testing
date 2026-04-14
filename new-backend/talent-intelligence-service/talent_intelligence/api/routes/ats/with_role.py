# AI assisted development
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from talent_intelligence.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from talent_intelligence.services.analyzer import analyze_resume
from talent_intelligence.services.resume_intake import ResumeValidationError

from .common import ANALYZE_RESPONSE_EXAMPLE, extract_uploaded_resume, logger

router = APIRouter()


@router.post(
    "/analyse/with-role",
    response_model=AnalyzeResponse,
    summary="Upload resume file and analyze against selected role only",
    response_description="ATS analysis output in required format",
    responses={
        200: {
            "description": "ATS output format",
            "content": {"application/json": {"example": ANALYZE_RESPONSE_EXAMPLE}},
        }
    },
)
async def analyse_with_role(
    file: UploadFile = File(..., description="Resume file (.pdf or .docx only)."),
    role: str = Form(..., description="Role ID or role title."),
    job_description: str = Form(
        default="",
        description="Optional pasted JD; when set, scoring matches /analyse/with-jd (catalog role + JD).",
    ),
    additional_context: str = Form(default="", description="Optional extra resume context."),
) -> AnalyzeResponse:
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
        logger.warning("Business validation failed in /analyse/with-role: %s", str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /analyse/with-role: %s", str(exc))
        raise HTTPException(status_code=500, detail="Unable to process resume analysis right now.") from exc
