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
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
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

## Where each piece of work has to run (operator ask 2026-08-10)

| Runs on                    | What                                                                                                                                                                                                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Operator's laptop ONLY** | Anything reading `~/.claude` interactive history or `~/.claude.json` — laptop-side consumption, the local login identity, and any `claude /usage` run against the laptop's account. This data exists on no other machine. Tagged `[OPERATOR]` so AO never tries to dispatch it. |
| **AO VM only**             | The meter-history sampler, calibration over `sub-c/d/e/f`, and any query against the live `state.db` or the VM's per-slot transcripts.                                                                                                                                          |
| **Either (repo work)**     | Price table, attribution fixes, per-account aggregation, dashboard, repricing script, tests — ordinary code a worker can do anywhere.                                                                                                                                           |

The laptop-only items are genuinely small: the laptop's contribution is confined to `sub-b-iggy2london`, so they exist
to quantify and quarantine ONE account, not to feed the main calibration.

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
- [ ] [BACKEND] P1. **Attribute cost by PROPORTIONAL ALLOCATION of the real subscription cost, not by dividing list
      value by a stored multiplier constant.** Formula:
      `task_cost = window_subscription_cost x (task_list_value / total_list_value_in_window)`. This always sums to
      exactly what we paid, needs no constant to maintain, and self-corrects when Anthropic changes rates (numerator and
      denominator move together) — whereas a hardcoded multiplier is workload-dependent and rots. Operator ruling
      2026-08-10 asked whether Max could simply be `list_value / 200`; measurement says ~190x promo / ~212x standard,
      but that ratio is a property of THIS cache-heavy workload (99% of window tokens were cache reads, which are cheap
      at list yet barely move the quota meter), not of the tier — a cache-light workload would measure very differently.
      The denominator MUST include all consumption on that account in the window (AO + laptop), else AO tasks absorb the
      whole subscription and are overstated. **Done when**: per-task costs for one window sum to that window's
      subscription cost within rounding, and a test proves the sum invariant holds when list rates change.
- [ ] [OPERATOR] P0. **Dedicate ONE max20 account to agent-orchestrator exclusively — never log the laptop into it — so
      its meter delta is 100% AO by construction.** Operator constraint 2026-08-10: an AO VM worker has no access to
      `~/.claude` on the laptop, so it can NEVER compute a denominator that includes laptop consumption at runtime.
      Reserving one account removes the entire contamination class permanently: calibration becomes exact and
      repeatable, the multiplier is measured on AO's OWN workload (which is what it will price), and no laptop-to-VM
      data channel is needed. `sub-d-odum1default` is the natural candidate — it has no local account env file and AO
      used it heavily (216 tasks, 08-07 to 08-10). Operator action, not a code change: it needs a human to commit to
      never using that account interactively. **Done when**: the reserved account is named here, recorded in the
      accounts registry comment, and one full weekly window has elapsed with the login sampler showing zero laptop
      sessions on it.
- [ ] [BACKEND] P1. **Given the VM cannot see laptop usage, apply cost via a multiplier MEASURED on an AO-exclusive
      window rather than a runtime denominator that needs both halves.** This supersedes the pure
      proportional-allocation form for the AO runtime path: allocation still holds as the definition, but the VM
      evaluates it using a stored multiplier derived from a window where AO owned the account outright (todo 11), so it
      needs no laptop input. Keep the sum-invariant as a periodic CHECK (recompute allocation offline where both halves
      are known) rather than a runtime requirement. **Done when**: the runtime path prices a task with no laptop data
      available, and an offline check confirms the per-task costs sum to the window's subscription cost within rounding.
- [ ] [OPERATOR] P2. **If no account can be reserved, ship a laptop-to-VM usage export instead — the laptop is the only
      place its own consumption exists.** Fallback for todo 11: extend the laptop sampler to write per-window token
      totals (per model, requestId-deduped) to a VM-readable location, and state plainly that the figure is stale
      whenever the laptop is off. Strictly worse than reservation because it introduces a channel that fails silently.
      **Done when**: either todo 11 is adopted and this is CANCELLED, or the export runs and the VM reads a non-stale
      total.
