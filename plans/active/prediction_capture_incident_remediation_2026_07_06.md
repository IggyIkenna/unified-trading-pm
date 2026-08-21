---
doc_type: plan
title:
  Prediction-capture incident remediation — capture-path dtype hardening + KALSHI/POLYMARKET-PERP adapter correction
summary:
  "Actionable remediation for the 2026-07-01→07-06 prediction-universe-capture outage (diagnosis + root-cause evidence:
  issue doc prediction_universe_capture_dead_since_07_01_2026_07_06). Two workstreams: (A) harden the capture path — UTL
  write-side dtype coercion shipped; residuals = fix the manifest consolidator's utf8 typing at source, audit sports for
  the same double-consolidator race, get the fixed UTL into the is-daily-enum image, backfill the missed window, add
  observability. (B) correct the KALSHI-PERP/POLYMARKET-PERP adapters — they query the WRONG Kalshi host (events, not
  the auth'd margin/perps API) and emit the entire binary event universe as fake PERPETUAL, contaminating cefi with
  25,473 rows. Demo-first repoint (config-drive host + shared RSA-PSS auth + margin API parse); prod cutover gated on
  Ikenna's perps member-rollout access answer."
status: active
nature: design
asset_group: [prediction, cefi]
stage: [data]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [
    manifest,
    consolidator,
    prediction,
    capture,
    dtype,
    arrow,
    adapter,
    kalshi,
    polymarket,
    perpetual,
    cefi,
    contamination,
    remediation,
    observability,
  ]
related: []
  # STALE-REF FIX (plan_reconciler, cefi tranche, agt-2e82f7, 2026-08-16): first 2 entries repointed to their
  # archived location (both moved, targets confirmed existing there). A 4th entry,
  # `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`, was removed — confirmed genuinely
  # dangling (not found anywhere in plans/active/ or plans/archive/ after a fresh corpus-wide search).
  # 2026-08-19 (na-eligibility-audit): all 3 remaining entries were themselves archived-plan citations, dropped to
  # satisfy the archive-safety-ratchet gate (active docs must not cite /plans/archive/... in `related:`) — all 3
  # remain preserved as inline body citations (the top blockquote cites the issue doc verbatim; the
  # is_daily_enum handoff is cited twice in Workstream A's own text). No discoverability lost.
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
last_updated: 2026-07-30 # (was: 2026-07-14 -- plan-reconcile 2026-08-15: body Progress Log entries through 2026-07-30 postdated the recorded last_updated, same staleness class as the 2026-07-14 correction)
locked_by:
locked_since:
depends_on: []
supersedes: []
superseded_by:
source:
  [
    operator-directed remediation 2026-07-06 (Ikenna — "don't remove the PERP venues,
    correct them; build against demo"),
    is-daily-enum-prediction daily-failure investigation 2026-07-06,
  ]
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    instruments-service/instruments_service/engine/orchestrator/prediction.py,
  ]
---

# Prediction-capture incident remediation

> **This plan tracks the ACTIONABLE remediation only. The diagnosis, root-cause evidence (live Kalshi API probe,
> contamination timeline, why-nothing-alerted), the demo→prod switch-cost analysis, and the operator-decision context
> are the RECORD and live in the issue doc — this plan references them, it does not duplicate them:**
> [`/plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`](/plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md).

## Codex SSOTs (read before touching the relevant workstream; post-phase audit updates them)

- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the consolidator that string-typed the canonical index
  (Workstream A dtype-at-source fix).
- `/codex/02-data/availability-manifest-and-data-status.md` — ManifestRow schema (`instrument_count` is `int`); the
  write-side coercion contract.
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` +
  `/codex/04-architecture/shard-level-failure-isolation.md` — reference-data adapter + per-shard-isolation contract
  (Workstream B adapter rewrite; the shard-isolation catch that swallowed the crash without `exc_info`).
- `/codex/06-coding-standards/config-reloader-pattern.md` — typed config for the `KALSHI_PERP_ENV` host resolver.
- Kalshi/Polymarket perps margin API: **no codex doc yet** — the issue doc is the reference until Phase 2/3 stub one.

## Scope — two workstreams from one incident

- **Workstream A — capture-path dtype hardening** (root cause #1: consolidator utf8-typed the canonical
  `_index/availability_index.parquet` → UTL merge `ArrowTypeError` → `is-daily-enum-prediction` died daily 07-01→07-06).
  The crash-proof UTL coercion is SHIPPED; residuals harden the source + close the missed window.
- **Workstream B — KALSHI-PERP / POLYMARKET-PERP adapter correction** (root cause #2, unmasked once A stopped the
  crash): the perp adapters query the **wrong Kalshi host** (events, not the auth'd margin/perps API) and emit the whole
  binary event universe as fake `PERPETUAL`, contaminating cefi with **25,473 rows**. Operator: KEEP the venues, correct
  the adapters. Demo-first; prod cutover gated on access.

Both workstreams are `data-pipeline-engineer`, one owning agent (this session), `local-only` (not
orchestrator-dispatched).

---

## Workstream A — capture-path dtype hardening

### Shipped 2026-07-06 (record — verified green)

- [x] [CODE] P0. ✅ UTL write-side schema coercion in `_merge_dataframes`:
      `instrument_count`/`schema_version`/`row_count` → nullable `Int64`, then bool (`expected`/`available`) →
      `boolean` + `expected_window_completeness_fraction` → `Float64` before every index/shard write — a dtype-divergent
      co-writer can never crash the capture path again. — unified-trading-library@6c090bb (Int64) + @1651340
      (bool/float). Gate: verified against the exact poisoned prod frame (24,994-row merge + `to_parquet` OK).
- [x] [INFRA] P1. ✅ Paused `uts-prod-manifest-consolidator-instruments-prediction-legacy-cron` — prediction ran BOTH
      legacy + non-legacy consolidators every minute (racing co-writers on one file; other AGs paused legacy 06-08).
      (Reversible: `gcloud scheduler jobs resume …`.) Gate: legacy cron shows `state: PAUSED`.
- [x] [CODE] P1. ✅ Catalogue feed-health clamp — `_warn_coverage_horizon` ignores future-dated (settlement) `day=`
      partitions so `CATALOGUE_STALE_BY_DATE` is not blinded by prediction's out-to-2029 dirs, + regression test. —
      instruments-service@4979429.
- [x] [VERIFY] P0. ✅ Local healing run of the exact capture command on the fixed UTL → green exit + today's prediction
      universe restored (index advanced to 07-06 with Int64 types). Gate: capture exit 0 + `max(available_from)` moved
      past 06-27.

### Residual open work

> **Scope note (2026-07-06):** Workstream A is **capture-hardening (root-cause-#1)** — NOT the KALSHI/POLYMARKET-PERP
> correction the slot-2 agent was assigned (Workstream B). These residuals (consolidator dtype-at-source, the
> is-daily-enum heal, missed-window backfill, exc_info) belong to the **capture-hardening owner**; the slot-2 agent is
> NOT executing them further. The unresolved heal is handed off in
> [`issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`](issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md).

- [x] [INFRA] P1. ✅ Audited **sports** (2026-07-06) — SAME condition, confirmed WORSE than prediction:
      `instruments-sports-cron` AND `instruments-sports-legacy-cron` were BOTH enabled (`*/1`); the sports instruments
      availability index is string-poisoned (`instrument_count`/`row_count`/`expected`/`available` all object/str,
      4,999,446 rows); and `is-daily-enum-sports` has FAILED every day 06-28→07-05 (failed_count=1) — sports instruments
      capture has been DEAD longer than prediction, previously undetected. Paused
      `uts-prod-manifest-consolidator-instruments-sports-legacy-cron` (now matches every other AG; reversible via
      `gcloud scheduler jobs resume`). The heal folds into the item below.
- [x] [DOCS] P0. ✅ **SPLIT OUT into AO-ready plans (2026-07-07)** — per operator direction, the 3 remaining residuals
      (consolidator dtype-at-source, the is-daily-enum heal, missed-window backfill, exc_info observability) were carved
      into 2 small AO-DISPATCHED plans, born `status: draft` (not ingested until flipped `active` — operator is updating
      the AO code first): - [`is_daily_enum_capture_heal_2026_07_07.md`](is_daily_enum_capture_heal_2026_07_07.md) —
      exc_info fix → redeploy → real diagnosis → fix → backfill (one sequential thread; the heal + backfill +
      observability items below all folded in here). -
      [`manifest_consolidator_dtype_at_source_fix_2026_07_07.md`](/plans/archive/2026_07/manifest_consolidator_dtype_at_source_fix_2026_07_07.md)
      — the consolidator dtype fix, independent (different repo — `market-tick-data-service` — parallel with the above).
      These supersede the 3 residual todos previously listed here; do not re-add them to this plan.

---

## Workstream B — KALSHI-PERP / POLYMARKET-PERP adapter correction (demo-first; prod gated on access)

> **Root cause (issue doc, confirmed via live probe):** `kalshi_perp` queries
> `https://api.elections.kalshi.com/trade-api/v2/markets` — the **events** host, 100% binary contracts, 0 perps. Real
> perps live on the auth'd margin host `https://external-api.kalshi.com/trade-api/v2/margin/` (demo
> `external-api.demo.kalshi.co`). The `category=Crypto` filter is ignored + the empty-category client filter passes →
> the whole binary event universe is emitted as fake `PERPETUAL`. **Confirmed demo endpoint:**
> `GET …/trade-api/v2/markets/margin` → `MarginMarket[]`. **Purge scope:** KALSHI-PERP 25,473 rows; POLYMARKET-PERP 0.
> All 0 MVP-tagged.
>
> **Coordination:** this touches instruments-service@4da6fe8 (another workstream's feature that enabled the PERP
> venues). Slot-2 executes Phases 0–3 + 5 and flags the 4da6fe8 author on the PR; Phase 4 (prod cutover) waits on
> Ikenna's access answer. No UAC venue-list change — the venues stay declared.
>
> **New evidence (2026-07-07, live probe, updates the Phase 1/4 auth assumption)**: a fresh, unauthenticated read-only
> `GET` against the **prod** margin host `https://external-api.kalshi.com/trade-api/v2/margin/markets` (not the demo
> host) returned **HTTP 200 with no auth headers sent** — 16 real crypto perp tickers
> (`KXBTCPERP`/`KXETHPERP`/`KXSOLPERP`/... ). `.../margin/markets/KXBTCPERP/orderbook` and
> `.../margin/trades?ticker=KXBTCPERP` also returned 200, real live depth and trades timestamped seconds before the
> probe. This contradicts the assumption baked into Phase 1/4 that the margin API needs RSA-PSS auth "rolling out member
> by member" — **market-data reads (listing/detail/orderbook/trades) appear to be public on prod right now, no
> enrollment or credentials required.** Order-placement endpoints were NOT tested (not needed for market data) and may
> still require auth/enrollment — this finding is about reads only. If confirmed, Phase 1's RSA-PSS extraction may only
> be needed for POLYMARKET-PERP (not yet probed) or for a future order-execution path, and Phase 4's
> `BLOCKED-OPERATOR-DECISION` may not gate the market-data repoint at all — re-verify with a second independent probe
> before removing the auth path from Phase 1/2, since one probe could be catching a temporarily-open endpoint or a
> Kalshi-side auth rollout gap.

