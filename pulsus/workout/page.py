"""One workout: duration and times, the route, the heart rate during it,
the time in heart-rate zones, the kilometres and the watch's numbers."""
from datetime import timedelta

from gi.repository import Adw, Gtk

from pulsus import text
from pulsus.charts import Chart, Series
from pulsus.data import track
from pulsus.workout import zones
from pulsus.workout.route import Route
from pulsus.workouts import NUMBERS, kind_name


def _card(title):
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    card.add_css_class("card")
    card.add_css_class("pulsus-chart-card")
    card.append(Gtk.Label(label=title, xalign=0, css_classes=["heading"]))
    return card


def _row(title, value, subtitle=""):
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    row.add_suffix(Gtk.Label(label=value, css_classes=["numeric"]))
    return row


def pace(seconds, metres):
    """'5:32 min/km'."""
    per_km = round(seconds / (metres / 1000))
    return f"{per_km // 60}:{per_km % 60:02d} min/km"


class WorkoutPage(Adw.NavigationPage):
    def __init__(self, window, workout):
        super().__init__(title=kind_name(workout), tag=f"workout-{workout.id}")
        store = window.source.store
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=12, margin_bottom=24, margin_start=12, margin_end=12)
        head = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label=text.duration(workout.duration), xalign=0)
        title.add_css_class("title-1")
        title.add_css_class("numeric")
        head.append(title)
        when = Gtk.Label(label=f"{text.day(workout.start.date())}, "
                               f"{text.clock(workout.start)}–{text.clock(workout.end)}",
                         xalign=0, wrap=True)
        when.add_css_class("dimmed")
        head.append(when)
        box.append(head)

        points = store.track(workout.id)
        self.route = None
        if len(points) >= 2:
            card = _card("Route")
            self.route = Route(points)
            card.append(self.route)
            card.append(Gtk.Label(
                label="The GPS track to scale, north up. Watch Health loads "
                      "no map data, so there is no map behind it.",
                xalign=0, wrap=True, css_classes=["caption", "dimmed"]))
            box.append(card)

        minutes = store.minutes(workout.start, workout.end)
        readings = [(m.ts - workout.start.timestamp(), m.heart_rate)
                    for m in minutes if m.heart_rate is not None]
        if readings:
            card = _card("Heart Rate")
            chart = Chart(height=200)
            length = max(60.0, (workout.end - workout.start).total_seconds())
            step = 600 if length <= 3600 else 1800
            values = [v for _, v in readings]
            chart.set_series(Series(
                readings, "line", 0, length, slots=False, gap=180,
                y_format=lambda v: f"{v:g}",
                describe=lambda x, y: f"{int(x // 60)} min: {y} bpm",
                x_labels=[(t, f"{t // 60} min") for t in range(0, int(length) + 1, step)],
                summary=f"Heart rate during the workout, {min(values)} to "
                        f"{max(values)} bpm."))
            card.append(chart)
            box.append(card)

        self.zones = self._zones(window, store, [v for _, v in readings])
        if self.zones is not None:
            box.append(self.zones)
        self.splits = self._splits(points)
        if self.splits is not None:
            box.append(self.splits)

        numbers = Adw.PreferencesGroup(title="Numbers")
        shown = set()
        for key, title_, how in NUMBERS:
            value = workout.number(key)
            if value:
                numbers.add(_row(title_, how(value)))
                shown.add(key)
        if shown:
            box.append(numbers)
        clamp = Adw.Clamp(maximum_size=760, child=box)
        toolbar.set_content(Gtk.ScrolledWindow(
            child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.set_child(toolbar)

    def _zones(self, window, store, readings):
        """Time in each heart-rate zone, as rows with a bar each."""
        own = window.settings.max_heart_rate
        maximum = own or store.highest_heart_rate()
        if not readings or not maximum:
            return None
        found, below = zones.time_in_zones(readings, maximum)
        source = "set in Preferences" if own else \
            "the highest reading Amazfish has stored, an estimate; set your own " \
            "in Preferences"
        group = Adw.PreferencesGroup(
            title="Heart-Rate Zones",
            description=f"Minutes in each tenth of your maximum heart rate of "
                        f"{maximum} bpm ({source}).")
        total = len(readings)
        for zone in reversed(found):
            row = _row(f"Zone {zone.number}", text.duration(timedelta(minutes=zone.minutes)),
                       f"{zone.percent} · {zone.beats}")
            bar = Gtk.ProgressBar(fraction=zone.minutes / total, valign=Gtk.Align.CENTER,
                                  accessible_role=Gtk.AccessibleRole.PRESENTATION)
            bar.add_css_class("pulsus-zone-bar")
            row.add_suffix(bar)
            group.add(row)
        if below:
            group.add(_row("Below Zone 1", text.duration(timedelta(minutes=below)),
                           f"under {found[0].low} bpm"))
        return group

    def _splits(self, points):
        """How long each kilometre of the track took."""
        parts = track.splits(points)
        if len(parts) < 2:
            return None
        group = Adw.PreferencesGroup(
            title="Kilometres",
            description="From the GPS track; pauses count.")
        for n, (metres, seconds) in enumerate(parts, 1):
            took = text.minutes_seconds(seconds)
            if metres >= 1000:
                group.add(_row(f"Kilometre {n}", took))
            else:
                group.add(_row(f"Last {metres:.0f} m", took, pace(seconds, metres))
                          if metres >= 50 else
                          _row(f"Last {metres:.0f} m", took))
        return group
