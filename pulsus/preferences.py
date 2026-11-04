"""Preferences: style, the daily step goal, and where the data comes
from (read-only)."""
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

        data = Adw.PreferencesGroup(
            title="Data",
            description="Pulsus reads Amazfish's database and never changes it. "
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