### Phase 0 — stop contamination + purge (NOW, no access needed) — SEQUENTIAL (guard ships before purge)

- [x] [CODE] P0. ✅ Guard both `kalshi_perp` + `polymarket_perp` adapters to emit **0 records** from the current (wrong,
      events) host until repointed — `_REPOINT_PENDING=True`; `get_instruments()`/`get_instrument()` return honest-empty
      BEFORE any network call + fixed the `kalshi _parse_market` empty-category "pass" bug (defense-in-depth). Venue
      declarations STAY. — instruments-service@c8c6dac76 | QG green (4000 pass, coverage ≥88%); tests assert 0 records
      from an events-host payload (`test_get_instruments_empty_even_with_events_host_payload`) + the events-host binary
      contract is rejected by the parser (`test_events_host_binary_market_is_rejected`); fetch-path coverage retained
      guard-lifted for the machinery Phase 2/3 reuses.
- [x] [INFRA] P0. ✅ Guard reached prod — cloud build `09a20bfe-4401-42cf-ae91-e832418550df` **SUCCESS** built
      `instruments-service:latest` = `sha256:e93483dd…` from `de3bcf5` (main w/ guard, promoted via the fleet promoter I
      dispatched); every `is-daily-enum-*` job resolves `:latest`.
      `Evidence: cloudbuild=09a20bfe-4401-42cf-ae91-e832418550df`. Runtime confirm (next cefi run writes 0
      `KALSHI-PERP`) = the post-purge catalogue staying clean through the 13:30 UTC run (folded into step 2's post-13:30
      check).
