---
doc_type: codex-ssot
title: Pre-Demo Discovery Framework
summary:
  Lightly-guided non-interrogation discovery — 8 signal dimensions sales infers and records without qualification forms
  (commercial-path readiness, DART fit, strategy state, market scope, exchange/treasury readiness, regulatory cover,
  decision-maker structure, timeline/appetite); every observed signal lands in the account-intelligence record.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, discovery, qualification, prospect, crm]
related:
  [
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
  ]
created: 2026-04-20
authoritative_for: [pre-demo discovery framework (signal dimensions)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Pre-Demo Discovery Framework

> What sales infers about the prospect and records without interrogating them. DART readiness, strategy state, exchange
> onboarding, treasury workflows, regulatory cover. Signals the sales person picks up across calls and briefing views,
> structured for feeding the account-intelligence record.

**Rule source:** [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md) §Lightly guided

## Posture

Rule 02 calls for lightly-guided discovery. Odum does not interrogate prospects with qualification questionnaires.
Institutional buyers resent being qualified. Instead, sales infers from observable signals and records what is observed.

The pre-demo discovery framework lists the signals sales looks for and where they are recorded (in the
account-intelligence record).

## Dimension 1 — Commercial path readiness

Does the prospect know which service they want?

| Signal                                                | What it tells you                               |
| ----------------------------------------------------- | ----------------------------------------------- |
| Intro-call framing names a specific service           | Path resolved or near-resolved                  |
| Intro-call framing is "what do you do?"               | Path unresolved; pb1 / rule 09 expansion needed |
| Prospect asks about "fund structure" or "NAV"         | Lean IM                                         |
| Prospect asks about "execution" or "venue onboarding" | Lean DART signals-only                          |
| Prospect asks about "regulatory cover" or "FCA"       | Lean Reg Umbrella                               |
| Prospect asks about "backtest" or "research"          | Lean full DART                                  |
| Prospect asks "all three?"                            | Combined; resolve in pb2                        |

## Dimension 2 — DART fit (if DART is the path)

For DART prospects, rule 10's fit-check resolves signals-only vs full-pipeline.

| Signal                                                                              | What it tells you                                     |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------- |
| "We have a working strategy"                                                        | Signals-only candidate; rule 10 fit-check runs        |
| "We want to build strategies"                                                       | Full DART candidate                                   |
| "We already backtest / do research"                                                 | Signals-only with own research; rule 10 fits          |
| "We don't have a strategy; want to use yours"                                       | `(Odum, full)` cell                                   |
| Prospect's description of their signal generator maps to rule 10's 8 fields cleanly | Signals-only schema fit                               |
| Their upstream needs "bespoke fields"                                               | Rich schema or block 13 custom premium                |
| They can't stably identify their strategies                                         | Schema fit-check fails; route to full DART or bespoke |

## Dimension 3 — Strategy state

Where is the prospect's existing strategy in its lifecycle?

| Signal                  | What it tells you                                         |
| ----------------------- | --------------------------------------------------------- |
| "Live on our own infra" | Mature; signals-only fit; scope inference possible        |
| "Paper-trading"         | Pre-commit; upgrade to full-DART promote pipeline may fit |
| "Just backtested"       | Early; full DART candidate                                |
| "Concept stage"         | Too early for demo; do more pb2 briefing work first       |

## Dimension 4 — Market scope

What venues, chains, instruments, strategy families does the prospect touch?

- Prospect names specific venues → record as `market_scope.venues`.
- Prospect names chains (even casually: "we're on Arbitrum") → record as `market_scope.chains`.
- Prospect names instruments or asset class (perps / options / spot / DeFi) → record as `market_scope.instrument_types`.
- Prospect mentions a strategy family or archetype → record as `market_scope.strategy_families`.

If no scope is mentioned, do not press. Ask ambient questions only: "what's the typical instrument set?"

## Dimension 5 — Exchange and treasury onboarding readiness

For DART and Reg Umbrella prospects, infer whether they have the operational bandwidth for onboarding.

| Signal                                | What it tells you                                 |
| ------------------------------------- | ------------------------------------------------- |
| "We already have venue accounts"      | Ready; onboarding is credential-handoff + API-key |
| "We need to open new venue accounts"  | Onboarding includes venue-setup time              |
| "Our treasury is on one wallet"       | DeFi-ready simple case                            |
| "We have complex multi-chain custody" | DeFi-ready complex case; scope accordingly        |
| No mention of custody                 | Probe gently — necessary for DeFi engagements     |

## Dimension 6 — Regulatory cover readiness

For Reg Umbrella prospects, and for any engagement touching regulated activity.

| Signal                                                     | What it tells you                             |
| ---------------------------------------------------------- | --------------------------------------------- |
| "We hold our own FCA permissions"                          | Reg Umbrella is wrong fit; IM or DART only    |
| "We're seeking regulatory cover"                           | Reg Umbrella fit confirmed                    |
| "We're exploring whether to apply for our own permissions" | Odum does not advise on that; route carefully |
| "We're launching a new vehicle"                            | Emerging manager fit                          |
| "We run a DeFi operation that's unclear regulatorily"      | Reg Umbrella scoping needed                   |

## Dimension 7 — Decision-maker structure

Who decides, who blocks, who signs?

- Single contact who attends everything → decision-maker alone. Turbo demos fit.
- Multiple attendees with varied roles → committee dynamic. Broader-platform demos fit.
- Prospect keeps referring back to "our CIO" or "our investment committee" → the decision is elsewhere; record the
  latent decision-maker.

## Dimension 8 — Timeline and commercial appetite

| Signal                            | What it tells you                                   |
| --------------------------------- | --------------------------------------------------- |
| "We want to launch by Q2"         | ~3-month timeline; aggressive onboarding            |
| "We're still evaluating"          | No specific timeline; broader-platform demos        |
| Objection to twelve-month minimum | Commercial sensitivity; handle directly, don't hide |
| "What does Tier B cost?"          | Decision-ready on commercial terms                  |

## Recording discipline

Every signal observed goes into the account-intelligence record (see
[`account-intelligence-record.md`](account-intelligence-record.md)) with:

- Timestamp
- Session context (call, briefing, demo)
- Verbatim quote if the prospect said something explicit
- Sales-person's inference if implicit

## Non-interrogation practice

- **Do not hand a qualification form.** Use observed signals + natural conversation.
- **Do not ask what you could infer.** If the prospect has declared signals-only intent, don't re-ask "so what path are
  you on?"
- **Do ask specific operational questions.** "What venues are you on currently?" is operational context, not
  qualification.
- **Do not probe on IP.** Never ask "what's your strategy edge?" or similar. Upstream stays upstream (rule 10).

## Cross-references

- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md)
- [rule 10 — strategy instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md)
- [account-intelligence-record.md](account-intelligence-record.md) — where signals land
- [demo-decision-matrix.md](demo-decision-matrix.md) — signals drive matrix resolution
- [pre-demo-curation-rules.md](pre-demo-curation-rules.md) — curation reads signals
