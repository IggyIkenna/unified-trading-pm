---
doc_type: plan
title: venue-axis-asset-group-vocabulary-2026-04-25
summary: 'Align code and docs on the trading **venue axis** vocabulary: **asset group** (CeFi / DeFi / TradFi / Sports /
  Prediction)

  with UAC SSOT dict keys unchanged (`cefi`, `defi`, …). Waves A–B shipped in UAC, UTL, MDPS, MTDS; remaining waves cover

  features services, execution consumer JSON keys, and deployment/SIT parity. Agent context lives in

  `unified-trading-pm/cursor-configs/CLAUDE.md` + this plan.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-service, e2e-testing, execution-service, instruments-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-25"
type: mixed
epic: epic-code-completion
archived_on: 2026-05-07
archive_reason:
  5 main vocabulary waves (A/B/C/D/E) shipped; 3 absorbed items folded into infrastructure_master + defi_master
  umbrellas
completion_gates: { code: C3, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C5, deployment: none, business: none }
  - { repo: unified-trading-library, code: C5, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C5, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C5, deployment: none, business: none }
  - { repo: unified-trading-api, code: C1, deployment: none, business: none }
  - { repo: instruments-service, code: C1, deployment: none, business: none }
depends_on: []
isProject: false
---

> **ARCHIVED 2026-05-07** — 5 main vocabulary waves (A/B/C/D/E) shipped per CLAUDE.md "Asset-group vocabulary" section.
> The 3 remaining absorbed items folded into:
>
> - `venue_start_dates` deletion →
>   [`infrastructure_master_2026_05_07.md`](../active/infrastructure_master_2026_05_07.md) § "VenueMapping
>   `venue_start_dates` cleanup"
> - Data-status dashboard SSOT verify →
>   [`infrastructure_master_2026_05_07.md`](../active/infrastructure_master_2026_05_07.md) § "VenueMapping
>   `venue_start_dates` cleanup" (paired with deletion)
> - `poolGetSnapshots` historical TVL → [`defi_master_2026_05_07.md`](../active/defi_master_2026_05_07.md) § "Tail-chain
>   / mid-tier protocol coverage"
>
> Each folded item carries a `(folded from venue_axis_asset_group_vocabulary_2026_04_25)` traceability suffix. This file
> is the historical SSOT for the asset_group vocabulary migration.

# Venue axis (asset group) vocabulary

## Codex SSOTs

This plan implements / extends the following SSOT documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) § "Asset-group vocabulary" — primary SSOT for the
  vocabulary rules (CLI flag `--asset-group`, env vars `VM_ASSET_GROUP` / `MDPS_ASSET_GROUP`, Python symbols
  `VENUES_BY_ASSET_GROUP` / `DATA_TYPES_BY_ASSET_GROUP` / `MarketAssetGroup`, hive-key `asset_group=` canonical vs
  legacy `category=`, the lowercase dict-key exception)
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  manifest hive partition keys (`asset_group=` canonical, `category=` legacy) + reader fallback discipline
- [`/codex/02-data/per-category-bucket-layouts.md`](/codex/02-data/per-category-bucket-layouts.md) — per-asset-group
  bucket layout + path templates the vocabulary touches

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 3 of 3 unchecked todos (all 3 are `Absorbed from sibling plans (2026-05-06)` items)
- **Mis-marked DONE -> flipped**: 0 — Waves A/B/C/D/E all already correctly marked `[x]` per CLAUDE.md
- **In-flight (running VMs)**: none gated by this plan
- **Blocked by**: none
- **Blocks**: nothing critical — Wave C/D consumer-side keys already shipped per checked items
- **Last meaningful commits**: UAC `068ce07` (clean break) -> features-\* 8-service Wave C
  (`7ded56e`/`818375e`/`95f8adb`/`2889de3`/`1797f32`+`a2032ca`/`5daba09e`/`2625996`/`9930b60`+`efce89f`) ->
  execution/strategy/PBM Wave D (`46dd6f67`/`335b666`/`a874b34`/`8ae32182`); deployment-service VM_ASSET_GROUP env vars
  verified live across 14+ launchers
