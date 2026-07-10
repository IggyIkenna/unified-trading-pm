---
doc_type: issue
title:
  "instruments-service QG is red at LDR HEAD (3 pre-existing failures) — cefi/defi golden fixtures + a DEFI producer
  drift-guard are stale relative to two unrelated in-flight UAC changes"
summary: |
  `bash scripts/quality-gates.sh` fails on a completely clean instruments-service checkout at LDR HEAD
  (`94512ec3 feat(reference-data): add COINBASE-CDE adapter`), with zero relation to any COINBASE-migration work.
  3 failures, byte-identical on a clean stash-reset tree: (1)
  `test_expected_universe_golden.py::test_expected_matches_golden[cefi]` — the checked-in `cefi.json` golden (from
  commit `94512ec3` itself) expects `COINBASE-CDE`/`DERIBIT-COMBO`/`OKX-SPOT` capability cells that do NOT exist in
  the actual UAC state at LDR HEAD (`unified-api-contracts@42270f63`, verified clean/fully-synced, no local dirt);
  (2) `test_expected_matches_golden[defi]` and (3)
  `TestVenueProducerUACInvariant::test_defi_set_equals_uac_denominator_drift_guard` — UAC commit
  `unified-api-contracts@42ce2de3 fix(defi): ... wire VENUS/BENQI/RADIANT/EULER_V2` widened
  `VENUES_BY_ASSET_GROUP["defi"]` without instruments-service's own DeFi producer/golden being updated to match.
  Independently corroborated by a concurrent slot (slot 3, `ikennaigboaka [slot-3·laptop]`) working the same
  `coinbase_bare_name_migration_2026_07_06.md` plan, who hit and documented the identical 3 (of their reported 5)
  failures as "pre-existing/unrelated" in the plan's S2 section 2026-07-10 12:56 UTC — their own hypothesis is that
  `94512ec3`'s golden was regenerated against a dirty, not-yet-pushed local UAC state (the in-flight OKX-SPOT
  venue-registration work) rather than what's actually on LDR. This blocks EVERY instruments-service QG run
  workspace-wide until resolved, independent of the COINBASE work.
status: open
nature: notes
asset_group: [cefi, defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, golden-fixture, layer1-denominator, qg-red, cross-repo, coinbase-cde, defi-lending]
related: [coinbase_bare_name_migration_2026_07_06.md, ../../codex/02-data/honest-coverage-model.md]
created: 2026-07-10
last_updated: 2026-07-10
parent_epic: instruments_master
priority: P1
source:
  orchestrator task `coinbase_bare_name_migration-002` (slot 9, data_engineering) — discovered while running `bash
  scripts/quality-gates.sh` for an unrelated COINBASE elif-branch deletion; corroborated by slot 3's plan annotation on
  the same file at 2026-07-10 12:56 UTC
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
audited_scope: single-repo-qg-run
---

# instruments-service QG red at LDR HEAD — golden fixtures stale vs. two unrelated in-flight UAC changes

## What I found

Running the full instruments-service `bash scripts/quality-gates.sh` (real exit code, not piped through `tail` — first
attempt mis-captured `tail`'s exit code as 0; re-ran writing to a file and checking `$?` directly, confirmed exit 1)
fails 3 tests on a `git stash`-clean tree at LDR HEAD `94512ec3`:

1. `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]` —
   golden has 5 phantom tuples (`COINBASE-CDE/future/trades`, `COINBASE-FUTURES/spot_pair/trades`,
   `DERIBIT-COMBO/options_chain/trades`, `OKX-SPOT/spot_pair/book_snapshot_5`, `OKX-SPOT/spot_pair/trades`) that
   `build_expected('cefi')` does not produce against the real, fully-synced `unified-api-contracts@42270f63` (I verified
   my UAC clone has zero local diff vs. `origin/live-defi-rollout` before concluding this). The golden is also MISSING
   the real current bare `OKX`/`BYBIT` `spot_pair` cells that DO still exist in UAC today.
2. `test_expected_matches_golden[defi]` — golden is missing 15 tuples UAC commit `unified-api-contracts@42ce2de3` added
   (VENUS-BSC/VENUS-ETHEREUM/BENQI-AVALANCHE/RADIANT-*/EULER_V2-ETHEREUM lending cells).
3. `TestVenueProducerUACInvariant::test_defi_set_equals_uac_denominator_drift_guard` — same root cause as #2:
   instruments-service's own DeFi producer set (`_build_defi_venues()`) hasn't been updated to match UAC's widened
   `VENUES_BY_ASSET_GROUP["defi"]` (7 venues: RADIANT-ARBITRUM/BENQI-AVALANCHE/VENUS-BSC/RADIANT-ETHEREUM/
   VENUS-ETHEREUM/RADIANT-BSC/EULER_V2-ETHEREUM).

None of these touch COINBASE or my `coinbase_bare_name_migration-002` (S2) diff — confirmed by running the identical QG
suite with my S2 changes stashed out entirely: byte-identical 3 failures, same test names.

Slot 3 independently hit and documented (in `coinbase_bare_name_migration_2026_07_06.md`'s S2 section, commit
`4f1ff7299`, 2026-07-10 12:56 UTC) a superset of this (5 failures on their host, 2 more from their own uncommitted local
WIP) with the same conclusion: pre-existing, unrelated to COINBASE, caused by other agents' in-flight work (OKX-SPOT
venue registration + DeFi capability-registry additions) landing UAC-side changes ahead of instruments-service's own
producer/golden updates.

