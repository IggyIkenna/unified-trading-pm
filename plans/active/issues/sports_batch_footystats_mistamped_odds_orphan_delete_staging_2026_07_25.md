---
doc_type: issue
title:
  batch_footystats mis-stamped ODDS_API objects — manifest rows already gone (orphaned objects), staged
  delete-suggestion for the remaining GCS bytes
summary: >-
  Re-verified the current state of
  plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md's 16,969-object mis-stamped
  population (pipeline_mode=batch_footystats, real venue=ODDS_API/source=ODDS_API data, empty instrument_type) for
  sports_satellite_ao_dispatch_batch2_2026_07_24.md's step-4 "batch_footystats copy+swap" todo (BLK-8e3fdaff). Finding:
  the consolidated manifest now carries ZERO rows matching that population's real signature (source=ODDS_API) — the
  manifest-side purge already happened. But the raw GCS objects themselves still exist (confirmed present on 5/8 sampled
  days spanning 2020-2024; absent on 2 sampled 2024-12/2025-01 days, suggesting a partial object-level cleanup already
  in flight). These are now ORPHAN objects (bytes with no manifest backing). A fresh content-compare on one sample day
  (2022-06-15) reconfirms the archived doc's 2026-07-17 exhaustive finding that this population is a pure duplicate of
  already-canonical batch_odds_api content (0 unique keys either side). Staging a delete-suggestion per the 5-part proof
  — NOT executing; this is a prod-bucket delete, human-only.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [sports, odds, footystats, orphan-object, delete-safety, manifest-desync, pipeline-mode, data-correctness]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: 2026-07-25
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P1
estimate_class: infra
source:
  sports_satellite_ao_dispatch_batch2_2026_07_24.md, league_id casing migration todo, step (4), BLK-8e3fdaff answer
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# batch_footystats mis-stamped ODDS_API population — orphaned objects, staged delete-suggestion

## What I found (2026-07-25, slot 7, data_engineering)

Following the operator's answer to `BLK-8e3fdaff` (scoped re-verification of the archived doc's residual), I re-checked
the CURRENT state of the population
`plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` diagnosed (16,969 objects at
`pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/instrument_type=/data_type=odds/`, `source=ODDS_API`
on 100% sampled rows, filenames `ticks_migrated_<ts>.parquet`).

### 1. The manifest no longer carries this population at all

