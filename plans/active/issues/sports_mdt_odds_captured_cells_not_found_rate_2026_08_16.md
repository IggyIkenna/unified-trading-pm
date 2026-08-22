---
doc_type: issue
title:
  93.15% of a 50,000-cell sample of "capture_status=captured" sports batch_odds_api manifest cells resolve to
  blob_exists()==False at their expected canonical path — possible false-positive coverage claim, likely correlated
  with the already-tracked ODDS league_id growth (51→384) investigation
summary: >-
  While re-verifying the poll-key-duplicate dedup rule (sports_satellite_ao_dispatch_batch9-010) via a fresh,
  full-population dry-run of `dedup_odds_api_poll_key_duplicates_2026_07_26.py`, the manifest's captured
  `batch_odds_api` (sports odds TRADES) cell count was found to be 4,240,790 — a 15.4x jump from the 275,136 measured
  on 2026-07-26 (3 weeks prior). A bounded 50,000-cell sample (first 50K rows in `read_availability_index` iteration
  order, NOT a randomized draw) found only 3,425 (6.85%) resolve to a real GCS object at the expected canonical
  path — the other 46,575 (93.15%) return `blob_exists()==False`. If this rate holds population-wide, it implies
  millions of manifest rows claim `capture_status=captured` for data that was never actually written — a
  false-positive coverage claim, not an honest gap. This is independent of (but directly relevant evidence for) the
  already-open todo in `sports_satellite_ao_dispatch_batch9_2026_08_04.md` investigating whether ODDS-specific
  league_id growth (51→384, ~7.5x, vs the ~4x baseline other data_types show) is genuine coverage expansion or a
  duplicate/near-duplicate seeding artifact.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, instruments-service, unified-trading-library]
scope: [engineer]
tags: [mdt, sports, odds, manifest, honest-coverage, data-correctness, capture-status, not-found, league-id-growth]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
    /plans/archive/issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-16
author: unknown
last_updated: 2026-08-22
priority: P0
parent_epic: sports_master
source: >-
  Discovered as a side-effect of executing sports_satellite_ao_dispatch_batch9-010 (root-cause the 216
  poll-key-duplicate residual) — the todo's own "fresh, not --affected-cells-file, run" instruction surfaced this
  finding before any per-cell dedup logic ran.
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
drift_direction: advance-code
resolved_by:
locked_by:
context_scope: [/plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md, /plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md, /codex/02-data/honest-absence-downstream-handling.md, /codex/02-data/availability-manifest-and-data-status.md, market-tick-data-service/scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py]
depends_on: []
---

# Sports MDT odds "captured" manifest cells — 93.15% sample not_found rate at canonical path

> **⚠️ CORRECTION (2026-08-16, slot-4, todo 1 resolution).** The randomized re-measurement todo 1 asked for CONFIRMED
> the not_found rate is population-representative (87.8%, not a sampling artifact) but DISCONFIRMED the premise
> linking it to the "51→384" league_id growth: `batch_odds_api`'s own distinct `league_id` count is FLAT at 40 across
> both the 2025 H1 and 2026 H1 windows (0 new). The league_id growth is a DIFFERENT manifest entirely (the
> instruments-service reference-data catalogue, already closed GENUINE_EXPANSION 2026-08-05,
> `instruments-service@7fc96c90`) — not this MTDS tick-data manifest. The REAL root cause: 86.4% of this manifest's
> captured population carries `data_type=odds_horizon_bucket`, a data_type with no raw vendor source by design, whose
> manifest rows have no backing parquet by construction — an ACTIVE writer bug (still writing as of 2026-08-15), not a
> seeding artifact. Full detail in todo 1 below and the Progress Log.

> **🚨 REGRESSION (2026-08-22, D2 disposition independent re-verification — this session, ~06:52-07:07 BST, ~6h
> after the entries below).** The "VERIFIED-ALREADY-ACHIEVED" claims on both `[DATA][OPERATOR] P1` todos below
> (dated 2026-08-22 00:49-01:17 BST, `market-tick-data-service@a9b1d055c9`) do **NOT hold six hours later**.
> Re-running that SAME already-committed script fresh (unmodified) found the `batch_odds_api` captured population
> back at **4,352,441 rows, 86.65% `data_type=odds_horizon_bucket`** (was 211,291 / 0% at 00:57 BST) and a fresh
> 1,500-row `gcs_describe_object` sample at **100% not_found** (was 0%) — WORSE than the original pre-cleanup
> baseline (4,281,228 rows / 86.4%, measured 2026-08-17). A follow-up bounded read confirmed the `odds_horizon_bucket`
> rows span the FULL historical range (2020-06-06 to 2026-08-15, not a narrow recent window) and that the good
> `data_type=odds` twin data is unaffected (527,541 rows, unchanged since 2026-07-26). Soft-delete retention
> re-confirmed independently (604800s, unchanged, qualifies) and the prior session's commits are confirmed real and
> already on `origin/live-defi-rollout` (`git log`/`git status` verified) — this is a genuine regrowth, not a stale
> read or a fabricated prior claim. **Neither queued row-removal plan was executed this session** — WITHHELD per the
> dispatch's own gate-failure rule, since removing rows from a population that just re-grew ~20x in 6h would race
> whatever is rewriting it (strong candidate lead: the long-running `mtds-backfill-odds-20260817-062648` VM, still
> `RUNNING` as of this check, launched pre-dating every writer fix in this doc and per its own sibling doc
> `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` "does not stop on an exhausted
> quota" — the-odds-api key was topped up 2026-08-21, which would let this never-restarted, pre-fix-code VM resume
> writing at full historical scale on the same 00:57→06:52 timeline). New `[DIAG][OPERATOR] P0` root-cause todo filed
> below (supersedes the "already achieved" verdict); doc `priority` bumped to P0. This is a **big finding** per
> workspace HARD RULE (active data-correctness regression, cross-repo MTDS/MDPS, contradicts this doc's own
> same-day-6-hours-earlier verified claim) — surfaced to the operator in this session's report in addition to this
> banner and the Progress Log entry below.

## What I found

Working `sports_satellite_ao_dispatch_batch9-010`'s explicit instruction ("regenerate the current undecidable-cell set
via a fresh, not `--affected-cells-file`, run of `dedup_odds_api_poll_key_duplicates_2026_07_26.py`"), a full-population
dry-run against `market-data-tick-sports-prd-central-element-323112` first logged:

```
No --affected-cells-file given: scanning all 4239538 captured cells
```

This is a **15.4x jump** from the 275,136 captured `batch_odds_api` cells measured on 2026-07-26 (per the archived
`mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`). That first full-scan attempt was **OOM-killed** (SIGKILL,
exit 137) by the shared host's cgroup — the script's `ThreadPoolExecutor` submits **all** N cells' futures in a single
eager dict comprehension, so at 4.2M+ cells this allocates millions of live `Future`/work-queue objects at once. Fixed
in the same session (bounded chunked submission, `--chunk-size`, default 2000; `market-tick-data-service` — see the
batch9-010 Progress Log for the commit).

Using the fixed (chunked, memory-safe) script, a **bounded 50,000-cell sample** — the first 50,000 rows in
`read_availability_index`'s iteration order, **not a randomized `df.sample()` draw** (caveat below) — was dry-run
scanned:

```
Status counts: {'not_found': 46575, 'clean': 3419, 'would_dedupe': 6}
```

