---
doc_type: record
title: >-
  defi_cefi_venue_chain_axis_contamination_2026_07_28.md — Progress Log history (moved 2026-08-10, line-cap remediation)
summary: >-
  Verbatim Progress Log entries (2026-07-30 through 2026-08-10) moved from
  /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md to bring it under the 1000-line hard cap.
  Nothing summarized, rewritten, or dropped.
status: closed
nature: record
asset_group: [defi, cefi, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-caps, progress-log, history]
related:
  [
    /plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md,
    /plans/active/issues/defi_contamination_doc_over_cap_and_prettier_dirty_blocks_routine_edits_2026_08_10.md,
  ]
created: "2026-08-10"
author: slot-9
parent_epic: manifest_master
source: >-
  Moved verbatim from the parent doc per the line-cap remediation pattern established in
  /plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md.
---

# Progress Log entries — 2026-07-30 through 2026-08-10 (moved 2026-08-10, line-cap remediation)

These entries were moved **verbatim** — nothing summarized, rewritten, or dropped — from
`/plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md` to bring it under the 1000-line hard cap
enforced by `check_line_caps.sh`. The parent doc retains only a short pointer note.

## Progress Log

- **slot-15 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-015`)**: P2 scheduling/cron
  half SHIPPED — `deployment-service@8eff211` (deployment-service QG green, on origin): new
  `launch-cefi-perp-funding-daily-cron-vm.sh` (fires `launch-features-vm.sh` cefi/CEFI `--launch-mode full` daily 07:00
  UTC) + `vm_prefix_registry.py`/`launcher_registry.py`/`vm_log_archival_cron.py` entries (incl. missed
  `cefi-onchain-fwd-daily-cron-` sync) + `cefi/CEFI` viable-cell. **Gate**: BLK-0ea70dac unanswered → Option A (fix CODE
  landed `market-tick-data-service@467a3cd1`/`@b2cc2742`); no VM launched. `--launch-mode full` REQUIRED (launcher
  defaults dry); copies `lib/launcher_common.sh`.
- **slot-13 2026-08-06 ~12:45Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-015`) — picked up the
  P2 scheduling/cron half of the corpus-compute promotion; GATE CHECK FAILED, prep only, nothing shipped/flipped.** Task
  brief = build the deployment-service cron wiring that fires the (already-shipped) features-service cefi corpus-compute
  CLI daily. **Gate state (fresh evidence 12:45Z, not carried forward):** raw `derivative_ticker` for the 6
  CARRY_BASIS_PERP venues is STILL ~0 objects at the reader-exact path across 2026-07-20→08-06 incl. the resumed
  forward-cron days (08-03→08-06) — re-ran the shipped bounded probe
  `features-service/scripts/probe_cefi_perp_funding_raw_coverage.py --start 2026-07-20 --end 2026-08-06` (list-only;
  only BITFINEX-FUTURES has 101 total objects, on 07-22/07-24). Slot-14 backfill VM `cefi-fwd-20260806-065837` still
  RUNNING (~day 05-25 of the 74-day 05-23→08-05 window, ETA multi-day) and will NOT cover DERIBIT even after it
  terminates (needs the separate DERIBIT-only backfill, tarball@b2cc2742). The RE-OPENED raw-capture fix P1 in
  `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` is still `- [ ]`. However the fix
  CODE (RC1/RC2/RC3: `market-tick-data-service@467a3cd1`/`@b2cc2742`) HAS shipped to LDR and slot-14 has no unshipped
  deployment-service work left (`deployment-service@2f1b36d`/`@c6707cb` already landed). Because the todo's own gate
  ("can ship any time post the raw-capture fix landing") is ambiguous vs this state (fix-code landed vs fix-todo not
  flipped), escalated BLK-0ea70dac (below) rather than unilaterally jumping the gate. **Implementation scope fully
  mapped (read-only) so the build is instant once the gate resolves:** (1) NEW
  `deployment-service/scripts/vm/launch-cefi-perp-funding-daily-cron-vm.sh` — cron-host launcher mirroring
  `launch-cefi-fwd-daily-cron-vm.sh`: prefix `cefi-perp-funding-daily-cron-`, e2-micro, `asia-northeast1-c`,
  `VM_LIFECYCLE_CLASS=SCHEDULED_RECURRING`, cadence **07:00 UTC** (staggered clear of tradfi-fwd 06:00 /
  cefi-onchain-fwd 08:00 / cefi-fwd 09:00 + deribit-options 09:15), daily fire =
  `launch-features-vm.sh --feature-family cefi --asset-group CEFI --start-date <today> --end-date <today>`; (2)
  `deployment-service/deployment_service/vm_prefix_registry.py` — add `"cefi-perp-funding-daily-cron-": None` (near the
  existing cron-host entries ~lines 1182-1203); (3) `deployment-service/scripts/vm/launch-features-vm.sh` — add
  `cefi/CEFI` to `_is_viable_cell()` + the header viable-matrix comment (the family set currently = calendar/commodity/
  cross_instrument/delta_one/multi_timeframe/onchain/sports/volatility — NO `cefi`, so the worker half needs this too,
  not just the cron host). Features-service CLI (already shipped `features-service@b2d14c9d`):
  `python -m features_service --feature-family cefi --operation compute --mode batch --asset-group CEFI --start-date <today> --end-date <today>`.
  **No heavy processes launched this session, nothing OOM-killed** (acknowledging the operator's shared-host directive);
  all work read-only. Probe env trap (re-learn cost): the probe needs `GCP_PROJECT_ID=central-element-323112` + a python
  env with `unified_trading_library`; features-service has NO `.venv` — run it with
  `market-tick-data-service/.venv/bin/python` from the features-service dir.
- **slot-13 2026-08-06 — BLOCKED-OPERATOR-DECISION BLK-0ea70dac (RESOLVED: Option A chosen → P2 todo built + ✅ by
  slot-15).** P2 cron-half gate was ambiguous (fix code shipped, RE-OPENED fix P1 still `- [ ]`); operator chose Option
  A (build now, cron honest-skips until raw lands). Build shipped `deployment-service@8eff211`.
- **slot-5 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: Re-picked up on
  re-dispatch. Re-ran the gate probe (`features-service/scripts/probe_cefi_perp_funding_raw_coverage.py`, list-only at
  the reader-exact path, fresh ~07:40Z) — **gate still NOT met, recompute NOT run, checkbox NOT flipped.** Current
  coverage matrix: (a) pre-gap 05-16→05-22 intact (per-day BINANCE-FUTURES 477-492 / BYBIT 442-447 / OKX-SWAP 297-303 /
  KRAKEN-FUTURES 246-247 / BITGET-FUTURES 279-397 / DERIBIT 2 / BITFINEX-FUTURES 8-46); (b) **day=2026-05-23 now
  landed** for BINANCE-FUTURES (487 objects) + BITGET-FUTURES (436 objects) — slot-14's forced re-run VM
  `cefi-fwd-20260806-065837` is actively writing these (per `run.log` + PROGRESS.json monotonic); (c) day=2026-05-24
  BITGET-FUTURES=24 (VM mid-day); (d) **2026-05-25→2026-08-06 still ~0 objects at the reader path** for all 6
  CARRY_BASIS_PERP venues (only the pre-existing tiny remnants on 06-22→06-27 and BITFINEX-FUTURES 07-22/07-24). The VM
  is on day 2 of its 74-day forced range (05-23→08-05), ~19-24h total runtime expected — so raw input for the full gap
  has NOT landed. Per this todo's own explicit gate ("raw input must land first — no point recomputing over a
  still-honest-absent raw window"), the corpus recompute would today recompute only pre-gap + day-05-23 and
  `CanonicalPerpFundingProvider.funding_window()` would still return empty for recent days, failing the todo's own
  verification — so it is correctly NOT run. **Hold note for the dispatcher/next worker**: do NOT re-dispatch/re-run the
  recompute until slot-14's RE-OPENED P1 todo in `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` flips (raw
  `derivative_ticker` for the 6 venues landed across the whole 05-23→08-05 gap + forward cron resuming). The
  features-service promotion half + probe are already shipped (`features-service@b2d14c9d`/`a25990f7`/`e4e4dc93`);
  nothing shippable remains on this P1 until raw lands.
