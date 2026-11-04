"""Amazfish's database, read-only: find it, take a private snapshot, and
answer the questions the pages ask. No GTK.

Amazfish (github.com/piggz/harbour-amazfish) writes one SQLite file
through KDb. Pulsus never opens that file for writing: it copies it with
SQLite's backup API (a consistent snapshot even while Amazfish writes)
into its own cache and reads only the copy. Table and column facts:
docs/amazfish-data.md.
"""
import logging
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from pathlib import Path

log = logging.getLogger("pulsus.store")

# Where Amazfish keeps its database: QStandardPaths::AppDataLocation with
# organisation and application "harbour-amazfish", file "amazfish.kexi".
_RELATIVE = Path("harbour-amazfish") / "harbour-amazfish" / "amazfish.kexi"
LOCATIONS = (
    # Installed as a system package (postmarketOS, Alpine, distributions).
    Path(".local/share") / _RELATIVE,
    # Installed from Flathub (uk.co.piggz.amazfish).
    Path(".var/app/uk.co.piggz.amazfish/data") / _RELATIVE,
)

# Heart rate: 255 means "not measured" (Amazfish's own charts filter
# heartrate < 255); 0 is no reading either.
HR_MIN, HR_MAX = 1, 254
# raw_kind of Zepp OS watches (Amazfit Balance), as Gadgetbridge reads
# them (HuamiExtendedSampleProvider): asleep, not worn, charging.
KIND_SLEEP = 120
KIND_NOT_WORN = 115
KIND_CHARGING = 118
# One night runs from noon to noon and belongs to the morning's date.
NIGHT_START = time(12, 0)
# Sleep minutes closer than this belong to the same sleep.
SLEEP_GAP = timedelta(minutes=60)
# Shorter sleeps (naps in the evening) are not the night's sleep.
SLEEP_MIN = timedelta(minutes=20)
# Resting heart rate (estimate): average of the day's lowest readings.
RESTING_READINGS = 30


def find_database(home=None, environ=None):
    """The Amazfish database, or None. PULSUS_DATABASE overrides the
    search. Inside the Flatpak the home directory is the real one, so
    the same paths work there (docs/amazfish-data.md#flatpak)."""
    environ = os.environ if environ is None else environ
    if environ.get("PULSUS_DATABASE"):
        path = Path(environ["PULSUS_DATABASE"]).expanduser()
        return path if path.is_file() else None
    home = Path(home or Path.home())
    for relative in LOCATIONS:
        path = home / relative
        if path.is_file():
            return path
    return None


def searched_paths(home=None):
    home = Path(home or Path.home())
    return [home / relative for relative in LOCATIONS]


