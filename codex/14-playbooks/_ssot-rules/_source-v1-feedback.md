# Source: v1 agent feedback on the playbook SSOT (2026-04-19)

This file captures the structural decisions from the "Client Experience Playbooks — Polished v1" feedback session, with
additions from the 2026-04-19 research↔live unification directive. It is the stable citation target for every
`_ssot-rules/*.md` file.

The full prose version of v1 (tone commentary, per-playbook narrative drafts, Axis/POD benchmarks, and the agent's
structural critique) was provided in the 2026-04-19 conversation. The Stage 1 agent executing
`plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md` Phase 1.0 should append the full verbatim text below the
**`## Full v1 prose (appendix)`** marker at the end of this file.

## Key structural claims (authoritative summary)

### On tone + posture

- Calm, specific, credible, lightly guided, never desperate.
- Restrained institutional posture. Benchmarks: [axis.to](https://www.axis.to/) and [podlabs.xyz](https://podlabs.xyz/).
- What to borrow from those benchmarks: restrained headlines; a few concrete proof points; clear explanation of how the
  operating model works; sparse navigation; low-drama trust markers.
- What **not** to borrow: waitlist-first posture, unfinished-page energy, retail-facing vocabulary, forward-tense
  language that implies the product isn't live today.
- Explicit anti-goal: do not sound AI-generated. Written by people who have run trading businesses.

### On document grammar (rule 01)

Every experience playbook has these 9 sections, in order:

1. Audience
2. Moment in journey
3. What Odum must prove
4. Experience goal
5. Walkthrough
6. Key messages
7. What not to show
8. Desired next step
9. Internal handoff

### On the same-system principle (rule 03)

Five sub-claims, locked 2026-04-19:

- **(a)** DART, IM, and Regulatory Umbrella client surfaces are **partitioned views of the same internal Odum operating
  system**, not three separate products.
- **(b)** **Research infrastructure ≡ live infrastructure.** Any metric generated during research is generated in live
  trading via the same underlying component.
- **(c)** The trading terminal is a **live/batch toggle over the same component tree.** Same numbers, same tables, same
  charts — the data source binds differently.
- **(d)** The strategy catalogue carries **phase tags** (research / paper / live) on a single row; the UI does not fork
  into separate catalogue products per phase.
- **(e)** Paper trading has the **same look and feel** as live. Paper is not a separate product.

**Phase (research/paper/live) is orthogonal to maturity (CODE_NOT_WRITTEN → LIVE_ALLOCATED).** A `LIVE_ALLOCATED` slot
can still be viewed in research phase when a researcher re-runs it over historical data. Phase is an execution-context
dimension; maturity is a promotion-stage dimension.

### On DART commercial model (rule 04)

**Two axes:**

- **Strategy origin** — Odum strategy vs client strategy
- **Stack depth** — reporting-only visibility / client-strategy+downstream-integration / full-DART-pipeline

**Three practical commercial paths** collapse out of those axes:

1. Reporting-only visibility — closer to reporting or regulatory visibility than true DART.
2. Client strategy + downstream integration — client keeps strategy generation outside Odum, sends instructions in, uses
   execution / trading / selected analytics / monitoring.
3. Full DART pipeline — client buys into enriched data services, research, backtesting, promotion, execution, trading,
   observation.

If a client wants Odum strategy exposure inside DART, they sit in path 3, not path 1 or 2.

### On data licensing boundary (rule 07)

DART is sold as **enriched platform and research services built on top of underlying data sources**, subject to
licensing and commercial constraints. DART is **not** a direct raw-data resale product.

Internal pricing can use data-sensitive building blocks; external positioning always frames the product as enriched
services.

### On building-block dimensions (rule 05)

Thirteen internal building blocks:

1. Reporting core
2. Regulatory umbrella reporting
3. IM allocator reporting
4. Strategy-service entry
5. Instructions integration
6. Research / promote pipeline
7. Execution layer
8. Venue packs (per venue or venue group)
9. Chain packs (per chain)
10. Instrument-type packs (per type: options / perps / futures / spot / sports-fixture / prediction-market / ...)
11. Analytics packs
12. Exclusivity / non-compete premium
13. Custom solution premium

These dimensions drive: (a) client-facing packaging in Stage 2's `commercial-model/pricing-building-blocks.md`, (b)
demo-restriction-profile construction in Stage 2's `demo-ops/`, (c) UAC combo rules in Stage 3B, (d) the
one-registry-four-derivations engine in Stage 3C.

### On pricing (rule 08)

Two external tiers:

- **Tier A — cost-plus.** Variable cost pass-through with a thin margin. Low barrier. No upfront. Per-block; client can
  buy some blocks on Tier A.
- **Tier B — fixed.** Upfront plus fixed monthly. Predictable. Unlocks exclusivity and custom premiums.

Twelve-month minimum commitment on both tiers. Internal cost column is codex-private — never appears in any
client-facing document. Clients can mix tiers per block (Tier A on marginal venues + Tier B on core reporting, for
example). Exclusivity and custom solution premiums are Tier B only.

Numbers are populated by Odum finance in Stage 2 outputs; this rule file is principles-only.

### On internal commercial one-liners (rule 09)

User voice, 2026-04-19:

- **DART** — "an accelerator for strategy, research, execution, and control — the same system Odum uses internally."
- **IM** — "allocate capital to Odum-managed strategies; reporting is built in because it is the same reporting system
  Odum uses itself."
- **Reg Umbrella** — "operate your regulated activity under Odum's FCA permissions; onboarding, compliance, MLRO,
  supervision, and reporting included."

These are internal sales shorthand. Every public-facing doc expands each into a calm, institutional paragraph using the
rule 02 tone; internal docs can use them directly.

### On the layered directory structure

```
codex/14-playbooks/
├── _ssot-rules/       (rules governing every experience doc — this dir)
├── experience/        (narrative playbooks, sales-owned)
├── shared-core/       (product truths reused across layers)
├── commercial-model/  (packaging, tiers, pricing — structure only; numbers from finance)
├── demo-ops/          (demo controls + sales ops — consolidated)
├── implementation-mapping/  (routes, personas, QA coverage)
├── playbooks/         (IMPL LAYER — engineering-grade, pre-existing)
├── authentication/    (IMPL LAYER)
├── environments/      (IMPL LAYER)
├── cross-cutting/     (IMPL LAYER)
├── page-triage/       (pre-existing — 177-page classification)
├── testing/           (pre-existing — Playwright coverage)
├── roadmap/           (superseded by infra-spec/stage-3e-refactor-plan.md on Stage 3 merge)
├── infra-spec/        (Stage 3 outputs — audit, combo rules, derivation engine, refactor plan)
└── presentations/     (Stage 3D target-experience slide deck with mermaid + screenshots)
```

### On demo mode vs commercial path vs production restriction

Three independent axes. Stage 3 specs the infra that lets all three derive from the same UAC combo registry:

- **Demo mode** — broader platform OR turbo; chosen per prospect, configurable toggle for comparison.
- **Commercial path** — reporting-only visibility / client-strategy+downstream / full-pipeline (DART); or IM /
  Reg-Umbrella path.
- **Production restriction** — what the paying client actually gets gated to.

### On sales ops orchestration

Every prospect generates an **account-intelligence record** (not just a lead tag) covering: organisation, service
interests, markets, commercial path, call notes, objections, inferred gaps, next-meeting hypothesis. Each demo session
appends back so later calls are cumulative. Stage 2 `demo-ops/` specifies structure; Stage 3E refactor plan specs the
CRM implementation.

Explicit orchestration rules: 7-day stall trigger, post-step follow-up asset per stage, qualification criteria per stage
transition.

## Full v1 prose (appendix)

> **Stage 1 agent Phase 1.0:** paste the full verbatim v1 text from the 2026-04-19 conversation below this line. The
> structural summary above is authoritative; the appendix preserves tone + narrative drafts + the agent's commentary for
> citations.

_(to be filled by Stage 1 agent; if unavailable at execution time, request from user before proceeding)_
