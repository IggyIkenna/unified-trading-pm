---
doc_type: plan
title: OmniRoute multi-provider LLM-gateway pilot — deployment-api pipeline-UAT commentary (human execution)
summary: >-
  Operator flagged omniroute.online (a self-hosted, OpenAI/Anthropic-compatible local gateway that auto-routes across
  268 providers' free/cheap tiers) as a possible cost-routing layer, given the fleet already has a DeepSeek-swap
  precedent (`agent-orchestrator/server/accounts.py`'s `AccountProvider`). Operator ruling 2026-07-30 waived the
  trust-boundary objection and directed the model-tier-SSOT-conflict objection be resolved by a structural guardrail
  rather than by staying gated — this doc records both rulings and gives the pilot itself full build-grade detail (exact
  files/fields/tests/done-whens), while staying a LOCAL/human-executed plan (not AO-dispatched) per the operator's
  explicit choice. 2026-08-02: operator pushed back on the original "never touch the worker fleet" framing — the
  "Worker- fleet routing" section records the actual fresh model-tier-risk review this required, resolving to a
  BOUNDED-relay design (OmniRoute configured to a curated model set, never full-auto) rather than a blanket ban, with 3
  research prerequisites (real OmniRoute account access, the real allowlist mechanism, the curated model list) before
  any code.
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
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
created: 2026-07-30
last_updated: 2026-08-02
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

- [x] [INFRA] P2. ✅ Add a guard comment directly above `AccountProvider = Literal["anthropic", "deepseek"]` in
      `agent-orchestrator/server/accounts.py` stating: this Literal must never gain a value that routes through a
      shared/opaque multi-provider gateway (OmniRoute or equivalent) without a fresh, explicit model-tier-risk review —
      cite `/codex/06-coding-standards/model-tier-selection.md`. Done-when: comment present, references the exact codex
      path. — `agent-orchestrator@f0c4726` (comment landed pre-generalization; carried forward intact through
      `agent-orchestrator@24bd611`'s Phase-2 AccountProvider broadening).
- [x] [INFRA] P2. ✅ Add a short note to `/codex/06-coding-standards/model-tier-selection.md` cross-referencing this
      plan and stating the same boundary from the SSOT side (an opaque multi-provider router is out of scope for any
      `AccountProvider`-routed worker traffic; the one sanctioned pilot surface is `deployment-api` pipeline-UAT
      commentary, tracked here). Done-when: the note exists and the plan doc is linked from it (or vice versa via
      `context_scope`). — `unified-trading-pm@1afce7135`, "Multi-provider gateway boundary (2026-07-30)" section added,
      cross-references this plan doc + the DeepSeek plan. (Superseded in spirit by the "worker-fleet routing" section
      below — the codex note describes the ORIGINAL blanket boundary; the refined, conditional policy is recorded here
      and should be folded into the codex note once the design is actually implemented, not before.)

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

- [x] [BACKEND] P2. ✅ **Add the config field.** In `deployment-api/deployment_api/deployment_api_config.py`, in the
      `# PIPELINE UAT COMMENTARY` section (currently lines 678-704, alongside
      `pipeline_uat_commentary_enabled`/`anthropic_api_key`/`pipeline_uat_model`), add:
      `python     pipeline_uat_llm_base_url: str | None = Field(         default=None,         validation_alias=AliasChoices("PIPELINE_UAT_LLM_BASE_URL"),         description="Optional Anthropic-compatible base URL override for pipeline UAT commentary "         "(e.g. a local OmniRoute gateway). None = call Anthropic directly (default, unchanged behavior).",     )     `
      Done-when: field present, `basedpyright`/`ruff` clean, no other config field touched. — `deployment-api@c61070d`,
      field added exactly as specified, no other field touched.
- [x] [BACKEND] P2. ✅ **Thread it into the client construction.** In
      `deployment-api/deployment_api/commentary/pipeline_uat.py`'s `_call_anthropic` (line 237), change:
      `python     client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)     ` to:
      `python     client = anthropic.AsyncAnthropic(         api_key=config.anthropic_api_key, base_url=config.pipeline_uat_llm_base_url     )     `
      (the `anthropic` SDK's `base_url` already defaults to `None` = its own default endpoint, so this is additive — no
      behavior change when the new config field is unset). Done-when: diff is exactly this one-line expansion, no other
      line in `_call_anthropic` touched. — `deployment-api@c61070d`, exactly this one-line expansion (ruff reformatted
      it onto a single line; no other line in `_call_anthropic` touched).
- [x] [BACKEND] P2. ✅ **Test both branches** in `deployment-api/tests/unit/test_pipeline_uat.py`, extending the
      existing `patch("deployment_api.commentary.pipeline_uat.anthropic.AsyncAnthropic")` pattern (see
      `test_run_pipeline_uat_enabled_calls_anthropic`): - a test asserting
      `mock_client.call_args.kwargs["base_url"] is None` when `pipeline_uat_llm_base_url` is left at its default (proves
      the default path is byte-for-byte unchanged); - a test asserting
      `mock_client.call_args.kwargs["base_url"] == "http://localhost:20128/v1"` when the config field is set to that
      value. Done-when: both tests pass under `bash scripts/quality-gates.sh` in `deployment-api`, and every
      pre-existing test in `test_pipeline_uat.py` still passes unmodified (this is additive, not a rewrite of existing
      assertions). — `deployment-api@c61070d`, both new tests added + passing, full deployment-api QG green
      (`quality-gates.sh --no-fix`, pytest + basedpyright + ruff clean), every pre-existing test unmodified.
- [ ] [OPERATOR] P3. **Stand up OmniRoute itself** (self-host the gateway locally/on the deployment-api host,
      `localhost:20128/v1`) and set `PIPELINE_UAT_LLM_BASE_URL` in the relevant env for a trial window. Tagged
      `[OPERATOR]` — this installs and runs a new persistent third-party network service, a class of decision (like a VM
      launch) this workspace routes to the operator rather than an autonomous worker, independent of the trust-boundary
      waiver above (the waiver says the RISK is accepted; running new infra is still an operator act).
- [ ] [REVIEW] P3. **Run the pilot for a real window** (operator's original proposal: ~2 weeks of pipeline-UAT runs) and
      compare cost-per-call, latency, and a spot-check that commentary quality didn't regress (system prompt's own bar:
      "concise, plain-language, under 6 sentences unless critical" — easy to eyeball). Done-when: a reported
      before/after on cost + a pass/fail on the quality spot-check.

## Worker-fleet routing — the "fresh model-tier-risk review" the guardrail called for (2026-08-02)

The guardrail above says extending OmniRoute to `accounts.py`'s `AccountProvider` needs its own fresh review, not an
inference from this doc. This section IS that review — conducted after the operator pushed back on the original "never"
framing: the actual objection was never "OmniRoute must never touch the worker fleet," it was specifically **OmniRoute's
own `auto` model-selection mode** (9-factor scoring, cheapest-across-268-providers) making the served model
unpredictable per spawn — nothing in AO's dispatch path could then verify a `sonnet`-tier task actually got
sonnet-equivalent quality, not some arbitrary weak free model.

**The resolution: a bounded relay, not a blanket ban.** `omniroute.online`'s own landing page (fetched 2026-08-02;
account signup required for the real dashboard/API docs, not yet done) confirms model selection supports **both** `auto`
**and pinning a specific model name** per request, and references "18 routing strategies" + a "build your own combo"
custom-routing-policy concept — very likely the mechanism for constraining the pool, though the exact config/field names
aren't in the public marketing page and need verification once an account exists. Operator's framing (2026-08-02): AO
would spawn a worker THROUGH OmniRoute, but OmniRoute itself is configured (gateway-side, an operator-curated "combo")
to a bounded set of vetted models — OmniRoute still auto-picks CHEAPEST _within_ that set, so cost-optimization stays
dynamic while quality risk is bounded to "one of several pre-vetted acceptable models," not "any of 268." This is
materially different from full-auto mode, and a reasonable middle ground given AO's own dispatch design already does the
heavy lifting of scoping work down to bounded, "easy" sonnet-tier tasks before a worker is ever spawned (context_scout +
plan-brainstorm's pre-authoring scoping, heavy/judgment-call work staying `opus-required` and hard-pinned to Claude
regardless).

**What does NOT change**: the opus/fable hard pin (`_short_tier(model) != "sonnet"` branch in
`select_account_for_spawn()`) is completely independent of which providers exist in the free pool — it already runs
BEFORE any provider, OmniRoute or otherwise, is even considered. Nothing about this design touches that gate.

**What's still missing before this can be built (research todos, not yet actionable as code):**

- [ ] [OPERATOR] P3. Sign up for `omniroute.online` and obtain real dashboard/API access — the public landing page has
      no developer docs; the actual "combo"/routing-strategy config schema, request/response shape, and auth model are
      only visible post-signup. Done-when: real account exists, real docs or dashboard screenshots available to design
      against.
- [ ] [REVIEW] P3. Once signed up, confirm the exact mechanism for constraining OmniRoute's routing to a curated model
      set (the "combo"/routing-strategy concept) — exact config location (dashboard vs. request header vs. a hosted
      config file), exact field names, and whether the constraint is enforced gateway-side (so AO's own request is
      simple) or must be specified per-request (so AO's code would need to carry the allowlist). Done-when: a dated
      Progress Log entry names the real mechanism with a citation (screenshot/doc link/config example).
- [ ] [OPERATOR] P3. Decide the actual curated model allowlist ("combo") — which specific models are vetted as
      "sonnet-tier-equivalent good enough" for AO worker spawns. A quality/business judgment call, not a technical one;
      tagged `[OPERATOR]` per the business-judgment carve-out (mirrors the self-hosted-models todo on the DeepSeek
      plan). Done-when: a named, dated list of acceptable models exists in this plan's Progress Log.
- [ ] [INFRA] P3. Once the above 3 are resolved, design + implement the actual `agent-orchestrator` integration:
      register `"omniroute"` as a new `AccountProvider` value (the Literal is already open per
      `deepseek_claude_blended_provider_routing_2026_07_28`'s Phase 2 generalization — `agent-orchestrator@24bd611` — so
      this is additive, not a re-generalization), an account entry pointing `ANTHROPIC_BASE_URL` at the OmniRoute
      gateway with whatever the confirmed allowlist mechanism requires, and a real isolated local pilot dispatch proving
      a sonnet-tier spawn routes through it correctly (same bar as the DeepSeek and generalized-provider work).
      Done-when: same proof standard as `[INFRA] P2` on the DeepSeek plan — a real, isolated local pilot dispatch, not
      just unit tests.

This section supersedes the earlier "not pre-approved by a good pilot result" framing below for the SPECIFIC bounded-
relay design — the previous framing (extending to `AccountProvider` needs a fresh review) is satisfied by this section
existing; what's not yet satisfied is the review's OWN 3 prerequisites above, so this remains a design decision with
concrete next steps, not yet a green light to write the integration code.

## Explicitly out of scope (the guardrail's remaining boundary)

**Full-auto OmniRoute routing** (no curated model allowlist — genuinely any of the 268 providers, whatever scores
cheapest) for worker-fleet traffic remains out of scope, full stop — that is the exact risk the guardrail exists to
block, and no operator ruling has waived it. Only the BOUNDED-relay design above (gateway-side curated model set) is
under active consideration, and only once its 3 prerequisite research todos resolve.

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — the qualitative `opus-required`/`fable-required` contract the
  guardrail protects, and where this plan's cross-reference note lands
- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the existing multi-account /
  `ANTHROPIC_BASE_URL` mechanism this pilot deliberately does NOT reuse (see guardrail)

## Progress Log

- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the
  doc's own opening section states an explicit, dated operator ruling (2026-07-30) waiving the trust-boundary objection
  and directing the model-tier-SSOT-conflict objection be resolved by a structural guardrail, explicitly keeping this
  doc `assigned_vm: NA`/`execution_scope: local-only` by operator choice even though the individual todos read as
  AO-dispatch grade. Citation confirmed present verbatim in the doc body — never re-litigating an established ruling.
- **2026-08-02 — `/autonomous` dispatch, all 5 non-operator-gated todos SHIPPED, closing them.** Guardrail comment +
  codex cross-reference, the `pipeline_uat_llm_base_url` config field, its `_call_anthropic` threading, and both unit
  tests — all landed exactly as this doc specified. Evidence: `agent-orchestrator@f0c4726` (guardrail comment),
  `deployment-api@c61070d` (config field + threading + tests, full QG green), this same commit (codex cross-reference).
  **Remaining on this plan — both operator-gated, none locally doable**: standing up OmniRoute itself (`[OPERATOR]` P3)
  and running the real pilot window (`[REVIEW] P3`, depends on the former) — per the plan's own scoping, these install
  persistent third-party infra and require a live 2-week window respectively, neither buildable/verifiable from a dev
  checkout.
- **2026-08-02 — worker-fleet routing revisited, interactive session.** Operator pushed back on this plan's original
  "OmniRoute must never touch AO's worker fleet" framing after the todos above shipped — clarified the actual intent was
  always "AO spawns through OmniRoute as another option," and asked whether that's still viable given the guardrail.
  Re-examined: the real risk was never "OmniRoute touches the fleet," it was specifically OmniRoute's `auto`
  model-selection mode making the served model unpredictable per spawn. Fetched `omniroute.online`'s public landing page
  (no account yet — dashboard/API docs are not public) and confirmed: OpenAI-compatible single endpoint translating
  OpenAI/Claude/Gemini request shapes; model selection supports both `auto` (9-factor scoring) and pinning a specific
  model name per request; references "18 routing strategies" + a "build your own combo" custom-policy concept as the
  likely (unconfirmed — needs real account access) mechanism for constraining the pool. Operator's resolution: a BOUNDED
  relay — OmniRoute configured (gateway-side, a curated "combo") to a vetted model set, still auto-picking cheapest
  WITHIN that set, reasoning that AO's own dispatch design (context_scout + plan-brainstorm's pre-authoring scoping)
  already bounds worker-spawned tasks to "easy," sonnet-tier work before a worker ever spawns — so a curated-set quality
  floor is an acceptable trade for dynamic free-tier cost optimization. Wrote this up as its own "Worker-fleet routing"
  section (supersedes "Explicitly out of scope" for this specific bounded design; full-auto routing stays explicitly out
  of scope, unchanged) with 3 research prerequisites before any code: real OmniRoute account/dashboard access, the real
  allowlist/combo mechanism confirmed against real docs (not the marketing page), and the operator's actual curated
  model list. No code shipped this entry — planning/research only.
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`, dispatch agt-da0e58, slot 10): re-verified, no change —
  all 6 remaining open todos are either directly `[OPERATOR]`-tagged (stand up OmniRoute, sign up for real account
  access, decide the curated model allowlist) or explicitly gated behind one of those three (`[REVIEW]`/`[INFRA]`
  follow-ons). Doc still stays `assigned_vm: NA`/`execution_scope: local-only` by explicit operator choice per its own
  opening section. No re-litigation needed — citation still present verbatim.
