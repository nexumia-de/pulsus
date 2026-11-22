"""Beyond single days: step-goal streaks, personal records and the last
seven days against the four weeks before, in plain words and without
judgement (docs/visualisation.md#summary). No GTK."""
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import fmean

from pulsus import stats, text

RECENT_DAYS = 7
EARLIER_DAYS = 28
# A pace record needs a workout of at least this many metres.
PACE_MIN_METRES = 1000


@dataclass
class Streaks:
    current: int                 # days in a row at the goal, up to today
    longest: int
    longest_end: date | None     # last day of the longest streak


def streaks(daily_steps, goal, today):
    """Days in a row with at least `goal` steps. Today counts once it has
    reached the goal and does not break the streak before."""
    longest, longest_end, run = 0, None, 0
    if daily_steps:
        day = min(daily_steps)
        while day <= today:
            run = run + 1 if daily_steps.get(day, 0) >= goal else 0
            if run > longest:
                longest, longest_end = run, day
            day += timedelta(days=1)
    current = current_streak(lambda first, last: daily_steps, goal, today)
    return Streaks(current, longest, longest_end)


def current_streak(fetch, goal, today, chunk=35):
    """The streak up to `today`, reading only as far back as it reaches:
    `fetch(first, last)` gives date -> steps for those days (the Today
    page must not read the whole history)."""
    last = today
    steps = fetch(last - timedelta(days=chunk - 1), last)
    current = 0
    day = today if steps.get(today, 0) >= goal else today - timedelta(days=1)
    while True:
        if day < last - timedelta(days=chunk - 1):
            last = day
            steps = fetch(last - timedelta(days=chunk - 1), last)
            if not steps:
                break
        if steps.get(day, 0) < goal:
            break
        current += 1
        day -= timedelta(days=1)
    return current


@dataclass
class Record:
    title: str
    value: str
    when: date
    workout_id: int | None = None
    kind: str = ""               # of the workout, e.g. "Running"


def records(daily_steps, workouts, kind_name=lambda w: "Workout"):
    """The user's own bests in what Amazfish has stored."""
    found = []
    if daily_steps:
        day = max(daily_steps, key=daily_steps.get)
        if daily_steps[day] > 0:
            found.append(Record("Most Steps in a Day",
                                f"{text.number(daily_steps[day])} steps", day))
    if workouts:
        longest = max(workouts, key=lambda w: w.duration)
        found.append(Record("Longest Workout",
                            text.duration(longest.duration),
                            longest.start.date(), longest.id, kind_name(longest)))
        far = [w for w in workouts if w.number("distanceMeters")]
        if far:
            w = max(far, key=lambda w: w.number("distanceMeters"))
            found.append(Record(
                "Longest Distance",
                f"{w.number('distanceMeters') / 1000:.2f} km",
                w.start.date(), w.id, kind_name(w)))
        paced = [w for w in far if w.number("paceAvg")
                 and w.number("distanceMeters") >= PACE_MIN_METRES]
        if paced:
            w = min(paced, key=lambda w: w.number("paceAvg"))
            pace = w.number("paceAvg")
            found.append(Record(
                "Fastest Average Pace",
                f"{int(pace)}:{round(pace % 1 * 60):02d} min/km",
                w.start.date(), w.id, kind_name(w)))
    return found


def _split(daily, today):
    recent = [v for d, v in daily.items()
              if today - timedelta(days=RECENT_DAYS) < d <= today]
    earlier = [v for d, v in daily.items()
               if today - timedelta(days=RECENT_DAYS + EARLIER_DAYS) < d
               <= today - timedelta(days=RECENT_DAYS)]
    return recent, earlier


def _against(recent, earlier, more="higher", less="lower"):
    """'9 % higher than in the 4 weeks before', or '' without enough
    earlier days."""
    if len(earlier) < stats.BASELINE_MIN_DAYS:
        return ""
    change = stats.compare(recent, earlier)
    if change is None:
        return ""
    period = f"the {EARLIER_DAYS // 7} weeks before"
    if abs(change) < stats.SAME:
        return f"about the same as in {period}"
    return f"{abs(change):.0%} {more if change > 0 else less} than in {period}"


@dataclass
class Line:
    title: str
    value: str
    note: str = ""


def week(steps, sleep_hours, resting, workouts, today):
    """The seven days up to `today`, one Line per measure that has data:
    `steps`, `sleep_hours`, `resting` are date -> number. Callers pass
    the last complete day, so a day that has just begun does not pull
    the averages down."""
    lines = []
    for title, daily, show, per, words in (
            ("Steps", steps, text.number, "A day on average", ("more", "fewer")),
            ("Sleep", sleep_hours, text.duration_hours, "A night on average",
             ("more", "less")),
            ("Resting Heart Rate", resting, lambda v: f"{text.number(v)} bpm",
             "On average", ("higher", "lower"))):
        recent, earlier = _split(daily, today)
        if not recent:
            continue
        note = _against(recent, earlier, *words)
        lines.append(Line(title, show(fmean(recent)),
                          f"{per}, {note}." if note else
                          f"{per} over {len(recent)} "
                          f"{'day' if len(recent) == 1 else 'days'}."))
    start = today - timedelta(days=RECENT_DAYS)
    recent = [w for w in workouts if start < w.start.date() <= today]
    earlier = [w for w in workouts
               if start - timedelta(days=EARLIER_DAYS) < w.start.date() <= start]
    if recent or earlier:
        total = sum((w.duration for w in recent), timedelta())
        value = f"{len(recent)} · {text.duration(total)}" if recent else "None"
        per_week = len(earlier) / (EARLIER_DAYS / 7)
        lines.append(Line("Workouts", value,
                          f"{per_week:g} a week in the {EARLIER_DAYS // 7} weeks before."))
    return lines
