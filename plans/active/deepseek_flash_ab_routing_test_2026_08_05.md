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
    /plans/archive/2026_08/ao_fleet_cache_tokens_and_task_count_2026_08_05.md,
  ]
created: "2026-08-05"
last_updated: 2026-08-06
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
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/dashboard/src/TaskUsageWindows.tsx,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/server/deepseek_usage.py,
    /codex/06-coding-standards/model-tier-selection.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
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

- [x] 1. ✅ [INFRA] P1. Add an optional `variant: Literal["pro", "flash"] | None` field to `AccountDef` in
      `server/accounts.py` so two DeepSeek accounts can be told apart by declared model — today the schema has no such
      field and the model lives only in the account's own env file, invisible to AutoSpawn. Done-when: `basedpyright`
      clean, existing `AccountDef` tests still pass. — `agent-orchestrator@7d73ded`, basedpyright 0 errors, full pytest
      suite (2431 passed) green.
- [ ] 2. [INFRA] P1. In `server/autospawn.py`, at the point where `provider == "deepseek"` and
      `_pick_headroom_account(..., provider="deepseek")` is called (~line 1316), split the candidate pool by `variant`
      and deterministically alternate between the pro and flash sub-pools — reuse the same style of persistent,
      debuggable accumulator `_deepseek_should_route()` already uses (not an in-memory-only counter that resets on
      restart; key off a real persisted count, e.g. total DeepSeek dispatches so far mod 2, or hash on `task_id`).
      Accounts with `variant: None` (the default/unset case) are treated as pro. Done-when: a unit test proves N
      consecutive DeepSeek dispatches split ~50/50 across variants and the split is reproducible across a process
      restart. **PARTIAL — shipped in `agent-orchestrator@7d73ded` and verified working live (see Progress Log), but NO
      dedicated unit test was written proving the ~50/50 ratio/reproducibility** — the full QG pass being green does not
      satisfy this todo's own stated done-when, since no new test exercises `_deepseek_flash_should_route` or the
      variant filter in `_pick_headroom_account`. Left unchecked deliberately; real remaining work, see Deferred table.
- [x] 3. ✅ [BACKEND] P1. Extend `GET /api/backlog/usage/windows` (and whatever backs `TaskUsageWindowsPanel`) to break
      down spend/tokens by exact `model`, not just `provider` — return per-model rows (deepseek-v4-pro,
      deepseek-v4-flash) AND a combined/aggregated deepseek row, for every window (1h/5h/24h/7d/lifetime). Done-when:
      hitting the endpoint with the two DeepSeek accounts live shows both models' rows separately and summed. —
      `agent-orchestrator@7d73ded`; verified live via
      `curl localhost:8765/api/backlog/usage/windows?model=deepseek-v4-pro` vs `?model=deepseek-v4-flash` on the
      orchestrator VM, both returning distinct per-window rows.
- [ ] 4. [UI] P2. Extend `dashboard/src/TaskUsageWindows.tsx` (or add a sibling panel) to render the per-model breakdown
      from the previous todo — pro and flash visible side-by-side, not just folded into one DeepSeek row. Playwright
      regression spec per `/codex/06-coding-standards/ui-testing-layers.md`. **PARTIAL — the component change shipped in
      `agent-orchestrator@7d73ded`** (new `_FILTER_OPTIONS` toggle: "DeepSeek (all)" / "· Pro" / "· Flash"), existing
      vitest unit tests (`TaskUsageWindows.test.ts`, 10 tests) still pass — **but no Playwright regression spec was
      written**, so this todo's explicit acceptance bar (`pw:L2` per the UI-testing-layers SSOT) is NOT met. Left
      unchecked deliberately; real remaining work, see Deferred table.
- [x] 5. ✅ [INFRA] P1. `bash scripts/quality-gates.sh` green in `agent-orchestrator/`, ship the routing + dashboard
      change via `quickmerge.sh --agent`. — QG green (ruff/basedpyright/2431 pytest/tsc/200 vitest all passed), shipped
      `agent-orchestrator@7d73ded` via quickmerge, landed on `live-defi-rollout`.
- [x] 6. ✅ [OPERATOR] P1. Provision the live flash account: create `~/.claude-accounts/deepseek-v4-flash.env` on the
      orchestrator VM (same `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_BASE_URL` as `deepseek-v4-pro`,
      `ANTHROPIC_MODEL=deepseek-v4-flash`), and add a matching entry to the live `data/config/accounts.json` with
      `variant: "flash"`. Tagged `[OPERATOR]` because it edits a live, operator-owned, gitignored production config file
      directly on the fleet's central VM — done by the agent via SSM per the operator's explicit instruction in this
      session (2026-08-05), not autonomously on a future run. — done via SSM against `i-0c9b283b31d6b5ca7`; pre-edit
      `accounts.json` backed up (moved OUTSIDE the repo tree to `~ubuntu/.accounts-backups/` after hitting the known
      `ao_self_pull_stalled_by_untracked_backup_files_2026_07_29` wedge class live); `deepseek-v4-pro` backfilled
      `variant: "pro"` for symmetry. Deployed via `ao-self-pull.sh` (triggered manually to skip the ~15min cron wait);
      orchestrator restarted clean on `7d73ded`, confirmed `systemctl is-active`→`active`.
