---
doc_type: issue
title:
  "Instruments remaining-work audit (2026-07-10) — everything genuinely open across instruments-related plans/issues,
  outside pure data backfills"
summary:
  'Synthesis of a 4-shard parallel sweep (4 agents x ~20 real instruments-related plans/issues each, 83 candidate docs
  total) that read every open instruments-touching plan and issue doc in plans/active/ and plans/active/issues/,
  verified each against its own checkbox state and cited evidence, and classified genuinely-still-open non-backfill work
  into 7 categories (CODE_PATH, GCS_BUCKET_MIGRATION, MANIFEST_COVERAGE, SSOT, DOCS_RECONCILIATION,
  INSTRUMENT_ID_CANONICALIZATION, OTHER). Excludes items that are resolved-but-not-flipped (stale status:open despite
  all todos checked) and excludes pure-backfill/download-only work. This is the reference doc for "what is left across
  instruments work outside data backfills" as of 2026-07-10 — it does not itself track new work, it points at the real
  source docs (each of which remains the SSOT for its own todos).'
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction, cross-cutting]
stage: [data, meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-ui,
    execution-service,
    strategy-service,
    features-service,
  ]
scope: [engineer, admin]
tags:
  [
    instruments,
    audit,
    synthesis,
    remaining-work,
    canonicalization,
    manifest-coverage,
    honest-coverage,
    ssot-drift,
    non-backfill,
  ]
related:
  [
    /plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
    /plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md,
    /plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
  ]
created: 2026-07-10
parent_epic: instruments_master
priority: P0
source:
  "Operator, 2026-07-10: requested a synthesized, categorized remaining-work list across all instruments-related
  plans/issues, outside pure data backfills — dispatched as 4 parallel shard agents (each reading ~20 of 83 real
  doc-index-derived candidate lines), then merged here."
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
    /plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md,
    /plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
  ]
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
last_updated: 2026-08-16 # bumped by plan_reconciler Phase -1 (real last-touch per git log; field was 5+ weeks stale)
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **How to read this doc.** Each entry below is a pointer, not a duplicate — the cited doc remains the SSOT for its own
> todos/checkboxes. This doc's only job is categorization + priority ordering across the whole corpus so the operator
> doesn't have to re-derive it from 83 scattered docs. Method: 4 parallel shard agents each read ~20 of 83 candidate
> doc-index lines (source: `DOC_INDEX.generated.md` grep over `plans/active/**`), verified real still-open status
> against each doc's own checkbox/Progress Log state (not frontmatter `status:`, which is frequently stale), and
> excluded anything resolved-but-not-flipped or pure-backfill. Within `INSTRUMENT_ID_CANONICALIZATION`, items already
> exhaustively tracked inside the big `instrument_id_format_canonicalization_2026_07_08.md` effort are only noted as
> existing (not re-listed in full) — that doc is the SSOT for its own sub-detail; this doc surfaces the genuinely
> SEPARATE canonicalization work that effort does not already track.