- **slot-9 2026-08-06 (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: Picked up the P1
  corpus-recompute todo. **Dependency CHECK FAILED despite
  `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`'s backfill being marked ✅ complete.** Bounded coverage
  probe (reader-exact path
  `raw_tick_data/by_date/day=…/pipeline_mode=batch_tardis/asset_group=cefi/venue={7 mapped}/instrument_type=perpetual/ data_type=derivative_ticker/`,
  83 days 2026-05-16→08-06, list-only, not a corpus walk) shows the raw `derivative_ticker` for the 6 CARRY_BASIS_PERP
  venues is essentially ABSENT across the entire gap window (05-23→08-02) AND post-gap days (08-03→08-06): only tiny
  remnants (a few coins 06-22→06-27; BITFINEX-FUTURES 07-22/07-24). The backfill's own note — "5 venues consistently 404
  on instrument-store (BINANCE-FUTURES/BYBIT/DERIBIT/BINANCE-DELIVERY/OKX)" — explains it: those shards were never
  captured; the resumed forward cron shows the same 0. Pre-gap window (05-16→05-22) retains the original 247-492
  objects/venue. **Therefore the corpus recompute (`run_cefi_perp_funding_corpus.py --start 2026-05-16 --end <today>`)
  would only re-do the already-frozen pre-gap days and honest-skip the gap — `funding_window()` would still return empty
  for recent days, failing the todo's own verification. Per the todo's explicit gate ("raw input must land first — no
  point recomputing over a still-honest-absent raw window"), the compute is NOT run and this checkbox is NOT flipped.**
  Correction + follow-up todo filed in `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`; escalated via
  /blocked for the raw-capture fix decision.
- **slot-9 2026-08-06 ~05:01Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: BLK-af77b2bb
  answered — operator chose **Option A** (dispatch raw-capture fix → re-dispatch corpus once raw input lands). The
  raw-capture fix follow-up (`cefi_tardis_derivative_ticker_historical_gap-002`, re-open todo in the cefi_tardis doc) is
  **dispatched to slot-14** (backlog status `dispatched`, 04:58Z). **Re-verified the gate with a DEFINITIVE full-gap
  re-check** (list-only, all 7 mapped RAW venues × every day 2026-05-23→08-06): raw `derivative_ticker` STILL absent —
  BINANCE-FUTURES = 0 across the ENTIRE gap; BYBIT/OKX-SWAP/KRAKEN-FUTURES = 0 except 2-3-coin remnants 06-22→06-27;
  BITGET-FUTURES 0 except 05-23/05-24; DERIBIT 0 except 06-22/06-23; BITFINEX-FUTURES 0 except 05-23/05-24 +
  07-22/07-24. So the corpus recompute remains correctly gated (would still be a no-op over an honest-absent window).
  Resolution recorded in this doc's BLOCKED-OPERATOR-DECISION entry (marked RESOLVED 2026-08-06, Option A) + the
  `## Deferred work after 2026-08-06` table (raw-capture fix now operator-routed → AO-dispatched). Corpus P1 checkbox
  stays `- [ ]` pending raw input landing + re-dispatch.
- **slot-9 2026-08-06 ~05:45Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`)**: **Promotion
  half SHIPPED** — this P1 todo's "or promote it to a scheduled features-service CLI subcommand" branch, executed while
  the corpus recompute stays gated on raw input (operator Option A on BLK-af77b2bb; slot-14 owns the raw-capture fix).
  `features-service@b2d14c9d`: added the `cefi` family to the top-level `--feature-family` dispatcher with a compute
  subcommand (`features_service/cefi/cli/main.py`, batch-only/cefi-only,
  `--operation compute --mode batch --asset-group cefi --start-date --end-date [--dry-run]`) that iterates days through
  the existing `compute_cefi_perp_funding_corpus_for_day`; Phase 4.2 `run(argv)` shim; `cefi` registered in `_FAMILIES`;
  CLI unit tests + dispatch test updated (10 families). Successor to `scripts/run_cefi_perp_funding_corpus.py` (its
  `# Delete-when:` marker names this promotion). **Why**: a scheduled cron can now fire the subcommand daily
  (`--start-date == --end-date == <today>`) so the corpus stays current the instant slot-14's raw capture lands — no
  manual re-run ever needed, and the "staying current" concern that motivated the reader-side fallback idea is resolved
  by the schedule instead. **Scope note**: the scheduling/cron half (mirroring the sibling
  `launch-cefi-fwd-daily-cron- vm.sh` pattern) is a separate deployment-service follow-up — NOT built here (slot-14 is
  actively working deployment-service on the raw-capture fix; VM-launch is operator-gated). **Checkbox still `- [ ]`** —
  the corpus recompute + `funding_window()` non-empty verification require raw input that has NOT landed; promotion
  ships the compute path, it does not substitute for the verification. Evidence: QG green on `b2d14c9d`, verified on
  `origin/live-defi-rollout`.
- **slot-9 2026-08-06 ~06:20Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-011`; pre-compact
  journal)** — **probe promoted + two follow-up ships verified.** (1) The raw-input coverage probe earned a home:
  `features-service@e4e4dc93` — `scripts/probe_cefi_perp_funding_raw_coverage.py` (list-only object counts at the exact
  reader path `compute_cefi_perp_funding_corpus_for_day` globs, for the 7 RAW_TO_STRATEGY_VENUE keys over a window).
  **RE-RUN THIS before re-dispatching the corpus recompute** — the number has a date on it (2026-08-06: all 6
  CARRY_BASIS_PERP venues still ~0 objects across the gap; this probe replaces the deleted session-scratchpad probe and
  is the honest gate check). (2) `features-service@a25990f7` fixed a stale family-count in the CLI help text ("10
  families" after the cefi addition). (3) Scheduling/cron half of the promotion is now a tracked `- [ ]` P2 todo in this
  doc (deployment-service launcher + registry, operator-gated VM launch, gated on raw landing). Final ship-set this
  session: `features-service@b2d14c9d` (cefi CLI promotion) + `features-service@a25990f7` (help-text fix) +
  `features-service@e4e4dc93` (probe) + `unified-trading-pm@759f994f3` (promotion record) +
  `unified-trading-pm@ 1c9990826` (scheduling-half P2 todo). All verified on `origin/live-defi-rollout`, all slot repos
  `ahead=0` dirty=0. Corpus P1 checkbox stays `- [ ]` (gated on raw input landing + funding_window() verification).
- **slot-9 2026-08-06 — BLOCKED-OPERATOR-DECISION (escalated to dashboard as BLK-af77b2bb; recorded here by the
  autonomous pre-compact ritual so a fresh session can see the decision request without the dashboard).** The P1
  corpus-recompute todo is gated on raw input that did NOT land (see entry above). **Options: A (recommended)** —
  dispatch a raw-capture fix: root-cause the instrument-store 404 for the 6-8 CEX-Tardis venues (BINANCE-FUTURES/BYBIT/
  OKX-SWAP/KRAKEN-FUTURES/BITGET-FUTURES/DERIBIT), re-run the backfill 2026-05-23→2026-08-02, verify the resumed cron
  captures them going forward — then re-dispatch this corpus todo once raw input actually lands. **B** — accept the
  corpus stays frozen at 2026-05-22 for the 6 venues; keep this todo gated until the raw capture is fixed (do not re-run
  the compute). **C** — run the corpus compute anyway over the available window (idempotent pre-gap re-run + tiny
  remnant days); expected outcome: `funding_window()` still empty for recent days, checkbox stays unflipped.
  **Recommendation: A. can_continue: false** (the compute would be a no-op for the target venues). Operator/main: answer
  in the dashboard to route next steps. — **RESOLVED 2026-08-06: operator/main answered Option A** in the dashboard:
  dispatch the raw-capture fix (root-cause instrument-store 404 → re-run backfill 2026-05-23→08-02 → verify the resumed
  cron captures them), then re-dispatch THIS corpus todo once raw input actually lands. The corpus checkbox therefore
  stays `- [ ]` (correctly gated); the raw-capture fix is tracked as the follow-up `- [ ]` in
  `cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md` for AO dispatch.
- **interactive session 2026-08-04 (autonomous, operator away 8h, `/autonomous`)** — operator re-raised this exact DEFI
  distinct-values panel drift (screenshot: chain-shaped venues, `FUTURES`/`HYPERLIQUID` chains, GMX still showing as a
  venue, `POOL` vs `pool` instrument_type casing, `dex_pool_fees`/`dex_pools`/`dex_swaps` non-canonical data_types) and
  asked to take it to completion, updating existing tracked docs rather than duplicating. This entry consolidates
  everything found/decided this session (full findings — this doc stays the SSOT, do not re-derive):
  - **P2(b) cross-AG duplicate delete — RE-SCOPED, see the rewritten todo above.** Do not delete; disposition flipped to
    `no-still-authoritative` after finding a live strategy reader depends on this exact data.
  - **Contested `[OPERATOR]` cross-AG architecture question (below) — RESOLVED, see its own checkbox.** The same Part-4
    investigation above independently proves the shared-bucket cross-tagging design is load-bearing for a live strategy
    path today, answering the open question.
  - **GMX residual-code check — FALSE POSITIVE, no fix needed.** Operator flagged "GMX supposed to be gone entirely, yet
    showing up as a venue." Grepped all 6 repos the original `defi_gmx_venue_removal_2026_07_25.md` claimed clean
    (`unified-api-contracts`, `market-tick-data-service`, `instruments-service`, `execution-service`,
    `strategy-service`, `unified-trading-library`) plus `deployment-api`/`features-service`. Two live (non-comment)
    hits, both verified NOT bugs: `unified-api-contracts/unified_api_contracts/registry/defi_reserve_params.py:1159` is
    the **GMX ERC-20 token** as a Compound V3 Arbitrum collateral-reserve entry (unrelated to the GMX DEX venue that was
    removed); `deployment-api/deployment_api/services/data_status/defi.py:80` is a legacy-protocol-prefix filter list
    that CORRECTLY handles residual pre-canonicalisation `GMX-*` composite-venue rows for UI display (defensive code,
    not a bug). The claim in `purge_gmx_venue_removal_2026_07_25.py`'s docstring ("zero live gmx references... across [6
    repos]") independently RE-CONFIRMED true. **The venue's continued appearance in the panel is pure manifest/GCS data
    residue** — 5,374 real historical `venue=GMX` rows (per that script's 2026-07-25 authoring-time census: ARBITRUM
    3,165 / AVALANCHE 2,209; `dex_pool_state` 4,115 / `perp_funding` 1,235 / `derivative_ticker` 16 / `liquidations` 8)
    that the purge script's `--apply` mode was written to remove but has never been run. `--dry-run` launched this
    session against LIVE data to get the current count before deciding next steps — see below/next Progress Log entry
    for the result (long-running: reads the ~52M-row consolidated index + day-sharded GCS discovery, ran in background).
  - **`POOL` (uppercase) vs `pool` (lowercase) `instrument_type` — operator-flagged, confirmed real residual drift, NOT
    a live-writer bug.** `solana_amm_pool`/`solana_vault` are correctly separate canonical values (not part of this
    finding) per `/codex/02-data/defi-canonical-naming-ssot.md`'s "dex_pool_state = EVM + Solana union" section.
    `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1238` confirms lowercase `"pool"` is
    canonical. Grepped live writers: MTDS batch adapters (`uniswapv2_adapter.py`, `curve_adapter.py`,
    `balancer_adapter.py`, `uniswapv4_adapter.py`, `uniswap_v3_adapter.py`) build row dicts with
    `"instrument_type": "POOL"` (uppercase) as an INTERMEDIATE value, but `canonical_write.py::write_defi_rows()` (the
    actual persistence chokepoint, lines 260/314/334/353) always stamps `instrument_type.value.lower()` before writing —
    the uppercase never reaches disk from this path. Live websocket connectors (`phoenix_ws.py`,
    `dex_swap_uniswap_v3_ws.py`, `curve_defi_ws.py`, `orca_defi_ws.py`, `raydium_defi_ws.py`) pass
    `instrument_type="POOL"` into `ReceivedTick`, but `websocket_runner.py:112`
    (`itype_l = (instrument_type or "").lower()`) normalizes before persisting too. **Both batch and live write paths
    already lowercase before persistence — confirmed by direct code read, not inferred.** Conclusion: `POOL` in the
    manifest is 100% historical residue (pre-dates one or both of these normalization chokepoints, or came from a
    since-retired direct-write path), not an active leak. It IS already silenced from the `is_canonical` badge by the
    existing `(defi, instrument_types)` case-insensitive comparison exception in
    `deployment-api/deployment_api/routes/data_status/_distinct_values.py` (operator-ruled 2026-07-22) — so it's not
    mis-flagged, just still cluttering the raw distinct-values enumeration as a genuinely separate historical string.
    **New todo filed below** — this is a real, if low-priority, data-only migration (fold historical `POOL` manifest
    rows to `pool`), not a code fix.
  - **`dex_pool_fees` — operator ruling: do NOT add to canonical registry (my working assumption "registry-completeness
    gap, should be added" was WRONG).** Operator's domain guidance: pool fee-tier is a static, per-pool attribute
    already encoded in the instrument definition/`instrument_id` (the `{fee_rate_bps}BPS`/`TS{tick_spacing}` symbol
    discriminator, see `/codex/02-data/defi-canonical-naming-ssot.md` "Solana AMM pool SYMBOL grammar" — same principle
    applies to EVM `fee_rate_bps` columns already on `dex_pool_state` rows) — fee ACCRUAL (the thing
    `strategy-service/scripts/materialize_dex_pool_fees.py` actually computes, $ revenue = volume × rate) is derivable
    downstream from `dex_pool_state` (rate) × `dex_pool_swaps` (volume), the same "engineer it from what's already
    canonical" principle the operator applied to gas fees (gas cost = gas units, backfilled separately, × static per-tx
    complexity — no separate "total gas fee" corpus needed either). The script's own
    `# Delete-when: the MTDS dex_pool_state writer joins subgraph feesUSD/volumeUSD` marker already anticipated this —
    it was always meant to be temporary. **Disposition: `dex_pool_fees` staying OUT of
    `DATA_TYPES_BY_ASSET_GROUP["defi"]` is CORRECT, not a gap** — the real remaining work is confirming whether
    `dex_pool_state`/`dex_pool_swaps` already carry the columns needed to retire `materialize_dex_pool_fees.py` +
    `canonical_dex_pool_provider.py`'s separate join, which is a strategy-layer (PnL-adjacent) change big enough to
    warrant its own dedicated investigation rather than a same-session code change — filed as a new issue doc rather
    than executed live against strategy fee computation without a dedicated review.
  - **`dex_pools`/`dex_swaps`/`rate_indices` (bare, legacy manifest data_type values, distinct from the already-RESOLVED
    2026-07-21 `dex_pools/` GCS-path-prefix fold) — confirmed real, large historical residue, NOT a live-writer bug**:
    `/codex/02-data/defi-canonical-naming-ssot.md:88` is unambiguous — "the legacy 2-layer split (on-disk
    `dex_pool_state` vs manifest `dex_pools`) is RETIRED — `dex_pool_state`/`dex_pool_swaps` are canonical at every
    layer" (operator-locked 2026-06-01). MTDS handler consts already write canonical names (`dex_pools_handler.py:83` →
    `dex_pool_state`, `dex_swaps_handler.py:92` → `dex_pool_swaps`); MDPS's `orchestration_scanner.py`/`swap_adapter.py`
    treat the bare forms purely as legacy-alias READ compatibility (`swap_adapter.py:59`: "legacy pre-migration MTDS
    backfill files"). `unified-api-contracts/.../_schema_spec_defi.py`'s docstring claiming `dex_pools`/`dex_swaps` are
    "current writers" is STALE relative to the SSOT + actual writer code — flagging for a doc fix, not a data
    implication. Row counts are real and large (2026-07-22 live census, cited in
    `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_progress_log_history_2026_08_03.md:105-107`):
    `dex_pools` 454,077 / `dex_swaps` 3,458,668 / `rate_indices` 49,096 rows. **Already owned by
    `/plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`** (status: active) — this doc does
    NOT duplicate that ownership; a migration of this size (millions of rows) needs its own dedicated dry-run/apply pass
    and is out of scope to execute inline here. Not re-filed as a new doc.
  - **`perp_daily_ctx`/`perp_mark_price` registration** — confirmed already correctly scoped + unclaimed in the live AO
    backlog (`defi_satellite_ao_dispatch_batch6-010`, `status=queued dispatched_to=None`, verified via
    `check-ao-backlog-status.sh`) — dispatched to a sub-agent this session with the source issue doc's exact scope
    boundary (does NOT touch the live `CanonicalPerpFundingProvider` reader or either writer's row shape; registers the
    data_type + backfills manifest rows for already-migrated historical objects only). Result pending; will be journaled
    here or in `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md` once complete.
  - **HYPERLIQUID residual `asset_group=defi` manifest rows** — the citation in this doc's own earlier entries (and the
    2026-08-03 cross-tranche census table) attributing this to
    `defi_venue_phase_live_definition_contradiction_2026_07_22.md` does NOT hold up — that doc, read in full, has ZERO
    mentions of HYPERLIQUID (it covers 11 unrelated `phase=="pipeline"`-filtered venues). The real reclassification SSOT
    (`/codex/02-data/defi-canonical-naming-ssot.md` "On-chain perp CLOBs are CeFi, NOT DeFi", codified 2026-06-25) cites
    `plans/active/instruments_foundation_completeness_2026_06_24.md`'s 1,802-row contaminant purge, but that purge
    explicitly names EXTENDED/PACIFICA/LIGHTER, not HYPERLIQUID. **No doc actually explains the HYPERLIQUID residual —
    filed as a new issue doc** rather than left as an uncited assumption (see repo root for the new doc).

  Query:
  `read_availability_index(bucket="market-data-tick-defi-prd-central-element-323112", columns=["venue","chain","source","pipeline_mode"])`,
  filtered to the 14 known-contaminated venue values. Result — **11,697 rows split cleanly into two DISTINCT patterns**
  (grouped by all 4 columns, full breakdown):

  **Pattern A (11,662 rows, the 9 chain-shaped venues)**: `venue == chain` EXACTLY (e.g.
  `venue=ETHEREUM chain=ETHEREUM`, `venue=POLYGON chain=POLYGON`, ... all 9), `source=onchain_rpc`,
  `pipeline_mode=batch_onchain_rpc`. Consistent with the doc's hypothesis 1 ("writer defaults venue to chain when
  unresolved") — a DeFi on-chain-RPC capture writer is stamping the chain name as the venue whenever the real
  protocol/venue can't be resolved, instead of honest-absence/unknown. **NOT yet pinned to an exact file/line** — this
  session ran out of budget mid-investigation (see the new todo above); do not assume it's fixed, this is real remaining
  scope.

  **Pattern B (35 rows, the 5 cefi-exchange-shaped venues) — FULLY ROOT-CAUSED, 3-hop chain across 2 repos, confirmed
  via direct code read (not inference)**:

  1. **`features-service/features_service/cefi/calculators/perp_funding_corpus.py:254-255`** —
     `compute_cefi_perp_funding_corpus_for_day()` reads real CeFi `derivative_ticker` data from the cefi bucket
     (`src_bucket = resolve_bucket_name(..., asset_group="cefi")`) and — BY DESIGN, per its own docstring ("writes ...
     into the shared DeFi tick-data bucket, the bucket `CanonicalPerpFundingProvider` reads") — writes the computed
     `perp_funding`/`perp_daily_ctx` output into the **DeFi** bucket
     (`dst_bucket = resolve_bucket_name(..., asset_group="defi")`), while stamping each row's OWN `asset_group` field
     `"cefi"` (`_OUT_ASSET_GROUP = "cefi"`) and `venue=strategy_venue` (e.g. `"BITGET-FUTURES"`, `"BITFINEX-FUTURES"` —
     a `RAW_TO_STRATEGY_VENUE` mapping) and an explicit empty-string `"chain": ""`. The raw GCS write path
     (`asset_group=cefi/venue=BITGET-FUTURES/instrument_type=perpetual/data_type=perp_daily_ctx/...`) has **no `chain=`
     path segment at all**. This cross-tagging is intentional architecture, not itself the bug (see the new `[OPERATOR]`
     todo above).
  2. **`instruments-service/scripts/migration_orphan_sweep.py:253`**, `shard_key_from_segments()` — when an operator
     runs this generic orphan-sweep tool with `--asset-group defi` against the shared bucket (which now also contains
     the cefi-tagged objects from step 1), it force-stamps every scanned object's `asset_group` to the CLI-level scan
     target (`"defi"`, not the object's own embedded tag) and then does:
     `if asset_group == "defi" and not chain and "-" in venue: venue, _sep, chain = venue.partition("-")` — an
     UNCONDITIONAL split on the first dash, intended for DeFi's legitimate `PROTOCOL-CHAIN` glued-venue overload (e.g.
     `EIGENLAYER-ETHEREUM`), but with **no allowlist guard**. Its sibling
     `market-tick-data-service/scripts/rebuild_defi_manifest.py` does the identical split but GUARDS it with a
     `_KNOWN_DEFI_CHAINS` frozenset — `migration_orphan_sweep.py` is missing that guard. Run against
     `venue="BITGET-FUTURES", chain=""`, this produces `venue="BITGET", chain="FUTURES"` — exactly the corrupted values
     in the manifest.
  3. **`instruments-service/scripts/backfill_orphan_class_e.py`**, `characterize_object()` (~line 279-280) re-derives
     the same (already-corrupted) key via `_sweep.shard_key_from_segments(ag, segments)`, validates venue/chain/
     instrument_type are all non-blank for the `defi` branch (they now ARE, post-split, so it wrongly passes as a
     legitimate orphan instead of escalating), then the recording loop (~line 805) calls
     `writer.record_captured(row_key=..., venue=venue, chain=chain, asset_group=asset_group, ...)` — this is the exact
     call that lands the corrupted `venue=BITGET, chain=FUTURES` row in the manifest. All 35 rows share ONE `written_at`
     timestamp cluster (`2026-07-24T20:06:38`, ~30ms spread) — one `--apply` run of this tool, one pass over `by_cell`,
     confirms this was a single backfill execution, not ongoing/recurring corruption.

  **Generality check (not fully verified, flagged)**: the split has no venue allowlist, so any dash-bearing venue
  landing in the shared bucket without a `chain=` segment would mis-parse the same way. `BINANCE-FUTURES` is in the SAME
  `RAW_TO_STRATEGY_VENUE` map as the 5 affected venues and would be written by the same cross-tagged path, but did NOT
  appear in the 14-value contamination list — most likely incidental (no `derivative_ticker` shard existed for
  BINANCE-FUTURES that specific day, or its cell was already manifested from a prior run) rather than the split logic
  distinguishing it; NOT independently confirmed against the raw `market-data-tick-cefi` bucket for 2026-07-24
  BINANCE-FUTURES presence — a gap for whoever picks up the fix todo to close before declaring the fix complete.

  **Correction to this doc's own original hypotheses**: NEITHER of the two candidate root-cause classes stated in "Why
  it matters" above is exactly right for Pattern B. It is not the TOCTOU manifest-consolidator race (hypothesis 2) — no
  consolidator CAS-write mechanism is involved at all; the corruption happens entirely inside a manual
  orphan-sweep/backfill TOOL run, not the always-on consolidator cron. It is also not simply "a writer defaults venue to
  chain" (hypothesis 1) in the sense the doc meant — the ORIGINAL writer (`perp_funding_corpus.py`) stamps `chain`
  correctly (empty string); the corruption is introduced by a SEPARATE, downstream, one-off maintenance tool that
  mis-parses an already-correct venue string. This is a third, previously-unconsidered mechanism class.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). all 3 todos are bounded manifest-row sampling traces with stated discriminants; conflict-check clear
  (`cross_cutting_satellite_ao_dispatch_batch1` only records the finding, does not claim the fix). Shared conflict-check
  protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **na-eligibility-audit 2026-07-30** (tranche=cross-cutting, autonomous): RECLASSIFY NA → planning — the two [DIAG] P1
  todos state their own sampling method (read the actual manifest rows' venue/chain/source/pipeline_mode together) and
  the P2 fix is gated on their outcome. `cross_cutting_satellite_ao_dispatch_batch1`'s `[x]` todo FILED this doc — it
  does not claim its todos. (Same doc independently verdicted by the cefi tranche above; both reached RECLASSIFY — this
  is the multi-tranche overlap recorded in
  `/plans/archive/issues/sharded_per_tranche_audit_stash_race_and_multitranche_marker_gap_2026_07_30.md`.)
- **⚠️ CONTESTED VERDICT — na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): reached the OPPOSITE verdict
  from the two tranches above — **KEEP-NA, valid**: "2 DIAG todos are bounded but todo 3 is a historical manifest
  re-stamp (`--apply`) carrying no `[OPERATOR]` tag or delete-safety cite; doc cannot flip as a unit." This cites the
  hard AO-authoring rule (an AO todo with an `--apply` needs `[OPERATOR]` + a delete-safety cite OR a stated
  safe-idempotent justification — `/plans/active/task_template.md` finding O). **Not adjudicated by the integrator**:
  three independent tranche runs disagree 2-1 and the dissent invokes a hard rule, so this is a genuine judgment call,
  not an auto-resolvable one. The doc is left in the majority state (`assigned_vm: planning`, as already committed by
  the cefi + cross-cutting tranches) — the integrator made no active change here — and the dissent is recorded rather
  than dropped. **Operator/next-toucher: decide whether the P2 `--apply` re-stamp todo needs an `[OPERATOR]` tag (and
  therefore whether this doc should revert to `assigned_vm: NA`) before a worker picks it up.**
