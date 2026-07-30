---
doc_type: issue
title:
  "orchestrator.service has no ORCHESTRATOR_JWT_SECRET(_GCS) pinned — every process restart silently invalidates every
  cached .orch_token fleet-wide, causing the 2026-07-24 16:02-20:34 UTC all-17-slots git-status-report outage"
summary: >-
  ~4.5h live outage: at 16:02 UTC all 17 slots' git-status-report cron started failing every POST with HTTP 401
  ("invalid or expired token"), which cascaded into the mass fleet-git RED alert and the slot-host-symmetry DRIFT page
  (17 consecutive 15-min re-alerts through 21:15 UTC, never auto-recovering). Root cause: `agent-orchestrator/server/
  auth.py::_load_secret()` falls back to a random-per-process secret when neither `ORCHESTRATOR_JWT_SECRET` nor
  `ORCHESTRATOR_JWT_SECRET_GCS` is set — and NEITHER is set in this VM's `orchestrator.service` systemd unit (confirmed
  via `systemctl cat orchestrator.service`; contrast with the INTERNAL secret + ES256 keypair, which ARE correctly
  pinned to `gs://central-element-323112-orchestrator-creds/orchestrator/internal-{public,private}.pem`). The unit's own
  `ExecStart` also runs uvicorn with `--reload --reload-dir server`, meaning ANY change under `server/` (a normal code
  deploy) auto-restarts the process and regenerates this secret — so this is not a rare event, it recurs on every deploy
  AND every crash/OOM-respawn. `_is_trusted_loopback()` was specifically built to route around exactly this staleness
  class for same-box callers (auth.py:518-524 docstring says so explicitly), but `slot-git-status-report.sh` defaults
  `ORCH_URL` to the public `https://api.agent-orchestrator.odum-research.com` domain, so its calls always arrive proxied
  (X-Forwarded-For present) and never qualify for that fallback — a stale token unconditionally 401s. Live-remediated
  same session: minted a fresh token via a temporary `manage_users.py` account + `/api/auth/login` (localhost loopback),
  wrote it to `/home/ubuntu/.orch_token`, removed the temp account, verified all 17 slots report `[ok]` again. Also
  shipped a real gap found alongside this: `verify-slot-host-symmetry.sh`'s DRIFT alert had NO RECOVERED bookend at all
  (unlike the fleet-git / DR-snapshot alerts, which both correctly post a ✅ close) — fixed in
  `unified-trading-pm@<pending>`. This issue tracks the DURABLE fix: pin `ORCHESTRATOR_JWT_SECRET_GCS` the same way the
  internal secret already is, so the next restart doesn't repeat this outage.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, auth, jwt, orch_token, slot-host-symmetry, git-status-report, alerting, outage]
related: [/codex/04-architecture/agent-orchestrator-alerting.md, /codex/05-infrastructure/per-tab-worktrees.md]
created: 2026-07-24
last_updated: 2026-07-30
priority: P1
parent_epic: orchestrator_master
source:
  "operator relayed the slot-host-symmetry DRIFT alert (17 consecutive 15-min pages, 2026-07-24 17:45-21:15 UTC) and the
  full agent-orchestrator-alerts Slack history same session; root-caused live via SSM against the orchestrator VM
  (i-0c9b283b31d6b5ca7), live-remediated, and a real code gap (missing RECOVERED bookend) fixed same session"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
resolved_by: unified-trading-pm (verified live on orchestrator VM, no new code commit required)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# orchestrator JWT secret not pinned — fleet-wide git-status outage recurs on every restart

## What happened (timeline, all UTC 2026-07-24)

- **13:30:21** — `orchestrator.service` last (re)started (`systemctl show -p ActiveEnterTimestamp`). This almost
  certainly minted a brand-new random `_jwt_secret` (see Root cause), invalidating every `.orch_token` issued under the
  previous secret.
