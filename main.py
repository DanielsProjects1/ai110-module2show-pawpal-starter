from pawpal import Owner, Pet, Scheduler, Task


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

print(Scheduler.get_summary(schedule1))