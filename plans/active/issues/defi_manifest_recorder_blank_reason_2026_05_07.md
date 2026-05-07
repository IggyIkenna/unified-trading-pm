---
title: "DefiManifestRecorder.record_empty() rejected by writegate Phase 3.D.5 — blank reason on every DeFi VM"
created: 2026-05-07
author: agent-4-claude
source:
  - market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py:173-201
  - VM run.log evidence: gs://deployment-scripts-central-element-323112/vm-logs/mtds-{vault-share-price,lst-rates,gas-fees}-20260507-19{47,47,47}/run.log
  - plans/active/work_split_2026_05_07_ikenna_5tab_layout.md (Agent 4 Item 2)
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# DefiManifestRecorder.record_empty() rejected by writegate Phase 3.D.5 — blank reason on every DeFi VM

> **Severity**: P0 — DeFi data-correctness on May-23 live-deadline critical path. Same bug class as 2026-05-07 RED
> ALERT (5 CeFi VMs) but on the DefiManifestRecorder side which Wave 2.M migration missed.
> **Blast radius**: every DeFi backfill that hits a "source returned 0 rows" date — affects MTDS handlers vault-share-
> price / lst-rates / gas-fees / token-transfers / flash-loan-events / bridge-events / eigenlayer-rewards / position-
> data (8 handlers, all instantiating `DefiManifestRecorder`). Manifest writes silently fail, parquets land on disk
> without manifest rows.
> **Suggested owner**: Agent 2 (writegate Phase 3.D.5 / 5) — Wave 2.M migration owner; the DeFi-side analogue of the
> cefi/sports recorder migrations that already shipped per UTL@68b3804a / UTL@7eca2c20.

## What I found

Agent 4 launched 3 DeFi backfill VMs (`mtds-vault-share-price-20260507-194644`, `mtds-lst-rates-20260507-194702`,
`mtds-gas-fees-20260507-194720`) per work_split Item 2. Per the no-fire-and-forget protocol, ~12 min after launch I
ran event-verification + run.log inspection. All three VMs were emitting STARTED + RESOURCE_PROFILER_SAMPLE events
(heartbeat-only) but their run.logs showed thousands of identical warnings:

```
WARNING DefiManifestRecorder(<handler>): record_empty failed for (venue=YEARNV3, chain=ETHEREUM,
data_type=vault_share_price): record_empty() called with blank reason. Pass a typed reason from
EMPTY_CONFIRMED_REASONS (EXPECTED_HOLIDAY / EXPECTED_WEEKEND / EXPECTED_PRE_VENUE_LAUNCH /
EXPECTED_PRE_GENESIS_CHAIN / EXPECTED_PRE_SOURCE_COVERAGE_START / EXPECTED_INSTRUMENT_NOT_LISTED /
EXPECTED_INSTRUMENT_DELISTED / EXPECTED_PARTIAL_HALF_DAY / EXPECTED_PAUSED_LEAGUE /
EXPECTED_DEPRECATED_DATA_TYPE / EXPECTED_REFDATA_CADENCE_CHANGE / SOURCE_RETURNED_ZERO), or use record_failed
if the absence is unexpected. [row_key={'date': '2020-01-01', 'venue': 'YEARNV3', 'chain': 'ETHEREUM',
'data_type': 'vault_share_price'}]
```

`market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py:173-201` defines
`DefiManifestRecorder.record_empty()` with signature:

```python
def record_empty(
    self,
    *,
    venue: str,
    chain: str,
    data_type: str,
    attempted_at: datetime | None = None,
) -> None:
    """Adapter succeeded AND returned zero rows (legitimate empty shard)."""
    row_key = _build_row_key(...)
    try:
        self._writer.record_empty(
            row_key=row_key,
            attempted_at=attempted_at or datetime.now(UTC),
        )
    except Exception as exc:
        logger.warning(
            "DefiManifestRecorder(%s): record_empty failed for ...", ...
        )
```

NO `reason=` parameter accepted, NO reason passed to `self._writer.record_empty()`. UTL `record_empty` (post-UTL@
68b3804a hardening) raises `LegacyBlankErrorReasonError` when reason is blank. The `try/except Exception` swallows the
loud raise into a warning.log line — which is why the VM kept running but produced zero manifest rows for empty days.

