---
doc_type: plan
title: Nick AI platform disclosure — closing the pre-audit's measured gaps
summary: >-
  Remediation of the 6 gap classes the Nick AI pre-audit measured (external API surface, archetype feature-group
  declarations, granularity declaration, per-AG BACKTESTABLE blockers, sports action-vocabulary confirmation, stale
  codex numbers). The audit is done — this plan does not re-measure. Dispatched as interactive-session sub-agents
  (same mechanism as the pre-audit itself), not AO-ingested.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos:
  [
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
    deployment-api,
  ]
scope: [admin, engineer]
tags: [nick-ai, external-api, readiness-remediation, venue-readiness, archetype-feature-groups, client-disclosure]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-16
source: >-
  Operator direction 2026-08-16, remediating the measured gaps from the Nick AI pre-audit (§§5-6 of the disclosure
  plan). Same interactive-session dispatch mechanism as the pre-audit itself, per the operator's own instruction.
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
effort: high
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    unified-trading-library/unified_trading_library/cloud_interface/api_auth.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py,
  ]
---

# Nick AI platform readiness remediation

## Read first

[`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md)
§§ PRE-AUDIT MEASUREMENTS 5-6 and
[`/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md`](/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md).
**The audit is done — every gap below is already evidenced there. This plan does not re-measure.**

## Two findings that changed the dispatch prompt's original scope — read before assuming the todos below match it verbatim

1. **W2 (archetype declarations) cannot be a bounded engineering todo.** `ARCHETYPE_FEATURE_GROUPS`'s own docstring
   (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py`): *"Coverage is
   deliberately partial. A wrong entry here would silently mislead a contract-step-17 BACKTESTABLE check — worse than
   an honest gap — so only archetypes traced to real dispatch code are declared."* Real tracing already found **zero**
   dispatch-code signal for the undeclared archetypes (`venue_readiness_and_registry_hardening_2026_08_16.md` Progress
   Log, 2026-08-16). Dispatching a sub-agent to "declare" them would fabricate strategy-domain judgment against this
   same-day ruling — a CLAIM≤MEASUREMENT violation, not a gap to close. **Resolved per operator direction 2026-08-16**:
   built a candidate-mapping scaffold instead — [**Archetype Feature
   Scaffold**](https://claude.ai/code/artifact/c6c345e7-10fb-4679-b9d2-6eada7fc3f6c), 55 undeclared archetypes (a
   measured correction — see the artifact's own "count correction" banner: the enum's docstring says 59/54, a live
   Python import measures 60 total / 5 confirmed / 55 undeclared), each tagged confidence high/medium/low with a
   grounded rationale, explicitly **not committed to any file**. Nothing in this plan dispatches W2 engineering work;
   see the tracked review item below.
