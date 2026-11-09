# 3. Adding devices

**What you'll do:** connect your smart devices to Home Assistant and put each one in its room.
**Time:** 5 to 10 minutes per device.

---

## The one rule: room first, always

Every time you add a device, Home Assistant asks which **area** (room) it is in. **Always pick one.** The dashboard's room cards, and the "light up when I come home" step, only see devices that are in a room.

Forgot one? **Settings > Devices and services > Devices** tab > click the device > pencil icon > **Area**.

---

## How devices usually get added

### 1. Found by itself (easiest)

Many devices on your Wi-Fi are discovered automatically: Philips Hue, Sonos, Google Cast, Apple TV, many printers and TVs.

1. **Settings > Devices and services**. Found devices appear at the top under **Discovered**.
2. Click **Add** > follow the steps (some ask you to press a button on the device or type a PIN shown on the TV).
3. Pick the **area** > **Finish**.

### 2. By brand (cloud account)

Some brands only work through their own app's account (for example many robot vacuums, some aircons and washing machines).

1. **Settings > Devices and services > Add integration**.
2. Search the brand name, e.g. `Roborock`. Click it.
3. Log in with the same email and password as the brand's phone app.
4. Pick the **area** for each device it finds.

If the brand isn't in the list, search the web for `"home assistant" BRANDNAME`. Often there is a community integration in the **Marketplace** (called HACS before Home Assistant 2026.11): **Settings > Marketplace**, search, **Install**, restart, then add it like above.

### 3. Matter (the new common standard)

Devices with the **Matter** logo work with any system, including Home Assistant.

1. On your phone, open the Home Assistant app > **Settings > Devices and services > Add integration > Add Matter device**.
2. Scan the QR code on the device or its box.
3. Pick the **area**.

Matter devices that use **Thread** (it says so on the box) also need a Thread border router nearby: an Apple TV 4K, HomePod mini, recent Google Nest hub, or a Home Assistant Connect ZBT-2 stick.

### 4. Zigbee (cheap sensors and bulbs)

Zigbee needs a small USB stick in the Home Assistant box, such as the **Home Assistant Connect ZBT-2**.

1. Plug in the stick. **Settings > Devices and services** shows **Zigbee Home Automation** under Discovered. Click **Add** and accept the suggestions.
2. To add a device: **Zigbee Home Automation** > **Add device**, then put the device in pairing mode (see its manual; often hold a button for 5 seconds).
3. Pick the **area**.

Tip: use a short USB extension cable for the stick. USB 3 ports and the box itself cause interference.

### 5. Infrared (old aircons, TVs and fans)

Devices with a plastic remote and no Wi-Fi can be controlled with a Wi-Fi infrared blaster (for example a **Broadlink RM4**). This takes more steps; search the Home Assistant docs for "Broadlink" or "SmartIR".

---

## Name things so you can find them

Short, plain names work best, and the room is added for you. For example, in the **Kitchen** area:

| Device name | Shows up as |
|---|---|
| `Ceiling` | Kitchen Ceiling |
| `Coffee machine` | Kitchen Coffee machine |

Rename a device: click it > pencil icon > **Name**. When Home Assistant offers to rename the entity IDs too, say **yes** while you're setting up.

---

## What each routine does with your devices

You don't need to add anything to the routines: they use "every device of this kind", so new devices join in by themselves.

| Kind of device | Routines that use it |
|---|---|
| Lights | Leaving Home, Good Night, Everything Off; I'm Home turns on the arrival room |
| Fans and air purifiers | Leaving Home, Everything Off |
| Aircon and heating (climate) | Leaving Home, Everything Off |
| TVs and speakers | Leaving Home, Good Night, Everything Off |
| Door locks | Leaving Home, Good Night (if you chose locking) |
| Blinds and curtains | Good Morning opens, Good Night closes (if you chose blinds) |
| Robot vacuum | Leaving Home starts it (if you chose that) |

Want a device left out (for example an air purifier that should keep running)? See guide 4, "Leave a device out".

✅ Check: open your dashboard. Each room card shows that room's devices; tap a card to see them all.

---

## If something goes wrong

| Problem | Try this |
|---|---|
| Device not discovered | It must be on the same network as Home Assistant. Guest networks and "client isolation" hide devices. |
| Wi-Fi device won't pair | Many cheap devices only use 2.4 GHz Wi-Fi. Some routers need the 5 GHz band turned off for a few minutes while you pair. |
| Device shows **Unavailable** | Is it powered and online? Restart it, then **Settings > Devices and services** > the integration > three dots > **Reload**. |
| Room card is empty | The device has no area, see "The one rule" above. |
| Matter pairing fails | Pair with the phone app, not the browser, and keep the phone on the home Wi-Fi with Bluetooth on. |

**Next:** [4. Routines and making changes](04-routines-and-changes.md)