## Why it matters

This is exactly the failure mode `test_expected_universe_golden.py`'s own docstring calls "the single most dangerous
failure mode of Honest Coverage v2" — a silently-wrong EXPECTED denominator. Right now it's LOUD (both goldens are red),
which is the test doing its job, but it means **every** instruments-service QG run is red workspace-wide until one of
the two root causes lands: (a) whatever landed the `94512ec3` CEFI golden either needs its real UAC prerequisite
(OKX-SPOT/DERIBIT-COMBO/COINBASE-CDE registration) to land for real, or the golden needs correcting back to match actual
LDR state; (b) instruments-service's DeFi producer/golden needs updating for the 7 new UAC lending venues (or an
explicit MVP-exclusion decision + a `_build_defi_venues()` filter update, mirroring the existing
`is_mvp()`/`_CEFI_SUB_VENUE_BASES` pattern).

## Recommended decision

- [x] [CODE] P1. ✅ Determine whether the real UAC OKX-SPOT/DERIBIT-COMBO/COINBASE-CDE registration work referenced by
      slot 3's plan annotation is imminent — instruments-service@2b0a-pending (this task's own S2 commit). It landed for
      real within the hour (UAC commits including
      `f0032d17 fix(defi,cefi): D10 defi lending capability entries +     DERIBIT-COMBO test coverage` and further
      OKX-SPOT/COINBASE-CDE registrations, confirmed via `unified_api_contracts.registry.market_data_categories` import
      — `build_expected('cefi')` now legitimately returns 80 tuples including COINBASE-CDE/DERIBIT-COMBO/OKX-SPOT).
      Regenerated `cefi.json` golden against the now-current UAC state (76→80 tuples) as part of
      `coinbase_bare_name_migration-002`; `test_expected_matches_golden[cefi]` passes clean. Bare `OKX`/`BYBIT`
      `spot_pair` still coexist alongside `OKX-SPOT`/`BYBIT-SPOT` in UAC (dual registration, transitional) — see the new
      item below for the fold-alignment side-effect this causes. (repo: instruments-service)
- [ ] [CODE] P2. New finding (surfaced while verifying the above):
      `tests/unit/scripts/test_check_enumeration_completeness.py::TestCompletenessMetrics::test_missing_instrument_type_column_yields_empty_enumerated`
      now fails — `len(result.missing_tuples) == 78` vs `len(expected) == 80`. Root cause: the S1 `_CEFI_VENUE_FOLD`
      alignment step collapses 2 tuples during fold (bare `OKX`+`OKX-SPOT` and bare `BYBIT`+`BYBIT-SPOT` pairs, both now
      dual-registered in UAC's cefi venue list, fold to the same aligned EXPECTED cell), so raw EXPECTED (80) and
      aligned EXPECTED (78) diverge — the test hardcodes an assumption that they're always equal. Confirmed
      pre-existing/unrelated to COINBASE on a clean stash-reset tree. Fix: either update the test to compare against the
      ALIGNED count (not raw `_build_expected_tuples`), or decide whether `_CEFI_VENUE_FOLD` should also fold bare
      `OKX`→`OKX-SPOT` and bare `BYBIT`→`BYBIT-SPOT` now that those venues are in the same dual-registration state
      COINBASE was in before S1. (repo: instruments-service)
- [x] [CODE] P1. ✅ Decide MVP scope for the 7 new UAC DeFi lending venues from `unified-api-contracts@42ce2de3`
      (VENUS-BSC/VENUS-ETHEREUM/BENQI-AVALANCHE/RADIANT-ARBITRUM/RADIANT-BSC/RADIANT-ETHEREUM/EULER_V2-ETHEREUM) —
      instruments-service@9b0c1095
      (`fix(defi): wire VENUS/BENQI/RADIANT/EULER_V2 orchestrator, fix Curve/Balancer     undercount`, landed by slot-3
      2026-07-10 12:57:31, already on LDR HEAD when this task was picked up) decided IN-SCOPE: added all 7 to
      `_STATIC_DEFI_VENUES` in `instruments_service/engine/orchestrator/defi.py` (the underlying adapters —
      venus.py/benqi.py/radiant.py/euler_v2.py — were already functional, just never requested by
      `_build_defi_venues()`) and regenerated the `defi.json` golden fixture. Verified on a clean LDR-HEAD checkout
      (`instruments-service@53367eba`): `test_expected_matches_golden[defi]` and
      `test_defi_set_equals_uac_denominator_drift_guard` both pass
      (`.venv/bin/python -m pytest     tests/unit/scripts/test_expected_universe_golden.py -k defi` → 2 passed;
      `tests/unit/test_orchestrator_helpers.py     -k drift_guard` → 1 passed). No further code change needed for this
      item. (repo: instruments-service)
- [ ] [DESIGN] P3. Consider whether golden-fixture regeneration commits should assert
      `git -C     <path-dep-repo> status --porcelain` is empty for every UAC/UTL path-dependency before writing the
      fixture — would have caught `94512ec3`'s dirty-local-UAC-state golden before it shipped. (repo:
      unified-trading-pm)
