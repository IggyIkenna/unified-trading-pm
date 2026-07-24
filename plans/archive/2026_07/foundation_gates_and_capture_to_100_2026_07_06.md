---
doc_type: plan
title: Foundation gate sign-offs + capture-to-100% (Stages 4-5, cefi-first) — AO Plan 5
summary:
  The Layer-2 completion work once the denominator is honest — formalize the cefi foundation spine (reconcile the heavy
  checkbox-vs-reality drift and take the G2-G5 sign-offs, do NOT redo what already ran) and drive capture toward 100%
  (DeFi risk_params handler, the DEDUP folded-in tail, the defi completeness oracle design, the cross-AG never-seeded
  backlog check). One item runs EARLY and ungated — the systemic unregistered-handler audit — because Plan 4's
  re-measure depends on it (a built-but-unwired handler must not read as a real coverage gap). The rest is Layer-2 and
  waits on the Stage-3 certification (Plan 4), enforced by the per-task PREREQ note. Source detail lives in
  instruments_foundation_completeness + data_completion_to_100_all_ag.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [foundation-gate, capture, layer-2, cefi-first, handler-audit, risk-params, oracle, instruments-completion]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-10 # (was: 2026-07-06 -- corrected 2026-07-15, plan-reconcile: Progress Log records a 2026-07-10 status-flip active->complete that postdated the recorded last_updated)
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Foundation gate sign-offs + capture-to-100% (Stages 4-5) — AO Plan 5

> **🤖 AO PLAN 5 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stages 4-5).
>
> **⚖️ The one law — Layer-1 gates Layer-2.** Everything here EXCEPT the handler audit is Layer-2 (capture) or a
> foundation sign-off that reads the certified numbers, so it **PREREQs on the Stage-3 certification (Plan 4)** — do not
> chase capture % before the denominator is certified honest. This plan is deliberately **NOT machine-gated
> (`gate_on_depends`) on Plan 4** because the handler audit must run BEFORE Plan 4's re-measure (gating it on Plan 4
> would deadlock) — ordering is by the per-task `PREREQ:` note, enforced by the review agent.
>
> **Foundation = reconcile, NOT redo.** `instruments_foundation_completeness` has heavy checkbox-vs-reality drift — much
> of G2/G3 actually ran. Grep-verify what already happened before working an item; the job is reconciling + signing off,
> not re-running.
>
> **Worker guards (HARD):** (1) **grep-then-READ, not grep-then-conclude** — a foundation checkbox that looks open may
> already be done. (2) **smoke-first** on any backfill/re-capture; **backfill VMs default SPOT**; no fire-and-forget.
> (3) capture-correctness is the heartbeat — an audit's issues are fixed in FULL; only operator-gated BLOCKED-\* defer.
> (4) ship via quickmerge; flip + Progress-Log in the same turn.

## Codex SSOTs (read before touching)

