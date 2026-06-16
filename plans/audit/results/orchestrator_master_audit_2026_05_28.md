---
type: audit-result
title: orchestrator_master audit — 2026-05-28
epic: orchestrator_master
auditor: harsh-claude-opus
date: "2026-05-28"
status: complete
instructions_ref: plans/audit/instructions/orchestrator_master_audit_instructions.md (v2 — refreshed 2026-05-28)
assigned_vm: vm-orchestrator
tier: L5
instructions: plans/audit/instructions/orchestrator_master_audit_instructions.md (v2 — refreshed 2026-05-28)
locked_by: live-defi-rollout
---

# orchestrator_master — Audit Result 2026-05-28

First run against the refreshed comprehensive audit instructions. Many checks GREEN, two **P0 incidents** surfaced
(central API VM impaired, fleet VMs unreachable from this audit host on the public path), plus several P1/P2 gaps.

## Section A — Fleet topology + connectivity

| ID  | Check                                         | Result      | Notes                                                                                                                                                                                                                                  |
| --- | --------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| a1  | Central API `/health` returns 200             | 🔴 **FAIL** | `curl https://api.agent-orchestrator.odum-research.com/health` times out (5s, 15s). DNS resolves to `13.113.200.22` correctly. Raw HTTP/HTTPS to `13.113.200.22` also times out.                                                       |
| a2  | `backends.json` matches running EC2 inventory | 🟢 PASS     | 10 epic VMs + 1 central + 1 local laptop = 12 entries. AWS `describe-instances` confirms all 10 epic VMs `running` with matching IPs. Central VM `i-0c9b283b31d6b5ca7` ("agent-orchestrator-vm-1") also `running`.                     |
| a3  | Central → fleet proxy reachable               | ⚪ N/A      | Cannot test — central API unreachable. Code path verified in `server/server.py::proxy_to_vm`.                                                                                                                                          |
| a4  | `/api/fleet/summary` fan-out works            | ⚪ N/A      | Cannot test — central API unreachable.                                                                                                                                                                                                 |
| a5  | Auth re-termination in `proxy_to_vm`          | 🟢 PASS     | Verified by code inspection: `_internal_tok = auth.get_internal_service_token()` + `fwd_headers["authorization"] = f"Bearer {_internal_tok}"` (server.py:2767-2769). Operator JWT never leaves the central perimeter when proxy works. |

### Root cause of a1 failure

`aws ec2 describe-instance-status --instance-ids i-0c9b283b31d6b5ca7` reports:

- Instance state: `running`
- System status: `ok`
- **Instance status: `impaired`** ← network stack wedged

Central VM appears to have an OS-level network/health failure. The instance is "running" but not responding on any port
from external traffic. Recovery requires AWS console: stop + start the instance (forces it to new physical hardware) or
reboot via API.

## Section B — Auth model (Phase 4b-cleanup setup-tokens-only HARD RULE)

| ID  | Check                                                       | Result  | Notes                                                                                                                                                                                               |
| --- | ----------------------------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| b1  | Every account in `accounts.json` has `oauth_token_env_file` | 🟢 PASS | All 4 accounts (sub-a-ikenna, sub-b-iggy2london, sub-c-ikenna-odum, harsh-primary) declare an env file.                                                                                             |
| b2  | Every account has `setup_token_expires_at`                  | 🟢 PASS | sub-a/b/c expire 2027-05-21; harsh-primary 2027-05-22. None within 30 days.                                                                                                                         |
| b3  | Env files exist in both GCS and S3 buckets                  | 🟢 PASS | GCS `gs://central-element-323112-orchestrator-creds/accounts/` and S3 `s3://uts-orchestrator-creds-427895769566/accounts/` both have all 4 `<id>.env` files (205-210 bytes each, dates 2026-05-22). |
| b4  | Legacy credential-swap code paths removed                   | 🟢 PASS | 0 hits in `server/` for `swap_credentials_for`, `restore_credentials`, `oauth_refresh.refresh`, `GCSCredsPoller`, `.credentials.{...}.json`.                                                        |
| b5  | `env_file` is required on every spawn                       | 🟢 PASS | 0 hits for `env_file: str \| None` in `tmux_spawn.py` and `usage_tracker.py`. Signatures are mandatory `env_file: str`.                                                                             |
| b6  | CredsEnvPoller alive on central VM                          | ⚪ N/A  | Central VM unreachable; can't verify journalctl. Code path is wired in `server/server.py` lifespan.                                                                                                 |

