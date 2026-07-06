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
related:
  [
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md,
  ]
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

> **This doc is the RECORD — root-cause evidence, contamination timeline, the demo→prod cost analysis, and the
> operator-decision context. All actionable `- [ ]` remediation was moved to the plan (2026-07-06), which references
> this doc for the diagnosis:**
> [`plans/active/prediction_capture_incident_remediation_2026_07_06.md`](../prediction_capture_incident_remediation_2026_07_06.md).

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

## Fix status (record — tracker is the plan)

**Root-cause-#1 fixes are tracked as Workstream A of the plan** →
[`prediction_capture_incident_remediation_2026_07_06.md`](../prediction_capture_incident_remediation_2026_07_06.md).
Shipped 2026-07-06: UTL write-side dtype coercion (Int64/bool/float) unified-trading-library@6c090bb + @1651340; legacy
prediction consolidator cron paused; catalogue feed-health future-date clamp instruments-service@4979429; local healing
run green (universe restored to 07-06). Residual open work (consolidator dtype-at-source, sports double-consolidator
audit, fixed-UTL→image, missed-window backfill, `exc_info` observability) lives as the plan's Workstream A `- [ ]` items
— not duplicated here.

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

### Operator decision + open questions (record — the actions are the plan's Phase 0–4)

Operator instruction 2026-07-06: KALSHI-PERP/POLYMARKET-PERP are intended trading venues — **KEEP them, correct the
adapters** (don't remove). Given the definitive root cause (wrong host; real perps need the auth'd, member-rollout
margin API), the correction is an immediate agent-executable mitigation (guard both adapters to emit 0 + purge the
25,473 fake rows) plus a real repoint to the margin API gated on access. **Those actions are tracked in the plan** —
Phase 0 (mitigation + purge), Phases 1–3 (demo repoint), Phase 4 (prod cutover). Two questions only the operator can
answer:

- **Q1 (access) — OPEN:** do we have a Kalshi account **enrolled in the perps/margin member rollout** with an API key
  that has margin access? (Docs: "rolling out member by member"; the margin API mirrors the event API's RSA-PSS auth —
  so it is NOT the public no-auth path the current adapter assumes.) If NO → the real fix is BLOCKED-CREDENTIALS, but
  the demo scaffold (plan Phases 1–3) proceeds regardless against `external-api.demo.kalshi.co`.
- **Q2 (scope) — ANSWERED (web research 2026-07-06): Polymarket perps ARE real.** Launched 2026-04-21, beta live
  2026-05-28 for a RESTRICTED set of legacy/high-activity users; up to 20x leverage, isolated margin, long/short any
  market continuously. So POLYMARKET-PERP is the SAME class as Kalshi: a real intended venue on a perps API the current
  `polymarket_perp` adapter is almost certainly NOT pointed at, beta-gated on access. Same repoint + access check
  against `docs.polymarket.com`. (Sources: bitcoin.com, cnbc.com, marketplace.org 2026-04/05.)

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

## Remediation → the plan (record)

The full demo-first correction (Phase 0 mitigation + purge → Phases 1–3 demo repoint → Phase 4 prod cutover → Phase 5
guardrail) is tracked as **Workstream B** of
[`plans/active/prediction_capture_incident_remediation_2026_07_06.md`](../prediction_capture_incident_remediation_2026_07_06.md).
Reference facts the plan builds on (kept here as the record): confirmed demo endpoint
`GET https://external-api.demo.kalshi.co/trade-api/v2/markets/margin` → `MarginMarket[]`
(`ticker`,`contract_type`,`underlying`,`strike_price`,`expiration_time`,`is_active`,`contract_size`,`tick_size`,
`leverage_estimate`); purge scope **KALSHI-PERP 25,473 rows; POLYMARKET-PERP 0** (its adapter never contaminated), all 0
MVP; coordination — the correction touches 4da6fe8 (another workstream's feature), so slot-2 flags that author on the PR
and Phase 4 waits on Ikenna's access answer.

## Progress log

- 2026-07-06: Found during the incremental-catalogue plan's weekend verification (catalogue rows green but prediction
  `max(available_from)` frozen at 06-27 → pulled the thread). Root cause chain verified end-to-end; UTL coercion fix
  written + verified on the poisoned prod frame; legacy consolidator cron paused; local healing capture + UTL quickmerge
  in flight (evidence appended when green). Operator notified in-session.
