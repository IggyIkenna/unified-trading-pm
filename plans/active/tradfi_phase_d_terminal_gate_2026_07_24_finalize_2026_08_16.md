---
doc_type: plan
title: TradFi Phase-D terminal gate — finalize
summary: >-
  Gated closeout for tradfi_phase_d_terminal_gate_2026_07_24.md — machine-held via depends_on + gate_on_depends until
  both of that plan's remaining todos (the post-full-backfill reconciliation run, the CboeCorrection test additions) are
  done. Self-contained plan (not a batch extraction) — its own checkboxes are the source of truth, so this finalize
  plan's job is: verify the reconciliation run's evidence, check whether tradfi_consolidated_closeout_2026_07_18.md's
  own archival-gate reference to this plan needs updating, then run the standard 6-step archival ritual.
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, phase-d, terminal-gate, close-out, finalize]
related:
  [
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_phase_d_terminal_gate_2026_07_24]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored by
  na-eligibility-audit (tradfi tranche, dispatch agt-45ad7b, 2026-08-16) in the same turn as reclassifying its source
  plan NA → planning. Ships status: active (not draft) per the 2026-07-30 no-double-gate ruling — gate_on_depends
  already machine-holds every task until the source plan's own todos are done.
---

# TradFi Phase-D terminal gate — finalize

> **Machine-gated on `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until both of that plan's remaining todos are `done`.

## Todos

- [ ] [REVIEW] P2. Verify the reconciliation-run todo's evidence directly: confirm a dated
      `/data-pipeline-reconciliation --asset-group tradfi` report path is cited covering BOTH the raw-tick and candles
      layers (per that todo's own done-when), and that any finding it surfaced is either resolved or already spun into
      a new tracked `- [ ]` todo somewhere (never left as prose). Do not trust the source plan's own checkbox text alone
      — open the cited report.
- [ ] [REVIEW] P2. Check `tradfi_consolidated_closeout_2026_07_18.md`'s own text (it references
      `tradfi_phase_d_terminal_gate_2026_07_24` as gating its archival per PLAN_FORMAT.md) — once the Phase-D plan
      archives below, confirm whether that reference now needs repointing at the archived path, and whether the
      closeout doc's own archival-readiness changes as a result. Done when: the closeout doc's citation is verified
      current (repointed if needed), not just left as a dangling assumption.
- [ ] [REVIEW] P2. Once `tradfi_phase_d_terminal_gate_2026_07_24.md` itself has zero open todos, run the standard
      6-step archival ritual on it (dated archive folder — `doc_type: plan` → `plans/archive/2026_08/`, archived
      banner, corpus-wide referrer-path fixup, codex-alignment check), then archive this finalize plan too. Done when:
      both docs are under `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan referrers to
      either.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
