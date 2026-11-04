import logging
import os
import tempfile
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from pulsus import (APP_ID, NAME, NIGHTLY, REPO_URL, SUPPORT_URL,  # noqa: E402
                    VERSION_LABEL)

log = logging.getLogger("pulsus")


def demo_source():
    """PULSUS_DEMO=1: the made-up person of pulsus.demo, written to a
    temporary directory, with temporary settings (screenshots)."""
    from pulsus import demo
    from pulsus.data.source import Source
    directory = Path(tempfile.mkdtemp(prefix="pulsus-demo-"))
    os.environ["XDG_CONFIG_HOME"] = str(directory / "config")
    os.environ["XDG_CACHE_HOME"] = str(directory / "cache")
    path = demo.create(directory / "amazfish.kexi")
    return Source(path, watch=False)


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.source = None
        self.settings_store = None
        for name, callback in (("about", self._on_about),
                               ("preferences", self._on_preferences),
                               ("show-workouts", self._on_show_workouts),
                               ("show-latest-workout", self._on_latest_workout),
                               ("quit", self._on_quit)):
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)
        # show-metric('steps'), show-metric('sleep:day'), show-metric(
        # 'heart-rate:month'): opens a metric page, also over D-Bus for the
        # screenshots (release.toml).
        action = Gio.SimpleAction.new("show-metric", GLib.VariantType("s"))
        action.connect("activate", self._on_show_metric)
        self.add_action(action)
        self.set_accels_for_action("app.quit", ["<Control>q"])
        self.set_accels_for_action("app.preferences", ["<Control>comma"])
        self.set_accels_for_action("app.show-workouts", ["<Control>w"])

    def do_startup(self):
        Adw.Application.do_startup(self)
        css = Gtk.CssProvider()
        css.load_from_path(str(Path(__file__).with_name("style.css")))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Pulsus's own symbolic icons; also when run from the source tree.
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icons = Path(__file__).resolve().parent.parent / "data" / "icons"
        if icons.is_dir():
            theme.add_search_path(str(icons))
        from pulsus import settings
        from pulsus.data.source import Source
        if os.environ.get("PULSUS_DEMO"):
            self.source = demo_source()
        else:
            self.source = Source()
        self.settings_store = settings.Store()
        from phosh_toolkit import style
        style.apply(self.settings_store.load().style)

    def do_activate(self):
        from pulsus.window import Window
        window = self.props.active_window
        if window is None:
            window = Window(self, self.source, self.settings_store)
            if os.environ.get("PULSUS_DEMO"):
                window.maximize()
            if NIGHTLY:
                window.add_css_class("devel")
        window.present()

    def _window(self):
        return self.props.active_window

    def _on_show_metric(self, action, value):
        if self._window():
            metric, _, range_id = value.unpack().partition(":")
            self._window().show_metric(metric, range_id=range_id or "week")

    def _on_show_workouts(self, *_):
        if self._window():
            self._window().show_workouts()

    def _on_latest_workout(self, *_):
        window = self._window()
        if window and window.source.found:
            latest = window.source.store.workouts(limit=1)
            if latest:
                window.show_workouts()
                window.show_workout(latest[0].id)

    def _on_quit(self, *_):
        self.quit()

    def _on_preferences(self, *_):
        window = self._window()
        if window:
            from pulsus.preferences import PreferencesDialog
            PreferencesDialog(window).present(window)

    def _on_about(self, *_):
        dialog = Adw.AboutDialog(
            application_name=NAME,
            application_icon=APP_ID,
            version=VERSION_LABEL,
            developer_name="suitably",
            website=REPO_URL,
            issue_url=f"{REPO_URL}/issues",
            license_type=Gtk.License.AGPL_3_0,
            comments="See the health data of your watch, as Amazfish downloads "
                     "it. Not affiliated with the Amazfish project or the watch "
                     "maker. Not a medical device.",
        )
        dialog.add_link("Support Development", SUPPORT_URL)
        dialog.present(self._window())


def main(argv):
    # PULSUS_DEBUG=1 logs snapshots and file changes.
    logging.basicConfig(format="pulsus: %(name)s: %(message)s")
    if os.environ.get("PULSUS_DEBUG"):
        logging.getLogger("pulsus").setLevel(logging.DEBUG)
    return Application().run(argv)
