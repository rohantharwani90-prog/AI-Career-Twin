"""
Tests for SkillGapAnalyzer — validation, gap classification, and readiness score.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from career_analyzer import (
    SkillGapAnalyzer,
    validate_email,
    validate_github_url,
    validate_name,
    validate_proficiency,
    validate_role,
    validate_skill_name,
)
from exceptions import (
    InvalidCareerRoleError,
    InvalidSkillError,
    InvalidStudentProfileError,
)
from models import Education, InterviewSession, Project, StudentProfile, StudentSkill


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_profile(
    name="Alice",
    role="data_analyst",
    skills=None,
    projects=None,
    email="",
    github_url="",
) -> StudentProfile:
    if skills is None:
        skills = [
            StudentSkill("Python", "Advanced"),
            StudentSkill("SQL", "Intermediate"),
            StudentSkill("Statistics", "Beginner"),
        ]
    return StudentProfile(
        name=name,
        target_role=role,
        skills=skills,
        projects=projects or [],
        email=email,
        github_url=github_url,
    )


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

class TestValidateName:
    def test_valid_name(self):
        assert validate_name("Alice Smith") == "Alice Smith"

    def test_strips_whitespace(self):
        assert validate_name("  Bob  ") == "Bob"

    def test_empty_raises(self):
        with pytest.raises(InvalidStudentProfileError):
            validate_name("")

    def test_digits_raise(self):
        with pytest.raises(InvalidStudentProfileError):
            validate_name("Alice123")

    def test_too_long_raises(self):
        with pytest.raises(InvalidStudentProfileError):
            validate_name("A" * 101)


class TestValidateEmail:
    def test_empty_ok(self):
        assert validate_email("") == ""

    def test_valid_email(self):
        assert validate_email("user@example.com") == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(InvalidStudentProfileError):
            validate_email("notanemail")


class TestValidateGithubUrl:
    def test_empty_ok(self):
        assert validate_github_url("") == ""

    def test_valid_github(self):
        url = "https://github.com/alice"
        assert validate_github_url(url) == url

    def test_valid_linkedin(self):
        url = "https://linkedin.com/in/alice"
        assert validate_github_url(url) == url

    def test_invalid_prefix_raises(self):
        with pytest.raises(InvalidStudentProfileError):
            validate_github_url("http://github.com/alice")


class TestValidateSkillName:
    def test_valid(self):
        assert validate_skill_name("Python") == "Python"

    def test_empty_raises(self):
        with pytest.raises(InvalidSkillError):
            validate_skill_name("")

    def test_too_long_raises(self):
        with pytest.raises(InvalidSkillError):
            validate_skill_name("A" * 51)

    def test_duplicate_raises(self):
        existing = [StudentSkill("Python", "Beginner")]
        with pytest.raises(InvalidSkillError):
            validate_skill_name("python", existing)  # case-insensitive


class TestValidateProficiency:
    def test_valid_levels(self):
        for level in ("Beginner", "Intermediate", "Advanced"):
            assert validate_proficiency(level) == level

    def test_invalid_raises(self):
        with pytest.raises(InvalidSkillError):
            validate_proficiency("Expert")


class TestValidateRole:
    def test_valid_roles(self):
        for slug in ("ai_ml_engineer", "software_developer", "data_analyst", "cybersecurity_analyst"):
            assert validate_role(slug) == slug

    def test_invalid_raises(self):
        with pytest.raises(InvalidCareerRoleError):
            validate_role("accountant")


# ---------------------------------------------------------------------------
# SkillGapAnalyzer.analyze()
# ---------------------------------------------------------------------------

class TestSkillGapAnalyzer:
    def setup_method(self):
        self.analyzer = SkillGapAnalyzer()

    def test_all_skills_strong(self):
        """All required skills present at Intermediate+ → 0 missing, full score."""
        skills = [
            StudentSkill("Python", "Advanced"),
            StudentSkill("SQL", "Intermediate"),
            StudentSkill("Statistics", "Intermediate"),
            StudentSkill("Pandas", "Advanced"),
            StudentSkill("Data Visualization", "Intermediate"),
            StudentSkill("Excel", "Intermediate"),
            StudentSkill("Projects", "Advanced"),
        ]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert result.missing_skills == []
        assert result.needs_improvement == []
        assert result.skills_score == 1.0

    def test_all_skills_missing(self):
        """A skill unrelated to the role → all required skills are missing, score = 0."""
        skills = [StudentSkill("Cooking", "Advanced")]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        # "Cooking" matches nothing in data_analyst requirements
        assert len(result.missing_skills) > 0
        assert result.skills_score == 0.0

    def test_empty_skills_list_still_runs(self):
        """Profile with no skills should return all required skills as missing."""
        profile = make_profile(role="data_analyst", skills=[])
        result = self.analyzer.analyze(profile)
        assert len(result.missing_skills) > 0
        assert result.skills_score == 0.0

    def test_beginner_skill_in_needs_improvement(self):
        """A required skill at Beginner → needs_improvement, not strong."""
        skills = [StudentSkill("Python", "Beginner")]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert "Python" in result.needs_improvement
        assert "Python" not in result.strong_skills

    def test_intermediate_skill_is_strong(self):
        """A required skill at Intermediate → strong."""
        skills = [StudentSkill("Python", "Intermediate")]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert "Python" in result.strong_skills

    def test_no_role_raises(self):
        profile = StudentProfile(name="Bob", target_role="")
        with pytest.raises(InvalidStudentProfileError):
            self.analyzer.analyze(profile)

    def test_invalid_role_raises(self):
        profile = StudentProfile(name="Bob", target_role="accountant")
        with pytest.raises(InvalidCareerRoleError):
            self.analyzer.analyze(profile)

    def test_no_name_raises(self):
        profile = StudentProfile(name="", target_role="data_analyst")
        with pytest.raises(InvalidStudentProfileError):
            self.analyzer.analyze(profile)

    def test_partial_score(self):
        """Strong + needs_improvement gives score between 0 and 1."""
        skills = [
            StudentSkill("Python", "Intermediate"),  # strong
            StudentSkill("SQL", "Beginner"),           # needs improvement
        ]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert 0.0 < result.skills_score < 1.0

    def test_skill_alias_resolves(self):
        """'stats' should match the required skill 'Statistics'."""
        skills = [StudentSkill("stats", "Intermediate")]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert "Statistics" in result.strong_skills

    def test_case_insensitive_match(self):
        """'python' (lowercase) should match required skill 'Python'."""
        skills = [StudentSkill("python", "Advanced")]
        profile = make_profile(role="data_analyst", skills=skills)
        result = self.analyzer.analyze(profile)
        assert "Python" in result.strong_skills


# ---------------------------------------------------------------------------
# SkillGapAnalyzer.calculate_readiness()
# ---------------------------------------------------------------------------

class TestCalculateReadiness:
    def setup_method(self):
        self.analyzer = SkillGapAnalyzer()

    def _gap_result(self, skills_score=1.0):
        from models import SkillGapResult
        return SkillGapResult(skills_score=skills_score)

    def test_no_sessions_interview_score_is_zero(self):
        profile = make_profile(projects=[Project("p1", ""), Project("p2", "")])
        gap = self._gap_result(skills_score=1.0)
        r = self.analyzer.calculate_readiness(profile, gap, [])
        assert r.interview_score == 0.0

    def test_three_projects_full_project_score(self):
        projects = [Project(f"P{i}", "") for i in range(3)]
        profile = make_profile(projects=projects)
        gap = self._gap_result()
        r = self.analyzer.calculate_readiness(profile, gap, [])
        assert r.projects_score == 100.0

    def test_one_project_partial_project_score(self):
        profile = make_profile(projects=[Project("P1", "")])
        gap = self._gap_result()
        r = self.analyzer.calculate_readiness(profile, gap, [])
        assert abs(r.projects_score - 33.3) < 1.0

    def test_completed_sessions_affect_interview_score(self):
        profile = make_profile()
        gap = self._gap_result()
        s1 = InterviewSession(profile_id=profile.profile_id, role="data_analyst",
                              session_score=0.5, completed=True)
        s2 = InterviewSession(profile_id=profile.profile_id, role="data_analyst",
                              session_score=1.0, completed=True)
        r = self.analyzer.calculate_readiness(profile, gap, [s1, s2])
        assert r.interview_score == 75.0

    def test_total_score_is_weighted_average(self):
        """With all components at 100%, total should be 100."""
        projects = [Project(f"P{i}", "") for i in range(3)]
        skills = [
            StudentSkill("Python", "Advanced"),
            StudentSkill("SQL", "Advanced"),
            StudentSkill("Statistics", "Advanced"),
            StudentSkill("Pandas", "Advanced"),
            StudentSkill("Data Visualization", "Advanced"),
            StudentSkill("Excel", "Advanced"),
            StudentSkill("Projects", "Advanced"),
        ]
        profile = StudentProfile(
            name="Alice",
            target_role="data_analyst",
            skills=skills,
            projects=projects,
            email="a@b.com",
            github_url="https://github.com/alice",
            education=[Education("MIT", "BSc", "2024")],
        )
        gap = self._gap_result(skills_score=1.0)
        s = InterviewSession(profile_id=profile.profile_id, role="data_analyst",
                             session_score=1.0, completed=True)
        r = self.analyzer.calculate_readiness(profile, gap, [s])
        assert r.total_score == 100.0
