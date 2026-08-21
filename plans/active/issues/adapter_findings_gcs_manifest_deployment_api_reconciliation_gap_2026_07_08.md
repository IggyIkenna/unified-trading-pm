---
doc_type: issue
title:
  "None of this session's adapter/instrument-definition findings have been verified for 3-layer reconciliation — GCS
  parquet, manifest, and deployment-ui/API may each tell a different story"
summary:
  "The 2026-07-07 full adapter smoke test (17 clusters, [[mtds_is_full_adapter_smoketest_findings_2026_07_07]]) and the
  lending a-token/debt-token investigation ([[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]) verified
  correctness at exactly one layer: can instruments-service/MTDS's adapters actually fetch/ enumerate real data from the
  venue/protocol's own API or on-chain source. Operator flagged (2026-07-08, using AAVE_V3 as the concrete example): we
  have not verified whether these same findings are consistently visible at the other two layers a real user/operator
  actually looks at — (1) the raw GCS parquet files themselves (column names, instrument_id values physically written to
  disk), (2) the manifest (`availability_index.parquet` / `expected_universe_ranges.parquet` — what
  `/codex/02-data/honest-coverage-model.md`'s Layer-1/Layer-2 model actually audits), and (3)
  deployment-ui/deployment-api (the actual UI surface this whole multi-week effort exists to fix). A bug could be fixed
  at the adapter level and still show wrong in the UI if the manifest or deployment-api has its own independent bug
  (stale cache, hardcoded instrument_type allowlist that does not know about A_TOKEN/DEBT_TOKEN yet, wrong query, etc) —
  or a bug could look fixed in a spot-check of raw GCS data while the manifest never gets updated to reflect it. This
  doc documents the gap; per the operator, actually closing it is staged work, not a single pass."
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, deployment-api, deployment-ui, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    gcs,
    manifest,
    deployment-ui,
    deployment-api,
    honest-coverage,
    data-pipeline-correctness,
    verification-gap,
  ]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    /plans/archive/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    /plans/archive/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-08
author: unknown
parent_epic: instruments_master
priority: P1
source:
  'Operator, 2026-07-08: "for all the issues for example aave_v3 are we reconciling at gcs data level (the parquets
  themselves) the manifest level and the deployment ui/api level? because we should" + "we should document that at
  least, fixing will be in stages ofc."'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
last_updated: 2026-08-21
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
context_scope: [/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md, /codex/02-data/honest-coverage-model.md, deployment-api/deployment_api/services/data_status/breakdowns_core.py, deployment-api/deployment_api/routes/data_status/_distinct_values.py, unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py]
---

> **Verification-gap finding, not a confirmed bug — the whole point is we don't yet know.** Every finding in the two
> cross-referenced docs was verified at the adapter/live-fetch layer only. This doc's job is to name the gap precisely
> and stage the work to close it, not to claim any specific 3-layer mismatch exists yet (though given the volume and
> severity of what the adapter-layer audit found, it would be surprising if none did).

## The three layers, precisely

1. **GCS parquet level** — the actual bytes on disk: column names, the literal `instrument_id`/`instrument_type` string
   values written into each row, partition path shape. This is what
   `instruments-store-{ag}-prd-.../prod/catalog.parquet` and `market-data-tick-{ag}-prd-.../raw_tick_data/...`
   physically contain. This IS what the smoke test and lending investigation read directly (via `get_storage_client()` +
   `download_bytes` + `pandas.read_parquet`) — this layer is well-covered by this session's work.
2. **Manifest level** — `availability_index.parquet` / `expected_universe_ranges.parquet`, the Honest-Coverage-v2
   tracking layer (`/codex/02-data/honest-coverage-model.md`) that derives `capture_status` (captured / empty_confirmed
   / expected_unattempted / attempted_failed) per `(venue, instrument_type, data_type, day)`. This layer is built FROM
   the GCS writes but is a separate artifact that can drift from what's actually on disk (already confirmed possible
   this session — the HYPERLIQUID phantom-audit false-negative found earlier flags exactly this kind of manifest/reality
   mismatch, just in the opposite direction: manifest said phantom, GCS had the real file). **Not checked this session**
   for any of the 59 adapter-layer findings.
