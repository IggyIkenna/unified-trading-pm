---
doc_type: issue
title:
  Recurring `claude /login` prompts on VM + VS Code — refresh-token rotation, shared `.credentials.json`, in-memory
  staleness
summary:
status: BLOCKED-OPERATOR
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md,
    /plans/archive/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md,
    /plans/active/master_to_live_defi_2026_05_23.md,
  ]
created: 2026-05-21
updated: 2026-05-21
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — CAPTURED — acute cascade resolved via env-var auth (agent-orch@5d78133);
> remaining legacy `harsh-primary` path tracked in `plans/epics/orchestrator_master.md` Phase 4b-cleanup + Phase 5
> (blocked on human setup-token).
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## 1. Symptoms (what the operator + agents see)

1. **VS Code Claude extension** intermittently shows a `/login` screen during chat. Operator confirmed 2026-05-21 "many
   times today". **Workaround they discovered**: close the chat tab + reopen the same chat from chat history → no login
   needed; chat resumes normally. Filed at operator's request.
2. **Slot worker (this VM, slot 3)** stuck since 2026-05-21 07:33 UTC on:
   ```
   Please run /login · API Error: 401 Invalid authentication credentials
   ```
   on every `/loop wakeup` (one per minute). Tmux pane is alive (kicker sees spinner activity) so the orchestrator's
   `WorkerLivenessKicker` keeps `slot.last_ping` refreshed → no `stale` flag fires → slot looks "working" in the
   dashboard while making zero progress.
3. **Orchestrator API `POST /api/accounts/{acct}/refresh-oauth`** returns
   `HTTP 400: {"error": "invalid_grant", "error_description": "Refresh token not found or invalid"}` for both
   `harsh-primary` and `ikenna-backup` (tested 2026-05-21 14:09 UTC).
4. **`/api/accounts` view shows `oauth_expired: true`** for both accounts even though `last_used_at` is recent — i.e.
   the orchestrator is still pulling state on the accounts but the tracked expiry timestamp is stale relative to
   whatever `.credentials.json` actually has.
5. **Recurrence cadence**: the issue has come back multiple times in a single day. Operator: "this login issue has been
   recurring and I am not able to understand this properly for a while".

## 2. Evidence (collected 2026-05-21 13:00–14:24 UTC, no token bytes inspected)

### File-mtime snapshot

```
/home/ubuntu/.claude/.credentials.json                          May 21 14:23   (live, freshly /login'd)
/home/ubuntu/.claude/.credentials.harsh-primary.json            May 21 14:11   (per-account snapshot)
/home/ubuntu/.claude/.credentials.ikenna-backup.json            May 21 14:23   (per-account snapshot)
```

Just before the most recent re-/login (~13:00):

```
/home/ubuntu/.claude/.credentials.json                          May 21 14:08
/home/ubuntu/.claude/.credentials.harsh-primary.json            May 20 19:07   ⚠️ 19h stale at that point
/home/ubuntu/.claude/.credentials.ikenna-backup.json            May 20 19:16   ⚠️ 19h stale at that point
```

### Binary state

```
/usr/bin/claude → /usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe
    binary mtime: May 21 14:04  (CLI was reinstalled/upgraded today)
/home/ubuntu/.vscode-server/extensions/anthropic.claude-code-2.1.145-linux-x64/resources/native-binary/claude
    binary mtime: May 21 10:35  (VS Code extension)
```

Both binaries are owned by their expected user. The CLI symlink target is root-owned (normal `npm install -g` output).
**Neither binary is the bug.**

### Process state

13 concurrent `claude --dangerously-skip-permissions` processes (slot workers) + 6 non-skip-perm `claude` processes (VS
Code extension + ad-hoc) all running as user `ubuntu`. Many of these were spawned hours-to-days ago and **hold an
access_token in process memory that they never reload from disk**.

### Orchestrator-side error message (verbatim)

```
OAuth refresh failed: HTTP 400: {"error": "invalid_grant",
"error_description": "Refresh token not found or invalid"}.
The refreshToken itself may be revoked.
Operator action: ssh to VM, run `claude`, type `/login`, complete browser flow,
then `cp ~/.claude/.credentials.json ~/.claude/.credentials.harsh-primary.json`.
```

`server/oauth_refresh.py` emits this when Anthropic's token endpoint rejects the stored `refreshToken`. The message
itself is the operator-side recovery instruction.

## 3. Why the sudo-install hypothesis is **NOT** the cause

