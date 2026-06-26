import datetime

import pytest

from pawpal_system import (
    Owner,
    Pet,
    PreferenceKey,
    RecurrenceFreq,
    Scheduler,
    Task,
    TaskStatus,
    TaskType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(
    task_id="t1",
    pet_id="p1",
    task_type=TaskType.WALK,
    description="Morning walk",
    status=TaskStatus.PENDING,
    start_h=8,
    start_m=0,
    end_h=9,
    end_m=0,
    priority=1,
    recurrence_freq=RecurrenceFreq.DAILY,
    recurrence_days=None,
) -> Task:
    return Task(
        task_id=task_id,
        pet_id=pet_id,
        type=task_type,
        description=description,
        status=status,
        start_time=datetime.time(start_h, start_m),
        end_time=datetime.time(end_h, end_m),
        priority=priority,
        recurrence_freq=recurrence_freq,
        recurrence_days=recurrence_days or [],
    )


def make_owner_with_task(task, preferences=None):
    owner = Owner(owner_id="o1", name="Alice", preferences=preferences or {})
    pet   = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(task)
    owner.add_pet(pet)
    return owner


TODAY = datetime.date.today()


# ---------------------------------------------------------------------------
# 1a. Time conflicts
# ---------------------------------------------------------------------------

def test_overlapping_tasks_detected():
    a = make_task(task_id="a", start_h=8, end_h=9)
    b = make_task(task_id="b", start_h=8, start_m=30, end_h=9, end_m=30)
    conflicts = Scheduler().detect_conflicts([a, b])
    assert len(conflicts) == 1
    assert (a, b) in conflicts


def test_adjacent_tasks_not_conflicting():
    a = make_task(task_id="a", start_h=8, end_h=9)
    b = make_task(task_id="b", start_h=9, end_h=10)
    assert Scheduler().detect_conflicts([a, b]) == []


def test_non_overlapping_tasks_no_conflict():
    a = make_task(task_id="a", start_h=7, end_h=8)
    b = make_task(task_id="b", start_h=10, end_h=11)
    assert Scheduler().detect_conflicts([a, b]) == []


def test_conflict_skips_lower_priority_task():
    high = make_task(task_id="high", priority=10, start_h=8, end_h=9)
    low  = make_task(task_id="low",  priority=1,  start_h=8, start_m=30, end_h=9, end_m=30)

    owner = Owner(owner_id="o1", name="Alice")
    pet   = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(high)
    pet.add_task(low)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert high in plan.scheduled_tasks
    assert low in plan.skipped_tasks


# ---------------------------------------------------------------------------
# 1b. Preferences
# ---------------------------------------------------------------------------

def test_meds_before_preference_skips_early_meds():
    meds  = make_task(task_id="m1", task_type=TaskType.MEDS, start_h=7, end_h=7, end_m=15)
    prefs = {PreferenceKey.NO_MEDS_BEFORE: datetime.time(9, 0)}
    plan  = Scheduler().generate_daily_plan(make_owner_with_task(meds, prefs), TODAY)
    assert meds in plan.skipped_tasks


def test_meds_after_threshold_is_scheduled():
    meds  = make_task(task_id="m2", task_type=TaskType.MEDS, start_h=10, end_h=10, end_m=15)
    prefs = {PreferenceKey.NO_MEDS_BEFORE: datetime.time(9, 0)}
    plan  = Scheduler().generate_daily_plan(make_owner_with_task(meds, prefs), TODAY)
    assert meds in plan.scheduled_tasks


def test_walk_exceeding_max_hours_is_skipped():
    walk  = make_task(task_id="w1", task_type=TaskType.WALK, start_h=8, end_h=10)  # 2 h
    prefs = {PreferenceKey.MAX_WALK_HOURS_PER_DAY: 1}
    plan  = Scheduler().generate_daily_plan(make_owner_with_task(walk, prefs), TODAY)
    assert walk in plan.skipped_tasks


def test_walk_within_max_hours_is_scheduled():
    walk  = make_task(task_id="w2", task_type=TaskType.WALK, start_h=8, end_h=9)  # 1 h
    prefs = {PreferenceKey.MAX_WALK_HOURS_PER_DAY: 2}
    plan  = Scheduler().generate_daily_plan(make_owner_with_task(walk, prefs), TODAY)
    assert walk in plan.scheduled_tasks


# ---------------------------------------------------------------------------
# 1c. Priority ordering
# ---------------------------------------------------------------------------

def test_sort_by_priority_descending():
    tasks = [
        make_task(task_id="low",  priority=1),
        make_task(task_id="high", priority=10),
        make_task(task_id="mid",  priority=5),
    ]
    result = Scheduler().sort_by_priority(tasks)
    assert [t.task_id for t in result] == ["high", "mid", "low"]


def test_higher_priority_wins_conflict():
    low  = make_task(task_id="low",  priority=1,  start_h=8, end_h=9)
    high = make_task(task_id="high", priority=10, start_h=8, start_m=30, end_h=9, end_m=30)

    owner = Owner(owner_id="o1", name="Alice")
    pet   = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(low)
    pet.add_task(high)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert high in plan.scheduled_tasks
    assert low in plan.skipped_tasks


# ---------------------------------------------------------------------------
# 1d. Recurrence
# ---------------------------------------------------------------------------

def test_daily_task_is_due_every_day():
    task = make_task(recurrence_freq=RecurrenceFreq.DAILY)
    for offset in range(7):
        d = datetime.date(2026, 1, 5) + datetime.timedelta(days=offset)
        assert task.is_due_on(d)


def test_once_task_never_due_via_is_due_on():
    task = make_task(recurrence_freq=RecurrenceFreq.ONCE)
    assert task.is_due_on(TODAY) is False


def test_weekly_task_due_on_matching_weekdays():
    task = make_task(recurrence_freq=RecurrenceFreq.WEEKLY, recurrence_days=[1, 3])
    monday    = datetime.date(2026, 6, 22)
    wednesday = datetime.date(2026, 6, 24)
    tuesday   = datetime.date(2026, 6, 23)
    assert task.is_due_on(monday) is True
    assert task.is_due_on(wednesday) is True
    assert task.is_due_on(tuesday) is False


# ---------------------------------------------------------------------------
# 2. mark_complete() changes task status
# ---------------------------------------------------------------------------

def test_mark_complete_sets_status_to_done():
    task = make_task(status=TaskStatus.PENDING)
    task.mark_complete()
    assert task.status == TaskStatus.DONE


def test_mark_complete_on_in_progress_task():
    task = make_task(status=TaskStatus.IN_PROGRESS)
    task.mark_complete()
    assert task.status == TaskStatus.DONE


def test_status_not_done_before_mark_complete():
    task = make_task(status=TaskStatus.PENDING)
    assert task.status != TaskStatus.DONE


# ---------------------------------------------------------------------------
# 3. Adding a task to a Pet increases task count
# ---------------------------------------------------------------------------

def test_new_pet_has_zero_tasks():
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    assert len(pet.tasks) == 0


def test_add_task_increases_count_by_one():
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(make_task())
    assert len(pet.tasks) == 1


def test_add_multiple_tasks_increases_count_correctly():
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    for i in range(5):
        pet.add_task(make_task(task_id=f"t{i}"))
    assert len(pet.tasks) == 5


def test_added_task_is_correct_instance():
    pet  = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    task = make_task(task_id="specific")
    pet.add_task(task)
    assert task in pet.tasks
