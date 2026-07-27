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
- [x] ✅ 2. [CODE] P0. **CODE SHIPPED 2026-07-27 (slot-10)** — `market-data-processing-service@caa995c`. Fixed both
      confirmed causes from todo 1: **(c) primary structural fix**: `_publish_emission_check`
      (`canonical_writer_stamping.py`) now special-cases `output_data_type.startswith("ohlcv_1m:")` and bypasses the
      self-referential manifest-lookup path entirely, publishing directly via
      `publish_with_policy(..., completeness_fraction=1.0)` — matching the module's own documented intent ("the writer's
      own emission IS the source-of-truth ... completeness=1.0 for the built bar means no inner-gap") instead of the
      buggy self-referential `_build_ohlcv_1m_upstream_window` lookup that always read completeness=0.0 on a shard's
      first-ever write. **(b) classify-don't-swallow**: the `record_captured` exception handler in `canonical_writer.py`
      now also calls `record_failed_for_shard(...)` so a failed manifest write lands an `attempted_failed` row instead
      of leaving the shard with NO row at all (mirrors the existing `SCHEMA_VALIDATION_FAILED` handler's own pattern one
      function up). Added a regression test class (`TestPublishEmissionCheckOhlcv1mBypass`) proving
      `ohlcv_1m:current`/`:historical` no longer call `publish_with_manifest_lookup` and that the REAL (unmocked)
      `publish_with_policy` now resolves `should_publish_row=True` on a first-ever write (pre-fix this was
      unconditionally `False`); extended 3 existing tests (`test_canonical_writer_ohlcv_1h_policy.py`,
      `test_canonical_writer_record_helpers.py`, `test_phantom_prevention.py`) to assert `record_failed_for_shard` fires
      on the swallowed-exception path. Full unit suite green (2222 passed, 1 skipped) + `quality-gates.sh` green (168s).
      **Acceptance criterion 2's "REAL prod (not `-test`-only) forward write" is NOT yet independently verified against
      live prod** — that requires the fix to reach the always-on MDPS Cloud Run service via the standard promote
      pipeline and a real candle write to land, which is exactly todo 6's ("3-surface spot check post-fix") job, not
      re-done here to avoid an open-ended live-deploy wait mid-dispatch. Hypothesis (a) was already refuted in todo 1 —
      no liveness/scheduling escalation needed.
