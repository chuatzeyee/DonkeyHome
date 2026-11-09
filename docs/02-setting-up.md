# 2. Setting up: run the wizard and copy your configuration

**What you'll do:** answer a few questions about your home, copy the files the wizard makes into Home Assistant, and switch on the routines and the dashboard.
**Time:** about 45 minutes.
**You need:** guide 1 finished, your laptop, and your Home Assistant login.

---

## Step 1: Download this kit

1. On this project's GitHub page, click the green **Code** button > **Download ZIP**.
2. Unzip it somewhere easy, like your Desktop.

(If you know git: `git clone` works too.)

✅ Check: you have a folder with `README.md`, `setup.bat`, `setup.sh`, `wizard/` and `docs/` in it.

---

## Step 2: Run the wizard

The wizard needs **Python 3.10 or newer**.

- **Windows:** double-click **`setup.bat`**. If it says Python is missing, install it from <https://www.python.org/downloads/> and tick **Add python.exe to PATH** on the first installer screen. Then double-click `setup.bat` again.
- **Mac:** open **Terminal**, type `cd ` (with a space), drag the kit's folder into the Terminal window, press Enter, then type `./setup.sh` and press Enter. If it asks to install developer tools, say yes and run it again.
- **Linux:** open a terminal in the kit's folder and run `./setup.sh`.

Answer the questions. Press **Enter** to keep the suggestion in `[brackets]`.

| Question | Tips |
|---|---|
| What do you call your home? | Shown as the dashboard's name, e.g. `The Tan Home`. |
| Who lives there? | First names, separated by commas. |
| Which rooms do you have? | E.g. `Living Room, Kitchen, Bedroom, Study`. Plain letters and numbers only. **Write this list down**: you'll create rooms with exactly these names in Step 3. |
| Which room should light up when you come home after dark? | Usually the room by the front door. |
| Phone notify names | **Leave empty for now.** You'll fill them in at Step 7. |
| Minutes after the last person leaves | 10 is a good start. Shorter can switch things off when someone only took the rubbish out. |
| The yes/no questions | Pick what suits you. You can change any answer later by running the wizard again. |

The wizard writes a folder called **`config`** inside the kit and saves your answers in **`my-answers.json`**, so next time it suggests your own answers.

✅ Check: the wizard ends with **Done** and lists your rooms; the kit now has a `config` folder.

---

## Step 3: Create your rooms (areas)

The routines and the dashboard work by room, so Home Assistant must know your rooms **with exactly the names you gave the wizard**.

1. In Home Assistant: **Settings > Areas, labels and zones**.
2. Home Assistant already made a few (Living Room, Kitchen, Bedroom). Keep the ones that match your list; delete or rename the rest (click the area > pencil icon).
3. For each missing room: **Create area** > type the name exactly as in your list > **Create**.

✅ Check: the Areas page shows the same rooms as the wizard's list. Spelling matters; capitals don't.

---

## Step 4: Copy the configuration into Home Assistant

You'll use the **Samba share** app, which makes Home Assistant's folder show up on your laptop like a USB stick.

### 4a. Install the Samba share app (once)

1. **Settings > Apps > Install app**, search **Samba share**, click it > **Install**.
2. Open its **Configuration** tab. Type a **Username** and **Password** (new ones, just for this share). Click **Save**.
3. **Info** tab > **Start**.

### 4b. Make a backup first

**Settings > System > Backups > Backup now**. Wait until it shows up in the list.

### 4c. Copy the files

1. Open the share on your laptop:
   - **Windows:** File Explorer > type `\\homeassistant\config` in the address bar > Enter. Sign in with the **Samba** username and password from 4a.
   - **Mac:** Finder > **Go > Connect to Server** > `smb://homeassistant.local/config` > **Connect**, then the Samba username and password.
   If the name doesn't work, use the IP address instead, like `\\192.168.1.50\config`.
2. Open the kit's **`config`** folder on your laptop. Select **everything inside it** (not the folder itself): `configuration.yaml`, `automations.yaml`, `scripts.yaml`, `scenes.yaml`, `packages` and `dashboards`.
3. Drag them into the share window. When asked, choose **Replace** for the four `.yaml` files.

