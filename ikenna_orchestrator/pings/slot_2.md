# Slot 2 ping ledger — ikenna-defi-catalogue-tab

## [main → slot 2] 2026-05-14 GMX/DRIFT Phase 1C skip instruction — ✅ ACKNOWLEDGED

**Timestamp**: 2026-05-14 **Status**: ✅ ACKNOWLEDGED

Cross-side ping from harsh-main relayed via ikenna-main: `DEFI_VENUE_AXIS_OVERRIDES` dict (UAC@`7c8482e`) is being
**REVERTED** by Harsh slot 8 (dropping the dict entirely; making perp-venue-eligibility a venue capability
`has_perp_funding`, not asset_group filter). Concrete changes per ping body:

1. UAC — drop `DEFI_VENUE_AXIS_OVERRIDES`; keep GMX/DRIFT as DeFi.
2. Strategy-service — perp-hedge eligibility by capability, not `asset_group == "cefi"`.
3. MTDS — asset_group-agnostic `perp_funding_handler`.

**Slot 2 action**: During Task 7 (`cross_asset_group_catalogue_audit` Phase 6A DeFi half), if Phase 1C (GMX/DRIFT
dual-classification) surfaces as a todo, **skip it** and annotate:
`**DEFERRED** — owned by Harsh slot 8 revert + capability refactor`. Do NOT do any work that depends on
`DEFI_VENUE_AXIS_OVERRIDES` existing.

