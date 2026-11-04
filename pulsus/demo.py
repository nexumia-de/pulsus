"""The demo database: a made-up person with an Amazfit Balance, 120 days
up to now, in the table layout Amazfish writes (docs/amazfish-data.md).
For screenshots and tests, never real health data (PULSUS_DEMO=1).

The values come from a seeded random generator, so every run gives the
same person; the dates follow today, so the Today page is never empty.
"""
import math
import random
import sqlite3
from datetime import datetime, time, timedelta
from pathlib import Path

from pulsus.data.values import KIND_CHARGING, KIND_SLEEP

DAYS = 120
# Ordinary daytime raw_kind values; Pulsus only reads 115, 118 and 120.
KIND_STILL = 80
KIND_WALK = 90
# Amazfish's ActivityKind values for the workouts.
RUNNING = 0x10
WALKING = 0x20
CYCLING = 0x80

SCHEMA = """
CREATE TABLE mi_band_activity (id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp INTEGER, timestamp_dt TEXT, device_id INTEGER, user_id INTEGER,
  raw_intensity INTEGER, steps INTEGER, raw_kind INTEGER, heartrate INTEGER);
CREATE INDEX mi_band_activity_timestamp ON mi_band_activity (timestamp);
CREATE TABLE info_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER,
  timestamp_dt TEXT, key INTEGER, value INTEGER);
CREATE TABLE sports_data (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
  version INTEGER, start_timestamp INTEGER, start_timestamp_dt TEXT,
  end_timestamp INTEGER, end_timestamp_dt TEXT, kind INTEGER,
  base_longitude REAL, base_latitude REAL, base_altitude REAL,
  device_id INTEGER, user_id INTEGER, gpx TEXT);
CREATE TABLE sports_meta (id INTEGER PRIMARY KEY AUTOINCREMENT,
  sport_id INTEGER, key TEXT, value TEXT, unit TEXT);
CREATE TABLE pai (id INTEGER PRIMARY KEY AUTOINCREMENT, pai_date TEXT,
  pai_low REAL, pai_moderate REAL, pai_high REAL, pai_low_time INTEGER,
  pai_moderate_time INTEGER, pai_high_time INTEGER, pai_today REAL,
  pai_total REAL);
CREATE TABLE hrv (hrv_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hrv_timestamp INTEGER, hrv_timestamp_dt TEXT, hrv_value INTEGER);
CREATE TABLE spo2 (spo2_id INTEGER PRIMARY KEY AUTOINCREMENT,
  spo2_timestamp INTEGER, spo2_timestamp_dt TEXT, spo2_automatic INTEGER,
  spo2_value INTEGER);
CREATE TABLE spo2sleep (spo2sleep_id INTEGER PRIMARY KEY AUTOINCREMENT,
  spo2sleep_timestamp INTEGER, spo2sleep_timestamp_dt TEXT,
  spo2sleep_value INTEGER, spo2sleep_duration INTEGER, spo2sleep_high TEXT,
  spo2sleep_low TEXT, spo2sleep_quality TEXT);
CREATE TABLE temperature (temperature_id INTEGER PRIMARY KEY AUTOINCREMENT,
  temperature_timestamp INTEGER, temperature_timestamp_dt TEXT,
  temperature_value REAL, temperature_location TEXT, temperature_type TEXT);
CREATE TABLE stress (stress_id INTEGER PRIMARY KEY AUTOINCREMENT,
  stress_timestamp INTEGER, stress_timestamp_dt TEXT, stress_value INTEGER,
  stress_type INTEGER);
"""


def _iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


