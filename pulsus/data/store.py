"""Questions about one snapshot of Amazfish's database: minutes, daily
values, readings, nights and workouts (docs/amazfish-data.md). No GTK."""
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

from pulsus.data import sleep as sleep_
from pulsus.data.records import Minute, Workout
from pulsus.data.values import HR_MAX, HR_MIN, KIND_SLEEP, RESTING_READINGS


def day_start(day):
    """Local midnight of `day` as a Unix timestamp."""
    return int(datetime.combine(day, time()).timestamp())


def days(first, last):
    """Every date from `first` to `last`, both included."""
    return [first + timedelta(days=n) for n in range((last - first).days + 1)]


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
        start, end = sleep_.window(night)
        rows = self._rows(
            "SELECT timestamp FROM mi_band_activity WHERE timestamp >= ? "
            "AND timestamp < ? AND raw_kind = ? ORDER BY timestamp",
            int(start.timestamp()), int(end.timestamp()), KIND_SLEEP)
        return sleep_.main_sleep(night, [datetime.fromtimestamp(ts) for (ts,) in rows])

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
