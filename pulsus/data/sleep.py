"""The night's main sleep from the minutes the watch marked as asleep
(docs/amazfish-data.md#sleep). No GTK."""
from datetime import datetime, time, timedelta

from pulsus.data.records import Sleep

# One night runs from noon to noon and belongs to the morning's date.
NIGHT_START = time(12, 0)
# Sleep minutes closer than this belong to the same sleep.
SLEEP_GAP = timedelta(minutes=60)
# Shorter sleeps (naps in the evening) are not the night's sleep.
SLEEP_MIN = timedelta(minutes=20)


def window(night):
    """The minutes that belong to `night` (the morning's date): noon to
    noon."""
    start = datetime.combine(night - timedelta(days=1), NIGHT_START)
    return start, start + timedelta(days=1)


def main_sleep(night, moments):
    """The Sleep of `night` from the asleep minutes `moments` (datetimes,
    oldest first), or None."""
    minute = timedelta(minutes=1)
    # Runs of asleep minutes, then runs joined across short wake-ups.
    segments = []
    for t in moments:
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
    return Sleep(night, main[0][0], main[-1][1], asleep, [(a, b) for a, b in main])
