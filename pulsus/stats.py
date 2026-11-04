"""Numbers behind the charts: personal normal range, rolling average,
trend against the weeks before, and axis ticks. No GTK.

The rules (docs/visualisation.md): compare with the user's own past,
not with population norms; say nothing until there is enough data; call
a small change "about the same".
"""
import math
from datetime import timedelta
from statistics import fmean, quantiles

# Days of data the normal range needs, and how far back it looks.
BASELINE_MIN_DAYS = 14
BASELINE_DAYS = 30
# Below this relative change a trend is "about the same".
SAME = 0.05


def percentile_range(values, low=10, high=90):
    """The range of the middle 80 % of `values` (10th to 90th
    percentile): the user's usual days, without the odd ones."""
    values = sorted(values)
    if len(values) < 2:
        return None
    q = quantiles(values, n=100, method="inclusive")
    return q[low - 1], q[high - 1]


def baseline(daily, before, days=BASELINE_DAYS, minimum=BASELINE_MIN_DAYS):
    """The user's normal range: the middle 80 % of the daily values in the
    `days` days before `before` (a date, not included). None while fewer
    than `minimum` days have a value."""
    values = [v for d, v in daily.items()
              if before - timedelta(days=days) <= d < before]
    if len(values) < minimum:
        return None
    return percentile_range(values)


def rolling_mean(daily, all_days, window=7):
    """date -> mean of the values in the `window` days up to that date,
    for every date in `all_days` that has at least half a window of
    values; a gap in the data stays a gap."""
    result = {}
    for d in all_days:
        values = [daily[d - timedelta(days=n)] for n in range(window)
                  if d - timedelta(days=n) in daily]
        if d in daily and len(values) * 2 >= window:
            result[d] = fmean(values)
    return result


def compare(recent, earlier):
    """Relative change of the mean of `recent` against `earlier`: a float
    (0.12 = 12 % more), or None if either has no values."""
    if not recent or not earlier:
        return None
    before = fmean(earlier)
    if before == 0:
        return None
    return fmean(recent) / before - 1


def trend_sentence(daily, today, what, recent_days=7, earlier_days=28):
    """'This week: 9% more steps than in the 4 weeks before.' or None."""
    recent = [v for d, v in daily.items()
              if today - timedelta(days=recent_days) < d <= today]
    earlier = [v for d, v in daily.items()
               if today - timedelta(days=recent_days + earlier_days) < d
               <= today - timedelta(days=recent_days)]
    if len(earlier) < BASELINE_MIN_DAYS or len(recent) < 3:
        return None
    change = compare(recent, earlier)
    if change is None:
        return None
    period = f"the {earlier_days // 7} weeks before"
    if abs(change) < SAME:
        return f"Last 7 days: {what} about the same as in {period}."
    direction = "higher" if change > 0 else "lower"
    return f"Last 7 days: {what} {abs(change):.0%} {direction} than in {period}."


def nice_ticks(low, high, count=4):
    """Round axis ticks covering [low, high]: (ticks, axis_low, axis_high)."""
    if high <= low:
        high = low + 1
    raw = (high - low) / count
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(m * magnitude for m in (1, 2, 2.5, 5, 10) if m * magnitude >= raw)
    axis_low = math.floor(low / step) * step
    axis_high = math.ceil(high / step) * step
    n = round((axis_high - axis_low) / step)
    return [axis_low + i * step for i in range(n + 1)], axis_low, axis_high