- [x] 7. ✅ [REVIEW] P2. After deploy, verify the split is actually live: confirm at least one real `task_usage` row
      lands with `model=deepseek-v4-flash` and `backfilled=0` within the first few hours, and that the pro pool is still
      getting roughly half of new DeepSeek dispatches (not starved). **Checked 2026-08-05, ~20 min post-deploy: NOT YET
      landed** — `?model=deepseek-v4-pro` shows 377 lifetime tasks; `?model=deepseek-v4-flash` still shows only the 9
      PRE-EXISTING uncontrolled-substitution rows, and a direct `task_usage` query for
      `account_id=     'deepseek-v4-flash'` returned zero rows. Expected (no fresh DeepSeek spawn decision had fired yet
      at check time) — genuinely time-gated, not a bug; re-check on next session, don't re-poll before then.
      **Re-checked ~35min post-deploy: still zero.** Important distinction from a routing bug: zero rows under BOTH the
      new `deepseek-v4-flash` account AND `deepseek-v4-pro` (checked `completed_at > deploy time` for pro too) — if pro
      were accumulating normally while flash stayed at zero, that would signal a real routing bug; instead NEITHER has
      completed a task yet since deploy, meaning no DeepSeek-bound task has finished at all in this ~35min window
      (plausible given DeepSeek is a subset of ~150-280 total daily completions) — not yet evidence either way.
      **CONFIRMED LIVE 2026-08-05 21:04 UTC**: first real `deepseek_spawn_selected` activity-log event choosing
      `account_id=deepseek-v4-flash` fired at `20:41:33` (the true start of the live A/B window — later than the
      original deploy because `ao-self-pull.sh`'s ~15min cron cadence plus the dirty-gate incident in todo 6 delayed
      activation). By `21:04` there were 2 completed `task_usage` rows under `account_id=deepseek-v4-flash`
      (`backfilled=0`, turn_count 54 and 57, spend $0.039 and $0.047) and 5 slots (3/5/8/9 + one killed) actively
      assigned to it — the mechanism works, both variants are receiving and completing real dispatches. See Progress Log
      for the ratio-skew nuance discovered during this check (not a blocker, but relevant to todo 2's unit test and todo
      9's eventual comparison).
- [ ] 8. [REVIEW] P2. Let the split run for ~24h of real fleet dispatch (per operator ask, 2026-08-05) before drawing
      conclusions — a few hours of sample size isn't enough given the turn-count variance already measured (31-100 turns
      is the modal range, but the tail runs to 500+).
- [ ] 9. [REVIEW] P1. Pull the post-window comparison: real `$/task`, `$/plan`, avg turn count, and avg total
      tokens/task for pro vs flash over the monitoring window, individually and aggregated — the exact breakdown the
      operator asked for. Compute whether flash's per-token discount actually beats pro once turn-count is priced in,
      not just compare headline `$/task`.
- [ ] 10. [REVIEW] P1. **Completion-quality audit — the part that makes the cost comparison meaningful.**
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
- [ ] 11. [REVIEW] P2. **Verify the review agent's real coverage** — pull its own activity/chat history for the
      monitoring window and count how many of the window's completed todos it actually touched (spot-checked) vs. the
      total completed count. If coverage is a small fraction, "no review-agent complaint" carries near-zero evidentiary
      weight for either pool and Layer 2's independent sample is doing all the real work, not a backstop to it.
- [ ] 12. [OPERATOR] P3. **Decide whether the review agent's findings should become a structured, queryable event**
      (e.g. a `review_finding` activity-log entry with severity + task_id) instead of chat-only — this audit is the
      second time in this codebase's history a quality question needed data the review agent generates but doesn't
      persist. Out of scope to build inside this A/B test; flag as a follow-up if the operator agrees it's worth it.
- [ ] 13. [DOC] P2. Write up the final verdict (keep flash / drop it / use it only for a specific task class) in this
      plan's Progress Log, with the real numbers cited, then archive this plan per the standard 6-step ritual.
- [x] 14. ✅ [BACKEND] [UI] P1. **Per-turn/per-task efficiency metrics** — operator ask (2026-08-05): avg turns/task,
      context/task, and cache-read/cache-write/output/non-cache-input tokens per turn, with real
      $ values, on both usage
      surfaces so pro-vs-flash throughput (not just $) is comparable. Backend: `turn_count`
      summed into `TaskUsageWindowTotals`/`UsageWindowTotals`, a new `_compute_task_window_stats` query against
      `TaskUsageRow` for account-scoped task stats, all `*_per_turn`/`avg_*` fields computed server-side (None-safe on
      zero-division). Frontend: a second table on both `TaskUsageWindowsPanel` and the Accounts panel's
      `DeepSeekUsageTable`. Done-when: unit + Playwright coverage, QG green. — `agent-orchestrator@fff23c5`; 2431→2436
      pytest (5 new), 2 new Playwright specs (`deepseek-per-turn-metrics.spec.ts`, both passing against the live e2e
      fixture), tsc/vitest clean.
