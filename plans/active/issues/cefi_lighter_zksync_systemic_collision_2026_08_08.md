---
doc_type: issue
title: CeFi LIGHTER-ZKSYNC systemic wire/canonical dual-write collision — 11,494 objects across 30+ dates (2026-08-08)
summary: >-
  During the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume sequence's 4-venue safe-residual
  apply, the LIGHTER-ZKSYNC leg — previously characterized as "zero collision risk" per that doc's Finding 10 — hit
  STOP-ON-SURPRISE with 11,494 genuine collisions spanning 30+ distinct dates (2026-04-18, plus a dense run
  2026-06-24..2026-07-14 at ~157/day, ~157 = the full LIGHTER-ZKSYNC PERPETUAL symbol universe). This is a materially
  larger/different-shaped population than the single-day precedent (Finding 8/10's HYPERLIQUID/ASTER 6-date pattern) —
  it looks like an ongoing, ~2-month ranging dual-write (both wire-form and canonical-form objects being written for the
  same day/symbol slot), not a one-off transitional artifact. Zero mutation occurred (script correctly refused).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, manifest, chain-drop, late-renames, collision, data-correctness]
related:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_finalize_2026_08_08.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
  ]
created: 2026-08-08
author: unknown
parent_epic: cefi_master
priority: P2
source: >-
  Discovered while resuming cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md's sole open todo (the
  2,962-object safe-residual venue-scoped rename apply), slot 18, 2026-08-08.
resolved_by:
locked_by:
assigned_vm: planning
assigned_role: data_engineering
code_refs:
  [
    market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    market-tick-data-service/scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    market-tick-data-service/scripts/audit_lighter_zksync_dual_write_collision_2026_08_08.py,
  ]
---

# CeFi LIGHTER-ZKSYNC systemic wire/canonical dual-write collision

## What I found

Resuming `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`'s sole open todo (apply the 2,962-object safe
residual across EXTENDED-STARKNET/LIGHTER-ZKSYNC/BYBIT-SPOT/COINBASE-FUTURES — all 4 previously declared "zero collision
risk" per that doc's Finding 10 full-range scan from 2026-07-25):

- **EXTENDED-STARKNET**: applied cleanly. 3,168 renamed (grown from the original 704 estimate — expected drift, more
  data accumulated since 2026-07-25), 0 errors, manifest updated.
  `canonical-migration-cefi-late-renames- 20260808-134921`, exit 0.
- **LIGHTER-ZKSYNC**: first full-range attempt (`...-150429`, retried after one prior stall-kill on `...-140152`) hit
  STOP-ON-SURPRISE: 40 genuine collisions, all on exactly 2026-04-17 (all PERPETUAL symbols) — same shape as the doc's
  own established Finding 8/10 precedent (a single transitional day, safe to exclude via date-range split). Split into
  two date-range applies excluding that day:
  - Range 1 (2025-11-01..2026-04-16): `...-153907`, exit 0, 0 renames needed in this sub-range (all LIGHTER-ZKSYNC
    activity postdates 2026-04).
  - Range 2 (2026-04-18..2026-07-24): `...-154345`, hit STOP-ON-SURPRISE again — **this time 11,494 unhandled
    collisions** across 30+ distinct dates: 2026-04-18 (the day right after the excluded one) plus a dense, near-daily
    run from 2026-06-24 through 2026-07-14 at ~156-157 collisions/day. 157 is the apparent full LIGHTER-ZKSYNC PERPETUAL
    symbol count (0G, 2Z, AAPL, AAVE, ADA, AERO, AMD, AMZN, APEX, APT, ARB, ARC, ASML, ASTER, AVAX, AVNT, AXS, AZTEC,
    BCH, BERA, BIRB, BMNR, BNB, BTC, COIN, CRCL, CRO, CRV, DASH, DIA, DOGE, DOLO, DOT, DUSK, DYDX, EDEN, EDGE, EIGEN,
    ENA, ETH, ... — same 40 seen in the first attempt reappear plus many more). Zero mutation (STOP-ON-SURPRISE fires
    before any write). `...-154345`, exit 4.
- **BYBIT-SPOT / COINBASE-FUTURES**: not yet characterized against this finding — proceeding with them separately
  (unaffected by this LIGHTER-ZKSYNC-specific issue per the original zero-collision breakdown).

## Why it matters

This is a **different-shaped population** than every prior collision finding in the parent doc:

- Finding 8/10's precedent (HYPERLIQUID/ASTER/DERIBIT) was a **handful of dates** (6, later a mislabel-driven trickle) —
  bounded, explicable as a one-off writer-transition artifact, safely excludable via date-range split.
- This LIGHTER-ZKSYNC population is **~30+ dates, densely packed across nearly 3 weeks in a row** (2026-06-24 through
  2026-07-14), each day showing essentially the **entire symbol universe** colliding — not a handful of stragglers. That
  shape (whole-universe, sustained, near-daily) is much more consistent with an **ongoing dual-write** (a live/forward
  pipeline now writing canonical-form filenames directly for LIGHTER-ZKSYNC, while something — a parallel backfill, a
  stale writer path, or a re-capture — is ALSO still writing wire-form for the same slots) than with a single discrete
  transition event.
- Continuing to date-split around this would mean excluding ~30 individual dates (or wide contiguous ranges) just to
  force the "safe residual" through — that stops being a safe, bounded, worker-determinable action and starts being
  exactly the kind of open-ended judgment call `data_engineering.md` says to escalate rather than absorb.
- No data was lost or merged incorrectly — the STOP-ON-SURPRISE gate did exactly its job. This is a report of a live,
  ongoing write-path issue, not a required data recovery.

## Recommended decision

1. **Root-cause investigation (bounded, worker-determinable)**: for a sample of the 2026-06-24..2026-07-14 dates, pull
   both the wire-form and canonical-form objects' capture timestamps (`timeCreated` via `gsutil stat` or the manifest's
   own capture columns) to determine whether this is (a) a live pipeline now writing canonical-form going forward while
   a **still-running historical backfill** independently re-captures the same recent days in wire-form (classic race,
   self-resolving once the backfill catches up / is stopped), or (b) two genuinely different, sustained capture paths
   that will keep colliding indefinitely (a real writer misconfiguration needing a code fix, not just a migration
   exclusion).
2. **Do NOT force a rename/merge/delete decision on this population without that investigation** — per the parent doc's
   own established policy (Finding 2/5/8), "two real captures, no way to prefer one without a policy call" defaults to
   leave-both-as-is until characterized.
