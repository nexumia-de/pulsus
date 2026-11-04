"""The page of one metric: range buttons, the headline number, a trend
sentence, the chart, the numbers behind it and how they are made
(docs/visualisation.md)."""
from datetime import datetime, time, timedelta
from statistics import fmean

from gi.repository import Adw, GLib, Gtk

from pulsus import stats, text
from pulsus.charts import Chart, Series

# Ranges: label, number of days.
RANGES = (("day", "Day", 1), ("week", "Week", 7), ("month", "Month", 30),
          ("year", "Year", 364))
# Metrics with a day view, and which one.
DAY_VIEWS = {"steps", "heart-rate", "sleep", "stress", "hrv", "spo2", "temperature"}


def _label(text_, classes=(), **kw):
    kw.setdefault("xalign", 0)
    kw.setdefault("wrap", True)
    label = Gtk.Label(label=text_, **kw)
    for c in classes:
        label.add_css_class(c)
    return label


def daily_values(store, metric, first, last):
    """date -> number for the metric (sleep in hours, PAI the 7-day total)."""
    raw = getattr(store, metric.daily)(first, last)
    return {d: metric.value(v) for d, v in raw.items()}


def week_x_labels(first, count, every):
    return [(n, text.short_day(first + timedelta(days=n)))
            for n in range(0, count, every)]


