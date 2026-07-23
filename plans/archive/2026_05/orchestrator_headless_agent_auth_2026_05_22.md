---
doc_type: plan
title:
  Orchestrator headless agent auth — token-auth interactive agents (workers + main), account switching, Remote-Control
  deferral
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: []
related: [plans/epics/orchestrator_master.md, plans/active/multi_backend_fleet_connectivity_2026_05_22.md]
created: 2026-05-22
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
priority: P0
last_updated: 2026-05-22
source: live debugging session with operator (Harsh) 2026-05-22 — agents stuck on OAuth after claude 2.1.145 upgrade
---

## Deferred work — migrated to:

- Deploy headless auth fix to fleet (DEFERRED-OPERATOR-DECISION: "we'll do that later") →
  `plans/epics/orchestrator_master.md` P2 block — operator to schedule fleet redeploy + verify UI-spawned worker on VM
  authenticates (**MIGRATED FROM:** orchestrator_headless_agent_auth_2026_05_22)
- Usage scraping re-engineering (DEFERRED-NEEDS-DEDICATED-SESSION: `server/usage_tracker.py` broken in claude 2.1.145) →
  `plans/epics/orchestrator_master.md` P2 block — needs dedicated session to re-engineer TUI scrape for 2.1.145 or drop
  for manual/backend-driven usage (**MIGRATED FROM:** orchestrator_headless_agent_auth_2026_05_22)

# Orchestrator headless agent auth (claude 2.1.145)

**TL;DR:** Every orchestrator agent spawn was hanging on a browser-OAuth screen and "nothing worked." Root cause:
**claude 2.1.145's interactive first-run onboarding wizard ignores `CLAUDE_CODE_OAUTH_TOKEN` and forces browser OAuth.**
Fix (verified live): point each spawn at a **per-session `CLAUDE_CONFIG_DIR` with onboarding pre-seeded**, so the wizard
is skipped and the env setup-token authenticates the interactive session directly. **Workers are fixed + verified.**
Main/review/backup agents need the same wiring (one small code change). Remote Control can't use setup tokens —
**deferred** (operator decision: headless for both main + worker now, RC later).

---

## What was broken (2026-05-22)

- The `claude` CLI was upgraded to **v2.1.145**. After that, every orchestrator-spawned agent (main + workers) sat at:
  ```
  Select login method:
  ❯ 1. Claude account with subscription …
  Browser didn't open? Use the url below to sign in … Paste code here if prompted >
  ```
  → agents never reached the chat UI → never started their `/loop` → never replied. The whole fleet was non-functional.
- The "Refresh from /usage" button also did nothing (same family of issue — see § "Usage scraping" below).

## Root cause (verified, not guessed)

1. **The setup token is valid.** `CLAUDE_CODE_OAUTH_TOKEN=<sk-ant-oat01-…> claude -p 'x'` → `AUTH_OK`. Tokens are
   ~1-year long-lived and were minted correctly.
