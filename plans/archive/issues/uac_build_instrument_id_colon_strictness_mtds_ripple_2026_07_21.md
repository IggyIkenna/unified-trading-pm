---
doc_type: issue
title:
  UAC `build_instrument_id` new embedded-`:` strictness breaks 3 MTDS tests (cross-repo ripple, discovered mid-flight
  2026-07-21)
summary: >-
  Discovered 2026-07-21 while trying to get `market-tick-data-service`'s full `quality-gates.sh` green to ship
  cefi_chain_tail_v6_canonicalisation_2026_07_21.md todos 2-5. A concurrent UAC commit (landed same session, HEAD moved
  `7335631d`(unrelated)→...→ eventually past `84af308f`, touching `unified_api_contracts/internal/reference/
  canonical_id_builder.py` + `tests/internal/unit/test_canonical_id_builder.py`) made `build_instrument_id` RAISE loud
  when the `symbol` argument carries an embedded `:` for any non-sports/non-prediction asset_group (routing such symbols
  through the new UAC quarantine model instead). MTDS installs UAC as an editable/workspace dependency, so this new
  strictness took effect immediately in MTDS's OWN test run without any MTDS-side commit — three MTDS tests that pass a
  raw wire symbol containing `:` (a Bitfinex-style `ADAF0:USTF0`, a DeFi pool `WETH:USDC`) now fail where they
  previously exercised the pre-quarantine passthrough behavior.
