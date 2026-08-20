---
doc_type: audit-result
title: Client artefact live-badge re-grade — second-pass audit 2026-08-18
summary: >-
  Re-graded every status badge (live/partial/planned) in both client-disclosure HTML artefacts against the
  2026-08-18 stricter `live` definition ("reachable on a production path AND validated with real capital"). Measured
  36 total badge instances across the two files (18 per file, including one embedded sub-badge each), not the 39
  named in the task brief — see § Measurement notes. Of the 16 top-level sections currently marked `live` (6 in the
  Nick AI artefact, 10 in the Elysium artefact — not 7/10 as briefed), every single one downgrades to `partial`
  under the strict conjunctive test: reachability holds for most of them (confirmed via the prior 2026-08-18 audit's
  own code verification), but an exhaustive workspace-wide search for positive real-capital evidence (a real fill,
  a mainnet transaction, a reconciled live P&L, a funded live client) found none anywhere. No section survives as
  `live`. This is consistent with the owning epic's own explicit scope statement, which deliberately excludes going
  live with capital before 2026-08-25 (today is 2026-08-18) — so no section COULD pass the capital half of the test
  yet, by the epic's own design, not by an artefact-writing oversight.
status: pass
nature: record
audited_scope: >-
  platform-external-api-walkthrough.html and strategy-service-walkthrough.html — every status badge (live/partial/
  planned) graded against the 2026-08-18 stricter `live` definition (reachable on a production path AND validated
  with real capital).
date: 2026-08-18
auditor: >-
  1 general-purpose sub-agent (sonnet), dispatched as one of 5 parallel agents doing a second-pass audit of
  client-disclosure artefacts, read-only, SUB_AGENT_MANDATORY_RULES.md pasted at spawn.
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi]
stage: [data, strategy, execution, meta]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-18
tags: [client-disclosure, nick-ai, elysium, audit, live-regrade]
---

# Client artefact live-badge re-grade — second-pass audit 2026-08-18

**Read-only audit. No HTML or plan file was edited to produce this report** — per the task's hard rule, this is
findings only. Both owning plans' "operator review before send" gate is untouched.

## Method

1. Read both artefacts in full: `platform-external-api-walkthrough.html` (Nick AI, 1187 lines) and
   `strategy-service-walkthrough.html` (Elysium, 1186 lines).
2. Enumerated every `class="st st-live|st-part|st-plan"` badge instance by line number (excluding the 3 legend
   entries and the 2 CSS rule definitions per file, which also match the same substring).
3. For each `live`-marked section, searched the codebase for (a) reachability evidence — a real deployed endpoint or
   production code path — and (b) real-capital evidence — grepped for `real capital`, `real money`, `mainnet
   transaction`, `funded wallet`, `capital deployed`, `tx_hash`, `is_live.*True`, `LIVE_TRADING_ENABLED`, checked
   `promote-workflow-architecture.md`'s live-client counts, checked `e2e-testing`'s `run-live.sh` /
   `PAPER_LIVE_CONVERGENCE.md` go-live checklist, and checked the owning epic's own scope statement.
4. Reused the prior same-day audit's (`nick_ai_and_elysium_artefact_audit_2026_08_18.md`) already-verified code
   citations for reachability where they overlap, rather than re-deriving — that audit independently re-verified
   its highest-severity findings via direct code reads; I did not need to repeat that work, only apply the new
   capital-validation lens on top of it.

## Measurement notes — count discrepancy from the task brief

The task brief stated "7 sections currently marked live" for Nick AI, "10" for Elysium, "39 sections graded in
total." Direct measurement of the HTML found:

- **Nick AI**: 17 numbered sections (`00`–`17`; `00` carries no badge). **6** marked `live` (`01,02,03,04,08,09`),
  **9** `partial` (`05,06,07,10,11,12,13,14,15`), **2** `planned` (`16,17`). Plus **1** embedded sub-badge (line
  1042, `planned`) inside §14. Total badge instances: **18**, not counting the legend.
- **Elysium**: 18 numbered sections (`01`–`18`; `01` carries no badge). **10** marked `live`
  (`02,03,05,08,09,10,13,15,16,17`), **6** `partial` (`04,06,07,11,12,14`), **1** `planned` (`18`). Plus **1**
  embedded sub-badge (line 272, `planned`) inside §02. Total badge instances: **18**.
