---
doc_type: plan
title: InstrumentRecord schema-completeness + extra='forbid' — stop silently dropping adapter kwargs
summary:
  Operator ruled 2026-07-18 to close the InstrumentRecord silent-drop class properly (not a minimal remove).
  InstrumentRecord uses pydantic's default extra='ignore', so any kwarg an adapter passes that the model does not
  declare is silently DROPPED (that is how the prediction title was lost before A4 added `question`). Measurement (flip
  extra='forbid' + run IS adapter tests) surfaced ~4 systemic undeclared kwargs across ~30 adapters — symbol /
  min_order_size / is_active / updated_at (+ more candidates from a static scan). This plan gets the authoritative list,
  decides per-field add-to-schema vs remove-from-caller, applies it, and flips extra='forbid' so future drops fail LOUD.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [uac-contract, instrument-record, pydantic, schema-completeness, honest-absence, silent-drop]
related:
  [
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-18
last_updated: 2026-07-18
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  "data_status_page_ux_and_canonicalisation_2026_07_16.md P3 InstrumentRecord side-discovery (operator ruling
  2026-07-18: schema-completeness, not minimal-remove)"
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-api-contracts/unified_api_contracts/internal/reference/instrument.py,
    /plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md,
  ]
supersedes:
superseded_by:
---

# InstrumentRecord schema-completeness + extra='forbid'

**Operator ruling (2026-07-18):** do the schema-completeness version — decide per-field whether each silently-dropped
kwarg SHOULD be captured (add to `InstrumentRecord` + the parquet schema) or removed from the caller — then flip
`extra='forbid'`. NOT the minimal behaviour-preserving remove.

## Context

`unified_api_contracts/internal/reference/instrument.py::InstrumentRecord` uses pydantic's default `extra='ignore'`. A
kwarg a caller believes it is persisting but that the model does not declare is a lie-by-omission (same honest-absence
class as a fabricated value) — it vanishes with no error, no log, no test failure. The concrete instance already fixed:
the prediction adapters passed `symbol=str(title)[:100]` which was dropped, so the catalogue label fell back to the raw
slug — A4 added the `question` field + the adapters now populate it (kalshi.py / polymarket parsing.py), and the old
`symbol=` consumer was removed there.

**Measured blast radius (2026-07-18, flip `extra='forbid'` + run IS adapter tests):** the model currently drops, at
minimum, these systemic kwargs (partial run — todo 1 gets the authoritative complete list):

| dropped kwarg    | seen in adapters                                  | likely disposition (todo 2 confirms)                                  |
| ---------------- | ------------------------------------------------- | --------------------------------------------------------------------- |
| `symbol`         | betfair, ibkr, renzo, solend (+ prediction fixed) | display/exchange symbol — likely REMOVE (raw_symbol covers it) or map |
| `min_order_size` | betfair, kalshi, polymarket parsing               | DISTINCT from declared `min_size` — decide ADD-field vs remove        |
| `is_active`      | betfair, kalshi, polymarket parsing               | overlaps declared `status` (InstrumentStatus) — likely map to status  |
| `updated_at`     | betfair, kalshi, polymarket parsing               | metadata timestamp — decide ADD-field vs remove                       |

A static scan flagged further candidates in defi/deribit adapters (`spot_asset`, `debt_symbol`, `onchain_symbol`,
`contract_address`, `decimals`, `borrow_symbol`, `capability`, …) — some may be false positives from greedy parsing; the
authoritative list comes from the full-suite `extra='forbid'` run (todo 1).

## Codex SSOTs (read before touching)

- `/codex/02-data/honest-absence-downstream-handling.md` — a dropped field a caller believed persisted is
  honest-absence.
- `/codex/02-data/availability-manifest-and-data-status.md` — INSTRUMENTS_PARQUET_SCHEMA alignment (adding a field is a
  parquet-column change; the InstrumentRecord docstring documents the 1:1 model↔column contract).
- `unified_api_contracts/internal/reference/instrument.py` — the model + `INSTRUMENTS_PARQUET_SCHEMA`.

## Todos

