---
doc_type: plan
title: Data pipeline completion — BATCH / PAPER / LIVE readiness gates, all shards, all asset groups
summary: >-
  The operator-owned data-pipeline deliverable for Friday 2026-08-21, with a Tuesday checkpoint. Every shard records a
  BATCH, PAPER and LIVE readiness stage across instruments-service through features-service, for every asset group,
  broken down by shard. Holds the three complete gate sets — BATCH (operator draft, extended), PAPER and LIVE (drafted
  here) — deliberately DISTINCT from trading/ephemeral deployment readiness gates, which cover strategy and execution
  and get their own treatment. Serves three purposes at once: what Elysium needs, what Nick AI needs, and a clean
  internal record of readiness everywhere so estimates stop being guesses.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, features]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    deployment-api,
  ]
scope: [admin, engineer]
tags: [data-pipeline, readiness-gates, honest-coverage, canonical, billing-waste, observability, deliverable]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-17
source: >-
  Operator direction 2026-08-17. Operator-set deliverable with a self-imposed Friday deadline; the BATCH gate set is
  the operator's own draft, extended here with gates traced to measured incidents. PAPER and LIVE drafted here for
  operator review.
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 10.0
estimate_calibrated_ai_days: 8.0
assigned_role: infra
effort: high
last_updated: "2026-08-17"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/orphan-object-detection.md,
  ]
---

# Data pipeline completion

> **Deadline: Friday 2026-08-21. Owner: Ikenna.** Parent epic:
> [`/plans/epics/system_readiness_master.md`](/plans/epics/system_readiness_master.md).
>
> **Checkpoint — EOD Tuesday 2026-08-18 — TWO dumps.** Recording the state is the Tuesday deliverable; *achieving* it
> is not.
>
> 1. **Readiness state dump** — every shard records a BATCH, PAPER and LIVE readiness stage across all services from
>    instruments-service through features-service, all asset groups, broken down by shard. Derived, with `unverified`
>    wherever no real check exists — a legitimate value that must be used, not worked around.
> 2. **Honest coverage dump** — how much data coverage exists per shard. **This is information we ALREADY HAVE**: a dump
>    of the manifest, not a measurement campaign.
>
> **Neither is blocked by the `instrument_type` axis.** That axis changes the GRANULARITY at which coverage can be
> expressed — from `(venue, data_type)` to the full 3-tuple — not whether today's coverage can be dumped. Conflating the
> two would defer a Tuesday deliverable behind a Friday dependency for no reason.
>
> **Both must be SKILLS, not one-off reports** — the coverage dump runs at today's grain now and RE-RUNS at 3-tuple once
> the axis lands. As a skill that upgrade is a re-run; as a hand-built report it is a rebuild, and the rebuild is where a
> stale figure survives into a client document.
>
> **Friday target**: all shards at **BATCH** readiness pending backfill completion.

## What this plan is, and what it deliberately is not

**Is**: the data-pipeline readiness gate set — instruments-service → MTDS → MDPS → features. Coverage, canonicalisation,
schemas, observability, cost and throughput.

**Is not**: trading/ephemeral deployment readiness. Strategy and execution gates are a distinct set with distinct
failure modes (order lifecycle, reconciliation, custody) and get their own treatment. **Machine learning also gets its
own treatment.** Keeping them separate matters because a shard can be fully BATCH-ready as data while no strategy can
consume it — conflating the two hides exactly that gap.

**Why one plan serves three purposes.** Elysium needs a defensible readiness claim; Nick AI needs honest coverage
percentages per shard; and we need a record precise enough to estimate from. These are the same measurement viewed
three ways — so the gate set is authored once and quoted three times, rather than re-derived per audience.

---

## Data pipeline readiness — BATCH

Operator draft, preserved. **Items marked `+ADDED` are proposed additions**, each traced to a measured incident rather
than a hypothesis — the operator asked specifically what past failures should become gates.

