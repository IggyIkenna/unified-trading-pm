---
name: orchestrator_master_audit_instructions
type: audit-instructions
epic: orchestrator_master
assigned_vm: vm-orchestrator
tier: L5
last_updated: 2026-05-28
---

# Orchestrator Master — Audit Instructions

## Epic Scope

The `agent-orchestrator` multi-VM stack (FastAPI + Vite/React dashboard), the 11-node AWS fleet (1 central API VM + 10
epic VMs, all `ap-northeast-1` in `vpc-6ee70e08`), the central-API-proxy connectivity model, the long-lived setup-token
auth model, the plan-driven backlog regeneration loop, the safety/auto-respawn machinery, per-VM state persistence,
notification surfaces (Slack + Telegram), the VM provisioning toolchain (Packer + bootstrap), and the operator-laptop
slot-host symmetry crons.

This is the L5 epic — orchestrates every other epic in the registry. Drift here ripples to all 18 other epics, so audit
cadence + completeness matters more than any single subsystem.

## Codex SSOTs

- [`codex/04-architecture/agent-orchestrator-overview.md`](../../../codex/04-architecture/agent-orchestrator-overview.md) — overall architecture
- [`codex/05-infrastructure/agent-orchestrator-worker-topology.md`](../../../codex/05-infrastructure/agent-orchestrator-worker-topology.md) — current fleet IPs + bootstrap
- [`codex/05-infrastructure/agent-orchestrator-deploy.md`](../../../codex/05-infrastructure/agent-orchestrator-deploy.md) — central API VM nginx/systemd
- [`codex/05-infrastructure/agent-orchestrator-dns-cutover.md`](../../../codex/05-infrastructure/agent-orchestrator-dns-cutover.md) — EIP + DNS recipe (Phase 11)
- [`codex/05-infrastructure/agent-orchestrator-slack-notifications.md`](../../../codex/05-infrastructure/agent-orchestrator-slack-notifications.md) — notification inventory
- [`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md) — multi-VM design
- [`codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](../../../codex/12-agent-workflow/orchestrator-safety-mechanisms.md) — stuck-detect + failover + git staleness
- [`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md) — setup-token auth
- [`codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md`](../../../codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md) — operator-laptop slot host

## Triggers

- **Weekly** (minimum cadence — single SLA for the L5 epic since its drift ripples everywhere)
- After **any commit to agent-orchestrator** touching `server/*.py`, `agents/*.md`, `data/config/*.json`, or
  `scripts/bootstrap_vm.sh`
- After **any change to `accounts.json`** (new account, removed account, token rotation)
- After **any change to `backends.json`** (fleet IP refresh, EIP allocation, new VM, decommissioned VM)
- After a **GitHub Support ticket** clears the workspace-qg ghost (re-verify CI green workspace-wide)
- After an **operator laptop is onboarded or re-configured** (slot-host symmetry re-verify)
- After a **codex doc in the SSOTs list is touched** (alignment check between doc + code)
- When the **orchestrator dashboard** is reachable but reports any RED VmAlert for >2h

## Checklist

### A. Fleet topology + connectivity

- [ ] **(a1) Central API VM is healthy.** `curl --max-time 5 https://api.agent-orchestrator.odum-research.com/health` returns
  HTTP 200 with `status: ok`, version ≥0.6.0. `last_snapshot_iso` is < 24h old.

- [ ] **(a2) Backends inventory matches the live fleet.** Every entry in `agent-orchestrator/data/config/backends.json` has
  `url`, `private_url`, `account_id`; no stale dead VMs. Run:
  `aws ec2 describe-instances --filters "Name=tag:Name,Values=agent-orch-*" --region ap-northeast-1 --query
  "Reservations[].Instances[?State.Name=='running'].[Tags[?Key=='Name']|[0].Value, PublicIpAddress, PrivateIpAddress]"`
  and reconcile with `backends.json` — every running instance is in `backends.json` AND every `backends.json` entry has a
  running instance.

- [ ] **(a3) Central API proxy works.** With an authed JWT, `GET <central>/api/vms/<id>/api/state` for at least one fleet
  VM returns the upstream VM's state JSON. Code path:
  [`server.py::proxy_to_vm`](../../../../agent-orchestrator/server/server.py) — verify `_USE_PRIVATE_URLS` flag is set
  (`ORCHESTRATOR_USE_PRIVATE_URLS=true`) on the central VM.

- [ ] **(a4) Fleet fan-out works.** `POST <central>/api/auth/login` then `GET <central>/api/fleet/summary` — response has
  `vms[]` with one entry per backend. Each entry has either `summary` (success) or `error` (unreachable). No more than 1
  VM `unreachable` is acceptable.

- [ ] **(a5) Auth re-termination is active.** Verify in
  [`server.py::proxy_to_vm`](../../../../agent-orchestrator/server/server.py) that the operator JWT is replaced with an
  internal service token (`auth.get_internal_service_token()`) before forwarding. Operator credentials must NEVER reach
  fleet VMs.

### B. Auth model (setup-tokens only, Phase 4b-cleanup HARD RULE)

- [ ] **(b1) Every account has `oauth_token_env_file`.** `data/config/accounts.json` — every entry in `accounts[]` must
  have a non-empty `oauth_token_env_file`. Run:
  `python3 -c "import json; d=json.load(open('agent-orchestrator/data/config/accounts.json')); missing=[a['id'] for a in
  d['accounts'] if not a.get('oauth_token_env_file')]; print('missing:', missing or 'OK')"` — expect `missing: OK`.

- [ ] **(b2) Every account has `setup_token_expires_at`.** Same file — every entry needs a non-empty
  `setup_token_expires_at`. No token within 30 days of expiry without an operator-acked rotation plan in
  `_agent_pings.md`.

- [ ] **(b3) Env files are in both clouds.** For each account, verify:
  `gcloud storage ls gs://central-element-323112-orchestrator-creds/accounts/<id>.env` AND
  `aws s3 ls s3://uts-orchestrator-creds-427895769566/accounts/<id>.env`. Sizes match (sanity: each ~200 bytes).

- [ ] **(b4) Legacy code paths are gone.** Hard rule that the legacy `.credentials.json` swap path was removed in Phase
  4b-cleanup. Grep:
  `rg "swap_credentials_for|restore_credentials|oauth_refresh\.refresh|GCSCredsPoller|\.credentials\.\{.*\}\.json"
  agent-orchestrator/server/ --type py` — expect 0 hits in `server/`.

- [ ] **(b5) `env_file` is required on every spawn.** Grep:
  `rg "env_file: str \| None\b" agent-orchestrator/server/tmux_spawn.py agent-orchestrator/server/usage_tracker.py` —
  expect 0 hits. The signatures must require `env_file: str` (no `None`).

- [ ] **(b6) CredsEnvPoller is alive on the central VM.** Inside central VM journalctl:
  `sudo journalctl -u orchestrator | grep -i "CredsEnvPoller started"` — find at least one match in the last service
  restart cycle.

### C. Backlog auto-generation from plans (Phase 6 HARD RULE)

- [ ] **(c1) `regen_backlog_from_plan.py` exists and parses real plans without error.** Manual:
  `cd agent-orchestrator && python -m server.regen_backlog_from_plan --pm-path
  ../unified-trading-pm` (verify it ran without exception; revert the side-effect on mock backlog before committing).

- [ ] **(c2) `PlanRegenLoop` is wired in lifespan.** Grep:
  `rg "PlanRegenLoop\(" agent-orchestrator/server/server.py` — expect at least 1 hit in the lifespan block.

- [ ] **(c3) Idempotency holds.** Run `regen` twice in a row against the same plans — second run should report
  `new_tasks=0, skipped_existing=N`. (Run inside a local environment / mock — never in production.)

- [ ] **(c4) Manual endpoint exists.** `grep "/api/backlog/regen" agent-orchestrator/server/server.py` — exactly one
  `@app.post` handler.

- [ ] **(c5) CLAUDE.md HARD RULE is present.** Grep:
  `rg "Agent-orchestrator backlog is plan-driven" unified-trading-pm/cursor-configs/CLAUDE.md` — expect 1 hit.

### D. Safety mechanisms (Phase 3)

- [ ] **(d1) Stuck-agent detection runs.** `WorkerLivenessKicker` daemon in `server/worker_liveness.py` started in
  lifespan. Verify in journalctl: `grep "WorkerLivenessKicker started"`.

- [ ] **(d2) Auto-respawn refuses to spawn without env_file.** Read
  [`server/worker_liveness.py`](../../../../agent-orchestrator/server/worker_liveness.py) auto-respawn path — must
  return early with a `WARN` log when account has no `oauth_token_env_file`.

- [ ] **(d3) Pre-spawn dirty-state gate is in place.** Grep:
  `rg "worktree_clean_check\.\(commit_and_push_dirty_repos\|check_slot_clean\)" agent-orchestrator/server/server.py` —
  expect at least 2 hits.

- [ ] **(d4) Git staleness alert fires.** `notify_git_staleness_red` exists in
  `agent-orchestrator/server/notifications/slack.py` AND `telegram.py`. Run `gh api repos/.../code/search`-style grep —
  both must exist.

### E. Notifications

- [ ] **(e1) Both notification modules export the same 11-function inventory.** Grep:
  `rg "^def notify_\|^async def notify_" agent-orchestrator/server/notifications/slack.py
  agent-orchestrator/server/notifications/telegram.py` — slack should have 10 funcs (`notify_setup_token_expiring`
  included), telegram should have 8 funcs + `notify_orchestrator_restart_loop`. Removed funcs must NOT appear:
  `notify_oauth_refresh_succeeded/failed`, `notify_oauth_token_expiring`.

- [ ] **(e2) Slack webhook is configured on the central VM.** SSH to central, run
  `sudo grep AGENT_ORCHESTRATOR_SLACK_WEBHOOK /home/ubuntu/unified-trading-system-repos/agent-orchestrator/.env.local`
  — value must be a non-empty `https://hooks.slack.com/services/...` URL.

- [ ] **(e3) Telegram chat ID is set.** Same env file — `ORCHESTRATOR_TELEGRAM_BOT_TOKEN` + `ORCHESTRATOR_TELEGRAM_CHAT_ID`
  populated.

### F. State persistence (Phase 8)

- [ ] **(f1) SQLite state.db exists and is writable.** On central:
  `ls -lh /home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db` — exists, mode `664`, owned
  by `ubuntu`.

- [ ] **(f2) Periodic snapshots fire.** Verify `last_snapshot_iso` in `/health` payload is < 1h old (default
  `ORCHESTRATOR_SNAPSHOT_INTERVAL_SECONDS=3600` on the central VM).

- [ ] **(f3) GCS / S3 backup is honest about its target.** Read [`server/gcs_sync.py`](../../../../agent-orchestrator/server/gcs_sync.py)
  — currently GCS-only; AWS-fleet VMs without `ORCHESTRATOR_GCS_BUCKET` set keep state on local disk only. Verify this
  is the documented state in
  [`codex/04-architecture/agent-orchestrator-overview.md`](../../../codex/04-architecture/agent-orchestrator-overview.md)
  § "Secrets + buckets" (the "Known gap" callout should still be present). If S3-side snapshot has shipped, the doc must
  reflect it.

### G. Dashboard

- [ ] **(g1) Firebase Hosting deploys are current.** `dashboard/dist/` tarball SHA matches the last `agent-orchestrator`
  LDR commit that touched `dashboard/src/*`. Run
  `cd agent-orchestrator/dashboard && git log -1 --pretty=%h -- src/` and verify the Firebase Hosting console matches.

- [ ] **(g2) Landing page hits `/api/fleet/summary`.** Grep:
  `rg "/api/fleet/summary" agent-orchestrator/dashboard/src/Landing.tsx` — expect 1 hit.

- [ ] **(g3) Per-VM proxy baseUrl is set correctly.** Grep:
  `rg "/api/vms/" agent-orchestrator/dashboard/src/App.tsx` — `backendBaseUrl()` returns `${BOOTSTRAP_URL}/api/vms/${b.id}` for non-central backends.

- [ ] **(g4) SetupTokenBadge (not OAuthBadge) is the only auth surface.** Grep:
  `rg "OAuthBadge\|oauth_expires_at\|oauth_expired\|oauth_expires_in_seconds" agent-orchestrator/dashboard/src/` —
  expect 0 hits. `SetupTokenBadge` should be the only auth-clock surface.

### H. VM provisioning (Phase 9)

- [ ] **(h1) Packer template parses.** Run:
  `cd deployment-service/packer/agent-orchestrator && packer validate .` — exit 0.

- [ ] **(h2) `bootstrap_vm.sh` detects prebaked marker.** Grep:
  `rg "/etc/orchestrator-ami-version\|IS_PREBAKED" agent-orchestrator/scripts/bootstrap_vm.sh` — expect ≥3 hits.

- [ ] **(h3) Launch script supports `AMI_ID` override.** Grep:
  `rg "AMI_ID" deployment-service/scripts/vm/launch-epic-vm-aws.sh
  deployment-service/scripts/vm/lib/aws_ec2_launch_lib.sh` — expect ≥2 hits.

- [ ] **(h4) Packer README + codex DNS-cutover SSOT both link to current code paths.** Read
  [`deployment-service/packer/agent-orchestrator/README.md`](../../../../deployment-service/packer/agent-orchestrator/README.md)
  +
  [`codex/05-infrastructure/agent-orchestrator-dns-cutover.md`](../../../codex/05-infrastructure/agent-orchestrator-dns-cutover.md) —
  no dead pointers (every file path resolves).

### I. EIP + DNS rollout state (Phase 11)

- [ ] **(i1) EIP allocation script exists and is executable.** Run:
  `bash deployment-service/scripts/aws/allocate-orchestrator-eips.sh --help` (or `-h`) — exits 0 with usage text. Do NOT
  run `--all` from the audit; allocation is operator-cost.

- [ ] **(i2) Fleet IPs in `backends.json` are either EIPs OR explicitly dynamic.** Cross-reference with
  `aws ec2 describe-addresses --filters "Name=tag:Project,Values=agent-orchestrator" --region ap-northeast-1 --query
  'Addresses[].{ip:PublicIp, instance:InstanceId, vm:Tags[?Key==\`VmId\`]|[0].Value}'`. If any VM's `backends.json url`
  IP isn't in this list, document it as "dynamic — drifts on stop/start" in the audit result.

- [ ] **(i3) DNS records exist OR the recipe is operator-deferred.** For each fleet VM, run
  `dig +short api-<vm>.agent-orchestrator.odum-research.com`. If no record exists, verify the
  [DNS-cutover doc](../../../codex/05-infrastructure/agent-orchestrator-dns-cutover.md) still marks it operator-deferred
  ("DNS zone access — operator-only credentials").

### J. Codex doc alignment

- [ ] **(j1) Connectivity model in overview doc matches code.** Read
  [`codex/04-architecture/agent-orchestrator-overview.md`](../../../codex/04-architecture/agent-orchestrator-overview.md)
  § "Connectivity model" — auth re-termination + private-VPC proxy described. Cross-check against `server/server.py::proxy_to_vm`.

- [ ] **(j2) No stale `OAuthBadge` / `oauth_refresh` / `GCSCredsPoller` references in any orchestrator codex doc.** Grep:
  `rg "OAuthBadge\|oauth_refresh\|GCSCredsPoller\|swap_claude_account" unified-trading-pm/codex/04-architecture/agent-orchestrator-overview.md
  unified-trading-pm/codex/05-infrastructure/agent-orchestrator-*.md
  unified-trading-pm/codex/12-agent-workflow/orchestrator-*.md
  unified-trading-pm/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — expect either 0 hits OR every
  hit must be inside a "removed in Phase 4b-cleanup" historical note.

- [ ] **(j3) Notification inventory matches.** Compare the table in
  [`codex/05-infrastructure/agent-orchestrator-slack-notifications.md`](../../../codex/05-infrastructure/agent-orchestrator-slack-notifications.md)
  to the actual `def notify_*` inventory in `server/notifications/`. Counts must match.

- [ ] **(j4) Fleet topology table in worker-topology doc matches `backends.json`.** Read
  [`codex/05-infrastructure/agent-orchestrator-worker-topology.md`](../../../codex/05-infrastructure/agent-orchestrator-worker-topology.md)
  § "Current fleet" — each VM's IP/instance ID matches `backends.json` (or backends.json says EIP — see check i2).

### K. Operational hygiene (operator-laptop slot hosts + crons)

- [ ] **(k1) `verify-slot-host-symmetry.sh` exits 0 on every operator laptop.** Run:
  `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh` — exit 0 required on Harsh laptop AND any Ikenna
  laptop currently driving slot 1+2.

- [ ] **(k2) Plan-hygiene cron is active.** Check `crontab -l` on the planning VM (central API VM = ikenna-vm) — entry
  at `0 5 * * *` UTC running `scripts/plan-hygiene/run_hygiene_sweep.sh`. Last run timestamp < 25h old.

- [ ] **(k3) Orphan-ping audit cron is active.** GCP Cloud Scheduler:
  `gcloud scheduler jobs describe uts-prod-orphan-ping-audit --location=asia-northeast1` — state `ENABLED`, schedule
  `15 2,6,10,14,18,22 * * *`.

- [ ] **(k4) `orchestrator_vm_registry.yaml` validates.** Run:
  `python3 unified-trading-pm/scripts/orchestrator/regen_vm_registry.py --check` — exit 0. Every plan's `assigned_vm`
  must be in the registry.

### L. Plan workflow + audit pool

- [ ] **(l1) `human_led_audit_pool_2026_05_21.md` is current.** Open
  [`plans/active/issues/human_led_audit_pool_2026_05_21.md`](../../../plans/active/issues/human_led_audit_pool_2026_05_21.md)
  — at least one of the 14 rows has been picked up since the prior audit OR an operator [ack] is in the comments.
  Operator-judgment check.

- [ ] **(l2) Workspace-qg ghost issue is tracked.** Open
  [`plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md`](../../../plans/active/issues/workspace_qg_ci_startup_failure_2026_05_26.md)
  — the affected-repos list reflects current state; the GitHub Support ticket reference is still valid.

### E2E Orchestrator Verification

- **(e2e-spawn)** Spawn a worker on a non-prod slot via `POST <central>/api/vms/vm-defi/api/slots/9/spawn` with a
  recovery boot prompt; observe the slot start a tmux session, post `/heartbeat`, then `/done`. Use a noop task (e.g.
  read a file + report sha). Cleanup: `DELETE` the slot afterwards.

- **(e2e-dispatch)** Pick one queued task from the backlog (any `status: queued, prereqs met`); confirm
  `dispatch.pick_next_task` returns it for an idle slot via `POST .../api/slots/N/boot`.

- **(e2e-failover)** Simulate an exhausted account by manually setting `weekly_pct=96` on one account row via
  `POST .../api/accounts/<id>/refresh-usage` (or DB write in a dev environment). Observe `rotate_all_slots_off_account`
  fire; verify slot respawns with the new account's env_file. Restore the row afterwards.

- **(mock-upstream)** Orchestrator health checks, plan-hygiene cron, slot management, and notification dispatch MUST be
  auditable against a local-only orchestrator instance (`ORCHESTRATOR_MODE=mock` + `CLOUD_MOCK_MODE=true`) — no real
  cloud calls needed.

## Success Criteria

- All A–L checklist items GREEN (or explicitly marked "deferred — operator action with ticket reference").
- All 10 epic VMs + the central API VM show as `reachable` in `/api/fleet/summary`.
- `verify-slot-host-symmetry.sh` exits 0 for every active operator laptop.
- No oauth/credentials legacy code paths remain in `agent-orchestrator/server/` (B4).
- All codex docs in § "Codex SSOTs" are last-touched within 30 days OR explicitly marked stable + verified by the
  current audit.

## Operating notes

- This audit is intended to take **~60-90 minutes** end-to-end when nothing has drifted; expand only when a check
  surfaces a real gap.
- **Never run `allocate-orchestrator-eips.sh --all`** from the audit — that's operator-cost. The audit only verifies the
  script exists and parses.
- **Never run the Packer `build`** from the audit — that costs an EC2 hour and creates AMI snapshots. `packer validate
  .` is sufficient.
- When a check surfaces a real drift, capture in the result file's "Findings" section with severity:
  - 🔴 **P0** — production fleet broken (auth, spawn, dispatch, dashboard inaccessible)
  - 🟠 **P1** — operational gap (snapshots stale, cron broken, doc drift on load-bearing rule)
  - 🟡 **P2** — codex/doc drift that doesn't affect runtime
  - ⚪ **P3** — nice-to-have polish

## Output Format

Result file at `plans/audit/results/orchestrator_master_audit_YYYY_MM_DD.md`. Frontmatter, then sections per A–L
checklist (one heading per area), then "Findings" (per-severity sublist), then "Recommendations" (action items with
owner + ETA). See `../README.md` for the canonical result-file template.

## Linked Results

| Date       | Result file                                                                            | Status |
| ---------- | -------------------------------------------------------------------------------------- | ------ |
| 2026-05-28 | [orchestrator_master_audit_2026_05_28.md](../results/orchestrator_master_audit_2026_05_28.md) | (pending — first run with new comprehensive instructions) |
