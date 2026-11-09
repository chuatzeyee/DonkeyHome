# 5. Looking after it

**What you'll do:** keep Home Assistant updated, backed up and healthy.
**Time:** 5 minutes a month.

---

## Every month: updates

Home Assistant releases a new version on the first Wednesday of each month, with small fix releases after.

1. **Wait a few days** after a release, then install the newest **fix** release (e.g. 2026.12.**1**, not 2026.12.0).
2. Before updating, read the **breaking changes** for integrations you use: **Settings > System > Updates** > click the update > **Release notes**.
3. Click **Install**. Leave **Create backup** ticked.
4. When it's back, tap each routine once and check your dashboard.

✅ Check: **Settings > System > Updates** says everything is up to date, and the routines still work.

---

## Every week: a quick glance

- Your phones get the **Weekly check: low batteries** message on Sunday if any battery is under 20 %. Change those batteries.
- **Settings > System > Repairs**: fix anything listed (each item explains itself).
- **Settings > System > Backups**: the last backup should be from today or yesterday.

---

## Backups and restoring

Automatic backups were switched on in guide 1, Step 6.

**Keep a copy off the box.** If the box dies, backups on it die too. Either:

- **Settings > System > Backups > Settings** > add a second location (for example **Home Assistant Cloud**, or a network share on your NAS: **Settings > System > Storage > Add network storage**), or
- once a month: **Settings > System > Backups > Show all backups** > the newest > **Download**.

**Restore after a mistake:**

1. **Settings > System > Backups > Show all backups** > pick one from before the problem.
2. **Restore** > choose what to restore (everything is safest) > type the encryption key from your emergency kit if asked.
3. Wait 10 to 20 minutes. Home Assistant restarts by itself.

**Restore onto a new box:** install Home Assistant on the new box (guide 1, Step 2), and on the first screen choose **Restore from backup** instead of Create my smart home.

---

## Reach it away from home

Home Assistant only works on your home network until you choose one of these:

| Option | Cost | Difficulty |
|---|---|---|
| **Home Assistant Cloud** (Settings > Home Assistant Cloud) | Small monthly fee; supports the project | Easiest: log in and it works. Also gives Alexa and Google Assistant. |
| **Tailscale** app (free VPN) | Free for home use | Medium: install the app on Home Assistant and on each phone. |

Don't open ports on your router to Home Assistant unless you know exactly what you're doing.

The phone app's notifications work away from home without any of these. Location for automatic leave and arrive also works; only opening the dashboard from outside needs one of the options.

---

## Troubleshooting

| Problem | Try this |
|---|---|
| Home Assistant page won't open | Is the box on and its network cable in? Wait 5 minutes after a power cut. Try the IP address instead of `homeassistant.local`. |
| It opens in **Recovery mode** | A YAML file has a mistake. Use the File editor link it offers, or copy the kit's `config` again (guide 2, Step 4c), then restart. |
| A device is **Unavailable** | Restart the device. Then **Settings > Devices and services** > its integration > three dots > **Reload**. |
| A routine "does nothing" for one device | Open **Settings > Automations and scenes > Scripts** > the routine > three dots > **Traces**. Each step shows what happened; a red step names the device that failed. |
| Leaving Home runs while someone is home | Their phone stopped reporting location. In the phone's settings allow the Home Assistant app location **Always** and turn off battery saving for it. Meanwhile turn off **Automatic leave and arrive**. |
| I'm Home didn't run | It only runs when the house mode is **Away**. Check the house mode on the dashboard. |
| No weekly battery message | It only sends one when something is under 20 %. |
| I said "no" to the weekly battery check, but still get it | Delete `packages/maintenance.yaml` in the share (copying never deletes old files), then restart. |
| The box is slow or full | **Settings > System > Repairs** and **Settings > System > Storage**. Old backups and a large history use space; reduce how many backups are kept. |

**Asking for help:** the community forum <https://community.home-assistant.io> and the Discord are friendly. Say which Home Assistant version you have (**Settings > About**) and paste the error from **Settings > System > Logs**.

---

You're done. Enjoy your smart home.
