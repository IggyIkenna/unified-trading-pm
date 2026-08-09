---
doc_type: codex-ssot
title: DeFi completeness oracle — chain-truth denominator (design SSOT)
summary: >-
  Design SSOT for the DeFi completeness ORACLE — the on-chain, non-circular denominator that answers "do we have ALL
  DeFi instruments?" from chain state (factory `poolCount`, lending registries, protocol markets endpoints) rather than
  from our own catalogue. Replaces the circular `EXPECTED = ENUMERATED` Layer-1 measurement for DeFi in the
  honest-coverage v2 model with an external truth source: per (protocol, chain) `completeness_pct = enumerated /
  on_chain_truth`, plus the per-pool creation-block `available_from` genesis oracle that kills the RAYDIUM `1970-01-01`
  defect.
status: current
nature: ssot
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, honest-coverage, denominator, oracle, layer-1, catalogue, completeness, factory, genesis]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/defi-venue-protocol-catalogue.md,
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
  ]
created: 2026-07-06
authoritative_for:
  [
    DeFi completeness oracle (Layer-1 denominator source for defi),
    per-protocol/chain probe contract (CompletenessProbe),
    Tier-A subgraph vs Tier-B RPC probe policy,
    per-instrument creation-block `available_from` genesis rule for DeFi,
  ]
referenced_by:
owner:
last_reviewed: 2026-07-06
code_refs:
  [
    instruments-service/instruments_service/reference_data/adapters/defi/,
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/scripts/measure_honest_coverage.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
  ]
---

# DeFi completeness oracle — chain-truth denominator (design SSOT)

> **Why this exists.** The honest-coverage v2 Layer-1 model treats `EXPECTED = IS_catalogue × UAC_matrix` and reports
> completeness against it. For cefi / tradfi / sports / prediction that's fine — the CATALOGUE is derivable from
> external exchange listing endpoints, so it IS the denominator. For **DeFi that measurement is CIRCULAR**: our
> catalogue is derived from the same subgraph queries the manifest reads, so `EXPECTED == ENUMERATED` by construction
> and Layer-1 always reads 100%. The catalogue can be missing an entire protocol × chain (e.g. Uniswap V3 on Base) and
> the number stays green. DeFi UNIQUELY has an EXTERNAL truth we can query: **on-chain factory counts / protocol
> registries**. This SSOT specifies the oracle that measures against that external truth and how it plugs into the
> Layer-1 denominator.
>
> **Provenance.** Design authored 2026-07-06 (data_engineering, slot 5) fulfilling
> `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md` item — "DeFi completeness ORACLE design"
> (Gate: an oracle design that answers defi could-exist completeness from chain state, not the manifest). Sketch source:
> `plans/active/instruments_foundation_completeness_2026_06_24.md` §Phase 2+ (defi Tier-B).

---

## 1. What the oracle answers

For each `(protocol, chain)` in UAC `PROTOCOL_CAPABILITIES`, one scalar: how many instruments exist on-chain? Then one
comparison: how many does the IS catalogue enumerate today? The delta is the **honest, quantified backfill signal** —
never a guess.

```
completeness_pct(protocol, chain) = enumerated_count / on_chain_expected_count
                                    │              │
                                    │              └─ external truth (this SSOT)
                                    └─ IS catalogue rows for (protocol, chain)
```

Semantics (aligned with the honest-coverage v2 fail-CLOSED rule):

- `enumerated == expected == 0` ⟹ status `undefined` (never green — matches the empty-denominator guard).
- `enumerated == expected > 0` ⟹ status `complete` (100%; we saw every on-chain instrument).
- `enumerated < expected` ⟹ status `gap` (`missing_delta = expected − enumerated` — named, quantified).
- `enumerated > expected` ⟹ status `over_enumerated` (stray; catalogue holds ghosts — investigate).
- probe throws / subgraph indexing-behind / RPC down ⟹ status `probe_failed` → `undefined` (fail-CLOSED, never 100%).

A DeFi `(protocol, chain)` is **NOT** certified `denominator_complete` until its Tier-B probe returns `complete`.
"Complete from our own capture" is never enough (§7.4 of the foundation plan).

---

## 2. Data contract — `CompletenessProbe`

The oracle returns one `CompletenessProbe` per `(protocol, chain, as_of_date)`. Lives in UAC under
`unified_api_contracts/canonical/crosscutting/honest_coverage.py` alongside `EmptyConfirmedReason`.

