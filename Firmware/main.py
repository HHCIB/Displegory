#!/usr/bin/env python3
"""Departure board main loop: periodic fetch, button-driven screen switching."""
import logging
import threading
import time

from gpiozero import Button

import fetch_data
import display_data
from config import BUTTON_NEXT_PIN, BUTTON_PREV_PIN, REFRESH_SECONDS

RADIO_SETTLE_SECONDS = 5  # pause between fetch and panel refresh

log = logging.getLogger("displegory")

screen = 0
screen_lock = threading.Lock()
redraw = threading.Event()


def change_screen(step, name):
    global screen
    with screen_lock:
        screen = (screen + step) % len(display_data.SCREENS)
        target = screen
    log.info("Button %s pressed: screen %d queued", name, target + 1)
    redraw.set()


def button_states(*buttons):
    return ", ".join(
        f"GPIO{b.pin.number}={'pressed' if b.is_pressed else 'released'}" for b in buttons
    )


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    next_button = Button(BUTTON_NEXT_PIN, bounce_time=0.05)
    prev_button = Button(BUTTON_PREV_PIN, bounce_time=0.05)
    next_button.when_pressed = lambda: change_screen(1, "next")
    prev_button.when_pressed = lambda: change_screen(-1, "previous")
    next_button.when_released = lambda: log.info("Button next released")
    prev_button.when_released = lambda: log.info("Button previous released")
    log.info("Buttons: next GPIO%d, previous GPIO%d. Pin factory: %s",
             BUTTON_NEXT_PIN, BUTTON_PREV_PIN, type(next_button.pin_factory).__name__)
    log.info("Button states at start: %s", button_states(next_button, prev_button))
    log.info("Refresh every %d s.", REFRESH_SECONDS)

    data = None
    next_fetch = 0.0

    while True:
        if time.monotonic() >= next_fetch:
            data = fetch_data.fetch()
            fetch_data.save(data)
            log.info("Fetched: %s", fetch_data.summary(data))
            next_fetch = time.monotonic() + REFRESH_SECONDS
            time.sleep(RADIO_SETTLE_SECONDS)
            redraw.set()

        if redraw.is_set():
            # Presses during the refresh set redraw again and are drawn next pass.
            redraw.clear()
            with screen_lock:
                current = screen
            log.info("Drawing screen %d", current + 1)
            started = time.monotonic()
            try:
                display_data.show(display_data.render(data, current))
                log.info("Display updated: screen %d (%.1f s)",
                         current + 1, time.monotonic() - started)
            except Exception:
                log.exception("Display update failed")
            # A driver that resets GPIO on sleep would leave the buttons dead; this shows it.
            log.info("Button states after refresh: %s", button_states(next_button, prev_button))
            continue

        redraw.wait(timeout=max(0.0, next_fetch - time.monotonic()))


if __name__ == "__main__":
    main()
