#!/usr/bin/env python3
"""End-to-end test: a throwaway Home Assistant + the real DonkeyHome app container, wired together.

  python3 tests/integration_test.py            run the test (needs Docker)
  python3 tests/integration_test.py --shots    also screenshot every wizard screen to /tmp/donkeyhome-shots
                                               (needs the Python Playwright package)

Nothing here touches a real Home Assistant.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HA_IMAGE = os.environ.get("HA_IMAGE", "ghcr.io/home-assistant/home-assistant:2026.10.2")
HA_PORT, APP_PORT = 18200, 18299
HA, APP = f"http://localhost:{HA_PORT}", f"http://localhost:{APP_PORT}"
SUFFIX = str(os.getpid())
ANSWERS = {
    "home_name": "Test Flat", "rooms": ["Living Room", "Kitchen", "Study"], "arrival_room": "Living Room",
    "notify": [], "leave_delay_minutes": 10, "lock_when_leaving": True, "blinds": True, "battery_check": True,
}


def http(method: str, url: str, data: object = None, token: str | None = None, form: bool = False) -> object:
    body = None
    headers = {}
    if data is not None:
        body = urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, body, headers, method=method), timeout=150) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


def wait(fn, what: str, timeout: float = 240) -> object:
    end = time.time() + timeout
    while time.time() < end:
        try:
            result = fn()
            if result:
                return result
        except (urllib.error.URLError, OSError, ValueError):
            pass
        time.sleep(2)
    raise SystemExit(f"Timed out waiting for {what}")


def onboard() -> str:
    cid = HA + "/"
    code = http("POST", HA + "/api/onboarding/users", {
        "client_id": cid, "name": "Test", "username": "test", "password": "test-pass-123", "language": "en"})["auth_code"]
    token = http("POST", HA + "/auth/token", {"grant_type": "authorization_code", "code": code, "client_id": cid},
                 form=True)["access_token"]
    for step in ("core_config", "analytics"):  # finish onboarding so the login page shows
        http("POST", f"{HA}/api/onboarding/{step}", {}, token)
    http("POST", HA + "/api/onboarding/integration", {"client_id": cid, "redirect_uri": cid + "?auth_callback=1"}, token)
    return token


def check(cond: bool, message: str) -> None:
    print(("PASS " if cond else "FAIL ") + message)
    if not cond:
        raise SystemExit(1)


def shots(out: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None)
        for scheme, size in (("light", (390, 844)), ("dark", (390, 844))):
            page = browser.new_page(viewport={"width": size[0], "height": size[1]}, color_scheme=scheme, device_scale_factor=2)
            page.goto(APP + "/")
            page.wait_for_selector("text=Let's start")
            page.screenshot(path=str(out / f"{scheme}-0-welcome.png"), full_page=True)
            page.click("text=Let's start")
            for n in range(1, 7):
                page.wait_for_timeout(300)
                page.screenshot(path=str(out / f"{scheme}-{n}.png"), full_page=True)
                if n == 6:
                    break
                page.click(".dock .btn.dark")
            # The last two screens, with the setup itself faked (the real one runs later in this test).
            fake = {"steps": ["Created the room Study", "Saved a backup", "Wrote 6 files", "Checked: all good",
                              "Restarting Home Assistant"], "backup": "donkeyhome_backups/2026-01-01_10-00-00"}
            page.route("**/api/apply", lambda r: r.fulfill(json={"ok": True, "data": fake, "error": None}))
            page.route("**/api/ping", lambda r: r.fulfill(json={"ok": True, "data": {"core": True}, "error": None}))
            page.click("text=Set up my home")
            page.wait_for_selector("text=Almost there")
            page.screenshot(path=str(out / f"{scheme}-7-working.png"), full_page=True)
            page.wait_for_selector("text=Your home is ready", timeout=90000)
            page.screenshot(path=str(out / f"{scheme}-8-done.png"), full_page=True)
            page.close()
        browser.close()
    print(f"Screenshots in {out}")


def add_demo_devices(ha_name: str, token: str) -> None:
    """Screenshots only: Home Assistant's demo lights, aircons, locks and weather, placed in rooms."""
    subprocess.run(["docker", "exec", ha_name, "sh", "-c", "printf 'demo:\\n' > /config/packages/zz_demo.yaml"], check=True)
    try:
        http("POST", HA + "/api/services/homeassistant/restart", {}, token=token)
    except (urllib.error.URLError, OSError):
        pass
    time.sleep(10)
    wait(lambda: http("GET", HA + "/api/states/light.kitchen_lights", token=token), "demo devices", 300)
    os.environ.update(CORE_WS=f"ws://localhost:{HA_PORT}/api/websocket", HA_TOKEN=token)
    sys.path.insert(0, str(ROOT / "donkeyhome" / "app"))
    import importlib
    import haclient
    importlib.reload(haclient)
    rooms = {"living": "living_room", "ceiling": "living_room", "kitchen": "kitchen", "bed": "study",
             "office": "study", "entrance": "living_room", "hvac": "living_room", "heatpump": "study", "ecobee": "kitchen"}
    with haclient.WebSocket(f"ws://localhost:{HA_PORT}/api/websocket") as ws:
        for entry in ws.call("config/entity_registry/list"):
            if entry["entity_id"].split(".")[0] in ("light", "climate"):
                area = next((a for k, a in rooms.items() if k in entry["entity_id"]), None)
                if area and entry.get("device_id"):  # the demo's entities take their room from their device
                    ws.call("config/device_registry/update", device_id=entry["device_id"], area_id=area)
    for entity in ("light.kitchen_lights", "light.living_room_rgbww_lights"):
        http("POST", HA + "/api/services/light/turn_on", {"entity_id": entity}, token=token)
    http("POST", HA + "/api/services/light/turn_off", {"entity_id": "light.ceiling_lights"}, token=token)
    http("POST", HA + "/api/services/light/turn_off", {"entity_id": "light.entrance_color_white_lights"}, token=token)


