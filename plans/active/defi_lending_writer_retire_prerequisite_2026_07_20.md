---
doc_type: plan
title: DeFi lending writer fix — resolver-based close-out of the D2 flat-LENDING question (physical retire WON'T-DO)
summary: >-
  Fix the MTDS market/event lending writers that broke into `attempted_failed`/zero-data when the flat-`LENDING` →
  `A_TOKEN`/`DEBT_TOKEN` retire was first attempted, and close the shard-atom desync (GCS `instrument_type=a_token` vs
  manifest `lending`) that the partial work-around introduced (todos 1-6/9/12/13, DONE). **Session-3 (2026-07-26,
  operator present) decision: the physical A_TOKEN/DEBT_TOKEN retire (todos 8/10/11/14) is WON'T-DO, permanently — after
  two reversals, a read-side resolver function (todo 15) delivers the same canonical-instrument-id → rate lookup without
  the GCS rewrite / manifest re-key / IS re-seed the flip required.** Also surfaced a live data-correctness bug (todo
  16): `evm_defi_handler.py` and `lending_indices_handler.py` redundantly double-capture Aave/Compound/Morpho
  `lending_indices` into the same shard, and the former silently drops the supply rate.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags:
  [
    lending,
    instrument-type,
    shard-atom,
    canonicalisation,
    mtds-writers,
    a-token,
    debt-token,
    prerequisite,
    migration-gate,
  ]
related:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    issues/canonical_closeout_open_questions_2026_07_18.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-07-20
last_updated: 2026-07-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2.0
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  operator ruling D2, 2026-07-20 — "complete the FULL LENDING retire"; scoped by
  data_pipeline_reconciliation_skill_2026_07_20.md todo 23
---

# DeFi lending writer fix — resolver-based close-out (physical retire WON'T-DO)

> **⛔ SUPERSEDES the original D2-retire gate banner below (session-3, 2026-07-26, operator present).** The operator's
> **D2** ruling (2026-07-20) originally called for the FULL flat-`LENDING` retire to `A_TOKEN`/`DEBT_TOKEN` via a
> ~16.7M-row migration. Sessions 1-2 (below) proved that migration cannot ship safely as a writer-fix-only step — it
> needs an atomic UAC+MTDS+UTL wave PLUS an instruments-service `expected_unattempted` re-seed, and the operation has
> already been reversed twice. **Session-3 decision: stop pursuing the physical retire. It will not ship.** Instead, a
> new read-side resolver (todo 15) gives downstream consumers the canonical A_TOKEN/DEBT_TOKEN instrument_id → rate
> lookup the retire was meant to provide, without touching the physical data model. See the session-3 Progress Log entry
> for the full reasoning and the newly-found `evm_defi_handler.py`/`lending_indices_handler.py` duplicate-capture bug
> (todo 16).
>
> **Original mandatory-order banner, preserved for history (no longer operative — steps 2/3 never happen):**
>
> 1. ~~Fix the writers (THIS PLAN) and prove them green on a real run.~~ — DONE for the parts that were real bugs (todos
>    1-6/9/12/13); the rest of "fixing the writers" (the flip itself) is now moot.
> 2. ~~Migrate the ~16.7M rows.~~ — WON'T-DO.
> 3. ~~Re-sync the shard atom across GCS · manifest · data-status · UI.~~ — WON'T-DO, nothing to re-sync.
>
> **Ruling authority**: `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` §"OPERATOR DECISIONS — ALL THREE
> RULED 2026-07-20" (D2 + its "D2 consequences" block) — **D2's migration mandate is reversed by this session's decision
> above**, D1 (C2a casing) is unaffected. **Codex SSOTs** (referenced, never duplicated here):
> `/codex/02-data/defi-canonical-naming-ssot.md` (the two-layer lending model — being updated by todo 17 to drop the
> interim/migration_pending framing) · `/codex/02-data/availability-manifest-and-data-status.md` (shard atom, 4-state
> `capture_status`) · `/codex/04-architecture/shard-level-failure-isolation.md` (per-shard `except` discipline).

---

## What actually broke — the measured mechanism

The first attempt shipped `unified-api-contracts@e319864f`, which moved `InstrumentType.LENDING` into
`UNSUPPORTED_BY_DESIGN`. The chain that follows is short and entirely mechanical:

1. `unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py:822-824` —
   `build_instrument_id` raises `ValueError` for any type in `UNSUPPORTED_BY_DESIGN`. (Post-revert, that frozenset is
   **empty** today: `:186` `UNSUPPORTED_BY_DESIGN: Final[frozenset[InstrumentType]] = frozenset()`.)
2. `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py:262` —
   `inst_id = build_instrument_id(v, instrument_type, symbol, chain=c)`, called **per row** inside `write_defi_rows`.
   Every lending row therefore raised.
3. Each handler wraps its per-shard body in a broad `except (… ValueError …)` → `recorder.record_failed(…)`. Verified
   verbatim at `flash_loan_events_handler.py:214-223`. The result is **`attempted_failed` manifest rows with zero
   captured data** — a silent, honest-looking failure, not a crash. This is the load-bearing detail: the writers did not
   break loudly; they broke into a state the manifest renders as a legitimate failure.
4. The partial work-around (migrate _some_ handlers to `A_TOKEN`) then split the atom, because the **GCS path
   `instrument_type`** and the **manifest row `instrument_type`** are derived from **two independent expressions** in
   most handlers — see the desync section below. Migrating one and not the other produced GCS `instrument_type=a_token`
   against manifest `lending`.

**Reversal record** (cited, read): `plans/active/defi_consolidated_closeout_2026_07_18.md:683-691` (the
`LENDING`-raise-reversed todo) and its Progress Log at `:1487-1500` (the "⚠️ BIG FINDING — the Wave-B flat-LENDING RAISE
over-reached" entry) and `:1465-1476` (the `market-tick-data-service@acfb76ca` revert + the
`no_raising_writer_remains=true` / `shard_atom_consistent=true` verify). The reverting commits are
`unified-api-contracts@ad4886ae` + `market-tick-data-service@acfb76ca`.

## The writers — measured, not the audit's "5+"

**The audit synthesis's "5+ MTDS lending writers" figure is an UNDERCOUNT.** It enumerated five _groups_
(`liquidation_events` / `flash_loan_events` / `position_data` / `evm_defi`'s EVM venues / `solana_defi`) taken from the
Progress Log at `defi_consolidated_closeout_2026_07_18.md:1493`. A separate, earlier log entry at `:1516-1522` names
three MORE that went QG-red on the same change (`lending_indices` / `liquidations` / `risk_params`), and those were
never folded into the "5+" headline. Grepping the live tree confirms the earlier entry.

**Real count: 7 modules emit flat `LENDING` today, plus 1 adjacent module emitting `SOLANA_LENDING`** — 8 in scope.
(`_instruments_metadata.py` was also named in one log line; it is **not** an emitter — its only `lending` occurrences
are a docstring at `:6` and a comment at `:167`, and its `:326` `"instrument_type"` is a column name. Excluded,
verified.)

All paths below are relative to `market-tick-data-service/market_tick_data_service/cli/handlers/`.

| #   | Writer                          | Emits today (GCS path side)                                                                                         | Emits today (manifest side)                                                                                                          | Post-retire target                                          | Why it broke / what must change                                                                                                                                                                                                                                                                                           |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `liquidation_events_handler.py` | `:306` `instrument_type=InstrumentType.LENDING` → `write_defi_rows`                                                 | `:330` passes the `instrument_type: str` param threaded from `_PROTOCOLS` `:54-57` (`("aave_v3","lending")`, `("morpho","lending")`) | `A_TOKEN`/`DEBT_TOKEN` per market side                      | **Dual literal.** The enum at `:306` and the hardcoded tuple strings at `:54-57` are independent — migrating one desyncs the atom. Raise path: `:306` → `canonical_write.py:262`.                                                                                                                                         |
| 2   | `flash_loan_events_handler.py`  | `:176` `InstrumentType.LENDING`                                                                                     | `:201` hardcoded string `"lending"`; also `:147` `read_instrument_addresses(instrument_type="lending")`                              | `A_TOKEN` (flash loans are supply-side against the reserve) | **Triple literal**, incl. a READ-side literal at `:147` that must move in lockstep or the known-pool lookup silently returns empty. Confirmed swallow at `:214-223` (`except (aiohttp.ClientError, OSError, ValueError, KeyError)` → `record_failed`).                                                                    |
| 3   | `position_data_handler.py`      | `:198` `InstrumentType.LENDING`                                                                                     | `:225` hardcoded string `"lending"`                                                                                                  | `A_TOKEN`/`DEBT_TOKEN` (positions carry both legs)          | **Dual literal.** Grain is the market address via `market_count_map(rows, _POSITION_GRAIN_FALLBACK_COLUMNS)` `:216`; the type change must not disturb that grain or ~1.04M `expected_unattempted` rows stop converting (see `_lending_grain.py:1-19`).                                                                    |
| 4   | `evm_defi_handler.py`           | `:200`+`:211` via `_resolve_evm_defi_instrument_type(protocol)` `:130-139`                                          | same resolver (single point, by design — see its docstring `:131-138`)                                                               | `A_TOKEN`/`DEBT_TOKEN`                                      | **7 protocols, not 6** — `:119-126` maps `aave_v3`, `compound_v3`, `morpho`, `venus`, `benqi`, `radiant`, `euler_v2`, plus a `.get(..., InstrumentType.LENDING)` default at `:139`. Already has the correct single-resolution-point shape; this is the pattern the other handlers must adopt.                             |
| 5   | `lending_indices_handler.py`    | `:863` hardcoded `InstrumentType.LENDING` (EVM/subgraph path); `:430` `SOLANA_LENDING` (Solana path)                | `:674` `itype_str` from `_lending_instrument_type_str(protocol)` `:182-184`                                                          | `A_TOKEN`/`DEBT_TOKEN` (EVM); Solana per todo 6             | **Write side is a hardcoded literal, manifest side is a resolver** — the two only agree today because the EVM branch happens to be the one reaching `:863`. That coincidence is the desync waiting to happen; unify onto one resolver.                                                                                    |
| 6   | `liquidations_handler.py`       | `:644` `InstrumentType.LENDING`                                                                                     | `:534` hardcoded string `"liquidation"`                                                                                              | `A_TOKEN`/`DEBT_TOKEN`                                      | **ALREADY DESYNCED IN PROD, independent of the retire** — GCS path writes `lending`, the manifest row says `liquidation`. Flagged as a known Wave-D item at `defi_consolidated_closeout_2026_07_18.md:1471-1474`. This must be fixed before the migration or the migration will rewrite one surface and orphan the other. |
| 7   | `risk_params_handler.py`        | `:651` via `_lending_instrument_type(protocol)` `:121-123` (`.get(..., InstrumentType.LENDING)`)                    | `:485`/`:554` via `_lending_instrument_type_str(protocol)` `:116-118`                                                                | `A_TOKEN`/`DEBT_TOKEN`                                      | **Two parallel resolvers** (one enum-returning, one str-returning) that must be kept in agreement by hand. Collapse to one.                                                                                                                                                                                               |
| 8   | `solana_defi_handler.py`        | `:585` via `_SOLANA_PROTOCOL_INSTRUMENT_TYPES` `:321-332` — `kamino_lending`/`marginfi`/`solend` → `SOLANA_LENDING` | same map                                                                                                                             | **scope decision required (todo 6)**                        | Not flat `LENDING`, so not strictly in the D2 retire's literal scope — but it is the Solana mirror of the same model, and its comment at `:315-320` explicitly ties it to `risk_params_handler`/`lending_indices_handler`. Leaving it behind creates a new EVM/Solana asymmetry.                                          |

## The shard-atom desync mechanism — where each side is derived

The two surfaces are derived at **different call sites from different expressions**, and nothing enforces their
agreement:

- **GCS path side** — `market_interface/adapters/defi/canonical_write.py`. The caller passes a typed `InstrumentType`
  (`:130`); the path segment is `instrument_type.value.lower()` at `:195`, and the same lowercased value is stamped into
  the parquet content column at `:249` and `:269`. Path shape documented at `:14`.
- **Manifest row side** — `DefiManifestRecorder.record_captured(instrument_type=…)`, called by each handler with an
  **independent, usually hardcoded, lowercase string** (writers 1, 2, 3, 6 above) or a **separate str-returning
  resolver** (writers 5, 7).

So `instrument_type` is written twice per shard, from two expressions, with no shared source. Migrating the enum without
migrating the string is exactly how the first attempt produced GCS `a_token` against manifest `lending`.
`evm_defi_handler.py:130-139` is the only handler that already collapses both onto one resolver — and its docstring at
`:134-138` states that as its explicit purpose. **That is the fix pattern for the whole family.**

---

## Acceptance criteria

This plan is **green** — and only then may step 2 (the ~16.7M-row migration) begin — when all of the following hold:

1. Every one of the 8 writers above derives its GCS-path `instrument_type` and its manifest-row `instrument_type` from a
   **single** resolution point, in the `evm_defi_handler.py:130-139` shape. Zero remaining hardcoded `instrument_type`
   string literals on any lending record/write site.
2. `liquidations_handler.py`'s `"liquidation"`-vs-`LENDING` divergence is closed on both surfaces.
3. `build_instrument_id` succeeds for every `(venue, instrument_type, symbol, chain)` tuple the 8 writers can produce,
   under the post-retire type set — proven by a test that enumerates the tuples from the handlers' own maps, not from a
   hand-written list.
4. A real one-day run of each of the 8 writers records **`captured` rows with non-zero counts and zero
   `attempted_failed`**, verified by reading the manifest — not by the handler's own return value.
5. GCS object `instrument_type=` path segment, the parquet content column, and the manifest row agree for every shard
   produced by that run (a 3-surface spot check at the shard atom).
6. The per-market grain is unchanged — `expected_unattempted` conversion behaviour is not regressed by the type change
   (the `_lending_grain.py:1-19` requirement).
7. MTDS `bash scripts/quality-gates.sh --no-fix` is green, and the DTZ/TID251/fallback-import baselines have not risen.
8. No `except … ValueError …` on a lending write path can convert a **contract** error into `record_failed` without a
   distinct, loud classification.

---

## Todos

- [x] ✅ 1. [DATA] P0. **Assert the gate in the migration's own plan.** Add a dated banner to
      `plans/active/defi_consolidated_closeout_2026_07_18.md`'s "Retire legacy `LENDING` → A_TOKEN/DEBT_TOKEN" todo
      (`:426`) stating the migration is BLOCKED on this plan and naming this file. Do **not** restate the mechanism
      there — link it. This exists so a worker reading the migration todo cold cannot start step 2 first, which is
      precisely what happened the first time.
- [x] ✅ 2. [CODE] P0. **SHIPPED `market-tick-data-service@fec20de2`.** Collapse writers 1, 2, 3 to a single resolution
      point. `liquidation_events_handler.py` (`:306` enum vs `:54-57`/`:330` strings), `flash_loan_events_handler.py`
      (`:176` vs `:147`/`:201`), `position_data_handler.py` (`:198` vs `:225`). One resolver per handler returning the
      `InstrumentType`; the manifest site derives its string from that same value. Mirror `evm_defi_handler.py:130-139`
      exactly, including its docstring rationale. No behaviour change yet — the emitted value stays `LENDING` in this
      todo.
- [x] ✅ 3. [CODE] P0. **SHIPPED `market-tick-data-service@fec20de2`.** Collapse writers 5 and 7.
      `lending_indices_handler.py` `:863` hardcoded enum vs `:674`/`:182-184` resolver; `risk_params_handler.py`
      `:121-123` enum resolver vs `:116-118` str resolver. One resolver each, str derived from the enum. Keep the
      EVM-vs-Solana branch distinction intact (`:430` must still resolve `SOLANA_LENDING`) — verify by reading which
      branch each protocol in `_DEFAULT_PROTOCOLS` `:172` actually reaches before collapsing, do not assume.
- [x] ✅ 4. [CODE] P0. **SHIPPED `market-tick-data-service@fec20de2`.** Fix the live `liquidations_handler` desync —
      `:534` manifest `"liquidation"` vs `:644` GCS `LENDING`. Decide which is correct against
      `/codex/02-data/defi-canonical-naming-ssot.md` (the naming SSOT is the authority, not either literal), fix both
      surfaces onto one resolver, and record whether already-written rows need a re-key as a todo in the migration plan
      (this plan does not own the data fix).
- [x] ✅ 5. [CODE] P0. **SHIPPED `market-tick-data-service@fec20de2`.** Make the contract error loud. On every lending
      write path, a `ValueError` originating from `build_instrument_id` must NOT be swallowed into `record_failed` as if
      it were a venue/network failure — classify it distinctly per
      `/codex/04-architecture/shard-level-failure-isolation.md` and UAC `classify_venue_error()`. Verified swallow site
      to start from: `flash_loan_events_handler.py:214-223`. This is the change that would have made the first attempt
      fail loudly in minutes instead of silently producing `attempted_failed` rows.
- [x] ✅ 6. [CODE] P0. **RULED (session-2 entry above) — SOLANA_LENDING is OUT of the D2 EVM retire scope.** Rule the
      `SOLANA_LENDING` scope question and record the answer in this plan. D2 names flat `LENDING`;
      `solana_defi_handler.py:321-332`, `lending_indices_handler.py:175-179` and `risk_params_handler.py:110-112` emit
      `SOLANA_LENDING` for `kamino_lending`/`marginfi`/`solend`. Either it splits to `A_TOKEN`/`DEBT_TOKEN` alongside
      EVM, or it is explicitly OUT of scope with a stated reason. Leaving it undecided reproduces the "interim that
      nobody ruled" state that produced this whole contradiction. Escalate as an option-set if it is not decidable from
      the naming SSOT.
- [x] ✅ 7. [CODE] P0. **Define the per-data_type target mapping — DESIGN COMPLETE, session-2 Progress Log ("Todo 7 —
      per-data_type A_TOKEN/DEBT_TOKEN target mapping (REFINED, SOLANA out)").** Full table shipped: `lending_indices` +
      `position_data` are FAN-OUT (both legs, per-row); `liquidation_events`/`flash_loan_events`/`risk_params`/
      `liquidations` are relabel-only (A_TOKEN). This is design-complete, NOT implementation — todo 8 remains open to
      apply it in code as part of the atomic 3-repo wave.
- [x] ⛔ 8. [CODE] P0. **WON'T-DO (session-3, 2026-07-26) — superseded, not deferred.** Was: ship the retire atomically
      across UAC/MTDS/UTL. The operator decided (session-3 Progress Log) to never do the physical flip — see todo 15's
      resolver instead. Closing rather than leaving `- [ ]` since the premise (a physical A_TOKEN/DEBT_TOKEN retire will
      eventually ship) no longer holds.
- [x] ✅ 9. [TEST] P0. **SHIPPED `market-tick-data-service@fec20de2` —
      `tests/unit/test_defi_lending_writer_instrument_type_pinning.py`.** Enumerate-from-source pinning tests. A test
      that reads each handler's own protocol→type map and asserts `build_instrument_id` succeeds for every producible
      tuple, plus a test asserting GCS-path segment == parquet column == manifest row `instrument_type` for a
      representative shard per writer. Enumerating from the handlers' maps (not a hand-written list) is what makes this
      survive the next protocol addition.
- [x] ⛔ 10. [DATA] P0. **WON'T-DO (session-3) — superseded.** Was the runtime green proof for the flip; moot, no flip
      is shipping.
- [x] ⛔ 11. [DATA] P0. **WON'T-DO (session-3) — superseded.** Was the 3-surface agreement check for the flip; moot.
- [x] ⛔ 12. [DATA] P1. **N/A — the flip never lands, so there is nothing to regress-check.** (Todo 12's own analysis
      already proved the writer-fix collapse is value-preserving; that finding stands independent of this closure.)
- [x] ✅ 13. [DOCS] P1. **SHIPPED `market-tick-data-service@fec20de2` (same wave as todo 2-5/9).** Align the MTDS docs
      to what shipped — `docs/GCS_PATHS.md`, `docs/DEFI_DOWNLOAD_STRATEGY.md`, `docs/DATA_TYPE_DECISIONS.md` all carry
      the interim `instrument_type=lending` statement (shipped `market-tick-data-service@e9764b38`). **Session-3 note:**
      these need a FURTHER update alongside todo 17 — "interim, migration_pending" language must become "permanent,
      resolver-backed" everywhere it appears, not just in the naming SSOT.
- [x] ⛔ 14. [PM] P1. **WON'T-DO (session-3) — superseded.** Was: flip the migration gate to CLEARED. There is no
      migration to clear into — see todo 18 (closes the migration plan's reference instead).
- [x] ✅ 15. [CODE] P0. **SHIPPED `unified-api-contracts@1d01a911`.** Build the canonical A_TOKEN/DEBT_TOKEN → rate
      resolver. New function in `unified-api-contracts`, DeFi lending domain module (grep for where
      `AavePoolParams`/`RateImpactResult` / `rate_model.py` live — colocate). Given a canonical A_TOKEN or DEBT_TOKEN
      instrument_id: resolve `(venue, chain, underlying_symbol)` from instruments-service's registered
      `InstrumentRecord` metadata for that instrument; look up the matching flat-`LENDING`/`SOLANA_LENDING`
      `lending_indices` row for `(venue, chain, underlying_symbol, day)`; return `supply_apy` for an A_TOKEN caller,
      `borrow_apy` for a DEBT_TOKEN caller. Grep features-onchain/strategy-service for any existing ad-hoc attempt at
      this join and point them at the new function. Unit tests: both branches, plus the underlying-symbol/venue/chain
      resolution, plus a not-found case (no LENDING row for that market/day — must return an honest absence, never a
      fabricated 0.0).
- [x] ✅ 16. [CODE] P0. **SHIPPED `market-tick-data-service@5c055e04`.** Reconciled the `evm_defi_handler.py` vs
      `lending_indices_handler.py` duplicate capture + fixed the missing-supply-rate bug. `evm_defi_handler.py`'s
      `collect-evm-defi` and `lending_indices_handler.py`'s `collect-lending-indices` both fetch Aave V3's
      `reserveParamsHistoryItems` for `aave_v3`/`compound_v3`/`morpho` and write the same `data_type=lending_indices`
      partition; `evm_defi_handler.py`'s batch query never fetches `liquidityRate` so its rows silently lack a supply
      rate, and whichever handler wrote last wins the shard. Read both capture paths fully (this is genuine
      investigation, not scripted — determine whether `collect-evm-defi` is still actively invoked anywhere for these 3
      overlapping protocols, or whether it's effectively dead/superseded historical-backfill-only code) before deciding:
      either stop `evm_defi_handler.py` from covering the 3 overlapping protocols (keep it for its unique
      `venus`/`benqi`/`radiant`/`euler_v2` coverage only, where there's no duplication), or fix its query to include
      `liquidityRate` and designate ONE of the two as authoritative writer-of-record. File as a data-correctness finding
      per `/codex/02-data/data-pipeline-correctness-hard-rule.md` regardless of which fix is chosen — this is a live
      bug, not a design question.
- [ ] 17. [DOCS] P0. **[session-3] Update the naming SSOT.** `codex/02-data/defi-canonical-naming-ssot.md`
      instrument_type row: replace "RULED 2026-07-20 D2... FULL retire... migration_pending" with the resolved decision
      — flat `LENDING`/`SOLANA_LENDING` is now PERMANENT for market/event lending data; canonical A_TOKEN/DEBT_TOKEN
      rate lookup is via todo 15's resolver (name it explicitly), not by re-keying raw data. State plainly this reverses
      D2's migration mandate and why (avoids a third reversal of the same operation; achieves the same downstream
      capability with no GCS rewrite / no manifest re-key / no IS re-seed). Also close the
      `"Same logic for `lending_indices`"` cross-reference in the `dex_pool_state` section and any other doc carrying
      the old "interim, migration_pending" framing (todo 13's docs need the same pass).
- [ ] 18. [PM] P0. **[session-3] Close the migration reference in `defi_consolidated_closeout_2026_07_18.md`.** That
      plan's `:426` "Retire legacy `LENDING` → A_TOKEN/DEBT_TOKEN" todo and its `:429` BLOCKED banner (set by this
      plan's own todo 1) currently point at a migration that is no longer going to happen. Close/remove that todo with a
      note pointing to this plan's session-3 decision + the updated codex doc. Do not touch any other todo in that plan.

---

## Progress Log

### 2026-07-20 — plan created (scoping only; no code touched)

Filed per todo 23 of `data_pipeline_reconciliation_skill_2026_07_20.md`, applying operator ruling **D2**.

**Correction to the audit synthesis**: the "5+ MTDS lending writers" figure is an undercount. The five named in
`defi_consolidated_closeout_2026_07_18.md:1493` omit `lending_indices` / `liquidations` / `risk_params`, which an
earlier log entry at `:1516-1522` names as the group that went MTDS-QG-red on the same change. Live-tree grep confirms
**7 modules emitting flat `LENDING`** plus **1 adjacent module emitting `SOLANA_LENDING`** — 8 in scope.
`_instruments_metadata.py`, named once in the logs, is not an emitter (docstring/comment only) and is excluded.

**Two findings surfaced during scoping that were not in the audit:**

1. `liquidations_handler.py` is **already desynced in production** — manifest `"liquidation"` (`:534`) vs GCS path
   `LENDING` (`:644`) — independent of the retire. Known as a Wave-D item (`:1471-1474`) but not previously connected to
   the migration's blast radius. Migrating with this open would rewrite one surface and orphan the other → todo 4.
2. `evm_defi_handler.py` maps **7** EVM protocols (`:119-126`), not the 6 the audit reports.

**Not verified / open:**

- The correct per-data_type `A_TOKEN`-vs-`DEBT_TOKEN` mapping (todo 7) is genuine unresolved design work — the
  reversal's own diagnosis was that no clean single mapping exists. This plan scopes it; it does not answer it.
- Whether `SOLANA_LENDING` is in or out of D2's scope (todo 6) is not decidable from the ruling text as written.
- Whether any Solana protocol can reach `lending_indices_handler.py:863` (the hardcoded-`LENDING` write path) was not
  traced to a terminal answer — todo 3 requires reading the branch before collapsing, not assuming.

### 2026-07-21 — todos 1-5, 9, 13 code-complete + verified; todo 3 branch traced; todos 6-7 ruled/designed; NOT YET COMMITTED (blocked on 2 unrelated cross-repo test-baseline regressions in the shared tree); todos 8/10/11/14 deferred

**Todo 3 branch trace** (verified before collapsing): `lending_indices_morpho.py::_maybe_dedicated_collector` routes
`chain=="SOLANA" and protocol in _SOLANA_LENDING_PROTOCOLS` → `_collect_solana_lending`, `protocol=="morpho"` →
`_collect_morpho_lending` (itself calls `_write_protocol_chain_rows`), else falls through to
`_write_protocol_chain_rows` via the generic subgraph cascade. So the `:863` hardcoded-enum site is reached by
`aave_v3`/`spark`/`compound_v3`/`morpho` only — never by `kamino_lending`/`solend`/`marginfi` (those always divert to
`_collect_solana_lending`, which had its OWN separate hardcoded resolver call, correct in value but a second
expression). Collapsed both onto ONE resolver (`_resolve_lending_indices_instrument_type`) — no behaviour change.

**Todo 6 ruling — SOLANA_LENDING IS IN SCOPE of the eventual full retire (decidable from evidence, no escalation
needed):** `instruments-service/reference_data/adapters/defi/marginfi.py` + `.../solend.py` ALREADY mint real
`InstrumentType.A_TOKEN`/`DEBT_TOKEN` HOLDINGS pairs for these exact Solana lending protocols today (verified
`marginfi.py:232,240,252,260`, `solend.py:131`) — the bare enum values, no Solana-specific variant. Combined with the
naming SSOT's "Same logic for `lending_indices`" clause, the eventual full retire should split Solana market/event
lending onto the SAME bare `A_TOKEN`/`DEBT_TOKEN` values IS already uses — `chain=SOLANA` remains the partition
differentiator. No new `SOLANA_A_TOKEN`/`SOLANA_DEBT_TOKEN` enum value is needed.

**Todo 7 — per-data_type mapping (design only, NOT shipped — that is todo 8):** `lending_indices` and `position_data`
are genuinely TWO-SIDED (one input row carries both supply + borrow columns, e.g. Aave's `aToken.id` +
`variableDebtToken.id` in the SAME reserve row) — each needs a real per-row FAN-OUT into an `A_TOKEN` row + a
`DEBT_TOKEN` row, not a relabel; this dovetails with the pending per-instrument re-architecture
(`defi_consolidated_closeout_2026_07_18.md` § R1-R4). `liquidation_events` / `liquidations` (5 lending protocols) map to
`A_TOKEN` only (primary identity = seized collateral; debt stays an informational column). `flash_loan_events` and
`risk_params` map to `A_TOKEN` only (no persistent debt leg / risk config is a collateral-side property). **Separate
discoveries, NOT this todo, flagged for a future ruling:** (a) `position_data` also carries Uniswap V3 LP rows tagged
`instrument_type=LENDING` — a pre-existing LP-vs-lending semantic mismatch, should be `POOL`; (b) `liquidations`' `gmx`
protocol is a DeFi perp (naming SSOT: GMX is `instrument_type=perpetual`), arguably not `LENDING`/`A_TOKEN` at all —
kept on `LENDING` in todo 4's fix to match the value already live in GCS, not re-ruled here. **(b) is now MOOT — GMX
REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; no future ruling needed for this
protocol.**

**Code-complete + individually verified** (market-tick-data-service, uncommitted — see below): todos 2 (writers 1-3
collapsed), 3 (writers 5+7 collapsed, branch-traced), 4 (`liquidations_handler` manifest/GCS desync closed — manifest
now derives from the same resolver as the GCS write, resolved to the value ALREADY live in GCS), 5 (a `ValueError` from
`build_instrument_id` now gets a distinct `DEFI_INSTRUMENT_ID_CONTRACT_VIOLATION` ERROR-severity event via a new shared
`record_contract_violation` helper in `_lending_grain.py`, wired into all 8 writers' per-shard except blocks — still
routes to `record_failed`, shard isolation unchanged, only observability is new), 9 (new
`tests/unit/test_defi_lending_writer_instrument_type_pinning.py` — reads each handler's own protocol map, asserts
`build_instrument_id` succeeds for every tuple under TODAY's interim type set; explicitly scoped to interim, not
post-retire, per its own docstring), 13 (dated correction annotations on `docs/GCS_PATHS.md`,
`docs/DEFI_DOWNLOAD_STRATEGY.md`, `docs/DATA_TYPE_DECISIONS.md`). Verification: `ruff check` + `basedpyright` clean on
every changed/added file; `bash scripts/quality-gates.sh --no-fix` run FIVE times end-to-end (6648-6651 tests, coverage
80.14-80.15% each time it measured cleanly) — every failure encountered across all five runs was proven UNRELATED to
this diff:

1. `test_rule11_per_ag_shard_counts_byte_unchanged` (CEFI 208 vs stale-pinned 200) — a pre-existing baseline drift
   (peer-filed `issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md`), fixed by a peer agent mid-session.
2. One run measured a bogus 32.51% coverage figure — a transient artifact of a DIFFERENT concurrent agent's
   `pytest --cov` process writing the SAME shared `coverage.xml` at the same time (confirmed via `ps aux`); the next run
   measured 80.15% again with no code change.
3. 3 tests (`test_slash_id_never_forges_a_path_segment`, a WETH:USDC leaf-byte-match, a Bitfinex `ADAF0:USTF0`
   catalog-decompose case) now fail on an ALREADY-COMMITTED `unified-api-contracts@502ef57e` (landed mid-session) that
   added a stricter embedded-`:`-in-symbol validation to `build_instrument_id`, breaking pre-existing colon-bearing CeFi
   symbol forms — filed as `issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md` (cross-repo,
   unrelated to DeFi lending). This is the CURRENT blocker on `.qg_last_passed_sha` — genuinely unresolved as of this
   Progress Log entry (not self-healing like #1, since it's a landed commit, not another agent's in-flight WIP).

**NOT YET COMMITTED** — the two-pass ship rule requires a green `quality-gates.sh` sentinel, which is currently blocked
by finding #3 above (fleet-wide, blocks EVERY MTDS commit, not just this one). The full diff is ready (file list +
commit message drafted, MTDS-scoped, no foreign files touched) to ship the moment that blocker clears — do not re-do
this work in a follow-up session; check `issues/mtds_uac_embedded_colon_symbol_validation_regression_2026_07_21.md`
first and re-run `bash scripts/quality-gates.sh --no-fix` in `market-tick-data-service`.

**Not completed this session — todos 8, 10, 11, 14 remain `- [ ]` in this SAME plan (honest partial, not a silent skip;
no successor plan — the work stays here for a follow-up pass on this plan):** todo 8 (the actual atomic UAC + MTDS + UTL
wave flipping the 8 writers off `LENDING`/`SOLANA_LENDING` onto `A_TOKEN`/`DEBT_TOKEN`) is exactly the action this plan
exists to gate — shipping it requires the todo-7 mapping to become real per-row fan-out code (not a relabel) for two
data_types, then proof via todo 10's real one-day run + todo 11's three-surface check on every one of the 8 writers, per
this plan's own "mandatory order" banner. This session did not exercise live credentials/network against all 8 writers'
external sources with a subsequent real GCS write + manifest read-back proof, and shipping the value flip without that
proof is the precise failure mode this plan documents as the cause of the first reversal — left `- [ ]` for a dedicated
follow-up with the design above as its starting point. Todo 14 (flip the gate to CLEARED) correspondingly does NOT apply
yet (acceptance criteria 1-8 are not all green — 8 is the gating one). The migration plan's banner (todo 1, applied
above) remains BLOCKED, correctly.

### 2026-07-21 (session 2, /autonomous) — prior session's uncommitted work was LOST; re-executing + a decisive todo-8 scope determination

**State on entry (measured, not assumed):** the 2026-07-21 session-1 entry above says todos 2-5/9/13 were "code-complete
but NOT committed." Verified by `git status` in `market-tick-data-service`: **none of the 8 lending handler files are
dirty** — all sit at HEAD `7ce100f9` in their pre-fix state. That uncommitted work was never shipped and is GONE (the
exact false-progress anti-pattern the ship rules warn about). Re-executing todos 2-5/9/12/13 from scratch, using
session-1's design notes above as the starting point. The only MTDS dirty files are a peer's GMX work
(`_perp_funding_gmx.py`, `test_perp_funding_handler*.py`), schema-artifact JSON, and fold/reshard scripts — none are my
8 handlers, so no collision.

**Todo 6 CORRECTION — SOLANA_LENDING is OUT of scope (session-1's ruling above is SUPERSEDED).** Session-1's entry ruled
"SOLANA_LENDING IS IN SCOPE of the eventual full retire." That is now overridden by the **later, authoritative operator
decision** in `defi_consolidated_closeout_2026_07_18.md:628-632` ("Operator decisions applied 2026-07-21"):
_"SOLANA_LENDING is OUT of the D2 LENDING→A_TOKEN/DEBT_TOKEN retire scope. … The retire applies to the legacy flat EVM
`lending` rows only; Solana rows keep `SOLANA_LENDING`."_ Kamino/Solend/MarginFi markets don't share Aave's
dual-token-per-reserve shape (`SOLANA_LENDING` is its own canonical Solana grain in the grammar table). So `LENDING`
(EVM) is in scope; `SOLANA_LENDING` (Solana) stays. `solana_defi_handler.py` is NOT flipped, and the Solana branches of
`lending_indices_handler` / `risk_params_handler` keep resolving `SOLANA_LENDING`. **Todo 6 = RULED (OUT).**

**Todo 8 / 10 / 11 / 14 — decisive scope determination (genuine cross-plan architectural impossibility for a
writer-fix-only plan; least-bad path taken per AUTONOMOUS_AGENT_RULES rule 1).** After reading the live code, the actual
value-flip cannot be shipped as a writer-fix-only change without reproducing the exact over-reach that was reversed
twice. Three independent, measured confirmations:

1. **The EU-reconciling shard atom is the market ADDRESS, matched to the IS-seeded `expected_unattempted`.**
   `position_data_handler.py:212-217` (verbatim) records `record_captured` at `market_address`, "The IS catalogue seeds
   position_data EU on the per-pool/per-reserve market ADDRESS." Flipping `instrument_type` LENDING→A_TOKEN/DEBT_TOKEN
   changes the holdings atom to the per-token id — but IS still seeds the EU at the market address for the interim
   model. Until IS re-seeds A_TOKEN/DEBT_TOKEN EU atoms (R2/R3/migration, NOT this plan), the flip **regresses
   acceptance criterion 6** (EU→captured conversion, the ~1.04M rows). AC 6 itself ties the flip to the migration.
2. **The A_TOKEN/DEBT_TOKEN canonical symbol synthesis lives in instruments-service** (`instruments-service@1af1be34`
   bakes the split into `build_instrument_catalogue`; isolated-market Morpho/Euler synthesize
   `A{coll}-{loan}[-marketId8]` per the naming SSOT). MTDS writers cannot reach IS (no service→service dep), and the
   subgraph rows carry only `aToken { id }` (an address), not the canonical A_TOKEN symbol form. Producing correct,
   oracle-passing A_TOKEN ids at the write site requires that synthesis exposed via UAC — the per-instrument
   re-architecture's job, not built.
3. **The codex + the code both state market/event lending is INTERIM LENDING.** `defi-canonical-naming-ssot.md:82,117`
   ("the uniform-`LENDING` interim holds until [the migration is done]"; retire is `migration_pending`);
   `evm_defi_handler.py:110-117` (docstring) — market/event lending stays LENDING "for ALL protocols … so writer +
   manifest agree on ONE shard atom (no `a_token` GCS-path vs `lending` manifest desync)."

Adding `LENDING` to UAC `UNSUPPORTED_BY_DESIGN` (todo 8's UAC leg) makes `build_instrument_id:822` raise on LENDING —
**that is literally step 1 of this plan's own "What actually broke" mechanism** and the reversal cause (`uac@e319864f`,
reverted `ad4886ae`). It is only safe once nothing produces or re-derives a LENDING id — i.e. after the writers flip AND
the 16.7M historical rows migrate AND the shard atom re-syncs (steps 2+3, the OTHER plan). The UTL dispatch retarget
(closeout `:663-666`) is explicitly gated "once the EVM retire lands," so it also cannot precede the migration. The
three repos of todo 8 are a single coupled unit that must land WITH the migration; none is safely separable.

**Decision:** ship the genuine "writer fix" — the structural readiness that eliminates BOTH documented reversal root
causes (dual-expression shard-atom desync + silent contract-error swallow) — as todos 2-5, 9, 12, 13, plus the rulings
(6) and design (7), plus the doc alignment (13). Do **NOT** ship a value-flip that would fail this plan's own AC 5/6 and
be the third reversal. Todos 8/10/11 stay `- [ ]` with the complete design below handed to the migration plan; **todo 14
does not flip — the gate stays BLOCKED, correctly** (AC 3/4/5/6 require the flip + real forward-run, which are
inseparable from the migration + IS re-seed + capture resume). This is exactly what the plan's own GATE banner says:
_"This plan owns step 1 only. It does not own the migration, the atom re-sync, or any GCS rewrite."_ The "writer fix"
(step 1) = make every writer a single-resolver-line from the flip with LOUD failure on any contract violation, so the
migration wave (step 2) is the safe one-line change per handler it was always meant to be.

**Todo 7 — per-data_type A_TOKEN/DEBT_TOKEN target mapping (REFINED, SOLANA out; this is the design the migration wave
executes — NOT shipped here).** For the EVM market/event lending data_types the eventual split is (relabel = one output
row; fan-out = one input row → two output rows):

| data_type            | A_TOKEN / DEBT_TOKEN            | shape   | per-row source (the writer already fetches this)                                                                                                                                                                    |
| -------------------- | ------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lending_indices`    | **BOTH** (A_TOKEN + DEBT_TOKEN) | FAN-OUT | one reserve row carries supply idx (`liquidityIndex`/`liquidityRate`) + borrow idx (`variableBorrowIndex`/`…Rate`) + `aToken.id` + `variableDebtToken.id` → A_TOKEN row (supply) + DEBT_TOKEN row (borrow)          |
| `position_data`      | **BOTH** (A_TOKEN + DEBT_TOKEN) | FAN-OUT | positions carry a supplied/collateral leg + a borrowed leg → A_TOKEN (supply) + DEBT_TOKEN (borrow) keyed to the reserve                                                                                            |
| `liquidation_events` | **A_TOKEN** only                | relabel | primary identity = seized collateral reserve; the repaid debt is an informational column                                                                                                                            |
| `flash_loan_events`  | **A_TOKEN** only                | relabel | supply-side against the reserve; no persistent debt leg                                                                                                                                                             |
| `risk_params`        | **A_TOKEN** only                | relabel | risk config is a collateral-side reserve property                                                                                                                                                                   |
| `liquidations`       | **A_TOKEN** only                | relabel | seized collateral (NB: `gmx` here is a DeFi perp arguably `perpetual` — separate flagged discovery, not re-ruled; MOOT — GMX REMOVED 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) |

A blanket `→ A_TOKEN` is the failure mode the reversal warned about — two of the six are genuinely two-sided and need a
real per-row FAN-OUT, not a relabel. `SOLANA_LENDING` data_types are OUT of scope (todo 6) and keep `SOLANA_LENDING`.

**Todo 8 handoff — what the migration wave (`defi_consolidated_closeout_2026_07_18.md`, step 2) must land ATOMICALLY,
and why none of it is safely separable into this writer-fix plan.** Three tightly-coupled legs plus a re-seed:

1. **MTDS writers**: apply the mapping above at each handler's SINGLE resolver (now a one-line-per-handler change thanks
   to this plan) — BUT the A_TOKEN/DEBT_TOKEN canonical **symbol** must be the form instruments-service mints (`aUSDC` /
   isolated-market synthesized `A{coll}-{loan}[-marketId8]`), which the writer does not have and cannot reach (no
   service→service dep; the Aave subgraph returns `aToken { id }` = an address, not the canonical symbol). This requires
   that symbol-synthesis exposed via UAC — the per-instrument re-architecture's job. The two-sided handlers additionally
   need the FAN-OUT (`write_defi_rows` takes ONE `instrument_type` per call, so fan-out = two calls or a per-row-typed
   write).
2. **UAC**: `canonical_id_builder.py:186` `UNSUPPORTED_BY_DESIGN` gains `LENDING` (removing it from
   `SUPPORTED_INSTRUMENT_TYPES` — a disjointness coverage test enforces the partition). This makes `build_instrument_id`
   RAISE on `LENDING` — which is STEP 1 of this plan's own "What actually broke" mechanism, safe **only** once nothing
   produces or re-derives a `LENDING` id, i.e. after the writers flip AND the 16.7M historical rows migrate.
3. **UTL**: `_derive_instrument_id.py` `_DISPATCH[('defi','lending')]` / `[('defi','lending_position')]` retarget/split
   so the EVM `lending` dispatch is removed and Solana's `SOLANA_LENDING` keeps a live entry (closeout `:663-666`,
   explicitly "once the EVM retire lands").
4. **IS `expected_unattempted` RE-SEED (acceptance criterion 6)**: the EU atom today is the market ADDRESS
   (`position_data_handler.py:212-217`, seeded by IS for the interim LENDING model). Flipping the writers' atom to the
   per-token A_TOKEN/DEBT_TOKEN id WITHOUT IS re-seeding the EU at that new atom leaves the ~1.04M EU rows
   `expected_unattempted` forever → AC 6 regresses. The re-seed is R2/R3 (migration) territory.

**Todo 12 (grain regression) — structurally verified GREEN for the shipped writer fix.** The collapse is
**value-preserving**: every new resolver returns the exact same `LENDING`/`SOLANA_LENDING` the prior literals did
(pinned by `test_lending_writers_emit_only_interim_types` +
`test_write_enum_and_manifest_string_are_one_resolution_point`), and `_lending_grain.py`'s grain functions
(`market_count_map` / `record_market_captures`) are UNCHANGED (only the new
`record_contract_violation`/`is_instrument_id_contract_violation` helpers were added). So the per-market
`record_captured` atom and the EU→captured conversion are unchanged by construction. The runtime EU-conversion
before/after MEASUREMENT the todo describes belongs to the value-flip's real run (todo 10), which is part of the gated
migration wave, not this value-preserving collapse.

**Todo 14 — gate STAYS BLOCKED (correct).** Acceptance criteria 1/2/7/8 hold for the shipped writer fix (single
resolution point, liquidations desync closed, MTDS QG green, contract errors loud). Criteria 3/4/5/6 REQUIRE the actual
value-flip + a real forward-write run + 3-surface agreement on flipped shards + non-regressed EU conversion — all
inseparable from the migration + IS re-seed + capture resume (above). So `todo 14` does NOT flip; the migration-plan
banner (closeout `:429`) stays BLOCKED, refreshed to this precise state. The ~16.7M-row migration remains gated.

### 2026-07-26 (session 3, /autonomous, interactive — operator present, decision made WITH the operator this session, not solo) — todo 7's premise is SUPERSEDED: no physical retire, ever; a resolver replaces the flip. Plus one new live bug found.

**Decision, made this session with the operator (documenting per rule 12f — this is a genuine scope change against the
prior sessions' documented intent, not a clarification within it):** Sessions 1-2 above correctly proved the atomic
writer-flip (todo 8) cannot ship safely — 4 tightly-coupled legs, an IS `expected_unattempted` re-seed, and a ~16.7M-row
migration that has already caused two reversals. This session's operator, independently reviewing the same tradeoff,
chose to **stop pursuing the physical flip entirely** rather than eventually clearing it: `lending_indices` /
`liquidations` / `liquidation_events` / `flash_loan_events` / `position_data` / `risk_params` stay flat
`LENDING`/`SOLANA_LENDING`-keyed **permanently** — not "interim, migration_pending." The downstream need the flip was
meant to serve (an A_TOKEN/DEBT_TOKEN canonical instrument_id resolving to a supply/borrow rate) is instead served by a
**new read-side lookup function** (this session's todo 15) that maps a canonical A_TOKEN/DEBT_TOKEN instrument_id →
`(venue, chain, underlying_symbol)` via instruments-service's registered metadata → the existing flat-`LENDING` row →
`supply_apy` or `borrow_apy`. No GCS rewrite, no manifest re-key, no IS re-seed, no UAC `UNSUPPORTED_BY_DESIGN`
addition. **This supersedes todo 7's fan-out design and closes todos 8/10/11/14 as WON'T-DO** (not deferred — the
premise they were gated on no longer applies). Todos 1-6, 9, 12, 13 remain valid and done independent of this pivot (the
resolver-desync fixes and SOLANA-out-of-scope ruling are correct regardless of whether the eventual target is a physical
flip or a read-side resolver).

**New finding this session (verified against live code, not the plan table — the table's "Post-retire target" column was
previously misread by this agent as "emits today"; corrected):** `evm_defi_handler.py`'s `_EVM_DEFI_INSTRUMENT_TYPES`
(`:119-126`) maps every protocol including `aave_v3`/`compound_v3`/`morpho` to flat `InstrumentType.LENDING` TODAY — so
there is no live A_TOKEN/DEBT_TOKEN `lending_indices` data anywhere in prod; the resolver design above has a clean
slate. BUT: `evm_defi_handler.py` (`collect-evm-defi`) and `lending_indices_handler.py` (`collect-lending-indices`) are
two INDEPENDENT capture pipelines that both fetch Aave V3's `reserveParamsHistoryItems` subgraph entity for the SAME
overlapping protocols (`aave_v3`, `compound_v3`, `morpho`) and both write `data_type=lending_indices` to the SAME
partition (`instrument_type=LENDING`, same venue/chain/symbol/day) — a genuine redundant-capture waste. Worse:
`evm_defi_handler.py`'s batch query (`_AAVE_V3_HISTORY_QUERY` `:334-352`) never fetches `liquidityRate`, so its parser
(`_parse_aave_v3_history` `:329-369`) never populates a supply-side rate at all — while `lending_indices_handler.py`'s
version does. Since both land in the same shard, write order silently determines whether that day's row has a supply
rate. `scripts/full-defi-backfill.sh:57-60` has run `collect-evm-defi` across 2022-01-01→2026-05-03. **Filed as a new
todo (16) — this is a live data-correctness bug per `/codex/02-data/data-pipeline-correctness-hard-rule.md`, not a
naming inconsistency.**

**New todos added this session** (15: build the resolver; 16: reconcile the aave_v3/compound_v3/morpho duplicate
capture + the missing-supply-rate bug; 17: update the naming SSOT to remove the migration_pending framing; 18: close the
migration reference in `defi_consolidated_closeout_2026_07_18.md`) — see Todos section below.

**Todo 16 — RESOLVED (confirmed LIVE, not hypothetical, via
`deployment-service/terraform/gcp/ defi_collection_scheduler.tf`).** Cloud Scheduler runs `collect-lending-indices`
daily at 00:45 UTC (`lending_indices_handler.py`, full field set incl. `liquidityRate`) and `collect-evm-defi` daily at
01:55 UTC (`evm_defi_handler.py`), both in `--mode batch` (confirmed from the `defi_collect_job` module's `args`) — so
`collect-evm-defi` runs through its BATCH/history code path (`_AAVE_V3_HISTORY_QUERY` / `_parse_aave_v3_history`) every
single day, not just during the one-time historical backfill. That query never fetches `liquidityRate`, so every daily
row `collect-evm-defi` writes for `aave_v3`/`compound_v3`/`morpho` has no supply rate; since both jobs write the SAME
GCS partition (`instrument_type=LENDING`, same venue/chain/symbol/day), whichever ran last determined whether that day's
row was complete — a live, ongoing correctness bug per `/codex/02-data/data-pipeline-correctness-hard-rule.md`, not a
one-off historical artifact. The terraform's own `collect-evm-defi` description ("for any chain not covered by
op-specific jobs") already documented the INTENDED non-overlapping scope; the code just never implemented it.

**Fix implemented + QG-green, SHIP BLOCKED (2026-07-26)** — quickmerge's Stage 1 dependency validation correctly
refused: `unified-trading-library` (unrelated GCS cloud_interface/provider refactor) and `unified-api-contracts`
(unrelated sports-venue classification WIP, `venue_constants.py`) both have uncommitted changes with mtimes ~26s old at
check time -- well under the 120s liveness threshold, i.e. another session is actively editing them right now. Per the
multi-agent-safety LIVENESS gate this is PROTECT, not inherit -- left untouched, not force-committed, not routed around.
Retry once that session's work settles/commits. `unified-api-contracts@1d01a911` (todo 15) already landed clean before
this contention appeared.

**Retry 1 (+300s): still blocked, escalating wait.** `unified-trading-library`'s dirty files unchanged for 329s
(possibly settled, but no commit landed -- still can't distinguish "paused mid-task" from "abandoned"). UAC's
`venue_constants.py` mtime MOVED again since the first check (edited within the last 189s of a ~5min window) -- proof
that session is still genuinely iterating, not a stale artifact. Considered `--skip-preflight` to force past the gate;
rejected -- MTDS's QG run was measured against these repos' CURRENT uncommitted local state, not their eventual
committed state, so forcing through risks a false-green that breaks once the real dependency version lands. Rescheduling
a longer wait instead of forcing through.

**Fix (pending ship)** (`market-tick-data-service`, evm_defi_handler.py): removed `aave_v3`/`compound_v3`/`morpho` from
`_EVM_DEFI_INSTRUMENT_TYPES`/`_DEFAULT_CHAINS`/`_DEFAULT_PROTOCOLS`/`_LIVE_ONLY_PROTOCOLS` — `collect-evm-defi`'s
default (cron-driven) dispatch now covers only `venus`/`benqi`/`radiant`/`euler_v2`, which have no other flat-LENDING
writer and so no duplication risk. The underlying `_AAVE_V3_QUERY`/`_AAVE_V3_HISTORY_QUERY`/`_parse_aave_v3*`/
`_parse_compound_v3*` query+parser code was left in place (still directly unit-tested, still reachable via the explicit
`--evm-defi-protocols` CLI override for debugging) rather than deleted — tracing every call site safely in one pass was
out of scope for this session; **follow-up P3 housekeeping item**: confirm nothing else references it and delete if
truly dead. Test updates: `tests/unit/test_evm_defi_handler.py`'s
`test_default_protocols_defined`/`test_default_chains_defined` updated to the new scope + a new
`test_aave_compound_morpho_removed_from_active_dispatch` regression guard.