```python
class CompletenessProbeStatus(StrEnum):
    COMPLETE = "complete"
    GAP = "gap"
    OVER_ENUMERATED = "over_enumerated"
    UNDEFINED = "undefined"
    PROBE_FAILED = "probe_failed"


class CompletenessProbeKind(StrEnum):
    # Tier-A: fast, indexed — trust unless subgraph drift detected.
    DEX_FACTORY_SUBGRAPH_TIER_A = "dex_factory_subgraph_tierA"
    LENDING_REGISTRY_SUBGRAPH_TIER_A = "lending_registry_subgraph_tierA"
    PERPS_MARKETS_API_TIER_A = "perps_markets_api_tierA"
    YIELD_REGISTRY_TIER_A = "yield_registry_tierA"
    # Tier-B: on-chain truth — replaces Tier-A per protocol as the RPC adapter lands.
    DEX_FACTORY_RPC_TIER_B = "dex_factory_rpc_tierB"
    LENDING_REGISTRY_RPC_TIER_B = "lending_registry_rpc_tierB"
    PERPS_MARKETS_RPC_TIER_B = "perps_markets_rpc_tierB"


@dataclass(frozen=True, slots=True)
class CompletenessProbe:
    protocol: str                    # UAC PROTOCOL_CAPABILITIES key, e.g. "uniswap_v3"
    chain: str                       # UAC chain name (upper), e.g. "ETHEREUM"
    as_of_date: date                 # UTC date the probe was pinned to
    probe_block: int                 # block number at which the on-chain count was read
    probe_ts_utc: datetime           # UTC probe execution timestamp
    probe_kind: CompletenessProbeKind
    probe_source: str                # subgraph_id / RPC endpoint URL / registry contract addr
    expected_count: int              # on-chain truth (this oracle's output)
    enumerated_count: int            # IS-catalogue count for (protocol, chain) at as_of_date
    missing_delta: int               # max(expected_count − enumerated_count, 0)
    stray_delta: int                 # max(enumerated_count − expected_count, 0)
    completeness_pct: float | None   # None when expected_count == 0 (UNDEFINED)
    status: CompletenessProbeStatus
    error_reason: str | None         # populated iff status == PROBE_FAILED
    creation_blocks: Mapping[str, int] | None  # optional: address → creation block (see §5)
```

The record is _immutable_ — a probe is a snapshot at `probe_block`. Downstream consumers keep the whole record; they do
not read a bare `completeness_pct` divorced from `probe_block` and `probe_source`.

---

## 3. Probe implementations — one per `protocol_class`