- [ ] [BACKEND] P2. **Ship per-task cost RANKING before the absolute-dollar question is settled, since the multiplier
      cancels out of any comparison.** Ordering tasks by cost needs only list value; the multiplier affects the absolute
      label alone. This unblocks the operator's original ask (a usable per-task cost breakdown) without waiting on
      calibration convergence. **Done when**: the dashboard ranks tasks by cost with the basis labelled, and the
      absolute figure is either shown from todo 9's allocation or clearly marked provisional.
- [ ] [DATA] P1. **Test whether the quota meter weights cache reads like other tokens, by measuring a second window with
      a very different cache-read share.** The 190x multiplier's transferability depends entirely on this: if the meter
      tracks list value, a single constant is safe across workloads; if it discounts cache reads (as the extreme ratio
      hints — 99% of the measured window's tokens were cache reads), then the multiplier is a property of workload shape
      and must be measured per workload class. Compare measured multipliers across the two windows. **Done when**: both
      windows' cache-read shares and multipliers are recorded here with an explicit stable/varies verdict.
- [ ] [DATA] P2. **Do NOT assign the Pro account a multiplier by extrapolating from the published band — measure it or
      leave it labelled unmeasured.** The tempting shortcut (`Pro = Max / 2`, i.e. ~100x) rests on the published Pro
      3-6x vs Max20 6-10x ratio, and that source has already been shown wrong by ~20x for Max, so the ratio carries no
      weight. Pro is only 128 of 1,005 Anthropic rows, so the cost of waiting is small. **Done when**: either a
      controlled Pro window is measured the same way the 2026-08-10 Max window was, or Pro rows render with an explicit
      unmeasured-basis label.
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
- [ ] [BACKEND] P0. **Calibrate FLEET-AGGREGATE rather than per-account, which sidesteps the unrecoverable login
      timeline entirely.** Because every laptop tab shares one login at a time, laptop consumption always lands on SOME
      account we own — so summing numerator and denominator across all accounts makes per-account attribution
      unnecessary: numerator = total list value (all AO accounts + all laptop turns), denominator = sum over accounts of
      `consumed_fraction x window_cost`. This is the only route to a real number before the todo-3 logger has
      accumulated history, and it dissolves the [32.2x, 126.1x] bracket that per-account calibration is currently stuck
      with. Requires a COMMON period across accounts, so it depends on todo 1's meter history (per-account windows are
      offset by days and `weekly_pct` is current-state only). **Done when**: a fleet-aggregate multiplier is reported
      for one common period with its numerator and denominator broken out, and it is stated whether it falls inside the
      published 6-10x band.
- [ ] [BACKEND] P1. **Register `claude-opus-5` in the price table — the laptop already runs it and the AO fleet does
      not.** Measured 2026-08-10: laptop windows carry 1.8B cache-read and 4.7M output tokens on `claude-opus-5` ($5/$25
      per MTok), a model string absent from the AO fleet's entire observed vocabulary. Any fleet dispatch that picks it
      up would silently null those rows under the unpriced-poisons-the-window rule, and any laptop-inclusive calibration
      needs it priced. **Done when**: `claude-opus-5` prices correctly in a test and the calibration no longer reports
      it unpriced.
- [ ] [BACKEND] P1. **Scale partial windows by their consumed percentage instead of discarding them, and gate only on
      capture completeness.** Operator correction 2026-08-10: a window at 50% is still a valid sample — the
      entitlement-equivalent value is `V / p`, so every window becomes usable and the sample size stops being
      one-per-account. The real disqualifier is not partial consumption but partial CAPTURE: `account_id` capture began
      ~2026-08-06, so `sub-e-odum2default`'s window (opens 2026-08-05 23:00) is missing its first day and must be
      excluded — that, not double-counting, is the leading explanation for the 6x list-value spread across four
      identically-entitled max20 accounts. Derive the window as `resets_at - 7d` (verified consistent with the stored
      `weekly_window_start` for every account). **Done when**: the script emits a scaled multiplier for a partial
      window, refuses any window not fully inside the capture era, and a test covers both paths.
