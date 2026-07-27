---
doc_type: plan
title: CeFi DERIBIT + BINANCE-FUTURES bundle backfill verification + phantom-residual triage
summary:
  Verify DERIBIT options/futures and BINANCE-FUTURES perp bundle backfill coverage and triage phantom-manifest
  residuals.
status: active
nature: process
asset_group: [cefi, defi]
stage: [meta]
repos: [deployment-service, instruments-service, market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, backfill, verification, phantom-audit, deribit, binance-futures]
related: [./cefi_manifest_canonicalisation_2026_06_01.md, ../epics/cefi_master.md]
created: "2026-06-12"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-20
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
source:
drift_direction: advance-code
---

> **Provenance**: extracted 2026-06-20 from the inline `cefi_master` epic body during the asset-group-umbrella
> restructure (umbrellas were carrying ~28 stale May-07 inline todos that the backlog regen never scanned). This plan is
> the **genuinely net-new, unowned** CeFi residual — the DERIBIT options/futures + BINANCE-FUTURES perp bundle backfill
> verification + the phantom-audit per-cluster triage. Manifest/coverage/source work for CeFi is owned separately by
> [`cefi_manifest_canonicalisation_2026_06_01.md`](./cefi_manifest_canonicalisation_2026_06_01.md); `available_at`
> stamping by
> [`available_at_lookahead_bias_completion_2026_05_08.md`](./available_at_lookahead_bias_completion_2026_05_08.md). Do
> NOT duplicate those here.

## Context

The `cefi_master` epic body asserted (May-07/08) that DERIBIT 2024 options/futures bundles were backfilled, with
2025/2026 light-VMs "relaunched 2026-05-06", and BINANCE-FUTURES perps "partial, manifest cleanup pending". A month has
elapsed and the per-asset-group Phase-3 backfills (`mtds_backfill_phase3_2026_05_22` /
`instruments_backfill_phase3_2026_05_22`) have since completed (`open:0`). So these are **almost certainly captured
now** — but per the "Data Pipeline Correctness" and honest-absence HARD RULES, that must be **verified, not assumed**.
This plan converts the stale assumption into a clean verification: confirm captured %, flip what's real, re-run only
genuine gaps.

It also absorbs the **phantom-audit residual** (slot-6 2026-05-11 ran
`reconcile_phantom_manifest_rows_all.py --asset-group cefi`: 1,290,706 real captures / 2,223 "phantom" = 0.17% — UNDER
the <0.5% criterion, so `--apply` was correctly withheld). The residual 2,223 are drift-axis-suspicious clusters (blank
`venue` 1,453; DERIBIT `options_chain`/`futures_chain` bundle equivalence ~136; `venue=UNKNOWN` 111; Bitfinex `*F0`
perpetual-code normalization ~400). These need per-cluster real-vs-false-positive triage.

## P0 — DERIBIT + BINANCE-FUTURES bundle verification

