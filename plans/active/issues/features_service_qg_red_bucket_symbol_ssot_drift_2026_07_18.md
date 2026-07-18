---
doc_type: issue
title:
  features-service quality-gates.sh RED — bucket-naming SSOT + tradfi symbol-suffix test drift blocks unrelated ships
summary:
  Dispatched to the features-sports manifest-aware-prune P2 todo
  (api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md); full quality-gates.sh run is RED
  with 10 pre-existing failures, verified byte-identical on a clean tree with my diff stashed. Two distinct, unrelated
  defect clusters — a stale bucket-naming assertion drift left behind by d98a1fdc (2026-07-17), and a tradfi symbol
  "-USD" suffix drift in cross_instrument — block EVERY ship from this repo under the green-tree HARD RULE, not just
  mine.
status: resolved
nature: issue
asset_group: [meta]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, quality-gates, bucket-naming, ssot, repo-blocker, qg-red]
related: [plans/active/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md]
created: "2026-07-18"
parent_epic: features_and_ml_master
priority: P1
assigned_vm: planning
source: [api_football_backfill_chronological_scan_never_reaches_pending_tail-004]
resolved_by:
  slot-8 (both todos verify-only closed 2026-07-18 — fix already shipped by unrelated Fold-A + UAC contract commits, see
  todo evidence)
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to the features-sports manifest-aware per-day-loop P2 todo (unrelated to this finding). Ran the full
`bash scripts/quality-gates.sh` in `features-service` after implementing my fix; it failed with 10 test failures across
4 unrelated feature families (cross_instrument, delta_one, volatility, top-level `tests/unit/test_config.py`) — none in
`sports/`. Verified pre-existing per RULES.md § 4b: `git stash push --include-untracked`, re-ran the exact 10 tests on
the clean tree at LDR HEAD (`2f187a4e`) — byte-identical failures — then `git stash pop` to restore my diff. This means
quality-gates.sh has been RED on `live-defi-rollout` HEAD since before my dispatch, blocking the `quickmerge --agent`
sentinel (`.qg_last_passed_sha`) for EVERY task in this repo, not just mine.

Two distinct, unrelated defect clusters:

**Cluster A — bucket-naming SSOT assertion drift (6 failures).** Traced to `d98a1fdc` ("fix(buckets): asset-group parity
— CLI choices are the SSOT; retire 3 dead OUTPUT_BUCKETS maps", 2026-07-17T15:28:23+01:00, already 17 commits behind
current HEAD). That commit deleted 3 hardcoded `OUTPUT_BUCKETS`/`_TEST` `ClassVar` maps from
`delta_one`/`onchain`/`volatility` dependency checkers and switched them to delegate to
`VolatilityServiceConfig`/`resolve_bucket()` (the real cloud-providers.yaml SSOT — what production writers already
used). The corresponding test assertions were never updated to match the new resolver output, so they still assert the
OLD per-family bucket shape (`features-volatility-cefi-{pid}`, `features-delta-one-cefi-{pid}`) while the SSOT resolver
now returns a flat/env-tiered shape (`features-cefi-prd-{pid}`) — a real shape change, not a typo:

- `tests/delta_one/unit/test_persistence_event_details.py::TestSinkBucketResolution::test_falls_back_to_canonical_bucket_when_env_unset`
  — expects `features-delta-one-cefi-test-project`, got `features-cefi-prd-test-project`.
- `tests/unit/test_config.py::test_get_output_bucket_falls_back_to_ssot` — expects `"features-delta-one" in resolved`,
  got `features-cefi-prd-test-project` (no `features-delta-one` substring at all).
- `tests/volatility/unit/test_dependency_config_models.py::TestDependencyCheckerDataStructures::test_output_bucket_ignores_test_mode`
  — expects `.startswith("features-volatility-cefi-")`, got `features-cefi-prd-test-project`.
- `tests/volatility/unit/test_dependency_config_models.py::TestDependencyCheckerDataStructures::test_output_bucket_resolves_canonical_shape_via_ssot`
  — expects `.startswith("features-volatility-")`, got `features-tradfi-prd-test-project`.
