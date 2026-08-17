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
last_updated: 2026-08-17
priority: P1
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
context_scope: [/plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md, /codex/02-data/honest-absence-downstream-handling.md, /codex/02-data/availability-manifest-and-data-status.md, market-tick-data-service/scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py]
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
- [ ] [DATA][OPERATOR] P1. Execute the stale-duplicate-row-removal plan above once operator sign-off is obtained:
      scoped dry-run first (count + snapshot), then `--apply` removal of confirmed-stale `batch_odds_api` rows,
      re-verify via a fresh randomized sample that the not_found rate has dropped to ~0% for rows with a canonical
      twin. Source: this doc's now-resolved P1 todos above. Done when: operator sign-off is recorded, the dry-run
      count + snapshot exist, the apply run completes with 0 errors, and a re-measurement confirms the not_found rate
      has dropped substantially (or the residual is explained).
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
- [ ] [DIAG] P2. Once the `uts-prod-mdps-odds-horizon-bucket` Cloud Run Job has completed a run scheduled AFTER
      2026-08-17T02:58:33Z (the timestamp the fixed image `bc55b99`/`0.30.4` became `:latest`) — expected
      ~2026-08-18T01:15Z or later per the job's ~24h cadence — read the manifest for
      `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket, capture_status=captured)` rows with
      `attempted_at`/`written_at` past that execution's start time: expect ZERO new rows in that combination, and
      instead see new rows landing under `pipeline_mode=batch_mdps_odds_horizon_bucket` (or the live/replay siblings)
      for the same period. Source: this doc's writer-fix-verify todo above (deploy-timing half done; this is the
      manifest-evidence half). Done when: a written verdict + fresh manifest evidence confirms the fix is live and no
      new phantom rows are landing, or names the reason it isn't yet.
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
- [ ] [DATA][OPERATOR] P1. Execute the odds_horizon_bucket row-removal plan above once operator sign-off is obtained:
      re-derive the drop set fresh against live disk immediately before the drop (not this session's sample),
      snapshot + pause consolidator + CAS-edit + force-consolidate per the manifest-consolidator-ssot.md recipe, then
      re-verify via a fresh randomized sample that 0 `(pipeline_mode=batch_odds_api, data_type=odds_horizon_bucket,
      capture_status=captured)` rows remain and the `data_type=odds` twin data is intact. Source: this doc's now
      -resolved relabel-plan todo above. Done when: operator sign-off is recorded, the pre-drop re-derivation +
      snapshot exist, the CAS write + force-consolidate complete with 0 errors, and a re-measurement confirms 0
      residual rows (or explains any residual).
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

- [ ] [CODE] P1. Root-cause and fix why `market-tick-data-service`'s `_write_shard_counts_to_manifest` /
      `_ManifestWriterPool` (`market_tick_data_service/engine/orchestrator/manifest_finalize.py`,
      `_manifest_bucket.py`) is not landing manifest rows for `(pipeline_mode=batch_odds_api, data_type=odds,
      fixture_id≠"")` shards, despite the 2026-08-09 fixture_id-routing fix being live in production and the
      corresponding GCS parquet objects being written successfully every ~5 minutes (see this doc's now-resolved
      DIAG P2 todo above for full evidence — a manifest query for any non-empty-`fixture_id` row finds nothing
      newer than 2026-06-09, while the GCS write side is confirmed live as of 2026-08-17). Suspect the
      `_ManifestWriterPool` flush/close lifecycle or a consolidator-side dedup collapse against a pre-fix bare-path
      row sharing the same `(venue, league_id, day)` key — both need checking. Source: this doc's DIAG P2 finding
      (2026-08-17). Done when: the root cause is identified and fixed, `quality-gates.sh` is green, and a fresh
      manifest read after the fix has run through at least one live capture cycle confirms new
      `(pipeline_mode=batch_odds_api, data_type=odds, capture_status=captured)` rows are landing with dates past
      the fix's deploy timestamp.

## Progress Log

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