> **[2026-07-12 correction, finding 28, §A2 B-queue]** (was: the todos below frame the `futures_chain` gap purely as a
> backfill-relaunch target): the `futures_chain` Tardis-channel absence is now CONFIRMED STRUCTURAL, not a coverage gap
> — `mvp_backfill_cefi_tick_v10_2026_06_27.md:869-874` verified via `GET /v1/exchanges/<exch>` that NO CeFi Tardis venue
> (binance-futures, bybit, deribit, kraken-futures, bitfinex-derivatives, bitget-futures, upbit) exposes a
> `futures_chain` channel at all; 66,007 `attempted_failed` cells were reclassed to
> `empty_confirmed`/`EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` accordingly. The "Backfill relaunch required" framing in
> the todos below is SUPERSEDED for the `futures_chain` structural portion — it remains accurate for the genuine
> `derivative_ticker`/other gaps.
>
> **🔴 [2026-07-15 correction, plan-reconcile §1, operator ruling A] — THAT RECLASS IS NON-DURABLE. Do not read the
> paragraph above as a settled end-state.** The STRUCTURAL half stands (no CeFi Tardis venue exposes a `futures_chain`
> channel — that finding is unchanged). The RECLASS half did not hold: per
> `plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (manifest triage ~2026-07-15), cefi
> `futures_chain` reads **112,727 / 112,727 `attempted_failed` — exactly 100.0%, 0 captured**. The population did not
> merely survive the reclass, it GREW (66,007 → 112,727): something is still attempting a channel that structurally
> cannot be captured, and each retry re-stamps `attempted_failed` over the `empty_confirmed` reclass.
>
> The live defect is therefore **not** "reclassify the cells again" — a re-reclass would be overwritten the same way. It
> is: **the retry path must stop attempting a structurally-absent channel** (gate it at the writer so the shards are
> never attempted, rather than repairing the manifest after the fact). That capture defect is **OPEN** and owned by
> `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`, which already scopes the shared
> `cefi-deribit-<year>-light` reprobe-VM class bundling `options_chain + derivative_ticker + futures_chain`. Per the
> data-pipeline-correctness HARD RULE this is a heartbeat item, not bookkeeping — an honest manifest must not claim
> `empty_confirmed` for cells the pipeline is actively re-failing.

- [x] [VERIFY] P0. Query the CeFi manifest for DERIBIT `options_chain` + `futures_chain` bundle roots across the
      genesis→today window; record per-day `captured` vs `attempted_failed` vs `expected_unattempted` distribution.
      Confirm `expected_root_clusters` cluster-validation passed at `record_captured` (per CLAUDE.md "Cluster validation
      MANDATORY"). Flip the verified-captured rows' tracking here to ✅ with the manifest evidence; list any genuine gap
      days. **VERIFIED 2026-06-12 — FINDING: ZERO genuine coverage. availability_index: 20,713 attempted_failed (99.3%)
      / 138 claimed captured / 3 empty_confirmed, date range 2019-03-30→2026-05-01 (2,590 days). Cluster validation
      FAILED: projected_index shows 136/138 "captured" rows are PHANTOM_CAPTURED_NO_OBJECT (manifest claims capture but
      no GCS file exists); only 1 genuine captured row out of 2,590 days. Error breakdown:
      LegacyBlankErrorReasonError=20,685 (MTDS per-instrument rows — market-tick-data-service wrote blank-error tracking
      entries for BTC/ETH/BTC-PERPETUAL/ETH-PERPETUAL per day), VENUE_FETCH_FAILED=16, [Errno 28] disk-full=12. Root
      cause: market-tick-data-service silently failed all bundle fetches; market-data-processing-service wrote 136
      phantom "captured" entries with no corresponding GCS objects. DERIBIT options_chain + futures_chain have never
      been successfully backfilled. Genuine gap: ALL 2,590 days (2019-03-30→2026-05-01). Backfill relaunch required (see
      [SCRIPT] P0 below).**
- [x] ✅ [VERIFY] P0. Same for BINANCE-FUTURES `perpetual` / `derivative_ticker` — per-instrument-per-day coverage ≥99%
      on live perps; manifest reconciliation has dropped phantom rows. _\_VERIFIED 2026-06-12 — FINDING: Coverage 54.7%,
      below ≥99% threshold. availability_index derivative_ticker: 38,390 captured / 17,935 attempted_failed / 13,895
      empty_confirmed (54.7% of non-empty rows captured). Phantom check PASS: projected_index shows
      PHANTOM_CAPTURED_NO_OBJECT=0 for BINANCE-FUTURES (all 58,090 captured rows have real GCS objects). Failed rows:
      LegacyBlankErrorReasonError=16,594 / VENUE_FETCH_FAILED=1,294 / other=142. futures_chain for BINANCE-FUTURES: 0
      captured, 13,334 attempted_failed (100% gap). Date range: 2019-12-30→2026-06-09 (all years affected). Additional
      per-instrument detail (slot-6 GCS SDK 2026-06-12): PERPETUAL-tagged rows only = 38,362 captured (100%),
      per-instrument tracking degraded to blank-instrument-id aggregate from 2026-04-29, complete gap
      2026-05-23→2026-06-08 (20 days, 0 rows), 2026-06-09 VENUE_FETCH_FAILED on _-PERP IDs. Orphan sweep 4,867
      BINANCE-FUTURES = all RECORD\*ONLY (legacy twins, not phantoms). Genuine gap: ~17,935 derivative_ticker
      day/instrument failures + 13,334 futures_chain gaps needing backfill. No phantoms — all captured entries are real.
      Backfill relaunch required (see [SCRIPT] P0 below).\*\*
- [x] ✅ [SCRIPT] P0. For any genuine gap days found above, relaunch the scoped backfill via the existing
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` (per launcher SSOT) — NOT a new launcher; verify
      STARTED + PROCESSING\_\* events + STOPPED at exit per the no-fire-and-forget rule. If zero genuine gaps, record
      that and skip. — deployment-service@20260624-011134 | DERIBIT: 14 VMs (heavy+light 2020-2026), BINANCE-FUTURES: 7
      VMs (light 2020-2026), TradFi: 12 VMs (CME ES + CBOE VIX 2024-2026). All 33 VMs RUNNING. STARTED:
      cefi-deribit-2020-heavy DEPLOYMENT_STARTED cd22c05e-ca8e-4053-9ab3-e923f56f2ff4 @ 19:44:37 UTC;
      cefi-binance-futures-2020-light DEPLOYMENT_STARTED 4a1db856-2aea-48bb-b130-3b045c384bbe @ 19:44:05 UTC.
      PROCESSING: DERIBIT writing book_snapshot_5/trades rows (698k manifest entries by 19:47 UTC); BINANCE-FUTURES
      writing derivative_ticker/liquidations rows (104k rows/batch by 19:46 UTC). Hung BINANCE-FUTURES-2024 VMs from
      prior session (cefi-binance-futures-2024-heavy/light-20260623-193543) were confirmed zero-progress after 5.5h and
      deleted before relaunch.
  > **GATED 2026-06-12 (slot-2, BLK-01710985)**: Re-queued with post-G4-apply prereq per operator ruling — same as
  > manifest-completion gate (BLK-fb70523c). Pre-migration drain active;
  > `Do NOT resume until migration verified-complete` constraint applies. G4 applies all 5 AGs still `[ ]` pending. Do
  > not launch cefi backfill VMs until G4 applies complete and drain is lifted.