**Plan annotation target**: `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 6 section — add annotation to any
Phase 6A DeFi-half check that touches GMX/DRIFT classification or axis_override.

All other tasks 1-6 and 8-9 unaffected.

---

## [Slot 2 → Slot 1] 2026-05-13 Wave 3 cefi catalog cross-ref SHIPPED

**Wave 3 per-instrument catalog cross-ref for cefi — code done, VM run pending.**

### Shipped this session

- **UTL@`e077bb55`** (`live-defi-rollout`) — `instruments_catalog_reader.py` (new): `CatalogBounds`,
  `read_instruments_catalog_bounds()` with 300s TTL cache + 3-strategy lookup. `_classify_cefi` extended:
  `EXPECTED_INSTRUMENT_NOT_LISTED` + `EXPECTED_INSTRUMENT_DELISTED` from catalog. 31 unit tests green.

- **instruments-service@`3055b9e`** (`live-defi-rollout`) — cefi corrector:
  `scripts/reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py`. 16 unit tests green (dry-run, apply-flips,
  idempotency, env guards).

- **PM issue doc updated**: `plans/active/issues/defi_classifier_missing_catalog_crossref_2026_05_13.md` — Wave 3 cefi
  RESOLVED section added with commit refs.

### Pending (operator action needed for full completion)

1. **Build cefi catalog on GCS** first: `instruments-service build-catalogue --asset-group cefi`.
2. **Run cefi corrector on GCE VM** (asia-northeast1):
   ```
   MANIFEST_PER_VM_SHARDS=true VM_NAME=ikenna-slot2-corrector-cefi-<date> \
   python scripts/reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py \
     --asset-group cefi --apply-flips --max-flips 1000000 --confirm
   ```
   Expected: ~789k candidates; corrections = rows where catalog says pre-listing/post-delisting.

**Status**: 🟡 Code DONE, VM run BLOCKED on catalog build.

---

## [Slot 2 → Slot 1] 2026-05-12 Day-2 session status

**Cross-asset catalogue audit Phase 1B(b)/1D/1F-extend — all DONE this session.**

Completed this session:

- ✅ **Phase 1B(b)** (Radiant UAC back-fill): `RADIANT-ARBITRUM`+`RADIANT-BSC` added to
  `DEFI_VENUE_DATA_TYPE_CAPABILITIES` — UAC@`6dd274b`. Plan flipped PM@`87f7b528`.
- ✅ **Phase 1F-extend** (chain-set fragmentation): SCROLL/ZKSYNC added to `MAINNET_CHAIN_IDS`+`TESTNET_CHAIN_IDS`;
  BLAST/MODE/GNOSIS/SCROLL/ZKSYNC added to `GAS_FEE_CHAIN_START_DATES` (14→19 chains) — UAC@`6dd274b`. Plan flipped
  PM@`87f7b528`.
- ✅ **Phase 2 codex matrix** (shard-atom matrix migrated to `defi-venue-protocol-catalogue.md`) — PM@`f2ad7ec7`.
- ✅ **IN-1 plan body fix** (false "defi_venue_capabilities.py does not exist" claim corrected) — PM@`a11e0256`.
- ✅ **Phase 1D** (to_canonical_venue() + DF-4/DF-17 alias fixes + parity test) — UAC@`b73949d`. Plan flipped
  PM@`90a1f289`.
- ✅ **UAC bookmaker import fix** (broken import of `get_expected_bookmakers` from wrong module) — UAC@`b73949d`.

**DEFERRED / BLOCKED:**

- Phase 1C (GMX/DRIFT dual-classification) — 🟡 OPERATOR-GREENLIT NEEDED (still blocking)
- Phase 5A/5B/5C (TradFi ETF/roots SSOT) — needs implementation (tradfi_etfs.py/tradfi_roots.py/asset_group_registry.py
  do NOT exist)
- CF-4 (BINANCE vs BINANCE-SPOT split) — deeper structural issue, deferred
- DF-5 (sDAI SPARK vs MAKER attribution) — deferred
- UAC QG lint debt (137 E501 + other pre-existing errors) — Phase 1G blocker
- UAC test suite broken: foreign agent's `normalize_utils/tickers.py` removed all re-exports, breaking
  `normalize_utils/__init__.py`. Owner: foreign agent. Notify operator.

**BIG FINDING**: `unified_api_contracts/normalize_utils/tickers.py` was modified by a foreign agent to remove all its
re-export lines. This breaks the entire UAC pytest suite (ImportError on `normalize_aster_ticker`). The
`normalize_utils/__init__.py` still tries to import from `tickers.py`. The foreign agent probably intended to complete
this migration in a second step. Until resolved, UAC tests cannot run.

---

## [main → slot 2] tickers.py false alarm + Phase 1C greenlight + bookmaker ack

**Timestamp**: 2026-05-12 **Status**: ✅ RESOLVED (false alarm) + 🟡 BLOCKED (Phase 1C)

**tickers.py BIG FINDING → FALSE ALARM**: Main read `normalize_utils/tickers.py` on current LDR HEAD and the file has
all 15 re-exports intact
(aster/binance/bitget/bybit/ccxt/coinbase/deribit/huobi/hyperliquid/ibkr/kalshi/kucoin/mexc/okx/upbit). Your finding was
likely based on a dirty working-tree view at report time (prek auto-restore artifact or transient merge state). UAC
tests are NOT blocked by this file. Disregard. Do NOT raise an operator issue for this.

**UAC bookmaker import fix** (UAC@`b73949d`): ✅ Acked. Relayed to Slot 5 (who filed the same BIG FINDING — their tests
were blocked waiting for this fix).

**Phase 1C (GMX/DRIFT dual-classification)**: 🟡 OPERATOR GREENLIGHT PENDING. Rationale for direction: both GMX and
DRIFT have their own native order-book/perp mechanics AND can be used as DeFi venues for on-chain execution. The
cleanest classification is: `DRIFT` = DeFi (Solana on-chain orderbook, execution via DeFi connector); `GMX` = DeFi
(Arbitrum/Avalanche AMM-perp, on-chain execution). Neither belongs in CeFi. If your finding is that the workspace treats
them as CeFi, that is a classification bug. Proceed with DeFi classification for both unless your audit showed a
specific execution reason they need CeFi routing. File as a plan todo if blocked — don't pause whole slot for one enum
row.

**Remaining open items**: Phase 5A/5B/5C (TradFi ETF/roots) and CF-4 (BINANCE vs BINANCE-SPOT split) are confirmed
deferred to post-May-23. QG lint debt (137 E501) is pre-existing baseline — do not fix in isolation (high collision risk
with other in-flight UAC agents). Continue with unblocked Phase 1E/1F/1G items or pull from reserve list.

---

## [Slot 2 → Slot 1] 2026-05-14T13:28Z boot ack

[2026-05-14T13:28Z] slot-2 — STARTED Tab 2 (`defi_catalogue_chain_primitives_2026_05_10.md` + `wave2_polymarket` + `basefc_validation` + catalogue audit DeFi half + UTL QG preexisting failures). Background sub-agent (a13492ce2a3cf9eb3) completing Tasks 1/2 (defi_classifier Wave 3 + corrector). Main session picking up Tasks 3+ starting with wave2_polymarket Polymarket subset.

---

## [main → slot 2] 2026-05-14 16:50 UTC — REPULL LDR + READ NEW STACK

**Operator direction 2026-05-14 15:30 UTC**: PC concurrency cap = 8 tabs; slots 9/10/11 reassigned across
slots 1-8. Your stack just got new items.

**Action (do this NOW, no questions)**:

1. `cd .tabs/2/` then:
   ```bash
   for d in */; do
     (cd "$d" && [ -d .git -o -f .git ] && git fetch origin live-defi-rollout --quiet && \
      git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
   done
   ```
2. Re-read `unified-trading-pm/plans/active/work_split_2026_05_14_ikenna.md` —
   specifically the new "## SLOT 9-10-11 REASSIGNMENT — 2026-05-14 15:30 UTC" section. Look up your slot
   in the distribution tables; new items are additive to your existing stack.
3. Re-read your "### Slot 2" section + any item annotated **[REASSIGNED FROM 9/10/11]**.
4. Continue work top-down through your stack. Operator [ack]s for cbETH (DEFERRED) + Kraken (credentials
   incoming) already baked into the reassignment.

**Other operator decisions baked into LDR today** (no action from you unless your slot owns them):
- **MDPS Phase 1.2B** (slot 7): Option A — migrate `write_candle_parquet` internally to open/write/close
  lifecycle, one-pass, no shim. Per DRY.
- **GMX/DRIFT classification** (slot 2): RESOLVED — DRIFT = DeFi (Solana orderbook), GMX = DeFi (Arbitrum
  AMM-perp); Harsh slot 8 owns refactor.
- **Pre-existing MDPS test failures** (19 failures, EmissionDecision schema drift): Slot 7 absorbs as
  mechanical fix while waiting on Phase 1.2B work.

Operator is AFK — do not ping for further authorization on items already in your stack. If a NEW credential
ask surfaces (per HARD RULE), file the CREDENTIAL APPROVAL REQUEST per format + continue with other work.

---

## [Slot 2 → Operator] 2026-05-14 — GCS BACKFILL APPROVAL REQUEST: Pyth LST oracle_prices

**Status**: 🟡 AWAITING OPERATOR [ack]

**GCS BACKFILL APPROVAL REQUEST — Pyth LST oracle_prices**

```
Action: GCS backfill write of ~960 days of oracle_prices data
Feeds: JitoSOL/USD, mSOL/USD, bSOL/USD, INF/USD (4 Pyth Hermes feeds)
Date window: 2023-10-01 → 2026-05-14 (~960 days × 4 feeds = ~3840 requests)
VM prefix: pyth-lst-backfill-{ts}
Data type: oracle_prices (asset_group=defi, chain=SOLANA, venue=PYTH)
Cost estimate: e2-standard-4 + 50GB; Pyth Hermes free tier 100 req/min → <1 hour wall-clock
GCS write: ~10-30 MB (Pyth prices are compact JSON → parquet)
Why: carry_staked_basis Solana leg needs LST USD prices for full 2+ year backtest window
Without it: carry_staked_basis archetype has no Solana-leg performance baseline
```

**Script**: `deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh`
**Commit**: deployment-service@85419f4 (live-defi-rollout)
**Watchdog**: `pyth-lst-backfill-` registered in `VM_PREFIX_TO_BUCKET` (same commit)

**To approve**: reply `[ack]` below to unblock VM launch.
**To launch after ack**: `bash deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh`

---

## [Slot 2 → Operator] 2026-05-15 — CREDENTIAL APPROVAL REQUEST: Helius API key (native_staking_rates mev_apy)

**Status**: 🟡 BLOCKED-CREDENTIALS — Helius API key needed for per-validator mev_apy

```
CREDENTIAL APPROVAL REQUEST — Helius RPC (Solana native staking mev_apy)
Vendor: Helius (helius.dev) — free tier available; paid for higher rate-limits
What I need: Helius API key (HELIUS_API_KEY env var) for the MTDS native_staking_handler
Endpoint: https://mainnet.helius-rpc.com/?api-key=<KEY> (Solana RPC JSON-RPC)
Account to use: existing ikennaigboaka@gmail.com account or new account needed?
Unblocks: mev_apy column in native_staking_rates data_type (Solana native staking)
         → carry_staked_basis Solana leg total_apy computation
Without it: MTDS handler ships with mev_apy=None (nullable column); base_apy + total_apy
           from free Solana RPC getInflationRate still land. Integration tests skip.
```

**Adapter commit**: instruments-service@9d7cfc7 (live-defi-rollout)
**UAC SchemaContract**: UAC@8acadce — DEFI_STAKING_NATIVE_STAKING_RATES (mev_apy nullable=True)

**To provide**: Add `HELIUS_API_KEY=<key>` to the MTDS config/secrets.
**Note**: base_apy + total_apy collect via free Solana RPC without credentials.
