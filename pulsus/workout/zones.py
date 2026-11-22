"""Heart-rate zones of a workout: the time spent in each tenth of the
maximum heart rate (docs/visualisation.md#workout). No GTK."""
from dataclasses import dataclass

# Share of the maximum heart rate where each zone starts; zone 5 has no
# upper end. The common five-zone convention, also used by the watch.
STARTS = (0.5, 0.6, 0.7, 0.8, 0.9)


@dataclass
class Zone:
    number: int          # 1..5
    low: int             # bpm, included
    high: int | None     # bpm, included; None for the last zone
    minutes: int = 0

    @property
    def percent(self):
        start = round(STARTS[self.number - 1] * 100)
        return f"{start}–{start + 10} %" if self.high is not None else f"from {start} %"

    @property
    def beats(self):
        if self.high is None:
            return f"from {self.low} bpm"
        return f"{self.low}–{self.high} bpm"


def limits(maximum):
    """The five zones for a maximum heart rate, without times."""
    lows = [round(maximum * share) for share in STARTS]
    return [Zone(n + 1, low, lows[n + 1] - 1 if n + 1 < len(lows) else None)
            for n, low in enumerate(lows)]


def time_in_zones(readings, maximum):
    """`readings`: one heart rate per stored minute of the workout. Returns
    (zones with their minutes, minutes below zone 1)."""
    zones = limits(maximum)
    below = 0
    for value in readings:
        zone = next((z for z in reversed(zones) if value >= z.low), None)
        if zone is None:
            below += 1
        else:
            zone.minutes += 1
    return zones, below
