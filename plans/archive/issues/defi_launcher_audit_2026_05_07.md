---
doc_type: issue
title: DeFi launcher audit — answers to the 3 operator-blocking Qs from defi_master 2026-05-07
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-07
author: harsh
source:
  [
    plans/active/defi_master_2026_05_07.md (commit b8edd01 PLANNING-CRITICAL block),
    "market-tick-data-service/market_tick_data_service/cli/handlers/{lending_indices,vault_share_price,lst_rates,gas_fee}_handler.py",
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    deployment-service/scripts/vm/launch-mtds-*-backfill-vm.sh,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# DeFi launcher audit — answers to the 3 operator-blocking Qs

> **Cross-ref 2026-05-07: writegate Phase 3.D.4 expected-universe `--apply-write` COMPLETE on all 5 asset_groups +
> CONSOLIDATOR MERGE LANDED (PM@79e47874 + PM@341bb285).** 1,455,901 rows written + merged into canonical 18:07-18:14
> UTC: TradFi 35,033 + Sports 13,176 + CeFi 119,152 (real impl per UAC@ac218dc + instruments-service@d1c9928, no longer
> a stub) + Prediction 2,280 (real impl) + DeFi 1,286,260 (cap raised 100k → 1M → 5M for this run via
> deployment-service@38b7a58 launcher pass-through). Consolidator P0 (`ArrowTypeError` on `instrument_count`) that
> briefly blocked tradfi / defi / prediction was resolved at PM@341bb285 (script-side root cause + 4 in-place shard
> fixes). Q3's denominator divergence + the data-status drilldown plan's "open drifts" stop biasing the rollup as soon
> as the rollup blob refreshes. Detail in
> [`../writegate_honest_coverage_endtoend_2026_05_06.md`](../writegate_honest_coverage_endtoend_2026_05_06.md) § Phase
> 3.D.4.

The 2026-05-07 PM commit `b8edd01` (planning-critical correction in `defi_master_2026_05_07.md`) raised three
operator-actionable questions to Ikenna gating next-stage launches. This doc answers each from code-side evidence, no VM
launches required.

**Source diagnostic (parallel agent, 2026-05-07):** Arbitrum/Base/Polygon at 0% on the canonical DeFi manifest; Ethereum
forward-poll stopped 2026-01-23 for most data_types; `launch-mtds-perp-funding-backfill-vm.sh` referenced in CLAUDE.md
but reportedly missing.

---

## Q1 (referenced) — was the original "60%" coverage claim reading a different bucket?

**Out of scope of this audit** — would need to read the deployment-api `_data_status_rollup_worker` and compare the
rollup it produces against the canonical manifest the parallel agent queried. Flag stays open. The parallel agent's
diagnostic at `gs://market-data-tick-defi-central-element-323112/_index/availability_index.parquet` is the canonical
source; whatever the rollup said previously is suspect.

---

## Q2 — are MTDS DeFi launchers Ethereum-only?

**Answer: NO. The handlers are multi-chain by design. The 0% Arb/Base/Polygon coverage is a different problem.**

### Per-handler evidence

| Handler                                                                                                                                         | Multi-chain?                                              | Source of chain list                                                  | Default chains today                                                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| [`gas_fee_handler.py:46`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/gas_fee_handler.py#L46)                       | ✅ Yes                                                    | hardcoded `DEFAULT_GAS_FEE_CHAINS`                                    | 14 chains: ETHEREUM, OPTIMISM, BSC, POLYGON, BASE, ARBITRUM, AVALANCHE, LINEA + 6 Tier 3                                              |
| [`lending_indices_handler.py:253`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py#L253)     | ✅ Yes                                                    | `get_supported_chains_for_protocol(protocol)` from UAC `SUBGRAPH_IDS` | AAVE_V3 → 8 chains (ETH, ARB, OPT, POL, AVAX, BASE, LINEA, BSC); COMPOUND_V3 → 4; MORPHO → 2 (ETH, BASE)                              |
| [`vault_share_price_handler.py:234`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/vault_share_price_handler.py#L234) | ⚠ Multi-chain capable but Ethereum-skewed by **registry** | `_VAULTS` registry                                                    | 9 ETHEREUM entries + sparse non-ETH (MORPHOVAULTS×2, MAKER, FRAX, ETHENA — these last 4 are protocol names not chains; need re-check) |
| [`lst_rates_handler.py:251,288,301,334`](../../../market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py#L251)     | ❌ No (by design)                                         | hardcoded `chain="ETHEREUM"` + Solana side-path for Marinade          | ETHEREUM (13 EVM LSTs) + SOLANA (Marinade) only — LSTs canonically live on these two chains                                           |

### Conclusion

The multi-chain capability **exists** in code. The `lending_indices` handler will iterate 8 chains for AAVE_V3,
including Arb/Base/Polygon, when the launcher fires it. So why do those chains have 0 rows on the manifest?

**Most likely answer: the lending-indices launcher hasn't been run with full-history scope yet.** The parallel agent's
diagnostic noted `mtds-lending-indices-20260507-140418` was launched 2026-05-07 14:04 IST with full history — that's in
flight RIGHT NOW (ETA 17:00-19:00 IST per their note). When that VM completes, Arb/Base/Polygon manifest rows for
AAVE_V3 / COMPOUND_V3 / MORPHO should populate.

**What would still need separate launches** to reach full DeFi coverage:

- `gas_fee_handler` for the same Arb/Base/Polygon chains (hits 14 chains by default — likely needs a launcher run)
- Per-chain DEX subgraph coverage (uniswap_v3 / balancer / curve etc. — these are NOT in the 4 launchers I audited; they
  flow via a different path I haven't traced yet)

**Action for Ikenna:**

1. Wait for `mtds-lending-indices-20260507-140418` to complete; re-check manifest. If Arb/Base/Polygon rows appear,
   chain-iteration is confirmed working and the original "0%" was simply "never invoked."
2. If those rows DON'T appear after the VM completes successfully, that's a real silent-no-op bug — drop into the
   handler logs or the orchestrator's `_should_skip_shard` to find where the chain is being filtered.

---

## Q3 — Ethereum forward-poll stopped 2026-01-23: paused or broken?

**Answer: launcher exists; no VM running; appears to be a missing-cron / never-relaunched situation, not a code
breakage.**

### Evidence

- [`launch-defi-forward-poll.sh`](../../../deployment-service/scripts/vm/launch-defi-forward-poll.sh) **exists** in the
  workspace.
- `gcloud compute instances list --filter='name~"^defi-fwd|^mtds-.*fwd"'` returns **empty** — no defi forward-poll VM
  currently running.
- Last MTDS lending-handler commit `a2d464c` (2026-05-06) was 4 months after the 2026-01-23 forward-poll cessation —
  whatever caused the stop happened well before any recent code change.

### Most-likely scenario

The forward-poll VM either auto-shut on completion of its window and was never re-launched (no operator action), OR a
crash/preemption took it down and no alert fired (operator missed it). Either way, **relaunching the launcher should
restore forward-poll** — no code fix needed unless the relaunch itself fails, in which case fall through to log
inspection.

**Action for Ikenna:**

1. Read `gcloud compute instances list --filter='name~"^defi-fwd"' --include-deleted` if available, or scan
   `gs://deployment-scripts-{pid}/vm-logs/defi-fwd-*/run.log` for the most recent termination event — confirm clean
   shutdown vs crash.
2. Relaunch with `bash deployment-service/scripts/vm/launch-defi-forward-poll.sh`; verify STARTED event within 90s per
   the no-fire-and-forget rule.
3. If the freshly-launched VM stalls or fails, then fall back to bug investigation — but as of this audit, there's no
   evidence of broken code.

**Caveat:** I didn't verify the launcher itself is current vs the post-2026-01-23 codebase. Worth a glance before
relaunch to confirm flags are still valid.

---

## Missing-launcher question — `launch-mtds-perp-funding-backfill-vm.sh`

**Answer: confirmed missing. Has NEVER existed in `deployment-service` git history.**

### Evidence

- `ls deployment-service/scripts/vm/ | grep -iE "perp-funding|funding"` → empty.
- `find . -name "launch*perp-funding*" -o -name "launch*funding*backfill*"` (workspace-wide, excluding `.venv` /
  `node_modules`) → empty.
- `git log --all --diff-filter=D --oneline -- 'scripts/vm/launch-mtds-perp-funding-backfill-vm.sh'` → empty (never
  existed-then-deleted).
- `git log --all --oneline -- 'scripts/vm/launch-mtds-perp-funding-backfill-vm.sh'` → empty (never authored at this
  path).

### Where the perp-funding data IS captured today

Per `carry_staked_basis_structure_axis_2026_05_04` plan archive, perp funding flows through TWO existing paths (neither
named `launch-mtds-perp-funding-`):

1. **Tardis derivative_ticker capture** — `derivative_ticker` data carries `funding_rate` + `open_interest` +
   `mark_price` + `index_price` via Tardis. 2026-05-05 audit confirmed coverage on BINANCE-FUTURES, BYBIT, OKX-SWAP,
   DERIBIT, HYPERLIQUID, BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES. Captured by the standard CeFi MTDS backfill
   flow.
2. **Native HYPERLIQUID + GMX funding** — `gs://perp-funding-{pid}/perp_funding/{hyperliquid,gmx}/` — captured by
   features-delta-one VMs (`features-delta-one-defi-backfill-20260505-115343` etc.).

So the **functional perp-funding coverage exists** via Tardis (CeFi) + features-delta-one (DeFi-native). The referenced
`launch-mtds-perp-funding-backfill-vm.sh` may be a stale CLAUDE.md reference predating the consolidation, or a
planned-but-never-authored launcher.

### Implication for `leveraged_funding_arb`

The second cutover archetype (`leveraged_funding_arb`) needs cross-venue funding-rate spreads. Per CLAUDE.md:

> `mtds-perp-funding-` referenced in CLAUDE.md "Singleton-locked launchers" + "VM Naming Convention" sections

The data flow already exists (Tardis + features-delta-one). The missing launcher might just be a **CLAUDE.md reference
correction** — not a blocker for `leveraged_funding_arb`, since the underlying data is being captured by other
launchers.

**Action for Ikenna:**

1. **Decide:** is the missing launcher a real gap (need to author it for some specific MTDS perp-funding data path the
   existing flows don't cover), OR is it a stale CLAUDE.md reference that should be removed?
2. If real gap: scope what data the new launcher would capture that Tardis + features-delta-one don't already cover.
3. If stale: remove the reference from CLAUDE.md `§ Singleton-locked launchers` + `§ VM Naming Convention`.

---

## Summary — recommended operator decisions

| Q                             | Status          | Recommended action                                                                                                                                                                          |
| ----------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Q1 — original 60% claim       | OPEN            | Audit `_data_status_rollup_worker` vs canonical manifest separately — out of scope here                                                                                                     |
| Q2 — multi-chain launchers    | RESOLVED        | Handlers ARE multi-chain. Wait for in-flight `mtds-lending-indices-20260507-140418`; if Arb/Base/Polygon don't populate after rc=0, then real bug — drop into orchestrator chain-skip logic |
| Q3 — Ethereum forward-poll    | LIKELY-RELAUNCH | Re-invoke `launch-defi-forward-poll.sh` per no-fire-and-forget protocol; only investigate if the freshly-launched VM stalls                                                                 |
| Missing perp-funding launcher | CLARIFY         | Decide: real gap or stale CLAUDE.md reference. Functional coverage already exists via Tardis + features-delta-one                                                                           |

---

## What this audit did NOT do

- Verify the in-flight `mtds-lending-indices-20260507-140418` is actually emitting per-chain manifest rows (would need
  to read the GCS event stream + manifest delta). Recommend ops check at ETA.
- Trace the per-chain DEX subgraph capture path (uniswap_v3 / balancer / curve coverage on Arb/Base/Polygon — not in the
  4 audited launchers).
- Inspect `_data_status_rollup_worker` (deployment-api) for the rollup-vs-manifest discrepancy that produced the
  original "60%" claim.
- Re-launch the defi forward-poll VM (operator decision per no-fire-and-forget rule + cost-aware launching).

---

## 2026-05-07 PM follow-up — data-status drilldown breakdown + truncation audit (Claude session)

**Operator finding 2026-05-07:** the data-status panel shows different coverage % at the top-level vs in the breakdowns,
AND the breakdowns appear to display only 20 or 50 shards rather than the full set. Audit answers each from code-side
evidence:

### Q1-redux: total-vs-breakdown discrepancy (RESOLVED — two code paths, two denominators)

The top-level coverage % and the drill-down breakdown coverage % are **served by different code paths reading different
sources** with **different denominators**:

| Layer                    | Code path                                                                                                      | Source                                                                            | Denominator                                                                                                                                                                                      |
| ------------------------ | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Top-level (panel header) | [`_slice_rollup_to_window`](../../../../deployment-api/deployment_api/services/data_status_service.py)         | Offline rollup blob (gzipped JSON in `gs://...uts-shared-deployment-api-rollup/`) | **Pre-computed expected universe** (calendar-clipped per `venue_trading_calendar`, source-coverage-clipped per UAC `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` / `CHAIN_GENESIS_DATES`) |
| Drill-down breakdown     | [`get_hierarchical_drilldown`](../../../../deployment-api/deployment_api/services/data_status_hierarchical.py) | Live `read_availability_index(bucket)` — manifest parquet                         | **Manifest row count** (only what the writer physically recorded)                                                                                                                                |

**Where they diverge:** any `(shard_key, day)` in the rollup's expected universe that has **no manifest row at all**
(not `captured`, not `empty_confirmed`, not `attempted_failed` — just absent) gets counted in the rollup denominator but
missed by the drill-down. Today this happens for:

- DeFi pre-genesis chain dates (ARBITRUM pre-2021-08-31, BASE pre-2023-07-13, etc.) where the orchestrator pre-skips
  with no row written.
- Sports pre-`SOURCE_COVERAGE_START` dates per source.
- Paused-league windows in `KNOWN_COVERAGE_GAPS`.
- Calendar non-trading days (TradFi holidays / weekends) where the orchestrator pre-skips.

**Active fix path (in flight):** the **writegate-honest-coverage Phase 2.E.2** work
([`writegate_honest_coverage_endtoend_2026_05_06.md`](../writegate_honest_coverage_endtoend_2026_05_06.md)) mandates
`record_expected_empty(reason=EXPECTED_*)` for every calendar-pre-skip case, so every expected `(shard_key, day)` gets a
manifest row. Once that ships across all five asset_groups, both code paths converge on the same denominator. **Until
then the drift is expected.**

Some Phase 2.E.2 work has shipped this session (instruments-service@8b5eca3 TradFi calendar pre-skips +
features-sports@a215e36 post-fetch tagging + UAC@2a970c5 `non_trading_day_reason` SSOT). DeFi pre-genesis + sports
pre-coverage + paused-league cases remain.

### Q2-redux: "20 or 50 shards" truncation (RESOLVED — three caps, one user-facing)

Three actual cap sources, each in a different layer:

| #   | Layer                                 | Symbol                            | Cap          | Where                                                                                                                                                                                            |
| --- | ------------------------------------- | --------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **deployment-service venue-detail**   | `top_instruments: df.head(30)`    | **30**       | [`manifest_reader.py:584`](../../../../deployment-service/deployment_service/cli/utils/manifest_reader.py#L584) — venue detail panel **sample** of instruments                                   |
| 2   | deployment-api per-league detail      | `missing_dates: missing_pf[:50]`  | **50**       | [`data_status_service.py:602`](../../../../deployment-api/deployment_api/services/data_status_service.py#L602) — missing-dates **sample list**, `missing_count` field has the correct full count |
| 3   | deployment-api hierarchical drilldown | `_MAX_CHILDREN_PER_NODE = 10_000` | **10,000**   | [`data_status_hierarchical.py:61`](../../../../deployment-api/deployment_api/services/data_status_hierarchical.py#L61) — defensive ceiling, paginated via `child_offset`/`child_limit`           |
| 4   | deployment-ui drilldown page          | `topPageSize = 200`               | **200/page** | [`HierarchicalShardDrilldown.tsx:70`](../../../../deployment-ui/src/components/HierarchicalShardDrilldown.tsx#L70) — has "Load next N of T remaining" button                                     |

**The cap you're seeing is #1** — venue detail's `top_instruments` is a 30-instrument **sample**, not the full
instrument list. For venues like BINANCE-FUTURES with 5000+ perp instruments, the panel only ever shows the first 30
sorted by `instrument_key`. There's no pagination and no "showing 30 of 5000" label. This pre-dates the hierarchical
drilldown's `child_offset`/`child_limit` shipping.

**Cap #2** (50 missing dates) is just a sample preview — the COUNT (`missing_count`) is correct and used for the
percentage. Not a real coverage issue, just a UI preview truncation.

**Caps #3 + #4** are well-shaped (10k defensive ceiling, 200/page with load-more).

**Already-shipped finding 3** — bundled-type drilldown collapse (`options_chain` / `futures_chain` with empty
`instrument_id`) was fixed by `_coalesce_instrument_id_from_underlying`
([`data_status_hierarchical.py:233`](../../../../deployment-api/deployment_api/services/data_status_hierarchical.py#L233))
— read-time virtualization that promotes `underlying → instrument_id` so bundled rows surface at the per-root level
(BTC, ETH for Deribit options; ESH4, NQH4 for CME futures). No further work needed there.

**In-flight finding 4** — 2.35M-row manifest causing CEFI/DEFI 502s. Per
[deployment-api@5bcea1d4](https://github.com/IggyIkenna/deployment-api/commit/5bcea1d4) handoff: pagination work in
flight on `data_status_hierarchical.py` (`child_offset` / `child_limit` / `_MAX_CHILDREN_PER_NODE=10000` /
underlying-column virtualization) by another agent. Listed in
[`data_status_drilldown_shard_atom_alignment_2026_05_07.md`](../data_status_drilldown_shard_atom_alignment_2026_05_07.md)
Phase 6 + handled by another agent's commit. Don't duplicate.

### Actionable todos — to be added to the existing data-status-drilldown plan

The existing
[`data_status_drilldown_shard_atom_alignment_2026_05_07.md`](../data_status_drilldown_shard_atom_alignment_2026_05_07.md)
covers Phase 6 pagination + bundled-root virtualization. **The audit findings above add three deltas not covered there**
— proposing for inclusion when that plan's owner next touches it (or as a small standalone follow-up plan if the
operator prefers):

- [ ] **[deployment-service]** P1. `manifest_reader.py:584` — replace `df.head(30)` with paginated `top_instruments`:
      add `instrument_offset: int = 0` + `instrument_limit: int | None = None` query params to the venue-detail
      endpoint; default `instrument_limit = 200` (matches drilldown UI page size); return
      `total_instruments_unfiltered: int` so the UI can render "showing N–M of T" + a load-more button. Bump cap from 30
      → 200 (or remove with explicit pagination). Document that this is the venue-detail panel's instrument sample,
      distinct from the hierarchical drilldown's `instrument_id` axis.
- [ ] **[deployment-ui]** P1. `VenueDetailPanel.tsx` — add pagination controls to the `top_instruments` rendering
      ([`VenueDetailPanel.tsx:200-208`](../../../../deployment-ui/src/components/VenueDetailPanel.tsx#L200)). When
      `total_instruments_unfiltered > top_instruments.length`, render "Show more (N remaining)" + count label. Mirror
      the pattern from `HierarchicalShardDrilldown.tsx:218`.
- [ ] **[deployment-api]** P2. `data_status_service.py:602` — `missing_dates: missing_pf[:50]` is fine as a sample
      preview but the UI should label it as "sample of 50 / total N missing" rather than "the missing dates". Pure doc /
      UI label fix, not a behaviour change.
- [x] **[codex]** P1 (shipped PM@372e23aa 2026-05-07). Documented the rollup-vs-drilldown denominator divergence in
      [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
      § "Rollup-vs-drilldown denominator divergence (codified 2026-05-07)". Closure (Half 2 — backward-fill via Phase
      3.D.4 enumerator) tracked in
      [`../writegate_honest_coverage_endtoend_2026_05_06.md`](../writegate_honest_coverage_endtoend_2026_05_06.md) §
      Phase 3.D.4. Scan-only sweep complete 2026-05-07; `--apply-write` per asset_group pending operator gate.
- [ ] **[deployment-api]** P2. Add a `totals_source: "rollup" | "manifest"` field to both code paths' response so the UI
      can render a tooltip explaining where each number came from and why they may differ until writegate Phase 2.E.2
      fully lands. Defensive observability — no behaviour change.

These are P1/P2 not P0 because:

- The percentages are correct given their respective denominators (no math bug).
- The "20 or 50" truncation is a sample-preview cap, not a count cap — the full counts are correct.
- Writegate Phase 2.E.2 (in flight) will close the rollup-vs-drilldown divergence as a side effect.

**The operator's audit confirms the existing plan's diagnosis** — Phase 6 pagination work shipped by another agent (per
`5bcea1d4` handoff) addresses the per-instrument lazy-load. The deltas above add the venue-detail-panel sample cap + the
cross-path denominator documentation that the existing plan didn't cover.

### What this follow-up audit did NOT do

- Re-test against a running deployment-api / deployment-ui locally — relied on code-reading. Recommend a Playwright pass
  with the deployment stack at `localhost:5183` once the existing Phase 6 work is verified shipped to confirm
  user-visible breakdown matches the corrected denominator.
- Trace the rollup's per-asset-group expected-universe enumeration in detail (which UAC SSOTs each asset_group's rollup
  uses for `expected_dates`). Out of scope for the truncation question; relevant for writegate Phase 2.E.2
  cross-asset-group rollout.
- Investigate whether the rollup blob itself is stale (last-rebuild timestamp). If the rollup is N hours old and
  manifest writes have landed since, the divergence is rollup-staleness, not denominator drift. Worth checking the
  rollup blob's `built_at` timestamp on the next divergence.
