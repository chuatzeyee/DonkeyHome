#!/usr/bin/env python3
"""DonkeyHome: Home Assistant starter wizard.

Turns a few answers about your home into a ready Home Assistant configuration.
The DonkeyHome app (server.py) uses it behind its point-and-click screens; you can also run it
yourself in a terminal (advanced, see docs/advanced-command-line.md). Standard library only.

  python3 donkeyhome/app/wizard.py                            ask the questions, write config/
  python3 donkeyhome/app/wizard.py --answers my-answers.json  no questions, use a saved answers file
  python3 donkeyhome/app/wizard.py --out somewhere/else       write the files somewhere else

Your answers are saved to my-answers.json so you can run the wizard again later and only
change what you need.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("Python 3.10 or newer is needed. Get it from https://www.python.org/downloads/")

# When run from a download: donkeyhome/app/wizard.py -> the repository folder. (Not used inside the app.)
ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUT = ROOT / "config"
DEFAULT_ANSWERS = ROOT / "my-answers.json"

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '&-]{0,39}$")
NOTIFY_RE = re.compile(r"^[a-z0-9_]+$")
MARKER = "# Made by DonkeyHome."
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
ASSETS = HERE / "assets"  # copied as-is into the config folder: theme, fonts, button-card
ASSET_VERSION = "2"  # bump when anything in assets/www changes, so browsers fetch the new files
UI_FILES = ("automations.yaml", "scripts.yaml", "scenes.yaml")  # created if missing, never overwritten
OPTIONAL_FILES = ("packages/maintenance.yaml",)  # removed again when switched off (only if DonkeyHome made it)

# Yes/no questions: key, question, default.
CHOICES = [
    ("lights_off_when_leaving", "Turn off all lights when everyone leaves?", True),
    ("climate_off_when_leaving", "Turn off aircon, heating and fans when everyone leaves?", True),
    ("media_off_when_leaving", "Turn off TVs and speakers when everyone leaves?", True),
    ("lock_when_leaving", "Lock the doors when everyone leaves and at Good Night?", True),
    ("vacuum_when_away", "Start the robot vacuum when everyone leaves?", False),
    ("blinds", "Open the blinds at Good Morning and close them at Good Night?", False),
    ("battery_check", "Send a weekly list of devices with low batteries?", True),
]

EXAMPLE = {
    "home_name": "Our Home",
    "people": ["Alex", "Sam"],
    "rooms": ["Living Room", "Kitchen", "Bedroom", "Bathroom"],
    "arrival_room": "Living Room",
    "notify": [],
    "leave_delay_minutes": 10,
    **{key: default for key, _, default in CHOICES},
}


class AnswerError(ValueError):
    """An answer that cannot be used. The message tells the user what to fix."""


# ---------------------------------------------------------------- validation
def slug(name: str) -> str:
    """The id Home Assistant gives an area or person with this name ('Living Room' -> 'living_room')."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def check_name(name: str, what: str) -> str:
    name = " ".join(str(name).split())
    if not NAME_RE.match(name):
        raise AnswerError(f"{what} '{name}' should be 1 to 40 letters, numbers or spaces (no accents or symbols).")
    return name


def check_notify(name: str) -> str:
    name = str(name).strip().removeprefix("notify.")
    if not NOTIFY_RE.match(name):
        raise AnswerError(f"Notify name '{name}' should look like mobile_app_alex_iphone (lowercase, numbers, _).")
    return name


