---
doc_type: plan
title: Sports legacy bucket cutover — freeze, move, purge, delete, restore
summary:
  Executable cutover runbook retiring the last two non-canonical sports buckets — instruments-store-sports-* and
  market-data-tick-sports-* — into their -prd- canonical twins. Synthesised from five read-only audits (code, infra,
  objects, manifests, v1_archive). Freeze writers, repoint the static legacy declarations, MOVE only the 30,333
  object-layer-verified unique objects to canonical paths, purge the 123,149 bogus index rows in the quiet window, prove
  zero-unique at the OBJECT layer, then delete and restore in reverse.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    deployment-service,
    market-tick-data-service,
    instruments-service,
    deployment-api,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [migration, bucket-canonicalisation, cutover, gcs, terraform, manifest, sports, destructive]
related:
  [
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_07/sports_data_sources_canonical_completion_2026_07_13.md,
    ../epics/sports_master.md,
    /plans/archive/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md,
    /plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md,
    /plans/archive/2026_07/sports_legacy_bucket_cutover_history_2026_07_24.md,
  ]
created: 2026-07-16
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator request 2026-07-16, 5-leg read-only audit 2026-07-16]
---

# Sports legacy bucket cutover — 2026-07-16

> **DESTRUCTIVE PLAN. Phases are STRICTLY SEQUENTIAL. Phase 5 (delete) is gated on Phase 4 (proof) and a FINAL
> live-writer re-check.** Every phase todo carries a Mechanism, a Verification, and an ABORT condition. An ABORT means
> STOP the phase and escalate — it never means "note it and continue."

**Operator goal (2026-07-16, verbatim)**: _"instruments-store-sports-central-element-323112 doesnt need to exist whilst
instruments-store-sports-prd-central-element-323112 exists — its the last instrument store bucket which has non
canonical [paths]. For that to migrate it needs us to ensure all the code and deployed vms and cloud run/service etc and
manifests and catalogues etc all migrate fully to the canonical bucket usage, and to avoid redownloading we should
instead MOVE any non already existent data into the canonical bucket."_ Operator additionally authorises _"stopping all
sports related crons and vms and cloud stuff to make the migrations and fixes and bucket deletes then rerunning
everything so sports is in canonical buckets and paths."_

| Legacy (delete)                                   | Canonical (survives)                                  |
| ------------------------------------------------- | ----------------------------------------------------- |
| `instruments-store-sports-central-element-323112` | `instruments-store-sports-prd-central-element-323112` |
| `market-data-tick-sports-central-element-323112`  | `market-data-tick-sports-prd-central-element-323112`  |

## Codex SSOTs (read before executing the phase that cites them)

| SSOT                                                            | Governs                                                          |
| --------------------------------------------------------------- | ---------------------------------------------------------------- |
| `/codex/02-data/sports-gcs-path-ssot.md`                        | Canonical sports path shape; `candidate_parquet_paths()`         |
| `/codex/02-data/pipeline-mode-partition.md`                     | `{mode}_{source}` segment placement; readers PREFIX-MATCH        |
| `/codex/02-data/availability-manifest-and-data-status.md`       | 4-state `capture_status`; per-VM shards; consolidator contract   |
| `/codex/02-data/honest-absence-downstream-handling.md`          | Phantom vs real absence; never fake `record_captured`            |
| `/codex/02-data/data-pipeline-correctness-hard-rule.md`         | Audit issues fixed in FULL; RED freezes layer N+1                |
| `/codex/02-data/bucket-naming-and-config.md`                    | `resolve_bucket_name()` is the only name producer                |
| `/codex/02-data/sports-data-source-coverage-matrix.md`          | `ODDS` writer is footystats only — no api_football odds path     |
| `/codex/05-infrastructure/gcs-object-operations.md`             | UTL `gcs_copy_object`/`gcs_delete_object` — never `gsutil`       |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md`        | Consolidator is Cloud Run; loud-fails on stale index             |
| `/codex/05-infrastructure/vm-launcher-runbook.md`               | Registered launchers; `VM_PREFIX_TO_BUCKET`; pre-migration drain |
| `/codex/05-infrastructure/deployment-service-gcp-tofu-state.md` | Terraform state ops; `state rm` vs `destroy`                     |
| `/codex/06-coding-standards/script-homes.md`                    | One-off lifecycle markers; delete-after-prod-run                 |

---

## ✅ FINAL STATUS (as of 2026-07-24) — both legacy buckets deleted, cutover complete

**Both legacy buckets are DELETED and this plan's own 45 todos (Phase 0-6) are all `- [x]` complete**:

- `instruments-store-sports-central-element-323112` — **DELETED 2026-07-16T19:52Z** (T5.4). 968,927 objects + 34,596
  versions purged, 0 errors; `describe` → 404; no-resurrection proved by a clean `tofu plan` (zero actions referencing
  the deleted bucket).
- `market-data-tick-sports-central-element-323112` — **DELETED 2026-07-17T~16:50Z** (T5.4 MDT half). OR-5b resolved
  (32-day / 549,392-key recovery landed into canonical, content-verified `legacy_only==0` on every gap day, zero loss);
  342,629 objects/versions purged, 0 errors; `describe` → 404; no-resurrection proved the same way
  (`deployment-service@1116901`).
- Phase 6 (RESTORE) completed 2026-07-17: all writers/consolidators/schedulers un-paused in reverse freeze order, every
  first run GREEN on canonical.

**This plan forked its last 4 open todos out to two sibling child plans on 2026-07-24** (via the plan-hygiene line-cap
remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 24, bucket (c)):

- [`sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`](/plans/archive/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)
  — T2.9 (MDT `(sports, odds, trades)` schema-contract drift) + T2.10 (47,253 phantom `api_football × trades` rows,
  entangled with `_legacy_seed.parquet`/OR-4/OR-5b). Both still open, P0.
- [`sports_legacy_cutover_closeout_tasks_2026_07_24.md`](/plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md)
  — T6.7 (post-phase codex audit) + T6.8 (retire the migration one-offs + dead `include_legacy_archive` knob + a
  false-progress tick). Both still open, P1/P2.

**Everything else — THE HEADLINE analysis (findings F-1..F-5), the full Phase 0-6 Todos section (all 45 checked), the
Deferred-work table, Risk Register, Rollback plan, Operator Rulings Needed (all resolved), and the entire Progress Log —
was moved VERBATIM, unedited, into**
[`sports_legacy_bucket_cutover_history_2026_07_24.md`](/plans/archive/2026_07/sports_legacy_bucket_cutover_history_2026_07_24.md)
on 2026-07-24, to bring this parent under the plan-hygiene line-count cap (`scripts/plan-hygiene/check_line_caps.sh`;
this plan is not umbrella-exempt — 45 todos is under the 100-todo exemption threshold and it carries no `locked_by`/
`umbrella: true` marker — so the applicable hard cap is 1000 lines, not the 2000-line umbrella cap). **Nothing was
deleted** — read the history file for the complete original text, including every gate, measurement, and the
2026-07-16/17 Progress Log entries.

> **🔴 DO NOT run a full `tofu apply` on prod** — it would resurrect `instruments-store-cefi-…` (404 but still declared
>
> - in state) and make 71 unaudited changes →
>   [`issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md`](issues/terraform_instruments_cefi_armed_resurrection_2026_07_16.md).
>   Full detail on why the two Phase-1 applies were never needed is in the history file's headline banner.
