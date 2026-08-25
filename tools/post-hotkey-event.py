#!/usr/bin/env python3
"""Post one synthetic macOS key press/release for isolated release verification."""

from __future__ import annotations

import argparse
import time

from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    CGEventSetFlags,
    kCGHIDEventTap,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("keycode", type=int)
    parser.add_argument("flags", type=int)
    args = parser.parse_args()
    if not 0 <= args.keycode <= 127 or args.flags <= 0:
        parser.error("keycode must be 0..127 and flags must be positive")

    for pressed in (True, False):
        event = CGEventCreateKeyboardEvent(None, args.keycode, pressed)
        if event is None:
            raise RuntimeError("CGEventCreateKeyboardEvent returned nil")
        CGEventSetFlags(event, args.flags)
        CGEventPost(kCGHIDEventTap, event)
        time.sleep(0.2)


if __name__ == "__main__":
    main()
