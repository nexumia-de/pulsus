"""The page of one metric: range buttons, the headline number, a trend
sentence, the chart, the numbers behind it and how they are made."""
from gi.repository import Adw, GLib, Gtk

from pulsus.charts import Chart
from pulsus.metric.day import DAY_VIEWS, day_view
from pulsus.metric.period import period_view

# Ranges: id, label, number of days.
RANGES = (("day", "Day", 1), ("week", "Week", 7), ("month", "Month", 30),
          ("year", "Year", 364))


def _label(value, classes=(), **kw):
    kw.setdefault("xalign", 0)
    kw.setdefault("wrap", True)
    label = Gtk.Label(label=value, **kw)
    for c in classes:
        label.add_css_class(c)
    return label


class MetricPage(Adw.NavigationPage):
    def __init__(self, window, metric, day, range_id="week"):
        super().__init__(title=metric.title, tag=f"metric-{metric.id}")
        self.window = window
        self.metric = metric
        self.day = day
        if range_id == "day" and metric.id not in DAY_VIEWS:
            range_id = "week"
        self.range_id = range_id
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=12, margin_bottom=24, margin_start=12, margin_end=12)
        clamp = Adw.Clamp(maximum_size=760, child=box)
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
        box.append(ranges)

        self.headline = _label("", ("title-1", "numeric"))
        self.caption = _label("", ("dimmed",))
        self.trend = _label("")
        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for widget in (self.headline, self.caption, self.trend):
            heading.append(widget)
        box.append(heading)

        self.chart = Chart(height=220)
        frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame.add_css_class("card")
        frame.add_css_class("pulsus-chart-card")
        frame.append(self.chart)
        self.hint = _label("Tap the chart to see a value.", ("caption", "dimmed"))
        frame.append(self.hint)
        box.append(frame)

        self.numbers = Adw.PreferencesGroup(title="Numbers")
        box.append(self.numbers)
        self._rows = []
        about = Adw.PreferencesGroup(title="How It Is Measured")
        about.add(_label(metric.explanation, margin_start=4, margin_end=4))
        box.append(about)

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
        if self.range_id == "day":
            view = day_view(store, self.metric, self.day)
        else:
            days = dict((r, n) for r, _, n in RANGES)[self.range_id]
            view = period_view(store, self.metric, self.day, days,
                               self.window.settings.step_goal)
        self.headline.set_label(view.headline)
        self.caption.set_label(view.caption)
        self.trend.set_label(view.trend)
        self.trend.set_visible(bool(view.trend))
        self.chart.set_series(view.series)
        self.hint.set_visible(view.tappable)
        for row in self._rows:
            self.numbers.remove(row)
        self._rows = []
        for title, value in view.rows:
            row = Adw.ActionRow(title=GLib.markup_escape_text(title))
            row.add_suffix(_label(value, ("numeric",), xalign=1, wrap=False))
            self.numbers.add(row)
            self._rows.append(row)
        self.numbers.set_visible(bool(view.rows))
