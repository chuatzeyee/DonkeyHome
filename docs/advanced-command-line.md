# Advanced: use DonkeyHome without the app

**Most people don't need this.** Use the DonkeyHome app instead ([guide 2](02-setting-up.md)).

This page is for Home Assistant installs without apps ("Container" or "Core" installs), or for people who prefer to look at and copy the files themselves. You run the same questions in a terminal, and copy the files in by hand.

**You need:** Python 3.10 or newer on your computer, and a way to copy files into Home Assistant's config folder.

---

## 1. Download

On this project's GitHub page: green **Code** button > **Download ZIP**, then unzip. (Or `git clone https://github.com/chuatzeyee/DonkeyHome`.)

## 2. Create your rooms first

In Home Assistant: **Settings > Areas, labels and zones**. Make sure every room you'll name exists, spelled the same. (The app does this for you; the command line can't.)

## 3. Find your phones' notify names (optional)

**Settings > Tools > Actions** tab > type `mobile_app` in the action box. Each phone shows as `notify.mobile_app_...`, for example `notify.mobile_app_alex_iphone`. Write down the part after `notify.`.

## 4. Run the questions

Open a terminal in the unzipped folder and run:

```bash
python3 donkeyhome/app/wizard.py
```

(On Windows: `py donkeyhome\app\wizard.py`.)

Press Enter to keep a suggestion in `[brackets]`. Your answers are saved in `my-answers.json` for next time. The files are written to the `config` folder.

No questions, from a saved answers file:

```bash
python3 donkeyhome/app/wizard.py --answers my-answers.json --yes
```

## 5. Copy the files in

Make a backup first (**Settings > System > Backups > Backup now**).

Copy everything inside the `config` folder into Home Assistant's config folder (next to `.storage`), replacing `configuration.yaml`. That includes the `themes` and `www` folders (the DonkeyHome look):

- **Home Assistant OS:** the **Samba share** app (`\\homeassistant\config` on Windows, `smb://homeassistant.local/config` on Mac) or the **Studio Code Server** app.
- **Container:** the folder you mounted as `/config`.

If you already have automations, scripts or scenes made in the screens, **don't** copy `automations.yaml`, `scripts.yaml` or `scenes.yaml`.

If you turned the weekly battery check off after having it on, delete `packages/maintenance.yaml` from Home Assistant's folder.

## 6. Check and restart

**Settings > Tools > YAML** tab > **Check configuration**. When it says the configuration is valid, click **Restart**.

✅ Check: your home's name appears in the sidebar as a dashboard with Routines, House and Rooms.

Then continue with guide 2 from [Step 5](02-setting-up.md#step-5-add-your-devices).

---

## For developers

```bash
python3 -m unittest discover tests        # fast offline checks
python3 tests/integration_test.py         # real Home Assistant + the app container (needs Docker)
python3 tests/integration_test.py --shots # also screenshots (needs Playwright)
```

The app is `donkeyhome/`: `config.yaml` (app manifest), `Dockerfile`, and `app/` (`server.py` web server, `haclient.py` Home Assistant client, `wizard.py` file generator, `web/` the setup screens, `templates/dashboard.yaml` the dashboard, `assets/` theme, fonts and button-card copied into Home Assistant). Standard library only, no build step.

The dashboard needs no entity IDs: button-card templates find each room's lights through the entity and device registries, and the room, Lights, Climate, Door and Media pages are Home Assistant's own view strategies (`home-area`, `light`, `climate`, `security`, `home-media-players`), styled by the theme.