def validate(raw: dict) -> dict:
    """Return a clean copy of the answers, or raise AnswerError with a friendly message."""
    rooms = [check_name(r, "Room") for r in raw.get("rooms", [])]
    if not rooms:
        raise AnswerError("Add at least one room.")
    if len({slug(r) for r in rooms}) != len(rooms):
        raise AnswerError("Two rooms have the same name. Give each room its own name.")
    arrival = check_name(raw.get("arrival_room") or rooms[0], "Arrival room")
    if arrival not in rooms:
        raise AnswerError(f"The arrival room '{arrival}' is not one of your rooms: {', '.join(rooms)}.")
    area_ids = {}
    for room, area_id in (raw.get("area_ids") or {}).items():
        if not NOTIFY_RE.match(str(area_id)):
            raise AnswerError(f"The room id '{area_id}' is not valid.")
        area_ids[check_name(room, "Room")] = str(area_id)
    try:
        delay = int(raw.get("leave_delay_minutes", 10))
    except (TypeError, ValueError):
        raise AnswerError("The leave delay must be a whole number of minutes.") from None
    if not 1 <= delay <= 120:
        raise AnswerError("The leave delay must be between 1 and 120 minutes.")
    clean = {
        "home_name": check_name(raw.get("home_name", "Home"), "Home name"),
        "people": [check_name(p, "Person") for p in raw.get("people", [])],
        "rooms": rooms,
        "arrival_room": arrival,
        "notify": [check_notify(n) for n in raw.get("notify", [])],
        "leave_delay_minutes": delay,
        "area_ids": {room: area_ids.get(room, slug(room)) for room in rooms},
    }
    for key, _, default in CHOICES:
        clean[key] = bool(raw.get(key, default))
    return clean


# ---------------------------------------------------------------- asking
def ask(question: str, default: str = "") -> str:
    shown = f" [{default}]" if default else ""
    reply = input(f"{question}{shown}: ").strip()
    return reply or default


def ask_list(question: str, default: list[str]) -> list[str]:
    reply = ask(question + " (separate with commas)", ", ".join(default))
    return [item.strip() for item in reply.split(",") if item.strip()]


def ask_yes(question: str, default: bool) -> bool:
    while True:
        reply = ask(question + " (y/n)", "y" if default else "n").lower()
        if reply in ("y", "yes", "n", "no"):
            return reply.startswith("y")
        print("  Please type y or n.")


def ask_until_valid(prev: dict) -> dict:
    while True:
        raw = {
            "home_name": ask("What do you call your home?", prev["home_name"]),
            "people": ask_list("Who lives there?", prev["people"]),
            "rooms": ask_list("Which rooms do you have?", prev["rooms"]),
        }
        rooms = raw["rooms"] or [""]
        default_room = prev["arrival_room"] if prev["arrival_room"] in rooms else rooms[0]
        raw["arrival_room"] = ask("Which room should light up when you come home after dark?", default_room)
        print("\nPhone notifications: leave this empty for now if the Home Assistant app is not on your phones yet.")
        print("docs/advanced-command-line.md shows how to find these names.")
        raw["notify"] = ask_list("Phone notify names", prev["notify"])
        raw["leave_delay_minutes"] = ask("How many minutes after the last person leaves should the house switch off?",
                                         str(prev["leave_delay_minutes"]))
        print()
        for key, question, _ in CHOICES:
            raw[key] = ask_yes(question, prev[key])
        try:
            return validate(raw)
        except AnswerError as err:
            print(f"\nThat did not work: {err}\nLet's try again (your answers are kept as the defaults).\n")
            prev = {**prev, **raw}


# ---------------------------------------------------------------- writing YAML
def q(text: str) -> str:
    """Quote a value for YAML (JSON strings are valid YAML)."""
    return json.dumps(text, ensure_ascii=False)


def step(alias: str, action: str, target: str = "entity_id: all", data: str = "") -> str:
    lines = [f"      - alias: {q(alias)}", f"        action: {action}", "        target:", f"          {target}"]
    if data:
        lines += ["        data:", f"          {data}"]
    lines.append("        continue_on_error: true")
    return "\n".join(lines)


def mode_step(mode: str) -> str:
    return (f"      - alias: {q('House mode ' + mode)}\n"
            "        action: input_select.select_option\n"
            "        target:\n          entity_id: input_select.house_mode\n"
            f"        data:\n          option: {mode}")


def script(key: str, alias: str, icon: str, description: str, steps: list[str]) -> str:
    return (f"  {key}:\n    alias: {q(alias)}\n    icon: {icon}\n    description: {q(description)}\n"
            "    mode: restart\n    sequence:\n" + "\n".join(steps))


def area_of(a: dict, room: str) -> str:
    return a.get("area_ids", {}).get(room) or slug(room)


