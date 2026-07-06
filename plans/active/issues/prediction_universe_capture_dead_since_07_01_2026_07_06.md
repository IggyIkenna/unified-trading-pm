---
doc_type: issue
title: Prediction universe capture dead 07-01→07-06 — consolidator string-types instrument_count, writer merge crashes
summary:
  "is-daily-enum-prediction (the 13:30 UTC prediction universe capture) failed with exit 1 every day 2026-07-01→07-06:
  the manifest consolidator persists the canonical availability index with instrument_count as STRINGS, the UTL
  ManifestWriter read-merges it with its own int rows, and merged.to_parquet dies with ArrowTypeError ('Expected bytes,
  got int'). Prediction by_date starved (2,193 ids 06-30 → 0 files 07-03/05 → 3 ids 07-06); catalogue stayed green on
  §7.3 thin-day semantics so nothing alerted. Compounding finds: prediction (and sports) run BOTH legacy AND non-legacy
  instruments consolidators every minute (racing co-writers; other AGs paused legacy 06-08); Cloud Run jobs ship no app
  logs to Cloud Logging; the shard-isolation catch logs without exc_info. UTL write-side Int64 coercion shipped as the
  crash-proof fix; consolidator dtype + migration + backfill of the missed days remain."
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [unified-trading-library, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [manifest, consolidator, prediction, capture, dtype, arrow, observability, instruments]
related: [plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md]
created: 2026-07-06
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source:
  [
    is-daily-enum-prediction daily failure investigation 2026-07-06 — consolidator string-typed instrument_count + UTL
    writer merge ArrowTypeError,
  ]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data-pipeline-engineer
drift_direction: advance-code
depends_on: []
---

# Prediction universe capture dead 2026-07-01 → 07-06 (found during catalogue weekend verification)

## Root-cause chain (each step verified 2026-07-06, slot-2)

1. **The canonical `_index/availability_index.parquet` in `instruments-store-pred-prd` carries `instrument_count` as
   STRING for all 24,994 rows** (verified by direct read; ManifestRow declares it `int`). The file's content is frozen
   at date ≤ 2026-06-27.
2. **The manifest consolidator rewrites that file every minute preserving/producing the string typing** — verified live:
   index mtime tracks the every-minute cron; a forced non-legacy run (`…-instruments-prediction-ltbf9`) rewrote it
   06:28:42Z, still all-string.
3. **The UTL `ManifestWriter` read-merges the canonical with its own int-typed rows** → object column with mixed str+int
   → `merged.to_parquet(...)` raises `ArrowTypeError("Expected bytes, got a 'int' object", column instrument_count)`
   (full traceback captured via a logging shim — the shard-isolation catch swallows it).
4. → **`is-daily-enum-prediction` failed daily 07-01→07-06** (6 consecutive exit-1 runs, ~30 min each); prediction
   by_date starved: 2,193 ids on 06-30 → 0 files 07-03/07-05 → 3 ids 07-06; catalogue `available_from` frozen at 06-27.

## Why nothing alerted (three masking layers)

- The **catalogue** §7.3 liveness correctly refuses to delist on thin/absent days → catalogue jobs stayed green.
- The catalogue's **`CATALOGUE_STALE_BY_DATE`** feed-health warn was blinded by prediction's FUTURE-dated `day=`
  partitions (settlement-dated dirs out to 2029 make `max(day)` never look old). Fixed: clamp to `day <= today`
  (instruments-service, shipped with regression test).
- **Cloud Run jobs ship almost no app logs to Cloud Logging** (only "Container called exit(1)") AND the UTL
  shard-isolation catch (`service_framework/_adapter.py` "Handler %s failed on payload") logs WITHOUT `exc_info` — the
  crash was invisible without a local repro + logging shim.

## Fixes shipped 2026-07-06

- [x] [CODE] P0. UTL write-side schema enforcement: `_merge_dataframes` coerces `instrument_count` / `schema_version` /
      `row_count` to nullable Int64 before every index/shard write — a dtype-divergent co-writer can never crash the
      capture path again. Verified against the exact poisoned prod frame (24,994-row merge + `to_parquet` OK). —
      unified-trading-library@<pending quickmerge sha, see progress log>
- [x] [INFRA] P1. Paused `uts-prod-manifest-consolidator-instruments-prediction-legacy-cron` — prediction ran BOTH
      legacy and non-legacy consolidators every minute (racing co-writers on one file); cefi/defi/tradfi paused their
      legacy variants 2026-06-08, prediction was missed. (Reversible: `gcloud scheduler jobs resume …`.)
- [x] [VERIFY] P0. Local healing run of the exact capture command on the fixed UTL → green + today's universe restored
      (see progress log for run evidence).
- [x] [CODE] P1. Catalogue feed-health clamp (`_warn_coverage_horizon` ignores future-dated days) + regression test —
      instruments-service (shipped with the same-day batch).

## Remaining (this issue's open work)

- [ ] [CODE] P1. **Fix the consolidator's dtype handling at ITS source** (it should persist schema-typed columns, not
      utf8) — locate the consolidator image/repo (manifest-consolidator SSOT:
      `codex/05-infrastructure/manifest-consolidator-ssot.md`), find where 2026-06-27-era changes began string-typing
      `instrument_count`, fix + redeploy. The UTL coercion makes this non-urgent but the canonical index dtype should be
      honest.
- [ ] [INFRA] P1. **Audit sports for the same double-consolidator condition** (`…instruments-sports-legacy` also shows
      recent every-minute runs) + pause its legacy cron if confirmed; verify sports capture/index dtype health.
- [ ] [INFRA] P1. Get the fixed UTL into the `is-daily-enum-*` Cloud Run image: UTL base republish → instruments-service
      pin bump → image rebuild (the dependency-update fan-out chain; manual short-circuit is the 07-04 recipe). Until
      then the 13:30 UTC cloud run may still fail — the local heal covers today; verify tomorrow's run.
- [ ] [VERIFY] P1. Backfill check for the missed window 07-01→07-06: confirm the healed capture's `--days-back` reach
      covers the gap days' by_date + manifest rows, or run a targeted backfill; then confirm the catalogue picks up
      post-06-27 listings (`max(available_from)` advances) on the next daily run.
- [ ] [CODE] P2. Observability: add `exc_info=True` to the UTL shard-isolation catch (`_adapter.py`) and root-cause why
      Cloud Run job stdout/stderr does not reach Cloud Logging (affects every lifecycle-catalogue/enum job — the
      2026-07-04 cefi/prediction weekly-full diagnoses also had to work blind).

## ROOT CAUSE #2 (2026-07-06, found after the ArrowTypeError fix unmasked it) — cefi KALSHI-PERP adapter filter broken

> **CORRECTION (2026-07-06, deeper verification — supersedes the "misrouting" mechanism below).** `KALSHI-PERP` /
> `POLYMARKET-PERP` are REAL, intended cefi venues (Kalshi launched CFTC-regulated crypto perpetual futures 2026-05-29;
> dedicated `reference_data/adapters/cefi/kalshi_perp.py` + `polymarket_perp.py`, UAC `VENUES_BY_ASSET_GROUP["cefi"]`
> members, unit tests — added by 4da6fe8). The bug is NOT prediction-record misrouting; it is that the `kalshi_perp`
> adapter's Kalshi `/markets?category=Crypto&status=open` filter is **completely ineffective**: classified 25,473
> catalogue rows, **0 are crypto perps** (`KXBTC…-PERP` etc.), **100% are general Kalshi EVENT contracts** —
> `KXMVESPORTSMULTIGAMEEXTENDED` (21,187) + `KXMVECROSSCATEGORY` (4,286) — all stamped `instrument_type=PERPETUAL`,
> venue `KALSHI-PERP`, written into the cefi store. So the confirmed defect is "the crypto-perp adapter ingests the
> whole Kalshi event universe and mislabels it PERPETUAL." The cefi-contamination CONCLUSION below stands; the mechanism
> is the broken adapter filter, not a prediction misroute. **STILL OPEN (do not act on as settled): whether the
> prediction KALSHI/POLYMARKET "0 records after filtering" is caused by these markets being claimed by the -PERP path,
> or is an independent prediction-enum issue — the heal run also wrote 7,981 records across 63 prediction sub-venue
> groups, so prediction is NOT fully starved; needs one more focused pass before a fix is chosen.**

> **DEFINITIVE ROOT CAUSE (2026-07-06, confirmed via live Kalshi API probe + Kalshi docs — supersedes the "broken
> filter" note above).** The `kalshi_perp` adapter is pointed at the **WRONG KALSHI API HOST ENTIRELY.** It queries
> `https://api.elections.kalshi.com/trade-api/v2/markets` — the **events** host, which serves ONLY binary event
> contracts. Live probe of 3,000 markets across all crypto series (KXBTC "Bitcoin range", KXBTCD, KXETHD …): **100%
> `market_type=binary`, 0 tickers containing "PERP"** — every "crypto" market there is a dated binary strike bet
> (`KXBTC-26JUL0605-T71799.99`), NOT a perpetual. Kalshi's actual perpetual futures ("Perps"/"margin") live on a
> SEPARATE host + namespace (Kalshi docs): **`https://external-api.kalshi.com/trade-api/v2/margin/`** (demo
> `external-api.demo.kalshi.co`), tickers like `BTC-PERPETUAL`, funding via `/margin/funding_rates/*`, **auth
> required**, and **"rolling out member by member."** The adapter's `category=Crypto` URL param is ignored by the events
> endpoint (markets carry `category: null`), and the client-side filter passes empty-category rows → it emits the entire
> binary event universe as fake PERPETUAL. **The fix is a repoint to the margin API, which is gated on Kalshi
> perps/margin API ACCESS + CREDENTIALS (member-rollout + API key) — an operator/credentials question, not a pure code
> fix.** See the OPERATOR DECISION block below.

The healed run (all writes green) exposed the DEEPER regression: the prediction records are being written to the WRONG
STORE under the WRONG venue/type.

- The heal run fetched a healthy universe (KALSHI 3,458 / POLYMARKET 7,577 after date filter) but wrote **0 records
  under prediction venues** ("Shard completeness: fetched OK but 0 records after filtering: ['KALSHI','POLYMARKET']" →
  `SOURCE_RETURNED_ZERO empty_confirmed` honest-absence rows — WRONG absence, the data exists).
- The records went to the **CEFI instruments store** instead: e.g.
  `instruments-store-cefi-prd/…/day=2026-07-05/venue=KALSHI-PERP/instruments.parquet` — 2,000 Kalshi SPORTS EVENT
  CONTRACTS (`KXMVESPORTSMULTIGAMEEXTENDED-…`) typed **PERPETUAL**.
- **cefi catalogue contamination: 25,473 `KALSHI-PERP` rows** (6.8% of 376,984), `available_from` 2026-06-27→07-05 —
  i.e. contaminating since the producer change landed, and a large share of the "weekend cefi growth" observed in the
  incremental-catalogue verification was THIS, not organic listings. Mitigation: **0 rows are MVP-tagged** (MVP views
  - MVP-scoped downloads unaffected); 2,000 currently active.
- **Suspect commit: instruments-service@4da6fe8** "feat: consolidate IS cefi/tradfi/prediction venue producers to UAC
  (named Tardis grain-adapter; delete \_CEFI/\_TRADFI mirrors); **enable KALSHI-PERP/POLYMARKET-PERP enumeration** +
  canonical venue casing" — landed in the exact regression window; the enabled PERP venue keys route the prediction
  fetch's records into cefi per-venue bucket routing.
- Timeline coherence (write-times, NOT `day=` partitions): 4da6fe8 authored **2026-06-29 08:46 UTC**; the FIRST
  contaminated production write was the 06-29 13:30 UTC enum run (object `day=2026-06-27/venue=KALSHI-PERP` written
  **2026-06-29T13:40Z** — the `day=` floor is just how far `--days-back` reached, NOT the ship date; commit reached the
  deployed `:latest` and ran in prod same-day, ~5h after authoring). Every 13:30 run since re-wrote KALSHI-PERP into
  cefi and those writes SUCCEEDED (cefi index is not string-poisoned), so cefi accumulated ~9 days of contamination
  while the SAME run's prediction-store write began dying on the ArrowTypeError 07-01 (root cause #1). Two independent,
  same-day-shipped failures — the second masking the first. **Corrected span: contamination = 06-29→07-06 daily runs**
  (earlier "since 06-27" was the logical partition floor, not the write date).

### OPERATOR DECISION REQUIRED (Ikenna) — KEEP the venues, fix the adapter (operator: "don't remove, correct them")

Operator instruction 2026-07-06: KALSHI-PERP/POLYMARKET-PERP are intended trading venues — KEEP them, correct the
adapter. Given the definitive root cause (wrong host; real perps need the **auth'd, member-rollout margin API**), the
"correct them" work splits into an immediate mitigation (agent can do now) + a real fix (gated on access):

**Immediate mitigation — RECOMMENDED, agent-executable now (venue stays declared):**

1. `kalshi_perp`/`polymarket_perp` adapters: **stop emitting binary event markets as perps.** Minimal correctness fix —
   the `_parse_market` empty-category "pass" is wrong; until repointed, the adapter must return **0** records (there are
   genuinely no perps on the events host). Stops the daily contamination at source; the UAC venue declaration stays
   (venue remains a valid trading target, just with an empty reference-data feed until repointed).
2. Purge the 25,473 fake `KALSHI-PERP` rows from the cefi catalogue (documented corrective:
   `--mode full --allow-catalogue-shrink` cefi run + by_date/manifest cleanup of `venue=KALSHI-PERP` cells). 0 are MVP.

**Real fix — the actual "correct them," GATED ON OPERATOR INPUT (credentials/access):** repoint the adapter to the
margin API `https://external-api.kalshi.com/trade-api/v2/margin/…` (perps host; tickers `BTC-PERPETUAL`; funding via
`/margin/funding_rates/*`). Two open questions ONLY the operator can answer:

- **Q1 (access):** do we have a Kalshi account **enrolled in the perps/margin member rollout** with an API key that has
  margin access? (Docs: "rolling out member by member"; margin API mirrors the event API's RSA-PSS auth — so it is NOT
  the public no-auth path the current adapter assumes.) If NO → the real fix is BLOCKED-CREDENTIALS; build the repointed
  adapter scaffold against demo `external-api.demo.kalshi.co` + status the venue pending-access.
- **Q2 (scope):** POLYMARKET-PERP — **ANSWERED (web research 2026-07-06): Polymarket perps ARE real.** Launched
  2026-04-21, beta live 2026-05-28 for a RESTRICTED set of legacy/high-activity users; up to 20x leverage, isolated
  margin, long/short any market continuously. So POLYMARKET-PERP is the SAME class as Kalshi: a real intended venue on a
  perps API the current `polymarket_perp` adapter is almost certainly NOT pointed at, beta-gated on access. Needs the
  same repoint + access check against `docs.polymarket.com` perps API. (Sources: bitcoin.com, cnbc.com, marketplace.org
  2026-04/05.)

### demo→prod switch cost (answers "what changes if we build against demo first")

Built correctly, the demo→prod switch is **config + credentials + enrollment — ZERO adapter code change.** Concretely:

1. **Host** — the ONLY deliberate change: `external-api.demo.kalshi.co` → `external-api.kalshi.com`. Today both perp
   adapters hardcode a module const (`_KALSHI_BASE_URL`); make it config-driven (a single `KALSHI_PERP_ENV=demo|prod`
   resolving the host) so the flip is one config value.
2. **Credentials** — demo and prod are SEPARATE Kalshi accounts with SEPARATE RSA keypairs; only the injected credential
   blob / Secret-Manager reference changes (`kalshi-perp-demo` → `kalshi-perp-prod`). The signing CODE is identical
   RSA-PSS and ALREADY EXISTS in `adapters/prediction/kalshi.py` (`_signed_headers`/`_parse_kalshi_creds`/`_can_sign`,
   blob `{api_key_id, private_key}`) — reuse it; the current `kalshi_perp` adapter does public no-auth reads and must
   GAIN this signing regardless of demo/prod.
3. **Member-rollout access** — prod "rolls out member by member": even with prod host+creds, the account must be
   enrolled or the margin endpoints 403. This is the real gate, and it is NOT testable in demo. (Same for Polymarket's
   restricted beta.)
4. **Data-universe divergence (the trap)** — demo serves synthetic/limited markets; the demo instrument universe ≠ prod.
   Demo validates the PLUMBING (auth, pagination, parse, schema→InstrumentRecord, catalogue integration) but demo
   markets MUST NOT land in the prod cefi store/catalogue. Capture demo into a non-prod store (or a dry-run) and
   re-enumerate against prod before the catalogue trusts KALSHI-PERP/POLYMARKET-PERP.
5. **Ancillary** — WS + FIX use separate perps hosts (Kalshi docs); irrelevant to reference-data enumeration, only if we
   later stream.

Net: scaffold against demo now to prove auth+parse+schema; the prod cutover is a config flip + prod key + enrollment
confirmation, with a mandatory prod re-enumeration before downstream trust. No throwaway work.

This touches ANOTHER WORKSTREAM's feature commit (4da6fe8); the slot-2 agent will make ONLY the contamination-stopping
mitigation + purge on approval, and leave the margin-API repoint to be done with the credentials answer + the 4da6fe8
author in the loop.

## EXECUTION PLAN — KALSHI-PERP / POLYMARKET-PERP correction (demo-first, prod cutover gated on access)

Operator direction 2026-07-06: build against Kalshi/Polymarket DEMO endpoints now; live-market access unknown (Ikenna
holds that answer) → prod cutover is a later, credentials-gated flip. Concrete endpoint confirmed:
`GET https://external-api.demo.kalshi.co/trade-api/v2/markets/margin` → `MarginMarket[]`
(`ticker`,`contract_type`,`underlying`,`strike_price`,`expiration_time`,`is_active`,`contract_size`,`tick_size`,
`leverage_estimate`). Purge scope confirmed: **KALSHI-PERP 25,473 rows; POLYMARKET-PERP 0** (its adapter never
contaminated). All 0 MVP.

### Phase 0 — stop contamination + purge (NOW, no access needed)

- [ ] [CODE] P0. Guard both `kalshi_perp` + `polymarket_perp` adapters to emit **0 records** from the current (wrong,
      events) host until repointed — fix the `_parse_market` empty-category "pass" bug. Ship (QG + quickmerge) + image
      rebuild so the 13:30 UTC cloud run stops writing fake perps. Venue declarations STAY. Gate: next cefi daily run
      writes 0 `KALSHI-PERP` rows.
- [ ] [DATA] P0. Purge the 25,473 fake `KALSHI-PERP` rows from cefi: corrective `--mode full --allow-catalogue-shrink`
      cefi run + delete the `venue=KALSHI-PERP` by_date + manifest cells. Gate: cefi catalogue has 0 `KALSHI-PERP` rows,
      row-count drop == 25,473, no other venue touched. **PURGE, not MOVE (operator Q 2026-07-06 — decided):** these are
      not merely misfiled — the perp adapter parsed them through the WRONG schema (`instrument_type=PERPETUAL`,
      `expiry=None`) whereas they are binary EVENT contracts that have expiries + event/series structure + YES/NO
      settlement the perp parser discarded. They are reference-data rows (no captured prices/trades — nothing
      irreplaceable), the correct producer is the prediction Kalshi adapter into the prediction store, and Kalshi is
      cheaply re-enumerable — so moving would relocate degraded stubs AND duplicate/conflict with the prediction store's
      canonical copies. Purge; let the correct producer re-capture. (The "are these markets captured anywhere
      correctly?" question the move-instinct surfaces is folded into Phase 3.)

### Phase 1 — foundation: config-drive host + shared RSA-PSS auth (no access needed)

- [ ] [CODE] P1. Make the perp base URL config-driven — `KALSHI_PERP_ENV=demo|prod` (via `UnifiedCloudConfig`, default
      `demo`) resolving the host; delete the hardcoded `_KALSHI_BASE_URL` events-host const from the perp adapters.
      Gate: unit test resolves demo vs prod host.
- [ ] [CODE] P1. Extract the RSA-PSS signing that ALREADY EXISTS in `adapters/prediction/kalshi.py`
      (`_signed_headers`/`_parse_kalshi_creds`/`_can_sign`) into a shared helper both perp adapters use; wire the demo
      credential blob via the injection path (secret ref `kalshi-perp-demo`). Gate: signed-header unit test.

### Phase 2 — repoint kalshi_perp to the margin API (demo)

- [ ] [CODE] P1. Rewrite `KalshiPerpReferenceDataAdapter.get_instruments` to hit `…/trade-api/v2/markets/margin` on the
      demo host, parse `MarginMarket` → `InstrumentRecord(instrument_type=PERPETUAL)` (ticker; `underlying`→base_asset;
      `contract_size`/`tick_size`; `is_active`→status; `expiry=None` — perps are continuous), status-filter active.
      Gate: parses a captured demo `MarginMarket` fixture.
- [ ] [VERIFY] P0. Demo dry-run: returned tickers are genuine perps (`BTC-PERPETUAL` shape, `contract_type` present),
      **0 event contracts**. Capture into a NON-PROD / dry-run sink — demo data MUST NOT enter the prod cefi store.
      Gate: demo run yields real perp instruments; a `KXMVE*` event ticker would be rejected.

### Phase 3 — polymarket_perp repoint (demo) + prediction Kalshi/Polymarket event-capture gap

- [ ] [RESEARCH] P1. `docs.polymarket.com` perps API — find the markets-listing endpoint + auth (beta-gated; launched
      2026-04-21). Gate: endpoint + auth documented in this issue.
- [ ] [CODE] P1. Repoint `polymarket_perp` against Polymarket's perps API (demo/testnet if available) →
      `InstrumentRecord(PERPETUAL)`. Gate: demo returns real Polymarket perps, 0 prediction-market rows.
- [ ] [VERIFY] P1. **Pin the prediction-store event-capture gap (surfaced by the purge-vs-move question 2026-07-06).**
      The KALSHI-PERP contamination is the DUPLICATE-in-the-wrong-place symptom; the real question the move-instinct
      raised is whether these Kalshi/Polymarket EVENT markets (`KXMVESPORTSMULTIGAMEEXTENDED`,`KXMVECROSSCATEGORY`, …)
      are captured CORRECTLY in the PREDICTION store at all. Evidence to resolve: the healed prediction enum wrote 0
      records under top-level venues `KALSHI`/`POLYMARKET` ("0 records after filtering") but 7,981 across 63 sub-venue
      groups — so it is unclear whether the full Kalshi/Polymarket event universe lands in prediction. Diff the
      prediction store's KALSHI/POLYMARKET instrument set vs the live Kalshi `/markets` (events host) + Polymarket CLOB
      universe. Gate: quantified — either "prediction captures them, purge loses nothing" (close), OR a named coverage
      gap (`N` markets missing) → file the fix in the PREDICTION Kalshi/Polymarket adapter (NOT by relocating the
      malformed cefi rows). This is the correct home for these markets; the perp path is not.

### Phase 4 — prod cutover (BLOCKED-OPERATOR-DECISION / -CREDENTIALS — Ikenna)

- [ ] [OPERATOR] P1. Confirm Kalshi + Polymarket perps **prod access** (Kalshi member-rollout enrollment; Polymarket
      beta enrollment) + provide prod credential blobs (`kalshi-perp-prod`, `polymarket-perp-prod`). BLOCKED until
      answered.
- [ ] [INFRA] P1. Flip `KALSHI_PERP_ENV=prod` + prod secret refs; confirm no 403 (enrollment live); **re-enumerate
      against prod** → prod cefi catalogue. Gate: prod perps land as genuine `PERPETUAL` crypto perps; `KALSHI-PERP`/
      `POLYMARKET-PERP` catalogue rows are real (spot-check tickers).

### Phase 5 — guardrail so this class can't recur

- [ ] [CODE] P2. Write-time validation: any `*-PERP` venue record MUST be `instrument_type=PERPETUAL` AND pass a
      perp-ticker sanity check (reject event-contract patterns, e.g. `KXMVE*`/`KXMVECROSSCATEGORY*`); reject at the
      writer, not silently. Gate: a synthetic event contract injected into a `-PERP` feed is rejected, not written to
      the catalogue.

> **Coordination:** all of the above touches 4da6fe8 (another workstream's feature). The operator has directed this
> correction; slot-2 will execute Phases 0–3 + 5 and flag the 4da6fe8 author on the PR; Phase 4 waits on Ikenna's access
> answer. Repos: instruments-service (adapters) + config (host/secret) — no UAC venue-list change (venues stay
> declared).

## Progress log

- 2026-07-06: Found during the incremental-catalogue plan's weekend verification (catalogue rows green but prediction
  `max(available_from)` frozen at 06-27 → pulled the thread). Root cause chain verified end-to-end; UTL coercion fix
  written + verified on the poisoned prod frame; legacy consolidator cron paused; local healing capture + UTL quickmerge
  in flight (evidence appended when green). Operator notified in-session.
