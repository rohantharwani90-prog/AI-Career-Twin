"""
Tests for data models — StudentProfile, StudentSkill, Education, Project,
InterviewSession, InterviewAnswer, Mission, RoadmapStep, ReadinessScore.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import (
    Education,
    InterviewAnswer,
    InterviewSession,
    Mission,
    Project,
    ReadinessScore,
    RoadmapStep,
    SkillGapResult,
    StudentProfile,
    StudentSkill,
)


# ---------------------------------------------------------------------------
# StudentSkill
# ---------------------------------------------------------------------------

class TestStudentSkill:
    def test_to_dict_round_trip(self):
        skill = StudentSkill(skill_name="Python", proficiency="Intermediate")
        assert StudentSkill.from_dict(skill.to_dict()) == skill

    def test_from_dict_defaults(self):
        skill = StudentSkill.from_dict({})
        assert skill.skill_name == ""
        assert skill.proficiency == "Beginner"


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

class TestEducation:
    def test_round_trip(self):
        edu = Education(institution="MIT", degree="BSc CS", year="2024")
        assert Education.from_dict(edu.to_dict()) == edu


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class TestProject:
    def test_round_trip(self):
        proj = Project(title="My App", description="A cool app")
        assert Project.from_dict(proj.to_dict()) == proj

    def test_description_optional(self):
        proj = Project.from_dict({"title": "No desc"})
        assert proj.description == ""


# ---------------------------------------------------------------------------
# StudentProfile
# ---------------------------------------------------------------------------

class TestStudentProfile:
    def _make_profile(self) -> StudentProfile:
        return StudentProfile(
            name="Alice",
            target_role="data_analyst",
            email="alice@example.com",
            skills=[StudentSkill("Python", "Advanced")],
            education=[Education("Oxford", "BSc", "2023")],
            projects=[Project("Dashboard", "A data dashboard")],
            github_url="https://github.com/alice",
        )

    def test_to_dict_has_all_keys(self):
        profile = self._make_profile()
        d = profile.to_dict()
        for key in ("profile_id", "name", "target_role", "email", "github_url",
                    "skills", "education", "projects", "created_at"):
            assert key in d

    def test_round_trip(self):
        profile = self._make_profile()
        restored = StudentProfile.from_dict(profile.to_dict())
        assert restored.name == profile.name
        assert restored.target_role == profile.target_role
        assert len(restored.skills) == 1
        assert restored.skills[0].skill_name == "Python"

    def test_profile_id_is_generated(self):
        p1 = StudentProfile(name="A")
        p2 = StudentProfile(name="B")
        assert p1.profile_id != p2.profile_id


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

class TestMission:
    def test_round_trip(self):
        m = Mission(cadence="daily", task="Practice Python", completed=True)
        restored = Mission.from_dict(m.to_dict())
        assert restored.task == "Practice Python"
        assert restored.completed is True
        assert restored.cadence == "daily"


# ---------------------------------------------------------------------------
# RoadmapStep
# ---------------------------------------------------------------------------

class TestRoadmapStep:
    def test_round_trip(self):
        step = RoadmapStep(week=2, skill="SQL", action="Learn joins", resource_hint="SQLZoo")
        assert RoadmapStep.from_dict(step.to_dict()) == step


# ---------------------------------------------------------------------------
# InterviewAnswer + InterviewSession
# ---------------------------------------------------------------------------

class TestInterviewSession:
    def test_session_round_trip(self):
        ans = InterviewAnswer(
            question_id="q1",
            question_text="What is Python?",
            answer_text="A programming language",
            score=0.5,
        )
        session = InterviewSession(
            profile_id="pid",
            role="data_analyst",
            answers=[ans],
            session_score=0.5,
            completed=True,
        )
        restored = InterviewSession.from_dict(session.to_dict())
        assert restored.completed is True
        assert len(restored.answers) == 1
        assert restored.answers[0].question_id == "q1"
