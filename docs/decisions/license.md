---
type: Decision Record
title: AGPL-3.0 license
description: Pulsus is AGPL-3.0-or-later like Ephyra and Nauta, with the same contributor terms.
tags: [decision, license]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Status

Accepted (2026-11-04), following the owner's choice for Ephyra and
Nauta.

# Decision

`AGPL-3.0-or-later`, contributions under the terms in
`CONTRIBUTING.md` (the author may relicense). AppStream metadata is
CC0-1.0. The symbolic icons and the app icon were drawn for Pulsus and
are AGPL like the code.

# Consequences

Pulsus reads Amazfish's database file and copies no code from Amazfish
(GPL-3.0) or Gadgetbridge (AGPL-3.0); facts about the table layout and
values are taken from their source ([Amazfish's data](../amazfish-data.md)).
phosh-toolkit's package (GPL-3.0-or-later) combines with it
([dependencies](../dependencies.md)).
