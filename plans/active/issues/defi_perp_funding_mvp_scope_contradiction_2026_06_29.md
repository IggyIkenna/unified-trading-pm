---
doc_type: issue
title: DeFi perp_funding MVP-scope contradiction — is_mvp() vs capability registries vs the backfill plan (2026-06-29)
summary:
  The `perp_funding` data_type evaluates is_mvp()=False for EVERY venue (DRIFT, Hyperliquid) under BOTH cefi and defi,
  yet the v10 backfill plan launched two perp_funding backfill VMs as MVP work and the honest-coverage denominator
  counts 424 DRIFT perp_funding cells as reachable. Three SSOTs disagree about whether DeFi perp_funding is in MVP
  scope. Blocks resolution of the P0 AO item on the Solana-drift backfill stall.
status: open
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [mvp-scope, defi, perp-funding, drift, hyperliquid, ssot-contradiction, data-quality, honest-coverage]
related: [plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md]
created: 2026-06-29
parent_epic: defi_master
priority: P1
source:
  [
    mvp_backfill_defi_onchain_v10_2026_06_27.md (G1.5 blocked OPERATOR item + perp_funding backfill VMs),
    agent-orchestrator backlog item mvp_backfill_defi_onchain_v10-010 (blocked),
    unified_api_contracts/canonical/crosscutting/mvp_scope.py (is_mvp SSOT),
  ]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
drift_direction: advance-code
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-09
locked_since: 2026-05-21
---

# DeFi perp_funding MVP-scope contradiction (2026-06-29)

> **🟡 2026-07-09: the "Resolution status" / "Recommendation" sections below (provisional Option 1, "out of MVP scope")
> are SUPERSEDED.** A broader operator ruling on DeFi MVP framing (`MVP_SCOPE["defi"]` v13,
> `unified-api-contracts@89b16943`) resolves this as **Option 2** — DRIFT-SOLANA `PERPETUAL` `perp_funding` IS MVP now.
> See the 2026-07-09 Progress Log entry at the bottom for what changed and what's still genuinely open (todos 2-4 — the
> registry pinning test, the v10 plan cell flip, and the Helius-ceiling backfill work are all unactioned).

> Filed while investigating the only `blocked` item in the locally-running agent-orchestrator backlog
> (`mvp_backfill_defi_onchain_v10-010`, `[OPERATOR] P0` — "Solana-drift backfill performance stall"). Before deciding
> the stall intervention, the operator asked: **is DRIFT / Solana actually in the DeFi MVP list?** Verifying that
> against the UAC SSOT surfaced a three-way contradiction that gates the answer.

## TL;DR

- **DRIFT-SOLANA the venue IS in the defi MVP list** — but only in its **DEX role** (`POOL`/`DEX_POOL` →
  `dex_pool_state`/`dex_pool_swaps`). Those cells are `is_mvp()`-true.
- **DRIFT `perp_funding` is NOT MVP**, and neither is Hyperliquid `perp_funding`. The `perp_funding` data_type evaluates
  `is_mvp()=False` for **every** venue under **both** asset groups.
- Funding data for perps is actually MVP **under `cefi`** via the `funding_rate` / `derivative_ticker` data_types on
  `PERPETUAL` instruments — NOT via the defi `perp_funding` data_type.
- **Per the operator's standing rule** ("fix only if under MVP scope, else don't download for now"), the blocked
  Solana-drift backfill is currently **out of MVP scope → do not build the sig index / do not download.** But the
  contradiction below must be ruled on first, because it equally affects the Hyperliquid perp VM and the v10 G2 gate.

## Resolution status (2026-06-29)

**Provisional operator call (Harsh, pending Ikenna confirm): OUT OF MVP SCOPE.** UAC `is_mvp()` is the designated SSOT
for "what is MVP"; it says not-MVP, so it's not-MVP. The AO blocked item `mvp_backfill_defi_onchain_v10-010` was
resolved on the planning-VM AO (plan G1.5 checkbox flipped, blocked-queue answered, stale task pruned). The UAC code fix
below is **deferred until Ikenna confirms** — do not ship it on the provisional call.

## Evidence

### 1. `is_mvp()` says `perp_funding` is MVP-true for zero cells