- [x] [DATA] P0. ✅ Purged the 25,473 fake `KALSHI-PERP` rows from cefi — deleted the 9 `venue=KALSHI-PERP` by_date
      snapshots (06-27→07-05) via `scripts/purge_kalshi_perp_events_contamination_2026_07_06.py --apply`, then
      `build_instrument_catalogue.py --asset-group cefi --mode full --allow-catalogue-shrink` (run
      `catalogue-rollup-cefi-20260706T110652Z`, monotonic guard ACCEPT shrink_overridden). **Verified against
      baseline:** catalogue 376,984→**351,511** rows (drop == **25,473**, exact), **KALSHI-PERP == 0**, 25→**24
      venues**, DERIBIT 331,803 + all other venues UNCHANGED. **PURGE, not MOVE (operator-decided 2026-07-06):** the
      perp parser stamped these binary EVENT contracts as `instrument_type=PERPETUAL`/`expiry=None`, discarding their
      expiry/series/YES-NO structure; they are reference-data rows (no captured prices), the correct producer is the
      prediction Kalshi adapter, and Kalshi is cheaply re-enumerable — moving would relocate degraded stubs + conflict
      with the prediction store's canonical copies. (The "are these captured correctly anywhere?" question is Phase 3's
      `[VERIFY]`.) Gate: cefi catalogue has 0 `KALSHI-PERP` rows; row-count drop == 25,473; no other venue touched. ✅
      MET.
- [x] [DATA] P1. ✅ Manifest cells: the cefi `_index/availability_index.parquet` self-healed — **VERIFIED 2026-07-10**
      (live read via `unified_trading_library.cloud_interface.factory.get_storage_client().download_bytes(...)` against
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 7,219,598 rows): **0
      `KALSHI-PERP` rows and 0 `POLYMARKET-PERP` rows** remain. The guarded `is-daily-enum-cefi` runs self-healed the 9
      lingering `captured` cells to honest-empty/absent as predicted. Gate MET — Phase 0 fully closed (all 4 todos now
      done).

> **🟡 2026-07-14 OPERATOR RULING: Kalshi/Polymarket perps are NOT part of MVP** — Polymarket perps are beta-gated and
> Kalshi requires member-rollout enrollment ("extra work"); there is nothing actionable until access exists. Phases 1–3
> perp-adapter repoint items + Phase 4 prod cutover are **DESCOPED/parked — do not dispatch**. Still ACTIVE (not
> perps-dependent): Phase 3's prediction event-capture-gap `[VERIFY]` and the Phase 5 write-time guardrail.

### Phase 1 — foundation: config-drive host + shared RSA-PSS auth (no access needed) — PARALLEL [DESCOPED-NOT-MVP 2026-07-14]

- [ ] [CODE] P1. Make the perp base URL config-driven — `KALSHI_PERP_ENV=demo|prod` (via `UnifiedCloudConfig`, default
      `demo`) resolving the host; delete the hardcoded `_KALSHI_BASE_URL` events-host const from the perp adapters.
      Gate: unit test resolves demo vs prod host from config.
- [ ] [CODE] P1. Extract the RSA-PSS signing that ALREADY EXISTS in `adapters/prediction/kalshi.py`
      (`_signed_headers`/`_parse_kalshi_creds`/`_can_sign`) into a shared helper both perp adapters use; wire the demo
      credential blob via the injection path (secret ref `kalshi-perp-demo`). Gate: signed-header unit test on the
      shared helper.

### Phase 2 — repoint kalshi_perp to the margin API (demo) — SEQUENTIAL after Phase 1 [DESCOPED-NOT-MVP 2026-07-14]

- [ ] [CODE] P1. Rewrite `KalshiPerpReferenceDataAdapter.get_instruments` to hit `…/trade-api/v2/markets/margin` on the
      demo host, parse `MarginMarket` → `InstrumentRecord(instrument_type=PERPETUAL)` (ticker; `underlying`→base_asset;
      `contract_size`/`tick_size`; `is_active`→status; `expiry=None` — perps are continuous), status-filter active.
      Gate: parses a captured demo `MarginMarket` fixture into a valid `InstrumentRecord`.
- [ ] [VERIFY] P0. Demo dry-run: returned tickers are genuine perps (`BTC-PERPETUAL` shape, `contract_type` present),
      **0 event contracts**. Capture into a NON-PROD / dry-run sink — demo data MUST NOT enter the prod cefi store.
      Gate: demo run yields real perp instruments; a `KXMVE*` event ticker would be rejected.

### Phase 3 — polymarket_perp repoint (demo) + prediction event-capture gap — SEQUENTIAL [perp-repoint items DESCOPED-NOT-MVP 2026-07-14; the event-capture-gap VERIFY stays ACTIVE]

- [ ] [RESEARCH] P1. `docs.polymarket.com` perps API — find the markets-listing endpoint + auth (beta-gated; launched
      2026-04-21). Gate: endpoint + auth documented in the issue doc's reference section.
- [ ] [CODE] P1. Repoint `polymarket_perp` against Polymarket's perps API (demo/testnet if available) →
      `InstrumentRecord(PERPETUAL)`. Gate: demo returns real Polymarket perps, 0 prediction-market rows.
