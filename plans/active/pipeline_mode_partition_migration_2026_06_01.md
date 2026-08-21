---
doc_type: plan
title:
  pipeline_mode on-disk partition migration — bundle pipeline_mode= hive partition into each bucket's next whole-corpus
  walk
summary:
  Promote pipeline_mode from a column to an on-disk hive partition key in GCS paths by bundling the change as a rider
  into each asset group's next scheduled whole-corpus manifest canonicalisation walk.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [pipeline-mode, partition, migration, gcs, single-walk, manifest, hive-partition]
related: []
created: 2026-06-01
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
last_updated: 2026-08-20
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/epics/batch_live_symmetry_master.md,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
  ]
---

**MIGRATED FROM:** `plans/archive/2026_06/pipeline_mode_implementation_2026_05_28.md` Phase 5 (on-disk partition —
DEFERRED at column-level completion 2026-05-28; single-walk discipline forbids a standalone partition-key walk, so the
work splits into this named successor that piggybacks on the next whole-corpus walk window per bucket).

# pipeline_mode on-disk partition migration

> **🟡 DeFi: `pipeline_mode=` path partition is operator-LOCKED CANONICAL (2026-06-01) and lands WITH the DeFi C0 walk,
> not after.** The DeFi C0 single-walk (`defi_manifest_canonicalisation_2026_06_01.md` §C) already writes
> `…/day=/pipeline_mode={mode}/asset_group=defi/…`. **What this requires (HARD — tracked as defi C0-CN6/CN4/CN5)**: the
> writer/readers must become pipeline_mode-AWARE together — UAC `build_defi_partition_path` makes `pipeline_mode=`
> canonical (not just a `candidate_parquet_paths` probe), and features-onchain + MDPS readers pass `pipeline_mode` —
> else consumers reading the base path won't find migrated DeFi data (the regression the 2026-06-01 naming audit
> caught). SSOT: `/codex/02-data/defi-canonical-naming-ssot.md`. For non-DeFi AGs this remains a column-scan interim per
> below.

The `pipeline_mode` **column-level** implementation shipped fully in `pipeline_mode_implementation_2026_05_28` (Phases
0–4 + 6: 43.5M rows backfilled, QG STEP 5.85 enforces enum-only writes, batch-live-reconciliation consumes
`GROUP BY pipeline_mode`, manifest carries the column). The remaining work is promoting `pipeline_mode` from a column to
an **on-disk hive partition key** in the GCS path: `day=…/pipeline_mode=…/asset_group=…/venue=…/…`.

Partition-key addition is **review-blocking outside a whole-corpus migration window** (single-walk discipline — HARD
RULE). It MUST bundle into each bucket's next scheduled whole-corpus walk; a standalone partition-only walk is
forbidden. Reads filter by column-scan (low cardinality, ~10 enum values) until the partition lands — acceptable interim
performance per the parent plan's "Out of scope" note.

## Coverage status

> **[⚠️ NEEDS VERIFICATION 2026-07-21, plan-reconcile]**: the cefi/tradfi/prediction rows below name L3 owner plans that
> are now `plans/archive/2026_07/` (archived+superseded by their asset-group `*_consolidated_closeout_2026_07_18`
> plans), and the successor umbrella `data_completion_to_100_all_ag_2026_06_21.md` never mentions "hive partition" and
> has no tracked C-pipeline_mode-RIDER todo of its own — so this table's coordination mechanism (rider bundled into a
> named walk) looks orphaned. **However**, a live-code spot-check found `pipeline_mode=` already present as a path
> segment in current production writes across cefi/defi (e.g. `.../day=<date>/pipeline_mode=live_hyperliquid/...`,
> `.../pipeline_mode=live_onchain_subgraph/...` — 80+ occurrences in `data_completion_to_100_all_ag_2026_06_21.md`
> alone), meaning the on-disk partition may already be live as a side effect of other writer work, not silently dropped.
> This plan's own checklist below was never verified against real GCS state either way — recommend an actual
> `gcloud storage ls`/manifest check per asset_group before treating this as done OR as a gap.

Each asset_group's `pipeline_mode=` partition is a RIDER bundled into **that AG's L3 manifest-canonicalisation walk**
(its named C-pipeline_mode rider todo). Completing the walk closes this plan's row for that AG — there is no separate
partition walk anywhere (single-walk discipline):

