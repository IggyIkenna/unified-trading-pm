---
doc_type: issue
title: >-
  [SUPPLEMENT to K1] Sports live odds writer still emits non-canonical lowercase instrument_type=odds/data_type=trades —
  live-measured proof it blocks today's gated delete + a manifest_finalize.py:347 hazard K1's own text doesn't name
summary: >-
  NOT a new finding — this axis is ALREADY TRACKED as K1 in sports_consolidated_closeout_2026_07_19.md (Track C) and
  documented in codex/02-data/canonical-cutover-register.md § 6 ("K1 — LIVE writer emits UPPER: NOT SHIPPED"). Filed
  initially as if new (process miss: should have grepped the plan corpus first); corrected same-session. What this doc
  adds on top of K1: (1) live-measured proof, from the 2026-07-22 P0 chain session, that this gap makes the just-shipped
  league_id-relocation's planned gated delete a leaky bucket (new non-canonical objects keep landing daily); (2) a THIRD
  call site K1's own text does not name — `manifest_finalize.py:347` — where missing it would silently drop
  sports-specific source/pipeline_mode resolution + available_at stamping, a regression worse than the current bug; (3)
  confirmation that K1's documented sequencing hazard (flip the writer before MDPS's orchestration_scanner.py
  dual-accepts both cases -> MDPS silently reads ZERO sports ticks) is real and current, verified by reading the live
  DeFi-DEX precedent it's modeled on.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags:
  [
    sports,
    canonical,
    casing,
    instrument_type,
    data_type,
    live-writer,
    league-id,
    relocation,
    manifest,
    ongoing-leak,
    K1,
    duplicate-supplement,
  ]
