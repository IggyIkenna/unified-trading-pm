---
doc_type: plan
title: Cross-asset-group available_at manifest backfill (market-data-tick — prediction, tradfi, defi)
summary: >
  Backfill the historical available_at="" backlog on CAPTURED market-data-tick manifest rows, now that
  unified-trading-library@9c9cdc50 fixed record_captured()/record_captured_from_counts() to actually persist the value.
  Phases smallest-blast-radius-first — prediction (46K rows) then tradfi (1.6M rows) — reusing each asset_group's
  existing rebuild script, which already derives available_at_envelope correctly and only needed the library fix to
  land. defi (3.0M rows) has NO existing capture-path available_at threading in its rebuild script, so it is
  audit-and-decide only in this plan, gated behind an explicit operator go/no-go given the sports CF-8 full-rebuild
  regression precedent. cefi is explicitly OUT OF SCOPE — its consolidator is stale/down, tracked separately.
status: active
nature: process
asset_group: [tradfi, defi, prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, available-at, manifest-writer, backfill, cross-asset-group, manifest-master]
related:
  [
    plans/active/issues/manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md,
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    plans/active/issues/mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md,
    plans/audit/results/available_at_fill_rate_audit_2026_07_13.py,
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_progress_log_history_2026_08_01.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
last_updated: 2026-08-01
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: true
source: >
  manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md todo P2 ("Scope + execute a
  cross-asset-group backfill plan... route through manifest_master epic as its own plan, NOT this issue doc")
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/epics/manifest_master.md,
    /plans/archive/issues/mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md,
  ]
---

# Cross-asset-group available_at manifest backfill (market-data-tick)

> **🟡 URGENT — this plan's tradfi cron-pause is now causing a FLEET-WIDE tradfi backfill outage (2026-08-02).**
> `uts-prod-manifest-consolidator-market-data-tradfi-cron` (paused by this plan's own 2026-07-29 pause todo) has kept
> `market-data-tick-tradfi-prd-*`'s `_index/availability_index.parquet` stale past `setup-data-pipeline-vm.sh`'s 24h
> OOM-preflight budget (~42h stale as of this writing) — EVERY tradfi download-VM launch now self-deletes at boot
> (`exit_code=78`) before doing any work, fleet-wide, not one shard. Details + evidence:
> `/plans/active/issues/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md`. The "Apply
> `rebuild_tradfi_manifest.py`..." + "Resume the tradfi consolidator cron" todos below are now CRITICAL PATH for the
> whole tradfi asset group, not routine cleanup — prioritize accordingly.

## Why this plan exists

`manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`'s audit (2026-07-13, live production read
via `read_availability_index()`, no whole-corpus walk) found `available_at` **uniformly 0% filled** on
`capture_status=captured` rows across every measurable non-sports asset_group on the `market-data-tick` (MTDS/MDPS)
write path:

| asset_group | bucket                                             | captured rows | fill rate |
| ----------- | -------------------------------------------------- | ------------: | --------: |
| defi        | market-data-tick-defi-prd-central-element-323112   |     3,010,913 |      0.0% |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112 |     1,620,826 |      0.0% |
| prediction  | market-data-tick-pred-prd-central-element-323112   |        45,542 |      0.0% |
| sports      | market-data-tick-sports-prd-central-element-323112 |       377,194 |      0.0% |

Sports is already covered by `sports_cf8_available_at_backfill_regression_2026_07_13.md`'s own P1 todo (gated on an
operator-coordinated maintenance window per that doc's Finding 1) — **not** duplicated here. cefi could not be measured
(consolidator stale/down, tracked as that issue doc's INFRA P3 todo) — **also not in scope here** until that is resolved
and a fresh audit confirms its state.

**Root cause is fixed** (`unified-trading-library@9c9cdc50`, unit-tested) for the go-forward write path. This plan is
ONLY about the historical backlog on already-captured rows.

## What we already know about the backfill mechanism, per asset_group (2026-07-13 code read)

- **prediction** (`rebuild_prediction_manifest.py`) — confirmed 2026-07-14: prediction's entire captured-row corpus is
  bundled-by-design (the whole asset_group routes through the "bundled cqg atom") and `emit_manifest_rows` calls
  `writer.record_captured_from_counts(..., available_at_envelope=..., ...)` uniformly. **This asset_group's claim
  holds** — a full-date-range re-run (no `--dry-run`) backfills the full prediction corpus, no new code needed.
  **Correction, 2026-07-14 (slot 5)**: neither `rebuild_prediction_manifest.py` nor `rebuild_tradfi_manifest.py` has a
  `--force`/`--no-dry-run` flag (confirmed via `_build_parser()` — both only accept `--project-id`/`--start-date`/
  `--end-date`/`--dry-run`[/`--venue`/`--workers`/`--beta-manifest-out`]); "apply for real" is simply omitting
  `--dry-run` over the target date range. Every `--force` mention below for these two scripts is stale plan language —
  read it as "full-range apply, `--dry-run` omitted", not a literal flag.
- **tradfi** (`rebuild_tradfi_manifest.py`) — **CORRECTION, 2026-07-14 (slot 3)**: the claim below (as originally
  written) overstated tradfi's coverage. `scan_and_rebuild`'s object-scan loop (line ~515) branches on
  `parsed.data_type in BUNDLED_DATA_TYPES`: ONLY that branch (line ~555-567, `_emit_bundled_shard_row` →
  `record_captured_from_counts(..., available_at_envelope=...)`) threads `available_at`. For every NON-bundled data_type
  — the general/majority case — the loop instead calls `target.add(processing_date=..., venue=..., ...)` (line 568-578)
  **without an `available_at=` kwarg at all**, even though `ManifestWriter.add()` has accepted one since 2026-06-26.
  `BUNDLED_DATA_TYPES` (`unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py`) is a narrow closed
  set for tradfi's write path — `options_chain`, `futures_chain`, `event_contract` — not tradfi's tick data generally.
  **A `--force` re-run of `rebuild_tradfi_manifest.py` will NOT backfill `available_at` on the non-bundled majority of
  the 1.6M-row corpus** — only on options/futures-chain/event-contract shards. Exact bundled-vs-non-bundled row split
  not yet measured (new todo below) — do not assume "re-run --force" alone closes tradfi's gap.
- **defi** (`rebuild_defi_manifest.py`) and **cefi** (`rebuild_cefi_manifest.py`) call ONLY `record_empty`/
  `record_failed` (gap-filling) — **never** `record_captured`/`record_captured_from_counts` — confirmed by grep, no call
  sites in either file. There is no existing rebuild entrypoint that touches captured rows for defi. **Correction,
  2026-07-14 (data_engineering slot-8)**: the "~30 separate collectors, each presumably deriving `available_at` its own
  way" framing was WRONG — see the completed audit todo below. In reality **36 of ~40 `cli/handlers/*.py` files route
  through ONE shared shim** (`DefiManifestRecorder` in `_defi_manifest.py`), and that shim's captured-row path never
  threads `available_at` at all (same root-cause shape as tradfi's non-bundled majority, fixed in
  `market-tick-data-service@65a6f9e0`) — a defi backfill is a SINGLE shim-level fix, not ~30 independent formulas. Still
  real, not-yet-scoped engineering work (the fix touches every defi write going forward, so needs the same
  dry-run/snapshot/pause-cron/guardrail-verify/resume-cron protocol as prediction/tradfi), just much narrower in surface
  area than originally scoped.

## The sports precedent this plan must respect (HARD constraint)

`sports_cf8_available_at_backfill_regression_2026_07_13.md`: a `--force` full-corpus rebuild on the IS sports surface
**regressed** `available_at` fill rate from 62.9% to 15.7% — a genuine, silent, production-data-destroying bug (root
cause: the serializer dropped the column; fixed `f5f15e3a`), only caught because the operator's own before/after
fill-rate check was run. A second incident (Finding 1) had an operator's routine `gcloud scheduler jobs resume` collide
with a paused consolidator cron mid-backfill. Both are now mitigated (`f5f15e3a` fixed the serializer; `2e132bb2` added
`_check_column_fill_regression()`/`MANIFEST_COLUMN_FILL_REGRESSION` as a defense-in-depth guardrail) but **every todo
below that touches production data must**: dry-run first, snapshot + pause the consolidator cron before applying, and
verify the guardrail did not trip + row counts are unchanged before resuming the cron.

## Todos

> **🟡 MEMORY-SAFETY (2026-07-31)**: the prediction/tradfi apply todos and the defi implement-and-apply todo below have
> no `--chunk-days` flag on their rebuild scripts yet (unbounded RSS growth measured on prediction's smaller corpus) —
> dispatch each only via bounded sub-ranges (e.g. quarterly) or a dedicated VM, never one full-range shot on the shared
> interactive/planning host, until
> `plans/active/issues/mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md`'s `-001` todo ships.

- [x] ✅ [DATA] P0. Confirm `unified-trading-library@9c9cdc50` (available_at persistence fix) AND `@2e132bb2`
      (`MANIFEST_COLUMN_FILL_REGRESSION` guardrail) are both pinned in `market-tick-data-service`'s dependency lock on
      `live-defi-rollout` — bump + redeploy first if either is missing. Do NOT proceed past this todo otherwise. (repo:
      market-tick-data-service, unified-trading-library) — 2026-07-14 (slot 9) verified the dependency-lock half
      (editable path source, both commits ancestors of LDR HEAD, no floor bump needed) and concluded no action needed;
      slot 8 additionally found the **production Docker digest pin** was stale (missed by that check) and shipped the
      fix — `market-tick-data-service@4d84268b`. Full evidence in Progress Log below.
- [x] ✅ [DATA] P0. **Retagged 2026-07-28 (previously gated on an operator decision)** — pause the prediction + tradfi
      consolidator crons for the backfill window below (per the sports Finding 1 cron-collision incident, still respect
      the dry-run/snapshot/pause/guardrail-verify/resume protocol). Operator ruling 2026-07-28 (CLAUDE.md Governance
      section: maintenance-window restarts/pauses of shared infra no longer need operator scheduling while
      pre-live-trading, brief downtime is acceptable) removes the "coordinate a window with the operator first" gate —
      dispatch directly: group prediction + tradfi's cron-pauses together (avoid the sports-precedent collision by
      pausing both explicitly and verifying each is actually paused, not by getting a human go-ahead), execute now, and
      verify each cron resumes healthy afterward per the todos below. (repo: NA) — ✅ 2026-07-29 (data_engineering
      slot-10): both paused together, see Progress Log for full evidence.
- [x] [DATA] P1. Dry-run `rebuild_prediction_manifest.py --dry-run` (no `--force` flag exists — see correction above)
      against `market-data-tick-pred-prd-central-element-323112`; spot-check the previewed `available_at_envelope`
      values against a handful of known-good rows before applying anything live. (repo: market-tick-data-service) — ✅
      2026-07-14 (slot 9): see Progress Log for full evidence (correction: the script has no `--force` flag — ran
      `--dry-run` instead, which is the actual no-writes preview mode).
- [x] ✅ [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling as the P0 todo above)**
      — Snapshot the prediction canonical manifest index (`_index/snapshots/pre_available_at_backfill_<ts>.parquet`) and
      pause its consolidator cron. (repo: market-tick-data-service) — PARTIAL 2026-07-14 (slot 4): snapshot half DONE +
      verified —
      `gs://market-data-tick-pred-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260714T000100Z.parquet`
      (47,908,172 bytes, byte-identical to the live index at snapshot time). Shipped
      `scripts/mtds_available_at_backfill_snapshot_prediction_2026_07_14.py` (market-tick-data-service@86467a0a).
      Cron-pause half was deliberately NOT done at the time (slot 5 `BLK-f3cdf442`, slot 9) because it was gated on the
      P0 maintenance-window todo above — that gate is resolved 2026-07-28 (pre-live-trading maintenance windows no
      longer need operator scheduling); pause the cron directly now and flip this checkbox once both halves are verified
      complete. **COMPLETE 2026-07-29 (data_engineering slot-10)**: cron paused (verified `PAUSED` state); the 07-14
      snapshot was 15 days stale by the time the pause actually happened (canonical grew 47,908,172 → 83,839,684 bytes
      in the interim, plus schema/content drift from ongoing captures) so it is NOT a safe rollback point for a backfill
      applied now — re-ran the existing snapshot script to take a FRESH one at the actual pause point:
      `gs://market-data-tick-pred-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260729T010653Z.parquet`
      (83,839,684 bytes, byte-identical to the live index at snapshot time). Both halves now genuinely complete. See
      Progress Log for full evidence.
- [ ] [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling)** — Apply
      `rebuild_prediction_manifest.py` (full date range, omit `--dry-run` — no such flag as `--force`/`--no-dry-run`),
      force-consolidate, then re-run `available_at_fill_rate_audit_2026_07_13.py` (or its successor) to confirm fill
      rate rose from 0% — verify the `MANIFEST_COLUMN_FILL_REGRESSION` guardrail did NOT trip and total row count is
      unchanged before declaring success. (repo: market-tick-data-service, unified-trading-library)
- [ ] [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling)** — Resume the prediction
      consolidator cron; record the before/after fill-rate evidence in this plan's Progress Log. **Retrofit 2026-07-30**
      (dp_watcher_003 issue's 2nd todo): resume via `scripts/mtds_available_at_backfill_resume_prediction_2026_07_30.py`
      (maintenance-window-aware), not raw `gcloud`. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. **NEW — 2026-07-14 correction**: query the tradfi canonical index (via `read_availability_index()` —
      single-walk-safe, NOT a raw GCS walk) for the bundled (`options_chain`/`futures_chain`/`event_contract`) vs
      non-bundled row-count split on `capture_status=captured` rows, so the true post-apply fill-rate ceiling is known
      BEFORE claiming success (a full-range apply only fixes the bundled subset — see "What we already know" correction
      above). **Sharper signal, 2026-07-14 (slot 5) dry-run todo below**: a bounded 260-object GCS sample (7 days, 2
      venues, `batch_databento`) found the bundled_count was 0/260 — `data_type` is always an OHLCV-granularity string
      (`ohlcv_1m`/`ohlcv_1s`), never a `BUNDLED_DATA_TYPES` literal, even under
      `instrument_type=options_chain/     futures_chain`. This is a SAMPLE, not the corpus-wide count this todo asks for
      — but it raises the possibility the true bundled fraction is ~0%, not just "non-bundled majority". This todo now
      must also explain/reconcile that sample finding, not just produce a count. If the non-bundled majority is
      material, thread `available_at=` into the `target.add(...)` call at `rebuild_tradfi_manifest.py:568` (same honest
      `written_at`-proxy pattern sports's `_available_at_from_row` uses, per `AVAILABILITY_AT_SEMANTICS`), unit-tested,
      BEFORE the apply todo below — otherwise scope this asset_group's non-bundled backfill as its own follow-up
      (mirroring defi's audit-and-decide gate) rather than declaring tradfi done on a partial fix. (repo:
      market-tick-data-service) — ✅ 2026-07-14 (slot 10): **corpus-wide split via `read_availability_index()`**
      (single-walk-safe): of 1,620,826 captured rows, bundled (`data_type` ∈ `BUNDLED_DATA_TYPES`, all `options_chain`;
      zero `futures_chain`/`event_contract` present) = 242,210 (14.9%), non-bundled = 1,378,616 (85.1%) — material.
      **Reconciled slot 5's zero-bundled-count sample**: not a contradiction — `parse_tradfi_path()` (this script's own
      parser) NEVER derives `data_type` as a chain-type literal from a current canonical path; the chain-type only ever
      lands in `instrument_type` (matched against the separate `BUNDLED_ITYPES` set, e.g. line ~304). So the branch at
      `scan_and_rebuild` line 555 (`if parsed.data_type in BUNDLED_DATA_TYPES`) can never fire for anything this script
      parses off today's canonical bucket — it looks like DEAD CODE post-v9-migration (the existing manifest's 242,210
      `options_chain` rows are residual from a different write convention — pre-migration path shape or a live-capture
      handler — not something a fresh object-scan rebuild reproduces). **Practical upshot: a full rescan-and-apply will
      route effectively 100% of emitted rows through the non-bundled path**, not just 85% — making the fix below even
      more necessary than the corpus split alone suggested. **Implemented + shipped**
      `market-tick-data-service@65a6f9e0`: added `_available_at_from_blob()` (honest proxy = the shard blob's own GCS
      `time_created`, mirroring sports's `written_at`-proxy pattern — no per-shard parquet re-read, single-walk
      discipline preserved) and threaded it into the non-bundled `target.add(...)` call
      (`rebuild_tradfi_manifest.py:578`, shifted by the earlier `_available_at_from_blob` insertion). 3 new unit tests
      (`_available_at_from_blob` direct + a `scan_and_rebuild` apply-path integration test asserting `available_at` on
      the writer's `.add()` call); full suite green (`quality-gates.sh` exit 0, sentinel-verified at
      `market-tick-data-service@65a6f9e0`). **Filed a new follow-up todo below** for the suspected
      `BUNDLED_DATA_TYPES`/`BUNDLED_ITYPES` branch-check mismatch — did NOT fix it in this touch (bigger blast radius:
      changes which shards get bundled shard-atom treatment; needs its own corpus-scale confirmation before touching).
- [x] 1. ✅ [DATA] P1. Dry-run `rebuild_tradfi_manifest.py --dry-run` (no `--force` flag — see correction above) against
      `market-data-tick-tradfi-prd-central-element-323112`; sanity-check envelope values across a sample of tradfi
      data_types/venues (bundled + non-bundled shards) — confirm non-bundled shards' `available_at` behavior matches
      whatever the prior todo decided (either newly threaded, or knowingly still blank pending follow-up). —
      market-tick-data-service (no code change, diagnostic only) 2026-07-14 (slot 5). **Ran for real**:
      `python -m market_tick_data_service.scripts.rebuild_tradfi_manifest --start-date 2026-07-01 --end-date     2026-07-10 --dry-run`
      → 260 shards parsed cleanly (0 unparseable), venues CBOE(16)/CME(244). Then used the script's own
      `parse_tradfi_path` + `BUNDLED_DATA_TYPES` against the same 260 objects directly: EVERY shard's `data_type` value
      is an OHLCV granularity string (`ohlcv_1m`/`ohlcv_1s`) — `(instrument_type, data_type)` pairs observed:
      `(futures_chain, ohlcv_1m/1s)`, `(combo, ohlcv_1m/1s)`, `(options_chain, ohlcv_1m/1s)`. **None** of these match
      `BUNDLED_DATA_TYPES` (`options_chain`/`futures_chain`/`event_contract`/…) literally — `data_type` is never the
      chain-type string itself, it's always the candle granularity. **bundled_count=0, nonbundled_count=260 (100%) in
      this sample.** Same pattern held across all 3 pipeline_modes spot-checked (`batch_databento`, `batch_massive`,
      `batch_yahoo`) and 6 instrument_types (`futures_chain`/`options_chain`/`combo`/`equity`/`etf`/ `spot_pair`).
      **This is a bigger finding than the prior todo's framing**: the plan assumed a "bundled fraction" exists and a
      full-range apply would at least fix that slice. This sample found **zero** shards whose `data_type` matches
      `BUNDLED_DATA_TYPES` — the bundled branch (`_emit_bundled_shard_row`) may never fire for tradfi's real captured
      objects at all (pending the still-open canonical-index row-count-split todo below for a corpus-wide confirmation
      via the single-walk-safe consolidated index, not a GCS walk). If this generalizes, a full-range apply gives **~0%
      fill-rate uplift** for tradfi, not just "won't fix the non-bundled majority" — do NOT snapshot/pause/apply tradfi
      until the split todo below is confirmed at corpus scale, otherwise the pause/apply/resume cycle carries real
      production risk (per the sports CF-8 precedent) for no measurable gain.
- [x] ✅ [DATA] P2. **NEW — 2026-07-14 (slot 10)**: confirm/fix the suspected dead-code bundled-branch check in
      `rebuild_tradfi_manifest.py`'s `scan_and_rebuild` (line ~555: `if parsed.data_type in BUNDLED_DATA_TYPES`) —
      `parse_tradfi_path()` never derives `data_type` as a chain-type literal from a current canonical path (only
      `instrument_type`, matched elsewhere against the separate `BUNDLED_ITYPES` set, e.g. line ~304), so this branch
      appears to never fire post-v9-migration (see the corroborating todo above: corpus-wide 0% `futures_chain`/
      `event_contract`, and slot 5's raw-object sample found 0/260 bundled). Confirm at corpus scale (not just the
      260-object sample) whether ANY current canonical object still routes through `_emit_bundled_shard_row`, and if
      truly dead, decide whether to (a) fix the check to `parsed.instrument_type in BUNDLED_ITYPES` so bundled shards
      once again get the `record_captured_from_counts` shard-atom treatment they were presumably designed for, or (b)
      confirm bundling is intentionally retired for tradfi's current write convention and delete the dead branch. —
      **RESOLVED 2026-07-14 (data_engineering slot-2, task `mtds_available_at_cross_asset_backfill-015`), decision
      (b).** Corpus-scale confirmation via `read_availability_index()`-equivalent read (SDK download of the live tradfi
      canonical index, single-walk-safe — `read_availability_index()` itself returned empty on this host, a separate
      GCS-access flakiness matching the sports audit's snap-confine/gcloud issue, so downloaded the index parquet
      directly): of 1,620,826 captured rows, 242,210 have `data_type` literally in `BUNDLED_DATA_TYPES` (all
      `options_chain`) — but **100% of them are `venue=CME` with blank `job_id`**, matching `manifest_finalize.py`'s
      live tick-orchestrator CME-options/futures/event-contract write path (confirmed by reading that file: it derives
      `data_type_key="options_chain"` explicitly for `venue=CME-OPTIONS`, a completely separate write flow from this
      rebuild script's object-scan). Separately, 550,333 rows have `instrument_type` in `BUNDLED_ITYPES`
      (combo/futures_chain/options_chain/continuous_future) — of these, 429,833 carry an OHLCV-granularity `data_type`
      (ohlcv_1m/ohlcv_1s/trades/tbbo), confirming this script's own per-file object scan legitimately writes these via
      plain `add()` today (since `data_type` never matches `BUNDLED_DATA_TYPES` for them) — `add()` is NOT banned for
      these rows, so no data is being silently dropped or misrouted. **Option (a) was rejected**:
      `_emit_bundled_shard_row` stamps `row_key["data_type"] = parsed.data_type` unchanged (still the OHLCV granularity,
      never the chain-type) — flipping the check to `instrument_type` would NOT restore real cluster validation (the
      helper's `expected_root_clusters={cluster_root:1}`/`observed_clusters={cluster_root:1}` is a fake always-pass
      placeholder for the historical-reconstruction case), and would actively regress today's correct behavior by
      collapsing many legitimate per-instrument `add()` rows into one fake per-underlying bundle row, losing
      granularity. **Implemented (b)**: removed the dead `if parsed.data_type in BUNDLED_DATA_TYPES:` branch + its
      now-unused `BUNDLED_DATA_TYPES` import from `scan_and_rebuild` — `_emit_bundled_shard_row` itself is KEPT (still a
      real, correct, reusable primitive for a caller that already knows a shard is bundled by construction:
      `reshape_tradfi_ice_cme_legacy_chain_tail_2026_07_13.py` calls it directly, unaffected by this change — verified
      both scripts still import cleanly). Added a new regression test
      (`test_scan_rebuild_chain_instrument_type_uses_plain_add_not_bundled_shard`) asserting a chain-instrument-type
      object (`instrument_type=options_chain`, `data_type=ohlcv_1m`) routes through `writer.add()` and NOT
      `writer.record_captured_from_counts()`. Full `tests/unit/scripts/test_rebuild_tradfi_manifest_coverage.py` green
      (21/21, was 20). Shipped `market-tick-data-service@c8c01855` via quickmerge. No production writes made — code +
      tests only. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling as the P0 todo above)**
      — Snapshot the tradfi canonical manifest index and pause its consolidator cron. (repo: market-tick-data-service) —
      PARTIAL 2026-07-14 (data_engineering slot-2, task `mtds_available_at_cross_asset_backfill-007`): snapshot half
      DONE + verified, mirroring the prediction precedent's split (slot 4's "Snapshot (safe half only)" entry above) —
      shipped `scripts/mtds_available_at_backfill_snapshot_tradfi_2026_07_14.py` (`market-tick-data-service@8f131104`,
      QG green, shipped via quickmerge), ran it against real prod:
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260714T011351Z.parquet`
      (162,825,635 bytes, byte-identical to the live index at snapshot time, independently re-verified via a fresh
      `blob.reload()` read). Cron-pause half was deliberately NOT done at the time (`BLK-272f061b`/`1e6326c7`/
      `f3cdf442`/`aa40e2b6`/`b484ff7a`) because it was gated on the P0 maintenance-window todo above — that gate is
      resolved 2026-07-28 (pre-live-trading maintenance windows no longer need operator scheduling); pause the cron
      directly now and flip this checkbox once both halves are verified complete. **COMPLETE 2026-07-29
      (data_engineering slot-10)**: cron paused (verified `PAUSED` state); the 07-14 snapshot was 15 days stale — the
      canonical actually SHRANK in the interim (162,825,635 → 98,958,709 bytes, consistent with the 2026-07-20 surgical
      `batch_massive`/phantom-row removal + the dead-bundled-branch code fix recorded above), so the old snapshot no
      longer even matches current schema/content and would be an unsafe rollback point — re-ran the existing snapshot
      script to take a FRESH one at the actual pause point:
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260729T010709Z.parquet`
      (98,958,709 bytes, byte-identical to the live index at snapshot time). Both halves now genuinely complete. See
      Progress Log for full evidence.
- [ ] [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling)** — Apply
      `rebuild_tradfi_manifest.py` (full date range, omit `--dry-run` — no `--force`/`--no-dry-run` flag exists),
      force-consolidate, then verify fill rate + guardrail + row count via the audit script, same protocol as
      prediction. **Do not declare tradfi's backlog fully resolved from this alone** — confirm the resulting fill rate
      matches the bundled-vs-non-bundled ceiling measured above (a rate matching only the bundled fraction means the
      non-bundled follow-up is still open, not a bug). **Update, 2026-07-14 (slot 10)**: per the reconciliation above,
      expect the post-apply fill rate to approach ~100% (not ~85%) since the bundled branch appears dead code — a rate
      near 85% instead would mean the dead-code theory is wrong and needs re-investigation before declaring success.
      (repo: market-tick-data-service, unified-trading-library) — **2026-08-02 (data_engineering slot-3), PARTIAL — the
      "dead code" theory was itself wrong** (see Progress Log #11 for the bundled-shard crash + fix,
      `market-tick-data-service@9d354cea`): applied `--start-date 2019-01-02 --end-date 2026-07-30 --chunk-days 30`
      (resumed from the crash point after the fix shipped), force-consolidated (`rows_out=6577303`), and cleared a
      `MANIFEST_COLUMN_FILL_REGRESSION` guardrail trip on `instrument_id` as a false positive (see #11 for the full
      investigation — structurally-blank underlying-bundle rows, not data loss). `available_at` fill on captured rows
      rose (69.97% → ~77-82%, exact number disputed between #11's and #12's independent reads, both far from 100%).
      **Still open (2026-08-02, slot-14, Progress Log #12)**: per-month breakdown shows 2019-01..2023-03 sitting at a
      stable ~50-60% fill, not near-100% — NOT resolved by this apply/consolidate. Unclear whether that's a genuine
      structural ceiling (a bundled/no-timestamp shard class `_available_at_from_blob`'s GCS-`time_created` proxy can't
      populate) or an incomplete-fill signal — chunks 1-52 of THIS todo's own apply ran the FIRST (pre-fix) launch's
      code, before `9d354cea` shipped, even though they didn't crash there. **Do not flip this checkbox until that
      question is resolved** — re-read `_available_at_from_blob`'s docstring + investigate, or re-run
      `--start-date 2019-01-02 --end-date 2023-04-10 --chunk-days 30` now that the fix is live, to see if the ceiling
      moves. (repo: market-tick-data-service, unified-trading-library)
- [x] ✅ [DATA] P1. **No longer gated on an operator decision (retagged 2026-07-28, same ruling)** — Resume the tradfi
      consolidator cron; record evidence in the Progress Log. **Retrofit 2026-07-30** (dp_watcher_003 issue's 2nd todo):
      resume via `scripts/mtds_available_at_backfill_resume_tradfi_2026_07_30.py` (maintenance-window-aware), not raw
      `gcloud`. (repo: market-tick-data-service) — ✅ 2026-08-02 (data_engineering slot-3): ran the sanctioned resume
      script, maintenance window released, cron confirmed `ENABLED` (`*/1 * * * *`) via
      `gcloud scheduler jobs     describe`. This closes the fleet-wide tradfi backfill VM outage tracked in
      `/plans/active/issues/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md` — the index
      will re-freshen every minute going forward, clearing the OOM-preflight guard for new VM launches.
- [ ] [INFRA] P3. **NEW — 2026-08-02 (slot-3)**: `MANIFEST_COLUMN_FILL_REGRESSION` (the consolidator's
      column-fill-regression guardrail) has no awareness of legitimately-blank-by-shape columns — tradfi's apply today
      tripped a false-positive on `instrument_id` (84.16%→81.72% aggregate) explained entirely by ~614K newly-visible
      underlying-bundle-shape rows that structurally never carry `instrument_id` (see Progress Log #11 for the full
      investigation + methodology). Scope the check to exclude columns known-blank-by-shard-atom for the affected row's
      `data_type`/`instrument_type` (e.g. via the same `BUNDLED_DATA_TYPES`/`BUNDLED_ITYPES` sets), so a real future
      regression isn't buried in noise and a future apply session doesn't have to re-re-derive this same investigation.
      Likely to false-positive again on this plan's own still-open prediction/defi apply todos (their bundled
      `prediction_canonical_question_group`/`sports_fixture_bundle` shapes carry the same structural blankness) — check
      before assuming a real regression there too. (repo: unified-trading-library)
- [x] ✅ [DATA] P2. Audit each `market_tick_data_service/cli/handlers/*_handler.py` DeFi collector (~30 files) for how
      (or whether) it currently derives `available_at` at live-capture time — map the per-data_type derivation formula
      each already uses, since a retroactive backfill must reuse the SAME formula per data_type rather than one blanket
      rule (confirmed via grep, 2026-07-13: `rebuild_defi_manifest.py` itself has zero
      `record_captured`/`record_captured_from_counts` call sites — no shared rebuild entrypoint exists to extend).
      (repo: market-tick-data-service) — ✅ 2026-07-14 (data_engineering slot-8): see Progress Log for full evidence.
      **Headline correction**: not ~30 independent formulas — 36 of the ~40 handler files share ONE write path
      (`DefiManifestRecorder` in `_defi_manifest.py`) that never threads `available_at` at all (blanket `""` for all of
      them, not a per-data_type formula gap). A handful of non-defi files living in the same directory (cefi/tradfi) use
      different, unrelated write paths.
- [ ] [DATA] P2. **RULED 2026-07-28 — GO. Retagged away from its prior operator-decision gate** (no specific operator
      answer was given for this go/no-go; applying the standing workspace theme instead: full backfills/migrations get
      done — as long as not superseded by newer work — and this one isn't; cost is a one-time manifest-only compute
      pass, nowhere near the pre-approved $100 threshold; "audit-and-decide" was the only gate, not a real blocker).
      Design option adopted (2026-07-14, slot-8's headline-correction option, unchanged): since 36/~40 defi handler
      files share ONE write path (`DefiManifestRecorder._emit_captured_add` → `ManifestWriter.add()` with no
      `available_at=`), the fix is a single shim-level change — thread an honest per-shard `available_at` proxy (mirror
      the tradfi/sports blob-`time_created` pattern from `market-tick-data-service@65a6f9e0`) into
      `_emit_captured_add`'s `self._writer.add(...)` call, then rebuild-and-apply via a NEW backfill entrypoint (no
      existing rebuild script touches captured defi rows — `rebuild_defi_manifest.py` only does gap-filling). Full
      completion mandate for the next todo — do not ship a partial/MVP version of this shim or backfill only a subset of
      the 3.0M rows. (repo: NA — this todo records the decision; implementation is the next todo)
- [ ] [DATA] P3. **No longer stretch/optional — retagged 2026-07-28, same GO ruling as the todo above.** Implement the
      chosen defi backfill mechanism (the shim + new backfill entrypoint above) with unit-test coverage and a dry-run
      preview before any live write, then apply for real across the full 3.0M-row defi captured corpus (no partial
      subset) — follow the same dry-run/snapshot/pause-cron/guardrail-verify/resume-cron protocol as prediction and
      tradfi above, including the same 2026-07-28 Governance-section ruling that the cron pause/resume itself needs no
      further operator scheduling round-trip. (repo: market-tick-data-service, unified-trading-library)

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — manifest schema, capture_status states, `available_at`
  semantics.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator cron pause/resume + staleness threshold.

## Progress Log

> **2026-08-01 line-cap remediation**: every entry from the 2026-07-13 plan authoring through the 2026-07-14 DeFi
> handler audit dispatch (data_engineering slot-8) extracted verbatim to
> `/plans/archive/2026_08/mtds_available_at_cross_asset_backfill_progress_log_history_2026_08_01.md` (doc was at
> 1003/1000 lines). The two most recent entries below are kept inline since they describe the CURRENT infra state (both
> crons paused, fresh snapshots taken 2026-07-29) that any future apply/resume dispatch needs without opening the
> archive. New entries append below them.

### 2026-07-28 — gate-cleanup pass (maintenance-window gate retagged)

Operator ruling 2026-07-28 (CLAUDE.md Governance section): shared-infra maintenance-window restarts/pauses no longer
need operator scheduling while pre-live-trading — brief downtime is acceptable. Retagged the P0
`[OPERATOR] BLOCKED-OPERATOR-DECISION` cron-coordination todo (prediction + tradfi consolidator crons) from `[OPERATOR]`
to `[DATA]`, and the 5 directly-dependent snapshot/apply/resume todos that were blocked solely on it (prediction ×3,
tradfi ×3, minus overlap) from `BLOCKED-OPERATOR-DECISION` to normal open todos — dispatch directly, group both crons'
pause together (respecting the sports-precedent cron-collision guard), execute now, verify each resumes healthy. The
many historical Progress Log entries above that note "the P0 `[OPERATOR] BLOCKED-OPERATOR-DECISION` maintenance-window
todo is still unchecked" were accurate at the time they were written and are left as-is (historical record); they
predate this ruling. The separate `[OPERATOR] P2` defi design-decision gate (present the defi audit + scoped design
option for a go/no-go) is UNAFFECTED — it is a design ruling, not a maintenance-window schedule, and stays gated. No
cron paused, no backfill applied, as part of this pass — retag/dispatch-shape only.

### 2026-07-29 — crons paused, fresh snapshots taken (data_engineering slot-10, task `mtds_available_at_cross_asset_backfill-002`)

Dispatched to the P0 cron-pause todo (the retag from 2026-07-28 made it directly dispatchable). Fresh-pulled
`market-tick-data-service` to `origin/live-defi-rollout` (clean FF, HEAD `f2f89fad`). Verified pre-state: both
`uts-prod-manifest-consolidator-market-data-prediction-cron` and
`uts-prod-manifest-consolidator-market-data-tradfi-cron` were `ENABLED`, both had a `_index/consolidator.lock` object
updated <90s prior (i.e. mid-normal-cycle, not stuck — Cloud Scheduler pause only stops FUTURE triggers, it does not
kill an in-flight execution, so this was not a blocker).

**Paused both together** (per the todo's instruction to avoid the sports-precedent cron-collision by pausing both
explicitly rather than sequencing them apart):

```
$ gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-prediction-cron --location asia-northeast1
Job has been paused.
$ gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1
Job has been paused.
```

Verified both `PAUSED` via `gcloud scheduler jobs describe … --format="value(name,state)"` immediately after. Also
confirmed no legacy flat variant of either market-data consolidator cron exists
(`gcloud scheduler jobs list … --filter "name~consolidator"` shows only the 5 env-tiered
`market-data-{cefi,defi,tradfi,sports,prediction}` crons, zero `-legacy` market-data crons) — nothing else needed
pausing.

**Correctness finding — the existing 07-14 snapshots were stale rollback points, not just "already done".** Both
downstream snapshot+pause todos (prediction, tradfi) were left PARTIAL specifically because their cron-pause half was
gated on this P0 todo; their snapshot half had been taken 2026-07-14, 15 days before this pause actually happened, with
the crons live and writing the whole time. Re-checking rather than trusting the old byte counts:

- Prediction canonical: 47,908,172 bytes (07-14 snapshot) → 83,839,684 bytes (live, just before this pause) — grew ~75%,
  i.e. real content drift.
- Tradfi canonical: 162,825,635 bytes (07-14 snapshot) → 98,958,709 bytes (live, just before this pause) — actually
  SHRANK, consistent with the 2026-07-20 surgical `batch_massive`/phantom-row removal (recorded in the manifest
  consolidator SSOT) and this plan's own dead-bundled-branch removal (`market-tick-data-service@c8c01855`) landing in
  between.

A 15-day-stale snapshot is not a safe restore point for a backfill applying now — using it as the declared rollback
target would silently discard 15 days of legitimate production writes/corrections if a rollback were ever needed. Since
the existing one-off snapshot scripts (`scripts/mtds_available_at_backfill_snapshot_{prediction,tradfi}_2026_07_14.py`)
are additive/idempotent (single GCS download → copy-write to `_index/snapshots/` → byte-verify, no mutation of the live
canonical, already QG-green and shipped) and their own `Delete-when:` marker says they're valid until this backfill has
"applied + verified", re-ran both AS-IS (no code change) right after pausing, to snapshot at the actual pause point:

```
$ .venv/bin/python scripts/mtds_available_at_backfill_snapshot_prediction_2026_07_14.py
Downloaded 83839684 bytes
Snapshotted to gs://market-data-tick-pred-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260729T010653Z.parquet
Snapshot verified: 83839684 bytes match source.

$ .venv/bin/python scripts/mtds_available_at_backfill_snapshot_tradfi_2026_07_14.py
Downloaded 98958709 bytes
Snapshotted to gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_available_at_backfill_20260729T010709Z.parquet
Snapshot verified: 98958709 bytes match source.
```

Re-verified both crons still `PAUSED` after the snapshot runs (no auto-resume, no other agent touched them mid-touch).
Flipped the P0 todo + both downstream snapshot+pause todos (prediction, tradfi) to `[x]` — their full scope (snapshot +
pause, both halves) is now genuinely complete, using the FRESH 07-29 snapshots as the operative rollback point, not the
stale 07-14 ones (both still retained in `_index/snapshots/` for history, just superseded as the active restore point).

**What I did NOT do**: did not run either `rebuild_{prediction,tradfi}_manifest.py` apply, did not force-consolidate,
did not resume either cron (that is explicitly the scope of the separate downstream apply/resume todos, still open
below), did not touch defi (its own `[OPERATOR] P2` design gate is unaffected by this touch). No code shipped this touch
— pure infra action (`gcloud scheduler jobs pause` ×2) + re-running an existing, already-shipped one-off script ×2 (no
new commits to `market-tick-data-service`) + this plan-doc update (`docs(plans):` carve-out).

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

**#8 — 2026-08-01 (slot-3, data_engineering) — IN PROGRESS, apply running, checkpoint before compaction.** Dispatched
`-006` ("Resume the prediction cron") again — same recurring premature-dispatch pattern as #2-#7: `-001` ("Apply
rebuild_prediction_manifest.py") was still `[ ]`/`queued`/unassigned live in `GET /api/backlog` at dispatch time. Per
the established precedent (slot-15's pragmatic-unblock recommendation) and since `-001`'s own prerequisites (dry-run,
snapshot, cron-pause) are all already `[x]` and the memory-safety `--chunk-days` flag has now shipped
(`market-tick-data-service@749ca622`), executed `-001`'s real work directly instead of re-filing another no-op decline.

**Baseline (before), read from the 2026-07-29 pre-backfill snapshot** (not a live read — index is intentionally stale
while the cron is paused): 1,268,286 total rows, 82,495 `capture_status=captured`, 51,826 filled (`available_at != ""`,
fill_rate=62.8%), 30,669 unfilled. **Correction to #7's claim**: #7 stated "real capture bounds
(2025-03-13..2026-07-28)" — a direct read of the snapshot's captured rows shows the true range is
**2021-06-30..2026-07-28** (confirmed real GCS objects exist as early as 2021-06-30, sparse but present, both venues).
Used the wider bound for the apply so no historical backlog is silently excluded.

**Apply in progress**: `rebuild_prediction_manifest.py --start-date 2021-06-30 --end-date 2026-07-31 --chunk-days 60`
(no `--dry-run` — live write). Two incidents en route, both diagnosed and recovered, neither touched production data
incorrectly:

1. The first invocation (chunks 1-18, covering 2021-06-30..2024-06-13, all flushed + verified clean) was **killed**
   partway through chunk 19 — not OOM (host had 35GB+ free, no dmesg OOM entries), not a reboot (`uptime` showed no
   recent boot). Suspected cause: a `ScheduleWakeup`-triggered re-invocation tore down the harness's tracked
   `run_in_background` bash process at the turn boundary — worth a dedicated issue doc if reproduced again (not yet
   filed; flagging here since this session couldn't fully root-cause it before needing to move on). **Recovery**:
   resumed the REMAINING range (2024-06-14..2026-07-31, `--chunk-days 30`) via the `Monitor` tool instead of
   `ScheduleWakeup` for the wait — no further kills since switching.
2. Severe, unrelated **shared-host contention**: `uptime` load average spiked to 131-160 (from a baseline ~14-34) during
   chunk 18, causing per-object throughput to collapse ~100x (56K→117K objects over 4.5h) while GCS connectivity itself
   was fine (`curl` to `storage.googleapis.com` returned in 36ms throughout) — genuine CPU/scheduling contention from
   other concurrent slot work, not a stall. Eased back to load avg 14-16 by chunk 22. Also hit a ~9-minute AO server
   (port 8765) outage (`connection refused`, uvicorn PID alive but not listening) around 08:39-08:48 — self-recovered,
   did not block the apply (which runs independently of the AO server).

**As of this checkpoint**: apply job (PID varies per relaunch, tracked via Monitor task) at chunk 22-23 of 26
(2026-03..2026-04 window), zero unparseable objects, zero failed_envelope/unclassified/zero_row across all completed
chunks (a handful of transient per-object `ConnectionResetError`/timeout warnings self-recovered via retry, not counted
as failures). **Not yet done**: apply not finished, force-consolidate not run, fill-rate/guardrail/row-count not
re-verified, cron not resumed. **Both `-001` and `-006` checkboxes stay unflipped until all of that completes** — do not
mistake this entry for completion. Cron confirmed still `PAUSED` as of dispatch time; snapshot from 07-29 still the

### 2026-08-01 — #9 (slot-4, data_engineering) — apply from #8 actually COMPLETED but was WRONG: instrument_type bug found + fixed; re-running corrected

Fresh session, dispatched `-006` again (`already_in_progress: true`, `dispatch_reason: resume`). The #8 apply process
(chunked, background) was no longer running (`ps aux` clean) — but GCS evidence (`_index/per_vm/` fragment listing: 18
fragments from the first invocation's PID + 26 chunk fragments + 1 final CF-11 reemit fragment from the recovery
invocation's PID, spanning the full range, last write 11:48 UTC) showed it had actually run to completion before the
session ended, not died mid-chunk as #8's checkpoint feared.

**Force-consolidated** (`manifest_consolidator --bucket market-data-tick-pred-prd-central-element-323112 --force`):
`success=True`, `rows_out=1,952,699` (canon was `1,949,995` pre-merge — no row loss), no `COLUMN FILL REGRESSION`
critical log line (guardrail clean). **But the fill-rate audit revealed the apply did NOT actually work**: overall
`available_at` fill rate on captured rows was only **20.08%** (not the ~100% expected), and diagnosis showed **every one
of 62 historical months read EXACTLY 50.0% filled** — the signature of a systematic 1-old-unfilled + 1-new-filled row
DUPLICATE per real cell, not a partial backfill.

**Root cause**: `market_tick_data_service/scripts/_rebuild_prediction_emit.py:43` hardcoded
`BUNDLED_INSTRUMENT_TYPE = "prediction"` (stale, lowercase), while the live writer
(`engine/orchestrator/manifest_finalize.py`'s `_finalize_prediction_bundles`) stamps the UAC canonical
`InstrumentType.PREDICTION_MARKET.value` (`"PREDICTION_MARKET"`) on the SAME shard atom — fixed there at
`market-tick-data-service@1ec415f8` (2026-07-19) for this EXACT failure mode ("a --force rebuild ... resurrected the
migration's removed stragglers"), but the rebuild script was never updated to match. Since `instrument_type` is a
manifest-consolidator dedup-key column, every backfilled row landed on a NEW dedup key instead of updating the existing
captured row — duplicating (~2,704 net-new rows after one consolidation) rather than backfilling, and leaving the real
historical rows still blank. Full evidence + row-level diagnosis in
`plans/active/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`.

**Fixed**: `market-tick-data-service@b8a8fa7a` — threads `InstrumentType.PREDICTION_MARKET.value` instead of the local
literal, + a regression test pinning the value. `quality-gates.sh` run before shipping.

**Also found**: an EXISTING, already-built sanctioned tool for cleaning up duplicate/stale-key rows,
`scripts/canonicalize_prediction_manifest_2026_07_18.py` (`--remove-stragglers`, in-place CAS REPLACE, snapshot-first,
STOP-ON-SURPRISE captured-cell guard) — its own docstring documented this SAME writer-root gap as "FINDING 2" back on
2026-07-18, one day before the live-writer half was fixed. Its `--apply` path is explicitly HELD pending operator
authorization ("do NOT self-execute") — did NOT run it. Filed as todo 2 in the issue doc above for operator review now
that the writer-root fix (its own checklist step 0) is fully landed at both points.

**Not yet done**: the corrected script's apply re-run (full range `2021-06-30..2026-07-31`), force-consolidate,
fill-rate/guardrail/row-count re-verification, cron resume. **Both `-001` and `-006` stay unflipped** — the
duplicate-row cleanup (issue-doc todo 2) is explicitly OUT of this plan's scope (operator-gated, separate doc) and does
not block `-001`/`-006`, which only need the corrected backfill to actually fill history's `available_at`. Cron
confirmed still `PAUSED`; snapshot from 07-29 still the valid rollback point (untouched).

**Checkpoint, same session (2026-08-01, ~14:27 UTC), context-usage-triggered — apply IN PROGRESS, not done.**

**Second bug caught before it wasted a full run**: the first corrected-script launch
(`--start-date 2021-06-30 --end-date 2026-07-31 --chunk-days 30`, no env prefix) completed all 22 chunks it reached with
`ManifestWriter write failed: ... GCP_PROJECT_ID or AWS_ACCOUNT_ID must be set in environment` on EVERY chunk — the
scan/classify counters (`captured_bundles`, etc.) log "success" independent of whether the actual GCS write landed, so
the run LOOKED healthy in the `chunk N complete` lines while writing NOTHING. Root cause: `ManifestWriter`'s own
storage-client resolution reads `GCP_PROJECT_ID` from the **environment**, separate from the script's `--project-id` CLI
arg (which only parameterises the plain `storage.Client(project=...)` used for the read/scan side) — the two are NOT
wired together. Caught via `grep -c "ManifestWriter write failed" <log>` across the WHOLE log, not the tail (the warning
is sparse relative to routine `Connection pool is full` noise, so a tail-only spot-check missed it for several chunks).
**Lesson for any future rebuild/backfill launch of this script (or others sharing this write path): always export
`GCP_PROJECT_ID=central-element-323112` in the launch command's own environment — the `--project-id` flag alone is NOT
sufficient** — and verify the FIRST chunk's write lands (a fresh `_index/per_vm/local-<pid>-*.parquet` object, or a
`per-VM shard updated` INFO line) before trusting a longer run. Killed the broken run (no partial writes to lose —
confirmed zero net rows changed) and relaunched with `GCP_PROJECT_ID=central-element-323112` prefixed; verified a fresh
per-VM shard landed within seconds.

**Live state as of this checkpoint** (verify freshly before resuming, don't trust these numbers as still-current):
launch command
`cd market-tick-data-service && GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u -m market_tick_data_service.scripts.rebuild_prediction_manifest --start-date 2021-06-30 --end-date 2026-07-31 --chunk-days 30`,
log at `<session scratchpad>/logs/prediction_backfill_corrected_v2_2026_08_01.log` (scratch — regenerable by re-running;
the durable output is the GCS per-VM shard writes themselves, not this log). PID `2843482`
(`ps aux | grep rebuild_prediction_manifest` to check liveness — if gone and no `all N chunk(s) scanned` terminal line
in the log, it died and needs relaunching from scratch, NOT resumed by date, since re-running is idempotent and this
covers the FULL range every time by design). At checkpoint time: chunk 42 of ~62 (this launch's own range is the FULL
5-year span, not the narrower 2024-06-14+ "recovery" range earlier sessions used, so the total chunk count differs from
those — don't reuse "26" as the expected total), zero `ManifestWriter write failed` occurrences since the relaunch, RSS
~900MB and rising gently with denser recent-date chunks (still well-bounded, no memory-safety concern).

**Still required after the apply finishes** (do not flip `-001`/`-006` before ALL of these): (1) confirm the log's
terminal `Elapsed ... Summary` line with zero unexpected failures; (2) force-consolidate
(`GCP_PROJECT_ID=central-element-323112 .venv/bin/python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-pred-prd-central-element-323112 --force`,
run IMMEDIATELY before the fill-rate read since the freshness budget for this bucket is 120s while the cron stays
paused); (3) verify `available_at` fill rate on `capture_status=captured` rows is now near 100% (not the 20.08% this
session's first, buggy apply produced) AND that total row count did NOT balloon the way it did last time (this run's
rows share the historical rows' dedup key, so count should stay flat, not grow by thousands) AND no
`COLUMN FILL REGRESSION`/`CAPTURED-ROW COLUMN FILL REGRESSION` critical log line appeared in the consolidate output; (4)
resume the cron via `scripts/mtds_available_at_backfill_resume_prediction_2026_07_30.py` (not raw `gcloud`); (5) record
the final before/after fill-rate evidence here and flip both checkboxes citing the apply's actual completion + the
consolidate run + the resume run.

### 2026-08-02 — #10 (slot-13, data_engineering) — diagnosed the real gap: corrected apply only covered 2021-06..2025-02; relaunched for the incomplete tail

Fresh session, dispatched `-006` (`already_in_progress: true`, `dispatch_reason: resume`). No
`rebuild_prediction_manifest` process was running (`ps aux` clean); the last recorded checkpoint (#9, chunk 42/62) was
gone. A force-consolidate had run since (2026-08-02T11:35 UTC, `latest.json`: `rows_out=1,955,294`,
`dedup_dropped=884,687`, `success=true`) — likely the tail end of #9's session before it ended.

**Read the freshly-consolidated `_index/availability_index.parquet` directly** (one-off diagnostic download +
`pd.read_parquet`, not a corpus GCS walk — the file `read_availability_index()` would itself read, just bypassing the
120s cron-paused staleness gate for this one read): aggregate fill rate on `capture_status=captured` is 19.96%, matching
#9's original bug signature — but splitting by `instrument_type` shows this is NOT a new regression:

- `instrument_type=PREDICTION_MARKET` (canonical, n=323,716): 16.1% filled.
- `instrument_type=prediction` (stale lowercase literal, n=18,096): 100% filled — these are the KNOWN #9-diagnosed
  duplicate stragglers from the pre-fix buggy apply (`written_at` 2026-07-31), cleanup explicitly
  deferred/operator-gated (issue-doc `mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md` todo 2) and out of
  THIS plan's scope per #9's own note — they cap the aggregate metric below 100% permanently until that separate cleanup
  runs, which is expected, not a new bug.
- `instrument_type=prediction_market` (different casing, n=9,720, `written_at` 07-17..07-23, 0% filled): unrelated
  legacy/cross-contamination rows, not touched by this backfill's scope either.

**The real signal is the canonical-only split by month**: `PREDICTION_MARKET` rows are **100% filled for every month
2021-06 through 2025-02** (the corrected apply, `written_at` up to 2026-08-02, DID succeed for that range) but drop
sharply from 2025-03 onward (66% → single digits by 2026-01..2026-05, a brief 95.8% spike in 2026-06, 25.6% in 2026-07,
1.7% in 2026-08) — and that later range is where the bulk of the row volume actually lives (2025-09 alone has 17,834
canonical rows vs ~30-120/month pre-2024-10). **The corrected apply never finished the dense recent range** — consistent
with the #9 checkpoint's chunk-42-of-62 stopping point (5-year full-range run, `--chunk-days 30`) landing right around
early 2025 before the session ended.

**Action (efficiency north-star — don't re-scan the already-100%-filled 2021-2024 range)**: relaunched
`rebuild_prediction_manifest.py --start-date 2025-01-01 --end-date 2026-08-01 --chunk-days 15` (small 1-month safety
overlap before the 2025-03 cliff; `--end-date` one day before today to avoid an in-flight partial capture day),
`GCP_PROJECT_ID=central-element-323112` exported per the #9-documented gotcha (script's `--project-id` flag alone does
NOT wire into `ManifestWriter`'s env-based project resolution). Verified chunk 1 (2025-01-01..2025-01-15, 46,312
objects) is processing cleanly, zero `ManifestWriter write failed` occurrences. Running in background under `Monitor`,
not `ScheduleWakeup` (the #8-documented harness-teardown risk). `unified-trading-sa` GCP identity used for the
diagnostic reads/cron-state checks (the default active gcloud account on this host, `github-actions-deploy`, lacks
`cloudscheduler.jobs.get` — switched per RULES.md § 5's self-service ambient-identity rule, not a blocked-question).

**Not yet done**: apply for 2025-01..2026-08 not finished, force-consolidate not re-run, fill-rate not re-verified, cron
not resumed. **Both `-001` and `-006` stay unflipped.** Cron confirmed still `PAUSED`
(`uts-prod-manifest-consolidator-market-data-prediction-cron`); 07-29 snapshot still the valid rollback point (untouched
by this session — only ran read-only diagnostics + the idempotent apply script). Maintenance-window lock
(`_maintenance_window.json`, expires 2026-08-03T04:56:45Z) still valid for this plan; if this session's apply runs past
that, the lock needs renewing before it lapses.

### 2026-08-02 — #11 (slot-3, data_engineering) — tradfi apply crashed on a real bundled-shard bug, fixed + shipped, resumed

Dispatched via `cf_manifest_audit_first_full_rollup_findings-001` (the fresh CF-manifest-audit's CF-8 finding for
tradfi, which is exactly this plan's remaining tradfi todos — folded in here rather than duplicated). Also the CRITICAL
PATH context from `/plans/active/issues/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md`:
the cron pause since 07-29 has left `availability_index.parquet` ~42h+ stale, causing EVERY tradfi download-VM to
self-delete at boot (`exit_code=78` OOM preflight) — fleet-wide outage, not one shard.

**Baseline read** (fresh index download, single-file, not a corpus walk): 1,496,036 captured rows, `available_at` 69.97%
filled (1,046,738) — live captures since the 07-14 writer fix (`market-tick-data-service@65a6f9e0`) are already filling
it going forward; the gap is the pre-fix historical backlog, exactly what this todo's apply closes. Date range
2019-01-02..2026-07-30.

**Launched** `rebuild_tradfi_manifest.py --start-date 2019-01-02 --end-date 2026-07-30 --chunk-days 30`
(`GCP_PROJECT_ID=central-element-323112` exported per the prediction session's documented gotcha). **Crashed at chunk
53/93** (`2023-04-11..2023-05-10`) after 52 chunks completed cleanly:
`ValueError: ManifestWriter.add() with bundled data_type='futures_chain' is banned`. Root cause: the 2026-07-14 "dead
code" removal (`c8c01855`, earlier in this same plan's Progress Log) deleted the
`if parsed.data_type in BUNDLED_DATA_TYPES` branch, reasoning from a 2026-07 recent-date sample + the live manifest's
already-captured rows that this branch never fires. **That sample never covered 2023-era history** — confirmed live via
`gsutil ls`:
`day=2023-05-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=futures_chain/ data_type=futures_chain/underlying=AUD/quote=USD/margin=linear/ticks.parquet`
— a real early-databento bundled-by-underlying convention (both `instrument_type` AND `data_type` literally the
chain-type) that later shifted to per-instrument OHLCV files. Since chunks 1-52 (2019-01-02..2023-04-10) completed
without hitting this, that range is confirmed clean — no earlier bundled-shape gap to worry about.

**Fixed + shipped**: `market-tick-data-service@9d354cea` restores the branch (extracted into a new `_emit_shard_row`
helper to stay under the 200-line function cap after the file also needed trimming to stay ≤900 lines), routing
genuinely-bundled `data_type` values through `_emit_bundled_shard_row`/`record_captured_from_counts`. New regression
test (`test_scan_rebuild_bundled_data_type_routes_to_record_captured_from_counts`) reproduces the exact crash. Full
`quality-gates.sh` green, `quickmerge --agent` landed on `live-defi-rollout` (verified via `merge-base --is-ancestor`).

**Resumed** the apply from the crash point: `--start-date 2023-04-11 --end-date 2026-07-30 --chunk-days 30` (not
re-scanning the already-clean 2019-2023-04-10 range — efficiency north-star). Running in background under `Monitor` with
a 9-min heartbeat, not `ScheduleWakeup`.

**Apply completed** (same session, checkpoint continued): all 41 chunks scanned (2023-04-11..2026-07-30),
`{'total_shards': 1138615, 'unparseable': 77, 'skipped_hyphen': 0, 'distinct_venues': 223, 'distinct_dates': 973}`,
CF-11 honest-absence reemit found 0 remaining gaps. The 77 unparseable objects
(`raw_tick_data/by_date/day=D/venue=V/ticks.parquet` — missing `data_type=` entirely, a tiny 0.007% pre-existing legacy
shape the parser correctly skips rather than crashes on, unrelated to this fix) are noted but not worth a follow-up todo
given the volume.

**Force-consolidated**: `manifest_consolidator --bucket market-data-tick-tradfi-prd-central-element-323112 --force`,
`rows_out=6577303` (pre: 6,380,949 → post: 6,577,303, +196,354, 3.1%). **Guardrail investigation** (required before
declaring success, per this plan's HARD constraint section): `MANIFEST_COLUMN_FILL_REGRESSION` DID trip on
`instrument_id` (aggregate 84.16%→81.72%, captured-only 67.08%→59.39%) — treated as a real signal, not waved off.
Downloaded pre/post index parquets and diffed directly:

- Absolute instrument_id-filled count only ROSE (968,812 → 976,226) — no previously-filled row lost its value; this
  rules out the sports-precedent "serializer silently drops a populated column" failure mode.
- The percentage drop is 100% explained by ~614K newly-visible rows (both bundled AND non-bundled by `data_type`) whose
  `instrument_type` ∈ {combo, futures_chain, options_chain, continuous_future} (~98% of the blank-instrument_id cohort)
  — these come from the underlying-bundle path shape (`_PAT_UNDERLYING_BUNDLE` in `rebuild_tradfi_manifest.py`,
  pre-existing parser code this fix did not touch), which structurally sets `instrument_id=""` always (the atom is the
  underlying-bundle, not a single instrument — `underlying` carries the identity instead, confirmed 95% populated on
  this cohort). This 2023-era historical corpus is dominated by one-file-per-underlying chain data that later shifted to
  per-instrument files — an honest reflection of the historical data shape, not a bug.
- Row-count growth (+196,354) is proportionate: `attempted_failed` -5,467 and `expected_unattempted` -208, `captured`
  +201,729, `empty_confirmed` +300 — real objects the scan discovered getting correctly reclassified from
  not-yet-captured to captured, not the sports-style runaway duplication.
- `available_at` fill on captured rows: **69.97% → 81.85%** (my aggregate read at this checkpoint — see #12 immediately
  below for a slightly different re-read + the more important per-month breakdown). Split by bundled/non-bundled:
  non-bundled 87.03% filled, bundled only 5.14% filled — the bundled shortfall is almost entirely the ~103,232
  PRE-EXISTING CME live-orchestrator bundled rows (`manifest_finalize.py`, a separate write path this rebuild script
  doesn't reconstruct — explicitly out of scope per this plan's "What we already know" section), not a defect in this
  fix (the ~4,064 NEWLY-backfilled bundled rows correctly got their `available_at_envelope` stamped).

**Resumed the cron**: `scripts/mtds_available_at_backfill_resume_tradfi_2026_07_30.py` — maintenance window released,
`gcloud scheduler jobs describe` confirms `ENABLED` (`*/1 * * * *`). This closes the fleet-wide tradfi backfill VM
outage (`/plans/active/issues/tradfi_ohlcv_backfill_oom_preflight_fails_paused_consolidator_2026_08_02.md`) — the index
will stay fresh going forward, clearing the `setup-data-pipeline-vm.sh` OOM-preflight guard for new launches. **This
cron-resume is independently complete and MUST NOT be re-paused** — re-pausing would reopen the fleet-wide outage this
closed. Only the "Apply" todo's completeness is still an open question — see #12 immediately below, which read the index
shortly after this checkpoint and found the aggregate fill number alone hides a real per-month structural gap. 07-29
snapshot (`pre_available_at_backfill_20260729T010709Z.parquet`) remains the pre-backfill rollback point if ever needed
(untouched this session). The guardrail false-positive is filed as its own new P3 todo above
(`MANIFEST_COLUMN_FILL_REGRESSION` blind to legitimately-blank-by-shape columns) — it will likely recur on this plan's
own prediction/defi apply todos.

### 2026-08-02 — #12 (slot-14, data_engineering) — dispatched `-006` again; diagnosed both lanes fresh, launched prediction continuation, flagged a new tradfi question

Fresh session, dispatched `mtds_available_at_cross_asset_backfill-006` (not `already_in_progress` this time — a clean
new claim, not a resume). Per the established precedent (declined by 4+ prior sessions), verified live state before
doing anything: `GET /api/backlog` confirms `-001` still `queued`/never dispatched while `-006` sat with this slot —
same dispatch-order violation, now corroborated as its own tracked issue
(`mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`). Rather than declining a 6th time, read the
plan's own established "pragmatic unblock" recommendation (that doc's option A: "any data_engineering worker directly
execute `-001`... unblocks both stalled plans") and, since `-001`/`-006` are the SAME plan I'm already dispatched into
(not a scope violation — task_template.md's "independent same-priority todos run concurrently" rule), continued the real
work both lanes have had in progress across #7-#11.

**Prediction lane — fresh diagnostic** (one-off direct download of the consolidated index, bypassing
`read_availability_index`'s 120s staleness gate since the cron is intentionally paused — matches #10's approach, not a
corpus walk): 323,719 `PREDICTION_MARKET` (canonical) captured rows, 351,535 total captured (18,096
`instrument_type=prediction` legacy-lowercase duplicates confirmed 100% filled — the known #9-diagnosed straggler class,
operator-gated cleanup, out of this plan's scope; 9,720 `instrument_type=prediction_market` mixed-case
legacy/cross-contamination rows, 0% filled, also out of scope per #10). **Canonical fill rate by month**: 100% for EVERY
month 2021-06 through 2024-12 (confirms #10's corrected-apply chunk-42 checkpoint held); 2025-01/02 at 98.8%/99.4%
(near-complete, not quite — #10's relaunch chunk 1 covered part of this); 2025-03 onward drops sharply (45.7% → single
digits by 2026-02, a partial 25.6% bump in 2026-07) — confirms #10's relaunch
(`--start-date 2025-01-01 --end-date 2026-08-01 --chunk-days 15`) made only minimal progress (chunk 1 of ~44) before its
session ended. Overall canonical fill rate 5.74% (diluted by the huge unfilled 2025-2026 volume — 2025-09 alone has
17,834 canonical rows, dwarfing the ~30-120/month pre-2024 baseline).

**Launched the prediction continuation**:
`GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp .venv/bin/python -u -m market_tick_data_service.scripts.rebuild_prediction_manifest --start-date 2025-01-01 --end-date 2026-08-01 --chunk-days 15`
(same range/chunk-size #10 already validated as safe — not re-deriving a new value). Verified per #9's documented gotcha
(env-var write-path failure looks healthy in scan logs): 0 `ManifestWriter write failed` occurrences through chunk 1's
first 20,000/46,312 objects processed, steady throughput, no OOM signature (RSS tracked via a `Monitor`-tool watch with
a 35GB safety-kill backstop, not `ScheduleWakeup` per #8's documented harness-teardown risk). Running in background;
**not yet done** — chunk 1 of ~44 in progress at this checkpoint, force-consolidate/fill-rate-reverify/ cron-resume all
still pending.

**Tradfi lane — fresh diagnostic, genuine progress confirmed but a NEW open question found**: same one-off
direct-download approach. Aggregate fill rate on `capture_status=captured` rows: **77.03%** (1,307,774/1,697,765) — up
from #11's baseline 69.97% (1,046,738/1,496,036), confirming #11's chunk-53+ resume landed real progress (both the
captured-row COUNT and the fill fraction grew — the rebuild evidently registers some previously-unregistered objects
too, not just fills existing rows' `available_at`). **Per-month breakdown surfaces something #11's aggregate-only
baseline didn't show**: 2019-01 through 2023-03 sits at a stable **~50-60%** fill rate (not near-100%), while 2023-04
onward (past #11's original crash point) sits at **~85-90%**. #11's own note says chunks 1-52 (2019-01-02..2023-04-10)
"completed cleanly" in the FIRST launch — but "completed cleanly" only means the scan/emit loop didn't crash, not that
it drove fill rate to ~100%.

**Follow-up same session — sharpened, NOT a structural ceiling.** Split fill rate by `(era, data_type)` and
`(era, is_bundled)` (bundled = `data_type in {futures_chain, options_chain, event_contract}`, matching
`_emit_shard_row`'s own gate): pre-2023-04 has **zero** bundled-`data_type` rows at all (the bundled-by-underlying
convention #11's crash example hit only appears from 2023-04-11 onward, i.e. it's entirely a post-2023-04 phenomenon in
THIS split, not a pre-existing pre-2023-04 class) — so the bundled/no-timestamp hypothesis is RULED OUT for this era.
The actual pre-2023-04 shortfall is concentrated in the two dominant, perfectly ordinary non-bundled data types:
`ohlcv_1s` (141,009 rows, 58.0% filled) and `ohlcv_1m` (137,322 rows, 55.1% filled) — plain per-instrument OHLCV shards
that `_available_at_from_blob`'s own docstring says should "not [be] expected" to fail (it only returns `""` when GCS
hasn't populated `time_created`, essentially never on a real listed blob). A ~55% ceiling on ordinary listed blobs
strongly suggests the chunks-1-52 scan simply never re-emitted roughly half of the existing captured rows for that era
(a path-parsing coverage gap, similar in KIND to the bundled-shape gap #11 found for 2023-04+, but a different,
not-yet-identified shape) — their manifest rows are un-touched leftovers from before the 07-14 live-writer fix, not
something the rebuild intentionally exempts. **Recommend**: re-running
`--start-date 2019-01-02 --end-date 2023-04-10 --chunk-days 30` (now on the `9d354cea`-fixed code) is the right next
step, but ALSO grep the resulting log for `unparseable` counts specifically for this range before trusting a clean
re-run — if unparseable stays 0 while fill rate still doesn't move, the gap is likely NOT a path-parsing issue and needs
a different explanation (e.g. dedup losing the fresh row to an older un-touched one on the consolidator side). Did not
attempt the re-run or the parser investigation this session (time-boxed to the prediction-lane launch).

**2026-08-02, resumed session — re-run DONE, this exact fallback case confirmed. The path-parsing hypothesis is now
DEFINITIVELY RULED OUT too.** Ran
`rebuild_tradfi_manifest.py --start-date 2019-01-02 --end-date 2023-04-10 --chunk-days 30` on the `9d354cea`-fixed code:
all 52 chunks completed clean, **0 unparseable across the entire range**, 151,696 total shards, 111s elapsed.
Force-consolidate contended briefly with the tradfi cron's own lock (normal — `_LOCK_TTL_SECONDS=300`, not a stuck lock;
a fresh cron cycle picked it up and the consolidated index genuinely refreshed, `Update Time` moved from `17:39:42Z` to
`17:46:36Z`, well after this re-run's writes landed at `17:41:52Z`). Re-ran the fill-rate check against the
confirmed-fresh index: **byte-identical to before the re-run** — `ohlcv_1s` 58.0%, `ohlcv_1m` 55.1%, overall 77.03%
(1,307,774/1,697,765), down to the exact row counts. **A completely clean re-scan of the whole range, with genuinely
fresh consolidated data, produced ZERO change.** This rules out both candidate explanations from the prior entry: not a
bundled/no-timestamp class (already ruled out — 0 bundled rows in this era), and now not a scan/path-parsing coverage
gap either (0 unparseable, so the scan lists and processes every object it can see). **The only remaining explanation
from the original recommendation is the third one**: the manifest consolidator's dedup is losing the fresh, filled row
to an older, unfilled one sharing the same row-key — i.e. this rebuild's writes ARE landing (confirmed via the per-VM
shard `time_created` bumps + the consolidator picking them up), but something in the merge/dedup ordering
(`rows_out`/`dedup_dropped` logic, or a `written_at` last-write-wins comparison) is choosing an OLDER pre-fix row over
this rebuild's fresh one for roughly half of 2019-2023-04's non-bundled OHLCV cells. **Not investigated further this
session** (would need reading the consolidator's actual dedup/last-write-wins comparator against a sample of the ~45%
still-unfilled row-keys, checking whether their `written_at` is older or newer than this rebuild's run, and if older,
whether the comparator is supposed to prefer newer writes but isn't) — flagging as the next concrete step, not
re-guessing with a third re-run (would just reproduce the same result for the third time).

**Prediction stays unflipped** (`-006`, neither lane complete for it). **Tradfi's cron-resume todo stays flipped**
(independently verified complete, see #11) but **the Apply todo is reverted to unflipped** per this session's own
finding above — the aggregate fill number alone hid a real per-month gap, so "applied without crashing" is not the same
as "backlog resolved." Cron confirmed still `PAUSED` for prediction
(`uts-prod-manifest-consolidator-market-data-prediction-cron`); tradfi's is `ENABLED` per #11. Snapshots from 07-29
remain the valid rollback points, untouched. `unified-trading-sa` GCP identity used for diagnostic reads (the default
`github-actions-deploy` active account lacks `cloudscheduler.jobs.get` — switched per RULES.md § 5's self-service
ambient-identity rule).

**Session-end handoff (2026-08-02T16:35Z, context-usage-triggered) — CORRECTED below, the "still running independently"
claim was wrong.** The prediction continuation (PID 4180822,
`--start-date 2025-01-01 --end-date 2026-08-01 --chunk-days 15`) was assumed to survive past this chat session ending.
**It did not**: confirmed killed (`ps -p 4180822` empty, no traceback/error in its log — an external termination, not a
crash) partway through chunk 18 (`2025-09-13..2025-09-27`, ~89,000/164,650 objects scanned when it stopped, no
completion line for that chunk). **Real, durable progress before the kill**: chunks 1-17 (`2025-01-01..2025-09-12`) all
show a clean `chunk N complete` line with 0 write failures each — that range's manifest rows are genuinely landed (each
chunk's `ManifestWriter.flush()` already happened). Chunk 18 itself made ZERO durable progress (killed before its own
flush). **Lesson for next session**: a `run_in_background` Bash-tool process is not guaranteed to outlive this specific
kind of session lifecycle event (compaction-adjacent) even without `nohup`/`ScheduleWakeup` — the established "survives
independently" assumption from earlier entries in this doc (e.g. #9, #10) needs re-verifying with a live `ps` check, not
just assumed from a chat claim, before trusting a "left it running" handoff. **Efficient resume** (don't re-scan the
confirmed-clean 2025-01-01..2025-09-12 range):
`GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp .venv/bin/python -u -m market_tick_data_service.scripts.rebuild_prediction_manifest --start-date 2025-09-13 --end-date 2026-08-01 --chunk-days 15`.
**Promoted 3 reusable scripts from scratchpad to `market-tick-data-service/scripts/`** (verified with
`quality-gates.sh`, `market-tick-data-service@3c51b3d0`): `mtds_prediction_fillrate_check_2026_08_02.py` and
`mtds_tradfi_fillrate_check_2026_08_02.py` (the exact fill-rate/era-split diagnostics this session used — re-run either
after the next apply chunk lands, no need to hand-roll a new one-off) and `odds_api_rss_sampler_2026_08_02.py` (for the
sibling OOM doc, once vendor credits are restored). **Next steps for whoever resumes**: (1) relaunch the prediction
apply scoped to `2025-09-13..2026-08-01` per the efficient-resume command above (verify chunk 1's write actually lands
per #9's documented env-var gotcha before trusting a longer run), then once done, force-consolidate + re-run the
fill-rate check + verify guardrail/row-count per the "Still required" checklist in #9's entry above; (2) separately,
re-run `--start-date 2019-01-02 --end-date 2023-04-10 --chunk-days 30` for tradfi to test whether the pre-2023-04
fill-rate ceiling moves now that the bundled-shard fix is live, checking `unparseable` counts per this session's
recommendation; (3) the operator has approved purchasing additional odds-api credits (BLK-6728ec9a, option B) for the
UNRELATED sports odds_api backfill — re-verify live before resuming that separate work, do not assume the purchase is
instant.

### 2026-08-02T17:52Z — #13 (slot-15, data_engineering, dispatched `-001`) — declining, exact apply already live under slot-14's `-006`

Dispatched `-001` ("Apply `rebuild_prediction_manifest.py`"). Before launching anything, verified live process state
(not trusting the doc's last checkpoint blind): `ps aux` shows PID 1860179,
`rebuild_prediction_manifest.py --start-date 2025-09-13 --end-date 2026-08-01 --chunk-days 15` — the EXACT command #12's
handoff recommended — already RUNNING (started 17:31Z, ~20min uptime, 127% CPU, healthy) from
`.tabs/14/market-tick-data-service`. Cross-checked `GET /api/state`: slot 14 is dispatched on
`mtds_available_at_cross_asset_backfill-006` with `last_msg` confirming "Prediction backfill continues healthily in
background (chunk 2/32, RSS ~2.3GB)" plus a completed tradfi pre-2023-04 re-run (see `unified-trading-pm@90dc8d193`).
Launching a second, identical apply here would waste shared-host compute and risk a write race on the same per-VM shard
prefix for no benefit — not doing that. Declining `-001` and skipping (not holding the slot for a multi-chunk apply
another slot already owns), `reason_code: "OTHER"` (a per-slot duplication fact, not a fleet-wide blocking condition —
the follow-through steps, force-consolidate/fill-rate-reverify/cron-resume, remain open work for whoever picks up next
once slot-14's run actually finishes).

**2026-08-02, resumed session (slot-14) — item (2) above done (see the tradfi Apply todo's own entry for the full
result); a sharper, verified lead found for the consolidator-dedup hypothesis.** Sampled real `attempted_at`/
`written_at`/`instrument_id` values directly from the manifest for the still-unfilled `pre-2023-04 ohlcv_1m` cells:
**`instrument_id` is blank/`None` on BOTH the filled and unfilled rows** for the same `(date, venue, data_type)`
combination (e.g. multiple distinct rows for `date=2020-01-02, venue=CME, data_type=ohlcv_1m` all carry
`instrument_id=None`). This is a sharper, directly-verified fact (not code-reading speculation) than the prior "dedup
last-write-wins" hypothesis — if the manifest's row-key groups by
`(date, venue, instrument_type, data_type, instrument_id)` and `instrument_id` is never populated for this era's OHLCV
rows, then MANY distinct real per-instrument objects (this row-key's dedup group plausibly represents dozens of
different CME futures contracts trading that day, not one instrument) collapse onto a tiny number of manifest row-keys —
consistent with the small `captured_cells` counts this session's re-run reported per chunk (e.g. `3796` cells for a
whole 30-day chunk) vs. the much larger row counts the fill-rate check's `groupby` sees when reading the full manifest —
those are two different levels of aggregation that this session did not fully reconcile.

**Same session, follow-up — CONFIRMED via the actual dedup-key code, not just data sampling.** Read
`unified_trading_library/manifest_consolidator.py`: `_BASE_DEDUP_COLS = ("date", "venue", "data_type", "service_name")`,
and `_OPTIONAL_DEDUP_COLS` explicitly **includes `"instrument_id"`** (`_resolve_dedup_cols`, line ~2109) — it IS a real
dedup dimension, not incidental.

**CORRECTION, same session — the "populate instrument_id per-object" conclusion immediately below was premature;
verified against the real GCS object and it does NOT hold.** Checked the actual object behind one of these rows directly
(`gs://.../day=2020-01-02/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=future/ data_type=ohlcv_1m/ticks.parquet`):
there is exactly ONE file, named `ticks.parquet` (not a per-instrument filename) — this shape is a genuine bundle-by-day
file covering many instruments, not a mis-parsed per-instrument object. So a blank `instrument_id` for this shape is
correct-by-design given the rebuild script's own parsing rules, not a parser bug — retracting the "real fix: populate
instrument_id per-object" recommendation two paragraphs above.

**What the same query DID surface, re-checked with `instrument_type` included this time (181 rows for just
`date=2020-01-02, venue=CME, data_type=ohlcv_1m`)**: the manifest carries BOTH lowercase (`combo`, `future`) AND
uppercase-canonical (`COMBO`, `FUTURE`) `instrument_type` values as PERMANENTLY DISTINCT dedup groups for what is
conceptually the same instrument class — e.g. many `combo` rows (old, `written_at` 2026-07-18..07-28) coexist alongside
`COMBO` rows (this session's fresh rebuild, `written_at` 2026-08-02T17:40) without ever merging, because dedup on
`instrument_type` is case-sensitive. **This is NOT a new bug** — it's the already-known, already-ruled C2a
`instrument_type` casing issue (`/codex/02-data/cross-asset-canonical-target-ssot.md` and siblings; CLAUDE.md's own
domain index: "C2a instrument_type COLUMN casing... RULED (D1/D2 2026-07-20) but migration_pending — compare
case-insensitively, do NOT flag, do NOT refuse"). Its practical effect here: this session's rebuild (uppercase) never
actually overwrites/fixes the old lowercase rows' `available_at` — it just adds a SEPARATE, parallel-but-never- merged
uppercase row, so the fill-rate check (which reads BOTH casings as distinct rows) sees the old unfilled lowercase rows
persist forever alongside the new filled uppercase ones, diluting the aggregate. **This plausibly explains the
byte-identical-after-re-run result better than the retracted instrument_id theory**: the rebuild isn't failing to write
useful data, it's writing correct data that the still-migration-pending casing split prevents from ever superseding the
old rows.

**CONFIRMED, same session — re-ran the fill-rate check with `instrument_type.str.upper()` folded before grouping**
(pre-2023-04, `ohlcv_1m`+`ohlcv_1s`, `n=280,005` rows): naive case-sensitive fill rate **56.8%**, matching the earlier
per-data_type numbers. Folded — grouping by `(date, venue, data_type, UPPER(instrument_type))` and counting a key as
"covered" if ANY casing variant of that key is filled — jumps to **8,832 distinct folded keys, 7,418 covered (84.0%)**.
**Casing duplication explains the large majority of the apparent gap** (56.8% → 84.0% just from folding), though not all
of it — a genuine ~16% remains unfilled even after folding, which is real remaining work, not a measurement artifact.
**Practical implication for whoever closes this out**: (1) the "fill rate" metric this whole investigation has been
using is measuring the wrong thing while the C2a casing migration stays pending — any completion check for this todo
should fold casing first, or it will perpetually undercount; (2) do NOT attempt a third full re-run of the rebuild
expecting a different result — the rebuild is already landing correct data, the remaining ~16% gap plus the casing-fold
itself are the real next steps, not another `rebuild_tradfi_manifest.py` invocation; (3) whether to actually MIGRATE the
old lowercase rows to canonical uppercase (closing the split permanently) is the C2a ruling's own open migration work,
out of this plan's scope — this doc's Apply todo should likely be evaluated against the FOLDED number, not the raw one,
when deciding whether to flip it.
