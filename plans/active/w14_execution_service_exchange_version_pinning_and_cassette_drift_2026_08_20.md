---
doc_type: plan
title: W14 — Execution-service exchange-version pinning and cassette drift detection
summary: >-
  A silent venue-API-version change (a field renamed, a response shape altered, a new required parameter) can go
  completely undetected today: recorded VCR cassettes replay old venue responses forever regardless of what the
  live venue now actually returns, and native (non-ccxt) REST adapters carry no explicit per-venue API-version
  assertion at all. This plan designs and builds the missing mechanism — per-venue version pinning where a real
  concept of "venue API version" exists, plus a drift-detection check that can tell a stale cassette apart from a
  genuinely-current one — per the epic's W14 workstream. No owning plan existed at authoring time; spun into its
  own dedicated AO plan 2026-08-20 with the operator's direct authorization for this specific plan (asked via
  AskUserQuestion mid-session, "AO plan" selected), following the same pattern as W15/W22 earlier the same day.
status: active
nature: design
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, cassettes, versioning, drift-detection, w14]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  T4's own code-readiness plan (code_readiness_t4_execution_settlement_2026_08_19.md), W14 workstream: "Pin the
  exchange version per venue and re-run cassettes on drift... No owning plan existed at authoring time." Spun out
  2026-08-20 after direct operator authorization for this specific plan (AskUserQuestion, mid-`/autonomous`
  session). Scoping measurements at authoring time: 8 cassette directories exist
  (`tests/{sports_execution,defi_execution,trade_execution}/cassettes`); `ccxt` is pinned via the standard
  pyproject/uv.lock range mechanism (`>=4.5.24,<5.0.0`) already, covering ccxt-wrapped venues' LIBRARY version but
  not the underlying exchange's own API version; native (non-ccxt) REST adapters
  (`trade_execution/adapters/kraken_rest_transport.py`, `bitfinex_native.py`, `bitget_native.py`, etc.) carry no
  explicit per-venue API-version assertion anywhere — confirmed via grep, zero hits for any version marker in
  those files.
context_scope:
  [
    execution-service/execution_service/trade_execution/adapters/,
    execution-service/execution_service/defi_execution/protocols/,
    execution-service/execution_service/sports_execution/adapters/,
    execution-service/tests/trade_execution/cassettes/,
    execution-service/tests/defi_execution/cassettes/,
    execution-service/tests/sports_execution/cassettes/,
  ]
---

# W14 — Execution-service exchange-version pinning and cassette drift detection

> A cassette is a recorded belief about what a venue's API looked like on the day it was captured. Nothing today
> checks whether that belief is still true. Epic section: `/plans/epics/system_readiness_master.md` § W14.

## Todos

### Phase 1 — establish what "version" means per transport (design, blocks everything after)

- [x] [AGENT] P0. **Enumerate every venue adapter by transport type**, real directory walk (not estimated, same
      discipline W15 used): ccxt-wrapped CeFi, native-REST CeFi
      (`trade_execution/adapters/*_native.py`/`*_rest_transport.py`), DeFi on-chain protocol connectors
      (`defi_execution/protocols/`), sports bookmaker/exchange adapters (`sports_execution/adapters/`), TradFi
      gateway adapters. Record the count and file list per category — this is the input every later todo sizes
      against. — Evidence: `rg --files` walk in execution-service; CCXT 8, native REST 3 (+ 1 shared transport),
      DeFi 31, sports external 7, TradFi 7; cassette files 17 across the three scoped cassette trees.; slot 4 inventory commit 8fa0a150a1
- [x] [AGENT] P0. **Decide what "exchange version" concretely means per transport category** — this is the real
      open design question, not mechanical. Candidates to evaluate per category, pick one (or a per-category mix)
      and write the decision down with reasoning: (a) an explicit API-version STRING the adapter asserts against
      a response header or a known-shape field (works for REST APIs that version explicitly, e.g. `/v1/`
      vs `/v2/` path segments already present in some URLs); (b) a SCHEMA HASH of the expected response shape,
      computed once at adapter-authoring time and re-checked against live/cassette responses; (c) for ccxt-wrapped
      venues, whether the existing `ccxt` library pin is actually sufficient (ccxt itself tracks upstream exchange
      changes as a dependency-update cadence) or whether a per-venue check is still needed underneath it; (d) for
      on-chain DeFi protocols, whether "version" means the deployed CONTRACT ADDRESS/ABI version instead of an API
      concept at all — on-chain protocols don't have a "REST API version," they have contract upgrades, which is
      a materially different drift risk (already partially covered by W15's per-adapter audit — cross-reference,
      don't duplicate). **Decision (2026-08-20, slot 4):** define an exchange-version marker as the smallest
      transport-specific compatibility identity, not as one universal numeric version. Native CeFi REST and sports
      HTTP adapters pin the provider/product API path version (for example `/v1`, `/v2`, `/v3`, or `/v4`) per base
      URL; when a provider has no versioned path or reliable version header, use the endpoint family plus a
      normalized response-schema fingerprint rather than inventing a version string. CCXT-wrapped CeFi pins the
      resolved CCXT library version (currently `4.5.39`, constrained by `>=4.5.24,<5.0.0`) as the adapter
      compatibility version, but explicitly does **not** claim to pin the upstream venue API; structural cassette
      checks remain the venue-drift guard and a separate per-venue HTTP assertion is not required in this phase.
      DeFi on-chain connectors use chain/network, deployed contract address, and the ABI/function-selector
      fingerprint; REST-backed DeFi connectors use the same path-version plus schema rule as native REST. TradFi
      adapters are seven facades over the shared IBKR gateway, so they have no independent exchange API version:
      pin the gateway wire/API major when the gateway exposes one, otherwise the adapter protocol/schema
      fingerprint. This mix is chosen because URL versions and contract addresses are observable compatibility
      inputs, while response headers are inconsistently available and a schema hash alone cannot identify a changed
      endpoint or contract. Phase 2 must record these markers; Phase 3 must hash normalized structure (field names,
      container shape, and scalar types; ignore values, timestamps, ordering, and secrets). Cross-reference W15 for
      contract/security findings and do not duplicate).
