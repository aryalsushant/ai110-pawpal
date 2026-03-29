# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

Three core actions a user needs to perform:

1. Add a pet with basic info (name, species, age).
2. Schedule a care task (feeding, walk, medication, grooming) for a specific pet at a specific time.
3. View today's full schedule, sorted by time, with conflict warnings and completion status.

The four main classes and their responsibilities:

Task: Holds all data about a single care activity. Attributes include description, scheduled time, duration, priority, frequency (once/daily/weekly), completion status, and due date. The class knows how to mark itself complete and generate the next recurrence.

Pet: Represents one pet. Stores the pet's name, species, and age. Owns a list of Task objects and provides methods to add, retrieve, and remove tasks.

Owner: Represents the human user. Stores the owner's name and a list of Pet objects. Provides a method to collect all tasks across every pet.

Scheduler: The decision-making layer. Accepts an Owner and operates on all tasks. Handles sorting by time, filtering by pet or status, detecting time conflicts, and advancing recurring tasks after completion.

**b. Design changes**

During implementation, the Scheduler gained a `mark_task_complete` method that wraps the Task's own `mark_complete`. The reason: the Scheduler is the only layer that knows about recurrence at the system level. Putting recurrence logic inside Task itself would have forced Task to know about dates and scheduling policy, mixing two responsibilities into one class.

A `due_date` field was also added to Task. The initial sketch used only a time string (HH:MM). Adding a date made it possible to filter "today's" tasks correctly and to advance daily or weekly tasks to their next occurrence.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

- Time: tasks are sorted by their scheduled time (HH:MM string, lexicographic sort works for zero-padded 24-hour format).
- Priority: high-priority tasks appear first within the same time slot.
- Due date: only tasks whose due_date matches today are included in the daily view.

Priority was treated as the tiebreaker rather than the primary sort key because pet care tasks are time-sensitive. A medication at 08:00 must happen at 08:00 regardless of whether a walk has higher priority.

**b. Tradeoffs**

The conflict detector checks for exact time matches only. Two tasks scheduled at 08:00 for the same pet will trigger a warning. Tasks scheduled at 08:00 and 08:15 will not, even if the first task has a 30-minute duration and would overlap.

This tradeoff is reasonable for an MVP. Most pet care tasks are short and loosely time-boxed. Owners think in slots ("morning," "evening") rather than precise minute-by-minute blocks. Implementing duration-based overlap detection would add significant complexity for a marginal benefit at this stage.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used for three things: brainstorming the class structure, generating the Mermaid UML diagram syntax, and suggesting test cases for edge scenarios like an owner with no pets or two tasks at identical times.

The most useful prompts were specific. Asking "how should Scheduler retrieve tasks from Owner's pets?" produced a clear pattern. Asking "generate a pet care app" produced too much at once.

**b. Judgment and verification**

The AI initially suggested storing tasks directly on the Scheduler as a flat list copied from the Owner at construction time. That would break the app: adding a new task after the Scheduler was built would not appear in the schedule.

The fix was to have Scheduler always call `owner.get_all_tasks()` at runtime rather than caching the list. This keeps the data source of truth in Owner and Pet, not in Scheduler.

---

## 4. Testing and Verification

**a. What you tested**

Five behaviors were tested:

1. `mark_complete()` sets the task's `completed` flag to True.
2. Adding a task to a Pet increases that pet's task count.
3. Sorting returns tasks in chronological order.
4. Marking a daily task complete creates a new task for the next day.
5. The Scheduler flags two tasks for the same pet at the same time as a conflict.

These tests matter because they cover the three layers of the system: data (Task), storage (Pet), and logic (Scheduler).

**b. Confidence**

Confidence level: 4/5 stars.

The core scheduling behaviors are verified. Edge cases to test next: a pet with zero tasks, an owner with zero pets, tasks with identical times across different pets (should not conflict), and weekly recurrence spanning a month boundary.

---

## 5. Reflection

**a. What went well**

The "CLI-first" workflow was effective. Having main.py as a fast feedback loop meant every feature was verified in the terminal before the UI was touched. Bugs appeared early when they were cheap to fix.

**b. What you would improve**

The Task `due_date` defaults to today, which means tasks added in the afternoon show up on the same day's schedule regardless of the intended start date. A proper task-creation form should always prompt for a due date.

**c. Key takeaway**

The human architect's job is to hold the system's rules in their head and catch when AI suggestions violate those rules. AI writes fast. It does not track your design constraints across the whole session. Reviewing each suggestion against the class diagram before accepting it saved real debugging time.