| # | Gate | Bar |
| --- | --- | --- |
| B1 | **Availability** | `>0` honest coverage (non-zero) reached for every shard dimension — instrument_type, data_type, venue, and chain where relevant for the asset group. Excluding `empty_confirmed`. |
| B2 | **Smoke test** | We can download the data. Minimum **1 hour of machine runtime**, so network transients, rate limits and time-emergent bottlenecks are actually encountered rather than missed by a 30-second pass. |
| B3 | **Observability and recovery** | Alerting covers transient and long-term failures, with automatic recovery, retries, escalation and preemption-based relaunch that **resumes where it died** rather than restarting. No zombies. No duplicate VMs for the same work. Shard registration hardened — even inside a bundle — so launching the same thing twice is *blocked*, not merely detected. |
| B4 | **Resource** | A record of the resources actually used to reach the current state, per shard. |
| B5 | **Performance** | Concrete throughput/performance figure for the download, and an ETA to completion for that shard from its current coverage state. |
| B6 | **Vertical scaling** | Resource requirements for a multi-shard bundled deployment (always grouped within one asset group) auto-built by aggregating shard-level resources, with real parallelisation and no wasted CPU or I/O. Combined throughput not materially below what the individual shard metrics predict. |
| B7 | **Daily T+1 backfill** | Running on schedule, writing to the same canonical target as batch, so honest coverage *stays* at 100% rather than decaying. |
| B8 | **Honest coverage 100%** | The terminal bar: full coverage over the declared expected set. |

### +ADDED — proposed BATCH gates, each from a real incident

| # | Gate | Bar | Why — the measured failure |
| --- | --- | --- | --- |
| B9 | **No silent zero-row success** `+ADDED` | Progress is measured as **count of TARGET artefacts created** — entity-scoped, keyed on `time_created` not `updated` — never as "activity". A run that exits 0 having written zero rows FAILS. | An entity-agnostic progress check passed for hours while the target wrote zero rows. Exit code 0 is a proxy, not the property. |
| B10 | **Non-retriable classification** `+ADDED` | Every `attempted_failed` shard carries a verdict: structurally non-retriable, or genuinely transient. Non-retriable shards are **excluded from future waves**. | Structurally non-retriable shards were silently re-attempted on every wave — pure billing waste, invisible because each attempt looked like normal activity. |
| B11 | **Rightsizing verdict** `+ADDED` | Any shard whose deployment runs >30 min carries a CPU + memory-growth rightsizing verdict, or a cited justification for its sizing. | The TradFi OHLCV backfill fleet averaged **6–7% CPU on a 16-vCPU machine** across 97% of fleet volume (measured 2026-08-10) — nobody owned "did this VM need what it was given". |
| B12 | **Per-source concurrency cap declared** `+ADDED` | Each source declares its max concurrent workers, derived from its real rate limits. Caps are declared, never discovered by storming the API. | Tardis has a hard cap of 1 concurrent VM across both clouds; exceeding it storms the vendor API. A cap learned by breaching it is not a cap. |
| B13 | **Single-walk discipline** `+ADDED` | The shard's coverage is answerable from the manifest without a new whole-corpus GCS walk. A new full walk is review-blocking. | Whole-corpus walks are the most expensive operation in the estate and were being re-improvised per audit. |
| B14 | **Shard-atom identity across surfaces** `+ADDED` | The atom string is **identical** across writer, manifest, data-status, gate and UI. | A shard that is one atom to the writer and another to the gate is unmeasurable — the two never reconcile, and each surface reports a different truth. |
| B15 | **Idempotent re-run / skip semantics** `+ADDED` | Without `--force`, a re-run skips what is genuinely captured and does **not** skip what is absent. Skip verdicts distinguish genuine (prod-captured) from ambiguous. | A skip that cannot tell "already have it" from "cannot see it" makes every subsequent coverage number unfalsifiable. |
| B16 | **Denominator declared** `+ADDED` | Every coverage percentage states its denominator, and the four capture states are reported separately: captured, expected-absent, expected-unattempted, not-expected. | `expected-absent` vs `expected-unattempted` is the difference between a limit and a schedule; collapsing them always flatters the reporter. Also: `not-expected` must be excluded from the denominator, or a complete dataset reads as broken. |
| B17 | **Cost recorded, not just resources** `+ADDED` | Actual spend to reach current state, per shard — so B5's ETA multiplies into a budget rather than a duration. | An ETA without a cost cannot be traded off against descoping. |
| B18 | **Canonical value-check, not just path shape** `+ADDED` | Canonicalisation verified via the UAC machine oracle **plus** separate checks on filename instrument_id and the `instrument_type`/`data_type`/`venue`/`chain` VALUES — or those are explicitly declared unchecked. | The oracle is path-structure-only and value-blind. "The oracle passed" has been read as "canonical" when the values were never examined. |
| B19 | **Consolidator freshness gating** `+ADDED` | A launcher whose manifest index is stale **exits** rather than proceeding. | Proceeding against a stale index writes into a lie, and every downstream number inherits it. |
| B20 | **Orthogonal shard vocabulary** `+ADDED` | Human sign-off that no two shard names describe the same thing. Near-duplicates are normalised, migrated and purged — in GCS *and* the manifest. | The operator's own bar: "no shard names that are not truly orthogonal and can be unified." Two names for one thing double-counts the denominator. |

