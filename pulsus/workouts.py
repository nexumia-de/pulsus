"""Workouts: their kinds and numbers, and the list grouped by month
(docs/visualisation.md#pages). One workout's page is pulsus/workout/."""
from gi.repository import Adw, GLib, Gtk

from pulsus import text

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


# Amazfish fetches workouts only from its Sports page, one per tap
# (docs/amazfish-data.md#workouts); its hourly sync does not.
NO_WORKOUTS = ("Amazfish downloads workouts only when asked. In Amazfish, open "
               "Sports and choose Download Next Activity, once for every "
               "workout on the watch. They show here right after.")


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
                                     description=NO_WORKOUTS))
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
