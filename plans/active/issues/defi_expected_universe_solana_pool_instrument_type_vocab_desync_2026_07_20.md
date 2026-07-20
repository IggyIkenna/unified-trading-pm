---
doc_type: issue
title:
  "DeFi Solana pools — the expected-universe enumerator seeds instrument_type=pool while the MTDS writer emits
  solana_amm_pool/solana_vault, so every Solana-pool expected_unattempted cell is permanently unsatisfiable and inflates
  the coverage denominator"
summary: >-
  Found by the /data-pipeline-reconciliation defi run (2026-07-20, F6). On the RAYDIUM/ORCA/PHOENIX (SOLANA) shards the
  manifest carries TWO instrument_type vocabularies for the same atom — solana_amm_pool (captured, matches the writer)
  AND pool/POOL (expected_unattempted, never satisfiable). Root cause is a writer↔catalogue vocabulary split on the
  EXPECTED side. The MTDS dex_pools writer stamps Solana AMM pools with instrument_type=solana_amm_pool and Kamino CLMM
  vaults with solana_vault (dex_pools_handler.py:229-234,721,733), while the instruments-service reference adapters and
  the catalogue stamp those same pools as InstrumentType.POOL (raydium.py, kamino.py, orca), which the expected-universe
  enumerator seeds verbatim into expected_unattempted cells. UAC _INSTRUMENT_TYPE_ALIASES keeps pool and solana_amm_pool
  as DISTINCT keys (no cross-alias), so the captured solana_amm_pool cells can never flip the expected pool cells to
  captured. Those pool cells sit permanently as expected_unattempted, overstating the honest-coverage denominator for
  every Solana DEX-pool venue. This is an H1-class defect on the EXPECTED side (the enumerator emits a vocabulary the
  writer never produces), distinct from the honest-coverage UPPERCASE/lowercase READ-side case break and from the
  phantom (captured-without-object) class.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    defi,
    honest-coverage,
    denominator,
    expected-unattempted,
    instrument-type,
    vocabulary-desync,
    solana,
    dex-pool,
  ]