> **🟡 HISTORICAL SNAPSHOT as of 2026-07-10.** This doc is a discoverability index, not a live tracker — several of the
> docs it points at have since split, been archived, or had their own status move on. It does not self-update; treat
> every entry below as "what was true on 2026-07-10" and confirm current state against the cited source doc (its own
> checkboxes/Progress Log are the SSOT) before acting on anything here. Added 2026-07-28 per
> `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s Track 15 follow-up.

# Instruments remaining-work audit (2026-07-10)

## Category definitions

- **CODE_PATH** — a real fix/feature needed in application code: adapter logic, orchestrator wiring, error handling, a
  missing construction/capture path. Excludes anything whose only remaining action is running a backfill.
- **MANIFEST_COVERAGE** — capture_status / denominator / honest-coverage correctness for the availability manifest,
  across one or more asset groups. Includes coverage-reporting bugs (a wrong number surfaced to a human), not just
  manifest-write bugs.
- **SSOT** — a real contradiction between two sources that are each individually treated as authoritative (codex vs.
  registry, doc vs. code, two registries) needing a decision about which one wins, not just a mechanical sync.
- **DOCS_RECONCILIATION** — a doc that is stale/wrong relative to the real current code or data state, with no
  accompanying code change needed — pure doc drift.
- **INSTRUMENT_ID_CANONICALIZATION** — instrument_id/symbol format work. Split into 5a (already exhaustively tracked
  inside `instrument_id_format_canonicalization_2026_07_08.md` — not re-listed here) and 5b (genuinely separate
  canonicalization work that doc does not track).
- **GCS_BUCKET_MIGRATION** — a real change to bucket naming, GCS object layout/path, or storage-tier migration.
- **OTHER** — genuine remaining work that doesn't cleanly fit the 6 buckets above (still real, still tracked, not a
  catch-all for vague items).

## 0. Headline P0s (read this if nothing else)

1. **Turbo API silently reports 0/0 for DeFi venues with real captured data** (deployment-api read-path bug hiding
   AAVE_V3-ARBITRUM/POLYGON, SPARK, + 5 more) — MANIFEST_COVERAGE §2.1.
2. **CeFi monotonicity guard has zero alerting — LIGHTER/PACIFICA dark 11+ days**, live incident — CODE_PATH §1.1.
3. **is-daily-enum-{prediction,sports} still exit(1) in the cloud** despite the fixed UTL coercion, root cause unknown
   (shard-isolation swallows the traceback) — CODE_PATH §1.2.
4. **59-bug MTDS + instruments-service adapter smoke test** — master record (was: "12 fully open todos incl. multiple P0
   crash risks (Deribit live-WS misclassification, Polymarket `book_snapshot_5` schema crash)" — corrected 2026-07-14,
   doc-reconciliation finding 132: both headline P0 crash risks are already fixed (`market-tick-data-service@c55c1509`
   Deribit dash-count classification fix; `unified-api-contracts@42ce2de3`+`market-tick-data-service@f4a118be`
   Polymarket schema fix), per this doc's own later Progress Log (§ item 4, "9 todos flipped with commit-sha evidence")
   and the source doc's `[x]`-flipped checkboxes; only ~2 of 13 todos genuinely remain open — 273-row root-cause, mockup
   update) — CODE_PATH §1.3.
5. **Instruments Completion Tracker** — the master coordinator itself, 33 of 37 items still open
   (denominator-correctness, Stage 3 re-measure, Stage 5 capture-to-100, D6 implementation follow-ups — decision itself
   approved 2026-07-07, see item 2 below) — MANIFEST_COVERAGE §2.2.
6. **Layer-1 re-measure + certify** — cefi/defi/prediction/sports done; tradfi `BLOCKED-PLAN2` on
   `tradfi_v9_stage1_finish` tasks 2–11 — MANIFEST_COVERAGE §2.3.

---

## 1. CODE_PATH

Real code fixes / features needed (not backfills, not pure doc drift).

### P0

1. **CeFi monotonicity guard has zero alerting — LIGHTER/PACIFICA dark 11+ days**
   `plans/active/issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` Live incident, partially
   diagnosed (OOM on `t1-recon` Cloud Run is plausible-not-confirmed). Open: diagnose+fix the 2 dark venues,
   backfill/honest-stamp the gap, wire `total_thin` into stdout, build the full alerting path, schedule the
   drawdown-guard script, generalize DeFi's monotonicity helper to CeFi/TradFi.

2. **is-daily-enum-{prediction,sports} still exit(1) in the cloud despite the fixed UTL coercion**
   `plans/active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md` Cloud Run jobs still fail
   after a full run; root cause unknown (shard-isolation catch swallows `exc_info`). Doc's own "suggested fix order" not
   yet executed.

3. **Full MTDS + instruments-service adapter smoke test — 59 real bugs**
   `plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` Master record, 12 open todos: P0 crash
   risks (Deribit live-WS misclassification, Polymarket `book_snapshot_5` schema crash), P1 fixes (OKX/Bybit margin-type
   mislabeling, VENUS/BENQI/ RADIANT/EULER_V2 orchestrator wiring, Curve factory-pool undercount), several pending
   operator decisions (GMX V2 coverage — **moot, GMX removed platform-wide 2026-07-25, see
   `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`** —, IDLE/JITORESTAKING/SYMBIOTIC/KARAK empty-feed
   acceptance).

### P1

4. **DeFi lending — real A_TOKEN/DEBT_TOKEN split — RESOLVED 2026-07-13** (one sub-item P0: Compound V3 invalid-enum
   crash risk) `plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` — all 9 protocols
   (AAVE_V3, SPARK, COMPOUND_V3, MORPHO, FLUID, VENUS, RADIANT, EULER_V2, BENQI) now emit the canonical
   A_TOKEN/DEBT_TOKEN split with real production data (2,949 rows, 100% canonical), shipped
   `instruments-service@72e0113`+`5226818`, `unified-api-contracts@48bfadff5`. **MARGINFI/SOLEND remain genuinely open**
   — no adapter exists for either, that caveat is unaffected by this resolution.

5. **Issue-docs remediation sweep — 12 remaining code-fixable items**
   `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md` MTDS liquidations/risk_params reconcile for
   radiant/euler, strategy-service staked-lending catalog entries, deployment-ui `DataStatusTab` hardcoded service list,
   deployment-api E2E trace feature, execution-service `service_name` drift, a SIT manifest-import-alignment QG
   violation, plus 3 `tofu apply` infra items pending operator execution.

6. **DP alert-flood triage — 06:00-UTC TradFi OHLCV OOM crash-loop** (+ a terraform-default drift risk)
   `plans/archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` Root-cause + run-to-completion still
   open; separately, `deployment-service:latest` doesn't yet carry the wave-launcher sentinel writer (a `tofu apply`
   would silently revert the live pin).

7. **order-book imbalance computed independently in BOTH MTDS and MDPS** — RESOLVED 2026-07-27
   `/plans/archive/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md` Both remaining checkboxes closed
   (UAC-side retirement shipped `unified-api-contracts@49314f51`; historical-agreement check closed MOOT — zero
   production rows were ever captured to compare); doc archived, `status: resolved`.

8. **WSFeedConnector Phase-3.5 rollout gap — 73 unregistered venues**
   `plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md` COINBASE bare-name removal blocked on a
   drafted-but-unexecuted migration plan; ICE WSFeedConnector blocked on Real-Time Databento credentials; ~46 DeFi
   venues + sports/tradfi venues pending Option-B architectural decision.

9. **Infra capture wiring + devops leftovers (Stage 5 infra) — AO Plan 6**
   `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` ASTER live connector BLOCKED-PREREQUISITES (2
   unlanded merges); 5 credential/operator-gated scaffold items (Pyth oracle-prices launcher, MANTLE paid RPC, Live-ODDS
   quota+2nd source, rate-limit probe VM, CLOB on-chain asset_group classification).

### P2

10. **Fleet data-acquisition health sweep 2026-06-21** — no checkboxes; several fixable bugs not confirmably shipped
    (prediction venue-case mismatch, Pyth Hermes hex-encoding, sports ODDS_API completeness-check false-flag, zero-byte
    footystats log, `book_snapshot`/`book_snapshot_5` SOURCE_PRIORITY key mismatch, mtds version-surface drift blocking
    QG) `plans/archive/2026_08/issues/fleet_data_acquisition_health_2026_06_21.md`

11. **instruments-service's `--run-tag` CLI flag doesn't do what its help text says**
    `/plans/archive/issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md` (archived 2026-07-28, resolved
    instruments-service@f7e64c54) 3 todos unchecked at the time of this audit: decide direction, implement, ship.

12. **TradFi's mvp_mode fetch-time filter is unreachable dead code**
    `plans/archive/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` Zero callers workspace-wide; 3 todos
    (operator decision wire-live-vs-delete, implement, ship).

13. **Crypto-venue single-stock perps + tokenized stocks — equity basis/dispersion arb** (CODE_PATH primary; also
    strategy-design/execution-service scope) `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`
    Phase 2 CeFi equity-perp adapter filter+type-stamp (instruments-service), Phase 3 live CLOB depth, Phase 5 KRX
    registration/backfill/parity gate/Databento-boundary precision/Barchart removal, Phase 1b propagation-ops (P0, real
    infra) + BLOCKED-DATA (Korea vendor), Phase 1c–1f strategy-archetype design + IBKR execution unlock +
    dynamic-universe redesign.

### P3

14. **Prediction migration script — connection-pool hardening fix sits uncommitted**
    `plans/active/issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md` Ruff/basedpyright-clean fix
    written, never committed (its QG run was CPU-starved and killed).

---

## 1a. CODE_PATH conflict + target-architecture review (2026-07-10)

Operator asked whether the 14 CODE_PATH items conflict with each other or with the documented target architecture,
before picking any up. Real review below — each item's real source doc + relevant codex SSOT, not a rubber stamp.

**Top-level summary**: 2 real mutual conflicts found, 3 items diverge from (or are under-verified against) documented
target state, 9 are clean. Look at the #3/#8 contradiction first (a live-vs-reference-data factual disagreement about a
real venue, already shipped in both directions), then the #4/#5 sequencing risk.

### P0

**1. CeFi monotonicity guard alerting** — conflicts: none. Design: strongly aligned — extends the existing
`DP-<CATEGORY>-<NNN>` alert registry (`/codex/05-infrastructure/data-pipeline-alerts.md`), not a new mechanism. Proceed
as proposed.

**2. is-daily-enum-{prediction,sports} exit(1)** — conflicts: none. Design: aligned (`exc_info=True` is additive
observability, doesn't touch the shard-isolation no-raise contract). Proceed — pure unblock, can't diagnose without it.

**3. 59-bug MTDS + IS adapter smoke test** — conflicts: **with #8** (see below). Design: ETHENA's fabricated-value fix
aligns with SSOT, proceed. **HUOBI/BITSTAMP venue-fix verdict SUPERSEDED 2026-07-12** — this "aligned with SSOT,
Proceed" call was written without knowledge of `unified-api-contracts@181b5311` (2026-07-09), a same-week peer commit
that deliberately removed huobi/bitstamp/htx for the opposite reason. Filed as its own SSOT-contradiction issue
(`plans/active/issues/huobi_bitstamp_htx_ssot_contradiction_2026_07_10.md`); operator resolved it 2026-07-12 in favor of
181b5311 — huobi/bitstamp/htx registration should NOT proceed, remove entirely instead (done,
`unified-api-contracts@62e0855c`). Resolve #8 first for the COINBASE-FUTURES venue entry specifically (unaffected by
this correction).

### P1

**4. DeFi lending A_TOKEN/DEBT_TOKEN split** — conflicts: **with #5** — `issue_docs_remediation_sweep_2026_06_02.md` has
an open, unchecked todo wiring VENUS/BENQI/RADIANT/EULER_V2 into strategy-service as usable lending legs, but #4's own
findings (2026-07-07, a month later) say those same 4 protocols currently emit an invalid `InstrumentType` that will
raise `UnknownInstrumentTypeError` the moment a real position needs P&L attribution. #5 predates #4's finding and hasn't
been updated. Design: aligned with `instruments-service-as-ssot-for-mtds.md` + the strategy layer's own existing
`is_supply`/`is_borrow` assumptions. **Recommendation: proceed on #4; flag #5's strategy-service todo as
blocked-behind-#4, don't pick it up standalone.**

**RESOLVED 2026-07-13** — #4 shipped in full: all 9 protocols now emit the canonical A_TOKEN/DEBT_TOKEN split with real
production data (`instruments-service@72e0113`+`5226818`, `unified-api-contracts@48bfadff5`); the
invalid-`InstrumentType` crash risk this conflict analysis flagged is gone. #5's VENUS/BENQI/RADIANT/EULER_V2
strategy-service wiring todo is now unblocked (the "blocked-behind-#4" hold above no longer applies) — it can proceed
standalone; not itself re-verified or picked up as part of this footnote.

**5. Issue-docs remediation sweep (12 items)** — conflicts: the #4 interaction above (only real one). The DEX
pools/swaps rename is correctly `BLOCKED-DISCIPLINE` on the single-walk migration, not a divergence. Design: aligned.
Proceed on the independent items; hold the lending-leg todo per #4.

**6. DP alert-flood / 06:00-UTC TradFi OOM crash-loop** — conflicts: none (and its already-shipped fixes are a directly
reusable template for #1's still-open `t1-recon` OOM diagnosis). Design: matches the sidecar-authoritative,
no-fire-and-forget pattern in `deployment-observability.md`. Proceed as proposed.

**7. Order-book imbalance computed in both MTDS and MDPS** — conflicts: none. Design: one of the cleanest matches in the
list — "MTDS is market-data only" (CLAUDE.md always-on), `order_flow_imbalance` is a derived feature and belongs in
MDPS, not MTDS. Proceed as proposed.

**8. WSFeedConnector Phase-3.5 — 73 unregistered venues** — conflicts: **with #3** — #3's smoke test (2026-07-07) says
COINBASE-FUTURES "genuinely has no FUTURE/OPTION/inverse product... verified 3 ways" and flags the registry's `FUTURE`
entry as phantom; #8 shipped (2026-07-06, one day earlier, `mtds@fd436aea`) a live COINBASE-FUTURES connector explicitly
built around both `PERPETUAL` and `FUTURE` being real, with 23 tests assuming `FUTURE` rows will arrive. Same-session,
same-repo, opposite conclusions, neither cross-references the other. Plausibly both are locally true (static catalogue
never captured a real FUTURE row vs. live parsing for a product that may exist but has never produced a trade) — but
nobody has reconciled it, and it directly determines whether #3's proposed fix (remove `FUTURE` from the registry) would
contradict #8's shipped connector. Design: the `BLOCKED-*` scaffold pattern itself is well-aligned with
`external-data-always-available-rule.md`. **Recommendation: settle the COINBASE-FUTURES fact question first (a direct
API check resolves it) before finalizing either doc's fix.**

**RESOLVED 2026-07-10** — real dispatched investigation + independent verify pass, 2 live API cross-checks. Neither doc
was simply right or wrong: `COINBASE-FUTURES` is wired (both reference-data and live) to Coinbase INTX, which genuinely
has zero dated futures (#3 correct for this venue); real dated futures exist on Coinbase Derivatives Exchange (CDE, 99
live contracts) — a completely separate, Tardis-uncovered Coinbase product #8's connector logic is actually built for,
just filed under the wrong venue key. Real fix: split into `COINBASE-CDE` (new venue + new adapter, since Tardis has
zero coverage) and scope `COINBASE-FUTURES` to INTX-only. Also found: #8's connector likely has a real,
previously-uncaught silent capture-gap (subscribing INTX-shaped ids to an endpoint that will never recognize them) — not
yet confirmed against production parquet. Full evidence in the Progress Log below. Dispatched for execution.

**9. Infra capture wiring (AO Plan 6)** — conflicts: none (ASTER's book5/liquidations gap in #9 is narrower than and
complementary to #8's general trades-key registration). Design: the self-block to avoid a 17,282-row over-seed is the
data-pipeline-correctness HARD RULE in practice. Proceed as proposed — stay blocked until the 2 named prerequisites
land.

### P2

**10. Fleet data-acquisition health sweep** — conflicts: none. Design: the proposed case-insensitive
`_resolve_connector` fallback is a tolerant-reader workaround for a registry casing inconsistency (cefi uppercase,
defi/prediction lowercase, no stated reason) rather than canonicalizing the casing itself. **RESOLVED 2026-07-10
(operator): "don't paper over the inconsistency, fix properly."** Source doc updated
(`fleet_data_acquisition_health_2026_06_21.md`) — the real fix is now canonicalizing every venue key in
`WS_FEED_CONNECTOR_FACTORIES` (and every producer that keys into it) to one convention, UPPERCASE, matching this
session's established canonical-instrument-id casing — not a runtime fallback. Not yet implemented.

**11. `--run-tag` CLI flag doesn't do what its help text says** — conflicts: none. Design: **the issue doc frames this
as a wide-open operator decision — it isn't.** `/codex/08-workflows/t1-batch-dag.md` already documents the target
`--run-tag` behavior verbatim, and instruments-service's own code already special-cases the exact `"t1-recon"` sentinel
from that SSOT, just never implements the GCS-prefix redirection. **RESOLVED 2026-07-10 (operator: "agree").** Source
doc updated (`instruments_service_run_tag_flag_not_applied_2026_07_08.md`) — option (a), wire it through. Not yet
implemented.

**12. TradFi `mvp_mode` dead fetch-time filter** — conflicts: none (soft note: #13 Phase 5 extends the same MVP registry
with 3 KRX equities — no action needed as long as future wiring reads it live). Design: genuinely open — unlike #11, no
SSOT pre-answers whether a fetch-time filter should exist. Proceed as proposed, decision is real.

**13. Crypto-venue equity-perps + tokenized stocks Phase 2** — conflicts: none against other CODE_PATH items. Design:
**authored 2026-06-20, before the 2026-07-08 one-canonical-builder decision** this whole audit doc's §5 tracks (the
effort retiring ~48 DeFi adapters' ad hoc f-string `instrument_key` construction). **RESOLVED 2026-07-10 (operator:
"update the doc to match canonical target").** Source doc updated
(`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 2, new step 2a) — `EQUITY_PERP`/ `TOKENIZED_EQUITY`
`instrument_id` construction must route through the shared canonical builder (same `@LIN` convention as regular CeFi
`PERPETUAL`), not a new ad hoc f-string. Not yet implemented.

