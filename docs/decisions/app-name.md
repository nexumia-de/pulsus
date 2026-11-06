---
type: Decision Record
title: App name Pulsus
description: The code name is Pulsus, Latin for pulse or beat; app id de.nexumia.Pulsus. The visible name is Watch Health.
tags: [decision, name]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Status

Accepted (2026-11-04) by the owner, who created `nexumia-de/pulsus`.
The visible name **Watch Health** was chosen by the owner on 2026-11-06
(issue #2), from the suggestions Watch Health, Vitals and Body Stats,
under the toolkit decision
[code names and visible names](../../../phosh-toolkit/docs/decisions/app-names.md).

# Decision

*Pulsus* is Latin for "pulse, beat". App id `de.nexumia.Pulsus`,
Python package and command `pulsus`, repository `nexumia-de/pulsus`.

Users see **Watch Health**: the `.desktop` `Name`, the metainfo
`<name>`, the window title, the About dialog and the texts that name the
app; the nightly build says "Watch Health (Nightly)". `GenericName`
stays "Health Data"; the keywords include `pulsus` and `amazfish`. The
docs keep the code name.

# Consequences

On 2026-11-04 and 2026-11-06 Flathub's search had no app named "Watch
Health"; "Health" and "Pulse" are taken.
