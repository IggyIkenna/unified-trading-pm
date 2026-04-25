---
name: venue-axis-asset-group-vocabulary-2026-04-25
overview: |
  Align code and docs on the trading **venue axis** vocabulary: **asset group** (CeFi / DeFi / TradFi / Sports / Prediction)
  with UAC SSOT dict keys unchanged (`cefi`, `defi`, …). Waves A–B shipped in UAC, UTL, MDPS, MTDS; remaining waves cover
  features services, execution consumer JSON keys, and deployment/SIT parity. Agent context lives in
  `unified-trading-pm/cursor-configs/CLAUDE.md` + this plan.
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C3
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C5
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C5
    deployment: none
    business: none
  - repo: market-data-processing-service
    code: C5
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C5
    deployment: none
    business: none
  - repo: unified-trading-api
    code: C1
    deployment: none
    business: none
  - repo: instruments-service
    code: C1
    deployment: none
    business: none

depends_on: []

isProject: false
---

# Venue axis (asset group) vocabulary

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

- [ ] [AGENT] Wave C: features-\* services — align local names / imports to `VENUE_TO_ASSET_GROUP` and asset-group
      language where the trading venue axis applies; keep on-disk / JSON keys stable where required.
- [ ] [AGENT] Wave D: execution-service / consumers — grid and CLI JSON keys: document vs migrate per
      `no-backward-compat` policy and coordinated UAC SemVer.

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

## References

- `unified-trading-pm/cursor-configs/CLAUDE.md` — “Venue axis (trading) SSOT” bullet (shared by symlinked service
  `CLAUDE.md`).
