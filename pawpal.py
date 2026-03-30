from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import bisect

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

@dataclass(eq=False)
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    assigned_pet: Optional["Pet"] = None
    status: str = "pending"
    recurrence: str = "none"  # "none", "daily", "weekly"
    due_date: Optional[datetime] = None

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

    def assign_to_pet(self, pet: "Pet"):
        """Assign this task to a specific pet.
        
        Sets the assigned_pet attribute and adds this task to the pet's tasks set
        if it's not already there.
        
        Args:
            pet: The Pet instance to assign this task to.
        """
        self.assigned_pet = pet
        pet.tasks.add(self)

    def unassign(self):
        """Remove this task from its currently assigned pet.
        
        Clears the assigned_pet attribute and removes this task from the pet's
        tasks set if it exists there.
        """
        if self.assigned_pet:
            owner_pet = self.assigned_pet
            owner_pet.tasks.discard(self)
            self.assigned_pet = None

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task as completed.
        
        Changes the task's status from 'pending' to 'completed'.
        If the task is recurring ('daily' or 'weekly'), creates a new
        instance for the next occurrence.
        
        Returns:
            A new Task instance if recurring, otherwise None.
        """
        self.status = "completed"
        if self.recurrence == "daily":
            new_due_date = datetime.now() + timedelta(days=1)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                assigned_pet=self.assigned_pet,
                recurrence=self.recurrence,
                due_date=new_due_date,
            )
        elif self.recurrence == "weekly":
            new_due_date = datetime.now() + timedelta(days=7)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                assigned_pet=self.assigned_pet,
                recurrence=self.recurrence,
                due_date=new_due_date,
            )
        return None

    def __post_init__(self):
        """Validate task attributes after initialization.
        
        Raises:
            ValueError: If priority is not 'high', 'medium', or 'low', if
                       duration_minutes is not positive, or if recurrence is
                       not 'none', 'daily', or 'weekly'.
        """
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"Invalid priority: {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be > 0")
        if self.recurrence not in ["none", "daily", "weekly"]:
            raise ValueError("recurrence must be 'none', 'daily', or 'weekly'")

@dataclass
class Pet:
    name: str
    species: str = "dog"
    age: Optional[float] = None  # years
    owner: Optional[Owner] = None
    tasks: set[Task] = field(default_factory=set)

    def add_task(self, task: Task):
        """Add a task to this pet's task set.
        
        Sets the task's assigned_pet to this pet and adds it to the tasks set.
        
        Args:
            task: The Task instance to add to this pet.
        """
        task.assigned_pet = self
        self.tasks.add(task)

    def remove_task(self, task: Task):
        """Remove a task from this pet's task set.
        
        Removes the task from the tasks set and clears its assigned_pet attribute
        if the task is currently assigned to this pet.
        
        Args:
            task: The Task instance to remove from this pet.
        """
        if task in self.tasks:
            self.tasks.discard(task)
            task.assigned_pet = None

@dataclass
class Owner:
    time_available: int = 180  # minutes per day
    preferred_start_hour: int = 8
    preferred_end_hour: int = 20
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's pet list.
        
        Adds the pet to the pets list and sets the pet's owner to this owner
        if the pet is not already in the list.
        
        Args:
            pet: The Pet instance to add to this owner.
        """
        if pet not in self.pets:
            self.pets.append(pet)
            pet.owner = self

    def remove_pet(self, pet: Pet):
        """Remove a pet from this owner's pet list.
        
        Removes the pet from the pets list and clears the pet's owner attribute
        if the pet is currently owned by this owner.
        
        Args:
            pet: The Pet instance to remove from this owner.
        """
        if pet in self.pets:
            self.pets.remove(pet)
            pet.owner = None

    def __post_init__(self):
        """Validate owner attributes after initialization.
        
        Raises:
            ValueError: If preferred_start_hour or preferred_end_hour are not
                       between 0-23, if preferred_end_hour is not after
                       preferred_start_hour, or if time_available is not positive.
        """
        if self.preferred_start_hour < 0 or self.preferred_start_hour > 23:
            raise ValueError("preferred_start_hour must be 0-23")
        if self.preferred_end_hour < 0 or self.preferred_end_hour > 23:
            raise ValueError("preferred_end_hour must be 0-23")
        if self.preferred_end_hour <= self.preferred_start_hour:
            raise ValueError("preferred_end_hour must be after preferred_start_hour")
        if self.time_available <= 0:
            raise ValueError("time_available must be > 0")

@dataclass
class ScheduleItem:
    task: Task
    start_time: datetime
    end_time: datetime
    reason: str

