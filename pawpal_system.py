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
    category: Optional[str] = None

@dataclass
class Pet:
    name: str
    species: str = "dog"
    age: Optional[float] = None  # years

@dataclass
class Owner:
    time_available: int = 180  # minutes per day
    preferred_start_hour: int = 8
    preferred_end_hour: int = 20
    pets: List[Pet] = field(default_factory=list)

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
        pass

    def explanation(self) -> str:
        pass

class Scheduler:
    @staticmethod
    def generate_schedule(
        tasks: List[Task],
        owner: Owner,
        reference_date: Optional[datetime] = None,
    ) -> ScheduleResult:
        pass

    @staticmethod
    def get_summary(result: ScheduleResult) -> str:
        pass
# </content>
# <parameter name="filePath">c:\Users\danie\OneDrive\Desktop\CodePath AI assignments\ai110-module2show-pawpal-starter\pawpal_system.py