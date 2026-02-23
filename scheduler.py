import random
from collections import defaultdict

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def generate_timetable(classes, subjects, faculty_limits):
    print(">>> NEW BALANCE SCHEDULER RUNNING")
    # Store timetable for ALL classes (critical)
    all_timetables = {}

    # Global faculty schedule (prevents clashes across classes)
    faculty_schedule = defaultdict(lambda: defaultdict(set))

    for cls in classes:
        class_id = cls["id"]
        class_name = cls["name"]
        periods = cls["periods_per_day"]
        working_days = DAYS[:cls["working_days"]]
        break_after = cls["break_after"]

        # Filter subjects for this class only
        class_subjects = [s for s in subjects if s["class_id"] == class_id]

        # Initialize empty timetable
        timetable = {day: ["Free"] * periods for day in working_days}

        # Insert fixed BREAK slot
        if break_after is not None and break_after < periods:
            for day in working_days:
                timetable[day][break_after] = "BREAK"

        # Track faculty daily workload (per class)
        faculty_daily_load = defaultdict(lambda: defaultdict(int))

        # ===================== LAB ALLOCATION (CONTINUOUS & REALISTIC) =====================
        for sub in class_subjects:
            if sub["is_lab"]:
                subject_name = sub["name"]
                faculty_id = sub["faculty_id"]
                duration = sub["lab_duration"] if sub["lab_duration"] else 1
                weekly_periods = sub["periods_per_week"]

                sessions_needed = max(1, weekly_periods // duration)
                sessions_allocated = 0

                days_shuffled = working_days[:]
                random.shuffle(days_shuffled)

                for day in days_shuffled:
                    if sessions_allocated >= sessions_needed:
                        break

                    possible_starts = list(range(periods - duration + 1))
                    random.shuffle(possible_starts)

                    for start in possible_starts:
                        valid = True

                        for j in range(duration):
                            slot = start + j

                            if timetable[day][slot] != "Free":
                                valid = False
                                break

                            if timetable[day][slot] == "BREAK":
                                valid = False
                                break

                            if slot in faculty_schedule[faculty_id][day]:
                                valid = False
                                break

                            if faculty_daily_load[faculty_id][day] >= faculty_limits.get(faculty_id, 4):
                                valid = False
                                break

                        if valid:
                            for j in range(duration):
                                slot = start + j
                                timetable[day][slot] = subject_name + " (Lab)"
                                faculty_daily_load[faculty_id][day] += 1
                                faculty_schedule[faculty_id][day].add(slot)

                            sessions_allocated += 1
                            break

        # ===================== THEORY ALLOCATION (EVEN + RANDOM DISTRIBUTION) =====================
        for sub in class_subjects:
            if not sub["is_lab"]:
                subject_name = sub["name"]
                faculty_id = sub["faculty_id"]
                total_needed = sub["periods_per_week"]

                allocations_done = 0
                attempts = 0
                max_attempts = 6000
                daily_limit = 2  # prevent same subject spam per day

                # Shuffle days for better weekly spread
                days_cycle = working_days[:]
                random.shuffle(days_cycle)

                while allocations_done < total_needed and attempts < max_attempts:
                    for day in days_cycle:
                        if allocations_done >= total_needed:
                            break

                        # Randomize slot order (fix same-period issue)
                        slots = list(range(periods))
                        random.shuffle(slots)

                        for slot in slots:
                            if timetable[day][slot] != "Free":
                                continue

                            if timetable[day][slot] == "BREAK":
                                continue

                            if timetable[day].count(subject_name) >= daily_limit:
                                continue

                            if slot in faculty_schedule[faculty_id][day]:
                                continue

                            if faculty_daily_load[faculty_id][day] >= faculty_limits.get(faculty_id, 4):
                                continue

                            timetable[day][slot] = subject_name
                            faculty_daily_load[faculty_id][day] += 1
                            faculty_schedule[faculty_id][day].add(slot)

                            allocations_done += 1
                            break

                    attempts += 1

               # ===================== BALANCED BACKFILL (ACADEMIC REALISM) =====================
        max_daily_teaching = periods - 2  # prevents 6/7 period overload

        remaining_subjects = []
        for sub in class_subjects:
            if not sub["is_lab"]:
                assigned = sum(row.count(sub["name"]) for row in timetable.values())
                remaining = sub["periods_per_week"] - assigned
                if remaining > 0:
                    remaining_subjects.extend([sub] * remaining)

        random.shuffle(remaining_subjects)

        for day in working_days:
            # Count current teaching load (excluding BREAK & Free)
            current_teaching = sum(
                1 for p in timetable[day] if p not in ["Free", "BREAK"]
            )

            # Skip if day already heavily loaded
            if current_teaching >= max_daily_teaching:
                continue

            for slot in range(periods):
                if timetable[day][slot] != "Free":
                    continue

                # Recalculate teaching load dynamically
                current_teaching = sum(
                    1 for p in timetable[day] if p not in ["Free", "BREAK"]
                )

                if current_teaching >= max_daily_teaching:
                    break  # stop filling this day

                for sub in remaining_subjects:
                    faculty_id = sub["faculty_id"]
                    subject_name = sub["name"]

                    # Faculty clash check
                    if slot in faculty_schedule[faculty_id][day]:
                        continue

                    # Faculty daily limit
                    if faculty_daily_load[faculty_id][day] >= faculty_limits.get(faculty_id, 4):
                        continue

                    timetable[day][slot] = subject_name
                    faculty_daily_load[faculty_id][day] += 1
                    faculty_schedule[faculty_id][day].add(slot)
                    remaining_subjects.remove(sub)
                    break

        # ===================== FINAL BALANCE (REALISTIC DISTRIBUTION) =====================
        for day in working_days:
            subject_count = {}
            for i, p in enumerate(timetable[day]):
                if p not in ["Free", "BREAK"]:
                    subject_count[p] = subject_count.get(p, 0) + 1

            for subject, count in subject_count.items():
                if count > 3:  # too many same subject in one day
                    excess = count - 3
                    for i in range(len(timetable[day])):
                        if timetable[day][i] == subject and excess > 0:
                            timetable[day][i] = "Free"
                            excess -= 1

        # 🔥 MOST IMPORTANT: Store timetable per class (fixes single class bug)
        all_timetables[class_name] = timetable

    # 🔥 MUST return all classes, not single timetable
    return all_timetables