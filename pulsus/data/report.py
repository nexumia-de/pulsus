"""What is in Amazfish's database, as text for the About dialog's
troubleshooting page: where the file is, how many rows each table has
and over which days, and how the values Pulsus depends on are spread
(docs/amazfish-data.md#checking-on-the-phone). Counts and dates only, no
readings. No GTK."""
from datetime import datetime

from pulsus.data.values import HR_MAX, HR_MIN, KIND_CHARGING, KIND_NOT_WORN, KIND_SLEEP

# table -> its Unix timestamp column.
TABLES = {
    "mi_band_activity": "timestamp",
    "stress": "stress_timestamp",
    "hrv": "hrv_timestamp",
    "spo2": "spo2_timestamp",
    "temperature": "temperature_timestamp",
    "pai": None,
    "sports_data": "start_timestamp",
    "sports_meta": None,
}
KINDS = {KIND_SLEEP: "asleep", KIND_NOT_WORN: "not worn", KIND_CHARGING: "charging"}


def _day(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"


def report(path, store, searched=()):
    """`path`: Amazfish's database or None; `store`: the Store on its
    snapshot or None; `searched`: where Pulsus looked."""
    lines = ["Counts and dates only. This text stays on this device unless "
             "you copy it.", ""]
    if store is None:
        lines.append("Amazfish database: not found")
        lines += [f"  looked for {p}" for p in searched]
        return "\n".join(lines)
    lines.append(f"Amazfish database: {path}")
    lines.append("")
    lines.append("Rows per table (first day to last day):")
    for table, column in TABLES.items():
        if not store.has(table):
            lines.append(f"  {table}: table missing")
            continue
        (count,), = store.db.execute(f"SELECT count(*) FROM {table}")
        line = f"  {table}: {count}"
        if count and column:
            (low, high), = store.db.execute(
                f"SELECT min({column}), max({column}) FROM {table}")
            line += f" ({_day(low)} to {_day(high)})"
        lines.append(line)
    if store.has("mi_band_activity"):
        lines += ["", "Minutes by raw_kind (Watch Health reads "
                      f"{KIND_SLEEP} as asleep):"]
        for kind, count in store.db.execute(
                "SELECT raw_kind, count(*) FROM mi_band_activity "
                "GROUP BY raw_kind ORDER BY count(*) DESC LIMIT 12"):
            name = f" ({KINDS[kind]})" if kind in KINDS else ""
            lines.append(f"  {kind}{name}: {count}")
        (zero, none, valid), = store.db.execute(
            "SELECT sum(heartrate = 0), sum(heartrate = 255), "
            "sum(heartrate BETWEEN ? AND ?) FROM mi_band_activity", (HR_MIN, HR_MAX))
        lines += ["", f"Heart rate minutes: {valid or 0} with a reading, "
                      f"{none or 0} with 255, {zero or 0} with 0"]
    if store.has("sports_data"):
        workouts = store.workouts()
        tracks = sum(1 for w in workouts if w.has_track)
        lines += ["", f"Workouts: {len(workouts)}, {tracks} with a GPS track "
                      "Watch Health can read"]
        if not workouts:
            lines.append("  Amazfish downloads workouts only when asked: Sports, "
                         "then Download Next Activity, once per workout.")
    return "\n".join(lines)
