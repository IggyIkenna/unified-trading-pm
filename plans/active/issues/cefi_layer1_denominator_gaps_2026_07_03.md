---
doc_type: issue
title:
  cefi Layer-1 denominator silently omits whole venues with real captured data (gate-authority gaps + one writer itype
  mis-stamp)
summary:
  'Found 2026-07-03 while implementing the UAC↔writer matrix reconciliation: the cefi Layer-1 EXPECTED matrix (44
  tuples) substantially under-counts the real could-exist universe. Two gate authorities silently zero-out whole venues:
  (1) the (venue,itype) gate reads VenueMapping.venue_instrument_type_to_tardis, which lacks the Tier-3 venues
  (BITFINEX-SPOT/BITGET-*/KRAKEN-SPOT) and all non-Tardis venues
  (HYPERLIQUID/ASTER/EXTENDED-STARKNET/PACIFICA/LIGHTER/KALSHI-PERP/POLYMARKET-PERP) — venues with REAL captured data
  get expected=0/0; (2) venues wholly absent from VENUE_DATA_TYPE_CAPABILITIES
  (BINANCE-DELIVERY/DERIBIT-COMBO/BYBIT-SPOT/COINBASE-FUTURES/KALSHI-PERP/POLYMARKET-PERP/PACIFICA/EXTENDED/LIGHTER)
  have every data_type carved out. Separately, the MTDS writer stamps BYBIT-SPOT rows instrument_type=PERPETUAL (spot
  venue). Net: cefi completeness % is measured over a fraction of the real universe — the "entire venue absent from the
  denominator" dishonesty class Honest-Coverage v2 exists to kill.'
status: open
nature: notes
asset_group: [cefi]
stage: [data, meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi]
related:
  [
    honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    ../honest_coverage_v2_instrument_denominator_2026_06_28.md,
    ../../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-03
parent_epic: infrastructure_master
priority: P1
source: honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md implementation session (Harsh)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-06
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding (data-correctness).** Surfaced 2026-07-03 while implementing
> `honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` (ground-truthing the cefi venue dialect from
> `coverage.json` `by_venue_instrument_type` + `layer_1.by_asset_group.cefi.by_venue`). NOT fixed in that pass — it
> changes the certified cefi denominator structurally and needs owner decisions on the gate authorities.

> **🤖 AO PLAN 1 of the instruments-completion set — cefi denominator completion (Stage 2 cefi).** Dispatched to the
> agent-orchestrator (`assigned_vm: planning`, role `data_engineering`). **Dispatch tier (frontmatter-driven, applies to
> EVERY task): Sonnet / high** (retiered 2026-07-07 — the C2 `_row_data_types` fix that justified Opus shipped
> `is@2170d9a3`; remaining tasks are mechanical, and the all-Opus spawn was thrashing the credit-limited accounts).
> Coordinator = `instruments_completion_tracker_2026_07_06.md` (Stage 2). The one law: **Layer-1 (denominator) gates
> Layer-2 (capture)** — this plan corrects + certifies the cefi denominator; capture (%) is meaningless until it lands.
> SSOT: `codex/02-data/honest-coverage-model.md` (do NOT derive the expected universe from the manifest — circular).
> Intra-plan ordering is by P-tag + the explicit `PREREQ:` note on each task; the critical spine is **2a
> `build_expected` → 2b gate-authority → 2c read-time MVP gate → 2f other venues → re-measure**.
>
> **Worker guards (HARD):** (1) **smoke-first on any data mutation** — one shard/slice foreground + verify the GCS +
> manifest side-effect before scaling; never fan out N×M blind. (2) **stop-on-surprise** — if a corrective touches more
> rows than expected or a measure moves the wrong direction, STOP and raise, don't push through (the 2c reclassify
> ~380k-row data-loss landmine is why). (3) **operator decisions → raise a BLOCKED-Q, do NOT guess** (see the
> `BLOCKED-OPERATOR-DECISION` item for the COINBASE / DERIBIT-COMBO MVP_SCOPE call). (4) ship via quickmerge; flip the
> checkbox + append to this plan's Progress Log in the SAME turn.

## Evidence (coverage.json 2026-07-02, layer_1.by_asset_group.cefi.by_venue)

Venues with `expected_tuples == 0` while the manifest holds REAL captured rows for them (Layer-2 strays today):

| Venue                                                                                               | expected | manifest itypes present          | why expected=0                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------- | -------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BITFINEX-SPOT / BITGET-SPOT / BITGET-FUTURES / KRAKEN-SPOT                                          | 0/0      | SPOT_PAIR / PERPETUAL + captures | absent from `VenueMapping.venue_instrument_type_to_tardis` (the checker's cefi (venue,itype) gate authority) — the Tier-3 2026-05-01 expansion never extended that map |
| HYPERLIQUID / ASTER / EXTENDED-STARKNET                                                             | 0/0      | PERPETUAL + captures             | non-Tardis venues — same gate reads only the Tardis map; `INSTRUMENT_TYPES_BY_VENUE` (which HAS them) is not consulted                                                 |
| BYBIT-SPOT / COINBASE-FUTURES                                                                       | 0/0      | rows present                     | wholly absent from `VENUE_DATA_TYPE_CAPABILITIES` → carve-out 1 removes EVERY data_type                                                                                |
| BINANCE-DELIVERY / DERIBIT-COMBO / PACIFICA-SOLANA / LIGHTER-ZKSYNC / KALSHI-PERP / POLYMARKET-PERP | (absent) | —                                | both gates blind to them (no Tardis-map keys AND no capability entries)                                                                                                |

Consequence: cefi Layer-1 "completeness" (65.91% certified 2026-06-29) is measured over a 44-tuple denominator that
omits whole venues UAC declares in `VENUES_BY_ASSET_GROUP["cefi"]` — the exact "entire venue absent from the
denominator" failure mode the v2 model exists to surface (`codex/02-data/honest-coverage-model.md` § Why v1 was not
enough). The % is neither an upper nor lower bound of the real value.

## Separate writer defect found in the same pass

- **BYBIT-SPOT rows are stamped `instrument_type=PERPETUAL`** (manifest `by_venue_instrument_type`: BYBIT-SPOT →
  {PERPETUAL} only; no SPOT_PAIR). Root cause candidate (verified 2026-07-03): MTDS
  `symbol_rules._VENUE_INSTRUMENT_TYPE` has `"BYBIT": "perpetual"` but **NO `BYBIT-SPOT` entry** (unlike
  BITFINEX-SPOT/BITGET-SPOT/KRAKEN-SPOT which map → spot) — BYBIT-SPOT rows fall through to whatever default stamped
  PERPETUAL. Add the map entry, fix the writer path, and corrective-relabel the existing rows. Until then (BYBIT,
  spot_pair, trades|book_snapshot_5) remain honest Layer-1 holes.

## Todos (Stage-2 cefi denominator — the critical spine, in order)

**Already shipped 2026-07-06 (context — DO NOT redo):**

- [x] [DESIGN] P1. **D2a — cefi (venue,itype) gate authority switched to declarative `INSTRUMENT_TYPES_BY_VENUE`** —
      `is@03cfd0f` (`_get_cefi_venue_itypes` sources `INSTRUMENT_TYPES_BY_VENUE` restricted to
      `VENUES_BY_ASSET_GROUP["cefi"]`, bundle roll-up preserved) + `uac@e76d874a` (completes the 10 missing declared
      venues; DERIBIT-COMBO → {OPTION}, Ikenna-confirmed future_combo not in MVP). Measured back-to-back: cefi Layer-1
      **84.09% → 73.61%** (+28 tuples, 0 removed — the honest direction). QG-green both repos, 41 tests pass (dynamic).
