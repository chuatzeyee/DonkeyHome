#!/usr/bin/env python3
"""Home Assistant starter wizard.

Asks a few plain questions about your home and writes a ready-to-copy Home Assistant
configuration folder (config/). Only uses Python's standard library.

  python3 wizard/wizard.py                               ask the questions, write config/
  python3 wizard/wizard.py --answers my-answers.json     no questions, use a saved answers file
  python3 wizard/wizard.py --out somewhere/else          write the files somewhere else

Your answers are saved to my-answers.json so you can run the wizard again later and only
change what you need.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 9):
    sys.exit("Python 3.9 or newer is needed. Get it from https://www.python.org/downloads/")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "config"
DEFAULT_ANSWERS = ROOT / "my-answers.json"

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '&-]{0,39}$")
NOTIFY_RE = re.compile(r"^[a-z0-9_]+$")

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
        print("docs/02-setting-up.md, step 7, shows how to find these names.")
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


def configuration_yaml(a: dict) -> str:
    return f"""# Home Assistant configuration made by the starter wizard for {a['home_name']}.
# Most of the logic lives in packages/ (one file per subject). This file just switches things on.
# After you edit any YAML file: Settings > Tools > YAML > Check configuration, then Restart.

# The standard Home Assistant features (history, logbook, phone app, sun, zones, backups and more).
default_config:

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
    return f"""# House mode, the automatic leave/arrive switch and the "notify everyone" helper.

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
    # Off until your phones are set up (docs/02-setting-up.md, step 8).
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
    arrival = f"area_id: {slug(a['arrival_room'])}"
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
    return ("# The one-tap routines. Each device step has continue_on_error, so one offline device never\n"
            "# stops a routine. 'entity_id: all' means every device of that kind, so new devices are\n"
            "# included automatically. To change a routine, edit this file or run the wizard again.\n\n"
            "script:\n" + "\n\n".join(scripts) + "\n")


def presence_yaml(a: dict) -> str:
    return f"""# Runs Leaving Home when the last person leaves and I'm Home when the first person arrives.
# Only works when the "Automatic leave and arrive" switch is on (docs/02-setting-up.md, step 8).
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
    return f"""# Weekly check-up: Sunday 10:00, lists every battery under 20 %.

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


def dashboard_yaml(a: dict) -> str:
    buttons = "\n".join(
        f"          - type: button\n            entity: script.{key}\n            show_state: false\n"
        "            tap_action:\n              action: toggle"
        for key in ("routine_good_morning", "routine_leaving_home", "routine_arriving_home",
                    "routine_good_night", "routine_everything_off"))
    rooms = "\n".join(f"          - type: area\n            area: {slug(r)}" for r in a["rooms"])
    return f"""# The {a['home_name']} dashboard. Room cards need the areas to exist with exactly these names:
# {', '.join(a['rooms'])} (Settings > Areas, labels and zones).

title: {q(a['home_name'])}
views:
  - title: Home
    path: home
    icon: mdi:home
    type: sections
    max_columns: 4
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Routines
{buttons}
      - type: grid
        cards:
          - type: heading
            heading: House
          - type: tile
            entity: input_select.house_mode
          - type: tile
            entity: input_boolean.auto_presence
      - type: grid
        cards:
          - type: heading
            heading: Rooms
{rooms}
"""


def build(a: dict) -> dict[str, str]:
    """Every file to write, keyed by its path inside config/."""
    files = {
        "configuration.yaml": configuration_yaml(a),
        "automations.yaml": "[]\n",
        "scripts.yaml": "{}\n",
        "scenes.yaml": "[]\n",
        "packages/house.yaml": house_yaml(a),
        "packages/routines.yaml": routines_yaml(a),
        "packages/presence.yaml": presence_yaml(a),
        "dashboards/home.yaml": dashboard_yaml(a),
    }
    if a["battery_check"]:
        files["packages/maintenance.yaml"] = maintenance_yaml(a)
    return files


def write(files: dict[str, str], out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)  # ponytail: the folder is fully generated; keep your own edits in a copy
    for rel, text in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Make a starter Home Assistant configuration for your home.")
    ap.add_argument("--answers", type=Path, help="use this answers file instead of asking")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the config folder")
    ap.add_argument("--yes", action="store_true", help="overwrite the output folder without asking")
    args = ap.parse_args(argv)

    try:
        if args.answers:
            answers = validate(json.loads(args.answers.read_text(encoding="utf-8")))
        else:
            print("Home Assistant starter wizard\n" + "=" * 29)
            print("Press Enter to keep the answer in [brackets]. Ctrl+C stops without changing anything.\n")
            saved = json.loads(DEFAULT_ANSWERS.read_text(encoding="utf-8")) if DEFAULT_ANSWERS.exists() else {}
            answers = ask_until_valid({**EXAMPLE, **saved})
            DEFAULT_ANSWERS.write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
            print(f"\nAnswers saved to {DEFAULT_ANSWERS.name}.")
        if args.out.exists() and not args.yes and not args.answers:
            if not ask_yes(f"Replace everything in {args.out}?", True):
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
    print("Then copy the folder in: docs/02-setting-up.md, step 4.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
