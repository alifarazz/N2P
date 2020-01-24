#!/usr/bin/env python3

import asyncio
import aioconsole

import signal
import sys

from typing import cast, List, Tuple

cancel_signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)

