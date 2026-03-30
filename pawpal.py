from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str = "medium"
    assigned_pet: Optional["Pet"] = None
    status: str = "pending"

    def assign_to_pet(self, pet: "Pet"):
        """Assign this task to a specific pet.
        
        Sets the assigned_pet attribute and adds this task to the pet's tasks list
        if it's not already there.
        
        Args:
            pet: The Pet instance to assign this task to.
        """
        self.assigned_pet = pet
        if self not in pet.tasks:
            pet.tasks.append(self)

    def unassign(self):
        """Remove this task from its currently assigned pet.
        
        Clears the assigned_pet attribute and removes this task from the pet's
        tasks list if it exists there.
        """
        if self.assigned_pet:
            owner_pet = self.assigned_pet
            if self in owner_pet.tasks:
                owner_pet.tasks.remove(self)
            self.assigned_pet = None

    def mark_complete(self):
        """Mark this task as completed.
        
        Changes the task's status from 'pending' to 'completed'.
        """
        self.status = "completed"

    def __post_init__(self):
        """Validate task attributes after initialization.
        
        Raises:
            ValueError: If priority is not 'high', 'medium', or 'low', or if
                       duration_minutes is not positive.
        """
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(f"Invalid priority: {self.priority}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be > 0")

@dataclass
class Pet:
    name: str
    species: str = "dog"
    age: Optional[float] = None  # years
    owner: Optional[Owner] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to this pet's task list.
        
        Sets the task's assigned_pet to this pet and appends it to the tasks list.
        
        Args:
            task: The Task instance to add to this pet.
        """
        task.assigned_pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from this pet's task list.
        
        Removes the task from the tasks list and clears its assigned_pet attribute
        if the task is currently assigned to this pet.
        
        Args:
            task: The Task instance to remove from this pet.
        """
        if task in self.tasks:
            self.tasks.remove(task)
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
        """Generate a daily schedule for pet care tasks.
        
        Sorts tasks by priority (high first), then by duration (longer first),
        and schedules them sequentially within the owner's available time window.
        Tasks that don't fit are marked as unplanned.
        
        Args:
            tasks: List of Task instances to schedule.
            owner: Owner instance with time constraints and preferences.
            reference_date: Date to use for scheduling (defaults to today).
            
        Returns:
            ScheduleResult containing scheduled items and unplanned tasks.
            
        Raises:
            ValueError: If no available scheduling window exists.
        """
        if reference_date is None:
            reference_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        available_minutes = min(owner.time_available, (owner.preferred_end_hour - owner.preferred_start_hour) * 60)
        if available_minutes <= 0:
            raise ValueError("No available scheduling window")

        sorted_tasks = sorted(
            tasks,
            key=lambda t: (PRIORITY_ORDER[t.priority], -t.duration_minutes, t.title),
        )

        scheduled_items: List[ScheduleItem] = []
        unplanned: List[Task] = []

        current_start = reference_date + timedelta(hours=owner.preferred_start_hour)
        current_time = current_start
        used_minutes = 0

        for task in sorted_tasks:
            if used_minutes + task.duration_minutes > available_minutes:
                unplanned.append(task)
                continue

            # schedule task at current_time
            end_time = current_time + timedelta(minutes=task.duration_minutes)
            reason_components: List[str] = []
            reason_components.append(f"High-priority" if task.priority == "high" else f"{task.priority.capitalize()} priority")
            reason_components.append(f"fits remaining time ({available_minutes - used_minutes}m left)")
            if task.duration_minutes >= 60:
                reason_components.append("long task scheduled early to preserve flexibility")
            reason = ", ".join(reason_components)

            scheduled_items.append(
                ScheduleItem(task=task, start_time=current_time, end_time=end_time, reason=reason)
            )

            used_minutes += task.duration_minutes
            current_time = end_time

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
