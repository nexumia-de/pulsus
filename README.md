# Watch Health (Pulsus)

*Watch Health* is the name you see in the app grid; the code name
*Pulsus*, Latin for *pulse*, is used for the repository, app id and
package.

Adaptive GTK4/libadwaita app for [Phosh](https://phosh.mobi/) phones and
the desktop that shows the health data
[Amazfish](https://github.com/piggz/harbour-amazfish) downloads from
your smartwatch: steps, resting heart rate, sleep, stress, heart rate
variability, blood oxygen, skin temperature, PAI and workouts.

- **Today at a glance**: one card per value, with its context and the
  last seven days.
- **Day, week, month, year** for every value, with a sentence on how
  the last week compares with the weeks before.
- **Your own normal range** instead of population averages, once there
  are two weeks of data.
- **Honest charts**: gaps stay gaps, estimates are labelled, the
  numbers are written out.
- **Only reads**: Pulsus opens Amazfish's database read-only and
  follows every sync. No account, no network, no Bluetooth of its own.

Built for the Amazfit Balance; other watches that Amazfish supports
should work, but their sleep data is untested. Status: first version
(milestone M0), not yet tested on a phone. See the
[milestones](https://github.com/nexumia-de/pulsus/milestones) and
[docs/roadmap.md](docs/roadmap.md).

Pulsus is an independent project, not affiliated with the Amazfish
project or the watch maker, and not a medical device.

## Install

After the first release, on the phone open <https://flatpak.nexumia.de/>
and tap Pulsus; GNOME Software installs it and keeps it updated.
Amazfish can be installed as a system package or from Flathub; Pulsus
finds its data in both cases.

## Support

Pulsus is free for everyone. If you want to support its development
and more free apps, you can do so on
[Liberapay](https://liberapay.com/suitably). What the money pays for
and which fees each platform takes:
[support](https://github.com/nexumia-de/phosh-toolkit/blob/main/docs/support.md).

## Development

This repository uses
[phosh-toolkit](https://github.com/nexumia-de/phosh-toolkit), checked out
next to it; its shared Python package `phosh_toolkit` is part of the app:

```
workspace/
  phosh-toolkit/
  pulsus/
```

```sh
[ -d phosh-toolkit ] || git clone https://github.com/nexumia-de/phosh-toolkit.git
bash phosh-toolkit/setup.sh
```

Run with `PYTHONPATH=../phosh-toolkit/lib python3 -m pulsus` (with a
made-up person instead of your data: add `PULSUS_DEMO=1`), test with
`xvfb-run -a python3 -m pytest`. Details:
[docs/dev-environment.md](docs/dev-environment.md).

Agent rules: [AGENTS.md](AGENTS.md). Knowledge bundle:
[docs/index.md](docs/index.md).

## License

GNU Affero General Public License v3.0 or later
(`AGPL-3.0-or-later`), see [LICENSE](LICENSE). Why:
[license decision](docs/decisions/license.md). Contributions are
accepted only under the terms in [CONTRIBUTING.md](CONTRIBUTING.md).
