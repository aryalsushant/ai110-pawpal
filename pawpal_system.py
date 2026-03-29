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

@dataclass
class Task:
    """A single pet care activity."""

    description: str
    time: str  # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str  # "once", "daily", "weekly"
    pet_name: str
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        pass

    def next_occurrence(self) -> Optional["Task"]:
        """Return a new Task for the next recurrence, or None if frequency is 'once'."""
        pass

    def __str__(self) -> str:
        pass


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
        """Add a task to this pet's task list."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet's task list."""
        pass

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        pass

    def __str__(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """The human who owns one or more pets."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        pass

    def get_pets(self) -> List[Pet]:
        """Return all pets."""
        pass

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across every pet."""
        pass

    def __str__(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Organizes and manages tasks across an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_todays_schedule(self) -> List[Task]:
        """Return all tasks due today, sorted by time."""
        pass

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Sort a list of tasks by scheduled time, then by priority."""
        pass

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Task]:
        """Filter tasks by pet name and/or completion status."""
        pass

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for tasks on the same pet at the same time."""
        pass

    def mark_task_complete(self, task: Task) -> None:
        """Mark a task complete and schedule its next recurrence if needed."""
        pass
