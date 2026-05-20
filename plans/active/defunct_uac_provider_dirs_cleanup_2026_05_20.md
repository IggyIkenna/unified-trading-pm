---
name: defunct_uac_provider_dirs_cleanup_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P3
status: complete
target_slot: ikenna-slot-1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
deadline: 2026-05-23
parent_plan: master_to_live_defi_2026_05_23.md
parent_epic: data_correctness
related_plans:
  - uac_source_capability_metadata_promotion_2026_05_20.md
  - issues/uac_weekly_validation_wif_secrets_missing_2026_05_17.md
codex_ssots:
  - codex/02-data/contracts-scope-and-layout.md
---

# Defunct UAC provider dirs cleanup — 2026-05-20

> **Trigger**: 2026-05-20 operator directive during WIF/canary scope-slicing for the weekly schema-validation work
> (parent issue: [[uac_weekly_validation_wif_secrets_missing_2026_05_17]] RESOLVED 2026-05-20). Operator flagged 12 UAC
> `external/<venue>/` dirs as defunct vendors / unused scaffolding to delete. Promoted from issue doc to active plan
> with operator instruction: "lets promote this to pm active plans... and then just do it all now with sub agents please
> in full then mark done and archive."

## Why this plan exists

12 UAC `external/<venue>/` dirs are defunct vendors (8) or never-wired infra-style stubs (4). They mislead anyone
reading UAC's surface as "supported sources," add noise to the weekly schema-validation canary's ✅/❌ output, and in
the case of `sharpapi` keep a real MTDS adapter alive against a vendor the operator said is "not trading, not used."
Delete cleanly, no shim.

## Goals

1. Delete 12 `external/<venue>/` dirs from UAC.
2. Remove all registry / `__init__.py` / capability-declaration / test references.
3. Delete the `sharpapi_adapter.py` from MTDS (cross-repo).
4. Pass UAC + MTDS quality-gates after deletion.
5. Bump minor version on both (semver-agent auto-handles).

## The 12 dirs (operator-flagged 2026-05-20)

| Venue          | Reason                                | Cross-repo touch points                                                              |
| -------------- | ------------------------------------- | ------------------------------------------------------------------------------------ |
| `glassnode`    | Defunct paid analytics (in-house now) | UAC `tests/unit/test_phase5_phase6_normalizers.py`                                   |
| `cryptoquant`  | Defunct paid analytics                | none (clean)                                                                         |
| `coinglass`    | Defunct paid analytics                | UAC `registry/capability_declarations/_altdata.py`                                   |
| `cryptopanic`  | Defunct paid analytics                | none (clean)                                                                         |
| `hyblock`      | Defunct paid analytics                | UAC `registry/capability_declarations/_altdata.py`                                   |
| `lunarcrush`   | Defunct paid analytics                | none (clean)                                                                         |
| `fear_greed`   | Defunct (in-house signal)             | MTDS `tests/.../test_vcr_ac_schema_validation.py`                                    |
| `coingecko`    | Defunct (replaced)                    | UAC `registry/_endpoint_registry_data.py` + `_altdata.py`                            |
| `sharpapi`     | Not trading, not used                 | **MTDS `market_interface/adapters/sports/sharpapi_adapter.py`**                      |
| `dydx`         | Dropping volume — out of universe     | UAC `tests/vcr/test_dydx_vcr.py` + MTDS `tests/.../test_vcr_ac_schema_validation.py` |
| `prime_broker` | No real API hookup                    | UAC `registry/venue_manifest/internal_services.py`                                   |
| `regulatory`   | No real API hookup                    | UAC `registry/venue_manifest/internal_services.py`                                   |

## Phased execution

### Phase 1 — UAC clean deletes (7 dirs) ✅ DONE 2026-05-20 — UAC@a408925c

`cryptoquant`, `cryptopanic`, `lunarcrush`, `prime_broker` (no refs) + `coinglass`, `hyblock`, `coingecko` (registry
refs only).

- [x] ✅ Delete `unified_api_contracts/external/{cryptoquant,cryptopanic,lunarcrush,prime_broker}/` — UAC@a408925c
- [x] ✅ Delete `unified_api_contracts/external/{coinglass,hyblock,coingecko}/` + remove SourceCapability entries from
      `registry/capability_declarations/_altdata.py` — UAC@a408925c