- [x] [DESIGN] P1. **D2b — `VENUE_DATA_TYPE_CAPABILITIES` completed + absent = not-expected codified** — `uac@e76d874a`
      (capability entries for PACIFICA/EXTENDED/LIGHTER/COINBASE-FUTURES; "a declared venue MUST carry a capability
      entry; absent = stray/not-expected").

**The critical spine (each task's `PREREQ:` defines the order; the review agent enforces it):**

- [x] ✅ [CODE] P0. **2a. Land the single `build_expected(asset_group)` producer** — `instruments-service@681f50a`. New
      module `scripts/expected_universe.py` exposes `build_expected(asset_group)` as THE public producer; per-AG
      strategies share one callable interface but preserve cefi/defi/tradfi/sports/prediction grains.
      `check_enumeration_completeness._build_expected_tuples` (and `..._sports`) now delegate via sibling-load (mirrors
      `measure_honest_coverage._load_completeness_module`); `measure_honest_coverage` routes transitively through the
      completeness module. Per-AG **byte-identical golden fixtures** at
      `tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json` (72/171/35/27/8 tuples) +
      `test_expected_universe_golden.py` (14 tests: single-producer contract + delegator parity + byte-identical golden
      per AG + fixture metadata coherence). D2a declarative-gate authority baked in (`INSTRUMENT_TYPES_BY_VENUE` +
      `PROTOCOL_CAPABILITIES` + `TRADFI_VENUE_INSTRUMENT_TYPES` — NOT the Tardis fetch-routing map). All 76 impacted
      tests pass; QG-green (105s); no producer surface duplication remains. COINBASE / DERIBIT-COMBO MVP_SCOPE question
      raised as `BLK-5cc7590e` (bare COINBASE + DERIBIT-COMBO declared in `VENUES_BY_ASSET_GROUP["cefi"]` but
      `get_mvp_data_types_for_cefi_venue()` returns `frozenset()` → silent EXPECTED=0; 2a preserves byte-identical
      behaviour so both remain at 0, matching pre-refactor — the fix is downstream in 2b/2c). Evidence:
      `.qg_last_passed_sha=a1038eef81f2a79fd26918baf70c121207c20ad5` (pre-quickmerge), quickmerge shipped `681f50a`.
- [x] ✅ [CODE] P0. **2b. cefi gate-authority fix on `build_expected`.** Apply D2a/D2b onto the single producer, then —
      in order — the ASTER live-forward split (enumerator `start_date` support is a HARD prereq before the UAC
      capability flip), the BYBIT-SPOT relabel, and the C2 MVP-data-type intersection (all detailed in the sections
      below). **PREREQ: 2a landed.** Gate: cefi EXPECTED reflects the full declared cefi universe (no whole-venue
      omission); dynamic tests pass (no golden edits); QG-green. **DONE 2026-07-07 — instruments-service@681f50a (2a
      byte-identical fold with D2a authority baked into `build_expected`) + `03cfd0f` (D2a landing pre-2a) + `2170d9a3`
      (C2 MVP intersection landed as -009 for `_row_data_types`).** Main-agent BLK-ec6dba83 (Option A) confirmed the 2b
      core work — Apply D2a/D2b onto the single producer — is COMPLETE via those SHAs; the remaining "in order"
      sub-parts are individually tracked backlog items with their own PREREQ chains (ASTER split → -007+-008, BYBIT-SPOT
      relabel → -006, C2 MVP → -009 shipped). Verified Gate DYNAMICALLY:
      `pytest     tests/unit/scripts/test_expected_universe_golden.py` → 14/14 pass (1.47s); `build_expected("cefi")`
      returns 72 tuples over 18 of 24 declared cefi venues; the 6 absent (BINANCE-DELIVERY / DERIBIT-COMBO / KALSHI-PERP
      / POLYMARKET-PERP / COINBASE / BYBIT-SPOT) each carry an explicit configuration reason — no silent whole-venue
      omission remains: BINANCE-DELIVERY/DERIBIT-COMBO/KALSHI-PERP/POLYMARKET-PERP have BOTH empty
      `VENUE_DATA_TYPE_CAPABILITIES` and empty `get_mvp_data_types_for_cefi_venue()`
      (COIN-M/future_combo/prediction-perp not-MVP, intentional); COINBASE has caps={book5, trades} but MVP=empty per
      BLK-5cc7590e (BLOCKED-OPERATOR-DECISION already surfaced); BYBIT-SPOT has MVP={book5, derv_ticker, funding,
      trades} but caps=empty, tracked as the writer defect in task -006 (targeted at slot-8 affinity=high). No code
      change or golden edit needed this turn — flip only.
- [x] ✅ [DATA] P0. **2c. cefi MVP read-time gate (re-scoped — the manifest-pruning script is RETIRED).** Do NOT run
      `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` — DATA-LOSS: its `_derive_base` mis-parses Bitfinex
      `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE ~380k legit **captured** BITFINEX/KRAKEN rows; also
      circular (honest-coverage-v2 forbids deriving the denominator from the manifest). Instead apply the MVP filter as
      a **read-time gate in `measure_honest_coverage`**, folded into 2a `build_expected`. **PREREQ: 2b + the ASTER split
      landed.** Gate: MVP-cut applied at read time, ZERO manifest rows mutated, cefi measure honest. **DONE 2026-07-06 —
      instruments-service@2fa3877 (slot-8 planning).** New public
      `check_enumeration_completeness.filter_manifest_to_expected(ag, df)` filters manifest to rows whose canonical
      `(venue, itype, dt)` key is in `build_expected(ag)` — MVP scope baked in via `get_mvp_data_types_for_cefi_venue`.
      `measure_honest_coverage._compute_coverage` calls the filter for cefi (`_MVP_READ_TIME_GATE_AGS = {"cefi"}`)
      BEFORE Layer-2 counting; Layer-1 keeps the UNFILTERED df so stray_tuples remain visible. ZERO manifest mutation
      (returns a filtered VIEW; input df untouched). Same canonical key as the L1 check (`_canon_key` — case-fold + UAC
      alias + bundle rollup + cefi venue-fold OKX-SPOT→OKX/etc). Smoke test demonstrated: BYBIT-SPOT/perpetual/trades
      manifest row → dropped from Layer-2, still visible in Layer-1 stray_tuples (writer PERPETUAL-stamp defect surfaced
      honestly). 11 unit tests (`tests/unit/scripts/test_filter_manifest_to_expected.py`) + 21 existing measure tests
      green (fake-checker stub updated with passthrough). QG-green 92s (sentinel 4368f381e). Filter is oracle-based on
      `build_expected`, so 2b/ASTER-split changes propagate through automatically at re-measure time (task 5 — P2, gates
      on 2a–2f + ASTER wire + KALSHI-PERP purge).
- [ ] [CODE] P1. **2f. Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA** — they share the ASTER
      live-WS/no-REST profile, so the same start-date-gated treatment applies once enumerator `start_date` support
      exists. **PREREQ: 2b + enumerator `start_date` support.** Gate: LIGHTER/EXTENDED/PACIFICA EXPECTED correct;
      tuple-diff clean.
- [ ] [SCRIPT] P2. **Re-measure + re-certify the cefi Layer-1 row** on the corrected catalogue (consolidates the two old
      re-measure todos). **PREREQ: 2a–2f landed + the ASTER live wire (Plan 5) + the KALSHI-PERP purge (Stage-3
      cross-plan prereq — 25,473 fake `KALSHI-PERP` rows pollute cefi Layer-2).** Gate: fresh cefi Layer-1 recorded in
      the Progress Log; denominator GREW, % dropped (honest). Feeds the global Stage-3 certify (Plan 4).

**Operator decision — agent RAISES via blocked-queue, operator answers later (do NOT guess):**

- [ ] [DESIGN] P1. **BLOCKED-OPERATOR-DECISION — COINBASE / DERIBIT-COMBO MVP_SCOPE membership.** Bare `COINBASE` +
      `DERIBIT-COMBO` still produce 0 EXPECTED because they are absent from `MVP_SCOPE["cefi"].venues` (which lists
      COINBASE-SPOT/FUTURES, not bare COINBASE) — gate #3 zeroes them REGARDLESS of the `INSTRUMENT_TYPES_BY_VENUE` fix.
      Decide: add bare `COINBASE` (+ a DERIBIT-COMBO membership call) to `MVP_SCOPE.venues`, or confirm intentionally
      out-of-MVP. (BINANCE-DELIVERY correctly 0 — COIN-M not-MVP per the 06-27 decision #3.) Park the dependent rows
      pending the answer. _(This line carries `BLOCKED-` so the orchestrator will not dispatch it — it stays visible for
      the operator; the working 2a/2b agent surfaces it via the blocked-queue.)_

**BYBIT-SPOT writer defect (independent of the gate work — can run in parallel with 2a):**

- [x] ✅ [CODE] P1. Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp (MTDS `symbol_rules._VENUE_INSTRUMENT_TYPE`
      has `"BYBIT": "perpetual"` but NO `BYBIT-SPOT` entry → spot rows fall through to PERPETUAL); add the map entry,
      fix the writer path, corrective-relabel existing rows. **Smoke-first** (relabel ONE shard + verify the manifest
      split, then scale). Gate: BYBIT-SPOT rows carry SPOT_PAIR; manifest `by_venue_instrument_type` shows the split.
      **CODE FIX DONE 2026-07-07 — market-tick-data-service@c4df8ae0 (slot-8 planning).** Root cause verified in TWO
      authorities: (i) `TardisAdapter._classify_row_instrument_type` at `tardis_adapter.py:321` — SPOT-venue set did not
      include `"BYBIT-SPOT"` so BYBIT-SPOT batch rows (arriving via the `bybit-spot` Tardis exchange) fell through to
      `return InstrumentType.PERPETUAL`; (ii) `symbol_rules._VENUE_INSTRUMENT_TYPE` — had bare `"BYBIT": "perpetual"`
      but no `"BYBIT-SPOT"` entry (unlike `BITFINEX-SPOT` / `BITGET-SPOT` / `KRAKEN-SPOT` which map → `spot`). Fixed
      both + regression test extended in
      `test_tardis_canonical_output.py::test_classify_row_instrument_type_option_future_perp_spot` covering BYBIT-SPOT
      (BTCUSDT / SOLUSDT) → SPOT_PAIR AND bare BYBIT (BTCUSDT) → PERPETUAL so the BYBIT-SPOT fix cannot silently regress
      BYBIT-FUTURES rows and vice versa. QG-green (sentinel `c4df8ae0`; retried three times through peer BITGET-SPOT +
      COINBASE-FUTURES connector landings). **Corrective-relabel DEFERRED — BIG FINDING, main-agent BLK-aff71ec9
      verdict**: the manifest state is materially larger than this plan's text anticipates (135,444 BYBIT-SPOT rows:
      81,659 EMPTY instrument_type + 53,785 PERPETUAL; ~54k rows under spot-nonsense data_types derivative_ticker /
      futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations — likely stray / mis-routed captures over
      months, not just the PERPETUAL stamp defect). A simple PERPETUAL→SPOT_PAIR relabel of the 53k subset would NOT
      close the Gate ("manifest by_venue_instrument_type shows the split") because 82k EMPTY-instrument_type rows + 54k
      spot-nonsense-data_type rows remain in states not modeled by this plan's relabel step. Filed follow-up issue doc
      **`plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`** with 4 tracked todos: (a) diagnose the
      82k EMPTY rows; (b) diagnose the 54k spot-nonsense-data_type rows; (c) ship the corrective-relabel script gated on
      (a)+(b); (d) populate `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC. Main-agent explicitly ruled: "-006
      forward-path fix (code) is the deliverable; mark DONE after the commit + issue doc are in; do not hold it open for
      the remediation." Operator notified via the issue doc — the stray-data_type finding may indicate re-capture (not
      just relabel) is needed for that subset.

## ASTER live-forward mode split (C1 RESOLVED — Ikenna 2026-07-03; sequencing is load-bearing)

Decision (recorded in `instruments_service_plan_reconciliation_2026_06_29.md` § C1): ASTER batch+live =
`trades`/`derivative_ticker`/`perp_funding`; **live-only-forward** = `book_snapshot_5` + `liquidations` (prediction-AG
pattern — live capture accumulates the history batch cannot provide; pre-wire history stays typed honest absence).
Capability check found the connectors already built (`aster_book_liq_ws.py`) but unwired, and ONE structural gap:
nothing date-gates seeding at the (venue, data_type) grain. Execute IN ORDER:

- [x] ✅ [CODE] P1. **Enumerator honours per-(venue,dt) `start_date`** — `_row_data_types`/the cefi date loop must read
      `get_venue_data_type_start_date(venue, dt)` and seed `expected_unattempted` only from that date (earlier days →
      typed `EXPECTED_*` absence or out-of-universe). PREREQ for the capability flip — flipping first re-creates the
      17,282-row over-seed purged 2026-07-03. **DONE 2026-07-07 — instruments-service@4a8cff7 (slot-5 planning).**
      `_enumerate_v2_cefi` pre-computes `dt_start_ts_by_dt` once per instrument (one `get_venue_data_type_start_date`
      UAC lookup per data_type — priority order: `VENUE_DATA_TYPE_CAPABILITIES` → `VENUE_REFERENCE_DATA_CAPABILITIES` →
      `VenueMapping.venue_start_dates` venue-level fallback). Alive branch consults the gate PER data_type before the
      expected_unattempted seed: dates before the declared start_date now emit `EXPECTED_PRE_SOURCE_COVERAGE_START`
      (empty_confirmed, closed-set-compliant) instead of `expected_unattempted`. Gate is scoped to manifest-aware mode
      (present_set is not None); legacy mode alive- branch continues to skip (unchanged). 4 new regression tests in
      `test_enumerate_expected_universe_v2.py` cover (i) alive < dt_start → EXPECTED_PRE_SOURCE_COVERAGE_START
      (HYPERLIQUID trades scenario, 2024-06-01 pre-2025-03-22), (ii) alive == dt_start → expected_unattempted
      (unchanged), (iii) per-data_type independence (HYPERLIQUID trades pre-2025-03-22 AND book_snapshot_5
      post-2023-04-15 on the same date → different reasons), (iv) unknown venue/dt permissive (no fallback → no gate
      applied). QG-green 93s (sentinel `7ded594`). 126/126 v2 unit tests pass + 102/102 across related enumerator suites
      (`test_enumerate_expected_universe`, `test_check_enumeration_completeness`, `test_filter_manifest_to_expected`,
      `test_expected_universe_golden`). Unblocks -008 (UAC capability flip for ASTER `book_snapshot_5` + `liquidations`
      — the 8-time bounced backlog task), -004 (2f LIGHTER/EXTENDED/PACIFICA), and -005 (re-measure).
- [ ] [CONFIG] P1. **UAC capability flip** — add `book_snapshot_5` + `liquidations` to
      `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` with `start_date` = the live-wire date; resolves the standing UAC
      self-contradiction with `EXPECTED_COVERAGE._CEFI["ASTER"]` (which already lists both).
- **[→ AO PLAN 5, INFRA role]** Register + launch the live connector `aster_book_liq_ws.py` into
  `live/connector_registry.py` + a live VM (KALSHI-PERP book5 VM is the in-cefi template); verify `live_aster` rows land
  (per-VM shard spot-check at T+10-15min). Connector SSOT: `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` BUG #4.
  _(Moved to the capture/infra plan for role-homogeneity — an INFRA VM launch is not a `data_engineering` task. This
  plan's 2c/2f re-measure PREREQs on it; tracked cross-plan.)_
- **[→ folded into the consolidated re-measure above]** Re-measure post-wire; ASTER book5/liquidations become
  expected-from-wire-date; the same model then applies to LIGHTER/EXTENDED/PACIFICA (2f) — they share the
  live-WS/no-REST profile.

## C2 point-fix (CONFIRMED — Ikenna 2026-07-03, direction (c))

The venue-blind denominator producer gets the MVP-gate intersection now; the structural single-producer fold (A17
`build_expected`) stays owned by `honest_coverage_v2_instrument_denominator_2026_06_28.md`.

- [x] ✅ [CODE] P1. **Point-fix `_row_data_types` (cefi branch): intersect with
      `get_mvp_data_types_for_cefi_venue(venue)`** so the seeded denominator matches the capture gate (kills the MVP-cut
      over-seed class, e.g. COINBASE-SPOT trades-only). Complements the 2026-07-03 capability carve-out
      (`instruments-service@3bb7acd`) — that closed the VENUE_DATA_TYPE_CAPABILITIES half; this closes the MVP half. ~5
      lines + tests. **DONE 2026-07-06 — instruments-service@2170d9a3 (slot-11 planning).** Bundle-aware MVP data_type
      gate landed in `_row_data_types` cefi branch (lines 873-899): `_mvp_capture_itype` normalises
      OPTIONS_CHAIN/COMBO→OPTION and FUTURES_CHAIN→FUTURE; when the bundle-normalised itype is NOT in
      `MVP_SCOPE["cefi"].instrument_type_data_types` (i.e. the flat/leaf case like COINBASE-SPOT trades), the
      venue-level MVP-gate intersection is applied against `get_mvp_data_types_for_cefi_venue(venue)`; when it IS in the
      override (Deribit OPTION → {options_chain}) the intersection is SKIPPED, preserving the upstream-narrowed
      `["options_chain"]` slice. A venue absent from MVP scope entirely returns an empty MVP set → the `if mvp_dts:`
      guard leaves row_dts unchanged (no blanket-block of non-MVP-scoped venues like BINANCE-DELIVERY). 4 regression
      tests added to `test_enumerate_expected_universe.py` covering COINBASE-SPOT drop-book5, Deribit
      options_chain/futures_chain survival, Deribit PERP drop-liquidations, and non-MVP-venue skip. QG-green (181s).
      Both failure modes flagged in the CAUTION avoided by the bundle-normalised `instrument_type_data_types` guard. >
      **⚠️ CAUTION (verified 2026-07-06, do not implement naively):** a literal >
      `get_mvp_data_types_for_cefi_venue(venue)` intersection breaks Deribit `options_chain` enumeration. That > helper
      is venue-only — it resolves DERIBIT to the flat cefi set (`trades`/`book_snapshot_5`/ >
      `derivative_ticker`/`funding_rate`), which does NOT contain `"options_chain"`. But `_row_data_types` for a >
      Deribit OPTION row has already been correctly narrowed upstream (via >
      `valid_data_types_for_venue_instrument_type` + `instrument_type_data_types={"OPTION": {"options_chain"}}`) > to
      `["options_chain"]` — intersecting that against the flat venue set empties it, silently wiping the > Deribit
      options_chain denominator (the exact G1 backfill `mvp_backfill_cefi_tick_v10` centers on). Confirmed > by running
      the change: no existing unit test in `test_enumerate_expected_universe*.py` currently covers > Deribit OPTION
      through `_row_data_types` directly, so this would NOT be caught by the existing suite — add a > Deribit-options
      regression test in the SAME commit as this point-fix. > A second attempt using the instrument-type-aware
      `is_mvp("cefi", venue, instrument_type, data_type)` instead > (to preserve the OPTION override) ALSO breaks:
      `is_mvp`'s cefi branch requires a `base_ccy` axis check > (`rule.base_ccys`) that `_row_data_types` has no way to
      supply from `InstrumentCatalogEntry` — calling it > with `base_ccy=None` fails that gate and wipes `row_dts` for
      every venue's every data_type, not just the > intended MVP-cut venues (confirmed via 17 failures across
      `test_enumerate_expected_universe_v2.py`, > including plain BTC/trades cases with no MVP-scope involvement at
      all). `is_mvp` also expects raw > instrument_type values (`OPTION`/`FUTURE`), not the post-bundle-rollup names
      (`options_chain`/ > `futures_chain`) `_row_data_types` sometimes receives from `enumerate_v2` — a second
      incompatibility > independent of the first. > **Net: this point-fix needs to be instrument-type/bundle-aware** —
      e.g. skip the intersection entirely when > `row_dts` was already narrowed by a non-trivial
      `instrument_type_data_types` override (Deribit OPTION, > possibly other bundle types), and only apply the
      venue-level MVP-gate intersection to the flat/leaf case > (e.g. COINBASE-SPOT). A correct implementation is closer
      to 15-20 lines + a Deribit-options regression test > than the original ~5-line estimate. Full trace of both failed
      attempts (reverted, no residue): > `unified-api-contracts@0e3989ce`+revert `8cc76fd0`,
      `instruments-service@86354d75`+revert `77314c0e` (local, > unpushed, this slot only — safe to ignore, kept for
      anyone who wants the failure detail).
- [x] ✅ [CODE] P2. **Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it** — **DEFERRED 2026-07-06 —
      v1 is NOT safe to delete.** Slot-10 investigation (`BLK-0ac84889`) confirmed three v1 roles v2 does NOT cover: (1)
      `_enumerate_v2_sports` explicitly delegates `EXPECTED_PRE_SOURCE_COVERAGE_START` dates to v1 (docstring L1552-1555
      "v2 must NOT re-emit them or the (data_type, date) cell is double-counted at two grains"); (2)
      `tests/integration/test_enumerate_v2_superset_property.py` documents "tradfi v1 (non-trading days) is NOT a v2
      grain match — v2 doesn't enumerate weekend/holiday cells" as an INTENTIONAL asymmetry; (3) v2 pre-venue-launch
      coverage is per-catalog-instrument grain vs v1 venue-grain sentinel — empty-catalog windows would lose seeding.
      Cross-repo cleanup also required in deployment-service (INFRA role). Main-agent ruling: BLOCK the full v1
      deletion; file issue doc noting the finding. **Follow-on todos filed in
      `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md`** covering v2 coverage extension (tradfi
      calendar + sports pre-coverage + venue-grain pre-launch sentinel), deployment- service infra cleanup, and the
      final v1 delete after those land. Evidence: no code change this pass; issue doc is the tracked-work artifact.

## Related fragility (observed live 2026-07-03)

- **Freshest-bucket PRIMARY selection is fragile to manifest surgery.** `measure_honest_coverage._read_manifest` picks
  the candidate with the newest `blob.updated` as PRIMARY (full frame) and reads the other as SECONDARY (**eu-only**).
  Rewriting the legacy cefi index (the ASTER corrective pass) bumped its mtime past prd → roles flipped → prd's
  captured-only tuples (e.g. BINANCE-FUTURES `future` rows consolidated 06-29) dropped from ENUMERATED and 3 artifact
  "holes" appeared. Mitigated in-session by a metadata bump restoring prd as freshest, but any future surgery on the
  older bucket re-triggers it. Consider content-based freshness (max manifest date) or pinning prd as primary. This may
  also explain the anomalous 05:07 UTC 2026-07-03 cefi-only measure (61.36%, present 29→27).
- [x] ✅ [CODE] P2. Harden `_read_manifest` primary selection against surgery-bumped mtimes (content-based freshness or
      pinned-primary with explicit override). **DONE 2026-07-06 — instruments-service@5b04878 (slot-5 planning).**
      `measure_honest_coverage._read_manifest` now pins PRIMARY to the first accessible candidate in
      `_MANIFEST_BUCKET_CANDIDATES[asset_group]` tuple order (which places the `-prd` bucket first by construction for
      every AG). `blob.updated` mtime is still logged for visibility but no longer drives selection — the 2026-07-03
      ASTER-corrective-pass scenario (surgery on legacy bucket bumped its mtime past prd, flipping roles and producing 3
      artifact "holes") is now a regression-tested guard. New `--primary-bucket=<name>` operator override forces a
      specific candidate when surgery or debugging demands it (falls back to the tuple-order pin with a warning if the
      named bucket is not accessible). New `_warn_if_secondary_newer` logs a `SURGERY-SIGNAL` warning when a secondary
      bucket has a newer mtime than primary, so operators can spot the anomaly and decide whether to switch primary via
      the override. 4 new/rewritten unit tests: `test_prd_wins_over_legacy_by_tuple_order`,
      `test_pinned_primary_wins_when_secondary_mtime_is_newer` (regression guard cite the 06-29 BINANCE-FUTURES/future
      scenario), `test_row_count_no_longer_a_tiebreaker`, `test_override_wins_over_tuple_pin_when_accessible`,
      `test_override_falls_back_to_pin_when_not_accessible`. All 24 module tests pass; QG-green (94s, sentinel
      `9263c803`).

## Progress Log

- **2026-07-03** — Filed from the reconciliation implementation session. Context: the venue-suffix fold + ASTER
  carve-out shipped in `instruments-service` (see the reconciliation issue doc); this finding is the structural
  remainder. Also noted: `INSTRUMENT_TYPES_BY_VENUE` exists in UAC and already covers most of the gate-blind venues —
  strongest candidate for the (venue,itype) authority.
- **2026-07-06** — **2a landed** (`instruments-service@681f50a`, slot-8 planning). Single-producer consolidation:
  `scripts/expected_universe.py::build_expected(asset_group)` is now THE Layer-1 EXPECTED producer;
  `check_enumeration_completeness._build_expected_tuples` delegates via sibling-load; `measure_honest_coverage` routes
  transitively. Byte-identical output preserved for all 5 AGs (cefi 72 / defi 171 / tradfi 35 / sports 27 /
  prediction 8) — captured as goldens under `tests/unit/scripts/goldens/expected_universe/`. New regression
  `test_expected_universe_golden.py` (14 tests: contract
  - delegator parity + golden byte-identical). Full suite green: 76 impacted tests + QG (105s). MVP_SCOPE
    COINBASE/DERIBIT-COMBO question surfaced as `BLK-5cc7590e` (verified empirically: both declared in
    `VENUES_BY_ASSET_GROUP["cefi"]` but `get_mvp_data_types_for_cefi_venue()` returns `frozenset()`); per plan warning,
    raised for operator decision rather than guessed — 2a itself is byte-identical so the silent zero persists exactly
    as before, and 2b/2c will act on the answer. 2a UNBLOCKS 2b (cefi gate-authority fix on `build_expected`).
- **2026-07-06** — **2f dispatch blocked on missing PREREQs** (slot-8 planning, `BLK-02a4b067`). Task 2f
  (`cefi_layer1_denominator_gaps-004`, "Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA") was
  dispatched by priority=20 alone — but the plan-declared PREREQ chain (`2b + enumerator start_date support`) is not
  machine-encoded on the backlog task, so the dispatcher missed it. Verified in code:
  `instruments-service/scripts/expected_universe.py` has zero `start_date` awareness; the only consumer of
  `get_venue_data_type_start_date` today is `market-tick-data-service/…/orchestrator/sentinels.py` +
  `instruments-service/scripts/cefi_per_venue_capture_summary.py` — the enumerator itself does not read it. Additionally
  verified LIGHTER's REST `_fetch_lighter_book_for_symbol` stamps `datetime.now(UTC)` as timestamp (not the requested
  date) — confirming the ASTER live-WS/no-REST profile for `book_snapshot_5`; a UAC capability flip that adds start_date
  before the enumerator honours it would re-create the 17,282-row over-seed the plan warns against. Main-agent verdict:
  skip -004, add `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-007]` to task -004 in
  `backlog.yaml` and regen so the dispatcher gates it correctly. 2f resumes when `-002` (2b) + `-007` (enumerator
  start_date) both land.
