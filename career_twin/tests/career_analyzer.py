"""
Career Analyzer — compares a student's skills against a target role's requirements
and produces a SkillGapResult, a ReadinessScore, and validates profile/skill data.
"""

from typing import List, Optional

import career_data as cd
from exceptions import (
    InvalidCareerRoleError,
    InvalidSkillError,
    InvalidStudentProfileError,
)
from models import ReadinessScore, SkillGapResult, StudentProfile, StudentSkill, InterviewSession


# ---------------------------------------------------------------------------
# Validation helpers (used by UI and tests)
# ---------------------------------------------------------------------------

def validate_name(name: str) -> str:
    """
    Validate and return the cleaned name.

    Raises InvalidStudentProfileError if the name is empty or contains digits.
    """
    name = name.strip()
    if not name:
        raise InvalidStudentProfileError("Name must not be empty.")
    if any(ch.isdigit() for ch in name):
        raise InvalidStudentProfileError("Name must not contain numbers.")
    if len(name) > 100:
        raise InvalidStudentProfileError("Name must be 100 characters or fewer.")
    return name


def validate_email(email: str) -> str:
    """
    Validate and return the cleaned email (optional field).

    Raises InvalidStudentProfileError if a non-empty value looks malformed.
    """
    email = email.strip()
    if not email:
        return email
    if "@" not in email or "." not in email.split("@")[-1]:
        raise InvalidStudentProfileError(
            "Email address does not look valid (expected format: user@domain.com)."
        )
    return email


def validate_github_url(url: str) -> str:
    """
    Validate and return the cleaned GitHub/LinkedIn URL (optional field).

    Raises InvalidStudentProfileError if a non-empty value has an unexpected prefix.
    """
    url = url.strip()
    if not url:
        return url
    allowed = ("https://github.com/", "https://linkedin.com/", "https://www.linkedin.com/")
    if not any(url.startswith(prefix) for prefix in allowed):
        raise InvalidStudentProfileError(
            "URL must start with https://github.com/ or https://linkedin.com/"
        )
    return url


def validate_skill_name(name: str, existing_skills: Optional[List[StudentSkill]] = None) -> str:
    """
    Validate and return the cleaned skill name.

    Raises InvalidSkillError if the name is empty, too long, or a duplicate.
    """
    name = name.strip()
    if not name:
        raise InvalidSkillError("Skill name must not be empty.")
    if len(name) > 50:
        raise InvalidSkillError("Skill name must be 50 characters or fewer.")
    if existing_skills:
        normalised = _normalise(name)
        for skill in existing_skills:
            if _normalise(skill.skill_name) == normalised:
                raise InvalidSkillError(f"Skill '{name}' is already in the list.")
    return name


def validate_proficiency(proficiency: str) -> str:
    """
    Validate that the proficiency level is one of the allowed values.

    Raises InvalidSkillError otherwise.
    """
    if proficiency not in cd.PROFICIENCY_LEVELS:
        raise InvalidSkillError(
            f"Proficiency must be one of: {', '.join(cd.PROFICIENCY_LEVELS)}."
        )
    return proficiency


