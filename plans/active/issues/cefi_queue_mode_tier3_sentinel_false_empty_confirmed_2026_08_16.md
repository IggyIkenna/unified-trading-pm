---
doc_type: issue
title:
  "CeFi Tier-3 sentinel wrote empty_confirmed over already-captured shards — a SINGLE_VM_QUEUE=1
  backfill silently overwrote real 2020 data as 'confirmed empty'"
summary: >-
  A SINGLE_VM_QUEUE=1 CeFi Tardis backfill (`cefi-queue-heavy-binancefutu-x17-20260815-220349`, 17 venues bundled,
  "heavy" tier) wrote 13,476 manifest rows with `capture_status=empty_confirmed` across 13 CeFi venues, dates
  2020-01-01 through 2020-09-12, in a ~17h window on 2026-08-15/16. At least one is directly confirmed FALSE:
  `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` trades `2020-01-02` was marked `empty_confirmed` despite a real captured
  parquet for that exact shard existing in GCS since 2026-04. Root cause: `sentinels.py::_emit_tier3_for_dt`'s
  Tier-3 fan-out (a third, distinct mechanism from the two SOURCE_RETURNED_ZERO miscategorization bugs already fixed
  today in `empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`) decides captured-vs-empty using ONLY the
  current run's own in-memory fetch results — it never checks the manifest or GCS for a prior `captured` row before
  writing `empty_confirmed`, so any per-instrument fetch that silently returns nothing (rate-limit, transient error,
  or a genuine but redundant re-check) permanently overwrites the true state. Separately, the VM itself was also a
  massive throughput/billing-waste incident (only 38 distinct days covered in 17h, re-walking already-captured 2020
  data with zero skip-check logging visible — see the companion VM-relaunch issue doc); this doc covers the
  data-correctness half specifically.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, tardis, manifest, empty_confirmed, data-correctness, big-finding]
related:
  [
    /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md,
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
# was: cefi_master (epic-assignment audit 2026-08-19) -- root cause + fix are in sentinels.py::_emit_tier3_for_dt, a generic asset-group-parameterized MTDS orchestrator sentinel emitter shared identically by CEFI/TRADFI/DEFI/SPORTS, not CeFi-specific code
parent_epic: mtds_mdps_master
source: "Interactive session 2026-08-16, slot 4 — operator asked to check queue-VM ETA/correctness, discovered live
  manifest corruption in progress, killed the VM, root-caused + fixed on operator's explicit /autonomous authorization"
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
    /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py,
  ]
---

# CeFi Tier-3 sentinel false empty_confirmed — root cause + correction

## What happened

`cefi-queue-heavy-binancefutu-x17-20260815-220349` (`SINGLE_VM_QUEUE=1`, all 17 default CeFi venues bundled, "heavy"
tier = trades + book_snapshot_5 + derivative_ticker + futures_chain + liquidations) ran 2026-08-15T22:03Z through
~2026-08-16T15:04Z (~17h, killed by operator once the corruption was found) and only advanced its shared date
checkpoint to `2020-09-12` — 38 distinct calendar days across 11-13 venues. In that window it wrote 13,476
`capture_status=empty_confirmed` manifest rows.

Directly verified false: `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` / `trades` / `2020-01-02` — GCS blob
`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2020-01-02/pipeline_mode=
batch_tardis/asset_group=cefi/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/
BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet` exists (confirmed `blob.exists()==True`), yet the manifest was
written `empty_confirmed` for this exact key at `2026-08-15T23:07:21Z`. The manifest never had a prior `captured`
row for this key either — only `expected_unattempted` (2026-04-22) and now the false `empty_confirmed` — a separate,
likely pre-existing gap (the April capture apparently never recorded its own manifest row) that this incident's
write then compounded.

## Root cause (confirmed via code read, not the read-side freshness-check)

