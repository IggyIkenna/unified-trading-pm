---
doc_type: plan
title: Alerting lifecycle SLO + DART runbook + operator-UX gaps (post-cutover)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service, deployment-ui, execution-service, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md,
    plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md,
    plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md,
  ]
created: 2026-05-12
archived: 2026-05-23
last_updated: 2026-05-23
last_reviewed: 2026-05-17
execution:
  {
    owner: alerting-platform + DART operability owner,
    cadence: post-cutover backlog drain (open until 2026-08-31),
    verifier: groups A-G success-criteria all flipped per plan body,
    last_executed: Groups A/C/E/F shipped 2026-05-14; D/G remain DEFERRED to UI slot,
  }
migrated_from: codex_vs_citadel_infrastructure_audit_2026_05_10 (POST_CUTOVER Phase 5)
estimate_class: design
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 2.4
parent_epic: observability_master
priority: P2
---

# Alerting lifecycle SLO + DART runbook + operator-UX gaps (post-cutover)

> **MIGRATED FROM:** `codex_vs_citadel_infrastructure_audit_2026_05_10` — Phase 5 POST_CUTOVER consolidation 2026-05-12.
> Source area issue docs: `plans/archive/issues/codex_audit_alerting_2026_05_12.md` (AL-22),
> `codex_audit_risk_2026_05_12.md` (R-15, R-16), `codex_audit_strategy_2026_05_12.md` (ST-11),
> `codex_audit_testing_2026_05_12.md` (TS-19, TS-20).

## Why this plan exists

A cluster of POST_CUTOVER findings share one shape: **operator-facing surfaces (runbooks, dashboards, decision matrices)
lack the codex-side discoverability required for someone walking up cold during an incident**. Each individual gap is
small; together they form an operator-UX debt that compounds when on-call rotates. Group them so one operator-UX sweep
covers the lot after May-23.

## Scope — migrated findings (7 operator-UX items)

