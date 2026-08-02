---
doc_type: issue
title: >-
  perp_daily_ctx/perp_funding manifest-invisibility — derivative_ticker migration DECLINED (live paper-trading reader
  risk); safe incremental fix identified instead
summary: >-
  Investigated distinct_values_noncanonical_audit_2026_07_20.md's perp_daily_ctx/perp_mark_price todo (migrate the MTDS
  HL backfill script + features-service CeFi corpus writer onto the derivative_ticker schema). Found the proposed target
  directly conflicts with the CURRENT production read shape — CanonicalPerpFundingProvider (instantiated by the live
  paper-trading CLI paper_run_handler.py:931-932) reads perp_funding + perp_daily_ctx TODAY, serving real,
  already-migrated historical HYPERLIQUID/GMX/CeFi funding+mark-price data (the 2026-07-13
  dedicated-bucket-to-shared-bucket migration copied years of real production rows into this exact shape). Migrating
  onto derivative_ticker would require rewriting the live reader + a real backfill/dual-read transition, and would
  pre-empt an already-gated, NOT-yet-approved separate design decision (see Established facts). Declined the risky
  migration per this task's own explicit safety override; documented a safe incremental alternative instead (register
  perp_daily_ctx as its own canonical data_type + backfill manifest rows for the already-migrated historical shard
  tuples, WITHOUT touching the reader or writer schema) — flagged as itself needing operator awareness before autonomous
  execution, mirroring this exact plan's own established "UAC canonical-set additions are not safe-code" precedent
  (RESULT 4, venue-axis case).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, features-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    perp-funding,
    perp-daily-ctx,
    derivative-ticker,
    manifest,
    honest-coverage,
    canonicalisation,
    live-strategy-reader,
    data-correctness,
  ]
related:
  [
    plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/active/issues/downstream_funding_staking_canonical_reader_audit_2026_07_21.md,
    plans/archive/issues/mtds_plan_reconciliation_2026_06_29.md,
  ]
created: "2026-07-22"
last_updated: "2026-07-22"
parent_epic: manifest_master
priority: P1
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md's perp_daily_ctx/perp_mark_price todo (line ~330), dispatched to a
  sub-agent under /autonomous with an explicit override to stop short of forcing the migration if the live-reader risk
  proved real
assigned_vm: NA
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
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
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
---

# perp_daily_ctx/perp_funding manifest-invisibility — derivative_ticker migration DECLINED, safe alternative identified

## Verdict

**Did NOT execute the migration the source todo asked for.** Investigation (below) shows the requested "migrate both
writers onto `derivative_ticker`" fix would touch a **live, currently-consumed strategy read path** in a way that cannot
be verified safe within this session's scope, and would pre-empt a separate, already-gated, not-yet-approved design
decision. Per this task's explicit safety override, stopping here with a full writeup + a concrete, safe, incremental
alternative rather than forcing the migration. No code was changed in market-tick-data-service, features-service, or
strategy-service.

## What the source todo asked for (paraphrased)

`distinct_values_noncanonical_audit_2026_07_20.md` (~line 330) flagged `perp_daily_ctx`/`perp_mark_price` as
"structurally invisible" to the honest-coverage system — written via raw `gcsfs` calls with zero manifest writes, by:

1. `market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — a campaign-scoped
   Hyperliquid mark-price backfill.
2. `features-service/features_service/cefi/calculators/perp_funding_corpus.py` — a CeFi perp-funding corpus writer.

Proposed fix: migrate both onto the `derivative_ticker` data_type/schema (`DEFI_PERPETUAL_DERIVATIVE_TICKER`,
`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:766-782` — one row per instrument/day with
`funding_rate`/`open_interest`/`mark_price`/`index_price` as embedded, nullable fields) and retire the raw-gcsfs path.

## Established facts (verified this session, file:line evidence)

1. **`perp_funding` is ALREADY a registered canonical data_type with a full SchemaContract** —
   `unified-api-contracts/.../registry/market_data_categories.py:165` (`DATA_TYPES_BY_ASSET_GROUP["defi"]`) +
   `unified_api_contracts/internal/schemas/contracts.py:745-758` (`DEFI_PERPETUAL_PERP_FUNDING`). The source todo's
   claim "neither is a canonical data_type" is only half right. **`perp_daily_ctx` is the genuine gap** — it appears
   nowhere in `DATA_TYPES_BY_ASSET_GROUP` or any `SchemaContract`.

2. **`CanonicalPerpFundingProvider` is the live production reader, and it reads `perp_funding` + `perp_daily_ctx`
   TODAY** — `strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py:65-66`
   (`_FUNDING_DATA_TYPE = "perp_funding"`, `_DAILY_CTX_DATA_TYPE = "perp_daily_ctx"`), reading from
   `resolve_bucket_name(kind="tick-data", asset_group="defi")` (the shared, canonical bucket — not a side channel).
   **Real production caller confirmed**: `strategy-service/strategy_service/cli/handlers/paper_run_handler.py:931-932`
   instantiates `CanonicalPerpFundingProvider()` and calls `funding_window(...)` directly in the paper-trading run path
   (also `paper_universe_metrics.py`). This is the CARRY_BASIS_PERP / CARRY_FUNDING_DISPERSION archetype's real data
   feed, not a dead or diagnostic-only path.

3. **The current `perp_funding`/`perp_daily_ctx` rows in the shared bucket are REAL, migrated PRODUCTION history, not
   placeholder/test data.**
   `market-tick-data-service/market_tick_data_service/scripts/ migrate_lst_perp_shared_bucket_gap_2026_07_13.py`
   (referenced from `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`) copied years of real
   HYPERLIQUID/GMX/CeFi funding + mark-price history from the now-deleted dedicated `perp-funding-{project}` bucket into
   the shared bucket at the IDENTICAL `perp_funding`/`perp_daily_ctx` path shape (same key, `gcs_copy_object`, no
   transform). Verified counts from that plan's Progress Log: HL `perp_daily_ctx` 1,109 objects + a later 6,941-object
   residual-gap closure (HL funding 177d, the whole HL `perp_mark_price` data_type 316d, GMX 2021-2023 funding history,
   7 CeFi Tardis venues' captures, etc). Post-migration live verification: `funding_for_day(2026-05-18)` → 697 real
   observations across 7 CeFi venues + HL + GMX, all with real `mark_price` populated from `perp_daily_ctx`.

4. **The MTDS HL mark-price backfill script targets a bucket that is CONFIRMED DELETED.** Live-checked this session:
   `gcloud storage buckets describe gs://perp-funding-central-element-323112` → **404 not found.** The script's
   `PF_BUCKET = f"perp-funding-{PROJECT}"` (line 42) can no longer be written to — any `--apply` run today would error
   outright, not silently succeed. This is corroborated by
   `plans/active/issues/downstream_funding_staking_canonical_reader_audit_2026_07_21.md` ("3 funding diagnostic scripts
   on the deleted `perp-funding-{pid}` bucket ... deleted 2026-07-10") and by
   `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s P3 housekeeping todo (open when this was written; closed
   2026-07-31 per na-eligibility-audit — doc now archived at
   `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`), which explicitly names
   `backfill_hl_*_2026_06_17.py` as hardcoding a dead bucket name tied to an already-completed migration — **this
   script's disposition was tracked in that OTHER plan.** Not touched here to avoid collision with whoever owns that
   plan's cleanup pass. Its own lifecycle marker
   (`# Delete-when: after HyperLiquid mark-price backfill prod-run verified + GCS orphan sweep = 0`) appears already
   satisfied — the backfill's real historical output is the exact data the 2026-07-13 migration copied forward, and the
   source bucket is confirmed gone.

5. **The features-service CeFi corpus writer (`perp_funding_corpus.py`) targets the CORRECT current-schema location but
   has never run in production.** Its own docstring (lines 21-26) states it writes to the shared bucket at
   `perp_funding`/`perp_daily_ctx` (matching what the reader expects), and "has never actually run in production
   (confirmed via a direct real-data check 2026-07-13 — zero `asset_group=cefi`/`pipeline_mode=batch_tardis` objects
   exist in either bucket across 2021-2026)". No historical CeFi data is at stake for this one specifically — but
   migrating ONLY this writer's schema to `derivative_ticker` without also updating the reader would make its future
   output permanently unreadable by `CanonicalPerpFundingProvider` (defeating the writer's whole purpose — unblocking
   CARRY_BASIS_PERP non-HL venues + CARRY_FUNDING_DISPERSION), since the reader would still be looking for
   `perp_funding`/`perp_daily_ctx`.

6. **The 2026-07-15 operator ruling on `derivative_ticker` is about the MTDS CAPTURE layer, and explicitly does NOT yet
   authorize retiring `perp_funding`/`perp_daily_ctx` as the read/strategy-facing shape.**
   `plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` established
   `derivative_ticker` as the canonical RAW-funding capture home for ALL perp venues going forward (MTDS wiring, GMX
   dual-write, etc) — this is a genuinely-shipped, separate change. But that SAME doc carries an explicitly gated,
   still-open `[DESIGN] P1` todo: _"Decide: demote `perp_funding` from a captured raw type to a DERIVED interval view...
   Scope of the decision (do NOT execute before the parity evidence exists)..."_ — unchecked (`[ ]`), and its own stated
   scope is `perp_funding` only; it never even mentions `perp_daily_ctx`/mark-price. Executing the source todo's
   requested migration (retire `perp_funding`/`perp_daily_ctx` on the STRATEGY READ side in favor of
   `derivative_ticker`) would pre-empt this still-undecided, explicitly-gated design question — for a shape (mark price)
   that design todo doesn't even cover yet.

## Why the requested migration is declined (risk assessment)

Doing what the source todo asked — rewrite both writers to emit `derivative_ticker` rows and retire the raw-gcsfs path —
necessarily also requires rewriting `CanonicalPerpFundingProvider` (it has no other way to see the new shape), which is
read by the live paper-trading CLI today. That, in turn, requires one of:

- **Backfilling** years of already-migrated real HL/GMX/CeFi `perp_funding`+`perp_daily_ctx` history into the new
  `derivative_ticker` row shape (a real, large, non-trivial data transform on live-strategy-facing history — no small
  "add a manifest call" change), or
- **Dual-reading** both shapes in the provider during a transition window (real added complexity + a real
  determinism/testing burden — `paper(W) == batch-rerun(W)` epsilon=0 must hold per
  `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, and this session cannot fully verify that
  invariant survives a live-schema change to a strategy-reading class without a dedicated backtest re-run), plus
- Pre-empting the separately-gated `[DESIGN] P1` decision above, which the operator has not yet ruled on.

This is exactly the class of risk the task's own explicit safety override anticipated ("the reader would need
simultaneous changes you're not confident are safe... STOP and write a thorough investigation"). Declining to force it.

## Safe, incremental alternative (proposed, NOT executed)

The actual complaint driving the source todo is **manifest-invisibility**, not the schema shape itself — "this cluster
will keep costing real coverage/completeness accuracy without ever tripping the distinct-values panel, since the panel
only ever sees what's in the manifest." That can be fixed WITHOUT touching the live reader or either writer's row shape:

1. Register `perp_daily_ctx` as its own canonical data_type in `DATA_TYPES_BY_ASSET_GROUP["defi"]` + add a
   `SchemaContract` mirroring `DEFI_PERPETUAL_PERP_FUNDING`'s shape (mark_price + day_ntl_vlm + open_interest columns,
   `instrument_id`/`venue`/`chain`/`ts_event`) — `perp_funding` already has one; `perp_daily_ctx` needs its own, not a
   fold into `derivative_ticker`.
2. Add real `ManifestWriter`/`record_captured` calls to both ad-hoc writers, keeping their CURRENT
   `perp_funding`/`perp_daily_ctx` data_types exactly as-is (zero change to what the reader sees or reads).
3. Backfill manifest rows for the already-migrated historical `(venue, data_type, day)` shard tuples sitting in the
   shared bucket today (mirrors the precedent already executed for the dex_pools/lending_indices fold —
   `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`, `status: resolved` 2026-07-22, path
   corrected 2026-07-26 by `/plan-reconcile defi` — a manifest-registration-only pass, zero GCS object mutation).

**This proposal is NOT executed here either**, for one reason worth flagging explicitly: step 1 (adding a new canonical
`data_type` to `DATA_TYPES_BY_ASSET_GROUP`) is the same class of change this exact parent plan
(`distinct_values_noncanonical_audit_2026_07_20.md`, RESULT 4) already established is **"NOT safe-code"** for the venues
axis — a canonical-set addition can expand what the standing expected-universe enumerator treats as
`expected_unattempted` across the historical calendar, which can visibly DROP measured `completeness_pct` fleet-wide
(the same "rule-11 blast radius" already flagged there for venues). The same mechanism plausibly applies to a new
data_type addition. This needs a quick, cheap check (does adding a data_type to this dict, for an
already-perpetual-scoped instrument_type, actually mint new `expected_unattempted` rows across the full historical
window, or is the perpetual/defi denominator already bounded by venue×instrument_type independent of this specific
list?) before executing autonomously — flagging for operator awareness rather than guessing.

## What was deliberately NOT touched (collision avoidance)

- `market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — disposition was tracked
  as a P3 todo in `defi_dedicated_bucket_shared_migration_2026_07_13.md` (housekeeping cluster, item 3; closed
  2026-07-31, doc now archived at `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`). Not
  deleted or edited here.
- `market-tick-data-service/market_tick_data_service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — same
  plan's P3 item 1 (its own `Delete-when` condition was already satisfied and the file deleted — see the archived doc).
  Not deleted here.
- `strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py` — the live reader. Not touched.
- `features-service/features_service/cefi/calculators/perp_funding_corpus.py` — the unrun CeFi writer. Not touched (its
  current schema is already correct for what the reader expects; only the manifest-writing gap is real).

## Todos (for whoever picks this up next — NOT dispatched automatically)

- [x] ✅ [VERIFY] P2. **DONE 2026-07-28 (slot-6, data_engineering).** Confirmed whether adding a data_type to
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` (for an already-registered venue×instrument_type combination) actually changes
      `expected_unattempted` materialisation / `completeness_pct`, or whether that denominator is scoped independently.
      See Progress Log entry above: NOT inert in general (the axis is a direct enumerator input, unlike the venue axis)
      but IS inert specifically for HYPERLIQUID/CeFi combos, since they enumerate under
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]`, a separate dict key.
- [ ] [CODE] P2. (Gated on the verify above.) Register `perp_daily_ctx` under `DATA_TYPES_BY_ASSET_GROUP["defi"]` ONLY
      (confirmed inert for HYPERLIQUID/CeFi combos, no operator sign-off needed for THIS specific registration — see
      Progress Log) as its own canonical data_type + SchemaContract (mirror `DEFI_PERPETUAL_PERP_FUNDING`); add manifest
      writes to both ad-hoc writers, unchanged schema; backfill manifest rows for the existing historical shard tuples.
      Repos: unified-api-contracts, market-tick-data-service, features-service, unified-trading-pm (manifest backfill
      script). **na-eligibility-audit 2026-08-01: KEEP-NA-STALE-DUPLICATE — already extracted verbatim into
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md:363-371` (status: active, `assigned_vm: planning`, cites this doc
      as source). Not reclassified — track completion there; close this checkbox by citation once batch6's todo lands.**
- [ ] [OPERATOR-DECISION] P3. Whether/when to execute the ALREADY-GATED `[DESIGN] P1` todo in
      `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` (demote `perp_funding` to a derived
      view) — and, if so, whether `perp_daily_ctx`/mark-price should be folded into that same decision. This issue doc
      does not resolve that question; it only establishes that the source todo's migration should not be forced ahead of
      it.

## Not fixed here, why

This is a stop-and-document outcome per this task's explicit safety override, not a completed migration. See "Verdict"
above.

## Progress Log

- **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE-DUPLICATE — re-verified: the [CODE] P2 half's AO-readiness (flagged
  2026-07-30) has since been realized via `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s verbatim extraction (same
  date, 2026-07-30) — see inline note above. Not reclassified (already dispatched elsewhere). The [OPERATOR-DECISION] P3
  item remains genuinely open/unresolved. Doc not archive-eligible until both resolve.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - carries an explicit [OPERATOR-DECISION] P3 todo; the [CODE] P2
  half is AO-ready but the doc cannot flip as a unit
- **context-scout 2026-08-01**: populated context_scope (4 entries).

### 2026-07-28 — data_engineering (slot-6): data_type-axis denominator trace

Answers this doc's own P2 verify todo + `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s mirrored todo.