def configuration_yaml(a: dict) -> str:
    return f"""{MARKER} Home Assistant configuration for {a['home_name']}.
# Most of the logic lives in packages/ (one file per subject). This file just switches things on.
# After you edit any YAML file: Settings > Tools > YAML > Check configuration, then Restart.

# The standard Home Assistant features (history, logbook, phone app, sun, zones, backups and more).
default_config:

frontend:
  # Themes from the themes folder, including the DonkeyHome light and dark themes.
  themes: !include_dir_merge_named themes
  # The DonkeyHome look: button-card (www/donkeyhome/button-card.js, MIT) and the Google Sans and
  # Instrument Serif fonts (www/donkeyhome/fonts.css, SIL Open Font License).
  extra_module_url:
    - /local/donkeyhome/button-card.js?v={ASSET_VERSION}
    - /local/donkeyhome/fonts.js?v={ASSET_VERSION}

homeassistant:
  # Every .yaml file in packages/ is loaded automatically.
  packages: !include_dir_named packages

lovelace:
  dashboards:
    my-home:
      mode: yaml
      filename: dashboards/home.yaml
      title: {q(a['home_name'])}
      icon: mdi:home
      show_in_sidebar: true

# Automations, scripts and scenes you make in the Home Assistant screens are saved in these files.
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
"""


def house_yaml(a: dict) -> str:
    sends = "\n".join(
        f"      - action: notify.{n}\n        data:\n          title: {q(a['home_name'])}\n"
        "          message: \"{{ message }}\"\n        continue_on_error: true" for n in a["notify"])
    return f"""{MARKER}
# House mode, the automatic leave/arrive switch and the "notify everyone" helper.

input_select:
  house_mode:
    name: House mode
    icon: mdi:home-switch
    options:
      - Home
      - Away
      - Night

input_boolean:
  auto_presence:
    # Off until everyone's phone shows them at home (Settings > People). Then switch it on.
    name: Automatic leave and arrive
    icon: mdi:map-marker-radius

script:
  notify_everyone:
    alias: Notify everyone
    icon: mdi:message-alert
    description: Sends a message to every phone listed in the wizard, and always to the bell icon in Home Assistant.
    mode: queued
    fields:
      message:
        description: What to say
        example: The front door is open
        required: true
        selector:
          text:
    sequence:
      - action: persistent_notification.create
        data:
          title: {q(a['home_name'])}
          message: "{{{{ message }}}}"
{sends}
""".rstrip() + "\n"


def routines_yaml(a: dict) -> str:
    arrival = f"area_id: {area_of(a, a['arrival_room'])}"
    leave, night, off = [mode_step("Away")], [mode_step("Night")], []
    if a["lights_off_when_leaving"]:
        leave.append(step("Lights off", "light.turn_off"))
    if a["climate_off_when_leaving"]:
        leave += [step("Aircon and heating off", "climate.turn_off"), step("Fans off", "fan.turn_off")]
    if a["media_off_when_leaving"]:
        leave.append(step("TVs and speakers off", "media_player.turn_off"))
    if a["lock_when_leaving"]:
        leave.append(step("Lock the doors", "lock.lock"))
        night.append(step("Lock the doors", "lock.lock"))
    if a["vacuum_when_away"]:
        leave.append(step("Start the robot vacuum", "vacuum.start"))
    leave.append("      - action: script.notify_everyone\n        data:\n"
                 "          message: Everyone has left. The house is switched off.")
    morning = [mode_step("Home")]
    if a["blinds"]:
        morning.append(step("Open the blinds", "cover.open_cover"))
        night.append(step("Close the blinds", "cover.close_cover"))
    night += [step("Lights off", "light.turn_off"), step("TVs off", "media_player.turn_off")]
    off += [step("Lights off", "light.turn_off"), step("Fans off", "fan.turn_off"),
            step("Aircon and heating off", "climate.turn_off"), step("TVs and speakers off", "media_player.turn_off")]
    arrive = [mode_step("Home"),
              f"      - alias: {q(a['arrival_room'] + ' lights on if it is dark')}\n"
              "        if:\n          - condition: state\n            entity_id: sun.sun\n            state: below_horizon\n"
              "        then:\n          - action: light.turn_on\n            target:\n"
              f"              {arrival}\n            continue_on_error: true"]
    scripts = [
        script("routine_good_morning", "Good Morning", "mdi:weather-sunset-up", "House mode Home" + (", blinds open." if a["blinds"] else "."), morning),
        script("routine_leaving_home", "Leaving Home", "mdi:exit-run",
               "House mode Away and switches the house off as chosen in the wizard.", leave),
        script("routine_arriving_home", "I'm Home", "mdi:home-import-outline",
               f"House mode Home; {a['arrival_room']} lights on if it is dark.", arrive),
        script("routine_good_night", "Good Night", "mdi:weather-night",
               "House mode Night, lights and TVs off, doors locked, blinds closed (as chosen).", night),
        script("routine_everything_off", "Everything Off", "mdi:power",
               "Lights, fans, aircon, TVs and speakers off. Nothing else changes.", off),
    ]
    return (f"{MARKER}\n# The one-tap routines. Each device step has continue_on_error, so one offline device never\n"
            "# stops a routine. 'entity_id: all' means every device of that kind, so new devices are\n"
            "# included automatically. To change a routine, edit this file or run the wizard again.\n\n"
            "script:\n" + "\n\n".join(scripts) + "\n")