@dataclass
class ScheduleResult:
    items: List[ScheduleItem] = field(default_factory=list)
    unplanned_tasks: List[Task] = field(default_factory=list)

    @property
    def total_planned_minutes(self) -> int:
        """Calculate the total minutes of all planned tasks.
        
        Returns:
            The sum of duration_minutes for all tasks in the scheduled items.
        """
        return sum((item.task.duration_minutes for item in self.items))

    def explanation(self) -> str:
        """Generate a human-readable explanation of the schedule.
        
        Returns:
            A formatted string describing the scheduled tasks, their timing,
            reasons for scheduling, and any unplanned tasks.
        """
        lines: List[str] = []
        if not self.items:
            lines.append("No tasks could be scheduled.")
            detail = "" if not self.unplanned_tasks else " Tasks were left unscheduled due to time constraints."
            lines.append(detail)
            return "\n".join(lines)

        lines.append("Daily plan explanation:")
        lines.append(f"Planned time window: {self.items[0].start_time.strftime('%H:%M')} - {self.items[-1].end_time.strftime('%H:%M')}")
        lines.append(f"Total planned minutes: {self.total_planned_minutes}")
        lines.append("")
        for item in self.items:
            t = item.task
            assigned = f" [pet: {t.assigned_pet.name}]" if t.assigned_pet else ""
            lines.append(
                f"- {t.title} ({t.priority}, {t.duration_minutes}m) from {item.start_time.strftime('%H:%M')} to {item.end_time.strftime('%H:%M')} - {item.reason}{assigned}"
            )

        if self.unplanned_tasks:
            lines.append("")
            lines.append("Unplanned tasks due to limited time:")
            for t in self.unplanned_tasks:
                lines.append(f"- {t.title} ({t.priority}, {t.duration_minutes}m)")

        return "\n".join(lines)