| B21 | **Manifest canonical on the named surface** `+ADDED` | **Zero non-canonical entries in Distinct Values in the deployment UI**, per asset group. That surface is the acceptance check — not a grep and not a script's own opinion. If Distinct Values shows a non-canonical value, the gate fails. | Operator's bar. A canonicalisation claim verified only by the tool that did the canonicalising is self-certifying. |
| B22 | **Path ↔ manifest reconciled BOTH ways** `+ADDED` | Every GCS path follows the same structure as the code, **and** every path entry is recorded in the manifest in canonical format. Bidirectional: manifest→path (does every entry have an object?) *and* path→manifest (does every object have an entry?). Manifest-driven, no new whole-corpus walk (B13). | The path→manifest direction is the one that gets skipped, and it is the one that matters: an object in GCS with no manifest row is invisible to every coverage number we quote. SSOT: `/codex/02-data/orphan-object-detection.md`. |
| B23 | **Schemas conformant, LOCKED and VERSIONED** `+ADDED` | Every GCS object conforms to its declared schema; schemas are locked and versioned, so a schema change is a deliberate versioned act rather than a drift downstream readers discover. | The 2026-04-14 incident: 85 `entity=fixtures_schedule` shards silently carried an instrument-catalogue shape instead of fixtures data, undetected until a downstream column projection failed. Conformance catches a WRONG-SHAPE write, which no coverage number ever will. |

> **MEASURED 2026-08-17 — B22 currently FAILS, with a number.** A bounded 4,000-blob sample of the cefi
> instruments-store: **1,000 non-canonical objects** (no `pipeline_mode=`/`asset_group=` segment, and a *different
> size* from their canonical twin — different content, not duplicates) and **270 `.bak` files in prod**. Roughly a
> third of sampled objects. Sports additionally uses a different path grammar (`day=/league=/venue=`), so "follows the
> same structure as the code" is not yet true across asset groups. Full per-AG re-measure tracked in
> [`/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md`](/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md).
>
> **B23 is currently UNVERIFIED, not satisfied.** The 51-column instruments schema exists and is populated, but whether
> it is *locked and versioned* has not been established. A schema existing is not a schema being locked.

- [x] ✅ [DATA] P0. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 1 (na-eligibility-audit 2026-08-17). Verify B21 — Distinct Values in the deployment UI shows zero non-canonical values, per AG.
- [ ] [OPERATOR] P0. **Sign off B20's shard-name orthogonality.** Human judgment, explicitly not delegable to a checker.
- [x] ✅ [DATA] P0. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 2 (na-eligibility-audit 2026-08-17). Verify B22 in BOTH directions, per AG, off the manifest.
- [x] ✅ [DATA] P0. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 3 (na-eligibility-audit 2026-08-17). Establish whether B23's schemas are locked and versioned, and if not, what locking them requires — the gate with the least existing evidence.

> **Doc-hygiene fix (na-eligibility-audit 2026-08-17)**: this section previously contained an accidentally
> near-verbatim duplicated block immediately below this point (the B21-B23 table + MEASURED blockquote appeared a
> second time, differing only in cosmetic rewording and straight-vs-Unicode arrow glyphs) — table+blockquote
> removed here; no content was lost, both copies said the same thing. The 4 duplicate checkboxes are individually
> marked CANCELLED below (not silently deleted) so the doc's total todo count stays conserved.

- **[DATA] P0. CANCELLED — SUPERSEDED 2026-08-17 (na-eligibility-audit): exact duplicate of the B21 checkbox above,
  accidental content-duplication artifact, not a second item.** Verify B21 — Distinct Values in the deployment UI
  shows zero non-canonical values, per AG.
- **[OPERATOR] P0. CANCELLED — SUPERSEDED 2026-08-17 (na-eligibility-audit): exact duplicate of the B20 checkbox
  above, accidental content-duplication artifact, not a second item.** Sign off B20's shard-name orthogonality.
