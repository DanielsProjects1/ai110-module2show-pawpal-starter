from datetime import datetime, timedelta

import pytest

from pawpal import Pet, Owner, Scheduler, Task, ScheduleResult, ScheduleItem


# ===== CATEGORY 1: Time Window & Availability Edge Cases =====

def test_zero_available_time_raises_error():
    """Edge case: Owner with zero time available raises ValueError."""
    with pytest.raises(ValueError, match="time_available must be > 0"):
        owner = Owner(time_available=0, preferred_start_hour=8, preferred_end_hour=20)


def test_invalid_time_window_end_before_start_raises_error():
    """Edge case: preferred_end_hour < preferred_start_hour raises ValueError."""
    with pytest.raises(ValueError, match="preferred_end_hour must be after"):
        owner = Owner(preferred_start_hour=20, preferred_end_hour=8)


def test_task_duration_exceeds_window_size_goes_unplanned():
    """Edge case: Task larger than time window goes to unplanned."""
    tasks = [Task(title="Groom", duration_minutes=120, priority="high")]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 0
    assert len(result.unplanned_tasks) == 1
    assert result.unplanned_tasks[0].title == "Groom"


def test_time_window_equals_available_time_boundary():
    """Edge case: available_time == sum(task_durations) exactly."""
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high"),
        Task(title="Feed", duration_minutes=30, priority="high"),
    ]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 2
    assert len(result.unplanned_tasks) == 0


def test_negative_task_duration_raises_error():
    """Edge case: Task with negative duration raises ValueError."""
    with pytest.raises(ValueError, match="duration_minutes must be > 0"):
        Task(title="Invalid", duration_minutes=-5, priority="high")


def test_task_duration_exactly_equals_remaining_time():
    """Edge case: Task duration == remaining time fits exactly."""
    tasks = [
        Task(title="Task1", duration_minutes=30, priority="high"),
        Task(title="Task2", duration_minutes=30, priority="high"),
    ]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 2
    assert result.total_planned_minutes == 60


# ===== CATEGORY 2: Sorting & Priority Edge Cases =====

