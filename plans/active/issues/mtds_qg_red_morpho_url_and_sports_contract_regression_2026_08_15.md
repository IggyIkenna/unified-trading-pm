---
doc_type: issue
title: "market-tick-data-service QG RED — hardcoded morpho URL + sports adapter-contract regression"
summary: >-
  quality-gates.sh for market-tick-data-service is currently RED due to two unrelated pre-existing findings from other
  recent commits, blocking unrelated in-flight work (confirmed not caused by this reporter's diff -- a crc32c
  content-verify fix in migrate_tradfi_underlying_display_names_2026_08.py, which touches neither flagged file).
status: open
nature: issue
asset_group: [defi, sports]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [qg-red, hardcoded-url, adapter-contract-regression, delete-safety-unrelated]
related: []
parent_epic: infrastructure_master
source: "tradfi_satellite_ao_dispatch_batch13_2026_08_13.md todo 4 -- discovered while shipping an unrelated fix"
assigned_vm: NA
created: 2026-08-15
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope: []
---

# market-tick-data-service QG RED — two unrelated pre-existing findings

## What I found

Running `bash scripts/quality-gates.sh --no-fix` for `market-tick-data-service` on a clean rebase of
`origin/live-defi-rollout` (HEAD `050620136f4d9ecd7f6898385b0b94cd24270733`) fails with 2 findings, neither touched by
my own diff (`market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py`

- its test):

1. **Hardcoded venue URL** — `market_tick_data_service/cli/handlers/_oracle_prices_constants.py:556`:

   ```
   ERROR: blue-api.morpho.org bare literal in .../cli/handlers (use get_evm_protocol_rest_url("morpho")
   from unified_api_contracts.registry)
   ```

   Last touched by `96eedd876410e3ac4c04e093cb6e4f75d5d2ca95` ("feat(defi): wire MORPHO-ETHEREUM oracle_prices capture
   (Morpho Blue IOracle.price())"), 2026-08-14 23:40:35 UTC — the comment on the flagged line reads
   `# DERIVED 2026-08-14 from docs.morpho.org (same endpoint morpho_adapter.py/lending_indices_morpho.py already use)`,
   confirming the literal was introduced deliberately but without routing through the UAC registry helper.

2. **Adapter contract regression** —
   `instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py`:
   ```
   [FAIL] ...sports_reference_core.py: 14 contract calls < baseline 19. Patterns tracked: classify_venue_error |
   ADAPTER_FETCH_FAILED | record_captured | record_empty | record_zero_rows | record_failed |
   record_catalog_unavailable | record_shard_failure.
   [check_adapter_contract_regression] 1 file(s) regressed below baseline.
   ```
   Last touched by `4844b6286b21c645a81cb05b43801da4bca03ff3` ("fix(sports): close api_football fixture-existence +
   observed-coverage gaps in expected-universe enumerator and live writer"), 2026-08-15 02:16:13 +0100 — this refactor
   appears to have dropped 5 of the tracked contract-call patterns (classify_venue_error / ADAPTER_FETCH_FAILED /
   record_captured / record_empty / record_failed) below the `adapter_contract_baseline.yaml` floor. This is
   cross-repo-checked from MTDS's own gate (§ "5.70/6 IS-MTDS CONTRACT INTEGRITY"), which is why it surfaces here even
   though the file lives in `instruments-service`.

## Why it matters

Both findings independently fail `quality-gates.sh` for `market-tick-data-service`, which blocks EVERY unrelated
shippable unit from this repo (per the commit-quality-boundary HARD RULE) until fixed. Confirmed pre-existing (not
caused by my diff) via `git log -1 -- <file>` on each flagged file, both showing very recent, unrelated authors/commits.

## Recommended decision

## Todos

- [ ] [CODE] P1. Route `market_tick_data_service/cli/handlers/_oracle_prices_constants.py:556`'s `_MORPHO_BLUE_API_URL`
      literal through `get_evm_protocol_rest_url("morpho")` from `unified_api_contracts.registry` instead of the bare
      `https://blue-api.morpho.org/graphql` string. Repo: market-tick-data-service.
- [ ] [CODE] P1. Restore the 5 missing tracked contract-call patterns (classify_venue_error, ADAPTER_FETCH_FAILED,
      record_captured, record_empty, record_failed) in
      `instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py` that
      `4844b6286b21c645a81cb05b43801da4bca03ff3`'s api_football fixture-existence refactor dropped below the
      `adapter_contract_baseline.yaml` floor of 19 — or, if the drop is a legitimate intentional consolidation,
      regenerate the baseline per the QG script's own instructions (`--regenerate-baseline`, never to mask a real
      regression). Repo: instruments-service.
