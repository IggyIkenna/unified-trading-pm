---
doc_type: plan
title: Finalize — Jupiter DeFi venue registration + MTDS live-connector wire-in
summary: >-
  Gated finalize companion for defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md — re-verifies the
  build's evidence (incl. its own todo 6's audit-doc + codex-doc edits), then archives both docs per
  plan-completion-and-archival-discipline once every todo is done.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, jupiter, finalize, archival, ao-build]
related:
  [
    /plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-11"
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
    /plans/archive/2026_08/defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
  ]
---

# Finalize — Jupiter DeFi venue registration + MTDS live-connector wire-in

Machine-held (`gate_on_depends: true`) until every todo in
`defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` is done. Do not start manually before then.

## Todos

- [x] ✅ [REVIEW] P2. Re-verify each of the build plan's 6 todos' cited commits/evidence actually exist
      (`git log`/`git show` against a fresh `git pull --ff-only` on each of `unified-api-contracts`,
      `instruments-service`, `market-tick-data-service`, `execution-service`, `unified-trading-pm` — don't trust the
      build plan's own evidence lines uncritically). Confirm todo 6's edits landed correctly: both
      `defi_adapter_dead_code_audit_2026_07_24.md` §6 checkboxes flipped with a real pointer to the build plan (not
      duplicated content), and `/codex/04-architecture/solana-defi-coverage.md`'s JUPITER MTDS-role line updated to
      reflect the shipped connector. Done-when: all 6 todos' evidence independently re-verified, any mis-citation found
      is corrected in the build plan directly. — ✅ VERIFIED 2026-08-11 (slot-17 review): all 6 SHAs exist and are
      ancestor-or-equal of origin/live-defi-rollout — unified-api-contracts@ad003d03, instruments-service@06c6f2dd,
      market-tick-data-service@9e9c9817, execution-service@507093de, market-tick-data-service@73abd655, and each
      commit's diff independently matches the plan's claims (UAC phase+key flip confirmed at runtime: `JUPITER-SOLANA` ∈
      VENUES_BY_ASSET_GROUP["defi"] with adapter key "jupiter", phase "live"; IS factory `_ADAPTERS`/drift-guard test
      present on origin; MTDS `jupiter_solana_ws.py` + `aave_liquidations_ethereum_ws.py` registered under
      JUPITER-SOLANA/AAVE_V3-ETHEREUM with data_type dex_pool_swaps/liquidations; execution JupiterConnector routing +
      `test_execute_swap_jupiter` present). Todo 6 edits landed: audit-doc §6 both checkboxes `- [x]` with real pointers
      to the build plan (not duplicated content), codex `solana-defi-coverage.md` JUPITER line now "live connector
      SHIPPED" + `spot_trades`→`dex_pool_swaps` corrected (no `spot_trades` refs remain); edit commit
      unified-trading-pm@c328a59f20 on origin. **No mis-citations found — nothing to correct in the build plan.**
- [x] ✅ [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07.md` and this finalize doc itself: archive
      both to `plans/archive/2026_08/`, and fix every corpus referrer path (grep the repo for the old paths and update
      each hit). Also check whether `defi_adapter_dead_code_audit_2026_07_24.md` now has zero remaining open `- [ ]`
      todos in §6 (the governance-params-poller re-verify item stays open — it was never in this plan's scope) — if it
      does not, leave it active; do not archive it prematurely. Done-when: `regenerate_active_plan_inventory.py` shows
      zero orphan referrers to the archived paths. — unified-trading-pm@<sha>

## Progress Log

- **2026-08-07 (interactive session)**: finalize plan authored alongside the build plan per `task_template.md`'s
  finalize-plan-coverage rule.
- **2026-08-11 (slot-12, data_engineering)**: executed 6-step archival ritual on both docs. Step 1 (deferred items):
  none to migrate — build plan todos all done, open questions explicitly marked NOT-todos. Step 2 (archival banner):
  `status: complete` + `last_updated` bumped on both. Step 3 (codex alignment): `solana-defi-coverage.md` already
  updated by build plan todo 6 (verified by slot-17 review). Step 4 (CLAUDE.md): no new contracts to promote. Step 5
  (referrer sweep): updated paths in epic (`infrastructure_master.md`), issue doc
  (`defi_adapter_dead_code_audit_2026_07_24.md`), batch11 plan, archived sports + inventory docs, and INDEX.md. Step 6
  (archive): confirmed `defi_adapter_dead_code_audit_2026_07_24.md` §6 still has 1 open `- [ ]`
  (governance-params-poller re-verify) — stays active per plan instructions.
