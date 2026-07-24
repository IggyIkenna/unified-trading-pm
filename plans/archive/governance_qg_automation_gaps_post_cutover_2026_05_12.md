---
doc_type: plan
title: Governance HARD RULE automation + QG ratchet gaps (post-cutover)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, strategy-service, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md,
    plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md,
    plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md,
  ]
created: 2026-05-12
type: plan
deadline: 2026-05-23
prior_deadline: 2026-08-31
deadline_change_reason: 'Operator direction 2026-05-13: pulled forward into May-23 scope. "QG is key to good trading
  hardened" —

  fixing governance automation + ratchet gaps pre-cutover means live trading runs with full HARD RULE

  enforcement from day 1, not retrofitted after. Filename retains _post_cutover_ suffix from prior planning

  (not renamed to avoid cross-ref churn).

  '
priority: P1
horizon: pre-May-23 cutover (pulled forward 2026-05-13)
prior_horizon: 3-month post-cutover backlog
companion_to: codex_vs_citadel_infrastructure_audit_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
migrated_from: codex_vs_citadel_infrastructure_audit_2026_05_10 (POST_CUTOVER Phase 5)
estimate_class: design
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 3.0
---

# Governance HARD RULE automation + QG ratchet gaps (post-cutover)

> **ARCHIVED 2026-05-18 (slot 10)** — 100% complete (7/7 checkboxes flipped, every item carries a `**MIGRATED FROM:**`
> annotation citing the source audit finding). Preserved for archaeology. Successor work (where applicable) lives in
> `codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` +
> `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md` (named in frontmatter `related_plans`).

> **MIGRATED FROM:** `codex_vs_citadel_infrastructure_audit_2026_05_10` — Phase 5 POST_CUTOVER consolidation 2026-05-12.
> Source area issue docs in `plans/archive/issues/codex_audit_governance_2026_05_12.md` +
> `codex_audit_data_2026_05_12.md` + `codex_audit_strategy_2026_05_12.md` + `codex_audit_ui_2026_05_12.md` +
> `codex_audit_position_balance_2026_05_12.md` + `codex_audit_alerting_2026_05_12.md`.

## Why this plan exists

A cluster of POST_CUTOVER findings share one shape: a CLAUDE.md HARD RULE or codex architectural rule exists, but its
enforcement is **reviewer discipline only** — no automated grep / QG ratchet / CI gate flags violators. Each individual
gap is small; together they form a class of "rule-without-teeth" technical debt that drifts the system over time. Group
them into one plan so a single QG-ratchet design sweep covers the lot post-May-23.

## Scope — migrated findings (10 QG-automation items)

| Finding | Source area      | Rule (today)                                                                                            | What's missing (QG check / ratchet to add)                                                                                             |
| ------- | ---------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| G-2     | governance       | "Capture Discoveries As Plan Todos Immediately" end-of-cycle audit clause                               | No grep-check enforces every deferral becomes `- [ ]` todo or `**DEFERRED**` annotation                                                |
| G-5     | governance       | Plan-filename convention: `plans/active/` uses `<slug>.md`                                              | Date-suffix variant (`<slug>_2026_MM_DD.md`) — codify which is canonical or normalize                                                  |
| G-8     | governance       | Daily Work-Split Model B polling cadence ~1min                                                          | No cron / scheduler enforces; depends on main-agent foregrounding                                                                      |
| G-12    | governance       | Codex doc freshness                                                                                     | `codex/11-project-management/` 8 docs mix 2026-04 + 2026-05 mtimes; no `last_verified` enforcement                                     |
| G-13    | governance       | "Plan Archival" HARD RULE — operational-completeness audit + deferred migration                         | No automated check; sample archive plans lack `## Deferred work — migrated to:` banner                                                 |
| D-18    | data             | "Cluster validation MANDATORY" QG STEP 5.64                                                             | Codex doc `availability-manifest-and-data-status.md:160-164` lacks cross-link to the QG script path                                    |
| ST-19   | strategy         | `benchmark-fills.md:12` warns "no standalone backtest engines"                                          | No QG step flags new modules under `strategy_service/engine/backtest/` computing P&L without `V2EngineOrchestrator`                    |
| UI-13   | ui               | UI types regen flow (`export_openapi → generate:types`) is manual                                       | No CI gate that committed `openapi.json` hash matches fresh export — generated types can silently rot                                  |
| UI-18   | ui               | "UI must be its own repo (not inside a Python service)" — one-line in `.claude/rules/python-backend.md` | No QG check that fails if a Python service repo contains `package.json` with React/Next/Vite deps                                      |
| PB-19   | position_balance | "PBMS itself must be mode-blind" (no `if mode == 'live'` branches)                                      | No QG ratchet flags `OperationalMode` / `pipeline_mode` branching in `position_balance_monitor_service/` engine/core                   |
| AL-21   | alerting         | "no orphan fired-but-never-cleared alerts" guarantee referenced in `alerting-batch-live.md:81/98`       | No codified check / dashboard surfaces "alert X fired N minutes ago, paired clear event never arrived" (`STALE_OPEN_ALERT` meta-alert) |