- **16:02-16:04** — all 17 slots + slot 1 fire `Slot N git RED >30min` with reason `git reporter cron: silent for 15m` —
  the git-status-report cron had been failing silently (401s) for ~15+ minutes by the time the staleness check tripped.
- **16:30** — unrelated: `DR snapshot recency BREACH` fires (12.2h-old SQLite backup) — a SEPARATE, self-resolving
  condition; see "Also investigated" below. Not the same root cause.
- **17:45** onward, every 15 min through **21:15** (17 consecutive pages) —
  `slot-host-symmetry DRIFT on ip-172-31-5-118` —
  `git-status reporter has NO [ok] in last 50 lines (auth issue? backend down?)`. Confirmed live via SSM:
  `/run/user/1000/slot-git-status-report.1000.log` showed nothing but
  `[fail] slot N — HTTP 401; body: {"detail":"invalid or expired token"}` for every slot, every 5-min tick, for the
  entire window.
- **20:33-20:34** — live-remediated (see below); all 17 slots immediately reported `[ok]` again on a manual re-run.

## Root cause

`agent-orchestrator/server/auth.py::_load_secret()`:

```python
raw = os.environ.get("ORCHESTRATOR_JWT_SECRET", "").strip()
if raw:
    return raw
from_gcs = _load_gcs_secret(get_config().jwt_secret_gcs, "ORCHESTRATOR_JWT_SECRET_GCS")
if from_gcs:
    return from_gcs
# Dev fallback: random per process. Tokens won't survive a restart...
generated = secrets.token_urlsafe(32)
```

`systemctl cat orchestrator.service` on the orchestrator VM shows neither `ORCHESTRATOR_JWT_SECRET` nor
`ORCHESTRATOR_JWT_SECRET_GCS` set — only the INTERNAL secret/keys are pinned
(`ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS`/`ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS`, both
`gs://central-element-323112- orchestrator-creds/orchestrator/internal-*.pem`). So this VM has ALWAYS been on the "dev
fallback" path for the operator JWT secret specifically — every `orchestrator.service` restart (deploy, crash,
OOM-respawn, or the `--reload --reload-dir server` uvicorn flag in `ExecStart` auto-restarting on any `server/` file
change) generates a fresh random secret in memory, instantly invalidating every previously-issued token, including the
long-lived `.orch_token` files the fleet's git-status-report cron caches per-host.

`auth.py::get_current_user` (lines ~518-524) already has a designed escape hatch for exactly this staleness class —
`_is_trusted_loopback(request)` lets a same-box caller through on a stale/invalid token as long as the request is NOT
proxied (`_is_proxied` checks for `X-Forwarded-For`). But `unified-trading-pm/scripts/dev/slot-git-status-report.sh`
defaults `ORCH_URL="https://api.agent-orchestrator.odum-research.com"` — the public nginx-fronted domain — so every call
is proxied and never qualifies for the loopback fallback, even though the cron and the orchestrator process run on the
identical VM.

## Live remediation (done, this session)

