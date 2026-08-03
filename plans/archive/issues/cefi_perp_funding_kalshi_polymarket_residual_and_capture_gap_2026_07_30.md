---
doc_type: issue
title: >-
  KALSHI-PERP/POLYMARKET-PERP perp_funding: uncorrected historical manifest rows, a live daily POLYMARKET_PERP capture
  failure with an unhelpful error_reason, and an unverified 2-day GCS/manifest discrepancy
summary: >-
  Follow-up from `cefi_sports_prediction_first_census_small_drift_2026_07_30.md` — that doc fixed the WRITER bugs (venue
  underscore, wrong-axis chain) so new ticks are canonical going forward, but explicitly did not migrate the
  pre-existing bad rows. Digging into exactly which rows those are surfaced four things, only the first of which was
  originally scoped: (1) the 8 known non-canonical manifest rows (4 KALSHI_PERP `captured` + 4 POLYMARKET_PERP
  `attempted_failed`, all dated 2026-07-26..07-29) are real, LIVE, DAILY writes — not old dead residue — so this has
  been silently wrong every single day since the venues launched, not a one-time historical blip; (2) every
  POLYMARKET_PERP row in this window is `attempted_failed` — Polymarket perp-funding has not successfully captured ANY
  data in the measured window, and the recorded `error_reason` is literally the string `"polymarket_perp"` (the
  protocol/source name, not a real exception message) — looks like a second bug in how the failure itself gets recorded,
  on top of the underlying collection failure; (3) the manifest `captured` row is a BUNDLE covering 13 separate
  per-ticker parquet objects (KXBTCPERP, KXETHPERP, ... one per Kalshi crypto-perp market), not a 1:1 row-to-object
  mapping — this wasn't accounted for when the small-drift doc scoped "8 rows" as if migrating them meant moving 8
  objects; (4) a bounded, exact-prefix GCS listing found ZERO objects at the expected `venue=KALSHI_PERP/` path for
  2026-07-26 and 2026-07-27, despite the manifest claiming `captured` for both dates — this is UNVERIFIED, not
  confirmed, because the delimiter-descent variant of the same listing method broke (wrong return-type assumption)
  partway through the same investigation, so a false negative from operator error can't yet be ruled out. No GCS writes,
  deletes, or manifest corrections were made — this doc exists specifically because the investigation stopped short of
  touching production data on shaky footing, per the workspace's own content-verify-not-existence delete-safety lesson.
  **UPDATE (same day, completing this doc's own todos):** the listing bug is fixed (Finding C CONFIRMED real, not a
  tooling artifact); Finding A root-caused to a `record_failed` classification-token bug (fixed + shipped); the 26
  confirmed-real KALSHI_PERP objects were migrated to canonical venue paths (applied + verified). A SEPARATE, SELF-
  CAUGHT P0 regression surfaced mid-fix: the sibling small-drift doc's "chain wrong-axis" finding was itself a
  misdiagnosis, and its same-day fix silently broke every perp_funding manifest write for these 3 venues for ~2h15m —
  caught and reverted same session, zero real writes lost. The 8-row + 76-row manifest metadata corrections remain
  BLOCKED, not on logic, but on `DefiManifestRecorder`'s full-index read-merge-write timing out repeatedly from a local
  session against the 9.5M-row consolidated manifest — this is the heavy-I/O-belongs-on-a-VM class of problem, not a
  data-correctness one.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    canonicalisation,
    manifest,
    perp_funding,
    kalshi,
    polymarket,
    capture-failure,
    honest-coverage,
    census,
  ]
related:
  [
    cefi_sports_prediction_first_census_small_drift_2026_07_30,
    cefi_live_spot_connectors_noncanonical_instrument_id_2026_07_30,
    perp_funding_data_semantics_and_cadence_2026_06_16,
    data_pipeline_reconciliation_skill_2026_07_20,
    gcs-and-manifest-delete-safety-protocol,
  ]