3. **deployment-ui / deployment-api level** — the actual coverage.json v2 response
   (`/codex/06-coding-standards/data-status-endpoint-contract.md`) and what deployment-ui renders from it. This is what
   an operator actually looks at day to day, and it's the layer this whole multi-week instrument-completion effort
   exists to make trustworthy. **Not checked this session at all** — no deployment-api endpoint was hit, no
   deployment-ui page was loaded, for any of the 59 findings.

## Why this matters (concrete, using the operator's own example)

Take AAVE_V3's `instrument_type` mislabel (real catalogue already splits A_TOKEN/DEBT_TOKEN correctly at the KEY level,
but the stored `instrument_type` FIELD says `LENDING` for both). Three independent questions, none yet answered:

- Does deployment-api's coverage computation key off the stored `instrument_type` FIELD, or off the instrument_id KEY's
  embedded type segment? If the field, deployment-api is currently showing AAVE_V3 as 100% `LENDING`-typed with zero
  A_TOKEN/DEBT_TOKEN breakdown, even though the real position-level split already exists in the data — a real
  under-representation the operator can't see today.
- Once the field gets fixed (per the queued P1 todo in [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]),
  does the manifest's own `expected_universe_ranges.parquet` get regenerated with the new type split, or does it need an
  explicit re-enumeration run? If the latter, the fix could ship in instruments-service and STILL not show up in
  deployment-ui until a separate manifest-rebuild step runs.
- Does deployment-ui have any hardcoded `instrument_type` allowlist/enum (a TypeScript union type, a filter dropdown's
  option list, a color-coding switch statement) that would need its OWN update to even display an `A_TOKEN`/`DEBT_TOKEN`
  row correctly, versus silently dropping or mis-rendering it?

Multiply this by all 59 findings in the smoke-test doc (margin-type mislabels on OKX/BYBIT/KRAKEN-FUTURES, the DERIBIT
live-vs-batch misclassification, HUOBI/BITSTAMP missing-from-venue-universe, ETHENA's fabricated prices, GMX's synthetic
funding, etc) — each one has this same 3-layer question open.

## What this is NOT

- Not a claim that deployment-api/deployment-ui are definitely broken — they may already correctly key off instrument_id
  rather than the (buggy) `instrument_type` field, in which case several of these findings might already be invisible to
  the operator in exactly the right way (correctly hidden) or exactly the wrong way (correctly hidden bugs that should
  be surfaced as gaps). Genuinely unknown until checked.
- Not asking to re-verify all 59 findings' adapter-layer correctness — that work is done and stands.
- Not a request to fix anything yet — per the operator, this is staged: document now, reconcile in stages later,
  starting with whichever findings turn out to matter most once the first few real traces are done.

## Related finding: `canonical_id_builder.py` is a dead/aspirational SSOT, not what production actually writes

Folded in here 2026-07-08 (operator: "i dont care you pick") rather than a separate doc — same shape as the rest of this
doc (a declared SSOT disagreeing with what's actually captured), just at the instrument_id-format layer instead of the
instrument_type-field layer.

`unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py` is documented as "the single
dispatch point for financial instrument IDs" — but grepping the whole workspace for real callers of
`build_instrument_id()` found exactly one, in Polymarket's parsing module. Every CeFi venue (Binance, Kraken, Bybit,
Deribit, the 5 on-chain-perp venues) builds its `instrument_id` some other way, per-adapter, with no shared
canonicalization step. Confirmed via direct reads of `prod/catalog.parquet` (both `cefi` and `defi` asset groups,
2026-07-08):