| Bucket          | L3 owner plan (carries the `pipeline_mode=` rider)          | Rider todo            |
| --------------- | ----------------------------------------------------------- | --------------------- |
| **defi**        | `defi_manifest_canonicalisation_2026_06_01.md` §C (C0 + C9) | bundled in C0/C9      |
| **cefi**        | `cefi_manifest_canonicalisation_2026_06_01.md`              | C-pipeline_mode RIDER |
| **tradfi**      | `tradfi_manifest_canonicalisation_2026_06_01.md`            | C-pipeline_mode RIDER |
| **sports**      | `sports_manifest_canonicalisation_2026_06_01.md`            | C0 (a) + C-partition  |
| **prediction**  | `prediction_manifest_canonicalisation_2026_06_01.md`        | C-pipeline_mode RIDER |
| **instruments** | `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (folded-in "C0" section) | cefi/tradfi/sports DONE (live-verified 2026-08-20); prediction OPEN — see Phase 1 |

## Phased execution

### Phase 1 — Bundle `pipeline_mode=` into each non-DeFi bucket's next whole-corpus walk

**LIVE-VERIFIED 2026-08-20 (F-G25-4 follow-up)** — supersedes the "not independently re-verified" note this banner
previously carried. Ran this doc's own prescribed Success-criteria spot-check for real, via
`unified_trading_library.cloud_interface` (`get_storage_client()` + `resolve_bucket_name()`, never raw gsutil/gcloud)
against PROD GCS. Result: **5 of 6 targets confirmed DONE, 1 confirmed a genuine, currently-open gap** — not a stale
assumption either way:

- **cefi / tradfi / sports / prediction tick-data buckets** (`market-data-tick-{cefi,tradfi,sports,pred}-prd-…`):
  `pipeline_mode=` IS present as a hive path segment, and already in the operator-ratified SOURCE-AWARE
  `{mode}_{source}` form (see Codex SSOTs below) — e.g.
  `.../day=2026-08-19/pipeline_mode=batch_fred/asset_group=tradfi/…` (tradfi, sampled on the MOST RECENT day, not just
  historical backfill), `.../pipeline_mode=batch_footystats/asset_group=sports/…`,
  `.../pipeline_mode=batch_kalshi/asset_group=prediction/…`, `.../pipeline_mode=batch_tardis/asset_group=cefi/…`.
- **instruments (reference-data) buckets** — cefi/tradfi/sports confirmed present too:
  `instruments-store-{cefi,tradfi}-prd-…` carry
  `instrument_availability/by_date/day=…/pipeline_mode=batch_instruments_service/asset_group=…/…`; sports carries both
  `pipeline_mode=batch_api_football/` and `pipeline_mode=batch_instruments_service/` (confirmed as recently as
  day=2026-08-27).
- **`instruments-store-pred-prd-…` (prediction instruments-store) is the one confirmed real gap**: exhaustively
  checked all 682 top-level `instrument_availability/by_date/canonical_question_group=*/` groups — **zero** carry a
  `pipeline_mode=` segment anywhere in the tree. Prediction's reference-data bucket is keyed
  `canonical_question_group=`/`day=`/`venue=` with no pipeline_mode axis at all.

The "instruments bucket — archived-complete 2026-06-26" claim previously here was ALSO stale, in a different way than
first thought: that archived plan's own banner states its apply-work (E3-E6, incl. the pipeline_mode= walk) was NEVER
run under it — it was folded 2026-06-26 into `instruments_mtds_subset_consistency_remediation_2026_06_17`, which
3-way-split 2026-07-24. The current live owner of the still-open rider is
`plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (folded-in "C0" section), not the
archived 2026-06-01 doc — corrected in the table above and Phase 1 below.

- [x] ✅ [INFRA] P2. **cefi / tradfi / sports / prediction tick-data buckets** — DONE, live-verified 2026-08-20 (see
      banner above): `pipeline_mode=` present as a hive path segment on all 4 buckets, in the ratified source-aware
      `{mode}_{source}` form, confirmed on both historical AND current-day objects. Landed as a byproduct of each AG's
      C-pipeline_mode RIDER inside its L3 manifest-canonicalisation walk, as designed — no standalone walk was run or
      needed.
- [x] ✅ [INFRA] P2. **instruments bucket — cefi / tradfi / sports** — DONE, live-verified 2026-08-20:
      `instruments-store-{cefi,tradfi,sports}-prd-…` all carry `pipeline_mode=` as a real on-disk path segment under
      `instrument_availability/by_date/day=…/` (`batch_instruments_service` for cefi/tradfi; `batch_api_football` +
      `batch_instruments_service` for sports).
- [ ] [DATA] P2. **instruments bucket — prediction is the one remaining real gap.** Live-verified 2026-08-20:
      `instruments-store-pred-prd-…`'s `instrument_availability/by_date/` tree is keyed
      `canonical_question_group=`/`day=`/`venue=` with **zero** `pipeline_mode=` segments across all 682 sampled
      question-groups — the partition never landed here, unlike its cefi/tradfi/sports siblings (which DO carry it
      live, even though the shared rider below still reads `[ ]` open for all four — a separate cross-plan doc-drift
      worth flagging there, not silently resolving here). The CURRENT live owner of the open rider is
      `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`'s folded-in "C0 — ONE bundled
      single-walk per non-sports instruments bucket … `pipeline_mode=` partition (CF-3)" todo (open `[ ]` there,
      scoped to cefi/defi/tradfi/prediction) — do NOT open a second walk here (single-walk discipline). This plan's
      prediction-instruments row closes when THAT todo closes; cross-referenced, not duplicated.

## Success criteria

