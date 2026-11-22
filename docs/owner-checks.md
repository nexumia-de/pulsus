---
type: Playbook
title: Checks only the owner can do
description: What is left for the owner after the issues were closed on 2026-11-22: checks on the phone with the real watch data, release settings, and the report to Amazfish.
tags: [owner, checklist, on-device, release, amazfish]
generated: { by: claude-code/2.1.318, at: 2026-11-22T02:00:00Z }
---

# Why this file

An agent in the cloud has no phone, no watch, no real health data and
no secrets. Each list below is the part of a closed issue that needs
one of them. Nothing here was checked on a device. Report results as
"matches" or "off by …" only; real values never go into an issue, the
repository or a log.

# Real data on the phone (#1)

Open **About Watch Health ▸ Troubleshooting ▸ Debugging Information**
first: it shows where the database is, the rows per table with first
and last day, the minutes per `raw_kind` and how many heart-rate minutes
are 0 or 255 ([what it shows](amazfish-data.md#checking-on-the-phone)).

- [ ] The database is found (system package or Flathub) and Today shows data.
- [ ] Sleep: `raw_kind` 120 is among the most frequent kinds; bed time,
      wake time and time asleep match the watch's own sleep screen.
- [ ] Heart rate: no implausible readings on the day view (only 0 and
      255 mean "no reading"); the resting estimate is within a few beats
      of the watch's resting heart rate.
- [ ] Times: the hours of steps and sleep line up with local time,
      nothing is shifted by the time-zone offset.
- [ ] Stress, HRV, SpO₂, skin temperature and PAI match the watch.
- [ ] Workouts: kinds, distance, pace and heart rate match the watch.
- [ ] Speed: Today and each Year view open in about a second with the
      full history. In the cloud a year of demo data stays well under
      two seconds per page (`tests/test_speed.py`); the phone is slower.

A value that is off becomes a new issue with the label `on device`,
without the real numbers.
