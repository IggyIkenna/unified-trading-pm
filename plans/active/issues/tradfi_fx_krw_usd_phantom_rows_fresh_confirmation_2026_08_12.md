---
doc_type: issue
title: "KRW/USD manifest rows are 97% phantom — fresh confirmation, matches the known FX-venue-wide defect class"
summary: >-
  While diagnosing the tradfi MVP "KRW/USD" backfill cell (per tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md),
  a stratified sample of 35 `FX:SPOT_PAIR:KRW-USD` manifest rows marked `capture_status=captured` across 2020-2026 found
  only 1/35 (the most recent) actually has a backing GCS object — the other 34 are phantom manifest rows (claim
  `captured`, no file exists; confirmed absent for e.g. day=2020-01-02). This matches the exact defect class documented
  in the ARCHIVED `plans/archive/issues/tradfi_fx_manifest_phantom_and_duplicate_rows_2026_08_03.md` (1,812 corpus-wide
  phantom rows found 2026-08-03, gated on a not-yet-executed design/apply remediation plan) — this is a fresh, dated
  re-confirmation on a specific pair, not a new discovery, filed as its own tracked todo per this workspace's "every
  deferral is a `- [ ]` todo, never prose" hard rule (the finding was reported only in chat/an agent's final summary
  before this doc, at risk of being lost).
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

# KRW/USD manifest rows are 97% phantom — fresh confirmation

## What was found (2026-08-12)

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

- [ ] [DATA] P2. Fold this fresh KRW/USD confirmation into the archived remediation plan's execution — do NOT blind
      `--force-recapture` across all 12 FX pairs × 7 year-shards (that would re-walk real, already-correct data too,
      exactly the "whole-corpus refetch" class `vm-launcher-runbook.md`'s own HARD RULE says to check for a surgical fix
      on first). A surgical, phantom-row-targeted re-capture (only the specific `(pair, date)` cells confirmed phantom)
      is the correct shape, mirroring the archived doc's own design intent.
- [ ] [OPERATOR] P3. Decide whether to fold this into the archived doc's plan now, or defer until a broader FX-pair pass
      is scheduled — flagged, not resolved, per the operator's own "fold into existing plan or defer?" framing when this
      was first reported.
