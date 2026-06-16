---
type: audit-result
title: DeFi pipeline — Code ↔ Codex drift audit (2026-05-27)
epic: defi_master
auditor: harsh
date: 2026-05-27
status: complete
instructions_ref: plans/audit/instructions/defi_master_audit_instructions.md
scope: DeFi data pipeline (instruments-service → MTDS → MDPS → features-onchain) — code ↔ codex drift only
---

# DeFi pipeline — Code ↔ Codex drift audit (2026-05-27)

Audit of where the **codex SSOTs disagree with the actual code/GCS**, run by re-reading the Python (MTDS / MDPS / UAC /
features-service) and cross-checking GCS on 2026-05-27 **while the end-to-end backfill is still running**. Per operator
direction: code-side fixes are **deferred until the run completes**; codex-doc fixes are safe now. Each finding has a
verdict (`codex-stale` = doc wrong, fix doc; `code-bug` = code wrong, fix code after run; `aligned` = no action;
`for-decision` = needs an operator/Ikenna call). Source method is codified in the instruction file checklist items j–n.

> **⚠ Other agents are correcting pipeline code concurrently.** Before acting on any `code-bug` row, re-verify current
> state — it may already be fixed. This audit changed **no service code**; only codex docs (D1) + this record.

## Checklist results (instruction items j–n + h/i re-checked)

| Item | Check                                                  | Result          | Evidence                                                                                                                                                                                                                                                                                  |
| ---- | ------------------------------------------------------ | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| (h)  | No removed providers (Elysium/Arkham/Bloxroute/Infura) | **RED**         | `bloxroute` live relay URLs in MTDS `cli/handlers/mev_events_handler.py:42-43` (+ stale `.bak`); `infura` in UAC `_defi_chain_data.py:734` + comment `gas_fee_handler.py:78`. Prior grep scope omitted MTDS (now fixed in instructions). `arkham`=clean; `elysium`=client name only (OK). |
| (i)  | Pyth Solana-only, Chainlink EVM                        | **GREEN**       | `oracle_prices_handler.py` — Chainlink `latestRoundData` (EVM) + Pyth Hermes (Solana). Matches `defi-execution-overview.md`.                                                                                                                                                              |
| (j)  | data_type names match catalog                          | **RED → fixed** | Code `_*_DATA_TYPE` = `dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`; catalog used `swap_events`/`pool_state`/`lending_metrics`/`funding_rates`. **Renamed in catalog this session.**                                                                                      |
| (k)  | data_type completeness                                 | **AMBER**       | Code emits ~22 DeFi data_types (`cli/main.py` collect-\* ops); catalog documented 14. Banner added; full reconciliation = gap.                                                                                                                                                            |
| (l)  | storage bucket per data_type                           | **GREEN**       | Verified `get_write_bucket_name(...)` per handler; dedicated buckets for lst_rates/lending_indices/dex_pools/oracle_prices/perp_funding; defi bucket for dex_swaps/vault_share_price/dex_pool_state. Matches `data-lineage`. Legacy in-bucket prefixes are stale (cleanup gap).           |
| (m)  | MDPS processed-vs-bypass scope                         | **RED**         | `DefiLendingIndicesAdapter` decorator-registered + UAC `needs_candle_processing("lending_indices")=True`, but NOT imported in top-level `app/adapters/__init__.py` → dead at runtime. Outcome matches codex "bypass" by accident.                                                         |
| (n)  | venue/capability consistency                           | **RED**         | `RADIANT` in `defi_venues.py` `DEFI_VENUE_PHASE=live` but absent from `PROTOCOL_CAPABILITIES`+`SUBGRAPH_IDS`. ~8 venues live in code but absent from `defi-venue-protocol-catalogue.md`.                                                                                                  |

## Findings register

