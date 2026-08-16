---
doc_type: plan
title: Venue readiness AO dispatch batch 1 — SIT invariants 2+4, LST SSOT migration, close-all, skills canonical audit
summary: >-
  Dispatch batch carrying the six bounded, determinable-outcome todos surfaced across the venue-readiness umbrella and
  the two reachability issue docs, which sit in local-only or draft parents and so were never ingested. Each has a
  named symbol or file, a stated done-when, and an outcome a worker can reach alone — the design calls those docs also
  carry are deliberately NOT here. Every todo touches a different file set, so they run concurrently by default.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    unified-api-contracts,
    execution-service,
    strategy-service,
    system-integration-tests,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [venue-readiness, ao-dispatch, sit-invariants, lst-ssot, close-all, canonical]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
  ]
created: 2026-08-16
source: >-
  Operator direction 2026-08-16 — "dispatch them", after an AO-eligibility pass over the open P0/P1 lists separated
  bounded work from design calls. Only the bounded half is here.
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: high
sequential: false
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
---

# Venue readiness AO dispatch batch 1

Every todo below already exists as analysis in a parent doc that is `assigned_vm: NA` or `status: draft`, so none of
them were ever ingested. This plan is the execution surface only — **read the cited parent for the full finding
before starting**; do not re-derive it here.

**Why these six and not the rest**: an AO todo must have an outcome the worker can reach alone. The parents also
carry design calls (the mode-axis spec, the dual-resolver typed-config choice, the vault-share config decision) —
those stay local by construction and are deliberately absent.

- [ ] [BACKEND] P1. **Wire SIT invariant 2 as its own ratchet baseline.** Invariant 2 is "MTDS venue ⟹ strategy
      reader on batch/live/paper". It was UNBLOCKED 2026-08-15 by `strategy-service@926be71046`, which built the
      per-mode capability axis it needed, but was never wired. Follow invariants 1 and 3 as the working precedent —
      `unified-api-contracts@056d5eea2d` + `system-integration-tests@da65ae1324`. **Use AST static parsing** per the
      real `run_cross_repo_invariants.sh`, NOT the codex doc's aspirational import template. Done-when: invariant 2
      runs as a ratchet baseline that fails on a new regression, and its baseline file records the current measured
      set. Parent: `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`.
- [ ] [BACKEND] P1. **Build SIT invariant 4 — UAC ↔ execution-service address drift.** Assert every contract address
      execution-service resolves matches the UAC SSOT, so the two cannot diverge silently. This matters because six
      addresses are now read by BOTH services from one registry, meaning a single error propagates rather than being
      caught by disagreement. Same AST-static-parsing method as above. Done-when: the invariant fails on a
      deliberately-introduced address mismatch — demonstrate it, do not assert it.
- [ ] [BACKEND] P1. **Migrate execution-service protocol modules onto the UAC LST address SSOT.** Removes the second
      source of truth for LST token addresses. The SSOT is
      `unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py`; `lido.py` already sources
      `rETH`/`weETH`/`ezETH`/`pufETH` by direct dict lookup from it — extend that pattern to the remaining modules.
      **Do NOT add eETH or rsETH**: they are deliberately absent (operator ruling 2026-08-16) because no venue
      declares them, and an entry no venue declares is unreachable. Done-when: no execution-service module carries its
      own LST address literal, and the invariant above covers the result.
- [ ] [BACKEND] P0. **Migrate close-all onto `/manual/instruction`.** Ruling 2026-08-16: close-all re-points onto the
      existing manual instruction surface, NOT a new `/api/orders`. `/manual/instruction` is the DIRECT path;
      `/manual/pending` is the approval-gated one — target the direct path. The value is that it is the same path
      humans already use manually, so it is continuously exercised rather than being an emergency-only route that
      rots. Real work is request-shape mapping. **Include an HTTP contract test across the service boundary** — the
      kind that would have caught the original 404. Done-when: close-all issues through `/manual/instruction` and the
      contract test fails if the route or request shape changes.
- [ ] [DATA] P0. **Audit the four `/data-pipeline-check-*` skills against current canonical expectations.** Measured
      2026-08-16: ZERO of the four call `canonical_path_violations()` — the UAC MACHINE ORACLE that must never be
      re-implemented — and two (`data-pipeline-check-is` line 25, `data-pipeline-check-mtds` line 255) carry their own
      banners saying their pass/fail is "actively misleading" while the raw→canonical migration is in flight, dated
      2026-07-18 and 2026-07-20. Three canonical-changing dispatches landed 2026-08-16 alone, so the drift is active.
      Per skill: route the canonical leg through the oracle or record why it cannot; check the filename instrument_id
      and the `instrument_type`/`data_type`/`venue`/`chain` VALUES separately (the oracle is path-structure-only and
      value-blind) or declare them unchecked; re-date or remove each banner. Done-when: all four are audited with a
      per-skill verdict. Parent: `/plans/active/venue_smoke_test_bar_2026_08_16.md`.
- [ ] [DOC] P2. **Fix the venue-coverage issue doc's stale frontmatter.** Its `summary` still says "~30 DeFi
      protocols" while the body carries the corrected figure. Done-when: frontmatter and body agree, sourced from the
      body's measured number, not re-counted.

## Definition of done

- [ ] [REVIEW] P1. **Every todo above flipped with evidence** (`<repo>@<sha>`), and each cited commit re-verified to
      resolve — not trusted from the plan's own copy of the line.

## Progress Log

**2026-08-16 — authored and dispatched.** Operator direction: "dispatch them", following an AO-eligibility pass that
split the open P0/P1 lists into bounded work and design calls. Six bounded items here; the design calls stay in their
local parents. `sequential: false` because each todo touches a disjoint file set — SIT invariants in
`system-integration-tests`, LST addresses and close-all in different `execution-service` modules, the skills audit in
`unified-trading-pm/cursor-configs/skills/`, the frontmatter fix in one doc — so they run concurrently by default.
Deliberately EXCLUDED as already-dispatched: the 69-constant reference-data inventory, which already sits in
`/plans/active/strategy_service_centralization_fixes_2026_08_16.md` (`assigned_vm: planning`, active) and would have
been a duplicate here.
