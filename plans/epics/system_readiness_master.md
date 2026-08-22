---
doc_type: epic
title: System Readiness Master — everything except going live, by 2026-08-25
summary: >-
  Cross-product L4 umbrella for system readiness. Every venue with a code path carries a DERIVED batch / paper /
  live readiness state across instruments-service, MTDS, MDPS, features, strategy and execution; honest coverage is
  measured on every axis and every granularity; the strategy service is fully scaffolded, fully configurable from the
  wizard, and reads only processed data; execution carries full order lifecycle, reconciliation, and exchange-contract
  fidelity per venue. Deliberately EXCLUDES going live with capital. Also owns the presentation artefacts (Elysium
  carve-out, Nick AI platform disclosure) because they are the same work — a client-facing readiness claim and an
  internal readiness state are the same measurement.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    execution-service,
    deployment-api,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags:
  [
    system-readiness,
    honest-coverage,
    venue-readiness,
    strategy-wizard,
    reconciliation,
    order-lifecycle,
    risk,
    pnl-attribution,
    security-audit,
    skills-automation,
    client-disclosure,
  ]
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-17
name: system_readiness_master
tier: L4
priority: P0
assigned_vm: NA
execution_scope: local-only
parent: master_to_live_defi_2026_05_23
co_operators:
target_completion: 2026-08-25
codex_ssots:
  - /codex/02-data/honest-coverage-model.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/04-architecture/tier-and-import-architecture.md
  - /codex/06-coding-standards/config-reloader-pattern.md
  - /codex/09-strategy/operational/paper-batch-live-reconciliation.md
related_plans:
  - /plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md
  - /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md
  - /plans/active/venue_e2e_wiring_2026_08_16.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - /plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md
  - /plans/active/lazy_scoped_loading_refactor_2026_08_16.md
  - /plans/active/strategy_service_centralization_fixes_2026_08_16.md
  - /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md
  - /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md
  - /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md
  - /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md
last_updated: "2026-08-21" # was 2026-08-19 — linked venue_websocket_resilience_and_error_code_mapping_2026_08_21
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 60.0
estimate_calibrated_ai_days: 48.0
---

# System Readiness Master

## Report

Live HTML ledger: https://claude.ai/code/artifact/5a00f0e6-7480-4001-8cab-398e8a40fe34 (generated 2026-08-19,
`/plan-reconcile system_readiness_master`)

> **Target completion: 2026-08-25.** Everything in this epic except **going live with capital**. Paper, testnet,
> batch, readiness derivation, coverage, scaffolding, reconciliation, security — all in scope. Live capital is not.

> **This documents EVERYTHING that needs to happen, not everything that will happen by the 25th.** The operator's
> explicit instruction: the documentation says everything even where the schedule cannot. A workstream that slips is
> then a visible, tracked slip rather than an undocumented gap. **Do not scope this epic down to what looks
> achievable** — that decision is the operator's, taken against a complete picture.

> **Capacity context**: ~300–500 agent tasks/day through the orchestrator, largely parallel. Volume is not the
> constraint; correct decomposition and honest measurement are. Size workstreams for parallelism (disjoint file sets),
> not for a human's serial throughput.

## The organising principle — one derived readiness state, six services deep

Everything here serves one sentence: **every venue with a code path carries a batch / paper / live readiness state
that is DERIVED, never declared, across the whole chain.** The chain, per mode:

| Service | The question it must answer per venue × mode |
| --- | --- |
| instruments-service | Does reference data resolve, with coverage windows? |
| market-tick-data-service | Is every declared data type captured, at what granularity? |
| market-data-processing-service | Is the raw shard consumed into something derived? |
| features-service | Does a feature group consume it? |
| ml (published outputs) | Where an archetype consumes ML, is that output actually published — Pub/Sub for live, GCS for batch — for this venue and mode? |
| strategy-service | Is there a position adapter **for this venue, in this mode**, and **at least one archetype registration** for this venue in this mode? |
| execution-service | Is there an adaptor handling every action the eligible archetypes emit, plus transfers? |

**Derived means derived.** Per the 2026-08-16 ruling: a step with no real machine check reports `unverified` — never a
silent pass. A readiness table that cannot say "I don't know" is not telling anyone anything, and every percentage in
this epic carries its denominator and measurement date.

## Cross-cutting invariants — true in every workstream below

- **strategy-service reads ONLY processed data — and via transport or storage, never a service call.** Corrected by the
  operator 2026-08-17: the processed sources are **MDPS, features-service AND machine-learning outputs** — an earlier
  draft of this epic listed only MDPS and features, which understated it. What stays absolutely fixed is that
  **strategy-service never reads MTDS directly**; if a strategy appears to need raw ticks, the answer is a feature, a
  derived candle or an ML output, not an import.
  **The access pattern is the load-bearing half**: strategy consumes ML the same way it consumes any processed
  input — **Pub/Sub for live, GCS for batch** — *not* a direct service-to-service dependency. This is why adding ML as
  a source does not weaken the tier rule: strategy depends on UTL/UAC and reads published artefacts, so no new
  service-to-service edge is created. A direct call to an ML service would be a violation; reading its published
  output is not.
- **Execution fails closed on granularity.** A venue whose data cannot support a matching class is REFUSED, never
  matched as though tick data existed.
- **Everything declared lives in UAC** as far as possible — capabilities, registries, eligibility, weightings. SSOT in
  a contract, never inferred at runtime.
- **Credentials gate RUNNING, never BUILDING.** Exhausting the free path is a credential ask, not a descope.
- **Canonical paths and naming for every artefact**, including everything strategy-service emits.
- **A proxy is not the property** — a row count, an exit code, a green test, "the connector exists" are all proxies.

---

## W1 — Readiness derivation and the state dump

### The readiness matrix the operator actually wants (ruling 2026-08-19) — measured gap

Per **venue**, readiness for six surfaces, split by owning service, across three modes:

| Surface             | Owning service    | Mode coverage today                                                        |
| ------------------- | ----------------- | -------------------------------------------------------------------------- |
| **market data**     | MTDS              | ⚠️ `market_tick_data` leg is **BATCH ONLY** — no live-feed check exists     |
| **position**        | strategy-service  | ✅ `position_read_mode_availability(venue)` — genuinely batch/paper/live     |
| **orders**          | execution-service | ❌ no leg                                                                   |
| **fills**           | execution-service | ❌ no leg                                                                   |
| **trades**          | execution-service | ❌ no leg                                                                   |
| **account balance** | execution-service | ❌ no leg                                                                   |
| **credentials**     | execution-service | ❌ no leg — added as a 7th dimension 2026-08-19, see "Credentials" below   |

Measured against the shipped leg table in `cursor-configs/skills/readiness-state-dump/SKILL.md`: of 18 cells
(6 surfaces × 3 modes) we derive **position across all three modes, and market data in batch only**. The
`execution_transfers` leg checks `VENUE_WALLET_CAPABILITIES` membership (transfers, not the four operational
surfaces) and `execution_instruction` is explicitly _"none wired yet"_. **Modes are batch (simulated) / paper
(testnet and-or simulated per declared possibility) / live.**

- [x] [BACKEND] P0. ✅ **Extend the readiness dump to the full surface × mode matrix**, with the service split above —
      strategy-service owns positions, execution-service owns orders / fills / trades / account balance. Reuse real
      checks per the skill's own fact-vs-proxy policy; a surface with no machine check prints `unverified`, never a
      silent pass. — `unified-trading-pm@6817d944ec`. Added `execution_orders`/`execution_fills`/`execution_trades`/
      `execution_account_balance` legs to `checks.py` + a new `_execution_order_capability_probe.py` cross-venv
      probe (execution-service's own `get_supported_venues()` adapter registry + UAC's `validate_operation`
      per-env `place_order` capability — real checks, not invented proxies). Verified live 2026-08-19 against
      `OKX-FUTURES`: `execution_orders` derives `unverified` at BATCH, `ready` at PAPER/LIVE (UAC capability
      resolves supported for both testnet and mainnet); `execution_fills`/`execution_trades`/
      `execution_account_balance` derive `unverified` (adapter registered, no per-operation capability declaration
      exists to go further) — no surface silently passes. SKILL.md's leg table updated to match.
