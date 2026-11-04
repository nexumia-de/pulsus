---
okf_version: "0.2"
---

# Pulsus knowledge bundle

[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(OKF v0.2) bundle of this app. Shared Phosh knowledge lives in
[../../phosh-toolkit/docs/index.md](../../phosh-toolkit/docs/index.md).
Change history is in [log.md](log.md).

# Plan

* [Roadmap](roadmap.md) - Goals and exit criteria of the milestones; the work items are GitHub issues.

# Design

* [Visual design](design.md) - Stock libadwaita with Pulsus's pulse-red accent, chart colours, the screens and the review checklist.
* [How Pulsus shows the data](visualisation.md) - Chart rules (one measure per chart, own normal range, gaps stay gaps, numbers written out), what other fitness apps taught us, the pages.
* [Amazfish's data](amazfish-data.md) - Where the database is, the tables and what their values mean for the Amazfit Balance, read-only snapshots, what the data lacks (sleep stages, resting heart rate).

# Development

* [Bundled dependencies](dependencies.md) - Only phosh-toolkit's shared package; everything else comes from the GNOME runtime.
* [Release channels](release-channels.md) - Stable from tags, nightly from main, screenshots from the demo person.
* [Development environment](dev-environment.md) - Hosts, host packages, run, test, screenshot, and the Flatpak against a read-only Amazfish folder.

# Decision records

* [Decisions](decisions/index.md) - Display only on top of Amazfish, name, licence.
