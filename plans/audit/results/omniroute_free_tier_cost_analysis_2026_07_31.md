---
doc_type: audit-result
title: OmniRoute (omniroute.online) — free-tier mechanics, real token economics, and applicability to our Claude spend
summary: >-
  Researches OmniRoute's free-tier LLM routing mechanism and economics against our 6-account Claude Max spend. Finding:
  OmniRoute requires per-provider account creation and OAuth-style linking (it does not create free accounts for you),
  free-tier allocations are small and provider-imposed (not OmniRoute's to enlarge), and no credible evidence supports
  meaningfully offloading Claude-specific work through it. Recommendation: do not integrate for Claude-cost reduction —
  the free-tier economics don't move the needle against 6 Max20x subscriptions.
status: pass
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [audit, omniroute, cost-optimization, claude-accounts, llm-routing]
related:
  - plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md
created: 2026-07-31
audited_scope:
  OmniRoute (omniroute.online) mechanism and account-creation model; free-tier token/dollar economics across providers;
  security posture; applicability to reducing the 6-account Claude Max fleet spend.
date: "2026-07-31"
auditor: claude-code (interactive session, slot NA)
parent_epic: orchestrator_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
---

> **Status note**: this is a completed research write-up evaluating a potential integration (not an audit of an existing
> system). Conclusion: do not integrate OmniRoute for Claude-cost reduction — nothing here blocks other work.

## Why this doc exists

Operator asked (2026-07-31) for a thorough, evidence-based report on OmniRoute answering three concrete questions,
prompted by our own 7-Claude-Max-account fleet (~$200+/mo each, continuous heavy agentic workload):

1. How much in tokens/dollars do we realistically get "free" from OmniRoute?
2. How does it actually work — does it create free accounts on all providers for us, or do we create our own accounts
   and OmniRoute just routes across them?
3. Given our actual usage pattern (7 Max accounts, "massive work everyday"), how much of that could realistically shift
   to OmniRoute for free?

This is downstream of
`/active/unified-trading-system-repos/unified-trading-pm/plans/active/omniroute_llm_gateway_pilot_design_2026_07_30.md`
(a separate, narrower LOCAL design doc scoping a pilot on `deployment-api`'s read-only pipeline-UAT commentary caller —
not the worker fleet). This doc is the cost/mechanics research underpinning any future decision on that pilot or on
touching the worker fleet at all; it does not modify that plan.

## Bottom line (read this first)

**OmniRoute cannot meaningfully reduce our actual Claude spend.** Anthropic/Claude is not part of its free-or-cheap
provider pool at all. The one indirect touchpoint (Kiro AI, an AWS Claude-Sonnet-4.5 wrapper) caps at roughly 25K–100K
tokens **total per month** — a rounding error against what one Max-plan account burns in a single day of continuous
agentic work — and using it through a proxy like OmniRoute is itself a violation of Kiro's own ToS. Every other
free/cheap provider in OmniRoute's pool is a **different, non-Claude model** (Mistral, GLM, DeepSeek, Cerebras, Qwen,
Gemini, etc.) — conceptually the same idea as our own DeepSeek integration (`agent-orchestrator/server/accounts.py`'s
`AccountProvider`), just against ~90 providers instead of one, with meaningfully worse security posture and no
additional Claude-cost benefit.

## 1. How it actually works (mechanism)

OmniRoute is a **self-hosted gateway you run yourself** — a local Node.js process, default endpoint
`http://localhost:20128/v1` — not a hosted service and not a shared account pool. You point `ANTHROPIC_BASE_URL` (or
`OPENAI_BASE_URL`) at it and it forwards each request to whichever of its cataloged providers your routing rules pick.

**It does not create accounts for you.** `omniroute setup` is an interactive wizard that walks _you_ through signing up
for each provider individually — your own email, your own API key from each provider's own dashboard, pasted into
OmniRoute's local dashboard. It is your identity and your ToS exposure, replicated across as many of the ~90 free-tier
providers as you choose to onboard. OmniRoute's own value-add is purely the routing/fallback/observability layer on top
of credentials you supply.

