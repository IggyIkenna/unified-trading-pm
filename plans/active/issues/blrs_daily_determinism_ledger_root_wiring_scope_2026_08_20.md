---
doc_type: issue
title:
  blrs-daily-determinism ledger-root wiring — `batch-rerun` is NOT a CLI operation (plan + terraform comment both assert
  it is); true scope is 2 repos + a prod deploy cycle, not a 1-hour single-checkbox item
summary: >-
  While working `citadel_satellite_ao_dispatch_batch2_2026_08_19.md`'s P2.7.5 todo ("wire
  `paper_ledger_root`/`batch_ledger_root` + a batch-rerun trigger stage into the `blrs-daily-determinism` cron"), the
  todo's own stated premise was measured FALSE: it directs the implementer to "trigger strategy-service's existing
  `batch-rerun` CLI op (`cli/handlers/batch_rerun.py`)", and
  `deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf`'s Stage-B comment repeats the same claim. There
  is no `batch-rerun` operation in strategy-service's `_OPERATIONS` registry
  (`strategy_service/cli/service_entry.py`) — the registry holds exactly `backtest`, `trade`, `seed-lifecycle`,
  `risk-monitor`, `position-recon`, `pnl-attribution`, `paper-run`, `paper-stream`. `batch_rerun.py` exposes only the
  LIBRARY function `rerun_from_manifest(...)`; nothing invokes it from a CLI entrypoint, so there is no command a cron
  stage could call today. Wiring the cron therefore requires ADDING a CLI operation (strategy-service) before any
  terraform stage can exist (deployment-service), and the todo's own Done-when ("the cron's own log shows a real
  (non-no-op) reconciliation result") additionally requires a Cloud Build image deploy + a subsequent cron execution to
  verify — none of which fits the item's `est_hours: 1.0` single-checkbox framing. Live baseline measured this session
  and unchanged: Stage B succeeds nightly but as the honest no-op.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, deployment-service]
scope: [engineer]
tags: [determinism, paper-batch-recon, cron, terraform, cli, scope-correction, citadel]
related:
  [
    /plans/active/citadel_satellite_ao_dispatch_batch2_2026_08_19.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/epics/batch_live_symmetry_master.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: "2026-08-20"
author: AO worker slot-8 (dispatch citadel_satellite_ao_dispatch_batch2-2444fa0c8907)
priority: P2
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "citadel_satellite_ao_dispatch_batch2_2026_08_19.md item P2.7.5, AO dispatch slot-8, 2026-08-20",
  ]
drift_direction: advance-code
context_scope:
  [
    deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf,
    strategy-service/strategy_service/cli/service_entry.py,
    strategy-service/strategy_service/cli/handlers/batch_rerun.py,
    batch-live-reconciliation-service/batch_live_reconciliation_service/cli/handlers/daily_determinism_handler.py,
  ]
---

## What I found

