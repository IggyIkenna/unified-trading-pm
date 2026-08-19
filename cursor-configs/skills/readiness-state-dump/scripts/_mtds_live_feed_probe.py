#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Cross-venv probe -- run under market-tick-data-service/.venv ONLY, as a
subprocess from derive_readiness.py. Never imported directly by anything
running under unified-api-contracts's venv, which does not have
market-tick-data-service installed (service-to-service import would violate
the T4 tier rule anyway -- this script is invoked as a separate process, not
imported as a module).

Answers "does this venue have a real live WSFeedConnector wired?" -- the
real, shipped per-venue live-connector registry
(market_tick_data_service.live.connector_registry / WS_FEED_CONNECTOR_FACTORIES,
Phase 3.5 of live_pipeline_mtds_mdps_features_2026_05_08.md). This script does
not reimplement that registry; it side-effect-loads every connector module via
the service's own market_tick_data_service.live.connectors.register_all()
helper (the same helper CLI startup uses to populate the registry) and then
reads it back.

Takes no stdin input -- the registry is a global, not a per-venue query.
Prints a JSON list of registered canonical venue names to stdout.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    from market_tick_data_service.live.connector_registry import registered_venues
    from market_tick_data_service.live.connectors import register_all

    register_all()
    json.dump(list(registered_venues()), sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
