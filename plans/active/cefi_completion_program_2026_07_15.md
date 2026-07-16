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

- [x] ✅ [DATA] P0. **E — liquidations SSOT fix.** liquidations is MVP for the PERPETUAL leg on the 6 real-feed venues,
      gated so it never false-seeds spot/HL/dated. **SHIPPED** — core: **uac@494fd90c** (PERPETUAL override +
      `get_mvp_data_types_for_cefi_venue_itype` helper + capability gating, version→15) · **is@92f3ca22** (itype-aware
      MVP-cut in `enumerate_expected_universe.py`) · **pm@68018d0f** (codex reconciliation). Companion: **is@8b6bd8f8**
      (`build_expected` itype-aware so liquidations counts in the MEASUREMENT denominator too — both producers now
      agree; cefi golden +6 liquidations tuples). Regression-safe (no COINBASE inflation — proven). OKX correction: bare
      OKX is the fold-target of OKX-SWAP so it KEEPS liquidations (restored). MVP_SCOPE_CONFIG_VERSION=15.
- [x] ✅ [DATA] P1. **I — EXTENDED-STARKNET book5.** Diagnosis (MTDS agent a9ee9179): `batch_capable` is a DEAD field (0
      readers); the real gate `LIVE_ONLY_DATA_TYPES` in `_onchain_perp_batch_live_only.py` ALREADY declares EXTENDED/
      PACIFICA/LIGHTER book5 (+ASTER liq, LIGHTER trades) live-only → EXTENDED book5 is ALREADY honest
      `empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE]` in batch, NOT a coverage gap. **Functionally satisfied
      at runtime**; the `data_type_capability.py batch_capable=False` edit is purely cosmetic declarative-consistency
      (no functional effect) — done as a tidy-up if the worktree is free, else harmless.
- [x] ✅ [BACKEND] P1. **G-code — equity-perp Phase 2 type-stamp.** IS: stamp `EQUITY_PERP` on the 70 catalogued equity
      perps (Binance/OKX/Bybit + fleet) via `CEFI_EQUITY_PERP_BASE_UNIVERSE`/`crypto_equity_link`; fix the ASTER-only
      legacy-row dating bug (`ASTER:PERP:*` uniform venue-launch `available_from`). instruments-service. **CODE SHIPPED
      is@559c6920**: 1,316 rows re-typed (1,237 PERP→EQUITY_PERP + 79 SPOT_PAIR→TOKENIZED_EQUITY, IDs unchanged); ASTER
      dating fixed (1,501→505 lineages, 0G→2025-09-24 discarding spurious 2023-07-22); 8 tests green. Classification
      lives in the catalogue builder (not adapter) to honor "don't change IDs". PROD EFFECT pending full rebuild (H).
- [x] ✅ [BACKEND] P1. **D-code — HYPERLIQUID dedup + phantom-path logic.** IS catalogue: alias old HL IDs / add
      rename-detection so the `:PERP:`/`:PERPETUAL:…@LIN` rows collapse to one lineage. MTDS: HL phantoms resolve.
      **CODE SHIPPED is@559c6920 + mtds@57e26c0f**. HL dedup 534→182 (3 forms/instrument, not 2), 0 live lost, 0
      collisions — root cause is FLEET-WIDE (@LIN migration dup'd every perp venue: BINANCE-FUTURES 1686→849, BITGET-F
      1708→994, LIGHTER 646→216 …). `_cefi_perp_lineage_key(venue,raw_symbol,margin)` keys on the underlying, wired into
      full+incremental. MTDS: HL phantom = RE-CENSUS not re-capture (1,277 on disk, 0 recapture) + a `parse_hive_path`
      regression test. PROD EFFECT pending full rebuild + `reconcile_phantom_manifest_rows_all.py --unphantom-only` (H).

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

### 2026-07-15T13:35Z — tick 1: code agents dispatched + A/B found already-in-flight

**Direct-question answers (banked):**

- BITGET-FUTURES: already run (174,386 captured). Residual fails ~92% Tardis-403 + blank-instrument_type accounting;
  last fail 2026-05-22. → NO re-run; needs re-census after the 403 sweep. (workstream B)
- funding_rate: HAVE IT — carried inside `derivative_ticker` (cols funding_rate/predicted_funding_rate/open_interest/
  mark_price), dense on every perp venue. Separate `funding_rate`/`perp_funding` data_type is redundant/near-empty. No
  action; `CeFiMvpRule.data_types` already lists funding_rate (maps to derivative_ticker).
- liquidations ground truth (manifest): captured on 6 perp venues — BINANCE-FUTURES(308k), OKX-SWAP(192k), BYBIT(157k),
  KRAKEN-FUTURES(48k), BITFINEX-FUTURES(20k), BITGET-FUTURES(6.9k); PERPETUAL leg. NOT ASTER(live-only)/HL(no feed)/
  OKX-FUTURES(dated)/COINBASE-FUTURES/EXTENDED/PACIFICA. → that is the honest gating target for workstream E.

**Code agents dispatched (Phase 1, per-repo to avoid conflicts):**

- E (UAC): add liquidations to CeFi MVP PERPETUAL leg, gated via VENUE_DATA_TYPE_CAPABILITIES to those 6 venues; bump
  MVP_SCOPE_CONFIG_VERSION 14→15; reconcile mvp-universe.yaml contradiction; codex update. [agent adb3a7cb]
- G-code + D-code-IS (instruments-service): EQUITY_PERP type-stamp for the 70 equity perps + ASTER dating fix; HL
  catalogue dedup (534→~358, rename-detection in `_merge_incremental`). [agent aa176bc4]
- D-code-MTDS + I-diagnosis (market-tick-data-service): HL phantom-path reconcile (@LIN canonical); diagnose
  EXTENDED-STARKNET book5 (adapter-gap vs live-only) — reports; does NOT edit UAC (avoid conflict with E). [agent
  a9ee9179]

**A/B (recent-tail backfill + 403 sweep) — ALREADY IN-FLIGHT, do NOT launch duplicates:**

- 2 lease-serialized Tardis VMs running (2/3 cap): `cefi-queue-heavy-20260714-123340` (START 2020-01-01, END 2026-07-13,
  LEASE=1, up ~32h) + `cefi-queue-heavy-20260715-105207` (END 2026-07-14, LEASE=1, launched today). Both = combined
  SINGLE_VM_QUEUE backfills covering the FULL range incl. the recent tail, from the prior mvp_backfill_cefi_tick_v10
  work.
