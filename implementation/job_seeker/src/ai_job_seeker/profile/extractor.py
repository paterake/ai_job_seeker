"""Extract candidate facts from a CV .docx into a dict matching the
CandidateProfile YAML schema.

Hard rules (from PCO no-fabrication / trace-to-profile):
  - Every value written to the output dict traces to exact text in the docx.
  - Inferred/missing target fields (roles, locations, salary_min_gbp) are
    explicitly LEFT EMPTY and marked as required-review fields in the CLI.
  - No LLM is used — this is a deterministic paragraph parser.

The docx shape we parse is the one from Kiera_Patel_CV.docx (paragraphs, no
tables, section headers in ALL-CAPS, bullets are plain paragraphs under the
header). This is deliberately simple; it works for this CV and similar
graduate-CV layouts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- Required section header keywords (case-insensitive match) ----------------

SECTION_HEADER_KEYWORDS = {
    "profile": {"PROFILE", "PERSONAL PROFILE", "SUMMARY", "PERSONAL STATEMENT"},
    "key_skills": {"KEY SKILLS", "SKILLS", "CORE SKILLS", "COMPETENCIES"},
    "education": {"EDUCATION"},
    "work_experience": {
        "WORK EXPERIENCE",
        "EXPERIENCE",
        "EMPLOYMENT",
        "EMPLOYMENT HISTORY",
        "PROFESSIONAL EXPERIENCE",
    },
    "achievements": {
        "ACHIEVEMENTS & AWARDS",
        "ACHIEVEMENTS AND AWARDS",
        "ACHIEVEMENTS",
        "AWARDS",
    },
    "interests": {"INTERESTS", "HOBBIES", "HOBBIES & INTERESTS"},
}

ROLE_COMPANY_DATE_RE = re.compile(
    r"^(?P<role>.+?)\s*[·•-]\s*(?P<company>.+?)"
    r"(?P<start>[A-Z][a-z]{2}\s+\d{4})\s*[-–—]\s*(?P<end>[A-Z][a-z]{2}\s+\d{4}|Present|Current|Date)$"
)

EDUCATION_SCHOOL_DATE_RE = re.compile(
    r"^(?P<school>.+?)\s*(?P<start>\d{4})\s*[-–—]\s*(?P<end>\d{4})$"
)


@dataclass
class ProfileExtractResult:
    """Result of docx → profile extraction.

    Fields marked required-review are those that cannot be reliably extracted
    from a CV (target roles/locations/salary_min_gbp). These are left as empty
    lists/None by the extractor and surfaced as review prompts by the CLI.
    """

    profile: dict[str, Any]
    required_review: list[str] = field(default_factory=list)


def _section_of(text: str) -> str | None:
    """Return a section key (e.g. 'work_experience') if text matches a header."""
    stripped = text.strip().upper()
    for section_key, variants in SECTION_HEADER_KEYWORDS.items():
        if stripped in variants:
            return section_key
    return None


def _parse_identity_header(paragraphs: list[tuple[int, str]]) -> dict[str, Any]:
    """Extract name + contact from the top of the CV (first 2 non-empty paras)."""
    name = paragraphs[0][1].strip() if paragraphs else ""
    contact_line = paragraphs[1][1].strip() if len(paragraphs) > 1 else ""

    identity: dict[str, Any] = {
        "name": name,
        "email": None,
        "phone": None,
        "linkedin_url": None,
        "nationality": None,
    }

    for piece in [p.strip() for p in re.split(r"[·•]", contact_line) if p.strip()]:
        if "@" in piece:
            identity["email"] = piece
        elif piece.startswith(("0", "+")) and any(c.isdigit() for c in piece):
            identity["phone"] = piece
        elif "linkedin" in piece.lower():
            url = piece if piece.startswith("http") else f"https://{piece}"
            identity["linkedin_url"] = url
        elif "national" in piece.lower():
            # "British National" — keep the whole phrase.
            identity["nationality"] = piece

    return identity


def _split_skill_string(line: str) -> list[str]:
    """Split a 'skill | skill · skill' line into normalised skills."""
    # Split on common separators first by converting to |.
    text = line.replace("·", "|").replace("•", "|").replace(";", "|")
    return [s.strip() for s in text.split("|") if s.strip()]


def _parse_work_block(lines: list[str]) -> dict[str, Any] | None:
    """Parse a single work-experience block: header line + bullet paragraphs."""
    if not lines:
        return None
    header = lines[0].strip()
    m = ROLE_COMPANY_DATE_RE.match(header)
    if not m:
        # Fallback: treat the line as role + company, no dates.
        parts = [p.strip() for p in re.split(r"[·•]", header) if p.strip()]
        if len(parts) < 2:
            return None
        return {
            "role": parts[0],
            "company": parts[1],
            "start_date": None,
            "end_date": None,
            "highlights": lines[1:],
        }
    return {
        "role": m.group("role").strip(),
        "company": m.group("company").strip(),
        "start_date": m.group("start").strip(),
        "end_date": m.group("end").strip(),
        "highlights": [l.strip() for l in lines[1:] if l.strip()],
    }


def _parse_education_block(lines: list[str]) -> dict[str, Any] | None:
    """Parse a single education entry: school+dates line + 0..n qualification lines."""
    if not lines:
        return None
    header = lines[0].strip()
    m = EDUCATION_SCHOOL_DATE_RE.match(header)
    if not m:
        # No parseable dates: keep the header text as-is as school_plus.
        qualifications = [l.strip() for l in lines[1:] if l.strip()]
        if not qualifications:
            return None
        return {
            "school": header,
            "start_year": None,
            "end_year": None,
            "qualifications": qualifications,
        }
    qualifications = [l.strip() for l in lines[1:] if l.strip()]
    return {
        "school": m.group("school").strip(),
        "start_year": int(m.group("start").strip()),
        "end_year": int(m.group("end").strip()),
        "qualifications": qualifications,
    }


def extract_profile_from_docx(docx_path: str | Path) -> ProfileExtractResult:
    """Parse a CV .docx and return a ProfileExtractResult containing the
    structured profile dict (suitable for YAML dump via save_profile) plus a
    list of required-review field names.

    Raises ProfileError if the .docx cannot be read (e.g. file missing).
    """
    from docx import Document  # noqa: WPS433 — dep declared in pyproject
    from ai_job_seeker.profile.loader import ProfileError

    path = Path(docx_path)
    if not path.is_file():
        raise ProfileError(f"CV .docx not found: {path}")
    try:
        doc = Document(str(path))
    except Exception as e:  # pragma: no cover — python-docx internal errors
        raise ProfileError(f"Could not read CV .docx ({path}): {e}") from e

    paras: list[tuple[int, str]] = [
        (i, p.text) for i, p in enumerate(doc.paragraphs) if p.text.strip()
    ]
    if not paras:
        raise ProfileError(f"CV .docx appears empty: {path}")

    # --- Section slicing: iterate through paragraphs, re-classifying current  ---
    # section key each time we hit an ALL-CAPS header match.
    identity = _parse_identity_header(paras)

    profile_text = ""
    skills: list[str] = []
    education: list[dict[str, Any]] = []
    experience: list[dict[str, Any]] = []
    achievements: list[str] = []
    interests: list[str] = []

    current_section: str | None = None
    # Accumulators for multi-paragraph blocks:
    work_block_lines: list[str] = []
    educ_block_lines: list[str] = []

    def _flush_work() -> None:
        nonlocal work_block_lines
        block = _parse_work_block(work_block_lines)
        if block is not None:
            experience.append(block)
        work_block_lines = []

    def _flush_educ() -> None:
        nonlocal educ_block_lines
        block = _parse_education_block(educ_block_lines)
        if block is not None:
            education.append(block)
        educ_block_lines = []

    # Start iterating from paragraph 2 (skip identity header + contact line).
    for _, raw in paras[2:]:
        text = raw.strip()
        section = _section_of(text)
        if section is not None:
            # Flush any in-flight blocks from the previous section first.
            if current_section == "work_experience":
                _flush_work()
            elif current_section == "education":
                _flush_educ()
            current_section = section
            continue

        if current_section == "profile":
            profile_text += (" " if profile_text else "") + text
        elif current_section == "key_skills":
            skills.extend(_split_skill_string(text))
        elif current_section == "work_experience":
            # A header-like line for a *new* job: contains a role·company and
            # ends with a date range. Flush previous block first.
            if ROLE_COMPANY_DATE_RE.match(text):
                if work_block_lines:
                    _flush_work()
            work_block_lines.append(text)
        elif current_section == "education":
            if EDUCATION_SCHOOL_DATE_RE.match(text):
                if educ_block_lines:
                    _flush_educ()
            educ_block_lines.append(text)
        elif current_section == "achievements":
            achievements.append(text)
        elif current_section == "interests":
            # One paragraph, comma or · separated.
            for piece in _split_skill_string(text):
                interests.append(piece)

    # End-of-document flushes.
    if work_block_lines:
        _flush_work()
    if educ_block_lines:
        _flush_educ()

    required_review: list[str] = []

    target: dict[str, Any] = {
        "roles": [],
        "locations": [],
        "remote": "any",
        "salary_min_gbp": None,
        "salary_max_gbp": None,
        "contract_types": [],
    }
    # --- Infer a hint for target.roles ONLY if the PROFILE paragraph ends ---
    # with an explicit "eager to channel X into a graduate [marketing or
    # communications] role"-type sentence. We pull the role mention literally.
    if profile_text:
        m = re.search(
            r"(?i)\b(?:graduate|entry[- ]?level|early[- ]?career)\s+"
            r"([A-Za-z, ]+?)\s*(?:role|position|opportunity|career)",
            profile_text,
        )
        if m:
            phrase = m.group(1).strip()
            # Split on "or"/commas, normalise.
            parts = [
                p.strip(" -")
                for p in re.split(r"\bor\b|,", phrase)
                if p.strip(" -")
            ]
            if parts:
                target["roles"] = parts
                # roles hint is still flagged for review — it's a single
                # sentence, not a canonical list of every title variant.
                required_review.append("target.roles (inferred — review)")
            else:
                required_review.append("target.roles")
        else:
            required_review.append("target.roles")
    else:
        required_review.append("target.roles")

    for field_name in ("target.locations", "target.salary_min_gbp", "target.contract_types"):
        required_review.append(field_name)

    profile: dict[str, Any] = {
        "identity": identity,
        "summary": profile_text.strip(),
        "skills": _classify_skills(skills),
        "experience": experience,
        "education": education,
        "achievements_and_awards": achievements,
        "interests": interests,
        "target": target,
    }

    return ProfileExtractResult(profile=profile, required_review=required_review)


def _classify_skills(raw: list[str]) -> dict[str, list[str]]:
    """Classify a flat skill list into {hard, soft, languages, tools}.

    No LLM used — keyword heuristics. Missing buckets kept as empty lists so
    the YAML schema stays stable. Duplicates are dropped (preserving order).
    """
    SOFT_HINTS = (
        "communication", "stakeholder", "engagement", "team", "collaboration",
        "time management", "attention to detail", "cross-cultural", "awareness",
        "research", "analysis", "management", "leadership", "presentation",
        "interpersonal", "organised", "organisation", "organizational",
        "problem solving", "critical thinking", "patience", "reliability",
        "professionalism",
    )
    LANG_HINTS = (
        "english", "spanish", "french", "german", "mandarin", "arabic",
        "chinese", "italian", "portuguese", "russian", "japanese",
    )
    TOOL_HINTS = (
        "microsoft", "excel", "word", "powerpoint", "outlook", "google",
        "python", "sql", "tableau", "photoshop", "canva", "indesign",
        "figma", "notion", "slack", "salesforce", "hubspot",
    )

    def _hint_in(name: str, hints: tuple[str, ...]) -> bool:
        low = name.lower()
        return any(h in low for h in hints)

    soft: list[str] = []
    hard: list[str] = []
    languages: list[str] = []
    tools: list[str] = []
    seen: set[str] = set()
    for name in raw:
        key = name.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        if _hint_in(name, LANG_HINTS):
            languages.append(name.strip())
        elif _hint_in(name, TOOL_HINTS):
            tools.append(name.strip())
        elif _hint_in(name, SOFT_HINTS):
            soft.append(name.strip())
        else:
            # No clear hint — treat as hard (subject-area skills like
            # "Numeracy (A-Level Maths)", "Research & Analysis", "Content
            # Writing", "Project Planning" all sit here if no soft-hint matched
            # above. The classifier treats "specific capability = hard" when
            # in doubt — better to surface on match phase-1 than hide in soft.
            hard.append(name.strip())

    # "Research & Analysis" contains the word "research" but is explicitly a
    # concrete capability. Re-classify it if the soft hints caught it.
    for specific in (
        "Research & Analysis", "Written Communication", "Numeracy (A-Level Maths)",
    ):
        if specific in soft:
            soft.remove(specific)
            hard.append(specific)
    # De-dupe within each list while preserving order.
    def _dedup(lst: list[str]) -> list[str]:
        out: list[str] = []
        s: set[str] = set()
        for x in lst:
            if x in s:
                continue
            s.add(x)
            out.append(x)
        return out
    return {
        "hard": _dedup(hard),
        "soft": _dedup(soft),
        "languages": _dedup(languages),
        "tools": _dedup(tools),
    }