def range_series(store, metric, day, days, goal=None):
    """The chart and its numbers for the `days` days up to `day`; a year
    shows 52 weekly averages. Returns (series, values, headline)."""
    if days > 31:
        first = day - timedelta(days=days - 1)
        daily = daily_values(store, metric, first, day)
        weeks = []
        for w in range(days // 7):
            start = first + timedelta(days=7 * w)
            values = [daily[start + timedelta(days=n)] for n in range(7)
                      if start + timedelta(days=n) in daily]
            weeks.append((w, fmean(values) if values else None, start))
        points = [(w, v) for w, v, _ in weeks]
        starts = {w: s for w, _, s in weeks}
        labels = [(w, f"{s:%b}") for w, _, s in weeks if s.day <= 7]
        series = Series(points, "bars" if metric.style == "bars" else "dots",
                        0, len(weeks) - 1, y_format=lambda v: axis(metric, v),
                        describe=lambda x, y: f"Week of {text.short_day(starts[x])}: "
                                              f"{metric.format(y)}",
                        x_labels=labels, goal=goal)
        if metric.style == "dots":
            series.style = "line"
            series.slots = True
        values = [v for _, v in points if v is not None]
        return series, daily, values
    first = day - timedelta(days=days - 1)
    since = min(first, day - timedelta(days=stats.BASELINE_DAYS + 1))
    daily = daily_values(store, metric, since, day)
    span = [first + timedelta(days=n) for n in range(days)]
    points = [(n, daily.get(d)) for n, d in enumerate(span)]
    series = Series(points, metric.style, 0, days - 1,
                    y_format=lambda v: axis(metric, v),
                    describe=lambda x, y: f"{text.day(span[x])}: {metric.format(y)}",
                    x_labels=week_x_labels(first, days, 1 if days <= 7 else 7),
                    goal=goal)
    if metric.style == "dots":
        mean = stats.rolling_mean(daily, span)
        series.average = [(n, mean.get(d)) for n, d in enumerate(span)]
    if metric.baseline:
        series.band = stats.baseline(daily, day)
    values = [v for _, v in points if v is not None]
    return series, daily, values


def axis(metric, value):
    if metric.id == "sleep":
        return f"{value:g} h"
    if abs(value) >= 1000:
        return f"{value / 1000:g}k"
    return f"{value:g}"


class MetricPage(Adw.NavigationPage):
    def __init__(self, window, metric, day, range_id="week"):
        super().__init__(title=metric.title, tag=f"metric-{metric.id}")
        self.window = window
        self.metric = metric
        self.day = day
        self.range_id = range_id if (range_id != "day" or metric.id in DAY_VIEWS) \
            else "week"
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                           margin_top=12, margin_bottom=24, margin_start=12,
                           margin_end=12)
        clamp = Adw.Clamp(maximum_size=760, child=self.box)
        toolbar.set_content(Gtk.ScrolledWindow(
            child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.set_child(toolbar)

        ranges = Gtk.Box(halign=Gtk.Align.CENTER, homogeneous=True)
        ranges.add_css_class("linked")
        self.range_buttons = {}
        group = None
        for range_name, label, _ in RANGES:
            if range_name == "day" and metric.id not in DAY_VIEWS:
                continue
            button = Gtk.ToggleButton(label=label, group=group)
            group = group or button
            button.connect("toggled", self._on_range, range_name)
            ranges.append(button)
            self.range_buttons[range_name] = button
        self.box.append(ranges)

        self.headline = _label("", ("title-1", "numeric"))
        self.caption = _label("", ("dimmed",))
        self.trend = _label("")
        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for widget in (self.headline, self.caption, self.trend):
            heading.append(widget)
        self.box.append(heading)

        self.chart = Chart(height=220)
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame.add_css_class("card")
        frame.add_css_class("pulsus-chart-card")
        frame.append(self.chart)
        self.hint = _label("Tap the chart to see a value.", ("caption", "dimmed"))
        frame.append(self.hint)
        self.box.append(frame)

        self.numbers = Adw.PreferencesGroup(title="Numbers")
        self.box.append(self.numbers)
        self._rows = []
        about = Adw.PreferencesGroup(title="How It Is Measured")
        about.add(_label(metric.explanation, margin_start=4, margin_end=4))
        self.box.append(about)

        self.range_buttons[self.range_id].set_active(True)
        self.refresh()

    def _on_range(self, button, range_name):
        if button.get_active():
            self.range_id = range_name
            self.refresh()

    def refresh(self):
        store = self.window.source.store
        if store is None:
            return
        for row in self._rows:
            self.numbers.remove(row)
        self._rows = []
        if self.range_id == "day":
            self._day(store)
        else:
            self._range(store, dict((r, n) for r, _, n in RANGES)[self.range_id])

    def _row(self, title, value):
        row = Adw.ActionRow(title=GLib.markup_escape_text(title))
        row.add_suffix(_label(value, ("numeric",), xalign=1, wrap=False))
        self.numbers.add(row)
        self._rows.append(row)

    # --- week, month, year ---------------------------------------------

    def _range(self, store, days):
        m = self.metric
        goal = self.window.settings.step_goal if m.id == "steps" else \
            100 if m.id == "pai" else None
        series, daily, values = range_series(store, m, self.day, days, goal)
        first = self.day - timedelta(days=days - 1)
        period = f"{text.short_day(first)} – {text.short_day(self.day)}"
        if values:
            average = fmean(values)
            per = " a day" if m.style == "bars" and m.id != "pai" else ""
            self.headline.set_label(f"{m.format(average)} {m.unit}".strip())
            what = "average per day" if m.id != "pai" else "average 7-day total"
            if days > 31:
                what = "average of the weekly averages" if m.style != "bars" \
                    else "average per day"
            self.caption.set_label(f"{what.capitalize()}, {period}")
            series.summary = (f"{m.title}, {period}: average {m.format(average)}"
                              f" {m.unit}{per}, lowest {m.format(min(values))}, "
                              f"highest {m.format(max(values))}.")
        else:
            self.headline.set_label("No Data")
            self.caption.set_label(f"Amazfish has stored no {m.what} for {period}.")
            series.summary = f"{m.title}: no data for {period}."
        self.chart.set_series(series)
        self.hint.set_visible(bool(values))
        sentence = stats.trend_sentence(daily, self.day, m.what)
        self.trend.set_label(sentence or "")
        self.trend.set_visible(bool(sentence) and days <= 31)
        if values:
            self._row("Average", f"{m.format(fmean(values))} {m.unit}".strip())
            self._row("Lowest", f"{m.format(min(values))} {m.unit}".strip())
            self._row("Highest", f"{m.format(max(values))} {m.unit}".strip())
            unit = "weeks" if days > 31 else "days"
            total = len(series.points)
            self._row(f"{unit.capitalize()} with data", f"{len(values)} of {total}")
        if m.id == "steps" and values and days <= 31:
            reached = sum(1 for v in values if v >= self.window.settings.step_goal)
            self._row("Goal reached", f"{reached} of {len(values)} days")
        if m.baseline:
            band = stats.baseline(daily, self.day)
            if band:
                self._row("Your normal range",
                          f"{m.format(band[0])}–{m.format(band[1])} {m.unit}".strip())
            else:
                self._row("Your normal range", "after 14 days of data")

    # --- one day -------------------------------------------------------

    def _day(self, store):
        m = self.metric
        if m.id == "sleep":
            return self._night(store)
        start = datetime.combine(self.day, time())
        end = start + timedelta(days=1)
        hours = [(h * 3600, f"{h:02d}:00") for h in (0, 6, 12, 18)]
        series = None
        values = []
        if m.id == "steps":
            minutes = store.day_minutes(self.day)
            per_hour = [0] * 24
            for minute in minutes:
                per_hour[datetime.fromtimestamp(minute.ts).hour] += minute.steps
            points = [(h, per_hour[h] if minutes else None) for h in range(24)]
            series = Series(points, "bars", 0, 23, y_format=lambda v: axis(m, v),
                            describe=lambda x, y: f"{x:02d}:00–{x + 1:02d}:00: "
                                                  f"{text.number(y)} steps",
                            x_labels=[(h, f"{h:02d}:00") for h in (0, 6, 12, 18)])
            total = sum(per_hour)
            values = [total] if minutes else []
            self.headline.set_label(f"{text.number(total)} steps")
            self.caption.set_label(text.day(self.day))
            series.summary = f"Steps on {text.day(self.day)}: {text.number(total)}."
            if minutes:
                self._row("Total", text.number(total))
                busiest = max(range(24), key=lambda h: per_hour[h])
                self._row("Busiest hour", f"{busiest:02d}:00–{busiest + 1:02d}:00")
        else:
            if m.id == "heart-rate":
                minutes = store.day_minutes(self.day)
                readings = [(datetime.fromtimestamp(x.ts), x.heart_rate)
                            for x in minutes if x.heart_rate is not None]
                style, gap = "line", 5 * 60
            else:
                readings = store.readings(m.readings, start, end, m.readings_where)
                style, gap = "dots", None
            points = [((t - start).total_seconds(), v) for t, v in readings]
            values = [v for _, v in points]
            if m.id == "heart-rate":
                # One-minute readings jump; draw 5-minute averages. The
                # numbers below use every reading.
                buckets = {}
                for x, v in points:
                    buckets.setdefault(int(x // 300), []).append(v)
                points = [(b * 300 + 150, fmean(vs)) for b, vs in sorted(buckets.items())]
                gap = 10 * 60
            series = Series(points, style, 0, 24 * 3600, slots=False, gap=gap,
                            y_format=lambda v: axis(m, v),
                            describe=lambda x, y: f"{text.clock(start + timedelta(seconds=x))}"
                                                  f": {m.format(y)} {m.unit}".strip(),
                            x_labels=hours)
            if values:
                self.headline.set_label(
                    f"{m.format(min(values))}–{m.format(max(values))} {m.unit}".strip())
                self.caption.set_label(f"Lowest to highest reading, {text.day(self.day)}")
                series.summary = (f"{m.title} on {text.day(self.day)}: "
                                  f"{len(values)} readings from {m.format(min(values))} "
                                  f"to {m.format(max(values))} {m.unit}.")
                self._row("Readings", text.number(len(values)))
                self._row("Average", f"{m.format(fmean(values))} {m.unit}".strip())
                if m.id == "heart-rate":
                    resting = store.daily_resting_heart_rate(self.day, self.day)
                    if self.day in resting:
                        self._row("Resting (estimate)",
                                  f"{m.format(resting[self.day])} bpm")
        if not values:
            self.headline.set_label("No Data")
            self.caption.set_label(f"Amazfish has stored no {m.what} for "
                                   f"{text.day(self.day).lower()}.")
        self.trend.set_visible(False)
        self.chart.set_series(series)
        self.hint.set_visible(bool(values))

    def _night(self, store):
        sleep = store.sleeps(self.day, self.day).get(self.day)
        self.trend.set_visible(False)
        if sleep is None:
            self.headline.set_label("No Data")
            self.caption.set_label("No sleep stored for the night to "
                                   f"{text.day(self.day).lower()}.")
            self.chart.set_series(Series([], "timeline", 0, 1, slots=False,
                                         summary="No sleep for this night."))
            self.hint.set_visible(False)
            return
        origin = sleep.start - timedelta(minutes=30)
        finish = sleep.end + timedelta(minutes=30)

        def x(t):
            return (t - origin).total_seconds()
        first_hour = (origin + timedelta(hours=1)).replace(minute=0)
        labels = []
        t = first_hour
        while t < finish:
            labels.append((x(t), text.clock(t)))
            t += timedelta(hours=2)
        series = Series([], "timeline", 0, x(finish), slots=False,
                        spans=[(x(a), x(b)) for a, b in sleep.segments],
                        x_labels=labels, y_zero=True)
        series.summary = (f"Sleep in the night to {text.day(self.day)}: asleep "
                          f"{text.duration(sleep.asleep)}, from {text.clock(sleep.start)}"
                          f" to {text.clock(sleep.end)}.")
        self.chart.set_series(series)
        self.hint.set_visible(False)
        self.headline.set_label(text.duration(sleep.asleep))
        self.caption.set_label(f"Asleep, {text.clock(sleep.start)}–"
                               f"{text.clock(sleep.end)}. Bars are asleep, gaps awake.")
        self._row("Fell asleep", text.clock(sleep.start))
        self._row("Woke up", text.clock(sleep.end))
        self._row("Asleep", text.duration(sleep.asleep))
        self._row("Awake in between", text.duration(sleep.awake))
