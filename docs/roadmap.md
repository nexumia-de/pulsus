---
type: Plan
title: Roadmap
description: Goals and exit criteria of Pulsus's milestones; the work items are GitHub issues in those milestones.
tags: [plan, roadmap, milestones]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# How the plan is tracked

Work items are [issues](https://github.com/nexumia-de/pulsus/issues),
grouped by [milestones](https://github.com/nexumia-de/pulsus/milestones)
and `area: …` labels; issues without a milestone are the backlog. This
file keeps only the goals. Workflow: the toolkit's
[planning with issues and milestones](../../phosh-toolkit/docs/planning.md).

# M0 – First version (done in the first pull request)

App skeleton with metadata, Flatpak manifest, CI and tests; read-only
snapshot of Amazfish's database that follows every sync; Today page,
every metric by day, week, month and year with the user's normal range,
workouts ([visualisation](visualisation.md)).

# M1 – On the phone

**Goal**: Pulsus shows the owner's real watch data correctly.

**Exit criteria**: first release installed from the shared repository;
it finds the owner's Amazfish database; the meaning of `raw_kind`, heart
rate 0/255 and timestamps checked against the owner's data and the
watch's own display; pages open fast with the owner's full history.

# M2 – Deeper insight

**Goal**: what the best fitness apps show beyond daily values.

**Exit criteria**: workout maps from the GPX track, heart-rate zones,
records and streaks, weekly summaries.

# Risks

- **Amazfish's table layout** has no stability promise
  ([display only](decisions/display-only.md)).
- **Sleep without stages** until Amazfish fetches Zepp OS sleep data
  ([Amazfish's data](amazfish-data.md#sleep)).
