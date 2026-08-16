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

- [ ] [DIAG] P1. Re-run the 50,000-cell not_found measurement as a genuine randomized sample (`df.sample(n=50000,
      random_state=<fixed seed>)` over the full captured `batch_odds_api` population, single bounded manifest read,
      no new GCS walk) to confirm or revise the 93.15% figure population-wide. Cross-tabulate not_found rate by
      `league_id` — if it concentrates heavily in the league_ids responsible for the 51→384 growth (vs. the original
      ~51 pre-growth league_ids), that directly confirms the seeding-artifact hypothesis for the league_id-growth todo.
      Source: this doc + `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s league_id-growth todo. Done when: a
      population-representative not_found rate is recorded, broken down by pre-growth vs. post-growth league_id, with
      a written verdict on whether the growth is a seeding artifact.
- [ ] [DATA] P1. Once the league_id-growth todo reaches a verdict, if genuine seeding-artifact rows are confirmed:
      determine the correct `capture_status` relabel (`attempted_failed` if the fetch genuinely failed / was never
      attempted, per honest-absence-downstream-handling.md) for the not_found population, and propose (do not execute
      without operator sign-off — this is a manifest-row-level correctness fix touching potentially millions of rows)
      a scoped relabel plan analogous to prior manifest-row correction precedents (e.g.
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Surgical ROW REMOVAL from the canonical"). Source:
      this doc.
      Done when: a concrete, reviewed relabel plan exists (or the not_found population is confirmed NOT a false-status
      case and this todo is closed as not-applicable, with reasoning recorded).

## Progress Log

**2026-08-16 (slot-30, `data_engineering`)** — filed while working `sports_satellite_ao_dispatch_batch9-010`. Measured
93.15% not_found rate on a 50,000-cell (non-randomized) sample; corpus grew 275,136→4,240,790 captured `batch_odds_api`
cells since 2026-07-26. Did not root-cause; handed to the existing league_id-growth todo with concrete supporting
numbers and a proposed randomized re-measurement.
