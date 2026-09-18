"""
Interview Engine — retrieves role-specific questions and evaluates student answers
using simple keyword matching.

⚠️  Feedback is basic AI-style practice feedback only.
    It does not evaluate real interview performance and cannot predict hiring success.
"""

import random
import string
from typing import Dict, List, Tuple

import career_data as cd
from exceptions import InvalidCareerRoleError, InvalidInterviewAnswerError
from models import InterviewAnswer, InterviewSession, StudentProfile


# ---------------------------------------------------------------------------
# InterviewEngine
# ---------------------------------------------------------------------------

class InterviewEngine:
    """
    Manages mock interview sessions for a student.

    Usage::

        engine = InterviewEngine()
        questions = engine.get_questions("ai_ml_engineer")
        answer   = engine.evaluate_answer(questions[0], "My answer text")
    """

    # Minimum number of characters for an answer to be considered non-trivial
    MIN_ANSWER_LENGTH: int = 10

    def get_questions(self, role_slug: str) -> List[Dict]:
        """
        Return a shuffled copy of the interview questions for the given role.

        Raises InvalidCareerRoleError if the role slug is unrecognised.
        """
        if role_slug not in cd.INTERVIEW_QUESTIONS:
            raise InvalidCareerRoleError(
                f"No interview questions found for role '{role_slug}'."
            )
        questions = list(cd.INTERVIEW_QUESTIONS[role_slug])
        random.shuffle(questions)
        return questions

    def evaluate_answer(self, question: Dict, answer_text: str) -> InterviewAnswer:
        """
        Evaluate a student's answer for one interview question.

        Returns an InterviewAnswer with a score (0.0–1.0) and feedback message.
        Raises InvalidInterviewAnswerError if the answer is blank.
        """
        if not answer_text.strip():
            raise InvalidInterviewAnswerError("Answer must not be empty.")

        keywords_found, score = self._score_answer(
            answer_text, question.get("expected_keywords", [])
        )
        feedback_message = self._build_feedback(answer_text, score, keywords_found)

        return InterviewAnswer(
            question_id=question["id"],
            question_text=question["text"],
            answer_text=answer_text,
            score=round(score, 2),
            feedback_message=feedback_message,
            keywords_found=keywords_found,
        )

    def start_session(self, profile: StudentProfile) -> InterviewSession:
        """Create and return a new (incomplete) interview session for a profile."""
        return InterviewSession(
            profile_id=profile.profile_id,
            role=profile.target_role,
        )

    def finish_session(self, session: InterviewSession) -> InterviewSession:
        """
        Mark the session as completed and compute the overall session score.

        The session score is the average of individual answer scores.
        """
        if session.answers:
            session.session_score = round(
                sum(a.score for a in session.answers) / len(session.answers), 2
            )
        session.completed = True
        return session

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _tokenise(self, text: str) -> List[str]:
        """Lowercase the text and split into individual words, removing punctuation."""
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text.split()

    def _score_answer(
        self, answer_text: str, expected_keywords: List[str]
    ) -> Tuple[List[str], float]:
        """
        Check how many of the expected keywords appear in the answer.

        Returns (keywords_found, score).
        score = matched / total keywords.  Returns 0.0 when no keywords are defined.
        """
        if not expected_keywords:
            return [], 0.0

        tokens = set(self._tokenise(answer_text))
        found = []
        for kw in expected_keywords:
            # A keyword can be a single word or a short phrase
            kw_lower = kw.lower()
            if kw_lower in answer_text.lower():
                found.append(kw)

        score = len(found) / len(expected_keywords)
        return found, score

    def _build_feedback(
        self, answer_text: str, score: float, keywords_found: List[str]
    ) -> str:
        """Build a plain-English feedback message based on the score."""
        lines = ["⚠️  This is basic AI-style practice feedback — not professional evaluation.\n"]

        # Length check
        if len(answer_text.strip()) < self.MIN_ANSWER_LENGTH:
            lines.append("❌  Your answer is too short. Try to explain your reasoning in full sentences.")
            return " ".join(lines)

        # Keyword-based rating
        if score >= 0.75:
            lines.append("✅  Great answer! You covered most of the key concepts.")
        elif score >= 0.5:
            lines.append("👍  Good attempt. You hit several important points.")
        elif score >= 0.25:
            lines.append("📝  Partial answer. Try to include more technical detail.")
        else:
            lines.append("💡  Keep practising! Try to mention the core concepts in your answer.")

        if keywords_found:
            lines.append(f"Key concepts mentioned: {', '.join(keywords_found)}.")

        # Encourage examples
        example_hints = ("example", "for instance", "such as", "e.g.", "i used", "i built")
        if any(hint in answer_text.lower() for hint in example_hints):
            lines.append("🌟  Nice — you included a real example, which strengthens your answer.")

        return "  ".join(lines)
