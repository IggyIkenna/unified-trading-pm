---
title:
  "pipeline_mode on-disk partition migration — bundle pipeline_mode= hive partition into each bucket's next whole-corpus
  walk"
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-01
locked_by: live-defi-rollout
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
> caught). SSOT: `codex/02-data/defi-canonical-naming-ssot.md`. For non-DeFi AGs this remains a column-scan interim per
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

- `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` — documents the deferred-partition note; flip the
  "deferred to next migration window" line to "landed per-bucket" as each bucket's walk completes.

## Composes with

- `defi_manifest_canonicalisation_2026_06_01.md` (§MASTER + §C) — DeFi bucket carries the partition inside its C0
  single-walk; the MASTER's CONFLICT-1 codifies this plan as a RIDER (never its own walk).
- `cefi_manifest_canonicalisation_2026_06_01.md` / `tradfi_manifest_canonicalisation_2026_06_01.md` /
  `sports_manifest_canonicalisation_2026_06_01.md` / `prediction_manifest_canonicalisation_2026_06_01.md` — each carries
  the `pipeline_mode=` partition as a named C-pipeline_mode rider in its single-walk.
- Single-walk discipline (HARD RULE — CLAUDE.md § Manifest + honest absence).