def presence_yaml(a: dict) -> str:
    return f"""{MARKER}
# Runs Leaving Home when the last person leaves and I'm Home when the first person arrives.
# Only works when the "Automatic leave and arrive" switch on the dashboard is on.
# zone.home counts how many people are at home.

automation:
  - id: presence_everyone_left
    alias: "Presence: everyone left"
    triggers:
      - trigger: numeric_state
        entity_id: zone.home
        below: 1
        for:
          minutes: {a['leave_delay_minutes']}
    conditions:
      - condition: state
        entity_id: input_boolean.auto_presence
        state: "on"
      - condition: template
        value_template: "{{{{ trigger.from_state.state not in ['unknown', 'unavailable'] }}}}"
    actions:
      - action: script.routine_leaving_home

  - id: presence_first_home
    alias: "Presence: first person home"
    triggers:
      - trigger: numeric_state
        entity_id: zone.home
        above: 0
    conditions:
      - condition: state
        entity_id: input_boolean.auto_presence
        state: "on"
      - condition: state
        entity_id: input_select.house_mode
        state: Away
    actions:
      - action: script.routine_arriving_home
"""


BATTERY_TEMPLATE = (
    "{% set ns = namespace(low=[]) %}"
    "{% for s in states.sensor if s.attributes.device_class == 'battery' and s.state | is_number"
    " and s.state | float < 20 %}{% set ns.low = ns.low + [s.name ~ ' (' ~ s.state ~ '%)'] %}{% endfor %}"
    "{{ ns.low | join(', ') }}"
)


def maintenance_yaml(a: dict) -> str:
    return f"""{MARKER}
# Weekly check-up: Sunday 10:00, lists every battery under 20 %.

automation:
  - id: weekly_battery_check
    alias: "Weekly check: low batteries"
    triggers:
      - trigger: time
        at: "10:00:00"
    conditions:
      - condition: time
        weekday: sun
    actions:
      - variables:
          low: >-
            {BATTERY_TEMPLATE}
      - condition: template
        value_template: "{{{{ low != '' }}}}"
      - action: script.notify_everyone
        data:
          message: "Batteries to change: {{{{ low }}}}"
"""


DOCK = (("Home", "mdi:home", "home"), ("Lights", "mdi:lightbulb-outline", "lights"),
        ("Climate", "mdi:snowflake", "climate"), ("Door", "mdi:lock", "door"), ("Media", "mdi:music", "media"))
# Pages built by Home Assistant itself (view strategies), themed by DonkeyHome: (path, title, icon, strategy).
DEVICE_PAGES = (("lights", "Lights", "mdi:lightbulb-outline", "light"),
                ("climate", "Climate", "mdi:snowflake", "climate"),
                ("door", "Door", "mdi:lock", "security"),
                ("media", "Music and TV", "mdi:music", "home-media-players"))


