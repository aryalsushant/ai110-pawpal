"""
PawPal+ CLI demo.

Run:  python main.py
"""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(tasks, title="Today's Schedule"):
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print(f"{'=' * 50}")
    if not tasks:
        print("  No tasks scheduled.")
    for task in tasks:
        check = "[x]" if task.completed else "[ ]"
        print(f"  {check} {task}")
    print(f"{'=' * 50}\n")


def main():
    # --- Setup ---
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "dog", 3)
    luna = Pet("Luna", "cat", 5)

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    # Tasks for Mochi (dog)
    mochi.add_task(Task(
        description="Morning walk",
        time="07:30",
        duration_minutes=30,
        priority="high",
        frequency="daily",
        pet_name="Mochi",
        due_date=today,
    ))
    mochi.add_task(Task(
        description="Breakfast feeding",
        time="08:00",
        duration_minutes=10,
        priority="high",
        frequency="daily",
        pet_name="Mochi",
        due_date=today,
    ))
    mochi.add_task(Task(
        description="Heartworm medication",
        time="08:00",
        duration_minutes=5,
        priority="high",
        frequency="once",
        pet_name="Mochi",
        due_date=today,
    ))
    mochi.add_task(Task(
        description="Evening walk",
        time="18:00",
        duration_minutes=45,
        priority="medium",
        frequency="daily",
        pet_name="Mochi",
        due_date=today,
    ))

    # Tasks for Luna (cat)
    luna.add_task(Task(
        description="Breakfast feeding",
        time="07:00",
        duration_minutes=5,
        priority="high",
        frequency="daily",
        pet_name="Luna",
        due_date=today,
    ))
    luna.add_task(Task(
        description="Grooming session",
        time="14:00",
        duration_minutes=15,
        priority="low",
        frequency="weekly",
        pet_name="Luna",
        due_date=today,
    ))

    # Task for tomorrow (should not show in today's schedule)
    mochi.add_task(Task(
        description="Vet appointment",
        time="10:00",
        duration_minutes=60,
        priority="high",
        frequency="once",
        pet_name="Mochi",
        due_date=today + timedelta(days=1),
    ))

    scheduler = Scheduler(owner)

    # --- Today's schedule ---
    print_schedule(scheduler.get_todays_schedule())

    # --- Conflict detection ---
    print("Conflict check:")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  WARNING: {warning}")
    else:
        print("  No conflicts found.")
    print()

    # --- Filter: Mochi's pending tasks ---
    pending_mochi = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    print_schedule(pending_mochi, title="Mochi's Pending Tasks")

    # --- Mark a daily task complete and verify recurrence ---
    morning_walk = mochi.get_tasks()[0]
    print(f"Marking complete: {morning_walk.description}")
    scheduler.mark_task_complete(morning_walk, mochi)
    print(f"  Status: {'done' if morning_walk.completed else 'pending'}")

    mochi_tasks = mochi.get_tasks()
    tomorrow_walk = [t for t in mochi_tasks if t.description == "Morning walk" and not t.completed]
    if tomorrow_walk:
        print(f"  Next occurrence created for: {tomorrow_walk[0].due_date}")
    print()

    # --- All tasks sorted ---
    all_sorted = scheduler.sort_by_time(owner.get_all_tasks())
    print_schedule(all_sorted, title="All Tasks (Sorted)")


if __name__ == "__main__":
    main()