(11 findings — AL-21 also has an alerting-lifecycle component that overlaps with the alerting/runbook successor plan;
this plan owns the QG/automation half.)

## Todos

- [x] ✅ [DESIGN] P2. **Group A — Plan-discipline grep-checks (G-2 + G-5 + G-13).** Shipped at
      `unified-trading-pm@<pending>`: `scripts/quality_gates/check_plan_discipline.py` covers all 3 sub-rules: (a)
      `A-deferred-no-banner` — 57 violations; (b) `B-active-filename` — 5 violations + `B-issue-filename` checks; (c)
      `C-archive-no-successor` — 169 violations. Total baseline 231; ratchet-down mode prevents regression while plans
      get touched. Baseline file at `scripts/quality_gates/plan_discipline_baseline.yaml`. PM `quality-gates.sh` wired.
      **MIGRATED FROM:** G-2, G-5, G-13.
- [x] ✅ [DESIGN] P2. **Group A.1 — Runbook Execution-Owner SSOT codification (HARD RULE in CLAUDE.md).** Ship
      `scripts/quality_gates/check_runbook_execution_owner.py` + baseline file + wire into PM's `quality-gates.sh`.
      Walks workspace for `*runbook*.md` (excluding archive) and asserts each declares
      `execution.{owner,cadence,verifier,last_executed}`. Initial baseline = 9 violations (codified at
      `scripts/quality_gates/runbook_execution_owner_baseline.yaml`); ratchet-down mode prevents regression while future
      PRs migrate the 9 existing runbooks to canonical format. Origin issue:
      `plans/archive/issues/runbook_execution_governance_gaps_2026_05_08.md`. Shipped at `unified-trading-pm@<pending>`.
      **MIGRATED FROM:** CLAUDE.md § "Runbook Execution-Owner SSOT (HARD RULE)".
- [x] ✅ [DESIGN] P2. **Group B — Codex freshness ratchet (G-12 + D-18).** Ship
      `scripts/quality_gates/check_codex_doc_freshness.py` + baseline file + wire into PM `quality-gates.sh`. Walks
      `codex/02-data/` + `codex/04-architecture/` + `codex/05-infrastructure/` + `codex/11-project-management/` (206
      docs total) and asserts every `*.md` has `last_reviewed: YYYY-MM-DD` frontmatter + age ≤ 90 days
      (`--staleness-days` configurable). Initial baseline = 188 violations (codified at
      `scripts/quality_gates/codex_doc_freshness_baseline.yaml`); ratchet-down mode prevents regression while future PRs
      add `last_reviewed:` stamps to existing docs. Shipped at `unified-trading-pm@<pending>`. **MIGRATED FROM:** G-12,
      D-18.
