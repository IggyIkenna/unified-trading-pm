---
name: defi_master_audit_instructions
type: audit-instructions
epic: defi_master
assigned_vm: vm-defi
tier: L0
last_updated: 2026-05-22
---

# DeFi Master — Audit Instructions

## Epic Scope

DeFi adapters, on-chain execution, Copper custody path, `carry_staked_basis` and `arbitrage_price_dispersion`
archetypes. Key code surfaces:

- LST APR adapters: Lido (stETH), RocketPool (rETH), Coinbase (cbETH), Solana JitoSOL, mSOL
- On-chain rate readers: Aave v3 / Compound v3 base rates
- DEX price feed adapters: Uniswap V3, Curve, Balancer, Sushi, PancakeSwap, Phoenix, Orca, Raydium, Drift
- On-chain execution: `UniswapConnector.swap_exact_input()` via SwapRouter02
- Flash loan: `deployment-service/contracts/FlashLoanReceiver.sol`
- Custody: `CLOUD_KMS_ENCRYPTED` path (May-23); Copper post-June-1
- Pyth oracle: Solana-only on-chain price feeds
- Chain RPC: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`
- Error classification: 30 `DefiErrorCode` values in UAC

## Triggers

- Weekly (minimum cadence)
- After any DeFi protocol version bump (Aave v4, Uniswap v4, etc.)
- After any new chain or LST is added to the universe
- When `manifest_master` audit surfaces new `empty_confirmed` rows for `asset_group=defi`
- When `batch_live_symmetry_master` audit surfaces adapter parity gaps for DeFi adapters

## Checklist

- [ ] (a) **30 DefiErrorCode coverage**: all 30 codes (13 Aave + 7 RECURSIVE*LOOP + 8 HL* + 2 ORACLE\_) present in UAC
      `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode`. Grep:
      `rg "DefiErrorCode" unified-api-contracts/ --include="*.py" | grep -c "="`

- [ ] (b) **CHAIN_RPC_TEMPLATES coverage**: every supported chain has an entry. Read:
      `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`

- [ ] (c) **TestnetContractRegistry**: validates `config/testnet_contracts.yaml` at load (no missing keys). Run:
      `cd execution-service && python -c "from unified_trading_library.config_interface.testnet_contracts import TestnetContractRegistry; TestnetContractRegistry()"`

- [ ] (d) **Batch + live adapter parity**: every LST APR adapter and DEX price adapter has both batch and live modes.
      Check: `a6_batch_live_adapter_parity.py` output for asset_group=defi rows

- [ ] (e) **FlashLoanReceiver.sol matches codex**: architecture description in
      `codex/04-architecture/flash-loan-receiver.md` matches the actual contract. Grep:
      `rg "FlashLoanReceiver" deployment-service/contracts/`

- [ ] (f) **No hardcoded RPC URLs**: QG `no_hardcoded_venue_urls.sh` passes for all DeFi service dirs. Run:
      `bash scripts/quality-gates/no_hardcoded_venue_urls.sh` in each affected service

- [ ] (g) **Archetype manifest rows**: `carry_staked_basis` and `arbitrage_price_dispersion` archetypes produce manifest
      rows with correct `schema_version`, `asset_group=defi`, and non-null `available_at`. Check: manifest divergence A3
      shows zero `MISSING_EXPECTED` for defi + these data_types

- [ ] (h) **No removed providers**: no imports of Elysium, Arkham, Bloxroute, or Infura anywhere. Grep:
      `rg "elysium|arkham|bloxroute|infura" --ignore-case unified-api-contracts/ execution-service/`

- [ ] (i) **Pyth oracle scope**: Pyth used for Solana on-chain only; other chains use Chainlink. Read:
      `codex/04-architecture/defi-execution-overview.md` and verify code matches

### E2E Batch, Paper, and Live Verification

- (e2e-batch) **Batch e2e**: For the MVP archetypes of this domain, run a dry-run batch audit using mock upstream
  fixtures (`CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local`) — confirm signals are generated end-to-end from adapter output
  through strategy. If real upstream unavailable, synthetic fixtures from `tests/e2e/fixtures/` suffice; the test MUST
  exercise the downstream code regardless of upstream readiness.
- (e2e-paper) **Paper trading audit** (once paper is running): confirm paper PnL events flow from strategy → execution →
  PnL calculator for ≥1 MVP archetype in this domain. Check manifest for strategy_output rows with
  `capture_status=captured` for the date range. If paper not yet running, verify the code path is wired (not
  BLOCKED-CREDENTIALS level — code exists, paper not started).
- (e2e-live) **Live trading audit** (once live is running): verify live execution produces execution_record rows in
  manifest with no DIVERGENT_EMPTY. Alert thresholds fire within SLA. PnL reported correctly.
- (mock-upstream) **Mock upstream pattern**: this domain's audit MUST be runnable WITHOUT live upstream data. Document
  the exact `pytest` fixtures or `CLOUD_MOCK_MODE=true` invocation in `## Output Format` so any slot can run the
  downstream-only audit independently.

## Success Criteria

- All 9 checklist items GREEN
- `a6_batch_live_adapter_parity.py` shows 100% parity for `asset_group=defi` rows
- Manifest divergence A3: zero `MISSING_EXPECTED` for defi asset_group
- QG exits 0 for all DeFi-touching services (execution-service, strategy-service)
- e2e batch audit produces signals for ≥1 MVP archetype using mock upstream data (CLOUD_MOCK_MODE=true green)
- Paper trading goal post: ≥1 archetype runs ≥7 continuous paper days without silent failures

## Output Format

Result file at `plans/audit/results/defi_master_audit_YYYY_MM_DD.md` must contain:

1. Frontmatter: `type: audit-result`, `epic: defi_master`, `instructions_ref: this file`, `auditor:`, `date:`, `status:`
2. Each checklist item: GREEN / AMBER / RED + grep output or script result as evidence
3. Gap items: `- [ ] [TYPE] P#. <description> — parent_epic: defi_master` for each RED/AMBER item
4. Table: `gap item | active plan absorbing it | plan status`
5. Archive condition: "Archives when all gap items below are `- [x]` in their parent plans"

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
