---
doc_type: plan
title: Execution-service bitfinex/bitget native unreachable — finalize (reconcile + archival)
summary: >-
  Gated closeout for execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md — machine-held via depends_on +
  gate_on_depends: true until that doc's single todo is done. Shape (b) bolt-on finalize sibling per the 2026-07-30
  na-eligibility-audit reclassification: reconcile the factory.py wiring checkbox, then archive the source doc via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [execution]
repos: [unified-trading-pm, execution-service]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-05"
last_updated: "2026-08-05"
parent_epic: execution_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [execution_service_bitfinex_bitget_native_unreachable_2026_07_28]
gate_on_depends: true
source: >-
  Shape (b) bolt-on finalize sibling per /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 1
  — the 2026-07-30 na-eligibility-audit reclassified this doc NA → planning in place but did not create the paired
  _finalize sibling that both the naming SSOT and task_template.md § 4's finalize-plan-coverage rule require. Batch5's
  closeout (cefi_satellite_ao_dispatch_batch5_2026_08_02_finalize.md todo 3) identified the gap and explicitly deferred
  it to this doc.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# Execution-service bitfinex/bitget native unreachable — finalize

> **Shape (b) bolt-on finalize sibling** per
> `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1 — the 2026-07-30
> na-eligibility-audit reclassified the source doc `NA → planning` in place but did not create the paired `_finalize`
> sibling. This doc closes that gap.

> **Machine-gated on `execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until that doc's single todo is `done`.
> `sequential: true` because todo 2 (archival) depends on todo 1's reconciliation confirming the source doc has 0 open
> items and is archival-ready.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile the source doc's single factory.py wiring checkbox.** The source doc
      (`execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md`) has exactly 1 todo — the factory.py wiring
      change — which was shipped 2026-08-03 (slot 8, backend_engineer) across two repos: execution-service@0f37ec8a
      (wires BITFINEX/BITGET into `DIRECT_REST_VENUES`, `_create_direct_rest_adapter`, `get_supported_venues()`) +
      unified-api-contracts@1ee4dbd5 (adds `BITFINEX_SPOT`/`BITGET_SPOT`/`BITGET_FUTURES` to `CLOB_VENUES` — required
      for factory.py's import-time `_unregistered_venues` consistency check). **Verify each SHA is still an ancestor of
      `origin/live-defi-rollout`** (both confirmed 2026-08-05 at authoring time — re-verify at execution time), then
      confirm the source doc has 0 remaining open todos (1 total, 1 done). **Done when**: both SHAs confirmed reachable
      on origin + source doc's open-todo count explicitly re-stated as 0.

- [ ] [DOC] P2. **Archive the source doc via the standard 6-step ritual** — but the doc carries
      `locked_by:     live-defi-rollout` (`locked_since: 2026-05-21`), which blocks archival under
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. **Step 0 (pre-ritual):** resolve the lock.
      Either (a) apply `[unlock-plan]` if the lock is stale/ceremonial (the doc's only todo shipped 2026-08-03 with no
      issues, and the locked_since date predates the doc's own creation by months — this may be a carryover from a
      template), or (b) if the lock is substantive, file a blocked-question with the operator asking whether to unlock.
      **Then the 6-step ritual**: migrate any remaining open items (expect 0 — confirm todo 1's reconciliation holds) →
      add the archive banner → codex-alignment check (this doc creates no new durable contract — confirm) → grep corpus
      for referrers of `execution_service_bitfinex_bitget_native_unreachable_2026_07_28` and repoint each to the
      archived path → clear `locked_by` (confirm already cleared from step 0) → `git mv` to `plans/archive/2026_08/`.
      **Done when**: the source doc is archived, every corpus referrer resolves to the new path, `run_hygiene_sweep.sh`
      stays green, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual + `[unlock-plan]`
  procedure that todo 2 executes.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1 shape (b) — the reclassified-doc
  finalize-sibling convention this doc itself instantiates.

## Progress Log

- **2026-08-05** (slot 6, review): Todo 1 reconciliation complete. Both SHAs verified as ancestors of
  `origin/live-defi-rollout` at execution time: execution-service@0f37ec8a ✅, unified-api-contracts@1ee4dbd5 ✅. Source
  doc `execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md` has exactly 1 todo, `[x]` done → 0 remaining
  open todos. Source doc carries `locked_by: live-defi-rollout` (since 2026-05-21) — unlock + archival deferred to
  todo 2.
- **2026-08-05** (slot 13, data_engineering): Authored this finalize sibling per batch5's closeout todo 3. Source doc's
  single todo (factory.py wiring) confirmed done at execution-service@0f37ec8a + unified-api-contracts@1ee4dbd5, both
  verified ancestors of `origin/live-defi-rollout` at authoring time. The `locked_by: live-defi-rollout` on the source
  doc prevents immediate archival — todo 2 handles unlock + 6-step ritual.
