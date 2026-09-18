# AI Career Twin — Implementation Plan

## Top-Level Overview

**Goal:** Build a beginner-friendly Python + Streamlit application that helps students assess their career readiness, identify skill gaps, follow a personalized learning roadmap, practice mock interviews, and track progress over time.

**Scope:**
- Pure Python business logic, fully separated from Streamlit UI code
- Object-Oriented design with type hints throughout
- JSON file for persistence (student profiles + interview history)
- The student chooses the save-file path inside the app
- Multiple named student profiles supported in one file
- Interview history accumulates across sessions
- Career-readiness score is a transparent, equally-weighted indicator across five criteria
- Mock interview feedback is keyword-based (no external APIs or ML)
- pytest for unit testing of all business logic

**Non-goals:**
- No authentication, cloud services, or database
- No real ML models, voice, or video
- No external APIs
- No complex design patterns (no dependency injection, no event bus, etc.)

---

## Architecture Overview

```
ai_career_twin/
├── app.py                     # Streamlit entry point — page routing only
├── data/
│   └── static_data.py         # All static role/skill/question definitions
├── models/
│   ├── profile.py             # StudentProfile, StudentSkill, Education, Project
│   ├── role.py                # CareerRole, Question, Feedback
│   ├── analysis.py            # SkillGapResult, Roadmap, Mission
│   └── interview.py           # InterviewSession, InterviewAnswer
├── services/
│   ├── analyzer.py            # SkillGapAnalyzer
│   ├── roadmap_generator.py   # RoadmapGenerator
│   ├── mission_generator.py   # MissionGenerator
│   ├── interview_engine.py    # InterviewEngine
│   ├── readiness_calculator.py# ReadinessCalculator
│   └── persistence.py         # ProfileStore (JSON read/write)
├── ui/
│   ├── profile_page.py        # Streamlit profile setup page
│   ├── analysis_page.py       # Skill gap + roadmap page
│   ├── missions_page.py       # Career missions page
│   ├── interview_page.py      # Mock interview page
│   └── dashboard_page.py      # Dashboard / progress page
├── exceptions.py              # All custom exceptions
└── tests/
    ├── test_analyzer.py
    ├── test_roadmap_generator.py
    ├── test_mission_generator.py
    ├── test_interview_engine.py
    ├── test_readiness_calculator.py
    └── test_persistence.py
```

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold & Static Data

**Intent:** Create the folder structure, empty module files, and all static reference data (roles, required skills, interview questions). This gives every other sub-task a stable foundation to build on.

**Expected Outcomes:**
- All folders and `__init__.py` files exist
- `exceptions.py` contains all custom exception classes
- `data/static_data.py` contains the four career roles, their required skill lists, and at least five interview questions per role with expected keyword lists

**Todo List:**
1. Create all folders: `data/`, `models/`, `services/`, `ui/`, `tests/`
2. Add empty `__init__.py` to each package folder
3. Write `exceptions.py` with these classes, all subclassing `ValueError` unless noted:
   - `InvalidRoleError`
   - `EmptySkillsError`
   - `InvalidProficiencyError`
   - `InvalidURLError`
   - `DuplicateSkillError`
   - `EmptyAnswerError`
   - `NoRoleSelectedError`
   - `ProfileNotFoundError`
   - `PersistenceError` (subclass `IOError`)
4. Write `data/static_data.py`:
   - `CAREER_ROLES`: dict keyed by role slug, each entry has `role_name`, `description`, `required_skills` (list of skill name strings)
   - Four roles: `ai_ml_engineer`, `software_developer`, `data_analyst`, `cybersecurity_analyst`
   - Each role has 8–12 required skills
   - `INTERVIEW_QUESTIONS`: dict keyed by role slug, each entry is a list of dicts with `id`, `text`, `expected_keywords`
   - At least 5 questions per role
   - `SKILL_ALIASES`: dict mapping common abbreviations to canonical skill names (e.g. `"ML"` → `"Machine Learning"`)
   - `PROFICIENCY_LEVELS`: ordered list `["Beginner", "Intermediate", "Advanced"]`
   - `PROFICIENCY_RANK`: dict mapping each level to an integer rank for comparison
   - `ROLE_SLUGS`: list of valid role slug strings

