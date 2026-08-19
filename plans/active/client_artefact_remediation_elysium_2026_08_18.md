---
doc_type: plan
title: Client artefact remediation — Elysium strategy-service walkthrough
summary: >-
  All remediation touching strategy-service-walkthrough.html only — accuracy fixes, disclosure and completeness
  additions, the live re-grade, and the evidence-tier tagging for this one file. Split out of
  client_artefact_remediation_2026_08_18.md so it runs in parallel with the Nick AI and sibling children; the file
  scope is what makes that safe, since no other child edits this HTML.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, elysium, artifact-remediation, audit-followup]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/audit/results/client_artefact_live_regrade_2026_08_18.md,
    /plans/audit/results/client_artefact_axis0_content_verification_2026_08_18.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
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
  Todos MOVED here from the parent's § A and § B plus the Elysium-scoped items of § E and § F — moved, not copied,
  so no todo is tracked in two places.
context_scope:
  [
    /plans/active/client_artefact_remediation_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
---

# Client artefact remediation — Elysium strategy-service walkthrough

**File owned by this plan**: `codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` — and
nothing else. No other remediation child edits it. Gated on the parent only for the evidence-tier spec.

Full evidence for every finding is in the audit reports listed in `related:`. Do not restate their reasoning here.

## Accuracy fixes

- [x] [DOC] P0. ✅ **Fix the instruction-type count in §01/§03** — says "9 Instruction types" / "The nine action
      types" and enumerates 9; the real `StrategyInstructionV2` union has **11**, missing `TransferInstructionV2`
      and `BridgeInstructionV2`. `/codex/04-architecture/strategy-execution-protocol.md` has correctly said 11 all
      along, so the codex was right and only this document drifted. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Fix §02's strategy-family list** — shows 5 families including an invented "Liquidity provision".
      The real `StrategyFamily` enum has 9 members: `ML_DIRECTIONAL, RULES_DIRECTIONAL, CARRY_AND_YIELD,
      ARBITRAGE_STRUCTURAL, MARKET_MAKING, EVENT_DRIVEN, VOL_TRADING, STAT_ARB_PAIRS, PORTFOLIO`. "Carry" and
      "Dispersion" are not separate families — they fold into `CARRY_AND_YIELD` and `VOL_TRADING`. This exact
      correction was already applied to `strategy-service-deep-dive.html` and never reached here. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Soften §11 "Automated movement"** — presented as functioning capability under a `partial` badge.
      Measured: `_ensure_default_handlers()` registers only `SUBACCOUNT_MOVE`; `CEX_WITHDRAW` is commented
      "NOT WIRED"; gas top-up/floor has no handler and no reserve-threshold logic anywhere; `REBALANCE` is
      enum-only; and `TransferCoordinator` is never instantiated in production code. The measured reality is closer
      to no production entry point at all than to a working subset. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Re-grade every `live` badge in this file to `partial`** — all 10 of them. The re-grade audit
      searched the whole workspace for positive real-capital evidence (a real fill, a mainnet transaction, a
      reconciled live P&L, a funded live client) and found none, so no section survives the conjunctive test. This
      is the definition working as designed, not a writing defect. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Add the custody explanatory note, do NOT edit the `SigningSurface` list** — the audit's original
      finding here was a FALSE POSITIVE. Ceffu is a stub ("STUB pending API spec" in the factory), its absence from
      the enum is deliberate (`CEFFU_ROUTES_VIA_COPPER_NOTE` — its signing routes via Copper), and Fireblocks is
      `SigningSurfaceStatus.OUT_OF_SCOPE`. Editing the list would make the document wrong; explain the design. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Fix the stale §05→§08 cross-reference** — the determinism proof is in §09. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Fix the CeFi spot-pair instrument-ID example** — uses instrument-type token `SPOT`; the real one
      is `SPOT_PAIR`. The other ID examples verified correct against `build_canonical_instrument_id()`, and all
      named venues are correctly bound in `VENUE_TO_ADAPTER_KEY` — one wrong token, not a systemic problem. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P0. ✅ **Remove the invented family's 2 hits in this file** (see § accuracy above) — the
      `platform-architecture.html` and `carveout-engineering.html` instances belong to the siblings child. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P2. ✅ **Soften §12's capital-budget "enforced by construction" claim** — already corrected by the prior
      slot-5 rewrite: §12 now states the per-slot-wallet enforcement claim "does not hold today," citing
      `get_trading_wallet()` having zero non-test call sites in either service. **Shipped `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Caveat the hard `paper == batch-rerun` equality near §08/§09** — present in §09 ("The equality's
      own precondition"): dynamic universe selection is on by default and the as-of-date manifest pinning the
      equality depends on is not yet built. **Shipped `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [REVIEW] P1. ✅ **Resolve the two re-verification findings that did not confirm — VERDICT: both already
      correctly reflected in the shipped file; no further edit needed.** Read
      `client_artefact_forward_claim_and_reverification_2026_08_18.md` Part (b) in full. Of the six re-verified
      findings, two touch this file and came back not-clean: item 2 (atomic multi-leg — schema enforces nothing,
      the "succeed or fail together" guarantee is an execution-service runtime property) and item 6 (capital
      budget "enforced by construction" — WRONG, neither `capital_budget_amount` nor `get_trading_wallet()` has a
      production call site). Both are already stated correctly in the live file: §03's `AtomicInstruction` callout
      says explicitly "the schema itself enforces nothing... an execution-service runtime guarantee," and §12 (see
      above) states the wallet-enforcement claim does not hold. The other four (targets-not-deltas,
      cross-client-transfer-impossible, archetype counts, attestation field population) either don't touch this
      file or are already confirmed accurate here. No text change required — verified, not just grepped.
- [x] [REVIEW] P1. ✅ **Verify §11's "Manual movement" claim — VERDICT: CONFIRMED accurate, independently traced
      against current code this session (not just trusting the file's own citation).** Read
      `execution-service/execution_service/engine/routing/handler_registry.py`: `OperationType.TRANSFER` maps to
      `TransferHandler` exactly as the file claims. Read `transfer_handler.py`: `execute()` dispatches to five real
      per-rail methods (`_execute_internal_transfer`, `_execute_cex_withdrawal`, `_execute_onchain_transfer`,
      `_execute_custody_transfer`, `_execute_bridge_transfer`), confirming "the same per-rail execution methods"
      for every transfer regardless of origin. Read `manual_pending_queue.py`: `PendingManualInstruction` wraps
      `orchestrator.StrategyInstruction`, whose fields are exactly `venue`, `instrument_id`, `side`, `quantity` —
      a verbatim match to the file's "trade-specific — venue, instrument, side, quantity" claim, and structurally
      incapable of representing a transfer (no `asset`/`venue_from`/`venue_to`/`target_balance_at_destination`).
      So the two mechanisms are correctly described as genuinely distinct: `TransferHandler` (the real, wired,
      shared dispatcher for every `TRANSFER`-type instruction, manual or automated) is not the same class as
      `TransferCoordinator` (the mostly-unwired target-state sweep/gas-topup/rebalance coordinator §11 already
      describes separately in "Automated movement"). The file's claim does not overstate reachability — it holds.

## Disclosure and completeness

- [x] [DOC] P1. ✅ **Add a scope statement near the top** stating this describes the full production repository and
      naming its intended audience — distinct from the future carve-out package. Without it a future editor could
      wrongly narrow this document to the carve-out's tighter scope. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Add a carve/hosted split note to §09** distinguishing strategy-owned position/fee/PnL
      reconciliation from custodian-spanning balance/transfer reconciliation, which sits closer to withheld IP. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P2. ✅ **Name the "strategy reads only processed data, never MTDS directly" invariant explicitly** —
      grep-confirmed absent. This document is its natural home. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P2. ✅ **Add mirrored-custody routing content (§11)** — present: "Mirrored custody: collateral stays put,
      the venue gets a credit," with a "Specified, not yet live" callout (venue-side API pending). **Shipped
      `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Add funding-route / per-client custody binding content (§11)** — present: "Funding follows the
      same binding backward through the rail set above: a `CEX_DEPOSIT` or `DEFI_DEPOSIT` targets the specific
      `(client_id, slot_label)` wallet that will trade it, not a shared pool divided afterward." **Shipped
      `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Add a capability-wizard boundary note (§04)** — present: "A separate capability wizard exists
      too, and the two should not be conflated: it walks readiness gaps across the whole capability graph... rather
      than one archetype's parameter set, which is what this wizard renders." **Shipped
      `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Add rank-allocator weighting-layer content** — present in §08: "made by a registered set of
      allocator engines, every one a subclass of one shared base... Adding a new weighting scheme is a new
      subclass, not a new allocation model bolted on beside the others" — stated as an open set, no fixed count.
      **Shipped `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Add book-level overlay content (§12)** — present: vol-target overlay and a hysteresis-band
      pattern confirmed; beta-hedge/rank-buffer at the whole-book level honestly tagged `? check` rather than
      asserted. **Shipped `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P2. ✅ **Add fee/gas-as-decision-input content (§03/§08)** — present in §08: "Fees and gas are priced
      into the decision, not just reconciled afterward," with the staked-basis `_estimate_gas_fees_apy_bps()`
      worked example. **Shipped `unified-trading-pm@6a5598e736`, verified this session.**
- [x] [DOC] P3. ✅ **Extend §03's `AtomicInstruction` block with a one-line worked example**, connecting it to
      §12's emergency-flatten reasoning — present: "a staked-basis entry pairs the stake and hedge as two legs
      sharing one `hedge_deadline_ms`... the same ordering concern §12's emergency-flatten unwind reasons about in
      reverse." **Shipped `unified-trading-pm@6a5598e736`, verified this session.**

## Evidence tiers and readiness

- [x] [DOC] P0. ✅ **Apply the parent's evidence-tier spec to every claim-bearing section in this file** — default
      `needs-check`; `machine-verified` requires naming the verifying command, skill or code symbol inline. **Shipped `unified-trading-pm@171dc40739`.**
- [x] [DOC] P1. ✅ **Give every claim-bearing section its owner mark** (workstream / plan / epic that closes it), per
      `system_readiness_master.md` W21's closure invariant. Genuinely open going into this session (grep-confirmed
      zero `.own`/`owner:` hits). Applied rule 13 in full: `.own` CSS block + legend line in the header, plus a
      badge on every section whose status is `st-part`/`st-plan` (16 of 18 — §01 carries no `.st` pill and is
      skipped per the rule), naming the closest `system_readiness_master.md` workstream or, where the gap is
      narrower than a workstream, the owning plan section (§09 → `elysium-disclosure §H.8`, §11 →
      `elysium-disclosure §C`, per the exact worked examples in rule 13 and W7). **Shipped `unified-trading-pm@8fb70b119b`.**
- [x] [DOC] P1. ✅ **Audit the archetype-readiness (batch/paper/live) content** — present in §02: derived-never-
      declared framing, the feature-groups registry now measured at 55 of 60 (up from ~40), and the per-archetype
      capability audit named explicitly as `planned`, not yet built. **Shipped `unified-trading-pm@6a5598e736`, verified this session.**

## Progress Log

**2026-08-18 — split out** of [`client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
per operator direction. Todos moved, not copied.

**context-scout 2026-08-19**: populated context_scope (4 entries) — added the owned HTML file and the
elysium-delivery plan the two open § P2 todos (§12 capital-budget, §08/§09 equality caveat) cite.

**2026-08-19 — reconciliation + owner marks.** Per-instruction Step 1, reconciled every checkbox against the live
file before starting new work: `git log` showed an unflagged prior commit
(`unified-trading-pm@6a5598e736`, slot-5, 1549 insertions) had already landed almost every remaining P2/P3 doc todo
in this plan — mirrored-custody, funding-route/custody binding, the capability-wizard note, the rank-allocator
content, book-level overlays, fee/gas-as-decision content, the AtomicInstruction worked example, the archetype-
readiness audit, the paper==batch manifest-pinning caveat, and the softened capital-budget claim. Each was verified
by opening the section and confirming intent (not just a grep hit) before flipping. Both `[REVIEW]` P1s were
resolved with an independent code trace this session (handler_registry.py / transfer_handler.py /
manual_pending_queue.py for §11; the forward-claim-and-reverification audit's Part (b) for the two findings) rather
than trusting the file's own citations. Net-new work this session: the owner-mark axis (rule 13), applied to all 16
eligible sections, `unified-trading-pm@8fb70b119b`. **Every todo in this plan is now `[x]`.** Not archived by this
session — scope was "this file only, nothing else," and archival's referrer-sweep step reaches outside that scope;
flagging for the orchestrating session to archive per the standard 6-step ritual, gated on `depends_on:
client_artefact_remediation_2026_08_18` per this plan's own frontmatter. (This session hit heavy git-index
contention from concurrent peer sessions sharing this checkout — repeated rebases shifted this same commit's SHA
three times and once fully orphaned it from branch history entirely, silently reverting this file to its pre-edit
state until a `git cherry-pick` recovered it; re-verified via `git log --grep`/`git merge-base --is-ancestor` before
every retry and before shipping, rather than trusting a stale citation or an "ahead=0" appearance of landedness.)