## Section C — Backlog auto-generation (Phase 6 HARD RULE)

| ID  | Check                                                   | Result  | Notes                                                                                                                                           |
| --- | ------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| c1  | `regen_backlog_from_plan.py` exists + parses real plans | 🟢 PASS | Module present at `server/regen_backlog_from_plan.py` (430 lines). Smoke-tested earlier this session: scans 14 plans, dedupes correctly.        |
| c2  | `PlanRegenLoop` wired in lifespan                       | 🟢 PASS | `server.py:211 — plan_regen = _regen_mod.PlanRegenLoop(on_regen=_on_plan_regen)`.                                                               |
| c3  | Idempotency holds (2nd regen → 0 new)                   | 🟢 PASS | Verified earlier this session — second run reports `new_tasks=0, skipped_existing=95`.                                                          |
| c4  | `/api/backlog/regen` manual endpoint exists             | 🟢 PASS | `server.py:1470 — @app.post("/api/backlog/regen", dependencies=AUTHED_DEPS)`.                                                                   |
| c5  | CLAUDE.md HARD RULE present                             | 🟢 PASS | Found in `cursor-configs/CLAUDE.md` § "Other key rules" — "Agent-orchestrator backlog is plan-driven (HARD RULE codified 2026-05-28, Phase 6)". |

## Section D — Safety mechanisms (Phase 3)

| ID  | Check                                     | Result  | Notes                                                                                                                                               |
| --- | ----------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| d1  | `WorkerLivenessKicker` daemon             | 🟢 PASS | Module present at `server/worker_liveness.py`. Started in lifespan. (Live verification N/A — central down.)                                         |
| d2  | Auto-respawn refuses no-env_file accounts | 🟢 PASS | Verified by code inspection: `worker_liveness.py:735-746` returns early with `WARN` log when `acc_def is None or not acc_def.oauth_token_env_file`. |
| d3  | Pre-spawn dirty-state gate                | 🟢 PASS | 4 references to `worktree_clean_check.{commit_and_push_dirty_repos\|check_slot_clean}` in `server.py`.                                              |
| d4  | `notify_git_staleness_red` exists         | 🟢 PASS | Both `slack.py` and `telegram.py` export the function.                                                                                              |

## Section E — Notifications

| ID  | Check                                   | Result  | Notes                                                                                                                                                                             |
| --- | --------------------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| e1  | Notification inventory matches expected | 🟢 PASS | Slack: 10 `def notify_*` funcs; Telegram: 8 `async def notify_*` funcs. Removed funcs (`notify_oauth_refresh_succeeded/failed`, `notify_oauth_token_expiring`) ARE GONE — 0 hits. |
| e2  | Slack webhook configured on central     | ⚪ N/A  | Central VM unreachable; can't ssh + grep `.env.local`.                                                                                                                            |
| e3  | Telegram chat ID set on central         | ⚪ N/A  | Same — central unreachable.                                                                                                                                                       |

## Section F — State persistence (Phase 8)

| ID  | Check                                            | Result  | Notes                                                                                                                                                                                                                                                       |
| --- | ------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| f1  | SQLite state.db exists on central                | ⚪ N/A  | Central VM unreachable.                                                                                                                                                                                                                                     |
| f2  | Periodic snapshots fire (last_snapshot_iso < 1h) | ⚪ N/A  | Central VM unreachable; can't read `/health` payload.                                                                                                                                                                                                       |
| f3  | State-snapshot AWS↔S3 gap honestly documented   | 🟢 PASS | Verified in `codex/04-architecture/agent-orchestrator-overview.md` § "Secrets + buckets" — the **Known gap** callout is present and accurate. `server/gcs_sync.py` is GCS-only; AWS fleet without `ORCHESTRATOR_GCS_BUCKET` keeps state on local disk only. |

## Section G — Dashboard

