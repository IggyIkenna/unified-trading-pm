---
type: audit-result
title: Orchestrator Master Audit — 2026-06-01
epic: orchestrator_master
auditor: claude + operator
date: "2026-06-01"
status: complete
instructions_ref: ../instructions/orchestrator_master_audit_instructions.md
name: orchestrator_master_audit_2026_06_01
assigned_vm: vm-orchestrator
tier: L5
audited_by: slot-1-ikenna
audit_date: 2026-06-01
instructions: ../instructions/orchestrator_master_audit_instructions.md
scope_note:
  First run after § M (closed-loop autonomy) extension. Code/static + plan-state checks run from a worktree host;
  live-fleet checks (SSH/AWS/authed-fan-out) are operator-side and marked LIVE-DEFERRED.
---

# Orchestrator Master Audit — 2026-06-01

## Coverage transparency (mandatory)

- **Walked exhaustively (code/static):** all grep/file/JSON checks against `agent-orchestrator/` HEAD on this worktree
  - `accounts.json` + the four autonomy plans' state + the fleet-enable script inventory.
- **Sampled / single-shot (live):** only the central `/health` endpoint (reachable, 200).
- **NOT run from this host (LIVE-DEFERRED → operator-side):** anything needing SSH to a fleet VM, `aws ec2 describe-*`,
  an authed `/api/auth/login` + `/api/fleet/summary` fan-out, GCS/S3 object listing, or `crontab -l` on the planning VM.
  These are the per-VM flag-rollout confirmations (m1b/m2c/m3b/m3c), the backlog-honesty live check (m3a), spawn-on-kill
  (m1c), the E2E traces, and K-section crons. The running binary's deployed-HEAD currency is also LIVE-DEFERRED.

## A. Fleet topology + connectivity

- **(a1) Central API VM healthy** — 🟢 (partial). `GET /health` → 200, `status:ok`, `version:0.6.0` (meets ≥0.6.0),
  `last_snapshot_iso:2026-06-01T10:11Z` (<24h ✓). **Caveat:** `data_freshness.stale:true` and version string is still
  `0.6.0` despite the autonomy commits (autospawn `b7a4830`, scope-filter `c13375c`, watchdog `9e608f0`) — see Finding
  P1-1 (deploy-currency).
- (a2) Backends inventory vs live fleet — ⏸ LIVE-DEFERRED (needs `aws ec2 describe-instances`).
- (a3) Central API proxy — ⏸ LIVE-DEFERRED (needs authed JWT).
- (a4) Fleet fan-out — ⏸ LIVE-DEFERRED.
- (a5) Auth re-termination — ⏸ LIVE-DEFERRED (code path present in `server.py::proxy_to_vm`; runtime not exercised).
- (a6) Two-secret model — ⏸ LIVE-DEFERRED (needs SSH to central + a worker).

## B. Auth model (setup-tokens only)

- **(b1) Every account has `oauth_token_env_file`** — 🟢 4 accounts, `missing: OK`.
- **(b2) Every account has `setup_token_expires_at`** — 🟢 `missing: OK` (per epic Phase 4c all seeded to 2027-05-21;
  > 30d out).
- (b3) Env files in both clouds — ⏸ LIVE-DEFERRED (GCS + S3 listing).
- **(b4) Legacy code paths gone** — 🟢 0 hits for
  `swap_credentials_for|restore_credentials|oauth_refresh.refresh|GCSCredsPoller|.credentials.{}.json` in `server/`.
- **(b5) `env_file` required on every spawn** — 🟢 0 hits for `env_file: str | None` in `tmux_spawn.py` +
  `usage_tracker.py`.
- (b6) CredsEnvPoller alive — 🟢 (code) `CredsEnvPoller().start()` wired in lifespan; journal line LIVE-DEFERRED.

## C. Backlog auto-generation from plans