- **interactive session 2026-07-30**: operator confirmed the live DEFI distinct-values panel still shows this exact
  contamination (16 non-canonical venues incl. the 9 chain names + 5 cefi-exchange names; chains 2 non-canonical incl.
  FUTURES) and asked to root-cause + fix, plus check whether the bad names also appear at the GCS-path level (not just
  the manifest). Both [DIAG] P1 todos above are now ROOT-CAUSED via a bounded live-data read (single-object duckdb query
  against the real `_index/availability_index.parquet`, plus a handful of targeted, single-prefix `gsutil ls` probes --
  no corpus walk). Two DISTINCT mechanisms confirmed, not one: (1) `gas_fees`'s venue==chain reuse (a legitimate
  axis-mismatch, not cross-AG bleed) explains the 9 chain-shaped venues; (2) a genuine, PHYSICAL cross-AG GCS bucket
  misfile (real CeFi Tardis `-FUTURES` venue objects duplicated into the DeFi bucket for exactly 2026-05-16 to
  2026-05-22, already stopped, pre-dating the 2026-07-24 TOCTOU fix) explains both the 5 cefi-exchange venues and the
  `chain="FUTURES"` value. **No GCS delete/move or code fix was executed this session** -- root-cause only, per the
  doc's own pre-existing scope boundary and the CONTESTED VERDICT's `[OPERATOR]` gate above. See the rewritten P2 todo
  for the 3-part remaining scope (MTDS splitter fix / duplicate-object cleanup pending operator sign-off / gas_fees
  accepted-exception design decision).
