---
doc_type: issue
title:
  "KRW/USD manifest rows are NOT phantom — CORRECTED 2026-08-14: real data exists, mislabeled pipeline_mode (batch_yahoo
  claimed, batch_databento actual)"
summary: >-
  ORIGINAL CLAIM (2026-08-12, WRONG, kept below for the record): a stratified sample of 35 `FX:SPOT_PAIR:KRW-USD`
  manifest rows marked `capture_status=captured` found only 1/35 with a backing GCS object under
  `pipeline_mode=batch_yahoo` (the manifest's own claimed prefix) — the other 34 looked phantom. **This reproduced the
  exact wrong-vocabulary-probe mistake the archived
  `plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` investigation already caught and
  documented on 2026-08-04**: it checked only the manifest's claimed `pipeline_mode=batch_yahoo` prefix and never the
  second, previously-uninspected `pipeline_mode=batch_databento` prefix where real (Yahoo-sourced, mislabeled-path)
  content actually lives. A live re-check 2026-08-14 against the FULL 2,023-row `FX:SPOT_PAIR:KRW-USD` captured
  population (60-date stratified sample) found **0 genuinely phantom dates** — every single sampled date has a real
  backing object under `pipeline_mode=batch_databento`, `source=yahoo` confirmed genuine Yahoo content, zero under the
  manifest's claimed `batch_yahoo`. The real, narrower defect: all 2,023 rows carry a **mislabeled `pipeline_mode`**
  (manifest says `batch_yahoo`, real object path says `batch_databento`) — a manifest/reality mismatch that would make
  any reader querying strictly by the manifest's claimed prefix find nothing, even though the data genuinely exists and
  is genuinely 100% Yahoo-sourced. Needs a `pipeline_mode` RE-STAMP (mirroring the already-proven disposition the
  archived doc's superseding fix used for the blank-`instrument_id` population), never a recapture/delete.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, fx, krw, phantom-manifest-rows, data-correctness]
related:
  [
    /plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    /plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md,
  ]
parent_epic: tradfi_master
source: "/backfill-monitor smoke-test diagnosis, 2026-08-12 interactive session, KRW/USD MVP cell"
assigned_vm: NA
created: 2026-08-12
resolved_by:
locked_by:
locked_since:
priority: P2
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py,
  ]
---

# KRW/USD manifest rows: mislabeled pipeline_mode, NOT phantom (corrected 2026-08-14)

## CORRECTED 2026-08-14 — the "97% phantom" premise does not hold

> **CORRECTION**, same shape as the archived doc's own 2026-08-04 self-correction: the original 2026-08-12 check below
> probed only `pipeline_mode=batch_yahoo` (the manifest's own claimed value) and never the second,
> previously-uninspected `pipeline_mode=batch_databento` prefix. A live re-check of the full 2,023-row
> `FX:SPOT_PAIR:KRW-USD` `captured` population (60-date stratified sample, both prefixes) found **0 genuinely phantom
> dates** — every sampled date has a real backing object, 100% of the time under `batch_databento`, 0% under the
> manifest's claimed `batch_yahoo`. All 2,023 candidate rows carry `pipeline_mode=batch_yahoo` + `source=yahoo` in the
> manifest despite their real content living under a `batch_databento` path — a genuine mislabel, but not data loss: the
> content is real, and per `source=yahoo` confirmed genuinely 100% Yahoo-sourced (matches the operator's standing
> requirement that KRW/USD stay 100% Yahoo — already true architecturally too:
> `TickDataHandler._VENUE_FIXED_SOURCE_VENUES` hardcodes FX to the Yahoo fetch path unconditionally, `--source` is never
> consulted for this venue).

## What the original (WRONG) 2026-08-12 check found

- `launch-tradfi-bf-fx-ohlcv-24h.sh` has no per-pair scoping flag — it always fetches the entire `FX_SPOT_PAIRS`
  universe (12 pairs including KRW-USD) in one run.
- The `underlying` column being blank for FX spot-pair rows is **by design**, not a bug — spot pairs have no
  "underlying" concept; `_extract_underlying`/`_resolve_underlying_column` in
  `market_tick_data_service/engine/orchestrator/symbol_rules.py` correctly derives blank for this instrument_type. Real
  per-pair identity lives in `instrument_id`/`symbol` (`FX:SPOT_PAIR:KRW-USD`), which the write path does populate
  correctly. **This is NOT the bug this doc tracks** — noted here only to correct an earlier same-session hypothesis, so
  it isn't re-investigated.
- The real defect: a stratified sample of 35 `FX:SPOT_PAIR:KRW-USD` `capture_status=captured` manifest rows spanning
  2020-2026 showed only the single most-recent row has a real backing GCS object. The other 34 are phantom — the
  manifest claims `captured` but `gcs_describe_object` confirms no file exists (spot-checked `day=2020-01-02` directly).
  Because MTDS's freshness-skip check operates at venue+date granularity (not per-pair), a plain (non-`--force`)
  relaunch will skip these phantom dates entirely, since the manifest already claims them "captured" — a normal backfill
  cannot self-heal this.

## Why this is filed separately from the archived doc

`plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` already covers this exact defect
class corpus-wide (1,812 rows) and has its own gated design/apply remediation plan — it is ARCHIVED, so this doc adds a
fresh, dated confirmation as a live, active, trackable todo rather than editing archived history. Whoever picks up the
archived doc's remediation plan should treat this KRW/USD sample as corroborating evidence, not a new root cause.

## Todos

- [x] ✅ [OPERATOR] P3. **ANSWERED 2026-08-14: fold in now, not deferred** — operator confirmed, adding the standing
      requirement that KRW/USD stay 100% Yahoo-sourced (already true architecturally, see correction above — no code
      change needed for that half).
- [ ] [DATA] P2. **REVISED disposition (was: surgical recapture; now: pipeline_mode re-stamp) — script shipped, apply in
      progress.** Full 2,023-row verification (not just the 60-date sample): 0 phantom, 1,949 mislabeled
      `batch_yahoo`→`batch_databento`, 59 already-correct, 15 with backing under both (left untouched, out of scope).
      Dry-run matched the full verification exactly. Script shipped: `market-tick-data-service@75a9ed0b54`
      (`scripts/restamp_tradfi_fx_krw_usd_mislabeled_pipeline_mode_2026_08_14.py`, snapshot-before-write + CAS +
      self-verify). First `--apply` attempt safely aborted (CAS generation mismatch — a concurrent writer touched the
      manifest mid-run; script confirmed no partial write occurred) — retrying.
- [ ] [DATA] P3. Once the KRW/USD re-stamp is confirmed applied, check whether the same `batch_yahoo`-claimed/
      `batch_databento`-actual mislabel affects the other 11 FX pairs too (this doc only sampled KRW-USD) — if so, widen
      the re-stamp to the full FX venue rather than re-discovering this pair-by-pair.

## Progress Log

- 2026-08-12 — Filed on a single-prefix (`pipeline_mode=batch_yahoo`) probe; premise later found wrong.
- 2026-08-14 — Operator decision: fold into remediation now, KRW/USD must stay 100% Yahoo (already true
  architecturally). Re-checking against both known FX prefixes (mirroring the archived doc's own 2026-08-04
  self-correction) found the "phantom" premise false — 0/60 sampled dates genuinely phantom, 100% resolve under
  `pipeline_mode=batch_databento`. Real defect is a manifest `pipeline_mode` mislabel (2,023 rows), not missing data.
  Corrected the doc's title/summary/todos in place rather than filing a second doc, since the original claim never
  shipped anything and would only mislead a future reader. Next: build + dry-run the re-stamp script (see revised P2
  todo), verify all 2,023 rows before any write.
