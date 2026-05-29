---
name: harsh_account_pool_expansion
title: "Harsh adds 2 Anthropic accounts to mirror Ikenna's rotation pool (Phase 5 setup-token flow)"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
status: active
created: 2026-05-29
last_updated: 2026-05-29
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
estimate_calibration_note: |
  Infra (0.8×): single-operator action × 2 accounts × known recipe. Mostly elapsed time
  (account-creation cooldowns + KYC waiting); active work is the setup-token mint +
  env-file push per Phase 5 SSOT. Same recipe Ikenna already followed for his 3 accounts.
locked_by: live-defi-rollout
locked_since: 2026-05-29
related:
  - issues/harsh_account_pool_expansion_2026_05_29.md
  - ../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md
---

# Harsh — expand to 3-account rotation pool (mirror Ikenna)

Operator-directed 2026-05-29 (ikenna): "put in one of the issues and plans that harsh needs to reauth the same way
Ikenna did on his 3 accounts." Single-account-Harsh is a structural rotation gap — see
[`issues/harsh_account_pool_expansion_2026_05_29.md`](issues/harsh_account_pool_expansion_2026_05_29.md) for the why.

End state: **3 harsh-tagged accounts** in `agent-orchestrator/data/config/accounts.json`, each with a working
setup-token and `oauth_token_env_file`. Mirrors Ikenna's pool exactly so harsh-tagged slots survive single-account
failures via the existing `_pick_next_account` round-robin.

## Phase 0 — Decide the two new account identities (P1)

- [ ] [HUMAN] P1. **Harsh** picks two more Anthropic identities to provision. Constraints (per
      `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`): - Must be distinct Anthropic-side identities
      (different primary email; OR same Google account with different secondary email allowed if Anthropic accepts). -
      Each must be on a **subscription tier** (Pro / Max5 / Max20) to qualify for weekly-msg-limit pooling. - Suggested
      labels mirroring Ikenna's pattern: `harsh-secondary` + `harsh-tertiary` (or equivalent slugs).
- [ ] [HUMAN] P1. Confirm tier + weekly_msg_limit per new account (1200/wk on max20 matches Ikenna's pool).

## Phase 1 — Mint setup-tokens (P1)

- [ ] [HUMAN] P1. For EACH new account, on a browser-capable machine, run: `bash     claude setup-token     ` →
      completes OAuth in browser → emits a long-lived setup-token (~365d TTL). Stores at `~/.claude/.credentials.json`
      on that machine.
- [ ] [HUMAN] P1. For EACH account, copy the setup-token + write to its env file under `~/.claude-accounts/`:
      `bash     cat > ~/.claude-accounts/<account-id>.env <<EOF     CLAUDE_CODE_OAUTH_TOKEN=<setup-token-value>     unset ANTHROPIC_API_KEY     EOF     chmod 600 ~/.claude-accounts/<account-id>.env     `

## Phase 2 — Push env files to fleet creds buckets (P1)

- [ ] [AGENT] P1. For each new env file, push to BOTH cred buckets (matches Phase 5 distribution path):
      `bash     gsutil cp ~/.claude-accounts/<id>.env gs://central-element-323112-orchestrator-creds/accounts/     aws s3 cp ~/.claude-accounts/<id>.env s3://uts-orchestrator-creds-427895769566/accounts/     `
      Verify mode 600 preserved.
- [ ] [AGENT] P1. Trigger the fleet credential-sync (whichever script/cron pulls into each VM's
      `/home/ubuntu/.claude-accounts/`) — confirm each backend has the new files.

## Phase 3 — Register in accounts.json (P0 — this is the SSOT flip)

- [ ] [AGENT] P0. Add the 2 new account entries to `agent-orchestrator/data/config/accounts.json` mirroring
      `harsh-primary`'s shape:
      `json     {       "id": "<new-account-id>",       "label": "Harsh — <sub-label>",       "tier": "max20",       "weekly_msg_limit": 1200,       "primary_email": "<email>",       "operator": "harsh",       "oauth_token_env_file": "~/.claude-accounts/<new-account-id>.env",       "setup_token_expires_at": "<ISO date ~365d from mint>"     }     `
      Update the `_phase5_note` to reflect 6 total accounts.
- [ ] [AGENT] P0. Reload accounts on every backend without restart (per the hot-reload pattern documented in
      `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`) OR rolling-restart the orchestrator service
      on each VM.

## Phase 4 — Verify rotation pool (P1)

- [ ] [AGENT] P1. Spawn a test worker on a free slot with `account_id: harsh-primary`. While running, mark
      `harsh-primary` rate-limited via `POST /api/conditions/<name>` (or simulate by injecting a 429). Confirm
      `_pick_next_account` rotates to `harsh-secondary` (NOT `sub-a-ikenna`) — round-robin must respect operator
      boundary if such filtering exists, OR confirm cross-operator rotation is acceptable.
- [ ] [AGENT] P1. Document the observed rotation behavior in this plan's success criteria + update
      `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` § "Rotation semantics" if it's not already
      specified.

## Phase 5 — Codex SSOT updates (P2)

- [ ] [AGENT] P2. Update `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` to note the
      operator-symmetric pool requirement (each operator should have ≥2 accounts to enable rotation; ≥3 matches Ikenna's
      resilience pattern). Cross-link from `agent-orchestrator/data/config/accounts.json` `_phase5_note`.

## Success criteria

- `accounts.json` contains 3 harsh-tagged accounts with valid `oauth_token_env_file` paths.
- Each env file present on every backend VM, mode 600.
- A simulated `harsh-primary` rate-limit triggers rotation to a harsh-side fallback (verified live).
- Harsh-tagged slots in `/api/state` can /heartbeat successfully on any of the 3 accounts.

## Out of scope

- Token refresh automation (annual re-auth is still HUMAN; setup-tokens last ~365d).
- Cross-operator rotation semantics — separate plan if rotation should respect operator boundary vs. share globally.
