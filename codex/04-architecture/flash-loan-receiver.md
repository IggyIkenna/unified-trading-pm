---
doc_type: codex-ssot
title: Flash Loan Receiver Contract
summary:
  Two Aave-V3 flash-loan callback contracts — passthrough FlashLoanReceiver (approve-repay only) and action-encoding
  RecursiveLeverageReceiver (whitelisted target/selector loop) — with deployed addresses, security model, and
  resolution.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [defi, execution, migration, verification]
related:
  [
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/15-runbooks/recursive-leverage-receiver-deploy-runbook.md,
    /codex/04-architecture/defi-phase3-infrastructure.md,
  ]
created: 2026-03-27
authoritative_for: [FlashLoanReceiver and RecursiveLeverageReceiver contract architecture]
referenced_by:
  [
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/04-architecture/cefi-perp-leg-bybit.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/04-architecture/mev-protection.md,
    /codex/15-runbooks/recursive-leverage-receiver-deploy-runbook.md,
    /codex/04-architecture/strategy-service-architecture.md,
    /codex/04-architecture/tenderly-execution-provider.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Flash Loan Receiver Contract

## What It Is

A minimal Solidity contract deployed once per chain that acts as the callback target for Aave V3 flash loans. Aave's
`Pool.flashLoan()` requires a receiver contract implementing `executeOperation()` — an externally-owned account
(EOA/wallet) cannot receive flash loans directly.

The contract does one thing: approve the Aave Pool to reclaim the borrowed amount + premium.

## Security

Two immutable access controls, set at deploy time:

- `msg.sender == POOL` — only the Aave V3 Pool contract can call `executeOperation()`
- `initiator == OWNER` — only our wallet can trigger a flash loan through this receiver

Custom errors (`UnauthorizedCaller`, `UnauthorizedInitiator`) revert with the offending address for diagnostics.

The contract is immutable — no admin functions, no proxy, no upgradability. Deploy once, use forever.

## Source Location

```
deployment-service/contracts/FlashLoanReceiver.sol
```

## Deployed Addresses

| Chain   | Chain ID | Address                                                                                                                                                                   | Aave Pool                                    |
| ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Sepolia | 11155111 | `0x480c9142C51A477e0D8A17E032463d81A3b611BA`                                                                                                                              | `0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951` |
| Holesky | 17000    | `0x480c9142C51A477e0D8A17E032463d81A3b611BA` (same receiver address as Sepolia per UAC `testnet_contracts.yaml` comment; refreshed 2026-05-12 per slot 8 exec audit EX-4) | (per UAC `testnet_contracts.yaml`)           |
| Mainnet | 1        | `0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c`                                                                                                                              | `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` |

> **Fork-chain-id convention reconciliation (codex audit EX-4 2026-05-12)**: Tenderly fork deployments use the aliased
> chain-id from `FORK_CHAIN_IDS` (== `MAINNET_CHAIN_IDS` per
> [`execution-modes-and-chain-resolution.md`](./execution-modes-and-chain-resolution.md) § "Chain Resolution"). For
> Ethereum mainnet fork the canonical fork chain-id is `1`, NOT `73571`. The `chain-id 73571` flag in the deployment
> script below predates the alias convention + is retained only for legacy Tenderly fork-IDs operators may carry over;
> new deployments use the canonical aliased chain-id from `MAINNET_CHAIN_IDS`.

Addresses are registered in:

- UAC: `config/testnet_contracts.yaml` under `{chain_id}.aave_v3.flash_loan_receiver`
- SM: `flash-loan-receiver-sepolia` (for Sepolia)

## Deployment

```bash
# Sepolia
bash deployment-service/scripts/deploy-flash-loan-receiver.sh --chain sepolia

# Mainnet (when ready)
bash deployment-service/scripts/deploy-flash-loan-receiver.sh --chain mainnet

# Tenderly fork (CI)
bash deployment-service/scripts/deploy-flash-loan-receiver.sh \
  --rpc-url "$FORK_RPC" --chain-id 73571 --private-key "$KEY"
```

The script compiles with solc 0.8.20, deploys via Web3, verifies bytecode on-chain, and outputs the address.

## Runtime Resolution

execution-service DeFi connector `AAVEConnector.connect()` resolves the receiver address:

1. `config["flash_loan_receiver"]` (explicit override)
2. UAC `testnet_contracts[chain_id].aave_v3.flash_loan_receiver` (registry lookup)

Then validates on-chain: `eth_getCode(address)` must return non-empty bytecode.

**Fail-loud behavior:**

- No address configured at all: `ValueError` at `connect()` — service won't start
- Address configured but no bytecode on-chain: `ValueError` at `connect()` — contract not deployed
- Both include the deploy command and this doc in the error message

## Modes

| Mode              | Contract Needed? | Behavior                                                           |
| ----------------- | ---------------- | ------------------------------------------------------------------ |
| Backtest          | No               | `flash_loan_simulator.py` in execution-service simulates in-memory |
| Paper trade       | No               | Signs but doesn't broadcast                                        |
| Testnet (Sepolia) | Yes              | Pre-deployed, address in UAC                                       |
| Tenderly fork     | Yes              | CI deploys fresh per fork via deploy script                        |
| Live (mainnet)    | Yes              | Pre-deployed, verified, address in UAC                             |

## CI Integration

```yaml
# integration-test.yml
- name: Deploy flash loan receiver to fork
  run: |
    bash deployment-service/scripts/deploy-flash-loan-receiver.sh \
      --rpc-url "$FORK_RPC" --chain-id 73571 --private-key "$WALLET_KEY"

- name: Run DeFi integration tests
  env:
    FLASH_LOAN_RECEIVER: $(cat /tmp/receiver-address.txt)
    DEFI_RPC_URL: ${{ env.FORK_RPC }}
  run: |
    cd execution-service && bash scripts/quality-gates.sh  # DeFi adapters live in execution-service (UDEI archived 2026-05-08)
```

## Owner

| Concern              | Owner                                     |
| -------------------- | ----------------------------------------- |
| Solidity source      | deployment-service                        |
| Deployment to chains | deployment-service                        |
| Address registry     | UAC testnet_contracts.yaml                |
| Preflight validation | execution-service AAVEConnector.connect() |
| Backtest simulation  | execution-service flash_loan_simulator.py |

---

## Extended receiver — RecursiveLeverageReceiver (action-encoder, Phase 4)

### Why a second contract?

The passthrough `FlashLoanReceiver` cannot execute supply/borrow/swap inside `executeOperation()` — it only approves
repayment. For atomic recursive-borrow opening (Family 1 + Family 2 of
[`defi_recursive_borrow_archetypes_2026_05_10.md`](../../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md)),
the receiver must loop through an encoded action sequence (`bytes[]`) calling Aave Pool / UniswapV3 Router / WETH9
inside the callback. The two contracts coexist:

- `FlashLoanReceiver` — passthrough. Used by liquidation-capture archetypes that don't recurse.
- `RecursiveLeverageReceiver` — action-encoder. Used by `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_BASIS_PERP_INV`
  orchestrators.

### Source location

```
deployment-service/contracts/RecursiveLeverageReceiver.sol
```

### Security model

Tighter than the passthrough — three layers:

1. `msg.sender == POOL` + `initiator == OWNER` (same as passthrough)
2. Target whitelist: only `pool`, `uniswapRouter`, `weth9` addresses (set at deploy time, immutable)
3. Selector whitelist: only `supply` / `borrow` / `repay` / `withdraw` (Aave) + `exactInputSingle` / `exactOutputSingle`
   (Uniswap V3) + `deposit` / `withdraw` (WETH9)
4. `nonReentrant` modifier on the `executeOperation` entrypoint
5. Owner-only `sweep(token, recipient)` for accidental token transfers

Custom errors: `TargetNotAllowed`, `SelectorNotAllowed`, `ActionFailed(idx)`,
`InsufficientRepaymentBalance(owed, balance)`, `ReentrancyDetected`.

### Constructor signature

```solidity
constructor(address pool, address uniswapRouter, address weth9)
```

The three addresses are checksum-validated then stored as immutables — re-deployment required to change any of them.

### Deployed addresses

| Chain    | Chain ID | Address                                                                                                                         | Deploy commit | Tx                                                                                                                    |
| -------- | -------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------- |
| Sepolia  | 11155111 | [`0x668BC0C59F434D7cE2498416E7eF9095b840c7cF`](https://sepolia.etherscan.io/address/0x668BC0C59F434D7cE2498416E7eF9095b840c7cF) | `602feaf`     | [`0x5c299e9f...`](https://sepolia.etherscan.io/tx/0x5c299e9f3e64c5179d81b8e26a695ab4f12392064f416ee22df205b0492aeab6) |
| Mainnet  | 1        | _pending — deploy via `deploy-recursive-leverage-receiver.sh --chain ethereum`_                                                 | _pending_     | _pending_                                                                                                             |
| Base     | 8453     | _pending — deploy via `deploy-recursive-leverage-receiver.sh --chain base`_                                                     | _pending_     | _pending_                                                                                                             |
| Tenderly | 1 (fork) | _per-fork ephemeral — written to `e2e-testing/scripts/configs/tenderly.env` by `setup-tenderly.sh`_                             | _per-fork_    | _per-fork_                                                                                                            |

Addresses are registered in:

- **UAC**: `unified_api_contracts/internal/architecture_v2/flash_loan_receiver.py` `FLASH_LOAN_RECEIVER_REGISTRY`
  (filter `receiver_kind="recursive_leverage"`)
- **Secret Manager**: `recursive-leverage-receiver-sepolia` in `central-element-323112`
- **Tenderly fork**: written to `e2e-testing/scripts/configs/tenderly.env` as
  `RECURSIVE_LEVERAGE_RECEIVER_TENDERLY=0x...`

### Deployment runbook

```bash
# Sepolia — credentials auto-fetched from Secret Manager
cd deployment-service
source .venv/bin/activate
bash scripts/deploy-recursive-leverage-receiver.sh --chain sepolia

# Mainnet — same shape, ≥0.05 ETH required in wallet
bash scripts/deploy-recursive-leverage-receiver.sh --chain ethereum

# Base — same shape, ≥0.02 ETH on Base required
bash scripts/deploy-recursive-leverage-receiver.sh --chain base

# Tenderly fork — explicit RPC + private key, mainnet pool/weth/router
bash scripts/deploy-recursive-leverage-receiver.sh \
  --rpc-url "$TENDERLY_FORK_RPC_URL" \
  --chain-id 1 \
  --private-key "$DEFI_WALLET_PRIVATE_KEY" \
  --pool-address "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2" \
  --weth-address "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" \
  --swap-router-address "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
```

The shell wrapper calls `scripts/deploy_contract.py --contract RecursiveLeverageReceiver` which:

1. Compiles with solc 0.8.20, evm_version=paris (broad compat — no PUSH0)
2. Sends EIP-1559 deploy tx (maxFee = 2× baseFee + 2 gwei priority)
3. Waits 300s for receipt
4. Verifies bytecode present at deployed address via `eth_getCode`
5. Writes address to `--output` file + stdout

After deploy, copy the address into:

1. The Secret Manager secret for that chain (`recursive-leverage-receiver-<chain>`)
2. `FLASH_LOAN_RECEIVER_REGISTRY` row for that chain (replace placeholder; commit + push)

### Runtime resolution (executor-side)

`RecursiveLoopOrchestrator.flash_open()` resolves the address by:

1. Query `FLASH_LOAN_RECEIVER_REGISTRY` filtered by `(chain, protocol=AAVE_V3, receiver_kind=recursive_leverage)`
2. Validate on-chain: `eth_getCode(address)` non-empty
3. Use as `params.receiver` in `Pool.flashLoan(receiver, assets, amounts, modes, onBehalfOf, params, referralCode)`

If no row matches or bytecode missing → raises `RECURSIVE_RECEIVER_NOT_DEPLOYED` (FAIL prefix in `DefiErrorCode`
taxonomy).

### CI integration

```yaml
# In integration-test.yml — Tenderly fork stage
- name: Setup Tenderly fork + deploy both receivers
  run: bash e2e-testing/scripts/defi/setup-tenderly.sh
  # Deploys FlashLoanReceiver AND RecursiveLeverageReceiver; addresses
  # written to e2e-testing/scripts/configs/tenderly.env

- name: Run recursive-borrow integration tests
  env:
    TENDERLY_RPC_URL: ${{ steps.setup.outputs.rpc }}
    RECURSIVE_LEVERAGE_RECEIVER: ${{ steps.setup.outputs.recursive_addr }}
  run: |
    cd execution-service && bash scripts/quality-gates.sh
```

### Verification commands

```bash
# Check deployed contract state via Web3 (after deploy)
python3 -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://eth-sepolia.g.alchemy.com/v2/\$ALCHEMY'))
addr = '0x668BC0C59F434D7cE2498416E7eF9095b840c7cF'
abi = [
  {'inputs': [], 'name': 'OWNER', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
  {'inputs': [], 'name': 'POOL', 'outputs': [{'type': 'address'}], 'stateMutability': 'view', 'type': 'function'},
]
c = w3.eth.contract(address=addr, abi=abi)
print('OWNER:', c.functions.OWNER().call())
print('POOL :', c.functions.POOL().call())
"
```

Expected: `OWNER` matches the deploy wallet (`0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f` for our setup); `POOL` matches
the chain-specific Aave V3 pool.

### Plan reference

- Phase 4 of
  [`defi_recursive_borrow_archetypes_2026_05_10.md`](../../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md)
- See also
  [`/codex/15-runbooks/recursive-leverage-receiver-deploy-runbook.md`](/codex/15-runbooks/recursive-leverage-receiver-deploy-runbook.md)
  for the full operator runbook (owner / cadence / verifier / last_executed metadata).
