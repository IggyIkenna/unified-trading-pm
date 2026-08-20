---
doc_type: audit-result
title: Client artefact Axis-0 verification — instrument IDs, venue glossary, archetype-readiness — second-pass audit 2026-08-18
summary: >-
  Independent code-level verification of previously-unverified content in the two client-disclosure HTML artefacts
  (Nick AI's platform-external-api-walkthrough.html, Elysium's strategy-service-walkthrough.html). Instrument-ID
  examples: 3 of 4 confirmed byte-for-byte real against build_canonical_instrument_id()/build_instrument_id() in
  unified-api-contracts, but the shared CeFi spot-pair example in BOTH artefacts uses the wrong instrument-type
  token ("SPOT" instead of the real "SPOT_PAIR"). Venue glossary: all 7 named venues across both artefacts (from a
  sparse, non-tabular set of mentions) are real, correctly-spelled, correctly-bound entries in VENUE_TO_ADAPTER_KEY.
  Archetype-readiness: the task brief's premise that ARCHETYPE_FEATURE_GROUPS declares "~40 of 60" archetypes is
  itself wrong — the real count is 55 of 60 declared, 5 explicitly and deliberately undeclared (4 MEV archetypes +
  PORTFOLIO_MULTI_STRATEGY) — and neither artefact claims 60/60 declared-input coverage; both are unusually careful
  here (readiness is stated as "planned, not built" / "unverified by construction", and Nick AI's §14 explicitly
  flags that many archetypes' input declarations are "deliberately incomplete"). A second, independently-found
  overclaim: Elysium's §04 states "Every archetype declares its parameters in a schema registry" — the real
  PARAM_SCHEMA_REGISTRY covers only 35 of 60 archetypes, a quantifiable, confirmed-wrong blanket claim.
status: pass
nature: record
audited_scope: >-
  platform-external-api-walkthrough.html and strategy-service-walkthrough.html — canonical-instrument-ID examples,
  venue-glossary content, and archetype-readiness (batch/paper/live) claims, verified against
  build_canonical_instrument_id()/build_instrument_id(), VENUE_TO_ADAPTER_KEY, and ARCHETYPE_FEATURE_GROUPS/
  PARAM_SCHEMA_REGISTRY.
date: 2026-08-18
auditor: >-
  1 general-purpose sub-agent (sonnet), dispatched as one of 5 parallel agents doing a second-pass audit of
  client-disclosure artefacts, read-only, SUB_AGENT_MANDATORY_RULES.md pasted at spawn.
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting, defi]
stage: [data, strategy, meta]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
related:
  [
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
  ]
created: 2026-08-18
tags: [client-disclosure, nick-ai, elysium, audit, axis-0, instrument-id, venue-glossary, archetype-readiness]
---

# Client artefact Axis-0 verification — 2026-08-18

Second-pass, independent verification of content in both artefacts that traces back to an earlier sub-agent report
(`/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md`) but was itself never checked against the
actual code. This report is read-only findings — neither HTML file nor any plan file was edited.

**Files checked**:
- `unified-trading-pm/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` (Nick AI)
- `unified-trading-pm/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` (Elysium)

**Code read directly**:
- `unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py` (`build_instrument_id`,
  `build_canonical_instrument_id`)
- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/canonical_ids.py` (`build_instrument_id`,
  `build_prediction_instrument_id`)
- `unified-api-contracts/unified_api_contracts/_instrument_enums.py` (`InstrumentType`)
- `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py` (`VENUE_TO_ADAPTER_KEY`)
- `unified-api-contracts/unified_api_contracts/registry/venue_constants.py` (`VENUE_CHAIN_MAP`)
- `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` (`SUBGRAPH_IDS`,
  `get_supported_chains_for_protocol`)
- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py` (`StrategyArchetype`)
- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_feature_groups.py`
  (`ARCHETYPE_FEATURE_GROUPS`, `UNDECLARED_ARCHETYPES`)
- `strategy-service/strategy_service/engine/strategies/v2/param_schema.py` (`PARAM_SCHEMA_REGISTRY`,
  `check_archetype_schema_coverage`)

---

## Part 1 — Canonical instrument IDs

### The real shape(s), read directly from `canonical_id_builder.py`

**Correction to the task brief's premise**: the brief states there are "three real ID shapes." Reading
`build_instrument_id`'s dispatch branches directly, this undercounts. The real structure is better described as
**one shared top-level grammar with ~8 distinct symbol-suffix shapes**, plus one asset group (`sports`) that bypasses
the grammar entirely at the `build_canonical_instrument_id` dispatch level:

| # | Shape | Instrument types | Example (from the module's own docstring) |
| --- | --- | --- | --- |
| 1 | `VENUE:TYPE:SYMBOL` | SPOT_PAIR, PERPETUAL, EQUITY_PERP, TOKENIZED_EQUITY | `BYBIT:PERPETUAL:BTCUSDT` |
| 2 | `VENUE:TYPE:SYMBOL-YYYYMMDD` | FUTURE | `CME:FUTURE:ES-20260620` |
| 3 | `VENUE:TYPE:SYMBOL-YYYYMMDD-STRIKE-C\|P` | OPTION | `DERIBIT:OPTION:BTC-20260328-65000-C` |
| 4 | `VENUE-CHAIN:TYPE:SYMBOL` (case preserved) | DeFi types (POOL, LENDING, LST, STAKING, …) | `AAVE_V3-ARBITRUM:LENDING:USDC` |
| 5 | `VENUE:TYPE:SYMBOL-QUOTE` (default `-USD`) | TradFi cash types (EQUITY, INDEX, CURRENCY, ETF, BOND, COMMODITY) | `NASDAQ:EQUITY:AAPL-USD` |
| 6 | `VENUE:TYPE:SYMBOL@LIN\|INV[-YYYYMMDD[-STRIKE-C\|P]]` | PERPETUAL/FUTURE/OPTION w/ `margin_marker` | `BINANCE_FUTURES:PERPETUAL:BTC-USDT@LIN` |
| 7 | `VENUE:COMBO:SYMBOL` (opaque) / `VENUE:COMBO:UNDERLYING-STRATEGY-ANCHORS…` (structured) | COMBO | `CME:COMBO:SP500-BUTTERFLY-20240621-5500-5600-5700` |
| 8 | `VENUE[-CHAIN]:TYPE:RAW_SYMBOL` (passthrough, no reconstruction) | any, `passthrough=True` | `DERIBIT:OPTION:BTC-9JUL26-56000-C` |
| 9 | Sports/prediction wrapper `VENUE:TYPE:<pre-built domain id>` (embeds further colons — the one case where `:` inside `symbol` is legal) | PREDICTION_MARKET, EXCHANGE_ODDS, FIXED_ODDS, PROP | `FOOTBALL:BETFAIR_EX_UK:MATCH_ODDS:…` (see below) |
| 10 | `LEAGUE:HOME_v_AWAY:DATE` — `asset_group=sports` bypasses `VENUE:TYPE:SYMBOL` entirely at `build_canonical_instrument_id` | n/a (fixtures, not instruments) | `ENG_PREMIER_LEAGUE:ARSENAL_v_CHELSEA:20260322` |

### Examples extracted from the artefacts

Both artefacts carry an **identical** instrument-ID code block (Nick AI §03 lines 434–439; Elysium §03 lines
337–340 — same content, same wording, confirming it is shared/copied source material):

| Claim (artefact text) | Verified reality | Verdict |
| --- | --- | --- |
| `BINANCE-SPOT:SPOT:BTCUSDT` | `InstrumentType.SPOT_PAIR.value == "SPOT_PAIR"` (`_instrument_enums.py:31`) — there is **no** `InstrumentType` member with value `"SPOT"`. `_build_cefi_simple()` would produce `BINANCE-SPOT:SPOT_PAIR:BTCUSDT`, not `…:SPOT:…`. | **WRONG** |
| `AAVE_V3-ARBITRUM:LENDING:USDC` | Byte-for-byte identical to the module's own docstring example (`canonical_id_builder.py:82-85`); `ARBITRUM` is a real registered chain for `aave_v3` (`SUBGRAPH_IDS["aave_v3"]["ARBITRUM"]`, `_defi.py:66`), auto-generated into `VENUE_TO_ADAPTER_KEY` via the `VENUE_PREFIX_TO_PROTOCOL` loop (`venue_adapter_keys.py:431-436`). | **CONFIRMED** |
| `CME:FUTURE:ES-20260320` | Matches `_build_future()`'s plain (no margin-marker) shape exactly (shape #2 above); `FUTURE` is not in `_TRADFI_CASH_QUOTE_SUFFIXED_TYPES` so no `-USD` suffix is expected. Date differs from the docstring's own `20260620` example but the date is illustrative, not load-bearing. | **CONFIRMED** (shape) |
| `FOOTBALL:BETFAIR_EX_UK:MATCH_ODDS:EPL:2025-26:ARSENAL-CHELSEA::HOME` and the Polymarket twin | Byte-for-byte identical to `build_prediction_instrument_id`'s own docstring example (`canonical_ids.py:315-316`: *"`FOOTBALL:POLYMARKET:MATCH_ODDS:EPL:2025-26:ARSENAL-CHELSEA::HOME`"* / *"`FOOTBALL:BETFAIR_EX_UK:MATCH_ODDS:EPL:2025-26:ARSENAL-CHELSEA::HOME`"*). Note: the module's own **top-of-file** docstring example (line 25) spells the league `ENG_PREMIER_LEAGUE`, not `EPL` — a pre-existing, harmless internal inconsistency in the code's own docstrings, not something to fault the artefact for since it copied a real, valid example verbatim. | **CONFIRMED** |

The `BINANCE-SPOT:SPOT:BTCUSDT` error sits in the same code block as two byte-for-byte-correct examples
(`AAVE_V3-ARBITRUM:LENDING:USDC` uses the real `LENDING` value; `CME:FUTURE:ES-20260320` uses the real `FUTURE`
value) — so this isn't a stylistic abbreviation choice, it is an inconsistent, wrong token sitting next to two
correct ones in the same three-line block, in **both** artefacts identically.

### Severity

**P1** — a definitional/technical error in the one code example an "AI-orchestrated audience" (Nick AI's own stated
readership) would most likely copy verbatim to construct a real query. Not P0 on its own (it doesn't misstate a
capability or cross a disclosure boundary), but it directly undermines the artefact's own stated selling point
("whatever you pull, you get a normalised identity"). Present identically in both artefacts — one fix in the shared
source material fixes both.

---

## Part 2 — Venue glossary

### What is actually in the artefacts

Neither artefact contains a dedicated venue-glossary table. Nick AI's "Glossary — the two words that carry the most
weight" (§03, line 407) defines the **terms** "Venue" / "Asset group" / "Instrument ID" — it names zero specific
venues. The only concrete venue names appearing anywhere in either document are the handful embedded in the
instrument-ID examples above, plus two DeFi examples in the surrounding prose (Nick AI line 416: *"DeFi venues carry
the chain in the identity itself (`AAVE_V3-ARBITRUM`, `LIDO-ETHEREUM`)"*) and a Kalshi mention (Nick AI line 463,
about its native ticker format — not a canonical venue-ID claim, see "what I could not verify" below).

| Venue named | Where | `VENUE_TO_ADAPTER_KEY` entry | Verdict |
| --- | --- | --- | --- |
| `BINANCE-SPOT` | Both, §03 code block | `"BINANCE-SPOT": "tardis"` (`venue_adapter_keys.py:107`) | **CONFIRMED** |
| `AAVE_V3-ARBITRUM` | Both, §03 code block + Nick AI prose | Auto-generated from `VENUE_PREFIX_TO_PROTOCOL["AAVE_V3"]="aave_v3"` × `SUBGRAPH_IDS["aave_v3"]["ARBITRUM"]` | **CONFIRMED** |
| `LIDO-ETHEREUM` | Nick AI prose (line 416) | `"LIDO-ETHEREUM": "lido"` (`venue_adapter_keys.py:178`) | **CONFIRMED** |
| `CME` | Both, §03 code block | `"CME": "databento"` (`venue_adapter_keys.py:143`) | **CONFIRMED** |
| `BETFAIR_EX_UK` | Both, §03 code block | Not a `VENUE_TO_ADAPTER_KEY` member (bare `BETFAIR` maps to a real-data-axis sports adapter key, but `BETFAIR_EX_UK` specifically is the sports-execution-axis venue) — confirmed real via `venue_constants.py:75` (`BETFAIR_EX_UK = "BETFAIR_EX_UK"`) and `SPORTS_EXECUTION_ADAPTER_VENUES` in `venue_adapter_keys.py:482` (real, wired `betfair.py` execution adapter). | **CONFIRMED** |
| `POLYMARKET` | Both, §03 code block | `"POLYMARKET": "polymarket"` (`venue_adapter_keys.py:171`) | **CONFIRMED** |
| `KALSHI` | Nick AI prose (line 462) | `"KALSHI": "kalshi"` (`venue_adapter_keys.py:172`) | **CONFIRMED** |

All 7 named venues, across both artefacts, are real, correctly spelled, and correctly bound in the registry.
`VENUE_CHAIN_MAP` (`venue_constants.py:907-923`) is a narrower, legacy-purpose registry (shared-wallet chain routing
for ~15 bare-form DeFi venue constants like `AAVE_V3`, `LIDO`) distinct from the venue-chain composition used inside
canonical instrument IDs — neither artefact makes a claim that depends on `VENUE_CHAIN_MAP` specifically (the
DeFi chain-suffix mechanism they describe is a real, separate, confirmed feature of `canonical_id_builder.py`'s
`_venue_token()`), so this registry surfaced no discrepancies but is flagged here for completeness per the task's
Part 2 instructions.

### Severity

No findings — **CONFIRMED clean**. The venue content is real but sparse; there is no larger venue-glossary table to
audit in either document as things stand today.

---

## Part 3 — Archetype-readiness (batch/paper/live)

### Correcting the task brief's premise, from the code directly

The brief states `ARCHETYPE_FEATURE_GROUPS` "declares ~40 of 60 archetypes." **This is wrong, measured directly**:

- `StrategyArchetype` (`enums.py`) has **60 members** — 59 declared as simple `= "…"` literals plus one,
  `MARKET_MAKING_CONTINUOUS`, declared via a multi-line parenthesised assignment (`enums.py:140-142`) that a naive
  regex scan misses (confirmed by direct, careful parse of the class body, not a `grep -c` proxy).
- The class's own docstring literally says **"59 archetypes"** (`enums.py:34`) — this is itself a stale/wrong count
  in the code's own docstring (off by the one multi-line-assigned legacy member); worth fixing separately but out of
  scope for this artefact audit.
- `ARCHETYPE_FEATURE_GROUPS` declares **55 of the 60** members (precise parse of the dict literal, not a line-count
  proxy). `UNDECLARED_ARCHETYPES` — the complement — has exactly **5** members: `ARBITRAGE_MEV_SANDWICH`,
  `ARBITRAGE_MEV_JIT_LIQUIDITY`, `ARBITRAGE_MEV_BACKRUN`, `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, and
  `PORTFOLIO_MULTI_STRATEGY` — exactly matching the module's own docstring, which names these 5 explicitly
  (`archetype_feature_groups.py:64-80`) and explains why each is a genuine, deliberate registry gap (MEV needs
  mempool/pending-tx visibility the codebase has no adapter for at all; `PORTFOLIO_MULTI_STRATEGY` is a
  strategy-of-strategies shape that doesn't fit the registry's per-instrument model) rather than "not yet reviewed."
  The docstring's own `ArchetypeFeatureGroupUndeclaredError` raises loudly rather than returning an empty set for
  these 5 — confirmed by reading the raise site (`archetype_feature_groups.py:269-274`).

