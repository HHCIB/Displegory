#!/usr/bin/env python3
"""Fetch SL departures. Run directly to fetch once and write DATA_FILE."""
import json
from datetime import datetime, timedelta

import requests

from config import (PENDELTAG_SITE_ID, BUS_STOP_ID, BUS_LINE, METRO_SITE_ID,
                    METRO_LINES, DATA_FILE)

API_URL = "https://transport.integration.sl.se/v1/sites/{}/departures"
MIN_MINUTES = 5
MAX_DEPARTURES = 13  # most rows any screen shows


def get_departures(site_id, responses):
    """All departures for a site. Each site is requested once per fetch()."""
    if site_id not in responses:
        try:
            response = requests.get(API_URL.format(site_id), timeout=10)
            responses[site_id] = response.json().get('departures', [])
        except Exception as e:
            print(f"Error fetching site {site_id}: {e}")
            responses[site_id] = []
    return responses[site_id]


def select(departures, matches):
    """Departures whose line matches, at least MIN_MINUTES away."""
    cutoff = datetime.now() + timedelta(minutes=MIN_MINUTES)
    selected = []
    for dep in departures:
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
    return selected[:MAX_DEPARTURES]


def is_train(line):
    return line.get('transport_mode') == 'TRAIN'


def is_bus(line):
    return line.get('designation') == BUS_LINE


def is_metro(line):
    if line.get('transport_mode') != 'METRO':
        return False
    return not METRO_LINES or line.get('designation') in METRO_LINES


def fetch():
    responses = {}
    return {
        'update_time': datetime.now().isoformat(),
        'pendeltag': select(get_departures(PENDELTAG_SITE_ID, responses), is_train),
        'buses': select(get_departures(BUS_STOP_ID, responses), is_bus),
        'metro': select(get_departures(METRO_SITE_ID, responses), is_metro),
    }


def save(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def summary(data):
    return (f"{len(data['pendeltag'])} trains, {len(data['buses'])} buses, "
            f"{len(data['metro'])} metro")


if __name__ == "__main__":
    data = fetch()
    save(data)
    print(f"Data saved: {summary(data)}")
