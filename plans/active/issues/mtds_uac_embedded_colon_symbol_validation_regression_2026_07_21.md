---
doc_type: issue
title: >-
  UAC uac@502ef57e's new "fail-loud on embedded ':' in build_instrument_id" broke 3 pre-existing MTDS/cefi tests that
  use colon-bearing symbols, blocking the full quality-gates.sh for every MTDS change right now
summary: >-
  unified-api-contracts@502ef57e ("feat(canonical): widen ID-FORM oracle to defi ... + fail-loud on embedded ':' in
  build_instrument_id") is an ALREADY-COMMITTED change (not dirty WIP) that raises ValueError whenever a symbol passed
  to build_instrument_id contains a ':' character. At least 3 MTDS unit tests exercise real venue symbol forms that
  legitimately contain ':' (Bitfinex-style "ADAF0:USTF0" perpetual symbols; a WETH:USDC leaf-byte-match fixture; a
  slash-id parity test) and now fail this new validation. Reproduced via `bash scripts/quality-gates.sh` on MTDS with a
  clean run (no relation to any DeFi lending-writer change); this is a genuine, unrelated, cross-repo test-breaking
  regression from an already-landed UAC commit — not caused by any in-flight MTDS work. It currently fails `bash
  scripts/quality-gates.sh` for EVERY MTDS change, blocking unrelated ships (same class of problem as
  `mtds_rule11_shard_count_stale_baseline_2026_07_21.md`, now resolved).
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [test-baseline-drift, quality-gates-blocker, cefi, canonical-id, cross-repo]
related:
  [
    /plans/archive/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md,
    /plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "hit while shipping defi_lending_writer_retire_prerequisite_2026_07_20 (todos 2-5/9/13) — pure MTDS DeFi lending
    handler changes, unrelated to CeFi/canonical-id-builder; blocked the full-tree quality-gates.sh for that commit",
  ]
resolved_by: "slot-7 (data_engineering), 2026-07-26 — resolved via the sibling doc's todos, see below"
locked_by:
---

# UAC's new embedded-`:` `build_instrument_id` validation broke 3 pre-existing MTDS/cefi tests

> **Duplicate-discovery note (added 2026-07-25, /plan-reconcile apply pass):** this is the SAME regression (same UAC
> commit, same 3 failing tests) independently discovered and written up the same day as
> [`uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`](/plans/active/issues/uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md),
> which carries the actionable, tracked-todo version (5 open todos vs this doc's 0 — this one is narrative-only). Track
> the fix there to avoid duplicated/uncoordinated work; this doc stays open as the reproduction record until that one
> resolves.

## Reproduction

```
cd market-tick-data-service && bash scripts/quality-gates.sh --no-fix
```

Fails with 3 failures, all the SAME root cause:

```
FAILED tests/unit/test_canonical_stem_live_batch_parity.py::test_slash_id_never_forges_a_path_segment
FAILED tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py::TestLeafByteMatchWithR1::test_decoded_leaf_equals_r1_forward_writer_leaf[WETH:USDC]
FAILED tests/market_interface/adapters/cefi/test_catalog_decompose_all_venues.py::test_disabled_by_default_output_is_byte_identical[BITFINEX-FUTURES-PERPETUAL-ADAF0:USTF0-BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0]
```

Sample error:

```
ValueError: build_instrument_id: symbol 'ADAF0:USTF0' for instrument_type=PERPETUAL carries an embedded ':' — the
canonical id's own VENUE:TYPE:SYMBOL delimiter. ... resolve the symbol against the catalogue/wire-map before calling
this builder, or route a genuinely-unresolvable instrument through the UAC quarantine model
(unified_api_contracts.canonical.quarantine) instead of building a malformed double-wrapped id.
```

**Verified this is an already-committed change, not dirty WIP**:
`git log --oneline -3 -- unified_api_contracts/internal/reference/canonical_id_builder.py` in the
`unified-api-contracts` checkout shows
`502ef57e feat(canonical): widen ID-FORM oracle to defi (VENUE-CHAIN:TYPE:SYMBOL) + fail-loud on embedded ':' in build_instrument_id`
as the tip commit for that file, and `git status --porcelain` shows NO local modifications to it. So this is real,
committed, cross-repo behavior — MTDS picks it up immediately via its local/editable `unified-api-contracts` dependency,
with no MTDS-side commit needed to trigger it.

## Impact

Same class as `mtds_rule11_shard_count_stale_baseline_2026_07_21.md`: a hard-gate blocker in `quality-gates.sh` for
**every** MTDS commit right now, regardless of what the commit actually touches — confirmed while shipping a completely
unrelated DeFi-lending-handler change (`defi_lending_writer_retire_prerequisite_2026_07_20`).

## Likely root cause / fix directions (not diagnosed to a terminal answer — flagging, not fixing, per scope)

Bitfinex's native symbol form for some perpetual/futures instruments legitimately contains a colon (e.g. `ADAF0:USTF0`).
`502ef57e`'s new validator treats ANY embedded `:` as malformed, which is correct for the general case (colon is the
canonical id's own delimiter) but did not account for this pre-existing venue-native form. Two directions, not
adjudicated here:

1. The Bitfinex adapter/catalog-decompose path should sanitize/remap this symbol form BEFORE calling
   `build_instrument_id` (e.g. via the UAC quarantine model the new error message itself points to), OR
2. The validator needs a documented, narrow allowlist/escape for this one legitimate venue-native colon form if
   quarantine-routing changes MTDS's on-disk id format for already-captured Bitfinex data (a canonicalisation-breaking
   change that would need its own migration).

Whichever direction is right, it is NOT a DeFi-lending-writer concern and is out of
`defi_lending_writer_retire_prerequisite_2026_07_20`'s scope — flagged here per workspace findings-triage ("outside
every plan → `plans/active/issues/`").

## Resolved 2026-07-26 (slot-7, `data_engineering`)

Per this doc's own duplicate-discovery note, the actionable fix landed on the sibling doc
(`uac_build_instrument_id_colon_strictness_mtds_ripple_2026_07_21.md`, all 5 todos now closed). Full
`market-tick-data-service` `quality-gates.sh` confirmed green, sentinel matching HEAD (`f6ea0010`).
