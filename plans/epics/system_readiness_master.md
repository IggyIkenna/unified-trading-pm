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
  - /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md
  - /plans/active/venue_e2e_wiring_2026_08_16.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - /plans/active/registry_ssot_hardening_2026_08_16.md
  - /plans/active/lazy_scoped_loading_refactor_2026_08_16.md
  - /plans/active/strategy_service_centralization_fixes_2026_08_16.md
  - /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md
  - /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md
  - /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md
  - /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md
last_updated: "2026-08-17"
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
| strategy-service | Is there a position adapter **for this venue, in this mode**, and **at least one archetype registration** for this venue in this mode? |
| execution-service | Is there an adaptor handling every action the eligible archetypes emit, plus transfers? |

**Derived means derived.** Per the 2026-08-16 ruling: a step with no real machine check reports `unverified` — never a
silent pass. A readiness table that cannot say "I don't know" is not telling anyone anything, and every percentage in
this epic carries its denominator and measurement date.

## Cross-cutting invariants — true in every workstream below

- **strategy-service reads ONLY processed data** — MDPS and features, never MTDS directly. Operator hard rule. If a
  strategy appears to need raw ticks, the answer is a feature or a derived candle, not an import.
- **Execution fails closed on granularity.** A venue whose data cannot support a matching class is REFUSED, never
  matched as though tick data existed.
- **Everything declared lives in UAC** as far as possible — capabilities, registries, eligibility, weightings. SSOT in
  a contract, never inferred at runtime.
- **Credentials gate RUNNING, never BUILDING.** Exhausting the free path is a credential ask, not a descope.
- **Canonical paths and naming for every artefact**, including everything strategy-service emits.
- **A proxy is not the property** — a row count, an exit code, a green test, "the connector exists" are all proxies.

---

## W1 — Readiness derivation and the state dump

The spine. Everything else feeds it.

- [ ] [BACKEND] P0. **Auto-derive readiness per (venue × mode) across all six services** per the table above. Not a
      per-AG rollup — per venue, because readiness is uneven within an asset group and that unevenness is the signal.
- [ ] [BACKEND] P0. **Strategy leg, stated precisely**: a position adapter must exist for this venue in this mode, AND
      at least one strategy archetype must be registered for this venue in this mode. Both, not either.
- [ ] [BACKEND] P0. **Readiness applies to archetypes too**, not only venues — an archetype has its own batch / paper /
      live state, and a venue-archetype pair has one as well.
- [ ] [SKILL] P0. **Build a readiness state-dump skill** — one invocation prints the current derived state across every
      venue, archetype, and mode, with `unverified` where checks do not exist. This is the artefact the presentation
      docs quote and the handover reader runs themselves.
- [ ] [SKILL] P1. **Build a strategy-capability audit skill** — what can each archetype actually trade, given real
      coverage and real venue capability.

## W2 — Data pipeline integrity

- [ ] [BACKEND] P0. **Manifest canonicalisation of every entry**, and **skip logic when `--force` is not used** — a
      re-run must not silently re-fetch what is already captured, and must not silently skip what is absent.
- [ ] [BACKEND] P0. **Manifest consolidators must be running, or VMs exit** — a launcher that proceeds against a stale
      index writes into a lie. Gate on index freshness and fail loudly rather than degrade.
- [ ] [BACKEND] P0. **Every venue's shards (instrument_type × chain × data_type) must be consumed by at least one of
      MDPS or features.** If nothing consumes it, storing it has no purpose — the shard is either a missing consumer or
      a data type that should not exist. Orphan output is a finding, never a footnote.
- [ ] [BACKEND] P1. **Cheap and safe coverage increase** — the download path must be both. Spot where possible, resume
      from measured progress, never replay from `START_DATE`, and never let a cost optimisation weaken a correctness
      check.

## W3 — Granularity as a first-class dimension

- [ ] [BACKEND] P0. **Model coverage per (venue × instrument_type × data_type × granularity)** — candles versus tick
      entering MTDS are different coverage questions, and coverage may be **better at one granularity and worse at
      another** for the same venue and data type. A single number across granularities hides exactly the fact a
      strategy needs.
- [ ] [BACKEND] P0. **Land the instrument_type axis on `VenueCapabilityRecord`** — currently absent, which is why the
      denominator is `(venue, data_type)` 2-tuples while numerators reach 3-tuples. Operator ruling 2026-08-17: land
      the axis first, then measure once at full granularity. **Blocks every final coverage percentage.**
- [ ] [BACKEND] P1. **Declare exceptions at the granularity they occur** — venue / instrument_type / data_type, with
      the exception stated rather than implied by absence.

## W4 — Observability, alerting and auto-recovery

- [ ] [BACKEND] P0. **Data-pipeline alerts for deployment health across VMs and Cloud Run**, with auto-escalation and
      auto-reconciliation. Standing conditions dedup by state transition; automatic lifecycle events never page.
- [ ] [BACKEND] P0. **Data-status honest-coverage rollup AND drilldown for instruments-service, MTDS, MDPS and
      features** — the rollup is the headline, the drilldown is what makes it believable.
- [ ] [BACKEND] P0. **Spot preemption auto-recovery resumes at the right place** — from measured progress, never a
      replay. A recovery that restarts from the beginning is a cost bug wearing a correctness mask.