- `tests/volatility/unit/test_dependency_config_models.py::TestDependencyCheckerDataStructures::test_output_bucket_defi_raises_no_defi_options`
  — expects `BucketNamingError` to raise for DEFI (per the operator's no-DeFi-volatility ruling cited in d98a1fdc); it
  no longer raises — the DEFI-rejection path itself may have regressed, not just a naming-shape mismatch.
- `tests/volatility/unit/test_io_loader_writer.py::TestVolatilityWriter::test_bucket_resolves_via_config_get_output_bucket_not_hardcoded`
  — expects `features-volatility-cefi-test-project`, got `features-cefi-prd-test-project`.

Whether the fix is "update the 6 tests to the new flat SSOT shape" or "the flat shape is itself wrong and the resolver
regressed the per-family segment" is a real judgment call I did NOT make — see Recommended decision.

**Cluster B — tradfi symbol "-USD" suffix drift (4 failures), unrelated to Cluster A.**
`tests/cross_instrument/unit/test_paired_dispatch.py::TestTradfiVenues` (`test_nasdaq_etf`, `test_nyse_etf`,
`test_ice_commodity_spot`, `test_nymex_commodity_spot`) all expect a bare symbol (e.g. `"NASDAQ:ETF:IBIT"`) but the
paired-dispatch resolver now emits a `-USD` quote suffix (`"NASDAQ:ETF:IBIT-USD"`) for every tradfi venue case. Some
upstream symbol-construction change (not identified in this dispatch — out of scope for my craft/task) started appending
the quote currency to tradfi symbols; either the tests are stale (symbol SHOULD carry `-USD` now) or the symbol builder
over-appended it. Not investigated further — outside this dispatch's scope (data_engineering craft, sports task).

## Why it matters

- **Blocks every ship from features-service**, not just mine — `quickmerge --agent` refuses whenever the
  `.qg_last_passed_sha` sentinel doesn't match HEAD, and quality-gates.sh cannot write a fresh sentinel while these 10
  failures stand. My own manifest-aware-prune fix (features-sports P2) is fully green in isolation (9/9 new tests + full
  `tests/sports/` suite pass) but cannot ship via the mandated quickmerge flow until this repo goes green.
- **Cluster A is bucket-naming correctness** — workspace HARD RULE territory
  (`codex/05-infrastructure/gcs-object-operations.md`, bucket-name SSOT). If the flat shape is the intended
  post-d98a1fdc behavior, 6 stale tests are silently vouching for a bucket name that hasn't existed since 2026-07-17 — a
  false-green risk the moment someone "fixes" the tests by weakening the assertion instead of confirming the real SSOT
  shape. If instead the resolver regressed (dropped the per-family segment), production writes may be landing in the
  WRONG bucket right now.

## Recommended decision

1. A backend/config-SSOT-craft agent should read `d98a1fdc` in full plus the current `resolve_bucket()` /
   `cloud-providers.yaml` SSOT to determine the CORRECT current bucket-naming shape for delta_one/volatility/onchain,
   then either (a) update the 6 Cluster-A tests to assert the correct current shape, or (b) if the flat shape is itself
   a regression, fix the resolver and confirm production buckets. This is NOT a test-only fix without that
   determination.
2. A separate agent should trace the Cluster-B `-USD` suffix change (likely a recent tradfi symbol-normalization commit)
   and determine whether the 4 `test_paired_dispatch.py::TestTradfiVenues` tests are stale or the symbol builder
   regressed.
3. Once both clusters are green, quality-gates.sh writes a fresh sentinel and every blocked ship (mine included) resumes
   via the normal quickmerge flow.

- [x] ✅ [BACKEND] P1. Determine the correct post-d98a1fdc bucket-naming shape for delta_one/volatility — **RESOLVED, no
      code change needed — features-service@1368732a.** Root cause was NOT d98a1fdc itself: an independent, much larger,
      operator-sanctioned migration (**Fold A**, `plans/active/bucket_fold_features_2026_07_17.md`) landed on
      `live-defi-rollout` the same day (2026-07-18) and deliberately retired the per-family
      `features-volatility-cefi-{pid}` shape in favor of the flat per-asset-group `features-{ag}-{env}-{pid}` shape —
      confirmed the CORRECT current SSOT (`cloud-providers.yaml` folded `features:` key +
      `VolatilityServiceConfig.get_output_bucket()` → `resolve_bucket(kind="features", ...)`). That same commit
      (features-service@1368732a) already updated all 6 Cluster-A tests to assert the new flat shape, INCLUDING
      `test_output_bucket_defi_raises_no_defi_options` — it was renamed to
      `test_output_bucket_defi_resolves_folded_features_bucket` because DEFI-rejection is now intentionally enforced at
      the CLI layer (`cli/main.py` asset_group_choices), not the bucket resolver, since the folded `features` yaml key
      legitimately carries a DEFI entry shared across families. Verified via a fresh full
      `bash scripts/quality-gates.sh` run on FF-pulled `live-defi-rollout` HEAD (`47acb31f`): **17682 passed, 0 failed,
      209 skipped** (sentinel written `47acb31f...`) — all 6 Cluster-A tests green, confirmed by direct inspection of
      their current assertions. My fresh-pull simply picked up the fix; I made no code edits. (repo: features-service)
- [x] ✅ [BACKEND] P1. Trace the tradfi `-USD` symbol-suffix drift in `TestTradfiVenues` — **RESOLVED, new correct
      behavior, not a regression — traced to UAC@33e3f369** ("fix(tradfi): extend `_build_tradfi_cash` -USD quote suffix
      to EQUITY/CURRENCY/ETF/BOND/COMMODITY", 2026-07-18T16:43:34+01:00). This is an operator-ratified contract change
      (`plans/active/tradfi_consolidated_closeout_2026_07_18.md` line 358: "Equity id = `-USD` on ALL FOUR surfaces" —
      target `NASDAQ:EQUITY:AAPL-USD`) that extends the existing INDEX-only `-USD` suffix convention (operator-ratified
      2026-06-11, commit `32d0d40`) to every other TradFi cash type, so the pattern is uniform regardless of asset class
      (CDS excluded — no base/quote dimension). `_TRADFI_CASH_QUOTE_SUFFIXED_TYPES` in
      `unified_api_contracts/internal/reference/canonical_id_builder.py` now includes EQUITY/CURRENCY/ETF/BOND/
      COMMODITY alongside INDEX. features-service@1368732a's QG run caught this same-day UAC contract drift and updated
      all 4 `TestTradfiVenues` assertions to the new `-USD`-suffixed form as a byproduct of the Fold-A ship. Verified
      via the same full `bash scripts/quality-gates.sh` run cited on the sibling todo (LDR HEAD `47acb31f`): **17682
      passed, 0 failed** — all 4 tests green, confirmed by direct inspection of their current assertions
      (`tests/cross_instrument/unit/test_paired_dispatch.py::TestTradfiVenues`). No code edits needed. (repo:
      features-service)

## Evidence

- Full run: `bash scripts/quality-gates.sh` in `.tabs/3/features-service` — `10 failed, 17681 passed, 209 skipped` in
  207.59s.
- Pre-existing verification: `git stash push --include-untracked` (removed my sports-only diff) → re-ran the exact 10
  failing test IDs on clean HEAD `2f187a4e` → byte-identical 10 failures → `git stash pop` (restored my diff).
- `git log --oneline d98a1fdc..HEAD | wc -l` → 17 (the suspected regression commit is well upstream of current HEAD, not
  a same-session in-flight change).
- My own scope (features-sports P2, `_pending_dates.py` + `main.py`): `tests/sports/` full suite green in isolation
  (background run, exit 0); `tests/sports/unit/test_pending_dates.py` + `tests/sports/unit/test_main_batch_prune.py` (9
  new tests) green; `basedpyright` + `ruff check` + `ruff format --check` clean on all touched/new files.
