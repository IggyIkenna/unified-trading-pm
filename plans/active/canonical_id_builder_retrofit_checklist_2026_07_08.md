---
doc_type: plan
title:
  Retrofit checklist — route every remaining ad hoc instrument_id/leg construction through the new shared
  build_canonical_instrument_id / build_leg builder
summary: >-
  The operator-decided one-builder architecture (instrument_id_format_canonicalization_2026_07_08.md — "one builder for
  everything... every asset group, every instrument type, can get its canonical instrument IDs, same with fixtures, just
  by filling in the right inputs") now has a real implementation: unified-api-contracts' canonical_id_builder.py gained
  build_canonical_instrument_id() (one entry point, dispatches CeFi/DeFi/TradFi/ Prediction to build_instrument_id and
  Sports to the fixture-id domain builder), build_leg() (shared InstrumentLeg construction), and passthrough=True on
  build_instrument_id() (raw exchange-native id wrapping, closing the gap that made the CCXT live-mode fix deliberately
  not route through this module). One real call site (deribit_options_adapter.py) was retrofitted as proof; ~48+ DeFi
  adapters, 5 on-chain-perp adapters, the Deribit combo-leg builder, both Prediction adapters, and 1 sports adapter
  still build instrument_key ad hoc. This plan enumerates that full remaining retrofit, with real file:line pointers
  gathered 2026-07-08.
status: active
nature: notes
asset_group: [cefi, defi, prediction, sports]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [instrument-id, canonicalization, instrument-identity, builder-retrofit, refactor]
related:
  [
    ../issues/instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md,
    ../canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    ../../audit/results/canonical_instrument_id_audit_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Sub-agent task (2026-07-08), implementing the operator's one-builder decision recorded in
  instrument_id_format_canonicalization_2026_07_08.md. Filed per that task's instruction to track the FULL remaining
  retrofit as its own plan rather than attempt it all in one pass — the core builder + a couple of proof retrofits +
  this checklist was the scoped deliverable for that round."
---

> **What already shipped (2026-07-08, this session)** — read before starting any todo below, it's the infrastructure
> every todo here builds on:
>
> - `unified_api_contracts.build_canonical_instrument_id(asset_group, venue, instrument_type, **kwargs)` — one entry
>   point, dispatches CEFI/DEFI/TRADFI/PREDICTION to `build_instrument_id()`, SPORTS to the fixture-id domain builder
>   (`canonical/domain/sports/canonical_ids.build_fixture_id`, producing `LEAGUE:MATCHUP:DATE` — NOT
>   `VENUE:TYPE:SYMBOL`, by design).
> - `build_instrument_id(..., passthrough=True)` — wraps an already-fully-formed raw/native symbol verbatim as
>   `VENUE[-CHAIN]:TYPE:SYMBOL` (DeFi preserves on-chain case) instead of reconstructing from expiry/strike/right. This
>   is the escape hatch the CCXT live-mode fix needed but didn't have (see
>   `canonical_id_p0_ccxt_live_batch_divergence_2026_07_08.md`'s Progress Log).
> - `build_leg(venue, instrument_type, symbol, *, side, ratio=1, ...)` — builds one
>   `unified_api_contracts.internal.InstrumentLeg` via the shared builder instead of an ad hoc f-string.
> - Proof retrofit: `instruments-service/instruments_service/reference_data/adapters/cefi/deribit_options_adapter.py`
>   now calls `build_instrument_id(..., passthrough=True)` for its OPTION `instrument_key` (behavior-preserving,
>   verified against `tests/unit/test_deribit_options_adapter.py`).
> - Compatibility proof (not a live retrofit):
>   `unified-api-contracts/tests/internal/unit/test_canonical_id_builder.py ::TestCcxtTardisCompatibility` shows the
>   shared builder reproduces the real, already-shipped CCXT/Tardis per-venue ids for all sample venues in the CCXT
>   plan's table — `ccxt_adapter.py` itself was NOT touched this round (see todo 9 below for the open refactor
>   question).

## Todos

- [ ] [DATA] P1. **Retrofit the ~48 DeFi adapters that build `instrument_key` as an ad hoc f-string** to
      `build_canonical_instrument_id(AssetGroup.DEFI, venue_tag_parts, InstrumentType.X, symbol, chain=...)` (or
      `passthrough=True` where the symbol is already the final on-chain form). Representative real file:line hits (grep
      for `instrument_key\s*=\s*f["']` under `instruments_service/reference_data/adapters/defi/*.py` for the full
      48-file list): `aave_v3.py:424,433` (A_TOKEN/DEBT_TOKEN), `balancer.py:226` (POOL), `curve.py:164` (POOL),
      `benqi.py:98` / `euler_v2.py:93` / `fluid.py:113` (LENDING_MARKET), `morpho.py:195` (LENDING_MARKET),
      `compound_v3.py:263,272` (SUPPLY/BORROW), `ethena.py:67` (YIELD_BEARING), `etherfi.py:83` / `kelpdao.py:87` (LST),
      `jito.py:126,148` (STAKING), `convex.py:98` / `beefy.py:260` / `idle.py:127` / `karak.py:117` /
      `jito_restaking.py:141` (VAULT), `eigenlayer.py:98` / `ethfi.py:92` (GOVERNANCE_TOKEN), `drift.py:253,291`
      (PERP/SPOT), `flash_trade.py:159` (PERP), `jupiter.py:174` (SPOT). Do NOT start this todo until todo 2 below is
      resolved — several of these TYPE tokens aren't real `InstrumentType` enum values yet.
- [ ] [DATA] P1. **Resolve the non-canonical TYPE-token question before retrofitting todo 1** — `VAULT`, `SUPPLY`,
      `BORROW`, `LENDING_MARKET`, `GOVERNANCE_TOKEN`, `SPOT`, `PERP` all appear as the middle segment of a real DeFi
      adapter's `instrument_key` (see file:line list in todo 1), but **none of these strings are real `InstrumentType`
      enum values** (the real enum has `LENDING`, `A_TOKEN`, `DEBT_TOKEN`, `STAKING`, `YIELD_BEARING`, `LST`, `POOL`,
      `DEX_POOL`, `SPOT_ASSET`, `PERPETUAL` — see `_instrument_enums.py`). This is the same bug CLASS as the
      already-fixed P0 "23 DeFi adapters silently return empty on canonical-form type filters" finding
      (`canonical_id_p0_defi_adapter_type_filter_bug_2026_07_08.md`) — confirm whether these 7 additional tokens are
      ALSO silently dropped by any canonical-form type filter downstream (same mechanism, different tokens), or whether
      they're intentionally distinct sub-types that need new `InstrumentType` enum members before
      `build_canonical_instrument_id` can represent them at all. Do not blindly map them onto an existing enum value
      without checking whether the distinction (e.g. SUPPLY vs BORROW within Compound V3) is load-bearing downstream.
- [ ] [DATA] P2. **VERIFY `morpho.py:195`'s real current code against finding 6** — the canonicalization issue doc's
      finding 6 describes a real 3rd-colon-inside-symbol bug (`MORPHO-BASE:LENDING_MARKET:USDC-EURC:0x305dd1`), but the
      CURRENT adapter code at `morpho.py:195` reads
      `instrument_key = f"{venue_tag}:LENDING_MARKET:{symbol}-{market_key[:8]}"` — already dash-separated, not
      colon-separated. This matches the pattern already confirmed for finding 2 (Uniswap V3 pool): the code may already
      be fixed and the divergence is a **catalog-regeneration gap** (stale `prod/catalog.parquet` predating this adapter
      code), not a code gap. Confirm via a live re-fetch or a fresh backfill sample before assuming finding 6 needs a
      code change here.
- [ ] [DATA] P1. **Retrofit the 5 on-chain-perp adapters** to
      `build_canonical_instrument_id(AssetGroup.CEFI, venue,     InstrumentType.PERPETUAL, ...)` — real file:line:
      `hyperliquid.py:164` (`HYPERLIQUID:PERPETUAL:{name}-USD`), `aster.py:207` (`ASTER:PERPETUAL:{base}-{quote}`),
      `pacifica.py:86` (`PACIFICA-SOLANA:PERPETUAL:{coin}-USDC`), `extended.py:147`
      (`EXTENDED-STARKNET:PERPETUAL:{sym}`), `lighter.py:121` (`LIGHTER-ZKSYNC:PERPETUAL:{base}-USDC`). These 5 already
      produce the DECIDED target shape (`VENUE:PERPETUAL:     BASE-QUOTE`, finding 3/4) — this todo is pure DRY (route
      the existing correct construction through the shared builder instead of a parallel f-string), not a behavior
      change. Confirm the per-venue settlement quote currency is really correct while here (finding 4's still-open
      `[DECISION]` todo in the canonicalization issue doc).
- [ ] [DATA] P1. **Fix the real `:TYPE:` segment bug in Deribit's combo-leg builder** — `deribit_combo_adapter.py:310`
      (`_build_legs`) constructs `InstrumentLeg(instrument_key=f"DERIBIT:{leg_name}", ...)`, which is missing the
      `:TYPE:` segment entirely (2 colon-parts instead of 3 — every other leg/instrument in the workspace is
      `VENUE:TYPE:SYMBOL`). Route through the new
      `build_leg("DERIBIT", <type>, leg_name, side=..., ratio=..., passthrough=True)` instead — this requires first
      classifying each leg's `InstrumentType` from Deribit's own instrument_name convention (`-PERPETUAL` suffix →
      PERPETUAL; `-{DDMMMYY}` 2-part suffix → FUTURE; `-{DDMMMYY}-{STRIKE}-{C|P}` 4-part suffix → OPTION) since the
      Deribit `get_combos` API doesn't return a per-leg type field directly. Add a small classifier + unit tests before
      wiring it in — do not guess the type without verifying against real Deribit combo API responses.
- [ ] [DATA] P2. **Fix the real `/`-delimiter bug in Betfair's sports adapter** — `betfair.py:279`
      (`_build_runner_record`) builds `instrument_key = f"{market_id}/{selection_id}"`, using `/` instead of the
      workspace's `:`-delimited convention (confirmed in `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "Known gaps"
      section as "the audit's most degenerate raw-passthrough found"). Sports keeps its own ID scheme (not forced into
      `VENUE:TYPE:SYMBOL` — operator decision), so this does NOT route through `build_canonical_instrument_id`; it just
      needs its own delimiter fix (`f"{market_id}:{selection_id}"`) plus a check for any downstream consumer that
      currently splits on `/`.