class Scheduler:
    @staticmethod
    def generate_schedule(
        tasks: List[Task],
        owner: Owner,
        reference_date: Optional[datetime] = None,
    ) -> ScheduleResult:
        """Generate a daily schedule for pet care tasks with greedy packing optimization.
        
        Algorithm Overview:
        1. Filter tasks to include only pending tasks (status='pending').
        2. Sort tasks by priority (high→medium→low), then by duration (longest first),
           then alphabetically by title.
        3. Schedule high/medium priority tasks sequentially within the time window,
           skipping any that don't fit.
        4. Use greedy packing optimization: After high/medium tasks are scheduled,
           attempt to fit low-priority tasks (sorted by duration ascending) into
           remaining time slots.
        
        Greedy Packing Details:
        - If time remains after priority scheduling, collect all unplanned low-priority tasks
        - Sort them by duration (ascending) to maximize "first-fit" probability
        - Attempt to insert each into the remaining time window
        - Remove successfully scheduled tasks from the unplanned list
        
        Time Complexity: O(n log n) for initial sort, O(m) for greedy packing where m = low-priority tasks
        Space Complexity: O(n) for scheduled items and unplanned list
        
        Args:
            tasks: List of Task instances to schedule.
            owner: Owner instance with time_available and preferred_start_hour/end_hour constraints.
            reference_date: Date to use for scheduling (defaults to today at 00:00:00).
            
        Returns:
            ScheduleResult containing:
            - items: List of ScheduleItem objects representing scheduled tasks
            - unplanned_tasks: List of Task objects that could not be scheduled
            
        Raises:
            ValueError: If no valid scheduling window exists (available_minutes <= 0).
        """
        if reference_date is None:
            reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Cache available_minutes calculation for clarity and efficiency
        window_hours = owner.preferred_end_hour - owner.preferred_start_hour
        available_minutes = min(owner.time_available, window_hours * 60)
        if available_minutes <= 0:
            raise ValueError("No available scheduling window")

        # Filter tasks to only include pending tasks
        pending_tasks = Scheduler.filter_by_status(tasks, "pending")

        sorted_tasks = sorted(
            pending_tasks,
            key=lambda t: (PRIORITY_ORDER[t.priority], -t.duration_minutes, t.title),
        )

        scheduled_items: List[ScheduleItem] = []
        unplanned: List[Task] = []

        current_start = reference_date + timedelta(hours=owner.preferred_start_hour)
        current_time = current_start
        used_minutes = 0

        # Phase 1: Schedule high and medium priority tasks
        for task in sorted_tasks:
            remaining = available_minutes - used_minutes
            if remaining <= 0:
                # No time left, add all remaining tasks to unplanned
                unplanned.extend(sorted_tasks[sorted_tasks.index(task):])
                break

            if task.duration_minutes > remaining:
                unplanned.append(task)
                continue

            # schedule task at current_time
            end_time = current_time + timedelta(minutes=task.duration_minutes)
            reason_components: List[str] = []
            reason_components.append(f"High-priority" if task.priority == "high" else f"{task.priority.capitalize()} priority")
            reason_components.append(f"fits remaining time ({remaining}m left)")
            if task.duration_minutes >= 60:
                reason_components.append("long task scheduled early to preserve flexibility")
            reason = ", ".join(reason_components)

            scheduled_items.append(
                ScheduleItem(task=task, start_time=current_time, end_time=end_time, reason=reason)
            )

            used_minutes += task.duration_minutes
            current_time = end_time

        # Phase 2: Greedy packing optimization for low-priority tasks
        # Attempt to fit low-priority tasks into remaining time slots
        remaining = available_minutes - used_minutes
        if remaining > 0 and unplanned:
            low_priority_tasks = [t for t in unplanned if t.priority == "low"]
            # Sort by duration ascending (first-fit decreasing strategy)
            low_priority_tasks.sort(key=lambda t: t.duration_minutes)
            scheduled_set = set()
            for item in scheduled_items:
                scheduled_set.add(item.task)
            
            to_remove = []
            for task in low_priority_tasks:
                if task not in scheduled_set and task.duration_minutes <= remaining:
                    end_time = current_time + timedelta(minutes=task.duration_minutes)
                    scheduled_items.append(
                        ScheduleItem(
                            task=task,
                            start_time=current_time,
                            end_time=end_time,
                            reason=f"Low priority, fits remaining time ({remaining}m left)",
                        )
                    )
                    used_minutes += task.duration_minutes
                    current_time = end_time
                    remaining -= task.duration_minutes
                    to_remove.append(task)
            
            for task in to_remove:
                unplanned.remove(task)

        if unplanned and scheduled_items:
            # optionally, include note about why unscheduled tasks were dropped
            pass

        result = ScheduleResult(items=scheduled_items, unplanned_tasks=unplanned)
        return result

    @staticmethod
    def get_summary(result: ScheduleResult) -> str:
        """Get a summary of the schedule result.
        
        This is an alias for ScheduleResult.explanation().
        
        Args:
            result: The ScheduleResult to summarize.
            
        Returns:
            A formatted string describing the schedule.
        """
        return result.explanation()

    @staticmethod
    def sort_by_time(result: ScheduleResult) -> ScheduleResult:
        """Sort schedule items by their start time in HH:MM format.
        
        Sorts the items in the ScheduleResult object by their start time in 
        "HH:MM" format using a lambda function as the sorting key, and returns
        the modified ScheduleResult object.
        
        Args:
            result: The ScheduleResult containing items to sort.
            
        Returns:
            The ScheduleResult object with items sorted by start_time in HH:MM format.
        """
        result.items = sorted(result.items, key=lambda item: item.start_time.strftime('%H:%M'))
        return result

    @staticmethod
    def filter_by_status(tasks, status: str):
        """Filter tasks or scheduled items by status.

        Works with either a list of Task objects (returns matching Task list) or
        a ScheduleResult (returns ScheduleItem list with tasks matching the status).

        Args:
            tasks: List[Task] or ScheduleResult.
            status: The status to filter by (e.g., 'completed' or 'pending').

        Returns:
            A list of Task objects if input is tasks list, or ScheduleItem objects
            if input is ScheduleResult.
        """
        if hasattr(tasks, "items"):
            return [item for item in tasks.items if item.task.status == status]
        return [task for task in tasks if task.status == status]

    @staticmethod
    def detect_conflicts(result: ScheduleResult) -> Optional[str]:
        """Detect scheduling conflicts in the schedule result.
        
        Checks for overlapping tasks in the scheduled items. Returns a warning
        message if conflicts are found, otherwise returns None.
        
        Args:
            result: The ScheduleResult to check for conflicts.
            
        Returns:
            A warning message string if conflicts are detected, None otherwise.
        """
        items = sorted(result.items, key=lambda item: item.start_time)
        conflicts = []
        for i in range(len(items) - 1):
            current = items[i]
            next_item = items[i + 1]
            if current.end_time > next_item.start_time:
                conflicts.append(
                    f"Tasks '{current.task.title}' and '{next_item.task.title}' overlap "
                    f"(ends at {current.end_time.strftime('%H:%M')}, next starts at {next_item.start_time.strftime('%H:%M')})"
                )
        if conflicts:
            return "Warning: Scheduling conflicts detected:\n" + "\n".join(conflicts)
        return None

    @staticmethod
    def insert_task_sorted(sorted_tasks: List[Task], task: Task) -> List[Task]:
        """Insert a task into a sorted list using binary search.
        
        Uses binary search (bisect) to insert a task into a pre-sorted task list
        by priority and duration, maintaining O(log n) insertion time for
        efficient incremental scheduling updates.
        
        Args:
            sorted_tasks: A list of Task objects already sorted by priority and duration.
            task: The Task instance to insert.
            
        Returns:
            The updated sorted tasks list with the new task inserted.
        """
        sort_key = (PRIORITY_ORDER[task.priority], -task.duration_minutes, task.title)
        # Create tuples of (sort_key, task) for bisect comparison
        task_tuples = [(PRIORITY_ORDER[t.priority], -t.duration_minutes, t.title, i, t) for i, t in enumerate(sorted_tasks)]
        bisect.insort(task_tuples, (sort_key[0], sort_key[1], sort_key[2], len(task_tuples), task))
        return [t[-1] for t in task_tuples]