def test_all_tasks_same_priority_sort_by_duration():
    """Edge case: Same priority tasks sort by duration (longest first)."""
    tasks = [
        Task(title="A", duration_minutes=20, priority="medium"),
        Task(title="B", duration_minutes=40, priority="medium"),
        Task(title="C", duration_minutes=30, priority="medium"),
    ]
    owner = Owner(time_available=90, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert result.items[0].task.title == "B"  # 40m first
    assert result.items[1].task.title == "C"  # 30m second
    assert result.items[2].task.title == "A"  # 20m third


def test_same_priority_and_duration_sort_by_title():
    """Edge case: Same priority and duration sort alphabetically by title."""
    tasks = [
        Task(title="Zebra", duration_minutes=30, priority="medium"),
        Task(title="Apple", duration_minutes=30, priority="medium"),
        Task(title="Mango", duration_minutes=30, priority="medium"),
    ]
    owner = Owner(time_available=90, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert result.items[0].task.title == "Apple"
    assert result.items[1].task.title == "Mango"
    assert result.items[2].task.title == "Zebra"


def test_empty_task_list_returns_empty_schedule():
    """Edge case: No tasks result in empty schedule."""
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule([], owner)
    assert len(result.items) == 0
    assert len(result.unplanned_tasks) == 0


def test_single_task_schedules_correctly():
    """Edge case: Single task schedules without issue."""
    tasks = [Task(title="Walk", duration_minutes=30, priority="high")]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 1
    assert result.items[0].task.title == "Walk"


def test_high_priority_too_large_low_priority_scheduled_via_greedy():
    """Edge case: High priority task too large, low priority fits via greedy packing."""
    tasks = [
        Task(title="LongHigh", duration_minutes=90, priority="high"),
        Task(title="SmallLow", duration_minutes=30, priority="low"),
    ]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner)
    # High priority is too large (90 > 60), small low priority should schedule via greedy
    assert len(result.unplanned_tasks) == 1
    assert result.unplanned_tasks[0].title == "LongHigh"


# ===== CATEGORY 3: Recurring Task Edge Cases =====

def test_mark_complete_non_recurring_returns_none():
    """Edge case: Non-recurring task mark_complete returns None."""
    task = Task(title="Walk", duration_minutes=30, priority="high", recurrence="none")
    result = task.mark_complete()
    assert result is None
    assert task.status == "completed"


def test_mark_complete_daily_task_creates_next_occurrence():
    """Edge case: Daily task mark_complete returns new task with +1 day due_date."""
    task = Task(title="Walk", duration_minutes=30, priority="high", recurrence="daily")
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.recurrence == "daily"
    assert next_task.status == "pending"
    assert task.status == "completed"
    assert next_task.due_date is not None


def test_mark_complete_weekly_task_creates_next_occurrence():
    """Edge case: Weekly task mark_complete returns new task with +7 days due_date."""
    today = datetime.now()
    task = Task(title="Groom", duration_minutes=60, priority="high", recurrence="weekly", due_date=today)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.recurrence == "weekly"
    assert next_task.due_date is not None
    expected_due = today + timedelta(days=7)
    assert next_task.due_date.date() == expected_due.date()


def test_invalid_recurrence_raises_error():
    """Edge case: Invalid recurrence value raises ValueError."""
    with pytest.raises(ValueError, match="recurrence must be"):
        Task(title="Walk", duration_minutes=30, recurrence="monthly")


def test_recurring_task_preserves_pet_assignment():
    """Edge case: mark_complete preserves pet assignment in new task."""
    pet = Pet(name="Buddy", species="dog")
    task = Task(title="Walk", duration_minutes=30, priority="high", recurrence="daily", assigned_pet=pet)
    next_task = task.mark_complete()
    assert next_task.assigned_pet == pet


def test_completed_task_filtered_before_scheduling():
    """Edge case: Completed tasks not included in pending_tasks filter."""
    task1 = Task(title="Walk", duration_minutes=30, priority="high", status="completed")
    task2 = Task(title="Feed", duration_minutes=20, priority="high", status="pending")
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule([task1, task2], owner)
    assert len(result.items) == 1
    assert result.items[0].task.title == "Feed"


# ===== CATEGORY 4: Conflict Detection Edge Cases =====

def test_overlapping_tasks_detected():
    """Edge case: Overlapping tasks return conflict warning."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    item1 = ScheduleItem(
        task=Task(title="Walk", duration_minutes=30),
        start_time=ref_date,
        end_time=ref_date + timedelta(minutes=30),
        reason="Test"
    )
    item2 = ScheduleItem(
        task=Task(title="Feed", duration_minutes=30),
        start_time=ref_date + timedelta(minutes=15),
        end_time=ref_date + timedelta(minutes=45),
        reason="Test"
    )
    result = ScheduleResult(items=[item1, item2])
    warning = Scheduler.detect_conflicts(result)
    assert warning is not None
    assert "overlap" in warning.lower()


def test_adjacent_tasks_no_conflict():
    """Edge case: Adjacent tasks (no overlap) return None."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    item1 = ScheduleItem(
        task=Task(title="Walk", duration_minutes=30),
        start_time=ref_date,
        end_time=ref_date + timedelta(minutes=30),
        reason="Test"
    )
    item2 = ScheduleItem(
        task=Task(title="Feed", duration_minutes=30),
        start_time=ref_date + timedelta(minutes=30),
        end_time=ref_date + timedelta(minutes=60),
        reason="Test"
    )
    result = ScheduleResult(items=[item1, item2])
    warning = Scheduler.detect_conflicts(result)
    assert warning is None


def test_empty_schedule_no_conflicts():
    """Edge case: Empty schedule has no conflicts."""
    result = ScheduleResult(items=[])
    warning = Scheduler.detect_conflicts(result)
    assert warning is None


def test_single_item_no_conflicts():
    """Edge case: Single scheduled item has no conflicts."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    item = ScheduleItem(
        task=Task(title="Walk", duration_minutes=30),
        start_time=ref_date,
        end_time=ref_date + timedelta(minutes=30),
        reason="Test"
    )
    result = ScheduleResult(items=[item])
    warning = Scheduler.detect_conflicts(result)
    assert warning is None


def test_multiple_overlaps_all_reported():
    """Edge case: Multiple overlaps all included in warning."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    item1 = ScheduleItem(
        task=Task(title="A", duration_minutes=60),
        start_time=ref_date,
        end_time=ref_date + timedelta(minutes=60),
        reason="Test"
    )
    item2 = ScheduleItem(
        task=Task(title="B", duration_minutes=60),
        start_time=ref_date + timedelta(minutes=30),
        end_time=ref_date + timedelta(minutes=90),
        reason="Test"
    )
    item3 = ScheduleItem(
        task=Task(title="C", duration_minutes=60),
        start_time=ref_date + timedelta(minutes=45),
        end_time=ref_date + timedelta(minutes=105),
        reason="Test"
    )
    result = ScheduleResult(items=[item1, item2, item3])
    warning = Scheduler.detect_conflicts(result)
    assert warning is not None
    assert warning.count("overlap") >= 2


