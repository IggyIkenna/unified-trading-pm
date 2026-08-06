---
doc_type: issue
title:
  "AutoSpawn fleet-wide critical-pool halt is Claude-only and provider-blind — when the best Anthropic account crosses
  90% it short-circuits the ENTIRE new-dispatch tick, starving the healthy DeepSeek pool (idle slots + 519 queued, ready
  tasks confirmed) instead of routing new tasks to DeepSeek"
summary: >-
  Operator reported (2026-08-04, msg 3703) that new tasks stopped being allocated to DeepSeek agents after the DeepSeek
  API integration. Confirmed root cause in `agent-orchestrator/server/autospawn.py`: the fleet-wide critical-pool halt
  (`is_pool_critically_exhausted` → `best_account_used_pct`) ranks ONLY `provider == "anthropic"` accounts (line ~1013)
  and fires at `_CRITICAL_POOL_HEADROOM_PCT = 90`. `_check_and_log_critical_pool_halt` runs BEFORE the backlog/prereq
  read and, when halted, short-circuits the ENTIRE new-dispatch tick — so the provider-aware router
  (`select_account_for_spawn(preferred_provider=None)`, which WOULD route to DeepSeek) never runs. Result at time of
  filing: best Claude account (sub-b) at 92% weekly → halt engaged → DeepSeek slots 10/11/12 IDLE and Claude slots 13-16
  IDLE, only 1 of 519 queued tasks dispatched, despite ≥10 confirmed READY (no-blocker) tasks in the first 118 queued
  sampled. The DeepSeek account is `status: healthy`, has no weekly/5h limits populated, and shows
  `balance_is_available: true` — it should be absorbing exactly this overflow. The halt was designed (operator ruling
  2026-07-29) BEFORE the DeepSeek blended-routing integration (2026-07-28) and was never made provider-aware, so a
  Claude-only exhaustion signal now incorrectly gates a mixed Claude+DeepSeek fleet.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, dispatch, deepseek, provider-routing, capacity-halt, pool-exhaustion]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: operator-report
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: "agent-orchestrator@3f06bea (code fix) + operator balance top-up, verified live 2026-08-04T14:33Z"
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# AutoSpawn critical-pool halt starves the DeepSeek pool (provider-blind halt)

## Reporter / trigger

Operator message **3694/3703** (2026-08-04T13:52Z): _"we recently integrated deepseek api so that we can use it and new
tasks should be allocated to them. did you stop dispatching new tasks to deepseek agents?"_ Filed by main orchestrator
agent `agt-fdecde` after live investigation.

## Observed state (evidence, 2026-08-04 ~13:52Z)

- `GET /api/state` `backlog_summary`: **`queued: 519`, `dispatched: 1`**, done 1028.
- Per-slot (`/api/state.slots`): slots **10, 11, 12 = IDLE, account `deepseek-v4-pro`**; slots 13-16 = IDLE (`sub-b`);
  slots 2-9 = working (`sub-b`). So the whole DeepSeek pool is idle while 519 tasks queue.
- `GET /api/accounts`: `deepseek-v4-pro` → `status: healthy`, `provider: deepseek`, `weekly_msg_limit: 0`,
  `rate_limited_until: null`, `balance_is_available: true` (`balance_usd: 0.34`), `used_by_slots: [9]`,
  `last_used_at: 13:45:53Z`. Best Anthropic account `sub-b` at **92% weekly** (≥ 90% halt threshold).
- STEP 2.4 readiness proof: sampled blockers on the queued set — **≥10 tasks return `"ready (no blockers)"`** in the
  first 118 checked (e.g. `cefi_satellite_ao_dispatch_batch3-002`, `cross_cutting_satellite_ao_dispatch_batch1-011`).
  Ready work exists and is NOT being dispatched → this is a genuine dispatch stall, not prereq-gated saturation.

## Root cause (code-grounded)

`agent-orchestrator/server/autospawn.py`:

1. `_CRITICAL_POOL_HEADROOM_PCT = 90` (line ~997).
2. `best_account_used_pct(session)` (line ~1000) filters to
   **`anthropic_accounts = [acc for acc in ... if acc.provider == "anthropic"]`** (line ~1013) — DeepSeek is invisible
   to this signal by construction.
3. `is_pool_critically_exhausted(session)` (line ~1029) returns `used >= 90`, i.e. True whenever the best _Claude_
   account is ≥90% — regardless of DeepSeek health.
4. `_check_and_log_critical_pool_halt` (line ~2110) is evaluated **before** the backlog/prereq read and, when halted,
   short-circuits the whole tick: _"skip new-task spawning for this tick entirely."_
