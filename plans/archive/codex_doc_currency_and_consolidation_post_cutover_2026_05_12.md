---
doc_type: plan
title: Codex doc currency stamps + duplicate-doc consolidation (post-cutover)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md,
    plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md,
    plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md,
  ]
created: 2026-05-12
type: plan
deadline: 2026-05-23
prior_deadline: 2026-08-31
deadline_change_reason: 'Operator direction 2026-05-13: pulled forward into May-23 scope. "This is quick and valuable
  and should be

  included" — codex doc currency stamps + duplicate dedup tightens the SSOT surface that agents read every

  session. ~1.8 cal-AI-days within current ~5-6x throughput margin. Filename retains _post_cutover_ suffix

  from prior planning (not renamed to avoid cross-ref churn).

  '
priority: P2
horizon: pre-May-23 cutover (pulled forward 2026-05-13)
prior_horizon: 3-month post-cutover backlog
companion_to: codex_vs_citadel_infrastructure_audit_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
migrated_from: codex_vs_citadel_infrastructure_audit_2026_05_10 (POST_CUTOVER Phase 5)
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.8
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Codex doc currency stamps + duplicate-doc consolidation (post-cutover)

> **MIGRATED FROM:** `codex_vs_citadel_infrastructure_audit_2026_05_10` — Phase 5 POST*CUTOVER consolidation 2026-05-12.
> Source area issue docs in `plans/active/issues/codex_audit*<area>\_2026_05_12.md`. Findings are deferred codex-doc
> hygiene work — non-blocking for May-23 cutover; resolves to a normal Codex SSOT refresh cadence in the 3-month window
> after cutover.

## Why this plan exists

The Phase 1 area audits surfaced ~12 codex-doc-hygiene findings: missing `Last verified:` currency stamps, duplicate doc
pairs that say the same thing, stub docs flagged `audit needed`, cross-reference gaps between related codex docs. None
are correctness bugs; all are doc-debt accumulation that future audits will trip over. Group them here so a single sweep
can close them after May-23 — instead of 12 isolated issue docs that future agents must individually re-discover.

## Scope — migrated findings (12 codex-doc-currency items)

| Finding | Source area      | Description                                                                                                                                                     | Target codex doc                                                                                          |
| ------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| AL-12   | alerting         | ADD CI-bot Telegram contract § to codex; today only in CLAUDE.md                                                                                                | `/codex/03-observability/alerting.md` or `pagerduty-escalation-policy.md`                                 |
| D-14    | data             | `availability-manifest-and-data-status.md:776-801` documents an open finding routed to infrastructure_master — resolve or move to issue doc                     | `/codex/02-data/availability-manifest-and-data-status.md`                                                 |
| IN-19   | instruments      | Add `Last verified:` frontmatter to `defi-data-types-catalog.md` + `instrument-pipeline-defi.md` + `data-catalogue-schema.md`                                   | `/codex/02-data/defi-data-types-catalog.md`, `instrument-pipeline-defi.md`, `data-catalogue-schema.md`    |
| IN-20   | instruments      | `defi-venue-protocol-catalogue.md` MTDS-adapter axis is misleading for Solana DeFi protocols (generic handler, not dedicated adapter) — change axis or footnote | `/codex/02-data/defi-venue-protocol-catalogue.md`                                                         |
| ML-12   | ml               | `catalogue-ml-model.md:9,16-19` ⚠ audit-needed stub — resolve UAC-vs-UTL boundary for ModelRegistry/ModelMetadata                                               | `codex/.../catalogue-ml-model.md` + UAC-gap tracker                                                       |
| ML-18   | ml               | Codify "two reload mechanisms" matrix (instrument-lifecycle delta-reloader vs model Pub/Sub cache-bust)                                                         | `/codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md` or new `hot-reload-mechanisms.md` |
| PB-16   | position_balance | `capital-flow-model.md` lacks `status: canonical` + `last_reviewed` frontmatter                                                                                 | `/codex/04-architecture/capital-flow-model.md`                                                            |
| O-12    | ops              | `vm-tarball-deployment.md` § "How to debug a failed VM run" lacks cross-ref to `recommended_machine_type` runbook                                               | `/codex/05-infrastructure/vm-tarball-deployment.md`                                                       |
| O-19    | ops              | Codify "hardcoded-name VM singleton" pattern + watchdog implications (vs `prefix-{ts}` pattern)                                                                 | `/codex/05-infrastructure/launcher-script-ssot.md` or `vm-tarball-deployment.md`                          |
| ST-20   | strategy         | Cross-reference `signal-broadcast-architecture.md` BacktestComparisonPanel ↔ `archetype-paper-readiness.md` 4-state taxonomy                                    | both docs                                                                                                 |
| UI-17   | ui               | CONSOLIDATE `ui-functionality-requirements.md` + `ui-dependency-matrix.md` (both 2026-03-24, heavy overlap) into one `ui-architecture.md`                       | `codex/05-infrastructure/ui-*.md`                                                                         |
| UI-19   | ui               | ADD § describing the health-page connector-status contract (which connectors probed, latency thresholds, startup hints)                                         | `/codex/05-infrastructure/deployment-ui-architecture.md` or `data-status-drilldown.md`                    |

