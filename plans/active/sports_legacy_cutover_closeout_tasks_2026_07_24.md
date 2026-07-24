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

- [ ] [REVIEW] P1. **T6.7 — Post-phase codex audit (HARD RULE).** _Mechanism_: update
      `/codex/02-data/sports-gcs-path-ssot.md` (legacy shape is now GONE — no reader should special-case it),
      `/codex/02-data/bucket-naming-and-config.md` (the last no-env Group-A twin is retired),
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` (legacy consolidator entries permanently removed);
      SUPERSEDED-banner anything the cutover invalidated. _Gate_: every codex path named here is either updated or
      explicitly confirmed unaffected. _ABORT_: none (review-blocking if skipped).
- [ ] [INFRA] P2. **T6.8 — Retire the one-offs + the dead knob + the false-progress tick.** _Mechanism_: per each file's
      own `Delete-when` (all satisfied once T5.4 lands + orphan-sweep = 0): delete `migrate_sports_canonical_v9.py`,
      `migrate_legacy_tick_buckets_to_canonical.py`, `patch_l6_legacy_manifest_{is,mtds}_2026_06_29.py`, and the ~26
      legacy-reading `instruments-service/scripts/**` one-offs. **Also delete the doubly-broken gate**
      `market-tick-data-service/market_tick_data_service/scripts/verify_v1_archive_row_coverage_2026_06_27.py` — see
      RISK-9; leaving it is a trap that re-issues a false COVERED verdict. **Retire the now-dead
      `include_legacy_archive` knob** from UAC `gcs_paths.py`/`partition_paths.py`
      (`rg 'include_legacy_archive\s*=\s*True'` → **zero hits** workspace-wide; the workspace bans shims). **Un-tick /
      annotate** the plan item `- [x] ✅ [DATA] P0.     v1_archive ROW-coverage gate` in
      `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md` — it was ticked on _"GATE SCRIPT SHIPPED"_
      evidence (`market-tick-data-service@18ca0e23`), i.e. on **shipping a script, never on a verified run of it**; that
      is exactly the false-progress class the commit+flip rule targets. Also correct that plan's standing claim that
      v1_archive is _"COLUMN-superseded by the union of understat_xg + v2 fixtures + v2 fixture_stats"_ —
      wrong-but-harmless: it is superseded by **v2 fixtures ALONE**, because the columns that supposedly required the
      union are 100% empty. _Gate_: `rg -c 'sports-central-element-323112'` workspace-wide → 0. _ABORT_: none.

> **Note on T6.8's cross-reference** — it names `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md`.
> This plan was flagged bucket (a) (stale-not-moved, locked) in the line-cap remediation triage and has now been
> archived (frontmatter unlocked + `status: superseded` confirmed, `git mv` to `plans/archive/2026_07/`) — T6.8's
> un-tick/annotate action above has been retargeted to the archived path accordingly.

## Sibling plan

Forked alongside
[`sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`](/plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)
(the other disjoint open-item group carved out of the same parent in the same remediation pass).
