---
doc_type: issue
title:
  "TradFi — live databento-mislabeled Yahoo-only venues + FX manifest instrument_id 0%-canonical (two live
  data-correctness defects)"
summary:
  Found during the 2026-07-24 /data-pipeline-reconciliation tradfi raw-tick run. (1) Yahoo-exclusive venues ICE (DXY)
  and KRX (single-stock equities) have REAL captured rows stamped pipeline_mode=batch_databento/source=databento
  starting ~2026-07-18 and continuing through the latest sampled day (2026-07-23) — contradicting
  tradfi-databento-sourcing-ssot.md and UAC's own get_dxy_daily_source()/venue_mapping.py routing code, which both say
  Yahoo-only. FX ohlcv_24h has a structurally identical, much longer-running (2020-2026) companion pattern at larger
  scale (802 of ~3,991 captured rows). (2) tradfi FX SPOT_PAIR manifest instrument_id is 0% canonically-formed across
  its ENTIRE captured history (0/4,310 rows, 2020-2026) — the real GCS object + its content ARE correctly formed
  (verified directly), only the manifest's copy of the shard-atom key is blank/malformed. Neither defect loses real
  market data; both make it wrong or invisible to consumers that trust the manifest/provenance stamp.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    tradfi,
    data-correctness,
    provenance,
    source-priority,
    databento,
    yahoo,
    manifest,
    instrument-id,
    shard-atom,
    ssot-contradiction,
    reconciliation,
  ]
related:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/reconciliation-finding-taxonomy.md,
    /codex/02-data/canonical-cutover-register.md,
    plans/audit/results/data_pipeline_reconciliation_tradfi_2026_07_24.md,
    plans/audit/results/data_pipeline_reconciliation_tradfi_2026_07_21.md,
    plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-24
priority: P0
parent_epic: tradfi_master
source: "/data-pipeline-reconciliation --asset-group tradfi (raw-tick layer, third campaign run), 2026-07-24/25"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# TradFi — live source-mislabeling + FX manifest instrument_id defects

## Why this is a "big finding" (per workspace triage rule)

`SUB_AGENT_MANDATORY_RULES.md` / `CLAUDE.md`: a data-correctness finding that also contradicts an SSOT + shipped code is
escalated to the operator in-chat AND filed as an issue doc, not buried in an audit report. Both defects below meet that
bar. Neither was fixed inline — this is a read-only reconciliation; fixing belongs to MTDS's own plan.

---

## Finding 1 — Yahoo-exclusive venues captured under `source=databento`, live and ongoing

### Evidence

| Venue                                  | Correct source (SSOT)                                              | Real captured rows w/ `source=databento` | Dates                   | First appeared                                                                    |
| -------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------- | ----------------------- | --------------------------------------------------------------------------------- |
| ICE (`ICE:INDEX:DXY-USD`, ohlcv_24h)   | `yahoo`                                                            | 4 (1/day)                                | 2026-07-20, 21, 22, 23  | first `batch_databento` ATTEMPT (empty) 2026-07-18; first REAL capture 2026-07-20 |
| KRX (single-stock equities, ohlcv_24h) | `yahoo`                                                            | 12 (3/day: `000660`, `005380`, `005930`) | 2026-07-20, 21, 22, 23  | same pattern                                                                      |
| FX (currency pairs, ohlcv_24h)         | `yahoo` (ohlcv_24h is documented as NOT a Databento schema at all) | 802 of ~3,991 captured FX ohlcv_24h rows | 2020-01-02 → 2026-07-23 | present since 2020 — a longer-running companion of the same defect class, not new |

**Content-verified, not just manifest-inferred.** Fetched the actual GCS object:

```
raw_tick_data/by_date/day=2026-07-20/pipeline_mode=batch_databento/asset_group=tradfi/venue=ICE/
  instrument_type=index/data_type=ohlcv_24h/ICE:INDEX:DXY-USD.parquet
```

Content: `open/high/low/close ≈ 100.98`, `volume=0.0`, `symbol=DXY`, `instrument_id=ICE:INDEX:DXY-USD` — a plausible,
correctly-typed, correctly-named DXY row. The corresponding manifest row for the same shard atom:
`pipeline_mode=batch_databento, source=databento, capture_status=captured`.

Same for KRX `000660`/`005380`/`005930` on 2026-07-21/22/23 — plausible KRW-scale close/volume, correct
`KRX:EQUITY:{code}-USD` id.

