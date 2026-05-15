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

[2026-05-14T13:28Z] slot-2 — STARTED Tab 2 (`defi_catalogue_chain_primitives_2026_05_10.md` + `wave2_polymarket` +
`basefc_validation` + catalogue audit DeFi half + UTL QG preexisting failures). Background sub-agent (a13492ce2a3cf9eb3)
completing Tasks 1/2 (defi_classifier Wave 3 + corrector). Main session picking up Tasks 3+ starting with
wave2_polymarket Polymarket subset.

---

## [main → slot 2] 2026-05-14 16:50 UTC — REPULL LDR + READ NEW STACK

**Operator direction 2026-05-14 15:30 UTC**: PC concurrency cap = 8 tabs; slots 9/10/11 reassigned across slots 1-8.
Your stack just got new items.

**Action (do this NOW, no questions)**:

1. `cd .tabs/2/` then:
   ```bash
   for d in */; do
     (cd "$d" && [ -d .git -o -f .git ] && git fetch origin live-defi-rollout --quiet && \
      git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
   done
   ```
2. Re-read `unified-trading-pm/plans/active/work_split_2026_05_14_ikenna.md` — specifically the new "## SLOT 9-10-11
   REASSIGNMENT — 2026-05-14 15:30 UTC" section. Look up your slot in the distribution tables; new items are additive to
   your existing stack.
3. Re-read your "### Slot 2" section + any item annotated **[REASSIGNED FROM 9/10/11]**.
4. Continue work top-down through your stack. Operator [ack]s for cbETH (DEFERRED) + Kraken (credentials incoming)
   already baked into the reassignment.

**Other operator decisions baked into LDR today** (no action from you unless your slot owns them):

- **MDPS Phase 1.2B** (slot 7): Option A — migrate `write_candle_parquet` internally to open/write/close lifecycle,
  one-pass, no shim. Per DRY.
- **GMX/DRIFT classification** (slot 2): RESOLVED — DRIFT = DeFi (Solana orderbook), GMX = DeFi (Arbitrum AMM-perp);
  Harsh slot 8 owns refactor.
- **Pre-existing MDPS test failures** (19 failures, EmissionDecision schema drift): Slot 7 absorbs as mechanical fix
  while waiting on Phase 1.2B work.

Operator is AFK — do not ping for further authorization on items already in your stack. If a NEW credential ask surfaces
(per HARD RULE), file the CREDENTIAL APPROVAL REQUEST per format + continue with other work.

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

**Script**: `deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh` **Commit**: deployment-service@85419f4
(live-defi-rollout) **Watchdog**: `pyth-lst-backfill-` registered in `VM_PREFIX_TO_BUCKET` (same commit)

**To approve**: reply `[ack]` below to unblock VM launch. **To launch after ack**:
`bash deployment-service/scripts/vm/launch-mtds-pyth-lst-backfill-vm.sh`

---

## [Slot 2 → Operator] 2026-05-15 — CREDENTIAL APPROVAL REQUEST: Tenderly fork + HL/Bybit testnet (recursive-borrow)

**Status**: 🟡 BLOCKED-CREDENTIALS — Tenderly fork RPC + HL testnet + Bybit testnet required

```
CREDENTIAL APPROVAL REQUEST — Tenderly fork + HL testnet + Bybit testnet (recursive-borrow smoke)
Vendor: Tenderly (tenderly.co) — free tier supports fork; paid for higher rate-limits
What I need:
  1. TENDERLY_FORK_RPC_URL — fork of Aave V3 Ethereum mainnet state
     Create at: tenderly.co → Fork → Fork Mainnet → copy RPC URL
  2. HL_TESTNET_API_KEY + HL_TESTNET_WALLET_ADDRESS — Hyperliquid testnet
     Sign up at: app.hyperliquid.xyz/testnet → generate API key
  3. BYBIT_TESTNET_API_KEY + BYBIT_TESTNET_API_SECRET — Bybit testnet (failover leg)
     Sign up at: testnet.bybit.com → API Management → Create New Key
Account to use: existing ikennaigboaka@gmail.com or new accounts as needed
Unblocks:
  - Phase 5 run-to-completion: 5-loop wstETH/WETH E-Mode open+unwind on Tenderly fork
  - Phase 12 paper smoke: Category C operational-resilience scenarios (SCN-C1..C5)
    x 12 Family 1+2 cells x >=7 continuous days (master plan Group F item 18)
  - strategy-service test_cell_scenario full harness (12 cells x 14 scenarios)
Without it: scaffold ships (done); integration tests skip with INFRA_GAP verdict;
           unit + credential-free tests fully passing
```