2. **W4-DeFi's "paused crons" blocker is already fully diagnosed and gated — not new investigation.** Read directly:
   `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8 (2026-07-22 correction entry). 7 schedulers (not
   14) are paused because a live `canonical-migration-defi-per-instrument-*` VM is actively rewriting exactly those
   data types; resuming now would race live writes against it. Two todos already track the resume, correctly gated
   (Track-1/2 landing + the migration VM finishing; the `dex_pool_state` pair additionally gated on
   `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` per task_template.md finding P). **This plan adds no new
   DeFi-cron work** — see the cross-reference item below.

## W1 — External HTTP layer (the headline; longest pole; independent — start in parallel)

**Measured state** (audit, unchanged): `instruments-service`, `market-tick-data-service`, `execution-service` each
have `api/main.py` at 62/116/43 lines exposing only `/health` + `/readiness` (line counts re-confirmed live
2026-08-16, unchanged from the audit). The contracts underneath (schemas, instruction taxonomy) are production-real —
this is missing surface, not missing capability.

**Auth — upgrade from the dispatch prompt's original framing.** The dispatch prompt said "mirror deployment-api's
`auth.py`" (`X-API-Key` only, no org/tier scoping — built for an internal ops console, no external counterparty
concept). A better-fitted precedent already exists and is unused by any of these 3 services:
`unified_trading_library.cloud_interface.api_auth.create_api_auth()` — a real, tested UTL dependency supporting
`X-Service-Token` (S2S), legacy `X-API-Key`, **and Bearer JWT with `org_id` + `subscription_tier`** (admin / internal
/ external-pro / external-basic). The JWT leg is exactly the counterparty shape this artifact pitches — an external
org, tier-limited — that deployment-api's simpler internal pattern doesn't have. Each todo below builds on this UTL
helper, not a hand-rolled copy.

- [ ] [BACKEND] P0. **instruments-service: build the external instruments surface.** New router (e.g.
      `instruments_service/api/routers/external.py`) wired into `api/main.py`, protected by
      `unified_trading_library.cloud_interface.api_auth.create_api_auth("instruments-service")`. Two endpoints
      mirroring deployment-api's "check, then download" shape: an instruments query (by asset_group/venue/
      instrument_type, reading the real `InstrumentRecord` catalogue already used internally — do not duplicate the
      read path) and a bulk parquet dump (streamed, not loaded fully into memory). Done-when: both endpoints return
      real data behind a valid `Authorization: Bearer` JWT with `org_id` set, and a `quality-gates.sh --no-fix` green
      run + a live curl against the running service, both cited.
- [ ] [BACKEND] P0. **market-tick-data-service: build the external market-data surface.** Same auth pattern. Two
      endpoints: an availability query (what's captured for a given asset_group/venue/data_type — reuse the real
      `coverage.json`/manifest read path the honest-coverage machinery already uses, never re-implement it) and a
      delivery endpoint covering both daily batch parquet and a streaming leg (reuse the UTL `EventTransport` facade
      for streaming — `unified_trading_library.streaming.event_facade` — never a bespoke transport). Done-when: both
      endpoints work behind the same auth dependency, `quality-gates.sh --no-fix` green + a live curl, cited.
- [ ] [BACKEND] P0. **execution-service: build the external instruction-submission surface.** Same auth pattern. One
      endpoint accepting a `StrategyInstructionEnvelope` (already-real schema —
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py`, class
      `StrategyInstructionEnvelope`) and routing it through the existing internal instruction-handling path — this
      surface should be a thin authenticated front door onto real logic, not new instruction-processing code. Done-
      when: a submitted instruction reaches the real handler (verified via a paper-mode round-trip, not a mock),
      `quality-gates.sh --no-fix` green, cited.

## W2 — Archetype feature-group scaffold

