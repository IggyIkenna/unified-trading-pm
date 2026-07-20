---
doc_type: plan
title: DeFi lending writer fix — HARD PREREQUISITE for the D2 flat-LENDING retire
summary:
  Fix the MTDS market/event lending writers that broke into `attempted_failed`/zero-data when the flat-`LENDING` →
  `A_TOKEN`/`DEBT_TOKEN` retire was first attempted, and close the shard-atom desync (GCS `instrument_type=a_token` vs
  manifest `lending`) that the partial work-around introduced. This plan is the UPSTREAM gate on the operator's D2
  ruling — the ~16.7M-row migration MUST NOT START until this plan is green. Omitting exactly this step is what caused
  the first attempt to be reversed.
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
    data_pipeline_reconciliation_skill_2026_07_20.md,
    defi_consolidated_closeout_2026_07_18.md,
    issues/canonical_closeout_open_questions_2026_07_18.md,
    ../../codex/02-data/defi-canonical-naming-ssot.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
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

# DeFi lending writer fix — HARD PREREQUISITE for the D2 flat-`LENDING` retire

> **⛔ GATE — READ FIRST.** The operator's **D2** ruling (2026-07-20) is to complete the FULL flat-`LENDING` retire to
> `A_TOKEN`/`DEBT_TOKEN`. That migration (~16.7M manifest rows) **MUST NOT START until this plan is green.** The retire
> was attempted once and **reversed** — the reversal cause was not the target model, it was executing the migration
> without first fixing the writers. Re-executing in the same order reproduces the same outage.
>
> Mandatory order — **all three steps, in this sequence**:
>
> 1. **Fix the writers** (THIS PLAN) and prove them green on a real run.
> 2. **Migrate the ~16.7M rows** (owned by `defi_consolidated_closeout_2026_07_18.md`, not this plan).
> 3. **Re-sync the shard atom** across GCS · manifest · data-status · UI (owned by the migration plan).
>
> **This plan owns step 1 only.** It does not own the migration, the atom re-sync, or any GCS rewrite.
>
> **Ruling authority**: `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` §"OPERATOR DECISIONS — ALL THREE
> RULED 2026-07-20" (D2 + its "D2 consequences" block). **Codex SSOTs** (referenced, never duplicated here):
> `codex/02-data/defi-canonical-naming-ssot.md` (the two-layer lending model + the interim banner) ·
> `codex/02-data/availability-manifest-and-data-status.md` (shard atom, 4-state `capture_status`) ·
> `codex/04-architecture/shard-level-failure-isolation.md` (per-shard `except` discipline).

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

- [ ] 1. [DATA] P0. **Assert the gate in the migration's own plan.** Add a dated banner to
      `plans/active/defi_consolidated_closeout_2026_07_18.md`'s "Retire legacy `LENDING` → A_TOKEN/DEBT_TOKEN" todo
      (`:426`) stating the migration is BLOCKED on this plan and naming this file. Do **not** restate the mechanism
      there — link it. This exists so a worker reading the migration todo cold cannot start step 2 first, which is
      precisely what happened the first time.
- [ ] 2. [CODE] P0. **Collapse writers 1, 2, 3 to a single resolution point.** `liquidation_events_handler.py` (`:306`
      enum vs `:54-57`/`:330` strings), `flash_loan_events_handler.py` (`:176` vs `:147`/`:201`),
      `position_data_handler.py` (`:198` vs `:225`). One resolver per handler returning the `InstrumentType`; the
      manifest site derives its string from that same value. Mirror `evm_defi_handler.py:130-139` exactly, including its
      docstring rationale. No behaviour change yet — the emitted value stays `LENDING` in this todo.
- [ ] 3. [CODE] P0. **Collapse writers 5 and 7.** `lending_indices_handler.py` `:863` hardcoded enum vs
      `:674`/`:182-184` resolver; `risk_params_handler.py` `:121-123` enum resolver vs `:116-118` str resolver. One
      resolver each, str derived from the enum. Keep the EVM-vs-Solana branch distinction intact (`:430` must still
      resolve `SOLANA_LENDING`) — verify by reading which branch each protocol in `_DEFAULT_PROTOCOLS` `:172` actually
      reaches before collapsing, do not assume.
- [ ] 4. [CODE] P0. **Fix the live `liquidations_handler` desync** — `:534` manifest `"liquidation"` vs `:644` GCS
      `LENDING`. Decide which is correct against `codex/02-data/defi-canonical-naming-ssot.md` (the naming SSOT is the
      authority, not either literal), fix both surfaces onto one resolver, and record whether already-written rows need
      a re-key as a todo in the migration plan (this plan does not own the data fix).