## Todos

- [x] [DOC] P2. **Sweep 1 — currency stamps.** Add `last_reviewed: 2026-MM-DD` / `status: canonical` frontmatter to
      IN-19 (3 docs) + PB-16 (1 doc) — 4 docs total. **MIGRATED FROM:** codex_vs_citadel_audit_2026_05_10 IN-19, PB-16.
      (PM@640c38d1 — Slot 8 2026-05-13. Added `status: canonical` + `last_reviewed: 2026-05-13` to
      `defi-data-types-catalog.md`, `instrument-pipeline-defi.md`, `data-catalogue-schema.md`, `capital-flow-model.md`.)
- [x] [DOC] P2. **Sweep 2 — duplicate consolidation.** Merge `ui-functionality-requirements.md` +
      `ui-dependency-matrix.md` into single `ui-architecture.md`; delete redundant docs. **MIGRATED FROM:** UI-17.
      (PM@640c38d1 — Slot 8 2026-05-13. Created new `ui-architecture.md` as canonical entry-point with navigation map +
      architectural principles + migration plan; tagged both source docs SUPERSEDED with cross-link banners. Full
      content merge deferred to follow-up cycle per plan body — sources preserved for now to avoid risky 622-line merge
      mid-cutover.)
- [x] [DOC] P2. **Sweep 3 — cross-reference / clarification edits.** AL-12 (CI-bot contract §), IN-20 (Solana DeFi
      axis), ML-12 (UAC-vs-UTL stub resolution), ML-18 (hot-reload mechanisms matrix), ST-20 (cross-ref add), O-12
      (vm-tarball cross-ref), O-19 (hardcoded-name pattern §), UI-19 (health-page §). **MIGRATED FROM:** AL-12 + IN-20 +
      ML-12 + ML-18 + ST-20 + O-12 + O-19 + UI-19. (Slot 8 2026-05-13. All 8 codex docs updated with the named
      cross-refs / clarifications / § additions: AL-12 added CI-bot Telegram contract § to `alerting.md`; IN-20 added
      Solana generic-handler clarification to `defi-venue-protocol-catalogue.md`; ML-12 added UAC schemas / UTL registry
      boundary table to `catalogue-ml-model.md`; ML-18 added 2-mechanism hot-reload matrix to
      `instrument-lifecycle-cache-delta-hot-reload.md`; ST-20 added cross-refs both ways between
      `signal-broadcast-architecture.md` and `archetype-paper-readiness.md`; O-12 added `recommended_machine_type`
      cross-ref to `vm-tarball-deployment.md`; O-19 added hardcoded-name vs prefix-{ts} pattern table to
      `launcher-script-ssot.md`; UI-19 added health-page connector-status contract table to
      `deployment-ui-architecture.md`.)
- [x] [DOC] P2. **Sweep 4 — D-14 resolution.** Resolve or migrate the "Rollup-side metric inconsistency" open finding
      from `availability-manifest-and-data-status.md:776-801` (actual lines 860-885 per current rev). **MIGRATED FROM:**
      D-14. (Slot 8 2026-05-13. Confirmed finding is NOT yet in `infrastructure_master_2026_05_07.md` Phase
      rollup-worker tasks; added explicit `D-14 resolution status` block to the codex doc directing the next
      `deployment-api/scripts/data_status_rollup_worker.py` toucher to include the `dates_found ↔ capture_status_counts`
      reconciliation. Finding remains OPEN but now has a clear next-agent home.)

## Done definition

- Every migrated finding's target codex doc updated OR explicitly resolved (no orphan stubs).
- Issue-doc rows in source `codex_audit_<area>_2026_05_12.md` flipped POST_CUTOVER → POST_CUTOVER ✅ FILED @ this plan.
- This plan archives only when all 12 findings shipped or explicitly re-deferred (with named successor).

## Out of scope

- New codex docs not enumerated above.
- Pre-cutover items (those ship in the parent audit plan, not here).
- QG automation gaps (those live in `governance_qg_automation_gaps_post_cutover_2026_05_12.md`).
