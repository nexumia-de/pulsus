"""The pages through the real widgets with the demo database: Today, every
metric in every range, workouts, preferences, a new snapshot, and the
page shown without a database. Needs a display (CI runs pytest under
xvfb-run)."""
import os
import shutil

import pytest

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    pytest.skip("needs a display", allow_module_level=True)

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib  # noqa: E402

from pulsus import data, settings  # noqa: E402
from pulsus.data import location, source  # noqa: E402
from pulsus.metrics import METRICS  # noqa: E402


@pytest.fixture(scope="module")
def app():
    """One application for all tests: a second one with the same id can't
    register on the session bus."""
    from pulsus.main import Application
    application = Application()
    application.register(None)
    Adw.init()
    yield application


def iterate(times=20):
    ctx = GLib.MainContext.default()
    for _ in range(times):
        while ctx.pending():
            ctx.iteration(False)


def visible(window):
    return window.nav.get_visible_page()


def new_window(app, path):
    from pulsus.window import Window
    window = Window(app, source.Source(path, watch=False), settings.Store())
    window.present()
    iterate()
    return window


def test_today_metrics_and_workouts(app, demo_db, tmp_path):
    from pulsus.metric import RANGES, MetricPage
    from pulsus.preferences import PreferencesDialog
    from pulsus.today import TodayPage
    from pulsus.workouts import WorkoutPage, WorkoutsPage

    db = tmp_path / "amazfish.kexi"
    shutil.copy(demo_db, db)
    window = new_window(app, db)
    today = visible(window)
    assert isinstance(today, TodayPage)
    for metric in METRICS:
        card = today.metric_cards[metric.id]
        assert card.get_parent().get_visible(), metric.id
        assert card.value.get_label() not in ("", "–"), metric.id
    assert today.workout_card.get_parent().get_visible()
    assert not today.banner.get_revealed()
    assert not today.next.get_sensitive()

    # Every metric in every range it has.
    for metric in METRICS:
        today.metric_cards[metric.id].emit("clicked")
        iterate()
        page = visible(window)
        assert isinstance(page, MetricPage) and page.metric is metric
        for range_name, _, _ in RANGES:
            button = page.range_buttons.get(range_name)
            if button is None:
                continue
            button.set_active(True)
            iterate()
            assert page.headline.get_label() and page.headline.get_label() != "No Data", \
                (metric.id, range_name)
            assert page.chart.series is not None and page.chart.series.summary
        window.nav.pop()
        iterate()

    # The day before.
    today.previous.emit("clicked")
    iterate()
    assert today.title.get_title() == "Yesterday"
    assert today.next.get_sensitive()
    today.next.emit("clicked")
    iterate()

    today.workout_card.emit("clicked")
    iterate()
    workouts = visible(window)
    assert isinstance(workouts, WorkoutsPage)
    latest = window.source.store.workouts(limit=1)[0]
    window.show_workout(latest.id)
    iterate()
    assert isinstance(visible(window), WorkoutPage)
    window.nav.pop_to_page(today)

    # The step goal changes the card at once and is kept.
    dialog = PreferencesDialog(window)
    dialog.goal_row.set_selected(settings.STEP_GOALS.index(12000))
    iterate()
    assert "12,000" in today.metric_cards["steps"].context.get_label()
    assert settings.Store().load().step_goal == 12000
    window.destroy()


def test_new_snapshot_refreshes_the_pages(app, tmp_path):
    from pulsus import demo
    db = demo.create(tmp_path / "amazfish.kexi", days=20)
    window = new_window(app, db)
    window.show_metric("steps")
    iterate()
    old = window.source.store
    con = __import__("sqlite3").connect(db)
    con.execute("UPDATE mi_band_activity SET steps = steps + 1")
    con.commit()
    con.close()
    window.source.refresh()
    iterate()
    assert window.source.store is not old
    window.destroy()


def test_without_a_database(app, monkeypatch, tmp_path):
    monkeypatch.setattr(location.Path, "home", lambda: tmp_path)
    from pulsus.window import Window
    window = Window(app, source.Source(None, watch=False), settings.Store())
    window.present()
    iterate()
    assert visible(window).get_tag() == "missing"
    # Amazfish synced meanwhile: Look Again finds it.
    from pulsus import demo
    demo.create(tmp_path / data.LOCATIONS[0], days=3)
    window._on_look_again()
    iterate()
    assert visible(window).get_tag() == "today"
    window.destroy()
