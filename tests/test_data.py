"""Reading Amazfish's database: finding it, the read-only snapshot, and
the daily values, checked against hand-made minutes."""
import os
import sqlite3
import stat
from datetime import date, datetime, time, timedelta

import pytest

from pulsus import data as store
from pulsus import demo
from pulsus.data.values import KIND_SLEEP


def make_db(path, minutes):
    """A database with Amazfish's activity table and the given
    (datetime, steps, heartrate, raw_kind) minutes."""
    db = sqlite3.connect(path)
    db.executescript(demo.SCHEMA)
    db.executemany(
        "INSERT INTO mi_band_activity (timestamp, steps, heartrate, raw_kind) "
        "VALUES (?, ?, ?, ?)",
        [(int(t.timestamp()), s, h, k) for t, s, h, k in minutes])
    db.commit()
    db.close()
    return path


def test_finds_the_native_and_the_flatpak_location(tmp_path):
    assert store.find_database(home=tmp_path, environ={}) is None
    flatpak = tmp_path / store.LOCATIONS[1]
    flatpak.parent.mkdir(parents=True)
    flatpak.write_bytes(b"")
    assert store.find_database(home=tmp_path, environ={}) == flatpak
    native = tmp_path / store.LOCATIONS[0]
    native.parent.mkdir(parents=True)
    native.write_bytes(b"")
    # The system package wins if both exist.
    assert store.find_database(home=tmp_path, environ={}) == native
    assert store.find_database(home=tmp_path, environ={
        "PULSUS_DATABASE": str(flatpak)}) == flatpak
    assert store.find_database(home=tmp_path, environ={
        "PULSUS_DATABASE": str(tmp_path / "none")}) is None


def test_snapshot_never_writes_to_amazfish(tmp_path, demo_db):
    """The database stays byte for byte the same, in a read-only
    directory as in the Flatpak (--filesystem=…:ro)."""
    source_dir = tmp_path / "amazfish"
    source_dir.mkdir()
    source = source_dir / "amazfish.kexi"
    source.write_bytes(demo_db.read_bytes())
    before = source.read_bytes()
    source.chmod(stat.S_IRUSR)
    source_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        copy = store.snapshot(source, tmp_path / "cache" / "snapshot.sqlite")
        s = store.Store(copy)
        assert s.has("mi_band_activity")
        s.close()
        assert sorted(os.listdir(source_dir)) == ["amazfish.kexi"]
    finally:
        source_dir.chmod(stat.S_IRWXU)
        source.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert source.read_bytes() == before


def test_snapshot_while_amazfish_holds_a_write_transaction(tmp_path, demo_db):
    source = tmp_path / "amazfish.kexi"
    source.write_bytes(demo_db.read_bytes())
    writer = sqlite3.connect(source)
    writer.execute("BEGIN")
    writer.execute("INSERT INTO mi_band_activity (timestamp, steps) VALUES (1, 5)")
    try:
        copy = store.snapshot(source, tmp_path / "snapshot.sqlite")
        # The uncommitted row is not in the copy.
        db = sqlite3.connect(copy)
        assert db.execute("SELECT count(*) FROM mi_band_activity "
                          "WHERE timestamp = 1").fetchone()[0] == 0
        db.close()
    finally:
        writer.rollback()
        writer.close()


def test_steps_heart_rate_and_gaps(tmp_path):
    day = date(2026, 3, 10)
    t0 = datetime.combine(day, time(8, 0))
    minutes = [(t0 + timedelta(minutes=n), 100, 255 if n % 2 else 60 + n, 80)
               for n in range(40)]
    # The next day: only readings of 0 (no reading).
    minutes += [(t0 + timedelta(days=1, minutes=n), 7, 0, 80) for n in range(3)]
    s = store.Store(make_db(tmp_path / "a.kexi", minutes))
    assert s.daily_steps(day, day + timedelta(days=2)) == {
        day: 4000, day + timedelta(days=1): 21}
    readings = [m.heart_rate for m in s.day_minutes(day)]
    assert readings[:3] == [60, None, 62]
    lo, avg, hi = s.daily_heart_rate_range(day, day)[day]
    assert (lo, hi) == (60, 98)
    # Lowest 30 readings of the 20 valid ones: all of them.
    assert s.daily_resting_heart_rate(day, day)[day] == pytest.approx(79)
    assert day + timedelta(days=1) not in s.daily_resting_heart_rate(
        day, day + timedelta(days=1))


def test_sleep_from_the_watch_minutes(tmp_path):
    night = date(2026, 3, 11)
    bed = datetime.combine(night - timedelta(days=1), time(23, 0))
    minutes = []
    for n in range(8 * 60):
        t = bed + timedelta(minutes=n)
        # Awake 02:00–02:20, and a 10-minute nap in the afternoon before.
        kind = 80 if 180 <= n < 200 else KIND_SLEEP
        minutes.append((t, 0, 55, kind))
    nap = datetime.combine(night - timedelta(days=1), time(15, 0))
    minutes += [(nap + timedelta(minutes=n), 0, 60, KIND_SLEEP) for n in range(10)]
    s = store.Store(make_db(tmp_path / "s.kexi", minutes))
    sleep = s.sleeps(night, night)[night]
    assert sleep.start == bed
    assert sleep.end == bed + timedelta(hours=8)
    assert sleep.asleep == timedelta(hours=8) - timedelta(minutes=20)
    assert sleep.awake == timedelta(minutes=20)
    assert len(sleep.segments) == 2
    assert s.daily_sleep(night, night + timedelta(days=1)) == {night: sleep.asleep}


def test_old_database_without_tables(tmp_path):
    db = sqlite3.connect(tmp_path / "old.kexi")
    db.execute("CREATE TABLE mi_band_activity (id INTEGER, timestamp INTEGER, "
               "steps INTEGER, heartrate INTEGER, raw_kind INTEGER)")
    db.close()
    s = store.Store(tmp_path / "old.kexi")
    today = date.today()
    assert s.daily_stress(today, today) == {}
    assert s.daily_pai(today, today) == {}
    assert s.workouts() == []
    assert s.latest("hrv") is None
    assert s.last_sample() is None


def test_demo_has_every_kind_of_data(demo_db):
    s = store.Store(demo_db)
    today = date.today()
    week = today - timedelta(days=6)
    assert len(s.daily_steps(week, today)) == 7
    assert len(s.sleeps(week, today)) == 7
    for method in ("daily_stress", "daily_spo2", "daily_hrv", "daily_temperature",
                   "daily_pai", "daily_resting_heart_rate"):
        assert getattr(s, method)(week, today), method
    workouts = s.workouts()
    assert workouts and workouts[0].start >= workouts[-1].start
    assert workouts[0].number("distanceMeters") > 0
    assert s.workout(workouts[0].id).id == workouts[0].id