def room_path(a: dict, room: str) -> str:
    return "room-" + area_of(a, room).replace("_", "-")


def dock_items() -> str:
    """The dock's buttons as a JavaScript array for the dashboard template: [name, icon, page]."""
    return json.dumps([list(item) for item in DOCK])


def subviews_yaml(a: dict) -> str:
    views = [f"  - path: {room_path(a, r)}\n    title: {q(r)}\n    subview: true\n"
             f"    strategy:\n      type: home-area\n      area: {area_of(a, r)}" for r in a["rooms"]]
    views += [f"  - path: {path}\n    title: {title}\n    icon: {icon}\n    subview: true\n    strategy:\n      type: {kind}"
              for path, title, icon, kind in DEVICE_PAGES]
    return "\n".join(views)


def dashboard_yaml(a: dict) -> str:
    keys = [f"r{n}" for n in range(len(a["rooms"]))]
    pills = "\n".join(
        f"              {k}: {{card: {{type: custom:button-card, template: dh_room_pill, name: {q(r)}, "
        f"variables: {{area: {area_of(a, r)}, path: {room_path(a, r)}}}}}}}" for k, r in zip(keys, a["rooms"]))
    lights = "\n".join(
        f"          - type: custom:button-card\n            template: dh_room_lights\n"
        f"            variables: {{name: {q(r)}, area: {area_of(a, r)}, path: {room_path(a, r)}}}\n"
        f"            grid_options: {{columns: 6, rows: 1}}" for r in a["rooms"])
    routines = "\n".join(
        f"          - type: custom:button-card\n            template: dh_pill\n"
        f"            variables: {{icon: \"{icon}\", title: {q(label)}, subtitle: {q(sub)}}}\n"
        f"            tap_action:\n              action: perform-action\n              perform_action: script.turn_on\n"
        f"              target:\n                entity_id: script.{key}\n            grid_options: {{columns: 6, rows: 1}}"
        for key, label, icon, sub in ROUTINES)
    text = (TEMPLATES / "dashboard.yaml").read_text(encoding="utf-8")
    for key, value in {"@@MARKER@@": MARKER, "@@HOME@@": a["home_name"], "@@ROOM_LIST@@": ", ".join(a["rooms"]),
                       "@@PILL_AREAS@@": " ".join(keys), "@@ROOM_COUNT@@": str(len(keys)),
                       "@@ROOM_PILLS@@": pills, "@@ROOM_LIGHTS@@": lights, "@@ROUTINES@@": routines,
                       "@@DOCK_ITEMS@@": dock_items(), "@@SUBVIEWS@@": subviews_yaml(a)}.items():
        text = text.replace(key, value)
    return text


ROUTINES = (("routine_good_morning", "Good Morning", "mdi:weather-sunset-up", "Start the day"),
            ("routine_leaving_home", "Leaving Home", "mdi:exit-run", "Switch off and lock"),
            ("routine_arriving_home", "I'm Home", "mdi:home-import-outline", "Welcome back"),
            ("routine_good_night", "Good Night", "mdi:weather-night", "Lights off, doors locked"),
            ("routine_everything_off", "Everything Off", "mdi:power", "Lights, fans, aircon, TV"))


def look_yaml(a: dict) -> str:
    return f"""{MARKER}
# The DonkeyHome look for every screen of Home Assistant: dark by default, light with the sun/moon button.
# Applied at every start, so a restored backup comes back the way it was left. Change it any time; to stop
# using it, set your own theme in your profile and delete this file.

input_boolean:
  donkeyhome_light_mode:
    name: Light mode
    icon: mdi:theme-light-dark

script:
  donkeyhome_toggle_theme:
    alias: Switch light and dark
    icon: mdi:theme-light-dark
    mode: queued
    sequence:
      - action: input_boolean.toggle
        target:
          entity_id: input_boolean.donkeyhome_light_mode
      - action: script.donkeyhome_apply_theme

  donkeyhome_apply_theme:
    alias: Apply the DonkeyHome theme
    mode: queued
    sequence:
      - action: frontend.set_theme
        continue_on_error: true
        data:
          name: "{{{{ 'DonkeyHome Light' if is_state('input_boolean.donkeyhome_light_mode', 'on') else 'DonkeyHome' }}}}"
          name_dark: "{{{{ 'DonkeyHome Light' if is_state('input_boolean.donkeyhome_light_mode', 'on') else 'DonkeyHome' }}}}"

automation:
  - id: donkeyhome_theme_at_start
    alias: "DonkeyHome: theme at start"
    triggers:
      - trigger: homeassistant
        event: start
    actions:
      - action: script.donkeyhome_apply_theme
"""


