"""The window: one navigation view (swipe back everywhere), the Today page
as its root, and a status page while no Amazfish database is found."""
import logging
from datetime import date

from gi.repository import Adw, Gio, GLib, Gtk

from pulsus import NAME, store
from pulsus.metrics import BY_ID

log = logging.getLogger("pulsus.window")


class Window(Adw.ApplicationWindow):
    def __init__(self, app, source, settings_store):
        super().__init__(application=app, default_width=1000,
                         default_height=700, title=NAME)
        # Breakpoints need a minimum size (phosh-toolkit adaptive rules).
        self.set_size_request(360, 294)
        self.source = source
        self.settings_store = settings_store
        self.settings = settings_store.load()
        self.nav = Adw.NavigationView()
        self.toasts = Adw.ToastOverlay(child=self.nav)
        self.set_content(self.toasts)
        self.today = None
        source.connect("changed", self._on_changed)
        # Back in front: Amazfish may have synced meanwhile.
        self.connect("notify::is-active", self._on_active)
        self._show_root()

    def menu_model(self):
        menu = Gio.Menu()
        menu.append("Workouts", "app.show-workouts")
        menu.append("Preferences", "app.preferences")
        menu.append("About Pulsus", "app.about")
        return menu

    def _show_root(self):
        if self.source.found:
            from pulsus.today import TodayPage
            self.today = TodayPage(self)
            self.nav.replace([self.today])
        else:
            self.today = None
            self.nav.replace([self._missing_page()])

    def _missing_page(self):
        page = Adw.NavigationPage(title=NAME, tag="missing")
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        menu = Gtk.MenuButton(icon_name="open-menu-symbolic", tooltip_text="Main Menu",
                              primary=True, menu_model=self.menu_model())
        menu.update_property([Gtk.AccessibleProperty.LABEL], ["Main Menu"])
        header.pack_end(menu)
        toolbar.add_top_bar(header)
        paths = "\n".join(GLib.markup_escape_text(str(p))
                          for p in store.searched_paths())
        status = Adw.StatusPage(
            icon_name="pulsus-heart-symbolic", title="No Amazfish Data Found",
            description="Pulsus shows the data that Amazfish downloads from your "
                        "watch. Pair your watch in Amazfish and let it sync once.\n\n"
                        f"<small>Pulsus looked for:\n{paths}</small>")
        if self.source.error:
            status.set_description(status.get_description() + "\n\n<small>"
                                   + GLib.markup_escape_text(self.source.error)
                                   + "</small>")
        button = Gtk.Button(label="Look Again", halign=Gtk.Align.CENTER)
        button.add_css_class("pill")
        button.add_css_class("suggested-action")
        button.connect("clicked", self._on_look_again)
        status.set_child(button)
        toolbar.set_content(status)
        page.set_child(toolbar)
        return page

    def _on_look_again(self, *_):
        path = store.find_database()
        if path is None:
            self.toast("Still no Amazfish database")
            return
        from pulsus.source import Source
        self.source = Source(path)
        self.source.connect("changed", self._on_changed)
        self._show_root()

    def _on_active(self, *_):
        if self.is_active() and self.source.found:
            self.source.refresh()

    def _on_changed(self, *_):
        """A new snapshot: refresh every page on the stack."""
        for page in self._pages():
            if hasattr(page, "refresh"):
                page.refresh()

    def _pages(self):
        stack = self.nav.get_navigation_stack()
        return [stack.get_item(i) for i in range(stack.get_n_items())]

    def toast(self, message):
        self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(message)))

    # --- navigation ----------------------------------------------------

    def _day(self):
        return self.today.day if self.today is not None else date.today()

    def show_metric(self, metric_id, day=None, range_id="week"):
        if not self.source.found or metric_id not in BY_ID:
            return
        from pulsus.detail import MetricPage
        self.nav.pop_to_page(self.today)
        self.nav.push(MetricPage(self, BY_ID[metric_id], day or self._day(), range_id))

    def show_workouts(self):
        if not self.source.found:
            return
        from pulsus.workouts import WorkoutsPage
        visible = self.nav.get_visible_page()
        if not isinstance(visible, WorkoutsPage):
            self.nav.pop_to_page(self.today)
            self.nav.push(WorkoutsPage(self))

    def show_workout(self, workout_id):
        from pulsus.workouts import WorkoutPage
        workout = self.source.store.workout(workout_id) if self.source.found else None
        if workout is not None:
            self.nav.push(WorkoutPage(self, workout))

    def save_settings(self):
        self.settings_store.save(self.settings)
        if self.today is not None:
            self.today.refresh()