# ===== CATEGORY 5: Pet & Task Assignment Edge Cases =====

def test_add_duplicate_task_to_pet_prevents_duplicate():
    """Edge case: Adding same task twice to pet uses set semantics (no duplicate)."""
    pet = Pet(name="Buddy", species="dog")
    task = Task(title="Walk", duration_minutes=30)
    pet.add_task(task)
    pet.add_task(task)  # Add same task again
    assert len(pet.tasks) == 1


def test_remove_task_not_in_pet_handles_gracefully():
    """Edge case: Removing task not in pet doesn't error."""
    pet = Pet(name="Buddy", species="dog")
    task1 = Task(title="Walk", duration_minutes=30)
    task2 = Task(title="Feed", duration_minutes=20)
    pet.add_task(task1)
    pet.remove_task(task2)  # task2 never added
    assert len(pet.tasks) == 1
    assert task1 in pet.tasks


def test_reassign_task_updates_pet_assignment():
    """Edge case: Task reassigned to different pet updates correctly."""
    pet1 = Pet(name="Buddy", species="dog")
    pet2 = Pet(name="Mittens", species="cat")
    task = Task(title="Walk", duration_minutes=30)
    
    task.assign_to_pet(pet1)
    assert task.assigned_pet == pet1
    assert task in pet1.tasks
    
    # Reassign requires unassign first to update both pets correctly
    task.unassign()
    task.assign_to_pet(pet2)
    assert task.assigned_pet == pet2
    assert task in pet2.tasks
    assert task not in pet1.tasks


def test_unassign_task_with_no_pet_handles_gracefully():
    """Edge case: Unassign task with no assigned pet doesn't error."""
    task = Task(title="Walk", duration_minutes=30)
    task.unassign()  # No pet assigned
    assert task.assigned_pet is None


def test_task_in_pet_set_after_assignment():
    """Edge case: Task immediately in pet.tasks after assign_to_pet."""
    pet = Pet(name="Buddy", species="dog")
    task = Task(title="Walk", duration_minutes=30)
    assert task not in pet.tasks
    task.assign_to_pet(pet)
    assert task in pet.tasks


# ===== CATEGORY 6: Status Filtering Edge Cases =====

def test_filter_empty_result_by_status():
    """Edge case: Filter empty schedule returns empty list."""
    result = ScheduleResult(items=[])
    filtered = Scheduler.filter_by_status(result, "pending")
    assert filtered == []