So the real state is **55/60 declared (91.7%), 5/60 deliberately undeclared** — not "~40/60" as the brief assumed.

### Does either artefact imply full (60/60) coverage?

**No clean instance found of either artefact claiming 60/60 archetype-input-declaration coverage.** Both documents
are, if anything, unusually careful about this exact axis:

| Claim (artefact text) | Verified reality | Verdict |
| --- | --- | --- |
| Nick AI §14 (line 1042-1044): *"planned — a capability audit deriving archetype readiness across batch, paper and live is specified and not yet built. Until it runs, that axis reports `unverified`…"* | Matches: no such capability audit exists in the codebase yet; `ARCHETYPE_FEATURE_GROUPS` is a *prerequisite input* to such an audit, not the audit itself. | **CONFIRMED** |
| Nick AI §14 (line 1057-1059): *"The strategy leg passes 24 of 864, dominated by archetypes whose input declarations are deliberately incomplete rather than by venues that cannot trade."* | This is an honest, direct echo of `archetype_feature_groups.py`'s own "coverage is deliberately partial" framing — the artefact does **not** claim full coverage here. | **CONFIRMED** |
| Elysium §01 (line 218, 237-239): *"60 Archetypes declared / 32 Factory-registered… The gap between 60 declared archetypes and 32 registered is deliberate… Counting declarations as capabilities would overstate what the system can run today."* | This "60 declared" is a **different axis** than `ARCHETYPE_FEATURE_GROUPS` — it means `StrategyArchetype` enum membership (60, confirmed above) vs. factory registration (32) — a claim the *first-pass* audit already independently confirmed clean (`nick_ai_and_elysium_artefact_audit_2026_08_18.md` line 333-334). Re-confirmed here: correct on its own terms, and explicitly self-aware about not overstating capability from mere declaration. | **CONFIRMED**, distinct axis — flagged only so a reader doesn't conflate "60 declared (enum)" with "60 have declared feature-group inputs" |
| Elysium §02 (line 258-274): *"Archetypes carry a readiness state too… derived, never declared… planned — a capability audit that derives this per archetype across all three modes is specified but not yet built. Until it exists, archetype readiness reports `unverified` by construction…"* | Matches the operator's "readiness derived, never declared" ruling exactly; no archetype is claimed ready in any mode. | **CONFIRMED** |
| Nick AI §09 (line 799, 804): *"An archetype declares what it consumes… and that declaration is machine-checked"* / *"Each archetype names the data types and feature groups it requires"* | Read as an absolute, universal statement this is inaccurate — 5/60 archetypes explicitly do **not** have a declared feature-group mapping (by design, not oversight). The document's own §14 (24 lines later, cited above) separately acknowledges this incompleteness, so the two sections sit in tension rather than either flatly contradicting the other. A reader who only reads §09 in isolation would get a falsely-universal impression. | **WRONG** in isolation (self-corrected elsewhere in the same document) |
| Elysium §04 (line 454): *"Every archetype declares its parameters in a schema registry rather than in free-form configuration…"* | `PARAM_SCHEMA_REGISTRY` (`param_schema.py:187`) has exactly **35 of 60** archetype keys, precisely counted from the dict literal (no `.update()` calls elsewhere in the file — confirmed by grepping every use site). The gap is large enough, and tracked by the codebase's own `check_archetype_schema_coverage()` (`param_schema.py:1165-1189`), that "every archetype" is a quantifiable, confirmed-wrong blanket claim — 25 archetypes have no parameter schema at all. | **WRONG** |