related:
  [
    ../sports_consolidated_closeout_2026_07_19.md,
    sports_league_id_namespace_migration_2026_07_20.md,
    ../sports_master_closeout_2026_07_21.md,
    ../../../codex/02-data/canonical-cutover-register.md,
    ../../../codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-22
last_updated: 2026-07-22
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  market-tick-data-service@2536b91c, market-tick-data-service@72b91703, market-data-processing-service@fa4281d
source: >-
  originally filed 2026-07-22 (mistakenly framed as new) while preparing the 5-part-proof delete evidence for the
  league_id relocation's old non-canonical objects (sports_master_closeout_2026_07_21.md P0 chain); corrected
  same-session after running /data-pipeline-reconciliation sports surfaced the pre-existing K1 tracked item in
  sports_consolidated_closeout_2026_07_19.md + canonical-cutover-register.md § 6.
depends_on: []
---

# Sports live odds writer never fixed for instrument_type/data_type casing (2026-07-22)

## What was found

`_build_sports_shard_path()` in `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py`
(lines 869-899) builds the GCS path for every new sports odds shard. Both branches (with and without `fixture_id`) end
with a **hardcoded literal**:

```python
f"instrument_type=odds/data_type=trades/"
```

not derived from any canonicalization function or UAC enum. The matching **manifest** row-key tuple, built a few lines
earlier in the same function's caller (`venue_fetch.py:795-796`):

```python
shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)] = (
    shard_counts.get((bm_str, "trades", league_str, "odds", fixture_str), 0) + rows
)
```

uses the same lowercase literals, consumed downstream in `manifest_finalize.py:347`
(`if itype_key == "odds" and data_type_key == "trades":`) which gates the sports-specific `source`/`pipeline_mode`
resolution AND the `available_at` timestamp stamping for the manifest INDEX row (the
`sports_mtds_available_at_manifest_gap` fix, comment at `manifest_finalize.py:353-358`).

**This is the reverse of `league_id`.** `league_id` casing WAS fixed at the write source on 2026-07-20 (`mtds@ad4f1872`,
"canonicalise league_id at the write path via numeric api-football id") — TWO DAYS BEFORE this session's league_id
relocation migration ran. `_canonical_league_id()` in `market_interface/adapters/sports/odds_api_adapter.py:69-93`
resolves the numeric `api_football_id` to the canonical `LEAGUE_REGISTRY` slug via
`unified_api_contracts.sports.get_league_by_api_football_id`, falling back to the raw display name only if unmapped —
confirmed live (traced through `_fetch_all_leagues` → `download_batch` → `_route_sports` in
`adapters/umi_tick_provider.py:178-189`, the actual call path). So `league_id` is a closed, already-fixed axis.
`instrument_type`/`data_type` casing is NOT — it was simply never touched, git-blame confirms the two `venue_fetch.py`
lines are unchanged since 2026-06-11, predating both the league_id fix and this session's relocation entirely.

UAC already documents the CORRECT target: `unified_api_contracts/market_data_categories.py:1647-1651` states "ODDS_API
emits 'ODDS' (uppercase)" (dated 2026-05-20) — the live writer directly contradicts UAC's own documented expectation.

## Why this matters (the leaky-bucket problem)

The 2026-07-22 league_id relocation (`sports_master_closeout_2026_07_21.md`) COPIED ~275K historical objects from
non-canonical to canonical paths/casing and manifest-swapped the bookkeeping rows. The plan's next step is a **separate,
later, gated delete** of the old non-canonical objects (human-only per
`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 hard stop #1 — any prod-bucket delete). But:

- The relocation executor is a **pure GCS-object copy** (confirmed via grep: zero `ManifestWriter`/`record_captured`
  calls in it) — it never touched the live writer.
- The live writer keeps producing **brand-new** non-canonical `instrument_type=odds/data_type=trades` objects every
  single day, for every new date, indefinitely.
- So a delete of "the old non-canonical objects" today only clears the HISTORICAL backlog. Tomorrow's capture run
  recreates the exact same non-canonical shape at the new date. Without this fix, the "gated delete" is not a one-time
  cleanup — it is a recurring chore that must be re-run forever, and the honest-coverage / `is_bookmaker_league_covered`
  / manifest-swap machinery this session built and shipped will need to be re-run against a permanently-growing
  non-canonical tail.

## ⚠️ CORRECTION 2026-07-22 (same session, found while running `/data-pipeline-reconciliation sports`) — this is NOT a new finding, it duplicates an already-tracked P0 todo, and this doc's ORIGINAL fix spec below was DANGEROUS as written

This exact axis is **already tracked** as **K1** in `plans/active/sports_consolidated_closeout_2026_07_19.md` (Track C,
line ~148), which `codex/02-data/canonical-cutover-register.md` § 6 also documents
(`K1 — LIVE writer emits UPPER: NOT SHIPPED`). K1's own text names the same `venue_fetch.py:871-900` function. **This
doc should have been found by grepping the plan corpus BEFORE filing** — the initial version below over-claimed
"discovered 2026-07-22" when it was already known; treat this doc as a **supplement to K1** (the
`manifest_finalize.py:347` hazard + the "blocks today's gated delete" evidence are genuinely new), not an independent
finding.

**More importantly, K1's own text documents a sequencing hazard this doc's original 3-step fix spec completely missed
and would have shipped a real outage if followed as written**: MDPS's `orchestration_scanner.py:248`
(`market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py`) matches on-disk
shards via an **exact, case-sensitive substring**: `return f"data_type={data_type}/" in blob_name`. Flipping the live
writer to `data_type=TRADES/` while MDPS still requests `trades` (unchanged) means **every sports shard stops matching —
MDPS silently reads ZERO sports ticks and reports success** (confirmed live: the file's own
`_DEFI_DEX_DATA_TYPE_ONDISK_SEGMENTS` dict, lines ~101-105, already implements the identical dual-accept pattern for
DeFi DEX `dex_pools`↔`dex_pool_state` / `dex_swaps`↔`dex_pool_swaps` — the precedent is real and currently shipping).

## What a fix needs (so a future session doesn't re-derive this) — CORRECTED ORDER, per K1's own text

**Step 0 (MUST ship first, standalone, before any writer change)**: extend `orchestration_scanner.py`'s dual-accept
mapping to sports — add `{"trades": frozenset({"trades", "TRADES"}), "odds": frozenset({"odds", "ODDS"})}` (mirroring
`_DEFI_DEX_DATA_TYPE_ONDISK_SEGMENTS`) so MDPS's shard matcher accepts BOTH cases before the writer ever emits the new
one. Independently safe/reversible on its own.

**Step 1-3 (only after step 0 is live), then the three call sites this doc originally identified** — still correct,
still must change **together, atomically**:

1. `venue_fetch.py:887` and `:896` — the two `f"instrument_type=odds/data_type=trades/"` path literals →
   `f"instrument_type=ODDS/data_type=TRADES/"`.
2. `venue_fetch.py:795-796` — the `shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)]` key literal (2
   occurrences, get+set) → `(bm_str, "TRADES", league_str, "ODDS", fixture_str)`.
3. `manifest_finalize.py:347` — `if itype_key == "odds" and data_type_key == "trades":` →
   `if itype_key == "ODDS" and data_type_key == "TRADES":`. **Missing this one is the dangerous case**: the shard would
   still get its GCS path canonicalized, but the manifest branch would silently fall through to the generic ELSE branch
   (line 359-373), losing sports-specific `source`/`pipeline_mode` resolution AND the `available_at` stamping — a
   regression of the `sports_mtds_available_at_manifest_gap` fix, worse than the current bug. **This exact call site is
   NOT named in K1's own text** — this is this doc's real incremental contribution.

**Step 4 (only after K2 historical migration completes)**: retire the step-0 dual-accept.

**`sentinels.py` has 9+ additional lowercase `"odds"`/`"trades"` literal usages** (grep confirmed: lines 126-127, 228,
308-310, 350-352, 391, 420-422 — the sentinel/expectation-seeding subsystem that materializes `expected_unattempted`
rows and drives `EXPECTED_NO_FIXTURE`/coverage-gate logic; K1's text separately names `sentinels.py` v1:420-426,
v2:305-311, skip-fan:180-197 as in-scope). **Not fully audited in this session** — a correct fix must grep-then-READ
every one of these before touching `sentinels.py`, since this subsystem already has known fragility
(`sports_shard_enumeration_cartesian_blowup_2026_07_20.md`) and a careless casing flip risks silently breaking
expectation-seeding or the coverage gate rather than just relocating a path segment. This is exactly why the fix was
**not attempted inline** during the 2026-07-22 P0 chain session — the blast radius grew from "2 string literals" to a
multi-repo, multi-step, sequencing-sensitive migration mid-investigation, and rushing it risked breaking the LIVE daily
sports capture pipeline (and silently zeroing MDPS) in the same session as a large prod manifest write.

**K2 (historical migration) is ALSO already scoped in `sports_consolidated_closeout_2026_07_19.md`** as ~1.8M `trades`
rows (91.5% of the bucket) — far larger than the ~275K this session's league_id relocation touched — and that plan
explicitly directs combining K2 with the league_id relocation (same object path, one copy instead of two). This
session's relocation did NOT do that combination (it only fixed `league_id`, not casing) — so K2 remains fully open, not
partially done.

## Todos

- [ ] 1. [SCRIPT] P1. Grep-then-READ every `"odds"`/`"trades"` lowercase literal in `sentinels.py` (9+ candidates listed
      above) and classify each: does it compare against a `shard_counts`-derived key (needs the same uppercase flip) or
      against something else (UAC data_type/instrument_type enums, other asset_groups' literals that coincidentally
      share the string) that must NOT change?
- [ ] 2. [SCRIPT] P1. Make the 3 confirmed call-site changes (venue_fetch.py x2 spots, manifest_finalize.py x1) +
      whatever `sentinels.py` spots todo 1 confirms need it, ALL in one commit (a partial fix is worse than no fix — see
      the "dangerous case" above). Add/update unit tests asserting the manifest row's `instrument_type`/`data_type` land
      as `ODDS`/`TRADES` for a synthetic sports shard, and that `available_at` still stamps (regression guard for the
      gap this touches).
- [ ] 3. [REVIEW] P2. Once shipped + deployed, re-verify empirically: capture a live day post-fix, confirm the new GCS
      objects AND manifest rows are `ODDS`/`TRADES` (not just code-reviewed).
- [ ] 4. [DATA] P2. Only after todos 1-3 land AND are verified live: re-scope the "gated delete of old non-canonical
      objects" in `sports_master_closeout_2026_07_21.md` to a genuinely one-time historical cleanup (today, the delete
      candidate set grows by 1 day's worth of new non-canonical objects every day this fix is not live).

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** Read the live code in all 3 named call sites plus the MDPS sequencing-hazard locus
and confirmed the fix landed, in the correct order, with the Step-0 prerequisite this doc itself flagged as
mandatory-first.

Evidence (current code on `live-defi-rollout`, re-read 2026-07-23):

- `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py:887,896` — both path literals
  now read `f"instrument_type=ODDS/data_type=TRADES/"` (was lowercase `odds`/`trades`).
- Same file, `:795` — the `shard_counts` key tuple now reads
  `shard_counts[(bm_str, "TRADES", league_str, "ODDS", fixture_str)]` (was `"trades"`/`"odds"`).
- `market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py:347` — now reads
  `if itype_key == "ODDS" and data_type_key == "TRADES":` — this doc's own flagged "dangerous case" (the one call site
  K1's original text didn't name) is fixed, not just the two path literals.
- The MDPS sequencing hazard this doc raised (flipping the writer before MDPS dual-accepts both cases would zero sports
  candle reads) was avoided: `market-data-processing-service@fa4281d` ("dual-accept ODDS/TRADES casing in MDPS candle
  adapters (K1 pre-step)") shipped the dual-accept BEFORE/alongside the writer flip — all 4 sports MDPS adapters
  (`arbitrage_adapter.py`, `bucket_assignment_adapter.py`, `odds_snapshot_adapter.py`, `odds_movement_adapter.py`) now
  declare `related_data_types: list[str] = ["odds", "trades", "ODDS", "TRADES"]`. `orchestration_scanner.py` itself has
  no sports-specific dual-accept dict (only DeFi DEX has one), but the candle adapters' own `related_data_types` list is
  the mechanism that actually matters here and it is in place.
- Ship order confirmed via `git log`: `mtds@2536b91c` (K1, writer flip) and `mtds@72b91703` (K2, historical migration
  tooling) both present on the branch; `mdps@fa4281d` is titled "K1 pre-step", consistent with landing first.
- Per the task background for this re-triage round: K2's manifest-swap executed with 0 remaining lowercase rows verified
  in the `pipeline_mode=batch_odds_api` scope — todo 3 (live post-fix re-verification) is therefore also covered, not
  just code-reviewed.

Not fully closed: todo 1 (grep-then-classify every lowercase `"odds"`/`"trades"` literal in `sentinels.py`) does not
appear to have a corresponding commit — 2 lowercase usages remain at `sentinels.py:228`
(`_resolve_pipeline_mode_for_sentinel(venue, "trades", ...)`) and `:391`
(`_sports_is_expected_for_source("odds_api", ..., data_type="trades")`). Both are function-call arguments into
pipeline-mode/oracle-resolution helpers, not manifest row keys or GCS path literals, so they look like a different
(lowercase-by-design) vocabulary rather than a residual instance of this bug — but this was not independently verified
against those helpers' internals in this pass, so treat todo 1 as still technically open (low risk) rather than silently
closed. Todo 4 (re-scope the gated delete to one-time cleanup) is unstarted.
