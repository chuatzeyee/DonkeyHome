# DonkeyHome

## How to use it

1. Click **Start**, then **Open web UI** (or click **DonkeyHome** in the sidebar).
2. Answer the six questions. Nothing changes until you press **Set up my home**.
3. Wait about a minute while Home Assistant restarts. Then open your new dashboard.

Run it again any time to change your answers; they are remembered.

## What it changes

- Creates the rooms (areas) you chose, if they don't exist yet.
- Writes `configuration.yaml`, the `packages/` files `house.yaml`, `routines.yaml`, `presence.yaml`, `look.yaml` and `maintenance.yaml`, and `dashboards/home.yaml`.
- Adds the DonkeyHome look: `themes/donkeyhome.yaml` (dark and light) and `www/donkeyhome/` (button-card, the Google Sans and Instrument Serif fonts). The theme is applied to all of Home Assistant; the sun/moon button on the dashboard switches light and dark. To use another theme, pick it in your profile and delete `packages/look.yaml`.
- Hides Home Assistant's top bar on the Home page (kiosk-mode, `www/donkeyhome/kiosk-mode.js`); admins get a gear button there for Settings. `?disable_km` in the address brings the bar back for a moment.
- Uses your licensed Canela font for headings if `Canela-Regular.woff2` / `Canela-Thin.woff2` are in `www/fonts/` or `www/donkeyhome/` (otherwise the free Instrument Serif). DonkeyHome never includes Canela itself.
- Creates `automations.yaml`, `scripts.yaml` and `scenes.yaml` only if they are missing. Automations you made yourself are never touched.
- Before writing, copies every file it changes into the `donkeyhome_backups` folder.
- Asks Home Assistant to check the new setup. If the check fails, it puts your old files back and changes nothing.

## Undo

Copy the files from the newest folder in `donkeyhome_backups` back into your config folder (for example with the **File editor** or **Samba share** app), then restart Home Assistant. Or restore a Home Assistant backup from **Settings > System > Backups**.

## Help

Guides and questions: https://github.com/chuatzeyee/DonkeyHome
