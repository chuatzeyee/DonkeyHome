# 1. Getting started: install Home Assistant

**What you'll do:** pick a small computer, put Home Assistant on it, and make your first login.
**Time:** about 1 hour.
**You need no programming knowledge.** If you can install an app on your phone, you can do this.

Written for Home Assistant 2026.10 and 2026.11. Menu names sometimes move between versions; if a menu is not where this guide says, use the search box at the top of the Settings page.

---

## What is Home Assistant?

Home Assistant is free software that runs on a small computer at home. It talks to your smart lights, plugs, aircon, TV, robot vacuum and phones, from almost any brand, and lets them work together: one button (or your phone leaving the house) can switch everything off.

It runs **in your home**, not in someone's cloud, so most things keep working when the internet is down.

### Words you'll see

| Word | Plain meaning |
|---|---|
| **Device** | A real thing: a bulb, a plug, a TV. |
| **Entity** | One thing a device can do or report. A smart plug may have two: "on/off" and "power used". Each has an ID like `light.kitchen_ceiling`. |
| **Area** | A room. You put devices into areas. This starter kit uses areas a lot. |
| **Integration** | The connector for one brand or kind of device (for example "Philips Hue" or "Matter"). |
| **App** | Extra software that runs next to Home Assistant on the same box (older guides call these "add-ons"). |
| **Automation** | "When this happens, do that." Runs by itself. |
| **Script / routine** | A list of steps you start with one tap, like **Good Night**. |
| **Dashboard** | A screen of buttons and cards. |
| **YAML** | The plain-text format the configuration files are written in. The wizard writes it for you. |

---

## Step 1: Choose the computer

Pick **one**. All three work well with this starter kit.

| Option | Good for | Roughly |
|---|---|---|
| **Home Assistant Green** | The easiest. It arrives with Home Assistant already installed. | Plug in and go |
| **Raspberry Pi 5** (4 GB or more) with an SSD or a good 64 GB+ SD card and the official power supply | Tinkerers, very low power | 30 minutes of setup |
| **A used mini PC** (Intel N100 or similar, 8 GB RAM, 128 GB+ SSD) | Most power for the money, room to grow | 1 hour of setup |

Also have ready:

- A **network cable** (Ethernet). Plug the box into your Wi-Fi router. Do not use Wi-Fi for the box itself.
- A **laptop or desktop** on the same home network, to follow these guides.
- Your **phone** with the free **Home Assistant** app (App Store or Google Play).

✅ Check: you have the box, its power supply and a network cable, and the box is next to your router.

---

## Step 2: Put Home Assistant on it

Follow the part for your box, then go to Step 3.

### A. Home Assistant Green

1. Plug the network cable into the Green and into your router.
2. Plug in the power. Wait 5 minutes.

That's it.

### B. Raspberry Pi 5

1. On your laptop, install **Raspberry Pi Imager** from <https://www.raspberrypi.com/software/>.
2. Put the SD card (or the SSD in a USB case) into your laptop.
3. In Imager: **Choose device** > Raspberry Pi 5. **Choose OS** > **Other specific-purpose OS** > **Home assistants and home automation** > **Home Assistant** > **Home Assistant OS (RPi 5)**. **Choose storage** > your card.
4. Click **Next** > **No** to customisation > **Yes** to erase. Wait until it says it is finished.
5. Put the card in the Pi, plug in the network cable, then the power. Wait 5 minutes.

### C. Mini PC

This erases everything on the mini PC (including Windows). Copy off anything you want to keep first.

1. Follow the official guide for "Generic x86-64": <https://www.home-assistant.io/installation/generic-x86-64>. In short: you start the mini PC from a USB stick with Ubuntu on it, download the Home Assistant OS image, and write it onto the mini PC's internal disk with the **Disks** app (**Restore Disk Image**).
2. Before that, in the mini PC's BIOS (usually press **Del** or **F7** while it starts), make sure **Secure Boot** is off and **UEFI** boot is on.
3. Remove the USB stick, plug in the network cable and restart. Wait 5 minutes.

✅ Check: the box's network light blinks, and the router's app or web page lists a device called **homeassistant**.

---

## Step 3: First login (onboarding)

1. On your laptop, open a browser and go to **<http://homeassistant.local>**.
   If that does not open, try **<http://homeassistant.local:8123>**, then the box's IP address from your router's device list, for example `http://192.168.1.50`.
2. You may see "Preparing Home Assistant". This can take up to 20 minutes the first time. Leave the page open.
3. Click **Create my smart home**.
4. Create **your** account. Write the username and password down somewhere safe (a password manager is best). This is the main admin account.
5. **Home location:** search your address. This sets your time zone, units and the sunrise and sunset times used by the routines.
6. **Analytics:** choose what you like. Nothing breaks either way.
7. Home Assistant may show devices it already found on your network. Leave them for now; you'll add them in guide 2.
8. Click **Finish**.

✅ Check: you see the Home Assistant **Overview** page with a sidebar on the left.

---

## Step 4: Give it a fixed address

So your phone and the wizard always find it, ask your router to keep Home Assistant on the same IP address.

1. Open your router's app or web page and find the device list.
2. Find **homeassistant** and choose **Reserve IP**, **Address reservation** or **Static DHCP** (the name depends on the router).
3. Note the address, for example `192.168.1.50`.

✅ Check: in Home Assistant, **Settings > System > Network** shows the same address.

---

## Step 5: Install the phone app

1. Install the **Home Assistant** app on every phone in the house.
2. Open it. It should find your home by itself; if not, type the address from Step 4, like `http://192.168.1.50`.
3. Log in. Each person should have **their own** login: create them first under **Settings > People > Add person**, turn on **Allow login**, and give them a username and password.
4. When the app asks, **allow location "Always"** and **allow notifications**. Location lets the house know when everyone has left; notifications let it tell you.

✅ Check: **Settings > People** lists everyone, and each person shows **Home** within a few minutes.

---

## Step 6: Turn on backups

Do this now, before anything else. A backup lets you undo almost any mistake.

1. **Settings > System > Backups > Set up backups**.
2. Choose **Recommended** (daily, keeps the last few).
3. **Download the emergency kit** and keep it in your password manager. Without its key nobody can restore a backup, including you.

✅ Check: **Settings > System > Backups** shows the next scheduled backup.

---

## If something goes wrong

| Problem | Try this |
|---|---|
| `homeassistant.local` doesn't open | Use the IP address from the router instead. Some networks and older Android phones don't support `.local` names. |
| "Preparing Home Assistant" for over 30 minutes | Check the network cable. Turn the box off and on once. |
| Mini PC starts Windows or a black screen | In the BIOS, disable Secure Boot and choose the internal disk first in the boot order. |
| Raspberry Pi keeps restarting | Use the official power supply. Weak power supplies cause most Pi problems. |
| Forgot the password | Owner accounts can be reset from the box's console: plug in a screen and keyboard and type `auth reset --username YOURNAME --password NEWPASSWORD`. |

**Next:** [2. Setting up: run the wizard and copy your configuration](02-setting-up.md)
