---
type: Playbook
title: Development environment
description: Hosts, host packages, and how to run, test, screenshot and build Pulsus, including the Flatpak against a read-only Amazfish folder.
tags: [development, environment, testing, flatpak]
generated: { by: claude-code/2.1.318, at: 2026-11-04T19:30:00Z }
---

# Hosts

Reached from the cloud environment on 2026-11-04: `github.com`
(Amazfish, the Flathub manifest), `codeberg.org` (Gadgetbridge),
`dl.flathub.org` and `flathub.org`. `pkgs.alpinelinux.org` answered
with a proxy `403` (it was only used to look for an Alpine Amazfish
package; not needed for development).

# Host packages (Ubuntu 24.04)

After `bash ../phosh-toolkit/setup.sh`: `python3-pytest xvfb`. The
cloud image's default `python3` has no `gi`; use `/usr/bin/python3.12`.
Pycairo is not installed and not needed (charts use `Gsk`).

# Run, test, screenshot

```sh
export PYTHONPATH=$PWD/../phosh-toolkit/lib                    # shared package
PULSUS_DEMO=1 /usr/bin/python3.12 -m pulsus                      # demo person
PULSUS_DATABASE=/path/to/amazfish.kexi /usr/bin/python3.12 -m pulsus
dbus-run-session -- xvfb-run -a /usr/bin/python3.12 -m pytest   # all tests, as in CI
../phosh-toolkit/scripts/screenshot.sh -i de.nexumia.Pulsus -d 6 -e PULSUS_DEMO=1 -e PYTHONPATH=$PYTHONPATH -o shot.png -- /usr/bin/python3.12 -m pulsus
```

Other states: `-a "app.show-metric('sleep:day')"`,
`-a "app.show-metric('heart-rate:month')"`, `-a app.show-workouts`,
`-a app.show-latest-workout`. `PULSUS_DEBUG=1` logs snapshots.

# Flatpak

```sh
flatpak-builder --user --install --force-clean --disable-rofiles-fuse build-dir de.nexumia.Pulsus.yml
```

`flatpak run` in the cloud container needs a system bus
(`mkdir -p /run/dbus && dbus-daemon --system --fork`), an
`XDG_RUNTIME_DIR` (`/run/user/0`) and `dbus-run-session`. Checked on
2026-11-04 with a demo database in each of Amazfish's two folders: the
sandbox sees the file, `touch` there fails with "Read-only file
system", and Pulsus shows the data.
