---
scope: [engineer, admin, sales]
---

# `cross-cutting/` — Concepts that span multiple playbooks

> **Layer:** Implementation. Narrative lives in [../experience/](../experience/).

Engineering-grade docs on concepts that appear in more than one playbook: catalogues, visibility slicing, client
reporting, fund / org hierarchy, SMA vs Pooled, investor relations, Bloomberg-style aesthetic.

## Contents

| File                                                         | Concept                                                                   |
| ------------------------------------------------------------ | ------------------------------------------------------------------------- |
| [catalogues.md](catalogues.md)                               | Umbrella over the 4 catalogues (Data, Strategy, ML Model, Execution Algo) |
| [catalogue-data.md](catalogue-data.md)                       | Data catalogue                                                            |
| [catalogue-strategy.md](catalogue-strategy.md)               | Strategy catalogue                                                        |
| [catalogue-ml-model.md](catalogue-ml-model.md)               | ML model catalogue                                                        |
| [catalogue-execution-algo.md](catalogue-execution-algo.md)   | Execution-algo catalogue                                                  |
| [visibility-slicing.md](visibility-slicing.md)               | Admin-sees-all / demo-sliced / prod-sliced model                          |
| [client-reporting.md](client-reporting.md)                   | The ONE reporting surface used by IM and Reg Umbrella                     |
| [fund-org-hierarchy.md](fund-org-hierarchy.md)               | org → Pooled/SMA → funds → clients                                        |
| [sma-vs-pooled.md](sma-vs-pooled.md)                         | Structural decision point                                                 |
| [investor-relations.md](investor-relations.md)               | Board / plan / IM / platform / regulatory presentations                   |
| [bloomberg-style-aesthetic.md](bloomberg-style-aesthetic.md) | UX principles                                                             |

## Relationship to `../experience/`

Experience playbooks cite these docs when the concept is invoked. For example:
[`../experience/im-decision-journey.md`](../experience/im-decision-journey.md) cites
[sma-vs-pooled.md](sma-vs-pooled.md);
[`../experience/investment-management-demo.md`](../experience/investment-management-demo.md) cites
[client-reporting.md](client-reporting.md).

Experience layer is narrative. This cross-cutting layer is engineering. Both are authoritative in their register;
experience docs describe what the audience experiences, cross-cutting docs describe the engineering-surface
implementation.

## Relationship to `../shared-core/`

`shared-core/` is a playbook-layer re-framing of some cross-cutting concepts for the commercial and experience layer.
For example, [`../shared-core/shared-reporting-core.md`](../shared-core/shared-reporting-core.md) re-frames
[client-reporting.md](client-reporting.md);
[`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md) re-frames
[fund-org-hierarchy.md](fund-org-hierarchy.md) + [sma-vs-pooled.md](sma-vs-pooled.md).

Split logic: engineering content stays in `cross-cutting/`; experience / commercial framing is in `shared-core/`. Both
are kept in sync; either can be the starting point.
