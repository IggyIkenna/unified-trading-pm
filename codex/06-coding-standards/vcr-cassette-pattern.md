---
doc_type: codex-ssot
title: VCR Cassette Pattern
summary:
  The in-test VCR pattern (`@vcr.use_cassette` decorator usage + replay shape) for replaying venue HTTP/WS/SDK responses
  in the owning interface repo; cassette ownership/recording SSOT is `02-data/vcr-cassette-ownership.md`, which wins on
  divergence.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [vcr, cefi, mtds, instruments, quality-gates]
related: [/codex/02-data/vcr-cassette-ownership.md, /codex/07-security/testing-with-api-keys.md]
created: 2026-03-27
authoritative_for: [VCR cassette in-test decorator and replay pattern]
referenced_by: [/codex/06-coding-standards/testing.md, /codex/07-security/testing-with-api-keys.md]
owner:
last_reviewed:
code_refs:
---

# VCR Cassette Pattern

## Overview

VCR (Video Cassette Recorder) cassettes capture real HTTP/WebSocket/SDK responses from external venues and data sources,
then replay them in tests to avoid live network calls. This enables deterministic, fast integration tests without
hitting rate limits or requiring credentials.

## Cassette Locations

> **2026-05-12 reconciliation (TS-2 + TS-3)**: this section was stale — paths now match shipped UAC layout. Canonical
> SSOT for cassette ownership / recording / contributing is
> [`02-data/vcr-cassette-ownership.md`](/codex/02-data/vcr-cassette-ownership.md); this doc covers the in-test _pattern_
> (decorator usage + replay shape). When the two docs diverge, `vcr-cassette-ownership.md` wins.

| Repo                    | Path                                                  | Purpose                                                                                                    |
| ----------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts` | `unified_api_contracts/external/<venue>/mocks/*.yaml` | Cassette YAML files, one per endpoint                                                                      |
| `unified-api-contracts` | `unified_api_contracts/testing/vcr_endpoints.py`      | Endpoint definitions — URL patterns, request/response schema                                               |
| (per-interface repo)    | `<interface>/scripts/record_*.py`                     | Recording script — owned by each interface repo, NOT by AC (per `vcr-cassette-ownership.md` § "Recording") |

## Recording Cassettes

Recording scripts live in the **owning interface repo** (not in unified-api-contracts; AC ships no recording script —
see `02-data/vcr-cassette-ownership.md` § "Recording"). The shipped cassettes are then contributed back to AC's
`unified_api_contracts/external/<venue>/mocks/` directory via PR so all replay consumers share one path.

## Replay in Interface Repos

Cassettes are replayed in the owning interface repo, with `unified-api-contracts` as a dependency:

```python
# market-tick-data-service/market_tick_data_service/market_interface/tests/integration/test_binance_adapter.py
import pytest
import vcr

@pytest.mark.integration
@vcr.use_cassette("path/to/cassettes/binance_spot_klines.yaml")
def test_binance_kline_normalization():
    adapter = BinanceMarketAdapter(api_key="dummy")
    candles = adapter.get_candles("BTCUSDT", "1h", limit=10)
    assert len(candles) == 10
    assert candles[0].close > 0
```

## Cassette Ownership

- **Definition + storage:** `unified-api-contracts` (external schemas, venue contracts)
- **Execution:** owning interface repo (market-tick-data-service/market_tick_data_service/market_interface,
  unified-cloud-interface, instruments-service (formerly unified-reference-data-interface))
- **Never:** run VCR tests standalone from `unified-api-contracts` — the interface repo provides the test runner and
  normalization layer under test

## Updating Cassettes

Re-run the recording script when:

1. Venue API response schema changes
2. New endpoint is added to AC
3. Cassette is >90 days old (staleness risk)
