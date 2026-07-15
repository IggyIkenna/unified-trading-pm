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
