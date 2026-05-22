---
name: strategy_master_audit_instructions
type: audit-instructions
epic: strategy_master
assigned_vm: vm-trading-core
tier: L2
last_updated: 2026-05-22
---

# Strategy Master — Audit Instructions

## Epic Scope

strategy-service post-consolidation: 53 archetypes across all asset_groups, `portfolio_allocator`, risk manager,
position tracker, PnL calculator, and batch=live code path identity. Shard-level failure isolation required.

Codex SSOTs: `codex/09-strategy/architecture-v2/archetypes/`, `codex/04-architecture/shard-level-failure-isolation.md`,
`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`

## Triggers

- Monthly (minimum cadence)
- After each new archetype is added or removed from the registry
- After any repo consolidation phase completes (verify no stale import references)
- When `execution_master` audit surfaces strategy→execution contract violations

## Checklist

- [ ] (a) **53 archetypes registered**: all 53 archetypes present in the archetype registry (no orphans). Grep:
      `rg "class.*Archetype\|register_archetype" strategy-service/ --include="*.py"` — count and verify

- [ ] (b) **strategy_archetype_logic_audit findings GREEN**: all findings from the Opus 1M logic audit are in code.
      Check: `plans/audit/results/strategy_archetype_logic_audit_2026_05_20.md` — verify all RED items have commit SHAs

- [ ] (c) **portfolio_allocator determinism**: same input → same allocation output (no time-dependent randomness). Run:
      unit test for `portfolio_allocator` with fixed seed if applicable

- [ ] (d) **QG passes clean**: zero new violations introduced by consolidation phases. Run:
      `bash scripts/quality-gates.sh` in strategy-service — exit 0 required

- [ ] (e) **Zero stale repo references**: consolidation Phase 11 stale ref cleanup fully shipped. Grep:
      `rg "strategy-and-dart-service|strategy_and_dart_service" --include="*.py"` across all service repos — should be 0
      hits (old consolidated repo name) Check: `strategy_consolidation_phase11_stale_ref_cleanup_2026_05_21.md` — all 6
      sub-phases `- [x]`

- [ ] (f) **Batch=live code path identity**: strategy produces identical signals for same tick sequence regardless of
      `--mode batch` vs `--mode live`. Verify: no `if mode == "live"` branching in signal computation logic Grep:
      `rg "mode.*live\|live.*mode" strategy-service/ --include="*.py"` — review any hits for correctness

- [ ] (g) **dYdX venue token regression resolved**: dYdX venue token issue has an operator-acked decision (Option A:
      re-add to UAC, B: remove from catalog, or C: xfail markers). Check:
      `strategy_dydx_venue_token_regression_2026_05_20.md` status — must not be indefinitely BLOCKED-OPERATOR

- [ ] (h) **Shard-level failure isolation**: no `raise` inside per-venue or per-shard loops in strategy computation.
      Grep: `rg "^\s+raise " strategy-service/ --include="*.py"` — review each hit; raises inside loops are violations

## Success Criteria

- All 8 checklist items GREEN
- strategy-service QG exits 0
- Zero stale old-repo import references workspace-wide

## Output Format

Result file at `plans/audit/results/strategy_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
