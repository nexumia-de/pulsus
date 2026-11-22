"""Pages stay fast with a long history: what Today and the Year view ask
of the store, on a year of the demo person. The bound is generous for a
CI machine; the check on the phone is in docs/owner-checks.md."""
import time
from datetime import date, timedelta

import pytest

from pulsus import data, demo
from pulsus.metrics import METRICS

BUDGET = 2.0   # seconds per page


@pytest.fixture(scope="module")
def year_store(tmp_path_factory):
    path = demo.create(tmp_path_factory.mktemp("year") / "amazfish.kexi", days=365)
    store = data.Store(path)
    yield store
    store.close()


def _seconds(call):
    start = time.perf_counter()
    call()
    return time.perf_counter() - start


def test_today_is_fast_with_a_year_of_history(year_store):
    today = date.today()

    def page():
        for metric in METRICS:
            getattr(year_store, metric.daily)(today - timedelta(days=37), today)
        year_store.workouts(limit=1)
        year_store.last_sample()
    assert _seconds(page) < BUDGET


@pytest.mark.parametrize("metric", METRICS, ids=lambda m: m.id)
def test_year_view_is_fast(year_store, metric):
    today = date.today()
    assert _seconds(lambda: getattr(year_store, metric.daily)(
        today - timedelta(days=364), today)) < BUDGET
