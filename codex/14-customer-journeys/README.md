---
scope: [engineer, admin, sales]
---

# 14-playbooks — Customer Playbook SSOT

Single source of truth for how every class of Odum user (marketing prospect → post-first-call warm prospect →
demo-account prospect → real paying client → Odum-internal admin) traverses the platform across its three environments
and three authentication tiers.

This directory is the **master IA doc**. If a plan, UI change, or marketing asset doesn't trace back to a playbook in
this directory, it's either missing context or out of scope.

## Layered structure

The playbook SSOT is organised in three logical layers under one directory:

- **Rules layer — [`_ssot-rules/`](_ssot-rules/)**: the ten rules governing every experience doc (grammar, tone,
  same-system principle, DART commercial axes, building blocks, show / don't-show, data licensing, pricing, internal
  one-liners, instruction schema). Citable, stable, orthogonal. Stage 1 output (2026-04-19).
- **Playbook layer** (Stage 2): narrative + commercial + operational docs:
  - **[`experience/`](experience/)** — narrative playbooks, sales-owned. Nine sections per doc
    ([rule 01](_ssot-rules/01-grammar.md)). Canonical reference:
    [`experience/im-decision-journey.md`](experience/im-decision-journey.md).
  - **[`shared-core/`](shared-core/)** — product truths reused across layers. Implementation maps for rules 03, 04, 05,
    07, 10; shared reporting core; org/fund/client entity model; shared pb3a+pb3b walkthrough.
  - **[`commercial-model/`](commercial-model/)** — blocks → packages → tiers. Three DART entry points; IM vs Reg
    Umbrella pricing logic; pricing structure (TBD stubs).
  - **[`demo-ops/`](demo-ops/)** — demo config (restriction profiles, demo modes, upsell overlays, curation) + sales ops
    (account-intelligence record, discovery framework, decision matrix, meeting tracking) + orchestration (seven-day
    stall trigger, post-demo follow-up).
  - **[`implementation-mapping/`](implementation-mapping/)** — bridge narrative → code. Route mapping, persona fixtures,
    provisioning flow, Playwright coverage.
- **Impl layer — [`playbooks/`](playbooks/)** and the other engineering sub-dirs (`authentication/`, `environments/`,
  `cross-cutting/`, `page-triage/`, `testing/`, `roadmap/`). Engineering-owned; routes, entitlements, services, data
  bindings, Playwright specs. Describes the same journeys at a different register.
- **Infra spec — [`infra-spec/`](infra-spec/)** (Stage 3): current-state audit (3A), UAC combo rules + YAML schema +
  instruction-schema contract + downstream-analytics capability matrix (3B), derivation engine with 4 formulas (3C),
  refactor plan with 26 G1/G2/G3 items (3E) — makes the rules + playbook-layer claims runtime-enforceable.
- **Target-experience presentations — [`presentations/`](presentations/)** (Stage 3D): 16-slide markdown deck with
  mermaid diagrams + 7 Playwright screenshots showing the post-refactor target state. Internal alignment +
  investor-briefing-ready.

Reader paths by role:

| Role                         | Read first                                                                                           | Then                                                                  |
| ---------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Sales / commercial / product | [`experience/`](experience/)                                                                         | [`_ssot-rules/`](_ssot-rules/) as content is invoked                  |
| Leadership                   | [`experience/`](experience/)                                                                         | [`_ssot-rules/`](_ssot-rules/)                                        |
| Engineering                  | [`playbooks/`](playbooks/) + [`cross-cutting/`](cross-cutting/)                                      | [`_ssot-rules/`](_ssot-rules/) when commercial decisions are in scope |
| Admin / ops                  | [`playbooks/`](playbooks/) + [`authentication/`](authentication/) + [`environments/`](environments/) | All                                                                   |

Experience docs and impl-layer docs are paired and cross-reference each other. Commercial content lives in the rules
dir, never inlined into impl-layer docs; impl-layer docs cite the rules. This keeps commercial policy in one place while
the engineering surface stays operational.

## What lives here

- [glossary.md](glossary.md) — DART, IM, SMA, Pooled, Briefings, Umbrella, Demo account — one canonical definition per
  term
