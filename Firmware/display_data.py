#!/usr/bin/env python3
import sys
import json
from datetime import datetime
from config import (STATION_NAME, BUS_LINE, BUS_STOP_NAME, METRO_LINES,
                    DISPLAY_MODE, DATA_FILE, EPD_LIB_PATH)
sys.path.append(EPD_LIB_PATH)
from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = '/usr/share/fonts/truetype/dejavu/'

# Sections per mode, top to bottom: (data key, rows shown).
# Row counts are sized to fit 480 px; see layout constants below.
LAYOUTS = {
    'train_bus': [('pendeltag', 6), ('buses', 5)],
    'train_bus_metro': [('pendeltag', 3), ('buses', 3), ('metro', 3)],
}

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
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
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


def draw_section(draw, fonts, y, title, rows, max_rows):
    """Draw a title bar and up to max_rows departures from y. Returns the next free y."""
    draw.rectangle((20, y, 780, y + BAR_H), fill=0)
    draw.text((400, y + BAR_H // 2), title, font=fonts['header'], fill=255, anchor="mm")
    y += BAR_H + BAR_GAP

    if not rows:
        draw.text((COL_DEST, y + ROW_H // 2), "No departures", font=fonts['normal'], fill=0, anchor="lm")
        y += ROW_H

    for row in rows[:max_rows]:
        mid = y + ROW_H // 2
        draw.text((COL_LINE, mid), str(row.get('line', '?')), font=fonts['normal'], fill=0, anchor="lm")
        draw.text((COL_DEST, mid), row.get('destination', 'Unknown')[:30], font=fonts['normal'], fill=0, anchor="lm")
        draw.text((COL_TIME, mid), format_time(row.get('time', '')), font=fonts['normal'], fill=0, anchor="lm")
        y += ROW_H

    return y + SECTION_GAP


def main():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        print("No data file found")
        return

    update_time = data.get('update_time', datetime.now().isoformat())
    try:
        update_time_str = datetime.fromisoformat(update_time).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        update_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    epd = epd7in5_V2.EPD()
    epd.init()

    fonts = load_fonts()
    image = Image.new('1', (800, 480), 255)
    draw = ImageDraw.Draw(image)

    # Header
    draw.rectangle((0, 0, 799, 55), fill=0)
    draw.text((400, 28), f"{STATION_NAME} - DEPARTURES", font=fonts['title'], fill=255, anchor="mm")
    draw.text((20, 70), "Showing departures in 5+ minutes", font=fonts['normal'], fill=0, anchor="lm")
    draw.text((780, 70), f"Updated: {update_time_str}", font=fonts['normal'], fill=0, anchor="rm")

    # Column headings, shared by all sections
    draw.text((COL_LINE, 92), "Line", font=fonts['bold'], fill=0, anchor="lm")
    draw.text((COL_DEST, 92), "Destination", font=fonts['bold'], fill=0, anchor="lm")
    draw.text((COL_TIME, 92), "Time", font=fonts['bold'], fill=0, anchor="lm")
    draw.line((40, 104, 760, 104), fill=0, width=1)

    y = SECTIONS_TOP
    for key, max_rows in LAYOUTS[DISPLAY_MODE]:
        y = draw_section(draw, fonts, y, section_title(key), data.get(key, []), max_rows)

    epd.display(epd.getbuffer(image))
    epd.sleep()
    print(f"Display updated at {update_time_str}")


if __name__ == "__main__":
    main()
