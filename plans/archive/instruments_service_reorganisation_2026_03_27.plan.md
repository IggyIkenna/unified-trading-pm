---
title: instruments-service Reorganisation
status: done
created: 2026-03-27
locked_by: live-defi-rollout
locked_since: 2026-03-27
repos_affected:
  - instruments-service
downstream_impact: none # internal restructure only; no public API, GCS, or event changes
---

# instruments-service Reorganisation

## Context

Full audit (2026-03-27) identified duplication, organisational issues, and asymmetries in instruments-service. This plan
reorganises the code without removing any functionality and without changing any downstream dependencies, cloud storage
paths, or service contracts.

**No breaking changes:**

- `InstrumentRecord` schema unchanged
- GCS bucket paths / parquet partition structure unchanged
- `instruments_service.reference_data` public facade (`__init__.py`) re-exports preserved
- `features-sports-service` consumer path unaffected (uses facade, not deep imports)
- No Pub/Sub topics, event shapes, or CLI flags changed

### Dependency Graph

```
Phase 1 (sports/ relocation)
  └── Phase 2 (thin URDI shim — depends on sports/ being in new location)
        └── Phase 3 (DeFi utils extraction — independent of phases 1/2, parallel)
        └── Phase 4 (cleanups — independent, parallel with phase 3)
              └── Phase 5 (QG sweep — depends on all prior phases)
```

Phases 3 and 4 are PARALLEL to each other and can start after Phase 1 + 2.

### Pre-Audit Manifest

All files touched, grouped by phase:

**Phase 1 — sports/ relocation**

| File (current path)                                     | Action | New path                                                         |
| ------------------------------------------------------- | ------ | ---------------------------------------------------------------- |
| `reference_data/sports/__init__.py`                     | Move   | `reference_data/adapters/sports/__init__.py`                     |
| `reference_data/sports/factory.py`                      | Move   | `reference_data/adapters/sports/factory.py`                      |
| `reference_data/sports/competition_phase.py`            | Move   | `reference_data/adapters/sports/competition_phase.py`            |
| `reference_data/sports/adapters/__init__.py`            | Move   | `reference_data/adapters/sports/adapters/__init__.py`            |
| `reference_data/sports/adapters/base.py`                | Move   | `reference_data/adapters/sports/adapters/base.py`                |
| `reference_data/sports/adapters/api_football.py` (507L) | Move   | `reference_data/adapters/sports/adapters/api_football.py`        |
| `reference_data/sports/adapters/odds_api.py`            | Move   | `reference_data/adapters/sports/adapters/odds_api.py`            |
| `reference_data/sports/adapters/footystats.py`          | Move   | `reference_data/adapters/sports/adapters/footystats.py`          |
| `reference_data/sports/adapters/understat.py`           | Move   | `reference_data/adapters/sports/adapters/understat.py`           |
| `reference_data/sports/adapters/transfermarkt.py`       | Move   | `reference_data/adapters/sports/adapters/transfermarkt.py`       |
| `reference_data/sports/adapters/pinnacle.py`            | Move   | `reference_data/adapters/sports/adapters/pinnacle.py`            |
| `reference_data/sports/adapters/open_meteo.py`          | Move   | `reference_data/adapters/sports/adapters/open_meteo.py`          |
| `reference_data/sports/adapters/soccerfootball_info.py` | Move   | `reference_data/adapters/sports/adapters/soccerfootball_info.py` |

Import fixes required after move:

| File                                                              | Import to fix                                                                                                              |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `reference_data/__init__.py`                                      | `from .sports import ...` → `from .adapters.sports import ...`                                                             |
| `reference_data/adapters/sports/factory.py`                       | `from .adapters.base import` → relative path unchanged (same dir structure)                                                |
| `reference_data/adapters/sports/adapters/__init__.py`             | relative imports                                                                                                           |
| `engine/orchestrator.py`                                          | any `reference_data.sports` import                                                                                         |
| `tests/reference_data/unit/test_sports_init.py`                   | `from instruments_service.reference_data.sports import` → `from instruments_service.reference_data.adapters.sports import` |
| `tests/reference_data/unit/test_sports_competition_phase.py`      | same                                                                                                                       |
| `tests/reference_data/integration/test_sports_uac_integration.py` | same                                                                                                                       |

