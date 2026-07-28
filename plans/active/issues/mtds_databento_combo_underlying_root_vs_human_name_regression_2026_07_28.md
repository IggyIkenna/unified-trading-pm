---
doc_type: issue
title:
  market-tick-data-service `test_databento_enrichment_combo_underlying.py` fails on current `live-defi-rollout` HEAD —
  `databento_enrichment.py` resolves COMBO underlyings to raw exchange root codes ("CL-BZ", "ZN") while the test (and
  presumably downstream consumers) expect human product names ("WTI-BZ", "UST-10Y")
summary: >-
  Discovered 2026-07-28 while shipping an unrelated fleet-wide `staging-lock-check.yml` template sync (self-hosted
  runner migration, `gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`) across all `ldr_main` repos —
  market-tick-data-service's `quality-gates.sh` re-gated against current HEAD (a peer's commit moved HEAD, invalidating
  the sentinel) and hit 3 REAL, reproducible-in-isolation failures in
  `tests/unit/test_databento_enrichment_combo_underlying.py`: `test_named_spread_combo_kept_with_resolved_underlying`
  (expected `'WTI-BZ'`, got `'CL-BZ'`), `test_root_qualified_ud_combo_recovers_real_root` (expected `'UST-10Y'`, got
  `'ZN'`), `test_mixed_batch_drops_only_opaque_combo` (same root-vs-human-name mismatch on the resulting set).
  Confirmed NOT a flake (reproduces deterministically via `.venv/bin/python -m pytest
  tests/unit/test_databento_enrichment_combo_underlying.py -p no:xdist -v`) and NOT caused by the staging-lock-check.yml
  change (a workflows-only YAML diff, unrelated to any Python enrichment code). The test + its implementation
  (`market_tick_data_service/market_interface/adapters/tradfi/databento_enrichment.py`) were both last touched
  together by `f645ea02` ("fix: CME combo underlying-garbage — databento_enrichment drops opaque-UD combos..."), which
  predates the HEAD-moving peer commit that surfaced this failure — so either that commit (or something it pulled in
  via merge) regressed the root->human-name resolution, or the two were already silently out of sync and this is the
  first re-gate to actually exercise the assertion since. This is the SAME naming-convention class as
  `tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md` (root codes like "CL"/"ZN" vs
  human/product names like "WTI"/"UST-10Y" for tradfi COMBO underlyings) but a DIFFERENT specific code path
  (MTDS's own `databento_enrichment.py` COMBO-resolution logic, not instruments-service's catalog/manifest rollup) —
  filed separately since the fix surface is a different repo/module, not to be folded into that doc's resolution.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, databento, combo, underlying-naming, regression, quality-gates, mtds]
related:
  [
    /plans/active/issues/tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md,
    /plans/active/issues/cme_combo_underlying_extraction_garbage_2026_07_19.md,
    /plans/active/issues/gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: infrastructure_master
source:
  "slot-15, discovered while shipping the staging-lock-check.yml fleet template sync — market-tick-data-service's QG
  re-gate hit a real, reproducible, unrelated test failure blocking the push"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# market-tick-data-service COMBO underlying resolves to root code, not human name — test regression

## What I found

1. `tests/unit/test_databento_enrichment_combo_underlying.py` on current `live-defi-rollout` HEAD fails 3/4 tests, all
   with the same shape: the code returns a raw exchange root code (`CL`, `ZN`) where the test expects the human/product
   name (`WTI`, `UST-10Y`) as part of the resolved combo underlying (e.g. `'CL-BZ'` vs expected `'WTI-BZ'`).
2. Reproduces deterministically in isolation (`-p no:xdist`), so this is not resource-contention flakiness (unlike the
   pytest-xdist `INTERNALERROR: Unexpectedly no active workers available` seen transiently elsewhere on this same
   heavily-loaded host during this session).
3. `git log` shows the test file and `databento_enrichment.py` were last touched together by `f645ea02` ("fix: CME
   combo underlying-garbage..."), predating the commit that moved this repo's `live-defi-rollout` HEAD during this
   session (surfacing the failure via quickmerge's sentinel re-gate). Not yet root-caused which specific change broke
   the mapping, or whether it was already broken and simply unexercised since `f645ea02`.

## Why it matters

The G1-ENUM present-set rollup work (`tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md`)
already found the SAME root-code-vs-human-name convention mismatch on the instruments-service/manifest side; this is
the same class of bug but in MTDS's own enrichment write path — worth fixing together or at least by the same owner,
since both trace back to "what is the canonical underlying-naming convention for a TradFi COMBO", and until resolved
this repo's `quality-gates.sh` is red on `live-defi-rollout` HEAD for anyone whose sentinel needs a re-gate.

## Recommended decision

- [x] [BACKEND] P2. ✅ — market-tick-data-service@4fdbcb0d ("fix(tests): update combo-underlying test assertions to
      match UAC short-root convention"), shipped by another agent within the hour this doc was filed. Confirms the
      hypothesis above: the root-code output (`CL`, `ZN`) is the now-intended UAC short-root convention, and the test
      was stale — not a `databento_enrichment.py` regression. `quality-gates.sh` is green on
      `market-tick-data-service`'s `live-defi-rollout` HEAD again.

## Codex SSOTs

- `/codex/02-data/tradfi-databento-sourcing-ssot.md`