**1. The `batch-rerun` CLI operation does not exist.** The P2.7.5 todo says to add "a stage that triggers
strategy-service's existing `batch-rerun` CLI op (`cli/handlers/batch_rerun.py`, proven ε=0 — P2.7.2/P9.B)". The Stage-B
comment block in `deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf` makes the identical claim ("no
stage here triggers strategy-service's `batch-rerun` CLI op").

Measured: `strategy_service/cli/service_entry.py`'s `_OPERATIONS` dict registers exactly `backtest`, `trade`,
`seed-lifecycle`, `risk-monitor`, `position-recon`, `pnl-attribution`, `paper-run`, `paper-stream`. There is no
`batch-rerun` key and no `BatchRerunHandler` class. `strategy_service/cli/handlers/batch_rerun.py` defines module-level
functions only — `rerun_from_manifest(...)`, `reconcile_paper_batch(...)`, `_batch_ledger_root(...)` — and its only
callers are its own unit tests. So `--operation batch-rerun` is not a runnable command; a terraform stage invoking it
today would exit non-zero at argparse.

This matters beyond pedantry: the todo is written as "wire the cron to call the thing that exists", which reads as a
terraform-only change. It is actually a strategy-service feature addition (new handler + registration + CLI args + a
GCS-side resolver for "yesterday's paper run" + unit tests) *followed by* the terraform work.

**2. `rerun_from_manifest` needs inputs no cron stage can supply at `tofu apply` time.** Its required kwargs are
`paper_ledger_root`, `batch_run_id`, `rerun_code_shas`, `account_id`, `asset_group`, `quote_currency`. The paper ledger
root embeds the paper `run_id`, and `_gen_run_id()` in `paper_run_handler.py` returns
`paper-{YYYYmmddHHMMSS}-{uuid4[:8]}` — a uuid4 suffix, so the run_id is **not** derivable from the date. It must be
resolved by listing GCS under `client_runs_prefix(client_id)` at job runtime. (Note `stream_run_id()` in the same module
IS deterministic per-day, but that is the separate `firm-paper-stream` client, not the determinism client.) There is no
public UTL helper that resolves "the newest run for a client" — `run_writer.py` has only the module-private
`_read_all_jsonl_under` / `_list_blobs` plumbing — so a resolver has to be written.

**3. The live baseline is exactly as the todo describes — confirmed, not assumed.** Both facts measured this session
against prod (`asia-northeast1`):

- Stage B `uts-prod-blrs-daily-determinism` execution `…-n9kxd`, completed `2026-08-20T02:30:50Z`, status True. Its log
  line, verbatim: `2026-08-20 02:30:45,761 INFO [daily-determinism] paper_ledger_root/batch_ledger_root unset — no run to
  reconcile (honest no-op)`. So the stage is green *because* it correctly no-ops, exactly as
  `daily_determinism_handler.py` is written to.
- Stage A `uts-prod-paper-engine-run` execution `…-wclvk`, completed `2026-08-20T02:05:07Z`, status True — and it writes
  real ledgers: run_id `paper-20260820020050-f370fbe9`, `run_manifest.json` + 3 InstructionLedger fills + 3 pricing
  marks + 18 transfer rows + 63 passive rows under
  `gs://central-element-323112-client-reports/ledger/client_id=firm-paper-determinism/run_id=paper-20260820020050-f370fbe9/`.

So the input data for a real reconciliation genuinely exists nightly; only the rerun + the root injection are missing.
The wiring is feasible — the scope is just larger than the item states.

**4. The Done-when is not satisfiable inside a single code-shipping session.** "Done when: the cron's own log shows a
real (non-no-op) reconciliation result" requires the new strategy-service image to reach Cloud Build + deploy, and then
a cron execution (or a manual `gcloud run jobs execute`) to produce that log line. That is a deploy-and-observe cycle
after the code lands, not something the code commit itself demonstrates.

## Why it matters

The determinism spine (paper(W) == batch-rerun(W), ε=0) is the proof that batch and live agree; the daily cron is its
standing regression guard. Right now that guard has been green-but-inert since the scheduler was enabled — it proves
nothing, and its greenness actively looks like coverage. Any agent picking up P2.7.5 as written will estimate a
terraform edit, discover mid-task that the CLI op is missing, and either under-deliver or silently expand scope across
two repos. Correcting the premise up front is what stops that repeating.

## Recommended decision

Split P2.7.5 into the four todos below and treat the original as superseded by them. The design question that
P2.7.5 leaves genuinely open — whether the roots reach Stage B via (a) a wrapper that resolves them and POSTs the job's
`:run` with `overrides.containerOverrides[].env`, or (b) resolution inside the BLRS handler when its config roots are
empty — is called out in todo 3 and should be settled by the operator/main before that todo is worked, because (b)
changes BLRS runtime behaviour for every caller while (a) keeps the honest-no-op contract untouched.

- [x] ✅ [BACKEND] P2. **Add a `batch-rerun` CLI operation to strategy-service.** New `BatchRerunHandler` in
      `strategy_service/cli/service_entry.py` registered as `"batch-rerun"` in `_OPERATIONS`, wrapping the existing
      `rerun_from_manifest(...)`. Reuse `paper_run_handler._git_sha()` for `rerun_code_shas` so the sha assertion matches
      what the paper run pinned (same image ⇒ same sha). Needs a `--paper-run-id` arg (explicit) plus a resolver for the
      default case. Unit tests must cover the resolver and the handler wiring using the injectable `replay_fn` /
      `storage_client` seams `batch_rerun.py` already exposes. Repo: strategy-service. Done when: `--operation
      batch-rerun` runs end-to-end against an injected fake storage client in a unit test and returns a `BatchRerunResult`
      with a populated `recon` verdict. — strategy-service@21296786. Added `resolve_newest_paper_run_id()` +
      `add_batch_rerun_args()` to `cli/handlers/batch_rerun.py` (the `--paper-run-id` default-case resolver, listing
      `client_runs_prefix(client_id)` for the lexicographically-newest `run_id=` child — no public UTL helper existed yet,
      see item 2 below) and `BatchRerunHandler` to `cli/service_entry.py`, registered as `"batch-rerun"`.
      `tests/unit/cli/handlers/test_batch_rerun_cli.py` covers the resolver (3 tests) and an end-to-end handler-wiring test
      that injects a fake storage client + deterministic replay through the real `rerun_from_manifest()` and asserts a
      populated `recon` verdict (`deterministic=True`, `fills_reproduced=4`). Full `quality-gates.sh` green, no new
      baseline violations.
- [x] [BACKEND] P2. ✅ **Add a public "resolve the newest run for a client" helper.** Paper run ids carry a uuid4 suffix, so
      the batch stage cannot derive yesterday's root — it must list `client_runs_prefix(client_id)` and pick the newest
      `run_id=` child (ids are timestamp-prefixed, so lexicographic order is chronological within the
      `firm-paper-determinism` client). Put it beside `client_ledger_root` / `client_runs_prefix` in
      `unified_trading_library/ledger/run_writer.py` so writer and reader keep sharing one convention; listing goes
      through the UTL cloud_interface storage client, never a subprocess `gcloud`/`gsutil`
      (`/codex/05-infrastructure/gcs-object-operations.md`). Repo: unified-trading-library. Done when: a unit test with a
      fake client returns the newest of several seeded run ids.
      — unified-trading-library@97195cb77d; Evidence: full quality-gates.sh passed (875s), quickmerge post-push ancestry verified.
- [ ] [OPERATOR] P2. **Settle how both ledger roots reach the Stage-B job, then implement it.** Option (a): a wrapper
      that resolves the roots and triggers `uts-prod-blrs-daily-determinism` via the Cloud Run `:run` API with
      `overrides.containerOverrides[].env` carrying `PAPER_LEDGER_ROOT` / `BATCH_LEDGER_ROOT` (`ReconConfig` extends
      `UnifiedCloudConfig` with `case_sensitive=False` and no env_prefix, so the field names map directly) — leaves
      `daily_determinism_handler.py` untouched. Option (b): resolve inside `DailyDeterminismHandler.run()` when the
      configured roots are empty, keeping the honest no-op only when resolution genuinely finds nothing — fewer moving
      parts but changes BLRS behaviour for all callers. Operator/main picks; do not guess. Repos: deployment-service
      (+ batch-live-reconciliation-service if (b)). Done when: the chosen mechanism is recorded here and implemented.
      **Gate id `BLK-op-blrs_daily_determinism_ledger_root_wiring_scope-29413eccdd3a`** (operator-gated, no worker
      spawned). Raised separately via the blocked-queue as `BLK-8d718e56` on 2026-08-20; review declined to resolve it
      there — deliberately, so two channels cannot answer the same question differently — and routed it back to THIS
      todo as the single decision point. Review did record that the worker's recommendation of **(a)** "sounds sound",
      on the reasoning that confining the new behaviour to the scheduler keeps a resolver bug from turning the honest
      no-op into a fabricated ε=0 verdict. That is an endorsement, NOT the decision: the operator still picks here.
- [ ] [INFRA] P2. **Add the Stage A2 batch-rerun job + cron to the terraform module and verify the cron logs a real
      verdict.** New `module "batch_rerun_job"` + `google_cloud_scheduler_job` in
      `deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf`, scheduled between Stage A (02:00) and
      Stage B (02:30) — note the existing stages are staggered independent crons, not a DAG, so the offset is the only
      ordering guarantee and the job must tolerate a late/absent Stage A run. Repo: deployment-service. Done when: a
      `uts-prod-blrs-daily-determinism` execution log shows a real reconciliation verdict (`deterministic=…` from
      `run_daily_determinism_stage`) instead of `skipped: no_run_configured`, with the execution id cited here.
- [ ] [INFRA] P3. **Re-check the untargeted terraform drift before any broad apply of `terraform/gcp/`.** The batch2
      plan's own 2026-08-20 Progress Log records that a full (untargeted) plan still reports `4 to add, 63 to change`
      unrelated drift, so the Stage A2 addition above must be applied targeted (`-target=module.batch_rerun_job` and the
      matching scheduler resource) until that drift is separately reconciled. Repo: deployment-service. Done when: the
      new resources are applied without dragging in the unrelated 63 changes.

## Progress Log

- **2026-08-20** (AO worker slot-8): filed. Measured the `_OPERATIONS` registry (no `batch-rerun` key), the
  `_gen_run_id()` uuid4 suffix, and both live Cloud Run execution logs cited above. Corrected the misleading Stage-B
  comment in `paper_week_determinism_scheduler.tf` in the same session (it asserted the CLI op exists). No code for the
  wiring itself was written — the four todos above carry it.
- **2026-08-20** (AO worker slot-19, backend_engineer): shipped item 1 — strategy-service@21296786. Items 2-4 remain
  open: item 2 (unified-trading-library public "resolve newest run" helper) is still needed for a shared writer/reader
  convention even though item 1's own resolver already unblocks the CLI op standalone; item 3 is operator-gated
  (`BLK-op-blrs_daily_determinism_ledger_root_wiring_scope-29413eccdd3a`); item 4 (terraform Stage A2 job + cron)
  depends on item 3's decision.
- **context-scout 2026-08-20**: reviewed context_scope (already populated at authoring time with 4 real source
  paths across the 3 involved repos) — no changes needed, left at 4 entries.

- **2026-08-20** (AO worker slot-12, backend_engineer): shipped item 2 — added public `resolve_newest_run_id()` beside the client run-prefix helpers, listing only the client-scoped UTL storage prefix and selecting the lexicographically newest timestamp-prefixed run id. Unit coverage verifies multiple runs, client isolation, and nested batch paths; full quality gates passed and quickmerge landed `unified-trading-library@e5ac1c0a4b`.
- **2026-08-20** (AO worker slot-8, infra): reverified item 2 at `unified-trading-library@97195cb77d`; the bounded full quality-gate run passed tests, type checking, import/codex compliance, and post-push ancestry verification.
