"""What a metric page shows for one range: the chart, the headline and
caption, a trend sentence and the rows of numbers. No widgets."""
from dataclasses import dataclass, field

from pulsus.charts import Series


@dataclass
class View:
    series: Series
    headline: str
    caption: str
    trend: str = ""
    rows: list = field(default_factory=list)    # (title, value)
    # Whether tapping the chart shows values.
    tappable: bool = True


def daily_values(store, metric, first, last):
    """date -> number for the metric (sleep in hours, PAI the 7-day total)."""
    raw = getattr(store, metric.daily)(first, last)
    return {d: metric.value(v) for d, v in raw.items()}


def axis(metric, value):
    """Axis text: '7 h', '12k', '48'."""
    if metric.id == "sleep":
        return f"{value:g} h"
    if abs(value) >= 1000:
        return f"{value / 1000:g}k"
    return f"{value:g}"


def with_unit(metric, value):
    return f"{metric.format(value)} {metric.unit}".strip()