| #   | Area                             | Verdict                                | Code/GCS truth (file:line)                                                                                                                                                                                                 | Decision (mine, for verification)                                                                                                                                                   |
| --- | -------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | data_type names                  | codex-stale → **FIXED**                | handler `_*_DATA_TYPE` constants → `dex_swaps`/`dex_pool_state`/`lending_indices`/`perp_funding`                                                                                                                           | Code authoritative. **Done**: renamed catalog headings + instrument-type map + banner (this rev).                                                                                   |
| D2  | bypass-type storage buckets      | codex-right; my pipeline doc was wrong | `get_write_bucket_name("lst-rates"/"lending-indices"/"dex-pools"/...)` → dedicated buckets; in-defi-bucket prefixes stale 2026-04-14                                                                                       | **Done**: corrected `defi-data-pipeline.md`. Legacy-prefix data cleanup = deferred gap.                                                                                             |
| D3  | MDPS lending adapter dead        | **code-bug**                           | `DefiLendingIndicesAdapter` registered + UAC gate `True`, not imported in `app/adapters/__init__.py` (MDPS)                                                                                                                | Intent = bypass (D4). Right fix: UAC gate→`False` + delete adapter + fix `__init__.py` comment. **Deferred** (code).                                                                |
| D4  | features-onchain read source     | aligned                                | `onchain/app/core/data_loader.py:433/470` read raw `raw_tick_data/...`                                                                                                                                                     | None.                                                                                                                                                                               |
| D5  | bucket-name convention           | codex-stale (self-bannered)            | canonical `resolve_bucket_name(...)`; lineage uses legacy `{category}`                                                                                                                                                     | Existing ML-14 rewrite item; no new action.                                                                                                                                         |
| D6  | catalog completeness             | codex-stale                            | ~22 data_types in code vs 14 in catalog (missing lst_rates, vault_share_price, liquidations, risk_params, rewards, eigenlayer_rewards, native_staking_rates, aggregator_route, restaking_rewards, governance_proposals, …) | Partial fix (banner+names). **Full reconciliation = gap item** (add missing types). Codex-side.                                                                                     |
| D7  | `bloxroute` MEV relays           | **for-decision** (poss. code-bug)      | `mev_events_handler.py:42-43` `MEV_BOOST_RELAYS` has 2 live bloxroute URLs; `.bak` file present                                                                                                                            | Ban (CLAUDE.md) targets data/RPC providers; MEV-Boost relays are a different concern. **Operator call**: is bloxroute-as-relay banned? Delete the `.bak` regardless. Deferred.      |
| D8  | `infura` references              | for-decision / codex-stale             | `_defi_chain_data.py:734` Starknet `infura_compatible` template; `gas_fee_handler.py:78` comment                                                                                                                           | Starknet infura-compatible endpoint may be legit (named option, not default). **Decision**: keep but rename/document to avoid tripping the ban; drop the gas-fee comment. Deferred. |
| D9  | venue list drift                 | codex-stale                            | EULER_V2/BENQI/VENUS/RADIANT/MARGINFI/SOLEND + SOLAYER/PICASSO/CAMBRIAN in code (`defi_venues.py`, `_defi.py`) but not in venue catalogue                                                                                  | Update `defi-venue-protocol-catalogue.md` to match code. **Gap item.** Codex-side.                                                                                                  |
| D10 | RADIANT live w/o capability      | **code-bug**                           | `defi_venues.py` `DEFI_VENUE_PHASE[RADIANT]=live` but no `PROTOCOL_CAPABILITIES`/`SUBGRAPH_IDS` entry — cannot actually fetch                                                                                              | Right fix: add capability+subgraph OR downgrade RADIANT from `live`. **Deferred** (code). Operator/Ikenna to confirm intent.                                                        |
| D11 | empty/deprecated venues          | codex-stale                            | TRADER_JOE/VELODROME/GMX-AVALANCHE in `EMPTY_OR_DEPRECATED_DEFI_VENUES`/`DEFI_INSTRUMENTS_NOT_YET_COLLECTED` but catalogue marks ✅                                                                                        | Annotate them in `defi-venue-protocol-catalogue.md`. **Gap item.** Codex-side.                                                                                                      |
| D12 | source-mapping drift             | codex-stale                            | catalog `oracle_prices` omits Pyth; `lending_indices` omits Spark + Compound V3; `lst_rates` absent (conflated w/ staking_yields)                                                                                          | Folded into D6 catalog reconciliation. Codex-side.                                                                                                                                  |
| D13 | governance_proposals vs \_events | for-decision (poss. parallel path)     | two handlers: `governance_events_handler.py` (`governance_events`) + `governance_proposals_handler.py` (`governance_proposals`)                                                                                            | Likely accidental parallel path (violates no-parallel-paths). **Operator call**: consolidate to one. Deferred.                                                                      |

**Verdict summary:** codex SSOTs are directionally correct on architecture; drift is mostly **stale catalog/venue docs**
(D1/D6/D9/D11/D12 — codex-side) plus **3 code issues** (D3 dead adapter, D7 banned relay, D10 unbacked live venue) and
**2 for-decision** items (D8, D13). No `code-bug` is currently breaking the running pipeline (D3 matches intended
bypass; D7/D10 affect MEV/venue scope, not the dex_swaps backfill).

## Update 2026-05-27 (same-day) — reconciliation applied + 2 new code findings

**Codex-doc fixes shipped this session** (code-authoritative, safe):

- **D1, D6, D12** — `defi-data-types-catalog.md` reconciled: canonical names + staleness banner (D1); § "Additional data
  types" added covering the ~12 previously-undocumented types (lst*rates, vault_share_price, liquidations, risk_params,
  utilization, rewards, eigenlayer_rewards, native_staking_rates, aggregator_route, protocol_outages,
  governance_proposals, dex_pool_swaps, restaking*\*) (D6); `oracle_prices` (+Pyth), `lending_indices` (+Spark/Compound
  V3), `perp_funding` (real venues, not Synthetix) sources corrected + dedicated-bucket note (D12).
