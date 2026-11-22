"""The GPS track of a workout: finding the file Amazfish wrote, reading
its points, length and kilometre times; and the store's side of it."""
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from pulsus import data, demo
from pulsus.data import track
from pulsus.data.track import Point

# The shape Amazfish's AbstractActivityDetailParser::toText writes.
GPX = """<?xml version="1.0" standalone="yes"?>
<?xml-stylesheet type="text/xsl" href="details.xsl"?>
<gpx
version="1.1"
creator="Amazfish for SailfishOS"
xmlns="http://www.topografix.com/GPX/1/1"
xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v2">
<metadata>
  <name>Running-20260310-0730</name>
</metadata>
<trk>
<trkseg>
<trkpt lat="52.0" lon="13.0">
  <ele>40</ele>
  <time>2026-03-10T06:30:00Z</time>
  <extensions>
    <gpxtpx:TrackPointExtension>
      <gpxtpx:hr>120</gpxtpx:hr>
    </gpxtpx:TrackPointExtension>
  </extensions>
</trkpt>
<trkpt lat="52.001" lon="13.0">
  <ele>41</ele>
  <time>2026-03-10T07:30:40+01:00</time>
</trkpt>
<trkpt lat="999" lon="13.0"><time>2026-03-10T06:31:00Z</time></trkpt>
<trkpt lat="52.002" lon="13.0"></trkpt>
</trkseg>
</trk>
</gpx>
"""


def test_parse_reads_points_times_and_skips_invalid_ones():
    points = track.parse(GPX)
    assert [(p.lat, p.lon) for p in points] == [(52.0, 13.0), (52.001, 13.0),
                                                (52.002, 13.0)]
    assert points[0].time == datetime(2026, 3, 10, 6, 30, tzinfo=timezone.utc)
    assert (points[1].time - points[0].time).total_seconds() == 40
    assert points[2].time is None
    assert track.length(points) == pytest.approx(222.4, abs=0.5)


def test_locate_reads_only_amazfishs_folder(tmp_path):
    folder = tmp_path / "amazfish"
    folder.mkdir()
    (folder / "Running-1.gpx").write_text(GPX)
    elsewhere = tmp_path / "Laufhelden"
    elsewhere.mkdir()
    (elsewhere / "Walking-2.gpx").write_text(GPX)
    # Amazfish stores the path of the .tcx twin, as it saw it.
    assert track.locate("/home/other/.local/share/x/Running-1.tcx", folder) \
        == folder / "Running-1.gpx"
    assert track.locate(str(folder / "Running-1.gpx"), folder) == folder / "Running-1.gpx"
    # A track outside the folder is not read, a missing one is None.
    assert track.locate(str(elsewhere / "Walking-2.tcx"), folder) is None
    assert track.locate("../Laufhelden/Walking-2.tcx", folder) is None
    assert track.locate("", folder) is None
    assert track.locate(None, folder) is None
    # Old rows may hold the GPX text itself.
    assert track.locate(GPX, folder) == GPX.strip()
    assert len(track.read(track.locate(GPX, folder))) == 3


def test_read_copes_with_a_broken_file(tmp_path):
    broken = tmp_path / "b.gpx"
    broken.write_text("<gpx><trk>")
    assert track.read(broken) == []
    assert track.read(tmp_path / "gone.gpx") == []


def line(metres_total, seconds_total, step=10):
    """Points due north at constant speed, one every `step` seconds."""
    start = datetime(2026, 3, 10, 7, 0, tzinfo=timezone.utc)
    per_degree = 111195.0
    return [Point(52.0 + metres_total * t / seconds_total / per_degree, 13.0,
                  start + timedelta(seconds=t))
            for t in range(0, seconds_total + 1, step)]


def test_splits_give_each_kilometre_its_time():
    # 2.5 km in 750 s: 300 s per kilometre.
    parts = track.splits(line(2500, 750))
    assert [round(m) for m, _ in parts] == [1000, 1000, 500]
    assert [s for _, s in parts] == pytest.approx([300, 300, 150], abs=1)


def test_splits_with_one_long_step_and_without_times():
    start = datetime(2026, 3, 10, 7, 0, tzinfo=timezone.utc)
    far = [Point(52.0, 13.0, start),
           Point(52.0 + 2200 / 111195.0, 13.0, start + timedelta(seconds=660))]
    parts = track.splits(far)
    assert [round(m) for m, _ in parts] == [1000, 1000, 200]
    assert [s for _, s in parts] == pytest.approx([300, 300, 60], abs=1)
    assert track.splits([Point(52.0, 13.0), Point(52.01, 13.0)]) == []
    assert track.splits(far[:1]) == []


def test_store_finds_the_demo_tracks_and_the_highest_heart_rate(tmp_path):
    path = demo.create(tmp_path / "amazfish.kexi", days=10)
    store = data.Store(path)
    workouts = store.workouts()
    assert workouts and all(w.has_track for w in workouts)
    points = store.track(workouts[0].id)
    assert len(points) > 100 and points[0].time is not None
    # A loop: back where it started, about as long as the watch says.
    assert track.metres(points[0], points[-1]) < 30
    assert track.length(points) == pytest.approx(
        workouts[0].number("distanceMeters"), rel=0.25)
    assert store.track(-1) == []
    highest = max(w.number("maxHR") for w in workouts)
    assert store.highest_heart_rate() >= highest
    store.close()

    # The snapshot lives elsewhere: without Amazfish's folder, no track.
    copy = data.snapshot(path, tmp_path / "cache" / "snapshot.sqlite")
    away = data.Store(copy)
    assert not any(w.has_track for w in away.workouts())
    near = data.Store(copy, folder=tmp_path)
    assert all(w.has_track for w in near.workouts())
    for s in (away, near):
        s.close()


def test_store_without_heart_rate_has_no_highest(tmp_path):
    db = sqlite3.connect(tmp_path / "e.kexi")
    db.executescript(demo.SCHEMA)
    db.close()
    store = data.Store(tmp_path / "e.kexi")
    assert store.highest_heart_rate() is None
    store.close()
