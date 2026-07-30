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

- [ ] [DATA] P1. **Fix the storage-client listing helper** used in this investigation (or find/reuse the already-
      correct pattern from `_axis_census.py`'s delimiter descent, which IS proven working — SKILL.md § 3f) so
      `list_blobs(..., delimiter='/')`'s prefix-grouping can be read reliably, then re-run the 07-26/07-27 check against
      a KNOWN-populated day first to prove the method before trusting a negative result.
- [ ] [DATA] P1. **Root-cause the POLYMARKET_PERP capture failure** (Finding A) — get a real error message (the
      manifest's `"polymarket_perp"` placeholder is not one), likely requires a live/dry-run repro of the Polymarket
      perp-funding collector in `market-tick-data-service` (`_perp_funding_kalshi_polymarket.py` /
      `perp_funding_handler.py`). Fix both the actual collection failure AND the `error_reason`-recording bug that let a
      non-message string reach the manifest.
- [ ] [DATA] P2. **Once § listing method is fixed and Finding C is resolved either way**: migrate the confirmed-real
      KALSHI_PERP objects (§3's per-day object counts, re-enumerated correctly) from `venue=KALSHI_PERP/` to
      `venue=KALSHI-PERP/` (copy → content-verify → delete-old, per the delete-safety protocol's five-part proof), and
      re-stamp the 8 manifest rows (venue + chain) so the census stops showing them. If Finding C confirms 07-26/07-27
      are genuinely phantom `captured` rows with no object, that's a `masked_empty_row` finding requiring its own
      remediation (likely `record_failed` re-stamp), not a migrate-in-place.
- [ ] [DATA] P3. **Migrate/correct the ~76 prediction `instrument_type=prediction` manifest rows** (from
      `cefi_sports_prediction_first_census_small_drift_2026_07_30.md` items 6-7) — these are CQG bundle rows with no 1:1
      GCS object (confirmed manifest-only), so this is a pure manifest re-stamp via `record_captured_from_counts` with
      the corrected `instrument_type`, no object migration needed. Lower priority than the cefi items above since it's a
      pure hygiene fix with no live-collection-failure component.