### Why this contradicts the SSOT — grep-then-READ, cited precisely

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` § "KRX + ICE are YAHOO FINANCE, not Databento" (2026-06-27 operator
  correction): _"neither KRX nor ICE is 'operator-blocked', 'Databento-sourced', 'needs an adapter', or 'off-allowlist'…
  the data is freely available via Yahoo and the adapters exist."_ Also: _"Explicitly NOT subscribed (querying them
  raises `DatabentoDatasetNotAllowedError`): all ICE feeds (`IFEU.IMPACT` Brent/Gasoil, `IFUS.IMPACT` ICE Dollar-Index +
  softs)…"_
- `unified-api-contracts/unified_api_contracts/registry/data_source_continuity.py:218-225` —
  `get_dxy_daily_source(query_date)` has exactly two return paths: `"GAP_NO_SOURCE"` (pre-2019-01-02) or
  `"YAHOO_FINANCE"`. There is no code path in this function that ever returns `"databento"`.
- `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:237` — `"ICE": "yahoo_finance"` is the **only**
  entry for `ICE` in `venue_to_data_provider`.
- `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1774-1777` — the BARCHART capability
  block was removed 2026-07-15 with the comment _"BARCHART was removed from `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24
  (VIX 15m now aggregates from VX futures via Databento XCBF.PITCH)"_ — the doc trail is explicit that Databento does
  not serve ICE/KRX-style daily-index/equity data by design; the whole point of the 2026-06-18 subscription lockdown was
  to enumerate exactly which venues/schemas Databento legitimately covers.

### Hypothesis (unverified — for the investigating team, not asserted as root cause)

The pattern (correct VALUE, wrong PROVENANCE STAMP, starting abruptly on a specific date, across multiple venues at
once) closely resembles the **already-fixed** 2026-06-19 CBOE bug documented in the same SSOT doc: _"the OHLCV write
path used to stamp `source`+`pipeline_mode` from `SOURCE_PRIORITY[(asset_group, data_type)][0]`… For
`("tradfi","ohlcv_1m")` priority is `["massive","databento"]`, so EVERY 1m row stamped `batch_massive` — including CBOE
VX futures, which only Databento carries."_ The fix added a per-venue `_VENUE_SOURCE_EXCLUSIONS` guard
(`("CBOE","ohlcv_1m"): {massive}`). The 2026-06-24 "TradFi SOURCE_PRIORITY is DATABENTO-FIRST" change (same SSOT doc)
may have introduced or reactivated a code path for `ohlcv_24h` / daily singles that does not yet carry an equivalent
`_VENUE_SOURCE_EXCLUSIONS` entry for ICE/KRX/FX the way CBOE already has one for `ohlcv_1m`. **Not verified this run** —
would require reading the live daily-forward-poll launcher/cron config and the write-stamp call site, which is out of
scope for a read-only reconciliation.

### Suggested next steps (not executed — belongs to MTDS's plan)

1. Find whatever process wrote these rows (daily forward-poll cron most likely, given the tight 4-consecutive-day
   pattern) and confirm whether it is passing `--source` explicitly or falling through to a priority-based default.
2. Add/verify `_VENUE_SOURCE_EXCLUSIONS` entries for `("ICE", "ohlcv_24h")`, `("KRX", "ohlcv_24h")`, and — given the
   SSOT states Databento serves no `ohlcv_24h`/`ohlcv_15m` schema at all — consider whether `ohlcv_24h` should be
   excluded from Databento venue-wide rather than per-venue.
3. Re-stamp the affected historical rows (4 ICE + 12 KRX this run, 802 FX, likely more once the true full-history FX
   count is walked) once the writer is fixed — do not leave mislabeled provenance in place.