`market_tick_data_service/engine/orchestrator/sentinels.py::_emit_tier3_for_dt` (line 632) fans out per expected
instrument for a (venue, data_type). Line 667: `captured_instruments = captured_per_instrument_shards.get((venue,
dt), set())` — populated ONLY from the CURRENT run's own in-memory fetch results, never from a manifest read or a
GCS existence check. Line 682-684 skips an instrument only if it's in that in-memory set; otherwise it falls through
to the terminal `else` (line 753-765) and writes `record_empty(reason="SOURCE_RETURNED_ZERO", ...)` unconditionally.
The in-line comment at 758-760 documents the ASSUMED invariant ("reached only when no failure surfaced... = proven
honest absence") — an assumption that doesn't hold when one instrument's fetch silently returns nothing while
siblings in the same (venue, dt) succeed (no venue-level `failed_reason_raw` fires), the same class of
"swallowed per-instrument failure" as the two sibling bugs already fixed today (Deribit DVOL sustained-429 with no
failure flag; Hyperliquid per-coin `return_exceptions=True` swallowing) — see
`empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`. This is a third, distinct instance of the same bug
CLASS, not a duplicate of either already-fixed mechanism.

This is separate from (and undiagnosable-because-of) a related silent-logging gap: `tick_data_handler.py::
_apply_freshness_skip`'s final fallback (line 548, reached when every venue is judged stale/missing) logs nothing,
unlike its SKIP/PARTIAL sibling branches — the queue VM's 202,349-line run.log had zero SKIP/PARTIAL/freshness
lines despite genuine fetch activity, which is what let this run silently for 17h before anyone noticed.

## Fix

1. **Code**: `_emit_tier3_for_dt` now checks for a pre-existing `captured` row before writing `empty_confirmed` (a
   single batched manifest read per (venue, dt) call, not per-instrument — avoids an N+1 query explosion across
   potentially thousands of expected instruments). `_apply_freshness_skip`'s silent branch now logs.
2. **Data**: `scripts/migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py` migrates every `empty_confirmed`
   row written by this incident's exact window (`written_at >= 2026-08-15T21:00:00Z`, 13,476 candidates measured) to
   `capture_status=attempted_failed`. Operator ruling 2026-08-16: do not attempt to prove each row individually
   true/false-empty — a corrective re-attempt is self-correcting either way once the write-side bug above is fixed
   first (a genuinely-empty shard re-confirms empty correctly; a wrongly-marked shard gets correctly re-captured).
   CAS write (`if_generation_match`), snapshot-before-write, self-verify after, per
   `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §5 — including the read-only consolidator-PAUSED
   precondition check (hard-aborts if not paused).

## Todos

- [x] ✅ [CODE] P0. **SHIPPED 2026-08-16.** `market-tick-data-service@f134d16595c3e5d1761ec76a7f40041535a6f4e3` —
      `sentinels.py::_emit_tier3_for_dt` now calls a new `_tier3_prior_capture_guard.py::
      fetch_prior_captured_instrument_ids()` (a single filtered `read_availability_index` call per (venue, dt)
      invocation, never per-instrument) and unions the result into `captured_instruments` before the per-instrument
      loop — an already-captured shard from ANY prior run can no longer receive any Tier-3 sentinel write, not just
      the `SOURCE_RETURNED_ZERO` branch. `tick_data_handler.py::_apply_freshness_skip`'s silent final-fallback branch
      now logs a `RETRY-ALL` line. 5 new regression tests. QG green (10,957 passed, 81.92% coverage). Shipped via the
      documented dirty-deps direct-carveout (`Quickmerge: direct-carveout-dirty-deps` trailer) — quickmerge's normal
      path was blocked by unrelated foreign WIP in `unified-api-contracts`.
- [x] ✅ [DATA] P0. **APPLIED 2026-08-16.** `scripts/migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py`
      (shipped `market-tick-data-service@338d91f0`, same dirty-deps carveout). Corrected targeting from an initial
      written_at-only pass (which over-caught 261,547 rows, 86% from an unrelated launcher family with legitimate
      `EXPECTED_*` reasons) to the precise signature: `capture_status=empty_confirmed` +
      `error_reason=SOURCE_RETURNED_ZERO` + `written_at>=2026-08-15T21:00:00Z` — 163,421 candidates, matching the
      exact bug's identifying string rather than a VM-name/venue heuristic (any CeFi launcher sharing the buggy code
      path could have written the same false signature). Consolidator cron
      (`uts-prod-manifest-consolidator-market-data-cefi-cron`) confirmed PAUSED before the write, RESUMED after. CAS
      write succeeded (generation `1786856513254256` → `1786899624148135`), self-verify 0 remaining, pre-write
      snapshot backed up to `_index/backups/availability_index.pre_cefi_queue_mode_false_empty_migration_
      20260816T165742Z.parquet`. Independently re-verified (fresh manifest read, not the script's own self-verify):
      the originally-confirmed-false `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` trades `2020-01-02` row now reads
      `capture_status=attempted_failed`.
- [x] ✅ [DATA] P0. **VM3 relaunched correctly 2026-08-16.** `cefi-binance-futures-2026-heavy-20260816-182747`,
      confirmed RUNNING, `LAUNCH_PARAMS.json` confirms `ONLY=BINANCE-FUTURES:2026:heavy SINGLE_VM_QUEUE=0
      TARDIS_CONCURRENCY_LEASE=1` (single-venue mode, not the queue-bundling mode this whole incident traces back
      to) — resuming from the real `2026-04-13` checkpoint per
      `vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md`'s own open P2. Now running
      on top of both fixes above, so its freshness-skip and Tier-3 sentinel writes should behave correctly.
- [ ] [DATA] P3. The pre-existing gap where the April 2026 BTC-USDT trades capture never recorded a manifest
      `captured` row at all (separate from today's false-empty write) is NOT chased in this doc — the
      `attempted_failed` migration above will cause a natural re-verification pass that either finds and records the
      real capture or genuinely re-fetches it; no separate backfill action needed unless the re-verification pass
      itself surfaces a new, distinct problem.
- [x] ✅ [DATA] P3. **EXTRACTED 2026-08-19 (ag-closeout-audit, cefi tranche)** — Delete
      `scripts/migrate_cefi_queue_mode_false_empty_confirmed_2026_08_16.py` once the re-verification pass above
      confirms the corrected rows resolved cleanly (its own `# Delete-when:` header names this doc's resolution as
      the trigger). Live todo now `cefi_satellite_ao_dispatch_batch22_2026_08_19.md` (currently `status: draft`,
      pending operator approval to dispatch — the item is tracked there, not re-worked here once approved).