3 VMs deleted at 20:00 UTC after diagnosis (prevented further Alchemy / Solana RPC quota burn).

## Why it matters

1. **Direct May-23 live-DeFi blocker.** `carry_staked_basis` reads `lst_rates` + `vault_share_price`; manifest never
   marking pre-launch / source-zero days as `empty_confirmed` means downstream consumers see "missing" forever and the
   orchestrator re-fetches the same dates on every relaunch. Wasted Alchemy CU + Solana RPC quota each cycle.
2. **Same anti-pattern as the 2026-05-07 RED ALERT** (5 CeFi VMs writing 96-100% empty rows with all blank reasons —
   bitfinex/bitget/kraken). The CeFi recorder was migrated as part of writegate Phase 3.D.5 Wave 2.M; the DEFI recorder
   was missed.
3. **Manifest gets the worst of both worlds:** parquets land on disk (under
   `gs://lst-rates-{pid}/raw_tick_data/by_date/.../lst_rates_<ts>.parquet` etc.) but manifest stays empty — phantom-shaped
   without being phantoms in the strict CLAUDE.md sense. Phantom audit (`reconcile_phantom_manifest_rows_all.py`) won't
   find these because the audit checks the OPPOSITE direction (manifest-says-captured but parquet-missing).

## Recommended decision

Fold into [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](../writegate_honest_coverage_endtoend_2026_05_06.plan.md)
as a Wave 2.M-extension item (the DEFI-side analogue of the cefi/sports migrations already shipped). The fix has 3
parts:

1. **`DefiManifestRecorder.record_empty(reason: EmptyConfirmedReason)` signature change** — make `reason` a
   non-optional kwarg; pass it through to `self._writer.record_empty(reason=reason)`. Catch `LegacyBlankErrorReasonError`
   loud (raise, don't swallow) so silent-fail mode is impossible.
2. **8 call-site updates in MTDS** — every handler that calls `recorder.record_empty(...)`:
   - `lst_rates_handler.py` — pre-2020-12 dates → `EXPECTED_PRE_VENUE_LAUNCH` (Lido stETH 2020-12, Marinade 2021-04,
     Jito 2022-11); rest → `SOURCE_RETURNED_ZERO`.
   - `vault_share_price_handler.py` — pre-launch dates per `_VAULTS` registry → `EXPECTED_PRE_VENUE_LAUNCH`; rest →
     `SOURCE_RETURNED_ZERO`.
   - `gas_fees_handler.py` — pre-`GAS_FEE_CHAIN_START_DATES[chain]` → `EXPECTED_PRE_GENESIS_CHAIN`; mid-window 0-fees
     blocks → `SOURCE_RETURNED_ZERO`.
   - `token_transfers_handler.py`, `flash_loan_events_handler.py`, `bridge_events_handler.py`,
     `eigenlayer_rewards_handler.py`, `position_data_handler.py` — same per-handler logic.
3. **Re-launch the 3 VMs** after the fix lands. The previous parquets on disk for those (date, venue, chain, data_type)
   tuples are valid — the orchestrator should NOT re-fetch them once the manifest properly records `empty_confirmed` for
   them. Per CLAUDE.md `§ Manifest concurrency principle`, the per-VM-shard write + consolidator merge will retroactively
   pick up these missing rows.

This is the same shape as 2026-05-07 RED ALERT cefi fix; the DEFI side is straightforward to follow the same pattern.
Effort estimate: ~½ day for the recorder + 8 handler updates + tests; second ½ day for VM re-launches + verification.

## Cross-references

- Reference incident: 2026-05-07 RED ALERT (cefi side) — fixed in writegate Phase 3.D.5 Wave 2.M (UTL@68b3804a +
  UTL@7eca2c20 + UTL@7276cca1 + instruments-service@86804c7 per recent live-defi-rollout commits a541f51e / 937df64b).
- CLAUDE.md `§ Four-category empty-output decision` — defines the `record_empty(reason=<typed>)` contract.
- CLAUDE.md `§ Honest absence vs fake placeholders` — defines the 3-category model that the typed reason taxonomy
  encodes.
- Agent 4 launches that exposed this: `mtds-vault-share-price-20260507-194644`,
  `mtds-lst-rates-20260507-194702`, `mtds-gas-fees-20260507-194720` (all stopped 2026-05-07 ~20:00 UTC after diagnosis).