**Question**: does adding a data_type to `DATA_TYPES_BY_ASSET_GROUP["defi"]` (for an already-registered HYPERLIQUID/CeFi
venue×instrument_type combination) change `expected_unattempted` materialisation / `completeness_pct`, or is that
denominator scoped independently — mirroring RESULT 4's venue-axis finding in
`distinct_values_noncanonical_audit_2026_07_20.md`?

**Verdict — for the specific HYPERLIQUID/CeFi combos named in the source todo: NO, it does not change anything.** But
the axis is NOT scoped independently in general — the mechanism is real and would fire for genuine defi-asset-group
protocols. Read-only code trace, no code/schema/manifest changes made.

**Mechanism (unlike the venue axis, which routes indirectly through the catalogue, the data_type axis is consumed
DIRECTLY by the enumerator):**

- `instruments-service/scripts/enumerate_expected_universe.py:4145` —
  `data_types_list = [str(dt) for dt in DATA_TYPES_BY_ASSET_GROUP.get(asset_group, [])]` (the
  `"defi"`/`"cefi"`/`"prediction"` fallback branch), fed into `enumerate_v2(...)` (:4160) →
  `_row_data_types(asset_group, instr, data_types)` (defi path at :1482).
- Inside `_row_data_types` (:649-698):
  `valid = valid_data_types_for_venue_instrument_type(asset_group, instr.venue, instr.instrument_type)` (:681);
  `known_ag_dts = frozenset(DATA_TYPES_BY_ASSET_GROUP.get(asset_group.lower(), []))` (:696);
  `row_dts = [dt for dt in data_types if dt in valid or dt not in known_ag_dts]` (:698). So once a data_type is
  registered (→ "known"), it survives the filter only if `valid` includes it.