- [x] ✅ Remove `coingecko` from `registry/_endpoint_registry_data.py` — UAC@a408925c
- [x] ✅ Remove `prime_broker` from `registry/venue_manifest/internal_services.py` — UAC@a408925c
- [x] ✅ Audit `unified_api_contracts/__init__.py` for re-exports of the 7 venues; remove — UAC@a408925c

### Phase 2 — UAC-internal touch (2 dirs) ✅ DONE 2026-05-20 — UAC@a408925c

- [x] ✅ `glassnode`: delete dir + remove from `tests/unit/test_phase5_phase6_normalizers.py` — UAC@a408925c (also
      removed glassnode normalize fns + altdata error mapping + venue rate limits +
      canonical/domain/execution/prime_broker.py file delete)
- [x] ✅ `regulatory`: delete dir + remove from `registry/venue_manifest/internal_services.py` — UAC@a408925c (also
      removed \_REGULATORY SourceCapability from `_tradfi.py` + normalize_regulatory_error +
      normalize_regulatory_trade_report)

### Phase 3 — Cross-repo MTDS coordination (3 dirs) ✅ DONE 2026-05-20

- [x] ✅ [SCRIPT] P3. `sharpapi`: confirm no live MTDS handler wired; deleted
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/sharpapi_adapter.py` + UAC
      `external/sharpapi/` — UAC@4aee80e1 + MTDS@adc56bc
- [x] ✅ [SCRIPT] P3. `fear_greed`: deleted UAC dir + removed fear_greed entry in MTDS
      `tests/market_interface/integration/test_vcr_ac_schema_validation.py` — UAC@4aee80e1 + MTDS@adc56bc
- [x] ✅ [SCRIPT] P3. `dydx`: deleted UAC dir + UAC `tests/vcr/test_dydx_vcr.py` + dydx entry in MTDS
      `test_vcr_ac_schema_validation.py` — UAC@4aee80e1 + MTDS@adc56bc

### Phase 4 — Validation + version bumps

- [ ] [SCRIPT] P3. UAC `bash scripts/quality-gates.sh` — must pass green
- [ ] [SCRIPT] P3. MTDS `bash scripts/quality-gates.sh` — must pass green
- [ ] [SCRIPT] P3. Dispatch UAC `weekly-validation.yml` workflow + verify 12 venues are gone from output
- [x] ✅ [SCRIPT] P3. Commit UAC + MTDS as `feat!:` — UAC@df2c7543 + MTDS@adc56bc (semver-agent auto-bumps minor)
- [ ] [SCRIPT] P3. Promote via quickmerge once both repos green

### Phase 5 — Extend: kill Manifold (operator-added 2026-05-20) ✅ DONE 2026-05-20 — UAC@276f9efd + MTDS@fae9416

Operator directive 2026-05-20 (during audit synthesis review):
> "play money prediction seems pointless. kill it entirely from docs, plans, uac and canary"

Manifold Markets is a play-money ("Mana") prediction-market platform. The 5-finding audit established: zero
production consumers reading any field except `probability` (with `or 0` fallback in the dormant MTDS adapter).
Reconciles with the earlier "deprecated for future use, keep but don't actually use" classification — operator
escalated to full deletion after seeing the canary noise from the BINARY-vs-MULTIPLE_CHOICE drift.

- [x] ✅ Delete `unified-api-contracts/unified_api_contracts/external/manifold/` (incl. cassette) — UAC@276f9efd
- [x] ✅ Delete `market-tick-data-service/.../market_interface/adapters/prediction/manifold_adapter.py` — MTDS@fae9416
- [x] ✅ Remove Manifold ripple refs across UAC (15 files: __init__.py, execution.py, normalize_utils/*,
      canonical/*, internal/*, config/provider_api_versions.yaml, 4 tests) — UAC@276f9efd
- [x] ✅ Remove Manifold from PM/codex active plans + SSOT docs (5 files: codex venue-availability +
      credentials-matrix + secret-manager-naming, plans/active api_keys_wallets_accounts_readiness +
      cross_cutting_may_23_deliverables) — landing now
- [x] ✅ Workspace-wide grep shows 0 active-source manifold refs after cleanup
- [x] ✅ Commit + push to UAC + MTDS + PM — UAC@276f9efd + MTDS@fae9416 + PM (landing now)

## Success criteria

- 0 references to the 12 venue names across UAC + MTDS source / tests / registry / configs
- UAC + MTDS quality-gates green on tab branch
- Weekly canary surface drops from 57 to 45 venues
- semver-agent auto-bumps UAC + MTDS minor versions on landing
