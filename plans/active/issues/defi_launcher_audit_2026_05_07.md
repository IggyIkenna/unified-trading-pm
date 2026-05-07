---
title: "DeFi launcher audit — answers to the 3 operator-blocking Qs from defi_master 2026-05-07"
created: 2026-05-07
author: harsh
source:
  - plans/active/defi_master_2026_05_07.plan.md (commit b8edd01 PLANNING-CRITICAL block)
  - market-tick-data-service/market_tick_data_service/cli/handlers/{lending_indices,vault_share_price,lst_rates,gas_fee}_handler.py
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py
  - deployment-service/scripts/vm/launch-mtds-*-backfill-vm.sh
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# DeFi launcher audit — answers to the 3 operator-blocking Qs

The 2026-05-07 PM commit `b8edd01` (planning-critical correction in `defi_master_2026_05_07.plan.md`) raised three
operator-actionable questions to Ikenna gating next-stage launches. This doc answers each from code-side evidence, no VM
launches required.

**Source diagnostic (parallel agent, 2026-05-07):** Arbitrum/Base/Polygon at 0% on the canonical DeFi manifest; Ethereum
forward-poll stopped 2026-01-23 for most data_types; `launch-mtds-perp-funding-backfill-vm.sh` referenced in CLAUDE.md
but reportedly missing.

---

## Q1 (referenced) — was the original "60%" coverage claim reading a different bucket?

**Out of scope of this audit** — would need to read the deployment-api `_data_status_rollup_worker` and compare the
rollup it produces against the canonical manifest the parallel agent queried. Flag stays open. The parallel agent's
diagnostic at `gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet` is the canonical
source; whatever the rollup said previously is suspect.

---

## Q2 — are MTDS DeFi launchers Ethereum-only?

**Answer: NO. The handlers are multi-chain by design. The 0% Arb/Base/Polygon coverage is a different problem.**

### Per-handler evidence

