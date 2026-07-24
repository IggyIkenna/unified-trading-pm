---
doc_type: plan
title:
  Prediction cross-venue arb detection + honest-coverage correctness — extracted history (2026-06-20 through 2026-06-24
  fully-closed sessions)
summary: >-
  Archive-bound extraction of thirteen fully-closed, dated Progress Log entries (2026-06-20 through 2026-06-24) from
  /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md, split out purely to bring that wave-1 child plan
  back under its 1000-line size cap. Content is verbatim and historical only -- covers the Kalshi historical-
  enumeration root-cause + bulk-seed converter (2026-06-20), the Polymarket v9 re-walk CF-11 phantom-row fix + manifest
  hygiene verification (2026-06-21), the P0 honest-coverage lifecycle root-cause + 43a/43b/43c fix chain, the P1 Kalshi
  cqg-grouping enumeration-flood root-cause + series-scoped fix, and the P1 fixture-parser real-sample spec +
  REAL-ticker verification (2026-06-23), and the live arb-detector VM launch/Slack-pager/two-axis-canonical-
  scheme/consolidated-handoff sessions (2026-06-24). Every checkbox extracted here was already `[x]` in the parent
  before extraction -- no open work moved. Zero open todos here -- this file is a record, not a work queue.
status: complete
nature: record
asset_group: [prediction, cefi]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags:
  [
    prediction,
    kalshi,
    polymarket,
    arb,
    cross-venue,
    honest-coverage,
    cqg,
    backfill,
    manifest,
    history,
    archive-bound,
    progress-log,
  ]
related: [/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  extracted 2026-07-24 from /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md to bring that plan under
  its 1000-line line-cap (plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 23 tail item)
---

# Prediction cross-venue arb detection + honest-coverage correctness — extracted history

> **Archive-bound record, not a work queue.** This file holds thirteen verbatim, fully-closed dated Progress Log entries
> (2026-06-20 through 2026-06-24) extracted from the parent plan's history so the parent could get back under its
> line-count cap. No open todos exist in this file -- every checkbox below was already `[x]` in the parent. Entries
> dated 2026-06-20 through 2026-06-24 that still carried an open `- [ ]` todo were LEFT IN the parent (not extracted)
> since this file is complete-only. See `/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` for the
> live plan.

## Extracted Progress Log entries

### 2026-06-24 (autonomous /autonomous) — arb → #paper-trading-alerts Slack pager SHIPPED (operator: "where does the arb alert come in… paper alerts slack is a good candidate")

The detector now PAGES on a real opportunity, not just silent-to-GCS. Shipped **features-service@295b3f83**:

- `app/prediction_arb_slack.py` (NEW) —
  `post_arb_alert(arbs, now, cooldown_state, *, cooldown_seconds=3600, webhook=None)`: pages `#paper-trading-alerts` on
  **freshly-flagged PURE_ARB** rows (a top-of-book crossing = the actionable signal), per-pair **1h cooldown** so a
  persistent arb pages once/hour not every tick; QUOTABLE-only ticks never page (counted in the message body only).
  Webhook resolves from the channel-locked SM secret `agent-orchestrator-paper-trading-slack-webhook` via cloud-agnostic
  `get_secret` (cached, **best-effort** — a Slack/SM failure logs a warning and never disturbs the loop; the GCS arb
  store stays the durable record). Same channel
  - webhook `paper_engine.py` uses, so prediction arbs land in the operator's existing paper-trading alert stream.
- `app/cross_venue_arb_runner.py` — wired `post_arb_alert` into `run_live_loop` (per-pair `alert_cooldown` dict persists
  across ticks; `total_slack_paged` added to cumulative totals).
- `tests/cross_instrument/unit/test_prediction_arb_slack.py` (NEW, 4 tests) — PURE pages once then cooldown; QUOTABLE
  doesn't page; no-webhook best-effort skip; empty no-page. QG-green (296s, sentinel-verified) before quickmerge.

Note: shipping was briefly blocked by a **live peer's** uncommitted UTL `cloud_interface/providers` WIP (the
`get_blob_metadata.last_modified` catalog-false-positive fix, UTL@7906df7a — directly the catalog-staleness root cause
filed below); PROTECTED it (mtime <120s = live editor), waited for the peer to commit, then quickmerged. Next: rebuild
the PREDICTION tarball + relaunch the detector VM so the pager goes live (the running VM 150427 predates this).

### 2026-06-24 (autonomous /autonomous) — DETECTOR CODE SHIPPED (features-service@ef7cd58c); VM launcher + 24h run next

Built the LIVE cross-venue arb DETECTOR in its canonical home (features-service `cross_instrument`), reusing the shipped
`run_prediction_cross_venue_dispersion` (book dispatch → matcher → align → kernel) UNCHANGED. Shipped
**features-service@ef7cd58c** (QG-green, quickmerge→LDR, Tier-C drains to staging):

- `app/calculators/prediction_arb_fee_model.py` — versioned public fee model (`FEE_MODEL_VERSION=v1_public_2026_06`;
  Kalshi `0.07·P·(1−P)` per-share, Polymarket 0% today). Stamped on every arb-store row.
- `app/calculators/cross_venue_arb_detector.py` — pure taxonomy kernel: PURE_ARB (raw_edge=xv_best_edge>0, bid×offer) /
  QUOTABLE_ARB (both two-way, mid_dispersion>threshold), `net_edge_after_fees`, `is_executable`, honest-skip
  one-sided/no-signal (no row). `summarise_detection` → truthful counters (two-way-on-both ticks, PURE/QUOTABLE,
  mid-disp distribution).
- `app/cross_venue_arb_runner.py` — recent-day scan + dedup-latest-per-pair + append-only GCS arb store
  (`features-cross-instrument` pred bucket, `cross_venue_arb/by_date/day=…/tick=…/opportunities.parquet`, via
  `resolve_bucket` + `upload_bytes`) + the live poll loop (SIGTERM-graceful, shard-isolated ticks, heartbeat log
  `ARB_DETECT_TICK`, `max_duration` bound).
- `cli/handlers/arb_detect_handler.py` + `cli/main.py` — new
  `--operation arb-detect --mode batch|live --asset-group PREDICTION` (batch=live: batch runs one tick, live loops). 24
  unit tests (fee math / taxonomy / honest-absence / scan+dedup / store-write / bounded-loop).

**LIVE-DATA STATE (verified on real GCS, this session):** all 4 `prediction-live-*` VMs are RUNNING and BOTH venues'
`book_snapshot_5` is FRESH (Kalshi + Polymarket writes at 11:37Z, 2026-06-24). The detector reads the live book feed —
ready to run.

- [x] ✅ [SCRIPT] P0. **Detector VM launcher (deployment-service)** — SHIPPED deployment-service@e9f7092:
      `launch-prediction-arb-detector.sh` (LONG_LIVED_LIVE, e2-standard-4, singleton-locked) running
      `python -m features_service.cross_instrument --operation arb-detect --mode live --asset-group PREDICTION`;
      `prediction-arb-detect` VM_TASK dispatch in `setup-data-pipeline-vm.sh`; `prediction-arb-detector-` prefix in
      `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET` (bucket=None heartbeat-only, LONG_LIVED_LIVE → classified LIVE) +
      `launcher_registry.py`. Also fixed two peer lint regressions in `vm_zombie_watchdog.py` that were fleet-blocking
      every deployment-service quickmerge (botched-TID251 F821 `storage` annotation + ambiguous unicode). — e9f7092.
