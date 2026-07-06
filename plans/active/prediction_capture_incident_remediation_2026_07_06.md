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
    plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md,
  ]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
last_updated: 2026-07-06
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
assigned_role: data-pipeline-engineer
drift_direction: advance-code
---

# Prediction-capture incident remediation

> **This plan tracks the ACTIONABLE remediation only. The diagnosis, root-cause evidence (live Kalshi API probe,
> contamination timeline, why-nothing-alerted), the demo→prod switch-cost analysis, and the operator-decision context
> are the RECORD and live in the issue doc — this plan references them, it does not duplicate them:**
> [`plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`](issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md).

## Codex SSOTs (read before touching the relevant workstream; post-phase audit updates them)

- `codex/05-infrastructure/manifest-consolidator-ssot.md` — the consolidator that string-typed the canonical index
  (Workstream A dtype-at-source fix).
- `codex/02-data/availability-manifest-and-data-status.md` — ManifestRow schema (`instrument_count` is `int`); the
  write-side coercion contract.
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` +
  `codex/04-architecture/shard-level-failure-isolation.md` — reference-data adapter + per-shard-isolation contract
  (Workstream B adapter rewrite; the shard-isolation catch that swallowed the crash without `exc_info`).
- `codex/06-coding-standards/config-reloader-pattern.md` — typed config for the `KALSHI_PERP_ENV` host resolver.
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

- [ ] [CODE] P1. Fix the manifest **consolidator's dtype handling at ITS source** — it should persist schema-typed
      columns, not utf8. Locate the consolidator image/repo (SSOT
      `codex/05-infrastructure/manifest-consolidator-ssot.md`), find where the ~2026-06-27-era change began
      string-typing `instrument_count`, fix + redeploy. Gate: a fresh consolidator cycle writes
      `_index/availability_index.parquet` with `instrument_count` as int (not utf8), verified by direct read.
      (Non-urgent — the UTL coercion crash-proofs the reader — but the canonical index dtype must be honest.)
- [ ] [INFRA] P1. Audit **sports** for the same double-consolidator condition (`…instruments-sports-legacy` also shows
      recent every-minute runs); pause its legacy cron if confirmed + verify sports capture/index dtype health. Gate:
      sports runs one consolidator; sports index dtypes match schema.
- [ ] [INFRA] P1. Get the fixed UTL into the `is-daily-enum-*` Cloud Run image (UTL base republish → instruments-service
      pin bump → image rebuild — the 07-04 dependency-update short-circuit recipe). Gate: the 13:30 UTC cloud
      `is-daily-enum-prediction` run exits 0 on the deployed image (not just the local heal);
      `Evidence: cloudbuild=<id>`.
- [ ] [VERIFY] P1. Backfill the missed window 07-01→07-06: confirm the healed capture's `--days-back` reach covered the
      gap days' by_date + manifest rows, or run a targeted backfill; then confirm the catalogue picks up post-06-27
      listings (`max(available_from)` advances) on the next daily run. Gate: no by_date/manifest holes in 07-01→07-06;
      catalogue `available_from` advances past 06-27.
- [ ] [CODE] P2. Observability: add `exc_info=True` to the UTL shard-isolation catch (`service_framework/_adapter.py`
      "Handler %s failed on payload") + root-cause why Cloud Run job stdout/stderr does not reach Cloud Logging (affects
      every lifecycle-catalogue/enum job — the weekly-full diagnoses had to work blind). Gate: a forced handler
      exception logs the full traceback; a Cloud Run job's app logs appear in Cloud Logging.

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

### Phase 0 — stop contamination + purge (NOW, no access needed) — SEQUENTIAL (guard ships before purge)

- [ ] [CODE] P0. Guard both `kalshi_perp` + `polymarket_perp` adapters to emit **0 records** from the current (wrong,
      events) host until repointed — fix the `_parse_market` empty-category "pass" bug. Ship (QG + quickmerge) + image
      rebuild so the 13:30 UTC cloud run stops writing fake perps. Venue declarations STAY. Gate: unit test asserts 0
      records from the events-host response; next cefi daily run writes 0 `KALSHI-PERP` rows;
      `Evidence: cloudbuild=<id>`.
- [ ] [DATA] P0. Purge the 25,473 fake `KALSHI-PERP` rows from cefi: corrective `--mode full --allow-catalogue-shrink`
      cefi run + delete the `venue=KALSHI-PERP` by_date + manifest cells. **PURGE, not MOVE (operator-decided
      2026-07-06):** the perp parser stamped these binary EVENT contracts as `instrument_type=PERPETUAL`/`expiry=None`,
      discarding their expiry/series/YES-NO structure; they are reference-data rows (no captured prices), the correct
      producer is the prediction Kalshi adapter, and Kalshi is cheaply re-enumerable — moving would relocate degraded
      stubs + conflict with the prediction store's canonical copies. (The "are these captured correctly anywhere?"
      question is Phase 3's `[VERIFY]`.) Gate: cefi catalogue has 0 `KALSHI-PERP` rows; row-count drop == 25,473; no
      other venue touched.

### Phase 1 — foundation: config-drive host + shared RSA-PSS auth (no access needed) — PARALLEL

- [ ] [CODE] P1. Make the perp base URL config-driven — `KALSHI_PERP_ENV=demo|prod` (via `UnifiedCloudConfig`, default
      `demo`) resolving the host; delete the hardcoded `_KALSHI_BASE_URL` events-host const from the perp adapters.
      Gate: unit test resolves demo vs prod host from config.
- [ ] [CODE] P1. Extract the RSA-PSS signing that ALREADY EXISTS in `adapters/prediction/kalshi.py`
      (`_signed_headers`/`_parse_kalshi_creds`/`_can_sign`) into a shared helper both perp adapters use; wire the demo
      credential blob via the injection path (secret ref `kalshi-perp-demo`). Gate: signed-header unit test on the
      shared helper.

### Phase 2 — repoint kalshi_perp to the margin API (demo) — SEQUENTIAL after Phase 1

- [ ] [CODE] P1. Rewrite `KalshiPerpReferenceDataAdapter.get_instruments` to hit `…/trade-api/v2/markets/margin` on the
      demo host, parse `MarginMarket` → `InstrumentRecord(instrument_type=PERPETUAL)` (ticker; `underlying`→base_asset;
      `contract_size`/`tick_size`; `is_active`→status; `expiry=None` — perps are continuous), status-filter active.
      Gate: parses a captured demo `MarginMarket` fixture into a valid `InstrumentRecord`.
- [ ] [VERIFY] P0. Demo dry-run: returned tickers are genuine perps (`BTC-PERPETUAL` shape, `contract_type` present),
      **0 event contracts**. Capture into a NON-PROD / dry-run sink — demo data MUST NOT enter the prod cefi store.
      Gate: demo run yields real perp instruments; a `KXMVE*` event ticker would be rejected.

### Phase 3 — polymarket_perp repoint (demo) + prediction event-capture gap — SEQUENTIAL

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

### Phase 4 — prod cutover (BLOCKED-OPERATOR-DECISION / -CREDENTIALS — Ikenna)

- [ ] [BLOCKED-OPERATOR-DECISION] P1. Confirm Kalshi + Polymarket perps **prod access** (Kalshi member-rollout
      enrollment; Polymarket beta enrollment) + provide prod credential blobs (`kalshi-perp-prod`,
      `polymarket-perp-prod`). Gate: operator answers Q1 (access) + provides prod secrets.
- [ ] [INFRA] P1. Flip `KALSHI_PERP_ENV=prod` + prod secret refs; confirm no 403 (enrollment live); **re-enumerate
      against prod** → prod cefi catalogue. Gate: prod perps land as genuine `PERPETUAL` crypto perps; `KALSHI-PERP`/
      `POLYMARKET-PERP` catalogue rows are real (spot-check tickers); `Evidence: cloudbuild=<id>`.

### Phase 5 — guardrail so this class can't recur

- [ ] [CODE] P2. Write-time validation: any `*-PERP` venue record MUST be `instrument_type=PERPETUAL` AND pass a
      perp-ticker sanity check (reject event-contract patterns, e.g. `KXMVE*`/`KXMVECROSSCATEGORY*`); reject at the
      writer, not silently. Gate: a synthetic event contract injected into a `-PERP` feed is rejected, not written to
      the catalogue.

---

## Progress log

- 2026-07-06: Plan carved out of the issue doc per operator direction ("issue doc = the issue; implementation items = a
  plan that references it"). Workstream A shipped items back-referenced with their quickmerge shas
  (UTL@6c090bb/@1651340, IS@4979429); the incremental-catalogue merge-key fix that preceded them is IS@dc378b6. Repo
  HEADs at carve-out: instruments-service@5410111, unified-trading-library@0e85227, unified-trading-pm@9971a14cb.
  Awaiting operator green-light to begin Phase 0.
