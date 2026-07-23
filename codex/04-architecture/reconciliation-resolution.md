---
doc_type: codex-ssot
title: Reconciliation Resolution Architecture
summary:
  The batch↔live↔paper reconciliation contract + operator resolution workflow — what gets compared (positions baseline,
  live vs simulated fills), the comparison keys, the 6-stage recon DAG (stage0 config/manifest/data-pipeline → stage1 ML
  → stage2 strategy → stage3 execution + 3b paper-live + 3c batch-paper), alpha decomposition (strategy vs execution vs
  data-pipeline vs ML), per-stage/per-pair tolerance bands, and the ACCEPT/REJECT/INVESTIGATE + book- correction UI
  flow. Per-archetype bands remain open (pvl-p21a).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [reconciliation, batch-live, execution, strategy, ui, data-correctness]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/04-architecture/reconciliation-age-tracking.md,
    /codex/04-architecture/separation-of-concerns.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    batch-live reconciliation resolution workflow (accept/reject/investigate + book-correction),
    batch-vs-live recon stage-DAG comparison contract,
  ]
referenced_by:
  [
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/04-architecture/reconciliation-age-tracking.md,
    /codex/04-architecture/separation-of-concerns.md,
    /codex/08-workflows/t1-batch-dag.md,
    /codex/15-runbooks/position-reconciliation-deploy-gate.md,
    plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
execution:
  {
    owner:
      batch-live-reconciliation-service maintainer (resolution API + per-stage thresholds) + DART operability owner (UI
      workflow),
    cadence: T+1 nightly (per-stage recon runs); on-demand (operator-driven break resolution via UI),
    verifier:
      batch-live-reconciliation-service GET /api/breaks + POST /api/resolve persists ReconciliationResolution per UAC
      internal/reconciliation.py; deviation thresholds per-stage from models/deviation_thresholds.py.,
    last_executed: NEVER (T+1 recon DAG runs in staging; prod activation pending master plan F-21),
  }
---

# Reconciliation Resolution Architecture

## Overview

The reconciliation resolution workflow allows operators to accept, reject, or investigate batch-live reconciliation
breaks from the UI, and book correcting trades when needed.

## Reconciliation contract — batch ↔ live (codified 2026-05-12 per slot 8 audit PB-17)

> **Architecture-level contract** for what gets compared between batch and live runs, the comparison keys, the per-stage
> deviation metrics, and the failure-routing policy. Sister doc to the UI-resolution workflow below.

Derived from the CLAUDE.md `Batch = Live: Unified Pipeline Architecture (CRITICAL)` invariant + master plan readiness
item F-21. The contract is **per-archetype** (every strategy archetype runs through the same recon DAG with
archetype-specific tolerance bands).

### Invariant — same code path, only fill source differs

Batch + live use identical service interactions (strategy → execution → PBMS → pnl-attribution → risk-and-exposure).
Recon does NOT exist to validate "two implementations of the same logic" — it exists because the **fill source differs**
(matching-engine simulated fills vs real venue fills) and we need to decompose **execution alpha**
(`live fills P&L − simulated fills P&L`) from **strategy alpha** (the alpha the strategy would capture under a perfect
fill model). Per CLAUDE.md `Batch = Live`: _"execution alpha = live fills P&L − simulated fills P&L"_.

### Inputs to the recon DAG

| Input                | Source                                                                                                                                                            | Role                                    |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Positions baseline   | PBMS query API (see [`separation-of-concerns.md`](separation-of-concerns.md) § "Positions SSOT")                                                                  | Canonical position state for both sides |
| Live fills           | execution-service fills stream (real venue)                                                                                                                       | Numerator: live execution P&L           |
| Simulated fills      | execution-service matching engine (5 matchers: L0 Sports TOB, L1 TradFi, L2 CeFi, AMM, ALPHA_ZERO) on the same input ticks                                        | Denominator: simulator P&L              |
| Strategy emissions   | strategy-service signals (Pub/Sub or replayed)                                                                                                                    | Strategy-alpha attribution              |
| Per-stage thresholds | `batch-live-reconciliation-service/.../models/deviation_thresholds.py` (`MLThresholds` / `StrategyThresholds` / `ExecutionThresholds` / `DataPipelineThresholds`) | Tolerance bands per pipeline stage      |

### Comparison keys

Both sides emit rows partitioned by `pipeline_mode` (batch / paper / live) per
[`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md). Matching is on:

- **`(strategy_id, instrument, timestamp_bucket)`** — primary diff key (timestamp_bucket = bar granularity, e.g. 1m / 1h
  depending on the stage).
- **`correlation_id`** — secondary lineage key for tracing a single signal through both pipelines.
- **`client_order_id` / `client_id`** — order-lineage match for execution-recon (per slot 8 audit PB-3, current
  execution-audit lineage is order-keyed; long-term threads `client_id` through both projections so the diff is
  unambiguous across batch + live).

### Stage DAG (per current shipped shape; 6 logical stages)

Per slot 8 audit PB-6 (corrected from "5-stage" in stale SSOT-INDEX):

1. **`stage0_config_pull`** — pulls the immutable config snapshot the recon will assert against.
2. **`stage0_manifest_reason_check`** — batch vs live manifest `capture_status` / `error_reason` agreement.
3. **`stage0_data_pipeline_recon`** — input-data parity (manifest row counts + parquet schema + sample reads match
   between batch + live).
4. **`stage1_ml_recon`** — ML prediction parity (`MLThresholds` deviation bands per feature × prediction).
5. **`stage2_strategy_recon`** — signal emission parity (`StrategyThresholds` band on signal magnitude + direction).
6. **`stage3_execution_recon`** — batch-vs-live fill-level parity (`ExecutionThresholds` band on slippage / commission /
   notional; this is where the `live − simulated` execution-alpha lives).
7. **`stage3b_paper_live_recon`** — paper-vs-live parity (`PaperLiveThresholds`, 2× tighter); breach →
   `AUTO_DEMOTE_TO_PAPER`.
8. **`stage3c_batch_paper_recon`** — batch-vs-paper parity (`BatchPaperThresholds`, wider); breach → `ALERT`.
9. **`stage4_agent_analysis`** + **`stage5_results_writer`** — narrative + report write.

> **3-way recon shipped 2026-05-27** (was marked DEFERRED; un-deferred per BLRS audit
> `plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md`). Only **per-archetype** tolerance bands
> remain open (`pvl-p21a`).

### Output shape — alpha decomposition

The recon report decomposes total P&L diff into:

- **Strategy alpha** — diff attributable to strategy-side divergence (signal not emitted, signal emitted with wrong
  magnitude, etc.). Driven by stage 2.
- **Execution alpha** — diff attributable to execution-side divergence (slippage, commission, latency, venue liquidity
  miss vs matching-engine estimate). Driven by stage 3.
- **Data-pipeline noise** — diff attributable to upstream input drift (input partition mismatch, schema drift,
  late-arriving rows). Driven by stage 0.
- **ML noise** — diff attributable to prediction divergence. Driven by stage 1.

Sum of the four = total live-vs-batch P&L diff over the recon window.

### Tolerance bands

**Per-stage + per-pair today** (per `models/deviation_thresholds.py` — `ExecutionThresholds` / `PaperLiveThresholds` /
`BatchPaperThresholds`). **Per-archetype tolerance bands** (e.g. tighter for `carry_staked_basis` than for high-vol
scalping archetypes) remain a deferred extension — see master plan F-21 / sub-item `pvl-p21a`.

### Failure-routing policy (closed set)

- **In-band** (every deviation < its stage threshold) → write recon report; no alert.
- **Out-of-band** (any stage threshold breached):
  - **`alert`** — Telegram + UI flag; operator acks via resolution workflow below.
  - **`auto-pause-live`** — circuit-breaker fires `BLOCK_NEW` per
    [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md); existing positions held.
  - **`auto-demote-to-paper`** — strategy mode-flips from `LIVE_VENUE` to `SIMULATION` per
    [`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md); operator must explicitly re-promote.

Routing in use today: `alert` (most stages, incl. `stage3c`) + `auto-demote-to-paper` (`stage3b` paper-vs-live P&L /
fill-rate / slippage breaches). `auto-pause-live` is defined but not yet wired. Per-archetype routing refinement is the
open `pvl-p21a` work.

### Recon report bucket

Recon reports land in the canonical recon bucket resolved via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind="recon", ..., env=...)` — per
CLAUDE.md bucket-name SSOT (slot 8 audit PB-10 routes the in-tree migration of two surviving `# noqa: gs-uri` callsites
to the batch-live-reconciliation-service maintainer).

