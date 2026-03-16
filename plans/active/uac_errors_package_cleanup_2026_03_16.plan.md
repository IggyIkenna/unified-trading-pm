---
name: uac-crosscutting-cleanup
overview: |
  Clean up duplicated, mis-categorized, and orphaned schemas in unified-api-contracts canonical/crosscutting/.
  Errors: (1) delete duplicate canonical/errors/ package, (2) deduplicate ErrorAction/VenueErrorClassification,
  (3) re-categorize misplaced venues to match VENUE_REGISTRY.
  Crosscutting modules: (4) delete fully-orphaned risk.py (0 imports), (5) prune dead symbols from
  analytics.py and connectivity.py, (6) resolve UAC↔UIC duplicate definitions for Factor* and WS lifecycle types.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: layer-1-delete-duplicate-errors-package
    content: |
      - [ ] [AGENT] P0. Delete `canonical/errors/` — it is byte-for-byte identical to
        `canonical/crosscutting/errors/` (all 7 files: __init__.py, _canonical.py, _types.py,
        altdata.py, cefi.py, defi.py, sports.py). Verify no external consumers import from
        `unified_api_contracts.canonical.errors` (vs `canonical.crosscutting.errors`). If any do,
        redirect their imports to `canonical.crosscutting.errors` first, then delete.
    status: todo
    note: "Both packages confirmed identical via diff. crosscutting/ is the documented home per UAC layout."

  - id: layer-2-deduplicate-erroraction-venue-error
    content: |
      - [ ] [AGENT] P0. In `canonical/crosscutting/errors/_canonical.py`, remove the duplicate
        definitions of `ErrorAction` (StrEnum) and `VenueErrorClassification` (dataclass). Replace
        with imports from `._types`. The _canonical.py docstring says "self-contained (no internal
        or schemas imports)" but there is no circular dependency risk — _types.py does not import
        from _canonical.py. Update __all__ in _canonical.py accordingly.
    status: todo
    note:
      "Both classes are identical in _types.py and _canonical.py. _types.py is the upstream used by venue data files."

  - id: layer-3a-create-tradfi-errors-file
    content: |
      - [ ] [AGENT] P1. Create `canonical/crosscutting/errors/tradfi.py` with VENUE_ERRORS_TRADFI
        dict. Move these venues from their current wrong files:
        - From cefi.py: tardis, yahoo_finance, ibkr, databento
        - From altdata.py: barchart, fred, ecb, ofr, openbb
        These are all TradFi venues per VENUE_REGISTRY. No tradfi.py file exists today.
    status: todo
    note: "9 TradFi venues currently scattered across cefi.py and altdata.py."

  - id: layer-3b-create-onchain-perps-errors-file
    content: |
      - [ ] [AGENT] P1. Create `canonical/crosscutting/errors/onchain_perps.py` with
        VENUE_ERRORS_ONCHAIN_PERPS dict. Move from altdata.py: hyperliquid, aster.
        These are Onchain Perps per VENUE_REGISTRY, not altdata.
    status: todo
    note: "2 Onchain Perps venues currently in altdata.py."

  - id: layer-3c-fix-defi-misplacements
    content: |
      - [ ] [AGENT] P1. Move misplaced DeFi venues to defi.py:
        - From altdata.py: aave_v3 (already has entries in defi.py? check for duplication first)
        - From sports.py: instadapp, defillama (both are DeFi per VENUE_REGISTRY)
        - From altdata.py: bloxroute (DeFi infra — decide: defi.py or separate infra file)
        - From cefi.py: alchemy, thegraph (DeFi infra — same decision)
        Note: bloxroute, alchemy, thegraph are NOT in VENUE_REGISTRY — may belong in a
        separate infra.py or should be validated for inclusion.
    status: todo
    note:
      "instadapp/defillama confirmed DeFi in VENUE_REGISTRY. alchemy/thegraph/bloxroute are DeFi infra but not in
      registry."

  - id: layer-3d-fix-altdata-to-only-altdata
    content: |
      - [ ] [AGENT] P1. After moving misplaced venues out, altdata.py should contain only
        actual alternative data providers. Currently coinglass and hyblock are the only true
        altdata venues — but they are NOT in VENUE_REGISTRY. Decide: add to VENUE_REGISTRY
        or document as ancillary/non-registry venues. Also move versifi out (not altdata).
    status: todo
    note:
      "Post-cleanup altdata.py may be nearly empty. Consider merging into a broader file or adding these venues to
      VENUE_REGISTRY."

  - id: layer-3e-fix-sports-to-only-sports
    content: |
      - [ ] [AGENT] P1. After moving DeFi venues out of sports.py, validate remaining:
        - polymarket, betfair, kalshi, smarkets, betdaq — prediction markets/sports (correct)
        - glassnode, arkham — onchain analytics/altdata (WRONG — move to altdata.py)
        - onchain_revert — crosscutting generic (WRONG — move to a crosscutting section or own file)
        - sports_generic — generic sports errors (correct)
        Note: polymarket/betfair/kalshi/smarkets/betdaq/glassnode/arkham are NOT in VENUE_REGISTRY.
    status: todo
    note: "glassnode/arkham are onchain analytics, not sports. onchain_revert is a generic EVM revert handler."

  - id: layer-3f-update-init-exports
    content: |
      - [ ] [AGENT] P1. Update `canonical/crosscutting/errors/__init__.py` to import from the
        new files (tradfi.py, onchain_perps.py). Add VENUE_ERRORS_TRADFI and
        VENUE_ERRORS_ONCHAIN_PERPS to the merged VENUE_ERROR_MAP dict and __all__.
    status: todo
    note: ""

  - id: layer-4-registry-parity-audit
    content: |
      - [ ] [AGENT] P2. Audit venue parity between VENUE_ERROR_MAP keys and UMI VENUE_REGISTRY
        keys. Document which error-map venues are NOT in VENUE_REGISTRY (15 currently:
        polymarket, betfair, kalshi, smarkets, betdaq, glassnode, arkham, coinglass, hyblock,
        versifi, bloxroute, alchemy, thegraph, onchain_revert, sports_generic) and decide:
        (a) add to VENUE_REGISTRY, (b) keep as ancillary with comment, or (c) remove.
    status: todo
    note: "All 33 VENUE_REGISTRY venues are covered. 15 extra non-registry venues exist in error maps."

  - id: layer-5-delete-orphaned-risk-module
    content: |
      - [ ] [AGENT] P0. Delete `canonical/crosscutting/risk.py` — ALL 10 symbols are INTERNAL
        computations, not external data normalization. None belongs in UAC per architecture.
        Specific dispositions:
        - SpanMarginLeg, MultiAssetMarginCalculation: ALREADY DUPLICATED in UIC risk.py — delete
        - PnLAttributionRecord, RealTimePnLRecord: move to UIC (internal P&L computation)
        - RiskLimitBreach: consolidate with UIC AlertMessage (same semantic)
        - VaRMethod, VaRRequest, VaRResult, StressScenario, StressTestResult: move to UIC
          (internal quant risk — no implementation yet, keep as framework in UIC)
        Remove from crosscutting __init__.py and any facade re-exports.
    status: todo
    note:
      "All 10 are internal computations. 2 already in UIC (SpanMarginLeg, MultiAssetMarginCalculation). UIC has 24 risk
      schemas already."

  - id: layer-6-fix-analytics-external-internal-split
    content: |
      - [ ] [AGENT] P1. analytics.py mixes EXTERNAL schemas (correct in UAC) with INTERNAL
        schemas (should be UIC). Split by disposition:
        KEEP IN UAC (external data normalization):
        - AlternativeDataType, AlternativeDataSignal, SentimentScore (used, external feeds)
        - SatelliteObservation, OptionsFlowRecord, DarkPoolPrintRecord (zero imports but
          external normalization schemas — keep in UAC, they're aspirational for external
          data vendors like Orbital Insight, FINRA ADF, IEX)
        MOVE TO UIC (internal computations, currently dead in UAC):
        - CorrelationRegime, CrossAssetCorrelationMatrix, CorrelationRegimeChange (internal
          correlation computation from historical prices — not from external APIs)
        REMOVE FROM UAC (already in UIC as SSOT):
        - FactorType, FactorExposure, FactorAttributionRecord, FactorAttributionModel
          (internal factor models — UIC domain/analytics/factor_exposure.py is SSOT.
          UAC should import and re-export from UIC, not redefine.)
        Update __all__ and facade re-exports.
    status: todo
    note:
      "6 external (keep in UAC), 3 internal dead (move to UIC), 4 internal duplicated (remove from UAC, UIC is SSOT)"

  - id: layer-7-prune-dead-connectivity-symbols
    content: |
      - [ ] [AGENT] P1. Remove 4 dead symbols from `canonical/crosscutting/connectivity.py`:
        - WebSocketPingFrame (zero consumer imports)
        - WebSocketPongFrame (zero consumer imports)
        - UnsubscribeRequest (zero consumer imports — only UIC has its own version)
        - WebSocketConnectionState (test-only usage — keep if test contract alignment needs it)
        Keep: CanonicalWsMessage, WebSocketEvent, CanonicalWebSocketLifecycle,
        HealthPingResponse, WebSocketConnectionOpened, WebSocketConnectionClosed,
        SubscribeRequest, HeartbeatMessage.
    status: todo
    note: "8 used, 4 dead. Ping/Pong frames are low-level WS internals that no service needs as schemas."

  - id: layer-8-resolve-uac-uic-factor-duplicates
    content: |
      - [ ] [AGENT] P2. Resolve UAC↔UIC duplication for Factor* types:
        FactorType, FactorExposure, FactorAttributionRecord, FactorAttributionModel are defined
        in BOTH UAC (analytics.py) and UIC (domain/analytics/factor_exposure.py). UIC is SSOT
        per analytics ownership. Options:
        (a) UAC imports from UIC and re-exports (if UAC already depends on UIC) — preferred
        (b) Move canonical definitions to UAC and make UIC import from UAC (if UAC is upstream)
        (c) Keep both but document UIC as SSOT (status quo — fragile)
        Verify dependency direction: does UAC depend on UIC or vice versa?
    status: todo
    note: "strategy-service imports from both UAC and UIC. ml-training imports from both. Single SSOT needed."

  - id: layer-9-resolve-uac-uic-ws-duplicates
    content: |
      - [ ] [AGENT] P2. Resolve UAC↔UIC duplication for WebSocket lifecycle types:
        HealthPingResponse exists in BOTH UAC (Pydantic BaseModel) and UIC (dataclass).
        WebSocketConnectionOpened, WebSocketConnectionClosed also duplicated with different
        type systems. Decide which repo owns WS lifecycle schemas and make the other import.
        UAC connectivity.py uses CanonicalBase (Pydantic); UIC uses plain dataclasses.
    status: todo
    note: "Type system mismatch: UAC = Pydantic, UIC = dataclass. Need single owner."

  - id: layer-10-quality-gates
    content: |
      - [ ] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` after
        all changes. Ensure no import errors, type errors, or test failures.
    status: todo
    note: ""
isProject: false
---

# UAC Errors Package Cleanup

## Context

Discovered 2026-03-16 during UAC duplication scan:

### Issue 1: Full package duplication

`canonical/errors/` and `canonical/crosscutting/errors/` are byte-for-byte identical (all 7 files). One must be deleted.
`crosscutting/` is the documented home per UAC layout docs.

### Issue 2: Within-package type duplication

Both `_types.py` and `_canonical.py` independently define identical `ErrorAction` (StrEnum) and
`VenueErrorClassification` (dataclass). `_canonical.py` should import from `_types.py`.

### Issue 3: Venue mis-categorization

Venues are scattered across the wrong files. The 4 files (cefi, defi, altdata, sports) don't match the VENUE_REGISTRY's
4 categories (cefi, tradfi, defi, onchain_perps). No tradfi.py exists. No onchain_perps.py exists. DeFi protocols appear
in sports.py and altdata.py. TradFi venues appear in cefi.py and altdata.py.

### Issue 4: Registry parity gap

15 venues in error maps are not in VENUE_REGISTRY. All 33 VENUE_REGISTRY venues are covered but in wrong files.

## Crosscutting Modules Audit (2026-03-16)

| Module              | Symbols | Used | Dead | Status     | Notes                                                                                                          |
| ------------------- | ------- | ---- | ---- | ---------- | -------------------------------------------------------------------------------------------------------------- |
| **rate_limits.py**  | 2       | 2    | 0    | **Clean**  | 32 import hits, 10+ services. No action needed.                                                                |
| **latency.py**      | 8       | 8    | 0    | **Clean**  | execution-service, UMI, market-tick-data. No overlaps.                                                         |
| **connectivity.py** | 12      | 8    | 4    | **Prune**  | PingFrame, PongFrame, UnsubscribeRequest, ConnectionState dead. 5 symbols duplicate UIC websocket/lifecycle.py |
| **analytics.py**    | 13      | 5    | 8    | **Prune**  | Factor* duplicate UIC. Correlation*, Satellite, OptionsFlow, DarkPool dead.                                    |
| **risk.py**         | 10      | 0    | 10   | **Delete** | Fully orphaned. risk-service uses UIC types instead.                                                           |

### UAC↔UIC Overlap Map

| UAC Symbol                | UIC Location                        | Type Mismatch                     | Resolution                   |
| ------------------------- | ----------------------------------- | --------------------------------- | ---------------------------- |
| FactorType                | domain/analytics/factor_exposure.py | No (both StrEnum)                 | Single SSOT needed           |
| FactorExposure            | domain/analytics/factor_exposure.py | No (both Pydantic)                | Single SSOT needed           |
| FactorAttributionRecord   | domain/analytics/factor_exposure.py | No                                | Single SSOT needed           |
| FactorAttributionModel    | domain/analytics/factor_exposure.py | No                                | Single SSOT needed           |
| HealthPingResponse        | domain/websocket/lifecycle.py       | YES (UAC=Pydantic, UIC=dataclass) | Reconcile type systems       |
| WebSocketConnectionOpened | domain/websocket/lifecycle.py       | YES (UAC=Pydantic, UIC=dataclass) | Reconcile type systems       |
| WebSocketConnectionClosed | domain/websocket/lifecycle.py       | YES (UAC=Pydantic, UIC=dataclass) | Reconcile type systems       |
| WebSocketPingFrame        | domain/websocket/lifecycle.py       | YES                               | Both dead — delete from both |
| WebSocketPongFrame        | domain/websocket/lifecycle.py       | YES                               | Both dead — delete from both |

## Venue Placement Summary (current → target)

| Venue          | Current File | VENUE_REGISTRY Category | Target File          |
| -------------- | ------------ | ----------------------- | -------------------- |
| binance        | cefi.py      | cefi                    | cefi.py              |
| bybit          | cefi.py      | cefi                    | cefi.py              |
| okx            | cefi.py      | cefi                    | cefi.py              |
| deribit        | cefi.py      | cefi                    | cefi.py              |
| coinbase       | cefi.py      | cefi                    | cefi.py              |
| ccxt           | cefi.py      | cefi                    | cefi.py              |
| upbit          | cefi.py      | cefi                    | cefi.py              |
| tardis         | cefi.py      | tradfi                  | **tradfi.py**        |
| yahoo_finance  | cefi.py      | tradfi                  | **tradfi.py**        |
| ibkr           | cefi.py      | tradfi                  | **tradfi.py**        |
| databento      | cefi.py      | tradfi                  | **tradfi.py**        |
| alchemy        | cefi.py      | NOT IN REGISTRY         | **infra or defi**    |
| thegraph       | cefi.py      | NOT IN REGISTRY         | **infra or defi**    |
| barchart       | altdata.py   | tradfi                  | **tradfi.py**        |
| fred           | altdata.py   | tradfi                  | **tradfi.py**        |
| ecb            | altdata.py   | tradfi                  | **tradfi.py**        |
| ofr            | altdata.py   | tradfi                  | **tradfi.py**        |
| openbb         | altdata.py   | tradfi                  | **tradfi.py**        |
| hyperliquid    | altdata.py   | onchain_perps           | **onchain_perps.py** |
| aster          | altdata.py   | onchain_perps           | **onchain_perps.py** |
| aave_v3        | altdata.py   | defi                    | **defi.py**          |
| bloxroute      | altdata.py   | NOT IN REGISTRY         | **infra or defi**    |
| coinglass      | altdata.py   | NOT IN REGISTRY         | altdata.py           |
| hyblock        | altdata.py   | NOT IN REGISTRY         | altdata.py           |
| versifi        | altdata.py   | NOT IN REGISTRY         | TBD                  |
| instadapp      | sports.py    | defi                    | **defi.py**          |
| defillama      | sports.py    | defi                    | **defi.py**          |
| glassnode      | sports.py    | NOT IN REGISTRY         | **altdata.py**       |
| arkham         | sports.py    | NOT IN REGISTRY         | **altdata.py**       |
| onchain_revert | sports.py    | NOT IN REGISTRY         | **crosscutting**     |
| polymarket     | sports.py    | NOT IN REGISTRY         | sports.py            |
| betfair        | sports.py    | NOT IN REGISTRY         | sports.py            |
| kalshi         | sports.py    | NOT IN REGISTRY         | sports.py            |
| smarkets       | sports.py    | NOT IN REGISTRY         | sports.py            |
| betdaq         | sports.py    | NOT IN REGISTRY         | sports.py            |
| sports_generic | sports.py    | NOT IN REGISTRY         | sports.py            |
| balancer       | defi.py      | defi                    | defi.py              |
| curve          | defi.py      | defi                    | defi.py              |
| ethena         | defi.py      | defi                    | defi.py              |
| euler          | defi.py      | defi                    | defi.py              |
| fluid          | defi.py      | defi                    | defi.py              |
| etherfi        | defi.py      | defi                    | defi.py              |
| lido           | defi.py      | defi                    | defi.py              |
| morpho         | defi.py      | defi                    | defi.py              |
| uniswap_v2     | defi.py      | defi                    | defi.py              |
| uniswap_v3     | defi.py      | defi                    | defi.py              |
| uniswap_v4     | defi.py      | defi                    | defi.py              |