A manifest census for `pipeline_mode=batch_footystats AND venue(case-insens)=ODDS_API` returns 640 rows — but ALL 640
have `source=footystats` (not `ODDS_API`), `capture_status=empty_confirmed`, and dates entirely BEFORE the 2020-06-06
sports data floor (`/codex/02-data/sports-2020-06-data-floor.md`) — an unrelated pre-floor placeholder population that
happens to share the venue string. A census filtered on `source(case-insens)=ODDS_API` under `batch_footystats` returns
**ZERO** rows. The archived doc's original 42,476-manifest-row population is **entirely absent from the manifest today**
— it was purged (or never re-absorbed) at some point between 2026-07-17 and now, most likely by
`prune_phantom_soccer_manifest_rows_2026_07_22.py` or the manifest-swap work this same plan's steps 1-2 executed
(`unified-trading-pm@8c0f34b31`'s Progress Log entry references `manifest_swap_2026_07_22.py --apply-prod`), though I
did not trace the exact commit — flagging as an open provenance gap, not asserting a specific cause.

### 2. The raw GCS objects still physically exist — now ORPHANED

Direct `gcloud storage ls` (bounded, 8 sampled days, not a corpus walk) on
`raw_tick_data/by_date/day=<D>/pipeline_mode=batch_footystats/asset_group=sports/venue=ODDS_API/`:

| day        | objects present? |
| ---------- | ---------------- |
| 2020-08-15 | yes              |
| 2021-11-03 | yes              |
| 2022-06-15 | yes              |
| 2023-05-20 | yes              |
| 2024-03-02 | yes              |
| 2024-06-01 | yes              |
| 2024-09-01 | yes              |
| 2024-12-01 | **no**           |
| 2025-01-10 | **no**           |

5/9 spot-checked days still have objects; the 2 latest-dated samples (2024-12-01, 2025-01-10) do not — suggesting a
partial, in-progress object-level cleanup for the tail of the date range, or that those specific days never had the
mis-stamp. Not exhaustively traced (would require a corpus walk to confirm the exact cutover boundary — out of scope
here; flagging for whoever executes the eventual delete to re-verify current state immediately before acting, since this
is evidently a moving target).

### 3. Content-verify (Part 2 of the 5-part proof) — fresh sample reconfirms the archived doc's finding

Read all 4 migrated objects for `day=2022-06-15` (17,336 raw rows across 3 per-league files + 1 bare/no-league file that
is the archived doc's documented 2x-duplicate) and all 89 canonical `batch_odds_api` objects for the same day (25,596
rows), keyed on `(instrument_id, fetch_utc, price, bm_time)` — the same family-agnostic key
`merge_migrated_odds_into_canonical_2026_07_17.py` used:

- migrated distinct keys: **8,668**
- canonical distinct keys: **8,668** (of a larger 25,596-row/multi-day-overlap canonical population)
- keys ONLY in migrated: **0**
- keys ONLY in canonical: **0**

**Exact match, zero unique content either side** — this one day is a pure duplicate, corroborating the archived doc's
exhaustive 1,815-day census (1,336 pure-duplicate days, 199 already-merged gain days, 280 add-keys-but-zero-derive-gain
days).

## Disposition (5-part-proof checklist, per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`)

```
Location:            raw_tick_data/by_date/day=<D>/pipeline_mode=batch_footystats/asset_group=sports/
                      venue=ODDS_API/instrument_type=/data_type=odds/ (the ~1,616 non-gain days per the
                      archived doc's exhaustive 2026-07-17 census, MINUS the 199 already-merged gain days)
Part 1 twin probe:   NOT run via gcs_describe_object per-object (would require enumerating all
                      remaining objects — out of scope for this staging pass). Twin EXISTENCE is
                      established indirectly: canonical batch_odds_api objects for the sampled day
                      were read directly (89 objects, 25,596 rows) and are live/present.
Part 2 content:      1,815-day exhaustive census (archived doc, 2026-07-17) + 1 fresh sample
                      (day=2022-06-15, this doc) -> legacy 8,668 keys / canon 8,668 keys /
                      intersection 8,668 / legacy-only 0. Sample-based re-confirmation, NOT a fresh
                      exhaustive re-walk (would need one before actual execution -- see Recommended
                      decision).
Part 3 writers:      grep "batch_footystats" (Explore agent, this session) -> only migration/patch
                      scripts, tests, PipelineMode enum; READ reprocess_sports_odds.py:117-120 and
                      merge_migrated_odds_into_canonical_2026_07_17.py -> no live writer recreates
                      this shape. WRITES? no.
Part 4 readers:      archived doc's own Blast Radius section (2026-07-17, exhaustive grep+READ
                      across reprocess_sports_odds.py / reconcile_phantom_manifest_rows_all.py /
                      features-service / instruments-service) -> nothing reads batch_footystats on
                      the MTDS raw-tick sports surface. Re-confirmed by this session's Explore agent
                      independently. READS? no.
Part 5 twin coverage: NOT measured as a %% -- the "twin" here is not a copy-then-orphan-legacy
                      relationship (Part 5's classic v9-migration case), it is closer to
                      independently-duplicated content (canonical batch_odds_api already held this
                      data via its own live capture, unrelated to these migrated objects). The
                      spirit of Part 5 (never delete without a confirmed canonical twin) is
                      satisfied for the SAMPLED day; not exhaustively re-verified for the full
                      remaining population.
Disposition:         yes-after-verify (for the subset matching the archived doc's "pure duplicate"
                      1,336-day bucket, corroborated but not freshly exhaustively re-walked) --
                      NOT yes-twin-confirmed. The 280-day "adds-keys-but-zero-derive-gain" bucket
                      from the archived census is explicitly EXCLUDED from this disposition --
                      those days add raw keys not present in canonical even though the derive
                      output is unchanged, so they need their own re-examination before any delete
                      (not pure duplicates by the strict Part-2 definition).
Hard stop:           prod-bucket delete (codex § 3.1) -- human-only, always.
```

## Recommended decision

1. **Do NOT execute any delete from this doc alone.** Before a human executes:
   - Re-run a fresh, EXHAUSTIVE content-verify census (mirroring the archived doc's 2026-07-17 1,815-day probe) since 8
     days have passed and the manifest-side state has already changed underneath this population once (rows purged) —
     confirm the object-level state has not silently drifted further (the 2 empty 2024-12/2025-01 samples in this doc
     suggest it may already be shifting).
   - Explicitly re-examine the 280-day "adds keys but zero derive gain" bucket separately — it is NOT covered by this
     doc's `yes-after-verify` disposition.
2. This resolves `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s step-4 "batch_footystats copy+swap" todo as:
   **the copy+swap already happened correctly on 2026-07-17** (the 199 genuine-gain days, via
   `merge_migrated_odds_into_canonical_2026_07_17.py`, acceptance-tested) — there is no remaining copy+swap work. What
   remains is the archived doc's own still-open PURGE todo (delete the now-redundant, now-orphaned duplicate objects),
   which is human-gated and tracked here + there, not a new script-extension task.

## Todos

- [ ] [DATA] P1. Run a fresh exhaustive content-verify census (all remaining days in the archived doc's original
      1,815-day scope, excluding the 199 already-merged gain days) to refresh the `yes-after-verify` disposition to
      `yes-twin-confirmed` before any human delete decision. **Tool already built and shipped for this** —
      `market-tick-data-service@c03890b3`,
      `scripts/sports/league_id_relocation/census_footystats_orphan_content_2026_07_25.py` (read-only, per-day
      `pure_duplicate`/`genuine_gain`/`no_migrated_objects` classification via the same family-agnostic key; smoke-
      tested against `2022-06-15` + `2024-12-01`, matches this doc's manual findings exactly). Build a `--days-file`
      covering the remaining ~1,616 days (the archived doc's original day list minus the 199 merged gain days) and run
      it — do not re-derive the comparison logic from scratch. (repo: market-tick-data-service)
- [ ] [DATA] P2. Separately re-examine the archived doc's 280-day "adds keys, zero derive gain" bucket — excluded from
      this doc's delete-suggestion; needs its own disposition. (repo: market-tick-data-service)
- [ ] [DOCS] P3. Trace the exact commit/process that purged the 42,476 mis-stamped manifest rows between 2026-07-17 and
      2026-07-25 (provenance gap noted above) — for the record, not blocking. (repo: unified-trading-pm)
