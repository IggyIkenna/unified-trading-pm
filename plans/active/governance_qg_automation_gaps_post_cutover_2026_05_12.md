---
title: Governance HARD RULE automation + QG ratchet gaps (post-cutover)
type: plan
status: active
created: 2026-05-12
deadline: 2026-08-31
horizon: 3-month post-cutover backlog
companion_to: codex_vs_citadel_infrastructure_audit_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
migrated_from: codex_vs_citadel_infrastructure_audit_2026_05_10 (POST_CUTOVER Phase 5)
related_plans:
  - plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md
  - plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md
  - plans/active/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md
estimate_class: design
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 3.0
---

# Governance HARD RULE automation + QG ratchet gaps (post-cutover)

> **MIGRATED FROM:** `codex_vs_citadel_infrastructure_audit_2026_05_10` — Phase 5 POST_CUTOVER consolidation
> 2026-05-12. Source area issue docs in `plans/active/issues/codex_audit_governance_2026_05_12.md` +
> `codex_audit_data_2026_05_12.md` + `codex_audit_strategy_2026_05_12.md` + `codex_audit_ui_2026_05_12.md` +
> `codex_audit_position_balance_2026_05_12.md` + `codex_audit_alerting_2026_05_12.md`.

## Why this plan exists

A cluster of POST_CUTOVER findings share one shape: a CLAUDE.md HARD RULE or codex architectural rule exists, but its
enforcement is **reviewer discipline only** — no automated grep / QG ratchet / CI gate flags violators. Each
individual gap is small; together they form a class of "rule-without-teeth" technical debt that drifts the system
over time. Group them into one plan so a single QG-ratchet design sweep covers the lot post-May-23.

## Scope — migrated findings (10 QG-automation items)

| Finding | Source area | Rule (today) | What's missing (QG check / ratchet to add) |
|---|---|---|---|
| G-2 | governance | "Capture Discoveries As Plan Todos Immediately" end-of-cycle audit clause | No grep-check enforces every deferral becomes `- [ ]` todo or `**DEFERRED**` annotation |
| G-5 | governance | Plan-filename convention: `plans/active/` uses `<slug>.md` | Date-suffix variant (`<slug>_2026_MM_DD.md`) — codify which is canonical or normalize |
| G-8 | governance | Daily Work-Split Model B polling cadence ~1min | No cron / scheduler enforces; depends on main-agent foregrounding |
| G-12 | governance | Codex doc freshness | `codex/11-project-management/` 8 docs mix 2026-04 + 2026-05 mtimes; no `last_verified` enforcement |
| G-13 | governance | "Plan Archival" HARD RULE — operational-completeness audit + deferred migration | No automated check; sample archive plans lack `## Deferred work — migrated to:` banner |
| D-18 | data | "Cluster validation MANDATORY" QG STEP 5.64 | Codex doc `availability-manifest-and-data-status.md:160-164` lacks cross-link to the QG script path |
| ST-19 | strategy | `benchmark-fills.md:12` warns "no standalone backtest engines" | No QG step flags new modules under `strategy_service/engine/backtest/` computing P&L without `V2EngineOrchestrator` |
| UI-13 | ui | UI types regen flow (`export_openapi → generate:types`) is manual | No CI gate that committed `openapi.json` hash matches fresh export — generated types can silently rot |
| UI-18 | ui | "UI must be its own repo (not inside a Python service)" — one-line in `.claude/rules/python-backend.md` | No QG check that fails if a Python service repo contains `package.json` with React/Next/Vite deps |
| PB-19 | position_balance | "PBMS itself must be mode-blind" (no `if mode == 'live'` branches) | No QG ratchet flags `OperationalMode` / `pipeline_mode` branching in `position_balance_monitor_service/` engine/core |
| AL-21 | alerting | "no orphan fired-but-never-cleared alerts" guarantee referenced in `alerting-batch-live.md:81/98` | No codified check / dashboard surfaces "alert X fired N minutes ago, paired clear event never arrived" (`STALE_OPEN_ALERT` meta-alert) |

(11 findings — AL-21 also has an alerting-lifecycle component that overlaps with the alerting/runbook successor plan;
this plan owns the QG/automation half.)

## Todos

- [ ] [DESIGN] P2. **Group A — Plan-discipline grep-checks (G-2 + G-5 + G-13).** Design + ship a PM-side script
      `scripts/quality_gates/check_plan_discipline.py` that walks `plans/active/` + `plans/archive/` and flags:
      (a) plans without a `## Deferred work — migrated to:` banner if `**DEFERRED**` annotations present;
      (b) filename-convention violations; (c) archived plans whose body mentions `**DEFERRED**` /
      `post-cutover` / `out of scope` without a successor reference.
      **MIGRATED FROM:** G-2, G-5, G-13.
- [ ] [DESIGN] P2. **Group B — Codex freshness ratchet (G-12 + D-18).** Add a QG ratchet that flags codex docs in
      cutover-critical surfaces (`codex/02-data/`, `codex/04-architecture/`, `codex/05-infrastructure/`,
      `codex/11-project-management/`) lacking `last_reviewed:` frontmatter or older than 90 days. Cross-reference
      D-18 cluster-validation gate to the QG STEP 5.64 script. **MIGRATED FROM:** G-12, D-18.
- [ ] [DESIGN] P2. **Group C — Architectural ratchets (ST-19 + PB-19 + UI-18).** Three "no standalone X" rules with
      no enforcing QG: standalone backtest engine in strategy-service, mode-branching in PBMS, embedded UI in Python
      service repo. Design one QG-ratchet helper that takes (target path glob, banned-substring set, owner) and
      raises with a clear message. **MIGRATED FROM:** ST-19, PB-19, UI-18.
- [ ] [DESIGN] P2. **Group D — Generated-artefact drift gate (UI-13).** Add CI gate (UI-QG or
      `unified-trading-api` QG) that compares committed `openapi.json` hash to a fresh export, so
      `lib/types/api-generated.ts` cannot silently rot when an endpoint is added. **MIGRATED FROM:** UI-13.
- [ ] [DESIGN] P3. **Group E — Operator-attentiveness automation (G-8).** Either spec a cron-scheduled ping that
      pokes the Model B main agent when ledger backlog exceeds N entries, OR downgrade G-8 from HARD RULE to
      "best-effort while operator active" + remove the bound from CLAUDE.md. **MIGRATED FROM:** G-8.
- [ ] [DESIGN] P2. **Group F — STALE_OPEN_ALERT meta-alert (AL-21 QG half).** Wire a closed-loop check that
      alerting-service surfaces `STALE_OPEN_ALERT` when a fire→clear pair's clear is overdue. Codified contract goes
      into `alert-code-taxonomy.md` (or new `alert-lifecycle-audit.md`). **MIGRATED FROM:** AL-21.

## Done definition

- Each Group ships its QG ratchet OR explicitly migrates to a more granular successor plan.
- Issue-doc rows in source `codex_audit_*_2026_05_12.md` flipped POST_CUTOVER → POST_CUTOVER ✅ FILED @ this plan.

## Out of scope

- Pre-cutover items.
- Codex-doc currency sweeps (those live in `codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`).
- Runbook gaps (those live in `alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md`).
