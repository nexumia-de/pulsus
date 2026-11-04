---
type: Concept
title: How Pulsus shows the data
description: The rules for Pulsus's charts and texts, what other fitness apps taught us, and how each page applies them.
tags: [design, visualisation, charts, baseline, accessibility]
resource: ../pulsus/charts.py
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# What other apps taught us

From a look at Gadgetbridge's charts (its source) and at well-known
commercial apps (from general knowledge, not checked against their
current versions), on 2026-11-04 at the owner's request:

| App | Idea Pulsus takes |
|---|---|
| Gadgetbridge | Per metric a day view and a period view; a dashboard of small cards; step streaks; HRV against a baseline |
| Apple Health | The same ranges everywhere (day, week, month, year); trends said in a sentence; one colour per meaning |
| Garmin Connect | The user's own normal range as a band, the value placed in it instead of a population norm |
| Fitbit, Oura | Sleep as a timeline of the night; a learning phase until the baseline exists; scores always with their factors |
| Strava | A workout page with its numbers and the heart rate during it |
| Zepp | Counter-example: every metric a separate deep page, hard to find |

# Rules

1. **One measure per chart**, never two y axes. Bars for amounts that
   add up (steps, sleep, PAI), dots with a 7-day average line for levels
   (heart rate, stress, HRV, SpO₂, temperature). Bars start at zero.
2. **Your own normal range**: the 10th to 90th percentile of the 30
   days before the day shown (`stats.baseline`), drawn as a band; not
   shown before 14 days of data, and the page says so.
3. **Trends in words, without judgement**: last 7 days against the 4
   weeks before; under 5 % change is "about the same"
   (`stats.trend_sentence`). No "good" or "bad", no medical advice.
4. **Gaps stay gaps**: no line across missing minutes or days; missing
   values are "–" or "No data", never 0.
5. **Estimates say so**: resting heart rate and sleep are derived by
   Pulsus ([Amazfish's data](amazfish-data.md)); each page explains how
   in "How It Is Measured".
6. **Numbers are written out**: headline, lowest/average/highest rows,
   the value under the finger (tap), and an accessible label with a
   summary for every chart. Colour is never the only carrier.
7. **No invented scores**: Pulsus shows what the watch measured and
   simple statistics of it. PAI is the watch's own score.
8. **Swipe back everywhere**; the chart takes taps only, so horizontal
   swipes stay with the navigation view.

# Pages

- **Today**: one card per metric with data in the last 5 weeks: value,
  context line (goal, normal range, times), 7-day sparkline; a card for
  the last workout. Previous/next day in the header. At the bottom when
  Amazfish last stored data; a banner after 24 h without new data.
- **Metric**: Day / Week / Month / Year (Day only where it exists; the
  year shows 52 weekly averages), headline, trend sentence, chart,
  numbers, normal range, "How It Is Measured". Day views: steps per
  hour, heart rate as 5-minute averages, sleep as a timeline, single
  readings as dots.
- **Workouts**: by month; a workout shows duration, times, heart rate
  during it (from the minute rows) and the watch's numbers.

# Not yet

Maps of GPS tracks, heart-rate zones, sleep stages, records and streaks:
issues in the later milestones.
