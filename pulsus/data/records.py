"""What the store hands to the pages: a stored minute, a night's sleep,
a workout. No GTK."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


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