**Relevant Context:** No existing code. This sub-task produces the shared reference data all services depend on.

**Status:** [ ] pending

---

### Sub-Task 2 — Data Models

**Intent:** Define all data-holding classes using Python dataclasses with type hints. These are pure data containers — no business logic inside them.

**Expected Outcomes:**
- All model classes are importable and instantiable
- Each model has a `to_dict()` and a `from_dict()` classmethod for JSON serialization
- No business logic lives inside model classes

**Todo List:**

1. Write `models/profile.py`:
   - `Education` dataclass: `institution: str`, `degree: str`, `year: str`
   - `Project` dataclass: `title: str`, `description: str`
   - `StudentSkill` dataclass: `skill_name: str`, `proficiency: str`
   - `StudentProfile` dataclass:
     - `profile_id: str` (UUID string, generated on creation)
     - `name: str`
     - `email: str` (optional, default `""`)
     - `target_role: str` (role slug, default `""`)
     - `education: list[Education]` (default empty list)
     - `projects: list[Project]` (default empty list)
     - `skills: list[StudentSkill]` (default empty list)
     - `github_url: str` (optional, default `""`)
     - `created_at: str` (ISO datetime string)
   - Each class: `to_dict()` returns a plain dict; `from_dict(data: dict)` classmethod reconstructs the object

2. Write `models/role.py`:
   - `CareerRole` dataclass: `slug: str`, `role_name: str`, `description: str`, `required_skills: list[str]`
   - `Question` dataclass: `id: str`, `text: str`, `expected_keywords: list[str]`, `role: str`
   - `Feedback` dataclass: `is_good: bool`, `message: str`, `keywords_found: list[str]`, `score: float` (0.0–1.0, fraction of keywords matched)

3. Write `models/analysis.py`:
   - `SkillGapResult` dataclass:
     - `strong_skills: list[str]` (matched at Intermediate or Advanced)
     - `needs_improvement: list[str]` (matched by name but only Beginner)
     - `missing_skills: list[str]` (not present at all)
     - `readiness_from_skills: float` (0.0–1.0)
   - `RoadmapStep` dataclass: `skill: str`, `why: str`, `resource_hint: str`
   - `Roadmap` dataclass: `steps: list[RoadmapStep]`
   - `Mission` dataclass: `cadence: str` (e.g. `"daily"` or `"weekly"`), `task: str`

4. Write `models/interview.py`:
   - `InterviewAnswer` dataclass: `question_id: str`, `question_text: str`, `answer_text: str`, `feedback: Feedback`, `answered_at: str`
   - `InterviewSession` dataclass:
     - `session_id: str` (UUID string)
     - `profile_id: str`
     - `role: str`
     - `answers: list[InterviewAnswer]`
     - `session_score: float` (0.0–1.0, average of per-answer scores)
     - `started_at: str`
     - `completed: bool`
   - Both: `to_dict()` and `from_dict()` methods

**Relevant Context:** Depends on Sub-Task 1 for `PROFICIENCY_LEVELS`. No services depend on models yet.

**Status:** [ ] pending

---

### Sub-Task 3 — Persistence Service

**Intent:** Build the single file-based persistence layer that reads and writes all student profiles and interview sessions to a JSON file chosen by the user.

**Expected Outcomes:**
- `ProfileStore` can load from and save to any valid file path the user provides
- Multiple profiles are stored in a single JSON file under a `profiles` key
- Interview sessions are stored under an `interview_sessions` key, keyed by `session_id`
- All IO errors surface as `PersistenceError`

**Todo List:**