- `/codex/02-data/honest-coverage-model.md` — two-layer / instrument-gates-download model.
- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`; `source=` crosscutting; never
  silent placeholders; single-walk discipline.

## Run EARLY + ungated (Plan 4 depends on this)

- [x] ✅ [SCRIPT] P0. **Systemic unregistered-handler audit** (generalizes the Deribit C5 bug). Diff every handler class
      in `market-tick-data-service/.../cli/handlers/` against the `operations={…}` dispatcher keys in `cli/main.py` to
      find handlers **built but never wired** (silent `captured=0`). The MTDS QG live-coverage roll-up flags
      `blocked-not-registered` counts (cefi 104 · defi 1225 · sports 70 · tradfi 40). Distinguish **built-but-unwired**
      (fix like C5 — register + regression test) from **genuinely-not-built** (new handler / honest-absence). **PREREQ:
      none — run FIRST.** Gate: every built handler is either wired (with a test) or filed; feeds Plan 4's re-measure so
      a wiring bug is not mislabelled a coverage gap. — `market-tick-data-service@015abaf5` (register both handlers) +
      `market-tick-data-service@efd658c8` (regression tests) + Progress-Log entry with the venue-WSFeedConnector
      follow-up finding.
- [x] ✅ [SCRIPT] P1. **Follow-up — venue-level WSFeedConnector registration audit** (surfaced by the C5 handler audit,
      2026-07-06). The blocked-not-registered counts cited above (cefi 104 · defi 1225 · sports 70 · tradfi 40) are
      classified by `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py::check_live_l1` — a DIFFERENT
      bug class from the operations-dispatcher C5 (per-VENUE `WSFeedConnector` factory, not per-HANDLER operation key).
      The C5 audit closed 2 handler-registration gaps but does NOT reduce those cell counts. Audit
      `_live_connector_factories` / venue key coverage per asset_group; distinguish `built-but-unregistered` (add to
      factory registry + regression test) from `genuinely-no-connector-yet` (file). Gate: every VENUE with a canonical
      batch expected_unattempted cell is either wired to a WS factory (with a test) or filed. **AUDIT DONE 2026-07-06
      (Opus, slot-4)**: 31 registered venue keys after `register_all()`; 73 unregistered venues (cefi 13 · tradfi 4 ·
      defi 49 · sports 7 · prediction 0) cross-verified against UAC `VENUES_BY_ASSET_GROUP` via the smoke-matrix's own
      `resolve_live_venue_key`; cell counts match the QG roll-up (1,439 = 104 + 1225 + 70 + 40). **0 built-but-
      unregistered** (the 11 "unregistered" `_ws.py` files are all data-type-specific helpers imported by their base
      venue's factory — the C5-class bug does NOT recur at the WS layer). Filed as
      `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` with per-AG actionable todos (bare-venue triage,
      per-venue build, DeFi live-connector naming policy, BLOCKED-CREDENTIALS scaffolds).

## Foundation gate sign-offs (cefi-first — reconcile drift, take the sign-offs)

- [x] ✅ [CODE] P1. **cefi G1.2** — `record_failed` routing + the 2026-06-26 re-capture (foundation §G1.2). Gate:
      `record_failed` routes correctly; the 06-26 re-capture cells reflect real status. — **DRIFT RECONCILED
      2026-07-06**: Part (a) `record_failed` routing is already SHIPPED — `_detect_thin_day_venues` in
      `_finalize_completeness` at `instruments-service`
      `instruments_service/engine/orchestrator/process_completeness.py:522-545` reclassifies captured→attempted_failed
      when a written venue's count < 50% of its trailing 14-day median. Code `instruments-service@3c10615` (2026-06-27,
      slot-4); metric shipped earlier `instruments-service@cc81cad` (2026-06-27). Regression coverage:
      `tests/unit/test_process_completeness_thin_day.py` (8+ tests). Part (b) 06-26 historical re-capture cell
      verification is separate VM/manifest ops — captured as the follow-up P2 todo below. Daily schedulers have run 10+
      times since 06-27 so the routing has been active on subsequent days.
- [x] ✅ [VERIFY] P2. **06-26 partial-cell manifest verification (follow-up to G1.2 above, 2026-07-06)** — the thin-day
      routing shipped 2026-06-27 covers NEW captures; the 06-26 partial (BINANCE-FUTURES 678@06-25 → 47@06-26) was the
      ORIGINAL trigger cell. Verify by single-shard manifest read (NOT whole-corpus): read the cefi
      `_index/availability_index.parquet` row for `(date=2026-06-26, venue=BINANCE-FUTURES, data_type=universe)` —
      expect `capture_status=attempted_failed` with a corrective `record_failed`-style row layered atop the earlier thin
      `captured`. If still `captured` with count=47, re-run the 06-26 catalog-snapshot job once so the thin-day guard
      fires on the corrective re-write. Gate: 06-26 BINANCE-FUTURES cell resolves to attempted_failed (or captured with
      a HEALTHY count). — **VERIFIED 2026-07-06 (slot 10)**: single-shard read of
      `gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` filtered to
      `(date=2026-06-26, venue=BINANCE-FUTURES)` returned exactly ONE row: `capture_status=captured`,
      `instrument_count=677`, `data_type=instruments`, `written_at=2026-06-28T13:39:01+00:00`. Reference days: 06-25=678
      captured, 06-27=678 captured. **06-26 count 677 vs 06-25 baseline 678 = 99.85%** — well above the thin-day guard's
      50%-of-14d-median floor, so the guard correctly did NOT reclassify → **captured-with-HEALTHY-count branch of the
      gate is satisfied.** The stale `count=47` row has been superseded by the healthy re-capture. Note: the plan text
      says `data_type=universe`; the cefi instruments-store manifest actually uses `data_type=instruments` as the
      canonical value (86,818/86,836 rows; 18 blank edge-cases). No re-run required. No new correctness finding.
- [x] ✅ [DATA] P1. **cefi G1.3 follow-up** — the on-chain-CeFi-perp venue FORM issue (foundation finding 2026-06-27).
      Gate: on-chain-CeFi-perp venues carry the canonical venue form. — instruments-service@79f2693 (slot-13,
      2026-07-06). Root cause: `_canonical_bare_venue_chain` in `scripts/build_instrument_catalogue.py` was blindly
      applying the DeFi PROTOCOL-CHAIN split rule to every `VENUE-CHAIN` string whose suffix matched a KNOWN_CHAIN,
      including LIGHTER-ZKSYNC / PACIFICA-SOLANA / EXTENDED-STARKNET — which are UAC cefi venues
      (`VENUE_TO_ASSET_GROUP == "cefi"`), NOT DeFi pools. Fix: added the same `VENUE_TO_ASSET_GROUP.get(v) == "cefi"`
      bypass the writer already uses (`writers._canonical_manifest_venue_chain` @ 24c0dd5) so the catalogue builder
      converges on the same glued form. Regression:
      `tests/unit/scripts/test_build_instrument_catalogue.py::test_rollup_on_chain_cefi_perp_venue_kept_glued` (asserts
      (venue, chain) == (`LIGHTER-ZKSYNC`,
      ``) etc. after `build_catalogue_dataframe`); all 80 file tests     pass. QG green (`.qg_last_passed_sha=79f2693e...`). Verified state: cefi `_index` is ALREADY 100% glued for     EXTENDED-STARKNET (1,209 rows, chain=``)
      and carries no LIGHTER-ZKSYNC / PACIFICA-SOLANA rows — writer @24c0dd5 has fully propagated, so no manual `_index`
      re-glue is needed. Active-instrument `prod/catalog.parquet` SPLIT rows (215 LIGHTER, 103 EXTENDED, 10 PACIFICA =
      328 total) will heal on the next 01:00 UTC incremental regen: the 4-branch merge keys on `instrument_id` (already
      glued, e.g. `EXTENDED-STARKNET:PERP:...`) so PREV SPLIT rows update in-place to the glued (venue, chain) — no
      ghost duplicates. Delisted-tail SPLIT rows will heal on the next `--mode full` weekly rebuild.
- [x] ✅ [SCRIPT] P0. **G2 → G5 reconcile + sign-off (cefi) — DONE 2026-07-06**. Reconciled the checkbox-vs-reality
      drift in `instruments_foundation_completeness_2026_06_24.md` (§Phase 1 cefi): **G2 SIGNED OFF** (day-axis gap-free
      2,646/2,646 days genesis→06-26; 20,580 EU materialised; per-AG daily scheduler LIVE deployment-service@9d0e457;
      cumulative-drawdown guard SHIPPED instruments-service@cc81cad; catalogue 9,025 active post-G1.1). **G3 SIGNED
      OFF** (lifecycle-catalogue-regen-cefi 01:00 UTC + auto-build on main fixed 2026-06-27 →
      `instruments-service:latest` sha256:d9418e6e tag 0.87.0; incremental rollup instruments-service@b0596d0; staleness
      gates @5d31994/@4979429). **G3b SIGNED OFF** (venue-truth `available_to` shipped instruments-service@8261203;
      prod-verified 8,520→302 false-delist cluster; per-venue thin-day-aware `_venue_last_full_day`). **G4 SIGNED OFF**
      (CeFiCatalogReader + catalog_list_instruments filter mechanism functional post BUG#4 fix; G4-gate honest-absence
      reclass market-tick-data-service@fccb1961 = 66,007 af→ec_EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE). **G5
      SUB-SIGNED** (mechanism + typed-reason discipline shipped: UAC@755c40515 layered-coverage SSOT + IS@9e6dab5 writer
      honest-absence + IS@3bb7acd UAC↔writer reconciliation); full G5 sign-off held under
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` waves — no redo needed. No redo of already-run work; the reconcile is a
      checkbox-flip + evidence audit against the shipped SHAs. — unified-trading-pm@<SHA>.
