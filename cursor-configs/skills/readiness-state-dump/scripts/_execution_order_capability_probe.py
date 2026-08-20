#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Cross-venv probe -- run under execution-service/.venv ONLY, as a subprocess
from derive_readiness.py. Never imported directly by anything running under
unified-api-contracts's venv, which does not have execution-service installed
(service-to-service import would violate the T4 tier rule anyway -- this
script is invoked as a separate process, not imported as a module).

Reads a JSON list of canonical dash-form venue names (e.g. "OKX-FUTURES") from
stdin. For each venue, resolves the base source string via execution-service's
OWN execution_service.trade_execution.factory._resolve_venue_str -- the real
per-market-type interpretation execution-service owns (it has documented
one-off exceptions, e.g. COINBASE-FUTURES has no real adapter even though
"coinbase" is a registered base venue -- a naive dash-strip would get this
wrong, so this probe defers to the real function rather than reimplementing
it centrally, per the workspace's own "reimplementation is drift with a delay
fuse" rule).

Reports, per venue:
  - adapter_present: whether an order-adapter class is registered for this
    venue at all (execution_service.trade_execution.factory.get_supported_venues()
    membership -- structural, never constructs a real adapter instance, so
    this never calls a live venue API).
  - place_order: {"mainnet": bool|None, "testnet": bool|None} -- the UAC
    capability registry's declared place_order support
    (unified_api_contracts.registry.validate_operation), read only when an
    adapter is present. None means the source has no capability declaration
    at all for this operation/env (genuinely unknown -- mirrors
    execution_service.trade_execution.factory._run_capability_preflight's own
    "pass through gracefully" handling of CapabilityResolutionError, not a
    negative).

Prints a JSON {venue: {...}} dict to stdout.
"""

from __future__ import annotations

import json
import sys

from execution_service.trade_execution.factory import _resolve_venue_str, get_supported_venues
from unified_api_contracts.registry import (
    CapabilityResolutionError,
    UnsupportedOperationError,
    validate_operation,
)


def _place_order_supported(venue_str: str, env: str) -> bool | None:
    try:
        validate_operation(venue_str, "place_order", env)
    except UnsupportedOperationError:
        return False
    except CapabilityResolutionError:
        return None
    return True


def main() -> int:
    venues = json.loads(sys.stdin.read())
    supported = set(get_supported_venues())
    out = {}
    for venue in venues:
        try:
            venue_str, _inferred_futures = _resolve_venue_str(venue)
        except ValueError:
            # A canonical venue string naming a market type with no real
            # execution adapter (e.g. COINBASE-FUTURES) -- structurally absent.
            out[venue] = {"adapter_present": False, "place_order": {"mainnet": None, "testnet": None}}
            continue
        adapter_present = venue_str in supported
        out[venue] = {
            "adapter_present": adapter_present,
            "place_order": {
                "mainnet": _place_order_supported(venue_str, "mainnet") if adapter_present else None,
                "testnet": _place_order_supported(venue_str, "testnet") if adapter_present else None,
            },
        }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