| Finding         | Source area | Description                                                                                                                                                                                                                                                                                                                                                     |
| --------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AL-22           | alerting    | `/codex/03-observability/slos.md:56` declares alerting-service "Alert false-positive rate < 1% — tracked via feedback" but no `AlertFeedback` model / metric exists. Wire feedback path OR downgrade SLO to "manual review during quarterly rehearsal" with named owner                                                                                         |
| R-15            | risk        | `kill-switch-event-bus.md:73-89` says `KILL_ALL_LIVE` arming must have provenance `OPERATOR_MANUAL` or `SCHEDULED_DRILL` — but doc doesn't explain why `SCHEDULED_DRILL` is treated as operator-equivalent. Add 1-paragraph rationale                                                                                                                           |
| R-16            | risk        | Wallet-tier kill-switch arm via DART operator UI shipped slot 8 but no runbook doc exists for: when to arm KILL_PER_WALLET vs KILL_PER_ARCHETYPE, rollback procedure, audit-log line confirming the arm landed. CLAUDE.md "Runbook Execution-Owner SSOT" requires every operator-runnable runbook to declare `execution.{owner,cadence,verifier,last_executed}` |
| ST-11           | strategy    | `block-list.md` and `category-instrument-coverage.md` have UI runtime mirrors (`unified-trading-system-ui/lib/architecture-v2/block-list.ts`) kept in sync **manually**. Either generate from codex/UAC matrix, or add CI parity check (mirror UAC's cassette-parity pattern)                                                                                   |
| TS-19           | testing     | No codex doc states the "two-pass QG model for agents" (Pass 1 = full `quality-gates.sh` incl. tests; Pass 2 = `quickmerge --agent` skips tests). It's in CLAUDE.md + `.claude/rules/python-backend.md` but not in `/codex/06-coding-standards/quality-gates.md`. Add 3-line subsection                                                                         |
| TS-20           | testing     | `integration-testing-layers.md:219-234` decision matrix conflates DeFi-unit (sim/responses) with DeFi-integration (Tenderly fork). ADD distinct row "DeFi on-chain integration → Tenderly VNet fork fixture"; also add IBKR row                                                                                                                                 |
| AL-21 (UX half) | alerting    | `STALE_OPEN_ALERT` meta-alert needs operator dashboard surface (the QG/automation half lives in `governance_qg_automation_gaps_post_cutover_2026_05_12.md`)                                                                                                                                                                                                     |

## Todos

- [x] [RUNBOOK] P2. **Group A — DART wallet-tier kill-switch runbook (R-16).** Write
      `/codex/15-runbooks/wallet-tier-kill-switch-operator.md` with `execution.{owner,cadence,verifier,last_executed}`
      frontmatter, decision tree (KILL_PER_WALLET vs KILL_PER_ARCHETYPE vs KILL_PER_VENUE), rollback procedure,
      audit-log signature. **MIGRATED FROM:** R-16. **DONE 2026-05-14**: `unified-trading-pm@slot6-item7` — runbook
      created with full frontmatter + decision tree + rollback + audit-log signature.
- [x] [DOC] P3. **Group B — kill-switch provenance rationale (R-15).** Add 1-paragraph rationale to
      `kill-switch-event-bus.md:73-89` explaining why `SCHEDULED_DRILL` is operator-equivalent (drill-runner
      operator-attended; chaos-cron unattended). **MIGRATED FROM:** R-15. **DONE 2026-05-14**: paragraph added after
      provenance gating rules section.
- [x] [DESIGN] P2. **Group C — Alert false-positive SLO measurement (AL-22).** Either: (a) wire minimal feedback path
      (operator marks an alert "noise" in UI → metric increments via `AlertFeedback` model in alerting-service); or (b)
      downgrade `/codex/03-observability/slos.md:56` to "manual review during quarterly rehearsal" with named owner.
      Compose with rehearsal procedure (AL-16). **MIGRATED FROM:** AL-22. **DONE 2026-05-14**: Chose option (b) — no
      `AlertFeedback` model exists; downgraded to "manual review during quarterly DR rehearsal" with named on-call
      owner. Upgrade note added.
- [x] [DESIGN] P2. **Group D — Block-list / category-instrument-coverage TS mirror parity (ST-11).** Either generate the
      `.ts` from codex doc / UAC matrix, or add CI parity check mirroring UAC cassette-parity. Fix likely belongs in UI
      repo; this plan owns the design call + cross-repo plan-spawning if implementation is complex. **MIGRATED FROM:**
      ST-11. **DESIGN CALL 2026-05-14**: CI parity check (not generation). Add
      `__tests__/scripts/block-list-parity.test.ts` to `unified-trading-system-ui` mirroring the orphan-audit pattern.
      Test reads `lib/architecture-v2/block-list.ts` BL-IDs and compares against
      `/codex/09-strategy/architecture-v2/block-list.md` BL-\* tokens. **DONE 2026-05-18**: 4 parity tests shipped
      (codex-exists, ts→md, md→ts, count-agreement); all pass (10 BL-IDs both ways). unified-trading-system-ui@e1b7b232.
- [x] [DOC] P3. **Group E — Two-pass QG model § in testing codex (TS-19).** Add 3-line subsection to
      `/codex/06-coding-standards/quality-gates.md` clarifying that Pass 2 (`quickmerge --agent`) does NOT re-run tests.
      **MIGRATED FROM:** TS-19. **DONE 2026-05-14**: subsection added after `--agent` flag description.
- [x] [DOC] P3. **Group F — DeFi-integration + IBKR rows in testing decision matrix (TS-20).** Add distinct rows to
      `integration-testing-layers.md:219-234` matrix: "DeFi on-chain integration → Tenderly VNet fork fixture
      (`execution-service/tests/defi_execution/integration/conftest.py`)" + "IBKR → `MagicMock(spec=IB)`". **MIGRATED
      FROM:** TS-20. **DONE 2026-05-14**: two rows added to the decision matrix.
- [x] [DESIGN] P2. **Group G — STALE_OPEN_ALERT operator dashboard (AL-21 UX half).** Wire the operator-facing surface
      for the STALE_OPEN_ALERT meta-alert (the QG/automation contract lives in the governance plan). UI tile in
      deployment-ui OR alerting-service dashboard. **MIGRATED FROM:** AL-21 (UX half). **DESIGN CALL 2026-05-14**: UI
      tile in `deployment-ui` AlertStatusPanel (NOT alerting-service — keeps alerting stateless). Tile polls
      `GET /api/alerts?status=stale&limit=20`. Implementation is **DEFERRED-POST-CUTOVER** to deployment-ui slot (slot 7
      owns deployment-ui). Routed to slot 7 via ping 2026-05-18. Successor: slot_7.md ping
      `[2026-05-18 14:05 UTC] [slot-4 → slot-7] SUCCESSOR ROUTING — Group G STALE_OPEN_ALERT dashboard`.
      **[DEFERRED-POST-CUTOVER]** 2026-05-19 slot 2: successor routing confirmed (slot_7.md ping 2026-05-18); plan body
      documents named successor per status taxonomy rule. Item closeable per audit.

## Done definition

- Each Group ships its operator-UX deliverable OR explicitly migrates to a granular successor.
- Issue-doc rows in source `codex_audit_*_2026_05_12.md` flipped POST_CUTOVER → POST_CUTOVER ✅ FILED @ this plan.

## Out of scope

- Pre-cutover items.
- Codex-doc currency sweeps.
- QG / CI ratchet design (lives in `governance_qg_automation_gaps_post_cutover_2026_05_12.md`).
