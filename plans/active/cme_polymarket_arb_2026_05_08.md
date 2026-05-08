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
      - [ ] [SCRIPT] P1. **Phase 1 — `InstrumentType.EVENT_CONTRACT` enum addition** to UAC
        `unified_api_contracts/canonical/domain/_tradfi.py`. Today the 9 CME roots are classified as
        `InstrumentType.OPTION` but they're semantically identical to Polymarket binary outcomes (resolved YES/NO
        with strike threshold). New enum member + Databento classifier mapping (Databento returns these as
        `instrument_class=BAG` per Databento docs; classifier maps BAG-with-event-contract-root to
        `InstrumentType.EVENT_CONTRACT`).
    status: todo

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
      - [ ] [AGENT] P1. **Codex updates**: (1) extend
        `codex/02-data/per-category-bucket-layouts.md` with the EVENT_CONTRACT shard atom shape; (2) extend
        `codex/09-strategy/architecture-v2/category-instrument-coverage.md` with the cross-venue-arb pattern;
        (3) NEW codex doc `codex/14-playbooks/strategy/cme-polymarket-arb.md` capturing the strategy archetype
        spec, basis-calc reference, leg-balancing assumptions, kill-switch rules.
    status: todo

isProject: false
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

- `tradfi_master_2026_05_07.plan.md` — owns Phase 0 (catalog backfill); blocks Phase 1 here (need the catalog rows
  before the EVENT_CONTRACT classifier has anything to classify).
- `predictions_master_2026_05_07.plan.md` — owns canonical_question_group backfill for the 6 new groups
  (ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E); blocks Phase 2 cross-link.
- `writegate_honest_coverage_endtoend_2026_05_06.plan.md` — Phase 1A bundled-data-type cluster validation; Phase 3 here
  registers EVENT_CONTRACT in `BUNDLED_DATA_TYPES`.
- `tradfi_master_2026_05_07` Q1+Q2 work (`CanonicalFuturesContract.expiry_date` etc.) — Phase 4 per-cluster expiry
  builds on top of the futures schema.
- `master_to_live_defi_2026_05_23.plan.md` — explicitly OUT of May-23 scope; this plan ships post-cutover.

## Out of scope

- Live trading the strategy: `cme_polymarket_event_arb` archetype must complete the standard onboarding checklist
  (paper-trade in staging, soak-test, operator approval) before going live. NOT a fast-path archetype.
- Other CME event-contract families beyond the 9 named roots — extend in a follow-up if liquidity grows.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness (C5 / D3 / B3); per-repo gates; Cursor checkboxes on
every todo; sibling-plan dependencies declared in `depends_on`; SSOT-first (codex docs in the codex-update todo own
intent, plan owns activation); pre-audit complete via the source RFC archived to `plans/archive/issues/`.
