---
scope: [engineer, admin, sales]
---

# Rule 09 — Internal commercial one-liners

> Three sentences, internal use only. Every public-facing doc expands them into a calm institutional paragraph using the
> rule-02 voice. Internal docs can use them verbatim.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On internal commercial one-liners (rule 09)". User
voice, 2026-04-19.

## The three one-liners

### DART

> An accelerator for strategy, research, execution, and control — the same system Odum uses internally.

### Investment Management (IM)

> Allocate capital to Odum-managed strategies; reporting is built in because it is the same reporting system Odum uses
> itself.

### Regulatory Umbrella

> Operate your regulated activity under Odum's FCA permissions; onboarding, compliance, MLRO, supervision, and reporting
> included.

## What these are for

Internal shorthand. A one-line answer to "what is DART / IM / Reg Umbrella" that a sales person, a new hire, or an
internal reviewer can give without ambiguity. They are the scope-setting sentences that every longer piece of content
expands.

## What these are not

They are **not client-facing copy as-is.** The one-liners are honest, but dense. Lifted directly into a website or
briefing, they read as internal shorthand. External docs expand each one into a calm paragraph that unpacks the claim,
offers a specific proof point, and uses rule-02 voice.

## Expansion pattern

Each one-liner expands using the same pattern for external docs:

1. Lead with the positioning claim (what the service does).
2. Follow with the differentiator (what makes it credible / what's the mechanism).
3. Close with a concrete proof point or scope statement.

Worked expansions below.

### DART — external expansion

> DART is the set of services Odum uses to build, research, promote, execute, and monitor its own systematic strategies,
> packaged for client use. Clients who operate their own strategies can plug their signals into Odum's execution and
> reporting stack, or they can use the full research and promotion pipeline. The underlying components are the same as
> Odum's internal operation — one system, partitioned views.

One paragraph, three sentences, no forward-tense, no adverbs.

### IM — external expansion

> Investment Management allocates client capital to Odum-run systematic strategies operating under Odum's FCA
> permissions. Reporting — positions, exposures, P&L, reconciliation — comes from the same surface Odum uses to run its
> own operation, with allocator-side views filtered by entitlement. The minimum engagement is twelve months; the
> onboarding path sets up the fund structure (Pooled or SMA), capital allocation, and reporting at the same time.

### Reg Umbrella — external expansion

> Firms running regulated activity that want operational coverage without seeking direct FCA authorisation can operate
> under Odum's permissions. Onboarding handles regulatory scope, compliance setup, MLRO coverage, and supervisory
> reporting. Reporting surfaces use the same component tree as IM and DART reporting, filtered to the firm's
> regulated-activity view.

## When to use the one-liner vs the expansion

| Context                                         | Use                                              | Why                                |
| ----------------------------------------------- | ------------------------------------------------ | ---------------------------------- |
| Internal sales notes, CRM records, agent briefs | One-liner                                        | Dense, unambiguous                 |
| Internal engineering / ops specs                | One-liner                                        | Scope-setting only                 |
| External briefing doc (pb2)                     | Expansion                                        | Calm register for reader           |
| External website page (pb1)                     | Expansion (often one sentence of it as headline) | Institutional posture              |
| External proposal / quote                       | Expansion                                        | Context before blocks and numbers  |
| Demo script preamble                            | Expansion (can be verbal)                        | Sets the frame before walk-through |

## Anti-patterns

- **Lifting the one-liner into the website.** Reads as internal shorthand. Expand.
- **Losing the mechanism in expansion.** The `same system Odum uses internally` claim is the differentiator across all
  three. Don't write expansions that omit it — that's the axis.to / podlabs.xyz posture (rule 02) and the rule-03
  same-system principle, both in one phrase.
- **Mixing two services in one expansion.** Each service gets its own paragraph. Don't write "DART or IM depending on
  what you want".
- **Treating the expansion as static marketing copy.** The expansion is the scope-setting paragraph; the longer brief
  (pb2) then does the heavy lifting. Don't over-invest in one paragraph and under-invest in the brief.

## Cross-service positioning

A prospect may be a candidate for more than one service. The positioning rule is:

1. **Start with the one-liner that matches their stated intent.** "Allocator looking for systematic exposure" → IM.
   "Fund operating its own strategy looking for execution cover" → DART signals-only or full. "Firm wanting to run
   regulated activity without FCA application" → Reg Umbrella.
2. **Mention the others briefly if the prospect is ambiguous.** A new hedge fund launching may need Reg Umbrella + DART;
   an allocator may pair IM with Reg Umbrella for their own structure. Mention the combination; don't pitch all three in
   one sentence.
3. **Route to rule 04's axis resolution for DART ambiguity.** If the DART one-liner fits but it's unclear whether
   they're signals-only or full, resolve via rule 04 before expanding.

## Enforcement rules

1. **One-liners are verbatim.** Don't rephrase them per doc. The wording above is canonical.
2. **Expansions follow the three-sentence pattern.** Position / differentiator / proof point. Don't sprawl.
3. **External docs never lift the one-liner unchanged.** They expand. Grep for exact one-liner matches in external docs
   as part of ship audit; zero matches required.
4. **Rule-02 voice applies to every expansion.** Read aloud. Anti-AI-tone guardrails.
5. **Cross-service positioning is explicit.** When pitching two services together, the doc names both services and their
   junction — not one service with the other as a footnote.

## Stage 2 implications

Stage 2's `commercial-model/dart-entry-points.md`, `commercial-model/im-entry-points.md`, and
`commercial-model/reg-umbrella-entry-points.md` each open with a rule-09 expansion paragraph. Website copy, briefing
intros, and proposal-template boilerplate all derive from these.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On internal commercial one-liners (rule 09)"
- [`02-tone-and-posture.md`](02-tone-and-posture.md) — voice expansions must match
- [`03-same-system-principle.md`](03-same-system-principle.md) — the mechanism behind all three one-liners
- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — DART one-liner resolves to a specific path per prospect
- [`../glossary.md`](../glossary.md) — canonical one-sentence definitions (related but narrower scope)