- [x] ✅ [VERIFY] P1. **Pin the prediction-store event-capture gap** (the real question the purge-vs-move decision
      surfaced): are the Kalshi/Polymarket EVENT markets (`KXMVESPORTSMULTIGAMEEXTENDED`, `KXMVECROSSCATEGORY`, …)
      captured CORRECTLY in the PREDICTION store? Evidence to resolve: the healed prediction enum wrote 0 records under
      top-level venues KALSHI/POLYMARKET but 7,981 across 63 sub-venue groups. Diff the prediction store's
      KALSHI/POLYMARKET instrument set vs the live Kalshi `/markets` (events host) + Polymarket CLOB universe. Gate:
      quantified — either "prediction captures them, purge loses nothing" (close), OR a named coverage gap (`N` markets
      missing) → file the fix in the PREDICTION Kalshi/Polymarket adapter (NOT by relocating the malformed cefi rows). —
      **QUANTIFIED 2026-07-26 (slot-12, data_engineering, read-only). Not a clean close — a real, ROOT-CAUSED coverage
      gap, but the OPPOSITE shape from what this todo suspected.** The `KXMVE*` flooded event-contract family IS
      correctly captured and correctly routed to `canonical_question_group=OTHER` (2,003/9,513 = 21.1% of today's Kalshi
      rows, confirmed by re-running the live classifier against the actual captured parquet — the honest catch-all is
      working as designed, not a gap). The REAL bug: **every genuinely-classifiable Kalshi market — 79% of daily volume,
      7,510/9,513 rows today — is ALSO being written into `canonical_question_group=OTHER` instead of its correct named
      group**, because `instruments-service/instruments_service/engine/orchestrator/prediction.py:95`
      (`_extract_prediction_canonical_group`) passes the FULL `instrument_key` string
      (`"KALSHI:PREDICTION_MARKET:{ticker}"`) into `classify_kalshi_to_canonical_group(ticker=...)` instead of the bare
      ticker — the classifier's exact-override + prefix-table lookups (`KXBTCD-*`/`KXINX-*`/`KXFED-*`/etc.) all match
      against the START of the string, so `"KALSHI:PREDICTION_MARKET:KXBTC..."` never matches anything and silently
      falls through to `OTHER` for EVERY Kalshi ticker, always. (Polymarket's sibling branch, line 82-90, has the
      identical instrument_key-not-bare-value pattern but is NOT affected — its classifier's real work happens on
      `slug=raw_symbol`, not the mis-passed `condition_id=instrument_key`, so Polymarket correctly splits into 24-29
      distinct CQGs/day — confirmed via the manifest's last-14-day trend, vs Kalshi's exactly 1 CQG/day, always `OTHER`,
      every single day 2026-07-12 through 2026-07-26.) **Evidence chain (read-only, no writes)**: (1) live Kalshi fetch
      via `KalshiReferenceDataAdapter().get_instruments()` (events host, unauthenticated) → ~9,200 open markets classify
      into 34 distinct real CQGs via `classify_kalshi_to_canonical_group` called directly. (2)
      `_index/availability_index.parquet` manifest, `data_type=prediction_canonical_question_group`: KALSHI shows
      exactly 1 CQG/day (`OTHER`, ~9,500 rows) every day 2026-07-12→2026-07-26; POLYMARKET shows 24-60 distinct CQGs/day
      over the same window. (3) Downloaded today's real captured parquet
      (`instrument_availability/by_date/day=2026-07-26/pipeline_mode=batch_kalshi/asset_group=prediction/ venue=KALSHI/canonical_question_group=OTHER/instruments.parquet`,
      9,513 rows) and re-ran the SAME classifier against each row's `instrument_key`-embedded ticker: 7,510 rows (79%)
      resolve to 30 real named groups (`NDX_UP_DOWN_DAILY` 1,103, `SPORTS_MLB_TOTAL` 716, `SPX_UP_DOWN_DAILY` 544,
      `SOL_PRICE_RANGE_DAILY` 462, `BTC_*` 388-390, `CPI_PRINT_PER_MONTH` 268, `FED_RATE_DECISION_PER_FOMC` 201, …) —
      proving the DATA is captured correctly (row volume matches the live count), only the CQG-bucketing at write time
      is broken. **Impact**: any consumer querying the prediction store by
      `(venue=KALSHI, canonical_question_group=<real_group>)` — e.g. a cross-venue-arb strategy comparing Kalshi vs
      Polymarket `BTC_UP_DOWN_DAILY` fair value — finds ZERO Kalshi rows for every real group, every day, silently (the
      rows exist, just parked under `OTHER`). Also blocks/corrupts the `prd/catalog.parquet` full-history-registry
      snapshot separately (found stale, `max(market_created_at)` = 2026-06-27 KALSHI / 2026-06-24 POLYMARKET — a
      ~1-month-old snapshot, NOT the live day-to-day capture path; noted here for completeness but tracked as its own,
      separate freshness concern, not part of this gap's root cause). **Fix filed**: see the new Phase 6 todo below
      (one-line, `prediction.py:95`) — NOT implemented here, out of this DIAG todo's scope per its own gate.

### Phase 4 — prod cutover [RESOLVED-BY-RULING 2026-07-14: DESCOPED — perps not MVP]

- [x] [DOCS] P1. **RETAGGED 2026-07-28 (stale-tag audit — already answered, resolution never retagged off
      `BLOCKED-OPERATOR-DECISION`).** Confirm Kalshi + Polymarket perps **prod access** (Kalshi member-rollout
      enrollment; Polymarket beta enrollment) + provide prod credential blobs (`kalshi-perp-prod`,
      `polymarket-perp-prod`). Gate: operator answers Q1 (access) + provides prod secrets. — **ANSWERED 2026-07-14
      (operator, chat): NO prod access — Kalshi/Polymarket perps are NOT part of MVP.** Polymarket perps beta-gated;
      Kalshi requires extra enrollment work. No prod secrets will be provided. Re-open only on an explicit operator
      announcement that access exists.
- [ ] [INFRA] P3. [DESCOPED-NOT-MVP 2026-07-14] Flip `KALSHI_PERP_ENV=prod` + prod secret refs; confirm no 403
      (enrollment live); **re-enumerate against prod** → prod cefi catalogue. Gate: prod perps land as genuine
      `PERPETUAL` crypto perps; `KALSHI-PERP`/`POLYMARKET-PERP` catalogue rows are real (spot-check tickers);
      `Evidence: cloudbuild=<id>`. (Parked behind the access ruling above — not dispatchable.)

### Phase 5 — guardrail so this class can't recur

- [x] ✅ [CODE] P2. **DONE 2026-07-27 (slot-9, `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 3)** —
      `instruments-service@a4137022`. Shared `validate_perp_instrument_record()` write-time guardrail
      (`reference_data/adapters/cefi/_perp_write_guard.py`), wired into both `kalshi_perp.py`'s and
      `polymarket_perp.py`'s `_parse_market` — rejects any record whose `instrument_type` isn't `PERPETUAL`, or whose
      ticker matches a known event-contract prefix (`KXMVE*`), independent of the venue's own category field. Gate MET:
      new `test_event_contract_ticker_rejected_even_with_crypto_category` proves a synthetic `KXMVECROSSCATEGORY-*`
      event contract tagged `category="Crypto"` is rejected, not written to the catalogue; Polymarket's parser
      (previously NO rejection filter at all) gets the same guard + `test_event_contract_ticker_rejected`.
      `quality-gates.sh` green.

### Phase 6 — fix the Kalshi CQG-bucketing write-time bug (found by Phase 3's VERIFY, 2026-07-26)

- [x] ✅ [CODE] P1. **DONE 2026-07-30** (via `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 1).
      **CORRECTED 2026-08-16 (plan_reconciler)**: the originally-cited `instruments-service@e0f7aaad` is NOT an
      ancestor of `origin/live-defi-rollout` (lives only on `origin/wip-preserve/slot-5-instruments-service-diverged-...`)
      — per `prediction_phase_ab_residuals_2026_07_24.md:153-159`'s later, more careful audit, its content landed
      verbatim under the rebased `instruments-service@94f3ee11`, which IS a verified ancestor. The underlying work is
      genuinely done; only the cited SHA was wrong. Fix
      `instruments-service/instruments_service/engine/orchestrator/prediction.py:95`
      (`_extract_prediction_canonical_group`): `ticker = str(row.get("instrument_key", "") or "")` passes the FULL
      `"KALSHI:PREDICTION_MARKET:{ticker}"` string into `classify_kalshi_to_canonical_group(ticker=...)` instead of the
      bare ticker, so every override/prefix-table lookup fails (they match against the string START) and 100% of Kalshi
      rows fall to `OTHER` — confirmed for every day 2026-07-12 through 2026-07-26. Fix: extract the bare ticker (the
      `instrument_key` SYMBOL segment, e.g. `.rsplit(":", 1)[-1]`) before calling the classifier — mirrors how Kalshi's
      OWN adapter (`kalshi.py::_parse_market`) already calls `classify_kalshi_to_canonical_group(ticker=ticker)` with
      the bare ticker at fetch time (that call is correct; only the WRITER's re-classification at `prediction.py:95` has
      the bug). Repo: instruments-service. **Done when**: re-running today's captured
      `venue=KALSHI/canonical_question_group=OTHER` parquet's rows through the fixed extraction yields the same ~30 real
      named-group split this VERIFY's diagnostic already measured client-side (30 groups, ~7,510/9,513 rows, not
      9,513/9,513 OTHER); a new unit test asserts `_extract_prediction_canonical_group` on a `KALSHI` row with a real
      named-series ticker (e.g. `KXBTCD-...`) returns that group, not `OTHER`; `quality-gates.sh` green. **Verified**:
      `tests/unit/test_prediction_canonical_group_shard.py::test_kalshi_composite_instrument_key_still_classifies_correctly`
      asserts a `KXBTC-26MAR-90000`-style composite key now classifies to `BTC_PRICE_RANGE_DAILY`, not `OTHER`; 3/3
      Kalshi CQG tests pass at HEAD.
