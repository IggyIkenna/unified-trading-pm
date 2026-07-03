---
doc_type: plan
title: UAC Residual Plan Expansion
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-14'
overview: Expand the UAC residual plan with full provider manifest schema (testnet, data_type, keys checklist), SSOT alignment, cursor rules, and API contracts docs. Verify superseded plans are archived. Single consolidated plan for all remaining UAC refactors.
todos: []
isProject: false
---

# UAC Residual Plan Expansion and Consolidation

## Verification (Already Done)

- **Superseded plans archived:** `uac_nested_domain_deviations_9a5e89ee` and `uac_package_reorganization_c1c0734e` are
  in `unified-trading-pm/plans/archive/` and no longer in `plans/active/`.
- **Symlink:** `.cursor/plans` -> `../unified-trading-pm/plans/active` — archiving from PM active removes them from
  `.cursor/plans` as well.

---

## 1. Expand Residual Plan Phase 3 (Provider Manifest)

Edit
[unified-trading-pm/plans/active/uac_residual_refactors_provider_manifest_2026_03_14.md](unified-trading-pm/plans/active/uac_residual_refactors_provider_manifest_2026_03_14.md)
to add:

### 1.1 Detailed Schema Table (replace current Phase 3 bullets)

| Field                  | Type   | Description                                   |
| ---------------------- | ------ | --------------------------------------------- |
| `has_testnet`          | bool   | Provider offers testnet/sandbox               |
| `testnet_keys_we_have` | bool   | We have testnet credentials in Secret Manager |
| `testnet_network`      | str    | e.g. `sepolia`, `testnet.binance.vision`      |
| `data_type`            | enum   | `central`                                     |
| `keys_public_we_have`  | bool   | At least one public/central key in SM         |
| `keys_private_we_have` | bool   | At least one private key in SM                |
| `secret_names`         | object | `{ public: [str], private: [str] }`           |

**Data type definitions:**

- **central:** One API key for all. Public data (market, reference). No per-client keys.
- **private:** Positions, orders, account data. Per-client API keys required.
- **both:** Provider has both (e.g. Binance: market + trading).

### 1.2 DeFi Testnet (align with defi_keys plan)

Reference
[defi_keys_data_integration_2026_03_13.md](unified-trading-pm/plans/active/defi_keys_data_integration_2026_03_13.md):
Sepolia (Alchemy), Tenderly fork RPC, Hyperliquid testnet, `wallet-dev-private-key`. Include in manifest with
`testnet_network` and `testnet_keys_we_have`.

### 1.3 Checklist Output

Generation script produces markdown table:
`provider | modes | has_testnet | testnet_keys | data_type | keys_public | keys_private | gap`.

### 1.4 New Todos

Add to the plan's `todos`:

- `manifest-cursor-rules`: Add cursor rule for provider manifest SSOT (API keys inventory).
- `manifest-api-contracts-docs`: Update unified-api-contracts docs (CONTRIBUTING, PACKAGE_LAYOUT) to reference provider
  manifest.
- `manifest-secret-check-script`: Add optional Secret Manager check to generation script; output checklist vs SM.

---

## 2. SSOT Alignment

**Single source:** `unified-api-contracts/unified_api_contracts/config/provider_api_versions.yaml` (or companion YAML if
schema grows large).

**Align and consolidate:**

- `DATA_SOURCE_TO_SECRET` (mappings in UAC or UMI)
- defi_keys plan Phase 1 secret lists
- Codex `07-security/secrets-management.md`
- Codex `10-audit/ssot-reference-mapping.md`
- Any scripts/docs doing API key inventories

**Audit:** Search codebase for "API key", "secret", "DATA_SOURCE" and ensure all point to provider manifest.

---

## 3. Cursor Rules

Add rule (or extend existing) in `.cursor/rules/` or `unified-trading-pm/.cursor/rules/`:

- Provider manifest is SSOT for API keys, testnet, and data_type.
- When adding a new provider or key, update `provider_api_versions.yaml` first.

---

## 4. API Contracts Docs

Update in `unified-api-contracts/`:

- `CONTRIBUTING.md` or equivalent: reference provider manifest for key inventory.
- `docs/PACKAGE_LAYOUT_AND_SCOPE.md`: mention provider manifest location and purpose.

---

## 5. Generation Script Extension

Extend `generate_data_source_modes.py` (or equivalent) to:

- Read new fields: `has_testnet`, `testnet_keys_we_have`, `data_type`, `keys_public_we_have`, `keys_private_we_have`,
  `secret_names`.
- Emit checklist table (can use context7 to determine which providers have testnets).
- Optional: `--check-secrets` flag to verify `secret_names` entries exist in GCP Secret Manager.

---

## 6. INDEX.md Update

Add to supersession map in [unified-trading-pm/plans/active/INDEX.md](unified-trading-pm/plans/active/INDEX.md):

| Archived Plan                         | → New Plan |
| ------------------------------------- | ---------- |
| uac_nested_domain_deviations_9a5e89ee | Plan 6     |
| uac_package_reorganization_c1c0734e   | Plan 6     |

---

## 7. No Conflicts

- Phase 1 (Sports/DeFi nesting) and Phase 2 (Reference data) remain as-is.
- Phase 3 expansion is additive; defi_keys plan remains the authority for secret provisioning; residual plan's manifest
  is the schema and checklist SSOT.
- No second reorganization: one canonical structure, one manifest.

---

## Execution Order

1. Edit residual plan (Phase 3 expansion + new todos).
2. Update INDEX supersession map.
3. Implement schema changes in `provider_api_versions.yaml` (when executing).
4. Extend generation script.
5. Add cursor rule.
6. Update Codex and UAC docs.
7. Audit and consolidate inventories.
