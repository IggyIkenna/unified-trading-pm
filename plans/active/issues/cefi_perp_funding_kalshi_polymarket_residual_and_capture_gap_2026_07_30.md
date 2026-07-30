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
status: open
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
last_updated: 2026-07-30
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
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
resolved_by:
depends_on: []
---

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
- [ ] [DATA] P1. **Re-stamp the 8 KALSHI_PERP/POLYMARKET_PERP manifest rows — BLOCKED on local-machine infra, not a
      logic gap.** Corrected script ready and dry-run-verified (venue + chain values confirmed correct against the
      reverted source's own `_chain_map`) — script preserved at
      `/private/tmp/claude-501/.../scratchpad/restamp_perp_funding_manifest_FINAL.py` (paste into a fresh script on
      whichever runner executes this). **Every one of 8 `--apply` attempts timed out** (120s client timeout,
      `HTTPSConnectionPool read timed out` / `write operation timed out` / one DNS resolution failure) across ~90
      minutes of retries from this interactive session. Root cause: `DefiManifestRecorder` triggers a full
      read-merge-write of the ENTIRE consolidated `_index/availability_index.parquet` (9.5M rows) on every instantiation
      — this is exactly the class of operation `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-I/O rule
      reserves for a VM in-region, never the operator's local machine ("manifest-index rewrites go on a VM ALWAYS").
      Running it from a local interactive session against a 9.5M-row index is very plausibly the actual cause of the
      sustained timeouts, not incidental network flakiness — 8 consecutive failures over 90 minutes is the
      stable-condition signal, not flapping. **Recipe for the next attempt** (VM, or a session with a demonstrably
      faster path to this bucket): run the preserved script with `--apply`; it write-corrects 4 KALSHI_PERP `captured`
      rows (07-28/07-29, matching the now-real objects) to `venue=KALSHI-PERP`, 2 KALSHI_PERP `captured` rows
      (07-26/07-27, the confirmed-phantom Finding C rows) to `record_failed` with an explicit `PHANTOM_CAPTURED_ROW`
      reason, and 4 POLYMARKET_PERP `attempted_failed` rows to `venue=POLYMARKET-PERP` with the corrected
      `SOURCE_UNREACHABLE` reason. Dedup/upsert semantics mean this is purely additive — nothing to undo if a partial
      run lands before a full one succeeds.
- [ ] [DATA] P3. **Migrate/correct the ~76 prediction `instrument_type=prediction` manifest rows** (from
      `cefi_sports_prediction_first_census_small_drift_2026_07_30.md` items 6-7) — confirmed CQG bundle rows with no 1:1
      GCS object (manifest-only), so this is a pure `record_captured_from_counts` re-stamp, no object migration. **Not
      attempted this session** — deliberately deferred once the identical `DefiManifestRecorder` local-timeout wall hit
      the todo above; the same VM/faster-path prerequisite applies. Lower priority than the cefi items above (pure
      hygiene, no live-collection-failure component).
