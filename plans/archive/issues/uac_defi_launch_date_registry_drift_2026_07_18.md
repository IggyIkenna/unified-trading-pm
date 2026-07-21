---
doc_type: issue
title:
  unified-api-contracts has TWO disagreeing DeFi protocol-launch-date registries (venue_launch_dates vs
  chain_env.PROTOCOL_LAUNCH_DATES)
summary:
  While fixing the instruments-service Solana available_from floor (P3, see plans progress log), found that
  unified_api_contracts.registry.venue_launch_dates.DEFI_VENUE_LAUNCH_DATES and
  unified_api_contracts.registry.chain_env.PROTOCOL_LAUNCH_DATES carry different launch dates for the same
  protocol-chain pairs — chain_env is subgraph-audited and more precise, venue_launch_dates is coarser and in one case
  (AAVE_V3-ETHEREUM) demonstrably reverts a documented correctness fix.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts]
scope: [engineer]
tags: [defi, ssot-contradiction, launch-dates, instruments-service]
related: []
created: 2026-07-18
parent_epic: defi_master
priority: P2
source: [instruments-service PIECE P3 — Solana DeFi available_from floor fix, 2026-07-18]
assigned_vm: NA
resolved_by:
  "unified-api-contracts@f849a238 (AAVE-ETH + 6 on-chain-verified corrections) + @a6933ef3 (≤4d tail fully reconciled,
  ETHEREUM re-verified, drift-guard allowlist emptied → 0 drift); see On-chain verification + Final resolution sections"
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-18
---

## What I found

Fixing `instruments-service` PIECE P3 (DeFi drilldown showing a generic pre-history floor for Solana protocols instead
of real launch dates) required threading
`unified_api_contracts.registry.venue_launch_dates.get_venue_launch_date("defi", venue)` into
`instruments_service/reference_data/adapters/defi/_solana_utils.py::get_protocol_floor_date`.

While doing so I found **two separate, disagreeing UAC registries for DeFi protocol/venue launch dates**, both live and
both consulted by instruments-service code:

1. `unified_api_contracts/registry/venue_launch_dates.py::DEFI_VENUE_LAUNCH_DATES` — keyed by `PROTOCOL-CHAIN` venue
   string (e.g. `KAMINO-SOLANA`). Its own docstring documents a **"prefer LATER when uncertain"** conservative
   principle, built for `EXPECTED_PRE_VENUE_LAUNCH` backward-fill classification + the data-status panel denominator.
2. `unified_api_contracts/registry/chain_env.py::PROTOCOL_LAUNCH_DATES` — keyed by `(CHAIN, PROTOCOL)` tuple. Consulted
   by `instruments-service`'s `reference_data/utils/evm_creation_resolver.py::get_protocol_floor_date` as the
   **primary** floor source for EVM DeFi `available_from`. Its docstring documents **subgraph-verified, day-precise**
   dates from a dedicated 2026-05-08 "Tab 14" audit, explicitly correcting several prior mis-aligned dates (see example
   below).

**These disagree on overlapping entries**, e.g.:

| Protocol-chain   | `venue_launch_dates` (DEFI_VENUE_LAUNCH_DATES) | `chain_env` (PROTOCOL_LAUNCH_DATES)                                                                                    |
| ---------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| AAVE_V3-ETHEREUM | 2022-03-16                                     | **2023-01-27** (subgraph-verified; 2022-03-16 was the debunked L2-cohort date — see chain_env.py's own inline comment) |
| KAMINO / Solana  | 2022-08-24                                     | 2022-08-23                                                                                                             |
| JITO / Solana    | 2022-08-16                                     | 2022-08-15                                                                                                             |

The AAVE_V3-ETHEREUM case is the concerning one: `chain_env.py`'s own comment says the 2022-03-16 date was proven wrong
by subgraph evidence (caused 11 months of legitimate 2022-03→2023-01 Aave V3 Ethereum data to be silently mis-classified
as `empty_confirmed[SOURCE_RETURNED_ZERO]`) and was fixed to 2023-01-27 on 2026-05-08 — but `venue_launch_dates.py`
still carries the debunked 2022-03-16 value. Any caller that (like I almost did) makes `venue_launch_dates`
unconditionally primary over `chain_env` for EVM protocols would silently **regress** that 2026-05-08 fix.

The Solana-only 1-day drifts (Kamino/Jito) are low-impact (both registries are close; neither is clearly right or wrong
without re-verifying against on-chain/subgraph truth) but are still an SSOT contradiction that should not exist.

## Why I did not fix it here

Reconciling two UAC-repo registries is a `unified-api-contracts` change, out of scope for the instruments-service-only
PIECE P3 fix (task explicitly scoped "instruments-service only"). I scoped my fix to
`_solana_utils.get_protocol_floor_date` only (which never previously consulted either UAC registry — pure local
hardcoded dict) and deliberately did **not** touch `evm_creation_resolver.get_protocol_floor_date`'s existing
`chain_env`-primary precedence, to avoid the AAVE_V3-ETHEREUM regression described above.

## Suggested resolution (not executed)

1. Audit which of the two registries should be the SSOT going forward — likely `chain_env. PROTOCOL_LAUNCH_DATES` for
   protocol-chain pairs it already covers (subgraph-audited, higher precision), with
   `venue_launch_dates.DEFI_VENUE_LAUNCH_DATES` deferring to it via a cross-reference or import, rather than maintaining
   a parallel hand-copied value.
2. Where `venue_launch_dates` covers a pair `chain_env` does not (this is the common case — `chain_env` only has ~15
   DeFi pairs, `venue_launch_dates` has ~50), keep `venue_launch_dates` as-is.
3. Re-audit the Solana entries in both registries against on-chain truth (mainnet-beta first transaction / program
   deployment slot) to settle the 1-day drifts.
4. Add a UAC-repo unit test asserting no `(protocol, chain)` pair exists in both registries with different values (or,
   if some divergence is intentional per-purpose, document why).

## Evidence

- `unified-api-contracts/unified_api_contracts/registry/venue_launch_dates.py` lines 148-246
  (`DEFI_VENUE_LAUNCH_DATES`).
- `unified-api-contracts/unified_api_contracts/registry/chain_env.py` lines 176-330+ (`PROTOCOL_LAUNCH_DATES`), see
  inline comment on `("ETHEREUM", "AAVE_V3")` documenting the 2026-05-08 subgraph-audit correction from 2022-03-14
  (pre-fix) via chain_env.
- `instruments-service/instruments_service/reference_data/utils/evm_creation_resolver.py` `get_protocol_floor_date`
  (consults `chain_env` only, not `venue_launch_dates`).
- Fixed in this session: `instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py`
  `get_protocol_floor_date` (now consults `venue_launch_dates` — the only one of the two Solana adapters previously had
  access to; `chain_env`'s Solana entries were never wired to any instruments-service caller either, a second small gap
  worth noting for the audit above).

## Progress 2026-07-18 (partial fix + full drift catalogue)

**Measured the FULL overlap: 34 pairs overlap, 19 DISAGREE** (not just AAVE-ETHEREUM). Full catalogue by delta:

| Pair                 | venue_launch | chain_env  | delta |
| -------------------- | ------------ | ---------- | ----- |
| AAVE_V3-BSC          | 2023-04-06   | 2024-01-23 | 292d  |
| AAVE_V3-LINEA        | 2024-09-26   | 2025-02-11 | 138d  |
| COMPOUND_V3-OPTIMISM | 2024-02-16   | 2024-04-06 | 50d   |
| COMPOUND_V3-ARBITRUM | 2023-04-14   | 2023-05-04 | 20d   |
| COMPOUND_V3-ETHEREUM | 2022-08-26   | 2022-08-13 | 13d   |
| COMPOUND_V3-BASE     | 2023-08-11   | 2023-08-04 | 7d    |
| AAVE_V3-POLYGON      | 2022-03-16   | 2022-03-12 | 4d    |
| AAVE_V3-AVALANCHE    | 2022-03-16   | 2022-03-12 | 4d    |
| AAVE_V3-OPTIMISM     | 2022-03-16   | 2022-03-15 | 1d    |
| + 10 more @ 1d       | …            | …          | 1d    |

(the ≤1d tail: COMPOUND_V3-SCROLL, UNISWAP_V2-ETHEREUM, UNISWAP_V3-ETHEREUM, UNISWAP_V3-POLYGON, ROCKETPOOL-ETHEREUM,
ETHENA-ETHEREUM, ETHERFI-ETHEREUM, KAMINO-SOLANA, JITO-SOLANA, GMX-AVALANCHE)

**DONE 2026-07-18 (`unified-api-contracts`):**

- ✅ Corrected the ONE proven-wrong value: `venue_launch_dates.DEFI_VENUE_LAUNCH_DATES["AAVE_V3-ETHEREUM"]`
  `2022-03-16 → 2023-01-27` (chain_env's own inline comment documents the subgraph-audit debunking; also aligns with
  this registry's "prefer LATER when uncertain" principle). This was the only drift with documented subgraph proof.
- ✅ Added a **drift-ratchet guard** —
  `tests/unit/test_protocol_launch_dates.py::test_venue_launch_dates_no_new_drift_vs_chain_env` allowlists the 19 known
  drifts (deltas commented) and FAILS on any NEW divergence; resolving one = removing it.

**STILL OPEN (needs operator decision — data-correctness, affects the data-status expected-window denominator):** the
other 18 drifts are NOT safely bulk-fixable — chain_env is subgraph-audited but not every one of its 111 pairs was
re-verified, and the divergences run BOTH directions (venue earlier in some, later in others), so I will NOT blind-defer
`venue_launch_dates` to `chain_env` wholesale. **Options:** (A) treat `chain_env` as the SSOT for overlapping pairs and
have `venue_launch_dates` overlay/import it (fast, but trusts chain_env for all 18 incl. the 292d/138d ones without
per-pair re-verification); (B) per-pair on-chain re-verify each ≥7d drift (AAVE_V3-BSC/LINEA, COMPOUND_V3-\*) against
mainnet first-tx / subgraph, accept the ≤1d tail as noise; (C) leave as-is + rely on the ratchet. **Recommend (B)** for
the ≥7d drifts (6 pairs) since a 292d error materially mis-classifies the expected window; the ≤1d tail is low-impact.

## On-chain verification of the 6 ≥7d drifts — DONE 2026-07-18 (operator: "run it")

Fanned out one agent per pair (Dune decoded-table lookups were blocked by "not enough credits", so each fell back to the
protocol's OWN canonical source — Aave changelog, Compound `comet` GitHub `roots.json` — + block-explorer contract
creation + governance execution timelines, cross-checked ≥2 sources). **Result: chain_env was NOT uniformly right** —
verifying per-pair was the correct call:

| Pair                 | venue      | chain_env  | **verified**   | winner        | conf | source                                             |
| -------------------- | ---------- | ---------- | -------------- | ------------- | ---- | -------------------------------------------------- |
| AAVE_V3-BSC          | 2023-04-06 | 2024-01-23 | **2024-01-23** | chain_env     | HIGH | Aave changelog "Jan 23 2024 BNB market deploys"    |
| AAVE_V3-LINEA        | 2024-09-26 | 2025-02-11 | **2025-02-11** | chain_env     | HIGH | Aave changelog Feb 11 2025 (venue matched nothing) |
| COMPOUND_V3-BASE     | 2023-08-11 | 2023-08-04 | **2023-08-11** | **venue**     | HIGH | Comet cUSDbCv3 Base contract creation              |
| COMPOUND_V3-ETHEREUM | 2022-08-26 | 2022-08-13 | **2022-08-26** | **venue**     | HIGH | Comet cUSDCv3 mainnet creation (launch ≥ creation) |
| COMPOUND_V3-ARBITRUM | 2023-04-14 | 2023-05-04 | **2023-05-15** | neither       | MED  | Compound Prop 160 executed ~May 14, market May 15  |
| COMPOUND_V3-OPTIMISM | 2024-02-16 | 2024-04-06 | **2024-04-16** | chain_env-ish | MED  | Comet OP first activity ~Apr 16 2024               |

**Applied all 6 corrections** so both registries now AGREE at the verified value — `venue_launch_dates.py`
(AAVE_V3-BSC/LINEA, COMPOUND_V3-ARBITRUM/OPTIMISM) + `chain_env.py` (COMPOUND_V3-ETHEREUM/BASE/ARBITRUM/OPTIMISM). The
drift-ratchet guard allowlist dropped from 19 → **13** (only the ≤4d tail remains: AAVE_V3-POLYGON/AVALANCHE 4d + the 1d
noise), with the 6 corrections locked by explicit assertions. The MED-confidence ARBITRUM/OPTIMISM values are
governance-execution-derived (Dune first-event confirmation was credit-blocked) — good to ±a few days, a large
improvement over the prior 20/50-day errors. **Status → resolved for the ≥7d drifts; the ≤4d tail is low-impact +
guarded.**

## CORRECTION 2026-07-18 (COMPOUND overrides reverted to the Tab-14 subgraph audit)

The instruments-service `test_evm_creation_resolver::test_compound_v3_arbitrum_uses_uac_ssot` FAILED against the first
correction pass and caught a real error in it: that test pins `("ARBITRUM","COMPOUND_V3") = 2023-05-04`, which is the
**Tab-14 subgraph audit** (2026-05-08 — earliest `dailyMarketAccountings` event 2023-05-04 22:00:26 UTC). The on-chain
verification agents could NOT run Dune (credits exhausted) and fell back to **governance-execution** dates for
ARBITRUM/OPTIMISM (medium confidence) and **contract-creation** dates for ETHEREUM/BASE — all LOWER authority than a
day-precise subgraph first-market-activity date. I had wrongly let those override the Tab-14 audit.

**Reverted all four COMPOUND pairs to the Tab-14 subgraph-audited `chain_env` values** and aligned `venue_launch_dates`
to them: ETHEREUM 2022-08-13, ARBITRUM 2023-05-04, BASE 2023-08-04, OPTIMISM 2024-04-06 (both registries now agree at
the audited value; the IS test passes). **The AAVE_V3-BSC (2024-01-23) and AAVE_V3-LINEA (2025-02-11) corrections
STAND** — those used Aave's OWN protocol changelog (a first-party authority that outranks a third-party subgraph audit,
and which agreed with chain_env). **Residual (flagged, not resolved):** ETHEREUM's contract-creation date (2022-08-26,
per Etherscan) vs the Tab-14 first-event (2022-08-13) is a genuine conflict — a first market event cannot precede
contract deployment, so one is wrong; needs a Dune first-`Supply`/`SupplyCollateral`-event query (blocked here by
credits) to settle. Kept the audited 2022-08-13 as the conservative default.