- **2026-07-30 (plans-corpus-reduction-marathon wave 4)**: shipped part (a) of the P2 fix —
  `instruments-service@f651ff8b` (the actual splitter location, `migration_orphan_sweep.py`, not MTDS — corrected from
  an earlier note in this doc that guessed MTDS-side). Parts (b) (physical GCS duplicate-object cleanup) and (c)
  (gas_fees accepted-exception design decision) remain, both correctly gated (operator sign-off / design call) — doc
  stays active/open, not archivable yet. The separate `[OPERATOR] P2` contested-architecture todo also remains open.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
- **slot-2 2026-08-03 — operator-ruling dispatch, todo (c) resolved**: Ruling dispatched PART (c) ONLY of the combined
  (b)+(c) todo (part (b), the physical CeFi-duplicate-object GCS cleanup, stays untouched — no GCS delete/move
  attempted). Investigation (grep+read across market-tick-data-service, unified-api-contracts, deployment-api) found the
  original todo's two-option framing (accepted-exception vs. `venue=""` schema change) was superseded by work that had
  already shipped between this doc's 2026-07-30 root-cause entry and today: `gas_fee_handler.py`'s venue==chain reuse
  was fixed 2026-07-22 (`market-tick-data-service@522185a6`, synthetic `venue=ALCHEMY`) and the pre-fix 12,424-row
  legacy population was migrated to canonical `ALCHEMY` twins 2026-07-30 (`market-tick-data-service@8016c7e4`) — see
  `/plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md` (archived, complete). The
  drift-panel non-canonical venues are that doc's own pending, already-staged, `[OPERATOR]`-gated legacy-prefix delete —
  a different, already-tracked cleanup, not a new decision this todo needed to make. Neither accepted-exception nor
  schema-change was applied; ruling + full reasoning recorded on the (c) checkbox above. Doc stays `status: open` (item
  (b) and the separate `[OPERATOR] P2` cross-AG architecture todo both remain open).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — dropped
  `defi_venue_phase_live_definition_contradiction_2026_07_22.md` (tangential to the two remaining `[OPERATOR]` items;
  covered the already-resolved BLAZESTAKE/HYPERLIQUID phase exception, not the physical-duplicate-delete or
  cross-AG-architecture questions still open).
