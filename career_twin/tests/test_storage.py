"""
Tests for ProfileStore — JSON persistence.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest

from exceptions import DataStorageError
from models import InterviewSession, Mission, StudentProfile, StudentSkill
from storage import ProfileStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_profile(name="Alice", role="data_analyst") -> StudentProfile:
    return StudentProfile(
        name=name,
        target_role=role,
        skills=[StudentSkill("Python", "Advanced")],
    )


# ---------------------------------------------------------------------------
# Basic I/O
# ---------------------------------------------------------------------------

class TestProfileStore:
    def test_load_non_existent_file_returns_empty(self, tmp_path):
        store = ProfileStore(str(tmp_path / "missing.json"))
        profiles = store.get_all_profiles()
        assert profiles == []

    def test_save_and_retrieve_profile(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        store.save_profile(profile)
        retrieved = store.get_profile(profile.profile_id)
        assert retrieved is not None
        assert retrieved.name == "Alice"

    def test_get_unknown_profile_returns_none(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        result = store.get_profile("nonexistent-id")
        assert result is None

    def test_save_multiple_profiles(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        p1 = make_profile("Alice")
        p2 = make_profile("Bob")
        store.save_profile(p1)
        store.save_profile(p2)
        all_profiles = store.get_all_profiles()
        names = {p.name for p in all_profiles}
        assert names == {"Alice", "Bob"}

    def test_upsert_updates_existing_profile(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile("Alice")
        store.save_profile(profile)
        profile.name = "Alice Updated"
        store.save_profile(profile)
        retrieved = store.get_profile(profile.profile_id)
        assert retrieved.name == "Alice Updated"
        assert len(store.get_all_profiles()) == 1

    def test_delete_profile(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        store.save_profile(profile)
        store.delete_profile(profile.profile_id)
        assert store.get_profile(profile.profile_id) is None

    def test_delete_nonexistent_profile_is_silent(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        store.delete_profile("does-not-exist")  # should not raise

    def test_corrupted_json_raises_datastorage_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{", encoding="utf-8")
        store = ProfileStore(str(path))
        with pytest.raises(DataStorageError):
            store.get_all_profiles()


# ---------------------------------------------------------------------------
# Missions
# ---------------------------------------------------------------------------

class TestMissions:
    def test_save_and_retrieve_missions(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        missions = [
            Mission(cadence="daily", task="Practice Python"),
            Mission(cadence="weekly", task="Complete a tutorial"),
        ]
        store.save_missions(profile.profile_id, missions)
        loaded = store.get_missions(profile.profile_id)
        assert len(loaded) == 2
        assert loaded[0].task == "Practice Python"

    def test_no_missions_returns_empty_list(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        assert store.get_missions("unknown-id") == []

    def test_mission_completion_persists(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        missions = [Mission(cadence="daily", task="Task A", completed=False)]
        store.save_missions(profile.profile_id, missions)
        missions[0].completed = True
        store.save_missions(profile.profile_id, missions)
        loaded = store.get_missions(profile.profile_id)
        assert loaded[0].completed is True


# ---------------------------------------------------------------------------
# Interview sessions
# ---------------------------------------------------------------------------

class TestInterviewSessions:
    def test_save_and_retrieve_session(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        session = InterviewSession(
            profile_id=profile.profile_id,
            role="data_analyst",
            session_score=0.75,
            completed=True,
        )
        store.save_session(session)
        sessions = store.get_sessions_for_profile(profile.profile_id)
        assert len(sessions) == 1
        assert sessions[0].session_score == 0.75

    def test_sessions_for_other_profile_not_returned(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        p1 = make_profile("Alice")
        p2 = make_profile("Bob")
        s1 = InterviewSession(profile_id=p1.profile_id, role="data_analyst")
        store.save_session(s1)
        assert store.get_sessions_for_profile(p2.profile_id) == []

    def test_no_sessions_returns_empty_list(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        assert store.get_sessions_for_profile("unknown") == []

    def test_delete_profile_removes_sessions(self, tmp_path):
        store = ProfileStore(str(tmp_path / "data.json"))
        profile = make_profile()
        store.save_profile(profile)
        session = InterviewSession(profile_id=profile.profile_id, role="data_analyst")
        store.save_session(session)
        store.delete_profile(profile.profile_id)
        assert store.get_sessions_for_profile(profile.profile_id) == []