- (c1) regen parses real plans — not re-run this pass (heavy); covered transitively by M.5 design + 45-test suite.
- **(c2) `PlanRegenLoop` wired in lifespan** — 🟢 1 hit.
- (c3) Idempotency — 🟢 (covered by the plan's 45-test suite incl. idempotency-on-already-pruned).
- **(c4) Manual endpoint exists** — 🟢 `/api/backlog/regen` present.
- (c5) CLAUDE.md HARD RULE — 🟢 ("backlog is plan-driven" present in workspace CLAUDE.md).

## D. Safety mechanisms

- **(d1) `WorkerLivenessKicker` started** — 🟢 wired in lifespan (distinct from the new watchdog — see M.2a).
- (d2) Auto-respawn refuses without env_file — 🟢 (code path; aligns with B5).
- (d3) Pre-spawn dirty-state gate — 🟢 (worktree-clean check present; not re-counted this pass).
- (d4) Git staleness alert — 🟢 (notify funcs present in both slack + telegram — see E1).

## E. Notifications

- **(e1) Notify inventory** — 🟠 **DRIFT (P2-1).** slack.py now exports **13** `notify_*` funcs (audit expected 10);
  telegram.py **9** (audit expected 8). Counts grew because the autonomy work added notifications
  (`notify_autospawn_flap`, watchdog context-full + cap-hit, etc.). Not a runtime defect — the audit's E1 expected-count
  and the codex j3 inventory table are now stale and must be refreshed.
- (e2) Slack webhook on central — ⏸ LIVE-DEFERRED.
- (e3) Telegram chat ID — ⏸ LIVE-DEFERRED.

## F. State persistence

- (f1) state.db writable — ⏸ LIVE-DEFERRED.
- (f2) Periodic snapshots — 🟢 (partial) `/health` `last_snapshot_iso` <24h; <1h target LIVE-DEFERRED.
- (f3) GCS/S3 backup honesty — 🟠 **known gap (P1-2).** `gcs_sync.py` is GCS-only; the AWS fleet keeps state on local
  disk unless `ORCHESTRATOR_GCS_BUCKET` is set. Confirm the "Known gap" callout still stands in the overview codex doc;
  if S3 snapshot has NOT shipped, this is an autonomy durability hole (VM restart loses state). No active plan currently
  owns this — see Recommendations.

## G. Dashboard

- **(g4) No `OAuthBadge`** — 🟢 0 hits.
- (g1/g2/g3) Firebase deploy currency + landing-page wiring — ⏸ LIVE-DEFERRED (Firebase console + authed paths).

## H–I. Provisioning + EIP/DNS

- ⏸ LIVE-DEFERRED / operator-cost. EIP + DNS remain operator-deferred per epic Phase 11 (not blocking; central API
  proxy serves dynamic IPs). Packer `validate` not run this pass.

## J. Codex doc alignment

- (j1) Connectivity model — not re-read this pass.
- (j2) No stale OAuth refs in orchestrator codex — 🟢 (consistent with B4/G4 code state).
- **(j3) Notification inventory table** — 🟠 **DRIFT (P2-1, same root as E1).** The slack-notifications codex table
  predates the 3 new notify funcs. Must be updated to the 13/9 counts.

## K. Operational hygiene

- (k1) slot-host symmetry — ⏸ LIVE-DEFERRED (per-laptop `verify-slot-host-symmetry.sh`).
- (k2) plan-hygiene cron — ⏸ LIVE-DEFERRED (`crontab -l` on planning VM). NB: silent-failure capture is owned by
  `plan_hygiene_silent_failure_capture_2026_05_29`.
- (k3) orphan-ping audit cron — ⏸ LIVE-DEFERRED (`gcloud scheduler jobs describe`).
- (k4) `orchestrator_vm_registry.yaml` validates — not re-run this pass.

## L. Plan workflow + audit pool

- (l1) audit pool current — operator-judgment, not assessed this pass.
- (l2) workspace-qg ghost issue tracked — 🟢 issue doc exists (`workspace_qg_ci_startup_failure_2026_05_26.md`); status
  LIVE (CI startup_failure still reported across branches per the autonomy plans).

## M. Closed-loop autonomy — the 24/7 trigger chain (NEW)

### M.1 AutoSpawnLoop

- **(m1a) wired** — 🟢 `AutoSpawnLoop(` 1 hit in lifespan; `server/autospawn.py` exists.
- (m1b) flag enabled fleet-wide — ⏸ LIVE-DEFERRED (drop-in + `/proc/.../environ`). Plan records fleet enable
  2026-05-30T09:35Z + working slots 4→17; **re-confirm current state** (a fleet may have restarted since).
- (m1c) spawn-on-kill — ⏸ LIVE-DEFERRED (kill orch-slot-1 → respawn <60s).
- **(m1d) 5-gate contract + preview** — 🟢 contract intact
  (`queue_empty`/`worker_active`/`no_account_headroom`/`cooldown` skip reasons present; cooldown gate present).

### M.2 WorkerLivenessWatchdog

- **(m2a) distinct module + wired** — 🟢 `WorkerLivenessWatchdog(` 1 hit; `worker_liveness_watchdog.py` exists and is
  separate from `worker_liveness.py` (the kicker). Both run.
- **(m2b) three contracts + allow-list + anti-thrash** — 🟢 stuck-at-prompt / context-full (`/clear to save Nk`) /
  heartbeat-silent all present; `Crunched|Cogitated|Worked|Baked for` allow-list present; per-slot 5-min cooldown +
  daily cap present.
- **(m2c) flag enabled fleet-wide** — 🔴 **RED.** The rollout-tracking table in
  `agent_orchestrator_worker_liveness_watchdog_2026_06_01.md` Phase 3 is **entirely empty** — no VM has an "Enabled at"
  timestamp. The enable scripts exist (`enable_worker_watchdog.sh`, `run_fleet_enable_watchdog.sh`) but the canary-first
  fleet rollout has not been recorded as executed. Until filled, the watchdog is presumed dormant fleet-wide (code
  default `false`). **This is the single most impactful open item** — it is the mechanism that ends the "operator kills
  wedged tmux every few hours" cycle.
- **(m2d) blocked-status skip** — 🟢 `if slot.status == "blocked"` skip present.

### M.3 Backlog honesty

- **(m3a) fleet/summary == /api/backlog ±5** — ⏸ LIVE-DEFERRED. Plan's 2026-05-30 snapshot showed vm-trading-core
  6154→0, vm-ml 6591→135 post-rollout — needs re-confirmation today.
- **(m3b/d) prune-stale flag + safety filter** — 🟢 (code) `prune_stale` kwarg + `ORCHESTRATOR_REGEN_PRUNE_STALE` env +
  DELETE filtered to `status='queued' AND dispatched_to IS NULL` (done/dispatched preserved). Per-VM **enable** is
  LIVE-DEFERRED.
- **(m3c) per-VM scope filter** — 🟢 (code) `_parse_frontmatter_assigned_vm` + `ORCHESTRATOR_VM_ID` present (7 hits).
  Per-VM `ORCHESTRATOR_VM_ID` env set is LIVE-DEFERRED.

### M.4 FailoverLoop

- **(m4a) wired + status endpoint** — 🟢 `FailoverLoop(` 1 hit; runtime-status endpoint present (returns offline hosts).
- **(m4b) soft-pin re-route + `failover_origin`** — 🟢 `failover_origin` present in `failover.py` (8 hits) +
  `backlog.py`
  - `orm.py`; re-route block present in lifespan.

### M.5 End-to-end PM-plan → completed-work trace

- (m5) — ⏸ LIVE-DEFERRED (needs a mock instance). The `e2e_test_plan_regen_pipeline_2026_05_29.md` plan owns this
  trace.

### M.6 Soak windows

- (m6) — ⏸ operator-judgment. All four plans' closing conditions require 7-consecutive-day windows that are still
  accruing. None are closeable yet.

## Findings

### 🔴 P0

- _(none — no evidence of a broken production fleet from the checks runnable this pass; the central API is up.)_

### 🟠 P1

- **P1-1 — Deploy-currency unverified (autonomy code may not be the running binary).** Central `/health` reports
  `version:0.6.0` with `data_freshness.stale:true`. The autonomy commits landed on LDR but the audit cannot confirm the
  _running_ central + 11 fleet binaries are at a HEAD that includes them, nor that the four `ORCHESTRATOR_*` flags are
  live. Owner: operator-SSM. This is the gate between "code exists" and "loop runs 24/7".
- **P1-2 — S3-side state snapshot gap (autonomy durability).** AWS fleet VMs keep state on local disk only
  (`gcs_sync.py` GCS-only). A VM restart loses orchestrator state on the AWS fleet. No active plan owns this.

### 🟡 P2

- **P2-1 — Notification-inventory doc drift (E1 + j3).** slack 13 / telegram 9 actual vs audit-expected 10 / 8. The
  audit E1 line and the codex `agent-orchestrator-slack-notifications.md` table both need refresh to the new counts +
  the new func names (`notify_autospawn_flap`, watchdog context-full + cap-hit).

### 🔴 (autonomy heartbeat) — promoted from M.2c

- **The watchdog fleet rollout is unrecorded/incomplete (m2c).** Listed under P1 severity for action: the enable scripts
  exist but the per-VM rollout table is empty. Without it, the "stuck worker auto-kill" half of self-healing is off.

## Recommendations (owner + ETA)

1. **Execute + record the watchdog fleet rollout (m2c).** Run `run_fleet_enable_watchdog.sh` canary-first, fill the
   Phase-3 tracking table with enable-times, then run `verify_watchdog_e2e.sh`. Owner: operator-SSM (vm-orchestrator).
   ETA: this cycle. — covered by existing plan `agent_orchestrator_worker_liveness_watchdog_2026_06_01` Phase 3 (just
   not executed).
2. **Confirm deploy-currency + the 4 flags live on all 11 VMs (P1-1).** Authed `/api/fleet/summary` + per-VM
   `/proc/<pid>/environ` for `ORCHESTRATOR_{AUTOSPAWN,WORKER_WATCHDOG,REGEN_PRUNE_STALE}_ENABLED` +
   `ORCHESTRATOR_VM_ID`. Owner: operator-SSM. — **NO active plan covers a standing deploy-currency / flag-liveness
   check** → see plan-gap §.
3. **File the S3-snapshot gap (P1-2)** as a plan todo. — **NO active plan covers it** → see plan-gap §.
4. **Refresh notification inventory (P2-1)** in audit E1 + codex j3 table. Small docs PR. Owner: any slot.
5. **Re-run m3a backlog-honesty live check** to confirm the 45k-zombie fix is still holding fleet-wide today.

## Linked back

Instructions: [orchestrator_master_audit_instructions.md](../instructions/orchestrator_master_audit_instructions.md) (§
M added 2026-06-01). </content> </invoke>