- For `asset_group == "defi"`, `valid` comes from `valid_data_types_for_venue_instrument_type`
  (`unified_api_contracts/registry/market_data_categories.py:1443-1517`), which narrows to the specific protocol's
  `PROTOCOL_CAPABILITIES[protocol].data_types` (:1487-1503), keyed off `venue.split("-", 1)[0]` — a registry entirely
  independent of `DATA_TYPES_BY_ASSET_GROUP`.
- **Conclusion on the general mechanism**: registering a new data_type in `DATA_TYPES_BY_ASSET_GROUP["defi"]` DOES
  expand the denominator / move `completeness_pct` for any real defi-asset-group protocol×instrument_type pair whose
  `PROTOCOL_CAPABILITIES` entry also lists that data_type — this axis is NOT independently scoped the way the venue axis
  effectively is; it is a direct enumerator input gated only by the protocol-capability allowlist.

**Why the HYPERLIQUID/CeFi combos specifically are unaffected**: `HYPERLIQUID` is registered in
`VENUES_BY_ASSET_GROUP["cefi"]` (`market_data_categories.py:360`, "On-chain CLOBs reclassified from DEFI" section), NOT
in `VENUES_BY_ASSET_GROUP["defi"]`. Its catalogue rows are therefore enumerated via the **CEFI** pass
(`_row_data_types("cefi", instr, data_types)` at `enumerate_expected_universe.py:1157`), whose candidate `data_types`
list is sourced from `DATA_TYPES_BY_ASSET_GROUP["cefi"]` — a completely separate dict key from `["defi"]`. Different
asset_group ⇒ different `data_types_list` ⇒ different `known_ag_dts` ⇒ different `valid` branch. So editing
`DATA_TYPES_BY_ASSET_GROUP["defi"]` alone touches zero HYPERLIQUID/CeFi shard tuples — it mints no new
`expected_unattempted` rows and moves no completeness_pct for them, full stop. (Note: a
`PROTOCOL_CAPABILITIES["hyperliquid"]` entry does exist, `capability_declarations/_defi.py:715-721`,
`data_types=["perp_funding", "oracle_prices"]` — but it is unreachable for enumeration purposes since HYPERLIQUID is
never iterated under the `"defi"` asset_group.)

**Implication for this doc's own gated P2 todo (below, "register `perp_daily_ctx` as its own canonical data_type")**:
the safe-alternative's step 1 is genuinely inert / operator-sign-off-free **only if `perp_daily_ctx` is registered
solely under `DATA_TYPES_BY_ASSET_GROUP["defi"]`** (as the todo literally asks) — because none of the affected
combinations (HYPERLIQUID, CeFi venues) enumerate under that key. It would NOT be inert if the registration instead
targeted `DATA_TYPES_BY_ASSET_GROUP["cefi"]` (the dict HYPERLIQUID/CeFi venues actually enumerate under) — that edit
would expand the cefi denominator for any cefi venue×instrument_type whose `valid_data_types_for_venue_instrument_type`
branch (cefi's own gating, not traced further here — out of this todo's scope) admits `perp_daily_ctx`, and would need
the same operator-gating precedent as RESULT 4's venue-axis finding.

Full trace performed by a dispatched read-only Explore sub-agent (Sonnet); no files edited in
instruments-service/unified-api-contracts/market-tick-data-service/features-service/strategy-service.