- [x] [BACKEND] P0. ✅ **Add a LIVE-feed leg to `market_tick_data`** — it currently answers batch only, so "can this
      venue's market data be pulled live?" is unanswered for every venue. Paper needs no separate feed leg: per
      [paper-batch-live-reconciliation](/codex/09-strategy/operational/paper-batch-live-reconciliation.md) § 0,
      **paper always consumes the LIVE feed**, never a testnet feed — testnet is an execution sub-mode, and a
      testnet price series would break the determinism proof by construction. So market data is a two-feed
      question (batch + live), not three. — `unified-trading-pm@6817d944ec`. Added `checks.mtds_live_feed()` (MTDS's
      own `WS_FEED_CONNECTOR_FACTORIES` registry, read via a new `_mtds_live_feed_probe.py` cross-venv probe that
      calls MTDS's own `connectors.register_all()` + `connector_registry.registered_venues()`) and wired
      `derive_readiness.py` so PAPER and LIVE rows reuse the SAME live-feed verdict, while BATCH keeps the
      pre-existing coverage.json-observed verdict — no separate paper feed leg was added. Verified live 2026-08-19
      against `OKX-FUTURES`: BATCH → `not_ready` (coverage.json, zero captured), PAPER and LIVE → identical
      `unverified` verdict (registered in `WS_FEED_CONNECTOR_FACTORIES`, live data flow itself unconfirmed).
- [x] [BACKEND] P0. ✅ **Archetype readiness is CODE completeness, not data availability.** The existing
      `strategy — archetype half` leg uses `satisfying_archetypes()`, which answers "which archetypes can this
      venue's DATA satisfy" — a different question from "are this archetype's code paths and hooks complete for
      batch / paper / live". Nothing answers the latter. Build it as a skill or script where the hooks are
      machine-detectable; where they are not, record a dated agent audit rather than leaving the cell blank. This
      supersedes the vaguer "readiness applies to archetypes too" framing below. — `unified-trading-pm@73c9e0036a`
      (`cursor-configs/skills/archetype-code-completeness/`). Checks 5 machine-detectable hooks across all 60
      `StrategyArchetype` members: `engine_factory` (`factory.ARCHETYPE_ENGINE_REGISTRY`), `param_schema`
      (`PARAM_SCHEMA_REGISTRY`), `target_universe_catalog` (`specs_for_archetype()`), `allocator_rank`
      (`ALLOCATOR_ARCHETYPE_REGISTRY`, mode-invariant), plus one mode-specific dispatch leg per BATCH
      (`STRATEGY_TYPE_TO_SLOT`) / PAPER (`paper_run_handler.py`'s 9 named tick-loader frozensets) / LIVE
      (`topology_enforcement.load_topology_requirements()`). Where no clean registry lookup exists (paper's
      non-DeFi-carry dispatch fallback, live's dispatch below the shared `V2EngineOrchestrator`), emits a DATED
      AGENT AUDIT record (2026-08-19) rather than guessing. Verified live 2026-08-19 against real strategy-service
      code (60 archetypes × 3 modes = 180 rows): counts cross-validate exactly against a direct read of every
      source registry (32 factory-registered engines, 35 param schemas, 8 dedicated allocator ranks, 12 paper
      tick-loader hits, 60/60 topology docs present). Rollup ~6 ready / ~47 not_ready / ~7 unverified per mode —
      only 32/60 archetypes have an engine at all today, the `VOL_*`/unbuilt `MARKET_MAKING_*` family accounting
      for most of the gap.
- [ ] [DOC] P1. **One shared readiness audit feeds BOTH client artefacts** (operator ruling 2026-08-19) — Elysium
      and Nick AI take the same underlying audit, not two per-artefact ones. It belongs to the shared parent
      remediation plan, not duplicated into the per-file children.

The spine. Everything else feeds it.

- [ ] [BACKEND] P0. **Auto-derive readiness per (venue × mode) across all six services** per the table above. Not a
      per-AG rollup — per venue, because readiness is uneven within an asset group and that unevenness is the signal.
- [ ] [BACKEND] P0. **Strategy leg, stated precisely**: a position adapter must exist for this venue in this mode, AND
      at least one strategy archetype must be registered for this venue in this mode. Both, not either.
- [ ] [BACKEND] P0. **Readiness applies to archetypes too**, not only venues — an archetype has its own batch / paper /
      live state, and a venue-archetype pair has one as well.
- [x] ✅ [SKILL] P0. **Build a readiness state-dump skill** — one invocation prints the current derived state across every
      venue, archetype, and mode, with `unverified` where checks do not exist. This is the artefact the presentation
      docs quote and the handover reader runs themselves. — `unified-trading-pm@5b3dbf99bd`
      (`cursor-configs/skills/readiness-state-dump/`). Shipped and verified live 2026-08-17 against real prod data
      (288 venues × 3 modes = 864 rows, ~20s), also recorded done in the gate-register plan's own "Tuesday dumps"
      section (`data_pipeline_completion_2026_08_21.md`). Grain is per (venue × mode); archetype is folded into the
      strategy leg's real AND-check (`position_read_mode_availability` + the shipped contract-step-17
      `satisfying_archetypes`) rather than reported as a separate third axis — the substantive ask (derived state,
      `unverified` surfaced honestly, runnable by a handover reader) is met. Re-run live 2026-08-18: rollup
      ready=0/not_ready=844/unverified=20 across 864 rows; `execution_instruction` leg 100% unverified fleet-wide —
      a real gap this dump now makes visible, not yet named elsewhere in this epic's Definition of done.
- [ ] [SKILL] P1. **Build a strategy-capability audit skill** — what can each archetype actually trade, given real
      coverage and real venue capability.

### Credentials — first-class readiness dimension (added 2026-08-19)

**Confirmed genuinely missing, not a duplicate tracker** (verified 2026-08-19 against
`/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md`, 3 open / 4 done): the W1 rollup's
six-surface table had no credentials/IAM dimension at all — a venue could show `ready` on every data/position/
execution leg while its actual API keys were still unscoped or unprovisioned in Secret Manager, a silent readiness
gap the matrix could not surface. **Credentials is now a 7th first-class dimension** (see the table above): per
venue, does the runtime identity hold a scoped (`{read,trade,write}`) GSM secret triple, and has a live authenticated
call been verified (not just an IAM policy dump)? Cross-reference, don't duplicate: the per-venue grant work itself
is tracked in `execution_master.md`'s "Venue MVP-readiness" P1 section (CeFi IAM grants for
bybit/hyperliquid/okx/aster, Kalshi/IBKR extension) — this workstream owns making credential-readiness VISIBLE in the
derived state, not owning the grants themselves.

- [ ] [BACKEND] P1. **Add a credentials leg to the readiness-state-dump skill** — per venue, `present` / `absent` /
      `unverified` (never collapsed, matching this epic's own W20 constraint on the venue-registry-completeness
      skill). `present` requires BOTH a scoped GSM secret AND a dated live-call verification, not either alone.
- [ ] [DOC] P2. **Name the full MVP-readiness acceptance cohort explicitly.** This epic's readiness matrix is
      measured on "all venues with a code path" in the abstract; the concrete 2026-08-19 priority set to close
      first is: CeFi (Deribit, Hyperliquid, Binance, OKX, Bybit, Aster), Ethereum DeFi (AAVE V3, Lido, EtherFi),
      sports (Betfair), Polymarket, Kalshi, IBKR, Morpho, Uniswap, CoW Swap, custody (Copper, CEFFU), plus the
      Solana spot+perp basis-trade set — **venue names now resolved 2026-08-19**: Jupiter, Raydium, Pacifica, and
      Jito (LST) per the real per-venue audit in `execution_master.md`'s "Solana venue set" section (Raydium and
      Jito confirmed genuinely registered/live-capable, not just referenced; Pacifica already fully shipped).
      **Drift is explicitly NOT part of this cohort pending resolution** — it was named in this session's operator
      instruction but conflicts with a standing, twice-stated codex kill ruling (last reaffirmed 2026-08-14); see
      the `[OPERATOR]` reconciliation todo in `execution_master.md`, don't add Drift here until that resolves. The
      Solana↔Ethereum BRIDGE architecture itself remains a separate, still-open placeholder (owned by a parallel
      agent in `codex/`, not duplicated here). Naming this cohort here gives the W1 dump's "which venues matter
      most right now" question a stated answer rather than an implicit "all 288".

### Manual execution mode — first-class alongside automated (added 2026-08-19)

Operator (2026-08-19), exact words: "the whole strategy service and execution need to understand that there's a
manual Live mode where everything is our own manual execution, and there's an automated Live mode." Cross-cutting
across every venue in the acceptance cohort above, not one venue's concern — full detail + code citations live in
`execution_master.md` and `strategy_master.md`'s matching todos (cross-reference, not duplicated here). For this
epic specifically: the W1 matrix's "position" and "orders/fills/trades" surfaces should be understood as being asked
once per **(venue x mode x manual-or-automated)**, not just per (venue x mode) — a venue can be automated-live-ready
while still lacking a manual-live path, or vice versa, and today's matrix has no way to express that distinction.