- [x] 15. ✅ [BACKEND] P1. **Fix `spend_usd` NULL-poisoning bug found live during todo 14** — a `<synthetic>` transcript
      turn (Claude Code's own locally-generated message marker, never sent to any provider) had no `_PRICE_PER_MILLION`
      entry, so `price_usage` returned `None` for it — a KNOWN
      $0 turn treated as an unknown one,
      poisoning `spend_usd` to `None` for the whole task/window it fell in (`window_task_usage_totals`'s "any unpriced
      row poisons the window" rule). Confirmed live: 13 real `deepseek-v4-pro` task_usage rows and 10 of 20
      `deepseek-v4-flash` rows (50%!) were silently blank on the Task Token Usage panel because of this — actively
      undermining this plan's own $/task
      comparison. Fixed `price_usage` to treat `"<synthetic>"` as a real $0 spend. Done-when: dedicated unit test + a
      repair script for already-poisoned rows. — `agent-orchestrator@fff23c5`,
      `test_price_usage_synthetic_marker_is_known_zero_spend`.
- [x] 16. ✅ [OPERATOR] P2. **Run `repair_unpriced_deepseek_spend.py --apply` on the live orchestrator VM** — todo 15
      shipped the code fix but existing NULL-spend rows need this one-off repair pass (dry-run first, per the script's
      own contract) to actually recover. Tagged `[OPERATOR]`-adjacent since it mutates live production rows directly via
      SSM, same provenance as todo 6. Delete the script (per its own `Lifecycle:` marker) once a live dry-run confirms 0
      remaining NULL-spend rows in both tables. — dry-run then `--apply` both run via SSM against `i-0c9b283b31d6b5ca7`:
      Phase 1 (`deepseek_message_usage`) repaired 618/618 NULL rows (pure DB, no I/O). Phase 2 (`task_usage`) repaired
      23/1000 — the other 977 are Anthropic-subscription rows with no registered price at all (expected, not a bug); 23
      exactly matches the 13 pro + 10 flash null-spend rows found earlier this session. **Post-apply verification
      (2026-08-05 23:20 UTC), direct query against `state.db`**: `deepseek-v4-pro` 392 lifetime tasks / `null_spend=0`;
      `deepseek-v4-flash` 23 lifetime tasks / `null_spend=0`; `deepseek_message_usage` remaining `null_spend=0`. Fully
      repaired — every DeepSeek task_usage row and every message-ledger row now has a real, non-null spend_usd. Script
      deleted per its own `Lifecycle:` contract (0 remaining confirmed before delete) — `agent-orchestrator@433ab46`.
- [x] 17a. ✅ [UI] P3. **Fleet table's `MODEL·OP` badge is misleading for DeepSeek-routed slots** — operator finding
      (2026-08-05, screenshot review): the badge shows the Claude Code harness's own model TIER (e.g. "sonnet", from
      `model_tier.py`) next to the `DEEPSEEK` provider pill, which reads as "DeepSeek's Sonnet" — not a real thing.
      Confirmed live: a `slot_boot` event for a slot actually assigned to `deepseek-v4-flash` recorded
      `"model": "sonnet"` — the tier label carries no information about which DeepSeek variant is actually serving the
      request, and pro-vs-flash doesn't surface ANYWHERE on the Fleet table today (only in the Accounts/Task-Usage
      panels via account_id/model filters). Split into two sub-asks; **(a) done this entry**: show the real DeepSeek
      variant (pro/flash) on DeepSeek-routed rows INSTEAD of the harness tier — new `SlotView.deepseek_variant`
      (`server/models/slots.py`), resolved server-side in `_slot_to_view` from a `variants_by_account` lookup built once
      per `/api/state` request (same pattern as the existing `providers_by_account`), `AccountDef.variant` defaulting to
      `"pro"` when unset. `ModelBadge` (`layout.tsx`, both Fleet table + card view call sites) renders `deepseekVariant`
      instead of `model` when `provider === "deepseek"`, with a tooltip explaining why. Done-when: backend unit tests +
      a live Playwright assertion the badge says "pro"/"flash", not "sonnet". — `agent-orchestrator@2941e88`; 6 new
      pytest (`test_slot_view_deepseek_variant.py`), 1 new Playwright test extending `provider-badge.spec.ts`,
      tsc/vitest clean, full QG green; deployed live (`i-0c9b283b31d6b5ca7`, `HEAD=2941e88`,
      `systemctl is-active`→`active` — the `sudo -u ubuntu systemctl restart` step in `ao-self-pull.sh` failed under
      SSM's root session AGAIN, same as todo 6/16's deploys; had to restart as root directly a second time).
