---
doc_type: issue
title: "Claude/Anthropic flat-rate billing calibration — derive a real $-per-token multiplier for Max/Pro subscriptions"
summary: >-
  New initiative proposed by the operator 2026-08-12, directly following the DeepSeek native-usage-capture proxy work
  landing the same day. Anthropic's Max ($200/mo) and Pro ($20/mo) plans are flat-rate, not metered — Anthropic never
  tells you how your actual token usage maps to subscription value. The ask: derive that mapping ourselves by comparing
  Anthropic's own %-of-weekly-limit signal (converted to an implied $ figure via day-prorated subscription cost) against
  our own captured token usage priced at Anthropic's published per-token list rates, for the SAME clean, AO-only-usage
  account and time window. The resulting ratio is a "boost multiplier" — how much more effective value a flat-rate
  account delivers vs. metered API pricing. Also requires the same crash-durability guarantee already built for DeepSeek
  (capture usage even if a tmux session dies before completing a turn), and a new "Claude Wallet Reconciliation"
  dashboard widget mirroring the existing DeepSeek one. Captured here in full rather than left in chat, per this
  workspace's session-checkpoint discipline. **2026-08-13**: plan destination confirmed human-driven, and the
  data-source open question resolved — no API exists for the %-of-weekly-limit signal, it requires a new tmux
  `/usage`-driving sampler (see dedicated sections below). Critical-path implementation work (the sampler) has NOT yet
  been built — this doc still tracks an unimplemented initiative, now with a concrete architecture instead of open
  questions.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, anthropic, claude, billing, spend, cost-attribution, wallet-reconciliation]
