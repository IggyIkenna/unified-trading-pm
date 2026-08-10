---
doc_type: plan
title:
  Anthropic per-task actual spend — measured subscription multiplier, per-account attribution, and task_usage repricing
summary:
  The task-usage dashboard's $ column is blank for 1,993 of 2,622 completed task_usage rows (100% of Anthropic rows)
  because `deepseek_usage._PRICE_PER_MILLION` only ever held DeepSeek entries, and one unpriced turn nulls a whole
  window by design. This plan makes Anthropic usage report ACTUAL per-task spend instead of Anthropic's opaque
  percent-of-weekly-limit — by pricing turns at documented API list rates and dividing by a subscription value
  multiplier that is MEASURED per account from a fully-consumed weekly window, never assumed. A first calibration pass
  (2026-08-10) returned 3x-107x across five accounts, which is not a usable answer — it exposed two upstream attribution
  defects (task_usage double-counts overlapping/whole-session windows; transcript attribution loses post-compaction
  sessions) that must be fixed before any multiplier is trustworthy. Also adds the per-account filter axis the
  calibration needs, and reprices the historical rows.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, billing, cost-attribution, pricing, anthropic, calibration, task-usage, dashboard]
related:
  [
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md,
    /plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md,
  ]
created: "2026-08-10"
last_updated: 2026-08-10
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: backend_engineer
effort: xhigh
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/server/accounts.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/scripts/orchestrator/backfill_task_usage.py,
    agent-orchestrator/scripts/orchestrator/measure-claude-usage-value.py,
    agent-orchestrator/dashboard/src/TaskUsageWindows.tsx,
  ]
supersedes:
superseded_by:
depends_on:
source: operator-request 2026-08-10 (interactive session — "why do these tasks sometimes not have $ amounts")
---

# Anthropic per-task actual spend — measured multiplier, per-account attribution, repricing

> **Goal in one line**: every completed task carries a real dollar cost, for Anthropic as well as DeepSeek, derived from
> what we actually pay — so cost-per-task is comparable across providers and Anthropic's percent-of-weekly-limit becomes
> a supplementary signal rather than the only one.

**Why `sequential: true`**: the phases are a genuine dependency chain (fix attribution -> measure multiplier -> price
with it -> reprice history), and most todos touch the same three files (`model_pricing.py`, `deepseek_usage.py`,
`state_store/slots.py`), so the default intra-plan concurrency would collide on the same-file rule.

**No Anthropic API access is required anywhere in this plan** (operator question 2026-08-10): rates are a static table,
usage comes from local transcripts + `state.db`, attribution comes from `agents.account_id`. A DeepSeek-backed worker
can execute every todo unauthenticated.

Codex SSOTs this plan references (do not duplicate their content here): `/codex/06-coding-standards/quality-gates.md`,
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`/codex/04-architecture/runtime-deployment-topology.md`.

## Measured starting state (2026-08-10, live `state.db`, read-only via SSM)

- `task_usage`: 2,622 rows, **1,993 unpriced** (`spend_usd IS NULL`). 100% of Anthropic rows (1,993 incl. provider-null
  historical), 1 of 630 DeepSeek rows.
- The single unpriced DeepSeek row (`infra_satellite_ao_dispatch_batch7_finalize-003`, slot 15, backfilled) is what
  blanked the operator's DeepSeek+Planning 5h/24h/7d/lifetime cells while 1h still showed `$1.6886`.
- `task_usage.account_id` is **100% populated for Anthropic** (1,005/1,005) from 2026-08-06 onward — per-account
  attribution needs no new capture path.
- Account registry: 5x `max20` ($200/mo) + 1x `pro` ($20/mo, `sub-a-ikenna`) + 2 DeepSeek `api` accounts.
- Live model vocabulary (411 transcripts, all 40 slot config dirs): `claude-sonnet-5`, `claude-opus-4-8`,
  `claude-sonnet-4-6`, `deepseek-v4-pro`, `deepseek-v4-flash`, `<synthetic>`, and a bare `sonnet` alias (68 turns).