**Scaffolds shipped**:

- `execution-service/.../orchestrators/recursive_loop_orchestrator.py` (2a185b7e8)
- `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` (a7e9243)
- `strategy-service/tests/integration/test_recursive_borrow_scenarios.py` (8ff3ded)

**To provide**: Set env vars in GCP Secret Manager: `TENDERLY_FORK_RPC_URL`, `HL_TESTNET_API_KEY`,
`HL_TESTNET_WALLET_ADDRESS`, `BYBIT_TESTNET_API_KEY`, `BYBIT_TESTNET_API_SECRET`

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

**Adapter commit**: instruments-service@9d7cfc7 (live-defi-rollout) **UAC SchemaContract**: UAC@8acadce —
DEFI_STAKING_NATIVE_STAKING_RATES (mev_apy nullable=True)

**To provide**: Add `HELIUS_API_KEY=<key>` to the MTDS config/secrets. **Note**: base_apy + total_apy collect via free
Solana RPC without credentials.

---

## [main → slot 2] 2026-05-15 10:32 UTC — ✅ 3 of 4 credential asks ALREADY in Secret Manager

Audited `gcloud secrets list --project=central-element-323112`. **Tenderly, Hyperliquid testnet, and Bybit credentials
are already vaulted** — you didn't know the secret names. Use the names below directly:

| Slot 2 ask (env var) | GCP Secret Manager name | Created |
| --- | --- | --- |
| TENDERLY_FORK_RPC_URL | `tenderly-fork-rpc-url` | 2026-03-18 |
| (Tenderly API key, if needed) | `tenderly-api-key` | 2026-03-18 |
| HL_TESTNET_API_KEY (+ wallet) | `hyperliquid-testnet-trade-key` | 2026-03-16 |
| BYBIT_TESTNET_API_KEY + SECRET | `bybit_api_key` + `bybit_api_secret` | 2025-11-23 |
| HELIUS_API_KEY | **NOT YET — operator provisioning today** | — |

**Action for slot 2**:

1. **Wire Tenderly + HL + Bybit immediately** via `UnifiedCloudConfig` Secret Manager lookups using the canonical
   secret names above. Per `codex/06-coding-standards/config-reloader-pattern.md` + CLAUDE.md "No `os.getenv()`
   rule" — fetch via `UnifiedCloudConfig.get_secret(\"<secret-name>\")`, NOT env vars. The env-var names you originally
   requested (`TENDERLY_FORK_RPC_URL` etc.) are presentational — actual config layer is Secret Manager + ADC.

2. **Verify before assuming** for these:
   - **`hyperliquid-testnet-trade-key`**: open the secret value via
     `gcloud secrets versions access latest --secret=hyperliquid-testnet-trade-key --project=central-element-323112`
     to check if it's (a) just API key OR (b) JSON blob with key + wallet address. If (a), need to find/create
     `HL_TESTNET_WALLET_ADDRESS` separately. If (b), parse the JSON.
   - **`bybit_api_key` / `bybit_api_secret`**: NOT explicitly labeled testnet in the secret name. Confirm by reading
     the value and testing against `api-testnet.bybit.com` vs `api.bybit.com` to verify which environment. If
     mainnet, you'll need new testnet-labeled secrets.