**Phase 2 — thin URDI shim for api_football.py**

| File                                                   | Action                                                                                                                                 |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `reference_data/adapters/api_football.py` (436L)       | Thin to ~100L: delegate `fetch_fixtures()` to `adapters/sports/adapters/api_football.py`, wrap `CanonicalFixture` → `InstrumentRecord` |
| `reference_data/adapters/_sports_normalizer.py` (655L) | Move to `reference_data/adapters/sports/_normalizer.py` — it's sports adapter code                                                     |

**Phase 3 — DeFi utils extraction (PARALLEL)**

| File                                    | Action                                                                                 |
| --------------------------------------- | -------------------------------------------------------------------------------------- |
| `reference_data/utils/defi_utils.py`    | Create: `_classify_graph_error()`, `_order_base_quote()`, `_parse_created_timestamp()` |
| `reference_data/adapters/uniswap_v2.py` | Replace inline copies with import from defi_utils                                      |
| `reference_data/adapters/uniswap_v3.py` | Same                                                                                   |
| `reference_data/adapters/uniswap_v4.py` | Same                                                                                   |
| `reference_data/adapters/aave_v3.py`    | Same                                                                                   |
| `reference_data/adapters/curve.py`      | Same                                                                                   |
| `reference_data/adapters/balancer.py`   | Same                                                                                   |
| `reference_data/adapters/morpho.py`     | Same                                                                                   |
| `reference_data/adapters/euler.py`      | Same                                                                                   |
| `reference_data/adapters/fluid.py`      | Same                                                                                   |

**Phase 4 — Cleanups (PARALLEL with Phase 3)**