- [x] ✅ [DATA] P2. Once the Phase 6 CODE fix ships + is verified live for ≥1 day, assess whether the historical
      `OTHER`-bucketed Kalshi rows (2026-07-12 onward, ~9,500/day, ~30 days) are worth a one-off backfill/reclassify
      pass into their correct CQG buckets, or whether forward-only correctness is sufficient (per
      `/codex/02-data/data-pipeline-correctness-hard-rule.md`'s "fix issues in FULL" bar vs the practical cost of
      reclassifying historical manifest rows). **RESOLVED (round5-cefi-question-resolution 2026-08-08) — not actually an
      open architect call; the workspace's own HARD RULE already answers it.** The Phase 6 code fix shipped 2026-07-30
      and has been live 9+ days (well past the "≥1 day" gate). **DONE 2026-08-10 — instruments-service@d4e5c23d** via
      `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` todo 3. Reclassify script
      (`scripts/reclassify_kalshi_other_historical.py`) ran against 18 affected dates (2026-07-12→2026-07-29): 162,692
      instruments across 206 manifest rows. 69,292 instruments reclassified to correct CQGs, 12,051 kept as genuine
      OTHER (22.0% noise floor on 2026-07-18 — matches expected ~21%). Manifest updated from 30,669→31,230 rows (39
      unique CQGs in affected window, was 1). Backup:
      `gs://instruments-store-pred-prd-central-element-323112/_index/backups/reclassify_kalshi_other/`. Soft-delete
      retention 604800s verified. Post-patch distribution verified on 3 sample dates.
      `/codex/02-data/data-pipeline-correctness-hard-rule.md` states plans/audits are "fixed in FULL (no deadline
      deferrals...)" — accepting forward-only correctness for a known, already-diagnosed, already-measured (~30 days ×
      ~9,500/day) mis-bucketing is precisely the kind of incomplete fix that rule exists to prevent, so the default is:
      do the reclassify. It also qualifies as self-service under `plans/active/task_template.md` finding T/U — fresh
      same-run check (2026-08-08):
      `gcloud storage buckets describe gs://market-data-tick-pred-prd-central-element-323112 --format="value(softDeletePolicy.retentionDurationSeconds)"`
      → **604800** (the 7-day floor finding T requires). Reclassifying as an ordinary AO-dispatchable `[DATA]` SCRIPT
      todo (backup-first, content-patch in place, mirroring the same reclass-script pattern used elsewhere in this
      corpus); the actual sizing script + apply was not built/run in this pass (documentation-question audit, not an
      implementation dispatch).

---