- **Grand total: 36 badge instances**, not 39. Nick AI's live count is **6**, not the briefed 7. Elysium's live
  count (**10**) matches the brief exactly.

Per the workspace's CLAIM ≤ MEASUREMENT rule, this is stated as a direct measurement rather than reconciled to the
brief's numbers — I could not find a grouping of the badges that produces 7/39, and did not want to silently
round to the briefed figures. All 36 instances are graded below regardless of the count question.

## Section 1 — Nick AI (`platform-external-api-walkthrough.html`)

| # | Section | Current mark | Reachability evidence | Real-capital evidence | Proposed mark |
| --- | --- | --- | --- | --- | --- |
| 01 | The platform, end to end (line 270) | live | Five-layer architecture is real (reference data, market data, strategy, execution, security all exist as code/services) — but this is a conceptual overview section, not itself a specific capability claim | None — no capital-specific claim in the section itself; nothing in the workspace shows real capital moving through the end-to-end stack | **partial** |
| 02 | How you connect (line 349) | live | Partially reachable: `instruments-service/instruments_service/api/routers/external.py` (`GET /v1/instruments`, `.../bulk`) and `market-tick-data-service/market_tick_data_service/api/routers/external.py` (availability/batch/stream, 310 lines) are real, auth-protected, live-deployed (`instruments-service@2fcf7a19`, `market-tick-data-service@6fefa63676`, per the 2026-08-18 audit's independent code re-verification). `execution-service/execution_service/api/external_instruction_api.py` is live for TRADE only; 10/11 `StrategyInstructionV2` types return HTTP 501. `strategy-service` has no counterparty-facing surface at all (admin-token-gated internal tooling only). Section itself admits "Endpoint paths, auth model and rate limits — pending" | None — no fill, transaction, or funded account evidence found for any of these endpoints | **partial** (and the section text should name the TRADE-only caveat per the remediation plan's §C P0 todo — already tracked there, not duplicated here) |
| 03 | Contracts and reference data (line 389) | live | Reference-data resolution is real and reachable (`instruments-service` external API above); the cross-venue detector is explicitly described in the section's own text as "shipped and **paper**-proven end to end" — the section itself does not claim live-capital validation | None. Reference-data lookups have no capital component at all — this section cannot satisfy the capital half of the test by its own nature (data resolution, not trading) | **partial** |
| 04 | The coverage model (line 490) | live | Real, measured data-coverage system (48.54% reachable coverage, 119,500,618-shard denominator, measured 2026-08-18) — a data-measurement capability, reachable and genuinely operated | None — coverage measurement has no capital component | **partial** |
| 08 | The instruction contract (line 729) | live | `StrategyInstructionEnvelope` and its subclasses are real, declared types (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:217`) used in production code paths. Externally, only TRADE is live-reachable (see §02 row); the other 10 action types return 501 | None — a schema being real and used internally is not capital validation, and 10/11 external action types have never executed | **partial** |
| 09 | Archetypes and registry scope (line 785) | live | Registry-contract-driven archetype declaration is real code (`ARCHETYPE_FEATURE_GROUPS`, capability checks) — but per the same-day pre-audit, only 5 of 59 archetypes are declared in `ARCHETYPE_FEATURE_GROUPS`, all 5 DeFi staking/lending, so "strategy consumability" reports `unverified` fleet-wide by construction | None | **partial** |

**Sub-badge (line 1042, §14)**: already `planned` — "a capability audit deriving archetype readiness across batch,
paper and live is specified and not yet built." Correct as-is; no change.

**Nick AI sections already below `live` (05,06,07,10,11,12,13,14,15 partial; 16,17 planned)**: no capital evidence
was found for any of these either (expected, since none claims capital validation). No upward re-grade is
warranted for any of them. These marks are outside the scope of a capital-validation downgrade by construction —
they were already correctly below the bar before the definition tightened.

## Section 2 — Elysium (`strategy-service-walkthrough.html`)

| # | Section | Current mark | Reachability evidence | Real-capital evidence | Proposed mark |
| --- | --- | --- | --- | --- | --- |
| 02 | Strategy identity: families, archetypes, slots (line 252) | live | `StrategyInstanceIdentity` is a real declared dataclass; slot-label scheme is real. Schema/identity description, not an execution claim | None | **partial** |
| 03 | The instruction contract, in full (line 321) | live | `StrategyInstructionEnvelope` + 9 (actually 11 per code, see the remediation plan's §A P0 finding — not duplicated here) action-type subclasses are real declared types | None | **partial** |
| 05 | Batch, paper and live — the mode axis (line 490, `new`) | live | `TradingMode` enum (`BATCH`/`PAPER`/`LIVE`) is real code; testnet-as-paper-submode is real. The section's own text defines `LIVE = "LIVE"  # real capital, real venues` as a declared enum value — it does not itself claim capital has moved | None — this section is literally *about* the mode axis that separates paper from live capital, and its own content confirms LIVE requires real capital that has not yet been deployed anywhere in this workspace (see § Workspace-wide capital search below) | **partial** |
| 08 | How a strategy picks: coins, venues, funding (line 616) | live | Coin/venue/funding selection logic (`venue_supports_perp_funding`, `perp_hedge_candidate_venues`, ADV filtering) is real code | None | **partial** |
| 09 | Reconciliation — the engines and the scenarios (line 669) | live | 9 reconciliation engines are real code (`reconciliation_engine`, `balance_reconciliation_engine`, etc.); the `live − batch = (paper − batch) + (live − paper)` decomposition is a real, described mechanism | None — the "live − paper" execution-quality leg presupposes a live trading history to measure against; no evidence any such live history exists yet (see below) | **partial** |
| 10 | The execution seam and its config loop (line 750) | live | Policy-binding/config-loop mechanism (`bindings: dict[str,str]`) is real code | None | **partial** |
| 13 | Auto-resolution and escalation (line 971, `new`) | live | `DependentAction`/`EscalationTarget` ladders, kill-switch arming — real operational-safety code, matches the codex autonomous-recovery-matrix SSOT | None — an escalation/kill-switch mechanism being real does not itself validate that real capital has run through it | **partial** |
| 15 | PnL, ledgers and the high-water mark (line 1045) | live | Parallel-ledger / flow-adjusted-HWM mechanism is real, matches the codex PnL-attribution SSOT | None — no evidence of a reconciled real (non-paper) PnL anywhere; `client-reporting-api` was searched directly for any existing real client/capital-under-management and returned 0 hits | **partial** |
| 16 | Backtest fidelity (line 1071) | live | `ExecutionFidelityTier` / `clamp_tier` are real code | **Not applicable by category** — backtesting is inherently offline historical replay; it has no capital component to validate at all. Flagged for the operator: applying a capital-validation bar to a batch-only capability may be a category mismatch worth a badge-scheme exception, rather than a genuine gap | **partial** (per the strict literal rule as given — absence of capital evidence fails it — but see the category-mismatch note above) |
| 17 | How this is kept honest (line 1106, `new`) | live | The described gates (reachability baseline, `BaseConnector.supports_live` fail-closed default, single-source registries, cross-repo invariants, ratcheted baselines) are real CI/QG infrastructure | **Not applicable by category** — same reasoning as §16: this section describes dev-tooling/CI gates, not a trading capability | **partial** (same literal-rule caveat as §16) |

**Sub-badge (line 272, §02)**: already `planned` — "a capability audit that derives this per archetype across all
three modes is specified but not yet built." Correct as-is; no change.

**Elysium sections already below `live` (04,06,07,11,12,14 partial; 18 planned)**: same conclusion as Nick AI — no
capital evidence found for any, no upward re-grade warranted.

## The section that survives — explicit search, explicit result

Per the task's instruction to look specifically for a survivor rather than assume uniform downgrade: **none of the
16 currently-`live` sections across both artefacts survives.** This was not a light search — the following were
checked directly, workspace-wide, beyond the per-section table above:

- **`plans/epics/system_readiness_master.md`** (the epic that owns both artefacts) states in its own summary and
  body: *"Deliberately EXCLUDES going live with capital"* and *"Target completion: 2026-08-25 ... Live capital is
  not [in scope]"* (lines 9, 93-95). Today is 2026-08-18 — seven days before that target. By the epic's own design,
  no capability it covers could have earned real-capital validation yet.
- **`/codex/04-architecture/promote-workflow-architecture.md`** lines 223-226: the `live_early` promotion target's
  client count is listed as **"Always 0"** — no client has ever been promoted through the standard live path.
- **`e2e-testing/scripts/defi/run-live.sh`** — a real script that CAN execute real mainnet trades via Copper MPC
  custody ("Live Trading — real chain, real money, Copper custody"), gated behind a typed `CONFIRM LIVE` operator
  confirmation and a 10-probe pre-flight gate. This is the closest thing to a live-capital execution path found
  anywhere in the workspace. Its sibling doc, **`e2e-testing/docs/defi/PAPER_LIVE_CONVERGENCE.md`**, carries a
  "Go-Live Checklist" with every item unchecked (`- [ ]`), including "Monitor first tick: verify fill appears in
  GCS with real tx_hash" under "Execution (Go-Live Day)" — worded as a future step, not a completed one. `git log`
  on this script and its pre-flight gate (`preflight-cutover.sh`) shows recent commits *adding* pre-flight probes
  (`feat(preflight): add Probe 9+10 — Tenderly VNet fork smoke...`, `add Probe 8 — Aave + Uniswap mainnet contract
  bindings audit`) — infrastructure still being built, not a completed live run being referenced.
- A workspace-wide grep for `tx_hash` outside test/mock paths found exactly two hits, both inside
  `unified-api-contracts/unified_api_contracts/external/aave/mocks/aave_liquidations_ethereum_ws.yaml` — fabricated
  mock fixture data (`"tx_hash":"0xabcdef1234567890..."`), not a real transaction.
- Greps for `real capital`, `real money`, `mainnet.*transaction`, `funded wallet`, `capital deployed`, `first live
  trade`, `went live with capital`, `LIVE_TRADING_ENABLED`, `is_live.*=.*True` (excluding tests/mocks) across the
  entire workspace returned **zero hits** describing an actual completed real-capital event.
- `client-reporting-api` was searched directly for any existing real/live client or capital-under-management —
  zero hits.

**Conclusion, stated plainly**: this is a genuine, confirmed finding, not a failure to find one. The system has
real, working production code paths (data reachability, instruction contracts, reconciliation engines, and even a
gated real-mainnet execution script), but as of 2026-08-18 nothing has been validated with real capital anywhere in
this workspace, and the owning epic says that is expected and by design for another 7 days at minimum. Every
`live` badge in both artefacts should read `partial` today.

## Internal inconsistency found in the artefacts themselves (not fixed — findings only)

- **Elysium's legend (line 173) already carries the new strict definition** — *"live: reachable on a production
  path AND validated with real capital"* — but **§01's own callout (lines 244-246) and the document's footer
  (lines 1178-1180) still state the OLD definition**: *"Live means something on a production path calls it — not
  that the code exists and passes its tests"* and *"Status reflects what is reachable on a production path, not
  what exists in the repository."* This is direct, in-document evidence that the definition was edited at the top
  (legend) but the re-grade never propagated through the rest of the document — exactly what the owning plan's own
  stub todo (`nick_ai_platform_disclosure_artifact_2026_08_16.md` § Build) already flagged as outstanding.
- **Nick AI's footer (lines 1180-1184), by contrast, already states the new strict definition consistently**
  ("Status reflects what is reachable on a production path AND validated with real capital... a section can be
  complete, wired and exercised in paper and still not carry a live mark") — but, as shown above, its own section
  badges (01,02,03,04,08,09) were never actually re-graded against that stated bar either. The prose caught up; the
  badges did not, in either document.

## What I could not verify

- **DeFi on-chain wiring's exact current state versus the 2026-08-15 measurement** — the Elysium walkthrough's §06
  cites a 2026-08-15 caller-graph sweep (27 of 33 on-chain connector classes had zero production callers) and notes
  wiring has landed since but was "deliberately not restated ... because it has not been re-measured." I did not
  re-run that sweep; I have no reason to doubt the section's own honesty about this, but I cannot independently
  confirm the current count either way.
- **Whether any live capital has ever been deployed prior to this epic's start (i.e., before `master_to_live_defi`
  began 2026-05-23)** — I checked the archived `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` epic
  exists but did not read it in full; the "Always 0" `live_early` client count in the promote-workflow doc and the
  epic's explicit "excludes going live with capital" framing are strong, but not literally exhaustive, evidence
  that no capital has ever been deployed through *any* path (as opposed to specifically the standard promote path
  and the DeFi `run-live.sh` path, both of which I checked directly).
- **Whether "39 sections" and "7 live (Nick AI)" refer to a different counting method** (e.g., including the two
  unbadged intro sections, or a grading pass that already happened elsewhere and used different criteria) — I
  measured 36 badge instances / 6 Nick-AI-live directly from the HTML and could not reconcile to the briefed
  numbers; flagged in § Measurement notes rather than silently adjusted.
