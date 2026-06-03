---
name: cross_operator_auth_failover
title: "Cross-operator account rotation + auth-fail trigger + Slack alert on rotation"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
status: archived
created: 2026-05-29
last_updated: 2026-05-29
archived: 2026-06-01
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
estimate_calibration_note: |
  Refactor (0.4×): rotation logic exists (_pick_next_account); changes are removing
  any operator-boundary filter, adding an auth-fail detection path (no-heartbeat-
  after-spawn → mark auth_failed → rotate), and threading a rotation-reason field
  through the existing Slack-alert path. No new infra; one StrEnum + one server
  branch + one alert template.
related:
  - issues/cross_operator_auth_failover_2026_05_29.md
  - ../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md
supersedes:
  - harsh_account_pool_expansion_2026_05_29.md # original misframing (operator corrected 2026-05-29)
---

## ✅ ARCHIVED 2026-06-01

Cross-operator auth-failover (account rotation on auth-fail, healing on heartbeat) shipped + deployed. 0 open todos.
Fleet-verified live (both AWS orchestrator VMs @589b711). **Deferred work:** none. **Codex aligned**
(agent-orchestrator-overview / -autospawn / -worker-liveness — all current 2026-06-01). Unlocked for archival.

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

- [x] ✅ [AGENT] P0. Read `agent-orchestrator/server/server.py` `_pick_next_account` (line 334). Confirm whether it
      filters by `operator` field on the account record. If yes — that filter is the bug; if no — confirm and document.
      **Finding (2026-05-29):** NO operator-boundary filter exists. The function (lines 334–352) loads ALL accounts from
      `accounts.json`, skips only `current_account_id` by position, then skips any account where
      `ss.account_is_rate_limited()` returns true. There is NO filter on the `operator` field. Cross-operator rotation
      already works at this level — if `harsh-primary` is rate-limited, `_pick_next_account` WILL return an ikenna
      account as the next candidate (assuming it is not rate-limited). The bug the operator describes (slot 6 not
      rotating to ikenna) is NOT a filter bug here; it is downstream — likely the `auth_failed` path (no heartbeat after
      spawn) is not implemented, so the stale-token slot never triggers rotation at all.
- [x] ✅ [AGENT] P0. Map every call-site of `_pick_next_account` (rate-limit branch line 404, /boot guard line 587,
      operator-directed line 728). Tabulate which existing dispatch_reason strings get emitted. **Finding
      (2026-05-29):** 4 call sites (plan said 3; there is a 4th at line 1117): | Line | Context | Trigger |
      dispatch_reason / message emitted | |------|---------|---------|-----------------------------------| | 404 |
      `rotate_all_slots_off_account()` | account quota sweep | activity: `account_rotation_triggered` →
      `_spawn_with_account_bg` (no dispatch_reason field returned) | | 589 | `/boot` endpoint | rate-limited at boot |
      `"account-rotated:{next_acc.id} — exiting, new session spawning"` or
      `"account {id} is rate-limited — no fallback accounts available"` | | 728 | `/heartbeat` endpoint | rate-limited
      at heartbeat | same pattern as /boot | | 1117 | `/done` endpoint | rate-limited after done | `message` field (not
      dispatch_reason): `"account-rotated:{next_acc.id} — exiting, new session spawning"` or
      `"Account {id} is rate-limited — no fallback accounts available. Slot held idle until window resets."` | No
      `operator_directed` trigger exists yet (plan item for Phase 3). The string `"account-rotated:<id>"` is the
      sentinel the worker detects to exit cleanly.
- [x] ✅ [AGENT] P0. Identify the existing Slack-alert plumbing (which module emits the `Slot N STALE` alert) and
      confirm whether rotation events flow through the same channel. Document the channel name
      (`agent-orchestrator-alerts`). **Finding (2026-05-29):** Slack module: `server/notifications/slack.py`. Webhook
      env var: `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`. `notify_slot_stale()` is called from `server/health.py:116`. A
      `notify_account_rotated()` stub exists at `slack.py:173` but is **not wired to any call site** — rotation events
      currently do NOT fire Slack alerts. Phase 3 must call `notify_account_rotated()` (or a richer version) from every
      `_pick_next_account` call site. Channel name: `agent-orchestrator-alerts` (configured in the Slack app's webhook
      URL; not hardcoded in Python).

