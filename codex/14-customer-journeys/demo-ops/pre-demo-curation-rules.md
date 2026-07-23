---
doc_type: codex-ssot
title: Pre-Demo Curation Rules
summary:
  Show/skim/skip curation of unlocked surfaces per prospect cell — sits between the mechanical restriction profile and
  the narrative session; per-cell curation tables (IM pb3b, Reg Umbrella pb3a, signals-only/full DART pb3c), curation
  principles (max 3 surfaces in a turbo demo, skip is not hidden), and the session-prep checklist.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, dart, curation, restriction-profile, session-prep]
related:
  [
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
  ]
created: 2026-04-20
authoritative_for: [pre-demo curation rules (show/skim/skip)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/staging-demo-setup.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Pre-Demo Curation Rules

> What to show / skip / skim per prospect profile. Sits between the restriction profile (mechanical) and the demo
> session (narrative).

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md),
[rule 06](../_ssot-rules/06-show-dont-show-discipline.md)

## What curation is

Curation is the sales person's choice of which unlocked surfaces to walk in a session. The restriction profile (see
[`demo-restriction-profiles.md`](demo-restriction-profiles.md)) defines the permissible surface set; curation picks from
that set based on the prospect's specific profile.

Curation is prioritisation, not exclusion. A surface labelled "skim" is still permissible; the sales person just spends
<1 minute on it.

## Three curation categories

- **Show.** Named in agenda; walked in depth.
- **Skim.** Surfaced briefly; held for prospect to ask.
- **Skip.** Not walked; available in nav if navigated.

## Curation per cell

### `(Odum, reporting-only)` → IM demo (pb3b)

| Surface                                   | Curation |
| ----------------------------------------- | -------- |
| Reporting landing                         | Show     |
| Positions + P&L                           | Show     |
| Reconciliation                            | Show     |
| Share-class NAV / fee accrual             | Show     |
| Investor statement path                   | Skim     |
| Audit trail                               | Skim     |
| Strategy catalogue (public + IM-reserved) | Show     |
| Execution-layer depth                     | Skip     |

### Reg Umbrella demo (pb3a)

| Surface                              | Curation |
| ------------------------------------ | -------- |
| Regulated-activity reporting landing | Show     |
| Transaction reporting                | Show     |
| Best-execution evidence              | Show     |
| Supervisory-artifact index           | Show     |
| Positions + P&L (reg-activity view)  | Skim     |
| Reconciliation                       | Skim     |
| Audit trail                          | Skim     |
| DART research / promote              | Skip     |

### Signals-only DART demo (pb3c)

| Surface                          | Curation |
| -------------------------------- | -------- |
| Catalogue (scope-filtered)       | Show     |
| Strategy-service entry           | Show     |
| Execution layer + reconciliation | Show     |
| TCA + execution-quality metrics  | Show     |
| Reporting surface                | Show     |
| Research / promote surfaces      | Skip     |
| Odum-run IM strategy detail      | Skip     |

### Full DART demo (pb3c)

| Surface                 | Curation |
| ----------------------- | -------- |
| Catalogue (all phases)  | Show     |
| Research surface        | Show     |
| Promote-pipeline ledger | Show     |
| Paper-trading view      | Show     |
| Strategy-service entry  | Show     |
| Execution layer         | Skim     |
| Reporting surface       | Skim     |
| Odum-strategy IP detail | Skip     |

### Combined Reg Umbrella + signals-only DART

Two sessions: pb3a reporting-focused, pb3c execution-focused. Do not combine; audience attention won't support it.

## Curation principles

- The prospect's intent drives curation. What pb2 briefing + second call resolved is the agenda target.
- Max three surfaces in a turbo demo. More dilutes.
- Skim surfaces are hold cards for depth questions.
- Skip ≠ hidden. Prospect can navigate there; the sales person doesn't walk there.
- Demo mode (see [`dart-demo-modes.md`](dart-demo-modes.md)) layers on top.
- Rule-02 calm posture applies. Don't rush through skim surfaces — either cut or walk properly.

## Session prep

1. Agenda: named list of Show surfaces + session goal.
2. Demo data: ensure synthetic data renders sensibly.
3. Hold cards: know Skim surfaces for depth questions.
4. The close: know the named next commitment.
5. Restriction-profile verify: sign in as demo user, test one path end-to-end.

## Cross-references

- [rule 04](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 06](../_ssot-rules/06-show-dont-show-discipline.md)
- [demo-restriction-profiles.md](demo-restriction-profiles.md)
- [dart-demo-modes.md](dart-demo-modes.md)
- [upsell-overlays.md](upsell-overlays.md)
- [account-intelligence-record.md](account-intelligence-record.md)
- [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md)
- [../experience/staging-demo-journey.md](../experience/staging-demo-journey.md)
