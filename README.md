# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
=== All pets | sorted by TIME ===
Daily Plan for 2026-06-25  |  Owner: Alice  |  Pet: All pets  |  Status: all
  Scheduled (4):
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3] [pending]
    [Coco]   FEEDING      - Morning feeding                (08:00 - 08:10) [priority: 3] [pending]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2] [pending]
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5] [pending]
  Done (0):
  Canceled (0):
  Skipped (1):
    [Coco]   MEDS         - Evening flea treatment         (06:30 - 06:35) [priority: 4] [pending]
  Reasoning:
    - Skipped [Coco] MEDS: meds not allowed before 08:00:00 (NO_MEDS_BEFORE preference)

=== All pets | sorted by PRIORITY ===
Daily Plan for 2026-06-25  |  Owner: Alice  |  Pet: All pets  |  Status: all
  Scheduled (4):
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5] [pending]
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3] [pending]
    [Coco]   FEEDING      - Morning feeding                (08:00 - 08:10) [priority: 3] [pending]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2] [pending]
  Done (0):
  Canceled (0):
  Skipped (1):
    [Coco]   MEDS         - Evening flea treatment         (06:30 - 06:35) [priority: 4] [pending]
  Reasoning:
    - Skipped [Coco] MEDS: meds not allowed before 08:00:00 (NO_MEDS_BEFORE preference)

=== Max only | sorted by TIME ===
Daily Plan for 2026-06-25  |  Owner: Alice  |  Pet: Max  |  Status: all
  Scheduled (3):
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3] [pending]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2] [pending]
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5] [pending]
  Done (0):
  Canceled (0):
  Skipped (0):

=== Max only | sorted by PRIORITY ===
Daily Plan for 2026-06-25  |  Owner: Alice  |  Pet: Max  |  Status: all
  Scheduled (3):
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5] [pending]
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3] [pending]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2] [pending]
  Done (0):
  Canceled (0):
  Skipped (0):
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority()`, `DailyPlan.summary(sort_by_priority=bool)` | Tasks sorted by priority (highest to lowest); can also sort by start time within each status section |
| Filtering | `Task.is_due_on()`, `Pet.get_pending_tasks()`, `Pet.get_tasks_due_on()`, `DailyPlan.summary(status_filter=list)` | Filters by recurrence date, task status, and pet; skips tasks if constraints violated (time conflicts, max walk hours, medication time restrictions) |
| Conflict handling | `Task.overlaps_with()`, `Scheduler.detect_conflicts()`, `Scheduler.generate_daily_plan()` | Detects overlapping time windows; skips conflicting tasks; prevents double-booking pets in same time slot |
| Recurring tasks | `RecurrenceFreq` enum (ONCE, DAILY, WEEKLY), `Task.is_due_on()`, `recurrence_days` field | Supports one-time tasks (scheduled_date), daily recurring, and weekly recurring with day-of-week selection |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