Operator hypothesis (2026-05-21 14:08): "the claude was installed using sudo so can that be the reason of this?". Ruled
out with this evidence:

| Concern                                          | Reality                                                                                                                                                                                                                           |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Binary owned by root → can't write config        | The binary doesn't write to its own dir. It writes to `$HOME/.claude/`. Owner of that directory and its contents is `ubuntu` (the invoking user). `ls -la ~/.claude/` confirms.                                                   |
| Different effective UID at runtime               | The running `claude` process for slot 3 is `ubuntu 1155484 ... claude --dangerously-skip-permissions ...` — UID matches the credential owner.                                                                                     |
| HOME env mismatch                                | Slot tmux sessions are started with `HOME=/home/ubuntu`. Verified via `/proc/<pid>/environ` for live worker processes.                                                                                                            |
| sudo-installed binary uses different config path | Both binaries (`/usr/lib/.../claude.exe` and the VS Code extension's bundled binary at `~/.vscode-server/.../native-binary/claude`) read/write the same `~/.claude/.credentials.json`. The path is hardcoded relative to `$HOME`. |

The sudo install is **conventional and correct** for an npm global package on a multi-user system. The fact that
re-/login + chat-reopen recovers immediately is itself proof that ownership/path are fine — if those were broken, no
auth flow would persist anywhere.

## 4. Actual root cause — three interlocking mechanisms

### 4a. OAuth refresh-token rotation

Anthropic's OAuth server **rotates the refresh_token on every successful refresh**. After a refresh call returns, the
old refresh_token is no longer valid; only the newly-returned one is. Standard practice for high-security OAuth. The
`oauth_refresh.py` module writes the rotated token back to whichever `.credentials*` file it just read:

```python
# server/oauth_refresh.py
creds["claudeAiOauth"]["refreshToken"] = data.get("refresh_token", refresh_token)
```

So per-file, the rotation is handled. The issue is **multi-file divergence**.

### 4b. Shared `.credentials.json` across many consumers

The system has multiple agents that all read from the same file:

| Consumer                                 | When it reads                                                                                                                    | When it refreshes                                                                                                       |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Slot worker N (long-running tmux Claude) | Once at spawn (loaded into process memory). Reads ~/.claude/.credentials.json or the per-account snapshot the spawn copied from. | When CLI internally hits a 401 → tries refresh against Anthropic; on success writes a new token to `.credentials.json`. |
| VS Code Claude extension                 | Once per chat tab (loaded into extension memory). Reads ~/.claude/.credentials.json.                                             | Same — when it hits 401, internal refresh, writes back.                                                                 |
| Orchestrator `usage_poller`              | Every 30 minutes. Reads per-account `.credentials.<id>.json`.                                                                    | Calls `oauth_refresh.refresh()` if expiry < 1h away; writes back to the per-account file.                               |
| `swap_claude_account.sh`                 | At swap time (operator-triggered). Reads the per-account file.                                                                   | Doesn't refresh; just `cp`s the snapshot to `.credentials.json` so the next spawn picks it up.                          |

When ANY of these refreshes, the rotation invalidates whatever the OTHERS still hold in memory. Specifically:

- Consumer A holds `refresh_token_v1` in memory; `.credentials.json` on disk has `refresh_token_v1`.
- Consumer B (a different process) hits 401, calls refresh, gets `refresh_token_v2`, writes it to `.credentials.json`.
  Server-side, `_v1` is now revoked.
- Consumer A doesn't know — its in-memory `_v1` is now a dead token.
- Consumer A later hits 401, tries to refresh with `_v1` → "Refresh token not found or invalid". The CLI's fallback for
  that case is to show the `/login` screen.

### 4c. In-memory staleness in long-running consumers

The VS Code extension and the slot tmux Claude Code sessions are **long-running**. They don't poll the filesystem for
credential updates. They read `.credentials.json` once at start, keep the token in memory, and only attempt a refresh
against Anthropic's server (not against the local file).

**This is why the operator's workaround works**: closing the VS Code chat tab + reopening it from history forces the
extension to **re-instantiate the session**, which re-reads `.credentials.json` from disk. If the file was updated by
another consumer in the interim (very likely on this VM with 13+ concurrent processes), the reopened chat picks up the
latest token. No `/login` needed.

The slot tmux sessions don't have an equivalent "reopen from history" path — their only equivalent is a respawn (kill
the tmux session + new spawn copying the latest credentials snapshot). That's why slot 3 was stuck while VS Code chats
kept recovering.