- **Recommendation**: ARCHIVE-READY after the 3 absorbed items resolve. All 5 main waves (A/B/C/D/E) confirmed shipped —
  UAC clean break verified (`grep VENUE_TO_CATEGORY` shows only `check_uac_adoption.py` legacy-detector rule + tests).
  The 3 remaining unchecked todos are absorbed from `venue_availability_ssot_2026_03_25` (which is archived). Suggest
  folding those 3 into the asset_group umbrellas (`defi_master_2026_05_07` for the `poolGetSnapshots` DeFi item;
  `infrastructure_master_2026_05_07` for the `venue_start_dates` deletion + dashboard SSOT items) and archiving this
  plan, since CLAUDE.md already documents the `asset_group` vocabulary as the canonical workspace rule.
- **Anomalies**: `venue_start_dates` still referenced in `deployment-service/tests/conftest.py` +
  `deployment-service/tests/unit/test_shard_calculator.py` + `test_shard_optimization.py` (8+ test sites) — confirms
  `[ ] P0 Delete venue_start_dates from VenueMapping` is still actionable. Cross-cutting impact lives in
  deployment-service shard-calculator tests, not in core SSOT.

**SSOT (data):** `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`

- Legacy names — `VENUES_BY_CATEGORY`, `DATA_TYPES_BY_CATEGORY`, `VENUE_TO_CATEGORY` (dict keys remain `cefi` / `defi` /
  `tradfi` / `sports` / `prediction`).
- Preferred aliases (identity) — `VENUES_BY_ASSET_GROUP`, `DATA_TYPES_BY_ASSET_GROUP`, `VENUE_TO_ASSET_GROUP`.

**UTL:** `get_bucket_for_asset_group` in `unified_trading_library.config_interface` (delegates to
`get_bucket_for_category`).

**MDPS:** `MarketAssetGroup` enum; `get_asset_group_for_venue`, `get_asset_groups_for_data_type`;
`MarketDataProcessingServiceConfig.get_bucket_for_asset_group`.

**MTDS:** `VENUE_TO_ASSET_GROUP` import; `get_tick_data_bucket(..., asset_group=...)`; GCS path segments may still use
`category=` in blob prefixes (layout SSOT) — do not rename wire paths in a doc-only pass.

## Todos

### Done (Waves A–B + agent SSOT)

- [x] [AGENT] UAC: add `VENUES_BY_ASSET_GROUP` / `DATA_TYPES_BY_ASSET_GROUP` / `VENUE_TO_ASSET_GROUP` aliases; export
      from `unified_api_contracts` + `registry`.
- [x] [AGENT] UTL: `get_bucket_for_asset_group`; export from `config_interface`.
- [x] [AGENT] MDPS: `MarketAssetGroup` + renames; config path helpers use `asset_group` where applicable.
- [x] [AGENT] MTDS: `VENUE_TO_ASSET_GROUP`; `get_tick_data_bucket` parameter `asset_group`.
- [x] [AGENT] UTL: `FreshnessMonitor` event details use `DataFreshnessContract.asset_class` (not a non-existent
      `asset_group` field).
- [x] [AGENT] UAC: `ProviderDataAvailability` field `category` → `asset_group`; `get_expected_trading_dates` uses
      `VENUE_TO_ASSET_GROUP`; workspace `VENUE_TO_CATEGORY` import sites migrated to `VENUE_TO_ASSET_GROUP`
      (definition + re-exports unchanged in `market_data_categories.py`).
- [x] [AGENT] PM: this plan; `plans/active/INDEX.md`; `unified-trading-pm/AGENTS.md`;
      `unified-trading-pm/cursor-configs/CLAUDE.md`; `.cursor/skills/workspace-context-inject/SKILL.md`.

### Remaining (Waves C–D — follow-on)

- [x] [AGENT] Wave C: features-\* services — align local names / imports to `VENUE_TO_ASSET_GROUP` and asset-group
      language where the trading venue axis applies; keep on-disk / JSON keys stable where required. **Shipped
      2026-04-28** in dependency order: Wave A (UAC `068ce07` — clean break of `VENUE_TO_CATEGORY` /
      `VENUES_BY_CATEGORY` / `DATA_TYPES_BY_CATEGORY` / `VALID_CATEGORIES`); Wave B (UTL `d3c8880d` — `ServiceCLI` kwarg
      flip `categories=` → `asset_group_choices=`, F821 leftover fixed); Wave C across 8 services in parallel:
      features-cross-instrument-service `7ded56e`, features-delta-one-service `818375e`, features-onchain-service
      `95f8adb`, features-sports-service `2889de3`, features-volatility-service `1797f32`+`a2032ca`,
      features-multi-timeframe-service `5daba09e`, features-commodity-service `2625996`, features-calendar-service
      `9930b60`+`efce89f`. PM follow-up: `generate_ui_reference_data.py` flipped `VALID_CATEGORIES` →
      `VALID_ASSET_GROUPS`.
