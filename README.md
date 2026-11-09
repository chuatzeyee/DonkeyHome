# Home Assistant Starter Wizard

A beginner-friendly way to go from "I bought a small computer" to a working smart home with one-tap routines, automatic "everyone left" switch-off, phone notifications and a tidy dashboard.

You answer a few questions in plain English. The wizard writes a ready-made Home Assistant configuration for **your** rooms, people and choices. The guides walk you through every click.

No programming needed. Written for Home Assistant 2026.10 and 2026.11.

## What you get

- **Five one-tap routines:** Good Morning, Leaving Home, I'm Home, Good Night, Everything Off.
- **Automatic leave and arrive:** when the last phone leaves, the house switches off (and tells you); when the first one comes back, the arrival room lights up after dark.
- **A dashboard** with the routines, the house mode and one card per room.
- **Phone notifications** through the Home Assistant app, plus a weekly low-battery list.
- **Works with any brand:** routines use "every light", "every fan" and so on, so new devices join in by themselves.

## Start here

| Step | Guide | Time |
|---|---|---|
| 1 | [Getting started: install Home Assistant](docs/01-getting-started.md) | 1 hour |
| 2 | [Setting up: run the wizard and copy your configuration](docs/02-setting-up.md) | 45 minutes |
| 3 | [Adding devices](docs/03-adding-devices.md) | 5 to 10 minutes per device |
| 4 | [Routines and making changes](docs/04-routines-and-changes.md) | as you like |
| 5 | [Looking after it](docs/05-looking-after-it.md) | 5 minutes a month |

## The wizard in 30 seconds

1. Download this project (green **Code** button > **Download ZIP**) and unzip it.
2. Windows: double-click `setup.bat`. Mac or Linux: run `./setup.sh` in a terminal.
3. Answer the questions (press Enter to keep a suggestion).
4. Copy the new `config` folder's contents into Home Assistant (guide 2 shows how).

Needs Python 3.9 or newer. Nothing else to install.

Prefer to look before you run anything? The `config` folder in this project is already filled in for an example home (4 rooms, 2 people) so you can read exactly what the wizard makes.

## Folder map

```text
README.md              this page
setup.bat, setup.sh    start the wizard (Windows / Mac and Linux)
wizard/wizard.py       the wizard (standard Python only)
example-answers.json   the answers used for the example config
config/                what the wizard writes; copy its contents into Home Assistant
  configuration.yaml   switches everything on
  packages/            routines, house mode, presence, weekly check
  dashboards/          your dashboard
docs/                  the step-by-step guides
tests/                 automatic checks for the wizard
```

## For tinkerers

```bash
python3 wizard/wizard.py --answers my-answers.json --out config --yes   # no questions
python3 -m unittest discover tests                                       # run the checks
```

The generated configuration is checked with Home Assistant's own `check_config` (2026.10.2).

## License

MIT. See [LICENSE](LICENSE).
