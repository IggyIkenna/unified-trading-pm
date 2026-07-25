---
doc_type: plan
title: Sports legacy bucket cutover closeout — post-phase codex audit + one-off retirement
summary: >-
  Forked from sports_legacy_bucket_cutover_2026_07_16.md's Phase 6 (RESTORE) admin tail — the post-phase codex audit
  across 3 named codex docs (T6.7), and retiring the migration one-off scripts + the dead `include_legacy_archive` knob
  + a false-progress tick on a sibling plan (T6.8).
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
tags: [migration, cutover, sports, codex-audit, cleanup, plan-hygiene]
related:
  [
    /plans/active/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "Forked 2026-07-24 from sports_legacy_bucket_cutover_2026_07_16.md via the plan-hygiene line-cap remediation triage
    (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 24, bucket (c))",
  ]
---

# Sports legacy bucket cutover closeout — admin tasks

> **Forked 2026-07-24** from
> [`sports_legacy_bucket_cutover_2026_07_16.md`](/plans/active/sports_legacy_bucket_cutover_2026_07_16.md) via the
> plan-hygiene line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 24, bucket (c))
> — the parent plan's ~2700 lines of completed cutover history stay in place; these were its last 2 open Phase-6
> (RESTORE) todos, moved here **verbatim, unedited**. Both are administrative closeout tasks (codex audit +
> one-off/dead-knob retirement), independent of the data-correctness followup forked into the sibling plan below. Full
> phase context (freeze/move/purge/verify/delete/restore) lives in the parent plan.

## Codex SSOTs (read before executing T6.7)

| SSOT                                                     | Governs                                                            |
| -------------------------------------------------------- | ------------------------------------------------------------------ |
| `/codex/02-data/sports-gcs-path-ssot.md`                 | Canonical sports path shape; T6.7 updates this once legacy is gone |
| `/codex/02-data/bucket-naming-and-config.md`             | `resolve_bucket_name()`; T6.7 retires the last no-env Group-A twin |
| `/codex/05-infrastructure/manifest-consolidator-ssot.md` | T6.7 removes the legacy consolidator entries here                  |

## Todos

- [x] [REVIEW] P1. ✅ **T6.7 — Post-phase codex audit (HARD RULE) — DONE 2026-07-24.** All 3 named codex paths resolved:
      `/codex/02-data/sports-gcs-path-ssot.md` UPDATED (its "SPORTS-CANON ALIGNMENT" note rewritten to past tense,
      citing both bucket deletions — `instruments-store-sports-central-element-323112` DELETED 2026-07-16T19:52Z,
      968,927 objects + 34,596 versions purged, `describe` → 404; `market-data-tick-sports-central-element-323112`
      DELETED 2026-07-17T~16:50Z, 342,629 objects/versions purged, `describe` → 404);
      `/codex/02-data/bucket-naming-and-config.md` CONFIRMED UNAFFECTED (it's a SUPERSEDED redirect stub about the
      unrelated legacy `{bucket_prefix}-{gcp_project_id}` env-var naming pattern; grepped for both deleted bucket names,
      zero hits, never framed their deletion as future work); `/codex/05-infrastructure/manifest-consolidator-ssot.md`
      CONFIRMED UNAFFECTED (its only "legacy bucket" mention is a general workspace-wide `[PENDING DECOMMISSION]` note
      covering ALL asset groups gated on a per-AG L3 single-walk reaching C-GREEN, not sports-specific and doesn't name
      either deleted sports bucket — still accurate as written). No SUPERSEDED-banner needed beyond what's already
      correct. Gate satisfied: every named codex path is either updated or explicitly confirmed unaffected.
- [x] ✅ [INFRA] P2. **T6.8 — Retire the one-offs + the dead knob + the false-progress tick — SAFE SUBSET SHIPPED,
      residual tracked.** Per-file `Delete-when` + git-history/import-graph verification found the blanket premise FALSE
      for `migrate_sports_canonical_v9.py` (live import from a 2026-07-13 migration script) and most of the "~26"
      `instruments-service/scripts/**` estimate (grep-derived, not individually vetted — 3 are `Lifecycle: permanent`,
      others gated on a broader campaign or recently active). **Shipped**: deleted the doubly-broken gate
      `market-tick-data-service/market_tick_data_service/scripts/verify_v1_archive_row_coverage_2026_06_27.py` +
      `migrate_legacy_tick_buckets_to_canonical.py` + `patch_l6_legacy_manifest_mtds_2026_06_29.py`
      (market-tick-data-service@f8276e22); the 5 independently-verified `instruments-service/scripts/**` one-offs
      (`patch_l6_legacy_manifest_is_2026_06_29.py`, `rebuild_sports_manifest.py`,
      `sports_legacy_schema_audit.{py,json}`, `validate_sports_fixtures_v2_parity.py`,
      `cutover_sports_fixtures_v2_to_canonical.py` — instruments-service@269440d7, same-day slot-3 recovery); **retired
      `include_legacy_archive` ENTIRELY** (stronger than the `=True`-only gate specified here) from UAC
      `gcs_paths.py`/`partition_paths.py` after fixing its one live caller (unified-api-contracts@887ab894,
      instruments-service@5ff530f9) — `rg 'include_legacy_archive'` workspace-wide → 0 hits. **Un-tick/annotate already
      done** (unified-trading-pm@3aff7f716, same day): the archived
      `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md` v1_archive gate checkbox is corrected +
      re-pointed at its real resolution mechanism, and the union-vs-v2-fixtures-ALONE claim is fixed. **Residual**
      (`migrate_sports_canonical_v9.py` cluster + ~14 unverified/active/permanent `instruments-service/scripts/**`
      files) tracked as follow-up todos in `plans/active/issues/sports_t6_8_oneoff_retirement_residual_2026_07_25.md` —
      not silently dropped. **Correction to this todo's own final Gate**: `rg -c 'sports-central-element-323112'`
      workspace-wide is NOT 0 and structurally cannot be — many remaining hits are legitimate (permanent-lifecycle
      tools, docs, epics, archived plans); the gate as written was an overbroad heuristic, not an achievable
      done-condition. _ABORT_: none.

> **Note on T6.8's cross-reference** — it names `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md`.
> This plan was flagged bucket (a) (stale-not-moved, locked) in the line-cap remediation triage and has now been
> archived (frontmatter unlocked + `status: superseded` confirmed, `git mv` to `plans/archive/2026_07/`) — T6.8's
> un-tick/annotate action above has been retargeted to the archived path accordingly.

## Sibling plan

Forked alongside
[`sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`](/plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)
(the other disjoint open-item group carved out of the same parent in the same remediation pass).