- Every cache write in the sample is **1h TTL** (`ephemeral_5m_input_tokens` = 0 across 17,446+ turns), so the 2.0x
  cache-write tier is the one that matters, not 1.25x.

## Todos

- [ ] [BACKEND] P0. **TIME-CRITICAL — start snapshotting the account usage meters to a history table now; every hour of
      delay permanently loses 5-hour windows.** `account_usage` is keyed by `account_id` alone (8 rows, 8 accounts —
      verified 2026-08-10), so it holds CURRENT STATE ONLY: every past weekly and 5-hour window is already
      unrecoverable, leaving exactly one weekly observation per account and zero historical 5h observations. Persist
      `weekly_pct`, `weekly_window_start`, `five_hour_pct`, `five_hour_window_start`, `representative_claim`,
      `overage_status`, `account_status` on a cadence at least twice per 5-hour window, keyed
      `(account_id, sampled_at)`. Independent of every other todo — do not let the attribution work delay it. **Done
      when**: the table exists on the live VM, a query shows >= 2 distinct `sampled_at` rows per active account, and the
      sampler survives an orchestrator restart.
- [ ] [BACKEND] P0. **Build a slot-to-account-over-time attribution map in `server/` so any transcript turn resolves to
      the account that owned its slot at that timestamp.** Current attribution has no correct path:
      `agents.claude_session_id` holds only the CURRENT session id, so compaction mints a new id and orphans every
      earlier transcript (measured: `sub-c-ikenna-odum` shows 274 completed tasks but only 1,723 resolvable turns,
      ~6/task, against 503-turn tasks visible in the same DB). Derive intervals from `AgentRow` (`account_id`,
      `tmux_session`/`last_tmux_session`, `registered_at`, `finished_at`) and assign each turn by its own timestamp.
      **Done when**: a unit test proves a turn in a post-compaction transcript still attributes to the correct account,
      and the resolver returns the same account for two sessions of one agent split by a compaction.
- [ ] [BACKEND] P0. **Add a globally `message.id`-deduped transcript walker so one turn is counted exactly once per
      account-window, regardless of how many files or task windows contain it.** `scan_session_usage` already dedups
      within one file; the account-level aggregate needs dedup ACROSS files (resume/replay copies the same turns into a
      second transcript — `measure-claude-usage-value.py`'s own docstring records 588,821 duplicate turns against
      649,255 real ones on this VM, ~47%). **Done when**: a test with the same `message.id` present in two transcript
      files under one account yields one counted turn, and the walker's total for a known window matches a hand-verified
      count.
- [ ] [BACKEND] P0. **Fix `task_usage` double-counting: a typed one-off with `assigned_at=None` bills the WHOLE session,
      and overlapping per-task windows on one slot bill the same turns to several tasks.** This corrupts per-task cost
      independently of pricing and is why the task_usage-derived multiplier reads HIGHER than the transcript-derived one
      for 4 of 5 accounts, despite being a strict subset of the same turns. Decide and implement one attribution rule
      (proposed: a turn belongs to exactly one task — the task whose window contains it, earliest-assigned wins on
      overlap) in `deepseek_usage.build_task_usage_snapshot` and the `/done` capture path. **Done when**: a regression
      test with two overlapping task windows on one slot proves each turn is counted once, and re-running the
      calibration shows method (A) no longer exceeding method (B).
- [ ] [REVIEW] P0. **Quantify the double-count blast radius on the live DB before repricing anything — report how many
      existing `task_usage` rows overlap another row on the same slot, and the token volume involved.** Read-only via
      `scripts/orchestrator/query-ao-state-db-readonly.sh`. This decides whether historical rows can be repriced in
      place or must be recomputed from transcripts. **Done when**: the query output is pasted into this plan's Progress
      Log with an explicit in-place-vs-recompute recommendation.
