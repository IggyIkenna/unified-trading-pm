---
doc_type: issue
title:
  Findings surfaced while empirically verifying the `smoke_matrix.py` -test- bucket routing fix — one severe unrelated
  CLI-breaking bug (multi_timeframe), stale smoke-harness verifier assumptions (calendar, delta_one), and two stale
  manifest consolidators (TRADFI, sports -test-)
summary: >-
  Fixing `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P0 (wiring `PROTOCOL_DATA_SINK_BUCKET*` into
  every `smoke_matrix.py`'s `_invoke_cli()`) required running all 8 families for real against live GCS to prove the fix.
  That exercise surfaced 4 distinct, pre-existing, unrelated bugs the fix itself does not touch: (1)
  `features_service.multi_timeframe`'s CLI cannot be invoked AT ALL — an `argparse` duplicate `--start-date`
  registration crashes even `--help` — this is a severe, standalone finding; (2) calendar's own `smoke_matrix.py`
  verifier (`_verify_gcs_parquet`/`_verify_test_manifest`) asserts a `feature_group="temporal"` path +
  `asset_group="CEFI"` manifest filter that never matches calendar's real (category-agnostic) write shape, so even a
  correctly-routed write can never PASS calendar's own harness; (3) delta_one's verifier prefix
  (`features/by_date/day=.../feature_group=.../`) doesn't match the real `OUTPUT_PATH_TEMPLATE`
  (`by_date/day=.../feature_group=.../timeframe=.../`, no `features/` prefix) — same class of bug; (4) two buckets'
  consolidated `availability_index` are stale/missing (`market-data-tick-tradfi-prd-...`, age 47,309s vs the 7,200s
  threshold; `features-sports-test-...`, no consolidated index has EVER been written), fail-closing dependency checks
  and skip-logic reads for those shards.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [features-service, e2e-testing]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    data-correctness,
    features,
    e2e-testing,
    smoke-matrix,
    multi-timeframe,
    cli-broken,
    manifest-consolidator,
    test-bucket-isolation,
  ]
related:
  [
    /plans/active/issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md,
    /plans/active/issues/features_service_catalogue_completeness_smoke_masking_findings_2026_08_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
source:
  "slot-12, data_engineering, discovered while empirically verifying
  features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md's P0 fix against live GCS, 2026-08-01"
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Smoke-matrix verification findings: mtf CLI broken, stale harness-verifier assumptions, stale consolidators

## What I found

Verifying `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P0 fix required running all 8
`e2e-testing/scripts/<family>/smoke_matrix.py` for real (non-dry-run) against live GCS (`central-element-323112`). The
routing fix itself is proven correct — full end-to-end writes landed at
`gs://features-calendar-test-central-element-323112/...` and `gs://features-defi-test-central-element-323112/...`, and a
real manifest write landed at `gs://features-cefi-test-central-element-323112/...` for delta_one — but the exercise also
surfaced 4 separate, pre-existing bugs unrelated to bucket routing:

### 1. `features_service.multi_timeframe` CLI is entirely non-functional (SEVERE)

```
$ python -m features_service.multi_timeframe --help
argparse.ArgumentError: argument --start-date: conflicting option string: --start-date
```

This is an `argparse` parser-construction bug (a `--start-date` flag registered twice) — it crashes during parser
_setup_, before any argument parsing happens, so **every** invocation of this CLI fails identically regardless of flags.
Confirmed via both a real `--operation compute` invocation and a bare `--help`. This means
`e2e-testing/scripts/multi_timeframe/smoke_matrix.py` has been unable to exercise this family's real compute path at all
— its own "3-step assertion contract" has been silently vacuous for however long this regression has existed, since the
harness's `_invoke_cli()` swallows the subprocess's non-zero exit as a plain `CLI rc=N` FAIL with no distinction from a
data-content failure.

### 2. calendar's `smoke_matrix.py` verifier can never PASS even with correct routing

