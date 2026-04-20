"""Deterministic ATS scoring engine for general, role, and JD flows."""

from __future__ import annotations

import re
from collections import Counter


MAX_ATS_SCORE = {
    "general": 72,
    "role": 80,
    "jd": 82,
}

_COMPONENT_WEIGHTS = {
    "general": {"FORMAT": 0.28, "SKILLS": 0.24, "EXPERIENCE": 0.34, "EDUCATION": 0.14},
    "role": {"FORMAT": 0.20, "SKILLS": 0.36, "EXPERIENCE": 0.31, "EDUCATION": 0.13},
    "jd": {"FORMAT": 0.18, "SKILLS": 0.40, "EXPERIENCE": 0.30, "EDUCATION": 0.12},
}

_STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "have",
    "in",
    "is",
    "it",
    "job",
    "of",
    "on",
    "or",
    "role",
    "that",
    "the",
    "this",
    "to",
    "using",
    "with",
    "work",
    "years",
}

_ACTION_VERBS = {
    "achieved",
    "automated",
    "built",
    "created",
    "delivered",
    "designed",
    "developed",
    "drove",
    "engineered",
    "executed",
    "implemented",
    "improved",
    "launched",
    "led",
    "optimized",
    "owned",
    "reduced",
    "scaled",
    "streamlined",
}

_WEAK_WORDS = {
    "assisted": ["supported", "contributed to", "helped deliver"],
    "handled": ["resolved", "owned", "delivered"],
    "helped": ["supported", "enabled", "contributed to"],
    "managed": ["led", "owned", "directed"],
    "multiple": ["several", "key", "cross-functional"],
    "responsible": ["owned", "delivered", "implemented"],
    "several": ["multiple", "key", "distinct"],
    "support": ["enable", "improve", "resolve"],
    "various": ["specific", "targeted", "distinct"],
    "worked": ["built", "delivered", "executed"],
}

_SECTION_HEADERS = {
    "summary": ("summary", "professional summary", "profile", "objective"),
    "skills": ("skills", "technical skills", "core skills", "tools", "competencies"),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "internship",
    ),
    "projects": ("projects", "project experience"),
    "education": ("education", "qualifications", "academic background"),
    "certifications": ("certifications", "certification", "awards", "achievements"),
}

_TECH_KEYWORDS = {
    "airflow",
    "api",
    "aws",
    "azure",
    "ci/cd",
    "css",
    "dashboard",
    "data analysis",
    "data modeling",
    "django",
    "docker",
    "etl",
    "excel",
    "fastapi",
    "figma",
    "firebase",
    "git",
    "html",
    "javascript",
    "kubernetes",
    "machine learning",
    "microservices",
    "mongodb",
    "mysql",
    "next.js",
    "node.js",
    "pandas",
    "postgresql",
    "power bi",
    "python",
    "pytorch",
    "react",
    "redis",
    "rest api",
    "spark",
    "sql",
    "statistics",
    "tableau",
    "tensorflow",
    "terraform",
    "typescript",
}

_SOFT_KEYWORDS = {
    "communication",
    "collaboration",
    "leadership",
    "mentoring",
    "ownership",
    "presentation",
    "problem solving",
    "stakeholder management",
    "teamwork",
}

_GENERIC_TARGET_WORDS = {
    "ability",
    "candidate",
    "candidates",
    "clearly",
    "consistent",
    "deliver",
    "demonstrates",
    "documentation",
    "execution",
    "habit",
    "habits",
    "ideal",
    "impact",
    "measurable",
    "prior",
    "problem",
    "results",
    "roles",
    "solve",
    "solving",
    "strong",
    "team",
    "teams",
}

_KEYWORD_LIST_MARKERS = (
    "required skills",
    "required skill",
    "skills include",
    "tools such as",
    "must have",
    "must-have",
    "nice to have",
    "nice-to-have",
    "experience with",
    "proficient in",
    "proficiency in",
)

_BULLET_MARKERS = ("- ", "* ", "• ")


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z0-9+#./-]*", text.lower())


def _stem_token(token: str) -> str:
    lowered = token.lower()
    for prefix, stem in (
        ("analy", "analy"),
        ("communicat", "communicat"),
        ("collaborat", "collaborat"),
        ("experiment", "experiment"),
        ("forecast", "forecast"),
        ("report", "report"),
        ("visualiz", "visualiz"),
    ):
        if lowered.startswith(prefix):
            return stem
    for suffix in ("ations", "ation", "ments", "ment", "ships", "ship", "ingly", "edly", "ing", "ed", "ics", "ies", "es", "s"):
        if lowered.endswith(suffix) and len(lowered) - len(suffix) >= 4:
            return lowered[:-len(suffix)]
    return lowered


def _keyword_matches_text(keyword: str, text: str) -> bool:
    lowered = text.lower()
    if keyword in lowered:
        return True
    keyword_tokens = [token for token in _tokenize(keyword) if not token.isdigit()]
    if not keyword_tokens:
        return False
    text_stems = {_stem_token(token) for token in _tokenize(lowered)}
    return all(_stem_token(token) in text_stems for token in keyword_tokens)


