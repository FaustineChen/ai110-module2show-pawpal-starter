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
    status: TaskStatus
    start_time: datetime.time
    end_time: datetime.time
    priority: int
    recurrence_freq: RecurrenceFreq
    recurrence_days: list[int] = field(default_factory=list)

    def is_due_on(self, date: datetime.date) -> bool:
        pass

    def overlaps_with(self, other: Task) -> bool:
        pass


@dataclass
class Pet:
    pet_id: str
    owner_id: str
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def get_pending_tasks(self, date: datetime.date) -> list[Task]:
        pass


@dataclass
class Owner:
    owner_id: str
    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_all_tasks(self) -> list[Task]:
        pass

    def get_preference(self, key: PreferenceKey, default=None):
        pass


@dataclass
class DailyPlan:
    date: datetime.date
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning_log: list[str] = field(default_factory=list)

    def summary(self) -> str:
        pass


@dataclass
class Scheduler:
    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        pass

    def generate_daily_plan(self, owner: Owner, date: datetime.date) -> DailyPlan:
        pass
