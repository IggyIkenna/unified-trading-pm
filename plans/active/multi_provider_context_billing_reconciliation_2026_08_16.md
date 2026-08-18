---
doc_type: plan
title: Multi-provider context accuracy + unified billing reconciliation
summary:
  Two linked problems surfaced testing the 4 new providers (Grok/Gemini/GLM/Codex) live — (1) context_used_pct, the
  number driving AO's 60% pre-compact trigger — is fed by per-turn token counts that are REAL for some providers and a
  known-fake char/4 estimate for Codex specifically, so the same uniform compact mechanism behaves accurately for some
  backends and not others; (2) there is no unified way to reconcile per-task billing to a fleet total, or to compare
  "what we spend / what we get" across metered-$, first-party-token, subscription-flat-rate, and rate-limited-free-tier
  providers on one normalized (input/output/cache-read/cache-write) basis. Human-driven — investigation, live testing,
  and design calls throughout, not bounded background-worker todos.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    context-window,
    tokenizer,
    pre-compact,
    billing,
    reconciliation,
    multi-provider,
    gemini,
    glm,
    codex,
  ]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/active/grok_gemini_translation_proxy_2026_08_14.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-16
last_updated: 2026-08-18
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 6
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: [deepseek_claude_blended_provider_routing, grok_gemini_translation_proxy, codex_luna_flex_bridge]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/scripts/orchestrator/calibrate_account_value.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/orm.py,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
---

# Multi-provider context accuracy + unified billing reconciliation

## Why

Testing the 4 new providers live (2026-08-16) surfaced two related gaps that predate this session but only became
visible once real traffic flowed through real proxies:

**1. Context-window/tokenizer accuracy is NOT uniform across providers, but the mechanism that depends on it IS.**
`context_lifecycle.py`'s 60% pre-compact trigger reads `context_used_pct` by scraping Claude Code's own self-reported
"N% context used" pane text — a number Claude Code computes from the `usage.input_tokens`/`output_tokens` fields in
each turn's response. For Gemini/GLM those fields are REAL (LiteLLM/GLM's native endpoint pass through the
vendor's own usage accounting — Grok was identical before its 2026-08-18 decommission). For **Codex/Luna they are a
placeholder**:
`server/codex_bridge_server.py::_estimate_tokens` is `len(text) // 4` — a crude heuristic, explicitly marked
"never to be trusted for billing" in its own docstring. This session independently demonstrated exactly how
unreliable a naive text-length-based token estimate can be: a word-count heuristic on a real Grok 4.6 context-limit
test undercounted the real (xAI-tokenizer-measured) count by 1.6x. If Codex's fake estimate has a similar or worse
skew, `context_used_pct` for a Codex-backed session is silently wrong, and the SAME 60%-trigger mechanics that work
correctly for Gemini/GLM will misfire for Codex specifically — either compacting too early (wasted turns) or,
worse, letting a session run past its real context ceiling undetected (an uncontrolled 400 mid-session, a materially
worse failure than the "recover with a fresh session" path this codebase already has for a *known*-saturated session).

The context-window claims themselves (from vendor docs/research, not yet all live-verified) also need direct testing
rather than trusted at face value — this session tested exactly one (Grok 4.6's 500K ceiling, confirmed real and
hard-enforced, no silent server-side truncation) and found nothing wrong, but that's 1 of 9 registered models. The
same test also settled a separate, real question: **none of the raw provider APIs self-compact** — Grok 4.6 rejected
an over-limit request with a clean `400`, not a truncated/summarized response. Context self-compaction only exists as
a **Claude Code harness feature** (`/compact`), never as vendor-API server-side behavior — worth stating plainly since
it was live-tested, not assumed.

**Separately (operator correction, 2026-08-16): the self-compaction question needs re-testing through the REAL path.**
The 500K-limit test above was a raw HTTP probe directly against the proxy, bypassing Claude Code entirely — it proves
the *backend* doesn't self-compact, but says nothing about whether Claude Code's own `/pre-compact` → `/compact`
mechanism, and the skills/hooks wrapped around it, actually work correctly when the backend is Gemini/GLM/Codex
specifically (Grok was decommissioned 2026-08-18, before this verification ran for it). DeepSeek already proved this end-to-end (`deepseek_claude_blended_provider_routing_2026_07_28` Progress
Log, 2026-07-29: "CLAUDE.md/agents/\*.md need no DeepSeek special-casing — both load identically regardless of which
backend ANTHROPIC_BASE_URL points at"), but that result does not automatically transfer to the 4 new providers and
needs its own live verification, the same way DeepSeek's was actually proven rather than assumed.

**Historical incident check**: one real, already-fixed compact-related bug was located
(`agent-orchestrator@c00dc13f9d`, 2026-08-04 — a pre-Skills CLI binary silently swallowed `/pre-compact` with no
error signal). That fix is generic (pane-text detection of "Unknown command"), not provider-specific, and does not
need re-verification per new provider. **A second, different incident the operator specifically recalled — "compact
runs, but the next turn still resends the full pre-compact history as if it hadn't shrunk" — was NOT located** in
this session's search. Either it exists in a doc/conversation not yet surfaced by grep, or it's being conflated with
something else. Flagged as an open question rather than guessed at (see todo below).

**2. There is no unified, model-agnostic per-task billing reconciliation.** Two distinct goals, stated by the
operator 2026-08-16, not yet designed:

- **Reconciliation**: the sum of every task's attributed billing should equal the fleet's real total spend. Today
  this exists cleanly for DeepSeek (`task_usage` table, real per-token cost) **and, corrected 2026-08-16, for
  Anthropic too** — `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` shipped a real, live
  `boost_multiplier` system (`compute_claude_wallet_reconciliation()`, `ClaudeWalletPanel.tsx`,
  `agent-orchestrator@616450ffac`) with real per-account numbers already pulled (Max20 accounts cluster 14x-32x; a
  genuine Pro-tier ~1047x outlier is still under investigation there, not a data bug — see that doc's own open
  todos). This plan's original framing wrongly described the Claude subscription-value question as unsolved; it
  isn't — it's the reusable PRECEDENT this plan should generalize, not a gap to fill from scratch. The 3 newer
  providers (Gemini/GLM/Codex) still have no per-task cost attribution built at all (Grok would have been a 4th,
  decommissioned 2026-08-18 before this work started — no subscription/free tier, judged not worth running).
- **Normalized bang-for-buck**: everything should reduce to input/output/cache-read/cache-write token counts so
  providers are comparable regardless of billing shape — metered-$ (DeepSeek), first-party token counts we trust
  (Anthropic, Gemini), subscription-flat-rate where the real value per dollar is now KNOWN for Claude (see above) but
  still genuinely UNKNOWN for GLM's Coding Plan (the one remaining real "Sonnet multiplier"-shaped gap — no
  equivalent calibration has been built for GLM's flat-rate subscription), and rate-limited-free-tier where "spend"
  doesn't exist but capacity does (Gemini's free tier — remaining-RPD-as-a-proxy needs a tested methodology, not an
  assumption). **Every number that lands in this system should be the provider's PUBLISHED rate** (not a computed
  effective rate) — that published number times real token counts is what answers "how much bang for the buck are we
  actually getting" against what we pay.

