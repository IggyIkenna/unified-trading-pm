---
title: Defunct UAC provider dirs — 12 venues operator-flagged for removal
created: 2026-05-20
author: ikenna-slot-1
source:
  - "operator directive 2026-05-20 during WIF/canary work"
  - "uac_weekly_validation_wif_secrets_missing_2026_05_17.md § Resolution"
locked_by: live-defi-rollout
locked_since: 2026-05-20
severity: P3 — workspace hygiene; not May-23 critical path
status: BLOCKED-CROSS-REPO-COORDINATION
---

## What I found

While slicing the weekly schema-validation canary scope with the operator, 12 UAC `external/<venue>/` dirs were flagged
as defunct vendors / unused scaffolding. They should be deleted from UAC to keep the workspace honest and remove stale
cassettes from the canary's run surface.

**The 12 dirs**:

| Venue          | Operator reason                       | Cross-repo touch points                                                              |
| -------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| `glassnode`    | Defunct paid analytics (in-house now) | UAC `tests/unit/test_phase5_phase6_normalizers.py` references it                     |
| `cryptoquant`  | Defunct paid analytics                | none (clean)                                                                         |
| `coinglass`    | Defunct paid analytics                | UAC `registry/capability_declarations/_altdata.py`                                   |
| `cryptopanic`  | Defunct paid analytics                | none (clean)                                                                         |
| `hyblock`      | Defunct paid analytics                | UAC `registry/capability_declarations/_altdata.py`                                   |
| `lunarcrush`   | Defunct paid analytics                | none (clean)                                                                         |
| `fear_greed`   | Defunct (in-house signal)             | MTDS `tests/.../test_vcr_ac_schema_validation.py`                                    |
| `coingecko`    | Defunct (replaced)                    | UAC `registry/_endpoint_registry_data.py` + `_altdata.py`                            |
| `sharpapi`     | Not trading, not used                 | **MTDS `market_interface/adapters/sports/sharpapi_adapter.py` — real adapter**       |
| `dydx`         | Dropping volume — out of universe     | UAC `tests/vcr/test_dydx_vcr.py` + MTDS `tests/.../test_vcr_ac_schema_validation.py` |
| `prime_broker` | No real API hookup                    | UAC `registry/venue_manifest/internal_services.py`                                   |
| `regulatory`   | No real API hookup                    | UAC `registry/venue_manifest/internal_services.py`                                   |

## Why it matters

1. **Workspace truth**: defunct vendors in `external/` mislead anyone reading UAC's surface as "supported sources." User
   has explicitly said these are not part of the operating universe.
2. **Canary noise**: cassettes for these venues currently get walked by the weekly canary and surface as ✅/❌ noise on
   every run.
3. **Schema-Health workflow noise**: the per-PR cassette-replay job also runs over these dirs.
4. **Sharpapi specifically**: MTDS still has a `sharpapi_adapter.py` that imports from the UAC dir. That adapter must be
   deleted (or migrated to a different vendor) before UAC's `external/sharpapi/` can be removed.

## Recommended decision

**Phase 1 — Clean deletes (7 dirs, single-repo UAC, ~1h):** `cryptoquant`, `cryptopanic`, `lunarcrush`, `prime_broker`,
plus `coinglass`/`hyblock`/`coingecko` (registry-ref-only — delete dir + remove their `SourceCapability` entry from
`_altdata.py`).

**Phase 2 — UAC-internal touch (2 dirs):**

- `glassnode`: delete dir + remove from `tests/unit/test_phase5_phase6_normalizers.py`
- `regulatory`: delete dir + remove from `registry/venue_manifest/internal_services.py`

**Phase 3 — Cross-repo MTDS coordination (3 dirs, needs Harsh side or slot 1 cross-repo):**

- `dydx`: delete UAC dir + delete UAC `tests/vcr/test_dydx_vcr.py` + delete MTDS
  `tests/market_interface/integration/test_vcr_ac_schema_validation.py` entry referencing dydx
- `fear_greed`: same pattern (delete from MTDS test)
- `sharpapi`: delete MTDS `sharpapi_adapter.py` first, then UAC dir. Confirm with operator that no live MTDS handler is
  wired to sharpapi (`rg "sharpapi" market-tick-data-service/market_tick_data_service/` is empty per my 2026-05-20 grep,
  but worth re-confirming before delete).

**Phase 4 — Post-delete validation**:

- Run UAC quality-gates (basedpyright + tests)
- Run MTDS quality-gates
- Run UAC schema-health workflow (must still pass with reduced surface)
- Bump UAC + MTDS minor versions (`feat!` on 0.x.x = MINOR per semver-agent)

## Cross-references

- Parent issue: `uac_weekly_validation_wif_secrets_missing_2026_05_17.md` (RESOLVED 2026-05-20)
- Canary scripts shipped: `unified-api-contracts@18c74a56`
- Live drift findings auto-filed: UAC issue #45 (separate from this cleanup)
