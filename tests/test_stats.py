from datetime import date, timedelta

from pulsus import stats, text

DAY = date(2026, 5, 31)


def series(values, end=DAY):
    return {end - timedelta(days=n): v for n, v in enumerate(reversed(values))}


def test_baseline_needs_two_weeks_and_excludes_the_day():
    assert stats.baseline(series([50] * 13 + [99]), DAY) is None
    daily = series(list(range(40, 60)) + [999])
    low, high = stats.baseline(daily, DAY)
    assert 40 < low < high < 60


def test_rolling_mean_keeps_gaps():
    daily = series([10, 20, 30, 40, 50, 60, 70])
    del daily[DAY - timedelta(days=3)]
    days = [DAY - timedelta(days=n) for n in range(7)]
    mean = stats.rolling_mean(daily, days)
    assert DAY - timedelta(days=3) not in mean
    assert mean[DAY] == (10 + 20 + 30 + 50 + 60 + 70) / 6


def test_trend_sentence():
    flat = series([100] * 35)
    assert "about the same" in stats.trend_sentence(flat, DAY, "steps")
    up = series([100] * 28 + [120] * 7)
    assert stats.trend_sentence(up, DAY, "steps") == \
        "Last 7 days: steps 20% higher than in the 4 weeks before."
    assert "lower" in stats.trend_sentence(series([100] * 28 + [80] * 7), DAY, "HRV")
    assert stats.trend_sentence(series([100] * 10), DAY, "steps") is None


def test_nice_ticks():
    ticks, low, high = stats.nice_ticks(0, 9200)
    assert low == 0 and high >= 9200 and ticks[1] - ticks[0] in (2000, 2500, 2500.0)
    ticks, low, high = stats.nice_ticks(46.2, 49.6)
    assert low <= 46.2 and high >= 49.6 and len(ticks) >= 3


def test_text():
    assert text.duration(timedelta(hours=7, minutes=12)) == "7 h 12 min"
    assert text.duration(timedelta(minutes=45)) == "45 min"
    assert text.duration_hours(1.5) == "1 h 30 min"
    assert text.number(12345) == "12,345"
    assert text.day(DAY, DAY) == "Today"
    assert text.day(DAY - timedelta(days=1), DAY) == "Yesterday"
