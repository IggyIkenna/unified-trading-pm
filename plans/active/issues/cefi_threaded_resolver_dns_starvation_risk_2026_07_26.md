---
doc_type: issue
title: >-
  CEFI live-venue clients (aster/hyperliquid) hardcode aiohttp's `ThreadedResolver()` — same DNS-starvation risk class
  already fixed on the shared Tardis clients
summary: >-
  While closing out `databento_default_executor_dns_starvation_risk_2026_07_17.md`'s todo 3
  (`market-tick-data-service@889ff829`, 2026-07-26), the fix switched the shared Tardis clients
  (`tardis_stream_client.py` + `tardis_base_client.py`, used by BOTH cefi and tradfi) from `ThreadedResolver()` /
  implicit-resolver to explicit `AsyncResolver()`. Two CEFI-only live-venue clients were found to hardcode the identical
  `ThreadedResolver()` pattern and were explicitly left untouched as out-of-scope for that tradfi-scoped todo —
  `aster_base_client.py` and `hyperliquid_base_client.py`. Same bug class, same fix shape, unapplied here.
status: open
resolved_by:
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, asyncio, executor, dns, latent-risk, follow-up]
related:
  [
    /plans/archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
source:
  - Flagged as a same-pattern follow-up in `databento_default_executor_dns_starvation_risk_2026_07_17.md`'s todo 3
    (slot-12, 2026-07-26) while fixing the shared Tardis clients for tradfi; extracted here per findings-closure rule so
    it doesn't stay a dangling prose note in a tradfi-scoped doc that's otherwise fully closed.
assigned_vm: NA
assigned_role: data_engineering
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
drift_direction: advance-code
parent_epic: infrastructure_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-26
locked_by:
locked_since:
---

# CEFI live-venue clients hardcode `ThreadedResolver()` — same DNS-starvation risk class

## The mechanism (same as the already-fixed Tardis path)

`aster_base_client.py` and `hyperliquid_base_client.py` explicitly construct their aiohttp `TCPConnector` with
`resolver=ThreadedResolver()` — the DNS resolver that runs `getaddrinfo` on asyncio's shared default
`ThreadPoolExecutor` rather than via `aiodns`'s non-blocking `AsyncResolver()`. This is the identical pattern already
fixed on `tardis_stream_client.py` / `tardis_base_client.py` (`market-tick-data-service@889ff829`, 2026-07-26) after
that same starvation class wedged the CeFi Tardis backfill at cpu=0% (`market-tick-data-service@2e7c2b5d`, 2026-07-17).
`aiodns` is already a direct dependency as of the Tardis fix, so this follow-up is a mechanical apply, not new plumbing.

## Todos

- [ ] [CODE] P3. Switch `aster_base_client.py` and `hyperliquid_base_client.py` from `ThreadedResolver()` to explicit
      `AsyncResolver()`, mirroring the exact change already landed on the Tardis clients
      (`market-tick-data-service@889ff829`). Add the same regression-test shape (assert the `TCPConnector` receives an
      `AsyncResolver` instance) for both clients. Repo: market-tick-data-service. **Done when**: both clients construct
      their connector with `AsyncResolver()`, both have a regression test asserting it, and `quality-gates.sh` is green.

## Progress Log (append-only)

- 2026-07-26: filed while reconciling `databento_default_executor_dns_starvation_risk_2026_07_17.md`'s checkboxes as
  part of `tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` todo 1 — that doc's own 3 todos are fully done,
  but its slot-12 Progress Log entry had deliberately kept `status: open` pending this exact CEFI follow-up being picked
  up somewhere. Extracting it here (asset_group: cefi, out of tradfi's scope) lets the tradfi doc close cleanly while
  this remains a tracked, actionable item instead of a dangling prose note.
