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
- [ ] [DATA] P0. **2c. cefi MVP read-time gate (re-scoped — the manifest-pruning script is RETIRED).** Do NOT run
      `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` — DATA-LOSS: its `_derive_base` mis-parses Bitfinex
      `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE ~380k legit **captured** BITFINEX/KRAKEN rows; also
      circular (honest-coverage-v2 forbids deriving the denominator from the manifest). Instead apply the MVP filter as
      a **read-time gate in `measure_honest_coverage`**, folded into 2a `build_expected`. **PREREQ: 2b + the ASTER split
      landed.** Gate: MVP-cut applied at read time, ZERO manifest rows mutated, cefi measure honest.
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

- [ ] [CODE] P1. **Point-fix `_row_data_types` (cefi branch): intersect with
      `get_mvp_data_types_for_cefi_venue(venue)`** so the seeded denominator matches the capture gate (kills the MVP-cut
      over-seed class, e.g. COINBASE-SPOT trades-only). Complements the 2026-07-03 capability carve-out
      (`instruments-service@3bb7acd`) — that closed the VENUE_DATA_TYPE_CAPABILITIES half; this closes the MVP half. ~5
      lines + tests. > **⚠️ CAUTION (verified 2026-07-06, do not implement naively):** a literal >
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
- [ ] [CODE] P2. **Confirm the v1 `_ENUMERATORS`/`main()` dispatch is legacy → DELETE it** (the enumerator file carries
      two dispatch tables; docstring calls v2 the live path). Removes the second producer surface C2 flagged.

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
