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
---

**MIGRATED FROM:** `plans/archive/2026_06/pipeline_mode_implementation_2026_05_28.md` Phase 5 (on-disk partition —
DEFERRED at column-level completion 2026-05-28; single-walk discipline forbids a standalone partition-key walk, so the
work splits into this named successor that piggybacks on the next whole-corpus walk window per bucket).

# pipeline_mode on-disk partition migration

The `pipeline_mode` **column-level** implementation shipped fully in `pipeline_mode_implementation_2026_05_28` (Phases
0–4 + 6: 43.5M rows backfilled, QG STEP 5.85 enforces enum-only writes, batch-live-reconciliation consumes
`GROUP BY pipeline_mode`, manifest carries the column). The remaining work is promoting `pipeline_mode` from a column to
an **on-disk hive partition key** in the GCS path: `day=…/pipeline_mode=…/asset_group=…/venue=…/…`.

Partition-key addition is **review-blocking outside a whole-corpus migration window** (single-walk discipline — HARD
RULE). It MUST bundle into each bucket's next scheduled whole-corpus walk; a standalone partition-only walk is
forbidden. Reads filter by column-scan (low cardinality, ~10 enum values) until the partition lands — acceptable interim
performance per the parent plan's "Out of scope" note.

## Coverage status

- **DeFi bucket** — ALREADY bundled into `defi_manifest_canonicalisation_2026_06_01.md` C0 single-walk (its derivation
  table row: `Pipeline mode | absent in path | pipeline_mode= hive partition (value batch or live)`). Tracked there; no
  separate action in this plan.
- **cefi / tradfi / sports / prediction / instruments buckets** — pending. Each adds the `pipeline_mode=` partition key
  when its next whole-corpus walk runs.

## Phased execution

### Phase 1 — Bundle `pipeline_mode=` into each non-DeFi bucket's next whole-corpus walk

- [ ] [INFRA] P2. For each of {cefi, tradfi, sports, prediction, instruments} buckets, add `pipeline_mode=` to the
      on-disk partition path during that bucket's next scheduled whole-corpus walk (NOT a standalone walk — single-walk
      discipline). Verify post-walk: selective path-listing on `pipeline_mode=batch` / `pipeline_mode=live` returns the
      expected file set; manifest row keys unchanged. Coordinate window with the bucket/manifest migration owner.

## Success criteria

| Phase   | Gate                                              | Verification                                                      |
| ------- | ------------------------------------------------- | ----------------------------------------------------------------- |
| Phase 1 | `pipeline_mode=` partition present in all buckets | `gcs ls` shows `pipeline_mode=` path segment across all 5 buckets |

## Codex SSOTs

- `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md` — documents the deferred-partition note; flip the
  "deferred to next migration window" line to "landed per-bucket" as each bucket's walk completes.

## Composes with

- `defi_manifest_canonicalisation_2026_06_01.md` — DeFi bucket carries the partition inside its C0 single-walk.
- Single-walk discipline (HARD RULE — CLAUDE.md § Manifest + honest absence). </content> </invoke>