`is_mvp()` (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py` ~L1091-1098) gates a defi
cell on a **strict 3-axis AND**: `venue` AND `instrument_type` AND `data_type` must all be declared in the rule.

Probe results (run via `unified-api-contracts/.venv`):

| asset_group | venue                | instrument_type | data_type         | `is_mvp`                                     |
| ----------- | -------------------- | --------------- | ----------------- | -------------------------------------------- |
| defi        | DRIFT-SOLANA         | DEX_POOL        | dex_pool_swaps    | ✅ True                                      |
| defi        | DRIFT-SOLANA         | POOL            | dex_pool_state    | ✅ True                                      |
| defi        | DRIFT-SOLANA         | **PERPETUAL**   | **perp_funding**  | ❌ **False**                                 |
| cefi        | DRIFT / DRIFT-SOLANA | PERPETUAL       | perp_funding      | ❌ False (DRIFT not a classified cefi venue) |
| cefi        | HYPERLIQUID          | PERPETUAL       | **perp_funding**  | ❌ **False**                                 |
| cefi        | HYPERLIQUID          | PERPETUAL       | funding_rate      | ✅ True                                      |
| cefi        | HYPERLIQUID          | PERPETUAL       | derivative_ticker | ✅ True                                      |
| cefi        | HYPERLIQUID          | PERPETUAL       | trades            | ✅ True                                      |

Root cause:

- **defi rule** (`mvp_scope.py` ~L567-584): `instrument_types = {POOL, DEX_POOL, LST, LENDING}` — **no `PERPETUAL`**;
  `data_types` includes `perp_funding`. Perp funding semantically lives on `PERPETUAL` instruments, so the 3-axis AND
  can never pass for `perp_funding`.
- **cefi rule**: `data_types = {book_snapshot_5, derivative_ticker, funding_rate, trades}` — **no `perp_funding`**. cefi
  captures funding via `funding_rate` / `derivative_ticker` instead.
- **`perp_funding`** is therefore a **defi-only data_type name** that is unreachable for MVP under either rule.

git-blame: the defi `instrument_types` frozenset was authored 2026-06-08 (`824944660`); `PERPETUAL` was never included.
Current `MVP_SCOPE_CONFIG_VERSION = 12`.

### 2. The defi rule's own comment lists perp_funding as intended-MVP

`mvp_scope.py` ~L537:

> `perp_funding — Perpetual funding rates (Hyperliquid, Aster, Drift)`

So author **intent** was that perp_funding (incl. Drift) is MVP — but the coded `instrument_types` axis contradicts it.

### 3. The capability/coverage registries DO declare DRIFT perp_funding (drives the denominator)

- `unified_api_contracts/registry/defi_venue_capabilities.py` ~L139:
  `"DRIFT-SOLANA": {"perp_funding": "2022-01-01", "dex_pool_swaps": "2022-01-01"}`
- `unified_api_contracts/registry/expected_coverage.py` ~L268: `"DRIFT-SOLANA": ["perp_funding", "position_data"]`

`instruments-service/scripts/measure_honest_coverage.py` computes
`reachable = captured + attempted_failed + expected_unattempted` (~L429) — it does **NOT** gate the denominator on
`is_mvp()`. The reachable set comes from the catalogue/manifest, which is seeded by these capability registries. That is
why the v10 G2 coverage table reports **424 DRIFT `perp_funding` cells as reachable** and the gate FAILS until they are
filled — even though `is_mvp()` says those cells are out of MVP.

### 4. The v10 plan treats perp_funding as MVP and launched two perp backfill VMs

`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`:

- G1 launched `mtds-solana-drift-backfill` (DRIFT `perp_funding`) **and** `mtds-perp-funding-backfill` (Hyperliquid
  `perp_funding`) as MVP work.
- G2 gate enumerates `perp_funding` as 1 of the 6 MVP defi data_types that must reach `attempted_failed=0`.

### 5. Live state of the blocked backfill (2026-06-29)

- VM `mtds-solana-drift-backfill` no longer exists (SPOT — preempted/terminated after its last log write 09:13Z).
- Consolidated `_index/drift_v2_sig_index.parquet` was **never built** (Option A not executed); only the 6,293+ parts
  exist.
- The **429-burst anomaly** is real: run.log's final writes show ~24 batches advanced in 0.25s on pure HTTP 429s (no
  backoff). DRIFT `perp_funding` parquets exist only for 2025-01-09/10/11 (117/94/74 MB); the 429-burst dates (e.g.
  2026-03-05/06) have **no** DRIFT parquet. The repeated Helius 429s point to a Helius plan rate-limit ceiling.

## The three-way contradiction (what must be ruled on)

| SSOT                                                                                      | Says about DeFi `perp_funding`                                                                            |
| ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `mvp_scope.is_mvp()` (the "what is MVP" SSOT)                                             | **NOT MVP** — unreachable for any cell                                                                    |
| `defi_venue_capabilities` + `expected_coverage` (drive the manifest/coverage denominator) | **In scope** — DRIFT-SOLANA produces perp_funding since 2022-01-01 → 424 reachable cells, gate-failing    |
| v10 backfill plan + cefi `funding_rate`/`derivative_ticker`                               | Plan treats it as MVP; meanwhile cefi already models perp funding under a different data_type/asset_group |

## Resolution options (OPERATOR RULING REQUIRED)

- **Option 1 — SSOT is correct; perp_funding out of defi MVP.** Remove `perp_funding` from `DRIFT-SOLANA` (and any other
  defi venue) in `defi_venue_capabilities` + `expected_coverage` so it leaves the reachable denominator; resolve the AO
  P0 item as out-of-scope (no sig index, no download); re-examine the Hyperliquid perp VM under the same logic. Net: do
  not download DRIFT perp data now. **← provisional pick (2026-06-29).**
- **Option 2 — intent is correct; perp_funding IS MVP.** Add `PERPETUAL` to the defi rule's `instrument_types` (matching
  the line-537 comment) so DRIFT/Hyperliquid/Aster perp_funding becomes `is_mvp()`-true; then the DRIFT backfill IS in
  scope → fix it (Helius plan upgrade for the 429 ceiling + build the consolidated sig index). Must also reconcile defi
  `perp_funding` vs cefi `funding_rate`/`derivative_ticker` to avoid double-modeling the same funding data.
- **Option 3 — perp funding is cefi-only.** Treat DRIFT/Hyperliquid perps as cefi; capture funding via cefi
  `funding_rate`/`derivative_ticker` on `PERPETUAL`; remove `perp_funding` from the defi rule + registries entirely;
  classify DRIFT as a cefi perp venue if it should be in scope at all.

**Recommendation:** the `is_mvp()` SSOT + the existing cefi `funding_rate`/`derivative_ticker` model both point to
Option 1/3 (DeFi `perp_funding` is not the intended capture path) — i.e. **the Solana-drift backfill is out of MVP scope
and should not be downloaded now.** But this is an operator ruling because it determines whether the Hyperliquid perp VM
and the v10 G2 perp_funding gate are valid.

## Todos

- [ ] [OPERATOR] P0. Confirm the ruling: Option 1 / 2 / 3 above (provisional = Option 1, out of scope). Determines
      DRIFT + Hyperliquid perp backfill scope and whether the AO item stays resolved or reopens.
- [ ] [SCRIPT] P1. Once ruled: reconcile `mvp_scope.py` (defi `instrument_types` / `data_types`) with
      `defi_venue_capabilities.py` + `expected_coverage.py` so `is_mvp()` and the coverage denominator agree on
      `perp_funding`. Repo: `unified-api-contracts`. Add a `test_mvp_scope.py` assertion pinning the ruling.
- [ ] [SCRIPT] P1. Apply the ruling to the v10 plan: update G1/G2 scope for `perp_funding`; flip 424 DRIFT
      `perp_funding` cells to the correct honest state (out-of-scope vs attempted_failed) so the coverage gate reflects
      reality. Repos: `instruments-service`, `unified-trading-pm`.
- [ ] [SCRIPT] P2. If Option 1/3: confirm Hyperliquid perp funding is captured via cefi
      `funding_rate`/`derivative_ticker` and is not silently dropped by removing defi `perp_funding`. Repo:
      `market-tick-data-service`.
- [x] [SCRIPT] P1. Fix the DRIFT SPOT_PAIR `perp_funding` leak (bundled `_PERPS` instrument_types with no
      per-instrument_type data_types split) via `VALID_DATA_TYPES_VENUE_EXCLUSIONS`; add regression tests. Repo:
      `unified-api-contracts`. ✅ — `unified-api-contracts@b7cf3106` (2026-07-11).
- [ ] [OPERATOR] P0. Decide the DRIFT V2 sig-index Helius throughput path: (a) upgrade the Helius API plan for higher
      RPS, (b) launch N more parallel-walker VM segments (`build_drift_v2_sig_index.py --before-sig`) to divide the
      ~11-month unindexed gap (2025-01-15 → 2025-12-23), or (c) accept the gap and mark those dates
      `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]`-equivalent out-of-reach, closing the AO item without full coverage.
      Blocks the actual DRIFT perp_funding backfill VM re-launch (AO item `mvp_backfill_defi_onchain_v10-010`).
- [ ] [SCRIPT] P2. Once the operator rules on the todo above: re-run the DeFi expected-universe enumerator
      (`instruments-service/scripts/enumerate_expected_universe.py`) so the manifest's `expected_unattempted` grid picks
      up the SPOT-leak fix (currently only stops NEW wrong rows; existing 51,301-row snapshot is stale until
      re-enumerated). Repo: `instruments-service`.

## Codex SSOTs

- `codex/02-data/honest-coverage-model.md` — two-layer / instrument-gates-download denominator model.
- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted` / reachable semantics.
- UAC `mvp_scope.py` is the live SSOT for "what is MVP"; the capability/coverage registries are the live SSOT for the
  reachable denominator — this issue is precisely that those two disagree for `perp_funding`.

