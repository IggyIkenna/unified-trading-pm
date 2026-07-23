---
doc_type: codex-ssot
title: Demo Decision Matrix
summary:
  Deterministic prospect-profile to demo-path recommendation — maps resolved commercial_path + decision-maker structure
  + readiness to demo flavour (pb3a/b/c or combined), demo mode, default restriction profile, and expected next
  commitment; a starting point sales confirms, with deviations documented in the account-intelligence record.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, engineer, admin]
tags: [demo-ops, sales, dart, decision-matrix, restriction-profile, curation]
related:
  [
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-curation-rules.md,
  ]
created: 2026-04-20
authoritative_for: [demo decision matrix (prospect profile to demo path)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/demo-restriction-profiles.md,
    /codex/14-customer-journeys/demo-ops/meeting-history-and-interest-tracking.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/staging-demo-setup.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Demo Decision Matrix

> Prospect profile → recommended demo path (flavour + mode + restriction profile + expected next commitment). Ties the
> pre-demo discovery framework to the restriction profile and demo mode.

**Rule source:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md),
[rule 06](../_ssot-rules/06-show-dont-show-discipline.md)

## What the matrix does

Given an account-intelligence record, the matrix recommends:

- **Demo flavour** — pb3a / pb3b / pb3c, or combination.
- **Demo mode** — broader-platform / turbo / deep-dive.
- **Restriction profile** — which of the standard profiles in
  [`demo-restriction-profiles.md`](demo-restriction-profiles.md).
- **Expected next commitment** — what the session is trying to produce.

The matrix is deterministic given a resolved prospect profile. The sales person consults it for a starting point;
deviations are documented with rationale.

## The matrix

| Resolved commercial path               | Decision-maker solo / committee | Exploratory / decision-ready | Flavour                    | Mode               | Default profile                                  | Expected commitment                           |
| -------------------------------------- | ------------------------------- | ---------------------------- | -------------------------- | ------------------ | ------------------------------------------------ | --------------------------------------------- |
| IM (SMA)                               | Solo                            | Decision-ready               | pb3b                       | Turbo              | IM allocator profile                             | Mandate signing date                          |
| IM (Pooled)                            | Solo                            | Decision-ready               | pb3b                       | Turbo              | IM allocator profile                             | Mandate signing date                          |
| IM (undecided structure)               | Solo                            | Exploratory                  | pb3b                       | Turbo              | IM allocator profile                             | Second session on structure                   |
| IM (committee)                         | Committee                       | Exploratory                  | pb3b                       | Broader platform   | IM allocator profile                             | Committee-review decision + follow-up         |
| Reg Umbrella                           | Solo                            | Decision-ready               | pb3a                       | Deep-dive          | Reg Umbrella profile                             | Onboarding kickoff date                       |
| Reg Umbrella                           | Committee                       | Exploratory                  | pb3a                       | Deep-dive          | Reg Umbrella profile                             | Onboarding kickoff or scope follow-up         |
| Signals-only DART (schema fits)        | Solo                            | Decision-ready               | pb3c                       | Turbo              | Signals-only DART profile                        | Onboarding kickoff or commercial close        |
| Signals-only DART (schema fits)        | Solo                            | Exploratory                  | pb3c                       | Broader platform   | Signals-only DART profile                        | Commercial close meeting                      |
| Signals-only DART (schema needs adapt) | Solo                            | Exploratory                  | pb3c                       | Broader platform   | Signals-only DART profile                        | Schema-adapt review + second demo             |
| Signals-only DART (committee)          | Committee                       | Exploratory                  | pb3c                       | Broader platform   | Signals-only DART profile                        | Committee-review + commercial close           |
| Full DART                              | Solo                            | Decision-ready               | pb3c                       | Turbo or deep-dive | Full DART profile                                | Commercial close + onboarding kickoff         |
| Full DART                              | Committee                       | Exploratory                  | pb3c                       | Broader platform   | Full DART profile                                | Committee-review + second demo on one surface |
| Combined Reg Umbrella + IM             | Any                             | Any                          | pb3a + pb3b (two sessions) | Deep-dive each     | Combined profile                                 | Mandate + onboarding sequenced                |
| Combined Reg Umbrella + DART           | Any                             | Any                          | pb3a + pb3c (two sessions) | Deep-dive each     | Combined profile                                 | Sequenced commitments                         |
| Combined IM + DART                     | Any                             | Any                          | pb3b + pb3c (two sessions) | Turbo / broader    | Combined profile                                 | Sequenced commitments                         |
| Reporting-only (not DART commercially) | Any                             | Any                          | pb3b or pb3a               | —                  | IM reporting-only or Reg Umbrella reporting-only | Commercial decision on reporting scope        |

## How to use

1. **Look up the row** that matches the prospect's resolved profile.
2. **Confirm restriction profile** matches the row's default. If overriding, document why.
3. **Confirm demo mode.** Sales-person judgement may adjust (e.g., switch from turbo to deep-dive if the prospect has
   deep questions on one surface).
4. **Set the next-commitment expectation** for the session. The close is designed around producing that commitment.

## What drives deviations

Common reasons to deviate from the default:

- **Prospect explicitly requests a different mode.** "We want to see everything" → broader platform regardless of
  decision-readiness.
- **Time constraint.** A 30-minute slot doesn't support broader-platform; compress to turbo or push to a second session.
- **Specific capability question.** "Show me how you handle options chain onboarding" → deep-dive on that surface even
  if the path suggests turbo.
- **Earlier deviation flagged in the record.** If the prior session raised a specific reservation, this session's
  curation targets it.

Every deviation from the default is documented in the account-intelligence record with the rationale.

## What the matrix does not do

- **Does not resolve unresolved paths.** If `commercial_path` is unresolved in the record, the demo should not be
  scheduled. The pb2 briefing + second call must resolve first.
- **Does not pick the restriction profile content.** The profile content is defined in
  [`demo-restriction-profiles.md`](demo-restriction-profiles.md).
- **Does not replace sales judgement.** The matrix is the starting point. Prospect-specific context adjusts.

## Cross-references

- [demo-restriction-profiles.md](demo-restriction-profiles.md) — profile definitions
- [dart-demo-modes.md](dart-demo-modes.md) — mode definitions
- [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md) — record inputs
- [account-intelligence-record.md](account-intelligence-record.md) — record structure
- [pre-demo-curation-rules.md](pre-demo-curation-rules.md) — curation given matrix output
- [../experience/staging-demo-journey.md](../experience/staging-demo-journey.md) — hub that ties the flavour demos
  together
- [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md) — commercial paths