- The module's own DERIBIT/OPTION docstring example (`BTC-USD-inverse-20261226-65000-C`, quote_asset+margin_type
  embedded in the ID) does not match real Deribit data at all — real IDs are `DERIBIT:OPTION:BTC-10APR20-4750-C`
  (Deribit's own native format), with `margin_type` stored as a separate column, never embedded in the key.
- `PERPETUAL` gets a real, working base-quote dash normalization (`BYBIT:PERPETUAL:10000000AIDOGE-USDT`,
  `BINANCE-FUTURES:PERPETUAL:BTC-USDT`) — but dated `FUTURE` on the exact same venues does NOT
  (`BINANCE-FUTURES:FUTURE:BTCUSDT_260925`, raw-concatenated + underscore-date;
  `KRAKEN-FUTURES:FUTURE:FF_XBTUSD_260731`, Kraken's raw uncleaned prefix passed straight through). Two different real
  code paths for two instrument_types on the same venue, not one shared builder.
- Every DEX-pool protocol (Uniswap, Balancer, Curve, PancakeSwap, Sushiswap, Camelot, Aerodrome, TraderJoe, Velodrome,
  GMX — 6,180 real rows, zero exceptions) stores `instrument_id` as the bare on-chain pool address, with NO
  `VENUE:TYPE:SYMBOL` structure at all — venue/chain/base_asset live in separate columns instead.
- The 5 on-chain-perp venues (HYPERLIQUID/ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC) all store
  `instrument_type="PERPETUAL"` as the field but embed `PERP` (not `PERPETUAL`) in the instrument_id key — consistent
  across all 5, but disagreeing with the field and with CeFi's own `PERPETUAL`-in-key convention.
- Base-quote normalization is inconsistent even within that same 5-venue cluster: HYPERLIQUID/LIGHTER-ZKSYNC use a bare
  symbol (no quote suffix), ASTER uses the raw concatenated exchange symbol (no dash), PACIFICA-SOLANA's quote segment
  is literally the string `PERP` (not a currency), and EXTENDED-STARKNET is the only one that's actually dash-cleaned
  with a real currency (`ETH-USD`).
- AAVE_V3-OPTIMISM has a second, misspelled venue-token duplicate (`AAVEV3-OPTIMISM`, missing the underscore) carrying 4
  real rows invisible to anything querying the correctly-spelled prefix — a live example of what happens with no shared,
  enforced ID-construction path. **✅ FIXED — 2026-07-12 correction** (was: no fix note; this bullet read as still
  live): retired the same session by a concurrent sibling agent (DeFi venue-token naming cleanup), confirmed via a fresh
  re-query of `prod/catalog.parquet` — 0 ghost rows, 16 rows correctly under `AAVE_V3-OPTIMISM`. See
  `/plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md`'s corresponding todo (checked `[x]`,
  flagged there as "stale by the time this plan was filed — the parallel work wasn't visible to the agent that wrote
  it"). Finding #127, plan-reconciliation
  `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling.

**Net**: `canonical_id_builder.py` reads as the intended SSOT but isn't reachable from almost anywhere real capture
happens — it's aspirational documentation of a convention the codebase mostly doesn't follow, not a live invariant. Real
instrument_id shape varies by adapter, sometimes by instrument_type within the same adapter, with no single place that
would catch a new inconsistency. This is a genuine, unstaffed migration-scoping question for whenever the operator wants
to pursue actual ID canonicalization — not something to fix inside this doc.

## Todos

- [x] [VERIFY] P1. **Trace AAVE_V3 end-to-end as the pilot case** (operator's own example) — for a single real reserve
      (e.g. `AAVE_V3-ARBITRUM:A_TOKEN:AAAVE`), confirm what deployment-api's `/data-status` (or equivalent coverage.json
      v2) endpoint actually returns for this instrument today, and whether deployment-ui renders it distinctly from its
      `DEBT_TOKEN` counterpart or collapses both under a generic `LENDING` bucket. This single trace answers whether the
      `instrument_type` field mislabel is cosmetic (key already correct, UI doesn't care) or a real UI-visible gap. —
      **DONE 2026-07-08.** Answer: visible, not cosmetic, but not broken/blank either — it collapses.
      `GET /instruments-for-shard` (`deployment-api/deployment_api/routes/data_status/_query_meta.py:305-374`) and
      `_build_instrument_type_breakdown` (`deployment_api/services/data_status/breakdowns_core.py:385,391`) group
      directly on the raw `instrument_type` manifest column — never parse the `instrument_id` key. Read
      `gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet` directly (214,726
      rows): AAVE_V3 rows independently carry the same `instrument_type="LENDING"` mislabel the GCS catalog has — the
      manifest doesn't disagree, it corroborates, just at coarser (per-venue/chain/date sentinel) grain with
      `instrument_id=""`. deployment-ui has no hardcoded `instrument_type` TS union/enum (grepped clean); rows render
      via generic `Object.entries(...).map(...)`, color keyed off `completion_pct` not the type string — so today's
      visible effect is one merged "LENDING" accordion row instead of separate A_TOKEN/DEBT_TOKEN rows, and a user can't
      select A_TOKEN/DEBT_TOKEN from the UI since the breakdown never surfaces them as options. **Net:
      deployment-api/deployment-ui need no code change** — the fix is entirely in instruments-service's manifest-writer
      (the code stamping `"LENDING"` into both `catalog.parquet` and the sentinel rows), plus a decision on whether the
      manifest needs new per-A_TOKEN/DEBT_TOKEN sentinel rows so the UI grid can actually split them post-fix (today it
      structurally can't, even after the field is corrected). One gap: could not confirm the per-row `instrument_type`
      inside the daily bundle `instrument_availability/by_date/.../instruments.parquet` (GCS reads timed out under this
      pass's budget) — flagged, not assumed to match.
- [x] ✅ [VERIFY] P1. **DONE 2026-07-29 — verdict: AUTOMATIC on both axes, no manual trigger needed.** **Check whether
      manifest regeneration is automatic or requires an explicit re-enumeration trigger** when an instruments-service
      adapter's stamped `instrument_type` changes. Two separate artifacts, both confirmed standing-cron-driven
      (`/codex/05-infrastructure/manifest-consolidator-ssot.md` + `deployment-service/terraform/gcp/*.tf`): (1)
      **`availability_index.parquet`** (captured-data manifest) — consolidated by a standing `*/1 * * * *` Cloud
      Scheduler cron (`manifest_consolidator_scheduler.tf`) that merges per-VM shards into the canonical manifest
      continuously; a new adapter write with a changed `instrument_type` shows up within ~1 minute of the next capture
      run, no manual step. (2) **`expected_universe_ranges.parquet`** (expected-universe enumeration) — regenerated by a
      standing DAILY cron (`expected_universe_v2_scheduler.tf`, `schedule = "30 1 * * *"` UTC). **So the "fix shipped
      but nothing looks different for N days" trap does NOT apply** — captured-data changes reflect in ~1 minute,
      expected-universe-derived numbers (denominators, expected cells) refresh within ≤24h automatically. No flag needed
      in future fixes' rollout plans beyond noting the ≤24h expected-universe lag if a fix specifically depends on that
      artifact.
- [x] [VERIFY] P2. **CORRECTED 2026-08-16 (plan_reconciler, tranche=tradfi, agt-a74a6a): the pointer below to an
      archived doc is misleading — the full execution write-up (Findings A/B/C) is actually IN THIS DOC's own Progress
      Log (2026-07-31/08-01 entries below), which is more complete than the archived doc.** **Spot-check 2-3 more
      findings from the smoke-test doc across all 3 layers** — good candidates: the
      DERIBIT live-vs-batch FUTURE misclassification (does deployment-ui show a FUTURE count that matches the real GCS
      row count, or does the live-WS mislabel bleed into the manifest?), and HUOBI-SPOT's missing-from-venue-universe
      gap (does deployment-ui even have a HUOBI-SPOT row to look wrong, or does the venue not appear in the UI's venue
      list at all — a different, more visible kind of gap).
- [x] [VERIFY] P2. **Check deployment-ui for hardcoded `instrument_type` allowlists/unions** (TypeScript types, filter
      dropdowns, color-coding switches) that would need their own update once A_TOKEN/ DEBT_TOKEN (and other
      target-state types from the canonicalization decision) start appearing in real data — a silently-broken or
      silently-dropped row is worse than a visibly-wrong one. — **DONE 2026-07-08, folded into the AAVE_V3 trace
      above.** Confirmed negative: no hardcoded TS union/enum for `instrument_type` anywhere in deployment-ui.
      `DataStatusDrilldown.tsx:85` types it opaque (`string`); `DataStatusTab.tsx:4817` / `VenueDetailPanel.tsx:182`
      both render via generic `Object.entries(...).map(...)`. An unrecognized value would print as literal text, not go
      blank or break — so this specific risk (silently-dropped row) is not live.
- [ ] [DATA] P2. Per D31 ruling (ADOPTED-REC 2026-08-21: "Spot-check — 2 of 3 spot-checked failures were structural
      manifest non-instrumentation a trace can't fix"): the reconciliation-cadence decision is now RESOLVED as
      spot-check, not full-trace. Continue spot-checking the remaining findings across the 3 layers (GCS/manifest/
      deployment-ui), reusing the 2026-07-31/08-01 Finding-A/B/C methodology — re-derive the live remaining-findings
      count from `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` directly first (its own bug list now shows
      the majority `[x]` FIXED with shipped commit SHAs; do not trust the stale restated "58"). Done-when: every
      still-unverified finding in that doc has a per-layer spot-check verdict recorded in this doc's Progress Log.
- [x] [DECISION] P2. **Scope whether/when to pursue real `instrument_id` canonicalization** — **DECIDED 2026-07-08**:
      operator chose to canonicalize, full scope, rather than leave unscoped. Moved to its own doc —
      [[instrument_id_format_canonicalization_2026_07_08]] — since it grew into a 6-finding enumeration with real target
      formats, not a one-line scoping question anymore.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole open todo is an explicit [DECISION] on reconciliation
  cadence (full trace vs lighter spot-check) for 58 findings

- **2026-07-08** — Filed after the operator asked, while reviewing the drilldown mockup's AAVE_V3 entry, whether this
  session's adapter-level findings have been reconciled against the manifest and deployment-ui/API layers too.
  Confirmed: no, they have not — this session's verification (the full adapter smoke test + the lending investigation)
  only ever checked the GCS/adapter layer. Operator explicitly wants this documented now with staged fixing to follow,
  not a single pass today. No investigation done yet beyond naming the gap and proposing AAVE_V3 as the pilot trace.
- **2026-07-08 (later same day)** — Pilot trace + hardcoded-allowlist check both completed (read-only, background
  agent). Result: the 3 layers are consistent with each other (GCS catalog, manifest, and deployment-ui/API all show the
  same `LENDING` mislabel — no independent drift found between them for this finding), and deployment-api/UI need no
  code change since both key genuinely generically off the stored `instrument_type` string. Net visible effect today:
  instruments-service/AAVE_V3's coverage grid shows one merged "LENDING" row instead of separate A_TOKEN/DEBT_TOKEN
  rows, and a user can't filter by A_TOKEN/DEBT_TOKEN in the UI since the manifest has no row grain fine enough to
  support it — a real scope decision to make alongside the field-label fix
  ([[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]), not just a cosmetic label change. Remaining P2 todos
  (spot-check 2-3 more findings; reconciliation-cadence decision) still open.
- **2026-07-08 (later still)** — While backfilling real instrument_id samples into the instruments-definitions mockup
  (per-leaf completeness pass), found and folded in the `canonical_id_builder.py` dead-code/aspirational-drift finding
  (see new section above) — operator explicitly deferred the separate-doc-vs-fold-in choice ("i dont care you pick").
  Confirmed via direct real-catalog reads: the module has exactly one real caller workspace-wide (Polymarket parsing);
  every other venue builds its instrument_id ad hoc, producing several concrete inconsistencies (DEX-pool bare addresses
  with zero canonical structure across 6,180 rows/13 protocols; PERP-vs-PERPETUAL key/field mismatch across all 5
  on-chain-perp venues; PERPETUAL-gets-cleaned-but-FUTURE-doesn't on the same CeFi venue; an AAVE_V3-OPTIMISM
  misspelled-venue-token duplicate fragmenting 4 real rows). New P2 decision todo added; not actioned, just scoped.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole open todo is an explicit
  `[DECISION]` on reconciliation cadence across 58 remaining findings.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole open todo is tagged `[DECISION]` and
  is one — 'decide the reconciliation cadence for the remaining 58 findings: full trace per finding (expensive,
  thorough) vs a lighter spot-check pattern' — a portfolio-cost tradeoff, not a determinable fact, even though its
  AAVE_V3 pilot prerequisite is now `[x]`

- **2026-07-31/08-01 (data_engineering slot-13, `cefi_misc_audits_and_hygiene-002`)**: spot-checked the next 3
  unverified findings from the smoke-test doc's 59-item list across all 3 layers, reusing the AAVE_V3 pilot's
  methodology (direct GCS/manifest parquet reads via `get_storage_client()`/`resolve_bucket_name()`, plus a
  deployment-api/deployment-ui code grep for how each field is actually surfaced). All 3 reads were live-production,
  read-only (no writes, no code changed).

  **Finding A — DERIBIT live-vs-batch FUTURE misclassification** (`deribit_ws.py:100`, P0). GCS/adapter layer already
  established by the smoke test (not re-verified). **Manifest layer: FAIL to surface — structurally blind, not
  corroborating or refuting.** Read `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`
  (9,658,011 rows): DERIBIT has 419,457 rows; `pipeline_mode=live_deribit` rows exist ONLY for
  `data_type=derivative_ticker` (148 FUTURE rows, 3,360 OPTION rows, 100% `capture_status=expected_unattempted` — never
  actually captured) — **zero `live_deribit` + `data_type=trades` rows exist for ANY instrument_type.** The manifest
  simply does not instrument live trade captures at the granularity this bug lives at, so it cannot show the mislabeling
  either way. **deployment-api/UI layer: also FAIL to surface, for the same root reason.**
  `deployment_api/routes/data_status/_deploy_turbo.py` supports `pipeline_mode` filtering (a v9 provenance axis) and
  `_live_coverage.py` has a dedicated `_is_live_mode()` live-prefix helper, so an operator COULD filter by
  `pipeline_mode=live_deribit` — but given the manifest gap above, any such query returns the same
  empty/`expected_unattempted`-only picture. **Net: this is a worse gap than AAVE_V3's** — there, the wrong value was at
  least consistently visible everywhere; here, the entire live-trade-classification path is a manifest blind spot,
  independent of whether the underlying classification bug is real.

  **Finding B — HUOBI-SPOT / HUOBI-FUTURES / BITSTAMP-SPOT missing from venue universe** (`market_data_categories.py`
  `VENUES_BY_ASSET_GROUP["cefi"]`, P0). **GCS layer: FAIL (confirmed absent) — corroborates.** 0 rows for all 3 venues
  in `instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet` (430,290 total rows). **Manifest layer:
  FAIL (confirmed absent) — corroborates.** 0 rows for all 3 venues in both the instruments-store manifest (84,615 rows)
  and the MTDS manifest (9,658,011 rows). **deployment-api/UI layer: FAIL, and a WORSE kind of fail than a visible
  zero-row.** `deployment_api/routes/data_status/_distinct_values.py:315` derives the expected venue set directly from
  `VENUES_BY_ASSET_GROUP[asset_group]` — the exact same UAC registry the finding names as the root cause. Since
  deployment-ui's venue-driven views (dropdowns, per-venue grid rows) are built from this same registry, the 3 venues
  **don't appear in the UI at all** — not a 0%-coverage row an operator could notice, a venue that silently doesn't
  exist in the picker. **Net: consistent 3-layer absence, and the UI's failure mode is the invisible kind, not the
  visible-but-wrong kind.**

  **Finding C — OKX margin_type inversion** (`tardis/parsing.py:388-427`, P0, real P&L-relevant per the finding's own
  framing — same bug class as the AAVE_V3 lending mislabel). **GCS layer: field populated, consistent with the finding's
  premise.** Catalog confirms real rows both ways (OKX-FUTURES: linear=2,895/inverse=2,592; OKX-SWAP:
  linear=607/inverse=46) — the field exists and varies, so if the finding's "inverted" claim is correct, a real user
  reading the catalog directly (e.g. strategy code) would see the wrong value. **Manifest layer: FAIL to surface —
  different shape of gap than Finding A.** All 7,718 OKX manifest rows (FUTURES=5,036, SWAP=2,682) carry a
  **blank/unpopulated `margin_type`** — the schema has the column, but nothing stamps it for OKX captures, so the
  manifest can't corroborate OR refute the inversion (distinct from AAVE_V3, where the manifest DID corroborate the same
  wrong value). **deployment-api/UI layer: FAIL — zero references to `margin_type` anywhere.** Grepped both
  `deployment-api` and `deployment-ui` end to end: no route, service, or component reads or renders `margin_type` today.
  **Net: the bug is real and GCS-verified, but has zero blast radius on the operator-facing coverage UI as it stands** —
  lower operator-visible urgency than the P0 tag implies for THIS specific surface, though the underlying P&L risk for
  any code reading the catalog field directly is unaffected by that.

  **Consolidated verdict across all 3**: none of the 3 findings are correctly reconciled end-to-end — every one FAILs at
  least one layer, and 2 of the 3 (A, B) fail ALL three layers in a way where the manifest/UI gap is not merely "shows
  the same wrong thing" (like AAVE_V3) but "cannot show anything at all" (a different, arguably more urgent class of gap
  — an operator has zero signal, not a misleading signal). No code changed this touch (read-only spot check, per this
  todo's own scope). The `[DECISION]` P2 reconciliation-cadence todo below remains open/human — these 3 results (2 of 3
  being "manifest doesn't even track this" rather than "manifest shows a fixable wrong value") should inform that
  cadence call: a full trace won't help findings where the gap is structural non-instrumentation, those need a
  manifest/schema fix before any per-finding trace would be meaningful.
- **na-eligibility-audit 2026-08-16** [body-hash:e6e02f855277b1dd]: KEEP-NA, valid — Read the doc in full end-to-end (243+ lines of body, all 6 todos, both Progress Log sections).

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid. Sole open todo is the `[DECISION] P2`
  reconciliation-cadence call — a genuine portfolio-cost tradeoff across 58 findings, not a determinable fact.
  `cefi_consolidated_native_ao_extract_2026_07_25.md` (active/planning) already reviewed and explicitly excluded this
  exact item as an undecided policy question. No reclassification.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- dropped 2 archived plan links, added 3 real
  source-code targets (breakdowns_core.py, _distinct_values.py, canonical_id_builder.py) the doc's own findings name.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-01 verdict.
  Sole open todo ([DECISION] P2) remains a portfolio-cost tradeoff (reconciliation cadence for the remaining 58
  findings: full trace vs lighter spot-check) with no autonomous-determinable answer; content unchanged besides
  context-scout refreshes.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid - reaffirms the 2026-08-07 verdict.
  Checked all 9 of today's generalizable rulings (IAM self-service, D16 all-repos, S5.1 tiered required-docs,
  context_scope/plan-destination default, escalation-N default, reversibility-qualified deletes, Option B retirement,
  AWS lower-stakes, script/tooling sibling-precedent self-service) against the sole open todo — none apply; it is still
  a genuine full-trace-vs-spot-check portfolio-cost tradeoff across 58 findings, not a fact/scope a worker can resolve
  alone.
  [`cefi_satellite_ao_dispatch_batch9_2026_08_07.md`](/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch9_2026_08_07.md)/`batch10_2026_08_08.md`
  (both active, `assigned_vm: planning`, most recent full-corpus cefi re-audits) do not reference this doc at all — no
  conflict, no coverage either way. No reclassification.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole open item is an explicit
  portfolio-cost tradeoff decision (reconciliation cadence for 58 findings: full-trace vs spot-check), not a
  determinable fact. Reaffirmed by 6 prior independent passes.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-18** [body-hash:90c21f8593395adb]: KEEP-NA, valid — reaffirmed (8th pass). Sole open todo
  ([DECISION] P2, reconciliation cadence across the smoke-test findings) remains a portfolio-cost tradeoff, not a
  determinable fact; a same-day plan_reconciler correction to the todo's own stale "58 findings" count doesn't change
  that. No reclassification.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-21 — ruling D31 (Smoke-test findings reconcile depth)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Spot-check — 2 of 3 spot-checked failures were structural manifest
  non-instrumentation a trace can't fix. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