5. Consequently the provider-aware router `select_account_for_spawn(preferred_provider=None)` (the
   `deepseek_claude_blended_provider_routing_2026_07_28` path that WOULD send new tasks to DeepSeek first) never
   executes on a halted tick.

**Net:** a Claude-only exhaustion gate, authored under the 2026-07-29 operator ruling — one day AFTER the 2026-07-28
DeepSeek blended-routing integration — halts ALL new dispatch for a fleet that now has a healthy non-Claude provider
sitting idle. The two features were never reconciled.

## Impact

- New backlog work is fully stalled whenever Claude is ≥90% used, even though DeepSeek could absorb it — directly the
  behavior the DeepSeek integration was meant to prevent.
- The `resume` pass and in-flight tasks continue (halt only withholds NEW dispatch), so this presents as a slow bleed:
  the fleet drains to idle and stays there until a Claude weekly window resets, not as an obvious hard failure.

## Proposed remediation (for engineer review — NOT yet actioned)

Make the halt provider-aware so it only fires when there is **no usable dispatch target of ANY provider**. Options:

- **(A, preferred)** Gate `is_pool_critically_exhausted` on "no usable Claude headroom **AND** no usable DeepSeek
  capacity" — i.e. only halt when the _entire blended pool_ is exhausted. When Claude is ≥90% but DeepSeek is healthy,
  do NOT halt; let the existing `preferred_provider=None` router send new tasks to DeepSeek.
- **(B)** On a Claude-only-exhausted tick, skip the fleet-wide short-circuit and instead force the spawn path with
  `preferred_provider="deepseek"` so overflow explicitly routes to DeepSeek while Claude is throttled.
- Either way: keep the alert, but reclassify it from "pool critically exhausted → halt" to "Claude pool exhausted →
  routing overflow to DeepSeek" so the dashboard reflects reality.
- Separately surface DeepSeek **balance** as a health gate (current balance `$0.34` is low — DeepSeek dispatch will
  itself fail-closed soon; that is a distinct operator top-up concern, not the routing bug).

## Follow-ups (tracked)

- [x] [BUG] P1. ✅ Make AutoSpawn critical-pool halt provider-aware so a healthy DeepSeek pool is not starved when
      Claude is ≥90% (`agent-orchestrator/server/autospawn.py`; option A above). Done when: the halt only fires when the
      ENTIRE blended pool (Claude + every other registered provider) is exhausted, not Claude alone. —
      `agent-orchestrator@3f06bea` on `live-defi-rollout`, `ahead=0`. `is_pool_critically_exhausted()` now also checks
      the new `_non_anthropic_pool_has_capacity()` (usable + health-gate-clear + real dollar balance via the new
      `_account_has_balance_headroom()`, populated by `DeepSeekBalancePoller`); the same balance check is also wired
      into `select_account_for_spawn()`'s per-candidate DeepSeek eligibility check (proactive — skips a drained account
      before ever attempting a spawn that would fail on auth, not just reactively after failures accumulate). 6 new unit
      tests covering the halt (headroom present/absent/unusable/health-gate-tripped/ no-non-anthropic-registered) +
      balance-headroom edge cases + the per-spawn balance-skip fallback chain; full suite green (2333 passed),
      `basedpyright`/`tsc`/`vitest` clean.
- [x] [OPERATOR] P2. ✅ Top up the `deepseek-v4-pro` balance (was `$0.34`) — even once the routing bug is fixed,
      DeepSeek dispatch fails-closed at zero balance. — Done: operator topped up to `$4.84` (confirmed live via
      `/api/accounts`, 2026-08-04 ~14:33Z).

## Notes

Main agent (`agt-fdecde`) does not push code and did not modify `autospawn.py`; this doc records the diagnosis for an
engineer worker / operator. The main agent's earlier "capacity halt is by-design, queue prereq-gated" read was
**incorrect** — corrected here by the STEP 2.4 per-task readiness proof above.

**2026-08-04 update — both follow-ups closed.** `[BUG] P1` fixed and shipped (`agent-orchestrator@3f06bea`); the fix
auto-deployed to the planning VM (`ao-self-pull.sh` restart at 14:30:19Z) and was verified live within minutes: DeepSeek
slots picked up real backlog tasks (`sports_curated_universe_domestic_selection_remaining-003`,
`sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists-006`) for the first time since the halt engaged.
`[OPERATOR] P2` (balance top-up) also done — balance confirmed `$4.84` live. This issue is fully resolved.
