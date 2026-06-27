---
doc_type: plan
title: "MVP backfill — CeFi trades+book5 (perp-gated) + Deribit options_chain ONLY (SPOT, budget-tightest)"
summary:
  "Backfill CeFi trades + book_snapshot_5 for the v10 perp-gated MVP universe and Deribit BTC/ETH options as
  options_chain ONLY (the big cost saver), on SPOT VMs, majors-first, reconcile-then-fill."
nature: process
stage: [data-ingestion]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, cefi, trades, book-snapshot-5, options-chain, deribit, spot-vm, v10, budget-aware]
related: []
created: 2026-06-27
parent_epic: cefi_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on: [mvp_catalogue_finalization_v10_2026_06_27]
related_plans:
  - plans/active/mvp_catalogue_finalization_v10_2026_06_27.md
  - plans/active/cefi_manifest_canonicalisation_2026_06_01.md
  - plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md
  - plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md
asset_group: cefi
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Part of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
>
> **🟡 GATED on Phase 0** — does NOT begin until `mvp_catalogue_finalization_v10_2026_06_27.md` signs off a v10-correct
> **cefi** catalogue (perp-gate applied; BINANCE-DELIVERY dropped; LIGHTER/EXTENDED/PACIFICA tagged CeFi). MTDS resolves
> the per-venue MVP-gated universe from the IS by_date snapshot — a stale catalogue = wrong universe.
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `codex/02-data/mvp-scope-canonical.md`. This
> plan REFERENCES it. **The single most important v10 cut: CeFi OPTION = `options_chain` ONLY** (Deribit BTC/ETH);
> per-strike trades + book_snapshot_5 are EXCLUDED — this collapses the heavy-instrument count ~275K→~14K. Any older
> cefi plan that says options need trades+book5, or that lists BINANCE-DELIVERY, or LIGHTER/EXTENDED/PACIFICA as DeFi,
> is stale and SUBORDINATE (see Phase-4 reconciliation).

## Codex SSOTs (READ before executing)

- `codex/02-data/mvp-scope-canonical.md` § CeFi — venues (incl. LIGHTER-ZKSYNC/EXTENDED-STARKNET/PACIFICA-SOLANA);
  data_type cut (trades + book_snapshot_5 + funding for spot/perp/dated-future/equity-perp; **OPTION = options_chain
  ONLY**); the **perp-gate** (`is_in_mvp_capture_universe`/`has_perp_for_base` — a SPOT/dated-FUTURE is in the capture
  universe ONLY IF the venue lists a perp for the base; PERP/EQUITY_PERP self-qualify; UPBIT spot +
  `STAKING_SPOT_EXCEPTION` carve-outs); **NOT MVP = BINANCE-DELIVERY**; deferred-no-source = HL trades pre-2025-03-22,
  ASTER book5+liquidations.
- `codex/02-data/cefi-capture-universe.md` — the perp-gate layer.
- `codex/02-data/honest-absence-downstream-handling.md` — 401≠honest-absence; expiry-window pre-filter for dated
  futures/options; DERIBIT-COMBO historical = `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` (do NOT re-attempt); HL/ASTER
  deferred-no-source reasons.
