---
type: Decision Record
title: Workout routes without map tiles; zones from the user's own maximum heart rate
description: The GPS track of a workout is drawn to scale without a map behind it, because Pulsus has no network; heart-rate zones are tenths of a maximum heart rate that is estimated from the stored data or set by the user.
tags: [decision, workouts, map, gps, heart-rate-zones, offline]
generated: { by: claude-code/2.1.318, at: 2026-11-22T03:00:00Z }
---

# Status

Accepted (2026-11-22). Decided by the agent by best practice while
closing #5, which left "the tile source and its attribution rules" and
the source of the maximum heart rate open; the owner asked for
decisions without questions.

# Route: no map tiles

The route is the track drawn to scale, north up, with start, end and a
scale bar (`pulsus/workout/route.py`).

- Map tiles need the network. Pulsus loads none by decision
  ([display only](display-only.md)), and a health app that never talks
  to a server is worth more than a street map behind a loop the user
  ran themselves. Asking a tile server for tiles would also tell it
  where the user trains.
- Offline tiles would mean bundling or downloading map data: hundreds
  of megabytes per region, a renderer as a new dependency, and
  attribution and update duties, for one card on one page.
- The shape, length and scale of a route are what the page needs; the
  watch's distance and the kilometre times are written out beside it.

If a map is wanted later, it is a new issue that has to change the
display-only decision first.

# Zones: tenths of the user's maximum heart rate

Five zones from 50 % of the maximum heart rate in steps of 10 %, the
convention the watch and most sport apps use. The maximum is:

1. what the user sets in Preferences (100–230 bpm), or
2. by default the highest heart rate Amazfish has stored (minutes and
   the workouts' own `maxHR`), named as an estimate on the page.

A formula from the age (220 − age) was not used: Pulsus does not know
the age and would have to ask for it and store it, and the formula is
off by ten beats and more for many people. The watch's own maximum
heart rate is not stored by Amazfish
([Amazfish's data](../amazfish-data.md#what-the-balance-delivers)).
The time in zones comes from the stored minutes, one reading per
minute. The page gives minutes and limits, no judgement of the
training ([visualisation](../visualisation.md#rules)).
