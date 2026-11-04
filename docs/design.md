---
type: Concept
title: Visual design
description: Stock libadwaita with Pulsus's pulse-red accent, the chart colours, the screens at 360 px and on the desktop, and the review checklist.
tags: [design, accent, adaptive, libadwaita]
resource: ../pulsus/style.css
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

Pulsus follows the toolkit's [visual design](../../phosh-toolkit/docs/design.md)
and [adaptive UI](../../phosh-toolkit/docs/adaptive-libadwaita.md) rules;
how data is drawn is in [visualisation](visualisation.md).

# Accent

Pulse red `#c6345a` with white text (contrast 5.2:1), set only through
`--accent-bg-color`/`--accent-fg-color` in `style.css` (plus
`@define-color` for libadwaita 1.5 hosts)
([one accent per app](../../phosh-toolkit/docs/decisions/app-accent-colours.md)).
Light and dark follow the system; Preferences → Appearance → Style
offers Follow System / Light / Dark (`phosh_toolkit.style`). The
metainfo branding colours are `#f5c2cf` (light) and `#6e1a31` (dark).

# Chart colours

Marks use the accent, `#c6345a` in light mode (5.0:1 on the light
card) and `#ef7b9b` in dark mode (5.0:1 on `#303030`), so they keep
the 3:1 that graphics need; the normal-range band is the same colour at
16 %. Grid lines and axis text use the theme's foreground colour at
12 % and 60 %. Fixed data colours are allowed by the toolkit; none
carries information alone.

# Screens

| Screen | Narrow (≤ 600 sp) | Wide |
|---|---|---|
| Today | one column of cards | two or three columns (flow box), clamped to 1100 px |
| Metric | range buttons, headline, chart 220 px, number rows | clamped to 760 px |
| Workouts | rows by month | same |
| Workout | duration, heart-rate chart, numbers | clamped to 760 px |
| No database | status page with the paths searched and "Look Again" | same |

Every page is pushed onto one `AdwNavigationView`. Own symbolic icons
for the metrics are in `data/icons/hicolor/symbolic/apps` (drawn for
Pulsus, AGPL like the app). No logos of Amazfish or the watch maker.

# Review checklist

The toolkit's checklist, and for Pulsus: no horizontal scrolling at
360 px, values never wrap inside number rows, every chart has an
accessible label, icon-only buttons (previous/next day, menu) have
tooltips and labels, gaps show as gaps.
