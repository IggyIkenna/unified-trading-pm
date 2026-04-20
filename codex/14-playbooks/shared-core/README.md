---
scope: [engineer, admin, sales]
---

# `shared-core/` — Product truths reused across layers

Shared concepts the experience playbooks and the Stage 3 infra spec both consume. Each doc cites the `_ssot-rules/` file
it derives from and expands into an implementation-adjacent reference. Nothing here is client-facing copy; experience
playbooks pull from here via link, demo-ops profiles read the same conceptual model, and Stage 3's derivation engine
uses the same identifiers.

## What belongs here

A doc belongs under `shared-core/` when it is:

1. **Re-used by two or more experience playbooks** — for example the client-reporting walkthrough used by both pb3a and
   pb3b.
2. **Implementation-map for a rule** — for example `instruction-schema-fit-and-package-boundaries.md` implementing rule
   10, or `same-system-principle.md` implementing rule 03's five sub-claims.
3. **Cross-audience concept** — for example the org / fund / client entity model used by IM, Reg Umbrella, and DART.

If a concept lives inside exactly one experience playbook and has no reuse potential, keep it in the playbook. If it
appears in three playbooks and in a demo profile, promote it here.

## Contents

| File                                                                                                 | Implements         | Primary consumers                                     |
| ---------------------------------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------- |
| [same-system-principle.md](same-system-principle.md)                                                 | rule 03            | all experience playbooks, Stage 3 3C derivation       |
| [org-fund-client-entity-model.md](org-fund-client-entity-model.md)                                   | rule 03 + existing | pb2a, pb3a, pb3b, Reg Umbrella; onboarding flow       |
| [shared-reporting-core.md](shared-reporting-core.md)                                                 | rule 03            | pb3a, pb3b, regulatory / IM commercial                |
| [strategy-origin-vs-stack-depth.md](strategy-origin-vs-stack-depth.md)                               | rule 04            | pb2b, pb3c, DART commercial model                     |
| [venue-chain-instrument-scope.md](venue-chain-instrument-scope.md)                                   | rule 05            | demo restriction profiles, pricing, Stage 3B registry |
| [instruction-schema-fit-and-package-boundaries.md](instruction-schema-fit-and-package-boundaries.md) | rule 10            | pb2b fit-check, pb3c demo gate, Stage 3B schema       |
| [data-licensing-boundaries.md](data-licensing-boundaries.md)                                         | rule 07            | pricing, marketing, demo data pipeline                |
| [client-reporting-demo-walkthrough.md](client-reporting-demo-walkthrough.md)                         | rule 03 + rule 06  | pb3a, pb3b shared demo click-path                     |

## Relationship to other dirs

- **[`../experience/`](../experience/)** — narrative playbooks reference shared-core via link. Experience docs do not
  duplicate the content here; they point.
- **[`../commercial-model/`](../commercial-model/)** — commercial docs cite shared-core where structural definitions are
  needed (for example the `strategy-origin-vs-stack-depth` matrix).
- **[`../demo-ops/`](../demo-ops/)** — restriction profiles reference shared-core identifiers (venue / chain /
  instrument-type scope, rule-10 schema depth).
- **[`../implementation-mapping/`](../implementation-mapping/)** — route and persona mappings trace to shared-core
  concepts for cross-consumer consistency.
- **[`../../09-strategy/architecture-v2/`](../../09-strategy/architecture-v2/)** — the strategy-architecture docs carry
  the upstream definitions; shared-core maps them into the playbook surface without re-authoring.

## Stage 3 relationship

Stage 3B's UAC combo registry and Stage 3C's derivation engine read identifiers declared here. The rule 10
package-boundary map becomes part of the Stage 3B schema contract; the same-system claim becomes a Stage 3E refactor
invariant; venue / chain / instrument-type scope becomes a Stage 3B registry dimension.

## Cross-references

- [`../_ssot-rules/`](../_ssot-rules/) — the ten rules this dir implements
- [`../experience/`](../experience/) — playbooks that consume shared-core
- [`../../00-SSOT-INDEX.md`](../../00-SSOT-INDEX.md)