- [x] ✅ [DESIGN] P2. **Group C — Architectural ratchets (ST-19 + PB-19 + UI-18).** Generic ratchet helper shipped at
      `unified-trading-pm@<pending>`: `scripts/quality_gates/check_architectural_ratchets.py` + per-rule yaml config at
      `scripts/quality_gates/architectural_ratchets.yaml` + zero-baseline file + PM `quality-gates.sh` wiring. Supports
      3 semantics per rule: `banned_substring`, `banned_pattern` (regex), `banned_unless_contains` + optional
      `condition_pattern`. Current 3 rules: - **ST-19**: `strategy-service/strategy_service/engine/backtest/**/*.py` —
      class with `[Bb]acktest` in name MUST contain `V2EngineOrchestrator`; **0 violations** (runner.py already
      compliant). - **PB-19**: PBMS `core/` + `engine/` — banned `if mode == "live"|"batch"|"paper"` patterns; **0
      violations**. - **UI-18**: 19 Python service repo `package.json` — banned React/Next/Vite/Webpack deps; **0
      violations** (no python service has package.json currently). Baseline 0 across all 3 rules; any new violation =
      regression. **MIGRATED FROM:** ST-19, PB-19, UI-18.
- [x] ✅ [DESIGN] P2. **Group D — Generated-artefact drift gate (UI-13).** Shipped + IMMEDIATELY CORRECTED: First pass
      at `unified-trading-pm@501dbe6d` wired `scripts/quality_gates/check_openapi_drift.py` in warn-only mode. Per
      ikenna-main investigation in `openapi_mirror_drift_2026_05_16.md` § INVESTIGATION, the check compares
      structurally-different files: `unified-trading-api/openapi.json` (61 paths, slim FastAPI facade) vs
      `unified-trading-system-ui/lib/registry/openapi.json` (479 paths, aggregated mirror of multiple backends). Hash
      comparison always shows drift by design — semantic is wrong. **Corrective fix shipped 2026-05-16**: QG wiring
      removed from `scripts/quality-gates.sh`; script docstring rewritten with DEPRECATED banner pointing at the
      architectural fix needed (find canonical aggregator output). Group D **contract** still codified; runtime check
      disabled until aggregator path identified (post-cutover scope). **MIGRATED FROM:** UI-13.
- [x] ✅ [DESIGN] P3. **Group E — Operator-attentiveness automation (G-8).** Resolved via the no-cron option: verified
      2026-05-16 (slot-8) — the "1 min polling cadence" wording lives in `ikenna_orchestrator/AGENT_ONBOARDING.md`
      (intra-side onboarding doc) as a descriptive line, NOT in `cursor-configs/CLAUDE.md` tagged as HARD RULE. The
      de-facto behaviour is already "best-effort while operator active" (agent-time-bound, not clock-bound). No
      CLAUDE.md edit needed; no cron-poker; no automation surface to ship. Closing as DESIGN-DECISION-ONLY: keep
      best-effort wording in AGENT_ONBOARDING.md; agents continue self-pacing per ScheduleWakeup/loop semantics.
      **MIGRATED FROM:** G-8.
- [x] ✅ [DESIGN] P2. **Group F — STALE_OPEN_ALERT meta-alert (AL-21 QG half).** Contract codified at
      `unified-trading-pm@<pending>` in `/codex/15-runbooks/alerting/alert-code-taxonomy.md` § "Alert lifecycle audit
      (STALE_OPEN_ALERT meta-alert)". Defines: (1) `alert_type: transient|paired` per-code classification; (2) paired
      alerts must clear within `clear_sla_seconds` (default 3600s) or alerting-service raises `STALE_OPEN_ALERT` with
      the original alert_id/code/elapsed time in details; (3) implementation surface
      (`alerting-service/alerting_service/lifecycle/stale_audit.py` + per-code metadata registry); (4) per-code SLA
      defaults table; (5) future QG step proposal for registry completeness. Implementation deferred to alerting-service
      slot pickup (contract is the QG half per the original spec). **MIGRATED FROM:** AL-21.

## Done definition

- Each Group ships its QG ratchet OR explicitly migrates to a more granular successor plan.
- Issue-doc rows in source `codex_audit_*_2026_05_12.md` flipped POST_CUTOVER → POST_CUTOVER ✅ FILED @ this plan.

## Out of scope

- Pre-cutover items.
- Codex-doc currency sweeps (those live in `codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`).
- Runbook gaps (those live in `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md`).