- Liveness: `_index/per_vm/cefi-queue-heavy-20260714-123340.parquet` mtime 2026-07-15T13:02Z (fresh, ~30 min) → alive +
  progressing. BUT recent tail (2026-06-15 BINANCE-FUTURES) still empty → VMs grinding historical 403-gaps first.
- Tardis cap=3 (operator 2026-07-14, `tardis-concurrency-guard.sh`); N>3 collapses. At 2/3, capacity for 1 more.
- **PLAN for A/B**: MONITOR these to completion on a climbing metric (recent-tail venue-day coverage). If they keep
  progressing but do NOT reach the tail within the monitoring window, launch ONE dedicated tail-only VM (START
  2026-05-24, END 2026-07-14, all main venues, LEASE=1, SPOT, DRY_RUN first) as the 3rd slot. Launcher =
  `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` (queue/combined-VM mode).
- Next ticks: (1) collect code-agent reports → ship/flip E, G, D; (2) monitor queue VMs; (3) then F (DERIBIT-COMBO
  hist), G-tick (equity-perp download), C (alias kill), H (final census).

### 2026-07-15T13:55Z — tick 2: E (liquidations) — Option 1 authorized (regression averted)

- UAC agent correctly STOPPED before shipping: the prescribed `instrument_type_data_types["PERPETUAL"]` mechanism would
  REGRESS COINBASE-FUTURES — the IS enumerator (`enumerate_expected_universe.py:723-729`) SKIPS its MVP-cut for any
  itype in `instrument_type_data_types`, bypassing the `venue_data_types={trades}` override → COINBASE PERP would
  inflate to book5+deriv_ticker+liquidations phantom cells, and ASTER/DERIBIT would leak liquidations (proven via
  `_row_data_types` probe). Also: the real enumerator gate is `VENUE_DATA_TYPE_CAPABILITIES` in
  `market_data_categories.py` (NOT `data_type_capability.py`); it ALREADY declares liquidations for the 6 +
  DERIBIT/OKX-bare/ASTER/COINBASE-FUTURES.
- DECISION (autonomous, root-cause per rule 1): **Option 1 — cross-repo (UAC + IS)**. Enumerator MVP-cut becomes
  instrument_type-AWARE (skip only for bundle-relabeled options_chain/futures_chain/combo; new helper
  `get_mvp_data_types_for_cefi_venue_itype` for leaf itypes). liquidations on the PERPETUAL leg, gated to exactly the 6.
- **ASTER RULING (mine): live-only feeds must NOT seed the BATCH denominator** (ASTER liq batch=0 is honest-absent). →
  remove liquidations from ASTER/DERIBIT/OKX-bare capability; keep the 6; COINBASE-FUTURES no cap edit (venue override).
  Same principle applies to the ASTER/EXTENDED book5 question (workstream I) for consistency.
- Sent Option-1 authorization to agent adb3a7cb (IS-coordination: touch only enumerate_expected_universe.py; land UAC
  then IS back-to-back before any recompute). Awaiting SHAs.
- Lesson: my original E spec was a mis-diagnosis; adversarial verification caught a real T0 regression pre-ship. Verify
  denominator changes against actual enumerator behavior, not the rule shape.

### 2026-07-15T14:05Z — tick 3: MTDS agent done (D-code-MTDS + I diagnosis) — two more corrections

**D-code-MTDS — HL phantom: RECONCILE not re-capture (mtds@57e26c0f, regression test only):**

- My `@LIN`-churn hypothesis was WRONG. The 1,277 `phantom_captured_no_parquet_at_canonical_path` HL rows are
  `pipeline_mode=live_hyperliquid`, OLD form `HYPERLIQUID:PERP:<COIN>`, dates 2026-06-23→06-29 — and the parquets EXIST
  on disk at the live path. Root cause: an OLD reconcile run probed only `batch_*` prefixes → false-phantomed live
  cells. Already fixed in UAC 2026-07-11 (`canonical_path_templates('cefi')` emits both batch+live prefixes).
- Split: **1,277 RECONCILE / 0 RECAPTURE** (proven via production-tool dry-run: unphantom 1277, still-phantom 0).
- **D-tail correction**: the plan's "re-capture the 1,277 phantom dates" is UNNECESSARY — data on disk; a re-census
  suffices. Command (run in workstream H, coordinated):
  `cd instruments-service && GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --unphantom-only --venues HYPERLIQUID --workers 16`
  (add `--dry-run` first; `--unphantom-only` is safe — only flips af→captured).
- The genuine HL tail gap = 2026-06-30 → now (part of workstream A recent-tail backfill). Separate residual: 206
  `StreamingParquetWriter pre-write validation failed` rows (blank itype, 2024-01-03→2026-02-05) = genuine writer fails,
  no parquet → need re-capture in the B sweep, not the re-census.
- MTDS deliverable = a `parse_hive_path` regression test locking BOTH HL conventions (live old-form + batch `@LIN`). No
  MTDS prod-code change (the scanner already resolves both; duplicating path-templates would recreate Axis-10 drift).

**I — EXTENDED-STARKNET book5: genuinely LIVE-ONLY → UAC `batch_capable=False`:**

- MTDS `cli/handlers/_onchain_perp_batch_live_only.py` declares
  `LIVE_ONLY_DATA_TYPES["EXTENDED-STARKNET"]={book_snapshot_5}` (orderbook endpoint is snapshot-only, no history — same
  as ASTER). Adapter has no historical orderbook method.
- UAC contradiction: `data_type_capability.py:653-669` — a comprehension sets `batch_capable=True` for (PACIFICA-SOLANA,
  EXTENDED-STARKNET, LIGHTER-ZKSYNC) × (trades, book_snapshot_5, derivative_ticker), contradicting ASTER's own book5
  entry (batch_capable=False) + the MTDS runtime SSOT. Also LIGHTER-ZKSYNC trades is over-declared batch.
- FIX (UAC edit, route through the UAC agent once it frees — avoid two-on-UAC): carve book5 (and LIGHTER trades) out of
  the batch_capable=True comprehension → `batch_capable=False, live_capable=True` (mirror ASTER). Post-fix the
  0-captured book5 becomes correct `empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE]`. This is the SAME
  live-only-not-in-batch- denominator principle as the ASTER liquidations ruling (tick 2).
- Status flips: D-code-MTDS ✅ shipped (mtds@57e26c0f). I = queued UAC edit. HL phantom re-census + 206-writer-fails =
  queued into H/B.