def asset_files() -> dict[str, bytes]:
    return {p.relative_to(ASSETS).as_posix(): p.read_bytes() for p in sorted(ASSETS.rglob("*")) if p.is_file()}


def build(a: dict) -> dict[str, str | bytes]:
    """Every file to write, keyed by its path inside config/. Text for YAML, bytes for the theme/font/card assets."""
    files: dict[str, str | bytes] = {
        "configuration.yaml": configuration_yaml(a),
        "automations.yaml": "[]\n",
        "scripts.yaml": "{}\n",
        "scenes.yaml": "[]\n",
        "packages/house.yaml": house_yaml(a),
        "packages/routines.yaml": routines_yaml(a),
        "packages/presence.yaml": presence_yaml(a),
        "packages/look.yaml": look_yaml(a),
        "dashboards/home.yaml": dashboard_yaml(a),
        **asset_files(),
    }
    if a["battery_check"]:
        files["packages/maintenance.yaml"] = maintenance_yaml(a)
    return files


def plan(files: dict[str, str | bytes], out: Path) -> tuple[dict[str, str | bytes], list[str]]:
    """What write() would do: (files to write, files to delete). Never touches your own files:
    automations/scripts/scenes are only created when missing, and only DonkeyHome's files are deleted."""
    to_write = {rel: text for rel, text in files.items() if rel not in UI_FILES or not (out / rel).exists()}
    to_delete = [rel for rel in OPTIONAL_FILES if rel not in files and (out / rel).exists()
                 and (out / rel).read_text(encoding="utf-8").startswith(MARKER)]
    return to_write, to_delete


def write(files: dict[str, str | bytes], out: Path) -> tuple[list[str], list[str]]:
    """Write the files into out (a config folder). Returns (written, deleted) relative paths."""
    to_write, to_delete = plan(files, out)
    for rel, text in to_write.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
    for rel in to_delete:
        (out / rel).unlink()
    return list(to_write), to_delete


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Make a starter Home Assistant configuration for your home.")
    ap.add_argument("--answers", type=Path, help="use this answers file instead of asking")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the config folder")
    ap.add_argument("--yes", action="store_true", help="write without asking")
    args = ap.parse_args(argv)

    try:
        if args.answers:
            answers = validate(json.loads(args.answers.read_text(encoding="utf-8")))
        else:
            print("DonkeyHome wizard\n" + "=" * 17)
            print("Press Enter to keep the answer in [brackets]. Ctrl+C stops without changing anything.\n")
            saved = json.loads(DEFAULT_ANSWERS.read_text(encoding="utf-8")) if DEFAULT_ANSWERS.exists() else {}
            answers = ask_until_valid({**EXAMPLE, **saved})
            DEFAULT_ANSWERS.write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
            print(f"\nAnswers saved to {DEFAULT_ANSWERS.name}.")
        if args.out.exists() and not args.yes and not args.answers:
            if not ask_yes(f"Update the DonkeyHome files in {args.out}?", True):
                print("Nothing changed.")
                return 1
    except (AnswerError, json.JSONDecodeError, OSError) as err:
        print(f"Could not use the answers: {err}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nStopped. Nothing changed.")
        return 130

    write(build(answers), args.out)
    print(f"\nDone. Your configuration is in {args.out}")
    print("Next: create these areas in Home Assistant (Settings > Areas, labels and zones):")
    for room in answers["rooms"]:
        print(f"  - {room}")
    print("Then copy the folder's contents into Home Assistant: docs/advanced-command-line.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
