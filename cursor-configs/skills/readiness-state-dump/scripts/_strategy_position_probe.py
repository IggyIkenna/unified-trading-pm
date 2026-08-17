#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Cross-venv probe -- run under strategy-service/.venv ONLY, as a subprocess
from derive_readiness.py. Never imported directly by anything running under
unified-api-contracts's venv, which does not have strategy-service installed
(service-to-service import would violate the T4 tier rule anyway -- this
script is invoked as a separate process, not imported as a module).

Reads a JSON list of venue names from stdin. Prints a JSON
{venue: {"batch": "...", "live": "...", "paper": "..."}} dict to stdout,
built by calling strategy-service's own position_read_mode_availability()
once per venue -- the real, shipped per-(venue, mode) position-adapter
capability table
(strategy_service/position/position_interface/capabilities.py). This script
does not reimplement that table; it only calls it and serializes the result.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

from strategy_service.position.position_interface.capabilities import (
    position_read_mode_availability,
)


def main() -> int:
    venues = json.loads(sys.stdin.read())
    out = {}
    for venue in venues:
        try:
            out[venue] = asdict(position_read_mode_availability(venue))
        except (ValueError, KeyError) as exc:
            out[venue] = {"error": str(exc)}
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
