"""The view of one day: steps per hour, heart rate through the day, the
readings of a day, or the night's sleep as a timeline. No widgets."""
from datetime import datetime, time, timedelta
from statistics import fmean

from pulsus import text
from pulsus.charts import Series
from pulsus.metric.view import View, axis, with_unit

# Metrics that have a day view.
DAY_VIEWS = {"steps", "heart-rate", "sleep", "stress", "hrv", "spo2", "temperature"}
HOURS = [(h, f"{h:02d}:00") for h in (0, 6, 12, 18)]


def day_view(store, metric, day):
    if metric.id == "sleep":
        return night_view(store, day)
    if metric.id == "steps":
        return _steps(store, metric, day)
    return _readings(store, metric, day)


def _no_data(metric, day, series):
    series.summary = f"{metric.title}: no data for {text.day(day).lower()}."
    return View(series, "No Data", f"Amazfish has stored no {metric.what} for "
                                   f"{text.day(day).lower()}.", tappable=False)


def _steps(store, metric, day):
    minutes = store.day_minutes(day)
    per_hour = [0] * 24
    for minute in minutes:
        per_hour[datetime.fromtimestamp(minute.ts).hour] += minute.steps
    series = Series([(h, per_hour[h] if minutes else None) for h in range(24)],
                    "bars", 0, 23, y_format=lambda v: axis(metric, v),
                    describe=lambda x, y: f"{x:02d}:00–{x + 1:02d}:00: "
                                          f"{text.number(y)} steps",
                    x_labels=HOURS)
    if not minutes:
        return _no_data(metric, day, series)
    total = sum(per_hour)
    busiest = max(range(24), key=lambda h: per_hour[h])
    series.summary = f"Steps on {text.day(day)}: {text.number(total)}."
    return View(series, f"{text.number(total)} steps", text.day(day), rows=[
        ("Total", text.number(total)),
        ("Busiest hour", f"{busiest:02d}:00–{busiest + 1:02d}:00")])


def _readings(store, metric, day):
    start = datetime.combine(day, time())
    if metric.id == "heart-rate":
        readings = [(datetime.fromtimestamp(m.ts), m.heart_rate)
                    for m in store.day_minutes(day) if m.heart_rate is not None]
    else:
        readings = store.readings(metric.readings, start, start + timedelta(days=1),
                                  metric.readings_where)
    points = [((t - start).total_seconds(), v) for t, v in readings]
    values = [v for _, v in points]
    style, gap = "dots", None
    if metric.id == "heart-rate":
        # One-minute readings jump; draw 5-minute averages. The numbers
        # below use every reading.
        buckets = {}
        for x, v in points:
            buckets.setdefault(int(x // 300), []).append(v)
        points = [(b * 300 + 150, fmean(vs)) for b, vs in sorted(buckets.items())]
        style, gap = "line", 10 * 60
    series = Series(points, style, 0, 24 * 3600, slots=False, gap=gap,
                    y_format=lambda v: axis(metric, v),
                    describe=lambda x, y: f"{text.clock(start + timedelta(seconds=x))}"
                                          f": {with_unit(metric, y)}",
                    x_labels=[(h * 3600, label) for h, label in HOURS])
    if not values:
        return _no_data(metric, day, series)
    low, high = min(values), max(values)
    series.summary = (f"{metric.title} on {text.day(day)}: {len(values)} readings "
                      f"from {metric.format(low)} to {with_unit(metric, high)}.")
    rows = [("Readings", text.number(len(values))),
            ("Average", with_unit(metric, fmean(values)))]
    if metric.id == "heart-rate":
        resting = store.daily_resting_heart_rate(day, day)
        if day in resting:
            rows.append(("Resting (estimate)", with_unit(metric, resting[day])))
    return View(series, f"{metric.format(low)}–{with_unit(metric, high)}",
                f"Lowest to highest reading, {text.day(day)}", rows=rows)


def night_view(store, night):
    sleep = store.sleeps(night, night).get(night)
    if sleep is None:
        series = Series([], "timeline", 0, 1, slots=False,
                        summary="No sleep for this night.")
        return View(series, "No Data", "No sleep stored for the night to "
                                       f"{text.day(night).lower()}.", tappable=False)
    origin = sleep.start - timedelta(minutes=30)
    finish = sleep.end + timedelta(minutes=30)

    def x(t):
        return (t - origin).total_seconds()

    labels = []
    t = (origin + timedelta(hours=1)).replace(minute=0)
    while t < finish:
        labels.append((x(t), text.clock(t)))
        t += timedelta(hours=2)
    series = Series([], "timeline", 0, x(finish), slots=False,
                    spans=[(x(a), x(b)) for a, b in sleep.segments], x_labels=labels,
                    summary=f"Sleep in the night to {text.day(night)}: asleep "
                            f"{text.duration(sleep.asleep)}, from "
                            f"{text.clock(sleep.start)} to {text.clock(sleep.end)}.")
    return View(series, text.duration(sleep.asleep),
                f"Asleep, {text.clock(sleep.start)}–{text.clock(sleep.end)}. "
                "Bars are asleep, gaps awake.",
                rows=[("Fell asleep", text.clock(sleep.start)),
                      ("Woke up", text.clock(sleep.end)),
                      ("Asleep", text.duration(sleep.asleep)),
                      ("Awake in between", text.duration(sleep.awake))],
                tappable=False)
