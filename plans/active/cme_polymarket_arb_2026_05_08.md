---
plan_type: code+infra
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: cme-polymarket-arb-2026-05-08
overview: >-
  Cross-venue arbitrage between CME event-contracts (9 roots: ECES / ECBTC / ECRTY / ECYM / ECGC / ECCL / ECNG / EC6E /
  ECNQ) and Polymarket binary outcomes. Source RFC: archived issue
  `plans/archive/issues/cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md` (26KB design doc spanning UAC +
  instruments-service + MTDS + strategy-service + execution-service — 5 layers). Operator decision 2026-05-08: Option
  (a) split — Phase 0 (catalog backfill, the unblocking move) lives in `tradfi_master_2026_05_07` scope; Phases 1-5
  (structural fixes) live HERE. Post-May-23 critical path; the CME × Polymarket arb is the option value of the
  live-trading deadline, NOT the deadline itself. Plan is small + focused — single new sub-plan rather than
  two-plan-track per operator's "no 20 new plans" direction.

type: mixed
epic: epic-business
status: active

completion_gates:
  code: C5
  deployment: D3
  business: B3

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none

depends_on:
  - tradfi-master-2026-05-07
  - predictions-master-2026-05-07
  - writegate-honest-coverage-endtoend-2026-05-06

todos:
  - id: phase-1-instrument-type-event-contract
    content: |
      - [x] [SCRIPT] P1. **Phase 1 — `InstrumentType.EVENT_CONTRACT` enum addition** to UAC
        `unified_api_contracts/_instrument_enums.py` (canonical SSOT location — re-exported via
        `canonical/domain` and the top-level `unified_api_contracts` facade). Today the 9 CME roots are classified as
        `InstrumentType.OPTION` but they're semantically identical to Polymarket binary outcomes (resolved YES/NO
        with strike threshold). New enum member + Databento classifier mapping (Databento returns these as
        `instrument_class=BAG` per Databento docs; classifier maps BAG-with-event-contract-root to
        `InstrumentType.EVENT_CONTRACT`). **SHIPPED 2026-05-08** uac@b95d146 — InstrumentType.EVENT_CONTRACT enum
        added; `_instrument_class_to_type` extended to take `raw_symbol` and dispatch BAG (current Databento
        encoding) or O (legacy) on EC* root prefix to EVENT_CONTRACT; INSTRUMENT_TYPES_BY_VENUE[CME] gains
        EVENT_CONTRACT; INSTRUMENT_TYPE_FOLDER_MAP seeded with `event_contracts` GCS subfolder; 4 new tests in
        tests/integration/test_registry_completeness.py (BAG+EC* → EVENT_CONTRACT; vanilla OPTION/FUTURE
        preserved; BAG-without-EC* → COMBO). Originally cited `_tradfi.py` per RFC but real SSOT is
        `_instrument_enums.py` (cycle-free design).
    status: done

  - id: phase-2-canonical-question-group-cross-link
    content: |
      - [ ] [SCRIPT] P1. **Phase 2 — `linked_canonical_question_group` cross-link field on EVENT_CONTRACT instrument
        rows**. Each CME event-contract root maps to a Polymarket canonical_question_group (e.g. ECBTC EOM strike →
        `BTC_UP_DOWN_DAILY` group). NEW UAC SSOT
        `unified_api_contracts/canonical/crosscutting/cme_polymarket_link.py` declares per-CME-root the canonical
        question group. **DEPENDS ON `predictions_master_2026_05_07` Phase 5** (canonical-groups backfill must
        complete for the 6 new Polymarket groups: ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E side — see archived issue Phase 5
        list). Until Phase 5 ships, only ECES/ECBTC have valid links.
    status: blocked
    blocked_by: predictions-master-2026-05-07
    note: "Phase 5 of predictions_master ships the 6 new canonical_question_groups."

  - id: phase-3-mtds-binary-outcome-shard-atom
    content: |
      - [ ] [SCRIPT] P1. **Phase 3 — MTDS binary-outcome shard atom** for EVENT_CONTRACT data_type. Per CLAUDE.md
        "Shard-granularity SSOT" — for cefi options/futures the shard atom is `(asset_group, venue, data_type,
        chain=options_chain, root, day)`. For CME event-contracts the shard is bundled by `(asset_group=tradfi,
        venue=CME, data_type=EVENT_CONTRACT, root, resolution_date, day)` — `resolution_date` joins per-day
        snapshots that resolve at the same expiry; `strike_threshold` differs per cluster within the bundle.
        Cluster validation per Phase 1A of writegate: `expected_root_clusters = {(root, resolution_date,
        strike_threshold): expected_count}` per UAC SSOT.
    status: todo

  - id: phase-4-instruments-service-per-cluster-expiry
    content: |
      - [ ] [SCRIPT] P1. **Phase 4 — instruments-service per-cluster expiry for daily binaries.** Daily ECBTC
        EOM contracts have a different expiry (date) per (root, resolution_date, strike_threshold) tuple.
        Per-cluster expiry stored in instruments-service catalog row alongside the existing futures
        `expiry_date` (which lives in CanonicalFuturesContract per `tradfi_master` Q1 work). Reader-side helper
        `unified_trading_library.event_contracts.expiry_for_cluster(root, resolution_date,
        strike_threshold) -> datetime`.
    status: todo

  - id: phase-5-strategy-execution-cross-venue-arb-pairs
    content: |
      - [ ] [SCRIPT] P1. **Phase 5 — strategy-service cross-venue arb pairs.** New archetype
        `cme_polymarket_event_arb` under
        `strategy-service/strategies/archetypes/`. Config: `cme_root + polymarket_canonical_question_group +
        max_basis_threshold + min_liquidity_per_leg`. Strategy reads CME event-contract bid/ask + Polymarket
        market price; computes basis; sizes a paired position when basis exceeds threshold. Execution-service
        cross-venue order-routing wires the CME leg to Databento-broker connector + Polymarket leg to existing
        Polymarket execution adapter.
    status: todo

  - id: codex-update
    content: |
      - [x] [AGENT] P1. **Codex updates**: (1) extend
        `codex/02-data/per-asset-group-bucket-layouts.md` with the EVENT_CONTRACT shard atom shape; (2) extend
        `codex/09-strategy/architecture-v2/category-instrument-coverage.md` with the cross-venue-arb pattern;
        (3) NEW codex doc `codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md` capturing the strategy archetype
        spec, basis-calc reference, leg-balancing assumptions, kill-switch rules. **SHIPPED 2026-05-08** as STUB —
        per-asset-group-bucket-layouts.md gained "TradFi EVENT_CONTRACT" bullet in the multi-axis correction banner
        (shard atom + cluster validation + folder-map ref); category-instrument-coverage.md Family 4
        ARBITRAGE_PRICE_DISPERSION gained "TradFi ↔ Prediction event_contract" coverage row + slot-label cluster
        cme-polymarket-{spx|btc}-up-down-daily-usd-prod; NEW codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md
        playbook stub with TL;DR, 9-root mapping table, basis-calc reference, leg-balancing assumptions,
        kill-switch rules, anti-patterns. Full content lands as Phases 2-5 ship.
    status: done

