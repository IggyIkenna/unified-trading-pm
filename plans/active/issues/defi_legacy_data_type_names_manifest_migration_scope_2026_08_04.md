---
doc_type: issue
title: >-
  `dex_pools`/`dex_swaps`/`rate_indices` legacy data_type manifest residue (~4.0M rows) — scoping only, NOT executed;
  needs its own dedicated content-verified migration pass
summary: >-
  Confirmed via `/codex/02-data/defi-canonical-naming-ssot.md:88` (operator-locked 2026-06-01) that `dex_pool_state`/
  `dex_pool_swaps` are canonical at every layer and the legacy 2-layer split (manifest `dex_pools`/`dex_swaps`) is
  RETIRED. Confirmed via direct code read that no live writer emits these bare forms (MTDS handler consts already write
  canonical names; MDPS treats them as read-only legacy aliases). Real row counts are large — 2026-07-22 live census
  (cited in
  `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md:105-107`):
  `dex_pools` 454,077 / `dex_swaps` 3,458,668 / `rate_indices` 49,096 rows (~4.0M total). This topic is nominally
  "owned" by `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`, but that plan is at its
  1000-line hard cap (verified 2026-08-04) with no concrete scoped todo for this exact rename/fold — it references
  `dex_pools` only in a catalog-freshness probe context, not a migration todo. Filed as a standalone, properly-scoped
  issue doc (cannot add to the capped master doc) rather than executed inline — a migration at this row count needs its
  own dedicated dry-run + content-verification pass, per this exact workspace's own R5 precedent
  (`/plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`: a superficially-safe-looking `dex_pools/`
  delete order was overturned by a content-verify that found 32 legacy-only high-TVL pools NOT present in the
  "canonical" set — "the paths looked duplicated; the content was not"). Rushing a rename across 4M rows without
  per-shard content verification risks exactly that failure mode at much larger scale.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    dex-pools,
    dex-swaps,
    rate-indices,
    canonicalisation,
    manifest,
    distinct-values,
    legacy-migration,
    data-correctness,
  ]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
source: >-
  Sub-agent research dispatched from interactive session 2026-08-04, investigating the DEFI distinct-values
  non-canonical data_types panel under /autonomous dispatch (see
  defi_cefi_venue_chain_axis_contamination_2026_07_28.md's Progress Log for full session context)
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
    market-tick-data-service/scripts/fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py,
    deployment-service/scripts/vm/launch-backfill-defi-legacy-datatype-fold-vm.sh,
  ]
---

# `dex_pools`/`dex_swaps`/`rate_indices` legacy data_type residue — scoping doc (2026-08-04)

## Why NOT executed this session

1. **Scale**: ~4.0M manifest rows spanning years — this is a genuine migration campaign, not a quick fix.
2. **The R5 precedent directly applies**: this exact workspace already had a near-miss on a superficially-identical
   "obviously safe" DeFi legacy-naming cleanup (`dex_pools/` GCS path fold, 2026-07-20/21) where a path/name-level
   "these look like duplicates" assumption was WRONG — content-verification found 32 legacy-only high-TVL pools
   (XMR/USDC $47M, BNB/USDC $18M, etc.) that a naive delete would have destroyed. A rename/fold of `dex_pools`→
   `dex_pool_state` (etc.) at the MANIFEST level carries the same risk class: is every `dex_pools`-labeled row's data
   actually IDENTICAL in shape/content to what a `dex_pool_state`-labeled row for the same cell would be, or did the
   legacy writer emit a different column set/grain that a blind rename would misrepresent? Not verified.
3. **Owning plan is capped**: `master_data_canonicalisation_migration_catalogue_2026_06_07.md` is at the 1000-line hard
   cap (`check_line_caps.sh`-enforced) — cannot append a new scoped todo there without first shrinking it (out of scope
   for this doc).