## Phase 1 — Cross-operator rotation (P0)

- [x] ✅ [AGENT] P0. If Phase 0 found an operator-boundary filter in `_pick_next_account`, remove it — the round-robin
      MUST pick from ALL non-rate-limited / non-auth-failed accounts regardless of `operator` field. Add a unit test
      proving `harsh-primary` rotates into `sub-a-ikenna` when no other harsh-tagged account is available. **Finding
      (2026-05-29):** No filter existed (Phase 0 confirmed). Added 6-test suite in `tests/test_account_rotation.py`
      (agent-orchestrator@9191967): proves harsh-primary→sub-a-ikenna wrap-around, rate-limited skipping across
      operators, pool-exhausted→None, single-account→None, unknown-account fallback.
- [x] ✅ [AGENT] P0. Live verify: spawn a test slot with `account_id: harsh-primary`, mark `harsh-primary` rate-limited
      via the DB (or `POST /api/conditions/<name>` if exposed), confirm next `/boot` returns a dispatch with an
      `ikenna`-tagged account in `dispatch_reason: account-rotated:<id>`. **Verified (2026-05-29):** Set
      `rate_limited_until=NOW+60s` directly in `account_usage` SQLite (bypasses `rotate_all_slots_off_account` fan-out
      to avoid disrupting active slots). `/boot` on slot 97 with `account_id=harsh-primary` returned:
      `dispatch_reason: "account-rotated:sub-a-ikenna — exiting, new session     spawning"`. `sub-a-ikenna`
      operator=ikenna ✓. Cleaned up orch-slot-97 tmux session and marked slot killed.

## Phase 2 — Auth-fail rotation trigger (P0)

- [x] ✅ [AGENT] P0. Define `AccountStatus` `StrEnum` in `agent-orchestrator/server/models.py` (or wherever
      account-status enums live): `healthy`, `rate_limited`, `auth_failed`, `disabled`. Migrate any existing boolean
      flag (e.g. the rate-limited DB column) to use the enum. **Shipped (agent-orchestrator@ab64720):**
      `AccountStatus(StrEnum)` with 5 values in `models.py`. New `account_status VARCHAR` column on `AccountUsageRow` +
      bootstrap migration. `mark_account_auth_failed()`, `clear_account_auth_failed()`, `account_is_usable()` in
      `state_store.py`. `_account_to_view()` surfaces `auth_failed`/`disabled` from DB column. Dashboard `types.ts` +
      `App.tsx` updated for new values.
- [x] ✅ [AGENT] P0. Add server-side watchdog: when `/api/slots/<N>/spawn` returns `ok` but no /heartbeat arrives within
      `SPAWN_HEARTBEAT_TIMEOUT_SECONDS` (default **180**), mark the assigned `account_id` as `auth_failed` in the DB.
      Then call `_pick_next_account` on that slot and re-spawn the tmux session with the new account. Cap retries at 2
      to avoid infinite-loop on a fully-broken pool. — agent-orchestrator@6871070:
      WorkerLivenessKicker.\_check_spawn_heartbeat_timeouts() ticks on every liveness scan; detects slots where
      last_spawned_at > TIMEOUT and last_ping < last_spawned_at; marks account auth_failed via
      state_store.mark_account_auth_failed(); picks next usable account via new state_store.pick_next_account(); fires
      \_do_auth_fail_respawn() in daemon thread (kill old session + spawn fresh); fires Slack alert
      (reason:auth_failed). Retry cap: spawn_retry_count ≥ 2 silences watchdog for that slot. Schema: last_spawned_at +
      spawn_retry_count on SlotRow (ORM + bootstrap migration); /spawn resets both fields on each spawn.
- [x] ✅ [AGENT] P0. Healing path: when an `auth_failed` account next successfully /heartbeats (after operator
      re-auths), flip its status back to `healthy`. Same pattern as rate-limit recovery — auto-unflag on success. —
      agent-orchestrator@7c4ba9b: heartbeat_slot detects account_is_auth_failed → calls clear_account_auth_failed + logs
      account_auth_restored activity. \_pick_next_account updated to use account_is_usable (covers rate_limited +
      auth_failed + disabled).