- `codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default.
- `plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` — HL/ASTER honest-absence treatment (already
  shipped).

## Definition of 100%

`captured` covers 100% of the v10 cefi MVP could-exist universe → `attempted_failed = 0` AND `expected_unattempted = 0`.
Honest `empty_confirmed` excluded (pre-venue-launch, expiry-window, 401-rotated cells are `attempted_failed` NOT empty,
deferred-no-source HL/ASTER cells are typed empty). Genuine source-unavailable → honest-empty + documented, never
BLOCKED.

## Budget posture (CeFi tick is the ONLY big cost — scope it TIGHTEST)

- CeFi trades+book_snapshot_5 (Tardis tick) is the workspace's only material backfill cost. After the v10 Deribit cut
  (options = options_chain only) the heavy-instrument count is ~14K (was ~275K) — the cut IS the cost saver.
- **Launch cheapest+highest-value first; majors first.** Order: (1) Deribit options_chain (tiny, high-value, the saver);
  (2) funding/derivative_ticker light data_types (cheap); (3) trades+book5 for the perp-gated majors per venue, oldest
  gaps last. SPOT VMs only (preemption-safe; per-shard manifest resume). Use `FREE_ONLY=1` for a cheap first pass if a
  Tardis key is constrained, then fill the paid tier.

---

## Todos (SEQUENTIAL phases; within a phase the owning agent may parallelize across venues/years)

### G0 — gate + reconcile

- [ ] [SCRIPT] P0. Confirm Phase-0 cefi catalogue sign-off (perp-gate applied, BINANCE-DELIVERY absent,
      LIGHTER/EXTENDED/PACIFICA CeFi, Deribit OPTION carve-out). **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows cefi G3 green. If not signed off → wait
      (task-level prereq). Also confirm the in-flight cefi remediation agent + the 06-26 partial-capture re-capture
      (Phase-4 a163/G1.2) are resolved so the catalogue active counts are correct (e.g. BINANCE-FUTURES is NOT ~47).
      SPOT N/A.
- [ ] [SCRIPT] P0. Build the cefi gap report for the v10 MVP universe, split by data_type class: (a) Deribit BTC/ETH
      **options_chain**; (b) **trades + book_snapshot_5** for perp-gated spot+perp+dated/fixed-delivery futures +
      equity-perps (EXCLUDING BINANCE-DELIVERY); (c) **funding** (derivative_ticker/funding_rate). Repos:
      `instruments-service`, `e2e-testing`. **Run:** `python scripts/measure_honest_coverage.py --asset-group cefi` +
      read `by_venue_data_type`; list (venue, year, group) cells with `attempted_failed>0` / `expected_unattempted>0`.
      **Gate:** gap list written to Progress Log, ordered cheapest-first, majors-first; confirm Deribit per-strike
      trades/book5 are NOT in the universe (v10 options_chain-only). SPOT N/A.

### G1 — Deribit options_chain ONLY (the cost saver — do this first)

- [ ] [SCRIPT] P0. Backfill Deribit BTC/ETH **options_chain ONLY** (NOT trades/book5). Repo: `deployment-service`.
      **SPOT VMs only** (`launch-targeted-options-chain-backfill.sh` defaults SPOT). **Run:**
      `bash scripts/vm/launch-targeted-options-chain-backfill.sh --venue DERIBIT --dry` to inspect, then
      `--venue DERIBIT --commit` (BTC;ETH, years 2020-2026; `VM_DATA_TYPES=options_chain` is fixed in the launcher;
      chain-glob expands strikes/expiries server-side). Do NOT launch Deribit trades/book5 — that is the explicitly
      excluded cost. **Gate:** Deribit options_chain attempted_failed=0; VMs self-stop; verify T+10min
      `gcloud compute instances list --filter='name~opt-deribit' --zones=asia-northeast1-c`. SPOT VMs only.

### G2 — funding / light data_types (cheap)

- [ ] [SCRIPT] P0. Backfill funding (derivative_ticker / liquidations / futures_chain light group) for the perp-gated
      MVP venues. Repo: `deployment-service`. **SPOT VMs only.** Use `launch-cefi-sharded-backfill.sh` scoped to the
      light group + gap venues/years from G0
      (`VENUES="..." YEARS="..." bash scripts/vm/launch-cefi-sharded-backfill.sh`; the light data groups
      `DATA_LIGHT_PERPS`/`DATA_LIGHT_DERIBIT` are cheap). **Gate:** funding/light attempted_failed=0 across MVP perp
      venues; verify T+10min. SPOT VMs only.

### G3 — trades + book_snapshot_5 (the heavy cost — majors first, tightest scope)

- [ ] [SCRIPT] P0. Backfill **trades + book_snapshot_5** for the perp-gated MVP universe, MAJORS FIRST. Repo:
      `deployment-service`. **SPOT VMs only** (`launch-cefi-sharded-backfill.sh` defaults SPOT; per-VM shard isolation +
      manifest resume = preemption-safe). MTDS `TardisAdapter._resolve_symbols` resolves the perp-gated MVP universe
      from the IS by_date snapshot (no hardcoded symbols). **Order:** launch the major venues + recent years first
      (`VENUES="BINANCE-FUTURES BINANCE-SPOT BYBIT OKX-SWAP OKX-SPOT" YEARS="2026 2025"`), then widen to the full v10
      venue set (KRAKEN/COINBASE/BITFINEX/BITGET/UPBIT + LIGHTER/EXTENDED/PACIFICA) and older gap years. EXCLUDE
      BINANCE-DELIVERY. Throttle with `MAX_CONCURRENT`; relaunch OOM-killed heavy shards via
      `ONLY="venue:year:heavy" MACHINE_TYPE_HEAVY=e2-highmem-16 FORCE=1`. **Gate:** trades+book5 attempted_failed=0
      across the perp-gated MVP universe; verify T+10min
      `gcloud compute instances list --filter='name~(cefi).*-(heavy|light)' --zones=asia-northeast1-c`.
      No-fire-and-forget (≥1 progress/hr per wave). SPOT VMs only.
- [ ] [SCRIPT] P0. HYPERLIQUID + ASTER perp trades/book5 gap-fill with the deferred-no-source carve-outs honored. Repo:
      `deployment-service`. **SPOT VMs only.** Use `launch-cefi-hl-aster-historical-backfill.sh` (HL S3 + ASTER REST;
      `VM_OPERATION=collect-onchain-perp-batch`). **Honor v10 deferred-no-source (typed honest-empty, do NOT mark
      attempted_failed):** HL **trades pre-2025-03-22** → `EXPECTED_PRE_SOURCE_COVERAGE_START` (HL S3 has no trades
      before then); ASTER **book_snapshot_5 + liquidations** → `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` (live-only;
      the handler auto-excludes; already shipped per the HL/ASTER issue doc). **Gate:** HL/ASTER in-source-coverage
      trades attempted_failed=0; the deferred cells are typed `empty_confirmed`, never silent. Verify T+10min. SPOT VMs
      only.

### G4 — verify honest-complete

- [ ] [SCRIPT] P0. Final cefi MVP verification: across the v10 perp-gated MVP universe, attempted_failed=0 AND
      expected_unattempted=0 for trades+book5+funding; Deribit OPTION present as options_chain ONLY (0 per-strike
      trades/book5 cells); every absence typed honest (pre-venue-launch / expiry-window / deferred-no-source). Repos:
      `instruments-service`, `e2e-testing`. **Run:** `python scripts/measure_honest_coverage.py --asset-group cefi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group cefi --mode full`;
      `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run`. **Gate:** both failure
      buckets zero; 0 phantom; 401-class cells re-attempted (attempted_failed not empty); verdict to Progress Log.
      **Full-execution criterion:** VM-list + coverage CLI output recorded per wave. SPOT N/A.

---

## Progress Log

_(append gap report + per-wave verification here)_
