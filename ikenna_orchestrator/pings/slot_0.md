
## 2026-06-21 — OPERATOR ASK: confirm live Polymarket perp beta endpoint (BLOCKED-UPSTREAM)
Plan: plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md (perp enumerator line 30 / Polymarket sub-item).
The Phase-0-documented `https://perps-api.polymarket.com/` does NOT resolve (DNS NXDOMAIN, verified 2026-06-21); perp paths under the resolving Polymarket hosts 404. `PolymarketPerpReferenceDataAdapter` scaffold + mocked unit tests are shipped (instruments-service@fdc9bad) but cannot run against a live endpoint. **Need**: the current live Polymarket perp REST base + `/markets` schema (or confirm perps moved/renamed). Kalshi-perp half is fully live. Unblocks: Polymarket-perp enumeration + the MTDS Polymarket-perp trades/funding adapter (line 34).

## 2026-06-22 — UPDATE: Polymarket-perp = NO PUBLIC API EXISTS (not a fixable hostname)
Investigated per operator (DNS region/auth?). Confirmed: `perps-api.polymarket.com` (+perps./perp.) NXDOMAIN on BOTH Google(8.8.8.8)+Cloudflare(1.1.1.1) — not region, not auth (DNS precedes both). Official docs (docs.polymarket.com + llms.txt) have ZERO perps mention. Polymarket perps are LIVE but WEB-UI BETA ONLY (restricted access) — no public REST/WS API shipped. **Operator action to unblock**: either (a) tell us when Polymarket publishes the public perps API, or (b) provision beta API access if available. Until then the scaffold stays (flows with zero code change on endpoint availability). Kalshi-perp is fully live (public API). NOTE: separately, Polymarket PREDICTION depth IS available now via public CLOB `/book` → being built as book_snapshot_5 (item 69).

---

## CREDENTIAL APPROVAL REQUEST — ICE market data (tradfi) — 2026-06-22

**Ref**: `plans/active/tradfi_multisource_backfill_2026_06_22.md` § `[BLOCKED-CREDENTIALS] P2`

**What it unblocks**: 530,600 ICE (IFEU/IFUS — Brent BRN, Gasoil G, US softs, ICE Dollar-Index DX)
`expected_unattempted` tradfi cells. The IS instrument catalogue for ICE already exists (2,067
BRN/G FUTURE+COMBO rows); ONLY the market-data SOURCE is missing.

**Why blocked**: ICE has **no source in our current universe** (verified 2026-06-22):
- Databento DROPPED ICE (IFEU.IMPACT/IFUS.IMPACT) in the 3-dataset subscription lockdown
  (operator 2026-06-18 — we pay for only GLBX.MDP3 + DBEQ.BASIC + XCBF.PITCH).
- Massive's S3 `flatfiles` bucket has **NO ICE prefix** (probed: only `us_futures_{cme,cbot,comex,nymex}`
  + equities + `global_forex`). Massive cannot serve ICE.

**Vendor/tier needed (operator pick)**: either (a) add the Databento ICE datasets (IFEU.IMPACT /
IFUS.IMPACT) back to the paid subscription + the `databento_subscription_allowlist`, or (b) another
ICE-data feed. Until acked, ICE stays `expected_unattempted` (NOT a wave-launcher dispatch — the
wave-launcher correctly excludes ICE).