- [ ] [BACKEND] P1. **Land `server/model_pricing.py` as the single pricing SSOT — date-effective list rates, per-tier
      cache-write rates, alias resolution — and delete the DeepSeek-only `_PRICE_PER_MILLION` from
      `deepseek_usage.py`.** Rates must carry validity windows (Claude Sonnet 5's intro $2/$10 expires 2026-08-31,
      standard $3/$15; it dominates fleet turn volume, so a flat rate is ~33% wrong on one side of that date) and a turn
      is priced at the rate in force at its OWN timestamp so history never re-prices. Register the bare `sonnet` alias
      to `claude-sonnet-5` per CLAUDE.md's model-tier rule; do NOT register `opus`/`haiku` aliases (no fleet turn emits
      them and the generation would be a guess). **Done when**: `bash scripts/quality-gates.sh` is green in
      `agent-orchestrator/` and a test asserts no two price windows for one model overlap.
- [ ] [BACKEND] P1. **Parse the `usage.cache_creation` 5m/1h split in `scan_session_usage` and price cache writes at
      1.25x / 2.0x input instead of the flat cache-miss rate.** The field is always a dict on this fleet
      (`ephemeral_5m_input_tokens` / `ephemeral_1h_input_tokens`, confirmed across 17,446 turns), so this is exact, not
      an approximation; DeepSeek has no cache-write premium and must keep billing cache-creation at its miss rate.
      **Done when**: a test proves an Anthropic 1h-TTL cache write bills at 2.0x input and a DeepSeek cache write bills
      at 1.0x, and the existing `test_deepseek_usage.py` assertions stay green.
- [ ] [SCRIPT] P1. **Ship `scripts/orchestrator/calibrate_account_value.py` — measure each account's subscription value
      multiplier from a fully-consumed weekly window.** Method: for an account at `weekly_pct=100`, sum every attributed
      turn in `[weekly_window_start, reset]` (using the todo-1/todo-2 attribution + dedup), price at list rates per
      model, and report `list_value / weekly_subscription_cost`. Must report per-model breakdown (Opus/Sonnet/4.6 have
      different rates and different quota weights), value at BOTH the Sonnet-5 intro and standard rate, and the
      published sanity band (max20 ~6-10x, pro ~3-6x) as a check, never as an input. Read-only; carries the
      `# Epic:`/`# Lifecycle:` markers per `/codex/06-coding-standards/script-homes.md`. **Done when**: the script runs
      against the live DB read-only and its per-account output is pasted into the Progress Log.
- [ ] [OPERATOR] P1. **Run the calibration across every `weekly_pct=100` account and record the measured multipliers,
      explicitly excluding `sub-a-ikenna`.** That account is tier `pro`, not `max20` (operator ruling 2026-08-10: it
      switched to Pro and would confuse the Max calibration). Safe-idempotent justification for the `[OPERATOR]` tag:
      the run is strictly read-only (SQLite `mode=ro` + transcript reads), writes nothing, and launches no VM — it is
      tagged `[OPERATOR]` only because interpreting whether a measured multiplier is credible is a judgment call, not
      because the action is risky. **Done when**: a measured multiplier per max20 account is recorded here with its
      window, and any account whose two attribution methods still disagree by >20% is named as unresolved.
- [ ] [BACKEND] P1. **Store the measured per-account multiplier as data (not a hardcoded constant) and derive effective
      spend as `list_value / multiplier`.** A multiplier must record which window measured it and when, so a stale one
      is visible rather than silently authoritative; an account with no measurement yet must fall back to a
      clearly-labelled default rather than silently pricing at list. **Done when**: a test proves an account with no
      recorded multiplier is flagged rather than priced as if the multiplier were 1.0.
- [ ] [BACKEND] P2. **Add an `account_id` filter axis to `window_task_usage_totals` and
      `GET /api/backlog/usage/windows`, composing AND-wise with the existing provider/model/role_group filters.**
      Per-account totals must sum to the provider total exactly as DeepSeek Pro+Flash already sum to DeepSeek. **Done
      when**: a test asserts the per-account sums equal the provider-scoped total for the same window, and the endpoint
      returns per-account rows.
