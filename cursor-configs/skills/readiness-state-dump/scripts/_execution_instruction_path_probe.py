#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Cross-venv probe -- run under execution-service/.venv ONLY, as a subprocess
from derive_readiness.py. Never imported directly by anything running under
unified-api-contracts's venv (same rule as the sibling
_execution_order_capability_probe.py).

Reads a JSON list of canonical dash-form venue names from stdin. Returns
``execution_service.readiness.instruction_path.instruction_path_availability_map(venues)``
as JSON to stdout -- verbatim, no reshaping. That function's own docstring
already anticipates this exact use ("The shape a cross-venv readiness probe
serialises straight to JSON"); this probe is what finishes wiring it in.

This closes a real gap, not a hypothetical one: `checks.py`'s
`execution_instruction()` module comment (dated 2026-08-20, same day this
module shipped as execution-service@b70d2edb16) says "no per-venue
instruction-path registry exists in execution-service" -- true when written,
false by end of day. The check this probe exposes IS that per-venue registry;
it was built for exactly this dump (see instruction_path.py's own module
docstring, "W20 grades each venue on twelve legs... this module is the check
it was missing") and simply never got wired in before this fix.
"""

from __future__ import annotations

import json
import sys

from execution_service.readiness.instruction_path import instruction_path_availability_map


def main() -> int:
    venues = json.loads(sys.stdin.read())
    result = instruction_path_availability_map(venues)
    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
