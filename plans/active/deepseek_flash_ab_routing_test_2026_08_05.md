---
doc_type: plan
title: DeepSeek flash-vs-pro A/B routing test — cost, throughput, and completion-quality comparison
summary:
  DeepSeek's own backend already silently substitutes deepseek-v4-flash for a small, uncontrolled fraction of
  deepseek-v4-pro-declared requests (confirmed live 2026-08-05, ~8 of 364 task_usage rows) — a confounded sample that
  can't answer whether flash is actually cheaper once turn-count overhead is included. This plan stands up an explicit
  flash-variant DeepSeek account, deterministically alternates DeepSeek-bound dispatches between the pro and flash pools
  (never a coin flip — matches the existing operator ruling against randomness in AutoSpawn's provider routing), extends
  the billing dashboard to break spend down by exact model (not just provider), and — the part that actually matters —
  runs a completion-quality audit on a matched sample from each pool once the window closes, since a cheaper model that
  produces broken work is not actually cheaper.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, deepseek, model-routing, cost-optimization, ab-test, billing, quality-audit]
related:
  [
    /plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/omniroute_multi_provider_routing_evaluation_2026_08_03.md,
    /plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md,
    /plans/active/ao_fleet_cache_tokens_and_task_count_2026_08_05.md,
  ]
created: "2026-08-05"
last_updated: 2026-08-05
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/dashboard/src/TaskUsageWindows.tsx,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
supersedes:
superseded_by:
depends_on:
source: operator-conversation-2026-08-05
assigned_role: infra
drift_direction: advance-code
---

# DeepSeek flash-vs-pro A/B routing test — cost, throughput, and completion-quality comparison

## Background

An interactive cost-per-task investigation (2026-08-05, operator + Ikenna's session) found `deepseek-v4-flash` already
leaking into the fleet unintentionally: DeepSeek's API serves it for a real fraction of `deepseek-v4-pro`-declared
requests regardless of what the account's env file names (`server/deepseek_usage.py`'s own docstring). The 8 real
flash-model `task_usage` rows found live showed ~4x the average turn count of pro (192 vs 48.6), but same-plan sibling
comparison showed this was confounded by task-difficulty selection, not a clean signal — DeepSeek's own routing chose
which requests got downgraded, we didn't. This plan runs a real controlled test instead.

**Design constraint carried over from AutoSpawn's existing Claude-vs-DeepSeek provider split**: that routing is
deliberately deterministic, not random — `autospawn.py:928`'s own comment records an operator ruling that predictable,
debuggable behavior beats a coin flip. The pro/flash split below follows the same philosophy: alternate
deterministically (not `random.random() < 0.5`) so a bad run is reproducible and debuggable.

## Todos

- [ ] [INFRA] P1. Add an optional `variant: Literal["pro", "flash"] | None` field to `AccountDef` in
      `server/accounts.py` so two DeepSeek accounts can be told apart by declared model — today the schema has no such
      field and the model lives only in the account's own env file, invisible to AutoSpawn. Done-when: `basedpyright`
      clean, existing `AccountDef` tests still pass.
- [ ] [INFRA] P1. In `server/autospawn.py`, at the point where `provider == "deepseek"` and
      `_pick_headroom_account(..., provider="deepseek")` is called (~line 1316), split the candidate pool by `variant`
      and deterministically alternate between the pro and flash sub-pools — reuse the same style of persistent,
      debuggable accumulator `_deepseek_should_route()` already uses (not an in-memory-only counter that resets on
      restart; key off a real persisted count, e.g. total DeepSeek dispatches so far mod 2, or hash on `task_id`).
      Accounts with `variant: None` (the default/unset case) are treated as pro. Done-when: a unit test proves N
      consecutive DeepSeek dispatches split ~50/50 across variants and the split is reproducible across a process
      restart.