def _normalize_keyword_phrase(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9+#./\-\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip(" ,.-")


def _is_generic_target_keyword(phrase: str) -> bool:
    tokens = [token for token in _tokenize(phrase) if not token.isdigit()]
    if not tokens:
        return True
    if len(tokens) == 1 and len(tokens[0]) < 4:
        return True
    return all(token in _STOPWORDS or token in _GENERIC_TARGET_WORDS for token in tokens)


def _extract_listed_keywords(text: str) -> list[str]:
    found: set[str] = set()
    for marker in sorted(_KEYWORD_LIST_MARKERS, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(marker)}\b\s*[:\-]?\s*(.+?)(?:[.;]\s|$)", re.IGNORECASE)
        for match in pattern.finditer(text):
            segment = match.group(1).strip()
            for piece in re.split(r",|/|\band\b|\bor\b", segment, flags=re.IGNORECASE):
                candidate = _normalize_keyword_phrase(piece)
                if candidate and not _is_generic_target_keyword(candidate):
                    found.add(candidate)
    return sorted(found)


def _date_regex() -> re.Pattern[str]:
    return re.compile(
        r"(?:19|20)\d{2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+(?:19|20)\d{2}",
        re.IGNORECASE,
    )


def _has_contact(text: str) -> bool:
    has_email = bool(re.search(r"[\w.\-]+@[\w.\-]+\.\w+", text))
    has_phone = bool(re.search(r"\+?\d[\d ()-]{8,}\d", text))
    return has_email or has_phone


def _detect_headers(lines: list[str]) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        lowered = re.sub(r"[:\-]+$", "", line.lower()).strip()
        for name, candidates in _SECTION_HEADERS.items():
            if lowered in candidates:
                hits.append((name, index))
                break
    return hits


def _section_map(lines: list[str]) -> dict[str, str]:
    headers = _detect_headers(lines)
    sections: dict[str, str] = {}
    if not headers:
        return sections
    for index, (name, start) in enumerate(headers):
        end = headers[index + 1][1] if index + 1 < len(headers) else len(lines)
        body = "\n".join(lines[start + 1 : end]).strip()
        if body:
            sections[name] = body
    return sections


def _collect_target_keywords(
    *,
    job_description: str,
    role_title: str,
    role_keywords: list[str] | None,
    role_summary: str = "",
) -> dict[str, list[str]]:
    title_terms = [
        token
        for token in _tokenize(role_title.replace("/", " "))
        if len(token) >= 3 and token not in _STOPWORDS and token not in _GENERIC_TARGET_WORDS
    ]

    hard_keywords = {
        normalized
        for normalized in (_normalize_keyword_phrase(kw) for kw in (role_keywords or []))
        if normalized and not _is_generic_target_keyword(normalized)
    }
    target_corpus = "\n".join(part for part in (job_description, role_summary, role_title) if part).lower()
    jd_lower = target_corpus
    for phrase in _extract_listed_keywords(job_description):
        hard_keywords.add(phrase)
    for phrase in _extract_listed_keywords(role_summary):
        hard_keywords.add(phrase)
    for phrase in _TECH_KEYWORDS:
        if phrase in jd_lower:
            hard_keywords.add(phrase)

    jd_tokens = Counter(
        token
        for token in _tokenize(target_corpus)
        if len(token) >= 4 and token not in _STOPWORDS and token not in _GENERIC_TARGET_WORDS and not token.isdigit()
    )
    seeded_tokens = {token for keyword in hard_keywords for token in _tokenize(keyword)}
    for token, count in jd_tokens.most_common(24):
        if token in _SOFT_KEYWORDS or _is_generic_target_keyword(token):
            continue
        if count >= 2 or token in seeded_tokens or token in _TECH_KEYWORDS:
            hard_keywords.add(token)

    soft_keywords = {kw for kw in _SOFT_KEYWORDS if kw in jd_lower}
    return {
        "title_terms": sorted(set(title_terms)),
        "hard_keywords": sorted(hard_keywords),
        "soft_keywords": sorted(soft_keywords),
    }


def _extract_resume_skills(resume_text: str, sections: dict[str, str]) -> list[str]:
    resume_lower = resume_text.lower()
    skills = {kw for kw in _TECH_KEYWORDS if kw in resume_lower}
    skill_section = sections.get("skills", "").lower()
    for token in _tokenize(skill_section):
        if len(token) >= 3 and token not in _STOPWORDS:
            skills.add(token)
    return sorted(skills)


def _extract_soft_signals(resume_text: str) -> list[str]:
    lowered = resume_text.lower()
    return sorted({kw for kw in _SOFT_KEYWORDS if kw in lowered})


def _metric_lines(lines: list[str]) -> list[str]:
    metric_pattern = re.compile(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*|\b\d+[kKmM]?\b")
    return [line for line in lines if metric_pattern.search(line)]


def _experience_year_span(text: str) -> int:
    years = sorted({int(year) for year in re.findall(r"(?:19|20)\d{2}", text)})
    if len(years) < 2:
        return 0
    return max(0, min(12, years[-1] - years[0]))


def _repeated_weak_words(text: str, target_keywords: list[str]) -> dict[str, int]:
    counts = Counter(_tokenize(text))
    excluded = {kw.lower() for kw in target_keywords} | _TECH_KEYWORDS
    repeated: dict[str, int] = {}
    for word in _WEAK_WORDS:
        if word in excluded:
            continue
        count = counts.get(word, 0)
        if count >= 3:
            repeated[word] = count
    return dict(sorted(repeated.items(), key=lambda item: (-item[1], item[0]))[:5])


def _replacement_suggestions(repeated: dict[str, int]) -> list[str]:
    lines: list[str] = []
    for word, count in repeated.items():
        a, b, c = _WEAK_WORDS.get(word, ["improved", "delivered", "built"])
        lines.append(f"{count} times: {word}\ntry replacing with\n{a}\n{b}\n{c}")
    return lines


def _section_keyword_coverage(section_text: str, keywords: list[str]) -> int:
    if not keywords:
        return 0
    matched = sum(1 for keyword in keywords if _keyword_matches_text(keyword, section_text))
    return int(round((matched / len(keywords)) * 100))


def _normalize_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _clamp_overall_score(value: int, mode: str) -> int:
    return max(0, min(MAX_ATS_SCORE[mode], value))


def _apply_market_calibration(
    *,
    raw_score: int,
    mode: str,
    has_contact: bool,
    has_summary: bool,
    has_skills: bool,
    has_experience_dates: bool,
    metric_count: int,
    repeated_words: dict[str, int],
    hard_keyword_coverage: float,
) -> int:
    score = int(raw_score)

    if not has_contact:
        score -= 4
    if not has_summary:
        score -= 4
    if not has_skills:
        score -= 6
    if not has_experience_dates:
        score -= 5

    if metric_count == 0:
        score -= 9
    elif metric_count == 1:
        score -= 5

    if repeated_words:
        score -= min(7, len(repeated_words) * 2)

    if mode == "general":
        if metric_count == 0 and (not has_summary or not has_skills):
            score = min(score, 52)
        elif metric_count == 0:
            score = min(score, 56)
        elif metric_count == 1:
            score = min(score, 64)
        elif metric_count == 2:
            score = min(score, 71)
        if repeated_words:
            score = min(score, 70)
    else:
        if hard_keyword_coverage < 0.20:
            score = min(score, 56 if mode == "jd" else 59)
        elif hard_keyword_coverage < 0.35:
            score = min(score, 64 if mode == "jd" else 67)
        elif hard_keyword_coverage < 0.50:
            score = min(score, 71 if mode == "jd" else 74)
        elif hard_keyword_coverage < 0.65:
            score = min(score, 77 if mode == "jd" else 79)

    return _clamp_overall_score(_normalize_score(score), mode)


def _format_quality(lines: list[str], sections: dict[str, str], has_contact: bool) -> tuple[int, list[str]]:
    issues: list[str] = []
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    word_count = len(_tokenize("\n".join(non_empty_lines)))
    bullet_lines = [line for line in non_empty_lines if line.startswith(_BULLET_MARKERS)]
    date_hits = len(_date_regex().findall(sections.get("experience", "")))
    long_lines = sum(1 for line in non_empty_lines if len(line) > 180)
    divider_like = sum(1 for line in non_empty_lines if line.count("|") >= 2 or "	" in line)

    structure_hits = int(has_contact)
    structure_hits += sum(1 for name in ("summary", "skills", "experience", "education") if sections.get(name))
    structure_hits += int(bool(sections.get("projects") or sections.get("certifications")))

    bullet_ratio = _safe_div(len(bullet_lines), max(1, len(non_empty_lines)))

    score = 16
    if has_contact:
        score += 14
    else:
        issues.append("Contact details are missing or unclear.")

    if sections.get("summary"):
        score += 8
    else:
        issues.append("Professional summary section is missing.")

    if sections.get("skills"):
        score += 12
    else:
        issues.append("Skills section is missing.")

    if sections.get("experience"):
        score += 18
    else:
        issues.append("Experience section is missing.")

    if sections.get("education"):
        score += 10
    else:
        issues.append("Education section is missing.")

    if date_hits >= 1:
        score += 7
    else:
        issues.append("Experience dates are not easy to detect.")

    if bullet_ratio >= 0.18:
        score += 8
    elif bullet_lines:
        score += 4
    elif sections.get("experience"):
        issues.append("Experience bullets are not clearly separated.")

    if 320 <= word_count <= 780:
        score += 7
    elif 220 <= word_count < 320 or 780 < word_count <= 950:
        score += 3
    elif word_count < 220:
        issues.append("Resume content is too thin for strong ATS confidence.")
    else:
        issues.append("Resume length may reduce clarity for ATS and recruiters.")

    if long_lines:
        score -= min(6, long_lines * 2)
        issues.append("Some bullets or lines are too long and may hurt scan clarity.")
    if divider_like:
        score -= min(6, divider_like * 2)
        issues.append("Layout appears to rely on separators or tabular formatting in places.")
    if not sections.get("projects") and not sections.get("certifications"):
        score -= 3
        issues.append("Supporting proof points like projects or certifications are limited.")

    if word_count < 320:
        score = min(score, 74)
    if structure_hits < 5:
        score = min(score, 70)
    if structure_hits < 4:
        score = min(score, 64)
    if not bullet_lines:
        score = min(score, 62)
    if not has_contact or not sections.get("experience"):
        score = min(score, 58)

    return _normalize_score(max(18, min(score, 86))), issues


def _experience_quality(lines: list[str], sections: dict[str, str]) -> tuple[int, list[str], list[str]]:
    issues: list[str] = []
    strengths: list[str] = []
    experience_text = f"{sections.get('experience', '')}\n{sections.get('projects', '')}".strip()
    if not experience_text:
        return 15, ["No clear experience or project evidence was detected."], strengths

    experience_lines = [line.strip("•- ").strip() for line in experience_text.splitlines() if line.strip()]
    metrics = _metric_lines(experience_lines)
    action_hits = sum(
        1
        for line in experience_lines
        if any(line.lower().startswith(verb) for verb in _ACTION_VERBS)
    )
    unique_metric_tokens = {
        token
        for token in re.findall(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*|\b\d+[kKmM]?\b", experience_text)
    }
    year_span = _experience_year_span(experience_text)

    score = 20
    score += 15 if len(experience_lines) >= 3 else 5
    score += min(18, len(metrics) * 6)
    score += min(14, action_hits * 3)
    score += 8 if sections.get("projects") else 0
    score += 6 if _date_regex().search(experience_text) else 0
    score += min(6, len(unique_metric_tokens))
    score += min(6, year_span)

    if metrics:
        strengths.append("Experience includes measurable outcomes.")
    else:
        issues.append("Experience bullets need more quantified results.")

    if action_hits == 0:
        issues.append("Experience bullets should start with stronger action verbs.")
    else:
        strengths.append("Action-oriented bullet phrasing is present.")

    if not _date_regex().search(experience_text):
        issues.append("Add clearer dates to work experience entries.")
    elif year_span >= 3:
        strengths.append("Experience timeline shows sustained professional progression.")

    if not metrics:
        score = min(score, 66)
    elif len(metrics) == 1:
        score = min(score, 74)
    return _normalize_score(score), issues, strengths


def _education_quality(sections: dict[str, str], lines: list[str]) -> tuple[int, list[str], list[str]]:
    issues: list[str] = []
    strengths: list[str] = []
    education_text = sections.get("education", "")
    cert_text = sections.get("certifications", "")

    score = 10
    if education_text:
        score += 55
        strengths.append("Education is visible to ATS parsers.")
        if any(token in education_text.lower() for token in ("bachelor", "master", "degree", "b.tech", "b.sc", "mba")):
            score += 15
    else:
        issues.append("Education section is missing.")

    if cert_text:
        score += 15
        strengths.append("Certifications or achievements are explicitly listed.")
    elif any("cert" in line.lower() for line in lines):
        score += 8

    return _normalize_score(score), issues, strengths


def _skills_quality(
    *,
    mode: str,
    sections: dict[str, str],
    resume_text: str,
    resume_skills: list[str],
    target: dict[str, list[str]],
) -> tuple[int, list[str], list[str], list[str]]:
    issues: list[str] = []
    strengths: list[str] = []
    missing_keywords: list[str] = []

    skill_section = sections.get("skills", "")
    summary_section = sections.get("summary", "")
    experience_section = f"{sections.get('experience', '')}\n{sections.get('projects', '')}".strip()
    lowered_resume = resume_text.lower()

    score = 12
    if skill_section:
        score += 12
        strengths.append("A dedicated skills section helps ATS parsing.")
    else:
        issues.append("Add a dedicated skills section for ATS-friendly keyword indexing.")

    score += min(12, len(resume_skills) * 2)

    title_terms = target["title_terms"]
    hard_keywords = target["hard_keywords"]
    soft_keywords = target["soft_keywords"]

    if mode == "general":
        skill_depth = len(resume_skills)
        if skill_depth >= 8:
            score += 18
            strengths.append("The resume includes a broad enough technical keyword base for general screening.")
        elif skill_depth >= 5:
            score += 10
        else:
            issues.append("Add more role-relevant technologies and tools to improve keyword depth.")
        spread_hits = sum(
            1 for section_text in (summary_section, skill_section, experience_section)
            if any(skill in section_text.lower() for skill in resume_skills[:12])
        )
        score += min(8, spread_hits * 3)
        return _normalize_score(min(score, 84)), issues, strengths, missing_keywords

    title_hits = sum(1 for term in title_terms if _keyword_matches_text(term, lowered_resume))
    hard_hits = [keyword for keyword in hard_keywords if _keyword_matches_text(keyword, lowered_resume)]
    missing_keywords = [keyword for keyword in hard_keywords if not _keyword_matches_text(keyword, lowered_resume)][:12]

    overall_cov = _safe_div(len(hard_hits), len(hard_keywords))
    skill_cov = _safe_div(sum(1 for keyword in hard_keywords if _keyword_matches_text(keyword, skill_section)), len(hard_keywords))
    exp_cov = _safe_div(sum(1 for keyword in hard_keywords if _keyword_matches_text(keyword, experience_section)), len(hard_keywords))
    summary_cov = _safe_div(sum(1 for keyword in hard_keywords if _keyword_matches_text(keyword, summary_section)), len(hard_keywords))

    score += min(12, title_hits * 4)
    score += int(round(overall_cov * 34))
    score += int(round(skill_cov * 10))
    score += int(round(exp_cov * 12))
    score += int(round(summary_cov * 8))

    if title_terms and title_hits == 0:
        issues.append("Target role phrasing is not visible in the summary or experience sections.")
    else:
        strengths.append("Target role wording appears in the resume.")

    if overall_cov >= 0.6:
        strengths.append("Important target keywords are already present across the resume.")
    elif overall_cov >= 0.35:
        strengths.append("Some target keywords are present, but deeper alignment is still possible.")
        issues.append("Several important target keywords are still missing from the resume.")
    else:
        issues.append("Core target keywords are missing from the resume.")

    if exp_cov < 0.2 and hard_keywords:
        issues.append("Important target keywords are not yet backed by experience or project evidence.")

    if soft_keywords and not any(_keyword_matches_text(keyword, lowered_resume) for keyword in soft_keywords):
        issues.append("Relevant soft-skill language from the target context is still missing.")

    return _normalize_score(min(score, 94)), issues, strengths, missing_keywords


def _parsing_issue_count(format_issues: list[str], sections: dict[str, str], has_contact: bool) -> int:
    count = 0
    if not has_contact:
        count += 1
    if not sections.get("skills"):
        count += 1
    if not sections.get("experience"):
        count += 1
    if not _date_regex().search(sections.get("experience", "")):
        count += 1
    return count


def _spelling_or_clarity_issue_count(lines: list[str]) -> int:
    issues = 0
    if any(len(line) > 220 for line in lines):
        issues += 1
    if any(".." in line or "??" in line for line in lines):
        issues += 1
    return issues


def _issue_text(count: int) -> str:
    if count <= 0:
        return "No issues"
    if count == 1:
        return "1 issue"
    return f"{count} issues"


def _section_missing_counts(sections: dict[str, str], missing_keywords: list[str]) -> dict[str, int]:
    if not missing_keywords:
        return {"SUMMARY": 0, "SKILLS": 0, "EXPERIENCE": 0, "PROJECTS": 0}

    summary_count = sum(1 for kw in missing_keywords if not _keyword_matches_text(kw, sections.get("summary", "")))
    experience_count = sum(
        1 for kw in missing_keywords if not _keyword_matches_text(kw, f"{sections.get('experience', '')}\n{sections.get('projects', '')}")
    )
    skills_count = sum(1 for kw in missing_keywords if not _keyword_matches_text(kw, sections.get("skills", "")))
    projects_count = sum(1 for kw in missing_keywords if not _keyword_matches_text(kw, sections.get("projects", "")))
    return {
        "SUMMARY": min(5, summary_count),
        "SKILLS": min(5, skills_count),
        "EXPERIENCE": min(5, experience_count),
        "PROJECTS": min(5, projects_count),
    }


def _general_gap_lines(
    *,
    sections: dict[str, str],
    metric_count: int,
    resume_skills: list[str],
) -> list[str]:
    lines: list[str] = []
    if not sections.get("summary"):
        lines.append("Add a professional summary so ATS parsers and recruiters see your target profile quickly.")
    if not sections.get("skills"):
        lines.append("Add a skills section so tools and technologies are indexed cleanly.")
    if metric_count == 0:
        lines.append("Add measurable results to experience bullets to strengthen credibility.")
    if len(resume_skills) < 6:
        lines.append("Add more concrete tools, platforms, and technical skills to improve keyword depth.")
    if not lines:
        lines.append("Refine bullet language and remove weak filler to improve clarity.")
    return lines[:3]


def _summary_text(
    *,
    mode: str,
    overall_score: int,
    top_strengths: list[str],
    top_gaps: list[str],
    target: dict[str, list[str]],
) -> str:
    context_label = {
        "general": "overall ATS quality",
        "role": "the selected role",
        "jd": "the pasted job description",
    }[mode]
    strengths = ", ".join(top_strengths[:3]).lower() if top_strengths else "basic resume structure"
    gaps = ", ".join(top_gaps[:3]).lower() if top_gaps else "keyword targeting and quantified impact"
    keyword_note = ""
    if target["hard_keywords"]:
        keyword_note = f" Target coverage was checked against {len(target['hard_keywords'])} important context keywords."
    return (
        f"This resume currently scores {overall_score} out of 100 for {context_label}. "
        f"Strongest signals: {strengths}. "
        f"Biggest gaps: {gaps}.{keyword_note}"
    )


def _ranked_suggestions(
    *,
    mode: str,
    format_issues: list[str],
    skills_issues: list[str],
    experience_issues: list[str],
    missing_keywords: list[str],
    repeated_words: dict[str, int],
    metric_count: int,
) -> list[str]:
    suggestions: list[str] = []

    if format_issues:
        suggestions.append(format_issues[0])
    if missing_keywords:
        label = "target keywords" if mode != "general" else "role-relevant keywords"
        suggestions.append(f"Add missing {label} such as {', '.join(missing_keywords[:4])}.")
    if metric_count == 0:
        suggestions.append("Rewrite the strongest experience bullets with measurable outcomes such as %, time saved, scale, or revenue.")
    if experience_issues:
        suggestions.append(experience_issues[0])
    if repeated_words:
        suggestions.append(
            f"Reduce repeated weak words like {', '.join(list(repeated_words)[:3])} and replace them with sharper action verbs."
        )
    if skills_issues:
        suggestions.append(skills_issues[0])

    deduped: list[str] = []
    for suggestion in suggestions:
        if suggestion not in deduped:
            deduped.append(suggestion)
    return deduped[:4]


def _achievements(lines: list[str]) -> list[str]:
    output: list[str] = []
    header_names = {
        candidate
        for candidates in _SECTION_HEADERS.values()
        for candidate in candidates
    }
    for line in lines:
        lowered = line.lower()
        normalized = re.sub(r"[:\-]+$", "", lowered).strip()
        if normalized in header_names:
            continue
        if any(token in lowered for token in ("cert", "award", "scholarship")):
            output.append(line)
            continue
        if re.search(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*|\b\d+[kKmM]?\b", line) and any(
            token in lowered for token in ("improv", "reduc", "increase", "grew", "saved", "built", "launched")
        ):
            output.append(line)
    return output[:4]


def _strength_lines(
    *,
    format_strengths: list[str],
    skill_strengths: list[str],
    experience_strengths: list[str],
    education_strengths: list[str],
) -> list[str]:
    ordered = format_strengths + skill_strengths + experience_strengths + education_strengths
    deduped: list[str] = []
    for item in ordered:
        if item not in deduped:
            deduped.append(item)
    return deduped[:4]


def _build_mode(job_description: str, role_title: str) -> str:
    if job_description.strip():
        return "jd"
    if role_title.strip():
        return "role"
    return "general"


def analyze_resume_heuristically(
    *,
    resume_text: str,
    job_description: str = "",
    role_title: str = "",
    role_keywords: list[str] | None = None,
    role_summary: str = "",
    additional_context: str = "",
) -> dict:
    mode = _build_mode(job_description, role_title)
    merged_text = resume_text if not additional_context.strip() else f"{resume_text}\n\nAdditional Context:\n{additional_context.strip()}"
    lines = _clean_lines(merged_text)

    if not lines:
        return {
            "ATS_Score": 0,
            "Summary": "No readable resume text was detected.",
            "Resume_Health": {
                "Content_Percent": 0,
                "ATS_Parse_Rate": "1 issue",
                "Quantifying_Impact": "1 issue",
                "Repetition": "No issues",
                "Spelling_Grammar": "1 issue",
            },
            "Suggestions_for_Improvement": ["Upload a resume with readable text content."],
            "Score_Breakdown": {"FORMAT": 0, "SKILLS": 0, "EXPERIENCE": 0, "EDUCATION": 0},
            "Missing_Keywords": {"SUMMARY": 0, "SKILLS": 0, "EXPERIENCE": 0, "PROJECTS": 0},
            "Missing_Keyword_List": [],
            "Achievements_or_Certifications": [],
            "Resume_Strength": [],
            "Key_Skills": [],
            "Repeated_Word_Frequency": {},
            "Word_Replacement_Suggestions": [],
        }

    sections = _section_map(lines)
    has_contact = _has_contact(merged_text)
    if sum(1 for name in ("skills", "experience", "education") if sections.get(name)) + int(has_contact) < 2:
        return {
            "ATS_Score": 0,
            "Summary": "The uploaded document does not look like a complete resume because core ATS sections are missing.",
            "Resume_Health": {
                "Content_Percent": min(35, len(_tokenize(merged_text)) // 4),
                "ATS_Parse_Rate": "3 issues",
                "Quantifying_Impact": "1 issue",
                "Repetition": "No issues",
                "Spelling_Grammar": "1 issue",
            },
            "Suggestions_for_Improvement": [],
            "Score_Breakdown": {"FORMAT": 0, "SKILLS": 0, "EXPERIENCE": 0, "EDUCATION": 0},
            "Missing_Keywords": {"SUMMARY": 0, "SKILLS": 0, "EXPERIENCE": 0, "PROJECTS": 0},
            "Missing_Keyword_List": [],
            "Achievements_or_Certifications": [],
            "Resume_Strength": [],
            "Key_Skills": [],
            "Repeated_Word_Frequency": {},
            "Word_Replacement_Suggestions": [],
        }

    target = _collect_target_keywords(
        job_description=job_description,
        role_title=role_title,
        role_keywords=role_keywords,
        role_summary=role_summary,
    )
    target_keywords = target["title_terms"] + target["hard_keywords"] + target["soft_keywords"]
    resume_skills = _extract_resume_skills(merged_text, sections)
    soft_signals = _extract_soft_signals(merged_text)
    repeated_words = _repeated_weak_words(merged_text, target_keywords)
    metric_count = len(_metric_lines(lines))
    content_percent = min(100, max(35, int(round(min(900, len(_tokenize(merged_text))) / 9))))

    format_score, format_issues = _format_quality(lines, sections, has_contact)
    experience_score, experience_issues, experience_strengths = _experience_quality(lines, sections)
    education_score, education_issues, education_strengths = _education_quality(sections, lines)
    skills_score, skills_issues, skill_strengths, missing_keywords = _skills_quality(
        mode=mode,
        sections=sections,
        resume_text=merged_text,
        resume_skills=resume_skills,
        target=target,
    )

    format_strengths = []
    if has_contact:
        format_strengths.append("Contact details are present in an ATS-friendly format.")
    if sections.get("skills"):
        format_strengths.append("Standard section headings make the resume easier to parse.")
    if sections.get("experience") and _date_regex().search(sections.get("experience", "")):
        format_strengths.append("Experience entries include detectable dates.")

    weights = _COMPONENT_WEIGHTS[mode]
    weighted_score = (
        format_score * weights["FORMAT"]
        + skills_score * weights["SKILLS"]
        + experience_score * weights["EXPERIENCE"]
        + education_score * weights["EDUCATION"]
    )

    hard_keyword_hits = sum(1 for kw in target["hard_keywords"] if kw and _keyword_matches_text(kw, merged_text))
    hard_keyword_coverage = (hard_keyword_hits / max(1, len(target["hard_keywords"]))) if target["hard_keywords"] else 1.0

    penalty = 0
    if metric_count == 0:
        penalty += 8
    elif metric_count == 1:
        penalty += 4
    if repeated_words:
        penalty += min(6, len(repeated_words) * 2)
    if mode != "general":
        penalty += min(10, max(0, len(missing_keywords) - 1))
        if hard_keyword_coverage < 0.35:
            penalty += 5

    if mode == "general" and format_score >= 84 and (metric_count < 2 or len(sections) < 4):
        format_score = min(format_score, 78)

    overall_score = _apply_market_calibration(
        raw_score=_normalize_score(weighted_score - penalty),
        mode=mode,
        has_contact=has_contact,
        has_summary=bool(sections.get("summary")),
        has_skills=bool(sections.get("skills")),
        has_experience_dates=bool(_date_regex().search(sections.get("experience", ""))),
        metric_count=metric_count,
        repeated_words=repeated_words,
        hard_keyword_coverage=hard_keyword_coverage,
    )

    missing_counts = _section_missing_counts(sections, missing_keywords) if mode != "general" else {
        "SUMMARY": 0,
        "SKILLS": 0,
        "EXPERIENCE": 0,
        "PROJECTS": 0,
    }

    strengths = _strength_lines(
        format_strengths=format_strengths,
        skill_strengths=skill_strengths + ([f"Detected soft signals: {', '.join(soft_signals[:3])}."] if soft_signals else []),
        experience_strengths=experience_strengths,
        education_strengths=education_strengths,
    )

    suggestions = _ranked_suggestions(
        mode=mode,
        format_issues=format_issues,
        skills_issues=skills_issues,
        experience_issues=experience_issues,
        missing_keywords=missing_keywords,
        repeated_words=repeated_words,
        metric_count=metric_count,
    )

    parse_issue_count = _parsing_issue_count(format_issues, sections, has_contact)
    quant_issue_count = 0 if metric_count >= 2 else 1 if metric_count == 1 else 2
    repetition_issue_count = min(3, len(repeated_words))
    clarity_issue_count = _spelling_or_clarity_issue_count(lines)

    return {
        "ATS_Score": overall_score,
        "Summary": _summary_text(
            mode=mode,
            overall_score=overall_score,
            top_strengths=strengths,
            top_gaps=suggestions,
            target=target,
        ),
        "Resume_Health": {
            "Content_Percent": content_percent,
            "ATS_Parse_Rate": _issue_text(parse_issue_count),
            "Quantifying_Impact": _issue_text(quant_issue_count),
            "Repetition": _issue_text(repetition_issue_count),
            "Spelling_Grammar": _issue_text(clarity_issue_count),
        },
        "Suggestions_for_Improvement": suggestions,
        "Score_Breakdown": {
            "FORMAT": min(format_score, 82),
            "SKILLS": skills_score,
            "EXPERIENCE": experience_score,
            "EDUCATION": education_score,
        },
        "Missing_Keywords": missing_counts,
        "Missing_Keyword_List": missing_keywords[:12] if mode != "general" else [],
        "Achievements_or_Certifications": _achievements(lines),
        "Resume_Strength": strengths,
        "Key_Skills": sorted(set(resume_skills + target["title_terms"]))[:10],
        "Repeated_Word_Frequency": repeated_words,
        "Word_Replacement_Suggestions": _replacement_suggestions(repeated_words),
        "Scoring_Weights": {
            key: int(round(value * 100)) for key, value in weights.items()
        },
    }


def _experience_entries(lines: list[str], sections: dict[str, str]) -> list[dict[str, str]]:
    source = sections.get("experience") or sections.get("projects") or ""
    if not source:
        return []

    entries: list[dict[str, str]] = []
    source_lines = [line.strip("•- ").strip() for line in source.splitlines() if line.strip()]
    current_header = ""
    current_body: list[str] = []

    def _flush() -> None:
        nonlocal current_header, current_body
        if not current_header and not current_body:
            return
        header = current_header or "Experience entry from the current resume"
        dates = " / ".join(_date_regex().findall(header)[:2]) if _date_regex().findall(header) else ""
        parts = [part.strip() for part in re.split(r"\s+\|\s+| - | — ", header) if part.strip()]
        title = parts[0] if parts else header
        company = parts[1] if len(parts) > 1 else ""
        description = " ".join(current_body[:2]).strip() or "Rewrite this entry with the same facts, clearer tools, and measurable outcomes."
        entries.append(
            {
                "Job_Title": title[:120],
                "Company": company[:120],
                "Dates": dates[:60] or "Keep original dates from the resume",
                "Description": description[:420],
            }
        )
        current_header = ""
        current_body = []

    for line in source_lines:
        if _date_regex().search(line) or (not current_header and len(line.split()) <= 10):
            _flush()
            current_header = line
        else:
            current_body.append(line)
        if len(entries) >= 3:
            break
    _flush()
    return entries[:3]


def _education_entries(sections: dict[str, str]) -> list[str]:
    return [line.strip("•- ").strip() for line in sections.get("education", "").splitlines() if line.strip()][:4]


def _certification_entries(lines: list[str], sections: dict[str, str]) -> list[str]:
    cert_lines = [line.strip("•- ").strip() for line in sections.get("certifications", "").splitlines() if line.strip()]
    if cert_lines:
        return cert_lines[:4]
    return [line for line in _achievements(lines) if "cert" in line.lower()][:4]


def build_upgrade_heuristically(
    *,
    resume_text: str,
    ats_report: dict,
    choice_id: int,
    context_data: str = "",
) -> dict:
    lines = _clean_lines(resume_text)
    sections = _section_map(lines)
    resume_skills = _extract_resume_skills(resume_text, sections)
    suggestions = ats_report.get("Suggestions_for_Improvement") or []
    summary_focus = {
        1: "overall ATS clarity, structure, and measurable impact",
        2: f"stronger alignment to {context_data or 'the selected role'}",
        3: "direct alignment to the pasted job description",
    }.get(choice_id, "overall ATS quality")

    professional_summary = (
        f"Rewrite the summary around {summary_focus}. "
        "Keep only claims already supported by the original resume, surface the most relevant tools first, "
        "and make the top line show role fit plus measurable value."
    )

    work_experience = _experience_entries(lines, sections)
    if not work_experience:
        work_experience = [
            {
                "Job_Title": "Existing experience from the resume",
                "Company": "",
                "Dates": "Preserve original dates",
                "Description": "Rewrite the strongest existing bullet to show tool, action, scope, and measurable result without inventing new facts.",
            }
        ]

    if suggestions:
        work_experience[0]["Description"] = f"{work_experience[0]['Description']} Priority fix: {suggestions[0]}"

    technical_skills = sorted({skill for skill in resume_skills if skill not in _SOFT_KEYWORDS})[:12]
    soft_skills = sorted({skill for skill in _extract_soft_signals(resume_text)})[:6] or ["communication", "ownership"]

    return {
        "Professional_Summary": professional_summary,
        "Work_Experience": work_experience,
        "Skills": {
            "Technical_Skills": technical_skills,
            "Soft_Skills": soft_skills,
        },
        "Education": _education_entries(sections),
        "Certifications": _certification_entries(lines, sections),
    }
