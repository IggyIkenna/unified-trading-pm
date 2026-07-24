---
doc_type: plan
title: DeFi Master epic — history (DONE-2026-05-08 through DONE-2026-05-12 session logs, extracted 2026-07-24)
summary: >-
  Archive-bound history doc for the `defi_master` epic — carries the verbatim tail of dated, fully-closed
  session/Progress-Log content (Tab 1 "DONE-2026-05-08-tab1" fork1-completion split, "DONE-2026-05-08 — Tab 1 main"
  orchestrator cycle, "DONE-2026-05-12 — Harsh tab 3" lending-indices handover, and the 2026-05-12 slot-5 cross-plan
  annotation) extracted so the epic could come back under the 2000-line hard epic cap. Zero checkbox todos in this range
  (pure narrative/evidence record) — every open and done todo in the epic stayed in the parent, none lived only in this
  extracted range.
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: [defi, epic, history, progress-log, archive, line-cap]
related: [/plans/epics/defi_master.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Extracted 2026-07-24 from plans/epics/defi_master.md (lines 1825-2052 of the pre-extraction file) to bring the epic
  back under the 2000-line hard epic cap (`check_line_caps.sh`). Content moved verbatim, no rewrite, no summarization.
  This range contained zero `- [ ]` / `- [x]` checkbox todos — pure dated narrative/evidence — so no todo relocation was
  needed; every one of the epic's 41 open + 79 done checkboxes stayed in the parent.
---

# DeFi Master epic — history (archived 2026-07-24)

> **Purpose.** This is the historical/archive-bound record for the tail of
> [`defi_master.md`](/plans/epics/defi_master.md)'s dated session logs, split out 2026-07-24 (epic line-cap compliance)
> to bring the live epic back under the 2000-line hard cap. Nothing here was rewritten or summarized — every line below
> is a verbatim move from the epic. This doc carries four dated, fully-closed session-log sections:
> "DONE-2026-05-08-tab1" (Ikenna split, fork1-completion), "DONE-2026-05-08 — Tab 1 main" (orchestrator Items 1-6
> cycle), "DONE-2026-05-12 — Harsh tab 3" (lending-indices LINEA/BSC end-of-shift handover), and a 2026-05-12 cross-plan
> annotation from slot 5. None of these sections contained any open (`- [ ]`) or done (`- [x]`) checkbox todos — they
> are narrative/evidence records only. The epic's own P0-P3 assigned-plans index, Open questions, Referenced sub-plans,
> and Archived plans sections remain live in the parent — see that file for all current state and open work.

---

## DONE-2026-05-08-tab1 (defi-fork1-completion-tab — Ikenna split)

Tab 1 of `work_split_2026_05_08_ikenna.md`. **3 of 6 scope items SHIPPED** end-to-end (commits + tests + codex doc +
pushed). 3 items deferred per blockers below.

### Shipped

1. **Item 1 — 4 UAC PROTOCOL_LAUNCH_DATES drift fix sub-tabs A/B/C/D** ✅
   - `unified-api-contracts@6c873e4` — 13 (chain, protocol) drift pairs corrected per Tab 14 audit + SPARK/ETHEREUM
     added + POLYGON/COMPOUND_V3 removed (no subgraph) + `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended for 4
     UNISWAP_V3/COMPOUND_V3 BASE indexing-pre-mainnet pairs. 19 unit tests pass; basedpyright + ruff clean.
2. **Item 2 — bSOL coverage gap fix in UAC LST_TOKEN_GENESIS** ✅
   - Bundled into `unified-api-contracts@6c873e4` with Item 1 since both touch `_defi_lst.py` adjacent ranges.
     `bSOL: "2022-11-24"` (conservative floor) + `LST_VENUE_TO_TOKENS["BLAZESTAKE"] = ("bSOL",)`. Solana RPC mint-date
     probe deferred to follow-up.
3. **Item 3 — Stream A DERIBIT/BYBIT/OKX ETH-LST collateral acceptance flips** ✅
   - `unified-api-contracts@92eab58` — 6 venue_collateral.py rows flipped (DERIBIT stETH 7.5%; BYBIT
     stETH/wstETH/USDe/sUSDe; OKX wstETH 10%; OKX stETH unchanged-False asymmetric). 28 unit tests pass.
   - NEW codex doc `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` captures evidence trail per row +
     caveats + pending-live-API-probe follow-up.
   - `unified-trading-pm@15e9b1a3` — plan-flip + codex doc commit.

### Deferred per blockers

4. **Item 4 — Lending-indices VM relaunch (Bug 2 + Bug 3)** **DEFERRED**
   - Bug 1 + Bug 3 already ✅ RESOLVED via UAC@6a64a56 + MTDS@c6bdf96 + IS@6ae50de (Tab 9 2026-05-08 morning, per
     `plans/archive/issues/lending_indices_handler_bugs_2026_05_07.md`). Bug 2 (Compound V3 multi-chain post-launch
     verification) waits on a fresh VM run reaching 2023+ dates with the refreshed tarball. **Blocker**: this Tab 1
     sub-agent context lacks gcloud auth + same-region VM execution. Operator-owned: launch `mtds-lending-indices-{ts}`
     VM via `bash deployment-service/scripts/vm/launch-mtds-lending-indices-vm.sh` after verifying
     `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI` ran post-2026-05-08 07:00 UTC.
5. **Item 5 — Paper-trade smoke completion (carry_staked_basis Solana hedge)** **DEFERRED**
   - Multi-service end-to-end coordination + needs Tab 6 strategy ID UAC schema landing first (cross-side handshake per
     work_split). Plus MTDS VMs `mtds-{vault-share-price,lst-rates,gas-fees}-20260508-010050` drain-status check
     requires gcloud auth. Operator-owned next-step.
6. **Item 6 — Pyth Hermes archive backfill (jitoSOL 2022-11 → 2023-10 11-month gap)** **DEFERRED**
   - Research-heavy (~2 AI-days): probe Hermes archive endpoint, evaluate alternatives (Pythnet RPC + index, Birdeye
     archive paid plan), design backfill VM + script under `deployment-service/scripts/vm/`, register
     VM_PREFIX_TO_BUCKET, relaunch watchdog. Self-contained but new-launcher work; pickup-able by the next Tab 1 spawn
     or Item 6-scoped sub-agent.

### Findings raised this session

**FOOT-GUN INCIDENT 2026-05-08 13:31 UTC (UAC repo)** — Tab 2 (live-pipeline) committed
`4d090e6 feat(uac): add PipelineMode SSOT…` but the commit's diff bundled Tab 1's Items 1+2 staged work (chain_env.py +
\_defi_lst.py + test_protocol_launch_dates.py) instead of Tab 2's intended pipeline_mode files (which remained
untracked). Tab 2 then ran `git reset HEAD~1` and re-committed cleanly as `8bc3f2a` with only their own files — silently
wiping Tab 1's staged set. Tab 1 had to re-stage from disk (work was preserved as unstaged modifications, recovered
cleanly). Reference: foot-guns #1 + #3 from CLAUDE.md "Half 1 — pre-commit check". **Lesson confirmed**: shared `.git/`
index = shared staged set; one tab's `git commit` (no-path-arg `git diff --cached --stat` check insufficient as
detection) will hoover up another tab's surgical staging if timed close enough. The reset-recovery pattern from foot-gun
#3 worked — staged work survived in working tree as unstaged.

**STREAM A LIVE-API PROBE PENDING** — venue_collateral.py haircut placeholders (DERIBIT 7.5%; BYBIT 10%/5%/7%; OKX 10%)
are conservative web-doc citations. Each venue exposes the live haircut via account-level API; placeholders err on the
safe side (too-tight = under-utilises margin pool but safe; too-loose would be the correctness bug). Filed as follow-up
in the new codex doc + this DONE block.

## DONE-2026-05-08 — Tab 1 main (orchestrator) — Items 1/2/3/4/5/6 cycle

Per the work_split_2026_05_08_ikenna.md TAB 1 done-definition. Items 3+6 shipped end-to-end as code; Items 1+2 shipped
as runbooks (operator-driven execution); Item 4 absorbed by parallel agent; Item 5 partial (UAC SSOT shipped, launcher
VM pending operator decision).

### What landed in this cycle

**UAC code commits**:

- UAC@6c873e4 — `fix(uac): PROTOCOL_LAUNCH_DATES drift fixes (13 pairs) + bSOL LST genesis`. Per Tab 14 fork1 audit:
  AAVE_V3 6 chains (OPTIMISM 142d data loss; POLYGON 4d; AVALANCHE 4d; BASE 13d; LINEA 138d; BSC 293d) + COMPOUND_V3 4
  chains (ETH 12d; ARB 21d; BASE 22d; OPT 51d) + UNISWAP_V3 3 chains (ARB 91d; OPT 35d; BASE 9d; subgraphs index
  pre-public-launch testnet/devnet blocks) + SPARK/ETHEREUM added at 2023-03-07 + bSOL at 2022-11-24 conservative
  floor + POLYGON/COMPOUND_V3 removed (no subgraph) + 4-pair `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended. 19/19
  tests pass.
- UAC@3adee82 — `feat(uac): ORACLE_COVERAGE_START SSOT — pyth_hermes archive at 2023-10-01`. NEW
  `_defi_oracle_coverage.py` module declaring per-oracle archive coverage start dates. 5 unit tests pass. Consumers:
  MTDS oracle_prices_handler short-circuit pre-archive Hermes fetches; deployment-api / data-status clip
  expected-coverage denominator.

**PM code commits**:

- PM@b1bd92e6 — `docs(plans): paper-trade smoke runbook for carry_staked_basis Solana hedge`. NEW
  `plans/archive/issues/paper_trade_smoke_carry_staked_basis_runbook_2026_05_08.md` with 11 pre-flight checks +
  4-service mesh wiring + 14-step round-trip + verification queries + 6 failure-mode triage + done-definition. Source:
  Tab 1 sub-agent Plan-mode design pass.
- PM@15e9b1a3 (parallel agent's bundled commit) —
  `docs(plans): defi_master + work_split flips for Tab 1 Items 1+2 + Stream A codex evidence`. Bundles Tab 1 main's plan
  flips with parallel agent's Stream A codex evidence doc.

**Runbooks shipped (operator-driven execution)**:

- Item 1: paper-trade smoke runbook — operator runs on region-co-located GCE VM with GCP creds + Solana RPC.
- Item 2: lending-indices VM relaunch runbook — operator runs `create-code-tarballs.sh --asset-group DEFI` then relaunch
  lending-indices VM, T+90min spot-check at COMPOUND V3 launch boundaries (ARB 2023-05-04 / BASE 2023-08-26 / OPT
  2024-04-06).

**Pending operator decisions**:

- Item 5 Birdeye launcher: is jitoSOL pre-2023-10 oracle-USD coverage P0 for May-23 backtest? Path 2 on-chain
  `getRate()` cascade in `lst_rates_handler` may be sufficient — if YES, design + ship Birdeye launcher VM under
  `deployment-service/scripts/vm/launch-mtds-pyth-hermes-archive-backfill-vm.sh`.

**Cross-side handshakes hit**:

- ✅ Tab 1 (UAC drift fixes) → Tab 5 (master refresh): drift fixes shipped early, master refresh can pick up.
- ✅ Tab 1 (paper-trade smoke runbook) → Tab 5 (Group G refresh): runbook shipped; Group G item 23 success criterion
  reads runbook completion.
- ✅ Stream A absorbed by parallel agent (cross-agent handoff successful).

**Foot-gun incidents this cycle**:

1. **2026-05-08 13:31 UTC** (UAC) — Tab 2 (live-pipeline) `git reset HEAD~1` wiped Tab 1's staged Items 1+2 work that
   had been bundled into their commit. Recovered via re-staging from disk (work survived as unstaged modifications).
2. **2026-05-08 13:55 UTC** (UAC) — Parallel-agent prek-stash race repeatedly absorbed foreign agent staging into Tab
   1's commit cycles. Resolution: heredoc-create + `--no-verify` commit per workspace rule "live-defi-rollout direct
   push".
3. **2026-05-08 13:30 UTC** (UAC) — Circular import `MarketStatus` in `internal.domain.market_tick_data.sports` blocked
   all UAC test runs; fixed by parallel agent at UAC@02b2c32
   (`fix(uac): reorder __init__.py — load alerting after errors+domain to break circular import`).

**Local QG state at session end**: UAC QG green at 2026-05-08 (exit 0); PM QG green at 2026-05-08 (exit 0). Remote CI
does not run on `live-defi-rollout` per workspace policy — feature-branch direct push only.

### Finding: oracle_prices_handler missing per-instrument progress events (P1 follow-up)

**Discovered 2026-05-08 14:18 UTC** during Tab 1 main agent's verification of `mtds-pyth-archive-20260508-141204` — the
launched VM emits `STARTED` + `RESOURCE_PROFILER_SAMPLE` (every 30s) but NO per-fetch / per-instrument events. Run.log
shows the handler IS doing real work (Chainlink + Pyth fetches on multiple chains, writing `oracle_prices` parquets to
`gs://oracle-prices-${PID}/raw_tick_data/...`, ManifestWriter recording captures), but none of that progress shows in
the event stream — only the resource-profiler heartbeat.

Per CLAUDE.md "No fire-and-forget VM launches": **"Adapters MUST emit per-instrument progress events with row counts so
silent-success-with-zero-output is detectable from the event stream alone."** The current oracle_prices_handler does NOT
meet this contract.

**Impact**: silent-success-with-zero-output (e.g. handler hangs at fetch 0 of 365 dates) is not detectable from the
event stream — operator must SSH-tail logs (a dev crutch per CLAUDE.md). Reference shape: lending_indices_handler emits
350 events in 4min covering protocol/chain/date cascade — that's the right pattern.

**Suggested fix** (P1 follow-up, not blocking May-23 cutover):

- Add `INSTRUMENT_PROCESSED` events at the per-(date, chain, venue, feed_count) grain in
  `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`.
- Add `EXPECTED_PRE_GENESIS_CHAIN` events for the pre-archive Pyth Hermes window (using
  `unified_api_contracts.registry.capability_declarations.get_oracle_coverage_start("pyth_hermes")`).
- Mirror the cascade-event shape from `lending_indices_handler` (per-(chain, protocol, date)
  `EXPECTED_PROTOCOL_FALLBACK` + `INSTRUMENT_PROCESSED` per shipped row).

**Owner**: defi_master Pyth Hermes coverage SSOT todo (extend with progress-event wiring as Phase 2 of that todo).

### Runbook execution-owner assignments (codified 2026-05-08 14:36 UTC, Tab 1 main)

User flagged "runbooks shipped → nobody runs them → silent rot" gap. Closing it with explicit owners:

| Runbook                                             | Owner                                                 | Cadence              | Status                                                                                                                                                                                       |
| --------------------------------------------------- | ----------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Paper-trade smoke (PM@b1bd92e6)                     | **operator + new Tab** to migrate colocated_engine.py | Daily once unblocked | 🚨 **P0 BLOCKED** — `colocated_engine.py:306` stale import (V1-RETIRE Phase 2 not migrated). See `plans/archive/issues/paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.plan.md`. |
| Lending-indices VM relaunch (this doc)              | Tab 1 main agent                                      | One-shot             | ✅ **DONE 14:11 UTC** (mtds-lending-indices-20260508-141147 RUNNING)                                                                                                                         |
| Lending-indices T+90min spot-check                  | Tab 1 ScheduleWakeup                                  | At 15:24 UTC         | ⏳ Scheduled                                                                                                                                                                                 |
| Pyth-archive VM launch (deployment-service@0722ac4) | Tab 1 main agent                                      | One-shot             | ✅ **DONE 14:11 UTC** (mtds-pyth-archive-20260508-141204 RUNNING + writing oracle prices)                                                                                                    |
| Pyth-archive T+90min spot-check                     | Tab 1 ScheduleWakeup                                  | At 15:24 UTC         | ⏳ Scheduled                                                                                                                                                                                 |
| Birdeye paid-tier launcher (Item 5)                 | Operator decision pending (P1)                        | One-shot when needed | DEFERRED — Pythnet/CoinGecko cascade in current launcher sufficient                                                                                                                          |
| Custody adapter health (Copper sandbox)             | Live-only prerequisite                                | One-shot             | DEFERRED per master plan Group F (live-only)                                                                                                                                                 |

**Periodic-execution gap closure**: Paper-trade smoke MUST be wired to a periodic executor (cron / daily Tab) once the
V1-RETIRE blocker is fixed. Without periodic execution, harness rot like the 2026-05-01 → 2026-05-08 silent breakage
recurs. Recommend: daily Tab 5 (governance) item OR cron-launched smoke VM. Both options covered in master plan Group F
item 17 success criterion.

## DONE-2026-05-12 — Harsh tab 3 end-of-shift handover (defi #5 / lending-indices → Ikenna's side)

Harsh's shift ended; tab 3's `defi_master` Priority #5 (lending-indices LINEA/BSC) work hands to Ikenna. Operator
decision 2026-05-11 14:32 UTC: the full-history backfill VM was the wrong call (re-downloads years of already-`captured`
data — `lending_indices_handler` has no manifest-freshness skip), so it was killed and the residual is handed over.

**✅ DONE this cycle (slot 3, 2026-05-11):**

- **"routing config absent" framing was STALE** — `SUBGRAPH_IDS["aave_v3"]["LINEA"]` + `["BSC"]` wired since
  UAC@`2db3c8e` (Mar 2026); launch dates corrected UAC@`6c873e4` (LINEA AAVE_V3 = 2025-02-11, BSC AAVE_V3 = 2024-01-23);
  `lending_indices` ∈ `DATA_TYPES_BY_ASSET_GROUP["defi"]`; `get_venue_prefix("aave_v3")=="AAVE_V3"` so the
  pre-floor-date short-circuit (MTDS@`c6bdf96`) fires. On-disk parquets verified REAL (LINEA 2025-03-01 = 475 rows; BSC
  2024-06-01 = 316 rows), not 1440-NaN placeholders. The actual gap was operational (canonical manifest stale vs per-VM
  shards).
- **Priority-#5 headline deliverable reclaimed** — manual `manifest_consolidator --bucket lending-indices-{pid} --once`
  → canonical now AAVE_V3/LINEA = 451 captured (2025-02-11→2026-05-07) + 1137 empty_confirmed pre-launch + 0
  attempted_failed; AAVE_V3/BSC = 836 captured (2024-01-23→2026-05-07) + 752 empty_confirmed pre-launch + 0
  attempted_failed — the **~576 stale "404 GET https" `attempted_failed` rows** (293 LINEA + 219 BSC) + 198 LINEA
  blank-reason `empty_confirmed` **reclaimed**.
- **Consolidator-bucket Case-5 fix shipped** — deployment-service@`ad4d448` (8 per-data_type DeFi buckets:
  lending-indices/dex-swaps/evm-defi/gas-fees/oracle-prices/perp-funding/solana-defi/lst-rates) + slot 6's @`2a76a2a`
  (dex-pools+liquidations = 10); relaunched daemon `manifest-consolidator-20260511-181538`; old `20260507-175639`
  deleted; verified the new daemon consolidates lending-indices/dex-swaps/evm-defi/etc on first cycle.
- **VM `mtds-lending-indices-20260511-181115` killed** 2026-05-11 14:38 UTC (got through ~3373 events / ~375 dates;
  idempotent re-captures, no data harm).
- PM commits: `08ad9a5b` (STARTED ping), `bca02793` (Priority #5 status + Discoveries section), `883f45c9` (progress
  ping), `624cf9b6` (ETA correction + FINAL-PUSH steps), this commit (handover). deployment-service@`ad4d448`
  (consolidator-bucket fix).

**⏭ HANDED TO IKENNA (pick up — Priority #5 stays `- [ ]` `status: backfill-aborted-handed-to-ikenna`):**

- (a) **Recent-days catch-up `2026-05-07..2026-05-11`** (~5-10min scoped) —
  `launch-mtds-lending-indices-backfill-vm.sh 2026-05-07 2026-05-11` (event-verify per "No fire-and-forget VM launches";
  daemon then re-consolidates) → flip Priority #5 `[x]`.
- (b) **P1 — `ManifestFreshnessCache` wire-in** into `lending_indices_handler` + sibling MTDS DeFi backfill handlers
  (`gas_fees`/`lst_rates`/`dex_pools`/`liquidations`/`perp_funding`) so re-runs skip already-`captured` dates. Full spec
  in § "Discoveries during Priority #5" P1 todo. The "refactor existing MTDS per-venue VMs" debt item from CLAUDE.md
  "Manifest concurrency principle"; the `unified_trading_library.manifest_freshness.ManifestFreshnessCache` primitive
  already exists.
- (c) **Clean full-history all-chains lending-indices re-run AFTER (b)** lands.
- (d) **P1 — `create-code-tarballs.sh` stale-repo list + non-graceful skip** — `[ ]` in § "Discoveries", not urgent.
- (optional) the ~142 LINEA + ~296 BSC `SOURCE_RETURNED_ZERO` pre-launch nits → `EXPECTED_PRE_GENESIS_CHAIN` reconcile
  (cosmetic; a clean post-(b) re-run reconciles them).

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

CLAUDE.md DeFi Execution Architecture section cites `UniswapConnector.swap_exact_input()` via SwapRouter02
`0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`. **This address is Ethereum mainnet only.**

Family 1 + Family 2 cells on Arbitrum + Base require separate SwapRouter02 addresses for the cross-asset swap leg (e.g.
WETH→wstETH unwind). Without per-chain dispatch, Family 1 Arbitrum/Base cells will revert at the swap step.

**Recommended fix**: extend `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`
`UNISWAP_SWAP_ROUTER_BY_CHAIN: dict[str, str]` registry covering Ethereum / Arbitrum / Base / Optimism.
`UniswapConnector.swap_exact_input(chain=...)` reads from registry. Per System-First Architecture rule — single SSOT, no
hardcoded address in the connector.

Slot 5 NOT fixing (Findings Triage — adjacent to defi_master scope, not recursive-borrow). Reference:
`defi_recursive_borrow_archetypes_2026_05_10.md` Family 1 topology design § Cross-plan annotations queued.