- [x] ✅ [OPS] P0. **Detector VM LAUNCHED + RUNNING the live loop (verified on-VM 2026-06-24).** VM
      `prediction-arb-detector-20260624-134310` (e2-standard-4, asia-northeast1-c) —
      `arb-detect: live loop START interval=600s scan_days=3 max_duration=0s` then `ARB_DETECT_TICK` firing every tick.
      **REAL NUMBERS (live + the batch smoke):** matcher = **8,932 Kalshi↔Polymarket cross-venue mappings**
      (day=2026-06-23); **two_way_on_both = 0, PURE_ARB = 0 (raw+net), QUOTABLE_ARB = 0, executable = 0,
      mid_dispersion_max = 0.0000, GCS arb-store rows = 0** — a TRUTHFUL honest-zero: the binding gate is the
      thin/one-sided Polymarket-crypto book liquidity (no two-sided liquid OVERLAP with Kalshi's rich crypto books) +
      IS-catalogue staleness for the current UTC day (the detector survives it via the `--scan-days 3` trailing window;
      the trades producers don't — see the IS-catalogue P0). The pipeline streams correctly + the store is the
      opportunity tape (writes nothing on 0 crossings, honest absence); it will flag + persist the instant a two-sided
      liquid overlap exists. Monitoring per the strict rules (run.log log-mtime + ARB_DETECT_TICK counter + exit_code;
      the launch took 5 attempts — each crash caught by no-fire-and-forget T+10 + fixed: wrong-module → committed
      dispatch; missing events topic → created; events-topic IAM → UTL best-effort lifecycle (5011dbc9); handler
      VALIDATION\*\* PubSub publish → removed; tarball-overwrite race → committed so fleet rebuilds converge).
      Provenance: on-VM verify 2026-06-24.
- [x] ✅ [OPS] P1. **Promoted to long-lived** — it launched AS the permanent service: `LONG_LIVED_LIVE` lifecycle
      (`launch-prediction-arb-detector.sh`, `VM_SHUTDOWN_ON_COMPLETION=false`, `max_duration=0` = runs indefinitely),
      classified **LIVE** (`prediction-arb-detector-` in `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET` →
      `classify_deployment_target`), watchdog-registered (heartbeat-only) + launcher-registry-mapped, and
      health-surfaced via `deployment_heartbeat` (DEPLOYMENT_STARTED/PROGRESS → deployment-observability + Slack). It
      just runs + appends to the GCS arb store.

- [x] [UAC] P2. **Lift public Kalshi/Polymarket prediction trading fees into UAC capability declarations** — the
      detector uses a documented versioned constant (`prediction_arb_fee_model.py`) because UAC's
      `internal/reference/fee_schedule.py` carries only per-client/execution fees, no public per-venue prediction
      trading fees. Wire a UAC accessor + point the detector at it (bump `FEE_MODEL_VERSION`). Repo:
      unified-api-contracts + features-service. Provenance: detector build 2026-06-24. ✅ UAC@4601e242 +
      features@909368a4 — `venue_fee_model.py` added to UAC canonical predictions domain
      (`KALSHI_FEE_COEFF=0.07, POLYMARKET_FEE_FRACTION=0.0, PREDICTION_VENUE_FEE_MODEL_VERSION, kalshi_fee/polymarket_fee/net_edge_sell_*`).
      Exported from `unified_api_contracts.predictions`. `prediction_arb_fee_model.py` deleted;
      `cross_venue_arb_detector.py` imports from UAC directly. `FEE_MODEL_VERSION` kept as an alias constant (same
      value) via PREDICTION_VENUE_FEE_MODEL_VERSION. QG green both repos. 2026-06-26.

### 2026-06-24 (autonomous /autonomous) — TWO-AXIS cross-venue canonical scheme SHIPPED (operator direction) — UAC@098d1698

Operator (2026-06-24) directed a **two-axis** cross-venue canonical scheme so overlap is measured COMPREHENSIVELY at the
underlying level (CRUDE_OIL is shared once PRICE_LEVEL-vs-UP_DOWN bet-type is stripped — 22 Kalshi / 18 Polymarket / 12
shared underlyings). SHIPPED `unified_api_contracts/canonical/domain/predictions/two_axis.py`:

- **Axis-1 = `PredictionUnderlying`** (57 categories:
  `crypto coins, SPX/NDX/RUT/DJIA, CRUDE_OIL/NATGAS/GOLD/SILVER/EUR, CPI/FED/GDP/NONFARM_PAYROLLS/PCE/PPI/TREASURY, WEATHER_TEMP, TRUMP/ELON/ELECTION, GEO_*, SPORTS_*`
  leagues, OTHER) — the semantic SUBJECT.
- **Axis-2 = `PredictionBetType`**
  (UP_DOWN/PRICE_RANGE/PRICE_LEVEL/MATCH/SPREAD/TOTAL/NRFI/PER_MONTH/APPROVAL_RATING/…).
- `CANONICAL_GROUP_TO_UNDERLYING` + `CANONICAL_GROUP_TO_BET_TYPE` — **comprehensive 97/97** cqg values mapped on each
  axis (a completeness test asserts `set(map) == set(CanonicalQuestionGroup)` so every future cqg MUST be categorized —
  no silent gaps). `underlying_for_group()`/`bet_type_for_group()` accessors + `cross_venue_underlying_overlap()` (→
  shared/kalshi_only/polymarket_only at Axis-1). Facade-exported (predictions + top-level). 10 tests; UAC QG-green.

This advances the cross-venue CATEGORIZATION layer of #684/#692 (every market categorizes at the underlying level, no
false pairs — Axis-1 is pure categorization, the arb-pairing layer decides bet-type+settlement compatibility
downstream). The **per-venue producibility + per-instrument arb-pairing** (which cqgs each venue actually lists, then
group by `(underlying, fixture/strike/print)` for the same-settlement arb pair) remains the downstream features/strategy
layer — tracked at #692 + the fixture-pairing residual #559.

> **🟢 IN-FLIGHT 2026-06-27**: 43d re-walk status (updated 07:52 UTC June 27):
>
> - **POLYMARKET re-walk v3**: `mtds-prediction-polyrewalk-20260627-075135` LAUNCHED 07:51 UTC (2025-03-14→2026-06-27,
>   --venue POLYMARKET, v0.89.0 tarball sha=aba6b129 — has actual CF-11 FetchEvidence fix ed4e35e0). Prior: v1
>   (`20260626-234137`) FAILED CF-11 at 01:14 UTC; v2 (`20260627-014254`) FAILED setup (uv pip install rc=2, wrong
>   tarball).
> - **KALSHI re-walk v2**: `mtds-prediction-kalshirewalk-20260627-075154` LAUNCHED 07:51 UTC (2021-06-30→2026-06-27,
>   --venue KALSHI, v0.89.0 tarball). Prior `20260626-234151` deployed v0.88.0 (sha=840a5996 = CI-only fix, NOT
>   FetchEvidence fix ed4e35e0) → FAILED CF-11 at 02:15 UTC.
> - **Root cause corrected**: progress log previously said FIX=`840a59963`. WRONG. sha=840a5996 is "downgrade node24
>   actions". Actual CF-11 fix = `ed4e35e0` "fix: supply FetchEvidence for SOURCE_RETURNED_ZERO rows". Both re-walk VMs
>   now use v0.89.0 which includes ed4e35e0.
> - **IS June 27 enumeration**: `instr-backfill-pred-20260627` COMPLETED 07:21 UTC — Kalshi OK (318 rows), Polymarket 0
>   BTC_UP_DOWN_DAILY (3:17 AM ET = too early). **RE-RUN SCHEDULED ~09:30 UTC** (launch IS --force again when Polymarket
>   has June 27 10am ET market listed).
> - **Arb detector**: `prediction-arb-detector-20260627-005823` RUNNING tick=40 @ 07:41 UTC, 0 pairs (June 27 Polymarket
>   BTC data not yet in IS; stale May 12 top-level parquet blocking fallback). Will show pairs after IS re-run.
> - **4 live prediction VMs**: all HEALTHY — Kalshi trades 10218 entries, Polymarket trades 148162 entries (07:51 UTC).

### 2026-06-24 (autonomous /autonomous) — P0 chain 43a/43b/43c SHIPPED + rule-11 GCS-verified; 43d operational pending

Drove the operator's #1 P0 honest-coverage-correctness chain to **code-complete + 5-repo QG-green + verified on real
GCS**. Ground-truth re-derivation (Grep-Then-Read) corrected the plan's stale prose: 43b was already substantially done
and 43c was PARTIAL (not OPEN). Shipped:

- **43c — coverage-math clip — SHIPPED** (UAC@ea9bfdd5 + UTL@c412a8ce + deployment-api@1390cc0). Root cause: UAC
  `compute_honest_coverage` gave out-of-life empties NUMERATOR CREDIT (the docstring's "credit == clip" is FALSE when
  failed/pending > 0). UAC already had `OUT_OF_COVERAGE_WINDOW_REASONS` but only `coverage.py` consumed it. Fix
  (back-compatible, default 0): `out_of_window` field on `CaptureStatusCounts` + clip in `compute_honest_coverage`;
  populated by UTL `read_capture_status_counts` (auto-fixes IS `/api/data-status` + the IS/mtds ratchet) +
  deployment-api `coverage_metrics`/`breakdowns_core`. **Rule-11 VERIFIED on real GCS** (212,636 rows): POLYMARKET
  95.28%→93.30% (49,665 clipped), KALSHI 81.50%→78.84% (5,521 clipped) — the intended out-of-life correction; ratchet is
  warn-only so no gate breaks.
- **43a — IS CLOB-history `available_from` enrich — SHIPPED** (instruments-service@0b2b944). Lift
  `accepting_order_timestamp`/`game_start_time` → `start_date` when no gamma creation field present. 4 tests.
- **43b — emission bounding already done in the v2 enumerator + a latent tardis TypeError FIXED**
  (market-tick-data-service@6003f512): `was_instrument_alive(venue=/instrument_id=/day=)` → correct
  `(available_from, available_to, day)` signature; + a pre-existing codex-gate os.environ exemption fix.
- **43d — operational re-walk LAUNCHED 2026-06-26** — POLYMARKET (`mtds-prediction-polyrewalk-20260626-234137`,
  2025-03-14→06-26, tarball 3043f2dc) + KALSHI (`mtds-prediction-kalshirewalk-20260626-234151`, 2021-06-30→06-26). Both
  RUNNING; consolidator merges per-VM shards after completion (~1-2h). SRZ reclassification with IS lifecycle (43b) +
  venue-aware (24db3f16) will reclassify within-bounds SOURCE_RETURNED_ZERO → `attempted_failed`. Tracked.

Multi-agent note: a concurrent "cockpit-agent" peer committed a deployment-api health-overview fix (9744cb6) and parked
my 43c WIP into a named stash — recovered intact (`git stash apply`) + shipped scoped to my 3 files; their work
untouched. Next: 43d operational + the operator's two-axis cross-venue canonical scheme (#559/#684/#692).

### 2026-06-24 — ⭐ CONSOLIDATED HANDOFF (AUTHORITATIVE — reconciles 3 overlapping dispatch snapshots vs ACTUAL LDR; git-verified)

Multiple autonomous dispatches carried conflicting/stale "ALREADY DONE" sections (one called my `UAC@3effe2fc` parser
"peer-built may exist"; one listed the cqg re-walk as still-to-do when its code fix already shipped). This is the SINGLE
source of truth — every "done" below is a git-verified ancestor-of-`live-defi-rollout`.

**✅ DONE + VERIFIED ON LDR (do NOT redo):**

1. **Kalshi cqg-CATEGORY canonicalization** (the KXMVE-flood fix) — `UAC classifiers.py` (`_kalshi_sports_group`,
   `KXRIPPLE→XRP`, `KXEURUSD` EUR-FX collision fix — 11 markers on LDR) + `IS kalshi.py` series-scoped enum
   (`_fetch_series_scoped_batch`/`_SERIES_CATEGORIES`/`series_ticker=` — 9 markers on LDR). KALSHI catalogue = **34 cqg
   partitions** (was 1=OTHER). Root cause was the IS 2000-cap `status=open` flood by `KXMVE*` parlays, NOT the mapper.
2. **P0 lifecycle FOUNDATIONAL fix** — `instruments-service@be45660` (ancestor-of-LDR ✅). `_parse_market` populates
   `available_from/to` best-effort from gamma fields. **NECESSARY-BUT-INSUFFICIENT** (the full P0 chain 43a-d below).
3. **P0 ROOT CAUSE proven** — NULL bounds come from the CLOB-history enum path (no gamma fields); gamma-active path has
   them; honest-cov inflated by `EXPECTED_INSTRUMENT_NOT_LISTED` numerator-credit; `was_instrument_alive()` exists
   (`_honest_coverage_logic.py:400`) but is UNWIRED into emission.
4. **P1 fixture PARSER** — `unified-api-contracts@3effe2fc` (on LDR ✅). `predictions/fixture_parsing.py`:
   `SportsFixtureKey` + `parse_kalshi_sports_fixture` + `parse_polymarket_sports_fixture` + order-independent
   `pairing_key()` + public `kalshi_sports_league_for_ticker`. 14 tests vs REAL live tickers. **(This is what the
   dispatch mislabeled "peer-built may exist" — it is shipped, not pending.)**
5. **P1 cqg BATCH re-walk venue-aware FIX** — `market-tick-data-service@24db3f16` (ancestor-of-LDR ✅).
   `rebuild_prediction_manifest.py` was Polymarket-only (would corrupt Kalshi→all-OTHER on `--apply`); now routes Kalshi
   tickers via `classify_kalshi_to_canonical_group`. 51/51 rebuild tests. **(Dispatch listed this as still-to-do — the
   CODE is shipped; only the `--apply` operational run remains.)**

**📊 VERIFIED honest coverage — newest real GCS supersedes the stale dispatch numbers** (`_index` has GROWN
194,238→**208,276 rows**; KALSHI captured climbed **18→7,248** as live VMs capture):

- **POLYMARKET 95.27%** (was quoted 95.54%) — captured 17,435 / empty 142,874 / failed 7,478. **Inflated by 49,609
  out-of-life empties** (`NOT_LISTED 47,922`+`PRE_VENUE_LAUNCH 974`+`DELISTED 713`) → drops after the P0 chain.
- **KALSHI 79.63%** (was quoted 68.55%) — captured 7,248 / empty 24,468 / **failed 8,108** (pre-endpoint-fix; 1.2
  backfill re-resolves).
- 4 `prediction-live-*` VMs RUNNING; KALSHI live `book_snapshot_5` = 4,199 parquets/06-23. cqg is NOT a raw-tick
  partition key → NO raw-tick migration ever (verified).

**⏳ REMAINING (every item a tracked `- [ ]` todo; no DEFERRED-without-todo):**

- **P0 chain 43a–43d** (operator's #1; fleet-blast-radius) — IS CLOB-history gamma enrich (→ available_from/to ≫16%) ·
  MTDS/UTL `was_instrument_alive`-bounded emission · UAC coverage-math exclude `NOT_LISTED/PRE_VENUE_LAUNCH/DELISTED`
  from num+denom across 4 consumers (rule-11 fleet verify) · `rebuild_prediction_manifest --apply` re-walk (now
  venue-safe). **Concurrent peer is live in IS on this** — coordinate / don't collide.
- **P1 fixture-pairing RESIDUAL** (VERIFIED genuinely open: `predictions/__init__` exports 0 parsers;
  `build_cross_venue_mapping`/`fixtures_pair` absent on LDR) — facade-export the parsers + add
  `build_cross_venue_mapping()`
  - `fixtures_pair()` (same-settlement guard) + arb-layer wiring (features/strategy) + IS sports-event link.
- **Operational tranche** — `--apply` Kalshi re-walk (find seeded tick dates) · Polymarket batch `book_snapshot_5`
  row-proof (2-stage IS re-enum) · Kalshi recent-window 06-20..22 + mid-gap backfill (8,108 failed re-resolve) ·
  recent-window catalogue re-enum · politics/geo canonicalization (judgment-heavy, no false pairs) · per-instrument arb
  pairing · manifest hygiene P3.
- **BLOCKED-UPSTREAM (skip):** Polymarket-PERP (no public API; scaffold ships honest-absence; auto-flows on endpoint).

### 2026-06-24 (autonomous, slot-continuation) — SESSION REPORT: 3 units shipped + verified; remaining = heavy infra/design ops; real GCS coverage numbers

**Shipped this session (all verified before ship — code, tests, QG-green, flipped):**

1. **P1 fixture parser — `UAC@3effe2fc`** (`canonical/domain/predictions/fixture_parsing.py` +
   `kalshi_sports_league_for_ticker`): `parse_kalshi_sports_fixture` / `parse_polymarket_sports_fixture` →
   `SportsFixtureKey` + order-independent `pairing_key()`. Built against REAL live tickers (the operator's "no guessing"
   bar): MLB has HHMM (`KXMLBGAME-26JUN261910SEACLE`), NFL has NO time + VARIABLE-width codes (`KXNFLGAME-26SEP14DENKC`
   = DEN+KC — proves the team-code split is unreliable; teams come from the `title`), tennis is a player-pair, season-
   futures (`KXNBA-27`) → None. 14 tests; UAC QG-green. Residual (registry-resolution + mapping-population + arb wiring)
   split to its own tracked P1 sub-todo.
2. **P1 BATCH cqg re-walk venue-aware fix — `mtds@24db3f16`**: a `--dry-run` (run BEFORE any write) caught that
   `rebuild_prediction_manifest.py` was POLYMARKET-ONLY — it classified every venue with
   `classify_polymarket_to_canonical_group`, so KALSHI tickers mis-bucketed to OTHER (`KXCPI`→OTHER vs the correct
   `CPI_PRINT_PER_MONTH`); a blind `--apply --venue KALSHI` would have CORRUPTED the manifest to all-OTHER. Fixed
   venue-aware (`compute_object_atom(..., venue)` routes KALSHI via `classify_kalshi_to_canonical_group(ticker=cid)`); 2
   regression tests; 51/51 rebuild tests + mtds QG green. The `--apply` operational run remains (now safe — see the
   re-walk todo).
3. **P0 independent confirmation**: re-derived the lifecycle root cause (CLOB-history fetch lacks gamma
   `createdAt`/`startDate`; gamma-active path has them — verified live) — MATCHES the peer's `be45660` (which I verified
   correct on LDR). The remaining P0 chain (43a-d: CLOB-history enrich / `was_instrument_alive`-bounded emission / UAC
   coverage-math exclude / re-walk) is **peer-owned** (a concurrent IS session shipped be45660 mid-session) — left to
   them to avoid file collision.

**VERIFY — real GCS 4-state honest coverage (`market-data-tick-pred-prd/_index`, 208,276 rows, 2026-06-24):**

- **POLYMARKET**: **95.27%** — 168,260 cells (captured 17,435 / empty 142,874 / failed 7,478 / eu 473). **Still inflated
  by 49,609 out-of-existence empties** (`EXPECTED_INSTRUMENT_NOT_LISTED` 47,922 + `PRE_VENUE_LAUNCH` 974 +
  `DELISTED` 713) — the operator's P0 finding; drops to the in-lifecycle universe once 43a-d + re-walk land. (93,264
  `SOURCE_RETURNED_ZERO` may also include out-of-life dates per 43d.)
