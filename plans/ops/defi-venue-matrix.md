# DeFi Venue Matrix

Source: `unified-market-interface/unified_market_interface/factory.py` VENUE_REGISTRY (14 DeFi protocols).

## DeFi Venues

| Venue      | Protocol          | Chain(s)                                         | Testnet Endpoint                                    | Testnet Faucet                                    | Required Env Vars                               | Notes                                                 |
| ---------- | ----------------- | ------------------------------------------------ | --------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------- |
| aave_v3    | Aave V3           | Ethereum, Arbitrum, Optimism, Polygon, Avalanche | `https://app.aave.com/?marketName=proto_sepolia_v3` | [Sepolia Faucet](https://sepoliafaucet.com)       | `AAVE_RPC_URL`, `AAVE_WALLET_KEY`               | Lending/borrowing; flash loans available              |
| balancer   | Balancer V2       | Ethereum, Arbitrum, Polygon                      | `https://app.balancer.fi/#/sepolia`                 | [Sepolia Faucet](https://sepoliafaucet.com)       | `BALANCER_RPC_URL`, `BALANCER_VAULT_ADDRESS`    | Weighted pools, boosted pools                         |
| curve      | Curve Finance     | Ethereum, Arbitrum, Optimism                     | `https://sepolia.curve.fi`                          | [Sepolia Faucet](https://sepoliafaucet.com)       | `CURVE_RPC_URL`, `CURVE_REGISTRY_ADDRESS`       | StableSwap AMM; factory pools                         |
| ethena     | Ethena            | Ethereum                                         | `https://testnet.ethena.fi`                         | [Sepolia Faucet](https://sepoliafaucet.com)       | `ETHENA_RPC_URL`, `ETHENA_API_KEY`              | USDe synthetic dollar; sUSDe staking                  |
| euler      | Euler V2          | Ethereum                                         | `https://app.euler.finance` (Sepolia)               | [Sepolia Faucet](https://sepoliafaucet.com)       | `EULER_RPC_URL`, `EULER_WALLET_KEY`             | Modular lending protocol; vault system                |
| fluid      | Fluid (Instadapp) | Ethereum, Arbitrum                               | `https://fluid.instadapp.io` (testnet)              | [Sepolia Faucet](https://sepoliafaucet.com)       | `FLUID_RPC_URL`, `FLUID_WALLET_KEY`             | Unified liquidity layer; smart lending                |
| etherfi    | Ether.fi          | Ethereum                                         | `https://testnet.ether.fi`                          | [Holesky Faucet](https://holesky-faucet.pk910.de) | `ETHERFI_RPC_URL`, `ETHERFI_WALLET_KEY`         | Liquid restaking; eETH/weETH                          |
| lido       | Lido              | Ethereum                                         | `https://stake-holesky.testnet.fi`                  | [Holesky Faucet](https://holesky-faucet.pk910.de) | `LIDO_RPC_URL`, `LIDO_STETH_ADDRESS`            | Liquid staking; stETH/wstETH                          |
| morpho     | Morpho            | Ethereum, Base                                   | `https://app.morpho.org` (Sepolia)                  | [Sepolia Faucet](https://sepoliafaucet.com)       | `MORPHO_RPC_URL`, `MORPHO_WALLET_KEY`           | Optimized lending; MetaMorpho vaults                  |
| uniswap_v2 | Uniswap V2        | Ethereum                                         | `https://app.uniswap.org` (Sepolia)                 | [Sepolia Faucet](https://sepoliafaucet.com)       | `UNISWAP_V2_RPC_URL`, `UNISWAP_V2_ROUTER`       | Legacy constant-product AMM                           |
| uniswap_v3 | Uniswap V3        | Ethereum, Arbitrum, Optimism, Polygon, Base      | `https://app.uniswap.org` (Sepolia)                 | [Sepolia Faucet](https://sepoliafaucet.com)       | `UNISWAP_V3_RPC_URL`, `UNISWAP_V3_ROUTER`       | Concentrated liquidity; tick-based                    |
| uniswap_v4 | Uniswap V4        | Ethereum                                         | `https://app.uniswap.org` (Sepolia)                 | [Sepolia Faucet](https://sepoliafaucet.com)       | `UNISWAP_V4_RPC_URL`, `UNISWAP_V4_POOL_MANAGER` | Hooks architecture; singleton pool                    |
| instadapp  | Instadapp         | Ethereum, Arbitrum, Polygon, Optimism, Avalanche | `https://testnet.instadapp.io`                      | [Sepolia Faucet](https://sepoliafaucet.com)       | `INSTADAPP_RPC_URL`, `INSTADAPP_DSA_ADDRESS`    | DeFi Smart Accounts (DSA); multi-protocol             |
| defillama  | DefiLlama         | Multi-chain (aggregator)                         | `https://api.llama.fi` (no testnet needed)          | N/A                                               | `DEFILLAMA_API_BASE`                            | TVL/yield aggregator; read-only API; no wallet needed |

## Common Configuration

All DeFi adapters share these base env vars (set via `UnifiedCloudConfig`):

| Env Var               | Description                | Default             |
| --------------------- | -------------------------- | ------------------- |
| `CLOUD_PROVIDER`      | Cloud provider context     | `local` for testnet |
| `CLOUD_MOCK_MODE`     | Enable mock mode for CI    | `true` in tests     |
| `DEFI_DEFAULT_CHAIN`  | Default blockchain         | `ethereum`          |
| `DEFI_GAS_PRICE_GWEI` | Max gas price for txns     | `50`                |
| `DEFI_SLIPPAGE_BPS`   | Default slippage tolerance | `50` (0.5%)         |

## Testnet Networks

| Network          | Chain ID | RPC (Public)                             | Explorer                                | Faucet                                                 |
| ---------------- | -------- | ---------------------------------------- | --------------------------------------- | ------------------------------------------------------ |
| Ethereum Sepolia | 11155111 | `https://rpc.sepolia.org`                | `https://sepolia.etherscan.io`          | `https://sepoliafaucet.com`                            |
| Ethereum Holesky | 17000    | `https://rpc.holesky.ethpandaops.io`     | `https://holesky.etherscan.io`          | `https://holesky-faucet.pk910.de`                      |
| Arbitrum Sepolia | 421614   | `https://sepolia-rollup.arbitrum.io/rpc` | `https://sepolia.arbiscan.io`           | `https://faucet.triangleplatform.com/arbitrum/sepolia` |
| Optimism Sepolia | 11155420 | `https://sepolia.optimism.io`            | `https://sepolia-optimism.etherscan.io` | `https://faucet.triangleplatform.com/optimism/sepolia` |
| Base Sepolia     | 84532    | `https://sepolia.base.org`               | `https://sepolia.basescan.org`          | `https://faucet.triangleplatform.com/base/sepolia`     |
| Polygon Amoy     | 80002    | `https://rpc-amoy.polygon.technology`    | `https://amoy.polygonscan.com`          | `https://faucet.polygon.technology`                    |
