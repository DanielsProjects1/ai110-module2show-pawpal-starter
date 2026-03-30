from datetime import datetime, timedelta
from pawpal import Owner, Pet, Scheduler, Task, ScheduleItem, ScheduleResult


owner1 = Owner(time_available=120, preferred_start_hour=8, preferred_end_hour=20)
pet1 = Pet(name="Buddy", species="dog", owner=owner1)
pet2 = Pet(name="Mittens", species="cat", owner=owner1)

owner1.add_pet(pet1)
owner1.add_pet(pet2)

task1 = Task(title="Morning walk", duration_minutes=30, priority="high", assigned_pet=pet1)
task2 = Task(title="Feed", duration_minutes=20, priority="medium", assigned_pet=pet1)
task3 = Task(title="Playtime", duration_minutes=45, priority="low", assigned_pet=pet2)
task4 = Task(title="Grooming", duration_minutes=60, priority="medium", assigned_pet=pet1)
task5 = Task(title="Vet visit", duration_minutes=90, priority="high", assigned_pet=pet2)
task6 = Task(title="Training", duration_minutes=30, priority="medium", assigned_pet=pet1)

pet1.add_task(task1)
pet1.add_task(task2)    
pet2.add_task(task3)    
pet1.add_task(task4) 
pet2.add_task(task5)
pet2.add_task(task6)   

schedule1 = Scheduler.generate_schedule(
    tasks=[task1, task2, task3, task4, task5, task6],
    owner=owner1)
Scheduler.sort_by_time(schedule1)
for item in schedule1.items:
    print(f"{item.task.title} for {item.task.assigned_pet.name} at {item.start_time.strftime('%H:%M')}")
print(Scheduler.get_summary(schedule1))

# Conflict detection test: two tasks intentionally overlap
conflict_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
conflict_items = [
    ScheduleItem(task=task2, start_time=conflict_start, end_time=conflict_start + timedelta(minutes=30), reason="Manual conflict #1"),
    ScheduleItem(task=task3, start_time=conflict_start + timedelta(minutes=15), end_time=conflict_start + timedelta(minutes=60), reason="Manual conflict #2"),
]
conflict_schedule = ScheduleResult(items=conflict_items)
conflict_warning = Scheduler.detect_conflicts(conflict_schedule)
if conflict_warning:
    print("\nConflict warning detected:")
    print(conflict_warning)
else:
    print("\nNo conflicts detected.")