- **[DATA] P0. CANCELLED — SUPERSEDED 2026-08-17 (na-eligibility-audit): exact duplicate of the B22 checkbox above,
  accidental content-duplication artifact, not a second item.** Verify B22 in BOTH directions, per AG, off the
  manifest.
- **[DATA] P0. CANCELLED — SUPERSEDED 2026-08-17 (na-eligibility-audit): exact duplicate of the B23 checkbox above,
  accidental content-duplication artifact, not a second item.** Establish whether B23's schemas are locked and
  versioned — the gate with the least evidence today.

| B24 | **Minimum history declared per shard, and TRANSITIVE** `+ADDED` | Every shard declares the minimum history it needs to produce anything at all — and the requirement for a consumer is the **transitive closure** through the chain, not its own hop. | You cannot build a 1-year candle without a year of tick history, and you cannot compute a 10-period moving average over 1-year candles without **ten years** of candles beneath it. The requirement COMPOUNDS per hop; declaring it only at the last hop understates it by the depth of the chain. |
| B25 | **Registration FAILS when declared config exceeds available history** `+ADDED` | A strategy/feature config asking for more lookback than measured coverage provides is rejected **at registration**, not at runtime. Declared lookback is checked against real honest coverage for that exact shard. | Otherwise we produce config that says what we want without ever checking the data exists to fulfil it — and the failure surfaces as quietly wrong numbers rather than an error. Composes with P12 (preflight registration) and B16 (denominator). |
| B26 | **Three-stage benchmark per shard** `+ADDED` | Measure and record the pipeline as **three separate stages**, never one aggregate: **(1) fetch** — vendor/venue download, as throughput; **(2) process** — transform/normalise, as **latency**; **(3) write** — save to GCS, as **IO throughput**. One figure per stage, per shard, **and per MODE — batch, paper and live** (operator, 2026-08-17): the same three stages carry different profiles per mode, so a batch figure says nothing about live headroom. | An aggregate end-to-end number cannot answer the question we need it for. If most wall-clock is vendor-side fetch, changing compute provider or machine size changes nothing — and B11's measured 6–7% CPU on a 16-vCPU TradFi fleet is exactly what a fetch-bound shard looks like. The split is what makes B5's ETA and B11's rightsizing verdict *explainable* rather than merely observed. |

### The three-stage benchmark — what it is FOR

**It is a portability baseline, not a scorecard.** The point is to be able to answer "how much worse would this be
somewhere else?" with a measurement instead of a guess.

- **Portable by construction.** The same harness must run **off-Google** — on a laptop, or on another provider — or the
  comparison is inference rather than measurement. A benchmark that only exists inside one provider's environment
  cannot tell you what leaving it costs.
- **The Google figure is the REFERENCE ETA, explicitly not a bar to beat.** Per the operator: we do not have to beat
  it; we need to know how far off we are. That framing matters, because a target invites tuning the benchmark, whereas
  a reference invites measuring honestly.
- **Why the stage split is the whole value.** Each stage has a different bottleneck and a different remedy — fetch is
  bound by vendor rate limits and network, process by CPU, write by IO and object count. A single end-to-end number
  averages all three and hides which one to act on. It also silently misattributes: a slow shard reads as "needs a
  bigger machine" when it is actually waiting on a vendor.
- **Per MODE, not just per shard.** Batch backfill is bulk and throughput-bound; live is streaming and latency-bound;
  paper sits between and must match batch (the ε=0 property). The same three stages therefore have three different
  profiles, and the interesting numbers are different ones: batch cares about fetch+write throughput, live cares about
  process latency and whether write keeps up in real time. Quoting a batch benchmark as if it bounded live capacity is
  the specific error this per-mode split prevents.
- **Composes with B6** (vertical scaling): when bundled throughput lags what the individual shard metrics predicted, the
  three-stage split identifies *which* stage failed to parallelise — otherwise the shortfall is unattributable.
- **Composes with B17** (cost): cost per stage, so an expensive stage is visible rather than averaged into a
  per-shard total.

- [x] ✅ [BACKEND] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 4 (na-eligibility-audit 2026-08-17). Instrument the three stages per shard and record fetch throughput, process latency, and GCS
      write throughput separately.
- [x] ✅ [BACKEND] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 5 (na-eligibility-audit 2026-08-17). Make the harness portable — same benchmark runnable on a laptop and on a non-Google provider,
      so the figures are directly comparable rather than adjusted.
