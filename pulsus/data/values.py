"""What Amazfish's stored values mean (docs/amazfish-data.md). No GTK."""

# Heart rate: 255 means "not measured" (Amazfish's own charts filter
# heartrate < 255); 0 is no reading either.
HR_MIN, HR_MAX = 1, 254
# raw_kind of Zepp OS watches (Amazfit Balance), as Gadgetbridge reads
# them (HuamiExtendedSampleProvider): asleep, not worn, charging.
KIND_SLEEP = 120
KIND_NOT_WORN = 115
KIND_CHARGING = 118
# Resting heart rate (estimate): average of the day's lowest readings.
RESTING_READINGS = 30
