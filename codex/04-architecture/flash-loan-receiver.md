---
scope: [engineer, admin]
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

| Chain   | Chain ID | Address                                      | Aave Pool                                    |
| ------- | -------- | -------------------------------------------- | -------------------------------------------- |
| Sepolia | 11155111 | `0x480c9142C51A477e0D8A17E032463d81A3b611BA` | `0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951` |
| Mainnet | 1        | `0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c` | `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` |

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
