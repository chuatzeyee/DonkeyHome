"""Talks to Home Assistant from inside the app: REST through the Supervisor proxy, plus a tiny WebSocket client.

Standard library only. Inside the app the defaults use the Supervisor proxy and SUPERVISOR_TOKEN; tests point
CORE_URL / CORE_WS / HA_TOKEN at a throwaway Home Assistant instead.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

CORE_URL = os.environ.get("CORE_URL", "http://supervisor/core")  # + /api/...
CORE_WS = os.environ.get("CORE_WS", "ws://supervisor/core/websocket")
TIMEOUT = 30


class HAError(RuntimeError):
    """Home Assistant could not be reached or refused a request."""


def token() -> str:
    value = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HA_TOKEN")
    if not value:
        raise HAError("No access token. Make sure 'homeassistant_api: true' is in the app's config.yaml.")
    return value


def rest(method: str, path: str, data: Any = None, timeout: float = TIMEOUT) -> Any:
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(CORE_URL + path, data=body, method=method, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as err:
        raise HAError(f"{method} {path} failed: {err.code} {err.read()[:300].decode(errors='replace')}") from None
    except (urllib.error.URLError, OSError) as err:
        raise HAError(f"Could not reach Home Assistant ({err}).") from None
    return json.loads(raw) if raw else None


class WebSocket:
    """Just enough of RFC 6455 for Home Assistant's WebSocket API: text frames, client masking, no extensions."""

    def __init__(self, url: str = CORE_WS, timeout: float = TIMEOUT):
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "ws":
            raise HAError(f"Only ws:// addresses are supported, not {url}")
        self.sock = socket.create_connection((parts.hostname, parts.port or 80), timeout=timeout)
        self.buf = b""
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {parts.path or '/'} HTTP/1.1\r\nHost: {parts.netloc}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = self._until(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise HAError("Home Assistant refused the WebSocket connection: " + head[:200].decode(errors="replace"))
        self.next_id = 1
        if self.recv().get("type") != "auth_required":
            raise HAError("Unexpected WebSocket greeting.")
        self.send({"type": "auth", "access_token": token()})
        if self.recv().get("type") != "auth_ok":
            raise HAError("Home Assistant refused the app's access token.")

    def __enter__(self) -> "WebSocket":
        return self

    def __exit__(self, *exc: object) -> None:
        self.sock.close()

    def _until(self, marker: bytes) -> bytes:
        while marker not in self.buf:
            self._fill()
        head, self.buf = self.buf.split(marker, 1)
        return head

    def _fill(self) -> None:
        chunk = self.sock.recv(65536)
        if not chunk:
            raise HAError("Home Assistant closed the connection.")
        self.buf += chunk

    def _take(self, n: int) -> bytes:
        while len(self.buf) < n:
            self._fill()
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, msg: dict) -> None:
        data = json.dumps(msg).encode()
        n = len(data)
        head = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else
                                struct.pack("!BH", 0x80 | 126, n) if n < 65536 else struct.pack("!BQ", 0x80 | 127, n))
        mask = os.urandom(4)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self) -> dict:
        payload = b""
        while True:
            b1, b2 = self._take(2)
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._take(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._take(8))[0]
            mask = self._take(4) if b2 & 0x80 else b""
            data = self._take(n)
            if mask:
                data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
            opcode = b1 & 0x0F
            if opcode == 0x8:
                raise HAError("Home Assistant closed the connection.")
            if opcode in (0x9, 0xA):  # ping/pong: Home Assistant doesn't need an answer from us for short calls
                continue
            payload += data
            if b1 & 0x80:
                return json.loads(payload)

    def call(self, msg_type: str, **fields: Any) -> Any:
        msg_id, self.next_id = self.next_id, self.next_id + 1
        self.send({"id": msg_id, "type": msg_type, **fields})
        while True:
            reply = self.recv()
            if reply.get("id") == msg_id and reply.get("type") == "result":
                if not reply.get("success"):
                    raise HAError(f"{msg_type} failed: {reply.get('error', {}).get('message', reply)}")
                return reply.get("result")
