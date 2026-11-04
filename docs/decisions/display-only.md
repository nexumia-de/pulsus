---
type: Decision Record
title: Amazfish collects, Pulsus only displays
description: Pulsus reads Amazfish's database read-only and never talks to the watch or to Amazfish; the alternatives (own Bluetooth stack, Gadgetbridge or Zepp under ATL) were rejected.
tags: [decision, architecture, amazfish, privacy]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Status

Accepted (2026-11-04) by the owner: "Amazfish runs stably for me and I
want to build on it", and "Pulsus only for displaying the data".

# Context

The owner wears an Amazfit Balance and uses Amazfish on the phone.
Amazfish's own charts are basic. Options looked at:

| Option | Result |
|---|---|
| Own Bluetooth connection in Pulsus | Rejected: the Zepp OS part alone is about 8,000 lines in Amazfish (encrypted, chunked protocol, auth key, file transfer); a third copy to maintain |
| Gadgetbridge under ATL as the collector | Possible (it already connects to the owner's Balance headless, see the ATL fork's `docs/apps.md`), but the owner prefers the native Amazfish |
| Zepp app under ATL | Rejected: needs a Zepp account and sends health data to Zepp's servers |
| **Read Amazfish's database** | **Chosen** |

# Decision

- Amazfish stays the only program that talks to the watch. Pulsus has
  no Bluetooth, no network, no D-Bus calls to Amazfish and no sync
  button.
- Pulsus reads a private snapshot of Amazfish's SQLite file and never
  writes to it ([Amazfish's data](../amazfish-data.md)); the Flatpak gets
  read-only access to Amazfish's two possible data folders.
- Pulsus keeps no health data of its own; the snapshot is a cache.
- What Amazfish does not store (sleep stages, resting heart rate for the
  Balance) is either estimated and labelled, or left out. Missing
  downloads belong into Amazfish (GPL-3.0, public on GitHub). Amazfish's
  `AI-Policy.md` asks that a human understands and submits every change,
  so such a change goes upstream only through the owner.

# Consequences

Pulsus depends on Amazfish's table layout, which has no stability
promise; the queries cope with missing tables, and changes are caught by
the owner's database in M1. Pulsus works with every watch Amazfish
supports, but its readings of `raw_kind` are checked for Zepp OS only.
