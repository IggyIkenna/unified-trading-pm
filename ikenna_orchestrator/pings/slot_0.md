
## 2026-06-21 — OPERATOR ASK: confirm live Polymarket perp beta endpoint (BLOCKED-UPSTREAM)
Plan: plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md (perp enumerator line 30 / Polymarket sub-item).
The Phase-0-documented `https://perps-api.polymarket.com/` does NOT resolve (DNS NXDOMAIN, verified 2026-06-21); perp paths under the resolving Polymarket hosts 404. `PolymarketPerpReferenceDataAdapter` scaffold + mocked unit tests are shipped (instruments-service@fdc9bad) but cannot run against a live endpoint. **Need**: the current live Polymarket perp REST base + `/markets` schema (or confirm perps moved/renamed). Kalshi-perp half is fully live. Unblocks: Polymarket-perp enumeration + the MTDS Polymarket-perp trades/funding adapter (line 34).