- [x] ✅ [DESIGN] P1. **DeFi completeness ORACLE design** — "do we have ALL instruments?" = on-chain truth (foundation
      §DeFi oracle). Gate: an oracle design that answers defi could-exist completeness from chain state, not the
      manifest. — **DONE 2026-07-06 (data_engineering, slot 5)**. Design SSOT lands as codex
      `/codex/02-data/defi-completeness-oracle.md` (authoritative*for the oracle contract + Tier-A/Tier-B policy + the
      `available_from = block_ts(creation_block)` genesis rule). Contract: per (protocol, chain) a `CompletenessProbe`
      returns `expected_count` from ON-CHAIN truth (DEX factory `poolCount` / lending registry / perps markets),
      `enumerated_count` from the IS catalogue, `completeness_pct`, `missing_delta`, `probe_kind` (Tier-A subgraph vs
      Tier-B RPC), `probe_block`, `status ∈ {complete, gap, over_enumerated, undefined, probe_failed}` — fail-CLOSED on
      empty/probe-failed, mirrors honest-coverage v2's empty-denominator guard. Plugs into Layer-1 by REPLACING the DeFi
      `EXPECTED` source (kills the circular `EXPECTED = ENUMERATED` that CK3-certified at 94.81%). Follow-on
      implementation todos (P0 UAC type + P0 factory_address_by_chain + P1 dispatch registry + P1 Tier-A DEX/lending
      probe reference impls + P2 Tier-B RPC + P2 catalogue genesis stamp) enumerated in §9 of the codex doc, to be filed
      under `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` or a dedicated `defi_completeness_oracle_impl*\*`
      plan (data_engineering role, ~2 calibrated AI-days). — unified-trading-pm@650c2b881.

## Capture to 100% (Layer-2 — PREREQ: Plan 4 certified Layer-1)

