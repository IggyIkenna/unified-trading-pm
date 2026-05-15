---
title: codex/04-architecture full drift audit — 2026-05-15 pass
created: 2026-05-15
author: slot-6
source:
  - slot-6 queue item 13 (continuation_prompts_harsh_2026_05_15.md)
locked_by: live-defi-rollout
---

## What I found

Full pass over `codex/04-architecture/` (90+ docs). Audited all docs containing shipped-code symbols,
const references, or file paths. No breaking drift found (no contract violations, no missing critical pointers).

Two categories of non-blocking stale references:

### Category A — Stale package name: `unified_trading_services` → `unified_trading_library`

Rename landed 2026-03-02 (workspace-manifest confirmed). Alias still works but docs should use canonical name.

| Doc | Line(s) | Stale reference |
|-----|---------|----------------|
| `cloud-agnostic-migration.md` | 145 | `from unified_trading_services import PubSubEventSink` |
| `README.md` | 39, 248 | "unified-trading-services" abstractions |
| `runtime-deployment-topology.md` | 1569, 1583, 1607 | `unified_trading_services.GoogleOAuthMiddleware` |
| `tier-and-import-architecture.md` | 147-149 | table column: `→ unified_trading_services` (should be `→ unified_trading_library`) |

Note: `tier-and-import-architecture.md:75-76` already has a note explaining the rename is in progress — update that note to say rename is complete.

### Category B — Stale tool name: `pyright` → `basedpyright`

Workspace standard is `basedpyright` per CLAUDE.md and quality-gates.

| Doc | Line(s) |
|-----|---------|
| `amm-slippage-simulation.md` | ~350 |
| `risk-preflight-flow.md` | ~40 |
| `schema-versioning.md` | ~25 |
| `runtime-deployment-topology.md` | ~1600 |

### Confirmed DRIFT-FREE (audited this session)

| Doc | Audit result |
|-----|-------------|
| `defi-execution-overview.md` | ✅ 30 DefiErrorCode values confirmed; Phase 9 cost model section accurate |
| `flash-loan-receiver.md` | ✅ matches FlashLoanReceiver.sol exactly (item 4, prior cycle) |
| `interface-credential-convention.md` | ✅ get_order_adapter/connector.connect/CLOUD_KMS_ENCRYPTED all match code |
| `shard-level-failure-isolation.md` | ✅ no bare raise in adapter loops; classify_venue_error correct |
| `custody-providers.md` | ✅ SigningSurface.CLOUD_KMS_ENCRYPTED confirmed; LocalKey+CloudKMS exist; CeffuStub=June-1 correct |
| `kill-switch-circuit-breaker.md` | ✅ `/tmp/execution_kill_switch.json` with nosec B108 — correct; active audit note for KillSwitchScope.WALLET is pre-existing |
| `service-emission-policy.md` | ✅ publish_with_policy + 4 policy values match shipped UTL code |
| `service-framework.md` | ✅ ServiceBootstrap in `service_framework/bootstrap.py` confirmed |
| `amm-slippage-simulation.md` | ✅ PoolMatcher Protocol + POOL_MATCHER_REGISTRY + register_pool_matcher all confirmed in `pool_matcher.py` |
| `solana-defi-coverage.md` | ✅ Pyth UNBANNED 2026-05-06 correctly reflected; Jito restaking adapter present |
| `mev-protection.md` | ✅ Bloxroute correctly marked REMOVED |
| `tenderly-execution-provider.md` | ✅ Infura correctly flagged as on Removed Providers list |
| `treasury-custody-flow.md` | ✅ Copper+CEFFU June-1 correctly stated; May-23=CLOUD_KMS_ENCRYPTED correct |
| `commercial-service-families.md` | ✅ "Elysium" usage = demo client shape name (not the removed on-chain data provider) |

## Why it matters

Category A stale imports could mislead devs into using the old package name in new code. Category B
stale tool names could cause QG failures if new services follow the doc examples.

## Recommended decision

1. **Low-priority doc-only batch cleanup** — fix Category A + B in one PM commit per SSOT fast-path
   (docs targeting main branch). This is a ~30-min sweep but should be batched with other stale-ref
   cleanup to avoid noisy commits. Not May-23 critical path.
2. **No code changes needed** — all code contracts verified accurate.
3. **P3 priority** — assign to a slot with available capacity after May-23 cutover.
