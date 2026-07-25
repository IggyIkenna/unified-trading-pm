---
doc_type: plan
title: Infra capture wiring + devops leftovers — finalize (re-check BLOCKED-* gates + archive)
summary: >-
  Gated closeout for infra_capture_and_devops_leftovers_2026_07_06.md (AO Plan 6 of the instruments-completion set) —
  machine-held via depends_on + gate_on_depends: true until that plan's todos are done. Backfills the
  finalize-plan-coverage gap for a plan predating the 2026-07-24 rule (task_template.md §4): not a batch extraction (its
  own todos are the primary record, nothing to reconcile back into a source doc), so this finalize's job is narrower —
  re-check each still-open BLOCKED-* item's gate, then run the standard archival ritual once genuinely done.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [infra, capture, close-out, finalize, blocked-recheck, archival]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/operator_iam_permission_parity_2026_06_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [infra_capture_and_devops_leftovers_2026_07_06]
gate_on_depends: true
source: >-
  Backfilled 2026-07-25 per task_template.md §4's finalize-plan-coverage rule (check_finalize_plan_coverage.py flagged
  this pre-existing AO plan as a ratchet regression — it predates the 2026-07-24 rule and never got a companion finalize
  plan).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Infra capture wiring + devops leftovers — finalize

> **Machine-gated on `infra_capture_and_devops_leftovers_2026_07_06.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until every todo in that plan is `done`. `sequential: true` because todo 2
> (BLOCKED-* re-check) must run before todo 3 (archival) can determine whether the plan is truly closeable.
>
> **Not a batch-extraction plan** — unlike the sports/tradfi/prediction satellite-batch finalize docs, this source plan
> was authored directly (not extracted from other docs' todos), so there is no "reconcile checkboxes back into a
> different source doc" step. Its 4 remaining open items are gated (`BLOCKED-PREREQUISITES` ×1, `BLOCKED-CREDENTIALS`
> ×3, `BLOCKED-OPERATOR-DECISION` ×1) — this finalize plan's job is to re-check each gate, not redo the work.

## Todos

- [ ] [REVIEW] P2. **Re-verify the ASTER live connector prereqs (`BLOCKED-PREREQUISITES` item).** The source plan's own
      2026-07-07 annotation already found both named prereqs landed on LDR shortly after the block was recorded
      (`unified-api-contracts@3652f99f` added `book_snapshot_5`/`liquidations` to
      `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]`; `instruments-service@4a8cff75` added the enumerator's
      per-(venue,data_type) `start_date` gate) but explicitly flagged that the connector launch itself was never
      re-verified or flipped on that basis alone. Confirm both prereqs are still present at current LDR tip, then either
      launch the connector (register `aster_book_liq_ws.py` into `live/connector_registry.py` + a live VM per the
      KALSHI-PERP book5 template, verify `live_aster` rows land via a T+10-15min per-VM shard spot-check, no
      fire-and-forget) or, if a newer blocker has since appeared, update the checkbox annotation with the current
      blocker. **Done when**: either `live_aster` book5/liquidations rows are confirmed landing daily (checkbox flips
      `[x]`) or the doc records the current, re-verified blocking reason.
- [ ] [REVIEW] P2. **Re-check the 4 credential/operator-gated items' gates** — `collect-oracle-prices` pyth key,
      gas-fees MANTLE paid RPC key, live ODDS quota decision, and the rate-limit-probe disposable-IP sanction. For each:
      check whether the named credential/decision has landed since 2026-07-14 (grep Secret Manager provisioning commits,
      `[ack-pending]` resolution, or an operator note elsewhere). If a gate cleared, either do the now-unblocked work
      directly (each is small — a launcher/adapter scaffold already exists per the source plan) or spin it into a new
      tracked todo if it needs its own dispatch. If still gated, leave the BLOCKED-* annotation as-is — do not descope.
      **Done when**: each of the 4 items has an explicit current-state note (still gated, with evidence checked / newly
      unblocked, with the resulting work done or re-tracked).
- [ ] [DOC] P3. **Archive `infra_capture_and_devops_leftovers_2026_07_06.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule) — ONLY if todos 1-2 above result in the plan having zero open items (all 5 either
      flip `[x]` or remain genuinely BLOCKED-* with no further action possible right now, in which case downgrade
      `status: active` → `blocked` instead of archiving, and skip this todo). If archivable: add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `infra_capture_and_devops_leftovers_2026_07_06` and fix each path to point at the archived location → clear
      `locked_by` (already empty, confirm) → move to `plans/archive/2026_07/` alongside this finalize doc in the same
      commit. **Done when**: either the plan is archived with every corpus referrer fixed, or (if still genuinely
      blocked) its `status` is downgraded to `blocked` with a note explaining which item(s) remain gated.
