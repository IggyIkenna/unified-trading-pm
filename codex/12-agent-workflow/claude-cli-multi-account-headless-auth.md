---
doc_type: codex-ssot
title: Claude CLI Multi-Account Headless Authentication (SSOT)
summary:
  Permanent SSOT for headless multi-account claude CLI auth on orchestrator VMs — use claude setup-token (1-year OAuth
  token via CLAUDE_CODE_OAUTH_TOKEN, never copy .credentials.json), always unset ANTHROPIC_API_KEY (it silently wins and
  flips to metered billing), seed a per-session CLAUDE_CONFIG_DIR for interactive TUI, shared-account pool with three
  rotation triggers, and context-preserving --resume.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, authentication, self-healing, monitoring, slack]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
    /codex/12-agent-workflow/canonical-plan-flow.md,
  ]
created: 2026-05-21
authoritative_for:
  [
    claude CLI multi-account headless setup-token authentication,
    setup-token scope limits (subscription tier is not readable),
  ]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/12-agent-workflow/canonical-plan-flow.md,
    /codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md,
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
    plans/epics/orchestrator_master.md,
  ]
owner:
last_reviewed:
code_refs: [agent-orchestrator/server/accounts.py, agent-orchestrator/server/usage_tracker.py]
---

# Claude CLI Multi-Account Headless Authentication (SSOT)

> **Permanent SSOT** for how the orchestrator authenticates claude CLI on VMs across multiple Max subscriptions.
> Codified 2026-05-21 from an operator-shared reference doc following the 2026-05-21 cascade incident.
>
> Authoritative over: `plans/epics/orchestrator_master.md § Auth & accounts r3`,
> `plans/active/ issues/claude_credentials_rotation_in_memory_staleness_2026_05_21.md § 9e` (both reference this file).
>
> Supersedes: `plans/active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md` (banner- marked SUPERSEDED).

## TL;DR

For headless multi-account automation across VMs use **`claude setup-token`** (1-year long-lived OAuth token,
`sk-ant-oat01-...` format) consumed via the **`CLAUDE_CODE_OAUTH_TOKEN`** env var. Do NOT copy `.credentials.json`
between machines — that's the short-lived interactive-session refresh chain; copying causes refresh-token-rotation
lockouts.

## Why this mechanism

The CLI exposes two auth paths:

| Path                                       | Mechanism                                         | Lifetime                                | Multi-machine                            | Right for our use?                                      |
| ------------------------------------------ | ------------------------------------------------- | --------------------------------------- | ---------------------------------------- | ------------------------------------------------------- |
| Interactive `/login` → `.credentials.json` | Short-lived access_token + rotating refresh_token | ~8h access / weeks refresh, both rotate | **NO** — copying file causes lockouts    | No (this is what bit us 2026-05-21)                     |
| `claude setup-token` → long-lived token    | Single static OAuth token via env var             | ~1 year, no rotation                    | **YES** — same token works on N machines | YES — the official path for CI/headless                 |
| `ANTHROPIC_API_KEY` env var                | Metered API, separate billing                     | Permanent until revoked                 | Yes but DIFFERENT BILLING                | No — would charge per-token instead of Max subscription |

`setup-token` is the only path that:

- Bills against the Max subscription quota (not metered API credits)
- Is account-scoped (one token = one Max account = one quota pool)
- Survives ~1 year without operator intervention
- Allows the same token to be deployed across multiple machines without rotation contention

## Critical gotcha: ANTHROPIC_API_KEY precedence

If BOTH `ANTHROPIC_API_KEY` and `CLAUDE_CODE_OAUTH_TOKEN` are set in the env when `claude` runs, **the API key wins**.
Billing silently flips from Max subscription to metered API credits — same behavior, completely different cost model.
The orchestrator's systemd unit must NOT set `ANTHROPIC_API_KEY`. Every claude-spawning code path must
`unset ANTHROPIC_API_KEY` before `exec claude`.

Verification:

```bash
# On the VM:
sudo systemctl show orchestrator --property=Environment | tr ' ' '\n' | grep ANTHROPIC
# (empty = correct — no override)
```

## Interactive sessions: CLAUDE_CONFIG_DIR + onboarding seed (added 2026-05-22)

**Context**: `claude` v2.1.145 introduced a first-run onboarding wizard (theme → "Select login method") that **ignores
`CLAUDE_CODE_OAUTH_TOKEN` for interactive TUI sessions** and forces browser OAuth regardless of the env var. This broke
every orchestrator-spawned interactive agent (main + workers) after the upgrade.

**Key distinction** — the env token has different behaviour by invocation mode:

| Mode                     | `CLAUDE_CODE_OAUTH_TOKEN` sufficient?          | Notes                                        |
| ------------------------ | ---------------------------------------------- | -------------------------------------------- |
| `claude -p 'prompt'`     | **YES** — works without seed                   | Headless print; wizard never runs            |
| Interactive `claude` TUI | **NO** — wizard blocks it in v2.1.145          | Must seed `CLAUDE_CONFIG_DIR` (see below)    |
| Remote Control session   | **NO** — setup tokens are inferred-scoped only | Needs full browser-login `.credentials.json` |

