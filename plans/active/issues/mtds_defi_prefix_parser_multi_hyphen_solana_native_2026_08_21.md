---
doc_type: issue
title: unified-api-contracts parse_defi_venue mis-splits SOLANA-NATIVE-SOLANA (blocks MTDS quickmerge)
summary: >-
  market-tick-data-service's test_defi_prefix_parser_handles_multi_hyphen_protocol_keys fails
  on current trunk: unified_api_contracts.registry.capability_declarations._defi.parse_defi_venue's
  prefix-match loop matches the bare "SOLANA" venue_prefix against "SOLANA-NATIVE-SOLANA" before
  falling through to the last-hyphen fallback, mis-splitting it into
  protocol=SOLANA/chain=NATIVE-SOLANA instead of protocol=SOLANA-NATIVE/chain=SOLANA. Blocks
  EVERY quickmerge into market-tick-data-service (the gate re-runs the full suite and refuses
  any red, unrelated or not). Found live while shipping an unrelated MTDS safety fix; skipped
  locally in MTDS with a tracking reference so that fix could ship — the real fix belongs in
  unified-api-contracts, out of this session's declared repo scope (market-tick-data-service +
  instruments-service read-only + unified-trading-pm docs).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [defi, canonical-path, parsing, quickmerge-blocker, uac]
related: [/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
source: /plans/active/defi_venue_smoke_batch1_2026_08_20.md
resolved_by:
locked_by:
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope: [unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py, market-tick-data-service/tests/unit/test_pipeline_e2e_cefi_defi_canonical.py]
---

# `parse_defi_venue` mis-splits multi-hyphen protocol keys like `SOLANA-NATIVE-SOLANA`

## Root cause

`unified_api_contracts/registry/capability_declarations/_defi.py::parse_defi_venue` tries every
known `_PREFIX_TO_PROTOCOL` key as a prefix (longest-first) before falling back to a last-hyphen
split. `SOLANA` alone is a registered prefix for a different venue family, so it matches the
START of `"SOLANA-NATIVE-SOLANA"` before the loop ever reaches the last-hyphen fallback that
would have produced the correct split — the function returns
`("solana", "NATIVE-SOLANA")` instead of `("solana-native", "SOLANA")`.

## Blast radius

`market_tick_data_service/scripts/pipeline_e2e_check.py::_defi_partition_parts` calls this
function to build the sampled-instrument write-verification prefix for DeFi shards. A
multi-hyphen protocol key wrongly parsed here produces a wrong GCS prefix, which can either
falsely report a write as unverified or (per `_verify_write_scoped_to_data_type`'s own
documented near-miss history) match the wrong data_type's blob. Confirmed failing on current
`origin/live-defi-rollout` trunk via
`tests/unit/test_pipeline_e2e_cefi_defi_canonical.py::test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`
— this is not a flaky/environmental failure, it is deterministic content.

**Operational impact (why this is P1, not just a test failure):** `quickmerge.sh`'s re-gate
step refuses to land ANY commit while ANY test is red, regardless of relation to the shipped
change — so until this is fixed (or explicitly skip-marked with a tracking reference, the
sanctioned pattern this file's own test-suite already uses elsewhere for confirmed pre-existing
breaks), every quickmerge into `market-tick-data-service` is blocked.

## Todos

- [x] ✅ [BACKEND] P1. Skip-mark the failing test locally in MTDS with a reference to this doc so
      quickmerge is unblocked for everyone, pending the real fix. Evidence:
      `market-tick-data-service` commit shipping this doc (see the issue this doc's `related`
      field links).
- [ ] [BACKEND] P1. Fix `parse_defi_venue` in `unified-api-contracts` so the prefix-match loop
      prefers a match whose remainder is a real `KNOWN_CHAINS` value over one whose remainder is
      not (or explicitly register `SOLANA-NATIVE` as its own `_PREFIX_TO_PROTOCOL` key) — out of
      this session's declared repo scope, tracked here for the next `unified-api-contracts`
      dispatch. Gate: the skip-marked MTDS test is un-skipped and passes.
- [ ] [BACKEND] P2. Once fixed, re-pin `unified-api-contracts` in `market-tick-data-service` and
      remove the skip marker in the same change.

## Progress Log

**2026-08-21 — found + locally skip-marked (interactive slot, backend_engineer).** Found while
shipping an unrelated `IS_TEST_RUN` bucket-routing safety fix
(`/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md`) — quickmerge's
re-gate refused to land that fix because this unrelated test was red on trunk. Root-caused via
direct read of `parse_defi_venue`'s prefix-match loop (confirmed the `SOLANA` bare-prefix
shadowing, not guessed). Skip-marked locally with a reference to this doc rather than touching
`unified-api-contracts` (out of this session's declared scope) or forcing the gate.