Real turn-shaped variance matters here too, not just $/token: "some models are cheap per turn but need many turns;
some are cheap per token but burn a lot of them" (operator, 2026-08-16) — a single-prompt test (what this session ran)
is a proxy, not a real workflow, and the eventual dashboard needs to show real per-task turn counts alongside token
counts once this reconciliation layer exists, so that distinction is visible on real work, not just a synthetic probe.

**Backfill is explicitly required, not optional** (operator ruling, 2026-08-16): whatever reset-aware reconciliation
mechanism gets built must be run back across ALL existing `account_usage_history`, not just applied going forward —
the existing ledger's reset-crossing windows should be reconciled, not left as dropped/unknown data.

## Non-goals

- Not rebuilding `calibrate_account_value.py`'s conservative single-clean-window design — that script answers a
  narrower, different question ($-per-percent-multiplier for ONE quota window) and merging across a reset there would
  genuinely corrupt that specific calculation (two different weekly-budget dollar values, ambiguous transcript
  attribution). The new reset-aware primitive is additive, not a replacement for that script.
- Not attempting to make Gemini's free tier report a dollar cost — it's genuinely $0. The goal there is a tested
  capacity-consumption proxy, not inventing a price that doesn't exist.
- Not building this as an AO-dispatched background-worker plan — see the operator's explicit "human plan" instruction,
  2026-08-16. The design calls and live-testing judgment here don't fit the AO-eligible bar (deterministic,
  worker-executable outcome).

## Todos

- **[OPERATOR] P2. CANCELLED — SUPERSEDED 2026-08-16 (operator confirmed this no longer occurs).** Was: Point at the actual incident doc/conversation for "compact runs but the next turn resends the
      full pre-compact history as if it hadn't shrunk" — this session's grep found the 2026-08-04 unsupported-binary
      incident (a different failure mode, already fixed, generic) but not this one. Done when: either the real
      incident is located and its fix's generality (provider-specific vs. generic) is confirmed, or the operator
      confirms it should be independently re-tested rather than assumed to be the same class of bug.
- [ ] [INFRA] P0. Fix Codex/Luna's fake token-count estimate (`_estimate_tokens = len(text)//4`,
      `codex_bridge_server.py`) — confirmed unreliable via this session's own 1.6x-off word-count test on a real
      tokenizer comparison. Investigate first whether the `openai-codex` SDK's own thread/turn result carries real
      usage data not currently being read (an easy fix if so); if genuinely unavailable, a real tokenizer
      (tiktoken-compatible for the GPT-5.6 family) is the fallback, not a better heuristic guess. Done when: a real
      sample of Codex-backed turns' captured token counts are cross-checked against the actual ChatGPT/Codex usage
      dashboard and found to agree within a stated tolerance — same standard already required by
      `codex_luna_flex_bridge_2026_08_14.md`'s existing accurate-usage-capture todo, which this directly unblocks.
- [ ] [REVIEW] P1. **Narrowed 2026-08-18 (Grok decommissioned)** — verify Claude Code's own end-to-end
      `context_used_pct` display is accurate for Gemini/GLM — the individual API responses carry real vendor-reported
      usage (confirmed this session), but the CUMULATIVE session-level percentage Claude Code itself computes and
      displays has not been independently checked end-to-end. Done when: a real multi-turn session against each of
      the 2 providers shows a `context_used_pct` reading that tracks real cumulative token consumption within a
      stated tolerance.
- [ ] [REVIEW] P0. **Narrowed 2026-08-18 (Grok decommissioned)** — live-test `/pre-compact` and `/compact` through
      the REAL harness (not a raw HTTP probe) for each of Gemini, GLM, and Codex — spawn real `claude` CLI sessions
      against each new account, run long enough to approach or force the 60% threshold, and confirm: (a) the
      skill/command actually executes (not silently swallowed), (b) `context_used_pct` genuinely drops afterward —
      proving compaction reduces what gets resent, not just that the command ran, (c) CLAUDE.md/skills/hooks behave
      identically to the already-proven DeepSeek case. Done when: a dated Progress Log entry records this for all 3
      remaining providers, each independently verified, not assumed to transfer from DeepSeek's or each other's
      result.
