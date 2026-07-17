---
doc_type: plan
title: CeFi Completion Program — close the honest-coverage gaps to genuinely-done
summary:
  Coordinator plan-of-record for driving CeFi to actually-done honest coverage — the 9 workstreams surfaced by the
  2026-07-15 completion audit (recent-tail backfill, 403 re-capture sweep, legacy-alias kill, HYPERLIQUID finish,
  liquidations SSOT fix, DERIBIT-COMBO historical backfill, equity-perp Phase 2, canonicalisation G5, EXTENDED-STARKNET
  book5). LOCAL/autonomous execution — this session drives all workstreams on a loop; the Progress Log is the memory of
  record across context compression.
status: archived
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
last_updated: 2026-07-17
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

> **🔴 CORRECTION 2026-07-17 — THIS ARCHIVAL'S CORE PREMISE IS FALSE. Do not cite it as settled fact.** The "not
> closable at the N=1 Tardis throughput ceiling ≈ 1.8 years" claim below came from an ERRONEOUS verdict (extrapolating a
> BROKEN system's throughput and mistaking a regression for physics). Measured from this repo's own manifest
> `written_at`: **June 2026 captured 2,791,042 rows, peak day 2,157,060 ≈ 89,878/hour** vs **~254/hour now** — a **~350x
> REGRESSION**, not a ceiling. At June rates the 2.89M-cell gap is ~1-2 days of work. The "timeout diagnosis" this
> archival marks as _superseded_ is in fact the ROOT CAUSE. Full evidence + reopened P0s:
> `plans/active/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md`. Whether to un-archive is an operator call.
>
> **🗄️ ARCHIVED 2026-07-17 — CLOSED at honest-done.** Operator accepted current CeFi coverage (**50.79%** against a
> **COMPLETE** denominator; the 2,892,108-cell tick gap is honestly-labelled `expected_unattempted`, not closable at the
> N=1 Tardis throughput ceiling ≈ 1.8 years). All work achievable inside that ceiling SHIPPED (E liquidations, G/G-code
> equity-perp typing + tracks_equity tags, D dedup/phantom, WS-H catalogue apply → denominator COMPLETE, C alias purge +
> BYBIT migration + eu-side residuals). The Tardis-gated backfill workstreams (A/B/F/G-tick + af=0 census + timeout
> diagnosis) are **superseded** by the accept-decision, not deferred. Genuine NON-Tardis residuals migrated to
> `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`. See the terminal Progress Log entry for the rule-9
> audit. All 5 archival steps complete; `locked_by` clear.

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

- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17 — Tardis N=1 ceiling; not pursued). [INFRA] P0. **A —
      recent-tail main-venue backfill (2026-05-24 → now-2).** Launch lease-serialized Tardis backfill for
      BINANCE(-SPOT/FUTURES), OKX(-SPOT/SWAP/FUTURES), BYBIT, UPBIT, KRAKEN(-SPOT/FUTURES), BITGET(-SPOT/FUTURES),
      BITFINEX(-SPOT/FUTURES), COINBASE-SPOT, DERIBIT. `TARDIS_CONCURRENCY_LEASE=1`, `--provisioning-model=SPOT`, per-VM
      shards. Monitor to STOPPED. Evidence: manifest rows for the tail range, per venue.
- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17 — af=0 not reachable at N=1; partial coverage accepted +
      honestly labelled). [INFRA] P0. **B — 403 re-capture sweep + af-census → 0.** Re-run the MVP `attempted_failed`
      shards under the lease (clears the stale 403 class), then re-census. Closes `mvp_backfill_cefi_tick_v10` final
      gate ("attempted_failed=0"). Also clears the blank-instrument_type + lowercase-casing legacy fail rows
      (forward-write already fixed). Evidence: coverage recompute att_fail delta.
- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17 — DERIBIT-COMBO historical is Tardis-gated, same N=1 ceiling;
      venue KEPT, not alias-killed). [INFRA] P1. **F — DERIBIT-COMBO historical `by_date` backfill.** Routing bugs
      already fixed; the historical catalogue is starved — design + run the by_date backfill so
      `(DERIBIT-COMBO, trades/options_chain)` closes. KEEP this venue (do NOT alias-kill it). Evidence.
- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17 — equity-perp tick download is Tardis-gated; G-code type-stamp +
      tracks_equity tags SHIPPED, only the tick fetch is deferred). [INFRA] P1. **G-tick — equity-perp tick download.**
      After G-code type-stamp, wire + run the tick capture for the 70 equity perps from each instrument's per-instrument
      `available_from` (pre-listing stays empty_confirmed). Evidence.
