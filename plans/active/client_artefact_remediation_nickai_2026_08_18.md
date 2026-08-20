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
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
    /plans/audit/results/client_artefact_forward_claim_and_reverification_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
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
    /plans/archive/2026_08/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
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

- [x] [DOC] P1. ✅ **Add the 7 fully-absent capability sections** — fee/gas breakdown; collateral usability and
      cross-margin per venue; manual trade on every venue as the disaster path; a reconciliation framework;
      PnL attribution across risk/exposure dimensions; risk in native AND share-class-normalised terms plus Greeks
      and DART's dimensions; latency/tracing, preflight input registration and per-input staleness SLAs. Written as
      target-state (§18-§24), `st-plan` "planned", tagged `? check` (six sections) or `~ assumed` (collateral +
      cross-margin, since no UAC registry field answers it — written as best current understanding, explicitly not
      a queryable matrix). Maps to W5/W10/W12/W13/W16/W17. **Shipped `unified-trading-pm@2b0c327e44`.**
- [x] [DOC] P2. ✅ **Add the 4 present-thin capability sections** — transfer rails/custody eligibility per venue; the
      batch=live determinism mechanism named (UTL `EventTransport`, `InMemoryTransport` vs Pub/Sub); order lifecycle
      vocabulary (creates/updates/cancels/amends plus restart recovery); TWAP named alongside straight-market. **TWAP, `EventTransport`/`InMemoryTransport` and the cancel/amend lifecycle vocabulary all verified present in the artefact. Verified 2026-08-19.**
- [x] [DOC] P2. ✅ **Name MDPS/features-service explicitly as the intermediary** in §1's architecture diagram —
      currently MTDS/MDPS/features collapse into one "Market data" box with a direct arrow to Strategy, which could
      read as a direct call and contradict the "strategy never reads MTDS directly" invariant. **Shipped `unified-trading-pm@ec08cccad1`.**

## Evidence tiers and readiness

- [x] [DOC] P0. ✅ **Apply the parent's evidence-tier spec to every claim-bearing section in this file** — default
      `needs-check`; `machine-verified` requires naming the verifying command, skill or code symbol inline. **Shipped `unified-trading-pm@ec08cccad1`.**
- [x] [DOC] P1. ✅ **Give every claim-bearing section its owner mark**, per W21's closure invariant. **25 `class="own"` marks verified in the file, each citing its owning epic/workstream in a title attribute. Verified 2026-08-19.**
- [x] ✅ [DOC] P1. **Audit the archetype-readiness (batch/paper/live) content — it asserts a dimension nothing can
      derive.** Measured 2026-08-18: the only skill emitting the three modes is `readiness-state-dump`, and it
      derives per **(venue x mode)** only — archetype is NOT one of its dimensions. Per-archetype readiness is an
      OPEN, unchecked `[BACKEND] P0` in [system_readiness_master](/plans/epics/system_readiness_master.md) W1 ("an archetype has its own batch /
      paper / live"). This content was added to BOTH artefacts at `unified-trading-pm@832033d094` on operator
      request and was never probed. Per W21, an artefact claim that outruns the derived state is a defect — so
      either mark it `~ assumed` with the gap stated, or cut it until the epic todo lands. Sibling todo in the
      Elysium child covers the other file.
      **AUDITED, ALREADY COMPLIANT — no edit needed.** `git blame` on the callout (`codex/14-customer-journeys/
      commercial-model/platform-external-api-walkthrough.html:2518-2531`, "Readiness applies to archetypes as well
      as venues") shows every line was authored in `unified-trading-pm@832033d0942` — the SAME commit the todo
      itself cites as "added... and never probed" — not a later fix. The text was hedged from its very first
      version: `<b class="st st-plan">planned</b> — a capability audit deriving archetype readiness across batch,
      paper and live is specified and not yet built. Until it runs, that axis reports <code>unverified</code>
      rather than being assumed.` This already satisfies W21 — it never claims the archetype axis is derived or
      live, uses the doc's own `st-plan` status badge correctly, and explicitly names the gap (the unbuilt capability
      audit, citing the same W1 todo this plan item cites). Deliberately did NOT add the doc's `ev-assumed` badge
      pair (used elsewhere for genuine best-guess claims, e.g. lines 1903/2624/2850) — the text's own wording
      ("reports unverified rather than being assumed") is a stronger, more accurate framing than `~ assumed` would
      be: it asserts no best-current-understanding at all, only that the check doesn't exist yet. Cross-checked the
      rest of §14 ("Readiness: batch, paper, live", lines 2382-2568) for any other archetype-readiness claim outside
      this one callout — the section's own measured table (2454-2513) is venue×mode only (288 venues × 3 modes =
      864 rows, matching `readiness-state-dump`'s real dimensions exactly), no archetype axis asserted there either.
      No HTML commit needed — content already correct as of its original authoring commit.
- [x] [DOC] P1. ✅ **Audit the glossary / canonical-instrument-ID framing** — check that it presents ONE dispatch
      spanning asset groups, not per-asset-group ID rules, which would invert asset-group-agnosticism. **Framing VERIFIED CORRECT — the artefact reads "a canonical identity built by one dispatcher for every asset group" and "a single dispatch point for instrument identity across every asset group", i.e. one dispatch spanning asset groups, not per-AG rules. Verified 2026-08-19.**

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md)
per operator direction. Todos moved, not copied.

**context-scout 2026-08-19**: populated context_scope (3 entries) — added the owned HTML file the remaining
archetype-readiness todo edits.

**2026-08-18 — 7 fully-absent capability sections shipped, `unified-trading-pm@2b0c327e44`** (slot 3): added
§18-§24 to `platform-external-api-walkthrough.html` — fees/gas by component, collateral+cross-margin per venue,
manual-trade disaster path, reconciliation framework, PnL attribution, risk in native+share-class terms w/ Greeks +
DART's dimensions, latency/preflight/staleness SLAs — plus matching contents-nav entries. All `st-plan` "planned",
tagged `? check` or `~ assumed`. No `live`/`partial` claims, no ClearLoop, no commercial or performance figures.
**Note on this ship**: this slot's checkout had 5+ concurrent sessions sharing it; a `git stash pop` (not mine) raced
my restore of an autostashed edit and left the working-tree copy with unresolved conflict markers for ~10 minutes.
The already-pushed commit was independently verified clean (`git show <sha>:<path>`, `git merge-base --is-ancestor`)
before this checkbox was flipped — the corruption never reached origin, only the local working tree, and was fixed by
re-checking out the file from the verified-clean `origin/live-defi-rollout`. Shipped via
`quickmerge.sh --isolated` after the first attempt (non-isolated) is what got quarantined by a peer's reconcile pass.
Owner-mark todo (P1 below) still deliberately untouched — its spec landed separately at `unified-trading-pm@19724f5e69`
after this pass started, out of scope for this todo. 4-thin-section (P2) and archetype-readiness/glossary-audit (P1)
todos also untouched.