def snapshot(source, target):
    """Copy the database `source` to `target` without writing to the
    source: SQLite's backup API on a read-only connection, so the copy is
    consistent even while Amazfish writes. Returns `target`."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    src = sqlite3.connect(f"{Path(source).resolve().as_uri()}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(tmp)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    tmp.replace(target)
    return target


def day_start(day):
    """Local midnight of `day` as a Unix timestamp."""
    return int(datetime.combine(day, time()).timestamp())


def days(first, last):
    """Every date from `first` to `last`, both included."""
    return [first + timedelta(days=n) for n in range((last - first).days + 1)]


@dataclass
class Minute:
    ts: int
    steps: int
    heart_rate: int | None
    kind: int


@dataclass
class Sleep:
    """One night's main sleep: from the first to the last asleep minute,
    with the asleep stretches in between. The Balance's stored data has
    no sleep stages (docs/amazfish-data.md#sleep)."""
    night: date
    start: datetime
    end: datetime
    asleep: timedelta
    segments: list = field(default_factory=list)  # (start, end) datetimes

    @property
    def in_bed(self):
        return self.end - self.start

    @property
    def awake(self):
        return self.in_bed - self.asleep


@dataclass
class Workout:
    id: int
    kind: int
    name: str
    start: datetime
    end: datetime
    has_track: bool
    meta: dict = field(default_factory=dict)   # key -> (value, unit)

    @property
    def duration(self):
        seconds = self.number("workoutDuration") or self.number("activeSeconds")
        return timedelta(seconds=seconds) if seconds else self.end - self.start

    def number(self, key):
        try:
            return float(self.meta[key][0])
        except (KeyError, TypeError, ValueError):
            return None


class Store:
    """Questions about one snapshot of the database. Every method copes
    with tables that an older Amazfish did not create."""

    def __init__(self, path):
        self.path = Path(path)
        self.db = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro", uri=True)
        self.tables = {name for (name,) in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        self._cache = {}

    def close(self):
        self.db.close()

    def has(self, table):
        return table in self.tables

    def _rows(self, sql, *args):
        return self.db.execute(sql, args).fetchall()

    # --- what is there -------------------------------------------------

    def last_sample(self):
        """Time of the newest minute Amazfish has stored, or None."""
        if not self.has("mi_band_activity"):
            return None
        (ts,), = self._rows("SELECT max(timestamp) FROM mi_band_activity")
        return datetime.fromtimestamp(ts) if ts else None

    def first_day(self):
        if not self.has("mi_band_activity"):
            return None
        (ts,), = self._rows("SELECT min(timestamp) FROM mi_band_activity")
        return datetime.fromtimestamp(ts).date() if ts else None

    # --- minutes -------------------------------------------------------

    def minutes(self, start, end):
        """Stored minutes in [start, end) (datetimes), oldest first."""
        if not self.has("mi_band_activity"):
            return []
        rows = self._rows(
            "SELECT timestamp, steps, heartrate, raw_kind FROM mi_band_activity "
            "WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp",
            int(start.timestamp()), int(end.timestamp()))
        return [Minute(ts, steps or 0,
                       hr if hr is not None and HR_MIN <= hr <= HR_MAX else None,
                       kind or 0)
                for ts, steps, hr, kind in rows]

    def day_minutes(self, day):
        start = datetime.combine(day, time())
        return self.minutes(start, start + timedelta(days=1))

    # --- daily values (date -> number) ---------------------------------

    def _daily(self, key, sql, first, last, *args):
        """Run a "date, value" query over [first, last]; days before today
        are cached (they don't change within one snapshot)."""
        cache = self._cache.setdefault(key, {})
        today = date.today()
        wanted = [d for d in days(first, last) if d not in cache or d >= today]
        if wanted:
            for d in wanted:
                cache.pop(d, None)
            rows = self._rows(sql, day_start(wanted[0]),
                              day_start(wanted[-1] + timedelta(days=1)), *args)
            found = {date.fromisoformat(d): v for d, v in rows if v is not None}
            for d in wanted:
                cache[d] = found.get(d)
        return {d: cache[d] for d in days(first, last) if cache.get(d) is not None}

    _DAY = "date({ts}, 'unixepoch', 'localtime')"

    def daily_steps(self, first, last):
        if not self.has("mi_band_activity"):
            return {}
        day = self._DAY.format(ts="timestamp")
        return self._daily(
            "steps",
            f"SELECT {day} AS d, sum(steps) FROM mi_band_activity "
            "WHERE timestamp >= ? AND timestamp < ? GROUP BY d", first, last)

    def daily_resting_heart_rate(self, first, last):
        """Estimate: the average of each day's RESTING_READINGS lowest
        one-minute readings (docs/amazfish-data.md#heart-rate)."""
        if not self.has("mi_band_activity"):
            return {}
        day = self._DAY.format(ts="timestamp")
        return self._daily(
            "resting",
            f"SELECT d, avg(hr) FROM (SELECT {day} AS d, heartrate AS hr, "
            f"row_number() OVER (PARTITION BY {day} ORDER BY heartrate) AS n "
            "FROM mi_band_activity WHERE timestamp >= ? AND timestamp < ? "
            "AND heartrate BETWEEN ? AND ?) WHERE n <= ? GROUP BY d",
            first, last, HR_MIN, HR_MAX, RESTING_READINGS)

    def daily_heart_rate_range(self, first, last):
        """date -> (lowest, average, highest) one-minute reading."""
        if not self.has("mi_band_activity"):
            return {}
        day = self._DAY.format(ts="timestamp")
        rows = self._rows(
            f"SELECT {day} AS d, min(heartrate), avg(heartrate), max(heartrate) "
            "FROM mi_band_activity WHERE timestamp >= ? AND timestamp < ? "
            "AND heartrate BETWEEN ? AND ? GROUP BY d",
            day_start(first), day_start(last + timedelta(days=1)), HR_MIN, HR_MAX)
        return {date.fromisoformat(d): (lo, avg, hi) for d, lo, avg, hi in rows}

    def _daily_average(self, table, prefix, first, last, where=""):
        if not self.has(table):
            return {}
        day = self._DAY.format(ts=f"{prefix}_timestamp")
        return self._daily(
            table + where,
            f"SELECT {day} AS d, avg({prefix}_value) FROM {table} "
            f"WHERE {prefix}_timestamp >= ? AND {prefix}_timestamp < ? {where} "
            "GROUP BY d", first, last)

    def daily_stress(self, first, last):
        # stress_type 1: measured automatically all day; 2: by hand.
        return self._daily_average("stress", "stress", first, last,
                                   "AND stress_type = 1")

    def daily_spo2(self, first, last):
        return self._daily_average("spo2", "spo2", first, last)

    def daily_hrv(self, first, last):
        return self._daily_average("hrv", "hrv", first, last)

    def daily_temperature(self, first, last):
        return self._daily_average("temperature", "temperature", first, last)

    def daily_pai(self, first, last):
        """date -> (PAI earned that day, PAI of the last 7 days)."""
        if not self.has("pai"):
            return {}
        rows = self._rows(
            "SELECT substr(pai_date, 1, 10), pai_today, pai_total FROM pai "
            "WHERE substr(pai_date, 1, 10) BETWEEN ? AND ? ORDER BY pai_date",
            first.isoformat(), last.isoformat())
        return {date.fromisoformat(d): (today or 0.0, total or 0.0)
                for d, today, total in rows}

    def daily_sleep(self, first, last):
        """night (the morning's date) -> asleep as a timedelta."""
        return {night: s.asleep for night, s in self.sleeps(first, last).items()}

    # --- readings of one day -------------------------------------------

    def readings(self, table, start, end, where=""):
        """(datetime, value) of hrv, spo2, stress or temperature."""
        if not self.has(table):
            return []
        rows = self._rows(
            f"SELECT {table}_timestamp, {table}_value FROM {table} "
            f"WHERE {table}_timestamp >= ? AND {table}_timestamp < ? {where} "
            f"ORDER BY {table}_timestamp",
            int(start.timestamp()), int(end.timestamp()))
        return [(datetime.fromtimestamp(ts), v) for ts, v in rows if v is not None]

    def latest(self, table, where=""):
        """The newest (datetime, value) of a table, or None."""
        if not self.has(table):
            return None
        rows = self._rows(
            f"SELECT {table}_timestamp, {table}_value FROM {table} "
            f"WHERE {table}_value IS NOT NULL {where} "
            f"ORDER BY {table}_timestamp DESC LIMIT 1")
        return (datetime.fromtimestamp(rows[0][0]), rows[0][1]) if rows else None

    # --- sleep ---------------------------------------------------------

    def sleeps(self, first, last):
        """night -> Sleep for the nights first..last that have one."""
        cache = self._cache.setdefault("sleep", {})
        today = date.today()
        result = {}
        for night in days(first, last):
            if night not in cache or night >= today:
                cache[night] = self._sleep(night)
            if cache[night] is not None:
                result[night] = cache[night]
        return result

    def _sleep(self, night):
        if not self.has("mi_band_activity"):
            return None
        start = datetime.combine(night - timedelta(days=1), NIGHT_START)
        rows = self._rows(
            "SELECT timestamp FROM mi_band_activity WHERE timestamp >= ? "
            "AND timestamp < ? AND raw_kind = ? ORDER BY timestamp",
            int(start.timestamp()), int((start + timedelta(days=1)).timestamp()),
            KIND_SLEEP)
        # Runs of asleep minutes, then runs joined across short wake-ups.
        minute = timedelta(minutes=1)
        segments = []
        for (ts,) in rows:
            t = datetime.fromtimestamp(ts)
            if segments and t - segments[-1][1] <= minute:
                segments[-1][1] = t + minute
            else:
                segments.append([t, t + minute])
        sleeps = []
        for seg in segments:
            if sleeps and seg[0] - sleeps[-1][-1][1] <= SLEEP_GAP:
                sleeps[-1].append(seg)
            else:
                sleeps.append([seg])
        if not sleeps:
            return None
        main = max(sleeps, key=lambda s: sum((b - a for a, b in s), timedelta()))
        asleep = sum((b - a for a, b in main), timedelta())
        if asleep < SLEEP_MIN:
            return None
        return Sleep(night, main[0][0], main[-1][1], asleep,
                     [(a, b) for a, b in main])

    # --- workouts ------------------------------------------------------

    def workouts(self, limit=None):
        """Newest first, with their meta data."""
        if not self.has("sports_data"):
            return []
        sql = ("SELECT id, kind, name, start_timestamp, end_timestamp, "
               "gpx IS NOT NULL AND length(gpx) > 0 FROM sports_data "
               "ORDER BY start_timestamp DESC")
        if limit:
            sql += f" LIMIT {int(limit)}"
        result = [Workout(i, kind or 0, name or "", datetime.fromtimestamp(s or 0),
                          datetime.fromtimestamp(e or s or 0), bool(track))
                  for i, kind, name, s, e, track in self._rows(sql)]
        if result and self.has("sports_meta"):
            by_id = {w.id: w for w in result}
            marks = ",".join("?" * len(by_id))
            for sport, key, value, unit in self._rows(
                    "SELECT sport_id, key, value, unit FROM sports_meta "
                    f"WHERE sport_id IN ({marks})", *by_id):
                by_id[sport].meta[key] = (value, unit or "")
        return result

    def workout(self, workout_id):
        for w in self.workouts():
            if w.id == workout_id:
                return w
        return None
