"""The troubleshooting text of the About dialog: counts and dates of what
Amazfish stored, never readings."""
import sqlite3

from pulsus import data
from pulsus.data.report import report


def test_report_counts_tables_kinds_and_workouts(demo_db):
    store = data.Store(demo_db)
    text = report(demo_db, store)
    rows = sqlite3.connect(demo_db).execute(
        "SELECT count(*) FROM mi_band_activity").fetchone()[0]
    assert f"Amazfish database: {demo_db}" in text
    assert f"mi_band_activity: {rows} (" in text
    assert "120 (asleep):" in text and "118 (charging):" in text
    assert "with 255" in text
    assert f"Workouts: {len(store.workouts())}," in text
    store.close()


def test_report_names_missing_tables_and_empty_workouts(tmp_path):
    db = sqlite3.connect(tmp_path / "old.kexi")
    db.execute("CREATE TABLE mi_band_activity (id INTEGER, timestamp INTEGER, "
               "steps INTEGER, heartrate INTEGER, raw_kind INTEGER)")
    db.execute("CREATE TABLE sports_data (id INTEGER, kind INTEGER, name TEXT, "
               "start_timestamp INTEGER, end_timestamp INTEGER, gpx TEXT)")
    db.close()
    store = data.Store(tmp_path / "old.kexi")
    text = report(tmp_path / "old.kexi", store)
    assert "mi_band_activity: 0" in text
    assert "stress: table missing" in text
    assert "Workouts: 0" in text and "Download Next Activity" in text
    store.close()


def test_report_without_a_database(tmp_path):
    text = report(None, None, data.searched_paths(tmp_path))
    assert "not found" in text
    assert str(tmp_path / data.LOCATIONS[0]) in text
