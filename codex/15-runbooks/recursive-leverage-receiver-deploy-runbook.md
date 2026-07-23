---
doc_type: codex-runbook
title: RecursiveLeverageReceiver — Deploy Runbook
summary:
  Operator runbook to deploy the Phase-4 RecursiveLeverageReceiver.sol to a target chain (Sepolia/Ethereum/Base/Tenderly
  fork) and register it — pre-deploy checklist, deploy commands, the 4 mandatory post-deploy steps (capture address →
  write Secret Manager → update UAC FLASH_LOAN_RECEIVER_REGISTRY → Web3 verify OWNER/POOL), known Sepolia deploy, and
  failure-mode troubleshooting.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, execution, runbook, deployment, uac]
related: [/codex/04-architecture/flash-loan-receiver.md]
created: 2026-05-15
authoritative_for: [RecursiveLeverageReceiver deploy runbook]
referenced_by: [/codex/04-architecture/flash-loan-receiver.md]
owner: slot-2-ikenna
last_reviewed: 2026-05-17
code_refs:
execution:
  {
    owner: slot-2-ikenna,
    cadence: one-shot-per-chain (Sepolia + Ethereum + Base) + per-Tenderly-fork,
    verifier: execution-service `AAVEConnector.connect()` + `eth_getCode` preflight,
    last_executed: 2026-05-15 (Sepolia),
  }
cadence: one-shot-per-chain (Sepolia + Ethereum + Base) + per-Tenderly-fork
verifier: execution-service `AAVEConnector.connect()` + `eth_getCode` preflight
last_executed: 2026-05-15 (Sepolia)
---

# RecursiveLeverageReceiver — Deploy Runbook

Operator runbook for deploying the Phase 4 `RecursiveLeverageReceiver.sol` (action-encoder pattern) to a target chain
and registering the address in UAC + Secret Manager.

Companion SSOT to [`/codex/04-architecture/flash-loan-receiver.md`](/codex/04-architecture/flash-loan-receiver.md) §
"Extended receiver".

## Pre-deploy checklist

| Item                            | Sepolia        | Ethereum mainnet | Base mainnet   | Tenderly fork             |
| ------------------------------- | -------------- | ---------------- | -------------- | ------------------------- |
| Wallet balance ≥ deploy gas     | ≥0.02 ETH      | ≥0.05 ETH        | ≥0.02 ETH      | n/a (auto-funded 100 ETH) |
| `defi-wallet-private-key` in SM | ✅ exists      | ✅ exists        | ✅ exists      | ✅ same wallet            |
| `alchemy-api-key` in SM         | ✅ exists      | ✅ exists        | ✅ exists      | n/a (uses Tenderly RPC)   |
| `tenderly-fork-rpc-url` in SM   | n/a            | n/a              | n/a            | ✅ exists                 |
| `solcx` + `web3` in venv        | ✅             | ✅               | ✅             | ✅                        |
| Aave V3 Pool address verified   | ✅ `0x6Ae4...` | ✅ `0x8787...`   | ✅ `0xA238...` | ✅ same as mainnet        |
| Existing deploy on chain?       | ✅ `0x668B...` | ❌               | ❌             | per-fork ephemeral        |

## Deploy commands

```bash
cd deployment-service
source .venv/bin/activate

# Sepolia (auto-fetches creds from Secret Manager)
bash scripts/deploy-recursive-leverage-receiver.sh --chain sepolia

# Ethereum mainnet
bash scripts/deploy-recursive-leverage-receiver.sh --chain ethereum

# Base mainnet
bash scripts/deploy-recursive-leverage-receiver.sh --chain base

# Tenderly fork (mainnet-mirroring)
bash scripts/deploy-recursive-leverage-receiver.sh \
  --rpc-url "$(gcloud secrets versions access latest --secret=tenderly-fork-rpc-url --project=central-element-323112)" \
  --chain-id 1 \
  --private-key "$(gcloud secrets versions access latest --secret=defi-wallet-private-key --project=central-element-323112)" \
  --pool-address "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2" \
  --weth-address "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" \
  --swap-router-address "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
```

## Post-deploy steps (MANDATORY)

After every successful deploy, run **all four** in sequence:

### 1. Capture the deployed address

```bash
DEPLOYED_ADDR=$(cat /tmp/recursive-leverage-receiver-address.txt)
echo "Deployed: $DEPLOYED_ADDR"
```

### 2. Write to Secret Manager

```bash
# Sepolia
echo -n "$DEPLOYED_ADDR" | gcloud secrets create recursive-leverage-receiver-sepolia \
  --project=central-element-323112 --data-file=-

# Mainnet (after audit clears)
echo -n "$DEPLOYED_ADDR" | gcloud secrets create recursive-leverage-receiver-mainnet \
  --project=central-element-323112 --data-file=-

# Base (after audit clears)
echo -n "$DEPLOYED_ADDR" | gcloud secrets create recursive-leverage-receiver-base \
  --project=central-element-323112 --data-file=-

# If secret already exists, add a new version instead:
echo -n "$DEPLOYED_ADDR" | gcloud secrets versions add recursive-leverage-receiver-<chain> \
  --project=central-element-323112 --data-file=-
```