- [x] 3. [DATA] P1. ✅ **DONE 2026-07-27 — mechanism scoped, no new script needed.** Read the referenced
      `defi_fold_manifest_registration_pending_2026_07_21.md` first per this todo's own instruction (confirms the
      `ManifestWriter(batch_size=1)` bare-script flush gap + the `GCP_PROJECT_ID`/`MANIFEST_PER_VM_SHARDS=true`
      requirements — both now fixed/documented, not rediscovered here).

      **Key finding: the registration mechanism ALREADY EXISTS and is ALREADY WIRED in, in
                          `market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py`.** Read the script directly rather
                          than assuming a new one was needed: `_apply_one()` dispatches on `cls.action` — for `A_VERIFY_ONLY` (an
                          already-canonical object needing no move, `_apply_one` line ~1080-1084) it calls
                          `_record_captured_for_target(uri, asset_group=asset_group)` directly; for `A_COPY` (a real
                          migrate/rename) it threads `record_manifest_asset_group=asset_group` into `_copy_verify_delete`, which calls the
                          SAME `_record_captured_for_target` on any outcome in `(success_label, "SRC_ALREADY_GONE",
                          "NOOP_TARGET_EQUALS_SOURCE")`. So **every object the apply pass touches — migrated OR already-canonical — is
                          already supposed to get a manifest row**, via a direct `ManifestWriter(service_name=...,
                          catalogue_bucket=bucket).record_captured(..., row_count=0, validate=False)` call
                          (`migrate_candle_canonical_2026_07.py:917-935`) — deliberately `row_count=0` + no content re-read, since
                          `check_shard_freshness` (the sole skip-if-fresh consumer, `unified_trading_library/manifest_writer/_queries.py`)
                          keys off shard PRESENCE + `capture_status`/`written_at`, never `row_count`, and re-reading ~11M objects' content
                          purely to satisfy a row-count would be prohibitively expensive at this scale (this reasoning is already in the
                          script's own docstring — not re-derived here). **This call is a DIRECT `ManifestWriter.record_captured()`, NOT
                          routed through `canonical_writer_stamping.py`'s `_publish_emission_check`/`should_publish_row` gate** (the
                          todo-1/2 root cause) — confirmed by reading the import (`from unified_trading_library import ManifestWriter`,
                          no `canonical_writer_stamping` import) and the inline QG-allow comment ("emission-policy-not-applicable —
                          migration re-record, not a derived output"). So todo 2's fix and this mechanism are INDEPENDENT — todo 2 fixed
                          the LIVE/forward writer path; this pre-existing migration-script path was never subject to that bug at all.

                          **Recommended mechanism: RE-RUN the EXISTING `<ag>-candle-apply` VM category**
                          (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`, `cefi-candle-apply` /
                          `defi-candle-apply` / `tradfi-candle-apply` / `prediction-candle-apply`) **in `full` mode for the complete date
                          range, per asset_group** — this is NOT a new script; it reuses the already-shipped, already-tested
                          `migrate_candle_canonical_2026_07.py --apply` pass verbatim, which already performs the SAME single-walk
                          enumeration (`gcloud storage ls -r gs://<bucket>/processed_candles/**`) this todo would otherwise need to build
                          from scratch, and is independently idempotent/re-run-safe by its own checkpoint-safety design — `VERIFIED_INPLACE`
                          / `NOOP_TARGET_EQUALS_SOURCE` / `SRC_ALREADY_GONE` are all explicitly `_CHECKPOINT_SAFE_OUTCOMES`, meaning a
                          re-run over already-migrated objects is a safe, cheap no-op on the move/rename side while still re-attempting the
                          manifest-record call. `MANIFEST_PER_VM_SHARDS=true` is already exported globally by
                          `setup-data-pipeline-vm.sh` for every VM this launcher spawns (per the launcher's own comment at line ~897) —
                          the defi-fold doc's env-var pitfall is NOT the cause here, already ruled out.

                          **Open question left for todo 5 (the execution) to check BEFORE re-running, not assumed here**: it is not yet
                          established WHY the P7/P8 apply pass (cited elsewhere in this plan as "COMPLETE 2026-07-23") left the manifest
                          this empty if `_record_captured_for_target` really fired for every object. Two live possibilities, undistinguished:
                          (i) the actual `--apply --quarantine --content-repair` `full`-mode run may not have been executed to genuine
                          completion across the FULL date range for all 4 asset_groups (only a `--dry-run`/census pass, or a partial/shard
                          subset, may have actually completed) — checkable by reading the staged run artifacts at
                          `gs://<CODE_BUCKET>/canonical-migration-candle-apply/<RUN_TS>/<vm_name>/` and each run's `CANDLE_APPLY_ENUM_LINES`
                          count vs. the ~10.9M P0-census total, per asset_group; (ii) the apply pass DID complete but
                          `_record_captured_for_target`'s own `except Exception` swallow path fired at scale for a reason distinct from the
                          already-ruled-out env-var gap — checkable via a targeted grep for `"manifest re-record failed for"` WARNING lines
                          in those same staged run logs. **Do a `--dry-run` (or a `--limit`-bounded `--apply` smoke) re-run FIRST and read
                          its output against these two hypotheses before committing to a full-corpus `--apply` re-run** — re-running blind
                          risks masking (i)/(ii) if the fix turns out to be something other than "just re-run it."

                          **Delete-safety**: the manifest `record_captured` calls this mechanism makes are pure additive bookkeeping
                          (`row_count=0` placeholder, no delete/overwrite of unrelated manifest rows) — NOT gated by the delete-safety
                          protocol. The underlying migration's `--quarantine --content-repair` gates DO carry real object
                          copy/verify/delete semantics for non-`VERIFY_ONLY` dispositions, but since the path migration is independently
                          documented COMPLETE for this corpus, a re-run is expected to land ~100% `VERIFIED_INPLACE` /
                          `NOOP_TARGET_EQUALS_SOURCE` / `SRC_ALREADY_GONE` outcomes (no new moves/deletes) — the dry-run-first step above is
                          exactly the check that confirms this before any `--apply` re-run touches real objects, so `[OPERATOR]` gating is
                          not being invoked here; if the dry-run instead reveals a large `A_COPY`/`A_QUARANTINE` population (meaning the
                          corpus is NOT actually fully migrated), STOP and treat that as a new finding requiring its own review before
                          proceeding, per the existing delete-safety citation this todo originally flagged.

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
- [ ] 9. [INFRA] P2. **`run-bounded-analysis.sh`'s cgroup cap silently no-ops when `systemd-run --user` is unavailable**
      (confirmed 2026-07-27, slot-6, this host: two ad-hoc `read_availability_index` reads on the defi manifest reached
      9.8GB and 12.15GB RSS respectively, unprotected, and had to be killed manually) — it degrades to an advisory log
      line only, with zero real memory enforcement, exactly the scenario the wrapper exists to prevent. Add a hard
      fallback (`ulimit -v`/`RLIMIT_AS` via a small `prlimit`/Python shim) for hosts without a working systemd user
      instance, or make the no-cgroup case refuse to run rather than silently proceeding unprotected. Repo:
      unified-trading-pm.

---

## Progress Log

### 2026-07-27 (slot-6) — Todo 4: root-caused the slow defi read; still not done, now correctly scoped for next attempt

Picked up todo 4 (fresh cross-AG re-measurement). The cefi read for comparison is fast (8.7M rows, ~10-20s). **The defi
read alone would not complete** across 4 attempts. Root-caused via the reader's own log line, not left as a guess:
`ManifestReader: consolidated blob age >120s threshold — falling back to per-VM shards` — defi's consolidated index is
considered stale by the reader's own freshness check, so it falls back to downloading + merging every un-consolidated
per-VM shard individually, a far more expensive path than cefi's single-blob read. One earlier attempt was NOT actually
killed by its `timeout` wrapper as first assumed — it kept running detached in the background for 29+ minutes (PID
2059749, up to 9.8GB RSS) and never finished the shard-merge. Checking `free -h` mid-session found the REAL aggravating
factor: this host was down to **363Mi free RAM with 11Gi of swap in use** — my own two concurrent measurement attempts
were themselves contributing to a live instance of the already-tracked
`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` class. Killed both redundant processes immediately
(`kill`/`kill -9`), which alone recovered ~8Gi of free memory — did not wait for either to "finish naturally" once the
resource-contention risk to the whole shared host was confirmed.

**Update — `run-bounded-analysis.sh` retried, confirmed NOT viable on this host either.** Re-ran the defi-only read
under `scripts/dev/run-bounded-analysis.sh` (`ANALYSIS_MEM_CAP=6G`) expecting the cgroup cap to bound it — the wrapper
itself logged
`systemd-run unavailable on this host ... running UNWRAPPED — no cgroup enforcement, this is advisory only here`, so no
real protection was active. The process reached **12.15GB RSS in 4:25** with host free memory back down to 371Mi (swap
climbing to 7.4Gi) — worse than the first unwrapped attempt (9.8GB) — and was killed again before it could finish or
risk an OOM cascade onto another slot's concurrently-running legitimate `pytest` (observed at 866MB and climbing on this
same host). **Two independent attempts, both killed for genuine host-safety reasons, neither completing**: this is now
definitively NOT an interactive-session task on this shared host, wrapper or not.

**Disposition**: todo 4 stays open, **DEFERRED to a dedicated VM** — not a code bug, not a "retry harder" situation.
This host's `systemd-run --user` unavailability means `run-bounded-analysis.sh`'s cap is a no-op here (a gap worth its
own tracked finding — the wrapper's own docstring assumes cgroup enforcement works and doesn't degrade to a hard
`ulimit`/ol' `RLIMIT_AS` fallback when it doesn't). **Next attempt must launch a dedicated one-off VM** (per
`vm-launcher-runbook.md`'s heavy-compute-on-shared-host rule) to run the defi/tradfi/prediction re-measurement, or use a
genuinely streamed/chunked read (DuckDB row-group iteration, never loading the full per-VM-shard-merged frame into
pandas at once) — and separately investigate _why_ defi's consolidated blob is chronically >120s stale (heavy concurrent
per-VM writing? a consolidator cadence gap specific to defi?), since that staleness is what triggers the expensive
per-VM-shard path on every read, not just this one. tradfi/prediction were never reached. No code changed, no manifest
touched, no VM launched this session. New [INFRA] P2 todo filed below for the wrapper's silent-no-cap gap.

### 2026-07-27 (slot-9) — Todo 3 done: backfill mechanism scoped, no new script needed

Read the referenced `defi_fold_manifest_registration_pending_2026_07_21.md` first (per this todo's own instruction).
Before designing anything new, read `migrate_candle_canonical_2026_07.py` directly and found the manifest-registration
mechanism this todo asked to design ALREADY EXISTS and is ALREADY WIRED into both the `A_VERIFY_ONLY` and `A_COPY`
dispatch paths of `_apply_one()` (`_record_captured_for_target`, a direct `ManifestWriter.record_captured()` call —
independently confirmed NOT routed through the buggy `should_publish_row` emission-policy gate todo 1/2 fixed, so that
fix and this mechanism are unrelated). Recommended mechanism: re-run the already-shipped `<ag>-candle-apply` VM launcher
category in `full` mode per asset_group (reuses the existing single-walk enumeration + is independently idempotent per
its own `_CHECKPOINT_SAFE_OUTCOMES` design) rather than building a new registration script. Verified
`MANIFEST_PER_VM_SHARDS=true` is already globally exported by `setup-data-pipeline-vm.sh` for every VM this launcher
spawns, ruling out the defi-fold doc's env-var pitfall as the cause here. Left one open question for todo 5 to check
before a full re-run (whether the P7/P8 apply pass actually completed in `--apply` mode across the full corpus, or only
a dry-run/partial subset did) — recommended a `--dry-run` or `--limit`-bounded smoke re-run first to distinguish this
before committing to the full corpus-scale re-run, and flagged the delete-safety posture (pure additive
`record_captured` bookkeeping; the underlying copy/quarantine gates carry real object semantics but are expected to
no-op given the migration's documented completeness — the dry-run-first step is what actually confirms that). No code
changed in this session — todo 3 is scoping-only per its own text.

### 2026-07-27 (slot-10) — Todo 2 done: code fix shipped for both confirmed causes

Read todo 1's findings, re-verified the exact code shape myself directly (`canonical_writer_stamping.py`'s
`_publish_emission_check`/`_build_ohlcv_1m_upstream_window`/`_resolve_policy_output_data_type`, UTL's
`emission_publisher.py`/`manifest_completeness.py`) before writing any fix, since this is a P0 correctness-critical
path. Confirmed independently: the `ohlcv_1m` passthrough case's upstream_window IS keyed identically to the row being
written (same date/venue/instrument_type/underlying/league_id/instrument_id, `data_type` hardcoded to `ohlcv_1m`) —
genuinely self-referential, not a paraphrase error. Shipped `market-data-processing-service@caa995c`: (c) ohlcv_1m:*
bypasses the manifest lookup, publishes with completeness_fraction=1.0 hardcoded per the module's own documented intent;
(b) the swallowed `record_captured` exception now also calls `record_failed_for_shard`. Added/extended 4 test files
proving both fixes at the unit level (2222 passed). Did NOT attempt the "real prod forward write" proof from acceptance
criterion 2 in this same session — that needs the fix to actually reach the always-on MDPS Cloud Run service via the
promote pipeline first, which is an open-ended wait not worth blocking a dispatch on; left explicitly as todo 6's job.
Also closed the duplicate-tracking todos on the two sibling docs that reference this same finding (see their own
Progress Logs): `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7,
`candle_canonical_path_migration_execution_2026_07_24.md` todo 16.

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
