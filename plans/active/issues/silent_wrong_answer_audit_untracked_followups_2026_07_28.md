---
doc_type: issue
title: >-
  e2e-testing's 4-pillar schema/NaN checks are vacuous for 51 of 61 (asset_group, data_type) pairs and need a
  schema-contract decision — the untracked follow-up from silent_wrong_answer_audit_candidates_2026_07_20.md
summary: >-
  While closing silent_wrong_answer_audit_candidates_2026_07_20.md's one remaining todo (the 2 stashed features-service
  fixes — both resolved, see that doc's Progress Log), found its "Recommended handling" section named 2 more
  genuinely-open findings only as prose, never as a tracked `- [ ]` todo anywhere. **The P0 half (strategy-service's
  `pnl_input_builder.py` hardcoding every DeFi fill's gas price to 1 gwei) was EXTRACTED 2026-07-30 by operator ruling
  into its own dispatchable doc, strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md** — it was bounded and
  ready to ship, and did not belong behind an undecided design question. What remains here is that design question: P1
  finding 9 — e2e-testing's `validate_shards_4pillar.py` pillar-2/3 (schema/NaN) checks are vacuous (they degrade to
  `row_count > 0`) for 51 of 61 (asset_group, data_type) pairs because no per-pair schema/NaN-tolerance contract exists
  to check against; the audit doc explicitly said it "needs a schema-contract decision" and left it for a follow-up that
  was never filed.
status: open
nature: issue
asset_group:
  [cross-cutting] # corrected 2026-07-29 (ag-closeout-audit orthogonality fix) -- was [defi, cross-cutting], a genuine
  # mistag: P1 (e2e-testing schema-contract gap, 51/61 asset_group x data_type pairs) is unambiguously cross-AG, and
  # parent_epic is infrastructure_master (cross-cutting's own scoping epic), not defi_master; already cited/covered as
  # cross-cutting content under Track 12 of cross_cutting_consolidated_closeout_2026_07_25.md. The DeFi-specific half
  # (the P0 gas-fee reader fix) left this doc on 2026-07-30, so cross-cutting is now the doc's only content, not just
  # its dominant one.
stage: [data]
repos: [e2e-testing]
scope: [engineer, admin]
tags: [silent-failure, 4-pillar, schema-contract, follow-up]
related:
  [
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
  ]
created: 2026-07-28
author: unknown
last_updated: 2026-07-30
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2 # was P1 while this doc still carried the P0 gas-fee fix; the sole remaining todo is the P2 e2e-testing
# schema-contract decision, so the doc-level priority now matches its actual content (2026-07-30 split-out).
estimate_class: research
estimate_baseline_ai_days: 0.3 # was 0.5 — halved 2026-07-30, the gas-fee half of the work left this doc
estimate_calibrated_ai_days: 0.36
assigned_role: backend
drift_direction: neutral
depends_on: []
source: >-
  Surfaced 2026-07-28 while closing silent_wrong_answer_audit_candidates_2026_07_20.md's stashed-fixes todo (the audit
  doc's own "Recommended handling" #2/#4 prose, never converted to todos).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    e2e-testing/scripts/validation/validate_shards_4pillar.py,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md,
  ]
---

# Silent-wrong-answer audit — the untracked schema-contract follow-up

## Todos

> **EXTRACTED 2026-07-30 — the P0 strategy-service gas-fee reader fix no longer lives here.** Operator ruled it out of
> this doc so a bounded real-money PnL bug is not gated behind the undecided schema-contract question below. It is now
> `/plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` (`assigned_vm: planning`, P0,
> immediately dispatchable), re-verified against the current code and expanded with three follow-on defects the original
> one-line todo did not name. **Do not re-add a gas-fee todo here** — that doc is the single place it ships from. This
> doc now tracks ONLY the P2 e2e-testing schema-contract decision.