### 4d. Per-account snapshot drift

`swap_claude_account.sh` reads from `~/.claude/.credentials.<account_id>.json` (a per-account snapshot) and copies it to
`~/.claude/.credentials.json` to switch active credentials. The snapshots are static — created by an operator-triggered
`cp ~/.claude/.credentials.json ~/.claude/.credentials.<id>.json` after a successful `/login` for that account. Once
written, **nothing automatically syncs the rotated token back to the per- account file**.

So after a day of rotations on `.credentials.json`, the per-account files are stale by N rotations. When the
orchestrator's `usage_poller` reads the per-account file, it finds an ancient refresh_token. When it tries to refresh
against Anthropic, the server says "invalid_grant" — that token was rotated out N rotations ago.

The error message in `oauth_refresh.py` literally tells the operator to manually re-sync:

```
Operator action: ... `cp ~/.claude/.credentials.json ~/.claude/.credentials.harsh-primary.json`.
```

But that's a manual step that has to happen after every `/login`. Realistically, nobody remembers to do this EVERY time,
so the snapshots drift, the orchestrator-side refresh fails, the per-account files become useless, and any new slot
spawn relying on them gets dead credentials from the start.

## 5. Known workaround (file this prominently, operator-discovered 2026-05-21)

**For the VS Code Claude extension**: if you see the `/login` screen mid-chat, **close the chat tab and reopen the same
chat from chat history**. The reopened chat re-reads `~/.claude/.credentials.json` from disk and continues without
re-auth, ASSUMING some other consumer on the VM has refreshed the credentials more recently than your stale in-memory
copy.

If no other consumer has refreshed recently, this workaround does nothing. In that case `/login` is the only path.

**For a stuck slot worker** (tmux Claude session hitting 401): no equivalent "reopen from history" exists. Recovery
requires `/api/slots/{N}/reassign?kill_worker=true` → `+ Spawn worker` from the dashboard. The spawn flow runs
`swap_claude_account.sh` which copies the latest credentials snapshot.

## 6. Affected consumers on this VM (2026-05-21 14:24 snapshot)

- ~13 slot workers running `claude --dangerously-skip-permissions ...` (some pre-cutover, some post)
- ~6 ad-hoc `claude` processes (VS Code extension chats, manual sessions)
- 1 orchestrator `usage_poller` (server-side, polls per-account snapshots every 30 min)
- 1 `oauth_refresh.refresh()` path triggered by HTTP 401 on `/api/accounts/{id}/refresh-oauth`

Total: **~20 concurrent consumers sharing one `~/.claude/.credentials.json` file with no cross-consumer coordination on
rotation**. This is the design issue.

## 7. Why it's gotten worse recently

Three factors compounded today (2026-05-21):

1. **CLI was reinstalled at 14:04 UTC**. New binary may have a more aggressive refresh check OR an updated client_id
   (the `oauth_refresh.py` notes `_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"` was "discovered 2026-05-21 by
   inspecting strings(claude-code-linux-x64/claude)" — i.e. someone re-extracted the client_id today, suggesting it
   might have changed in a recent update). If the client_id rotated, server-side refresh_tokens issued under the old
   client_id would be invalidated en masse.
2. **Per-account snapshots were 19 hours stale by morning** (`.credentials.harsh-primary.json` at May 20 19:07; we
   observed it at May 21 14:00). Plenty of opportunity for rotation drift to accumulate.
3. **Cutover-day high spawn rate** — many slots being spawned + respawned today, each calling `swap_claude_account.sh`
   which reads a stale per-account snapshot and writes it as `.credentials.json`, which then gets refreshed by Consumer
   X, which invalidates the snapshot's refresh_token (which is then re-written-back as new `.credentials.json` — but the
   snapshot remains stale). Cascade.

## 8. Immediate recovery (operator-side, manual)

Until the structural fix lands, the recovery dance is:

```bash
# 1. /login interactively, complete the browser flow.
ssh ubuntu@<VM>
claude
# (in claude:)  /login
# (complete browser auth; produces fresh ~/.claude/.credentials.json)

# 2. Sync the freshly-/login'd credentials to BOTH per-account snapshots.
cp ~/.claude/.credentials.json ~/.claude/.credentials.harsh-primary.json
cp ~/.claude/.credentials.json ~/.claude/.credentials.ikenna-backup.json
# (or just to the account whose login flow you completed — depends on which account you authed as)

# 3. Respawn any slot workers that hit 401 (their in-memory token is dead).
# Dashboard → Fleet panel → click + Spawn worker on the dead slot, or:
curl -X POST $ORCH/api/slots/N/reassign \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"kill_worker": true}'
# then re-spawn from the dashboard.

# 4. Confirm refresh works:
curl -X POST $ORCH/api/accounts/harsh-primary/refresh-oauth \
    -H "Authorization: Bearer $TOKEN"
# should return oauth_expired: false + a future oauth_expires_at.
```

