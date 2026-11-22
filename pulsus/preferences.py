"""Preferences: style, the daily step goal, the maximum heart rate for
the zones, and where the data comes from (read-only)."""
from gi.repository import Adw, GLib, Gtk
from phosh_toolkit.style import style_row

from pulsus import settings


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, window):
        super().__init__(title="Preferences")
        self.window = window
        page = Adw.PreferencesPage(title="General",
                                   icon_name="preferences-system-symbolic")
        appearance = Adw.PreferencesGroup(title="Appearance")
        self.style_row = style_row(window.settings.style, self._on_style)
        appearance.add(self.style_row)
        page.add(appearance)

        goals = Adw.PreferencesGroup(title="Goals")
        names = Gtk.StringList.new([f"{g:,} steps" for g in settings.STEP_GOALS])
        self.goal_row = Adw.ComboRow(title="Daily Step Goal", model=names)
        goal = window.settings.step_goal
        if goal in settings.STEP_GOALS:
            self.goal_row.set_selected(settings.STEP_GOALS.index(goal))
        self.goal_row.connect("notify::selected", self._on_goal)
        goals.add(self.goal_row)
        page.add(goals)

        low, high = settings.MAX_HEART_RATE
        own = window.settings.max_heart_rate
        store = window.source.store
        highest = store.highest_heart_rate() if store else None
        zones = Adw.PreferencesGroup(
            title="Heart-Rate Zones",
            description="The zones of a workout are tenths of your maximum "
                        "heart rate.")
        self.estimate_row = Adw.SwitchRow(
            title="Estimate From Your Data",
            subtitle=f"The highest reading Amazfish has stored: {highest} bpm"
                     if highest else "The highest reading Amazfish has stored",
            active=not own)
        self.max_row = Adw.SpinRow(
            title="Maximum Heart Rate", subtitle="Beats per minute",
            adjustment=Gtk.Adjustment(lower=low, upper=high, step_increment=1,
                                      page_increment=5,
                                      value=own or min(max(highest or 180, low), high)),
            sensitive=bool(own))
        self.estimate_row.connect("notify::active", self._on_max)
        self.max_row.connect("notify::value", self._on_max)
        zones.add(self.estimate_row)
        zones.add(self.max_row)
        page.add(zones)

        data = Adw.PreferencesGroup(
            title="Data",
            description="Watch Health reads Amazfish's database and never changes it. "
                        "It keeps no health data of its own.")
        path = window.source.path
        row = Adw.ActionRow(title="Amazfish Database",
                            subtitle=GLib.markup_escape_text(str(path) if path else
                                                             "Not found"),
                            subtitle_selectable=True)
        data.add(row)
        page.add(data)
        self.add(page)

    def _on_style(self, style):
        self.window.settings.style = style
        self.window.save_settings()

    def _on_goal(self, row, *_):
        self.window.settings.step_goal = settings.STEP_GOALS[row.get_selected()]
        self.window.save_settings()

    def _on_max(self, *_):
        estimate = self.estimate_row.get_active()
        self.max_row.set_sensitive(not estimate)
        self.window.settings.max_heart_rate = \
            0 if estimate else int(self.max_row.get_value())
        self.window.save_settings()