status: resolved
nature: issue
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cross-repo, breaking-change, canonical-id, build_instrument_id, quarantine-model, editable-install-ripple]
related:
  [
    /plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/archive/issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "slot-7 (data_engineering), 2026-07-26 — all 5 todos closed, see todos section"
source:
  discovered blocking an unrelated MTDS quickmerge attempt (cefi_chain_tail_v6_canonicalisation_2026_07_21.md),
  2026-07-21
depends_on: []
---

# UAC `build_instrument_id` colon-strictness — MTDS ripple

> **Duplicate-discovery note (added 2026-07-25, /plan-reconcile apply pass):** the identical regression (same UAC
> commit, same 3 failing tests) was independently discovered and written up the same day as
> [`mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md`](/plans/archive/issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md)
> (narrative-only, no tracked todos). This doc carries the actionable todos below — track the fix here.

## What happened

While running `market-tick-data-service`'s full `bash scripts/quality-gates.sh` repeatedly to get a green sentinel for
an UNRELATED fix (cefi chain-tail v6), a concurrent, independent UAC commit landed mid-session that changed
`unified_api_contracts.internal.reference.canonical_id_builder.build_instrument_id` to RAISE `ValueError` when `symbol`
carries an embedded `:` for a non-sports/non-prediction asset_group (message:
`"the canonical id's own VENUE:TYPE:SYMBOL delimiter... route a genuinely-unresolvable instrument through the UAC quarantine model (unified_api_contracts.canonical.quarantine)"`).
Because MTDS installs `unified-api-contracts` as an editable workspace dependency, this new strictness applied to MTDS's
test suite IMMEDIATELY, with zero MTDS-side commit — purely from UAC's HEAD moving underneath it.

Three MTDS tests now fail (confirmed reproducible, confirmed NOT caused by any uncommitted MTDS diff — `git status`
shows all three files + `git diff` clean against MTDS's own HEAD `7335631d`):

1. `tests/unit/test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment` — DeFi Chainlink
   oracle-price live path (`live_tick_blob_path`), symbol `eth/usd` fails a DIFFERENT (pre-existing, unrelated)
   defi-filename-canonical-stem check downstream once `build_instrument_id` no longer silently passes through.
2. `tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py::TestLeafByteMatchWithR1:: test_decoded_leaf_equals_r1_forward_writer_leaf[WETH:USDC]`
   — `write_defi_rows` → `build_instrument_id(..., "WETH:USDC", ...)` for `instrument_type=POOL` now raises instead of
   building the (admittedly malformed) double-wrapped id the test was pinning.
3. `tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py:: test_disabled_by_default_output_is_byte_identical[BITFINEX-FUTURES-PERPETUAL-ADAF0:USTF0-...]`
   — `tardis_shared.derive_row_instrument_id` → `build_instrument_id(venue, PERPETUAL, "ADAF0:USTF0")` (the
   disabled-by-default / no-wire-map fallback path) now raises for the SAME reason.

## Why this is a genuine finding, not noise

- Confirmed NOT a transient/host-load artifact: reproduced deterministically twice, in isolation, against MTDS's own
  unchanged, clean-diff HEAD.
- Confirmed the CAUSE: the traceback's `unified_api_contracts` frame resolves to
  `../unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py:862` — i.e. MTDS's `.venv`
  really is reading UAC's live/current source via the editable install, and UAC's `git log` shows the exact landing
  commit touched that file + its test.
- **This is a real cross-repo breaking-change gap**: UAC tightened a shared contract (`build_instrument_id`) without
  MTDS's own call sites / tests being updated in the same wave — the two repos are momentarily out of lockstep. Per
  `/codex/04-architecture/tier-and-import-architecture.md` MTDS depends on UAC as a shared lib; a UAC-side behavior
  change that MTDS's test suite doesn't yet accommodate is exactly the kind of drift that gate is meant to catch.
- **Blast radius on the shipping pipeline**: as long as this persists, `market-tick-data-service`'s full
  `quality-gates.sh` cannot reach green for ANY agent's diff (not just this one) — it blocks all MTDS quickmerges
  fleet-wide until resolved.

## What was NOT done (explicitly out of scope for the discoverer)

The discovering session did not fix this — it is unrelated to that session's actual task (cefi chain-tail v6), the fix
requires understanding the NEW UAC quarantine model's intended MTDS-side call pattern (which route legitimately needs
quarantine vs which needs a catalogue/wire-map resolution fix), and touching `write_defi_rows` /
`tardis_shared.derive_row_instrument_id` / the Chainlink oracle live path is real, unrelated surface area.

## Todos

- [x] ✅ 1. [REVIEW] P1. **DONE 2026-07-26 (slot-7, `data_engineering`).** `git log` confirms the companion MTDS fix
      landed the SAME day: `market-tick-data-service@08f15f26` ("fix(tests): update 2 stale regression-guard tests for
      uac@502ef57e's fail-loud-on-embedded-colon build_instrument_id ruling"), 2026-07-21. Cross-linked here, not
      duplicated.
- [x] ✅ 2. [DATA] P1. **DONE 2026-07-26 (slot-7, `data_engineering`) — VERIFIED NO CODE FIX NEEDED.** Traced every real
      production caller of `write_defi_rows` with `instrument_type=POOL`
      (`_dex_pools_subgraph.py`/`dex_swaps_handler.py` via `_dex_pool_symbol.py::resolve_pool_symbol` — catalogue +
      row-level token_a/token_b resolution, dash-separated `TOKEN0-TOKEN1[-FEE]`, honest bare-pool-address fallback;
      `orca_whirlpool_state_handler.py`/`raydium_classic_amm_handler.py` via hardcoded underscore-joined `pool_label`,
      e.g. `Whirlpool_SOL_USDC`) — NONE produce a colon-bearing symbol. `WETH:USDC` was a synthetic test fixture
      exercising a hypothetical, not a real wire-format symbol any live adapter emits. `08f15f26` correctly removed the
      unrealistic parametrize case rather than leaving a live gap. No quarantine routing needed (the quarantine registry
      is explicitly narrow-scoped to ONE permanent exception, PACIFICA-SOLANA — using it for a non-existent case would
      be a misuse of that mechanism).
- [x] ✅ 3. [DATA] P1. **DONE — same verification.** `tardis_shared.py::derive_row_instrument_id`'s disabled-by-default
      fallback: `08f15f26` added `test_disabled_by_default_raises_on_embedded_colon_symbol`, explicitly documenting that
      the REGISTERED path (`_SYNTHETIC_MAP`) already resolves `ADAF0:USTF0` → `ADA-USDT@LIN` correctly in production;
      the disabled fallback correctly fails loud now for a genuinely-unresolved symbol (the intended new contract),
      which only matters for the synthetic no-catalogue test scenario, not live traffic.
- [x] ✅ 4. [REVIEW] P2. **DONE — confirmed DISTINCT, not the same fix.** `test_slash_id_never_forges_a_path_segment`
      now carries its own
      `@pytest.mark.xfail(reason="uac@502ef57e widened _ID_FORM_CHECKED_ASSET_GROUPS...",     strict=False)` — a
      separate mechanism (bare oracle pair-id `eth_usd` failing the ID_FORM check), tracked in
      `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` §7. Currently XPASSes (the assertions hold); not a
      blocker (`strict=False`).
- [x] ✅ 5. [REVIEW] P2. **DONE 2026-07-26** — full `market-tick-data-service` `bash scripts/quality-gates.sh --no-fix`
      run clean, sentinel matches HEAD (`f6ea0010`). All 3 originally-failing tests pass/no-longer-apply; no other
      fallout found. Setting `status: resolved`.