- [ ] [REVIEW] P2. **Narrowed 2026-08-18 (Grok decommissioned, its 4.3's 1M claim dropped — untested and now moot)**
      — live-test the remaining context-window claims from this session's research table (GLM's 1M/131K, Gemini's
      1,048,576/65,536 — already confirmed live for Gemini, DeepSeek's 1,048,576/384,000,
      GPT-5.6's 1.05M/128K) the same way Grok 4.6's 500K was — a real oversized request, built on-host to avoid
      transport payload limits, confirming the vendor enforces its documented ceiling and does not silently truncate.
      Done when: each is either confirmed live or explicitly flagged as still resting on published docs only.
- [ ] [INFRA] P1. Design + build the reset-aware rolling-window cumulative-consumption primitive: given a wall-clock
      period that may cross one or more quota resets, compute TRUE total consumption as
      `(100 - pct_at_period_start) + pct_at_first_reset_boundary + ... + pct_at_period_end`, chained across every
      reset the period spans, using the existing `*_window_start`/`*_resets_at` fields `account_usage_history`
      already carries. Additive to, not a replacement for, `calibrate_account_value.py`'s existing conservative
      single-window design. **Refinement (operator, 2026-08-16): raw percentages are only addable across a reset if
      the account's TIER stayed constant for the whole period.** A pre-reset 1% (e.g. of a Pro $20/wk budget) and a
      post-reset 25% (e.g. of a Max $200/wk budget, if the account was upgraded — or if it's simply a DIFFERENT
      account/model entirely) are not the same unit and cannot be summed as "26%" — each segment must be converted to
      a common unit (dollars, via the same prorated-budget method `compute_claude_wallet_reconciliation` already
      uses) BEFORE summing, using whichever tier/account was actually active during THAT segment. This requires
      tier/account identity tracked PER SEGMENT, not read once at query time as "whatever the account's current tier
      is now" — check whether `account_usage_history` (or any sampled table) already carries a tier snapshot per row;
      if not, that's a real gap to close as part of this same todo, not a separate one. Done when: a real historical
      window that crosses at least one confirmed reset produces a correct, testable total (verified against real
      5h/weekly reset timestamps in the live data, not synthetic), AND a synthetic/real case where the tier changed
      mid-window is handled correctly (dollar-normalized, not raw-percentage-summed).
- [ ] [INFRA] P1. Backfill the reset-aware primitive across the FULL existing `account_usage_history` table —
      explicit operator requirement (2026-08-16): this is not going-forward-only. Must use the tier-per-segment logic
      above, not a naive percentage sum, for any historical window where the account's tier changed. Done when: every
      historical reset-crossing window in the live table has a computed, correct cumulative-consumption value, not
      left as dropped/unknown.
- [ ] [UI] P2. **New, operator 2026-08-16**: once a window's tier/account changed mid-window, its `boost_multiplier`
      (both the existing `ClaudeWalletPanel.tsx` and any new per-provider equivalent this plan builds) must be
      VISIBLY marked unreliable, not silently shown as a normal number — a dashed/red indicator with a hover reason
      ("account switched mid-window: sub-X → sub-Y" or "tier changed: pro → max20"). This is per-window, not
      per-account: a 1h window fully inside one tier is still a valid, normal-styled multiplier; the SAME account's
      lifetime view spanning a tier change is not. Depends on the tier-per-segment tracking in the todo above (the
      flag can't be computed until segment tier identity is actually tracked). Done when: a real window with a tier
      change renders visibly flagged, and a real window without one renders normally, side by side.
- [ ] [DATA] P1. Design the unified per-task billing schema — normalized input/output/cache-read/cache-write token
      counts as the common denominator across every provider's billing shape (metered-$, first-party-token,
      subscription-flat-rate, rate-limited-free-tier), each priced at the provider's PUBLISHED rate (not a computed
      effective rate) for the "bang for the buck" comparison. Must generalize DeepSeek's existing `task_usage` table
      rather than create a second, parallel per-task ledger. Done when: a design doc or schema proposal covers all 6
      currently-registered providers (Anthropic, DeepSeek, Gemini, GLM, Codex, Kimi) with a concrete field mapping
      for each (Grok decommissioned 2026-08-18, dropped from scope).
- [ ] [DATA] P1. Reconciliation proof: sum of every task's attributed billing (once the schema above is populated for
      a real window) must equal the fleet's real total spend for that window, per provider. Done when: a dated
      Progress Log entry shows this reconciling within a stated tolerance for at least DeepSeek + one new provider.
- [ ] [REVIEW] P2. Gemini free-tier capacity-as-proxy methodology: design and run a real test that translates
      "remaining RPD/RPM capacity in a given window" into a spend-equivalent comparison figure, the way
      `gemini_headroom.py`'s ceilings are already tracked for dispatch-gating — this is the same underlying data,
      repurposed for the reconciliation/comparison goal rather than just the dispatch gate. Done when: a documented,
      tested methodology exists, not just the raw ceiling numbers already recorded.
- [ ] [REVIEW] P2. Verify the "manual/interactive Claude usage sits on separate accounts from AO dispatch" assumption
      is actually true today, not just believed — this is the stated precondition for treating AO's own usage
      tracking as clean/isolated from personal usage. Done when: the account roster is checked against what AO
      actually dispatches to vs. what's used interactively, and any overlap is flagged.
- [ ] [UI] P3. Once the reconciliation layer exists, surface real per-task turn counts alongside token counts on the
      dashboard — the stated reason for building this at all: "some models are cheap per turn but need many turns;
      some are cheap per token but use lots of tokens" is only visible on real task data, not a synthetic single-prompt
      probe. Done when: a real dispatched task's turn count and token count are both visible in one place.
- [ ] [SCRIPT] P1. New, operator-refined 2026-08-17, step 1 of the Codex/GLM subscription-model workstream below —
      confirm real end-to-end task completion through AO's actual backlog/worker path (not a raw HTTP or direct-CLI
      smoke test) for both GLM and Codex specifically. Check each account's current `account_status` first (may
      already be `disabled`/paused per the same "register paused until routing exists" pattern used for
      Kimi/Gemma, `kimi_gemma_provider_onboarding_2026_08_16.md` — not yet confirmed for GLM/Codex, do not assume
      either way); if paused, that's an explicit operator call before unpausing, not a default action to take
      unilaterally. Done when: at least one real backlog task exists in `task_usage` for a GLM account and one for a
      Codex account, each completed through the normal `/done` gate (not a synthetic/manual row).
- [ ] [REVIEW] P1. New, operator-refined 2026-08-17, step 2 — determine each provider's REAL usage-limit metric before
      building any reconciliation math on top of it. Operator's own framing: "Codex usage limit and GLM's usage
      limit: one's based on messages, I think, and one's based on tokens" — explicitly not yet verified, don't build
      on the assumption. Check each vendor's own docs/account dashboard directly (same live-verification discipline
      the sibling `kimi_gemma_provider_onboarding_2026_08_16.md` plan already used for model names/pricing — trust a
      live source, not vendor marketing copy or memory). Done when: both GLM's and Codex's real usage-limit unit
      (messages vs. tokens) and the real numeric cap are confirmed against a live source, cited by URL/screenshot,
      not guessed.
