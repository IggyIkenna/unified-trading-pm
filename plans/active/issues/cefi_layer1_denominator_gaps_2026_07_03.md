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
model_tier: opus-required
thinking_tier: max
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
> EVERY task): Opus / max.** Coordinator = `instruments_completion_tracker_2026_07_06.md` (Stage 2). The one law:
> **Layer-1 (denominator) gates Layer-2 (capture)** — this plan corrects + certifies the cefi denominator; capture (%)
> is meaningless until it lands. SSOT: `codex/02-data/honest-coverage-model.md` (do NOT derive the expected universe
> from the manifest — circular). Intra-plan ordering is by P-tag + the explicit `PREREQ:` note on each task; the
> critical spine is **2a `build_expected` → 2b gate-authority → 2c read-time MVP gate → 2f other venues → re-measure**.
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

- [x] ✅ [CODE] P0. **2a. Land the single `build_expected(asset_group)` producer** — `instruments-service@681f50a`.
      New module `scripts/expected_universe.py` exposes `build_expected(asset_group)` as THE public producer; per-AG
      strategies share one callable interface but preserve cefi/defi/tradfi/sports/prediction grains.
      `check_enumeration_completeness._build_expected_tuples` (and `..._sports`) now delegate via sibling-load (mirrors
      `measure_honest_coverage._load_completeness_module`); `measure_honest_coverage` routes transitively through the
      completeness module. Per-AG **byte-identical golden fixtures** at
      `tests/unit/scripts/goldens/expected_universe/{cefi,defi,tradfi,sports,prediction}.json` (72/171/35/27/8 tuples)
      + `test_expected_universe_golden.py` (14 tests: single-producer contract + delegator parity + byte-identical
      golden per AG + fixture metadata coherence). D2a declarative-gate authority baked in
      (`INSTRUMENT_TYPES_BY_VENUE` + `PROTOCOL_CAPABILITIES` + `TRADFI_VENUE_INSTRUMENT_TYPES` — NOT the Tardis
      fetch-routing map). All 76 impacted tests pass; QG-green (105s); no producer surface duplication remains.
      COINBASE / DERIBIT-COMBO MVP_SCOPE question raised as `BLK-5cc7590e` (bare COINBASE + DERIBIT-COMBO declared in
      `VENUES_BY_ASSET_GROUP["cefi"]` but `get_mvp_data_types_for_cefi_venue()` returns `frozenset()` → silent
      EXPECTED=0; 2a preserves byte-identical behaviour so both remain at 0, matching pre-refactor — the fix is
      downstream in 2b/2c). Evidence: `.qg_last_passed_sha=a1038eef81f2a79fd26918baf70c121207c20ad5` (pre-quickmerge),
      quickmerge shipped `681f50a`.
- [ ] [CODE] P0. **2b. cefi gate-authority fix on `build_expected`.** Apply D2a/D2b onto the single producer, then — in
      order — the ASTER live-forward split (enumerator `start_date` support is a HARD prereq before the UAC capability
      flip), the BYBIT-SPOT relabel, and the C2 MVP-data-type intersection (all detailed in the sections below).
      **PREREQ: 2a landed.** Gate: cefi EXPECTED reflects the full declared cefi universe (no whole-venue omission);
      dynamic tests pass (no golden edits); QG-green.