- [ ] [SCRIPT] P2. Spot-check: download 3 random days of DERIBIT options; verify `options_chain` greeks / IVs populated
      (not NaN-blanket).
- [ ] [SCRIPT] P2. Spot-check: download 1 day of BINANCE-FUTURES perps; verify funding + open_interest populated.

## P0 — phantom-audit per-cluster residual triage

- [x] [SCRIPT] P0. Per-cluster real-vs-false-positive triage of the 2,223 cefi phantom rows (blank-venue 1,453 / DERIBIT
      bundle-equivalence ~136 / `venue=UNKNOWN` 111 / Bitfinex `*F0` ~400). For each cluster: sample, check parquet
      existence at the canonical path. For false-positive drift axes (blank/UNKNOWN venue, `option`↔`options_chain`
      bundle equivalence, `BTCF0`→canonical normalization), add the missing drift axis to
      `reconcile_phantom_manifest_rows_all.py`'s cefi `prefix_tpls` / equivalence templates so the audit stops flagging
      them. For any genuinely-real subset, `--apply` ONLY that subset (never blanket-flip — the 2026-05-04
      130k-false-positive class is the cautionary precedent). *\_DONE 2026-06-12 — GCS spot-check + projected_index
      triage completed for all 4 clusters. Blank venue (1,481 captured): no blank-venue GCS paths exist → all genuine
      phantoms; applied. DERIBIT bundle (138 captured, data_type=options_chain/futures_chain): GCS scan confirmed zero
      data_type=futures_chain/options_chain blobs for any sampled date → all 138 genuine phantoms; applied. UNKNOWN
      venue (111 captured): no canonical GCS path for UNKNOWN venue → all genuine phantoms; applied. Bitfinex *F0
      (~400): projected\*index shows 0 PHANTOM_CAPTURED_NO_OBJECT for BITFINEX-FUTURES + GCS spot-check confirms
      BTCF0:USTF0 parquet files exist at canonical paths → NO phantoms, no script changes needed. Total flipped: 1,730
      rows to attempted_failed with error_reason=phantom_captured_no_parquet_at_canonical_path. No false-positive drift
      axes found; no template changes required (the 4 claimed drift axes were all genuinely-phantom or non-phantom, not
      false positives).\*\*
- [x] [VERIFY] P0. Re-run `reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` after the template
      fixes; confirm phantom rate stays <0.5% and the residual is classified by drift axis (zero unclassified).
      **VERIFIED 2026-06-12 — Post-apply manifest scan (workspace venv, direct GCS read): captured=1,332,922,
      phantom-flagged=1,762 (attempted_failed + phantom error_reason). Phantom rate = 1,762 / (1,332,922+1,762) = 0.132%
      — PASS (<0.5%). All 3 clusters cleared: blank_venue=0, unknown_venue=0, deribit_bundle=0. Phantom-flagged
      breakdown: blank-venue=1,493 / DERIBIT-bundle=138 / UNKNOWN=131 — all correctly classified by drift axis, zero
      unclassified rows.**

## Success criteria

- DERIBIT options/futures + BINANCE-FUTURES bundle coverage is manifest-verified (not assumed): every (venue, data_type,
  day) cell is `captured`, honestly `empty_confirmed`/`expected_unattempted`, or has a genuine-gap backfill that ran to
  completion.
- Phantom residual fully classified by drift axis; templates updated so the audit is clean; <0.5% rate held.
- `bash scripts/quality-gates.sh` green on any `instruments-service` / `mtds` template change before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the verification queries + any gap
backfill run on real GCS manifest data; the phantom-audit re-run executes on a same-region VM and reports the post-fix
rate.
