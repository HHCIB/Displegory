# Displegory firmware

Python scripts that fetch live SL departures (commuter rail, one bus line and optionally metro) and render them on a Waveshare 7.5" e-Paper V2 display (800x480, black/white) driven by a Raspberry Pi.

Device setup and configuration: [setup/README.md](setup/README.md).

## Files

| File | Purpose |
|---|---|
| `fetch_data.py` | Queries the SL Transport API, filters departures, writes them to a JSON file. |
| `display_data.py` | Reads the JSON file, renders the departure board, pushes it to the display. |
| `config.py` | Loads settings from `.env`. Imported by both scripts. |
| `run.sh` | Main loop: fetch, pause, display, wait. |
| `.env.example` | Settings template. Copy to `.env`. |
| `.env` | Local settings (station IDs, names, paths). Not committed. |

All files must be in the same directory: `config.py` reads `.env` from its own directory, and `run.sh` calls the scripts from its own directory.

## Data flow

```
SL Transport API --> fetch_data.py --> DATA_FILE (JSON) --> display_data.py --> e-Paper
```

Fetching and rendering run as separate processes so the network step and the display refresh never overlap.

## Display modes

Set with `DISPLAY_MODE` in `.env`.

| Mode | Sections (rows shown) |
|---|---|
| `train_bus` (default) | Pendeltåg (6), bus (5) |
| `train_bus_metro` | Pendeltåg (3), bus (3), metro (3) |

## fetch_data.py

Queries `https://transport.integration.sl.se/v1/sites/<site_id>/departures` (no API key, one request per distinct site) and writes `update_time`, `pendeltag`, `buses` and `metro` to `DATA_FILE`.

| Section | Site | Filter | Max |
|---|---|---|---|
| Trains | `PENDELTAG_SITE_ID` | `transport_mode == "TRAIN"` | 8 |
| Buses | `BUS_STOP_ID` | `designation == BUS_LINE` | 5 |
| Metro | `METRO_SITE_ID` | `transport_mode == "METRO"`, `designation` in `METRO_LINES` if set | 8 |

Metro is fetched only in `train_bus_metro` mode. Departures under 5 min away are dropped. On error a section is written empty.

## display_data.py

- Driver: `waveshare_epd.epd7in5_V2`, imported from `EPD_LIB_PATH`.
- Canvas: 800x480, 1-bit (`PIL.Image` mode `"1"`).
- Fonts: DejaVu Sans / Sans Bold from `/usr/share/fonts/truetype/dejavu/`. Falls back to the PIL default font if missing.
- Layout, top to bottom:
  - Header bar: `<STATION_NAME> - DEPARTURES`
  - Last update time and filter note
  - Column headings: line, destination, time
  - One section per transport type, per `LAYOUTS[DISPLAY_MODE]`. Titles: `Pendeltåg`, `BUS <BUS_LINE> - <BUS_STOP_NAME>`, `Tunnelbana <METRO_LINES>`. An empty section shows `No departures`.
- Destinations are truncated to 30 characters. Times are shown as `HH:MM`, or `??:??` if they can't be parsed.
- After the refresh the panel is put into deep sleep (`epd.sleep()`); the image is retained without power.
- Runs without root if the user is in the `spi` and `gpio` groups (default for the first user on Raspberry Pi OS).

stdout on success: `Display updated at <YYYY-MM-DD HH:MM:SS>`

Exits without touching the display if `DATA_FILE` is missing.

## config.py

- Parses `KEY=VALUE` lines from `.env` (UTF-8). Blank lines and `#` comments are ignored; surrounding quotes are stripped.
- Environment variables override values in `.env`.
- Missing required settings stop the script with `Missing required setting '<KEY>' (check <path>/.env)`.
- No third-party dependencies.

Settings reference: [setup/README.md#configuration](setup/README.md#configuration).

## run.sh

Loop:

1. `python3 fetch_data.py`
2. `sleep 5` (lets the Wi-Fi radio go idle before the panel refresh)
3. `python3 display_data.py`
4. `sleep 60`

Effective refresh interval: about 65 s plus script runtime. Stop with Ctrl+C.

## Running manually

On the Pi, in the firmware directory:

```bash
python3 fetch_data.py
python3 display_data.py
./run.sh
```

As a service: `setup/displegory.service`, see [setup/README.md](setup/README.md#9-start-on-boot).

## Customisation

| Change | Where |
|---|---|
| Mode, stations, lines, labels, paths | `.env` |
| 5-minute departure cutoff | `fetch_data.py`, `MIN_MINUTES` |
| Number of departures fetched | `fetch_data.py`, last argument of each `select()` call |
| Rows shown per section, section order | `display_data.py`, `LAYOUTS`. Total must fit 480 px: 112 + per section (40 + rows x 25). |
| Layout, fonts | `display_data.py`, layout constants |
| Refresh interval | `run.sh`, `sleep 60` |