created: 2026-07-30
last_updated: 2026-07-31
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  operator request 2026-07-30 — asked whether the small-drift census fixes actually removed the non-canonical values
  from the manifest/GCS (they had not); investigating exactly which rows needed migrating surfaced these 4 findings
resolved_by: >-
  market-tick-data-service@dcd1bc8d (Finding A), @5d856acb + @17204fca (P1 manifest re-stamp + oneoff cleanup),
  @fb32fb65 (P0 regression revert); P3 redirected, not separately shipped — see that todo
depends_on: []
context_scope:
  [
    /plans/active/issues/cefi_sports_prediction_first_census_small_drift_2026_07_30.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py,
    deployment-api/deployment_api/routes/data_status/_axis_census.py,
    /plans/archive/issues/cefi_sports_prediction_first_census_small_drift_2026_07_30.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

> **✅ ARCHIVED 2026-08-02** — all 5 todos `[x]`, `locked_by:` empty. P0-P2 shipped directly
> (`market-tick-data-service@dcd1bc8d`/`@5d856acb`/`@17204fca`/`@fb32fb65`); the P3 "~76 prediction rows" todo was found
> stale by ~4 orders of magnitude on re-check (real corpus-wide count ~652k+) and redirected to the already-in-progress,
> correctly-scoped, operator-gated effort at
> `/plans/active/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md` (todo 2, `[OPERATOR]`) and
> `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` (tasks `-001`/`-006`) rather than executed here.
> Moved to `plans/archive/issues/`.

# CeFi perp_funding (KALSHI-PERP/POLYMARKET-PERP): residual manifest rows + a live capture failure + an unverified gap

## 1. Measured evidence (bounded manifest read, `market-data-tick-cefi-prd-central-element-323112`)

Targeted read (columns projected:
`date, venue, chain, instrument_type, data_type, instrument_id, pipeline_mode, source, capture_status, error_reason, written_at`)
filtered to `venue in (KALSHI_PERP, POLYMARKET_PERP)` — 8 rows total, all `asset_group=cefi`, `data_type=perp_funding`:

| date       | venue           | capture_status   | error_reason      | written_at (UTC)    |
| ---------- | --------------- | ---------------- | ----------------- | ------------------- |
| 2026-07-26 | KALSHI_PERP     | captured         | —                 | 2026-07-27T01:15:53 |
| 2026-07-27 | KALSHI_PERP     | captured         | —                 | 2026-07-28T01:16:06 |
| 2026-07-28 | KALSHI_PERP     | captured         | —                 | 2026-07-29T01:15:57 |
| 2026-07-29 | KALSHI_PERP     | captured         | —                 | 2026-07-30T01:16:37 |
| 2026-07-26 | POLYMARKET_PERP | attempted_failed | `polymarket_perp` | 2026-07-27T01:15:54 |
| 2026-07-27 | POLYMARKET_PERP | attempted_failed | `polymarket_perp` | 2026-07-28T01:16:06 |
| 2026-07-28 | POLYMARKET_PERP | attempted_failed | `polymarket_perp` | 2026-07-29T01:15:58 |
| 2026-07-29 | POLYMARKET_PERP | attempted_failed | `polymarket_perp` | 2026-07-30T01:16:38 |

`venue == chain` for every row (the wrong-axis bug `cefi_sports_prediction_first_census_small_drift_2026_07_30.md`
already fixed at the writer level — these 8 rows predate that fix).

**This spans the venue's entire observed lifetime in this window, with a write EVERY DAY through the morning this doc
was filed.** The writer fix shipped today (`market-tick-data-service@4d147d9a`) should make tomorrow's (2026-07-31) run
the first canonical one — **not yet verified**, since it hasn't run yet as of filing.

## 2. Finding A — POLYMARKET_PERP has captured zero real data in this window, and the failure's own error message is uninformative

Every POLYMARKET_PERP row in the measured window is `attempted_failed`. This is not a canonicalisation defect — it's a
genuine, ongoing data-collection failure: Kalshi's own perp-funding side is capturing fine (4/4 `captured`),
Polymarket's is failing 4/4. Compounding it: `error_reason` for all 4 rows is the literal string `"polymarket_perp"` —
that's the protocol/source identifier, not a real exception message or failure class (contrast the kalshi bulk-seed
script's own convention, `error="ClassifierConfidenceLow"` — a real classified reason). Something in the POLYMARKET_PERP
failure path is passing the protocol name where a caught exception's message should go, which means whoever picks this
up will have to re-derive the actual root cause from scratch (logs, a live repro) rather than reading it off the
manifest.

## 3. Finding B — the manifest row is a BUNDLE, not a 1:1 GCS object

A bounded, exact-prefix listing (not a corpus walk — scoped to the known `(day, pipeline_mode, venue)` triple from the
manifest rows above) found **13 separate per-ticker parquet objects** under one `captured` manifest row for 2026-07-28
and again for 2026-07-29:

```
.../venue=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/{KXBCHPERP,KXBTCPERP,KXDOGEPERP,KXETHPERP,
KXHYPEPERP,KXKSHIBPERP,KXLINKPERP,KXLTCPERP,KXNEARPERP,KXSOLPERP,KXSUIPERP,KXXRPPERP,KXZECPERP}.parquet
```

Any migration of the 4 KALSHI_PERP `captured` rows to the canonical `venue=KALSHI-PERP/` path therefore means moving up
to 13 objects per day (≤52 objects total for the 4 known days), not 4 — the small-drift doc's "8 rows" framing
undercounted the true object count by roughly an order of magnitude. Still small/low-risk in absolute terms, but the
migration script needs to enumerate per-day, not assume one object per manifest row.

## 4. Finding C — UNVERIFIED: 2026-07-26 and 2026-07-27 show zero objects at the expected path despite `captured`

The same bounded-prefix method that found the 26 objects for 07-28/07-29 (§3) returned an **empty list** for
`venue=KALSHI_PERP/` on 2026-07-26 and 2026-07-27, even though the manifest marks both dates `captured`. This would
normally be exactly the `masked_empty_row`/honest-coverage-violation class the reconciliation taxonomy already has a
name for — a `captured` status with no real backing object.

**This is explicitly NOT confirmed.** Immediately after finding it, a follow-up attempt to cross-check via a day-level
delimiter descent (to see whether the objects exist under some other pipeline_mode/path shape for those 2 earlier dates)
failed with `AttributeError: 'generator' object has no attribute 'prefixes'` — the wrapped storage client's `list_blobs`
does not return the same iterator type this investigation assumed, so the cross-check itself was invalid, and by
extension so is confidence in the original "empty" result for those 2 dates (the SAME listing call pattern was used for
both the 07-28/07-29 success and the 07-26/07-27 empty result, so if the pattern has a subtler failure mode than the one
caught, both could be affected). **Do not treat "0 objects for 07-26/07-27" as established fact — re-verify with a
listing method proven correct against a KNOWN-populated day before concluding anything, let alone acting on it (no
deletes, no "fixing" a phantom row, until this is settled).**

## 5. Why nothing was migrated or corrected in this pass

Per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s core lesson (independently re-learned by this same
plan's dex_pools investigation, 2026-07-20 — a wrong "twin VERIFIED ABSENT" claim from probing the wrong vocabulary
almost authorized destroying 32 legacy-only pools): **an absence result is only evidence once the probing tool itself is
proven correct.** §4's broken delimiter-descent check means this investigation cannot currently tell the difference
between "the objects really are missing" and "my listing call has a bug" for the 07-26/07-27 dates. Acting on that
(migrating what might not exist, or worse, deleting/overwriting anything) would repeat the exact failure mode this
workspace has already been burned by once.

## Todos

- [x] [DATA] P1. **Fix the storage-client listing helper** — root-caused: the CLIENT-level `list_blobs(bucket, ...)`
      convenience wrapper (`unified_trading_library/cloud_interface/providers/gcp.py:283`) iterates the raw
      `HTTPIterator` internally and only ever yields `BlobMetadata` — it discards `.prefixes` entirely, which is why
      asking it for `.prefixes` crashed. The BUCKET-level API
      (`client.bucket(name).list_blobs(prefix=...,     delimiter='/')`, `gcp.py:135`) returns the native iterator that
      DOES preserve `.prefixes`. Re-verified Finding C with the correct method against a known-populated day first
      (07-28/07-29, confirmed 13 objects each) before trusting the negative result — **Finding C is CONFIRMED real**:
      2026-07-26 and 2026-07-27 have zero `pipeline_mode=batch_kalshi_perp/` (or `batch_polymarket_perp/`) directories
      at all under `asset_group=cefi` — only
      `batch_aster`/`batch_deribit`/`batch_extended`/`batch_hyperliquid`/`batch_tardis` exist for those 2 dates.
- [x] [DATA] P1. **Root-cause the POLYMARKET_PERP capture failure** (Finding A) — NOT a live bug: Polymarket's
      perp-funding endpoint (`perps-api.polymarket.com`) has a known, DELIBERATE, documented DNS-outage scaffold since
      2026-06-21 (`_collect_polymarket_perp`'s own docstring) — it correctly raises to route to `attempted_failed`. The
      REAL bug was narrower: `DefiManifestRecorder.record_failed` derives the manifest `error_reason` from
      `str(error).split(":", 1)[0]` (the first colon-delimited segment), and the raised message started
      `"polymarket_perp: ..."` — so the classification token extracted was the venue name, not a real reason. Fixed by
      reordering the message to `"SOURCE_UNREACHABLE: polymarket_perp perps-api.polymarket.com     unreachable..."` + a
      regression test asserting the token. Shipped `market-tick-data-service@dcd1bc8d`.
- [x] [DATA] P2. **Migrate the confirmed-real KALSHI_PERP objects** — 26 objects (13 tickers × 2 days, 07-28/07-29; the
      manifest row is a BUNDLE covering 13 per-ticker files, not 1:1 — undercounted in the original filing). Copy →
      crc32c content-verify → delete-old, per the delete-safety protocol's proof. **APPLIED and verified**: 26/26
      copied + content-verified, 26/26 legacy objects deleted, final listing confirms `venue=KALSHI_PERP/` = 0 objects
      remaining and `venue=KALSHI-PERP/` = 13 objects on each of 07-28/07-29.
- [x] [DATA] P0. **SELF-CAUGHT REGRESSION, urgently reverted** — while preparing this todo's manifest re-stamp, found
      that `cefi_sports_prediction_first_census_small_drift_2026_07_30.md`'s "chain wrong-axis" finding (and its
      same-day fix) was a MISDIAGNOSIS: `DefiManifestRecorder` enforces a hard A4-full invariant (every DeFi-family
      shard, perp_funding included, requires a non-blank `chain` — the last caller that ever keyed a blank chain was
      deliberately removed 2026-07-25 to close this off). Setting `chain=""` (shipped
      `market-tick-data-service@     4d147d9a`, 2026-07-30T14:12 UTC) made every `record_captured`/`record_failed` call
      for kalshi_perp/ polymarket_perp/hyperliquid perp_funding silently raise `BlankChainError`, caught by shard-level
      isolation, and drop the row with only a WARNING — no manifest write at all. **Reverted same session**
      (`market-tick-data-service@fb32fb65`, QG-green) — `chain=<VENUE>` restored as the established, load-bearing
      workaround for a venue with no underlying blockchain. **Blast radius measured as ZERO real production rows lost**:
      no `written_at` timestamp exists for any of the 3 venues' perp_funding rows in the 14:00-16:30 UTC window (the
      daily batch cron runs once ~01:15 UTC and did not fire again inside the regression window).
      `cefi_sports_prediction_first_census_small_drift_2026_07_30.md` corrected to retract the finding.
