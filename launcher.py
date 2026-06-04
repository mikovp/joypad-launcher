#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Joypad Launcher entry point. Real code lives in the `joypad` package."""

import sys

from joypad.app import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