- [x] ✅ [BACKEND] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 6 (na-eligibility-audit 2026-08-17). Publish the per-shard reference ETA derived from the Google figures, labelled REFERENCE and not
      a target, alongside the per-stage breakdown that explains it.

### History sufficiency — why it is a chain problem, not a per-shard number

The dependency chain is `tick -> candle -> feature -> feature group -> archetype`, and **each hop multiplies rather than
adds**. An archetype's real requirement is resolved by walking the whole chain — venue, feature group, and the
individual feature within that group — and taking the deepest transitive need. A feature registry that records only
"this feature needs 10 periods" is not enough; it must resolve to "therefore this shard needs N years of ticks at that
granularity", which is what can then be checked against coverage.

**This is what makes B25 enforceable.** Without the transitive resolution, a registration check can only compare a
declared lookback against the immediately-upstream shard and will pass configs that are unsatisfiable further down.

- [ ] [BACKEND] P0. **Encode minimum-history per shard and resolve the transitive closure per archetype**, across MDPS
      and the feature registry — per venue, per feature group, and per feature within a group.
- [ ] [BACKEND] P0. **Wire B25 as a registration-time gate** and prove it rejects a deliberately over-reaching config.

---

## Data pipeline readiness — PAPER

**Drafted for operator review.** The organising idea: PAPER is where the pipeline stops being a historical archive and
starts being a live feed that must agree with that archive. Almost every gate below is a form of *batch and live must
not diverge*.

| # | Gate | Bar |
| --- | --- | --- |
| P1 | **Live adapter parity** | A live adapter exists for **every** batch adapter — never the reverse. This direction is already a cascade invariant; PAPER makes it a gate. |
| P2 | **Live capture running, with a freshness SLA** | Live capture is running for the shard and meets a declared freshness SLA. "Running" without a staleness bound is not a state. |
| P3 | **Schema parity, batch ↔ live** | Identical schemas. No live-only data types, no live-only columns. Live is the same code path as batch. |
| P4 | **Determinism proof (ε=0)** | For a window W, `paper(W)` equals `batch-rerun(W)` trade-for-trade. Not argued — proven, with a negative control that shows the test can fail. |
| P5 | **Gap backfill closes the loop** | If live drops, the T+1 batch pass fills the hole and honest coverage returns to 100%. A live gap is a scheduling event, not permanent data loss. |
| P6 | **Stream continuity detection** | Sequence/ordering continuity checked; duplicates and gaps detected rather than silently absorbed. |
| P7 | **Transport is the event-log spine** | Published via the UTL `EventTransport` facade — never a bespoke transport. This is what makes paper and colocated behave identically. |
| P8 | **Latency instrumentation** | Time-data-received and time-data-sent recorded on every artefact, so latency and tracing are measurable rather than inferred. |
| P9 | **Staleness SLA per input** | Each input declares how long is a reasonable wait before it is considered stale, and what happens when it is. |
| P10 | **Testnet position recorded per venue** | Does this venue have a testnet, how does it behave, or must it be simulated through our own matching engine as close as possible to both batch and live? Recorded per venue — written down, never assumed. |
| P11 | **Read credentials present** | Live market-data read credentials exist. Note this is a *read* gate: PAPER needs real live data, not venue execution accounts. |
| P12 | **Preflight input registration** | A shard's consumers fail at registration if a required input is absent — not at runtime, mid-run. |

| P13 | **Gap-recovery policy declared per (SOURCE x STRATEGY)** | Two independent axes, and the policy is their cross product: (a) **can this source replay intraday at all** — some vendors permit it, some do not (Tardis on an academic subscription cannot replay intraday); (b) **does this strategy tolerate a gap** — some are indifferent, some are not. Declared per pair, never generalised. |

> **Why this cannot be one global policy.** Neither axis alone determines the answer. A gap-tolerant strategy on a
> replayable source needs no action; a gap-sensitive strategy on a non-replayable source has no recovery path at all and
> must halt rather than silently continue on incomplete data. The other two combinations sit between. A single
> "recover intraday" policy is unimplementable across that matrix, which is why it is declared per pair — and why the
> non-replayable/gap-sensitive cell must be identified in advance rather than discovered during an outage.

---

## Data pipeline readiness — LIVE

**Drafted for operator review.** PAPER plus everything that only matters when the feed is load-bearing and someone is
paged at 3am. **Note the boundary**: execution credentials and funded accounts are *trading* readiness, not data
pipeline readiness — they are deliberately absent here.