- [ ] [OPERATOR] P0. **LAPTOP-ONLY, TIME-CRITICAL — start recording the laptop's login identity on every change, because
      the switch history is unrecoverable and the operator switches accounts often.** `~/.claude.json`'s `oauthAccount`
      is current-state only; the sole surviving evidence on disk is three snapshots across eight days showing TWO
      different accounts (2026-08-02 `ikenna@odum-research.com` = `sub-c`, 2026-08-10 `iggy2london@gmail.com` =
      `sub-b`). Telemetry carries no account fields and `~/.claude/session-env` is empty, so nothing else records it.
      Append `(timestamp, accountUuid, emailAddress)` to a local log whenever it changes, so future windows are
      attributable even though past ones are not. Laptop-only — this state exists on no other machine. **Done when**:
      the log exists, contains at least one entry, and survives a Claude Code restart.
- [ ] [BACKEND] P1. **Treat EVERY measured multiplier as a lower bound and report `max(measured)` as the defensible
      floor — no account can currently be certified laptop-free.** Retracts this plan's earlier "four pure
      agent-orchestrator accounts" claim: `sub-c` was a laptop login on 2026-08-02, and the `~/.claude-accounts/*.env`
      absence that made `sub-d` look clean proves nothing, since those env files serve headless AO slot spawns while
      interactive login goes through `claude /login` and needs no env file. Laptop contamination only ever removes
      tokens from the numerator, so contamination biases the multiplier DOWN and the largest measurement is the closest
      to truth — currently **>= 32.2x at August promo rates for max20**, already well above the published 6-10x band.
      **Done when**: the calibration output labels each per-account figure a lower bound, states the fleet-wide floor as
      the maximum, and never averages across accounts.
- [ ] [BACKEND] P1. **Compute the window's real dollar cost as `7 / days_in_month x monthly_price`, requiring the window
      to fall entirely within one calendar month.** Operator ruling 2026-08-10: Anthropic never has to give us a dollar
      figure — we know what we pay, so the subscription price IS the anchor. Exact rather than an averaged
      4.348-weeks-per-month divisor, and it correctly captures that a 7-day window is cheaper in a 31-day month
      ($45.16 for max20 in August 2026) than in a 28-day one ($50.00), because the same $200 buys 4.43 windows instead
      of 4. A window straddling a month boundary must be prorated across the two daily rates or excluded. All five
      current windows fall entirely within August 2026, so no proration is needed today. **Done when**: the calibration
      emits the per-window cost from this formula with `days_in_month` shown, and a test covers both the within-month
      and straddling cases.
- [ ] [BACKEND] P1. **Stamp every multiplier with the valuation date and the rate set used, because the Sonnet-5
      promotion expiring 2026-08-31 shifts it ~50% with no change in usage or spend.** The same token volume valued at
      standard rates instead of the August promo rates moves `sub-c` from 32.2x to 46.9x — a bare multiplier with no
      date attached is not interpretable, and comparing an August measurement against a September one would read as a
      real efficiency change when nothing changed. **Done when**: the stored multiplier carries its valuation date and
      rate-set identifier, and a test proves two windows valued under different rate sets are not silently compared.
- [ ] [BACKEND] P1. **Correct the cost denominator to subscription PLUS extra-usage spend — overage was paid, contrary
      to the first reading.** `overage_status='rejected'` + `overage_disabled_reason='out_of_credits'` means overage is
      currently REFUSED because the credit pool is exhausted, not that none was used: the laptop account's live `/usage`
      payload shows `extra_usage.used_credits = 15078` against `monthly_limit = 20000` (GBP, 2dp) — £150.78 of real
      additional billing this month. Any account with non-zero `used_credits` in a calibrated window must have that
      added to its subscription cost, and the currency recorded (GBP here, not USD). **Done when**: the calibration
      reports cost as subscription + extra usage per window with currency, and a test proves a window with overage is
      not priced at bare subscription cost.
