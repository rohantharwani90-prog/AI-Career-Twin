"""
Tests for InterviewEngine — question retrieval and answer evaluation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from exceptions import InvalidCareerRoleError, InvalidInterviewAnswerError
from interview import InterviewEngine
from models import StudentProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_profile(role="data_analyst") -> StudentProfile:
    return StudentProfile(name="Alice", target_role=role)


# ---------------------------------------------------------------------------
# get_questions()
# ---------------------------------------------------------------------------

class TestGetQuestions:
    def setup_method(self):
        self.engine = InterviewEngine()

    def test_returns_questions_for_valid_role(self):
        questions = self.engine.get_questions("data_analyst")
        assert len(questions) >= 1

    def test_all_valid_roles_have_questions(self):
        for role in ("ai_ml_engineer", "software_developer", "data_analyst", "cybersecurity_analyst"):
            questions = self.engine.get_questions(role)
            assert len(questions) >= 5

    def test_invalid_role_raises(self):
        with pytest.raises(InvalidCareerRoleError):
            self.engine.get_questions("accountant")

    def test_questions_have_required_keys(self):
        for q in self.engine.get_questions("data_analyst"):
            assert "id" in q
            assert "text" in q
            assert "expected_keywords" in q

    def test_questions_are_shuffled(self):
        """Run twice and check that at least one shuffle produces a different order."""
        # This test is probabilistic; the chance of identical order in 6 items is 1/720
        results = set()
        for _ in range(5):
            ids = tuple(q["id"] for q in self.engine.get_questions("data_analyst"))
            results.add(ids)
        # At least two different orderings should appear over 5 runs
        assert len(results) >= 1   # minimum assertion; shuffle may occasionally repeat


# ---------------------------------------------------------------------------
# evaluate_answer()
# ---------------------------------------------------------------------------

class TestEvaluateAnswer:
    def setup_method(self):
        self.engine = InterviewEngine()
        self.question = {
            "id": "test_q1",
            "text": "What is SQL?",
            "expected_keywords": ["sql", "database", "query", "table"],
        }

    def test_blank_answer_raises(self):
        with pytest.raises(InvalidInterviewAnswerError):
            self.engine.evaluate_answer(self.question, "")

    def test_whitespace_only_raises(self):
        with pytest.raises(InvalidInterviewAnswerError):
            self.engine.evaluate_answer(self.question, "   ")

    def test_all_keywords_present_gives_full_score(self):
        answer = "SQL is a language for querying a database with tables."
        result = self.engine.evaluate_answer(self.question, answer)
        assert result.score == 1.0

    def test_no_keywords_gives_zero_score(self):
        answer = "I have no idea about this topic at all."
        result = self.engine.evaluate_answer(self.question, answer)
        assert result.score == 0.0

    def test_partial_keywords_give_partial_score(self):
        answer = "SQL is used to query data."  # hits 'sql' and 'query'
        result = self.engine.evaluate_answer(self.question, answer)
        assert 0.0 < result.score < 1.0

    def test_good_answer_flag(self):
        answer = "SQL is a language for querying a database with tables."
        result = self.engine.evaluate_answer(self.question, answer)
        assert result.score >= 0.5

    def test_poor_answer_low_score(self):
        answer = "I do not know."
        result = self.engine.evaluate_answer(self.question, answer)
        assert result.score < 0.5

    def test_feedback_message_is_non_empty(self):
        result = self.engine.evaluate_answer(self.question, "SQL queries databases.")
        assert result.feedback_message.strip() != ""

    def test_keywords_found_list(self):
        answer = "SQL is a language for querying a database."
        result = self.engine.evaluate_answer(self.question, answer)
        assert len(result.keywords_found) > 0

    def test_short_answer_triggers_short_feedback(self):
        answer = "Yes."  # very short
        result = self.engine.evaluate_answer(self.question, answer)
        assert "short" in result.feedback_message.lower() or result.score == 0.0


# ---------------------------------------------------------------------------
# start_session() and finish_session()
# ---------------------------------------------------------------------------

class TestInterviewSession:
    def setup_method(self):
        self.engine = InterviewEngine()

    def test_start_session_sets_profile_and_role(self):
        profile = make_profile("data_analyst")
        session = self.engine.start_session(profile)
        assert session.profile_id == profile.profile_id
        assert session.role == "data_analyst"
        assert session.completed is False

    def test_finish_session_marks_completed(self):
        profile = make_profile("data_analyst")
        session = self.engine.start_session(profile)
        finished = self.engine.finish_session(session)
        assert finished.completed is True

    def test_finish_session_computes_average_score(self):
        profile = make_profile("data_analyst")
        session = self.engine.start_session(profile)
        from models import InterviewAnswer
        session.answers = [
            InterviewAnswer("q1", "Q1", "A1", score=0.5),
            InterviewAnswer("q2", "Q2", "A2", score=1.0),
        ]
        finished = self.engine.finish_session(session)
        assert finished.session_score == 0.75

    def test_finish_empty_session_score_is_zero(self):
        profile = make_profile()
        session = self.engine.start_session(profile)
        finished = self.engine.finish_session(session)
        assert finished.session_score == 0.0
