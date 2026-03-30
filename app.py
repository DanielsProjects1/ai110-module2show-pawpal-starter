import streamlit as st
from datetime import datetime

from pawpal import Owner, Pet, Scheduler, Task

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

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    st.session_state.tasks.append(
        {"title": task_title, "duration_minutes": int(duration), "priority": priority}
    )

if st.session_state.tasks:
    st.write("Current tasks:")
    st.table(st.session_state.tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Owner Preferences")
cols = st.columns(3)
with cols[0]:
    max_minutes = st.number_input("Time available (minutes per day)", min_value=15, max_value=1440, value=180)
with cols[1]:
    start_hour = st.number_input("Preferred start hour", min_value=0, max_value=23, value=8)
with cols[2]:
    end_hour = st.number_input("Preferred end hour", min_value=1, max_value=23, value=20)

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not st.session_state.tasks:
        st.warning("Please add at least one task before generating a schedule.")
    else:
        owner = Owner(
            time_available=int(max_minutes),
            preferred_start_hour=int(start_hour),
            preferred_end_hour=int(end_hour),
            pets=[pet]
        )
        pet = Pet(name=pet_name, species=species)

        tasks = [
            Task(title=t["title"], duration_minutes=t["duration_minutes"], priority=t["priority"])
            for t in st.session_state.tasks
        ]

        result = Scheduler.generate_schedule(tasks, owner, reference_date=datetime.now())

        st.success("Schedule generated successfully!")

        if result.items:
            st.write("### Planned schedule")
            schedule_data = [
                {
                    "Task": item.task.title,
                    "Start": item.start_time.strftime("%H:%M"),
                    "End": item.end_time.strftime("%H:%M"),
                    "Duration (min)": item.task.duration_minutes,
                    "Priority": item.task.priority,
                    "Reason": item.reason,
                }
                for item in result.items
            ]
            st.table(schedule_data)

            st.write("### Explanation")
            st.text(result.explanation())

        if result.unplanned_tasks:
            st.warning("Some tasks could not be scheduled due to time limits.")
            st.write("### Unplanned tasks")
            st.table(
                [{"Task": t.title, "Duration (min)": t.duration_minutes, "Priority": t.priority} for t in result.unplanned_tasks]
            )

