---
doc_type: plan
title: CeFi Completion Program — close the honest-coverage gaps to genuinely-done
summary:
  Coordinator plan-of-record for driving CeFi to actually-done honest coverage — the 9 workstreams surfaced by the
  2026-07-15 completion audit (recent-tail backfill, 403 re-capture sweep, legacy-alias kill, HYPERLIQUID finish,
  liquidations SSOT fix, DERIBIT-COMBO historical backfill, equity-perp Phase 2, canonicalisation G5, EXTENDED-STARKNET
  book5). LOCAL/autonomous execution — this session drives all workstreams on a loop; the Progress Log is the memory of
  record across context compression.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, honest-coverage, backfill, canonicalisation, manifest, liquidations, equity-perp, autonomous]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    issues/tardis_concurrent_ip_lockout_2026_07_12.md,
    issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 11.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# CeFi Completion Program — close the honest-coverage gaps

> **Dispatch**: operator 2026-07-15 — "make the plans then execute yourself /autonomous". Verify-then-**auto-delete**
> for legacy aliases (workstream C), **excluding DERIBIT-COMBO**. Runs under `AUTONOMOUS_AGENT_RULES.md` (finish to
> DONE, no DEFERRED/BLOCKED-OPERATOR leftovers, full chicken-and-egg authority) on a self-paced loop. Model: Opus 4.8
> (1M).

## Brief — what "done" means

The 2026-07-14 honest-coverage manifest reads CeFi 99.27% / `expected_unattempted=0`, but that is measured against an
`INCOMPLETE` denominator that hides three real gaps: (1) every main Tardis venue is empty after ~2026-05-23; (2) 17,103
MVP `attempted_failed` remain (mostly stale Tardis-403 lockout noise, but the drive-to-zero gate is NOT met); (3) equity
perps are catalogued but never tick-captured. **DONE = the honest-coverage recompute for CeFi shows
`denominator_complete: true`, `expected_unattempted=0` against the FULL/current MVP denominator, `attempted_failed=0`
(genuine — after lease-serialized re-capture clears the 403 class), the recent tail is filled to `now-2` for all main
venues, and the legacy-alias / instrument_type-casing strays are gone.**

## Codex SSOTs (read before touching a workstream — plan↔codex drift is review-blocking)

- `codex/02-data/cefi-capture-universe.md` — two-layer model + perp-gate + `CeFiMvpRule` (the denominator predicate).
- `codex/02-data/availability-manifest-and-data-status.md` — 4-state capture_status, `expected_unattempted` writer.
- `codex/02-data/honest-coverage-model.md` — two-layer / two-view / instrument-gates-download.
- `codex/02-data/pipeline-mode-partition.md` — `{mode}_{source}` partitioning (readers prefix-match).
- `codex/05-infrastructure/vm-launcher-runbook.md` (§ Tardis cap 3) + `…/spot-vms-for-backfill.md`.
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns the catalogue; MTDS derives capture.

## Findings evidence (from the 2026-07-15 audit — see Progress Log for the raw queries)

- Recent-tail cliff: main Tardis venues drop 15→9→1 across 2026-05-22→05-26; only
  ASTER/EXTENDED-STARKNET/PACIFICA-SOLANA (+COINBASE-CDE/DERIBIT-COMBO) exist on recent days. HYPERLIQUID stops
  ~2026-06-23.
- BITGET-FUTURES: 174,386 captured; residual fails ~92% Tardis-403 + blank-instrument_type accounting bug; last fail
  2026-05-22. Already-run — needs re-census, not re-run.
- HYPERLIQUID fails = 1,277 `phantom_captured_no_parquet_at_canonical_path` + 206 writer pre-write validation — ID churn
  `:PERP:BTC`→`:PERPETUAL:BTC-USD@LIN`; same root as the 176-row catalogue dedup defect. Path problem, not data.
- funding: present inside `derivative_ticker` (cols funding_rate/predicted_funding_rate/open_interest/mark_price) — no
  separate feed needed; `funding_rate`/`perp_funding` data_type is redundant/near-empty.
- liquidations: densely captured (1.02M raw manifest rows) but excluded from `CeFiMvpRule` — SSOT contradiction vs the
  un-superseded `mvp-universe.yaml` (P1-critical).

---

## Workstreams (todos) — dependency-ordered; T0 (UAC) code first, then backfills, then cleanup, then close

### Phase 1 — code / SSOT fixes (fast; correct the denominator before re-measuring)

- [ ] [DATA] P0. **E — liquidations SSOT fix.** Add `liquidations` to `CeFiMvpRule.data_types` for the venue/itype cells
      where a Tardis liquidations feed genuinely exists (perp venues with a liq channel; NOT HL — no liq feed; NOT
      spot). Bump `MVP_SCOPE_CONFIG_VERSION`. Supersede/reconcile the `mvp-universe.yaml` (2026-03-04) vs
      `mvp-scope-canonical.md` contradiction. UAC + codex. Evidence: uac@<sha> + a `data_type_capability` cross-check +
      codex update.
- [ ] [DATA] P1. **I — EXTENDED-STARKNET book5.** Registry says `book_snapshot_5` batch_capable=True but 0 captured.
      Diagnose (adapter vs capability drift), fix so book5 is either captured or honestly-typed. UAC/MTDS. Evidence.
