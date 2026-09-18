"""
Persistence layer — reads and writes all application data to a single JSON file.

The file schema is:
{
    "profiles":           { "<profile_id>": { ...StudentProfile } },
    "interview_sessions": { "<session_id>": { ...InterviewSession } },
    "missions":           { "<profile_id>": [ { ...Mission }, ... ] }
}
"""

import json
import os
from typing import Dict, List, Optional

from exceptions import DataStorageError
from models import InterviewSession, Mission, StudentProfile


# ---------------------------------------------------------------------------
# Default empty store structure
# ---------------------------------------------------------------------------

def _empty_store() -> Dict:
    return {"profiles": {}, "interview_sessions": {}, "missions": {}}


# ---------------------------------------------------------------------------
# ProfileStore
# ---------------------------------------------------------------------------

class ProfileStore:
    """Manages all persistent data for the AI Career Twin application."""

    def __init__(self, file_path: str) -> None:
        """
        Initialise the store with the given file path.

        The file is not opened until the first read or write operation.
        """
        self.file_path = file_path

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def _load_raw(self) -> Dict:
        """
        Read the JSON file and return the raw dict.

        Returns an empty store structure if the file does not exist.
        Raises DataStorageError if the file exists but cannot be parsed.
        """
        if not os.path.exists(self.file_path):
            return _empty_store()
        try:
            with open(self.file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Ensure all top-level keys are present (forward-compatibility)
            for key in ("profiles", "interview_sessions", "missions"):
                data.setdefault(key, {})
            return data
        except json.JSONDecodeError as exc:
            raise DataStorageError(
                f"Could not parse '{self.file_path}': {exc}"
            ) from exc
        except OSError as exc:
            raise DataStorageError(
                f"Could not read '{self.file_path}': {exc}"
            ) from exc

    def _save_raw(self, data: Dict) -> None:
        """Write the full data dict back to the JSON file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise DataStorageError(
                f"Could not write to '{self.file_path}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Profile operations
    # ------------------------------------------------------------------

    def get_all_profiles(self) -> List[StudentProfile]:
        """Return all saved profiles, sorted by creation time."""
        data = self._load_raw()
        profiles = [
            StudentProfile.from_dict(p) for p in data["profiles"].values()
        ]
        return sorted(profiles, key=lambda p: p.created_at)

    def get_profile(self, profile_id: str) -> Optional[StudentProfile]:
        """Return the profile with the given id, or None if not found."""
        data = self._load_raw()
        raw = data["profiles"].get(profile_id)
        if raw is None:
            return None
        return StudentProfile.from_dict(raw)

    def save_profile(self, profile: StudentProfile) -> None:
        """Insert or update a profile in the store."""
        data = self._load_raw()
        data["profiles"][profile.profile_id] = profile.to_dict()
        self._save_raw(data)

    def delete_profile(self, profile_id: str) -> None:
        """Remove a profile and all its associated data from the store."""
        data = self._load_raw()
        data["profiles"].pop(profile_id, None)
        # Remove associated interview sessions
        sessions_to_remove = [
            sid for sid, s in data["interview_sessions"].items()
            if s.get("profile_id") == profile_id
        ]
        for sid in sessions_to_remove:
            del data["interview_sessions"][sid]
        # Remove associated missions
        data["missions"].pop(profile_id, None)
        self._save_raw(data)

    # ------------------------------------------------------------------
    # Mission operations
    # ------------------------------------------------------------------

    def get_missions(self, profile_id: str) -> List[Mission]:
        """Return all missions for a profile."""
        data = self._load_raw()
        raw_list = data["missions"].get(profile_id, [])
        return [Mission.from_dict(m) for m in raw_list]

    def save_missions(self, profile_id: str, missions: List[Mission]) -> None:
        """Overwrite the mission list for a profile."""
        data = self._load_raw()
        data["missions"][profile_id] = [m.to_dict() for m in missions]
        self._save_raw(data)

    # ------------------------------------------------------------------
    # Interview session operations
    # ------------------------------------------------------------------

    def get_sessions_for_profile(self, profile_id: str) -> List[InterviewSession]:
        """Return all interview sessions for a profile, oldest first."""
        data = self._load_raw()
        sessions = [
            InterviewSession.from_dict(s)
            for s in data["interview_sessions"].values()
            if s.get("profile_id") == profile_id
        ]
        return sorted(sessions, key=lambda s: s.started_at)

    def save_session(self, session: InterviewSession) -> None:
        """Insert or update an interview session in the store."""
        data = self._load_raw()
        data["interview_sessions"][session.session_id] = session.to_dict()
        self._save_raw(data)