def create(path, now=None, days=DAYS, seed=7):
    """Write the demo database to `path` and return it."""
    now = (now or datetime.now()).replace(second=0, microsecond=0)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    rng = random.Random(seed)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    minutes, stress, hrv, spo2, temps, pai = [], [], [], [], [], []
    first = now.date() - timedelta(days=days - 1)
    pai_days = []
    # Nights: (bed, wake), the evening before the first day included;
    # later on Friday and Saturday.
    nights = []
    for n in range(-1, days):
        evening = first + timedelta(days=n)
        late = evening.weekday() >= 4
        bed = datetime.combine(evening, time(23, 0)) + timedelta(
            minutes=rng.randint(-40, 40) + (40 if late else 0))
        wake = datetime.combine(evening + timedelta(days=1), time(6, 40)) + timedelta(
            minutes=rng.randint(-25, 30) + (75 if late else 0))
        nights.append((bed, wake))
    for n in range(days):
        day = first + timedelta(days=n)
        weekend = day.weekday() >= 5
        # A slow fitness gain over the months: resting rate drifts down.
        fitness = n / days
        rest = 60 - 4 * fitness + rng.uniform(-2, 2)
        tonight = nights[n:n + 2]
        workout = None
        if n % 3 == 1 or (weekend and n % 2 == 0):
            kind = (RUNNING, WALKING, CYCLING)[n % 3] if weekend else RUNNING
            start = datetime.combine(day, time(18, 10) if not weekend else time(10, 0))
            start += timedelta(minutes=rng.randint(-20, 20))
            length = rng.randint(28, 48) if kind == RUNNING else rng.randint(45, 80)
            workout = (kind, start, start + timedelta(minutes=length))
        walks = [(datetime.combine(day, time(h, rng.randint(0, 40))), rng.randint(8, 25))
                 for h in (8, 12, 17) if rng.random() < 0.85]
        if weekend:
            walks.append((datetime.combine(day, time(15, 0)), rng.randint(30, 70)))
        charging = datetime.combine(day, time(20, rng.randint(0, 50)))
        active = 0
        awake_until = None
        for m in range(24 * 60):
            t = datetime.combine(day, time()) + timedelta(minutes=m)
            if t > now:
                break
            asleep = any(bed <= t < wake for bed, wake in tonight)
            hr, steps, kind, intensity = None, 0, KIND_STILL, rng.randint(0, 20)
            if charging <= t < charging + timedelta(minutes=35):
                kind, hr = KIND_CHARGING, None
            elif asleep:
                kind = KIND_SLEEP
                # Wake-ups now and then, a few minutes long.
                if awake_until is None and rng.random() < 0.004:
                    awake_until = t + timedelta(minutes=rng.randint(4, 18))
                if awake_until is not None:
                    if t < awake_until:
                        kind = KIND_STILL
                    else:
                        awake_until = None
                hr = rest - 4 + rng.gauss(0, 1.5) + 3 * math.sin(m / 40)
            elif workout and workout[1] <= t < workout[2]:
                progress = (t - workout[1]) / (workout[2] - workout[1])
                peak = 158 if workout[0] == RUNNING else 122
                hr = peak - 25 * math.exp(-8 * progress) + rng.gauss(0, 3)
                steps = rng.randint(150, 170) if workout[0] == RUNNING else \
                    rng.randint(95, 115) if workout[0] == WALKING else 0
                kind, intensity = KIND_WALK, rng.randint(120, 220)
                active += 1
            elif any(s <= t < s + timedelta(minutes=length) for s, length in walks):
                hr = rest + 35 + rng.gauss(0, 5)
                steps, kind, intensity = rng.randint(85, 118), KIND_WALK, rng.randint(60, 140)
                active += 1
            else:
                hr = rest + 18 + 8 * math.sin(m / 90) + rng.gauss(0, 4)
                if 7 * 60 <= m <= 22 * 60 and rng.random() < 0.25:
                    steps = rng.randint(2, 30)
            if hr is not None and rng.random() < 0.06:
                hr = None              # the watch missed a reading
            minutes.append((int(t.timestamp()), _iso(t), 1, 1, intensity, steps,
                            kind, 255 if hr is None else int(round(hr))))
            if not asleep and kind != KIND_CHARGING and m % 30 == 0 and m > 6 * 60:
                level = 28 + 14 * math.sin(m / 200) + (12 if day.weekday() < 5 else 0)
                stress.append((int(t.timestamp()), _iso(t),
                               max(1, min(99, int(level + rng.gauss(0, 8)))), 1))
            if not asleep and kind != KIND_CHARGING and m % 120 == 30 and m > 8 * 60:
                spo2.append((int(t.timestamp()), _iso(t), 1, rng.choice((96, 97, 97, 98, 98, 99))))
        reading = datetime.combine(day, time(5, 30))
        if reading <= now:
            hrv.append((int(reading.timestamp()), _iso(reading),
                        int(42 + 10 * fitness + rng.gauss(0, 5))))
            temps.append((int(reading.timestamp()), _iso(reading),
                          round(34.2 + rng.gauss(0, 0.25), 2), "wrist", "skin"))
        if workout and workout[2] <= now:
            _workout(db, rng, *workout)
        earned = min(30.0, active * (0.55 if workout and workout[0] == RUNNING else 0.15))
        pai_days.append(earned)
        total = sum(pai_days[-7:])
        pai.append((day.isoformat(), earned * 0.2, earned * 0.5, earned * 0.3,
                    active // 3, active // 2, active // 4, round(earned, 1),
                    round(total, 1)))
    db.executemany(
        "INSERT INTO mi_band_activity (timestamp, timestamp_dt, device_id, user_id, "
        "raw_intensity, steps, raw_kind, heartrate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        minutes)
    db.executemany("INSERT INTO stress (stress_timestamp, stress_timestamp_dt, "
                   "stress_value, stress_type) VALUES (?, ?, ?, ?)", stress)
    db.executemany("INSERT INTO hrv (hrv_timestamp, hrv_timestamp_dt, hrv_value) "
                   "VALUES (?, ?, ?)", hrv)
    db.executemany("INSERT INTO spo2 (spo2_timestamp, spo2_timestamp_dt, "
                   "spo2_automatic, spo2_value) VALUES (?, ?, ?, ?)", spo2)
    db.executemany("INSERT INTO temperature (temperature_timestamp, "
                   "temperature_timestamp_dt, temperature_value, "
                   "temperature_location, temperature_type) VALUES (?, ?, ?, ?, ?)",
                   temps)
    db.executemany("INSERT INTO pai (pai_date, pai_low, pai_moderate, pai_high, "
                   "pai_low_time, pai_moderate_time, pai_high_time, pai_today, "
                   "pai_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", pai)
    db.execute("INSERT INTO info_log (timestamp, timestamp_dt, key, value) "
               "VALUES (?, ?, 2, 64)", (int(now.timestamp()), _iso(now)))
    db.commit()
    db.close()
    return path


NAMES = {RUNNING: "Running", WALKING: "Walking", CYCLING: "Cycling"}


def _workout(db, rng, kind, start, end):
    seconds = int((end - start).total_seconds())
    speed = {RUNNING: rng.uniform(2.7, 3.2), WALKING: rng.uniform(1.3, 1.6),
             CYCLING: rng.uniform(5.5, 7.0)}[kind]
    distance = speed * seconds
    peak = 158 if kind == RUNNING else 122
    name = f"{NAMES[kind]}-{start:%Y%m%d-%H%M}"
    cur = db.execute(
        "INSERT INTO sports_data (name, version, start_timestamp, start_timestamp_dt, "
        "end_timestamp, end_timestamp_dt, kind, base_longitude, base_latitude, "
        "base_altitude, device_id, user_id, gpx) VALUES (?, 1, ?, ?, ?, ?, ?, "
        "?, ?, ?, 1, 1, ?)",
        (name, int(start.timestamp()), _iso(start), int(end.timestamp()), _iso(end),
         kind, 0.0, 0.0, 0.0, ""))
    meta = [
        ("distanceMeters", f"{distance:.0f}", "meters"),
        ("workoutDuration", str(seconds), "seconds"),
        ("activeSeconds", str(seconds), "seconds"),
        ("averageHR", str(peak - 12 + rng.randint(-3, 3)), "bpm"),
        ("maxHR", str(peak + rng.randint(4, 10)), "bpm"),
        ("minHeartRate", str(peak - 40), "bpm"),
        ("caloriesBurnt", str(int(seconds / 60 * (11 if kind == RUNNING else 6))), "calories"),
    ]
    if kind != CYCLING:
        meta += [("paceAvg", f"{1000 / speed / 60:.2f}", "min_km"),
                 ("steps", str(int(seconds / 60 * (160 if kind == RUNNING else 105))), "steps")]
    db.executemany("INSERT INTO sports_meta (sport_id, key, value, unit) "
                   "VALUES (?, ?, ?, ?)", [(cur.lastrowid, *m) for m in meta])
