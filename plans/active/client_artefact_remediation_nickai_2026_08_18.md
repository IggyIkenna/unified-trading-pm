---
doc_type: plan
title: Client artefact remediation — Nick AI platform walkthrough
summary: >-
  All remediation touching platform-external-api-walkthrough.html only — accuracy fixes, the seven absent and four
  thin capability sections, the live re-grade, the forward-claim cut, and evidence-tier tagging for this one file.
  Split out of client_artefact_remediation_2026_08_18.md so it runs in parallel with the Elysium and sibling
  children; file scope is what makes that safe.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, artifact-remediation, audit-followup]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
    /plans/audit/results/client_artefact_forward_claim_and_reverification_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-18 to split client_artefact_remediation_2026_08_18.md by artefact for parallelism.
  Todos MOVED here from the parent's § C and § D plus the Nick-AI-scoped items of § E and § F.
context_scope:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
---

# Client artefact remediation — Nick AI platform walkthrough

**File owned by this plan**: `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` —
and nothing else. Gated on the parent only for the evidence-tier spec.

## Accuracy fixes

- [x] [DOC] P0. ✅ **Rewrite §2/§3's external-API status framing.** The layer is now substantively real — 2 read
      endpoints on instruments-service, 3 on MTDS, 1 write endpoint on execution-service — so the pre-audit's "it
      doesn't exist" is stale. But "you get the contract our own execution service gets" is still untrue: **only
      TRADE is live end-to-end; the other 10 of 11 instruction types return an honest HTTP 501.** Name the concrete
      live surface and state the 501 plainly. strategy-service has no counterparty-facing surface at all and stays
      `planned`. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P0. ✅ **Re-grade every `live` badge in this file to `partial`** — all 6 of them. No section survives the
      conjunctive test; an exhaustive workspace search found no real-capital evidence anywhere. By the owning
      epic's own design, not a writing defect. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P0. ✅ **Cut the forward claim** — "most venues and strategies on the current plan complete over the
      remainder of this year." The corpus search found no committed basis anywhere. Cut, do not soften. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P1. ✅ **Fix §4's four-state coverage table** — it marks "Expected, absent" (`empty_confirmed`) as
      counting toward coverage, while the "How to read 48.54%" callout two paragraphs later defines the denominator
      as `captured + attempted-failed + expected-unattempted` only. The two contradict; reconcile them. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P1. ✅ **Reconcile the 288-venue figure** — stated alone. Either place all three legitimately-different
      units side by side (151 canonical / 183 physical / 288 manifest-grain) or scope 288 explicitly as "venues in
      the 2026-08-18 coverage manifest at readiness-dump grain, not comparable to registry-declared counts". The
      difference is a measurement-unit difference, and we need the answer ready if asked. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P1. ✅ **Fix the CeFi spot-pair instrument-ID example** — instrument-type token `SPOT` should be
      `SPOT_PAIR`. Other ID examples and all named venues verified correct. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P2. ✅ **Fix §14's "19-step contract" mislabel** — the quoted 864-row / 0-844-20 rollup came from the
      readiness-dump's **8-leg** model, a different framework. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P2. ✅ **Qualify §16's "a great deal of testnet work is already complete"** — real gaps exist (no per-venue
      cefi testnet declaration, sports' live credential probe stubbed, tradfi's only live probe covers Tardis,
      Polymarket has no testnet and no written paper-trading ruling) alongside real progress (AAVE Sepolia, Solana
      LST devnet, Kalshi demo host). **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P3. ✅ **Scope §5's "every figure is pending measurement" lede** to the coverage-percentage cells only —
      it currently sits above tree summaries showing already-measured readiness splits. **Shipped `unified-trading-pm@ec08cccad1`.**

## Missing capability

- [ ] [DOC] P1. **Add the 7 fully-absent capability sections** — fee/gas breakdown; collateral usability and
      cross-margin per venue; manual trade on every venue as the disaster path; a reconciliation framework;
      PnL attribution across risk/exposure dimensions; risk in native AND share-class-normalised terms plus Greeks
      and DART's dimensions; latency/tracing, preflight input registration and per-input staleness SLAs. **Write
      these as target-state, marked with the parent's evidence tier** — each maps to an open P0 workstream
      (W5/W10/W12/W13/W16/W17) with nothing checked off. Per operator ruling the content goes IN and is marked; it
      is not withheld, because the top-down view is what surfaces duplication and misplaced logic.
- [ ] [DOC] P2. **Add the 4 present-thin capability sections** — transfer rails/custody eligibility per venue; the
      batch=live determinism mechanism named (UTL `EventTransport`, `InMemoryTransport` vs Pub/Sub); order lifecycle
      vocabulary (creates/updates/cancels/amends plus restart recovery); TWAP named alongside straight-market.
- [x] [DOC] P2. ✅ **Name MDPS/features-service explicitly as the intermediary** in §1's architecture diagram —
      currently MTDS/MDPS/features collapse into one "Market data" box with a direct arrow to Strategy, which could
      read as a direct call and contradict the "strategy never reads MTDS directly" invariant. **Shipped `unified-trading-pm@ec08cccad1`.**

## Evidence tiers and readiness

- [x] [DOC] P0. ✅ **Apply the parent's evidence-tier spec to every claim-bearing section in this file** — default
      `needs-check`; `machine-verified` requires naming the verifying command, skill or code symbol inline. **Shipped `unified-trading-pm@ec08cccad1`.**
- [ ] [DOC] P1. **Give every claim-bearing section its owner mark**, per W21's closure invariant.
- [ ] [DOC] P1. **Audit the archetype-readiness (batch/paper/live) content — it asserts a dimension nothing can
      derive.** Measured 2026-08-18: the only skill emitting the three modes is `readiness-state-dump`, and it
      derives per **(venue x mode)** only — archetype is NOT one of its dimensions. Per-archetype readiness is an
      OPEN, unchecked `[BACKEND] P0` in [system_readiness_master](/plans/epics/system_readiness_master.md) W1 ("an archetype has its own batch /
      paper / live"). This content was added to BOTH artefacts at `unified-trading-pm@832033d094` on operator
      request and was never probed. Per W21, an artefact claim that outruns the derived state is a defect — so
      either mark it `~ assumed` with the gap stated, or cut it until the epic todo lands. Sibling todo in the
      Elysium child covers the other file.
- [ ] [DOC] P1. **Audit the glossary / canonical-instrument-ID framing** — check that it presents ONE dispatch
      spanning asset groups, not per-asset-group ID rules, which would invert asset-group-agnosticism.

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
per operator direction. Todos moved, not copied.