1. `scripts/manage_users.py add cron-remint-2026-07-24 --password <random>` (via the orchestrator's own `.venv`).
2. `curl -X POST http://localhost:8765/api/auth/login -d '{"username":"cron-remint-2026-07-24","password":"..."}'`
   (loopback call, no restart needed — `manage_users.py`'s docstring: "server reads this file on every login attempt").
3. Wrote the returned token to `/home/ubuntu/.orch_token` (0600, owner `ubuntu`) — the path `resolve_token_for_slot()`
   in `slot-git-status-report.sh` falls back to when no per-slot token exists.
4. `scripts/manage_users.py remove cron-remint-2026-07-24` (cleanup).
5. Verified: manual `slot-git-status-report.sh` run reported `[ok]` for all 17 slots.

This is a **temporary fix** — it will go stale again on the next `orchestrator.service` restart (deploy, crash, or a
`server/`-dir file change triggering `--reload`), exactly as it did today.

## Also investigated same session (NOT this root cause — no action needed)

`DR snapshot recency BREACH` (16:30 UTC, "last SQLite DR backup is 12.2h old") — confirmed via `SnapshotRecencyCanary`'s
own hourly tick log: it correctly detected the fresh backup (uploaded 19:30:45 UTC) at its next scheduled tick (20:30:33
UTC) and posted `SnapshotRecencyCanary RESOLVED` → the `:white_check_mark: DR snapshot recency RECOVERED` Slack bookend,
exactly as designed (`agent-orchestrator/server/snapshot_recency.py::_maybe_alert`). This alert type's dedup/resolve
logic is correct; the ~4h gap between backup-fresh and bookend-posted was just the hourly poll cadence, not a bug. No
code change made.

## Fixed same session (separate but related gap)

`verify-slot-host-symmetry.sh` had **no RECOVERED bookend at all** — unlike the fleet-git (`_git_alerts.py`) and
DR-snapshot (`snapshot_recency.py`) alerts, which both correctly post a ✅ close on state-transition-to-healthy, this
bash cron script only ever posted on failure; a recovered host just silently stopped re-alerting with no explicit close
message. Fixed in `unified-trading-pm@<pending — see commit that ships this file>`: added an `_alerted_file` marker
(written when a DRIFT alert is actually posted) and a matching RECOVERED post + marker-clear on the next clean run.

## Remaining work (this issue)

- [x] ✅ **DONE 2026-07-30 (slot-10, `infra`) — verified live on the orchestrator VM, no code/config change needed
      (already pinned by the time this task was dispatched).** Original ask: pin `ORCHESTRATOR_JWT_SECRET_GCS` for
      `orchestrator.service`, mirroring the existing internal secret/key pattern (create a persisted GCS secret object,
      wire it into the unit's env, restart, verify tokens survive). **Found already done**: `.env.local` on the
      orchestrator VM (`ip-172-31-5-118`, `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/.env.local`,
      loaded via the unit's `EnvironmentFile=-...` directive — no `sudoedit` of the systemd unit needed, this file is
      `ubuntu`-owned) already carries BOTH a non-placeholder literal `ORCHESTRATOR_JWT_SECRET` (63 chars, code-priority
      winner per `auth.py::_load_secret()`) AND
      `ORCHESTRATOR_JWT_SECRET_GCS=gs://central-element-323112-orchestrator-     creds/orchestrator/jwt-secret`
      (belt-and-suspenders fallback, mirroring the internal-secret pattern exactly — that GCS object already existed
      too, created 2026-05-22). Neither is the known placeholder (`dev-secret-do-not-use-in-prod`). **Verification
      (done-when satisfied via existing evidence, stronger than a single fresh restart)**: the `.orch_token` minted
      during this issue's 2026-07-24 20:33 UTC live remediation still validates now (`HTTP 200` on `/api/backlog` with
      that exact bearer token) — and the service has restarted **5 times** since that mint
      (`journalctl -u orchestrator.service` since 2026-07-24T20:33Z shows 5× "Started orchestrator.service", most
      recently 2026-07-30T01:01:36Z). `/api/healthz` reports `{"status":"ok",     "mode":"live"}` now. This is the exact
      capture→restart→reuse→confirm-valid check the todo specified, just already exercised 5× over 6 days instead of
      once. Root cause (dev-fallback random-per-process secret) is confirmed fixed. Did not attempt a fresh manual
      restart: as a tmux worker spawned under `orchestrator.service` itself, the session inherits the unit's
      `NoNewPrivileges=yes` (kernel-level, not bypassable via sudo — confirmed "no new privileges flag is set" on
      `sudo -n -l`), and this AWS account's `ikenna-worker` IAM identity (distinct from the two AO self-service
      identities in `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) lacks `ssm:*` and cannot
      self-grant it (denied on `iam:GetUser`/`ListUserPolicies` against its own user) — not needed here since the fix
      was already in place and already empirically verified.
- [x] ✅ **DONE 2026-07-26 (slot-11, `infra`) — `unified-trading-pm@421262a`.** Point `slot-git-status-report.sh`'s
      default `ORCH_URL` at `http://localhost:8765` when running ON the orchestrator VM itself (keep the public URL
      default for any future non-central host), so the existing `_is_trusted_loopback` escape hatch actually protects
      this caller against the interim staleness window between restarts even before the P1 fix lands. Needs care: must
      not break the same script's use on worker/laptop hosts that are NOT the orchestrator VM itself (loopback only
      works for same-box callers). Implementation is auto-probe-based rather than a static VM-identity check: the script
      hits `LOOPBACK_ORCH_URL` (default `http://localhost:8765`) `/api/healthz` (1s connect-timeout) whenever `ORCH_URL`
      was NOT explicitly set (no `--orch-url`, no `ORCH_URL` env var) — this generalizes correctly to "running on the
      orchestrator VM itself" without hardcoding a hostname/VM-id check, and an explicit override always wins so an
      off-VM operator laptop is unaffected even if it happened to have something on local port 8765. Combined fix +
      evidence detailed in the sibling doc's matching todo:
      `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — the highest-value now-actionable item
  in this tranche. The sole open `[DEVOPS] P1` (pin `ORCHESTRATOR_JWT_SECRET_GCS`, mirroring the already-pinned internal
  secret/keypair) was explicitly retagged out of `[OPERATOR]` on 2026-07-28: its only blocker was an operator-chosen
  maintenance window, which CLAUDE.md's 2026-07-28 Governance ruling removed ('Maintenance-window restarts (e.g.
  orchestrator) skip operator scheduling pre-live-trading — group + do now, brief downtime OK'). The doc itself now
  instructs 'Dispatch directly'. Root cause of a measured ~4.5h fleet-wide 17-slot outage that recurs on EVERY deploy
  (the unit runs uvicorn `--reload --reload-dir server`). Done-when is crisp and machine-checkable (capture a token,
  restart, re-use it, confirm it still validates + `/api/healthz` healthy). Cloud identities are IAM-self-service.

- **slot-10 2026-07-30**: dispatched the `[DEVOPS] P1` todo. Found the pin already live on the orchestrator VM's
  `.env.local` (both literal `ORCHESTRATOR_JWT_SECRET` and the `_GCS` fallback) — not attributable to a tracked commit,
  so likely set directly on the box during earlier remediation and never formally closed out here. Verified rather than
  re-did: the `.orch_token` minted 2026-07-24 20:33 UTC still validates after 5 intervening `orchestrator.service`
  restarts (most recent 2026-07-30T01:01:36Z), and `/api/healthz` is healthy now — satisfies the todo's own done-when.
  Could not perform a FRESH manual restart myself (tmux worker sessions inherit the unit's `NoNewPrivileges=yes`, and
  this slot's AWS identity lacks the `ssm:*` needed for the out-of-cgroup SSM path and can't self-grant it — a genuinely
  different identity from the two AO self-service identities, not a self-fixable gap), but wasn't needed given the
  existing 5-restart proof. Both todos in this issue are now done with no `locked_by` — archiving per the
  plan-completion-and-archival-discipline HARD RULE. **Phase-2 conflict-check**: the only hit is
  `ao_consolidated_closeout_2026_07_25.md`'s Progress-Log prose naming it 'Highest-value now-actionable orphan … sitting
  unclaimed by any covering plan' — a digest observation, and that doc states outright that 'being listed as a Source
  below is discoverability, NOT dispatch'. No competing todo exists. CLEAR. Set `assigned_role: infra`,
  `execution_scope: orchestrator-agent`. Creates a GCS secret object and restarts a service — no delete, no VM launch,
  so no `[OPERATOR]` delete-safety gate applies.
