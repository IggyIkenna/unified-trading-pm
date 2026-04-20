# 14-playbooks — Customer Playbook SSOT

Single source of truth for how every class of Odum user (marketing prospect → post-first-call warm prospect →
demo-account prospect → real paying client → Odum-internal admin) traverses the platform across its three environments
and three authentication tiers.

This directory is the **master IA doc**. If a plan, UI change, or marketing asset doesn't trace back to a playbook in
this directory, it's either missing context or out of scope.

## Layered structure

Two layers plus a rules set, co-located in this dir:

- **[`_ssot-rules/`](_ssot-rules/)** — the ten rules governing every experience doc (grammar, tone, same-system
  principle, DART commercial axes, building blocks, show / don't-show, data licensing, pricing, internal one-liners,
  instruction schema). Citable, stable, orthogonal. Stage 1 output (2026-04-19).
- **[`experience/`](experience/)** — narrative playbooks, sales-owned. One doc per (audience × moment) cell; nine
  sections per doc ([rule 01](_ssot-rules/01-grammar.md)). Calm institutional tone
  ([rule 02](_ssot-rules/02-tone-and-posture.md)). Canonical reference:
  [`experience/im-decision-journey.md`](experience/im-decision-journey.md).
- **[`playbooks/`](playbooks/)** and the other engineering-grade sub-dirs (`authentication/`, `environments/`,
  `cross-cutting/`, `page-triage/`, `testing/`, `roadmap/`) — the **impl layer**. Engineering-owned; routes,
  entitlements, services, data bindings, Playwright specs. Describes the same journeys at a different register.

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

- [catalogues.md](cross-cutting/catalogues.md) — umbrella over the 4 catalogues (Data, Strategy, ML Model, Execution
  Algo)
- [visibility-slicing.md](cross-cutting/visibility-slicing.md) — admin-sees-all / demo-sliced / prod-sliced model
- [client-reporting.md](cross-cutting/client-reporting.md) — the ONE reporting surface used by both IM and Reg Umbrella
- [fund-org-hierarchy.md](cross-cutting/fund-org-hierarchy.md) — org → Pooled/SMA → funds → clients
- [sma-vs-pooled.md](cross-cutting/sma-vs-pooled.md) — the structural decision point
- [investor-relations.md](cross-cutting/investor-relations.md) — board/plan/IM/platform/regulatory presentations
- [bloomberg-style-aesthetic.md](cross-cutting/bloomberg-style-aesthetic.md) — UX principles

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
- Local dev (transcluded): [../08-workflows/local-dev.md](../08-workflows/local-dev.md)
- Strategy architecture (referenced by DART playbook):
  [../09-strategy/architecture-v2/README.md](../09-strategy/architecture-v2/README.md)
- Compliance (referenced by Regulatory Umbrella playbook): [../07-security/compliance.md](../07-security/compliance.md)