- [ ] [DATA] P1. New, operator-refined 2026-08-17, step 3 — build the wallet-reconciliation / `boost_multiplier`
      calculation for GLM and Codex, generalizing `compute_claude_wallet_reconciliation()`
      (`claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`, shipped `agent-orchestrator@616450ffac`) —
      read real token usage plus the real usage-limit-percentage-consumed (from the todo above) and convert it into
      an implied/API-equivalent spend, the same "what would this usage have cost as pay-per-token" shape Claude's
      multiplier already computes. Depends on the usage-metric todo directly above — do not build against an assumed
      metric. Also wire the display side: extend `dashboard/src/layout.tsx:4485`'s `isDeepseek`-only branch to a real
      `providerUsageKind(provider)` lookup so Codex/GLM stop inheriting the raw `weekly_msg_limit=240` default
      (`server/accounts.py:142`) with no live signal behind it, and render the same weekly/5-hour + boost-multiplier
      columns Anthropic already has (`ClaudeWalletPanel.tsx`). Done when: a real computed `boost_multiplier` exists
      for at least one GLM and one Codex account, backed by real usage data, and both render in the dashboard using
      the same columns as Anthropic — apples-to-apples once tasks start flowing to all three, per the operator's
      stated reason for doing this at all.
- [ ] [REVIEW] P1. New, operator-refined 2026-08-17, step 4 — three-way reconciliation check for GLM and Codex: does
      (a) AO's own computed implied-spend/usage-pct (from the todo above), (b) what the provider's own site/docs
      state as the plan's limits and real consumption, and (c) the actual dollar amount paid for the subscription,
      all agree? This is the "check that dollars spent are recorded correctly" check the operator asked for
      explicitly, not just a one-sided computation. Done when: a real 3-way comparison table exists in this doc's
      Progress Log for both GLM and Codex, with any mismatch explained (not silently dropped).
- [ ] [UI] P2. New, operator-refined 2026-08-17 — for Gemma (NVIDIA NIM, free tier): explicitly SKIP the $/
      boost-multiplier reconciliation above — operator's own words, "there's nothing to really reconcile with," and
      it's genuinely $0 (see this plan's existing Non-goals section, same principle already applied to Gemini's free
      tier). But still show REAL request/token counts on the dashboard, not a placeholder, an omitted panel, or a
      copy of another provider's shape. Done when: Gemma's account row shows real usage numbers with no
      reconciliation math attached, visibly distinct from the metered/subscription rows (not silently blank or
      mislabeled as reconciled).
- [ ] [UI] P2. New, operator-refined 2026-08-17 — add an operator-facing quick sanity-check surface: show "requests
      tracked by AO" per account (GLM/Codex/Gemma first, but not exclusive to them) so the operator can manually spot
      -check it against the provider's own console/dashboard. Operator's own framing: "It might make sense for an
      operator to quickly check the UI to just see how many requests that shows versus what we're tracking." This is
      deliberately a manual cross-check aid, not a new automated poller — no live "requests remaining" API is assumed
      to exist for every provider (confirmed absent for Codex specifically, `FlatRateBoostPanel.tsx:9-16`). Done
      when: an operator can view AO's tracked request count for a given account, with enough detail (account id,
      window) to manually verify it against the vendor's own console.