- [ ] [DATA] P1. **Fix the real "no VENUE:TYPE: wrap at all" gap in both Prediction adapters** — Kalshi
      (`kalshi.py:799`, `instrument_key=ticker`) and Polymarket (`polymarket/parsing.py:139`,
      `instrument_key=condition_id`) both store the BARE raw provider id as `instrument_key` with zero structure — not
      even the `VENUE:TYPE:` prefix every other asset group carries. This is a real, separate finding from finding 8 in
      the canonicalization issue doc (which is about `base_asset`/`underlying`/`raw_symbol` being NULL — this is about
      `instrument_key` itself). Target:
      `build_canonical_instrument_id(AssetGroup.PREDICTION, venue, InstrumentType.PREDICTION_MARKET, raw_id,     passthrough=True)`
      → e.g. `KALSHI:PREDICTION_MARKET:<ticker>`. **Before retrofitting**: check every downstream consumer that
      currently joins on the bare `condition_id`/`ticker` shape (the Polymarket adapter's own
      `_register_clob_token_ids(condition_id, ...)` side-table keyed by the CURRENT bare value is one real consumer
      found in `parsing.py:135` — confirm it and any others tolerate or get updated for the wrapped shape) — same
      consumer-impact-check discipline as the CCXT plan. **Coordinate with, don't conflate against,
      `prediction_canonical_identity_migration_2026_07_08.md`** — that plan's `canonical_instrument_id` field (populated
      from `cross_venue_mapping`) is a SEPARATE, complementary field from the `instrument_key` this todo wraps, not a
      conflicting proposal. Sequence so this todo's downstream-consumer check and that plan's todo 6 (same underlying
      question, different field) don't get answered inconsistently by 2 different agents.
