# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    - The system is composed of 5 core classes plus 3 Enums used for type safety.
    - The design follows OOP principles: each class has a single, clear responsibility, and objects reference each other via IDs (not direct object references) to avoid circular dependencies and keep the model serialization-friendly.  
- Enums (supporting types)
    ```
    class TaskType(Enum):
        WALK = "walk"
        FEEDING = "feeding"
        MEDS = "meds"
        ENRICHMENT = "enrichment"
        GROOMING = "grooming"
        APPOINTMENT = "appointment"

    class TaskStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        DONE = "done"
        CANCELED = "canceled"

    class RecurrenceFreq(Enum):
        ONCE = "once"
        DAILY = "daily"
        WEEKLY = "weekly"

    class PreferenceKey(Enum):
        NO_MEDS_BEFORE = "no_meds_before"
        MAX_WALK_HOURS_PER_DAY = "max_walk_hours_per_day"
    ```
- What classes did you include, and what responsibilities did you assign to each?

    ### Class 1: `Owner`

    **Responsibility:** Represents the pet owner; owns a collection of pets and holds scheduling preferences.

    | Attribute | Type |
    |---|---|
    | `owner_id` | `str` |
    | `name` | `str` |
    | `pets` | `List[Pet]` |
    | `preferences` | `Dict[str, Any]` (key restricted to `PreferenceKey.value`) |

    | Method | Description |
    |---|---|
    | `add_pet(pet: Pet) -> None` | Adds a pet to this owner |
    | `get_all_tasks() -> List[Task]` | Aggregates tasks across all owned pets |
    | `get_preference(key: PreferenceKey, default=None) -> Any` | Safe accessor for preferences |

    ### Class 2: `Pet`

    **Responsibility:** Represents a pet; owns and manages its own task list.

    | Attribute | Type |
    |---|---|
    | `pet_id` | `str` |
    | `owner_id` | `str` (reference by ID, not object) |
    | `name` | `str` |
    | `species` | `str` |
    | `tasks` | `List[Task]` |

    | Method | Description |
    |---|---|
    | `add_task(task: Task) -> None` | Adds a task to this pet |
    | `get_pending_tasks(date: date) -> List[Task]` | Returns tasks due today and not yet done |

    ### Class 3: `Task`

    **Responsibility:** Represents a single care task; knows how to evaluate its own recurrence and time overlap.

    | Attribute | Type |
    |---|---|
    | `task_id` | `str` |
    | `pet_id` | `str` (reference by ID) |
    | `type` | `TaskType` |
    | `status` | `TaskStatus` |
    | `start_time` | `time` |
    | `end_time` | `time` |
    | `priority` | `int` |
    | `recurrence_freq` | `RecurrenceFreq` |
    | `recurrence_days` | `Optional[List[int]]` (used only when `freq == WEEKLY`) |

    | Method | Description |
    |---|---|
    | `is_due_on(date: date) -> bool` | Determines if this task should appear in today's plan |
    | `overlaps_with(other: Task) -> bool` | Checks time-window conflict with another task |

    ### Class 4: `Scheduler`

    **Responsibility:** Stateless logic engine — sorts tasks, detects conflicts, and produces the final `DailyPlan`. Does not store data itself; operates on `Owner`/`Pet`/`Task` data.

    | Method | Description |
    |---|---|
    | `sort_by_priority(tasks: List[Task]) -> List[Task]` | Orders tasks by priority + owner preference weighting |
    | `apply_no_meds_before(tasks: List[Task], earliest_time: time) -> Tuple[List[Task], List[str]]` | Delays any `MEDS` task scheduled before `earliest_time`; returns adjusted tasks + reasoning messages |
    | `apply_walk_hour_limit(tasks: List[Task], max_hours: float) -> Tuple[List[Task], List[Task], List[str]]` | Processes `WALK` tasks in priority order, accumulating duration; skips tasks once the daily limit would be exceeded. Returns (kept tasks, skipped tasks, reasoning messages) |
    | `detect_conflicts(tasks: List[Task]) -> List[Tuple[Task, Task]]` | Finds overlapping task pairs |
    | `generate_daily_plan(owner: Owner, date: date) -> DailyPlan` | Orchestrates sorting + conflict resolution into a final plan |
    
    **Execution order inside `generate_daily_plan`:**
    1. Filter tasks due today via `Task.is_due_on(date)`
    2. `sort_by_priority` — establish base ordering
    3. `apply_no_meds_before` — adjust meds task timing if needed
    4. `apply_walk_hour_limit` — skip lowest-priority walk tasks exceeding the daily cap
    5. `detect_conflicts` — run last, on the final adjusted timings
    6. Assemble results into `DailyPlan` (`scheduled_tasks`, `skipped_tasks`, `reasoning_log`)

    ### Class 5: `DailyPlan`

    **Responsibility:** Structured result object — holds the final schedule plus the reasoning/explanation, decoupling Scheduler's logic from the Streamlit UI's rendering needs.

    | Attribute | Type |
    |---|---|
    | `date` | `date` |
    | `scheduled_tasks` | `List[Task]` |
    | `skipped_tasks` | `List[Task]` |
    | `reasoning_log` | `List[str]` |

    | Method | Description |
    |---|---|
    | `summary() -> str` | Generates a human-readable summary for display in the UI |

    ### Relationships (for UML)

    - `Owner` **1 → \*** `Pet` (composition: Owner owns Pets; referenced via `owner_id` in Pet)
    - `Pet` **1 → \*** `Task` (composition: Pet owns Tasks; referenced via `pet_id` in Task)
    - `Scheduler` **uses** `Owner`, `Task` (dependency, not ownership — Scheduler takes them as method parameters)
    - `Scheduler` **creates** `DailyPlan` (dependency: returns a new `DailyPlan` instance)
    - `Task` **uses** `TaskType`, `TaskStatus`, `RecurrenceFreq` (attribute typing)
    - `Owner` **uses** `PreferenceKey` (key validation for `preferences` dict)

    ### Key design decisions
    - **ID-based references** (`str`, UUID-style) instead of direct object references between `Pet`↔`Owner` and `Task`↔`Pet`, avoiding circular references and easing future persistence (DB/JSON).
    - **Enums for closed sets** (`TaskType`, `TaskStatus`, `RecurrenceFreq`, `PreferenceKey`) to prevent typos and enable UI dropdowns directly from `[e.value for e in Enum]`.
    - **Dict for open-ended data** (`Owner.preferences`) since preference *types* are fixed (via `PreferenceKey`) but *values* vary in shape (time, number, list).
    - **No separate `RecurrenceRule` class** — kept as two fields + one method on `Task` (`recurrence_freq`, `recurrence_days`, `is_due_on()`), since the recurrence logic is simple enough not to warrant a dedicated class at this project's scope.
    - **`DailyPlan` as a dedicated return object** rather than a raw list, since the spec explicitly requires the system to "explain why" — this gives the Streamlit UI a clean, structured object to render (schedule + reasoning + conflicts) separately.



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed in several ways during implementation:

1. Pet-level filtering in `generate_daily_plan`
   - Originally, `generate_daily_plan` only operated at the Owner level — it aggregated and scheduled tasks across all pets belonging to an owner.
   - This was changed to support generating a plan for a specific pet by adding an optional pet_id parameter. In practice, an owner with multiple pets often wants to check just one pet's schedule rather than always seeing every pet's tasks combined.'
   - This filtering was added without breaking the original all-pets behavior (omitting pet_id still returns the combined plan).
2. Scheduled date for one-time tasks
   - A `scheduled_date` field was added to support one-time (`RecurrenceFreq.ONCE`) tasks.
   - Originally, `Task.is_due_on()` only handled recurring patterns (daily/weekly); there was no way for a one-time task to specify which date it actually falls on.
   - Adding scheduled_date lets the owner pick a specific calendar date for one-off tasks (e.g., a one-time vet appointment), and `is_due_on()` checks this field directly when recurrence_freq == ONCE.
3. Status filtering on `DailyPlan`
   - `DailyPlan` was extended with additional fields — `filter_pet_id`, `done_tasks`, and `canceled_tasks` — so the UI can let the user filter which task statuses are displayed.
   - Originally `DailyPlan` only tracked `scheduled_tasks` and `skipped_tasks`.
   - Separating them gives the UI clearer control over what to display and avoids overloading skipped_tasks with multiple meanings.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    - Time conflicts (hard constraint) — Task.overlaps_with() checks whether two tasks' time windows overlap. This is treated as a hard constraint because two overlapping tasks are physically impossible to perform simultaneously.
    - Priority (soft ranking) — Each Task carries a priority value. In the absence of conflicts or preference violations, higher-priority tasks are scheduled first via sort_by_priority.
    - Owner preferences (user-defined soft constraints) — Two concrete preferences are implemented:
        1. NO_MEDS_BEFORE: medication tasks cannot be scheduled before a specified time; violating tasks are delayed.
        2. MAX_WALK_HOURS_PER_DAY: a daily cap on total walk duration; tasks are processed in priority order and accumulated against this cap, with lower-priority tasks skipped once the cap is reached.