- [ ] [UI] P2. **Add per-account filter buttons to `TaskUsageWindows.tsx` as a third independent filter row, alongside
      the existing provider and role-group rows.** Labels come from the accounts registry (`label`/`account_id`), not
      hardcoded. **Done when**: `[UI]` + `pw:L2 ✓` with a cited regression spec under `dashboard/tests/e2e/`, per
      `/codex/06-coding-standards/ui-testing-layers.md`.
- [ ] [UI] P2. **Surface the spend basis in the task-usage panel so a DeepSeek dollar (metered) and an Anthropic dollar
      (subscription-attributed at a measured multiplier) are distinguishable, and keep Anthropic's
      percent-of-weekly-limit visible alongside it.** Operator intent 2026-08-10: Anthropic becomes actual spend, the
      percent stays as a supplementary signal rather than the only one. **Done when**: `pw:L2 ✓` with a spec asserting
      both the $ figure and the basis indicator render for an Anthropic-scoped window.
- [ ] [SCRIPT] P2. **Ship `scripts/orchestrator/reprice_task_usage.py` — recompute `spend_usd` for every row where it is
      NULL, transcript-accurate where the transcript survives and flagged-approximate where it has rotated.** Dry-run by
      default, `--apply` to write, idempotent, mirroring `backfill_task_usage.py`'s structure and provenance
      conventions. Must report exact/approximate/still-unpriced counts and name any model string it could not price.
      **Done when**: a dry run against the live DB reports a per-model coverage breakdown and the script has a
      regression test for the approximate-fallback path.
- [ ] [OPERATOR] P2. **Run `reprice_task_usage.py --apply` against the live orchestrator VM via SSM after reviewing the
      dry-run report.** Tagged `[OPERATOR]` because it mutates ~1,993 live production rows; mirrors the established
      precedent of `deepseek_flash_ab_routing_test_2026_08_05.md` todo 16's `repair_unpriced_deepseek_spend.py --apply`.
      Not a delete — it fills NULL columns only and is re-runnable. **Done when**: a post-run query showing the
      remaining `spend_usd IS NULL` count (and the reason for any residual) is pasted into the Progress Log.
- [ ] [REVIEW] P2. **Verify the operator's original symptom is gone: the DeepSeek + Planning filter must show a dollar
      figure for 1h, 5h, 24h, 7d and lifetime.** That was one backfilled mixed-model row poisoning four windows. **Done
      when**: the live endpoint response for `provider=deepseek&role_group=planning` is pasted here showing a non-null
      `spend_usd` in every window.
- [ ] [BACKEND] P1. **Gate the calibration set to windows fully inside the `account_id` capture era and require >= 98%
      meter consumption; treat every other window as a LOWER BOUND, never a measurement.** Consuming fraction `p` of an
      entitlement yields `p x M`, so a partial window cannot measure the multiplier (operator ruling 2026-08-10).
      Capture began ~2026-08-06, so `sub-e-odum2default`'s window (opens 2026-08-05 23:00) is structurally undercounted
      and must be excluded — this, not double-counting, is the leading explanation for the 6x list-value spread across
      four identically-entitled max20 accounts. **Done when**: the calibration script refuses to emit a multiplier for a
      sub-98% or partially-captured window, labelling it a lower bound instead, with a test covering both rejection
      paths.
- [ ] [BACKEND] P1. **Calibrate the 5-hour meter as its own track, and record which meter was BINDING for each window.**
      `representative_claim` shows 5 of 6 accounts are `five_hour`-bound and only `sub-c-ikenna-odum` is
      `seven_day`-bound (2026-08-10), so weekly-only calibration measures the non-binding constraint for most accounts.
      5h windows reset ~33x more often than weekly, so once the sampler from todo 1 has run they are the far better
      statistical surface. Depends on todo 1 — there is no retroactive 5h data. **Done when**: a per-account 5h
      multiplier is reported from >= 3 fully-consumed 5h windows and compared against that account's weekly multiplier,
      with any divergence stated rather than averaged away.
