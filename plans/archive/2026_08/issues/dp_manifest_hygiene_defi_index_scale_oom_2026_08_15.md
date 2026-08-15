---
doc_type: issue
title:
  dp-manifest-hygiene-changed OOM at Cloud Run's 32Gi ceiling — defi manifest index is 160M rows, needs a
  streaming/DuckDB rewrite
summary: >-
  DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED escalation agt-11a922 (2026-08-15): `uts-prod-dp-manifest-hygiene-changed`
  OOM-killed on every daily 08:00 UTC run for 2026-08-11..08-15+. Bumping to 8vCPU/32Gi (Cloud Run gen2's hard ceiling)
  and vectorizing the divergence-detector's groupby (both shipped, both real improvements, both KEPT) were CONFIRMED
  INSUFFICIENT via two live re-executions that still OOM'd. Root cause pinned down via direct measurement: `defi`'s
  `availability_index.parquet` is 160,774,844 rows / 6.75GB on disk (13x the next-largest AG) — `detect_manifest_
  divergence.py`'s manifest reader loads this into a pandas DataFrame in full, which no in-process fix can bound within
  32Gi. A genuine redesign (streaming/DuckDB pushdown, or reducing defi's manifest row-count at the source) is needed;
  this exceeds what a one-shot escalation worker should freelance-rewrite for a data-correctness-critical oracle.
status: resolved
nature: issue
asset_group: [defi, cross-cutting]
stage: [data]
repos: [unified-trading-library, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-pipeline, dp-watcher-006, oom, defi, manifest, divergence, cloud-run, escalation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
  ]
created: 2026-08-15
author: claude-code (data_pipeline_failure escalation worker, slot 2, escalation agt-11a922)
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source:
  [
    "DP-WATCHER-006/DP_CLOUD_RUN_JOB_FAILED escalation agt-11a922, dispatched 2026-08-15 for
    uts-prod-dp-manifest-hygiene-changed failing 1398m prior. No issue doc was pre-filed — the alert carried the details
    per the escalation context.",
  ]
resolved_by:
  unified-trading-pm (this doc's own scope: escalation-trail + the two shipped mitigations documented, Option-A
  rewrite handed off to data_pipeline_self_healing_completion_residual_2026_07_24.md's P1 todo, Option-C investigation
  completed 2026-08-15 with findings recorded below — see Progress Log)
locked_by:
locked_since:
context_scope:
  [
    unified-trading-library/scripts/detect_manifest_divergence.py,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-15** — this doc's own scope is closed: the escalation trail is documented, the two shipped
> mitigations (32Gi ceiling bump + vectorized aggregation) are KEPT, the durable Option-A streaming/DuckDB rewrite is
> handed off to `/plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`'s P1 todo (dispatch from
> there, this doc is not the tracking home for it), and the Option-C non-blocking investigation completed this same
> session with findings recorded in the Follow-up section below. 0 open todos here.

# dp-manifest-hygiene-changed OOM — defi manifest index scale exceeds Cloud Run's ceiling

## What I found

`uts-prod-dp-manifest-hygiene-changed` (Cloud Run Job, `asia-northeast1`, `central-element-323112`) OOM-killed
("Container terminated on signal 9" / "The configured memory limit was reached") on every completed execution from at
least 2026-08-11 through 2026-08-15 — 5+ consecutive daily 08:00 UTC failures, each dying in ~55-126s (fast, nowhere
near the 1800s job timeout).

**Investigation trail (this session, escalation agt-11a922):**

1. Confirmed via `gcloud run jobs executions list` — every recent execution's `conditions` message is literally "The
   configured memory limit was reached" at the prior 4vCPU/16Gi config.
2. **Attempt 1** (initially wrong diagnosis): suspected `detect_manifest_divergence.py::_build_oracle_expected`'s nested
   per-day×venue×data_type Python-dict-list generation. Bumped `dp_manifest_hygiene_changed_job` to 8vCPU/32Gi (Cloud
   Run gen2's hard ceiling — 32Gi requires cpu=8, confirmed the platform max) via `deployment-service@6c98fbacc9`,
   applied live via `tofu apply` (verified `gcloud run jobs describe` shows `cpu=8;memory=32Gi` live). **Re-executed the
   job manually to verify — still OOM'd** (same signal, ~126s runtime, slightly longer than at 16Gi but not
   proportionally so).
3. Measured `get_expected_pairs()` per AG directly: cefi=65, defi=226, tradfi=16, sports=6, prediction=5 pairs — the
   oracle-mode row count is `pairs × date_span_days`, measured ≈205K for cefi (3149-day span) and same order for others.
   **This is NOT the memory hog** — a few hundred thousand rows is cheap. Attempt 1's diagnosis was wrong; corrected the
   terraform comment + this doc's predecessor plan-todo in the same session rather than leave a stale pointer.
4. **Attempt 2**: found `_aggregate_manifest()` used `.groupby(...).agg(col=("capture_status", lambda x: ...))` — a
   per-group Python-lambda callback pandas cannot vectorize. Rewrote to whole-frame vectorized boolean columns + the
   pandas built-in `"any"`/`"count"` aggregators (zero logic change; 17/17 existing
   `tests/unit/test_detect_manifest_divergence.py` cases pass). Shipped `unified-trading-library@2945ab584c`, verified
   ancestor of `origin/live-defi-rollout`. **Re-executed the job again — still OOM'd**, same signal.
5. **Root cause, confirmed by direct measurement**: `gcs_describe_object` shows `defi`'s
   `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` is **6,749,359,952 bytes
   (6.75GB)** — cefi is 514.8MB, tradfi 375.3MB, sports 306.3MB, prediction 207.2MB (defi is 13-33x every other AG). A
   `pyarrow.parquet.ParquetFile(...).metadata.num_rows` read (footer-only, cheap, does not materialize data) confirms
   **159,774,844 rows / 1,300 row groups** for defi alone. A local reproduction of
   `detect_manifest_divergence.py::_load_manifest_index`'s exact 4-column projected `pd.read_parquet` call **got
   OOM-killed on THIS shared host mid-read** (`/usr/bin/time -v` showed RSS at 14.1GB and still climbing when SIGKILL'd)
   — i.e. even the column-pruned pandas read of defi's index alone, independent of any downstream aggregation, already
   exceeds what fits comfortably even on a host with far more headroom than the 32Gi Cloud Run ceiling. Object-dtype
   pandas string columns over ~160M rows across even 4 columns (date/venue/data_type/ capture_status) is the expected
   shape of this blowup (~50-100+ bytes of Python object overhead per cell, independent of the actual string content
   length).

**Why defi's index is so much larger than every other AG's** (not yet root-caused — flagged as an open question, not
established fact): the oracle's `get_expected_pairs("defi")` only returns 226 (venue, data_type) pairs, yet the raw
manifest has 160M rows — many orders of magnitude finer-grained than the oracle's venue abstraction. This is CONSISTENT
with (but not confirmed as) defi's manifest being keyed per-pool-address / per-instrument rather than at the oracle's
coarser protocol-level venue grain, which would be architecturally expected for DeFi (many pools per protocol × years of
daily granularity) but is worth an explicit design confirmation rather than assumed.

## Why it matters

- **The alert is still firing** — the two shipped fixes (32Gi ceiling bump + vectorized aggregation) are both real,
  correct, low-risk improvements and are KEPT (do not revert), but neither is SUFFICIENT alone, and 32Gi is the Cloud
  Run gen2 platform maximum — there is no further "bump memory" lever available on this compute tier.
- **A correctness-critical oracle** (`detect_manifest_divergence.py` — DIVERGENT_EMPTY/MISSING_EXPECTED classification
  feeds the manifest-hygiene RED/GREEN verdict and the daily digest) cannot currently complete for `defi` at all via the
  daily "changed" path — defi's divergence/missing-expected findings have been silently absent from every recent daily
  hygiene run (the job dies before producing any per-AG output).
- Per the data-pipeline-correctness HARD RULE, a persistent alert is "a bug to close, not noise to mute" — this should
  NOT be left muted/ignored while unresolved.

## Recommended decision

Three real options, not mutually exclusive:

- **A. [WORKER REC] Rewrite `detect_manifest_divergence.py`'s manifest read + aggregate path to never materialize the
  full frame** — either (i) iterate `pyarrow` row-groups (1,300 for defi) and aggregate incrementally per (venue,
  data_type, date) key without holding all rows at once, or (ii) push the aggregation into DuckDB via SQL over the
  parquet file directly (projection + predicate pushdown, no full pandas materialization) — DuckDB was already flagged
  as the established pattern for this problem CLASS (see the digest job's OOM history,
  `data_pipeline_self_healing_completion_residual_2026_07_24.md`). This is the durable fix but needs real design +
  careful equivalence verification against the existing 17-case test suite and the downstream CSV/DP-event consumers
  before shipping — genuinely more than a one-shot escalation should freelance under a 15-minute liveness bound for code
  this close to the honest-absence/divergence data-correctness contract.
- **B. Give `defi` a dedicated, appropriately-sized compute path** for its divergence check (e.g. a VM-based batch job
  like the backfill launchers use, rather than a lightweight daily Cloud Run job) — faster to ship than A, but changes
  what "daily manifest hygiene" actually covers/costs for defi and should be a deliberate choice, not a side-effect of
  an OOM patch.
- **C. Investigate whether defi's manifest SHOULD be this granular** — if per-pool/per-instrument rows could be
  aggregated coarser at write time (or the index itself pre-aggregated to a smaller companion artifact), the problem
  shrinks at the source instead of every downstream reader needing to cope with 160M rows. Bigger/riskier data-model
  question; likely a separate investigation, not blocking A or B.

## Current state (what to pick up)

- ✅ `deployment-service@6c98fbacc9` — `dp_manifest_hygiene_changed_job` at 8vCPU/32Gi (live, verified). KEEP.
- ✅ `unified-trading-library@2945ab584c` — vectorized `_aggregate_manifest`. KEEP, real improvement, just not
  sufficient alone.
- ❌ The job still OOMs on every execution (verified twice, 2026-08-15 08:39 and 08:53 UTC executions).
- Tracked follow-up already exists in `data_pipeline_self_healing_completion_residual_2026_07_24.md`'s residual section
  — the P1 todo there points here for the full investigation trail.

## Operator ruling (2026-08-15, via BLK-b06d255a, disposition: final)

> **Option A** — pursue the durable streaming/DuckDB-pushdown rewrite of `detect_manifest_divergence.py`'s manifest
> read+aggregate path, per the worker's own recommendation. This matches CLAUDE.md's Data Pipeline Correctness HARD RULE
> (a persistent alert on a correctness-critical oracle is a bug to close in full, not to mute or defer) and DuckDB is
> already the established pattern for this exact problem class per the referenced 2026-07-24 digest-job OOM precedent.
> Keep both already-shipped mitigations (32Gi ceiling bump + vectorized aggregation) — real, correct, just insufficient
> alone. Given the worker's own scoping (real design + equivalence verification against the 17-case test suite, too much
> for a one-shot escalation under a liveness bound), this should be dispatched as a properly-scoped follow-up task/todo
> rather than freelanced further in this escalation. Option C (investigate whether defi's manifest should be this
> granular at write time) is worth pursuing as a SEPARATE, non-blocking investigation in parallel — do not gate A on it.
> Option B (dedicated VM path) is not needed as the primary fix since A is the intended durable path and B would
> silently change what daily hygiene covers as a side effect of an OOM patch, which the doc itself says should be a
> deliberate choice, not adopted here.

**Resolution**: the streaming/DuckDB rewrite (Option A) is tracked as the P1 todo in
`data_pipeline_self_healing_completion_residual_2026_07_24.md` — dispatch it from there, do not re-open this
investigation. Option C (defi manifest granularity) is now tracked below (non-blocking on A).

## Follow-up

- [x] ✅ [DIAG] P3. **Investigate whether defi's manifest SHOULD be this granular at write time (Option C, non-blocking
      on Option A).** If per-pool/per-instrument rows could be aggregated coarser at write time (or the index itself
      pre-aggregated to a smaller companion artifact), the problem shrinks at the source instead of every downstream
      reader needing to cope with 160M rows. Separate investigation, does not gate the Option-A streaming/DuckDB
      rewrite. — unified-trading-pm (docs-only, this session, 2026-08-15). Findings below.

### Investigation finding (Option C), 2026-08-15

**Confirmed: defi's manifest IS this granular by deliberate design, not by accident or a writer bug.**
`DefiManifestRecorder.record_captured` / `record_empty`
(`market-tick-data-service/market_tick_data_service/cli/ handlers/_defi_manifest.py::_build_row_key`) accepts an
optional `instrument_id` (bare pool address, lowercase) that gets folded into the manifest `row_key` for
`dex_pools`/`dex_swaps` and per-feed oracle rows whenever non-blank — so the manifest grain for those data_types is
`(date, venue, chain, data_type, instrument_id)`, one row PER POOL, not per `(date, venue, chain, data_type)`.

**Scale check.** The prod DeFi instrument catalogue is **79,005 instruments** (measured 2026-08-05,
`defi_satellite_ao_dispatch_batch6_2026_07_30.md`) vs. the oracle's 226 `(venue, data_type)` pairs — a ~350x multiplier,
consistent with the observed 160M manifest rows: a venue-level grain would produce on the order of 226 pairs ×
~3,149-day span ≈ 710K rows (same order as cefi's 205K measured in this doc's Attempt 1 above), whereas per-pool grain ×
per-instrument effective lifespan lands at 160M.

**Why it's this granular is intentional, not a bug.** Per-pool manifest rows are the documented honest-coverage
mechanism: a per-pool `empty_confirmed`/`captured` row reconciles against the IS-seeded per-pool `expected_unattempted`
row (`_defi_manifest.py::record_empty` docstring: "a catalogue pool the subgraph returned no data for lands a PER-POOL
EXPECTED_NOT_ENOUGH_TVL reconciling its IS-seeded EU row"). Coarsening the WRITE-time grain to venue/chain level would
regress this per-pool honest-absence tracking — the SAME class of regression the lending A_TOKEN/DEBT_TOKEN per-token
retire caused (attempted twice, reverted twice, now ruled "WON'T-DO, permanently" —
`/codex/02-data/defi-canonical-naming-ssot.md` § lending; that retire's own investigation found flipping the write grain
silently regresses ~1.04M EU→captured conversions without a matching IS re-seed).

**Recommendation: do NOT change the write-time grain.** The "aggregate per-pool rows coarser at write time" half of
Option C is unsafe for the reason above. The safe half of Option C is a separate **READ-SIDE pre-aggregated companion
artifact** — e.g. a consolidator-materialized `_index/availability_index_by_venue.parquet` rollup
(venue/chain/data_type/date grain, alongside the existing per-pool index) — for `detect_manifest_divergence.py` to read
instead of the full 160M-row per-pool index, since the UAC oracle's `expected_coverage()` only ever classifies at
venue/chain/data_type/date grain and never needs per-pool detail for its DIVERGENT_EMPTY/MISSING_EXPECTED
classification. This does not replace Option A (the DuckDB/streaming rewrite is still the durable general fix and covers
every AG, not just defi) but would let a future divergence-detector redesign skip touching the per-pool rows entirely
for defi. Feeds Option A's design; no code changed in this investigation — tracked as design input for the P1 todo in
`data_pipeline_self_healing_completion_residual_2026_07_24.md`, not a new separate follow-up.
