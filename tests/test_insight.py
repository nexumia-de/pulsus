"""Streaks, records and the last seven days in words."""
from datetime import date, datetime, timedelta

from pulsus import insight
from pulsus.data.records import Workout

TODAY = date(2026, 3, 20)


def back(n):
    return TODAY - timedelta(days=n)


def test_streak_counts_days_in_a_row_at_the_goal():
    # Reached on the last 3 days before today, missed 4 days ago, a run
    # of 5 before that; today is still short.
    steps = {back(0): 2000, back(1): 9000, back(2): 8000, back(3): 12000,
             back(4): 7999, **{back(n): 10000 for n in range(5, 10)}}
    found = insight.streaks(steps, 8000, TODAY)
    assert found.current == 3
    assert (found.longest, found.longest_end) == (5, back(5))
    # Today reached: it counts.
    steps[back(0)] = 8000
    assert insight.streaks(steps, 8000, TODAY).current == 4
    # A day without data breaks the streak.
    del steps[back(2)]
    assert insight.streaks(steps, 8000, TODAY).current == 2
    assert insight.streaks({}, 8000, TODAY) == insight.Streaks(0, 0, None)


def test_current_streak_reads_back_only_as_far_as_it_reaches():
    steps = {back(n): 9000 for n in range(0, 100)}
    asked = []

    def fetch(first, last):
        asked.append((first, last))
        return {d: v for d, v in steps.items() if first <= d <= last}
    assert insight.current_streak(fetch, 8000, TODAY, chunk=35) == 100
    assert len(asked) == 3          # three windows of 35 days cover it
    asked.clear()
    steps[back(3)] = 0
    assert insight.current_streak(fetch, 8000, TODAY, chunk=35) == 3
    assert len(asked) == 1


def workout(wid, day, minutes, metres=None, pace=None, kind=0x10):
    start = datetime.combine(day, datetime.min.time()) + timedelta(hours=18)
    meta = {"workoutDuration": (str(minutes * 60), "seconds")}
    if metres:
        meta["distanceMeters"] = (str(metres), "meters")
    if pace:
        meta["paceAvg"] = (str(pace), "min_km")
    return Workout(wid, kind, "Running-x", start, start + timedelta(minutes=minutes),
                   False, meta)


def test_records_are_the_users_own_bests():
    steps = {back(3): 15321, back(2): 9000}
    workouts = [workout(1, back(9), 30, 5000, 6.0), workout(2, back(5), 75),
                workout(3, back(2), 50, 9000, 5.5),
                # Too short for a pace record.
                workout(4, back(1), 3, 600, 4.0)]
    found = {r.title: r for r in insight.records(steps, workouts, lambda w: "Running")}
    assert found["Most Steps in a Day"].value == "15,321 steps"
    assert found["Most Steps in a Day"].when == back(3)
    assert found["Longest Workout"].workout_id == 2
    assert found["Longest Workout"].value == "1 h 15 min"
    assert found["Longest Workout"].kind == "Running"
    assert found["Longest Distance"].value == "9.00 km"
    assert found["Fastest Average Pace"].workout_id == 3
    assert found["Fastest Average Pace"].value == "5:30 min/km"
    assert insight.records({}, []) == []


def test_week_compares_with_the_four_weeks_before_without_judging():
    steps = {back(n): 11000 if n < 7 else 10000 for n in range(35)}
    sleep = {back(n): 7.0 for n in range(35)}
    resting = {back(n): 55.0 for n in range(5)}        # too little before
    workouts = [workout(1, back(1), 40), workout(2, back(3), 20),
                workout(3, back(10), 30), workout(4, back(20), 30)]
    lines = {line.title: line for line in insight.week(steps, sleep, resting,
                                                      workouts, TODAY)}
    assert lines["Steps"].value == "11,000"
    assert lines["Steps"].note == "A day on average, 10% more than in the 4 weeks before."
    assert lines["Sleep"].value == "7 h"
    assert lines["Sleep"].note == \
        "A night on average, about the same as in the 4 weeks before."
    assert lines["Resting Heart Rate"].note == "On average over 5 days."
    assert lines["Workouts"].value == "2 · 1 h"
    assert lines["Workouts"].note == "0.5 a week in the 4 weeks before."
    for line in lines.values():
        assert not any(word in line.note.lower() for word in ("good", "bad", "should"))
    assert insight.week({}, {}, {}, [], TODAY) == []
