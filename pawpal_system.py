from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

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


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_id: str
    pet_id: str
    type: TaskType
    description: str
    status: TaskStatus
    start_time: datetime.time
    end_time: datetime.time
    priority: Priority
    recurrence_freq: RecurrenceFreq
    recurrence_days: list[int] = field(default_factory=list)
    scheduled_date: Optional[datetime.date] = None

    def is_due_on(self, date: datetime.date) -> bool:
        """Return True if this task is scheduled to recur on the given date."""
        if self.recurrence_freq == RecurrenceFreq.ONCE:
            return self.scheduled_date == date
        
        # DAILY
        if self.recurrence_freq == RecurrenceFreq.DAILY:
            return True
        
        # WEEKLY: recurrence_days holds ISO weekday numbers (1=Mon … 7=Sun)
        return date.isoweekday() in self.recurrence_days

    def overlaps_with(self, other: Task) -> bool:
        """Return True if this task's time window overlaps with another task's."""
        return self.start_time < other.end_time and other.start_time < self.end_time
    
    def mark_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
    
    def mark_complete(self) -> None:
        self.status = TaskStatus.DONE

    def mark_cancel(self) -> None:
        self.status = TaskStatus.CANCELED


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def get_pending_tasks(self, date: datetime.date) -> list[Task]:
        """Return all PENDING tasks due on the given date for this pet."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING and t.is_due_on(date)]

    def get_tasks_due_on(self, date: datetime.date) -> list[Task]:
        """Return all tasks due on the given date regardless of status."""
        return [t for t in self.tasks if t.is_due_on(date)]

@dataclass
class Owner:
    owner_id: str
    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of every task across all of this owner's pets."""
        all_tasks = []
        for pet in self.pets:
            for t in pet.tasks:
                all_tasks.append(t)
        
        return all_tasks

    def get_preference(self, key: PreferenceKey, default=None):
        """Look up an owner preference by key, returning default if not set."""
        return self.preferences.get(key, default)


@dataclass
class Scheduler:
    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted from highest to lowest priority."""
        return sorted(tasks, key=lambda t: t.priority, reverse=True)

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return all pairs of tasks whose time windows overlap."""
        conflicts = []
        for i, a in enumerate(tasks):
            for b in tasks[i + 1:]:
                if a.overlaps_with(b):
                    conflicts.append((a, b))
        return conflicts

    def generate_daily_plan(
        self,
        owner: Owner,
        date: datetime.date,
        pet: Optional[Pet] = None,
    ) -> DailyPlan:
        """Build a DailyPlan by scheduling eligible tasks and logging skipped ones.

        Scheduling always considers ALL of the owner's pets so that conflict
        resolution is consistent regardless of which pet is later filtered for
        display.  ``pet`` is forwarded to ``DailyPlan`` only as a display hint.
        """
        pet_names = {p.pet_id: p.name for p in owner.pets}

        # Collect all tasks due today across ALL pets, split by status
        schedulable = []
        for p in owner.pets:
            for task in p.get_tasks_due_on(date):
                if task.status == TaskStatus.DONE:
                    pass  # collected below after plan is created
                elif task.status == TaskStatus.CANCELED:
                    pass
                else:
                    schedulable.append(task)

        # Priority is lowest-weight — only used for ordering
        sorted_tasks = self.sort_by_priority(schedulable)

        no_meds_before = owner.get_preference(PreferenceKey.NO_MEDS_BEFORE)
        max_walk_hours = owner.get_preference(PreferenceKey.MAX_WALK_HOURS_PER_DAY)

        filter_pet_id = pet.pet_id if pet is not None else None
        plan = DailyPlan(date=date, owner_name=owner.name, pet_names=pet_names, filter_pet_id=filter_pet_id)

        # Pre-fill done / canceled buckets
        for p in owner.pets:
            for task in p.get_tasks_due_on(date):
                if task.status == TaskStatus.DONE:
                    plan.done_tasks.append(task)
                elif task.status == TaskStatus.CANCELED:
                    plan.canceled_tasks.append(task)

        total_walk_minutes = 0.0

        for task in sorted_tasks:

            # 1. Hard constraint: time conflict with already-scheduled tasks
            conflict = None
            for scheduled in plan.scheduled_tasks:
                if task.overlaps_with(scheduled):
                    conflict = scheduled
                    break

            task_pet = pet_names.get(task.pet_id, task.pet_id)

            if conflict is not None:
                conflict_pet = pet_names.get(conflict.pet_id, conflict.pet_id)
                plan.skipped_tasks.append(task)
                plan.reasoning_log.append(
                    f"Skipped [{task_pet}] {task.type.name}: "
                    f"time conflict with [{conflict_pet}] {conflict.type.name} "
                    f"(task_id={task.task_id})"
                )
                continue

            # 2. Owner preference: NO_MEDS_BEFORE
            if task.type == TaskType.MEDS and no_meds_before is not None:
                if task.start_time < no_meds_before:
                    plan.skipped_tasks.append(task)
                    plan.reasoning_log.append(
                        f"Skipped [{task_pet}] {task.type.name}: "
                        f"meds not allowed before {no_meds_before} (NO_MEDS_BEFORE preference) "
                        f"(task_id={task.task_id})"
                    )
                    continue

            # 2. Owner preference: MAX_WALK_HOURS_PER_DAY
            task_walk_minutes = 0.0
            if task.type == TaskType.WALK and max_walk_hours is not None:
                start_dt = datetime.datetime.combine(date, task.start_time)
                end_dt = datetime.datetime.combine(date, task.end_time)
                task_walk_minutes = (end_dt - start_dt).total_seconds() / 60
                if total_walk_minutes + task_walk_minutes > max_walk_hours * 60:
                    plan.skipped_tasks.append(task)
                    plan.reasoning_log.append(
                        f"Skipped [{task_pet}] {task.type.name}: "
                        f"would exceed MAX_WALK_HOURS_PER_DAY ({max_walk_hours}h) "
                        f"(task_id={task.task_id})"
                    )
                    continue

            # All constraints passed — schedule the task
            total_walk_minutes += task_walk_minutes
            plan.scheduled_tasks.append(task)

        return plan