- [ ] [BACKEND] P2. **Fold a manual-vs-automated sub-axis into the readiness-dump extension** (the credentials-leg
      todo above and the surface x mode matrix todo already in this workstream) once the execution-service/
      strategy-service modeling decision lands there — do not build a parallel manual-mode concept here; this epic
      consumes that decision, it does not make it.

## W2 — Data pipeline integrity

> **Gate register**: [`/plans/active/data_pipeline_completion_2026_08_21.md`](/plans/active/data_pipeline_completion_2026_08_21.md)
> — operator-owned, deadline Friday 2026-08-21 with a Tuesday checkpoint. Holds the complete BATCH / PAPER / LIVE
> data-pipeline gate sets (20 BATCH gates, 12 PAPER, 13 LIVE) and cross-links each gate to its owning plan. That
> register is the SSOT for data-pipeline gates; this workstream's todos below are the ones with no other owner.

- [ ] [BACKEND] P0. **Manifest canonicalisation of every entry**, and **skip logic when `--force` is not used** — a
      re-run must not silently re-fetch what is already captured, and must not silently skip what is absent.
- [ ] [BACKEND] P0. **Manifest consolidators must be running, or VMs exit** — a launcher that proceeds against a stale
      index writes into a lie. Gate on index freshness and fail loudly rather than degrade.
- [ ] [BACKEND] P0. **Every venue's shards (instrument_type × chain × data_type) must be consumed by at least one of MDPS or features.**
      If nothing consumes it, storing it has no purpose — the shard is either a missing consumer or a data type that
      should not exist. Orphan output is a finding, never a footnote.
- [ ] [BACKEND] P1. **Cheap and safe coverage increase** — the download path must be both. Spot where possible, resume
      from measured progress, never replay from `START_DATE`, and never let a cost optimisation weaken a correctness
      check.
- [ ] [DOC] P2. **Historical replay data is itself a readiness gate, not just a nice-to-have — general principle,
      2026-08-19.** Operator's own framing (verbatim, re: CoW Swap): "we also need to have historical data for CoW
      batch-live symmetry, right? Otherwise we can't replay the market data... Should we simulate how that would
      have looked historically by having the data we would have got from that thing?" This is a direct instance of
      this workspace's own hard invariant (CLAUDE.md "Live = batch (event-log spine)...
      paper(W)==batch-rerun(W) epsilon=0"): a venue with a live execution adapter but no MTDS/MDPS historical
      capture cannot be backtested or paper-simulated, so it can never actually reach `ready` on the W1 matrix's
      paper/batch legs regardless of how complete its live leg looks. Pointer only, not a duplicate SSOT — the
      concrete instance (CoW Swap) and the general-principle todo are tracked in `mtds_mdps_master.md`; this note
      exists so "has historical replay data" is visible as a readiness dimension from this epic too, not just
      discoverable by reading the MTDS epic.

## W3 — Granularity as a first-class dimension

### Coverage denominator — the shard space is NOT a Cartesian product (operator ruling 2026-08-19)

The coverage SSOT already forbids the naive cross-product: per
[honest-coverage-model](/codex/02-data/honest-coverage-model.md), the expected matrix is keyed by
**`(asset_group, instrument_type)` at the writer/lowercase grain**, never the broad `DATA_TYPES_BY_ASSET_GROUP`
superset, "because using it as the denominator over-counts". The operator's 2026-08-19 ruling extends that:

- Take the dimensions that **actually exist for each shard at its deepest granularity** — data_type, chain,
  instrument_type, and per-AG axes — never a uniform product across all venues.
- **Sports gets instrument_type and chain too**, with **leagues** as a real axis. **Fixtures are excluded from the
  shard COUNT** (too noisy) but still belong in the full denominator.
- The **full denominator = shards × available days**. The **combinatoric view drops days** — that is the
  human-friendly number. Percentage completion is computed against the full denominator.

- [ ] [BACKEND] P0. **Reconcile the shipped denominator against this ruling.** Today's headline is 48.54% over a
      119,500,618 volume-weighted denominator across 3,960 shards. Confirm whether 3,960 is the true deepest-grain
      shard count including per-AG axes (sports leagues especially) or a coarser projection — the operator's
      expectation is that a genuinely exhaustive count is LARGER. Any change to the denominator is a change to
      every published coverage number, so land it as a dated supersession, never a silent edit.
- [ ] [BACKEND] P0. **The readiness dump is coarser than the coverage model — close the gap.**
      `readiness_pipeline_stage_per_shard_2026_08_18.json` is `venue × asset_group × mode` (864 rows) and its rows
      carry no `instrument_type` or `data_type`, so it cannot answer the per-shard question at all. Scope is
      pipeline-only (declared → instruments_service → market_tick_data → MDPS → features), which is CORRECT and
      should stay: strategy and execution are ephemeral — they scale with config iterations and client count, so a
      percentage is meaningless there. Coverage % is a statement about the pipeline up to features, and should say so.
- [ ] [DOC] P1. **Its `grain` field is mislabelled** — it declares `grain: instrument_type` while no row carries an
      `instrument_type` key. Anyone trusting the label believes they have a finer breakdown than exists. Fix the
      writer, not just the file.


- [ ] [BACKEND] P0. **Model coverage per (venue × instrument_type × data_type × granularity)** — candles versus tick
      entering MTDS are different coverage questions, and coverage may be **better at one granularity and worse at
      another** for the same venue and data type. A single number across granularities hides exactly the fact a
      strategy needs.
- [x] [BACKEND] P0. ✅ Done 2026-08-17 — `unified-api-contracts@d19866d339`. **Land the instrument_type axis on the
      coverage denominator** — new additive module `venue_instrument_type_axis.py` (inverts the existing G1-ENUM
      combinator rather than mutating `VenueCapabilityRecord` in place). Denominator re-measured: 353 (venue,
      data_type) pairs → 660 (venue, instrument_type, data_type) triples, 12 cells (3.4%) disclosed unresolved.
      Full evidence: `/plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md` § W3.
- [ ] [BACKEND] P1. **Declare exceptions at the granularity they occur** — venue / instrument_type / data_type, with
      the exception stated rather than implied by absence.

## W4 — Observability, alerting and auto-recovery

- [ ] [BACKEND] P0. **Data-pipeline alerts for deployment health across VMs and Cloud Run**, with auto-escalation and
      auto-reconciliation. Standing conditions dedup by state transition; automatic lifecycle events never page.
- [ ] [BACKEND] P0. **Data-status honest-coverage rollup AND drilldown for instruments-service, MTDS, MDPS and features** —
      the rollup is the headline, the drilldown is what makes it believable.
- [ ] [BACKEND] P0. **Spot preemption auto-recovery resumes at the right place** — from measured progress, never a
      replay. A recovery that restarts from the beginning is a cost bug wearing a correctness mask.
- [ ] [BACKEND] P0. **No duplicate VMs running.** Detect and prevent, do not merely alert.
- [ ] [BACKEND] P1. **Canonical GCS paths for everything, and clean up backup / stale / old paths** — deletes stay
      proof-gated and prod-bucket deletes remain human-only unless reversibility-qualified.
- [ ] [BACKEND] P1. **DR procedures, automation and cost optimisation** documented top-down across the data pipeline
      and deployment surface.

## W5 — Venue registry completeness

The registry must answer commercial and operational questions, not just "does this venue exist".

