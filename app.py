"""
PawPal+ Streamlit UI.

Run:  streamlit run app.py
"""

import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task
from ui_helpers import task_emoji, species_emoji, priority_badge_html, status_badge_html

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def html_table(rows: list[dict], badge_cols: dict[str, str] = {}) -> str:
    """Render a list of dicts as an HTML table. badge_cols maps col name to 'priority'/'status'."""
    if not rows:
        return ""
    headers = list(rows[0].keys())
    th = "".join(
        f'<th style="padding:6px 12px;text-align:left;border-bottom:2px solid #e0e0e0;'
        f'font-size:0.85em;color:#555;">{h}</th>'
        for h in headers
    )
    body = ""
    for i, row in enumerate(rows):
        bg = "#fafafa" if i % 2 == 0 else "#fff"
        tds = ""
        for h in headers:
            val = row[h]
            if h == "Priority":
                val = priority_badge_html(str(val).lower())
            elif h == "Status":
                val = status_badge_html(val == "Done")
            tds += (
                f'<td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">{val}</td>'
            )
        body += f'<tr style="background:{bg};">{tds}</tr>'
    return (
        f'<table style="width:100%;border-collapse:collapse;font-size:0.9em;">'
        f"<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"
    )


# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Owner setup
# ---------------------------------------------------------------------------

st.header("Owner & Pet Setup")

with st.form("owner_form"):
    owner_name = st.text_input("Your name", value="Jordan")
    submitted_owner = st.form_submit_button("Set owner")
    if submitted_owner and owner_name.strip():
        if st.session_state.owner is None:
            st.session_state.owner = Owner(owner_name.strip())
            st.session_state.scheduler = Scheduler(st.session_state.owner)
        st.success(f"Owner set: {st.session_state.owner.name}")