- **KALSHI**: **79.63%** — 39,827 cells (captured **7,248** — climbed from 18 as the live VMs capture / empty 24,468 /
  **failed 8,108** [pre-endpoint-fix trade/book, re-resolve on the 1.2 backfill] / eu 3).
- **Live VM evidence**: 4 `prediction-live-{kalshi,polymarket}-{trades,book-snapshot-5}` VMs RUNNING; KALSHI live
  `book_snapshot_5` = **4,199** parquets on day=2026-06-23 (the Kalshi CLOB-WS fix capturing). Cross-venue cqg overlap
  (catalogue-derived, prior-verified) ≈ 18 shared non-OTHER groups (the tick `_index` carries no
  `canonical_question_group` column — overlap lives in the catalogue + cqg bundle).

**Remaining (all tracked as `- [ ]` todos) — heavy infra/design ops needing fresh context:** P0 43a-d (peer-owned) ·
re-walk `--apply` (find Kalshi-seeded tick dates first) · Polymarket batch book_snapshot_5 row-proof (2-stage IS re-enum
dep) · Kalshi recent-window + mid-gap backfill (VM) · recent-window catalogue re-enum (IS) · politics/geo cross-venue
(judgment-heavy) · per-instrument arb pairing (now unblocked by the fixture parser; strategy/features) · manifest
hygiene (P3). Polymarket-perp stays BLOCKED-UPSTREAM (no public API). **No DEFERRED-without-todo; every remaining item
is a tracked checkbox.**

