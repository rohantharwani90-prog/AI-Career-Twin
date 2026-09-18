"""
Roadmap and Mission generators.

RoadmapGenerator  — turns a SkillGapResult into a week-by-week learning plan.
MissionGenerator  — turns a Roadmap into concrete daily/weekly tasks.
"""

from typing import List

import career_data as cd
from models import Mission, RoadmapStep, SkillGapResult


# ---------------------------------------------------------------------------
# RoadmapGenerator
# ---------------------------------------------------------------------------

class RoadmapGenerator:
    """
    Builds a personalised learning roadmap from a SkillGapResult.

    Missing skills are prioritised before skills that need improvement.
    Each step gets a simple action sentence and a resource hint.
    """

    def generate(self, gap_result: SkillGapResult) -> List[RoadmapStep]:
        """
        Return an ordered list of RoadmapStep objects.

        Returns an empty list when there are no gaps.
        """
        steps: List[RoadmapStep] = []
        week = 1

        # Missing skills first (highest priority)
        for skill in gap_result.missing_skills:
            steps.append(self._make_step(week, skill, priority="missing"))
            week += 1

        # Skills that need improvement second
        for skill in gap_result.needs_improvement:
            steps.append(self._make_step(week, skill, priority="improve"))
            week += 1

        return steps

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_step(self, week: int, skill: str, priority: str) -> RoadmapStep:
        """Build one RoadmapStep for a skill."""
        if priority == "missing":
            action = f"Start learning {skill} from scratch — complete a beginner tutorial."
        else:
            action = f"Deepen your {skill} knowledge — practice exercises and build a small example."

        hint_key = skill.strip().lower()
        resource_hint = cd.RESOURCE_HINTS.get(hint_key, cd.RESOURCE_HINTS_DEFAULT)

        return RoadmapStep(week=week, skill=skill, action=action, resource_hint=resource_hint)


# ---------------------------------------------------------------------------
# MissionGenerator
# ---------------------------------------------------------------------------

class MissionGenerator:
    """
    Converts a list of RoadmapSteps into daily and weekly Mission tasks.

    Rules:
    - The first 3 steps each produce one daily mission and one weekly mission.
    - Steps 4 and beyond produce only a weekly mission.
    - If no steps exist, returns an empty list.
    """

    def generate(self, steps: List[RoadmapStep]) -> List[Mission]:
        """Return a flat list of Mission objects."""
        missions: List[Mission] = []

        for index, step in enumerate(steps):
            if index < 3:
                missions.append(Mission(
                    cadence="daily",
                    task=self._daily_task(step.skill),
                ))
            missions.append(Mission(
                cadence="weekly",
                task=self._weekly_task(step.skill),
            ))

        return missions

    def _daily_task(self, skill: str) -> str:
        return f"Practice {skill} for at least 30 minutes today."

    def _weekly_task(self, skill: str) -> str:
        return f"Complete one {skill} tutorial or exercise this week."