| ID  | Check                                    | Result            | Notes                                                                                                                                                                    |
| --- | ---------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| g1  | Firebase Hosting deploys current         | 🟢 PASS (partial) | Dashboard SPA at `https://agent-orchestrator.odum-research.com` returns HTTP 200 in 0.5s. Cannot verify SHA-match without comparing to Firebase console — operator-side. |
| g2  | Landing page hits `/api/fleet/summary`   | 🟢 PASS           | `dashboard/src/Landing.tsx` has the fetch call.                                                                                                                          |
| g3  | Per-VM proxy baseUrl wired               | 🟢 PASS           | `dashboard/src/App.tsx::backendBaseUrl` returns `${BOOTSTRAP_URL}/api/vms/${b.id}` for non-central backends.                                                             |
| g4  | OAuthBadge removed, only SetupTokenBadge | 🟢 PASS           | 0 hits for `OAuthBadge`, `oauth_expires_at`, `oauth_expired`, `oauth_expires_in_seconds` in `dashboard/src/`.                                                            |

## Section H — VM provisioning (Phase 9)

| ID  | Check                                                     | Result               | Notes                                                                                                                                 |
| --- | --------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| h1  | Packer template validates                                 | ⚪ N/A               | `packer` not installed on this audit host. Operator-runnable: `cd deployment-service/packer/agent-orchestrator && packer validate .`. |
| h2  | `bootstrap_vm.sh` detects `/etc/orchestrator-ami-version` | 🟢 PASS              | 8 hits for `IS_PREBAKED` + 1 for `/etc/orchestrator-ami-version`. Skip logic present for STEP 1, 2, warm-cache rsync.                 |
| h3  | `launch-epic-vm-aws.sh` supports `AMI_ID` override        | 🟢 PASS              | 5 hits across `launch-epic-vm-aws.sh` and `lib/aws_ec2_launch_lib.sh`. Falls back to SSM-resolved Ubuntu when unset.                  |
| h4  | Packer README + DNS-cutover doc link to live paths        | 🟢 PASS (spot-check) | Sampled the file references in both docs; all resolve.                                                                                |

## Section I — EIP + DNS (Phase 11)

| ID  | Check                                    | Result                   | Notes                                                                                                                                                                                                                                                                        |
| --- | ---------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| i1  | EIP allocation script exists + parses    | 🟢 PASS                  | `bash allocate-orchestrator-eips.sh -h` exits 0 with usage text. Script is idempotent + tagged.                                                                                                                                                                              |
| i2  | Fleet IPs are EIPs OR explicitly dynamic | 🟡 **operator-deferred** | `aws ec2 describe-addresses --filters tag:Project=agent-orchestrator` returns empty — no fleet EIPs allocated. Central VM EIP `13.113.200.22` exists (`agent-orchestrator-vm-eip`, allocation `eipassoc-0f3bb6623bc7fbfda`). Fleet IPs remain dynamic per Phase 11 deferred. |
| i3  | DNS records exist OR operator-deferred   | 🟡 **operator-deferred** | `dig` returns no A records for `api-<vm>.agent-orchestrator.odum-research.com` (10 VMs checked, all empty). Recipe still operator-deferred.                                                                                                                                  |

## Section J — Codex doc alignment

| ID       | Check                                                               | Result            | Notes                                                                                                                                                                                                                                                                                   |
| -------- | ------------------------------------------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| j1       | Connectivity model in overview matches code                         | 🟢 PASS           | Auth re-termination + private-VPC proxy + central-VM-also-planning-role all reflected in `agent-orchestrator-overview.md` § "Connectivity model" + § "Fleet topology".                                                                                                                  |
| j2       | No stale `OAuthBadge` / `oauth_refresh` / `GCSCredsPoller` in codex | 🟢 PASS           | 6 hits surfaced; every one is in a "removed" / "historic" / "legacy" context. No claims of current behaviour.                                                                                                                                                                           |
| j3       | Notification inventory in slack-notifications.md matches code       | 🟢 PASS           | Doc table lists 11 functions; code exposes 10 (slack) + 8 (telegram with overlap). Inventory matches the documented current set.                                                                                                                                                        |
| j4       | Worker-topology IP table matches `backends.json`                    | 🟢 PASS (sampled) | Sampled vm-defi/cefi/tradfi/sports — doc IPs match backends.json. Remaining 6 VMs not exhaustively cross-checked here.                                                                                                                                                                  |
| j5 (NEW) | Fleet VM port-8026 reachability claim in worker-topology doc        | 🟡 **STALE**      | Worker-topology.md § "Fleet dashboard entry point" says "Port 8026 is open to 0.0.0.0/0 in the security group." **Actual SG `sg-0080310387e84f613` restricts port 8026 to `172.31.0.0/16` (private VPC only)** — which is the CORRECT centralized-router behaviour. Doc claim is stale. |

