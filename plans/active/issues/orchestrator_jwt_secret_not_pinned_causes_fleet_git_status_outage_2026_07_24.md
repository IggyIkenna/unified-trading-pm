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
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, auth, jwt, orch_token, slot-host-symmetry, git-status-report, alerting, outage]
related: [/codex/04-architecture/agent-orchestrator-alerting.md, /codex/05-infrastructure/per-tab-worktrees.md]
created: 2026-07-24
last_updated: 2026-07-24
priority: P1
parent_epic: orchestrator_master
source:
  "operator relayed the slot-host-symmetry DRIFT alert (17 consecutive 15-min pages, 2026-07-24 17:45-21:15 UTC) and the
  full agent-orchestrator-alerts Slack history same session; root-caused live via SSM against the orchestrator VM
  (i-0c9b283b31d6b5ca7), live-remediated, and a real code gap (missing RECOVERED bookend) fixed same session"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
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

- [ ] [OPERATOR] P1. **Pin `ORCHESTRATOR_JWT_SECRET_GCS`** for `orchestrator.service`, mirroring the existing internal
      secret/key pattern: create a persisted secret object (e.g.
      `gs://central-element-323112-orchestrator-creds/orchestrator/jwt-secret.txt`, a random value, NOT derived from
      anything guessable), add `Environment=ORCHESTRATOR_JWT_SECRET_GCS=gs://...` to
      `/etc/systemd/system/orchestrator.service` (via `sudoedit` per the unit's own header comment), then
      `systemctl daemon-reload && systemctl restart orchestrator.service` — a deliberate restart of the shared
      orchestrator, so this needs an operator-chosen maintenance window, not a silent agent action. **Done when**: a
      restart of `orchestrator.service` no longer invalidates existing `.orch_token` files (verify: capture a token,
      restart the service, re-use the same token, confirm it still validates).
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
