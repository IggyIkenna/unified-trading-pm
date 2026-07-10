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
    instruments_docs_audit_outstanding_items_2026_07_08.md,
    instruments_service_plan_reconciliation_2026_06_29.md,
    ../instruments_completion_tracker_2026_07_06.md,
    ../instrument_id_format_canonicalization_2026_07_08.md,
    ../layer1_remeasure_and_certify_2026_07_06.md,
    mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
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
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-10
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
4. **59-bug MTDS + instruments-service adapter smoke test** — master record, 12 fully open todos incl. multiple P0 crash
   risks (Deribit live-WS misclassification, Polymarket `book_snapshot_5` schema crash) — CODE_PATH §1.3.
5. **Instruments Completion Tracker** — the master coordinator itself, 33 of 37 items still open
   (denominator-correctness, Stage 3 re-measure, Stage 5 capture-to-100, Decision Gate D6) — MANIFEST_COVERAGE §2.2.
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
   operator decisions (GMX V2 coverage, IDLE/JITORESTAKING/SYMBIOTIC/KARAK empty-feed acceptance).

### P1

4. **DeFi lending — real A_TOKEN/DEBT_TOKEN split needed** (one sub-item P0: Compound V3 invalid-enum crash risk)
   `plans/active/issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` AAVE_V3/SPARK relabel, Compound V3
   crash-risk fix (needs GCS migration), MORPHO model change, plus operator-approved generalization to
   FLUID/VENUS/RADIANT/EULER_V2/BENQI/MARGINFI/SOLEND.

5. **Issue-docs remediation sweep — 12 remaining code-fixable items**
   `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md` MTDS liquidations/risk_params reconcile for
   radiant/euler, strategy-service staked-lending catalog entries, deployment-ui `DataStatusTab` hardcoded service list,
   deployment-api E2E trace feature, execution-service `service_name` drift, a SIT manifest-import-alignment QG
   violation, plus 3 `tofu apply` infra items pending operator execution.

6. **DP alert-flood triage — 06:00-UTC TradFi OHLCV OOM crash-loop** (+ a terraform-default drift risk)
   `plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` Root-cause + run-to-completion still
   open; separately, `deployment-service:latest` doesn't yet carry the wave-launcher sentinel writer (a `tofu apply`
   would silently revert the live pin).

7. **order-book imbalance computed independently in BOTH MTDS and MDPS**
   `plans/active/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md` Core duplication resolved; 2 open:
   UAC-side retirement of stale capability/pipeline_mode declarations, historical-agreement verify.

8. **WSFeedConnector Phase-3.5 rollout gap — 73 unregistered venues**
   `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` COINBASE bare-name removal blocked on a
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
    QG) `plans/active/issues/fleet_data_acquisition_health_2026_06_21.md`

11. **instruments-service's `--run-tag` CLI flag doesn't do what its help text says**
    `plans/active/issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md` 3 todos unchecked: decide
    direction, implement, ship.

12. **TradFi's mvp_mode fetch-time filter is unreachable dead code**
    `plans/active/issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` Zero callers workspace-wide; 3 todos
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
`DP-<CATEGORY>-<NNN>` alert registry (`codex/05-infrastructure/data-pipeline-alerts.md`), not a new mechanism. Proceed
as proposed.