- [x] [AGENT] P1. **Decide the cassette-drift-detection mechanism.** Options to evaluate: (a) a scheduled job that
      re-records a small canary request per venue against the LIVE API (read-only, safe endpoints only — e.g.
      exchange-info/ticker, never anything that could place an order) and diffs its shape against the checked-in
      cassette, alerting on structural drift (field added/removed/type-changed) rather than value drift (a price
      changing is not drift, a field disappearing is); (b) a cassette max-age check that fails CI/nags once a
      cassette exceeds N days old, forcing a manual re-record + review; (c) both, layered (age check catches
      "nobody looked at this in months," live-diff check catches "the shape actually changed"). Write the decision
      + reasoning down; this determines the shape of every build todo below.
      Decision (2026-08-21): choose the offline layered mechanism: schema fingerprints plus a configurable max-age check, not a live canary. It is credential-free and cannot place an order; live canary re-recording remains a separately gated follow-up.

### Phase 2 — build per-transport version pinning

- [ ] [AGENT] P1. **Add the decided version marker to every native (non-ccxt) REST adapter.** Confirm which
      adapters (from Phase 1's inventory) genuinely lack one before adding — some URLs may already embed a version
      segment that just needs to be asserted rather than newly introduced.
- [x] [AGENT] P1. **Confirm and, if needed, tighten the ccxt-wrapped venues' version story** per Phase 1's
      decision — either document why the existing pyproject range is sufficient, or add the per-venue check
      decided in Phase 1. — execution-service@48bf2728: added `CCXT_VERSION_RANGE` (">=4.5.24,<5.0.0", matching
      pyproject/uv.lock) and a real runnable `assert_ccxt_version_pinned()` check + unit tests in `ccxt_common.py`
      confirming the pyproject range IS the pinning mechanism for the 8 ccxt-wrapped venues, per Phase 1's decision
      that a separate per-venue HTTP version assertion is not required underneath ccxt.
- [ ] [AGENT] P1. **DeFi protocol connectors: pin the expected contract address/ABI version per protocol** if
      Phase 1 decided this is a materially different mechanism than the REST-API-version concept — cross-check
      against W15's audit findings first (`/plans/active/w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`)
      to avoid duplicating work already covered there.
- [ ] [AGENT] P2. **Sports bookmaker/exchange adapters: apply the same marker**, following whichever pattern
      Phase 1 decided fits their transport (most are REST, likely following the native-REST pattern above).

### Phase 3 — build cassette drift detection

- [x] [AGENT] P0. **Build the decided drift-detection mechanism** (Phase 1's choice) as a real, runnable check —
      not a design doc. If it's a live-diff canary job, it must be READ-ONLY and safe to run unattended (never a
      write/order-placing call); if it's an age check, it must be wired into `quality-gates.sh` or a scheduled job,
      not a manual reminder nobody runs.
      Evidence: execution-service offline checker and checked-in schema baseline; non-zero on drift/staleness, zero only on a clean baseline.
- [ ] [AGENT] P1. **Wire the drift check into CI or a scheduled job** (whichever this repo's existing infra
      supports more cleanly — check for an existing scheduled-job pattern in this repo before inventing a new
      one) so drift surfaces automatically, not only when someone happens to run the check by hand.
- [ ] [AGENT] P2. **Alert routing**: if drift fires, it should reach a real channel per this workspace's own
      alerting conventions (`/codex/04-architecture/ci-alerting.md` / `agent-orchestrator-alerting.md`) — dedup by
      state-transition, never spam every run, and close the alert when the cassette is re-recorded.

### Phase 4 — triage and close-out

- [ ] [AGENT] P1. **Run the drift check for real against every venue's cassettes once built**, and record the
      actual current staleness state (which cassettes are genuinely stale vs current) — this is the first real
      evidence this mechanism was worth building, not just a smoke test that it runs.
- [ ] [AGENT] P1. **Re-record every cassette the drift check flags as genuinely stale**, or file a tracked
      follow-up per stale cassette if re-recording needs credentials/access this dispatch doesn't have
      (`BLOCKED-CREDENTIALS`, per `/codex/02-data/external-data-always-available-rule.md` — build the mechanism
      regardless, credential gaps are never a reason to skip the scaffold).
- [ ] [AGENT] P2. **Post-phase codex audit**: check whether any codex doc under `/codex/06-coding-standards/` or
      `/codex/04-architecture/` should document this new mechanism (so the NEXT venue adapter added to this repo
      picks up version pinning + cassette drift coverage by convention, not by someone re-deriving this plan).

## Progress Log

> Append-only. Record shas, corrections, and traps here as work lands — this is what a compressed future session
> reconstructs from, not the checkboxes alone.

- **2026-08-20, T4 (interactive session, `/autonomous`)**: plan authored after the operator directly authorized
  spinning W14 out as a dedicated AO plan (AskUserQuestion mid-session). Scoping measurements (8 cassette dirs,
  ccxt pyproject-range pin already present, zero native-adapter version markers found) done via real grep, not
  estimated. Phase 1's three design todos are the load-bearing ones — everything after depends on their outcome,
  so they are P0 and must land first even though `sequential: true` was deliberately NOT set (the plan-authoring
  rule reserves that for genuinely single-threaded work; Phase 1's three todos ARE independent of each other and
  can run concurrently, they just each gate their own downstream phase).
- **2026-08-20, slot 4, Phase 1 inventory**: measured by `rg --files` plus top-level class declarations. Counts: **CCXT-wrapped CeFi 8** (`trade_execution/adapters/{aster,binance,bybit,coinbase,deribit,hyperliquid,okx,upbit}_ccxt.py`); **native-REST CeFi 3 concrete venues** (`bitfinex_native.py`, `bitget_native.py`, `kraken_rest_adapter.py`; `kraken_rest_transport.py` is a shared mixin); **DeFi 31 connectors** (`defi_execution/protocols/{aave,aster,beefy,bybit,cctp,convex,eigenlayer,etherfi,hyperliquid,idle,jito,jito_restaking,jupiter,kamino,karak,kelpdao,lido,marinade,morpho,orca,pacifica,pendle,puffer,raydium,renzo,rocket_pool,solblaze,symbiotic,uniswap,weth,yearn}.py`, excluding bases/helpers); **sports 7 external bookmaker/exchange adapters** (`sports_execution/adapters/aggregator/odds_api.py`, `bookmaker_api/{api_football,onexbet}.py`, `exchanges/{betfair,kalshi,matchbook,polymarket_clob}.py`; paper and Unity are non-venue); **TradFi 7 gateways** (`trade_execution/adapters/{cboe_adapter,cme_adapter,fx_adapter,ibkr_tradfi,ice_adapter,nasdaq_adapter,nyse_adapter}.py`). Legacy `trade_execution/adapters/sports_adapter.py` and `polymarket_adapter.py` facades are outside the requested sports surface and not double-counted.

- **2026-08-20, slot 4, Phase 1 version-semantics decision**: Evidence from the real adapter walk and scoped cassettes supports a transport-specific marker: native CeFi and sports use URL/endpoint API path versions with normalized response-schema fingerprints where no explicit version exists; CCXT records the exact lock-resolved library version but does not assert an upstream venue API version; on-chain DeFi uses chain/network plus contract-address and ABI/selector fingerprints, while REST-backed DeFi follows the native rule; TradFi inherits the shared IBKR gateway protocol and has no independent exchange version. Structural hashes ignore values, timestamps, ordering, and secrets.
- 2026-08-21, slot 14: real run at 2026-08-21T00:00:00Z inspected 17 cassettes, found 13 stale at the 90-day budget and 4 undated sports cassettes, and exited 1. This confirms an actionable failure state rather than a forced-green stub.
- **2026-08-21, slot 14, implementation ship**: `execution-service@1d7c1cf4a6` landed via quickmerge after `bash scripts/quality-gates.sh --no-fix` exited 0 (8,898 passed, 22 skipped, 1 xfailed; 82.57% coverage). The checker is offline and read-only: it fingerprints normalized response structure, ignores values/order/timestamps, and applies a 90-day capture-date budget; the live run reported 13 stale and 4 undated cassettes for Phase 4 follow-up.
- **2026-08-22, slot 8, ccxt version-story confirmation**: `execution-service@48bf2728`. Confirmed the pyproject/uv.lock ccxt range (`>=4.5.24,<5.0.0`, resolved `4.5.39`) is still the pinning mechanism per Phase 1's decision — no upstream-venue HTTP assertion added underneath ccxt, structural cassette checks remain the drift guard. Made this a real runnable check rather than only a design-doc claim: `CCXT_VERSION_RANGE` + `assert_ccxt_version_pinned()` in `ccxt_common.py`, with unit tests (`test_ccxt_common.py::TestAssertCcxtVersionPinned`) covering both the in-range pass and an out-of-range `RuntimeError`. Full `quality-gates.sh` green; shipped via quickmerge, verified on origin.
