"""Heart-rate zones: limits from the maximum heart rate and the minutes
of a workout in each."""
from pulsus.workout import zones


def test_limits_are_tenths_of_the_maximum():
    found = zones.limits(200)
    assert [(z.number, z.low, z.high) for z in found] == [
        (1, 100, 119), (2, 120, 139), (3, 140, 159), (4, 160, 179), (5, 180, None)]
    assert found[0].percent == "50–60 %" and found[4].percent == "from 90 %"
    assert found[2].beats == "140–159 bpm" and found[4].beats == "from 180 bpm"


def test_every_minute_lands_in_one_zone_or_below():
    readings = [90, 99, 100, 119, 120, 150, 179, 180, 210]
    found, below = zones.time_in_zones(readings, 200)
    assert below == 2
    assert [z.minutes for z in found] == [2, 1, 1, 1, 2]
    assert below + sum(z.minutes for z in found) == len(readings)


def test_limits_have_no_gaps_for_an_odd_maximum():
    found = zones.limits(187)
    for lower, upper in zip(found, found[1:]):
        assert lower.high + 1 == upper.low
