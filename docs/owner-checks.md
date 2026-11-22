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

# Workouts from Amazfish (#8)

Amazfish downloads workouts only from its Sports page
([why](amazfish-data.md#workouts)).

- [ ] In Amazfish open **Sports** and choose **Download Next Activity**,
      once per workout on the watch.
- [ ] Watch Health ▸ Workouts lists them (About ▸ Troubleshooting shows
      the `sports_data` row count).
- [ ] If `sports_data` has rows and Workouts stays empty, that is a bug
      in Pulsus: open an issue with the Troubleshooting text.
- [ ] If Download Next Activity stores nothing for the Balance, that is
      a gap in Amazfish and belongs in the report below.

# Report to Amazfish (#4)

[Decision](decisions/amazfish-gaps.md): the gap is reported upstream by
the owner, in the owner's own words (Amazfish's `AI-Policy.md` does not
accept AI-written reports or replies).

- [ ] Check that <https://github.com/piggz/harbour-amazfish/issues> has
      no report for it yet.
- [ ] Open one. The facts, with sources, are in
      [Amazfish's data](amazfish-data.md): for Zepp OS watches
      `supportedDataTypes` has no sleep sessions, resting and maximum
      heart rate or breathing rate; Gadgetbridge fetches them; the
      sleep chart counts kinds 9 and 11 while the Balance stores 120.
- [ ] If the Sports download stores nothing for the Balance (#8 above),
      add that or report it separately.

# Workout route and zones (#5)

Tested only with recorded GPX files and the demo person; the format of
the Balance's own tracks was not seen.

- [ ] After a GPS workout is downloaded (#8 above), its page shows the
      route; its shape matches the watch's or the Zepp app's map.
- [ ] Distance and the time per kilometre are close to the watch's.
- [ ] The maximum heart rate under Preferences is plausible (or set
      your own); the minutes per zone roughly match the watch.
- [ ] A workout without GPS shows no route card and no error.

# Summary (#6)

- [ ] Summary ▸ last 7 days, the step-goal streak and the records match
      what the watch and Amazfish show for the same days.
- [ ] Summary opens quickly with the full history.

# First release (#3)

Published: <https://flatpak.nexumia.de/> lists Watch Health and Watch
Health (Nightly) (seen 2026-11-22).

- [ ] Import `.github/rulesets/main.json` as the ruleset for `main`
      (Settings ▸ Rules ▸ Rulesets ▸ Import), if not done yet; an agent
      cannot see or change the repository's rulesets.
- [ ] Install Watch Health on the phone from <https://flatpak.nexumia.de/>
      and start it once; then go on with the list for #1 above.
- [ ] Merge the next release pull request (`release/v…`) and push its
      tag when the changes of this file's pull request should reach the
      stable app.
