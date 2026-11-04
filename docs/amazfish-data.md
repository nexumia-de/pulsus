---
type: Reference
title: Amazfish's data as Pulsus reads it
description: Where Amazfish keeps its SQLite database, which tables and columns Pulsus reads and what their values mean for the Amazfit Balance, how Pulsus reads without writing, and what the stored data lacks.
tags: [amazfish, database, sqlite, zepp-os, amazfit-balance, sleep, heart-rate]
resource: ../pulsus/data/
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
sources:
  - id: af-schema
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/daemon/src/deviceinterface.cpp
    title: Amazfish daemon/src/deviceinterface.cpp (createTables, database file name)
  - id: af-app
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/daemon/src/harbour-amazfish-daemon.cpp
    title: Amazfish daemon main (organisation and application name)
  - id: af-zepp
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/daemon/src/devices/huami/zepposdevice.cpp
    title: Amazfish ZeppOSDevice::supportedDataTypes
  - id: af-fetch
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/daemon/src/operations/huami/activityfetchoperation.cpp
    title: Amazfish ActivityFetchOperation::saveSamples (one row per minute)
  - id: af-ui
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/ui/src/datasource.cpp
    title: Amazfish ui/src/datasource.cpp (heartrate < 255, its sleep calculation)
  - id: af-summary
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/daemon/src/devices/huami/zeppos/zepposactivitysummaryparser.cpp
    title: Amazfish ZeppOsActivitySummaryParser (workout meta keys and units)
  - id: af-kind
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/lib/src/activitykind.h
    title: Amazfish lib/src/activitykind.h (workout kinds)
  - id: gb-kind
    resource: https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/351b0389e660b9e001da2573dcf4395fba4513d5/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/devices/huami/HuamiExtendedSampleProvider.java
    title: Gadgetbridge HuamiExtendedSampleProvider (raw kinds 115, 118, 120 of Zepp OS watches)
  - id: gb-fetch
    resource: https://codeberg.org/Freeyourgadget/Gadgetbridge/src/commit/351b0389e660b9e001da2573dcf4395fba4513d5/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huami/operations/fetch
    title: Gadgetbridge Huami fetch operations (sleep sessions, resting heart rate)
  - id: fh
    resource: https://github.com/flathub/uk.co.piggz.amazfish
    title: Amazfish on Flathub (uk.co.piggz.amazfish)
---

# Source

Read from Amazfish's source at commit `730b542` (2026-11-04) and, for
the meaning of Zepp OS values, Gadgetbridge at `351b038` (2026-11-04),
both cloned with git. Facts only: Pulsus contains no code of either
(GPL-3.0, AGPL-3.0). **Not yet checked against the owner's database**
(issue in M1).

# Where the database is

Amazfish writes one SQLite file through KDb, `amazfish.kexi`, in
`QStandardPaths::AppDataLocation`[^af-schema]; organisation and
application name are both `harbour-amazfish`[^af-app]. So:

| Amazfish installed as | Path |
|---|---|
| System package (postmarketOS, Alpine, distributions) | `~/.local/share/harbour-amazfish/harbour-amazfish/amazfish.kexi` |
| Flathub, `uk.co.piggz.amazfish`[^fh] | `~/.var/app/uk.co.piggz.amazfish/data/harbour-amazfish/harbour-amazfish/amazfish.kexi` |

Pulsus tries them in this order (`data.find_database`);
`PULSUS_DATABASE=<file>` overrides the search.

## Flatpak

The manifest grants read-only access to exactly these two folders
(`--filesystem=~/.local/share/harbour-amazfish:ro` and
`--filesystem=~/.var/app/uk.co.piggz.amazfish/data/harbour-amazfish:ro`).
Inside the sandbox the home directory is the real one, so the same paths
work. Pulsus has no network and no D-Bus names.

## Reading safely

Pulsus never opens Amazfish's file for writing. It copies it with
SQLite's backup API from a `mode=ro` connection into
`~/.cache/pulsus/amazfish-snapshot.sqlite` and reads only the copy
(`data.snapshot`): the copy is consistent even while Amazfish writes,
uncommitted rows are left out (tests in `tests/test_data.py`). A file
monitor on the folder takes a new snapshot 3 s after Amazfish stopped
writing, and again when the window comes back to the front
(`data/source.py`). Older Amazfish versions lack some tables; every query
checks first.

# What the Balance delivers

`ZeppOSDevice::supportedDataTypes` lists activity, GPS tracks, heart
rate, PAI, SpO₂, stress, HRV and temperature[^af-zepp]. **No sleep
sessions, no resting or maximum heart rate, no breathing rate**: the
watch has them, Gadgetbridge fetches them[^gb-fetch], Amazfish does not
(issue for an Amazfish change in the backlog).

# Tables

All timestamps are Unix seconds (`*_timestamp`); the `*_dt` text
columns are not used.

| Table | Columns Pulsus reads | Meaning |
|---|---|---|
| `mi_band_activity` | `timestamp`, `steps`, `heartrate`, `raw_kind` | One row per minute[^af-fetch]: steps in that minute, heart rate, what the watch thought you did |
| `stress` | `stress_timestamp`, `stress_value`, `stress_type` | 0–100; type 1 automatic, 2 measured by hand |
| `hrv` | `hrv_timestamp`, `hrv_value` | ms |
| `spo2` | `spo2_timestamp`, `spo2_value` | % |
| `temperature` | `temperature_timestamp`, `temperature_value` | °C (skin) |
| `pai` | `pai_date`, `pai_today`, `pai_total` | PAI earned that day and of the last 7 days |
| `sports_data` | `id`, `kind`, `name`, `start_timestamp`, `end_timestamp`, `gpx` | Workouts; `kind` is Amazfish's `ActivityKind`[^af-kind], `name` like `Running-20261104-0730` |
| `sports_meta` | `sport_id`, `key`, `value`, `unit` | Workout numbers: `distanceMeters`, `workoutDuration` (s), `averageHR`, `maxHR`, `caloriesBurnt`, `paceAvg` (min/km), `steps`, …[^af-summary] |

Not read yet: `spo2sleep`, `info_log` (battery), the GPX track.

## Heart rate

`heartrate` 255 means "not measured" (Amazfish's own charts keep
`heartrate < 255`[^af-ui]); Pulsus also drops 0. Missing minutes stay
gaps in the charts. Amazfish stores no resting heart rate, so Pulsus
**estimates** it: the average of the day's 30 lowest one-minute readings
(`data/values.py`). These are mostly sleeping minutes, so the
estimate runs a few beats below the watch's own resting value; it is
labelled as an estimate.

## Sleep

Zepp OS watches mark asleep minutes with `raw_kind` 120, not worn with
115 and charging with 118[^gb-kind]. The sleep stages (light, deep,
REM) come from separate sleep data, which Amazfish does not fetch for
Zepp OS; the extra bytes of each minute that Gadgetbridge reads for
stages are dropped by Amazfish (`m_sampleSize == 8`)[^af-fetch].

Amazfish's own sleep chart counts minutes whose low four bits are 9
(light) or 11 (deep)[^af-ui]: `120 & 0xf` is 8, so **Amazfish probably
shows no sleep for the Balance**. Pulsus reads 120 as asleep and builds
the night's main sleep (`data/sleep.py`): the night runs from
noon to noon and belongs to the morning's date; asleep minutes closer
than 60 min form one sleep; the sleep with the most asleep time is the
night's, if it has at least 20 min. Pulsus shows asleep and awake only.
