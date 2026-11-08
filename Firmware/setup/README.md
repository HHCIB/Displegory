# Setup and configuration

Installs the Displegory firmware on a Raspberry Pi 3 B+ from a blank SD card. Software reference: [../README.md](../README.md).

## Requirements

| Item | Notes |
|---|---|
| Raspberry Pi 3 B+ | Any board with the 40-pin header and SPI should work; only the 3 B+ is covered here. |
| Waveshare 7.5" e-Paper V2 + driver HAT | 800x480 black/white. Datasheet: `7.5inch_e-Paper_V2_Specification.pdf` in the project root. |
| microSD card | 8 GB or larger. |
| Power supply | 5 V / 2.5 A micro-USB. |
| Computer | Raspberry Pi Imager, SSH and `scp`. |

Tested OS release: Raspberry Pi OS Lite 64-bit, Debian 13.7 (trixie), `aarch64`.

## 1. Flash the OS

On your computer, in Raspberry Pi Imager:

1. Device: Raspberry Pi 3. OS: Raspberry Pi OS (other) > Raspberry Pi OS Lite (64-bit). No desktop needed; the device is managed over SSH.
2. Open OS customisation and set:

| Setting | Value |
|---|---|
| Hostname | `<hostname>` |
| Username / password | `displegory` (default; any other name requires setting `EPD_LIB_PATH`) / your choice |
| Wi-Fi | SSID, password, country |
| SSH | Enabled. Public-key authentication recommended. |

3. Write the image. **This erases the selected card.**

Boot the Pi and connect:

```bash
ssh <user>@<hostname>
```

If `<hostname>` doesn't resolve, try `<hostname>.local` (mDNS) or the Pi's IP (`hostname -I` on the Pi). WSL often can't resolve `.local` names.

If you've used the hostname or IP for another device before, remove its old host key first: `ssh-keygen -R <hostname>`.

## 2. Enable SPI

On the Pi:

```bash
sudo raspi-config nonint do_spi 0
```

Reboot after step 4.

## 3. Install dependencies

On the Pi:

```bash
sudo apt update
sudo apt install -y python3-requests python3-pil python3-spidev python3-rpi.gpio python3-gpiozero fonts-dejavu-core git
```

Use `apt`, not `pip` (PEP 668 blocks system-wide pip installs). If `python3-rpi.gpio` is not found, install `python3-rpi-lgpio` instead.

## 4. Install the Waveshare driver

On the Pi:

```bash
git clone --depth 1 https://github.com/waveshare/e-Paper.git ~/e-Paper
mkdir -p ~/firmware
sudo reboot
```

After the reboot, verify SPI and the driver:

```bash
ls /dev/spidev*
ls ~/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd7in5_V2.py
```

Expected: `/dev/spidev0.0  /dev/spidev0.1`, then the driver file path.

The driver path used by the firmware is `/home/<user>/e-Paper/RaspberryPi_JetsonNano/python/lib`.

## 5. Copy the firmware

On your computer, in the `Firmware` directory:

```bash
scp fetch_data.py display_data.py config.py run.sh .env.example <user>@<hostname>:~/firmware/
```

If you already have a configured `.env`, add it to the `scp` command and skip `cp .env.example .env` in step 6.

Keep all files in one directory on the Pi; `config.py` and `run.sh` locate the other files relative to themselves.

If you edit files on Windows, save them with LF line endings; CRLF breaks `run.sh`.

## 6. Configure

On the Pi:

```bash
cd ~/firmware
cp .env.example .env
chmod 600 .env
chmod +x run.sh
nano .env
```