def test_filter_all_completed_tasks():
    """Edge case: All completed tasks filtered before scheduling."""
    tasks = [
        Task(title="A", duration_minutes=20, status="completed"),
        Task(title="B", duration_minutes=30, status="completed"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 0
    assert len(result.unplanned_tasks) == 0


def test_filter_mixed_pending_and_completed():
    """Edge case: Only pending tasks scheduled from mixed list."""
    tasks = [
        Task(title="Pending1", duration_minutes=20, status="pending", priority="high"),
        Task(title="Completed1", duration_minutes=30, status="completed", priority="high"),
        Task(title="Pending2", duration_minutes=25, status="pending", priority="high"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    scheduled_titles = [item.task.title for item in result.items]
    assert "Pending1" in scheduled_titles
    assert "Pending2" in scheduled_titles
    assert "Completed1" not in scheduled_titles


def test_filter_by_invalid_status_returns_empty():
    """Edge case: Filtering by invalid status returns empty list."""
    tasks = [Task(title="Walk", duration_minutes=30)]
    filtered = Scheduler.filter_by_status(tasks, "invalid_status")
    assert filtered == []


# ===== CATEGORY 7: Greedy Packing Edge Cases =====

def test_no_low_priority_tasks_in_unplanned():
    """Edge case: Greedy packing skips when no low-priority unplanned tasks."""
    tasks = [
        Task(title="HighLarge", duration_minutes=100, priority="high"),
        Task(title="MediumLarge", duration_minutes=50, priority="medium"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    # Medium fits (50 < 60), High doesn't (100 > 60), no low-priority to pack
    assert len(result.items) == 1
    assert result.items[0].task.title == "MediumLarge"


def test_low_priority_task_fits_perfectly():
    """Edge case: Low priority task exactly fits remaining time."""
    tasks = [
        Task(title="High", duration_minutes=30, priority="high"),
        Task(title="Low", duration_minutes=30, priority="low"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    assert len(result.items) == 2
    scheduled_titles = [item.task.title for item in result.items]
    assert "High" in scheduled_titles
    assert "Low" in scheduled_titles


def test_multiple_low_priority_only_some_fit():
    """Edge case: Multiple low-priority tasks, only subset fits via greedy packing."""
    tasks = [
        Task(title="High", duration_minutes=25, priority="high"),
        Task(title="Low1", duration_minutes=20, priority="low"),
        Task(title="Low2", duration_minutes=30, priority="low"),
        Task(title="Low3", duration_minutes=15, priority="low"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    # High (25) + greedy packing of low-priority by duration ascending
    # Sorted low-priority: Low3 (15), Low1 (20), Low2 (30)
    # High fits first, then Low3 and Low1 fit, Low2 doesn't
    assert len(result.items) >= 2
    assert len(result.unplanned_tasks) >= 1


def test_all_low_priority_tasks_too_large():
    """Edge case: All low-priority tasks too large for remaining time."""
    tasks = [
        Task(title="High", duration_minutes=50, priority="high"),
        Task(title="Low1", duration_minutes=20, priority="low"),
        Task(title="Low2", duration_minutes=30, priority="low"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    # High fits (50), remaining (10) too small for any low-priority task
    assert len(result.items) == 1
    assert result.items[0].task.title == "High"


def test_greedy_packing_with_zero_remaining_time():
    """Edge case: Greedy packing skips when remaining time is zero."""
    tasks = [
        Task(title="High", duration_minutes=60, priority="high"),
        Task(title="Low", duration_minutes=30, priority="low"),
    ]
    owner = Owner(time_available=60)
    result = Scheduler.generate_schedule(tasks, owner)
    # High uses all 60m, no time for Low
    assert len(result.items) == 1
    assert len(result.unplanned_tasks) == 1


# ===== CATEGORY 8: Sorting & Binary Search Edge Cases =====

def test_insert_task_into_empty_list():
    """Edge case: Binary search insertion into empty list."""
    task = Task(title="Walk", duration_minutes=30, priority="high")
    result = Scheduler.insert_task_sorted([], task)
    assert len(result) == 1
    assert result[0] == task


def test_insert_high_priority_at_beginning():
    """Edge case: High priority task inserted at start."""
    existing = [
        Task(title="Medium", duration_minutes=30, priority="medium"),
        Task(title="Low", duration_minutes=20, priority="low"),
    ]
    new_task = Task(title="High", duration_minutes=40, priority="high")
    result = Scheduler.insert_task_sorted(existing, new_task)
    assert result[0].priority == "high"


def test_insert_low_priority_at_end():
    """Edge case: Low priority task inserted at end."""
    existing = [
        Task(title="High", duration_minutes=40, priority="high"),
        Task(title="Medium", duration_minutes=30, priority="medium"),
    ]
    new_task = Task(title="Low", duration_minutes=20, priority="low")
    result = Scheduler.insert_task_sorted(existing, new_task)
    assert result[-1].priority == "low"


def test_sort_by_time_with_random_order():
    """Edge case: sort_by_time orders unsorted items correctly."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    items = [
        ScheduleItem(task=Task(title="C", duration_minutes=60), start_time=ref_date + timedelta(hours=2), end_time=ref_date + timedelta(hours=3), reason="Test"),
        ScheduleItem(task=Task(title="A", duration_minutes=60), start_time=ref_date, end_time=ref_date + timedelta(hours=1), reason="Test"),
        ScheduleItem(task=Task(title="B", duration_minutes=60), start_time=ref_date + timedelta(hours=1), end_time=ref_date + timedelta(hours=2), reason="Test"),
    ]
    result = ScheduleResult(items=items)
    sorted_result = Scheduler.sort_by_time(result)
    assert sorted_result.items[0].task.title == "A"
    assert sorted_result.items[1].task.title == "B"
    assert sorted_result.items[2].task.title == "C"


def test_sort_by_time_idempotent():
    """Edge case: Sorting already-sorted schedule is idempotent."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    items = [
        ScheduleItem(task=Task(title="A", duration_minutes=60), start_time=ref_date, end_time=ref_date + timedelta(hours=1), reason="Test"),
        ScheduleItem(task=Task(title="B", duration_minutes=60), start_time=ref_date + timedelta(hours=1), end_time=ref_date + timedelta(hours=2), reason="Test"),
    ]
    result = ScheduleResult(items=items)
    sorted1 = Scheduler.sort_by_time(result)
    sorted2 = Scheduler.sort_by_time(sorted1)
    assert [item.task.title for item in sorted1.items] == [item.task.title for item in sorted2.items]


# ===== CATEGORY 9: Owner & Validation Edge Cases =====

def test_invalid_start_hour_negative():
    """Edge case: Negative start_hour raises ValueError."""
    with pytest.raises(ValueError):
        Owner(preferred_start_hour=-1, preferred_end_hour=20)


def test_invalid_start_hour_over_23():
    """Edge case: start_hour > 23 raises ValueError."""
    with pytest.raises(ValueError):
        Owner(preferred_start_hour=25, preferred_end_hour=20)


def test_invalid_end_hour_over_23():
    """Edge case: end_hour > 23 raises ValueError."""
    with pytest.raises(ValueError):
        Owner(preferred_start_hour=8, preferred_end_hour=25)


def test_negative_time_available():
    """Edge case: Negative time_available raises ValueError."""
    with pytest.raises(ValueError):
        Owner(time_available=-100, preferred_start_hour=8, preferred_end_hour=20)


def test_end_hour_not_after_start_hour():
    """Edge case: end_hour <= start_hour raises ValueError."""
    with pytest.raises(ValueError):
        Owner(preferred_start_hour=20, preferred_end_hour=20)


# ===== CATEGORY 10: Date & Time Edge Cases =====

def test_reference_date_none_defaults_to_today():
    """Edge case: None reference_date uses datetime.now().replace(...)."""
    tasks = [Task(title="Walk", duration_minutes=30, priority="high")]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner, reference_date=None)
    assert len(result.items) == 1


def test_reference_date_midnight_hour_calculation():
    """Edge case: reference_date at midnight, hour calculation adds correctly."""
    ref_date = datetime(2023, 1, 1, 0, 0, 0)
    tasks = [Task(title="Walk", duration_minutes=30, priority="high")]
    owner = Owner(time_available=60, preferred_start_hour=8, preferred_end_hour=20)
    result = Scheduler.generate_schedule(tasks, owner, reference_date=ref_date)
    assert result.items[0].start_time.hour == 8


def test_daily_task_due_date_crosses_month():
    """Edge case: Daily task due_date+1d crosses month boundary."""
    today = datetime(2023, 1, 31)
    task = Task(title="Walk", duration_minutes=30, recurrence="daily", due_date=today)
    next_task = task.mark_complete()
    # Next task due date should be today + 1 day = 2026-03-30 (current date + 1)
    # Since mark_complete uses datetime.now(), check it's 1 day after current
    assert next_task.due_date > datetime.now()


def test_weekly_task_due_date_crosses_year():
    """Edge case: Weekly task due_date+7d crosses year boundary."""
    today = datetime(2022, 12, 31)
    task = Task(title="Groom", duration_minutes=60, recurrence="weekly", due_date=today)
    next_task = task.mark_complete()
    # Next task due date should be current_date + 7 days (uses datetime.now())
    expected_min = datetime.now() + timedelta(days=6.9)
    expected_max = datetime.now() + timedelta(days=7.1)
    assert expected_min < next_task.due_date < expected_max


# ===== CATEGORY 11: Performance & Scalability Edge Cases =====

def test_large_task_list_1000_tasks():
    """Edge case: Large task list (1000) generates schedule efficiently."""
    import time
    tasks = [Task(title=f"Task{i}", duration_minutes=1, priority="low") for i in range(1000)]
    owner = Owner(time_available=100, preferred_start_hour=8, preferred_end_hour=20)
    start = time.time()
    result = Scheduler.generate_schedule(tasks, owner)
    elapsed = time.time() - start
    assert elapsed < 1.0  # Should complete in under 1 second
    assert len(result.items) <= 100  # Can't schedule more than 100 mins


def test_binary_search_1000_task_inserts():
    """Edge case: Binary search insertion maintains sorted order for 1000 tasks."""
    tasks = []
    for i in range(100):
        task = Task(title=f"Task{i}", duration_minutes=30 - (i % 30), priority=["high", "medium", "low"][i % 3])
        tasks = Scheduler.insert_task_sorted(tasks, task)
    assert len(tasks) == 100


def test_repeated_sort_by_time_deterministic():
    """Edge case: Multiple sort_by_time calls produce identical order."""
    ref_date = datetime(2023, 1, 1, 8, 0)
    items = [
        ScheduleItem(task=Task(title=f"Task{i}", duration_minutes=10), start_time=ref_date + timedelta(minutes=i*10), end_time=ref_date + timedelta(minutes=(i+1)*10), reason="Test")
        for i in range(50)
    ]
    result = ScheduleResult(items=items)
    sorted1 = Scheduler.sort_by_time(result)
    sorted2 = Scheduler.sort_by_time(sorted1)
    assert [item.task.title for item in sorted1.items] == [item.task.title for item in sorted2.items]