Leave everything else in the share alone (`.storage`, `secrets.yaml`, the database and log files belong to Home Assistant).

> **Already made automations in the Home Assistant screens?** Replacing `automations.yaml`, `scripts.yaml` or `scenes.yaml` would delete them. In that case, don't copy those three files; copy only `configuration.yaml`, `packages` and `dashboards`.

✅ Check: the share now has a `packages` folder with `house.yaml`, `routines.yaml` and `presence.yaml` in it.

---

## Step 5: Check and restart

1. **Settings > Tools > YAML** tab > **Check configuration**. Wait for **Configuration will not prevent Home Assistant from starting!**
2. Click **Restart** > **Restart Home Assistant**. Wait about a minute and refresh the page.

✅ Check: the sidebar has a new entry with your home's name. Open it: you see **Routines**, **House** and **Rooms**.

---

## Step 6: Add your devices

Now connect your lights, plugs, aircon and so on. Guide 3 explains how. The most important rule: **put every device in its room**, because the room cards and the "light up when I come home" step use rooms.

Come back here when your main devices are in.

---

## Step 7: Phone notifications

1. Make sure each phone has the Home Assistant app and is logged in (guide 1, Step 5).
2. **Settings > Tools > Actions** tab. In the action box type `mobile_app`. You see one `notify.mobile_app_...` line per phone, for example `notify.mobile_app_alex_iphone`. Write them down.
3. Run the wizard again (Step 2). At **Phone notify names** type them separated by commas, e.g. `mobile_app_alex_iphone, mobile_app_sam_pixel`. Keep every other answer by pressing Enter.
4. Copy **`packages`** into the share again (Step 4c), then **Check configuration** > **Restart** (Step 5).
5. Test it: **Settings > Tools > Actions** tab > pick **Script: Notify everyone** > type `Hello` in **message** > **Perform action**.

✅ Check: every phone gets "Hello".

---

## Step 8: Switch on automatic leave and arrive

Only do this once Step 7 works and every person's phone shows **Home** under **Settings > People**.

1. Open your dashboard. Under **House**, turn on **Automatic leave and arrive**.

From now on:

- When **everyone** has been away for the number of minutes you chose, **Leaving Home** runs (and you get a message).
- When the **first person** comes back, **I'm Home** runs.

✅ Check: next time everyone goes out, you get "Everyone has left. The house is switched off."

---

## Step 9: Try the routines

Tap each button under **Routines** once while you're home:

| Button | What it does |
|---|---|
| **Good Morning** | House mode Home; opens the blinds (if you chose that). |
| **Leaving Home** | House mode Away; switches off what you chose in the wizard; locks the doors (if chosen); sends a message. |
| **I'm Home** | House mode Home; lights in your arrival room if it is dark outside. |
| **Good Night** | House mode Night; lights and TVs off; locks and closes blinds (if chosen). |
| **Everything Off** | Lights, fans, aircon, TVs and speakers off. Nothing else. |

Guide 4 shows how to change them.

✅ Check: each button does what the table says, for the devices you have.

---

## If something goes wrong

| Problem | Try this |
|---|---|
| `setup.bat` flashes and closes | Python is missing or not on PATH. Reinstall Python and tick **Add python.exe to PATH**. |
| Mac says `permission denied: ./setup.sh` | Type `bash setup.sh` instead. |
| `\\homeassistant\config` refuses your password | Use the **Samba share** username and password (its Configuration tab), not your Home Assistant login. Make sure the app is **Started**. |
| Check configuration names a file and line | You (or an editor) changed that file. Run the wizard again and copy the files again; that rewrites them cleanly. |
| A room card shows a red error | The room doesn't exist in Home Assistant, or is spelled differently. Fix it in Step 3. |
| The dashboard isn't in the sidebar | `configuration.yaml` wasn't replaced, or landed in a subfolder. It must sit directly in the share, next to `.storage`. |
| Notify everyone fails | A notify name is wrong. Compare with **Settings > Tools > Actions** and run Step 7 again. |
| Leaving Home ran when someone was home | That person's phone isn't reporting location. In the phone's settings, allow the Home Assistant app location **Always**. |

**Next:** [3. Adding devices](03-adding-devices.md)
