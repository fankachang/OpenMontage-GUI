#!/usr/bin/env python3
"""Local web server and SQLite settings store for OpenMontage GUI."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = Path.home() / "Library" / "Application Support" / "OpenMontage-GUI"
DATA_DIR = Path(os.environ.get("OPENMONTAGE_GUI_DATA_DIR", DEFAULT_DATA_DIR)).expanduser()
DATABASE = DATA_DIR / "settings.sqlite3"
HOST = "127.0.0.1"
PORT = int(os.environ.get("OPENMONTAGE_GUI_PORT", "4760"))

DEFAULT_SETTINGS = {
    "language": "zh",
    "local_only": True,
    "blender_path": "/Applications/Blender.app/Contents/MacOS/Blender",
    "interfaces": [],
    "settings_tab": "general",
}
ALLOWED_KEYS = set(DEFAULT_SETTINGS)
ALLOWED_ROLES = {"text", "vision", "stt", "embedding", "image", "video", "audio"}
ALLOWED_TYPES = {"openai", "comfyui", "other"}


def connect_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE, timeout=10)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value_json TEXT NOT NULL)"
    )
    return connection


@contextmanager
def database():
    connection = connect_db()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def read_settings() -> tuple[dict, bool]:
    with database() as connection:
        rows = connection.execute("SELECT key, value_json FROM settings").fetchall()
    settings = dict(DEFAULT_SETTINGS)
    settings.update({key: json.loads(value) for key, value in rows if key in ALLOWED_KEYS})
    return settings, bool(rows)


def validate_settings(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Settings must be an object")
    unknown = set(payload) - ALLOWED_KEYS
    if unknown:
        raise ValueError("Unsupported settings field")
    settings = dict(DEFAULT_SETTINGS)
    settings.update(payload)
    if settings["language"] not in {"zh", "en"}:
        raise ValueError("Invalid language")
    if not isinstance(settings["local_only"], bool):
        raise ValueError("local_only must be a boolean")
    if not isinstance(settings["settings_tab"], str) or settings["settings_tab"] not in {
        "general", "models", "tools", "project"
    }:
        raise ValueError("Invalid settings tab")
    for field in ("blender_path",):
        value = settings[field]
        if not isinstance(value, str) or len(value) > 2048:
            raise ValueError("Invalid path value")
    interfaces = settings["interfaces"]
    if not isinstance(interfaces, list) or len(interfaces) > 100:
        raise ValueError("Invalid interface list")
    clean_interfaces = []
    for entry in interfaces:
        if not isinstance(entry, dict):
            raise ValueError("Invalid interface entry")
        if set(entry) - {"name", "type", "url", "model", "roles"}:
            raise ValueError("Unsupported interface field")
        name, kind, url, model, roles = (
            entry.get("name", ""), entry.get("type", "other"), entry.get("url", ""),
            entry.get("model", ""), entry.get("roles", []),
        )
        if not all(isinstance(value, str) for value in (name, kind, url, model)):
            raise ValueError("Invalid interface values")
        if kind not in ALLOWED_TYPES or len(name) > 200 or len(url) > 2048 or len(model) > 300:
            raise ValueError("Invalid interface values")
        if not isinstance(roles, list) or any(role not in ALLOWED_ROLES for role in roles):
            raise ValueError("Invalid interface roles")
        clean_interfaces.append({"name": name, "type": kind, "url": url, "model": model, "roles": roles})
    settings["interfaces"] = clean_interfaces
    return settings


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/api/settings":
            settings, initialized = read_settings()
            return self.send_json(200, {"settings": settings, "initialized": initialized})
        return super().do_GET()

    def do_PUT(self):
        if urlparse(self.path).path != "/api/settings":
            return self.send_json(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 256_000:
                raise ValueError("Invalid request size")
            body = json.loads(self.rfile.read(length))
            settings = validate_settings(body)
            with database() as connection:
                connection.executemany(
                    "INSERT INTO settings(key, value_json) VALUES(?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json",
                    [(key, json.dumps(value, ensure_ascii=False)) for key, value in settings.items()],
                )
            return self.send_json(200, {"settings": settings, "initialized": True})
        except (ValueError, json.JSONDecodeError, sqlite3.Error) as error:
            return self.send_json(400, {"error": str(error)})

    def send_json(self, status: int, value: dict):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args):
        # Do not log request bodies or settings values.
        super().log_message(fmt, *args)


if __name__ == "__main__":
    with database():
        pass
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"OpenMontage GUI: http://{HOST}:{PORT}/")
    print(f"Settings database: {DATABASE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nOpenMontage GUI stopped.")
    finally:
        server.server_close()
