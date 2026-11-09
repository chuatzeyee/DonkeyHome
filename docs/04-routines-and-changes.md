# 4. Routines and making changes

**What you'll do:** understand what the starter kit set up, and change it safely.
**Time:** 10 minutes to read; changes take a few minutes each.

---

## What the kit set up

| Name | Kind | Where it lives |
|---|---|---|
| Good Morning, Leaving Home, I'm Home, Good Night, Everything Off | Scripts (routines) | `packages/routines.yaml` |
| House mode (Home, Away, Night) | Helper | `packages/house.yaml` |
| Automatic leave and arrive (on/off switch) | Helper | `packages/house.yaml` |
| Notify everyone | Script | `packages/house.yaml` |
| Presence: everyone left / first person home | Automations | `packages/presence.yaml` |
| Weekly check: low batteries (Sunday 10:00) | Automation | `packages/maintenance.yaml` |
| Your dashboard | Dashboard | `dashboards/home.yaml` |

You can see all of them in Home Assistant under **Settings > Automations and scenes** (Automations and Scripts tabs). They show a small lock or "read only" note: that's because they come from files. That is on purpose; it keeps them safe from accidental edits.

---

## The easy way to change things: open DonkeyHome again

For anything DonkeyHome asked (rooms, phones, the yes/no choices):

1. Click **DonkeyHome** in the sidebar. Your previous answers are filled in.
2. Change what you like, then click **Set up my home** on the last screen.

DonkeyHome rewrites its own files each time (`configuration.yaml`, `packages/house.yaml`, `routines.yaml`, `presence.yaml`, `maintenance.yaml` and `dashboards/home.yaml`), so hand edits **in those files** are replaced. Keep your own additions in the Home Assistant screens (next section) or in your own package file (below). A copy of the old files is always kept in `donkeyhome_backups`.

---

## Add your own automations (no files needed)

Make new automations in the Home Assistant screens. They're saved in `automations.yaml`, which DonkeyHome never touches.

Example: a lamp on at sunset.

1. **Settings > Automations and scenes > Create automation > Create new automation**.
2. **When:** **Add trigger** > **Sun** > **Sunset**.
3. **Then do:** **Add action** > **Light** > **Turn on** > **Choose entity** > your lamp.
4. **Save** > name it `Lamp on at sunset`.

Tip: in an automation you can use any routine as an action: **Add action** > **Script** > e.g. **Good Night**. For example: run Good Night every day at 23:30.

---

## Leave a device out of a routine

The routines use `entity_id: all`, meaning "every light" or "every fan". To leave something out (say, an air purifier that should keep running), list the devices you **do** want for that step instead.

1. Open `packages/routines.yaml` with the **File editor** app (**Settings > Apps > Install app > File editor > Install > Start**, then **Show in sidebar**).
2. Find the step, for example:

   ```yaml
         - alias: "Fans off"
           action: fan.turn_off
           target:
             entity_id: all
           continue_on_error: true
   ```

3. Replace `entity_id: all` with the devices you want, or with whole rooms:

   ```yaml
           target:
             entity_id:
               - fan.bedroom_ceiling
               - fan.living_room_ceiling
   ```

   or

   ```yaml
           target:
             area_id:
               - bedroom
               - living_room
   ```

   Find a device's entity ID: **Settings > Devices and services > Entities** tab, search for it, and look at the **Entity ID** column. Area IDs are the room name in lowercase with `_` for spaces.

4. **Save**, then **Check configuration** > **Restart**.

Note: running DonkeyHome again undoes this. Write your change down, or keep a copy of the file.

---

## Your own package file

For bigger additions that should survive DonkeyHome, make a new file in the `packages` folder with the File editor app, e.g. `packages/my_extras.yaml`. Every `.yaml` file there is loaded. DonkeyHome only writes `house.yaml`, `routines.yaml`, `presence.yaml` and `maintenance.yaml`, and leaves every other file alone.

```yaml
# packages/my_extras.yaml
automation:
  - id: my_good_night_at_2330
    alias: "Good Night at 23:30"
    triggers:
      - trigger: time
        at: "23:30:00"
    actions:
      - action: script.routine_good_night
```

---

## YAML in two minutes

The files are plain text. Three rules prevent nearly every mistake:

1. **Spaces, never tabs.** Each level is indented by 2 spaces.
2. **Line things up.** Items in a list start with `- ` at the same indent.
3. **Quote text that contains `: `** (a colon and a space), `#`, or starts with `{`, `[`, `*` or `!`. Example: `message: "Heads up: door open"`.

Always run **Check configuration** before **Restart**. If it complains, it names the file and line; the mistake is on that line or the one above.

---

## Make the dashboard yours

DonkeyHome's dashboard is a file (`dashboards/home.yaml`), so it is rewritten each time you run DonkeyHome. Two ways to customise:

- **Edit the file** in File editor. After saving, open the dashboard > three dots > **Refresh**. (Check configuration does not check dashboards: if a card is wrong it shows a red box.)
- **Make your own dashboard in the screens:** **Settings > Dashboards > Add dashboard > Default dashboard**, then pencil icon to add cards by clicking. This one is never touched by DonkeyHome.

**Next:** [5. Looking after it](05-looking-after-it.md)
