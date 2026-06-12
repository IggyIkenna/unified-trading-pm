---
title: "CeFi DERIBIT + BINANCE-FUTURES bundle backfill verification + phantom-residual triage"
parent_epic: cefi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ./cefi_manifest_canonicalisation_2026_06_01.md
  - ../epics/cefi_master.md
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

- [x] [VERIFY] P0. Query the CeFi manifest for DERIBIT `options_chain` + `futures_chain` bundle roots across the
      genesis→today window; record per-day `captured` vs `attempted_failed` vs `expected_unattempted` distribution.
      Confirm `expected_root_clusters` cluster-validation passed at `record_captured` (per CLAUDE.md "Cluster validation
      MANDATORY"). Flip the verified-captured rows' tracking here to ✅ with the manifest evidence; list any genuine gap
      days. **VERIFIED 2026-06-12 — FINDING: ZERO genuine coverage. availability_index: 20,713 attempted_failed
      (99.3%) / 138 claimed captured / 3 empty_confirmed, date range 2019-03-30→2026-05-01 (2,590 days). Cluster
      validation FAILED: projected_index shows 136/138 "captured" rows are PHANTOM_CAPTURED_NO_OBJECT (manifest claims
      capture but no GCS file exists); only 1 genuine captured row out of 2,590 days. Error breakdown:
      LegacyBlankErrorReasonError=20,685 (MTDS per-instrument rows — market-tick-data-service wrote blank-error tracking
      entries for BTC/ETH/BTC-PERPETUAL/ETH-PERPETUAL per day), VENUE_FETCH_FAILED=16, [Errno 28] disk-full=12.
      Root cause: market-tick-data-service silently failed all bundle fetches; market-data-processing-service wrote 136
      phantom "captured" entries with no corresponding GCS objects. DERIBIT options_chain + futures_chain have never been
      successfully backfilled. Genuine gap: ALL 2,590 days (2019-03-30→2026-05-01). Backfill relaunch required (see
      [SCRIPT] P0 below).**
- [x] ✅ [VERIFY] P0. Same for BINANCE-FUTURES `perpetual` / `derivative_ticker` — per-instrument-per-day coverage ≥99% on
      live perps; manifest reconciliation has dropped phantom rows. **VERIFIED 2026-06-12 — FINDING: Coverage 54.7%,
      below ≥99% threshold. availability_index derivative_ticker: 38,390 captured / 17,935 attempted_failed / 13,895
      empty_confirmed (54.7% of non-empty rows captured). Phantom check PASS: projected_index shows
      PHANTOM_CAPTURED_NO_OBJECT=0 for BINANCE-FUTURES (all 58,090 captured rows have real GCS objects). Failed rows:
      LegacyBlankErrorReasonError=16,594 / VENUE_FETCH_FAILED=1,294 / other=142. futures_chain for BINANCE-FUTURES:
      0 captured, 13,334 attempted_failed (100% gap). Date range: 2019-12-30→2026-06-09 (all years affected). Additional
      per-instrument detail (slot-6 GCS SDK 2026-06-12): PERPETUAL-tagged rows only = 38,362 captured (100%), per-instrument
      tracking degraded to blank-instrument-id aggregate from 2026-04-29, complete gap 2026-05-23→2026-06-08 (20 days, 0 rows),
      2026-06-09 VENUE_FETCH_FAILED on *-PERP IDs. Orphan sweep 4,867 BINANCE-FUTURES = all RECORD_ONLY (legacy twins, not phantoms).
      Genuine gap: ~17,935 derivative_ticker day/instrument failures + 13,334 futures_chain gaps needing backfill.
      No phantoms — all captured entries are real. Backfill relaunch required (see [SCRIPT] P0 below).**
- [ ] [SCRIPT] P0. For any genuine gap days found above, relaunch the scoped backfill via the existing
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` (per launcher SSOT) — NOT a new launcher; verify
      STARTED + PROCESSING\_\* events + STOPPED at exit per the no-fire-and-forget rule. If zero genuine gaps, record
      that and skip.
  > **GATED 2026-06-12 (slot-2, BLK-01710985)**: Re-queued with post-G4-apply prereq per operator ruling — same as
  > manifest-completion gate (BLK-fb70523c). Pre-migration drain active; `Do NOT resume until migration verified-complete`
  > constraint applies. G4 applies all 5 AGs still `[ ]` pending. Do not launch cefi backfill VMs until G4 applies
  > complete and drain is lifted.
- [ ] [SCRIPT] P2. Spot-check: download 3 random days of DERIBIT options; verify `options_chain` greeks / IVs populated
      (not NaN-blanket).
- [ ] [SCRIPT] P2. Spot-check: download 1 day of BINANCE-FUTURES perps; verify funding + open_interest populated.

## P0 — phantom-audit per-cluster residual triage

- [ ] [SCRIPT] P0. Per-cluster real-vs-false-positive triage of the 2,223 cefi phantom rows (blank-venue 1,453 / DERIBIT
      bundle-equivalence ~136 / `venue=UNKNOWN` 111 / Bitfinex `*F0` ~400). For each cluster: sample, check parquet
      existence at the canonical path. For false-positive drift axes (blank/UNKNOWN venue, `option`↔`options_chain`
      bundle equivalence, `BTCF0`→canonical normalization), add the missing drift axis to
      `reconcile_phantom_manifest_rows_all.py`'s cefi `prefix_tpls` / equivalence templates so the audit stops flagging
      them. For any genuinely-real subset, `--apply` ONLY that subset (never blanket-flip — the 2026-05-04
      130k-false-positive class is the cautionary precedent).
- [ ] [VERIFY] P0. Re-run `reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` after the template
      fixes; confirm phantom rate stays <0.5% and the residual is classified by drift axis (zero unclassified).

## Success criteria

- DERIBIT options/futures + BINANCE-FUTURES bundle coverage is manifest-verified (not assumed): every (venue, data_type,
  day) cell is `captured`, honestly `empty_confirmed`/`expected_unattempted`, or has a genuine-gap backfill that ran to
  completion.
- Phantom residual fully classified by drift axis; templates updated so the audit is clean; <0.5% rate held.
- `bash scripts/quality-gates.sh` green on any `instruments-service` / `mtds` template change before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the verification queries + any gap
backfill run on real GCS manifest data; the phantom-audit re-run executes on a same-region VM and reports the post-fix
rate.
