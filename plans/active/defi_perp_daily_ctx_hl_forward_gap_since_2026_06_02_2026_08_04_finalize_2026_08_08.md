---
doc_type: plan
title: Finalize — HYPERLIQUID perp_daily_ctx forward-write gap close-out
summary: >-
  Gated finalize companion for /plans/archive/2026_08/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md (reclassified
  NA→planning, na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08) — re-verifies the forward-write build's
  evidence (the new HL `/info` mark-price fetch, the CeFi partition-path write, the manifest registration, and the
  follow-up CeFi Tardis writer diagnostic), then archives both docs per plan-completion-and-archival-discipline once
  every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, perp-daily-ctx, hyperliquid, finalize, archival, ao-build]
related:
  [
    /plans/archive/2026_08/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
    /plans/archive/issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: [defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep) — every AO-dispatched plan/reclassified issue doc needs a
  gated finalize companion (/plans/active/task_template.md §4).
context_scope:
  [
    /plans/archive/2026_08/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_hyperliquid.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
  ]
---

# Finalize — HYPERLIQUID perp_daily_ctx forward-write gap close-out

Machine-held (`gate_on_depends: true`) until every todo in
`/plans/archive/2026_08/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` is done. Do not start manually before then.

## Todos

- [x] ✅ [REVIEW] P2. Re-verify the build's evidence: (1) the `[CODE] P2` todo's cited commit shipping the new HL `/info`
      mark-price/volume/OI fetch in `_perp_funding_hyperliquid.py`, wired into `_collect_hyperliquid()`'s existing
      per-coin loop — confirm via `git log`/`git show` against a fresh `git pull --ff-only origin live-defi-rollout` on
      `market-tick-data-service` (don't trust the build todo's own evidence line uncritically); (2) confirm the write
      path used the CeFi partition shape (`build_cefi_partition_path`, `get_write_bucket_name("market_data", "cefi")`,
      `DefiManifestRecorder(asset_group="cefi")`) and NOT the old dead-bucket convention; (3) confirm a live/backfill
      run produced real `perp_daily_ctx` manifest rows for HYPERLIQUID on a fresh date (a bounded manifest read,
      `venue=HYPERLIQUID, data_type=perp_daily_ctx`, date > 2026-06-01 — no whole-corpus walk) and that existing
      `perp_funding` tests stayed green; (4) confirm the `[DIAG] P3` follow-up (CeFi Tardis `perp_funding_corpus.py`
      writer re-check) was actually run and its finding recorded, not left as an open question. Done-when: all 4 points
      independently re-verified with cited evidence; any mis-citation found is corrected in the source doc directly.
      **RE-VERIFIED 2026-08-17 (slot-9, review) — all 4 points independently confirmed, no mis-citation found:**
      1. `market-tick-data-service@f5753479` confirmed present on a fresh `git pull --ff-only origin live-defi-rollout`
         (`git log --oneline -1 f5753479` resolves; `git show --stat` matches the cited file list). The commit's diff
         shows `_collect_hyperliquid()` now calls `_collect_perp_daily_ctx()` at its tail (gated on `recorder is not
         None`), which itself calls the new `_fetch_asset_ctxs()` (HL `/info` `metaAndAssetCtxs`) and writes via the
         new `_write_hyperliquid_perp_daily_ctx_rows()` — confirmed wired into the existing per-coin-batch loop, not a
         parallel/duplicate path.
      2. Confirmed by direct read: `_collect_perp_daily_ctx()` writes via `_write_hyperliquid_cefi_rows(...,
         data_type="perp_daily_ctx", ...)` which calls `build_cefi_partition_path(venue="HYPERLIQUID",
         instrument_type=InstrumentType.PERPETUAL, data_type=data_type, ...)`; `perp_funding_handler.py`'s diff shows
         the caller passes `bucket = get_write_bucket_name("market_data", "cefi")` and
         `recorder = DefiManifestRecorder(..., asset_group="cefi", ...)` through `_dispatch_protocol` →
         `_collect_hyperliquid(..., recorder=recorder, chain_for_manifest=chain_for_manifest, attempted_at=attempted_at)`
         — the CeFi partition shape, not the old dead-bucket convention.
      3. Bounded manifest read (`read_availability_index_safe(get_write_bucket_name("market_data", "cefi"),
         columns=["date","venue","data_type","capture_status","row_count","written_at","source"],
         filters=[("venue","==","HYPERLIQUID"),("data_type","==","perp_daily_ctx"),("date",">","2026-06-01")])`, row-group
         pushdown, no whole-corpus walk) returned 7 real `capture_status=captured` rows, one per day
         2026-08-09..2026-08-15, 232 rows/day, `source=hyperliquid` — the forward gap is genuinely closed in
         production. `market-tick-data-service`'s full unit suite (`bash scripts/quality-gates.sh --test --no-fix`,
         includes `tests/unit/test_perp_funding_hyperliquid.py`) ran green: **11001 passed, 28 skipped, 1 xpassed, 0
         failed**. (The QG run's separate live-mode network smoke matrix shows unrelated `FAIL`s for
         BINANCE-FUTURES/BYBIT/DERIBIT `perp_funding` — pre-existing "no network in this sandbox" L1-only blocks, not
         HYPERLIQUID/perp_daily_ctx, and not a regression from this change.)
      4. `[DIAG] P3` confirmed actually run and its finding recorded: the source issue doc's 2026-08-15 Progress Log
         entry (slot-23, data_engineering) documents the CeFi Tardis `perp_funding_corpus.py` writer re-check in full —
         historical run confirmed (2026-05-16..22), promotion+cron code shipped 2026-08-06, but a fresh 2026-08-15
         bounded probe found the corpus still not fresh, root-caused to the `cefi-perp-funding-daily-cron-*` VM never
         having been launched (+ the forward-poll cron host terminated) — not left as an open question; a concrete
         `[DATA] P1` follow-up was filed in the sibling `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` doc
         rather than duplicated here, per that entry's own note.
- [ ] [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `/plans/archive/2026_08/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` and this finalize doc itself: archive
      both to `plans/archive/2026_08/issues/` (or `plans/archive/2026_08/` for this finalize doc, matching this corpus's
      existing split convention), and fix every corpus referrer path (grep the repo for the old paths —
      `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` and `defi_satellite_ao_dispatch_batch6_2026_07_30.md`
      both cite the source doc — and update each hit). Done-when: `regenerate_active_plan_inventory.py` shows zero
      orphan referrers to the archived paths.

## Progress Log

- **2026-08-08 (na-eligibility-audit round7 RECLASSIFY sweep)**: finalize plan authored alongside the RECLASSIFY flip of
  the source issue doc, per `task_template.md`'s finalize-plan-coverage rule.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (4 entries).
- **2026-08-17 (slot-9, review)**: `[REVIEW] P2` closed. All 4 re-verification points independently confirmed (see
  inline evidence on the checkbox above): commit `market-tick-data-service@f5753479` present on origin/live-defi-rollout
  and correctly wired; write path uses the CeFi partition shape (not the dead-bucket convention); a bounded manifest
  read confirmed 7 real captured `perp_daily_ctx` rows for HYPERLIQUID (2026-08-09..15, 232 rows/day); the full unit
  suite (11001 passed, 0 failed) stayed green; `[DIAG] P3` was confirmed run with its finding recorded in the source
  issue doc. No mis-citation found — nothing needed correcting in the source doc. `[DOC] P2` (the archival ritual) is
  the plan's remaining todo — not in this task's scope.
- **context-scout 2026-08-17**: re-verified context_scope, no change needed (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
