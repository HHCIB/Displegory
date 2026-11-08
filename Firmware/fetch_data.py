#!/usr/bin/env python3
import json
from datetime import datetime, timedelta

import requests

from config import (PENDELTAG_SITE_ID, BUS_STOP_ID, BUS_LINE, METRO_SITE_ID,
                    METRO_LINES, SHOW_METRO, DATA_FILE)

API_URL = "https://transport.integration.sl.se/v1/sites/{}/departures"
MIN_MINUTES = 5

_responses = {}


def get_departures(site_id):
    """All departures for a site. Each site is requested once per run."""
    if site_id not in _responses:
        try:
            response = requests.get(API_URL.format(site_id), timeout=10)
            _responses[site_id] = response.json().get('departures', [])
        except Exception as e:
            print(f"Error fetching site {site_id}: {e}")
            _responses[site_id] = []
    return _responses[site_id]


def select(site_id, matches, limit):
    """Departures at site_id whose line matches, at least MIN_MINUTES away."""
    cutoff = datetime.now() + timedelta(minutes=MIN_MINUTES)
    selected = []
    for dep in get_departures(site_id):
        line = dep.get('line', {})
        if not matches(line):
            continue
        time_str = dep.get('expected', dep.get('scheduled', ''))
        if not time_str:
            continue
        try:
            if datetime.fromisoformat(time_str.replace('Z', '+00:00')) < cutoff:
                continue
        except Exception:
            pass  # unparseable time: keep the departure
        selected.append({
            'line': line.get('designation', '?'),
            'destination': dep.get('destination', 'Unknown'),
            'time': time_str,
            'state': dep.get('state', ''),
        })
    return selected[:limit]


def is_train(line):
    return line.get('transport_mode') == 'TRAIN'


def is_bus(line):
    return line.get('designation') == BUS_LINE


def is_metro(line):
    if line.get('transport_mode') != 'METRO':
        return False
    return not METRO_LINES or line.get('designation') in METRO_LINES


data = {
    'update_time': datetime.now().isoformat(),
    'pendeltag': select(PENDELTAG_SITE_ID, is_train, 8),
    'buses': select(BUS_STOP_ID, is_bus, 5),
    'metro': select(METRO_SITE_ID, is_metro, 8) if SHOW_METRO else [],
}

with open(DATA_FILE, 'w') as f:
    json.dump(data, f)

summary = f"{len(data['pendeltag'])} trains, {len(data['buses'])} buses"
if SHOW_METRO:
    summary += f", {len(data['metro'])} metro"
print(f"Data saved: {summary}")
