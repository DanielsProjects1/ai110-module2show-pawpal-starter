from datetime import datetime

import pytest

from pawpal import Pet, Owner, Scheduler, Task


def test_scheduler_honors_priority_and_time_limit():
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=20, priority="medium"),
        Task(title="Groom", duration_minutes=120, priority="low"),
    ]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner, reference_date=datetime(2023, 1, 1))

    # only 60 minutes available, so Walk + Feed should be scheduled first
    assert len(result.items) == 2
    assert result.items[0].task.title == "Walk"
    assert result.items[1].task.title == "Feed"
    assert len(result.unplanned_tasks) == 1
    assert result.unplanned_tasks[0].title == "Groom"


def test_scheduler_respects_available_window():
    tasks = [Task(title="Enrichment", duration_minutes=90, priority="high")]
    owner = Owner(time_available=120, preferred_start_hour=9, preferred_end_hour=10)
    result = Scheduler.generate_schedule(tasks, owner, reference_date=datetime(2023, 1, 1))

    # only 60 min window in preferred hours
    assert len(result.items) == 0
    assert len(result.unplanned_tasks) == 1


def test_explanation_contains_unplanned_tasks():
    tasks = [
        Task(title="Meds", duration_minutes=30, priority="high"),
        Task(title="Groom", duration_minutes=180, priority="low"),
    ]
    owner = Owner(time_available=45, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner, reference_date=datetime(2023, 1, 1))

    explanation = result.explanation()
    assert "Unplanned tasks" in explanation
    assert "Groom" in explanation


def test_task_mark_complete_changes_status():
    task = Task(title="Walk", duration_minutes=30, priority="high")
    assert task.status == "pending"
    task.mark_complete()
    assert task.status == "completed"


def test_adding_task_to_pet_increases_task_count():
    pet = Pet(name="Mochi", species="dog")
    task = Task(title="Walk", duration_minutes=30, priority="high")
    
    assert len(pet.tasks) == 0
    pet.add_task(task)
    assert len(pet.tasks) == 1