3. Once characterized: if (a) self-resolving, re-run the LIGHTER-ZKSYNC Range 2 apply after the backfill completes (no
   code change needed, just a later retry). If (b) a genuine writer bug, the fix belongs in `tardis_shared.py`'s
   canonicalization path (same file/pattern as the parent doc's Finding 9 recurrence fix) — scope that as its own
   follow-up once root-caused.
4. The remainder of the resume sequence (BYBIT-SPOT, COINBASE-FUTURES, cron resume, loop-until-dry verifier, 4-surface
   re-proof) is unaffected and proceeds independently — see the parent todo's own progress log.

## Root-cause findings (2026-08-08 audit, slot 20)

**Method**: read-only audit script
`market-tick-data-service/scripts/audit_lighter_zksync_dual_write_collision_2026_08_08.py` (committed as evidence/
tooling; no rename/delete/merge — reuses the SAME shared resolver + single-walk-safe per-day discovery the migration
scripts use). Sampled 8 evenly-spaced dates across the reported 2026-06-24..2026-07-14 dense run, plus 3 supplementary
post-window dates (2026-07-20, 2026-07-28, 2026-08-05) to test whether the pattern is still recurring today. For every
(wire-form, canonical-form) pair coexisting in the same (day, pipeline_mode, data_type) group, fetched both objects' GCS
metadata (`last_modified` as the `timeCreated` proxy) and an exact row count (parquet footer `num_rows`, no full
decode).

**Findings**:

1. **The colliding population is 100% `pipeline_mode=batch_tardis`, `data_type=derivative_ticker`** — every sampled
   pair, no exceptions. Not a general capture-path issue.
2. **Row counts are IDENTICAL between the wire-form and canonical-form object in every sampled pair** (e.g.
   `LIGHTER-ZKSYNC:PERPETUAL:AAVE` on 2026-06-24: both 73,355 rows) — these are genuine duplicate captures of the SAME
   underlying data, not a partial-vs-complete mismatch. Byte size differs (wire-form consistently larger despite equal
   row count — a schema/dtype difference, not a content difference).
3. **`canonical_last_modified` clusters tightly at 2026-07-25T04:22-04:35Z (most dates) and 2026-07-27T00:58Z**
   (2026-07-11 only) — i.e. an EARLIER canonicalization pass wrote the canonical-form objects for this whole window in
   one bounded run. This matches the parent doc's own "Finding 8/10 full-range scan from 2026-07-25" characterization of
   LIGHTER-ZKSYNC as zero-collision-risk AT THAT TIME.
4. **`wire_last_modified` is ALWAYS later than `canonical_last_modified`** (72-348h later) and falls into exactly TWO
   tight clusters: `2026-07-30T00:57-01:00Z` (dates 2026-07-05..2026-07-14) and `2026-08-08T16:31-16:37Z` — i.e. TODAY,
   ~4h before this audit ran (dates 2026-06-24..2026-07-03). The wire-form copies were written well AFTER the
   already-canonical objects existed, in a pattern consistent with a backfill walking through this date range over
   multiple separate runs/sessions.
5. **Zero collisions on the 3 post-window dates (07-20, 07-28, 08-05)** — the live/forward capture path is clean; the
   dual-write is confined to this specific historical re-processing of the pre-07-15 window.
6. **The live write path (`tardis_shared.py`) has built fully-canonical filenames via `build_canonical_instrument_id` /
   `_file_stem_for` since commit `d302f07a` (2026-07-17)** — well before every wire-form timestamp observed. No evidence
   of an ongoing code-level dual-write bug in the current default (live/websocket) write path.
7. **Identified the active culprit**: VM `cefi-fwd-20260808-123230` (`VM_TASK=cefi-backfill`,
   `VM_SERVICE=market_tick_data_service`, `VM_OPERATION=download`, RUNNING, `VM_SHUTDOWN_ON_COMPLETION=true`) is
   executing (confirmed via serial-port log, launched 2026-08-08T12:34:45Z):
   `python -m market_tick_data_service --operation download --mode batch --asset-group CEFI --start-date 2026-06-05 --end-date 2026-08-05 --force --data-types derivative_ticker`
   — a BOUNDED, `--force` (unconditional overwrite) historical re-download of `derivative_ticker` across the whole
   2026-06-05..2026-08-05 window (which fully contains the reported 2026-06-24..2026-07-14 dense run). This VM (and its
   immediate predecessors today) is tracked in detail, independently, by
   `/plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` — per that doc's own progress
   log, elapsed ~90h as of the latest update, frontier at 2026-07-11, **measured ETA ~2026-08-12T05:00Z** (throughput
   ~0.67 days/hour). That doc's own venue-coverage checks were scoped to the 6 CARRY_BASIS_PERP venues
   (BINANCE-FUTURES/BYBIT/OKX-SWAP/KRAKEN-FUTURES/BITGET-FUTURES/BITFINEX-FUTURES); this audit independently confirms
   the SAME VM's unscoped (`--asset-group CEFI`, no `--venue` filter) `derivative_ticker` download is ALSO producing
   wire-form LIGHTER-ZKSYNC writes in exactly its target window.

**Determination: (a) SELF-RESOLVING RACE**, per the Recommended-decision framing above — a still-running, BOUNDED
historical backfill (`cefi-fwd-20260808-123230`) is independently re-capturing `derivative_ticker` for dates an earlier
canonicalization pass (2026-07-25/07-27) already normalized, using a base-only (missing `-USDC@LIN`) file stem. The VM
self-terminates on completion (`VM_SHUTDOWN_ON_COMPLETION=true`, explicit `--end-date`) — this is not an indefinitely
recurring writer misconfiguration. No code change is required in `tardis_shared.py`'s live canonicalization path (it has
been correct since 2026-07-17); residual uncertainty on why THIS SPECIFIC `--force --data-types derivative_ticker`
historical-download code path emits a base-only stem is not resolved here (would need a deployed-code-version read on
the VM) but does not change the recommended next action either way.

**Next action (todo 2, below) is gated on the `cefi-fwd-20260808-123230` VM lineage completing** (~2026-08-12T05:00Z per
the sibling doc) — do NOT re-attempt the Range 2 apply before then; it would re-hit the same collisions for whatever
dates the backfill is still mid-processing, and could race a live write.

## Todos

- [x] ✅ [DATA] P2. **Root-cause the LIGHTER-ZKSYNC wire/canonical dual-write collision** — market-tick-data-service
      (slot 20, 2026-08-08). Audit script + findings above; determination = (a) self-resolving race, culprit identified
      (`cefi-fwd-20260808-123230`, ETA ~2026-08-12T05:00Z). Zero mutation — audit only, per scope.
