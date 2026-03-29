"""
PawPal+ Streamlit UI.

Run:  streamlit run app.py
"""

import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling for busy owners.")

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
            st.success(f"Added {pet_name.strip()} the {species}.")

pets = owner.get_pets()
if pets:
    st.write("Your pets:", ", ".join(str(p) for p in pets))

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
            # Validate time format
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
                st.success(f"Task '{description.strip()}' added for {selected_pet}.")

# ---------------------------------------------------------------------------
# Today's schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Today's Schedule")

schedule = scheduler.get_todays_schedule()
conflicts = scheduler.detect_conflicts()

if conflicts:
    for warning in conflicts:
        st.warning(warning)

if not schedule:
    st.info("No tasks scheduled for today. Add some tasks above.")
else:
    rows = []
    for task in schedule:
        rows.append({
            "Time": task.time,
            "Pet": task.pet_name,
            "Task": task.description,
            "Duration": f"{task.duration_minutes} min",
            "Priority": task.priority,
            "Frequency": task.frequency,
            "Status": "Done" if task.completed else "Pending",
        })
    st.table(rows)

# ---------------------------------------------------------------------------
# Mark tasks complete
# ---------------------------------------------------------------------------

st.subheader("Mark Task Complete")

all_pending = [t for t in scheduler.get_todays_schedule() if not t.completed]
if not all_pending:
    st.info("No pending tasks for today.")
else:
    task_labels = [f"{t.time} - {t.pet_name}: {t.description}" for t in all_pending]
    chosen_label = st.selectbox("Select a task to complete", task_labels)
    chosen_index = task_labels.index(chosen_label)
    chosen_task = all_pending[chosen_index]

    if st.button("Mark as complete"):
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
            "Date": str(t.due_date),
            "Time": t.time,
            "Pet": t.pet_name,
            "Task": t.description,
            "Priority": t.priority,
            "Status": "Done" if t.completed else "Pending",
        }
        for t in filtered_sorted
    ]
    st.table(filter_rows)