- [x] ✅ [DATA] P0. **2c. cefi MVP read-time gate (re-scoped — the manifest-pruning script is RETIRED).** Do NOT run
      `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` — DATA-LOSS: its `_derive_base` mis-parses Bitfinex
      `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE ~380k legit **captured** BITFINEX/KRAKEN rows; also
      circular (honest-coverage-v2 forbids deriving the denominator from the manifest). Instead apply the MVP filter as
      a **read-time gate in `measure_honest_coverage`**, folded into 2a `build_expected`. **PREREQ: 2b + the ASTER split
      landed.** Gate: MVP-cut applied at read time, ZERO manifest rows mutated, cefi measure honest.
      **DONE 2026-07-06 — instruments-service@2fa3877 (slot-8 planning).** New public
      `check_enumeration_completeness.filter_manifest_to_expected(ag, df)` filters manifest to rows whose canonical
      `(venue, itype, dt)` key is in `build_expected(ag)` — MVP scope baked in via
      `get_mvp_data_types_for_cefi_venue`. `measure_honest_coverage._compute_coverage` calls the filter for cefi
      (`_MVP_READ_TIME_GATE_AGS = {"cefi"}`) BEFORE Layer-2 counting; Layer-1 keeps the UNFILTERED df so stray_tuples
      remain visible. ZERO manifest mutation (returns a filtered VIEW; input df untouched). Same canonical key as the
      L1 check (`_canon_key` — case-fold + UAC alias + bundle rollup + cefi venue-fold OKX-SPOT→OKX/etc). Smoke test
      demonstrated: BYBIT-SPOT/perpetual/trades manifest row → dropped from Layer-2, still visible in Layer-1
      stray_tuples (writer PERPETUAL-stamp defect surfaced honestly). 11 unit tests
      (`tests/unit/scripts/test_filter_manifest_to_expected.py`) + 21 existing measure tests green (fake-checker stub
      updated with passthrough). QG-green 92s (sentinel 4368f381e). Filter is oracle-based on `build_expected`, so
      2b/ASTER-split changes propagate through automatically at re-measure time (task 5 — P2, gates on 2a–2f + ASTER
      wire + KALSHI-PERP purge).
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

- [ ] [CODE] P1. Diagnose + fix the BYBIT-SPOT `PERPETUAL` itype stamp (MTDS `symbol_rules._VENUE_INSTRUMENT_TYPE` has
      `"BYBIT": "perpetual"` but NO `BYBIT-SPOT` entry → spot rows fall through to PERPETUAL); add the map entry, fix
      the writer path, corrective-relabel existing rows. **Smoke-first** (relabel ONE shard + verify the manifest split,
      then scale). Gate: BYBIT-SPOT rows carry SPOT_PAIR; manifest `by_venue_instrument_type` shows the split.

## ASTER live-forward mode split (C1 RESOLVED — Ikenna 2026-07-03; sequencing is load-bearing)

Decision (recorded in `instruments_service_plan_reconciliation_2026_06_29.md` § C1): ASTER batch+live =
`trades`/`derivative_ticker`/`perp_funding`; **live-only-forward** = `book_snapshot_5` + `liquidations` (prediction-AG
pattern — live capture accumulates the history batch cannot provide; pre-wire history stays typed honest absence).
Capability check found the connectors already built (`aster_book_liq_ws.py`) but unwired, and ONE structural gap:
nothing date-gates seeding at the (venue, data_type) grain. Execute IN ORDER:

- [ ] [CODE] P1. **Enumerator honours per-(venue,dt) `start_date`** — `_row_data_types`/the cefi date loop must read
      `get_venue_data_type_start_date(venue, dt)` and seed `expected_unattempted` only from that date (earlier days →
      typed `EXPECTED_*` absence or out-of-universe). PREREQ for the capability flip — flipping first re-creates the
      17,282-row over-seed purged 2026-07-03.
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
      lines + tests.
      **DONE 2026-07-06 — instruments-service@2170d9a3 (slot-11 planning).** Bundle-aware MVP data_type gate landed in
      `_row_data_types` cefi branch (lines 873-899): `_mvp_capture_itype` normalises OPTIONS_CHAIN/COMBO→OPTION and
      FUTURES_CHAIN→FUTURE; when the bundle-normalised itype is NOT in `MVP_SCOPE["cefi"].instrument_type_data_types`
      (i.e. the flat/leaf case like COINBASE-SPOT trades), the venue-level MVP-gate intersection is applied against
      `get_mvp_data_types_for_cefi_venue(venue)`; when it IS in the override (Deribit OPTION → {options_chain}) the
      intersection is SKIPPED, preserving the upstream-narrowed `["options_chain"]` slice. A venue absent from MVP scope
      entirely returns an empty MVP set → the `if mvp_dts:` guard leaves row_dts unchanged (no blanket-block of
      non-MVP-scoped venues like BINANCE-DELIVERY). 4 regression tests added to `test_enumerate_expected_universe.py`
      covering COINBASE-SPOT drop-book5, Deribit options_chain/futures_chain survival, Deribit PERP drop-liquidations,
      and non-MVP-venue skip. QG-green (181s). Both failure modes flagged in the CAUTION avoided by the bundle-normalised
      `instrument_type_data_types` guard. > **⚠️ CAUTION (verified 2026-07-06, do not implement naively):** a literal >
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
- [x] ✅ [CODE] P2. **Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it** — **DEFERRED
      2026-07-06 — v1 is NOT safe to delete.** Slot-10 investigation (`BLK-0ac84889`) confirmed three v1
      roles v2 does NOT cover: (1) `_enumerate_v2_sports` explicitly delegates `EXPECTED_PRE_SOURCE_COVERAGE_START`
      dates to v1 (docstring L1552-1555 "v2 must NOT re-emit them or the (data_type, date) cell is
      double-counted at two grains"); (2) `tests/integration/test_enumerate_v2_superset_property.py` documents
      "tradfi v1 (non-trading days) is NOT a v2 grain match — v2 doesn't enumerate weekend/holiday cells" as an
      INTENTIONAL asymmetry; (3) v2 pre-venue-launch coverage is per-catalog-instrument grain vs v1 venue-grain
      sentinel — empty-catalog windows would lose seeding. Cross-repo cleanup also required in deployment-service
      (INFRA role). Main-agent ruling: BLOCK the full v1 deletion; file issue doc noting the finding. **Follow-on
      todos filed in `plans/active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md`** covering v2
      coverage extension (tradfi calendar + sports pre-coverage + venue-grain pre-launch sentinel), deployment-
      service infra cleanup, and the final v1 delete after those land. Evidence: no code change this pass; issue
      doc is the tracked-work artifact.

## Related fragility (observed live 2026-07-03)

- **Freshest-bucket PRIMARY selection is fragile to manifest surgery.** `measure_honest_coverage._read_manifest` picks
  the candidate with the newest `blob.updated` as PRIMARY (full frame) and reads the other as SECONDARY (**eu-only**).
  Rewriting the legacy cefi index (the ASTER corrective pass) bumped its mtime past prd → roles flipped → prd's
  captured-only tuples (e.g. BINANCE-FUTURES `future` rows consolidated 06-29) dropped from ENUMERATED and 3 artifact
  "holes" appeared. Mitigated in-session by a metadata bump restoring prd as freshest, but any future surgery on the
  older bucket re-triggers it. Consider content-based freshness (max manifest date) or pinning prd as primary. This may
  also explain the anomalous 05:07 UTC 2026-07-03 cefi-only measure (61.36%, present 29→27).
- [ ] [CODE] P2. Harden `_read_manifest` primary selection against surgery-bumped mtimes (content-based freshness or
      pinned-primary with explicit override).

## Progress Log

- **2026-07-03** — Filed from the reconciliation implementation session. Context: the venue-suffix fold + ASTER
  carve-out shipped in `instruments-service` (see the reconciliation issue doc); this finding is the structural
  remainder. Also noted: `INSTRUMENT_TYPES_BY_VENUE` exists in UAC and already covers most of the gate-blind venues —
  strongest candidate for the (venue,itype) authority.
- **2026-07-06** — **2a landed** (`instruments-service@681f50a`, slot-8 planning). Single-producer consolidation:
  `scripts/expected_universe.py::build_expected(asset_group)` is now THE Layer-1 EXPECTED producer;
  `check_enumeration_completeness._build_expected_tuples` delegates via sibling-load;
  `measure_honest_coverage` routes transitively. Byte-identical output preserved for all 5 AGs (cefi 72 / defi 171 /
  tradfi 35 / sports 27 / prediction 8) — captured as goldens under
  `tests/unit/scripts/goldens/expected_universe/`. New regression `test_expected_universe_golden.py` (14 tests: contract
  + delegator parity + golden byte-identical). Full suite green: 76 impacted tests + QG (105s). MVP_SCOPE
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
  `instruments-service/scripts/cefi_per_venue_capture_summary.py` — the enumerator itself does not read it.
  Additionally verified LIGHTER's REST `_fetch_lighter_book_for_symbol` stamps `datetime.now(UTC)` as timestamp
  (not the requested date) — confirming the ASTER live-WS/no-REST profile for `book_snapshot_5`; a UAC capability
  flip that adds start_date before the enumerator honours it would re-create the 17,282-row over-seed the plan
  warns against. Main-agent verdict: skip -004, add `depends_on: [cefi_layer1_denominator_gaps-002,
  cefi_layer1_denominator_gaps-007]` to task -004 in `backlog.yaml` and regen so the dispatcher gates it correctly.
  2f resumes when `-002` (2b) + `-007` (enumerator start_date) both land.
- **2026-07-06** — **UAC capability flip PARKED — BLOCKED-PREREQUISITES** (slot-8 planning, `BLK-36eeb447`). Task
  `cefi_layer1_denominator_gaps-008` (UAC capability flip — add ASTER `book_snapshot_5` + `liquidations` to
  `VENUE_DATA_TYPE_CAPABILITIES` with `start_date` = live-wire date, target
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144`) was dispatched by priority=20
  alone — SAME machine-encoded `depends_on` gap as -004. Verified LDR tip: `instruments-service/scripts/expected_universe.py`
  + `check_enumeration_completeness.py` still have zero `start_date` references; task -007 (enumerator `start_date`
  support) is `status=dispatched` to a peer slot but has NOT reached LDR (no commit to either file since 2a). Plan is
  explicit: "**PREREQ for the capability flip — flipping first re-creates the 17,282-row over-seed purged 2026-07-03.**"
  Main-agent verdict (`BLK-36eeb447` answered): PARK -008; do NOT touch UAC `VENUE_DATA_TYPE_CAPABILITIES` until -007
  confirmed shipped to LDR; the machine-encoded `depends_on` fix is an operator backlog.yaml action. -008 resumes when
  `-007` (enumerator `start_date`) lands. Slot-8 rotated to `cefi_layer1_denominator_gaps-009` (C2 point-fix).
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (2nd dispatch)** (slot-7 planning,
  `BLK-d8cba69b`). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-7 by priority=20 alone (the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` is still uncorrected on the backlog task — `depends_on:
  None` verified via `/api/backlog?limit=500`). Re-verified LDR tip at re-dispatch time:
  `instruments-service/scripts/expected_universe.py` + `check_enumeration_completeness.py` still have zero `start_date`
  references (last touching commits: `a1038ee` 2a, `2fa3877` 2c — neither adds start_date). Task -007 is `status=dispatched`
  to slot-11; tmux pane capture confirms slot-11 mid-work adding a per-`(venue, dt) start_date` regression test to
  `test_enumerate_expected_universe_v2.py`, but NOT yet shipped to LDR. Main-agent verdict (`BLK-d8cba69b` answered):
  PARK -008 — same ruling as `BLK-36eeb447`; the 17,282-row over-seed risk is real and documented; -008 will be
  re-dispatched after -007 lands. Slot-7 handed `understat_local_backfill_completion-004` (unrelated manifest
  normalisation) as next task.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (4th dispatch, `BLK-9072b84f`)** (slot-5
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-5 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` is still uncorrected on the backlog task.
  Re-verified LDR tip at re-dispatch: `instruments-service/scripts/expected_universe.py` +
  `check_enumeration_completeness.py` still have zero `start_date` / `get_venue_data_type_start_date` references (grep
  returns empty). Task `-007` remains `status=queued` (has NOT reached LDR — dispatched to a peer slot per prior
  entries but the work not committed). Main-agent verdict (`BLK-9072b84f` answered): PARK -008 — **4th ruling, same
  answer**. The 17,282-row over-seed risk stands; do NOT flip UAC `VENUE_DATA_TYPE_CAPABILITIES`. **Operator action
  required**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen
  to stop the bounce loop (4 dispatches, 4 blocks). Slot-5 goes idle pending operator's backlog fix; -008 resumes only
  when `-007` (enumerator `start_date`) reaches LDR.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (5th dispatch, `BLK-545a3adb`)** (slot-2
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-2 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged in `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` is STILL uncorrected on
  the backlog task (verified via `/api/backlog?limit=500`: `-008.depends_on = null`). Re-verified LDR tip at 5th
  re-dispatch: `instruments-service/scripts/expected_universe.py` last touched by `2fa3877` (2c) + `a1038ee` (2a) —
  neither commit adds `start_date` awareness; `check_enumeration_completeness.py` likewise contains zero
  `start_date` / `get_venue_data_type_start_date` refs. Task `-007` remains `status=queued` on the backlog
  (unchanged since 4th dispatch — no worker has landed it). Slot-2 verdict: PARK -008 — **5th consecutive block,
  same 17,282-row over-seed risk**. The bounce loop is now definitively an operator-backlog defect: 5 slots have been
  spent (8, 7, unnamed 3rd, 5, 2) verifying + escalating the same fact. **Operator action required (5th escalation)**:
  add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; -008 stays
  in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-2 goes idle pending operator's backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (6th dispatch)** (slot-9 planning). Task
  `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 by priority=20 alone; `depends_on` gap flagged in
  `BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` + `BLK-545a3adb` remains uncorrected on the backlog task (verified
  via `/api/backlog?limit=500`: `-008.status=dispatched`, `-008.depends_on = null`; `-007.status=queued`,
  `-007.depends_on = null`). Re-verified LDR tip at 6th re-dispatch: `instruments-service/scripts/expected_universe.py`
  contains ZERO `start_date` / `get_venue_data_type_start_date` refs (grep empty; last touching commit `a1038ee` 2a);
  `check_enumeration_completeness.py` likewise contains ZERO such refs (last touching commits `2fa3877` 2c + `a1038ee`
  2a). Task `-007` (enumerator `start_date` support) remains `status=queued` on the backlog with no worker having
  landed the work. Slot-9 verdict: PARK -008 — **6th consecutive block, same 17,282-row over-seed risk**. The bounce
  loop persists: 6 slots have now been spent verifying + escalating the same operator-backlog defect
  (`depends_on: [cefi_layer1_denominator_gaps-007]` still not encoded on `-008`). **Operator action required (6th
  escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and
  regen; -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9 goes idle pending operator's
  backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (7th dispatch)** (slot-9 planning, new
  session). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-9 AGAIN after the prior slot-9 session's
  6th-block park commit `7ad9a3c6b` (18:09 UTC) landed on LDR; task status returned to queued/dispatched. Machine-encoded
  `depends_on` gap flagged across 6 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` + `BLK-545a3adb` +
  6th-block) remains uncorrected: `/api/backlog?limit=500` at 7th re-dispatch: `-008.status=dispatched,
  depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip:
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` still contain ZERO
  `start_date` / `get_venue_data_type_start_date` refs (last touching commits `a1038ee` 2a + `2fa3877` 2c —
  neither adds start_date). Confirmed ASTER capability entry alive at `unified-api-contracts/registry/
  market_data_categories.py:1144` (target of the flip). Slot-9 verdict: PARK -008 — **7th consecutive block, same
  17,282-row over-seed risk**. The bounce loop is not self-correcting: 7 slots (8, 7, unnamed 3rd, 5, 2, 9, 9-again)
  have now been spent verifying + escalating the identical operator-backlog defect. **Operator action required (7th
  escalation)**: add `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and
  regen; -008 stays in queue until `-007` (enumerator `start_date`) reaches LDR. Slot-9 goes idle pending operator's
  backlog fix.
- **2026-07-06** — **UAC capability flip RE-PARKED — BLOCKED-PREREQUISITES (8th dispatch, `BLK-e642f2aa`)** (slot-4
  planning). Task `cefi_layer1_denominator_gaps-008` was RE-dispatched to slot-4 by priority=20 alone; the
  machine-encoded `depends_on` gap flagged across 7 prior blocks (`BLK-36eeb447` + `BLK-d8cba69b` + `BLK-9072b84f` +
  `BLK-545a3adb` + 6th + 7th) is STILL uncorrected. Re-verified at 8th re-dispatch via `/api/backlog?limit=500`:
  `-008.status=dispatched, depends_on=null`; `-007.status=queued, depends_on=null`. Re-verified LDR tip with
  `rg -c 'start_date|get_venue_data_type_start_date'` on both files: ZERO matches on
  `instruments-service/scripts/expected_universe.py` + `scripts/check_enumeration_completeness.py` (last touching
  commits unchanged: `a1038ee` 2a + `2fa3877` 2c). Confirmed ASTER capability entry alive at
  `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1144` (flip target). Slot-4 verdict:
  PARK -008 — **8th consecutive block, same 17,282-row over-seed risk**. The bounce loop remains not self-correcting:
  8 slots (8, 7, unnamed 3rd, 5, 2, 9, 9-again, 4) have now been spent verifying + escalating the identical
  operator-backlog defect — this is now a systemic-cost finding (each dispatch consumes ~10 min of a worker's context
  budget + a Claude-Code cycle). **Operator action required (8th escalation)**: add
  `depends_on: [cefi_layer1_denominator_gaps-007]` to `-008` in `data/config/backlog.yaml` and regen; alternatively
  flip `-008`'s backlog priority to 999 so higher-priority queued tasks dispatch instead. -008 stays in queue until
  `-007` (enumerator `start_date`) reaches LDR. Slot-4 goes idle pending operator's backlog fix.
- **2026-07-06** — **C2 point-fix (-009) flipped ✅** (slot-9 planning). Main released -008 via /skip-current-task
  answering `BLK-be92ef1e` Option A; -009 dispatched to slot-9 next. Verified code already landed on LDR by slot-11:
  `instruments-service@2170d9a3` (18:23:15 UTC, "feat(scripts): bundle-aware MVP data_type gate in _row_data_types
  cefi branch — closes cefi_layer1_denominator_gaps C2 point-fix (item 009)") — 31 lines in
  `scripts/enumerate_expected_universe.py` (the MVP data_type gate at lines 873-899) + 117 lines of regression tests
  (4 tests) in `tests/unit/scripts/test_enumerate_expected_universe.py`; QG-green 181s per commit message. The
  correct instrument-type/bundle-aware approach the CAUTION prescribed is implemented via `_mvp_capture_itype`
  normalisation + `cefi_rule.instrument_type_data_types` membership check. Deribit `options_chain` slice preserved via
  the OPTION-override skip; COINBASE-SPOT `book_snapshot_5` dropped; Deribit PERP `liquidations` dropped;
  non-MVP-scoped venues (e.g. BINANCE-DELIVERY) unaffected by the empty-mvp_dts guard. Slot-9 action:
  checkbox-flip only (no code change) — /done cites `2170d9a3` as the shipped SHA.
- **2026-07-06** — **Re-measure task (-005) PARKED — BLOCKED-PREREQUISITES (`BLK-ad7abfcd`)** (slot-8 planning). Task
  `cefi_layer1_denominator_gaps-005` ("Re-measure + re-certify the cefi Layer-1 row") was dispatched to slot-8 by
  priority=50 alone; the machine-encoded `depends_on` gap flagged across 8 prior `-008` blocks now also affects `-005`
  (verified via `/api/backlog?limit=500`: `-005.status=dispatched, depends_on=null`). Verified plan-declared PREREQ
  chain ("2a–2f landed + ASTER live wire (Plan 5) + KALSHI-PERP purge (Stage-3)") is NOT met:
  (i) `-002` (2b cefi gate-authority fix on `build_expected`) status=queued — D2a `INSTRUMENT_TYPES_BY_VENUE` authority
  IS baked into `scripts/expected_universe.py` (part of 2a's consolidation) but the 2b sub-parts (ASTER live-forward
  split + BYBIT-SPOT relabel) remain unshipped;
  (ii) `-004` (2f LIGHTER/EXTENDED/PACIFICA denominator-gap) status=queued — depends on enumerator `start_date`;
  (iii) `-007` (enumerator `start_date` support) status=queued — verified LDR tip:
  `instruments-service/scripts/expected_universe.py` has ZERO `start_date` / `get_venue_data_type_start_date` refs
  (grep empty; last touching commits `a1038ee` 2a + `2fa3877` 2c — neither adds start_date);
  (iv) ASTER live wire (Plan 5, INFRA role) — connector `market_tick_data_service/live/connectors/aster_book_liq_ws.py`
  EXISTS but is NOT registered in `market_tick_data_service/live/connector_registry.py` (grep empty on
  `aster_book_liq_ws|AsterBookLiq`);
  (v) KALSHI-PERP purge (Stage-3) — commit `c8c6dac` only guards the KALSHI-PERP/POLYMARKET-PERP adapters to emit 0 (a
  forward stop-gap); the 25,473 fake `KALSHI-PERP` cefi Layer-2 rows still pollute the manifest and would over-inflate
  the numerator. Running the re-measure now would produce a misleading % moving in the WRONG direction from the plan
  Gate ("denominator GREW, % dropped honest") — the denominator would still UNDER-count (2f venues at 0-expected while
  their manifest rows exist) while the numerator OVER-counts (fake KALSHI-PERP rows). Slot-8 verdict: PARK -005 —
  recommendation A of `BLK-ad7abfcd`. **Operator action required**: add
  `depends_on: [cefi_layer1_denominator_gaps-002, cefi_layer1_denominator_gaps-004, cefi_layer1_denominator_gaps-007]`
  to `-005` in `data/config/backlog.yaml` + regen (or flip `-005` priority to 999) to prevent the same bounce-loop the
  `-008` block-chain hit 8×. -005 stays in queue until 2b/2f/-007/ASTER-wire/KALSHI-PERP-purge all reach LDR. Slot-8
  goes idle pending operator answer + backlog fix.