1. Write `services/persistence.py` with class `ProfileStore`:

   **Constructor:** `__init__(self, file_path: str)` — stores the path; does not open the file yet

   **Methods:**
   - `load() -> dict`: reads the JSON file; if file does not exist, returns `{"profiles": {}, "interview_sessions": {}}`; raises `PersistenceError` on malformed JSON
   - `save(data: dict) -> None`: writes the full data dict to the file as pretty-printed JSON; raises `PersistenceError` on IO failure
   - `get_all_profiles() -> list[StudentProfile]`: loads file, returns all profiles as model objects
   - `get_profile(profile_id: str) -> StudentProfile`: raises `ProfileNotFoundError` if not found
   - `save_profile(profile: StudentProfile) -> None`: upserts profile by `profile_id`
   - `delete_profile(profile_id: str) -> None`: removes profile; raises `ProfileNotFoundError` if missing
   - `get_sessions_for_profile(profile_id: str) -> list[InterviewSession]`: returns all sessions for a given profile, sorted by `started_at` ascending
   - `save_session(session: InterviewSession) -> None`: upserts session by `session_id`

2. File schema (JSON structure):
   ```
   {
     "profiles": {
       "<profile_id>": { ...StudentProfile.to_dict() }
     },
     "interview_sessions": {
       "<session_id>": { ...InterviewSession.to_dict() }
     }
   }
   ```

**Relevant Context:** Depends on Sub-Tasks 1 and 2. Used by the Streamlit UI pages to persist state between sessions.

**Status:** [ ] pending

---

### Sub-Task 4 — Skill Gap Analyzer

**Intent:** Implement the service that compares a student's skills against a role's required skills and produces a `SkillGapResult`.

**Expected Outcomes:**
- `SkillGapAnalyzer.analyze()` correctly classifies every required skill into strong, needs_improvement, or missing
- Score is computed as `(strong_count + 0.5 * needs_improvement_count) / total_required`
- Skill name comparison is case-insensitive and alias-aware
- Raises `EmptySkillsError` if the profile has no skills
- Raises `NoRoleSelectedError` if `target_role` is empty
- Raises `InvalidRoleError` if the role slug does not exist in `CAREER_ROLES`

**Todo List:**

1. Write `services/analyzer.py` with class `SkillGapAnalyzer`:

   **Constructor:** `__init__(self)` — no dependencies; reads from `static_data`

   **Private helpers:**
   - `_normalize(name: str) -> str`: lowercases, strips, resolves aliases via `SKILL_ALIASES`
   - `_is_strong(skill: StudentSkill) -> bool`: returns True if proficiency rank >= Intermediate rank
   - `_find_student_skill(skill_name: str, skills: list[StudentSkill]) -> StudentSkill | None`: finds a student skill by normalized name

   **Public method:**
   - `analyze(profile: StudentProfile) -> SkillGapResult`:
     1. Validate profile (raises on empty skills or missing role)
     2. Look up `CareerRole` from `CAREER_ROLES` (raises `InvalidRoleError` if not found)
     3. For each required skill, classify into strong / needs_improvement / missing
     4. Compute `readiness_from_skills` score
     5. Return `SkillGapResult`

**Relevant Context:** Depends on Sub-Tasks 1 and 2. Called by the analysis page and readiness calculator.

**Status:** [ ] pending

---

### Sub-Task 5 — Roadmap Generator

**Intent:** Produce a `Roadmap` — an ordered list of learning steps — from a `SkillGapResult`. Missing skills come first (highest priority), then needs-improvement skills.

**Expected Outcomes:**
- Steps for missing skills appear before steps for needs-improvement skills
- Each step has a `why` string explaining the priority
- Each step has a `resource_hint` (a plain text suggestion, e.g. "Practice on freeCodeCamp")
- Resource hints are defined as simple static strings per skill in `static_data.py`

**Todo List:**

1. Add `RESOURCE_HINTS: dict[str, str]` to `data/static_data.py` — a mapping from skill name (lowercase) to a one-line resource suggestion. Provide hints for every skill in all four role skill lists. Use a generic fallback string for any skill not in the map.

2. Write `services/roadmap_generator.py` with class `RoadmapGenerator`:

   **Constructor:** `__init__(self)` — no dependencies

   **Public method:**
   - `generate(gap_result: SkillGapResult) -> Roadmap`:
     1. Build steps for missing skills first (why = "Required skill you haven't started yet")
     2. Build steps for needs-improvement skills second (why = "You know this but need to reach Intermediate level")
     3. Look up `resource_hint` from `RESOURCE_HINTS`; fall back to generic string if not found
     4. Return `Roadmap(steps=...)`

