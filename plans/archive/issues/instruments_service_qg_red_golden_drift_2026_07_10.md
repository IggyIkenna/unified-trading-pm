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
status: resolved
nature: notes
asset_group: [cefi, defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [honest-coverage, golden-fixture, layer1-denominator, qg-red, cross-repo, coinbase-cde, defi-lending]
related: [/plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md, /codex/02-data/honest-coverage-model.md]
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
resolved_by: instruments-service@aa897b08, instruments-service@7048ae7e, unified-api-contracts@0ab1074a
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
      slot 3's plan annotation is imminent — it landed for real (`unified-api-contracts@1cafb3c5` registers
      COINBASE-CDE + declares OKX-SPOT its own cefi venue "Option A, 2026-07-10 operator decision"; `f0032d17` adds
      DERIBIT-COMBO test coverage). A concurrent commit (`instruments-service@53b1247a`) regenerated `cefi.json` to 80
      tuples against UAC state that still carried the dual-registration side-effect described below — that WAS the
      "launder the phantom bare-venue tuples back in" anti-pattern the fixture's own docstring warns against, not the
      correct final state. Completed Option A instead of accepting the dual-registration: removed the now-redundant
      `SPOT_PAIR` from bare `OKX`/`BYBIT` in UAC's `INSTRUMENT_TYPES_BY_VENUE` (`unified-api-contracts@0ab1074a`) since
      `OKX-SPOT`/`BYBIT-SPOT` now carry that capability as their own distinct venues, and removed `"OKX-SPOT": "OKX"`
      from instruments-service's `_CEFI_VENUE_FOLD` (`instruments-service@c0f5529c`) so `OKX-SPOT` compares directly
      against its own EXPECTED entry instead of folding into bare OKX. Regenerated `cefi.json` back to the correct 76
      tuples (`instruments-service@aa897b08`) — no dual registration, no fold-alignment collapse, item 2 below resolved
      as a side effect (verified `test_missing_instrument_type_column_yields_empty_enumerated` passes clean).
      `quality-gates.sh`: ALL PASSED on both repos. (repo: instruments-service, unified-api-contracts)
- [x] [CODE] P2. ✅ Resolved as a side effect of item 1's Option-A completion above — with the bare-OKX/BYBIT
      `SPOT_PAIR` dual-registration removed entirely (not just aligned-around), there are no more collapsing fold pairs,
      so raw EXPECTED and aligned EXPECTED no longer diverge.
      `test_missing_instrument_type_column_yields_empty_enumerated` passes clean at `instruments-service@aa897b08`. No
      separate test/behavior change needed. (repo: instruments-service) **Addendum (slot-3, verifying this item):**
      confirmed passing independently; also caught + fixed a residual STEP 5.101 empty-string-fallback ratchet
      regression surfaced by the same fast-moving window — a concurrent commit had annotated 4 of 5 needed
      `# noqa: qg-empty-fallback` sites in `reconcile_phantom_manifest_rows_all.py` but missed line 237 (`raw_venue`),
      leaving the ratchet 1-over baseline (369>368). Fixed + shipped `instruments-service@7048ae7e`, `quality-gates.sh`
      ALL PASSED. Also independently re-derived the same TID251/cefi-golden-drift diagnosis as
      `instruments-service@aa897b08`/`23d53f69` while investigating — those landed first, kept as-is via conflict
      resolution rather than duplicating. Baseline ratcheted down (`no_empty_string_fallback_baseline.yaml`
      instruments-service: 369→368) same commit as this plan flip. (repo: instruments-service, unified-trading-pm)
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
- [x] [DESIGN] P3. ✅ Decision: YES — added the assertion. Confirmed `unified-api-contracts` and
      `unified-trading-library` are both **editable path-dependencies** (`instruments-service/pyproject.toml`
      `tool.uv.sources` → `../unified-api-contracts`, `../unified-trading-library`), so `build_expected()` reads
      whatever is on disk in the sibling clones at import time — uncommitted local state included. This is exactly the
      mechanism behind `94512ec3`'s phantom-tuple golden. Implemented `instruments-service@23d53f69`: new
      `scripts/regenerate_expected_universe_golden.py` runs `git -C <path> status --porcelain` against both path-deps
      and refuses to write the fixture (loud `SystemExit` listing the dirty files) unless clean or `--allow-dirty` is
      passed explicitly; the test docstring's regeneration recipe now points at this script instead of the raw inline
      `python -c` one-liner. Verified both the clean-pass and dirty-refuse paths locally before shipping.
      `quality-gates.sh`: ALL PASSED (`.qg_last_passed_sha=23d53f69660b3b9fc8b7e1b8c0619f614fbdd0e1` == HEAD). (repo:
      instruments-service)