- [ ] [BACKEND] P1. **Persist the FULL `/usage` payload, not just the two percentage fields AO currently keeps.** The
      live payload carries `seven_day_opus` / `seven_day_sonnet` per-model sub-meters, a `limits[]` array with
      model-scoped buckets (`kind: weekly_scoped`, `scope.model.display_name`), `extra_usage` money fields, and
      `limit_dollars`/`used_dollars`/`remaining_dollars` (null for subscription windows, populated for extra usage). The
      per-model sub-meters are precisely the quota-weight signal todo 7 needs and Anthropic already exposes them — AO
      discards everything except `weekly_pct` and `five_hour_pct`. Compose with the todo-1 sampler so history captures
      the whole structure. **Done when**: a sampled row round-trips the per-model sub-meters and `extra_usage` block,
      verified against a live capture.
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
- [ ] [OPERATOR] P2. **LAPTOP-ONLY — measure this laptop's own Claude consumption per window so `sub-b-iggy2london` can
      be decontaminated rather than discarded.** Scan `~/.claude/projects/**/*.jsonl` (4,026 transcripts, ~4.1G, four
      concurrent interactive tabs active as of 2026-08-10 15:01) deduping by `requestId`, and sum tokens per model
      inside each `sub-b` calibration window. Local transcripts carry NO account identifier, so this is only sound
      because the laptop's login is known to be `sub-b` alone; state that assumption in the output. Runs on the
      operator's laptop by necessity — `~/.claude` exists nowhere else. Read-only, no VM, no deletes. **Done when**:
      laptop token totals per window are recorded here, and `sub-b`'s AO-only value plus laptop value is compared
      against its meter percentage.
- [ ] [OPERATOR] P2. **LAPTOP-ONLY — reconstruct as much of the historical login timeline as the operator can recall, to
      bound which windows are contaminated.** Disk evidence is exhausted (three snapshots, two accounts, no telemetry or
      session-env record), so operator recollection is the only remaining source for windows before the todo-3 logger
      starts. Even coarse answers ("sub-c was my laptop account most of early August") materially change which
      measurements are usable. **Done when**: either a recalled timeline is recorded here with its uncertainty stated,
      or it is explicitly noted that pre-logger windows can only ever yield lower bounds.
- [ ] [DATA] P1. **Write the tool-call batching SSOT under `/codex/06-coding-standards/` (suggested filename
      `tool-call-batching.md`) — the durable contract every other surface points at.** Measured 2026-08-10: 57.3% of ALL
      API calls are consecutive same-tool chains collapsible into one (Bash alone 52.8%, runs of 20/23/26/28/32
      observed, 69% of Bash calls inside a chain); each collapse saves one ~406k-token prefix re-read AND one model
      round-trip (median gap 10.5s, 8.6h of aggregate agent-time sits inside collapsible chains in a 4h25m window).
      State the rule positively — compound shell with `;`/`&&`, multiple `tool_use` blocks in one message for
      independent calls, `replace_all` or one Write instead of serial Edits, never re-read a file already read — plus
      the exception that genuinely result-dependent calls must stay sequential. **Done when**: the doc exists with
      `authoritative_for:` frontmatter and carries the measured baseline.
- [ ] [DOC] P1. **Propagate a one-line batching directive + SSOT pointer to EVERY agent-prompt surface, because AO
      worker classes do not share one rules file.** Distribution paths verified 2026-08-10: `CLAUDE.md` (auto-loaded by
      every session — orchestrator main, planning workers, interactive), `agents/RULES.md` (all AO workers),
      `SUB_AGENT_MANDATORY_RULES.md` (sub-agents, which do NOT auto-load CLAUDE.md), and
      `cursor-configs/AUTONOMOUS_AGENT_RULES.md` (`/autonomous` only). Targeting only the autonomous file would leave
      escalation workers, scheduled jobs, CI/CD, data-pipeline and planning workers unchanged. Condense to one line +
      pointer per the size budgets both rules files are QG-gated on (CLAUDE.md <= 40KB, SUB_AGENT_MANDATORY_RULES.md <=
      10KB) — never inline the full guidance. **Done when**: all four files carry the directive,
      `check_agent_rules_size_cap.py` still passes, and a grep shows each pointing at the codex SSOT rather than
      restating it.
- [ ] [DOC] P2. **Audit the 23 per-role files in `agents/` for any instruction that actively encourages sequential
      single-tool calls, and fix those specifically.** A universal rule is undermined if a role doc walks its agent
      through numbered one-command-per-step procedures. Roles to check include the escalation family (`cicd`,
      `conflict_resolver`, `data_pipeline_failure`), the scheduled family (`plan_health`, `plan_reconciler`,
      `docs_reconciler`, `ag_closeout_auditor`, `na_eligibility_auditor`, `context_scout_auditor`, `cefi_*`), the craft
      roles (`backend_engineer`, `infra`, `quant_dev`, `ui_developer`, `data_engineering`, `review`), and
      `main`/`worker`. **Done when**: each role file is either confirmed clean or amended, with the list of amended
      files recorded here.
