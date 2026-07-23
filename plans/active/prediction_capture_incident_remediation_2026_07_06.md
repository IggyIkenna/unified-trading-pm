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
related:
  [
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    plans/active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md,
    plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md,
    plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
  ]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
last_updated: 2026-07-14 # (was: 2026-07-10 -- bumped 2026-07-15, plan-reconcile: 2026-07-14 operator-ruling banner/descope edit + matching Progress Log entry postdated the recorded last_updated, same staleness class as the 2026-07-12 correction)
locked_by: live-defi-rollout
locked_since: 2026-07-06
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
---

# Prediction-capture incident remediation

> **This plan tracks the ACTIONABLE remediation only. The diagnosis, root-cause evidence (live Kalshi API probe,
> contamination timeline, why-nothing-alerted), the demo→prod switch-cost analysis, and the operator-decision context
> are the RECORD and live in the issue doc — this plan references them, it does not duplicate them:**
> [`plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`](issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md).

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
      [`manifest_consolidator_dtype_at_source_fix_2026_07_07.md`](manifest_consolidator_dtype_at_source_fix_2026_07_07.md)
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
- [ ] [VERIFY] P1. **Pin the prediction-store event-capture gap** (the real question the purge-vs-move decision
      surfaced): are the Kalshi/Polymarket EVENT markets (`KXMVESPORTSMULTIGAMEEXTENDED`, `KXMVECROSSCATEGORY`, …)
      captured CORRECTLY in the PREDICTION store? Evidence to resolve: the healed prediction enum wrote 0 records under
      top-level venues KALSHI/POLYMARKET but 7,981 across 63 sub-venue groups. Diff the prediction store's
      KALSHI/POLYMARKET instrument set vs the live Kalshi `/markets` (events host) + Polymarket CLOB universe. Gate:
      quantified — either "prediction captures them, purge loses nothing" (close), OR a named coverage gap (`N` markets
      missing) → file the fix in the PREDICTION Kalshi/Polymarket adapter (NOT by relocating the malformed cefi rows).

### Phase 4 — prod cutover [RESOLVED-BY-RULING 2026-07-14: DESCOPED — perps not MVP]

- [x] [BLOCKED-OPERATOR-DECISION] P1. Confirm Kalshi + Polymarket perps **prod access** (Kalshi member-rollout
      enrollment; Polymarket beta enrollment) + provide prod credential blobs (`kalshi-perp-prod`,
      `polymarket-perp-prod`). Gate: operator answers Q1 (access) + provides prod secrets. — **ANSWERED 2026-07-14
      (operator, chat): NO prod access — Kalshi/Polymarket perps are NOT part of MVP.** Polymarket perps beta-gated;
      Kalshi requires extra enrollment work. No prod secrets will be provided. Re-open only on an explicit operator
      announcement that access exists.
- [ ] [INFRA] [DESCOPED-NOT-MVP 2026-07-14] P3. Flip `KALSHI_PERP_ENV=prod` + prod secret refs; confirm no 403
      (enrollment live); **re-enumerate against prod** → prod cefi catalogue. Gate: prod perps land as genuine
      `PERPETUAL` crypto perps; `KALSHI-PERP`/`POLYMARKET-PERP` catalogue rows are real (spot-check tickers);
      `Evidence: cloudbuild=<id>`. (Parked behind the access ruling above — not dispatchable.)

### Phase 5 — guardrail so this class can't recur

- [ ] [CODE] P2. Write-time validation: any `*-PERP` venue record MUST be `instrument_type=PERPETUAL` AND pass a
      perp-ticker sanity check (reject event-contract patterns, e.g. `KXMVE*`/`KXMVECROSSCATEGORY*`); reject at the
      writer, not silently. Gate: a synthetic event contract injected into a `-PERP` feed is rejected, not written to
      the catalogue.

---

## Progress log

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
