---
type: audit-result
epic: defi_master
instructions_ref: plans/audit/instructions/defi_master_audit_instructions.md
auditor: harsh
date: 2026-05-27
status: complete
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

## Gap items (ready to paste / tracked in the active issue plan)

- [x] [DOC] P2. D1 — catalog data_type names renamed to canonical + staleness banner — `pm@<this commit>` — parent_epic:
      defi_master
- [ ] [DOC] P2. D6/D12 — reconcile `defi-data-types-catalog.md`: add the ~8–13 missing data_types + fix
      `oracle_prices`/`lending_indices` sources — parent_epic: defi_master
- [ ] [DOC] P2. D9/D11 — update `defi-venue-protocol-catalogue.md`: add
      EULER_V2/BENQI/VENUS/MARGINFI/SOLEND/SOLAYER/PICASSO/CAMBRIAN; flag TRADER_JOE/VELODROME/GMX-AVALANCHE
      empty/deprecated — parent_epic: defi_master
- [ ] [CODE] P2. **DEFERRED-UNTIL-PIPELINE-DONE** D3 — UAC `needs_candle_processing("lending_indices")=False` + delete
      dead `DefiLendingIndicesAdapter` + fix `app/adapters/__init__.py` comment — parent_epic: defi_master
- [ ] [CODE] P3. **DEFERRED + FOR-DECISION** D7 — remove `bloxroute` relay URLs from `mev_events_handler.py` if covered
      by removed-providers rule (operator call); delete stale `mev_events_handler.py.bak` regardless — parent_epic:
      defi_master
- [ ] [CODE] P3. **DEFERRED + FOR-DECISION** D8 — Starknet `infura_compatible` template: keep+rename/document or remove;
      drop the `gas_fee_handler.py:78` infura comment — parent_epic: defi_master
- [ ] [CODE] P2. **DEFERRED-UNTIL-PIPELINE-DONE** D10 — RADIANT: add `PROTOCOL_CAPABILITIES`+`SUBGRAPH_IDS` or downgrade
      from `DEFI_VENUE_PHASE=live` — parent_epic: defi_master
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