def dashboard_shots(out: Path, token: str) -> None:
    """Log in to the throwaway Home Assistant and screenshot DonkeyHome's dashboard on a phone, dark then light."""
    from playwright.sync_api import sync_playwright

    ui = f"http://127.0.0.1:{HA_PORT}"  # not localhost: avoids the service worker reloading mid-shot
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None)
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        page.goto(ui + "/", wait_until="networkidle")
        page.fill("input[name=username]", "test")
        page.fill("input[name=password]", "test-pass-123")
        page.keyboard.press("Enter")
        page.wait_for_function("() => document.querySelector('home-assistant')?.hass?.connected", timeout=60000)
        for scheme in ("dark", "light"):
            if scheme == "light":
                http("POST", HA + "/api/services/script/donkeyhome_toggle_theme", {}, token=token)
                time.sleep(2)
            for path in ("home", "room-living-room", "lights", "climate"):
                page.goto(f"{ui}/my-home/{path}", wait_until="networkidle")
                page.wait_for_timeout(2500)
                page.screenshot(path=str(out / f"ha-{scheme}-{path}.png"), full_page=path == "home")
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", action="store_true")
    args = ap.parse_args()
    cfg = Path(tempfile.mkdtemp(prefix="donkeyhome-it-"))
    os.chmod(cfg, 0o777)
    ha_name, app_name = f"dh-ha-{SUFFIX}", f"dh-app-{SUFFIX}"
    try:
        subprocess.run(["docker", "build", "-q", "-t", "donkeyhome-test", str(ROOT / "donkeyhome")], check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(["docker", "run", "-d", "--name", ha_name, "-p", f"{HA_PORT}:8123", "-v", f"{cfg}:/config",
                        HA_IMAGE], check=True, stdout=subprocess.DEVNULL)
        wait(lambda: http("GET", HA + "/api/onboarding") is not None, "Home Assistant to start")
        token = onboard()
        subprocess.run(["docker", "run", "-d", "--name", app_name, "--network", "host",
                        "-e", f"CORE_URL={HA}", "-e", f"CORE_WS=ws://localhost:{HA_PORT}/api/websocket",
                        "-e", f"HA_TOKEN={token}", "-e", "ALLOWED_CLIENT=*", "-e", f"PORT={APP_PORT}",
                        "-e", "DATA_DIR=/tmp/data", "-v", f"{cfg}:/homeassistant", "donkeyhome-test"],
                       check=True, stdout=subprocess.DEVNULL)

        info = wait(lambda: http("GET", APP + "/api/discover"), "DonkeyHome to answer")
        check(info["ok"], "discover answers")
        names = [a["name"] for a in info["data"]["areas"]]
        check("Living Room" in names and "Study" not in names, f"discover sees the starting rooms {names}")
        check(info["data"]["config_status"] == "fresh", "fresh configuration.yaml detected")
        check("Let's start" in urllib.request.urlopen(APP + "/app.js").read().decode(), "wizard page is served")

        try:
            http("POST", APP + "/api/apply", {**ANSWERS, "rooms": []})
            check(False, "empty rooms refused")
        except urllib.error.HTTPError as err:
            check(err.code == 400 and "room" in json.loads(err.read())["error"], "empty rooms refused with a message")

        if args.shots:
            shots(Path("/tmp/donkeyhome-shots"))

        mine = "- id: mine\n  alias: Mine\n  triggers: []\n  actions: []\n"  # the user's own automation
        subprocess.run(["docker", "exec", ha_name, "sh", "-c", f"printf '{mine}' > /config/automations.yaml"], check=True)
        result = http("POST", APP + "/api/apply", ANSWERS)
        check(result["ok"], "apply succeeds")
        steps = result["data"]["steps"]
        print("     " + "\n     ".join(steps))
        check(any("Study" in s for s in steps), "the missing room was created")
        check((cfg / "packages" / "routines.yaml").exists(), "routines written")
        check("id: mine" in (cfg / "automations.yaml").read_text(), "the user's own automation was kept")
        check(any((cfg / "donkeyhome_backups").iterdir()), "backup folder made")

        def back_up() -> bool:
            return http("GET", APP + "/api/ping")["data"]["core"] and http(
                "GET", HA + "/api/states/script.routine_good_night", token=token) is not None
        wait(back_up, "Home Assistant to restart with the new setup", 300)
        check(True, "Home Assistant restarted and loaded the routines")
        for entity in ("input_select.house_mode", "input_boolean.auto_presence", "script.routine_leaving_home",
                       "automation.presence_everyone_left", "automation.weekly_check_low_batteries", "automation.mine"):
            state = wait(lambda e=entity: http("GET", f"{HA}/api/states/{e}", token=token), entity, 90)["state"]
            check(state != "unavailable", f"{entity} exists")
        http("POST", HA + "/api/services/script/routine_good_night", {}, token=token)
        time.sleep(2)
        mode = http("GET", HA + "/api/states/input_select.house_mode", token=token)["state"]
        check(mode == "Night", "Good Night runs and sets the house mode to Night")
        boards = http("GET", APP + "/api/discover")["data"]
        check(boards["config_status"] == "donkeyhome" and boards["saved"]["home_name"] == "Test Flat",
              "second visit remembers the answers")
        if args.shots:
            add_demo_devices(ha_name, token)
            dashboard_shots(Path("/tmp/donkeyhome-shots"), token)
        print("\nAll good.")
        return 0
    finally:
        if os.environ.get("KEEP"):  # debugging: leave both containers running
            print(f"Kept: Home Assistant {HA} (test / test-pass-123), app {APP}, config {cfg}")
            return 0
        subprocess.run(["docker", "rm", "-f", ha_name, app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["docker", "run", "--rm", "-v", f"{cfg}:/c", "alpine", "rm", "-rf", "/c/.storage", "/c/deps"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    sys.exit(main())