### 3. Update UAC `FLASH_LOAN_RECEIVER_REGISTRY`

Edit `unified-api-contracts/unified_api_contracts/internal/architecture_v2/flash_loan_receiver.py`. Replace the
placeholder row for that chain with the actual deploy data:

```python
FlashLoanReceiverDeployment(
    chain="<CHAIN>",
    protocol=FlashLoanProtocol.AAVE_V3,
    receiver_kind="recursive_leverage",
    receiver_address="<DEPLOYED_ADDR>",
    deployment_commit_sha="<deployment-service sha>",
    deployed_at_utc="<ISO-8601 timestamp>",
    supported_tokens=("WETH", "WSTETH", "WEETH", "CBETH"),
    notes="<chain> RecursiveLeverageReceiver. Pool=<pool>; "
    "SwapRouter02=<router>; WETH9=<weth9>. "
    "Deploy tx <tx_hash> (gas_used=<gas>). "
    "Etherscan: <etherscan-url>. "
    "Secret: recursive-leverage-receiver-<chain>.",
),
```

Commit + push to `live-defi-rollout`.

### 4. Verify on-chain state via Web3

```bash
ALCHEMY_KEY=$(gcloud secrets versions access latest --secret=alchemy-api-key --project=central-element-323112)
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_KEY}'))
addr = '$DEPLOYED_ADDR'
abi = [
  {'inputs': [], 'name': 'OWNER', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
  {'inputs': [], 'name': 'POOL', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
]
c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
print('OWNER:', c.functions.OWNER().call())
print('POOL :', c.functions.POOL().call())
"
```

Expected: `OWNER` = deploy wallet (`0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f`); `POOL` = chain-specific Aave V3.

## Known successful deploys

### Sepolia (2026-05-15)

```
Address:           0x668BC0C59F434D7cE2498416E7eF9095b840c7cF
Tx:                0x5c299e9f3e64c5179d81b8e26a695ab4f12392064f416ee22df205b0492aeab6
Gas used:          1,508,218
Deployer:          0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f
Pool:              0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951 (Aave V3 Sepolia)
SwapRouter02:      0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45
WETH9:             0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14
Bytecode size:     5,304 bytes
solc:              0.8.20, evm_version=paris
Etherscan:         https://sepolia.etherscan.io/address/0x668BC0C59F434D7cE2498416E7eF9095b840c7cF
Secret:            recursive-leverage-receiver-sepolia (central-element-323112) v1
Deploy commit SHA: deployment-service@602feaf
UAC registry SHA:  unified-api-contracts@468df51
```

## Failure modes + troubleshooting

| Symptom                                           | Cause                                                  | Fix                                                                                    |
| ------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `ImportError: No module named 'solcx'`            | venv missing deps                                      | `cd deployment-service && uv pip install web3 py-solc-x`                               |
| `Contract '...' not found in compiled output`     | Wrong `--contract` arg or wrong source file            | Verify file at `deployment-service/contracts/<Contract>.sol`; check class name matches |
| `Deployer wallet ... has zero balance`            | Wallet unfunded on target chain                        | Send testnet ETH from faucet (Sepolia: <https://sepoliafaucet.com>) or mainnet ETH     |
| `Deploy transaction reverted`                     | Constructor reverted (invalid address arg, ETH sent)   | Re-check `--pool-address` / `--weth-address` / `--swap-router-address`                 |
| `Bytecode verification failed: no code at <addr>` | Tx mined but contract self-destructed or address wrong | Investigate via `eth_getTransactionReceipt`; should never happen with this contract    |
| `Cannot connect to RPC endpoint`                  | Invalid Alchemy key or RPC URL                         | Verify `gcloud secrets versions access latest --secret=alchemy-api-key`                |
| Stuck pending > 300s                              | Gas underpriced or nonce conflict                      | Cancel via 0-value self-tx with same nonce + higher gas; rerun deploy                  |

## Owner/cadence/verifier (Runbook Execution-Owner SSOT)

| Field         | Value                                                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------- |
| Owner         | slot-2-ikenna (defi_recursive_borrow plan owner)                                                                 |
| Cadence       | One-shot per chain (Sepolia/Ethereum/Base) + per-Tenderly-fork (CI ephemeral). Re-deploy only if contract bumped |
| Verifier      | `execution-service AAVEConnector.connect()` runs `eth_getCode` preflight; raises if bytecode missing             |
| Last executed | 2026-05-15 Sepolia (deployment-service@602feaf)                                                                  |

## Plan reference

- Phase 4 of
  [`defi_recursive_borrow_archetypes_2026_05_10.md`](../../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md)
- Companion: [`/codex/04-architecture/flash-loan-receiver.md`](/codex/04-architecture/flash-loan-receiver.md)
  (passthrough sibling contract)
