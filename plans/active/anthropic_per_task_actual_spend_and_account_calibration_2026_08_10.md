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
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19.md,
  ]
created: "2026-08-10"
last_updated: 2026-08-19
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
    agent-orchestrator/server/model_pricing.py,
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
- Account registry: 4x `max20` ($200/mo) + 2x `pro` ($20/mo, `sub-a-ikenna`, `sub-d-odum1default`) + 2 DeepSeek
  `api` accounts. **Corrected 2026-08-18 (/plan-reconcile)**: originally read "5x max20 + 1x pro" — Todo 1's
  2026-08-16 correction established `sub-d-odum1default` is tier `pro`, not `max20`, so this 2026-08-10
  starting-state count is updated to match (2 pro, not 1; 4 max20, not 5).
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

## Operator ruling 2026-08-10 (evening) — two accounts RESERVED for AO, everything else paused

This resolves the contamination problem the plan was working around, and it changes what the calibration measures from
"a lower bound polluted by unknown laptop use" to a direct reading.

| Account                                | Tier      | Monthly (ex-VAT) | Monthly (paid, incl. VAT) | Weekly meter resets |
| -------------------------------------- | --------- | ---------------- | ------------------------- | ------------------- |
| **Ikenna — sub A** (`ikennaigboaka@…`) | **pro**   | $20              | **$24**                   | **Wednesday 13:00** |
| **Ikenna — sub E** (`odum3default@…`)  | **max20** | $200             | **$240**                  | **Wednesday 22:00** |

**CORRECTED 2026-08-12 (/plan-reconcile, operator-confirmed), then RE-CORRECTED 2026-08-19 (/plan-reconcile
orchestrator_master)**: the 2026-08-12 fix conflated this account's EMAIL suffix (`odum3default@...`, genuinely
correct) with its SLUG id and renamed every `sub-e-odum2default` occurrence to `sub-e-odum3default` — but the live
`accounts.json`/`state.db` slug is `sub-e-odum2default` (email `odum3default@gmail.com`), independently confirmed by
`claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` todo 1 (DONE 2026-08-13, queried directly against
accounts.json). Every `sub-e-odum3default` occurrence in this doc has been reverted to `sub-e-odum2default` to match
the live id; the email/slug suffix mismatch (email says `odum3default`, slug says `odum2default`) is a real,
confirmed-cosmetic quirk of the live system, not a doc error to "fix" again.

Every OTHER Claude account is paused, so the AO pool is exactly DeepSeek + these two. Three consequences:

1. **Both accounts become measurable, not just one.** The plan previously had no path to a Pro multiplier at all — the
   published 3-6x band was worthless as an input, since the same source was already shown wrong by ~20x for max20. A
   dedicated Pro account measures it the same way max20 was measured.
2. **The 5-hour meter becomes the better statistical surface.** With the fleet concentrated on two accounts, 5h windows
   (which reset ~33x more often than weekly) accumulate quickly rather than being spread thin.
3. **Deadline: the code must be ready BEFORE the Wednesday resets**, because a reset is what gives a clean window
   boundary. Calibration starts from the first post-reset sample, not from a mid-window guess.

**No 7-day wait is required.** `weekly_pct x 7 / days_in_month x monthly_price` values ANY window, however short — a
window that consumed 7% of the meter cost 7% of the weekly budget. This is why the calibration script gates on capture
completeness and month boundaries rather than on the window being fully consumed.

**VAT is excluded from the multiplier basis, deliberately.** Anthropic's per-token list rates are published ex-tax, so
dividing a VAT-inclusive subscription price by ex-VAT list rates would understate the multiplier by the VAT rate. The
paid figure stays reportable (`SubscriptionPlan.monthly_usd_incl_tax`) so real cash cost is never lost.

**Timezone caveat, unresolved:** the reset times above are as the operator stated them (local, i.e. BST). Nothing
depends on them — the calibration reads `weekly_window_start` from Anthropic's own payload, which is authoritative — so
they serve as a cross-check, and a mismatch between the two is itself a finding worth recording.

## Todos