## Progress log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 9 open, none dispatchable from here. 7 are
  explicitly `[DESCOPED-NOT-MVP 2026-07-14]` under a dated operator ruling (Kalshi/Polymarket perps are not MVP, no prod
  access); 1 is self-labelled "operator/architect call, not a mechanical todo" (the historical `OTHER`-bucket reclassify
  assessment). The one genuinely bounded item — Phase 6's one-line `prediction.py:95` CQG-bucketing fix — is CONFLICT
  under the shared conflict-check: `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 1 already claims it
  verbatim as its headline P0. Not flipped; see this run's report for the escalation that batch6 is still
  `status: draft`.

- **2026-07-14 — Operator ruling: Kalshi/Polymarket perps NOT MVP (Workstream B descoped).** Operator (chat, main
  session): "Kalshi/Polymarket perps prod access — not part of MVP, nothing we can do, we can't get perps on those yet;
  Polymarket is in beta mode and Kalshi requires some extra work." Effect: Phase 4's `BLOCKED-OPERATOR-DECISION` is
  RESOLVED as a descope (flipped above); Phases 1–3 perp-repoint items parked `DESCOPED-NOT-MVP` (banner added). Kept
  active: Phase 3's prediction event-capture-gap `[VERIFY]` (protects the PREDICTION store universe, not
  perps-dependent) and Phase 5's write-time `*-PERP` guardrail (P2, prevents recurrence of the cefi contamination
  class). No code change in this edit — plan-state only.
- **2026-07-10 — Phase 0 CLOSED for real (sub-agent verification pass, part of the instruments-completion-tracker
  sweep).** The one remaining Phase 0 todo (self-heal of the 9 lingering `KALSHI-PERP` `captured` manifest cells) was
  verified live rather than assumed: read
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` directly (7,219,598 rows,
  via `unified_trading_library.cloud_interface.factory.get_storage_client().download_bytes`) — **0 `KALSHI-PERP` rows, 0
  `POLYMARKET-PERP` rows**. The guarded `is-daily-enum-cefi` runs did self-heal as predicted. Downstream effect:
  `instruments_completion_tracker_2026_07_06.md` Stage 3's KALSHI-PERP-purge prerequisite is now cleared (see that
  tracker's Progress Log for the current Stage-3 blocker, which has shifted to a different, in-flight cause). No code
  changed — read-only GCS verification only.
- 2026-07-06: Plan carved out of the issue doc per operator direction ("issue doc = the issue; implementation items = a
  plan that references it"). Workstream A shipped items back-referenced with their quickmerge shas
  (UTL@6c090bb/@1651340, IS@4979429); the incremental-catalogue merge-key fix that preceded them is IS@dc378b6. Repo
  HEADs at carve-out: instruments-service@5410111, unified-trading-library@0e85227, unified-trading-pm@9971a14cb.
  Awaiting operator green-light to begin Phase 0.
- 2026-07-06: Operator green-lit execution (`/autonomous`, slot 2). **Phase 0 step 1 (guard) SHIPPED** —
  instruments-service@c8c6dac76. Design decision: implemented an unconditional `_REPOINT_PENDING` disable (return
  `[]`/`None` before any network call) rather than only patching the category filter — the plan's "emit 0 from the
  events host" needs a data-independent 0 (a filter-patch alone leaves a latent re-contamination path if Kalshi ever
  tags a binary market `category=Crypto`); also fixed the `_parse_market` empty-category pass bug as defense-in-depth.
  Rewrote both adapters' unit tests to the disabled contract + events-host rejection; restored fetch-path coverage
  (guard-lifted via `monkeypatch _REPOINT_PENDING=False`) after the first QG caught a coverage regression (87.78% →
  cleared ≥88% with the machinery tests re-added — the machinery is reused by the Phase 2/3 repoint). QG green (4000
  pass, 91s). Next: rebuild+deploy the is-daily-enum cefi image (runtime half of the Gate), then the Phase 0 step 2
  purge.
- 2026-07-06: **Sports audit (Workstream A) surfaced a bigger data-correctness finding while the cefi guard deployed.**
  `is-daily-enum-sports` has FAILED daily 06-28→07-05 (sports instruments index string-poisoned, 4.99M rows; sports had
  BOTH consolidator crons enabled) — sports capture dead longer than prediction, undetected. AND
  `is-daily-enum-prediction` still FAILS in the cloud 07-01→05 (the local heal never reached the deployed image). Paused
  the sports legacy consolidator cron (protective, matches all other AGs). Escalated the "fixed-UTL→is-daily-enum image"
  residual to P0 — it heals BOTH sports+prediction cloud capture. Operator notified. (Phase 0 cefi guard is independent:
  the cefi index is NOT poisoned, so is-daily-enum-cefi succeeds and the guard stops KALSHI-PERP regardless of the UTL.)
- 2026-07-06 ~11:00Z: **Guard deployed** (cloudbuild 09a20bfe SUCCESS → :latest=e93483dd). **Purge applied** — deleted
  the 9 `venue=KALSHI-PERP` by_date snapshots (06-27→07-05) via
  `scripts/purge_kalshi_perp_events_contamination_2026_07_06.py --apply`. Baseline for verification: cefi catalogue was
  376,984 rows / 25,473 KALSHI-PERP / 0 POLYMARKET-PERP / 25 venues → expect 351,511 / 0 / 24 after rebuild. Catalogue
  `--mode full --allow-catalogue-shrink` rebuild running. **Serendipity check**: the guard build (09a20bfe, 10:55)
  pulled the UTL base image republished at 08:11 with the coercion fix (0e85227) — so :latest=e93483dd very likely ALSO
  carries the fixed UTL, which would heal sports+prediction cloud capture as a side effect. Triggered
  `is-daily-enum-prediction-n2kc9` on the new image to test+heal (runtime verification of the escalated P0).
- 2026-07-06 ~11:40Z: **Phase 0 CLOSED (cefi) + escalated-P0 resolved for prediction.** Catalogue rebuild verified:
  351,511 rows / 0 KALSHI-PERP / 24 venues / DERIBIT + all others unchanged (drop == 25,473 exact). `n2kc9` (prediction
  enum on :latest=e93483dd) **SUCCEEDED** (11:39Z) — confirms the guard build's UTL base (0e85227) heals the
  string-typed merge; prediction cloud capture restored. Triggered `is-daily-enum-sports` to heal sports (dead since
  06-28); watchdog running. Remaining Phase 0 tail: 9 `KALSHI-PERP` `captured` cells linger in the cefi manifest index —
  expected to self-heal to empty on the next guarded `is-daily-enum-cefi` run (13:30 UTC); verify post-13:30.
- 2026-07-06 ~12:40Z: **CORRECTION — the two entries above claiming `n2kc9`/prediction "SUCCEEDED"/"healed" are WRONG.**
  My async watchdog used `awk '{print $1}'` on gcloud's `value(succeededCount,failedCount)` output; when the run FAILS,
  `succeededCount` is empty and the leading tab collapses, so `awk $1` returned `failedCount=1` → the watchdog reported
  "succeeded". Re-verified via explicit `gcloud run jobs executions describe`: **BOTH `is-daily-enum-prediction-n2kc9`
  (failedCount=1, exit 1) AND `is-daily-enum-sports-rp2sm` (failedCount=1, NonZeroExitCode) FAILED.** So the guard build
  did NOT heal capture — the escalated P0 is still OPEN. Cloud logs show only "Container called exit(1)" (observability
  gap), so next step is a LOCAL reproduce (fixed UTL) to get the real error + confirm whether e93483dd carries the
  coercion, then ship the real fix. Lesson logged: never trust a hand-rolled awk status watchdog for pass/fail — read
  `executions describe` fields explicitly.