| Phase   | Gate                                                                      | Verification                                                                                                                                                                                                    |
| ------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | `pipeline_mode=` partition present, in SOURCE-AWARE form, in every bucket | live GCS listing via `unified_trading_library.cloud_interface` shows `pipeline_mode={mode}_{source}` as a path segment — **5/6 confirmed DONE 2026-08-20** (cefi/tradfi/sports/prediction tick-data + cefi/tradfi/sports instruments-store); **1/6 confirmed OPEN** (prediction instruments-store) |

## Codex SSOTs

- `/codex/02-data/pipeline-mode-partition.md` — the canonical-form SSOT. The `{mode}_{source}[_{transport}]`
  source-aware form was operator-ratified 2026-06-07 — 6 days AFTER this plan was authored (2026-06-01) — so it is the
  bar this plan's Success Criteria actually checks against, not the plain "`pipeline_mode=` segment present" this doc
  originally wrote. Every live-verified occurrence found 2026-08-20 already uses the source-aware form (no coarse
  `batch`/`live` stragglers in the sampled buckets) — the drift changed the bar, not (so far) the outcome.
- `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` — documents the deferred-partition note; flip the
  "deferred to next migration window" line to "landed per-bucket" as each bucket's walk completes.

## Composes with

- `defi_manifest_canonicalisation_2026_06_01.md` (§MASTER + §C) — DeFi bucket carries the partition inside its C0
  single-walk; the MASTER's CONFLICT-1 codifies this plan as a RIDER (never its own walk).
- `cefi_manifest_canonicalisation_2026_06_01.md` / `tradfi_manifest_canonicalisation_2026_06_01.md` /
  `sports_manifest_canonicalisation_2026_06_01.md` / `prediction_manifest_canonicalisation_2026_06_01.md` — each carries
  the `pipeline_mode=` partition as a named C-pipeline_mode rider in its single-walk.
- Single-walk discipline (HARD RULE — CLAUDE.md § Manifest + honest absence).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — `locked_by: live-defi-rollout`; both todos are riders that
  complete only inside another plan's whole-corpus walk (single-walk discipline) and need window coordination with the
  IS migration owner.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: fixed context_scope -- the 2026-08-01 edit had left malformed YAML (a nested list + a
  stray `? context_scope` complex-mapping-key token) despite the marker claiming "2 entries"; rebuilt clean (5 entries),
  all verified on disk.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-07-30; both open todos are true riders
  (single-walk discipline forbids a standalone partition walk) that close only when another plan's whole-corpus walk
  completes. Secondary finding, not actioned: the doc's own "⚠️ NEEDS VERIFICATION 2026-07-21" banner recommends a live
  `gcloud storage ls`/manifest spot-check per asset_group to confirm whether `pipeline_mode=` has already landed as a
  side effect of other writer work — that check is prose-only, not a tracked todo, so it stays invisible to backlog
  regen; worth converting to a real todo on a future pass.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified all 5 still resolve; unchanged.
- **live GCS spot-check 2026-08-20**: ran this doc's own prescribed Success-criteria check for real (via
  `unified_trading_library.cloud_interface`, never raw gsutil/gcloud) against PROD. Result: cefi/tradfi/sports/
  prediction tick-data buckets + cefi/tradfi/sports instruments-store buckets all confirmed DONE (source-aware
  `pipeline_mode=` present, incl. on current-day objects, not just historical); prediction's instruments-store bucket
  confirmed the one real open gap (0/682 `canonical_question_group=` groups carry the segment). Also checked
  requirements drift since 2026-06-01 authoring per operator request: the canonical form itself moved to source-aware
  `{mode}_{source}[_{transport}]` (ratified 2026-06-07, codex `/codex/02-data/pipeline-mode-partition.md`) — this
  didn't invalidate what's landed (it's already source-aware everywhere it exists) but the plan's original "segment
  present" success criterion never named that bar; tightened it. Also traced the "instruments" row's true current
  owner: the archived 2026-06-01 instruments-canonicalisation plan's apply-work was folded 2026-06-26 →
  3-way-split 2026-07-24 → now lives in `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`'s open "C0"
  rider — corrected the coverage table + Phase 1 pointer away from the archived doc. Flipped Phase 1's
  cefi/tradfi/sports/prediction-tick-data and cefi/tradfi/sports-instruments todos to `[x]`; split prediction's
  instruments gap out as its own open todo with the corrected current-owner pointer. Not actioned (outside this
  plan's scope, flagged for the other plan's own maintainers): `instruments_store_cf_canonicalization_single_walk_
  2026_07_24.md`'s "C0" checkbox still reads `[ ]` open for cefi/tradfi even though live GCS shows those two AGs
  already carry the partition — a cross-plan doc-drift, not resolved here (collision risk).

- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — sole open item
  (prediction instruments-bucket gap) is already correctly cross-referenced to
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`'s own "C0" todo as the live tracked owner, with
  an explicit "do NOT open a second walk here (single-walk discipline)" note — no citation fix needed, already
  self-consistent.