The oracle dispatches on `PROTOCOL_CAPABILITIES[protocol].protocol_class`. Every protocol currently in UAC (`aave_v3` /
`compound_v3` / `morpho` / `spark` / `fluid` / `venus` / `benqi` / `radiant` / `euler_v2` / `uniswap_v2` / `_v3` / `_v4`
/ `balancer` / `curve` / `sushiswap` / `pancakeswap_v3` / `aerodrome_v3` / `velodrome_v2` / `camelot_v3` /
`trader_joe_v2` / …) maps to exactly one Tier-A + one Tier-B probe. (`gmx` dropped from this list — GMX REMOVED
2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`.)

### 3.1 DEX (`protocol_class == DEX`)

**Tier-A — subgraph `factory{poolCount}`.** All UniV3/UniV2/Messari-schema subgraphs expose a `factory` (or `factories`)
entity with a `poolCount` scalar that increments on every `PoolCreated` event. Query:

```graphql
{
  factory(id: "<factory_address>") {
    poolCount
  }
}
```

Fallback for Messari schema (`liquidityPoolCount`): `{ dexAmmProtocol(id: "…") { totalPoolCount } }`.

**Tier-B — RPC `eth_getLogs(PoolCreated)`.** Read the factory contract's event log range `[deploy_block, latest − 30]`
in chunked windows (10 000 blocks per RPC call) and count `PoolCreated` topics. The factory address per (protocol,
chain) is added to `_defi.py` as a new field `PROTOCOL_CAPABILITIES[…].factory_address_by_chain: dict[str, str]` — one
canonical address per chain.

Cost note: Tier-B is amortised — the counts up to `deploy_block + N chunks` are cached in GCS
`gs://<oracle-cache-bucket>/defi_completeness/<protocol>-<chain>/<from_block>-<to_block>.json`; only the tip window is
re-scanned daily.

### 3.2 LENDING (`protocol_class == LENDING`)

Per-protocol registry — the count of **reserves** (Aave family), **markets** (Compound family), or **vaults/markets**
(Morpho family / Euler V2 family).

| Protocol      | Tier-A source                                          | Tier-B RPC call                                     |
| ------------- | ------------------------------------------------------ | --------------------------------------------------- |
| `aave_v3`     | Subgraph `{ reserves(first: 1000) { id } }` count      | `PoolAddressesProvider.getPool().getReservesList()` |
| `spark`       | Same as aave_v3 (Aave V3 fork)                         | Same as aave_v3 (Spark forks the Aave contracts)    |
| `compound_v3` | Subgraph `{ markets(first: 1000) { id } }` count       | `Comptroller.getAllMarkets()`                       |
| `morpho`      | blue-api `GET /markets?chainId=<id>` — `total` field   | `Morpho.marketsCount()` view                        |
| `fluid`       | Subgraph `{ pools(first: 1000) { id } }` count         | `FluidVaultResolver.getAllVaults()`                 |
| `venus`       | Subgraph `{ markets(first: 1000) { id } }` count       | `Unitroller.getAllMarkets()`                        |
| `benqi`       | Subgraph `{ markets(first: 1000) { id } }` count       | `BenqiComptroller.getAllMarkets()`                  |
| `radiant`     | Messari-schema `{ markets(first: 1000) { id } }` count | `LendingPool.getReservesList()`                     |
| `euler_v2`    | Goldsky `{ eulerVaults(first: 1000) { id } }` count    | `PerspectiveRegistry.perspectives()` per-chain      |

Both tiers key on **underlying-asset address** (or vault-address for morpho/euler) — the same key IS catalogue's lending
row uses in its canonical instrument_id. So `enumerated_count` for `(aave_v3, ETHEREUM)` at a given date equals the
count of catalogue rows with `venue=AAVE_V3 chain=ETHEREUM instrument_type=lending` and
`available_from <= as_of_date <= (available_to or ∞)`.

### 3.3 PERPS (`protocol_class == PERPS`)

Perp DEXes typically expose their universe as an authoritative REST endpoint that IS the on-chain state projection.

| Protocol      | Tier-A source                                                | Tier-B RPC call                              |
| ------------- | ------------------------------------------------------------ | -------------------------------------------- |
| `hyperliquid` | REST `POST /info { type: "meta" }` — `universe` array length | Same (this IS the on-chain projection)       |
| `drift`       | Solana program account scan (`Market` accounts)              | Same (RPC is Tier-A; Solana has no subgraph) |
| `jupiter`     | REST `GET /perps-markets` — length                           | Program-account scan (aggregator)            |

> `flash_trade`/`mango`/`zeta` rows removed 2026-07-15 (operator ruling — venues deleted; dead API endpoints, ~$0 TVL,
> zero MTDS capture ever wired). See `/codex/04-architecture/solana-defi-coverage.md`. `gmx` row removed 2026-07-25 —
> GMX venue support removed platform-wide (its captured `perp_funding` history was a synthetic OI-imbalance proxy, not
> real funding-rate data). See `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`.

### 3.4 YIELD / STAKING / RESTAKING (`protocol_class ∈ {YIELD, STAKING, RESTAKING}`)

Registry-driven. Each protocol has a small, well-known set of instruments (e.g. Ethena `sUSDe` + `ENA`, Lido `stETH` +
`wstETH`, EtherFi `weETH`). The Tier-A source is a curated per-protocol constant living beside the adapter (already
implied by the existing `required_tokens` field on `_ProtocolCapability`); Tier-B is
`PROTOCOL_CAPABILITIES[protocol].required_tokens` — the count of that frozenset. When the two disagree, treat Tier-B as
authoritative and the delta as a UAC drift finding.

### 3.5 INFRASTRUCTURE (`protocol_class == INFRASTRUCTURE`)

`gas_fees` / `token_transfers` / `mev_events` are chain-level, not per-protocol. Their "instrument set" is one row per
`(chain, data_type)`. The oracle reports `expected_count = 1` per chain in the UAC `DEFAULT_GAS_FEE_CHAINS` set;
`enumerated_count = 1` iff the IS catalogue synthesises the ALCHEMY-venue row for that chain. No factory/registry to
query.

---

## 4. Where the oracle plugs in

```
                    Layer-1 denominator (honest-coverage v2)
                    ─────────────────────────────────────────
   cefi │ tradfi │ sports │ prediction:      DeFi:
                                             ┌─────────────────────────┐
   EXPECTED = IS_catalogue × UAC_matrix      │ EXPECTED = ∑ probes     │
                                             │  probe(p,c).expected... │
                                             └──────────┬──────────────┘
                                                        │
                                                        ▼
                                             CompletenessProbe records
                                                        │
                                                        ▼
                                             layer_1.by_asset_group.defi.
                                             by_venue.<PROTOCOL>-<CHAIN>
                                             { completeness_pct, missing_delta,
                                               probe_kind, probe_block, ... }
```

**File contract:** the oracle lives at `instruments-service/instruments_service/oracle/defi_completeness_probe.py`
(per-protocol_class implementations, each ~50-100 LOC) + `oracle/probe_registry.py` (dispatch table by
`protocol_class` + `_defi.py` `SUBGRAPH_IDS` lookup). Consumers:

1. `instruments-service/scripts/measure_honest_coverage.py` — Phase-1 Layer-1 build, per `(protocol, chain)` in
   `PROTOCOL_CAPABILITIES`. For `asset_group=defi`, `EXPECTED_tuples` is derived from probe results, NOT from IS × UAC.
   For every other AG the existing v2 code path is unchanged.
2. `instruments-service/scripts/build_instrument_catalogue.py` — on catalogue regen, the oracle output populates
   `available_from = block_timestamp(creation_block)` for each observed DEX pool (see §5). This is the **genesis
   oracle** side-effect.
3. `deployment-ui HonestCoverageCard.tsx` — additive fields under `layer_1.by_asset_group.defi.by_venue[…]` (unchanged
   consumer contract: existing keys byte-preserved; new optional fields added per honest-coverage v2
   `schema_version: 2`).

The oracle IS the DeFi Layer-1 denominator source. Once wired, `denominator_complete` for defi becomes
`all(probe.status == COMPLETE for probe in probes)` — an empty probe set falls back to `UNDEFINED` (fail-CLOSED).

---

## 5. `available_from` = per-pool on-chain creation block (genesis oracle)

Every `CompletenessProbe` for a DEX or lending protocol optionally carries `creation_blocks: Mapping[str, int]` mapping
each on-chain address to the block that emitted its `PoolCreated` / reserve-init event. The catalogue producer reads
this dict and stamps `available_from = chain_block_ts_utc(creation_block)` on the corresponding instrument row.

This kills three defects the current genesis rule leaves in place:

1. **RAYDIUM `available_from = 1970-01-01`** — Solana pools land without a creation timestamp because subgraph
   introspection returns `null`. The oracle-observed pool-creation slot IS the truth.
2. **Backfill window drift** — MTDS backfills default to `2020-05-01` for DeFi ("close enough to Uniswap V2"),
   over-fetching pre-genesis days that write `expected_unattempted` cells forever. A pool created 2023-07-14 has its EU
   seeds start 2023-07-14, not 2020-05-01.
3. **Circular "first-seen" `available_from`** — the current fallback derives `available_from` from the first day the
   pool appears in our own manifest; a two-year backfill window then never fills the pool's real early history because
   the "first-seen" was two days ago. Creation-block truth breaks the loop.

Rules for the writer:

- If `creation_blocks` is present and contains the instrument's address: `available_from = ts_utc(block)`.
- Else if the existing catalogue rule yields a bounded date: keep it.
- Else `available_from = None` and the row IS a Layer-1 finding — the oracle KNOWS the pool exists (it counted it in
  `expected_count`) but we can't stamp a genesis; log as `oracle_genesis_missing` for follow-up.

---

## 6. Tier-A → Tier-B rollout

**Tier-A first, everywhere.** Subgraphs already reachable from IS DeFi adapters — SUBGRAPH_IDS in UAC `_defi.py` — cover
~24 protocols out of the ~40 in `PROTOCOL_CAPABILITIES`. Ship Tier-A probes for those first; they run per-day in a
single Cloud Run job (~5 s / probe × ~120 probes ≈ 10 min).

**Tier-B when Tier-A drifts.** Two triggers move a probe from Tier-A to Tier-B:

1. **Subgraph indexing-behind detected** — probe reads `_meta.block.timestamp` ; if it lags real time by
   > 15 min the probe emits `probe_failed` and the Tier-B RPC path takes over that day.
2. **Persistent Tier-A vs Tier-B divergence** — a companion audit runs Tier-A + Tier-B in parallel weekly. If they
   disagree > 1 % or > 5 rows for three consecutive weeks, Tier-A is DEPRECATED for that protocol/chain and Tier-B
   becomes the default probe.

A protocol is CERTIFIED complete when the Tier-B probe returns `COMPLETE`. Tier-A is a rollout accelerator, NOT the
certification bar.

---

## 7. Fail-CLOSED behaviour (no silent 100%)

The oracle inherits every "no silent green" rule from `honest-coverage-model.md`:

- **Empty on-chain count** (`expected_count == 0`): status `UNDEFINED`, `completeness_pct = None`, LOUD-log
  (`oracle_expected_zero`). NEVER 100%.
- **Probe throws / times out**: status `PROBE_FAILED`, `completeness_pct = None`, `error_reason` carries the underlying
  exception class. NEVER 100%.
- **Tier-A vs Tier-B disagreement** on a paired weekly audit: status `OVER_ENUMERATED` or `GAP` with
  `error_reason = "tier_probe_divergence"`. The system NEVER silently averages the two. The lower count is reported
  (fail-CLOSED — assume we're missing more, not less).
- **Reorg safety**: EVM probes read `latest − 30 blocks`; Solana probes read `latest − ~60 slots` (~30 s finality).
  Never `latest` — a reorg would poison `probe_block` and the cached count.

---

## 8. Credentials / cost

- Tier-A: **no new credentials.** The Graph API key already lives in `THE_GRAPH_API_KEY` (used by every existing DeFi
  adapter). Morpho blue-api is public. Hyperliquid REST is public.
- Tier-B: **no new credentials for the top 7 EVM chains** — Ethereum / Arbitrum / Optimism / Base / Polygon / BSC /
  Avalanche RPC URLs exist in `CHAIN_RPC_TEMPLATES` + Alchemy fallbacks. Solana RPC in `SOLANA_RPC_TEMPLATES` (Jito,
  Helius). Hyperliquid HTTP in `HYPERLIQUID_RPC_TEMPLATES`.
- **BLOCKED-CREDENTIALS scaffold rule (per `external-data-always-available-rule.md`):** for any chain present in
  `PROTOCOL_CAPABILITIES` but absent from the RPC templates (currently: `LINEA`, `MANTLE`, `SCROLL`, `ZKSYNC` for some
  protocols), ship the adapter scaffold anyway with status `BLOCKED-CREDENTIALS` and open a credential ask — DO NOT
  descope.
- Cost: ~120 Tier-A + ~120 Tier-B probes/day. Tier-A subgraph reads are free (already-subscribed API key). Tier-B RPC is
  `~ 3 × eth_getLogs` per protocol/chain per day (start-of-day, tip-window scan) — ~$0 on Alchemy free tier for all EVM
  chains combined. Single-walk discipline: **one probe per (protocol, chain) per day, not per pool** (per-pool
  creation-block enrichment happens ONCE at pool birth, then cached).

---

## 9. Rollout — plan todos to file after this design

The design lands as a codex SSOT (this doc). Implementation is broken into these plan-item deltas — file them under
`defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` or a fresh `defi_completeness_oracle_impl_<date>.md` plan
(data_engineering role, ~2 calibrated AI-days total):

- P0 [SCHEMA]: land `CompletenessProbe` + `CompletenessProbeStatus` + `CompletenessProbeKind` in UAC
  `canonical/crosscutting/honest_coverage.py`; unit tests exercise the semantic table in §1.
- P0 [SCHEMA]: add `factory_address_by_chain: Mapping[str, str]` (default empty dict) to UAC `_ProtocolCapability`;
  populate for the top-10 DEX protocols (uniswap_v2/v3/v4, sushiswap_v3, balancer, curve, pancakeswap_v3, aerodrome_v3,
  velodrome_v2, camelot_v3).
- P1 [CODE]: `instruments-service/instruments_service/oracle/probe_registry.py` — dispatch table (empty probes at
  first). Wire the module import into `measure_honest_coverage.py` behind an `--use-defi-oracle` flag (default OFF).
- P1 [CODE]: Tier-A DEX probe (uniswap_v3, aave_v3, curve) as reference implementations — ~150 LOC each, reusing
  existing adapter's subgraph client. (`gmx` dropped from this list — GMX REMOVED 2026-07-25, see
  `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`.)
- P2 [CODE]: Tier-A probes for the remaining ~20 protocols (10 DEX / 6 lending / 4 perps / 3 yield).
- P2 [CODE]: Tier-B RPC probe for uniswap_v3 + aave_v3 on ETHEREUM (proves the RPC path end-to-end).
- P2 [CODE]: `--use-defi-oracle` becomes DEFAULT ON in `measure_honest_coverage.py`; the DeFi Layer-1 number is now
  oracle-driven; the CK3-certified 94.81% is superseded by a real chain-truth number.
- P2 [DATA]: emit `available_from = ts_utc(creation_block)` for every DEX pool in the next catalogue regen (kills the
  RAYDIUM `1970-01-01` defect + tightens the EU-seed window).
- P3 [SCRIPT]: Tier-A ↔ Tier-B weekly reconciliation audit; alert on `tier_probe_divergence` > 1 % or > 5 rows.

Each todo is scoped for one data_engineering worker (Sonnet, ~0.5-0.8 calibrated AI-day). None of them touch UI,
execution, or strategy — pure IS + UAC. The oracle sits on the IS Layer-1 boundary and never talks to MTDS or downstream
services directly; consumers read the honest-coverage v2 `coverage.json`.

---

## 10. Non-goals (what the oracle IS NOT)

- **Not a MTDS-side check.** MTDS captures market data; the oracle is a Layer-1 instrument-denominator check. A
  protocol/chain being 100% complete in the oracle says NOTHING about how many pool-day cells were captured; that's
  Layer-2 (honest-coverage v2's `captured / (captured + attempted_failed + expected_unattempted)`).
- **Not a per-day time-series.** The oracle answers "is the enumerated set complete at this date"; it is not a
  historical enumeration engine. `available_from` populated per-pool from creation blocks + the `_enumerate_v2_defi`
  date-axis walk handle the historical Layer-1 view (§2.1 of the foundation plan's Tier-A vs Tier-B distinction).
- **Not a live monitoring alert.** Alerts on the `#data-pipeline-alerts` channel fire from `deployment-service` reading
  the daily coverage.json; the oracle does not push its own alerts. A Layer-1 gap from a probe surfaces as a
  `layer_1.by_asset_group.defi.by_venue[…].completeness_pct < 100` cell — the same path a cefi gap surfaces on.
- **Not a MTDS backfill trigger.** The oracle reports gaps; the backfill decision is a separate operator/plan call. Zero
  automation from oracle-gap → backfill-VM — that's the fire-and-forget class we banned.

---

## 11. Relationship to other SSOTs (do NOT duplicate)

- **`honest-coverage-model.md`** — this doc extends its Layer-1 model with an external denominator source for DeFi.
  `honest-coverage-model.md` remains the SSOT for the two-layer / two-view / coverage.json v2 schema; this doc is the
  SSOT for the DeFi-specific denominator override.
- **`availability-manifest-and-data-status.md`** — the manifest is the write ledger (Layer-2). This oracle never writes
  to the manifest; it only informs Layer-1's `EXPECTED` set for DeFi.
- **`defi-canonical-naming-ssot.md`** — the oracle emits venue + chain in the canonical form the SSOT defines
  (`PROTOCOL` + `CHAIN`, glued for on-chain-CeFi-perp venues per that SSOT's rules). The oracle does NOT introduce a new
  venue grain.
- **`defi-venue-protocol-catalogue.md`** — the enumeration of which protocols the oracle covers is exactly the set
  defined there. Adding a protocol to `PROTOCOL_CAPABILITIES` implicitly adds it to the oracle's probe set.
- **`external-data-always-available-rule.md`** — a chain with no RPC template ships a scaffold + status
  `BLOCKED-CREDENTIALS`, never a descope (§8).

---

## 12. Certification bar

DeFi Layer-1 is CERTIFIED complete when, for every `(protocol, chain)` in `PROTOCOL_CAPABILITIES`:

1. A Tier-B probe runs successfully on the daily Cloud Run job (`probe_kind` ends in `_tierB`,
   `status != PROBE_FAILED`).
2. `completeness_pct == 100.0` (never `>= 100.0` — `>` is an over-enumeration).
3. `probe_block` is within `latest − 60 min` (probe freshness).

CK3 for defi Layer-1 lifts from the honest-coverage-model.md's current caveat ("94.81% measured against the CATALOGUE's
declared pool set") to "100% measured against on-chain factory / registry truth, per §12." That graduation is a
follow-on plan item — this doc is the design SSOT for the path to it.