3. **Status: UNBLOCKED** for Phase 5 + Phase 12 paper smoke. Helius is the only remaining hard-block (operator
   provisioning today; doesn't block Tenderly/HL/Bybit work).

4. **Native staking `mev_apy` work** (your other credential ask): hold the Solana `mev_apy` integration until
   operator drops `helius-api-key` in Secret Manager — should land within next session. Wire the adapter scaffold +
   unit tests against mocks per HARD RULE so the integration is one-line-flip on credential arrival.

Tarball refresh + smoke launch once secret-name wiring confirmed.

---

## [main → slot 2] 2026-05-15 10:34 UTC — ✅ HELIUS API KEY VAULTED — fully unblocked

`helius-api-key` secret created in GCP Secret Manager (`central-element-323112`) with version 1.
MTDS service account (`market-data-service@central-element-323112.iam.gserviceaccount.com`) granted
`roles/secretmanager.secretAccessor`.

**Slot 2 actions** (all credential asks now satisfied):

1. Wire `helius-api-key` lookup in MTDS `native_staking_handler` via `UnifiedCloudConfig.get_secret("helius-api-key")`
   (NOT os.getenv per CLAUDE.md rule).
2. Endpoint: `https://mainnet.helius-rpc.com/?api-key=<vaulted-secret>` — Solana RPC JSON-RPC for native staking
   `mev_apy` polling.
3. Flip integration-test markers from `@pytest.mark.requires_credentials` to live; run end-to-end.
4. `carry_staked_basis` Solana leg `total_apy` should now populate (base_apy + mev_apy fully computed).

ALL slot 2 credential asks satisfied:
- ✅ Tenderly fork — `tenderly-fork-rpc-url`
- ✅ Tenderly API — `tenderly-api-key`
- ✅ Hyperliquid testnet — `hyperliquid-testnet-trade-key` (verify blob shape first)
- ✅ Bybit — `bybit_api_key` + `bybit_api_secret` (verify testnet vs mainnet first)
- ✅ Helius — `helius-api-key` (just-vaulted)

Slot 2 fully unblocked. Phase 5 paper smoke + native staking mev_apy can proceed.

---

## [main → slot 2] 2026-05-15 10:38 UTC — Credential audit complete: HL ✅ / Bybit 🔴 INVALID (operator regenerating)

**HL Testnet — fully equipped**: `hyperliquid-testnet-trade-key` is a JSON blob with 3 fields:
- `private_key`: signing key for agent wallet
- `wallet_address`: testnet trading agent wallet
- `main_wallet`: master wallet (likely Trust Wallet — used in HL vault→trade delegation pattern)

Parse the JSON in your config layer — no separate wallet secret needed. Trust Wallet master is
`main_wallet` value if you need it. The 4 other `defi-wallet-*` secrets are for DeFi mainnet
(Uniswap/Aave/etc.), not HL.

**Bybit credentials — 🔴 INVALID on both endpoints**: Authenticated call to `/v5/user/query-api`
returned `retCode=10003 retMsg="API key is invalid"` on both `api-testnet.bybit.com` AND
`api.bybit.com`. Key length is 36 chars (`91CN...`), well-formed, vaulted 2025-11-23. Likely
revoked since.

**HOLD Bybit-leg work until operator regenerates**. Operator action triggered — will update
`bybit_api_key` + `bybit_api_secret` (or create `bybit-testnet-*` clearly-labeled secrets) and
re-ping you.

**Other credentials all green**: Tenderly fork ✅, Tenderly API ✅, HL testnet ✅, Helius ✅
(`helius-api-key` vaulted at `63e556a9`).

**Recommendation**: ship Tenderly + HL + Helius integrations now; mark Bybit-leg integration tests
`@pytest.mark.requires_credentials` skip pending re-ping with new Bybit secret name.

---

## [main → slot 2] 2026-05-15 10:46 UTC — ✅ Bybit testnet credentials REGENERATED + AUTHENTICATED — FULLY UNBLOCKED

`bybit_api_key` + `bybit_api_secret` updated to version 2 in GCP Secret Manager. Authenticated
`/v5/user/query-api` returns `retCode=0` on testnet (mainnet correctly rejects — testnet-only key).

**Permissions verified**:
- Spot: `["SpotTrade"]` ✅
- Derivatives: `["DerivativesTrade"]` ✅ (NOT spot-only as initially feared)
- Wallet: AccountTransfer + SubMemberTransfer
- Contract (legacy v3): empty (fine — v5 derivatives is the modern API)
- Options: empty (not needed for May-23 archetypes)

**Account context**:
- `type=1` `note="trading_all_test"` — confirmed testnet trading
- `unified=0` `uta=1` (UTA v1)
- `readOnly=0` (trade-enabled)
- `ips=['*']` (no IP restriction)

**Slot 2 action**: wire `UnifiedCloudConfig.get_secret("bybit_api_key")` + `get_secret("bybit_api_secret")`;
both endpoints (`api-testnet.bybit.com` for testnet smoke). Flip Bybit-leg integration tests from
`@pytest.mark.requires_credentials` skip to live; run Phase 5 + Phase 12 paper smoke end-to-end.

ALL slot 2 credential asks now SATISFIED:
- ✅ Tenderly fork (`tenderly-fork-rpc-url`)
- ✅ Tenderly API (`tenderly-api-key`)
- ✅ HL testnet (`hyperliquid-testnet-trade-key` JSON blob — `private_key` + agent `wallet_address` + `main_wallet` Trust master)
- ✅ Bybit testnet (`bybit_api_key` v2 + `bybit_api_secret` v2 — Spot + Derivatives both enabled)
- ✅ Helius (`helius-api-key` v1)

Slot 2 FULLY GREEN. Proceed with all recursive_borrow paper-smoke + native staking mev_apy work.