isProject: false
estimate_class: design
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

# CME × Polymarket Cross-Venue Event-Arb Plan

## Why this plan exists (post-May-23 critical path)

The 9 CME event-contract roots (ECES / ECBTC / ECRTY / ECYM / ECGC / ECCL / ECNG / EC6E / ECNQ) are semantically
identical to Polymarket binary outcomes — both resolve YES / NO at a strike threshold on a known resolution date. Today
they sit in different asset_groups (CME = tradfi, Polymarket = prediction) with different schemas + different shard
atoms. A cross-venue basis exists (sometimes >50bps annualised on liquid roots) and is exploitable but invisible to the
workspace because no strategy can read both venues with a unified understanding.

Operator decision 2026-05-08: split scope between `tradfi_master_2026_05_07` (Phase 0 catalog backfill — the unblocking
move) and this plan (Phases 1-5 structural fixes). NOT a May-23 critical-path item; cross-venue arb is the option value
of being live, not the deadline itself.

## Architecture (cross-references the source RFC)

The 26KB source RFC is archived at
`plans/archive/issues/cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md`. Read it for the full design
intent + per-phase blast-radius analysis. This plan is the migration shell — every Phase 1-5 todo above references the
corresponding section of the archived RFC.

## Sibling plan relationships

- `tradfi_master_2026_05_07.md` — owns Phase 0 (catalog backfill); blocks Phase 1 here (need the catalog rows before the
  EVENT_CONTRACT classifier has anything to classify).
- `predictions_master_2026_05_07.md` — owns canonical_question_group backfill for the 6 new groups
  (ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E); blocks Phase 2 cross-link.
- `writegate_honest_coverage_endtoend_2026_05_06.md` — Phase 1A bundled-data-type cluster validation; Phase 3 here
  registers EVENT_CONTRACT in `BUNDLED_DATA_TYPES`.
- `tradfi_master_2026_05_07` Q1+Q2 work (`CanonicalFuturesContract.expiry_date` etc.) — Phase 4 per-cluster expiry
  builds on top of the futures schema.
- `master_to_live_defi_2026_05_23.md` — explicitly OUT of May-23 scope; this plan ships post-cutover.

## Out of scope

- Live trading the strategy: `cme_polymarket_event_arb` archetype must complete the standard onboarding checklist
  (paper-trade in staging, soak-test, operator approval) before going live. NOT a fast-path archetype.
- Other CME event-contract families beyond the 9 named roots — extend in a follow-up if liquidity grows.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness (C5 / D3 / B3); per-repo gates; Cursor checkboxes on
every todo; sibling-plan dependencies declared in `depends_on`; SSOT-first (codex docs in the codex-update todo own
intent, plan owns activation); pre-audit complete via the source RFC archived to `plans/archive/issues/`.

## DONE-2026-05-08 — Tab 5 cycle (Phase 1 + codex stub only; Phases 2-5 blocked)