- [information-architecture.md](information-architecture.md) — top-down IA: homepage → signed-in services → per-service
  sub-surfaces
- [audiences-and-journeys.md](audiences-and-journeys.md) — 3 playbook families × N personas × 3 environments matrix

### [shared-core/](shared-core/) (Stage 2)

Product truths reused across experience and commercial docs. Implementation maps for rules 03, 04, 05, 07, 10. Eight
content docs + README:

- [same-system-principle.md](shared-core/same-system-principle.md) — rule 03 implementation
- [org-fund-client-entity-model.md](shared-core/org-fund-client-entity-model.md) — entity hierarchy
- [shared-reporting-core.md](shared-core/shared-reporting-core.md) — one reporting surface, 3 audiences
- [strategy-origin-vs-stack-depth.md](shared-core/strategy-origin-vs-stack-depth.md) — rule 04 matrix
- [venue-chain-instrument-scope.md](shared-core/venue-chain-instrument-scope.md) — rule 05 sub-scoping
- [instruction-schema-fit-and-package-boundaries.md](shared-core/instruction-schema-fit-and-package-boundaries.md) —
  rule 10
- [data-licensing-boundaries.md](shared-core/data-licensing-boundaries.md) — rule 07 expanded
- [client-reporting-demo-walkthrough.md](shared-core/client-reporting-demo-walkthrough.md) — shared pb3a+pb3b path

### [commercial-model/](commercial-model/) (Stage 2)

Blocks → packages → tiers. Six content docs + README:

- [dart-entry-points.md](commercial-model/dart-entry-points.md) — 3 practical DART paths
- [im-vs-reg-reporting-logic.md](commercial-model/im-vs-reg-reporting-logic.md) — same UI, two framings
- [building-block-packaging.md](commercial-model/building-block-packaging.md) — 13 × 6 matrix
- [pricing-building-blocks.md](commercial-model/pricing-building-blocks.md) — 3 cols × 13 rows (TBD)
- [fixed-vs-variable-commercials.md](commercial-model/fixed-vs-variable-commercials.md) — Tier A vs Tier B
- [exclusivity-and-noncompete.md](commercial-model/exclusivity-and-noncompete.md) — Tier B modifier

### [demo-ops/](demo-ops/) (Stage 2)

Demo config + sales ops + post-demo orchestration. Nine content docs + README:

- [demo-restriction-profiles.md](demo-ops/demo-restriction-profiles.md)
- [dart-demo-modes.md](demo-ops/dart-demo-modes.md)
- [upsell-overlays.md](demo-ops/upsell-overlays.md)
- [pre-demo-curation-rules.md](demo-ops/pre-demo-curation-rules.md)
- [account-intelligence-record.md](demo-ops/account-intelligence-record.md)
- [pre-demo-discovery-framework.md](demo-ops/pre-demo-discovery-framework.md)
- [demo-decision-matrix.md](demo-ops/demo-decision-matrix.md)
- [meeting-history-and-interest-tracking.md](demo-ops/meeting-history-and-interest-tracking.md)
- [post-demo-followup-orchestration.md](demo-ops/post-demo-followup-orchestration.md)

### [implementation-mapping/](implementation-mapping/) (Stage 2)

Narrative → code bridge. Four content docs + README:

- [route-mapping.md](implementation-mapping/route-mapping.md)
- [persona-and-user-prototype-mapping.md](implementation-mapping/persona-and-user-prototype-mapping.md)
- [demo-email-and-provisioning-flow.md](implementation-mapping/demo-email-and-provisioning-flow.md)
- [playbook-to-qa-coverage.md](implementation-mapping/playbook-to-qa-coverage.md)

### [authentication/](authentication/)

Three-tier auth: light briefings gate · Firebase staging · Firebase production.

### [environments/](environments/)

Three environments: localhost · `odum-research.co.uk` (staging) · `odum-research.com` (production).

### [playbooks/](playbooks/)

Three families:

1. **Pre-first-call marketing** ([01-marketing-pre-first-call.md](playbooks/01-marketing-pre-first-call.md))
2. **Post-first-call research & documentation** — hub
   ([02-research-and-documentation.md](playbooks/02-research-and-documentation.md)) + three sub-areas (IM, DART,
   Regulatory Umbrella)