## Progress Log

### 2026-06-29 — filed + AO item resolved (provisional)

Investigation triggered by the blocked AO item. Confirmed `is_mvp()` returns False for all `perp_funding` cells (defi +
cefi), confirmed the capability/coverage registries declare DRIFT-SOLANA perp_funding (424 reachable cells), confirmed
cefi models funding via `funding_rate`/`derivative_ticker`, and confirmed the v10 plan launched two perp_funding VMs as
MVP work. Live state: DRIFT VM gone, sig index never built, 429-burst anomaly real (only 3 dates of genuine data).
Operator (Harsh) provisional call: out of MVP scope per UAC `is_mvp()`. Resolved the AO item on the planning-VM AO (G1.5
checkbox flipped, blocked-queue entry answered as operator, stale blocked task pruned → 0 blocked). UAC code fix
deferred pending Ikenna confirm.

### 2026-07-09 — superseded by a broader operator ruling: **Option 2** (perp_funding IS MVP)

A separate, broader operator ruling on DeFi MVP framing generally (§E5 of
`instruments_docs_audit_outstanding_items_2026_07_08.md`: _"DeFi MVP framing — define for now, just keep all as MVP
though"_) landed a real `MVP_SCOPE["defi"]` rule (`DeFiMvpRule` v13, `unified-api-contracts@89b16943`) that resolves
this issue's three-way contradiction as **Option 2**, not the provisional Option 1 above: `PERPETUAL` is now a real DeFi
MVP `instrument_type` (derived from live adapter code, not hand-picked), so
`is_mvp("defi", "DRIFT-SOLANA", "PERPETUAL", "perp_funding")` now evaluates `True`. This is a side effect of the broader
"everything we capture" ruling, not a dedicated re-litigation of the DRIFT-perp-backfill question specifically — the
operator ruling this doc tracks is superseded, not independently re-confirmed.

**What this changes**: `is_mvp()` (Evidence §1) now agrees with the capability/coverage registries (Evidence §3) and the
v10 plan (Evidence §4) that DRIFT-SOLANA `perp_funding` is in scope — the axis-1-vs-axis-3 contradiction this doc was
filed to track is closed.

**What this does NOT change / still open**:

- Todo 2 (reconcile `defi_venue_capabilities.py` / `expected_coverage.py` with `is_mvp()`, add a pinning test) — NOT
  done. Those registries were never edited by the v13 pass; they already independently declared DRIFT-SOLANA
  perp_funding, so no conflict remains to reconcile, but the todo's own pinning-test ask is still unactioned.
- Todo 3 (apply the ruling to the v10 backfill plan; flip the 424 DRIFT perp_funding cells) — NOT done. The real
  live-state finding in Evidence §5 (VM gone, sig index never built, 429-burst Helius rate-limit ceiling) is unaffected
  by the MVP-scope ruling — a Helius plan upgrade + sig-index build is still real, unstarted work if the Solana-drift
  backfill is to actually run.
- Todo 4 (confirm Hyperliquid perp funding capture path) — NOT done, unaffected by this ruling.
- Todo 1 (operator confirm) — the ORIGINAL question (Option 1/2/3 for THIS specific DRIFT-backfill decision) was never
  independently re-asked; it was overtaken by the broader DeFi-MVP-framing ruling before an explicit answer landed. If
  the Helius-ceiling / sig-index work is picked up, worth a fresh explicit confirm that "in MVP scope" (now true) also
  means "worth spending the backfill effort now" — those are two different questions this doc's Option 1/2/3 only
  partially separates.

### 2026-07-11 — picked up AO item `mvp_backfill_defi_onchain_v10-010`; found + fixed a second, separate bug; the real

### backfill is genuinely blocked on a Helius infra/cost decision

Slot 3 (data_engineering) picked up the reopened AO todo "Backfill the 424 DRIFT perp_funding cells." Live-state
investigation found the plan's "424" figure is now stale — the current availability manifest
(`_index/availability_index.parquet`) shows DRIFT `perp_funding`: `captured=8`, `attempted_failed=39` (stale
`attempted_at=2026-05-31`, error `drift_v2_sig_index.parquet missing`), and **`expected_unattempted=51,301`** across 41
distinct `instrument_id`s.

**New bug found + FIXED (shipped `unified-api-contracts@b7cf3106`):** most of those 41 instrument_ids are DRIFT SPOT
markets (`DRIFT-SOLANA:SPOT:BSOL`, `:USDE`, `:PYUSD`, `:JITOSOL`, `:LBTC`, `:CBBTC`, `:BONK`, `:PYTH`, `:DRIFT`,
`:EURC`, `:SUSDE`, `:WBTC`, `:JUP`, ...) — SPOT instruments structurally cannot have a funding rate. Root cause:
`unified_api_contracts/registry/capability_declarations/_defi.py`'s `drift` entry bundles `instrument_types=_PERPS`
(`[PERPETUAL, SPOT_PAIR]`) with a single `data_types=["perp_funding","oracle_prices"]` list applied to both types — the
`_ProtocolCapability` schema has no per-instrument_type data_types split, so
`valid_data_types_for_venue_instrument_type` (`market_data_categories.py:1121-1123`) returns the full `perp_funding`
grant for DRIFT SPOT markets too. Fixed via the existing `VALID_DATA_TYPES_VENUE_EXCLUSIONS` mechanism (same pattern as
the prior ICE `futures_chain`/`ohlcv_1s` fix): added `("defi", "DRIFT", "spot_pair"): frozenset({"perp_funding"})`, kept
`oracle_prices` (legitimately applies to SPOT). 4 new regression tests in
`tests/test_valid_data_types_by_instrument_type.py`. This will shrink the `expected_unattempted` count once the manifest
is next re-enumerated (not yet re-run — enumeration is a separate, scheduled process; this fix only stops NEW rows from
being seeded wrong).

**What's still genuinely blocked (todo 3, unchanged) — this IS an operator decision, not something fixable in code:**
confirmed via GCS row-group inspection that the consolidated `_index/drift_v2_sig_index.parquet` still does not exist.
Two partial part-sets exist from the prior stalled effort: `_index/drift_v2_sig_index_parts/` (6,293 parts, Builder #1
walking HEAD backwards, covers blockTime range **2025-12-23 → 2026-05-29**) and `_index/drift_v2_sig_index_parts_b/`
(876 parts, Builder #2 parallel walker, covers **2024-10-31 → 2025-01-15**). There is a genuine **~11-month unindexed
gap (2025-01-15 → 2025-12-23)** neither builder ever walked. Also confirmed: Drift's public S3 historical archive
(`_backfill_drift_s3_date` in `market-tick-data-service`) only covers up to 2025-01-07/08 (V1→V2 migration) — past that
date the ONLY path to historical funding data is walking Solana tx signatures via Helius RPC `getSignaturesForAddress`,
which is exactly what hit the 429-burst rate-limit wall documented in G1.5 above. This is a real Helius API
plan/throughput ceiling, not a retry/backoff code bug (the builder script `build_drift_v2_sig_index.py` already retries
with backoff, 5 attempts, up to ~30s, before giving up per page). Closing an 11-month gap at the previously-observed
serial throughput (~85-90 sig-pages/min, one VM) is impractical without either (a) a paid Helius plan upgrade for higher
RPS, or (b) launching several more parallel-walker VM segments (`--before-sig` / `--parts-prefix`) to divide the gap —
both are cost/infra tradeoffs an operator needs to weigh, not something this agent can decide or execute unilaterally.
Filed as a `/blocked` on the AO todo rather than guessing.
