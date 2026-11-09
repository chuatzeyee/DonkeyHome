#!/usr/bin/env python3
"""DonkeyHome app: the point-and-click wizard, served inside Home Assistant (ingress).

GET  /                 the wizard page (web/)
GET  api/discover      what Home Assistant already has: rooms, people, phones, device counts
POST api/preview       the files the answers would make (for the "show me the details" link)
POST api/apply         create rooms, back up, write files, check; restore on failure, else restart
GET  api/ping          is Home Assistant up again after the restart?

Standard library only. Responses are {"ok": bool, "data": ..., "error": str|null}.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import haclient
import wizard
from haclient import HAError, WebSocket, rest

CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", "/homeassistant"))
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
PORT = int(os.environ.get("PORT", "8099"))
ALLOWED_CLIENT = os.environ.get("ALLOWED_CLIENT", "172.30.32.2")  # the Supervisor's ingress proxy; "*" in tests
WEB = Path(__file__).resolve().parent / "web"
STATIC = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css"), "/donkey.svg": ("donkey.svg", "image/svg+xml")}
MAX_BODY = 64 * 1024
DEVICE_DOMAINS = ("light", "fan", "climate", "media_player", "lock", "cover", "vacuum")
# Lines of Home Assistant's own starting configuration.yaml (comments and blank lines ignored).
DEFAULT_CONFIG_LINES = {"default_config:", "frontend:", "themes: !include_dir_merge_named themes",
                        "automation: !include automations.yaml", "script: !include scripts.yaml",
                        "scene: !include scenes.yaml"}

log = logging.getLogger("donkeyhome")
apply_lock = threading.Lock()


# ---------------------------------------------------------------- what is there already
def config_status() -> str:
    """'missing', 'fresh' (Home Assistant's default), 'donkeyhome' (made by us) or 'custom' (someone edited it)."""
    path = CONFIG_DIR / "configuration.yaml"
    if not path.exists():
        return "missing"
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith(wizard.MARKER):
        return "donkeyhome"
    lines = {ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")}
    return "fresh" if lines <= DEFAULT_CONFIG_LINES else "custom"


def phone_label(service: str) -> str:
    return service.removeprefix("mobile_app_").replace("_", " ").title()


def discover() -> dict[str, Any]:
    warnings: list[str] = []
    cfg = rest("GET", "/api/config")
    states = rest("GET", "/api/states")
    services = rest("GET", "/api/services")
    notify = next((d["services"] for d in services if d["domain"] == "notify"), {})
    try:
        with WebSocket() as ws:
            areas = [{"id": a["area_id"], "name": a["name"]} for a in ws.call("config/area_registry/list")]
    except HAError as err:
        warnings.append(f"Could not read your rooms: {err}")
        areas = []
    saved_path = DATA_DIR / "answers.json"
    return {
        "home_name": cfg.get("location_name") or "Home",
        "version": cfg.get("version"),
        "areas": sorted(areas, key=lambda a: a["name"].casefold()),
        "people": sorted(({"name": s["attributes"].get("friendly_name", s["entity_id"]),
                           "tracked": bool(s["attributes"].get("device_trackers")), "state": s["state"]}
                          for s in states if s["entity_id"].startswith("person.")), key=lambda p: p["name"]),
        "phones": [{"service": name, "label": phone_label(name)}
                   for name in sorted(notify) if name.startswith("mobile_app_")],
        "counts": {d: sum(1 for s in states if s["entity_id"].startswith(d + ".")) for d in DEVICE_DOMAINS},
        "config_status": config_status(),
        "saved": json.loads(saved_path.read_text(encoding="utf-8")) if saved_path.exists() else None,
        "choices": [{"key": k, "question": q, "default": d} for k, q, d in wizard.CHOICES],
        "warnings": warnings,
    }


# ---------------------------------------------------------------- doing it
def ensure_areas(rooms: list[str], steps: list[str]) -> dict[str, str]:
    """Return {room name: area_id}, creating the rooms Home Assistant doesn't have yet."""
    with WebSocket() as ws:
        existing = {a["name"].casefold(): a["area_id"] for a in ws.call("config/area_registry/list")}
        ids = {}
        for room in rooms:
            if room.casefold() in existing:
                ids[room] = existing[room.casefold()]
            else:
                ids[room] = ws.call("config/area_registry/create", name=room)["area_id"]
                steps.append(f"Created the room {room}")
    return ids


def backup(paths: list[str]) -> tuple[Path, list[str]]:
    """Copy the files we are about to change into donkeyhome_backups/<time>/. Returns (folder, new files)."""
    folder = CONFIG_DIR / "donkeyhome_backups" / time.strftime("%Y-%m-%d_%H-%M-%S")
    new = []
    for rel in paths:
        src = CONFIG_DIR / rel
        if src.exists():
            dst = folder / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            new.append(rel)
    folder.mkdir(parents=True, exist_ok=True)
    return folder, new


def restore(folder: Path, new: list[str]) -> None:
    for src in folder.rglob("*"):
        if src.is_file():
            shutil.copy2(src, CONFIG_DIR / src.relative_to(folder))
    for rel in new:
        (CONFIG_DIR / rel).unlink(missing_ok=True)


def apply(raw: dict) -> dict[str, Any]:
    answers = wizard.validate(raw)
    steps: list[str] = []
    answers = wizard.validate({**answers, "area_ids": ensure_areas(answers["rooms"], steps)})
    files = wizard.build(answers)
    to_write, to_delete = wizard.plan(files, CONFIG_DIR)
    folder, new = backup(list(to_write) + to_delete)
    steps.append(f"Saved a backup of your old files in {folder.relative_to(CONFIG_DIR)}")
    try:
        wizard.write(files, CONFIG_DIR)
        check = rest("POST", "/api/config/core/check_config", timeout=120)
    except Exception:
        restore(folder, new)  # half-written (disk full, Home Assistant gone): put the old files back first
        raise
    steps.append(f"Wrote {len(to_write)} files" + (f", removed {len(to_delete)}" if to_delete else ""))
    if check.get("result") != "valid":
        restore(folder, new)
        log.error("Check failed, files restored: %s", check.get("errors"))
        raise HAError("Home Assistant found a problem, so nothing was changed (your old files are back). "
                      f"Details: {check.get('errors')}")
    steps.append("Home Assistant checked the new setup: all good")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "answers.json").write_text(json.dumps(answers, indent=2), encoding="utf-8")
    try:
        rest("POST", "/api/services/homeassistant/restart", {}, timeout=10)
    except HAError:
        pass  # the restart often cuts the connection before it answers; that's expected
    steps.append("Restarting Home Assistant")
    return {"steps": steps, "backup": str(folder.relative_to(CONFIG_DIR))}


def ping() -> dict[str, bool]:
    try:
        rest("GET", "/api/", timeout=5)
        return {"core": True}
    except HAError:
        return {"core": False}


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "DonkeyHome"

    def _allowed(self) -> bool:
        if ALLOWED_CLIENT == "*" or self.client_address[0] == ALLOWED_CLIENT:
            return True
        self.send_error(403)
        return False

    def _json(self, status: int, data: Any = None, error: str | None = None) -> None:
        body = json.dumps({"ok": error is None, "data": data, "error": error}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _run(self, fn: Any, *args: Any) -> None:
        try:
            self._json(200, fn(*args))
        except wizard.AnswerError as err:
            self._json(400, error=str(err))
        except HAError as err:
            log.warning("%s", err)
            self._json(502, error=str(err))
        except Exception:  # noqa: BLE001 - last resort: log it, tell the user something useful
            log.exception("Unexpected error")
            self._json(500, error="Something unexpected went wrong. The app's Log tab has the details.")

    def do_GET(self) -> None:  # noqa: N802 - http.server naming
        if not self._allowed():
            return
        path = self.path.split("?", 1)[0]
        if path in STATIC:
            name, ctype = STATIC[path]
            body = (WEB / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/discover":
            self._run(discover)
        elif path == "/api/ping":
            self._run(ping)
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if not self._allowed():
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            self._json(413, error="Request too large.")
            return
        try:
            raw = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(raw, dict):
                raise ValueError
        except ValueError:
            self._json(400, error="The request was not valid JSON.")
            return
        path = self.path.split("?", 1)[0]
        if path == "/api/preview":
            self._run(lambda: wizard.build(wizard.validate(raw)))
        elif path == "/api/apply":
            if not apply_lock.acquire(blocking=False):
                self._json(409, error="Already setting up. Please wait.")
                return
            try:
                self._run(apply, raw)
            finally:
                apply_lock.release()
        else:
            self.send_error(404)

    def log_message(self, fmt: str, *args: Any) -> None:
        log.debug(fmt, *args)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info("DonkeyHome on port %s, config folder %s, Home Assistant at %s", PORT, CONFIG_DIR, haclient.CORE_URL)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
