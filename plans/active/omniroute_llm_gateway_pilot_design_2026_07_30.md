---
doc_type: plan
title: OmniRoute multi-provider LLM-gateway pilot — deployment-api pipeline-UAT commentary (human execution)
summary:
  Operator flagged omniroute.online (a self-hosted, OpenAI/Anthropic-compatible local gateway that auto-routes across
  268 providers' free/cheap tiers) as a possible cost-routing layer, given the fleet already has a DeepSeek-swap
  precedent (`agent-orchestrator/server/accounts.py`'s `AccountProvider`). Operator ruling 2026-07-30 waived the
  trust-boundary objection and directed the model-tier-SSOT-conflict objection be resolved by a structural guardrail
  rather than by staying gated — this doc records both rulings and gives the pilot itself full build-grade detail (exact
  files/fields/tests/done-whens), while staying a LOCAL/human-executed plan (not AO-dispatched) per the operator's
  explicit choice.
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
  the worker fleet; rulings on both objections same session"
locked_by:
locked_since:
context_scope:
  [
    /codex/06-coding-standards/model-tier-selection.md,
    agent-orchestrator/server/accounts.py,
    deployment-api/deployment_api/deployment_api_config.py,
    deployment-api/deployment_api/commentary/pipeline_uat.py,
  ]
---

# OmniRoute multi-provider LLM-gateway pilot — deployment-api pipeline-UAT commentary

## Why this doc exists, and why it stays LOCAL despite the build-grade detail below

Operator asked whether omniroute.online — a free, self-hosted AI gateway (Node.js server, OpenAI-compatible
`localhost:20128/v1` endpoint, 268 providers, automatic free-tier draining + cheapest-per-token routing + rate-limit
fallback) — could route the worker fleet to cheaper/free models, noting the fleet already has a DeepSeek-swap precedent.
The original version of this doc flagged two objections and stayed gated on both. Same session, operator ruled on both:

1. **Trust boundary (OmniRoute proxying API keys) — WAIVED.** Operator: don't gate the pilot on this.
2. **Model-tier SSOT conflict — NOT waived, but resolved via a structural guardrail** (§ below), so the objection is
   addressed by construction rather than by a standing gate someone has to remember to check.

Per operator direction, this is written to AO-dispatch-grade detail (every step names its exact file, field, test, and
done-when) — but **stays `assigned_vm: NA` / `execution_scope: local-only` by explicit operator choice**: the operator
wants this executed by a human, not auto-dispatched, while still getting the same precision an AO todo would need.

## What already exists that this plugs into

`agent-orchestrator/server/accounts.py` already has the mechanism the ORIGINAL ask (route the worker fleet) would have
needed:

```python
AccountProvider = Literal["anthropic", "deepseek"]
```

`"anthropic"` (default, every account today) authenticates via `CLAUDE_CODE_OAUTH_TOKEN`; a non-anthropic account
sources `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` pointed at a third-party Anthropic-compatible endpoint (the
DeepSeek precedent). This pilot deliberately does **not** touch this mechanism — see the guardrail below for why.

## The model-tier guardrail (baked in, not just documented)

**The risk, precisely:** `/codex/06-coding-standards/model-tier-selection.md` and CLAUDE.md make
`opus-required`/`fable-required` a qualitative judgment about Claude's own reasoning capability for a specific task
class (main orchestrator role, cross-repo architecture judgment, trading judgment). An opaque router that silently
substitutes a cheaper/free model when Anthropic's endpoint is rate-limited or costlier would violate that contract
invisibly — a task correctly tiered "sonnet is enough" landing on some unrelated free-tier model is not the same risk as
it actually landing on sonnet, and nothing in the dispatch path (`server/plan_health.py`'s `smart_tier` forcing,
`server/model_tier.py`) would know the difference.

**The guardrail (what "baking it in" means concretely):** the pilot is structurally confined to a code path that has
**no model-tier semantics at all** — `deployment-api`'s pipeline-UAT commentary caller is a direct `anthropic` SDK call
from a non-worker service, never a Claude Code CLI session, never touched by `smart_tier`/`model_tier.py`. Two repos, no
service↔service dependency (already true per CLAUDE.md's tier-and-import-architecture rule), so there is no code path
today by which this pilot's config can reach `accounts.py`. The guardrail makes that boundary an **explicit, documented
rule** instead of an implicit accident of current architecture, so a future change can't cross it silently:

- [ ] [INFRA] P2. Add a guard comment directly above `AccountProvider = Literal["anthropic", "deepseek"]` in
      `agent-orchestrator/server/accounts.py` stating: this Literal must never gain a value that routes through a
      shared/opaque multi-provider gateway (OmniRoute or equivalent) without a fresh, explicit model-tier-risk review —
      cite `/codex/06-coding-standards/model-tier-selection.md`. Done-when: comment present, references the exact codex
      path.
- [ ] [INFRA] P2. Add a short note to `/codex/06-coding-standards/model-tier-selection.md` cross-referencing this plan
      and stating the same boundary from the SSOT side (an opaque multi-provider router is out of scope for any
      `AccountProvider`-routed worker traffic; the one sanctioned pilot surface is `deployment-api` pipeline-UAT
      commentary, tracked here). Done-when: the note exists and the plan doc is linked from it (or vice versa via
      `context_scope`).

This makes "don't extend this to the worker fleet" a documented, citable rule at exactly the two places someone would
look (the enum itself, and the model-tier SSOT) — not just a paragraph in a design doc that stops being read once the
pilot ships.

## The pilot surface: deployment-api pipeline-UAT commentary

`deployment-api/deployment_api/commentary/pipeline_uat.py` calls the Anthropic SDK directly to generate a
natural-language batch-pipeline QA summary — read-only, advisory-only by its own docstring ("This module is READ-ONLY —
it never modifies pipeline state or triggers redeployments. All decisions remain with humans"), already fail-soft on API
errors (`"[Commentary unavailable: ...]"`).

```python
# deployment_api/commentary/pipeline_uat.py:237 (current)
client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)
```

### Implementation steps (human-executed; each names its exact file/field/test)

- [ ] [BACKEND] P2. **Add the config field.** In `deployment-api/deployment_api/deployment_api_config.py`, in the
      `# PIPELINE UAT COMMENTARY` section (currently lines 678-704, alongside
      `pipeline_uat_commentary_enabled`/`anthropic_api_key`/`pipeline_uat_model`), add:
      `python     pipeline_uat_llm_base_url: str | None = Field(         default=None,         validation_alias=AliasChoices("PIPELINE_UAT_LLM_BASE_URL"),         description="Optional Anthropic-compatible base URL override for pipeline UAT commentary "         "(e.g. a local OmniRoute gateway). None = call Anthropic directly (default, unchanged behavior).",     )     `
      Done-when: field present, `basedpyright`/`ruff` clean, no other config field touched.
- [ ] [BACKEND] P2. **Thread it into the client construction.** In
      `deployment-api/deployment_api/commentary/pipeline_uat.py`'s `_call_anthropic` (line 237), change:
      `python     client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)     ` to:
      `python     client = anthropic.AsyncAnthropic(         api_key=config.anthropic_api_key, base_url=config.pipeline_uat_llm_base_url     )     `
      (the `anthropic` SDK's `base_url` already defaults to `None` = its own default endpoint, so this is additive — no
      behavior change when the new config field is unset). Done-when: diff is exactly this one-line expansion, no other
      line in `_call_anthropic` touched.
- [ ] [BACKEND] P2. **Test both branches** in `deployment-api/tests/unit/test_pipeline_uat.py`, extending the existing
      `patch("deployment_api.commentary.pipeline_uat.anthropic.AsyncAnthropic")` pattern (see
      `test_run_pipeline_uat_enabled_calls_anthropic`): - a test asserting
      `mock_client.call_args.kwargs["base_url"] is None` when `pipeline_uat_llm_base_url` is left at its default (proves
      the default path is byte-for-byte unchanged); - a test asserting
      `mock_client.call_args.kwargs["base_url"] == "http://localhost:20128/v1"` when the config field is set to that
      value. Done-when: both tests pass under `bash scripts/quality-gates.sh` in `deployment-api`, and every
      pre-existing test in `test_pipeline_uat.py` still passes unmodified (this is additive, not a rewrite of existing
      assertions).
- [ ] [OPERATOR] P3. **Stand up OmniRoute itself** (self-host the gateway locally/on the deployment-api host,
      `localhost:20128/v1`) and set `PIPELINE_UAT_LLM_BASE_URL` in the relevant env for a trial window. Tagged
      `[OPERATOR]` — this installs and runs a new persistent third-party network service, a class of decision (like a VM
      launch) this workspace routes to the operator rather than an autonomous worker, independent of the trust-boundary
      waiver above (the waiver says the RISK is accepted; running new infra is still an operator act).
- [ ] [REVIEW] P3. **Run the pilot for a real window** (operator's original proposal: ~2 weeks of pipeline-UAT runs) and
      compare cost-per-call, latency, and a spot-check that commentary quality didn't regress (system prompt's own bar:
      "concise, plain-language, under 6 sentences unless critical" — easy to eyeball). Done-when: a reported
      before/after on cost + a pass/fail on the quality spot-check.

## Explicitly out of scope (the guardrail's own boundary)

Extending this to `agent-orchestrator/server/accounts.py`'s `AccountProvider` (i.e. routing actual Claude Code worker
sessions through OmniRoute) is **not** part of this pilot and is not pre-approved by a good pilot result — per the
guardrail above, that would need its own fresh model-tier-risk review, not an inference from this doc.

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — the qualitative `opus-required`/`fable-required` contract the
  guardrail protects, and where this plan's cross-reference note lands
- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the existing multi-account /
  `ANTHROPIC_BASE_URL` mechanism this pilot deliberately does NOT reuse (see guardrail)