related:
  [
    data_pipeline_reconciliation_defi_2026_07_20,
    defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20,
    defi_expected_unattempted_backlog_1m_2026_07_03,
    honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20,
    honest-coverage-model,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation defi run 2026-07-20 (finding F6); code-verified against the MTDS writer + IS catalogue
  adapters + UAC instrument-type alias table"
resolved_by:
---

# DeFi Solana pools — expected-universe seeds `pool` while the writer emits `solana_amm_pool`

> **⚠️ BIG FINDING (data-correctness — denominator-defining).** The defect is on the EXPECTED side of honest coverage —
> the enumerator materialises `expected_unattempted` cells with an `instrument_type` value the writer never emits, so
> those cells can never reconcile to `captured` and permanently inflate the coverage denominator for every Solana DEX
> venue. Surfaced by the /data-pipeline-reconciliation defi run (F6, `data_pipeline_reconciliation_defi_2026_07_20.md`).

## The vocabulary split (verified in code)

| Side                                                         | instrument_type for a Solana AMM / CLMM pool                      | Evidence                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------ | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTDS writer (captured rows)                                  | `solana_amm_pool` (Orca/Raydium/Phoenix), `solana_vault` (Kamino) | `market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py:229-234` (`_SOLANA_DEX_ITYPE_STR`), applied at `:721` (`_itype_str`) → `:733` `record_captured(instrument_type=_itype_str, ...)`                                                  |
| IS catalogue / expected-universe (expected_unattempted rows) | `POOL` → normalised `pool`                                        | `instruments-service/.../reference_data/adapters/defi/raydium.py:4` ("instrument_type=\"POOL\""), `.../kamino.py:4,82` ("Raydium/Orca CLMM pools ... instrument_type=\"POOL\""), + the other defi POOL adapters; enumerator seeds catalogue `instrument_type` verbatim |
| UAC alias table                                              | keeps `pool` and `solana_amm_pool` DISTINCT                       | `unified-api-contracts/.../registry/market_data_categories.py:720` (`"pool": "pool"`), `:727` (`"solana_amm_pool": "solana_amm_pool"`) — no cross-alias, so a value comparison never unifies them                                                                      |

The MTDS branch is explicit: `_itype_str = _SOLANA_DEX_ITYPE_STR.get(protocol, "pool") if chain == "SOLANA" else "pool"`
(`dex_pools_handler.py:721`). So EVM pools get `pool` on BOTH sides (they reconcile fine); the divergence is
**Solana-only** — Orca/Raydium/Phoenix (`solana_amm_pool`) and Kamino (`solana_vault`) captured cells vs `pool` expected
cells.

## Why it matters

The shard atom includes `instrument_type`.
`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` (honest-coverage-model, CK3). A
Solana-pool `expected_unattempted` cell keyed on `instrument_type=pool` has NO captured twin (the twin is keyed
`solana_amm_pool`), so it can never move to the numerator — it is a permanent denominator drag that no amount of
successful capture can clear. The reconciliation report measured this live on RAYDIUM/SOLANA
(`data_pipeline_reconciliation_defi_2026_07_20.md` §3 row 2, §4 F6). The scale is corroborated by the v2 enumerator's
own by-instrument_type breakdown — `pool 42.2M` expected rows (`defi_expected_unattempted_backlog_1m_2026_07_03.md`,
2026-07-10 diagnostic) — an unknown but non-trivial slice of which are Solana pools whose captured twins carry
`solana_amm_pool`/`solana_vault`.

## Distinct from adjacent open issues (do NOT dedupe away)

- NOT the honest-coverage READ-side case break
  (`honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`) — that is UPPERCASE-vs-lowercase
  of the SAME token on the read/compare side; this is a genuinely DIFFERENT token (`pool` vs `solana_amm_pool`),
  case-normalisation does not fix it.
- NOT `defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md` — that is about non-POOL types (lending,
  lst, holdings) having no residual emitter; this is a POOL type whose captured writer-vocabulary simply does not match
  the expected catalogue-vocabulary.
- NOT the phantom class (F8, `phantom_captures_defi_2026_06_28.md`) — phantoms are `captured` rows with no object; these
  are `expected_unattempted` rows that can never become captured.

## The fix decision (needs a ruling on which vocabulary is canonical)

The two vocabularies must be unified on the `instrument_type` axis for Solana pools. Candidate directions (operator /
architecture call — do NOT blind-pick):

- **A** — make the EXPECTED side match the writer. Alias `pool` → `solana_amm_pool` (and `solana_vault`) for Solana
  venues at enumeration time, or have the catalogue stamp Solana pools with the writer vocabulary. Narrowest; matches
  the atom the data actually lands under.
- **B** — make the WRITER match the catalogue enum (`pool` everywhere), dropping the Solana-specific `solana_amm_pool`/
  `solana_vault` tokens. Larger blast radius (every Solana captured object + manifest key + downstream reader).
- **Other** — a shared alias in UAC `_INSTRUMENT_TYPE_ALIASES` that folds `solana_amm_pool`/`solana_vault` and `pool` to
  one canonical key, applied on BOTH the writer emission and the enumerator seed AND every coverage/reconciliation
  comparison (so the reconciliation probe, the honest-coverage join, and the phantom/orphan `is_valid_shard_key` all
  agree).

## Todos

- [ ] 1. [DATA] P1. Measure the live blast radius — count `expected_unattempted` cells keyed `instrument_type=pool` on
      Solana venues (RAYDIUM/ORCA/PHOENIX/KAMINO) in the defi `_index` that have a `captured` twin keyed
      `solana_amm_pool`/`solana_vault` on the same `(venue, chain, data_type, instrument_id, day)` — the permanently-
      unsatisfiable set (repo: instruments-service / manifest read).
- [ ] 2. [DECISION] P1. Operator/architecture ruling — direction A (expected matches writer) vs B (writer matches
      catalogue) vs a UAC alias fold. Blocks the code fix; must keep the writer, the enumerator, the honest-coverage
      join, and the phantom/orphan `is_valid_shard_key` all on ONE unified `instrument_type` vocabulary for Solana
      pools.
- [ ] 3. [CODE] P1. Apply the ruling and add a regression test that a Solana AMM pool captured under `solana_amm_pool`
      reconciles (flips to captured) the enumerator's expected cell for the same instrument — i.e. the writer emission
      and the enumerator seed produce the SAME atom (repos: market-tick-data-service, instruments-service,
      unified-api-contracts).
- [ ] 4. [DATA] P2. After the fix, re-run the defi expected-universe scan and confirm the Solana-pool
      `expected_unattempted` count drops to the genuinely-outstanding set (no permanently-unsatisfiable residue), and
      the defi honest-coverage denominator refreshes (repo: instruments-service).