related:
  [
    /plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md,
    /codex/06-coding-standards/model-tier-selection.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
context_scope:
  - agent-orchestrator/server/state_store/account_usage.py
  - agent-orchestrator/server/usage_poller.py
  - agent-orchestrator/server/model_pricing.py
created: 2026-08-12
last_updated: 2026-08-13
parent_epic: orchestrator_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Operator chat instruction, 2026-08-12, immediately following the DeepSeek native-usage-capture proxy landing — "now
  there is a plan around this for a max account... same for pro which is a different multiplier... together with our
  deepseek stuff we'd have good billing across Accounts and Task Token Usage and DeepSeek Wallet Reconciliation and our
  new widget Claude Wallet Reconciliation."
execution_scope: local-only
drift_direction: advance-code
---

# Claude/Anthropic flat-rate billing calibration

## The core idea, as the operator described it

Anthropic subscriptions (Max $200/mo, Pro $20/mo) are flat-rate — you pay the same regardless of usage, up to a
weekly-resetting limit Anthropic enforces but never translates into a dollar figure for you. The proposed calibration
method:

1. Take a **clean, AO-only-usage account** (no interactive/laptop sessions mixed in, so its weekly usage is attributable
   entirely to fleet work) over a **known window** (e.g., 7 days within August).
2. Compute that window's **prorated subscription budget**: `monthly_price × (window_days / 31)`. Worked example from the
   operator: `$200 × (7/31) ≈ $45.16` for a Max account over one week.
3. Read Anthropic's own **%-of-weekly-limit-used** signal for that account/window — **Open Question 1 answered
   2026-08-13, see the dedicated section below: there is no API for this, it must be read from a live `/usage` command
   in an active Claude Code session.**
4. Multiply: `% used × prorated budget = implied $ spent` — e.g., operator's own example, "if we use 1% on a task that's
   $0.45 roughly spent" (1% × $45.16 ≈ $0.45).
5. Separately, compute what that SAME window's actual captured token usage would cost at **Anthropic's published
   per-token list rates** (already in this repo: `agent-orchestrator/server/model_pricing.py`'s Anthropic rate cards —
   input/output/cache-read/cache-write, per model, date-effective).
6. The ratio between (4) and (5) is the **"boost multiplier"** for that plan tier — expected to differ between Max and
   Pro since they're different plans with (presumably) different usage-to-limit ratios.
7. Once calibrated, apply the multiplier to **backfill more accurate effective-cost numbers** for Claude usage generally
   — i.e., convert list-price-equivalent token costs into "real value extracted from the subscription."

## Named test accounts (operator-specified, 2026-08-12; sub-E swap 2026-08-13)

The operator has committed to NOT using the clean sample account(s) for interactive/laptop sessions, specifically so
they stay "clean" AO-only samples for this calibration:

- **sub-E, `odum3default@gmail.com`** — **Max** plan ($200/mo). **CONTAMINATED as of 2026-08-13** — the operator had to
  use this account directly on their laptop ("i gotta use account odum3 right now else we can't even get any work done
  on my laptop") to keep working, which invalidates it as a clean AO-only sample for the CURRENT weekly window. Do not
  use any Max-tier data from this account's current window for calibration; it remains a valid sample again only after
  its next weekly reset, and only if it goes untouched interactively from that reset forward.
- **sub-F, `odum2default@gmail.com`** — **elected as the replacement clean Max-tier sample**, operator instruction
  2026-08-13. Already configured to allow AO jobs (no setup needed). Its weekly reset is **under 11 hours away as of the
  2026-08-13 instruction** — meaning any AO-only usage accrued on sub-F before that reset is itself a partial/short
  window, and a genuinely clean full-week sample won't be available until the reset AFTER that one. Use sub-F in place
  of sub-E everywhere below.
- **sub-D, `odum1default@gmail.com`** — **Pro** plan ($20/mo), unaffected by this swap. (Operator's message names
  "Ikenna — sub D" for this one; the exact account-label mapping should be double-checked against `accounts.json`/the
  `.claude-accounts/*.env` files before use, same as every DeepSeek account-identity check this workspace has needed all
  session.)

**Caveat directly from the operator, stated as a known risk, not an aside**: "the issue is when we use those accounts
locally on my laptop skews the results" — i.e., the calibration is only valid for a window where the account was
GENUINELY AO-only. The sub-E contamination above is exactly this risk materializing, not a hypothetical — treat any
future accidental laptop use of sub-F/sub-D the same way: it contaminates that account as a calibration sample going
forward until its next weekly reset.

## Requirement 2: crash-durability for Claude usage capture, same as DeepSeek

Direct quote: "just like DeepSeek need to make sure that even if a tmux session is killed before completing, we still
get the token balances that we need to calculate the billing, so we don't lose short sessions in our billing."

**Important framing difference from the DeepSeek case, worth stating explicitly so nobody re-derives the wrong
architecture**: DeepSeek needed a translating proxy because DeepSeek's own `/anthropic` compat endpoint was LOSSY — it
discarded native cache-hit/cache-miss fields server-side before the response ever reached us. Claude/Anthropic accounts
have NO equivalent lossy layer — the `claude` CLI talks to Anthropic's REAL, NATIVE Messages API directly, so
token-count ACCURACY is not the same open question here. The remaining gap is purely the CRASH-DURABILITY one: if a tmux
session dies after Anthropic has already generated and billed tokens but before the CLI finishes writing its own
transcript, that usage is invisible to the existing transcript-sweep capture path — exactly the class of loss the
DeepSeek proxy's "persist usage before relaying the response" design closes as a side effect, not its primary purpose
there. For Claude, a MUCH SIMPLER proxy could close this same gap — a transparent capture-then-relay shim with NO
translation logic needed at all (request/response already match on both sides), unlike DeepSeek's proxy which had to do
full Anthropic<->DeepSeek-native protocol translation. Confirm this simpler architecture is actually sufficient before
scoping real implementation work — don't reflexively clone the full DeepSeek proxy's translation-layer complexity where
it isn't needed.

**Alternative worth checking before building (2026-08-13 research)**: the `claude` CLI has built-in,
Anthropic-sanctioned OpenTelemetry export (`CLAUDE_CODE_ENABLE_TELEMETRY=1`) that emits token usage/cost metrics
natively — see public examples `zcquant/claude-code-monitor` and `TechNickAI/claude_telemetry` on GitHub. No network
interception needed at all if this covers what we need. Caveat: it's SDK-level instrumentation inside the CLI's own
process, so it likely shares the same "died before flushing" crash-durability risk our capture-then-relay proxy design
exists to avoid by sitting at the network layer instead — confirm which failure mode OTel spans actually protect against
(do they flush per-turn, or only at session end?) before treating this as a substitute for the simple capture-then-relay
proxy above, rather than a possible source to cross-check it against.

**Also checked (2026-08-13): no public repo, proxy or otherwise, can recover a separate thinking-token count.**
Confirmed directly against a real transcript with extended thinking enabled AND via Anthropic's own docs
(`platform.claude.com/docs/en/build-with-claude/extended-thinking`): thinking tokens count toward `max_tokens` and are
folded into `output_tokens` with no distinct field in the `usage` response object. A proxy only sees what's actually on
the wire — since Anthropic's own API response never carries a separate thinking-token count, nothing external (ours or a
third party's) can produce one. See the "Known gap" section above for the full finding; this rules out "just intercept
it like DeepSeek" as an approach to closing that specific gap.

**Steer clear of `kobie3717/claude-oauth-proxy`-style tools** if this space gets researched further — its own
description advertises an "anti-ban engine" that spoofs headers/tool definitions to evade Anthropic's abuse detection so
a Max/Pro subscription can be used as a raw metered API. That is ToS evasion, not a billing-accuracy tool, and has no
place in this pipeline regardless of how useful its data would be.

## CORRECTION (2026-08-13, same day, after live verification): both capture halves already exist

The section below concluded "no API, must build a tmux `/usage` sampler" — that was WRONG, found by not checking this
repo's own code before researching externally. Verified live on the VM: **`server/usage_poller.py` has been polling
Anthropic's real `anthropic-ratelimit-unified-5h/7d-utilization` response headers since 2026-05-29**, persisting
`weekly_pct`/`five_hour_pct`/`weekly_window_start` per account into `AccountUsageRow` + a full history table
(`AccountUsageHistoryRow`, snapshotted every ~15-30 min). Confirmed 161 real history rows for sub-d/sub-e/sub-f going
back to 2026-08-10. It even already has a TUI-reconcile fallback (`usage_tracker.fetch_usage_via_claude`, a
`claude /usage` pexpect probe) for near-cap accounts where the header read under-reports — i.e. the tmux-driven approach
this doc proposed building was ALSO already built, as a secondary path.

**Token-side pricing already exists too.** `TaskUsageRow` captures every task's real token usage for ANY provider with a
`claude_session_id` (not DeepSeek-only), written durably at `/done`, and — verified live — `spend_usd` is ALREADY
populated for sub-d/sub-e/sub-f using `model_pricing.py`'s existing Anthropic rate cards (`claude-sonnet-5`,
`claude-sonnet-4-6`, etc. all registered). Real numbers pulled live 2026-08-13: sub-d ≈$4.46, sub-e ≈$4.61, sub-f ≈$7.49
in list-rate spend already sitting in `task_usage.spend_usd`.

**Net effect: nothing needs to be CAPTURED. The entire remaining task is a computation joining two tables that already
exist**, plus a dashboard widget — much closer to `deepseek_spend_probe.py` (a read-only reconciliation script) than to
the DeepSeek proxy's capture-infrastructure buildout. Requirement 2 (crash-durability) is effectively MOOT for both
halves: the %-limit poll is independent of any specific task/session (a killed tmux session doesn't affect the next
periodic API poll), and `TaskUsageRow` is already the durable, provider-generic, written-at-`/done` record every other
usage feature relies on — this initiative doesn't need its own new durability guarantee.

**Lesson for next time**: grep the OWN codebase for prior art before researching externally — this was fully built and
running in production for 2.5 months and I nearly proposed rebuilding it.

## Open Question 1 (SUPERSEDED by the correction above, kept for the record) — no API exists — must sample `/usage` from a live session

Researched directly (Anthropic's own docs + two open GitHub feature requests against `anthropics/claude-code`): **there
is no programmatic way to read Max/Pro subscription weekly-limit-% for an account.**
[`Expose Max plan usage limits via Claude Code API/SDK` (issue #32796)](https://github.com/anthropics/claude-code/issues/32796)
and
[`Feature request: claude usage command / API endpoint for Max subscription limits` (issue #44328)](https://github.com/anthropics/claude-code/issues/44328)
are both open, unresolved asks for exactly this — confirming Anthropic has not shipped it. The Rate Limits API
(`/v1/organizations/rate_limits`) and Usage & Cost API are a DIFFERENT product surface (metered API-key/org billing),
not subscription plan limits, and do not return this number. The %-used figure (session bar + weekly bar, both
all-models and Sonnet-only cuts) is **only ever rendered by the `claude` CLI itself**, via the `/usage` slash command
inside an active session, or on claude.ai's Settings → Usage page (UI-only there too).

**Architecture implication — this is not a proxy-shaped problem.** A network proxy captures request/response traffic;
`/usage` is a CLIENT-SIDE UI render with no corresponding API call to intercept. The only way to get this number is to
actively DRIVE a live Claude Code session on the target account: send `/usage` into a running session's pane, capture
the rendered output, and regex-parse the session/weekly percentages out of it — the same tmux `capture-pane` pattern
already used elsewhere in this workspace (see CLAUDE.md's "Pane deep" rule), not a new technique, but a genuinely
different capture mechanism from Requirement 2's token-usage proxy. Two independent, differently-shaped mechanisms are
needed for the two halves of the ratio:

- **Token-side (the $ actually billed at list rates)**: already fully available via the existing generic
  transcript-sweep (`server/deepseek_usage.py`'s `scan_session_usage`, confirmed provider-agnostic 2026-08-13) — no new
  capture needed for this half at all, only new PRICING logic (Anthropic list rates × captured tokens for a Claude
  account, reusing `model_pricing.py` the same way the DeepSeek `spend_usd` fix did).
- **Limit-side (the %-of-weekly-limit signal)**: needs a NEW periodic sampler — a small script/cron-style job that, on a
  cadence (e.g. hourly, mirroring `deepseek_balance_history`'s sampling pattern in
  `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md`), attaches to (or spawns) a live
  Claude Code session on the target account, sends `/usage`, captures the pane text, parses out session-%/weekly-%/
  reset-time, and persists it to a new table (analogous to `deepseek_balance_history`). This sampler is real,
  well-scoped new work — not yet built.

This also reframes Requirement 2's crash-durability ask: the token-usage half needs no new proxy (transcript-sweep
already covers it, provider-agnostic), so the ONLY open crash-durability question is whether transcript-sweep's EXISTING
gap (a session killed before its JSONL write flushes) is a real, measured loss for Claude accounts the way it was
hypothesized to be — not yet measured; see updated Todo list.

## Plan destination ANSWERED (2026-08-13): human-driven, confirmed by operator

Per the ask-before-creating-a-plan hard rule (Open Question 4): operator confirmed **human-driven** (`assigned_vm: NA`),
not AO-dispatched, and asked to "update existing claude billing plans around this and action as human" — i.e. proceed
directly in operator-present sessions like this one, not scope into background-AO-executed work.

## Requirement 3: new "Claude Wallet Reconciliation" dashboard widget

Per-account breakdown, mirroring the existing `DeepSeekWalletPanel.tsx`/`deepseek-wallet-reconciliation` routes in shape
but for Claude accounts:

- % of weekly limit used, converted to an implied $ figure (per the calibration method above)
- actual token usage × Anthropic's published list rates (already computable from existing captured data +
  `model_pricing.py`, no new capture needed for this half)
- the derived ratio/multiplier needed to align the two — "how much boost we're getting" from the flat-rate plan

## Known gap: Claude thinking/reasoning tokens have no source value (confirmed 2026-08-13)

The operator asked whether the fleet/agent-type view's 🧠 reasoning-token badge (built this session for DeepSeek) also
covers native Claude accounts. Investigated and confirmed **it structurally cannot yet**: the badge itself
(`TokenUsageBadge` in `dashboard/src/components.tsx`) and its typing (`dashboard/src/types.ts`) are provider-agnostic —
they render for any non-null `reasoning_tokens`. The gap is upstream: every value feeding it today comes exclusively
from `deepseek_native_usage` via `server/state_store/slots.py`'s `deepseek_native_reasoning_tokens_by_session`/
`_for_session`/`deepseek_native_reasoning_window_totals`, called from `server/routes/agents.py`,
`server/routes/ state.py`, and `server/routes/backlog.py`. Checked a real live transcript with extended thinking enabled
(`thinking` content blocks present): Anthropic's actual `usage` JSON block (`input_tokens`,
`cache_creation_input_tokens`, `cache_read_input_tokens`, `output_tokens`, `server_tool_use`, `service_tier`,
`cache_creation`) carries **no distinct thinking-token field** — unlike DeepSeek's
`completion_tokens_details. reasoning_tokens`, Anthropic folds thinking tokens into `output_tokens` with no separate
breakout in the transcript usage object it writes. `TaskUsageRow`/`record_task_usage` also has no `reasoning_tokens`
column to persist one into even if a source existed. This is not a missed wiring step — there is currently no source
value to wire. Extending the badge to Claude accounts needs either a different Anthropic API surface (unconfirmed to
exist) or accepting this can't be split out from `output_tokens` today; out of scope for this doc's core calibration
work, noted here so it isn't rediscovered.

## Open questions — resolve before this is a real, scoped plan

1. ~~How is "%-of-weekly-limit-used" actually exposed for a given account/window?"~~ **ANSWERED 2026-08-13** — no API,
   see the dedicated section above; needs a tmux `/usage`-driving sampler.
2. **Is the "boost multiplier" actually stable enough to be useful, or does it vary by usage mix the same way the
   DeepSeek cache-hit ratio did?** The DeepSeek investigation this same day found that a workload-dependent ratio
   (cache-hit rate) is NOT safe to extrapolate across different periods/task mixes — worth checking whether Claude's
   %-of-limit consumption per token is similarly workload-sensitive (e.g., does heavy cache-read usage consume the
   weekly limit differently than heavy fresh-input usage?) before treating any single calibration as broadly applicable,
   rather than a periodically-recalibrated, explicitly-dated figure.
3. **Account-identity confirmation** — verify sub-F=`odum2default@gmail.com`=Max (replacing contaminated sub-E) and
   sub-D=`odum1default@gmail.com`=Pro against the actual `accounts.json`/`.claude-accounts/*.env` mapping before using
   either as a calibration sample; this workspace has hit real account-identity mixups before (the DeepSeek
   `CLAUDE_ACCOUNT_LABEL` copy-paste bug found and fixed the same day as this doc, for one recent example).
4. ~~Plan destination~~ **ANSWERED 2026-08-13** — human-driven, see the dedicated section above.

## Requirement 3 SHIPPED (2026-08-13) — real calibration numbers, live in production

`compute_claude_wallet_reconciliation()` (`server/state_store/account_usage.py`), the
`/api/accounts/claude/wallet-reconciliation` route, and `ClaudeWalletPanel.tsx` (wired into all 3 dashboard view sites)
are built, tested (6 backend unit tests, 14 vitest, 3 real Playwright L2 e2e tests, all passing), shipped
(`agent-orchestrator@616450ffac` + a same-day follow-up fix `agent-orchestrator@7a38b4bb06`), deployed to the VM, and
verified against real production data.

**Real bug caught and fixed via live verification, same day**: the first deploy computed
`boost_multiplier = implied/actual`. Every real account read back <1 (0.03x-0.48x), which inverts the intended meaning —
flat-rate subscriptions are cheap relative to metered API pricing BY DESIGN, so `actual_spend_usd` (list-rate-priced
captured tokens) is always the LARGER number, not `implied_spend_usd`. Fixed to `boost_multiplier = actual/implied` (how
many multiples of the prorated subscription "budget" the real token usage would cost at metered rates). This is exactly
the class of bug this session's whole DeepSeek investigation trained for: build against real data, don't trust the first
number that comes back just because the pipeline ran without erroring.

**Real numbers, pulled live 2026-08-13 ~12:49 UTC** (all mid-window, none yet a clean complete week):

| account                             | tier  | weekly % | implied $ | actual $ (list-rate) | boost           |
| ----------------------------------- | ----- | -------- | --------- | -------------------- | --------------- |
| sub-a (ikennaigboaka)               | pro   | 46%      | $2.08     | $29.60               | **14.25x**      |
| sub-b (iggy2london)                 | max20 | 98%      | $44.26    | $730.45              | **16.50x**      |
| sub-c (ikenna-odum)                 | max20 | 100%     | $45.16    | $1455.53             | **32.23x**      |
| sub-d (odum1default, Pro test acct) | pro   | 23%      | $1.04     | $1088.19             | **1047.64x** ⚠️ |
| sub-e (odum3default, contaminated)  | max20 | 11%      | $4.97     | $9.46                | 1.90x           |
| sub-f (odum2default, Max test acct) | max20 | 100%     | $45.16    | $699.73              | **15.49x**      |
| sub-g (alpavoltratrading)           | max20 | 99%      | $44.71    | $105.68              | 2.36x           |

**sub-d's 1047x is a genuine outlier, not a data bug** (unpriced_turns=0, real captured tokens, real weekly_pct read) —
worth flagging to the operator directly, not just filed as a curiosity: either Pro's weekly_pct denominator is measuring
something very different from Max's (e.g. Pro's 5h/weekly cap tracks message COUNT more than token volume, so a
token-heavy workload on Pro barely moves the %, while the SAME workload on Max would move weekly_pct much more), or Pro
accounts are systematically the most "boosted" tier by a wide margin. The 5 max20 accounts cluster in a much narrower
1.9x-32x band. This is direct empirical evidence for Open Question 2 (is the multiplier workload/tier-stable) — it is
NOT tier-stable; Pro and Max20 read on completely different scales and must be calibrated/reported separately, never
averaged together.

## Todo

- [x] [BACKEND] P2. **Confirm sub-F/sub-D account identity mapping** — DONE 2026-08-13, verified against accounts.json's
      `primary_email` field (authoritative; the `id` slug for sub-e is cosmetically stale, already flagged in its own
      label). sub-d-odum1default=odum1default@gmail.com=Pro, sub-e-odum2default=odum3default@gmail.com=Max20 (currently
      contaminated), sub-f-odum2default=odum2default@gmail.com=Max20 — all match the operator's mapping.
- [x] [BACKEND] P1. **Build `compute_claude_wallet_reconciliation()`** — DONE 2026-08-13,
      `server/state_store/account_usage.py`, `agent-orchestrator@616450ffac` + fix `@7a38b4bb06`.
- [x] [BACKEND] P1. **Route** `/api/accounts/claude/wallet-reconciliation` — DONE 2026-08-13,
      `server/routes/accounts.py`.
- [x] [FRONTEND] P1. **Build `ClaudeWalletPanel.tsx`** — DONE 2026-08-13, wired into `App.tsx` at all 3 sites, real
      Playwright L2 coverage (`dashboard/tests/e2e/claude-wallet-reconciliation.spec.ts`, 3 tests).
- [x] [INVESTIGATE] P2. **Run the reconciliation against real data** — DONE 2026-08-13, see table above. Answers Open
      Question 2: the multiplier is NOT tier-stable (Pro reads ~1000x, Max20 reads ~2-32x) — never average across tiers.
- [ ] [OPERATOR] P1. **Investigate the sub-d 1047x outlier** — is Pro's weekly_pct denominator measuring something
      fundamentally different from Max20's (message-count-weighted vs token-volume-weighted), or is Pro genuinely this
      much more "boosted"? Needs either an Anthropic-side answer or more Pro-tier samples to know if 1047x is typical or
      a fluke of this specific window's workload mix.
- [ ] [INVESTIGATE] P3. **Re-run once sub-f's window resets** (~2026-08-13 22:00 UTC, confirmed live via
      `weekly_window_start=2026-08-06 22:00`) for a genuinely clean full-week Max sample — the pre-reset window is real
      but partial (sub-f was already at weekly_pct=100% mid-window as of this check).
- [ ] [OPERATOR] P3. **sub-e stays excluded** from calibration until it goes untouched interactively through a full
      weekly reset (contamination noted above still stands).

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