- [x] [DATA] P1. ✅ **Re-stamp the 8 KALSHI_PERP/POLYMARKET_PERP manifest rows** — market-tick-data-service@5d856acb.
      The prior interactive session's timeouts were confirmed heavy-I/O-on-local-machine, not a logic gap: run from an
      AO-fleet slot VM (exempt per `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-I/O rule), the same
      9.5M-row read-merge-write completed in ~72s (download 1.0s, pre-write gate 27s, CAS write 21s, post-write verify
      11s) — confirming the root cause was local-machine network path, not the operation itself. Re-derived the script
      from this todo's own fully-enumerated spec (the original ephemeral scratch-path script was gone, as expected) as
      `market-tick-data-service/scripts/restamp_cefi_perp_funding_kalshi_polymarket_venue_2026_07_31.py`, with a
      read-only dry-run mode + a per-row precondition check (aborts on any mismatch vs. the exact values this todo
      documented, never guesses) + a collision check against the candidate-venue subset before any write. Applied
      2026-07-31T05:39 UTC, generation `1785474578081701` → `1785476391377825`, row count unchanged at 9,629,206 (pure
      in-place field edits, no add/drop), pre-apply snapshot at
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/backups/availability_index.pre_perp_funding_kalshi_polymarket_restamp_20260731T053926Z.parquet`.
      All 8 rows post-write-verified: 2 KALSHI_PERP `captured` rows (2026-07-26/27, confirmed-phantom) →
      `attempted_failed`/`PHANTOM_CAPTURED_ROW`, venue left as-is (no real object to anchor a rename to); 2 KALSHI_PERP
      `captured` rows (2026-07-28/29, confirmed-real, GCS-side already migrated) → `venue=KALSHI-PERP`; 4
      POLYMARKET_PERP `attempted_failed` rows (2026-07-26..29) → `venue=POLYMARKET-PERP` +
      `error_reason=SOURCE_UNREACHABLE` (was the literal string `"polymarket_perp"`) — this exact corrected shape was
      cross-checked against the real 2026-07-30 canonical row the writer fix had already produced by the time this ran
      (`venue=POLYMARKET-PERP chain=POLYMARKET_PERP error_reason=SOURCE_UNREACHABLE`), confirming both the venue-naming
      and error_reason-token conventions independently before applying. `chain` intentionally left untouched on every
      row — the live reference row showed `chain` deliberately stays the underscore form (`_chain_map` in
      `perp_funding_handler.py`) even for the now-canonical hyphenated `venue`, so venue/chain equality is NOT the
      post-fix invariant (only the 8 pre-fix rows had that property, and only by coincidence of the pre-fix bug).
- [x] [DATA] P3. **SUPERSEDED, not executed here — the "~76 rows" premise was stale by ~4 orders of magnitude.**
      Re-checked before building a VM-based fix (per this doc's own pre-task conflict-check discipline) and found a
      SEPARATE, already-in-progress investigation had root-caused the SAME `instrument_type="prediction"` (non-canonical
      lowercase, vs. the canonical `PREDICTION_MARKET`) value one day after this todo was last touched:
      `plans/active/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md` found the real corpus-wide
      straggler count is **~652k+** (per `canonicalize_prediction_manifest_2026_07_18.py`'s own FINDING 2, corpus-wide
      as of 2026-07-18) plus a fresh **~2,704 duplicate rows** from a 2026-08-01 backfill re-run that hit the identical
      writer-vs-rebuild-script mismatch this todo would have. Root cause fixed at the writer level twice over
      (`market-tick-data-service@1ec415f8` 2026-07-19, `@b8a8fa7a` 2026-08-01); the corrected backfill apply was
      actively re-running as of that doc's last checkpoint (2026-08-01 ~14:27 UTC, chunk 42/~62, PID `2843482`) against
      the SAME `market-data-tick-pred-prd-central-element-323112` canonical index this todo would have written to —
      writing an independent ad-hoc script against the same manifest right now would risk colliding with that in-flight
      apply, exactly the class of "additive VM writes against a shared consolidated index" risk the perp_funding P1 todo
      above already surfaced once (concurrent-write race). The actual cleanup tool for the straggler rows
      (`scripts/canonicalize_prediction_manifest_2026_07_18.py --remove-stragglers --apply --confirm-prod-write`)
      already exists, is safety-checked (snapshot-first, CAS-REPLACE, STOP-ON-SURPRISE), and its `--apply` path is
      **explicitly operator-gated** ("do NOT self-execute") — an open `[OPERATOR] P2` todo in the linked issue doc
      already tracks the authorization decision. **No separate action taken or needed from this doc** — closing this
      todo as superseded/redirected rather than leaving a stale, wrong-scoped "~76 rows, VM-based" instruction that
      could mislead a future dispatch into re-doing (or worse, duplicating against) already-correctly-scoped, in-flight,
      operator-gated work. Track remaining prediction-manifest work at
      `mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md` and
      `mtds_available_at_cross_asset_backfill_2026_07_13.md` (tasks `-001`/`-006`), not here.

## Progress Log

- **na-eligibility-audit 2026-07-31** (tranche=cefi, autonomous): **RECLASSIFY, conflict-cleared** — both remaining open
  todos are bounded, deterministic manifest re-stamp work with the target row-level actions already fully enumerated and
  dry-run-verified; blocked purely on infra (local-machine heavy-I/O timeout against the 9.5M-row consolidated manifest,
  per `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-I/O rule), not on any open judgment call. Stated
  safe-idempotent justification present in the P1 todo's own text ("Dedup/upsert semantics mean this is purely additive
  — nothing to undo if a partial run lands before a full one succeeds"), satisfying the VM-launch/`--apply` gating rule
  without an `[OPERATOR]` tag. **Conflict-check (3 surfaces) clear**: (a) no currently-active `assigned_vm: planning`
  plan in `parent_epic: manifest_master` (or elsewhere) claims this exact row set — the adjacent
  `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` and
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md` cover a DIFFERENT, already-resolved set (the DEFI-asset_group
  KALSHI_PERP rows, removed 2026-07-26 via `remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py`), not this doc's
  CEFI-asset_group rows; (b) no sibling batch/finalize doc drafted this run; (c) not cited by any
  `cefi_consolidated_closeout_*.md` aggregation doc. Flipped `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent`, `assigned_role: data_engineering` (verified against the live
  `agents/*.md` registry). **No companion finalize plan authored** — this is a `doc_type: issue` doc, structurally
  exempt from `task_template.md`'s finalize-plan-coverage rule (`check_finalize_plan_coverage.py` only globs
  `plans/active/*.md`, not `plans/active/issues/*.md`), per the skill's own explicit carve-out. **Caveat for the
  dispatched worker**: the P1 todo's cited corrective script lives at an ephemeral scratch path
  (`/private/tmp/claude-501/.../scratchpad/restamp_perp_funding_manifest_FINAL.py`) that will almost certainly not exist
  by dispatch time — re-derive the script from the todo's own fully-enumerated row-level spec (4 KALSHI_PERP captured
  rows → `venue=KALSHI-PERP`; 2 KALSHI_PERP captured rows → `record_failed`/`PHANTOM_CAPTURED_ROW`; 4 POLYMARKET_PERP
  attempted_failed rows → `venue=POLYMARKET-PERP` + `SOURCE_UNREACHABLE`), do not depend on the original file being
  present.

- **worker (slot 16, data_engineering) 2026-07-31**: P1 todo SHIPPED — `market-tick-data-service@5d856acb`. The
  heavy-I/O hypothesis was confirmed rather than just plausible: run from this AO fleet slot (already cloud-hosted,
  exempt from the local-machine restriction), the exact same 9.5M-row full read-merge-write completed in ~72s total
  end-to-end, vs. 8/8 timeouts at 120s each from the prior interactive session. All 8 target rows corrected + verified
  (generation `1785474578081701` → `1785476391377825`, row count invariant at 9,629,206, snapshot taken pre-write). One
  correction to the recipe as originally written: it said "4 KALSHI_PERP captured rows (07-28/07-29) ->
  venue=KALSHI-PERP" — the correct count is 2 (one per date), matching the total of 4 KALSHI_PERP rows split 2-phantom /
  2-real; applied as 2, not 4. Only 6 of the 8 rows needed a venue rename (the 2 phantom KALSHI_PERP rows keep their
  original venue, per the recipe's own wording — nothing to anchor a rename to since no GCS object ever existed for
  those 2 dates).

- **interactive session 2026-07-31 (reconciliation + independent verification)**: this same P1 todo was ALSO being
  worked concurrently by the operator's interactive session (the two efforts collided because the na-eligibility-audit
  reclassified this doc `assigned_vm: NA → planning` and it was dispatched to slot 16 WHILE the interactive session was
  already mid-flight building its own VM-based fix, per the operator's own explicit "put it on a VM then" instruction
  issued earlier the same day) — a genuine multi-agent race, not a process miss on either side. Both fixes are
  append-only / CAS-protected against the same consolidated index, so no data was lost or corrupted; they differed on
  one design point: this session's script
  (`market-tick-data-service/scripts/restamp_perp_funding_venue_manifest_2026_07_30.py`, now deleted, see below) renamed
  `venue` to canonical (`KALSHI-PERP`) on **all 4** KALSHI rows including the 2 confirmed-phantom ones, on the reasoning
  that `venue` identifies which exchange a row is _about_ — an axis orthogonal to whether that day's capture actually
  succeeded — whereas slot 16's script deliberately left the 2 phantom rows' venue unchanged (`KALSHI_PERP`), reasoning
  there was no real backing object to "anchor a rename to." **Ground truth, re-verified by direct read of the live
  consolidated `availability_index.parquet` just now** (178.7 MB blob, last updated `2026-07-31T08:09:16Z`, i.e. after
  slot 16's 05:39 UTC write): all 8 target rows read back fully canonical under the doc's own established recency-wins
  convention — **including both phantom KALSHI rows, which now show `venue=KALSHI-PERP`**
  (`written_at=2026-07-31T07:50:44Z`, i.e. a later write than slot 16's, most likely this session's own earlier VM
  attempt landing via the normal per-VM-shard→consolidator path). So the finished state is the MORE complete of the two
  designs (fully canonical venue on all 8 rows, not just 6) — slot 16's todo-text description of "2 rows keep original
  venue" is now stale against live data and this note supersedes it; no further write is needed. This session's own
  later VM run (race-condition-fixed script, 3rd launch of `mtds-migrate-perp-funding-restamp`, completed `rc=0` at
  `2026-07-31T08:27:19Z`, self-deleted) re-applied the same 8 target values into its own per-VM shard — redundant with
  the already-correct consolidated state, but harmless (idempotent, additive) and independently confirms it.
  **Cleanup**: both now-redundant oneoff scripts deleted per their own `Delete-when` markers (8/8 rows verified
  corrected, held across ≥1 consolidator cycle) — `market-tick-data-service@17204fca` (this session's script
  - slot 16's `restamp_cefi_perp_funding_kalshi_polymarket_venue_2026_07_31.py`, both removed in the same commit). The
    matching VM launcher (`deployment-service/scripts/vm/launch-perp-funding-manifest-restamp-vm.sh`) also has its
    `Delete-when` condition met but is **NOT YET deleted** — the orchestrator's `block_destructive_commands.py`
    guardrail hook rejected a plain `git rm` on this path as a false-positive "recursive rm (tree delete)" match; per
    the hook's own instruction not to route around it, this is left for a future hygiene pass or an operator with a
    permissive session to remove. **P1 todo item is CONFIRMED fully done** — no reopen needed, this is a verification +
    cleanup note, not a correction to the shipped result.
- **context-scout 2026-08-01**: populated context_scope (3 entries).
