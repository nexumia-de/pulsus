@../phosh-toolkit/AGENTS.md

# Pulsus

Shows the health data that [Amazfish](https://github.com/piggz/harbour-amazfish)
downloads from the owner's watch (an Amazfit Balance), on Phosh phones
and the desktop. The shared rules in ../phosh-toolkit/AGENTS.md apply as
well.

- App id: `de.nexumia.Pulsus`.
- Plan: work items are [issues](https://github.com/nexumia-de/pulsus/issues)
  in [milestones](https://github.com/nexumia-de/pulsus/milestones); goals
  per milestone are in [docs/roadmap.md](docs/roadmap.md).
- **Display only** ([decision](docs/decisions/display-only.md)): Amazfish
  is the only program that talks to the watch. Pulsus never writes to
  Amazfish's database, has no Bluetooth, no network and no sync of its
  own, and keeps no health data outside its snapshot cache. Read
  [docs/amazfish-data.md](docs/amazfish-data.md) before touching
  `pulsus/data/`.
- Visible name: **Watch Health** (chosen by the owner on 2026-11-06,
  [decision](docs/decisions/app-name.md)); the code name Pulsus stays for
  the repository, app id, package and docs.
- Facts about Amazfish's tables come from its source at a recorded
  commit, facts about Zepp OS values from Gadgetbridge's source; never
  copy code from either (GPL-3.0, AGPL-3.0).
- Amazfish's `AI-Policy.md` forbids changes an agent submits on its
  own: a missing download (sleep stages, resting heart rate) becomes an
  issue here, and goes upstream only through the owner.
- Charts and texts follow [docs/visualisation.md](docs/visualisation.md):
  one measure per chart, the user's own normal range, gaps stay gaps,
  estimates labelled, no medical advice, no invented scores.
- Screenshots and UI tests use the demo person (`PULSUS_DEMO=1`,
  `pulsus/demo.py`), never real health data. Real data from the owner
  stays on the phone and never goes into the repository, an issue or a
  log.
- Run PyGObject code with `/usr/bin/python3.12` on the cloud host; the
  default `python3` has no `gi`.