- [ ] [BACKEND] P0. **Collateral that can actually be used, per venue — populate the remaining ~50-58 venues.**
      Re-verified 2026-08-18 (client_artefact_remediation_2026_08_18.md § E research todo): the schema already
      exists — `VenueCapabilityV2.collateral_rules` (`CollateralRulesV2`: per-asset LTV/haircut,
      `cross_margin_supported`, `portfolio_margin_supported`) in `unified-api-contracts/unified_api_contracts/
      internal/architecture_v2/schemas.py` — and is already consumed by `strategy-service/strategy_service/
      risk/v2/{margin_sim,preflight,orchestrator}.py`. **2026-08-22 correction**: the research doc's "populate,
      don't design" framing was itself incomplete — the registry/resolver mechanism (a `dict[venue_id,
      VenueCapabilityV2]` + resolver function) didn't exist either, so there was nowhere to populate INTO. Both
      are now built: `unified_api_contracts/registry/capability_declarations/venue_capability_v2/` (split by
      venue family — `_cefi_derivatives.py`, `_defi_lending.py`), `get_venue_capability_v2(venue) ->
      VenueCapabilityV2 | None`, seeded with 2 real venues (`BINANCE-FUTURES`, `AAVE_V3-ETHEREUM`) and wired
      into `strategy-service`'s `FourLayerGateOrchestrator.evaluate(venue_id=...)`. Remaining work is genuinely
      population-only now: ~50-58 more relevant CeFi-derivatives/DeFi-lending venues, each real-sourced with a
      cited official URL per number (no guessed values — see the two seeded entries for the pattern). See
      [research findings](/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md).
- [ ] [BACKEND] P0. **Cross-margin logic where it exists**, declared rather than discovered — same
      `MarginSpec`/`CollateralRulesV2` population gap as above, not a separate design task.
- [ ] [BACKEND] P0. **Transfer capability per venue as explicit eligibility flags**: Copper-eligible, Ceffu-eligible,
      manual-transfer-eligible, automated prime-broker-eligible (per prime broker), IBKR / Alpaca eligible.
      Re-verified 2026-08-18: genuinely absent — no existing field on `VenueCapabilityV2` or elsewhere declares
      this, unlike collateral/margin above (which at least has an unpopulated schema). This one needs new fields,
      not just population.
- [ ] [BACKEND] P0. **Manual trade capability for EVERY venue** — no exceptions. This is the disaster path.
- [ ] [BACKEND] P1. **All of the above in UAC**, as declarations — not inferred at runtime.

## W6 — Strategy archetype scaffolding, config and the wizard

- [ ] [BACKEND] P0. **Scaffold ALL strategy archetypes, not just the MVP ones.** The MVP set must be understood
      deeply, but the scaffolding of every archetype is what prevents a heavy refactor each time another comes online.
      The structure is the deliverable here, not the alpha.
- [ ] [BACKEND] P0. **Every archetype / family / slot fully configurable, with all config in `config*.py` in the same place**,
      hot-reloadable **including credentials**.
- [ ] [BACKEND] P0. **Configuration must be fully derivable from the strategy wizard** — the wizard is not a
      convenience layer, it is the sanctioned way config comes into being, and an agent must be able to drive it.
- [ ] [BACKEND] P0. **Complete the strategy wizard.** Every stage, constrained by the layer beneath it, emitting config
      valid by construction.
- [ ] [BACKEND] P0. **Strategy logic follows codex** — non-negotiable, and reviewable.

## W7 — Centralisation and anti-drift

- [ ] [DOC] P0. **Generalise the slow-path/fast-path boundary beyond venue routing — EXTEND the existing SSOT, do NOT author a new one.**
      Operator ruling 2026-08-18 restated the boundary as: *strategy decides WHAT we want to
      do (slow path) and hands execution a cache it can react to fast on a tick basis; execution decides HOW (fast
      path).* Measured 2026-08-18: that boundary IS owned, but only for venue routing —
      [/codex/04-architecture/slow-fast-routing-split.md](/codex/04-architecture/slow-fast-routing-split.md) is
      `authoritative_for: [slow-fast venue-routing split architecture]` and returns **zero** hits for
      transfer/gas-top-up/reserve/capital-budget;
      [/codex/04-architecture/strategy-execution-protocol.md](/codex/04-architecture/strategy-execution-protocol.md)
      owns the instruction protocol (5 rules, 11 actions);
      [/codex/04-architecture/transfer-coordinator.md](/codex/04-architecture/transfer-coordinator.md) states no
      owner for thresholds or policy at all. **So fund-movement policy and capital-budget enforcement have no
      declared slow/fast owner** — extend the routing-split doc (or add a sibling section it links) to cover them.
      A third doc would be the exact duplication this workstream exists to prevent.
- [ ] [DOC] P0. **Cite that boundary from the transfer-handler P0 before it is implemented** —
      `elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md` § C is open and unclaimed. Concrete
      risk: gas top-up needs a reserve threshold, and today there is "no handler, no reserve-threshold logic
      anywhere." If that logic lands inside `TransferCoordinator`, execution-service acquires a policy decision,
      needs per-chain/per-venue reserve tables locally (breaking venue-agnosticism), and gets consulted on the fast
      path — three violations from one reasonable-looking commit. Required shape: thresholds/policy resolve
      slow-path into the cache; execution handlers only execute a pre-computed decision. Same question applies to
      "capital budget enforced by construction" — a per-tick budget check in execution is a slow-path concern
      leaking into the fast path.
- [ ] [DOC] P1. **Fold the tick-cache mechanism into the boundary SSOT — the design work is ALREADY DONE, do not re-derive it.**
      The operator's "strategy hands execution a cache it reacts to on a tick basis" framing is
      real and has real code, independently established by a concurrent session on 2026-08-18
      (`unified-trading-pm@219a310df0`):
      [/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md](/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md)
      gives the full 3-layer design — Layer 1 strategy publishes intent, Layer 2 the execution-side
      trigger/sensitivity cache, Layer 3 the order-fill algo. `execution_service/engine/delta_proxy_repricer.py`
      already implements it (strategy publishes reference price + delta/gamma ONCE; execution extrapolates per tick
      with a `max_adjustment_pct` staleness clamp that flags `stale=True` rather than extrapolating past a sane
      bound), with real dataclasses and unit tests, plus `QuoteMaintainer` wiring it to a submitter protocol.
      Blocked on: UAC's `QuoteInstruction` carrying no `delta`/`gamma`/`underlying_instrument_id` (wiring defaults
      `delta = 1.0`, the spot/perp self-underlying case only), and the strategy-side receipt point (`QuoteHandler`)
      having been deleted 2026-08-15 as dead code with no replacement. **This epic's job is to cite it, not restate
      it** — the boundary SSOT names this as the canonical instance of the slow→fast cache handoff and links out.
**Ownership split — W16 delivers, W7 constrains.** The design doc is pointed at from two workstreams (W16 in the
issue-doc corpus below, W7 here) and that is intentional, but ownership is singular: **W16 — Triggers, latency and
preflight owns BUILDING the sensitivity/trigger cache**; W7 owns only the invariant that it must not become
execution-owned policy. Do not open delivery todos for the cache here — they belong to W16 and the design doc.

The 11 judgment calls are tracked in the design doc itself and are NOT restated here — that doc is the single place
of record, and a second tickable copy is exactly the duplication this workstream exists to prevent. Three of them
bear on W7's principles and should be ruled consistently with them: **#4** (is "never branch on archetype"
*structurally* enforced or merely conventional — strategy-agnosticism), **#9** (reuse `order_semantics.py`'s
existing per-venue vocabulary rather than inventing a parallel schema — SSOT), **#10** (execution consumes
strategy's `ExposureAggregator` rather than keeping a duplicate local exposure view — no same-concern-in-two-places).

- [ ] [PROCESS] P1. **Re-tag the design doc's gated todo so AO cannot pick up an operator decision.** Its
      `[DESIGN] P1` todo reads "Design `ExecutionSensitivityEntry` + `AmbientMarketLean`, resolving judgment calls
      1-5 and 9" — that bundles an operator ruling with worker-executable design. Per the dispatch-eligibility rule
      (an AO todo's outcome must be determinable by the worker alone), the rulings need their own `[OPERATOR]` gate
      in that doc, with the design todo gated behind it. Same check for the `[DESIGN] P2` todos resolving calls 7
      and 8. Without this, a worker either invents a ruling or stalls.

- [ ] [BACKEND] P0. **Every strategy-agnostic module and function call lives centrally**, so multiple archetypes call
      one implementation instead of reimplementing it. Reimplementation is drift with a delay fuse.
- [ ] [BACKEND] P0. **Reference / registry / config data must never live inside a single strategy's code path** — the
      four-destination rule (UAC / service config via the reloader / UTL / a centralised domain module) decides where
      it goes. Tracked in `/plans/active/strategy_service_centralization_fixes_2026_08_16.md`.
- [ ] [BACKEND] P0. **Position-risk / margin health must be asset-group-agnostic** — DeFi, CeFi and (once built)
      TradFi leverage share ONE generic collateral/exposure/health-ratio core; only the per-venue-type sourcing
      adapter differs. Ruled 2026-08-17: not an asset-group-specific module. SSOT:
      [position-risk-centralization](/codex/04-architecture/position-risk-centralization.md).
- [ ] [AGENT] P0. **Reconcile the two parallel position-risk mechanisms discovered 2026-08-17** —
      `DeFiHealthAggregator` (DeFi-only, not live-fed) versus the already-live, already-cross-service
      `margin_event_emitter.py`/`MarginEvent` pipeline built on UTL's generic core. Converge on one before any
      archetype wires onto either. Tracked in
      `/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md`.
- [ ] [OPERATOR] P3. **Target November 2026 — decide whether to extract `position-balance-monitor-service` (PBM)
      into its own deployed service.** Today PBM's role lives inside strategy-service's `position/` package on top
      of UTL, so a strategy-service restart has no external source to recover position/margin truth from, and
      `margin_event_emitter.py`'s own docstring names execution-service, alerting-service and
      risk-and-exposure-service as consumers whose position-awareness is currently coupled to strategy-service's
      uptime for no domain reason. Deliberately deferred — not blocking this epic's 2026-08-25 target. Full
      reasoning and the target topology: `/codex/04-architecture/runtime-deployment-topology.md` (Layer 6).
- [ ] [OPERATOR] P3. **Target 2027 — decide whether to extract `risk-and-exposure-service` and
      `pnl-attribution-service` into their own deployed services**, per the same Layer 6 target topology in
      `/codex/04-architecture/runtime-deployment-topology.md`. Same un-split gap as PBM (both currently live inside
      strategy-service/UTL, not as separate repos), but a materially later target than PBM (operator ruling
      2026-08-18) — scope as its own decision when the time comes, not bundled with the PBM extraction above.

## W8 — Weightings, declared not inferred

- [ ] [BACKEND] P0. **Define which dimension each weighting applies to, in the contracts registry as SSOT.** Strategy
      slot weightings apply on a portfolio basis per client; coin and venue weightings can, for some archetypes, live
      on the archetype itself. Both are legitimate — what is not legitimate is inferring which at runtime.

## W9 — Account balances: the single strategy I/O

- [ ] [BACKEND] P0. **Account balances are the raw balances of our positions at `instrument_id` granularity**, with
      columns that allow slicing and summing by **venue, client, strategy slot, strategy archetype, expiry and
      instrument type**. It exposes the right columns and fields; it does **not** do the summing or slicing itself.
- [ ] [BACKEND] P0. **This is the ONLY strategy-service I/O, and it lives in one place.** Lookup tables are fine; the
      point is one presentation surface rather than several partial ones.
- [ ] [BACKEND] P0. **Normalised by share class AND USD equivalent — always both**, so native-share-class positions and
      dollar positions are visible on their own axes.
- [ ] [BACKEND] P0. **Normalised exposure is a first-class data type emitted by strategy-service**, alongside account
      balances, risk, PnL and PnL attribution.

## W10 — Risk and exposure

- [ ] [BACKEND] P0. **Risk exposure raw in native token terms AND normalised into share-class terms**, so it sums and
      breaks down on both axes.
- [ ] [BACKEND] P0. **Dimensions**: account (a specific instance of a venue for a client), instrument_id, instrument
      type — and every Greek: net delta, basis risk, and the rest.
- [ ] [BACKEND] P0. **Satisfy the risk dimensions the UI (DART) already needs** — there is real information there and
      the data model must serve it rather than diverge from it.

## W11 — Order lifecycle and execution state

- [ ] [BACKEND] P0. **Every incremental step of the order lifecycle is stored in the order table** — creates, updates,
      deletes, cancels — in a normalised format, with the **exchange reason derived from the request, response and
      error codes**.
- [ ] [BACKEND] P0. **Execution-service must restart and recover its state.** A restart that loses in-flight state is
      an incident generator.
- [ ] [BACKEND] P0. **In-flight versus post-confirmation must be distinguishable** — a cancel attempted before
      confirmation and one after are different events, and an audit record that cannot tell them apart cannot answer
      the question that matters after an incident.

## W12 — Reconciliation

- [ ] [BACKEND] P0. **Per-venue reconciliation where venue specifics change behaviour, normalised to one generic
      model** everywhere else: thresholds, tolerances, intervals, and defined behaviour when reconciliation is bad or
      down.
- [ ] [BACKEND] P0. **Auto-adjustment of positions via booked reconciliation entries** — the correction is itself an
      audited entry, not a silent overwrite.
- [x] ✅ [BACKEND] P0. **Manual trades bookable as seen-by-the-system or not-seen**, for disaster cases: we know we
      hold a position, reconciliation has not caught up, and it must not delete that position. Reconciliation pauses
      BEFORE manual entry; persistent-delta (virtual) entries are excluded from the reconciliation delta.
      `recon_excluded` threaded through `ManualInstruction`/`TradeFillRecord`/`LedgerRow` and BLRS's ledger-matching
      skip (tested). **Closed 2026-08-21 (T4 tranche)**: the functional half landed same day — manual fills now
      write a real `TradeFillRecord`/`LedgerRow` via `manual_instruction_ledger.py` (same `write_run_ledger`
      batch/paper path), `execution-service@ee694cf46b` + `unified-trading-library@707020ff7b` — so
      `recon_excluded` has a real live `LedgerRow` to act on for manual fills, per
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §7 G6. **Strategy-driven live fills remain
      unwired** (out of this todo's manual-trade scope; would need its own follow-up if wanted).

## W13 — PnL attribution

- [ ] [BACKEND] P0. **Attribute PnL across every risk metric and exposure-normalisation metric, in the same dimensions
      and buckets.** If exposure can be sliced a certain way, PnL must be attributable the same way — otherwise the two
      cannot be reconciled against each other.

## W14 — Exchange contract fidelity

- [x] [BACKEND] P0. **Every venue error code understood across every consumer** — ✅ unified-api-contracts@3b13629f9f
      (exhaustive doc-cited per-venue error tables, ~2,000 codes across CeFi/DeFi/TradFi/sports/prediction/altdata)
      + unified-api-contracts@235acfea88 (census closure: every adaptered venue resolves a venue-error table or an
      explicit honest-absence marker, every capability declares its ws protocol, zero dead-duplicate keys —
      `tests/unit/test_registry_census_ws_resilience.py`, gated as UAC STEP 5.110). Consumers classify through the
      UAC registry by construction (`classify_venue_error` call sites measured 2026-08-22: MTDS 117,
      instruments-service 60, execution-service 85, strategy-service 5). Executed by
      `/plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md`.
- [ ] [BACKEND] P0. **Pin the exchange version tested**, so a venue-side version change triggers a **cassette re-run to
      detect drift** — and only then, not on every build.
- [ ] [OPERATOR] P0. **Test accounts with credentials for each venue** — a prerequisite for the above, and an operator
      action rather than an engineering one.

## W15 — Security

- [ ] [BACKEND] P0. **Security audit of every venue adaptor for vulnerabilities, especially DeFi.** On-chain write
      paths carry irreversible consequences; this is not a documentation exercise. **Status 2026-08-22 (re-verified
      against the plan's live checkbox state, not a prior summary)**: dedicated plan
      `/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md` — all 13 audit phases
      complete (incl. sports-unity, the last one, 2026-08-22) and **zero open P0s remain**. Everything still open
      is P1/P2 follow-up work, each already tracked with an explicit reason in its own todo text (full Orca/Raydium
      account derivation; Kamino on-chain market cross-check; wiring the real on-chain calls behind the
      staking/restaking fail-closed guards; EigenLayer pre-deposit approval + Karak vault address; 3 Unity
      input-validation/fill-parsing/idempotency follow-ups; native rate-limit/blocking-sleep hardening; 2 P2
      dead-code fixes). NOT a close-out claim — see that plan's live Todos section, not this line, for current
      per-item status.

## W16 — Triggers, latency and preflight

- [ ] [BACKEND] P0. **Each strategy's triggers explicitly understood** — what it grabs and when: time-based,
      event-based. The normal shape is Pub/Sub broadcasting events, the strategy subscribing, then reading the data off
      the stream.
- [ ] [BACKEND] P0. **Every artefact records time-data-received and time-data-sent** for latency analysis and tracing.
- [ ] [BACKEND] P0. **Preflight registration checks fail if required data is absent** — at registration, not at
      runtime. Discovering a missing input mid-run is the expensive way to learn it.
- [ ] [BACKEND] P0. **An SLA per input for how long is a reasonable wait before data is considered stale.**
- [ ] [BACKEND] P0. **RULED 2026-08-18 — missing or stale required data fails CLOSED, not open, as the default
      across every archetype.** Concrete trigger: while wiring the DeFi own-leverage gates onto real position data
      (`strategy_service_centralization_fixes_2026_08_16.md`), found the current gate logic treats a missing
      health factor as "no check, proceed" — meaning a genuinely underwater leveraged position could trade
      unchecked during any gap before the live poll first populates. Operator ruling generalizes this beyond the
      one gate: **every strategy archetype must be considered startup-ready only once it has fresh data across
      everything it needs** — position, PnL, risk, the specific venues it trades, and every market-data
      type/feature group it consumes — each checked for both **presence** (the W16 preflight registration check
      above) **and freshness** (the SLA-per-input line above), with **absent or stale failing closed by default**.
      This is the behavior the two checks above were implicitly assuming but never stated; this line makes it
      explicit. Done-when: a named startup-readiness check exists per archetype covering all of the above
      dimensions, defaulting fail-closed, with any deliberate fail-open exception stated and justified per input,
      not assumed by an unhandled-`None` code path. First concrete instance:
      `strategy_service_centralization_fixes_2026_08_16.md`'s DeFi health-factor gates.
- [ ] [BACKEND] P1. **Generic price-sensitivity contract for fast execution-side repricing — real infra exists,
      unwired on both ends.** Found 2026-08-18: execution-service already has a fully-written, unit-tested
      delta/gamma linearization engine (`DeltaProxyRepricer` + `QuoteMaintainer`) that is exactly the "strategy
      caches a reference + sensitivity once, execution-service extrapolates cheaply against a live feed without a
      round-trip" pattern this workstream's Pub/Sub-triggers model implies — but its strategy-side receipt point
      (`QuoteHandler`) was deleted 2026-08-15 as dead code with no replacement, no live underlying-tick loop drives
      it, and the arb-leg-repricing analog (`price_dispersion.py`) has zero implementation at all (only an unused
      declarative enum naming the concept). Full detail + 9 todos:
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md`.