### 2026-06-23 (autonomous, slot-continuation) — P0 independently re-confirmed (peer-owned, be45660 verified) + P1 fixture-parse REAL-SAMPLE spec captured

Second autonomous session. Independently re-derived the P0 root cause (NULL `available_from/to` because the
**CLOB-history enumeration path lacks gamma `createdAt`/`startDate`** while the **gamma-active path has them** —
verified live: `gamma-api…/markets?active=true` returns `createdAt`/`startDate`/`endDateIso` populated, and
`PolymarketGammaMarket.model_validate` correctly carries them) — **matches the peer's finding exactly** (adds
confidence). The peer's IS code fix **`be45660`** (populate `available_from/to` directly+best-effort from gamma fields,
preferring the strict lifecycle) is **on LDR + verified correct** (read `polymarket/parsing.py:107-128` — the
`available_from = startDate|createdAt`, `available_to = closedTime|endDateIso`, lifecycle-preferred logic is present and
the `InstrumentRecord(...)` return uses it). **P0 remaining = the peer's scoped 43a–43d chain** (IS CLOB-history gamma
enrich · MTDS/UTL `was_instrument_alive`-bounded emission · UAC coverage-math exclude out-of-life reasons [fleet
blast-radius] · mtds re-walk). **Left to the active peer to avoid file collision** (slot-cron FF-pull brought `be45660`
in mid-session → a concurrent session is live in IS). My pivot: independent, non-colliding todos.