- [ ] [BACKEND] P1. Extend `GET /api/backlog/usage/windows` (and whatever backs `TaskUsageWindowsPanel`) to break down
      spend/tokens by exact `model`, not just `provider` — return per-model rows (deepseek-v4-pro, deepseek-v4-flash)
      AND a combined/aggregated deepseek row, for every window (1h/5h/24h/7d/lifetime). Done-when: hitting the endpoint
      with the two DeepSeek accounts live shows both models' rows separately and summed.
- [ ] [UI] P2. Extend `dashboard/src/TaskUsageWindows.tsx` (or add a sibling panel) to render the per-model breakdown
      from the previous todo — pro and flash visible side-by-side, not just folded into one DeepSeek row. Playwright
      regression spec per `/codex/06-coding-standards/ui-testing-layers.md`.
- [ ] [INFRA] P1. `bash scripts/quality-gates.sh` green in `agent-orchestrator/`, ship the routing + dashboard change
      via `quickmerge.sh --agent`.
- [ ] [OPERATOR] P1. Provision the live flash account: create `~/.claude-accounts/deepseek-v4-flash-1.env` on the
      orchestrator VM (same `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_BASE_URL` as an existing pro account,
      `ANTHROPIC_MODEL=     deepseek-v4-flash`), and add a matching entry to the live `data/config/accounts.json` with
      `variant: "flash"`. Tagged `[OPERATOR]` because it edits a live, operator-owned, gitignored production config file
      directly on the fleet's central VM — done by the agent via SSM per the operator's explicit instruction in this
      session (2026-08-05), not autonomously on a future run.
- [ ] [REVIEW] P2. After deploy, verify the split is actually live: confirm at least one real `task_usage` row lands
      with `model=deepseek-v4-flash` and `backfilled=0` within the first few hours, and that the pro pool is still
      getting roughly half of new DeepSeek dispatches (not starved).
- [ ] [REVIEW] P2. Let the split run for ~24h of real fleet dispatch (per operator ask, 2026-08-05) before drawing
      conclusions — a few hours of sample size isn't enough given the turn-count variance already measured (31-100 turns
      is the modal range, but the tail runs to 500+).
- [ ] [REVIEW] P1. Pull the post-window comparison: real `$/task`, `$/plan`, avg turn count, and avg total tokens/task
      for pro vs flash over the monitoring window, individually and aggregated — the exact breakdown the operator asked
      for. Compute whether flash's per-token discount actually beats pro once turn-count is priced in, not just compare
      headline `$/task`.
- [ ] [REVIEW] P1. **Completion-quality audit — the part that makes the cost comparison meaningful.**
      `agents/review.md`'s persistent review agent DOES watch every `slot_done`/PR and check the diff against the plan's
      `done_definition` — but confirmed 2026-08-05 (grep across `server/`) it is (a) ONE persistent agent for the WHOLE
      fleet (coverage at ~150-280 completions/day unverified), (b) enforcement is explicitly conversational only — its
      own `does_not` says "Auto-reject work — flags concerns conversationally," it never flips `/done` state or calls
      `/reopen` itself, and (c) its findings have NO structured/queryable event type (only `slot_done_no_plan_flip`, a
      mechanical ship-contract check, is logged) — so "the review agent would have caught it" is not independently
      auditable after the fact. This is why Layer 2 below is still required, not redundant. **Layer 1 (cheap,
      automated):** for every task in each pool during the window, check whether it was later hit by
      `POST /api/backlog/{task_id}/reopen` (via the activity log), and whether its eventual promoted commit's
      `quality-gates-v2` CI run was green. **Layer 2 (the one that actually proves correctness):** pull a stratified
      sample of ~15-20 completed todos from EACH pool, matched by plan/`estimate_class` so difficulty is comparable, and
      run an independent review pass (fresh agent or operator, no stake in the outcome) against the actual diff — did
      this todo genuinely get done correctly, not just "did it commit and pass QG." Done-when: a written verdict per
      sampled item (correct / needs-rework / broken) exists for both pools, not just an aggregate percentage.
