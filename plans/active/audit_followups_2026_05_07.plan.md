---
type: plan
asset_group: cross-cutting
priority: P2
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
status: active
date: 2026-05-07
---

# Audit Followups — 2026-05-07 Anomalies Cleanup

Tracks the 6 housekeeping anomalies from
[`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) §6 that didn't have a dedicated plan
home. Each is a small, scoped line-edit to an existing plan or codex doc. No code changes. Estimated total: ~1
engineer-hour for all 6.

P2 (post-May-23 housekeeping; not on the live-trading critical path) but recommended to land before the next workspace
audit so the anomalies don't echo into future sessions.

## Codex SSOTs

This plan tracks line-edit followups against an audit document (no code changes). The driving SSOT for every anomaly
below is the audit itself; cite it before making any plan-or-codex line edit:

- [`plans/active/_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) — workspace dependency
  graph audit (2026-05-07); §6 enumerates the 6 anomalies this plan resolves

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Anomaly fixes

### #1 — Master plan body references folded plans (audit §6 #2)

[`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) body still references
`defi_e2e_pipeline_2026_04_30`, `leveraged_leg_controller_2026_05_01`, `defi_pipeline_extension_2026_05_01` as live
plans. All three were folded into `defi_master_2026_05_07` per Stage 7 batch consolidation (see commit `a2ddbea7`).

- [ ] [SCRIPT] P2. Grep master plan:
      `grep -n "defi_e2e_pipeline_2026_04_30\|leveraged_leg_controller_2026_05_01\|defi_pipeline_extension_2026_05_01" plans/active/master_to_live_defi_2026_05_23.plan.md`
      to enumerate references.
- [ ] [SCRIPT] P2. Replace each ref with `defi_master_2026_05_07.plan.md:Fork-1` (carry_staked_basis live wiring) or
      `:Fork-2` (leveraged_funding_arb), as appropriate. Work-stream-E EXTEND items + Week-1 critical-path alerting line
      need updating.
- [ ] [QG] P2. Re-grep to confirm zero stale refs remain.

### #2 — Service-readiness matrix lists archived plan (audit §6 #3)

`master_to_live_defi_2026_05_23.plan.md` service-readiness matrix at ~lines 453-474 lists
`manual_trade_booking_reconciliation_2026_03_22` as "to archive." Stage 1 already archived it (per master plan line 637
of the audit pass).

- [ ] [SCRIPT] P2. Locate the matrix row referencing `manual_trade_booking_reconciliation_2026_03_22`. Replace with
      `consolidated_operational_validation_2026_04_15` reference.
- [ ] [QG] P2. Verify matrix consistency: every plan reference in the matrix exists in `plans/active/` (not
      `plans/archive/`).

### #3 — Plan-hygiene work-stream-G obsolete item counts (audit §6 #4)

Master plan work-stream-G claims "140/142/31 plans affected" but Stage 7 batch consolidation reduced `plans/active/` to
~23 plans + `plans/ai/` to ~111. Counts must re-derive against current state.

- [ ] [SCRIPT] P2. Re-derive: `ls plans/active/*.plan.md | wc -l` (should be ~23) + `ls plans/ai/*.plan.md | wc -l`
      (~111). Update master plan work-stream-G item counts to actual values.
- [ ] [SCRIPT] P2. Re-derive per-todo scope where work-stream-G items reference specific plan-counts: each todo should
      describe the action (e.g. "add `audit_run` field to all active-plan frontmatter") + the count derives at script
      time, not hardcoded.

### #4 — manifest_migration_master stale module path (audit §6 #5)

[`manifest_migration_master_2026_05_07.plan.md`](manifest_migration_master_2026_05_07.plan.md) ~line 473 cites
`unified_api_contracts.canonical.crosscutting.empty_confirmed_reasons.EMPTY_CONFIRMED_REASONS`. The actual canonical
module is `unified_api_contracts.canonical.crosscutting.honest_coverage` (verified 2026-05-07 via UAC@`8867891` —
`EMPTY_CONFIRMED_REASONS` lives there now).

- [ ] [SCRIPT] P2. Find the line:
      `grep -n "empty_confirmed_reasons" plans/active/manifest_migration_master_2026_05_07.plan.md`. Replace with
      `unified_api_contracts.canonical.crosscutting.honest_coverage.EMPTY_CONFIRMED_REASONS`.
- [ ] [QG] P2. `grep -rn "empty_confirmed_reasons" --include="*.md" --include="*.py"` workspace-wide to confirm no other
      stale refs.

### #5 — infrastructure_master STALE MDPS-1440-NaN reproduction-test (audit §6 #6)

[`infrastructure_master_2026_05_07.plan.md`](infrastructure_master_2026_05_07.plan.md) includes a "MDPS-1440-NaN
reproduction-test" todo that's superseded by the writegate Phase 2.A adapter migrations (MDPS@`5b52d0b`/`b9f9328`/
`80cf141`/`e9520a0`) + reconciler MDPS@`d3be0ef`. The 1440-NaN placeholder anti-pattern has been ripped out of the
adapters; a reproduction-test is no longer meaningful.

- [ ] [SCRIPT] P2. Find the MDPS-1440-NaN todo in infrastructure_master. Mark with
      `[AUDIT 2026-05-07: STALE — superseded by writegate Phase 2.A adapter migrations (MDPS@5b52d0b/b9f9328/80cf141/e9520a0) + reconciler MDPS@d3be0ef. _create_empty_output() ripped out of all adapters.]`
      and flip to `[x]` if appropriate (or leave `[ ]` with STALE marker).
- [ ] [QG] P2. Verify infrastructure_master audit header `Stale` count is correct after this flip.

### #6 — strategy_architecture_v2 Phase 3 entirely STALE (audit §6 #7)

[`strategy_architecture_v2_finalization_2026_04_19.plan.md`](strategy_architecture_v2_finalization_2026_04_19.plan.md)
Phase 3 is the V2-shadow window (14-21d shadow before V1-retire). Operator bypassed it per directive _"if v2 tests pass,
just delete the old stuff"_ (captured in audit). `STRATEGY_DISPATCH_MODE` Literal collapsed to `["v2_prod"]` only —
`v2_shadow` itself retired in commits `8035162` + `a7f6f79`.

- [ ] [SCRIPT] P2. Mark all 4 Phase 3 OPS items in strategy_architecture_v2 as
      `[AUDIT 2026-05-07: STALE — V1-RETIRE bypassed Phase 3 shadow window per operator directive 2026-05-01. STRATEGY_DISPATCH_MODE collapsed to v2_prod only.]`.
- [ ] [SCRIPT] P2. Recommend: drop Phase 3 from the plan entirely in next housekeeping pass (single-line removal per
      todo). Leave the marker for now so audit history is preserved.
- [ ] [QG] P2. Verify strategy_architecture_v2 audit header `Stale` count reflects the 4 flipped items.

## Validation across all 6 anomalies

- [ ] [SCRIPT] P2. After all 6 fixes land, re-run a quick audit grep on the affected 4 plans:
      `for f in master_to_live_defi_2026_05_23 manifest_migration_master_2026_05_07 infrastructure_master_2026_05_07 strategy_architecture_v2_finalization_2026_04_19; do grep -c "AUDIT 2026-05-07" "plans/active/$f.plan.md"; done`
      to confirm markers landed (or commit references in `git log --oneline`).
- [ ] [SCRIPT] P2. Update `_AUDIT_2026_05_07_dependency_graph.md` §"Anomalies from §6 still open" table — flip the 6 to
      ✅ done with commit references.

## Coordination notes

- All 6 fixes are line-level edits to existing plans. **Pre-commit prettier will reformat** — expect format-only diffs
  alongside content edits, same as throughout the 2026-05-07 audit pass.
- **Two teammates rule** — these plans are high-traffic. Commit + push each fix immediately per CLAUDE.md `896c9bc5`
  hard rule. If a concurrent agent's edit lands first, rebase and retry; do NOT `git checkout origin -- .` to "resolve."
- Folding plans for #1 (`defi_master:Fork-1` / `:Fork-2` references) — confirm the fold-target sub-anchors exist in
  `defi_master_2026_05_07.plan.md` before editing master. If they don't, the fix becomes "create matching anchor in
  defi_master + then update master."

## Cross-plan blockers

**Blocked by**: nothing.

**Blocks**: nothing critical-path — these are housekeeping. The only downstream effect is slightly cleaner reading for
the next workspace audit.

## Audit 2026-05-07

- **Audit run**: 2026-05-07T12:45Z (created at session close-out time)
- **Verified**: 0 of 6 (new plan, all items pending kickoff)
- **In-flight**: none
- **Blocked by**: nothing
- **Blocks**: nothing critical
- **Last meaningful commit**: this plan ships as the closure for §6 housekeeping anomalies.
- **Recommendation**: pick up between higher-priority work; ~1h total. Or fold into the next session's quickmerge as
  opportunistic edits.