**Relevant Context:** Depends on Sub-Tasks 1, 2, and 4. Called by the analysis page.

**Status:** [ ] pending

---

### Sub-Task 6 — Mission Generator

**Intent:** Turn a `Roadmap` into a flat list of concrete daily and weekly `Mission` tasks that a student can act on immediately.

**Expected Outcomes:**
- First 3 roadmap steps each produce one daily mission and one weekly mission
- Remaining steps produce only weekly missions
- Daily missions are short, action-verb-first sentences (e.g. "Practice Python for 30 minutes today")
- Weekly missions are broader goal statements (e.g. "Complete one Python tutorial this week")
- If the roadmap is empty, returns an empty mission list

**Todo List:**

1. Write `services/mission_generator.py` with class `MissionGenerator`:

   **Constructor:** `__init__(self)` — no dependencies

   **Private helpers:**
   - `_daily_task(skill: str) -> str`: returns a formatted daily task string for a skill
   - `_weekly_task(skill: str) -> str`: returns a formatted weekly task string for a skill

   **Public method:**
   - `generate(roadmap: Roadmap) -> list[Mission]`:
     1. Iterate roadmap steps
     2. First 3 steps: append one `Mission(cadence="daily", ...)` and one `Mission(cadence="weekly", ...)`
     3. Steps 4+: append only one `Mission(cadence="weekly", ...)`
     4. Return the full list

**Relevant Context:** Depends on Sub-Tasks 2 and 5. Called by the missions page.

**Status:** [ ] pending

---

### Sub-Task 7 — Interview Engine

**Intent:** Implement the service that retrieves interview questions for a role and evaluates student answers using keyword matching.

**Expected Outcomes:**
- `get_questions()` returns a shuffled list of questions for the given role
- `evaluate_answer()` computes a score and constructs a `Feedback` object
- Score is `matched_keyword_count / total_keywords` for the question (0.0 if no keywords defined)
- `is_good` is True when score >= 0.5
- Raises `InvalidRoleError` if role not found
- Raises `EmptyAnswerError` if answer text is blank

**Todo List:**

1. Write `services/interview_engine.py` with class `InterviewEngine`:

   **Constructor:** `__init__(self)` — no dependencies

   **Private helpers:**
   - `_tokenize(text: str) -> list[str]`: lowercases and splits answer into words; strips punctuation
   - `_score(keywords_found: list[str], total_keywords: int) -> float`: safe division

   **Public methods:**
   - `get_questions(role: str) -> list[Question]`:
     1. Validate role (raises `InvalidRoleError`)
     2. Look up questions from `INTERVIEW_QUESTIONS`
     3. Return a shuffled copy (use `random.sample`)
   - `evaluate_answer(question: Question, answer: str) -> Feedback`:
     1. Validate answer (raises `EmptyAnswerError` if blank)
     2. Tokenize answer
     3. Find which expected keywords appear in the tokenized answer
     4. Compute score
     5. Build feedback message: if `is_good`, positive canned message; otherwise constructive canned message
     6. Return `Feedback`

**Relevant Context:** Depends on Sub-Tasks 1 and 2. Called by the interview page.

**Status:** [ ] pending

---

### Sub-Task 8 — Readiness Calculator

**Intent:** Compute the overall career-readiness score (0–100%) by equally weighting five transparent criteria.

**Expected Outcomes:**
- Score is the average of five component scores, each 0.0–1.0, multiplied by 100
- Each component is calculated independently and returned alongside the total so the UI can display a breakdown
- The scoring formula is clearly documented in the code

**Todo List:**

