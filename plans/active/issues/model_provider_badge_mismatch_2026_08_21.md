---
doc_type: issue
title: >-
  Model/provider naming mismatch bug class across the AO dashboard and stats surfaces —
  Fleet table and Agent Types tab fixed; DeepSeek-native billing aggregation and
  dispatch-ranking still read the raw, uncorrected model field
summary: >-
  Root cause: several places store or read a task/slot/agent's `model` as a raw,
  self-reported string that is only ever corrected at specific WRITE sites — but the
  account actually serving a task can change out-of-band (watchdog usage-cap resume,
  escalation/cicd one-shot dispatch never calling `/boot`, headroom-based account
  selection landing on any provider) without re-triggering that correction, so the
  displayed/aggregated model goes stale while the provider it's paired with updates
  live. Two instances of this fixed so far, same fix shape each time — resolve the
  model live, at READ time, via `effective_model_for_telemetry(account, self_reported)`
  keyed off the CURRENT account_id, never trust a write-time correction alone:
  (1) Fleet table (`server/routes/state.py::_slot_to_view`, agent-orchestrator@2ccdfe22ae)
  — reported as "claude-sonnet-5 OpenAI (Codex)" / "sonnethigh Google (Gemini)".
  (2) Agent Types tab + HumanFleet.tsx (`server/routes/agents.py::_agent_to_view`,
  agent-orchestrator@bcab4a0210) — reported as "sonnet Gemini" for an escalation
  dispatched with request-time literal `model="sonnet"` (server/ci_reconcile.py:908)
  that landed on a Gemini account. An audit agent (2026-08-21) traced every other
  stats surface for the same class; two real findings remain UNFIXED, deferred below —
  one is aggregate billing/token-usage corruption, not just a display glitch, matching
  the operator's own stated concern ("token usage per account... batching efficiency...
  dying rates... all other stats that we keep track of").
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    model-naming,
    provider-badge,
    effective_model_for_telemetry,
    deepseek,
    billing,
    dispatch,
    task-usage,
  ]
related:
  [
    /plans/archive/2026_08/issues/codex_bridge_tiktoken_missing_leaked_orphan_processes_2026_08_21.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/deepseek_native_proxy_server.py,
    agent-orchestrator/server/deepseek_native_translate.py,
    agent-orchestrator/server/deepseek_usage.py,
    agent-orchestrator/server/batching_stats.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/accounts.py,
  ]
source: >-
  Operator, interactive session, 2026-08-21: reported the Agent Types tab row
  "cicd1-shot / agt-a5d400 / market-tick-data-service / sonnet Gemini↓0 ↑0 $0.0000 /
  gemini-3-7-flash-proj2" and asked to check + fix, PLUS check whether the same class
  taints "token usage per account and token usage per tasks and batching efficiency and
  other tabs that... classify which model is completing how many tasks and their dying
  rates and their token usage and all other stats". Investigated live via slot 15,
  general-purpose sub-agent audit (agentId a51a3f99f0cc24022) traced every surface.
---

## Fixed (shipped, verified)

1. **Fleet table** — `server/routes/state.py::_slot_to_view`. agent-orchestrator@2ccdfe22ae.
   Live-verified: `GET /api/state` now shows `codex-luna` for every Codex slot,
   `gemini-3.5-flash-lite` for the originally-reported slot 11, versioned
   `claude-sonnet-5` for Anthropic slots. Deployed dashboard bundle confirmed
   (grepped the live JS: new `PROVIDER_DISPLAY` labels present, old ones gone).
2. **Agent Types tab + HumanFleet.tsx** — `server/routes/agents.py::_agent_to_view`.
   agent-orchestrator@bcab4a0210. 5 new regression tests
   (`tests/test_agent_view_model_provider_alignment.py`) reproduce the exact reported
   row and pass. Full quality gate green (5269 backend + 468 dashboard tests).

Both fixes follow the identical shape: resolve `accounts_by_id: dict[str, AccountDef]`
once per request (mirrors the existing `providers_by_account` pattern each function
already had for the provider badge), call
`effective_model_for_telemetry(accounts_by_id.get(account_id), self_reported_model)`
for the model field instead of trusting the stored/raw value. `ci_reconcile.py:908`'s
hardcoded `model="sonnet"` dispatch-request literal is NOT itself a bug to fix — it's a
legitimate tier request; the read-time correction above makes whatever's displayed
correct regardless of what tier was requested at dispatch time or which account ends
up serving it.

## Deferred — real, unfixed, NOT display-only

