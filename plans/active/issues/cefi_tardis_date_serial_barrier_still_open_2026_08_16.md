---
doc_type: issue
title:
  "CeFi Tardis backfill still runs date-serial — the 2026-07-17 throughput doc's own final fix was never shipped, and
  its ~14x estimate is now stale"
summary: >-
  Live-measured on the running BINANCE-FUTURES resume VM (2026-08-16): real end-to-end throughput is ~4 MB/s
  (download-leg ~4.01 MB/s, upload-leg ~3.22 MB/s, measured from 3,984 real per-shard timestamps), against a
  documented resolved ceiling of 17.56 MB/s from `cefi_tardis_throughput_collapse_350x_2026_07_17.md` and a real cold
  32-wide `curl` ceiling of 21.3 MB/s. Root cause confirmed still present: `market_tick_data_service/engine/
  orchestrator/__init__.py::process_ticks` fans out one calendar date's venues via `asyncio.gather()`, then writes
  that date's manifest, before the caller starts the next date — the archived doc's own final, never-closed todo
  ("kill the date-serial barrier"). A full design pass (2026-08-16, this doc's linked plan) found the fix mostly
  ALREADY EXISTS (`unified-trading-library`'s `--batch-date-concurrency` driver, already live on the TradFi/Deribit
  fleet, just never enabled for CeFi's launcher) but also found 6 real correctness bugs that must be fixed first —
  including a SPOT-preemption checkpoint (`monotonic` watermark) regression that is CONFIRMED ALREADY HAPPENING on
  the live TradFi fleet today, independent of CeFi. **Correcting the record on scale**: the archived doc's "~14x"
  estimate predates 5 more fixes that landed the same day and decoupled fetch concurrency from in-flight task count —
  today's honest comparable is TradFi's own measured real-world result, 1.56x at concurrency=20. Expect low
  single-digit-x, not 10x.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [cefi, tardis, throughput, barrier, big-finding, cross-cutting]
related:
  [
    /plans/active/cefi_tardis_date_concurrency_2026_08_16.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md,
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
# was: cefi_master (epic-assignment audit 2026-08-19) -- the barrier lives in process_ticks, the shared asset-group-parameterized MTDS orchestrator entrypoint (CEFI/TRADFI/DEFI/SPORTS all route through it); the fix is already live on TradFi/Deribit and one of the 6 correctness bugs is a confirmed TradFi production regression independent of CeFi
parent_epic: mtds_mdps_master
source: "Interactive session 2026-08-16, slot 4 — operator asked for the real e2e download-to-GCS rate on the live
  BINANCE-FUTURES resume VM after flagging '30 min/day' as too slow; measurement led to a full design investigation"
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P0
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/cefi_tardis_date_concurrency_2026_08_16.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py,
    unified-trading-library/unified_trading_library/service_framework/_adapter.py,
  ]
---

# CeFi Tardis backfill still runs date-serial — corrected estimate + design

## The measurement (2026-08-16, live)

VM: `cefi-binance-futures-2026-heavy-20260816-182747` (single-venue BINANCE-FUTURES heavy tier, resuming from a real
`2026-04-13` checkpoint per `vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md`,
`TARDIS_MAX_CONCURRENT_DOWNLOADS` at bare default 32-wide).

- 3,984 completed shards / 22.63 GB / 1.15B rows in ~95 minutes wall clock.
- Download-leg aggregate rate (measured from real `Tardis streaming request` → `Tardis streaming success` per-shard
  timestamps): **4.01 MB/s**.
- Upload-leg aggregate rate (from `StreamingParquetWriter: uploaded` timestamps): **3.22 MB/s**.
- Both legs move together, not one gating the other — the signature of work-starvation (idle concurrency slots), not
  a hard per-leg cap.

## Why this matches, and updates, the archived doc

`plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md` diagnosed the identical signature in July
("only ~3-4 of ~30 connections transferring at any instant") and root-caused it to the SAME `process_ticks`
date-serial `asyncio.gather()` barrier — fixed 5 other stacked bugs the same day (DNS starvation, finalise-offload,
decoupled fetch-to-disk, a GIL-bound finalise round-trip) reaching a resolved 17.56 MB/s steady state, but never
shipped the barrier fix itself. That doc's final unfixed todo is this doc's subject.

**Correction to the archived doc's own estimate**: its "~14x (1.5 → up to ~21 MB/s)" figure was written at 13:55Z
that day, BEFORE the in-flight-task/fetch-semaphore decoupling fix landed later the same session (20:40Z entry). With
that fix live, 128 in-flight tasks already queue behind the 32-slot fetch semaphore — the pipeline is not
structurally starved the way it was when 14x was estimated. The design pass this doc links to found the honest
comparable already measured in production: **TradFi's own `--batch-date-concurrency=20` gets 1.56x**
(`tradfi_backfill_throughput_followups_2026_07_24.md`). Expect a similar order of magnitude for CeFi, not 10x. Do not
cite "~14x" anywhere else in the corpus without this correction (`cefi_consolidated_closeout_2026_07_18.md:269` and
`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md:69` both still carry the stale figure — fix in the same pass
that closes this doc).

## The real fix, and why it's bigger than "flip a flag"

Full design: `/plans/active/cefi_tardis_date_concurrency_2026_08_16.md` (this doc's linked plan — read it for the
complete architecture map, correctness analysis, and phased rollout). Headline: the concurrency mechanism
(`unified-trading-library`'s `--batch-date-concurrency`, already shipped and already running on TradFi/Deribit) can
be enabled for CeFi's launcher with a small, additive change — but 6 real correctness bugs must be fixed first, and
**one of them is a live, already-happening production issue on the TradFi fleet today, independent of CeFi**: the
SPOT-preemption checkpoint mechanism (`unified_trading_library/manifest_writer/_vm_progress.py`'s `monotonic`
watermark) is very likely already going false under TradFi's live concurrency=20, silently degrading preemption
recovery to full-chunk replay or a page — this needs its own verification + fix regardless of the CeFi decision.

## Todos

- [ ] [BACKEND] P0. Execute the phased plan at `/plans/active/cefi_tardis_date_concurrency_2026_08_16.md` — Phase 0
      measurement gates, Phase 1 correctness fixes (F1-F8), Phase 2 checkpoint watermark, Phase 3 CeFi enablement +
      canary. See that plan for full todo detail.
- [ ] [DATA] P1. Verify the TradFi live-fleet checkpoint regression: read a real TradFi VM's `PROGRESS.json` and
      confirm `monotonic` is already `false` under `--batch-date-concurrency=20`. If confirmed, this needs its own
      urgency independent of the CeFi barrier work — file as its own P0 if the TradFi backfill owners aren't already
      tracking it.
- [x] ✅ [DOC] P3. **DONE 2026-08-19 (ag-closeout-audit, cefi tranche)** — Corrected the stale throughput claim
      everywhere it's cited in the corpus (`cefi_consolidated_closeout_2026_07_18.md`,
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) — both now carry a dated correction note pointing at
      this doc's live-measured figure (~4 MB/s, not the stale ~14 MB/s "fixed" claim).

## Progress Log

- 2026-08-16 — Filed. Operator flagged live BINANCE-FUTURES VM throughput as "way too slow", asked for the real e2e
  download-to-GCS rate; measurement (4 MB/s vs 17.56 MB/s documented resolved ceiling) confirmed the archived doc's
  barrier was never fixed. A full design investigation (dispatched same session, opus-tier given the stakes) found
  the fix mechanism already exists in UTL and is already live on TradFi, but surfaced 6 real correctness bugs
  (including a live TradFi production regression) that gate enabling it for CeFi. Operator ruled: human plan (not
  AO-dispatched), execute today, test on the live VM.
- **na-eligibility-audit 2026-08-17** [body-hash:130f149e38436c8b]: KEEP-NA, valid. First audit pass (fresh doc, created 2026-08-16, no prior marker). Doc's own Progress Log carries an explicit dated operator ruling: human plan (not AO-dispatched), execute today, test on the live VM -- citation-hold class (a)-adjacent, covering the whole doc. Item 1 redirects to cefi_tardis_date_concurrency_2026_08_16.md. Items 2 (TradFi checkpoint verify) and 3 (stale-estimate correction) read individually bounded but are bundled under the same-day human-track ruling for a 1-day-old doc still being actively executed as a unit -- flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE (low confidence) for next-run reassessment rather than extracted now. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries), unchanged -- the linked design plan, the archived
  throughput-collapse doc, and the two source paths (MTDS orchestrator barrier, UTL concurrency adapter) still cover
  the doc's subject matter.
- **ag-closeout-audit 2026-08-19 (cefi tranche)**: mechanical corpus-hygiene fix, done in-run per the skill's HARD
  rule (fix in-run, never park). Item 3 (stale throughput-figure correction) shipped: both cited docs
  (`cefi_consolidated_closeout_2026_07_18.md`, `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) now carry a
  dated correction note. Items 1 and 2 remain open -- item 1 redirects to `cefi_tardis_date_concurrency_2026_08_16.md`
  (itself audited this run: orphaned, time-gated on the same Tardis N=1 slot occupied by the live BINANCE-FUTURES
  backfill); item 2 (verify TradFi checkpoint regression) stays bundled under this doc's own explicit 2026-08-16
  operator ruling ("human plan, not AO-dispatched, execute today") -- not extracted into a batch. No real covering
  plan (assigned_vm: planning + status: active with an open Todos-section citation) claims either remaining item.
  Overall verdict for the cefi closeout-completeness sweep: orphaned_partial_coverage, non-batchable
  (operator-gated/time-gated per the standing 2026-08-16 ruling), one item resolved this run.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries) — all existing entries still resolve (the linked
  design plan, the archived throughput-collapse doc, the MTDS orchestrator barrier, and the UTL concurrency adapter).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; items 1/2 stay under the doc's own
  explicit 2026-08-16 operator ruling (human plan, execute today); item 3 (stale-citation fix) already closed
  2026-08-19.
