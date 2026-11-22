"""The route drawing's geometry: flat metres from coordinates and the
scale bar."""
import pytest

from pulsus.data.track import Point

gi = pytest.importorskip("gi")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from pulsus.workout import route  # noqa: E402


def test_project_keeps_distances_and_puts_north_up():
    flat = route.project([Point(52.0, 13.0), Point(52.009, 13.0), Point(52.0, 13.0146)])
    (x0, y0), (x1, y1), (x2, y2) = flat
    assert y1 < y0                                  # north is up (smaller y)
    assert y0 - y1 == pytest.approx(1000, rel=0.01)
    assert x2 - x0 == pytest.approx(1000, rel=0.01)  # east is right
    assert x1 == pytest.approx(x0)


def test_scale_bar_takes_at_most_a_third_of_the_width():
    assert route.scale_length(4000) == 1000
    assert route.scale_length(700) == 200
    assert route.scale_length(20) == 50
    assert route.scale_text(500) == "500 m" and route.scale_text(2000) == "2 km"