**2. is-daily-enum-{prediction,sports} exit(1)** — conflicts: none. Design: aligned (`exc_info=True` is additive
observability, doesn't touch the shard-isolation no-raise contract). Proceed — pure unblock, can't diagnose without it.

**3. 59-bug MTDS + IS adapter smoke test** — conflicts: **with #8** (see below). Design: HUOBI/BITSTAMP venue-fix
location and ETHENA's fabricated-value fix both align with SSOT. Proceed, but resolve #8 first for the COINBASE-FUTURES
venue entry specifically.

### P1

**4. DeFi lending A_TOKEN/DEBT_TOKEN split** — conflicts: **with #5** — `issue_docs_remediation_sweep_2026_06_02.md` has
an open, unchecked todo wiring VENUS/BENQI/RADIANT/EULER_V2 into strategy-service as usable lending legs, but #4's own
findings (2026-07-07, a month later) say those same 4 protocols currently emit an invalid `InstrumentType` that will
raise `UnknownInstrumentTypeError` the moment a real position needs P&L attribution. #5 predates #4's finding and hasn't
been updated. Design: aligned with `instruments-service-as-ssot-for-mtds.md` + the strategy layer's own existing
`is_supply`/`is_borrow` assumptions. **Recommendation: proceed on #4; flag #5's strategy-service todo as
blocked-behind-#4, don't pick it up standalone.**

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

**9. Infra capture wiring (AO Plan 6)** — conflicts: none (ASTER's book5/liquidations gap in #9 is narrower than and
complementary to #8's general trades-key registration). Design: the self-block to avoid a 17,282-row over-seed is the
data-pipeline-correctness HARD RULE in practice. Proceed as proposed — stay blocked until the 2 named prerequisites
land.

### P2

**10. Fleet data-acquisition health sweep** — conflicts: none. Design: the proposed case-insensitive
`_resolve_connector` fallback is a tolerant-reader workaround for a registry casing inconsistency (cefi uppercase,
defi/prediction lowercase, no stated reason) rather than canonicalizing the casing itself — diverges slightly from this
workspace's broader instinct toward canonicalization over tolerant fallback. Not a hard violation. **Recommendation:
needs a design call — accept the fallback as permanent, or use this as the trigger to canonicalize venue-key casing
across the registry (cleaner, larger).**

**11. `--run-tag` CLI flag doesn't do what its help text says** — conflicts: none. Design: **the issue doc frames this
as a wide-open operator decision — it isn't.** `codex/08-workflows/t1-batch-dag.md` already documents the target
`--run-tag` behavior verbatim, and instruments-service's own code already special-cases the exact `"t1-recon"` sentinel
from that SSOT, just never implements the GCS-prefix redirection. **Recommendation: proceed with wiring it through (not
deleting/re-describing it) — that's the option that brings the code into compliance with the already-documented target;
the issue doc is missing the cross-reference.**

**12. TradFi `mvp_mode` dead fetch-time filter** — conflicts: none (soft note: #13 Phase 5 extends the same MVP registry
with 3 KRX equities — no action needed as long as future wiring reads it live). Design: genuinely open — unlike #11, no
SSOT pre-answers whether a fetch-time filter should exist. Proceed as proposed, decision is real.

**13. Crypto-venue equity-perps + tokenized stocks Phase 2** — conflicts: none against other CODE_PATH items. Design:
**authored 2026-06-20, before the 2026-07-08 one-canonical-builder decision** this whole audit doc's §5 tracks (the
effort retiring ~48 DeFi adapters' ad hoc f-string `instrument_key` construction). Implementing Phase 2 as originally
written — without checking whether the new `EQUITY_PERP`/`TOKENIZED_EQUITY` ids should route through the shared
canonical builder — would add a fresh instance of exactly the pattern being retired elsewhere. **Recommendation:
re-check Phase 2's instrument-id construction against the canonical builder before implementing.**

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
   capture-to-100, Stage 6 hygiene, + open Decision Gate D6 (shard-dimension model).

3. **Layer-1 re-measure + certify (Stage 3), AO Plan 4** `plans/active/layer1_remeasure_and_certify_2026_07_06.md` 1 of
   8 open: tradfi `BLOCKED-PLAN2` pending `tradfi_v9_stage1_finish` tasks 2–11 (cannot certify against a stale pre-v9
   catalogue). cefi/defi/prediction/sports freshly certified with real evidence.

4. **CeFi legacy gap-fill + manifest canonicalisation (single-walk) — L3 owner for cefi**
   `plans/active/cefi_manifest_canonicalisation_2026_06_01.md` 1,980 lines, 26 unchecked / 56 checked: v9 apply-time
   migration remaining tranches, F2 (cefi FUTURE bundle-grain rollup), deployment-api dedup/filter fixes,
   execution-service DeFi raw-path fix, operational catalog-path could-exist seed run.

5. **prediction_manifest_canonicalisation — L3 owner for prediction**
   `plans/active/prediction_manifest_canonicalisation_2026_06_01.md` 15 unchecked / 66: C0 bundled legacy→canonical
   walk, pipeline_mode/source riders, post-walk verify, E3 writer-drain confirm, E4 dry+full VM run, E7 CF-audit, E8
   legacy-bucket delete handoff, cross-AG v2-enumerator rollout, QG import-pattern gate finding.

6. **tradfi_v9_stage1_finish — AO Plan 2** `plans/active/tradfi_v9_stage1_finish_2026_07_06.md` 6 of 11 unchecked,
   heavily evidenced: orphan sweep (blocked on manifest rebuild ordering), straggler VM re-run, manifest rebuild 99.77%
   not 100% (13,971-row v4 tail + 42K blank-pipeline_mode gap), E7 CF-audit 2 genuine REDs, schema-tail restamp blocked
   on fleet-drain, operator-gated legacy-bucket deletes.

7. **BYBIT-SPOT manifest — 135,444 anomalous rows, checkboxes claimed done but production is unchanged**
   `plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md` **Moved back here 2026-07-10** — a second
   verification pass (while flipping resolved-but-not-flipped docs) found this one's `[x]` todos cite only that the fix
   scripts were _shipped_ (dry-run/--smoke/--apply modes exist), not that `--apply` actually ran. Live manifest read
   (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, 2026-07-10) shows row
   counts byte-identical to the original 2026-07-07 diagnosis: 81,659 EMPTY-instrument_type + 53,785
   PERPETUAL-mislabeled rows, plus ~54K stray spot-nonsense-data_type rows (derivative_ticker/futures_chain/
   options_chain/perp_funding/liquidations — none valid for a SPOT venue). No pre-apply backup snapshot exists at either
   expected path. The real fix (relabel + delete) has never actually been executed against production.

### P1

7. **DeFi expected_unattempted backlog ≥1M cells**
   `plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` Operator-gated manifest-seeding write never
   applied; `BLOCKED-OPERATOR-DECISION` on apply-scope; 1 VERIFY P2 todo to check other asset groups.

8. **Honest-coverage shard dimension model is wrong for definitional data** (Decision Gate D6)
   `plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` Writer fix, DataStatusTab
   UI fix, bare-BYBIT/OKX phantom removal shipped; open: widen writer fix to 7 Solana DeFi venues + CURVE-OPTIMISM,
   retire DERIBIT-COMBO as its own venue key, remove phantom `OPTION` from bare OKX, move `market_metadata` off the MTDS
   daily axis, backfill historical rows, add `missing_dates` to breakdown entries, spot-check 5 more CeFi venues.

9. **Phantom captures — defi manifest (2026-06-28)** `plans/active/issues/phantom_captures_defi_2026_06_28.md` 219,529
   `captured` rows with no backing parquet (10.5% of captured defi scope), concentrated in `swaps_ohlcv_*`/UNISWAP_V4. 3
   unchecked: diagnose systematic writer failure, apply reconciliation, confirm no recurrence.

10. **cefi Layer-1 denominator silently omits whole venues with real captured data**
    `plans/active/issues/cefi_layer1_denominator_gaps_2026_07_03.md` 2 `BLOCKED-OPERATOR-DECISION` remain: bare
    COINBASE/DERIBIT-COMBO in `MVP_SCOPE.venues`; OKX-SPOT zero EXPECTED tuples (interim P0 fix shipped, DESIGN decision
    Option A vs B still open).

11. **honest_coverage_smoke_harness — 4-AG live-run discrepancies**
    `plans/active/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` 3 of 4 shipped; 1 remains (re-run
    `run_live_verify_tradfi.py` once `tradfi_v9_stage1_finish` tasks 2-11 land) — self-parked after 4 dispatch bounces.

12. **manifest_consolidator_dtype_at_source_fix** (`status: draft`)
    `plans/active/manifest_consolidator_dtype_at_source_fix_2026_07_07.md` Both todos open: trace + fix the DuckDB merge
    that persists numeric columns as utf8 in the canonical `_index` (root cause of the prediction+sports capture-death
    incident). Not urgent (reader-side coercion crash-proofs it) but canonical index still dishonestly typed.

13. **e2e DeFi strategy configs — taxonomy/wizard round-trip fidelity gaps**
    `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` 9 unchecked: D2 (wizard can't
    reproduce tuned configs), D3 (missing Solana-DEX-spot wizard cell), D4 (blocked-credentials), collateral-aware
    down-sizing not implemented, dead YAML key, hardcoded per-LST spot venue, wizard exposes ~0 of the numeric param
    surface. D1 explicitly INTENTIONAL.

14. **mvp_scope_catalogue_tagging** — 2 of 10 unchecked `plans/active/mvp_scope_catalogue_tagging_2026_06_08.md`
    Features/strategy/model MVP sections not started (no consumer endpoint yet); full real-data MVP-toggle verify
    blocked on a paused manifest consolidator behind a held migration.

15. **predictions_other_bucket_and_ui_drilldown** — 3 of 11 unchecked
    `plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md` UI re-walk VERIFY blocked on a
    UI-capable/playwright slot; Phase-5 canonical-groups backfill for ~24 remaining groups (has a real UAC-registry SSOT
    component); prediction sentinel fan-out fix for honest `empty_confirmed` on zero-trading-day canonical groups.

### P2

16. **Empty re-probe disagreements — today's new empties may be C1 bugs**
    `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` Auto-filed daily-audit doc; candidate CSV referenced
    but disposition/trace not done.

17. **Manifest hygiene RED — 2026_06_27** — `plans/active/issues/manifest_hygiene_red_2026_06_27.md` 1 unchecked
    diagnose+fix todo (defi: schema_version_not_v9, oracle_expects_but_empty, noncanonical paths, phantom_captured,
    shard_4pillar_fail), untouched since filing.

18. **Manifest hygiene RED — 2026_06_29** — `plans/active/issues/manifest_hygiene_red_2026_06_29.md` Same pattern, cefi.
    1 unchecked todo, untouched.

---

## 3. SSOT

Cross-doc / cross-registry contradiction, drift, or design-authority gaps.

### P1

1. **Instruments-Service Plan Reconciliation — open plans vs SSOT**
   `plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md` 986-line cross-plan contradiction audit
   (67 plans vs live UAC+codex). Most of C1–C9 resolved, but **C6, C7, C9 still "AWAITING IKENNA"**, **C5
   "with-Ikenna"** (Deribit options false-complete), and Section F plan-consolidation/archival (F.1–F.4) awaiting
   operator sign-off.

2. **UAC data-type-validity combinator is fragmented across CEFI/DEFI/TRADFI**
   `plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` No asset group has a real
   `(venue, instrument_type) → data_types` table; a live provably-wrong cell exists (CME/ICE identical `futures_chain`
   valid-data_types despite ICE having no Databento coverage); DeFi's two capability registries have drifted. 6
   unchecked todos incl. a proposed two-layer redesign pending operator approval.

3. **DeFi hardcoded on-chain-derivable values + UAC date-drift elimination**
   `plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md` Phases 5–5.6 shipped; 2 residuals: operator
   go/no-go on Pyth Hermes jitoSOL pre-2023-10 backtest scope, and a "Bug-class-3" sweep for local fallback dicts
   silently overriding UAC values.

### P2

4. **Carry archetypes declare CEFI venues but ARCHETYPE_CAPABILITY_REGISTRY has no CEFI cells**
   `plans/active/issues/archetype_venue_universe_cefi_vs_registry_no_cefi_cells_2026_06_30.md` Confirmed codex↔registry
   contradiction (`CARRY_BASIS_PERP_INV`/`CARRY_STAKED_BASIS`); awaiting strategy-owner decision (add cells vs. trim
   doc).

5. **DeFi pipeline — code↔codex drift (audit 2026-05-27)** `plans/active/issues/defi_code_codex_drift_2026_05_27.md`
   D1–D9/D13/D14 done; 2 open: D10 (6 DeFi venues `phase=live` with no backing capabilities — needs operator confirm),
   D15 (HYPERLIQUID/ASTER phase-label reconciliation).

6. **instruments-service quality-gates.sh RED on LDR HEAD — CEFI expected-universe drift**
   `plans/active/issues/instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` P0 fix/verify done (reverted, QG
   green). 1 DESIGN todo open: `BLOCKED-OPERATOR-DECISION` — keep the interim permanent 2-tuple bare-BYBIT phantom, vs.
   declare `OKX-SPOT` its own venue and remove the `_CEFI_VENUE_FOLD` entry.

7. **COINBASE bare-name UAC removal + downstream caller migration** (`status: draft`, not dispatched)
   `plans/active/coinbase_bare_name_migration_2026_07_06.md` Full 7-step (S0–S7) multi-repo migration plan (44 UAC + 5
   IS + 4 MTDS + cross-repo callers) awaiting operator flip to `active`; all steps unchecked.

---

## 4. DOCS_RECONCILIATION

### P1

1. **Instruments-service docs audit (2026-07-08) — consolidated outstanding items across all 7 asset docs** (spans
   CODE_PATH too) `plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md` 604-line, sections A–H.
   A1/A2/B3 resolved. Open: §B canonical-id builder adoption (~4/63 adapters — overlaps the big canonicalization
   effort), §C (6 DeFi adapter/coverage gaps: no A_TOKEN/DEBT_TOKEN split for 6 lending protocols, MARGINFI/SOLEND
   missing adapters, hardcoded `YEARN-ETHEREUM`, Solana key/field mismatches, live DEX-swap streaming placeholder-only),
   §D (Prediction/Sports wiring gaps: `build_cross_venue_mapping()` never wired, `sports-odds-ready` publisher never
   built). §H (TradFi) explicitly deferred.

---

## 5. INSTRUMENT_ID_CANONICALIZATION

### 5a. Already tracked inside `instrument_id_format_canonicalization_2026_07_08.md`

The big canonicalization effort (`plans/active/instrument_id_format_canonicalization_2026_07_08.md`) is already
exhaustively self-tracked — its own sub-detail is NOT re-listed here. Noted only as existing; several items below are
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
   `plans/active/canonical_id_p0_kraken_futures_collision_2026_07_08.md` 6 of 7 shipped/verified (125 files, 37.5M rows
   corrected). 1 new P2 todo: a discovered `FI_`-vs-`FF_` same-(ticker,expiry) instrument_id collision — needs an
   operator decision on a contract-subtype marker. Distinct finding from the big effort, directly related.

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
   `plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` Ongoing churn (overage
   bouncing 380→368→377→372 across concurrent sessions); latest entry shows instruments-service still 3 sites over its
   ratchet baseline, still blocking quickmerge pushes.

6. **predictions_lookahead_and_reader_migration** — 1 of 5 unchecked
   `plans/active/predictions_lookahead_and_reader_migration_2026_06_20.md` Register predictions `feature_groups` into
   UAC `FEATURE_REQUIRED_INPUTS` per canonical_question_group + binary-outcome — not started.

7. **features-service DeFi end-to-end test blocked on multiple data layer issues**
   `plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md` Narrative-only; doc's own final note
   says the four DeFi operator-decisions remain open. PRD's `dex_swaps`→`dex_pool_swaps` rename makes all UNISWAP V3
   invisible to features-service; legacy-bucket manifest never registered its most important pool; OHLC values look
   wrong for `dex_swaps` (price≈1.0 for ETH/USDC); duplicate schema columns. Parallel CeFi path found 3 more bugs (MDPS
   column-order drift, tz-aware/naive join mismatch, filter-pushdown memory bug) — unclear if fixed elsewhere, flagged
   uncertain-but-not-excluded.

### P2

8. **No generic manifest-reprocessing mechanism — 11 near-identical one-off reclassify scripts**
   `plans/active/issues/manifest_reprocessing_generic_utility_2026_07_07.md` 4 unchecked: design + build
   `select_shards_for_reprocess()`, wire as IS CLI subcommand, retire the 11 one-offs.

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
    `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` Highest-priority live item: POLYMARKET
    instrument lifecycle `available_from`/`available_to` never populated → manifest emits `empty_confirmed` outside a
    market's real life instead of honest blank (P0 honest-absence bug). Also open: Polymarket-perp reference-data
    adapter BLOCKED-UPSTREAM (no public perps API), residual lowercase/blank/UNKNOWN `venue` rows splitting the Kalshi
    denominator, 1,454-row v4 schema tail, UAC politics/geo cross-venue canonicalization + same-event arb-pairing design
    gaps.

12. **carry_staked_basis_funding_scan_experiment** — 49 unchecked of 54, exploratory research harness
    `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md` Mostly strategy-research backlog (live venue
    wiring dYdX/Vertex, LST APR source wiring, gas/slippage cost modeling, `share_class` axis). Two real non-backfill
    code bugs buried in it worth flagging separately: `lending-indices`/`lst-rates` writer targets a legacy un-suffixed
    bucket key instead of the canonical one (lines 236, 497) — a GCS_BUCKET_MIGRATION-class bug.

13. **master_to_live_defi — May-23 cutover master** `plans/active/master_to_live_defi_2026_05_23.md` Only 4 of 172
    unchecked, all nested under one already-`✅ DEFERRED-FUTURE-WORK`-tagged parent: DART terminal manual-trade lane
    (real-time archetype rendering, manual trade entry through execution-service, monitored window, automation-toggle
    gate). Real unbuilt UI/execution work, explicitly deferred beyond May-23 scope, not urgent.

---

## Excluded (resolved-but-not-flipped, or superseded — verified across all 4 shards)

**UPDATE 2026-07-10**: all 15 genuinely-resolved docs below have now been re-verified a SECOND time and their `status:`
frontmatter flipped for real (`unified-trading-pm@8f15f8233`). **One of the original 16 was NOT flipped —
`bybit_spot_manifest_stray_captures_2026_07_07.md` is a real, still-open gap**, moved back into §2 MANIFEST_COVERAGE
below: its checkboxes claimed the 53,785-row PERPETUAL relabel and 53,934-row spot-nonsense delete were done, citing
only that the fix scripts were _shipped_ — a live production manifest read (2026-07-10) found the real row counts
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
- `plans/active/canonical_id_p1_onchain_perp_perp_shorthand_2026_07_08.md`
- `plans/active/issues/features_read_book_columns_not_snapshots_2026_06_28.md`
- `plans/active/canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`
- `plans/active/foundation_gates_and_capture_to_100_2026_07_06.md`
- `plans/active/mdps_features_full_month_benchmark_binance_2026_06_28.md`
- `plans/active/instruments_catalogue_incremental_rollup_2026_06_29.md` (1 residual `[ ]` is an operator-declined
  optional band-aid, not real work)
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

- 2026-07-10: Synthesized from a 4-shard parallel sweep of 83 real doc-index-derived candidate lines across
  `plans/active/**`; 62 docs kept as genuinely open non-backfill work across 7 categories, 16 excluded as
  resolved-but-not-flipped, 3 fragment lines flagged uncaptured. Read-only audit — no code or plan checkboxes changed.
- 2026-07-10 (later): Added category definitions (§ Category definitions) and a full CODE_PATH conflict +
  target-architecture review (§1a) per operator request. Re-verified and flipped 15 of the 16 excluded docs for real
  (`unified-trading-pm@8f15f8233`); the 16th (`bybit_spot_manifest_stray_captures_2026_07_07.md`) was found to still be
  genuinely open — its checkboxes claimed done but production data shows the fix was never actually applied — moved into
  §2 MANIFEST_COVERAGE P0 instead of flipped. §1a found 2 real mutual conflicts (item #3/#8 COINBASE-FUTURES
  contradiction, item #4/#5 sequencing risk) and 3 items diverging from documented target architecture (items #10, #11,
  #13) among the 14 CODE_PATH items.