- [x] ✅ [BACKEND] P2. **e2e-testing** — resolve the schema-contract decision `validate_shards_4pillar.py`'s pillar-2
      (NaN) / pillar-3 (schema) checks need: they are vacuous (degrade to `row_count > 0`) for 51 of 61
      `(asset_group, data_type)` pairs because no per-pair schema/NaN-tolerance contract exists to check against. This
      is the harness MTDS quality-gates STEP 5.88 runs and the batch+live matrix delegates its batch verdict to, so the
      gap is load-bearing, not cosmetic. Source: silent_wrong_answer_audit_candidates_2026_07_20.md P1 finding 9 (the
      7th "safe survivor" — flagged as needing this decision, never actioned).

      **RESOLVED 2026-08-08 (operator ruling, NA-corpus blocker digest round 5, id=62 — "let Claude propose a real
          contract per pair, deriving from the existing 10 real pairs' conventions").** Read
          `e2e-testing/scripts/validation/validate_shards_4pillar.py` in full (563 lines) first.

          **Root finding**: the script already LOADS a per-family UAC-sourced required-column contract for all 4
          families — `_OHLCV_REQUIRED`, `_TICK_REQUIRED`, `_DEFI_REQUIRED`, `_SPORTS_REQUIRED` (`_load_uac_required()`,
          lines 96-129, sourced from `unified_api_contracts.internal.testing.seed_validator`). **But
          `required_row_columns_for()` (line 184) only ever consults `_OHLCV_REQUIRED`** — every non-OHLCV family
          hardcodes `base = frozenset()` (line 196), discarding the already-loaded tick/defi/sports contracts. Pillar-3
          degrades to time-column-only for 51/61 pairs not because no contract exists, but because 3 of 4 already-defined
          contracts are dead code. Pillar-2 has the matching gap: `_NAN_SCAN_COLUMNS` (lines 162-166) has no `tick` entry
          at all, so tick-family NaN checks are vacuously green regardless of `price`/`quantity` nulls.

          **Proposed concrete contract (extends the OHLCV pattern verbatim)**: (1) wire `_TICK_REQUIRED` into
          `required_row_columns_for()` for `family=="tick"` → required columns `{trade_id, price, quantity, side}`,
          covers every `trades`/`tick`/`tbbo`/`bbo`/`mbo`/`mbp` pair fleet-wide; (2) add `"tick": ("price", "quantity")`
          to `_NAN_SCAN_COLUMNS` at the same 1% default threshold; (3) wire `_DEFI_REQUIRED`/`_SPORTS_REQUIRED` too, but
          ONLY for the specific data_types their single flat UAC contract actually matches (yield/lending-shaped defi;
          `odds` sports) — do NOT apply blindly to the whole family (defi/sports each span several distinct real schemas,
          e.g. `dex_pools` has no `apy` column; forcing the yield contract on it would false-fail). The remaining
          non-matching defi/sports data_types need their own per-data_type UAC contracts first — genuine design work,
          filed as its own follow-up below, not blocking the tick-family fix.

          **NOT implemented this session** — the code change is in `e2e-testing`, out of this session's edit scope;
          filed as a fully-scoped spec citing exact file:line targets (`:96-129`, `:162-166`, `:184-197`) for the next
          e2e-testing session. See the implementation todo immediately below.

- [x] ✅ [SCRIPT] P2. **PARTIAL — tick wired (1+2 shipped); defi/sports (3) deliberately NOT wired, new finding: the
      flat UAC contracts don't match ANY live production schema, not just the "remaining" ones.** e2e-testing
      (2026-08-15, slot-31·cicd/infra). Shipped: (1) wired `_TICK_REQUIRED` into `required_row_columns_for()` for
      `family=="tick"` — post-strip required = `{trade_id, price, quantity, side}`, verified against live CEFI
      connectors (`tardis_machine_ws.py`, `deribit_ws.py`, `binance_futures_ws.py`, `coinbase_spot_ws.py`, `okx_ws.py`,
      `bitfinex_spot_ws.py`, `bybit_ws.py` all emit a literal `trade_id` column) — matches for real, safe to enforce;
      (2) added `"tick": ("price", "quantity")` to `_NAN_SCAN_COLUMNS`. **NOT implemented — (3)
      `_DEFI_REQUIRED`/`_SPORTS_REQUIRED` wiring, with evidence**: before wiring, verified the two "should obviously
      match" candidates each contract names (yield-shaped defi, sports odds) against their actual live GCS-writer column
      names — neither matches: - `_DEFI_REQUIRED` = `{protocol, asset, apy}` (post-strip). `staking_yields_handler.py`
      writes `{symbol, ts_event, venue, chain, apy, total_staked}` — has `apy` but no `protocol`/`asset` column at all
      (uses `symbol`). `lst_rates_handler.py`'s `_OUTPUT_COLUMNS` =
      `{timestamp, token, exchange_rate, apy, quote_asset, protocol, chain, block_number, method, contract}` — has
      `protocol` + `apy` but uses `token`, never a literal `asset` column. `lending_indices_write.py` never emits a flat
      `apy` at all (writes `supply_apy`/`borrow_apy` per `LendingRate`, matching `protocol_data.py`'s dataclass). -
      `_SPORTS_REQUIRED` = `{league, venue, match_id, odds_home, odds_away}` (post-strip: `venue` is path-identity so
      really `{league, match_id, odds_home, odds_away}`). `odds_api_adapter.py` writes `event_id` (never `match_id`) and
      no `odds_home`/`odds_away` columns anywhere in the file; broader grep across every
      `market_interface/ adapters/sports/*.py` + `live/connectors/odds_api_ws.py` found zero hits for
      `match_id`/`odds_home`/`odds_away` fleet-wide, only one incidental `league` hit (`opticodds_adapter.py`). Wiring
      either contract in as specified would have false-failed real production shards under the MTDS quality-gates STEP
      5.88 harness this script backs (a load-bearing gate, not cosmetic) — exactly the "do NOT apply blindly... would
      false-fail" risk the 2026-08-08 ruling itself warned about, just a bigger blast radius than that ruling assumed
      (it's not only the "remaining non-matching" defi/sports data_types that need new contracts — the two it assumed
      already matched don't either). Left `required_row_columns_for()` returning `frozenset()` for defi/sports
      (unchanged no-op behavior, safe) with a docstring recording this evidence inline. Added regression tests
      (`tests/unit/test_validate_shards_4pillar_required_columns.py`) pinning both the new tick contract AND the
      deliberate defi/sports non-wiring, so a future edit can't silently reintroduce the false-fail risk. Did NOT re-run
      `--json-out` pair-count split — the DEFI/SPORTS numbers are unchanged from the pre-existing baseline (still
      advisory/vacuous), only the tick pair count moved; a fresh live sample run is folded into the design todo below
      once real per-data_type contracts exist to validate against. Source:
      `plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md`
- [ ] [BACKEND] P3. **RULING D125 (2026-08-21, ADOPTED-REC) — Author: a load-bearing MTDS gate depends on these;
      leaving 2 of 4 families vacuous defeats the audit's purpose.** Corrected scope, 2026-08-15: NOT limited to the
      "remaining" non-yield/non-odds data_types (dex_pools/swaps/bridge/gas_fees for defi; non-odds sports types) as
      originally scoped — the flat `_DEFI_REQUIRED`/`_SPORTS_REQUIRED` UAC seed_validator contracts don't match live
      production column names even for the "obviously yield/odds-shaped" candidates (`staking_yields`/`lst_rates`
      write `symbol`/`token`+no bare `apy` in one case, `apy`+no `protocol`/`asset` in the other; the `odds` writer
      uses `event_id` with no `match_id`/`odds_home`/`odds_away` at all). Author real per-data_type UAC
      `seed_validator` entries matching each data_type's ACTUAL live writer schema (not the seed-data mirror),
      extending the tick-family pattern already wired 2026-08-15, then wire `required_row_columns_for()`/
      `_NAN_SCAN_COLUMNS` in `validate_shards_4pillar.py` to enforce them. Done when: per-data_type contracts exist
      matching live writer schemas, wired into the pillar-2/3 checks, and validated against a live sample with 0
      false-fails. (repos: unified-api-contracts, e2e-testing)

## Why this wasn't fixed inline

Both original findings were cross-repo (strategy-service / e2e-testing) — outside the filing session's assigned repo
(features-service) and its narrow mandate (reconcile 2 stashed features-service fixes). Filed per the "every follow-up
is a `- [ ]` todo, never prose" HARD RULE so archiving the parent audit doc doesn't silently drop them.

The remaining item stays `assigned_vm: NA` because it is a genuine design decision, not bounded work: nobody has decided
what the per-pair schema/NaN-tolerance contract should say, and "figure out how X should look" is a human decision, not
an AO todo (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility").
Once that contract is decided, wiring `validate_shards_4pillar.py` to enforce it is ordinary dispatchable work and
should be filed as its own todo against that decision's outcome.

## Progress Log

- **2026-07-30 (operator-ruled split-out)**: Extracted the P0 strategy-service gas-fee reader fix into
  `/plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` (`assigned_vm: planning`, P0)
  so it is dispatchable immediately instead of being trapped behind the undecided schema-contract question that is the
  reason this doc is `assigned_vm: NA`. The new doc re-verified the claim against current code (the 1-gwei fallback, the
  dead `gas_fees/chain_id=…/` prefix, MTDS's real canonical write path) and added three follow-on defects the one-line
  todo here never named. Narrowed this doc's frontmatter to match what it actually still holds: `repos`
  `[strategy-service, e2e-testing]` → `[e2e-testing]`, `stage` `[strategy, data]` → `[data]`, dropped the
  `gas-fees`/`pnl-correctness` tags, `priority` P1 → P2, estimate halved. Docs-only, no code changed.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the P2 todo is explicitly a schema-contract DECISION ('no
  per-pair schema/NaN-tolerance contract exists to check against'). NOTE the P0 gas-fee reader fix IS bounded and
  specific — worth an operator call on splitting it out. (That call was made the same day — see the split-out entry
  above.)

- **context-scout 2026-08-03**: refreshed context_scope (4 entries — added the extracted-successor doc
  `strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md`, cited repeatedly in this doc's own text).
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — re-confirms 2026-07-30; the sole remaining open todo is an
  explicitly undecided design/schema-contract question ("nobody has decided what the per-pair schema/NaN-tolerance
  contract should say"), citing the dispatch-scope-eligibility SSOT directly. The bounded P0 half was already split out
  2026-07-30 into its own AO-dispatchable doc.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirms 2026-07-30/2026-08-04; the sole open todo remains an
  explicitly undecided schema-contract design question (no per-pair schema/NaN-tolerance contract exists to check
  against), not bounded work a worker could resolve alone.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-15 (slot-31·cicd/infra, cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md dispatch)**: Implemented
  the tick half of the 2026-08-08-ruled contract (safe, verified against live connectors); did NOT implement the
  defi/sports half — live-schema verification found the flat UAC contracts don't match production column names for
  either candidate data_type, a bigger/different finding than the 2026-08-08 ruling assumed. See the todo above for the
  full evidence trail; corrected the DESIGN follow-up's scope to match. Doc remains `assigned_vm: NA` — the corrected
  DESIGN todo is still a genuine open decision (real per-data_type contracts, or a reframing of seed_validator's role).

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** [body-hash:71c8c1b9b53c3205]: KEEP-NA, valid -- Reaffirmed KEEP-NA 3x (2026-07-30, 08-04, 08-07). The bounded P0 half (gas-fee reader fix) was already extracted 2026-07-30 into its own AO-dispatchable doc. The sole remaining DESIGN todo was further investigated 2026-08-15 and found to be a BIGGER open design gap than originally scoped: the flat UAC seed_validator contracts don't match live production column names even for the 'obviously matching' candidates (yield-shaped defi, sports odds), so wiring them in as originally ruled would have false-failed real production shards under a load-bearing MTDS quality-gate.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — re-confirms 2026-07-30
  through 2026-08-17 (5 prior passes). Sole open item is still an explicit, unresolved design/schema-contract
  question (real per-data_type UAC contracts, or a reframing of `seed_validator`'s intended role) — bounded
  implementation only becomes possible once that call is made. No change since the last pass.
- **2026-08-21 — ruling D125 (seed_validator contract scope)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Author — a load-bearing MTDS gate depends on these; leaving 2 of 4
  families vacuous defeats the audit's purpose. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
