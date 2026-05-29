---
name: cross_operator_auth_failover
title: "Cross-operator account rotation + auth-fail trigger + Slack alert on rotation"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
status: active
created: 2026-05-29
last_updated: 2026-05-29
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
estimate_calibration_note: |
  Refactor (0.4×): rotation logic exists (_pick_next_account); changes are removing
  any operator-boundary filter, adding an auth-fail detection path (no-heartbeat-
  after-spawn → mark auth_failed → rotate), and threading a rotation-reason field
  through the existing Slack-alert path. No new infra; one StrEnum + one server
  branch + one alert template.
locked_by: live-defi-rollout
locked_since: 2026-05-29
related:
  - issues/cross_operator_auth_failover_2026_05_29.md
  - ../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md
supersedes:
  - harsh_account_pool_expansion_2026_05_29.md # original misframing (operator corrected 2026-05-29)
---

# Cross-operator account rotation + auth-fail trigger + Slack alert

Operator-corrected 2026-05-29 (ikenna): "harsh shoudl be able to fail ove rteh ieknna auth those 4 keys are there for a
reason for both to be able to round robin betwene each ... doesnt need 2 more harsh accounts just neeeds use of ikenna
accounts ... Setup-token stale / OAuth auth-fail at startup shoudl allo round robin and send a slack alert to inform us
that we have switche deithe rbwcause of Setup-token stale / OAuth auth-fail at startup or Account rate-limited (429 from
Anthropic)."

End state:

1. `_pick_next_account` round-robins across the **entire** `accounts.json` pool regardless of `operator` tag.
2. A worker that fails to /heartbeat within N seconds of `/spawn` triggers rotation with reason `auth_failed`.
3. Every rotation event posts a Slack alert with the reason (`rate_limit` | `auth_failed` | `operator_directed`).

See [`issues/cross_operator_auth_failover_2026_05_29.md`](issues/cross_operator_auth_failover_2026_05_29.md) for the
why + reproduction.

## Phase 0 — Pre-audit (P0)

- [ ] [AGENT] P0. Read `agent-orchestrator/server/server.py` `_pick_next_account` (line 334). Confirm whether it filters
      by `operator` field on the account record. If yes — that filter is the bug; if no — confirm and document.
- [ ] [AGENT] P0. Map every call-site of `_pick_next_account` (rate-limit branch line 404, /boot guard line 587,
      operator-directed line 728). Tabulate which existing dispatch_reason strings get emitted.
- [ ] [AGENT] P0. Identify the existing Slack-alert plumbing (which module emits the `Slot N STALE` alert) and confirm
      whether rotation events flow through the same channel. Document the channel name (`agent-orchestrator-alerts`).

## Phase 1 — Cross-operator rotation (P0)

- [ ] [AGENT] P0. If Phase 0 found an operator-boundary filter in `_pick_next_account`, remove it — the round-robin MUST
      pick from ALL non-rate-limited / non-auth-failed accounts regardless of `operator` field. Add a unit test proving
      `harsh-primary` rotates into `sub-a-ikenna` when no other harsh-tagged account is available.
- [ ] [AGENT] P0. Live verify: spawn a test slot with `account_id: harsh-primary`, mark `harsh-primary` rate-limited via
      the DB (or `POST /api/conditions/<name>` if exposed), confirm next `/boot` returns a dispatch with an
      `ikenna`-tagged account in `dispatch_reason: account-rotated:<id>`.

## Phase 2 — Auth-fail rotation trigger (P0)

- [ ] [AGENT] P0. Define `AccountStatus` `StrEnum` in `agent-orchestrator/server/models.py` (or wherever account-status
      enums live): `healthy`, `rate_limited`, `auth_failed`, `disabled`. Migrate any existing boolean flag (e.g. the
      rate-limited DB column) to use the enum.
- [ ] [AGENT] P0. Add server-side watchdog: when `/api/slots/<N>/spawn` returns `ok` but no /heartbeat arrives within
      `SPAWN_HEARTBEAT_TIMEOUT_SECONDS` (default **180**), mark the assigned `account_id` as `auth_failed` in the DB.
      Then call `_pick_next_account` on that slot and re-spawn the tmux session with the new account. Cap retries at 2
      to avoid infinite-loop on a fully-broken pool.
- [ ] [AGENT] P0. Healing path: when an `auth_failed` account next successfully /heartbeats (after operator re-auths),
      flip its status back to `healthy`. Same pattern as rate-limit recovery — auto-unflag on success.
- [ ] [AGENT] P0. Unit + integration tests: (a) spawn slot with deliberately-stale token → 180s timeout → auto-rotate to
      next account → second spawn /heartbeat-s → original account status `auth_failed`. (b) Operator re-auths original
      account → next spawn on it /heartbeat-s → status flips back to `healthy`.

## Phase 3 — Slack alert on every rotation (P0)

- [ ] [AGENT] P0. Add a `RotationReason` `StrEnum`: `rate_limit`, `auth_failed`, `operator_directed`. Thread it through
      every `_pick_next_account` callsite so the dispatch_reason string carries the reason verbatim.
- [ ] [AGENT] P0. Wire the existing Slack `agent-orchestrator-alerts` channel to fire on every rotation event. Payload
      shape:
      `     🔄 Account rotation     Slot:        <N>     Operator:    <ikenna|harsh>     Swapped out: <old_account_id> (operator: <ikenna|harsh>)     Swapped in:  <new_account_id> (operator: <ikenna|harsh>)     Reason:      rate_limit | auth_failed | operator_directed     Time:        <ISO UTC>     `
      Cross-operator rotation (e.g. `harsh-primary` → `sub-a-ikenna`) should be visually highlighted (different emoji or
      color) so the operator immediately sees when one operator's slot is using another operator's quota.
- [ ] [AGENT] P0. End-to-end test on staging: trigger each rotation reason in turn, confirm Slack receives one alert per
      event with the correct reason field.

## Phase 4 — Codex SSOT updates (P1)

- [ ] [AGENT] P1. Update `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` to document: - Shared-pool
      design (any account can serve any operator). - Rotation triggers (`rate_limit`, `auth_failed`,
      `operator_directed`). - The 180s spawn-heartbeat watchdog. - The Slack alert schema for rotation events.
- [ ] [AGENT] P1. Cross-link from `agent-orchestrator/data/config/accounts.json` `_phase5_note` → this codex doc → this
      plan.

## Success criteria

- `_pick_next_account` proven (by test) to rotate cross-operator (harsh → ikenna pool and vice versa).
- A stale-token worker spawn auto-rotates within 180s, with the original account marked `auth_failed`.
- Slack `agent-orchestrator-alerts` receives one alert per rotation event, citing reason. Verified on staging.
- Re-spawning slot 6 today with `harsh-primary` (still stale per the 2026-05-29 reproduction) results in: 180s timeout →
  rotation to an ikenna account → worker /heartbeats → Slack alert fires with `reason: auth_failed`.

## Out of scope

- Adding more accounts to the pool (operator explicitly excluded 2026-05-29).
- Token-refresh automation (annual re-auth remains HUMAN; setup-tokens last ~365d).
- Per-operator quota-billing reconciliation when one operator's slot rides another operator's account — separate finance
  plan if needed.