- [ ] [BACKEND] P1. **G-code — equity-perp Phase 2 type-stamp.** IS: stamp `EQUITY_PERP` on the 70 catalogued equity
      perps (Binance/OKX/Bybit + fleet) via `CEFI_EQUITY_PERP_BASE_UNIVERSE`/`crypto_equity_link`; fix the ASTER-only
      legacy-row dating bug (`ASTER:PERP:*` uniform venue-launch `available_from`). instruments-service. Evidence.
- [ ] [BACKEND] P1. **D-code — HYPERLIQUID dedup + phantom-path logic.** IS catalogue: alias old HL IDs / add
      rename-detection to `_merge_incremental` so the 176 `:PERP:`/`:PERPETUAL:…@LIN` rows collapse to one lineage.
      MTDS: make the phantom-audit resolve the `@LIN` canonical path (or re-point/relocate) so the 1,277 phantoms clear.
      Evidence: is@<sha> + mtds@<sha> + catalogue dedup verified.

### Phase 2 — data / backfill (under the Tardis cap-3 lease; SPOT VMs)

- [ ] [INFRA] P0. **A — recent-tail main-venue backfill (2026-05-24 → now-2).** Launch lease-serialized Tardis backfill
      for BINANCE(-SPOT/FUTURES), OKX(-SPOT/SWAP/FUTURES), BYBIT, UPBIT, KRAKEN(-SPOT/FUTURES), BITGET(-SPOT/FUTURES),
      BITFINEX(-SPOT/FUTURES), COINBASE-SPOT, DERIBIT. `TARDIS_CONCURRENCY_LEASE=1`, `--provisioning-model=SPOT`, per-VM
      shards. Monitor to STOPPED. Evidence: manifest rows for the tail range, per venue.
- [ ] [INFRA] P0. **B — 403 re-capture sweep + af-census → 0.** Re-run the MVP `attempted_failed` shards under the lease
      (clears the stale 403 class), then re-census. Closes `mvp_backfill_cefi_tick_v10` final gate
      ("attempted_failed=0"). Also clears the blank-instrument_type + lowercase-casing legacy fail rows (forward-write
      already fixed). Evidence: coverage recompute att_fail delta.
- [ ] [INFRA] P1. **F — DERIBIT-COMBO historical `by_date` backfill.** Routing bugs already fixed; the historical
      catalogue is starved — design + run the by_date backfill so `(DERIBIT-COMBO, trades/options_chain)` closes. KEEP
      this venue (do NOT alias-kill it). Evidence.
- [ ] [INFRA] P1. **G-tick — equity-perp tick download.** After G-code type-stamp, wire + run the tick capture for the
      70 equity perps from each instrument's per-instrument `available_from` (pre-listing stays empty_confirmed).
      Evidence.
- [ ] [INFRA] P1. **D-tail — HYPERLIQUID tail + phantom re-capture.** Fill HL from ~2026-06-24 → now-2 and re-capture
      the 1,277 phantom dates to the `@LIN` canonical path. Evidence.

### Phase 3 — cleanup (only after Phase-2 data is verified present under canonical names)

- [ ] [DATA] P1. **C — kill legacy venue aliases (verify → migrate → auto-delete), EXCEPT DERIBIT-COMBO.** For
      OKEX/OKEX-SWAP/OKEX-FUTURES, BYBIT-FUTURES, COINBASE-INTERNATIONAL, bare BINANCE/BITFINEX/BITGET/KRAKEN,
      CRYPTOFACILITIES, and the lowercase-itype strays (`spot`/`spot_pair`/`perpetual`): (1) verify every aliased
      shard's data already exists under the canonical venue+UPPERCASE itype; (2) migrate any genuinely-unique data; (3)
      **auto-delete** the alias manifest rows + GCS objects; (4) re-consolidate the index. Evidence: pre/post row
      counts + GCS deletion manifest. **DERIBIT-COMBO is a legit distinct venue — never delete it.**

### Phase 4 — close + prove

- [ ] [DATA] P0. **H — canonicalisation G5 + final honest-coverage recompute.** Drive `master_data_canonicalisation` G5
      ("backfill → 100% honest coverage") for cefi; re-enumerate the denominator (`enumerate_expected_universe.py`) so
      it reflects liquidations + equity perps + the filled tail; run `compute_honest_coverage`; confirm CeFi
      `denominator_complete: true`, `expected_unattempted=0`, `attempted_failed=0` (genuine). Evidence: the new
      `coverage.json`.
- [ ] [REVIEW] P0. **Final audit + report.** Rule-9 report in this plan: verified end-state per venue/data_type, every
      forced tradeoff, every genuine impossibility. Post-plan codex audit (update cefi-capture-universe /
      honest-coverage docs on any contract change). Nothing left for the operator to pick up.

---

## Progress Log (append-only — this is the loop's memory across context compression)

### 2026-07-15 — program authored

- Completion audit run (see chat): 4 research sub-agents + direct GCS/manifest analysis. Downloaded
  `availability_index.parquet` (11.25M rows, cefi) + `expected_universe_ranges.parquet` + `coverage.json` (2026-07-14,
  latest full cefi snapshot) to scratchpad. Key numbers captured in "Findings evidence" above.
- Operator answered: execute yourself `/autonomous`; aliases = verify + auto-delete (except DERIBIT-COMBO).
- Plan-of-record created. Next: Phase-1 workstream E (liquidations SSOT), then arm the loop.
