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

## Why it matters

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

- [ ] [SCRIPT] P0. **features-service** — root-cause + fix the `multi_timeframe` CLI's `argparse` duplicate
      `--start-date` registration (confirmed: crashes even `--help`, not just a specific flag combination). Add a
      regression test that imports the CLI's `build_parser()` (or equivalent) and asserts it constructs without raising.
      **Done when**: `python -m features_service.multi_timeframe --help` exits 0 and prints usage.
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
- [ ] [DATA] P1. **operator/infra** — investigate why `market-data-tick-tradfi-prd-central-element-323112`'s manifest
      consolidator is ~13h+ behind (age 47,309s vs 7,200s threshold at time of check) — check the Cloud Run Job +
      Scheduler health for this specific bucket per the error's own remediation pointer. **Done when**: consolidated
      `availability_index` age is back under the 7,200s threshold, or a root cause + ETA is documented if the job is
      genuinely down.
- [ ] [DATA] P2. **operator/infra** — determine why `features-sports-test-central-element-323112` has never had a
      consolidated `availability_index` written (while per-VM shards exist) — confirm whether the manifest
      consolidator's bucket registry includes `-test-` siblings at all, and if not, whether it should. **Done when**:
      either a consolidated index exists for this bucket, or a decision is documented that `-test-` buckets are
      intentionally out of consolidator scope (in which case smoke-harness reads against them should set
      `MANIFEST_ALLOW_STALE_FALLBACK=true` or read per-VM shards directly, not fail-closed).
- [ ] [DATA] P1. **features-service** — investigate why `perp_collapse` retained 0/215 CEFI instruments for
      `technical_indicators` on 2026-07-28 (`dropped ... no-rep=214` — no qualifying representative venue found for
      214/215 bases). Determine whether this is a `perp_collapse` logic regression or a genuine upstream
      representative-venue data gap for that date, then either fix the logic or confirm the date is a legitimate thin
      day. **Done when**: a real CEFI/technical_indicators run for a date with known-good representative-venue data
      either produces real feature rows or a genuinely `FetchEvidence`-backed `empty_confirmed` — not a `record_failed`
      from an unproven absence.

## Progress Log

- 2026-08-01 (slot-12, data_engineering): Filed as the FINDINGS CLOSURE follow-up for
  `features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md`'s P0 (this session's primary task, shipped
  `e2e-testing@04d261d`). None of these findings fixed inline — each requires independent per-family/per-bucket
  investigation properly scoped as its own todo, per the task's own narrow `_invoke_cli()` scope.
- 2026-08-01 (slot-12, data_engineering, pre-compact audit): added finding 5 (delta_one CEFI `perp_collapse`
  0/215-retained + rejected empty-write) — this was cited in the parent plan's checkbox evidence and this session's ship
  commit message but had not actually been captured as a tracked todo here; caught during the pre-compact "every
  deferral must already exist as a `- [ ]`" check. 5 findings total, all still open.