## Progress Log

- 2026-08-16 — Filed. Operator asked to investigate the running queue VM's ETA/correctness/throughput; discovered
  live manifest corruption mid-investigation (false `empty_confirmed` over real captured data), killed the VM,
  root-caused via sub-agent investigation, fixed under explicit `/autonomous` operator authorization. Cross-linked
  (not duplicated) into `empty_confirmed_and_coverage_correctness_audit_2026_08_15.md`, which already tracks the
  sibling SOURCE_RETURNED_ZERO miscategorization bug class this is a third instance of.
- 2026-08-16 (same session, execution pass) — All three P0 todos closed: code fix shipped and verified live
  (`market-tick-data-service@f134d16595c3e5d1761ec76a7f40041535a6f4e3`), manifest migration applied and independently
  re-verified (163,421 rows corrected, CAS-confirmed, consolidator-pause-gated per
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §5), and the VM3 relaunch this whole investigation
  started from is now running correctly on top of both fixes. Also shipped, same batch: the KRW/USD re-stamp
  race-fix script that had been blocked since earlier in this session on the same `unified-api-contracts` dirty-deps
  issue (`market-tick-data-service@338d91f0`, unrelated to this doc's own bug but shipped in the same commit for
  efficiency — see `tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md` for that finding's own record).
  A genuinely foreign, live-adjacent blocker surfaced mid-launch: `deployment-service` had 72-minute-old foreign WIP
  (a terraform lockfile diff + one new test file) blocking its own tarball rebuild — handled via a scoped, named
  `git stash push`/`pop` around the tarball-build step only (never touched the content, restored immediately after,
  confirmed byte-identical via `git status` before/after) rather than force-including it via `--allow-dirty-tarball`
  or waiting indefinitely.
- **na-eligibility-audit 2026-08-16** [body-hash:001b7452f28b77e7]: KEEP-NA, valid — Full end-to-end read (146 lines) confirms this is a same-day (2026-08-16), fully-executed incident-response issue doc, not a stale backlog item.
- **context-scout 2026-08-17**: populated context_scope (4 entries) — field already carried accurate content from
  filing; this is its first context-scout marker.
- **ag-closeout-audit 2026-08-19 (cefi tranche, dispatch agt-5a343c)**: item 2 (delete the migration script once
  re-verification confirms clean) extracted to `cefi_satellite_ao_dispatch_batch22_2026_08_19.md` — conflict-checked
  clear against every existing active cefi batch/finalize plan and the wider corpus (zero hits). Item 1 (the
  contingent April-2026 gap watch-item) is unaffected — still not currently actionable, no action needed unless the
  re-verification pass itself surfaces a new distinct problem. Doc stays `open`/`assigned_vm: NA` (1 item remains,
  contingent and not itself extractable).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries) — all existing entries still resolve (the sibling
  audit plan, the delete-safety SSOT, and the two MTDS sentinel/handler source paths).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms 2026-08-19 verdict; sole open item (the
  April-2026 gap watch-item, contingent, not currently actionable) unchanged.