if st.session_state.owner is None:
    st.info("Set your name above to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Add a pet
# ---------------------------------------------------------------------------

st.subheader("Add a Pet")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

    add_pet = st.form_submit_button("Add pet")
    if add_pet and pet_name.strip():
        existing = [p.name for p in owner.get_pets()]
        if pet_name.strip() in existing:
            st.warning(f"{pet_name.strip()} is already added.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {species_emoji(species)} {pet_name.strip()} the {species}.")

pets = owner.get_pets()
if pets:
    pet_labels = "  ".join(
        f"{species_emoji(p.species)} **{p.name}** ({p.species}, age {p.age})"
        for p in pets
    )
    st.markdown(pet_labels)

# ---------------------------------------------------------------------------
# Add a task
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Schedule a Task")

if not pets:
    st.info("Add a pet first before scheduling tasks.")
else:
    with st.form("task_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_pet = st.selectbox("For which pet?", [p.name for p in pets])
            description = st.text_input("Task description", value="Morning walk")
            task_time = st.text_input("Time (HH:MM, 24-hour)", value="08:00")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
            due_date = st.date_input("Due date", value=date.today())

        add_task = st.form_submit_button("Add task")
        if add_task and description.strip() and task_time.strip():
            parts = task_time.strip().split(":")
            valid_time = len(parts) == 2 and all(p.isdigit() for p in parts)
            if not valid_time:
                st.error("Time must be in HH:MM format (e.g. 08:30).")
            else:
                target_pet = next(p for p in pets if p.name == selected_pet)
                new_task = Task(
                    description=description.strip(),
                    time=task_time.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                    pet_name=selected_pet,
                    due_date=due_date,
                )
                target_pet.add_task(new_task)
                emoji = task_emoji(description.strip())
                st.success(f"{emoji} '{description.strip()}' added for {selected_pet}.")

# ---------------------------------------------------------------------------
# Today's schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Today's Schedule")

schedule = scheduler.get_todays_schedule()
conflicts = scheduler.detect_conflicts()

for warning in conflicts:
    st.warning(f"⚠️ {warning}")

if not schedule:
    st.info("No tasks scheduled for today. Add some tasks above.")
else:
    rows = [
        {
            "":         task_emoji(t.description),
            "Time":     t.time,
            "Pet":      t.pet_name,
            "Task":     t.description,
            "Duration": f"{t.duration_minutes} min",
            "Priority": t.priority,
            "Freq":     t.frequency,
            "Status":   "Done" if t.completed else "Pending",
        }
        for t in schedule
    ]
    st.markdown(html_table(rows), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Mark tasks complete
# ---------------------------------------------------------------------------

st.subheader("Mark Task Complete")

all_pending = [t for t in scheduler.get_todays_schedule() if not t.completed]
if not all_pending:
    st.info("No pending tasks for today.")
else:
    task_labels = [
        f"{task_emoji(t.description)} {t.time} - {t.pet_name}: {t.description}"
        for t in all_pending
    ]
    chosen_label = st.selectbox("Select a task to complete", task_labels)
    chosen_index = task_labels.index(chosen_label)
    chosen_task = all_pending[chosen_index]

    if st.button("✅ Mark as complete"):
        target_pet = next(p for p in pets if p.name == chosen_task.pet_name)
        scheduler.mark_task_complete(chosen_task, target_pet)
        if chosen_task.frequency != "once":
            st.success(
                f"Done! '{chosen_task.description}' marked complete. "
                f"Next {chosen_task.frequency} occurrence scheduled."
            )
        else:
            st.success(f"Done! '{chosen_task.description}' marked complete.")
        st.rerun()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Filter Tasks")

col1, col2 = st.columns(2)
with col1:
    filter_pet = st.selectbox(
        "Filter by pet", ["All"] + [p.name for p in pets], key="filter_pet"
    )
with col2:
    filter_status = st.selectbox(
        "Filter by status", ["All", "Pending", "Done"], key="filter_status"
    )

pet_filter = None if filter_pet == "All" else filter_pet
status_filter = None
if filter_status == "Pending":
    status_filter = False
elif filter_status == "Done":
    status_filter = True

filtered = scheduler.filter_tasks(pet_name=pet_filter, completed=status_filter)
filtered_sorted = scheduler.sort_by_time(filtered)

if not filtered_sorted:
    st.info("No tasks match the filter.")
else:
    filter_rows = [
        {
            "":         task_emoji(t.description),
            "Date":     str(t.due_date),
            "Time":     t.time,
            "Pet":      t.pet_name,
            "Task":     t.description,
            "Priority": t.priority,
            "Status":   "Done" if t.completed else "Pending",
        }
        for t in filtered_sorted
    ]
    st.markdown(html_table(filter_rows), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Urgency ranking
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🔥 Urgency Ranking")
st.caption(
    "Score = priority weight + overdue penalty + frequency urgency. "
    "Higher score = needs attention sooner."
)

ranked = scheduler.get_urgency_ranked_tasks()
if not ranked:
    st.info("No pending tasks to rank.")
else:
    rank_rows = [
        {
            "Score":    f"{score:.1f}",
            "":         task_emoji(task.description),
            "Pet":      task.pet_name,
            "Task":     task.description,
            "Priority": task.priority,
            "Due":      str(task.due_date),
            "Freq":     task.frequency,
        }
        for task, score in ranked
    ]
    st.markdown(html_table(rank_rows), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Next available slot finder
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🕐 Find Next Available Slot")
st.caption("Finds the earliest gap in a pet's today schedule that fits your task.")

if not pets:
    st.info("Add a pet first.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        slot_pet = st.selectbox("Pet", [p.name for p in pets], key="slot_pet")
    with col2:
        slot_duration = st.number_input(
            "Task duration (min)", min_value=1, max_value=240, value=30, key="slot_dur"
        )
    with col3:
        slot_start = st.text_input("Search from (HH:MM)", value="00:00", key="slot_start")

    if st.button("Find slot"):
        parts = slot_start.strip().split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            st.error("Enter time in HH:MM format.")
        else:
            result = scheduler.find_next_available_slot(
                slot_pet, int(slot_duration), slot_start.strip()
            )
            if result:
                st.success(
                    f"🟢 Next available {int(slot_duration)}-minute slot for "
                    f"{slot_pet}: **{result}**"
                )
            else:
                st.warning(
                    f"No {int(slot_duration)}-minute gap found for {slot_pet} "
                    f"after {slot_start.strip()} today."
                )