@dataclass
class DailyPlan:
    date: datetime.date
    owner_name: str = ""
    pet_names: dict = field(default_factory=dict)
    filter_pet_id: Optional[str] = None
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    done_tasks: list[Task] = field(default_factory=list)
    canceled_tasks: list[Task] = field(default_factory=list)
    reasoning_log: list[str] = field(default_factory=list)

    def summary(self, status_filter: Optional[list[str]] = None, sort_by_priority: bool = False) -> str:
        """Return a formatted string report of the daily plan.

        Args:
            status_filter: If provided, only sections whose status value appears
                in this list are rendered.  Pass None or an empty list to show all sections.
            sort_by_priority: When True, tasks within each section are sorted
                highest-priority first; otherwise they are sorted by start time.
        """
        def fmt(task: Task) -> str:
            pet_col    = f"[{self.pet_names.get(task.pet_id, task.pet_id)}]"
            type_col   = f"{task.type.name:<12}"
            desc_col   = f"{task.description:<30}"
            time_col   = f"({task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')})"
            prio_col   = f"[priority: {task.priority.name}]"
            status_col = f"[{task.status.value}]"
            return f"    {pet_col:<8} {type_col} - {desc_col} {time_col:<15} {prio_col} {status_col}"

        def keep_pet(task: Task) -> bool:
            """Return True if the task belongs to the currently filtered pet (or no filter is set)."""
            return self.filter_pet_id is None or task.pet_id == self.filter_pet_id

        show_all = status_filter is None or len(status_filter) == 0

        def show_section(status_value: str) -> bool:
            """Return True if this status section should appear in the output."""
            return show_all or status_value in status_filter

        def filtered(tasks: list[Task]) -> list[Task]:
            """Return only the tasks that pass the pet filter."""
            return [t for t in tasks if keep_pet(t)]

        sort_key = (lambda t: -t.priority) if sort_by_priority else (lambda t: t.start_time)

        scheduled = filtered(self.scheduled_tasks)
        done      = filtered(self.done_tasks)
        canceled  = filtered(self.canceled_tasks)
        skipped   = filtered(self.skipped_tasks)
        reasoning = [
            e for e in self.reasoning_log
            if self.filter_pet_id is None
            or f"(task_id=" not in e
            or any(
                t.task_id in e
                for t in self.skipped_tasks
                if t.pet_id == self.filter_pet_id
            )
        ]

        pet_label = self.pet_names.get(self.filter_pet_id, "All pets") if self.filter_pet_id else "All pets"
        status_label = ", ".join(status_filter) if not show_all else "all"
        lines = []
        lines.append(f"Daily Plan for {self.date}  |  Owner: {self.owner_name}  |  Pet: {pet_label}  |  Status: {status_label}")

        if show_section("pending") or show_section("in_progress"):
            visible = [t for t in scheduled if show_all or t.status.value in status_filter]
            lines.append(f"  Scheduled ({len(visible)}):")
            for task in sorted(visible, key=sort_key):
                lines.append(fmt(task))

        if show_section("done"):
            lines.append(f"  Done ({len(done)}):")
            for task in sorted(done, key=sort_key):
                lines.append(fmt(task))

        if show_section("canceled"):
            lines.append(f"  Canceled ({len(canceled)}):")
            for task in sorted(canceled, key=sort_key):
                lines.append(fmt(task))

        if show_all or show_section("pending") or show_section("in_progress"):
            lines.append(f"  Skipped ({len(skipped)}):")
            for task in sorted(skipped, key=sort_key):
                lines.append(fmt(task))
            if reasoning:
                lines.append("  Reasoning:")
                for entry in reasoning:
                    display = re.sub(r"\s*\(task_id=[^)]+\)", "", entry)
                    lines.append(f"    - {display}")

        return "\n".join(lines)