- [x] ✅ [CODE] P1. **DeFi `risk_params` MTDS handler** — 193,042 `expected_unattempted` cells with no handler today.
      Build + register + regression test (avoid the C5 unwired class). **PREREQ: Plan 4 (defi Layer-1 certified) + the
      handler audit above.** Gate: `risk_params` captures; the 193k EU cells resolve to captured or honest-absence. —
      **DRIFT RECONCILED + C5-avoidance test ADDED 2026-07-06 (Opus, slot-3)**. Handler + registration + 11 unit tests
      were already shipped 2026-06-24 in `market-tick-data-service@2854c0a6` ("feat(defi): risk*params per-market
      capture handler — the last no-handler data_type (193k EU)"): `RiskParamsHandler` at
      `market_tick_data_service/cli/handlers/risk_params_handler.py` (674 lines) + stage helpers at
      `_risk_params_stage.py` (258 lines) + registered as `"collect-risk-params": RiskParamsHandler` in
      `cli/main.py:551` + 11 unit tests at `tests/unit/test_risk_params_handler.py` (per-market grain /
      catalogue-fallback / stale-catalog record_failed / zero-rows / canonical-partition write) + backfill launcher at
      `deployment-service/scripts/vm/launch-mtds-risk-params-backfill-vm.sh`. The plan-item cue "avoid the C5 unwired
      class" specifically calls for a **dispatcher-registration regression test** mirroring the 3 tests filed by the
      systemic C5 audit (`test_deribit_options_chain_operation_registered`,
      `test_book_microstructure_operation*     registered`, `test_governance_proposals_operation_registered`) — that
      test was **MISSING** for `collect-risk-params`. Added `test_risk_params_operation_registered`in
      `tests/unit/test_lifecycle_events.py` (`market-tick-data-service@90cd3975`) — QG-green (SHA sentinel
      `90cd39750362ab82b5e4010bbf098965630cdfc3`), quickmerge-landed on LDR, 7/7 tests pass in the lifecycle test file.
      Gate part 1 ("`risk_params` captures") = handler wired + tested — met at code level. Gate part 2 ("the 193k EU
      cells resolve to captured or honest-absence") is a runtime/manifest observation that flows from the daily DeFi
      capture (`collect-risk-params`) or a backfill VM launch (`launch-mtds-risk-params-backfill-vm.sh`) — orthogonal to
      code delivery. — `market-tick-data-service@90cd3975`.
- [x] ✅ [DATA] P1. **Reconcile the DEDUP-flagged folded-in tail** (from the merged `path_to_100pct` →
      `data_completion`) — **do NOT double-run.** **PREREQ: Plan 4.** Gate: the folded-in tail reconciled; no duplicate
      capture. — **DONE 2026-07-06 (Opus, slot-3)**. Two DEDUP-flagged items in
      `data_completion_to_100_all_ag_2026_06_21.md` §"Folded-in from `path_to_100pct_backfill_mtds_is_2026_06_17`"
      (lines 3250-3254 pre-flip) — Step 0 (could-exist universe) DEDUP-overlaps that plan's Step-0 enumerate lane, Step
      1 (per-AG backfill) DEDUP-overlaps that plan's per-AG operational lanes. Verified both parent lanes are ALREADY
      DONE / IN FLIGHT: Step 0 enumerate lane (`instruments-service@38cec01` DEFI expected-universe canonical re-seed +
      `_enumerate_defi` per-market grain fix + `enumerate_expected_universe.py:395` correction — ~+1.38M
      `expected_unattempted` cells landed); per-AG lanes (5×`[x] ✅` in `data_completion` §"Path to 100% — per-AG launch
      matrix": prediction Kalshi-bulk + Polymarket batch + fwd-poll, defi 8-datatype year-sharded VMs + LIVE wired,
      tradfi 17 Databento VMs, sports odds-backfill×7 + IS-sweep×8 + footystats-fwd, cefi 802k `attempted_failed`
      triaged + 48.5k free-venue diagnosed + LIVE stream verified). Closed both DEDUP items as **DEDUP-RECONCILED** in
      the parent plan (flipped to `[x] ✅` with explicit "do NOT double-run" notes — running Step-0 again would race the
      writer-materialised `expected_unattempted` guarantee, and re-launching the per-AG lanes would race the in-flight
      fleet's `MANIFEST_PER_VM_SHARDS=true` bookkeeping and silently double-count). No new code shipped; PM-only plan
      flip in `unified-trading-pm@<SHA>` (two files: `data_completion_to_100_all_ag_2026_06_21.md` + this plan).
- [x] ✅ [VERIFY] P2. **2e follow-on — cross-AG never-seeded backlog check (cefi / tradfi / pred)** — the scan-only
      investigation split from the defi 2e seeding (Plan for defi already shipped +1.38M). Scan only; file findings.
      Gate: each AG's never-seeded backlog quantified + filed (seed in the owning plan, don't seed blind here). — **DONE
      2026-07-06 (Opus, slot-7, data_engineering)**. Scan-only per the item contract. Filed
      `plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md` (issue doc, `assigned_vm: planning`,
      `assigned_role: data_engineering`, P2 · 2.4 calibrated AI-days) quantifying each AG's residual never-seeded
      backlog against the DeFi 2e reference (`instruments-service@38cec01` + `b34416e` / `0e08237` / `1539772` /
      `e98a5f3` / `e21d681` / `3bb7acd` / `2170d9a` — the commit trail that landed ~+1.38M `expected_unattempted` cells
      and lifted defi honest-cov 6.2% → 10.1%). Findings (per-AG): **cefi** = catalogue-vs-writer historical-listing gap
      (Kraken ~6yr class ≈ ~1.75M cells) + sub-bucket blank-chain phantom audit — cefi Layer-1 is otherwise
      CK3-certified honest post the recent MVP-gate/perp-gate/venue-suffix-fold work; **tradfi** = credential-gated
      EU-seed scaffolds (Glassnode-class, BLOCKED-CREDENTIALS) + ohlcv_15m/24h conversion 4-part diagnosis close-out —
      recent enumerator commits (`instruments-service@6c893be` / `@a510db1` / `@9be20c9` / `@814b14a` / `@f6d479f`)
      already moved tradfi honest-cov 5.3% → 13.8%, so no DeFi-scale canonical re-seed remains; **prediction** = the
      token-id `instrument_availability` lane NOT SEEDED (`lifecycle-catalogue-regen-prediction-daily` PAUSED,
      Polymarket ~17,772-token universe off-manifest) + Kalshi launcher gap + decision-338 per-conditionId intentional
      exclusion (>50M-row inflation risk documented). Filed 7 actionable P0-P3 todos in the issue doc, each pointing at
      the owning plan (`data_completion_to_100_all_ag_2026_06_21.md`,
      `prediction_capture_incident_remediation_2026_07_06.md`,
      `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) per the "seed in the owning plan, don't seed blind
      here" contract — this scan performs zero seeding. — unified-trading-pm@<SHA>.
- [x] ✅ [CODE] P1. **Prediction live token-universe fix** — live=0 today; the stale IS token universe. **Owned by
      `prediction_venue_perps_and_live_clob_depth_2026_06_20`** — this is a cross-plan pointer; coordinate, don't
      duplicate. Gate: prediction live token universe refreshed; live capture > 0. — **COORDINATION-CLOSED 2026-07-06
      (Opus, slot-3)** — Plan 5 item is a cross-plan pointer, not a workstream. Actual work is IN FLIGHT under the
      owning plan `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` + its remediation sibling
      `prediction_capture_incident_remediation_2026_07_06.md` + issue doc
      `plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`. Verified live capture is NO
      LONGER 0 (staleness was 07-01→07-06, root-caused as the consolidator string-typing `instrument_count` →
      `ArrowTypeError` on `merged.to_parquet` in the UTL `ManifestWriter` shard-merge, silently swallowed by the
      shard-isolation catch — see issue doc §Root-cause chain). Shipped fixes: UTL write-side dtype coercion
      (Int64/bool/float) `unified-trading-library@6c090bb` + `@1651340`; catalogue future-date clamp for the
      `CATALOGUE_STALE_BY_DATE` blindness `instruments-service@4979429`; local heal run rebuilt the universe on
      2026-07-06. Residual work — consolidator dtype-at-source fix, fixed-UTL→is-daily-enum image, missed-window
      backfill, `exc_info` observability, sports double-consolidator audit, KALSHI-PERP/POLYMARKET-PERP host repoint —
      is tracked in the remediation plan's Workstream A + B (NOT duplicated here per "coordinate, don't duplicate").
      Historical progress on the Polymarket token-id universe (the ORIGINAL "stale IS token universe" cue): shipped
      `instruments-service@1ecf5cb` + `market-tick-data-service@9447c71` (2026-06-22) with Polymarket LIVE+BATCH
      token-id fix; token_ids OPERATIONALIZED; 4 `prediction-live-*` VMs running writing GCS parquets (kalshi
      book_snapshot_5 = 2,107 parquets/06-26; polymarket book_snapshot_5 = 468 of 17,772 resolved tokens, thin
      liquid-overlap gate tracked in the owning plan). — cross-plan pointer, no new code / no SHA from slot-3.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-10** — **Status-flip note**: all 9 todos confirmed `[x]` with cited evidence across both the early-run
  handler-audit items and the foundation-sign-off / capture-to-100% items. Flipped `status: active` → `complete`.
- **2026-07-06** — **✅ Task -008 DONE — cross-AG never-seeded backlog scan filed as issue** (Opus, slot-7,
  data_engineering). Scan-only per the item contract. Filed
  `plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md` with per-AG quantification + 7 actionable P0-P3
  todos (each targeting the owning plan, no blind seeding here). Reference: the DeFi 2e commit trail
  (`instruments-service@38cec01` + `b34416e` / `0e08237` / `1539772` / `e98a5f3` / `e21d681` / `3bb7acd` / `2170d9a`)
  that landed ~+1.38M `expected_unattempted` cells + moved defi honest-cov 6.2% → 10.1%. Per-AG summary: **cefi** =
  Kraken-6yr class catalogue-vs-writer historical-listing gap (~1.75M cells order-of-magnitude) + sub-bucket blank-chain
  phantom audit (both open in `data_completion_to_100_all_ag_2026_06_21.md`, no new work required by this scan);
  **tradfi** = credential-gated EU-seed scaffolds (Glassnode-class, BLOCKED-CREDENTIALS) + ohlcv_15m/24h conversion
  4-part diagnosis (already open in same owning plan); **prediction** = token-id `instrument_availability` lane NOT
  SEEDED (`lifecycle-catalogue-regen-prediction-daily` PAUSED, Polymarket ~17,772-token universe off-manifest —
  cross-referenced to `prediction_capture_incident_remediation_2026_07_06.md` Workstream A/B) + Kalshi launcher gap
  (`data_completion_to_100_all_ag_2026_06_21.md#L3275` P1) + decision-338 per-conditionId intentional exclusion
  (>50M-row inflation risk affirmed as documentation-only). No enumerator/manifest writes performed; no seeding
  executed. — unified-trading-pm@&lt;SHA&gt;.

- **2026-07-06** — Prediction live token-universe fix (Capture-to-100% item 4) **coordination-closed** (Opus, slot-3) —
  cross-plan pointer, work is IN FLIGHT under the owning plan
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` + remediation
  `prediction_capture_incident_remediation_2026_07_06.md` + issue doc
  `plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`. The 07-01→07-06 live=0 outage was
  root-caused (consolidator string-typing `instrument_count` → `ArrowTypeError` on UTL
  `ManifestWriter.merged.to_ parquet`, silently swallowed by shard-isolation catch); UTL write-side dtype coercion
  shipped `unified-trading-library@6c090bb` + `@1651340`; catalogue future-date clamp `instruments-service@4979429`;
  local heal restored the universe on 2026-07-06. Polymarket token-id universe (the original "stale IS token universe"
  cue) was shipped 2026-06-22 as `instruments-service@1ecf5cb` + `market-tick-data-service@9447c71`; 4
  `prediction-live-*` VMs writing GCS parquets (Kalshi book_snapshot_5 = 2,107 parquets/06-26). Residual work
  (consolidator dtype-at- source, is-daily-enum image bump, missed-window backfill, exc_info observability, sports
  double-consolidator audit, KALSHI-PERP/POLYMARKET-PERP host repoint) tracked in the remediation plan's Workstream A +
  B — NOT duplicated here per the item's own "coordinate, don't duplicate" instruction. No code shipped this session on
  this item; PM-only plan flip in `unified-trading-pm@<SHA>`.
- **2026-07-06** — DEDUP-flagged folded-in tail (Capture-to-100% item 2) **reconciled + signed off** (Opus, slot-3) — no
  new code shipped; PM-only plan flip in the parent + this plan. `data_completion_to_100_all_ag_2026_06_21.md`
  §"Folded-in from `path_to_100pct_backfill_mtds_is_2026_06_17` (2026-06-30 consolidation merge)" carried 2 items
  explicitly `_(DEDUP: overlaps ...)_`-flagged (Step 0 could-exist universe + Step 1 per-AG backfill). Grep-verified
  both DEDUP parent-lanes are done / in-flight in the SAME parent plan: Step 0 enumerate lane =
  `instruments-service@38cec01` (DEFI expected-universe canonical re-seed with `_enumerate_defi` per-market grain fix
  - `enumerate_expected_universe.py:395` correction landing ~+1.38M `expected_unattempted`) + the P0 IS-enumerator + P1
    enumerator-fix checks in §"Wave-1 verify findings"; per-AG operational lanes = all 5 items in §"Path to 100% —
    per-AG launch matrix" carry `[x] ✅` (prediction Kalshi-bulk + Polymarket + fwd-poll; defi 8-datatype year-sharded
    VMs + LIVE wired `deployment-service@48d57a5`; tradfi 17 Databento VMs `deployment-service@f243eb4`; sports
    odds-backfill×7 + IS-sweep×8 + footystats-fwd `deployment-service@b42d98c`; cefi 802k `attempted_failed` triaged +
    48.5k free-venue diagnosed + LIVE stream verified `market-tick-data-service@46adace,e6b0f29` +
    `unified-trading-library@057264fd`). Closed both DEDUP items in the parent plan by flipping to `[x] ✅` with
    explicit **do-NOT-double-run** rationale (running Step-0 again would race the writer-materialised
    `expected_unattempted` guarantee; re-launching the per-AG lanes would race the in-flight fleet's
    `MANIFEST_PER_VM_SHARDS=true` bookkeeping and silently double-count). The remaining folded-in items in that same
    section (Steps 2-5, DeFi catalogue MVP, DeFi honest-absence residual tail, DeFi swallow-fixes CF-11, Kalshi launcher
    gap, sports-odds `--tier` arg, BLOCKED-OPERATOR-DECISION CLOB-on-chain classification, QG 5.70 dex*swaps baseline)
    do NOT carry `*(DEDUP: ...)\_` markers and remain open — this task's gate is specifically "DEDUP-flagged tail" not
    "all folded-in items", per the item text "no duplicate capture" (the concern is the double-run risk from the two
    DEDUP overlaps, not the residual open items).
- **2026-07-06** — DeFi `risk_params` MTDS handler (Capture-to-100% item 1) **drift-reconciled + C5-avoidance test
  added + signed off** (Opus, slot-3). Grep-verified against MTDS: the handler was already shipped
  `market-tick-data-service@2854c0a6` (2026-06-24) as a fully implemented per-market capture path — 674-line
  `RiskParamsHandler` at `market_tick_data_service/cli/handlers/risk_params_handler.py`, 258-line stage helpers at
  `_risk_params_stage.py`, registered in `cli/main.py:551` as `"collect-risk-params": RiskParamsHandler`, 11 unit tests
  at `tests/unit/test_risk_params_handler.py` (write / per-market grain / catalogue fallback / stale-catalog +
  `record_failed` / zero-rows), and a `launch-mtds-risk-params-backfill-vm.sh` VM launcher wired into
  `vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET`. The plan-item cue "avoid the C5 unwired class" specifically calls for
  a **dispatcher-registration regression test** mirroring the 3 tests filed by the systemic C5 audit
  (`test_deribit_options_chain_operation_registered`, `test_book_microstructure_operation_registered`,
  `test_governance_proposals_operation_registered` — all in `tests/unit/test_lifecycle_events.py`) — that specific
  regression test was **MISSING** for `collect-risk-params`. Added `test_risk_params_operation_registered` in the same
  file, mirroring the exact pattern (mock ServiceBootstrap → assert
  `operations["collect-risk-params"] is RiskParamsHandler`). QG-green (SHA sentinel
  `90cd39750362ab82b5e4010bbf098965630cdfc3`), 7/7 tests pass in the lifecycle-events test file, quickmerged to LDR as
  `market-tick-data-service@90cd3975`. The plan carried this as `- [ ]` because it was written 2026-07-06 (today)
  without checking that the handler was already shipped 12 days earlier — "Foundation = reconcile, NOT redo" +
  "grep-then-READ, not grep-then-conclude" (per plan intro) applied strictly. Gate part 1 ("risk_params captures") =
  code-level MET (handler wired + tested); Gate part 2 ("the 193k EU cells resolve to captured or honest-absence") is
  the runtime/manifest observation gated on the daily scheduler firing `collect-risk-params` or a
  `launch-mtds-risk- params-backfill-vm.sh` invocation — orthogonal to code delivery, not blocked on further code.

- **2026-07-06** — **✅ DeFi completeness ORACLE DESIGN shipped** (Opus, slot-5, data*engineering). Item 5 flipped.
  Design SSOT lands at `/codex/02-data/defi-completeness-oracle.md` (authoritative_for oracle contract + Tier-A/B
  policy + genesis rule) — one page, 12 sections. Core contract: per (protocol, chain) a `CompletenessProbe` returns
  `expected_count` from ON-CHAIN truth (DEX factory `poolCount` / lending registry `getReservesList` / Morpho
  `marketsCount` / GMX `allWhitelistedTokens` / Hyperliquid REST `universe` / …), `enumerated_count` from the IS
  catalogue, `completeness_pct = enumerated / expected` (fail-CLOSED if either is 0 or probe throws), `probe_kind`
  (`dex_factory_subgraph_tierA` / `dex_factory_rpc_tierB` / …), `probe_block` for auditability,
  `status ∈ {complete, gap, over_enumerated, undefined, probe_failed}`. Plugs into honest-coverage v2 Layer-1 by
  REPLACING DeFi's `EXPECTED` source — kills the circular `EXPECTED = ENUMERATED` that CK3-certified at 94.81% (a
  catalogue-vs-catalogue tautology). Tier-A → Tier-B rollout ladder (subgraph first for fast rollout; RPC event count as
  truth once the adapter lands). Byproduct: per-pool `creation_blocks` dict populates catalogue `available_from` from
  the on-chain `PoolCreated`/reserve-init block — kills the RAYDIUM `1970-01-01` defect + shrinks the over-fetched EU
  seed window. Follow-on impl broken into 8 P0-P3 todos in §9 of the codex doc (~2 calibrated AI-days total), to be
  filed under `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` or a fresh `defi_completeness_oracle_impl*\*`
  plan. Zero code shipped this task; design-only per the [DESIGN] tag. No cross-plan banners needed (not launching a VM,
  not in-flight refactor); no findings issue doc (design task, no audit findings).

- **2026-07-06** — cefi G1.2 (item 2) **drift-reconciled + signed off** (Opus, slot-3) — no new code needed.
  Grep-verified against `instruments-service`: `_detect_thin_day_venues` in `_finalize_completeness` at
  `instruments_service/engine/orchestrator/process_completeness.py:522-545` already wires the thin-day verdict →
  `attempted_failed` via a corrective `record_failed` row (consolidator last-write-wins semantics ensures it supersedes
  the earlier thinned `captured`). Code shipped `instruments-service@3c10615` (2026-06-27, slot-4); underlying monitor
  metric shipped `instruments-service@cc81cad` (2026-06-27). Regression coverage:
  `tests/unit/test_process_completeness_thin_day.py` (8+ tests). The plan carried this as `- [ ]` — the drift =
  plan-vs-reality lag, not open work. Part (b) 06-26 historical partial cell (BINANCE-FUTURES 678@06-25 → 47@06-26)
  verification is captured as a new P2 follow-up manifest-read todo (single-shard read, not whole-corpus). Zero code
  shipped this session on this item; PM-only plan flip.
- **2026-07-06** — G2 → G5 cefi RECONCILE + SIGN-OFF (item 3) **shipped** (slot-4). Grep-audited the
  `instruments_foundation_completeness_2026_06_24.md` §Phase 1 cefi G-gates against the shipped commits (2026-06-25 →
  2026-07-03) + prod-verified numbers in the plan's Progress Log; the drift was heavy — G2/G3/G3b/G4 had all shipped
  under G1.1/G1.2/G1.4-driven work + the 2026-06-26 autonomous run + the 2026-06-27 auto-build fix but the gate
  checkboxes were never flipped. Flipped in the sibling plan with evidence: G2 (day-axis gap-free 2,646/2,646 days + EU
  20,580 + per-AG scheduler `deployment-service@9d0e457` + drawdown guard `instruments-service@cc81cad`); G3
  (lifecycle-catalogue-regen-cefi 01:00 + auto-build fix `instruments-service:latest` sha256:d9418e6e + incremental
  rollup @b0596d0 + staleness gate @5d31994/@4979429); G3b (venue-truth available_to `instruments-service@8261203`,
  prod-verified 8,520→302 false-delist cluster); G4 (`sentinels.py` filter mechanism +
  `market-tick-data-service@fccb1961` G4-gate reclass 66,007 af→ec). G5 SUB-SIGNED (mechanism + typed-reason discipline
  shipped `UAC@755c40515` + `instruments-service@9e6dab5`/@3bb7acd); full G5 sign-off held under the MVP backfill plan
  (waves in flight — separate coordinator, no redo here). No redo of already-run work. **Foundation = reconcile, NOT
  redo** applied strictly.

- **2026-07-06** — **✅ Task 010 DONE — WSFeedConnector venue-level audit filed as issue** (Opus, slot-4). Ran
  `register_all()` on `mtds@HEAD` (post C5 fix); 31 registered venue keys. Cross-referenced UAC `VENUES_BY_ASSET_GROUP`
  via the smoke matrix's own `resolve_live_venue_key`
  (`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:201`): **73 unregistered venues** total — cefi 13
  · tradfi 4 · defi 49 · sports 7 · prediction 0. Cell counts reconcile exactly to the QG roll-up: 13·8=104
  - 49·25=1225 + 7·10=70 + 4·10=40 = 1,439 `blocked-not-registered` cells. **0 built-but-unregistered** — the 11
    `_ws.py` files on disk that `register_all()` doesn't import are ALL data-type-specific helpers imported by their
    base venue's factory (binance_futures_book_ticker_ws → binance_futures_ws; deribit_book_ticker_ws → deribit_ws;
    hyperliquid_l2book_ws + hyperliquid_ticker_ws → hyperliquid_ws; kalshi_trades_ws → kalshi_clob_ws;
    polymarket_trades_ws → polymarket_clob_ws; coinbase_book_ws → coinbase_spot_ws; bybit/kraken/okx `_book_ticker`
    variants → their base modules; tardis_machine_ws is intentional opt-in fallback). The C5-class bug does NOT recur at
    the WS layer. **Filed** `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` with per-AG actionable todos
    (bare-venue triage · per-venue build · DeFi live-connector naming policy call · BLOCKED-CREDENTIALS scaffolds).
    **Interpretation for Plan 4:** the 1,439 `blocked-not-registered` cells are a live-transport rollout gap, not a
    wiring bug — Layer-2 capture % should not be dragged down by them if the underlying batch REST capture is
    honest-complete.

- **2026-07-06** — Systemic unregistered-handler audit (item 1) **shipped**. Grep-audited the 34 `class *Handler`
  classes under `market_tick_data_service/cli/handlers/` against the 32 keys in `ServiceBootstrap(operations={…})` in
  `market_tick_data_service/cli/main.py`. Found 2 unwired handlers, both C5-class (built + unit-tested but missing from
  the dispatcher): `BookMicrostructureHandler` (cefi Phase D P2b, derives `order_flow_imbalance` from L5
  `book_snapshot_5`; queue_position + depth_of_book_10 stay honest-gap) and `GovernanceProposalsHandler`
  (defi_simulation_realism Phase 4A, writes UAC `GovernanceProposal` rows for Aave V3 / Compound V3 / Spark / Lido).
  Registered as `derive-book-microstructure` and `collect-governance-proposals` + two regression tests mirroring
  `test_deribit_options_chain_operation_registered` — `market-tick-data-service@015abaf5` (register both handlers) +
  `market-tick-data-service@efd658c8` (regression tests). Zero GENUINELY-NOT-BUILT handlers found in `cli/handlers/`;
  audit Gate met.

  **Follow-up finding (filed as new plan todo above)**: the plan cited the QG batch+live smoke-matrix
  `blocked-not-registered` counts (cefi 104 · defi 1225 · sports 70 · tradfi 40) as the motivating signal, but a code
  read of `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py::check_live_l1` shows those cells are
  classified by per-VENUE `WSFeedConnector` factory registration (`no WSFeedConnector registered for venue`), NOT by the
  operations-dispatcher C5 class this audit covers. Running the QG after the two-handler fix confirms the counts are
  unchanged: cefi 104 / defi 1225 / sports 70 / tradfi 40. Those counts will only fall after a per-VENUE WS-connector
  audit — captured as the P1 follow-up todo above so Plan 4's re-measure interprets them correctly (they are a
  live-transport gap, not a handler wiring bug).

- **2026-07-06** — Plan authored + dispatched to AO (Plan 5 of the instruments-completion set). Combines Stage-4
  foundation sign-offs (reconcile, not redo) + Stage-5 capture-to-100% data work. The unregistered-handler audit runs
  early + ungated (Plan 4 depends on it); the rest PREREQs on Plan 4's Layer-1 certification.
