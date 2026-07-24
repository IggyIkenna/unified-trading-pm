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
status: open
nature: issue
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cross-repo, breaking-change, canonical-id, build_instrument_id, quarantine-model, editable-install-ripple]
related:
  [
    /plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
    /codex/06-coding-standards/tier-and-import-architecture.md,
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
resolved_by:
source:
  discovered blocking an unrelated MTDS quickmerge attempt (cefi_chain_tail_v6_canonicalisation_2026_07_21.md),
  2026-07-21
depends_on: []
---

# UAC `build_instrument_id` colon-strictness — MTDS ripple

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

- [ ] 1. [REVIEW] P1. Confirm with whoever landed the UAC `canonical_id_builder` colon-strictness change (or via
      `git log`/`git blame` on `unified_api_contracts/internal/reference/canonical_id_builder.py`) whether MTDS
      call-site updates were intended to land in the SAME wave — if a companion MTDS fix is already in flight,
      cross-link it here instead of duplicating.
- [ ] 2. [DATA] P1. Fix `market_tick_data_service/market_interface/adapters/defi/canonical_write.py::write_defi_rows`
      (the `WETH:USDC` POOL case) — resolve the symbol against the DeFi pool catalogue/wire-map before calling
      `build_instrument_id`, or route genuinely-unresolvable pool symbols through
      `unified_api_contracts.canonical.quarantine` per the new UAC contract.
- [ ] 3. [DATA] P1. Fix
      `market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py::     derive_row_instrument_id`'s
      disabled-by-default fallback (the `ADAF0:USTF0` case) the same way — either resolve via the wire-map first or
      quarantine.
- [ ] 4. [REVIEW] P2. Re-check `test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment` —
      it fails on a DIFFERENT, downstream defi-filename-canonical-stem check once the `build_instrument_id` call no
      longer silently passes through; confirm whether this is the SAME fix as todo 2 or a separate defi-oracle-price
      naming gap.
- [ ] 5. [REVIEW] P2. Once 2-4 ship, re-run MTDS's full `quality-gates.sh` to confirm this ripple is the only blocker
      (no other UAC-contract-change fallout) before the NEXT agent tries to quickmerge into MTDS.