### P3

**14. Prediction connection-pool hardening fix uncommitted** — conflicts: none. Design: no SSOT concern, pure ship-it
item. Proceed whenever a quiet QG window is available.

---

## 2. MANIFEST_COVERAGE

Manifest correctness / denominator / honest-coverage work (excludes pure backfill/download).

### P0

1. **Turbo API silently reports 0/0 for DeFi venues with real, current captured data**
   `plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` Live-verified deployment-api read-path
   bug: AAVE_V3-ARBITRUM (18,771 rows), AAVE_V3-POLYGON (24,278 rows), SPARK (7,405 rows, omitted entirely) show
   `0/0`/absent. Sweep found 5 more hidden venues + flagged HYPERLIQUID/ASTER/COMPOUND_V3/FLUID-ETHEREUM for
   cross-check. Main root-cause CODE todo still unchecked — single biggest still-open item in its shard.

2. **Instruments Completion Tracker — denominator → numerator (cefi-first, operator-driven)**
   `plans/active/instruments_completion_tracker_2026_07_06.md` Master coordinator, 33 unchecked / 4 checked across
   Stages 0–6: TradFi v9 apply completion + legacy-twin bucket deletes, denominator-correctness (single `build_expected`
   producer, cefi gate-authority fix, IS-catalogue B0→B2, LIGHTER/EXTENDED/PACIFICA denominator-gap reapply), Stage 3
   re-measure+certify (blocked on KALSHI-PERP contamination purge), Stage 4 foundation sign-offs, Stage 5
   capture-to-100, Stage 6 hygiene, + Decision Gate D6 (shard-dimension model) — decision itself **APPROVED 2026-07-07**
   (was: "open Decision Gate D6"; corrected 2026-07-14, doc-reconciliation finding 131: operator go-ahead already given
   per `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:379-386`, writer fix, DataStatusTab UI
   fix, and bare-BYBIT/OKX phantom removal already shipped; only downstream implementation follow-ups remain open —
   DERIBIT-COMBO venue retirement, Solana DeFi widening — not the decision gate itself. NOTE: the tracker this D6 was
   originally a candidate on, `active/instruments_completion_tracker_2026_07_06.md`'s own Decision Gates table, still
   shows D6 "⏳ OPEN" with no operator-call date recorded — that file is outside this pair's scope, flagged not fixed
   here).