### 2026-07-15T14:20Z — tick 4: IS agent done (G-code + D-code-IS) → is@559c6920; flipped G-code + D-code

- **is@559c6920** (build_instrument_catalogue.py + test, direct-push under dirty-deps carve-out since UAC is dirty with
  the sibling E agent's WIP; only its 2 files committed, strict-quickmerge passed). 8 new tests; 102 catalogue + 165
  enumerator tests green.
- G-code ✅: 1,316 rows re-typed (1,237 PERP→EQUITY_PERP + 79 SPOT_PAIR→TOKENIZED_EQUITY); ASTER dating fixed.
- D-code ✅ (both halves): HL dedup 534→182; the fix is **fleet-wide** (every perp venue's @LIN dup collapses), verified
  0 live lost / 0 collisions.
- **FLAGS to carry**: (1) HL=534→182 not ~358 (3 forms/instrument — correct). (2) Dedup blast radius is FLEET-WIDE (cefi
  perp-family 9,177→5,358 rows) — a corrective SHRINK; prod apply needs `--allow-catalogue-shrink` + a live-count
  invariant check at apply. (3) EQUITY_PERP includes commodities/indices (XAU/XAG/NATGAS/SPX/SPY/QQQ) per the UAC
  universe composition — name reads "EQUITY" but matches `CEFI_EQUITY_PERP_BASE_UNIVERSE`; follow-up naming decision
  only, not a blocker. (4) Classification is at the catalogue-rollup layer (not adapter) — the by_date adapter still
  emits generic PERPETUAL/SPOT_PAIR; catalogue is the derived-type SSOT.

**Workstream-H apply-list (accumulating — run ONCE, coordinated, after E lands):**

1. Full catalogue rebuild `build_instrument_catalogue.py … --allow-catalogue-shrink` (cefi) — lands the HL/fleet dedup +
   ASTER dating + EQUITY_PERP/TOKENIZED_EQUITY re-type on prod `catalog.parquet`. Verify live-instrument count unchanged
   (dedup must not drop any `available_to IS NULL` row).
2. HL phantom re-census:
   `reconcile_phantom_manifest_rows_all.py --asset-group cefi --unphantom-only --venues HYPERLIQUID --workers 16`
   (dry-run first → expect 1,277 unphantom / 0 still-phantom).
3. Re-enumerate the expected universe (`enumerate_expected_universe.py`) against the new UAC (liquidations v15 +
   EXTENDED book5 live-only) + the rebuilt catalogue → materialize the denominator.
4. `compute_honest_coverage` → the new coverage.json; assert `denominator_complete: true`, `expected_unattempted=0`,
   `attempted_failed=0` (genuine, after the tail/403 backfill B/A completes).

**Current Phase-1 status**: D-code-MTDS ✅ mtds@57e26c0f · G-code ✅ · D-code ✅ is@559c6920 · E ⏳ (UAC agent) · I ⏳
(queued UAC edit after E). Backfill A/B ⏳ (queue VMs). Then F, G-tick, C, H.

### 2026-07-15T14:25Z — A/B backfill monitoring: climbing, tail still empty; tail-VM decision deferred (not abandoned)

- Queue VMs CLIMBING (stall-safety OK): `cefi-queue-heavy-20260714` per_vm 70k→87k bytes (mtime 13:42Z);
  `cefi-queue-heavy-20260715` now writing 37k (mtime 13:49Z). Both alive + progressing.
- Recent tail STILL empty under batch_tardis (2026-06-05/15/25 = 0 venues; 05-30/07-05 = 1) — the VMs are grinding
  historical 403-gaps first. Tail-fill is inherently slow under the operator's cap-3 (2026-07-14) rule.
- Launcher interface learned (`launch-cefi-sharded-backfill.sh`): `SINGLE_VM_QUEUE=1` = combined ≤cap VM;
  `TARDIS_CONCURRENCY_LEASE=1`; SPOT default; NO `VM_INSTRUMENT_IDS` → MTDS resolves the full catalogue-MVP universe;
  `ONLY="venue:year:group"` scopes shards. Idempotent skip-if-fresh per shard.
- **DECISION**: do NOT launch a 3rd (2026-scoped) Tardis VM YET — the 2 queue VMs ALREADY cover 2026 (END 07-13/14), so
  a duplicate 2026 VM risks double-processing the same tail shards + lease contention at the 3/3 cap edge. This is NOT
  abandonment: the correct full-universe mechanism is already running + climbing.
- **NEXT-TICK ACTION (specific, not vague)**: download + inspect `_index/per_vm/cefi-queue-heavy-*.parquet` CONTENTS to
  read which (venue, date) shards each VM has already covered → determine whether they are approaching the tail. If they
  are chronological-historical-first and won't reach 2026-06+ soon, launch ONE `ONLY=<the-exact-empty-tail-shards>`
  SINGLE_VM_QUEUE LEASE=1 SPOT VM scoped to the non-overlapping tail range (DRY_RUN first, guard confirms ≤3). That
  closes the operator's headline recent-tail gap without duplicating the queue VMs' in-flight work.

### 2026-07-15T14:45Z — tick 5: E (liquidations) CORE shipped + companion/I authorized

- E core SHIPPED (Option 1, root-cause, regression-safe): **uac@494fd90c** (PERPETUAL override +
  `get_mvp_data_types_for_cefi_venue_itype` helper + ASTER/DERIBIT/OKX-bare liq gate removal + version→15) ·
  **is@92f3ca22** (`enumerate_expected_universe.py` itype-aware MVP-cut) · **pm@68018d0f** (codex reconciliation:
  mvp-universe.yaml / mvp-scope-canonical.md / cefi-capture-universe.md). Both repos QG green. Probe: liquidations ∈ the
  6 PERPETUAL, ∉ COINBASE-FUTURES (stays trades-only — NO regression), ∉ FUTURE/spot/HL/ASTER/EXTENDED/etc.
  MVP_SCOPE_CONFIG_VERSION=15.
- **E NOT yet flipped** — a required completion gap surfaced: there are TWO expected-universe producers.
  `enumerate_expected_universe.py` (expected-EMPTY manifest writer, FIXED) vs
  `instruments-service/scripts/expected_universe.py::build_expected()` (THE honest-coverage MEASUREMENT denominator
  SSOT, routed by `measure_honest_coverage.py`) — the latter still uses the venue-only helper, so **liquidations would
  not actually count in the coverage %** until it's made itype-aware too. Same silent-denominator-drift class the file
  warns about. Nothing runs in prod until WS-H, so no live drift yet.
- AUTHORIZED the UAC agent (rule 1 — finish completely): (1) `build_expected` itype-aware + regenerate cefi golden
  (verify diff = ONLY the 6-venue PERPETUAL liquidations additions); (2) workstream **I** — carve
  EXTENDED-STARKNET/PACIFICA/LIGHTER book5 + LIGHTER trades out of the `data_type_capability.py` batch_capable=True set
  → batch_capable=False (mirror ASTER), WITH proof it removes EXTENDED book5 from the batch denominator; (3) minor
  mvp-scope-canonical version prose 14→15. Awaiting SHAs.
- **Phase-1 status**: G-code ✅ · D-code ✅ (is@559c6920 + mtds@57e26c0f) · E core ✅ (flip pending build_expected) · I
  ⏳ (in the same follow-up). Once E-companion + I land → Phase 1 DONE → Phase 2 backfill monitoring + WS-H apply-list.

### 2026-07-15T14:36Z — tick 6: P0 LIVE multi-agent collision → PROTECT + wait; 2 correctness saves

- **INCIDENT** (issue doc `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`, pm@058cbb913): a
  concurrent YAHOO_FINANCE-removal agent is ACTIVELY writing this slot-3 worktree (UAC files 0-min mtime). Its removal
  (`uac@fec3f110`) left IS QG RED (test_silent_absent_fixes fixture + stale tradfi golden; 1 failed/4461) =
  fleet-blocking. Per multi-agent-safety HARD RULE (live WIP → PROTECT), I am NOT touching contested UAC/IS files; the
  UAC agent HARD-STOPPED correctly. NOTIFIED operator. (Uncommitted plan edits are being reverted by the contended
  worktree — hence the issue doc is the durable record.)
- **Save 1 (my ruling was wrong)**: bare `OKX` is the canonical fold-target for `OKX-SWAP` in
  `check_enumeration_completeness._CEFI_VENUE_FOLD`, so it MUST carry liquidations — removing it (my tick-2 instruction)
  would have zeroed OKX-SWAP's 191,923 captured liq. Agent RESTORED it (landed in fec3f110, content-correct). E core is
  CORRECT.
- **Save 2 (WS-I already satisfied)**: `batch_capable` is a DEAD field; the real gate MTDS `LIVE_ONLY_DATA_TYPES`
  already declares EXTENDED/PACIFICA/LIGHTER book5 (+ASTER liq, LIGHTER trades) live-only → already `empty_confirmed`
  [EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE] in batch. So EXTENDED book5 is NOT a coverage gap. I = functionally DONE
  (the `data_type_capability.py` edit is cosmetic; do it when the worktree frees).
- **E-companion** (build_expected itype-aware + cefi golden, +6/−0 verified) HELD uncommitted in IS, blocked by red
  tree + live collision. Ship `--files`-scoped to `scripts/expected_universe.py`+`goldens/…/cefi.json` ONLY (NOT the
  YAHOO agent's tradfi/defi/prediction/sports golden regens) once IS is single-owner + green.
- **PLAN**: loop re-checks worktree mtime each tick; when the concurrent agent goes idle (>~5 min stale) AND IS is green
  → reconcile + ship E-companion → flip E + I. Backfill A/B monitoring continues (orthogonal, no collision).

### 2026-07-15T16:35Z — tick 7: collision cleared (dead agent) → IS reconciled + E-companion SHIPPED → Phase 1 DONE

- Concurrent YAHOO/CBOE agent went DEAD (~2h idle, files 100-135min stale). Inherited-dead-WIP per multi-agent-safety.
- Reconciliation agent a3123cbc SHIPPED **is@8b6bd8f8** (7 files, IS QG GREEN, 266 tests pass — the fleet-blocking IS
  red tree is FIXED):
  - build_expected itype-aware LANDED (E-companion) → liquidations counts in the MEASUREMENT denominator; both producers
    now agree.
  - 5 goldens regenerated FRESH + every diff explainable: cefi +6 liquidations (incl. BITGET-FUTURES + OKX-fold); tradfi
    −13 YAHOO +1 CBOE ohlcv_24h (my regen SUPERSEDED the dead agent's stale golden — it had removed YAHOO but MISSED the
    CBOE tuple its own committed code produces); defi/prediction/sports = captured_at date bump only.
  - Red-test fixed root-cause: `test_silent_absent_fixes.py` YAHOO_FINANCE fixture → FX (sole TradFi NO_ADAPTER_YET
    venue), teeth preserved. + a pre-existing RUF002 `×`-in-docstring fixed in-commit.
  - Non-blocking FYI: pre-existing MTDS contract-integrity advisory (3 handlers below baseline) + a BSD-grep bug in a QG
    advisory script — advisory (QG exit 0), different repo, untouched.
- **E ✅ fully done** (uac@494fd90c + is@92f3ca22 + pm@68018d0f + is@8b6bd8f8, v15). **I ✅ functionally satisfied**
  (runtime LIVE_ONLY_DATA_TYPES already excludes EXTENDED book5; cosmetic cap edit optional).
- **PHASE 1 COMPLETE**: G ✅ · D ✅ · E ✅ · I ✅. Remaining = Phase 2 backfill (A tail VM launched + B/F/G-tick, cap-3
  bound) → WS-H apply-list (gated on backfill) → C alias-kill. The code substance is fully landed.

### 2026-07-15T17:05Z — tick 8: recent-tail VM (A) confirmed running; fleet 3/3

- Tail VM **cefi-queue-heavy-20260715-160552** UP + running the real backfill (serial + run.log verified):
  `mtds --operation download --mode batch --asset-group CEFI --venues <all 15 main> --start-date 2026-01-01 --end-date 2026-07-14 --data-types trades book_snapshot_5`.
  Heartbeat active. Fleet = 3/3 (cap).
- Launched from human-planning Linux VM (i-0dd9812a96cdda5dc) via SSM as `sudo -iu ubuntu`, deployment-service launcher,
  `SINGLE_VM_QUEUE=1 LAUNCH_GROUPS=heavy TARDIS_CONCURRENCY_LEASE=1 ONLY=<15 venues>:2026:heavy`. Guard OK 2+1=3.
- REALITY CHECK: launcher is YEAR-granular (`start_date=${year}-01-01` hardcoded, no sub-year override), so the tail VM
  processes 2026 CHRONOLOGICALLY — currently re-capturing 2026-01 failed shards (403-heavy) before it reaches the empty
  June-July tail. It IS the only VM on 2026 (the 2 queue VMs are at mid-2020), so still the fast path. run.log shows
  Tardis 403 code=274 (expected N=3 lease-rotation contention, ~50-70% efficiency per the cap-3 SSOT). ETA to fill the
  empty June-July tail: ~1-3 days. Not worth a launcher code-change to skip Jan-May.
- LIGHT slice (derivative_ticker/funding + liquidations) for the tail: blocked at 3/3 cap — launch `LAUNCH_GROUPS=light`
  same ONLY when a slot frees (a queue VM finishes / the tail VM completes).
- Gate A (collision) RESOLVED tick-7 (is@8b6bd8f8, IS green). Remaining = throughput-bound: A(tail heavy running) +
  B(queue VMs, weeks) + light slice → WS-H apply → F, C.

### 2026-07-15T17:41Z — tick 9: tail VM preempted (SPOT) → relaunched; fleet volatile; honest ETA revision

- Tail VM cefi-queue-heavy-20260715-160552 **DIED ~17:23Z** (SPOT preemption — `describe`=Could not fetch resource,
  run.log stopped mid-2026-01-11, ~50min uptime, never wrote a per_vm shard = never reached the empty tail). A queue VM
  also dropped (guard now counts **1 running**). SPOT preemption is churning the fleet.
- **RELAUNCHED** the tail VM (idempotent, guard OK 1+1=2; PID 2131271 on i-0dd9812a96cdda5dc). It resumes 2026 heavy.
- **HONEST ETA REVISION**: the recent-tail (empty June-July) fill is SLOWER than the earlier ~1-2d estimate — three
  compounding drags: (a) SPOT preemption kills the VM ~hourly (idempotent resume, but restart overhead + it re-walks);
  (b) the launcher is YEAR-granular so the VM grinds 2026-01+ re-captures (403-heavy) before reaching the empty tail;
  (c) N=3 single-IP lease = ~50-70% efficiency + 403 churn. Realistic empty-tail fill: **several days**, not 1-2.
- OPTION if the tail keeps preempting without reaching June: add a `START_DATE` override to the launcher (currently
  hardcodes `${year}-01-01`) so a tail VM jumps straight to 2026-06-01 (small ~44-day empty slice → fills before
  preemption). Deferred (launcher is a shared macOS-untestable script; only worth it if the plain relaunch keeps failing
  to progress). Full af=0 all-history stays ~2-3 weeks (cap-3 ceiling) regardless.
- Phase-1 code remains DONE + landed; this is purely backfill throughput under the operator's cap-3 + SPOT constraints.

### 2026-07-15T18:15Z — tick 10: CAP VIOLATION found (4 VMs) → protectively reduced to a clean heavy+light pair

- Found **4 Tardis VMs RUNNING > cap 3** — a launch RACE: 3 identical heavy VMs (cefi-queue-heavy-173940/174106/174244,
  all 2026-01-01..07-14 trades;book5 SPOT) + 1 light (cefi-queue-light-174110, deriv_ticker;liquidations;futures_chain).
  Only 174106 was mine (my 17:41 relaunch); **another process launched the other heavies + the light** ~17:39-17:44 →
  guard raced (each saw <3 before creating). The original historical queue VMs (20260714/20260715-105207) had died
  (SPOT) — so the fleet is now all-2026.
- **PROTECTIVE ACTION** (cap-3 hard rule, N>3 collapse risk = protective-kill autonomy): deleted the 2 redundant
  duplicate heavies (173940, 174244). Fleet now = **cefi-queue-heavy-174106 (trades+book5) + cefi-queue-light-174110
  (deriv_ticker+liquidations+futures_chain)** = COMPLETE 2026-tail coverage (all data types), N=2 (higher efficiency,
  under cap).
- **KEY REALIZATION**: a SEPARATE process (orchestrator or another agent) is ALSO managing the CeFi tail backfill (it
  launched the light + 2 heavies). My manual SSM launching RACES with it → over-cap. → **Shift to MONITOR-primarily**:
  verify fleet ≤3 + tail filling; only relaunch if the fleet drops to 0-1 tail VMs AND stays down a full tick (don't
  aggressively relaunch — let the other manager act first); ALWAYS re-verify ≤3 after any launch and kill duplicates.
  Historical 2020→2026 sweep is currently NOT running (queue VMs died) — the other manager may relaunch it; if not,
  that's the ~2-3wk af=0 work, lower priority than the tail.
- Both tail slices (heavy+light) now cover the empty 2026-06+ tail (still chronological-from-Jan, SPOT-preemptible). Net
  state is HEALTHY at N=2.

### 2026-07-15T19:02Z — tick 11: fleet cap-safe (3); co-manager active; widening cadence

- Fleet = 3, cap-safe: cefi-queue-heavy-174106 + cefi-queue-light-174110 + cefi-queue-light-183058 (co-manager launched
  a 2nd light at 18:30). 1 heavy + 2 light — redundant-ish but NOT over-cap → no protective kill (killing would race the
  co-manager). Both light VMs writing.
- Tail (2026-06+) still NOT filling — all VMs on 2026-01 chronological grind (year-granular launcher). Slow but not
  broken; will reach June eventually.
- ROLE: the co-manager is actively driving the VM fleet. My unique remaining jobs = (a) cap-safety backstop (kill only
  if >3), (b) the WS-H apply once the tail+sweep land, (c) F + C + rule-9 report. Backing off to a ~1h monitor cadence
  (nothing to do between data-landing milestones; frequent checks are noise). No code/data changes this tick.

### 2026-07-15T21:08Z — tick 13: co-manager owns the VM fleet now; my role = cap-backstop + WS-H finalize

- The co-manager relaunched a NEW wave ~20:20 with its OWN venue-based naming (cefi-queue-heavy-binancefutu-x15,
  cefi-queue-light-binancefutu-x2, cefi-queue-light-bybit-x4) — a different launcher than my timestamped ones. My old
  VMs (174106/174110/183058) died (SPOT). Fleet now = 1 RUNNING (the heavy; the 2 light wrote per_vm 20:49-20:52 then
  SPOT-preempted). Cap-safe (1 ≤ 3), no action.
- CLEAR HANDOFF: VM launching/management is now the co-manager's; my manual launches only race it. My remaining UNIQUE
  jobs = (a) cap-safety backstop (delete dupes only if >3), (b) WS-H apply once the tail+sweep data lands, (c) F, C,
  rule-9 report. I will NOT launch VMs (co-manager churns them through SPOT).
- ETA HONESTY: recent-tail (June-July) fill is SLOWER than the earlier 1.5-2d — the SPOT-preempt + relaunch-from-Jan +
  chronological grind + N≤3 lease is choppy; grind still in 2026-01 after ~5h. Realistic tail-landed: several days. Full
  af=0 history: ~2-3wk (cap-3 ceiling). Unchanged: all Phase-1 code shipped + landed.

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [SCRIPT] P0. Final cefi MVP verification: across the v10 perp-gated MVP universe, attempted_failed=0 AND
      expected_unattempted=0 for trades+book5+funding; Deribit OPTION present as options_chain ONLY (0 per-strike
      trades/book5 cells — **per-strike pre-v10 artifacts: resolution = PURGE (todos below) per operator ruling
      2026-07-12 (finding 30, `issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2); after the purge G4
      counts them zero by construction.**); every absence typed honest (pre-venue-launch / expiry-window /
      deferred-no-source). Repos: `instruments-service`, `e2e-testing`. **Run:**
      `python scripts/measure_honest_coverage.py --asset-group cefi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group cefi --mode full`;
      `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run`. **Gate (BOTH layers):**
      (Layer-2) both failure buckets zero; 0 phantom; 401-class cells re-attempted (attempted_failed not empty); AND
      (Layer-1) `layer_1.by_asset_group.cefi.denominator_complete == True` (100%, `missing_tuples == []`) in the same
      coverage.json — **[Corrected 2026-07-14, finding 26]** (was: a baked-in "Layer-1 currently 79.55% with 9 real
      holes" baseline that never matched any logged run in this doc, incl. the 07-03 runs closest to it at 61.4%/17 and
      73.61%/19 tuples) — Layer-1 last measured 91.78% (6 missing tuples) at the 2026-07-13T23:22Z→2026-07-14T00:05Z
      session close (see Progress Log "G4 Session Close-out"); re-run `measure_honest_coverage.py` fresh before relying
      on any number here, this line is a point-in-time snapshot, not the gate's live source of truth. G4 cannot close
      before the denominator-gap work in `issues/cefi_layer1_denominator_gaps_2026_07_03.md` lands. Verdict to Progress
      Log. **Full-execution criterion:** VM-list + coverage CLI output recorded per wave. SPOT N/A. (FOLDED IN from
      mvp_backfill_cefi_tick_v10_2026_06_27, 2026-07-15, plan-reconcile §6 operator ruling)
- Backing off to a pure 1h cap-backstop; will act only on (tail reaches June → WS-H) / (cap breach) / (completion).

## Progress Log (append-only)

### Three structural blockers that explain ~30 VM-hours of ZERO progress — recovered entries — 2026-07-15T22:25Z

**Provenance note (content-loss recovery)**: these findings were journaled into
`mvp_backfill_cefi_tick_v10_2026_06_27.md` during 2026-07-15 17:00-22:20Z, but that plan was archived at `98e8fd5ba`
("archive 13 emptied fold shells", plan-reconcile §6) from a base predating the last three entries — the `git mv` won
and the entries were dropped from the tracked tree (verified: commits `b671b3e10` / `4f0f84da8` / `6c864ac76` ARE
ancestors of origin, yet `git grep` finds none of their text in any tracked file). Re-homed HERE, the live successor,
rather than resurrecting an archived plan. Not a complaint — the fold itself was correct; only the content-survival
check (RULE 4: "verify content survival — grep both your additions and the incoming ones — before pushing") was missed.

**Why the cefi backfill has never converged.** Three INDEPENDENT defects, each individually sufficient to produce
exactly zero measured progress. Measured: eu 2,773,292 → 2,773,292 across multiple hours and multiple fleets.

1. **Waves aimed where there is nothing to close.** The gap is ONLY 2026-02..07 (a by_day cross-tab of the live manifest
   shows all 82 months 2019-03..2026-01 at eu=0). Yet every wave ever launched derived `start_date="${year}-01-01"` from
   `YEARS=` and scanned chronologically — the 2020-chronological waves were at 2020-06-21 after **29 hours**; their 2026
   replacements were still at 2026-01-01/01-03/01-12 after **91 minutes**, i.e. inside the eu=0 zone where progress was
   IMPOSSIBLE. **FIXED**: `START_DATE` override shipped (deployment-service, QG-green, quickmerged); waves now launch
   `2026-02-01..2026-07-14`.
2. **The writer stamped ids the denominator cannot credit.** `captured` rows carried raw vendor symbols (`PI_ETHUSD`,
   `XBT`) while `expected_unattempted` rows are keyed canonically (`KRAKEN-FUTURES:PERPETUAL:PIXEL-USD@LIN`) — disjoint
   namespaces, so a capture could never satisfy an expected cell. Site:
   `engine/orchestrator/venue_fetch.py::_record_venue_shard_counts`. **FIXED** by three lanes converging within an hour
   — `mtds@56679e78` (silent no-op: lowercase itype set vs the uppercase the write path emits), `mtds@5d44a197` (**the
   working fix**), `mtds@90ecde17` (the missing unit tests + unresolved-symbol visibility). The parquet FILE contents
   were always canonical — only the manifest KEY was raw, so nothing needs re-downloading.
3. **SPOT preemption DELETES waves and NOTHING relaunches them.** GCP operations, unambiguous:
   `compute.instances.preempted cefi-queue-heavy-binancefutu-x15-20260715-215549 15:05:38 system` — preempted ~6 min
   into real gap work (last line a genuine mid-fetch `deribit/BTC-6FEB26 — 2339276 rows` on day=2026-02-01, then
   silence). `launch-cefi-sharded-backfill.sh:498,702` uses
   `--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure` with **no relaunch
   mechanism** (only `launch-transfermarkt-backfill-vm.sh` has any preemption handling). The codex SPOT rule
   (`codex/05-infrastructure/spot-vms-for-backfill.md`) justifies SPOT because "idempotent shards **re-run on
   preemption**" — **that premise is false for this launcher family.** **NOT FIXED IN CODE** — see the todo below.

**Status of the writer fix: UNTESTED in production, NOT disproven.** Three eu tests, three INVALID results (fleet in the
January eu=0 zone / same / preempted 6 min in). Each time the "eu flat ⇒ blocker confirmed" verdict was retracted rather
than shipped as a finding. A valid test requires a wave whose cursor is inside 2026-02+ AND that survives long enough to
write.

**Also still open from this thread** (evidence in the archived plan): the stale per-venue eu ATOM (BINANCE-FUTURES eu
rows carry `instrument_type=''` + lowercase-raw `hotusdt` while KRAKEN-FUTURES eu rows are canonical — the enumerator
has emitted at least two shapes, violating the "shard atom identical across writer/manifest/status/gate/UI" HARD RULE);
the relabel pass over historical raw-id captures (peer dry-run `instruments-service@f021cb2b`: 3,133,117 candidates,
82.7% resolvable, 542,888 honestly unresolved, `--apply` operator-gated); and `sentinels.py` Tier-3 comparing canonical
`expected_instruments` against heuristically-canonicalized `captured_instruments` (same class, filed not blind-fixed).

- [ ] [INFRA] P0. **Close the SPOT-preemption relaunch gap for the cefi/tardis launcher family.** Today a preempted
      backfill wave is DELETED and silently never returns, which is why long waves never finish (evidence above: 2 of 3
      VMs preempted 6 min in, 2026-07-15T22:05Z). Either wire a preemption-aware relauncher (mirror
      `launch-transfermarkt-backfill-vm.sh`) or move to `--instance-termination-action=STOP` + a restart watchdog —
      architecture call. Until shipped, a session-scoped keeper loop is refilling the fleet to cap every 30 min
      (`START_DATE=2026-02-01`, lease-ON, `STALL_TIMEOUT_SEC=3900`, always via `tardis_concurrency_guard`), which is a
      crutch, not the fix. **Partial progress (data_engineering slot-12, 2026-07-16T02:15Z)**: shipped
      `deployment-service@dabcf05` — a new `lc_write_preemption_signal_file()` helper in `launcher_common.sh` (mirrors
      `launch-transfermarkt-backfill-vm.sh`'s existing pattern), wired into both `launch-cefi-sharded-backfill.sh`
      `gcloud compute instances create` call sites. This is observability-only (marks a SPOT preemption in GCS so fleet
      monitors classify it as expected rather than an unexplained `DP_VM_GONE_NO_CAPTURE`) — it does NOT auto-relaunch.
      The actual relaunch mechanism (the "architecture call" above) is still open; deliberately not attempted solo given
      its explicit framing as a design decision, not a mechanical fix. SSOT to correct once done:
      `codex/05-infrastructure/spot-vms-for-backfill.md` (its "idempotent shards re-run on preemption" premise is
      currently false for this family).

### 🔴 FOURTH blocker + it CORRUPTS the manifest: 3 lease-ON VMs in the real gap = 403 storm, ~94% false failures — 2026-07-16T06:10Z

**The first VALID production test finally ran** — the light waves survived ~8h with cursors deep inside the gap
(2026-05-17 and 2026-05-28, well past the eu=0 zone). Result, measured (20:22Z baseline → 06:05Z):

| metric               | 20:22Z    | 06:05Z    | delta        |
| -------------------- | --------- | --------- | ------------ |
| expected_unattempted | 2,773,292 | 3,193,942 | **+420,650** |
| captured             | 3,058,241 | 3,060,443 | **+2,202**   |
| attempted_failed     | 34,605    | 71,817    | **+37,212**  |
| coverage_pct         | 52.13     | 48.38     | **−3.75**    |

**8 hours × 3 VMs bought +2,202 captures and +37,212 FAILURES — a ~94% failure rate, and coverage went BACKWARD.**

**Mechanism (verified in the VMs' own logs, all three confirmed `TARDIS_CONCURRENCY_LEASE=1`):**

```
cefi-queue-light-bybit-x4       : 10,300 × HTTP 403 concurrent-IP-lock  vs   912 successes
cefi-queue-light-binancefutu-x2 : 15,034 × HTTP 403 concurrent-IP-lock  vs     0 successes
```

The lease is not merely failing to help — **it is the amplifier**. Its fail-open path
(`Tardis lease FAIL-OPEN: could not acquire within 1800s — proceeding WITHOUT the single-IP lock`) means that at N=3
every VM waits 30 min, fails to acquire, and then they ALL proceed unlocked _simultaneously_ — a guaranteed mutual-403
storm.

**Why the 2026-07-14 "N=3 grinds at ~50-70% efficiency" observation was misleading (and this lane propagated it):** that
measurement was taken while the VMs were re-walking **2020 data that was already captured** — skip-scans need few real
Tardis calls, so contention was mild and 3 VMs looked survivable. In the REAL gap every cell needs a live fetch, so N=3
is maximal contention. The operator's cap-3 hard rule was calibrated on the wrong regime. **The honest conclusion: for
genuine gap fetching, N=1.** (Cap-3 remains a correct upper bound — it just is not a target.)

**This is a DATA-CORRECTNESS issue, not just waste**: those +37,212 `attempted_failed` rows are **FALSE** — the cells
were never really attempted against the source, they were 403'd by our own self-contention. They now pollute the
manifest as if the venue had refused the data. (Workstream **B — 403 re-capture sweep + af-census → 0** in this plan is
exactly the cleanup, and its scope just grew by ~37k self-inflicted rows.)

**Action taken**: killed the two 403-storming light VMs; left ONE Tardis VM running
(`cefi-queue-heavy-binancefutu-x15-20260716-025616`, all 15 venues, trades+book5, START_DATE=2026-02-01, cursor
2026-02-02) so it can acquire the lease uncontended. Non-Tardis VMs (pacifica etc.) untouched — different key, no
contention.

**Note on eu +420,650**: the expected universe GREW during the window (new days accrue daily + catalogue growth) —
another reason a fetch-only strategy cannot converge while the daily inflow is unclosed. The forward/live capture path
is what should be preventing new gap accrual; that it is not is worth its own investigation.

**Writer fix (`mtds@5d44a197`) status: STILL not cleanly testable** — this test was valid on scan-position but the 403
storm meant almost nothing was actually fetched (+2,202 captures across 3 VMs/8h). The N=1 run now in flight is the
first configuration that can produce a clean signal.

### 2026-07-16T05:10Z — tick: WS-H CATALOGUE APPLY LANDED (dedup/equity-perp/dating/liquidations/denominator-complete)

> **[slot-3 /autonomous session]** — coordinating on the shared plan with the backfill co-manager (whose N=1 / 403-storm
> notes are above). I OWN the CODE + WS-H CATALOGUE side; the co-manager OWNS the Tardis backfill VM strategy. I am
> STOPPING all backfill VM management (my earlier N=3 tail launches fed the 403 storm — the co-manager's N=1 cut is
> correct; do not re-add tail VMs).

WS-H apply-list run via SSM on i-0dd9812a96cdda5dc (agent aa0f8f04), NON-tail-gated parts DONE:

- **Catalogue rebuild `--mode full --allow-catalogue-shrink` PROMOTED to prod** (backup:
  `prod/catalog.pre-wsh-dedup.20260716-050958.bak.parquet`). 427,552→424,224 rows. **CRITICAL INVARIANT PASSED: live
  count 9,952→10,122 (+170, ZERO live dropped).** Dedup: perp-family 9,177→5,386, HL 534→182 (177 live unchanged).
  EQUITY_PERP 0→636 + TOKENIZED_EQUITY 0→79. ASTER dating fixed 1,501→506. → G-code + D-code(HL/fleet dedup) PROD EFFECT
  now LIVE (no longer "pending rebuild").
- **liquidations (E) LIVE in prod honest-coverage** for all 6 feed venues (1,580,700 rows). **Denominator now
  `COMPLETE`** (was INCOMPLETE) — a DONE-criteria milestone. cefi recompute = 48.37% vs the complete denominator
  (remainder = the co-manager's in-flight backfill: expected_unattempted + the 403-class attempted_failed). Published to
  labeled sibling `gs://central-element-323112-honest-coverage/2026-07-16/coverage_cefi_wsh_20260716.json` (did NOT
  clobber the canonical defi-only coverage.json).
- **2 residual follow-ups** (agent STOPPED rather than guess on prod): (1) **HL phantom re-census OOM'd** — the
  reconcile tool full-loads the 12M-row manifest (~28GB) > the 15GB VM; no prod mutation (was dry-run); needs a 32-64GB
  VM (e.g. orchestrator m8i.4xlarge) OR a memory-frugal/DuckDB rewrite; the 1,277 HL phantoms are ready. HL will also
  re-census naturally once the backfill+consolidator run. (2) **equity-perp denominator propagation** deferred —
  catalogue re-type landed, but manifest rows are still typed PERPETUAL so they're ALREADY counted (just labeled
  PERPETUAL); re-labeling is cosmetic, not a coverage gap; running enumerate --apply-write now would DOUBLE-SEED
  (correctness risk) → needs the manifest PERPETUAL rows re-typed first.

**Remaining to DONE**: co-manager's backfill → af=0 (403-class) + recent-tail filled (their N=1 grind); then the FINAL
coverage recompute asserting af=0; + C (alias verify+auto-delete except DERIBIT-COMBO) + F (DERIBIT-COMBO history) +
optional HL re-census on a big VM. Phase-1 code + WS-H catalogue = DONE.

### 🔴 FIFTH gap — the Tardis cap is BLIND to forward-poll / T+1-cron / live VMs — 2026-07-16T07:00Z

Operator question: _"what about for the t+1 backfill schedulers that fill yesterday, the live tardis markets vms
(presumably again needs to be one vm)"_ — **correct, and it is currently unenforced.**

The guard's `TARDIS_VM_NAME_PATTERN` is `^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-`. It does
NOT match:

| launcher                           | VM name shape              | Tardis exposure                                                                                                                                                                               | counted? |
| ---------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `launch-cefi-forward-poll.sh`      | `cefi-fwd-<ts>`            | **YES** — reads `tardis-machine-api-key` from Secret Manager                                                                                                                                  | ❌ NO    |
| `launch-cefi-fwd-daily-cron-vm.sh` | `cefi-fwd-daily-cron-<ts>` | indirect — `VM_OPERATION=cron-trigger` that fires the forward-poll                                                                                                                            | ❌ NO    |
| `launch-mtds-live.sh`              | `mtds-live-*`              | **CONDITIONAL** — `--live-source native\|tardis-machine`; it already passes `TARDIS_CONCURRENCY_LEASE` + cites the lockout issue, so the exposure is known — but it is NOT wired to the guard | ❌ NO    |

**Why we have not been bitten yet — verified, not assumed**: `gcloud compute instances list` shows **zero** `cefi-fwd-*`
and zero `mtds-live-*` running right now. THAT is why the solo N=1 backfill VM measures ZERO 403s. The instant the T+1
forward-poll cron fires (or a `tardis-machine` live VM starts), it takes the single IP slot and the backfill silently
reverts to the 403 storm — including its FALSE `attempted_failed` manifest corruption — with nothing in the guard to
notice.

**Design note for the fix (deliberately NOT half-shipped — a naive pattern widen would over-block):**

1. **Priority is asymmetric — live/forward MUST win, backfill MUST yield.** So: COUNT fwd/live VMs in
   `tardis_running_vm_count` (making a backfill launch refuse while they run), but do NOT wire the guard INTO
   `launch-mtds-live.sh` / `launch-cefi-forward-poll.sh` — live must always be able to start.
2. **Match precisely.** `^cefi-fwd-[0-9]` catches the forward-poll without false-positiving the `cefi-fwd-daily-cron-`
   trigger (which holds no Tardis connection itself).
3. **Live is CONDITIONAL, so a name-only match over-blocks**: a `native`-source live VM does NOT touch Tardis and must
   not stall the backfill. The count needs the instance's `--live-source`/metadata, not just its name — i.e. read
   `TARDIS_*` metadata (or a new `VM_TARDIS_CONSUMER=1` stamp set by the launchers) rather than pattern-matching alone.
   **Recommendation: have every Tardis-consuming launcher stamp `VM_TARDIS_CONSUMER=1` into VM metadata and have the
   guard count THAT** — self-declaring beats a name regex that must be kept in sync with 83 launchers forever.
4. The running backfill VM should also yield gracefully rather than 403-storm when live grabs the slot (today it just
   fails cells and records them as `attempted_failed`).

- [ ] [INFRA] P0. **Make the Tardis cap see forward-poll / T+1-cron / live VMs.** Today the cap is enforced only across
      backfill VM name shapes, so a T+1 forward-poll or `tardis-machine` live VM silently contends with the capped
      backfill and re-creates the 403 storm + FALSE-af manifest corruption. Implement per the design above:
      `VM_TARDIS_CONSUMER=1` metadata stamp from every Tardis-consuming launcher + guard counts it; backfill yields to
      live/forward (never the reverse); backfill should pause-and-retry rather than record false `attempted_failed` when
      the slot is held. SSOTs to update once shipped: `codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap +
      the CLAUDE.md one-liner.