- [ ] [DATA] P2. **Re-measure the collapsible-call share after the batching guidance ships, to confirm it moved rather
      than assuming it did.** Baseline to beat (2026-08-10 controlled window): 3,123 calls, 57.3% collapsible, 405,833
      mean cache-read tokens per call, 1.27B total reads. Reuse the same requestId-unioned method (content blocks must
      be unioned across all JSONL lines sharing a requestId — deduping to the first line silently drops tool_use blocks
      and was the bug in this plan's first content pass). **Done when**: a post-change window is measured with the same
      method and the before/after collapsible share and cache-read totals are recorded here.
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

### 2026-08-10 — Laptop-side probe: the contamination is confined to ONE account

Operator flagged that the same Claude accounts are used on their laptop (including the session authoring this plan), so
agent-orchestrator-only token sums would understate consumption and bias the multiplier DOWNWARD. Measured on the
laptop:

- **The laptop's interactive login is `iggy2london@gmail.com` = `sub-b-iggy2london`** (`~/.claude.json` `oauthAccount`).
- **Local slot config dirs went dormant 2026-08-04** (`~/.claude-configs/orch-slot-90{1..5}`, `orch-slot-99` — newest
  transcript 2026-08-04 14:35), while every current calibration window opens 2026-08-05 or later.
- ~~Therefore `sub-c`, `sub-d`, `sub-e`, `sub-f` are pure agent-orchestrator for their current windows.~~ **RETRACTED
  same day — see the account-switch entry below. No account can be certified laptop-free.**
- `sub-b` is genuinely contaminated and cannot be split: **local transcripts carry no account identifier** (fields are
  `cwd`, `effort`, `entrypoint`, `gitBranch`, `sessionId`, `requestId`, `timestamp`, `version` — no account/org id). It
  is also the only account not at 100% weekly (63%), consistent with being the shared one.

**CORRECTION to the 2026-08-10 feasibility probe — overage WAS paid.** That entry recorded "no overage was ever paid,
the denominator needs no adjustment", reading `overage_status='rejected'`. That reading was wrong: `rejected` +
`out_of_credits` means overage is currently REFUSED because the pool is exhausted, not that none was consumed. The
laptop account's live `/usage` payload shows `extra_usage.used_credits = 15078` of `monthly_limit = 20000` (GBP, 2
decimal places) — **£150.78 of real additional billing this month**. Cost denominators must be subscription + extra
usage, with currency recorded (todo 8).

**Anthropic exposes no dollar figure for subscription usage** — `limit_dollars` / `used_dollars` / `remaining_dollars`
are in the `/usage` schema but `null` for both the `five_hour` and `seven_day` windows; only `extra_usage` carries
money. **This does NOT block calibration** (operator correction, same day): we know what we pay, so the subscription
price is the anchor and Anthropic only ever needed to supply the consumption side. An earlier note here framed the
missing dollar field as a blocker — it is not; it merely removes an independent cross-check.

**Window cost formula (operator ruling 2026-08-10)**: `7 / days_in_month x monthly_price`, with the window required to
sit entirely inside one calendar month. For max20 in August 2026 that is `7/31 x $200 = $45.16` — a 1.9% correction to
the $46.00 (averaged 4.348 weeks/month) used in the first pass. All five current windows satisfy the within-month
constraint.

**Re-run of the clean accounts against the corrected denominator**, valued at the published August rates INCLUDING the
Sonnet-5 promotion (the correct valuation for an August window):

| account            | list value (promo) | multiplier |             at standard rates |
| ------------------ | -----------------: | ---------: | ----------------------------: |
| sub-c-ikenna-odum  |          $1,455.53 |      32.2x |                         46.9x |
| sub-d-odum1default |          $1,088.19 |      24.1x |                         35.1x |
| sub-f-odum2default |            $699.73 |      15.5x |                         22.8x |
| sub-e-odum2default |            $274.89 |       6.1x | 7.8x (excluded — capture era) |

**The denominator is now exact and the spread survives it** — 15.5x to 32.2x across three clean, identically-entitled
max20 accounts. The residual error is therefore entirely in the NUMERATOR (attribution coverage), which todos 2-6
address; no further denominator precision will close it.

