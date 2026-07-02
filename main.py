from pawpal_system import *
from datetime import time, date

owner1 = Owner(
    owner_id="o1",
    name="Alice",
    pets=[],
    preferences={
        PreferenceKey.NO_MEDS_BEFORE: time(8, 0),
        PreferenceKey.MAX_WALK_HOURS_PER_DAY: 2,
    }
)

pet1 = Pet(
    pet_id="p1",
    owner_id="o1",
    name="Max",
    species="dog",
    tasks=[]
)

pet2 = Pet(
    pet_id="p2",
    owner_id="o1",
    name="Coco",
    species="cat",
    tasks=[]
)

# --- Tasks for Max (dog) --- added OUT OF ORDER (18:00, 07:00, 12:00) ---
pet1.add_task(Task(
    task_id="t3",
    pet_id="p1",
    type=TaskType.MEDS,
    description="Evening heartworm pill",
    status=TaskStatus.PENDING,
    start_time=time(18, 0),
    end_time=time(18, 5),
    priority=Priority.HIGH,
    recurrence_freq=RecurrenceFreq.DAILY,
))

pet1.add_task(Task(
    task_id="t1",
    pet_id="p1",
    type=TaskType.WALK,
    description="Morning walk",
    status=TaskStatus.PENDING,
    start_time=time(7, 0),
    end_time=time(7, 45),
    priority=Priority.MEDIUM,
    recurrence_freq=RecurrenceFreq.DAILY,
))

pet1.add_task(Task(
    task_id="t2",
    pet_id="p1",
    type=TaskType.FEEDING,
    description="Lunch feeding",
    status=TaskStatus.PENDING,
    start_time=time(12, 0),
    end_time=time(12, 15),
    priority=Priority.LOW,
    recurrence_freq=RecurrenceFreq.DAILY,
))

# --- Tasks for Coco (cat) --- added OUT OF ORDER (14:00, 06:30, 08:00) ---
pet2.add_task(Task(
    task_id="t5",
    pet_id="p2",
    type=TaskType.GROOMING,
    description="Afternoon brushing",
    status=TaskStatus.PENDING,
    start_time=time(14, 0),
    end_time=time(14, 20),
    priority=Priority.LOW,
    recurrence_freq=RecurrenceFreq.WEEKLY,
    recurrence_days=[3],  # Wednesday
))

pet2.add_task(Task(
    task_id="t6",
    pet_id="p2",
    type=TaskType.MEDS,
    description="Evening flea treatment",
    status=TaskStatus.PENDING,
    start_time=time(6, 30),
    end_time=time(6, 35),
    priority=Priority.HIGH,
    recurrence_freq=RecurrenceFreq.DAILY,
))

pet2.add_task(Task(
    task_id="t4",
    pet_id="p2",
    type=TaskType.FEEDING,
    description="Morning feeding",
    status=TaskStatus.PENDING,
    start_time=time(8, 0),
    end_time=time(8, 10),
    priority=Priority.MEDIUM,
    recurrence_freq=RecurrenceFreq.DAILY,
))

owner1.add_pet(pet1)
owner1.add_pet(pet2)

scheduler = Scheduler()
today = date(2026, 6, 25)

plan_all = scheduler.generate_daily_plan(owner1, today)
plan_max = scheduler.generate_daily_plan(owner1, today, pet=pet1)

print("=== All pets | sorted by TIME ===")
print(plan_all.summary())

print()
print("=== All pets | sorted by PRIORITY ===")
print(plan_all.summary(sort_by_priority=True))

print()
print("=== Max only | sorted by TIME ===")
print(plan_max.summary())

print()
print("=== Max only | sorted by PRIORITY ===")
print(plan_max.summary(sort_by_priority=True))