## W17 — Fees and gas

- [ ] [BACKEND] P0. **Fees broken down into clearing, broker, exchange, gas, and other** (a loose field — for example
      paying for execution via a third party), in both strategy-service and execution-service, so strategy can bake
      them into the decision and execution can bake them into alpha PnL.

## W18 — Canonical output paths for strategy-service

- [ ] [BACKEND] P0. **Canonical path structure and naming for everything strategy-service emits** — risk, account
      balances, raw and normalised positions, PnL attribution, strategy instructions — and it must hold for carry,
      arbitrage, options, sports, machine learning, every asset group. One grammar, no per-archetype dialects.

## W19 — Corpus audit: what already exists, and what has rotted

- [ ] [AGENT] P0. **Audit every plan/issue doc `created:` within the last 7 days** — there is a great deal directly
      relevant to this epic, and it must be folded in rather than duplicated. **Key off the `created:` frontmatter, not
      file mtime**: 781 of 804 active docs have an mtime inside 7 days purely because pulls touch files, so mtime is a
      false signal here.
- [ ] [AGENT] P0. **Audit older docs for two distinct failure modes**: (a) issues and completions that are genuinely
      still outstanding, and (b) content that is **out of date versus the upgraded logic** — a doc describing the old
      model is worse than no doc, because it is believed.