| # | Gate | Bar |
| --- | --- | --- |
| L1 | **All PAPER gates hold** | Non-negotiable precondition. |
| L2 | **SLOs declared and measured** | Freshness, completeness and latency SLOs per shard, with actual attainment measured — not aspirational targets. |
| L3 | **Alerting pages a human, with a defined ladder** | Failures escalate through the retry → restart → drain → hold-dependants → halt ladder, with scope declared per step. Automatic lifecycle events never page; genuine failures always do. |
| L4 | **Auto-recovery matrix respected** | Protective arming is autonomous; resume is only autonomous within the recovery matrix. Anything classed manual stays human-only. |
| L5 | **In-line data-quality rejection** | Bad rows are rejected or quarantined at write time rather than written and cleaned later. No silent placeholders, ever. |
| L6 | **Backpressure handled** | Defined behaviour when consumers fall behind — shed, buffer or halt, chosen explicitly rather than discovered under load. |
| L7 | **Consolidator availability** | The manifest consolidator is not a single point of failure for the live path. |
| L8 | **Runbook with owner, cadence, verifier** | Declared and current. A runbook without a verifier and a last-executed date is a document, not a control. |
| L9 | **DR and failover exercised** | Region/cloud failover for the capture path, tested — not merely designed. |
| L10 | **Retention and lifecycle policy** | Declared per data type, and actually enforced, so live volume does not silently become an unbounded cost. |
| L11 | **Production-scale cost model** | Cost at live volume, with headroom stated — the point where B17's per-shard spend becomes a run rate. |
| L12 | **Access control and audit** | Who can read each shard, recorded and enforced; the data record itself immutable with audited status changes. |
| L14 | **Intraday recovery EXERCISED, not designed** | For every (source x strategy) pair whose P13 policy claims intraday recovery, that recovery has actually been run and verified — and for pairs with no recovery path, the halt behaviour has been exercised. History matters across every service, so a recovery that has never been executed is a plan, not a control. |
| L13 | **Reconciliation against venue-reported totals** | Where the venue publishes its own totals, our captured totals reconcile to them within a declared tolerance. This is the only gate that catches "we captured something, consistently, and it was wrong." |

---

## Tie-in to existing plans — link, do not duplicate

Each gate above is owned by an existing plan wherever one exists. This plan is the **gate register**; the work lives
where it already lives.