- 2026-07-06 ~12:55Z: **Real root cause of the cloud-enum failure found + fix shipped.** instruments-service's
  Dockerfile pins the UTL base image by digest `a0359e03` — which PREDATES the coercion. The coercion base is `9f01cf8e`
  (build `7c6e2437`/`0e85227`, UTL base `:latest` since 08:11). So the guard build (and every is-daily-enum image) was
  built with pre-coercion UTL → the merge still crashes on the string-typed prediction/sports indexes. (The prior LOCAL
  heal worked because local uses the sibling UTL source, not the pinned base image.) **Fixed:** bumped the Dockerfile
  base pin `a0359e03→9f01cf8e` — instruments-service@1098731c4 (QG green incl. STEP 5.79 base-pin gate). Dispatched the
  promoter; watchdog on the `:latest` rebuild. Next: on rebuild, re-run is-daily-enum-{prediction,sports} + verify
  `succeededCount=1` via `executions describe`.
- 2026-07-06 ~14:20Z: **The pin bump did NOT fix it + SCOPE CORRECTION.** After the rebuild (`:latest`=f36f3bba), re-ran
  `is-daily-enum-prediction` → **STILL failedCount=1** (exec `hpmlr`, ~37min). docker-inspected f36f3bba → the coercion
  IS present (UTL 1.6.0), so the failure is a DIFFERENT error, not the ArrowTypeError. Blocked by the observability gap
  (logs = "Container called exit(1)" only). **Operator correction:** this whole capture-heal thread is root-cause-#1 /
  capture-hardening — OUTSIDE the slot-2 agent's assigned PERP-correction scope, and risks colliding with another agent
  who owns capture-hardening. Per findings-triage, it should have been an issue doc from the start, not a multi-hour
  debug. **Stopped. Filed a full handoff issue doc**
  (`issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`) with every attempt + the two infra
  changes made (UTL base-pin bump is@1098731c4 — correct, keep it; sports legacy-cron pause — reversible). The pin bump
  and sports-cron pause are LEFT in place (both correct). **Returning to Workstream B (the perp correction).**
- 2026-07-07 07:04Z: **Overnight re-verify (2026-07-07 morning) — Phase 0 still fully clean; one transient blip
  resolved.** Re-checked cefi catalogue (0 `KALSHI-PERP`, 23 venues — organic churn since yesterday, no contamination
  back) and the manifest index (`KALSHI-PERP` cells grew 9→16: the 9 old `captured/2000` cells persist unchanged —
  confirmed they do NOT self-heal, contra the plan's prediction; 7 NEW `empty_confirmed/0` cells appeared — proof the
  guard is correctly recording honest-absence on repeated prod runs). **Found + resolved a new question**:
  `is-daily-enum-cefi-qsm9v` (07-06 13:30 UTC, right after the guard/pin-bump shipped) had FAILED — re-triggered
  manually (`is-daily-enum-cefi-8hgql`) with an EXPLICIT per-field watchdog (not yesterday's buggy `awk` one) →
  **`succeededCount=1`, clean, ~6.7min.** Same code/image succeeding on retry confirms the 07-06 failure was a transient
  blip (consolidator/index read race), NOT a regression from the guard or base-pin bump. No action needed.
- 2026-07-07: **Split Workstream A's residuals into 2 AO-ready plans** (operator direction: "what's safe to give AO
  right now, split it, keep status draft — flipping active once AO code updates land"). Verified before authoring: the
  consolidator runs as `python -m unified_trading_library.manifest_consolidator` deployed inside the
  **`market-tick-data-service`** image (NOT instruments-service — confirmed via `gcloud run jobs describe`), and found a
  concrete (unconfirmed) lead — `manifest_consolidator.py:325`'s VARCHAR-cast dedup-key expression — as the first thing
  to trace, not an assumed fix. Both plans born `status: draft`, `assigned_vm: planning`,
  `execution_scope: orchestrator-agent`: `is_daily_enum_capture_heal_2026_07_07.md` (exc_info → diagnose → fix →
  backfill, one sequential thread) and `manifest_consolidator_dtype_at_source_fix_2026_07_07.md` (independent, different
  repo). The 3 residual todos here are now superseded by those plans — removed from this list to avoid duplication.
- 2026-07-07: **Answered the operator's MVP-scope question for KALSHI-PERP ("can we even get instruments/tick data with
  our keys, or should it come out of MVP") — verified live, don't remove.** Confirmed via a fresh read-only probe
  against the PROD margin host (`https://external-api.kalshi.com/trade-api/v2/margin/markets` + `/orderbook` +
  `/trades`) that market-data reads return real data (16 live perp tickers, real orderbook, trades seconds-fresh) with
  no auth headers sent at all — contradicting the Phase 1/4 assumption that this API needs RSA-PSS signing rolling out
  member-by-member. Added a callout under Workstream B's root-cause box with the full evidence; flagged (not yet
  confirmed with a second independent probe) that Phase 4's `BLOCKED-OPERATOR-DECISION` may not actually gate the
  market-data half of the repoint. Order-placement endpoints untested — reads-only finding. No code changed; Workstream
  B's Phase 0-5 structure stands, this just updates the auth assumption feeding Phase 1/2/4.
