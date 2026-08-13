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
last_updated: 2026-06-27
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
| **instruments** | (no canonicalisation plan yet — bundle into IS's next walk) | pending — see Phase 1 |

## Phased execution

### Phase 1 — Bundle `pipeline_mode=` into each non-DeFi bucket's next whole-corpus walk

- [ ] [INFRA] P2. **cefi / tradfi / sports / prediction** — the `pipeline_mode=` partition is the named C-pipeline_mode
      RIDER inside each AG's L3 manifest-canonicalisation walk (table above). This plan's row for each AG is satisfied
      when that walk completes — do NOT open a standalone partition walk (single-walk discipline). Verify post-walk:
      selective path-listing on `pipeline_mode=batch` / `pipeline_mode=live` returns the expected file set; manifest row
      keys unchanged.
- [ ] [INFRA] P2. **instruments bucket** — no canonicalisation plan exists yet; bundle `pipeline_mode=` into
      instruments-service's next scheduled whole-corpus walk. Coordinate window with the IS migration owner.

## Success criteria

| Phase   | Gate                                              | Verification                                                      |
| ------- | ------------------------------------------------- | ----------------------------------------------------------------- |
| Phase 1 | `pipeline_mode=` partition present in all buckets | `gcs ls` shows `pipeline_mode=` path segment across all 5 buckets |

## Codex SSOTs

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
