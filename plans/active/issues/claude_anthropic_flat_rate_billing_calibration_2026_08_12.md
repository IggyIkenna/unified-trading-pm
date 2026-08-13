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
  workspace's session-checkpoint discipline — NOT YET SCOPED INTO A REAL PLAN, see open questions below.
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
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
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
3. Read Anthropic's own **%-of-weekly-limit-used** signal for that account/window (however it's actually exposed — see
   Open Question 1 below, this is not yet confirmed to have a clean API).
4. Multiply: `% used × prorated budget = implied $ spent` — e.g., operator's own example, "if we use 1% on a task that's
   $0.45 roughly spent" (1% × $45.16 ≈ $0.45).
5. Separately, compute what that SAME window's actual captured token usage would cost at **Anthropic's published
   per-token list rates** (already in this repo: `agent-orchestrator/server/model_pricing.py`'s Anthropic rate cards —
   input/output/cache-read/cache-write, per model, date-effective).
6. The ratio between (4) and (5) is the **"boost multiplier"** for that plan tier — expected to differ between Max and
   Pro since they're different plans with (presumably) different usage-to-limit ratios.
7. Once calibrated, apply the multiplier to **backfill more accurate effective-cost numbers** for Claude usage generally
   — i.e., convert list-price-equivalent token costs into "real value extracted from the subscription."

## Named test accounts (operator-specified, 2026-08-12)

The operator has committed to NOT using these two accounts for interactive/laptop sessions, specifically so they stay
"clean" AO-only samples for this calibration — **since their most recent weekly reset**, both accounts have been
AO-only:

- **sub-E, `odum3default@gmail.com`** — **Max** plan ($200/mo).
- **sub-D, `odum1default@gmail.com`** — **Pro** plan ($20/mo). (Operator's message names "Ikenna — sub D" for this one;
  the exact account-label mapping should be double-checked against `accounts.json`/the `.claude-accounts/*.env` files
  before use, same as every DeepSeek account-identity check this workspace has needed all session.)

**Caveat directly from the operator, stated as a known risk, not an aside**: "the issue is when we use those accounts
locally on my laptop skews the results" — i.e., the calibration is only valid for a window where the account was
GENUINELY AO-only. Any future accidental laptop use of sub-E/sub-D would contaminate that account as a calibration
sample going forward until its next weekly reset.

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

## Requirement 3: new "Claude Wallet Reconciliation" dashboard widget

Per-account breakdown, mirroring the existing `DeepSeekWalletPanel.tsx`/`deepseek-wallet-reconciliation` routes in shape
but for Claude accounts:

- % of weekly limit used, converted to an implied $ figure (per the calibration method above)
- actual token usage × Anthropic's published list rates (already computable from existing captured data +
  `model_pricing.py`, no new capture needed for this half)
- the derived ratio/multiplier needed to align the two — "how much boost we're getting" from the flat-rate plan

## Open questions — resolve before this is a real, scoped plan

1. **How is "%-of-weekly-limit-used" actually exposed for a given account/window?** Is there an Anthropic Console API
   that returns this programmatically, or does it require a manual check in Anthropic's own UI per account per window?
   This determines whether the whole pipeline can be automated or needs a recurring manual data-entry step. Not yet
   investigated as of this doc's creation.
2. **Is the "boost multiplier" actually stable enough to be useful, or does it vary by usage mix the same way the
   DeepSeek cache-hit ratio did?** The DeepSeek investigation this same day found that a workload-dependent ratio
   (cache-hit rate) is NOT safe to extrapolate across different periods/task mixes — worth checking whether Claude's
   %-of-limit consumption per token is similarly workload-sensitive (e.g., does heavy cache-read usage consume the
   weekly limit differently than heavy fresh-input usage?) before treating any single calibration as broadly applicable,
   rather than a periodically-recalibrated, explicitly-dated figure.
3. **Account-identity confirmation** — verify sub-E=`odum3default@gmail.com`=Max and sub-D=`odum1default@gmail.com`=Pro
   against the actual `accounts.json`/`.claude-accounts/*.env` mapping before using either as a calibration sample; this
   workspace has hit real account-identity mixups before (the DeepSeek `CLAUDE_ACCOUNT_LABEL` copy-paste bug found and
   fixed the same day as this doc, for one recent example).
4. **Plan destination** — per this workspace's HARD RULE, ask the operator explicitly whether this becomes an
   AO-dispatched plan or a human-driven one before authoring the real plan doc; do not default silently.

## Todo

- [ ] [OPERATOR] P2. **Answer Open Question 1** — confirm whether Anthropic exposes %-of-weekly-limit-used
      programmatically (Console API) or only via manual UI check, before any automation gets scoped.
- [ ] [INVESTIGATE] P2. **Answer Open Question 2** — check whether the DeepSeek-style workload-sensitivity problem (a
      ratio that looks stable over one window but isn't a true constant) applies to Claude's weekly-limit consumption
      too, before treating any single calibration run as broadly reusable.
- [ ] [BACKEND] P2. **Confirm sub-E/sub-D account identity mapping** against `accounts.json`/`.claude-accounts/*.env`
      before using either as a calibration sample (Open Question 3).
- [ ] [OPERATOR] P2. **Decide plan destination** (AO-dispatched vs human) before authoring the real implementation plan
      (Open Question 4) — per this workspace's ask-before-creating-a-plan hard rule.
- [ ] [BACKEND] P3. **Scope the Claude crash-durability capture mechanism** — confirm the simpler
      transparent-capture-then-relay design (no translation layer needed, unlike DeepSeek's proxy) is sufficient before
      implementation.
- [ ] [BACKEND] P3. **Build the "Claude Wallet Reconciliation" dashboard widget** (Requirement 3) — blocked on the
      calibration method (Open Questions 1-2) being confirmed workable first.