### Spot-check of specific per-archetype content against `ARCHETYPE_FEATURE_GROUPS`

Neither artefact makes granular per-archetype-to-feature-group claims in prose (e.g. neither says "CARRY_STAKED_BASIS
consumes lending_rates and lst_yields"), so there is little to spot-check on that specific axis. What both
artefacts *do* use are specific archetype **names** as illustrative examples — every one checked is a real,
currently-declared `StrategyArchetype` member with a real `ARCHETYPE_FEATURE_GROUPS` entry:

| Example used | Where | Real & declared? |
| --- | --- | --- |
| `CARRY_STAKED_BASIS@lido-uniswapv3-deribit-…` (slot-label example) | Elysium §02, line 298 | Yes — `StrategyArchetype.CARRY_STAKED_BASIS` is dispatch-traced (`archetype_feature_groups.py:99`, `{lending_rates, lst_yields}`); the venues named (Lido = staking, Uniswap v3 = spot hedge, Deribit = dated-future hedge) are architecturally consistent with a staked-basis carry structure. |
| `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` | Elysium §12, line 938 | Yes, same as above. |
| `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` | Elysium §12, line 939 | Yes — declared, `{cross_venue_spreads}` (`archetype_feature_groups.py:134`). |
| `KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS` | Elysium §12, line 940 | Yes — declared, `{technical_indicators, momentum, oscillators, moving_averages, volatility_realized}` (`archetype_feature_groups.py:120-122`). |

No wrong or fabricated archetype names found in either document.

### Severity

**P2** for the §09 "Each archetype names…" universal phrasing (real but self-qualified elsewhere in the same
document, and no numeric coverage claim attached). **P1** for the Elysium §04 "Every archetype declares its
parameters" claim — a specific, checkable, quantifiably false blanket statement (35/60, not 60/60) about a named,
real registry.

---

## Severity-ranked findings, all three parts

| Severity | Finding | Artefact | Part |
| --- | --- | --- | --- |
| P1 | Shared instrument-ID example uses wrong instrument-type token: `BINANCE-SPOT:SPOT:BTCUSDT` should be `BINANCE-SPOT:SPOT_PAIR:BTCUSDT` (`InstrumentType.SPOT_PAIR.value == "SPOT_PAIR"`, no `"SPOT"` member exists) | Both (identical code block) | 1 — Instrument IDs |
| P1 | "Every archetype declares its parameters in a schema registry" (§04) — real `PARAM_SCHEMA_REGISTRY` covers 35/60, not 60/60 | Elysium | 3 — Archetype-readiness |
| P2 | "Each archetype names the data types and feature groups it requires" (§09) reads as universal but 5/60 archetypes are deliberately undeclared; self-qualified 24 lines later in the same document's §14 | Nick AI | 3 — Archetype-readiness |
| — | Task brief's own premise ("~40 of 60 archetypes declared") is itself wrong — measured reality is 55/60 declared, 5/60 deliberately undeclared | n/a — corrects the audit brief, not the artefacts | 3 |
| — | Task brief's own premise ("three real ID shapes") is itself an undercount — measured reality is ~8-10 distinct symbol-suffix shapes under one shared top-level grammar, plus a separate sports-fixture bypass | n/a — corrects the audit brief, not the artefacts | 1 |

No hard disclosure-boundary issue found in this pass (this axis was already covered by the first-pass audit and was
not re-litigated here). No wrong or fabricated venue names found (Part 2 clean). No fabricated archetype names found
(Part 3 spot-check clean).

---

## What I could not verify

- **Kalshi's native ticker format** (`KXBTCD-26JUN24-T95000`, Nick AI line 463) — this is presented as Kalshi's own
  internal ticker convention, not a canonical-instrument-ID claim this task's registries cover. Not checked against
  the Kalshi adapter's real wire format; out of scope for the three named axes (instrument IDs / venue glossary /
  archetype-readiness) but worth a follow-up spot-check if the operator wants full coverage of that paragraph.
