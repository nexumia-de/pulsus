"""The Summary page: the last seven days in words, the step-goal streak
and the user's records (docs/visualisation.md#pages)."""
from datetime import date, timedelta

from gi.repository import Adw, GLib, Gtk

from pulsus import insight, text
from pulsus.workouts import kind_name


def gather(store, step_goal, today=None):
    """(week lines, streaks, records) from the store."""
    today = today or date.today()
    first = store.first_day() or today
    steps = store.daily_steps(first, today)
    since = today - timedelta(days=insight.RECENT_DAYS + insight.EARLIER_DAYS + 1)
    sleep = {d: text.hours(v) for d, v in store.daily_sleep(since, today).items()}
    resting = store.daily_resting_heart_rate(since, today)
    workouts = store.workouts()
    return (insight.week(steps, sleep, resting, workouts, today - timedelta(days=1)),
            insight.streaks(steps, step_goal, today),
            insight.records(steps, workouts, kind_name))


def days(count):
    return f"{count} day" if count == 1 else f"{count} days"


class SummaryPage(Adw.NavigationPage):
    def __init__(self, window):
        super().__init__(title="Summary", tag="summary")
        self.window = window
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        self.page = Adw.PreferencesPage()
        toolbar.set_content(self.page)
        self.set_child(toolbar)
        self.groups = []
        self.refresh()

    def _group(self, title, description=""):
        group = Adw.PreferencesGroup(title=title, description=description)
        self.page.add(group)
        self.groups.append(group)
        return group

    @staticmethod
    def _row(title, value, subtitle=""):
        row = Adw.ActionRow(title=GLib.markup_escape_text(title),
                            subtitle=GLib.markup_escape_text(subtitle))
        row.add_suffix(Gtk.Label(label=value, css_classes=["numeric"]))
        return row

    def refresh(self):
        for group in self.groups:
            self.page.remove(group)
        self.groups = []
        store = self.window.source.store
        if store is None:
            return
        goal = self.window.settings.step_goal
        lines, streak, records = gather(store, goal)

        group = self._group("Last 7 Days",
                            "The 7 days up to yesterday, against the 4 weeks before.")
        for line in lines:
            group.add(self._row(line.title, line.value, line.note))
        if not lines:
            group.add(self._row("No Data", "–", "Amazfish has stored nothing "
                                                "for the last 7 days."))

        group = self._group("Step Goal Streak",
                            f"Days in a row with {text.number(goal)} steps or more.")
        group.add(self._row("Current Streak", days(streak.current),
                            "Today counts once the goal is reached."))
        group.add(self._row(
            "Longest Streak", days(streak.longest),
            f"Until {text.day(streak.longest_end)}." if streak.longest_end else ""))

        if records:
            group = self._group("Records", "Your own bests in what Amazfish has stored.")
            for record in records:
                when = text.day(record.when)
                row = self._row(record.title, record.value,
                                f"{record.kind}, {when}" if record.kind else when)
                if record.workout_id is not None:
                    row.set_activatable(True)
                    row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
                    row.connect("activated", lambda r, wid=record.workout_id:
                                self.window.show_workout(wid))
                group.add(row)
