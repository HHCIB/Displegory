#!/usr/bin/env python3
"""Render departures to the e-Paper panel.

Run directly to show DATA_FILE once: python3 display_data.py [screen number]
"""
import sys
import json
from datetime import datetime
from config import (STATION_NAME, BUS_LINE, BUS_STOP_NAME, METRO_SITE_ID, METRO_LINES,
                    DATA_FILE, EPD_LIB_PATH)
sys.path.append(EPD_LIB_PATH)
from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = '/usr/share/fonts/truetype/dejavu/'
WIDTH, HEIGHT = 800, 480

# Screens in button order. Each: sections top to bottom as (data key, rows shown).
# Row counts fit 480 px: SECTIONS_TOP + per section (BAR_H + BAR_GAP + SECTION_GAP + rows * ROW_H).
if METRO_SITE_ID:
    SCREENS = [
        [('pendeltag', 3), ('buses', 3), ('metro', 3)],
        [('metro', 13)],
        [('buses', 13)],
        [('pendeltag', 13)],
    ]
else:  # no metro configured
    SCREENS = [
        [('pendeltag', 5), ('buses', 5)],
        [('buses', 13)],
        [('pendeltag', 13)],
    ]

# Layout (px)
COL_LINE, COL_DEST, COL_TIME = 40, 140, 680
SECTIONS_TOP = 112
BAR_H = 28
BAR_GAP = 4
ROW_H = 25
SECTION_GAP = 8


def section_title(key):
    if key == 'pendeltag':
        return "Pendeltåg"
    if key == 'buses':
        return f"BUS {BUS_LINE} - {BUS_STOP_NAME}" if BUS_STOP_NAME else f"BUS {BUS_LINE}"
    if key == 'metro':
        return "Tunnelbana " + "/".join(METRO_LINES) if METRO_LINES else "Tunnelbana"
    return key


def format_time(time_str):
    if not time_str:
        return '??:??'
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00')).strftime('%H:%M')
    except Exception:
        return '??:??'


def load_fonts():
    try:
        return {
            'title': ImageFont.truetype(FONT_DIR + 'DejaVuSans.ttf', 28),
            'header': ImageFont.truetype(FONT_DIR + 'DejaVuSans.ttf', 20),
            'normal': ImageFont.truetype(FONT_DIR + 'DejaVuSans.ttf', 18),
            'bold': ImageFont.truetype(FONT_DIR + 'DejaVuSans-Bold.ttf', 18),
        }
    except Exception:
        default = ImageFont.load_default()
        return {'title': default, 'header': default, 'normal': default, 'bold': default}


FONTS = load_fonts()


def draw_section(draw, y, title, rows, max_rows):
    """Draw a title bar and up to max_rows departures from y. Returns the next free y."""
    draw.rectangle((20, y, 780, y + BAR_H), fill=0)
    draw.text((400, y + BAR_H // 2), title, font=FONTS['header'], fill=255, anchor="mm")
    y += BAR_H + BAR_GAP

    if not rows:
        draw.text((COL_DEST, y + ROW_H // 2), "No departures", font=FONTS['normal'], fill=0, anchor="lm")
        y += ROW_H

    for row in rows[:max_rows]:
        mid = y + ROW_H // 2
        draw.text((COL_LINE, mid), str(row.get('line', '?')), font=FONTS['normal'], fill=0, anchor="lm")
        draw.text((COL_DEST, mid), row.get('destination', 'Unknown')[:30], font=FONTS['normal'], fill=0, anchor="lm")
        draw.text((COL_TIME, mid), format_time(row.get('time', '')), font=FONTS['normal'], fill=0, anchor="lm")
        y += ROW_H

    return y + SECTION_GAP


def render(data, screen):
    """Build the image for screen index `screen` (0-based) from fetched data."""
    try:
        updated = datetime.fromisoformat(data.get('update_time', '')).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        updated = '?'

    image = Image.new('1', (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.rectangle((0, 0, WIDTH - 1, 55), fill=0)
    draw.text((400, 28), f"{STATION_NAME} - DEPARTURES", font=FONTS['title'], fill=255, anchor="mm")
    draw.text((20, 70), f"{screen + 1}/{len(SCREENS)}   Departures in 5+ min", font=FONTS['normal'], fill=0, anchor="lm")
    draw.text((780, 70), f"Updated: {updated}", font=FONTS['normal'], fill=0, anchor="rm")

    # Column headings, shared by all sections
    draw.text((COL_LINE, 92), "Line", font=FONTS['bold'], fill=0, anchor="lm")
    draw.text((COL_DEST, 92), "Destination", font=FONTS['bold'], fill=0, anchor="lm")
    draw.text((COL_TIME, 92), "Time", font=FONTS['bold'], fill=0, anchor="lm")
    draw.line((40, 104, 760, 104), fill=0, width=1)

    y = SECTIONS_TOP
    for key, max_rows in SCREENS[screen]:
        y = draw_section(draw, y, section_title(key), data.get(key, []), max_rows)
    return image


def show(image):
    """Full refresh of the panel, then deep sleep (image is retained without power)."""
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.display(epd.getbuffer(image))
    epd.sleep()


if __name__ == "__main__":
    screen = int(sys.argv[1]) - 1 if len(sys.argv) > 1 else 0
    if not 0 <= screen < len(SCREENS):
        raise SystemExit(f"Screen must be 1-{len(SCREENS)}")
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        raise SystemExit(f"No data file found at {DATA_FILE}; run fetch_data.py first")
    show(render(data, screen))
    print(f"Display updated: screen {screen + 1}")