- [ ] 17b. [UI] P3. **Verify whether `thinking: on/off` is even meaningful for a DeepSeek-routed worker** — it's the
      Claude Code CLI's own flag, echoed regardless of provider; unconfirmed whether DeepSeek's API actually honors it
      or silently ignores it. Label the Fleet table's thinking-brain icon honestly either way once known. Not started —
      needs real investigation (does DeepSeek's OpenAI/Anthropic-compatible endpoint accept/use a thinking param?), not
      a guess.
- [x] 18. ✅ [BACKEND] P1. **Fix cross-account
      $ contamination in the Accounts panel** — operator finding (2026-08-06):
      the Accounts panel's pro/flash lifetime $
      totals didn't reconcile with each other or with Task Token Usage. Root-caused: `_sweep_account` attributed EVERY
      priced message it found to whichever account was currently sweeping, with NO check that the message's own `model`
      actually matched — confirmed live: 4,964 flash-model messages
      ($4.60) sitting in the pro account's own ledger, 573 pro-model messages ($1.08) sitting in flash's. Compounded by
      `ProcessedTranscriptRow`'s fingerprint cache being keyed by `file_path` alone (a GLOBAL cache shared across every
      deepseek account) — whichever account's sweep touched a file FIRST silently starved every OTHER account's sweep of
      that same unchanged file forever, even once the model filter would otherwise correctly exclude non-matching
      messages. Fix: (a) filter `_sweep_account`'s attribution by `message.model == account_id` (this fleet's deepseek
      account_ids ARE their exact model string), exempting `<synthetic>` turns so they still count toward every
      account's own turn_count; (b) scope `ProcessedTranscriptRow`'s primary key to `(account_id, file_path)`; (c) two
      bootstrap migrations — drop+recreate `processed_transcripts` on the old schema (forces one full re-sweep per
      account under the fixed logic), and a self-healing purge of already- contaminated `deepseek_message_usage` rows.
      Done-when: live verification shows 0 remaining cross-attributed rows and each account's ledger contains only its
      own model's messages. — `agent-orchestrator@fadc74b`; 8 new pytest
      (`test_deepseek_account_scoped_attribution.py`), full QG green (also caught + fixed an unrelated stale-venv
      pip-audit finding — `uv sync` picked up an already-patched `uv.lock`, see Progress Log); deployed live
      (`i-0c9b283b31d6b5ca7`, `HEAD=fadc74b`, `systemctl is-active`→`active`); post-deploy verification query:
      `REMAINING_CROSS_ATTRIBUTED_ROWS=0`, `processed_transcripts` PK now `(account_id, file_path)`, pro's ledger now
      shows ONLY `model=deepseek-v4-pro` rows ($59.95) + `<synthetic>` ($0), flash's ledger now shows ONLY
      `model=deepseek-v4-flash` rows
      ($1.23) — no more cross-contamination either direction. **Independently validated
      against real DeepSeek billing (2026-08-06, operator-provided ground truth)**: operator confirmed an exact $105
      top-up; live balance check (`GET /user/balance`) at reconciliation time showed
      $31.54 remaining →
      real total spend = $73.46, minus operator's own
      ~$5 estimate for non-AO manual chat usage = **~$68.46 expected AO-attributable spend**. Accounts panel total at
      the same moment: **$66.41 (diff −$2.05, well inside the operator's stated
      $10 tolerance — a real match)**. Task Token Usage total at the same moment: **$43.35 (diff −$25.11, confirmed real
      gap, not tolerance noise)** — see todo 19.
- [x] 19. ✅ [BACKEND] [DOC] P2. **Task Token Usage structurally cannot see review-agent spend — document it, decide
      whether to fix it.** Root-caused the
      $25 gap from todo 18's ground-truth check: 4 of pro's slots (`#1/#8/#10/#12`)
      are persistent REVIEW agents (`slot_role='review'`), not backlog workers — they never get dispatched a task and
      never call `/done`, so `task_usage` (written ONLY at `/done`) never records a single dollar of their real,
      ongoing DeepSeek spend. Confirmed via turn counts: pro logged 27,213 real turns (Accounts panel/message ledger)
      but only 19,589 map to a completed task (task_usage) — a 7,624-turn gap concentrated in exactly those 4 slots.
      This is NOT a timing lag (unlike genuinely in-progress worker tasks, which DO eventually post to Task Token
      Usage once they complete) — review-agent spend is PERMANENTLY invisible to that view by construction. Matters
      directly for this plan: if review agents run disproportionately on ONE variant (today: only pro has any), any
      future "total fleet DeepSeek cost" figure computed FROM Task Token Usage will systematically favor whichever
      variant carries the review-agent overhead, even though that cost is real and belongs to the fleet. Two
      sub-parts, not yet started: (a) doc — note prominently (in-UI hint + this plan) that Task Token Usage answers
      "$/completed-task"
      only, never "total fleet spend" (use the Accounts panel or a real balance check for that); (b) decide (operator
      call, not a unilateral agent decision) whether review-agent activity should get its OWN lightweight per-turn
      ledger entry (not a fake "task") so its real cost becomes independently visible/attributable, or whether this is
      accepted as out-of-scope forever. Flash's own smaller residual gap (~$2.35, no review-role slots) is NOT yet
      explained by this mechanism — separate, smaller, still-open sub-question. **Resolved 2026-08-06**: part (a) was
      already satisfied by TaskUsageWindowsPanel's existing in-UI hint ("Completed tasks only... See the Accounts panel
      for real-time per-account totals instead"); part (b) — operator ruled 2026-08-06: "orchestrator and review agent
      spend yes we should track separately but not as per-task breakdowns" — implemented via todo 20, not a fake task
      row. Correction: the earlier "4 slots are persistent review agents" claim in this todo's own body was itself wrong
      — see the 2026-08-06 Progress Log correction below (only ONE real persistent review agent exists fleet-wide, off
      the numbered slots entirely; `slot_role='review'` on slots #1/#8/#10/#12 is a worker craft/skill tag for
      task-dispatch routing, unrelated to agent persistence).