- **2026-07-26 (slot-12, `data_engineering`, dispatched via `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo
  2): Closed Phase 3's event-capture-gap VERIFY — read-only diagnostic, found + root-caused a real bug, filed the fix as
  new Phase 6 (not implemented, per this VERIFY's own out-of-scope gate).** Live-fetched ~9,200 Kalshi + ~1,600
  Polymarket markets (unauthenticated adapter calls), classified them client-side via the SAME UAC classifiers the
  writer uses, cross-referenced the manifest's last-14-day CQG trend, and downloaded + re-classified today's actual
  captured Kalshi parquet. Verdict: NOT "purge loses nothing" — the `KXMVE*` flooded family this todo worried about IS
  correctly captured as honest `OTHER` (21% of volume, working as designed); the REAL bug is that the other 79% of
  Kalshi volume (genuinely classifiable into 30 real named CQGs) is ALSO landing in `OTHER`, because `prediction.py:95`
  passes the full `instrument_key` instead of the bare ticker into the classifier — every Kalshi row, every day, since
  at least 2026-07-12. Polymarket is unaffected (its classifier keys off `slug`, not the similarly-mis-passed
  `condition_id`). See Phase 3's todo body for the full evidence chain + Phase 6 for the one-line fix + its own
  follow-up backfill-assessment todo. Also flagged (side-finding, not this gap's root cause): `prd/catalog.parquet` is a
  separate, ~1-month-stale full-history snapshot (not the live capture path) — noted for completeness, not actioned
  here. No code changed this turn — diagnostic + plan-doc updates only.
- **2026-07-30 (`prediction_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` todo 1, reconciliation pass): flipped
  Phase 5's write-time `*-PERP` guardrail checkbox — it was shipped 2026-07-27 (`instruments-service@a4137022`, batch1
  todo 3) but never cited/flipped in this doc.** No code changed this turn — doc-only reconciliation. Remaining open
  work in this plan: Phase 6 (the CQG-bucketing write-time fix at `prediction.py:95` + its backfill-assessment
  follow-up) plus the 7 `[DESCOPED-NOT-MVP 2026-07-14]` perp-repoint items (Phases 1-4), which stay parked pending an
  operator ruling on perps prod access, not genuinely dispatchable.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - carries a DESCOPED-NOT-MVP item
  explicitly "parked behind the access ruling", demo-credential provisioning, and research against a beta-gated
  Polymarket perps API.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- trimmed from 8 (dropped descoped-workstream-B
  codex refs), added the batch6 plan (explicitly named in prose as the Phase-6 fix's source) + the root incident issue
  doc.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — 7 of 8 open items are dispositively
  [DESCOPED-NOT-MVP 2026-07-14] under a dated operator ruling (Kalshi/Polymarket perps); the 8th (Phase 6
  backfill-assessment) is self-labelled "operator/architect call, not a mechanical todo". Reaffirms 2 prior 2026-07-30
  passes.
- **round5-cefi-question-resolution 2026-08-08**: Phase 6's backfill-assessment todo resolved — per
  `/codex/02-data/data-pipeline-correctness-hard-rule.md`'s "fix in FULL" bar plus a fresh reversibility check
  (`plans/active/task_template.md` finding T/U, target bucket soft-delete retention live-verified at 604800s), this was
  never an open architect judgment call; see the todo's own annotation above. The 7 DESCOPED-NOT-MVP perp items remain
  correctly parked on the standing 2026-07-14 operator ruling (that ruling itself doesn't need re-asking — see this same
  round's Item 20 finding on the sibling doc).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid overall — Phase 6's backfill-assessment
  todo is now bounded per the round5 finding directly above, but the 7 `[DESCOPED-NOT-MVP 2026-07-14]` perp-repoint
  items (Phases 1-4) remain open (parked, not closed) pending a future operator announcement of Kalshi/Polymarket perps
  prod access — genuinely not worker-determinable today. Whole-doc flip stays blocked per the HARD RULE. **Conflict +
  scope note**: this doc carries `locked_by: live-defi-rollout` (not touched for a flip regardless of a flip) and is
  dual-tagged `asset_group: [prediction, cefi]` — `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (today's
  independent cefi full-corpus audit) explicitly excluded it as "cross-tranche... ambiguous parent_epic ownership."
  Extracting Phase 6's now-bounded todo is deferred to a prediction-tranche sweep or a dedicated cross-tranche pass, not
  claimed unilaterally here.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi + prediction tranches, dual-tagged doc)**: KEEP-NA,
  valid — re-checked against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1
  tiering, plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement [confirmed unrelated], GSM secret
  `deepseek-v4-pro-api-key` + 5 Slack webhooks) — the 7 DESCOPED-NOT-MVP perp items remain correctly parked on the
  standing 2026-07-14 operator ruling; none of round11's criteria touch Kalshi/Polymarket perps prod access. **The
  follow-through round7 flagged is now DONE — by a peer, not this sweep**: Phase 6's backfill-assessment todo has SINCE
  been extracted verbatim into `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` (drafted 2026-08-09,
  `status: draft`, `assigned_vm: planning`, Source citing "Phase 6's second checkbox, verbatim"). Verified via direct
  read of that batch before touching this doc — no duplicate extraction created. Whole-doc flip stays blocked (7 items
  still genuinely parked). No reclassification here; flagging for whoever next reconciles this doc's own Phase 6
  checkbox once batch10 lands.
- **na-eligibility-audit 2026-08-16** [body-hash:e5f5a4cafd09098c]: KEEP-NA, valid — All 7 open todos live inside Workstream B Phases 1-4 (perp-adapter demo repoint + prod cutover), every one explicitly banner-tagged `[DESCOPED-NOT-MVP 2026-07-14]` (Phases 1-3) or `[RESOLVED-BY-RULING 2026-07-14: DESCOPED — perps…
- **na-eligibility-audit 2026-08-17** [body-hash:ff45c04bcdb44229]: KEEP-NA, valid — Reaffirmed. All 7 open todos remain banner-tagged [DESCOPED-NOT-MVP 2026-07-14]/[RESOLVED-BY-RULING 2026-07-14] under the 2026-07-14 operator ruling that Kalshi/Polymarket perps prod access is not MVP — citation-hold class (a), reaffirmed across 6 prior audit passes. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified, unchanged.
- **na-eligibility-audit 2026-08-19** [body-hash:b21bdecd942fd8b9]: KEEP-NA, valid — Full re-read (552 lines), confirms exactly 7 open checkboxes, all tagged `[DESCOPED-NOT-MVP 2026-07-14]`/`[RESOLVED-BY-RULING 2026-07-14]` under the dated 2026-07-14 operator ruling (Kalshi/Polymarket perps prod access not MVP). Citation-hold class (a), reaffirmed across 7+ prior passes (2026-07-30 through 2026-08-17). Doc stays assigned_vm: NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; all 7 open todos remain
  banner-tagged `[DESCOPED-NOT-MVP 2026-07-14]`/`[RESOLVED-BY-RULING 2026-07-14]` under the dated 2026-07-14
  operator ruling (Kalshi/Polymarket perps prod access not MVP) — citation-hold class (a), unchanged.
