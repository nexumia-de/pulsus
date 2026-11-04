"""The view of a week, a month (one value per day) or a year (52 weekly
averages), with the trend sentence and the normal range. No widgets."""
from datetime import timedelta
from statistics import fmean

from pulsus import stats, text
from pulsus.charts import Series
from pulsus.metric.view import View, axis, daily_values, with_unit


def goal_of(metric, step_goal):
    return step_goal if metric.id == "steps" else 100 if metric.id == "pai" else None


def _year_series(metric, daily, first, days, goal):
    weeks = []
    for w in range(days // 7):
        start = first + timedelta(days=7 * w)
        values = [daily[start + timedelta(days=n)] for n in range(7)
                  if start + timedelta(days=n) in daily]
        weeks.append((w, fmean(values) if values else None, start))
    starts = {w: s for w, _, s in weeks}
    return Series([(w, v) for w, v, _ in weeks],
                  "bars" if metric.style == "bars" else "line", 0, len(weeks) - 1,
                  y_format=lambda v: axis(metric, v),
                  describe=lambda x, y: f"Week of {text.short_day(starts[x])}: "
                                        f"{metric.format(y)}",
                  x_labels=[(w, f"{s:%b}") for w, _, s in weeks if s.day <= 7],
                  goal=goal)


def _day_series(metric, daily, first, day, days, goal):
    span = [first + timedelta(days=n) for n in range(days)]
    series = Series([(n, daily.get(d)) for n, d in enumerate(span)], metric.style,
                    0, days - 1, y_format=lambda v: axis(metric, v),
                    describe=lambda x, y: f"{text.day(span[x])}: {metric.format(y)}",
                    x_labels=[(n, text.short_day(first + timedelta(days=n)))
                              for n in range(0, days, 1 if days <= 7 else 7)],
                    goal=goal)
    if metric.style == "dots":
        mean = stats.rolling_mean(daily, span)
        series.average = [(n, mean.get(d)) for n, d in enumerate(span)]
    if metric.baseline:
        series.band = stats.baseline(daily, day)
    return series


def period_view(store, metric, day, days, step_goal):
    """The `days` days up to `day`; more than a month shows weeks."""
    goal = goal_of(metric, step_goal)
    first = day - timedelta(days=days - 1)
    since = min(first, day - timedelta(days=stats.BASELINE_DAYS + 7 * 4))
    daily = daily_values(store, metric, since, day)
    year = days > 31
    if year:
        series = _year_series(metric, daily, first, days, goal)
    else:
        series = _day_series(metric, daily, first, day, days, goal)
    values = [v for _, v in series.points if v is not None]
    period = f"{text.short_day(first)} – {text.short_day(day)}"
    if not values:
        series.summary = f"{metric.title}: no data for {period}."
        return View(series, "No Data",
                    f"Amazfish has stored no {metric.what} for {period}.",
                    tappable=False)
    average = fmean(values)
    if metric.id == "pai":
        what = "Average 7-day total"
    elif year and metric.style != "bars":
        what = "Average of the weekly averages"
    else:
        what = "Average per day"
    per = " a day" if metric.style == "bars" and metric.id != "pai" else ""
    series.summary = (f"{metric.title}, {period}: average {with_unit(metric, average)}"
                      f"{per}, lowest {metric.format(min(values))}, highest "
                      f"{metric.format(max(values))}.")
    rows = [("Average", with_unit(metric, average)),
            ("Lowest", with_unit(metric, min(values))),
            ("Highest", with_unit(metric, max(values))),
            (f"{'Weeks' if year else 'Days'} with data",
             f"{len(values)} of {len(series.points)}")]
    if metric.id == "steps" and not year:
        reached = sum(1 for v in values if v >= step_goal)
        rows.append(("Goal reached", f"{reached} of {len(values)} days"))
    if metric.baseline:
        band = stats.baseline(daily, day)
        rows.append(("Your normal range",
                     f"{metric.format(band[0])}–{with_unit(metric, band[1])}"
                     if band else "after 14 days of data"))
    trend = "" if year else stats.trend_sentence(daily, day, metric.what) or ""
    return View(series, with_unit(metric, average), f"{what}, {period}", trend, rows)
