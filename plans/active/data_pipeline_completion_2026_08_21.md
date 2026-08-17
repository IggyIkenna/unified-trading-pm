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
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
---

# Data pipeline completion

> **Deadline: Friday 2026-08-21. Owner: Ikenna.** Parent epic:
> [`/plans/epics/system_readiness_master.md`](/plans/epics/system_readiness_master.md).
>
> **Checkpoint — EOD Tuesday 2026-08-18**: every shard records a BATCH, PAPER and LIVE readiness stage across all
> services from instruments-service through features-service, across all asset groups, broken down by shard. Recording
> the state is the Tuesday deliverable; *achieving* it is not.
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
| L13 | **Reconciliation against venue-reported totals** | Where the venue publishes its own totals, our captured totals reconcile to them within a declared tolerance. This is the only gate that catches "we captured something, consistently, and it was wrong." |

---

## Tie-in to existing plans — link, do not duplicate

Each gate above is owned by an existing plan wherever one exists. This plan is the **gate register**; the work lives
where it already lives.

- [ ] [DOC] P0. **Cross-link every gate to its owning plan/issue doc** so the register resolves to real tracked work:
      canonicalisation and orthogonality → [`/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`](/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md)
      (steps 18–19); smoke-test bar → [`/plans/active/venue_smoke_test_bar_2026_08_16.md`](/plans/active/venue_smoke_test_bar_2026_08_16.md);
      per-venue e2e legs → [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md);
      coverage figures for disclosure → [`/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md`](/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md).
      Where a gate has **no** owning plan, that absence is the finding — record it rather than silently absorbing it.
- [ ] [OPERATOR] P0. **Review and ratify the PAPER and LIVE gate sets** above, and the 12 `+ADDED` BATCH gates. They
      are drafted, not ruled.
- [ ] [DATA] P0. **Tuesday checkpoint**: record BATCH/PAPER/LIVE stage per shard across IS → features, all asset
      groups. Recording, not achieving. `unverified` is a legitimate value and must be used where no check exists.
- [ ] [DATA] P1. **Friday target**: all shards at BATCH pending backfill completion, with the residual explicitly
      being B8 (honest coverage 100%) and nothing else.
- [ ] [SKILL] P1. **Build the gate-evaluation skill** so this register is re-runnable rather than a point-in-time
      snapshot — the same shape as the readiness state dump in the parent epic's W1/W20.

## Open question for the operator

The BATCH draft's final line was truncated mid-sentence — *"All of the data pipeline readiness batch criteria are met
except for f…"*. Read as **"except for full honest coverage (B8), pending backfill completion"**, which is consistent
with the Friday target above. Confirm or correct; it is the definition of the Friday deliverable, so it should not rest
on my inference.

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