- **The "cross-venue detector over Kalshi, Polymarket and Betfair is shipped and paper-proven end to end" claim**
  (Nick AI §03, lines 460-461) — a live/shipped capability claim, not an instrument-ID/venue-glossary/archetype
  question. Belongs to the first-pass audit's Axis 2 (accuracy against the current system), not re-checked here.
- **Whether `PARAM_SCHEMA_REGISTRY`'s 35-entry set and `ARCHETYPE_FEATURE_GROUPS`'s 55-entry set overlap in any
  particular pattern** (e.g. is every schema-covered archetype also feature-group-declared?) — not cross-referenced;
  the two registries answer genuinely different questions (wizard parameter schema vs. feature-group data
  consumption) and doing so was not needed to resolve either specific artefact claim checked above.
- **Whether any OTHER prose in either artefact makes a narrower per-archetype coverage claim not caught by the
  grep patterns used** (`archetype`, `60`, `declares its parameters`, `/60`, `of 60`) — a full manual line-by-line
  read of both ~1,187-line files was not performed; targeted greps plus full reads of every section containing
  "archetype" were used instead. Given the grep hit counts (27 in Nick AI, 40 in Elysium) and the specific sections
  read in full, this is believed to be complete for the task's stated scope, but is not a claim of exhaustive
  line-by-line coverage.