1. Write `services/readiness_calculator.py` with class `ReadinessCalculator`:

   **Constructor:** `__init__(self)` — no dependencies

   **The five components and their scoring rules:**

   | Component | Rule |
   |---|---|
   | `skills_score` | From `SkillGapResult.readiness_from_skills` (already 0.0–1.0) |
   | `proficiency_score` | Average proficiency rank of all student skills, normalized to 0.0–1.0 using `max_rank` |
   | `projects_score` | `min(len(projects) / 3, 1.0)` — 3 or more projects = full score |
   | `profile_score` | Count of non-empty optional fields (email, github_url, each education entry, each project) divided by a fixed max of 6 |
   | `interview_score` | Average `session_score` across all completed interview sessions for the profile; 0.0 if no sessions |

   **Public method:**
   - `calculate(profile: StudentProfile, gap_result: SkillGapResult, sessions: list[InterviewSession]) -> dict`:
     Returns a dict with keys: `skills_score`, `proficiency_score`, `projects_score`, `profile_score`, `interview_score`, `total_score` (all as floats 0.0–100.0)

**Relevant Context:** Depends on Sub-Tasks 1, 2, 4, and 7. Called by the dashboard page.

**Status:** [ ] pending

---

### Sub-Task 9 — Streamlit UI Pages

**Intent:** Build the five Streamlit pages that wire up the business logic services to a user-facing interface. All pages must read/write state through `st.session_state` and call services directly — no business logic inside UI code.

**Expected Outcomes:**
- The app runs with `streamlit run app.py`
- Each page renders correctly and calls the appropriate service
- Profile changes are only persisted when the student clicks "Save Profile"
- The student can select a save-file path before creating or loading a profile
- Role change mid-session triggers a confirmation dialog and clears previous analysis

**Todo List:**

1. Write `app.py`:
   - Sidebar navigation with five entries: Profile, Analysis, Missions, Interview, Dashboard
   - Initialize `st.session_state` keys on first load: `current_profile`, `store`, `gap_result`, `roadmap`, `missions`, `current_session`
   - Route to the selected page module

2. Write `ui/profile_page.py` — `render()` function:
   - File path input at the top; "Load / Create Store" button initializes `ProfileStore` in session state
   - Profile selector dropdown (existing profiles from store + "Create New")
   - Form fields: name, email, target role (selectbox), skills (add/remove rows with skill name + proficiency dropdown), education (add/remove rows), projects (add/remove rows), GitHub URL
   - "Save Profile" button: validates inputs, calls `store.save_profile()`, shows success/error message
   - Inline validation messages for each field (no page reload required)

3. Write `ui/analysis_page.py` — `render()` function:
   - Guard: redirect to Profile page if no profile loaded
   - "Run Analysis" button: calls `SkillGapAnalyzer.analyze()`, stores result in session state
   - Three columns: Strong Skills (green), Needs Improvement (yellow), Missing Skills (red)
   - Roadmap section below: calls `RoadmapGenerator.generate()`, displays numbered steps with `why` and `resource_hint`

4. Write `ui/missions_page.py` — `render()` function:
   - Guard: redirect if no gap result
   - Calls `MissionGenerator.generate()` from session state roadmap
   - Two sections: Daily Missions (checkbox list), Weekly Missions (checkbox list)
   - Checkboxes are UI-only (not persisted)

5. Write `ui/interview_page.py` — `render()` function:
   - Guard: redirect if no profile loaded
   - "Start New Interview" button: calls `InterviewEngine.get_questions()`, creates a new `InterviewSession` in session state
   - Shows one question at a time with a text area for the answer and a "Submit Answer" button
   - After each submit: calls `evaluate_answer()`, displays `Feedback` inline
   - "Finish Interview" button: computes `session_score`, marks `completed=True`, calls `store.save_session()`
   - Previous sessions section: shows past session scores in a simple table

6. Write `ui/dashboard_page.py` — `render()` function:
   - Guard: redirect if no profile loaded
   - Calls `ReadinessCalculator.calculate()`
   - Top: profile summary card (name, role, education count, project count)
   - Progress section: `st.progress()` bar for total score; expandable breakdown of five components with short explanations
   - Strengths and gaps summary (from latest `SkillGapResult` in session state)
   - Roadmap summary (first 3 steps)
   - Interview history table (session date, score, role)

