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
parent_epic: security_and_cross_cutting_master
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
archive_exempt: true # na-eligibility-audit 2026-08-16: this run's edit dropped every open checkbox (extraction citation / stale-item close) -- 0-open-todos state is intentional, archival deferred to a separate follow-on pass per the sanctioned flip-then-mv two-commit pattern (scripts/plan-hygiene/check_archive_candidates.sh).
context_scope:
  [
    /codex/04-architecture/shard-level-failure-isolation.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py,
    instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
  ]
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

- **[CODE] P1. CANCELLED — extracted 2026-08-16 (na-eligibility-audit) → `defi_satellite_ao_dispatch_batch14_2026_08_16.md`
      (status: draft, pending operator approval)** — conflict-check found this exact fix already drafted there
      verbatim (todo "Route MTDS's hardcoded Morpho URL through the UAC registry"); do not re-extract or re-dispatch
      until that batch either activates+completes or is abandoned. Original item: route
      `market_tick_data_service/cli/handlers/_oracle_prices_constants.py:556`'s `_MORPHO_BLUE_API_URL` literal
      through `get_evm_protocol_rest_url("morpho")` from `unified_api_contracts.registry` instead of the bare
      `https://blue-api.morpho.org/graphql` string. Repo: market-tick-data-service.
- [x] ✅ [CODE] P1. **RESOLVED — verified live 2026-08-15.** Re-ran the actual scanner
      (`python3 unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <ws>`)
      against the current checkout: `OK — 363 baselined file(s) at or above minimum` (no violations). Root cause was a
      legitimate cohesion-module split, not a real drop: `4844b6286b`'s refactor extracted the fixture-existence
      cross-check into a new sibling file, `sports_reference_fixture_existence_gate.py` (308 lines, confirmed real
      `record_empty(...)` calls at lines 147/257/273/294 — not a stub), to keep `sports_reference_core.py` under its
      900-line cap (895→1004 before the split, 775 after). The baseline was correctly regenerated same-day
      (`unified-trading-pm@438838ae72`, "bump adapter-contract baseline for sports_reference_core.py cohesion-module
      split", landed 2026-08-15 02:23:11+0100, confirmed on `origin/live-defi-rollout`): `sports_reference_core.py`
      floor 19→14 + new entry `sports_reference_fixture_existence_gate.py` floor 6 (14+6=20 ≥ original 19 — call count
      went UP, not down). This is the SAME commit already cited in
      `sports_honest_coverage_gap_closure_2026_08_14.md:215`'s "FIXED, shipped, tested" claim — that claim was accurate;
      no correction needed there. This doc's todo-1 (hardcoded morpho URL, `_oracle_prices_constants.py:556`) is
      UNRELATED to this todo and still genuinely open (re-verified: literal `https://blue-api.morpho.org/graphql` still
      present, not yet routed through `get_evm_protocol_rest_url("morpho")`) — MTDS `quality-gates.sh` is still red on
      that finding alone, separate decision, not part of this todo's scope.

## Progress Log

- **context-scout 2026-08-15**: populated context_scope (3 entries).
- **2026-08-15 (P1 re-investigation)**: confirmed the adapter-contract-regression finding is resolved (baseline bump
  already shipped + verified via live scanner re-run); flipped that todo. The morpho-URL todo remains open and unrelated
  — `sports_honest_coverage_gap_closure_2026_08_14.md`'s "shipped, tested" claim was about the sports fix only and is
  confirmed accurate.
- **na-eligibility-audit 2026-08-16** [body-hash:9cc73d463ea1fac2]: KEEP-NA-STALE (already-duplicated), applied — sole open todo (route the hardcoded Morpho URL through the UAC registry) is verbatim-duplicated in defi_satellite_ao_dispatch_batch14_2026_08_16.md (status: draft). Converted the checkbox to a citation marker rather than reclassifying (would open a second dispatch path once batch14 activates). Doc stays NA, 0 open checkboxes remaining.
- **na-eligibility-audit 2026-08-17**: ARCHIVE-ready, reconfirmed — 0 open checkboxes. archive_exempt: true remains deliberately set per this doc's own note (flip-then-mv two-commit pattern) — not executed this run (hand off to the dedicated archive-candidates-audit pass).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
