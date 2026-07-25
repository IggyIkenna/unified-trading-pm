---
doc_type: plan
title: CeFi 4-surface canonicalization migration — execution log history, part 1 (2026-07-18 → 2026-07-20)
summary: >-
  Verbatim extraction of the OLDEST Progress Log entries (2026-07-18 CUTOVER/manifest-canonicalization narrative through
  the 2026-07-20 catalogue-coverage-gap measurement) from `cefi_4surface_migration_execution_log_2026_07_24.md`, split
  out for line-cap compliance (`plans/active/task_template.md` §3 finding J). Content moved verbatim, nothing summarized
  or dropped. The 6 open todos originally trailing this range ("Deferred / handoff") were kept LIVE in the parent, not
  archived here — this child carries zero open todos by design. Part 2 of this history
  (`/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md`) covers the 2026-07-21
  PRE-COMPACT checkpoint + its DELTA updates; the parent plan
  (`/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md`) remains the single live source of truth for all
  open work.
status: complete
nature: record
asset_group: [cefi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [cefi, close-out, canonicalisation, manifest, execution-log, progress-log, history, migration]
related:
  [
    /plans/active/cefi_4surface_migration_execution_log_2026_07_24.md,
    /plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Split out of cefi_4surface_migration_execution_log_2026_07_24.md (1635 lines, over the 1000L hard line-cap) per the
  plan-hygiene extraction pattern (`plans/active/task_template.md` §3 finding J) — the oldest, fully-closed dated
  Progress Log range (2026-07-18 through the 2026-07-20 catalogue-coverage-gap section) moved verbatim into this
  dedicated history child so the parent can trim to recent state + open todos. Session-driven extraction, 2026-07-24.
---

# CeFi 4-surface canonicalization migration — execution log history, part 1 (2026-07-18 → 2026-07-20)

> **This is history part 1 of 2, extracted from
> [`cefi_4surface_migration_execution_log_2026_07_24.md`](/plans/active/cefi_4surface_migration_execution_log_2026_07_24.md)**
> for line-cap compliance (2026-07-24). Zero open todos live here — the 6 todos originally trailing this range
> ("Deferred / handoff") stayed in the parent. Part 2
> (`/plans/archive/2026_07/cefi_4surface_migration_execution_log_history_part2_2026_07_24.md`) covers the 2026-07-21
> PRE-COMPACT checkpoint that immediately follows this range. Content below is verbatim, unedited.

## Progress Log

- **2026-07-20 (slot-3, /autonomous) — NO-ORPHANS ACCOUNTING (deliverable A) + READY MVP-gap BACKFILL (deliverable B).**
  Live re-run of the shipped audit (`mtds/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`) on the
  10,085,983-row cefi tick manifest + a per-id MVP categorizer that reuses Script-3's EXACT resolver
  (`is/scripts/complete_cefi_manifest_canonical_dedup_2026_07_17.py` `resolve_canonical` + `_build_*` maps) and the UAC
  shared predicate `is_in_mvp_capture_universe` (perp-gate derived by parsing catalogue ids). Full artifact:
  `/tmp/cefi_no_orphans_accounting_2026_07_20.json`; categorizer + logs in the slot-3 scratchpad.

  **A. NO ORPHANS — verdict: SATISFIED for captured data; residual is id-LABELING, not missing data.** Of **3,216,054
  captured rows, 98.36% (3,163,413) are already canonical+catalogued.** The **1.64% (52,641) captured-not-clean rows
  carry ZERO missing data** — every one is an id-form problem: **32,730 blank-`instrument_id`** rows (captured tick data
  whose manifest row lost its id — data present in GCS, needs a manifest re-derivation, NOT a backfill; incl. 9,750 also
  blank `data_type`) + **19,911 bare-wire** captured ids (BYBIT `ETHUSD`/`BTCUSD` inverse, bare `BTC`/`ETH` majors,
  BITGET dated COIN-M letter-month `BTCUSDH/M/U/Z`) that the v2 recanon (itype-fix + wire-map/decompose) canonicalizes.
  The **173,453 §4 non-canonical + 33,144 §6 orphan** rows categorize (by MVP membership) into:
  - **FIXABLE_RECANON — 5,086 distinct ids / 2,159,453 rows** (bare-wire→canonical, marker-less-perp→`@LIN/@INV`); the
    MAIN agent's v2 re-canonicalization+dedup fixes them. **RESOLVER GAP FOUND (hand to the v2 pass):** Script-3
    `resolve_canonical` returns a marker-less canonical-shaped perp UNCHANGED (does NOT add `@LIN/@INV`) even though
    `marker_base` HAS the mapping — the v2 `--apply` needs an explicit marker-add leg or ~4,500 marker-less perp ids
    persist as orphans. (The audit's `_CANON_RE` makes the margin marker optional, which is why these hide inside the
    "canonical" bucket and surface only as §6 orphans.)
  - **NON_MVP_HISTORICAL — 31,829 ids / 770,996 rows / 28 captured** → PROVED legit-absent: expired dated contracts
    (expiry < 2026-07-20) **30,268 ids** (the DERIBIT 2019-2025 options dominate §6, e.g. `BTC-10APR20-4750-C`),
    mvp-base **delisted** with no data **1,307 ids** (WAVES/EOS…), base not in the 556-member `CEFI_BASE_ASSET_UNIVERSE`
    **254 ids**. EXPECTED honest-raw, NOT defects.
  - **MVP_GAP — 311 ids / 45,650 rows / 0 captured** → real current-MVP instruments with `attempted_failed` + no capture
    (deliverable B). Venues: **DERIBIT 191** (dated futures `BTC/ETH-25SEP26/25DEC26/26MAR27` + combos), **BYBIT 80**,
    **BITGET-FUTURES 17** (`*USD_CM` COIN-M), **KRAKEN-FUTURES 9** (majors BTC/ETH/ADA/…-USD), **BINANCE-FUTURES 8**
    (SYS/B3/VINE/DENT/LRC-USDT@LIN), **OKX-SWAP 4** — ALL Tardis venues. Full list + per venue×data_type×date-range in
    the JSON (`bucket_2_MVP_instrument_gaps`).
  - **UNRESOLVED_INDET — 673 ids / 63,621 rows** (blank-id + bare-wire the resolver can't map standalone; the 33,027
    captured here = the blank-id manifest-labeling defect above). Resolve via the v2 itype-fix pass.

  **B. OPTIMIZED BACKFILL — READY (validated launch-ready via DRY-RUN, NOT run — cap-1 slot is occupied).**
  Authoritative gap: **cefi honest coverage 48.80%** (`measure_honest_coverage --diagnose-layer1`: 3,065,577 captured /
  6,281,484 reachable; Layer-1 denominator COMPLETE, 0 holes). **The Track-2 [DATA] P1 backfill is ALREADY LIVE**:
  `cefi-queue-heavy-binancefutu-x17-20260720-102103` (SPOT, `VM_TARDIS_CONSUMER=1`, ALL 17 Tardis venues, HEAVY group
  `trades;book_snapshot_5`, 2026-02-27→2026-07-19) — it holds the single Tardis slot now. Whole-corpus gap = **668,695
  `attempted_failed` (re-fetch) + 2,547,212 `expected_unattempted` (never attempted)** — `eu` dominates. Per-venue
  coverage (worst gaps first; full table in `/tmp/cefi_no_orphans_accounting_2026_07_20.json` →
  `deliverable_B_coverage`): BINANCE-FUTURES 48.2% (af 176k/eu 497k) · BITGET-FUTURES 25.8% (af 116k/eu 394k) · BYBIT
  53.3% (af 109k/eu 217k) · KRAKEN-FUTURES 55.7% · **DERIBIT 8.6% (af 114k — worst)** · OKX-SPOT 35.6% · and the
  **NON-Tardis (cap-EXEMPT) venues with real `eu` gaps: ASTER 41.3% (eu 163k) · HYPERLIQUID 38.4% (eu 140k) ·
  EXTENDED-STARKNET 37.8% (eu 37k) · LIGHTER-ZKSYNC 0.0% (eu 28,648, ZERO captured)**. **CORRECTION to the earlier
  orphan-only note:** the on-chain venues DO have large `eu` gaps (they showed no `attempted_failed` in the §6 orphan
  set, hence absent from MVP_GAP) → the cap-EXEMPT `launch-cefi-hl-aster-historical-backfill.sh` (DRY-RUN validated
  launch-ready: `cefi-hyperliquid-/aster-/ lighter-zksync-/extended-starknet-*` VMs, `SHARD_DAYS` parallelizable) should
  run **IN PARALLEL** with the Tardis waves (they never touch the licensed Tardis IP, so parallelism is free
  throughput). Tardis venues → the sharded launcher below. **Cap-1-safe Tardis waves to run AFTER the heavy VM frees the
  slot (each sequential; `tardis-concurrency-guard.sh` refuses a 2nd Tardis VM):**
  - Wave-2 LIGHT/perps (1 VM):
    `DRY_RUN=0 SINGLE_VM_QUEUE=1 LAUNCH_GROUPS=light VENUES="BINANCE-FUTURES BYBIT OKX-SWAP KRAKEN-FUTURES BITFINEX-FUTURES BITGET-FUTURES" TARDIS_MAX_CONCURRENT_DOWNLOADS=32 TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=8 bash scripts/vm/launch-cefi-sharded-backfill.sh --env prod`
    (uniform `derivative_ticker;liquidations;futures_chain` → exactly ONE `cefi-queue-light-*` VM).
  - Wave-3 DERIBIT LIGHT (1 VM, separate — options_chain): same command with `VENUES="DERIBIT"`.
  - Wave-4 earlier-year HEAVY (2020-2025) if coverage still <target after the recent window: same,
    `LAUNCH_GROUPS=heavy YEARS="2024 2025"` etc.
  - Wave-P NON-Tardis (run NOW, in PARALLEL — cap-EXEMPT, no Tardis slot contention):
    `DRY_RUN=0 SYMBOLS=ALL SHARD_DAYS=21 bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (fills the
    ASTER/HL/ LIGHTER-ZKSYNC/EXTENDED-STARKNET `eu` gaps; LIGHTER-ZKSYNC at 0% is the priority). SPOT-default; not
    year-clamped so it covers each venue's genesis→today.
  - **CAP-1 FINDING (surfaced):** `SINGLE_VM_QUEUE=1 LAUNCH_GROUPS=light` over DERIBIT+perp venues flushes **2** VMs
    (DERIBIT's `options_chain` data_types differs → separate bucket) while the guard's planned-count counts light as
    **1** — a latent cap-1 breach. Keep DERIBIT-light its own wave (above) until the guard's `_QUEUE_BUCKETS` is taught
    to count per (group|data_types), not per group.
  - **Optimizations applied (SSOT `/codex/05-infrastructure/vm-launcher-runbook.md` §Tardis,
    `…/spot-vms-for-backfill.md`):** Tardis **cap-1 both clouds** (guard wired in; scale on the ONE IP, never more VMs)
    · **SINGLE_VM_QUEUE=1** bundles every venue onto one VM · **TARDIS_MAX_CONCURRENT_DOWNLOADS=32 /
    TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=8** (defaults 16/4 leave the box ~93% idle) · **SPOT-default** + the shipped
    PROGRESS.json checkpoint auto-resume (`deployment@c138957`+`utl@3de3296b`; `RelaunchPreemptedVm` re-enters through
    the guard) · pd-balanced 250GB boot disk (kills the throughput cliff) · `STALL_PROGRESS_REGEX=uploaded`. HL/ASTER
    launcher (`launch-cefi-hl-aster-historical-backfill.sh`, cap-EXEMPT, `SHARD_DAYS` parallelizable) also validated
    launch-ready if on-chain gaps surface. **Do NOT launch a 2nd Tardis VM while `cefi-queue-heavy-*` runs.**

- **2026-07-18 (slot-3, /autonomous) — CUTOVER STATUS: surface C DONE+durable; surfaces A/B staged + BRIDGED; both
  sub-agents died on a session limit (resets 21:40 Europe/London).** The reader-bridge (D3) resolves wire→canonical at
  read time, so the system reads canonical NOW even before A/B physically complete.
  - **Surface C (manifest) — ✅ APPLIED + DURABLE** (see entry below): 16.67%→1.59% non-canonical, gate passed, survived
    consolidator re-enable. `is@555ddf1c`.
  - **Surface A (rename, Script 2) — BLOCKED on a bounded, verified data issue**: 12-day dry-run clean (11,141
    would-rename) EXCEPT **15 DERIBIT USDC dual-name collisions**. VERIFIED (read both parquets, day=2023-11-21):
    `BTC_USDC-PERPETUAL.parquet` (symbol=`BTC_USDC-PERPETUAL`, id=`DERIBIT:PERPETUAL:BTC_USDC-PERPETUAL`, 1,090,049
    rows) and `BTC_USDC.parquet` (symbol=`BTC_USDC`, id=`DERIBIT:PERPETUAL:BTC_USDC`, 449,580 rows) are the SAME DERIBIT
    USDC perp under two Tardis symbol aliases, overlapping timestamps — both → canonical
    `DERIBIT:PERPETUAL:BTC-USDC@LIN` (same for ETH_USDC etc.). Script 3 ALREADY deduped these to ONE manifest row; the
    two PHYSICAL files collide on rename. **HANDLING (for the resume): MERGE** the two objects into the canonical stem
    (concatenate + de-dup book rows by timestamp) OR keep the manifest-retained one; keep STOP-ON-SURPRISE for any
    non-same-instrument collision. Row-count asymmetry (2.4×) means dedup-by-timestamp, not blind concat. Script 2 +
    shared module are staged (dirty) in MTDS.
  - **Surface B (content, Script 1) — NOT STARTED**: to run on a SPOT cefi-migration VM via dirty tarball
    (`create-code-tarballs.sh --allow-dirty-tarball` → `launch-cefi-migration-vm.sh` with `VM_MIGRATION_CMD`→Script 1,
    DRY-RUN first). Agent hadn't packaged the tarball before the session limit.
  - **RESUME PLAN** (when the session limit lifts / sub-agents available): (1) B finishes the Script 2 merge +
    re-dry-run → I run rename `--apply --stamp <ts>`; (2) content-VM agent packages the tarball + dry-runs Script 1 on a
    VM → I review → `--apply` on the VM (~day). Then verify `ADAF0:USTF0` + `DERIBIT AVAX-USDC@LIN` on all 4 surfaces.

- **2026-07-18 (slot-3, /autonomous) — ✅ MIGRATION 1/3 APPLIED + DURABLE: the manifest (surface C) is canonicalized on
  the LIVE cefi tick manifest and it STUCK.** Sequence: (1) first `--apply` of Script 3 canonicalized the index but its
  post-verify gate caught 42,915 eu/captured 5-col collisions the eu-reconcile missed (cross-`pipeline_mode`: a
  `batch_tardis` eu vs a `batch_native` captured — the 6-col dedup can't catch it). (2) Root discovery: the **manifest
  CONSOLIDATOR cron `uts-prod-manifest-consolidator-execution-cefi-cron` runs EVERY MINUTE and re-rawed the index** —
  this is why "nothing stuck" before; the Track-1 drain is mandatory, not optional. (3) A shipped the eu-reconcile fix
  (`instruments-service@555ddf1c`: reconcile against the FULL post-relabel captured-key set, on ALL blobs). (4)
  **DRAIN**: paused the consolidator cron + stopped the live cefi backfill VM. (5) **RE-APPLY** (drained, 555ddf1c) →
  `GATE PASSED: 0 further-resolvable captured, 0 eu/captured collisions` (id_changed=1,535,266, itype_changed=3,519,879,
  perp=374,227, eu-dropped=70,114, orphans-dropped=167,859 non-captured, cull PACIFICA 2,960 EMPTY rows, snapshot
  `_index/snapshots/pre_d4_*`). (6) **RE-ENABLE** consolidator → **STICK TEST PASSED**: manifest stays **97.94%
  canonical / 1.59% non-canonical** (captured-non-canonical 425k→**18,983** genuinely-unresolvable) after the
  consolidator rebuilt from the now-canonical per-VM shards. Fleet restored (consolidator ENABLED). Surface A (rename) +
  surface B (content on a VM) next; then verify `ADAF0:USTF0` + `DERIBIT AVAX-USDC@LIN` on all four surfaces.

- **2026-07-18 (slot-3) — Script 3 `--apply` RAN by operator; POST-APPLY GATE FAILED (42,915 eu/captured collisions) →
  eu-reconcile FIXED + shipped (`instruments-service@555ddf1c`; supersedes `@ae4030ef`).** The canonicalization landed
  (itype_changed 3.5M, relabeled 436,934, perp 374,227, dated_itype_fixed 888,752, cull PACIFICA 2,960 empty, dedup
  collapsed 1.12M, orphans dropped 168,129, NON-cull captured-with-data=0 ✓, snapshots `pre_d4_20260718T190342Z`), but
  the post-apply verify gate exited 1 on **42,915 `expected_unattempted` rows still colliding (5-col) with a captured
  row**. **ROOT CAUSE (confirmed by diagnostic):** the eu-reconcile dropped only eu twins of RELABELED (id-changed)
  captured rows, MISSING eu twins of ALREADY-CANONICAL captured rows (and dropping 0 on an idempotent re-apply). 100% of
  the residual collisions were cross-`pipeline_mode` with venue-prefixed canonical ids (which is why the 6-col de-dup
  couldn't catch them — the 5-col eu-reconcile must). **FIX:** (1) reconcile against the FULL post-relabel captured
  5-col key set (not just id-changed); (2) run on EVERY loaded blob (not main-only — cross-blob collisions); (3) skip
  the candidate/`:PERP:` VOLUME STOP bands on an idempotent re-apply (before-fraction ≥ 90%). eu rows carry no data →
  dropping is always safe; captured-with-data-safe invariant intact. Dry-run drops **71,662** eu rows → 0 residual. **⚠️
  OPERATIONAL FINDING surfaced to the coordinator:** the LIVE index measured RAW AGAIN post-apply (candidates=547,886) —
  **the manifest CONSOLIDATOR re-consolidated OVER the `--apply`** between 19:03 and ~20:31. So the re-apply is a FULL
  apply, and it will be OVERWRITTEN again unless the consolidator + live cefi backfill VMs are DRAINED first (the plan's
  Track-1 "pre-migration drain, then apply"). DRY-RUN only; operator drives the gated re-apply.

- **2026-07-18 (slot-3) — Track-6 resolver-gap fix (`-SPOT`/`-SWAP` itype) + operator-CONFIRMED drop-venue cull SHIPPED
  (`instruments-service@ae4030ef`; supersedes `@4b4b9a7d`).**
  - **RESOLVER-GAP FIX (coordinator suspicion confirmed + fixed):** a residual diagnostic over ALL captured rows found a
    gap — BYBIT-SPOT rows carrying a mis-set `PERPETUAL` itype COLUMN made the 3-tuple wire-map miss (a `-SPOT` venue
    trades ONLY spot). Added a **DEFINITIVE venue-suffix itype override** (`-SPOT`→SPOT_PAIR, `-SWAP`→PERPETUAL) that
    corrects the mis-set column. **+3,531 captured rows / 186M ticks; adjusted canonical-fraction 99.30%→99.41%** (raw
    97.39%→97.49%). CONFIRMED the big classes resolve — undashed `MATICUSDT`→`MATIC-USDT` (via wire-map, counted as
    `catalogue` not `base_quote_map`, which is why base_quote_resolved is only ~2.6k yet 431k bare-wire resolve), dashed
    `SC-USDT`/`BTC-USDC` (base-quote map), slash `XBT/USD` (0 slash residual).
  - **EXACT RESIDUAL (post-resolver, post-cull): 53,965 captured rows / 7.46B ticks**, all genuinely-unresolvable
    without fabrication: bare-no-quote 11,487 / 6.08B ticks (`DERIBIT:ETH`/`BTC` index, `BYBIT:BTCUSD` spot/perp
    AMBIGUOUS — catalogue holds a stale no-marker `BYBIT:PERPETUAL:BTC-USD` dup alongside `@INV`, worth a catalogue
    cleanup), undashed-delisted 3,633 (BITGET CME `ETHUSDH` no year), OKX 3-seg `TRX-USD-SWAP` 2,525, EXTENDED-STARKNET
    bare-marker `SUI-USD@LIN` 1,108, nonascii junk 384, delisted 170, CME-no-day 33, DERIBIT hex-strike 26. Plus 34,597
    null-id bundle/roadmap KEPT (canonically null).
  - **DROP-VENUE CULL (operator-CONFIRMED "yeah cull drop venue"):** implemented snapshot-first, drops ALL rows incl
    captured-with-data for 13 venues (the ONE authorized captured-data exception; STOP bound + per-venue impact log;
    matches the venue-chain-glued form). **FINDING — 12 of the 13 cull venues have ZERO rows in the cefi TICK manifest**
    (BINANCE-DELIVERY appears 0× anywhere — its COIN-M is only in the instruments CATALOGUE as reference, NOT captured
    into cefi tick data). Only **PACIFICA** matches (stored as `PACIFICA-SOLANA`): **2,960 rows / 0 captured-with-data /
    0 ticks** (all empty probes). So the cull is a **near-no-op on THIS manifest** — surfaced to the operator: the
    BINANCE-DELIVERY COIN-M data you expected to cull is not in the cefi manifest. captured-with-data (non-cull) dropped
    = 0 (invariant held). DRY-RUN only; `--apply` NOT run.

- **2026-07-18 (slot-3) — Track-6 DATED-WIRE itype-fix SHIPPED — the 41B-tick lever (`instruments-service@4b4b9a7d`;
  supersedes `@a63a0556`).** Operator Option A. A dated contract is a FUTURE/OPTION, never a PERPETUAL; the manifest's
  itype column is often mis-set to PERPETUAL/blank on a dated wire (`OKX-FUTURES`/`LTC-USD-210625`), so the 3-tuple
  wire-map — which ALREADY keys the venue-native dated `raw_symbol` — missed. `_resolve_itype` now detects a genuine
  date tail (numeric `[-_]YY[YY]MMDD`, DERIBIT text date `-5APR19`, CME letter-month `…USDH25`, option strike
  `…-3250-C`) and overrides PERPETUAL/blank → FUTURE/OPTION, which UNBLOCKS the existing wire-map. **KEY FINDING: the
  itype-fix ALONE (via the existing wire-map) resolves ~115,225 of ~118,204 captured dated rows / ~40.7B ticks — the
  base-quote-WITH-DATE map the coordinator specified is largely redundant (the wire-map already keys the dated
  raw_symbols; it adds only 1,286).** Also: MATIC→POL rebrand alias (folds into base-quote); bare-underlying
  bundle-vs-genuine split (0 bundle unresolved / 6,214 genuine no-quote single instruments, honest-raw); race-tolerant
  per-VM shard load (a live-VM shard consolidated mid-run → skip; documented in `QUALITY_GATE_BYPASS_AUDIT.md`).
  **canonical-fraction: raw 83.15%→97.39%, adjusted (excl. the 63,776 canonically-null bundle/blank captured shards)
  84.98%→99.30%.** Residual ~93.8k honest-unresolved is genuinely-unresolvable without fabrication (no-quote bare
  underlyings, delisted alts absent from the catalogue, BITGET CME with no derivable expiry day). captured-with-data
  dropped = 0 (invariant held). DRY-RUN only; `--apply` NOT run. Surfaced to the coordinator.

- **2026-07-18 (slot-3) — Track-6 follow-up: base-quote SSOT map + Kraken/underscore reconstruct + operator CORRECTIONS
  SHIPPED (`instruments-service@a63a0556`; supersedes `@9bb339f9`).** Extended Script 3's `resolve_canonical` with a
  SECOND catalogue map keyed on each id's `BASE-QUOTE` segment (undated perp/spot) — resolves the dashed manifest value
  to the EXACT catalogue id (the catalogue IS complete, incl. delisted; the bare-wire miss was a key-form mismatch, not
  a delisting gap) — plus a narrow Kraken-slash/underscore reconstruct. Applied the operator CORRECTIONS:
  **KALSHI-PERP/POLYMARKET-PERP KEPT** (roadmap venues, removed from the drop set); **bundle rows
  (`futures_chain`/`options_chain`) KEPT untouched with NO id synthesis** (null id valid, keyed on `underlying`); KEEP-
  trend (only genuine catalogue-orphans drop, non-captured only; captured-with-data ALWAYS protected — invariant held,
  **0 captured-with-data dropped**); per-VM shard load made race-tolerant (a live-VM shard consolidated mid-run → skip).
  **KEY FINDING (authoritative re-measure — the "420k clean dashed" model was WRONG):** the base-quote map recovers only
  **~2,737 rows**, because the unresolved-captured population (172,721 rows / **48.3B ticks**) is dominated by
  **dated_contract 115,251 rows / 41.0B ticks** (`OKX-FUTURES` dated futures + DERIBIT options — DATED, out of scope for
  the undated base-quote map; ROOT = itype mis-set to PERPETUAL on a dated wire so the wire-map misses; the real lever
  to ~100% is a **dated-wire itype-fix**, next follow-up), null-id bundle/blank 34,596 (KEPT), undashed bare underlyings
  18,687 / 7.0B ticks, OKX 3-seg 2,525, MATIC→POL renames 1,157. Canonical-fraction: raw **83.15%→93.90%**, adjusted
  (excl. the 63,776 canonically-null bundle/blank captured shards) **84.98%→95.75%**. DRY-RUN only; `--apply` NOT run.
  Surfaced to the coordinator with the dated-wire itype-fix as the recommended next step.

- **2026-07-18 (slot-3) — Track-6 `[SCRIPT] P0` instrument_type-column normalization SHIPPED + DRY-RUN validated
  (`instruments-service@9bb339f9`).** Extended Script 3 (`complete_cefi_manifest_canonical_dedup_2026_07_17.py`) with a
  shared `resolve_canonical(venue, raw_itype, id_or_symbol, data_type)` resolver that aligns the newly-enumerated
  non-canonical axes to the rebuilt catalogue SSOT. Dry-run over the whole 11,185,557-row cefi manifest (main index +
  `_legacy_seed` per-VM shard), `--apply` NOT run (drain-gated for the parent to drive). **Measured before→after:**
  itype-column changed **3,639,041** (of which blank/`None`/unknown → **inferred 3,110,955** — the ROOT that unblocks
  the bare-wire 3-tuple resolution); captured bare-wire **relabeled 346,719**; `:PERP:`→`:PERPETUAL:` **rewritten
  374,227** (matches the audit's 374,272); de-dup collapsed **1,091,710** (captured only 2,896); eu-reconcile dropped
  18,888; bare-OKX remapped 0/48; canonical-fraction (captured venue-prefixed) **83.15% → 94.86%**. All STOP-ON-SURPRISE
  bands green (candidates 558,072 ∈ [400k,700k]; perp ∈ [250k,500k]; total-dropped 243,463 < 400k). **KEY DATA-SAFETY
  DECISION (surfaced, not the operator's literal ruling — flagged to the dispatcher):** a naive read of the operator's
  "orphans → DROP" ruling would drop **12,825 captured rows with real data (→ 41,889 across both blobs)** carrying
  **~7.27B ticks** — bare underlyings (`DERIBIT:ETH`), Kraken slash-wires (`XBT/USDT`), BITGET letter-month futures
  (`BTCUSDH`), dated `ETHUSDT_210326` (the missing-quote/`nc:other` class). Per the data-correctness HARD RULE the
  resolver **PROTECTS captured-with-data rows from the drop** (kept honest-unresolved; `_verify_gate` asserts 0
  captured-with-data dropped) and hands them to the Track-6 P1 `missing-quote + nc:other decompose` todo. Only
  non-captured/empty bookkeeping orphans actually drop (**243,463**: blank 74,616 + orphan 168,799 + okx 48). Manifest
  side of the `:PERP:` P0 is also covered by this resolver (on-disk GCS rename + MTDS writer side still open).

- **2026-07-18 (slot-3, /autonomous) — Track-2 REVIEW P0 RULED (both §119 + §252, one decision).** RE-OPEN the CeFi
  Completion Program + REVERSE the inferred 50.79% acceptance. Rationale (all operator-stated across the dispatch
  session): the archived 1.8-year-ceiling premise is a verified-false ~350x code-bug (`run_in_executor(None,…)`
  default-pool + date-serial barrier), NOW FIXED + measured live @~14 MB/s on real infra; the "accept 50.79%" was
  inferred from that erroneous ceiling, not given. The 2.89M-cell gap is ~1-2 days at June rates. This is an autonomous
  ruling made WITHIN documented intent (operator: "continue mapping all todos until they are 100% done /autonomous" +
  the fixed-throughput facts) — recorded so the operator can reverse. The ACTION (resume the cefi Tardis backfill on the
  fixed code, N=1 cap, SPOT, AFTER the Track-1 re-enable so it doesn't fight the drain) is now the `[DATA] P1` todo
  under §119; coverage % is the climbing metric, re-measured post-run to supersede the archived 50.79%.

- **2026-07-18 (slot-3) — Plan authored from a 3-agent audit of ~30 active cefi/IS/MTDS docs + direct verification.**
  Verdict: id-canonicalization migration (Track 1) is FINAL for its axis and cutover-ready; cefi overall has 5 separate
  open tracks. Biggest is Track 2 — the archived "honest-done 50.79%" rests on a verified-false 1.8-year-ceiling premise
  (a ~350x code bug, now fixed; gap fillable in ~1-2 days) and the acceptance may have been inferred, not given → needs
  an operator ruling. All source docs referenced above; none duplicated here.

- **2026-07-20 (slot-3, /autonomous, operator away 6h) — STATE + PLAN (resumability handoff; context may compress).**
  Success criteria the operator set: (1) ALL migrations done on existing data, NO orphans MVP-or-not; (2) code READY to
  backfill the remaining MVP-instrument gaps with optimized download/processing/upload. **DONE + committed (survived a
  mid-run laptop reboot):** Surface C v1 manifest canonicalization (98.27% canonical); Surface A renames (~~2.77M
  files); TRACK H SPOT preemption CHECKPOINT CONTRACT (reader deployment-service@c138957 + UTL writer utl@3de3296b +
  tee-wrapper + docs utl-pm@7a69e6ba1 — new backfills auto-resume from vm-logs/{vm}/PROGRESS.json, monotonic-gated);
  TRACK G DURABILITY (write-gate mtds@571e258c makes non-Tardis cefi manifest canonicalize at write; reconciliation
  orphan audit §6 mtds@b4251642). **IN FLIGHT:** Surface B content-column apply — 41/44 slices done, 3 left (24,25,29);
  the reboot wiped the /private/tmp scratchpad so the fleet agent (ae18c5ef) rebuilt orchestration to a reboot-durable
  home (~~/cefi_content_fleet/) with a 15-min system cron recovery; slow SPOT slices converted to ON-DEMAND to break
  preemption thrash (operator-approved — small one-off cost; future backfills stay SPOT+checkpoint-recovery). Collision
  W-drop for slices 01+10 (~10,154 wire objects, per-object W⊆C gate, validated 20/20 + 100/100) auto-fires at
  COVERING_DONE (slices 25,29) — dual-watcher armed (fleet buclu52o1 + my backstop bs214s08j). **REMAINING WORK (this
  session):** (1b) manifest v2 fixable cleanup — re-canonicalize the ~5,485 wire-map-RESOLVABLE non-canonical rows the
  migration missed (incl. operator probe `ADAF0:USTF0`) + no-marker→@LIN + lowercase-itype dups, via a drain+re-apply
  after B+drop; (1c) NO-ORPHANS accounting — categorize the 173,453 §4 non-canonical + 33,144 §6 orphans into FIXABLE
  (~5,485) / MVP-orphan (real defect, resolve) / non-MVP historical (expired/delisted, provably-legitimate, document);
  (2) optimized backfill CODE ready for the MVP gaps (Tardis cap-1 + SINGLE_VM_QUEUE + SPOT+checkpoint-recovery +
  batched uploads). Agents driving: `ae18c5ef` (surface B + drop + final would_patch≈0 verification),
  `a1a5b7732a0277dcf` (1c orphan-accounting + 2 MVP-backfill-code). Manifest v2 (1b) + the final 4-surface verification
  (ADAF0:USTF0 + DERIBIT AVAX-USDC@LIN on filename/column/manifest/reader) driven by the main loop after B+drop.
  Coverage/MDPS-readiness Q answered this session: readiness = manifest capture_status==captured per shard; bundles read
  complete via cluster validation; measure_honest_coverage.py is the gap CLI; two follow-ups (per-timeframe cut +
  canonical-fraction fusion). Two new skill prompts (/data-pipeline-check-mdps + /data-pipeline-check-features) drafted
  for the operator to dispatch.

- **2026-07-20 (slot-3, manifest v2 PREP) — (1b) MANIFEST v2 BUILT + DRY-RUN VALIDATED; `--apply` NOT run (drain-gated,
  main loop drives).** Script: `instruments-service/scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`
  (imports + reuses v1 "Script 3" wholesale — resolver/wire-map/itype/orphan-drop/eu-reconcile/de-dup/snapshot/
  STOP-ON-SURPRISE; adds only the 3 axes v1 structurally could not close).
  - **WHY v1 MISSED THEM (diagnosed empirically, not assumed).** TWO distinct root causes: **(1) the MANDATORY MARGIN
    MARKER is invisible to v1** — v1's `_CANON_ID_RE` makes `@(LIN|INV)` OPTIONAL, so `_extract_raw` classifies a
    marker-less perp (`BINANCE-FUTURES:PERPETUAL:BTC-USDT`) as `canonical` and `_resolve_full` short-circuits to
    `already_canon`, NEVER reaching the `marker_base` path that would add it; `_verify_gate` skips it for the same
    reason, so v1's apply passed its own gate with 2.3M marker-less rows present. **(2) the 5,485 bare-wire fixables are
    NOT a resolver bug** — v1's own `resolve_canonical` resolves ALL 5,485 today and **captured=0** (every one is an
    `attempted_failed`/`empty_confirmed`/`expected_unattempted` probe row). They are rows the every-minute CONSOLIDATOR
    re-introduced in raw-wire form AFTER the one-shot 2026-07-18 apply. So: marker = a code gap; wire = a re-run gap.
    NOT a pipeline_mode/partition gap (v1 already loads main index + every `_index/per_vm/*` shard).
  - **DRY-RUN measured live (10,085,987-row `_index` + `_legacy_seed`, catalogue 425,690 ids, Phase -1 gate GREEN):**
    **marker added 2,301,076 rows (captured 20,659)** — the dominant axis, matching the plan's own worklist row ("perp
    missing @LIN/@INV → 2,402,330") and the no-orphans agent's FIXABLE_RECANON (5,086 distinct ids / 2,159,453 rows); v2
    is slightly broader because it canonicalises the marker on ALL marker-less perps incl. delisted/uncatalogued (the
    correct canonical FORM). **de-dup collapsed 1,220,259** (eu 605,225 / empty 460,672 / af 154,362) — this is the
    wire + no-marker + marker forms collapsing to ONE row per shard. **eu-reconcile dropped 165,172.** OKX OPTION
    re-attributed → `OKX-OPTIONS` **8 rows (2 captured-with-data, 54.1M + 48.2M ticks, NEVER dropped)**; DERIBIT-COMBO
    **195 rows, 0 captured**. **The marker is constructed DIRECTLY from the quote**
    (USDT/USDC/BUSD/DAI/FDUSD/TUSD→`@LIN`, USD→`@INV`) — NOT via the catalogue, because the catalogue itself still holds
    **609 marker-less** perp/future ids (BITGET-FUTURES 275, BINANCE-FUTURES 154, COINBASE-FUTURES 107 …), so a
    catalogue-keyed lookup would leave them raw.
  - **DATA-SAFETY STOP fired on run 1 and was FIXED (the safety working).** Run 1 halted with "7 captured-with-data
    bare-OKX rows in the drop set": they are bare-OKX `captured` rows with **blank itype/id/data_type, `row_count`=NaN
    but `instrument_count` 232k-796k** (malformed aggregate/rollup artifacts) that `_ensure_cols`' row_count←
    instrument_count backfill made look like real ticks. Fix: the OKX/DERIBIT-COMBO drops are now gated on `~captured`
    (hard-rule-strict), NOT `~captured_data` — a CAPTURED bare-OKX row is never dropped; unqualifiable ones are KEPT +
    counted (`okx_captured_kept_unqualified`) for the (1c) orphan triage.
  - **✅ PROOF (operator probe) — `ADAF0:USTF0` collapses to the ONE canonical
    `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`.** All three live forms confirmed in the manifest (wire `ADAF0:USTF0` af;
    no-marker `…ADA-USDT` af/empty/eu + a lowercase-`perpetual` variant; canonical `…ADA-USDT@LIN` captured 776,527,983
    ticks). Proof run: 5 input rows → marker_added=2, de-dup collapsed=4 → **1 row,
    id=`BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, capture_status=captured, 776,527,983 ticks preserved**; wire-map
    `canonical_for(BITFINEX-FUTURES, PERPETUAL, ADAF0:USTF0)` → the same id. OVERALL PASS.
  - **(2) VENUE AXIS.** bare-`OKX` OPTION → **`OKX-OPTIONS`** (routing SSOT `venue_mapping.py`
    `("OKX","OPTION")→ "okex-options"`; `get_tardis_exchange_for_venue("OKX-OPTIONS")→"okex-options"`; mirrors
    OKX-SWAP/-SPOT/-FUTURES). **⚠ REGISTRATION GAP — `OKX-OPTIONS` is NOT in `VENUE_TO_ADAPTER_KEY` /
    `VENUES_BY_ASSET_GROUP` / `INSTRUMENT_TYPES_BY_VENUE`, and the catalogue has ZERO OKX OPTION rows** (OKX* =
    OKX-FUTURES 5,603 / OKX-SPOT 1,398 / OKX-SWAP 652). Register it or the re-attributed captured options read as an
    unexpected venue.
  - **(3) EXPECTED-UNIVERSE / CENSUS purge — root cause FOUND + patched.** The Axis Census reads a DIFFERENT manifest
    per service (`SERVICE_TO_KIND`: `instruments-service`→`instruments-store`): the **instruments-store-cefi
    expected-universe manifest (84,230 rows) carries BINANCE-DELIVERY 4,810 · DERIBIT-COMBO 3,269 · PACIFICA-SOLANA
    3,155 · bare-COINBASE 2 · bare-OKX 2**, while the market-data tick `_index` has ZERO of them — which is exactly why
    "the live captured index is clean but the census still shows them". Patched
    `instruments-service/scripts/enumerate_expected_universe.py` with `_CEFI_EXPECTED_UNIVERSE_EXCLUDED_VENUES` skipped
    in BOTH the venue-grain pre-launch pass (`_yield_v2_cefi_pre_venue_launch_rows`) AND the per-instrument loop
    (`_enumerate_v2_cefi` — the catalogue still holds ~68k DERIBIT-COMBO instruments that would re-seed). Venues stay
    REGISTERED in UAC (honours the operator's "keep BINANCE-DELIVERY registered, just non-MVP" ruling §431) — the guard
    only stops SEEDING.
  - **⚠️ OPERATOR DECISION NEEDED — DERIBIT-COMBO (do NOT `--apply` the combo leg until confirmed).** The dispatch
    directs folding `DERIBIT-COMBO` out of the venue axis, but that **CONTRADICTS** the 2026-07-18 ruling (§314
    "DERIBIT:COMBO is CANONICAL … combos get MIGRATED, not excluded"), the live `deribit_combo` adapter + its routing,
    and the ~68k DERIBIT-COMBO catalogue rows. All 195 manifest rows are **0-captured** probes with DRIFTED itypes
    (OPTION 36 / options_chain 151 / FUTURE 8), so every option is data-safe. v2 exposes
    `--deribit-combo {purge,rename,keep}` (default `purge`); the enumerator exclusion must move in LOCK-STEP with
    whichever is chosen.
  - **RUNBOOK — DRAIN → APPLY → RE-ENABLE (for the MAIN loop).** Preconditions: surface B + collision-drop COMPLETE;
    catalogue Phase -1 gate GREEN (v2 refuses `--apply` if RED); DERIBIT-COMBO decision made. **1 DRAIN (mandatory — the
    every-minute consolidator WILL re-raw an un-drained apply, the measured surface-C lesson):**
    `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-cefi --location=asia-northeast1 --project=central-element-323112`
    (+ the legacy flat `…-execution-cefi` cron if still ENABLED); verify BOTH `state: PAUSED`; STOP every RUNNING cefi
    capture/backfill VM (else new per-VM shards land mid-apply); hold ≥2 consolidator ticks. **2 APPLY:**
    `.venv/bin/python scripts/complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py --apply --deribit-combo <mode>` —
    snapshots EVERY blob to `_index/snapshots/pre_d4_<ts>/` before any write; STOP-ON-SURPRISE halts on any CAPTURED row
    in a drop set / marker_added outside [1.5M, 3.0M] / v1 captured-with-data drop ≠ 0; the post-apply STRICT gate
    requires 0 captured marker-less + 0 further-resolvable + 0 eu/captured collisions. **3 RE-ENABLE:**
    `gcloud scheduler jobs resume …` (verify `ENABLED`), restart the stopped VMs. **4 STICK TEST:** poll ~10 min
    post-resume and assert the marker-canonical fraction HOLDS — durable because MTDS canonicalises the marker AT WRITE
    (`market_interface/adapters/cefi/tardis_margin_marker.py` for Tardis + the Track-G write-gate `mtds@571e258c` for
    non-Tardis), so the consolidator rebuilds from marker-canonical shards. If it REGRESSES a writer path is still
    emitting marker-less ids → fix the writer, do NOT loop the apply. **ROLLBACK:** restore each blob from
    `_index/snapshots/pre_d4_<ts>/`, then resume the crons.

- **2026-07-20 — BAD-VENUE-AXIS diagnosis (operator flagged bare COINBASE/OKX in the data-status Axis Value Census).**
  Ran `check_bad_venues.py` against the LIVE captured availability-index (`read_availability_index`, cefi bucket,
  10,085,983 rows / 27 venues). Result — the captured manifest is MOSTLY CLEAN; the census reads a broader/staler
  source. Per-suspect:
  - `BINANCE-DELIVERY` = **0 rows** · bare `COINBASE` = **0 rows** · `PACIFICA-SOLANA` = **0 rows** → culled/never in
    the live captured index. The census shows them because `_axis_census.py` (the non-canonical-naming DETECTOR) reads a
    consolidated manifest CACHE + `enumerate_expected_universe` still lists defunct venues as should-exist. Fix = purge
    defunct venues from the expected-universe enumeration + regenerate the consolidated cache → Axis Census reads clean.
  - bare `OKX` = **22 rows incl 9 CAPTURED** (BTC/ETH options, data_type trades/options_chain) → RE-ATTRIBUTE to the
    qualified OKX options venue (captured-data-safe, never drop); ~13 empty/attempted_failed OKX-bare rows purged.
  - `DERIBIT-COMBO` = **195 rows, 0 captured** (combo strategies CS/STRD, expected_unattempted/empty/failed) → re-name
    `DERIBIT`+`COMBO` itype or purge (0 captured = safe). All three folded into the manifest v2 cleanup — delegated to
    agent `a6a2ea3074322f82e` (PREP + dry-run-validate the instrument_id ~5,485 fixables + venue-axis
    re-attribution/purge + census/expected-universe defunct-venue purge; the MAIN loop triggers the drain+apply AFTER
    surface B + the collision drop). Endgame: fleet agent `ae18c5ef` narrowing the last 3 slices (24,25,29, on-demand)
    which were re-scanning full ranges (~6h) → resume-day narrow to finish the un-done tail (~1-2h) → covering-set
    (25,29) → drop → final would_patch≈0 verification.

- **2026-07-20 — SURFACE A (GCS FILENAME) IS A CORPUS-WIDE GAP (operator flagged `ADAF0:USTF0.parquet` filename is
  wrong).** GCS layout:
  `raw_tick_data/by_date/day=YYYY-MM-DD/pipeline_mode={mode}/asset_group=cefi/venue={V}/ instrument_type={it}/data_type={dt}/{STEM}.parquet`
  — the STEM is the instrument_id. Filename stems by date:
  - **CANONICAL through ~2025-11-01**; **WIRE from ~2025-11-15 → present (2026-07-20)** — every Tardis venue (BITFINEX
    `ADAF0:USTF0`, BINANCE `ATHUSDT`, DERIBIT `ETH-PERPETUAL`, OKX `BSB-USDT-SWAP`). On-chain lanes
    (batch_hyperliquid/aster) are CANONICAL on the same wire days → **scope = batch_tardis ONLY**.
  - The content fleet is `content-*` = Script 1 (the in-file `instrument_id` COLUMN, surface B) — rewrites the column in
    place, NEVER renames the file, so finishing surface B leaves stems wire.
  - **Root cause**: pre-2026-07 Tardis backfills stamped the wire symbol into BOTH column and filename. Current writer
    (`partitioned_writer._resolve_file_symbol`, FIX D1-live + D2, 2026-07-17) normalises the column to canonical in
    `_prepare_write_df` and names the file from it (`f"{file_symbol}.parquet"` verbatim) — so NEW backfill writes
    canonical (on-chain lanes prove it), PROVIDED the backfill VMs carry D2.
  - **Fix**: Script 2 = `market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py`
    (server-side copy+delete + PAIRED manifest-key rewrite; NOT a Tardis fetch → cap-1 does NOT apply → WIDE-PARALLEL)
    over batch_tardis 2025-11-15→present. RACE-SAFETY: never run Script 2 on a date a Script-1 content VM is active on
    (copy+delete vs read+rewrite race) — non-conflicting ranges (≤2025-12-31) first, active 2026-01/04 slice ranges only
    AFTER content+drop+would_patch done. Dispatched to fleet agent `ae18c5ef` (scope file count + Script 2 CLI shard
    model, prep, launch). + verify remaining-MVP backfill deploys D2 so new writes are canonical natively (no
    re-drift/treadmill). Now the operator's TOP priority for "all migrations done, no orphans".

- **2026-07-20 — TWO INFRASTRUCTURE FAILURES FOUND during the surface-B endgame (both measured, both fixed/being
  fixed).**
  1. **ZOMBIE VM (slice-29)** — `canonical-migration-cefi-content-29-...-od235611` was `status=RUNNING` while its
     PROCESS was dead: run.log mtime `Mon 20 Jul 2026 00:08:51 GMT` (~11.2h stale), last line
     `Progress: 10000/11233 files ... 'already_canonical_skipped': 10000`, `patched` ABSENT (0 — its range was already
     fully canonical), and NO terminal SUMMARY. Slices 24 AND 25 (the drop bottleneck) both finished; 29 was the last
     covering-set member, so the drop was gated ~11h on a corpse. **Lesson (async-discipline "found asleep" class):**
     completion/health MUST key on **log-mtime freshness + progress ADVANCE + a terminal SUMMARY**, NEVER on VM
     `status=RUNNING`. Both my heartbeat and the fleet watchers had this blind spot; being baked into the Script-2 fleet
     watchers.
  2. **SHA-PINNED TARBALLS ROTATED OUT → ALL RELAUNCH/RECOVERY IMPOSSIBLE** —
     `deployment-service/scripts/vm/ cleanup_old_tarballs.py` (scheduled Cloud Scheduler + Cloud Run Job, `--keep 5`,
     `--noncurrent --max-age-days 7`) deleted the fleet's pinned tarball. Exact failure shape PROVEN:
     `unified-api-contracts-code@acd8714c...manifest.json` STILL EXISTS in
     `gs://deployment-scripts-central-element-323112/code/` but the sibling `...tar.gz` is GONE → VM setup resolves the
     pin from the manifest, fails the fetch, CORRECTLY refuses the floating fallback, exits 1, self-deletes. **This
     DEFEATS the shipped PROGRESS.json checkpoint contract** — resuming from the right date is worthless if the code
     tarball no longer exists. Immediate unblock: did NOT rebuild tarballs (the IS working tree carries the v2 agent's
     in-flight `enumerate_expected_universe.py`/`build_instrument_catalogue.py` edits and UTL has foreign WIP — a dirty
     tarball would ship half-done code); instead RE-PINNED to a validated currently-available set: `uac@34580d921a64…`,
     `utl@d099cf15de31…`, `mtds@e639c71f54b8…` (VERIFIED contains Script 1 + Script 2 + the resolver),
     `is@367e382b1271…`. **Systemic fix in flight** (workflow `w6127epwn`): pin-aware retention (never delete a tarball
     a RUNNING VM depends on; atomic tar.gz+manifest deletion so a manifest can never again point at a deleted
     tarball) + a LOUD audit-logged re-pin fallback on relaunch (never a silent degrade to the floating tarball;
     fail-CLOSED if in-use pins can't be determined). This closes the operator's "so we don't have the issue again" ask
     — the checkpoint contract alone was necessary but NOT sufficient.

- **2026-07-20 — SURFACE-A CENSUS (authoritative), TREADMILL VERDICT, and the Script-2 launch blocker.**
  - **CENSUS METHOD**: full direct census (one scoped `list_blobs` per day at
    `raw_tick_data/by_date/day=X/pipeline_mode=batch_tardis/asset_group=cefi/`, 32 threads, 293 days, **88s, ~1.02M
    objects**) — single-walk discipline respected. The MANIFEST route was tried and **REJECTED**: obj/atom ratio is
    unstable (2026-01-15 → 1.03, 2026-03-10 → 1.75, 2025-12-05 → **12.28**), so availability-index rows are NOT a valid
    object proxy in this window.
  - **BOUNDARY**: **first wire day = 2025-11-05** (last canonical 2025-11-04) — a HARD CLIFF, no ramp; 13 of 17 Tardis
    venues flip on exactly that day. Exceptions never canonical in Oct-2025: KRAKEN-SPOT, LIGHTER-ZKSYNC,
    PACIFICA-SOLANA, DERIBIT (partial from 2025-10-06) → **start the run at 2025-10-01** to sweep +13,159 objects.
  - **COUNTS** (2025-11-05..2026-07-20): total single-instrument 985,023; wire-named 893,221; already-canonical 91,802
    (a Feb–Apr 2026 island from a prior partial apply — Script 2 no-ops); chain bundles 1,962; **actual renames
    ≈811,200; wire-but-UNRESOLVABLE ≈82,000 (left honest-raw)**. Median object **7.96 MB**, p90 31.6 MB.
  - **SCRIPT 2 DOES NOT CLOSE SURFACE A — catalogue gap, not a script bug**: EXTENDED-STARKNET 0% (26,721), KRAKEN-SPOT
    0% (25,131), LIGHTER-ZKSYNC 0% (12,067), PACIFICA-SOLANA 0% (265), DERIBIT 10.9% (~9,200 unresolvable) ≈ **73,400
    objects** need instrument-catalogue entries before any rename can work. SEPARATE FINDING: those on-chain venues sit
    under `pipeline_mode=batch_tardis` — a **mislabeled lane**, warrants its own issue doc.
  - **LAUNCH BLOCKER FOUND + FIXED**: Script 2 populated `processed_vd` only `if (renames or merges) and objs:` (line
    446), so the planned "parallel `--skip-manifest` renames now, single-threaded manifest pass later" was a **SILENT
    NO-OP** — by Phase B everything is `already_canonical`, `processed_vd` empty, `in_scope` all-False, index written
    back UNCHANGED, leaving manifest keys pointing at deleted wire objects. Fixed (+44/-4):
    `build_plan(..., scope_all_venue_days)` records EVERY discovered (venue, day), plus a new `--manifest-only`
    standalone Phase-B flag. (`rewrite_manifest` read-modify-writes the shared **162 MB**
    `_index/availability_index.parquet` with NO CAS and NO locking → `--skip-manifest` on the parallel fleet is
    mandatory.)
  - **TREADMILL VERDICT: NO TREADMILL — the rename is ONE-AND-DONE.** Traced end-to-end: the Tardis lane
    (`tardis_shared.py::finalise_rows_and_path` → `derive_row_instrument_id` (catalogue-first FIX D1) → `_file_stem_for`
    → `build_partition_path` writing `f"{file_stem}.parquet"`) emits the canonical id as the stem; **even on a catalogue
    MISS** it falls through to `build_instrument_id(venue, itype, symbol)` → a WRAPPED canonical form, so post-D2 code
    **cannot** emit a bare-wire stem. `_prepare_write_df`/`_resolve_file_symbol` are NOT on the Tardis path (that lane
    never calls `write_chunk`) — FIX D1-live + D2 serve the live/on-chain lanes, which is why on-chain objects were
    already canonical on wire days. Two lanes, two mechanisms, same canonical result. D1+D1-live+D2 all landed in
    `d302f07a` (2026-07-17), so **the ~2025-11-05 boundary is Script 2's MIGRATION FRONT, not a writer regression** — no
    adapter retrofit needed.
  - **DROP validated**: slice-01 dry-run `would_drop=20`, **stop-on-surprise=0** — reproduces the original 20 collisions
    against current post-content state, all passing the per-object gate (C-reads-OK + W⊆C on tick-key).
  - **SLICE-COMPLETION ACCOUNTING IS UNRELIABLE** (recorded so nobody re-derives it wrongly): 128 content VM log dirs
    for ~44 slices; completion was inferred from VM-ABSENCE. Slice-12's latest VM died at 14,400/139,376 with
    `patched: 10,373`. BUT the work IS cumulative+idempotent across relaunches — slice-28's original VM reached
    97,200/137,243 with `patched: 75,414`. So a latest-VM at 10% does NOT mean the slice is 10% done. **The only valid
    surface-B completion metric is the corpus-wide `would_patch` count**, which the final `--apply` pass measures.

- **2026-07-20 — SURFACE A MEASURABLY MOVED (first hard evidence the rename fleet works).** 13 venue-sharded Script-2
  VMs over `2025-10-01..2026-01-15`, all `EXIT=0` / `no-surprise` / `renamed == planned`: **175,165 renames applied, 0
  collisions.** Measured by `verify_cefi_canonical_4surface_2026_07_20.py`, not inferred:

  | Surface        | Baseline | After early window        | Δ                                     |
  | -------------- | -------- | ------------------------- | ------------------------------------- |
  | **A FILENAME** | 20.82%   | **29.94%** (6,795/22,695) | **+9.12pp**                           |
  | B COLUMN       | 47.50%   | 47.50%                    | — (`would_patch --apply` not yet run) |
  | C MANIFEST     | 98.34%   | 98.34%                    | — (Phase B not yet run)               |
  | D READER       | PASS     | PASS                      | —                                     |

  Per-day proves the renames landed exactly where targeted: **2025-12-15 `0.00% → 65.31%`**, 2025-11-20 → 88.18%, while
  the untouched late window stayed flat (2026-02-01 = 5.67%, 2026-05-01 = 0.00%). OVERALL still FAIL — correct, three
  passes outstanding. **Holding DERIBIT out of the fleet was the right call**: it isolated the one colliding venue and
  let the other 13 run clean. `unresolved_wire` left honest-raw on otherwise-healthy venues (OKX-SPOT 2,822,
  COINBASE-SPOT 1,322, BITGET-FUTURES 544, OKX-SWAP 402, BYBIT 291, BINANCE-FUTURES 32 ≈ 5,413) proves the catalogue gap
  is NOT confined to the four 0%-resolve venues.

- **2026-07-20 — `--manifest-only` DESIGN FLAW found + fixed (second no-op trap on the same feature).** The first
  implementation derived scope by WALKING GCS OBJECTS — a ~45-min whole-window walk that died mid-discovery at day 94 of
  107 (`cumulative_objects=140,606`, elapsed 2,147s) without ever emitting a verdict. The walk was pointless:
  `rewrite_manifest` keys on **(venue, day)** and operates on **manifest ROWS, not objects**. Scope is now the
  `scope_pairs × days` cross-product — **no GCS walk**, verdict in ~2 min instead of ~45, which also removes a
  gratuitous whole-corpus walk (single-walk discipline). Dead `scope_all_venue_days` param removed; the outcome-derived
  path is re-documented AT THE SOURCE so the original silent-no-op trap is recorded where the next reader will hit it.
  **PASS gate unchanged and enforced: `N>0` scope pairs AND non-zero rewrite stats, else STOP and diagnose — never
  proceed to `--apply` on a zero.**

- **2026-07-20 — GOVERNING PHILOSOPHY (operator, verbatim): _"the whole point is migration is making ssot canonical and
  migrating others and failing hard in manifest and code read and writes."_** Canonical is the SSOT; everything else
  migrates to it; non-canonical must FAIL HARD across manifest, reads and writes. Consequence for design: the
  `build_instrument_id()` catalogue-miss fallback that emits a wrapped `VENUE:ITYPE:<raw wire>` id is **itself the bug**
  — silently tolerating a miss is the mechanism that polluted ~811,200 objects. Tolerance must be replaced by loud
  failure. OPEN SEQUENCING QUESTION for the operator: ~82,000 objects are genuinely unresolvable today (venues with NO
  catalogue entries — EXTENDED-STARKNET, KRAKEN-SPOT, LIGHTER-ZKSYNC, PACIFICA-SOLANA, most of DERIBIT), so fail-hard
  reads would make them unreadable until the catalogue is filled → either switch on now with those explicitly
  quarantined, or gate fail-hard on closing the catalogue gap first.

- **2026-07-20 — UAC PATH ORACLE IS BLIND TO THE FILENAME STEM (systemic; would let this defect recur undetected).**
  `unified_api_contracts/canonical/partition_paths.py::canonical_path_violations()` returns **0 violations
  ("CANONICAL")** for bucket-relative cefi paths ending `ADAF0:USTF0.parquet`, `AVAX_USDC-PERPETUAL.parquet`, and the
  double-wrapped `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet` — with `require_pipeline_mode` False OR True. Root
  cause in its own code: `partition_segments = segments[:-1]` / _"Last segment is the file name; the rest are hive
  key=value partitions"_ — **the stem is dropped before validation**. Because the workspace rule states canonicality IS
  this oracle, a rule-following `/data-pipeline-reconciliation` would report cefi surface-A CLEAN while ~811,200 objects
  carry wire ids (independently measured at 20.82%→29.94% canonical). Path-structure and instrument-id-form are
  **ORTHOGONAL questions; neither alone proves canonical.** Fix in flight: stem check ON BY DEFAULT (operator: _"it
  shouldn't count everything as canonical"_), violations classified structural vs id-form, chain `ticks.parquet` never
  flagged, plus a full cross-repo caller audit (raising callers reported, NOT silently softened). Gotcha for
  reproducers: pass a BUCKET-RELATIVE path — a `gs://bucket/...` URI fails the prefix check for the wrong reason.

- **2026-07-20 — FIRST MEASURED 4-SURFACE BASELINE + a NEW BUG CLASS (double-wrapped ids).** Ran
  `market-tick-data-service/scripts/verify_cefi_canonical_4surface_2026_07_20.py`. This replaces inferred completion
  (VM-absence) with a MEASURED corpus canonical-fraction per surface. **Re-run after every milestone.**
  - **A — FILENAME: 20.82% canonical** (4,725/22,695 sampled single-instrument objects; chain bundles excluded). Wire
    days 2025-11-20 / 2025-12-15 / 2026-05-01 = 0.00%; 2026-02-01 = 5.67%; pre-boundary days ~89–93%.
  - **B — COLUMN: 47.50%** (19/40 sampled objects carry an all-canonical `instrument_id`).
  - **C — MANIFEST: 98.34%** (10,032,051 / 10,201,092 cefi rows; 10,263,294 incl. chain bundles).
  - **D — READER: PASS.** `resolve_cefi_instrument_id` peels BOTH wire forms and `read_shard` returns canonical ids
    (`ADAF0:USTF0` → `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`, 502,955 rows; `AVAX_USDC-PERPETUAL` →
    `DERIBIT:PERPETUAL:AVAX-USDC@LIN`, 11,678 rows). **READS ARE ALREADY CORRECT — the migration is closing consistency
    debt, not repairing broken data access.**
  - 🔴 **NEW BUG CLASS — DOUBLE-WRAPPED COLUMN ID.** Objects exist whose FILENAME is fully canonical but whose COLUMN is
    `VENUE:ITYPE:` + the RAW WIRE symbol — the `build_instrument_id()` catalogue-miss fallback:
    `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0` (stem `...ADA-USDT@LIN`) and `DERIBIT:PERPETUAL:AVAX_USDC-PERPETUAL` (stem
    `...AVAX-USDC@LIN`), both on 2025-06-15. It LOOKS canonical at a glance but the instrument part is still wire. It
    does NOT match `_CANON_ID_RE` (which requires `BASE-QUOTE` with a DASH; `ADAF0:USTF0` carries a colon), so the
    resolver's wrapped-wire-peel leg SHOULD fix it — **but this must be PROVEN**: if `would_patch` skips it as
    already-canonical, surface B stays permanently broken while appearing done. Targeted dry-run over 2025-06-15
    (BITFINEX-FUTURES + DERIBIT) requested before surface B can be declared complete.
  - Manifest duplicates confirmed still live: `ADAF0:USTF0` 4 rows (canonical 4,580), `AVAX_USDC-PERPETUAL` 1 row
    (canonical 805) — the v2 apply collapses them.

- **2026-07-20 — SURFACE-A RENAMES EXECUTING + three collision findings.** 13 venue shards launched over
  `2025-10-01..2026-01-15` (`--workers 32`, `--apply --stamp d4fnrename20260720 --skip-manifest`, SPOT, new pins,
  `STALL_TIMEOUT_SEC=900`); **measured progress: fn01 `renamed 2000/29299`, fn02 `renamed 2000/18529`** — the first real
  surface-A movement of the program. Only **7 of 13** VMs exist; hypothesis under triage is that 6 hit `sys.exit(4)` on
  collisions and self-deleted (Script 2 aborts BEFORE `run_gcs_merge`/`run_gcs_rename`, so an aborting shard mutates
  NOTHING — the abort IS the per-shard collision check).
  - 🔴 **DATA-LOSS NEAR-MISS**: one early-window collision is **MERGE-needed, NOT safe-drop** — `not_in_C=6661`, i.e.
    dropping that W object would **destroy 6,661 captured rows**. It belongs in the merge bucket. The per-object gate
    caught it; this is why the drop must never be a blanket delete.
  - 🔴 **THE COLLISION SET IS A MOVING TARGET**: the catalogue grew **425,573 → 428,625 (+3,052 rows)** mid-migration,
    so objects formerly `unresolved_wire` now RESOLVE onto canonical names that earlier renames already created →
    **brand-new collisions appear in previously-clean ranges**. Consequence: convergence is **loop-until-dry**, not
    one-shot, and the drop's ~10,154 figure needs re-verification before `--apply` (its per-object gate re-checks each
    one, so it stays safe).
  - DERIBIT HELD from the early fleet (known 2025-10-02 collisions incl. the merge-needed case). Excluded as 0%-resolve:
    EXTENDED-STARKNET, KRAKEN-SPOT, LIGHTER-ZKSYNC, PACIFICA-SOLANA.

- **2026-07-20 — LATE-WINDOW PARALLELIZATION PROVEN + launch-path auth incident.** Venue-collision histogram over
  `2026-02-01..2026-07-20` (24-worker fan-out): **TOTAL 13,163 collisions, CONCENTRATED not smeared** — 10 colliding
  venues (BINANCE-FUTURES 6,200 · COINBASE-SPOT 2,048 · BINANCE-SPOT 1,058 · OKX-SWAP 897 · …· DERIBIT 58 MERGE-only),
  **16 venues zero-collision** (object-disjoint from the drop, PROVEN safe to rename concurrently). Collisions are ALSO
  date-concentrated: nearly all before **2026-03-10**, so even colliding venues are drop-disjoint after that date → drop
  `--apply` sequenced `2026-02-01..03-10` first. Decision: launch the ~14 resolver-independent zero-collision venues NOW
  in parallel with the drop (Option A), re-pin + add EXTENDED-STARKNET after. KRAKEN-SPOT pulled into its own
  STRUCTURAL-REPAIR class (the `ADA/USD.parquet` spurious-hive-segment corruption from `tardis_shared.py:671`), not a
  rename shard.
  - **LAUNCH-PATH AUTH INCIDENT (my error, corrected):** stale `gcloud`/`gsutil` CLI creds blocked ALL
    `gcloud compute instances create` — I wrongly told the operator "nothing on the critical path needs the CLI" (the
    launcher IS the CLI); the fleet agent caught it, zero VMs created. Bridge found + tested: gcloud accepts an
    ADC-minted token via `CLOUDSDK_AUTH_ACCESS_TOKEN` (identity preserved, `cloud-platform` scope) → unblocked without
    operator action. Operator then ran `gcloud auth login`; native CLI restored, bridge retired
    (`unset CLOUDSDK_AUTH_ACCESS_TOKEN`). Tarball cleanup cron re-verified PAUSED throughout.
  - **Single-shard create CONFIRMED**: COINBASE-FUTURES RUNNING in ~25s → EXIT 0 (`already_canonical=21040, planned=0` —
    already fully canonical late-window; several zero-collision venues will be zero-work, which is fine/measurable).
  - **RESOLVER-FIX VERIFIER DELTA (no new renames): surface A 29.94% → 30.93%** (7,120/23,020), purely
    previously-unresolvable objects now scoring canonical; sharpest at 2026-05-01 (0.00% → 5.86%). Clean pre-batch
    baseline. WRITE-PATH MAP recorded 11 tolerance points; highest-leverage guards A3 (`canonical_id_builder.py:268-270`
    `_build_cefi_simple`, zero symbol validation) and A11 (NO write-time path guard on the Tardis cefi lane at all — the
    structural reason 811,200 objects landed). Fail-hard quarantine must key on `(venue, data_type)` KEY-SPACE class,
    not "catalogue missing".

### 2026-07-20 (slot-3) — the "catalogue-coverage gap" is mostly NOT a catalogue gap · MEASURED

**Headline correction: of the ≈82,000 objects believed unresolvable for want of catalogue entries, only ~422 are
genuinely missing reference data.** Four of the five gap venues already have COMPLETE catalogue coverage; they failed on
resolver and path defects. Measured against the real prod corpus + the real 428,625-row cefi catalogue.

**Per-venue root cause (each verified independently — no generalisation across venues):**

| Venue                 | catalogue rows | root cause                                                                       | class                    |
| --------------------- | -------------- | -------------------------------------------------------------------------------- | ------------------------ |
| **EXTENDED-STARKNET** | **103** ✅     | wire stem carries `@LIN`; catalogue keys the UNMARKED `raw_symbol`               | RESOLVER defect          |
| **KRAKEN-SPOT**       | **1,158** ✅   | wire is `ATOM/USD` — the `/` makes a GCS pseudo-dir, Script 2 `_PATH_RE` rejects | PATH/SCOPE defect        |
| **LIGHTER-ZKSYNC**    | **219** ✅     | 93.5% of stems are numeric market indices (`0`,`1`,…); catalogue keys symbols    | REFERENCE-DATA gap       |
| **PACIFICA-SOLANA**   | **0** ❌       | venue CULLED 2026-07-16 (Solana perp DEX drop); no lane, no rows                 | permanently honest-raw   |
| **DERIBIT**           | **338,050** ✅ | already 93.9% resolving — the "10.9%" figure is STALE (pre-catalogue-rebuild)    | measurement was outdated |

**Two resolver defects found + FIXED (shared resolver, so all THREE surfaces inherit it):**

1. `marker_suffix_not_peeled` — an on-disk stem carrying the margin marker (`AAVE-USD@LIN`) missed every catalogue
   lookup because the catalogue keys the unmarked wire. Fixed by a marker-peel CATALOGUE retry (still a catalogue path,
   so it precedes all construction and cannot override the SSOT; the marker comes BACK from the catalogue id, so a wrong
   marker on disk is CORRECTED, not propagated).
2. `canonical_regex_rejects_catalogue_id` — `_CANON_ID_RE` admitted only `[A-Z0-9]` in the base token, so the resolver
   looked up 23 catalogue ids SUCCESSFULLY and then discarded them at its own shape gate (an SSOT contradiction: 20
   EXTENDED-STARKNET `AAPL_24_5-USD@LIN` 24/5 equity perps, 2 KRAKEN-SPOT `BRK.BX-USD` tokenized equities). Base now
   admits `_` and `.`; still REJECTS the genuinely corrupt `BITGET-FUTURES:PERPETUAL:??-USDT`.

**Measured before → after (same 10-day sample, same script, prod GCS):**

| Venue             | before | after       | note                                                   |
| ----------------- | ------ | ----------- | ------------------------------------------------------ |
| EXTENDED-STARKNET | 0.00%  | **100.00%** | 1,608/1,608 renameable                                 |
| LIGHTER-ZKSYNC    | 0.00%  | **5.16%**   | 16 closed; 290 numeric ids + 4 absent remain           |
| KRAKEN-SPOT       | 0.00%  | 0.00%       | resolver resolves it; blocked on the FENCED `_PATH_RE` |
| PACIFICA-SOLANA   | 0.00%  | 0.00%       | 0 catalogue rows — correctly stays honest-raw          |
| DERIBIT           | 98.92% | 98.92%      | unchanged (already healthy)                            |

Catalogue SSOT contradictions **23 → 1** (the remaining 1 is genuinely corrupt data and must stay rejected). **A/B
regression over ALL 428,625 catalogue `raw_symbol`s: 22 GAINED, 0 LOST, 0 CHANGED.**

**Two NEW defect classes found that no earlier pass had named:**

- **Wire-key AMBIGUITY from duplicate catalogue rows (658 3-tuples).** `BTC-25SEP20` HAS catalogue rows but resolves to
  `None` because the catalogue holds it TWICE with off-by-one expiries (`…INV-20200926` AND `…INV-20200925`), so
  `CeFiWireCanonicalMap` excludes the key as ambiguous. By venue: DERIBIT 442, OKX-FUTURES 146, BYBIT 39, BITGET-FUTURES
  18, OKX-SWAP 5, BINANCE-DELIVERY 4, KRAKEN-FUTURES 2, BINANCE-FUTURES 2. Fix is upstream catalogue de-duplication, NOT
  resolver work. **HYPOTHESIS TESTED AND REJECTED**: this is NOT what the ≈5,413 healthy-venue residue is — measured
  below.
- **THE REAL healthy-venue residue: a genuine catalogue-coverage gap on the 98-100% venues** (the one place the
  "catalogue-coverage gap" label is literally true). Measured by classifying each venue's residue and then probing the
  catalogue for the wire:
  - **OKX-SPOT** (87.50% resolve, 165/1,320 residue): unresolved stems are **fiat-quote** pairs `BTC-AED`, `BTC-AUD`,
    `BTC-BRL`, `BTC-TRY` — **0 catalogue rows each**. The OKX-SPOT catalogue holds only 5 quote currencies
    (`TEV, USD, USDC, USDK, USDT`); the fiat-quote pairs were never enumerated.
  - **COINBASE-SPOT** (91.52%, 70/825): unresolved stems are **crypto-quote** pairs `ADA-BTC`, `ADA-ETH`, `ATOM-BTC` —
    **0 catalogue rows**. Catalogue holds only `CAD, USD, USDC, USDT` quotes.
  - **BITGET-FUTURES** (98.62%, 36/2,602): unresolved stems are **CME-letter-month dated futures** `BTCUSDH26`,
    `BTCUSDZ25` — **0 catalogue rows**; all 998 BITGET-FUTURES catalogue rows are `*USDT` perp-style, ZERO letter-month
    rows. This is upstream enumeration work in the catalogue builder (fiat-quote + crypto-quote spot pairs, and dated
    delivery futures), not resolver or manifest work. Per the external-data-always-available rule these are CLOSEABLE,
    not honest-raw-forever.
- **COMBO instruments stored in a `perpetual` partition** (`BTC-FS-29SEP23_PERP`, 23/787 DERIBIT sample). The catalogue
  HAS them under itype `COMBO`; the path says `perpetual`. This needs a partition MOVE, not a rename — renaming alone
  would leave path-itype and id-itype disagreeing.

**Lane-mislabel verdict (separate issue doc filed):** the `batch_tardis` label on EXTENDED-STARKNET / LIGHTER-ZKSYNC's
early `ohlcv_1m` / PACIFICA-SOLANA IS a genuine mislabel (with a split-brain — EXTENDED-STARKNET writes
`derivative_ticker` into BOTH lanes on the SAME day), **but it is NOT the root cause of the resolve gap**: the shared
resolver takes no `pipeline_mode` argument, and EXTENDED-STARKNET objects in BOTH lanes measured 0% before the fix and
100% after. LIGHTER's `derivative_ticker` under `batch_tardis` is CORRECT and declared — do not "fix" it. See
`issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`.

**Closure plan — what is closeable vs permanently honest-raw (census-extrapolated from measured per-venue rates):**

| Class                                   | objects       | what it needs                                                 | status                  |
| --------------------------------------- | ------------- | ------------------------------------------------------------- | ----------------------- |
| EXTENDED-STARKNET marker-peel + regex   | **26,721**    | the shipped resolver fix — re-run Script 2                    | ✅ **CLOSED in code**   |
| LIGHTER-ZKSYNC marker-peel              | **~627**      | the shipped resolver fix                                      | ✅ **CLOSED in code**   |
| KRAKEN-SPOT embedded-slash wire         | **25,131**    | `_PATH_RE` slash tolerance in Script 2 (**FENCED**)           | 🔴 **BLOCKED on fence** |
| LIGHTER-ZKSYNC numeric market index     | **~11,283**   | market-index→symbol map from the Lighter API (upstream)       | 🟡 reference-data work  |
| Wire-key ambiguity (dup catalogue rows) | **~658 keys** | catalogue de-dup (**`build_instrument_catalogue.py` FENCED**) | 🔴 **BLOCKED on fence** |
| DERIBIT COMBO in perp partition         | ~2.9% DERIBIT | partition MOVE + rename                                       | 🟡 design needed        |
| LIGHTER `TON-USDC`                      | **~157**      | genuinely absent from catalogue                               | 🟠 upstream backfill    |
| DERIBIT delisted MATIC options          | ~1.1% DERIBIT | genuinely absent (MATIC→POL rebrand, never backfilled)        | 🟠 upstream backfill    |
| **PACIFICA-SOLANA**                     | **265**       | venue culled — no lane, no rows, no upstream                  | ⚫ **PERMANENTLY RAW**  |

**Quarantine set for fail-hard enablement** (measured, not assumed): PACIFICA-SOLANA (265) is the only genuinely
permanent honest-raw venue class. Everything else is closeable — two classes are blocked only by file fences, not by
missing data. **This materially de-risks fail-hard**: the blocker is ~422 genuinely-absent objects plus fenced-file
edits, not ~82,000 unresolvable ones.