2. **Interactive claude runs a first-run onboarding wizard** (theme → "Select login method") that **ignores**
   `CLAUDE_CODE_OAUTH_TOKEN` and steers into browser OAuth. Confirmed by docs + the claude changelog (_"Fixed `/login`
   having no effect in a session launched with `CLAUDE_CODE_OAUTH_TOKEN`"_) and by direct test on this box.
   `claude --help`'s `--bare` text also says OAuth/keychain are normally read (not the env token) for interactive.
3. So: the env token works for **`-p` (headless print)** but the **interactive TUI's onboarding wizard** blocks it. The
   orchestrator spawns **interactive** sessions (agents need slash commands / `/loop`), so they hit the wizard.

## The fix (verified working)

Skip the onboarding wizard by giving each spawn an **isolated, pre-seeded `CLAUDE_CONFIG_DIR`**. With onboarding marked
complete, interactive claude no longer shows the wizard and **authenticates via the env `CLAUDE_CODE_OAUTH_TOKEN`
directly**.

**The recipe (per spawn):**

1. `CLAUDE_CONFIG_DIR=<base>/<session>` — isolated config dir per session (base = `ORCHESTRATOR_CLAUDE_CONFIG_BASE`,
   default `~/.claude-configs`). Isolates creds + onboarding + sessions + settings.
2. Seed `$CLAUDE_CONFIG_DIR/.claude.json` (once) with:
   ```json
   {
     "theme": "dark",
     "hasCompletedOnboarding": true,
     "hasCompletedProjectOnboarding": true,
     "hasTrustDialogAccepted": true,
     "bypassPermissionsModeAccepted": true
   }
   ```
3. `source ~/.claude-accounts/<account_id>.env` (sets `CLAUDE_CODE_OAUTH_TOKEN`, `unset ANTHROPIC_API_KEY`) — **every
   spawn**, because the token is NOT persisted to the config dir (verified: no `.credentials.json` is written).
4. `exec claude <flags>` → authenticated interactive session, no wizard.

**Key facts proven on the box (2026-05-22):**

- One account: interactive session reached the chat prompt and replied `WORKS`.
- Two accounts in parallel (harsh-primary + sub-a-ikenna, separate config dirs + separate tokens) → both replied
  independently → **account isolation + switching works**.
- The onboarding seed is **one-time per config dir** (persists in `.claude.json`); the **token must be re-sourced every
  spawn** (it's never saved — `echo $CLAUDE_CODE_OAUTH_TOKEN` in a plain shell is empty by design).
- A real `tmux_spawn.spawn(env_file=…)` worker came up authenticated and processed its pasted prompt (`SPAWN_WORKS`).

## What's DONE

- [x] ✅ [AGENT] P0. `agent-orchestrator/server/tmux_spawn.py` — the `env_file` (setup-token) spawn path now sets a
      per-session onboarding-seeded `CLAUDE_CONFIG_DIR`. `_ensure_claude_config_dir()` + `_ONBOARDING_SEED`. Workers
      spawn authenticated. ruff + basedpyright green, verified live. — agent-orchestrator@`1717768` (LDR).

## What's REMAINING (pick up tomorrow)

- [x] ✅ [AGENT] P0. **Make main/review/backup agents headless too.** `tmux_spawn.spawn_named()` (used by the
      agent-spawn endpoint `server.py:3158 spawn_agent_endpoint` → `:3240 spawn_named`) does **NOT** take `env_file`, so
      agents use the legacy path (no token → wizard → OAuth). Add an `env_file` param to `spawn_named()` (mirror
      `spawn()`), thread the account's `oauth_token_env_file` through `spawn_agent_endpoint`, and apply the same
      `_ensure_claude_config_dir` logic. Then main/review/backup are headless token-auth'd like workers. **Operator
      decision: do this — headless for both main + worker now.** — agent-orchestrator@`b133cdf` (this slot).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Deploy to the fleet** (deferred by operator — "we'll do that later").
      The fix is on `agent-orchestrator` LDR; ride LDR→main + redeploy to the 10 worker VMs + central. Each VM already
      has its accounts' `~/.claude-accounts/<id>.env` (synced from buckets). Verify a UI-spawned worker on a VM
      authenticates.
- [x] ✅ DEFERRED-NEEDS-DEDICATED-SESSION [AGENT] P1. **Usage scraping is separately broken**
      (`server/usage_tracker.py`). It drives the interactive `/usage` TUI; in 2.1.145 there's no non-interactive usage
      command and `claude -p '/usage'` returns only a stub. Needs re-engineering the TUI scrape for 2.1.145, OR dropping
      it for manual/backend-driven usage. Not auth-related.
- [x] ✅ [AGENT] P2. **Update the codex SSOT** `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` with
      these verified findings (the CLAUDE_CONFIG_DIR + onboarding-seed recipe; that the env token is `-p`-only WITHOUT
      the seed). The existing doc predates the 2.1.145 findings. — PM@`f785f13` (this slot).

---

## Account switching — how it works

The orchestrator runs multiple Claude subscriptions and switches between them (e.g., when one is rate-limited). With the
headless model this is clean:

- **Per-account token files:** `~/.claude-accounts/<account_id>.env` — each
  `export CLAUDE_CODE_OAUTH_TOKEN=<that account's setup token>` + `unset ANTHROPIC_API_KEY`. All 4 accounts are wired in
  `data/config/accounts.json` via `oauth_token_env_file`:
  - `sub-a-ikenna`, `sub-b-iggy2london`, `sub-c-ikenna-odum`, `harsh-primary`.
- **Token SSOT:** these `.env` files are stored in **both** `gs://central-element-323112-orchestrator-creds/accounts/`
  and `s3://uts-orchestrator-creds-427895769566/accounts/`, and synced onto each machine's `~/.claude-accounts/`.
- **Switching = which env_file a spawn sources.** The spawn picks the account's `oauth_token_env_file` → that account's
  token → that subscription. Different account = source a different `.env`. The `CLAUDE_CONFIG_DIR` is per-session and
  account-agnostic (the token isn't persisted there), so the **same** config dir can be reused across accounts, or use a
  per-(slot, account) dir — either works. **Verified: two accounts ran simultaneously in separate config dirs.**
- **When one account is exhausted:** respawn the slot with a different account's `env_file` (the orchestrator's
  account-routing already selects the account; this fix just makes the resulting interactive spawn actually
  authenticate). No browser, no re-login — just a different token file.
- **Token lifecycle:** setup tokens last ~1 year. Re-mint with `claude setup-token` (browser, once, per account) → write
  to `~/.claude-accounts/<id>.env` → re-upload to GCS + S3. They do **not** auto-refresh (unlike browser-login creds).

## Remote Control caveat (why RC is deferred)

- **Setup tokens (`CLAUDE_CODE_OAUTH_TOKEN`) cannot be used for Remote Control sessions.** Per Anthropic's docs +
  observed behaviour, RC requires a **full-scope session token from a standard browser `claude` login**, not a
  long-lived setup token (which is inference-scoped only).
- So a headless, token-auth'd agent **functions fully** (polls `/loop`, chats via the dashboard message queue, runs
  tools) but **cannot expose a `claude.ai/code` Remote-Control URL**.
- **To get RC** you need a real browser-login `.credentials.json` (auto-refreshing) in that agent's `CLAUDE_CONFIG_DIR`
  — one browser login per account, captured + synced (the file persists + auto-refreshes). That's a separate build-out:
  a `.credentials.json` capture/sync pipeline (mirror the setup-token flow) + per-account config dirs for RC-capable
  agents. **Both auth types coexist on one machine** via separate `CLAUDE_CONFIG_DIR`s — token-workers and browser-login
  RC-agents don't interfere.

### Operator decision (2026-05-22)

**For now: headless (setup-token) agents for BOTH main and worker. Enable Remote Control later.** So:

- No browser-login automation needed right now.
- RC is a convenience (operator dropping into a live session), not required for agents to function.
- Revisit the `.credentials.json` capture/sync + RC wiring when RC is actually wanted.

---

## Quick verification recipe (for whoever picks this up)

```bash
# Prove an account's setup token is valid (headless):
set -a; . ~/.claude-accounts/harsh-primary.env; set +a
claude -p 'reply AUTH_OK'                      # → AUTH_OK

# Prove the interactive headless recipe (the fix), in an isolated config dir:
mkdir -p /tmp/ck && printf '%s' '{"theme":"dark","hasCompletedOnboarding":true,"hasCompletedProjectOnboarding":true,"hasTrustDialogAccepted":true,"bypassPermissionsModeAccepted":true}' > /tmp/ck/.claude.json
tmux new-session -d -s ck "CLAUDE_CONFIG_DIR=/tmp/ck bash -c 'source ~/.claude-accounts/harsh-primary.env; cd /tmp; exec claude'"
# → skips wizard, reaches chat prompt authenticated (accept the one folder-trust prompt with Enter)

# Prove the orchestrator spawn path (workers):
python3 -c "from server import tmux_spawn; print(tmux_spawn.spawn(slot_id=99, boot_prompt='reply SPAWN_WORKS', cwd='/tmp', env_file='$HOME/.claude-accounts/harsh-primary.env'))"
tmux capture-pane -t orch-slot-99 -p | tail   # → authenticated, replied SPAWN_WORKS
```

## Files / pointers

- Fix: `agent-orchestrator/server/tmux_spawn.py` — `_ensure_claude_config_dir()`, `_ONBOARDING_SEED`, env_file branch of
  `_start_session()`. Commit `1717768`.
- Agent-spawn (needs env_file wiring): `agent-orchestrator/server/server.py:3158` (`spawn_agent_endpoint`) → `:3240`
  (`spawn_named`).
- Worker-spawn (already wired): `server.py:1807` (`tmux_spawn.spawn(env_file=…)`).
- Accounts + token files: `data/config/accounts.json` (`oauth_token_env_file`), `~/.claude-accounts/<id>.env`.
- Token SSOT buckets: `gs://central-element-323112-orchestrator-creds/accounts/`,
  `s3://uts-orchestrator-creds-427895769566/accounts/`.
- Codex SSOT (update pending): `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`.
