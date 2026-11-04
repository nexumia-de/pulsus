"""The page of one metric (docs/visualisation.md#pages).

- view.py: what a page shows for one range, independent of widgets
- period.py: the view of a week, a month or a year
- day.py: the view of one day or night
- page.py: the page: range buttons, headline, chart, numbers
"""
from pulsus.metric.page import RANGES, MetricPage

__all__ = ["MetricPage", "RANGES"]
