---
doc_type: plan
title: Client artefact remediation — fix accuracy, completeness and drift found by the 2026-08-18 audit
summary: >-
  Fixes every accuracy, completeness and target-state-fidelity finding from the 2026-08-18 audit of
  platform-external-api-walkthrough.html (Nick AI) and strategy-service-walkthrough.html (Elysium) — content-only
  edits to the two artefacts, citing real evidence for every change. Does NOT build new system functionality; where
  a finding traces to a genuine system gap rather than a documentation gap, this plan cites the existing tracked
  item instead of duplicating it (§ "Real system gaps — already tracked, not duplicated here").
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, nick-ai, elysium, artifact-remediation, audit-followup]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: infra
effort: high
drift_direction: none
depends_on: []
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Operator direction 2026-08-18: audit both client artefacts with sub-agents, verify with an independent pass, then
  document and push a triage-ready dispatch plan so the agent-orchestrator fleet can pick up the remediation.
context_scope:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/epics/system_readiness_master.md,
    scripts/plan-hygiene/check_artefact_disclosure.py,
    scripts/plan-hygiene/check_artefact_enum_drift.py,
  ]
---

# Client artefact remediation — 2026-08-18 audit follow-up

**Read the audit first**:
[`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)
— every todo below cites a specific finding from it. `sequential: true` because every todo edits one of only two
files (`strategy-service-walkthrough.html`, `platform-external-api-walkthrough.html`) — concurrent dispatch would
race edits on the same file, which the workspace's own concurrency rule forbids (independent todos must touch
different files).

**Disclosure boundary reminder for every todo below** — do not drift past this while fixing content:
- Both artefacts: no commercial figures, never name ClearLoop.
- Nick AI (`platform-external-api-walkthrough.html`): archetypes yes/edge no; code snippets limited to config
  schemas and API contracts; ML/features out of scope.
- Elysium (`strategy-service-walkthrough.html`): the config loop stays withheld; no performance figures.
- **No todo here authorises sending either document anywhere.** Both owning plans already carry their own final
  "operator review before send" gate — [`nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)'s
  "Operator review before send" P0 todo and the equivalent disclosure-review items in
  [`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`](/plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md)
  § E — this plan does not re-create that gate.

## Split 2026-08-18 — this plan is now the SPEC + TOOLING gate; per-file work lives in three children

Operator direction 2026-08-18: split by artefact for parallelism. File collision was the only real constraint, so
each child owns a disjoint file set and the three run **concurrently**.

| Child                                                                                                                   | Owns                                                                        | Gated?                     |
| ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------------------------- |
| [siblings](/plans/active/client_artefact_remediation_siblings_2026_08_18.md)                                             | deep-dive · platform-architecture · carveout-engineering · ODUM Phase2        | **No — P0 stop-ship**      |
| [elysium — archived](/plans/archive/2026_08/client_artefact_remediation_elysium_2026_08_18.md)                              | `strategy-service-walkthrough.html`                                          | on this plan's spec        |
| [nickai](/plans/active/client_artefact_remediation_nickai_2026_08_18.md)                                                  | `platform-external-api-walkthrough.html`                                     | on this plan's spec        |

Todos were **moved, not copied** — nothing below duplicates a child. This plan deliberately holds no per-file edit:
its todos define the marks the children apply, and build the tooling that stops all of this recurring.

- [x] [DOC] P0. ✅ **Define the evidence-tier spec** — exact markup, wording and legend copy for `machine-verified` /
      `needs-check` / `assumption`, visually distinct from the `live`/`partial`/`planned` status pill. Children
      apply it to their own file, so defining it once here is what keeps the two documents consistent. Rule:
      default is `needs-check`; `machine-verified` requires naming the verifying command, skill or code symbol
      inline, which is what makes a later re-audit cheap. **Shipped `unified-trading-pm@171dc40739 + ec08cccad1`.**
- [x] [DOC] P0. ✅ **Define the owner-mark spec** — how a section names the workstream/plan/epic that closes it, per
      `system_readiness_master.md` W21's closure invariant. Keep it terse enough to sit beside two other marks.
      **Shipped `unified-trading-pm` —**
      [rule 13 — artefact claim marks](/codex/14-customer-journeys/_ssot-rules/13-artefact-claim-marks.md): exact
      CSS (`.own`, a solid neutral chip — distinct from `.st`'s solid colour-bordered pill and `.ev`'s dashed
      colour-bordered pill), section-head markup, legend copy, and the content grammar (workstream shorthand `W<N>`
      / plan short-tag `§<section>` / epic slug, omitted once status reaches `live`). `_ssot-rules/README.md`
      index also fixed to list rules 11-13 (was silently stuck at "the ten rules").
