# Slot 1 ping file — re-themed 2026-05-30

> Doorbell only. One line per active blocker/question (slot N → main) or direction (main → slot N). Full Q&A lives in
> the slot's plan-of-record § "Open questions". Resolved entries removed by main. Format:
> `[YYYY-MM-DD HH:MM UTC] <agent-tag> — <one-line>`

[2026-05-30 15:10 UTC] [main → slot 1] — RE-THEMED via --reset-slot. Prior theme: TBD (main fills from yesterday's
LEDGER + prior plan's DONE block on first read). New theme: TBD (main fills from today's work-split + plan-of-record +
spawn prompt).

## CREDENTIAL APPROVAL REQUEST — Tardis API key

[2026-06-15 18:39 UTC] [slot-1 → main] — BLOCKED-CREDENTIALS: Tardis historical crypto-options adapter scaffold is
shipped (market-tick-data-service Phase D P1c Item 3) but cannot run until operator ACKs this request.

- **vendor**: Tardis.dev (https://tardis.dev)
- **tier + approx cost**: Individual plan ~$250/mo; Enterprise plan (needed for full options replay) ~$1,200/mo. Exact
  pricing: https://tardis.dev/pricing
- **what's needed**: API key + Tardis.dev account with access to the `options_chain` data channel for Deribit.
- **what it unblocks**: Historical crypto-options backfill for all VOL\_\* engines (implied-vol surface, greeks
  snapshots). Without this, the `(cefi, options_chain)` SOURCE_PRIORITY primary source (tardis=BATCH) has no data. The
  Deribit LIVE path (Item 1) works today, but the batch historical path is dark.
- **plan-of-record**: `plans/active/v2_engine_venue_buildout_2026_06_15.md`
- **adapter scaffold path**:
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_options_adapter.py`
- **unit tests**: `market-tick-data-service/tests/market_interface/adapters/cefi/test_tardis_options_adapter.py` (run
  under QG --block-network; integration tests marked @pytest.mark.requires_credentials are skipped by default)
- **status**: BLOCKED-CREDENTIALS — NOT deferred; adapter scaffold + unit tests already shipped.
- **operator action needed**: Reply `[ack]` below with Tardis API key location in Secret Manager once provisioned.