With the P0 fix's routing confirmed correct (real writes now land at
`gs://features-calendar-test-central-element-323112/calendar/{time_features,economic_events,yield_curve,economic_results}/by_date/day=<D>/features.parquet`),
the harness's own verification still FAILs:

- `_verify_gcs_parquet` checks prefix `features/by_date/day=<D>/feature_group=temporal/` — "temporal" is not one of
  calendar's 4 real feature groups (`time_features`, `economic_events`, `yield_curve`, `economic_results`), and the real
  write path has no `features/` root segment or `feature_group=` directory at all — it's
  `calendar/<feature_group>/by_date/day=<D>/features.parquet`.
- `_verify_test_manifest` filters the manifest by `asset_group=CEFI` (or whatever `--asset-group` cell is under test) —
  but calendar is explicitly category-agnostic (single bucket, no per-asset_group split, per its own module docstring),
  so its real manifest rows likely carry a different/no asset_group value, and the filter never matches.

Net effect: calendar's smoke check has **never** been able to genuinely PASS its own 3-step contract — before this
session's fix, step 1 always silently landed on PROD (masking steps 2/3's own brokenness); now that step 1 is fixed,
steps 2/3's independent bugs are exposed for the first time.

### 3. delta_one's `smoke_matrix.py` verifier prefix doesn't match the real write path

`_verify_gcs_parquet`'s prefix is `features/by_date/day=<D>/feature_group=<G>/` (extra `features/` segment). The real
write path — confirmed via `features_service/delta_one/app/core/dependency_checker.py`'s own
`OUTPUT_PATH_TEMPLATE = "by_date/day={date}/feature_group={group}/timeframe={timeframe}/"` — has no `features/` prefix
segment and includes a `timeframe={timeframe}/` segment the verifier omits entirely. Same class of bug as finding 2,
independently confirmed via a second family.

**Not yet checked**: whether cross_instrument/onchain/sports/volatility's verifiers have the same class of prefix
mismatch — this session did not get a genuinely completed real run far enough to confirm any of their verifier prefixes
against actual write output (see "Why not fixed here" below for why).

### 4. Two buckets' consolidated `availability_index` are stale or missing

- `market-data-tick-tradfi-prd-central-element-323112`: consolidated index last updated 2026-07-31T18:29:55Z — 47,309s
  old at time of check, ~6.6x past the `MANIFEST_CONSOLIDATED_STALENESS_SEC=7200` threshold. Any dependency check or
  lookback read against this bucket fail-closes with `ManifestConsolidatorStaleError`
  (`Refusing to fall back to the per-VM shard merge`). Blocked delta_one/volatility TRADFI verification this session.
- `features-sports-test-central-element-323112`: **no consolidated `_index/availability_index.parquet` object exists at
  all** (`404`), while per-VM shard files apparently do (the same fail-closed guard fires: "stale or missing ... while
  per-VM shards exist"). This suggests the manifest consolidator job has never run against this specific `-test-` bucket
  — plausible if consolidator scheduling is keyed off a PROD-bucket registry that doesn't include the `-test-` siblings.

### 5. delta_one CEFI/technical_indicators: `perp_collapse` retains 0/215 instruments, and the resulting empty-write is REJECTED as unproven honest-absence

A real `features_service.delta_one --asset-group CEFI --feature-group technical_indicators --date 2026-07-28` run
(173/173 lookback-valid instruments, 215 post-universe-filter) logged:

```
INFO perp_collapse: retained 0/215 (bases=178; dropped non-rep-venue=1, no-rep=214, unparseable=0)
WARNING No instruments remain after MVP universe filter for group=technical_indicators asset_group=CEFI (started with 219)
WARNING empty_confirmed manifest write failed for technical_indicators date=2026-07-28: record_empty(reason=SOURCE_RETURNED_ZERO)
  requires FetchEvidence proving a clean 200+empty fetch ... This is most likely an auth/rate-limit/5xx/timeout/exception/
  missing-credential path masquerading as honest absence — call record_failed instead.
INFO Recorded record_failed manifest row for CEFI/technical_indicators on 2026-07-28 (error=orchestrator_returned_false)
```

`perp_collapse` (representative-venue-per-base selection) drops 214/215 instruments as "no-rep" — i.e. it found zero
instruments with a qualifying representative venue for CEFI on this date, which emptied the entire universe. The
service's own honest-absence guard correctly REFUSED to record this as `empty_confirmed` (no `FetchEvidence` proves this
is a genuine clean-zero rather than a masked failure), so it fell through to `record_failed` instead — the correct
conservative behavior per `/codex/02-data/honest-absence-downstream-handling.md`, but it means CEFI technical_indicators
is currently unable to produce EITHER a real feature write OR a confirmed-empty manifest row for at least this date. Not
root-caused this session (is `perp_collapse`'s representative-venue selection logic broken, or is CEFI's
representative-venue MTDS input genuinely missing/stale for 2026-07-28 specifically?) — that determination needs its own
investigation into `perp_collapse`'s upstream inputs before a fix is attempted.