- [ ] [DATA] P2. **Re-attempt the LIGHTER-ZKSYNC Range 2 (2026-04-18..2026-07-24) `cefi-late-renames` apply** —
      **Original gate (culprit `cefi-fwd-20260808-123230` terminated) is MET — confirmed deleted 2026-08-09T02:13:58Z.**
      **2026-08-10 dry-run VERDICT: still BLOCKED — genuine unhandled collisions persist** (see Progress Log entry):
      `would_rename=3524` but the tool logs `Refusing to proceed to --apply while unhandled collisions exist` (e.g.
      `LIGHTER-ZKSYNC:PERPETUAL:APT-USDC@LIN` etc. on 2026-04-18). The premise that culprit termination clears the
      collision population is empirically FALSE. Unblock = the BROAD-comparison fix tracked in the new P2 todo below
      (extend `_confirm_would_patch_duplicate`'s exclusion set per Finding 11), then re-run this apply. Sequence once
      the fix lands: confirm fresh spot-check, pause cron, verify PAUSED, run, verify 0 unhandled collisions, resume
      cron, verify ENABLED. (repo: market-tick-data-service, deployment-service)

- [x] ✅ [DATA] P2. **Extend `_confirm_would_patch_duplicate` (cefi-late-renames script) with a casefold-aware
      `instrument_type` check + keep `symbol`/`underlying`/`available_at` excluded (Finding 11 BROAD definition)** —
      market-tick-data-service@5c0c7f3f (slot 27, 2026-08-10T19:33Z). BROAD comparison fix shipped. Slot 7 dry-run
      (below) confirmed the fix resolves the false-positive collision class (content-identical wire/canonical pairs now
      correctly classified as DUP-CONFIRMED) but 11,305 genuine collisions remain where wire and canonical objects have
      genuinely different content — this is NOT a comparison bug, it's real divergent data.

## Progress Log

- **2026-08-10 (slot 6, data_engineering, dispatched on the Range-2 apply todo)** — Executed the todo's gate sequence.
  (1) Culprit gate MET: `cefi-fwd-20260808-123230` confirmed terminated (deleted 2026-08-09T02:13:58Z per tracking doc
  line 226; forward backfill reached full coverage through 08-05, past the 07-24 window end). Fresh spot-check of
  LIGHTER-ZKSYNC `derivative_ticker` objects on dense-window dates shows the stable pre-existing population, no live
  writer into the historical window. (2) Fresh same-run soft-delete retention check on `market-data-tick-cefi-prd-…`:
  **604800s (7 days)** — delete-safety path (c) qualified. (3) Paused consolidator cron
  `uts-prod-manifest-consolidator-market-data-cefi-cron`, verified `PAUSED`. (4) Launched the venue-scoped
  `cefi-late-renames` dry-run (`canonical-migration-cefi-late-renames-20260810-161902`, `--venue LIGHTER-ZKSYNC`,
  2026-04-18..2026-07-24). First two SPOT launches were preempted in the early-boot blind window (46s / 2.5min, zero
  mutation); relaunched `ON_DEMAND=true`. **Dry-run VERDICT: still blocked** —
  `Outcome breakdown: {already_canonical: 11769, plan: 14829, would_rename: 3524, unresolved_wire: 19}` but the tool
  logs "Refusing to proceed to --apply while unhandled collisions exist" with 40+ genuine-collision ERROR lines
  (content-differs, e.g. `LIGHTER-ZKSYNC:PERPETUAL:APT-USDC@LIN` / `ARB-USDC@LIN` / `BTC-USDC@LIN` on 2026-04-18) — the
  SAME strict-compare misclassification Finding 11 documented for HYPERLIQUID/ASTER. The apply CORRECTLY refused (no
  mutation; the run also OOM'd rc=137 on e2-standard-8 after the collision verdict, consistent with Finding 6's
  bigger-machine note). (5) RESUMED cron + verified `ENABLED`. **Conclusion**: the "culprit-terminates → collisions
  clear" premise is falsified; the unblock is the BROAD-comparison fix (new P2 todo above), not re-attempting the apply
  as-is. Skipped this task (`reason_code=GATED`) pending that fix.
- **2026-08-08** — Filed during the `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` resume, slot 18.
  EXTENDED-STARKNET applied clean; LIGHTER-ZKSYNC blocked on this systemic collision after a safe single-day exclusion
  attempt proved insufficient; proceeding to BYBIT-SPOT/COINBASE-FUTURES independently.
- **2026-08-08 (slot 20)** — Root-cause todo closed. Read-only audit (script committed) sampled 11 dates (8 dense-window
  - 3 post-window), confirmed 100%-`derivative_ticker` collision population with identical wire/canonical row counts,
    and traced the wire-form writes to the active, bounded `cefi-fwd-20260808-123230` `--force` historical backfill VM
    (tracked separately, ETA ~2026-08-12T05:00Z). Determination: self-resolving race, not a code bug. Todo 2 left open,
    gated on that VM's completion.
- **2026-08-08 (slot 18, re-dispatch attempt)** — Re-picked up todo 2; VM `cefi-fwd-20260808-123230` confirmed still
  RUNNING via `gcloud compute instances list`. Fresh GCS spot-check (BINANCE-FUTURES, `derivative_ticker`,
  `raw_tick_data/by_date/day=<d>/pipeline_mode=batch_tardis/asset_group=cefi/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/`):
  2026-07-14 COMPLETE (584 objects, matches sibling doc's last logged frontier); 2026-07-15/16/17 all 0 objects (matches
  the sibling doc's established structural-lag pattern, not yet reached); 2026-07-18/07-20/07-24 all 0 objects
  (`CommandException: One or more URLs matched no objects` — confirmed genuinely empty, not a false-positive count).
  **Frontier has NOT yet reached the Range-2 window end (2026-07-24)** — the todo's own gate is still accurate; NOT
  ready to re-attempt. Parked via `POST /api/slots/18/skip-current-task` (`reason_code=GATED`, `park_now=true`) per
  `RULES.md`/`auto_park.py`'s "worker hitting an EXTERNAL gate" mechanism, rather than forcing the apply or busy-waiting
  ~4 days in-session. No code/data changed this pass.
- **2026-08-10 (slot 7, data_engineering, dispatched on Range-2 apply todo)** — Re-attempted with BROAD comparison fix
  (todo 3, shipped by slot 27 @ `5c0c7f3f`). Full sequence: (1) Confirmed culprit `cefi-fwd-` VMs all TERMINATED. (2)
  Fresh spot-check: LIGHTER-ZKSYNC `derivative_ticker` population stable (264-327 objects/day across sampled dates). (3)
  Paused consolidator cron `uts-prod-manifest-consolidator-market-data-cefi-cron` (asia-northeast1), verified PAUSED.
  (4) Launched venue-scoped dry-run (`canonical-migration-cefi-late-renames-20260810-202927`, `ON_DEMAND=true`,
  `--venue LIGHTER-ZKSYNC`, 2026-04-18..2026-07-24). First SPOT launch (`...-201928`) preempted at plan-build start (~3
  min, zero mutation). **Dry-run VERDICT: BROAD comparison works for false-positive class but 11,305 genuine collisions
  remain.** Discovery: 26,617 objects across 98 days. Plan-build: 121 groups, ~14 min. BROAD comparison correctly
  classified the content-identical class as DUP-CONFIRMED (wire/canonical pairs with identical row counts, differing
  only in column layout excluded by the fix). However:
  `Outcome breakdown: {already_canonical: 11769, plan: 14829, would_rename: 3524, unresolved_wire: 19, would_merge: 0, mislabel_left_raw: 0}`
  with `STOP-ON-SURPRISE — 11,305 UNHANDLED collision(s) detected` across dates 2026-06-18..2026-07-14 (~150-157/day,
  full symbol universe) and 2026-04-18. These are GENUINE content-differs — the wire-form and canonical-form objects
  have different underlying data (likely from the culprit VM's `--force` re-download producing different Tardis API
  responses than the original captures), not the same data in a different column layout. The apply CORRECTLY refused.
  RC=137 (OOM) on e2-standard-8 after collision verdict. (5) RESUMED cron + verified ENABLED. **Also noted: bucket
  soft-delete policy is NULL (not set) — delete-safety path (c) does NOT currently qualify.** Skipping this task
  (`reason_code=GATED`); needs operator policy decision on genuine-collision handling (leave-both / prefer-wire /
  prefer-canonical).
- **context-scout 2026-08-09**: populated context_scope (4 entries) -- no prior context-scout marker existed on this
  doc; added the gating `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md` (todo 2's explicit BLOCKED-on
  dependency) and the read-only audit script that produced the root-cause findings.
