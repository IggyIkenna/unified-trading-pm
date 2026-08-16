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
repos: [market-tick-data-service, instruments-service, unified-trading-library]
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
last_updated: 2026-08-16
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
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py,
  ]
depends_on: []
---

# Sports MDT odds "captured" manifest cells — 93.15% sample not_found rate at canonical path

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
