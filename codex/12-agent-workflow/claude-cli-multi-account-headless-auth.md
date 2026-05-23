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

**tmux_spawn.py** (`_ensure_claude_config_dir()` + `_ONBOARDING_SEED`):

- Derives `CLAUDE_CONFIG_DIR=<base>/<session>` where base = `ORCHESTRATOR_CLAUDE_CONFIG_BASE` env (default
  `~/.claude-configs`).
- Creates the dir and writes `.claude.json` from `_ONBOARDING_SEED` on first call per session.
- Both `spawn()` (worker path) and `spawn_named()` (main/review/backup agent path) accept `env_file: str | None`.
- Commits: workers `1717768` (2026-05-22), main/review/backup agents `76c966e` (2026-05-23).

**server.py** (`spawn_agent_endpoint`):

- `SpawnAgentRequest.account_id: str | None` — new field (2026-05-23).
- When set, resolves `oauth_token_env_file` from `data/config/accounts.json` via `load_accounts()` and passes it as
  `env_file` to `spawn_named()`.
- Pattern mirrors the worker spawn path at `~line 1808` (`tmux_spawn.spawn(env_file=…)`).

### Quick verification recipe

```bash
# Prove setup token works headless (no seed needed):
set -a; . ~/.claude-accounts/harsh-primary.env; set +a
claude -p 'reply AUTH_OK'   # → AUTH_OK

# Prove the interactive headless recipe (with seed):
mkdir -p /tmp/ck && printf '%s' \
  '{"theme":"dark","hasCompletedOnboarding":true,"hasCompletedProjectOnboarding":true,"hasTrustDialogAccepted":true,"bypassPermissionsModeAccepted":true}' \
  > /tmp/ck/.claude.json
tmux new-session -d -s ck "CLAUDE_CONFIG_DIR=/tmp/ck bash -c 'source ~/.claude-accounts/harsh-primary.env; cd /tmp; exec claude'"
# → skips wizard, reaches chat prompt authenticated (accept one folder-trust prompt with Enter)

# Prove the orchestrator spawn path:
python3 -c "from server import tmux_spawn; print(tmux_spawn.spawn(slot_id=99, boot_prompt='reply SPAWN_WORKS', cwd='/tmp', env_file='$HOME/.claude-accounts/harsh-primary.env'))"
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
└── sub-c-harsh.env                  # chmod 600
```

Each env file:

```bash
# ~/.claude-accounts/sub-a-ikenna.env
unset ANTHROPIC_API_KEY              # required — overrides token if set, flips to metered billing
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
export CLAUDE_ACCOUNT_LABEL=sub-a-ikenna   # for orchestrator logging + dashboard
```

The `unset` line is non-negotiable. Treat it as part of the env-file contract.

## Switching accounts manually

```bash
source ~/.claude-accounts/sub-a-ikenna.env
claude /status   # confirms which account is active
```

For orchestrator-driven switching: the spawn endpoint sources the matching env file before `exec claude` (per
`plans/epics/orchestrator_master.md` Phase 4a). Operator never switches manually in steady state.

## Rotation across accounts (on rate-limit hit)

The orchestrator detects 5h / weekly / Sonnet quota exhaustion on the current account → picks the next available account
(lowest-pct-first across the VM's distinct-subscription roster) → NEW SPAWNS use the new env var. In-memory tokens of
already-running workers are NOT swapped mid-session (claude CLI doesn't re-read env mid-session); the rotation only
affects subsequent spawns. Live workers continue on their existing token until they hit the rate limit themselves (at
which point they /done and the next spawn picks up the new account).

## Multi-machine

The same token can be deployed across N machines simultaneously. **They all share that account's quota** — adding 2 VMs
with the same token doesn't multiply throughput; the 5h / weekly bars are per-account, not per-machine. Throughput
multiplication comes from having N DISTINCT subscriptions, each with its own token, distributed across the VMs.

Distribution: operator uploads the env files to GCS (via `unified-trading-pm/scripts/orchestrator/push_creds_to_gcs.sh`
after refactor in Phase 4b); every VM pulls via the `GCSCredsPoller` daemon (5-min poll) into its local
`~/.claude-accounts/`.

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
- Renewal: re-run `claude setup-token` on a machine with browser → copy new token → `push_creds_to_gcs.sh` propagates to
  all VMs within 5 min
- The orchestrator dashboard's `OAuthBadge` shows `expires <date>` for each account; yellow at 30-day-out, red at
  7-day-out (per Phase 4c)
- Telegram `notify_oauth_token_expiring` fires at 30-day-out + crit at 7-day-out

## Bare mode limitation

`CLAUDE_CODE_OAUTH_TOKEN` works with `claude` and `claude -p`. It does NOT work with bare mode (`claude --bare`) or
Remote Control sessions — those have their own auth paths the operator doesn't currently use.

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

| Symptom                                           | Likely cause                                              | Fix                                                                   |
| ------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------- |
| `401 authentication_error` immediately            | Token invalid or revoked                                  | Regenerate with `claude setup-token`                                  |
| Billing shows API usage instead of Max            | `ANTHROPIC_API_KEY` set                                   | `unset ANTHROPIC_API_KEY`, verify with `claude /status`               |
| `OAuth authentication is currently not supported` | Known intermittent CLI bug                                | Wait + retry; verify token wasn't accidentally revoked                |
| All accounts hit limit simultaneously             | Rotation logic wrong OR all accounts genuinely exhausted  | `claude /status` per account; if all show limited, wait for 5h window |
| New VM prompts for browser login                  | Token env var not set OR shell didn't source the env file | `source ~/.claude-accounts/<id>.env` before running `claude`          |
| Token works locally but not in cron/systemd       | Env vars not inherited                                    | Source env file in cron command OR systemd `EnvironmentFile=`         |
| Two emails seem to share quota                    | Aliases on same orgId (not distinct subs)                 | Check `claude auth status                                             | grep orgId`; remove the alias from roster |

## Composes with

- `plans/epics/orchestrator_master.md § Auth & accounts r3` — architecture overview citing this SSOT
- `plans/epics/orchestrator_master.md § Phase 4 r3` — the migration that implements this design
- `plans/active/issues/claude_credentials_rotation_in_memory_staleness_2026_05_21.md` — root-cause doc for the
  2026-05-21 cascade that motivated this SSOT
- `plans/active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md` — SUPERSEDED by this SSOT (long-lived
  tokens eliminate the file-contention problem that plan tried to solve)
- `unified-trading-pm/scripts/orchestrator/push_creds_to_gcs.sh` — operator helper for laptop-to-GCS distribution (will
  be refactored Phase 4b to ship env-file payloads)
- CLAUDE.md HARD RULE (to add Phase 4b): "Claude auth on VMs uses long-lived `setup-token` via `CLAUDE_CODE_OAUTH_TOKEN`
  env var. Do NOT copy `.credentials.json` between machines."