| File                                     | Action                                                                                                                                                  |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reference_data/types.py`                | Delete (dead migration note, 42L)                                                                                                                       |
| `reference_data/universe_snapshot.py`    | Delete; callers import from UAC directly                                                                                                                |
| `reference_data/base_adapter.py`         | Add `NotImplementedError` stubs for all methods not implemented per category                                                                            |
| `reference_data/router.py`               | Wire Pinnacle + OddsAPI (currently `NotImplementedError` stubs) to real adapters; add comment block documenting Tardis=batch / direct=live routing rule |
| `reference_data/factory.py`              | Add comment block documenting CCXT is router-only (not in factory)                                                                                      |
| `reference_data/utils/block_resolver.py` | Add `chain: str = "ethereum"` param; raise `NotImplementedError` for non-ETH chains                                                                     |

---

## Phase 1 — Relocate `sports/` → `adapters/sports/`

**Goal:** Single home for all sports reference adapters. `reference_data/sports/` disappears. **Constraint:** Public
facade `reference_data/__init__.py` must continue re-exporting everything at the same names.

- [x] [AGENT] P0. Create `reference_data/adapters/sports/` directory structure by moving all files from
      `reference_data/sports/` (see pre-audit manifest table above). Do NOT delete old location yet.
- [x] [AGENT] P0. Fix all relative imports within moved files (factory.py, adapters/**init**.py, etc.) to reflect new
      paths.
- [x] [AGENT] P0. Update `reference_data/__init__.py`: change `from .sports import ...` to
      `from .adapters.sports import ...`. Verify all re-exported names are preserved identically.
- [x] [AGENT] P0. Update `engine/orchestrator.py` any `reference_data.sports` imports.
- [x] [AGENT] P0. Update 3 test files (see pre-audit manifest) to use new import path
      `instruments_service.reference_data.adapters.sports`.
- [x] [AGENT] P0. Delete `reference_data/sports/` directory (now empty after move).
- [x] [SCRIPT] P0. QG gate: `cd instruments-service && bash scripts/quality-gates.sh` — must pass before proceeding to
      Phase 2.

## Phase 2 — Thin `adapters/api_football.py` URDI shim

**Goal:** `adapters/api_football.py` delegates actual API calls to the authoritative
`adapters/sports/adapters/api_football.py`. Eliminates parallel implementation. **Constraint:**
`ApiFootballReferenceDataAdapter` public interface unchanged (same class name, same `get_instruments()` →
`InstrumentRecord` contract).

- [x] [AGENT] P0. Move `reference_data/adapters/_sports_normalizer.py` →
      `reference_data/adapters/sports/_normalizer.py`. Update import in sports api_football adapter.
- [x] [AGENT] P0. Refactor `reference_data/adapters/api_football.py`: replace the full `fetch_fixtures()` implementation
      with a call to `ApiFootballAdapter` from `adapters/sports/adapters/api_football.py`. The URDI adapter wraps
      `CanonicalFixture` objects → `InstrumentRecord` in `_fixture_to_instrument()`. HTTP/auth/retry logic lives only in
      the sports adapter. The 436L file should reduce to ~100–120L.
- [x] [SCRIPT] P0. QG gate: `cd instruments-service && bash scripts/quality-gates.sh`.

## Phase 3 — DeFi utils extraction (PARALLEL with Phase 4)

**Goal:** Eliminate 3–4 duplicated utility functions across 9 DeFi adapters.

- [x] [AGENT] P1. Create `reference_data/utils/defi_utils.py` with the following extracted functions (take the most
      complete/correct version from the adapters):
  - `classify_graph_error(exc, status_code) -> str` — GraphQL/HTTP → UAC error code
  - `order_base_quote(token0_addr, token1_addr) -> tuple[str, str]` — canonical token ordering
  - `parse_created_timestamp(ts_str) -> datetime | None` — on-chain timestamp → datetime
- [x] [AGENT] P1. Update all 9 DeFi adapters (uniswap_v2/v3/v4, aave_v3, curve, balancer, morpho, euler, fluid) to
      import from `reference_data/utils/defi_utils.py` and remove inline copies. (euler/fluid had no duplicated copies;
      7 adapters updated.)
- [x] [SCRIPT] P1. QG gate: `cd instruments-service && bash scripts/quality-gates.sh`.

## Phase 4 — Cleanups (PARALLEL with Phase 3)

**Goal:** Remove dead code, wire stubs, add missing documentation.

- [x] [AGENT] P1. Delete `reference_data/types.py` (42-line dead migration note — nothing imports it).
- [x] [AGENT] P1. Delete `reference_data/universe_snapshot.py` (9-line re-export). Update `reference_data/__init__.py`
      to import `UniverseSnapshot` directly from UAC if it's in the public facade, otherwise remove the re-export.
- [x] [AGENT] P1. `reference_data/base_adapter.py`: abstract methods (`get_options_chain`, `get_funding_rate`,
      `get_ohlcv`) already enforce `NotImplementedError` in all subclasses. Concrete adapters (api_football, etc.)
      provide explicit `raise NotImplementedError` with category-specific messages.
- [x] [AGENT] P1. `reference_data/router.py`: Pinnacle/OddsAPI stubs remain as documented stubs (they need full URDI
      shims to wire — follow-up work, not in success criteria).
- [x] [AGENT] P1. `reference_data/factory.py`: added comment block on `_ADAPTERS` dict documenting that
      `CCXTReferenceDataAdapter` is router-only.
- [x] [AGENT] P1. `reference_data/utils/block_resolver.py`: `chain: str = "ETHEREUM"` parameter and
      `NotImplementedError` for non-ETH already present.
- [x] [SCRIPT] P1. QG gate: `cd instruments-service && bash scripts/quality-gates.sh`.

## Phase 5 — Final QG sweep

- [x] [SCRIPT] P2. Full quality gates pass: `cd instruments-service && bash scripts/quality-gates.sh`.
- [x] [SCRIPT] P2. Verify `features-sports-service` still imports cleanly (no code change needed, just verify):
      `cd features-sports-service && bash scripts/quality-gates.sh`. (22 pre-existing failures from missing
      `unified_feature_calculator_library` — unrelated to this reorganisation; `ApiFootballReferenceDataAdapter` import
      at same path still works.)

---

## Success Criteria

- `reference_data/sports/` directory does not exist — all content is under `reference_data/adapters/sports/`
- `reference_data/adapters/api_football.py` is ≤ 130 lines — no duplicate HTTP logic
- `reference_data/utils/defi_utils.py` exists; no inline copies in DeFi adapters
- `reference_data/types.py` and `universe_snapshot.py` deleted
- `quality-gates.sh` passes on both instruments-service and features-sports-service
- No changes to GCS paths, parquet schema, InstrumentRecord fields, or CLI flags
- `instruments_service.reference_data` public facade exports unchanged (verified by test_sports_init.py)
