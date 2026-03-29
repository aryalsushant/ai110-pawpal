"""
PawPal+ Streamlit UI.

Run:  streamlit run app.py
"""

import pandas as pd
import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task
from ui_helpers import task_emoji, species_emoji

st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal CSS tweaks only
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
        [data-testid="stMetricValue"] { font-size: 2rem !important; }
        [data-testid="stMetricDelta"] { font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

PRIORITY_LABELS = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Sidebar: owner setup + pet management
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🐾 PawPal+")
    st.caption("Smart pet care for busy owners.")
    st.divider()

    st.subheader("Owner")
    with st.form("owner_form"):
        owner_name = st.text_input(
            "Name", placeholder="Your name", label_visibility="collapsed"
        )
        if st.form_submit_button("Set owner", use_container_width=True):
            if owner_name.strip():
                if st.session_state.owner is None:
                    st.session_state.owner = Owner(owner_name.strip())
                    st.session_state.scheduler = Scheduler(st.session_state.owner)
                st.success(f"Welcome, {st.session_state.owner.name}!")

    if st.session_state.owner is None:
        st.info("Enter your name above to begin.")
        st.stop()

    owner: Owner = st.session_state.owner
    scheduler: Scheduler = st.session_state.scheduler

    st.divider()
    st.subheader("Add a Pet")
    with st.form("pet_form"):
        p_name = st.text_input("Pet name", placeholder="e.g. Mochi")
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            p_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        with p_col2:
            p_age = st.number_input("Age", min_value=0, max_value=30, value=2)
        if st.form_submit_button("Add pet", use_container_width=True):
            if p_name.strip():
                existing = [p.name for p in owner.get_pets()]
                if p_name.strip() in existing:
                    st.warning(f"{p_name.strip()} is already added.")
                else:
                    owner.add_pet(Pet(p_name.strip(), p_species, int(p_age)))
                    st.toast(
                        f"{species_emoji(p_species)} {p_name.strip()} added!", icon="✅"
                    )

    # Pet roster
    pets = owner.get_pets()
    if pets:
        st.divider()
        st.subheader("Your Pets")
        for p in pets:
            total = len(p.get_tasks())
            done = sum(1 for t in p.get_tasks() if t.completed)
            with st.container(border=True):
                st.markdown(
                    f"{species_emoji(p.species)} &nbsp; **{p.name}**  \n"
                    f"`{p.species}` &nbsp;·&nbsp; age {p.age}  \n"
                    f"<small>{done}/{total} tasks done today</small>",
                    unsafe_allow_html=True,
                )

# Keep a fresh reference after sidebar renders
pets = owner.get_pets()

# ---------------------------------------------------------------------------
# Header + KPI metrics
# ---------------------------------------------------------------------------

st.title(f"🐾 {owner.name}'s Pet Dashboard")

schedule_today = scheduler.get_todays_schedule()
conflicts = scheduler.detect_conflicts()
n_pending = sum(1 for t in schedule_today if not t.completed)
n_done = sum(1 for t in schedule_today if t.completed)

m1, m2, m3, m4 = st.columns(4, gap="small")
m1.metric("Pets", len(pets))
m2.metric("Tasks Today", len(schedule_today))
m3.metric(
    "Pending",
    n_pending,
    delta=f"⚠️ {len(conflicts)} conflict(s)" if conflicts else "No conflicts",
    delta_color="off",
)
m4.metric(
    "Completed",
    n_done,
    delta=f"+{n_done}" if n_done else None,
    delta_color="normal",
)

for warning in conflicts:
    st.warning(f"⚠️ {warning}")

st.divider()

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------

tab_today, tab_add, tab_filter, tab_urgency, tab_slot = st.tabs([
    "📅  Today's Schedule",
    "➕  Add Task",
    "🔍  Filter Tasks",
    "🔥  Urgency Ranking",
    "🕐  Find Available Slot",
])

# ---- Tab 1: Today's Schedule ------------------------------------------------

with tab_today:
    if not schedule_today:
        st.info("No tasks scheduled for today. Use the **Add Task** tab to get started.")
    else:
        df_today = pd.DataFrame([
            {
                "":         task_emoji(t.description),
                "Time":     t.time,
                "Pet":      t.pet_name,
                "Task":     t.description,
                "Duration": t.duration_minutes,
                "Priority": PRIORITY_LABELS.get(t.priority, t.priority),
                "Freq":     t.frequency.capitalize(),
                "Status":   "✅ Done" if t.completed else "⏳ Pending",
            }
            for t in schedule_today
        ])
        st.dataframe(
            df_today,
            column_config={
                "":         st.column_config.TextColumn("", width=40),
                "Time":     st.column_config.TextColumn("Time", width=80),
                "Duration": st.column_config.NumberColumn("Duration", format="%d min", width=110),
                "Status":   st.column_config.TextColumn("Status", width=120),
            },
            hide_index=True,
            use_container_width=True,
        )

    st.divider()
    st.subheader("Mark Task Complete")

    pending_tasks = [t for t in schedule_today if not t.completed]
    if not pending_tasks:
        st.success("All done for today! 🎉")
    else:
        task_labels = [
            f"{task_emoji(t.description)}  {t.time}  —  {t.pet_name}: {t.description}"
            for t in pending_tasks
        ]
        chosen_label = st.selectbox(
            "Select a task", task_labels, label_visibility="collapsed"
        )
        chosen_task = pending_tasks[task_labels.index(chosen_label)]

        if st.button("✅ Mark as complete", type="primary"):
            target_pet = next(p for p in pets if p.name == chosen_task.pet_name)
            scheduler.mark_task_complete(chosen_task, target_pet)
            suffix = (
                f" Next {chosen_task.frequency} occurrence scheduled."
                if chosen_task.frequency != "once"
                else ""
            )
            st.toast(f"'{chosen_task.description}' marked complete!{suffix}", icon="✅")
            st.rerun()

# ---- Tab 2: Add Task --------------------------------------------------------

with tab_add:
    if not pets:
        st.info("Add a pet in the sidebar before scheduling tasks.")
    else:
        with st.form("task_form", border=True):
            st.subheader("New Task")
            col1, col2 = st.columns(2, gap="large")
            with col1:
                selected_pet = st.selectbox("For which pet?", [p.name for p in pets])
                description = st.text_input(
                    "Task description", placeholder="e.g. Morning walk"
                )
                task_time = st.text_input("Time (HH:MM, 24-hour)", value="08:00")
                due_date = st.date_input("Due date", value=date.today())
            with col2:
                duration = st.number_input(
                    "Duration (minutes)", min_value=1, max_value=240, value=20
                )
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
                st.markdown("")  # spacer

            submitted = st.form_submit_button(
                "Add task", type="primary", use_container_width=True
            )
            if submitted:
                parts = task_time.strip().split(":")
                valid_time = len(parts) == 2 and all(p.isdigit() for p in parts)
                if not description.strip():
                    st.error("Enter a task description.")
                elif not valid_time:
                    st.error("Time must be in HH:MM format (e.g. 08:30).")
                else:
                    target_pet = next(p for p in pets if p.name == selected_pet)
                    target_pet.add_task(
                        Task(
                            description=description.strip(),
                            time=task_time.strip(),
                            duration_minutes=int(duration),
                            priority=priority,
                            frequency=frequency,
                            pet_name=selected_pet,
                            due_date=due_date,
                        )
                    )
                    st.toast(
                        f"{task_emoji(description)} Task added for {selected_pet}!",
                        icon="➕",
                    )
                    st.rerun()

# ---- Tab 3: Filter Tasks ----------------------------------------------------

with tab_filter:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        filter_pet = st.selectbox(
            "Filter by pet", ["All"] + [p.name for p in pets]
        )
    with col2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Done"])

    pet_filter = None if filter_pet == "All" else filter_pet
    status_filter = (
        None
        if filter_status == "All"
        else (False if filter_status == "Pending" else True)
    )

    filtered = scheduler.sort_by_time(
        scheduler.filter_tasks(pet_name=pet_filter, completed=status_filter)
    )

    if not filtered:
        st.info("No tasks match the selected filters.")
    else:
        df_filter = pd.DataFrame([
            {
                "":         task_emoji(t.description),
                "Date":     t.due_date,
                "Time":     t.time,
                "Pet":      t.pet_name,
                "Task":     t.description,
                "Priority": PRIORITY_LABELS.get(t.priority, t.priority),
                "Freq":     t.frequency.capitalize(),
                "Status":   "✅ Done" if t.completed else "⏳ Pending",
            }
            for t in filtered
        ])
        st.dataframe(
            df_filter,
            column_config={
                "":     st.column_config.TextColumn("", width=40),
                "Date": st.column_config.DateColumn("Date", format="MMM DD, YYYY"),
                "Time": st.column_config.TextColumn("Time", width=80),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption(f"{len(filtered)} task(s) shown.")

# ---- Tab 4: Urgency Ranking -------------------------------------------------

with tab_urgency:
    st.caption(
        "Score = priority weight (high 3 / medium 2 / low 1) "
        "+ overdue penalty (days × 2, capped at 10) "
        "+ frequency urgency (daily 1 / weekly 0.5 / once 0). "
        "Max possible score: 14."
    )
    ranked = scheduler.get_urgency_ranked_tasks()
    if not ranked:
        st.info("No pending tasks to rank.")
    else:
        df_rank = pd.DataFrame([
            {
                "":         task_emoji(task.description),
                "Score":    score,
                "Pet":      task.pet_name,
                "Task":     task.description,
                "Priority": PRIORITY_LABELS.get(task.priority, task.priority),
                "Due":      task.due_date,
                "Freq":     task.frequency.capitalize(),
            }
            for task, score in ranked
        ])
        st.dataframe(
            df_rank,
            column_config={
                "":      st.column_config.TextColumn("", width=40),
                "Score": st.column_config.ProgressColumn(
                    "Urgency Score",
                    min_value=0,
                    max_value=14,
                    format="%.1f",
                ),
                "Due":   st.column_config.DateColumn("Due Date", format="MMM DD, YYYY"),
            },
            hide_index=True,
            use_container_width=True,
        )

# ---- Tab 5: Find Available Slot ---------------------------------------------

with tab_slot:
    st.caption(
        "Scans today's schedule for a given pet and returns the earliest "
        "free gap that fits your requested duration."
    )
    if not pets:
        st.info("Add a pet in the sidebar first.")
    else:
        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            slot_pet = st.selectbox("Pet", [p.name for p in pets])
        with col2:
            slot_dur = st.number_input(
                "Duration needed (min)", min_value=1, max_value=240, value=30
            )
        with col3:
            slot_start = st.text_input("Search from (HH:MM)", value="00:00")

        if st.button("Find slot", type="primary"):
            parts = slot_start.strip().split(":")
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                st.error("Enter time in HH:MM format (e.g. 09:00).")
            else:
                result = scheduler.find_next_available_slot(
                    slot_pet, int(slot_dur), slot_start.strip()
                )
                if result:
                    st.success(
                        f"🟢 Next available **{int(slot_dur)}-minute** slot "
                        f"for **{slot_pet}**: **{result}**"
                    )
                    # Show how the day looks for context
                    today_pet = [
                        t for t in schedule_today if t.pet_name == slot_pet
                    ]
                    if today_pet:
                        st.caption("Existing tasks for this pet today:")
                        df_ctx = pd.DataFrame([
                            {
                                "Time":     t.time,
                                "Task":     t.description,
                                "Duration": t.duration_minutes,
                                "Status":   "✅ Done" if t.completed else "⏳ Pending",
                            }
                            for t in today_pet
                        ])
                        st.dataframe(
                            df_ctx,
                            column_config={
                                "Duration": st.column_config.NumberColumn(
                                    "Duration", format="%d min"
                                ),
                            },
                            hide_index=True,
                            use_container_width=True,
                        )
                else:
                    st.warning(
                        f"No {int(slot_dur)}-minute gap found for {slot_pet} "
                        f"after {slot_start.strip()} today."
                    )