### 6. `e2e-testing@04d261d`'s `TEST_BUCKET_TEMPLATE` fold broke 13 of features-service's OWN unit tests — CI-red for the whole repo (FIXED)

Discovered + fixed by slot-7 (2026-08-01) while shipping an unrelated task
(`basedpyright_extrapaths_pyproject_migration_findings_2026_08_01.md`'s features-service todo) —
`bash scripts/quality-gates.sh` failed with 13 pre-existing test failures, all `AssertionError`s in
`tests/<family>/unit/test_smoke_matrix.py::test_test_bucket_per_category`/`test_test_bucket_single` across
cross_instrument (3), delta_one (4), multi_timeframe (3), onchain (1), volatility (2). Each test dynamically loads its
family's `e2e-testing/scripts/<family>/smoke_matrix.py` and asserts `mod._test_bucket(pid, cat)`'s return value against
a hardcoded expected string — but those test files still hardcoded the PRE-Fold-A per-family bucket name (e.g.
`features-cross-instrument-cefi-test-p`) that finding P0's `e2e-testing@04d261d` correctly retired in favor of the
folded `features-{asset_group_lower}-test-{project_id}` shape (confirmed live-correct via `client.bucket(...).exists()`
per that todo's evidence). The e2e-testing SIDE of the fix (the template + `_test_bucket()` itself) was correct; only
features-service's own test-assertion literals were never updated to match, so `quality-gates.sh`/CI has been RED for
the entire repo since `04d261d` landed — confirmed pre-existing (not this session's other change) via CI run
`30691249715` failing identically at SHA `0e95a756683d81b92ab0b97c5871d637d71d1db0` (this session's own clean starting
HEAD, before any of this session's edits).

**Fixed inline** (small + clear + directly blocking, per findings-triage's `≤30 min` carve-out — not deferred): updated
all 13 hardcoded `expected` literals in the 5 affected files to the folded shape, matching exactly what `_test_bucket()`
now returns and what finding P0 already live-verified against real GCS. `features-service@b9cf1e1c`. Full
`quality-gates.sh` re-run green after this fix (see checkbox evidence below).

## Why it matters

- **Finding 6** was the most URGENT in practice (even though now resolved): it broke `quality-gates.sh`/CI for the
  entire features-service repo, blocking every task — not just this doc's own scope — from shipping anything under the
  green-tree HARD RULE, for however long `04d261d` sat unreconciled (multiple CI runs failed identically across
  2026-07-31 21:59 through 2026-08-01 08:10). Caught opportunistically by an unrelated task rather than by this doc's
  own follow-through, which is itself a gap worth noting: a same-session "does the fix's own repo still pass CI" check
  after `04d261d` shipped would have caught this immediately instead of leaving the repo red for ~10+ hours.
- **multi_timeframe (finding 1)** is the most severe: the family's CLI is unusable in ANY mode (batch, live, compute) —
  not a data-quality issue but a total service outage for anyone trying to run it, including any automated pipeline
  check that shells out to it. This should be triaged with urgency independent of the smoke harness context it was
  discovered in.
- **Findings 2-3** mean the "institutional smoke matrix" design's own contract (each file's docstring: "Writes are
  test-bucket-only... Verify >=1 parquet blob... Verify TEST bucket manifest row") has been unverifiable for calendar
  and delta_one specifically, for reasons independent of and layered on top of the bucket-routing bug this session's P0
  fixed. A "PASS" from these harnesses, even after the routing fix, cannot currently be trusted as proof the family's
  real pipeline works — exactly the smoke-check-masking risk class the companion doc
  (`features_service_catalogue_completeness_smoke_masking_findings_2026_08_01.md`) is already tracking for a different
  pair of families.
- **Finding 4** means TRADFI delta_one/volatility and SPORTS features currently cannot pass their dependency-check or
  skip-logic reads at all until the consolidator catches up or is fixed — a live data-pipeline availability gap, not a
  cosmetic issue.

## Why not fixed here

This session's task (`features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P0) was scoped narrowly to
`_invoke_cli()`'s env-var wiring. Fixing findings 2-3 correctly requires confirming the REAL write-path shape for each
of the remaining 5 families individually (this session only confirmed 2 of 8, calendar + delta_one) rather than guessing
a shared pattern — properly scoped as its own todo. Finding 1 (mtf CLI) is a `features-service` code bug entirely
outside `e2e-testing`'s scope. Finding 4 is an infra/consolidator-ops issue, not a code fix. None of these block this
session's P0 fix, which is proven correct independent of them (calendar + onchain got full real end-to-end writes;
delta_one got a real confirmed manifest write; the other 5 families' bucket _resolution_ was confirmed correct via
direct `get_output_bucket()` calls using the exact env vars the fix sets).

**Also not covered here**: a separate, more urgent incident (`features_service.cross_instrument`'s smoke-verify run
growing to ~38.8GB RSS over several hours, ignoring its `timeout` wrapper, causing two same-day agent-orchestrator
outages) was independently discovered and is being tracked in its own issue doc
(`features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md`) by the agent who filed it —
not duplicated here.

## Recommended decision

- [x] ✅ [SCRIPT] P0. **features-service** — root-cause + fix the `multi_timeframe` CLI's `argparse` duplicate
      `--start-date` registration (confirmed: crashes even `--help`, not just a specific flag combination). Add a
      regression test that imports the CLI's `build_parser()` (or equivalent) and asserts it constructs without raising.
      **Done when**: `python -m features_service.multi_timeframe --help` exits 0 and prints usage. — Root cause:
      `ServiceBootstrap` defaults `add_date_args=True`, registering `--start-date`/`--end-date` via
      `ServiceCLI._add_date_window_args()` inside `build_parser()` BEFORE it invokes `extra_args_fn`; multi_timeframe's
      own `_extra_args` re-registered both flags, so `argparse.ArgumentError` fired during parser construction itself.
      Removed the duplicate registrations (kept the family's unique `--date`); added `test_build_parser_does_not_raise`
      (builds the exact `ServiceCLI` `ServiceBootstrap` constructs and asserts parser construction succeeds — the
      pre-existing `test_main_help_exits` didn't catch this because `ServiceBootstrap`'s generic exception handler also
      raises `SystemExit(1)` on any uncaught exception, which a bare `pytest.raises(SystemExit)` can't distinguish from
      a genuine `--help` exit). Verified live: `python -m features_service.multi_timeframe --help` exits 0.
      `features-service@39cc8653` — full `quality-gates.sh` green (`18072 passed, 209 skipped, 0 failed`).
- [ ] [SCRIPT] P2. **e2e-testing** — fix calendar's `smoke_matrix.py` verifier: change `SMOKE_FEATURE_GROUP` to a real
      calendar feature group (e.g. `economic_events`) and correct `_verify_gcs_parquet`'s prefix to
      `calendar/{feature_group}/by_date/day={date}/` (no `features/` root, no `feature_group=` directory segment).
      Correct `_verify_test_manifest`'s asset_group filter to match how calendar's manifest rows are actually tagged
      (read a real manifest row first to confirm the field/value rather than assuming). **Done when**: a real
      (non-dry-run) calendar smoke run returns PASS from the harness itself, not just a cited gs:// path in the CLI's
      own log output.
- [ ] [SCRIPT] P2. **e2e-testing** — fix delta_one's `smoke_matrix.py` `_verify_gcs_parquet` prefix to match
      `OUTPUT_PATH_TEMPLATE` (`by_date/day={date}/feature_group={group}/timeframe={timeframe}/`, no `features/` prefix)
      — confirm the exact `timeframe` value the smoke cell's CLI invocation implies (check `_build_cli_invocation`'s
      default/omitted `--timeframe`) before hardcoding it into the verifier. **Done when**: a real delta_one smoke run
      (any viable asset_group with real upstream data) returns PASS from the harness itself.
- [ ] [SCRIPT] P2. **e2e-testing** — audit cross_instrument/onchain/sports/volatility's `smoke_matrix.py` verifiers
      (`_verify_gcs_parquet` prefix, `_verify_test_manifest` asset_group/feature_group filter) against each family's
      REAL write-path code (writer/orchestrator, not assumptions) — this session only confirmed the bucket NAME is now
      correct for these 4 (via `TEST_BUCKET_TEMPLATE` fixes already shipped), not the object-key PREFIX shape within
      that bucket. Fix any mismatches found, mirroring the calendar/delta_one pattern above.
- [x] ✅ [DATA] P1. **operator/infra** — investigate why `market-data-tick-tradfi-prd-central-element-323112`'s manifest
      consolidator is ~13h+ behind (age 47,309s vs 7,200s threshold at time of check) — check the Cloud Run Job +
      Scheduler health for this specific bucket per the error's own remediation pointer. **Done when**: consolidated
      `availability_index` age is back under the 7,200s threshold, or a root cause + ETA is documented if the job is
      genuinely down. — **Root cause + ETA documented 2026-08-01 (slot 7)**, satisfying the doc-when-genuinely-down
      branch: NOT a broken/stuck consolidator — `uts-prod-manifest-consolidator-market-data-tradfi-cron` is
      **deliberately** `PAUSED` (verified `state=PAUSED`, `userUpdateTime=2026-07-31T18:25:11Z`; index
      `update_time=2026-07-31T18:29:55Z`, now ~53,900s stale — grown since this doc's original 47,309s reading, not
      shrunk) as the tracked pause-half of `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own
      Apply→force-consolidate→Resume backfill sequence (its own todos at that plan's lines 296-308: Apply
      `rebuild_tradfi_manifest.py` full-range, then Resume the cron). This exact root cause (deliberate, plan-owned
      pause, not a stuck/broken automation) is already fully diagnosed in the sibling issue
      `/plans/active/issues/tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md` — not re-derived here,
      cross-referenced. **ETA / current status**: the tradfi Apply step has NOT started — no worker/tmux session is
      currently running `rebuild_tradfi_manifest.py` for tradfi (confirmed via a live pane sweep), and its Resume-cron
      backlog task (`mtds_available_at_cross_asset_backfill-003`) is `queued`/undispatched. This lags its sibling
      PREDICTION lane, which IS actively running (backlog task `-006`, dispatched to slot 3, mid chunked-apply as of
      this check) — i.e. tradfi's resume has no live ETA yet because its own Apply hasn't even been picked up,
      consistent with the already-tracked dispatcher issue
      `/plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`. **Not fixed here**:
      running the tradfi Apply/Resume belongs to `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own todos
      (lines 296-308) — doing it from this doc's scope would duplicate ownership of a plan that already tracks it and
      risk the exact concurrent-dispatch collision the prediction lane's own Progress Log documents happening 3x.
      Recommend: once tradfi's own Apply/Resume todos are dispatched (directly, or once the dispatch-order bug is
      fixed), this bucket self-heals — no separate action item needed in this doc.
- [ ] [DATA] P2. **operator/infra** — determine why `features-sports-test-central-element-323112` has never had a
      consolidated `availability_index` written (while per-VM shards exist) — confirm whether the manifest
      consolidator's bucket registry includes `-test-` siblings at all, and if not, whether it should. **Done when**:
      either a consolidated index exists for this bucket, or a decision is documented that `-test-` buckets are
      intentionally out of consolidator scope (in which case smoke-harness reads against them should set
      `MANIFEST_ALLOW_STALE_FALLBACK=true` or read per-VM shards directly, not fail-closed).
- [x] ✅ [DATA] P1. **features-service** — investigate why `perp_collapse` retained 0/215 CEFI instruments for
      `technical_indicators` on 2026-07-28 (`dropped ... no-rep=214` — no qualifying representative venue found for
      214/215 bases). Determine whether this is a `perp_collapse` logic regression or a genuine upstream
      representative-venue data gap for that date, then either fix the logic or confirm the date is a legitimate thin
      day. **Done when**: a real CEFI/technical_indicators run for a date with known-good representative-venue data
      either produces real feature rows or a genuinely `FetchEvidence`-backed `empty_confirmed` — not a `record_failed`
      from an unproven absence. — Root-caused to a `unified-trading-library` bug, not a genuine thin day or a
      `features-service`/`perp_collapse` regression: `unified-trading-library@d120aa54`.
      `aggregate_cefi_manifest_volume`'s `_base_asset_from_symbol` only trusted the manifest's own `quote_asset` column
      to strip the quote suffix, but that column is blank for ~100% of captured CEFI PERPETUAL rows across EVERY venue
      (HYPERLIQUID 42492/42492 blank, ASTER 26757/26757, LIGHTER-ZKSYNC 5176/5176, COINBASE-FUTURES 3222/3222,
      EXTENDED-STARKNET 2892/2899, BITFINEX-FUTURES 1566/1573, DERIBIT 471/471 — confirmed via a real column-pruned read
      of the prod cefi manifest, 30-day window ending 2026-07-28), so `venue_volumes` came back as effectively 1
      observation instead of hundreds, starving `feature_perp_representative` and collapsing `perp_collapse` to
      near-zero retention for almost every base. Fixed by falling back to parsing BASE-QUOTE directly off the canonical
      `VENUE:TYPE:SYMBOL@LIN|INV` grammar via `accepted_quotes_for_venue` when `quote_asset` is blank (mirrors
      `features_service...mvp_universe_filter._extract_base_asset`, which never depended on that column). Verified live
      (not just unit tests): `venue_volumes` count 1 → 1162 for the 2026-07-28 window, and re-running
      `filter_instruments_for_family` against the real 2026-07-28 CEFI PERPETUAL instrument universe now retains 86/207
      with `no-rep=0` (was 0/215 with `no-rep=214`). 2 new regression tests added + full `quality-gates.sh` green.
- [x] ✅ [SCRIPT] P0. **features-service** — update the 13 stale `_test_bucket()` expected-value literals across
      `tests/{cross_instrument,delta_one,multi_timeframe,onchain,volatility}/unit/test_smoke_matrix.py` to the folded
      `features-{asset_group_lower}-test-{project_id}` shape `e2e-testing@04d261d` shipped. **Done when**:
      `bash     scripts/quality-gates.sh` is green for features-service. — `features-service@b9cf1e1c` (test fix) +
      `features-service@217eb3a2` (unrelated extraPaths todo shipped same session). Full `quality-gates.sh` green (see
      Progress Log for run evidence); confirmed the 13 failures were pre-existing via CI run `30691249715` at SHA
      `0e95a756683d81b92ab0b97c5871d637d71d1db0` before fixing.

## Progress Log

- 2026-08-01 (slot-12, data_engineering): Filed as the FINDINGS CLOSURE follow-up for
  `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P0 (this session's primary task, shipped
  `e2e-testing@04d261d`). None of these findings fixed inline — each requires independent per-family/per-bucket
  investigation properly scoped as its own todo, per the task's own narrow `_invoke_cli()` scope.
- 2026-08-01 (slot-12, data_engineering, pre-compact audit): added finding 5 (delta_one CEFI `perp_collapse`
  0/215-retained + rejected empty-write) — this was cited in the parent plan's checkbox evidence and this session's ship
  commit message but had not actually been captured as a tracked todo here; caught during the pre-compact "every
  deferral must already exist as a `- [ ]`" check. 5 findings total, all still open.
- 2026-08-01 (slot-7, ui_developer craft slot working a [SCRIPT] todo — see
  `basedpyright_extrapaths_pyproject_migration_findings_2026_08_01.md`): added + immediately closed finding 6 —
  `e2e-testing@04d261d`'s bucket-naming fold broke 13 of features-service's own unit test assertions, confirmed CI-red
  for the whole repo since `04d261d` landed (~10+ hours across 4 CI runs). Fixed inline (small+clear+directly-blocking
  carve-out): `features-service@b9cf1e1c`. Full `quality-gates.sh` re-run green — `18071 passed, 209 skipped, 0 failed`
  (up from `18058 passed, 13 failed` pre-fix), sentinel-verified at HEAD=b9cf1e1c, shipped via quickmerge + verified
  landed on `live-defi-rollout` (`git merge-base --is-ancestor` against origin). 6 findings total; 1 (this one) now
  closed, 5 still open.
- 2026-08-01 (slot-7, data_engineering, backlog task `features_smoke_matrix_verification_findings-005`): closed the
  finding-4a (TRADFI) todo via investigation, not a fix — root cause is a DELIBERATE cron pause owned by a different
  in-flight plan (`mtds_available_at_cross_asset_backfill_2026_07_13.md`), already independently diagnosed in
  `/plans/active/issues/tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md`; cross-referenced rather than
  re-derived. Confirmed via live checks: cron still `PAUSED`, index still stale (now ~53,900s, up from the original
  47,309s reading — actively worsening, not recovering on its own). Confirmed tradfi's own Apply step
  (`rebuild_tradfi_manifest.py`) has not even started (no live process, Resume-cron task `-003` still queued) — behind
  its sibling prediction lane, which IS actively running. Did not run the Apply/Resume myself: that work is already
  tracked under the OTHER plan's own todos (lines 296-308), and duplicating it here risks the same concurrent-dispatch
  collision that plan's own Progress Log already documents 3x for the prediction lane. Left the sports-`-test-` finding
  (P2, features-sports-test bucket, no consolidated index) untouched — separate root cause (consolidator scheduler never
  wired to `-test-` buckets by design, per `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Coverage
  exemptions"), out of this todo's scope.
- 2026-08-01 (slot-12, data_engineering, backlog task `features_smoke_matrix_verification_findings-001`): closed finding
  1 (multi_timeframe CLI argparse duplicate). Root cause: `ServiceBootstrap` defaults `add_date_args=True`, which
  registers `--start-date`/`--end-date` inside `build_parser()` BEFORE `extra_args_fn` runs; multi_timeframe's own
  `_extra_args` re-registered both flags, causing `argparse.ArgumentError` at parser-construction time (crashes even
  `--help`). Fix: removed the duplicate registrations from `_extra_args` (kept the family's unique `--date`). Added
  `test_build_parser_does_not_raise`, which builds the exact `ServiceCLI` `ServiceBootstrap` constructs and asserts
  parser construction succeeds — confirmed the pre-existing `test_main_help_exits` did NOT catch this bug (verified
  pre-fix: `ArgumentError` gets caught by `ServiceBootstrap`'s generic exception handler and re-raised as `sys.exit(1)`,
  still a `SystemExit`, indistinguishable from a genuine `--help` exit under a bare `pytest.raises(SystemExit)`).
  Verified live pre/post-fix via direct CLI invocation (`python -m features_service.multi_timeframe --help`: pre-fix
  `ArgumentError` traceback + exit 1; post-fix usage printed + exit 0). `features-service@39cc8653`, full
  `quality-gates.sh` green (`18072 passed, 209 skipped, 0 failed`, sentinel
  `.qg_last_passed_sha=39cc865347b60273ec05bc38c4144526750ee499`). 6 findings total; 2 closed (this one + finding 6), 4
  still open.
- 2026-08-01 (slot-15, data_engineering, backlog task `features_smoke_matrix_verification_findings-007`): closed finding
  5 (delta_one CEFI `perp_collapse` 0/215-retained). Root-caused via a real, column-pruned read of the prod
  `market-data-tick-cefi-prd-central-element-323112` manifest (30-day window ending 2026-07-28): `captured` PERPETUAL
  rows are 90%+ parseable and mostly `instrument_type=PERPETUAL` as expected, but the manifest's `quote_asset` column —
  which `unified_trading_library.manifest_writer._volume_aggregation._base_asset_from_symbol` exclusively relied on to
  strip the quote suffix — is blank for essentially every venue (HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/COINBASE-FUTURES 100%
  blank; EXTENDED-STARKNET/BITFINEX-FUTURES/DERIBIT 99.6-100% blank), so `aggregate_cefi_manifest_volume` returned only
  1 `VenueVolumeObservation` instead of hundreds, starving `feature_perp_representative` and collapsing `perp_collapse`
  for nearly every base — not a `perp_collapse` logic bug and not a genuine thin day; the bug lives entirely upstream in
  the shared UTL aggregator both `features-service` (this collapse) and MTDS's `cefi_catalog_reader.py` (margin-leg
  gate) depend on. Fixed `_base_asset_from_symbol` to fall back to parsing BASE-QUOTE directly off the symbol's own
  canonical grammar (mirroring `mvp_universe_filter._extract_base_asset`, which never needed the column) when
  `quote_asset` is blank or doesn't match. Verified live before/after: `venue_volumes` 1 → 1162 for the 2026-07-28
  window; re-running `filter_instruments_for_family` against the real 2026-07-28 CEFI PERPETUAL universe: 0/215
  (`no-rep=214`) → 86/207 (`no-rep=0`). Added 2 regression tests (`test_blank_quote_asset_falls_back_to_symbol_grammar`,
  `test_venue_specific_quote_extension_used_in_grammar_fallback`)
  - updated the existing "skipped not guessed" test's framing to the still-genuine unparseable-symbol case; all 9 tests
    pass. `unified-trading-library@d120aa54`, full `quality-gates.sh` green (172s), sentinel
    `.qg_last_passed_sha=d120aa54a7fecd925f04373fcf4863bb8fae6741`, verified landed on `live-defi-rollout` via
    `git merge-base --is-ancestor`. Did not re-run the real
    `features_service.delta_one --asset-group CEFI --feature-group technical_indicators --date 2026-07-28` CLI
    end-to-end (that would additionally write real prod manifest/GCS rows for that historical date) — the fix is
    verified at the exact layer that was broken (`aggregate_cefi_manifest_volume` →
    `filter_instruments_for_family`/`perp_collapse`), which is what actually starved the CLI run; a follow-up full-CLI
    re-run to produce the real feature/manifest row for 2026-07-28 is worth doing but is a separate, larger action
    (writes to prod) than this todo's own root-cause-and-fix scope. 6 findings total; 3 closed (this one + findings 1,
    6), 3 still open (2, 3, and the sports-`-test-` consolidator gap).
