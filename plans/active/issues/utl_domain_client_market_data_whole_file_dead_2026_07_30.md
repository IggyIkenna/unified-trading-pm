---
doc_type: issue
title:
  unified-trading-library domain_client/clients/market_data.py — entire file appears dead (6 classes, zero callers, zero
  tests)
summary: >-
  Discovered while investigating the GCS path-resolution centralization audit's "duplicate raw_tick_data path builders"
  todo (both originally-cited files are already resolved — see that todo's flip in
  gcs_path_resolution_centralization_audit_2026_07_28.md). This is a NEW, separate finding: a different file,
  unified_trading_library/domain_client/clients/market_data.py, contains 6 classes (MarketTickDomainClient,
  MarketCandleDomainClient, MarketCandleDataDomainClient, MarketTickDataDomainClient, MarketDataDomainClient, plus
  factory functions) — grep across unified-trading-library, market-tick-data-service, features-service,
  execution-service, instruments-service, and market-data-processing-service found ZERO real production callers for ANY
  of the 6 classes (checked class-by-class, not just the file as a whole), and ZERO test coverage anywhere. One of the
  classes (MarketTickDataDomainClient._build_tick_gcs_path) also has the SAME missing-segments bug pattern this whole
  audit has been finding elsewhere (hand-rolled f"raw_tick_data/by_date/day={date_str}/data_type=..." prefix, missing
  pipeline_mode=/asset_group=/venue= — never delegates to the PATH_REGISTRY SSOT).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [gcs, path-resolution, dead-code, domain-client]
related: [/plans/archive/issues/gcs_path_resolution_centralization_audit_2026_07_28.md]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-07-30 while closing out the GCS path-resolution centralization audit's remaining open todos under
  /autonomous, specifically while investigating whether the "duplicate raw_tick_data path builders" finding was fully
  resolved. This file was not part of that todo's original scope (which cited domain/standardized_service.py and
  domain/market_data_client.py — a DIFFERENT, already-deleted module) — it's a fresh discovery in a
  differently-named-but-confusingly-similar module (domain_client/clients/ vs the old domain/).
resolved_by:
depends_on: []
---

# unified-trading-library domain_client/clients/market_data.py — entire file appears dead

## What was found

`unified_trading_library/domain_client/clients/market_data.py` (390 lines) defines:

- `MarketTickDomainClient(BaseDataClient)` (line 43)
- `MarketCandleDomainClient(BaseDataClient)` (line 89)
- `MarketCandleDataDomainClient` (line 141)
- `MarketTickDataDomainClient` (line 264) — has `_build_tick_gcs_path()`, a hand-rolled
  `f"raw_tick_data/by_date/day={date_str}/data_type={data_type}"` prefix that never delegates to the
  `unified_trading_library.config_interface.paths.registry.PATH_REGISTRY` SSOT — missing `pipeline_mode=`,
  `asset_group=`, `venue=` segments, same bug class this whole audit has been fixing everywhere else.
- `MarketDataDomainClient(MarketCandleDataDomainClient)` (line 347) — has its own docstring:
  `"""DEPRECATED: Use MarketCandleDataDomainClient or MarketTickDataDomainClient instead."""` (line 348) — confirming
  even the file's own author considers part of it legacy.
- 3 factory functions: `create_market_candle_data_client`, `create_market_tick_data_client`,
  `create_market_data_client`.

**Caller check** (2026-07-30): grepped for each class name individually across
`unified-trading-library`/`market-tick-data-service`/`features-service`/`execution-service`/`instruments-service`/
`market-data-processing-service`, excluding the file's own definition and the `domain_client/clients/__init__.py` +
`domain_client/__init__.py` re-export chains. Zero real callers found for all 6 classes.

**Test coverage check**: grepped `tests/` for any reference to `domain_client.clients.market_data` or any of the 6 class
names. Zero matches — this file appears to have NEVER had a dedicated test file.

## Why this wasn't just deleted in the same session

This is a genuinely separate discovery from what was in scope — the original audit todo
(`gcs_path_resolution_centralization_audit_2026_07_28.md`'s "duplicate raw_tick_data path builders" finding) cited
`unified_trading_library/domain/standardized_service.py` and `unified_trading_library/domain/market_data_client.py` —
the OLD `domain/` module (not `domain_client/`), which is a **different, already-fully-resolved** legacy layer (both
files handled: `market_data_client.py` deleted, `standardized_service.py`'s offending code removed, both as part of
`unified-trading-library@f4987fb8` earlier the same day). This `domain_client/clients/market_data.py` finding surfaced
only because of the confusingly similar naming (`MarketTickDataDomainClient` exists in BOTH the old deleted file and
this still-live one) while double-checking the original todo was truly closed.

Given the scope of a full 6-class deletion (verify each class's caller status individually — done above — then delete
the file, clean up 2 `__init__.py` re-export chains, and confirm no test breakage) is a genuinely separate unit of work
from what this session's task was, it's being filed here rather than folded into an already-in-flight,
differently-scoped commit.

## Recommended next step

- [ ] [SCRIPT] P2. **Delete `unified_trading_library/domain_client/clients/market_data.py` in full** (all 6 classes + 3
      factory functions) — re-verify the zero-callers finding above is still current (things move fast on this shared
      branch), then delete the file and remove its exports from
      `unified_trading_library/domain_client/clients/__init__.py` and
      `unified_trading_library/domain_client/__init__.py`. No test files need updating (none reference this module). Run
      `quality-gates.sh` to confirm nothing else breaks, then ship via quickmerge. (repo: unified-trading-library)