- [x] [REVIEW] P1. ✅ Operator reviewed the [Archetype Feature
      Scaffold](https://claude.ai/code/artifact/c6c345e7-10fb-4679-b9d2-6eada7fc3f6c) 2026-08-16 and approved the
      35-row High-confidence tier for declaration. Shipped —
      `unified-api-contracts@a617bbdf` ("feat: declare 35 High-confidence StrategyArchetype feature_group mappings
      (operator-reviewed scaffold, W2)"): `ARCHETYPE_FEATURE_GROUPS` grew from 5 to 40 declared archetypes (verified
      via direct Python import: `len(ARCHETYPE_FEATURE_GROUPS)==40`, `len(UNDECLARED_ARCHETYPES)==20`,
      `40+20==60` ✓); the module docstring now honestly distinguishes the two evidence tiers (dispatch-code-traced
      vs. operator-reviewed-scaffold) rather than conflating them. One real, correct side-effect caught by
      `quality-gates.sh` and fixed in the same commit:
      `tests/unit/test_venue_strategy_consumability.py::test_venue_with_no_satisfying_archetype_fails` asserted a
      venue offering only `ohlcv_1m` satisfies no archetype — no longer true, since `ML_DIRECTIONAL_CONTINUOUS`/
      `RULES_DIRECTIONAL_CONTINUOUS`/`TSMOM_BTC_CTA` all resolve to `ohlcv_1m`-only inputs now. Fixed the fixture to
      `mev_events` (a real registry gap — zero feature_group consumers anywhere) rather than weakening the check.
      `quickmerge.sh` printed a transient exit-10 "silent revert" warning mid-run (a concurrent peer's push landing
      during the Not-Behind Gate) — verified directly (file content diff + `git show HEAD:<path>` + `git
      merge-base --is-ancestor HEAD origin/live-defi-rollout`) that the final commit genuinely landed with the full
      change on both local HEAD and origin before treating it as done; not a blind re-run.
- [ ] [REVIEW] P2. **The 20 rows NOT declared** (8 Medium — ambiguous domain/ML-layer-unclear; 12 Low — genuine
      `feature_group` registry gaps: CeFi perp-funding basis, on-chain MEV, DEX-pool-state/vault-share-price,
      PORTFOLIO_MULTI_STRATEGY's meta-strategy shape) remain open in the scaffold artifact, un-actioned. The 12 gap
      rows are a separate, likely-larger follow-up (new `feature_group` definitions in features-onchain/
      features-delta-one, not an archetype-declaration task) — do not fold them into a future declaration pass.

## W3 — Granularity declaration (step 13) — land early, genuinely independent

**Ruled 2026-08-16** in `venue_readiness_and_registry_hardening_2026_08_16.md`: a UAC registry, keyed per
`(venue × instrument_type × data_type)`, extending `VenueCapabilityRecord`
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`) — it already carries the
`(venue × data_type)` axis this needs, missing only the instrument-type axis and the granularity/exceptions fields.
Seed from manifest + plans + code, never hand-populated; where the three disagree, **the manifest is the measurement
and wins** — a disagreement is itself a finding, not a tie to break quietly. Do not conflate this with per-venue
coverage-*start-dates* (an interval) — step 13 asks for the achievable *fidelity tier*, a different axis (the
tradfi sub-agent's pre-audit read conflated these; correct that reading here, don't repeat it).

- [ ] [AGENT] P0. **Extend `VenueCapabilityRecord` with the instrument-type axis + granularity/exceptions fields**,
      seeded from a reconciliation of the live manifest, `VENUE_DATA_TYPE_CAPABILITIES`, and the readiness-contract's
      own fidelity vocabulary (`execution_fidelity.py`: `L2_MBP` > `CANDLE_BOOK_COLS` > `L1_MBP` > `L0_TOB`, plus
      `AMM`/`ALPHA_ZERO`). Cite every manifest-vs-code disagreement found, don't silently resolve them. Done-when: the
      extended registry populates for at least the 5 asset groups' declared venues, `quality-gates.sh --no-fix`
      green, and the umbrella plan's own open P1 ("Publish the granularity view") can render from it.

## W4 — Per-AG BACKTESTABLE blockers

- [ ] [AGENT] P1. **CeFi: close the wallet-capability + error-classification gaps.** Measured (audit): only 7/25
      venues have a `VENUE_WALLET_CAPABILITIES`-family entry under their canonical name (step 9, transfers) — file
      candidates: `unified-api-contracts/unified_api_contracts/internal/domain/execution_service/transfer_types.py`
      and `.../defi/wallet_config.py` (confirm which is the real cefi-scoped registry as this todo's first step, cite
      it). ~14/25 venues have no dedicated classification in `VENUE_ERRORS_CEFI`
      (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/cefi.py`, step 10). Both are
      enumerable against the existing 25-venue UAC declaration — add the missing entries, sourced from each venue's
      own API docs where available, `unverified` (not invented) where not. Done-when: both registries cover 25/25
      venues (or each remaining gap is cited with why — no venue-specific docs found), `quality-gates.sh --no-fix`
      green.
- [ ] [AGENT] P1. **Sports: fix the mock-only live config + resolve the step-8 registry contradiction.**
      `deployment-api/deployment_api/routes/sports_venues.py` returns `"live_not_configured"` verbatim in live mode
      (step 11, FAIL) — wire it to real config, matching the pattern other asset groups' venue-credential endpoints
      already use. Separately: `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py` declares
      `NO_ADAPTER_YET` for nearly every sports bookmaker while `execution-service/execution_service/sports_execution/`
      has 5 real adapters (betfair.py, matchbook.py, kalshi.py, polymarket_clob.py) wired through a real
      `SportsExecutionRouter` (`execution-service/execution_service/sports_execution/routing.py`). **Determine which
      side is stale and fix it at the source** — do not reconcile in a doc. Done-when: the UAC registry and
      execution-service's real dispatch map agree, cited with the specific commits on both repos,
      `quality-gates.sh --no-fix` green on both.
- [ ] [AGENT] P2. **Sports: confirm or add the back/lay action mapping (W5).** The audit could not find `back`/`lay`
      mapped to `InstructionActionV2` or `AccountActionV2`
      (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py`) — plausibly
      `TradeInstruction` with a `side` field, unconfirmed. Either confirm the existing mapping and document it inline
      (a code comment citing where back/lay actually route), or add it if genuinely missing. The artifact's central
      claim — one instruction vocabulary spans every asset class — must be true, not assumed. Done-when: a concrete
      code citation (existing or newly added) shows back/lay resolving to a real `InstructionActionV2` member,
      `quality-gates.sh --no-fix` green if code changed.
- [ ] [AGENT] P1. **Prediction: wire Polymarket into the existing matching engine for paper mode.** Per the operator's
      2026-08-16 ruling (simulate via our own matching engine, per the readiness contract's own fallback wording) —
      **not a from-scratch simulator.** Polymarket's own captured data is real CLOB depth, not a coarse odds
      snapshot: `book_snapshot_5` carries real bid/ask JSON arrays up to 50 levels (audit, confirmed). Step 1: check
      whether execution-service's existing paper/backtest matching engine already accepts a `book_snapshot_5`-shaped
      input for any venue (the fidelity-tier vocabulary above suggests it should, since `L1_MBP`/`L2_MBP` tiers are
      already modeled) — if so, this is a wiring task (add Polymarket to whatever venue-dispatch map the matching
      engine reads), not new matching-engine code. If a genuine gap exists once checked, scope exactly what's missing
      before writing it — do not assume the size of this task before step 1 is done. Done-when: a paper-mode
      Polymarket instruction produces a real fill through the matching engine (not a mock), with the fidelity tier it
      ran at cited, `quality-gates.sh --no-fix` green.
- **DeFi — no new todo.** See the "Two findings" section above; the pause is already correctly diagnosed and gated
  in `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 8. Nothing to add here.

## W6 — Codex refresh: deferred to the gated finalize companion

Refreshing `/codex/02-data/honest-coverage-model.md`'s stale certified numbers (defi/tradfi/sports/prediction) needs
the FINAL post-remediation state, not the pre-remediation snapshot — tracked in
[`nick_ai_platform_readiness_remediation_finalize_2026_08_16.md`](/plans/active/nick_ai_platform_readiness_remediation_finalize_2026_08_16.md),
gated on this plan via `depends_on` + `gate_on_depends: true`.

## Known traps (already applied once in the pre-audit; re-apply during remediation)

Probe the vocabulary the writer emits (registries key on CONSTANTS, not literals) · 0 hits ≠ missing, check the
directory before concluding absence · `canonical_path_violations()` is path-structure-only, value-blind · stale
`/data-pipeline-check-*` skills — read the real registries directly · sports 2020-06 data floor already applied
upstream · Databento boundary is by SOURCE not asset group · never weaken a check to make a state pass — an accurate
`unverified` is correct output, not a failure to fix · **credentials gate RUNNING, never BUILDING** — build the full
path, mark `BLOCKED-CREDENTIALS` where it can't run · do not edit the artifact HTML — the operator reviews numbers
before they reach a client document.

## Progress Log

**2026-08-16 — authored.** Read the two source docs (nick_ai plan §§5-6, full pre-audit results) plus the venue-
readiness umbrella plan and `defi_consolidated_closeout_2026_07_18.md` Track 8 before drafting — found the two
scope-changing landmines documented above (W2 fabrication risk, W4-DeFi already-answered). Confirmed a better-fitted
auth precedent for W1 (`unified_trading_library.cloud_interface.api_auth`) by reading it directly rather than
mirroring the dispatch prompt's original citation blind. Verified the 3 thin `api/main.py` line counts (62/116/43)
still match the audit exactly. Built and published the W2 scaffold artifact (55 rows, confidence-tagged, grounded in
a direct read of the full `StrategyArchetype` enum + `FEATURE_REQUIRED_INPUTS` registry — not inferred from category
names alone); caught and corrected a real count-drift while building it (enum docstring claims 59/54, a live Python
import measures 60/5/55 — noted in the artifact itself, not silently used the stale number). Operator ruling
2026-08-16 on the Polymarket paper-trading blocker: simulate via the existing matching engine, framed above as a
wiring-first investigation given Polymarket's real CLOB depth data, not an assumed from-scratch build.
