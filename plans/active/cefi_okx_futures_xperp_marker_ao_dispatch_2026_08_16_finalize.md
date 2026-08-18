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
- [x] ✅ [INFRA] P2.2. **DONE 2026-08-17 (slot-17, infra).** Redeploy half only (split further below — see
      P2.3 for the still-open live-verify half). Confirmed `3acdd478e5` is an ancestor of the floating
      `mtds-code` tarball's pinned commit (`e9709d59054efb16b57eac1bf512ac1a6a3c58b0`, tarball refreshed
      2026-08-17T02:42:25Z, `git_status_clean: true`) via `git merge-base --is-ancestor`. The stale VM
      (`mtds-live-cefi-consolidated-20260814-041422`) was deleted and `mtds-live-cefi-consolidated-20260817-025031`
      relaunched via the standard launcher — done by an earlier pass of this same session before a context
      reset (no Progress Log entry existed for it yet; this entry documents the verification, not the action
      itself, which this worker independently confirmed via evidence rather than assuming). Confirmed via SSH
      (`ps aux`) that all 24 MVP shard processes are up, including all 3 OKX-FUTURES shards
      (`cefi:OKX-FUTURES:trades`, `:book_snapshot_5`, `:derivative_ticker`). Old VM's heartbeat blob
      (`vm-heartbeat/mtds-live-cefi-consolidated-20260814-041422.txt`) was still fresh (updated 02:48:36Z)
      right up to the cutover — confirms this was a deliberate stale-code replacement per the VM-delete
      guardrail (infra.md STEP 0.65), not a zombie/stale-detection case.
- [ ] [DATA] P2.3. **⏸ PARKED 2026-08-17 (slot-17, infra) — genuinely time-gated, not worker-satisfiable
      right now.** The live-verify half of the original P2.2 (real non-zero rows for a fixed xperp symbol in
      warm-tier `live-events/warm/cefi/{trades,book_snapshot_5,derivative_ticker}/*.parquet` timestamped after
      the redeploy) cannot be completed yet: investigation found the new VM's live connectors are correctly
      up but sitting in an honest-absence retry loop (`IS universe empty ... retrying in 300s`) for **every**
      CeFi venue, not just OKX-FUTURES — instruments-service's daily `is-daily-enum-cefi` job (13:30 UTC) has
      not yet published `day=2026-08-17`'s instrument partition as of this check (03:15 UTC), and this MTDS
      code path has no fallback to the prior day's partition on a cold start. Full root-cause + recommended
      fix filed as `/plans/active/issues/mtds_live_cefi_redeploy_cold_start_is_universe_gap_2026_08_17.md`
      (2 follow-up todos there, not this plan's scope to fix inline). This is self-resolving, not a genuine
      blocker: expect real OKX-FUTURES xperp rows to start flowing automatically ~13:35-13:40 UTC today once
      the daily job lands, no further redeploy needed. A future worker (or this same worker on a later pass)
      should re-check after that time: read `live-events/warm/cefi/{trades,book_snapshot_5,derivative_ticker}/*.parquet`
      objects timestamped after ~13:35 UTC 2026-08-17 for real `OKX-FUTURES:FUTURE:<SYMBOL>-USD@LIN-2031....`
      rows (one of the 28 fixed equity/ETF xperp symbols, e.g. AAPL), then flip this todo and archive this
      plan (all conditions of the original combined P2.2 todo will finally be met). Repo: market-tick-data-service
      (verification only, no code diff expected).

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
- **2026-08-17 (slot-17, infra, AO-dispatched, resumed session)**: Picked up P2.2. Found the redeploy already
  done by an earlier pass of this same session (no Progress Log entry existed for it — likely lost to a
  context reset before it could be written) — independently verified rather than trusting the absence of a
  record: `mtds-live-cefi-consolidated-20260817-025031` is the current RUNNING live-CeFi VM (old
  `...-20260814-041422` is gone), tarball manifest pinned to `e9709d59054efb16b57eac1bf512ac1a6a3c58b0` with
  `3acdd478e5` confirmed an ancestor (`git merge-base --is-ancestor`), all 24 MVP shard processes up via SSH
  `ps aux` (incl. all 3 OKX-FUTURES shards). Split P2.2 further into P2.2 (redeploy — flipped done above) and
  new P2.3 (live-verify — parked) after live-verify investigation found the new VM's connectors correctly up
  but capturing ZERO rows for EVERY CeFi venue (not OKX-FUTURES-specific): SSH log tail showed
  `IS universe empty ... retrying in 300s` for OKX-FUTURES/BINANCE-FUTURES/HYPERLIQUID alike, root-caused to
  instruments-service's `is-daily-enum-cefi` Cloud Scheduler job (13:30 UTC daily) not yet having published
  `day=2026-08-17`'s instrument partition (checked GCS directly: `day=2026-08-15`/`day=2026-08-16` exist,
  `day=2026-08-17` does not, as of 03:15 UTC) combined with this MTDS code path having no fallback to the
  prior day's partition on a cold start (confirmed the OLD VM, still running at 02:40-02:47 UTC today before
  I/an earlier pass deleted it, was NOT hitting this gap — it resolves its universe once at process startup
  and holds it, so only a fresh redeploy lands in this window). This is self-resolving (expect real data
  ~13:35-13:40 UTC once the daily job lands) and affects the WHOLE live-CeFi fleet, not just this task's
  scope, so filed it as its own issue doc rather than absorbing a code fix into this finalize plan:
  `/plans/active/issues/mtds_live_cefi_redeploy_cold_start_is_universe_gap_2026_08_17.md` (2 follow-up todos:
  a prior-day fallback in MTDS, and a launcher-comment warning in deployment-service). Did not flip P2.3 or
  archive this plan — genuinely not done yet, time-gated on IS's daily refresh, not a judgment call this
  session can resolve synchronously.