3. **Layer-1 re-measure + certify (Stage 3), AO Plan 4**
   `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md` 1 of 8 open: tradfi `BLOCKED-PLAN2` pending
   `tradfi_v9_stage1_finish` tasks 2–11 (cannot certify against a stale pre-v9 catalogue). cefi/defi/prediction/sports
   freshly certified with real evidence.

4. **CeFi legacy gap-fill + manifest canonicalisation (single-walk) — L3 owner for cefi**
   `plans/active/cefi_manifest_canonicalisation_2026_06_01.md` 1,980 lines, 26 unchecked / 56 checked: v9 apply-time
   migration remaining tranches, F2 (cefi FUTURE bundle-grain rollup), deployment-api dedup/filter fixes,
   execution-service DeFi raw-path fix, operational catalog-path could-exist seed run.

5. **prediction_manifest_canonicalisation — L3 owner for prediction**
   `plans/active/prediction_manifest_canonicalisation_2026_06_01.md` 15 unchecked / 66: C0 bundled legacy→canonical
   walk, pipeline_mode/source riders, post-walk verify, E3 writer-drain confirm, E4 dry+full VM run, E7 CF-audit, E8
   legacy-bucket delete handoff, cross-AG v2-enumerator rollout, QG import-pattern gate finding.

6. **tradfi_v9_stage1_finish — AO Plan 2** `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md` was: 6 of 11
   unchecked incl. orphan sweep (blocked on manifest rebuild ordering) — corrected 2026-07-12, finding 107, §A2 B-queue
   ruling: this entry was authored earlier the same 2026-07-10 day than the plan's own task-2 orphan-sweep gate-flip (🎯
   GATE MET 2026-07-10 17:17:22 UTC, `orphan_class_E=0`, checkbox flipped). As of 2026-07-12 the plan shows **5 of 11
   unchecked** (manifest rebuild, E7 verify, schema-tail restamp, legacy-bucket deletes, scheduler-resume runbook);
   orphan sweep is no longer open and is no longer blocked on manifest-rebuild ordering. Remaining open items: manifest
   rebuild 99.77% not 100% (13,971-row v4 tail + 42K blank-pipeline_mode gap), E7 CF-audit 2 genuine REDs, schema-tail
   restamp blocked on fleet-drain, operator-gated legacy-bucket deletes.

7. **BYBIT-SPOT manifest — 135,444 anomalous rows, checkboxes claimed done but production is unchanged**
   `plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md` **Moved back here 2026-07-10** — a second
   verification pass (while flipping resolved-but-not-flipped docs) found this one's `[x]` todos cite only that the fix
   scripts were _shipped_ (dry-run/--smoke/--apply modes exist), not that `--apply` actually ran. Live manifest read
   (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 2026-07-10) shows row
   counts byte-identical to the original 2026-07-07 diagnosis: 81,659 EMPTY-instrument_type + 53,785
   PERPETUAL-mislabeled rows, plus ~54K stray spot-nonsense-data_type rows (derivative_ticker/futures_chain/
   options_chain/perp_funding/liquidations — none valid for a SPOT venue). No pre-apply backup snapshot exists at either
   expected path. The real fix (relabel + delete) has never actually been executed against production. **RESOLVED
   2026-07-26** — `plans/archive/2026_07/cefi_bybit_spot_manifest_remediation_2026_07_25.md` re-verified this finding
   was still current as of 2026-07-25 (found (b) partially changed: the PERPETUAL→SPOT_PAIR gate had organically closed
   via routine reprocessing, but the 53,934 spot-nonsense rows had not), then ran the real `--apply` against production.
   Independently reconfirmed via `by_data_type` (only `{trades, book_snapshot_5}` remain) and
   `measure_honest_coverage.py` (0 of the cefi-wide `stray_tuples` belong to BYBIT-SPOT). This finding is closed; the
   2026-07-07 diagnosis doc's `status: resolved` is now genuinely accurate, not just checkbox-claimed.

### P1

7. **DeFi expected_unattempted backlog ≥1M cells**
   `plans/archive/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` Operator-gated manifest-seeding write never
   applied; `BLOCKED-OPERATOR-DECISION` on apply-scope; 1 VERIFY P2 todo to check other asset groups.

8. **Honest-coverage shard dimension model is wrong for definitional data** (Decision Gate D6)
   `plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` Writer fix, DataStatusTab
   UI fix, bare-BYBIT/OKX phantom removal shipped; open: widen writer fix to 7 Solana DeFi venues + CURVE-OPTIMISM,
   retire DERIBIT-COMBO as its own venue key, remove phantom `OPTION` from bare OKX, move `market_metadata` off the MTDS
   daily axis, backfill historical rows, add `missing_dates` to breakdown entries, spot-check 5 more CeFi venues.

9. **Phantom captures — defi manifest (2026-06-28)** `plans/archive/issues/phantom_captures_defi_2026_06_28.md` 219,529
   `captured` rows with no backing parquet (10.5% of captured defi scope), concentrated in `swaps_ohlcv_*`/UNISWAP_V4. 3
   unchecked: diagnose systematic writer failure, apply reconciliation, confirm no recurrence.

10. **cefi Layer-1 denominator silently omits whole venues with real captured data**
    `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md` 2 `BLOCKED-OPERATOR-DECISION` remain: bare
    COINBASE/DERIBIT-COMBO in `MVP_SCOPE.venues`; OKX-SPOT zero EXPECTED tuples (interim P0 fix shipped, DESIGN decision
    Option A vs B still open).

11. **honest_coverage_smoke_harness — 4-AG live-run discrepancies**
    `plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` 3 of 4 shipped; 1 remains (re-run
    `run_live_verify_tradfi.py` once `tradfi_v9_stage1_finish` tasks 2-11 land) — self-parked after 4 dispatch bounces.