**Lesson:** a documented subgraph audit outranks a governance/announcement/contract-creation date; do NOT override it on
lower-authority evidence. The drift-ratchet guard + the downstream evm_creation_resolver test together caught it.

## Final resolution 2026-07-18 (`unified-api-contracts@a6933ef3`) — 0 drift, allowlist emptied

Closed the last two open items. **Registries are now FULLY reconciled — the drift-ratchet allowlist is empty and the
guard asserts zero drift as the standing contract.**

**1. ETHEREUM contract-creation-vs-subgraph conflict → RESOLVED (no code change; the audited 2022-08-13 is correct).**
The residual flag above worried that the Etherscan contract-creation `2022-08-26` predated the Tab-14 first-event
`2022-08-13` (impossible — a market event cannot precede deployment). Re-verified against the canonical Compound III
`cUSDCv3` Comet contract `0xc3d688B66703497DAA19211EEdff47f25384cdc3`: Etherscan reports its creation as **"3 yrs 339
days ago"** (from 2026-07-18 ≈ **2022-08-13**), tx `0xfe8e6819…3cc83cc0` — i.e. deployment ≈ the same day as the first
subgraph event. A web search confirmed the **August 26, 2022** figure my earlier agent used was the public
**announcement/blog** date, NOT the on-chain deployment. So there was no real conflict: `2022-08-13` (subgraph
first-event ≈ contract creation) is correct; `2022-08-26` was an announcement. Both registries already held `2022-08-13`
— confirmed, not changed.

