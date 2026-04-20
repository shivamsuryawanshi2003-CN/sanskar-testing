from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from talent_intelligence.schemas.analysis import AnalyzeRequest, UpgradeSuggestionResponse
from talent_intelligence.services.analyzer import analyze_resume
from talent_intelligence.services.ats.analysis import llm_general_score_only
from talent_intelligence.services.resume_extract import extract_resume_text
from talent_intelligence.services.suggestion import upgrade_resume_with_gpt35
from .common import logger

router = APIRouter()


def _resume_text_from_upload(file: UploadFile) -> str:
    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must include a filename.")
    raw = file.file.read()
    try:
        return extract_resume_text(filename, raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/analyse/upgrade",
    response_model=UpgradeSuggestionResponse,
    summary="Generate a resume upgrade JSON using ATS analysis context",
    response_description="Structured, validated resume upgrade suggestions.",
)
async def analyse_upgrade(
    file: UploadFile = File(None, description="Resume file (.pdf or .docx only). Optional if resume_text provided."),
    resume_text: str = Form("", description="Resume text. Used when file is not provided."),
    choice_id: int = Form(..., description="Choice type for upgrade: 1=general, 2=role, 3=JD-only."),
    role: str = Form("", description="Role ID or title for role-based upgrades."),
    job_description: str = Form("", description="Pasted job description for JD-based upgrades."),
    additional_context: str = Form("", description="Optional extra resume context."),
) -> UpgradeSuggestionResponse:
    if not resume_text.strip() and file is None:
        raise HTTPException(status_code=422, detail="Provide either resume_text or resume file.")

    if choice_id not in (1, 2, 3):
        raise HTTPException(status_code=422, detail="choice_id must be 1, 2, or 3.")

    try:
        if not resume_text.strip():
            resume_text = await run_in_threadpool(_resume_text_from_upload, file)

        if choice_id == 1:
            ats_report = llm_general_score_only(resume_text=resume_text)
            context_data = ""
        else:
            if choice_id == 2 and not role.strip():
                raise HTTPException(status_code=422, detail="Role is required for choice_id 2.")
            if choice_id == 3 and not job_description.strip():
                raise HTTPException(status_code=422, detail="job_description is required for choice_id 3.")

            payload = AnalyzeRequest(
                resume_text=resume_text,
                role=role if choice_id == 2 else "",
                job_description=job_description,
                additional_context=additional_context,
            )
            ats_report = await run_in_threadpool(analyze_resume, payload)
            context_data = job_description.strip() if choice_id == 3 else role.strip()

        upgraded = upgrade_resume_with_gpt35(
            resume_text=resume_text,
            ats_report=ats_report,
            choice_id=choice_id,
            context_data=context_data,
        )
        return UpgradeSuggestionResponse.model_validate(upgraded)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error in /analyse/upgrade: %s", str(exc))
        raise HTTPException(status_code=500, detail="Unable to generate resume upgrade right now.") from exc
