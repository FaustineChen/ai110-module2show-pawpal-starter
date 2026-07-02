import datetime

import pytest

from pawpal_system import (
    Owner,
    Pet,
    PreferenceKey,
    Priority,
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
    priority=Priority.LOW,
    recurrence_freq=RecurrenceFreq.DAILY,
    recurrence_days=None,
    scheduled_date=None,
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
        scheduled_date=scheduled_date,
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
    high = make_task(task_id="high", priority=Priority.HIGH, start_h=8, end_h=9)
    low  = make_task(task_id="low",  priority=Priority.LOW,  start_h=8, start_m=30, end_h=9, end_m=30)

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
        make_task(task_id="low",  priority=Priority.LOW),
        make_task(task_id="high", priority=Priority.HIGH),
        make_task(task_id="mid",  priority=Priority.MEDIUM),
    ]
    result = Scheduler().sort_by_priority(tasks)
    assert [t.task_id for t in result] == ["high", "mid", "low"]


def test_higher_priority_wins_conflict():
    low  = make_task(task_id="low",  priority=Priority.LOW,  start_h=8, end_h=9)
    high = make_task(task_id="high", priority=Priority.HIGH, start_h=8, start_m=30, end_h=9, end_m=30)

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


# ---------------------------------------------------------------------------
# 4. ONCE recurrence with a matching scheduled_date
# ---------------------------------------------------------------------------

def test_once_task_due_when_scheduled_date_matches():
    task = make_task(recurrence_freq=RecurrenceFreq.ONCE, scheduled_date=TODAY)
    assert task.is_due_on(TODAY) is True


def test_once_task_not_due_on_different_date():
    other_day = TODAY + datetime.timedelta(days=1)
    task = make_task(recurrence_freq=RecurrenceFreq.ONCE, scheduled_date=other_day)
    assert task.is_due_on(TODAY) is False


# ---------------------------------------------------------------------------
# 5. overlaps_with: full overlap / containment edge cases
# ---------------------------------------------------------------------------

def test_identical_time_windows_overlap():
    a = make_task(task_id="a", start_h=8, end_h=9)
    b = make_task(task_id="b", start_h=8, end_h=9)
    assert a.overlaps_with(b) is True
    assert Scheduler().detect_conflicts([a, b]) == [(a, b)]


def test_task_fully_contained_in_another_overlaps():
    outer = make_task(task_id="outer", start_h=8, end_h=12)
    inner = make_task(task_id="inner", start_h=9, end_h=10)
    assert outer.overlaps_with(inner) is True
    assert inner.overlaps_with(outer) is True


# ---------------------------------------------------------------------------
# 6. generate_daily_plan: DONE / CANCELED tasks are bucketed, not scheduled
# ---------------------------------------------------------------------------

def test_done_task_goes_to_done_bucket_not_scheduled():
    done_task = make_task(task_id="d1", status=TaskStatus.DONE)
    owner = make_owner_with_task(done_task)
    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert done_task in plan.done_tasks
    assert done_task not in plan.scheduled_tasks
    assert done_task not in plan.skipped_tasks


def test_canceled_task_goes_to_canceled_bucket_not_scheduled():
    canceled_task = make_task(task_id="c1", status=TaskStatus.CANCELED)
    owner = make_owner_with_task(canceled_task)
    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert canceled_task in plan.canceled_tasks
    assert canceled_task not in plan.scheduled_tasks
    assert canceled_task not in plan.skipped_tasks


def test_done_and_canceled_tasks_do_not_block_pending_task_scheduling():
    done_task = make_task(task_id="d1", status=TaskStatus.DONE, start_h=8, end_h=9)
    pending_task = make_task(task_id="p1", status=TaskStatus.PENDING, start_h=8, end_h=9)

    owner = Owner(owner_id="o1", name="Alice")
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(done_task)
    pet.add_task(pending_task)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert pending_task in plan.scheduled_tasks


# ---------------------------------------------------------------------------
# 7. generate_daily_plan: MAX_WALK_HOURS_PER_DAY accumulates across walks
# ---------------------------------------------------------------------------

def test_second_walk_skipped_once_accumulated_hours_exceed_max():
    walk1 = make_task(task_id="w1", task_type=TaskType.WALK, start_h=7, end_h=8)   # 1h
    walk2 = make_task(task_id="w2", task_type=TaskType.WALK, start_h=9, end_h=10)  # +1h = 2h total
    prefs = {PreferenceKey.MAX_WALK_HOURS_PER_DAY: 1}

    owner = Owner(owner_id="o1", name="Alice", preferences=prefs)
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(walk1)
    pet.add_task(walk2)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert walk1 in plan.scheduled_tasks
    assert walk2 in plan.skipped_tasks


def test_multiple_walks_within_combined_max_are_all_scheduled():
    walk1 = make_task(task_id="w1", task_type=TaskType.WALK, start_h=7, end_h=8)   # 1h
    walk2 = make_task(task_id="w2", task_type=TaskType.WALK, start_h=9, end_h=10)  # +1h = 2h total
    prefs = {PreferenceKey.MAX_WALK_HOURS_PER_DAY: 2}

    owner = Owner(owner_id="o1", name="Alice", preferences=prefs)
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(walk1)
    pet.add_task(walk2)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    assert walk1 in plan.scheduled_tasks
    assert walk2 in plan.scheduled_tasks


# ---------------------------------------------------------------------------
# 8. DailyPlan.summary()
# ---------------------------------------------------------------------------

def test_summary_includes_scheduled_task_line():
    task = make_task(task_id="s1", description="Morning walk")
    owner = make_owner_with_task(task)
    plan = Scheduler().generate_daily_plan(owner, TODAY)
    text = plan.summary()
    assert "Morning walk" in text
    assert "Scheduled (1):" in text


def test_summary_status_filter_hides_other_sections():
    scheduled_task = make_task(task_id="s1")
    meds = make_task(task_id="m1", task_type=TaskType.MEDS, start_h=7, end_h=7, end_m=15)
    prefs = {PreferenceKey.NO_MEDS_BEFORE: datetime.time(9, 0)}

    owner = Owner(owner_id="o1", name="Alice", preferences=prefs)
    pet = Pet(pet_id="p1", owner_id="o1", name="Buddy", species="dog")
    pet.add_task(scheduled_task)
    pet.add_task(meds)
    owner.add_pet(pet)

    plan = Scheduler().generate_daily_plan(owner, TODAY)
    text = plan.summary(status_filter=["pending"])
    assert "Scheduled (" in text
    assert "Done (" not in text
    assert "Canceled (" not in text


def test_summary_pet_filter_only_shows_that_pets_tasks():
    task_a = make_task(task_id="a1", pet_id="pA")
    task_b = make_task(task_id="b1", pet_id="pB", start_h=11, end_h=12)

    owner = Owner(owner_id="o1", name="Alice")
    pet_a = Pet(pet_id="pA", owner_id="o1", name="Buddy", species="dog")
    pet_b = Pet(pet_id="pB", owner_id="o1", name="Milo", species="cat")
    pet_a.add_task(task_a)
    pet_b.add_task(task_b)
    owner.add_pet(pet_a)
    owner.add_pet(pet_b)

    plan = Scheduler().generate_daily_plan(owner, TODAY, pet=pet_a)
    text = plan.summary()
    assert "Buddy" in text
    assert "Milo" not in text
