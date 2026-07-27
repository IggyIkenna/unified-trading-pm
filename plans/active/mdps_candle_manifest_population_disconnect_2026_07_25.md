---
doc_type: plan
title: MDPS candle-manifest population disconnect — root-cause + fix (S3 near-empty vs ~10.9M live candle objects)
summary:
  MDPS-owned root-cause + fix for the candle object↔manifest disconnect — root-cause first (three undistinguished
  hypotheses), because a fresh 2026-07-25 re-measurement shows the manifest is STILL only 6 degenerate CEFI rows, 4 days
  AFTER the writer fix landed. Then fix + backfill the historical corpus so skip-if-fresh and honest coverage stop lying
  about candles. This plan does NOT own the Option-A candle-path migration (a separate, already-tracked effort).
status: draft
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
assigned_vm: NA
execution_scope: local-only
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

- [ ] 1. [DATA] P0. **Distinguish hypotheses (a)/(b)/(c) with evidence.** For at least CEFI and one other asset_group:
      (i) find the most recent candle object's write timestamp per AG and compare to 2026-07-21 17:01 +0100 (752eaff) —
      falsifies (a) if any real post-fix write exists; (ii) if a post-fix write exists, check MDPS service logs /
      `log_event` output around that write for the `record_captured` try/except (the docstring's own comment names the
      catch site in `canonical_writer.py`) for a swallowed exception — confirms/refutes (b); (iii) instrument or sample
      `_resolve_policy_output_data_type`/`_publish_emission_check`'s decision across a representative batch of real
      candle writes to measure the actual `should_publish_row=False` rate — confirms/refutes (c). Definition of done: a
      named root cause (or a ranked set with evidence for each), not a guess between the three.
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

### 2026-07-25 — plan filed (scoping only; no code touched)

Filed per `data_pipeline_reconciliation_skill_2026_07_20.md` todo 40. Re-measured the CEFI manifest fresh against live
prod (not trusted from the source doc) specifically to check whether the 2026-07-21 writer fix had already closed the
gap by the time of filing — it had not (see Measured evidence). Read `canonical_writer.py` /
`canonical_writer_stamping.py` / `candle_write_mixin.py` directly to confirm the `record_captured` call's current shape
and its two follow-up commits (`752eaff` + same-day `2d720b4`), which is why this plan's framing is "still broken in a
more specific way" rather than "call is missing" — filing it as the latter would have been stale the moment it was
written. No code changed in this repo or in `market-data-processing-service` as part of this filing.
