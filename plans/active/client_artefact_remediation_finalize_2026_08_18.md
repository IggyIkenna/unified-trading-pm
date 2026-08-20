---
doc_type: plan
title: Client artefact remediation — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_2026_08_18.md. Reconciles completed-todo evidence back
  into the audit report and the two owning artefact plans, re-checks whether any deferred system-gap gate has since
  cleared, and archives the parent plan once fully done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, elysium, artifact-remediation, finalize]
related:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — every assigned_vm:planning
  plan with more than one todo needs a gated finalize plan.
context_scope:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
---

# Client artefact remediation — finalize

Gated on [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
being fully done. Do not start before then.

- [x] ✅ [REVIEW] P1. **Reconcile completed-todo evidence back into source docs.** For every checked todo in the
      parent plan, re-verify the cited HTML section/commit actually reflects the claimed edit (open the live file,
      don't trust the checkbox text alone) and update the corresponding finding's status in
      [`nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)'s
      summary table from open to resolved. Also check whether either owning artefact plan
      ([`nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md),
      [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md))
      needs its own Progress Log updated to reflect that this remediation pass ran. — **Done 2026-08-19** (evidence:
      all 13 audit summary-table findings RESOLVED after live re-verification of both walkthroughs + both wired
      checkers green; owning plans' Progress Logs updated — see Progress Log below).
- [x] ✅ [REVIEW] P1. **Re-check every item in the parent plan's "Real system gaps — already tracked, not duplicated
      here" section.** If transfer-handler wiring, capital-budget enforcement, dynamic-universe pinning, or any of
      `system_readiness_master.md` W5/W10/W12/W13/W16/W17/W18 has landed since this plan was authored, the
      corresponding artefact content can move from target-state framing to a present-deep claim — spin that into a
      new tracked todo (a new small plan or an addition here) rather than leaving the artefact under-claiming a now-
      real capability. — **Done 2026-08-19: re-checked every item; NONE has landed since authoring.** § B
      capital-budget P0, § C transfer-handler P0, § H.8 dynamic-universe-pinning P0 (all in
      `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`) and `system_readiness_master.md`
      W5/W10/W12/W13/W16/W17/W18 remain `- [ ]` open with zero items checked off — no target-state→present-deep
      re-frame warranted, no new todo spun up. See Progress Log below.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual (status →
      `archived`, `git mv` into the dated archive folder, exact-successor banner if applicable, corpus-wide
      referrer-path fixup, verify no broken links, confirm line caps still hold).

## Progress Log

**2026-08-18 — authored** alongside the parent plan, per task_template.md §4's mandatory finalize-companion rule.

**context-scout 2026-08-19**: reviewed; context_scope unchanged (2 entries) — parent plan + audit report already
cover this gate's reconcile/re-check/archive todos; source-path hunt skipped (finalize gate).

**2026-08-19 — todo 1 (reconcile evidence) done.** Re-verified every checked parent-plan todo against the live repo,
not the checkbox text alone: all 14 cited SHAs resolve (`171dc40739, ec08cccad1, 8b7e78e21f, 2b0c327e44, 6a5598e736,
8fb70b119b, 832033d0942, 4067ff23da, 512d5b07a8, 98ee4fdc70, a7621fb5e5, a472bdb5fd, 5644680849, 19724f5e69`); both
hygiene checkers (`scripts/plan-hygiene/check_artefact_disclosure.py`, `check_artefact_enum_drift.py`) exist, are
wired into `run_hygiene_sweep.sh`, and run green (0 hard disclosure violations / 0 enum-drift violations — real enum
counts 9 strategy families, 11 instruction envelopes); `_ssot-rules/` 11/12/13 + all cited audit-result docs present.
Live-verified both walkthroughs carry the claimed edits (eleven action types; §02's 9 real families; §11
target-state framing; TRADE-only / 501 disclosure; §14 8-leg; `.ev-*` legend + `.own` owner marks in both files).
Updated
[`nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)'s
summary table — all 13 findings marked RESOLVED, `status` flipped `partial`→`pass` (audit-result status enum), Progress Log entry added;
appended remediation-pass entries to both owning artefact plans'
([`nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)
+ [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md))
Progress Logs. Todos 2 (re-check "Real system gaps") and 3 (archive parent) remain for subsequent dispatches.

**2026-08-19 — todo 2 (re-check "Real system gaps") done.** Re-checked every item in the parent plan's
[`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md) § "Real system
gaps" against the live plans — none has landed since the 2026-08-18 audit, so no artefact content moves from
target-state to present-deep and no new todo is warranted:
- **Transfer-handler production wiring** — `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`
  § C P0 "Replace the stub `TransferHandler` implementations" still `- [ ]` open.
- **Capital-budget enforcement** — same plan § B P0 "Verify capital-budget enforcement, or build it" still `- [ ]` open.
- **Dynamic-universe as-of-date pinning** — same plan § H.8 P0 "Stamp the resolved dynamic-universe as-of date into the
  run manifest" still `- [ ]` open.
- **W5/W10/W12/W13/W16/W17/W18** — `system_readiness_master.md`: collateral/cross-margin/transfer-eligibility/manual-
  trade (W5), risk native+share-class/Greeks (W10), reconciliation (W12), PnL attribution (W13),
  latency/tracing/preflight/SLA (W16), fee/gas (W17), canonical output paths (W18) — every P0 still `- [ ]` open, zero
  checked off. (W16's fail-closed ruling and W5's populate-not-design refinements landed on 2026-08-18 as *new* tracked
  items, not capability landings.) Todo 3 (archive parent) is now unblocked.