**Timing trap**: the Sonnet-5 promo expires 2026-08-31, so the identical token volume becomes ~50% more valuable at list
on 2026-09-01. The multiplier jumps by half with no change in usage or spend — hence todo 10's requirement that every
multiplier carry its valuation date and rate set.

**AO is discarding most of the `/usage` payload** (todo 9): it keeps `weekly_pct` and `five_hour_pct` and drops the
`seven_day_opus` / `seven_day_sonnet` per-model sub-meters, the `limits[]` array with model-scoped buckets
(`kind: weekly_scoped`, `scope.model.display_name: "Fable"`), and the whole `extra_usage` block. Those per-model
sub-meters are exactly the quota-weight signal todo 7 was written to go hunting for.

### 2026-08-10 — Why the 190x DOES transfer to AO: identical cache profiles

Operator question: if the quota meter is weighted by the cache discount, how would that change the calibrated 190x?

- **If the meter is price-weighted** (cache reads counted at 0.1x, as they are billed), quota consumed is proportional
  to list value and **the multiplier is workload-INDEPENDENT** — 190x transfers to any mix unchanged.
- **If the meter counts raw tokens equally**, 190x is specific to a 99%-cache-read mix, and cache-light work measures
  HIGHER (the same quota buys full-rate tokens instead of 0.1x ones). So 190x is a FLOOR, not a ceiling.

**Either way it transfers to AO**, because AO's workload sits at the same point on the curve — measured cache-read share
of total tokens: **laptop 98.90%** (1,267,416,118 / 1,281,547,098) vs **AO on `sub-c` 98.54%** (5,527,290,327 /
5,609,037,297). The two are the same shape, so the metering hypothesis does not change the transfer. The meter
experiment is therefore a REFINEMENT for pricing genuinely cache-light work (a short one-shot task), not a blocker on
using ~190x for AO today.

## Deferred work after 2026-08-10

| item                                               | state / why deferred                                                                                                                              | blocked on                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Reserve one max20 account for AO exclusively       | **Operator-owned** — needs a human commitment never to use it interactively; unlocks exact, laptop-free calibration                               | operator                                     |
| Meter-history + laptop-login samplers (todos 1, 3) | **Not done** — highest priority; every hour without them permanently destroys 5-hour windows and login attribution                                | nobody                                       |
| Quota-meter weighting experiment                   | **Cannot be done yet** — needs a second window at a very different cache-read share; only refines pricing for cache-light work, does not block AO | elapsed time / a differently-shaped workload |
| Pro-account multiplier                             | **Cannot be done yet** — needs a controlled Pro window measured the way the Max one was                                                           | elapsed time                                 |
| Batching rule propagation (todos 24-26)            | **Not done** — cheap doc work, large payoff (~46% of bill), but recoverable later unlike the samplers                                             | nobody                                       |
| Plan line-cap extraction                           | **Not done** — 575 lines on origin vs 500 soft / 1000 hard; extract oldest closed Progress Log sections before it hits the hard cap               | nobody                                       |

**Recommended NEXT item**: the two samplers (todos 1 and 3). Everything else in this plan is recoverable work; those two
are the only items whose input data is destroyed by the passage of time.

### Session lessons (carry these, they cost real time)

1. **Dedupe transcript lines by `requestId` for TOKENS, but UNION content blocks across all lines sharing it.** Claude
   Code writes one JSONL line per content block. Keeping only the first line silently drops `tool_use`/`thinking` blocks
   and produced two wrong figures in this session (89% thinking, 71% tool-free turns) before correction.
2. **`overage_status: rejected` + `out_of_credits` means overage WAS used and the pool is now exhausted** — not that
   none was ever paid. Cost `GBP 150.78` was invisible under the first reading.
3. **`~/.claude-accounts/*.env` files gate HEADLESS slot spawns only.** Their absence says nothing about interactive
   use, which goes through `claude /login`. This invalidated a "provably clean account" claim.
4. **`account_usage` and `~/.claude.json` are both CURRENT-STATE only.** No history exists for the usage meters or the
   laptop login; past windows are unrecoverable, which is why the samplers are P0.
5. **A checker that takes a path argument may ignore it.** `check_reference_paths.py` scans all 2,042 files regardless,
   and its `--only` mode reads the git index — so validating a single unstaged file needs a different approach.
