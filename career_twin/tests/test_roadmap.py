"""
Tests for RoadmapGenerator and MissionGenerator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import SkillGapResult
from roadmap import MissionGenerator, RoadmapGenerator


# ---------------------------------------------------------------------------
# RoadmapGenerator
# ---------------------------------------------------------------------------

class TestRoadmapGenerator:
    def setup_method(self):
        self.gen = RoadmapGenerator()

    def test_missing_skills_come_before_needs_improvement(self):
        gap = SkillGapResult(
            missing_skills=["Machine Learning", "Statistics"],
            needs_improvement=["Python"],
        )
        steps = self.gen.generate(gap)
        skills_in_order = [s.skill for s in steps]
        ml_idx = skills_in_order.index("Machine Learning")
        py_idx = skills_in_order.index("Python")
        assert ml_idx < py_idx

    def test_empty_gap_returns_empty_roadmap(self):
        gap = SkillGapResult()
        steps = self.gen.generate(gap)
        assert steps == []

    def test_week_numbers_are_sequential(self):
        gap = SkillGapResult(
            missing_skills=["SQL", "Python"],
            needs_improvement=["Git"],
        )
        steps = self.gen.generate(gap)
        weeks = [s.week for s in steps]
        assert weeks == list(range(1, len(steps) + 1))

    def test_step_has_resource_hint(self):
        gap = SkillGapResult(missing_skills=["Python"])
        steps = self.gen.generate(gap)
        assert steps[0].resource_hint != ""

    def test_fallback_hint_for_unknown_skill(self):
        gap = SkillGapResult(missing_skills=["Quantum Computing"])
        steps = self.gen.generate(gap)
        # Should use the default hint, not crash
        assert "freeCodeCamp" in steps[0].resource_hint or steps[0].resource_hint != ""

    def test_missing_skill_action_mentions_learning(self):
        gap = SkillGapResult(missing_skills=["SQL"])
        steps = self.gen.generate(gap)
        assert "learn" in steps[0].action.lower() or "start" in steps[0].action.lower()

    def test_needs_improvement_action_mentions_deepening(self):
        gap = SkillGapResult(needs_improvement=["Python"])
        steps = self.gen.generate(gap)
        assert "deepen" in steps[0].action.lower() or "practice" in steps[0].action.lower()


# ---------------------------------------------------------------------------
# MissionGenerator
# ---------------------------------------------------------------------------

class TestMissionGenerator:
    def setup_method(self):
        self.gen = MissionGenerator()
        self.rgen = RoadmapGenerator()

    def _make_steps(self, count: int):
        skills = [f"Skill{i}" for i in range(count)]
        gap = SkillGapResult(missing_skills=skills)
        return self.rgen.generate(gap)

    def test_empty_roadmap_returns_empty_missions(self):
        missions = self.gen.generate([])
        assert missions == []

    def test_first_three_steps_each_have_daily_and_weekly(self):
        steps = self._make_steps(3)
        missions = self.gen.generate(steps)
        daily = [m for m in missions if m.cadence == "daily"]
        weekly = [m for m in missions if m.cadence == "weekly"]
        assert len(daily) == 3
        assert len(weekly) == 3

    def test_step_four_has_only_weekly(self):
        steps = self._make_steps(4)
        missions = self.gen.generate(steps)
        # Steps 1–3: 1 daily + 1 weekly each = 6 missions
        # Step 4: 1 weekly only = 1 mission
        # Total = 7 missions
        assert len(missions) == 7

    def test_missions_have_non_empty_tasks(self):
        steps = self._make_steps(2)
        missions = self.gen.generate(steps)
        for m in missions:
            assert m.task.strip() != ""

    def test_mission_cadence_values(self):
        steps = self._make_steps(1)
        missions = self.gen.generate(steps)
        for m in missions:
            assert m.cadence in ("daily", "weekly")

    def test_completed_defaults_to_false(self):
        steps = self._make_steps(1)
        missions = self.gen.generate(steps)
        for m in missions:
            assert m.completed is False