`.env` holds your stations and paths. Keep it out of version control (it's listed in `.gitignore`).

## Configuration

`.env` format: one `KEY=VALUE` per line, UTF-8, `#` for comments. Quotes are optional. Environment variables with the same name override the file.

| Setting | Required | Description | Example |
|---|---|---|---|
| `DISPLAY_MODE` | No | `train_bus` or `train_bus_metro`. Default: `train_bus`. | `train_bus_metro` |
| `PENDELTAG_SITE_ID` | Yes | SL site ID of the train station. All `TRAIN` departures from this site are shown. | `9117` |
| `BUS_STOP_ID` | Yes | SL site ID of the bus stop. | `9117` |
| `BUS_LINE` | Yes | Bus line number, as shown on the bus. Only this line is shown. | `50` |
| `METRO_SITE_ID` | In `train_bus_metro` | SL site ID of the metro station. | `9117` |
| `METRO_LINES` | No | Comma-separated metro lines to show. Empty: all metro lines at the site. | `17,18,19` (green line) |
| `STATION_NAME` | No | Display header text. Default: `Station`. | `Odenplan` |
| `BUS_STOP_NAME` | No | Bus section title suffix. Omitted if empty. | `Odenplan` |
| `DATA_FILE` | No | JSON file passed from fetch to display. Default: `/tmp/transport_data.json`. | `/tmp/transport_data.json` |
| `EPD_LIB_PATH` | No | Waveshare driver directory. Default: `/home/displegory/e-Paper/RaspberryPi_JetsonNano/python/lib`; set this if your username differs. | `/home/<user>/e-Paper/RaspberryPi_JetsonNano/python/lib` |

`STATION_NAME` and `BUS_STOP_NAME` support Swedish characters (å, ä, ö) if `.env` is saved as UTF-8.

### Finding site IDs

The site list (no API key required). Replace `<name>` with part of the station name:

```bash
curl -s https://transport.integration.sl.se/v1/sites | python3 -c 'import json,sys; [print(s["id"], s["name"]) for s in json.load(sys.stdin) if "<name>".lower() in s["name"].lower()]'
```

### Checking bus and metro lines

Lists the lines currently departing from a site (`BUS`, `METRO`, `TRAIN`):

```bash
curl -s https://transport.integration.sl.se/v1/sites/<site_id>/departures | python3 -c 'import json,sys; [print(d["line"]["designation"], d["line"]["transport_mode"], d["destination"]) for d in json.load(sys.stdin)["departures"]]'
```

## 7. Test

On the Pi, in `~/firmware`:

```bash
python3 fetch_data.py
```

Expected: `Data saved: <n> trains, <m> buses`

```bash
python3 display_data.py
```

Expected: `Display updated at <YYYY-MM-DD HH:MM:SS>`, and the departure board appears on the panel. No `sudo`: the user needs to be in the `spi` and `gpio` groups (check with `groups`; add with `sudo usermod -aG spi,gpio $USER`, then log in again).

| Error | Cause |
|---|---|
| `Missing required setting '<KEY>'` | `.env` missing from `~/firmware`, or the key is empty. |
| `ModuleNotFoundError: No module named 'config'` | `config.py` not in the same directory as the scripts. |
| `ModuleNotFoundError: No module named 'waveshare_epd'` | `EPD_LIB_PATH` doesn't match the driver location. |
| No SPI device / display doesn't refresh | SPI not enabled, or no reboot after enabling it. |

## 8. Run

```bash
./run.sh
```

Refreshes about every 65 s. Stop with Ctrl+C.

## 9. Start on boot

`displegory.service` runs `run.sh` as a systemd service after the network is up, and restarts it if it exits with an error. The file assumes the default user `displegory` and `/home/displegory/firmware`; the `sed` below substitutes your username if it differs.

On your computer, in the `Firmware` directory:

```bash
scp setup/displegory.service <user>@<hostname>:~/firmware/
```

On the Pi:

```bash
sed "s/displegory/$USER/g" ~/firmware/displegory.service | sudo tee /etc/systemd/system/displegory.service
sudo systemctl daemon-reload
sudo systemctl enable --now displegory.service
systemctl status displegory.service
```

Expected: `Active: active (running)`. The panel refreshes within about 10 s.

| Task | Command |
|---|---|
| Follow log output | `journalctl -u displegory -f` |
| Stop | `sudo systemctl stop displegory` |
| Disable on boot | `sudo systemctl disable displegory` |
| Restart after changing files or `.env` | `sudo systemctl restart displegory` |

Don't run `./run.sh` manually while the service is running; both would drive the display at once.