def validate_role(role_slug: str) -> str:
    """
    Validate that the role slug exists in CAREER_ROLES.

    Raises InvalidCareerRoleError otherwise.
    """
    if role_slug not in cd.CAREER_ROLES:
        raise InvalidCareerRoleError(
            f"'{role_slug}' is not a recognised career role. "
            f"Valid roles: {', '.join(cd.ROLE_SLUGS)}."
        )
    return role_slug


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lowercase, strip, and resolve skill aliases."""
    clean = text.strip().lower()
    resolved = cd.SKILL_ALIASES.get(clean, clean)
    return resolved.lower()


def _proficiency_rank(proficiency: str) -> int:
    """Return the integer rank for a proficiency level (Beginner=0, …, Advanced=2)."""
    return cd.PROFICIENCY_LEVELS.index(proficiency) if proficiency in cd.PROFICIENCY_LEVELS else 0


def _strong_threshold_rank() -> int:
    return _proficiency_rank(cd.STRONG_THRESHOLD)


# ---------------------------------------------------------------------------
# SkillGapAnalyzer
# ---------------------------------------------------------------------------

class SkillGapAnalyzer:
    """
    Compares a student profile's skills against the target role's requirements.

    Usage::

        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(profile)
    """

    def analyze(self, profile: StudentProfile) -> SkillGapResult:
        """
        Analyse the skill gap for the given profile.

        Raises InvalidStudentProfileError if no name or no role is set.
        Raises InvalidCareerRoleError if the role slug is unrecognised.
        """
        if not profile.name.strip():
            raise InvalidStudentProfileError("Profile must have a name.")
        if not profile.target_role:
            raise InvalidStudentProfileError(
                "Please select a target career role before running the analysis."
            )
        validate_role(profile.target_role)

        role_data = cd.CAREER_ROLES[profile.target_role]
        required: List[str] = role_data["required_skills"]

        strong: List[str] = []
        needs_improvement: List[str] = []
        missing: List[str] = []

        for req_skill in required:
            student_skill = self._find_student_skill(req_skill, profile.skills)
            if student_skill is None:
                missing.append(req_skill)
            elif _proficiency_rank(student_skill.proficiency) >= _strong_threshold_rank():
                strong.append(req_skill)
            else:
                needs_improvement.append(req_skill)

        total = len(required)
        if total == 0:
            skills_score = 0.0
        else:
            # Strong = full point, needs_improvement = half point
            score_raw = len(strong) + 0.5 * len(needs_improvement)
            skills_score = score_raw / total

        return SkillGapResult(
            strong_skills=strong,
            needs_improvement=needs_improvement,
            missing_skills=missing,
            skills_score=skills_score,
        )

    # ------------------------------------------------------------------
    # Readiness score
    # ------------------------------------------------------------------

    def calculate_readiness(
        self,
        profile: StudentProfile,
        gap_result: SkillGapResult,
        sessions: List[InterviewSession],
    ) -> ReadinessScore:
        """
        Calculate the overall career readiness score broken into five components.

        The score is a transparent indicator — it does not predict hiring success.
        """
        # 1. Skill coverage (from gap analysis)
        skills_score = gap_result.skills_score  # already 0.0 – 1.0

        # 2. Proficiency — average rank of all entered skills normalised to 0–1
        if profile.skills:
            max_rank = len(cd.PROFICIENCY_LEVELS) - 1  # 2
            avg_rank = sum(
                _proficiency_rank(s.proficiency) for s in profile.skills
            ) / len(profile.skills)
            proficiency_score = avg_rank / max_rank
        else:
            proficiency_score = 0.0

        # 3. Projects — 3 or more = full score
        projects_score = min(len(profile.projects) / 3.0, 1.0)

        # 4. Profile completeness — non-empty optional fields out of 4
        optional_filled = sum([
            bool(profile.email.strip()),
            bool(profile.github_url.strip()),
            len(profile.education) > 0,
            len(profile.projects) > 0,
        ])
        profile_score = optional_filled / 4.0

        # 5. Interview practice — average session score across completed sessions
        completed = [s for s in sessions if s.completed]
        if completed:
            interview_score = sum(s.session_score for s in completed) / len(completed)
        else:
            interview_score = 0.0

        # Weighted total (weights from ReadinessScore.WEIGHTS)
        rs = ReadinessScore(
            skills_score=round(skills_score * 100, 1),
            proficiency_score=round(proficiency_score * 100, 1),
            projects_score=round(projects_score * 100, 1),
            profile_score=round(profile_score * 100, 1),
            interview_score=round(interview_score * 100, 1),
        )
        rs.total_score = round(
            skills_score * 40
            + proficiency_score * 20
            + projects_score * 20
            + profile_score * 10
            + interview_score * 10,
            1,
        )
        return rs

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_student_skill(
        self, required_skill: str, skills: List[StudentSkill]
    ) -> Optional[StudentSkill]:
        """
        Find a student skill that matches the required skill name (alias-aware).

        Returns None if no match is found.
        """
        target = _normalise(required_skill)
        for skill in skills:
            if _normalise(skill.skill_name) == target:
                return skill
        return None