Tab: `cme-polymarket-phase1-tab` (Harsh-side, Tab 5 sub-agent under `mechanical-refactor-tab` parent). Scope per task
spec: Phase 1 + codex updates only. Phases 2-5 deferred to subsequent cycles per blocker analysis (Phase 2 blocked on
`predictions-master-2026-05-07` Phase 5; Phases 3-4 blocked on `tradfi_master_2026_05_07` Q1+Q2; Phase 5 depends on
Phases 2-4).

### Code commits

- **uac@b95d146** — `feat(uac): add InstrumentType.EVENT_CONTRACT + Databento BAG classifier`
  - `unified_api_contracts/_instrument_enums.py` — `InstrumentType.EVENT_CONTRACT` enum value (cycle-free SSOT location;
    re-exported via canonical/domain + facade).
  - `unified_api_contracts/external/databento/normalize.py` — extended `_instrument_class_to_type` to accept
    `raw_symbol`; dispatches `BAG` (current Databento encoding) or `O` (legacy) on EC\* root prefix to `EVENT_CONTRACT`.
    Plain `BAG` without EC\* root → `COMBO`. Both `normalize_databento_definition` and `normalize_databento_symbol`
    updated to pass `raw_symbol`.
  - `unified_api_contracts/registry/venue_constants.py` — added `EVENT_CONTRACT` to `INSTRUMENT_TYPES_BY_VENUE[CME]`
    - `INSTRUMENT_TYPE_FOLDER_MAP["EVENT_CONTRACT"] = "event_contracts"`.
  - `tests/integration/test_registry_completeness.py` — 4 new tests:
    `test_cme_event_contract_bag_maps_to_event_contract` (BAG+EC\* → EVENT_CONTRACT, both BAG and legacy O encodings);
    `test_regular_option_still_classifies_as_option` (vanilla ES.OPT/SPX.OPT preserved);
    `test_regular_future_still_classifies_as_future` (F instrument_class unaffected by EC\* root);
    `test_bag_without_event_contract_root_maps_to_combo` (generic BAG → COMBO).

### Plan-flip + codex commits

- **pm@&lt;next sha&gt;** — `plan(cme-polymarket-arb): flip Phase 1 + codex-update checkboxes; ship codex stubs` (this
  commit — flips Phase 1 and codex-update todos, extends 2 codex docs, creates 1 NEW codex playbook stub, appends this
  DONE block).
  - `codex/02-data/per-asset-group-bucket-layouts.md` — EXTENDED multi-axis correction banner with "TradFi
    EVENT_CONTRACT" shard atom bullet (root, resolution_date, day) + cluster validation kwargs + GCS subfolder
    reference.
  - `codex/09-strategy/architecture-v2/category-instrument-coverage.md` — EXTENDED Family 4 `ARBITRAGE_PRICE_DISPERSION`
    coverage table with "TradFi ↔ Prediction event_contract" PARTIAL row covering 9 CME roots; added slot-label cluster
    `ARBITRAGE_PRICE_DISPERSION@cme-polymarket-{spx,btc}-up-down-daily-usd-prod`.
  - `codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md` — **NEW STUB** playbook with frontmatter
    `scope: [strategist, engineer]`; documents archetype name (`cme_polymarket_event_arb`), 9-root → canonical-group
    mapping table, basis-calc reference (annualised bps), leg-balancing assumptions (notional matching, expiry
    alignment, strike matching, settlement-rule equivalence), kill-switch rules (per-leg fill failure, mid-position
    resolution divergence, liquidity floor, per-trade clip), DART manual-trade gate (live-only), anti-patterns (don't
    skip canonical-question-group cross-link, don't treat ECBTC as vanilla option, don't reuse ES.OPT cluster taxonomy,
    don't trade without paper-trade soak). Full content TBD as Phases 2-5 ship.

### Findings raised during the cycle

- **Case-1 (in-scope)**: `INSTRUMENT_TYPE_FOLDER_MAP` test in `test_registry_completeness.py` failed initially on
  missing EVENT_CONTRACT key. Fixed in same commit by seeding folder name `event_contracts`. No external finding
  required.
- **Case-3 / Case-4**: zero. Phase 1 changes are additive (new enum value + new classifier branch); existing `OPTION`
  consumers unaffected because the EC\* override is gated on the EC\* root prefix.

### What is NOT in this cycle (still `- [ ]`)

- Phase 2 — `linked_canonical_question_group` cross-link + `cme_polymarket_link.py` SSOT.
- Phase 3 — MTDS binary-outcome shard atom registration + cluster validation kwargs.
- Phase 4 — instruments-service per-cluster expiry handling for daily binaries.
- Phase 5 — strategy-service `cme_polymarket_event_arb` archetype + execution-service CME ClearPort connector.
- Re-classification migration of existing on-disk manifest rows from `instrument_type=OPTION` to
  `instrument_type=EVENT_CONTRACT` for the 9 EC\* roots — deferred until Phase 3 ships (manifest migration shape same as
  `migrate_local_sfi_to_canonical.py` precedent per CLAUDE.md "Manifest migration, NOT fallback" rule).