**2. ≤4d tail (13 pairs) → RECONCILED.** With ETHEREUM confirming chain_env's Tab-14 subgraph dates are the day-precise
authority, the 11 EVM tail pairs (AAVE_V3-POLYGON/AVALANCHE/OPTIMISM, COMPOUND_V3-SCROLL, UNISWAP_V2-ETHEREUM,
UNISWAP_V3-ETHEREUM/POLYGON, ROCKETPOOL-ETHEREUM, ETHENA-ETHEREUM, ETHERFI-ETHEREUM, GMX-AVALANCHE) were aligned
`venue_launch_dates → chain_env` (venue's "prefer later" bias was systematically +1d; chain_env's subgraph first-event
is exact). The **2 Solana pairs (KAMINO-SOLANA, JITO-SOLANA) were reconciled the OTHER way** — chain_env aligned to the
P3-verified `venue_launch_dates` values (2022-08-24 / 2022-08-16) — because Solana has no Graph subgraph, so the Tab-14
EVM-subgraph audit never covered it and the P3 agent's mainnet-launch verification is the better authority there.

**Guard:** `test_venue_launch_dates_no_new_drift_vs_chain_env` now asserts `not drifts` (full reconciliation), the
`known_drifts_pending_audit` allowlist is `set()`, and all 20 reconciled pairs (6 ≥7d + 11 EVM tail + AAVE-ETH + 2
Solana) are locked by explicit membership + value assertions, so any revert fails CI.

**Lesson (extends the one above):** authority is domain-specific — an EVM subgraph audit is authoritative for EVM
chains, but on Solana (no equivalent subgraph) a first-party mainnet-launch verification wins. Reconcile toward the
higher-authority source _for that chain_, not blanket-toward one registry.