- [ ] [DATA] P3. New, operator-refined 2026-08-17 — forward-looking capacity question, explicitly gated on the
      request-tracking sanity-check above being validated first (do not attempt before that todo is done — the
      operator's own sequencing: "once we know we're tracking requests in the right way, what we really care about
      is: is there enough requests to do a task"). Once tracking accuracy is confirmed, measure the real
      requests-per-task consumption rate from actual dispatched tasks (per provider), to answer whether a given
      plan's request/message allowance is sufficient capacity for the number of tasks intended to run through it.
      Done when: a real measured requests-per-task figure exists for at least one subscription-shaped provider,
      derived from real completed tasks, not estimated.
- [x] ✅ [DATA] P1. New (2026-08-17): join per-task compaction occurrence — whether a given `task_id` triggered
      `forced_precompact`/`forced_compact`/`forced_compact_ineffective` during its own run — onto a queryable
      per-task record. `ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md` already logs these
      events with a timestamp + `slot_id` (`server/fleet_kpis.py`/`server/context_lifecycle.py`), and `TaskUsageRow`
      (`server/orm.py:292`) already carries `assigned_at`/`completed_at` per task — the join key (an event's
      timestamp falling inside a task's own `[assigned_at, completed_at]` window for that `slot_id`) exists in
      principle but is never materialized as a field or query today. Precondition for retrospective complexity
      routing — "give me all tasks that required autocompact," so a model with a small context ceiling can be routed
      away from tasks that historically need compaction. Done when: a real query (or a new persisted field, e.g.
      `TaskUsageRow.compact_count`) answers "did task X trigger compaction" for a real historical task without
      hand-correlating timestamps. **Extracted 2026-08-18 (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 1** — conflict-checked clear (outside the doc-level Non-goals ruling's own stated scope). Track dispatch/completion there, not here.
- [x] ✅ [INFRA] P1. New (2026-08-17): capture the PEAK/high-watermark `context_used_pct` reached during a task, not
      just the end-state token sums `TaskUsageRow` already stores. `context_lifecycle.py`'s per-tick reader already
      sees `context_used_pct` live for every active target — nothing records the max value seen during a task's own
      window onto its durable per-task record. Second precondition for complexity routing (route historically
      low-peak-context tasks to a model with a small context ceiling). Done when: a real completed task's record
      shows a real peak-context value, cross-checked against a live session known to have approached a specific pct.
      **Extracted 2026-08-18 (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 2** — conflict-checked clear. Track dispatch/completion there, not here.
- [x] ✅ [DATA] P2. New (2026-08-17): capture which repo(s) a task actually touched (from its real diff/commits, not the
      plan's declared `repos:` frontmatter, which is a stated intent, not a measurement) and persist it per task. No
      such field exists today — confirmed by grep: `repos_touched`/`repo_count` in `server/` only match unrelated
      dirty-worktree-state concepts (`server/routes/git_health.py:277`, `server/worktree_clean_check/_report.py:51`).
      Useful as a difficulty heuristic alongside turns/context. Done when: a real completed task's record shows the
      real repo(s) it committed to, sourced from actual commit/push evidence. **Extracted 2026-08-18
      (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 3** —
      conflict-checked clear. Track dispatch/completion there, not here.
- [x] ✅ [DATA] P2. New (2026-08-17): persist the task's `context_scope` (the reading-list already passed to the worker
      at dispatch, `server/dispatch.py:564`) onto the completed-task record, so it's retrospectively joinable against
      the task's real turn count/token usage/compaction outcome (todo above). Today `context_scope` is
      dispatch-time-only and never carried through to `TaskUsageRow` or any other durable per-task table — this is
      what lets a future analysis ask "does a bigger context_scope reading list predict more turns/context/
      compaction" rather than assuming it. Done when: a real completed task's record shows both its `context_scope`
      size and its real outcome metrics (turns/tokens/compacted) joinable in one query. **Extracted 2026-08-18
      (na-eligibility-audit, ao tranche) → `ao_satellite_ao_dispatch_batch24_2026_08_18.md` item 4** —
      conflict-checked clear. Track dispatch/completion there, not here.
- [x] [BACKEND] P2. **New, operator ask 2026-08-18 — hourly, clock-aligned time-series aggregation per
      (provider, role_group).** Built `fleet_kpis.compute_hourly_provider_role_usage()` (extends
      `compute_dispatch_efficiency_by_day`'s UTC-calendar-day pattern to hourly, per the plan's own instruction — not a
      parallel mechanism), bucketed by FIXED UTC clock-hour boundaries (`_hour_bucket()` truncates to
      minute=second=microsecond=0, never a rolling window). Exposed as `GET /api/backlog/usage/hourly-series` in
      `server/routes/backlog.py` (`provider`/`role_group`/`start`/`end` query params, same AND-composing/laissez-faire
      convention as `/api/backlog/usage/windows`); range defaults to `fleet_kpis.earliest_usage_timestamp()` (MIN across
      `task_usage.completed_at` and `task_dispatched` activity rows) when `start` omitted. Each bucket reports
      published rate(s) actually in use (`model_pricing.rates_for()` per distinct model seen that hour — never an
      averaged blend across models), 4-way token usage, $ spend (poisoned to None by any unpriced row, same rule as
      `window_task_usage_totals`), completed-task count, and dispatch-ATTEMPT count. Dispatch attempts resolve
      provider via `slot_account_attribution.resolve_turn_account()` against `tmux_spawn.session_name(slot_id)` (a
      `task_dispatched` activity event's own `details_json` carries no account_id — confirmed via direct read of
      `routes/slots_worker.py:709-715`); role_group resolves via `state_store.task_role_group()` (same taxonomy
      `/api/backlog/usage/windows` already filters on), not `RoleDispatchEfficiency.role`'s finer raw-role bucketing.
      New Pydantic views: `HourlyUsageBucketView`/`HourlyModelRateView` in `server/models/backlog.py`.
      **Evidence — real query against a real seeded DB** (`dashboard/tests/e2e/fixtures/seed_e2e_state.py`'s own
      fixture, via the real `run-e2e-backend.sh` mock-mode env, not a synthetic script):
      ```
      hour=2026-08-18T05:00:00+00:00 provider=anthropic role_group=planning task_count=2 dispatch_attempts=2
      hour=2026-08-18T06:00:00+00:00 provider=deepseek  role_group=cicd     task_count=1 dispatch_attempts=5
      ```
      The 06:00 bucket is the burst — 5 dispatch attempts landing only 1 completion, visibly identifiable against the
      05:00 bucket's healthy 2-attempts/2-completions neighbor, satisfying the "done when" bar verbatim. Full backend
      quality gate green (`bash scripts/quality-gates.sh --no-fix`: ruff/basedpyright 0 errors, pytest 4022 passed/7
      skipped).
- [x] [UI] P2. **New, operator ask 2026-08-18 — adopt a charting library (operator's explicit choice over a
      hand-rolled SVG alternative, since this dashboard has zero charting precedent today — confirmed via
      `dashboard/package.json`, no recharts/chart.js/d3/victory/visx/nivo anywhere).** Added `recharts@^3.10.1`
      (the actively-maintained major — 2.x is deprecated upstream, confirmed via `npm install`'s own deprecation
      warning before switching; React 16-19 peer range, compatible with this dashboard's React 18.3). Composes cleanly:
      `npm run typecheck`/`test`/`format:check` all green, `npm audit`'s pre-existing 8 vulnerabilities are all
      transitive dev-tooling (vite/vitest/postcss/esbuild/babel/nanoid) unchanged before/after adding recharts —
      confirmed by diffing `npm audit --json` output pre/post. Proof-of-concept chart:
      `dashboard/src/UsageTimeSeriesModal.tsx` (`ComposedChart` — dispatch-attempts/tasks-completed bars +
      spend line, dual y-axis, custom tooltip) renders real data from the new hourly endpoint. `pw:L2 ✓` —
      `dashboard/tests/e2e/usage-time-series.spec.ts`, 3/3 passed against the real e2e stack.
- [x] [UI] P2. **New, operator ask 2026-08-18 — shared popup/modal chart component, launched from MULTIPLE entry
      points, not duplicated per-panel.** One component (`UsageTimeSeriesModal.tsx`) consuming the new hourly endpoint
      (provider/role-group filter toggles reusing `TaskUsageWindows.tsx`'s own `ROLE_GROUP_FILTER_OPTIONS`), opened via
      an "Usage over time" button added to the `Panel`'s `right` slot in ALL FIVE named entry points: `FleetKpis.tsx`,
      `ClaudeWalletPanel.tsx` (pre-scoped `initialProvider="anthropic"`), `DeepSeekWalletPanel.tsx` (pre-scoped
      `"deepseek"`), `KimiWalletPanel.tsx` (pre-scoped `"kimi"`), `TaskUsageWindows.tsx` (pre-scoped to that panel's
      own current filter selection) — one implementation, five launch sites, not five copies.
      **Real bug found + fixed while wiring this** (not pre-existing scope, a genuine regression this feature's FleetKpis
      entry point was the first to expose): `.topbar` sets `backdrop-filter` for its frosted-glass look, which per the
      CSS spec establishes a new containing block for `position: fixed` descendants — the shared `Modal` component
      (`components.tsx`) was never portaled, so a Modal instantiated from inside a TopBar popover (FleetKpisMenu's
      "KPIs" dropdown) rendered fixed-relative-to-the-144px-tall-topbar instead of the viewport, landing its content
      far outside clickable/visible bounds (confirmed via `getBoundingClientRect()`: `.modal-back` measured
      `144px` tall instead of the full `720px` viewport). Fixed by portaling `Modal` to `document.body` via
      `createPortal` — a general fix benefiting every future modal-in-popover case, not a workaround scoped to this
      feature. That portal in turn broke `usePopover`'s outside-click detection (a portaled modal's DOM node is no
      longer a descendant of the popover's own `ref`, so any click inside it read as "click outside the popover" and
      closed it, unmounting the modal); fixed with an explicit `.closest(".modal-back")` carve-out in
      `layout.tsx`'s `usePopover`. Both fixes are small, targeted, and verified via the real Playwright run below —
      not present in any other Modal usage's behavior (confirmed all other Modal call sites render from `App.tsx`'s
      top level, never nested inside a TopBar popover, so this bug never manifested before).
      **Evidence**: `dashboard/tests/e2e/usage-time-series.spec.ts` — 3/3 passed real end-to-end runs: (1) opens from
      FleetKpis's "KPIs" popover, renders a real chart; (2) opens from ClaudeWalletPanel, pre-scoped to anthropic,
      renders the same live data; (3) changing the provider filter from "All providers" to "Anthropic" re-fetches and
      the burst-note banner (only present for deepseek's HOUR_B burst) correctly disappears. New fixture data:
      `dashboard/tests/e2e/fixtures/seed_e2e_state.py`'s `E2E_USAGE_TS_*` constants — two real UTC-hour-anchored
      buckets (anthropic/planning healthy pattern + deepseek/cicd deliberate 5-attempts/1-completion burst), with
      dedicated `AgentRow` rows on slots 2/6 so `slot_account_attribution` has real intervals to resolve against.

- [~] [DATA] P2. New, operator ask 2026-08-18 — capture reasoning/thinking tokens as part of the unified per-task
      billing schema above (that todo scopes cache-read/write; reasoning tokens are the one dimension it doesn't yet
      name). Investigate what's actually capturable per vendor before assuming uniform feasibility.
      **PARTIAL `agent-orchestrator@b6fe23c7c6`** — DeepSeek: **DONE**, `DeepSeekNativeUsageRow.reasoning_tokens` is
      now joined onto `TaskUsageRow.reasoning_tokens` (new nullable column, migrated via
      `_TASK_USAGE_MIGRATION_COLUMNS` per the 2026-08-05 schema-drift-outage lesson) at both `/done` write-path call
      sites (`_record_done_task_usage` in `routes/slots_worker.py`, and the human-usage-push route) — persisted going
      forward, not just computable via the pre-existing live read-time join in `routes/backlog.py`. NULL (never a
      fabricated 0) when no matching `DeepSeekNativeUsageRow` exists for the session. Evidence: 2 new pytest cases in
      `tests/test_record_done_task_usage_isolation.py` (5/5 passing), full backend suite 4047 passed/5 skipped,
      full `quality-gates.sh` green. Claude: confirmed **N/A** (no reasoning-token field in the API's `usage` object
      at all — unchanged from `claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`'s known gap). Codex:
      confirmed still **blocked** on the P0 fake-token-estimate fix above landing real usage data first (unchanged).
      **Still open — Kimi/GLM**: the generic Anthropic-shape proxy parser these route through never reads a
      reasoning-token field, and it's not yet established whether Moonshot/Zhipu's actual API response even carries
      one — that requires either reading vendor API docs or a live probe, and a live probe against Kimi specifically
      is undesirable right now given Kimi's accounts are deliberately paused fleet-wide (see the "Kimi Blocked"
      badge work above; do not spend metered requests probing this before the Moonshot waitlist resolves). If the
      field does exist, capturing it durably would need a DeepSeek-style dedicated native proxy (a real, separate
      build — not a quick parser tweak), since the generic proxy is intentionally shape-agnostic. Done when: Kimi/GLM
      resolved either way (captured + joined, or documented N/A same as Claude) — the other three providers already
      meet the original "capture-or-explicitly-N/A" bar.
- [x] ✅ [DATA] P2. New, operator ask 2026-08-18 — bring Kimi's wallet reconciliation up to the same depth Claude/
      DeepSeek already have. Today `compute_kimi_wallet_window_reconciliation()` (`server/state_store/slots.py:1373`)
      only covers the 1h/24h/7d/Lifetime WINDOWED view — no lifetime LEDGER table (known top-up total / opening
      balance / attributed spend / residual), the shape `compute_claude_wallet_reconciliation()`
      (`account_usage.py:533`) and `compute_deepseek_wallet_reconciliation()` (`slots.py:1468`) both already have.
      `kimi_gemma_provider_onboarding_2026_08_16.md`'s own todo explicitly forward-points here for "full
      billing-schema inclusion" rather than duplicating scope in that doc. No new UI pattern needed — same
      `KimiWalletPanel.tsx` component, same lifetime-table shape already proven twice. Done when: `KimiWalletPanel.tsx`
      shows a lifetime reconciliation table alongside its existing windowed one, backed by a real
      `compute_kimi_wallet_reconciliation()`-equivalent, same as DeepSeek's/Claude's.
      **DONE `agent-orchestrator@39d35ed696`** — new `compute_kimi_wallet_reconciliation()` (mirrors
      `compute_deepseek_wallet_reconciliation()`, simpler: no worker/orchestrator/review split, no opening-balance
      freeze — Kimi's wallet has no pre-observability gap), new `KimiTopupRow`/`GET+POST /api/accounts/kimi/
      wallet-reconciliation`+`topups`, new lifetime table + top-up form in `KimiWalletPanel.tsx` alongside the
      existing windowed one. **Evidence**: 6 new backend pytest cases (`tests/test_kimi_wallet_reconciliation.py`),
      `pw:L2 ✓` — 2 new e2e tests in `kimi-wallet-reconciliation.spec.ts` (real computed numbers:
      $20.0000 topup − $12.5000 balance = $7.5000 real spend, $2.0000 attributed, $5.5000 residual; a second
      recorded top-up updates the table in place), full backend+dashboard quality gate green before shipping.

## Progress Log

- **2026-08-18 (delta investigation, operator ask) — re-investigated existing coverage before adding scope, per
  operator instruction ("investigate the delta ... I'm not sure why there are so many extra to-dos").** Operator's
  original ask ("reconciliation, task usage, batch call usage, terms, reasoning, tokens ... across all providers")
  mapped almost entirely onto this plan's ALREADY-open scope: cache-token schema unification (existing `[DATA] P1`
  unified-schema todo already names all 6 providers), published-rate "terms" (already the Why section's explicit
  requirement), Codex's fake-token bug (already the #1 `[INFRA] P0` todo, re-confirmed today still current via a
  fresh read of `codex_bridge_server.py:237-254` — unchanged). "Batch call usage" was a genuine misread on my part —
  the operator clarified it means TOOL-CALL BATCHING (the hook that nudges chaining Bash/Read/Edit calls, not LLM
  provider batch-billing APIs). Verified real, not a gap: `cursor-configs/hooks/batching-nudge.py` is the actual
  hook; `server/batching_stats.py` + `batching_stats_poller.py` (registered `server.py:329`) do real transcript
  scanning (with a genuine, hard-won multi-line `message.id`-grouping fix documented in its own module docstring);
  `dashboard/src/BatchingEfficiencyPanel.tsx` already surfaces it with the same 1h/5h/24h/7d/Lifetime window shape as
  every other reconciliation panel, filterable by provider/model/role-group/account — nothing to build there. Two
  genuine deltas found and added as todos above: (1) reasoning tokens are not named anywhere in this plan's existing
  unified-schema todo, captured for DeepSeek only, never joined onto `TaskUsageRow`; (2) Kimi's reconciliation depth
  is windowed-only, no lifetime ledger table the way Claude/DeepSeek both have. No new UI pattern for either — same
  existing panel/table shapes, real accuracy work only, per the operator's own framing ("it's just accuracy on all
  the providers, we already have the things we need shown there").
- **2026-08-18 (implementation) — all 3 hourly-usage-chart todos shipped, uncommitted in the working tree.**
  `agent-orchestrator` files touched: `server/fleet_kpis.py` (new `compute_hourly_provider_role_usage`,
  `earliest_usage_timestamp`), `server/models/backlog.py` + `server/models/__init__.py` (new
  `HourlyUsageBucketView`/`HourlyModelRateView`), `server/routes/backlog.py` (new `GET
  /api/backlog/usage/hourly-series`), `dashboard/package.json` (+`recharts@^3.10.1`), new
  `dashboard/src/UsageTimeSeriesModal.tsx` + `.test.ts`, `dashboard/src/{FleetKpis,ClaudeWalletPanel,
  DeepSeekWalletPanel,KimiWalletPanel,TaskUsageWindows}.tsx` (launch button wiring), `dashboard/src/components.tsx`
  (Modal portal fix — see the 3rd todo above for why), `dashboard/src/layout.tsx` (usePopover click-outside carve-out
  — same root cause), `dashboard/src/styles.css` (`.usage-ts-tooltip`), new
  `dashboard/tests/e2e/usage-time-series.spec.ts`, `dashboard/tests/e2e/fixtures/seed_e2e_state.py`
  (`E2E_USAGE_TS_*` fixture block). Backend quality gate green (ruff/basedpyright/4022 pytest); dashboard
  typecheck/408 vitest/format:check green; new Playwright spec 3/3 passed against the real e2e stack. Judgment calls
  made without an operator ruling (flagged, not hidden): exact endpoint path/param names
  (`/api/backlog/usage/hourly-series?provider=&role_group=&start=&end=`, mirroring `/api/backlog/usage/windows`'s
  existing convention); burst-detection threshold (`dispatch_attempts >= 3 AND >= 2x task_count`, chosen so a single
  crash/timeout requeue never false-flags); modal styling (plain `Modal`/`Panel` reuse, `ComposedChart` with dual
  y-axis — bars for attempts/completions, line for spend — token totals surfaced via tooltip/rates-line rather than a
  5th chart series, to avoid a scale mismatch against attempt/completion counts). No todo's "done when" bar was
  infeasible — real historical spread existed (or was fixture-added) for every claim above.
- **2026-08-18 (/plan-brainstorm) — 3 new todos added: hourly per-provider/per-role usage time-series + chart UI.**
  Operator ask: plot usage over time per provider, broken down by role, showing published API rates/usage/real $
  spent/task-completion counts, PLUS dispatch-attempt counts (not just completions — "trying a lot of times" without
  landing the task is its own signal), launched as a popup from the KPI panel and/or each wallet-reconciliation/
  task-usage panel. Operator explicitly ruled: fold into an existing plan, no new plan doc. Researched first (this
  doc's own `context_scope` + `FleetKpis.tsx`/`server/fleet_kpis.py`): `DailyDispatchEfficiency`/
  `RoleDispatchEfficiency`/`DispatchRetryStats` already exist (daily-granularity dispatch/done/retry KPIs) — this is
  NOT greenfield, it's an hourly generalization + a new billing/rate dimension layered on. The plan that originally
  built FleetKpis (`ao_fleet_observability_kpis_2026_07_20`) is archived, and the only other active KPI-adjacent plan
  (`ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md`) is scoped to compaction/death-
  diagnostics specifically — neither is the right home, so this doc (already covering per-task/per-provider billing
  reconciliation) is. Two operator decisions resolved via `/plan-brainstorm` clarifying questions: (1) adopt a real
  charting library (not hand-rolled SVG) despite this being the dashboard's first-ever charting dependency; (2)
  hourly buckets (not daily) to actually surface intraday burst patterns. Operator separately clarified mid-session:
  buckets must be FIXED UTC clock-hour boundaries (00:00, 01:00, ...), never a rolling "last N hours from now"
  window — a different shape from every existing `window_hours` lookback endpoint in this codebase (the wallet
  panels' own 1h/24h/7d/Lifetime toggle shipped earlier today), folded into the new todo's own text so it isn't
  conflated by whoever builds it.

- **2026-08-18 — Grok (xAI) decommissioned, operator decision; every open todo above narrowed to drop it.** Reason
  stated verbatim: no subscription/Max-style tier and no free tier — pure metered pay-per-token — judged pointless
  vs Claude/DeepSeek's subscription economics and Gemini's genuine free tier. Full removal record (code + the
  dedicated onboarding plan) lives in `grok_gemini_translation_proxy_2026_08_14.md` (retitled to drop Grok, its own
  2026-08-18 Progress Log entry has the file-by-file `agent-orchestrator` diff). This doc's provider-count references
  updated (4→3 new providers: Gemini/GLM/Codex; 7→6 total registered providers), and the `[REVIEW]` context-window/
  compaction-verification todos narrowed to the remaining providers. Historical findings (e.g. the real Grok 4.6
  context-ceiling test that grounded this doc's "vendors don't self-compact" finding) left untouched — they're a
  record of what was measured, not live scope.

- **2026-08-16 (created)**: Plan authored from a same-session investigation following the live 9-model billing/context
  test battery (see the sibling provider plans' 2026-08-16 Progress Log entries for that raw data). Real findings this
  session, cited above: Codex's fake `len(text)//4` token estimate (confirmed via direct code read), the
  provider-agnostic-mechanism-vs-provider-specific-data-accuracy gap in `context_lifecycle.py`, Grok 4.6's 500K
  context ceiling confirmed live (hard-enforced, no self-compaction), and `calibrate_account_value.py`'s deliberate
  (not buggy) reset-window-dropping design. No code written yet — investigation + plan authoring only.
- **2026-08-17 — 5 new todos from an interactive UI/telemetry review**: operator reviewed the AO dashboard and asked
  three things. (1) What does "Input per turn" mean — answered inline, not a gap: confirmed real cache-miss input
  tokens/turn, working as intended (`dashboard/src/TaskUsageWindows.tsx:320-323`, `server/routes/backlog.py:928`), not
  a tool-call count. (2) Why every account shows Anthropic-shaped weekly/5-hour limits regardless of provider —
  confirmed a real gap (`server/accounts.py:142`, `dashboard/src/layout.tsx:4485`), narrowed by the operator's own
  follow-up correction: Codex and GLM are subscription-shaped like Anthropic and should get the SAME
  weekly/5-hour+boost treatment, not be excluded from it — new `[UI] P1` todo above. (3) Whether enough per-task
  telemetry exists to retrospectively identify "hard" tasks before more providers go live. Confirmed `TaskUsageRow`
  (`server/orm.py:292`) already durably captures turn_count/4-way token breakdown/spend/duration per task, but four
  things do not exist yet — per-task compaction-occurred flag, peak-context high-watermark, real repos-touched, and
  context_scope size carried through to the completed-task record — added as the 4 new todos above. None of this
  plan's existing todos covered those four; the existing `[DATA] P1` unified-billing-schema todo is billing-shaped
  (token counts × published rate), not difficulty-shaped (turns/compaction/context/repos as future routing signals) —
  kept separate, not merged, since they answer different questions. No code written this session — doc-only.
- **2026-08-17 — Codex/GLM boost-parity todo refined into a 7-step workstream**: operator broke the single
  Codex/GLM-parity todo (added earlier the same day) into an explicit sequence: (1) confirm real end-to-end task
  completion through AO for GLM/Codex specifically (not just a smoke test), (2) determine each provider's real
  usage-limit metric — messages vs. tokens, not yet verified for either, don't assume — before doing any math on it,
  (3) build the `boost_multiplier`/wallet-reconciliation calculation generalizing Claude's
  `compute_claude_wallet_reconciliation()` once the metric is known, and wire the same dashboard columns Anthropic
  already has, (4) a three-way check that AO's computed spend, the vendor's own stated docs/limits, and the actual
  dollars paid all agree. Separately: Gemma should explicitly SKIP $ reconciliation (genuinely free, "nothing to
  reconcile with") but still show real, non-placeholder usage numbers. Two more items added: an operator-facing
  "requests tracked by AO" surface so the operator can manually spot-check AO's count against each vendor's own
  console, and a forward-looking (explicitly gated on that surface being validated first) measurement of real
  requests-per-task, to eventually answer whether a plan's request allowance covers the number of tasks intended to
  run through it. Replaced the single prior todo with these 7, rather than leaving both (no work had landed against
  the original yet). No code written this session — doc-only.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ee26e6744e46c17e]: KEEP-NA, valid — explicit dated operator ruling on record: 'human plan, not AO-dispatched' for the whole doc's live-testing/design-call content (multi-provider billing/context research).
- **na-eligibility-audit 2026-08-18 (ao tranche)**: RECLASSIFY (per-todo split) — re-read end to end. The doc-level 'human plan' ruling correctly covers the bulk of the remaining ~19 open todos (live-testing verification, schema/methodology design work, the GLM/Codex boost-parity workstream), all KEEP-NA on that citation. But 4 telemetry-capture todos added 2026-08-17 (compaction-occurrence join, peak-context watermark, repo-touched capture, context_scope-size capture) are pure bounded backend/DB engineering with zero design or live-testing judgment component — outside the cited ruling's own stated scope. Conflict-checked clear and extracted to `ao_satellite_ao_dispatch_batch24_2026_08_18.md` items 1-4. Doc stays `assigned_vm: NA` for its remaining ~19 items.
