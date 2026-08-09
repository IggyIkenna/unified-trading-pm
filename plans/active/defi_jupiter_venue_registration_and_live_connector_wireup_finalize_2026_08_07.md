---
doc_type: plan
title: Finalize — Jupiter DeFi venue registration + MTDS live-connector wire-in
summary: >-
  Gated finalize companion for defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md — re-verifies the
  build's evidence (incl. its own todo 6's audit-doc + codex-doc edits), then archives both docs per
  plan-completion-and-archival-discipline once every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, jupiter, finalize, archival, ao-build]
related:
  [
    defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-07-24 — every AO-dispatched plan needs a gated finalize companion (see
  /plans/active/task_template.md §4).
context_scope:
  [
    defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
---

# Finalize — Jupiter DeFi venue registration + MTDS live-connector wire-in

Machine-held (`gate_on_depends: true`) until every todo in
`defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` is done. Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. **Corrected 2026-08-09 by plan_reconciler — the build plan actually has 8 todos, not 6** (todos 7
      "Capture the two missing WS frame cassettes" and 8 "Add the standing xfail-needs-todo rule" were added after this
      finalize doc was authored and never folded into its re-verify scope). Re-verify each of the build plan's 8 todos'
      cited commits/evidence actually exist (`git log`/`git show` against a fresh `git pull --ff-only` on each of
      `unified-api-contracts`, `instruments-service`, `market-tick-data-service`, `execution-service`,
      `unified-trading-pm` — don't trust the build plan's own evidence lines uncritically). Confirm todo 6's edits
      landed correctly: both `defi_adapter_dead_code_audit_2026_07_24.md` §6 checkboxes flipped with a real pointer to
      the build plan (not duplicated content), and `/codex/04-architecture/solana-defi-coverage.md`'s JUPITER MTDS-role
      line updated to reflect the shipped connector. Additionally confirm todo 7's WS cassettes are real captures (not
      fabricated) and todo 8's xfail-standing-rule decision is recorded. Done-when: all 8 todos' evidence independently
      re-verified, any mis-citation found is corrected in the build plan directly.
- [ ] [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` and this finalize doc itself: archive
      both to `plans/archive/2026_08/`, and fix every corpus referrer path (grep the repo for the old paths and update
      each hit). Also check whether `defi_adapter_dead_code_audit_2026_07_24.md` now has zero remaining open `- [ ]`
      todos in §6 (the governance-params-poller re-verify item stays open — it was never in this plan's scope) — if it
      does not, leave it active; do not archive it prematurely. Done-when: `regenerate_active_plan_inventory.py` shows
      zero orphan referrers to the archived paths.

## Progress Log

- **2026-08-07 (interactive session)**: finalize plan authored alongside the build plan per `task_template.md`'s
  finalize-plan-coverage rule.