- [x] ✅ [DATA] P1. **Get the AUTHORITATIVE list** — flip `model_config = ConfigDict(extra="forbid")` on a branch and
      run the FULL UAC + IS suites (not a -k subset); collect every `extra_forbidden` field name + the adapter/call-site
      that passes it. This is the foundation gate (my measurement was a subset). — **DONE** (via
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`, 2026-07-28, slot-6): flipped `extra='forbid'` on a
      local scratch branch, ran the FULL UAC + instruments-service `quality-gates.sh` suites, AST-parsed every
      `InstrumentRecord(...)` call site. Authoritative complete list: `symbol`, `is_active`, `updated_at`,
      `min_order_size`, plus two newly-surfaced fields the partial measurement missed — `asset_group`, `lot_size`. See
      that plan's Progress Log for the full method + evidence.
- [x] ✅ [DATA] P1. **Per-field disposition table — the bias is REMOVE, ADD is the exception.** These kwargs are
      currently DUMPED across the board by the adapters and READ BY NOTHING (that silent no-op is why they went
      unnoticed). So for each dropped kwarg apply a three-part test (operator 2026-07-18) and ADD to the schema ONLY if
      all three hold, else REMOVE from the caller: 1. **Code usage** — grep for a real CONSUMER: does any code path
      (features/ml/strategy/UI/download) actually read this field off the record/parquet, or would a concrete consumer
      want it? "An adapter passes it" is NOT usage. 2. **Business reason** — is there a plausible trading/reference-data
      reason to persist it (does it carry decision value), vs incidental adapter scratch state. 3. **Doesn't already
      exist** — no declared field already carries the same information. Record the verdict + evidence per field.
      Anchors: `is_active`→already `status` (REMOVE/map); `symbol`→already `raw_symbol` (likely REMOVE);
      `min_order_size` vs `min_size` (distinct? only ADD if a consumer needs the order minimum separately); `updated_at`
      (a consumer of capture-provenance? else REMOVE). — **DONE** (batch1, 2026-07-28, slot-6): verdicts —
      `symbol`→REMOVE (zero usage, `raw_symbol` covers it); `is_active`→REMOVE (zero usage, `MarketLifecycle` is the
      real lifecycle signal); `updated_at`→REMOVE (zero usage); `lot_size`→REMOVE (test-fixture-only, zero production
      usage); `asset_group`→**RENAME to `asset_class`** (bug-fix — an already-declared field was being silently missed
      under the wrong kwarg name across 6 TradFi/Databento/IBKR call sites, defaulting `asset_class` to CRYPTO
      regardless of real class); `min_order_size`→**LEFT AMBIGUOUS** (operator-judgment flag stands, distinct from
      `min_size`, execution-sizing use unclear — not yet resolved).
- [x] [DATA] P1. **ADD the kept fields** — declare them on `InstrumentRecord` + align `INSTRUMENTS_PARQUET_SCHEMA` (1:1
      model↔column contract); additive + optional (non-breaking added-optional-field), so existing rows/validators are
      unaffected. UAC unit test per added field. — ✅ 2026-08-20: **N/A, confirmed final** — `min_order_size` (the
      one field left ambiguous) resolved to REMOVE, not ADD (see todo 2's update below), so no field's verdict is
      ADD. This todo needs no further action.
- [x] [DATA] P1. **FIX the callers** — for REMOVE fields, drop the undeclared kwarg from each adapter; for ADD fields,
      point the adapter at the new declared field. Cover every call site the todo-1 run surfaced. — **DONE**
      (batch1, `instruments-service@ee2d6c75`): dropped `symbol`/`is_active`/`updated_at`/`lot_size`
      from all 9 production + test-fixture call sites; renamed `asset_group`→`asset_class` at all 6 real sites (a
      correctness fix, not cosmetic) + opportunistically fixed `ibkr.py::_build_instrument_from_uac`'s missing
      `raw_symbol=`. instruments-service `quality-gates.sh --no-fix` ALL PASSED (4988 passed / 0 failed).
      ✅ 2026-08-20 (T2 tranche, `/autonomous`) — **`min_order_size` resolved + fixed, todo now fully closed.**
      Applied the operator's own three-part test with a concrete code check (grep, not assumption): zero
      consumers of `min_order_size`/`minimum_order_size` anywhere across execution-service, strategy-service,
      risk-and-exposure-service, or unified-trading-library — the one plausible consumer named in the 2026-07-18
      ambiguity note ("execution sizing could legitimately want it") does not exist. Verdict: REMOVE, matching
      every other field's disposition. Dropped `min_order_size=` (and the now-dead intermediate `min_order`
      variable) from all 5 call sites: `polymarket/parsing.py`, `kalshi.py`, `betfair.py` (production adapters) +
      `test_base_adapter.py` (2 test fixtures); corrected a stale docstring in
      `test_prediction_adapters_comprehensive.py`. 421 adapter tests + full `quality-gates.sh` green. Evidence:
      `instruments-service@588f35aeb0`.
- [ ] [DATA] P1. **Flip `extra='forbid'`** — add `model_config = ConfigDict(extra="forbid")`; UAC + IS suites green
      (proves no remaining undeclared-kwarg caller). Add a UAC test asserting an unknown kwarg now RAISES.
      **Filed to T1 2026-08-20** — `InstrumentRecord` lives in `unified-api-contracts/unified_api_contracts/internal/
      reference/instrument.py`, outside this tranche's 3 owned repos (instruments-service, market-tick-data-service,
      market-data-processing-service). Every REMOVE-verdict caller is now clean (todo above, fully done) — the flip
      itself is unblocked and ready whenever T1 picks it up. See
      `/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md`'s `## Inbound requests`.
- [ ] [REVIEW] P2. **Post-phase codex audit** — note the extra='forbid' contract + any new fields in
      `honest-absence-downstream-handling.md` + the InstrumentRecord docstring; confirm no plan↔codex drift.

## Progress Log

- **2026-07-18** — Authored after the operator chose schema-completeness (not minimal-remove) for the InstrumentRecord
  silent-drop hardening. Human plan (operator-driven). The concrete prediction-title data-loss is ALREADY fixed (A4
  `question=`); this plan closes the systemic class + makes the contract fail-loud.

- **2026-07-18 (autonomous) — TODO-2 disposition PRE-ANALYSIS for the 4 confirmed kwargs** (applying the operator's
  code-usage + business-reason + not-already-exists test; read-only, no code shipped). Confirmed on real code: NONE of
  `is_active`/`updated_at`/`min_order_size`/`symbol` are in `INSTRUMENTS_PARQUET_SCHEMA` (so they are never persisted →
  no downstream reader can consume them — code-usage = ZERO by construction), and a workspace grep for `.is_active`
  attribute reads found only unrelated account/client/subscription domain objects (their OWN `is_active`), never an
  instrument record. Pre-verdicts:
  - **`is_active` → REMOVE** — zero usage + already covered by the declared `status` (InstrumentStatus ACTIVE/DELISTED).
  - **`symbol` → REMOVE** — zero usage + already covered by the declared `raw_symbol`.
  - **`updated_at` → REMOVE** — zero usage; a per-capture metadata timestamp with no consumer + no business reason.
  - **`min_order_size` → OPERATOR JUDGMENT** — zero usage today, BUT semantically distinct from the declared `min_size`
    (minimum instrument/lot size) — it is the minimum ORDER size, which execution sizing could legitimately want. ADD
    (as an additive optional field + parquet column) only if execution needs the order-minimum; else REMOVE. This is the
    one field where the business-reason test is not obviously "no". TODO-1's full-suite `extra='forbid'` run still owns
    the AUTHORITATIVE complete list (the static scan flagged further defi/deribit candidates —
    `spot_asset`/`debt_symbol`/`onchain_symbol`/etc. — to be confirmed real-vs-parse-artifact and dispositioned the same
    way).

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the per-field disposition todo carries an explicit OPERATOR
  JUDGMENT field (`min_order_size`: ADD only if execution needs the order-minimum) that gates the ADD/REMOVE pass.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (4 entries), still minimal and accurate.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — re-confirms 2026-07-30; all 4 open todos are sequentially gated
  behind todo 2's still-open operator-judgment verdict on `min_order_size` (explicitly flagged ambiguous, not yet
  resolved).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate. No content change since
  the last pass beyond the context-scout re-scout.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-04 (unchanged): all 4 open todos remain
  sequentially gated behind todo 2's still-unresolved operator-judgment verdict on `min_order_size` disposition.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (4 entries).
