---
doc_type: plan
title: OmniRoute multi-provider LLM-gateway — pilot design proposal (not yet executed)
summary:
  Operator flagged omniroute.online (a self-hosted, OpenAI/Anthropic-compatible local gateway that auto-routes across
  268 providers' free/cheap tiers) and asked whether it could cut cost on our worker fleet, given we've already tried
  swapping Claude for DeepSeek. Found the exact seam this would plug into (`agent-orchestrator/server/accounts.py`'s
  existing `AccountProvider = Literal["anthropic", "deepseek"]`, which already sources `ANTHROPIC_BASE_URL` for a
  non-Anthropic account) and a much lower-stakes pilot surface (`deployment-api`'s pipeline-UAT commentary caller, a
  direct non-worker Anthropic SDK call). This is a genuine judgment/security call, not bounded execution work — this doc
  is a design proposal only; no infra changes have been made.
status: active
nature: design
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-api]
scope: [engineer, admin]
tags: [omniroute, llm-gateway, cost, multi-provider, model-tier, security]
related:
  [
    /codex/06-coding-standards/model-tier-selection.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: infra
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
source:
  "operator ask 2026-07-30, interactive session slot 1 — https://omniroute.online/ as a possible cost-routing layer for
  the worker fleet"
locked_by:
locked_since:
context_scope:
  [
    /codex/06-coding-standards/model-tier-selection.md,
    agent-orchestrator/server/accounts.py,
    deployment-api/deployment_api/commentary/pipeline_uat.py,
  ]
---

# OmniRoute multi-provider LLM-gateway — pilot design proposal

## Why this doc exists, and why it's a design doc, not a build todo list

Operator asked whether omniroute.online — a free, self-hosted AI gateway (Node.js server, OpenAI- compatible
`localhost:20128/v1` endpoint, 268 providers, automatic free-tier draining + cheapest- per-token routing + rate-limit
fallback) — could help route our worker fleet to cheaper/free models, noting we'd already experimented with swapping
DeepSeek in for Claude. This is a genuine judgment call with a real security/correctness dimension (routing model
traffic through a third-party local process, and interacting with this workspace's Claude-specific model-tier rules) —
per `task_template.md`'s dispatch-scope-eligibility bar, that makes it a LOCAL design doc, not an AO-eligible todo. **No
infra has been touched. Nothing here is executed.** It exists so the decision is captured with the actual code seams
identified, ready for an explicit go/no-go.

## What already exists that this would plug into

`agent-orchestrator/server/accounts.py` already has exactly the mechanism this idea needs:

```python
AccountProvider = Literal["anthropic", "deepseek"]
```

Per its own comment: `"anthropic"` (default, every account today) authenticates via `CLAUDE_CODE_OAUTH_TOKEN` against
Anthropic's own API; a non-anthropic account instead sources `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` pointed at "a
third-party Anthropic-compatible endpoint (e.g. DeepSeek)" — this is the DeepSeek experiment the operator referenced.
OmniRoute's own pitch is "drop-in compatible... without code changes... translates between OpenAI, Claude, Gemini...
formats transparently" — so in principle a NEW `AccountDef` could point `ANTHROPIC_BASE_URL` at `localhost:20128/v1`
(OmniRoute) instead of directly at one third-party vendor, and OmniRoute would fan out from there across its 268
providers. **No new mechanism would be needed** — this is a config-only change to an existing, already-used seam, which
is exactly why it deserves a careful look rather than a reflexive "sounds useful, wire it in."

## The two real problems with pointing the ACTUAL worker fleet at it

1. **Model-tier SSOT conflict.** `/codex/06-coding-standards/model-tier-selection.md` and this workspace's CLAUDE.md
   make `opus-required`/`fable-required` a QUALITATIVE judgment about Claude's own reasoning capability for a specific
   task class (main orchestrator role, cross-repo architecture judgment, trading judgment). An opaque router that
   silently swaps in a cheaper/free model when Anthropic's own endpoint is rate-limited or costlier would violate that
   contract invisibly — a task correctly tiered "sonnet is enough" landing on some unrelated free-tier model is not the
   same risk profile as it actually landing on sonnet, and nothing in the current dispatch path would know the
   difference.
2. **Trust boundary.** OmniRoute is a third-party open-source local process that would sit between every worker and its
   model provider, proxying `ANTHROPIC_AUTH_TOKEN`/API keys. Routing a trading system's agent-fleet traffic through it
   is a deliberate security decision, not something to back into via a quick account-config edit.

Neither of these is a reason to reject the idea outright — they're reasons this needs an explicit operator decision
before any `AccountDef` gets a `provider` pointed at it, not reasons the code mechanism doesn't already exist.

## A much lower-stakes pilot surface exists, and it isn't the worker fleet at all

`deployment-api/deployment_api/commentary/pipeline_uat.py` calls the Anthropic SDK directly (not via a Claude Code CLI
worker) to generate a natural-language batch-pipeline QA summary:

```python
client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
```

This is:

- **Read-only and advisory by construction** — the module's own docstring: "This module is READ-ONLY — it never modifies
  pipeline state or triggers redeployments. All decisions remain with humans," and its system prompt explicitly bans
  recommending trades or infra changes autonomously. Model-tier judgment risk is near-zero — a worse commentary summary
  is a UX annoyance, not a trading or infra-correctness risk.
- **Already fail-soft** — a call failure already degrades to `"[Commentary unavailable: ...]"` rather than blocking the
  pipeline.
- **A trivial, additive, reversible code change** — `anthropic.AsyncAnthropic(api_key=..., base_url=...)` accepts an
  optional `base_url` exactly like `ANTHROPIC_BASE_URL` does for the account mechanism above; a config-gated override
  defaulting to unset (current behavior unchanged) costs nothing to add and nothing to roll back.

This is the natural place to actually test OmniRoute's real cost/reliability claims — cheaper-per- token routing on
genuinely low-stakes text generation — without touching the fleet's own worker sessions or their model-tier guarantees
at all.

## Proposed pilot (pending operator go-ahead — NOT started)

1. Stand up OmniRoute locally (self-hosted, no account needed) and point ONLY `pipeline_uat.py`'s `_call_anthropic` at
   it via a config-gated `base_url` override (`config.pipeline_uat_llm_base_url` or similar, default unset = current
   direct-Anthropic behavior).
2. Run it for a real window (e.g. 2 weeks of pipeline UAT runs) and compare: cost per commentary call, latency, and —
   since this is human-read text — a spot-check that commentary quality didn't regress (the system prompt's bar is
   "concise, plain-language, under 6 sentences unless critical" — easy to eyeball).
3. Report the real numbers before considering ANY extension toward the actual worker fleet (`accounts.py`'s
   `AccountProvider`) — that extension, if ever proposed, needs its own separate operator decision given the
   model-tier/trust-boundary concerns above; this pilot's results don't pre-approve it.

## Open questions for the operator (none of these are assumed — this is why the doc stays a design doc)

- Is a third-party local process proxying API traffic acceptable for `deployment-api` (non-trading, advisory-only) even
  if it wouldn't be for the worker fleet?
- Is the pipeline-UAT commentary pilot worth the (small) engineering cost given it's explicitly advisory/non-critical,
  or is the cost savings here too marginal to bother with (this is a single low-volume commentary call per batch run,
  not a high-throughput surface)?
- If the pilot goes well, is extending toward the worker fleet (`accounts.py`) ever in scope, or is that boundary
  intentional and permanent?

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — the qualitative `opus-required`/ `fable-required` contract this
  doc's risk section is about
- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the existing multi-account /
  `ANTHROPIC_BASE_URL` mechanism this proposal would reuse, not replace
