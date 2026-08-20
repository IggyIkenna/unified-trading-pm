---
doc_type: audit-result
title: Nick AI platform + Elysium strategy-service walkthroughs — completeness, accuracy, target-state fidelity audit
summary: >-
  Three-axis audit (missing capability / accuracy / target-state fidelity) of the two committed client-disclosure
  artefacts — platform-external-api-walkthrough.html (Nick AI, open disclosure) and strategy-service-walkthrough.html
  (Elysium, guarded carve-out) — against the real system and against the plans that govern them. Dispatched as 4
  parallel sub-agents (2 per artefact, split by axis), each carrying SUB_AGENT_MANDATORY_RULES.md and the ground
  truth from the owning plans; the orchestrating session then ran an independent verification pass that surfaced one
  material correction the sub-agents' own ground-truth snapshot had gone stale on (the Nick AI external-API build
  landed the same day as, but after, the pre-audit both agents relied on). No hard disclosure-boundary violation
  found in either artefact; both have real, material accuracy and completeness gaps, detailed below.
status: pass
nature: record
audited_scope: >-
  platform-external-api-walkthrough.html and strategy-service-walkthrough.html — completeness against
  system_readiness_master.md's 21 workstreams, accuracy against code and measured coverage/readiness data,
  target-state fidelity against the 4 load-bearing corpus findings and named operator rulings, and disclosure-
  boundary compliance for both artefacts' distinct rules.
date: 2026-08-18
auditor: >-
  4 parallel general-purpose sub-agents (sonnet, high effort), dispatched from an interactive session, plus an
  independent verification pass by the orchestrating session (code reads against strategy-service, execution-service,
  instruments-service, market-tick-data-service, unified-api-contracts).
severity: P0
parent_epic: system_readiness_master
resulting_plan: /plans/active/client_artefact_remediation_2026_08_18.md
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi]
stage: [data, strategy, execution, meta]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [client-disclosure, nick-ai, elysium, audit, accuracy, target-state-fidelity, disclosure-boundary]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/client_artefact_remediation_2026_08_18.md,
  ]
created: 2026-08-18
source: >-
  Operator direction 2026-08-18, interactive session. "so all these can use sub agents and verify their work with
  your own pass" — 4 sub-agents dispatched (2 per artefact × missing-capability/disclosure + accuracy/target-state),
  orchestrating session ran its own verification pass on the highest-severity findings before writing this report.
context_scope:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# Nick AI + Elysium artefact audit — 2026-08-18

**Do not edit either HTML from this report.** Per both owning plans, the operator reviews all numbers/claims before
they reach a client document. This is a findings report only.

## Method note

4 sub-agents ran in parallel: Nick-AI-missing-capability+disclosure, Nick-AI-accuracy+target-state,
Elysium-missing-capability+disclosure, Elysium-accuracy+target-state. Each read its artefact in full, the owning
plan(s) in full, and the capability epic, then verified claims against code or the plans' own measured ground truth.
The orchestrating session then independently re-verified the highest-severity findings by reading code directly
(UAC `schemas.py`/`enums.py`, execution-service's `transfer_coordinator.py`/`custody/factory.py`, and the three
services' `api/main.py` + router files) — **this surfaced one correction to the sub-agents' own ground truth**,
recorded in Nick AI § Axis 2 below.

---

## Disclosure-boundary findings — READ THIS SECTION FIRST

**No hard rule violation found in either artefact.** No commercial figures, no ClearLoop naming, no strategy-alpha
disclosure, no performance figures, no advocacy language in either document. Both sub-agents grepped exhaustively
for every named term in each artefact's boundary rules; the orchestrating session independently confirmed the
ClearLoop-naming and commercial-figure checks by grepping both HTML files and the fleet for "clearloop"/"$"/"budget"
directly.

Two **moderate pre-send risks** on the Elysium artefact, neither a rule violation but both worth the operator's
attention before this document goes anywhere near a client:

1. **`strategy-service-walkthrough.html` never names "Elysium" anywhere** (grep-confirmed: 0 hits) and carries no
   hosted-vs-carved scope statement at all — no sentence anywhere states whether this document describes the full
   production repository or a specific client's contracted carve-out. Concretely, §06 discusses live Jupiter/Kamino
   wiring, both explicitly OUT of the Elysium carve-out's A3 venue/asset scope (CEX-only, 4 venues, BTC/ETH/SOL,
   Lido-only staking) — **not a violation**, because per the October-delivery plan §E this walkthrough appears to be
   the *full-repository-send* artefact (voluntary, broader disclosure), not the narrower future carve-out package —
   but nothing in the corpus currently states which artefact is which, and a future editor could easily "fix" this
   document by wrongly narrowing it to the carve-out's scope. **Recommend**: add one sentence near the top stating
   this describes the full production repository and its intended audience/use, distinct from the future carve-out
   package.
