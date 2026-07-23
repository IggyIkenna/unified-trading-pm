---
doc_type: codex-ssot
title: Account Intelligence Record
summary:
  The per-prospect structured CRM record (12 fields + freeform) — commercial_path, service_interests, market_scope,
  dart_schema_fit, objections_raised, inferred_gaps, next_commitment, deviations_logged; created on pb1 booking, filled
  progressively across intro/pb2/demo/follow-up; feeds pre-demo curation and post-demo follow-up orchestration.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, crm, prospect, account-record, curation, follow-up]
related:
  [
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [account-intelligence record schema]
referenced_by:
  [
    /codex/08-workflows/client-onboarding.md,
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Account Intelligence Record

> The structured CRM record per prospect. Replaces "just a lead tag." Captures the commercial path, service interests,
> markets, call notes, objections, inferred gaps, and next-meeting hypothesis. Cited by every experience playbook's §9
> internal handoff.

**Rule source:** [rule 01](../_ssot-rules/01-grammar.md) §Cross-section consistency + §9 grammar, plus
[rule 09](../_ssot-rules/09-internal-commercial-oneliners.md) where one-liners anchor the record's service slots.

## Why this record

Every Odum prospect generates structured context across multiple touches: the pb1 website visit, the intro call, the pb2
briefing read, the second call, the demo, any follow-ups. Without a structured record, that context lives in inboxes,
memory, and ad-hoc notes. The account-intelligence record centralises it.

The record serves four purposes:

1. **Continuity across touches.** The next sales session reads the cumulative record, not a fresh guess.
2. **Curation inputs.** Pre-demo curation (see [`pre-demo-curation-rules.md`](pre-demo-curation-rules.md)) reads from
   the record.
3. **Follow-up orchestration.** Post-demo follow-up (see
   [`post-demo-followup-orchestration.md`](post-demo-followup-orchestration.md)) triggers off record fields.
4. **Operational auditability.** Rule 06 deviations (sales showed something on the not-show list) log back to the record
   so weekly review surfaces patterns.

## The record schema

Twelve structured fields plus freeform notes. Every field is optional at creation and fills in over the sales cycle.

| Field                  | Type / format                                                                                                 | Populated by                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `organisation`         | Firm name, legal entity                                                                                       | pb1 booking form or intro call                |
| `primary_contact`      | Name, title, email                                                                                            | Booking or intro call                         |
| `commercial_path`      | `IM` / `Reg Umbrella` / `signals-only DART` / `full DART` / `combined:<list>` / `reporting-only` / unresolved | Intro call; confirmed in pb2 briefing session |
| `strategy_origin`      | `Odum` / `client`                                                                                             | Intro call or pb2 briefing                    |
| `stack_depth`          | `reporting-only` / `downstream` / `full-pipeline`                                                             | Intro call or pb2 briefing                    |
| `service_interests`    | Union of: DART, IM, Reg Umbrella                                                                              | Prospect's stated intent                      |
| `market_scope`         | Venues / chains / instrument types / strategy families                                                        | Prospect's declared intent                    |
| `dart_schema_fit`      | For signals-only: `fits` / `needs-adapt` / `no-fit` / `n/a`                                                   | pb2b fit-check result                         |
| `structure_preference` | For IM: `SMA` / `Pooled` / `undecided`                                                                        | pb2a briefing + second call                   |
| `objections_raised`    | List of named objections with timestamp + session                                                             | Accumulated across sessions                   |
| `inferred_gaps`        | Gaps sales has spotted but prospect hasn't stated                                                             | Sales person observations                     |
| `next_commitment`      | Named next action — book call, sign mandate, etc.                                                             | Updated post each session                     |
| `deviations_logged`    | Rule-06 / rule-07 / rule-08 deviations during demos                                                           | Sales person logs verbatim with justification |
| `freeform_notes`       | Unstructured narrative                                                                                        | Anytime                                       |

## Example record

A worked example for a DART signals-only prospect mid-cycle:

```
organisation: DeFiAlpha Capital
primary_contact: Jane Smith, Head of Execution
commercial_path: signals-only DART
strategy_origin: client
stack_depth: downstream
service_interests: [DART]
market_scope:
  venues: [Binance-perp, Coinbase, Hyperliquid]
  chains: [Arbitrum, Base]
  instrument_types: [perps, spot]
  strategy_families: [stat-arb-pairs-fixed]
dart_schema_fit: fits  (confirmed in pb2b briefing 2026-04-10)
structure_preference: n/a
objections_raised:
  - (2026-04-10, pb2b): 12-month minimum is longer than expected
  - (2026-04-10, pb2b): wants exclusivity on their scope (premium flagged to commercial)
inferred_gaps:
  - Reconciliation automation — prospect hasn't asked but their spreadsheet-based current state suggests this is a value area
next_commitment: pb3c demo booked 2026-04-18
deviations_logged: []
freeform_notes: Founder is technical. Head of Execution is the decision-maker. Capital already allocated; timeline ~4 weeks to contract.
```

## How the record is created

The account-intelligence record is created automatically when a pb1 booking is placed (see
[`../experience/marketing-journey.md`](../experience/marketing-journey.md) internal handoff). It is populated
progressively:

1. **pb1 booking.** organisation + primary_contact + intent hint from booking form.
2. **Intro call.** commercial_path + strategy_origin + stack_depth + service_interests + market_scope preliminary.
3. **pb2 briefing view.** briefing-read event + dwell signals + section-skip patterns.
4. **pb2 second call.** Refined market_scope, dart_schema_fit, structure_preference, objections_raised.
5. **pb3 demo session.** Restriction profile applied, demo walked, deviations logged, next_commitment updated.
6. **Follow-up sessions.** Record updates each touch.

## How the record is accessed

- **Before a session.** The sales person reads the record during pre-session prep (15-30 min before).
- **During a session.** The sales person has the record open in a side panel; updates in-session are time-stamped.
- **After a session.** Structured post-session update. See
  [`meeting-history-and-interest-tracking.md`](meeting-history-and-interest-tracking.md).

## Privacy and segregation

- Access scoped to the sales team owning the prospect. Other sales people on other paths do not see the record.
- Rule 07 data licensing applies — no raw market data in the record.
- Prospect PII follows Odum's security controls (see [`../../07-security/`](../../07-security/)).

## Cross-references

- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md) — deviations logged
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — service interests
  anchor
- [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md) — how sales infers without interrogating
- [meeting-history-and-interest-tracking.md](meeting-history-and-interest-tracking.md) — session updates
- [post-demo-followup-orchestration.md](post-demo-followup-orchestration.md) — follow-up triggers
- [demo-decision-matrix.md](demo-decision-matrix.md) — record informs matrix
- [../experience/](../experience/) — every experience playbook's §9 updates this record