### Open design questions (PRE_CUTOVER — operator gate)

- **Per-archetype tolerance bands** — `carry_staked_basis` (steady carry) vs `leveraged_funding_arb` (higher variance)
  want different `ExecutionThresholds`. Today the thresholds are stage-level only. Operator/Ikenna call on whether
  per-archetype bands ship by May-23 or defer to `pvl-p21a`.
- **Recon schedule** — T+1 nightly (today) vs intra-day rolling window for the cutover monitoring period. Today declared
  T+1 in the `execution:` frontmatter above; a tightened cadence for the 7-day continuous-live window is a deferred
  decision.

### Composes with

- [`batch-live-architecture.md`](batch-live-architecture.md) — defines the `batch = live` invariant that recon enforces.
- [`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md) — describes the 4-mode seam this recon validates
  (batch ↔ live ↔ paper 3-way, shipped 2026-05-27).
- [`separation-of-concerns.md`](separation-of-concerns.md) § "Positions SSOT" — the canonical positions ledger (PBMS,
  merged into `strategy-service/position` on 2026-05-20). NOTE: whether BLRS reads that ledger's query API as its
  baseline (vs the GCS event archives it reads today) is open decision **D2** in the BLRS audit.

## Resolution Schema

`ReconciliationAction` enum and `ReconciliationResolution` model in UIC `reconciliation.py`:

| Action      | Value         | Description                                                    |
| ----------- | ------------- | -------------------------------------------------------------- |
| ACCEPT      | `accept`      | Expected divergence (timing, rounding) -- no correction needed |
| REJECT      | `reject`      | Error requiring correction -- triggers book-correction flow    |
| INVESTIGATE | `investigate` | Needs further analysis before resolution                       |

`ReconciliationResolution` fields:

- `break_id`: str -- ID of the break being resolved
- `action`: ReconciliationAction
- `note`: str (min 10 chars) -- FCA audit trail
- `resolved_by`: str -- Operator identity (OAuth sub)
- `correcting_instruction_id`: str | None -- Links to manual booking when action=REJECT

## Resolution API

Served by `batch-live-reconciliation-service/api/resolution_api.py`:

| Method | Path                            | Description                                                 |
| ------ | ------------------------------- | ----------------------------------------------------------- |
| GET    | /reconciliation/breaks          | List breaks with filters (venue, type, status)              |
| POST   | /reconciliation/resolve         | Accept/reject/investigate a break                           |
| POST   | /reconciliation/book-correction | Generate pre-filled ManualInstructionRequest for correction |

## UI Workflow

### Accept/Reject/Investigate

On the reconciliation page (`/services/reports/reconciliation`):

1. Non-resolved rows show 3 action buttons: Accept (green), Reject (red), Investigate (blue)
2. Clicking opens a dialog with note textarea (min 10 chars for FCA)
3. On confirm: calls `useResolveBreak()` mutation -> POST /reconciliation/resolve
4. Break status updates in the table

### Book Correcting Trade

When a break is rejected:

1. "Book Correction" button appears (PenLine icon)
2. Click calls `useBookCorrection()` -> POST /reconciliation/book-correction
3. Response contains pre-filled params (venue, instrument, delta quantity, execution_mode=record_only)
4. Navigates to `/services/trading/book?prefill={encoded_params}`
5. Back-office page reads prefill and populates the form

### View Market

Every reconciliation row has a "View Market" link -> navigates to
`/services/trading/markets?instrument={id}&venue={venue}`. The markets page has ManualTradingPanel as a slide-out for
that instrument.

## SSOT

- Resolution schemas: `unified-api-contracts/unified_api_contracts/internal/reconciliation.py`
- Resolution API: `batch-live-reconciliation-service/batch_live_reconciliation_service/api/resolution_api.py`
- UI hooks: `unified-trading-system-ui/hooks/api/use-reports.ts` (useResolveBreak, useReconciliationBreaks,
  useBookCorrection)
- Reconciliation page: `unified-trading-system-ui/app/(platform)/services/reports/reconciliation/page.tsx`