- [ ] [BACKEND] P1. **DeepSeek-native transcript `model` field corrupts aggregate billing
      stats** (TaskUsageWindows, BatchingEfficiencyPanel, UsageTimeSeriesModal — all
      group $/token totals by `TaskUsageRow.model`/`BatchingTurnRow.model`, populated
      from the transcript's own `message.model`, itself written from
      `anthropic_body.get("model", "")` at `server/deepseek_native_proxy_server.py:347`
      — the CLI's self-declared REQUEST model, whose OWN code comment already says
      "already documented fleet-wide as an unreliable self-declared value... never used
      for pricing/routing"). Being used for pricing/aggregation anyway, contradicting
      that comment. A sibling bug in a DIFFERENT table (`DeepSeekNativeUsageRow`,
      `deepseek_native_usage_spend_pricing_model_bug_2026_08_12`) was already fixed the
      same way this needs to be fixed — `pricing_model=account_id`
      (`deepseek_native_proxy_server.py:259-260`) — but that fix never touched what gets
      WRITTEN into the transcript / `TaskUsageRow.model` these three panels read.
      Deferred: billing-critical, touches transcript-writing semantics, needs careful
      verification of whether historical rows also need correcting or only forward
      writes — a decision for whoever picks this up, not something to change
      unilaterally. Gemini/GLM/Codex transcript-writing paths were NOT traced in the
      2026-08-21 audit pass — verify those too before considering this closed.
- [ ] [BACKEND] P2. **`server/dispatch.py:200,564`** (`_blocks_model_tier`,
      `_task_outranks_slot`) reads the raw, uncorrected `SlotRow.model` (`s.model or
      "sonnet"`) to rank task-vs-slot tier eligibility for real dispatch decisions — a
      FUNCTIONAL consumer, not display. A slot whose stored model field is stale could
      get its dispatch priority computed against a misleading tier baseline. Not yet
      verified how much this actually skews real dispatch outcomes, nor whether tier
      comparison is even well-defined across providers (the comparison may implicitly
      assume an Anthropic-only tier hierarchy) — needs investigation before a fix is
      designed, not a mechanical swap-in of `effective_model_for_telemetry`.

## In progress, NOT yet root-caused: Gemini accounts show no weekly usage limit

Separate report, same session (2026-08-21): operator says Gemini accounts show no
weekly limit in some dashboard view, and suspects the panel is using a Claude-shaped
"5-hour + weekly" window that doesn't match how Gemini's real quota is actually
designed.

**Confirmed so far**: `server/gemini_headroom.py` + `dashboard/src/GeminiCapacityPanel.tsx`
already exist and are ALREADY CORRECT — Gemini's real ceiling is RPM (requests/min) +
RPD (requests/day) + TPM (tokens/min, informational-only, no live "used" count exists
pre-dispatch since token counts are only known after a turn completes). The panel
already polls every 30s via `GET /api/accounts/gemini/capacity` →
`compute_gemini_capacity_snapshot`, already shows RPM/RPD/TPM, not a 5hr/weekly shape.

**NOT yet found**: which OTHER component the operator is actually looking at that
renders Gemini accounts through the WRONG (Claude 5-hour/weekly) shape, leaving weekly
blank. Candidates identified via `grep -rl "5.hour\|weekly" dashboard/src/*.tsx` but not
yet individually checked: `ClaudeWalletPanel.tsx`, `FlatRateBoostPanel.tsx`, `App.tsx`,
`layout.tsx`. Hypothesis: the generic "Accounts" panel (or a shared per-account usage
table component) renders EVERY account — including Gemini ones — through a template
built around Claude's real 5-hour-rolling + weekly window shape, alongside (not
instead of) the correct, separate `GeminiCapacityPanel`; the operator may be looking at
that generic row, not the dedicated Gemini panel, and not know the correct one exists,
or the generic one needs to stop attempting to render weekly/5hr fields for a
non-Anthropic provider at all.

- [ ] [UI] P1. **Root-cause and fix the Gemini weekly-limit display gap.** Read
      `ClaudeWalletPanel.tsx`, `App.tsx`, `layout.tsx` for the generic per-account usage
      table/component the operator is actually seeing Gemini rows in. Confirm whether
      it's (a) rendering Gemini accounts through the Claude 5hr/weekly shape at all
      (should skip or route to the RPM/RPD shape instead), or (b) something else
      entirely. Fix so Gemini accounts either don't render through the Claude-shaped
      table, or that table itself detects `provider === "gemini"` and shows the real
      RPM/RPD/TPM figures (already computed by `gemini_headroom.py`, just needs
      wiring into whichever component this turns out to be) instead of blank weekly
      figures. Confirm the fixed numbers update on the same live-refresh cadence as
      every other account (operator's explicit ask: "make sure... they are also
      updated with every other accounts").