- [x] ✅ [DOC] P0. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 7 (na-eligibility-audit 2026-08-17). Cross-link every gate to its owning plan/issue doc
      so the register resolves to real tracked work:
      canonicalisation and orthogonality → [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
      (steps 18–19); smoke-test bar → [`/plans/active/venue_smoke_test_bar_2026_08_16.md`](/plans/active/venue_smoke_test_bar_2026_08_16.md);
      per-venue e2e legs → [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md);
      coverage figures for disclosure → [`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md).
      Where a gate has **no** owning plan, that absence is the finding — record it rather than silently absorbing it.
- [ ] [OPERATOR] P0. **Review and ratify the PAPER and LIVE gate sets** above, and the 12 `+ADDED` BATCH gates. They
      are drafted, not ruled.
- [x] ✅ [DATA] P0. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 8 (na-eligibility-audit 2026-08-17). Tuesday checkpoint: record BATCH/PAPER/LIVE stage per shard across IS → features, all asset
      groups. Recording, not achieving. `unverified` is a legitimate value and must be used where no check exists.
- [x] ✅ [DATA] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 9 (na-eligibility-audit 2026-08-17). Friday target: all shards at BATCH pending backfill completion, with the residual explicitly
      being B8 (honest coverage 100%) and nothing else.
- [x] ✅ [SKILL] P1. Extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 10 (na-eligibility-audit 2026-08-17). Build the gate-evaluation skill so this register is re-runnable rather than a point-in-time
      snapshot — the same shape as the readiness state dump in the parent epic's W1/W20.

## Open question for the operator

The BATCH draft's final line was truncated mid-sentence — *"All of the data pipeline readiness batch criteria are met
except for f…"*. Read as **"except for full honest coverage (B8), pending backfill completion"**, which is consistent
with the Friday target above. Confirm or correct; it is the definition of the Friday deliverable, so it should not rest
on my inference.

## Tuesday dumps — the two skills

- [x] ✅ [SKILL] P0. Shipped — `unified-trading-pm@5b3dbf99bd`
      (`cursor-configs/skills/readiness-state-dump/`). **Readiness state-dump skill** — derived per (venue x mode)
      across IS -> MTDS -> MDPS -> features -> strategy -> execution, printing `unverified` where a check does not
      exist. Strategy leg is a real AND of two checks: strategy-service's own `position_read_mode_availability`
      (mode-aware position adapter) and the shipped contract-step-17 `satisfying_archetypes` (archetype
      registration) — both, not either. Shares `shard_universe.py` with the honest-coverage-dump skill below.
      Verified live 2026-08-17 against production data (288 venues x 3 modes, ~20s) — e.g. OKX-FUTURES/BATCH
      correctly derives `strategy=not_ready` from a `ready` archetype half + a `none` position-adapter half, proving
      the AND-logic. Tuesday deliverable 1. Same artefact the parent epic's W1/W20 name, and the one a handover
      reader runs for themselves rather than trusting a table someone typed.
- [x] ✅ [SKILL] P0. Shipped — `unified-trading-pm@5b3dbf99bd`
      (`cursor-configs/skills/honest-coverage-dump/`). **Honest-coverage dump skill** — per-shard coverage read
      straight from the already-computed `coverage.json` (reuses instruments-service's `measure_honest_coverage.py`
      output verbatim, never recomputes a capture_status), four capture states reported separately (B16) plus a
      "not-expected" section for Layer-1 stray/missing tuples, denominator stated on every percentage. Grain
      auto-detected from the payload every run (never hardcoded) — verified live 2026-08-17 the payload already
      carries populated `by_venue_instrument_type_data_type` (3,960 shards), so this dump already reads 3-tuple
      grain from the manifest side; re-run after the `VenueCapabilityRecord` axis lands on the declared-capability
      side to diff against today's output, no code change either way. Tuesday deliverable 2.
- [ ] [DATA] P1. **Re-run both dumps after the axis lands and diff against the Tuesday output.** The diff is the
      evidence that the granularity upgrade changed what we can say, and it is where a previously-hidden gap surfaces.

## Progress Log

**2026-08-17 — authored.** Gate register created from the operator's BATCH draft, extended with 12 `+ADDED` gates and
complete PAPER and LIVE sets drafted for review. Every addition is traced to a specific measured incident rather than
offered as good practice — the operator asked what past failures should become gates, and an untraceable gate is one
nobody will defend when it blocks a ship.

Three of the additions exist purely to stop money leaking (B10 non-retriable classification, B11 rightsizing, B12
per-source concurrency caps) and one to stop a false pass (B9 no-silent-zero-row) — that last one is the highest-value
addition, because a smoke test that exits 0 having written nothing satisfies B2 as originally worded.

Deliberately kept OUT: strategy, execution and ML readiness. They are separate gate sets with different failure modes,
and folding them in here would let a data-complete shard read as trading-ready.

**na-eligibility-audit 2026-08-17** [body-hash:c833814dff07254d]: RECLASSIFY (per-todo split) -- of 18 grep-matched checkboxes
(14 semantically distinct after collapsing an accidental duplicate block, see the doc-hygiene fix above), 10 bounded
items extracted to `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` items 1-10 (B21/B22/B23 verify,
3-stage benchmark instrumentation + portability + reference ETA, gate->plan cross-link, Tuesday/Friday checkpoint
recording, gate-eval skill build). Doc stays `assigned_vm: NA` for its remaining 4 items: B20 shard-name-orthogonality
sign-off `[OPERATOR]`, PAPER/LIVE+12-batch gate ratification `[OPERATOR]`, and the minimum-history/transitive-closure
resolver design work (line 213 + its dependent at 215 — cross-service, no cited existing pattern, matches the
"multi-file rewrite, not bounded" bar even though phrased as one todo). Conflict-check clear. Cross-cutting tranche
audit.
**context-scout 2026-08-17**: refreshed context_scope (6 entries) -- swapped `spot-vms-for-backfill.md` for
`orphan-object-detection.md`, which the doc's own B22 gate text cites as "SSOT:" twice but which was missing from the
original list; the other 5 entries (VM-launcher, VM-preemption-billing-waste, four-surface-reconciliation,
honest-coverage, availability-manifest) remain accurate for this gate register's broad scope. No source path added --
this plan is explicitly a gate register that links to owning plans rather than implementing directly ("this plan is
the gate register; the work lives where it already lives").