**46,575/50,000 (93.15%) of cells the manifest marks `capture_status=captured` return `blob_exists()==False`** at the
canonical path `raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue={V}/
league_id={L}/instrument_type={ODDS|odds}/data_type={D}/ticks.parquet`. Only 3,425 (6.85%) resolved to a real object —
of those, 6 carried poll-key duplicates (all 6 fully decided by the already-shipped Rule 2, 0 undecided — this is
strong, separate evidence the dedup rule itself is sound; not this doc's concern).

**Caveat — sample is NOT randomized.** `--limit N` in the dedup script takes `cells[:N]`, the first N rows of
whatever order `read_availability_index()` returns (parquet scan order, not date-sorted or shuffled). The 93.15%
figure is a real, measured result for THIS specific 50,000-row slice, but has not been confirmed representative of
the full 4,240,790-cell population — a genuinely randomized sample (or the full population, VM-dispatched given its
scale) is needed before treating 93.15% as a population-wide rate.

## Why it matters

- If this rate is anywhere close to population-representative, it means **millions of manifest rows claim
  `capture_status=captured` for sports odds data that does not exist at its canonical path** — the worst class of
  honest-coverage violation this workspace's own doctrine names explicitly: a **silent placeholder / false-positive**,
  not an honest gap (`capture_status=attempted_failed` or `expected_unattempted` would be the honest states; `captured`
  with no backing object is neither — see `/codex/02-data/honest-absence-downstream-handling.md`).
- This is **strong supporting evidence** (not proof) for the already-open todo in the SAME plan
  (`sports_satellite_ao_dispatch_batch9_2026_08_04.md`, [DIAG] P3): "Investigate the FIXTURES/FIXTURES_OUTCOMES/
  ODDS-specific distinct league_id growth (88→924, 88→926, 51→384 respectively, vs the ~4x baseline other sports
  data_types show) to classify it as genuine coverage expansion vs a duplicate/near-duplicate league_id seeding
  artifact." A 93% not-found rate on a corpus that grew 15.4x in 3 weeks is far more consistent with a seeding
  artifact (many net-new manifest rows never backed by a real write) than with genuine coverage expansion.
- Downstream consumers reading this manifest for coverage/completeness metrics (honest-coverage dashboards, dispersion
  aggregates that trust `captured` status) would silently under-report the TRUE gap, believing sports odds coverage is
  far more complete than it actually is.

## Recommended decision

This doc does NOT root-cause the underlying writer/seeding mechanism (out of scope for the task that surfaced it,
and the league_id-growth todo above already owns that investigation). It exists to hand the league_id-growth
investigation strong, freshly-measured evidence, and to make the false-`captured`-status possibility explicit and
trackable on its own, since it is a distinct concern (coverage-reporting correctness) from the growth mechanism
itself (why so many new league_id rows exist).

- [x] ✅ [DIAG] P1. **DONE 2026-08-16 (slot-9, `data_engineering`).** Ran a genuine randomized sample
      (`df.sample(n=50000, random_state=20260816)` over the full captured `batch_odds_api` population — 4,279,597
      rows, single bounded manifest read, no new GCS walk) via
      `market-tick-data-service/scripts/measure_odds_not_found_rate_randomized_2026_08_16.py`.
      **Result: 43,824/50,000 (87.65%) not_found — confirms the raw 93.15% figure is population-representative**
      (same order of magnitude, randomized). Cross-tabulated by pre-growth (H1-2025, 40 distinct ODDS league_ids) vs
      post-growth (28 new league_ids introduced since): **PRE-growth league_ids show a HIGHER not_found rate (87.90%,
      n=49,726) than POST-growth league_ids (42.34%, n=274)** — the INVERSE of what the seeding-artifact-causes-
      not_found hypothesis predicted. This does NOT confirm concentration in the growth league_ids; see the Progress
      Log below for the corrected root-cause finding (stale rekey duplicates, not seeding-artifact fetch failures).
      Also measured: current distinct ODDS league_id count is only **68** (not 384) — the
      `canonicalize_sports_league_id_schema_2026_06_24.py --drop-out-of-universe --apply` re-key run (2026-08-04,
      already landed per `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s completed todos) has already
      consolidated the league_id space back down close to the 51 H1-2025 baseline — see the league_id-growth verdict
      this unblocks, below.
- [x] ✅ [DATA] P1. **DONE 2026-08-16 (slot-9, `data_engineering`).** League_id-growth verdict reached (see
      `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s todo, flipped alongside this one): the 51→384 growth WAS
      predominantly a duplicate/near-duplicate league_id seeding artifact, since substantially remediated by the
      2026-08-04 re-key (384→68 distinct ODDS league_ids). That satisfies this todo's gating condition. **However,
      the proposed fix is NOT an `attempted_failed` relabel** — a bounded in-memory twin-check (same script, 300 of
      the sampled not_found rows) found **296/300 (98.67%) have a `captured` row for the SAME (date, venue,
      data_type) under a DIFFERENT (canonical) league_id.** The underlying data is NOT missing — it was correctly
      re-captured under the canonical league_id by the 2026-08-04 rekey; the not_found row is a STALE DUPLICATE
      manifest entry (pre-rekey league_id spelling) whose object was superseded/moved and never cleaned up.
      `attempted_failed` would be factually wrong here (it asserts a fetch attempt failed; the fetch succeeded, just
      under a different key) — the correct honest-absence-downstream-handling.md-consistent action is **row REMOVAL**
      (the stale row has no backing object AND a canonical twin already carries the real data), analogous to
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL from the canonical", not a
      capture_status relabel. **Proposed scoped plan (NOT executed — operator sign-off required, ~3.75M-row-scale
      candidate population at the measured 87.65% rate)**:
      1. For every `batch_odds_api` `captured` row where `blob_exists()==False` at its own canonical path AND a
         `captured` row exists for the same `(date, venue, data_type)` under a different `league_id`: DROP the stale
         row (manifest-only edit; no GCS object to delete since none exists at that row's path).
      2. For the residual ~1.33% with no twin found by the (date, venue, data_type) key: needs individual triage
         (broader join key, e.g. include `source`, or manual sampling) before deciding relabel vs removal — do NOT
         assume `attempted_failed` for these either without checking a wider twin key first.
      3. Snapshot the affected rows before drop (same precedent as the 2026-08-04 rekey's
         `pre_league_id_canonicalize_20260804T075724Z.parquet` snapshot) for reversibility.
      4. VM-scale dispatch required given population size (mirrors this task's own script needing the chunked-submit
         fix for the same corpus scale).
      Done when (this todo): satisfied — league_id-growth verdict reached, not_found population is confirmed a
      false-`captured`-status case (stale duplicate rows, not lost data), and a concrete, reviewed plan (row removal,
      corrected from the originally-proposed relabel) is recorded above, pending operator sign-off to execute (see
      new [OPERATOR] todo below).
- [x] ✅ [DATA][OPERATOR] P1. **VERIFIED-ALREADY-ACHIEVED 2026-08-22 (D2 disposition execution — dispositions.json D2
      "APPROVED ALL... under each item's stated precondition"; NOT executed by this session — see below).** Fresh
      precondition re-check: bucket soft-delete retention re-queried live via `gcs_bucket_soft_delete_retention_seconds`
      = 604800s (≥7d, qualifies). A fresh, column-projected manifest read (today, no new GCS walk) then found the
      target post-state **already reached**: full `batch_odds_api` captured population is now 211,291 rows (down
      from 4,281,228 measured 2026-08-17), **100% `data_type=odds`** (0 residual stale-duplicate rows of any other
      data_type), and a fresh sample (n=1500, seed=20260822, `gcs_describe_object` per row — stronger than the prior
      `list_blobs`-based checks) found **0/1500 (0%) not_found** — down from the 87.65-93.15% repeatedly measured
      2026-08-16/17. 5/5 additional spot-checked rows resolved to real backing objects. This satisfies this todo's
      own done-condition ("a re-measurement confirms the not_found rate has dropped substantially"). **Could not
      identify the executing mechanism**: no commit in `market-tick-data-service` since 2026-08-19 matches (checked
      local HEAD — confirmed == `origin/live-defi-rollout` via fresh fetch — and grepped commit messages), and no
      manifest snapshot exists under this plan's own proposed naming (`pre_league_id_canonicalize_stale_removal_*`);
      only an unrelated `_index/snapshots/k2_stale_twin_presync/` prefix is present. The `_index/availability_index.
      parquet` blob's `last_modified` is 2026-08-21T23:16:42Z, immediately after a `_index/latest.json` run logging
      `rows_in=0/rows_out=0` (a no-op incremental merge) — the actual large rewrite landed in an EARLIER write this
      run didn't perform. Given heavy parallel activity on this exact manifest today (the D7 the-odds-api key-rotation
      + batch-consumer-bounding todo above resolved 2026-08-21 in this same doc; sibling D2 docs
      `sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md` / `sports_halftime_odds_sfi_vs_inplay_
      2026_07_16.md` also touch this bucket), this most likely landed via a parallel worker's corrective pass. Filed
      as a new audit-trail-gap follow-up below — not blocking, since the OUTCOME is independently verified via this
      todo's own stated success criteria; only the provenance trail is missing. **No `--apply` was run in this
      session**: the population is already clean, so re-running against it would be a no-op at best and risks
      racing a possible in-flight sibling writer (exactly the hazard `gcs-and-manifest-delete-safety-protocol.md`
      §5's consolidator-pause-check exists to prevent). Evidence: `market-tick-data-service@a9b1d055c9`
      (`scripts/fresh_precondition_check_d2_odds_2026_08_22.py`, read-only, safe to re-run); full counts in the
      Progress Log entry below.
**Update 2026-08-16 (todo 1 resolution)**: the link to the league_id-growth todo assumed above did NOT hold — see the
correction banner at the top of this doc. The not_found population's root cause IS now identified
(`data_type=odds_horizon_bucket` mislabeling, an active writer bug), and the remediation path is the 3 todos added
below (stop the writer, relabel the existing population, investigate the coincident `odds` capture stall).

- [x] ✅ [DIAG] P1. **DONE 2026-08-16 (slot-4).** Re-ran as a genuine randomized sample: `df.sample(n=50000,
      random_state=20260816)` over the full captured `batch_odds_api` population (4,281,228 cells; single bounded
      `read_availability_index_safe` read filtered to `pipeline_mode=batch_odds_api, capture_status=captured` at the
      parquet level, no new GCS walk). **Confirmed population-representative: 43,900/50,000 (87.8%) not_found** —
      close to (slightly below) the original biased 93.15% estimate, so the finding was real, not a sampling artifact.
      **Pre-growth/post-growth split as originally framed does NOT apply to this manifest**: distinct `league_id`
      count in `batch_odds_api` is FLAT at 40 in both the 2025-01-01..2025-06-30 and 2026-01-01..2026-06-30 windows (0
      new league_ids). The "51→384" growth this todo assumed drives the not_found rate lives in a DIFFERENT
      manifest/bucket (`instruments-store-sports-prd-*`, the instruments-service reference-data catalogue's ODDS
      entity — already closed GENUINE_EXPANSION, high confidence, `instruments-service@7fc96c90`), not this MTDS
      tick-data manifest.
      **Root cause identified instead** (via a targeted GCS prefix spot-check, not a new corpus walk): 3,700,051 of
      4,281,228 captured cells (86.4%) carry `data_type=odds_horizon_bucket` — a data_type with NO registered raw
      vendor source (UAC `SOURCE_PRIORITY[('sports','ODDS_HORIZON_BUCKET')]` names only the MDPS-derived source; see
      the already-open `pipeline_e2e_check.py` enumeration todo in `sports_satellite_ao_dispatch_batch9_2026_08_04.md`
      — that todo is about a diagnostic script's enumeration; THIS finding is that the production writer itself is
      still emitting the bad rows). Spot-checking 5 `odds_horizon_bucket` not_found cells against their exact GCS
      prefix confirmed the real objects at that (date, venue, league_id) location exist under
      `data_type=odds`/`data_type=trades`, never `data_type=odds_horizon_bucket` — the one sampled cell with
      `data_type=odds` resolved cleanly (`found=True`). 86.4% ≈ the measured 87.8% not_found rate — this single
      mislabeling explains essentially the entire phenomenon. The `odds_horizon_bucket` rows span 2020-06-06 through
      **2026-08-15 (yesterday)** — an ACTIVE, ONGOING writer bug, not a one-time historical artifact.
      **Second, separate observation**: real `data_type=odds` captures stop at **2026-07-26** (527,541 rows total,
      same date as this doc's original "3 weeks prior" baseline) — genuine raw odds capture may have gone silent
      exactly when `odds_horizon_bucket` volume started exploding. Filed as its own todo below, not yet root-caused.
      **Verdict: NOT a league_id-seeding artifact.** The not_found rate is a `data_type` mis-write (an honest-absence
      Class 2/3-shaped violation per `honest-absence-downstream-handling.md` — `capture_status=captured` recorded for
      a data_type that structurally cannot have a backing raw parquet under this pipeline_mode), unrelated to the
      catalogue-side league_id count growth. Evidence: `market-tick-data-service@2dec315fd0`
      (`scripts/measure_odds_api_not_found_rate_randomized_2026_08_16.py`); full spot-check transcript in this
      session's Progress Log entry below. Source: this doc + `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s
      league_id-growth todo (now known to be unrelated to this finding).
- [x] ✅ [CODE] P0. **DONE 2026-08-16 (slot-18, `backend_engineer`) — market-data-processing-service@3ae762e725, NOT
      market-tick-data-service.** **Correction to this todo's own framing**: the offending call site was never in
      MTDS — a full grep of `market_tick_data_service/` (package code, not one-off `scripts/`) found zero live
      `record_captured` callers for `odds_horizon_bucket`; every hit was a comment or a migration script. The real
      writer is MDPS's sports candle pipeline (`bucket_assignment_adapter.py`'s
      `SportsBucketAssignmentAdapter`/`canonical_writer.py`'s `write_candle_parquet`), which resolves its manifest
      `pipeline_mode` via `resolve_pipeline_mode_from_source(blob_path)` — the RAW upstream ODDS_API tick file's own
      mode — and threads that SAME value through to its OWN derived-candle output, even though
      `odds_horizon_bucket`'s registered `SOURCE_PRIORITY` source (`mdps_odds_horizon_bucket`) already has a
      dedicated closed-set `PipelineMode` triple (`BATCH_/LIVE_/REPLAY_MDPS_ODDS_HORIZON_BUCKET`, defined in UAC)
      that the live write path simply never used — confirmed by a standalone repair script
      (`market-data-processing-service/scripts/reprocess_sports_odds.py`) already writing the CORRECT dedicated mode,
      proving the intended target was known but never wired into production. Fix: added
      `resolve_output_pipeline_mode(source_data_type, pipeline_mode)` (`canonical_writer_shaping.py`) and called it at
      both write choke points — `write_candle_parquet` (covers the eager `_write_candles` path AND the
      chain-bundle path, both funnel through it) and `_streaming_write_one_group`
      (`live_workers_streaming.py`, the streaming path) — remapped BEFORE any path/manifest use so path==manifest
      stays true by construction; every other `source_data_type` passes through unchanged (verified via unit tests,
      `TestResolveOutputPipelineMode` in `tests/unit/test_canonical_writer_utility_functions.py`). `quality-gates.sh`
      green. **Not yet done**: a fresh manifest read confirming zero NEW `(pipeline_mode=batch_odds_api,
      data_type=odds_horizon_bucket, capture_status=captured)` rows past this fix's deploy timestamp — needs the fix
      live in production for at least one capture cycle first; tracked as a follow-up below.
- [x] ✅ [DIAG] P2. **DONE 2026-08-17 (slot-13).** Deploy-timing verdict (not yet a manifest-evidence verdict — the
      fixed code has not run through a live capture cycle yet, see below): `3ae762e725` (committed
      2026-08-16T23:19:50Z) is a confirmed ancestor of HEAD; it reached `main` via promote commit `bc55b99b`
      (2026-08-17T02:54:47Z) and the corresponding Artifact Registry image
      (`market-data-processing-service:bc55b99,0.30.4`, built/pushed 2026-08-17T02:58:33Z) is now the `:latest` tag
      the Cloud Run Job `uts-prod-mdps-odds-horizon-bucket` (region `asia-northeast1`, project
      `central-element-323112`) resolves at execution time. **However**, that job's most recent execution
      (`uts-prod-mdps-odds-horizon-bucket-n24lc`, ran 2026-08-17T01:15:07Z–01:16:16Z) completed BEFORE the fixed image
      became `:latest` at 02:58:33Z — it ran against the PRIOR image (`ba13a3b`, built 2026-08-16T21:08:55–22:18:58Z,
      itself before the fix commit) and therefore still carries the phantom-`pipeline_mode` bug. The job runs on a
      ~24h cadence (prior executions: 2026-08-13/14/15/16 all ~01:15Z) — **the fix has NOT yet run through any live
      capture cycle**; the earliest opportunity is the next scheduled execution (~2026-08-18T01:15Z). Manifest
      evidence (zero new phantom rows / new rows under the dedicated MDPS mode) is therefore not yet obtainable and is
      deferred to the follow-up todo below, per this todo's own "or names the reason it isn't yet" done-condition.
      Evidence: `git merge-base --is-ancestor 3ae762e725f5ac5e912a532614c4921ea6145bff HEAD` (true);
      `gcloud artifacts docker images list ... --include-tags` (bc55b99/0.30.4/latest, 2026-08-17T02:58:33);
      `gcloud run jobs executions list --job=uts-prod-mdps-odds-horizon-bucket` (last run 2026-08-17T01:15:07Z, prior
      to the fix landing as `:latest`).
- [x] ✅ [DIAG] P2. **DONE 2026-08-22 (D2 fresh-precondition-check side-finding).** A fresh, column-projected,
      bounded manifest read (no new GCS walk) confirms BOTH expected halves of this todo's done-condition: **ZERO**
      rows remain under `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket, capture_status=captured)`
      (population count = 0, down from ~3.75M), and a NEW dedicated mode `pipeline_mode=
      batch_mdps_odds_horizon_bucket` now carries **109,312** captured rows — exactly the dedicated MDPS mode the
      writer fix (`market-data-processing-service@3ae762e725`) was built to route to. Verdict: the fix is confirmed
      LIVE in production and correctly routing new writes; the historical phantom population is gone (removed, not
      migrated — see the resolved `[DATA][OPERATOR]` todo below for why removal-not-relabel was correct: the real
      data already existed under `data_type=odds` at the same shard key). Evidence:
      `market-tick-data-service/scripts/fresh_precondition_check_d2_odds_2026_08_22.py` (read-only, safe to re-run);
      raw counts also recorded in the Progress Log entry below.
- [x] ✅ [DATA] P1. **DONE 2026-08-17 (slot-32, `data_engineering`).** Ran a genuine randomized, non-overlapping
      two-sample check (n=500 then n=5,000, `random_state=20260817`) over the full captured
      `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket)` population (3,745,896 → 3,746,422 rows across
      the two runs, single bounded `read_availability_index_safe` read, no new corpus walk) via
      `market-tick-data-service/scripts/probe_odds_horizon_bucket_relabel_candidates_2026_08_17.py`. Per sampled row,
      ONE bounded `list_blobs` call against the row's own `(day, venue, league_id)` shard-key prefix (no
      `data_type`/`fixture_id` filter) checks 4 candidate shapes at once: the row's own bare canonical path, a TWIN
      object at the SAME shard slot under `data_type=odds` (the slot-4 2026-08-16 spot-check hypothesis), and both a
      `fixture_id=`-scoped `odds_horizon_bucket` sibling and a `fixture_id=`-scoped `odds` sibling (the
      `fixture_id`-scoped-path-variant check this todo asked for — MTDS's raw-tick sports writer,
      `_build_sports_shard_path` in `engine/orchestrator/venue_fetch.py`, CAN shard per-fixture with a
      `fixture_id={F}/` path segment; `fixture_id` is row-level, not a manifest shard axis, so one logical manifest
      row can be backed by several fixture-scoped physical objects the bare-path check alone would miss).
      **Result: 0% bare-path found (confirms the original finding) — but 100% of BOTH samples resolve to a real twin
      object at the SAME shard key**: 98.78-99.4% via `data_type=odds` at the bare shard slot, the residual 0.6-1.22%
      via a `fixture_id=`-scoped `odds` sibling. **0% true-not-found (no candidate anywhere) in either sample.** This
      is a decisive, population-representative verdict, not a partial one: the entire ~3.75M-row population is a
      false-`captured`-status case where the real, correctly-captured data already exists — just under
      `data_type=odds`, not `odds_horizon_bucket` — consistent with the writer-fix todo's own root-cause (the RAW
      upstream tick file's `pipeline_mode`/`data_type` was threaded straight into MDPS's derived candle output
      instead of the dedicated MDPS mode).
      **Correct disposition is ROW REMOVAL, not a `capture_status` relabel** (correcting this todo's own original
      `attempted_failed` framing) — `attempted_failed` would assert the fetch failed, but the fetch succeeded and the
      data is correctly captured elsewhere under the same shard key; the `odds_horizon_bucket` row itself is the only
      defect (a phantom write of the SOURCE data_type/pipeline_mode instead of the correct MDPS-derived one), exactly
      analogous to `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL from the
      canonical" and this SAME issue doc's own earlier league_id-rekey stale-duplicate-row-removal precedent (todo 1
      above). **Proposed scoped plan (NOT executed — operator sign-off required per this todo's own gate; ~3.75M-row
      population, `market-data-tick-sports-prd-central-element-323112`)**:
      1. Re-derive the drop set fresh at execution time (not this session's sample) — every
         `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket, capture_status=captured)` row — via the
         SSOT's own "re-derive against LIVE DISK, never a stale heuristic list" rule: a phantom-looking list can go
         stale the moment something changes, so re-verify each candidate's bare path is still not_found immediately
         before drop, not from a cached list.
      2. Follow the manifest-consolidator-ssot.md "Surgical ROW REMOVAL from the canonical" recipe verbatim: PAUSE the
         bucket's consolidator Cloud Scheduler cron; SNAPSHOT the exact generation to
         `_index/snapshots/pre_odds_horizon_bucket_row_removal_<ts>.parquet`; edit at the Arrow level preserving exact
         schema (`schema_version` int64 etc.); CAS write with `if_generation_match=<snapshotted gen>`; immediately
         call `manifest_consolidator.consolidate(bucket, force=True)` in the SAME operation to re-stamp the marker
         (skipping this step is a confirmed resurrection-window bug per the SSOT); verify durability across ≥4
         consolidator cycles, not just one.
      3. No GCS object deletion needed — none of these rows have a backing object at their own claimed path (0%
         bare-path found in both samples), so this is a manifest-only edit. The real underlying data (already
         correctly captured under `data_type=odds`) is untouched.
      4. Post-removal, re-run a fresh randomized sample of the (now-empty-if-successful)
         `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket, capture_status=captured)` population to
         confirm 0 rows remain, and confirm the `data_type=odds` twin rows this removal exposes as the "real" data
         are themselves still intact (spot-check a handful post-removal).
      5. This removal is independent of, and should NOT block on, the still-open `[DIAG] P2` writer-fix-verify todo
         below (verifying the fix stops NEW phantom rows) — that todo covers future writes; this one covers the
         historical population already on disk. Both can proceed in parallel once each is individually ready.
      Evidence: `market-tick-data-service/scripts/probe_odds_horizon_bucket_relabel_candidates_2026_08_17.py`
      (read-only, safe to re-run; no manifest writes). Done when (this todo): satisfied — a concrete, reviewed
      relabel/removal plan exists covering the full ~3.75M-row population (not a subset, since the sampled
      re-check confirms the population IS uniformly a false-status case), pending operator sign-off to execute (see
      new `[OPERATOR]` todo below).
- [x] ✅ [DATA][OPERATOR] P1. **VERIFIED-ALREADY-ACHIEVED 2026-08-22 (D2 disposition execution; NOT executed by this
      session — see below).** This todo's own verification query is satisfied by the SAME fresh read documented in
      the sibling `[DIAG] P2` todo above and the sibling `[DATA][OPERATOR]` todo's evidence: a fresh, bounded manifest
      read (2026-08-22) finds **0** rows remain under `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket,
      capture_status=captured)` — down from ~3.75M — and the `data_type=odds` twin data is confirmed intact (the
      full `batch_odds_api` population, now 211,291 rows, is 100% `data_type=odds`, all spot-checked backed by real
      objects). This is EXACTLY this todo's stated done-condition ("a re-measurement confirms 0 residual rows").
      **Not executed by this session** — same audit-trail-gap caveat as the sibling todo above applies: no matching
      commit or `pre_odds_horizon_bucket_row_removal_*` snapshot was found in this repo's history to attribute the
      actual CAS write + force-consolidate to; most likely a parallel D2/D7 worker's corrective pass on this same
      shared bucket today. See the new follow-up todo below. Evidence: `market-tick-data-service@a9b1d055c9`
      (`scripts/fresh_precondition_check_d2_odds_2026_08_22.py`); full counts in the Progress Log entry below.
- [ ] [DIAG][OPERATOR] P2. Identify WHO/WHAT executed the odds_horizon_bucket + stale-duplicate row removals whose
      post-state this doc's 2026-08-22 fresh precondition check independently verified (population collapsed
      4,281,228→211,291 captured `batch_odds_api` rows, 100% `data_type=odds`, `_index/availability_index.parquet`
      last_modified=2026-08-21T23:16:42Z) — no commit in `market-tick-data-service` since 2026-08-19 and no manifest
      snapshot under either plan's own proposed naming convention explains it. Check: (a) whether a sibling D2/D7
      worker on `sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md` /
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` / the D7 the-odds-api key-rotation todo executed a broader
      corrective flip that happened to cover this population too (check those docs' own Progress Logs first); (b)
      whether the `_index/snapshots/k2_stale_twin_presync/` prefix (found during this check, unrelated naming) is
      actually connected; (c) whether a script ran uncommitted (e.g. from a `/tmp` one-off or a different repo/slot
      whose commit hasn't reached this checkout yet). Source: this doc's two now-verified-already-achieved
      `[OPERATOR]` todos above. Done when: the executing session/mechanism is identified and cited here (or, if
      genuinely unrecoverable, the manifest-write-coordination-gate SSOT `/codex/02-data/gcs-and-manifest-delete-
      safety-protocol.md` §5 is confirmed to have been satisfied by inspecting the CAS generation history, or the
      gap is explicitly accepted as unrecoverable audit-trail loss with that stated).
- [ ] [DIAG][OPERATOR] P0. **REGRESSION FOUND 2026-08-22 (D2 disposition independent re-verification, this
      session) — SUPERSEDES the "VERIFIED-ALREADY-ACHIEVED" verdict on both `[DATA][OPERATOR] P1` todos above.**
      A fresh, independent re-run of the already-committed `scripts/fresh_precondition_check_d2_odds_2026_08_22.py`
      (unmodified, new invocation, 06:52-06:54 BST) found the `batch_odds_api` captured population back at
      **4,352,441** rows (86.65% `data_type=odds_horizon_bucket`) with a fresh 1,500-row sample at **100%
      not_found** — UP from the 211,291-row / 0%-not_found state that same script measured only 6 hours earlier
      (00:57 BST, `market-tick-data-service@a9b1d055c9`), and WORSE than the original pre-cleanup peak (4,281,228
      rows / 86.4%, 2026-08-17). Root-cause this 6-hour, ~20x regrowth **before** executing either queued
      row-removal plan.
      A follow-up bounded, single-read, ad-hoc analysis this session (read-only, same `read_availability_index`
      call already used above, no new script committed given the shared host's QG queue was saturated at check
      time — reproducible via: load the manifest once, filter `pipeline_mode=="batch_odds_api"` +
      `capture_status=="captured"`, `value_counts()` on `data_type`, min/max `date` on the `odds_horizon_bucket`
      slice) found: full breakdown `{odds_horizon_bucket: 3771272, odds: 527541, odds_snapshot: 17951,
      arbitrage_opportunity: 17851, odds_movement: 17834}` (total 4,352,449, ~1-min read-skew vs the 4,352,441 above
      is expected under concurrent writes); the `odds_horizon_bucket` rows span **2020-06-06 through 2026-08-15** —
      the ENTIRE sports-odds historical range, NOT a narrow recent window, which rules out "live cron traffic
      regressed" and strongly implicates a **bulk historical replay**; the good `data_type=odds` twin data is
      confirmed intact and unaffected at exactly **527,541** rows (unchanged from every prior measurement since
      2026-07-26 — the real data was never at risk); the dedicated `batch_mdps_odds_horizon_bucket` mode (the
      writer-fix's intended destination) also grew slightly to **128,611** rows (up from 109,312), so the fix IS
      still processing some traffic, just dwarfed by whatever is replaying the full history through the unfixed
      path.
      **Leading candidate (strong, not yet confirmed)**: `mtds-backfill-odds-20260817-062648` (historical odds
      batch-backfill VM) is confirmed **RUNNING right now** (`gcloud compute instances list`) and, per its own
      sibling doc `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`, "does not stop
      on an exhausted quota" and was launched pre-dating every writer fix in this doc (never restarted, so — per
      that SAME doc's own precedent finding for a different bug on the SAME VM — it runs frozen pre-fix tarball code
      that cannot pick up the `resolve_output_pipeline_mode` remap). A full-history date range (2020-06-06 onward)
      is exactly what a "historical odds backfill" VM would touch. The shared `odds-api-key` was topped up
      2026-08-21 (D7 resolution) — this VM resuming historical fetch+write once the key started working again
      lines up with the observed 00:57→06:52 regrowth window. That same sibling doc has an OPEN
      `- [ ] [OPERATOR] P0` todo to "pause `mtds-backfill-odds-*`" that was never closed — action it as part of
      this root-cause (pausing/restarting this VM on current LDR would pick up the writer fix and should stop new
      phantom rows; it does not by itself clean the now-larger existing population, which is the separate,
      still-gated row-removal work). Rule out the alternative that the still-unattributed mechanism which performed
      the original 4.28M→211K cleanup (see the sibling `[DIAG][OPERATOR] P2` todo above) is itself lossy/
      non-idempotent before treating VM-pause as sufficient.
      Done when: the actual writer/backfill responsible is identified and (if still live) paused/fixed, and a FRESH
      re-measurement shows the `batch_odds_api`/`odds_horizon_bucket` population stable-or-shrinking (not growing)
      across ≥2 checks taken hours apart — only then should the queued row-removal plans be re-evaluated against
      the by-then-current population size. Evidence: re-run of the already-committed
      `market-tick-data-service@a9b1d055c9` (`scripts/fresh_precondition_check_d2_odds_2026_08_22.py`, no code
      change) + an ad-hoc uncommitted bounded read this session (exact query above, reproducible) +
      `gcloud compute instances list --filter="name~mtds-backfill-odds"` (RUNNING, live at check time).
- [ ] [DATA][OPERATOR] P1. **WITHHELD 2026-08-22 (D2 disposition execution, this session) — precondition FAILED on
      fresh re-check, action NOT executed.** Per the D2 dispatch's own instruction ("if the precondition fails,
      WITHHOLD the action and record gate-failed-withheld with the measured value"): the precondition for treating
      either queued row-removal recipe as a safe, bounded, historical-cleanup-only edit was the population already
      being at the claimed clean post-state (211,291 rows / 0% not_found per the 00:57 BST check). The 06:52 BST
      fresh re-check falsifies that (4,352,441 rows / 100% not_found sample — see the `[DIAG][OPERATOR] P0` todo
      above). Do NOT execute either recipe (league_id-rekey stale-duplicate removal, or odds_horizon_bucket
      removal) until that root-cause todo is resolved — the retention half of the precondition still independently
      passes (`gcs_bucket_soft_delete_retention_seconds` = 604800s, ≥7d) but is moot while the "already clean"
      premise does not hold. Measured (withheld) value: `batch_odds_api` captured population = 4,352,441.
- [x] ✅ [DIAG] P2. **DONE 2026-08-17 (slot-6, `infra`).** Verdict: **NOT a capture outage — a silent
      MANIFEST-RECORDING gap** while the real fetch/write keeps succeeding. Evidence:
      1. **GCS write side is live, right now.** `uts-prod-sports-scheduler` (Cloud Run Job, `*/5 * * * *`,
         confirmed via `gcloud scheduler jobs describe` + `gcloud run jobs executions list`, all recent runs
         `succeededCount=1`) fires fixture-proximate `odds_t*` triggers (`odds_t24h`…`odds_t1h`) that dispatch
         `uts-prod-market-tick-data-service-fast-t1-recon`. Its live logs (execution
         `uts-prod-market-tick-data-service-fast-t1-recon-jwrqq`, 2026-08-17T00:06-00:07Z, ~15 min before this
         investigation) show `Odds API batch complete: date=2026-08-17 leagues=MLS rows=2591 credits_used=780`
         followed by dozens of `StreamingParquetWriter: uploaded …` lines writing real objects to
         `market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=2026-08-17/
         pipeline_mode=batch_odds_api/asset_group=sports/venue={V}/league_id=MLS/fixture_id={F}/
         instrument_type=odds/data_type=odds/ticks.parquet` — the raw ODDS_API vendor fetch is alive and paid
         (`remaining=2811392` credits).
      2. **The manifest has recorded zero rows for this exact shard since 2026-07-26**, confirmed via a fresh
         `read_availability_index` read (single bounded read, no GCS walk) against the freshly-consolidated index
         (`_index/availability_index.parquet`, GCS `updated=2026-08-17T11:09:37Z` — the consolidator itself is
         healthy and current, ruling out "stale index" as the cause): 527,541 `(pipeline_mode=batch_odds_api,
         data_type=odds, capture_status=captured)` rows total, max `date=2026-07-26`, 0 rows on/after 2026-07-27.
         Sibling `batch_odds_api` data_types (`odds_snapshot`, `odds_movement`, `arbitrage_opportunity`,
         `odds_horizon_bucket`) DO have fresh rows through 2026-08-17 — only the raw `data_type=odds` /
         `fixture_id=`-scoped shard is affected.
      3. **Correlates with, but is not resolved by, the 2026-08-09 fixture_id-routing fix**
         (`market-tick-data-service@cf855ff0`, `sports_odds_af_shard_reconciliation_defect_2026_08_09.md`) —
         `manifest_finalize.py`'s `_write_shard_counts_to_manifest` now correctly routes the fixture_id through
         `underlying_key`→`fixture_id` for `(itype_key=="odds", data_type_key=="odds")` shards, and this fix IS
         live in the currently-deployed image (`market-tick-data-service:latest`/`0.143.2`, built
         2026-08-17T10:32:03Z, i.e. hours after this investigation's own log evidence above — confirming the
         fix-bearing code was already the one running when the jwrqq execution wrote those objects). Yet a direct
         manifest query for ANY row with a non-empty `fixture_id` column (the fix's own signature) finds max date
         **2026-06-09** — i.e. not one fixture-scoped manifest row has EVER landed since the fix shipped, despite
         the write path visibly executing (evidence #1). The gap is therefore downstream of `venue_writer.add(...)`
         itself (no per-shard exception isolation exists at that call site per the code's own comment, and the job
         exits 0/succeeded, so it is not a raised-and-swallowed exception either) — most likely in the
         `_ManifestWriterPool` flush/close path or a consolidator-side collapse of the fixture-scoped row into an
         earlier bare-path row's dedup key. Not root-caused further in this session (out of this todo's DIAG scope).
      Verdict: **real capture is LIVE, not stalled** — but manifest coverage for `data_type=odds` has been
      **silently lying (false-negative absence) since 2026-07-26**, a `honest-absence-downstream-handling.md`
      Class-1-shaped violation (in-flight write success, no manifest marker) rather than the Class-3/false-
      `captured` pattern this doc's earlier todos found for `odds_horizon_bucket`. Follow-up filed below.

- [x] ✅ [CODE] P1. **DONE 2026-08-17 (slot-11, `infra`) — `market-tick-data-service@03cf5a20f4`.** Root cause: NOT
      the `_ManifestWriterPool` flush/close lifecycle — it's a consolidator-side dedup collapse, and the collapse is
      BY DESIGN for the wrong key. `unified_trading_library.manifest_consolidator`'s dedup key
      (`_BASE_DEDUP_COLS` + present `_OPTIONAL_DEDUP_COLS`) is `(date, venue, data_type, service_name[, league_id])`
      — **`fixture_id` is deliberately NOT a dedup-key column** (it's a display/row-level axis; the sports shard atom
      is `(bookmaker=venue, league_id, day)`, not per-fixture). Meanwhile
      `sentinels.py::_emit_sports_v2_sentinels` fans out one honest-absence sentinel row per
      `(bookmaker, league_id, fixture_id)` triple from the catalog, and only skipped emission when that EXACT triple
      was already in `captured_sports_shards` — it did NOT check the coarser `captured_sports_league_pairs` set
      (bookmaker+league only, already computed and already used elsewhere in the same file, e.g. the off-season-
      leagues loop and the sibling `_emit_sports_v1_sentinels`). So for any `(bookmaker, league)` pair where fixture A
      was genuinely captured but fixture B was not, the per-fixture-B sentinel row shared its dedup key with
      fixture A's real captured row for the same cell — and last-write-wins consolidation silently overwrote the
      captured row with the sentinel's honest-absence one, i.e. the exact "GCS write succeeds, manifest shows
      nothing" symptom this doc's DIAG P2 todo measured. **Fix**: added the missing coarser skip check
      (`if (bm, _canon_lid) in captured_sports_league_pairs: continue`) right after the existing exact-triple skip in
      `_emit_sports_v2_sentinels`, reusing the pre-existing set — no new computation, no schema change. New
      regression test `test_emit_sports_v2_sentinels_skips_uncaptured_fixture_when_league_pair_captured` in
      `tests/unit/engine/test_sentinels_coverage.py` asserts 0 sentinel rows emitted (and no downstream
      writer/coverage-check calls) when one fixture in a league pair is captured and a sibling fixture is not.
      `quality-gates.sh` green end-to-end (full suite, `EXITCODE=0`, zero ❌ gate failures) before commit. Pushed via
      quickmerge, post-push ancestry verified — `market-tick-data-service@03cf5a20f4` is an ancestor of
      `origin/live-defi-rollout`. **Live-production confirmation is a separate, genuinely time-gated step — see the
      new `[DIAG]` follow-up todo below** (cannot be done in this session: needs the fix to actually reach the
      deployed image and at least one real ~5-min capture cycle to elapse afterward).
- [x] ✅ [DIAG] P2. **DONE 2026-08-20 (slot-17, `infra`). Verdict: STILL STALE — but with a NEW ROOT CAUSE identified
      (the todo's own "if still 0, identify a new root cause" branch).** Fix `market-tick-data-service@03cf5a20f4` IS
      deployed (confirmed ancestor of `origin/live-defi-rollout`; the fast-t1-recon job's `:latest` image is `0.146.5` /
      digest `e00fc61`, built 2026-08-20T14:44:10Z, weeks after the 2026-08-17T12:14 fix commit — the fix-bearing code
      has been running capture cycles since 08-18). Yet the fresh bounded read
      (`scripts/verify_odds_manifest_recording_fix_live_2026_08_20.py`,
      `read_availability_index_safe` filtered to `pipeline_mode=batch_odds_api, data_type=odds,
      capture_status=captured`) returns **0 rows past the pre-fix baseline**: `total_captured_rows=527,541`,
      `max_date=2026-07-26` (identical to the pre-fix max), `rows_past_baseline=0`, `fixture_scoped_rows=0` — verdict
      `STILL_STALE_OR_PARTIAL`. **New root cause (verified via two companion diagnostics, `market-tick-data-service@
      e45a49bf`): the `batch_odds_api` manifest surface has gone entirely silent — a broad
      `pipeline_mode=batch_odds_api` read (any data_type, any capture_status) shows **zero rows dated after
      2026-08-15** (`max_date_all=2026-08-15`), while the consolidator is healthy (`_index/latest.json` `rows_in=0`,
      `verdict=empty`, last run 2026-08-20T14:50:44Z — NOT a stale-index artifact), and on-disk GCS objects under
      `raw_tick_data/by_date/day=…/pipeline_mode=batch_odds_api/` stop after 2026-08-17 (44 objects on 08-17, **0 on
      08-18/19/20**). **The sports odds capture has MOVED its manifest recording to
      `pipeline_mode=live_odds_api`**: the 2026-08-16..08-20 window read shows live_odds_api carrying `odds|captured`
      (7,851 rows, max 08-16) + `odds|empty_confirmed` (31,664 rows, max 08-20) — the live leg is still recording
      honest-absence through yesterday. So the sentinel dedup-collapse fix (03cf5a20f4) did resolve the *sentinel
      clobbering* mechanism it targeted, but it does NOT restore `batch_odds_api` captured rows because that
      pipeline_mode is no longer the surface where raw odds captures land — the batch label appears retired/superseded
      by the live path, and the batch surface's last write predates even the fix deploy. **⚠️ PARTIAL-CORRECTION
      (2026-08-20, slot-17, DIAG P1 resolution below):** the "moved to live_odds_api / batch retired" framing was
      WRONG. `live_odds_api` is a LONG-STANDING, ratified, separate surface (manifest rows since 2026-06-21; real
      `odds_api_ws` WSFeedConnector + UAC `LIVE_ODDS_API` PipelineMode), not a new migration destination. The
      `batch_odds_api` surface is silent because the fast-t1-recon batch job (`--mode batch --asset-group SPORTS
      PREDICTION`) is failing the-odds-api with **HTTP 401 Unauthorized since 2026-08-18** (0×401 on 08-15/16/17 → 2×
      08-18 → 500× 08-19 → 337× 08-20 in job logs; last working fetch 08-17, per slot-6 evidence) — a CREDENTIAL
      failure (expired/revoked the-odds-api key), NOT a routing migration and NOT the sentinel bug. Follow-up filed
      below.
- [x] ✅ [DIAG] P1. **DONE 2026-08-20 (slot-17, `infra`). Verdict: NOT a routing migration, NOT a writer regression —
      the `batch_odds_api` surface is silent because the-odds-api returns HTTP 401 (credential failure) since
      2026-08-18.** Answers to the three questions: (1) **`live_odds_api` is the SANCTIONED long-standing surface, but
      it is NOT a migration destination from `batch_odds_api`** — both are ratified, closed-set PipelineModes
      (`pipeline_mode-partition.md`; UAC `PipelineMode.BATCH_ODDS_API` + `.LIVE_ODDS_API`), and `live_odds_api` has
      carried `data_type=odds` manifest rows continuously since **2026-06-21** (long before any of this window), backed
      by a real `odds_api_ws` WSFeedConnector. The fast-t1-recon job is `--mode batch --asset-group SPORTS PREDICTION`
      (`deployment-service/terraform/gcp/audit03_cron_provisioning.tf`) and writes `batch_odds_api`; nothing routes
      batch captures to the live label. (2) **`live_odds_api` `odds|captured` stopping at 08-16 is an EXPECTED
      off-season/quiet-odds gap, NOT the sentinel persistence bug recurring** — the live leg is healthy and continues
      recording `odds|empty_confirmed` through 08-20 (31,664 rows, max 08-20), i.e. the live path polls, finds no
      playable odds on those days, and records honest absence; captured rows require actual odds to exist. (3)
      **`batch_odds_api` DOES still have a writer — the fast-t1-recon batch job — and it is FAILING, not absent**:
      its 08-20T01:42 logs show `ERROR Venue ODDS_API: unexpected error (shard isolated): 401, message='Unauthorized',
      url='https://api.the-odds-api.com/v4/historical/sports/soccer_usa_mls/odds?apiKey=5634d6f10…'` →
      `Processed date=2026-08-20: 0 venues ok, 1 failed … 0 total records` + `SHARD_INCOMPLETE`. 401-count by day in
      the job's logs: **0 (08-15/16/17) → 2 (08-18) → 500 (08-19) → 337 (08-20)** — the key authenticated through
      08-17 (slot-6's `credits_used=780, remaining=2811392` evidence) and began failing 08-18. **Root cause of the
      still-open batch gap: the-odds-api API key is unauthorized/expired since 2026-08-18.** This also explains why
      the DIAG P2's "still stale after the sentinel fix" verdict held: 03cf5a20f4 (sentinel dedup-collapse) was
      correctly deployed, but no captured rows can land while the vendor rejects the key with 401. Fix todo filed
      below. Evidence: `market-tick-data-service@3d420cde` (diag scripts) + `gcloud logging read` on
      `uts-prod-market-tick-data-service-fast-t1-recon` (401 counts + shard-isolated error lines).
- [x] ✅ [OPERATOR][CODE] P1. Rotate/replace the the-odds-api.com API key (HTTP 401 Unauthorized since 2026-08-18) in GCP
      Secret Manager (`odds-api-key`, per `MarketDataProviderConfig.odds_api_secret_name`), then re-verify a fresh
      `(pipeline_mode=batch_odds_api, data_type=odds, capture_status=captured)` manifest read lands new rows with
      `date` past the rotation time (pre-failure max was 2026-07-26, objects stopped 08-17, 401s since 08-18).
      Operator-gated: the key is a vendor credential held in Secret Manager. Source: this doc's now-resolved [DIAG] P1
      verdict above (root cause = credential failure, not routing/writer). Done when: a new key is in place (or the
      existing one is re-authorized), the fast-t1-recon job logs show 0×401 on a fresh run, and a bounded manifest
      read confirms new `batch_odds_api/odds/captured` rows landing past the rotation time (or the residual is
      explained). **RESOLVED 2026-08-21 (D7 operator ruling, see
      `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`)**: key confirmed
      re-authorized/topped-up — live probe
      `GET /v4/sports` returns `x-requests-remaining=22,489,366` (was 15M/15M exhausted). `uts-prod-market-tick-
      data-service-fast-t1-recon` job logs for the 2026-08-21T22:00-23:05Z window show **0×401** across several
      completed executions (`succeededCount=1`) — confirms the credential-failure root cause is resolved. The
      fresh-captured-rows manifest re-verification was attempted but the bounded read hit a GCS download timeout
      (`RetryError: Timeout of 120.0s exceeded ... IncompleteRead`) on the large availability index — not
      completed this session; the residual is explained by the download timeout, not a persisting credential
      issue (0×401 evidence stands independently). Also bounded the batch consumer itself this same session so
      this credential-exhaustion class cannot recur the same way — see
      `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`'s Progress Log
      (`market-tick-data-service@5ac0a32149`).

## Progress Log

**2026-08-22 (D2 disposition execution — independent re-verification finds a REGRESSION, this session)** —
dispatched against operator disposition D2 for this same doc (a re-dispatch; the entry immediately below this one
shows a prior same-day session already ran this exact precondition-check-before-execute flow ~6h earlier). Rather
than trusting this doc's own "VERIFIED-ALREADY-ACHIEVED" claims, re-ran the FRESH precondition per the dispatch's
own instruction: re-executed the identical, unmodified, already-committed `scripts/fresh_precondition_check_d2_odds_
2026_08_22.py` (06:52:24-06:54:59 BST) and found the claimed clean post-state does **NOT hold** — `batch_odds_api`
captured population is back at **4,352,441** rows (86.65% `data_type=odds_horizon_bucket`, up from 211,291/0% six
hours earlier at 00:57 BST), and a fresh 1,500-row `gcs_describe_object` sample of `odds_horizon_bucket` rows found
**100% not_found** (up from 0%) — WORSE than the original pre-cleanup peak (4,281,228/86.4%, measured 2026-08-17).
First confirmed this is a real regrowth and not a stale/fabricated read: the prior session's commits
(`aabaa3effe1`, `d552a9b21b`, `a9b1d055c9`) are real, already on `origin/live-defi-rollout`, and this doc's own
working tree was clean at that HEAD (`git log`/`git status` verified) — the earlier "already achieved" measurement
was genuinely correct AT THE TIME, it has since regressed. Soft-delete retention re-confirmed independently
(604800s, unchanged, qualifies — moot while the "already clean" premise fails). Ran a follow-up bounded, ad-hoc
read-only analysis (same manifest-read primitive, no new GCS walk) which found: the `odds_horizon_bucket` rows span
the FULL historical range **2020-06-06 to 2026-08-15** (not a narrow recent window — rules out "live cron
regressed," implicates a bulk historical replay); the good `data_type=odds` twin data is unaffected at exactly
527,541 rows (unchanged since 2026-07-26); the dedicated `batch_mdps_odds_horizon_bucket` mode (the writer-fix's
intended destination) grew slightly to 128,611 (up from 109,312) so the fix is still processing some traffic, just
dwarfed by the regrowth. This ad-hoc analysis was NOT committed as a new script — the shared host's QG queue was
saturated (host-wide concurrency cap fully busy with ~5+ other slots' full `quality-gates.sh` runs, 8+ min queued
with no sign of clearing) and an open-ended wait risked losing the whole result if the session ended mid-queue, so
the exact reproducible query is documented inline in the todo below instead of shipped as source; the CORE finding
(population count + not_found sample) remains fully evidenced by the already-committed, unmodified
`fresh_precondition_check_d2_odds_2026_08_22.py`, just re-run. Cross-referenced the sibling `dp_live_004_sports_
odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` doc and confirmed via live `gcloud compute instances
list` that `mtds-backfill-odds-20260817-062648` (a historical odds batch-backfill VM that doc already documents as
"does not stop on an exhausted quota" and running pre-fix frozen tarball code) is still **RUNNING** right now — a
strong, not-yet-confirmed candidate: the shared odds-api-key was topped up 2026-08-21 (D7), which would let this
never-restarted VM resume full-history fetch+write exactly on the observed 00:57→06:52 timeline, and that doc has
its own still-open, never-closed `[OPERATOR] P0` "pause `mtds-backfill-odds-*`" todo. **Did not execute either
row-removal plan** — WITHHELD per the dispatch's own gate-failure instruction ("if the precondition fails, WITHHOLD
the action and record gate-failed-withheld with the measured value"); executing a CAS rewrite against an
actively-regrowing ~3.77M-row population would race whatever is rewriting it and risks masking/losing evidence of
the live regression, and is VM-scale regardless of the regression (laptop-session heavy-I/O rule). Filed a new
`[DIAG][OPERATOR] P0` root-cause todo (supersedes the "already achieved" verdict, does not overwrite the historical
`[x]` record of what was true 6h earlier) and a `[DATA][OPERATOR] P1` WITHHELD todo recording the gate failure with
its measured value. Bumped doc `priority` P1→P0 and added a top-of-doc regression banner. Added the
`dp_live_004_...` doc to `context_scope`. **This is a big finding per workspace HARD RULE** (active data-correctness
regression, cross-repo MTDS/MDPS, directly contradicts this same doc's own same-day-6-hours-earlier verified claim)
— flagged for operator visibility in this session's report in addition to this entry. **Operational note on this
checkout's contention**: this same doc edit was made once already this session and was found REVERTED to HEAD
moments later (working tree returned fully clean, no diff vs HEAD, no matching content in the 2 most recent
autostash entries either) — this shared `.tabs/6/unified-trading-pm` checkout shows 100+ accumulated autostash/
pre-reconcile-quarantine entries from concurrent sessions, confirming heavy multi-session contention on this exact
checkout; re-applied the edit and am shipping it immediately via `safe-doc-push.sh` (isolated-worktree commit) to
close the vulnerability window rather than leaving it sitting uncommitted. Evidence: re-run of
`market-tick-data-service@a9b1d055c9` (unmodified) + `gcloud compute instances list
--filter="name~mtds-backfill-odds"`.

**2026-08-22 (D2 disposition execution)** — took `sports_mdt_odds_captured_cells_not_found_rate_2026_08_16.md` as
`affected_docs[1]` of operator disposition D2 (`.ao_checkpoints/issues_corpus_completion_2026_08_21/dispositions.json`,
"Manifest/GCS correction batch", OPERATOR-RULED 2026-08-21 — approved all under each item's stated precondition).
This doc carried two `[DATA][OPERATOR] P1` manifest-row-removal execution todos gated on sign-off. Wrote
`market-tick-data-service/scripts/fresh_precondition_check_d2_odds_2026_08_22.py` (read-only) to re-run each item's
precondition FRESH before executing: (1) `gcs_bucket_soft_delete_retention_seconds` on
`market-data-tick-sports-prd-central-element-323112` = 604800s (≥7d, qualifies — relevant because the manifest
`_index` blob these plans would CAS-rewrite is itself subject to the same overwrite-retention mechanism); (2) a fresh
sample re-derivation of both drop sets. The fresh read found the target post-state of BOTH plans **already reached**:
captured `batch_odds_api` population is now 211,291 rows (was 4,281,228 on 2026-08-17), 100% `data_type=odds` (0
`odds_horizon_bucket` rows remain, down from ~3.75M; 0 residual stale-duplicate rows of any other data_type), and a
fresh `gcs_describe_object`-backed sample (n=1500, seed=20260822) found 0/1500 (0%) not_found — down from the
87.65-93.15% repeatedly measured 2026-08-16/17. A broader unfiltered read also found a NEW dedicated
`pipeline_mode=batch_mdps_odds_horizon_bucket` now carrying 109,312 rows — confirming the `market-data-processing-
service@3ae762e725` writer fix (shipped 2026-08-16) is live and correctly routing new writes, closing this doc's
still-open `[DIAG] P2` fix-verification todo as a side-effect. Investigated who executed the actual removals before
crediting them: no commit in `market-tick-data-service` since 2026-08-19 matches (local HEAD confirmed == freshly-
fetched `origin/live-defi-rollout`), and no manifest snapshot exists under either plan's own proposed naming
convention (only an unrelated `_index/snapshots/k2_stale_twin_presync/` prefix). The `_index/availability_index.
parquet` blob's `last_modified` (2026-08-21T23:16:42Z) sits immediately after a `_index/latest.json` run logging
`rows_in=0/rows_out=0` (a no-op incremental merge) — the actual rewrite landed in an earlier write outside this
session's own visibility, most likely a parallel worker on one of this same batch's sibling sports docs (heavy
concurrent activity on this exact bucket is independently evidenced by the D7 the-odds-api key-rotation todo's
2026-08-21 resolution in this same doc). **Did not re-execute either removal** — the population is already clean;
re-running against it would be a no-op at best and risks racing a possibly-still-in-flight sibling writer (the exact
hazard the manifest-write-coordination-gate in `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §5
exists to prevent). Flipped both `[DATA][OPERATOR] P1` todos to done (VERIFIED-ALREADY-ACHIEVED, citing the fresh
measured evidence per each todo's own stated verification query), flipped the `[DIAG] P2` fix-verify todo to done,
and filed a new `[DIAG][OPERATOR] P2` follow-up to identify the actual executing mechanism (not blocking — the
outcome is independently verified correct; only the provenance trail is missing). Script committed + landed on
`live-defi-rollout`: `market-tick-data-service@a9b1d055c9` (post-push ancestry verified).

**2026-08-21 (D7 operator ruling execution)** — closed the [OPERATOR][CODE] P1 key-rotation todo. Probed the live
`odds-api-key` (GSM + `GET /v4/sports`): `x-requests-remaining=22,489,366` (was 15M/15M exhausted) — operator's
top-up confirmed landed. `uts-prod-market-tick-data-service-fast-t1-recon` job logs for 2026-08-21T22:00-23:05Z show
0×401 across several successful executions. Attempted the fresh-captured-rows manifest re-verification; the bounded
read hit a GCS download timeout on the large availability index (not a credential issue) — not completed this
session, but the 0×401 evidence independently confirms the credential root cause is resolved. Also shipped a bound
on the batch consumer itself (`market-tick-data-service@5ac0a32149`, `RESERVED_LIVE_CREDIT_FLOOR` +
`MAX_CREDITS_PER_RUN`) so this exact quota-exhaustion class cannot recur the same way — full detail in
`dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`'s Progress Log.

**2026-08-20 (slot-17, `infra`)** — closed the [DIAG] P1 todo (batch_odds_api → live_odds_api "migration"
classification). Verdict: **NOT a migration, NOT a writer regression — the-odds-api credential failure (HTTP 401
since 2026-08-18)**. `live_odds_api` is a long-standing (manifest rows since 2026-06-21) ratified surface with a real
`odds_api_ws` connector — not a new destination. The fast-t1-recon job (`--mode batch --asset-group SPORTS
PREDICTION`, terraform `audit03_cron_provisioning.tf`) is the `batch_odds_api` writer and is FAILING: its logs show
`ERROR Venue ODDS_API: unexpected error (shard isolated): 401 Unauthorized … api.the-odds-api.com/…/soccer_usa_mls/odds`
→ `0 venues ok, 1 failed, 0 total records` + `SHARD_INCOMPLETE`. 401-count by day in job logs: 0 (08-15/16/17) → 2
(08-18) → 500 (08-19) → 337 (08-20); the key authenticated through 08-17 (slot-6 credits evidence) and began failing
08-18. Corrected my own P2 annotation's "moved to live_odds_api / batch retired" framing (it was wrong — the surface
is credential-blocked, not retired). The sentinel fix (03cf5a20f4) is deployed but can't land captured rows while the
vendor rejects the key. New [OPERATOR][CODE] P1 fix todo filed (rotate/replace the-odds-api key + re-verify). Evidence:
`market-tick-data-service@3d420cde` + `gcloud logging read` on the fast-t1-recon job.

**2026-08-20 (slot-17, `infra`)** — closed the last open `[DIAG] P2` todo (fix-live verification). Confirmed
`market-tick-data-service@03cf5a20f4` is deployed: ancestor of `origin/live-defi-rollout`; the fast-t1-recon Cloud Run
Job's `:latest` image is `0.146.5`/digest `e00fc61`, built 2026-08-20T14:44:10Z (the fix commit is 2026-08-17T12:14Z),
and the job has been executing successfully through today (executions 2026-08-20T01:40Z, status succeeded). Re-ran a
fresh bounded `read_availability_index_safe` read for `(pipeline_mode=batch_odds_api, data_type=odds,
capture_status=captured)`: **STILL STALE** — 527,541 total rows, max `date=2026-07-26`, 0 rows past baseline, 0
fixture-scoped rows. Then root-caused WHY the fix didn't restore the surface: a broad `batch_odds_api` read (any
data_type/status) shows **zero rows dated after 2026-08-15**; the consolidator is healthy (`latest.json` rows_in=0,
verdict=empty, 2026-08-20T14:50:44Z); on-disk objects under `…/pipeline_mode=batch_odds_api/` stop after 08-17 (44 on
08-17, 0 on 08-18/19/20). The odds capture has moved its manifest recording to `pipeline_mode=live_odds_api`
(2026-08-16..20 window: `odds|captured` 7,851 max 08-16; `odds|empty_confirmed` 31,664 max 08-20). New [DIAG] P1
follow-up filed (intended-vs-regression classification). Scripts: `market-tick-data-service@e45a49bf`
(`verify_odds_manifest_recording_fix_live_2026_08_20.py` from the prior session's commit 39949d24, plus
`diag_odds_manifest_landing_2026_08_20.py` + `diag_sports_recent_days_2026_08_20.py`), all read-only.

**2026-08-16 (slot-30, `data_engineering`)** — filed while working `sports_satellite_ao_dispatch_batch9-010`. Measured
93.15% not_found rate on a 50,000-cell (non-randomized) sample; corpus grew 275,136→4,240,790 captured `batch_odds_api`
cells since 2026-07-26. Did not root-cause; handed to the existing league_id-growth todo with concrete supporting
numbers and a proposed randomized re-measurement.

**2026-08-16 (slot-9, `data_engineering`)** — resolved both open P1 todos. Randomized 50,000-cell sample (seed
20260816) confirmed 87.65% not_found population-wide, but the cross-tab REFUTED the seeding-artifact-causes-not_found
hypothesis (pre-growth league_ids 87.90% not_found vs post-growth 42.34% — inverse of predicted). Separately measured
current distinct ODDS league_id count at only 68 (down from the 384 peak), confirming the 51→384 growth WAS a
seeding/duplicate artifact largely already consolidated by the 2026-08-04 `canonicalize_sports_league_id_schema
--apply` re-key. A bounded twin-check (in-memory, no extra GCS calls) then found the TRUE root cause: 98.67% of
not_found rows have a `captured` twin under a different (canonical) league_id for the same (date, venue, data_type) —
these are stale duplicate manifest rows left over from the rekey, not lost data. Corrected the originally-proposed
`attempted_failed` relabel to a row-REMOVAL plan (the twin already carries the real data). New `[OPERATOR]` execution
todo filed, gated on sign-off. Script:
`market-tick-data-service/scripts/measure_odds_not_found_rate_randomized_2026_08_16.py` (read-only, safe to re-run).
**2026-08-16 (slot-4, review-role worker, todo 1)** — closed todo 1. Wrote
`market-tick-data-service/scripts/measure_odds_api_not_found_rate_randomized_2026_08_16.py`
(`market-tick-data-service@2dec315fd0`), a genuine `df.sample(n=50000, random_state=20260816)` over the full captured
`batch_odds_api` population (4,281,228 cells as of this run, up from 4,240,790 two days ago), read via
`read_availability_index_safe` with a parquet-level `(pipeline_mode, capture_status)` filter — single bounded read, no
new GCS walk. Result: 43,900/50,000 (87.8%) not_found, confirming the finding is population-representative.
Pre/post-growth cross-tab as originally framed came back N/A: `batch_odds_api`'s distinct `league_id` count is flat at
40 across both H1-2025 and H1-2026 (0 new) — the league_id growth this todo assumed drives the not_found rate lives in
a completely different bucket/manifest (`instruments-store-sports-prd-*`, already closed GENUINE_EXPANSION
2026-08-05). Root-caused instead via a targeted 5-cell GCS prefix listing (not a corpus walk):
`data_type("odds_horizon_bucket")` — 3,700,051/4,281,228 (86.4%) of the population — has no raw vendor source (UAC
`SOURCE_PRIORITY` names only the MDPS-derived source) and no backing parquet was ever written for it under
`pipeline_mode=batch_odds_api`; the real objects at the same (date, venue, league_id) prefix sit under
`data_type=odds`/`data_type=trades`. Rows span through 2026-08-15 (yesterday) — an active, ongoing writer bug. Also
noticed real `data_type=odds` captures stop dead at 2026-07-26 (527,541 rows, zero since) — filed as a separate P2
diag todo, not yet explained. Replaced todo 2 (which was gated on the disproven league_id-growth link) with 3 new
todos: [CODE] P0 stop-the-writer, [DATA] P1 relabel-the-existing-population, [DIAG] P2 the odds-capture-stall
question. Verdict recorded: NOT a league_id-seeding artifact.

**2026-08-16 (slot-18, `backend_engineer`)** — closed the [CODE] P0 stop-the-writer todo:
`market-data-processing-service@3ae762e725`. **The todo's own framing named the wrong repo** — grepped
`market_tick_data_service/` (package code) for `odds_horizon_bucket`: every hit was a comment or a one-off
migration script, zero live `record_captured` callers. The real writer is MDPS's sports candle pipeline
(`SportsBucketAssignmentAdapter` in `bucket_assignment_adapter.py` -> `write_candle_parquet` in
`canonical_writer.py`), which resolves its manifest `pipeline_mode` via
`resolve_pipeline_mode_from_source(blob_path)` — the RAW upstream ODDS_API tick file's own mode — and threads
that unchanged into its OWN derived `odds_horizon_bucket` candle output. UAC already carries a dedicated
closed-set `PipelineMode` triple for exactly this case
(`BATCH_/LIVE_/REPLAY_MDPS_ODDS_HORIZON_BUCKET`, matching `SOURCE_PRIORITY[("sports","ODDS_HORIZON_BUCKET")] ==
["mdps_odds_horizon_bucket"]`), and a standalone repair script
(`market-data-processing-service/scripts/reprocess_sports_odds.py`) already uses it correctly — proving the
intended fix was known but never wired into the live write path. Added
`resolve_output_pipeline_mode(source_data_type, pipeline_mode)` to `canonical_writer_shaping.py` and called it at
the two write choke points: `write_candle_parquet` (covers both the eager per-instrument-file path and the
chain-bundle path — both funnel through the shared `_write_candles`/`_upload_candles_to_gcs` mixin into this one
function) and `_streaming_write_one_group` in `live_workers_streaming.py` (the memory-bounded streaming path),
remapped BEFORE any path/manifest use in each so the on-disk object path and the manifest row stay consistent by
construction. Every OTHER `source_data_type` (including the sibling `odds_snapshot`/`odds_movement`/
`arbitrage_opportunity` sports adapters, which have no dedicated MDPS source registered) passes through unchanged.
5 new unit tests (`TestResolveOutputPipelineMode`, `tests/unit/test_canonical_writer_utility_functions.py`) cover
the batch/live/replay remap plus the pass-through cases; `quality-gates.sh` green
(`.qg_last_passed_sha=3ae762e7`). Corrected this doc's `repos:` frontmatter to add
`market-data-processing-service` (was missing the repo the actual fix landed in). Filed a new [DIAG] P2 follow-up
todo to verify the fix is live in production (needs one real capture cycle to elapse first) — could not verify
that in this session since it requires post-deploy manifest evidence. Did NOT touch the [DATA] P1
existing-population relabel todo or the [DIAG] P2 odds-capture-stall todo — both remain open, unblocked by this
fix.

**2026-08-17 (slot-32, `data_engineering`)** — closed the [DATA] P1 relabel-plan todo. Wrote
`market-tick-data-service/scripts/probe_odds_horizon_bucket_relabel_candidates_2026_08_17.py` (read-only, no
manifest writes) and ran it twice (n=500, then n=5,000, `random_state=20260817`) against the full captured
`(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket)` population (~3.75M rows), each sampled row checked
via a single bounded `list_blobs` on its own `(day, venue, league_id)` shard-key prefix so 4 candidate shapes are
read in one call: the row's own bare path, a `data_type=odds` twin at the same shard slot, and `fixture_id=`-scoped
siblings of both. Result both runs: 0% bare-path found (reconfirms 2026-08-16), but **100% resolve to a real twin
object at the same shard key** (98.78-99.4% via the bare `data_type=odds` twin, 0.6-1.22% via a `fixture_id=`-scoped
`odds` sibling) — **0% genuinely missing in either sample**. This is decisive at population scale, not a subset
finding: corrected the todo's original `attempted_failed`-relabel framing to a ROW-REMOVAL plan (analogous to
`manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL from the canonical" and this doc's own earlier
league_id-rekey stale-duplicate-removal precedent) since the fetch never actually failed — the data is correctly
captured, just mislabeled `data_type`. Wrote the full proposed removal recipe (re-derive-at-drop-time, pause
consolidator, snapshot, CAS edit, force-consolidate, ≥4-cycle durability check) into the todo above. New
`[OPERATOR]` execution todo filed, gated on sign-off — not executed this session per the todo's own instruction.
Did NOT touch the `[DIAG] P2` writer-fix-verify or `[DIAG] P2` odds-capture-stall todos — both remain open,
independent of this removal plan.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).

**2026-08-17 (slot-6, `infra`)** — closed the last open `[DIAG] P2` todo (real `data_type=odds` capture-stall
question). Confirmed via live `gcloud scheduler`/`gcloud run`/log inspection that `uts-prod-sports-scheduler` is
firing `odds_t*` fixture-proximate triggers every ~5 min and `uts-prod-market-tick-data-service-fast-t1-recon` is
successfully fetching + writing real ODDS_API parquet objects (paid credits consumed) to the canonical
`fixture_id=`-scoped path, right up to minutes before this investigation. But a fresh manifest read (bounded, off
the freshly-consolidated index) shows ZERO `(pipeline_mode=batch_odds_api, data_type=odds, capture_status=captured)`
rows since 2026-07-26, and zero rows with a non-empty `fixture_id` column since 2026-06-09 — despite the
fixture_id-routing fix (`market-tick-data-service@cf855ff0`, 2026-08-09) being live in the currently-deployed image.
Verdict: real capture is NOT stalled; the MANIFEST is silently under-reporting it (a Class-1-shaped honest-absence
violation — successful write, no manifest marker), root cause not yet identified (suspect
`_ManifestWriterPool` flush/close or a consolidator-side dedup collapse). Filed a new `[CODE] P1` follow-up todo to
root-cause and fix. Did not attempt the fix itself (DIAG-scoped task; the fix is a distinct, larger investigation).

**2026-08-17 (slot-11, `infra`)** — closed the `[CODE] P1` root-cause-and-fix todo:
`market-tick-data-service@03cf5a20f4`. Root cause was a consolidator-side dedup collapse, not the
`_ManifestWriterPool` flush/close path the prior DIAG suspected. `manifest_consolidator.py`'s dedup key
(`_BASE_DEDUP_COLS`+`_OPTIONAL_DEDUP_COLS`) deliberately excludes `fixture_id` — the sports shard atom is
`(bookmaker, league_id, day)`. `sentinels.py::_emit_sports_v2_sentinels` fanned out one honest-absence sentinel row
per catalog `(bookmaker, league_id, fixture_id)` triple and only skipped the exact-triple case, not the coarser
`(bookmaker, league_id)` case — so an uncaptured fixture's sentinel row shared its dedup key with a captured sibling
fixture's real row for the same cell, and last-write-wins silently clobbered the captured row. Fix: skip sentinel
emission whenever `(bookmaker, league_id)` is already in the pre-existing `captured_sports_league_pairs` set (same
set already used by the off-season-leagues loop and `_emit_sports_v1_sentinels` — just not wired into this loop).
One new regression test. Full `quality-gates.sh` green before commit; quickmerge push-ancestry verified. Filed a new
`[DIAG] P2` todo for the live-production confirmation step (needs the fix live in the deployed image + one real
capture cycle — could not be done in this session). This closes the doc's original `[CODE] P1` todo but the doc
itself stays `open` pending that DIAG P2 follow-up.

**2026-08-22 — forensic investigation verdict on the `[DIAG][OPERATOR] P2` "WHO/WHAT executed the removal" todo
(this session, does NOT resolve the todo — recorded findings only, todo stays open).** Investigated the population
collapse (4,281,228→211,291 captured rows) and later regrowth (211,291→4,352,441) documented in the two
`[DIAG][OPERATOR] P0/P1` todos above.

- Sibling docs `sports_cf8_out_of_window_mechanism_reconciliation_2026_08_16.md` and
  `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` are confirmed UNCONNECTED — disjoint populations (cf8) and a
  read-only investigation (halftime SFI-vs-inplay) respectively; neither performed or explains a row-removal.
- `dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md` is ADJACENT (same shared
  `odds-api-key`, same VM class) but only supplies a regrowth *hypothesis* — it has no executed action that
  explains either event (the collapse or the regrowth) on its own.
- The `_index/snapshots/k2_stale_twin_presync/` GCS prefix found during the fresh precondition check is confirmed
  UNRELATED — it is from a wholly different, month-earlier 2026-07-22 K2 league_id-casing migration, not this
  incident.
- No uncommitted/off-repo script was found responsible. No commit in `market-tick-data-service` in the
  2026-08-18→2026-08-22 window performs a manifest row-removal/CAS-write for `odds_horizon_bucket`.

**FINAL VERDICT — collapse**: the original population collapse (4,281,228→211,291 captured rows) is a genuine,
unrecoverable audit-trail gap. Recording it as such per this todo's own fallback option ("the gap is explicitly
accepted as unrecoverable audit-trail loss").

**Leading hypothesis, NOT a firm conclusion — regrowth**: the later regrowth (211,291→4,352,441) has a
plausible-but-only-partially-confirmed explanation: backfill VM `mtds-backfill-odds-20260817-062648` was preempted
2026-08-19T23:57-58Z and recreated 2026-08-20T00:01Z, predating the writer fix `market-tick-data-service@e00fc618`
(2026-08-20T14:38Z). But the VM's own date-range metadata (`2022-05-09` to `2026-03-28`) does NOT cover the full
observed regrowth span (`2020-06-06` to `2026-08-15`) — so this is stated as a leading hypothesis, not a firm
conclusion; the `[DIAG][OPERATOR] P0` todo above (root-causing the regrowth before any row-removal plan proceeds)
stays genuinely open pending closing that date-range gap.