### The fix: per-session `CLAUDE_CONFIG_DIR` + onboarding seed

For every interactive spawn, give the agent an **isolated, pre-seeded `CLAUDE_CONFIG_DIR`** so the wizard is skipped:

1. **Set `CLAUDE_CONFIG_DIR`** to a per-session path (e.g. `~/.claude-configs/<session_id>/`). This isolates creds,
   settings, and onboarding state across agents and accounts.
2. **Seed `$CLAUDE_CONFIG_DIR/.claude.json`** once on first use:
   ```json
   {
     "theme": "dark",
     "hasCompletedOnboarding": true,
     "hasCompletedProjectOnboarding": true,
     "hasTrustDialogAccepted": true,
     "bypassPermissionsModeAccepted": true
   }
   ```
3. **Source the account env file every spawn** (`source ~/.claude-accounts/<id>.env`). The token is NOT persisted to the
   config dir — `echo $CLAUDE_CODE_OAUTH_TOKEN` is empty in a plain shell; must be re-injected each time.
4. **`exec claude <flags>`** — now reaches the chat prompt authenticated, no wizard.

The seeded `.claude.json` persists across re-spawns of the same session (one-time per config dir). The token is
re-sourced from the env file each spawn. The `CLAUDE_CONFIG_DIR` is account-agnostic (the token isn't stored there), so
the same config dir can serve multiple accounts, or use separate dirs per (slot, account) — either works.

### Orchestrator implementation (agent-orchestrator)

The orchestrator wires this via two layers:

**tmux_spawn.py** (`_ensure_claude_config_dir()` + `ONBOARDING_SEED`):

- Derives `CLAUDE_CONFIG_DIR=<base>/<session>` where base = `ORCHESTRATOR_CLAUDE_CONFIG_BASE` env (default
  `~/.claude-configs`).
- Creates the dir and writes `.claude.json` from `ONBOARDING_SEED` on first call per session.
- Both `spawn()` (worker path) and `spawn_named()` (main/review/backup agent path) **require** `env_file: str` (Phase
  4b-cleanup 2026-05-28 — the legacy `env_file=None` fallback that allowed claude to inherit
  `~/.claude/.credentials.json` is gone; every spawn must source a per-account setup-token env file).
- Commits: workers `1717768` (2026-05-22), main/review/backup agents `76c966e` (2026-05-23), env_file-required
  enforcement `87becbb` (2026-05-28).

**server.py** (`spawn_agent_endpoint`):

- `SpawnAgentRequest.account_id: str | None` — field signature, but the runtime now refuses (HTTP 400) when `account_id`
  is missing OR the resolved account in `accounts.json` has no `oauth_token_env_file` (Phase 4b-cleanup).
- When set, resolves `oauth_token_env_file` from `data/config/accounts.json` via `load_accounts()` and passes it as
  `env_file` to `spawn_named()`.
- Pattern mirrors the worker spawn path (`tmux_spawn.spawn(env_file=…)`).

### Quick verification recipe

```bash
# Prove setup token works headless (no seed needed):
set -a; . ~/.claude-accounts/sub-a-ikenna.env; set +a
claude -p 'reply AUTH_OK'   # → AUTH_OK

# Prove the interactive headless recipe (with seed):
mkdir -p /tmp/ck && printf '%s' \
  '{"theme":"dark","hasCompletedOnboarding":true,"hasCompletedProjectOnboarding":true,"hasTrustDialogAccepted":true,"bypassPermissionsModeAccepted":true}' \
  > /tmp/ck/.claude.json
tmux new-session -d -s ck "CLAUDE_CONFIG_DIR=/tmp/ck bash -c 'source ~/.claude-accounts/sub-a-ikenna.env; cd /tmp; exec claude'"
# → skips wizard, reaches chat prompt authenticated (accept one folder-trust prompt with Enter)

# Prove the orchestrator spawn path:
python3 -c "from server import tmux_spawn; print(tmux_spawn.spawn(slot_id=99, boot_prompt='reply SPAWN_WORKS', cwd='/tmp', env_file='$HOME/.claude-accounts/sub-a-ikenna.env'))"
tmux capture-pane -t orch-slot-99 -p | tail   # → authenticated, replied SPAWN_WORKS
```

## One-time setup (on a machine with browser)

For EACH distinct Max subscription:

1. Sign into the target Anthropic Max account at <https://claude.ai>
2. Run on a machine with a browser available:
   ```bash
   claude setup-token
   ```
3. Approve the OAuth flow in the browser
4. **Copy the printed token immediately** — it's shown ONCE, not stored on disk
5. Sign out, sign into the next subscription, repeat

Result: one `sk-ant-oat01-...` token per distinct Max subscription. Store in a password manager or encrypted secrets
file.

## VM file layout

```
~/.claude-accounts/                  # chmod 700
├── sub-a-ikenna.env                 # chmod 600
├── sub-b-iggy2london.env            # chmod 600
├── sub-c-ikenna-odum.env            # chmod 600
└── sub-d-odum1default.env           # chmod 600
```

**These two bucket paths are the canonical creds-bucket location — the ONLY place a setup-token
`.env` file should ever be uploaded.** (Roster count is a snapshot, not re-verified every edit —
check `GET /api/accounts` for the live list rather than trusting a stale number here; last hand-count
was 2026-05-28 at 4 accounts, corrected 2026-08-18 to 7 (`sub-a` through `sub-g`) while onboarding
an 8th — don't trust either number without a live check.)

```
gs://central-element-323112-orchestrator-creds/accounts/<account_id>.env
s3://uts-orchestrator-creds-427895769566/accounts/<account_id>.env
```

**Do not copy these commands from `agent-orchestrator/docs/WORKER_SPAWN_PREREQUISITES.md`** — that
doc used to carry the same instructions with the bucket names left as unresolved placeholders
(`<creds-bucket>`), which cost a live session real time re-deriving them from `bootstrap_vm.sh` /
`creds_env_poller.py` on 2026-08-18. It now points back here instead of duplicating.

Each env file:

```bash
# ~/.claude-accounts/sub-a-ikenna.env
unset ANTHROPIC_API_KEY              # required — overrides token if set, flips to metered billing
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
export CLAUDE_ACCOUNT_LABEL=sub-a-ikenna   # for orchestrator logging + dashboard
```

The `unset` line is non-negotiable. Treat it as part of the env-file contract.

## Adding a BRAND-NEW account (not just a new host for an existing one)

Everything above (`~/.claude-accounts/`, the two creds buckets, `CredsEnvPoller`) is about
**distributing** a token to hosts. A brand-new account additionally needs registering with the
live orchestrator, and that step has a real gap (confirmed live 2026-08-18, igboestates-account
onboarding) that cost a session real time re-deriving — recorded here so it isn't re-discovered:

1. Mint the token (`claude setup-token`) and upload the `.env` file to both creds buckets.
   **Do NOT run `gcloud storage cp` / `aws s3 cp` directly** — an interactive session's
   `block_destructive_commands.py` `PreToolUse` hook rejects any raw GCS/S3 object-CLI subprocess
   call outright (workspace HARD RULE, not specific to this task — same rule QG STEP 5.105 enforces
   on committed code). Use UTL's `cloud_interface` instead, the exact pattern already used by
   `gcs_sync.py`'s own account-adjacent uploaders:
   ```python
   from unified_trading_library import get_storage_client
   get_storage_client(provider="gcp").upload_file(
       "central-element-323112-orchestrator-creds", f"accounts/{account_id}.env", str(local_path),
       content_type="text/plain",
   )
   get_storage_client(provider="aws").upload_file(
       "uts-orchestrator-creds-427895769566", f"accounts/{account_id}.env", str(local_path),
       content_type="text/plain",
   )
   ```
   `get_storage_client()` needs `GCP_PROJECT_ID`/`AWS_ACCOUNT_ID` set in the environment (not
   auto-detected) — export both before running, or the call raises `ValueError` immediately.
   Delete the local `.env` copy once both uploads succeed — don't leave a live token sitting on a
   laptop disk longer than needed.
2. Add a new `AccountDef` entry to `data/config/accounts.json` (`server/accounts.py`'s schema) —
   at minimum `id`, `label`, `tier`, `weekly_msg_limit`, `primary_email`, `operator`, and
   `oauth_token_env_file` (the `.env` filename from step 1, NOT the token itself — `accounts.json`
   never contains the secret, only a path reference to where the poller/spawn path reads it from).
   `tier` is `Literal["pro","max5","max20","team","enterprise","api"]` (`accounts.py:13`) —
   operator-declared and unverifiable from the token alone (see "Scope limitation" below), ask
   rather than guess; if the operator just says "a Max plan" with no further detail, `max20` /
   `weekly_msg_limit: 1200` is the established default for every one of this operator's personal
   accounts so far (`sub-a` through `sub-g`) — confirm against a recent sibling account's own entry
   rather than assuming the number never changes. Edit the LIVE file on the orchestrator VM
   (`$WD/data/config/accounts.json`, `WD` = `systemctl show orchestrator.service
--property=WorkingDirectory --value`) as the `ubuntu` user (`sudo -u ubuntu python3 -c '...'` via
   SSM, matching the file's real ownership) — back it up first (`shutil.copy` to a dated
   `.bak-<date>` alongside it) before writing.
3. **The gap**: unlike `POST /api/accounts/{id}/tier` (which writes `accounts.json` AND the live
   `AccountRow` for an EXISTING account), there is no equivalent "create" endpoint for a brand-new
   account. `bootstrap.sync_accounts_to_db()` (`server/bootstrap.py`) is the only code path that
   syncs `accounts.json` into the live DB-backed rows `/api/accounts` actually serves from, and it
   runs **once, at server boot** — confirmed via a full grep of `server/*.py`, zero other call
   sites. A raw file edit alone will NOT make the new account appear in `/api/accounts` or become
   spawn-eligible. **Restarting `orchestrator.service` IS required** to pick up a new account (an
   existing account's tier/limits can be live-edited via the API without one; a brand-new id
   cannot) — confirm with the operator before doing it, especially if other sessions have in-flight
   dispatches, rather than restarting unilaterally. **Verified safe live (2026-08-18,
   igboestates-account onboarding)**: `sudo systemctl restart orchestrator.service`, API back up in
   ~11s, all 24 live worker tmux sessions survived and reconnected (`KillMode=process` — only the
   uvicorn PID restarts).
4. After the restart, confirm via `GET /api/accounts` that the new `account_id` appears with
   `status: "healthy"` and the expected fields — `weekly_pct`/`five_hour_pct`/`*_resets_at` all come
   back `null` at this point, that's correct, not a bug: those are populated by the usage poller
   once the account is actually used for a spawn, not at registration time. A spawn against it
   succeeding (the "Quick verification recipe" above) is the final confirmation, not yet exercised
   by the 2026-08-18 pass — do it if you want full end-to-end proof, not just registration proof.

**Worth building, not yet built**: a live "register new account" endpoint that writes
`accounts.json` and inserts the new `AccountRow` in one call, the same way the tier-editor does for
an existing account — would remove the restart requirement entirely. Not filed as a todo here since
no active plan owns this; raise it as a new plan/issue if it recurs enough to be worth building.

### Gotcha: a brand-new account's first weekly window is NOT a fresh 7 days (confirmed 2026-08-18, `sub-h-igboestates`)

Do not be alarmed if a just-registered account's `weekly_pct` reads disproportionately high relative
to its `five_hour_pct` within hours of first use — this is expected, not a capture bug. Anthropic's
own docs (support.claude.com articles 8325606 and 11049741, Pro/Max plans) state the weekly limit
"resets at a fixed time each week that is assigned to your account... regardless of when you start
using Claude or when your subscription begins" — the window is a **fixed, per-account-assigned
calendar boundary**, not a rolling 7-day window anchored to first use. Confirmed live on
`sub-h-igboestates` (registered 2026-08-18): its `weekly_window_start` was `2026-08-13 08:00:00 UTC`
— five days before the account's first real use — cross-checked identically from two independent
sources (AO's server-polled `account_usage` row, and the account's own `~/.claude.json`
`cachedUsageUtilization.seven_day.resets_at`, worked back 7 days). A `five_hour` window that opened
at first-use today will naturally look small next to a `weekly` window with a multi-day head start;
this is not a burst penalty (searched for one specifically, 2026-08-18 — not documented, and the one
mechanism that ever rate-shaped Claude usage, peak-hour throttling, only ever touched the 5-hour
meter and was removed fleet-wide 2026-05-06) and not a poller/attribution bug. Full investigation:
`/plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` § "New-account
weekly-window inheritance". **Does not explain** the separate sub-d Pro-tier ~1047x multiplier
outlier tracked in that same doc — different mechanism, do not conflate the two.

## Switching accounts manually

```bash
source ~/.claude-accounts/sub-a-ikenna.env
claude /status   # confirms which account is active
```

For orchestrator-driven switching: the spawn endpoint sources the matching env file before `exec claude` (per
`plans/epics/orchestrator_master.md` Phase 4a). Operator never switches manually in steady state.

## Cross-operator shared account pool (codified 2026-05-29)

All accounts in `data/config/accounts.json` are available to **any operator's worker**, regardless of the `operator`
field tag. The `operator` field is metadata only (for logging / dashboards); it does NOT restrict which accounts can
serve which worker slots. This "shared pool" design means:

- harsh-pc workers can rotate to ikenna accounts when harsh's tokens are exhausted or stale.
- ikenna workers can use harsh accounts similarly.
- The pool is the union of all `accounts.json` entries with `failover_allowed: true` (default) and a valid
  `oauth_token_env_file`.

**Why**: the original 4 accounts (sub-a-ikenna, sub-b-iggy2london, sub-c-ikenna-odum, sub-d-odum1default) — grown since
(7+ as of 2026-08-18, `sub-a` through `sub-g`; check `GET /api/accounts` for the live list, see caveat above) — exist
so BOTH operators
can survive independently. Restricting by operator tag would waste the cross-operator failover benefit.

SSOT: `plans/active/cross_operator_auth_failover_2026_05_29.md`.

## Rotation across accounts — three triggers

The orchestrator rotates the account used for NEW SPAWNS when any of these fires:

| Trigger             | Detection mechanism                                                                     | Orchestrator action                                                                                              |
| ------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `rate_limit`        | Usage poller reports 5h_pct ≥ 95% OR weekly_pct ≥ 95% OR Sonnet limit hit               | `_pick_next_account()` selects lowest-pct available account; new spawns use new account                          |
| `auth_failed`       | Worker spawned, did NOT send /heartbeat within 180s of `/spawn` (setup-token stale/bad) | Spawn-heartbeat watchdog marks account `auth_failed`, rotates immediately, re-spawns slot on next available acct |
| `operator_directed` | POST `/api/slots/{id}/rotate-account` with `reason=operator_directed`                   | Immediate rotation; current worker keeps its token until /done; next spawn uses new account                      |

In-memory tokens of already-running workers are NOT swapped mid-session (claude CLI doesn't re-read env mid-session).
Rotation only affects subsequent spawns. Live workers continue on their existing token until they /done.

### Context-preserving resume across a token change (shipped 2026-06-17)

A worker / main agent that hits a **usage cap** is the one exception that continues across an account change — not a
mid-session swap (impossible; the CLI never re-reads env), but a **kill + `claude --resume <id>` relaunch** on the
headroom account. Verified facts (Claude Code v2.1.175 + official docs, 2026-06-17), used by the watchdog usage-cap
trigger + the MainAgentKeeper (`orchestrator_account_failover_resume_respawn_2026_06_17`):

- **Session id is assignable at launch** — `claude --session-id <uuid>` sets a specific id, so the orchestrator
  GENERATES the UUID at spawn (`tmux_spawn.new_session_id()`), owns it from t=0, and persists it on
  `SlotRow`/`AgentRow.claude_session_id`. No transcript-filename scraping, no race for the id.
- **`claude --resume <id>` reloads conversation context** when relaunched in the SAME `CLAUDE_CONFIG_DIR` (per-session,
  keyed by tmux session name → stable across respawns) + SAME cwd (the slot worktree → unchanged). The transcript is
  pure conversation history; it carries NO account identity.
- **Resume works across a token change.** Sourcing a different account's `CLAUDE_CODE_OAUTH_TOKEN` (env file) and
  resuming the same session authenticates as the new account while replaying the old conversation — because account
  identity lives only in the token (`.credentials.json` is bypassed entirely under setup-token env auth). Reusing the
  per-session config dir with a new token is clean; no clearing required.
- **Gotchas:** `--resume` must run from the original cwd (satisfied — same slot worktree); permissions don't carry
  across resume (covered — `--dangerously-skip-permissions`); resumed context is the _compacted_ history (acceptable);
  kill via the exact `tmux_spawn.kill_session(<name>)`, NEVER `pkill -f claude…` (a wildcard reaps sibling slots).

This is consistent with "live workers are not swapped mid-session" — the resume path kills the wedged process first,
then relaunches it; the new token is read fresh at launch. Full headroom-gating (decision B: leave frozen when no
headroom) is in `/codex/04-architecture/agent-orchestrator-overview.md` § "Trigger 1.4 — usage-cap account failover".

### Spawn-heartbeat watchdog (180s threshold)

Every `/api/slots/{id}/spawn` call starts a background 180-second watchdog:

1. On spawn, `last_spawned_at` is written to `SlotRow`; `spawn_retry_count` increments.
2. If the slot fails to send `/heartbeat` within 180s, the watchdog concludes the token is stale / the claude CLI
   couldn't authenticate.
3. The current account is marked `account_status = 'auth_failed'` in `account_usage`.
4. `_pick_next_account()` rotates to the next available account in the shared pool.
5. The slot is re-spawned with the new account.
6. A Slack alert fires with `reason: auth_failed` (see below).

Implementation: `FailoverLoop`-style background thread in `server/autospawn.py` (heartbeat watchdog). SSOT commit:
agent-orchestrator@6871070 (Phase 2 task-007).

### Slack alert schema for rotation events

Every rotation — regardless of trigger — posts to `#agent-orchestrator-alerts`:

```
🔄 Account rotated on <vm_id> slot <N> at <timestamp>
  reason: <rate_limit | auth_failed | operator_directed>
  from:   <old_account_id> (<old_weekly_pct>% weekly, <old_5h_pct>% 5h)
  to:     <new_account_id> (<new_weekly_pct>% weekly, <new_5h_pct>% 5h)
  [if auth_failed] spawn→heartbeat gap: <elapsed>s (threshold 180s)
```

The alert is posted via `server/slack_notifier.py` `notify_account_rotation()`. The webhook is read from
`ORCHESTRATOR_SLACK_WEBHOOK_URL` env var (not hardcoded; pulled from systemd EnvironmentFile).

## Multi-machine

The same token can be deployed across N machines simultaneously. **They all share that account's quota** — adding 2 VMs
with the same token doesn't multiply throughput; the 5h / weekly bars are per-account, not per-machine. Throughput
multiplication comes from having N DISTINCT subscriptions, each with its own token, distributed across the VMs.

Distribution: operator uploads the env files to both creds buckets (GCS and S3); every VM pulls via the `CredsEnvPoller`
daemon in `agent-orchestrator/server/creds_env_poller.py` (5-min poll, env var `ORCHESTRATOR_CREDS_GCS_BUCKET` /
`ORCHESTRATOR_CREDS_S3_BUCKET` selects cloud) into its local `~/.claude-accounts/`. The legacy `GCSCredsPoller` (which
synced `.credentials.<id>.json` short-lived token blobs) was deleted in Phase 4b-cleanup 2026-05-28.

## Verifying a token is valid + active

```bash
# Confirm which account/auth method is active in current shell
claude /status

# Quick non-interactive smoke test
echo "test" | claude -p "respond with ok"

# Confirm token env var is set
echo "${CLAUDE_CODE_OAUTH_TOKEN:0:20}..."

# Confirm API key is NOT set (would override the token)
echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-unset}"
```

## Distinct-quota check (NOT orgId alone — verify by quota, codified 2026-05-21 r2)

The failover benefit of adding a token to the roster depends on whether it draws from a **separate 5h/weekly quota
pool**. Two emails can be personal-Max **aliases** on one org (same `orgId`, ONE shared quota → no failover benefit), OR
**separate seats on a Team/Enterprise org** (same `orgId`, but SEPARATE per-seat quotas → real failover benefit).
`orgId` equality alone does NOT prove shared quota. **The authoritative test is the quota reading itself.**

```bash
# Authoritative: probe each candidate's quota via the env-file path and compare.
# IDENTICAL weekly% across two tokens => same quota pool => SKIP the second.
# DIFFERENT weekly% => distinct quota pools => keep both.
for acct in <candidate-a> <candidate-b>; do
  source ~/.claude-accounts/$acct.env
  echo "$acct"; claude /usage   # compare the weekly + 5h bars
done
```

> CLI 2.1.146 note: `claude auth status` returns only `{loggedIn, authMethod, apiProvider}` — it does NOT print `orgId`.
> The old `claude auth status | grep orgId` recipe no longer works; use the quota probe above.

**Empirical correction (2026-05-21 r2)**: `ikennaigboaka@gmail.com` (8% weekly) and `ikenna@odum-research.com` (90%
weekly) were earlier recorded as same-orgId aliases, but their `/usage` weekly bars are **wildly different** — proving
they draw from **separate quota pools** (consistent with separate seats on a Team org, not personal-Max aliases). They
ARE usable as distinct failover accounts. The earlier "same orgId ⇒ shared quota ⇒ skip" conclusion was the wrong
inference. Treat the quota probe — not orgId — as the deciding test.

## What NOT to do

| Don't                                                                        | Reason                                                                                                  |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Copy `~/.claude/.credentials.json` between machines                          | Different mechanism — rotating refresh-token chain; cross-machine copies cause `invalid_grant` lockouts |
| Set `ANTHROPIC_API_KEY` in any orchestrator env                              | Overrides `CLAUDE_CODE_OAUTH_TOKEN`, silently switches billing to metered API                           |
| Generate multiple tokens for the same account expecting quota multiplication | Tokens are sub-scoped, not token-scoped; N tokens for one sub = same 5h/weekly bars                     |
| Skip the `unset ANTHROPIC_API_KEY` line in env files                         | One inherited env var from a sibling process is all it takes to silently flip billing                   |
| Hardcode tokens in code or commit them to git                                | Tokens are bearer secrets; commit to operator's encrypted secrets store only                            |

## Revocation

To revoke a specific token (e.g. compromised VM, decommissioned machine):

1. Sign in at <https://claude.ai/settings/account>
2. Active Connections / API Keys section → revoke the specific token
3. Other tokens for the same account continue to work
4. Delete the env file from any VMs that had it
5. Rotate the GCS-stored copy via `push_creds_to_gcs.sh` with a fresh token

## Token expiration + renewal

- Tokens last **~1 year** from generation
- Set a calendar reminder for 30 days before expiry per account
- Renewal: re-run `claude setup-token` on a machine with browser → copy new token → push to both creds buckets;
  `CredsEnvPoller` on every VM picks up the new env file within 5 min. **Was silently disabled fleet-wide until
  2026-08-19** (`orchestrator.service`'s systemd unit never set `ORCHESTRATOR_CREDS_S3_BUCKET`/`_GCS_BUCKET`, so
  `_provider_and_uri()` returned `None` and the poller thread never started — the ORIGINAL 8 accounts only ever got
  their env files from `bootstrap_vm.sh`'s one-time boot fetch). Fixed live 2026-08-19 by setting
  `ORCHESTRATOR_CREDS_S3_BUCKET=uts-orchestrator-creds-427895769566` on the central orchestrator VM
  (`i-0c9b283b31d6b5ca7`) + restart; **confirmed 2026-08-22** the var is live in the actual running process's
  `/proc/<pid>/environ` (not just the config file) and the code path (`server/creds_env_poller.py::start()`)
  structurally starts the poller thread whenever that var is set — not yet independently observed catching a live
  token rotation end-to-end (no rotation has occurred since the fix to observe). Full incident:
  `plans/archive/issues/ao_creds_env_poller_disabled_no_live_token_rotation_2026_08_18.md`.
- The orchestrator dashboard's `SetupTokenBadge` shows `expires <date>` for each account; yellow at 30-day-out, red at
  7-day-out (per Phase 4c). The historic `OAuthBadge` (which read 8h-refresh `.credentials.json` expiry) was removed in
  Phase 4b-cleanup 2026-05-28 — setup-token expiry is the only auth-clock now.
- Slack / Telegram `notify_setup_token_expiring` fires at 30-day-out + crit at 7-day-out.

## Interactive spawn authentication — CLAUDE_CONFIG_DIR + onboarding seed (2.1.145+)

**Problem discovered 2026-05-22**: claude 2.1.145 added a first-run interactive onboarding wizard (theme → login method)
that **ignores `CLAUDE_CODE_OAUTH_TOKEN`** and forces browser OAuth for interactive TUI sessions (`tmux spawn`). The env
token works for `claude -p` (headless print) but the wizard blocks it for interactive sessions. This caused the entire
orchestrator fleet to hang at a browser-OAuth prompt after the CLI upgrade.

**Fix (verified live 2026-05-22)**: Give each interactive spawn an isolated, pre-seeded `CLAUDE_CONFIG_DIR`. With
onboarding marked complete, the wizard is skipped and the env token authenticates the session directly.

**Recipe (applied by `tmux_spawn._start_session()` when `env_file` is set):**

1. `CLAUDE_CONFIG_DIR=<base>/<session>` — per-session isolated config dir. Base defaults to `~/.claude-configs` (env
   `ORCHESTRATOR_CLAUDE_CONFIG_BASE`). Isolates credentials, settings, onboarding state, and session history.
2. Seed `$CLAUDE_CONFIG_DIR/.claude.json` once on first use:
   ```json
   {
     "theme": "dark",
     "hasCompletedOnboarding": true,
     "hasCompletedProjectOnboarding": true,
     "hasTrustDialogAccepted": true,
     "bypassPermissionsModeAccepted": true
   }
   ```
3. `source ~/.claude-accounts/<account_id>.env` every spawn (sets `CLAUDE_CODE_OAUTH_TOKEN`, `unset ANTHROPIC_API_KEY`).
   The token is **not persisted** to the config dir — it must be re-sourced each spawn.
4. `exec claude <flags>` → authenticated interactive session, no wizard.

**Key invariants:**

- The seed is written once per config dir (file persists). The token must be sourced every spawn (never saved).
- Multiple accounts work simultaneously in separate config dirs — account isolation is clean.
- The `CLAUDE_CONFIG_DIR` is per-session, not per-account; the same dir can be reused across accounts if desired.

**Manual verification:**

```bash
mkdir -p /tmp/ck
printf '%s' '{"theme":"dark","hasCompletedOnboarding":true,"hasCompletedProjectOnboarding":true,"hasTrustDialogAccepted":true,"bypassPermissionsModeAccepted":true}' > /tmp/ck/.claude.json
tmux new-session -d -s ck "CLAUDE_CONFIG_DIR=/tmp/ck bash -c 'source ~/.claude-accounts/sub-a-ikenna.env; cd /tmp; exec claude'"
# → skips wizard, reaches chat prompt authenticated (accept one folder-trust prompt if a new dir)
```

**Remote Control caveat**: setup tokens (`CLAUDE_CODE_OAUTH_TOKEN`) cannot be used for Remote Control sessions. RC
requires a full-scope browser-login `.credentials.json`. The headless token-auth path gives a fully functional agent
(polls `/loop`, receives messages, runs tools) without RC. RC is deferred; both auth modes coexist via separate
`CLAUDE_CONFIG_DIR`s.

## Bare mode limitation

`CLAUDE_CODE_OAUTH_TOKEN` works with `claude -p` (headless) and with interactive sessions **when the onboarding seed is
in place** (see above). It does NOT work with bare mode (`claude --bare`) or Remote Control sessions — those have their
own auth paths the operator doesn't currently use.

## Scope limitation: the token cannot read its own subscription tier (measured 2026-08-08)

**A setup-token cannot tell you which plan the account is on.** So `AccountDef.tier` in `accounts.json` is
operator-DECLARED and permanently unverifiable — a downgrade is invisible to every automated path. Do not add code that
claims to detect the tier; it has been probed and the paths are closed:

| Probe                                | Result                                                                                                                                                         |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /v1/messages` response headers | No plan/tier/limit header. `anthropic-ratelimit-unified-*` is NORMALISED 0-1 utilisation — a Pro account at 27% and a max20 account at 27% are byte-identical. |
| `GET /api/oauth/profile`             | **403** — `OAuth token does not meet scope requirement any_of(user:profile, user:office)`. `claude setup-token` does not mint those scopes.                    |
| `GET /api/claude_cli_profile`        | **403** — `OAuth authentication is currently not allowed for this endpoint.`                                                                                   |
| `GET /v1/organizations/me`           | **403** — `Authentication method not allowed for this endpoint.`                                                                                               |
| `claude /usage` TUI                  | Untested — the bars never rendered in a local probe. Unknown whether the panel names the plan.                                                                 |

**The one usable signal** is `anthropic-ratelimit-unified-upgrade-paths` (observed `upgrade_plan`): an account already
on a top tier has nothing to upgrade to, so being offered an upgrade suggests the declared tier is stale. It is a HINT
with real false-positive modes and is deliberately one-directional — see `tier_contradicted_by_upgrade_paths` in
`agent-orchestrator/server/accounts.py` for the full caveat list. It rides mostly on a **429**, which
`fetch_usage_via_api`'s `raise_for_status()` discards, so the poller reads it off the exception's response.

**Consequences for anything that touches tier:**

- Correct a tier via `POST /api/accounts/{id}/tier` (or the dashboard's tier badge, which is styled as declared-not-
  verified precisely because of this section). It writes `accounts.json` **and** the live `AccountRow` — a DB-only write
  silently reverts, because `bootstrap.sync_accounts_to_db` re-reads the file on every boot.
- Change `weekly_msg_limit` in the same edit. It is the denominator the poller uses to derive msgs-used from the API's
  percentage, so a stale limit keeps that figure wrong even once the tier badge is right.
- Regression cover: `dashboard/tests/e2e/tier-editor.spec.ts` (own backend pair; boots against a disposable copy of
  `accounts.mock.json` because the endpoint rewrites the accounts file for real) +
  `tests/test_account_tier_declared.py`.

## June 15, 2026 policy change (watch)

Per the operator-shared reference doc: starting that date, `claude -p` and Agent SDK usage on subscription plans draw
from a SEPARATE monthly Agent SDK credit bucket, distinct from the interactive 5-hour and weekly bars. This affects
automation-heavy workflows (us). Re-check rotation quota math + the orchestrator's `claude /usage` parser output after
the change rolls out, since new bars may appear in `/usage` that aren't in the current regex.

## Multi-account on Max — ToS consideration

Max is sold as a personal subscription. Running heavy automation across multiple Max accounts feeding a single workload
is a grey area. The `setup-token` mechanism itself is sanctioned by Anthropic (it's built for CI/CD use), but the
multi-account aggregation pattern is the part that could draw attention. Enforcement has historically been inconsistent.
Keep the operator aware; if Anthropic flags the pattern, the fleet may need to consolidate onto a Team or Enterprise
plan.

## Troubleshooting

| Symptom                                                   | Likely cause                                                        | Fix                                                                                                                                                                   |
| --------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `401 authentication_error` immediately                    | Token invalid or revoked                                            | Regenerate with `claude setup-token`                                                                                                                                  |
| Billing shows API usage instead of Max                    | `ANTHROPIC_API_KEY` set                                             | `unset ANTHROPIC_API_KEY`, verify with `claude /status`                                                                                                               |
| `OAuth authentication is currently not supported`         | Known intermittent CLI bug                                          | Wait + retry; verify token wasn't accidentally revoked                                                                                                                |
| All accounts hit limit simultaneously                     | Rotation logic wrong OR all accounts genuinely exhausted            | `claude /status` per account; if all show limited, wait for 5h window                                                                                                 |
| Interactive tmux spawn shows "Select login method" wizard | claude 2.1.145+ onboarding wizard ignores `CLAUDE_CODE_OAUTH_TOKEN` | Ensure `tmux_spawn._start_session()` uses `env_file=` path which seeds `CLAUDE_CONFIG_DIR`; verify `hasCompletedOnboarding:true` in `$CLAUDE_CONFIG_DIR/.claude.json` |
| New VM prompts for browser login                          | Token env var not set OR shell didn't source the env file           | `source ~/.claude-accounts/<id>.env` before running `claude`                                                                                                          |
| Token works locally but not in cron/systemd               | Env vars not inherited                                              | Source env file in cron command OR systemd `EnvironmentFile=`                                                                                                         |
| Two emails seem to share quota                            | Aliases on same orgId (not distinct subs)                           | Check `claude auth status \| grep orgId`; remove the alias from roster                                                                                                |

## Composes with

- `plans/epics/orchestrator_master.md § Auth & accounts r3` — architecture overview citing this SSOT
- `plans/epics/orchestrator_master.md § Phase 4 r3` — the migration that implements this design
- `plans/active/cross_operator_auth_failover_2026_05_29.md` — shared-pool design, spawn-heartbeat watchdog, Slack
  rotation alerts (Phase 2+3 of that plan; codified here 2026-05-29)
- `plans/active/issues/claude_credentials_rotation_in_memory_staleness_2026_05_21.md` — root-cause doc for the
  2026-05-21 cascade that motivated this SSOT
- `plans/active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md` — SUPERSEDED by this SSOT (long-lived
  tokens eliminate the file-contention problem that plan tried to solve); Phase 4b-cleanup completed 2026-05-28
- CLAUDE.md HARD RULE "Agent-orchestrator auth — setup-tokens only" — landed 2026-05-28 (Phase 4b-cleanup). Mirrors the
  contract documented here: every account in `accounts.json` MUST declare `oauth_token_env_file`; runtime spawns refuse
  accounts without one; never copy `.credentials.json` between machines.