- [ ] [DATA] P2. **Determine whether the quota meter weights models differently from list pricing, and stop treating the
      multiplier as a scalar if it does.** The `weekly_sonnet_pct` / `weekly_sonnet_msgs_used` sub-meter exists in
      schema but is NULL/0 on every account (verified 2026-08-10), so there is currently NO per-model quota signal — a
      single multiplier is unvalidated against model mix, and our five sampled accounts had materially different mixes
      (opus-4-8 + sonnet-4-6 vs near-pure sonnet-5). Either populate the sub-meter from `claude /usage`, or infer
      per-model quota weights by solving across many (window, mix, consumed-pct) observations once todo 1 supplies them.
      **Done when**: either per-model weights are reported with their residuals, or the evidence that a single scalar is
      adequate is recorded explicitly.
- [ ] [DATA] P2. **Quantify how sensitive the measured multiplier is to cache-read share, since ~78% of our list-priced
      value is cache reads.** If Anthropic's quota meter discounts cache reads relative to list pricing, the multiplier
      is a property of the WORKLOAD's cache profile rather than of the account or tier, and would not transfer to a
      differently-shaped workload. Regress measured multiplier against cache-read share of tokens across all calibrated
      windows. **Done when**: the correlation is reported, and if material, the multiplier is redefined over a
      cache-read-adjusted base rather than raw list value.
- [ ] [DATA] P3. **Detect account tier changes over history rather than applying today's tier retroactively.**
      `sub-a-ikenna` is currently `pro`; if it was Max earlier, every historical window priced against a $20/mo cost is
      wrong. **Done when**: either a tier-change timeline is reconstructed from available evidence, or windows preceding
      the earliest confirmed tier are excluded from calibration and that exclusion is recorded.
- [ ] [BACKEND] P3. **Exclude usage-probe replay turns from value while still counting their real turns toward quota.**
      `measure-claude-usage-value.py`'s docstring records 588,821 duplicate turns against 649,255 real ones (~47%) on
      this VM, caused by probe sessions replaying a resumed session's prior turns into their own transcript — those
      replayed turns were never re-billed and must not inflate list value, but the probe's own genuine turns do consume
      quota. **Done when**: a test proves a replayed turn is excluded from value and a probe's own turn is retained, and
      the calibrated totals change in the expected direction.
- [ ] [DATA] P3. **Write the codex SSOT for cost attribution — pricing basis, the measured-multiplier method, the
      weekly-window calibration procedure, and the attribution rules from todos 1-3 — under `/codex/04-architecture/`.**
      Per CLAUDE.md's SSOT-direction hard rule the durable contract belongs in codex, not in this plan. **Done when**:
      the doc exists with `authoritative_for:` frontmatter and this plan links to it rather than restating it.
- [ ] [REVIEW] P3. **Re-run the calibration after the attribution fixes land and compare against the 2026-08-10 baseline
      recorded below.** If the multipliers converge into a narrow band per tier, record it; if they stay divergent, open
      an issue doc rather than averaging the spread into a single misleading number. **Done when**: the re-run output is
      recorded here with an explicit converged/not-converged verdict.

## Progress Log

### 2026-08-10 — Diagnosis + first calibration pass (interactive session, read-only)

**Root cause of the blank $ column**: `deepseek_usage._PRICE_PER_MILLION` contained exactly two entries, both DeepSeek.
Every Claude turn priced to `None`, and `state_store.slots.window_task_usage_totals`'s deliberate "any unpriced row
nulls the whole window" rule blanked the aggregate. Not a data gap — a missing price table.

**Live unpriced distribution** (`task_usage`, 2,622 rows):

| provider       | model                     |  rows | unpriced |
| -------------- | ------------------------- | ----: | -------: |
| anthropic/null | `claude-sonnet-5`         | 1,738 |    1,738 |
| anthropic      | `claude-sonnet-4-6`       |   213 |      213 |
| null/anthropic | `claude-opus-4-8`         |    22 |       22 |
| anthropic/null | `<synthetic>`, mislabeled |     8 |        8 |
| deepseek       | `deepseek-v4-pro`         |   505 |        0 |
| deepseek       | `deepseek-v4-flash`       |   125 |        1 |

