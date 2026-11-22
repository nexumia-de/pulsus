---
type: Decision Record
title: Gaps in Amazfish's downloads go upstream as a report by the owner
description: Missing Zepp OS downloads (sleep stages, resting and maximum heart rate, breathing rate) are reported to Amazfish by the owner; no own Amazfish fork, and Pulsus keeps estimating meanwhile.
tags: [decision, amazfish, upstream, sleep, heart-rate]
generated: { by: claude-code/2.1.318, at: 2026-11-22T02:30:00Z }
sources:
  - id: af-policy
    resource: https://github.com/piggz/harbour-amazfish/blob/730b54257d72da8b24df6aa77a99490a01cec49c/AI-Policy.md
    title: Amazfish AI-Policy.md
---

# Status

Accepted (2026-11-22). Decided by the agent by best practice, because
the owner asked for the open issues to be closed without questions
(#4); the owner can overturn it by reopening #4.

# Context

For the Amazfit Balance, Amazfish stores no sleep sessions with stages,
no resting or maximum heart rate and no breathing rate, although the
watch has them ([Amazfish's data](../amazfish-data.md#what-the-balance-delivers)).
Issue #4 named two ways: a bug report to Amazfish written by the owner,
or an own Amazfish fork with the change kept ready for upstream.

# Decision

**A report to Amazfish, written and sent by the owner. No fork.**

- Amazfish's policy asks to discuss anything non-trivial in an issue
  before implementing it, and forbids descriptions and replies written
  by an AI and changes nobody on the contributor's side
  understands[^af-policy]. Four new fetch operations for a Bluetooth
  protocol are not trivial, and nobody here can test them without the
  watch.
- A fork would make Pulsus depend on a second program the owner has to
  build, package and keep in step with upstream for a watch that
  Amazfish runs stably today
  ([display only](display-only.md)). The fork would also need the
  Gadgetbridge protocol facts re-implemented in C++ without a device to
  test on.
- Pulsus loses nothing by waiting: it shows asleep and awake and an
  estimated resting heart rate, and labels both as such.

# Consequences

- The facts for the report are in
  [Amazfish's data](../amazfish-data.md) with their sources; the owner
  writes the report in their own words
  ([owner checks](../owner-checks.md#report-to-amazfish-4)).
- When Amazfish stores the data, Pulsus reads the new tables; that
  becomes an issue then, not before.
- Agents never open issues or pull requests at Amazfish.
