"""
Automated tests for PawPal+ core logic.
Run:  python -m pytest
"""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(description="Walk", time="08:00", priority="high",
              frequency="once", pet_name="Buddy",
              completed=False, due_date=None):
    return Task(
        description=description,
        time=time,
        duration_minutes=20,
        priority=priority,
        frequency=frequency,
        pet_name=pet_name,
        completed=completed,
        due_date=due_date or date.today(),
    )


def make_owner_with_pet():
    owner = Owner("Alex")
    pet = Pet("Buddy", "dog", 2)
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_sets_flag():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_once_task_has_no_next_occurrence():
    task = make_task(frequency="once")
    assert task.next_occurrence() is None


def test_daily_task_next_occurrence_is_tomorrow():
    today = date.today()
    task = make_task(frequency="daily", due_date=today)
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False


def test_weekly_task_next_occurrence_is_seven_days():
    today = date.today()
    task = make_task(frequency="weekly", due_date=today)
    next_task = task.next_occurrence()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    pet = Pet("Luna", "cat", 4)
    assert len(pet.get_tasks()) == 0
    pet.add_task(make_task(pet_name="Luna"))
    assert len(pet.get_tasks()) == 1


def test_remove_task_decreases_count():
    pet = Pet("Luna", "cat", 4)
    task = make_task(pet_name="Luna")
    pet.add_task(task)
    pet.remove_task(task)
    assert len(pet.get_tasks()) == 0


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_owner_collects_all_tasks():
    owner, pet = make_owner_with_pet()
    pet2 = Pet("Whiskers", "cat", 6)
    owner.add_pet(pet2)

    pet.add_task(make_task(pet_name="Buddy"))
    pet2.add_task(make_task(pet_name="Whiskers"))
    pet2.add_task(make_task(pet_name="Whiskers", description="Feeding"))

    assert len(owner.get_all_tasks()) == 3


def test_owner_with_no_pets_returns_empty():
    owner = Owner("Sam")
    assert owner.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(description="Walk", time="14:00"))
    pet.add_task(make_task(description="Feeding", time="07:00"))
    pet.add_task(make_task(description="Meds", time="09:30"))

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(owner.get_all_tasks())
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_todays_schedule_excludes_future_tasks():
    owner, pet = make_owner_with_pet()
    today = date.today()
    tomorrow = today + timedelta(days=1)

    pet.add_task(make_task(description="Today task", due_date=today))
    pet.add_task(make_task(description="Tomorrow task", due_date=tomorrow))

    scheduler = Scheduler(owner)
    schedule = scheduler.get_todays_schedule()
    assert len(schedule) == 1
    assert schedule[0].description == "Today task"


def test_filter_by_pet_name():
    owner = Owner("Jordan")
    dog = Pet("Rex", "dog", 1)
    cat = Pet("Miso", "cat", 2)
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(make_task(pet_name="Rex"))
    cat.add_task(make_task(pet_name="Miso"))

    scheduler = Scheduler(owner)
    rex_tasks = scheduler.filter_tasks(pet_name="Rex")
    assert len(rex_tasks) == 1
    assert rex_tasks[0].pet_name == "Rex"


def test_filter_by_completed_status():
    owner, pet = make_owner_with_pet()
    pet.add_task(make_task(description="Done task", completed=True))
    pet.add_task(make_task(description="Pending task", completed=False))

    scheduler = Scheduler(owner)
    done = scheduler.filter_tasks(completed=True)
    pending = scheduler.filter_tasks(completed=False)
    assert len(done) == 1
    assert len(pending) == 1


def test_detect_conflicts_same_pet_same_time():
    owner, pet = make_owner_with_pet()
    today = date.today()
    pet.add_task(make_task(description="Walk", time="08:00", due_date=today))
    pet.add_task(make_task(description="Feeding", time="08:00", due_date=today))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_different_pets_no_warning():
    owner = Owner("Pat")
    dog = Pet("Max", "dog", 3)
    cat = Pet("Cleo", "cat", 2)
    owner.add_pet(dog)
    owner.add_pet(cat)

    today = date.today()
    dog.add_task(make_task(pet_name="Max", time="08:00", due_date=today))
    cat.add_task(make_task(pet_name="Cleo", time="08:00", due_date=today))

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()
    assert warnings == []