- [ ] 5. [CODE] P0. **Make the contract error loud.** On every lending write path, a `ValueError` originating from
      `build_instrument_id` must NOT be swallowed into `record_failed` as if it were a venue/network failure — classify
      it distinctly per `codex/04-architecture/shard-level-failure-isolation.md` and UAC `classify_venue_error()`.
      Verified swallow site to start from: `flash_loan_events_handler.py:214-223`. This is the change that would have
      made the first attempt fail loudly in minutes instead of silently producing `attempted_failed` rows.
- [ ] 6. [CODE] P0. **Rule the `SOLANA_LENDING` scope question and record the answer in this plan.** D2 names flat
      `LENDING`; `solana_defi_handler.py:321-332`, `lending_indices_handler.py:175-179` and
      `risk_params_handler.py:110-112` emit `SOLANA_LENDING` for `kamino_lending`/`marginfi`/`solend`. Either it splits
      to `A_TOKEN`/`DEBT_TOKEN` alongside EVM, or it is explicitly OUT of scope with a stated reason. Leaving it
      undecided reproduces the "interim that nobody ruled" state that produced this whole contradiction. Escalate as an
      option-set if it is not decidable from the naming SSOT.
- [ ] 7. [CODE] P0. **Define the per-data_type target mapping** — for each of `lending_indices`, `liquidation_events`,
      `flash_loan_events`, `position_data`, `risk_params`, `liquidations`, state which of `A_TOKEN`/`DEBT_TOKEN` each
      row resolves to and from which row column. The reversal's own diagnosis was that these are "DIVERSE data_types
      with no clean single A_TOKEN mapping" (`defi_consolidated_closeout_2026_07_18.md:1494-1495`) — so this mapping is
      the genuine design work, and a blanket `→ A_TOKEN` is the failure mode to avoid. Two-sided data_types
      (`position_data`) need both legs.
- [ ] 8. [CODE] P0. **Ship the retire atomically across all three repos in ONE wave** — UAC
      (`canonical_id_builder.py:186` `UNSUPPORTED_BY_DESIGN` gains `LENDING`), MTDS (all 8 writers on their new
      mapping), UTL (`_derive_instrument_id.py:76-77` `_DISPATCH[('defi','lending')]`/`[('defi','lending_position')]`,
      the third consumer identified at `defi_consolidated_closeout_2026_07_18.md:693-699`). The documented META-LESSON
      of the reversal is that a partial wave IS the outage; do not land UAC ahead of MTDS.
- [ ] 9. [TEST] P0. **Enumerate-from-source pinning tests.** A test that reads each handler's own protocol→type map and
      asserts `build_instrument_id` succeeds for every producible tuple, plus a test asserting GCS-path segment ==
      parquet column == manifest row `instrument_type` for a representative shard per writer. Enumerating from the
      handlers' maps (not a hand-written list) is what makes this survive the next protocol addition.
- [ ] 10. [DATA] P0. **Runtime green proof — run it, don't read it.** Execute a real one-day run for each of the 8
      writers and verify from the MANIFEST that each recorded `captured` with non-zero rows and **zero
      `attempted_failed`**. Cite the day, the venue/chain shards touched, and the measured row counts. A handler return
      value is not evidence; the manifest is.
- [ ] 11. [DATA] P0. **Three-surface agreement check** on the shards produced by todo 10 — GCS object path segment ·
      parquet content column · manifest row, at the shard atom. Any disagreement is a hard fail of this plan, not a
      follow-up.
- [ ] 12. [DATA] P1. **Grain regression check** — confirm the type change did not disturb the per-market
      `record_captured` grain that converts `expected_unattempted` (`_lending_grain.py:1-19`, `:84-119`). Compare
      EU→captured conversion counts for the run day before and after.
- [ ] 13. [DOCS] P1. **Align the MTDS docs to what shipped** — `docs/GCS_PATHS.md`, `docs/DEFI_DOWNLOAD_STRATEGY.md`,
      `docs/DATA_TYPE_DECISIONS.md` all carry the interim `instrument_type=lending` statement (shipped
      `market-tick-data-service@e9764b38`). Update them in the SAME wave as todo 8, with a dated correction annotation,
      not a silent overwrite.
- [ ] 14. [PM] P1. **Flip the gate and hand off.** When acceptance criteria 1-8 all hold, record the evidence here, flip
      the todo-1 banner in the migration plan from BLOCKED to CLEARED with the commit SHAs, and notify the operator that
      step 2 (the ~16.7M-row migration) may begin. Do not start step 2 from this plan.

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
</content>

</invoke>