2. **§09 "Reconciliation — the engines and the scenarios" carries real depth (nine named engines, the
   `ReconciliationSnapshot` field set, the three-gate auto-correction logic) with no carve/hosted split**, even
   though the carve-out plan names `TreasuryService`/`ReconciliationService` as the specific territory to ship inert
   because "this is where the newest IP sits." Most of §09 (position/fee/PnL reconciliation) plausibly sits on the
   disclosed "strategy decides" side, but `balance_reconciliation_engine`/`transfer_reconciler` sit closer to the
   withheld custody/treasury domain, and nothing in the section marks the boundary. **Recommend**: a one-line scope
   note distinguishing strategy-owned book-check reconciliation from custodian-spanning balance/transfer
   reconciliation — relevant primarily if/when this content is reused for the future carve-out artefact, since (per
   finding 1) this document may currently be the intentionally-broader full-repo-send artefact.

---

## Section 1 — Nick AI platform artefact (`platform-external-api-walkthrough.html`)

### Axis 1 — Missing capability (14 probes against `system_readiness_master.md`)

| # | Probe | Verdict | Note |
| --- | --- | --- | --- |
| 1 | Fee/gas breakdown (W17) | **absent** | Zero mentions anywhere. Draft copy prepared (see full sub-agent report). |
| 2 | Transfer rails/custody eligibility per venue (W5) | present-thin | Qualitative only ("exchange-internal, on-chain, or custody"); no Copper/Ceffu/IBKR/Alpaca/per-broker detail. |
| 3 | Collateral usability / cross-margin per venue (W5) | **absent** | Zero real-text mentions. |
| 4 | Batch=live determinism (ε=0) | present-thin | Property stated twice, correctly as enforced not asserted; mechanism (UTL `EventTransport`, `InMemoryTransport` vs Pub/Sub) never named. |
| 5 | Manual trade on every venue (W5, disaster path) | **absent** | Zero mentions. |
| 6 | Order lifecycle completeness (W11) | present-thin | Append-only/audited transitions stated; no creates/updates/cancels/amends vocabulary, no execution-service restart-recovery statement. |
| 7 | Reconciliation framework (W12) | **absent** | Zero mentions anywhere, despite two natural adjacent sections. |
| 8 | PnL attribution across risk/exposure dims (W13) | **absent** | Zero mentions. |
| 9 | Risk native+share-class, Greeks, DART dims (W10) | **absent** | Zero mentions — no risk-model section exists at all. |
| 10 | Per-client isolation | **present-deep** | Stated twice with real specificity, contract-layer enforcement conveyed without naming the internal class — appropriate restraint under the code-snippet boundary. |
| 11 | Strategy wizard agent-drivable (W6) | **present-deep** | One of the strongest sections in the document; near-verbatim match to the probe's own framing. |
| 12 | Chained atomic sequences + 3 execution depths | present-thin | Three-depths table and chained-sequence framing present; the operator's own named example (TWAP vs straight market) only half-shown — "TWAP" itself never appears. |
| 13 | Venue universe breadth (660 triples / 288 venues) | **present-deep** | Matches the epic's freshest 2026-08-17/18 landing exactly; correctly supersedes the plan's original pre-audit's 3-unit ambiguity with one fresh, internally-consistent denominator (verified: the per-AG breakdown sums to 288 exactly). One open question worth being able to answer if asked: why 288 differs from the pre-audit's 151/183 (different measurement — the readiness-dump's manifest walk vs. the AG-summed venue count, and 288 includes a 24-venue "Unattributed" bucket the AG sums never had). |
| 14 | Latency/tracing, preflight, staleness SLAs (W16) | **absent** | Zero mentions. |

**Tally: present-deep 3, present-thin 4, absent 7.** Pattern: contract-*shape* content (wizard, per-client isolation,
venue-universe measurement) is present-deep — exactly what the pre-audit measured most thoroughly. Operational-
*completeness* content (fees, manual-trade fallback, reconciliation, PnL attribution, risk/Greeks, latency/SLA) is
uniformly absent — these map directly onto `system_readiness_master.md` W10/W12/W13/W16/W17, none of which have any
P0 item checked off yet. **The artefact isn't hiding these capabilities; the underlying epic hasn't landed them
yet** — this is a target-state-fidelity-consistent gap, not a writing gap, for 6 of the 7 absent items. Full draft
copy for every thin/absent probe is preserved in the sub-agent transcript and reproduced in the companion dispatch
plan's todos where it maps to net-new artefact content versus content gated on epic work landing first.

### Axis 2 — Accuracy against the current system

**Correction to the sub-agents' own ground truth, found in the orchestrating session's verification pass**: both
Nick AI sub-agents (and the pre-audit they relied on, dated 2026-08-16) treated "the external HTTP layer exposing
[the contracts] to a counterparty does not exist today" as current fact. **This is now stale.** A same-day follow-up
plan, [`nick_ai_platform_readiness_remediation_2026_08_16.md`](/plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md)
W1, built and shipped real external routers **after** the pre-audit ran — independently re-confirmed by direct code
read just now:

- `instruments-service/instruments_service/api/routers/external.py` (live) — `GET /v1/instruments` (catalogue query)
  and `GET /v1/instruments/bulk` (streamed parquet dump), auth via UTL `create_api_auth` (X-Service-Token /
  X-API-Key / Bearer JWT with `org_id`+`subscription_tier`) — evidenced live against real prod GCS data
  (`instruments-service@2fcf7a19`).
- `market-tick-data-service/market_tick_data_service/api/routers/external.py` (live, 310 lines) —
  `GET /external/market-data/availability`, `GET /external/market-data/delivery/batch`,
  `GET /external/market-data/delivery/stream` — same auth pattern (`market-tick-data-service@6fefa63676`).
- `execution-service/execution_service/api/external_instruction_api.py` (live) — `POST /external/instructions`;
  **TRADE routes through the real handler** (`ManualOperationHandler` → `LiveOrchestrator.execute_instruction()`,
  the same path DART's internal manual-trade route uses), verified via a real (non-mocked) paper-mode round-trip.
  **Every other `StrategyInstructionV2` variant (SWAP/LEND/BORROW/STAKE/UNSTAKE/QUOTE/TRANSFER/BRIDGE/ATOMIC/CANCEL
  — 10 of 11 instruction types) returns an honest HTTP 501**, not a silent drop, but also not live
  (`execution-service@3567e7a180`).
- `strategy-service` still has **no** true counterparty-facing surface — its real endpoints remain admin-token-gated
  internal tooling (registry reads, restriction-profile router, operational-mode flip), unchanged since the
  pre-audit.

**Revised verdict on §2/§3's "live" badges**: neither sub-agent's recommendation to downgrade §2 to `planned` is
correct as stated — the external layer is now substantively real for 2 of 4 target services and partially real for a
third. But the artefact still **overstates** in a different way: §2 says "you get the contract our own execution
service gets," which is not yet true for 10 of 11 instruction types (only TRADE is live end-to-end; the rest 501).
**Corrected finding**: §2/§3 should name the concrete live surface (2 read endpoints on instruments-service, 3 on
MTDS, 1 write endpoint on execution-service) and state plainly that only TRADE instructions are live through the
external endpoint today — the other 10 types return 501, not a silent no-op, but not "the same contract" either.
strategy-service's external surface remains genuinely unbuilt and should still be named as `planned`.

Other verified findings (sub-agent-sourced, orchestrating session did not independently re-check each one — see full
sub-agent transcripts for evidence trails):

- **660 triples / 48.54% / 3,960 shards / 288 venues (§4 stat-row)** — **CONFIRMED**, correctly using the freshest
  (2026-08-18) figures over the plan's own slightly older 48.40%/118,842,731.
- **288-venue figure presented alone**, with no cross-reference to the pre-audit's own explicit instruction to state
  all three legitimately-different venue-count units side by side (151 canonical / 183 physical / "158-84" stale) —
  **CORRECTED**: either reconcile all units in one place, or scope "288" explicitly as "venues in the 2026-08-18
  coverage manifest at readiness-dump grain, not directly comparable to the registry-declared counts."
- **§4's four-state coverage table internally contradicts its own denominator formula**: the table marks "Expected,
  absent" (i.e. `empty_confirmed`) as counting against coverage ("Yes"), while the "How to read 48.54%" callout two
  paragraphs later defines the denominator as `captured + attempted-failed + expected-unattempted` only — **verified
  directly against the HTML** (lines 508-512 vs 536-542) — `empty_confirmed` does not appear in the stated formula
  at all. **CORRECTED**: either add the missing state to the table with its correct denominator treatment, or
  reconcile the "Yes" verdict with the formula so the two don't contradict.
- **§14's "19-step contract" language sits directly above the 864-row/0-844-20 numbers**, but those numbers were
  produced by the readiness-state-dump skill's **8-leg** model, a different framework from the 19-step contract used
  in the pre-audit's own §5 — **CORRECTED**: name the 8-leg framework that actually produced the quoted rollup.
- **§16 "a great deal of testnet work is already complete"** stated unqualified — **CORRECTED**: real gaps exist
  (no per-venue cefi testnet declaration, sports' live credential probe entirely stubbed, tradfi's only live probe
  covers Tardis only, Polymarket has no testnet and no written paper-trading ruling) alongside real progress (AAVE
  Sepolia, Solana LST devnet, Kalshi demo host); recommend qualifying rather than a blanket "already complete."
- **§5's "every figure is pending measurement" lede** sits above tree summaries showing real, already-measured
  readiness splits — **CORRECTED (minor)**: scope the "pending" claim to the coverage-percentage cells only.

### Axis 3 — Target-state fidelity

**The 4 load-bearing findings — all 4 respected, verified against exact HTML text**:
1. Path canonicalisation failure (113 non-canonical, 13× active casing regression) — stated in §14, per-AG
   breakdown matches the corpus finding verbatim, no stray "canonical" claim found anywhere else in the document.
2. Prediction's active capture outage — stated in §14 ("8 days and counting"), no coverage percentage asserted
   anywhere for prediction.
3. Corporate-actions banned-vendor — vacuously respected (zero mentions of corporate actions anywhere).
4. 8 unattributed venues — disclosed twice (prose + a labeled table row), the strongest of the four.

**Operator rulings**:
- **Readiness derived, never declared** — landed cleanly and consistently; every readiness figure checked shows
  `unverified` as its own state.
- **Strategy reads only processed data, never MTDS directly** — **DRIFT-RISK, not a hard violation**. §1's
  architecture diagram/table collapses MTDS+MDPS+features into one undifferentiated "Market data" box with a direct
  arrow to "Strategy," and neither MDPS, features-service, MTDS, Pub/Sub, nor GCS is named anywhere as the actual
  access pattern (grep-confirmed). Nothing explicitly claims a direct call, but the simplification could read that
  way to the artefact's own stated AI-orchestrated audience. Recommend naming the intermediary layer explicitly.
- **Modes batch\|paper\|live, testnet a paper sub-mode** — landed exactly; §14's table shows testnet correctly
  folded into paper's "needs" column, no fourth mode anywhere.

---

## Section 2 — Elysium strategy-service walkthrough (`strategy-service-walkthrough.html`)

### Axis 1 — Missing capability (13 probes against the carve-out plan's "full-picture surface" + relevant epic W-items)

| # | Probe | Verdict | Note |
| --- | --- | --- | --- |
| 1 | Mirrored-custody routing (Copper/Ceffu) | **absent** | `COPPER_MPC` named as a signing surface; the two-custodian mirroring model itself is not — "Ceffu" has 0 hits. |
| 2 | Funding-route graph / per-client custody binding (`WalletMappingConfig`) | **absent** | §11 describes a different, narrower per-(client,slot) wallet concept; the route-feasibility graph itself is absent. |
| 3 | Capability wizard / restriction graph | **absent** | §04's "wizard" is the per-archetype param-schema wizard, a different thing from the capability/eligibility wizard the carve-out plan means (which per H.11's correction mostly lives outside strategy-service anyway). |
| 4 | ADV-ranked dynamic universe (default ON since 2026-08-12) | present-thin | Mechanism described without naming it as "ADV" or stating it's now the running default rather than an optional mode. |
| 5 | Rank-allocator weighting layer (17 engines) | **absent** | "allocator" appears only referring to the *client* as capital allocator, never the rank-allocation engine concept. |
| 6 | Book-level overlays (vol-target, beta-hedge, no-trade band, rank-buffer) | **absent** | Zero mentions of any of the four; §12's per-position limits are adjacent but not the same thing. |
| 7 | Venue/instrument capabilities (frozen collateral/margin per A2) | present-thin | Field names present (`collateral_health_min`); no specific structures (`LST_AS_MARGIN` vs `USDC_MARGIN_BUFFERED`), haircuts, or "this is the frozen answer for these venues" framing. |
| 8 | Batch=live determinism (ε=0) | **present-deep** | §09 gives the actual decomposition mechanism (`live − batch = (paper − batch) + (live − paper)`) with the hard-equality rationale — genuinely strong. One stale cross-reference: §05 points to "§08" for this proof; it's actually in §09. |
| 9 | Fee/gas breakdown (W17) baked into decisions | present-thin | Gas appears only in transfer-automation context; fees appear only as a reconciled/monitored quantity, not a decision input. |
| 10 | Canonical output paths (W18) | **absent** | Zero mentions, despite the document's own live/partial/planned status-marking rigor being exactly the kind of precision that would make this credible. |
| 11 | PnL attribution across risk/exposure dims (W13) | present-thin | Real identity-axis attribution (venue/account/client/instrument/slot); no risk-metric or exposure-normalisation axis. |
| 12 | Per-client isolation | **present-deep** | Strongly stated, matches the codex SSOT precisely, states the mechanism's substance without naming the internal exception class. |
| 13 | Chained atomic sequences (`AtomicInstruction`) | present-thin | `AtomicInstruction` shown with only a one-line comment; real depth on chained-sequence *reasoning* exists elsewhere (§12's emergency-flatten worked example) but isn't connected to the schema. |

**Tally: present-deep 2, present-thin 6, absent 5.**

### Axis 2 — Accuracy against the current system

**Two fresh, previously-uncaught inaccuracies, both independently confirmed by the orchestrating session's own code
read (not just trusted from the sub-agent report)**:

1. **Instruction-type count: artefact says 9, code has 11.** §01's stat-row and §03's heading both say "9
   Instruction types" / "The nine action types" and enumerate exactly 9 — missing `TransferInstructionV2` and
   `BridgeInstructionV2`. **Verified directly**: `unified-api-contracts/unified_api_contracts/internal/
   architecture_v2/schemas.py` declares 11 `StrategyInstructionEnvelope` subclasses (confirmed by grepping every
   `class ... (StrategyInstructionEnvelope)` declaration and the `StrategyInstructionV2` union, which lists all 11
   by name). The October-delivery plan's own claims-audit table verified "11 instruction types" as **VERIFIED** —
   but against the *deep-dive* sibling document, not this walkthrough; this walkthrough was never checked against
   that finding and independently states a wrong count.
2. **Strategy families: still shows the invented "Liquidity provision" family, still says 5 families.** §02's
   keypoints list exactly: Carry, Dispersion, Volatility, **"Liquidity provision"**, Event-driven. **Verified
   directly**: `StrategyFamily(StrEnum)` in `unified-api-contracts/.../architecture_v2/enums.py` has 9 members —
   `ML_DIRECTIONAL, RULES_DIRECTIONAL, CARRY_AND_YIELD, ARBITRAGE_STRUCTURAL, MARKET_MAKING, EVENT_DRIVEN,
   VOL_TRADING, STAT_ARB_PAIRS, PORTFOLIO` — the enum's own docstring says "9 orthogonal families" and explicitly
   documents that a 17-member v1 enum was deleted 2026-04-21. **No member is named or maps to "Liquidity provision,"
   "Carry," or "Dispersion" as separate families** (they're folded into `CARRY_AND_YIELD` and `VOL_TRADING`
   respectively). This is exactly the "WAS WRONG" defect the October-delivery plan's §F already found and marked
   corrected — **but that correction was applied to `strategy-service-deep-dive.html`, a sibling document, and never
   reached this walkthrough**, which still carries the original, invented family and the wrong count. This is the
   single clearest doc-drift finding across both artefacts in this audit.

**Transfer handlers — the plan's highest-risk finding, re-verified live against today's code, confirmed still
open**: §11 "Automated movement" presents dust sweep, gas top-up/floor, and inter-wallet rebalance as functioning
capability, unhedged, under a "partial" status badge. **Verified directly against
`execution-service/execution_service/transfer_coordinator.py`**:
- `_ensure_default_handlers()` auto-registers **only** `BusTransferType.SUBACCOUNT_MOVE`.
- `CEX_WITHDRAW` carries an inline comment: **"NOT WIRED"** (dated 2026-08-16, two days before this audit).
- Gas top-up/gas floor: **no handler, no reserve-threshold logic anywhere in the codebase** — only an unenforced
  classifier tag exists.
- `REBALANCE` is enum-only, zero handlers.
- `TransferCoordinator` is **never instantiated in production code** (`grep "TransferCoordinator(" -- ':!tests/'`
  returns nothing).
This matches — and arguably understates — the October-delivery plan's own framing: "a stub returning success on a
funds-movement path reports money moved that did not move — the highest-risk item in this plan," still an open,
unchecked P0 todo there. The artefact's "partial" badge implies a working subset; the measured reality is closer to
no production entry point at all for anything the section describes as automated.

**Custody provider list: verbatim-accurate as a code quote, materially misleading as documentation.** §11's
`SigningSurface` code block (LOCAL_KEY, CLOUD_KMS_ENCRYPTED, COPPER_MPC, FIREBLOCKS_MPC, MOCK) is byte-for-byte
correct against `unified-api-contracts/.../domain/defi/wallet_config.py`. **But**
`execution-service/execution_service/custody/factory.py`'s real, working `get_custody_provider()` branches are
`mock, local_key, cloud_kms, copper, ceffu` — **verified directly**: no `fireblocks` branch exists (calling it
raises `ValueError`; its own docstring flags it as a "June-1 client-credential flip target" that never landed), and
**Ceffu — a real, working provider — has no `SigningSurface` member at all**. The artefact accurately quotes a type
that doesn't match the working implementation roster.

**Lower-severity, previously-flagged (sub-agent-sourced, not independently re-verified by the orchestrating session
beyond spot-checking the confirmed-clean items)**:
- Targets-not-deltas, atomic multi-leg (schema-level), cross-client-transfer-impossible, attestation-softened-
  correctly, archetype counts (60/32) — all **CONFIRMED** clean.
- Capital budget "enforced by construction" — the artefact's wallet-funding framing is a narrower, more defensible
  claim than the plan's still-`UNVERIFIED` "capital_budget_amount is enforced" line, but worth a second look before
  the repository ships given the overlap.
- §09's hard `paper == batch-rerun` equality claim sits undisclosed next to §08's now-default-ON dynamic universe,
  which per the October-delivery plan §H.8 (still open P0) currently lacks the manifest-pinning needed to guarantee
  that exact equality — the artefact should not present this as unconditionally settled while that gap is open.

### Axis 3 — Target-state fidelity

**The 4 load-bearing findings** — not relevant to this artefact's content (no path/manifest/prediction/corporate-
actions discussion anywhere); correctly out of scope, not a compliance gap.

**Operator rulings**:
- **Readiness derived, never declared** — **CONFIRMED**, landed near-verbatim in §18.
- **Strategy reads only processed data, never MTDS directly** — **NOT STATED anywhere** (grep-confirmed zero hits
  for MDPS/features-service/Pub-Sub/MTDS/market-tick-data/market-data-processing). §01 says only "it consumes
  features and market state" — compatible with the rule but doesn't make the load-bearing assertion. Given this is
  the natural home for this invariant, its silent omission is a real gap.
- **Modes batch\|paper\|live, testnet a paper sub-mode** — **CONFIRMED, strong match**, including a dedicated
  subsection on why testnet is a sub-mode, tied to the determinism proof.
- **Risk limits ship as our live values** — **CONFIRMED, consistently framed** ("our own operating values rather
  than conservative defaults... not a calibration to someone else's balance sheet"), matching the 2026-08-16 ruling
  closely. No numeric values are shown anywhere in the artefact (only field names), so there's nothing to check for
  stale-placeholder-vs-real; the framing is right, the "numbers" half has no content to verify.
- **"Betfair/ibkr/polymarket ship as-is"** — grepped broadly, no exact ruling text located under this phrasing, and
  this artefact never mentions betfair/ibkr/polymarket at all (CeFi/DeFi carry-only content). **Out of scope for
  this artefact**, likely governs a different (sports/prediction/tradfi) artefact not in this audit's scope.

**Archetype/venue scope — important clarification, not a violation**: `CARRY_FUNDING_DISPERSION` is confirmed
**still fully live in production** (factory-registered, has a `PARAM_SCHEMA_REGISTRY` entry and an allocator rank
entry). The 2026-08-16 "ruled OUT" decision applies specifically to the **separate, not-yet-started, `status: draft`
carve-out package** (`elysium_carveout_stubbed_strategy_service_2026_08_12.md` §A2/A3) — this walkthrough is not
that package. Per the October-delivery plan §E, the full-repository send is meant to disclose all nine families
voluntarily. The walkthrough's broader scope (venue/family breadth beyond the carve-out's A2/A3 narrowing) is
therefore consistent with its likely role as the full-repo-send artefact, **not** scope drift — but this reinforces
disclosure-boundary finding 1 above: nothing in the corpus currently states which artefact plays which role, and a
future editor could wrongly narrow this document to the carve-out's tighter scope.

---

## Summary table — severity-ranked, both artefacts

| Severity | Finding | Artefact | Axis | Status |
| --- | --- | --- | --- | --- |
| P0 | Instruction-type count wrong (9 vs 11), 2 real types missing from §03 | Elysium | Accuracy | ✅ RESOLVED 2026-08-19 — §01/§03 now state 11 (`unified-trading-pm@171dc40739`); live-verified "The eleven action types" |
| P0 | Invented "Liquidity provision" strategy family still shown; 5 vs real 9 families | Elysium | Accuracy | ✅ RESOLVED 2026-08-19 — §02 lists the 9 real `StrategyFamily` members (`@171dc40739`); the one remaining "Liquidity provision" mention describes the removal, not a recurrence |
| P0 | §11 "Automated movement" overstates reachability — no production transfer path exists | Elysium | Accuracy | ✅ RESOLVED 2026-08-19 — reworded to "specified as a target state, mostly not yet wired" with explicit NOT-WIRED caveats (`@171dc40739`) |
| P0 | §2/§3 external-API "live" badge doesn't disclose the TRADE-only-live / 10-of-11-types-501 reality | Nick AI | Accuracy | ✅ RESOLVED 2026-08-19 — names the concrete live surface, states TRADE-only-live / 10-of-11 return 501 (`@ec08cccad1`) |
| P1 | §4 coverage table internally contradicts its own denominator formula | Nick AI | Accuracy | ✅ RESOLVED 2026-08-19 — table/formula reconciled (`@ec08cccad1`) |
| P1 | Custody `SigningSurface` list (shows Fireblocks, omits Ceffu) doesn't match the working provider roster | Elysium | Accuracy | ✅ RESOLVED 2026-08-19 — FALSE POSITIVE: Ceffu stub routes via Copper (`CEFFU_ROUTES_VIA_COPPER_NOTE`), Fireblocks `SigningSurfaceStatus.OUT_OF_SCOPE`; explanatory note added, enum list deliberately untouched (`@171dc40739`) |
| P1 | "Strategy never reads MTDS directly" invariant unstated in both artefacts | Both | Target-state | ✅ RESOLVED 2026-08-19 — Elysium names it explicitly (`@171dc40739`); Nick AI names MDPS/features-service as the intermediary (`@ec08cccad1`) |
| P1 | No artefact scope statement distinguishing full-repo-send vs future carve-out | Elysium | Disclosure (moderate) | ✅ RESOLVED 2026-08-19 — full-repository scope statement added near top (`@171dc40739`) |
| P1 | §09 reconciliation detail has no carve/hosted split vs withheld IP | Elysium | Disclosure (moderate) | ✅ RESOLVED 2026-08-19 — carve/hosted split note added (`@171dc40739`) |
| P2 | 7 of 14 Nick AI missing-capability probes fully absent (fees, collateral, manual-trade, reconciliation, PnL, risk/Greeks, latency/SLA) | Nick AI | Missing capability | ✅ RESOLVED 2026-08-19 — §18-§24 added as target-state, `st-plan` (`@2b0c327e44`) |
| P2 | 5 of 13 Elysium missing-capability probes fully absent (custody routing, funding graph, wizard, rank-allocator, overlays) | Elysium | Missing capability | ✅ RESOLVED 2026-08-19 — mirrored-custody, funding-route, wizard note, allocator, overlays all present (`@6a5598e736`) |
| P3 | §05→§08 stale cross-reference (should be §09) | Elysium | Accuracy (minor) | ✅ RESOLVED 2026-08-19 — `@171dc40739` |
| P3 | §14 "19-step contract" mislabels the 8-leg framework that produced the quoted numbers | Nick AI | Accuracy (minor) | ✅ RESOLVED 2026-08-19 — now names the 8-leg readiness-dump framework (`@ec08cccad1`) |

## Progress Log

**2026-08-18 — audit complete.** 4 sub-agents dispatched in parallel (general-purpose, sonnet, high effort,
`SUB_AGENT_MANDATORY_RULES.md` pasted at spawn), each given the owning plans' full text as ground truth plus
instructions to verify against code directly. Orchestrating session independently re-verified the highest-severity
findings (instruction-type count, strategy-family count, transfer-handler stub state, custody-provider mismatch, and
critically the Nick AI external-API-surface claim) via direct code reads, which surfaced one material staleness in
the sub-agents' own ground truth — the pre-audit's "no external HTTP layer exists" finding had already been
superseded by same-day remediation work by the time this audit ran. Corrected in Section 1 § Axis 2 above rather
than left as the sub-agent's original (now-wrong) recommendation. Companion dispatch plan authored at
[`/plans/active/client_artefact_remediation_2026_08_18.md`](/plans/active/client_artefact_remediation_2026_08_18.md)
per operator direction to hand this off to the agent-orchestrator fleet for triage and execution.

**2026-08-19 — reconciled by the finalize pass
([`client_artefact_remediation_finalize_2026_08_18.md`](/plans/active/client_artefact_remediation_finalize_2026_08_18.md)).**
Every checked todo in the parent remediation plan + all three children (elysium/nickai/siblings) re-verified against
the live HTML and cited commits — not checkbox text alone. All 13 summary-table findings below are **RESOLVED**:
live grep of both walkthroughs confirms the fixes (eleven action types; §02's 9 real `StrategyFamily` members; §11
"specified as a target state, mostly not yet wired"; TRADE-only / 501 disclosure; §14 names the 8-leg framework;
evidence-tier `.ev-*` legend + `.own` owner marks in both files), all 14 cited SHAs resolve on
`origin/live-defi-rollout`, and the two wired hygiene checkers run green
(`check_artefact_disclosure.py`: 0 hard violations; `check_artefact_enum_drift.py`: 0 violations, real enum counts
9/11). `status` flipped `partial`→`pass` (the audit-result status enum is `fail/partial/pass`) — this marks the two audited walkthroughs' findings addressed, NOT the
underlying system gaps (W5/W10/W12/W13/W16/W17/W18) the parent plan cross-references, which remain tracked and open
in `system_readiness_master.md` / `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`.

**2026-08-19 (slot 1)** — Landed here independently via `client_artefact_remediation_elysium_finalize_2026_08_18.md`
item 3, at the same time as the broader parent-level finalize pass above; that pass's reconciliation is a superset
(covers both artefacts + a `status` flip) of what this session's own edit would have added, so this session's
redundant table edit was dropped on rebase in favor of the parent pass — see that plan's own Progress Log for the
resulting checkbox citation.