## Section K — Operational hygiene

| ID  | Check                                                      | Result                   | Notes                                                                                                                                                                              |
| --- | ---------------------------------------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| k1  | `verify-slot-host-symmetry.sh` exits 0 on operator laptops | 🔴 **FAIL** (audit host) | Script reports `1 passed / 5 failed` on this audit host (harsh-claude session running). Slot-host symmetry not compliant.                                                          |
| k2  | Plan-hygiene cron `0 5 * * *` UTC on planning VM           | ⚪ N/A                   | Central/planning VM unreachable — can't run `crontab -l`.                                                                                                                          |
| k3  | `uts-prod-orphan-ping-audit` Cloud Scheduler enabled       | 🔴 **FAIL**              | Job NOT FOUND in `central-element-323112` / any location. The CLAUDE.md HARD RULE references it as the GCP-side orphan-ping cron; the SSOT-named job is missing or never deployed. |
| k4  | `regen_vm_registry.py --check` exits 0                     | 🟢 PASS                  | "OK — all assigned_vm values valid (11 vm-ids)".                                                                                                                                   |

## Section L — Plan workflow + audit pool

| ID  | Check                                | Result         | Notes                                                                                                                                                                                                          |
| --- | ------------------------------------ | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| l1  | Audit pool active + showing progress | 🟡 **STALLED** | 14 rows: 2 IN-FLIGHT (#1, #2), 12 SEEDED (#3-#14). No movement since 2026-05-21 seed date — no rows transitioned to PICKED-UP / AUDIT-COMPLETE / WRAPPER-PLAN-CREATED / DONE. The dispatch flow isn't running. |
| l2  | Workspace-qg ghost issue tracked     | 🟢 PASS        | `workspace_qg_ci_startup_failure_2026_05_26.md` updated today (2026-05-28) to include deployment-ui as an affected repo. GitHub Support ticket #4422570 referenced.                                            |

---

## Findings

### 🔴 P0 — Production fleet impacted

- **F-1 — Central API VM is impaired and unreachable.** Instance `i-0c9b283b31d6b5ca7` (EIP `13.113.200.22`) reports
  `instance status: impaired`. The dashboard SPA loads but cannot reach the central API. All `/api/fleet/summary`,
  `/api/vms/<id>/*` proxy calls, `/api/auth/login`, and per-VM operations are down. **Action**: AWS console reboot or
  stop+start the instance.

- **F-2 — Fleet VMs are not externally reachable, but documented as if they were.** Public IPs on port 8026 return
  connection timeout from this audit host. SG `sg-0080310387e84f613` correctly restricts port 8026 to `172.31.0.0/16`
  (private VPC only). This is **architecturally correct** (browser→central→VPC→fleet), but:
  - The codex doc claims port 8026 is `0.0.0.0/0` — stale.
  - `backends.json` `url` fields contain public IPs that are not reachable externally. Anyone trying to debug a fleet VM
    by curl-ing its `url` from outside the VPC will fail.

  Severity is P0 because if the central API is down (F-1) the entire fleet becomes unreachable — there's no operator
  backdoor on the public path. Add operator SSH tunnel docs OR open port 8026 for operator IP ranges.

### 🟠 P1 — Operational gap

- **F-3 — `uts-prod-orphan-ping-audit` Cloud Scheduler job is missing.** CLAUDE.md names this as the GCP-side cron for
  the 4-hourly orphan-ping audit; it's not present in `central-element-323112` (any location). The audit is currently
  not running. **Action**: redeploy the Terraform module at
  `deployment-service/terraform/gcp/orphan_ping_audit_scheduler.tf` (per CLAUDE.md SSOT) OR confirm the cron moved
  somewhere else and update the SSOT.

- **F-4 — Audit pool isn't being dispatched.** 14 rows in `human_led_audit_pool_2026_05_21.md` have shown no movement
  since seed date 2026-05-21 (week+ ago). Rows #3-#14 are all SEEDED — the audit pool dispatch flow isn't actually
  generating wrapper plans. Either the planning VM (= central API VM, currently impaired) hasn't been running the
  dispatch, OR the operators haven't been picking rows. **Action**: pick a row + ack it on the next planning session.

- **F-5 — `verify-slot-host-symmetry.sh` fails on the audit host (Harsh laptop).** 5 of 6 checks fail. Same machine
  drives slot 2 interactive sessions. Per the local-slot=VM-slot HARD RULE, this is a violation. **Action**: install the
  FF-pull cron + git-status reporter per `codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md` Step 5.

### 🟡 P2 — Doc drift / minor cleanup

- **F-6 — Worker-topology doc port claim is stale.** § "Fleet dashboard entry point" says port 8026 open `0.0.0.0/0`.
  Reality: restricted to `172.31.0.0/16`. Update the doc to reflect VPC-only access.

### ⚪ Not checked

- Live state on the central VM (state.db freshness, journalctl, env.local secrets, plan-hygiene cron). Blocked on F-1.
- Live e2e spawn/dispatch/failover smoke tests. Blocked on F-1.
- Live verification that fleet VMs' orchestrator backends are running (only the SG was checked — port reachability
  doesn't prove the process is up).

---

## Recommendations

| Owner                 | ETA                   | Action                                                                                                                                                                                                            |
| --------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operator (Ikenna)** | ASAP                  | F-1: AWS console — stop + start instance `i-0c9b283b31d6b5ca7` (the central API VM). The stop forces it to new underlying hardware; the start brings it back. EIP stays attached.                                 |
| **Operator**          | After F-1 cleared     | Re-run this audit end-to-end — all the ⚪ N/A live-state checks become testable.                                                                                                                                  |
| **Operator**          | This week             | F-3: Re-apply the Terraform for `uts-prod-orphan-ping-audit`. If the cron is deliberately decommissioned, update CLAUDE.md to remove the SSOT reference.                                                          |
| **Operator**          | Next planning session | F-4: Pick at least one audit-pool row + ack it. If the pool itself is no longer useful, mark it as archived with a successor plan.                                                                                |
| **Operator (Harsh)**  | This session          | F-5: Install the slot-host symmetry crons on this laptop per `harsh-laptop-migration-2026-05-20.md` Step 5.                                                                                                       |
| Agent                 | 30 min                | F-6: Update `agent-orchestrator-worker-topology.md` § "Fleet dashboard entry point" — replace "Port 8026 is open to 0.0.0.0/0" with the correct VPC-only restriction + operator SSH-tunnel note. Doc-only change. |

## Summary

- **Auth model**: 🟢 Phase 4b-cleanup HARD RULE holds. All 4 accounts on setup-tokens; both clouds; legacy code paths
  fully removed.
- **Backlog regen**: 🟢 Phase 6 implementation is sound; idempotent + manual endpoint + CLAUDE.md HARD RULE in place.
- **Safety mechanisms**: 🟢 All code paths confirmed.
- **Notifications**: 🟢 Inventory clean — old funcs removed, new ones present.
- **Dashboard**: 🟢 SPA up; landing + proxy code present; SetupTokenBadge sole auth-clock.
- **VM provisioning**: 🟢 Packer + bootstrap fast-path + AMI_ID override all wired (not run, but operator-ready).
- **EIP + DNS**: 🟡 Operator-deferred — recipes and scripts shipped, no operational action yet.
- **Live infrastructure**: 🔴 Central API VM impaired (F-1) — currently blocks the dashboard + every audit check that
  needs live state. Top-of-stack incident.
- **Documentation**: 🟢 Phase 4b-cleanup + Phase 6 changes accurately reflected. 🟡 One stale claim about fleet port
  exposure (F-6).
- **Operational hygiene**: 🟠 Two missing pieces — the orphan-ping cron (F-3) and a slot-host laptop compliance fix
  (F-5). Plus the audit pool isn't being driven (F-4).

Net: the orchestrator implementation is in good shape (code + docs aligned post the 2026-05-28 sweep). The current pain
is operational — one VM impaired and three workflow loops that have gone quiet.