6. **This checkout is ~98 commits behind origin and cannot `git pull --ff-only`** (peer sessions' untracked files block
   it). Local validators therefore disagree with the pre-commit hooks, which run against origin in an isolated worktree.
   Trust the hook, not the local run.

### 2026-08-10 — AO account rotation timeline, and the cache-accounting verification

**AO burns accounts to exhaustion then rotates**, rather than spreading load — measured from `task_usage` + `agents`:
`sub-e` 08-06 00:18 -> 08-08 (49 tasks, exhausted), `sub-f` 08-06 22:53 -> 08-09 23:44 (166, exhausted), `sub-c` 08-07
19:27 -> 08-09 18:46 (274, exhausted), `sub-d` 08-07 19:35 -> 08-10 09:14 (216, exhausted), `sub-b` 08-09 19:14 -> live
(172, 63%), `sub-a` pro 08-06 -> 08-10 (128, exhausted). DeepSeek volume spikes on 08-10 exactly as the Anthropic pool
empties. The `agents` table attributes further back than `task_usage` does (sub-d from 08-02, sub-b and sub-c from
08-04) and is the usable attribution source for the pre-08-06 window where `task_usage.account_id` is null.

**Cache accounting verified correct** (operator challenge): the flat `cache_creation_input_tokens` equals the
`cache_creation` 5m+1h breakdown EXACTLY over the controlled window (11,711,885 = 747,496 + 10,964,389, zero per-turn
mismatches), the four token classes are disjoint so summing cannot double count, and no server-tool calls were billed
(`web_search=0`, `web_fetch=0`). The gross figure therefore already incorporates cache pricing at published rates (read
0.1x, write 1.25x/2.0x) — it does NOT assume an uncached workload.

**Open question the multiplier's transferability rests on**: we know what Anthropic CHARGES for cache, but not what its
quota METER counts. If the meter weights cache reads like any other token, 7% of weekly bought 1.28B tokens
(~18.3B/week); if it largely ignores them, 7% bought ~14.1M non-cache tokens (~201M/week). One observation cannot
separate these, and they imply very different multipliers for differently-shaped work. Testable with a second window at
a very different cache-read share — tracked below.

### 2026-08-10 — CONTROLLED MEASUREMENT: ~190x on a clean laptop-only window (best datapoint to date)

Operator supplied a controlled experiment that removes every contamination problem above: a 4h25m window
(`2026-08-10 10:02:35Z -> 14:27:34Z`) that was **strictly laptop, strictly `iggy2london@gmail.com` (`sub-b`), zero AO**,
across which the weekly meter moved **57% -> 64% = 7%**. Actual money spent is therefore `0.07 x $45.16 = $3.16`.

Measured from the laptop's own transcripts (tabs 1-4 + subagents), deduped by `requestId`:

| model           | turns |    cache read |    output | documented cost |
| --------------- | ----: | ------------: | --------: | --------------: |
| claude-opus-5   | 1,998 |   745,335,541 | 1,617,949 |         $459.02 |
| claude-sonnet-5 | 1,125 |   522,080,577 |   788,135 |         $137.82 |
| **total**       | 3,123 | 1,267,416,118 | 2,406,084 |     **$598.71** |

**Multiplier = $598.71 / $3.16 = ~190x at August promo rates (~212x at standard).** Against 15-32x from the contaminated
AO-side attempts and 6-10x published — confirming the AO figures were understated exactly as the contamination analysis
predicted.

Notes that make this the reference measurement:

- **Opus dominates cost, not turn count**: 77% of documented value off 64% of turns ($5/$25 vs Sonnet-5's promo $2/$10),
  and Opus cache reads alone are $373. Model mix, not volume, drives equivalent value — a Sonnet-only window would value
  at roughly a third.
- **Compaction replay is real and large**: 3,270 replay lines were skipped against 3,123 genuinely billed turns — over
  half of transcript lines re-write already-billed calls. Deduping on `requestId` (stable across replay) is what makes
  the number trustworthy; naive counting roughly doubles it. Same mis-measurement class the pre-compact trigger hit.
- AO touched `sub-b` only twice inside the window, both known mislabeled-telemetry rows (`deepseek-v4-pro` /
  `<synthetic>` model strings), worth at most ~$37 — immaterial.
- **Caveats**: 57->64 is integer-rounded, so the true delta is 6.5-7.5% and the range ~176-204x; and if heavy Opus use
  draws on a scoped `seven_day_opus` bucket rather than `weekly_all`, the 7% understates consumption and would pull the
  multiplier DOWN — the one open risk, already tracked as the per-model quota-weight todo.

### 2026-08-10 — Cost structure: cache reads are 80% of the bill, and 90% of calls are un-batched

Decomposition of the controlled window's $598.71 by token class, and where the reducible waste is.

| class                   |    cost | share |
| ----------------------- | ------: | ----: |
| cache read              | $477.09 | 79.7% |
| cache write             |    ~$73 | 12.2% |
| output (incl. thinking) |  $48.33 |  8.1% |
| input (uncached)        |  ~$0.04 |   ~0% |

**Cache reads dominate four-to-one.** Mean cache read per API call is **405,833 tokens**, and within-session context
growth is only **1.37x** (344k -> 471k first-vs-last quartile), so compaction is working and cost is **linear in CALL
COUNT at a ~406k constant**, not quadratic in context. Every call re-reads the full prefix regardless of how small its
work is.

**89.9% of API calls make exactly one tool call; only 4.0% batch 2+.** Because cost is linear in calls, merging X% of
calls saves X% of cache reads: 25% -> 317M tokens, 50% -> 634M tokens (~$239, ~40% of the total bill, i.e. roughly
double the work per weekly quota window). Independent tool calls (multiple reads, parallel greps) batch at zero quality
cost; genuinely dependent ones cannot. The second, equally linear lever is resident context size itself.

**Thinking is 68.8% of output tokens** (Opus 66.9%, Sonnet 72.8%) but only ~$33 of $599 — **5.5% of cost**. Thinking
depth is not the spend lever; cache reads are.

**Method correction**: an earlier pass reported 89% thinking and claimed 71% of turns made no tool call. Both were
artifacts of deduping transcript lines by `requestId` and keeping only the FIRST line — Claude Code writes one JSONL
line per content block, all sharing a requestId, so `tool_use`/`thinking` blocks logged on later lines were dropped.
Token totals were unaffected (usage is per API call and was correctly counted once); only the content statistics were
wrong. Content must be UNIONED across all lines sharing a requestId.

### 2026-08-10 — RETRACTION: the laptop switches accounts, so no account is certifiably clean

Operator correction: "we literally switched accounts today and we switch often." Investigated every account-history
source on the laptop. Findings:

- **Only three login observations survive on disk, showing TWO different accounts**: `2026-08-02 23:41` =
  `ikenna@odum-research.com` (**`sub-c-ikenna-odum`**, from a stale `.claude.json.tmp` file), and `2026-08-10 12:36` +
  `14:32` = `iggy2london@gmail.com` (`sub-b`). So `sub-c` — named a clean calibration subject hours earlier — was itself
  a laptop login inside the same month.
- **No switch history exists anywhere**: `~/.claude/telemetry` carries no account-bearing fields,
  `~/.claude/session-env` is empty, `~/.claude/backups` spans only today, and local transcripts have no account
  identifier. The timeline is unrecoverable.
- **The "sub-d is doubly clean" inference was also wrong.** `~/.claude-accounts/*.env` files serve HEADLESS AO slot
  spawns; interactive login goes through `claude /login` and requires no env file, so their absence says nothing about
  interactive use.

**Consequence**: no account can currently be certified laptop-free, and every per-account multiplier is a LOWER BOUND of
unknown tightness. The useful invariant is directional — laptop contamination only ever removes tokens from the
numerator, never adds them — so contamination biases the multiplier DOWN and `max(measured)` is the closest to truth.
That yields a defensible fleet floor today of **>= 32.2x at August 2026 promo rates for max20**, still far above the
published 6-10x band. Fixed by todo 3 (start logging login identity now — same "cannot recover the past" property as the
meter sampler) and todo 6 (report lower bounds and a max, never an average).

**Incidental findings**: every cache write on this fleet is 1h TTL (`ephemeral_5m_input_tokens` = 0 across 17,446+
sampled turns), so only the 2.0x cache-write tier matters; cache-read volume is enormous (5.2B tokens on `sub-c` in one
week), which is what pushes measured value so far above the published band — nearly free on a subscription, expensive at
list rates. A bare `sonnet` model alias appears on 68 turns and would keep poisoning rows even after the canonical model
ids are registered.
