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
parent_epic: security_and_cross_cutting_master
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
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md,
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

- [x] [DATA] P0. ✅ Measured 2026-08-16. **Honest coverage per (asset_group × venue × instrument_type × data_type ×
      chain)** — 5 parallel sub-agents read the real `coverage.json` / manifest live via the deployment-api/UAC
      machinery, not a re-implementation. See § PRE-AUDIT MEASUREMENTS §2 below (per-AG summary) and §5 there for
      why full per-venue/per-cell detail isn't inlined.
- [x] [DATA] P0. ✅ Measured 2026-08-16. **"≈50%/≈99%" claim verified — corrected, not confirmed.** ≈50% is right
      only as a shard-volume-weighted average (48.40%); the naive per-AG average is 73.04%. ≈99% has no measured or
      documented basis anywhere in this workspace. See § PRE-AUDIT MEASUREMENTS §3.
- [x] [DATA] P0. ✅ Measured 2026-08-16. **Venue-universe denominator reconciled** — "~170" has no code citation;
      "158/84" is real but 2-days-stale and traces to
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`; fresh per-AG counts
      bracket it at 151 (canonical) to 183 (physical). See § PRE-AUDIT MEASUREMENTS §1.
- [x] [DATA] P1. ✅ Measured 2026-08-16. **Current vs expected size per AG** — measured for 4/5 AGs (~50.02 TB
      current, sum); prediction's bytes are explicitly not measurable in this environment (missing package), stated
      as such rather than estimated. See § PRE-AUDIT MEASUREMENTS §4.
- [x] [DATA] P1. ✅ Measured 2026-08-16. **Readiness stage per AG**, derived from the 19-step Venue Readiness
      Contract, `unverified` shown wherever no real check exists. No AG cleanly clears BACKTESTABLE today. See
      § PRE-AUDIT MEASUREMENTS §5.
- [x] [BACKEND] P1. ✅ Measured 2026-08-16. **External API surface enumerated — contracts exist, the external HTTP
      layer does not yet.** See § PRE-AUDIT MEASUREMENTS §6 (auth model, instruction-contract shape) and §7
      (per-shard schema counts + gaps).
- [x] [BACKEND] P2. ✅ Measured 2026-08-16. **Credentials/testnet position stated per AG**, including two real gaps
      (no written Polymarket paper-trading ruling; TradFi's only live credential-health probe covers Tardis only).
      See § PRE-AUDIT MEASUREMENTS §8.

## PRE-AUDIT MEASUREMENTS — 2026-08-16

Full coverage + readiness audit, dispatched as 5 parallel per-asset-group sub-agents (cefi/defi/tradfi/sports/
prediction; general-purpose, sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted at spawn) against the real deployment-api/
UAC honest-coverage machinery and manifest — never re-implemented. Every figure below carries its denominator,
measurement date, and method. Where something could not be measured, that is stated explicitly rather than
estimated. Full per-venue/per-shard/per-cell detail (too large for this plan's line cap) lives in
[`/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md`](/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md);
this section is the AG-level summary the artifact should build from.

### 1. Venue-universe denominator — three different units, reconciled

| Figure | Value | Unit | Source | Date |
| --- | --- | --- | --- | --- |
| "~170 venues" | — | — | **No code citation found**, by any of the 6 investigators (5 sub-agents + this synthesis). Purely relayed in conversation. | — |
| "158 capture venues across 84 families" | 158 / 84 | fleet-wide, `VENUE_DATA_TYPE_CAPABILITIES ∪ DeFi` | `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` L62-65 | 2026-08-14 (2 days stale) |
| CeFi declared venues | 25 | UAC `VENUES_BY_ASSET_GROUP["cefi"]` | sub-agent (cefi) | 2026-08-16 |
| DeFi protocol identities | 79 (105 venue-string spellings incl. legacy dual-naming; 71 Layer-1-tracked) | UAC `by_venue.defi` live rollup | sub-agent (defi) | 2026-08-16 |
| TradFi declared venues | 8 (+1 retired-but-inert: BARCHART, 9,119 rows/0 captured) | `VENUE_TO_ADAPTER_KEY` + `VENUE_DATA_TYPE_CAPABILITIES`, cross-checked | sub-agent (tradfi) | 2026-08-16 |
| Sports canonical declared | 37 (31 bookmakers + 1 direct exchange + 5 reference sources); 45 physical manifest keys (incl. deregistered/historical + 3 data-quality artifacts) | UAC registries + live manifest | sub-agent (sports) | 2026-08-16 |
| Prediction declared venues | 2 (POLYMARKET, KALSHI) | UAC `VENUES_BY_ASSET_GROUP["prediction"]` | sub-agent (prediction) | 2026-08-16 |
| **Sum, canonical/declared basis** | **151** | 25+79+8+37+2 | this synthesis | 2026-08-16 |
| **Sum, physical/manifest-observed basis** | **183** | 22(cefi, w/ any manifest row)+105(defi spellings)+9(tradfi incl. Barchart)+45(sports physical)+2(prediction) | this synthesis | 2026-08-16 |

**Verdict**: the three units genuinely differ and should not be collapsed into one number in the artifact. "158/84"
is real but 2 days stale and computed under a different method than any single sub-agent's count; the fresh per-AG
sums (151 canonical / 183 physical) bracket it but don't match exactly — the gap is explained by whether DeFi's dual
legacy/canonical venue-string spellings and Sports' historical/deregistered venues are counted. State all three
explicitly in the artifact, labelled by unit — do not pick the flattering one. The readiness contract's own
denominator (venue × data type) is a fourth, finer unit — see per-AG leaf-cell counts in §5/§7.

### 2. Honest coverage — Layer 1 (instrument-denominator) and Layer 2 (download), per AG

All from the real `coverage.json` (`gs://central-element-323112-honest-coverage/2026-08-16/`,
`generated_at: 2026-08-16T00:43:09Z`) — the actual output of `instruments-service/scripts/measure_honest_coverage.py`,
read live by each sub-agent, not re-implemented.

