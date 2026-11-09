<p align="center"><img src="donkeyhome/logo.png" alt="DonkeyHome" width="420"></p>

**A beautiful, phone-first smart home in six easy questions.** No programming, no files, no command line.

DonkeyHome is an app that runs inside Home Assistant. You tap through six friendly screens (your home's name, your rooms, who lives there, coming and going, what should happen, check) and it turns Home Assistant into this:

<p align="center">
<img src="docs/images/dashboard-dark.png" alt="DonkeyHome dashboard, dark" width="250">
<img src="docs/images/dashboard-light.png" alt="DonkeyHome dashboard, light" width="250">
<img src="docs/images/dashboard-room.png" alt="A room page" width="250">
</p>

- **A dashboard that feels like an app:** a greeting that tells you what's going on ("3 lights are on. The door is unlocked."), room pills that turn pink when a room's lights are on, one tap per room for its lights, a floating dock, and a page per room. No top bar on Home. Light and dark, switched with one button. Google Sans, with Canela for headings if you have its licence (Instrument Serif otherwise).
- **Five one-tap routines:** Good Morning, Leaving Home, I'm Home, Good Night, Everything Off.
- **Automatic leave and arrive:** when the last phone leaves, the house switches off and tells you; when the first one comes back, the arrival room lights up after dark.
- **Phone messages** through the Home Assistant app, and a weekly list of batteries to change.
- **Any brand:** routines use "every light", "every fan" and so on, so new devices join in by themselves.

It's safe: DonkeyHome backs up every file it changes, has Home Assistant check the new setup, and puts everything back if there is any problem. It never touches automations you made yourself.

The setup itself looks the same:

<p align="center">
<img src="docs/images/wizard-welcome.png" alt="DonkeyHome welcome screen" width="250">
<img src="docs/images/wizard-rooms.png" alt="Choosing rooms" width="250">
<img src="docs/images/wizard-review.png" alt="The plan, before anything changes" width="250">
</p>

## Install

Already have Home Assistant? Click:

[![Add DonkeyHome to my Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fchuatzeyee%2FDonkeyHome)

Then **Install** > **Start** > **Open web UI**. Full steps with pictures: [guide 2](docs/02-setting-up.md).

## The guides

Written for complete beginners. Each step ends with a ✅ check, and each guide ends with "If something goes wrong".

| | Guide | Time |
|---|---|---|
| 1 | [Getting started: install Home Assistant](docs/01-getting-started.md) (which box to buy, installing, first login, phones, backups) | 1 hour |
| 2 | [Setting up: install DonkeyHome and answer six questions](docs/02-setting-up.md) | 15 minutes |
| 3 | [Adding devices](docs/03-adding-devices.md) | 5 to 10 minutes per device |
| 4 | [Routines and making changes](docs/04-routines-and-changes.md) | as you like |
| 5 | [Looking after it](docs/05-looking-after-it.md) (updates, backups, remote access, troubleshooting) | 5 minutes a month |
| | [Advanced: without the app](docs/advanced-command-line.md) (Container installs, developers) | |

Works with Home Assistant OS (Home Assistant Green, Raspberry Pi, mini PC, virtual machine) on Home Assistant 2026.10 and newer.

## What's in this repository

```text
repository.yaml        tells Home Assistant this is an app repository
donkeyhome/            the app: config.yaml, Dockerfile, DOCS.md, icon and logo
  app/server.py        the web page's server (runs inside Home Assistant)
  app/wizard.py        turns your answers into Home Assistant files (also a command-line tool)
  app/haclient.py      talks to Home Assistant
  app/web/             the six screens
  app/templates/       the dashboard DonkeyHome writes
  app/assets/          the DonkeyHome theme, fonts and button-card, copied into Home Assistant
config/                example of what DonkeyHome writes (4 rooms, 2 people)
example-answers.json   the answers behind that example
docs/                  the guides
tests/                 offline checks, plus an end-to-end test with a real Home Assistant
```

## License

MIT. See [LICENSE](LICENSE). Bundled: button-card and kiosk-mode (MIT), Google Sans and Instrument Serif (SIL Open Font License), Material Design Icons (Pictogrammers Free License); details in `donkeyhome/app/assets/www/donkeyhome/LICENSES.md`. Canela (Commercial Type) is not included; DonkeyHome uses your own licensed copy if you add it.
