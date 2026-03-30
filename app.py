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

# Initialize owner in session state if not exists
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        time_available=180,
        preferred_start_hour=8,
        preferred_end_hour=20
    )

# Add Pet functionality
if st.button("Add Pet"):
    # Check if pet already exists
    pet_key = f"pet_{pet_name.lower().replace(' ', '_')}"
    if pet_key not in st.session_state:
        # Create new pet
        new_pet = Pet(name=pet_name, species=species)
        st.session_state[pet_key] = new_pet
        # Add pet to owner using the method
        st.session_state.owner.add_pet(new_pet)
        st.success(f"✅ Added pet '{pet_name}' to owner!")
    else:
        st.warning(f"⚠️ Pet '{pet_name}' already exists!")

st.markdown("### Tasks")
st.caption("Add tasks and assign them to pets. Tasks will feed into the scheduler.")

# Scheduling functionality
st.divider()
st.subheader("Generate Schedule")

if st.button("Generate Daily Schedule"):
    # Collect all tasks (both assigned and unassigned)
    all_tasks = []
    all_tasks.extend(st.session_state.tasks)  # Unassigned tasks
    for pet in st.session_state.owner.pets:
        all_tasks.extend(pet.tasks)  # Assigned tasks
    
    if all_tasks:
        try:
            # Use Scheduler.generate_schedule method
            result = Scheduler.generate_schedule(
                tasks=all_tasks,
                owner=st.session_state.owner,
                reference_date=datetime.now()
            )
            
            st.success("✅ Schedule generated successfully!")
            
            # Display the schedule using the explanation method
            st.markdown("### Daily Schedule")
            st.code(result.explanation(), language="text")
            
            # Show summary
            st.markdown(f"**Summary:** {len(result.items)} tasks scheduled, {len(result.unplanned_tasks)} tasks left unplanned")
            
        except ValueError as e:
            st.error(f"❌ Scheduling failed: {e}")
    else:
        st.warning("⚠️ No tasks to schedule. Add some tasks first!")

# Demonstration of st.session_state usage
st.divider()
st.subheader("Session State Investigation")

st.markdown("""
**Understanding st.session_state:**

`st.session_state` is Streamlit's persistent storage mechanism that maintains data across app reruns.
It's essentially a dictionary that survives user interactions, form submissions, and page refreshes.

**Checking if an object exists in session state:**
""")

# Example 1: Basic key existence check
st.markdown("**1. Basic key existence check:**")
if "demo_counter" not in st.session_state:
    st.session_state.demo_counter = 0
    st.write("Created demo_counter in session state")

st.session_state.demo_counter += 1
st.write(f"Counter value: {st.session_state.demo_counter}")

# Example 2: Object initialization pattern
st.markdown("**2. Object initialization pattern (recommended for PawPal):**")

# Check if owner object exists, create if not
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        time_available=180,
        preferred_start_hour=8,
        preferred_end_hour=20
    )
    st.write("✅ Created new Owner object in session state")
else:
    st.write("ℹ️ Owner object already exists in session state")

# Check if pet object exists, create if not
pet_key = f"pet_{pet_name.lower()}"
if pet_key not in st.session_state:
    st.session_state[pet_key] = Pet(name=pet_name, species=species)
    st.write(f"✅ Created new Pet object '{pet_name}' in session state")
else:
    st.write(f"ℹ️ Pet object '{pet_name}' already exists in session state")

# Example 3: Using getattr with default (alternative approach)
st.markdown("**3. Alternative: Using getattr with default:**")
owner_alt = getattr(st.session_state, 'owner_alt', None)
if owner_alt is None:
    st.session_state.owner_alt = Owner(time_available=120)
    st.write("✅ Created owner_alt using getattr pattern")
else:
    st.write("ℹ️ owner_alt already exists")

# Display current session state contents
st.markdown("**Current session state contents:**")
st.json(dict(st.session_state))

# Methods to check existence
st.markdown("""
**Methods to check if an object exists in session state:**

1. **`key in st.session_state`** - Most common and Pythonic
2. **`hasattr(st.session_state, 'key')`** - Alternative approach
3. **`getattr(st.session_state, 'key', None) is not None`** - Check and get in one step
4. **`st.session_state.get('key') is not None`** - Using dict.get()

**Best practice for PawPal:**
```python
# Check before creating expensive objects
if "owner" not in st.session_state:
    st.session_state.owner = Owner(...)
    
if "pet_moch" not in st.session_state:
    st.session_state.pet_mochi = Pet("Mochi", "dog")
```
""")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    # Get available pets for assignment
    available_pets = [pet.name for pet in st.session_state.owner.pets] if st.session_state.owner.pets else []
    assign_to_pet = st.selectbox("Assign to pet", ["None"] + available_pets)

if st.button("Add Task"):
    # Create actual Task object
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority
    )
    
    # Assign to pet if selected
    if assign_to_pet != "None":
        pet_key = f"pet_{assign_to_pet.lower().replace(' ', '_')}"
        if pet_key in st.session_state:
            pet = st.session_state[pet_key]
            pet.add_task(new_task)  # Use the method to add task to pet
            st.success(f"✅ Added task '{task_title}' and assigned to pet '{assign_to_pet}'!")
        else:
            st.error(f"❌ Pet '{assign_to_pet}' not found!")
    else:
        # Add to general tasks list
        st.session_state.tasks.append(new_task)
        st.success(f"✅ Added task '{task_title}' (unassigned)!")

# Display current pets and their tasks
if st.session_state.owner.pets:
    st.markdown("### Current Pets and Tasks")
    for pet in st.session_state.owner.pets:
        with st.expander(f"🐾 {pet.name} ({pet.species})"):
            if pet.tasks:
                st.write("Assigned tasks:")
                task_data = [
                    {
                        "Title": task.title,
                        "Duration": f"{task.duration_minutes}m",
                        "Priority": task.priority,
                        "Status": task.status
                    }
                    for task in pet.tasks
                ]
                st.table(task_data)
            else:
                st.info("No tasks assigned yet.")
else:
    st.info("No pets added yet.")

# Display unassigned tasks
if st.session_state.tasks:
    st.markdown("### Unassigned Tasks")
    unassigned_data = [
        {
            "Title": task.title,
            "Duration": f"{task.duration_minutes}m", 
            "Priority": task.priority,
            "Status": task.status
        }
        for task in st.session_state.tasks
    ]
    st.table(unassigned_data)

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