It does support genuine Anthropic-Messages-API wire format for Claude Code specifically (an `anthropic-compatible-cc-*`
provider type, not just an OpenAI-compatible passthrough) — so from a wire-protocol standpoint, pointing
`ANTHROPIC_BASE_URL` at it is technically viable. This corrects an earlier open question from the
`omniroute_llm_gateway_pilot_design_2026_07_30.md` scrutiny, which had flagged this as an unverified assumption.

**Provider count is inconsistent across OmniRoute's own marketing surfaces** (264 in its README, 236 on its website, 250
in auto-generated docs) — a minor but real signal about how carefully the project's own numbers are maintained.

## 2. The "1.4–1.6B free tokens/month" headline, examined

Real in the sense that it is a documented sum of ~40–90 providers' individually-published free tiers, but softer than
the headline suggests once you look at concentration and caps:

- **~65% of the entire pool is one provider** — Mistral, ~1B tokens/month by itself. An independent reviewer's math:
  _"if Mistral tightens its free tier or your account loses eligibility, the recurring budget effectively collapses to a
  few hundred million tokens"_ spread across a long tail of much smaller providers.
- **Real per-provider ceilings well below fleet-scale usage**: Cerebras ~30K tokens/minute, Groq ~14.4K requests/day,
  Kiro ~50 credits/month. A continuously-running agentic worker fleet would exhaust most of these in minutes, not hours,
  then fall back to each provider's own paid tier anyway.
- **~19 of the cataloged providers are ToS-flagged "caution" by OmniRoute's own docs** for explicitly prohibiting
  proxy/resale/third-party-credential use — i.e., routing them through a gateway like this is itself the exact violation
  category their terms exist to prevent. OmniRoute's own stance: _"informational, not legal advice — you decide."_
- Signup-credit tiers (Vertex ~300M one-time, AgentRouter ~200M one-time, Together ~25M, DeepSeek ~5M) are **one-time**,
  not recurring — they inflate a "first month" headline number that does not repeat.

## 3. Does this touch our Claude spend? (the central finding)

Checked directly against OmniRoute's own `docs/reference/FREE_TIERS.md`: **Anthropic/Claude appears nowhere in it.** No
free tier, no credits, no paid-but-cheap tier — nothing.

The **only** path to anything resembling real Claude access anywhere in OmniRoute's ecosystem:

- **Kiro AI** (AWS's Claude-powered IDE backend) serves genuine **Claude Sonnet 4.5** — same model tier as a paid
  Anthropic subscription — but capped at **~50 credits/month, roughly 25K–100K tokens total for the whole month**, not
  per day. **Kiro's own ToS explicitly prohibits third-party proxy/harness use** — using it via OmniRoute is precisely
  the pattern flagged as a violation risk elsewhere in OmniRoute's own docs.

One independent reviewer's framing is the cleanest summary: _"OmniRoute does not unlock Anthropic's models for free — it
redirects the Claude Code CLI to other backends,"_ routing to Mistral/Cerebras/GLM/DeepSeek/etc. instead of Anthropic's
own infrastructure.

**Answer to the operator's core question**: realistically, **none** of our 7-Max-account daily workload could shift to
OmniRoute for free. The absolute ceiling — Kiro's ~100K tokens/month, obtained only by violating Kiro's ToS — is
multiple orders of magnitude below what a single Max account burns in a single day of continuous agentic work, let alone
what 7 accounts running "massive work everyday" consume.

## 4. What OmniRoute would actually be useful for (and why we've already built the useful part)

Its genuine value proposition is substituting **non-Claude** models for tasks that don't need Claude's judgment — the
same shape as our shipped DeepSeek routing (`AccountProvider = Literal["anthropic", "deepseek"]` in `accounts.py`), just
against ~90 providers instead of 1. Realistic incremental value on top of what we already have is limited by:

- Free-tier rate limits sized for individual-developer usage, not a fleet of continuous agentic workers.
- Lossy prompt compression (advertised 15–95% token savings via "RTK+Caveman") — reviewers are explicit this degrades
  output quality on complex reasoning/code, a real risk for correctness-sensitive agentic work.
- Any dollar saved would be incremental on top of DeepSeek, never a replacement for the $1,400+/mo baseline the 7 Max
  accounts represent.

## 5. Security / legitimacy posture (recap, load-bearing for any go/no-go)

- Ships a **MITM proxy + TLS-fingerprint stealth (JA3/JA4)** — explicitly designed to evade providers' anti-abuse
  detection; a deliberate design choice, not a side effect.
- **Socket.dev flagged npm v3.8.5** (May 2026). Maintainer confirmed 2 of 6 flagged items were genuine vulnerabilities —
  a silent credential-overwrite path in Cloud Sync, and a Keychain-import flaw exposing credentials — patched in v3.8.6.
  The Socket.dev reporter rated the maintainer's response as responsible.
- Young, single-maintainer project with no production track record. One reviewer's framing: _"20,000 GitHub stars is not
  20,000 production hours."_

## Recommendation

Do not integrate OmniRoute to reduce Claude spend — it structurally cannot, since Anthropic is absent from its
free/cheap pool, and the one adjacent path (Kiro) is both trivially small relative to our usage and itself a ToS
violation to use at all. If ever revisited, the only defensible angle is as one more low-stakes _alternate-provider_
option layered on the DeepSeek pattern already shipped — and even there, the security trade (MITM/stealth tooling,
single-maintainer supply chain, ~19 ToS-flagged providers) is materially worse than what exists today for the one
provider (DeepSeek) we already trust and have integrated cleanly.

## Open questions for further research (per operator: doc stays local until these are resolved)

- [ ] Quantify actual current call volume through `deployment-api`'s pipeline-UAT commentary caller (the one pilot
      surface proposed in `omniroute_llm_gateway_pilot_design_2026_07_30.md`) — is it even enabled/scheduled anywhere
      today? Config default is `pipeline_uat_commentary_enabled: false`; no scheduler/cron wiring was found in the
      research pass that touched this. If it's genuinely idle, the pilot has ~$0 at stake either way.