## 9. Proposed structural fixes (for the agent who picks this up)

Ranked by leverage:

### 9a. Sync rotated tokens back to per-account snapshots automatically (HIGH leverage, LOW effort)

In `server/oauth_refresh.py`, after `_persist_refreshed_credentials()` writes the new token to whichever file was read,
**also write to the per-account snapshot** if the file being refreshed IS the per-account snapshot. Concretely: if
`refresh()` is called with `account_id="harsh-primary"`, it should read `~/.claude/.credentials.harsh-primary.json`, get
the new token, AND write the new credentials block back to both `.credentials.harsh-primary.json` (the snapshot) AND
`.credentials.json` (the live file used by new spawns) — atomically, so they never diverge.

This eliminates 4d. The orchestrator-side `usage_poller` becomes the authoritative refresher for the per-account files,
and the snapshots stay fresh.

### 9b. Reverse-sync from `.credentials.json` to all per-account snapshots on detected refresh (MEDIUM)

Add an inotify-or-poller watcher on `~/.claude/.credentials.json`. When the live file changes (because the CLI
internally refreshed), find which per-account snapshot was most-recently the source (via `swap_claude_account.sh`
recording the active account in a sidecar file like `~/.claude/.active_account`) and copy the new `.credentials.json`
content back to that account's snapshot.

This solves the bidirectional drift: any consumer's refresh updates both the live file AND its account's snapshot.

### 9c. Per-spawn HOME-shim isolation (HIGH effort, ALREADY PLANNED)

Each slot worker gets its own isolated `$HOME/.claude/` with its own `.credentials.json`. Rotation in slot A's
credentials doesn't affect slot B. Per-account snapshots become unnecessary because each slot owns its credentials
end-to-end. See `plans/active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md` — this was already on the
docket; this issue is one more reason to prioritise.

### 9d. Trigger a "reopen from history" on the VS Code extension side (LOW leverage, complex)

Currently the VS Code extension forces `/login` when its in-memory access_token returns 401, even if `.credentials.json`
on disk has a fresher token. If the extension re-read the file on 401 instead of immediately /login-prompting, the
operator wouldn't need the close+reopen workaround. This is upstream fix territory (file with Anthropic if it's a
CLI/extension bug).

### 9e. GCS-backed credentials backplane for cross-VM rotation coordination (HIGH leverage, MEDIUM effort) — **multi-VM solution**

> **r3 supersedence note (2026-05-21 ~16:00 UTC)**: the operator shared a reference doc (Claude CLI Multi-Account
> Headless Authentication Guide) confirming that `claude setup-token` produces a **1-year long-lived OAuth token** that
> is account-scoped, multi-machine-safe, and does NOT participate in the refresh-token-rotation chain that motivated
> this issue. Under the long-lived-token architecture (plans/epics/orchestrator_master.md § Auth & accounts r3 + Phase 4
> r3), the cross-VM rotation race §9e was solving no longer exists. The GCS-backed distribution mechanism is still
> useful — it becomes "GCS as SSOT for the operator's `setup-token` outputs" (env files instead of `.credentials.json`)
> — but the elected-refresher complexity becomes a no-op since the tokens don't rotate. Keep §9e shipped; refactor the
> payload from `.json` to env file in Phase 4b. The §9a-9d local-snapshot-drift fixes also become moot once we stop
> using `.credentials.json` per-account snapshots entirely.

> **Added 2026-05-21 r2 by Harsh** (`harsh@odum-research.com`): "the thing about using the same account across different
> vms is a classic problem that i used to face when using same trading account from multiple pc. so the auth token gets
> refreshed everytime we login. so if other vms are using the old token they will receive the 401 error and once we
> login there, other vms will face that. so we login from our local machine and then upload it to gcs and then we update
> the token to vms via backend. we will create a new api for that and then it can be sorted. we need a human anyway to
> login for now. and that way account rotation will be just fetch login token from gcs and update it on the vm
> credentials.json file. only caveat is whenever we login we have to make sure we update the gcs with fresh token."

