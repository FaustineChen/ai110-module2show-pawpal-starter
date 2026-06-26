from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import Enum
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
    priority: int
    recurrence_freq: RecurrenceFreq
    recurrence_days: list[int] = field(default_factory=list)

    def is_due_on(self, date: datetime.date) -> bool:
        """Return True if this task is scheduled to recur on the given date."""
        # ONCE tasks have no recurring date; caller matches by task_id
        if self.recurrence_freq == RecurrenceFreq.ONCE:
            return False
        
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
        pending_tasks = []
        for t in self.tasks:
            if t.status == TaskStatus.PENDING and t.is_due_on(date):
                pending_tasks.append(t)
        
        return pending_tasks

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
        """Build a DailyPlan by scheduling eligible tasks and logging skipped ones."""
        pets_in_scope = [pet] if pet is not None else owner.pets
        pet_names = {p.pet_id: p.name for p in pets_in_scope}

        # Collect all pending tasks due today from pets in scope
        all_tasks = []
        for p in pets_in_scope:
            for task in p.get_pending_tasks(date):
                all_tasks.append(task)

        # Priority is lowest-weight — only used for ordering
        sorted_tasks = self.sort_by_priority(all_tasks)

        no_meds_before = owner.get_preference(PreferenceKey.NO_MEDS_BEFORE)
        max_walk_hours = owner.get_preference(PreferenceKey.MAX_WALK_HOURS_PER_DAY)

        plan = DailyPlan(date=date, owner_name=owner.name, pet_names=pet_names)
        total_walk_minutes = 0.0

        for task in sorted_tasks:

            # 1. Hard constraint: time conflict with already-scheduled tasks
            conflict = None
            for scheduled in plan.scheduled_tasks:
                if task.overlaps_with(scheduled):
                    conflict = scheduled
                    break

            if conflict is not None:
                plan.skipped_tasks.append(task)
                plan.reasoning_log.append(
                    f"Skipped {task.type.name} '{task.description}' (task_id={task.task_id}): "
                    f"time conflict with '{conflict.description}' (task_id={conflict.task_id})"
                )
                continue

            # 2. Owner preference: NO_MEDS_BEFORE
            if task.type == TaskType.MEDS and no_meds_before is not None:
                if task.start_time < no_meds_before:
                    plan.skipped_tasks.append(task)
                    plan.reasoning_log.append(
                        f"Skipped {task.type.name} '{task.description}' (task_id={task.task_id}): "
                        f"meds not allowed before {no_meds_before} (NO_MEDS_BEFORE preference)"
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
                        f"Skipped {task.type.name} '{task.description}' (task_id={task.task_id}): "
                        f"would exceed MAX_WALK_HOURS_PER_DAY ({max_walk_hours}h)"
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
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning_log: list[str] = field(default_factory=list)

    def summary(self) -> str:
        def fmt(task: Task) -> str:
            pet_col   = f"[{self.pet_names.get(task.pet_id, task.pet_id)}]"
            type_col  = f"{task.type.name:<12}"
            desc_col  = f"{task.description:<30}"
            time_col  = f"({task.start_time.strftime('%H:%M')} - {task.end_time.strftime('%H:%M')})"
            prio_col  = f"[priority: {task.priority}]"
            return f"    {pet_col:<8} {type_col} - {desc_col} {time_col:<15} {prio_col}"

        lines = []
        lines.append(f"Daily Plan for {self.date}  |  Owner: {self.owner_name}")
        lines.append(f"  Scheduled ({len(self.scheduled_tasks)}):")
        for task in sorted(self.scheduled_tasks, key=lambda t: t.start_time):
            lines.append(fmt(task))

        lines.append(f"  Skipped ({len(self.skipped_tasks)}):")
        for task in sorted(self.skipped_tasks, key=lambda t: t.start_time):
            lines.append(fmt(task))
        if self.reasoning_log:
            lines.append("  Reasoning:")
            for entry in self.reasoning_log:
                lines.append(f"    - {entry}")
        return "\n".join(lines)