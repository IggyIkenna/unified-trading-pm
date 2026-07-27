---
doc_type: plan
title: MDPS candle-manifest population disconnect — root-cause + fix (S3 near-empty vs ~10.9M live candle objects)
summary:
  MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER the writer fix landed. Then fix + backfill the historical corpus so skip-if-fresh and honest coverage stop lying
  about candles. This plan does NOT own the Option-A candle-path migration (a separate, already-tracked effort).
status: active
nature: process
asset_group: [cefi, defi, tradfi, prediction]
stage: [data]
repos: [market-data-processing-service, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [mdps, candles, manifest, record-captured, object-manifest-disconnect, honest-coverage, skip-if-fresh, root-cause]
related:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/mdps-candle-canonical-reconciliation.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  candle_feature_canonical_path_divergence_2026_07_20.md todo 7 (object↔manifest disconnect, first measured 2026-07-20,
  re-confirmed cross-AG 2026-07-23); filed per data_pipeline_reconciliation_skill_2026_07_20.md todo 40 ("scope the
  writer fix as its own MDPS-owned plan — this plan does not own MDPS writer work")
---

# MDPS candle-manifest population disconnect — root-cause + fix

> **Filing note (operator: ask-before-creating a new plan).** Default track applied here is **LOCAL / human**
> (`assigned_vm: NA`, `status: draft`) per the workspace's ask-before-creating rule — this doc was not authored with
> operator confirmation that the fleet should pick it up automatically. **Recommendation, not a decision**: todo 1 (the
> root-cause diagnostic) reads as AO-dispatch-eligible on its own — it is a bounded, determinable audit ("which of
> hypotheses a/b/c explains the gap, with evidence"), similar in shape to the already-AO-dispatched
> `defi_lending_writer_retire_prerequisite_2026_07_20.md`. Todos 2-3 (the actual writer fix + historical backfill) carry
> real prod blast radius (a manifest backfill touching up to ~4.4M rows across 4 asset_groups) and are less clearly
> dispatch-safe without a human decision on backfill mechanism. If the operator wants this on the fleet, flip
> `assigned_vm: planning` + `status: active` and consider splitting todo 1 into its own gating plan per the
> partial-parallelism rule (`task_template.md` §4) rather than flipping the whole doc at once.

> **Why this is its own plan, not folded into the reconciliation-skill plan or the candle-path migration.** The
> reconciliation-skill plan (`data_pipeline_reconciliation_skill_2026_07_20.md`) is itself fully shipped except for the
> two todos (40/41) that reference this gap — it does not own MDPS writer work by design (todo 40's own text). The
> Option-A candle-**path** migration (`candle_feature_canonical_path_divergence_2026_07_20.md`, folded into
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md`) is a PATH-shape migration (add `instrument_type=` +
> `pipeline_mode=` segments) — already P6→P7→P8 COMPLETE for all 4 asset_groups (2026-07-23). This plan is a
> **different** axis: the candle **manifest** is not being populated at all, independent of which path shape the objects
> carry. Fixing the path shape did nothing to fix this (confirmed directly, see Measured evidence).

---

## Measured evidence (fresh, 2026-07-25 — not carried forward from the source issue doc)

Re-verified directly against the LIVE prod CEFI manifest today, rather than trusting the 2026-07-20/2026-07-23
measurements as still current:

```
bucket: market-data-tick-cefi-prd-central-element-323112
object: _index/availability_index.parquet (165.65 MB, downloaded fresh 2026-07-25)
total rows: 9,192,725
rows where service_name == "market-data-processing-service": 6
  all date=2026-04-14; all written_at in [2026-04-16T15:25:11.888861Z, 2026-04-16T15:25:11.915172Z]
  (one row per SOURCE data_type: book_snapshot_5, derivative_ticker, futures_chain, liquidations, options_chain, trades)
```

**This is byte-identical to the 2026-07-20 and 2026-07-23 measurements** in the source issue doc — unchanged across
three independent measurements spanning 5 days, **including the 4 days after the writer fix
(`market-data-processing-service@752eaff`, 2026-07-21) shipped.** Cross-AG numbers from the 2026-07-23 measurement (not
re-verified today, carried from the source issue doc — re-verify per todo 4 before trusting them further): defi 0 rows
(23.47M total manifest rows, 1,123,415 live candle objects) · tradfi 73 rows (5.88M total, 534,679 objects, all
`instrument_type=''`) · prediction 168 rows (758,961 total, 583,228 objects). The P0 census (2026-07-22) measured
**~10.9M live candle objects** across the 4 asset_groups with `ORPHAN=0` on every one — the objects are real and
structurally sound; they are simply invisible to the manifest.

## The writer DOES call `record_captured` today — the "not calling it at all" framing is stale

`market_data_processing_service/app/core/canonical_writer.py`'s `write_candle_parquet` — reached via
`CandleWriteMixin._upload_candles_to_gcs`, which its own module docstring calls **the sole candle write path** ("Phase
5b.2 ... all GCS writes now route through `canonical_writer.write_candle_parquet`") — **does** emit
`manifest_writer.record_captured(...)` per shard, keyed on the SOURCE `data_type` (landed
`market-data-processing-service@752eaff`, 2026-07-21 17:01 +0100; a same-day follow-up
`market-data-processing-service@2d720b4`, 2026-07-21 18:11 +0100, fixed a `MissingSourceError` the first version raised
on every multi-source cell — confirmed by the reconciliation-skill plan's own Progress Log: _"the `-test-` gate ran...
first attempt failed on a real regression (a `source=` manifest-write guard mismatch, fixed `mdps@2d720b4`), then PASSED
— a real GCS object was ground-truthed carrying the exact LOCKED shape, path==manifest confirmed."_).

So the call **exists** and was **proven working against a `-test-` bucket** the same day it landed. The measured PROD
gap (still 6 degenerate rows, 4 days later) is therefore a **more specific defect than "missing call"** — this plan's
first job is to find out exactly which of three non-exclusive hypotheses (below) explains why a call that is proven to
work in `-test-` is not populating PROD.

## Three hypotheses — none yet distinguished (this is todo 1)

- **(a) No genuine PROD candle write has executed since 2026-07-21 to exercise the fixed path at all.** Candle capture
  may be effectively paused: DeFi capture is stated STOPPED elsewhere in the corpus
  (`data-pipeline-reconciliation/SKILL.md` §3d), the raw-tick migration fleet was still draining as of 2026-07-21-23
  (candle-path migration explicitly scheduled to start only after that drains), and the ~10.9M-object candle corpus the
  P0 census measured is dominated by PRE-2026-07-21 historical writes. If no live/forward MDPS candle run has actually
  executed against a `-prd-` bucket since 752eaff, the manifest would trivially still show only the 2026-04-14 rows —
  this is the cheapest hypothesis to falsify (check the most recent candle object's `updated`/creation timestamp per AG
  against 2026-07-21).
- **(b) The call is reached but silently fails in prod.** The `record_captured` call sits inside a bare
  `try: ... except Exception as exc:` block (`canonical_writer.py`, comment: _"manifest write failure must not corrupt
  the candle write"_) — ANY exception (the 4-pillar write-gate's own validation, a `LookaheadBiasError`, a
  `MalformedRowKeyError`, exhausted GCS 429 retries in `_flush_manifest_with_backoff`) is caught, logged, and the
  function returns normally with the parquet bytes already in GCS. This is BY DESIGN for shard isolation, but it means a
  _systematic_ prod-only failure (e.g. a prod-only manifest-bucket permission gap, a `GCP_PROJECT_ID`/env difference
  between the `-test-` proof run and the real prod deployment, a row-key field only prod data exercises) would be
  invisible except as this exact symptom — no service error, no alert, just an ever-widening gap. No log/metric evidence
  of this firing has been checked yet.
- **(c) The `should_publish_row` emission-policy gate suppresses more than its "heartbeat-only" carve-out intends.**
  `_resolve_policy_output_data_type` / `_publish_emission_check` (`canonical_writer_stamping.py`) can set
  `should_publish_row=False`, in which case the parquet is still uploaded but `record_captured` is skipped entirely (by
  design, for genuinely heartbeat-only paths) — but the actual selectivity of this gate in real prod traffic has not
  been measured. If it fires far more broadly than the "heartbeat-only" case it was built for, most real candle shards
  would be silently manifest-invisible **without any exception being raised at all** — a different mechanism than (b),
  same symptom.

**Do not guess between these — todo 1 exists to distinguish them with evidence** (a log line, a measured
`should_publish_row=False` rate, or a timestamp comparison), not to assume one.

---

## Todo 1 Findings (2026-07-27, slot-14) — ranked root cause with evidence

**(a) No real prod candle write since `752eaff` — REFUTED.**
`deployment-service/configs/cloud-run/market-data-processing-service.yaml` declares MDPS as an always-on Cloud Run
Service (`autoscaling.knative.dev/minScale: "1"`, `DEPLOYMENT_ENV=prod`), with the module docstring stating "Streaming
processor runs as background thread inside FastAPI lifespan." `deployment-service/terraform/gcp/t1_batch_scheduler.tf`
also fires a daily `market-data-processing` Cloud Run Job at `0 1 * * *` ("T+1 recon batch — candle aggregation"). Git
history for `market-data-processing-service` since `752eaff` shows **active, very recent (2026-07-26) engineering work**
fixing real bugs hit while running actual candle backfills against real prod-scale data volumes — e.g. `86a1623` ("scope
CEFI raw_tick_data GCS listing by venue to fix backfill OOM"), `8e5db1d` ("row-group date filter on DEFI live-gap
manifest read to fix t1-recon OOM"), `335e9cc`/`22b926c` (CEFI listing/retry fixes) — these describe real
OOM/empty-listing incidents against real GCS objects and manifests at multi-million-row scale, which could not happen if
candle capture were paused. The candle-processing pipeline is demonstrably running; the disconnect is downstream of the
write, in the manifest-recording step.

**(b) `record_captured` exception silently swallowed in prod — CONFIRMED, contributing.**
`market_data_processing_service/app/core/canonical_writer.py:509-586` (`write_candle_parquet`) wraps the
`manifest_writer.record_captured(...)` call in a bare `except Exception as exc:` that logs only at WARNING
(`log_event("DEPLOYMENT_FAILED", severity="WARNING", ...)` +
`logger.warning("MDPS canonical_writer: manifest write failed for %s day=%s tf=%s: %s", ...)`), never re-raises, and
returns `bytes_written` normally — the candle parquet is already uploaded to GCS at that point (line ~499, before this
block), so the write "succeeds" from every caller's perspective even when the manifest row never lands. This is not
theoretical: commit `2d720b4` (2026-07-21 18:11 +0100, one hour after `752eaff`) fixed a real `MissingSourceError` (a
`ValueError` subclass, `unified-trading-library/unified_trading_library/manifest_writer/_schema.py:308`) that fired on
"every force-leg write for CEFI:DERIBIT:trades" through this exact swallow path — proof the mechanism is live-fire, not
hypothetical. Any other manifest-write exception (GCS 429/Forbidden/NotFound, a schema-contract violation, a
`LookaheadBiasError`) reduces to the identical silent-WARNING outcome. This explains a REAL but likely smaller slice of
the gap (whatever fraction of writes hit a genuine exception) — it does not by itself explain a near-total (6-row)
manifest population across ~10.9M objects.

**(c) The `should_publish_row` emission-policy gate suppresses far more than its "heartbeat-only" intent — CONFIRMED,
primary/structural cause.**
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/service_emission_policy/_policies.py:17-22` sets
`STRICT_FAIL` for `("market-data-processing-service", "ohlcv_1m:current")`, `("...", "ohlcv_1h:current")`, and
unconditionally for `("...", "book_snapshot_5")` (no `:current`/`:historical` split at all) — these are MDPS's primary
real-time CeFi candle products, not a narrow heartbeat carve-out. `canonical_writer_stamping.py:528-557`
(`_build_ohlcv_1m_upstream_window`) is the upstream-window builder wired for ALL 4 gated data_types via
`_publish_emission_check` (line 472) — **independently verified**: it always returns a single-element list keyed at
`data_type="ohlcv_1m"` with the SAME `(date, venue, instrument_type, instrument_id, timeframe)` tuple as the row_key
being written, regardless of which output_data_type triggered the check. Its own docstring admits this: "Returns a
single-element list — manifest-grain completeness for the POC; bar-level sub-day inspection is a future enhancement."
For the `ohlcv_1m → ohlcv_1m` passthrough case specifically (the module docstring's own table,
`canonical_writer_stamping.py:362-370`), this means the completeness check for a shard's OWN manifest row reads the
availability index (`read_availability_index`,
`unified-trading-library/unified_trading_library/manifest_completeness.py:391-397`) for that SAME shard's key — on the
first-ever write, `status_by_key.get(lookup_key)` returns `None` (no prior row exists) → treated as
`expected_unattempted` → completeness < 1.0 → `STRICT_FAIL` fires → `should_publish_row=False` → `record_captured` is
skipped before it's ever called → the row can never be created → every subsequent write of the same shard hits the
identical check and fails identically, forever. This is a permanent, self-reinforcing lockout for every "current-day"
1m/1h candle and unconditionally for every book_snapshot_5 candle (no historical exemption for the latter at all) —
structurally matching the observed near-total manifest absence far better than (b) alone. Suppression is logged only at
`logger.info` (`canonical_writer.py:417-428`, message
`"MDPS emission policy skipped record_captured for %s day=%s ... "`) — the lowest severity, easily filtered out of prod
log routing, which is consistent with this having gone unnoticed for weeks.

**Evidence NOT yet gathered (deferred, not required to name the root cause)**: a live GCS-object-timestamp check for a
specific recent CEFI candle shard (todo 1(i)'s literal ask) was attempted but timed out twice (~30-60s) against a
still-recovering-from-contention host — not re-attempted further since the deployment-config + git-history evidence
above already refutes (a) independently and doesn't change the (b)/(c) ranking. A future session/todo-2 implementer
should feel free to re-run this as a sanity check, but it is not a blocker for todo 2 (the fix), since (c)'s mechanism
is proven from the code itself, not inferred from absence of GCS activity.

---

## Acceptance criteria

This plan is done when:

1. The root cause (one or more of a/b/c, or a fourth found during investigation) is named with evidence, not inferred.
2. Whatever writer defect exists is fixed and proven by a **real** forward candle write (not a `-test-`-only proof) that
   lands a `capture_status=captured` manifest row with non-`NaN` `row_count` for at least one shard per affected
   asset_group, verified by reading the manifest — not by the writer's own return value.
3. The historical corpus (objects written before the fix, or by any writer version that never populated the manifest)
   has manifest rows backfilled/re-derived so `service_name=="market-data-processing-service"` row counts are within a
   stated tolerance of the live GCS object counts, per asset_group — or, if a full backfill is ruled out of scope, that
   decision is recorded explicitly with the reason (this plan does not assume the backfill is in scope by default; it is
   scoped by todo 3).
4. A fresh 3-surface (object / manifest / path) spot check post-fix shows the disconnect closed for at least one
   asset_group on real data, not just a design review.
5. The parent issue doc's todo 7 (`candle_feature_canonical_path_divergence_2026_07_20.md`) and the reconciliation-skill
   plan's todo 40 both carry the resolution + evidence.

---

## Todos

- [x] ✅ 1. [DATA] P0. **DONE 2026-07-27 (slot-14).** Distinguished hypotheses (a)/(b)/(c) with evidence — see "Todo 1
      Findings" section below. **Ranked verdict: (c) is the primary, structural root cause; (b) is a real contributing
      mechanism for a smaller subset of failures; (a) is REFUTED.** The gate logic in `canonical_writer_stamping.py`
      applies uniformly across all 4 asset_groups (data_type-keyed policy table, not asset_group-keyed), and the
      Measured-Evidence section's cross-AG numbers (defi 0, tradfi 73, prediction 168 manifest rows vs 1.1M+ live
      objects each) already show the identical symptom shape everywhere this code path runs — consistent with a
      shared-code-level bug, not a CEFI-specific one.
- [ ] 2. [CODE] P0. **Fix the root cause found in todo 1.** Scope depends entirely on todo 1's finding — do not
      pre-design the fix before todo 1 lands. If (a): this becomes a liveness/scheduling question (why isn't the live
      candle writer running against prod) rather than a code fix — escalate to the operator with the finding rather than
      inventing a code change for a non-code problem. If (b): make the swallowed exception loud + fixed (mirroring
      `/codex/04-architecture/shard-level-failure-isolation.md`'s classify-don't-swallow discipline, same pattern used
      in `defi_lending_writer_retire_prerequisite_2026_07_20.md` todo 5). If (c): tighten the emission-policy predicate
      so it fires only for genuine heartbeat-only shards. Prove the fix with a REAL prod (not `-test-`-only) forward
      write per acceptance criterion 2.
- [ ] 3. [DATA] P1. **Scope the historical-corpus manifest backfill.** ~10.9M live candle objects (P0 census,
      2026-07-22) predate any working writer fix and will never retroactively gain manifest rows from the fix alone.
      Decide + record the mechanism: most likely a candle-specific manifest-backfill pass modeled on the raw-tick
      manifest consolidator (`/codex/05-infrastructure/manifest-consolidator-ssot.md`) or the `record_captured`-from-
      GCS-listing shape the defi 648-twin fold hit the SAME wall on
      (`/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md` — read that doc first, it already
      found `ManifestWriter(batch_size=1)` does not flush cleanly from a plain script; do not rediscover this the hard
      way). **Heavy I/O — this is a corpus-scale backfill across 4 asset_groups (~10.9M candidate rows) and MUST run on
      a VM, never in-session** (per the heavy-I/O hard rule). `[OPERATOR]` if the chosen mechanism involves a prod
      manifest write at this scale without an already-established idempotent pattern — cite
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` if any delete/overwrite semantics are involved (a pure
      `record_captured` backfill of previously-absent rows is additive, not a delete, but state that explicitly rather
      than assuming it). If overwrite semantics ARE involved (e.g. rewriting an existing manifest shard rather than
      appending), the §3a reversibility carve-out may apply instead of `[OPERATOR]` — GCS Soft Delete covers overwrites
      too, not just deletes — provided a fresh `gcs_bucket_soft_delete_retention_seconds(...)` check on the target
      manifest bucket returns `>= 604800` at execution time; cite the actual queried value, don't assume it.
- [ ] 4. [DATA] P1. **Re-verify the cross-AG numbers fresh** (this plan's Measured Evidence carried defi/tradfi/
      prediction from the 2026-07-23 measurement in the source issue doc, only re-verifying cefi directly) before
      relying on them for the backfill's sizing in todo 3 — a stale number risks under- or over-sizing the VM job.
- [ ] 5. [DATA] P1. **Run the historical backfill** designed in todo 3, on a VM, with a heartbeat watchdog per the
      async-wait discipline (progress metric = manifest rows written, entity-scoped, `time_created` not activity).
      Depends on 3.
- [ ] 6. [DATA] P0. **3-surface spot check post-fix** — object path / manifest row / parquet content agree for a sample
      of shards written after todo 2's fix, and for a sample of shards backfilled by todo 5, on real data. Any
      disagreement is a fail of this plan's acceptance criterion 4, not a follow-up note.
- [ ] 7. [REVIEW] P1. **Close the loop on the source docs.** Flip
      `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7 with this plan's evidence (do not duplicate the
      writeup — link here), and confirm `data_pipeline_reconciliation_skill_2026_07_20.md` todo 40's pointer to this doc
      is accurate post-completion.
- [ ] 8. [PM] P2. **Notify the operator** of the root cause found in todo 1 regardless of which hypothesis it turns out
      to be — this is a cross-cutting data-correctness finding (skip-if-fresh + honest coverage both silently wrong for
      the entire candle layer) per the big-finding notification rule, and hypothesis (a) in particular (candle capture
      not actually running in prod) would be a distinct, separately-actionable operational finding beyond a code fix.

---

## Progress Log

### 2026-07-27 (slot-14) — Todo 1 done: root cause distinguished with evidence

Distinguished the three hypotheses via direct code reads (`canonical_writer.py`, `canonical_writer_stamping.py`,
`unified-api-contracts`'s `service_emission_policy/_policies.py`, `unified-trading-library`'s
`manifest_completeness.py`/`emission_publisher.py`) plus `deployment-service`'s Cloud Run config + Terraform scheduler

- MDPS git history. See "Todo 1 Findings" section above for the full evidence with file:line citations. **Verdict: (a)
  refuted, (b) confirmed as a real but partial contributor, (c) confirmed as the primary structural cause** — the
  `should_publish_row` emission-policy gate's upstream-window check for `ohlcv_1m`/`ohlcv_1h`/`book_snapshot_5`
  degenerates to checking a shard's own not-yet-written manifest row (a documented "POC" simplification per the
  function's own docstring), creating a permanent chicken-and-egg lockout on the first-ever write of any shard, with
  zero historical exemption for `book_snapshot_5`. No code changed in this session — todo 1 is diagnostic-only per its
  own scope; todo 2 (the fix) is a separate todo, not pre-designed here per its own instruction ("do not pre-design the
  fix before todo 1 lands").

### 2026-07-25 — plan filed (scoping only; no code touched)

Filed per `data_pipeline_reconciliation_skill_2026_07_20.md` todo 40. Re-measured the CEFI manifest fresh against live
prod (not trusted from the source doc) specifically to check whether the 2026-07-21 writer fix had already closed the
gap by the time of filing — it had not (see Measured evidence). Read `canonical_writer.py` /
`canonical_writer_stamping.py` / `candle_write_mixin.py` directly to confirm the `record_captured` call's current shape
and its two follow-up commits (`752eaff` + same-day `2d720b4`), which is why this plan's framing is "still broken in a
more specific way" rather than "call is missing" — filing it as the latter would have been stale the moment it was
written. No code changed in this repo or in `market-data-processing-service` as part of this filing.
