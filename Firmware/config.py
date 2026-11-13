#!/usr/bin/env python3
"""Load settings from the .env file next to this script.

Values set in the real environment take precedence over the file.
"""
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_env_file(path):
    values = {}
    if not path.exists():
        return values
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    return values


_file_values = _load_env_file(ENV_PATH)


def get(key, default=None, required=False):
    value = os.environ.get(key, _file_values.get(key, default))
    if required and value in (None, ""):
        raise SystemExit(f"Missing required setting '{key}' (check {ENV_PATH})")
    return value


PENDELTAG_SITE_ID = get("PENDELTAG_SITE_ID", required=True)
BUS_STOP_ID = get("BUS_STOP_ID", required=True)
BUS_LINE = get("BUS_LINE", required=True)
METRO_SITE_ID = get("METRO_SITE_ID", "")  # empty: no metro sections or screen
METRO_LINES = [l.strip() for l in get("METRO_LINES", "").split(",") if l.strip()]

# Buttons (BCM numbers), wired to GND; internal pull-ups are used.
BUTTON_NEXT_PIN = int(get("BUTTON_NEXT_PIN", "26"))
BUTTON_PREV_PIN = int(get("BUTTON_PREV_PIN", "19"))
REFRESH_SECONDS = int(get("REFRESH_SECONDS", "60"))

STATION_NAME = get("STATION_NAME", "Station")
BUS_STOP_NAME = get("BUS_STOP_NAME", "")

DATA_FILE = get("DATA_FILE", "/tmp/transport_data.json")
EPD_LIB_PATH = get("EPD_LIB_PATH", "/home/displegory/e-Paper/RaspberryPi_JetsonNano/python/lib")