This is the cross-VM extension of 9a. Sections 9a-9d fix WITHIN-VM token drift. But once we move to the v0.7 multi-VM
topology (1 planning VM + 8 epic VMs sharing 4 OAuth accounts via primary-with- 3-failovers per VM), the SAME
refresh-token-rotation problem manifests CROSS-VM: VM-A refreshes, VM-B's stored refresh_token for the same account is
now invalid.

**Architecture**:

1. **GCS bucket per env** (e.g. `gs://agent-orchestrator-creds-prd/`) is the SSOT for every account's creds. Path:
   `accounts/<account_id>.json` (KMS-encrypted with the same key as v0.7 § Persistence).
2. **Operator login flow** (one-time per account, ever):
   - Operator runs `claude setup-token` (or `claude /login`) on their LOCAL machine (only laptop has browser).
   - Resulting `~/.claude/.credentials.json` is uploaded to GCS at `accounts/<account_id>.json` via a new endpoint or
     `gsutil cp`.
3. **VM pull-on-spawn + scheduled poll**:
   - Every VM has a `creds_sync` daemon polling GCS every 5 min for any changed account file (etag-aware; only pulls on
     change).
   - On change, write to `~/.claude/.credentials.<account_id>.json` + atomically swap if `<account_id>` matches the
     currently-active account.
4. **Rotation coordination**:
   - Only ONE refresher per account at a time (elected via GCS object-lease lock at `accounts/<account_id>.lock`). The
     lease holder runs the auto-refresh; everyone else just pulls.
   - On refresh success, lease holder uploads new creds to GCS (CAS via etag) → other VMs detect change on next poll →
     write to local.
   - If lease holder dies, lease times out (~10 min) and another VM acquires it.
5. **New backend API**: `POST /api/accounts/{account_id}/sync-from-gcs` — manual trigger for any VM to force a fresh
   pull (used when 9a/9b's local detection mechanisms aren't fast enough).
6. **VM-launch bootstrap**: every newly-provisioned VM pulls all 4 account files from GCS on first boot (per v0.7 § VM
   provisioning Phase 9). No per-VM `claude /login` needed ever again.

**Single elected refresher per account, not per VM** matters: if all VMs try to refresh independently, they race and
rotate each other's refresh_tokens into uselessness. The lease ensures one refresh per cycle.

**Caveats** (per Harsh): "whenever we login we have to make sure we update the gcs with fresh token." Operator login →
upload to GCS is the operator's manual step until automated. A small local helper script
(`scripts/orchestrator/push_creds_to_gcs.sh <account_id>`) reduces this to one command after each `claude /login` cycle.

**Composes with**:

- 9a + 9b (local sync within a VM) — needed regardless of GCS backplane; 9e is the cross-VM coordination layer on top.
- 9c (per-spawn HOME-shim) — orthogonal but adds complexity. 9e + 9a alone may obsolete 9c if the orchestrator owns
  refresh + sync, and slot workers just read the latest token on each refresh. Decide per migration.
- v0.7 plan § "Persistence" (Phase 8): same GCS bucket pattern; creds add as another artefact.
- v0.7 plan § "Auth & accounts" (Phase 4): the lowest-pct-first failover algorithm now reads candidate accounts' state
  from GCS, not from per-VM stale snapshots.

**Verification (extends § 11)**:

- [ ] Operator runs `claude /login` for account X on their laptop ONCE; the credentials propagate to ALL VMs within 5
      min without per-VM intervention.
- [ ] On a VM, `swap_claude_account.sh` to a previously-untouched account on this VM works immediately (creds are
      present, pulled from GCS during the last sync tick).
- [ ] When VM-A's elected refresher rotates account X's tokens, VM-B observes the new tokens within 5 min + does NOT 401
      on its next claude spawn.
- [ ] If the elected refresher VM (VM-A) is killed, another VM acquires the lease within 10 min and resumes rotation for
      account X.

## 10. Open questions for the agent picking this up

1. **Did the CLI's `_CLIENT_ID` actually rotate in today's update?** If yes, refresh_tokens issued under the old
   client_id are dead and only `/login` recovers. If no, the issue is purely rotation drift + in-memory staleness and
   the structural fix in 9a should suffice. Check the `_CLIENT_ID` value in `server/oauth_refresh.py` against what
   `strings $(realpath $(which claude))` returns today vs. what's in this VM's `/home/ubuntu/.claude/backups/` if any
   binary backup exists.
