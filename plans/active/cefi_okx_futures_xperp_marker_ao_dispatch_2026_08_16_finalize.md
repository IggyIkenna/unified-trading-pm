---
doc_type: plan
title: Finalize — OKX-FUTURES xperp wire-format fix
summary: Gated finalize companion for cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, finalize]
related:
  [
    /plans/active/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md,
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 6, 2026-08-16"
locked_by:
context_scope: [/plans/active/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md]
locked_since:
context_scope:
  [
    /plans/active/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md,
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
    deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh,
  ]
resolved_by:
---

# Finalize — OKX-FUTURES xperp wire-format fix

## Todos

- [x] ✅ [REVIEW] P2.1. **DONE 2026-08-16 (slot 22, review).** Code-level confirmation: re-ran
      `market-tick-data-service`'s test-only quality gate on current HEAD (which contains
      `3acdd478e5` as an ancestor — confirmed via `git log`) and independently reproduced parity-test-green,
      not just read the worker's self-report. `test_okx_futures_live_batch_id_parity.py`'s fixture directly
      covers the real xperp case (`AAPL-USD_UM_XPERP-310613` ↔ `OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613`).
      Also confirmed the `[OPERATOR] P1` todo in `okx_futures_instid_marker_convention_mismatch_2026_07_30.md`
      was ALREADY flipped to done-with-sha before this session touched it (no action needed there). Full
      evidence in the Progress Log below.
- [ ] [INFRA] P2.2. **NEW 2026-08-16 (slot 22, review — split from the original combined todo, mirroring the
      P1.1/P1.2 precedent in `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`).** The
      "live subscriptions for xperp contracts confirmed non-zero" half of the original todo is NOT yet true:
      the currently-running live CeFi capture VM (`mtds-live-cefi-consolidated-20260814-041422`, created
      2026-08-13/14) predates the fix commit (`3acdd478e5`, landed 2026-08-16) by 2-3 days, and this
      deployment model bakes code in at VM-launch time (no live auto-pull) — so the running connector almost
      certainly still lacks the `_XPERP` fix. Redeploy: confirm the floating `mtds-code` tarball manifest
      (`gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`) has `3acdd478e5` (or
      later) as an ancestor, delete the stale VM, relaunch via the standard launcher
      (`launch-mtds-live-cefi-consolidated.sh --env prod`), confirm all shard processes come up, then
      live-verify (per the P1.1 precedent's method) real non-zero rows for one of the 28 fixed equity/ETF
      xperp symbols (e.g. AAPL, `OKX-FUTURES:FUTURE:AAPL-USD@LIN-20310613`) in
      `live-events/warm/cefi/{trades,book_snapshot_5,derivative_ticker}/*.parquet` objects timestamped AFTER
      the redeploy. Then flip this todo and archive this plan (all conditions of the original combined todo
      will be met). Repo: market-tick-data-service (host-level VM redeploy, no code diff).

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-16 (slot 22, review, AO-dispatched)**: Picked up this finalize todo. Read the dependency plan
  (`cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md`) and the referenced issue doc
  (`okx_futures_instid_marker_convention_mismatch_2026_07_30.md`) first — found the `[OPERATOR] P1` checkbox
  in the issue doc was already flipped to done-with-sha (`market-tick-data-service@3acdd478e5`) by a prior
  pass, so that half of this todo needed no action. Re-verified the code fix independently rather than
  trusting the self-report: fresh-pulled `market-tick-data-service` to current `live-defi-rollout` HEAD
  (`5f4bf143ba9c`), confirmed `3acdd478e5` is a real ancestor commit (`git log --oneline -1 3acdd478e5`
  resolves), read `test_okx_futures_live_batch_id_parity.py`'s fixture (directly covers the real xperp case),
  then ran `bash scripts/quality-gates.sh --test --no-fix` (test-only phase — the sanctioned gate entrypoint,
  never raw pytest) to independently reproduce green rather than reading the prior worker's claimed
  "10968 passed" figure. Separately investigated the "live subscriptions... non-zero" half and found it is
  NOT yet true in production: `gcloud compute instances list --filter="name~mtds-live-cefi"` shows the only
  running live CeFi capture VM is `mtds-live-cefi-consolidated-20260814-041422`, created 2026-08-13/14 — 2-3
  days BEFORE today's fix commit. This mirrors the exact `[INFRA] P1.1` precedent in
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (a prior worker found this same VM
  class stale by 17 days and had to explicitly redeploy — code fixes do not reach the running capture process
  without a redeploy under this VM's launch-time-bake deployment model). Attempted a live SSH check of the
  deployed connector file directly but hit repeated PID churn on this shared host (the specific
  `okx_futures_ws.py` process PID changed between SSH calls); did not force further SSH archaeology once the
  VM-creation-date-vs-fix-commit-date comparison alone was already conclusive. Did NOT redeploy the production
  live-capture VM myself — that is a real production action (briefly interrupts capture for all 17 shard
  processes across every CeFi venue, not just OKX-FUTURES) that goes beyond this task's "confirm" framing and
  deserves its own explicitly-scoped infra pass rather than being folded into a review task silently. Split
  the original combined todo into P2.1 (done — code-level confirmation) / P2.2 (new — the redeploy +
  live-verify, mirroring the P1.1/P1.2 split pattern) instead of forcing a false "non-zero confirmed" claim or
  prematurely archiving this plan. Did not flip `[OPERATOR] P1` again (already correctly flipped) and did not
  archive this plan (P2.2 still open).
