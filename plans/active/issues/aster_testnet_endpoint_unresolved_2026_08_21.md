---
doc_type: issue
title: Aster registry base_urls were dead DNS; mainnet fixed, testnet host still unverified
summary: >-
  UAC _cefi.py declared api.aster.finance (mainnet) and testnet-api.aster.finance (testnet) —
  both NXDOMAIN. The real, already-shipped execution adapter uses fapi.asterdex.com and never
  referenced aster.finance at all. Mainnet corrected in this session; no working testnet host
  has been found, so Aster's supports_testnet=True claim is currently unverified.
status: open
nature: issue
asset_group: [cefi]
stage: [data, execution]
repos: [unified-api-contracts, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, cefi, aster, registry-drift, dns]
related:
  - /plans/active/cefi_venue_smoke_batch1_2026_08_20.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
parent_epic: security_and_cross_cutting_master
priority: P2
created: 2026-08-21
author: slot-21
assigned_vm: planning
source:
  - /plans/active/cefi_venue_smoke_batch1_2026_08_20.md
  - "execution-service/scripts/run_cefi_testnet_connectivity_smoke.py live run, 2026-08-21: ASTER -> host_unreachable, ConnectionError NameResolutionError for testnet-api.aster.finance"
  - "Live getent/curl checks from the workspace VM, 2026-08-21: both api.aster.finance and testnet-api.aster.finance NXDOMAIN; testnet.asterdex.com also NXDOMAIN; fapi.asterdex.com live-verified 200 on /fapi/v1/ping"
resolved_by:
locked_by:
context_scope:
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_cefi.py
  - execution-service/execution_service/defi_execution/protocols/aster.py
---

# Aster registry base_urls were dead DNS; mainnet fixed, testnet host still unverified

## What I found

While running a live testnet connectivity smoke for the 17 CeFi venues with a declared
testnet (per this batch's own todo #3), the ASTER check failed with a DNS resolution error
against the UAC-declared testnet host `testnet-api.aster.finance`. A direct `getent hosts` +
`curl` check from this workspace VM confirmed BOTH `api.aster.finance` (mainnet) and
`testnet-api.aster.finance` (testnet) are NXDOMAIN — not a transient blip, not specific to
the testnet subdomain. Every other of the 16 live-checked venues in this batch resolved and
responded normally from the same VM/network in the same run, ruling out a general network
issue.

Cross-checking `execution-service/execution_service/defi_execution/protocols/aster.py`
(the real, already-shipped Aster execution adapter) shows it never used `aster.finance` at
all — its own `ASTER_REST_BASE = "https://fapi.asterdex.com"` and docstring both point at
`asterdex.com`. A live check confirmed `fapi.asterdex.com/fapi/v1/ping` returns 200. A guess
at the equivalent testnet host, `testnet.asterdex.com`, does NOT resolve.

## Why it matters

`unified_api_contracts/registry/capability_declarations/_cefi.py`'s `_ASTER.base_urls` and
`unified_api_contracts/registry/endpoints.py`'s `"aster"` entry are the SSOT other consumers
resolve Aster's base URL from (the venue smoke-test generator, capability-driven callers,
docs). The actual live trading path was never affected — the real adapter hardcodes its own
correct URL and does not read from this registry — but any OTHER consumer trusting the
registry's declared URL was getting a value that has apparently never resolved from this
network. Separately, `supports_testnet=True` is declared for Aster with no verified testnet
host behind it — this batch's parent plan counted ASTER among the "17 real testnet venues"
on the strength of that flag; that count may need revisiting if no testnet host can be found.

## Recommended decision

- [x] ✅ [BACKEND] P2. Correct the dead mainnet base_url in both registry locations to the
      real, live-verified adapter host. (repo: unified-api-contracts) — fixed this session:
      `_cefi.py` `_ASTER.base_urls["mainnet"]` and `endpoints.py["aster"]` both now
      `https://fapi.asterdex.com`; live-verified 200 on `/fapi/v1/ping` before landing.
- [ ] [BACKEND] P2. Find Aster's real testnet/demo host (if one exists) via their public API
      docs (`https://github.com/asterdex/api-docs`) or an operator ask, and either populate a
      verified `base_urls["testnet"]` or flip `supports_testnet=False` if Aster genuinely has
      no testnet. Until resolved, `_cefi.py`'s testnet URL for Aster is left at its prior
      (dead) value rather than a guessed replacement. (repo: unified-api-contracts)
- [ ] [BACKEND] P3. Grep the registry for other `SourceCapability.base_urls` entries that may
      share this class of drift (declared URL never live-verified) — this was found only
      because this batch's smoke test happened to exercise it live; no other venue in this
      batch's 17-row check showed the same symptom, but the registry has ~24 CeFi source
      declarations total and only these 17 were live-attempted. (repo: unified-api-contracts)

## Progress Log

**2026-08-21 — slot 21.** Found while executing `cefi_venue_smoke_batch1_2026_08_20.md` todo
#3 (testnet smoke coverage). Fixed the evidenced mainnet URL in the same session; left the
unverified testnet question as tracked follow-up work above rather than guessing.