3. **Warm-prospect demo on staging** — hub ([03-warm-prospect-demo.md](playbooks/03-warm-prospect-demo.md)) + three
   sub-flavours (Reg Umbrella, IM, DART)

### [cross-cutting/](cross-cutting/)

Concepts that appear in multiple playbooks:

- [catalogues.md](playbook-concepts/catalogues.md) — umbrella over the 4 catalogues (Data, Strategy, ML Model, Execution
  Algo)
- [visibility-slicing.md](playbook-concepts/visibility-slicing.md) — admin-sees-all / demo-sliced / prod-sliced model
- [client-reporting.md](playbook-concepts/client-reporting.md) — the ONE reporting surface used by both IM and Reg
  Umbrella
- [fund-org-hierarchy.md](playbook-concepts/fund-org-hierarchy.md) — org → Pooled/SMA → funds → clients
- [sma-vs-pooled.md](playbook-concepts/sma-vs-pooled.md) — the structural decision point
- [investor-relations.md](playbook-concepts/investor-relations.md) — board/plan/IM/platform/regulatory presentations
- [bloomberg-style-aesthetic.md](playbook-concepts/bloomberg-style-aesthetic.md) — UX principles

### [page-triage/](page-triage/)

Classification of every existing `.tsx` page in unified-trading-system-ui and user-management-ui against the playbook
spec:

- [triage-matrix.md](page-triage/triage-matrix.md) — master table (177 routes × action)
- [broken-links.md](page-triage/broken-links.md) — confirmed + probable broken outbound hrefs
- [duplicate-clusters.md](page-triage/duplicate-clusters.md) — 10 overlap clusters + merge decisions
- [partial-archive.md](page-triage/partial-archive.md) — pages where only some tabs promote forward

### [testing/](testing/)

Every playbook ships with a Playwright e2e test that walks the canonical click path:

- [test-matrix.md](testing/test-matrix.md) — playbook × persona × environment → test file
- [example-playbook-test.md](testing/example-playbook-test.md) — reference test

### [roadmap/](roadmap/)

What comes after this SSOT lands. Each follow-up plan is referenced here so the end-to-end picture is never lost:

- [next-waves.md](roadmap/next-waves.md) — 5-8 follow-up plans (demo-account flows, org/fund/client RBAC, DART rebrand,
  per-catalogue SSOTs, staging Firebase, visibility-slicing impl)
- [plan-references.md](roadmap/plan-references.md) — map each future plan to its current reference (memory / existing
  plan / needs-new-plan)

## The reuse-first philosophy

Odum has 177 UI pages already. Before writing a new page, component, or service — **look for an existing one**. The
triage matrix in [page-triage/triage-matrix.md](page-triage/triage-matrix.md) classifies every page as
`promote / refactor / merge-into / partial-archive / deprecate / defer`. Most orphans are promote-or-refactor
candidates, not delete candidates. An `archive` decision is the big one and requires explicit confirmation.

## How to add a new playbook

1. Draft the new playbook doc under [playbooks/](playbooks/) using an existing one as template.
2. Add the canonical click path step-by-step with route references.
3. Write a Playwright spec under `unified-trading-system-ui/tests/playbooks/` that asserts the path.
4. Update [testing/test-matrix.md](testing/test-matrix.md).
5. Update [audiences-and-journeys.md](audiences-and-journeys.md).
6. Reference the playbook from [roadmap/next-waves.md](roadmap/next-waves.md) if it requires follow-up implementation.

## How to update an existing playbook

When a playbook doc changes, the matching Playwright spec MUST be updated in the same PR. CI enforces this.

## Links out

- Codex top-level: [../README.md](../README.md)
- Master index: [../00-SSOT-INDEX.md](../00-SSOT-INDEX.md)
- Local dev (transcluded): [/codex/08-workflows/local-dev.md](/codex/08-workflows/local-dev.md)
- Strategy architecture (referenced by DART playbook):
  [/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md)
- Compliance (referenced by Regulatory Umbrella playbook):
  [/codex/07-security/compliance.md](/codex/07-security/compliance.md)