**Relevant Context:** Depends on all previous sub-tasks. This is the final integration layer.

**Status:** [ ] pending

---

### Sub-Task 10 — Unit Tests

**Intent:** Write pytest tests for all five service classes. Tests should cover happy paths, edge cases, and exception-raising conditions. No Streamlit code is tested — only the business logic services.

**Expected Outcomes:**
- All tests pass with `pytest tests/`
- Each service has at least one test file
- Tests use only standard library + pytest (no mocking libraries unless needed)
- Test fixtures use hardcoded sample data (no file I/O except persistence tests which use `tmp_path`)

**Todo List:**

1. Write `tests/test_analyzer.py`:
   - Test: all required skills present at Intermediate → `missing_skills` is empty, score = 1.0
   - Test: no skills present → score = 0.0, all in `missing_skills`
   - Test: one skill at Beginner → in `needs_improvement`, score < 1.0
   - Test: empty skills list → raises `EmptySkillsError`
   - Test: empty role → raises `NoRoleSelectedError`
   - Test: invalid role slug → raises `InvalidRoleError`
   - Test: skill alias resolves correctly (e.g. `"ML"` matches `"Machine Learning"`)

2. Write `tests/test_roadmap_generator.py`:
   - Test: missing skills produce steps before needs-improvement steps
   - Test: empty gap result → empty roadmap
   - Test: resource hint fallback is used when skill not in `RESOURCE_HINTS`

3. Write `tests/test_mission_generator.py`:
   - Test: first 3 roadmap steps produce both daily and weekly missions
   - Test: step 4+ produces only weekly missions
   - Test: empty roadmap → empty mission list

4. Write `tests/test_interview_engine.py`:
   - Test: `get_questions()` returns correct role's questions
   - Test: invalid role → raises `InvalidRoleError`
   - Test: blank answer → raises `EmptyAnswerError`
   - Test: answer with all expected keywords → `is_good=True`, score=1.0
   - Test: answer with no keywords → `is_good=False`, score=0.0
   - Test: answer with some keywords → score between 0 and 1

5. Write `tests/test_readiness_calculator.py`:
   - Test: profile with 3 projects → `projects_score` = 100.0
   - Test: profile with 1 project → `projects_score` ≈ 33.3
   - Test: no interview sessions → `interview_score` = 0.0
   - Test: two sessions with scores 0.5 and 1.0 → `interview_score` = 75.0
   - Test: total score is average of the five components

6. Write `tests/test_persistence.py`:
   - Use pytest `tmp_path` fixture for all file operations
   - Test: save and reload a profile roundtrip
   - Test: load from non-existent file → returns empty data dict
   - Test: `get_profile` with unknown id → raises `ProfileNotFoundError`
   - Test: save two profiles, retrieve both
   - Test: save session, retrieve by profile id

**Relevant Context:** Depends on all service sub-tasks. Run after each sub-task is implemented to validate correctness.

**Status:** [ ] pending

---

## Data Flow

```
Student Input (Streamlit UI)
        │
        ▼
  ProfileStore (persistence.py)
        │
        ▼
  StudentProfile (models/profile.py)
        │
        ├──► SkillGapAnalyzer ──► SkillGapResult
        │           │
        │           ▼
        │    RoadmapGenerator ──► Roadmap
        │           │
        │           ▼
        │    MissionGenerator ──► list[Mission]
        │
        ├──► InterviewEngine ──► list[Question]
        │           │
        │           ▼
        │    InterviewSession + InterviewAnswer + Feedback
        │           │
        │           ▼
        │    ProfileStore (save_session)
        │
        └──► ReadinessCalculator ──► score dict
                    │
                    ▼
              Dashboard UI
```

---

## Validation Rules

