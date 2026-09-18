"""
AI Career Twin — Streamlit Application
=======================================

Run with:
    streamlit run app.py

All business logic lives in the sibling modules (career_analyzer, roadmap,
interview, storage).  This file contains only UI code.
"""

import sys
import os

# Allow imports from the career_twin/ package directory
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

import career_data as cd
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
    DataStorageError,
    InvalidCareerRoleError,
    InvalidInterviewAnswerError,
    InvalidSkillError,
    InvalidStudentProfileError,
)
from interview import InterviewEngine
from models import (
    Education,
    Mission,
    Project,
    StudentProfile,
    StudentSkill,
)
from roadmap import MissionGenerator, RoadmapGenerator
from storage import ProfileStore

# ---------------------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Career Twin",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

def _init_state() -> None:
    defaults = {
        "store": None,           # ProfileStore instance
        "store_path": "",        # path chosen by the user
        "profile": None,         # StudentProfile currently in view
        "gap_result": None,      # SkillGapResult
        "roadmap_steps": None,   # list[RoadmapStep]
        "missions": None,        # list[Mission]
        "interview_session": None,  # InterviewSession in progress
        "interview_questions": [],  # list[dict] for current session
        "current_q_index": 0,
        "page": "🏠 Profile",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_state()

# ---------------------------------------------------------------------------
# Sidebar — navigation & store setup
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🎯 AI Career Twin")
    st.caption("Personal Career Readiness & Interview Agent")
    st.divider()

    # File-path selector
    st.subheader("💾 Data File")
    path_input = st.text_input(
        "Save file path (e.g. career_data.json)",
        value=st.session_state["store_path"],
        placeholder="career_data.json",
    )
    if st.button("Connect", use_container_width=True):
        if not path_input.strip():
            st.error("Please enter a file path.")
        else:
            st.session_state["store_path"] = path_input.strip()
            st.session_state["store"] = ProfileStore(path_input.strip())
            st.success("Connected!")

    st.divider()

    # Navigation
    st.subheader("📋 Navigation")
    pages = [
        "🏠 Profile",
        "📊 Analysis",
        "🗺️ Roadmap",
        "🎯 Missions",
        "🎤 Interview",
        "📈 Dashboard",
    ]
    for page in pages:
        if st.button(page, use_container_width=True):
            st.session_state["page"] = page

    st.divider()
    if st.session_state["profile"]:
        st.caption(f"👤 {st.session_state['profile'].name}")
        role_slug = st.session_state["profile"].target_role
        if role_slug in cd.CAREER_ROLES:
            st.caption(f"🎯 {cd.CAREER_ROLES[role_slug]['role_name']}")

# ---------------------------------------------------------------------------
# Helper: require store
# ---------------------------------------------------------------------------

def _require_store() -> bool:
    """Show a warning and return False if no store is connected."""
    if st.session_state["store"] is None:
        st.warning("👈 Please enter a save file path in the sidebar and click **Connect** first.")
        return False
    return True


def _require_profile() -> bool:
    """Show a warning and return False if no profile is loaded."""
    if st.session_state["profile"] is None:
        st.warning("👈 Please create or load a profile on the **🏠 Profile** page first.")
        return False
    return True


def _require_analysis() -> bool:
    """Show a warning and return False if gap analysis has not been run."""
    if st.session_state["gap_result"] is None:
        st.warning("📊 Please run the **Skill Gap Analysis** first (go to the **📊 Analysis** page).")
        return False
    return True


# ===========================================================================
# PAGE: Profile
# ===========================================================================

def page_profile() -> None:
    st.header("🏠 Student Profile")

    if not _require_store():
        return

    store: ProfileStore = st.session_state["store"]

    # ---- Profile selector -------------------------------------------------
    st.subheader("Select or Create a Profile")
    try:
        existing = store.get_all_profiles()
    except DataStorageError as exc:
        st.error(str(exc))
        return

    profile_options = {f"{p.name} (id: {p.profile_id[:8]})": p for p in existing}
    options_list = ["➕ Create new profile"] + list(profile_options.keys())

    selected_label = st.selectbox("Profile", options_list)

    if selected_label != "➕ Create new profile":
        if st.button("Load selected profile"):
            loaded = profile_options[selected_label]
            st.session_state["profile"] = loaded
            # Clear previous analysis when profile changes
            st.session_state["gap_result"] = None
            st.session_state["roadmap_steps"] = None
            st.session_state["missions"] = None
            # Load saved missions
            try:
                st.session_state["missions"] = store.get_missions(loaded.profile_id)
            except DataStorageError:
                st.session_state["missions"] = []
            st.success(f"Loaded profile: {loaded.name}")

    st.divider()

    # ---- Profile form -----------------------------------------------------
    st.subheader("Profile Details")

    # Pre-fill from current profile if one is loaded
    current: StudentProfile = st.session_state["profile"] or StudentProfile(name="")

    with st.form("profile_form"):
        name = st.text_input("Full Name *", value=current.name)
        email = st.text_input("Email (optional)", value=current.email)
        github_url = st.text_input("GitHub / LinkedIn URL (optional)", value=current.github_url)

        # Role selection
        role_display_map = {
            v["role_name"]: k for k, v in cd.CAREER_ROLES.items()
        }
        role_names = list(role_display_map.keys())
        current_role_name = (
            cd.CAREER_ROLES[current.target_role]["role_name"]
            if current.target_role in cd.CAREER_ROLES
            else role_names[0]
        )
        selected_role_name = st.selectbox(
            "Target Career Role *",
            role_names,
            index=role_names.index(current_role_name),
        )

        st.divider()

        # Skills
        st.markdown("**Skills**")
        st.caption("Add your current skills and rate your proficiency.")

        # We use a dynamic list stored in session state outside the form
        submitted = st.form_submit_button("💾 Save Profile")

    # ---- Skills editor (outside form for dynamic add/remove) ---------------
    st.subheader("My Skills")
    _render_skills_editor(current)

    st.divider()

    # ---- Education editor --------------------------------------------------
    st.subheader("Education")
    _render_education_editor(current)

    st.divider()

    # ---- Projects editor ---------------------------------------------------
    st.subheader("Projects")
    _render_projects_editor(current)

    st.divider()

    # ---- Save --------------------------------------------------------------
    if st.button("💾 Save Profile", key="save_profile_bottom", type="primary"):
        _save_profile(name, email, github_url, selected_role_name, role_display_map, current, store)


def _render_skills_editor(current: StudentProfile) -> None:
    """Render the add/remove skills section."""
    # Initialise working list in session state
    if "draft_skills" not in st.session_state:
        st.session_state["draft_skills"] = [
            {"name": s.skill_name, "proficiency": s.proficiency}
            for s in current.skills
        ]

    # Sync when profile changes
    profile_skill_names = [s.skill_name for s in current.skills]
    draft_skill_names = [d["name"] for d in st.session_state["draft_skills"]]
    if profile_skill_names != draft_skill_names:
        st.session_state["draft_skills"] = [
            {"name": s.skill_name, "proficiency": s.proficiency}
            for s in current.skills
        ]

    # Display existing skills
    for i, skill_draft in enumerate(st.session_state["draft_skills"]):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            new_name = st.text_input(
                f"Skill {i + 1}", value=skill_draft["name"], key=f"skill_name_{i}"
            )
            st.session_state["draft_skills"][i]["name"] = new_name
        with col2:
            new_prof = st.selectbox(
                "Proficiency",
                cd.PROFICIENCY_LEVELS,
                index=cd.PROFICIENCY_LEVELS.index(skill_draft["proficiency"])
                if skill_draft["proficiency"] in cd.PROFICIENCY_LEVELS
                else 0,
                key=f"skill_prof_{i}",
            )
            st.session_state["draft_skills"][i]["proficiency"] = new_prof
        with col3:
            if st.button("❌", key=f"remove_skill_{i}", help="Remove skill"):
                st.session_state["draft_skills"].pop(i)
                st.rerun()

    # Add new skill
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        new_skill_name = st.text_input("New skill name", key="new_skill_name", placeholder="e.g. Python")
    with col2:
        new_skill_prof = st.selectbox("Proficiency", cd.PROFICIENCY_LEVELS, key="new_skill_prof")
    with col3:
        st.write("")
        st.write("")
        if st.button("➕ Add", key="add_skill"):
            if new_skill_name.strip():
                try:
                    existing = [
                        StudentSkill(d["name"], d["proficiency"])
                        for d in st.session_state["draft_skills"]
                    ]
                    validate_skill_name(new_skill_name.strip(), existing)
                    validate_proficiency(new_skill_prof)
                    st.session_state["draft_skills"].append(
                        {"name": new_skill_name.strip(), "proficiency": new_skill_prof}
                    )
                    st.rerun()
                except InvalidSkillError as exc:
                    st.error(str(exc))
            else:
                st.warning("Please enter a skill name.")


def _render_education_editor(current: StudentProfile) -> None:
    """Render the add/remove education section."""
    if "draft_education" not in st.session_state:
        st.session_state["draft_education"] = [
            {"institution": e.institution, "degree": e.degree, "year": e.year}
            for e in current.education
        ]

    for i, edu in enumerate(st.session_state["draft_education"]):
        with st.expander(f"Education {i + 1}: {edu.get('institution', '')}", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state["draft_education"][i]["institution"] = st.text_input(
                    "Institution", value=edu["institution"], key=f"edu_inst_{i}"
                )
            with col2:
                st.session_state["draft_education"][i]["degree"] = st.text_input(
                    "Degree", value=edu["degree"], key=f"edu_deg_{i}"
                )
            with col3:
                st.session_state["draft_education"][i]["year"] = st.text_input(
                    "Year", value=edu["year"], key=f"edu_year_{i}"
                )
            if st.button("❌ Remove", key=f"remove_edu_{i}"):
                st.session_state["draft_education"].pop(i)
                st.rerun()

    if st.button("➕ Add Education", key="add_edu"):
        st.session_state["draft_education"].append(
            {"institution": "", "degree": "", "year": ""}
        )
        st.rerun()


def _render_projects_editor(current: StudentProfile) -> None:
    """Render the add/remove projects section."""
    if "draft_projects" not in st.session_state:
        st.session_state["draft_projects"] = [
            {"title": p.title, "description": p.description}
            for p in current.projects
        ]

    for i, proj in enumerate(st.session_state["draft_projects"]):
        with st.expander(f"Project {i + 1}: {proj.get('title', '')}", expanded=True):
            st.session_state["draft_projects"][i]["title"] = st.text_input(
                "Project Title *", value=proj["title"], key=f"proj_title_{i}"
            )
            st.session_state["draft_projects"][i]["description"] = st.text_area(
                "Description (optional, max 500 chars)",
                value=proj["description"],
                max_chars=500,
                key=f"proj_desc_{i}",
            )
            if st.button("❌ Remove", key=f"remove_proj_{i}"):
                st.session_state["draft_projects"].pop(i)
                st.rerun()

    if st.button("➕ Add Project", key="add_proj"):
        st.session_state["draft_projects"].append({"title": "", "description": ""})
        st.rerun()


def _save_profile(
    name: str,
    email: str,
    github_url: str,
    selected_role_name: str,
    role_display_map: dict,
    current: StudentProfile,
    store: ProfileStore,
) -> None:
    """Validate inputs and save the profile to the store."""
    errors = []

    try:
        clean_name = validate_name(name)
    except InvalidStudentProfileError as exc:
        errors.append(str(exc))
        clean_name = name

    try:
        clean_email = validate_email(email)
    except InvalidStudentProfileError as exc:
        errors.append(str(exc))
        clean_email = ""

    try:
        clean_url = validate_github_url(github_url)
    except InvalidStudentProfileError as exc:
        errors.append(str(exc))
        clean_url = ""

    # Validate skills from draft
    skills = []
    for d in st.session_state.get("draft_skills", []):
        try:
            validate_skill_name(d["name"])
            validate_proficiency(d["proficiency"])
            skills.append(StudentSkill(skill_name=d["name"], proficiency=d["proficiency"]))
        except InvalidSkillError as exc:
            errors.append(str(exc))

    # Validate projects
    projects = []
    for d in st.session_state.get("draft_projects", []):
        if d["title"].strip():
            projects.append(Project(title=d["title"].strip(), description=d.get("description", "")))
        elif d["title"] == "" and d.get("description", ""):
            errors.append("A project has a description but no title.")

    education = [
        Education(
            institution=d["institution"],
            degree=d["degree"],
            year=d["year"],
        )
        for d in st.session_state.get("draft_education", [])
        if d["institution"].strip()
    ]

    if errors:
        for err in errors:
            st.error(err)
        return

    role_slug = role_display_map[selected_role_name]

    # Update existing profile or create a new one
    if current.profile_id and store.get_profile(current.profile_id):
        current.name = clean_name
        current.email = clean_email
        current.github_url = clean_url
        current.target_role = role_slug
        current.skills = skills
        current.education = education
        current.projects = projects
        profile = current
    else:
        profile = StudentProfile(
            name=clean_name,
            email=clean_email,
            github_url=clean_url,
            target_role=role_slug,
            skills=skills,
            education=education,
            projects=projects,
        )

    try:
        store.save_profile(profile)
        st.session_state["profile"] = profile
        # Clear stale analysis when profile is saved
        st.session_state["gap_result"] = None
        st.session_state["roadmap_steps"] = None
        st.session_state["missions"] = None
        st.success(f"✅ Profile saved for **{profile.name}**!")
    except DataStorageError as exc:
        st.error(str(exc))


# ===========================================================================
# PAGE: Analysis
# ===========================================================================

def page_analysis() -> None:
    st.header("📊 Skill Gap Analysis")

    if not _require_store() or not _require_profile():
        return

    profile: StudentProfile = st.session_state["profile"]
    role_data = cd.CAREER_ROLES.get(profile.target_role, {})
    role_name = role_data.get("role_name", profile.target_role)

    st.write(f"Analysing skills for **{profile.name}** → target role: **{role_name}**")

    if not profile.skills:
        st.warning("⚠️  You have no skills on your profile yet. Go to **🏠 Profile** and add some skills first.")
        return

    if st.button("🔍 Run Skill Gap Analysis", type="primary"):
        analyzer = SkillGapAnalyzer()
        try:
            result = analyzer.analyze(profile)
            st.session_state["gap_result"] = result
            st.success("Analysis complete!")
        except (InvalidStudentProfileError, InvalidCareerRoleError) as exc:
            st.error(str(exc))
            return

    gap = st.session_state["gap_result"]
    if gap is None:
        st.info("Click the button above to run the analysis.")
        return

    st.divider()

    # Results
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("✅ Strong Skills")
        if gap.strong_skills:
            for skill in gap.strong_skills:
                st.success(skill)
        else:
            st.info("None yet — keep building!")

    with col2:
        st.subheader("📈 Needs Improvement")
        if gap.needs_improvement:
            for skill in gap.needs_improvement:
                st.warning(skill)
        else:
            st.info("Nothing in this category.")

    with col3:
        st.subheader("❌ Missing Skills")
        if gap.missing_skills:
            for skill in gap.missing_skills:
                st.error(skill)
        else:
            st.balloons()
            st.success("You have all required skills! 🎉")

    st.divider()
    total_required = len(role_data.get("required_skills", []))
    st.metric(
        "Skills Score",
        f"{gap.skills_score * 100:.0f}%",
        help=f"Strong = 1 pt, Needs Improvement = 0.5 pt, Missing = 0 pt. Total required: {total_required}",
    )


# ===========================================================================
# PAGE: Roadmap
# ===========================================================================

def page_roadmap() -> None:
    st.header("🗺️ Personalised Learning Roadmap")

    if not _require_profile() or not _require_analysis():
        return

    gap = st.session_state["gap_result"]

    if not gap.missing_skills and not gap.needs_improvement:
        st.success("🎉 You have no skill gaps! Your roadmap is clear. Consider building more projects.")
        return

    generator = RoadmapGenerator()
    steps = generator.generate(gap)
    st.session_state["roadmap_steps"] = steps

    st.write("Here is your personalised week-by-week learning plan based on your skill gaps.")
    st.caption("Missing skills are prioritised first, then skills needing improvement.")
    st.divider()

    for step in steps:
        with st.expander(f"📅 Week {step.week} — {step.skill}", expanded=step.week <= 3):
            st.write(f"**Action:** {step.action}")
            st.info(f"📚 Resource: {step.resource_hint}")


# ===========================================================================
# PAGE: Missions
# ===========================================================================

def page_missions() -> None:
    st.header("🎯 Career Missions")

    if not _require_profile() or not _require_analysis():
        return

    profile: StudentProfile = st.session_state["profile"]
    store: ProfileStore = st.session_state["store"]

    # Generate or reload missions
    if st.session_state["missions"] is None:
        if st.session_state["roadmap_steps"] is None:
            generator = RoadmapGenerator()
            st.session_state["roadmap_steps"] = generator.generate(st.session_state["gap_result"])

        mission_gen = MissionGenerator()
        st.session_state["missions"] = mission_gen.generate(st.session_state["roadmap_steps"])

    missions: list[Mission] = st.session_state["missions"]

    if not missions:
        st.success("🎉 No missions needed — your skills are on target! Keep practising.")
        return

    st.write("Complete these tasks to close your skill gaps. Check off tasks as you finish them.")

    daily = [m for m in missions if m.cadence == "daily"]
    weekly = [m for m in missions if m.cadence == "weekly"]

    changed = False

    if daily:
        st.subheader("📅 Daily Missions")
        for i, mission in enumerate(daily):
            idx = missions.index(mission)
            new_val = st.checkbox(mission.task, value=mission.completed, key=f"mission_{idx}")
            if new_val != mission.completed:
                missions[idx].completed = new_val
                changed = True

    if weekly:
        st.subheader("🗓️ Weekly Missions")
        for i, mission in enumerate(weekly):
            idx = missions.index(mission)
            new_val = st.checkbox(mission.task, value=mission.completed, key=f"wmission_{idx}")
            if new_val != mission.completed:
                missions[idx].completed = new_val
                changed = True

    if changed:
        try:
            store.save_missions(profile.profile_id, missions)
        except DataStorageError as exc:
            st.error(str(exc))

    completed_count = sum(1 for m in missions if m.completed)
    st.divider()
    st.metric("Missions Completed", f"{completed_count} / {len(missions)}")


# ===========================================================================
# PAGE: Interview
# ===========================================================================

def page_interview() -> None:
    st.header("🎤 Mock Interview")
    st.caption(
        "⚠️  This is a practice tool only. Feedback is basic and keyword-based. "
        "It does not evaluate your real interview performance or predict hiring success."
    )

    if not _require_profile():
        return

    profile: StudentProfile = st.session_state["profile"]
    store: ProfileStore = st.session_state["store"]

    if not profile.target_role:
        st.warning("Please select a target career role on the Profile page first.")
        return

    engine = InterviewEngine()

    # ---- Past sessions ----------------------------------------------------
    try:
        past_sessions = store.get_sessions_for_profile(profile.profile_id)
    except DataStorageError:
        past_sessions = []

    completed_sessions = [s for s in past_sessions if s.completed]
    if completed_sessions:
        with st.expander(f"📜 Past Sessions ({len(completed_sessions)})", expanded=False):
            for sess in reversed(completed_sessions):
                st.write(
                    f"📅 {sess.started_at[:10]}  |  "
                    f"Score: **{sess.session_score * 100:.0f}%**  |  "
                    f"Questions answered: {len(sess.answers)}"
                )

    st.divider()

    # ---- Start or resume session ------------------------------------------
    session = st.session_state["interview_session"]
    questions = st.session_state["interview_questions"]

    if session is None or session.completed:
        if st.button("▶️ Start New Interview Session", type="primary"):
            new_session = engine.start_session(profile)
            try:
                questions = engine.get_questions(profile.target_role)
            except InvalidCareerRoleError as exc:
                st.error(str(exc))
                return
            st.session_state["interview_session"] = new_session
            st.session_state["interview_questions"] = questions
            st.session_state["current_q_index"] = 0
            st.rerun()
        return

    # ---- Active session ----------------------------------------------------
    q_index: int = st.session_state["current_q_index"]
    total_q = len(questions)

    st.progress(q_index / total_q, text=f"Question {q_index + 1} of {total_q}")

    if q_index >= total_q:
        # All questions answered — finish
        _finish_interview(engine, session, store)
        return

    current_q = questions[q_index]
    st.subheader(f"Q{q_index + 1}. {current_q['text']}")

    answer_text = st.text_area("Your answer:", height=150, key=f"answer_{q_index}", max_chars=1000)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit Answer", type="primary"):
            if not answer_text.strip():
                st.error("Please write an answer before submitting.")
            else:
                try:
                    answer_obj = engine.evaluate_answer(current_q, answer_text)
                    session.answers.append(answer_obj)
                    # Persist after each answer
                    try:
                        store.save_session(session)
                    except DataStorageError:
                        pass
                    st.session_state["current_q_index"] = q_index + 1
                    st.rerun()
                except InvalidInterviewAnswerError as exc:
                    st.error(str(exc))

    with col2:
        if st.button("⏭️ Skip Question"):
            st.session_state["current_q_index"] = q_index + 1
            st.rerun()

    # Show feedback for previous answer if available
    if session.answers and len(session.answers) == q_index:
        last = session.answers[-1]
        st.divider()
        st.subheader("Feedback on your last answer")
        st.info(last.feedback_message)
        st.metric("Answer Score", f"{last.score * 100:.0f}%")

    st.divider()
    if st.button("🏁 Finish Interview Early"):
        _finish_interview(engine, session, store)


def _finish_interview(engine: InterviewEngine, session, store: ProfileStore) -> None:
    """Complete the session, save it, and display summary."""
    finished = engine.finish_session(session)
    try:
        store.save_session(finished)
    except DataStorageError as exc:
        st.error(str(exc))

    st.session_state["interview_session"] = finished
    st.success(f"🎉 Interview complete! Your session score: **{finished.session_score * 100:.0f}%**")

    st.subheader("Answer Review")
    for i, ans in enumerate(finished.answers):
        with st.expander(f"Q{i + 1}. {ans.question_text}", expanded=False):
            st.write(f"**Your answer:** {ans.answer_text}")
            st.info(ans.feedback_message)
            st.metric("Score", f"{ans.score * 100:.0f}%")


# ===========================================================================
# PAGE: Dashboard
# ===========================================================================

def page_dashboard() -> None:
    st.header("📈 Career Dashboard")

    if not _require_profile():
        return

    profile: StudentProfile = st.session_state["profile"]
    store: ProfileStore = st.session_state["store"]

    role_data = cd.CAREER_ROLES.get(profile.target_role, {})
    role_name = role_data.get("role_name", "Not selected")

    # ---- Profile summary ---------------------------------------------------
    st.subheader("👤 Profile Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Name", profile.name)
    col2.metric("Target Role", role_name)
    col3.metric("Skills", len(profile.skills))
    col4.metric("Projects", len(profile.projects))

    st.divider()

    # ---- Career Readiness Progress ----------------------------------------
    st.subheader("🎯 Career Readiness Progress")
    st.caption(
        "This score is a transparent progress indicator based on five criteria. "
        "**It does not predict whether you will get a job.**"
    )

    # Need a gap result — run analysis if not available
    gap = st.session_state["gap_result"]
    if gap is None:
        if profile.skills and profile.target_role:
            analyzer = SkillGapAnalyzer()
            try:
                gap = analyzer.analyze(profile)
                st.session_state["gap_result"] = gap
            except (InvalidStudentProfileError, InvalidCareerRoleError):
                gap = None

    try:
        sessions = store.get_sessions_for_profile(profile.profile_id)
    except DataStorageError:
        sessions = []

    if gap is not None:
        analyzer = SkillGapAnalyzer()
        readiness = analyzer.calculate_readiness(profile, gap, sessions)

        st.metric(
            "Overall Career Progress",
            f"{readiness.total_score:.0f} / 100",
            help="Weighted average of the five components below.",
        )
        st.progress(readiness.total_score / 100)

        with st.expander("📊 Score Breakdown (click to expand)"):
            breakdown = {
                "Skill Coverage (40%)": readiness.skills_score,
                "Skill Proficiency (20%)": readiness.proficiency_score,
                "Projects (20%)": readiness.projects_score,
                "Profile Completeness (10%)": readiness.profile_score,
                "Interview Practice (10%)": readiness.interview_score,
            }
            for label, value in breakdown.items():
                col1, col2 = st.columns([3, 1])
                col1.write(label)
                col2.write(f"{value:.0f}%")
                st.progress(value / 100)
    else:
        st.info("Add skills and run the Skill Gap Analysis to see your readiness score.")

    st.divider()

    # ---- Strengths & Gaps -------------------------------------------------
    if gap is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("💪 Strengths")
            if gap.strong_skills:
                for s in gap.strong_skills:
                    st.success(s)
            else:
                st.info("Complete the analysis to see your strengths.")
        with col2:
            st.subheader("📉 Skill Gaps")
            for s in gap.missing_skills:
                st.error(s)
            for s in gap.needs_improvement:
                st.warning(s)
            if not gap.missing_skills and not gap.needs_improvement:
                st.success("No gaps! 🎉")

    st.divider()

    # ---- Roadmap preview ---------------------------------------------------
    st.subheader("🗺️ Top Roadmap Steps")
    steps = st.session_state.get("roadmap_steps")
    if steps is None and gap is not None:
        steps = RoadmapGenerator().generate(gap)
        st.session_state["roadmap_steps"] = steps

    if steps:
        for step in steps[:3]:
            st.write(f"**Week {step.week} — {step.skill}:** {step.action}")
    elif gap is not None:
        st.success("Your roadmap is clear — no gaps to address!")
    else:
        st.info("Run the analysis to generate your roadmap.")

    st.divider()

    # ---- Interview progress ------------------------------------------------
    st.subheader("🎤 Interview Progress")
    completed_sessions = [s for s in sessions if s.completed]
    if completed_sessions:
        avg_score = sum(s.session_score for s in completed_sessions) / len(completed_sessions)
        st.metric("Average Interview Score", f"{avg_score * 100:.0f}%")
        st.metric("Sessions Completed", len(completed_sessions))
    else:
        st.info("No mock interview sessions completed yet. Head to the **🎤 Interview** page.")


# ===========================================================================
# Router
# ===========================================================================

PAGE_MAP = {
    "🏠 Profile": page_profile,
    "📊 Analysis": page_analysis,
    "🗺️ Roadmap": page_roadmap,
    "🎯 Missions": page_missions,
    "🎤 Interview": page_interview,
    "📈 Dashboard": page_dashboard,
}

current_page = st.session_state.get("page", "🏠 Profile")
PAGE_MAP.get(current_page, page_profile)()