- [x] [SCRIPT] P0. ✅ **Build a banned-term / disclosure checker over the artefact directory, and wire it into QG.**
      Measured 2026-08-18: **no checker anywhere greps client artefacts for the banned client name** — the
      six-hit stop-ship in `strategy-service-deep-dive.html` was found only because an audit was commissioned, and
      nothing would catch a recurrence tomorrow. Must scan **raw file text, not rendered prose** (one original hit
      was inside an SVG `<text>` element), cover all six files in
      `codex/14-customer-journeys/commercial-model/`, and derive its rules from
      [show-dont-show-discipline](/codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md) — the
      codex SSOT — rather than restating them. Also flag performance-figure patterns; note that legitimate uses
      exist ("net carry (annualised, bps)"), so this warns for review rather than hard-failing on the word alone.
      **Shipped**: `scripts/plan-hygiene/check_artefact_disclosure.py` (+ `artefact_disclosure_baseline.yaml`),
      wired into `run_hygiene_sweep.sh`. Raw-text scan (no HTML parser, so an SVG `<text>` hit is caught
      identically). HARD zero-tolerance class: banned client name, `CODE_NOT_WRITTEN`/`CODE_WRITTEN` maturity
      leaks, internal `/admin/`,`/ops/`,`/config/`,`/devops/` route leaks. WARN shrinking-ratchet class:
      performance-figure patterns (seeded baseline 1, from one legitimate "2.5% APR" hit). **Live-ran against the
      corpus at ship time: HARD class is currently RED — 6 real ClearLoop hits in `strategy-service-deep-dive.html`,
      owned by `client_artefact_remediation_siblings_2026_08_18.md`, not a regression from this wiring.** The
      hygiene-sweep gate will stay red until that sibling todo lands — expected, not a defect in this checker.
- [x] [SCRIPT] P1. ✅ **Build the enum-drift check** validating artefact-quoted enum data against the UAC enums.
      Root cause of two P0s: enum contents are hand-transcribed into six HTMLs, so one concern lives in seven
      places. Proof it recurs — the invented strategy family reached three documents, and
      `/codex/04-architecture/strategy-execution-protocol.md` correctly said "11 actions" while the artefact said
      9. Cover all six artefacts; ratchet-baseline it; name which enum each claim derives from.
      **Shipped**: `scripts/plan-hygiene/check_artefact_enum_drift.py` (+ `artefact_enum_drift_baseline.yaml`),
      wired into `run_hygiene_sweep.sh`. AST-parses ground truth from UAC source (no import dependency); tracks
      `StrategyFamily` (9 members) and `StrategyInstructionEnvelope` (11 subclasses) to start, extensible.
      Count-based (not per-member-name — documented as a deliberate, non-silent scope limit in the script's
      docstring). Caught and required fixing one false positive during build: "the other 10 action types" in
      `platform-external-api-walkthrough.html` §2 is correct prose (11 total minus the 1 already named, TRADE),
      not a drift — added an "other N" exclusion so the check doesn't flag total-minus-N phrasing. Live-ran clean
      (0 violations) at ship time; baseline seeded at 0.
