import datetime
import uuid

import streamlit as st

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
# Session state init
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_id="owner", name="", pets=[])
if "daily_plan" not in st.session_state:
    st.session_state.daily_plan = None

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
st.subheader("Owner")
owner_name = st.text_input("Owner name", value=st.session_state.owner.name or "Jordan")
st.session_state.owner.name = owner_name

st.markdown("**Preferences**")
prefs = {}

col1, col2 = st.columns(2)
with col1:
    use_no_meds_before = st.checkbox("Set no-meds-before time")
    if use_no_meds_before:
        no_meds_before = st.time_input("No meds before", value=datetime.time(9, 0))
        prefs[PreferenceKey.NO_MEDS_BEFORE] = no_meds_before

with col2:
    use_max_walk = st.checkbox("Set max walk hours/day")
    if use_max_walk:
        max_walk = st.number_input("Max walk hours", min_value=0.5, max_value=24.0, value=2.0, step=0.5)
        prefs[PreferenceKey.MAX_WALK_HOURS_PER_DAY] = max_walk

st.session_state.owner.preferences = prefs

# ---------------------------------------------------------------------------
# Add pet
# ---------------------------------------------------------------------------
st.subheader("Pets")

with st.form("add_pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        new_pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
    add_pet = st.form_submit_button("Add pet")

if add_pet:
    pet = Pet(
        pet_id=str(uuid.uuid4()),
        owner_id="owner",
        name=new_pet_name,
        species=new_species,
    )
    st.session_state.owner.add_pet(pet)
    st.success(f"Added {new_pet_name}!")

if st.session_state.owner.pets:
    for pet in st.session_state.owner.pets:
        st.markdown(f"- **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------------------
# Add task
# ---------------------------------------------------------------------------
st.subheader("Tasks")

if not st.session_state.owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_map = {p.name: p for p in st.session_state.owner.pets}

    selected_pet_name = st.selectbox("For pet", list(pet_map.keys()))

    col1, col2 = st.columns(2)
    with col1:
        task_type = st.selectbox("Task type", [t.value for t in TaskType])
    with col2:
        description = st.text_input("Description", value="Morning walk")

    col3, col4 = st.columns(2)
    with col3:
        start_time = st.time_input("Start time", value=datetime.time(8, 0))
    with col4:
        end_time = st.time_input("End time", value=datetime.time(9, 0))

    start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
    end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
    duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
    if duration_minutes > 0:
        st.caption(f"Duration: {duration_minutes} minutes")
    else:
        st.warning("End time must be after start time.")

    col5, col6 = st.columns(2)
    with col5:
        priority = st.selectbox("Priority", [1, 2, 3, 4, 5], index=2)
    with col6:
        recurrence_freq = st.selectbox("Recurrence", [f.value for f in RecurrenceFreq])

    DAY_MAP = {"Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6, "Sun": 7}
    scheduled_date = None
    recurrence_days = []

    if recurrence_freq == RecurrenceFreq.ONCE.value:
        scheduled_date = st.date_input("Scheduled date", value=datetime.date.today())
    elif recurrence_freq == RecurrenceFreq.WEEKLY.value:
        selected_days = st.multiselect("Repeat on", list(DAY_MAP.keys()))
        recurrence_days = [DAY_MAP[d] for d in selected_days]

    if st.button("Add task"):
        if duration_minutes <= 0:
            st.error("End time must be after start time.")
        else:
            task = Task(
                task_id=str(uuid.uuid4()),
                pet_id=pet_map[selected_pet_name].pet_id,
                type=TaskType(task_type),
                description=description,
                status=TaskStatus.PENDING,
                start_time=start_time,
                end_time=end_time,
                priority=priority,
                recurrence_freq=RecurrenceFreq(recurrence_freq),
                recurrence_days=recurrence_days,
                scheduled_date=scheduled_date,
            )
            pet_map[selected_pet_name].add_task(task)
            st.success(f"Added task '{description}' to {selected_pet_name}! ({duration_minutes} min)")

    status_options = [s.value for s in TaskStatus]

    for pet in st.session_state.owner.pets:
        if pet.tasks:
            st.markdown(f"**{pet.name}'s tasks:**")
            header_cols = st.columns([2, 3, 1, 1, 1, 1, 2])
            for label in ["type", "description", "start", "end", "priority", "recurrence", "status"]:
                header_cols[["type", "description", "start", "end", "priority", "recurrence", "status"].index(label)].markdown(f"**{label}**")

            for t in pet.tasks:
                cols = st.columns([2, 3, 1, 1, 1, 1, 2])
                cols[0].write(t.type.value)
                cols[1].write(t.description)
                cols[2].write(t.start_time.strftime("%H:%M"))
                cols[3].write(t.end_time.strftime("%H:%M"))
                cols[4].write(t.priority)
                cols[5].write(t.recurrence_freq.value)
                new_status = cols[6].selectbox(
                    "status",
                    status_options,
                    index=status_options.index(t.status.value),
                    key=f"status_{t.task_id}",
                    label_visibility="collapsed",
                )
                if new_status != t.status.value:
                    t.status = TaskStatus(new_status)

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Build Schedule")

if not st.session_state.owner.pets:
    st.info("Add a pet first before generating a schedule.")
else:
    col1, col2 = st.columns(2)
    with col1:
        pet_options = ["All pets"] + [p.name for p in st.session_state.owner.pets]
        selected_pet_option = st.selectbox("Pet", pet_options)
    with col2:
        schedule_date = st.date_input("Date", value=datetime.date.today())

    status_filter = st.multiselect(
        "Show task statuses",
        options=[s.value for s in TaskStatus],
        default=["pending", "in_progress"],
    )
    sort_by_priority = st.checkbox("Sort by priority (high → low) within each status")

    if st.button("Generate schedule"):
        owner = st.session_state.owner
        pet_arg = None
        if selected_pet_option != "All pets":
            pet_arg = next(p for p in owner.pets if p.name == selected_pet_option)
        st.session_state.daily_plan = Scheduler().generate_daily_plan(owner, schedule_date, pet=pet_arg)

    if st.session_state.daily_plan is not None:
        plan = st.session_state.daily_plan
        st.markdown(f"```\n{plan.summary(status_filter=status_filter or None, sort_by_priority=sort_by_priority)}\n```")
