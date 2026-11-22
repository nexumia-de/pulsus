---
type: Reference
title: Bundled dependencies
description: Pulsus bundles only phosh-toolkit's shared package; everything else comes from the GNOME runtime.
tags: [dependencies, licensing, flatpak]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Rules

The shared rules are in
[../../phosh-toolkit/docs/licensing.md](../../phosh-toolkit/docs/licensing.md).
CI fails if a module of `de.nexumia.Pulsus.yml` is missing here or
installs no licence files.

# Modules

| Module | Version | Licence | Licence files |
|---|---|---|---|
| `phosh-toolkit` | tag `v0.8.1` (commit `1910057`) | GPL-3.0-or-later (own code, same author) | `LICENSE` → `/app/share/licenses/<app id>/phosh-toolkit/` |

Only `lib/phosh_toolkit/` is installed; Pulsus uses `settings`
(`JsonStore`, `app_dir`), `style` (light/dark)
([shared code](../../phosh-toolkit/docs/shared-connection.md#used-by))
and, since `v0.8.1`, `feedback` (Report a Problem…, with its `http`,
`keyring`, `feedback_dialog` and `feedback_report` modules;
[feedback](../../phosh-toolkit/docs/feedback.md)).
GPL-3.0-or-later code may be combined with Pulsus's AGPL-3.0-or-later
(section 13 of both licences).

# From the runtime (not bundled)

`org.gnome.Platform//51` provides Python 3 with `sqlite3`, PyGObject,
GTK 4 (its `Gsk` paths draw the charts, so no plotting library),
libadwaita, and for the feedback module libsoup 3 (`Soup`) and libsecret
(`Secret`).

# Not used

No code or assets from Amazfish (GPL-3.0) or Gadgetbridge (AGPL-3.0).

# Permissions

The Flatpak's `finish-args` are, besides display, GPU and the two
read-only Amazfish folders ([Amazfish's data](amazfish-data.md#flatpak)):

| Permission | Why |
|---|---|
| `--share=network` | **Report a Problem…** creates a GitHub issue through the REST API with the user's own token (libsoup). Nothing else uses it; no health data is ever sent. |
| `--talk-name=org.freedesktop.secrets` | libsecret keeps that token in the user's keyring (the same grant as the other apps with a keyring). |

Without a token the dialog opens GitHub's issue form in the browser
instead, which needs neither. What is sent: the title and text the user
typed, the app version and the kind of device
([feedback](../../phosh-toolkit/docs/feedback.md#what-is-sent)). Tests
and screenshots set `PHOSH_TOOLKIT_TEST_KEYRING=memory`.