- [ ] Independently verify the Kiro AI credit-to-token conversion (~50 credits ≈ 25K–100K tokens) against Kiro's own
      published docs rather than secondary sources — the range is wide enough to matter if this is ever revisited.
- [ ] Check whether any of the ~90 free-tier providers offer a model genuinely competitive with DeepSeek V4 Pro for our
      existing sonnet-tier routing split, which would be the only scenario where OmniRoute adds real incremental value
      over what's already shipped.

## Sources

- [GitHub — diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute)
- [OmniRoute FREE_TIERS.md](https://github.com/diegosouzapw/OmniRoute/blob/main/docs/reference/FREE_TIERS.md)
- [OmniRoute USER_GUIDE.md](https://github.com/diegosouzapw/OmniRoute/blob/main/docs/guides/USER_GUIDE.md)
- [OmniRoute CLAUDE-CODE-CONFIGURATION.md](https://github.com/diegosouzapw/OmniRoute/blob/main/docs/guides/CLAUDE-CODE-CONFIGURATION.md)
- [OmniRoute Review (2026) — rohitraj.tech](https://rohitraj.tech/en/notes/omniroute-ai-gateway-review-2026)
- [OmniRoute: Free Local AI Gateway for Claude Code — explainx.ai](https://explainx.ai/blog/omniroute-ai-gateway-free-llm-proxy-claude-code-2026)
- [OmniRoute's "unlimited free" claim — 90 providers, not 200 — dev.to](https://dev.to/creeta/omniroutes-unlimited-free-claim-90-providers-not-200-49j2)
- [Security concern: v3.8.5 flagged by Socket.dev — GitHub Issue #2863](https://github.com/diegosouzapw/OmniRoute/issues/2863)
- [OmniRoute Review 2026 — compsmag.com](https://www.compsmag.com/reviews/omniroute-review/)
- [9.3k-Star GitHub Project OmniRoute Unlocks 1.6B Free Tokens — nerdzap.com](https://nerdzap.com/news/omniroute-open-source-ai-gateway-free-tokens/)
- [Claude Code Pricing 2026 — finout.io](https://www.finout.io/blog/claude-code-pricing-2026)

## Related

- `/active/unified-trading-system-repos/unified-trading-pm/plans/active/omniroute_llm_gateway_pilot_design_2026_07_30.md`
- `agent-orchestrator/server/accounts.py` (`AccountProvider` — the existing DeepSeek-routing seam)
- `deployment-api/deployment_api/commentary/pipeline_uat.py` (the one proposed pilot surface)
