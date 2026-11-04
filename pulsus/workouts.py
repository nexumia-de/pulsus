"""Workouts: the list, grouped by month, and one workout with its numbers
and the heart rate during it (docs/visualisation.md#workouts)."""
from gi.repository import Adw, GLib, Gtk

from pulsus import text
from pulsus.charts import Chart, Series

# Amazfish's ActivityKind values (lib/src/activitykind.h) for the kinds
# a Zepp OS watch records most; other kinds take the name Amazfish
# stored ("Running-20261104-0730" -> "Running").
KINDS = {
    0x10: "Running", 0x20: "Walking", 0x40: "Swimming", 0x80: "Cycling",
    0x100: "Treadmill", 0x200: "Exercise", 0x400: "Open Water Swimming",
    0x800: "Indoor Cycling", 0x1000: "Elliptical", 0x2000: "Jump Rope",
    0x4000: "Yoga", 0x10000: "Rowing Machine", 0x200000: "Strength Training",
    0x400000: "Hiking", 0x800000: "Climbing", 0x04000009: "Pilates",
    0x04000012: "Indoor Walking", 0x04000016: "Rowing",
}
ICONS = {0x80: "pulsus-cycling-symbolic", 0x800: "pulsus-cycling-symbolic"}

# Shown first, in this order: key, title, how.
NUMBERS = (
    ("distanceMeters", "Distance", lambda v: f"{v / 1000:.2f} km"),
    ("paceAvg", "Average pace", lambda v: f"{int(v)}:{round(v % 1 * 60):02d} min/km"),
    ("averageHR", "Average heart rate", lambda v: f"{v:.0f} bpm"),
    ("maxHR", "Highest heart rate", lambda v: f"{v:.0f} bpm"),
    ("caloriesBurnt", "Energy", lambda v: f"{v:.0f} kcal"),
    ("steps", "Steps", lambda v: text.number(v)),
    ("stepsAvgCadence", "Average cadence", lambda v: f"{v:.0f} steps/min"),
    ("elevationGain", "Climbed", lambda v: f"{v:.0f} m"),
    ("aerobicTrainingEffect", "Aerobic training effect", lambda v: f"{v:.1f}"),
    ("maximumOxygenUptake", "VO₂ max (watch)", lambda v: f"{v:.0f} ml/kg/min"),
)


def kind_name(workout):
    if workout.kind in KINDS:
        return KINDS[workout.kind]
    name = workout.name.split("-")[0].strip()
    return name or "Workout"


def summary(workout):
    parts = [text.clock(workout.start), text.duration(workout.duration)]
    distance = workout.number("distanceMeters")
    if distance:
        parts.append(f"{distance / 1000:.2f} km")
    return " · ".join(parts)


class WorkoutsPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title="Workouts", tag="workouts")
        self.window = window
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.page = Adw.PreferencesPage()
        toolbar.set_content(self.page)
        self.set_child(toolbar)
        self.groups = []
        self.refresh()

    def refresh(self):
        for group in self.groups:
            self.page.remove(group)
        self.groups = []
        store = self.window.source.store
        workouts = store.workouts() if store else []
        if not workouts:
            group = Adw.PreferencesGroup()
            group.add(Adw.StatusPage(icon_name="pulsus-workout-symbolic",
                                     title="No Workouts",
                                     description="Workouts recorded on the watch "
                                                 "show here after Amazfish has "
                                                 "downloaded them."))
            self.page.add(group)
            self.groups.append(group)
            return
        group = None
        month = None
        for w in workouts:
            if (w.start.year, w.start.month) != month:
                month = (w.start.year, w.start.month)
                group = Adw.PreferencesGroup(title=f"{w.start:%B %Y}")
                self.page.add(group)
                self.groups.append(group)
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(
                    f"{kind_name(w)}, {text.day(w.start.date())}"),
                subtitle=GLib.markup_escape_text(summary(w)), activatable=True)
            row.add_prefix(Gtk.Image(icon_name=ICONS.get(w.kind, "pulsus-workout-symbolic")))
            row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
            row.connect("activated", lambda r, wid=w.id: self.window.show_workout(wid))
            group.add(row)


class WorkoutPage(Adw.NavigationPage):
    def __init__(self, window, workout):
        super().__init__(title=kind_name(workout), tag=f"workout-{workout.id}")
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

        minutes = window.source.store.minutes(workout.start, workout.end)
        readings = [(m.ts - workout.start.timestamp(), m.heart_rate)
                    for m in minutes if m.heart_rate is not None]
        if readings:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.add_css_class("card")
            card.add_css_class("pulsus-chart-card")
            card.append(Gtk.Label(label="Heart Rate", xalign=0, css_classes=["heading"]))
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

        numbers = Adw.PreferencesGroup(title="Numbers")
        shown = set()
        for key, title_, how in NUMBERS:
            value = workout.number(key)
            if value:
                row = Adw.ActionRow(title=title_)
                row.add_suffix(Gtk.Label(label=how(value), css_classes=["numeric"]))
                numbers.add(row)
                shown.add(key)
        if shown:
            box.append(numbers)
        clamp = Adw.Clamp(maximum_size=760, child=box)
        toolbar.set_content(Gtk.ScrolledWindow(
            child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.set_child(toolbar)