- [x] 20. ✅ [BACKEND] [UI] P2. **DeepSeek Wallet Reconciliation — worker/orchestrator/review spend split + operator
      top-up tracking + human-usage-outside-AO residual**, implementing todo 19(b)'s operator ruling. New
      `deepseek_topups` table (operator-recorded real top-up events, audit-trail-only, never overwritten) + a nullable
      `slot_id` on `deepseek_message_usage` (backfills naturally as the poller re-sweeps);
      `compute_deepseek_wallet_     reconciliation()` splits attributed spend by `slot_id` (0=orchestrator,
      `config.review_slot_ids()`=review, everything else=worker) and computes
      `real_total_spend = known_topups − current_balance`, `residual =     real_total_spend − attributed_total` —
      deliberately `None` (not a misleading 0) until at least one top-up is recorded. New `DeepSeekWalletPanel.tsx`
      (table + a top-up-entry form) mounted on the dashboard next to each `TaskUsageWindowsPanel`. 6 backend pytest + 7
      frontend vitest + 2 Playwright e2e (one caught a real autoflush-off bug: the POST route's same-session re-read
      didn't see its own just-inserted row without an explicit `session.flush()` — fixed, this codebase runs with
      autoflush off everywhere) — all green; full QG green (2464 backend / 212 frontend). Landed
      `agent-orchestrator@0c5fb6e` (+ 4 of the new files landed in a neighboring concurrent-session commit
      `agent-orchestrator@e430623` due to a shared-checkout staging race — see Progress Log; no work lost, both pushed,
      `ahead=0`). Deployed live (VM `i-0c9b283b31d6b5ca7`, confirmed `HEAD=0c5fb6e` + `systemctl is-active`=active).
      **Live-verified against the operator's real $105 top-up**:
      balance $30.25 → real total spend
      $74.75; attributed (worker-bucket only — `slot_id` backfill still pending
      the next poller sweep) $67.67;
      **residual $7.08 — matches the operator's own ~$5 non-AO-chat estimate, well inside the stated
      $10 tolerance**. **Follow-up bug found + fixed same day, `agent-orchestrator@8385728`**:
      operator asked "where is the orchestrator/review spend" — investigation found slot 0's real transcripts live
      under `main_agent_keeper.MAIN_SESSION_NAME` ("orch-agent-main"), never under "orch-slot-0" (which doesn't exist
      on disk — confirmed live) — the sweep was searching the wrong directory, so `orchestrator_spend_usd` was
      STRUCTURALLY unreachable (not just pending backfill) until fixed. Same bug shape as
      `test_slot_view_main_session_liveness.py`'s earlier, unrelated fix. Review (slot_id in
      `config.review_slot_ids()`) had no such bug — `orch-slot-2` is a real directory — it was genuinely just
      pending its next sweep. New regression test
      `test_sweep_looks_up_slot_zero_via_main_session_name_not_orch_slot_zero`. QG green (2465/212), deployed live
      (confirmed `HEAD=8385728` + active). Also resolved live: CI-escalation ("cicd" role) work dispatches onto a
      real borrowed numbered slot (`server/escalation.py`'s `slot_id` plumbing through `do_spawn`/claim), so its
      DeepSeek spend IS captured by the normal per-slot sweep and lands in the "worker" bucket — it is NOT part of
      the residual, and is not a separate invisible category. The residual is genuinely isolated to spend from a
      `claude` session run entirely outside every tracked slot/main-agent transcript directory (manual chats) —
      once the orchestrator/review buckets finish backfilling (self-corrects as those sessions' transcripts grow
      and get re-swept), today's $67.67
      "worker" total will redistribute into worker/orchestrator/review without changing the $7.08 residual figure itself
      (attributed_total is invariant under that redistribution).

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
- **2026-08-05 21:04 UTC — split confirmed live; ratio-skew finding**: re-queried `state.db`'s real table
  (`data/state/state.db`, NOT `data/agent_orchestrator.db`/`data/orchestrator.db` — both exist on the VM but are empty;
  a future session re-running this check should go straight to `state/state.db`). Confirmed 2 completed
  `deepseek-v4-flash` task_usage rows and 22 `deepseek_spawn_selected` events choosing flash vs only 2 choosing pro in
  the ~23min window since the first flash selection (`20:41:33`-`21:04`) — a real, measured 22:2 skew, not 50/50. **Root
  cause (read directly from the deployed `autospawn.py`, lines ~1348-1386)**:
  `wants_flash = _deepseek_flash_should_route(...)` only controls whether the code tries the FLASH-filtered sub-pool
  FIRST; when `wants_flash` is `False`, there is no symmetric "prefer pro" branch — it falls straight into the same
  unfiltered `_pick_headroom_account(provider="deepseek")` call used as the `wants_flash=True` branch's own fallback.
  Because DeepSeek accounts never populate `five_hour_pct`/`weekly_pct` (`_account_has_headroom` treats this as "always
  has headroom" by design), the unfiltered picker's sort key degenerates to `(0, 0, active_slot_count)` — i.e.
  **whichever DeepSeek account currently has fewer active slots wins the unfiltered pick**, regardless of `wants_flash`.
  A freshly-seeded flash account starts at zero active slots, so both the `wants_flash=True` path AND most
  `wants_flash=False` picks (which land here with no variant preference at all) currently resolve to flash until slot
  counts even out. **Not a bug that blocks the test** — both arms are still receiving real, valid dispatches, which is
  the actual requirement — but it means `deepseek_flash_route_fraction=0.5` should NOT be read as "50% of outcomes,"
  it's closer to "at least 50% preference, further amplified by a least-loaded tie-break until slot counts converge."
  Relevant to todo 2 (a unit test asserting a strict alternating 50/50 on `_deepseek_flash_should_route` alone would
  pass while still missing this real-world skew — the test should exercise the full `select_account_for_spawn` path, not
  just the accumulator helper) and to todo 9 (expect unequal sample sizes between pools; that's fine to report, not
  something to force into balance).
- **2026-08-05 23:04-23:16 UTC — per-turn/per-task metrics shipped; live spend_usd repair applied**: operator asked (via
  a screenshot of the Accounts panel) for avg turns/task, context/task, and cache-read/write/output/input tokens per
  turn with real
  $ values on both usage panels — shipped as `agent-orchestrator@fff23c5` (todo 14). While building it,
  the operator separately flagged the Task Token Usage panel's Spend/Avg-$/task
  columns rendering blank for real traffic — root-caused to a `<synthetic>` transcript-turn marker (Claude Code's own
  locally-generated message stub, never sent to any provider) having no price-table entry, which poisoned `spend_usd` to
  `None` for the WHOLE task/ window it fell in (todo 15). Fixed in the same ship; then ran
  `repair_unpriced_deepseek_spend.py` live via SSM (todo 16): dry-run showed 618/618 `deepseek_message_usage` rows
  repairable (pure DB, no I/O) and 23/1000 `task_usage` rows repairable — the other 977 are Anthropic-subscription rows
  that never had a registered price to begin with (not a bug; `TaskUsageRow`'s own docstring already documents this),
  and 23 matches EXACTLY the 13 pro + 10 flash null-spend rows found earlier in this same session's investigation.
  Applied live — see next entry for the post-apply count. Separately, reviewing the Fleet table for this same screenshot
  surfaced todo 17 (harness-tier "sonnet" label is meaningless/misleading next to the DEEPSEEK provider badge;
  pro-vs-flash doesn't surface on the Fleet table at all) — filed as a tracked todo, not started, real remaining UI work
  on a different surface than todo 14's usage panels.
- **2026-08-05 ~23:17 UTC — deploy + repair-apply verification pending**: `ao-self-pull.sh` hit the SAME dirty-gate
  class as todo 6 (`ao_self_pull_stalled_by_untracked_backup_files_2026_07_29`) — this time an untracked, 0-byte
  `data/agent_orchestrator.db` file, traced to this SAME session's own earlier `sqlite3.connect()` DB-discovery script
  (SQLite auto-creates an empty file on connect to a nonexistent path — a side effect of read-only-INTENDED exploration,
  not a real artifact). Deleted, deploy proceeded clean; `systemctl restart orchestrator` then failed under the
  `sudo -u ubuntu` wrapper (needs root, not the ubuntu user) — retried as root directly, confirmed `HEAD=fff23c5` +
  `systemctl is-active`→`active`. Repair script `--apply` run immediately after; result being verified now — see the
  next Progress Log entry (or this plan's Deferred table if not yet closed out) for the actual post-apply row counts.
- **context-scout 2026-08-06**: trimmed context_scope from 12 to 6 entries (was over the 2-6 MVI budget) — dropped
  `server/accounts.py`/`deepseek_usage_poller.py`/`models/accounts.py`/`models/backlog.py`/`state_store/slots.py`/
  `dashboard/src/layout.tsx` (already-shipped-work surfaces, one-hop-reachable from kept files) and
  `scripts/orchestrator/repair_unpriced_deepseek_spend.py` (**confirmed deleted from disk** per todo 16 — was a stale
  dead reference); added `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md` (already self-cited
  twice in this doc's own Codex SSOTs/related but missing from context_scope).
- **2026-08-06 — cross-account
  $ contamination found + fixed (todo 18)**: operator flagged, from a live dashboard
  screenshot, that the Accounts panel's pro/flash lifetime $
  totals didn't add up to each other or to Task Token Usage. Investigation (direct SQL against `state.db`, not guessed)
  found `_sweep_account` had NO filter checking a found message's own `model` against the account being swept — it
  attributed EVERYTHING it found to whichever account was currently running, live numbers: 4,964 flash-model messages
  ($4.60) inside pro's own ledger, 573
  pro-model messages ($1.08) inside flash's. A SECOND, compounding bug:
  `ProcessedTranscriptRow`'s fingerprint cache was keyed by `file_path` alone — a GLOBAL cache shared across every
  deepseek account — so whichever account's sweep touched a file FIRST silently starved every OTHER account's later
  sweep of that same unchanged file, even once a model filter would otherwise correctly separate them. Fixed both
  (model-match filter + per-account composite-PK fingerprint scoping) plus a one-time self-healing purge migration,
  shipped `agent-orchestrator@fadc74b`, deployed live, verified: `REMAINING_CROSS_ATTRIBUTED_ROWS=0`; pro's ledger now
  shows ONLY `deepseek-v4-pro` messages ($59.95)
  - `<synthetic>` ($0); flash's ledger now shows ONLY `deepseek-v4-flash` messages ($1.23). **Remaining gap noted but
    misdiagnosed in this same entry, corrected below**: Accounts-panel sum still exceeded Task Token Usage's sum;
    claimed at the time this was the "in-progress work" distinction — that claim was WRONG, see the next entry. Side
    effect during shipping: full QG caught a stale `.venv` in this checkout (msgpack/pip/pyasn1/setuptools all several
    patch versions behind an ALREADY-fixed `uv.lock` — `uv sync` resolved it; not a new vulnerability,
    `cve_affected_pinned_deps_remediation_2026_06_18.md` already tracks the fleet-wide effort this was part of).
- **2026-08-06 — correction + real ground-truth validation (todo 19 filed)**: operator pushed back on the "in-progress
  work" explanation above — correctly. Measured it directly: total spend across every CURRENTLY-working DeepSeek slot
  was $0.47, nowhere near the ~$23 gap. That explanation was wrong and is retracted. Real cause: 4 of pro's slots
  (`#1/#8/#10/#12`) are persistent REVIEW agents, not backlog workers — they never call `/done`, so `task_usage` never
  sees their real, ongoing spend (not delayed — permanently absent by construction). Confirmed via turn counts: pro
  logged 27,213 real turns, only 19,589 map to a completed task, a 7,624-turn gap concentrated in exactly those 4 slots.
  Operator then supplied REAL ground truth: exact $105 top-up, ~$5 estimated non-AO manual chat usage. Live balance
  check at reconciliation time: $31.54 remaining → real total spend $73.46 →
  ~$68.46 expected
  AO-attributable. Accounts panel (post-fix): $66.41, diff
  −$2.05 — **a genuine match, independently validating the
  cross-attribution fix against real DeepSeek billing, not just internal consistency.** Task Token Usage: $43.35,
  diff
  −$25.11 — confirmed real, explained by the review-agent finding, not tolerance noise. Filed todo 19 (doc + operator
  decision on whether review-agent spend should get its own visible ledger entry); flash's own smaller residual gap
  (~$2.35,
  no review-role slots) remains unexplained, separate open question.
- **2026-08-06 — correction to the todo-19 "4 review-agent slots" claim, then todo 19+20 shipped**: operator asked
  directly what the fleet's real persistent-agent roles are. Queried live `AgentRow` data — the "slots #1/#8/#10/#12 are
  persistent review agents" claim in todo 19 was WRONG: those slots have real, substantial `task_usage` rows (112/65/87
  completed tasks) — they're normal backlog workers whose `slot_role='review'` is a worker craft/skill tag for
  task-dispatch routing (matches an `agents/review.md` persona), unrelated to `AgentRow.role` (the actual
  persistent-agent classification). Corrected to the operator; retracted in todo 19's own body above. The REAL taxonomy:
  persistent roles are `main` (orchestrator) and `review` (the one real persistent review agent, confirmed running on
  host `ip-172-31-5-118`, off the numbered slots entirely), plus `plan_reconciler` and a `custom` bucket for
  auto-triggered skill-agents (`cicd`, `docs_reconciler`, `conflict_resolver`, `data_pipeline_failure`,
  `context_scout_auditor`, `na_eligibility_auditor`, `ag_closeout_auditor`, `plan_health`). Operator then ruled on todo
  19(b): "orchestrator and review agent spend yes we should track separately but not as per-task breakdowns... the
  residual gap is human work, which can be derived from the difference in actual spend... across the entire deepseek pro
  and flash API... that residual can also be tracked in the UI." Shipped as todo 20 (see above for the full
  implementation + evidence). Live-verified against the operator's real $105 top-up: residual $7.08, matching the
  operator's own ~$5 non-AO estimate within the
  stated $10 tolerance — a second independent validation of both the
  cross-attribution fix (todo 18) and this new feature against real DeepSeek billing. One caveat carried forward:
  orchestrator/review spend currently reads $0 live because `slot_id` is a newly-added nullable column that only
  backfills as `DeepSeekUsagePoller` naturally re-sweeps existing transcripts (`merge()`); everything defaults to the
  worker bucket until that next sweep cycle.
- **2026-08-06 — orchestrator-spend bug found + fixed same day (`agent-orchestrator@8385728`)**: operator followed up
  asking where the orchestrator/review split actually shows up, whether CI escalations count as tasks, and whether the
  $7.08 residual is purely manual chats or also includes orchestrator/review/CI. Investigated live rather than
  guessing: `~/.claude-configs/orch-slot-0` does not exist on the orchestrator VM — the main agent's real transcripts
  live under `main_agent_keeper.MAIN_SESSION_NAME` ("orch-agent-main"). The sweep's `find_slot_transcripts(f"orch-
  slot-{slot_id}")` call was unconditional, so slot 0 was searching a directory that never existed —
  `orchestrator_spend_usd` could never be anything but $0,
  not merely pending backfill. Same bug shape as an earlier, unrelated fix (`test_slot_view_main_session_liveness.py`,
  2026-07-28) — that fix covered slot-liveness display, not the DeepSeek sweep, so this exact directory mismatch
  survived in a second place. Fixed: slot 0 now resolves to `MAIN_SESSION_NAME`; every other slot unchanged. Verified
  `orch-slot-2` (review) IS a real directory with real transcripts — no bug there, genuinely just pending its next sweep
  (self-corrects once that session's transcript file next grows). Separately confirmed CI-escalation ("cicd" role)
  dispatches run on a real borrowed numbered slot (`escalation.py`'s `slot_id` plumbing), so their spend already lands
  correctly in the "worker" bucket via the normal per-slot sweep — not a hidden third category, not part of the
  residual. New regression test proves slot 0 is never searched via "orch-slot-0". QG green (2465 backend/212 frontend),
  deployed live, confirmed `HEAD=8385728` + `systemctl is-active`=active.

## Deferred work after 2026-08-05

| Item                                                                                                                                                   | State / why deferred                                                                                                                                                                                | Blocked on                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Todo 2 — unit test proving the ~50/50 pro/flash split ratio + reproducibility                                                                          | **Not done** — real work, nobody's turn to wait on                                                                                                                                                  | Nothing — pick up directly                                        |
| Todo 4 — Playwright regression spec for the new filter toggle                                                                                          | **Not done** — real work                                                                                                                                                                            | Nothing — pick up directly                                        |
| Todo 8 — let the split run ~24h before drawing conclusions                                                                                             | **Cannot be done yet** — needs real elapsed time, not work. Clock starts `20:41:33` (first real flash selection), not the earlier deploy time — target check-in ≈`2026-08-06 20:41 UTC`             | Elapsed time                                                      |
| Todos 9-11 — post-window cost comparison, quality audit, review-agent coverage check                                                                   | **Cannot be done yet** — all depend on todo 8's 24h window closing                                                                                                                                  | Todo 8                                                            |
| Todo 12 — decide whether review-agent findings become a structured event                                                                               | **Operator-owned** — a product/process decision, not something to start unprompted                                                                                                                  | Operator                                                          |
| Todo 13 — final verdict + archive                                                                                                                      | **Cannot be done yet** — depends on todos 9-11                                                                                                                                                      | Todos 9-11                                                        |
| Todo 17b — unverified thinking-flag meaning for DeepSeek slots (17a done — pro/flash variant now shown)                                                | **Not done** — real work, needs investigation into whether DeepSeek's API honors the thinking param at all                                                                                          | Nothing — pick up directly                                        |
| Flash's own ~$2.35 residual real-time-vs-task-usage gap (no review-role slots involved)                                                                | **Not done** — root cause genuinely unknown, don't guess; needs the same kind of direct investigation todo 19's pro finding got                                                                     | Nothing — pick up directly                                        |
| Confirm orchestrator/review buckets actually populate non-zero after the `orch-slot-0` fix (todo 20's follow-up)                                       | **Cannot be done yet** — needs the next `DeepSeekUsagePoller` sweep tick (600s) to touch each session's now-fixed/still-growing transcript; check the live wallet-reconciliation numbers after that | Elapsed time (~1 poller tick)                                     |
| `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`'s own todos (confirm systemic, strengthen worker prompt, turn-count circuit breaker) | **Not done** — real work, separate issue doc, not blocking this plan                                                                                                                                | Nothing — pick up directly, independent of this plan's 24h window |

**Recommended next item**: nothing until todo 8's window closes (≈`2026-08-06 20:41 UTC`, 24h from the first real flash
selection). Do not re-poll the fleet for the A/B split itself in the meantime — todo 7 already confirmed the mechanism
works; further early checks just burn an SSM round-trip without changing the answer to anything actionable yet. Todo 17
(Fleet-table label fix) is real, standalone work that could be picked up independently of the 24h wait if there's
appetite for it.
