---
type: Playbook
title: Release channels
description: Pulsus (stable, from tags v<version>) and Pulsus (Nightly) (de.nexumia.Pulsus.Devel, from every push to main), changelog fragments, and store screenshots from the demo person.
tags: [release, nightly, flatpak, ci, changelog, screenshots]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Channels

| Channel | App | App id | Fed by |
|---|---|---|---|
| Stable | Pulsus | `de.nexumia.Pulsus` | tags `v0.1.0`, … |
| Nightly | Pulsus (Nightly) | `de.nexumia.Pulsus.Devel` | every push to `main` |

Both come from `https://flatpak.nexumia.de/`: on 2026-11-22 its page
listed `de.nexumia.Pulsus` and `de.nexumia.Pulsus.Devel` for aarch64
and x86_64, so the tag `v0.1.0`, the secret `PUBLISH_TOKEN` and the
entry in phosh-apps' `apps.txt` are in place (#3). Left for the owner:
[owner checks](owner-checks.md#first-release-3). Mechanics: the toolkit's
[Flatpak workflow](../../phosh-toolkit/docs/flatpak-workflow.md#release-channels)
and [releases](../../phosh-toolkit/docs/releases.md).

# Nightly variant

`-Dprofile=development` gives the app id `de.nexumia.Pulsus.Devel`
and derives desktop file and metainfo from `data/` with `sed` in
`meson.build`; `-Dbuild_label` shows the commit in the About dialog.

# Release

Every pull request users notice adds a fragment to `changelog.d/`.
The release workflow collects them into a release pull request
(`release/v<version>`); merging it and pushing the tag publishes the
stable app. 0.1.0 was tagged as `v0.1.0`.

# Screenshots

`release.toml` lists them; CI takes each at 360×720 and 1000×700,
light and dark, from the built Flatpak with `PULSUS_DEMO=1`: the app
writes the made-up person of `pulsus/demo.py` (120 days up to now,
seeded, so always the same person) into a temporary directory and shows
it. Never real health data.

| Shot | Actions |
|---|---|
| `today` | – |
| `steps-month` | `app.show-metric('steps:month')` |
| `heart-rate` | `app.show-metric('heart-rate')` |
| `sleep` | `app.show-metric('sleep:day')` |
| `workout` | `app.show-latest-workout` |
