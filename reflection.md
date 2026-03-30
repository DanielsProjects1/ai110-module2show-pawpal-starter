# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My UML diagram has6 classes in total. A pet class, owner, class, task class, ScheduleItem class, Scheduler class, and a ScheduleResult class. The Owner class owns a list of Pets, and the ScheduleItem class uses a Task and is then contained in the ScheduleResult class as part of a list of ScheduleItems. The Scheduler class generates a schedule for an owner based on tasks and the owners preferences.

- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?

Yes.

- If yes, describe at least one change and why you made it.

When I asked Copilot if it noticed any missing relationships or potential logic bottlenecks in pawpal_system.py, it pointed out that there was no association between a task and a pet in my skeleton. It also pointed out that although the Owner class had a list of pets to show which pets an owner had, there was no bidirectional relationship. So I asked Copilot to fix these things for me as well as remove the unnecessary Task.category attribute as well.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

Time was the constraint considered most in my Scheduler class.

- How did you decide which constraints mattered most?

I decided time mattered the most because to the user, that is probably the most important thing.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

Caches available_minutes calculation.

- Why is that tradeoff reasonable for this scenario?

Pne place to change if time logic evolves.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Copilot to help me design, code and refactor the project.

- What kinds of prompts or questions were most helpful?

The most useful prompts were me just telling it what I wanted it to do.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The AI wanted to remove the filter_by_status method in the Scheduler task for the detect_conflict method. I rejected this because the instruction for the project wanted me to keep the method.

- How did you evaluate or verify what the AI suggested?

By testing its suggestions before keeping them.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

I tested the programs sorting behavior, recurrence logic, conflict detection, edge date handling, and greedy packing.

- Why were these tests important?

Because I used these tests to verify that the code the AI gave me works and will not crash the app when it's run.

**b. Confidence**

- How confident are you that your scheduler works correctly?

4 out of 5

- What edge cases would you test next if you had more time?

Duplicate pet names: Multiple pets with same name - should use unique IDs for hashing.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

Most of the code and suggestion Copilot gave me were helpful.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would redesign the app so that the user can see schedules for each individual pet that they own.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

When designing systems with AI, it is much easier when you already have a clear idea of what your app looks like and you're at least familiar with how you want it to behave. The AI can give you suggestions along the way that you can either choose to implement or disregard.