- **D9, D11** — `defi-venue-protocol-catalogue.md` gained a "Registry inconsistencies + pending venues" section (the
  catalogue was already ~90% complete; only ~8 edge venues were missing, and they're in broken registry states).

**New code findings (deferred-until-pipeline-done):**

- **D14 — `dex_pools` vs `dex_pool_state` data_type divergence.** `dex_pools_handler.py` records the manifest under
  `_DEX_POOLS_DATA_TYPE = "dex_pools"` (L62) but writes the parquet with `data_type="dex_pool_state"` (L569). Manifest
  and data disagree on the data_type name. **code-bug** — pick one canonical name.
- **D15 — HYPERLIQUID + ASTER phase mismatch.** Both `DEFI_VENUE_PHASE=pipeline` in `defi_venues.py` but
  `perp_funding_handler` actively collects them. **code-bug** — reconcile phase (or confirm cefi-axis classification).
- **D10 generalized** — not just RADIANT: EULER_V2, VENUS, BENQI, RADIANT-ETH, MARGINFI, SOLEND are all
  `DEFI_VENUE_PHASE=live` + in `MTDS_DEFI_VENUES` with **no `PROTOCOL_CAPABILITIES`/`SUBGRAPH_IDS`** backing; and
  SOLAYER/PICASSO/CAMBRIAN are the inverse (capability declared, venue not registered).

## Gap items (ready to paste / tracked in the active issue plan)

- [x] [DOC] P2. D1 — catalog data_type names renamed to canonical + staleness banner — `pm@<this commit>` — parent_epic:
      defi_master
- [x] [DOC] P2. D6/D12 — reconciled `defi-data-types-catalog.md`: § "Additional data types" added (~12 types) +
      `oracle_prices`/`lending_indices`/`perp_funding` sources fixed + dedicated-bucket note — this session —
      parent_epic: defi_master
- [x] [DOC] P2. D9/D11 — `defi-venue-protocol-catalogue.md` gained "Registry inconsistencies + pending venues" section
      (catalogue was ~90% complete; the ~8 missing venues are in broken registry states, documented there) — this
      session — parent_epic: defi_master
- [ ] [CODE] P3. **DEFERRED-UNTIL-PIPELINE-DONE** D14 — `dex_pools_handler`: align manifest data_type (`dex_pools`) with
      written data_type (`dex_pool_state`) — pick one canonical — parent_epic: defi_master
- [ ] [CODE] P3. **DEFERRED-UNTIL-PIPELINE-DONE** D15 — reconcile HYPERLIQUID/ASTER `DEFI_VENUE_PHASE` (pipeline) with
      active `perp_funding` collection (live) — parent_epic: defi_master
- [ ] [CODE] P2. **DEFERRED-UNTIL-PIPELINE-DONE** D3 — UAC `needs_candle_processing("lending_indices")=False` + delete
      dead `DefiLendingIndicesAdapter` + fix `app/adapters/__init__.py` comment — parent_epic: defi_master
- [ ] [CODE] P3. **DEFERRED + FOR-DECISION** D7 — remove `bloxroute` relay URLs from `mev_events_handler.py` if covered
      by removed-providers rule (operator call); delete stale `mev_events_handler.py.bak` regardless — parent_epic:
      defi_master
- [ ] [CODE] P3. **DEFERRED + FOR-DECISION** D8 — Starknet `infura_compatible` template: keep+rename/document or remove;
      drop the `gas_fee_handler.py:78` infura comment — parent_epic: defi_master
- [ ] [CODE] P2. **DEFERRED-UNTIL-PIPELINE-DONE** D10 (generalized) — 6 venues `live` with no capability backing
      (EULER_V2, VENUS, BENQI, RADIANT-ETH, MARGINFI, SOLEND) + 3 inverse (SOLAYER/PICASSO/CAMBRIAN: capability, no
      venue): add `PROTOCOL_CAPABILITIES`+`SUBGRAPH_IDS` / register venue, or downgrade from `live` — parent_epic:
      defi_master
- [ ] [CODE] P3. **DEFERRED + FOR-DECISION** D13 — consolidate `governance_events` vs `governance_proposals` handlers to
      a single path — parent_epic: defi_master

## Active plans absorbing these gaps

| Gap            | Active plan                                                                                                                  | Status |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------ |
| D1             | (this audit — codex doc, shipped)                                                                                            | done   |
| D3, D2-cleanup | [`issues/defi_code_codex_drift_2026_05_27`](../../active/issues/defi_code_codex_drift_2026_05_27.md)                         | active |
| D6–D13         | [`issues/defi_code_codex_drift_2026_05_27`](../../active/issues/defi_code_codex_drift_2026_05_27.md) (expanded this session) | active |

## Archive condition

Archives when all gap items above are `- [x]` in `plans/active/issues/defi_code_codex_drift_2026_05_27.md` (or their
successor active plans), and the code-side items are provably shipped (commit SHA) after the backfill completes.
