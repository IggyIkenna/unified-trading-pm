---
doc_type: issue
title:
  MTDS `collect-vault-share-price` silently stopped capturing ALL 5 vaults (sFRAX/FRAX, sDAI/MAKER, sUSDe/ETHENA,
  yvUSDC-1 etc./YEARN_V3, steakUSDC+GTUSDCP/MORPHO_VAULTS) after 2026-06-21 — ~1 month gap, other DeFi handlers
  unaffected
summary: >-
  Discovered while verifying the FRAX (sFRAX) DeFi adapter for the 15-protocol distinct-values audit
  (`distinct_values_noncanonical_audit_2026_07_20.md`). A direct on-chain re-test today (2026-07-22) proves the sFRAX
  adapter logic in `vault_share_price_handler.py` is correct and live: `_query_share_price()` against the real sFRAX
  contract (`0xA663B02CF0a4b149d2aD41910CB81e23e1c41c32`, confirmed via `symbol()`="sFRAX"/`name()`="Staked FRAX") at
  the noon-UTC block for a real sample day (2026-07-15, block 25537916) returns a sane share price (1.1595995078043464
  FRAX/sFRAX), matching a manual `eth_call` cross-check byte-for-byte. Production GCS
  (`market-data-tick-defi-prd-central-element-323112`) confirms the handler WAS capturing correctly: real rows exist for
  `venue=FRAX` and `venue=MAKER` (sibling vault in the same `_VAULTS` registry / same handler run) through
  `day=2026-06-21` (`available_at=2026-06-21T19:10:19Z`, real block numbers, real share prices). But **no
  `vault_share_price` objects exist for ANY of the 5 registered vaults for any day sampled from 2026-06-25 through
  2026-07-22** (checked 06-25/06-28/07-01/07-05/07-08/07-10/07-15/07-18/07-20/07-21/07-22, all empty). This is NOT a
  FRAX-specific or general DeFi-capture problem: a different handler (`lst_rates_handler.py`, venue=STADER) captured
  continuously across the exact same window (06-25/07-05/07-15 all present), so other DeFi cron/orchestration paths are
  healthy — only the `collect-vault-share-price` CLI operation appears to have stopped running or stopped succeeding
  roughly 2026-06-22 onward. Root cause not yet diagnosed (out of scope for the single-protocol FRAX verification unit
  that found this) — needs someone to check whether `collect-vault-share-price` is still scheduled at all
  (cron/orchestrator config) and, if so, why it's failing/not writing (Alchemy client init, secret rotation, an
  unhandled exception upstream of the per-vault try/except, etc.).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags:
  [
    defi,
    vault-share-price,
    capture-gap,
    frax,
    maker,
    ethena,
    yearn,
    morpho-vaults,
    data-pipeline-correctness,
    cron-scheduling,
  ]
related: [plans/active/distinct_values_noncanonical_audit_2026_07_20.md]
created: "2026-07-22"
parent_epic: defi_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [sub-agent-observation]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Verifying the FRAX protocol adapter for the 15-protocol distinct-values audit, I ran a real sample-day on-chain query
against the shipped `_query_share_price()` function in
`market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py`, targeting the real sFRAX
contract at `0xA663B02CF0a4b149d2aD41910CB81e23e1c41c32` on Ethereum mainnet (confirmed via on-chain `symbol()`/`name()`
= "sFRAX"/"Staked FRAX"). For day=2026-07-15 (noon-UTC block 25537916), the handler's own function returned
`share_price=1.1595995078043464`, byte-identical to a manual `eth_call` cross-check via three independent public archive
RPCs (`eth-mainnet.public.blastapi.io`, `eth.drpc.org`, `rpc.mevblocker.io`) — the adapter code is correct and the
on-chain data is real and sane (also spot-checked the value moves genuinely over a 1-year window: 1.136→1.160, ~2.07%,
ruling out a stub/constant response).

I then checked whether this is actually landing in production GCS (`market-data-tick-defi-prd-central-element-323112`,
`raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue={V}/...`):

- `venue=FRAX` and `venue=MAKER` (the immediate sibling vault in the same `_VAULTS` dict, same handler, same per-run
  write) both have real captured rows through **day=2026-06-21** (`sFRAX.parquet` /
  `available_at=2026-06-21T19:10:19.755422+00:00`, real block_number, real share_price — genuine T+1 batch capture, not
  a migration artifact, despite an object-metadata `Last modified` of 2026-07-19 from an unrelated later reshard/rename
  pass).
- **No `vault_share_price` object exists for FRAX or MAKER on any sampled day from 2026-06-25 onward**, including
  today's date (2026-07-22): 06-25, 06-28, 07-01, 07-05, 07-08, 07-10, 07-15, 07-18, 07-20, 07-21, 07-22 all came back
  empty for `venue=FRAX/.../data_type=vault_share_price/` (and the same for `venue=MAKER`).
- This is scoped to the `vault_share_price_handler` specifically, not a general DeFi-capture outage: a _different_
  handler (`lst_rates_handler.py`, `venue=STADER`) captured without a gap across the identical window (06-25, 07-05,
  07-15 all present), and `venue=LIDO` / `venue=UNISWAP_V3` both have data as recently as 07-20/07-21.

So: the adapter is provably correct and was working in production up to 2026-06-21, then the entire
`collect-vault-share-price` capture path (covering all 5 registered vaults — sFRAX/FRAX, sDAI/MAKER, sUSDe/ETHENA, the 3
Yearn V3 vaults, steakUSDC + GTUSDCP/MORPHO_VAULTS) appears to have stopped running or stopped succeeding, silently, for
roughly a month.

# What I did NOT do

I did not diagnose the root cause (no Alchemy Secret Manager / production cron access from this sandbox —
`gcloud secrets list` denied on the available service account, and the human account's gcloud token can't be refreshed
non-interactively here). Plausible causes to check: whether `collect-vault-share-price` is still on the CLI/cron
schedule at all; an Alchemy API key rotation/expiry that only this handler's client-init path hits; an unhandled
exception upstream of the per-vault `try/except` (e.g. in `preflight()` or bucket/manifest setup) that would abort the
whole run before any vault is attempted, which would explain why ALL 5 vaults disappeared together rather than failing
individually with per-vault manifest `record_failed` rows.

# Why this matters

This is exactly the kind of silent gap `codex/02-data/data-pipeline-correctness-hard-rule.md` exists to catch — a
handler that both looks "phase=pipeline"/wired-and-working from static code review AND has historical captured rows in
the manifest/GCS (so a lookback query would show "yes, this venue has data") while actually being dead for the most
recent ~4 weeks. It affects the ADD/DROP verdict framing for this audit too: FRAX's adapter itself verdicts ADD (real,
correct, tested), but any claim that it is _currently_ capture-live would be wrong without this fix — same for MAKER,
ETHENA, YEARN_V3, and MORPHO_VAULTS, which are presumably other units' territory in the same 15-protocol survey.

# Suggested next step

A dedicated fix-unit (not this single-protocol audit slot) should: (1) confirm whether `collect-vault-share-price` is
still scheduled anywhere (VM cron / orchestrator config), (2) run it manually for today with verbose logging to surface
the actual exception, (3) fix and confirm a real day's capture resumes for all 5 vaults, (4) backfill the ~30-day gap
once the root cause is fixed.