2. **Does the VS Code extension's bundled binary use the SAME `_CLIENT_ID` as the CLI?** If different, refreshes by one
   don't affect the other's tokens. Check via `strings` on
   `~/.vscode-server/extensions/anthropic.claude-code-2.1.145-linux-x64/resources/native-binary/claude`.
3. **Are slot workers using stored access_tokens directly, or going through the CLI's auth-refresh path?** If the CLI
   handles refresh internally on every API call, the issue is narrower than 4c suggests.
4. **What's the actual TTL on access_tokens vs. refresh_tokens?** Per oauth_refresh.py comments, "Access tokens have ~8h
   TTL". Refresh_tokens TTL unknown — if they have a hard expiry independent of rotation, that's another failure mode to
   consider.

## 11. Verification criteria when the structural fix lands

- [ ] An operator can run `/login` once, walk away for 24h, and the orchestrator + all slot spawns continue working
      without further /login prompts.
- [ ] `POST /api/accounts/{harsh-primary,ikenna-backup}/refresh-oauth` returns `oauth_expired: false` 24h after the
      most-recent /login, without operator `cp` intervention.
- [ ] `~/.claude/.credentials.<account_id>.json` mtime stays within 30 minutes of `~/.claude/.credentials.json` mtime
      indefinitely (verified via cron-checked metric).
- [ ] Slot worker hitting an internal 401 recovers without `/login` (extension/CLI re-reads file). OR if upstream-bug,
      document the operator workaround prominently in `agents/RULES.md` § 4.
- [ ] VS Code chat that hits /login can be recovered by the close+reopen workaround in 100% of cases where
      `.credentials.json` was updated within the prior hour (or document the limitation).

## 13. Status update — 2026-05-22 (orchestrator Phase 4a-4c shipped)

**Orchestrator epic Phase 4a + 4b + 4c are DONE** (per `plans/epics/orchestrator_master.md`):

- Phase 4a: Spawn path migrated to env-var auth (`oauth_token_env_file` + `tmux_spawn.py`) — agents now use
  `CLAUDE_CODE_OAUTH_TOKEN` from env files instead of `.credentials.json` swaps. No more rotation races for sub-a /
  sub-b / iggy2london accounts.
- Phase 4b: r3 env-file routing live — `sub-a-ikenna`, `sub-b-iggy2london` on long-lived `setup-token` tokens. Legacy
  `.credentials.json` path retained for `harsh-primary` only (pending Harsh running `claude setup-token`).
- Phase 4c: `SetupTokenBadge` in dashboard — 1-year expiry warn/crit/expired levels; all 3 r3 accounts seeded to
  2027-05-21.

**Still open**:

- Phase 4b-cleanup (PENDING): remove legacy swap/refresh code once `harsh-primary` migrates to setup-token. Blocked on
  Harsh running `claude setup-token` for `harsh.kantariya00787@gmail.com`.
- Phase 5: GCS distribution + account roster expansion (Harsh setup-token needed).

**This issue doc** remains active until Phase 4b-cleanup lands (harsh-primary on setup-token). The acute rotation/401
cascade described in §§1-7 is largely resolved for Ikenna accounts; `harsh-primary` is the last legacy path.

**Tracking**: `plans/epics/orchestrator_master.md` Phase 4b-cleanup + Phase 5 are the authoritative tracking items.

## 12. Audit-trail breadcrumbs (so next agent can reproduce)

- This doc was written by `agt-5566ea` (main agent on `ip-172-31-5-118`, registered 2026-05-21 13:16 UTC).
- The slot 3 401 was first observed at 07:33 UTC and was still failing at 14:09 when this doc started.
- BLK-5b419250 (slot 3 escalation about PH-2-B3-SLOT-3) was auto-answered by this main agent at 13:19:58 UTC; the
  auto-answer was correct but moot because slot 3 can't actually act on it without fresh credentials.
- The cutover plan-of-record (`data_pipeline_master_coordination_2026_05_20.md`) does not currently call out an
  auth-hardening prerequisite; consider adding one to its Phase 0 audits.
- Per-account snapshot mtimes at boot (this VM, 13:00 UTC): harsh-primary May 20 19:07 (19h stale), ikenna-backup May 20
  19:16 (19h stale). After operator /login + cp at ~14:11 + 14:23: harsh-primary 14:11, ikenna-backup 14:23, live 14:23.
  State as of doc-finalisation: in-sync.
