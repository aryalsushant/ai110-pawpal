"""
PawPal+ backend logic.

Classes: Task, Pet, Owner, Scheduler
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str               # "HH:MM" 24-hour, zero-padded
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    frequency: str          # "once", "daily", "weekly"
    pet_name: str
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Set the completed flag to True."""
        self.completed = True

    def next_occurrence(self) -> Optional["Task"]:
        """Return a new Task for the next recurrence, or None if frequency is 'once'."""
        if self.frequency == "daily":
            next_date = self.due_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = self.due_date + timedelta(weeks=1)
        else:
            return None

        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            pet_name=self.pet_name,
            completed=False,
            due_date=next_date,
        )

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        return (
            f"[{self.time}] {self.description} ({self.pet_name}) "
            f"| {self.duration_minutes}min | {self.priority} | {status}"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """A pet owned by an Owner."""

    def __init__(self, name: str, species: str, age: int) -> None:
        self.name = name
        self.species = species
        self.age = age
        self._tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self._tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list if it exists."""
        if task in self._tasks:
            self._tasks.remove(task)

    def get_tasks(self) -> List[Task]:
        """Return a copy of the task list."""
        return list(self._tasks)

    def __str__(self) -> str:
        return f"{self.name} ({self.species}, age {self.age})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """The human who owns one or more pets."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's pet list."""
        self._pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return a copy of the pet list."""
        return list(self._pets)

    def get_all_tasks(self) -> List[Task]:
        """Collect and return all tasks from every pet."""
        tasks: List[Task] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def __str__(self) -> str:
        return f"Owner: {self.name} ({len(self._pets)} pet(s))"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Organizes and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_todays_schedule(self) -> List[Task]:
        """Return all tasks due today, sorted by time then priority."""
        today = date.today()
        todays = [t for t in self.owner.get_all_tasks() if t.due_date == today]
        return self.sort_by_time(todays)

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by scheduled time, then by priority (high first)."""
        return sorted(
            tasks,
            key=lambda t: (t.time, PRIORITY_ORDER.get(t.priority, 1)),
        )

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Filter all tasks by pet name and/or completion status."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for tasks on the same pet at the same time and date."""
        warnings: List[str] = []
        seen: dict[tuple, str] = {}
        for task in self.owner.get_all_tasks():
            key = (task.pet_name, task.time, task.due_date)
            if key in seen:
                warnings.append(
                    f"Conflict: {task.pet_name} has two tasks at {task.time} "
                    f"on {task.due_date} -- '{seen[key]}' and '{task.description}'"
                )
            else:
                seen[key] = task.description
        return warnings

    def mark_task_complete(self, task: Task, pet: Pet) -> None:
        """Mark a task complete and add its next recurrence to the pet if applicable."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)

    # ------------------------------------------------------------------
    # Advanced algorithms
    # ------------------------------------------------------------------

    @staticmethod
    def _to_minutes(time_str: str) -> int:
        """Convert a 'HH:MM' string to minutes since midnight."""
        h, m = time_str.split(":")
        return int(h) * 60 + int(m)

    @staticmethod
    def _to_hhmm(minutes: int) -> str:
        """Convert minutes since midnight to a zero-padded 'HH:MM' string."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def find_next_available_slot(
        self,
        pet_name: str,
        duration_minutes: int,
        start_after: str = "00:00",
    ) -> Optional[str]:
        """Return the earliest HH:MM slot on today's schedule that fits duration_minutes.

        The algorithm collects all of today's tasks for the named pet, converts
        each into a busy interval [start, start + duration), then scans the day
        from start_after onward for the first gap large enough to fit the
        requested duration. Returns None if no gap exists before midnight.
        """
        today = date.today()
        pet_tasks = [
            t for t in self.owner.get_all_tasks()
            if t.pet_name == pet_name and t.due_date == today
        ]

        # Build sorted list of busy intervals (start_min, end_min)
        busy: List[tuple[int, int]] = sorted(
            (self._to_minutes(t.time), self._to_minutes(t.time) + t.duration_minutes)
            for t in pet_tasks
        )

        cursor = self._to_minutes(start_after)
        end_of_day = 24 * 60  # 1440 minutes

        for interval_start, interval_end in busy:
            # Gap between cursor and this interval's start
            if cursor + duration_minutes <= interval_start:
                return self._to_hhmm(cursor)
            # Advance cursor past this interval
            cursor = max(cursor, interval_end)

        # Check gap after the last interval
        if cursor + duration_minutes <= end_of_day:
            return self._to_hhmm(cursor)

        return None

    def get_urgency_ranked_tasks(self) -> List[tuple["Task", float]]:
        """Return all incomplete tasks ranked by a weighted urgency score.

        Score formula:
          priority_weight  (high=3, medium=2, low=1)
          + overdue_bonus  (days overdue * 2, capped at 10)
          + frequency_weight (daily=1.0, weekly=0.5, once=0.0)

        Higher scores mean the task needs attention sooner. Only incomplete
        tasks are included. Returns a list of (task, score) tuples, highest
        score first.
        """
        priority_weight = {"high": 3, "medium": 2, "low": 1}
        frequency_weight = {"daily": 1.0, "weekly": 0.5, "once": 0.0}
        today = date.today()

        scored: List[tuple[Task, float]] = []
        for task in self.owner.get_all_tasks():
            if task.completed:
                continue
            days_overdue = max(0, (today - task.due_date).days)
            overdue_bonus = min(days_overdue * 2, 10)
            score = (
                priority_weight.get(task.priority, 1)
                + overdue_bonus
                + frequency_weight.get(task.frequency, 0.0)
            )
            scored.append((task, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
