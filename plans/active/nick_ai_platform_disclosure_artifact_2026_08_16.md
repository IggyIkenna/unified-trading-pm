---
doc_type: plan
title: Nick AI platform disclosure — pre-audit, coverage measurement, and the external-API artifact
summary: >-
  A second client disclosure track, distinct from Elysium: this one pitches the PLATFORM (contracts + reference data,
  market tick data, strategy-service as the asset-class-agnostic instruction API, execution-service as the algo and
  routing layer, security) rather than a strategy carve-out, and it may state readiness and honest-coverage
  percentages openly. The counterparty connects EXTERNALLY via the same service-to-service API contracts our own
  services use, and browses/downloads data through a deployment-api-style surface. Deliverable is one long
  collapsible HTML artifact; density is explicitly fine (the reader is AI-orchestrated). This plan holds the scope
  rulings, the pre-audit measurements the artifact must not invent, and the disclosure boundary.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    execution-service,
    deployment-api,
  ]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, artifact, honest-coverage, external-api, pre-audit]
related:
  [
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-16
source: >-
  Operator direction 2026-08-16 (interactive + relayed counterparty thread). Second client track; target Tuesday.
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: design
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: high
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
---

# Nick AI platform disclosure

## How this differs from the Elysium track — read this first

Both are client disclosure. They are **not** the same shape, and conflating them is the main risk.

| | Elysium | **Nick AI (this plan)** |
| --- | --- | --- |
| What is sold | a strategy carve-out — strategy-service code | **the platform**, as an external API |
| Readiness disclosure | guarded | **open** — readiness stage and honest-coverage % are stated plainly |
| Integration | they run the code | **they call us** over the same service-to-service contracts our services use |
| Data | not the product | **is** the product — browse, then download |
| Density | tuned for a CTO read | **dense is fine** — the reader is AI-orchestrated (counterparty's own words) |

## Scope — what the artifact pitches

The whole system **except ML and the features feeding ML**:

1. **Unified contracts + reference data** — contract/instrument definitions.
2. **Market tick data** — with clear disclosure of the boundaries of each data type per venue, across the full venue
   universe.
3. **Strategy-service** — a strategy- and asset-class-agnostic unified API to execution. The pitch is the
   NORMALISATION: swap, lend, transfer, back, lay, withdraw, deposit all travel as one unified instruction set. This
   is the piece the counterparty most needs, because they want users to move from an AI chatbot into a strategy
   solution, which only works if everything looks and behaves the same.
4. **Execution-service** — the algo smarts and adaptors that route normalised instructions to real venue actions.
5. **Security** — stated as a prerequisite of any final delivery, not an add-on.

**Explicitly OUT**: ML, and the features that feed ML.

## Disclosure boundary — HARD

- **Archetypes yes, edge no.** Describe the archetypes, how quickly new ones are added, and how they subscribe to
  modules via registry contracts and what scope each covers. **Do NOT describe how our strategies actually make
  money.** This is the same line the Elysium artifact holds, for a different reason: there we withheld the config
  loop, here we withhold the alpha.
- **Code snippets are limited to configuration schemas and API contracts** — the service-interaction contracts,
  mirroring the in-house service-to-service contracts we already have. Not strategy internals.
- **No commercial figures.** No budget, funding, valuation, or cost/ARR numbers anywhere in the artifact. Those exist
  in the relationship, not in the document.
- **No third-party commercial relationships named** without an explicit operator ruling.

## Execution depth — RULED

The counterparty asked how far to take execution: router only, or chained atomic instruction sequences (borrow →
swap → stake), and execution algos (TWAP vs straight market). **Ruling: cover it.** Their own answer was "if it's
available, we can build into it; if it's not, we can start simple" — so the honest move is to disclose the full
capability and let them choose the entry point. Same for treasury/wallet: cover both balance querying AND transfer
instruction, marking which is which.

## Artifact structure requirements

- **One long HTML artifact. Length is explicitly acceptable here** — this is the stated exception, because
  collapsing carries the density.
- **Collapsible at every level of the hierarchy**: asset group → venue → instrument type → data type. The reader
  must be able to collapse an entire AG and never see it.
- **Per-shard schemas shown**, so they can see exactly what is there.
- **The config they would need is displayed.**
- **Data access model mirrors deployment-api/UI**: check what is available, then download — daily batch parquet and
  streaming live for market data, a parquet dump for instruments.

## PRE-AUDIT — numbers the artifact must NOT invent

Every figure below goes in only once measured. A client-facing percentage sourced from memory is the one error that
cannot be walked back, and this artifact is mostly numbers.

- [ ] [DATA] P0. **Measure honest coverage per (asset_group × venue × instrument_type × data_type × chain)** from the
      availability manifest via the deployment-api data-status surface — the same machinery the UI already uses, not
      a re-implementation. Record the denominator each percentage is over; a percentage without its denominator is
      not a measurement. SSOT: [honest-coverage-model](/codex/02-data/honest-coverage-model.md).
- [ ] [DATA] P0. **Verify the "≈50% average now, ≈99% obtainable" claim** already relayed to the counterparty. If the
      measured figure differs, the artifact states the measured one and the relayed number is corrected in
      conversation — the document must not carry a number to stay consistent with a prior claim.
- [ ] [DATA] P0. **State the venue-universe denominator precisely.** "~170 venues" has been relayed; the umbrella's
      measured figure is 158 capture venues across 84 families, and the readiness contract applies per
      (venue × data type). Reconcile before publishing, and say which unit each count is in.
- [ ] [DATA] P1. **Current vs expected size per AG after backfills complete** — both figures, with the expected one
      labelled as a projection and its basis stated.
- [ ] [DATA] P1. **Readiness stage per AG (batch / paper / live)**, derived from the Venue Readiness Contract rather
      than declared. Per the 2026-08-16 ruling a step with no real check reports `unverified`, never a pass — so the
      artifact must show `unverified` where that is the truth.
- [ ] [BACKEND] P1. **Enumerate the external API surface** they would actually call, mirroring the internal
      service-to-service contracts: instruments, market data availability + download, the strategy instruction
      contract, execution routing. Include the per-shard schemas.
- [ ] [BACKEND] P2. **State the credentials/testnet position honestly** — venue connectivity needs capital in place;
      many testnets are complete; the remaining work is weeks, not months, and depends on which venues they want.

## Build

- [ ] [DOC] P0. **Build the artifact** once the P0 pre-audit items are measured. Reuse the established design
      language from the existing walkthrough artifacts rather than redesigning — they read well and consistency
      across our client documents is itself a signal.
- [ ] [REVIEW] P0. **Operator review before send**, against the disclosure boundary above.

## Progress Log

**2026-08-16 — authored.** Captured from an interactive session plus a relayed counterparty thread, ahead of any
build work, specifically so the scope rulings and the disclosure boundary survive outside chat. The pre-audit section
exists because this artifact is mostly figures: unlike the Elysium walkthrough, which describes mechanisms, this one
quantifies coverage — so the measurement discipline is the deliverable's main risk, not a formality.