| Field | Rule |
|---|---|
| `name` | Required, non-empty, max 100 chars, letters and spaces only |
| `email` | Optional; if provided must match `x@y.z` pattern |
| `target_role` | Must be a valid key in `ROLE_SLUGS` |
| `skill_name` | Required per skill, non-empty, max 50 chars |
| `proficiency` | Must be exactly one of `PROFICIENCY_LEVELS` |
| `github_url` | Optional; if provided must start with `https://github.com/` or `https://linkedin.com/` |
| `project.title` | Non-empty if project block is filled; max 100 chars |
| `project.description` | Optional; max 500 chars |
| `interview answer` | Non-empty before submission; max 1000 chars |
| Skills list | At least 1 skill before `analyze()` is called |
| Duplicate skill | Same normalized skill name may not appear twice in a profile |

---

## Exception Handling

| Exception | Raised by | Caught by |
|---|---|---|
| `InvalidRoleError` | `SkillGapAnalyzer`, `InterviewEngine` | Analysis and interview UI pages |
| `EmptySkillsError` | `SkillGapAnalyzer` | Analysis page |
| `InvalidProficiencyError` | Validation helper | Profile page |
| `InvalidURLError` | Validation helper | Profile page |
| `DuplicateSkillError` | Validation helper | Profile page |
| `EmptyAnswerError` | `InterviewEngine` | Interview page |
| `NoRoleSelectedError` | `SkillGapAnalyzer` | Analysis page |
| `ProfileNotFoundError` | `ProfileStore` | Profile page |
| `PersistenceError` | `ProfileStore` | Profile page, interview page |

All UI pages wrap service calls in try/except and display `st.error(str(e))` messages.

---

## JSON Persistence Design

**File location:** Chosen by the student via a text input in the Profile page. Stored in `st.session_state["store_path"]`.

**File structure:**
```json
{
  "profiles": {
    "<uuid>": {
      "profile_id": "...",
      "name": "...",
      "email": "...",
      "target_role": "...",
      "education": [...],
      "projects": [...],
      "skills": [...],
      "github_url": "...",
      "created_at": "..."
    }
  },
  "interview_sessions": {
    "<uuid>": {
      "session_id": "...",
      "profile_id": "...",
      "role": "...",
      "answers": [...],
      "session_score": 0.0,
      "started_at": "...",
      "completed": false
    }
  }
}
```

**Write strategy:** Always read the full file → update the in-memory dict → write the full file back. File is small enough that this is acceptable.

---

## Development Order

Sub-tasks are listed in dependency order. Each one can be reviewed before the next begins.

```
Sub-Task 1 (Scaffold + Static Data)
    └── Sub-Task 2 (Data Models)
            └── Sub-Task 3 (Persistence)
            └── Sub-Task 4 (Skill Gap Analyzer)
                    └── Sub-Task 5 (Roadmap Generator)
                            └── Sub-Task 6 (Mission Generator)
            └── Sub-Task 7 (Interview Engine)
            └── Sub-Task 8 (Readiness Calculator)
                    └── Sub-Task 9 (Streamlit UI)
                            └── Sub-Task 10 (Unit Tests)
```

---

## Edge Cases

| # | Case | Handling |
|---|---|---|
| EC-01 | Student has all required skills at Intermediate+ | Readiness = 100% on skills component; show congratulations; roadmap is empty |
| EC-02 | Student has all skills at Beginner | skills_score = partial; all in needs_improvement; roadmap has full list |
| EC-03 | Role changed mid-session | Confirmation dialog; clear `gap_result`, `roadmap`, `missions` from session state |
| EC-04 | Skill alias near-match (ML vs Machine Learning) | Resolved by `_normalize()` using `SKILL_ALIASES` dict |
| EC-05 | No interview sessions completed | `interview_score = 0.0`; UI shows "No interviews yet" message |
| EC-06 | Save file path is invalid or unwriteable | `PersistenceError` displayed as `st.error()` |
| EC-07 | Student submits one-word or very short answer | No keywords matched; constructive feedback; not an error |
| EC-08 | Profile has zero projects | `projects_score = 0.0`; missions suggest building a project |
| EC-09 | Streamlit page refreshed unexpectedly | Session state cleared; store path must be re-entered; data is safe in JSON file |
| EC-10 | Duplicate skill name entered | `DuplicateSkillError` shown inline; skill not added |
