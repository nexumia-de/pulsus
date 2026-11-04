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
| `phosh-toolkit` | tag `v0.3.0` (commit `c29a2a1`) | GPL-3.0-or-later (own code, same author) | `LICENSE` → `/app/share/licenses/<app id>/phosh-toolkit/` |

Only `lib/phosh_toolkit/` is installed; Pulsus uses `settings`
(`JsonStore`, `app_dir`) and `style` (light/dark)
([shared code](../../phosh-toolkit/docs/shared-connection.md#used-by)).
GPL-3.0-or-later code may be combined with Pulsus's AGPL-3.0-or-later
(section 13 of both licences).

# From the runtime (not bundled)

`org.gnome.Platform//51` provides Python 3 with `sqlite3`, PyGObject,
GTK 4 (its `Gsk` paths draw the charts, so no plotting library) and
libadwaita.

# Not used

No code or assets from Amazfish (GPL-3.0) or Gadgetbridge (AGPL-3.0).
