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

During implementation, the Scheduler gained a `mark_task_complete` method wrapping the Task's own `mark_complete`. The Scheduler is the only layer aware of recurrence at the system level. Putting recurrence logic inside Task itself would have forced Task to know about dates and scheduling policy, mixing two responsibilities into one class.

A `due_date` field was also added to Task. The initial sketch used only a time string (HH:MM). Adding a date made it possible to filter today's tasks correctly and to advance daily or weekly tasks to their next occurrence.

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

Three Copilot features drove most of the work:

Agent Mode was used to flesh out the full class implementations in pawpal_system.py after the skeleton was in place. It handled writing all method bodies at once, which was faster than doing each method in isolation.

Inline Chat was used on specific algorithmic methods. For the `sort_by_time` method, the prompt was: "how do I sort a list of objects by a HH:MM string attribute?" The suggestion to use a lambda with `sorted()` was correct and kept.

The Generate tests smart action was used to draft the initial test stubs for `test_pawpal.py`. The generated tests covered happy paths well but missed edge cases, so additional tests were written by hand for things like an owner with no pets and weekly recurrence across month boundaries.

Separate chat sessions were opened for each phase. The design session stayed focused on UML and class responsibilities. The algorithmic session focused on sorting, filtering, and conflict detection. The testing session focused entirely on edge cases. Keeping sessions separate meant the context window held only relevant code and questions. Mixing everything into one session would have produced suggestions informed by stale context from earlier phases.

**b. Judgment and verification**

The AI initially suggested storing tasks directly on the Scheduler as a flat list copied from the Owner at construction time. Accepting this suggestion as-is would have broken the app: adding a new task after building the Scheduler would not appear in the schedule.

The fix was to have Scheduler always call `owner.get_all_tasks()` at runtime rather than caching a list at startup. This keeps the data source of truth in Owner and Pet. The verification step was running `main.py` after adding a task mid-session and confirming the new task appeared in the output.

---

## 4. Testing and Verification

**a. What you tested**

Ten behaviors were tested across three system layers:

Task layer: `mark_complete()` sets the completed flag. Daily recurrence produces a task dated one day forward. Weekly recurrence produces a task dated seven days forward. A once task produces no next occurrence.

Pet layer: Adding a task increases the pet's task count. Removing a task decreases it.

Scheduler layer: Sorting returns tasks in chronological order. Today's schedule excludes tasks with a future due date. Filter by pet name returns only tasks for the named pet. Filter by status separates done from pending. Conflict detection flags two tasks for the same pet at the same time. Conflict detection does not flag identical times across different pets. Marking a daily task complete adds a new task for tomorrow.

These tests matter because they cover all three layers independently and the interactions between them.

**b. Confidence**

Confidence level: 4 out of 5 stars.

The core scheduling behaviors are verified across both happy paths and the key edge cases. Edge cases to test in a future iteration: tasks with identical descriptions for the same pet at different times, weekly recurrence where the next date crosses a year boundary, and the behavior when an Owner has zero pets and the schedule is requested.

---

## 5. Reflection

**a. What went well**

The CLI-first workflow was effective. Having `main.py` as a fast feedback loop meant every feature was verified in the terminal before the UI was touched. Bugs appeared early when they were cheap to fix. The separation between data (Task, Pet, Owner) and logic (Scheduler) also made writing tests straightforward because each layer is testable in isolation, without setting up the others.

**b. What you would improve**

The Task `due_date` defaults to today, which means tasks added in the afternoon show up on the same day's schedule regardless of the intended start date. A proper task-creation form should always prompt for a due date explicitly. The conflict detector also only checks same-pet conflicts. A future version should let the owner opt into cross-pet conflict detection so they know when two pets need attention at the same time.

**c. Key takeaway**

The human architect's job is to hold the system's rules and review each AI suggestion against the existing design before accepting it. AI writes fast and generates plausible code, but it does not track your design constraints across a whole session. Reviewing every suggestion against the class diagram before accepting it prevented at least two real bugs. Using separate chat sessions for each phase kept suggestions grounded in the right context and made the collaboration more predictable.

---

## 6. Challenge 4: Professional UI and Output Formatting

I added a shared `ui_helpers.py` module with four formatting functions: `task_emoji` maps description keywords to emojis (🦮 for walks, 🍖 for feeding, 💊 for medication, ✂️ for grooming, 🏥 for vet appointments, 🎾 for play), `species_emoji` maps pet species to icons, `priority_badge_html` returns a color-coded HTML span (red for high, orange for medium, green for low), and `status_badge_html` returns ✅ Done or ⏳ Pending badges. In `main.py`, I replaced the plain print loop with `tabulate` using the `rounded_outline` style and `colorama` for priority colors (red for high, yellow for medium, green for low) and cyan for pending status. In `app.py`, I replaced every `st.table()` call with a custom `html_table()` function rendered via `st.markdown(unsafe_allow_html=True)` so priority and status columns show colored badges instead of plain text.

The app was later redesigned using proper Streamlit layout components. The layout switched to `wide` mode with a persistent sidebar for owner and pet setup. The main area uses five `st.tabs` to separate today's schedule, task creation, filtering, urgency ranking, and slot finding. Four `st.metric` cards replace the plain header so pet count, tasks today, pending, and completed are visible at a glance. All tables now use `st.dataframe` with `column_config` typed columns, and the urgency ranking uses `st.column_config.ProgressColumn` to show a visual bar for each task's score. `st.toast` replaces inline `st.success` calls so form state is preserved after submission.

---

## 7. Challenge 1: Advanced Algorithmic Capability

I added two advanced algorithms to the Scheduler class using Agent Mode. For the first, I prompted: "Write a method that finds the earliest available time slot for a new task given a pet's existing tasks as busy intervals." Agent Mode generated a gap-scanning loop that converts each task into a `[start, start + duration)` interval, sorts them, and advances a cursor until it finds a gap wide enough. I changed the end-of-day boundary from 1439 to 1440 minutes so tasks ending exactly at midnight are correctly rejected. For the second, I prompted: "Score each incomplete task by priority, days overdue, and recurrence frequency, then sort by urgency." The formula it produced was correct, but the overdue penalty was uncapped. I added a cap of 10 so a month-old task does not completely bury everything else in the ranking. Both methods are tested and wired into the Streamlit UI.
