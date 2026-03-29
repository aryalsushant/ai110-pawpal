"""
PawPal+ CLI demo.

Run:  python main.py
"""

from datetime import date, timedelta

from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate

from pawpal_system import Owner, Pet, Scheduler, Task
from ui_helpers import task_emoji, species_emoji

colorama_init(autoreset=True)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

PRIORITY_COLOR = {
    "high":   Fore.RED + Style.BRIGHT,
    "medium": Fore.YELLOW + Style.BRIGHT,
    "low":    Fore.GREEN,
}


def fmt_priority(priority: str) -> str:
    return PRIORITY_COLOR.get(priority, "") + priority + Style.RESET_ALL


def fmt_status(completed: bool) -> str:
    if completed:
        return Fore.GREEN + Style.BRIGHT + "✅ done" + Style.RESET_ALL
    return Fore.CYAN + "⏳ pending" + Style.RESET_ALL


def print_schedule(tasks, title="Today's Schedule"):
    print(f"\n{Style.BRIGHT}{Fore.MAGENTA}{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}{Style.RESET_ALL}")
    if not tasks:
        print(f"  {Fore.YELLOW}No tasks scheduled.{Style.RESET_ALL}\n")
        return
    rows = [
        [
            task_emoji(t.description),
            Style.BRIGHT + t.time + Style.RESET_ALL,
            t.pet_name,
            t.description,
            f"{t.duration_minutes} min",
            fmt_priority(t.priority),
            fmt_status(t.completed),
        ]
        for t in tasks
    ]
    headers = ["", "Time", "Pet", "Task", "Duration", "Priority", "Status"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    print()


def print_urgency(ranked):
    print(f"\n{Style.BRIGHT}{Fore.MAGENTA}{'─' * 60}")
    print("  Urgency Ranking")
    print(f"{'─' * 60}{Style.RESET_ALL}")
    if not ranked:
        print(f"  {Fore.YELLOW}No pending tasks.{Style.RESET_ALL}\n")
        return
    rows = [
        [
            Style.BRIGHT + f"{score:.1f}" + Style.RESET_ALL,
            task_emoji(task.description),
            task.pet_name,
            task.description,
            fmt_priority(task.priority),
            str(task.due_date),
        ]
        for task, score in ranked
    ]
    headers = ["Score", "", "Pet", "Task", "Priority", "Due"]
    print(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    print()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    owner = Owner("Jordan")

    mochi = Pet("Mochi", "dog", 3)
    luna = Pet("Luna", "cat", 5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    print(f"\n{Style.BRIGHT}Owner:{Style.RESET_ALL} {owner.name}")
    for pet in owner.get_pets():
        print(f"  {species_emoji(pet.species)} {pet.name} ({pet.species}, age {pet.age})")

    today = date.today()

    mochi.add_task(Task("Morning walk",       "07:30", 30, "high",   "daily", "Mochi", due_date=today))
    mochi.add_task(Task("Breakfast feeding",  "08:00", 10, "high",   "daily", "Mochi", due_date=today))
    mochi.add_task(Task("Heartworm medication","08:00", 5,  "high",   "once",  "Mochi", due_date=today))
    mochi.add_task(Task("Evening walk",       "18:00", 45, "medium", "daily", "Mochi", due_date=today))

    luna.add_task(Task("Breakfast feeding",   "07:00",  5, "high",   "daily", "Luna",  due_date=today))
    luna.add_task(Task("Grooming session",    "14:00", 15, "low",    "weekly","Luna",  due_date=today))

    mochi.add_task(Task("Vet appointment",    "10:00", 60, "high",   "once",  "Mochi",
                        due_date=today + timedelta(days=1)))

    scheduler = Scheduler(owner)

    # Today's schedule
    print_schedule(scheduler.get_todays_schedule())

    # Conflict detection
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            print(f"{Fore.RED + Style.BRIGHT}⚠  {w}{Style.RESET_ALL}")
        print()
    else:
        print(f"{Fore.GREEN}✓  No scheduling conflicts.{Style.RESET_ALL}\n")

    # Filter: Mochi's pending tasks
    pending_mochi = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    print_schedule(pending_mochi, title="Mochi's Pending Tasks 🐕")

    # Mark a task complete and show recurrence
    morning_walk = mochi.get_tasks()[0]
    scheduler.mark_task_complete(morning_walk, mochi)
    print(
        f"Marked {Fore.CYAN}{morning_walk.description}{Style.RESET_ALL} complete. "
        f"Next occurrence: {Fore.GREEN}"
        + str(next(
            t.due_date for t in mochi.get_tasks()
            if t.description == "Morning walk" and not t.completed
        ))
        + Style.RESET_ALL
    )
    print()

    # Urgency ranking
    print_urgency(scheduler.get_urgency_ranked_tasks())

    # Next available slot demo
    slot = scheduler.find_next_available_slot("Mochi", 20, start_after="07:00")
    print(
        f"Next 20-min slot for Mochi after 07:00: "
        f"{Fore.GREEN + Style.BRIGHT}{slot}{Style.RESET_ALL}\n"
    )


if __name__ == "__main__":
    main()