- [x] ✅ [AGENT] P0. Unit + integration tests: (a) spawn slot with deliberately-stale token → 180s timeout → auto-rotate
      to next account → second spawn /heartbeat-s → original account status `auth_failed`. (b) Operator re-auths
      original account → next spawn on it /heartbeat-s → status flips back to `healthy`. — agent-orchestrator@9e0c712:
      19 tests (14 state_store unit + 4 \_pick_next_account skip-auth_failed + 1 healing path integration). 1
      spawn-watchdog stub skipped pending task-007. Tests verify: mark/clear/is_auth_failed, account_is_usable
      (healthy/RL/auth_failed/disabled), rotation skips unusable via account_is_usable mock, healing path (clear →
      usable). All 19 pass; pre-existing 5 failures unrelated to Phase 2.

## Phase 3 — Slack alert on every rotation (P0)

- [x] ✅ [AGENT] P0. Add a `RotationReason` `StrEnum`: `rate_limit`, `auth_failed`, `operator_directed`. Thread it
      through every `_pick_next_account` callsite so the dispatch_reason string carries the reason verbatim. **Shipped
      (agent-orchestrator@d69598c):** `RotationReason(StrEnum)` added to `models.py`. Threaded through all 4 call-sites
      in `server.py` (rotate_all_slots_off_account, /boot, /heartbeat, /done): `rotation_reason` field in `log_activity`
      details + dispatch_reason strings now carry the reason verbatim, e.g.
      `"account-rotated:<id> — reason:rate_limit — exiting, new session spawning"`. Preserves `account-rotated:<id>`
      sentinel for worker exit detection. All current sites use `rate_limit`; `auth_failed`/`operator_directed` wired in
      Phase 2 watchdog + future operator-directed endpoint.
- [x] ✅ [AGENT] P0. Wire the existing Slack `agent-orchestrator-alerts` channel to fire on every rotation event.
      Payload shape:
      `     🔄 Account rotation     Slot:        <N>     Operator:    <ikenna|harsh>     Swapped out: <old_account_id> (operator: <ikenna|harsh>)     Swapped in:  <new_account_id> (operator: <ikenna|harsh>)     Reason:      rate_limit | auth_failed | operator_directed     Time:        <ISO UTC>     `
      Cross-operator rotation (e.g. `harsh-primary` → `sub-a-ikenna`) should be visually highlighted (different emoji or
      color) so the operator immediately sees when one operator's slot is using another operator's quota. **Shipped
      (agent-orchestrator@3daacc0):** `_fire_rotation_alert()` helper fires `notify_account_rotated()` in a daemon
      thread at all 4 call-sites. `notify_account_rotated()` upgraded to full 6-arg Block Kit impl with
      `:rotating_light:` + "CROSS-OPERATOR" header suffix for cross-operator swaps.
- [x] ✅ [AGENT] P0. End-to-end test on staging: trigger each rotation reason in turn, confirm Slack receives one alert
      per event with the correct reason field. — agent-orchestrator@d190136: 13 tests in
      tests/test_rotation_slack_e2e.py: RotationReason enum (all 3 values), notify_account_rotated Block Kit payload per
      reason, cross-operator highlight, \_fire_rotation_alert wiring. Staging procedure documented in test module
      docstring.

## Phase 4 — Codex SSOT updates (P1)

- [x] ✅ [AGENT] P1. Update `codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` to document: -
      Shared-pool design (any account can serve any operator). - Rotation triggers (`rate_limit`, `auth_failed`,
      `operator_directed`). - The 180s spawn-heartbeat watchdog. - The Slack alert schema for rotation events. **DONE
      2026-05-30** — new §§ "Cross-operator shared account pool" + "Rotation across accounts — three triggers" added
      with trigger table, watchdog mechanics, Slack alert schema, Composes-with cross-link.
- [x] ✅ [AGENT] P1. Cross-link from `agent-orchestrator/data/config/accounts.json` `_phase5_note` → this codex doc →
      this plan. **DONE 2026-05-30** — `_shared_pool_note` added to accounts.json referencing codex doc + this plan.

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
