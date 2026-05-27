---
title: "MTDS DeFi Handler Bugs + SOURCE_RETURNED_ZERO Manifest Cleanup"
created: 2026-05-23
source:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - plans/epics/mtds_mdps_master.md
  - plans/epics/defi_master.md
status: resolved
resolved_at: 2026-05-23
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — RESOLVED (frontmatter status:resolved 2026-05-23) — 3 handler bugs fixed
> MTDS@69d694b1 + e86a6ad8; successor DeFi VM relaunch tracked in `plans/epics/mtds_mdps_master.md` MDPS-3.3.DeFi-V.
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## What I found

Three MTDS DeFi handler bugs caused ~100% of `gas_fees`, ~0% of `lending_indices`, and all `dex_swaps` rows to land as
`empty_confirmed SOURCE_RETURNED_ZERO` instead of `captured`:

### Bug 1 — `dex_swaps` hardcoded as `dex_pool_swaps`

`dex_swaps_handler.py` line 553 hardcoded `data_type="dex_pool_swaps"` instead of using the module-level constant
`_DEX_SWAPS_DATA_TYPE = "dex_swaps"`. All dex_swaps writes since the UAC rename landed under the wrong partition key
(`dex_pool_swaps`) in the manifest and GCS.

**Fix**: `market-tick-data-service@69d694b1` — changed to `data_type=_DEX_SWAPS_DATA_TYPE`.

### Bug 2 — `gas_fees` null eth_feeHistory result silently returns []

When Alchemy returns `result: null` for `eth_feeHistory` (e.g. for recent blocks not yet finalized), `gas_fee_client.py`
did `data.get("result", {})` which returns `None`. The check `not isinstance(None, dict)` is True, so it returned `[]`
silently without raising. This prevented the `_fee_from_block_txns` fallback from triggering → 0 fee rows →
`SOURCE_RETURNED_ZERO`.

**Fix**: `market-tick-data-service@69d694b1` — added `if result is None: raise ValueError(...)` before the isinstance
check; added `"returned null result"` to the fallback condition.

### Bug 3 — `lending_indices` silently skips when The Graph API key is missing from SM

`lending_indices_handler.py` loaded the API key from Secret Manager with `except Exception: logger.warning(...)`. On
failure, `self._api_key` stayed `None`. The handler then hit `if not self._api_key: return 0` (old code) →
`record_empty(SOURCE_RETURNED_ZERO)`. The key IS in Secret Manager as `thegraph-api-key`.

**Fix**: `market-tick-data-service@e86a6ad8` — SM failure now logs at ERROR level (visible); added
`os.environ.get("THE_GRAPH_API_KEY")` fallback per secrets-management.md convention; the `return 0` was changed to
`raise RuntimeError(...)` in the prior commit so missing key surfaces as `attempted_failed` rather than
`empty_confirmed`.

---

## Why it matters

All three data_types are P0 for the two DeFi archetypes (`carry_staked_basis` + `arbitrage_price_dispersion`):

- `gas_fees` — cost basis for DeFi transactions, required for strategy PnL
- `lending_indices` — Aave/Compound/Spark lending rates, required for `carry_staked_basis`
- `dex_swaps` — DEX execution data, required for `arbitrage_price_dispersion`

The `empty_confirmed SOURCE_RETURNED_ZERO` rows also act as skip-markers: the MTDS orchestrator's pre-flight check
treats `empty_confirmed` the same as `captured` and skips those slots forever. Without cleaning the manifest, re-running
the fixed handlers won't process the affected dates.

---

## Recommended decision

→ **DONE**: Handler bugs fixed and pushed to `live-defi-rollout`.

→ **DONE (in progress)**: `scripts/reset_source_returned_zero_manifest.py` — deletes all
`empty_confirmed SOURCE_RETURNED_ZERO` rows from per-VM shards + consolidated index across all MTDS buckets. Run
dry-run, then apply, then trigger manifest consolidator.

→ **Next**: Re-run MTDS DeFi backfill for the affected date ranges (gas_fees / lending_indices / dex_swaps) now that the
manifest is clean. The fixed handlers will populate `captured` rows.

---

## Fix evidence

| Bug                         | Fix commit      | Files changed                                    |
| --------------------------- | --------------- | ------------------------------------------------ |
| dex_swaps hardcode          | `mtds@69d694b1` | `dex_swaps_handler.py:553`                       |
| gas_fees null result        | `mtds@69d694b1` | `gas_fee_client.py:195-198, 421`                 |
| lending_indices silent skip | `mtds@e86a6ad8` | `lending_indices_handler.py:249,252-254`         |
| Manifest reset script       | `mtds@e86a6ad8` | `scripts/reset_source_returned_zero_manifest.py` |

## Temporary states + their canonical follow-up plans

- Manifest SOURCE_RETURNED_ZERO rows being deleted → next state: `expected_unattempted` (no row) → handled by MTDS
  re-run. Successor: `plans/epics/mtds_mdps_master.md` MDPS-3.3.DeFi-V item (relaunch DeFi VMs with fixed code).