12. **manifest_consolidator_dtype_at_source_fix — RESOLVED + ARCHIVED 2026-07-25** (was: `status: draft`, "Both todos
    open" — corrected, stale relative to this doc's 2026-07-10 vintage)
    [`plans/archive/2026_07/manifest_consolidator_dtype_at_source_fix_2026_07_07.md`](/plans/archive/2026_07/manifest_consolidator_dtype_at_source_fix_2026_07_07.md)
    Both todos done — the generalized `_TYPED_MANIFEST_COLUMNS`/`_typed_col_projection` dtype-at-source guard had
    already shipped under `unified-trading-library@02fc4661` (2026-07-21); verified live 2026-07-25 against both
    previously-poisoned buckets (sports + prediction) reading real `int64`/`bool`/`double` columns off the canonical
    `_index`. No longer open.

13. **e2e DeFi strategy configs — taxonomy/wizard round-trip fidelity gaps**
    `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` 9 unchecked: D2 (wizard can't
    reproduce tuned configs), D3 (missing Solana-DEX-spot wizard cell), D4 (blocked-credentials), collateral-aware
    down-sizing not implemented, dead YAML key, hardcoded per-LST spot venue, wizard exposes ~0 of the numeric param
    surface. D1 explicitly INTENTIONAL.

14. **mvp_scope_catalogue_tagging** — 2 of 10 unchecked `plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md`
    Features/strategy/model MVP sections not started (no consumer endpoint yet); full real-data MVP-toggle verify
    blocked on a paused manifest consolidator behind a held migration.

15. **predictions_other_bucket_and_ui_drilldown** — 3 of 11 unchecked (stale path CORRECTED 2026-08-16,
    plan_reconciler — this whole doc is a self-bannered non-self-updating historical snapshot, so the "3 of 11" claim
    itself is unverified/likely superseded; the doc is now RESOLVED + archived per `predictions_master.md`)
    `plans/archive/2026_08/predictions_other_bucket_and_ui_drilldown_2026_06_20.md` UI re-walk VERIFY blocked on a
    UI-capable/playwright slot; Phase-5 canonical-groups backfill for ~24 remaining groups (has a real UAC-registry SSOT
    component); prediction sentinel fan-out fix for honest `empty_confirmed` on zero-trading-day canonical groups.

### P2

16. **Empty re-probe disagreements — today's new empties may be C1 bugs**
    `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` Auto-filed daily-audit doc; candidate CSV referenced
    but disposition/trace not done.

17. **Manifest hygiene RED — 2026_06_27** — `plans/archive/issues/manifest_hygiene_red_2026_06_27.md` 1 unchecked
    diagnose+fix todo (defi: schema_version_not_v9, oracle_expects_but_empty, noncanonical paths, phantom_captured,
    shard_4pillar_fail), untouched since filing.

18. **Manifest hygiene RED — 2026_06_29** — `plans/archive/issues/manifest_hygiene_red_2026_06_29.md` Same pattern,
    cefi. 1 unchecked todo, untouched.

---

## 3. SSOT

Cross-doc / cross-registry contradiction, drift, or design-authority gaps.

### P1

1. **Instruments-Service Plan Reconciliation — open plans vs SSOT**
   `plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md` 986-line cross-plan contradiction audit
   (67 plans vs live UAC+codex). Most of C1–C9 resolved, but **C6, C7, C9 still "AWAITING IKENNA"**, **C5
   "with-Ikenna"** (Deribit options false-complete), and Section F plan-consolidation/archival (F.1–F.4) awaiting
   operator sign-off.

2. **UAC data-type-validity combinator is fragmented across CEFI/DEFI/TRADFI**
   `plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` No asset group has a real
   `(venue, instrument_type) → data_types` table; a live provably-wrong cell exists (CME/ICE identical `futures_chain`
   valid-data_types despite ICE having no Databento coverage); DeFi's two capability registries have drifted. 6
   unchecked todos incl. a proposed two-layer redesign pending operator approval.

3. **DeFi hardcoded on-chain-derivable values + UAC date-drift elimination** — ✅ RESOLVED 2026-07-27, both residuals
   shipped and the plan archived: `/plans/archive/2026_07/defi_onchain_derivable_values_and_date_drift_2026_06_20.md`
   Phases 5–5.6 shipped; the 2 residuals noted here are done — Pyth Hermes jitoSOL pre-2023-10 backtest scope resolved
   as **clip** (`unified-api-contracts@4a29261e`), and the "Bug-class-3" local-fallback sweep shipped
   (`instruments-service@8b02b647`).

### P2

4. **Carry archetypes declare CEFI venues but ARCHETYPE_CAPABILITY_REGISTRY has no CEFI cells**
   `plans/active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md` Confirmed codex↔registry
   contradiction (`CARRY_BASIS_PERP_INV`/`CARRY_STAKED_BASIS`); awaiting strategy-owner decision (add cells vs. trim
   doc).

5. **DeFi pipeline — code↔codex drift (audit 2026-05-27)**
   `plans/archive/2026_08/issues/defi_code_codex_drift_2026_05_27.md` D1–D9/D13/D14 done; 2 open: D10 (6 DeFi venues
   `phase=live` with no backing capabilities — needs operator confirm), D15 (HYPERLIQUID/ASTER phase-label
   reconciliation).

6. **instruments-service quality-gates.sh RED on LDR HEAD — CEFI expected-universe drift**
   `/plans/archive/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` — 0 open todos. P0 fix/verify done
   (reverted, QG green); the DESIGN `BLOCKED-OPERATOR-DECISION` above (entry #1, Option A) was the resolution — shipped
   `unified-api-contracts@0ab1074a` + `instruments-service@c0f5529c`. Resolved + archived 2026-07-30.

7. **COINBASE bare-name UAC removal + downstream caller migration** (was: `status: draft`, not dispatched, all steps
   unchecked — corrected 2026-07-12, finding 105, §A2 B-queue ruling: this §3 entry was never back-edited after the
   flip; see this doc's own Progress Log, operator decision #3 and the Orchestration-state / Follow-up-verification
   entries below, which already document the dispatch + completion)
   `plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md` Full 7-step (S0–S7) multi-repo migration plan (44
   UAC + 5 IS + 4 MTDS + cross-repo callers). **Now `status: active`, dispatched for execution 2026-07-10, all S0–S7
   steps `[x]`** (per the plan's own frontmatter + banner as of 2026-07-12).

---

## 4. DOCS_RECONCILIATION

### P1

1. **Instruments-service docs audit (2026-07-08) — consolidated outstanding items across all 7 asset docs** (spans
   CODE_PATH too) `plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md` 604-line, sections A–H.
   A1/A2/B3/C1 resolved (C1, the A_TOKEN/DEBT_TOKEN split, RESOLVED 2026-07-13 — see that doc). Open: §B canonical-id
   builder adoption (~4/63 adapters — overlaps the big canonicalization effort), §C remaining gaps (MARGINFI/SOLEND
   missing adapters, hardcoded `YEARN-ETHEREUM`, Solana key/field mismatches, live DEX-swap streaming placeholder-only),
   §D (Prediction/Sports wiring gaps: `build_cross_venue_mapping()` never wired, `sports-odds-ready` publisher never
   built). §H (TradFi) explicitly deferred.

---

## 5. INSTRUMENT_ID_CANONICALIZATION

### 5a. Already tracked inside `instrument_id_format_canonicalization_2026_07_08.md`

The big canonicalization effort (now archived:
`/plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md` — **repointed 2026-08-18, plan_reconciler
cross-cutting**, was a dangling `plans/active/...` reference; the doc's own frontmatter already cited the correct
archived path) is already exhaustively self-tracked — its own sub-detail is NOT re-listed here. Noted only as existing; several items below are
its direct satellites/follow-ups (cited explicitly where a shard identified the relationship) rather than duplicates of
its own checklist.

### 5b. Genuinely SEPARATE canonicalization work (the real new information)

#### P1

1. **canonical_id_p1_tradfi_combo_leg_canonicalization** — 3 of 11 unchecked (8 done incl. a shipped fix + 34K+ row
   migration) `plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` All 3 remaining are NEW
   follow-ups filed 2026-07-09: a large TradFi single-leg `@LIN`/`@INV` dated- derivative extension (own future plan,
   reversed-into-scope by the operator), extending the 1–4-leg cap to Deribit combos, a UAC `build_leg()` venue-omission
   mode.

2. **CME options_chain legacy flat layout — ~187.5M rows outside canonicalization**
   `plans/active/issues/tradfi_cme_options_chain_legacy_layout_2026_07_10.md` Confirmed via live GCS listing: 120,946
   CME `options_chain` manifest entries deliberately excluded from the 2026-07-09 single-leg `@LIN` migration
   (unverified legacy per-contract flat layout, no `underlying=` subdir). Needs its own investigation + migration;
   separate but related effort.

#### P2

3. **canonical_id_builder_retrofit_checklist** — 9 of 12 unchecked
   `plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md` Explicit follow-up checklist for the 2026-07-08
   one-builder architecture decision. Retrofit ~48 DeFi adapters' ad hoc f-string instrument_key construction through
   the shared builder (blocked on resolving 7 non-canonical TYPE tokens — real crash-risk enum gap), a Betfair
   `/`-delimiter bug, both Prediction adapters storing bare unwrapped ids.

4. **prediction_canonical_identity_migration** — 4 of 8 unchecked
   `plans/active/prediction_canonical_identity_migration_2026_07_08.md` Genuine distinct follow-up (not a duplicate)
   from the big effort's finding-8. Todos 1/3/4/5 shipped + verified vs prod GCS. Remaining: full `prod/catalog.parquet`
   regen/backfill (real-scoped, ~25-40min, intentionally not run unsupervised), a downstream-uniqueness VERIFY, a
   bucket-template rename DECISION, a stale MDPS test-assertion fix.

5. **Fix Kraken-Futures dated-future symbol collision**
   `plans/archive/2026_07/canonical_id_p0_kraken_futures_collision_2026_07_08.md` 6 of 7 shipped/verified (125 files,
   37.5M rows corrected). 1 new P2 todo: a discovered `FI_`-vs-`FF_` same-(ticker,expiry) instrument_id collision —
   needs an operator decision on a contract-subtype marker. Distinct finding from the big effort, directly related.

---

## 6. GCS_BUCKET_MIGRATION

### P1

1. **tradfi_manifest_canonicalisation — L3 owner for tradfi**
   `plans/active/tradfi_manifest_canonicalisation_2026_06_01.md` 23 of 60 unchecked: C0 walk, source/pipeline_mode
   riders, E3–E7, orphan sweep, R1/R2 delete sweep, could-exist denominator seed. Flag: `tradfi_v9_stage1_finish` (item
   6 above) executes against this doc's E5–E7/R1/R2 detail and has landed much since 2026-07-06 — checkboxes here (last
   touched ~2026-06-02/08) look stale relative to that newer plan; reconcile before treating all as open.

2. **solana_defi_legacy_migration** — 0 `[ ]` but 3 real `[~]` partials missed by naive checkbox grep
   `plans/active/solana_defi_legacy_migration_2026_05_27.md` Gate 2 (legacy→canonical history migration): script
   shipped + smoke verified, full ~5,995-shard/ ~1,199-date run still pending. Gate 4 (delete legacy
   `lending_indices/`+`dex_pools/`) blocked on Gate 2. A stale VM monitoring item (`mdps-backfill-defi-20260528-071130`)
   ~6 weeks stale, never verified-closed.

### P2/P3

3. **DeFi — ~104K dead-storage duplicate objects (safe-to-delete candidate)**
   `plans/active/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md` Only 2 of 2,353 day-partitions
   spot-checked (byte-identical, unread by any real consumer); recommends a dedicated full-corpus SAFE-TO-DELETE audit
   before any deletion.

---

## 7. OTHER

Tooling / infra / ML-training / strategy-research items that don't fit the above 6 buckets.

### P0

1. **CeFi ML_DIRECTIONAL_CONTINUOUS — live archetype end-to-end**
   `plans/active/cefi_ml_directional_continuous_live_2026_06_20.md` Infra/code shipped and checked; 1 major P0 remaining
   (≥7 continuous days live on real capital across OKX/Binance/Bybit) gated on operator hard-stops (wallet keys,
   kill-switch arming).

2. **predictions_ml_walk_forward_and_arb** — 4 of 7 unchecked
   `plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md` Model 2A walk-forward run + Group-F AUC/calibration
   gate not yet run (was `BLOCKED-ON sports_master:Group E` — that gate may now be satisfiable per item 3 below, but
   this plan hasn't re-checked). Also open: model-registry persistence, predictions MTDS completion-% slice.

3. **tradfi_sp500_ml_and_arb_backtest_readiness** — 8 of 9 unchecked
   `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` Most P0 items
   `BLOCKED-OPERATOR-DECISION`/`BLOCKED-UPSTREAM` on the MDPS tradfi-passthrough dependency gap — but that gap was
   actually **resolved** 2026-06-28 (`tradfi_mdps_passthrough_dependency_gap`); this plan's `last_updated: 2026-06-27`
   predates the fix, so its blocking status is stale and should be re-verified before treating these as still-blocked.

### P1

4. **mdps_features_reduced_artifact_tracker** (`status: draft`, DAG-coordinator)
   `plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md` Only 2 of 9 sub-plans confirmed resolved
   (`mdps_book_microstructure_precompute_columns`, `tradfi_mdps_passthrough_dependency_gap`); 7 still pending/draft (UAC
   MVP-for-features selector, honest-coverage smoke harness, execution fidelity tiers, Polars engine sharpening, etc.).

5. **market-tick-data-service quality-gates.sh Codex compliance red repo-wide** (empty-string-fallback ratchet)
   `plans/archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` Ongoing churn (overage
   bouncing 380→368→377→372 across concurrent sessions); latest entry shows instruments-service still 3 sites over its
   ratchet baseline, still blocking quickmerge pushes.

6. **predictions_lookahead_and_reader_migration** — 1 of 5 unchecked
   `plans/archive/2026_07/predictions_lookahead_and_reader_migration_2026_06_20.md` Register predictions
   `feature_groups` into UAC `FEATURE_REQUIRED_INPUTS` per canonical_question_group + binary-outcome — not started.

7. **features-service DeFi end-to-end test blocked on multiple data layer issues**
   `plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md` Narrative-only; doc's own final note
   says the four DeFi operator-decisions remain open. PRD's `dex_swaps`→`dex_pool_swaps` rename makes all UNISWAP V3
   invisible to features-service; legacy-bucket manifest never registered its most important pool; OHLC values look
   wrong for `dex_swaps` (price≈1.0 for ETH/USDC); duplicate schema columns. Parallel CeFi path found 3 more bugs (MDPS
   column-order drift, tz-aware/naive join mismatch, filter-pushdown memory bug) — unclear if fixed elsewhere, flagged
   uncertain-but-not-excluded.

### P2

8. **No generic manifest-reprocessing mechanism — 11 near-identical one-off reclassify scripts** — **RESOLVED
   2026-07-30**, all 4 todos done (design + build `select_shards_for_reprocess()`, wired as IS CLI subcommand, 13
   one-offs left in place as historical record per the doc's own carve-out). Archived:
   `/plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md`.

9. **instruments-service GET /api/data-status is dead code**
   `plans/active/issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` 2 unchecked:
   delete-or-document decision (deployment-api built its own richer computation independently; only caller is this
   endpoint's own unit test).

10. **None of this session's adapter/instrument-definition findings verified for 3-layer reconciliation**
    `plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md` Pilot trace
    (AAVE*V3) done, no code change needed there. 2 unchecked VERIFY todos remain (spot-check more findings, decide
    reconciliation cadence). Also folds in a real SSOT finding (`canonical_id* builder.py` documented canonical but
    exactly one real caller workspace-wide) — moved to the big canonicalization effort per operator.

11. **prediction_venue_perps_and_live_clob_depth** — 12 unchecked + 2 partial of 85
    `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` — **split + archived 2026-07-24** (plan
    line-cap remediation) into `plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`
    (perps-venue residuals below), `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (live capture
    residuals), and `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (honest-absence + manifest
    residuals below). Highest-priority live item: POLYMARKET instrument lifecycle `available_from`/`available_to` never
    populated → manifest emits `empty_confirmed` outside a market's real life instead of honest blank (P0 honest-absence
    bug). Also open: Polymarket-perp reference-data adapter BLOCKED-UPSTREAM (no public perps API), residual
    lowercase/blank/UNKNOWN `venue` rows splitting the Kalshi denominator, 1,454-row v4 schema tail, UAC politics/geo
    cross-venue canonicalization + same-event arb-pairing design gaps.

12. **carry_staked_basis_funding_scan_experiment** — 49 unchecked of 54, exploratory research harness
    `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md` Mostly strategy-research backlog (live venue
    wiring dYdX/Vertex, LST APR source wiring, gas/slippage cost modeling, `share_class` axis). Two real non-backfill
    code bugs buried in it worth flagging separately: `lending-indices`/`lst-rates` writer targets a legacy un-suffixed
    bucket key instead of the canonical one (lines 236, 497) — a GCS_BUCKET_MIGRATION-class bug.

13. **master_to_live_defi — May-23 cutover master** `plans/archive/2026_07/master_to_live_defi_2026_05_23.md` Only 4 of
    172 unchecked, all nested under one already-`✅ DEFERRED-FUTURE-WORK`-tagged parent: DART terminal manual-trade lane
    (real-time archetype rendering, manual trade entry through execution-service, monitored window, automation-toggle
    gate). Real unbuilt UI/execution work, explicitly deferred beyond May-23 scope, not urgent.

---

## Excluded (resolved-but-not-flipped, or superseded — verified across all 4 shards)

**UPDATE 2026-07-10**: all 15 genuinely-resolved docs below have now been re-verified a SECOND time and their `status:`
frontmatter flipped for real (`unified-trading-pm@8f15f8233`). **One of the original 16 was NOT flipped —
`bybit_spot_manifest_stray_captures_2026_07_07.md` is a real, still-open gap**, moved back into §2 MANIFEST*COVERAGE
below: its checkboxes claimed the 53,785-row PERPETUAL relabel and 53,934-row spot-nonsense delete were done, citing
only that the fix scripts were \_shipped* — a live production manifest read (2026-07-10) found the real row counts
byte-identical to the original 2026-07-07 diagnosis, and no pre-apply backup snapshot exists at either expected path,
meaning `--apply` was never actually run. The checkboxes were marked done based on "script exists" not "script executed"
— a real discrepancy the second verification pass caught before flipping it.

The 15 genuinely resolved (flipped `unified-trading-pm@8f15f8233`):

- `plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md` (flipped to `status: superseded` —
  real, 2 unchecked items are tracked-to-closure inside other plans, not abandoned)
- `plans/active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md`
- `plans/active/issues/instruments_handler_pd_na_ambiguous_and_af_classification_2026_07_06.md`
- `plans/active/issues/mtds_defi_catalog_reader_reads_dead_static_snapshot_path_2026_07_06.md`
- `plans/active/issues/tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`
- `plans/active/issues/uac_ws_cassette_coexistence_20_missing_map_entries_and_cassettes_2026_07_07.md`
- `plans/archive/2026_07/canonical_id_p1_onchain_perp_perp_shorthand_2026_07_08.md`
- `plans/active/issues/features_read_book_columns_not_snapshots_2026_06_28.md`
- `plans/archive/2026_07/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`
- `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md`
- `plans/active/mdps_features_full_month_benchmark_binance_2026_06_28.md`
- `plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md` (1 residual `[ ]` is an
  operator-declined optional band-aid, not real work)
- `plans/active/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md`
- `plans/active/mdps_book_microstructure_precompute_columns_2026_06_28.md`
- `plans/active/sports_features_readiness_for_predictions_2026_06_20.md`

## Uncaptured — flagged for follow-up

Shard A reported 3 orphaned metadata fragments in its chunk (lines 2, 7, 21 of the candidate file) that had no
title/path — line-wrap artifacts from the doc-index extraction. Traceable topics only: line 2 =
ci-cd/breaking-change-detection/contract-surface/registry/cross-repo-gate (P1, instruments- service); line 7 =
never-seeded/expected-universe/enumerator/honest-coverage/layer-1/capture-to-100 (P2); line 21 =
instruments-service/docs-audit/canonical-instrument-id/reference-data/outstanding-items (P1, likely a fragment of §4
item 1 above). Real work may be hiding here uncaptured — worth a targeted `DOC_INDEX.generated.md` re-grep to resolve
the source docs if this list is used for dispatch planning.

## Progress Log

- **2026-07-10 (authoring day)**: full synthesis + dispatch narrative (83-doc corpus sweep, §1a CODE_PATH conflict
  review, 12 operator decisions, COINBASE-CDE split, wf_60ecfd13-752 P0-wave results) extracted verbatim to
  `/plans/archive/2026_08/instruments_remaining_work_audit_2026_07_10_progress_log_history_2026_08_06.md` 2026-08-06
  (line-cap remediation -- a na-eligibility-audit marker addition pushed this doc to 1003L). Read the extraction only if
  a deeper citation on a specific 2026-07-10 finding's reasoning is needed.
- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole todo is an umbrella over 6
  distinct P0 workstreams (Turbo API, monotonicity alerting, is-daily-enum crash, 59-bug record, completion tracker,
  tradfi v9 stage1); not a single determinable outcome.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2 prior tranche verdicts (cefi, sports, both
  2026-07-30, unchanged): sole todo is a portfolio umbrella over 6 separately-tracked, partly operator-gated
  workstreams, not one determinable outcome.

- **na-eligibility-audit 2026-08-17** [body-hash:f5c512054618ab8f]: KEEP-NA, valid -- This 846-line doc is a self-declared 'HISTORICAL SNAPSHOT... a discoverability index, not a live tracker' whose entire content is pointers to other docs' own SSOT checkboxes -- it explicitly redirects, matching the never-relitigate criterion for doc-level redirection. Its single remaining todo is an umbrella spanning 6 independently-scoped major workstreams (Turbo API bug, a live CeFi monotonicity incident, an unexplained cloud crash, a 59-bug master smoke-test record, the entire Instruments Completion Tracker at 33/37 open — doc #2 in this same batch — and a tradfi Layer-1 block owned by yet another plan), several explicitly operator-gated. Two independent prior na-eligibility-audit passes (2026-07-30 sports tranche, 2026-08-07 cross-cutting tranche) already reached this identical conclusion with matching language; my own read confirms it is not a single determinable outcome.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Self-declared 'HISTORICAL SNAPSHOT... discoverability index, not a live tracker' whose entries are explicitly pointers to other docs' own SSOT checkboxes; sole open todo is an umbrella over 6 independently-tracked.

## Orchestration state — dispatched execution workflow

`wf_1e191185-1c2` (`instruments-audit-decisions-execution`) — **COMPLETE**, 8/8 agents returned. Real per-item verdict:

- **OKX-SPOT + Kraken marker**: landed (`instruments-service@c0f5529c` for OKX-SPOT fold-invert (was:
  `instruments-service@300b0767` — corrected 2026-07-14, doc-reconciliation finding 133: that SHA is a factual
  misattribution, it is actually the COINBASE `_CEFI_VENUE_FOLD` invert
  (`plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md:339-347`,
  `scripts/check_enumeration_completeness.py` only, no OKX-SPOT mention); the real "stop folding OKX-SPOT to bare OKX"
  fix landed as `c0f5529c` (2026-07-10 12:43 UTC), with a same-day follow-on `60c2e3b6`); Kraken marker part was
  mid-quickmerge waiting on a background QG run when the agent's window closed — verify it shipped, re-dispatch if not).
- **DeFi backlog apply**: correctly did NOT execute the stale command — found the same 46× v1→v2 scale explosion this
  doc's Progress Log already recorded; superseded by the operator decision + real launch this session (see above).
- **Archetype registry CEFI cells**: DONE, `unified-api-contracts@7f20bdee`, two-sided-audit contradiction count 2→0,
  17/17 new tests green. Caught + reverted an accidental write to a **different slot's** UI clone before contamination.
  New tracked gap: UAC→UI archetype-capability sync would break the UI TS build (`VenueCategoryV2` not yet exported by
  `enums.ts`) — filed as its own issue.
- **Coinbase bare-name migration (S0-S7)**: 6 of 7 steps landed across `unified-trading-pm`/`instruments-service`/
  `unified-api-contracts`/`market-tick-data-service`/`features-service`/`market-data-processing-service`/
  `deployment-service`. Found + fixed 2 real bugs the plan's own migration table missed (would have silently zeroed
  Coinbase's cefi EXPECTED set / misclassified a NautilusTrader-internal venue map as a rekey target). **S2 (dead
  `elif COINBASE` branch removal) is code-complete + QG-verified locally but never landed** — blocked 5+ retries by
  OTHER concurrent agents' unrelated dirty deps in `unified-api-contracts`/`unified-trading-library`. Needs a clean-tree
  re-attempt. A new S2-ordering issue doc was also filed (`coinbase_bare_name_migration_s2_ordering_2026_07_10.md`).
- **MVP scope + D10 capabilities**: both done. `DERIBIT-COMBO` added to `MVP_SCOPE["cefi"].venues` + `venue_data_types`
  override + capability entry (was silently zero before). COINBASE trades-only cost control turned out to already exist
  (`CeFiMvpRule.venue_data_types`, landed 2026-06-28) — no code change needed. D10's original finding was stale (already
  fixed); the REAL gap was a third registry table (`DEFI_VENUE_DATA_TYPE_CAPABILITIES`) — fixed for
  RADIANT-ETHEREUM/EULER_V2-ETHEREUM+ARBITRUM/VENUS-BSC+ETHEREUM/BENQI-AVALANCHE.
- **Coinbase CDE split**: DONE, matches the resolution already recorded above (2 live API cross-checks + the silent
  capture-gap independently reconfirmed via a live manifest read — 16,819 `COINBASE-FUTURES` rows are 100%
  `batch_tardis`, zero `live_coinbase`, confirmed zero real rows captured live since ship).
- **UAC two-layer redesign**: DONE, `unified-api-contracts@fa9cece5`. Live-reverified before fixing: the CME/ICE bug was
  real (fixed via a new subtraction-only `VALID_DATA_TYPES_VENUE_EXCLUSIONS` table); the DeFi registry-drift claim was
  refined on re-check — only 1 of 34 originally-flagged venues (`AAVE_V3-ETHEREUM` oracle_prices) was genuinely
  mis-declared, the other 33 are a different bug (declared-but-never-captured) filed separately rather than papered
  over. 196/196 new tests green.
- **`mvp_mode` universal build**: both real fixes complete and tested (root cause was one level higher than filed —
  `TickDataHandler.process()` parsed `--mvp-mode` but never read it, so NO asset group's batch path could ever reach
  `mvp_mode=True`, not just TradFi's). **Blocked from shipping** — a concurrent sibling agent's unrelated COINBASE-CDE
  work left `quality-gates.sh` intermittently red on unrelated tests during the shipping window. Needs a clean-tree
  re-attempt to land.

**Follow-up verification, 2026-07-10 (later): all 3 previously-open items confirmed SHIPPED** — re-checked directly
against git history (not re-trusting the earlier "code-complete, blocked" self-report): (1) Coinbase-migration S2
dead-branch removal landed as `instruments-service@db33ded7` (slot 9, reconciled with a concurrent slot-3 attempt per
operator direction — see `plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md` line ~424 for the full ship
narrative); (2) `mvp_mode` universal build landed as `market-tick-data-service@e7581b8b` (committed 2026-07-10
16:32:27+01:00, root-caused one level higher than filed — `TickDataHandler.process()` parsed `--mvp-mode` but never read
it, blocking every asset group's batch path, not just TradFi's); (3) Kraken FI*/FF* marker fix confirmed shipped in both
consumers — `instruments-service@c2d3fbbc` (`_KRAKEN_FUTURES_PREFIXES` in
`reference_data/adapters/cefi/tardis/parsing.py`, 2026-07-09) and `market-tick-data-service@20dc1be8`
(`kraken_futures_book_ticker_ws.py`, 2026-07-10) — both files clean in the working tree, no uncommitted drift. No
re-shipping action needed for any of the three. Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3-unified-trading-pm/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/instruments-audit-decisions-execution-wf_1e191185-1c2.js`

`wf_60ecfd13-752` (`instruments-audit-p0-wave`, dispatched 2026-07-10, operator: "finish all fixes now") — **COMPLETE**,
see the Progress Log entry above for the real per-item verdict (2 fixed, 1 still open with a new actionable lead, 3
partial/honestly-left-open). The 6 remaining Headline P0s not covered by either in-flight workflow: Turbo API 0/0 bug,
CeFi monotonicity guard alerting (live incident), is-daily-enum cloud crash, the 59-bug smoketest master record (GMX
V2/empty-feed protocols decided: accept documented-empty, don't build new coverage), the Instruments Completion Tracker
(33/37 open, real partial progress expected honest outcome), and Layer-1 tradfi's `tradfi_v9_stage1_finish` block.
Script:
`/Users/ikennaigboaka/.claude/projects/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/75f22ce1-df33-490d-921e-c63d29f3656f/workflows/scripts/instruments-audit-p0-wave-wf_60ecfd13-752.js`

## Todos

- [ ] [DATA] P0. DEFERRED-BY-DESIGN — RULED 2026-08-22 (D1): repeated audits agree this doc's remaining "close the 6
      Headline P0s" umbrella is churn, not a live task; approved to stay as a historical discoverability pointer, no
      further autonomous dispatch of this umbrella item (the individual P0s remain tracked in their own owning docs).
      Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole todo is an umbrella 'close the 6
  remaining Headline P0s not covered by any in-flight workflow' across a 979-line, 5-asset-group audit — a portfolio of
  independently-scoped P0s, not a single determinable outcome, and several of its constituents are themselves
  operator-gated (e.g. the HUOBI/BITSTAMP SSOT contradiction)
- **context-scout 2026-08-03**: refreshed context_scope (6 entries, unchanged) — verified all 6 cited source docs still
  exist at their given (post-archival-correction) paths; this is a pure synthesis/index doc over other plans/issues,
  genuinely code-free by design.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged — the only changes since
  the last pass were a line-cap history extraction and a na-eligibility-audit re-affirmation, neither of which shifts
  what the sole remaining "6 Headline P0s" todo points at; all 6 entries still resolve.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged since 2026-07-30.
  Sole todo is still the same umbrella 'close the 6 remaining Headline P0s' across independently-scoped items, several
  themselves operator-gated; not a single determinable outcome.
- **context-scout 2026-08-17**: re-verified context_scope (6 entries), unchanged.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed unchanged. Self-declared "HISTORICAL SNAPSHOT...
  discoverability index, not a live tracker"; sole open todo is still an umbrella over 6 independently-scoped major
  workstreams, several operator-gated, not a single determinable outcome. Cross-cutting tranche, batch 2 of 3.
- **2026-08-22 — ruling D1 (Stale meta-doc disposition)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Approve all — repeated audits agree these are churn, not live tasks; the two
  keep-open items and the one split are the only exceptions. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