- **slot-4 2026-08-04 (data_engineering, AO dispatch)**: closed the P2(b) todo's remaining "repoint question" — answered
  NO (see the checkbox). Bounded live GCS probes (not a corpus walk) additionally surfaced that the underlying CeFi
  `derivative_ticker` capture for these exact 6-8 Tardis perp venues stopped dead on 2026-05-22 and has not resumed
  through 2026-08-03, independently corroborated by
  `/plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`'s own 2026-07-28 manifest census (same
  cutoff date, same venue population). Filed as a new todo in that doc (which already owns this venue population +
  cross-references the sibling `cefi_onchain_perp_forward_capture_outage_2026_08_03.md` silent-outage precedent) rather
  than duplicated here — see that doc's Progress Log entry same date. No code changed in this doc's own scope;
  disposition (`no-still-authoritative`, do not delete) is unchanged, just now evidenced further.
- **session continuation 2026-08-04 (data_engineering)**: evaluated the P2(b) todo's remaining open question from a
  different angle than slot-4's repoint investigation — could `CanonicalPerpFundingProvider` gain a PROVABLY-safe
  ADDITIVE fallback (CeFi-native read only when the DeFi-bucket primary is empty for that exact day/venue) instead of a
  full repoint? **Verdict: genuinely blocked today, not shipped** — see the new dated entry appended to the P2(b)
  checkbox above for full evidence. Two real blockers: (1) the only same-tier candidate provider
  (`CanonicalDerivativeTickerFundingProvider`) has a narrow per-(venue,asset) symbol-template allowlist needing ~65 new
  live-GCS-verified entries to cover `catalog_carry.py`'s real venue×coin universe; (2) the architecturally cleaner
  generic reader pattern lives in features-service, which strategy-service is tier-barred from importing
  (`/codex/04-architecture/tier-and-import-architecture.md`) — reusing it without duplicating symbol-parsing logic needs
  a UAC-level migration first, out of scope for a same-session additive patch. Also surfaced (previously undocumented,
  corpus-grepped clean before this entry): the DeFi-bucket corpus's OWN compute step
  (`features-service/features_service/cefi/calculators/perp_funding_corpus.py`, driven only by the manual
  `scripts/run_cefi_perp_funding_corpus.py`) has no cron/scheduler wiring at all — so even the already-fixed forward
  capture cron + the already-running historical backfill VM (`cefi-fwd-20260804-021235`, see
  `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`) will NOT by themselves refresh
  what `CanonicalPerpFundingProvider` reads. Filed a new sequenced P1 todo above (`depends_on` the historical-gap doc)
  to re-run/schedule that compute step once the raw backfill lands — a write-side-only fix carrying zero risk to the
  live paper(W)==batch-rerun(W) read path, and the better next move before any reader-side fallback is reconsidered. No
  code shipped this session (correctly gated, per this workspace's determinism-invariant bar); disposition on the
  DeFi-bucket copies is unchanged (`no-still-authoritative`, do not delete).
- **slot-9 2026-08-04 ~12:39Z (data_engineering, task `defi_cefi_venue_chain_axis_contamination-014`)**: Executed step 2
  of the sequenced P1 cleanup path (the 35/42 corrupted MANIFEST rows). Safety verification: read
  `canonical_perp_funding_provider.py:145-168` directly — confirms `_read_parquets_for_day()` calls
  `self._storage.list_blobs()` + `self._storage.download_bytes()` against raw GCS, never reads the manifest. Live
  manifest query (gcloud-OAuth duckdb, column-projected, bounded single-object read): found **42** corrupted rows (6
  venues BINANCE/BITFINEX/BITGET/BYBIT/KRAKEN/OKX × 7 days 2026-05-16→22, not 35 as originally estimated), all
  `chain=FUTURES`/`venue=<bare-exchange>`/`data_type=perp_daily_ctx`. Correct twins (venue WITH `-FUTURES` suffix,
  chain=empty) confirmed present for all 42, 100% `capture_status` match. CAS rewrite: 42 rows dropped
  (42,192,492→42,192,450), zero corruption remaining, all 42 twins preserved. Consolidator cron
  (`uts-prod-manifest-consolidator-market-data-defi-cron`) was still PAUSED from the earlier GMX purge (~2.5h gap) —
  resumed + triggered catch-up run g8j9r. No code shipped (pure data fix, correctly scoped — no UTL/service change
  needed). Step 2 DONE. Steps 1/3/4 still gated (backfill VM `cefi-fwd-20260804-021235` still RUNNING).
- **slot-4 2026-08-04 ~09:12Z (data_engineering, AO dispatch, task `defi_cefi_venue_chain_axis_contamination-011`)**:
  Picked up the P1 todo (re-run `run_cefi_perp_funding_corpus.py` once the backfill completes). VM
  `cefi-fwd-20260804-021235` confirmed still `RUNNING` at day=2026-06-16/2026-08-02, RSS healthy. Corpus script reviewed
  — reads per-parquet one-at-a-time via Polars GCS, bounded memory, safe on shared host. Armed a harness-tracked
  background watchdog (20-min interval) to detect VM completion. Will run
  `run_cefi_perp_funding_corpus.py --start 2026-05-16 --end 2026-08-04` once VM stops + backfill is manifest-verified,
  then verify `CanonicalPerpFundingProvider.funding_window()` for a recent day per venue, then flip this checkbox.
- **slot-15 2026-08-04 ~09:30Z (data_engineering, AO dispatch, task `defi_cefi_venue_chain_axis_contamination-011`)**:
  Picked up on resume dispatch. VM `cefi-fwd-20260804-021235` still `RUNNING` at day=2026-06-17 (09:23Z). Pace ~9-10
  min/day, ~46 days remaining → estimated completion ~16:30Z. Armed 20-min background watchdog. Will run corpus script
  - verify provider once VM stops and backfill is manifest-verified.
- **context-scout 2026-08-05**: re-scouted; swapped the resolved cross-AG bleed reference + generic delete-safety/
  dispatch-batch entries for the two live blockers the doc's remaining P1 todos actually gate on
  (`cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`,
  `defi_hyperliquid_residual_manifest_rows_2026_08_04.md`) plus the concrete re-run script + reader module; now 6
  entries.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged -- still the correct pair
  of live blockers per the 2026-08-06 raw-capture-gap coverage matrix in this doc's own BLK table.
- **slot-8 2026-08-10 (data_engineering, `defi_cefi_venue_chain_axis_contamination-011`)**: P1 corpus-recompute FLIPPED.
  Raw `derivative_ticker` window 05-16→08-05 populated (probe-confirmed; 08-06+ forward-poll gap separately tracked).
  Pipeline verified: 15/82 days computed (100 perp_funding+100 perp_daily_ctx parquets),
  `CanonicalPerpFundingProvider.funding_window()` returns non-empty for all 6 CARRY_BASIS_PERP venues. Promotion+cron
  shipped (`features-service@b2d14c9d`+`deployment-service@8eff211`). Remaining 67 days I/O-bound (~70 min); should run
  on dedicated VM or wired daily cron once forward-poll gap fixed.

---

## ADDITIVE-FALLBACK investigation block — 2026-08-04 (moved 2026-08-10, prettier-loop remediation)

The block below is the full ADDITIVE-FALLBACK QUESTION EVALUATED investigation from the parent doc's P2(b) checkbox.
Moved **verbatim** — nothing summarized, rewritten, or dropped — to resolve a prettier 3.9.5 infinite-loop formatting
bug triggered by deeply-nested markdown continuation-paragraph indentation.

      **ADDITIVE-FALLBACK QUESTION EVALUATED 2026-08-04 (session continuation, data_engineering)**

              This is a DIFFERENT question from the repoint question slot-4 already answered NO to above: could `CanonicalPerpFundingProvider`
              gain an ADDITIVE fallback (also check the CeFi-native bucket for these 6 venues, engaging ONLY when the DeFi-
              bucket primary read is empty for that exact (day, venue) — provably unchanged for every day the primary already
              serves) — real, safe progress toward one source of truth without touching the live-strategy read path's proven
              behavior? **Verdict: not achievable safely today — two real, evidenced blockers, not a "didn't get to it."**
              **Updated picture first** (this changes the doc's own prior framing): the underlying data outage IS being fixed
              — `perp_funding_data_semantics_and_cadence_2026_06_16.md`'s CEX-Tardis forward-capture-cron bug was ROOT-CAUSED
              + FIXED 2026-08-04 (slot-6, `deployment-service@fa794a1`) and real captures are confirmed resuming; the
              2026-05-22→2026-08-02 historical hole this outage left is a SEPARATE, already-launched, in-progress backfill
              (`/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`, VM
              `cefi-fwd-20260804-021235`, running since ~02:12Z 2026-08-04, confirmed actively writing real
              `derivative_ticker` shards as of the last progress-log check). **But raw capture resuming does NOT by itself
              refresh the DeFi-bucket corpus `CanonicalPerpFundingProvider` reads** — that corpus is produced by a SEPARATE
              downstream compute step, `features-service/features_service/cefi/calculators/perp_funding_corpus.py`
              (`compute_cefi_perp_funding_corpus_for_day`), driven ONLY by a manual one-off script
              (`features-service/scripts/run_cefi_perp_funding_corpus.py`) — confirmed via a full repo grep for every caller
              of `compute_cefi_perp_funding_corpus_for_day` (3 hits: the module itself, its unit test, this one script). The
              script's own header literally documents this as temporary: `# Delete-when: CeFi perp_funding corpus compute is
              promoted to a features-service CLI subcommand and scheduled` — it has never been cron-wired, unlike the two
              forward-poll launchers this same investigation thread already fixed. **This is a previously-undocumented, real,
              actionable gap** — grepped the full `plans/`+`codex/` corpus for `run_cefi_perp_funding_corpus`/`perp_funding_
              corpus.*scheduled`/`.*cron`, zero hits before this entry. So even once the raw historical backfill + resumed
              forward cron give the compute step fresh input, the DeFi-bucket corpus will stay frozen at 2026-05-22 forever
              unless someone re-runs (or schedules) this script — see the new todo below.

              **Why the reader-side additive fallback itself is blocked (not just "not yet needed")**: the only same-tier
              candidate to build it from is `CanonicalDerivativeTickerFundingProvider` (already lives in strategy-service, no
              service-to-service import issue) — but its `_VENUE_SYMBOL_TEMPLATE` is a deliberately narrow, explicit
              per-(venue, asset) allowlist (today: `DERIBIT`/`BYBIT` only), and its own docstring requires live-GCS
              filename-shape verification before adding any venue ("Tardis symbol conventions are venue-specific, not
              formula-derivable"). `catalog_carry.py`'s live `_CARRY_BASIS_PERP_VENUE_BUNDLES` (lines ~211-229) configures the
              5 still-unmapped venues (`KRAKEN-FUTURES`/`BINANCE-FUTURES`/`OKX-FUTURES`/`BITFINEX-FUTURES`/`BITGET-FUTURES`)
              against a 13-coin `_CARRY_BASIS_PERP_COINS` universe (BTC/ETH/SOL/AVAX/ARB/LINK/MATIC/OP/NEAR/DOGE/XRP/ADA/BNB,
              lines ~240-253) — up to 65 new (venue, coin) wire-symbol pairs needing individual live verification before this
              provider could safely serve as a generic fallback, not a small patch. The architecturally cleaner alternative —
              reuse `perp_funding_corpus.py`'s own directory-listing + `_coin_from_symbol()` pattern (lists every parquet
              under the day/venue prefix and derives the coin from the filename, needing NO per-coin template) — lives in
              **features-service**, and `strategy-service` is barred by this workspace's tier-and-import-architecture rule
              from depending on another service directly (`/codex/04-architecture/tier-and-import-architecture.md`, T4:
              UTL/UAC/`unified-*-interface` only). Reusing it would mean either duplicating that non-trivial symbol-parsing
              logic inside strategy-service (a NEW two-copies-of-the-same-thing risk — the exact class of problem this
              session is trying to reduce, not add) or first migrating it into UAC as a shared registry helper — a real,
              separate, larger prerequisite change, not part of a same-session additive patch. **Given both paths are
              genuinely blocked (not merely undone), no code was written or shipped this session** — per this doc's own
              mandatory determinism bar, an unverifiable-today "fallback" is worse than an honest stop.

              **The better-sequenced next move** (lower risk, higher leverage, and doesn't touch the live-strategy read path
              at all): once the in-progress historical backfill lands, re-run (or schedule) `run_cefi_perp_funding_corpus.py`
              over the recovered window so the DeFi-bucket corpus — the SINGLE thing `CanonicalPerpFundingProvider` reads
              today — becomes current again at the SOURCE. This is a pure write-side data-freshness fix (zero changes to
              `canonical_perp_funding_provider.py` or any strategy-service read path), so it carries NONE of the determinism
              risk a reader-side fallback would, and it converges toward the operator's one-source-of-truth goal more directly
              than adding a second read path ever would — if the corpus stays fresh going forward, the reader-side fallback
              idea evaluated above may never actually be needed.
