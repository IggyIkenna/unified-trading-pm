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
status: open
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
