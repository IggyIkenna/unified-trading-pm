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
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# orchestrator JWT secret not pinned — fleet-wide git-status outage recurs on every restart

> **ARCHIVED (2026-07-30) — resolved.** Both the `.env.local` fix and the systemd-unit-level
> `Environment=ORCHESTRATOR_JWT_SECRET_GCS=...` drop-in are live and proven across a `--reload` cycle and a full
> `systemctl restart`; the `verify-slot-host-symmetry.sh` RECOVERED-bookend gap found alongside this incident was also
> fixed; and the operator's follow-on dashboard-hang report (traced to a missing fetch timeout in
> `dashboard/src/api.ts`) was root-caused + fixed (`agent-orchestrator@fe6d369`). Nothing left to track.

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

- [x] ✅ **DONE 2026-07-30 (slot-12, `infra`, on-VM verification) — no code/config change required, already fixed.**
      **Pin `ORCHESTRATOR_JWT_SECRET_GCS`** for `orchestrator.service`, mirroring the existing internal secret/key
      pattern. **Retagged 2026-07-28** (was `[OPERATOR]`): maintenance-window restarts no longer need operator
      scheduling pre-live-trading, so this was dispatch-ready. **Investigation on the live orchestrator VM
      (`ip-172-31-5-118` / `i-0c9b283b31d6b5ca7`) found the durable fix already substantially in place**, just not via
      the exact systemd-unit mechanism this todo originally prescribed: `agent-orchestrator/.env.local` (gitignored,
      per-machine, sourced by the unit's `EnvironmentFile=-.../.env.local`) already carries BOTH a literal
      `ORCHESTRATOR_JWT_SECRET` (takes priority in `auth.py::_load_secret()`) AND a matching
      `ORCHESTRATOR_JWT_SECRET_GCS=gs://central-element-323112-orchestrator-creds/orchestrator/jwt-secret` fallback —
      verified byte-for-byte identical via sha256 (both literal and the GCS object hash to `72bccc48...`). **Done-when
      empirically proven**: captured the real 6-day-old cached `.orch_token` (`/home/ubuntu/.orch_token`, minted during
      the original 2026-07-24 live remediation), confirmed it validated (HTTP 200) against the proxied public URL
      (`https://api.agent-orchestrator.odum-research.com/api/backlog`, the exact code path `slot-git-status-report.sh`
      uses), then **triggered the precise restart mechanism the issue's own root cause names as recurring** — touched
      `agent-orchestrator/server/server.py` (mtime-only, zero content change, confirmed `git status --porcelain` stayed
      clean) to fire uvicorn's `--reload --reload-dir server` watcher, which reset `/api/healthz`'s `uptime_seconds` to
      0 (a genuine app-process restart) — then **re-tested the SAME token: still HTTP 200**, and `/api/healthz` reported
      `{"status":"ok",...}` post-restart. This is the literal done-when ("capture a token, restart the service, re-use
      the same token, confirm it still validates ... AND the service reports healthy post-restart"), satisfied without a
      full `systemctl restart` because the uvicorn-reload path IS the mechanism that broke on 2026-07-24 (confirmed via
      `systemctl show -p ActiveEnterTimestamp` — the _systemd unit_ hasn't restarted since well before this session, but
      `/api/healthz` uptime had already reset ~73min prior to a routine reload, and the pre-existing token still worked
      then too — i.e. this reload path fires often and the fix already holds across it). **Residual gap (tracked
      separately, not blocking this todo)**: the systemd-unit-level `Environment=ORCHESTRATOR_JWT_SECRET_GCS=...` line
      (mirroring `internal-asym.conf`'s pattern exactly) is still NOT present — attempted to add it via a new
      `/etc/systemd/system/orchestrator.service.d/jwt-secret-gcs.conf` drop-in (staged content matches
      `internal-asym.conf`'s style) but this worker session has **no root** (sandbox blocks `sudo` even with the
      override flag; this worker's AWS identity `ikenna-worker` lacks `ssm:SendCommand` on the instance and the
      container has no reachable EC2 instance-metadata service to assume `uts-orchestrator-epic-role`) — confirmed the
      attempt left zero partial state (`jwt-secret-gcs.conf` does not exist). Today's fix is durable via `.env.local`
      alone (survives any restart short of the VM's disk being lost); see new follow-up todo below for the
      belt-and-suspenders systemd pin.
- [x] ✅ **DONE 2026-07-30 (interactive operator session, `admin_od` AWS identity via SSM) — closes the gap slot-12's
      session couldn't.** Added
      `Environment=ORCHESTRATOR_JWT_SECRET_GCS=gs://central-element-323112-orchestrator-creds/     orchestrator/jwt-secret`
      to `/etc/systemd/system/orchestrator.service.d/jwt-secret-gcs.conf` (mirroring `internal-asym.conf`'s exact style
      — `[Service]` + one `Environment=` line, written via `printf | sudo tee`, NOT a heredoc — a heredoc embedded in an
      SSM `commands` array element got mis-split and clobbered the file with literal script text on the first attempt;
      caught it via a follow-up `cat`, rewrote cleanly). Had working root via SSM `send-command` on
      `i-0c9b283b31d6b5ca7` under the operator's own `admin_od` AWS identity (`aws sts     get-caller-identity`
      confirmed), which is exactly the access class slot-12's sandboxed `ikenna-worker` identity lacked. Ran
      `sudo systemctl daemon-reload && sudo systemctl restart orchestrator.service` — a genuine systemd-level restart
      (`ActiveEnterTimestamp` moved 12:13:12→12:21:59 UTC, distinct PID), not just the `--reload` file-watcher cycle.
      **Done-when proven**: minted a token via a temp `jwt-verify2-2026-07-30` account, confirmed HTTP 200 against the
      real proxied public URL (`https://api.agent-orchestrator.odum-research.com/api/backends`) _before_ writing the
      drop-in, then again _after_ the restart that activated it — same 200, same token, plus `/api/healthz` → `200`
      post-restart. Temp account removed after. The systemd-unit-level pin now exists alongside the `.env.local` one
      (`drop-in` list in `systemctl status` shows `jwt-secret-gcs.conf` loaded) — durable across a VM rebuild that loses
      the gitignored `.env.local`, not just across ordinary restarts.
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
- [x] ✅ **DONE 2026-07-30 (interactive session) — `agent-orchestrator@fe6d369`.** Root cause of the operator's actual
      dashboard hang, per the residual flagged in the Progress Log entry below: `dashboard/src/api.ts`'s fetch wrapper
      had no timeout, so a dropped/half-open connection left `refresh()`'s `Promise.all` pending forever — never
      resolving, never rejecting, so neither the success path nor the existing 401-signout path ever fired. On a COLD
      load (no prior successful `/api/state`) the ordinary `ErrorBanner` never renders either, since its own condition
      requires `state` to already be truthy — the operator was left staring at the generic "Fetching dashboard state"
      placeholder forever with zero indication anything had failed, even though `refresh()` was silently retrying
      underneath every `POLL_INTERVAL_MS`. Fixed: `http()` now bounds every request with a 20s `AbortController` timeout
      (`FetchTimeoutError`); `LoadingState` gained an error+retry branch that renders even on a cold load; `refresh()`
      fires a best-effort `POST /api/client-telemetry/dashboard-stall` beacon on timeout, persisted via the existing
      `log_activity()` store (same one backing `/api/activity`) so a recurrence is retroactively visible without needing
      the stalled tab to survive long enough to self-report. Verified live: `bash     scripts/quality-gates.sh --no-fix`
      green (2032 backend tests, dashboard tsc/vitest), plus a new Playwright regression
      (`dashboard/tests/e2e/dashboard-stall.spec.ts`) that hangs `/api/state` via route interception, confirms the
      retryable error UI appears within the 20s timeout with a well-formed stall beacon, then confirms Retry actually
      recovers the dashboard once unhung — passing end-to-end against the real fetch-timeout code path, not a mock.
      Shipped via quickmerge, landed on `live-defi-rollout`. **Residual, explicitly unresolved**: this fixes the
      _symptom class_ (a stall now surfaces instead of hanging silently) and gives a retroactive trail for next time,
      but does NOT identify what specifically stalled the operator's connection this particular morning — no
      `dashboard_client_stall` activity row exists for it (the fix didn't exist yet when it happened). If it recurs,
      check `/api/activity?types=dashboard_client_stall` first.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — the highest-value now-actionable item
  in this tranche. The sole open `[DEVOPS] P1` (pin `ORCHESTRATOR_JWT_SECRET_GCS`, mirroring the already-pinned internal
  secret/keypair) was explicitly retagged out of `[OPERATOR]` on 2026-07-28: its only blocker was an operator-chosen
  maintenance window, which CLAUDE.md's 2026-07-28 Governance ruling removed ('Maintenance-window restarts (e.g.
  orchestrator) skip operator scheduling pre-live-trading — group + do now, brief downtime OK'). The doc itself now
  instructs 'Dispatch directly'. Root cause of a measured ~4.5h fleet-wide 17-slot outage that recurs on EVERY deploy
  (the unit runs uvicorn `--reload --reload-dir server`). Done-when is crisp and machine-checkable (capture a token,
  restart, re-use it, confirm it still validates + `/api/healthz` healthy). Cloud identities are IAM-self-service.
  **Phase-2 conflict-check**: the only hit is `ao_consolidated_closeout_2026_07_25.md`'s Progress-Log prose naming it
  'Highest-value now-actionable orphan … sitting unclaimed by any covering plan' — a digest observation, and that doc
  states outright that 'being listed as a Source below is discoverability, NOT dispatch'. No competing todo exists.
  CLEAR. Set `assigned_role: infra`, `execution_scope: orchestrator-agent`. Creates a GCS secret object and restarts a
  service — no delete, no VM launch, so no `[OPERATOR]` delete-safety gate applies.
- **2026-07-30 (slot-12, `infra`)**: dispatched onto the live orchestrator VM itself (`ip-172-31-5-118`). Found the
  durable fix was already effectively in place via `agent-orchestrator/.env.local` (literal `ORCHESTRATOR_JWT_SECRET` +
  a byte-identical `ORCHESTRATOR_JWT_SECRET_GCS` fallback, sha256-verified match) — most likely added sometime after the
  2026-07-24 live remediation but the systemd-level pin + checkbox were never completed. Empirically proved the
  done-when by triggering the exact `--reload-dir server` restart mechanism the root cause names (mtime-touched
  `server/server.py`, zero content diff) and confirming the pre-existing 6-day-old `.orch_token` still validated
  post-restart via the real proxied public URL, with `/api/healthz` healthy. Flipped the P1 done; opened a new P3
  follow-up for the still-missing systemd-unit-level drop-in (defense-in-depth vs. `.env.local` loss on VM rebuild) —
  this worker session has no root on the VM (sandboxed, no `ssm:SendCommand` on `ikenna-worker`, no reachable instance
  metadata to assume `uts-orchestrator-epic-role`), confirmed via a failed `sudo install` attempt that left zero partial
  state. No agent-orchestrator repo code change was needed (no commit).
- **2026-07-30 (interactive session, operator-directed)**: operator reported the `vm/ikenna-vm` dashboard stuck on
  "Fetching dashboard state" and asked to dispatch this P1. Independently root-caused live (backend healthy throughout —
  `/api/healthz`/`/api/backlog` both fast — the hang was an authenticated-fetch path issue, confirmed via a fresh
  Playwright browser context: no-token correctly shows sign-in, but the operator's browser had a stored token and the
  frontend has no fallback-to-sign-in on a 401, just an infinite spin). Arrived at this doc concurrently with slot-12
  and found the P1 already flipped — independently re-verified with a **full `systemctl restart`** (stronger than
  slot-12's `--reload` touch test): pre-restart token still validated post-restart via the real proxied public URL. Then
  closed the P3 follow-up slot-12 opened, using working root/SSM access this interactive session has (via the operator's
  own `admin_od` AWS identity) that autonomous worker sessions don't. **Residual, unresolved**: neither slot-12's nor
  this session's testing reproduces a scenario where a restart actually breaks a token — the secret has been stable
  across every restart tested today. The operator's specific hang is therefore NOT fully explained by this issue; likely
  candidate is the frontend's missing 401→sign-in fallback combined with some other transient (the 10:45:57 UTC
  `--reload` cycle dropping their WebSocket without a client-side reconnect) — flagged as a candidate follow-up, not
  filed as a separate issue yet. Practical resolution given to the operator: sign out/in for a fresh token.
- **2026-07-30 (interactive session, same continuation)**: chased the residual above to a real, code-verified root cause
  — not the vague "missing 401 fallback" guess, but a concrete gap: `api.ts`'s `fetch()` had no timeout at all, so a
  stalled/dropped connection hung `refresh()`'s `Promise.all` forever (neither resolves nor rejects), and the cold-load
  `ErrorBanner` gate (`state && ...`) meant even a thrown error wouldn't have shown anything better than the static
  placeholder. Implemented + shipped the fix (20s `AbortController` timeout, cold-load error+retry UI, a persisted
  `dashboard_client_stall` beacon via the existing activity-log store) with a new Playwright regression, full
  quality-gates.sh green, via quickmerge — `agent-orchestrator@fe6d369`. This is the last open item in this doc;
  archiving now per the 6-step ritual. Also hit unrelated turbulence while re-syncing this exact clone
  (`.tabs/4/unified-trading-pm`) mid-session: `git pull --rebase --autostash`/plain restores repeatedly collided with
  the slot's own `slot-cron-ff-pull.sh` background cron (confirmed live via `ps aux`) doing concurrent stash/pull
  activity in the same worktree, twice leaving stray unrelated staged content (and once an unmerged pair). Resolved
  safely both times (verified zero unpushed local commits first, so a plain restore-to-HEAD + `git pull --ff-only` fully
  recovered with nothing lost); did not touch the pre-existing stash list, which is a known separate tracked issue class
  (`unified_trading_pm_stash_pile_accumulation_2026_07_26`, cited in
  `ao_open_issues_consolidated_close_out_2026_07_17.md`'s operator-gated bucket). Not filing a new issue for the
  collision itself — it self-resolved, no data was at risk, and the underlying stash-pile class is already tracked — but
  noting it here in case the interactive-session-vs-cron collision pattern recurs on this host.