- **2026-07-06** — **UAC capability flip PARKED — BLOCKED-PREREQUISITES** (slot-8 planning, `BLK-36eeb447`). Task
  `cefi_layer1_denominator_gaps-008` (UAC capability flip — add ASTER `book_snapshot_5` + `liquidations` to
  `VENUE_DATA_TYPE_CAPABILITIES` with `start_date` = live-wire date, target
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144`) was dispatched by priority=20
  alone — SAME machine-encoded `depends_on` gap as -004. Verified LDR tip:
  `instruments-service/scripts/expected_universe.py`
  - `check_enumeration_completeness.py` still have zero `start_date` references; task -007 (enumerator `start_date`
    support) is `status=dispatched` to a peer slot but has NOT reached LDR (no commit to either file since 2a). Plan is
    explicit: "**PREREQ for the capability flip — flipping first re-creates the 17,282-row over-seed purged
    2026-07-03.**" Main-agent verdict (`BLK-36eeb447` answered): PARK -008; do NOT touch UAC
    `VENUE_DATA_TYPE_CAPABILITIES` until -007 confirmed shipped to LDR; the machine-encoded `depends_on` fix is an
    operator backlog.yaml action. -008 resumes when `-007` (enumerator `start_date`) lands. Slot-8 rotated to
    `cefi_layer1_denominator_gaps-009` (C2 point-fix).
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (2nd dispatch)** (slot-7 planning,
  `BLK-d8cba69b`). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-7 by priority=20 alone (the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` is still uncorrected on the backlog task —
  `depends_on: None` verified via `/api/backlog?limit=500`). Re-verified LDR tip at re-dispatch time:
  `instruments-service/scripts/expected_universe.py` + `check_enumeration_completeness.py` still have zero `start_date`
  references (last touching commits: `a1038ee` 2a, `2fa3877` 2c — neither adds start_date). Task -007 is
  `status=dispatched` to slot-11; tmux pane capture confirms slot-11 mid-work adding a per-`(venue, dt) start_date`
  regression test to `test_enumerate_expected_universe_v2.py`, but NOT yet shipped to LDR. Main-agent verdict
  (`BLK-d8cba69b` answered): PARK -008 — same ruling as `BLK-36eeb447`; the 17,282-row over-seed risk is real and
  documented; -008 will be re-dispatched after -007 lands. Slot-7 handed `understat_local_backfill_completion-004`
  (unrelated manifest normalisation) as next task.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (4th dispatch, `BLK-9072b84f`)** (slot-5
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-5 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` is still uncorrected on the backlog task.
  Re-verified LDR tip at re-dispatch: `instruments-service/scripts/expected_universe.py` +
  `check_enumeration_completeness.py` still have zero `start_date` / `get_venue_data_type_start_date` references (grep
  returns empty). Task `-007` remains `status=queued` (has NOT reached LDR — dispatched to a peer slot per prior entries
  but the work not committed). Main-agent verdict (`BLK-9072b84f` answered): PARK -008 — **4th ruling, same answer**.
  The 17,282-row over-seed risk stands; do NOT flip UAC `VENUE_DATA_TYPE_CAPABILITIES`. **Operator action required**:
  add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen to stop the
  bounce loop (4 dispatches, 4 blocks). Slot-5 goes idle pending operator's backlog fix; -008 resumes only when `-007`
  (enumerator `start_date`) reaches LDR.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (5th dispatch, `BLK-545a3adb`)** (slot-2
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-2 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` is STILL uncorrected on
  the backlog task (verified via `/api/backlog?limit=500`: `-008.depends_on = null`). Re-verified LDR tip at 5th
  re-dispatch: `instruments-service/scripts/expected_universe.py` last touched by `2fa3877` (2c) + `a1038ee` (2a) —
  neither commit adds `start_date` awareness; `check_enumeration_completeness.py` likewise contains zero `start_date` /
  `get_venue_data_type_start_date` refs. Task `-007` remains `status=queued` on the backlog (unchanged since 4th
  dispatch — no worker has landed it). Slot-2 verdict: PARK -008 — **5th consecutive block, same 17,282-row over-seed
  risk**. The bounce loop is now definitively an operator-backlog defect: 5 slots have been spent (8, 7, unnamed 3rd,
  5, 2) verifying + escalating the same fact. **Operator action required (5th escalation)**: add
  `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; -008 stays in
  queue until `-007` (enumerator `start_date`) reaches LDR. Slot-2 goes idle pending operator's backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (6th dispatch)** (slot-9 planning). Task
  `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 by priority=20 alone; `depends_on` gap flagged in
  `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` + `BLK-545a3adb` remains uncorrected on the backlog task (verified
  via `/api/backlog?limit=500`: `-008.status=dispatched`, `-008.depends_on = null`; `-007.status=queued`,
  `-007.depends_on = null`). Re-verified LDR tip at 6th re-dispatch: `instruments-service/scripts/expected_universe.py`
  contains ZERO `start_date` / `get_venue_data_type_start_date` refs (grep empty; last touching commit `a1038ee` 2a);
  `check_enumeration_completeness.py` likewise contains ZERO such refs (last touching commits `2fa3877` 2c + `a1038ee`
  2a). Task `-007` (enumerator `start_date` support) remains `status=queued` on the backlog with no worker having landed
  the work. Slot-9 verdict: PARK -008 — **6th consecutive block, same 17,282-row over-seed risk**. The bounce loop
  persists: 6 slots have now been spent verifying + escalating the same operator-backlog defect
  (`depends_on: [cefi_layer1_denominator_gaps-007]` still not encoded on `-008`). **Operator action required (6th
  escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen;
  -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9 goes idle pending operator's backlog
  fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (7th dispatch)** (slot-9 planning, new
  session). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 AGAIN after the prior slot-9 session's
  6th-block park commit `7ad9a3c6b` (18:09 UTC) landed on LDR; task status returned to queued/dispatched.
  Machine-encoded `depends_on` gap flagged across 6 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` +
  `BLK-545a3adb` + 6th-block) remains uncorrected: `/api/backlog?limit=500` at 7th re-dispatch:
  `-008.status=dispatched, depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip:
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain ZERO
  `start_date` / `get_venue_data_type_start_date` refs (last touching commits `a1038ee` 2a + `2fa3877` 2c — neither adds
  start_date). Confirmed ASTER capability entry alive at
  `unified-api-contracts/registry/ market_data_categories.py:1144` (target of the flip). Slot-9 verdict: PARK -008 —
  **7th consecutive block, same 17,282-row over-seed risk**. The bounce loop is not self-correcting: 7 slots (8, 7,
  unnamed 3rd, 5, 2, 9, 9-again) have now been spent verifying + escalating the identical operator-backlog defect.
  **Operator action required (7th escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in
  `data/config/backlog.yaml` and regen; -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9
  goes idle pending operator's backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (8th dispatch, `BLK-e642f2aa`)** (slot-4
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-4 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged across 7 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` +
  `BLK-545a3adb` + 6th + 7th) is STILL uncorrected. Re-verified at 8th re-dispatch via `/api/backlog?limit=500`:
  `-008.status=dispatched, depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip with
  `rg -c 'start_date|get_venue_data_type_start_date'` on both files: ZERO matches on
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` (last touching
  commits unchanged: `a1038ee` 2a + `2fa3877` 2c). Confirmed ASTER capability entry alive at
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144` (flip target). Slot-4 verdict:
  PARK -008 — **8th consecutive block, same 17,282-row over-seed risk**. The bounce loop remains not self-correcting: 8
  slots (8, 7, unnamed 3rd, 5, 2, 9, 9-again, 4) have now been spent verifying + escalating the identical
  operator-backlog defect — this is now a systemic-cost finding (each dispatch consumes ~10 min of a worker's context
  budget + a Claude-Code cycle). **Operator action required (8th escalation)**: add
  `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; alternatively flip
  `-008`'s backlog priority to 999 so higher-priority queued tasks dispatch instead. -008 stays in queue until `-007`
  (enumerator `start_date`) reaches LDR. Slot-4 goes idle pending operator's backlog fix.
- **2026-07-06** — **C2 point-fix (-009) flipped ✅** (slot-9 planning). Main released -008 via /skip-current-task
  answering `BLK-be92ef1e` Option A; -009 dispatched to slot-9 next. Verified code already landed on LDR by slot-11:
  `instruments-service@2170d9a3` (18:23:15 UTC, "feat(scripts): bundle-aware MVP data_type gate in \_row_data_types cefi
  branch — closes cefi_layer1_denominator_gaps C2 point-fix (item 009)") — 31 lines in
  `scripts/enumerate_expected_universe.py` (the MVP data_type gate at lines 873-899) + 117 lines of regression tests (4
  tests) in `tests/unit/scripts/test_enumerate_expected_universe.py`; QG-green 181s per commit message. The correct
  instrument-type/bundle-aware approach the CAUTION prescribed is implemented via `_mvp_capture_itype` normalisation +
  `cefi_rule.instrument_type_data_types` membership check. Deribit `options_chain` slice preserved via the
  OPTION-override skip; COINBASE-SPOT `book_snapshot_5` dropped; Deribit PERP `liquidations` dropped; non-MVP-scoped
  venues (e.g. BINANCE-DELIVERY) unaffected by the empty-mvp_dts guard. Slot-9 action: checkbox-flip only (no code
  change) — /done cites `2170d9a3` as the shipped SHA.
- **2026-07-06** — **Re-measure task (-005) PARKED — BLOCKED-PREREQUISITES (`BLK-ad7abfcd`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-005` ("Re-measure + re-certify the cefi Layer-1 row") was dispatched to slot-8 by
  priority=50 alone; the machine-encoded `depends_on` gap flagged across 8 prior `-008` blocks now also affects `-005`
  (verified via `/api/backlog?limit=500`: `-005.status=dispatched, depends_on=null`). Verified plan-declared PREREQ
  chain ("2a–2f landed + ASTER live wire (Plan 5) + KALSHI-PERP purge (Stage-3)") is NOT met: (i) `-002` (2b cefi
  gate-authority fix on `build_expected`) status=queued — D2a `INSTRUMENT_TYPES_BY_VENUE` authority IS baked into
  `scripts/expected_universe.py` (part of 2a's consolidation) but the 2b sub-parts (ASTER live-forward split +
  BYBIT-SPOT relabel) remain unshipped; (ii) `-004` (2f LIGHTER/EXTENDED/PACIFICA denominator-gap) status=queued —
  depends on enumerator `start_date`; (iii) `-007` (enumerator `start_date` support) status=queued — verified LDR tip:
  `instruments-service/scripts/expected_universe.py` has ZERO `start_date` / `get_venue_data_type_start_date` refs (grep
  empty; last touching commits `a1038ee` 2a + `2fa3877` 2c — neither adds start_date); (iv) ASTER live wire (Plan 5,
  INFRA role) — connector `market_tick_data_service/live/connectors/aster_book_liq_ws.py` EXISTS but is NOT registered
  in `market_tick_data_service/live/connector_registry.py` (grep empty on `aster_book_liq_ws|AsterBookLiq`); (v)
  KALSHI-PERP purge (Stage-3) — commit `c8c6dac` only guards the KALSHI-PERP/POLYMARKET-PERP adapters to emit 0 (a
  forward stop-gap); the 25,473 fake `KALSHI-PERP` cefi Layer-2 rows still pollute the manifest and would over-inflate
  the numerator. Running the re-measure now would produce a misleading % moving in the WRONG direction from the plan
  Gate ("denominator GREW, % dropped honest") — the denominator would still UNDER-count (2f venues at 0-expected while
  their manifest rows exist) while the numerator OVER-counts (fake KALSHI-PERP rows). Slot-8 verdict: PARK -005 —
  recommendation A of `BLK-ad7abfcd`. **Operator action required**: add
  `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-004, cefi_layer1_denominator_gaps-007]`
  to `-005` in `data/config/backlog.yaml` + regen (or flip `-005` priority to 999) to prevent the same bounce-loop the
  `-008` block-chain hit 8×. -005 stays in queue until 2b/2f/-007/ASTER-wire/KALSHI-PERP-purge all reach LDR. Slot-8
  goes idle pending operator answer + backlog fix.
- **2026-07-06** — **v1 deletion task (-010) PARKED — BLOCKED-OPERATOR-DECISION (`BLK-6cf82522`)** (slot-4 planning).
  Task `cefi_layer1_denominator_gaps-010` ("Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it") was
  dispatched to slot-4 by priority=50. **Confirmation FAILED**: v1 is NOT purely legacy — it still owns 3 seed
  categories that v2 explicitly defers to it, so a blind delete is a data-correctness regression (violates the
  data-pipeline-correctness HARD rule). Verified on LDR tip
  (`instruments-service/scripts/enumerate_expected_universe.py`): (i) **sports v2** (`_enumerate_v2_sports`, line
  1552-1554): docstring explicitly says _"date < the data_type's source coverage start → SKIP — those dates are owned by
  the v1 `_enumerate_sports` pre-coverage rows (`EXPECTED_PRE_SOURCE_COVERAGE_START`, league_id="" grain). v2 must NOT
  re-emit them or the (data_type, date) cell is double-counted at two grains."_ — deleting v1 loses
  `EXPECTED_PRE_SOURCE_COVERAGE_START` seeds entirely. (ii) **tradfi v2** (`_enumerate_v2_tradfi`, line 1377-1379):
  docstring says _"Weekend and holiday dates fall through to the pipeline (v1 handles them at venue-grain; v2 only adds
  per-instrument rows for the non-trading-day windows outside the instrument lifecycle)."_ — MTDS orchestrator
  `process_ticks` DOES emit `EXPECTED_WEEKEND/HOLIDAY` during actual capture (verified
  `market-tick-data-service/tests/unit/test_orchestrator_non_trading_session.py`), but ONLY for dates the pipeline
  attempts; v1 `_enumerate_tradfi` pre-seeds them for the full calendar window (backfill role). Also v1
  `_enumerate_tradfi_indices` seeds Yahoo-index pre-genesis dates (VIX 1990-01-02 / DXY 2019-01-02 / treasuries
  2000-01-03) at instrument grain — v2 tradfi may cover this via catalogue but not verified. (iii) **defi v1** has
  `_enumerate_defi_gas_fees` (line 484-513) that seeds chain-level `EXPECTED_PRE_GENESIS_CHAIN` cells at `venue=ALCHEMY`
  for `gas_fees` data_type. v2 defi does per-instrument lifecycle but does not cover this chain-level slice
  (`venue=ALCHEMY` is not in the per-instrument catalogue). Cefi + prediction ARE fully covered by v2 (verified by
  `tests/integration/test_enumerate_v2_superset_property.py` which asserts v2 ⊇ v1 for cefi/defi/prediction pre-launch
  cells; docstring at line 43+47 calls v2 "the live path" for cefi + prediction only, NOT
  tradfi/sports/defi-chain-level). Production context: `expected_universe_v2_scheduler.tf` runs v2 only, on ALL 5 AGs
  daily @ 01:30 UTC (v2 wired 2026-06-19). v1 launcher (`launch-expected-universe-enumerator-vm.sh`) exists but is
  MANUAL, not scheduled — so the sports pre-cov / defi gas_fees pre-genesis / tradfi Yahoo-index cells are already NOT
  being freshly seeded via any scheduled path; they exist in the manifest only from historic v1 manual runs. Slot-4
  verdict: PARK -010 — recommendation A of `BLK-6cf82522`: DEFER pending a preceding task that either (i) extends v2 to
  cover the 3 asymmetric slices, or (ii) folds them into `build_expected` / `scripts/expected_universe.py`; then delete
  v1 cleanly. **Operator action required**: file a new task (or resize this one) to enhance v2 sports (emit
  `EXPECTED_PRE_SOURCE_COVERAGE_START` while preserving the two-grain double-count guard), v2 tradfi (emit
  weekend/holiday pre-seeds venue-grain + Yahoo-index pre-genesis instrument-grain), and v2 defi (emit chain-level
  `gas_fees` `EXPECTED_PRE_GENESIS_CHAIN` at `venue=ALCHEMY`) BEFORE -010's delete lands; alternatively answer with
  Option C/D from `BLK-6cf82522` if the operator accepts the correctness trade-off or wants both in one commit. Slot-4
  goes idle pending operator answer.
- **2026-07-06** — **\_read_manifest hardening (-011) SHIPPED ✅** (slot-5 planning). Task
  `cefi_layer1_denominator_gaps-011` ("Harden `_read_manifest` primary selection against surgery-bumped mtimes") shipped
  via `instruments-service@5b04878`. Chose the pinned-primary approach (tuple-order first-accessible = `-prd` by
  construction) over content-based freshness (max manifest date): simpler, deterministic, and matches the plan's own
  wording ("pinning prd as primary"). mtime-based `_sort_key` removed from `_read_manifest`; replaced with
  `_select_primary_index(accessible, override, asset_group)`. New CLI flag `--primary-bucket=<name>` overrides the pin
  for surgery/debugging (falls back to pin + warning if the named bucket isn't accessible). New
  `_warn_if_secondary_newer` helper logs `SURGERY-SIGNAL` when a secondary's mtime > primary's — surfaces the
  ASTER-corrective-pass scenario without silently flipping roles. Regression test
  `test_pinned_primary_wins_when_secondary_mtime_is_newer` locks the fix: legacy bucket with newer mtime + prd with
  older mtime → prd still primary. Full test suite 24/24 green; QG-green 94s (sentinel `9263c803`). Docstring + usage
  examples updated; no other callers of `_read_manifest` in the codebase (grep confirmed).
- **2026-07-06** — **Task -010 STALE RE-DISPATCH — no-op /done** (slot-9 planning). Task
  `cefi_layer1_denominator_gaps-010` ("Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it") was
  re-dispatched to slot-9 by priority=50 alone. Plan line 248 already carries the `[x] ✅ DEFERRED` flip from slot-10
  (commit `a16ac0649` — "docs(plans): defer v1 enumerator delete + file follow-on issue doc", verified on LDR via
  `git merge-base --is-ancestor a16ac0649 origin/live-defi-rollout` = YES). Follow-on issue doc exists at
  `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md` (5 follow-on todos: v2
  tradfi/sports/pre-launch coverage extension, deployment-service infra cleanup, and the final v1 delete after those
  land). No code change was needed by original design (v1 NOT safe to delete per main-agent ruling on `BLK-0ac84889`)
  and none is needed on this re-dispatch — the plan artifact + issue doc are the tracked-work outputs. Slot-9
  verification result: task -010 is fully complete on LDR; the backlog task remained `status=dispatched` because the
  PlanRegenLoop had not yet re-parsed the flipped checkbox at the time of this /boot. Slot-9 /done cites `a16ac0649` as
  the shipped SHA (existing artifact). Cross-reference: slot-4's BLK-6cf82522 entry above independently re-verified the
  same three v2-does-not-cover slices documented in `v1_enumerator_dispatch_not_deletable_2026_07_06.md`.
- **2026-07-07** — **2b flipped ✅ — checkpoint-only, no code change** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-002` ("2b. cefi gate-authority fix on `build_expected`") was dispatched to slot-8 as the
  highest-tier queued task (tier=1, priority=10, `depends_on=null`). Ambiguity in the task text — "Apply D2a/D2b onto
  the single producer, then — in order — the ASTER live-forward split ... the BYBIT-SPOT relabel, and the C2
  MVP-data-type intersection" — could be read as (i) 2b consists of a D2a/D2b checkpoint plus separately-tracked
  followers, or (ii) 2b bundles all four items. Slot-8 filed `BLK-ec6dba83` asking main-agent to disambiguate. Main
  answered Option A: "CLOSE cefi_layer1_denominator_gaps-002 as DONE. D2a+D2b are confirmed applied via 2a
  byte-identical fold + commit 03cfd0f — the core gate-authority fix on build_expected is complete. The remaining
  sub-parts are correctly tracked in their own dedicated backlog entries: ASTER live-forward split in -007 (has its own
  HARD prereq gate), BYBIT-SPOT relabel in -006 (MTDS writer defect tracked separately), C2 MVP intersection in -009
  (already shipped). Do NOT hold -002 open waiting for those — they are individually gated and dispatched." Verified on
  LDR at flip time: (i) `scripts/expected_universe.py::_get_cefi_venue_itypes` sources `INSTRUMENT_TYPES_BY_VENUE`
  restricted to `VENUES_BY_ASSET_GROUP["cefi"]` with `FUTURE_BUNDLE_VENUES` bundle roll-up — the D2a declarative
  authority (last touched: `681f50a` 2a byte-identical fold, preceded by `03cfd0f` D2a landing). (ii)
  `_expected_generic` applies `VENUE_DATA_TYPE_CAPABILITIES` as Carve-out 1 for
  `VENUE_CAPABILITY_AGS = {"cefi", "tradfi"}` — the D2b intersection. (iii) Venue-level cefi MVP override via
  `get_mvp_data_types_for_cefi_venue(venue)` applied as Carve-out 2 (the `build_expected` analogue of the -009 C2 fix on
  `_row_data_types`). Dynamic Gate verification:
  `.venv/bin/python -m pytest tests/unit/scripts/test_expected_universe_golden.py -x -q` → 14/14 pass in 1.47s.
  `build_expected("cefi")` returns 72 tuples over 18 of 24 declared cefi venues (ASTER, BINANCE-FUTURES/SPOT,
  BITFINEX-FUTURES/SPOT, BITGET-FUTURES/SPOT, BYBIT, COINBASE-FUTURES, DERIBIT, EXTENDED-STARKNET, HYPERLIQUID,
  KRAKEN-FUTURES/SPOT, LIGHTER-ZKSYNC, OKX, PACIFICA-SOLANA, UPBIT); the 6 absent venues each carry an explicit
  configuration reason — BINANCE-DELIVERY / DERIBIT-COMBO / KALSHI-PERP / POLYMARKET-PERP have BOTH
  `VENUE_DATA_TYPE_CAPABILITIES[v]={}` AND `get_mvp_data_types_for_cefi_venue(v)==frozenset()` (COIN-M / future_combo /
  prediction-perp not-MVP per operator decisions 06-27 #3 + Ikenna 07-03); bare COINBASE has caps={book5, trades} but
  MVP=empty (BLK-5cc7590e BLOCKED-OPERATOR-DECISION already surfaced by 2a); BYBIT-SPOT has MVP populated but caps=empty
  (writer-defect tracked as -006, `target_slot=8 affinity=high`). No silent whole-venue omission remains — every absence
  is explicit, satisfying the plan Gate. Slot-8 action: checkbox-flip only (no `build_expected` code change; no golden
  edit; no instruments-service commit). /done cites `681f50a` as the shipped SHA for the 2b `build_expected` change. 2b
  flip UNBLOCKS the "2b landed" leg of PREREQ chains for -005 (re-measure — still blocked on -004+-007+ASTER wire
  - KALSHI-PERP purge) and -004 (2f — still blocked on -007).
- **2026-07-07** — **Task -004 (2f) RE-PARKED — BLOCKED-PREREQUISITES (`BLK-7b511dcb`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-004` ("2f. Reapply the denominator-gap model to LIGHTER / EXTENDED / PACIFICA") was
  RE-dispatched to slot-8 by priority=20 immediately after the 2b flip cited above; the machine-encoded `depends_on` gap
  flagged in the 2026-07-06 slot-8 park entry (add
  `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-007]` to `-004` in `backlog.yaml`) is
  still uncorrected (verified via `/api/backlog?limit=500`: `-004.status=dispatched, depends_on=null`). Re-verified LDR
  tip at RE-dispatch: (i) `scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain
  ZERO per-`(venue, dt)` `start_date` / `get_venue_data_type_start_date` refs (the CLI-level global `start_date` at
  `enumerate_expected_universe.py:2991` is the only `start_date` string in the enumerator scripts — that's the batch
  window, not the per-(venue,dt) gate the plan requires). The only in-tree consumer of `get_venue_data_type_start_date`
  on LDR remains `scripts/cefi_per_venue_capture_summary.py`. (ii) UAC `VENUE_DATA_TYPE_CAPABILITIES["ASTER"]` still
  holds `{trades: 2023-07-22, derivative_ticker: 2023-07-22, perp_funding: 2023-07-22}` — NO `book_snapshot_5`, NO
  `liquidations`. (iii) Task `-007` (enumerator `start_date` support) remains `status=dispatched to slot-5` on the
  backlog — main-agent confirmed "slot5 has impl complete (126/126 tests green) but has NOT shipped via quickmerge".
  Main-agent verdict (`BLK-7b511dcb` answered): "PARK — BLOCKED-PREREQUISITES. Same ruling as 2026-07-06. ... Take PARK
  - /skip-current-task. Do NOT attempt workarounds." Operator actions main-agent surfaced: (a) ensure slot-5 ships
    cefi-007 via quickmerge (impl done, tests green); (b) update UAC `ASTER` capabilities to include `book_snapshot_5` +
    `liquidations`. Once both land on LDR, cefi-004 can re-dispatch. Slot-8 action: file this Progress Log entry, commit
    via `docs(plans):` cross-repo PM flip, then call `/api/slots/8/skip-current-task` per main-agent instruction
    (avoiding the same bounce-loop the `-008` chain hit 8×).

- **2026-07-07** — **Task -006 (BYBIT-SPOT itype-stamp) CODE FIX SHIPPED ✅** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-006` ("Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp") was dispatched after the
  -004 park + /skip. Diagnosis on LDR: the PERPETUAL stamp on BYBIT-SPOT batch rows comes from **two** authorities that
  both silently omitted BYBIT-SPOT — (i) `TardisAdapter._classify_row_instrument_type` at `tardis_adapter.py:321`
  SPOT-venue set had `BINANCE-SPOT / OKX-SPOT / COINBASE-SPOT / UPBIT / BITFINEX-SPOT / BITGET-SPOT / KRAKEN-SPOT` but
  NOT `BYBIT-SPOT` → the venue's rows fell through to `return InstrumentType.PERPETUAL`; (ii)
  `symbol_rules._VENUE_INSTRUMENT_TYPE` had bare `"BYBIT": "perpetual"` with no `"BYBIT-SPOT"` entry (unlike the Tier-3
  sisters `BITFINEX-SPOT / BITGET-SPOT / KRAKEN-SPOT` which explicitly map → `spot`). Fixed both authorities +
  regression-tested via `test_tardis_canonical_output.py::test_classify_row_instrument_type_option_future_perp_spot`
  which now covers BYBIT-SPOT (BTCUSDT + SOLUSDT) → SPOT_PAIR AND bare BYBIT (BTCUSDT) → PERPETUAL to prevent the
  BYBIT-SPOT fix silently regressing BYBIT-FUTURES (bare BYBIT is the canonical MTDS venue for BYBIT perp/futures via
  Tardis `bybit` exchange). Shipped via `market-tick-data-service@c4df8ae0` after three QG cycles (peers landed
  BITGET-SPOT + COINBASE-FUTURES connectors between my QG runs; each landed via clean rebase; sentinel finally matched
  HEAD at `c4df8ae0`). **BIG FINDING surfaced during manifest audit — main-agent BLK-aff71ec9 verdict**: BYBIT-SPOT
  manifest holds 135,444 rows in three anomalous states — 81,659 with EMPTY `instrument_type` (not modeled by the -006
  plan) + 53,785 stamped PERPETUAL (the class this task describes) + ~54,000 rows under spot-nonsense data_types
  (derivative_ticker / futures_chain / options_chain / ohlcv_1m / perp_funding / liquidations — none valid for a spot
  venue; likely stray captures leaked from BYBIT-FUTURES or another venue). A simple PERPETUAL→SPOT_PAIR relabel of the
  53k subset would NOT close the plan's Gate ("manifest `by_venue_instrument_type` shows the split") because 82k EMPTY
  rows + 54k spot-nonsense-data_type rows would remain in states the plan does not model. Main-agent ruled: "-006
  forward-path fix (code) is the deliverable; mark DONE after the commit + issue doc are in; do not hold it open for the
  remediation. Operator notify: the stray derivative_ticker/futures_chain/options_chain/perp_funding/liquidations rows
  on a spot venue may indicate months of mis-routed capture — the issue doc should flag whether a re-capture (not just
  relabel) is needed for those rows." Follow-up issue doc filed at
  **`plans/active/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`** (`assigned_vm: planning`,
  `assigned_role: data_engineering`, `depends_on: [cefi_layer1_denominator_gaps-006]`) with 4 P1/P2 todos: (a) diagnose
  the 82k EMPTY rows (read-only); (b) diagnose the 54k spot-nonsense-data_type rows (read-only, cross-reference against
  BYBIT-FUTURES manifest to check for duplicates); (c) ship corrective-relabel script gated on (a)+(b); (d) populate
  `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` in UAC with `trades` + `book_snapshot_5`. Operator explicitly notified
  via the issue doc's NOTIFY-OPERATOR banner. Slot-8 /done cites `c4df8ae0` as the shipped SHA.
