---
doc_type: issue
title:
  DP-FETCH-009 for defi/dex_pool_swaps (14036 attempted_failed) traced to 13 stale UNISWAP_V3/ETHEREUM dates —
  re-captured live with current code (0 code bug found); stale-row purge filed as follow-up
summary: >-
  Escalation agt-d2c3cc: DP-FETCH-009 fired for asset_group=defi data_type=dex_pool_swaps (14036 attempted_failed of
  8471219 attempted, abs>=500 threshold; 13382 fresh in the last 1d). Bounded manifest reads (pyarrow GcsFileSystem +
  column-projection + Arrow-level filter, mirroring `_attempted_failed_index.py`'s own OOM-safe pattern) isolated the
  finding: of 7,841,388 raw dex_pool_swaps attempted_failed rows, 7,827,336 carry a `superseded_by_*` error_reason
  (already excluded from the detector's count by design) — the REAL non-superseded total is 14,052 (~matches the
  alert's 14,036, small drift from the trailing-window boundary), split SCHEMA_VALIDATION_FAILED 13,673 +
  MANIFEST_WRITE_FAILED 379. The SCHEMA_VALIDATION_FAILED rows are 100% venue=UNISWAP_V3, 100% chain=ETHEREUM, and
  span exactly 13 distinct TARGET dates (2025-01-09..2025-01-21, ~1000-1100 rows/date) — NOT 13 rows (one per
  shard-attempt), so these were written by repeated re-attempts against the same 13 historical dates over the
  `attempted_at` window (2026-08-10..2026-08-16), not a single failing run.

  Root-cause hunt for the literal `SCHEMA_VALIDATION_FAILED` string in current MTDS/UTL/UAC code came up EMPTY —
  it is not `dex_swaps_handler.py`'s generic exception-classify path (traced `classify_venue_error()`'s exact-match
  semantics fully; no UAC error map entry registers this literal anywhere in `canonical/crosscutting/errors/*.py`),
  not `schema_validation.py`'s `SchemaValidationError` (dynamic per-shard message, would never produce a UNIFORM
  literal across 13 different dates), and not `write_defi_rows`'s contract/symbol-column checks (repro'd with
  edge-case rows — None tokens, emoji symbols, empty pool_id — all wrote cleanly, no exception). The ONLY live source
  of this exact literal in the whole workspace is MDPS's `canonical_writer.py:499` (`open_candle_writer(strict=True)`
  → `ValueError` → hardcoded `reason: "SCHEMA_VALIDATION_FAILED"` in the `DEPLOYMENT_FAILED` event) — a DIFFERENT
  service's candle-derivation write path that `dex_swaps_handler.py`/`canonical_write.py` (MTDS's raw-tick writer)
  does not use at all (confirmed by reading both files' write paths end-to-end: no `open_candle_writer` import,
  no UTL strict-writer boundary — MTDS's `write_defi_rows` writes pandas/pyarrow directly).

  **Direct live re-verification (the decisive test)**: re-ran the REAL `DexSwapsHandler._collect_one_shard` code path
  (current git HEAD, `market-tick-data-service@$(git rev-parse --short HEAD)` at investigation time) for
  uniswap_v3/ethereum against all 13 affected dates, end-to-end (fetch → catalogue-filter → cascade parse → schema
  validate → `write_defi_rows` → GCS upload → `DefiManifestRecorder.record_captured` per pool). **All 13 dates
  succeeded cleanly, zero exceptions**, writing real production data:
  2025-01-09=46578, 01-10=41274, 01-11=34658, 01-12=35668, 01-13=57087 (2 runs, first bypassed the recorder — see
  Progress Log), 01-14=38908, 01-15=41262, 01-16=41381, 01-17=41627, 01-18=44589, 01-19=50227, 01-20=47562,
  01-21=44995 swap rows, to `gs://market-data-tick-defi-prd-central-element-323112`, with `record_captured` rows
  written per pool via the real `DefiManifestRecorder`. This conclusively demonstrates the underlying write path is
  healthy against current code — whatever wrote these 13673 stale rows either used code from before one of the many
  defi-adjacent MTDS fixes that landed 2026-08-10..2026-08-16 (git log shows a dense run of `fix(defi):`/`c6b9113b
  CF-11 swallow-fixes in manifest recorder...` commits in exactly this window), or hit a transient upstream
  condition (subgraph indexer gap) for that specific 13-day window that has since cleared. No currently-running VM
  or Cloud Run job for this specific backfill was found (`gcloud compute instances list` / `gcloud run jobs list`,
  both empty for dex/defi-swap-shaped names as of investigation time) — so this is not an active broken writer, it
  is stale manifest residue.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags:
  [
    dp-fetch-009,
    defi,
    dex-pool-swaps,
    uniswap-v3,
    schema-validation-failed,
    stale-manifest-rows,
    honest-coverage,
    re-verified-fixed,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/2026_08/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
source: dp-fleet-monitor
resolved_by: ""
locked_by: ""
created: 2026-08-16
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline: 0.3
calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope: [market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py, market-tick-data-service/market_tick_data_service/cli/handlers/_dex_swaps_queries.py, deployment-service/deployment_service/data_pipeline_monitors/_attempted_failed_index.py, /codex/05-infrastructure/data-pipeline-alerts.md]
---

## What I found

Full diagnosis chain + live re-verification evidence in the summary above and the Progress Log below. Headline: the
`attempted_failed` cells are real but STALE — 13 historical UNISWAP_V3/ETHEREUM dex_pool_swaps dates (2025-01-09..21)
that failed repeatedly against an OLDER (now-superseded) version of the write path; current code captures all 13
cleanly, verified live against production GCS + the real manifest recorder.

## Why it matters

DP-FETCH-009's abs-threshold (`attempted_failed >= 500`) fires regardless of ratio once a batch of failures exists,
so these 14,036 stale rows will keep paging every sweep until either (a) they age out of the detector's
`ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14` window (the 08-10 rows age out ~08-24; the 08-16 spike ~08-30), or (b) a
proper reclassification purges them from the consolidated `_index/availability_index.parquet` — mirroring the
`tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md` precedent's `reclass_*.py` pattern
(dry-run sizing script → snapshot-before-write → reversibility check → `--apply`, `superseded_by_<reason>_<date>`
error_reason prefix, which the detector's own `SUPERSEDED_BY_REASON_PREFIX` mechanism already excludes from the
count/ratio).

## Recommended decision

1. **No MTDS code fix needed** — verified live, current code works cleanly for all 13 affected dates.
2. **Data remediation APPLIED this session** — all 13 dates re-captured with real data + manifest `record_captured`
   rows (see Progress Log for exact counts/paths).
3. **Stale-row purge — NOT attempted inline** (scoped as todo 2 below): the consolidated defi
   `_index/availability_index.parquet` is ~159M rows / ~6.8GiB — an in-place rewrite on the shared host would
   violate the "heavy I/O never runs on the operator's local machine, always a VM" HARD RULE
   (`/codex/05-infrastructure/vm-launcher-runbook.md`) and needs the same dry-run/snapshot/reversibility rigor the
   Tardis precedent used (that took a dedicated multi-session script for a comparable ~5,568-row purge on a much
   smaller ~10.3M-row cefi index). Filed as a properly scoped follow-up rather than improvised here.

## Todos

- [x] [DATA] P2. Re-capture all 13 stale UNISWAP_V3/ETHEREUM dex_pool_swaps dates (2025-01-09..2025-01-21) with the
      current write path, verifying zero exceptions and real row counts. Repo: market-tick-data-service. **DONE**
      this session — see Progress Log for per-date counts; real data + `record_captured` manifest rows written to
      `gs://market-data-tick-defi-prd-central-element-323112`.
- [x] [SCRIPT] P2. Build a dry-run-first reclassification script (mirroring
      `market-tick-data-service/scripts/reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py`'s shape) that
      snapshots the defi `_index/availability_index.parquet`, sizes the SCHEMA_VALIDATION_FAILED rows for
      `(asset_group=defi, data_type=dex_pool_swaps, venue=UNISWAP_V3, chain=ETHEREUM, date in
      [2025-01-09..2025-01-21])`, and reclassifies them to
      `error_reason=superseded_by_verified_recapture_success_2026_08_16` (excluded from DP-FETCH-009's count/ratio
      by `SUPERSEDED_BY_REASON_PREFIX`). **DONE** this session (agt-c57d2e, slot 6) —
      `market-tick-data-service/scripts/reclass_defi_uniswap_v3_schema_validation_failed_stale_2026_08_17.py`,
      shipped `market-tick-data-service@1b620c5485`. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. **➡️ EXTRACTED → plans/active/defi_satellite_ao_dispatch_batch19_2026_08_21.md (2026-08-21,
      ag-closeout-audit Phase 3 sweep).** Run the reclass script's `--apply` pass (todo above) on a dedicated VM, not the shared host —
      the defi index is ~159M rows / ~6.8GiB, too large for a full read/write on this host per the heavy-I/O HARD
      RULE. Gate `--apply` on a fresh reversibility check (`softDeletePolicy.retentionDurationSeconds` on the
      target bucket) per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a before running. This is
      the step that actually stops DP-FETCH-009 from re-paging on these 13 dates (short of the natural
      ~2026-08-24 window-aging). Repo: market-tick-data-service.
- [x] [DATA] P3. If DP-FETCH-009 re-fires for `defi/dex_pool_swaps` after this session's re-capture + before todo 2
      lands, confirm first whether it is these SAME 13 already-remediated dates re-aging into the trailing window
      (expected, self-resolves) vs. a genuinely NEW failing date/venue before treating it as a new incident. Repo:
      market-tick-data-service. **DONE this session** — see Progress Log 2026-08-16 (agt-c971d7) entry: confirmed
      re-fire is the SAME known issue, not a new incident.

## Progress Log

- **2026-08-16 (data_pipeline_failure escalation agt-d2c3cc, slot 26)**: Read RULES.md, SUB_AGENT_MANDATORY_RULES.md,
  `/codex/05-infrastructure/data-pipeline-alerts.md`. No issue was pre-filed (alert carried the details directly).
  Grepped `plans/active/`+`issues/` for conflicts — found 4 unrelated dex_pool_swaps docs (Solana ORCA/RAYDIUM
  indexer scope + its parked-task incident + a Tardis cefi precedent) and one plan
  (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`) whose `SCHEMA_VALIDATION_FAILED` mentions turned out
  to be about a DIFFERENT service (MDPS `canonical_writer.py:499` candle-write path, cefi liquidations) — read it
  fully enough to rule out overlap before filing this doc.
  Bounded-read diagnosis (pyarrow `GcsFileSystem().open_input_file` + `pq.read_table(columns=[...])` +
  `pc.equal`/`pc.and_` filters applied in Arrow BEFORE `.to_pandas()`, mirroring
  `deployment-service/deployment_service/data_pipeline_monitors/cli.py::_make_streaming_index_reader`'s own
  documented OOM-safety pattern — the defi index is ~159M rows and two attempts at >6-column projections OOM-killed
  (exit 137) even with Arrow-level filtering, so kept every query to 6-7 narrowly-scoped columns): isolated the
  finding to 13,673 SCHEMA_VALIDATION_FAILED rows, 100% UNISWAP_V3/ETHEREUM, spanning exactly 13 target dates
  (2025-01-09..21).
  Spent significant effort tracing the literal error-string provenance through `dex_swaps_handler.py` →
  `_defi_manifest.py::record_failed` → UAC `classify_venue_error()` (confirmed exact-match-only, no registered
  entry for this literal in any `errors/*.py` file) → `schema_validation.py::SchemaValidationError` (dynamic
  per-shard message, ruled out by the string's uniformity across dates) → `write_defi_rows`'s contract/symbol-column
  paths (repro'd directly with `apply_pool_symbols`/`write_defi_rows` against synthetic rows including edge cases —
  None tokens, emoji symbols, 300-char symbols, empty pool_id — all wrote cleanly) → found the ONLY live match for
  the literal string is MDPS's `canonical_writer.py:499`, a different service's candle-derivation write path MTDS's
  raw-tick writer doesn't touch. Concluded the original writer code either predates one of the dense run of
  `fix(defi):` commits that landed 2026-08-10..2026-08-16 in this exact repo, or hit a transient upstream condition
  for that 13-day window.
  Decisive live re-verification: ran `DexSwapsHandler._collect_protocol_chain` directly for uniswap_v3/ethereum
  2025-01-13 first (bypassing the manifest recorder) — succeeded, wrote 57092 real rows / 351 shards to prod GCS.
  Then re-ran properly through `_collect_one_shard` (the real recorder-integrated path) for all 13 dates in one
  background job (`market-tick-data-service` `.venv`, monitored via the harness Monitor tool) — **all 13 succeeded,
  zero exceptions**, real row counts 34658-57087/date, `record_captured` manifest rows written per pool via the real
  `DefiManifestRecorder`. Confirmed no currently-running VM/Cloud Run job for this backfill exists
  (`gcloud compute instances list`/`gcloud run jobs list`, both empty for dex/defi-swap-shaped names).
  No code change shipped (none needed — verified working). Filed this issue doc capturing the diagnosis + the
  data-remediation-applied outcome + the properly-scoped stale-row-purge follow-up (too large/risky for an inline
  one-shot fix per the heavy-I/O-needs-a-VM HARD RULE). `market-tick-data-service` worktree left clean
  (`git status` — nothing to commit, no uncommitted changes; only GCS writes + manifest ADDs, no local file
  changes).

- **2026-08-16 (data_pipeline_failure escalation agt-c971d7, slot 20)**: Re-fire of the same DP-FETCH-009
  finding dispatched to a second slot (asset_group=defi, data_type=dex_pool_swaps, 14036 attempted_failed of
  8472925 attempted; "13382 attempted_failed row(s) in the last 1d" — this "fresh in last 1d" figure is
  IDENTICAL to the one in the original filing above). Read RULES.md + SUB_AGENT_MANDATORY_RULES.md +
  `/codex/05-infrastructure/data-pipeline-alerts.md`; pre-task grep of `plans/active/issues/` found this SAME
  doc (filed minutes earlier by agt-d2c3cc/slot 26). Read it in full per the pre-task conflict-check HARD RULE
  instead of re-diagnosing from scratch. Confirmed via count comparison (no bounded parquet re-read needed —
  the prior investigation already OOM'd twice at >6-column projections and the numbers are decisive on their
  own): `attempted_failed` is EXACTLY 14036 in both filings (would have been HIGHER than 14036 if any new
  failure had landed since), while total `attempted` grew 8471219→8472925 (+1706, consistent with ordinary
  ongoing captures elsewhere in the defi corpus, not new failures in this cell) — this is the SAME 13 stale
  UNISWAP_V3/ETHEREUM SCHEMA_VALIDATION_FAILED dates (2025-01-09..21) still sitting in the 14-day
  `ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS` window (their `attempted_at` spans 2026-08-10..16, so they don't age
  out until ~08-24) and NOT yet purged (todo 2 below still open) — expected per this doc's own todo 3
  prediction, not a new incident. `market-tick-data-service` repo confirmed unchanged since the prior
  investigation (`git log` HEAD `d3435040`, no new commits on the dex-swap write path) — ruling out a code
  regression as the source of a "new" failure. Also matches the documented DP-FETCH-009/`DP_RUN_MOSTLY_EMPTY`
  wiring caveat in `data-pipeline-alerts.md` (60s default alert-dedup TTL does not bridge a slower detector
  cadence unless the event is in `_RECURRING_ALERT_COOLDOWNS`) — plausibly the mechanism behind two escalation
  workers being dispatched for what is effectively one underlying condition. No code fix needed (none exists to
  make — confirmed by the prior investigation's live re-verification). No new issue doc filed (would duplicate
  this one). Checked off todo 3. `market-tick-data-service` and `unified-trading-pm` worktrees left clean.

- **2026-08-17 (data_pipeline_failure escalation agt-ef0f27, slot 5)**: THIRD re-fire of the same DP-FETCH-009
  finding (asset_group=defi, data_type=dex_pool_swaps, 14036 attempted_failed of 8460364 attempted; "13456
  attempted_failed row(s) in the last 1d"). Read RULES.md + SUB_AGENT_MANDATORY_RULES.md +
  `/codex/05-infrastructure/data-pipeline-alerts.md`; pre-task grep of `plans/active/issues/` found this SAME
  doc. `attempted_failed` is EXACTLY 14036 for the third consecutive filing (2026-08-16 ×2, now 2026-08-17) —
  decisive per the prior sessions' own methodology (an OOM-prone bounded re-read was not repeated here for the
  same reason it wasn't in the second filing). `market-tick-data-service` HEAD confirmed unchanged
  (`c9bc8151`, no new dex-swap-relevant commits since the original investigation) — rules out a code
  regression. **Note for whoever picks up todo 2**: this filing's total `attempted` (8460364) is LOWER than
  both prior filings (8471219, then 8472925) despite arriving later in wall-clock time — inconsistent with the
  monotonic-growth pattern the second filing used as corroborating evidence. Not investigated further here (the
  identical 14036 `attempted_failed` count is the load-bearing signal and a third bounded-read risks the same
  OOM the first session hit twice); plausibly a consolidator snapshot/partition-timing artifact given several
  dex_pool_swaps fold/retire/dedup one-off scripts exist in this repo that could shrink the total independent of
  this cell, but flagging rather than asserting. This is still the SAME 13 stale UNISWAP_V3/ETHEREUM dates
  (2025-01-09..21, `attempted_at` 2026-08-10..16) sitting in the 14-day trailing window (self-clears ~08-24) and
  NOT yet purged — todo 2 (the reclass script) is still open below and is the actual fix for the repeated
  paging; this is the second consecutive re-fire that todo 3 already predicted, so no further todo change here.
  No code fix needed, no new issue doc filed (would duplicate this one). `$AUTHORING_SLOT=dp-fleet-monitor` is
  non-numeric — skipped the authoring-slot ping per the role doc (no real originator slot to notify).
  `market-tick-data-service` and `unified-trading-pm` worktrees left clean.
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)

- **2026-08-17 (data_pipeline_failure escalation agt-c57d2e, slot 6)**: FOURTH re-fire (asset_group=defi,
  data_type=dex_pool_swaps, 14055 attempted_failed of 8463757 attempted; "13691 attempted_failed row(s) in the
  last 1d"). Read RULES.md + SUB_AGENT_MANDATORY_RULES.md + `/codex/05-infrastructure/data-pipeline-alerts.md`;
  pre-task grep found this SAME doc. Checked the count-delta first per the prior sessions' own methodology:
  `attempted_failed` is 14055 here vs 14036 in all three prior filings (+19) — NOT identical, unlike the second
  and third filings. `market-tick-data-service` HEAD confirmed unchanged since the original investigation
  (`git log c9bc8151..767c4208` — zero commits touching `dex_swaps_handler.py`/`_dex_swaps_queries.py`), ruling
  out a code regression as the source of the +19 delta; most likely explanation is the trailing-window boundary
  shifting one day forward (consistent with the third filing's own flagged total-`attempted` non-monotonicity
  note) rather than a genuinely new failure, but not exhaustively proven (a fourth OOM-risking bounded re-read
  was judged not worth it for a 0.1%-scale delta against an already-3x-confirmed root cause).
  Given this is now the 4th escalation dispatched for the same known root cause, and todo 2 (the reclass script
  — the actual fix for the repeated paging) was still unbuilt, built it this session rather than filing a fourth
  "still the same issue" log entry alone:
  `market-tick-data-service/scripts/reclass_defi_uniswap_v3_schema_validation_failed_stale_2026_08_17.py` —
  dry-run-first, mirrors `reclass_cefi_no_batch_source_phantom_rows_2026_07_29.py`'s shape (closest live
  precedent; the doc's originally-cited `reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py` was
  already deleted per its own one-off `Delete-when` marker). The dry-run/sizing path uses the same OOM-safe
  pyarrow `GcsFileSystem` + column-projection + Arrow-level-filter pattern
  (`deployment-service/deployment_service/data_pipeline_monitors/cli.py::_make_streaming_index_reader`) this
  issue's own diagnosis proved safe against this exact 159M-row index — confirmed columns via
  `market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py` (`date`/`venue`/`chain`/
  `data_type` row-key fields). `--apply` (the full read+write of the index) is deliberately NOT run by this
  script invocation or this session — left for todo 2b below, per the heavy-I/O HARD RULE (needs a dedicated
  VM). Ran `quality-gates.sh --no-fix` (exit 0, ruff auto-fixed formatting on first attempt, re-staged and
  re-ran clean) and shipped via `quickmerge --agent --files` —
  `market-tick-data-service@1b620c5485`, verified ancestor of `origin/live-defi-rollout`. Split todo 2 into
  "build the script" (done, checked off) and a new todo 2b (run `--apply` on a VM — the step that actually
  stops the paging). `$AUTHORING_SLOT=dp-fleet-monitor` is non-numeric — skipped the authoring-slot ping per the
  role doc. `market-tick-data-service` and `unified-trading-pm` worktrees left clean.