- [ ] [DATA] P3. **Cross-reference, don't duplicate, the TradFi combo-leg fix** — finding 7 (CBOE/VX spreads bypassing
      `InstrumentLeg`/COMBO entirely) already has its own dedicated plan,
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`. Note there that the new `build_leg()` helper is
      now available for that plan to use once its pending `[DECISION]` (per-leg `VENUE:` prefix drop) resolves — do not
      re-scope that work into this plan.
- [ ] [DATA] P3. **DECIDED — yes, refactor `ccxt_adapter.py` to call the shared builder.** Operator guidance: no real
      ambiguity here (explicitly "no output change" either way per this todo's own framing) — do it for consistency,
      same for the MTDS callers below. Not urgent, pick up opportunistically.
- [ ] [DATA] P3. **DECIDED — yes, upgrade MTDS's already-correct callers to the new one-entry-point** —
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py:242` and
      `.../cefi/tardis_shared.py:433,464,473`. Cosmetic consistency change, no behavior change expected. Not urgent.
- [x] [DATA] P3. **Retire the misspelled `AAVEV3-OPTIMISM` venue-token duplicate** (finding 5) — DONE, fixed by a
      concurrent sibling agent the same session (DeFi venue-token naming cleanup), confirmed via a fresh real re-query
      of `prod/catalog.parquet`: 0 ghost rows, 16 rows correctly under `AAVE_V3-OPTIMISM`. This todo was stale by the
      time this plan was filed — the parallel work wasn't visible to the agent that wrote it.
- [ ] [SCRIPT] P2. **Ship each retrofit batch via quickmerge**, quality-gates green per repo, citing before/after
      `instrument_key` evidence per adapter touched (same evidence pattern as the CCXT plan's per-venue table). Batch by
      asset-group-cluster (todo 1+2 together, todo 4 alone, todo 6 alone, etc.) rather than one giant commit.

## Progress Log

- **2026-07-08** — Filed as the follow-up checklist for the one-builder-for-everything architecture decision. Core
  builder (`build_canonical_instrument_id`, `build_leg`, `passthrough=True`) shipped this session in
  `unified-api-contracts`; one real live retrofit (`deribit_options_adapter.py`) and one compatibility-test proof
  (CCXT/Tardis table) landed alongside it. This plan captures the full remaining retrofit surface with real file:line
  evidence gathered via direct grep + read, not guessed.
