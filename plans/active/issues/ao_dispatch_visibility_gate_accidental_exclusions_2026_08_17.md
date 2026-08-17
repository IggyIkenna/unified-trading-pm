---
doc_type: issue
title: AO dispatch-visibility gate — 6 new undeclared (accidental) exclusions block PM LDR QG
summary: >-
  `check_ao_dispatch_visibility_gate.py` (quality-gates.sh post-gate check) is failing on
  unified-trading-pm: accidental_exclusions=6 > baseline 0 + buffer 5. Blocks any quickmerge
  Pass-1 QG on this repo regardless of the shipped diff's own content. Found while shipping an
  unrelated infra todo (`ci_satellite_ao_dispatch_batch15_2026_08_16.md` — re-baseline
  `qg_resource_baseline.json`); confirmed unrelated to that change (this gate scans
  `plans/active/*.md` todo text only, the shipped diff touched only a `scripts/dev/*.json` data
  file).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, plan-hygiene, ao-dispatch-visibility, ratchet, qg-red]
related: []
created: "2026-08-17"
parent_epic: infrastructure_master
source: >-
  Found while shipping ci_satellite_ao_dispatch_batch15_2026_08_16.md's qg-baseline
  re-measurement todo; discovered via a quality-gates.sh pre-commit failure on
  unified-trading-pm, confirmed unrelated to that shipped diff.
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
---

# AO dispatch-visibility gate — 6 new undeclared (accidental) exclusions

## What I found

`bash scripts/quality-gates.sh --no-fix` on `unified-trading-pm` (live-defi-rollout) fails the
`check_ao_dispatch_visibility_gate` post-gate check:

```
check_ao_dispatch_visibility_gate: FAILED
  - accidental (undeclared) exclusions grew: 6 > baseline 0 + buffer 5
```

`python3 scripts/quality_gates/check_ao_dispatch_visibility_gate.py --json` names the 6 todos
whose disk-vs-backlog dispatch visibility dropped without a declared
`BLOCKED-*`/`DEFERRED-BY-DESIGN`/stretch marker at the start of their line:

1. `plans/active/infra_satellite_ao_dispatch_batch18_2026_08_16.md` — "[SCRIPT] P0. Measure p95
   and max shard duration per launcher family from `vm-logs/` run.log PROGRESS…"
2. `plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md` — "[DOC] P2.
   Re-check the Deferred/excluded population for cleared gates. batch6 excluded 11 docs across
   6…"
3. `plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` — "[DOC]
   P2. Residual gaps (2)(3)(4) — still open, each a judgment call / operator ruling, not
   AO-eligible.…"
4. `plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` — "[DATA] P1. UNBLOCKED
   2026-08-15 — the MVP backfill readiness gate above is now `[x]` done (2026-08-15,…"
5. `plans/active/issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md` —
   "[BACKEND] P1. New: exercise `build_transfer_wiring` end-to-end against a real exchange
   sandbox/testnet…"
6. `plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`
   — "[DATA] P2. Write + backup-first apply a marker-format migration covering: BYBIT's raw-date
   dated-future symbol…"

Each spans a different tranche (infra / prediction / strategy / tradfi / cefi) with domain
context I don't own from this (infra-craft) task — declaring the correct marker per todo needs a
per-doc read by whoever's already tracking that doc's state, not a blind mechanical stamp.

## Why it matters

Blocks `quality-gates.sh` (and therefore quickmerge Pass-1) fleet-wide on `unified-trading-pm`
for EVERY shipper, regardless of what they're actually changing — confirmed via a stash test:
the failure is corpus-content-only (`plans/active/*.md` todo text), reproducible with zero
relation to the shipped diff.

## Recommended decision

For each of the 6: either (a) the todo is genuinely still open/dispatchable — investigate why its
`backlog_open` count diverged from `disk_open` and fix the underlying dispatch-visibility bug, or
(b) it's a legitimate exception (blocked/deferred/judgment-call, matching the pattern the other 13
already-declared exclusions use) — add the matching marker
(`BLOCKED-<token>`/`DEFERRED-BY-DESIGN`/stretch) at the START of its own line. Once all 6 are
resolved one way or the other, `check_ao_dispatch_visibility_gate.py` should return to
`accidental_exclusions <= 5`; if a residual legitimate exception count needs to be retained,
`--update-baseline` with the reviewed count and reasoning in the commit message per the gate's own
remedy text.

## Todos

- [ ] [REVIEW] P1. Classify `infra_satellite_ao_dispatch_batch18_2026_08_16.md`'s flagged todo
      (repo: unified-trading-pm) — genuinely open (fix dispatch-visibility) or needs a declared
      marker.
- [ ] [REVIEW] P1. Classify `prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md`'s
      flagged todo (repo: unified-trading-pm).
- [ ] [REVIEW] P1. Classify
      `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`'s flagged todo
      (repo: unified-trading-pm).
- [ ] [REVIEW] P1. Classify `tradfi_phase_d_terminal_gate_2026_07_24.md`'s flagged todo (repo:
      unified-trading-pm) — note its own text says "UNBLOCKED 2026-08-15", likely just needs the
      stale exclusion-affecting marker removed/updated.
- [ ] [REVIEW] P1. Classify
      `issues/cefi_ccxt_withdraw_stub_returns_false_confirmed_2026_08_16.md`'s flagged todo (repo:
      unified-trading-pm).
- [ ] [REVIEW] P1. Classify
      `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`'s
      flagged todo (repo: unified-trading-pm).

## Progress Log

- **2026-08-17 (slot 6, infra-craft worker)**: found while shipping
  `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s qg-baseline re-measurement todo. Confirmed
  unrelated to that diff (gate scans plan-corpus todo text only). Filed this issue + declared a
  `qg_red` repo-blocker for `unified-trading-pm` per RULES.md §4b.
