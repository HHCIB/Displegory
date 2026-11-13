# Displegory firmware

Python program that fetches live SL departures (commuter rail, one bus line, metro) and shows them on a Waveshare 7.5" e-Paper V2 display (800x480, black/white) driven by a Raspberry Pi. Two buttons switch between four screens.

Device setup and configuration: [setup/README.md](setup/README.md).

## Files

| File | Purpose |
|---|---|
| `main.py` | Long-running loop: fetches on a timer, redraws on button press. |
| `fetch_data.py` | Queries the SL Transport API and filters departures. |
| `display_data.py` | Renders a screen and pushes it to the display. |
| `config.py` | Loads settings from `.env`. |
| `run.sh` | Starts `main.py` (used by the systemd service). |
| `.env.example` | Settings template. Copy to `.env`. |
| `.env` | Local settings (station IDs, names, paths). Not committed. |

All files must be in the same directory: `config.py` reads `.env` from its own directory, and `run.sh` starts `main.py` from its own directory.

## Screens

| # | Sections (rows shown) |
|---|---|
| 1 | Pendeltåg (3), bus (3), metro (3) |
| 2 | Metro (13) |
| 3 | Bus (13) |
| 4 | Pendeltåg (13) |

Button 1 (GPIO26) moves to the next screen, button 2 (GPIO19) to the previous one; both wrap around. The current screen number is shown under the header. Starts on screen 1.

## main.py

- Fetches every `REFRESH_SECONDS` (default 60), waits 5 s (lets the Wi-Fi radio go idle), then redraws the current screen.
- A button press redraws immediately from the last fetched data; no API call.
- A full panel refresh takes a few seconds. Presses during a refresh are collapsed; the final screen is drawn once the refresh finishes.
- Buttons: `gpiozero.Button`, internal pull-up, 50 ms debounce. Buttons are optional; without them the board stays on screen 1.
- Display errors are logged and retried at the next fetch.
- Logs button presses and releases, the GPIO pin factory, button states at start and after each refresh, and refresh duration.

## fetch_data.py

Queries `https://transport.integration.sl.se/v1/sites/<site_id>/departures` (no API key, one request per distinct site).

| Section | Site | Filter |
|---|---|---|
| `pendeltag` | `PENDELTAG_SITE_ID` | `transport_mode == "TRAIN"` |
| `buses` | `BUS_STOP_ID` | `designation == BUS_LINE` |
| `metro` | `METRO_SITE_ID` | `transport_mode == "METRO"`, `designation` in `METRO_LINES` if set |

Up to 13 departures per section; departures under 5 min away are dropped. On error a section is empty. Each fetch is also written to `DATA_FILE`.

Run directly to fetch once: prints `Data saved: <n> trains, <m> buses, <k> metro`.

## display_data.py

- Driver: `waveshare_epd.epd7in5_V2`, imported from `EPD_LIB_PATH`. Full refresh, then deep sleep (image retained without power).
- Fonts: DejaVu Sans / Sans Bold from `/usr/share/fonts/truetype/dejavu/`.
- Layout: header with `STATION_NAME`, screen number and update time, shared column headings (line, destination, time), then the screen's sections. Section titles: `Pendeltåg`, `BUS <BUS_LINE> - <BUS_STOP_NAME>`, `Tunnelbana <METRO_LINES>`. Empty sections show `No departures`.
- Runs without root if the user is in the `spi` and `gpio` groups.

Run directly to draw `DATA_FILE` once: `python3 display_data.py [1-4]` (screen number, default 1).

## config.py

- Parses `KEY=VALUE` lines from `.env` (UTF-8). Blank lines and `#` comments are ignored; surrounding quotes are stripped.
- Environment variables override values in `.env`.
- Missing required settings stop the program with `Missing required setting '<KEY>' (check <path>/.env)`.

Settings reference: [setup/README.md#configuration](setup/README.md#configuration).

## Running manually

On the Pi, in the firmware directory. Stop the service first (`sudo systemctl stop displegory`); only one process may drive the display.

```bash
sudo systemctl stop displegory
python3 fetch_data.py        # fetch once
python3 display_data.py 2    # draw screen 2 from the last fetch
./run.sh                     # full program, Ctrl+C to stop
sudo systemctl start displegory
```

As a service: `setup/displegory.service`, see [setup/README.md](setup/README.md#9-start-on-boot).

## Customisation

| Change | Where |
|---|---|
| Stations, lines, labels, button pins, fetch interval | `.env` |
| 5-minute departure cutoff | `fetch_data.py`, `MIN_MINUTES` |
| Screens, section order, rows per section | `display_data.py`, `SCREENS`. Height: 112 + per section (40 + rows x 25) must be at most 480. Raise `MAX_DEPARTURES` in `fetch_data.py` if a section shows more than 13 rows. |
| Layout, fonts | `display_data.py`, layout constants |
