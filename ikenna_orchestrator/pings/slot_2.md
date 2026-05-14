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