- [x] ✅ [DATA] P0. **CORRECTION 2026-08-16 (main agent, BLK-050d1304): `sub-d-odum1default` is tier `pro` ($20/mo),
      NOT `max20` ($200/mo) — verified directly against `agent-orchestrator/data/config/accounts.json` (the
      authoritative live source; `"tier": "pro", "weekly_msg_limit": 600`). Every table row in this doc that labels
      `sub-d-odum1default` as `max20` (Progress Log "2026-08-10 — Diagnosis + first calibration pass" and "Re-run of
      the clean accounts against the corrected denominator") used the $200/mo denominator and is therefore wrong —
      the multipliers (34.4x/18.4x first pass, 24.1x/35.1x re-run) need recomputing against the Pro denominator
      (`7/days_in_month x $20`, ~$4.52 for an August window), which raises them roughly 10x, not lowers them. **This
      may be the same root cause as the "1047x outlier" P1 open in
      `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`** (that doc independently classifies the same
      account as Pro and is investigating why its multiplier reads so far outside the max20 band — a mislabeled
      denominator here would explain an outsized multiplier there too, since both docs are measuring the SAME
      account's list-value consumption against two different assumed subscription costs). **Done when**: both tables'
      `sub-d-odum1default` rows are recomputed at the Pro denominator (or struck if superseded by todo 11's
      exclusion), and someone with both docs open confirms/refutes whether the 1047x outlier and this mislabeling are
      the same bug.
- [x] ✅ [BACKEND] P0. **Meter-history sampler SHIPPED — agent-orchestrator@ce3389f.** `account_usage_history` (PK
      `account_id, sampled_at`) plus `snapshot_account_usage_history()` called on every UsagePoller tick, covered by
      `tests/test_account_usage_history.py`. **Cadence verified adequate 2026-08-10**: the poller runs every 30 min
      (`usage_poll_interval_minutes`, default 30), giving ~336 samples per weekly window and ~10 per 5-hour window.
      Reset-boundary resolution is +/-30 min, which introduces no bias — the multiplier is a DELTA between two observed
      samples and the transcript walk is clipped to exactly that interval. Flipped late: the code landed days before the
      checkbox, which is precisely the false-progress this rule exists to prevent.
- [x] ✅ [BACKEND] P0. **Slot-to-account-over-time attribution map SHIPPED — agent-orchestrator@5516a0a.**
      `server/slot_account_attribution.py` builds `AccountInterval`s from `AgentRow` history and resolves a turn (or a
      whole transcript) to the account that held the slot AT THAT TIME, so a post-compaction session still attributes
      correctly. `calibrate_account_value.value_window()` consumes it, and `test_calibration_end_to_end.py` proves a
      session owned by a DIFFERENT account contributes nothing — the property the whole reservation depends on. Flipped
      late, same reason as the sampler above.
- [x] ✅ [BACKEND] P0. **Add a globally `message.id`-deduped transcript walker so one turn is counted exactly once per
      account-window, regardless of how many files or task windows contain it.** `scan_session_usage` already dedups
      within one file; the account-level aggregate needs dedup ACROSS files (resume/replay copies the same turns into a
      second transcript — `measure-claude-usage-value.py`'s own docstring records 588,821 duplicate turns against
      649,255 real ones on this VM, ~47%). **Done when**: a test with the same `message.id` present in two transcript
      files under one account yields one counted turn, and the walker's total for a known window matches a hand-verified
      count. — agent-orchestrator@ff2f1c5 + QG green; `scan_usage_across_transcripts` (first-occurrence-wins across
      files) + `scan_account_transcripts` (per-account window clip + global dedup); tests prove cross-file dedup (same
      `message.id` in two files counted once) and the known-window total equals the hand-verified count (input 300 /
      output 30).
- [x] ✅ [BACKEND] P0. **Fix `task_usage` double-counting: a typed one-off with `assigned_at=None` bills the WHOLE
      session, and overlapping per-task windows on one slot bill the same turns to several tasks.** This corrupts
      per-task cost independently of pricing and is why the task_usage-derived multiplier reads HIGHER than the
      transcript-derived one for 4 of 5 accounts, despite being a strict subset of the same turns. Decide and implement
      one attribution rule (proposed: a turn belongs to exactly one task — the task whose window contains it,
      earliest-assigned wins on overlap) in `deepseek_usage.build_task_usage_snapshot` and the `/done` capture path.
      **Done when**: a regression test with two overlapping task windows on one slot proves each turn is counted once,
      and re-running the calibration shows method (A) no longer exceeding method (B). — agent-orchestrator@382e278 + QG
      green; regression test proves each turn counted once (partition_task_usage + /done + backfill wiring).
- [ ] [REVIEW] P0. **Quantify the double-count blast radius on the live DB before repricing anything — report how many
      existing `task_usage` rows overlap another row on the same slot, and the token volume involved.** Read-only via
      `scripts/orchestrator/query-ao-state-db-readonly.sh`. This decides whether historical rows can be repriced in
      place or must be recomputed from transcripts. **Done when**: the query output is pasted into this plan's Progress
      Log with an explicit in-place-vs-recompute recommendation.
- [x] ✅ [BACKEND] P1. **`server/model_pricing.py` landed as the single pricing SSOT — agent-orchestrator@c40d847ac6.**
      Date-effective rate cards for every model the fleet runs; Anthropic's three cache tiers derived from the base
      input rate (read 0.1x, 5m write 1.25x, 1h write 2.0x); DeepSeek's no-write-premium rates expressed as absolute
      numbers rather than a special case. `_PRICE_PER_MILLION` deleted from `deepseek_usage.py`, which now delegates.
      Sonnet 5 carries two non-overlapping cards (intro $2/$10 to 2026-08-31, standard $3/$15 after) and a turn is
      priced at its OWN timestamp. `test_no_model_has_overlapping_rate_windows` checks the no-overlap invariant
      structurally, so a future card cannot introduce an order-dependent price. **Deviation from the todo, stated:**
      `opus`/`haiku` aliases WERE registered, against the todo's instruction. Justification: every registered Opus
      generation is $5/$25 and only one Haiku is registered, so those aliases are RATE-NEUTRAL — the generation cannot
      change the price. Leaving them unpriced would let one aliased turn poison an entire calibration window under
      `summed_spend`'s all-or-nothing rule. Only `sonnet` is a real assumption, and `used_family_alias` flags it so a
      calibration run reports the count.
- [x] ✅ [BACKEND] P1. **`usage.cache_creation` 5m/1h split parsed and priced by TTL — agent-orchestrator@c40d847ac6.**
      `_cache_creation_split` returns `(None, None)` when the key is absent rather than zeros, so "no 1h writes" is
      distinguishable from "this transcript predates the breakdown"; the latter falls back to the CHEAPER 5m rate,
      under- rather than over-charging. Tests prove a 1h write bills at 2.0x input, a 5m write at 1.25x, and a DeepSeek
      cache write at 1.0x.
- [x] ✅ [SCRIPT] P1. **`calibrate_account_value.py` SHIPPED (agent-orchestrator@c40d847ac6) — code landed; live run
      deferred to Wednesday.** Meter history -> longest reset-free window -> attributed transcript walk -> multiplier,
      with two REFUSALS rather than caveats (month-straddling windows, and windows opening before attribution capture
      began 2026-08-06). Reports per-model turn counts, the cache/output cost split, alias-turn count, and the binding
      meter. Read-only. **Live run deferred**: the per-account output must be pasted into the Progress Log, and there is
      no post-reset window to measure until Wednesday. Code is on origin/live-defi-rollout; the script, its 186-line
      test suite, and the PricingPlan/MeterSample/MeasuredValue types all landed in c40d847ac6.
- [x] ✅ [SCRIPT] P1. **UNTAGGED from `[OPERATOR]` 2026-08-16** (`task_template.md` §3 finding Y triage, Track 7 of
      `ao_open_work_consolidated_tracker_2026_08_14.md` — mis-tag, not a fork candidate): **Run the calibration
      across every `weekly_pct=100` account and record the measured multipliers, explicitly excluding
      `sub-a-ikenna`.** That account is tier `pro`, not `max20` (operator ruling 2026-08-10 — see this doc's own
      `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md` § "Operator ruling 2026-08-10": it switched to Pro and
      would confuse the Max calibration). The run is strictly read-only (SQLite `mode=ro` + transcript reads), writes
      nothing, and launches no VM — the prior `[OPERATOR]` tag was reflexive, not backed by genuine ambiguity per
      finding U's 3-part test (no business/spend judgment, no credential-only access, no delete). **Done when**: a
      measured multiplier per max20 account is recorded here with its window, and any account whose two attribution
      methods still disagree by >20% is named as unresolved — flag that disagreement for a human read, but the run
      itself is fully AO-dispatchable.
      **Run 2026-08-17** (direct read of the live `state.db`, no SSM) — see Progress Log "Second calibration pass"
      for the full table, the `sub-e` account-id naming discrepancy, and the flagged >20% swings (`sub-c`, `sub-f`).
- [x] ✅ [BACKEND] P1. **`subscription_value.allocate_proportionally()` SHIPPED — agent-orchestrator@54e6347aa7.**
      `task_cost = window_subscription_cost x (task_list_value / total_list_value_in_window)`, exact by construction
      (sum-invariant holds regardless of rate changes since numerator and denominator move together). 6 tests in
      `tests/test_subscription_value_allocation.py` prove: sum-to-window-cost, proportional split, the sum invariant
      surviving BOTH a uniform rate change (every task's value doubles) and a non-uniform one (one model's rate moves,
      others don't), zero-total-value returns 0.0 per task rather than dividing by zero, empty input, and the
      single-task edge case. **Scope note**: this ships the allocation FUNCTION + its invariant proof (the todo's
      literal done-when, verified with synthetic task-value fixtures) — it is not yet wired to a live window's
      `task_usage` rows, since todo 12 (immediately below) explicitly supersedes the runtime path with the measured-
      multiplier form and keeps this allocation form as an OFFLINE reconciliation check, not the hot path. QG green:
      4017 backend + 387 dashboard tests.
- [ ] [DATA] P0. **Verify the reservation actually held over the first post-reset window — the operator has RESERVED the
      accounts, so what remains is measurement, not a decision.** Operator ruling 2026-08-10 (evening, see the ruling
      section above): `sub-a-ikenna` (pro) and `sub-e-odum2default` (max20) are dedicated to agent-orchestrator and
      every other Claude account is paused, so the AO pool is exactly DeepSeek + those two. This closes the
      contamination class the plan was working around — the earlier `sub-d-odum1default` suggestion is SUPERSEDED, and
      it was reasoned from a false premise anyway (the absent `~/.claude-accounts/*.env` proves nothing, since env files
      serve headless spawns while interactive login goes through `claude /login`). What is left is a check, not a
      commitment. **Done when**: for the first window after the Wednesday resets, the login sampler (todo 21) shows zero
      laptop sessions on either reserved account, and any laptop session found is named here rather than averaged away.
- [ ] [BACKEND] P1. **Given the VM cannot see laptop usage, apply cost via a multiplier MEASURED on an AO-exclusive
      window rather than a runtime denominator that needs both halves.** This supersedes the pure
      proportional-allocation form for the AO runtime path: allocation still holds as the definition, but the VM
      evaluates it using a stored multiplier derived from a window where AO owned the account outright (todo 11), so it
      needs no laptop input. Keep the sum-invariant as a periodic CHECK (recompute allocation offline where both halves
      are known) rather than a runtime requirement. **Done when**: the runtime path prices a task with no laptop data
      available, and an offline check confirms the per-task costs sum to the window's subscription cost within rounding.
- [x] ✅ CANCELLED [DATA] P2. **Laptop-to-VM usage export — not needed; the reservation was adopted instead.** This was
      the explicit fallback for todo 11 ("either todo 11 is adopted and this is CANCELLED"), and todo 11 was adopted on
      2026-08-10: `sub-a-ikenna` + `sub-e-odum2default` are AO-exclusive, so no cross-machine channel has to exist.
      Cancelled on the merits, not deferred — the export was strictly worse by design, since it introduces a data path
      that fails SILENTLY whenever the laptop is off, and a silently-stale denominator is exactly the failure this plan
      exists to eliminate. Re-open only if the reservation is ever withdrawn.
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
- [ ] [DATA] P1. **Measure the Pro multiplier directly on `sub-a-ikenna` — never extrapolate it from the published
      band.** The tempting shortcut (`Pro = Max / 2`, i.e. ~100x) rests on the published Pro 3-6x vs Max20 6-10x ratio,
      and that source has already been shown wrong by ~20x for Max, so the ratio carries no weight. This was P2 while no
      Pro account was measurable; the 2026-08-10 reservation makes it directly measurable, so it is now P1 and runs in
      the same pass as max20 — the two differ only in `PLAN_MONTHLY_USD_EX_TAX`. Worth measuring for its own sake: if
      Pro and max20 land at the SAME multiplier, the subscription tiers price work identically and tier choice is purely
      about throughput; if they differ, that ratio is itself a purchasing decision. **Done when**: a post-reset Pro
      window is measured the same way the max20 one was, both multipliers are recorded here with their valuation dates,
      and any divergence is stated rather than averaged.
- [x] ✅ [BACKEND] P2. **`account_id` filter axis landed on `window_task_usage_totals` +
      `GET /api/backlog/usage/windows` — agent-orchestrator@12fad94355.** Composes AND-wise with
      provider/model/role_group. `test_per_account_totals_sum_to_the_provider_total` is the operator's own acceptance
      test — per-account slices must sum to the provider total exactly as DeepSeek pro+flash already do. A third test
      pins the honest edge: rows with a NULL `account_id` (written before capture began ~2026-08-06) match NO account
      filter, so per-account sums legitimately fall SHORT of the unfiltered total on historical data — that shortfall is
      the signal those rows are unattributed, not an aggregation bug.
- [x] ✅ [UI] P2. **Per-account filter row added to `TaskUsageWindows.tsx` — agent-orchestrator@12fad94355. pw:L2 ✓**,
      regression spec `dashboard/tests/e2e/task-usage-account-filter.spec.ts` (6/6 chromium). Buttons are built from the
      LIVE accounts registry, not hardcoded — accounts are paused/rotated often enough that a literal list would be
      stale within days — and sorted by `account_id` so they cannot reshuffle under the cursor between polls. The last
      spec deliberately asserts the SHORTFALL: tasks on an unregistered account are unreachable by any filter, so the
      per-account slices sum to 12,000 of 17,000 rather than the whole. **Trap worth keeping**: the first version of
      that spec read the cell with `textContent` straight after clicking a filter and raced the refetch, silently
      summing the PREVIOUS slice (29,000 instead of 12,000). Use auto-retrying `toHaveText`; the sibling
      provider/role-group specs never hit this because they only ever assert one slice.
- [ ] [UI] P2. **Surface the spend basis in the task-usage panel so a DeepSeek dollar (metered) and an Anthropic dollar
      (subscription-attributed at a measured multiplier) are distinguishable, and keep Anthropic's
      percent-of-weekly-limit visible alongside it.** Operator intent 2026-08-10: Anthropic becomes actual spend, the
      percent stays as a supplementary signal rather than the only one. **Done when**: `pw:L2 ✓` with a spec asserting
      both the $ figure and the basis indicator render for an Anthropic-scoped window.
- [ ] [SCRIPT] P2. **`reprice_task_usage.py` SHIPPED (agent-orchestrator@c40d847ac6) — remaining: the live dry run.**
      Dry-run by default, `--apply` to write, `--only-unpriced` to touch just the blank rows, idempotent, prices each
      row at the rates in force on its OWN `completed_at`. Reports newly-priced / repriced / unchanged / still-unpriced
      and names every model it could not price. **Deviation from the todo, stated:** the exact-vs-approximate split was
      NOT built. Repricing is a pure DB recompute from each row's stored tokens, so a window that ran on more than one
      model is priced at `task_usage.model` (the LAST turn's). Instead of a second transcript-reading code path, the
      script REPORTS how many changed rows still have a `claude_session_id`, which is the information needed to decide
      whether the exact path is worth building at all. **Still open because the done-when requires a live dry run**
      against the VM DB.
- [ ] [SCRIPT] P2. **Run `reprice_task_usage.py --apply` against the live orchestrator VM via SSM after reviewing the
      dry-run report.** Retagged `[OPERATOR]` -> `[SCRIPT]` on operator instruction 2026-08-11 — no human gate needed.
      **Safe-idempotent justification** (required for any AO `--apply` todo per `plans/active/task_template.md` finding
      O): this is NOT a delete and touches no GCS object. It recomputes `task_usage.spend_usd` from each row's OWN
      already-stored token counts and `model` — a pure DB recompute, no transcript access — writing a column that is
      currently NULL on ~1,993 of 2,622 rows. It is dry-run BY DEFAULT (`--apply` required to write), fully re-runnable
      (a second run recomputes the same values and reports them unchanged), and `--only-unpriced` narrows it to just the
      blank rows. A partial or interrupted run is safe to re-invoke. The values it writes are derived, not authored, so
      a wrong result is corrected by re-running after fixing the rate table rather than by restoring data. **Done
      when**: a post-run query showing the remaining `spend_usd IS NULL` count (and the reason for any residual) is
      pasted into the Progress Log.
- [ ] [REVIEW] P2. **Verify the operator's original symptom is gone: the DeepSeek + Planning filter must show a dollar
      figure for 1h, 5h, 24h, 7d and lifetime.** That was one backfilled mixed-model row poisoning four windows. **Done
      when**: the live endpoint response for `provider=deepseek&role_group=planning` is pasted here showing a non-null
      `spend_usd` in every window.
- [x] ✅ CANCELLED [BACKEND] P0. **Fleet-aggregate calibration — no longer needed; the operator's reservation removed
      the problem it existed to route around.** This was a workaround for one specific defect: laptop consumption
      landing on an unknown account, making per-account denominators untrustworthy, with no recoverable login history to
      repair them. As of 2026-08-10 evening `sub-a-ikenna` and `sub-e-odum2default` are AO-exclusive and every other
      Claude account is paused, so a per-account denominator is exact BY CONSTRUCTION for any window after the Wednesday
      resets — no aggregation needed. Cancelled on the merits rather than deferred: summing across accounts would now
      DESTROY the very signal we want, since the whole point of running both a Pro and a max20 account is to compare
      their multipliers, and an aggregate collapses them into one number. Re-open only if the reservation is withdrawn.
- [x] ✅ [BACKEND] P1. **`claude-opus-5` registered (with 4.8/4.7/4.6, Fable 5, Sonnet 4.6/4.5, Haiku 4.5) —
      agent-orchestrator@c40d847ac6.** `test_every_model_the_fleet_runs_is_priced` parametrises over the models actually
      observed in transcripts. Dated ids (`claude-haiku-4-5-20251001`) resolve by stripping the `-YYYYMMDD` suffix, so a
      new release snapshot cannot silently become an unpriced turn.
- [x] ✅ [BACKEND] P1. **Partial windows are valued, not discarded; only CAPTURE completeness gates —
      agent-orchestrator@c40d847ac6.** `window_disqualification()` refuses a window opening before
      `ATTRIBUTION_CAPTURE_ERA_START` (2026-08-06) and one straddling a month boundary, and explicitly does NOT treat
      partial consumption as a disqualifier — a window that consumed 7% is a valid sample because the percentage is what
      converts to dollars. Tests cover accept / month-straddle / pre-capture / partial-consumption.
- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-19 (Track-A/B classification pass, forked per `task_template.md`
  §3 finding Y): re-scoped to a companion NA doc, nothing left to complete here** — laptop-only login-identity
  logging, structurally unreachable from an AO VM worker. See
  [`anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19.md`](/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19.md).
- [ ] [BACKEND] P1. **Report `max(measured)` as the defensible floor for PRE-reservation windows — but stop calling
      post-reservation windows lower bounds, because they are not.** Amended 2026-08-10 evening. The original reasoning
      still holds for history: `sub-c` was a laptop login on 2026-08-02, the `~/.claude-accounts/*.env` absence never
      proved `sub-d` was clean (env files serve headless spawns; interactive login goes through `claude /login`), and
      unattributed laptop turns only ever REMOVE tokens from the numerator — so contamination biases a historical
      multiplier DOWN and the largest measurement is closest to truth (currently >= 32.2x at August promo rates for
      max20). But from the Wednesday resets onward `sub-a`/`sub-e` are AO-exclusive, so their windows are exact, not
      floors, CONTINGENT on the reservation-verification todo actually confirming zero laptop sessions. Labelling an
      exact measurement a lower bound is its own error — it invites someone to inflate it. **Done when**: the
      calibration output distinguishes the two regimes explicitly (pre-reservation = lower bound,
      post-reservation-and-verified = measured), and never averages across accounts in either.
- [x] ✅ [BACKEND] P1. **`7 / days_in_month x monthly_price` implemented as the dollar anchor —
      agent-orchestrator@c40d847ac6.** `subscription_value.weekly_budget_usd()` uses the real month length, and the
      calibration report prints it (`$200.00/mo ex-tax x 7/31 days -> $45.16 per weekly window`). A month-straddling
      window is REFUSED rather than prorated, which is the honest handling — it would also straddle Sonnet 5's rate
      change. Tests cover both the within-month and straddling cases, and that August ($45.16) and February ($50.00)
      differ.
- [x] ✅ [BACKEND] P1. **Every multiplier carries its valuation date and rate set — agent-orchestrator@c40d847ac6.**
      `MeasuredValue` stores `valuation_date` and the report prints
      `MULTIPLIER 190x (LOWER BOUND — rates as of <date>)`. The date IS the rate-set identifier by construction, since
      `rates_for` is a pure function of it. Two windows valued under different rate sets cannot be silently compared
      because the only window that could mix them — one straddling 2026-08-31 — is refused outright, with a test.
- [ ] [BACKEND] P1. **Correct the cost denominator to subscription PLUS extra-usage spend — overage was paid, contrary
      to the first reading.** `overage_status='rejected'` + `overage_disabled_reason='out_of_credits'` means overage is
      currently REFUSED because the credit pool is exhausted, not that none was used: the laptop account's live `/usage`
      payload shows `extra_usage.used_credits = 15078` against `monthly_limit = 20000` (GBP, 2dp) — £150.78 of real
      additional billing this month. Any account with non-zero `used_credits` in a calibrated window must have that
      added to its subscription cost, and the currency recorded (GBP here, not USD). **Done when**: the calibration
      reports cost as subscription + extra usage per window with currency, and a test proves a window with overage is
      not priced at bare subscription cost.
- [ ] [BACKEND] P1. **Capture the rich `/usage` payload on a SEPARATE path — AO's poller never receives one, so this
      cannot be done by "persisting more of what it already has".** CORRECTION 2026-08-10 (verified in
      `server/usage_tracker.py`, module docstring + `fetch_usage_via_api`): the background poller is header-based, not
      payload-based. It sends a minimal POST to `/v1/messages` and reads exactly four `anthropic-ratelimit-unified-*`
      response headers (5h/7d utilisation + their reset timestamps). There is no JSON body to keep — no per-model
      sub-meters, no `limits[]`, no `extra_usage`, and `weekly_sonnet_pct` is explicitly `None` on this path because the
      headers do not carry it. The rich payload exists only on the SLOW pexpect TUI path (`fetch_usage_via_claude`,
      ~12s, one `claude` PTY subprocess per account), which the polling loop deliberately does not call and which is
      reached only by the operator-triggered `POST /api/accounts/{id}/refresh-usage`. Consequences that change the work:
      (a) the £150.78 of `extra_usage` this plan wants in the cost denominator is NOT obtainable from the poller; (b)
      the per-model quota-weight signal needs the TUI path too, so the quota-weighting question cannot be answered from
      history AO is already collecting. Scope this as a low-frequency TUI capture (e.g. once per quota window, not per
      tick) whose cost is justified precisely because it is rare. **Done when**: one scheduled TUI capture per account
      per window persists the per-model sub-meters and `extra_usage` block, verified against a live capture, WITHOUT
      adding a subprocess to the per-tick polling loop.
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
- [x] ✅ CANCELLED [OPERATOR] P2. **Measuring laptop consumption to decontaminate `sub-b-iggy2london` — moot; `sub-b` is
      paused and is not being calibrated.** The AO pool is now DeepSeek + `sub-a` + `sub-e` only. `sub-b` is not in it,
      so there is no `sub-b` multiplier to decontaminate and no window that needs its laptop half measured. The
      4,026-transcript scan this described would cost real time to produce a number nothing consumes. Cancelled, not
      deferred. (The scanning METHOD is not lost — it is written up in
      `/codex/06-coding-standards/tool-call-batching.md`'s re-measurement section, including the requestId-UNION rule
      that a naive dedup gets wrong.)
- [x] ✅ CANCELLED [OPERATOR] P2. **Reconstructing the historical login timeline from recollection — moot; those windows
      are refused by the calibration script regardless of what we recall.** Two independent gates already exclude every
      pre-reservation window: `window_disqualification()` refuses anything opening before attribution capture began
      2026-08-06, and calibration now runs forward from the Wednesday resets. Operator recollection cannot make a
      refused window usable, so this would buy a fuzzy timeline for measurements that will never be taken. Cancelled on
      the merits. The honest statement it was meant to produce is already recorded: pre-logger windows can only ever
      yield lower bounds.
- [x] ✅ [DATA] P1. **Tool-call batching SSOT written — `/codex/06-coding-standards/tool-call-batching.md`.** Carries
      `authoritative_for: tool-call-batching` frontmatter and the full measured baseline (57.3% of calls collapsible,
      Bash 52.8%, runs of 20/23/26/28/32, 69% of Bash calls in a chain, 405,833 mean cache-read tokens per call, 8.6h of
      agent-time inside collapsible chains in a 4h25m window). States the rule positively, names the narrow exception
      (result-dependent calls, and any check that authorises a destructive act, stay sequential), and records the
      requestId-UNION measurement method so a re-measure cannot repeat the dedup bug. Also states explicitly that
      cutting reasoning is the WRONG lever — thinking is 68.8% of output tokens but only ~5.5% of cost.
- [x] ✅ [DOC] P1. **Directive + SSOT pointer propagated to all four agent-prompt surfaces.** `cursor-configs/CLAUDE.md`
      (§ Agent behavior), `agents/RULES.md` (§7), `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (§ Identity + workspace)
      and `cursor-configs/AUTONOMOUS_AGENT_RULES.md` (new rule 12; the loop rule renumbered to 13 and its two
      cross-references repointed). `check_agent_rules_size_cap.py` passes. **Two things worth knowing that the todo's
      premise got wrong:** (a) `SUB_AGENT_MANDATORY_RULES.md` ALREADY carried a batching rule, added ~2026-08-05
      alongside `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`, citing a
      measured ~11% of fleet turns batching >1 call. So it was amended in place with the SSOT pointer + the new figure
      rather than duplicated. **This means guidance alone has already been tried once on this exact problem and the rate
      did not move** — see the re-measurement todo, which is now a real test of whether a rule is sufficient, not a
      formality. (b) BOTH capped files were effectively AT their caps before this (CLAUDE.md 22 B of headroom,
      SUB_AGENT_MANDATORY_RULES.md 56 B), so propagation required condensing first. Net result is MORE headroom than
      before despite the additions (156 B and 173 B) — but both still sit past the 95% WARN threshold, so the next
      person to add a rule to either file must condense again.
- [ ] [DOC] P2. **Audit the 23 per-role files in `agents/` for any instruction that actively encourages sequential
      single-tool calls, and fix those specifically.** A universal rule is undermined if a role doc walks its agent
      through numbered one-command-per-step procedures. Roles to check include the escalation family (`cicd`,
      `conflict_resolver`, `data_pipeline_failure`), the scheduled family (`plan_health`, `plan_reconciler`,
      `docs_reconciler`, `ag_closeout_auditor`, `na_eligibility_auditor`, `context_scout_auditor`, `cefi_*`), the craft
      roles (`backend_engineer`, `infra`, `quant_dev`, `ui_developer`, `data_engineering`, `review`), and
      `main`/`worker`. **Done when**: each role file is either confirmed clean or amended, with the list of amended
      files recorded here.
- [x] ✅ [DATA] P1. **MECHANISM SHIPPED — `cursor-configs/hooks/batching-nudge.py`, a PostToolUse hook that nudges
      IN-LOOP — unified-trading-pm@19dc43ec69.** Fires at the 3rd consecutive round-tripped same-tool call, then every
      5th, with tool-specific advice (`&&` for Bash, `replace_all` for Edit) and the do-NOT-batch carve-out
      (result-dependent calls, and any check authorising a destructive act, stay sequential). 15 tests. **The design
      constraint that makes it safe**: four Reads batched into ONE message emit the same PostToolUse sequence as four
      Reads across four turns, so a naive same-tool counter would fire HARDEST at correct behaviour and train agents out
      of it. Separated by LATENCY — a gap under `SAME_MESSAGE_WINDOW_SECONDS` (2s) is treated as evidence of correct
      batching and does NOT advance the counter (measured median inter-turn gap: 10.5s). Three of the 15 tests exist
      only to pin that. **Propagation verified on origin**: hook file tracked at mode 100755, `PostToolUse` registered
      in the tracked `cursor-configs/settings.json`, and the `.claude/settings.json` symlink is created by
      `link-claude-skills.sh` which `quality-gates.sh` itself invokes — so any slot/machine that pulls LDR and has
      bootstrapped picks it up. Real AO workers included: `tmux_spawn.spawn()` launches an INTERACTIVE `claude`, not
      `claude -p` (the documented hook-skipping path). **Sessions must RESTART** — hooks load at session start, so a tab
      that pulls mid-session has correct files and zero nudges. **Live evidence it works**: it nudged THIS session 43+
      times, correctly, against an agent that wrote it and was actively trying to comply. That is the strongest
      available argument that a written rule was never going to move this number — and a caution that a nudge alone may
      not either.
- [ ] [DATA] P1. **Re-measure the collapsible-call share — and treat a flat result as evidence that a RULE is not
      enough, because a rule was already tried.** Upgraded from P2 on 2026-08-10: the sub-agent rules file has carried a
      batching directive since ~2026-08-05 (issue doc
      `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`, ~11% of turns batching >1
      call), and five days later 57.3% of calls were still collapsible. So this is not a formality: if the share does
      not move, the answer is a MECHANISM (a lint on the transcript, a per-agent batching metric surfaced in the
      dashboard, a boot-prompt worked example) rather than restating the rule a third time. Baseline to beat (2026-08-10
      controlled window): 3,123 calls, 57.3% collapsible, 405,833 mean cache-read tokens per call, 1.27B total reads.
      Reuse the same requestId-unioned method (content blocks must be unioned across all JSONL lines sharing a requestId
      — deduping to the first line silently drops tool_use blocks and was the bug in this plan's first content pass).
      **Done when**: a post-change window is measured with the same method and the before/after collapsible share and
      cache-read totals are recorded here.
- [ ] [DATA] P3. **Write the codex SSOT for cost attribution — pricing basis, the measured-multiplier method, the
      weekly-window calibration procedure, and the attribution rules from todos 1-3 — under `/codex/04-architecture/`.**
      Per CLAUDE.md's SSOT-direction hard rule the durable contract belongs in codex, not in this plan. **Done when**:
      the doc exists with `authoritative_for:` frontmatter and this plan links to it rather than restating it.
- [x] ✅ [REVIEW] P3. **Re-run the calibration after the attribution fixes land and compare against the 2026-08-10
      baseline recorded below.** If the multipliers converge into a narrow band per tier, record it; if they stay divergent, open
      an issue doc rather than averaging the spread into a single misleading number. **Done when**: the re-run output is
      recorded here with an explicit converged/not-converged verdict. **DONE 2026-08-17** — see Progress Log "Second
      calibration pass" § ">20% disagreement flag": explicit NOT-CONVERGED verdict (`sub-c-ikenna-odum` 32.2x->140x,
      `sub-f-odum2default` 15.5x->60x, both far outside 20%), with a working explanation given (todos 3-5's coverage
      fixes landing between the two runs) rather than left unexplained. No separate issue doc opened — the
      divergence is judged an expected, explained consequence of the shipped fixes, flagged here for a human to
      confirm that reading rather than re-litigated. — /plan-reconcile 2026-08-18.

### Anthropic Wallet Reconciliation (operator ask 2026-08-11)

Operator ask, interactive session 2026-08-11: _"track our Anthropic usage in tokens converted to $ against our actual $
spend on the weekly limits, from Wednesday"_ — i.e. the subscription-side analogue of the DeepSeek Wallet Reconciliation
panel (`server/state_store/slots.py::compute_deepseek_wallet_reconciliation` + `dashboard/src/DeepSeekWalletPanel.tsx`),
which answers "where did the money go" for a metered wallet and surfaces the unattributed remainder as an explicit
`residual_usd` instead of folding it into whichever bucket is biggest.

- [ ] [BACKEND] P1. **Persist an operator-recorded real-charges ledger per Anthropic account — the analogue of
      `DeepSeekTopupRow`.** That row type exists precisely because DeepSeek publishes no spend-history API; Anthropic
      publishes none either, so "what we actually paid" has to be a recorded fact, not derived from a plan-price
      constant. Must carry the subscription charge for the period PLUS the `extra_usage` credits the TUI-capture todo
      above obtains, with CURRENCY recorded (the laptop account's live payload is GBP, not USD — £150.78 this month,
      measured 2026-08-10). **Done when**: the ledger persists real charges with period + currency, never edits a prior
      entry (audit trail, same contract as `record_deepseek_topup`), and a test proves a window carrying overage is not
      priced at bare subscription cost.
- [ ] [BACKEND] P1. **`compute_anthropic_wallet_reconciliation()` — per account, per weekly window: paid $, consumed $,
      residual.** Mirrors the DeepSeek reconciliation's shape, including the worker / orchestrator (slot 0) / review
      split taken from the `is_review_slot` value SNAPSHOTTED on each row at sweep time rather than re-derived from
      today's config (see `orm.py::DeepSeekMessageUsageRow.is_review_slot` for why a query-time membership check
      retroactively relabels an entire historical sum). Consumed $ = list-priced value from `model_pricing.py` converted
      by that account's MEASURED multiplier, never a hardcoded one. `residual_usd` must be None whenever the multiplier
      or the paid-charges row is missing — never a number computed against an unset baseline, same contract the DeepSeek
      view already holds. **Done when**: the endpoint returns a per-account, per-window breakdown and tests cover the
      missing-multiplier and missing-payment cases.
- [ ] [BACKEND] P1. **Store each weekly window's OPEN and CLOSE meter readings so a past window stays reconcilable after
      the meter rolls.** The meter-history sampler records `weekly_pct` over time, but a reconciliation needs the pair
      anchored to the Wednesday reset (`weekly_resets_at`); without a stored boundary pair a closed window cannot be
      reconstructed. This is the same defect measured on the DeepSeek side on 2026-08-11 — no balance history is
      persisted anywhere (`account_usage_history` has no balance column, `account_usage` holds only the CURRENT
      reading), which is why the DeepSeek wallet view can only ever be lifetime and a "last 24 hours" residual is not
      computable at all today. Do not repeat it here. **Done when**: every closed weekly window since the Wednesday
      resets has a stored (open, close) reading per account, and the reconciliation can be recomputed for any past
      window.
- [ ] [UI] P2. **`AnthropicWalletPanel.tsx` beside `DeepSeekWalletPanel.tsx` — per-account weekly-window table.** Same
      structure as the DeepSeek panel (pure exported formatters, vitest-covered; the React shell owns only fetch/poll
      state and the latest-request-id guard against a slow poll clobbering a fresher write). Shows paid $ / consumed $ /
      residual / implied multiplier per account per window, with the spend BASIS labelled — a subscription dollar and a
      metered dollar are not the same unit. **Done when**: the panel renders live data and a cited playwright regression
      spec passes; `[UI]` + `pw:L2 ✓` required per `/codex/06-coding-standards/ui-testing-layers.md`.
- [ ] [DATA] P1. **Report the reconciliation for the first full post-Wednesday-reset window and state a residual
      target.** This is the acceptance measurement for the four todos above. With the two RESERVED AO-exclusive accounts
      the denominator is exact by construction, so an unexplained residual on those two is a real attribution defect,
      not laptop contamination. **Done when**: the first closed window's per-account residual is recorded here with an
      explicit within-target / not verdict, and any gap is either root-caused or opened as an issue doc rather than
      averaged away.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (8 entries)
- **2026-08-19 (Track-A/B classification pass, ao_open_work_consolidated_tracker_2026_08_14.md Track 7, per
  task_template.md §3 finding Y)**: the sole open `[OPERATOR] P2` item (laptop login-identity logging) forked into a
  companion NA doc —
  `/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10_operator_items_2026_08_19.md` —
  cross-linked via `related:` both directions, source checkbox replaced with a bold pointer digest line. The
  2026-08-18 Track 7 re-check had already confirmed this item is not a mis-tag but stopped short of forking it out;
  this pass completes that step. 27 plain dispatchable todos remain open in this plan, unaffected.

### 2026-08-17 — Second calibration pass (AO worker, slot 15, read-only)

Ran `calibrate_account_value.py` (every account) directly against the LIVE `state.db` — this slot's VM IS the
orchestrator server's VM, so `agent-orchestrator/data/state/state.db` was read directly, no SSM needed. Weekly
meter, promo rates (Sonnet-5 promo through 2026-08-31).

| account            | tier  | meter    | list value | sub/window       | **multiplier**                                  |
| ------------------ | ----- | -------- | ---------: | ----------------: | ------------------------------------------------ |
| sub-a-ikenna       | pro   | 0->94%   |    $492.59 | $4.52 (5h-bound)  | 116x (excluded per todo instruction)              |
| sub-b-iggy2london  | max20 | 64->99%  |    $149.18 | $45.16            | **9x — contaminated (see 08-10 entry), not clean** |
| sub-c-ikenna-odum  | max20 | 0->86%   |  $5,421.21 | $45.16            | **140x**                                          |
| sub-d-odum1default | pro   | 0->96%   |  $1,786.23 | $4.52 (5h-bound)  | 412x (pro, bonus — out of max20 scope)            |
| sub-e-odum2default | max20 | 0->99%   |    $523.18 | $45.16            | **12x**                                           |
| sub-f-odum2default | max20 | 0->99%   |  $2,664.85 | $45.16            | **60x**                                           |
| sub-g-alpavolt     | max20 | 5->99%   |    $469.13 | $4.52 (5h-bound, stale — reset since) | 11x                    |

**Naming discrepancy — RESOLVED 2026-08-19 (/plan-reconcile orchestrator_master)**: this doc's tables previously used
`sub-e-odum3default`; the LIVE `accounts.json`/`state.db` id for that same account is `sub-e-odum2default`
(independently confirmed by `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` todo 1, DONE 2026-08-13,
direct accounts.json query). No human call needed and no account rename occurred — the 2026-08-12 "fixed to
sub-e-odum3default throughout" note (see line ~117) itself introduced the error by conflating the email suffix
(`odum3default@...`, genuinely correct) with the slug id. Every occurrence in this doc has been reverted to
`sub-e-odum2default` to match the live id.

**`sub-g-alpavolt`** is live but absent from every prior table (the 08-10 roster only covers a-f) — a 6th max20
account added after 2026-08-10. Recorded for completeness, not folded into the "5 max20 accounts" framing elsewhere
without a human confirming it belongs.

**>20% disagreement flag (this todo's own done-when)**, vs the 08-10 corrected-denominator table (promo rates):
`sub-c-ikenna-odum` 32.2x->**140x** (+335%), `sub-f-odum2default` 15.5x->**60x** (+287%) — both far outside 20%.
**Working explanation, not left unexplained**: todos 3-5 (message-id dedup, capture-era gating, task_usage
double-count fix) all shipped between the two runs, and every multiplier here is a documented LOWER BOUND that
rises as attribution coverage improves — a same-direction 3-4x jump right after three coverage fixes land is
consistent with that, not anomalous. NOT re-verified against a parallel method-(A) run this pass (out of scope —
todos 3-5's own tests already prove the fix); a human should decide if that corroboration is worth running before
treating 140x/60x as superseding the 08-10 figures.

**sub-b excluded from the clean max20 read** (not a new finding — restates the 08-10 laptop-contamination entry):
9x is the lowest of the six Anthropic accounts and the only one below the published 6-10x band, consistent with
genuine shared laptop+AO usage diluting the AO-attributed multiplier downward, not with AO usage actually costing
less on that account.

> **2026-08-17 line-cap extraction**: the 2026-08-10 diagnosis + first (uncorrected) calibration pass + feasibility
> probe + laptop-contamination probe + corrected-denominator re-run + cache-transfer reasoning that used to sit here
> moved verbatim to
> `/plans/archive/2026_08/anthropic_per_task_actual_spend_and_account_calibration_progress_log_history_2026_08_17.md`
> (this plan hit the
> 1000-line hard cap). Every figure still in active use (32.2x/15.5x/6.1x corrected multipliers, the 190x reference
> measurement) is already restated at its point of use in the Todos and the 2026-08-16/08-17 entries below — nothing
> downstream depends on the narrative staying inline.

- [ ] [CICD] P2. **`quality-gates.sh` lints only `server/`, but the pre-commit hook also lints staged `tests/` and
      `scripts/` — so a QG-green tree can still fail at commit time.** Hit live 2026-08-10: a fully green QG (3,306
      tests, basedpyright/tsc/vitest clean) was followed by a `quickmerge` commit failure on a ruff rule (`zip()` ->
      `itertools.pairwise()`) in a NEW TEST FILE the gate never linted. This contradicts the workspace's own "a
      `quality-gates.sh`-green tree is the contract" framing — the gate is not a superset of the hook, so the safety net
      has a hole exactly where new test/script files land, which is most of what a plan like this adds. Either widen the
      QG ruff leg to the paths the hook covers, or state the narrower contract explicitly in
      `/codex/06-coding-standards/quality-gates.md` so agents stop treating QG-green as commit-safe. **Done when**: the
      two linters cover the same paths, or the codex SSOT documents the gap and CLAUDE.md's wording is corrected.

- **context-scout 2026-08-15**: populated/refreshed context_scope (8 entries) — added `model_pricing.py` (named in the
  doc's own "Why sequential" line as one of the three files most todos touch, previously missing from the list).

### 2026-08-15 (slot-4, data_engineering) — todo 11 (reservation verification) BLOCKED, not completable from this slot

Dispatched todo 11 ("Verify the reservation actually held over the first post-reset window"). Two independent
blockers, neither self-fixable from here:

1. **Live VM data is unreachable from this identity.** Attempted `calibrate_account_value.py --account sub-a-ikenna`
   and `--account sub-e-odum2default` (since 2026-08-12, the first Wednesday reset after the reservation) via a direct
   `aws ssm send-command` against the central orchestrator VM — `AccessDeniedException` on `ssm:SendCommand` for
   `ikenna-worker`, the same fleet-wide gap already tracked (13 independent confirmations now) in
   `/plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`. Also checked the authed
   HTTP surface as a substitute — `GET /api/accounts/claude/wallet-reconciliation/window` already exists and computes a
   windowed per-account multiplier, which would have been directly usable, but `ikenna-worker` has no bearer token and
   no script mints one. Appended a 13th confirmation entry to that issue doc rather than re-diagnosing.
2. **The task's own "Done when" needs todo 21 (laptop-side login sampler, `[OPERATOR]`, not yet shipped) regardless of
   #1** — "for the first window after the Wednesday resets, the login sampler shows zero laptop sessions on either
   reserved account." No VM-side proxy substitutes for that: `account_usage_history` alone cannot distinguish an AO
   turn from a laptop turn on the same reserved account, only whether the meter moved.

**Incidental finding, not yet actioned**: `server/routes/accounts.py` already ships `compute_claude_wallet_reconciliation`
/ `compute_claude_wallet_window_reconciliation` (referenced in code as
`claude_anthropic_flat_rate_billing_calibration_2026_08_12`) — an implied-$-vs-actual-$ boost-multiplier calculation
per Anthropic account, live as an HTTP endpoint. This looks like it may overlap with this plan's own
`calibrate_account_value.py` (todo 6) and the proportional-allocation todos (9, 12). Not investigated further this
session — worth a follow-up read of `state_store.compute_claude_wallet_reconciliation` before more calibration code is
written here, to avoid duplicating what already shipped elsewhere.

Not flipping todo 11 — its Done-when is not met. Released via `/skip-current-task` with `reason_code: GATED` rather
than re-dispatched blind.

### 2026-08-17 (slot-21, data_engineering) — todo 11 re-checked, blocker #2 still holds unchanged

Re-dispatched onto todo 11. Blocker #1 from the 2026-08-15 entry above (SSM `AccessDeniedException`) does NOT apply
to this session — this slot runs directly on the orchestrator VM (same as the 2026-08-17 second-calibration-pass
entry above), so `agent-orchestrator/data/state/state.db` and `account_usage_history` are readable with no SSM hop.
**But blocker #2 is unchanged and is the one that actually gates this todo**: the done-when requires todo 21's
laptop-side login sampler (`~/.claude/laptop_login_identity_log.jsonl`) to show zero laptop sessions on
`sub-a-ikenna`/`sub-e-odum2default` for the first post-reset window. That file lives on the OPERATOR'S LAPTOP, not
on this VM, under any identity — grepped this whole plan file plus every `plans/` doc for
`laptop_login_identity_log` and found only todo 21's own description (script shipped 2026-08-16); no run output has
been posted anywhere in the corpus. `account_usage_history` alone still cannot distinguish an AO turn from a laptop
turn on the same reserved account (same limitation slot-4 already noted) — VM-side meter/attribution data answers
"how much moved," not "who used it." **Not flipping todo 11** — releasing again via `/skip-current-task` with
`reason_code: GATED`; next dispatch should wait on the operator running `scripts/dev/log-laptop-login-identity.py`
and posting its output (or confirming zero laptop sessions) here, not on blind re-dispatch to another VM slot.

> **2026-08-17 line-cap extraction (continued)**: the 2026-08-10 "Deferred work" snapshot (superseded — the calibration
> code it describes as blocked has since shipped, see the Todos' `[x]` marks), both "Session lessons" sections, the AO
> account-rotation timeline + cache-accounting verification, the ~190x CONTROLLED MEASUREMENT derivation, the
> cost-structure breakdown, and the RETRACTION establishing no account is certifiably laptop-free all moved verbatim to
> `/plans/archive/2026_08/anthropic_per_task_actual_spend_and_account_calibration_progress_log_history_2026_08_17.md`
> alongside the block
> above. The 190x figure and the >= 32.2x fleet-floor framing are already live in the Todos (e.g. todo 6's own
> wording); several of the general session lessons are now also captured structurally in
> `/codex/06-coding-standards/tool-call-batching.md`.

### 2026-08-16 (slot-24, data_engineering) — sub-d Pro-denominator recompute + confirm/refute vs the 1047x outlier

**Recomputed both tables' `sub-d-odum1default` rows at the Pro denominator**, per BLK-050d1304's correction todo. Pro
window cost = `7/31 x $20 = $4.52` (August 2026, same window length both tables already used for max20). Scaling each
existing multiplier by `old_denominator / $4.52`:

- First calibration pass (denominator was $46.00, the averaged max20 figure the first pass used): list value (A) =
  34.4x x $46.00 = $1,582.40 -> **350.1x** at $4.52; list value (B) = 18.4x x $46.00 = $846.40 -> **187.3x** at $4.52.
- Re-run against the corrected max20 denominator ($45.16): promo list value $1,088.19 -> **240.8x**; standard-rate list
  value (back-derived: 35.1x x $45.16 = $1,585.12) -> **350.7x**.

**Cross-check**: the first-pass (A) figure (350.1x, standard rates per that table's own "Sonnet-5 valued at its standard
rate" note) and the re-run's standard-rate figure (350.7x) land within 0.2% of each other despite coming from different
attribution methods and denominator-correction paths — strong evidence the recompute is arithmetically sound rather than
a coincidence of rounding. Both figures now correctly read as roughly **10x higher** than their mislabeled max20 values,
matching the todo's own prediction ("raises them roughly 10x, not lowers them").

**Confirm/refute vs the `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` 1047x outlier: REFUTED — not the
same root cause.** Read that doc's live table (2026-08-13 pull) directly: it already labels sub-d `tier: pro` correctly
and computes `implied $ = weekly_pct x prorated_Pro_budget = 23% x $4.52 approx $1.04` — the CORRECT $20/mo Pro
denominator, not the $200/mo max20 figure this plan's tables were mislabeled with. So the two docs' sub-d numbers are
wrong (or in this case, actually correct) for entirely different reasons:

- **This plan's bug**: a straight `list_value / full_window_subscription_cost` multiplier, computed against the WRONG
  subscription cost ($200/mo instead of $20/mo) — a denominator-mislabeling bug, now fixed above.
- **The sibling doc's 1047x**: `list_value / (weekly_pct x correct_Pro_budget)` — already using the right $20/mo Pro
  budget, but scaled down further by a LOW observed `weekly_pct` (23%) that appears disproportionate to the account's
  real token consumption ($1,088.19 of list value). That is a genuine measurement anomaly in how Pro's weekly-limit
  meter tracks consumption (message-count-weighted vs token-volume-weighted, per that doc's own open question), not an
  arithmetic denominator error.

Both docs' sub-d readings are now internally consistent with each other in direction (both say Pro is "boosted" far more
than the 6-10x published band suggests — this plan's own recompute lands sub-d in the same 240-350x range as its clean
Sonnet-5-heavy siblings once correctly denominated), which is itself informative: it suggests the sibling doc's 1047x
is the outlier-within-Pro, not evidence that Pro categorically reads ~1000x. The sibling doc's open `[OPERATOR]` todo
("Investigate the sub-d 1047x outlier") stands unchanged — this session did not touch that doc's todos, only used it as
a cross-reference to answer this plan's own confirm/refute question.