**First calibration pass** — list-priced value consumed in each fully-consumed weekly window vs subscription cost.
Method (A) = `task_usage` scoped by `account_id`; method (B) = transcripts resolved via `agents.account_id`. Sonnet-5
valued at its standard rate.

| account            | tier  |   (A) |   (B) | published band        |
| ------------------ | ----- | ----: | ----: | --------------------- |
| sub-c-ikenna-odum  | max20 | 46.0x |  4.7x | 6-10x                 |
| sub-d-odum1default | max20 | 34.4x | 18.4x | 6-10x                 |
| sub-f-odum2default | max20 | 22.4x | 23.0x | 6-10x                 |
| sub-e-odum2default | max20 |  7.7x |  3.5x | 6-10x                 |
| sub-a-ikenna       | pro   |  107x | 63.8x | 3-6x (excluded — Pro) |

**Verdict: not a usable multiplier yet.** Method (A) is a strict subset of the same turns as (B) and should be a lower
bound, yet reads higher for 4 of 5 accounts. That inversion isolates the two defects now tracked as todos 1-3:
`task_usage` double-counts (whole-session one-offs + overlapping windows), and transcript attribution silently loses
every pre-compaction session. `sub-f` is the only account where both methods converge (22.4x vs 23.0x), consistent with
it having rotated sessions least. Shipping any multiplier from this spread would bake a 3x-107x error into the cost
column, so the attribution fixes gate the pricing work.

### 2026-08-10 — Calibration feasibility probe (read-only): what data does NOT exist

Follow-up to the operator's question "anything we need to research to avoid an unfair representation, and do we only
measure fully-consumed windows?" — four findings that reshaped the todo list:

1. **No usage-meter history exists.** `account_usage` is keyed by `account_id` alone — 8 rows, 8 distinct accounts,
   current state only. Every past weekly and 5-hour window is unrecoverable, so today there is exactly ONE weekly
   observation per account and ZERO historical 5h observations. Retroactive 5h calibration is impossible; sampling has
   to start now (todo 1) or the same n=1 problem persists indefinitely. This is the most time-critical item in the plan.
2. **Most accounts are 5-hour-bound, not weekly-bound.** `representative_claim`: `five_hour` for sub-a, sub-b, sub-d,
   sub-e, sub-f; `seven_day` only for sub-c. Weekly-only calibration therefore measures the non-binding constraint for 5
   of 6 accounts.
3. **No overage was ever paid** — `overage_status='rejected'` on every account (`out_of_credits` for sub-a/sub-b,
   `org_level_disabled` for sub-c/d/e/f). The subscription price is the full cost for these windows, so the denominator
   of the multiplier needs no overage adjustment. One less confound.
4. **Double-counting is NOT the main driver of the 6x spread.** Measured: only **162 overlapping `task_usage` row
   pairs** (both windows known) and **3 rows with `assigned_at IS NULL`** (2 anthropic, 1 deepseek) doing whole-session
   counting. Against 2,622 rows that is ~6% — real (todo 3 still fixes it) but far too small to explain a 6x spread. The
   leading explanation is **coverage**: `sub-e`'s window opens 2026-08-05 23:00 while `account_id` capture began ~08-06,
   so its first day is structurally missing, and it is precisely the account with the fewest attributed rows (49). This
   is what todo 5's capture-era gate exists to prevent. Partially answers todo 4 — the remaining piece is the token
   volume inside those 162 pairs.

Also unresolved and now tracked: the `weekly_sonnet_pct` sub-meter is NULL/0 on every account, so there is currently no
per-model quota signal to validate a scalar multiplier against (todo 7); and ~78% of our list-priced value is cache
reads, whose quota weighting is unknown (todo 8).

**Incidental findings**: every cache write on this fleet is 1h TTL (`ephemeral_5m_input_tokens` = 0 across 17,446+
sampled turns), so only the 2.0x cache-write tier matters; cache-read volume is enormous (5.2B tokens on `sub-c` in one
week), which is what pushes measured value so far above the published band — nearly free on a subscription, expensive at
list rates. A bare `sonnet` model alias appears on 68 turns and would keep poisoning rows even after the canonical model
ids are registered.
