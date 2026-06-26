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
=== All pets ===
Daily Plan for 2026-06-25  |  Owner: Alice
  Scheduled (4):
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3]
    [Coco]   FEEDING      - Morning feeding                (08:00 - 08:10) [priority: 3]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2]
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5]
  Skipped (1):
    [Coco]   MEDS         - Evening flea treatment         (06:30 - 06:35) [priority: 4]
  Reasoning:
    - Skipped MEDS 'Evening flea treatment' (task_id=t6): meds not allowed before 08:00:00 (NO_MEDS_BEFORE preference)

=== Max only ===
Daily Plan for 2026-06-25  |  Owner: Alice
  Scheduled (3):
    [Max]    WALK         - Morning walk                   (07:00 - 07:45) [priority: 3]
    [Max]    FEEDING      - Lunch feeding                  (12:00 - 12:15) [priority: 2]
    [Max]    MEDS         - Evening heartworm pill         (18:00 - 18:05) [priority: 5]
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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