**P1 fixture-level cross-venue pairing — REAL ticker/slug samples captured (de-risks the operator's "no guessing,
per-league formats vary, false pairs dangerous" warning).** Verified live from
`api.elections.kalshi.com/trade-api/v2/events?series_ticker=…&status=open`:

- **MLB** `KXMLBGAME-{YY}{MON}{DD}{HHMM}{AWAY}{HOME}` — `KXMLBGAME-26JUN261910SEACLE` (title "Seattle vs Cleveland") =
  26-JUN-26 19:10, away SEA, home CLE; 3-char team codes (`PHINYM`=PHI+NYM, `NYYBOS`=NYY+BOS). **Has HHMM.**
- **NFL** `KXNFLGAME-{YY}{MON}{DD}{AWAY}{HOME}` — `KXNFLGAME-26SEP14DENKC` ("Denver vs Kansas City") = 26-SEP-14, away
  DEN, home KC. **NO HHMM**; team codes are **VARIABLE 2–3 chars** (`DENKC`=DEN+KC, `DALNYG`=DAL+NYG, `WASPHI`=WAS+PHI)
  → the 6-char-split assumption FAILS for NFL; must split by the **title** ("Away vs Home") + a Kalshi-abbrev→canonical
  map, NOT a fixed offset.
- **Tennis ATP/WTA** `KX{ATP,WTA}MATCH-{YY}{MON}{DD}{P1}{P2}` — `KXATPMATCH-26JUN24HUMBRO` ("Humbert vs Brooksby") =
  player-pair, 3-char surname prefixes (HUM+BRO). Player-pair, not team.
- **Season-futures are NOT per-game** — `KXNBA-27` ("2027 Pro Basketball Champion"), `KXNHL-27` ("…Stanley Cup Winner")
  carry no fixture → MUST be excluded (only `KX{LEAGUE}GAME` / per-match tickers pair). The per-game NBA series is
  `KXNBAGAME-*` (verify when in season).

**Design (for the implementation tick):** the reliable fixture key is `(league, away_canonical, home_canonical, date)`
derived from the **`title` "Away vs Home"** (deterministic) + the **`{YY}{MON}{DD}` date** from the ticker (NOT the
brittle team-code split — NFL proves codes are variable-length). Then resolve to the canonical sport fixture via the
sports domain registry (api-football fixture / odds-api event) → populate
`CanonicalPredictionMarket.mapped_sport_event_id`

- `PredictionMarketCrossVenueMapping` (schema EXISTS, `prediction_mapping.py:55-80`, unpopulated). Same-start-time guard
  before pairing (MLB carries HHMM; NFL date-only → guard on date + team-pair only). Reuse
  `_KALSHI_SPORTS_PREFIX_TO_LEAGUE` (`classifiers.py:603`) for league + the existing team-canonicalisation maps.
  Polymarket side: parse the gamma slug/`event_title` ("Arsenal vs. Chelsea") via the existing
  `_parse_vs_string`/`_extract_teams` (already in `polymarket/markets.py`) → same `(league, away, home, date)` key →
  join on it. Build per-league (formats differ); validate against these REAL samples + a live fetch each run.

Drove the P0 honest-coverage / NULL-lifecycle finding to a **proven root cause** (prior sessions had only a vague "raw
gamma dump" hypothesis). Empirical findings (real GCS + live gamma API):

- `available_from_datetime`/`available_to_datetime` = **0% populated** on bare-path POLYMARKET catalogue parquets
  (`by_date/day=*/venue=POLYMARKET/instruments.parquet`, 0/452 sampled) and **~16%** on fresh cqg-first parquets
  (`canonical_question_group=*/day=2026-06-23/venue=POLYMARKET/`, 1495/9416). Confirms operator's 0/25 drill-down.
- `classify_lifecycle`'s parse logic is **CORRECT** — 200 live gamma markets (100 active + 100 closed) → **100% would
  classify**. NULLs are NOT a parse bug.
- **REAL root cause**: strict `classify_lifecycle` requires BOTH creation AND resolution ts; batch/date-mode markets are
  enumerated via the **CLOB-history path** (opaque short-key schema `r/t/c/mos/…`) carrying **no gamma lifecycle
  fields** → lifecycle None → both bounds NULL. Only the **gamma-active path** (`get_instruments(date=None)`/today)
  carries them → the ~16%.
- **Honest-coverage MATH confirmed** (`_honest_coverage_logic.compute_honest_coverage`): `empty_confirmed` (incl.
  `EXPECTED_INSTRUMENT_NOT_LISTED`) is NUMERATOR credit → out-of-existence cell scored "honestly answered" → inflates %.
  `was_instrument_alive(available_from, available_to, day)` **already exists** in UAC (`_honest_coverage_logic.py:400`)
  but is only used by the `EmptyFromLiveInstrumentError` backstop, NOT by the empty-emission decision.

**SHIPPED (foundational, strictly-better, verifiable):** IS `polymarket/parsing.py::_parse_market` now populates
`available_from/to` **directly + best-effort from gamma fields** (from = startDate|createdAt, to =
closedTime|endDateIso), preferring the strict lifecycle's settlement-lag-adjusted values when it classifies, else the
raw gamma bound. So the **gamma-active/live universe now fully carries bounds**; partial-gamma markets get a partial
bound (beats NULL). 2 regression tests added; 16/16 lifecycle tests pass; IS QG green. — **instruments-service@be45660**
| QG-green sentinel.

**BIG-FINDING — remaining P0 chain is a deep, fleet-blast-radius multi-stage fix (operator: this is data-correctness,
honest-coverage semantics).** The `_parse_market` tweak is necessary-but-INSUFFICIENT: it does not help CLOB-history
markets carrying NO gamma fields, and does not change the existing 142k manifest empties or the inflated %. Full fix =
the open P0 sub-todos below (item-43a..43d).

- [x] ✅ [SCRIPT] P0. **43a — IS CLOB-history lifecycle lower-bound SHIPPED (instruments-service@0b2b944)**: the
      CLOB-history `/markets` shape carries no gamma `createdAt`/`startDate` (→ NULL `available_from`) but DOES carry
      `accepting_order_timestamp` + `game_start_time` (verified against the live CLOB endpoint). New
      `_enrich_clob_lifecycle_lower_bound` (markets.py) lifts the earliest into `start_date` — ONLY when no gamma
      creation field is present (never overrides a real gamma bound) — so `_parse_market`'s existing best-effort
      derivation yields a non-NULL lifecycle lower bound for CLOB-history rows (`available_to` already came from
      `end_date_iso`). No per-condition_id gamma re-fetch needed. 4 regression tests vs REAL CLOB samples; IS QG-green.
      Operational re-enum verify (parquet `available_from` ≫16%) rides 43d. Provenance: autonomous /autonomous
      2026-06-24.
- [x] ✅ [SCRIPT] P0. **43b — emission bounding ALREADY DONE in the enumerator + a latent tardis bug FIXED
      (market-tick-data-service@6003f512)**: ground-truth read (Grep-Then-Read) found the IS
      `enumerate_expected_universe.py` **v2 enumerators ALREADY bound emission by `available_from`/`available_to`
      inline** — `d_ts < af_ts → EXPECTED_INSTRUMENT_NOT_LISTED`, `d_ts > at_ts → EXPECTED_INSTRUMENT_DELISTED`, else
      alive → `expected_unattempted` (across cefi/defi/tradfi/sports/prediction; the prediction enumerator at
      L1625-1692). They reimplement the bounds check directly (not via `was_instrument_alive`), so emission is correctly
      life-bounded. The only real gap was a **latent TypeError**: mtds `tardis_batch_download.py` called
      `was_instrument_alive(venue=/instrument_id=/day=)` — the WRONG kwargs vs the UAC
      `(available_from, available_to, day)` signature → crash on the Empty-CSV branch. Fixed to the real signature
      (bounds from the row key; absent → conservative honest-absence, correct for a proven flat-file empty). Also fixed
      a pre-existing codex-gate violation (nested `os.environ.get` config-bootstrap exemption on the wrong line). mtds
      QG-green. Provenance: autonomous /autonomous 2026-06-24.
- [x] ✅ [UAC] P0. **43c — coverage-math clip SHIPPED (UAC@ea9bfdd5 + UTL@c412a8ce + deployment-api@1390cc0)**: root
      cause precise — UAC `compute_honest_coverage` gave out-of-life empties NUMERATOR CREDIT; the docstring's "credit
      == clip, same ratio" is FALSE whenever `attempted_failed`/pending > 0 (prediction has 7,478 failed) → inflation.
      UAC already had the canonical `OUT_OF_COVERAGE_WINDOW_REASONS` frozenset (incl.
      NOT_LISTED/DELISTED/PRE_VENUE_LAUNCH) but only deployment-api `coverage.py` (the live panel) consumed it; UAC
      core + UTL + IS `/api/data-status` + deployment-api `coverage_metrics` did NOT (inconsistent surfaces). **Fix
      (back-compatible, default 0):** added `out_of_window: int` to `CaptureStatusCounts` + clip in
      `compute_honest_coverage` (`within_window_empty = empty_confirmed − out_of_window`, clipped from BOTH num+denom).
      Producers populate it: UTL `read_capture_status_counts` (→ AUTO-fixes IS `/api/data-status` + the IS/mtds
      honest-coverage ratchet, both via `compute_coverage_for_bucket`) + deployment-api
      `coverage_metrics`/`breakdowns_core`. `coverage.py` already correct, left untouched. 6 UAC + 3 UTL + 7 DA
      regression tests; all 3 repos QG-green. **Rule-11 blast radius VERIFIED on REAL GCS**
      (`market-data-tick-pred-prd/_index`, 212,636 rows): POLYMARKET 95.28%→**93.30%** (49,665 out-of-life empties
      clipped), KALSHI 81.50%→**78.84%** (5,521 clipped) — the intended out-of-life correction ("blanks where we
      expected data"), no gate breaks (the `honest_coverage_ratchet.sh` is `|| log_warn` warn-only + auto-rebaselines
      its daily snapshot). Provenance: operator empty_confirmed drill-down + autonomous /autonomous 2026-06-24.
- [x] [SCRIPT] P0. **43d — re-walk to reclassify the ~49.6k out-of-life empties**: after 43a-c land + a fresh tarball,
      run `market_tick_data_service/scripts/rebuild_prediction_manifest.py --venue {POLYMARKET,KALSHI}` (VM job) to
      physically convert out-of-life `empty_confirmed[EXPECTED_*]` cells → BLANK/`expected_unattempted`; audit whether
      the 93,264 `SOURCE_RETURNED_ZERO` include out-of-lifecycle dates (same root cause). Verify honest % recomputed
      over the in-lifecycle universe. KALSHI lifecycle already flows onto `available_from/to` (`kalshi.py:816-817`) —
      verify it survives the same CLOB-vs-gamma split. Repo: market-tick-data-service. Provenance: autonomous P0
      2026-06-23. ✅ DONE 2026-06-27 — both `mtds-prediction-polyrewalk-20260627-075135` (POLYMARKET) +
      `mtds-prediction-kalshirewalk-20260627-075154` (KALSHI) ran to completion (VMs auto-deleted). Per-VM shards
      written with 5000 rows of `attempted_failed` = normal CFM-11 re-emission of in-lifecycle failed rows; out-of-life
      rows dropped (not re-emitted) → now blank/`expected_unattempted` in consolidated index.
      market-tick-data-service@(rewalk-complete-2026-06-27).

### 2026-06-23 (autonomous) — FINAL REPORT: P1 cross-venue Kalshi canonicalization RESOLVED + VERIFIED + LIVE; partition-completeness answered (real GCS numbers)

**P1 (cross-venue Kalshi grouping) — DONE + VERIFIED end-to-end.** Root cause was NOT the mapper (comprehensive since
c3bf51d1) — it was the IS Kalshi enum capping at 2000 `status=open` markets FLOODED by `KXMVE*` multivariate parlays →
all crypto/macro/sports pushed out → catalogue all-OTHER. Fixed with **series-scoped enumeration** (fetch the
cross-venue-relevant series via `/markets?series_ticker=`, non-OTHER-filtered, throttled w/ 429 backoff) + the **Kalshi
sports classifier** (per-game → shared `SPORTS_{LEAGUE}_{BETTYPE}`) + **KXRIPPLE→XRP** + **EUR-FX collision fix** + the
**`not historical` guard fix** (a dated `--mode batch` re-enum was skipping series-scoped).

**Shipped (fleet, on LDR):** UAC classifiers.py (sports + KXRIPPLE + EUR + 6 tests) · IS kalshi.py (series-scoped +
throttle + Sports/Politics categories + guard fix + 4 tests). UAC & IS QGs green.

**VERIFIED — real GCS numbers (2026-06-23):**

- **IS catalogue cqg split (`instruments-store-pred-prd`, day=2026-06-23):** venue=KALSHI **1 → 34 cqg partitions** (was
  all-OTHER): crypto BTC/ETH/SOL/XRP/DOGE/BNB/HYPE (up-down + range), indices SPX/NDX/DJIA/RUT, macro
  CPI/FED/GDP/NONFARM_PAYROLLS/PCE/TREASURY, CRUDE_OIL, EUR, **SPORTS_MLB_MATCH/SPREAD/TOTAL + SPORTS_NFL_MATCH +
  SPORTS_WORLD_CUP_MATCH**. venue=POLYMARKET = 27 cqg (unchanged). Re-enum wrote 6887 KALSHI records across 34 groups
  (OTHER=2004 = the KXMVE parlays, correctly).
- **MTDS tick manifest 4-state + honest coverage (UAC `compute_honest_coverage`, `market-data-tick-pred-prd/_index`,
  194,238 rows):**
  - POLYMARKET **95.54%** — 168,259 cells (captured 17,405 / empty_confirmed 142,874 / attempted_failed 7,507 / eu 473).
  - KALSHI **68.55%** — 25,790 cells (captured 18 / empty 17,657 / **attempted_failed 8,112** / eu 3). The 8,112 failed
    cells are the pre-endpoint-fix Kalshi trade/book failures (the `/markets/trades` 404 era + book) — they re-resolve
    to captured/empty on the 1.2 backfill with the fixed adapter.
- **Live evidence:** 4 `prediction-live-*` VMs RUNNING; the 2 KALSHI shards relaunched on the cqg-fixed tarball resolve
  the full **6887-instrument** universe (was 2000-flooded), 0 errors. POLYMARKET shards untouched (unaffected).
- **Cross-venue overlap set (Kalshi ∩ Polymarket, live 2026-06-23) ≈ 18 shared groups** (was ~16; +SPORTS_MLB):
  BTC/ETH/SOL/XRP/DOGE/BNB/HYPE `_UP_DOWN_DAILY`, BTC/ETH/SOL/XRP `_PRICE_RANGE_DAILY`, SPX/DJIA/RUT `_UP_DOWN_DAILY`,
  CRUDE_OIL, **SPORTS_MLB_MATCH/SPREAD/TOTAL**. Kalshi-rich-but-Polymarket-not-live-today: CPI/FED/GDP/payrolls/PCE/
  treasury/NDX (auto-pair when Polymarket lists them — groups are shared). The KXRIPPLE fix specifically enabled XRP
  overlap; the sports classifier enabled the MLB overlap.

**Partition-completeness (operator Q "do partition updates need migrations/backfills for live+batch?"):**

- **No raw-tick GCS migration** (cqg is NOT a raw-tick partition key) ✓ — verified.
- **Catalogue** (cqg-partitioned): today refreshed (34 groups) ✓; recent-window re-enum = tracked todo (rides 1.2).
- **Live**: relaunched ✓ (6887 universe resolved on fixed code).
- **Batch** historical cqg re-walk (`rebuild_prediction_manifest --venue KALSHI`, ~5000s VM job): tracked P1 todo.
- Determinism holds (stable classifier hash) → batch re-walk == live capture.

**Tracked remaining (precise todos filed above):** batch cqg re-walk · recent-window catalogue re-enum · politics/geo
cross-venue canonicalization (wording-sensitive, needs arbability analysis) · per-instrument same-game arb pairing
(strategy layer) · 1.1 Polymarket batch book_snapshot_5 row-proof · 1.2 Kalshi batch recent-window+mid-gap backfill ·
1.3 manifest hygiene (313 lowercase/blank venue + 1,454 v4 rows, NICE-TO-HAVE). Polymarket-perp stays BLOCKED-UPSTREAM.

**Also this session (operator side-requests):** PM synced (was 322 behind on a regen-churn dirty file) · 5 service repos
unblocked from `uv.lock` internal-version-drift churn + durable cron auto-discard shipped (PM PR#512) · prediction alert
triage (`DP_CATALOG_NOT_RUNNING` = stale transient, catalog fresh 17:10Z; the 55 VM_STALL/13 VM_GONE are tradfi/sports).

### 2026-06-23 (autonomous, continuous-flow) — fleet uv.lock unblock + P1 Kalshi-grouping ROOT CAUSE = enumeration KXMVE-flood (NOT the mapper)

**Operator side-requests (DONE first):** (1) PM repo was 322 commits behind, blocked by a dirty
`canonical-dependency-manifest.json` (regen `generatedAt`-timestamp churn) → stashed + FF-pulled to current. (2) **5
service repos stranded 11–54 commits behind on dirty `uv.lock`** (e2e-testing/fund-administration-service/
strategy-service/system-integration-tests/trading-agent-service) — the dirty lock was pure **internal editable-package
`version =` drift** (e.g. strategy-service 0.15→0.36, UAC 0.19→0.47, UTL 0.13→0.35) from a non-frozen
`uv sync`/`uv lock` (setup.sh), which the FF-pull cron's auto-discard set did NOT cover → `[skip:dirty]` → stranded.
Cleared all 5 (stash + FF-pull → now 0/0 clean; entire service fleet 0/0). **Durable fix shipped** (PM PR#512,
auto-merging): added a uv.lock internal-version-drift auto-discard to `scripts/dev/slot-cron-ff-pull.sh`, gated to
"uv.lock diff = `version =` lines only" (a real external floor bump also dirties pyproject.toml → preserved →
skip:dirty). `pm-pull-ff.sh` needs no change (PM has no uv.lock).

**P1 Kalshi canonical grouping — the premise was STALE; the real bug is the ENUMERATION CAPTURE.** Grep-then-read +
empirical verification found: `classify_kalshi_to_canonical_group` (UAC `classifiers.py`) ALREADY carries a
comprehensive `KALSHI_TICKER_PREFIX_TO_GROUP` (landed `c3bf51d1` 2026-06-20) wired into the IS Kalshi adapter
(kalshi.py:658) + IS orchestrator (prediction.py:96) + MTDS adapter. Classifying the LIVE `/series` catalogue (5,802
series across Crypto/Economics/Financials/Politics/Sports) through it: **~255 series correctly map to SHARED Polymarket
groups** (BTC_PRICE_RANGE×37, SPX_UP_DOWN×29, FED×24, CPI×17, SOL×18, ETH×13, EUR×12, NDX×11, DOGE/GDP/GOLD/XRP/…). So
the mapper is NOT the gap. **The ACTUAL root cause**: the catalogue's `venue=KALSHI` day=06-22/06-23 holds only
`canonical_question_group=OTHER` — 2000 markets, **ALL `KXMVE*` (multivariate parlay/cross-category) tickers**. The IS
Kalshi live enumeration caps at `_MAX_PAGES=10` (2000 markets) of `/markets?status=open`, and Kalshi's open universe is
**dominated by auto-generated KXMVE parlay markets**, so the crypto/macro markets (the cross-venue arb universe) get
pushed out of the 2000-cap and are NEVER enumerated. `?category=Crypto` on `/markets` is ignored (still KXMVE-flooded),
but **`/markets?series_ticker=KXBTCD&status=open` works perfectly** → fix = series-scoped enumeration of the
cross-venue-relevant families (in progress, IS kalshi.py).

**Shipped this session:** (a) UAC `classifiers.py` — `KXRIPPLE*` → XRP groups (Kalshi lists XRP under the legacy
"RIPPLE" stem; verified live, was falling to OTHER → split XRP off its Polymarket counterpart) + 2 new tests
(real-live-ticker→shared-group coverage + Kalshi↔Polymarket cross-venue same-group invariant); UAC QG green (252s). (b)
IS `kalshi.py` stale docstring fixed (claimed "override-only→OTHER"; the prefix classifier has been wired since
c3bf51d1). **In progress:** IS series-scoped enumeration so the crypto/macro universe is captured + re-enumerate +
cross-venue overlap report.

### 2026-06-20 (PM-3) — Phase 1 SHIPPED (live+batch adapter); Phase 2 converter drafted (reuse-based)

**Phase 1 — SHIPPED + QG-green (instruments-service@8b118d9, 17 tests):** cutoff-aware `get_instruments(date)` routing
(live `/markets` vs `/historical/markets` by `/historical/cutoff`) + RSA-PSS auth (parses `kalshi-api-credentials`,
signs `ts+method+path`; the wrong `Bearer` retired; live `status=open` is unauth-OK). LIVE confirmed end-to-end (2000
records); deep dates → honest-absence. **This makes Kalshi live + batch enumeration work for continuation going forward,
in the unified canonical path.**

**Phase 2 — bulk→canonical converter DRAFTED (thin, reuse-based), NOT yet launched:**
`market-tick-data-service/market_tick_data_service/scripts/ingest_kalshi_bulk_to_canonical.py`. Design (de-risked —
reuses already-correct code, no parallel writer/manifest): per UTC day, DuckDB/pyarrow-slice the Jon-Becker bulk Kalshi
trades (corpus = single 33.5GB `https://s3.jbecker.dev/data.tar.zst`, kalshi subset: trades =
trade_id/ticker/count/yes_price(cents)/no_price/taker_side/created_time(UTC); markets =
ticker/event_ticker/status/open|close|created_time/result; chunk-partitioned, not date) → per ticker REUSE the live
adapter's `_annotate_kalshi_ticker` (identical canonical columns + `canonical_question_group` via UAC
`classify_kalshi_to_canonical_group` + `available_at` floor) → write to UAC
`candidate_parquet_paths( prediction, "trades", day, pipeline_mode="batch_kalshi", venue=KALSHI, condition_id=ticker, ...)`
(the SAME path the live/batch writer emits) → then build v9 manifest by reusing the existing
`rebuild_prediction_manifest.py` over the written parquets. So bulk-seeded data is INDISTINGUISHABLE from API-fetched
(the parity test).

**Remaining Phase-2 steps (precise — converter is ~90% there):**

- [x] ✅ [SCRIPT] P0. market-tick-data-service — `ingest_kalshi_bulk_to_canonical.py` SHIPPED (mtds@74a2dd7, QG-green, 6
      unit tests): pyarrow.dataset day-slice + REUSE `_annotate_kalshi_ticker` +
      `candidate_parquet_paths(pipeline_mode=batch_kalshi)` + `upload_bytes`; byte-identical to live path. ~~finish: (a)
      replace the `duckdb` slice with `pyarrow.dataset` (duckdb is NOT an MTDS dep; pyarrow IS —
      `ds.dataset(glob).to_table( filter=created_time in [day,day+1))`); (b) resolve the actual UCI write call (the live
      `PartitionedWriter` `write_chunk` path — mirror its `get_storage_client()` upload, NOT the unverified
      `upload_bytes`); (c) QG-green. Bucket kind `market-data-tick-prediction` ✅ confirmed; `candidate_parquet_paths`
      prediction kwargs (venue/condition_id/instrument_type) ✅ confirmed. Repo: market-tick-data-service.
- [x] ✅ [SCRIPT] P0. deployment-service — `launch-kalshi-bulk-seed-vm.sh` SHIPPED (deployment-service@2e37dcd) + runner
      mtds@94f0816; **VM LAUNCHED** `mtds-prediction-kalshibulk-20260621-130813` (e2-standard-8, 250GB, parity day
      2026-01-15), async run: download corpus → parity-gate → full-range 2021-07-30→2026-02-05 → rebuild v9 manifest.
      T+10min verify armed. ~~spec:; converter is DONE+shipped mtds@74a2dd7). Reuse pattern: VM with ~200GB boot disk +
      `VM_TASK=canonical-migration` (gives full UTL/env/code setup for free) + a `VM_MIGRATION_CMD` wrapper that: (1)
      `curl -sSL https://s3.jbecker.dev/data.tar.zst | zstd -d | tar -x -C /data --wildcards 'kalshi/*'` (extract ONLY
      the kalshi subset, ~skip Polymarket); (2)
      `python -m market_tick_data_service.scripts.ingest_kalshi_bulk_to_canonical --data-dir /data/kalshi --day <PARITY_DAY>`
      then run the live `/historical` API path for the same day
      (`mtds download --asset-group PREDICTION --venues KALSHI --data-types trades --start-date <D> --end-date <D>`) and
      a parity assert (bulk trade_id/price/count/ts ⊆ API for shared tickers) — FAIL the VM on mismatch; (3) on pass,
      run the converter full range `--start 2021-07-30 --end 2026-04-21`; (4) reuse `rebuild_prediction_manifest.py`
      over the written parquets → v9 manifest; T+10min verify. Repo: deployment-service. ~~OLD: download `data.tar.zst`
      → extract ONLY `data/kalshi/` → run the converter `--day <D>` for ONE parity day → ALSO run the live `/historical`
      API path for D → **assert byte-parity (same tickers/trades/prices/ts)**; on pass, run the full
      `--start 2021-07-30 --end 2026-04-21` range → reuse `rebuild_prediction_manifest.py` → verify manifest v9
      coverage. T+10min verify. Repo: deployment-service. (Do NOT launch until the converter is QG-green — unverified
      writes to the canonical prediction bucket are a data-correctness risk.)

### 2026-06-20 (PM) — "is Kalshi downloading history?" ROOT-CAUSE + fix launched

Operator asked whether Kalshi IS+MTDS is downloading history. **Answer: it was NOT, two-stage gap now being fixed:**

- **Stage-2 (MTDS download) was launched without stage-1 (IS enumeration).** Launched the MTDS Kalshi trades backfill
  (`mtds-prediction-kalshi-20260620-130906`, 2021-07-30→2026-06-20) — it RAN but produced **0 records every date**: 404
  on `instruments-store-pred-prd/instrument_availability/by_date/day=X/venue=KALSHI/instruments.parquet` → "no
  instruments" → SHARD_INCOMPLETE. **Stopped that VM** (can't produce data without stage-1).
- **Root cause: IS never enumerated Kalshi** — `gsutil ls **venue=KALSHI**` = ZERO parquets fleet-wide (Polymarket has
  full `canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet` coverage). The MTDS Kalshi adapter is
  fine: its primary path `_load_market_lifecycle_for_date` reads the `market_lifecycle/by_canonical_group/` store
  (venue-agnostic, would include Kalshi once IS writes it); the flat `by_date/day=X/venue=KALSHI` fallback 404 is just
  noise. IS _supports_ Kalshi — `get_venues_for_asset_groups(["PREDICTION"])` returns `["POLYMARKET","KALSHI"]`
  (venue_core.py:258), and `process_write._write_prediction_venue` handles both — the enumeration just had never been
  **run** for Kalshi (separate from the MTDS get_venues KALSHI-disable I fixed earlier at mtds@ebf947b).
- **Ran the IS PREDICTION backfill `instr-backfill-pred-20260620` (2021-07-30→2026-06-20) — and "check events" surfaced
  the DEEPER blocker (operator was right to verify):** the IS Kalshi enumeration RUNS and hits the API
  (`URDI[KALSHI]: fetched 2000 instruments`) but returns **ZERO records for every historical date** (2021-09-02…09-21:
  106 zero-record errors). **Every one of 106,000 fetched tickers is `…-S2026…` (current-settlement)** — i.e. the API
  returns the CURRENT market snapshot, not a point-in-time list. **Stopped the VM** (it would walk ~1,700 dates
  producing all-zero).
- **ROOT CAUSE #2 (the real one) — the Kalshi IS adapter is current-snapshot-ONLY**
  (`instruments_service/reference_data/adapters/prediction/kalshi.py:113-178`): `get_instruments` takes NO `as_of_date`,
  uses `now = datetime.now(UTC)`, and `_fetch_markets_page` sends `params={"limit":…, "status":"open"}` — it can only
  ever return _currently-open_ markets. The live/ forward daily enumeration is correct; **historical backfill is
  structurally impossible with it.**
- **ROOT CAUSE #3 — Kalshi's public API historical depth is thin/unavailable unauthenticated:** direct probes
  `GET /trade-api/v2/markets?status=settled&min_close_ts=…&max_close_ts=…` for 2023-06 / 2024-06 / 2025-06 windows all
  returned **0 markets** (while `status=open` returns 2000+). So even adding an `as_of_date`/settled-windowed historical
  mode may not yield deep history without authenticated settled-market pagination — or it may simply not be served.
- **DECISION NEEDED (operator) — closed set:** (a) **forward-only Kalshi** — accept that historical Kalshi
  instruments/trades are unavailable; run live enumeration from now on (works today), honest- absence the past; (b)
  **adapter R&D** — add an authenticated `status=settled` + `min/max_close_ts` windowed historical mode and verify how
  far back the authenticated API actually serves (uncertain payoff); (c) **paid historical vendor** for Kalshi. The MTDS
  Kalshi trades backfill is moot until the IS instrument universe exists for the target dates, so it stays un-relaunched
  pending this decision.
- **Lesson (still valid):** prediction backfills are a 2-stage IS→MTDS pipeline — IS enumeration MUST precede MTDS
  download. But for Kalshi the stage-1 itself can't reconstruct history with the current adapter + public API.
- [x] ✅ [SCRIPT] P0. **instruments-service — Kalshi historical enumeration** — ALREADY SHIPPED
      (instruments-service@8b118d9, prior session, promoted to v0.22.0/main): `get_instruments(date=None)` cutoff-aware
      routing — `date=None`→live `status=open` (default, unchanged); `date` set→`/historical/cutoff` + RSA-PSS-signed
      `/historical/markets` with client-side date filtering; deep dates (>3d pre-cutoff)→honest-absence `[]` (the bulk
      Jon-Becker seed covers deep history). Tests:
      `test_deep_date_is_honest_absence`/`test_parse_kalshi_creds_rsa_blob`/`test_signed_headers_present_only_when_creds`.
      Verified ancestor of LDR (45 date/historical/cutoff refs). — 2026-06-21

### 2026-06-21 20:47 — Polymarket v4→v9 re-walk: CF-11 phantom-row fix + relaunch (v2)

- **First re-walk (VM 183617) FAILED at ~112min** on `MalformedRowKeyError`: the CF-11 honest-absence re-emit
  (`_rebuild_prediction_cf11.py::reemit_honest_absence_rows`) iterated stale pre-canonical phantom rows with a BLANK
  `instrument_id` (`data_type='trades'`, `instrument_id=''`) and built a per-instrument `row_key` with
  `instrument_id=''` → Phase-4 `hard_schema_enforcement` rejects it; the crash hit BEFORE the per-VM shard flush, so
  nothing landed.
- **Fix**: `reemit_honest_absence_rows` now SKIPS blank-`instrument_id` rows (`counters['reemit_skipped_blank_iid']`);
  the canonical cqg bundle atom supersedes those legacy per-instrument phantoms. Committed durable:
  market-tick-data-service@LDR
  (`fix(prediction): rebuild CF-11 re-emit skips malformed blank-instrument_id phantom rows`).
- **Relaunch**: tarball rebuilt with the fix; re-walk VM v2 `mtds-prediction-polyrewalk-20260621-204658` RUNNING
  (`--venue POLYMARKET`, concurrent-safe with the Kalshi seed). ETA ~112min. P1 item flips on its clean exit.
- **Kalshi seed (VM 170001)** healthy + climbing: last converted day `kalshi-bulk 2024-08-03` (was 2024-05-15). THE
  deliverable.

### 2026-06-21 20:50 — Two P2 manifest items resolved (verified, no code change)

- **prefix_tpls covers batch_kalshi** (line 157): the phantom reconciler derives `prefix_tpls` from UAC
  `canonical_path_templates("prediction")` (Axis-10 fix — no hand-copy). Verified it now yields
  `pipeline_mode=batch_kalshi/asset_group=prediction/` because my UAC source registration added kalshi to
  `external_batch_sources_for_asset_group("prediction")` → `['kalshi','polymarket_clob','polymarket_gamma_api']`. The
  seeded `batch_kalshi` parquets are PROTECTED from a phantom `--apply` flip. Evidence:
  `_canonical_pipeline_mode_prefixes("prediction")` HAS batch_kalshi=True.
- **Live finalize NOT batch-mode-stamped** (line 153 — STALE PREMISE): `manifest_finalize.py` is the BATCH
  orchestrator's finalize (`_DateRunState` carries only `mvp_mode`, no live flag); the LIVE websocket path uses
  `live/manifest_recorder.py`, which takes a REQUIRED `live_<source>` `pipeline_mode` per call resolved by the runner
  via `live_pipeline_mode_for_venue`. Verified `live_pipeline_mode_for_venue("prediction","KALSHI",...) -> live_kalshi`
  and `...,"POLYMARKET",... -> live_polymarket_clob`. So batch finalize correctly stamps `batch_`, live recorder
  correctly stamps `live_` — no mode-awareness bug; the line-153 "finalize on the live path" assumption was incorrect.