- [x] [AGENT] Wave D: execution-service / consumers — grid and CLI JSON keys: document vs migrate per
      `no-backward-compat` policy and coordinated UAC SemVer. (5 migrated + 4 documented; below 5-consumer escalation
      threshold so per-consumer migration was correct. execution-service `46dd6f67`, strategy-service `335b666`,
      position-balance-monitor-service `a874b34`, PM SSOT-BOUNDARY `8ae32182`.)

### Done (Wave E — deployment env vars, 2026-04-25)

- [x] [AGENT] Wave E: deployment-service VM env vars renamed `VM_CATEGORY` → `VM_ASSET_GROUP` across 25 shell scripts
      (`scripts/vm/launch-*.sh`, `setup-data-pipeline-vm.sh`, `vm-exec-with-gcs-tee.sh`, `backfill-cluster.sh`,
      `create-code-tarballs.sh`). Read-side compat (`${VM_ASSET_GROUP:-${VM_CATEGORY:-UNKNOWN}}`) carried in
      `setup-data-pipeline-vm.sh` + `vm-exec-with-gcs-tee.sh` so any straggler launchers keep working during transition.
      MDPS env var `MDPS_CATEGORY` → `MDPS_ASSET_GROUP` (Python `cli/main.py` accepts both with new name preferred).
      `e2e-testing/configs/defi/*.env` `CATEGORY=DEFI` → `ASSET_GROUP=DEFI`. Local bash `CATEGORY` variables across
      `instruments-service/scripts/`, `market-tick-data-service/scripts/`, `e2e-testing/scripts/` renamed to
      `ASSET_GROUP` for consistency. GCS path segments (e.g. `category=cefi/...` blob prefixes) intentionally retained
      as wire-format SSOT. GCE labels (`--labels=category="${cat}"`) intentionally retained — searchable resource tags,
      separate concern. Operator note: all Wave-E-affected VMs were stopped + deleted before rollout, so no live VM
      registry rows reference the old name; new launches use the new name only.

## Absorbed from sibling plans (2026-05-06)

Items folded in from `venue_availability_ssot_2026_03_25` (since archived). The asset-group vocabulary cluster lead
absorbs the venue-axis SSOT cleanup items:

- [ ] [AGENT] P0. Delete `venue_start_dates` from `VenueMapping` (old format) — replace with the canonical venue+date
      shape (per the source plan's design doc). [AUDIT 2026-05-07: FRESH — actionable; 8+ deployment-service test sites
      still reference `venue_start_dates` (`tests/conftest.py:392`,
      `tests/unit/test_shard_calculator.py:486/513/543/577/623`, `test_shard_optimization.py:80/107/137/171`); deletion
      is a real ~10-file change; consider folding into `infrastructure_master_2026_05_07`]
- [ ] [AGENT] P1. Use `poolGetSnapshots` for historical TVL when querying past dates (DeFi pool query path). [AUDIT
      2026-05-07: FRESH — actionable; `grep poolGetSnapshots` returns 0 hits in workspace, confirming this DeFi-pool
      query path migration has not yet shipped; consider folding into `defi_master_2026_05_07`]
- [ ] [AGENT] P2. Data-status dashboard checks against same SSOT — confirm dashboard reads venue start dates from the
      canonical source post-cleanup. [AUDIT 2026-05-07: BLOCKED-ON venue_axis:absorbed-item-1; cannot verify dashboard
      SSOT consumption until `venue_start_dates` is deleted from VenueMapping]

## References

- `unified-trading-pm/cursor-configs/CLAUDE.md` — “Venue axis (trading) SSOT” bullet (shared by symlinked service
  `CLAUDE.md`).
