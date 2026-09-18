"""
Data models for the AI Career Twin application.

All classes are plain dataclasses — no business logic lives here.
Each class provides to_dict() for JSON serialisation and from_dict() for deserialisation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Return a short unique identifier."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Profile sub-models
# ---------------------------------------------------------------------------

@dataclass
class Education:
    """Represents one education entry on a student's profile."""

    institution: str
    degree: str
    year: str

    def to_dict(self) -> Dict:
        return {"institution": self.institution, "degree": self.degree, "year": self.year}

    @classmethod
    def from_dict(cls, data: Dict) -> "Education":
        return cls(
            institution=data.get("institution", ""),
            degree=data.get("degree", ""),
            year=data.get("year", ""),
        )


@dataclass
class Project:
    """Represents one project on a student's profile."""

    title: str
    description: str = ""

    def to_dict(self) -> Dict:
        return {"title": self.title, "description": self.description}

    @classmethod
    def from_dict(cls, data: Dict) -> "Project":
        return cls(title=data.get("title", ""), description=data.get("description", ""))


@dataclass
class StudentSkill:
    """Represents one skill with its self-rated proficiency level."""

    skill_name: str
    proficiency: str  # "Beginner" | "Intermediate" | "Advanced"

    def to_dict(self) -> Dict:
        return {"skill_name": self.skill_name, "proficiency": self.proficiency}

    @classmethod
    def from_dict(cls, data: Dict) -> "StudentSkill":
        return cls(
            skill_name=data.get("skill_name", ""),
            proficiency=data.get("proficiency", "Beginner"),
        )


# ---------------------------------------------------------------------------
# Main profile
# ---------------------------------------------------------------------------

@dataclass
class StudentProfile:
    """Full student profile — the central data object of the application."""

    name: str
    target_role: str = ""           # role slug, e.g. "ai_ml_engineer"
    email: str = ""
    github_url: str = ""
    skills: List[StudentSkill] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    profile_id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "target_role": self.target_role,
            "email": self.email,
            "github_url": self.github_url,
            "skills": [s.to_dict() for s in self.skills],
            "education": [e.to_dict() for e in self.education],
            "projects": [p.to_dict() for p in self.projects],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StudentProfile":
        return cls(
            profile_id=data.get("profile_id", _new_id()),
            name=data.get("name", ""),
            target_role=data.get("target_role", ""),
            email=data.get("email", ""),
            github_url=data.get("github_url", ""),
            skills=[StudentSkill.from_dict(s) for s in data.get("skills", [])],
            education=[Education.from_dict(e) for e in data.get("education", [])],
            projects=[Project.from_dict(p) for p in data.get("projects", [])],
            created_at=data.get("created_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Skill gap analysis result
# ---------------------------------------------------------------------------

@dataclass
class SkillGapResult:
    """Output of the skill gap analysis for a given student profile."""

    strong_skills: List[str] = field(default_factory=list)
    needs_improvement: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    skills_score: float = 0.0   # 0.0 – 1.0


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------

@dataclass
class RoadmapStep:
    """One step in the personalised learning roadmap."""

    week: int
    skill: str
    action: str
    resource_hint: str

    def to_dict(self) -> Dict:
        return {
            "week": self.week,
            "skill": self.skill,
            "action": self.action,
            "resource_hint": self.resource_hint,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RoadmapStep":
        return cls(
            week=data.get("week", 1),
            skill=data.get("skill", ""),
            action=data.get("action", ""),
            resource_hint=data.get("resource_hint", ""),
        )


# ---------------------------------------------------------------------------
# Career Mission
# ---------------------------------------------------------------------------

@dataclass
class Mission:
    """A single daily or weekly task for the student."""

    mission_id: str = field(default_factory=_new_id)
    cadence: str = "weekly"         # "daily" or "weekly"
    task: str = ""
    completed: bool = False

    def to_dict(self) -> Dict:
        return {
            "mission_id": self.mission_id,
            "cadence": self.cadence,
            "task": self.task,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Mission":
        return cls(
            mission_id=data.get("mission_id", _new_id()),
            cadence=data.get("cadence", "weekly"),
            task=data.get("task", ""),
            completed=data.get("completed", False),
        )


# ---------------------------------------------------------------------------
# Interview
# ---------------------------------------------------------------------------

@dataclass
class InterviewAnswer:
    """One submitted answer during a mock interview session."""

    question_id: str
    question_text: str
    answer_text: str
    score: float = 0.0          # 0.0 – 1.0, fraction of keywords matched
    feedback_message: str = ""
    keywords_found: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "answer_text": self.answer_text,
            "score": self.score,
            "feedback_message": self.feedback_message,
            "keywords_found": self.keywords_found,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InterviewAnswer":
        return cls(
            question_id=data.get("question_id", ""),
            question_text=data.get("question_text", ""),
            answer_text=data.get("answer_text", ""),
            score=data.get("score", 0.0),
            feedback_message=data.get("feedback_message", ""),
            keywords_found=data.get("keywords_found", []),
        )


@dataclass
class InterviewSession:
    """One complete (or in-progress) mock interview session."""

    session_id: str = field(default_factory=_new_id)
    profile_id: str = ""
    role: str = ""
    answers: List[InterviewAnswer] = field(default_factory=list)
    session_score: float = 0.0  # 0.0 – 1.0
    started_at: str = field(default_factory=_now_iso)
    completed: bool = False

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "profile_id": self.profile_id,
            "role": self.role,
            "answers": [a.to_dict() for a in self.answers],
            "session_score": self.session_score,
            "started_at": self.started_at,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InterviewSession":
        return cls(
            session_id=data.get("session_id", _new_id()),
            profile_id=data.get("profile_id", ""),
            role=data.get("role", ""),
            answers=[InterviewAnswer.from_dict(a) for a in data.get("answers", [])],
            session_score=data.get("session_score", 0.0),
            started_at=data.get("started_at", _now_iso()),
            completed=data.get("completed", False),
        )


# ---------------------------------------------------------------------------
# Readiness score breakdown
# ---------------------------------------------------------------------------

@dataclass
class ReadinessScore:
    """Breakdown of the five-component career readiness score."""

    skills_score: float = 0.0           # 40 % weight
    proficiency_score: float = 0.0      # 20 % weight
    projects_score: float = 0.0         # 20 % weight
    profile_score: float = 0.0          # 10 % weight
    interview_score: float = 0.0        # 10 % weight
    total_score: float = 0.0            # weighted total, 0 – 100

    WEIGHTS: Dict[str, float] = field(default_factory=lambda: {
        "skills_score": 0.40,
        "proficiency_score": 0.20,
        "projects_score": 0.20,
        "profile_score": 0.10,
        "interview_score": 0.10,
    })

    LABELS: Dict[str, str] = field(default_factory=lambda: {
        "skills_score": "Skill Coverage (40%)",
        "proficiency_score": "Skill Proficiency (20%)",
        "projects_score": "Projects (20%)",
        "profile_score": "Profile Completeness (10%)",
        "interview_score": "Interview Practice (10%)",
    })