def test_mark_task_complete_creates_recurrence():
    owner, pet = make_owner_with_pet()
    today = date.today()
    task = make_task(description="Walk", frequency="daily", due_date=today)
    pet.add_task(task)

    scheduler = Scheduler(owner)
    initial_count = len(pet.get_tasks())
    scheduler.mark_task_complete(task, pet)

    assert task.completed is True
    assert len(pet.get_tasks()) == initial_count + 1

    new_task = pet.get_tasks()[-1]
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.completed is False


# ---------------------------------------------------------------------------
# find_next_available_slot tests
# ---------------------------------------------------------------------------

def test_slot_finder_gap_between_tasks():
    """30-min slot should fit in the 30-min gap between two tasks."""
    owner, pet = make_owner_with_pet()
    today = date.today()
    pet.add_task(make_task(description="Walk",    time="07:00", due_date=today))
    # duration defaults to 20 min, so walk ends at 07:20
    pet.add_task(make_task(description="Feeding", time="08:00", due_date=today))

    scheduler = Scheduler(owner)
    slot = scheduler.find_next_available_slot("Buddy", 30, start_after="07:00")
    # gap after 07:20 and before 08:00 is 40 min — fits a 30-min task
    assert slot == "07:20"


def test_slot_finder_advances_past_overlapping_interval():
    """Requested duration that doesn't fit before next task skips to after it."""
    owner, pet = make_owner_with_pet()
    today = date.today()
    pet.add_task(make_task(description="Walk",    time="07:00", due_date=today))  # ends 07:20
    pet.add_task(make_task(description="Feeding", time="07:30", due_date=today))  # ends 07:50

    scheduler = Scheduler(owner)
    # 60-min task won't fit between walk (end 07:20) and feeding (start 07:30)
    slot = scheduler.find_next_available_slot("Buddy", 60, start_after="07:00")
    assert slot == "07:50"


def test_slot_finder_no_tasks_returns_start_after():
    """Pet with no tasks should return start_after as the first available slot."""
    owner, pet = make_owner_with_pet()
    scheduler = Scheduler(owner)
    slot = scheduler.find_next_available_slot("Buddy", 30, start_after="09:00")
    assert slot == "09:00"


def test_slot_finder_returns_none_when_day_is_full():
    """Should return None when no slot fits before midnight."""
    owner, pet = make_owner_with_pet()
    today = date.today()
    # One task that runs from 00:00 for 1440 minutes (fills the whole day)
    pet.add_task(Task(
        description="All day block",
        time="00:00",
        duration_minutes=1440,
        priority="low",
        frequency="once",
        pet_name="Buddy",
        due_date=today,
    ))
    scheduler = Scheduler(owner)
    slot = scheduler.find_next_available_slot("Buddy", 10, start_after="00:00")
    assert slot is None


# ---------------------------------------------------------------------------
# get_urgency_ranked_tasks tests
# ---------------------------------------------------------------------------

def test_urgency_ranking_high_priority_scores_above_low():
    owner, pet = make_owner_with_pet()
    today = date.today()
    pet.add_task(make_task(description="Low task",  priority="low",  due_date=today))
    pet.add_task(make_task(description="High task", priority="high", due_date=today))

    scheduler = Scheduler(owner)
    ranked = scheduler.get_urgency_ranked_tasks()
    assert ranked[0][0].description == "High task"


def test_urgency_ranking_overdue_task_outranks_fresh_high_priority():
    """A low-priority task overdue by 5 days should beat a fresh high-priority task."""
    owner, pet = make_owner_with_pet()
    today = date.today()
    five_days_ago = today - timedelta(days=5)

    pet.add_task(make_task(description="Fresh high", priority="high", due_date=today))
    pet.add_task(make_task(description="Overdue low", priority="low", due_date=five_days_ago))

    scheduler = Scheduler(owner)
    ranked = scheduler.get_urgency_ranked_tasks()
    # overdue low: 1 + min(5*2,10) + 0 = 11; fresh high: 3 + 0 + 0 = 3
    assert ranked[0][0].description == "Overdue low"


def test_urgency_ranking_excludes_completed_tasks():
    owner, pet = make_owner_with_pet()
    today = date.today()
    pet.add_task(make_task(description="Done task",    completed=True,  due_date=today))
    pet.add_task(make_task(description="Pending task", completed=False, due_date=today))

    scheduler = Scheduler(owner)
    ranked = scheduler.get_urgency_ranked_tasks()
    descriptions = [t.description for t, _ in ranked]
    assert "Done task" not in descriptions
    assert "Pending task" in descriptions