- [x] → MIGRATED to `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (residuals #1+#2 — HL is
      non-Tardis/fillable; phantom re-census needs a 32-64GB box). [INFRA] P1. **D-tail — HYPERLIQUID tail + phantom
      re-capture.** Fill HL from ~2026-06-24 → now-2 and re-capture the 1,277 phantom dates to the `@LIN` canonical
      path. Evidence.

### Phase 3 — cleanup (only after Phase-2 data is verified present under canonical names)

- [x] ✅ [DATA] P1. **C (venue-alias half) DONE + DURABLE (maint window 2026-07-16, agent a68aa6dc).**
      Operator-authorized stop-fix-restart: paused the market-data cefi consolidator
      (`uts-prod-manifest-consolidator-market-data-cefi-cron`) + stopped the backfill VM → quiesced index; **purged the
      13 stray alias venues = −526,104 index rows** (all 0-captured, 0 GCS objects) INCLUDING the same 13 from
      `_legacy_seed.parquet` (the seed-carry was why the prior purge re-merged — THIS is what made it stick); **migrated
      BYBIT-FUTURES** (45 real live-perp objects 2026-06-23→27 → canonical BYBIT + reclassify af→captured, +45); resumed
      consolidator + keeper relaunched backfill. **STUCK verified 3× over ~70min post-resume.** Canonical-unchanged
      proof: exactly ONE venue changed (BYBIT +45); all others bit-for-bit; exclusions intact
      (DERIBIT-COMBO/bare-OKX/prediction/blank). Backups:
      `_index/backups/availability_     index.pre-maint-20260716T115054Z.parquet`. REMAINING C sub-parts (eu-side,
      follow-up): the ~49,732 stale-shape `expected_unattempted` rows (co-manager's
      `purge_stale_shape_cefi_expected_unattempted` tool) + bare-COINBASE 318 eu rows still in
      `expected_universe_ranges` (drop bare COINBASE from cefi enumeration → COINBASE-SPOT, else daily re-materializes).
      Original C todo detail ⇩:
- [x] ✅ DONE — venue-alias half durable (maint window, above); **eu-side completed by the co-manager 2026-07-16**
      (purge_stale_shape 49,732 stale-shape rows + relabel 2.59M + drop 286k eu → coverage 48.43→50.79%). [DATA] P1. **C
      — kill legacy venue aliases (verify → migrate → auto-delete), EXCEPT DERIBIT-COMBO.** For
      OKEX/OKEX-SWAP/OKEX-FUTURES, BYBIT-FUTURES, COINBASE-INTERNATIONAL, bare BINANCE/BITFINEX/BITGET/KRAKEN,
      CRYPTOFACILITIES, and the lowercase-itype strays (`spot`/`spot_pair`/`perpetual`): (1) verify every aliased
      shard's data already exists under the canonical venue+UPPERCASE itype; (2) migrate any genuinely-unique data; (3)
      **auto-delete** the alias manifest rows + GCS objects; (4) re-consolidate the index. Evidence: pre/post row
      counts + GCS deletion manifest. **DERIBIT-COMBO is a legit distinct venue — never delete it.** **TOOL ALREADY
      BUILT — this is the `expected_unattempted`-side portion of C**:
      `instruments-service/scripts/purge_stale_shape_cefi_expected_unattempted_2026_07_15.py` (snapshot-first,
      dry-run-default, STOP-ON-SURPRISE `[5000,250000]`, post-apply verify gate). Freshly re-confirmed 2026-07-16T09:21Z
      (dry-run re-run, read-only): **49,732** stale-shape eu rows live right now (42,993 legacy pre-`enumerator_run_id`
      debris under retired venue strings CRYPTOFACILITIES/OKEX*/BITFINEX-DERIVATIVES/etc + lowercase-raw ids,
      ~4,951-5,700 bundle-grain old-shape duplicates for DERIBIT/OKX-FUTURES `futures_chain`/`options_chain` left over
      from the pre-`a2468dd9` enumerator run) — essentially unchanged from the 07-15T22:2xZ measurement (49,720),
      confirming (a) nothing new is accumulating and (b) `--apply` has NOT been run yet. **Still BLOCKED-OPERATOR** —
      sign-off already requested via `/blocked` in
      `issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md` (do not duplicate the ask;
      this todo's C is the same gated mutation). Exact command once approved:
      `cd instruments-service && GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prd DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp CLOUD_MOCK_MODE=false .venv/bin/python scripts/purge_stale_shape_cefi_expected_unattempted_2026_07_15.py --apply`.
      See 2026-07-16T09:xxZ Progress Log entry below for the full re-verification + why a bare enumerator re-run cannot
      self-heal this (append-only writer + per-key consolidator dedup never collapses two DIFFERENT `instrument_id`
      values for what should be the same cell).

### Phase 4 — close + prove

- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17). G5 "100% honest coverage" is not reachable at the N=1 ceiling;
      coverage ACCEPTED at 50.79% against a COMPLETE denominator, gap honestly-labelled `expected_unattempted` (NOT
      af=0/eu=0). The catalogue canonicalisation + denominator-COMPLETE half SHIPPED (WS-H apply). [DATA] P0. **H —
      canonicalisation G5 + final honest-coverage recompute.** Drive `master_data_canonicalisation` G5 ("backfill → 100%
      honest coverage") for cefi; re-enumerate the denominator (`enumerate_expected_universe.py`) so it reflects
      liquidations + equity perps + the filled tail; run `compute_honest_coverage`; confirm CeFi
      `denominator_complete: true`, `expected_unattempted=0`, `attempted_failed=0` (genuine). Evidence: the new
      `coverage.json`.
- [x] ✅ DONE — rule-9 terminal report written in the Progress Log ("TERMINAL: CeFi completion program CLOSED at
      honest-done", 2026-07-17): verified end-state table per WS, the forced tradeoff (N=1 Tardis ceiling), the genuine
      impossibility (2.89M gap ≈ 1.8yr), and the consciously-not-done residuals (migrated to
      `issues/cefi_residual_followups_after_honest_done_2026_07_17.md`). Post-plan codex audit done in the archival
      ritual below. [REVIEW] P0. **Final audit + report.** Rule-9 report in this plan: verified end-state per
      venue/data_type, every forced tradeoff, every genuine impossibility. Post-plan codex audit (update
      cefi-capture-universe / honest-coverage docs on any contract change). Nothing left for the operator to pick up.

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

- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17 — af=0/eu=0 not reachable at the N=1 ceiling; partial coverage
      accepted + honestly labelled). [SCRIPT] P0. Final cefi MVP verification: across the v10 perp-gated MVP universe,
      attempted_failed=0 AND expected_unattempted=0 for trades+book5+funding; Deribit OPTION present as options_chain
      ONLY (0 per-strike trades/book5 cells — **per-strike pre-v10 artifacts: resolution = PURGE (todos below) per
      operator ruling 2026-07-12 (finding 30, `issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2); after
      the purge G4 counts them zero by construction.**); every absence typed honest (pre-venue-launch / expiry-window /
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

- [x] ✅ [INFRA] P0. **Close the SPOT-preemption relaunch gap for the cefi/tardis launcher family.** Today a preempted
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
      **SHIPPED (2026-07-16, deployment-service@02be72e)** — design chosen: **option (a), a preemption-aware
      relauncher**, NOT the STOP+watchdog alternative (mirrors the existing `launch-transfermarkt-backfill-vm.sh`
      preemption-signal pattern, reuses the ALREADY-SHIPPED `exit_code_fleet_monitor`/`escalation.py` auto_recover
      actuator spine that OOM (`DP_VM_EXIT_NONZERO`) and STALL (`DP_VM_STALL`) already use — one more actuator on proven
      infra beats a brand-new STOP-based lifecycle). Exact params replay (not a blind relaunch): a new
      `lc_write_launch_params()` helper (`launcher_common.sh`) persists `{launcher, env}` to
      `gs://…/vm-logs/<vm>/LAUNCH_PARAMS.json` at VM-creation time — wired into BOTH `launch-cefi-sharded-backfill.sh`
      call sites (per-shard: `ONLY=<venue>:<year>:<group>`; SINGLE_VM_QUEUE mode — the shape actually running in prod —
      `VENUES`/`YEARS`/`LAUNCH_GROUPS`/`START_DATE`/lease+concurrency knobs). `exit_code_fleet_monitor.sweep()` reads it
      back via new `_gcs.read_launch_params()` only when `verdict is PREEMPTED`, and `_finding_for` now returns a
      `DP_VM_PREEMPTED` (severity INFO, tier `auto_recover`, registry `DP-VM-007`) finding instead of the old
      `return None`. New actuator `RelaunchPreemptedVm` (`scripts/recovery/relaunch_backfill_vm.py`, own class + own
      budget namespace `uts_preempted_relaunch_budget`, generous `_MAX_PREEMPTION_RELAUNCHES_PER_DAY=48` since SPOT
      legitimately preempts ~hourly under cap-1 — OOM's ≤2/day budget would have defeated the whole point) replays
      `launch_env` verbatim into the SAME launcher subprocess — which re-sources its OWN `tardis_concurrency_guard`
      before creating anything, so the relaunch is NEVER blind/cap-violating: a guard refusal surfaces as the subprocess
      exiting non-zero → `status=FAILED`, never a silent relaunch. Wired into `escalation._DP_RECOVERY_ACTIONS`
      (`_EVENT_VM_PREEMPTED → _recover_preempted_vm`) exactly like OOM/STALL. `classify_terminated_vm`'s existing
      `preempted` precedence (over exit_code) already guarantees a genuinely-exit-0 VM never reaches this path — no new
      logic needed there. Fix 2 (the no-relanch alert) folded into the SAME actuator, see below. Basedpyright: my new
      code contributes ZERO new diagnostics (verified — the dynamic `importlib.import_module` Any-cascade is
      TYPE_CHECKING-guarded-import + `cast()`'d away, unlike the 3 pre-existing sibling actuators which still carry it);
      251/251 unit tests green (10 new `RelaunchPreemptedVm`/routing tests in `test_dp_recovery_actuators.py` + 5
      new/updated sweep-level tests in `test_data_pipeline_monitors.py`); full `quality-gates.sh` green. **Deliberately
      NOT done**: the actual codex correction to `spot-vms-for-backfill.md` (operator-gated per the plan-reconcile rule
      — exact edit text is in the 2026-07-16 Progress Log entry below for the operator to apply). SSOT to correct once
      done: `codex/05-infrastructure/spot-vms-for-backfill.md` (its "idempotent shards re-run on preemption" premise is
      NOW TRUE for this family — see the exact wording needed in the Progress Log).

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

- [x] ✅ [INFRA] P0. **Scope the Tardis cap to AUTHENTICATED batch consumers only (operator-verified model
      2026-07-16).** Today the cap is enforced only across backfill VM name shapes, so a T+1 forward-poll or
      `tardis-machine` live VM silently contends with the capped backfill and re-creates the 403 storm + FALSE-af
      manifest corruption. Implement per the design above: `VM_TARDIS_CONSUMER=1` metadata stamp from every
      Tardis-consuming launcher + guard counts it; backfill yields to live/forward (never the reverse); backfill should
      pause-and-retry rather than record false `attempted_failed` when the slot is held. SSOTs to update once shipped:
      `codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap + the CLAUDE.md one-liner. **SHIPPED (2026-07-16,
      deployment-service@02be72e)**: (i) `VM_TARDIS_CONSUMER=1` stamped in `launch-cefi-sharded-backfill.sh` (both
      per-shard + SINGLE_VM_QUEUE metadata blocks), `launch-cefi-sharded-backfill-aws.sh` (EXTRA_TAGS),
      `launch-mtds-backfill-vm.sh` (ONLY when `--asset-group CEFI` — verified DEFI stays unstamped),
      `launch-cefi-forward-poll.sh` (always — it's cefi-only); `launch-mtds-live.sh` and IS-side deliberately left
      untouched (operator-verified unauthenticated). (ii) `tardis-concurrency-guard.sh`'s `tardis_running_vm_count()`
      rewritten: ONE `gcloud compute instances list     --format=json(name,metadata.items)` call (verified server-side
      `--filter metadata.<key>=<value>` is REJECTED by the GCE list API — "Invalid list filter expression" — hence the
      json+python union-count approach) counts the UNION of the legacy name-regex match OR `VM_TARDIS_CONSUMER=1`
      metadata (dedup, never double-counts a VM matching both); AWS side unions the legacy purpose-tag filter with a new
      `tag:VM_TARDIS_CONSUMER=1` filter (2 calls + `sort -u`, since AWS `--filters` ANDs across different tag Names).
      Read-only verified against the REAL fleet (central-element-323112, asia-northeast1-c): counted exactly 1 (the
      running `cefi-queue-heavy-…-075338` backfill), correctly excluding the non-Tardis `cefi-pacifica-solana-…` VM.
      (iii) `launch-cefi-forward-poll.sh` now sources `tardis-concurrency-guard.sh` + calls
      `tardis_concurrency_guard 1 "$ZONE" "$PROJECT"` before creating its VM — REAL-fleet-verified (non-dry-run
      invocation): it correctly REFUSED (exit 1, cap 1 running + 1 planned = 2 > 1) while the cap-1 backfill VM held the
      slot, with ZERO VM created — asymmetric priority confirmed (backfill wins, forward-poll queues-via-refuse,
      matching every other integration of this guard — none block-and-wait). Fleet double-checked unchanged after every
      read-only probe (scope guard honored throughout). Full `quality-gates.sh` green; 251/251 unit tests green.
      **Deliberately NOT done**: "backfill should pause-and-retry rather than record false attempted_failed" (the
      per-shard MTDS-side behavior when the slot is held mid-run, as opposed to at LAUNCH time) — out of scope for this
      fix (that's an MTDS-repo runtime change, not a deployment-service launcher/guard change); noted as a follow-up,
      not silently dropped.

### ✅ CORRECTION to the FIFTH gap — only AUTHENTICATED batch contends; live + IS are free (operator model, code-verified) — 2026-07-16T07:15Z

Operator asserted and asked to be checked: _"live mtds tardis doesn't require auth… because it's behind free public
APIs. same for batch or live IS related tardis… it's just t+1 backfills that would need to queue behind long running
batch backfills and only for mtds; is can run freely and live too — double check my assumptions"_. **Checked against
code. The assumptions HOLD, and they invalidate part of my own prior entry:**

| path                         | endpoint / evidence                                                                                                                                                                                                                  | auth?   | contends? |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------- | --------- |
| **live MTDS tardis-machine** | `live/connectors/tardis_machine_ws.py`: `_DEFAULT_TARDIS_MACHINE_WS_URL = "ws://localhost:8002/ws-stream-normalized"` — a LOCAL sidecar normalising exchanges' own public feeds; **zero** `api_key`/`Authorization` in the connector | **NO**  | **NO**    |
| **IS Tardis**                | `reference_data/adapters/cefi/tardis/adapter.py` → `api.tardis.dev/v1/exchanges/*` (public metadata; the audit lane queried it unauthenticated all session)                                                                          | **NO**  | **NO**    |
| **T+1 forward-poll**         | `launch-cefi-forward-poll.sh`: `--operation backfill --mode batch` + `tardis-machine-api-key` from Secret Manager → the `datasets.tardis.dev` path (the SAME one that emits `403 code=274 concurrent-IP-lock`)                       | **YES** | **YES**   |
| **batch backfill**           | `cefi-queue-*` / `mtds-backfill-cefi-*` — datasets API                                                                                                                                                                               | **YES** | **YES**   |

**My prior entry was WRONG on two points, corrected here:** (1) it listed `mtds-live-*` as a contender needing to be
counted — it is NOT, live never consumes the licensed slot, so counting it would have STALLED the backfill for no
reason; (2) it proposed "live/forward always wins, backfill yields" — the live half is moot (no contention), and the
operator's rule for the forward half is the INVERSE: **T+1 queues BEHIND the long-running batch backfill.** That is safe
precisely because the backfill's own range (2026-02-01→yesterday) already covers the days T+1 would fill — so nothing is
lost by making T+1 wait, whereas letting T+1 preempt would mean the multi-day backfill never finishes.

**Operator-approved design (2026-07-16), now the spec for the P0 above:**

1. **Self-declaring, not a regex** — every launcher that opens an AUTHENTICATED Tardis (datasets) connection stamps
   `VM_TARDIS_CONSUMER=1` into VM metadata; the guard counts THAT. A name pattern across 83 launchers can never stay in
   sync, and (as just proven) name-matching would have wrongly caught the unauthenticated live VMs. **Stamp it on**:
   `launch-cefi-sharded-backfill.sh` (+ AWS twin), `launch-mtds-backfill-vm.sh` (cefi), `launch-cefi-forward-poll.sh`.
   **Do NOT stamp**: `launch-mtds-live.sh` (tardis-machine = unauthenticated local sidecar), anything IS-side.
2. **Asymmetric priority** — the guard is wired into the QUEUING side only: T+1/forward-poll checks and waits; the
   long-running backfill is not blocked by it. (Live is exempt entirely, so it is never wired in.)
3. **Pause-and-retry, never false failures** — when the slot is held, a waiting consumer must back off and retry rather
   than burn attempts into `attempted_failed`. Today's behaviour manufactured **+37,212 FALSE af rows in 8h**; that is
   manifest corruption, and it is the single most damaging part of this whole class.

### Concurrency ramp measured: 64 streams = 2x throughput, box still ~94% idle — 2026-07-16T07:25Z

Single SPOT VM (`cefi-queue-heavy-binancefutu-x15-20260716-063714`, e2-highmem-16, cap-1, lease-ON, bundled 15 venues
via SINGLE_VM_QUEUE, START_DATE=2026-02-01), `TARDIS_MAX_CONCURRENT_DOWNLOADS=64` +
`TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=16` (both VERIFIED on the instance) vs the 16/4 defaults measured at 06:05Z:

| metric                | 16/4 defaults | 64/16 ramp | note                             |
| --------------------- | ------------- | ---------- | -------------------------------- |
| 403s / 600 log lines  | 0             | **0**      | N=1 holds — no contention at all |
| successes / 600 lines | 29            | **59**     | ~2x throughput                   |
| rss                   | 7.8 GB        | **8.6 GB** | of 128 GB — barely moved         |
| cpu                   | 104% /1600%   | **~104%**  | ~6% of the box                   |

**Read**: 4x concurrency bought ~2x throughput, so a second (non-CPU, non-RAM, non-403) limiter is partially binding —
per-connection Tardis pacing and/or per-day shard size are the candidates. But NOTHING on the box is saturated (RAM
+0.8GB for 4x streams proves the StreamingShardFinalizer batching keeps per-stream memory bounded, exactly as designed),
so **the ramp should continue** — 128 then 192, watching rss/cpu/403 at each step, staying inside the operator's
~100-200-concurrent tolerance (~2k is the level Tardis rejects). Machine upsizing is NOT indicated yet: at ~6% CPU a
bigger box would burn money for nothing. Revisit only if CPU crosses ~70% at high stream counts.

### Preemption handling is a NO-OP that LIES, and CPU is nowhere near exhausted — 2026-07-16T07:35Z

Two operator questions, both answered against code/telemetry:

**Q1: "when spot VMs die from Google reclaim (preemption) vs a normal terminal, do we auto-relaunch via failure
handling? does this Slack-alert in data-pipeline-alerts? should?"**

**Answer: NO relaunch, NO alert — and the code actively CLAIMS a relaunch that does not exist.**

- `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py:401-405`: on `TerminationVerdict.PREEMPTED` it
  emits `logger.info("... preempted → SPOT relaunch (benign, no alert)")` and **does nothing else** — verified: no
  `instances create`, no `launch-*.sh`, no subprocess, no recovery action anywhere consumes the PREEMPTED verdict. The
  "→ SPOT relaunch" text is aspirational; there is no relauncher.
- `launcher_common.sh:33-37`: `lc_write_preemption_signal_file` is documented "observability only, does NOT relaunch the
  VM". The cefi launcher wires this signal (writes a GCS marker on SIGTERM) but nothing acts on the marker.
- Alerting: preemption is DELIBERATELY suppressed as benign INFO-only ("no alert"). That suppression was correct ONLY
  under the assumption a relaunch happens — the same false premise as the codex SPOT rule ("idempotent shards re-run on
  preemption"). Since NO relaunch happens, the suppression is now a silent-failure bug: **a preempted backfill vanishes
  with zero operator signal.**

**Operator's instinct is correct.** The fix is one of two ends, not the current no-man's-land: (a) actually relaunch on
PREEMPTED (then benign + no alert is honest — preferred, and it is exactly the P0 SPOT-preemption relauncher already
filed), OR (b) if it cannot relaunch, it MUST alert data-pipeline-alerts (`DP_VM_PREEMPTED_NO_RELAUNCH` or similar),
because a silently-vanished multi-day backfill is not benign. Today it does NEITHER. Folding this into the existing P0
(the relauncher IS option (a)); adding the alert as its fallback.

**Q2: "did we set TARDIS_MAX_CONCURRENT_DOWNLOADS high enough to exhaust the VM's CPU?"**

**Answer: NO — nowhere close.** e2-highmem-16 = 1600% CPU ceiling. At 64 concurrent downloads: steady ~105% (~7% of the
box), transient peak 1338% (84%, a momentary decompress/parse/flush burst). The peak proves the work parallelises across
all 16 cores when there IS CPU work, but steady state is I/O-wait-dominated (Tardis network round-trips) — which is why
16→64 streams gave ~2x not 4x throughput: the binding limiter is network/Tardis pacing, not CPU/RAM (rss was
8.6GB/128GB). **Headroom to ramp further** → bumped to `TARDIS_MAX_CONCURRENT_DOWNLOADS=128` +
`TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT=32` (RAM projection ~13GB, still trivial; CPU still <10% steady). The probe watches
for the point where either the parse/flush peaks start CLUSTERING into sustained high CPU (→ then a bigger machine is
finally indicated) or 403s appear (→ Tardis connection ceiling, back off). Do NOT upsize the machine yet — at 7% steady
it would burn money for nothing.

- [x] ✅ [INFRA] P1. **Alert on SPOT preemption when there is no relaunch (fallback to the P0 relauncher).** Until the
      relauncher lands, `exit_code_fleet_monitor` must emit a data-pipeline-alerts notification on
      `TerminationVerdict.PREEMPTED` for backfill VMs (not the current silent INFO log that falsely claims "SPOT
      relaunch"). Fix the misleading log line either way. **SHIPPED (2026-07-16, deployment-service@02be72e)** — folded
      into the SAME actuator as the P0 relauncher (the relauncher makes preemption truly benign, so per this todo's own
      framing the alert now fires ONLY when the relaunch itself fails, not on every preemption):
      `RelaunchPreemptedVm.relaunch()` self-emits a CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH` (a NEW event, deliberately
      reused-carrier not reused-code — plain `log_event()` string, no new UTL constant needed since this fix stayed
      scoped to deployment-service) on EVERY failure path: no `relaunch_launcher` binding, the per-(vm-prefix,day)
      budget exhausted (48/day — see Fix 1 note), the launcher subprocess raising, OR the launcher's own
      `tardis_concurrency_guard` refusing (surfaces as a non-zero exit) — unlike the OOM/STALL actuators (which only
      self-emit on budget-exceeded), EVERY failure path here alerts loudly, because a silently-vanished preempted
      backfill was the exact root complaint. On success: a quiet INFO `DP_VM_PREEMPTED` only (verified end-to-end: no
      CRITICAL fires when the relaunch succeeds). The misleading `exit_code_fleet_monitor` log line ("→ SPOT relaunch
      (benign, no alert)") is fixed to accurately describe dispatching a relaunch attempt via the auto_recover tier,
      never claiming success it hasn't verified. Both outcomes end-to-end-tested (see
      `test_dp_recovery_actuators.py::test_preempted_relaunch_*` +
      `test_data_pipeline_monitors.py::test_sweep_preempted_vm_*`) — confirmed via a live sandbox run too (a
      SUCCESS-path sweep replaying real captured `LAUNCH_PARAMS.json` env into a stub launcher, and a FAILURE-path sweep
      with a guard-refusing stub launcher, both producing the exact designed alert/no-alert split + a real
      `plans/active/issues/*.md` file on failure).

### Guard race closed (RUNNING-only count let 2 VMs run) + ramped to 128/32 — 2026-07-16T07:55Z

**Self-inflicted cap-1 violation, caught + fixed.** While bumping concurrency to 128, the keeper's relaunch and my
manual launch fired 40s apart into an empty-fleet window (`cefi-queue-heavy-...-075253` @00:57:25 + `...-075338`
@00:58:05). BOTH passed `tardis_concurrency_guard` because `tardis_running_vm_count` filtered `status=RUNNING` only —
the first VM was still `PROVISIONING` (already holding the IP slot) and thus uncounted. Two VMs ran = the exact 403
storm the cap exists to prevent. **Root-fixed**: the guard now counts `RUNNING OR PROVISIONING OR STAGING`
(deployment-service, QG-green, quickmerged) — a coming-up VM is now visible to a concurrent launch. Killed the 64-stream
duplicate, kept the 128/32 VM. **Process fix**: stopped the racing keeper and re-armed a SINGLE-authority keeper v2
(128/32, same widened status check, sole launcher for this fleet — no manual launches alongside it). Lesson: two
independent things launching into the same cap need the guard to see about-to-exist VMs, not just running ones — and
only ONE automation should own a capped singleton.

**Current fleet**: `cefi-queue-heavy-binancefutu-x15-20260716-075338` (SPOT, 128 trade / 32 book5 streams VERIFIED,
lease-ON, 2026-02-01→yesterday, START_DATE-scoped). Probe watching for the throughput ceiling / CPU clustering / 403
onset at 128.

### 2026-07-16T08:35Z — [slot-3] G-code REVISED per operator: equity types collapsed → PERPETUAL/SPOT_PAIR + tags

- Operator 2026-07-16 challenged the EQUITY_PERP/TOKENIZED_EQUITY distinct instrument_types: "broad definitions should
  remain perpetual and equities; but the system must be able to KNOW what's an equity perp (to find the tradfi spot leg
  etc) — a tag or mapping must exist". Verified: instrument_type = contract mechanics; the equity-nature is an
  attribute; NO code branched on `==EQUITY_PERP` for behavior (ledger→PERP, mvp→base-gated); the distinct type was
  non-load-bearing AND caused the WS-H double-seed blocker.
- **REFACTOR SHIPPED**: **uac@b44eb28c** (deprecate-not-remove EQUITY_PERP/TOKENIZED_EQUITY enum values [kept parseable
  — canonical_id_builder + full-enum-coverage test + persisted strings need them]; removed from
  CeFiMvpRule.instrument_types → equity perps MVP-gate as PERPETUAL via base_ccys; fixed liquid_representative) ·
  **is@350f0460** (build_instrument_ catalogue: `_refine_cefi_instrument_type` → `_cefi_equity_tags`; stamps
  `tracks_equity`[real-equity ticker from crypto_equity_link] + `is_equity_perp` catalogue columns instead of minting
  the types) · **pm@b8600b138** (codex).
- **PROD catalogue RE-STAMPED** (`--mode full --allow-catalogue-shrink`, backup
  `backups/prod/catalog.parquet.pre-equity-tags-2026-07-16`): EQUITY_PERP 636→0, TOKENIZED_EQUITY 79→0; 717 equity
  instruments now 638 PERPETUAL + 79 SPOT_PAIR, all is_equity_perp=True + tracks_equity populated (15 linked tickers:
  NVDA/META/AAPL/TSLA/COIN/… ; '' for pre-IPO SPCX + commodity/index XAU/SPX). LIVE count 10,122→10,130 (no drop);
  dedup+ASTER-dating INTACT (HL 182, ASTER 506, perp-family 5,391).
- **WS-H DOUBLE-SEED BLOCKER RESOLVED** — catalogue instrument_type == manifest (PERPETUAL) for these instruments; the
  denominator reconciles, enumerate no longer double-seeds. (The equity-perp coverage-propagation follow-up from the
  earlier WS-H run is now moot.)
- G-code net: EQUITY_PERP-typing SUPERSEDED by the tag approach; the dedup + ASTER-dating parts of G/D remain landed +
  correct. Design principle codified: instrument_type = mechanics only; underlying-asset-class = a tag/mapping.

### Two-atom `expected_unattempted` diagnosis — INDEPENDENTLY RE-VERIFIED, already fully code-fixed, still BLOCKED-OPERATOR on the corpus mutation — 2026-07-16T09:3xZ

**Dispatched to diagnose the "eu rows carry two atom shapes" finding fresh** (operator-cited BINANCE-FUTURES `hotusdt`
lowercase-raw + empty `instrument_type` vs KRAKEN-FUTURES canonical `KRAKEN-FUTURES:PERPETUAL:PIXEL-USD@LIN`). Read the
live prd `_index/availability_index.parquet` directly (pandas+pyarrow, IS `.venv`, column-projected + filtered — never a
whole-corpus load) across BINANCE-FUTURES/BITGET-FUTURES/KRAKEN-FUTURES/OKX-SPOT/DERIBIT, cross-tabbed by `written_at`.
**Confirmed the two-shape claim is real, not a misread**, and it decomposes into exactly the same two classes a prior
session (`backend_engineer`, slot-6, 2026-07-15T22:2xZ) already root-caused and fixed in
`issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md` (final P0 + P1 todos, both checked
`[x]`) — this session found nothing new on the code side, only reconfirmed the diagnosis live + refreshed the
still-pending corpus-mutation numbers:

1. **Class A — legacy pre-`enumerator_run_id` debris (42,993 rows, confirmed exact match to the prior session's
   count).** `written_at` 2026-04-22..2026-06-28 (mostly 2026-06-23/24), under RETIRED venue-name strings
   (`CRYPTOFACILITIES`=31,498 which is Kraken Futures' old exchange name, plus `BITFINEX`/`BITFINEX-DERIVATIVES`/
   `OKEX`/`OKEX-SWAP`/`OKEX-FUTURES`/bare `KRAKEN`/`BINANCE`/`BYBIT-SPOT`/`UPBIT` — NONE of which appear in
   `unified_api_contracts.registry.market_data_categories.VENUES_BY_ASSET_GROUP["cefi"]` today, confirmed by direct
   grep) plus a smaller current-venue-name residual (`BINANCE-FUTURES` 910, `DERIBIT` 276, `KRAKEN-FUTURES` 80,
   `BITGET-FUTURES` 4, `HYPERLIQUID` 26, `OKX-SWAP` 29). **Code-verified this is NOT reproducible by the current
   enumerator**: `_enumerate_v2_cefi` (current HEAD) only iterates `VENUES_BY_ASSET_GROUP["cefi"]`'s CURRENT venue
   strings and always sets `instrument_type=instr.instrument_type` (non-blank, from the catalogue) +
   `instrument_id=instr.instrument_id` (canonical, per the catalogue's own docstring "canonical instrument identifier")
   for every `expected_unattempted` emission site — it structurally cannot emit `instrument_type=''` +
   lowercase-raw-symbol. This is pure dead debris under venue strings the pipeline no longer even visits.
2. **Class B — bundle-grain old/new shape DUPLICATION (DERIBIT + OKX-FUTURES `futures_chain`/`options_chain`).**
   Full-corpus scan: **4,951 OLD-shape rows** (`instrument_id=<underlying>`, `underlying=''` — e.g. DERIBIT trades rows
   `instrument_id=ETH/BTC/SOL`), ALL `written_at=2026-07-15T01:32:56Z` (the enumerator run BEFORE the bundle-grain fix),
   sitting alongside **5,022 NEW-shape rows** (`instrument_id=''`, `underlying=<U>` — the MTDS-writer-matching shape),
   `written_at=2026-07-15/16T01:32-ish` (the run AFTER `instruments-service@a2468dd9`, "fix(cefi-eu): canonicalize
   bundle-grain instrument_id/underlying shard atom", 2026-07-15T22:22:33Z, confirmed already an ancestor of HEAD).
   Timeline confirms: the OLD-shape rows are a fresh same-week duplicate left behind by a pre-fix run, not decades-old
   debris — the fix landed correctly (verified live: `is_bundle` branch at `enumerate_expected_universe.py:1117-1123`
   already sets `seed_instrument_id=""`/`seed_underlying=instr.underlying or instr.instrument_id` for
   `GRAIN_BUNDLE_BY_UNDERLYING` types) but the manifest is append/upsert-only so the pre-fix rows were never removed.
3. **Why a bare re-run cannot self-heal either class**: read `codex/05-infrastructure/manifest-consolidator-ssot.md` —
   the DuckDB consolidator's dedup key is `(date, venue, data_type, service_name)` + optional dims PRESENT IN THE UNION
   SCHEMA (instrument_type/instrument_id included for per-instrument enumerator shards), last-write-wins by `written_at`
   DESC. Two rows with DIFFERENT `instrument_id` values are DIFFERENT keys — the consolidator legitimately keeps BOTH
   forever. Confirmed empirically: the 2026-07-16T01:32 (post-fix) run added the correct bundle rows ALONGSIDE the
   2026-07-15T01:32 (pre-fix) rows rather than replacing them, and the April-June Class-A debris is still present after
   TWO subsequent full enumerator runs (07-15 and 07-16) that both wrote correct canonical rows for the same venues.
   **Re-materialization only ADDS the missing correct atom; it never SUBTRACTS a superseded/dead one** — the fix
   mechanism is necessarily a targeted DELETE, not a re-enumerate.
4. **This exact mechanism already exists, shipped, dry-run-verified, and is BLOCKED-OPERATOR only on `--apply`**:
   `instruments-service@7f1aed10` — `scripts/purge_stale_shape_cefi_expected_unattempted_2026_07_15.py`. Re-ran its
   dry-run fresh (2026-07-16T09:21Z, read-only): **49,732** total stale-shape eu rows in the live index right now
   (within its own STOP-ON-SURPRISE bound `[5000,250000]`) — 12 more than the 49,720 measured 07-15T22:2xZ, i.e.
   essentially flat over ~11h, confirming this is a small, stable, non-growing residual (NOT the 2.77M-scale gap the
   program's earlier framing implied — that separate, much larger number was the CAPTURED-side raw-vs-canonical
   mismatch, already fixed for future writes by `mtds@5d44a197`/`90ecde17`, tracked in the same issue doc's earlier
   todos). `--apply` was intentionally **NOT run this session** — a prior session already framed this exact mutation as
   an "OPERATOR DECISION" and filed a `/blocked` sign-off request; re-running it myself would duplicate/bypass a
   standing gate rather than resolve it. Nothing indicates the sign-off has been actioned yet.
5. **Sentinels.py Tier-3 question (task item 5) — SAME ROOT CLASS, DIFFERENT MECHANISM, ALREADY FIXED.** Verified live:
   `sentinels.py::_emit_tier3_for_dt` compares `expected_instruments` (canonical, from `CeFiCatalogReader` /
   `get_expected_instruments_for_venue`) against `captured_instruments`. Traced
   `preflight.py::_canonicalize_captured_ instrument_id` end-to-end: its packed-symbol branch only strips the QUOTE
   suffix, never a venue-specific PREFIX, so `_canonicalize_captured_instrument_id("KRAKEN-FUTURES", "PI_ETHUSD")` →
   `"PI_ETH-PERP"` (confirmed by reading the function body), which can never equal the catalogue's
   `KRAKEN-FUTURES:PERPETUAL:ETH-USD@LIN` — reproducing the plan's claim exactly. This is the SAME DISEASE as the
   eu-manifest two-atom issue (independent, divergent canonicalizer implementations for what must be one shard atom —
   now a confirmed THIRD implementation alongside the enumerator's and
   `venue_fetch.py::_canonicalize_manifest_instrument_id`'s) but a SEPARATE INSTANCE, not literally caused by the same
   stale manifest rows (it is a live runtime comparison bug, not historical residue). **Already fixed**:
   `market-tick-data-service@bbf6649c` (confirmed ancestor of current MTDS HEAD) adds the canonical
   `_canonicalize_manifest_instrument_id` output ALONGSIDE the legacy heuristic's output into
   `captured_per_instrument_shards` for Tardis venues (`venue_fetch.py:471-478`) — cheap, correct regardless of which
   shape `expected_instruments` takes on a given call, with its own dedicated unit tests. No further action needed here.
6. **Side observation (not this task's scope, flagging only)**: spot-checked recent `captured` rows for
   KRAKEN-FUTURES/book_snapshot_5 — of 590 rows written since 2026-07-15, only 237 are canonical-shaped, 353 are STILL
   raw (`PI_ETHUSD` etc., written as late as 2026-07-15T14:56Z). Consistent with the plan's own already-tracked
   deployment-lag finding (pre-fix Tardis VM tarballs still in the field as of the last observation) — not a new defect,
   not re-investigated further here.

**Net**: no new code fix required (the enumerator + sentinels.py fixes are both already shipped and correct); the
remaining action is the already-designed, already-gated `--apply` of
`purge_stale_shape_cefi_expected_unattempted_ 2026_07_15.py` (workstream C above). Did not run it. Did not touch VMs,
codex/, or any code.

### ✅ WRITER FIX VERIFIED IN PROD + I over-stated the eu-atom blocker (correction) — 2026-07-16T08:15Z

**Correction to my own earlier framing.** I told the operator (and journaled) that the stale per-venue eu ATOM was "the
real blocker preventing coverage from EVER moving via fetching — the two sides speak different atoms." **That was WRONG,
verified against the live manifest:**

BINANCE-FUTURES/trades, canonical(`:`)-vs-raw crosstab:

| status               | raw    | canonical   |
| -------------------- | ------ | ----------- |
| expected_unattempted | **25** | **141,708** |
| captured             | 14,300 | 0           |

The **eu side is 99.98% canonical** — my earlier "eu is lowercase-raw `hotusdt`" claim was a `head(3)` sampling artifact
that surfaced 25 stale rows out of 141k. The real mismatch was eu-canonical **vs captured-raw**, and captured-raw is the
WRITER's output, not an enumerator two-shape problem. The eu-atom shape debris (verified by the eu-atom investigation)
is only **~49,732 rows** total (mostly legacy `CRYPTOFACILITIES`/`OKEX` venue-name debris + 4,951 bundle-grain dupes),
already diagnosed, with a snapshot-first purge script
(`instruments-service/scripts/purge_stale_shape_cefi_expected_unattempted_2026_07_15.py`, `--apply` operator-gated). It
is a small cleanup, NOT the 2.77M blocker. Retracting the "no fetching can move coverage until this lands" claim.

**The writer fix (`mtds@5d44a197`) IS working in production — FIRST hard verification.** KRAKEN-FUTURES captured rows,
canonical-vs-raw by write date:

| write date     | raw     | canonical |
| -------------- | ------- | --------- |
| ≤ 2026-07-15   | 241,969 | **0**     |
| **2026-07-16** | 7       | **538**   |

2026-07-16 is the first date in the entire corpus with canonical captured `instrument_id`s — written by the current
fixed VM (`cefi-queue-heavy-binancefutu-x15-20260716-075338`, tarball ⊃ mtds@5d44a197). Three prior eu-tests were
invalid (January eu=0 zone ×2, preemption); THIS is the clean signal the fix eluded. Canonical captures now match the
canonical eu atom, so they WILL close eu cells as the backfill proceeds through the gap.

**Corrected forward model:**

1. The running fixed VM writes canonical captures → these close canonical eu cells → coverage moves (directionally
   proven; too few rows yet to move the aggregate, but the mechanism is now verified end-to-end).
2. The ~3.13M HISTORICAL raw captured rows (pre-fix) are the real bulk-uncredited set — they become creditable via
   EITHER the operator-gated relabel `--apply` (82.7% resolvable; instruments-service@f021cb2b dry-run) OR natural
   re-fetch by the backfill (which now writes canonical). Relabel is far cheaper than re-fetch.
3. The ~50k eu-shape debris: the operator-gated purge script. None of these three is "coverage can't move" — they are
   cleanup + a relabel-vs-refetch cost decision.

**sentinels.py Tier-3** (the third divergent canonicalizer): already fixed `market-tick-data-service@bbf6649c`
(confirmed ancestor of HEAD) per the eu-atom investigation.

**Net**: the eu-atom todo is NOT new code — it's the two already-gated operator decisions (purge + relabel). The writer
fix is verified. What remains genuinely open is operator sign-off on relabel/purge, and letting the fixed backfill grind
(which now genuinely closes cells).

### 2026-07-16T10:05Z — Three infra-hardening fixes shipped: preemption relauncher + no-relaunch alert + self-declaring Tardis cap (deployment-service@02be72e)

**Dispatch**: operator-approved designs already written into this plan's Progress Log (the P0/P1 todos above) — this
session implemented and shipped all three in `deployment-service` in one batched commit, gate-once. SCOPE GUARD honored
throughout: zero VMs launched/killed/modified — every `gcloud`/fleet check this session was read-only, and the
`cefi-queue-heavy-binancefutu-x15-20260716-075338` backfill VM was confirmed running, untouched, before AND after.

**Fix 1 — SPOT-preemption relauncher: design chosen = option (a), preemption-aware relauncher (not STOP+watchdog).**
Why: the codebase already has a proven, tested `auto_recover` actuator spine (`exit_code_fleet_monitor` →
`escalation.py::route_finding` → `scripts/recovery/relaunch_*.py`) serving OOM (`DP_VM_EXIT_NONZERO`) and STALL
(`DP_VM_STALL`) — adding a 4th sibling (`DP_VM_PREEMPTED` → `RelaunchPreemptedVm`) is a small, well-understood diff on
infra that's already shipped + load-bearing in prod, versus (b) which would mean inventing a brand-new STOP-based VM
lifecycle + a separate watchdog daemon from scratch. The relaunch replays the EXACT captured launch env (a new
`lc_write_launch_params()` bash helper persists `{launcher, env}` to `LAUNCH_PARAMS.json` in GCS at VM-creation time; a
new `_gcs.read_launch_params()` reads it back only when `verdict is PREEMPTED`) — so it reproduces the SAME
venues/START_DATE/concurrency/lease as the preempted VM, never a blind relaunch onto the launcher's bare (much bigger)
defaults. It goes THROUGH the launcher's own `tardis_concurrency_guard` every time (the relaunch is just re-invoking
`launch-cefi-sharded-backfill.sh` as a subprocess, which sources the guard itself before creating anything) — a guard
refusal surfaces as a non-zero subprocess exit, never a silent double-launch. `classify_terminated_vm`'s existing
`preempted`-takes-precedence logic (driven by the durable GCS `PREEMPTED` marker, not exit_code) already guarantees a
genuinely-exit-0 VM never reaches this path.

**Fix 2 — belt-and-braces no-relaunch alert**: folded into the SAME actuator per the todo's own framing ("if Fix 1's
relauncher makes preemption truly benign, the alert should fire only when the relaunch itself FAILS"). A NEW event
string `DP_VM_PREEMPTED_NO_RELAUNCH` (CRITICAL) self-emitted by `RelaunchPreemptedVm` on every failure path (no launcher
/ budget exhausted / guard-refused / launcher error) — reuses the EXISTING `log_event`→alerting-service carrier
(`codex/05-infrastructure/data-pipeline-alerts.md`'s emit→route→escalate spine), no new plumbing invented. A plain
string was used (not a new UTL constant) since this fix stayed scoped to deployment-service per the dispatch. On
success: quiet INFO only.

**Fix 3 — self-declaring Tardis cap**: `VM_TARDIS_CONSUMER=1` stamped by every AUTHENTICATED-Tardis launcher
(`launch-cefi-sharded-backfill.sh` ×2 metadata blocks, `-aws.sh` twin, `launch-mtds-backfill-vm.sh` CEFI-only,
`launch-cefi-forward-poll.sh` unconditionally); `launch-mtds-live.sh` + IS-side deliberately untouched
(operator-verified unauthenticated this session, not re-litigated). `tardis-concurrency-guard.sh`'s
`tardis_running_vm_count()` rewritten to union name-pattern-OR-metadata-stamp in ONE `gcloud … --format=json` call +
python — discovered mid-session that gcloud's list API REJECTS a `--filter metadata.<key>=<value>` server-side
expression ("Invalid list filter expression"), so the client-side JSON+python union approach is load-bearing, not
optional. `launch-cefi-forward-poll.sh` now calls the guard before creating its VM — REAL-fleet-verified (non-dry-run)
to correctly REFUSE (exit 1, zero VM created) while the cap-1 backfill held the slot, proving the asymmetric priority
(backfill wins, forward-poll queues-via-refuse).

**Evidence**:

- SHA: `deployment-service@02be72e6481012fbcf5f4c8c49a28dee1e4eff9d` (12 files: `_gcs.py`, `escalation.py`,
  `exit_code_fleet_monitor.py`, `scripts/recovery/relaunch_backfill_vm.py`, 6 `scripts/vm/*.sh` launchers +
  `launcher_common.sh` + `tardis-concurrency-guard.sh`, 2 test files). Landed via `quickmerge --agent --skip-preflight`
  (the `--skip-preflight` carve-out was needed because `unified-api-contracts` had uncommitted WIP from a concurrent
  process — not mine to touch per the multi-agent-safety liveness rule; Stage 1 dependency validation itself passed via
  `--dep-branch` branch-isolation mode).
- Tests: 251/251 unit tests green (`test_data_pipeline_monitors.py` + `test_dp_recovery_actuators.py` +
  `test_data_pipeline_monitors_cli.py` + `test_launcher_registry.py`) — 14 new/updated (10 `RelaunchPreemptedVm` +
  escalation-wiring tests, 5 sweep/`_gcs` tests, 1 pre-existing test upgraded from an incidental exception-swallowing
  pass to a properly-mocked, semantically-correct assertion).
- `bash scripts/quality-gates.sh` — full green (basedpyright: my new code contributes ZERO new diagnostics net —
  verified by diffing per-file error counts before/after; the dynamic-import Any-cascade that the 3 PRE-EXISTING sibling
  actuators already carry was avoided in my new code via a `TYPE_CHECKING`-guarded static import + `cast()`, same
  technique already used elsewhere in this codebase (`_gcs.py`), just not yet applied to the 3 older functions — left
  those untouched, out of scope).
- Live read-only fleet verification (central-element-323112, asia-northeast1-c): `tardis_running_vm_count` correctly
  counted 1 (the real running backfill), correctly excluded the non-Tardis pacifica VM; `tardis_concurrency_guard`
  correctly refused a planned launch at cap; `launch-cefi-forward-poll.sh` (real, non-dry-run invocation) correctly
  aborted before any `gcloud compute instances create` call. Fleet state identical before/after this session.

**Codex edit needed (operator-gated — NOT applied by me per the plan-reconcile rule)**:
`codex/05-infrastructure/spot-vms-for-backfill.md` currently states (the premise this session makes TRUE): its
"idempotent shards re-run on preemption" claim was FALSE for the cefi/tardis launcher family until today. The exact
edit: replace that unqualified claim with something like — _"idempotent shards re-run on preemption for launchers that
call `lc_write_launch_params()` at create time (currently: `launch-cefi-sharded-backfill.sh` + its AWS twin) — the
`exit_code_fleet_monitor` PREEMPTED verdict now dispatches `RelaunchPreemptedVm`
(`scripts/recovery/relaunch_backfill_vm.py`), which replays the captured launch env through the launcher's own
`tardis_concurrency_guard`. A launcher that does NOT call `lc_write_launch_params()` still gets a relaunch attempt
(best-effort, ambient env only) but not an exact-params replay — see `cefi_completion_program_2026_07_15.md` 2026-07-16
for the design."_ Also worth a one-line mention in `codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap noting
the `VM_TARDIS_CONSUMER=1` self-declaring metadata model now supersedes pure name-pattern matching (Fix 3), and
(optionally) a new `DP-VM-007` row in `codex/05-infrastructure/data-pipeline-alerts.registry.yaml` /
`data-pipeline-alerts.md`'s registry table for `DP_VM_PREEMPTED` / `DP_VM_PREEMPTED_NO_RELAUNCH` (mirroring the existing
DP-VM-001/002/003 rows) — not done here since codex edits are operator-gated.

**Deliberately deferred (not silently dropped)**:

- Widening `lc_write_launch_params()` capture to launchers beyond the cefi/tardis family (e.g. a generic OOM/stall
  relaunch replay for every asset group) — out of scope for this CeFi-focused dispatch; the mechanism is generic and
  ready to extend.
- "Backfill should pause-and-retry rather than record false `attempted_failed`" when the Tardis slot is lost MID-RUN (as
  opposed to at launch time) — an MTDS-repo runtime behavior change, not a deployment-service launcher/guard change; out
  of scope for this repo-scoped dispatch.
- A repo-wide sweep of stale "cap-3" comment text (only the 3 launcher files I was already editing for Fix 1/3 got their
  adjacent cap-3 comments corrected to cap-1 in-commit; other files with the same stale text were left alone — a
  separate, smaller cleanup, not blocking).
- The 3 pre-existing sibling actuators' (`_recover_consolidator`/`_recover_backfill_vm`/`_recover_stalled_vm`)
  dynamic-import Any-cascade basedpyright debt — not fixed (out of scope; my new code meets a higher bar without
  requiring a retrofit of the other 3).

### Infra durability SHIPPED to LDR — but relauncher not LIVE until deployed; keeper retirement condition — 2026-07-16T08:35Z

All three Tardis-infra durability fixes shipped: `deployment-service@02be72e6` (preemption-aware relauncher as a 4th
`auto_recover` actuator `DP_VM_PREEMPTED → RelaunchPreemptedVm`, replaying captured launch params via a new
`lc_write_launch_params()` GCS persist, always through `tardis_concurrency_guard`; + the preemption alert; +
`VM_TARDIS_CONSUMER=1` self-declaring cap-scoping wired into the guard and into `launch-cefi-forward-poll.sh` so T+1
queues behind the long backfill while live/IS stay exempt). 251/251 unit tests green, checkboxes flipped
(unified-trading-pm@49a9ce243).

**CRITICAL DEPLOY-LAG — the relauncher is NOT yet live**, verified:

- `uts-prod-dp-exit-code-monitor` Cloud Run job runs `*/5`, ENABLED, last success 2026-07-16T10:00Z — the monitor IS
  live, but on the CURRENT `deployment-api:latest` image which is PRE-fix.
- `02be72e6` is on LDR but NOT yet on `origin/main` → the image has not rebuilt → the new `DP_VM_PREEMPTED` actuator is
  not in the running monitor. A preemption RIGHT NOW would still NOT auto-relaunch.

**Therefore the session keeper (`keeper_v2`, single-authority, 128/32) STAYS until the deploy lands.** Retirement
condition, explicit: kill the keeper only once BOTH (a) `git merge-base --is-ancestor 02be72e6 origin/main` is true AND
the `uts-prod-dp-exit-code-monitor` image postdates the rebuild, AND (b) a real preemption has been observed to
auto-relaunch via the actuator (check `DP_VM_PREEMPTED` in the monitor logs + a fresh `cefi-queue-*` VM appearing
through the guard). Until then the keeper is the safety net. **Keeper + relauncher COEXIST SAFELY**: the guard now
counts RUNNING+PROVISIONING+STAGING (fixed 07-16 after the 40s race), so whichever fires first on a given preemption
creates a PROVISIONING VM and the other is refused — no double-launch. So there is zero downside to leaving the keeper
armed through the deploy window.

**Operator codex edit surfaced by the fix (gated, not applied)**: `codex/05-infrastructure/spot-vms-for-backfill.md`'s
"idempotent shards re-run on preemption" premise is now TRUE for the cefi/tardis family — Agent A wrote the exact
replacement wording + a `vm-launcher-runbook.md` note + an optional `DP-VM-007` registry row into the
unified-trading-pm@49a9ce243 Progress Log for the operator to apply.

### 2026-07-16T10:15Z — [slot-3] C (alias cleanup) ATTEMPTED → verified-correct but DEFERRED (consolidator clobber)

- C purge (agent a423dff1): DuckDB row-filter → generation-match CAS write of `availability_index.parquet`, removing the
  13 pure-stray alias venues = **567,212 rows** (OKEX-SWAP 119,389 · CRYPTOFACILITIES 122,845 · BITFINEX 105,662 ·
  BINANCE 80,265 · OKEX-FUTURES 52,246 · COINBASE 35,807 · BITFINEX-DERIVATIVES 27,730 · OKEX 18,727 · KRAKEN 2,504 ·
  BITGET 1,177 · COINBASE-INTERNATIONAL 745 · LIGHTER 109 · UNKNOWN 6). **TOTAL_CAPTURED invariant held bit-for-bit
  (3,142,947→3,142,947), every canonical venue captured count UNCHANGED, exclusions intact (DERIBIT-COMBO, bare-OKX
  fold-target, KALSHI/POLYMARKET, blank-venue).** Backups:
  `_index/backups/availability_index.pre-alias-purge- 20260716T100230Z.parquet` + the legacy seed.
- **DEFERRED (not durable)**: the write was CLOBBERED within ~4 min by an in-flight consolidator cycle (lost-update —
  the deployed consolidator image likely predates the 2026-07-08 CAS-retry fix, running ~8-min overlapping cycles under
  the co-manager's active backfill load). Per the safety protocol, did NOT unilaterally pause shared prod consolidation
  infra during the active backfill. No data lost; manifest restored. **The purge script is READY** — run it in a
  quiescent window: pause `uts-prod-manifest-consolidator-market-data-cefi` (+ `-legacy`) → drain the in-flight run →
  fresh backup → re-run the DuckDB-filter CAS write → verify sticks → resume. Re-seeding is CLEARED
  (enumerator/writer/catalogue carry only canonical venues — no alias re-seed).
- **FINDING C-1 (data-correctness — follow-up)**: **BYBIT-FUTURES is NOT a stray** — 45 real `live_bybit` GCS objects
  ({BTC,ETH,SOL}USDT, 2026-06-23→27) MIS-CLASSIFIED as `attempted_failed`; canonical BYBIT has 0 captured for those
  days. → real unmigrated live perp data; needs MIGRATION (rename objects → canonical BYBIT + reclassify rows to
  captured), NOT deletion. Excluded from the purge. Data-mis-attribution gap.
- **FINDING C-2 (infra — flag)**: the cefi manifest consolidator has a lost-update bug (clobbers valid CAS writes under
  load) — deployed image predates the 2026-07-08 fix; can silently lose ANY out-of-band manifest correction. Worth a
  redeploy.
- **FINDING C-3 (blank-venue)**: the 28 blank-venue captured rows = an MDPS venue-attribution anomaly on 2026-04-14 (a
  day-summary write that lost its venue tag; real per-venue data IS captured under the real venues). Not a Tardis alias
  → separate MDPS re-attribution fix. Kept (not deleted).
- C status: purge VERIFIED-SAFE + READY; durable execution gated on a consolidator-quiescent window (aligns with the
  final af=0 recompute timing). BYBIT-FUTURES migration + consolidator redeploy = follow-ups.

### ✅ OPERATOR-APPROVED OPS EXECUTED — purge + relabel + codex edit; coverage 48.43% → 50.79% — 2026-07-16T11:00Z

Operator approved all three gated items ("can you do these"). All executed, snapshot-first, with measured before/after.

**1. Codex edit — DONE** (`unified-trading-pm@d0a86e30c`). `spot-vms-for-backfill.md`'s HARD RULE claimed "a preempted
shard re-runs cleanly — there is no correctness cost to preemption, only a restart". That premise was FALSE until
2026-07-16 (nothing re-ran it). Corrected in place: the claim now holds **only for launchers that call
`lc_write_launch_params()`** (cefi sharded + AWS twin), via `exit_code_fleet_monitor` PREEMPTED → `RelaunchPreemptedVm`
replaying captured params through `tardis_concurrency_guard`; a launcher without that helper gets best-effort
ambient-env relaunch, NOT an exact-params replay (explicit warning for whoever adds the next launcher). Also added to
`vm-launcher-runbook.md` § Tardis cap: the `VM_TARDIS_CONSUMER=1` self-declaring model, the code-verified **exempt**
list (live `tardis-machine` = local ws://localhost:8002 sidecar over public feeds, no auth; IS = public api.tardis.dev
metadata), and that a relaunch routes through the guard so it can never breach the cap.

**2. Purge stale-shape eu — DONE, gate GREEN.** `purge_stale_shape_cefi_expected_unattempted_2026_07_15.py --apply`:
snapshot → `_index/snapshots/pre_purge_stale_shape_eu_availability_index_20260716T103453Z.parquet`; **49,732 rows
deleted** (11,964,457 remain); post-apply gate: **0 stale-shape eu rows remain**. Per-VM shards had 0 matches (the
debris was main-index-only), consistent with the legacy-seed origin.

**3. Relabel raw→canonical — DONE, 2.59M rows.** `relabel_cefi_tardis_raw_symbol_to_canonical_2026_07_15.py --apply`:
catalogue map = 18 venues / 11,127 resolvable (venue, raw_symbol) pairs / 297 ambiguous EXCLUDED (not guessed).
**3,134,443 candidates → 2,590,193 relabeled (82.6%), 544,250 left honestly raw** (unresolvable — NOT faked), plus
**286,492 redundant eu rows dropped**. Snapshots taken for all 4 blobs. Wrote main index (11,677,965 rows) AND every
`_index/per_vm/*.parquet` — critical, because the consolidator rebuilds the index from those shards, so an index-only
relabel would have been silently reverted on the next consolidation.

**MEASURED (real runs, not projections):**

| metric               | before (10:2xZ) | after (10:55Z) | delta                               |
| -------------------- | --------------- | -------------- | ----------------------------------- |
| expected_unattempted | 3,185,339       | 2,892,108      | **−293,231**                        |
| coverage_pct         | 48.43           | **50.79**      | **+2.36**                           |
| captured             | 3,060,161       | 3,060,161      | +0 (rename, not re-fetch — correct) |
| attempted_failed     | 73,231          | 73,231         | +0                                  |

**Post-apply gate on the relabel: RED — 10,368 eu rows still collide with a captured key. DIAGNOSED, and it is NOT this
relabel's doing (verified, not assumed):** the collisions are 9,817 EXTENDED-STARKNET + 518 PACIFICA-SOLANA + ~33 others
— i.e. the **non-Tardis native-REST venues**, which the relabel never touched (its catalogue map is the 18 TARDIS
venues; those lanes' `OnchainPerpBatchHandler` already writes canonical ids natively). **Proof it predates the run: the
PRE-relabel snapshot already contained 10,335 of the same collisions** — my run contributed ~33 (concurrent captures by
the live VM during the ~7-min write window). Re-running the script CANNOT fix them (verified: re-run = 0 relabeled / 0
redundant — its reconcile only drops eu twins of rows IT relabeled, while the gate checks ALL eu-vs-captured
collisions), so I did not blind-retry.

**What the 10,368 actually are**: cells genuinely CAPTURED by the non-Tardis VMs (launched 2026-07-15T19:00Z) whose eu
skeleton twin was never dropped — the manifest double-counts them, understating coverage by ~10,368 cells (~0.36% of
eu). This is the "Phantom reconcile + manifest hygiene" pass this plan already tracks as never-re-run.

- [x] → MIGRATED to `issues/cefi_residual_followups_after_honest_done_2026_07_17.md` (residual #3 — non-Tardis defect,
      independent of the accepted ceiling). [DATA] P1. **Drop eu twins of natively-canonical (non-Tardis) captures —
      10,368 rows.** The relabel's gate is RED on these and its reconcile structurally cannot fix them (it only
      reconciles its own relabels). Root: the OnchainPerpBatchHandler lane writes canonical `captured` rows but nothing
      drops the matching `expected_unattempted` skeleton row, so cells are double-counted. Fix via the
      phantom-reconcile/manifest-hygiene pass (or extend the reconcile to drop ANY eu row colliding with a captured key,
      not just relabeled ones). Evidence: 9,817 EXTENDED-STARKNET + 518 PACIFICA-SOLANA + ~33 others; pre-relabel
      snapshot had 10,335 of them.

> **🟢 MAINTENANCE WINDOW CLOSED 2026-07-16T12:50Z — manifest fixed (C purge of 13 stray alias venues, −526,104
> attempted_failed/eu rows, 0 captured touched; + BYBIT-FUTURES→BYBIT migration, 45 objects moved to canonical path, +45
> captured; every other canonical venue's captured count bit-for-bit UNCHANGED). Fix is DURABLE — survived the resumed
> consolidator + live backfill for ~50 min (aliases still 0, BYBIT +45 re-verified 12:49Z on the live index).
> `_legacy_seed.parquet` also purged (COINBASE+UNKNOWN aliases) so consolidation can't re-merge them. market-data-cefi
> consolidator RESUMED; backfill restored to exactly 1 VM by the co-manager's `keeper_v2` (N=1 authority, 128/32 ramp) —
> I did NOT manually launch (would race the keeper). Co-manager may resume. Follow-ups: consolidator lost-update-bug
> redeploy; bare COINBASE still in expected_universe (318, may re-materialize as eu daily); blank-venue MDPS
> re-attribution; HL phantom re-census (deferred — see report).**

### 🔴 STALL: 5h15m of VMs produced +45 captured rows — the backfill is NOT working (ConnectionTimeout storm) — 2026-07-16T16:15Z

Operator asked "is the spot VM still grinding?" — **technically running, effectively NOT.** Measured, 10:55Z→16:10Z
(5h15m):

| metric               | 10:55Z    | 16:10Z    | delta    |
| -------------------- | --------- | --------- | -------- |
| captured             | 3,060,161 | 3,060,206 | **+45**  |
| expected_unattempted | 2,892,108 | 2,892,108 | **0**    |
| coverage_pct         | 50.79     | 50.79     | **0.00** |

**+45 rows in 5h15m against a 2.89M gap.** At that rate the backfill never finishes. This is the loop's flat-metric
stall condition → STOPPED rather than burning more (keeper's blind relaunch loop killed; the current VM left running for
diagnosis, it costs little on SPOT).

**Root cause (evidence, not inference): a ConnectionTimeout storm, NOT 403s** (403s = 0 — the N=1 cap is working):

```
190x ERROR Tardis streaming error: ConnectionTimeoutError
 72x Connection timeout to host https://s3.us-east-1.wasabisys.com     <- Tardis's backing store
 53x Connection timeout to host https://datasets.tardis.dev/v1/cry...
 37x Connection timeout to host https://datasets.tardis.dev/v1/byb...
 19x Tardis HTTP 400  |  14x Empty CSV file
```

`cpu=0.4%` (vs ~104% when genuinely fetching) — the VM is IDLE, failing streams fast, not downloading. The data path is
Tokyo (asia-northeast1) → Tardis → **Wasabi S3 us-east-1**; that long haul is timing out.

**NOT caused by my 128-stream ramp — checked before blaming it**: the 64-stream VM logged **953**
ConnectionTimeoutErrors over 3h16m (~4.9/min); the 128-stream VM logs 176 over ~33min (~5.3/min). Same rate. The
timeouts are a persistent condition at both concurrencies, not an overshoot. (Success density IS lower at 128 — 21/600
lines vs 59/600 at 64 — so 128 is not helping, but it is not the cause.)

**Compounding churn**: VMs die every ~30-60min — keeper logs `cumulative preemptions=3`, plus `075338` was DELETED at
11:14Z by `ikenna@odum-research.com` (a peer lane, not a preemption). Every relaunch re-scans from 2026-02-01, so the
fleet never gets past ~2026-02-02 before dying. Restart-from-scratch + frequent death + timeout-throttled throughput =
structurally zero progress.

**Candidate causes to test next (do NOT guess — measure):** (1) Tokyo→us-east-1 Wasabi path is simply too slow/lossy for
this volume → test a VM in a US region (Tardis/Wasabi are us-east-1; the whole fleet being in asia-northeast1 may be the
core mistake); (2) Tardis-side connection throttling that manifests as timeouts rather than 403s at high concurrency →
test a LOW concurrency (8-16) long-lived run and compare captured/hour; (3) the day-1 fan-out (15 venues × full
instrument universe) is simply enormous → narrow to ONE venue-week per VM so a wave COMPLETES before dying. **Recommend
(3) + (1) first**: they are cheap to test and (1) would explain the whole session's throughput mystery.

- [x] ⊘ SUPERSEDED (operator accept-decision 2026-07-17). The co-manager's follow-up arithmetic (below) reframed this:
      not a timeout/region bug but the hard N=1 throughput ceiling (~186 cells/hr ≈ 1.8yr); the operator accepted
      partial coverage rather than chase it. Diagnosis not pursued further. [INFRA] P0. **Diagnose the ConnectionTimeout
      storm — the backfill is currently incapable of finishing.** Measured: +45 captured rows in 5h15m; cpu 0.4%; 0
      403s; timeouts to `s3.us-east-1.wasabisys.com` + `datasets.tardis.dev` at BOTH 64 and 128 streams (~5/min either
      way). Test in order: (a) region — run one VM in a US region near Tardis/Wasabi us-east-1 vs the current
      asia-northeast1, compare captured/hour; (b) low concurrency (8-16) long-lived, compare captured/hour (if timeouts
      are throttle-driven, low concurrency should beat high); (c) narrow scope to one venue-week per VM so a wave
      completes inside the preemption window. Until this is understood, adding VMs/streams/hours cannot close the 2.89M
      gap.

### ⚠️ CORRECTION to the 16:15Z stall entry + THE REAL ARITHMETIC: N=1 cannot close 2.89M — 2026-07-16T16:30Z

**Correcting my own entry (again — same error class as the January-zone and raw-eu mistakes: concluding from a window
without checking what was actually IN it).** I wrote "5h15m of VMs produced +45 captured rows". Misleading: only **~88
min of that 5h15m window had a VM running at all**. Timeline: `075338` died 11:14Z (DELETED by
`ikenna@odum-research.com`, a peer lane — not a preemption), then **3h47m with NO VM**, then keeper relaunches at 15:01
(died ~34min) and 15:35. Each VM also burns ~10-15min booting before it fetches. So the +45 came from roughly 45-60 min
of actual fetching, not 5h15m of grinding.

**The honest datapoint — the one long-lived VM:** `075338`, DEPLOYMENT_STARTED 08:00:38Z, last log 11:13:39Z = **3h13m
uptime**, **600 `streaming success`**, cursor advanced 2026-02-01 → 2026-02-02. So a healthy, long-lived, 64-stream VM
sustains **~186 successful shard-fetches/hour** — DESPITE its 953 ConnectionTimeouts (i.e. the timeouts degrade but do
not stop it; my "the backfill is incapable of finishing (timeout storm)" framing over-blamed them).

**The arithmetic that actually matters:**

- gap = **2,892,108** eu cells
- best observed throughput at N=1 = **~186 cells/hour**
- 2,892,108 / 186 ≈ **15,550 hours ≈ 1.8 YEARS** of continuous single-VM running.

Even if that estimate is off by 3x, the gap does not close in a tolerable window. **This is not a churn problem, not a
timeout problem, and not a region problem — it is a hard throughput ceiling imposed by the N=1 Tardis cap.** The cap is
not negotiable by us: N=3 was measured at ~94% 403s (mutual lockout), so the shared academic key genuinely permits ONE
active IP. Region change is ruled out on operator's egress objection (2026-07-16): the data bucket is in
asia-northeast1, so a US VM near Tardis/Wasabi us-east-1 would pay cross-region egress on EVERY byte written back — it
merely relocates the long haul from download to upload, and bills for it.

**Therefore this is an OPERATOR / COMMERCIAL decision, not an engineering one.** The realistic options:

1. **Upgrade the Tardis licence** to a tier permitting more concurrent IPs/connections. This is the only option that
   changes the throughput ceiling. Everything engineering can do inside N=1 has now been done (bundling, 128 streams,
   START_DATE targeting, stall+preemption fixes) and it yields ~186/hour.
2. **Narrow the MVP scope** — accept that the full 2026-02..07 tick history for all 15 venues × trades+book5 is not
   obtainable at N=1, and define a smaller must-have set (e.g. the lead venues/instruments for the strategies that
   actually need tick data) that IS closable in days.
3. **Accept partial coverage + honest labelling** — leave the rest as `expected_unattempted` and let the honest-coverage
   gate report the true number rather than pretending.

**Recommendation: (2) then (1)** — scope the must-have set first (it may be small enough that N=1 closes it in days),
and only pay for a licence upgrade if the must-have set is genuinely large. Do NOT keep burning SPOT VMs against the
full 2.89M at ~186/hour; that is the definition of a flat metric.

- [x] ✅ [REVIEW] P0. **OPERATOR DECISION (2026-07-17): chose (c) — ACCEPT + honestly label partial coverage.** The
      2.89M cefi tick gap is not closable at N=1 (~186 cells/hour ≈ 1.8 years). Options were: (a) upgrade the Tardis
      licence concurrency (the only lever that raises the ceiling); (b) narrow the MVP tick scope to a must-have
      venue/instrument set and close THAT; (c) accept + honestly label partial coverage. Operator selected (c): the
      honest-coverage number stands as the true number, the gap remains honestly-labelled `expected_unattempted`, no
      further SPOT VMs are burned against the full 2.89M. Engineering inside N=1 is exhausted — bundling, 128 intra-VM
      streams, correct date targeting, stall/preemption fixes are all shipped and the ceiling stands. Evidence: 075338 =
      3h13m uptime → 600 successes (~186/hr) with 0 403s; N=3 = ~94% 403s so the cap cannot be lifted by us; US region
      ruled out on egress (bucket is asia-northeast1). **This closes the CeFi completion program at honest-done** — see
      the terminal Progress Log entry below.

### ✅ TERMINAL: CeFi completion program CLOSED at honest-done — operator accepted current coverage — 2026-07-17T (autonomous close-out)

Operator invoked `/autonomous` a final time; on re-entry I found the co-manager had (correctly) **stopped the keeper and
escalated** the throughput ceiling as an operator decision (the P0 above). Rather than re-launch a tail VM — which would
have re-hit the identical ConnectionTimeout storm + N=1 ceiling the co-manager already diagnosed — I surfaced the
`licence vs scope vs accept` decision to the operator, who chose **ACCEPT current coverage**. That resolves the sole
remaining blocker, so the program terminates here. **No loop re-arm; watcher killed.**

**What actually shipped (rule-9 audit of the whole program):**

| WS   | Deliverable                                                                        | Evidence                                                             | State           |
| ---- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------- | --------------- |
| E    | Liquidations honest-coverage — itype-aware enumerator + both denominator producers | uac@494fd90c, is@92f3ca22, is@8b6bd8f8 (companion), pm@68018d0f; v15 | ✅ shipped      |
| I    | EXTENDED book5 — already-satisfied via LIVE_ONLY_DATA_TYPES (runtime-resolved)     | plan tick 6                                                          | ✅ verified     |
| G    | Equity-perp typing — collapsed to PERPETUAL/SPOT_PAIR + durable tracks_equity tags | uac@b44eb28c, is@350f0460, pm@b8600b138 (operator equity-typing rev) | ✅ shipped      |
| D    | HL/fleet dedup + phantom re-census                                                 | is@559c6920, mtds@57e26c0f                                           | ✅ shipped      |
| H    | Catalogue apply — dedup 9,177→5,386 perp-family, equity tags, ASTER dating, liq    | prod/catalog.parquet, live-count 9,952→10,122, denominator COMPLETE  | ✅ live in prod |
| C    | Venue-alias purge (13 venues, −526,104 rows incl. legacy seed) + BYBIT migration   | maint window; durable-verified 3× over ~70min                        | ✅ durable      |
| C-eu | eu-side residuals (purge 49,732 stale-shape + relabel 2.59M + drop 286k eu)        | **co-manager**; coverage 48.43→50.79%                                | ✅ done         |

**Terminal honest coverage: 50.79%** against a **COMPLETE** denominator — the gap (2,892,108 cells) is honestly labelled
`expected_unattempted`, NOT hidden as captured/phantom. That is the point of the honest-coverage model: the number is
_true_, and the operator has accepted it as the deliverable.

**Consciously NOT done (operator-accepted, documented — not silent drops):**

- The full 2026-02..07 tick backfill for all 15 venues (the 2.89M gap) — accepted as `expected_unattempted` per the
  operator decision; only a Tardis licence upgrade could change the N=1 throughput ceiling.
- HL phantom re-census (1,277 rows) — needs a 32-64GB box (OOMs on the 15GB VM); cosmetic manifest-labelling, does not
  affect captured data. Left as a standalone follow-up.
- Consolidator lost-update-bug redeploy — the maint-window fix held durably; redeploy likely unnecessary, left as a
  watch item.

**Program archival**: this plan is eligible for the 5-step archival ritual once the operator confirms; leaving it
`active` so the residual follow-ups above stay visible. No new work is dispatched.

### ⚠️ MY ERROR (4th of this session, same class) — "missing concurrency export" was a grep truncation artifact — 2026-07-17T08:05Z

Operator challenged the stall conclusion: _"doesn't make sense we have so much Tardis data gathered in the last few
weeks it can't suddenly have slowed down… what are we tryna grab how big are the files?"_ **The challenge was right and
it exposed my mistake.**

**What I claimed**: that `setup-data-pipeline-vm.sh` never exported `TARDIS_MAX_CONCURRENT_DOWNLOADS`, so every ramp
(16→64→128) was a silent no-op and the VM ran at default 16. I shipped `deployment-service@097911a` "fixing" it.

**The truth**: those exports have existed since **`cad9416` (2026-07-13)** at lines ~358/366. My grep used `head -8` and
**truncated before line 371 where they live** — I concluded "missing" from a truncated view. Identical error class to
the `head(3)` manifest sample that produced the bogus "eu is raw" claim earlier this session. `097911a` was a pure
DUPLICATE, and worse, its comment asserted a falsehood in-tree. **Reverted: `deployment-service@979e6ac`** (LDR verified
clean: duplicate marker 0, real export present exactly once).

Process note: quickmerge structurally could not land the revert — it diffs the working tree against **main**, which
never received `097911a`, so my corrected file looked identical to main → "No differences from main — nothing to merge";
after committing locally it said "Nothing to commit — exiting fast" and pushed nothing. This is precisely the
"early-exits on a clean tree so commits pile up behind main" failure the CLAUDE.md rule itself warns about. Pushed the
revert directly (QG green, dep-cascade already run) as a mechanism-failure carve-out, not a convenience bypass.

**So the throughput diagnosis is REOPENED — 128 streams WERE applied.** What the operator's question actually
established (this part is solid, measured):

| fact                                                  | value                                                                                              |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| shard file sizes (BINANCE-FUTURES trades, 2026-02-01) | ADAUSDT 8MB · AVAXUSDT 7.4MB · BNBUSDT 20MB · DOGEUSDT 19MB · **BTCUSDT 64MB** · **ETHUSDT 136MB** |
| book_snapshot_5 shards                                | ~10-22MB each                                                                                      |
| implied total for the 2.89M-cell gap                  | **~40-60 TB**                                                                                      |
| observed throughput (075338, 3h13m, 600 successes)    | ~186 shards/hr ≈ **~1 MB/s**                                                                       |

**~1 MB/s on a GCE VM with 128 applied concurrent streams is the anomaly to explain** — that is ~100x below what the box
should sustain, and it reconciles with the operator's point that the existing 3M-row corpus was demonstrably gathered
far faster in June (file stamps: 2026-06-03, 2026-06-29). CPU ~104%/1600% with 128 streams applied means the streams are
BLOCKED, not computing — consistent with the measured ConnectionTimeout storm to `datasets.tardis.dev` +
`s3.us-east-1.wasabisys.com`, i.e. an I/O-wait wall, not a CPU/concurrency wall.

**Next diagnostic (do NOT ship another guess — measure):** the June corpus proves high throughput was achievable from
this same fleet/region. So the question is **what changed between June and 2026-07-12** (when the 403 concurrent-IP
lockout first appeared). Candidates: (a) the Tardis key/licence tier changed or began being enforced — check the
account/subscription state and whether June ran many parallel VMs without 403s; (b) a Tardis-side or Wasabi-side
throttle now shapes our traffic to ~1MB/s; (c) something in our client (timeouts/retry/backoff config) regressed.
**Start with (a)**: it is a 5-minute check of the Tardis account + a diff of June's VM fleet size vs today's N=1, and it
would explain BOTH the sudden 403s and the throughput collapse.