- [x] [RESEARCH] P1. ✅ **Research real per-venue transfer rails / custody eligibility / collateral / cross-margin.**
      Measured: **no UAC registry field answers these** — `VenueCapabilityRecord` is market-data only (`route` +
      `data_types`), `VenueCapability` covers actions, and a registry-wide grep for
      `cross_margin|collateral_eligib|transfer_rail|withdraw_enabled|margin_asset` returns empty. Per the operator
      ruling recorded in this plan's own § E preamble
      ([`/plans/active/client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
      § E, "do NOT withhold full system functionality"), the best current answer goes into the artefacts marked
      `assumption`/`needs-check` rather than being withheld — **and this todo's output must spawn a
      registry-extension todo under W5**, so the artefact ends up downstream of a machine SSOT instead of becoming
      one.
      **CORRECTION found during research 2026-08-18**: the premise above is only half right. A grep for
      `cross_margin` (no `_eligib` suffix) DOES hit — `VenueCapabilityV2.collateral_rules`/`.margin_spec`
      (`CollateralRulesV2`/`MarginSpec` in `unified-api-contracts/.../architecture_v2/schemas.py`) is a real,
      actively-consumed schema (`strategy-service/strategy_service/risk/v2/{margin_sim,preflight,orchestrator}.py`)
      that already covers per-asset LTV/haircut collateral and cross-/portfolio-margin flags — populated for
      **zero** real venues. Custody-eligibility and transfer-rail-eligibility per venue remain genuinely absent
      (no field anywhere). Full findings + suggested `assumption`/`needs-check` artefact copy:
      [venue transfer/custody/collateral research](/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md).
      **Registry-extension todos added to `system_readiness_master.md` W5** — refined the existing "Collateral
      that can actually be used" and "Cross-margin logic" P0 items to point at the specific unpopulated schema
      (population, not design), and clarified the "Transfer capability per venue" P0 item still needs new fields
      (no existing type to extend, unlike collateral/margin).
- [x] [REVIEW] P1. ✅ **Audit the four sibling artefacts** — delivered by the second-pass audit,
      `unified-trading-pm@8b7e78e21f`; findings in
      [sibling-docs audit](/plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md). Remediation
      moved to the siblings child.
- [x] [REVIEW] P1. ✅ **Cross-document consistency sweep across all six artefacts** — delivered,
      `unified-trading-pm@8b7e78e21f`; findings in
      [cross-document consistency](/plans/audit/results/client_artefact_cross_document_consistency_2026_08_18.md).
      Found the invented family in three documents and the three-way custody contradiction.

## Real system gaps — already tracked, not duplicated here

These findings trace to genuine gaps in the system itself, not documentation gaps. **Do not re-author them as todos
in this plan** — each already has an open, tracked item; this plan's job is to make sure the artefact team knows
they gate certain content from moving out of "thin"/"absent," not to re-derive the fix:

- **Transfer handler production wiring** (blocks A's §11 rewrite from ever becoming a "live" claim) —
  `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § C, P0, open.
- **Capital-budget enforcement** — same plan § B, P0, open.
- **Dynamic-universe as-of-date pinning** (the paper==batch-rerun equality risk) — same plan § H.8, P0, open.
- **Fee/gas breakdown, collateral/cross-margin, manual-trade-on-every-venue, reconciliation framework, PnL
  attribution, risk-in-native+share-class-terms/Greeks, latency/tracing/preflight/SLA** —
  `system_readiness_master.md` W5, W10, W12, W13, W16, W17 — all P0, all open, zero items checked off across all
  six workstreams as of this audit.
- **Canonical output paths for everything strategy-service emits** — same epic, W18, P0, open.

Mirrored-custody routing, the funding-route graph, the rank-allocator weighting layer and the book-level overlays
(§ B above) are **not** in this list — the audit confirmed these already exist in the running system
(`CUSTODY_TRANSFER` rail, `ALLOCATOR_ARCHETYPE_REGISTRY`'s 17 engines, the carved `risk-guards-local` overlays per
`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § H.5) — their absence from the artefact is
purely a documentation gap, which is why they're todos in § B rather than cross-references here.

## Disposition of todos moved by the 2026-08-18 split

Every todo below left this plan for a child in the table above. Recorded as SUPERSEDED dispositions rather than
deleted, so the todo total is conserved and each one stays traceable to where it now lives.

- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix the instruction-type count in `strategy-service-walkthrough.html` §01/§03" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix §02's strategy-family list" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Soften §11 "Automated movement"" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "REVISED 2026-08-18 — the original custody finding was a FALSE POSITIVE; do not "fix"…" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix the stale §05→§08 cross-reference" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Soften §12's capital-budget "enforced by construction" claim" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add a caveat near §08/§09's hard equality claim" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add a scope statement near the top of `strategy-service-walkthrough.html`" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add a one-line carve/hosted split note to §09" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add mirrored-custody routing content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add funding-route / per-client custody binding content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add a capability-wizard boundary note" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add rank-allocator weighting-layer content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add book-level overlay content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Name the "strategy reads only processed data, never MTDS directly" invariant explicitly" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add fee/gas-as-decision-input content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P3. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Extend §03's `AtomicInstruction` block with a one-line worked example" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Rewrite §2/§3's external-API status framing" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix §4's four-state coverage table" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Reconcile the 288-venue figure" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix §14's "19-step contract" mislabel" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Qualify §16's "a great deal of testnet work is already complete"" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P3. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Scope §5's "every figure is pending measurement" lede" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add the 7 fully-absent capability sections" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add the 4 present-thin capability sections" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Name MDPS/features-service explicitly as the intermediary" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Introduce the evidence-tier axis in both artefacts" now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Tag every claim-bearing section in both artefacts with an evidence tier." now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Re-grade all `live` badges against the stricter definition" now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Audit the inherited glossary / canonical-instrument-ID material (Axis 0)." now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Audit the archetype-readiness (batch/paper/live) content" now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Ground or cut the forward claim" now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[RESEARCH] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "**Research real per-venue transfer rails / custody eligibility / colla" now tracked in `retained in this plan (spec/tooling)`.**
- **[SCRIPT] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Add a QG check validating artefact-quoted enum data against the UAC enums" now tracked in `retained in this plan (spec/tooling)`.**
- **[REVIEW] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Re-verify the six audit findings the audit itself did NOT independently check." now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[REVIEW] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Audit the four sibling client artefacts never covered" now tracked in `client_artefact_remediation_siblings_2026_08_18`.**
- **[REVIEW] P2. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Cross-document consistency sweep across all six artefacts." now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "STOP-SHIP: the banned client name appears 6× in `strategy-service-deep-dive.html`." now tracked in `client_artefact_remediation_siblings_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Performance figures in two client documents" now tracked in `client_artefact_remediation_siblings_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "`platform-architecture.html` asserts the staked-basis structure as present-tense capa…" now tracked in `client_artefact_remediation_siblings_2026_08_18`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "The invented strategy family is in THREE documents, not one." now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "RESOLVED VERDICT — every `live` badge downgrades to `partial`." now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[DOC] P0. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "RESOLVED VERDICT — cut the forward claim." now tracked in `client_artefact_remediation_nickai_2026_08_18`.**
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Fix the CeFi spot-pair instrument-ID example in BOTH artefacts" now tracked in `client_artefact_remediation_elysium_2026_08_18 + client_artefact_remediation_nickai_2026_08_18 (decomposed per file)`.**
- **[REVIEW] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Reconcile the two re-verification findings that did NOT confirm." now tracked in `client_artefact_remediation_elysium_2026_08_18`.**
- **[PROCESS] P1. CANCELLED — SUPERSEDED 2026-08-18 (split by artefact, per operator ruling): "Bring the four sibling artefacts under a tracked owner permanently" now tracked in `client_artefact_remediation_siblings_2026_08_18`.**

## Progress Log

**2026-08-18 — authored**, immediately following
[`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md),
per operator direction to produce a triage-ready dispatch plan for the agent-orchestrator fleet. `sequential: true`
because every todo touches one of only two files. Deliberately excludes any todo that would build new system
functionality — those gaps are cross-referenced to their existing tracked items (§ "Real system gaps") rather than
duplicated, per the workspace's plan-authoring HARD RULE that a plan references other plans/epics rather than
re-deriving their content.

**2026-08-18 — all 4 spec/tooling todos shipped; plan now fully done (0 open todos).** Owner-mark spec (rule 13),
disclosure checker + enum-drift checker (both wired into `run_hygiene_sweep.sh`), and the transfer/custody/
collateral research doc all landed — see each todo's own evidence above. Note the "sequential: true because every
todo touches one of only two files" sentence two paragraphs up is now stale prose left over from before the
2026-08-18 split — this plan hasn't held an HTML-editing todo since the split table above was introduced; kept
unedited here as historical record of why the plan was originally authored that way, not as current guidance. The
gated finalize companion,
[`client_artefact_remediation_finalize_2026_08_18.md`](/plans/active/client_artefact_remediation_finalize_2026_08_18.md),
is now unblocked — its own todos (reconcile evidence back into the audit report, re-check the "Real system gaps"
list, archive this plan) are outside this session's scope (spec/tooling only, no artefact HTML) and were not
started here.

## Progress Log (context-scout)

- **context-scout 2026-08-19**: reviewed; context_scope unchanged (5 entries) — plan is fully done (0 open todos),
  the existing audit-report + two-owning-plan + epic list still covers what a reader needs before touching the
  "Real system gaps" cross-references or the pending finalize.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries) — dropped
  `elysium_carveout_stubbed_strategy_service_2026_08_12.md` (not cited anywhere in this doc's own body text, only
  in frontmatter `related`); added this doc's two actually-shipped source-code deliverables,
  `scripts/plan-hygiene/check_artefact_disclosure.py` and `scripts/plan-hygiene/check_artefact_enum_drift.py` (the
  P0/P1 SCRIPT todos' real code targets, both wired into `run_hygiene_sweep.sh`), so the list isn't codex/plan-only
  despite this being a spec+tooling gate doc. Unconfirmed suggestion not added: `_ssot-rules/13-artefact-claim-
  marks.md` (the owner-mark spec this doc defines) is a real, cited codex path but was left out to stay within the
  2-6 target once the two script paths were added.