- [ ] [REVIEW] P2. **Verify the review agent's real coverage** — pull its own activity/chat history for the monitoring
      window and count how many of the window's completed todos it actually touched (spot-checked) vs. the total
      completed count. If coverage is a small fraction, "no review-agent complaint" carries near-zero evidentiary weight
      for either pool and Layer 2's independent sample is doing all the real work, not a backstop to it.
- [ ] [OPERATOR] P3. **Decide whether the review agent's findings should become a structured, queryable event** (e.g. a
      `review_finding` activity-log entry with severity + task_id) instead of chat-only — this audit is the second time
      in this codebase's history a quality question needed data the review agent generates but doesn't persist. Out of
      scope to build inside this A/B test; flag as a follow-up if the operator agrees it's worth it.
- [ ] [DOC] P2. Write up the final verdict (keep flash / drop it / use it only for a specific task class) in this plan's
      Progress Log, with the real numbers cited, then archive this plan per the standard 6-step ritual.

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — model tier discipline this routing choice must not violate.
- `plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md` — the account-pool/routing-policy plan this
  variant split extends.

## Progress Log

- **2026-08-05**: Plan authored from an interactive cost-per-task investigation. Operator confirmed: deterministic
  alternation (not literal randomness), agent provisions the live account via SSM, plan tracked as LOCAL/human
  (`assigned_vm: NA`) since it involves a live production routing change the operator wants to review, not autonomous AO
  dispatch.
- **2026-08-05 — shipped `agent-orchestrator@7d73ded`**: `variant` field on `AccountDef`; deterministic pro/flash
  alternation in `autospawn.py` (`_deepseek_flash_should_route`, `deepseek_flash_route_fraction=0.5`, fails back to the
  unfiltered pool if the flash sub-pool is empty/unhealthy); `?model=` filter added to
  `GET /api/backlog/usage/windows` + `TaskUsageWindowsPanel` UI toggle (DeepSeek · Pro / · Flash options). QG green
  (2431 backend tests, 200 frontend tests). Landed on `live-defi-rollout`.
- **2026-08-05 — live account provisioned via SSM**: added `deepseek-v4-flash` to the orchestrator VM's
  `data/config/accounts.json` (`variant: "flash"`, `oauth_token_env_file: ~/.claude-accounts/deepseek-v4-flash.env` —
  same DeepSeek auth token as `deepseek-v4-pro`, only `ANTHROPIC_MODEL` line changed); backfilled `variant: "pro"` onto
  the existing `deepseek-v4-pro` entry for symmetry. Pre-edit `accounts.json` backed up to `~ubuntu/.accounts-backups/`
  (deliberately OUTSIDE the git tree — an earlier incident, `ao_self_pull_stalled_by_untracked_backup_files_2026_07_29`,
  wedged `ao-self-pull.sh`'s dirty-gate for 2+ hours on exactly this class of untracked backup file; hit + fixed live
  during this same provisioning, see next entry).
- **2026-08-05 — deploy verified**: `ao-self-pull.sh` initially skipped ("dirty (non-churn)") because my own
  `accounts.json.bak-*` file was untracked and un-gitignored inside the repo tree — moved it to
  `~ubuntu/.accounts-backups/` (never added to `.gitignore`, since a one-off backup doesn't belong in the repo at all)
  and re-ran; orchestrator restarted clean on `7d73ded`, `systemctl is-active`→`active`. Confirmed the new `?model=`
  filter works live: `deepseek-v4-pro` shows 377 lifetime tasks / avg $0.086/task (1h window); the 9 lifetime
  `deepseek-v4-flash` rows visible are the PRE-EXISTING uncontrolled-substitution rows (same ones found during the
  original investigation), not yet the new controlled split — no `task_usage` row has landed under the NEW
  `account_id=deepseek-v4-flash` yet, expected, since that only fires on the next fresh AutoSpawn spawn decision
  post-deploy, not instantly. **Next check-in**: confirm a real task_usage row lands with `account_id=deepseek-v4-flash`
  (not just `model=deepseek-v4-flash` under the old pro account) — this is the todo above ("verify the split is actually
  live"), not done yet as of this entry.