4. Check whether this indicates an actual Databento API call is being made for these venues (a possible billing-guard
   gap) or whether the value is genuinely fetched via Yahoo but mis-stamped downstream (a pure write-time labeling bug).
   The evidence available to this reconciliation (real, plausible values; a doc trail saying Databento can't serve this)
   leans toward the latter, but this was not independently confirmed against the Databento allowlist guard's runtime
   behavior.

---

## Finding 2 — tradfi FX `SPOT_PAIR` manifest `instrument_id` is 0% canonically-formed, entire history

### Evidence

Of **4,310 captured FX rows** (every FX row in the manifest with `capture_status=captured`, spanning 2020-01-02 →
2026-07-23), **0 (0.00%)** carry a well-formed `FX:SPOT_PAIR:XXX-USD` id in the **manifest** `instrument_id` column:

| Manifest `instrument_id` shape                                                          | Count | Note                                                                  |
| --------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------------------- |
| blank                                                                                   | 2,812 | majority, all years                                                   |
| literal string `"ticks"`                                                                | 983   | the BUNDLE FILENAME token (`ticks.parquet`) leaking into the id field |
| bare pair, no venue/type prefix (`EUR-USD`, `AUD-USD`, `KRW-USD`, …)                    | 501   | ALL from 2026 — i.e. the CURRENT, latest write shape                  |
| `FX:SPOT_PAIR:...` / `YAHOO_FINANCE:SPOT_PAIR:...` (correctly or near-correctly shaped) | 13    | 2025 only, a small minority                                           |

**The real GCS object and its own content ARE correctly formed** — verified directly:

```
raw_tick_data/by_date/day=2026-07-23/pipeline_mode=batch_databento/asset_group=tradfi/venue=FX/
  instrument_type=spot_pair/data_type=ohlcv_24h/FX:SPOT_PAIR:AUD-USD.parquet
```

content: `instrument_id="FX:SPOT_PAIR:AUD-USD"` — matches the filename byte-for-byte. This is a correct S1 (path) and S2
(content) pair. The **manifest row for the exact same shard atom** (venue=FX, date=2026-07-23,
pipeline_mode=batch_databento, instrument_type=spot_pair, data_type=ohlcv_24h) carries `instrument_id="AUD-USD"` — one
of the 501 "bare pair" rows above, missing the `FX:SPOT_PAIR:` prefix that the real file has.

**FX is a categorical outlier, not the tail of a shared distribution.** The same blank-id check on other tradfi
single-instrument venues: NASDAQ EQUITY 0.81% blank, NYSE EQUITY 0.11% blank, NASDAQ/NYSE ETF 0.0% blank. Nowhere else
in tradfi does the manifest lose the id at anything close to this rate.

### Why this doesn't fit an existing taxonomy type cleanly

`reconciliation-finding-taxonomy.md`'s 20 named types don't have a clean home for "the GCS path + parquet content
(S1+S2) are correct, but the manifest's (S3) copy of the atom key is wrong/blank, for a flat-per-contract pattern where
the manifest key is supposed to be non-null by design." `non_canonical_id` (§2.7) is about the PARQUET row's own
`instrument_id` vs the rebuilt id — that's fine here, so it doesn't fire. This is reported under the taxonomy's own
rule: _"A disagreement that fits no type is itself a finding — of a taxonomy gap — and gets escalated."_

### Operational impact

Any consumer that resolves an individual FX pair via the manifest's `instrument_id` column — a per-instrument
data-status drilldown, a phantom-reconciler stem-vs-column check, an id-keyed join into features/strategy — sees garbage
or nothing for FX, for the entire 6-year captured history, including the most recent capture. The market data itself is
not lost; it is simply not discoverable through the manifest's own key.

### Suggested next steps (not executed)

1. Read the FX write path in MTDS (`_umi_yahoo.py` per the sourcing SSOT's routing comments) and find why the
   manifest-writer call for FX never receives a populated `instrument_id`, unlike every other single-instrument tradfi
   venue's write path.
2. Once fixed going forward, backfill the manifest `instrument_id` column for the 4,310 affected historical rows — this
   is a manifest-only repair (`record_captured`-style re-stamp via `merge_canonical_with_outstanding_shards`), NOT a GCS
   content rewrite; the underlying parquet files do not need to change.
3. Consider whether `reconciliation-finding-taxonomy.md` should gain a formal type name for this class ("manifest atom
   key desync from the file's own true id, on a pattern where the key is supposed to be non-null") — the taxonomy
   owner's call, not this issue doc's.

---

## What this issue doc is NOT

- Not a delete suggestion. No delete is proposed for either finding.
- Not a claim about billing exposure. Finding 1 may or may not reflect an actual Databento API call for an off-allowlist
  venue; this was not independently confirmed.
- Not a full-corpus certification. Both findings are evidenced by direct content fetches (small, targeted samples) plus
  full-manifest-index aggregate counts (which ARE exhaustive over the manifest, unlike the GCS-side samples).

## Full report this issue was extracted from

`plans/audit/results/data_pipeline_reconciliation_tradfi_2026_07_24.md` §3d, §3e, §7.

## Progress Log

- **2026-07-26 (slot-3) — Finding 1 ROOT-CAUSED + FIXED at the code level; historical re-stamp + Finding 2 still open.**
  Traced the write path: `market-tick-data-service`'s manifest-finalize call (`_write_shard_counts_to_manifest` →
  `_resolve_pipeline_mode_for_sentinel(..., source=state.source)`) reaches
  `unified_trading_library.pipeline_mode_resolver.derive_pipeline_mode_for_row`'s EXPLICIT-source branch, which trusted
  a caller-supplied `--source` unconditionally on the documented assumption that `assert_source_capable_for_venue` had
  already fail-closed-validated it at fetch time. That assumption only holds for the `venue_data_types` actually
  validated in ONE `venue_fetch.py` call — a shared run-level `--source databento` (legitimate for CME/CBOE
  `ohlcv_1m`/`ohlcv_1s` in the same VM run, confirmed against
  `deployment-service/scripts/vm/launch-tradfi-forward-poll.sh:132` `VM_SOURCE=databento`) reaching a manifest-finalize
  call for a DIFFERENT (venue, data_type) pair — ICE/KRX/FX `ohlcv_24h`, which is Yahoo-only
  (`SOURCE_PRIORITY[("tradfi","ohlcv_24h")] = ["yahoo"]`, databento not even a registered member) — fabricated a
  `batch_databento` stamp for what was structurally-verified-plausible Yahoo-sourced data. This does NOT indicate an
  actual off-allowlist Databento API call (no evidence of that either way; the manifest stamp itself was simply wrong) —
  the "billing-guard gap" question in Finding 1's suggested next-steps stays genuinely unconfirmed. **Fix**:
  `unified-trading-library@f237b75a` — `derive_pipeline_mode_for_row`'s explicit-source branch now re-validates via
  `is_source_capable_for_venue(asset_group, data_type, venue, source)` before trusting the explicit source; an incapable
  combination falls through to the venue-aware/SOURCE_PRIORITY resolution (Yahoo) instead of stamping a provenance lie.
  Regression tests added (`test_explicit_source_incapable_for_venue_falls_ through_not_fabricated`,
  `test_explicit_source_capable_for_venue_still_honored`); `quality-gates.sh` green. This closes the write path for ALL
  current + future callers, not just this one occurrence — broader and safer than the originally-suggested narrow
  `_VENUE_SOURCE_EXCLUSIONS` entries (which would have been redundant here since `databento` isn't registered for
  `ohlcv_24h` at all; the actual gap was the explicit-source branch bypassing the capability check entirely). **NOT done
  this pass** (genuinely remaining, tracked as fresh todos below): (a) re-stamp the confirmed-affected historical rows
  (4 ICE + 12 KRX + 802 FX, likely more on a full walk) now that new captures write correctly; (b) Finding 2 (FX
  `SPOT_PAIR` manifest `instrument_id` 0%-canonical) — a fully separate defect in a different write path, not
  investigated this pass.

### Deferred work after 2026-07-26 (slot-3)

| Item                                                                                    | State                                                                                             | Blocked on                                                                         |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Re-stamp historical ICE/KRX/FX `ohlcv_24h` rows (4+12+802, snapshot-first)              | ✅ Census DONE 2026-07-26 (slot 2) — see below; APPLY still `[OPERATOR]`-gated                    | operator CAS-apply per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` |
| Finding 2 — FX `SPOT_PAIR` manifest `instrument_id` write-path fix + 4,310-row backfill | IN PROGRESS 2026-07-26 (slot 2) — write-path fix underway, historical backfill stays out of scope | nobody                                                                             |
| Confirm/rule out an actual Databento billing-guard gap for the pre-fix window           | Not done — needs Databento request-log access, not just code reading                              | possibly operator (Databento account access)                                       |

Recommended next: the historical re-stamp (bounded, mechanical, unblocks nothing else) before Finding 2 (a fresh
investigation of similar depth to Finding 1's).

### Full-history census (2026-07-26, slot 2)

Read the live `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` as a single object
(no GCS walk — same method the legacy-bucket census used), snapshot at 2026-07-26 ~18:33 UTC. Filtered
`capture_status == "captured"`, `data_type == "ohlcv_24h"`, `venue` in `{ICE, KRX, FX}`, and (`pipeline_mode` containing
`databento` OR `source == "databento"`) — the same databento-derived-mislabel signature Finding 1 documents. Total
manifest rows scanned: 5,825,023.

**Corpus-wide result: 1,141 mis-stamped rows (vs. the 818-row 2026-07-24 sample-window estimate — the real number is
~40% higher, and FX's affected range starts in 2020, not just "present since 2020" as prose — it never fully stopped):**

| Venue | Year | Count |
| ----- | ---- | ----- |
| ICE   | 2026 | 5     |
| KRX   | 2026 | 12    |
| FX    | 2020 | 134   |
| FX    | 2022 | 2     |
| FX    | 2023 | 114   |
| FX    | 2024 | 297   |
| FX    | 2025 | 401   |
| FX    | 2026 | 176   |

**Totals by venue**: ICE=5, KRX=12, FX=1,124. **Grand total: 1,141**. Snapshot path:
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (read 2026-07-26, do not
reuse this count without a fresh re-read — the manifest keeps growing). The 2021 gap in FX's per-year breakdown (zero
rows) is itself worth noting for whoever runs the apply — either a genuine gap in the mislabeling pattern that year, or
FX simply had less overall `ohlcv_24h` capture volume in 2021; not investigated further here (out of this todo's
read-only scope). This is the exact worklist the `[OPERATOR]` CAS re-stamp gate needs — the count itself is NOT applied
here, per this todo's explicit scope boundary.
