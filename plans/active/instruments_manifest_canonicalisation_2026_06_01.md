---
title:
  "Instruments-service manifest + data canonicalisation (audit-first single-walk) — L3 owner for the instruments I/O
  surface"
created: 2026-06-01
author: ikenna
parent_epic: epics/instruments_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER (per-service canonicalisation axis — instruments was uncovered)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12 — the invariants this walk lands)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Instruments-service manifest + data canonicalisation (L3 owner for the instruments I/O surface)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, per-service axis). Instruments-service is the
> **input (I/O) side** of the data pipeline — it owns reference data (instrument records, universe, fixtures, capability
> snapshots) that everything downstream reads. Its `_index`(es) + objects need the SAME canonical form as the MTDS tick
> buckets. **Single-walk discipline (HARD RULE)**: one bundled walk per instruments bucket — bundle every CF invariant
> (CF-1…CF-12 in `canonical_form_cross_service_audit_checklist.md`). Do NOT open a second walk;
> `pipeline_mode_partition_migration` + `data_source_provenance` ride THIS walk.

## Why this exists — the per-AG plans cover MTDS, not the instruments surface

The per-AG manifest-canonicalisation plans (defi/cefi/tradfi/sports/prediction) canonicalise the **MTDS**
`market-data-tick-{ag}` buckets. Instruments-service writes a **separate** surface (`instruments-store-{ag}` +
reference/instrument-record indices) that no per-AG plan covers — yet it carries the same legacy debt: `category=` not
`asset_group=`, no `pipeline_mode=` partition, schema_version spread (read DATA-STATE — `pipeline_mode_partition`
already lists `instruments` as pending), `source` in path/blank not column, untyped empty reasons, possible
date-impossible phantom rows. This plan is the instruments analogue of the AG §C single-walk, **audit-first** (we read
the actual instruments `_index` state before migrating — manifest-v8 lesson).

## Scope boundary — no overlap with the per-AG walks

- **`instruments-store-sports`** canonical FORM rides the SPORTS walk: `sports_manifest_canonicalisation_2026_06_01.md`
  already claims the sports reference surface + owns the sports-specific CF-5 typed-reason relabel (fixture/season/
  transfer-window/genesis via the sports coverage oracle). This plan does NOT re-walk the sports instruments bucket — it
  provides the cross-service CF audit coverage and owns the **non-sports** AG instruments-store buckets
  (`instruments-store-{cefi,defi,tradfi,prediction}`) + the cross-AG instrument-record/universe indices.
- **`source` write-path code** for sports `FIXTURES` (multi-source) already shipped (instruments-service@6bbd6919 per
  `data_source_provenance` Phase 4); this plan re-consolidates source into the instruments `_index` as a RIDER.
- **MTDS tick buckets** are NOT in scope (per-AG plans own them).

## Sequencing — gate before any instruments backfill (inherits master HARD RULE)

No instruments backfill / writer relaunch until each in-scope instruments bucket's walk is C-GREEN (master L3-gates-L5).
L0 tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a
VM. Runs behind the pre-migration drain.

## Canonical target form (instruments-service) — per CF-1…CF-12

| Dimension       | Legacy / now                                    | Canonical (target)                                                           | CF    |
| --------------- | ----------------------------------------------- | ---------------------------------------------------------------------------- | ----- |
| Bucket          | `instruments-store-{ag}-{project}` (verify env) | `instruments-store-{ag}-{env}-{project}` (env-split, `resolve_bucket_name`)  | CF-9  |
| asset-group key | `category=` (paths + rows)                      | `asset_group=` (paths + manifest rows)                                       | CF-2  |
| pipeline_mode   | absent in path (`pipeline_mode` pending here)   | `pipeline_mode=` hive partition                                              | CF-3  |
| schema_version  | read DATA-STATE spread                          | v9 (data-state verified)                                                     | CF-1  |
| source          | path/blank                                      | `source` COLUMN (multi-source `FIXTURES`=2 rows; co-mingled, not a path key) | CF-4  |
| empty reason    | blank / mislabeled                              | typed `EmptyConfirmedReason` (sports fixture set rides the sports plan)      | CF-5  |
| names           | possible drift                                  | canonical data_type (underscore) + entity/league keys                        | CF-7  |
| available_at    | per-row (verify)                                | preserve / honest poll-time (no lookahead)                                   | CF-8  |
| phantom         | possible date-impossible rows                   | object-backed captured only                                                  | CF-10 |

## Phased execution

### P0 — instruments canonical-form AUDIT (run the SSOT checklist for the instruments surface)

- [ ] [DATA] P0. Run the CF-1…CF-12 checks (per `canonical_form_cross_service_audit_checklist.md`) against each in-scope
      instruments `_index` + sample objects: read the actual `schema_version` distribution, `category=` vs
      `asset_group=` on paths + rows, `pipeline_mode=` partition presence, `source` column blank-rate, empty-reason
      histogram, name drift, date-impossible captured rows. Emit a per-CF GREEN/RED with data-state evidence. This is
      the audit the operator re-runs; it feeds `instruments_master_audit_instructions.md` Canonical-form section.
- [ ] [DATA] P0. Confirm which instruments buckets are AG-partitioned vs cross-AG; record object counts to migrate.

### C — single-walk (bundled CF-1…CF-12) per in-scope instruments bucket

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled walk per non-sports instruments bucket: `category=`→`asset_group=` (paths + rows,
      CF-2) + `pipeline_mode=` partition (CF-3, RIDER — satisfies `pipeline_mode_partition_migration` instruments row) +
      v9 re-version (CF-1, data-state asserted) + env-split (CF-9) + canonical names (CF-7) + `available_at` preserve
      (CF-8) + phantom relabel (CF-10). Server-side `gcs_copy_object`, layout-aware. RUN ON A VM (gated on L0) or local
      if P0 says small.
- [ ] [DATA] P1. C-source RIDER (CF-4): re-consolidate the `source` column into the instruments `_index` (multi-source
      `FIXTURES`=2 rows). Folds `data_source_provenance` instruments-side re-consolidation — no separate walk.
- [ ] [CODE] P1. C-reasons (CF-5): instruments writers emit typed `EmptyConfirmedReason` (non-sports AGs) so future
      writes are honest; fetch-failure → `attempted_failed` not `empty_confirmed` (CF-11 swallow sweep).

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: re-run the P0 CF audit → all CF GREEN (data-state) for every in-scope instruments bucket; 0
      legacy-only cells vs canonical. C-GREEN signal for `bucket_name_ssot…` L6 instruments legacy decommission.

## Success criteria

- Every in-scope instruments `_index` = v9 + `asset_group=` + `pipeline_mode=` partition + `source` column + typed
  reasons + canonical names + honest `available_at` (CF-1…CF-12 GREEN, data-state).
- Sports instruments surface confirmed owned by the sports plan (no double-walk); cross-AG instruments indices
  canonical.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy instruments buckets deletable; instruments writer relaunch unblocked.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — instruments canonical form.
- `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — the CF checklist this walk lands +
  `instruments_master_audit_instructions.md` Canonical-form coverage section.
