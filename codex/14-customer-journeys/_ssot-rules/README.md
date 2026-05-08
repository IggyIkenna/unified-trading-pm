---
scope: [engineer, admin, sales]
---

# `_ssot-rules/` — Rules governing every experience doc

Every doc under [`../experience/`](../experience/) answers to these rules. The impl-layer docs under
[`../playbooks/`](../playbooks/) and related engineering-grade dirs do not — they continue to operate at their
engineering register and cross-reference here when commercial or audience-facing decisions apply.

## Why this dir exists

The playbook SSOT went through a v1 review (2026-04-19). The conclusion: the existing docs describe the platform
correctly but in the wrong register for sales, product, and leadership. The fix was a layered structure — an
**experience layer** (narrative, sales-owned) sitting on top of the **impl layer** (engineering-grade). This dir holds
the rules that govern the experience layer.

Rules are citable, stable, and orthogonal. Each rule has its own file. Experience docs cite rules by number.

## The ten rules

| #   | Rule                                                                                   | One-line summary                                                                         |
| --- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 01  | [grammar](01-grammar.md)                                                               | Every experience playbook has these nine sections in this order                          |
| 02  | [tone and posture](02-tone-and-posture.md)                                             | Calm, specific, credible, non-desperate — axis.to / podlabs.xyz benchmarks               |
| 03  | [same-system principle](03-same-system-principle.md)                                   | One operating system, partitioned views. Research ≡ live infra. Phase ⊥ maturity         |
| 04  | [DART commercial axes](04-dart-commercial-axes.md)                                     | Two axes (strategy origin × stack depth), three practical paths                          |
| 05  | [building-block dimensions](05-building-block-dimensions.md)                           | Thirteen blocks; pricing, demos, and entitlements all compose from them                  |
| 06  | [show / don't-show discipline](06-show-dont-show-discipline.md)                        | Walkthrough and what-not-to-show are paired; LOCKED-VISIBLE vs HIDDEN-ENTIRELY           |
| 07  | [data licensing boundaries](07-data-licensing-boundaries.md)                           | Enriched services, not raw-data resale                                                   |
| 08  | [pricing principles](08-pricing-principles.md)                                         | Two external tiers, per-block mixable, twelve-month minimum, internal cost codex-private |
| 09  | [internal commercial one-liners](09-internal-commercial-oneliners.md)                  | DART / IM / Reg Umbrella — internal shorthand, expanded externally                       |
| 10  | [strategy instruction schema principles](10-strategy-instruction-schema-principles.md) | Signals-only fit-check: what Odum needs, what it doesn't, package boundary               |

## Reading order

First-time reader:

1. `01-grammar.md`, `02-tone-and-posture.md` — how experience docs are written.
2. `03-same-system-principle.md` — the product architecture claim that underpins audience framing.
3. `04-dart-commercial-axes.md` → `10-strategy-instruction-schema-principles.md` — DART commercial logic end-to-end.
4. `05-building-block-dimensions.md` + `08-pricing-principles.md` — atomic unit + pricing structure.
5. `06-show-dont-show-discipline.md` + `07-data-licensing-boundaries.md` — what to leave off the page.
6. `09-internal-commercial-oneliners.md` — the internal shorthand that every external expansion derives from.

Reviewing an experience doc: skim `01`, `02`, `06`, then check it cites whichever of `03`–`10` its content depends on.

`_source-v1-feedback.md` is a frozen **archive** of the original v1 synthesis. Rules 01–11 now carry every load-bearing
claim. Cite the numbered rule files, never the archive.

## How to cite a rule

Experience docs reference rules by number and path:

> See [rule 03 (same-system principle)](../_ssot-rules/03-same-system-principle.md).

Impl-layer docs that touch commercial decisions (e.g. demo scripts) cite the same way. Sub-agents executing Stage 2 and
Stage 3 must read the rules first; the plan's mandatory-read-set enforces this.

## Relationship to other layers

```
codex/14-customer-journeys/
├── _ssot-rules/       (this dir — the rules)
├── experience/        (narrative playbooks; every doc obeys rules 01–10)
├── playbooks/         (IMPL LAYER — engineering click-paths; cite rules when making commercial decisions)
├── authentication/    (IMPL LAYER)
├── environments/      (IMPL LAYER)
├── cross-cutting/     (IMPL LAYER)
├── page-triage/       (pre-existing — 177-page classification)
├── testing/           (pre-existing — Playwright coverage)
└── roadmap/           (pre-existing — follow-up waves)
```

Experience docs are sales-owned. Impl docs are engineering-owned. Rules are owned collectively — changes require review
from both sides.

## Pre-drafted files (do not overwrite)

Three rule files were pre-committed by the master planner (commit `bd958e50`, 2026-04-19):

- `03-same-system-principle.md`
- `04-dart-commercial-axes.md`
- `08-pricing-principles.md`

Future edits require the same master-planner discipline. Inconsistencies surface as review comments, not silent edits.
`_source-v1-feedback.md` is an archive (see Reading order above) — no edits beyond archive-marker hygiene.

## Stage boundaries

This rules dir is complete after Stage 1 of the playbook SSOT restructure. Stage 2 applies the rules to rewrite the
other experience playbooks and create commercial-model / demo-ops / shared-core / implementation-mapping sub-dirs. Stage
3 specs the infra (UAC combo registry + derivation engine) that implements the rules at runtime.

- Stage 1 plan:
  [`plans/ai/playbook_ssot_stage_1_rules_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_1_rules_2026_04_19.plan.md)
- Stage 2 plan:
  [`plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
- Stage 3 plan:
  [`plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)