| Handler                                                                                                                                         | Multi-chain?                                               | Source of chain list                                                  | Default chains today                                                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [`gas_fee_handler.py:46`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/gas_fee_handler.py#L46)                       | ✅ Yes                                                     | hardcoded `DEFAULT_GAS_FEE_CHAINS`                                    | 14 chains: ETHEREUM, OPTIMISM, BSC, POLYGON, BASE, ARBITRUM, AVALANCHE, LINEA + 6 Tier 3                                              |
| [`lending_indices_handler.py:253`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py#L253)     | ✅ Yes                                                     | `get_supported_chains_for_protocol(protocol)` from UAC `SUBGRAPH_IDS` | AAVE_V3 → 8 chains (ETH, ARB, OPT, POL, AVAX, BASE, LINEA, BSC); COMPOUND_V3 → 4; MORPHO → 2 (ETH, BASE)                              |
| [`vault_share_price_handler.py:234`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py#L234) | ⚠ Multi-chain capable but Ethereum-skewed by **registry** | `_VAULTS` registry                                                    | 9 ETHEREUM entries + sparse non-ETH (MORPHOVAULTS×2, MAKER, FRAX, ETHENA — these last 4 are protocol names not chains; need re-check) |
| [`lst_rates_handler.py:251,288,301,334`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py#L251)     | ❌ No (by design)                                          | hardcoded `chain="ETHEREUM"` + Solana side-path for Marinade          | ETHEREUM (13 EVM LSTs) + SOLANA (Marinade) only — LSTs canonically live on these two chains                                           |

### Conclusion

The multi-chain capability **exists** in code. The `lending_indices` handler will iterate 8 chains for AAVE_V3,
including Arb/Base/Polygon, when the launcher fires it. So why do those chains have 0 rows on the manifest?

**Most likely answer: the lending-indices launcher hasn't been run with full-history scope yet.** The parallel agent's
diagnostic noted `mtds-lending-indices-20260507-140418` was launched 2026-05-07 14:04 IST with full history — that's in
flight RIGHT NOW (ETA 17:00-19:00 IST per their note). When that VM completes, Arb/Base/Polygon manifest rows for
AAVE_V3 / COMPOUND_V3 / MORPHO should populate.

**What would still need separate launches** to reach full DeFi coverage:

- `gas_fee_handler` for the same Arb/Base/Polygon chains (hits 14 chains by default — likely needs a launcher run)
- Per-chain DEX subgraph coverage (uniswap_v3 / balancer / curve etc. — these are NOT in the 4 launchers I audited; they
  flow via a different path I haven't traced yet)

**Action for Ikenna:**

1. Wait for `mtds-lending-indices-20260507-140418` to complete; re-check manifest. If Arb/Base/Polygon rows appear,
   chain-iteration is confirmed working and the original "0%" was simply "never invoked."
2. If those rows DON'T appear after the VM completes successfully, that's a real silent-no-op bug — drop into the
   handler logs or the orchestrator's `_should_skip_shard` to find where the chain is being filtered.

---

## Q3 — Ethereum forward-poll stopped 2026-01-23: paused or broken?

**Answer: launcher exists; no VM running; appears to be a missing-cron / never-relaunched situation, not a code
breakage.**

### Evidence

- [`launch-defi-forward-poll.sh`](../../../deployment-service/scripts/vm/launch-defi-forward-poll.sh) **exists** in the
  workspace.
- `gcloud compute instances list --filter='name~"^defi-fwd|^mtds-.*fwd"'` returns **empty** — no defi forward-poll VM
  currently running.
- Last MTDS lending-handler commit `a2d464c` (2026-05-06) was 4 months after the 2026-01-23 forward-poll cessation —
  whatever caused the stop happened well before any recent code change.

### Most-likely scenario

The forward-poll VM either auto-shut on completion of its window and was never re-launched (no operator action), OR a
crash/preemption took it down and no alert fired (operator missed it). Either way, **relaunching the launcher should
restore forward-poll** — no code fix needed unless the relaunch itself fails, in which case fall through to log
inspection.

**Action for Ikenna:**

1. Read `gcloud compute instances list --filter='name~"^defi-fwd"' --include-deleted` if available, or scan
   `gs://deployment-scripts-{pid}/vm-logs/defi-fwd-*/run.log` for the most recent termination event — confirm clean
   shutdown vs crash.
2. Relaunch with `bash deployment-service/scripts/vm/launch-defi-forward-poll.sh`; verify STARTED event within 90s per
   the no-fire-and-forget rule.
3. If the freshly-launched VM stalls or fails, then fall back to bug investigation — but as of this audit, there's no
   evidence of broken code.

**Caveat:** I didn't verify the launcher itself is current vs the post-2026-01-23 codebase. Worth a glance before
relaunch to confirm flags are still valid.

---

## Missing-launcher question — `launch-mtds-perp-funding-backfill-vm.sh`

**Answer: confirmed missing. Has NEVER existed in `deployment-service` git history.**

### Evidence

- `ls deployment-service/scripts/vm/ | grep -iE "perp-funding|funding"` → empty.
- `find . -name "launch*perp-funding*" -o -name "launch*funding*backfill*"` (workspace-wide, excluding `.venv` /
  `node_modules`) → empty.
- `git log --all --diff-filter=D --oneline -- 'scripts/vm/launch-mtds-perp-funding-backfill-vm.sh'` → empty (never
  existed-then-deleted).
- `git log --all --oneline -- 'scripts/vm/launch-mtds-perp-funding-backfill-vm.sh'` → empty (never authored at this
  path).

### Where the perp-funding data IS captured today

Per `carry_staked_basis_structure_axis_2026_05_04` plan archive, perp funding flows through TWO existing paths (neither
named `launch-mtds-perp-funding-`):

1. **Tardis derivative_ticker capture** — `derivative_ticker` data carries `funding_rate` + `open_interest` +
   `mark_price` + `index_price` via Tardis. 2026-05-05 audit confirmed coverage on BINANCE-FUTURES, BYBIT, OKX-SWAP,
   DERIBIT, HYPERLIQUID, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES. Captured by the standard CeFi MTDS backfill
   flow.
2. **Native HYPERLIQUID + GMX funding** — `gs://perp-funding-{pid}/perp_funding/{hyperliquid,gmx}/` — captured by
   features-delta-one VMs (`features-delta-one-defi-backfill-20260505-115343` etc.).

So the **functional perp-funding coverage exists** via Tardis (CeFi) + features-delta-one (DeFi-native). The referenced
`launch-mtds-perp-funding-backfill-vm.sh` may be a stale CLAUDE.md reference predating the consolidation, or a
planned-but-never-authored launcher.

### Implication for `leveraged_funding_arb`

The second cutover archetype (`leveraged_funding_arb`) needs cross-venue funding-rate spreads. Per CLAUDE.md:

> `mtds-perp-funding-` referenced in CLAUDE.md "Singleton-locked launchers" + "VM Naming Convention" sections

The data flow already exists (Tardis + features-delta-one). The missing launcher might just be a **CLAUDE.md reference
correction** — not a blocker for `leveraged_funding_arb`, since the underlying data is being captured by other
launchers.

**Action for Ikenna:**

1. **Decide:** is the missing launcher a real gap (need to author it for some specific MTDS perp-funding data path the
   existing flows don't cover), OR is it a stale CLAUDE.md reference that should be removed?
2. If real gap: scope what data the new launcher would capture that Tardis + features-delta-one don't already cover.
3. If stale: remove the reference from CLAUDE.md `§ Singleton-locked launchers` + `§ VM Naming Convention`.

---

## Summary — recommended operator decisions

| Q                             | Status          | Recommended action                                                                                                                                                                          |
| ----------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q1 — original 60% claim       | OPEN            | Audit `_data_status_rollup_worker` vs canonical manifest separately — out of scope here                                                                                                     |
| Q2 — multi-chain launchers    | RESOLVED        | Handlers ARE multi-chain. Wait for in-flight `mtds-lending-indices-20260507-140418`; if Arb/Base/Polygon don't populate after rc=0, then real bug — drop into orchestrator chain-skip logic |
| Q3 — Ethereum forward-poll    | LIKELY-RELAUNCH | Re-invoke `launch-defi-forward-poll.sh` per no-fire-and-forget protocol; only investigate if the freshly-launched VM stalls                                                                 |
| Missing perp-funding launcher | CLARIFY         | Decide: real gap or stale CLAUDE.md reference. Functional coverage already exists via Tardis + features-delta-one                                                                           |

---

## What this audit did NOT do

- Verify the in-flight `mtds-lending-indices-20260507-140418` is actually emitting per-chain manifest rows (would need
  to read the GCS event stream + manifest delta). Recommend ops check at ETA.
- Trace the per-chain DEX subgraph capture path (uniswap_v3 / balancer / curve coverage on Arb/Base/Polygon — not in the
  4 audited launchers).
- Inspect `_data_status_rollup_worker` (deployment-api) for the rollup-vs-manifest discrepancy that produced the
  original "60%" claim.
- Re-launch the defi forward-poll VM (operator decision per no-fire-and-forget rule + cost-aware launching).