4. This session already made and caught one "assumed safe, wasn't" mistake on a much smaller delete candidate this same
   session (`defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b)) — proceeding to execute a 4M-row migration
   on the same day, on the same class of assumption, without a dedicated verification pass would repeat that exact
   failure mode at far larger scale.

## What's confirmed (safe to rely on)

- Canonical target: `dex_pool_state`/`dex_pool_swaps` (operator-locked 2026-06-01,
  `/codex/02-data/defi-canonical-naming-ssot.md:88`). No ambiguity on the TARGET naming.
- No live writer emits the bare legacy forms today (`dex_pools_handler.py`/`dex_swaps_handler.py` handler consts already
  write canonical names — this is a pure historical-residue migration, not a live-writer bug to fix first).
- `rate_indices` — NOT yet investigated this session; same "legacy vs current" question needs answering before assuming
  it's the same shape of fix as `dex_pools`/`dex_swaps` (do not assume; check the naming SSOT + writer code for
  `rate_indices`'s own canonical target before scoping the fix).

## Todos

- [x] ✅ [DIAG] P2. **CLOSED 2026-08-07 (na-eligibility-audit, stale-item citation-fix).** Confirm `rate_indices`'s
      canonical target name/relationship — already extracted, verbatim, as its own dispatched todo in the active
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md:159-166` (`assigned_vm: planning`, explicit `Source:` citation to
      this doc, "Done when: the source doc's open DIAG todo is checked off"). That todo also cites
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s 2026-08-01 finding (verified against live `_lending_grain.py`,
      `market-tick-data-service@13f14b78`) which already answers the canonical-target-name half:
      `rate_indices`/`utilization` → `lending_indices`. Do not re-open this checkbox; real remaining work (the narrower
      population-overlap residual) lives at the cited batch9 todo.
- [x] ✅ [DIAG] P2. **RESOLVED 2026-08-04 (interactive session) — the R5 concern is CONFIRMED REAL for `dex_swaps`,
      REFUTED for `dex_pools`. Two genuinely different cases, not one.** Bounded, per-(venue,chain) date-set +
      instrument_id-set comparison (live `pyarrow.dataset` reads against `_index/availability_index.parquet`,
      columns-projected, filtered to the 4 data_types in question — not a full-corpus walk): - **`dex_pools` vs
      `dex_pool_state` — CLEAN 1:1, safe.** Only 2 (venue,chain) pairs carry `dex_pools` data (`ORCA/SOLANA`,
      `RAYDIUM/SOLANA`). At BOTH the date grain AND the finest instrument_id grain: **zero legacy-only entries** —
      canonical dates (1327/1326) and instrument_ids (28328/554) strictly SUPERSET the legacy population (32/31 dates,
      14093/109 instrument_ids) in both cases. This is a true 1:1 rename candidate. - **`dex_swaps` vs `dex_pool_swaps`
      — NOT clean, real content gap confirmed, same failure class as R5.** Date-grain comparison across all 24
      `dex_swaps` (venue,chain) pairs: **22 of 24 show a real legacy-only date gap** (only `UNISWAP_V2/ETHEREUM` and a
      near-zero 1-date case on `UNISWAP_V3/ETHEREUM` are clean). Gaps range from small (`PANCAKESWAP_V3/BSC`: 15
      legacy-only dates) to severe (`SUSHISWAP_V3/ARBITRUM`: **1,049 of 1,243 legacy dates (84%) have NO canonical twin
      at all**; `BALANCER`/`SUSHISWAP`/`CURVE` pairs show 400-620 legacy-only dates each). Two distinct gap shapes
      observed, both real: (a) OLD historical gaps (2023 dates, e.g. `BALANCER/ARBITRUM` starting 2023-03-08) — genuine
      historical legacy-only captures never re-backfilled under the canonical name; (b) a RECENT, consistent
      ~130-140-day gap clustered around 2025-07-27→2025-08-06+ across MANY venues simultaneously (`AERODROME_V3/BASE`,
      `CAMELOT_V3/ARBITRUM`, `PANCAKESWAP_V3/{BASE,ETHEREUM}`, `SUSHISWAP_V3/{AVALANCHE,ETHEREUM}`,
      `UNISWAP_V3/{ARBITRUM,BASE,OPTIMISM}` all show ~130-140 legacy-only dates in this exact window) — this shape
      suggests either a canonical writer that stopped/lagged recently for many venues at once, or a legacy writer that
      (surprisingly) kept running past its supposed retirement — NOT yet root-caused, flagging as a genuinely new
      sub-finding for whoever picks up the DATA migration below. Instrument_id-grain comparison NOT run for `dex_swaps`
      (3.46M legacy rows — the date-grain result alone is already decisive; an instrument_id pass would only refine
      severity, not the safe/unsafe verdict). **Verdict: `dex_pools` is DIAG-cleared for a simple rename; `dex_swaps` is
      NOT — it needs a real content migration (copy the legacy-only rows forward under the canonical name, verify, THEN
      retire), never a blind rename/delete.** This directly validates the caution this doc was filed under and the R5
      precedent it cited — the fear was not hypothetical.
- [x] ✅ [DATA] P2. **DONE 2026-08-05.** `dex_pools` → `dex_pool_state`: turned out to be pure manifest retirement, not
      a GCS rename — direct content comparison found the canonical writer already captured byte-identical data under
      `instrument_type=solana_amm_pool` (not `pool`, the exact wrong-vocabulary gotcha CLAUDE.md warns about).
      `retire_dex_pools_legacy_captured_rows_2026_08_05.py` bulk-verified every (instrument_id, date) pair has a
      canonical twin before touching anything; ran against prod — 453,985/454,014 rows retired (capture_status
      captured→attempted_failed, GCS objects untouched, reversible), 29 rows excluded (no twin found, all dated
      2025-01-17 — a real, narrow residual left `captured`, needs its own small follow-up investigation, NOT retired
      blind). Round-trip verified.
- [ ] [DATA] P2. **`dex_swaps` → `dex_pool_swaps`**: DIAG above proves this is NOT a rename — it is a real content
      migration. Recipe: for each of the 22 gapped (venue,chain) pairs, copy the legacy-only-dated `dex_swaps` rows
      forward to canonical `dex_pool_swaps` form (mirroring the R5 fold precedent — copy, verify, THEN retire the legacy
      label), never delete first. **Before designing the migration, first root-cause the recent ~2025-07-27→2025-08-06+
      multi-venue gap cluster** (is a live writer currently still emitting `dex_swaps` for some venues today, or did the
      canonical writer silently stop for a window?) — migrating a STILL-ACTIVE legacy writer's output without first
      stopping/redirecting it would just regenerate the gap. Full five-part delete-safety proof required before any
      GCS-level change; this is now a genuinely large, multi-week-scale migration given severity (up to 84% legacy-only
      on some pairs), not a same-session task.
- [x] ✅ [REVIEW] P3. Fixed independently of the DATA migration below (no data risk, as this todo itself notes) —
      `unified-api-contracts@ab4693de` ("docs: correct stale _schema_spec_defi.py docstring — dex_pools/dex_swaps are
      RETIRED, not current writers"). Live-verified: the docstring now reads "RETIRED legacy manifest data_type names
      (corrected 2026-08-04: this docstring previously and incorrectly described these bare forms as 'current'
      writers...)" and cites this exact issue doc. — interactive session, 2026-08-04.

## Progress Log

- **2026-08-16 (plan_reconciler, defi-tranche Phase -1) — cross-link, not independently re-verified**: hunter batch B
  of the 2026-08-16 defi-tranche `/plan-reconcile` run found `dex_swaps` migration-completion claims conflicting by
  ~3.26M rows across 4 docs that don't cross-reference each other, this one included:
  `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`,
  `/plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (the same manifest-
  consolidator/VM-relaunch machinery this doc's own dispatched root-cause todo targets). Added per
  `plan_reconciler_findings_defi_2026_08_16.md`'s Contradiction #2 recommendation so a worker on any one of these 4
  docs sees the others; the row-count conflict itself is NOT resolved here (needs a fresh live manifest read).
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling — scoped)**: operator asked to dispatch
  the `dex_swaps` migration. Given this doc's own repeated `too_large_or_risky` corroboration (2026-08-04 x2,
  2026-08-07, 2026-08-09 — the migration design itself has no predetermined outcome until the recent multi-venue
  gap cluster is root-caused), scoped the dispatch DOWN to only the bounded root-cause step:
  `/plans/archive/2026_08/defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md` (+ finalize, both archived
  2026-08-17 — root-caused and confirmed no live writer active). The full content migration
  is NOT dispatched — it stays gated on that finding plus a full five-part delete-safety proof, per this doc's own
  standing caution. This doc stays `assigned_vm: NA` until the migration itself is scoped.
- **interactive session 2026-08-05**: executed the `dex_pools` half only (see the flipped todo above for full detail).
  `dex_swaps`/`rate_indices` remain genuinely untouched -- both need their own dedicated pass (the `dex_swaps` gap
  root-cause + real content migration is the dominant remaining scope by far, ~3.46M of the ~4.0M total rows).
- **interactive session 2026-08-04 (autonomous, `/autonomous`)**: filed as a scoping-only doc after confirming (a) the
  row counts are large enough to warrant dedicated care, (b) the owning master plan is at its hard line cap, and (c)
  this exact session already caught one "looked safe, wasn't" mistake on a smaller, related delete candidate this same
  day — proceeding to a 4M-row migration on an unverified content-equivalence assumption would repeat that failure mode.
  Not executed.
- **interactive session 2026-08-04 (separate session, `/autonomous`)**: independently arrived at this same doc while
  investigating an operator report of `dex_pools`/`dex_swaps` showing as non-canonical in a Data Status panel — cross-
  checked live writers (two running `mtds-dex-swaps-backfill-*` VMs' own per-VM manifest shards read directly from GCS:
  4527 + 400 rows, 100% `data_type=dex_pool_swaps`, zero legacy `dex_swaps` rows), confirming this doc's "no live writer
  emits the bare legacy forms" finding independently. Did not duplicate the DIAG/DATA todos above (correctly scoped,
  already gated on real content-verification per the R5 precedent this doc cites) — flipped only the REVIEW P3 todo,
  which was already shipped (`unified-api-contracts@ab4693de`) but left unchecked.
- **interactive session 2026-08-04 (continuation, operator directive: "batch/live symmetry — bad names shouldn't
  exist")**: ran the DIAG P2 content-comparison this doc had left open, per-(venue,chain) date-set + instrument_id-set
  bounded live reads (not a corpus walk). **Result is a genuine split verdict, not the single-outcome the todo
  anticipated**: `dex_pools` cleared clean (zero legacy-only content at any grain, safe rename); `dex_swaps` confirmed
  UNSAFE for a blind rename — 22 of 24 (venue,chain) pairs have real legacy-only date coverage, up to 84% on
  `SUSHISWAP_V3/ARBITRUM`. Rewrote the DIAG/DATA todos above to reflect the split (P2a rename-safe, P2b real-migration-
  required) and flagged an unexplained recent multi-venue gap cluster (~2025-07-27→2025-08-06+) for the next DATA
  picker-upper to root-cause before designing the P2b migration. This is exactly the R5 failure mode this doc was filed
  to guard against — confirmed real this time, not just a theoretical risk.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — the 3 open items are a
  diagnostic pair (rate_indices canonical-target check, sample-based content-equivalence comparison) feeding a
  DATA-migration item gated on their outcome and likely needing delete-safety/[OPERATOR] handling; the
  content-equivalence judgment call is the exact risk class this doc's own cited R5 precedent shows can be wrong, so it
  stays genuine-caution NA rather than a clean mechanical RECLASSIFY. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope's `defi_dex_pools_delete_order_stale_2026_07_20.md` reference
  had moved to `/plans/archive/issues/` since it was written (RESOLVED, archived) — corrected the path in place, now 5
  entries.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA, stale item closed — re-read end to end (2 open items at
  entry, grep-verified). The `dex_swaps` → `dex_pool_swaps` DATA migration remains genuine, judgment-heavy scope
  (root-causing an unexplained gap cluster + a full five-part delete-safety proof before any change) — independently
  corroborated as `too_large_or_risky` by `defi_satellite_ao_dispatch_batch10_2026_08_06.md:173-176`. The `rate_indices`
  DIAG item is stale in framing: already extracted, verbatim, as an active dispatched todo in
  `defi_satellite_ao_dispatch_batch9_2026_08_06.md:159-166` — closed by citation, not reclassified (flipping this doc's
  `assigned_vm` would dispatch a duplicate). Doc stays `assigned_vm: NA`.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (1 open
  `[DATA] P2` item at entry: `dex_swaps` → `dex_pool_swaps`). Checked against every accumulated round11 precedent (IAM
  self-service, D16 all-repos, S5.1 tiering, plan-destination-defaults-AO-dispatched, escalation-N=3-days,
  reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks now existing) — none apply: the
  remaining scope is still gated on root-causing a live, unexplained multi-venue gap cluster (is a legacy writer still
  active today?) before any migration design is even possible, plus a full five-part delete-safety proof once designed —
  genuinely judgment-heavy, not a bare mechanical copy. Not eligible for satellite-extraction as a bounded todo (the
  root-cause step itself has no predetermined outcome). Doc stays `assigned_vm: NA` (KEEP-NA valid, round11).
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — dropped `dex_pools_handler.py` (that half is DONE,
  retired 2026-08-05, see todo above); added `fold_legacy_dex_pools_swaps_rate_indices_2026_08_04.py` (the built tool
  covering BOTH remaining open items — the `dex_swaps` real-content migration and, per its own docstring, an ALREADY-
  ANSWERED `rate_indices` canonical-target finding — `lending_indices` — that the open `[DIAG] P2` checkbox above does
  not yet reflect; flagging as a stale-candidate for `/plan-reconcile`, not resolving the checkbox here) and its VM
  launcher `launch-backfill-defi-legacy-datatype-fold-vm.sh`.
- **2026-08-12 (slot 14, data_engineering, task `defi_pool_rate_indices_dex_pool_fees_retirement` todo 9) — FINDING: the
  2026-08-10/11 defi manifest rebuild RE-REGISTERED the 2026-08-05-retired `dex_pools` legacy rows back to `captured` —
  the exact pre-retirement population is back (454,014 rows).** Post-rollup Distinct-Values census on the fresh
  `2026-08-12` `coverage.json` shows `dex_pools` as a non-canonical data_type AGAIN: `ORCA` 450,976 + `RAYDIUM` 3,038 =
  **454,014 captured, 0 attempted_failed** (vs the 2026-08-05 terminal state of 29 captured / 453,985 attempted_failed).
  The `canonical-migration-defi-rebuild-20260810-204358` disk scan re-added every legacy `dex_pools` physical object as
  `captured` — the SAME recurrence mechanism as the POOL uppercase recurrence
  (`defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`): **a capture_status-flip retirement whose underlying GCS
  objects still exist at a legacy path is undone by the next `rebuild_defi_manifest.py` scan.** Implication for the
  still-open `dex_swaps → dex_pool_swaps` migration below: a manifest-only flip will NOT be durable while the legacy
  objects exist and the rebuild re-scans them — the migration's five-part delete-safety proof (or a rebuild-scan
  skip-legacy-path fix) is REQUIRED for a durable outcome, not optional. Immediate reversible re-retirement of the
  re-registered `dex_pools` rows is the short-term fix; the durable fix belongs with the POOL-recurrence root-cause
  tracking. Not executing either here (bounded task scope: pool/rate_indices/dex_pool_fees retirement + rollup + panel
  check).
- **na-eligibility-audit 2026-08-16** [body-hash:a72416208cabee9e]: KEEP-NA, valid — The sole open todo (dex_swaps -> dex_pool_swaps real content migration, NOT a safe rename per a live-run DIAG that found up to 84% legacy-only content on some venue/chain pairs) has been repeatedly corroborated too_large_or_risky across four prior touchpoints (2026-08-04 x2, na-eligibility-audit 2026-08-07, round11-sweep 2026-08-09) as genuinely judgment-heavy: it requires root-causing an unexplained recent multi-venue gap cluster plus a full five-part delete-safety proof before any GCS-level change.
- **na-eligibility-audit 2026-08-17**: KEEP-NA, valid — sole open todo now DEPENDENCY_BLOCKED on the separately-dispatched defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md (status: active) resolving first, then the five-part delete-safety proof. Checked today's plan_reconciler_findings_defi_2026_08_17.md "2025 vs 2026 date typo propagation" flag against this doc — refuted (both docs agree on 2025), no bearing on this verdict. Doc stays assigned_vm: NA.
- **2026-08-17 (slot 9, data_engineering, `defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md`) — ROOT-CAUSED:
  the ~2025-07-27..2025-08-06+ recent multi-venue gap cluster is CLOSED, not a live-writer bug.** Bounded live
  manifest reads (`pyarrow.dataset`, columns-projected, filtered to the 9 flagged `(venue,chain)` pairs
  (`AERODROME_V3/BASE`, `CAMELOT_V3/ARBITRUM`, `PANCAKESWAP_V3/{BASE,ETHEREUM}`, `SUSHISWAP_V3/{AVALANCHE,
  ETHEREUM}`, `UNISWAP_V3/{ARBITRUM,BASE,OPTIMISM}`) + `{dex_swaps, dex_pool_swaps}`, date range
  2025-06-01..2025-12-31 — not a corpus walk) against
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`:
  - **As of 2026-08-17, ZERO legacy-only dates remain for all 9 pairs** — legacy `dex_swaps` and canonical
    `dex_pool_swaps` both show the identical 214/214 dates for 2025-06-01..2025-12-31 (previously the
    2026-08-04 DIAG above found this exact window as the "RECENT ~130-140-day gap" bucket).
  - **Root cause: the gap was a transient snapshot artifact of the `mtds-dex-swaps-backfill` VM's in-progress
    chronological historical re-crawl, caught mid-flight by the original 2026-08-04 DIAG — not a stopped/lagging
    canonical writer and not a still-active legacy writer.** The canonical `dex_pool_swaps` rows for the exact
    2025-07-27..2025-08-06 window carry `attempted_at` timestamps of `2026-08-04T09:08:53Z` through
    `2026-08-10T22:01:50Z` (34,074 rows) — i.e. this specific window was captured in the days immediately
    following (and during) the original DIAG's read, as the backfill VM's chronological walk passed through it.
    Corroborated by `/plans/archive/2026_08/issues/mtds_dex_swaps_backfill_wasteful_2023_replay_2026_08_09.md`:
    the predecessor `-2` VM (before consolidation into the current `mtds-dex-swaps-backfill`) was assigned range
    `2025-05-12..2025-12-14` and "ran the stale pre-fix binary until ~2026-08-07T15:22Z" — squarely explaining
    why the window closed within days of the DIAG.
  - **(a) refuted**: no `mtds-dex-swaps-*` VM is currently running (`gcloud compute instances list` empty,
    checked 2026-08-17); current `dex_swaps_handler.py` source has written only the canonical `dex_pool_swaps`
    label since the 2026-06-02 rename (`market-tick-data-service@0a3a7071`, "collapse DeFi dex pool/swap
    data_type to canonical on-disk name") — no code path can emit the legacy label today.
  - **(b) refined, not confirmed as stated**: the canonical writer did not "stop" — a still-in-progress backfill
    campaign simply hadn't reached this date range yet at DIAG time, and has since caught up.
  - **Scope note — does NOT resolve the broader migration**: this closes ONLY the "recent
    ~2025-07-27..2025-08-06+" cluster the rootcause plan was scoped to. It does NOT resolve the broader
    `dex_swaps` → `dex_pool_swaps` content-migration scope (the OLD/scattered 2023-era legacy-only dates on 22
    of 24 `(venue,chain)` pairs, up to 84% legacy-only on `SUSHISWAP_V3/ARBITRUM`, per the original 2026-08-04
    DIAG above) — that remains open, still needs its own five-part delete-safety proof before any GCS-level
    change, per this doc's standing caution. The still-open `[DATA] P2` todo above is unaffected by this finding
    except that its "root-cause the gap cluster first" precondition is now satisfied for the recent-window half.
- **context-scout 2026-08-17**: re-scouted; context_scope unchanged (6 entries), still accurate — all 6 still resolve
  and cover the sole remaining open item (the `dex_swaps` → `dex_pool_swaps` content migration, still gated on a
  five-part delete-safety proof).
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — sole open item (`dex_swaps` → `dex_pool_swaps` real content migration) remains DEPENDENCY_BLOCKED / judgment-heavy per the 2026-08-17 verdict: the recent-window gap cluster is root-caused and closed, but the broader OLD/scattered 2023-era legacy-only content (up to 84% on some venue/chain pairs) still needs its own five-part delete-safety proof before any GCS-level change. Doc stays `assigned_vm: NA`.