- [ ] [AGENT] P1. **Fold, supersede or archive** — every audited doc resolves to one of: folded into this epic's
      workstreams, superseded with a banner, or archived. No doc stays ambiguous.

## W20 — Skills and automation

Automation is how 300–500 tasks/day becomes throughput rather than churn, and it is the beginning of handover
documentation. These extend the existing skill corpus. **The constraints under each item below are load-bearing,
not commentary** — derived once, and otherwise re-derived or missed by whoever builds the skill.

- [x] ✅ [SKILL] P0. **Readiness state dump** (see W1) — venue × archetype × mode, derived. — Shipped, same evidence
      as W1's checkbox (`unified-trading-pm@5b3dbf99bd`).
- [x] ✅ [SKILL] P0. **Honest coverage dump** — per-shard coverage from the manifest, four capture states separately,
      denominator stated. Shipped `unified-trading-pm@5b3dbf99bd` alongside the readiness dump; evidence in
      `/plans/active/data_pipeline_completion_2026_08_21.md` § "Tuesday dumps". **Was missing from this list
      entirely** — added 2026-08-18 so the epic's skill inventory is complete.
- [ ] [SKILL] P0. **Strategy capability audit** — what each archetype can actually trade given real coverage.
      **Constraint**: its output is honestly PARTIAL by construction — `ARCHETYPE_FEATURE_GROUPS` declares ~40 of 60
      archetypes and its docstring deliberately refuses to guess the rest ("a wrong entry would silently mislead a
      contract-step-17 BACKTESTABLE check — worse than an honest gap"). Report the remainder as a measured limit; do
      NOT fill it. This is also why the 2026-08-18 readiness dump's strategy leg passes only 24/864.
- [ ] [SKILL] P1. **Venue registry completeness check** — collateral, cross-margin, transfer eligibility, manual-trade
      capability, per venue.
      **Constraint**: report three distinct values — present / absent / `unverified`. An absent capability and an
      unchecked one are different findings and must never be collapsed. Manual-trade capability is required for EVERY
      venue with no exceptions (it is the disaster path), so its absence is a P0 finding, not a noted gap.
- [ ] [SKILL] P1. **Shard utilisation / orphan sweep** — every shard consumed by MDPS or features; every declared
      data_type, instrument_type, venue and chain consumed somewhere.
      **Constraint (SAFETY)**: emits a CONSUMPTION VERDICT ONLY — **never a delete suggestion**. A false orphan verdict
      could send someone deleting live data; runtime-resolved consumers do not appear in a token grep, so it must READ
      the consumer rather than infer from grep count, and print `unverified` when uncertain.
      **Constraint (consistency)**: reuse the shard-enumeration engine the two shipped dumps share
      (`scripts/shard_universe.py`) — a third independent enumeration would disagree on the denominator, which is worse
      than being slower.
- [ ] [SKILL] P1. **Exchange contract drift check** — cassette re-run gated on venue version change.
      **Blocked on the OPERATOR, not on engineering**: needs test accounts with credentials per venue (W14) before
      cassettes can be pinned. Do not dispatch ahead of those credentials or it stalls mid-build.
- [ ] [SKILL] P2. **Strategy config completeness check** — every archetype/family/slot fully configurable and
      wizard-derivable.

## W21 — Presentation artefacts

Not a separate track. A client-facing readiness claim and an internal readiness state are the same measurement, which
is why they share this epic — and why an artefact number that outruns the derived state is a defect, not a
presentation choice.

- [ ] [DOC] P0. **Nick AI platform disclosure artifact** — 36 figures currently marked pending; all resolve from W1–W3
      measurement. Quote the denominator with its unit, state the volume-weighted basis explicitly, and omit any figure
      without a measured basis.
- [ ] [DOC] P0. **Elysium carve-out artefacts** — keep aligned to the same derived state; the carve-out's own
      readiness claims must not diverge from this epic's numbers.
- [ ] [DOC] P1. **Every artefact regenerates from measurement, not from prose.** Where a number is quoted, its source
      and date are recorded, so the next edition is a re-run rather than a re-write.

### The closure invariant — measured 2026-08-18, and it is NOT "everything under this epic"

The operator's goal is: *build the epic in full, and the two artefacts have nothing missing.* Corpus topology says
that cannot be delivered by parenting work under this epic. **This epic declares a single-digit number of docs; the
other ~850 hang off ~30 other epics**, and that distribution is correct — the artefacts' claim surface legitimately
spans work owned by many of them. Do not flatten it.

**Derive the numbers, never quote them from here.** A frozen snapshot in this section was already wrong within
hours: the 2026-08-18 taxonomy restructure (9 `parent_epic` reclassification batches + 3 new epics — `ci_master`,
`uac_master`, `security_and_cross_cutting_master`) moved the single largest owner from `infrastructure_master` at
297 to `security_and_cross_cutting_master` at 212, while epics went 29 → 32. Any reader relying on the old list
would have been misled about who owns what. Re-derive with:

```bash
ls plans/epics/*.md | wc -l                                        # epics
rg -N --no-filename '^parent_epic:' plans/active/*.md plans/active/issues/*.md \
  | sed 's/parent_epic: *//' | sort | uniq -c | sort -rn           # ownership distribution
for f in plans/active/*.md plans/active/issues/*.md; do rg -qN '^parent_epic:' "$f" || echo "$f"; done
```

**True orphans are already zero** — corrected 2026-08-19: the 3rd exemption cited below
(`_cefi_canonical_blueprint_2026_07_17.md`) was a real gap, not a legitimate exclusion — renamed (dropped the stale
underscore-prefix), given a `parent_epic: cefi_master`, and archived (0 open todos, resolved-by-reference to an
already-completed forked plan). Only `INDEX.md` and `_agent_pings.md` remain as genuine, non-plan exemptions. So
corpus-level orphan hygiene is not the gap. **The gap is directional** — nothing checks that every artefact CLAIM has
a tracked owner. Invert the invariant: not "every plan hangs under this epic" (wrong direction, ~850 docs) but
**"every claim-bearing artefact section maps to a tracked item, wherever it lives."**

**This invariant has already failed once, measurably.** The 2026-08-18 second-pass audit found P0 disclosure
violations in four sibling client artefacts (`strategy-service-deep-dive.html`, `platform-architecture.html`,
`carveout-engineering.html`, `ODUM_Elysium_Phase2_Update_2026-07-24.html`) — none of which is covered by any
remediation plan, because the only such plan scopes to the two audited documents. Four client-sendable documents
carrying hard-rule violations, with no owning plan, is exactly the orphan class this section exists to catch.

**True orphans are already zero**: exactly 2 active docs lack a `parent_epic` key, both genuine non-plan exemptions
(`INDEX.md`, `_agent_pings.md`) — see the correction above. So corpus-level orphan hygiene is not the gap. **The gap
is directional** — nothing checks that every artefact CLAIM has a tracked owner. Invert the invariant: not "every
plan hangs under this epic" (wrong direction, 851 docs) but **"every claim-bearing artefact section maps to a
tracked item, wherever it lives."**

- [ ] [DOC] P0. **Give every claim-bearing artefact section a third mark: its OWNER** — the workstream, plan or
      epic that closes the gap. With the status mark (what the system does) and § E's evidence tier (how we know),
      the artefact becomes an index INTO the corpus: scroll it, and every non-`live` claim names who is delivering
      it. **A section with no owner is the orphan class that actually threatens this epic's promise** — an artefact
      claim nobody is tracking — and nothing currently measures it. **Spec defined**:
      [rule 13 — artefact claim marks](/codex/14-customer-journeys/_ssot-rules/13-artefact-claim-marks.md)
      (`unified-trading-pm`, client_artefact_remediation_2026_08_18.md § E) — exact CSS, markup and the owner-mark
      content grammar (workstream shorthand vs plan short-tag vs epic slug). Applying it to the two lead artefacts
      is tracked in the elysium/nickai children of that plan; this item stays open until both apply it.
- [ ] [SCRIPT] P0. **Bidirectional closure check between the artefacts and the corpus.** Forward: every
      claim-bearing section resolves to a live tracked item (fail on an unowned section). Reverse: every workstream
      here is either referenced by an artefact section or explicitly marked internal-only — so a capability we hold
      but never disclose is a deliberate choice rather than an oversight. Run it in the hygiene sweep so the answer
      is refreshed, not remembered.
- [ ] [SCRIPT] P1. **Extend the orphan check to issue docs.** `scripts/plans/regenerate_active_plan_inventory.py`
      defines orphan as "plan not referenced by master or any epic" but covers `plans/active/*.md` only — measured
      2026-08-18: **the 489 active issue docs are outside its scope entirely**, against 356 plans inside it. Issue
      docs are where agent-generated findings land, so they are the highest-churn and highest-orphan-risk class in
      the corpus.
- [ ] [PROCESS] P1. **Agent-generated docs must be swept in on a cadence, not noticed by luck.**
      `execution_delta_proxy_repricer_generalization_2026_08_18.md` was folded into W7 only because an interactive
      session happened to read a `git log` line while shipping something unrelated. It was well-formed (it declared
      `parent_epic: system_readiness_master` itself), so the sweep only has to FIND it — but discovery by
      coincidence does not scale to ~300–500 agent tasks/day. Fold this into the existing daily
      `/plan-reconcile` sweep rather than adding a new mechanism.

## W22 — Strategy/execution messaging and the external instruction API

Operator ruling 2026-08-19: the bridge from a strategy's decision to execution is currently unmeasured and,
per a workspace-wide search on 2026-08-19, unbuilt end-to-end — the only live instruction path is the manual one
(`ManualOperationHandler → LiveOrchestrator.execute_instruction()`), not an automated strategy-to-execution bridge.
This workstream is that bridge, plus what it takes to expose the same instruction contract to an external client
two ways: we host it, or they run our container themselves. Surfaced while auditing
[`platform-external-api-walkthrough.html`](/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html)
§25 for [`client_artefact_remediation_nickai_2026_08_18.md`](/plans/active/client_artefact_remediation_nickai_2026_08_18.md).

- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-21 — execution-service@79e951ea (subscriber) + execution-service@99962afa1f (startup wiring).
      Strategy instructions now reach execution through the UTL `EventTransport` facade, not a service dependency;
      Evidence: both commits exist and are ancestors of `origin/live-defi-rollout`, with the source plan evidence from `bash scripts/quality-gates.sh --no-fix`. Source: `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`.
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-20 — execution-service@f0a33fd3d8 + execution-service@62d2e3ab76.
      Execution subscribes only to the feature groups it needs; Evidence: both commits exist and are ancestors of `origin/live-defi-rollout`, with the source plan evidence from `bash scripts/quality-gates.sh --no-fix`. Source: `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`.
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-21 — execution-service@c6b8bd02ad. Every strategy-emitted instruction is persisted one-by-one through the existing manifest/shard pipeline; Evidence: bash scripts/quality-gates.sh --no-fix (8877 passed, 22 skipped, 1 xpassed; isolated quickmerge gate green).
      Queryable through the existing BigQuery external-table pattern; distinct from market-tick-data aggregation (W2/W3), a separate axis.

Full todo detail, commit SHAs, and evidence: `/plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`
— this section tracks landed/open status only and does not duplicate the plan's evidence trail.

- [x] [BACKEND] P0. Instruction action vocabulary past TRADE/QUOTE — SWAP, LEND, WITHDRAW, STAKE, UNSTAKE, BORROW,
      REPAY, TRANSFER, CANCEL, BRIDGE, and ATOMIC are now all wired on the external HTTP surface (the DeFi actions
      via a `defi_adapter=` injection seam, TRANSFER/CANCEL/BRIDGE via the transfer-wiring seam, ATOMIC via the
      existing multi-leg router), each producing a real settlement result or an honest structured rejection, never
      a silent drop or fabricated success. SHIPPED 2026-08-20/21. The underlying venue-side ATOMIC multi-leg
      execution engine (compensation semantics, partial-fill handling) is a separate, genuinely open follow-up —
      tracked in `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md`. Detail: the
      plan's "Instruction action vocabulary" section.
- [x] [BACKEND] P0. Kill-switch and flatten-position as instructions — SHIPPED 2026-08-21.
      `KILL_SWITCH`/`FLATTEN_POSITION` route through the existing kill-switch and
      `AccountInstructionOrchestrator.CLOSE_ALL` primitives, not a second authority path.
- [ ] [BACKEND] P0. **Three execution-service deployment topology, one schema, protocol per deployment**:
      internal (Pub/Sub), external-automated (registered/allow-listed clients, HTTP/WebSocket), manual (HTTP).
      Same `StrategyInstructionEnvelope` across all three. STILL OPEN — a verification pass now that the
      messaging-bridge and vocabulary prerequisites have landed; not started.
- [ ] [BACKEND] P0. **External hosting, two ways**: we run it for a registered client, or they run the same image
      themselves (Dockerized, config-driven). STILL OPEN, not started.
- [ ] [BACKEND] P1. **Broker and routing configuration via the existing `venue_constraints` field** — population
      and validation only, no new schema. STILL OPEN, not started.
- [ ] [BACKEND] P1. **Registered-client management for the external-automated deployment** — allow-list +
      onboarding. A related but DISTINCT mechanism shipped 2026-08-21 (`_enforce_client_org_binding` — a
      client_id-vs-org_id ownership binding, not an org allow-list) does not close this. STILL OPEN, not started.

Codex SSOTs: `/codex/02-data/live-data-persistence-and-event-log.md` (EventTransport facade),
`/codex/04-architecture/tier-and-import-architecture.md` (no service→service dependency).

---

---

## Issue-doc corpus, 2026-08-17/18 — folded in so nothing is tracked only in an issue doc

**38 issue docs** were filed in two days off other agents' findings, mapped to workstreams below so this epic is a
complete index of outstanding work — a finding tracked nowhere but its own issue doc is one nobody will schedule.

**Load-bearing for the artefacts — these change what we may claim:**

| Finding | Impact |
| --- | --- |
| `b21_distinct_values_noncanonical_live_2026_08_18` (P1) | **B21 measurably FAILS live**: 113 non-canonical entries across all 5 AGs (defi 38, sports 71, cefi 1, prediction 1, tradfi 2), most unaccounted for by the accepted-exceptions registry. **No artefact may claim "paths canonical".** |
| `cefi_instrument_type_casing_active_writer_regression_2026_08_17` (P1) | Casing residual **grew 13x, 2,982 -> 39,286 rows — an ACTIVE WRITER regression, not historical debt**, traced to MTDS `partitioned_writer.py` lowercasing leaking into the manifest row-key. Canonical quality is degrading in real time, so any canonical claim has a shelf life. |
| `manifest_hygiene_red_all_2026_08_17` (P1) | DIVERGENT_EMPTY across cefi/tradfi/prediction; POLYMARKET CQG rollup empty on 43% of days across all history; **prediction raw trades has an 8-day-and-counting capture outage**. Prediction coverage must not be quoted as steady-state. |
| `features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18` (P1) | Corporate actions sourced from a **fleet-wide BANNED vendor**. Blocks the corporate-actions path this epic already noted as post-MVP. |

**W2 — data pipeline integrity**: the four above, plus `manifest_hygiene_red_all_2026_08_18` ·
`empty_reprobe_disagreement_all_2026_08_17` (closed) + `..._2026_08_18` ·
`mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17` (closed) ·
`utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18` (**P0**, closed — a silent write failure, exactly
the class gate B9 exists to catch).

**W4 — observability, alerting, recovery**: `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18` (P1) ·
`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17` (P1) ·
`dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17` (P1) ·
`cefi_lighter_zksync_preempted_relaunch_blocked_tardis_cap_2026_08_17` (P2 — preemption relaunch blocked by the Tardis
1-VM cap: gate B12 and the spot-recovery gate interacting) ·
`escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18` (P2) ·
`main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18` (P1).

**W5 — venue readiness**: `defi_venue_e2e_batch1_deferred_followups_2026_08_17` (P2) ·
`mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17` (P3) ·
`defi_gas_net_cost_partial_wiring_gap_2026_08_17` (P1).

**W6 strategy / W11 order lifecycle**: `mev_engines_opportunity_detection_signals_unproduced_2026_08_18` (P1 — engines
exist, signals unproduced: the reachability class again) ·
`execution_order_tracker_missing_cancelled_amended_status_2026_08_17` (P2 — directly W11's "every incremental step
including updates and cancels").

**W16 triggers/latency**: `execution_delta_proxy_repricer_generalization_2026_08_18` (P1 — real, unwired
delta/gamma repricing infra; generalizes beyond MEV to market-making and arb-leg repricing).

**Features**: `features_service_calendar_domain_manifest_tracking_gap_2026_08_18` (P2) + the banned-vendor P1 above.

**Tooling / corpus hygiene (tracked, not epic-scope)**:
`git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17` (P1 — the contention class that fired
the self-inflicted-conflict guard repeatedly) · `unified_trading_ci_ff_pull_cron_branch_override_gap_2026_08_17` (P1) ·
`git_status_red_nudge_false_positive_wrong_branch_comparison_2026_08_17` (P3) ·
`ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17` (P2) ·
`ao_dashboard_activity_log_role_vocabulary_gap_2026_08_18` (P2) ·
`na_eligibility_*` (3) · `docs_reconcile_findings_2026_08_17` (P2) ·
`plan_reconciler_findings_{cefi,tradfi}_2026_08_18` · `sit_stamp_dispatch_503_false_positive_2026_08_17` (P3) ·
`promote_pr_non_supersession_after_greeks_service_fix_2026_08_18` (P3) ·
`tradfi_reconciliation_2026_08_17_findings_2026_08_17` (P2).

- [ ] [AGENT] P1. **Re-fold this index weekly.** It is a 2026-08-17/18 snapshot and will rot — the mechanism that keeps
      it true is a re-run, not an edit. When a doc closes, drop it from here rather than marking it closed twice.

## Definition of done for the epic

### The goalpost — the ONLY work that may still be pending (operator ruling 2026-08-19)

When this epic is done, everything is **complete in code**. The only things still outstanding may be:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK, not an acceptable end state. This is the
filter to audit against: the question is never "does the document match reality", it is "what is not yet
code-complete, and is it on this list".


- [ ] [BACKEND] P0. **Every venue with a code path has a derived batch / paper / live state**, with `unverified`
      surfaced honestly where a check does not exist.
- [ ] [BACKEND] P0. **Honest coverage measured on every axis and granularity**, each figure carrying denominator and
      date.
- [ ] [BACKEND] P0. **No orphans** — no shard stored that nothing consumes, no declared entity with no consumer, no
      venue with no archetype able to use it.
- [ ] [BACKEND] P0. **Strategy-service is fully scaffolded, fully configurable from the wizard, and reads only
      processed data.**
- [ ] [BACKEND] P0. **Execution carries full order lifecycle, state recovery, reconciliation and manual trade on every
      venue.**
- [ ] [DOC] P0. **The presentation artefacts quote the derived state**, with no figure that outruns its measurement.
- [ ] [AGENT] P1. **The corpus is reconciled** — nothing relevant left un-folded, nothing stale left believed.

## Progress Log

**2026-08-21 — W11 order-lifecycle / state-recovery: OMS-persistence design closed.**
`w_execution_orchestrator_oms_persistence_2026_08_20` closed all 10 design todos same-session — the write
contract, persistence backend (`PostgreSQLOrderPersistence`, a real but 100%-stub class), schema, and
hot-path latency tradeoff for making `ExecutionOrchestrator`'s live order-submission path durably persist
into an OMS are all decided (full spec: that plan's 2026-08-21 Progress Log entry). Follow-up implementation
plan authored: `/plans/archive/2026_08/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` (+ finalize). The
"Execution carries full order lifecycle, state recovery, reconciliation and manual trade on every venue"
checkbox above stays open — design is not implementation — but the design blocker `w_state_recovery_real_wiring
_2026_08_20`'s own Close-out section named (nothing in the live order-submission path durably persists order
state, so `OrderRecoveryEngine`'s `OrderBook` is structurally guaranteed empty at every restart) now has a
concrete, scoped implementation plan closing it, not an open design question.

**2026-08-22 — W11 order-lifecycle / state-recovery: implementation landed + finalize-reviewed.**
`w_execution_orchestrator_oms_persistence_impl_2026_08_21` landed (`execution-service@bc2edc16874a3b0828ef692682b69174ddcab4bf`,
ancestor of `origin/live-defi-rollout`) and its finalize independently re-verified live-in-code that `_run_live_async`
threads one shared `UnifiedOrderManager` into both `OrderRecoveryEngine`'s `OrderBook` and every venue's
`OrderAdapter` — `OrderBook` is no longer structurally guaranteed empty. This clears the `BLOCKED-OPERATOR` half of
`w_state_recovery_real_wiring_2026_08_20`'s "run real recovery" gate; `BLOCKED-CREDENTIALS` remains open pending
operator-provided venue credentials. The epic checkbox above stays open — real-recovery verification and the epic's
broader reconciliation/manual-trade criteria are still outstanding.

**2026-08-17 — authored.** Formalised from an operator brain-dump covering the full readiness surface, with a hard
target of 2026-08-25. Deliberately cross-product rather than per-asset-group: the existing `defi_master` and siblings
own their own rollouts, while this epic owns the invariants that apply across all of them. AO and CI/CD are excluded
except where AO pertains to orchestration, per operator direction — they are already carried by their own umbrellas.

Two framing decisions worth preserving. **First, the documentation states everything that must happen, not everything
achievable by the 25th** — scoping down is the operator's call taken against a complete picture, and a workstream that
slips should be a visible slip rather than an absent one. **Second, the presentation artefacts are inside this epic
rather than beside it**, because a client-facing readiness claim and an internal derived readiness state are the same
measurement; separating them is precisely how an artefact number comes to outrun the system it describes.

One measurement correction recorded at authoring time: an mtime-based sweep reports 781 of 804 active docs as modified
within 7 days, which is an artefact of pulls touching files rather than real recency. W19's audit must key off the
`created:` frontmatter field instead — chasing the 781 would waste a large fraction of the audit budget on docs that
have not changed.

**2026-08-17 — W7 extended, asset-group-agnostic ruling.** Interactive session established that position-risk /
margin-health centralization (the DeFi-only fix already tracked under W7) must be asset-group-agnostic across
DeFi, CeFi and TradFi, not DeFi-specific — same four-destination rule, applied to a concrete case. That
investigation also surfaced a previously-missed second centralized mechanism
(`margin_event_emitter.py`/`MarginEvent`, already live and cross-service) alongside the one the corpus already
tracked, added as a new P0 reconciliation todo. Full detail:
[position-risk-centralization](/codex/04-architecture/position-risk-centralization.md).
