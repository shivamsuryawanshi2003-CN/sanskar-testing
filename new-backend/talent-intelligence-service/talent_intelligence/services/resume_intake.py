# AI assisted development
"""Shared resume loading and validity checks for general, with-role, with-jd, and without_jd flows."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .resume_extract import ResumeExtractError, extract_resume_text

# Align with AnalyzeRequest.resume_text and LLM "not a resume" copy.
MIN_RESUME_TEXT_LENGTH = 20
NOT_A_RESUME_MESSAGE = "This document does not appear to be a resume. No ATS score will be generated."
TOO_SHORT_MESSAGE = "Resume text is too short or empty after extraction."


class ResumeValidationError(Exception):
    """Raised when extracted text does not look like a resume (structure check)."""

    def __init__(self, message: str = NOT_A_RESUME_MESSAGE) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ResumeStructureAssessment:
    """Matches product rule: invalid if two or more of the four facets are missing."""

    contact: bool
    skills: bool
    experience: bool
    education: bool

    @property
    def present_count(self) -> int:
        return sum((self.contact, self.skills, self.experience, self.education))

    @property
    def is_valid(self) -> bool:
        # "If ANY TWO OR MORE of these are missing" => need at least 3 of 4 present.
        return self.present_count >= 3


def assess_resume_structure(text: str) -> ResumeStructureAssessment:
    """Heuristic facet detection (same signals as Section 1–3 prompts)."""
    t = (text or "").strip()
    lower = t.lower()

    has_contact = bool(
        re.search(r"[\w.+-]+@[\w.-]+\.[\w.-]+", t)
        or re.search(r"\+?\d[\d\s().-]{8,}\d", t)
    )
    has_skills = any(
        k in lower
        for k in (
            "skills",
            "technical skills",
            "competencies",
            "technologies",
            "tech stack",
            "core skills",
        )
    )
    has_experience = any(
        k in lower
        for k in (
            "experience",
            "employment",
            "work history",
            "professional experience",
            "work experience",
            "career",
            "internship",
        )
    )
    has_education = any(
        k in lower
        for k in (
            "education",
            "academic",
            "university",
            "college",
            "bachelor",
            "master",
            "phd",
            "b.s.",
            "m.s.",
            "b.tech",
            "m.tech",
            "degree",
        )
    )
    return ResumeStructureAssessment(
        contact=has_contact,
        skills=has_skills,
        experience=has_experience,
        education=has_education,
    )


def is_valid_resume_text(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < MIN_RESUME_TEXT_LENGTH:
        return False
    return assess_resume_structure(t).is_valid


def require_valid_resume_text(text: str) -> str:
    """Return stripped text or raise ResumeValidationError."""
    t = (text or "").strip()
    if len(t) < MIN_RESUME_TEXT_LENGTH:
        raise ResumeValidationError(TOO_SHORT_MESSAGE)
    if not assess_resume_structure(t).is_valid:
        raise ResumeValidationError(NOT_A_RESUME_MESSAGE)
    return t


def load_resume_text_from_bytes(filename: str, data: bytes) -> str:
    """Extract text from PDF/DOCX bytes, then apply shared validity rules."""
    raw = extract_resume_text(filename, data)
    return require_valid_resume_text(raw)