| AG | Layer-1 completeness | Holes | Strays | captured | empty_confirmed | attempted_failed | expected_unattempted | reachable coverage_pct | all_shards_pct |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cefi | 94.52% (69/73) | 4 | 82 | 9,756,593 | 6,437,038 | 764,259 | 10,879,751 | 45.59% | 35.05% |
| defi | 83.08% (108/130) | 22 | 698 | 32,963,774 | 78,750,991 | 7,875,315 | 40,514,840 | 40.52% | 20.59% |
| tradfi | 67.74% (21/31) | 10 | 70 | 8,116,669 | 5,110,207 | 801,630 | 415,073 | 86.96% | 56.20% |
| sports | 79.03% (49/62) | 13¹ | 754 | 6,202,819 | 22,596 | 35,720 | 0 | 99.43%² | 99.07% |
| prediction | 100.0% (4/4) | 0 | 4³ | 478,638 | 2,283,224 | 31,480 | 6,170 | 92.71% | 17.10% |

¹ 4 are genuine zero-data venues; 9 are very likely a trades↔odds taxonomy-migration artifact (contract landed,
physical re-stamp still P2-scope) rather than 9 independent gaps — not fully confirmed, flagged as the most likely
reading. ² Flagged by its own measurement as a likely-inflated lower bound — Layer-1 is only 79.03% complete, so the
"reachable" denominator may itself undercount the true expected universe. ³ By-design cluster/market-id-grain
exclusions, not gaps.

**The captured/empty_confirmed/attempted_failed/expected_unattempted split — the single most important output**:
`empty_confirmed` (legitimate absence, a limit) vs `expected_unattempted` (never-tried, a schedule) differ enormously
by AG. CeFi's `expected_unattempted` (39.1%) exceeds its own `captured` (35.1%) — the real bottleneck is unattempted
backlog, not absence. DeFi's `empty_confirmed` (49.2%) dominates. TradFi and Sports are capture-dominant (56.2%/99.1%
`captured` respectively).