- [ ] [BACKEND] P0. **No duplicate VMs running.** Detect and prevent, do not merely alert.
- [ ] [BACKEND] P1. **Canonical GCS paths for everything, and clean up backup / stale / old paths** — deletes stay
      proof-gated and prod-bucket deletes remain human-only unless reversibility-qualified.
- [ ] [BACKEND] P1. **DR procedures, automation and cost optimisation** documented top-down across the data pipeline
      and deployment surface.

## W5 — Venue registry completeness

The registry must answer commercial and operational questions, not just "does this venue exist".

- [ ] [BACKEND] P0. **Collateral that can actually be used**, per venue.
- [ ] [BACKEND] P0. **Cross-margin logic where it exists**, declared rather than discovered.
- [ ] [BACKEND] P0. **Transfer capability per venue as explicit eligibility flags**: Copper-eligible, Ceffu-eligible,
      manual-transfer-eligible, automated prime-broker-eligible (per prime broker), IBKR / Alpaca eligible.
- [ ] [BACKEND] P0. **Manual trade capability for EVERY venue** — no exceptions. This is the disaster path.
- [ ] [BACKEND] P1. **All of the above in UAC**, as declarations — not inferred at runtime.

## W6 — Strategy archetype scaffolding, config and the wizard

- [ ] [BACKEND] P0. **Scaffold ALL strategy archetypes, not just the MVP ones.** The MVP set must be understood
      deeply, but the scaffolding of every archetype is what prevents a heavy refactor each time another comes online.
      The structure is the deliverable here, not the alpha.
- [ ] [BACKEND] P0. **Every archetype / family / slot fully configurable, with all config in `config*.py` in the same
      place**, hot-reloadable **including credentials**.
- [ ] [BACKEND] P0. **Configuration must be fully derivable from the strategy wizard** — the wizard is not a
      convenience layer, it is the sanctioned way config comes into being, and an agent must be able to drive it.
- [ ] [BACKEND] P0. **Complete the strategy wizard.** Every stage, constrained by the layer beneath it, emitting config
      valid by construction.
- [ ] [BACKEND] P0. **Strategy logic follows codex** — non-negotiable, and reviewable.

## W7 — Centralisation and anti-drift

- [ ] [BACKEND] P0. **Every strategy-agnostic module and function call lives centrally**, so multiple archetypes call
      one implementation instead of reimplementing it. Reimplementation is drift with a delay fuse.
- [ ] [BACKEND] P0. **Reference / registry / config data must never live inside a single strategy's code path** — the
      four-destination rule (UAC / service config via the reloader / UTL / a centralised domain module) decides where
      it goes. Tracked in `/plans/active/strategy_service_centralization_fixes_2026_08_16.md`.

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
- [ ] [BACKEND] P0. **Manual trades bookable as seen-by-the-system or not-seen**, for disaster cases: we know we hold a
      position, reconciliation has not caught up, and it must not delete that position. Reconciliation pauses BEFORE
      manual entry; persistent-delta (virtual) entries are excluded from the reconciliation delta.

## W13 — PnL attribution

- [ ] [BACKEND] P0. **Attribute PnL across every risk metric and exposure-normalisation metric, in the same dimensions
      and buckets.** If exposure can be sliced a certain way, PnL must be attributable the same way — otherwise the two
      cannot be reconciled against each other.

## W14 — Exchange contract fidelity

- [ ] [BACKEND] P0. **Every venue error code understood across every consumer** — MTDS, instruments-service, execution
      adaptors, and strategy-service balance queries. Every request and response schema, code and format.
- [ ] [BACKEND] P0. **Pin the exchange version tested**, so a venue-side version change triggers a **cassette re-run to
      detect drift** — and only then, not on every build.
- [ ] [OPERATOR] P0. **Test accounts with credentials for each venue** — a prerequisite for the above, and an operator
      action rather than an engineering one.

## W15 — Security

- [ ] [BACKEND] P0. **Security audit of every venue adaptor for vulnerabilities, especially DeFi.** On-chain write
      paths carry irreversible consequences; this is not a documentation exercise.

## W16 — Triggers, latency and preflight

- [ ] [BACKEND] P0. **Each strategy's triggers explicitly understood** — what it grabs and when: time-based,
      event-based. The normal shape is Pub/Sub broadcasting events, the strategy subscribing, then reading the data off
      the stream.
- [ ] [BACKEND] P0. **Every artefact records time-data-received and time-data-sent** for latency analysis and tracing.
- [ ] [BACKEND] P0. **Preflight registration checks fail if required data is absent** — at registration, not at
      runtime. Discovering a missing input mid-run is the expensive way to learn it.
- [ ] [BACKEND] P0. **An SLA per input for how long is a reasonable wait before data is considered stale.**

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
documentation. 23 skills exist today; these extend the pattern.

- [ ] [SKILL] P0. **Readiness state dump** (see W1) — venue × archetype × mode, derived.
- [ ] [SKILL] P0. **Strategy capability audit** — what each archetype can actually trade given real coverage.
- [ ] [SKILL] P1. **Venue registry completeness check** — collateral, cross-margin, transfer eligibility, manual-trade
      capability, per venue.
- [ ] [SKILL] P1. **Shard utilisation / orphan sweep** — every shard consumed by MDPS or features; every declared
      data_type, instrument_type, venue and chain consumed somewhere.
- [ ] [SKILL] P1. **Exchange contract drift check** — cassette re-run gated on venue version change.
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

---

## Definition of done for the epic

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
