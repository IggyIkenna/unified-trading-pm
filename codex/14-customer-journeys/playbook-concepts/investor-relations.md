---
doc_type: codex-ssot
title: Investor Relations
summary:
  The /investor-relations/* section serves Odum's investors, advisors and board (NOT client prospects) — a distinct
  audience from the pb1/pb2/pb3 playbooks; personas investor/advisor/admin, per-deck entitlements, and partial-archive
  rules promoting redacted slides into pb2 briefings.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [investor-relations, ui, persona, entitlements, briefings, page-triage]
related:
  [
    ../authentication/README.md,
    ../playbooks/02-research-and-documentation.md,
    ../page-triage/triage-matrix.md,
    ../page-triage/partial-archive.md,
  ]
created: 2026-04-19
authoritative_for: [investor-relations UI section (audience separation from playbooks)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/page-triage/partial-archive.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/shared-core/shared-reporting-core.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Investor Relations

A separate section of the platform (`/investor-relations/*`) for Odum **investors and advisors** — NOT for prospects.
These are fundraising and board-level materials for people invested in Odum the firm.

## Distinction from playbooks

- **Playbooks** (pb1/pb2/pb3) = prospects becoming clients (allocating capital TO Odum strategies, or using Odum
  platform)
- **Investor Relations** = investors in Odum itself (Odum's equity holders, board members, strategic advisors)

Don't mix these audiences. IR content does NOT promote clients; client demos do NOT show IR content.

## Route tree

- `/investor-relations` — landing
- `/investor-relations/board-presentation` — board deck
- `/investor-relations/plan-presentation` — plan deck
- `/investor-relations/investment-presentation` — IM business presentation
- `/investor-relations/platform-presentation` — DART/platform business presentation
- `/investor-relations/regulatory-presentation` — regulatory business presentation
- `/investor-relations/disaster-recovery` — BCP / DR briefing
- `/investor-relations/site-navigation` — orphan / redundant with `/investor-relations` landing

## Personas with access

Per [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts):

- `investor` — sees all IR pages
- `advisor` — sees board + plan only (restricted)
- `admin` — sees everything

Entitlements: `investor-relations`, `investor-board`, `investor-plan`, `investor-im`, `investor-platform`,
`investor-regulatory`, `investor-archive`.

## Promotion candidates per playbook

Some IR presentations contain content that's also useful (in redacted form) for client prospects:

| IR presentation           | Playbook reuse candidate            | Action                                                                                    |
| ------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------- |
| `investment-presentation` | pb2a (IM briefing) — partial slides | `partial-archive`: promote content blocks into briefings, keep full deck as investor-only |
| `platform-presentation`   | pb2b (DART briefing)                | Same                                                                                      |
| `regulatory-presentation` | pb2c (Reg Umbrella briefing)        | Same                                                                                      |
| `disaster-recovery`       | pb2c (Reg Umbrella)                 | Same — DR matters for umbrella clients                                                    |
| `board-presentation`      | Investor-only                       | `promote` unchanged; not a client briefing                                                |
| `plan-presentation`       | Investor-only                       | Same                                                                                      |
| `site-navigation`         | None                                | `merge-into:/investor-relations` landing — redundant                                      |

Decisions finalised in [../page-triage/triage-matrix.md](../page-triage/triage-matrix.md).

## Visibility slicing

IR is gated by `investor-relations` entitlement + sub-entitlements. Advisors see less than board members. See
[visibility-slicing.md](visibility-slicing.md).

## Content source

Today: each presentation is a React component tree with slides. Heavy per-presentation code.

Long-term consideration: move slide content to markdown + render via a shared presentation shell. Tracked in
[../roadmap/next-waves.md](../roadmap/next-waves.md).

## Related

- Personas: [../authentication/README.md](../authentication/README.md)
- Playbook pb2 briefings that surface partial IR content:
  [../playbooks/02-research-and-documentation.md](../playbooks/02-research-and-documentation.md)
- Triage decisions: [../page-triage/triage-matrix.md](../page-triage/triage-matrix.md)