**Chain axis (DeFi — mandatory per this plan)**: real, measured, materially differentiates coverage (BSC 68.79%
reachable vs AVALANCHE 27.25%, full per-chain table in the defi sub-agent's report) — but the shipped `coverage.json`
rollup does **not** expose a fully-crossed (venue × chain × instrument_type × data_type) cell for the 79 "bare-form"
multi-chain protocols (AAVE_V3 spans 8 chains, UNISWAP_V3 spans 5, etc.) — only the 26 legacy combined-form
venue-strings carry chain in the venue name itself. A direct manifest crosstab to close this gap timed out (120s)
from this sandbox — genuinely not measurable here, not fabricated.

**Stale codex SSOT, 4 of 5 rows superseded** — `/codex/02-data/honest-coverage-model.md`'s certified table is out of
date and should be refreshed by its owner (not edited here):

| AG | Codex-cited (date) | Fresh (2026-08-16) | Why it moved |
| --- | --- | --- | --- |
| defi | 94.81%, 73/77 (not re-measured since 2026-07-03) | 83.08%, 108/130 | Denominator grew 77→130 (more protocols/chains onboarded); completeness dropped |
| tradfi | 51.43%, 18/35 (2026-07-03) | 67.74%, 21/31 | MVP scope narrowed 2026-05-15 (tick data trades/tbbo/mbp_10 deferred to post-cutover) — both numerator and denominator shape changed |
| sports | 30.77%, 8/26 (2026-07-03, never refreshed) | 79.03%, 49/62 | Same pattern — stale by ~6 weeks |
| prediction | 66.67%, 4/6 (2026-07-03) | 100.0%, 4/4 | A UAC matrix entry was deleted 2026-07-07 (broke Layer-1 to `EXPECTED=0/UNDEFINED`) and only restored 2026-08-15 — the cited figure predates a broken-measurement window |

### 3. Verifying "≈50% average now, ≈99% obtainable"

**Method matters — two honest averages, far apart**:
- **Simple average across the 5 AGs' reachable coverage_pct**: (45.59+40.52+86.96+99.43+92.71)/5 = **73.04%**
- **Shard-volume-weighted average** (total captured ÷ total reachable-denominator across all 5 AGs: 57,518,493 /
  118,842,731): **48.40%**

The weighted figure is the more representative one for "what fraction of the whole data universe is captured" — and
it lands almost exactly on the relayed "≈50%." The simple average would overstate it by 25 points because it treats
every AG equally regardless of size; DeFi alone is 68% of the fleet's reachable-shard volume and its coverage
(40.52%) pulls the weighted number down. **Verdict: "≈50% average now" is correct only if stated as a
volume-weighted average — the artifact should say so explicitly, not leave the method unstated.**

**"≈99% obtainable"**: none of the 5 sub-agents nor this synthesis found any measured figure, projection, or
documented basis for this anywhere in the codebase or codex. **This should not appear in the artifact without a
cited basis being established first** — it reads as an aspirational/relayed number with no measurement behind it
today.

### 4. Current vs expected size per AG

| AG | Current (measured) | Expected (PROJECTION, basis stated) | Rows |
| --- | --- | --- | --- |
| cefi | 47.103 TB | ~103.32 TB (÷ reachable 45.59%) or ~134.42 TB (÷ all-shards 35.05%) — linear extrapolation, unverified against true per-shard byte distribution | shard-cells only; no row-count field in coverage.json |
| defi | ≈1.7754 TB | ≈4.38 TB (÷ reachable 40.52%) — same linear-extrapolation caveat | NOT attempted — `read_availability_index_safe`'s own docstring documents a prior OOM incident on unfiltered DeFi-index reads; genuinely not measured, not guessed |
| tradfi | 0.7055 TB | 0.81 TB (÷ reachable 86.96%) or 1.26 TB (÷ all-shards 56.20%) — both an explicit **floor**: pre-2026-05-15 tick-level scope (trades/tbbo/mbp_10) is deferred to an unscoped "post-cutover" plan, not cancelled | **6.92B underlying data rows** (directly summed from the manifest's real `row_count` column — distinct from the 8.1M shard-cell count) |
| sports | 0.4384 TB | ≈0.46–0.47 TB — rough order-of-magnitude, peer-cohort proxy, wide error bars | 6,261,135 shard-cells (not underlying tick rows) |
| prediction | **NOT MEASURABLE in this environment** — `measure_honest_coverage.py`'s Cloud Monitoring byte call failed with `ImportError: cannot import name 'monitoring_v3'`, a missing package in this checkout's `.venv`, not an auth/network block (the same venv succeeded at the GCS parquet read moments earlier) | not produced (no baseline to project from without inventing one) | 2,799,512 shard-cells |
| **Sum (4 of 5 AGs with measured bytes)** | **≈50.02 TB** | — | — |

**Methodological gap, not papered over**: only TradFi cleanly separated "manifest shard-cell count" from "underlying
tick/bar row count" (6.92B rows in 8.1M shards — a ~850× ratio). The other 4 AGs' "row" figures above are shard-cell
counts, not true row totals — a fleet-wide row total is NOT consistently measured and should not be quoted as one
number without redoing this per-AG with TradFi's method.

### 5. Readiness per AG — derived from the 19-step Venue Readiness Contract, never declared

Per the 2026-08-16 operator ruling: a step with no real check reports `unverified`, never a silent pass. Full
per-step tables are in each sub-agent's report; rollup below.

| AG | BACKTESTABLE | PAPER-READY | LIVE-READY | Headline blocker |
| --- | --- | --- | --- | --- |
| cefi | Partial — step 1 (Declared) partial, step 13 not built | Not reached | Not reached | Step 9 (transfers): only 7/25 venues have a wallet-capability entry. Step 10 (error semantics): ~14/25 venues have no dedicated classification. |
| defi | Not cleanly cleared — step 3 only 40.52% reachable-complete | Not met | Not met | Step 4 (live) documented PAUSED (3 `defi-fwd-*` crons, since 2026-06-08/07-18); step 13 not built |
| tradfi | Closest of the 5, still not certified | Not reached | Not assessed (gated on paper) | Step 11 (config) genuinely unsettled **workspace-wide**, not tradfi-specific; step 4 rests on a stale 2026-06-21 confirmation |
| sports | Not cleanly achieved | Further out | Further out | Step 11 (config) = **FAIL, mock-only** (`sports_venues.py` live mode returns `"live_not_configured"` verbatim); step 8 shows contradictory UAC-vs-execution-service signals (registry says `NO_ADAPTER_YET`, code has 5 real adapters) |
| prediction | Cannot be certified | Cannot be certified | Not determinable | **No written ruling exists for how Polymarket would be paper-traded** (no testnet, unlike Kalshi's real demo API) — a hard PAPER-READY blocker per the contract's own "settled, recorded answer" requirement |

**Fleet-wide pattern, not per-AG**: Step 13 (Granularity declared) is not yet built for **any** asset group —
confirmed directly against the umbrella plan's own open P1 ("Publish the granularity view"). (The tradfi sub-agent
read step 13 as passing, based on real per-venue coverage-start dates in `VENUE_DATA_TYPE_CAPABILITIES` — that's real
data, but it's the *interval*, not the *achievable fidelity tier* the contract's step 13 actually asks for; going
with the conservative, contract-literal, cross-AG-consistent reading: not built, tradfi included.) Step 17 (Strategy
consumability) can only mechanically pass today for the 5 of 59 archetypes declared in `ARCHETYPE_FEATURE_GROUPS` —
all 5 are DeFi staking/lending — so every AG's strategy-consumability check reports `unverified` by construction, not
because the strategies don't work.

### 6. External API surface — what exists, what doesn't

**Auth model (real, confirmed)**: `deployment-api/deployment_api/auth.py` — `X-API-Key` header (`APIKeyHeader`),
validated via `UnifiedCloudConfig`; separate `X-Service-Token` header for service-to-service calls; `DISABLE_AUTH=true`
is a hard-refused RuntimeError in production. This is the auth pattern to mirror, not a citation of the pattern
already being externally exposed.

**The honest finding**: the instruction/data **contracts are solid and complete**; the external HTTP layer exposing
them to a counterparty **does not exist today**.
- `instruments-service`, `market-tick-data-service`, `execution-service` each have their own `api/main.py`
  (62/116/43 lines) — **all three expose only `/health` + `/readiness`**, nothing else.
- `strategy-service/api/main.py` (188 lines) is the partial exception: SSE signal streaming (`/stream/signals`),
  admin-token-gated registry reads (built "for UI CatalogueTruthinessAdapter"), an admin-token-gated
  operational-mode-flip endpoint, a restriction-profile router ("HTTP surface for UI SSR + cross-service callers") —
  real endpoints, but internal tooling gated by a shared admin token, not counterparty auth.
- `deployment-api` has the real "check availability, then download" pattern already built (`/api/data-status`,
  `/api/capabilities`, `/api` + fixtures/catalogue-lifecycle/prediction-catalogue routers, X-API-Key auth) — but it
  is an internal ops/devops console (VM management, Cloud Build, fleet census, kill-switch, chaos injection — dozens
  of unrelated routes), not a counterparty-facing service. Its shape is the pattern to mirror; it is not itself the
  surface.
- A structurally similar precedent exists: `client-reporting-api` (LP/investor performance reports, HWM fee calc,
  X-API-Key auth) — proves the workspace already builds external-facing, API-key-gated services; it serves a
  different purpose (investor reporting, not strategy instruction) and isn't the surface either.

**Instruction contract (real, well-typed)**: `StrategyInstructionEnvelope`
(`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:217`), one subclass per action —
`TradeInstruction`, `SwapInstruction`, `LendInstruction`, `BorrowInstruction`, `StakeInstruction`,
`UnstakeInstruction`, `QuoteInstruction`, `TransferInstructionV2`, `BridgeInstructionV2`, `AtomicInstruction` (wraps
an `AtomicLeg` list — the chained-sequence mechanism, e.g. borrow→swap→stake), `CancelInstruction` — plus a separate
`AccountInstruction` for account-level ops (close_all/set_margin_mode/set_leverage/emergency_liquidate/
transfer_subaccount/withdraw/deposit_ack/rotate_credential/pause/resume), mapped from `InstructionActionV2`
(14 members) / `AccountActionV2` (11 members). **Open item, not resolved**: sports "back"/"lay" actions were not
found mapped to either enum directly — plausibly `TradeInstruction` with a side field, unconfirmed.

**Verdict for the artifact**: state plainly that the contracts (types, schemas, action taxonomy) are production-real
and can be shown as config/API-contract snippets per the disclosure boundary — but the external-facing HTTP layer
itself is unbuilt work, not yet-measured existing capability. Conflating the two would overstate readiness.

### 7. Per-shard schemas — counts, exhaustive detail referenced not inlined (plan line-cap)

| AG | Registered schema count | Notable gaps found |
| --- | --- | --- |
| cefi | 9 declared data types (all schemas read from source) | `futures_chain` schema not located; `options_chain`/`ohlcv_1m`/`book_snapshot_5` each have 2 coexisting candidate schema classes, write-path selection not resolved |
| defi | 35 `(instrument_type, data_type)` registrations, ~34 distinct data types — exhaustive against both UAC contract files | Canonical-orthogonality candidates: `utilization`/`utilisation` spelling divergence (one documented-removed, appears anyway); `dex_pool_swaps` has 2 identical-shape registry keys; the 7-member perp-data cluster is self-documented in-source as mostly derivable from `perp_funding` |
| tradfi | 14 static + a dynamic re-aggregated-candle set, exhaustive | `tbbo` and `yield_curve` (FRED's flagship, 100% coverage) both have real captured production data with **zero registered schema** |
| sports | 22 registered `CONTRACT_REGISTRY` entries (21 in-scope + 1 features-adjacent, excluded) | `FOOTBALL` venue artifact (910 rows, instrument_type values are literally lowercase bookmaker names — a write-path bug, flagged not fixed); 754 Layer-1 strays dominated by 84 distinct per-market-line instrument_type tokens (a real Step-19 orthogonality candidate) |
| prediction | 4 registered `SchemaContract`s (trades, book_snapshot_5, market_metadata, fills) + 1 dataclass (`market_lifecycle`, no formal contract) | `market_lifecycle`/`MARKET_LIFECYCLE` (both casings) show **zero captured rows** despite real writer code designed to populate them; `market_metadata`/`fills` have schemas but don't appear in the live capture vocabulary |

Full field-level schemas (every column, type, nullability) for all 5 AGs were extracted in full by each sub-agent and
are too large for this plan's line cap — they live in
[`/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md`](/plans/audit/results/nick_ai_platform_disclosure_pre_audit_2026_08_16.md)
and should be pulled directly into the artifact when it's built, not re-derived.

### 8. Credentials / testnet position — per AG, narrative

| AG | Position |
| --- | --- |
| cefi | Tardis key-status probe returned `status=error` (live, real call) — inconclusive whether that's a genuine key problem or this sandbox's own non-Google egress restriction; **no per-venue testnet declaration found anywhere** in execution-service or UAC |
| defi | Real testnet support confirmed in code for AAVE (Sepolia, via `get_testnet_contract_registry()`) and Solana LST protocols (public devnet, no key needed); Karak/Pendle connector files exist but aren't in the live dispatch-reachability map |
| tradfi | `/api/venue-credentials` (the only live credential-health surface) **only probes Tardis** — zero TradFi credential (Databento/FRED/IBKR) status coverage exists today; no tradfi-specific testnet documentation found |
| sports | No live credential-probe surface for sports bookmakers exists at all (`sports_venues.py` live mode is entirely stubbed, `"live_not_configured"`); Kalshi has a real testnet declared (`demo-api.kalshi.co`), the other direct-connector venues (Betfair/Pinnacle/Matchbook) declare `supports_testnet=False` |
| prediction | A reserved GSM secret slot exists (`credentials-matrix.md`, not verified populated); Kalshi has a coded demo host, **Polymarket has no testnet and no written ruling on how it would be paper-traded** |

**General narrative** (matches the plan's own pre-audit framing): live connectivity is credential-gated, not
code-gated, per "credentials gate RUNNING, never BUILDING" — the remaining work across AGs is weeks not months only
where a genuine testnet/simulation path already exists; prediction (Polymarket) and several cefi/sports venues need
that path *designed*, not just funded.

### Known-traps checklist — confirmed applied, not skipped

- **Vocabulary-emitted-by-writer**: checked and caught real drift multiple times (TradFi's ICE/KRX `databento`-label-
  vs-Yahoo-actual mismatch; Sports' live `SOCCER_EPL` sport-key leak into `instrument_type`; CeFi's
  `KALSHI-PERP`/`KALSHI_PERP` spelling variant).
- **0 hits ≠ missing**: multiple sub-agents explicitly reported "0 hits, not exhaustively searched" rather than
  asserting absence (tradfi's FRED secret name, sports' config search).
- **`canonical_path_violations()` blind spots**: this audit measured coverage/completeness (a different axis), not
  path-canonicalization — that oracle was not invoked; if a path-canonical audit is wanted, that is
  `/data-pipeline-reconciliation`'s job, not this one.
- **`/data-pipeline-check-*` skills**: not invoked by any sub-agent — all 5 read the real `coverage.json`/manifest
  directly via the same machinery the skills would eventually call, sidestepping the skills' own known-stale-banner
  risk entirely.
- **Sports 2020-06 floor**: confirmed already applied upstream by the real measurement machinery
  (`SOURCE_COVERAGE_START` clamps every sports source to 2020-06-06) — no pre-floor gap was observed or reported as
  one.
- **Databento boundary by SOURCE not asset group**: applied — tradfi's per-venue table above shows KRX and ICE
  labeled `databento` in the adapter-key registry while actually being Yahoo-sourced end to end; flagged as a
  label/reality mismatch, not corrected (read-only scope).
- **No proxy quoted for the property**: every coverage figure above is a real 4-state count from the production
  manifest, not a row count, exit code, or green-test proxy.

## Build

- [x] [DOC] P0. **DONE — shipped `unified-trading-pm@ec08cccad1`** ("Nick AI walkthrough aligned to verified
      source-of-truth"): all 6 `live` badges re-graded to `partial`, cross-referencing
      `client_artefact_remediation_nickai_2026_08_18.md`'s own already-closed matching todo rather than re-doing the
      work.
- [ ] [DOC] P0. **Re-grade every section mark in BOTH artefacts against the STRICTER `live` definition** (operator, 2026-08-18): `live` now means reachable on a production path **AND validated with real capital**. The definition
      landed (`unified-trading-pm@832033d094`); **the section marks did not change.** Since the epic excludes going live
      with capital before 2026-08-25, expect most `live` marks to drop to `partial` — a section can be complete, wired
      and paper-exercised and still not earn `live`. Do not leave the two documents grading on different definitions.
- [x] [DOC] P0. **DONE — shipped `unified-trading-pm@ec08cccad1`.** The forward claim was cut, not softened; live
      `grep` for "most of the venues and strategies" in
      `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` returns 0 hits.
- [ ] [DOC] P0. **Ground or remove the forward claim in the platform guide's intro** — *"most of the venues and
      strategies on the current plan complete over the remainder of this year"*. It came from operator framing and has
      **no cited basis in any plan**. A counterparty will hold us to it: cite what supports it, or cut it. This is the
      only unsupported forward-looking commitment in either artefact.

- [ ] [DOC] P0. **Build the artifact** once the P0 pre-audit items are measured. Reuse the established design
      language from the existing walkthrough artifacts rather than redesigning — they read well and consistency
      across our client documents is itself a signal.
- [ ] [REVIEW] P0. **Operator review before send**, against the disclosure boundary above.

## Progress Log

**2026-08-16 — authored.** Captured from an interactive session plus a relayed counterparty thread, ahead of any
build work, specifically so the scope rulings and the disclosure boundary survive outside chat. The pre-audit section
exists because this artifact is mostly figures: unlike the Elysium walkthrough, which describes mechanisms, this one
quantifies coverage — so the measurement discipline is the deliverable's main risk, not a formality.

**2026-08-16 — full pre-audit measurement complete, all 7 items flipped.** Dispatched as 5 parallel sub-agents
(cefi/defi/tradfi/sports/prediction, general-purpose, sonnet, `SUB_AGENT_MANDATORY_RULES.md` pasted at spawn) against
the real `coverage.json`/manifest via UTL's GCS SDK path — never re-implemented. 4 of 5 hit a session rate limit
mid-task and were resumed via SendMessage once capacity returned; all 5 completed with real, cross-verified findings
(usage: 383K/315K/403K/405K/347K output tokens for cefi/prediction/sports/defi/tradfi respectively — this was a
genuinely large audit, not a cheap one). Two items done directly rather than delegated (venue-universe denominator,
external API surface), to stay within the workspace's 5-parallel-agent cap while the AG agents ran. Full tables in
the § PRE-AUDIT MEASUREMENTS section above.

**Headline corrections to numbers already relayed to the counterparty**: "≈50% average now" is correct only as a
shard-volume-weighted average across AGs (48.40%) — the naive per-AG average is 73.04%, a 25-point difference the
artifact must not paper over by leaving the method unstated. "≈99% obtainable" has no measured or documented basis
anywhere in this workspace and should not appear in the artifact without one. "~170 venues" has no code citation at
all (purely relayed); "158 capture venues / 84 families" is real but 2 days stale (2026-08-14) and reconciles to a
range of 151 (canonical) to 183 (physical/manifest-observed) under a fresh 2026-08-16 measurement — state all three
units, not one flattering number.

**Stale codex SSOT found and flagged, not edited**: `/codex/02-data/honest-coverage-model.md`'s certified Layer-1
table is out of date for defi/tradfi/sports/prediction (all dated 2026-07-03, "not re-measured" per its own text) —
fresh figures for all 5 AGs are in § PRE-AUDIT MEASUREMENTS §2 above. That doc's owner should refresh it; flagged
here so the drift doesn't compound further before someone does.

**Side finding, fixed in this same session**:
`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`'s W4 bullet claimed
`venue_e2e_wiring_2026_08_16.md` "was never actually created" — false; the file exists (163 lines, real content,
`status: draft`) as of this session's fresh read. Corrected inline there per the HARD RULE that a misleading pointer
is a finding fixed on contact.

**Not done, deliberately**: the artifact HTML was not touched — the operator reviews these numbers before they reach
a client document, per this plan's own instruction. The "Build the artifact" and "Operator review" todos below
remain unchecked, correctly blocked on that review.
- **na-eligibility-audit 2026-08-17** [body-hash:13e6f20212196355]: KEEP-NA, valid -- Client-facing disclosure artifact with an explicit, hard disclosure boundary (archetypes-yes/edge-no, no commercial figures, code snippets limited to schemas/contracts) requiring ongoing editorial judgment against that boundary, not a mechanical build. All 7 pre-audit measurement todos are already done (checked). The 2 remaining todos are 'build the artifact' (content/design judgment applying the disclosure boundary to a large coverage dataset) and an explicit operator-review gate before any client-facing send. The doc's own Progress Log states this was deliberate.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) -- added `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`, the doc's own "read this first" comparison-track cite; other 3 re-verified, still resolve.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Client-facing disclosure artifact with a hard, operator-set disclosure boundary; all 7 pre-audit measurement todos are already done (checked). Of the 4 currently-open todos: 2 are the previously-audited. (1/4 items tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment.)

**2026-08-19 — 2026-08-18 artefact-remediation pass reconciled (`platform-external-api-walkthrough.html`)**: the
[`client_artefact_remediation`](/plans/archive/2026_08/client_artefact_remediation_2026_08_18.md) family (parent + nickai
child + siblings + elysium children) shipped and was independently re-verified this session (finalize pass) — §2/§3
external-API framing now names the concrete live surface and states TRADE-only-live / 10-of-11-types-501, all 6
`live` badges re-graded to `partial`, the forward claim cut, §4 coverage table + 288-venue figure reconciled, §14
names the 8-leg readiness-dump framework, §16 testnet claim qualified, §5 lede scoped, 7 absent + 4 thin capability
sections added (§18-§24 + §1 MDPS/features-service intermediary), and the evidence-tier `.ev-*` legend + 26
`class="own"` owner marks applied. Landing commits `unified-trading-pm@{ec08cccad1, 2b0c327e44, 19724f5e69}`
(per-todo evidence in the nickai child plan). The "Operator review before send" P0 gate below remains the standing
pre-send check — this remediation pass does not authorise sending the document anywhere.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — 4 open P0 items, all
  client-disclosure content-authoring/review work: re-grading every section mark against a stricter operator-ruled
  "live" definition, grounding-or-cutting an unsupported forward-looking claim (needs a citation-basis decision, not
  bounded implementation), building the artifact, and an explicit `[REVIEW]` "Operator review before send" gate.
  Correctly stays human-judgment work for a counterparty-facing disclosure document.
