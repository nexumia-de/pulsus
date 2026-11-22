"""The GPS track of a workout: where Amazfish keeps it, its points, its
length and the time of each kilometre (docs/amazfish-data.md#gps-track).
No GTK."""
import logging
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

log = logging.getLogger("pulsus.track")

# Amazfish's files are small (one point a second); anything larger is
# not a track.
MAX_BYTES = 20 * 1024 * 1024
EARTH_RADIUS = 6371000.0


@dataclass
class Point:
    lat: float
    lon: float
    time: datetime | None = None


def locate(value, folder):
    """What `sports_data.gpx` points to: the GPX text itself (a string
    starting with "<"), the path of the GPX file in `folder`, or None.

    Amazfish writes <name>.gpx and <name>.tcx next to its database and
    stores the path of the .tcx file; only the name is used, and only
    `folder` is read (the one folder the Flatpak may read)."""
    value = (value or "").strip()
    if not value:
        return None
    if value.startswith("<"):
        return value
    if folder is None:
        return None
    path = Path(folder) / (PurePosixPath(value).stem + ".gpx")
    return path if path.is_file() else None


def read(found):
    """The points of what `locate` found; [] if it can't be read."""
    try:
        if isinstance(found, Path):
            if found.stat().st_size > MAX_BYTES:
                return []
            found = found.read_text(encoding="utf-8", errors="replace")
        return parse(found)
    except (OSError, ElementTree.ParseError, ValueError) as e:
        log.info("can't read the track: %s", e)
        return []


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def parse(text):
    """The track points of a GPX text, in order. Points without valid
    coordinates are left out; a missing time stays None."""
    points = []
    for element in ElementTree.fromstring(text).iter():
        if _local(element.tag) != "trkpt":
            continue
        try:
            lat, lon = float(element.get("lat")), float(element.get("lon"))
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        when = None
        for child in element:
            if _local(child.tag) == "time" and child.text:
                try:
                    when = datetime.fromisoformat(child.text.strip())
                except ValueError:
                    when = None
        points.append(Point(lat, lon, when))
    return points


def metres(a, b):
    """Great-circle distance between two points."""
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(h))


def length(points):
    return sum(metres(a, b) for a, b in zip(points, points[1:]))


def splits(points, every=1000.0):
    """[(metres, seconds)] for each full `every` metres and the rest:
    how long each kilometre took, pauses included. [] if a point has no
    time."""
    if len(points) < 2 or any(p.time is None for p in points):
        return []
    result = []
    done = 0.0                       # metres since the last split
    started = points[0].time
    for a, b in zip(points, points[1:]):
        step = metres(a, b)
        while step > 0 and done + step >= every:
            part = (every - done) / step
            crossing = a.time + (b.time - a.time) * part
            result.append((every, (crossing - started).total_seconds()))
            started = crossing
            a = Point(a.lat + (b.lat - a.lat) * part, a.lon + (b.lon - a.lon) * part,
                      crossing)
            step -= every - done
            done = 0.0
        done += step
    rest = (points[-1].time - started).total_seconds()
    if done >= 1 and rest > 0:
        result.append((done, rest))
    return result