- How did you decide which constraints mattered most?
    - Hard constraints (time conflicts) are resolved first conceptually, since there's no flexibility to ignore them.
    - Owner preferences rank above plain priority ordering, because they represent an explicit rule the owner deliberately set (e.g., "don't wake me up to give meds at 6am"), as opposed to priority, which is just a relative ranking used when nothing else dictates order.
    - Priority is the lowest-weighted constraint, used only to break ties or decide ordering once hard constraints and preferences have already been satisfied.
    - When two tasks share the same priority and overlap in time, the scheduler relies on Python's stable sort to break the tie — the task added earlier by the owner is retained, and the later-added conflicting task is moved to `skipped_tasks` with a "time conflict" entry in `reasoning_log`. This is an implicit first-come-first-served behavior rather than an explicit tie-breaking rule.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.  
    When total walk duration would exceed MAX_WALK_HOURS_PER_DAY, the scheduler processes walk tasks in priority order and skips lower-priority tasks entirely once the cap is reached, rather than proportionally shortening every walk task to fit.
- Why is that tradeoff reasonable for this scenario?  
    Shortening tasks proportionally is harder to implement and can produce degenerate results (e.g., a 30-minute walk cut to 5 minutes). Skipping is simpler, fully explainable — each skip is logged in reasoning_log with a clear reason — and lets the owner manually review or override it. The cost is that skipped tasks don't appear at all that day, which is an acceptable simplification at this project's scope.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project?
    - AI was used primarily during implementation and testing.
    - The overall system design (class structure, responsibilities, constraints) was largely decided upfront through discussion rather than delegated to AI — the role of AI there was more to pressure-test data structure choices (e.g., ID-based references vs. direct object references, Enum vs. dict for preferences) than to generate the design outright.
    - During coding, AI helped with implementation details and translating design decisions into working Python.
    - During testing, AI helped generate pytest cases as a starting point.

- What kinds of prompts or questions were most helpful?
    - The most useful prompts were specific and grounded in existing code — for example, asking AI to explain what a particular block of code was doing before deciding whether to accept a suggestion, or asking "what are the tradeoffs between X and Y for this specific case" rather than open-ended questions.
    - Asking AI to justify its suggestions (rather than just produce code) made it easier to evaluate whether the output actually fit the system's design.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
    - First, AI-generated pytest cases included more edge cases than were practical for this project's scope, so lower-value tests were pruned to keep the test suite focused.
    - Second, AI initially implemented pet-level filtering in `generate_daily_plan` as a display-level filter applied after generating a full combined plan — meaning if Pet A and Pet B had tasks at the same time slot with different priorities, the scheduler would correctly keep only one in the combined plan, but filtering to Pet A or Pet B individually would still show that task for both, which is incorrect. This was caught by reasoning through the expected behavior manually and corrected so that filtering scopes the input to the scheduler, not just the output.

- How did you evaluate or verify what the AI suggested?
    - AI suggestions were not accepted without first reading through the logic and confirming it made sense.
    - For code that wasn't immediately clear, the approach was to ask AI to explain what the code was doing before deciding whether to use it.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
    - I tested the scheduler’s core behaviors, including detecting time conflicts, respecting owner preferences, ordering tasks by priority, handling recurring tasks, and correctly sorting completed, canceled, and pending tasks into the daily plan.
- Why were these tests important?
    - They verify that the scheduler makes sensible decisions, avoids overlapping tasks, follows user rules, and handles common real-world cases correctly.

**b. Confidence**

- How confident are you that your scheduler works correctly?
    - 4, for the main scenarios covered by the tests.
- What edge cases would you test next if you had more time?
    - more edge cases such as multiple pets with overlapping tasks, unusual preference combinations, very short or very long tasks, and boundary cases around recurring schedules and dates.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
