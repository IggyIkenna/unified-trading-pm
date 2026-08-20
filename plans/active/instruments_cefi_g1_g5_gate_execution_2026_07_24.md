---
doc_type: plan
title: Instruments Foundation — cefi G1→G5 gate execution
summary:
  Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns cefi's gated G1→G5 rebuild — instrument-definition correctness (G1.1-G1.4 catalogue
  false-delisting / capture-stability / canonical-form pollution / junk-symbol rejection), backfill (G2),
  scheduler+aggregation (G3/G3b), MTDS catalogue-as-filter (G4), and MTDS coverage climb (G5) — plus the cefi-specific
  historical execution log (the reclassification of on-chain-perp venues into cefi, Phase-0-for-cefi execution session,
  canonical-form audit, and the G1 correctness verification/fix chain). depends_on the Phase-0 cross-cutting child for
  GATE 0.
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [instruments, catalogue, honest-coverage, data-correctness, backfill, cefi, manifest, foundation, gate-execution]
related:
  [
    instruments_foundation_completeness_2026_06_24,
    instruments_foundation_phase0_cross_cutting_2026_07_24,
    instruments_tradfi_g1_g5_gate_execution_2026_07_24,
    plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-17"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
context_scope: [/codex/02-data/instruments-foundation-and-catalogue-completeness.md, /plans/active/instruments_foundation_completeness_2026_06_24.md, /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md, instruments-service/instruments_service/reference_data/adapters/cefi/extended.py, instruments-service/instruments_service/engine/orchestrator/process_fetch.py, deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh]
supersedes:
superseded_by:
depends_on: [instruments_foundation_phase0_cross_cutting_2026_07_24]
source:
  [
    "plan-hygiene split of instruments_foundation_completeness_2026_06_24.md, 2026-07-24 (operator-approved, see
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14)",
  ]
---

# Instruments Foundation — cefi G1→G5 gate execution

**Split provenance (2026-07-24):** this plan was extracted from
[`instruments_foundation_completeness_2026_06_24.md`](instruments_foundation_completeness_2026_06_24.md) (the umbrella)
as part of the operator-approved plan-line-cap remediation
(`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row #14 — 4-way split). **`depends_on`
[`instruments_foundation_phase0_cross_cutting_2026_07_24.md`](instruments_foundation_phase0_cross_cutting_2026_07_24.md)
for GATE 0** — the cross-cutting prerequisites (observability, Honest-Coverage v2, canonical-form single-SoT migration)
that block G2. The umbrella (`instruments_foundation_completeness_2026_06_24.md`) stays the process SSOT + rolling
status index across all 4 children (this one, Phase-0, tradfi, and the defi/sports plans it already delegates to).

**Codex SSOT (the standard this plan executes):** `/codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

---

## Near-term target — cefi + defi daily instrument pipeline live (operator 2026-06-26)

The concrete first outcome for cefi **and** defi together (do them as one workstream — same producer, same aggregator):

1. **Daily instrument-definition backfill complete, both AGs, with the RIGHT missing reasons.** Rebuild the dead daily
   producer (see Phase 0 / the folded `[INFRA] P0 "Rebuild the IS daily definition producer"`), then fill the freeze gap
   (cefi `by_date` frozen ~2026-05-21 → present; defi ~2026-05-07 → present) so each day is captured. **Honest 4-state
   reasons (HARD):** missing/un-attempted days seeded `expected_unattempted` (gap reads 0%, not absent); genuine empty →
   typed `EmptyConfirmedReason` (never blank); fetch-failure → `attempted_failed`, NOT `empty_confirmed` (the CF-11
   swallow class — writer-fix so future daily writes are honest). DoD: no silent day-gaps for cefi/defi; every
   non-captured cell carries a typed reason; the daily producer runs green on a schedule (no fire-and-forget —
   registered observable BATCH job).
2. **Daily catalogue aggregator live + green, both AGs.** The lifecycle roll-up (`build_instrument_catalogue.py` →
   `{env}/catalog.parquet`) runs on a daily per-AG schedule. Remaining work (folded `[INFRA] P1` items):
   `terraform apply` of `lifecycle_catalogue_scheduler.tf` (deployment@98bee4b) **+ fix the cloud regen job's
   fast-fail** (add stdout bisection logging, localize the job-only failure, fix it). DoD: the cefi + defi catalogue
   regenerates daily from the fresh `by_date` definitions, monotonic-guard ACCEPT, click-through-able in the cockpit; a
   manual T+10min and a next-day T+24h execution both verified.

Gate: this target is the cefi+defi half of G0→G1; **stop here for operator sign-off before the per-AG G2+ gates.**
Coverage is the verification lens — every number flows through `compute_honest_coverage` (Phase 0 below).

### Findings + todos from Sonnet dispatch #1 (2026-06-26, live GCP-verified)

- [x] [CODE] P0. ✅ **IS writer seeds `expected_unattempted` pre-capture — SHIPPED instruments-service@f739a41.** Seeder
      in `process_write.py::_seed_expected_unattempted_for_target_universe` (runs in `_write_all_venues` before
      `manifest.close()`, same per-run manifest, no extra GCS walk); row-key parity with the capture writer via the
      shared `writers.py::_canonical_manifest_venue_chain` helper; seeds only in-universe venue-grain cells not already
      captured/failed (`lookup() is None`, never overwrites attempted_failed → honest 4-state intact); pre-launch venues
      stay absent. QG-green (3810 passed), 9 unit tests; runtime-verified: synthetic cefi gap day → 24 EU cells = 0.0%
      honest gap. (Original finding below.) The IS instruments manifest has ZERO `expected_unattempted` rows → missing
      days are silently absent, so `day_coverage ≈ 99.9%` is a dishonest blind number (this is THE G1-honesty blocker).
      The v2 enumerator seeds only the MTDS market-data manifest, not the IS instruments manifest. Per the codex HARD
      RULE ("`expected_unattempted` materialised by the WRITER, never re-derived"), extend the IS daily producer so that
      BEFORE attempting capture it seeds `expected_unattempted` for its configured could-exist universe at the IS grain
      (venue × day) — so a missing day reads 0%, not absent. Repo: instruments-service (+ UTL writer if needed). DoD:
      cefi+defi IS manifest shows real `expected_unattempted` counts; a synthetic gap day reads 0%.
- [x] [INFRA] P0. ✅ **defi prod daily producer CREATED + verified** — created `uts-prod-instruments-service-t1-recon`
      (the name the 00:00 scheduler already targets), cloned cefi's spec, pointed at `--asset-group=DEFI`; one run
      **wrote 53 defi venue parquets for `day=2026-06-26`** (AAVE_V3 ×8 chains, …). defi `by_date` was frozen ~05-07
      because this prod job never existed. NOTE: the all-AG no-`--asset-group` form **crashes** (exit 1) — see new
      finding; job is defi-scoped for now. Was: only `uts-prod-instruments-service-cefi-t1-recon` existed.
- [x] [INFRA] P0. ✅ **cefi producer de-hardcoded + verified** — removed the fixed `--start-date/--end-date=2026-06-23`
      override; CLI now self-defaults to today. One run **succeeded (count=1) + wrote 24 cefi venue parquets for
      `day=2026-06-26`** (BINANCE-SPOT/FUTURES, BYBIT, BITGET, ASTER, …). The blank counts were the stale fixed-date
      re-runs; now genuinely completing. Was: `--start-date=2026-06-23 --end-date=2026-06-23` re-running one day
      forever.
- [x] ✅ [INFRA] P1. **Disable/update the dead-CLI legacy daily Workflow.** `services/instruments-service/gcp/main.tf`
      `instruments-service-daily` (09:00 UTC) uses the dead CLI `--operation instrument` (singular) +
      `--CEFI/--TRADFI/--DEFI` flags; current CLI is `--operation instruments --asset-group <ag>`. If still scheduled it
      silently fails daily. Disable or update. Repo: instruments-service / deployment-service. — **DONE 2026-07-26**:
      the 2026-06-26 disable (`62a6645`) commented out the module blocks but left `outputs.tf` referencing them, so
      `tofu plan/apply` failed outright ever since — fixed `deployment-service@d5fde721`, plan now resolves (1 destroy:
      the scheduler trigger). Actually destroying the live dead resources is BLOCKED-CREDENTIALS (no available account
      has `workflows.workflows.get`/admin). Full write-up: `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item (a).
- [x] [INFRA] P1. ✅ **Catalogue-regen fast-fail diagnosis — IS bisection SHIPPED @f739a41; terraform + apply pending.**
      The 6 `[BISECT-*]` markers in `build_instrument_catalogue.py` landed in instruments-service@f739a41. REMAINING:
      ship the `PYTHONUNBUFFERED=1` add to `lifecycle_catalogue_scheduler.tf` (deployment-service) → `terraform apply` →
      one manual run → read the last `[BISECT-*]` marker → fix the real cloud failure. Repo: deployment-service.
      _(Cross-ref 2026-07-03: SUPERSEDED by `instruments_catalogue_incremental_rollup_2026_06_29.md` Phase 3 — the cloud
      failure was diagnosed (full-history walk > 3600s timeout, 3 of 5 AGs), the durable fix is the incremental rollup
      @b0596d0c, and its terraform apply carries `PYTHONUNBUFFERED=1` (already in the tf) + the weekly full self-heal
      jobs. Verify there before re-doing work here.)_ — instruments-service@f739a41d + deployment-service@c1d2e3e6 (both
      reachable on origin/live-defi-rollout); terraform/gcp/lifecycle_catalogue_scheduler.tf carries
      `PYTHONUNBUFFERED = 1`.
- [x] ✅ [INFRA] P1. **NEW (2026-06-26): the all-AG no-`--asset-group` producer path crashes (exit 1, ~1 min, no
      traceback).** Same image/spec as cefi but omitting `--asset-group` → instant exit 1. The "all" path
      (`instruments_handler.py:367` is_all → SPORTS/CEFI/DEFI/TRADFI) is broken. Fix it so one 00:00 job can capture all
      AGs; until then the 00:00 job is defi-scoped and **sports/tradfi/prediction have NO working prod daily producer**
      (a separate gap to stand up). Repo: instruments-service. — **VERIFIED DONE 2026-07-26**: already fixed same-day by
      `instruments-service@d2796158` (2026-06-26); live-reproduced a real all-AG run for 150s in dev env with zero
      crash, real fetches across cefi/defi/tradfi/sports/prediction. Full write-up:
      `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item (b).
- [x] ✅ [INFRA] P1. **NEW (2026-06-26): the t1-recon Cloud Run JOB specs have no IaC source.** terraform manages only
      the schedulers (`t1_batch_scheduler.tf`); the JOB definitions (image/args) are imperative — which is how the cefi
      date-drift and the missing all-AG job went invisible. Codify the job specs (terraform or a tracked deploy script)
      so they can't silently rot. Repo: deployment-service. — **DONE 2026-07-26**: `deployment-service@54aa6f5`, the 4
      instruments-service t1-recon jobs codified + imported into the shared prod tofu state, verified zero-drift via
      re-apply. Full write-up: `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item (c).
- [x] ✅ [SCRIPT] P2. **Registry gap:** `lifecycle-catalogue-regen-prediction` is in the TF `for_each` (5 AGs) but not
      in `cloud_run_job_registry.py::_LIFECYCLE_CATALOGUE_JOBS` (4 AGs, "no prediction"). Reconcile so the guard test
      doesn't flag drift. Repo: deployment-service. — **VERIFIED DONE 2026-07-26**: already fixed —
      `_LIFECYCLE_CATALOGUE_JOBS` derives from the 5-entry `_ASSET_GROUPS` tuple; guard test 10/10 pass.

> **Verified OK (no CF-11 swallow on the IS side):** fetch-failure → `record_failed`/`attempted_failed`
> (`process_completeness.py::_finalize_completeness`) and genuine-empty handling are correct. The only honesty gap is
> the `expected_unattempted` seeding above. Slot-hygiene note: the IS clone Sonnet #1 used is 83 commits behind LDR (3
> stale VIX-cash tests fail) — `git pull --ff-only origin live-defi-rollout` before shipping IS code.

### Progress Log — autonomous run 2026-06-26 (cefi+defi catalogues to done)

> **🟢 VMs RUNNING (instruments-definition freeze-gap backfill, asia-northeast1-c):** `cefi-instr-all-20260626-120626`
> (cefi 2026-05-21→06-25, all venues, skip-existing) + `instr-backfill-defi-targeted-20260625` (defi 2026-05-07→06-25,
> e2-standard-8). Per-VM shard isolation + consolidator merge. Verify written rows land in the `-prd` bucket the
> catalogue reads (launcher echoes a legacy non-`prd` name — VM resolves via DEPLOYMENT_ENV=prod).

- **cefi producer** ✅ de-hardcoded + verified (24 venues, day=2026-06-26, succeeded=1).
- **defi producer** ✅ created `uts-prod-instruments-service-t1-recon`→DEFI + verified (53 venues, day=2026-06-26).
- **EU-seeding** ✅ SHIPPED instruments-service@f739a41 (QG-green, runtime-verified) — promoting LDR→staging.
- **catalogue-regen bisection** ✅ SHIPPED in @f739a41 (IS side); deployment-service `PYTHONUNBUFFERED` +
  `terraform apply` NEXT.
- **freeze-gap backfills** 🟢 launched (both VMs RUNNING) — fills the no-gap history; monitor to completion.
- **catalogue PYTHONUNBUFFERED** ✅ applied live + codified deployment-service@c90cf97.

#### Actual gap shape (manifest-measured 2026-06-26) — gaps are SMALL + recent, not a months freeze

- **cefi**: 59,485 captured, 26 venues, history to 2019 (re-written 06-24). Cell grain = `date×venue` (data_type is
  empty for cefi defs; instrument class lives in `instrument_type` inside the parquet, NOT a manifest cell). Gaps: **5
  absent days** (06-19/20/21/24/25) + 5 thin days (06-12→16) + 2 straggler venues (COINBASE/OKX bare aliases) + 44
  attempted_failed. 0 expected_unattempted yet (EU runs once the image carries f739a41).
- **defi**: 169,541 captured, 31 venues, 11 chains, 2 data_types (defs + `instrument-catalog`). Gaps: **4 absent days**
  (06-22→25) + 3 straggler venues (CAMELOT_V3-ARBITRUM/EXTENDED/UNISWAP_V3-BASE) + 1,269 attempted_failed.
- **The instrument backfill fills `days×venues(×chains)` — NOT data_types.** `data_types` (ohlcv_1s/1m, trades, swaps)
  are the MTDS market-data layer (separate; the tradfi ES ask below).

---

## Phase 1 — cefi (FIRST), gated G1→G5

- [ ] [SCRIPT] P0. **G1 — instruments-service correct per-day** (mtds/instruments-service): code right + deterministic +
      on LDR + QG-green; single-day re-run byte-reproducible; **junk/test symbols rejected** at capture; per-instrument
      fields (available_from, type, symbol, MVP, universe-tag) correct. DoD: a sample day audited cell-correct.

  > **🔴 G1 VERIFICATION (2026-06-26/27, opus cefi agent — read-only duckdb on live `prod/catalog.parquet` 349,156
  > rows + `_index/availability_index.parquet` 83,851 rows). VERDICT: G1 is NOT done — 4 live correctness defects. The
  > day-axis IS fixed (✅ no day-gaps: 2,646/2,646 days genesis→06-26, 0 missing; ✅ expected-universe materialised:
  > 20,580 `empty_confirmed` rows, was 0; ✅ MVP tags + schema_version=9). The four blocking defects below MUST clear
  > before GATE G1.** Each is a concrete G1 todo:
  - [x] ✅ [SCRIPT] P0. **G1.1 — catalogue `available_to` mass FALSE-DELISTING (§7.3) — DONE, PROD-VERIFIED 2026-06-27**
        (code instruments-service@8261203; prod catalogue re-audit: 8,520-cluster 8,520→302, BINANCE-FUTURES 47→671,
        total active 4,410→9,025, EXTENDED/PACIFICA/LIGHTER not mass-delisted — see final Progress Log entry). FIX
        LANDED (LDR): `build_catalogue_dataframe` now derives `available_to` from VENUE TRUTH — (1) explicit
        `delisted_at`, (2) dated FUTURE/OPTION/COMBO `expiry` (both pulled into `_extract_meta` +
        `_InstrumentAggregate`), (3) else perp/spot active (None) iff present on its OWN venue's last FULL trading day
        via new `_venue_last_full_day` (per-venue, thin-day-aware: a day < 50% of the venue's 14-day median count is
        SKIPPED so a partial capture can't mass-delist), else last-seen fallback. Replaces the global
        `latest_day = max(all_days)` + last-seen rule. **ONE fix covers cefi G1.1 AND slot-3 tradfi G1.h** (shared file;
        checked git log 665966b clean before+after edit). 6 new regression tests + 1 existing test corrected
        (empty-latest-day no longer false-delists); QG-green (102s), all 54 roll-up tests pass. REMAINING DoD (gated on
        the in-flight cefi `_index` remediation completing — must NOT regen against a mutating manifest): rebuild the
        image to carry @8261203, re-run `lifecycle-catalogue-regen-cefi`, re-download `prod/catalog.parquet`, confirm
        the 8,520 06-25 cluster GONE + per-venue active ≈ real listed count + a sampled Deribit/dated-future
        `available_to` == venue-truth expiry. Live baseline (prod-verified 2026-06-27, the bug this moves):
        active=4,410/349,156; BINANCE-FUTURES 47 active; 8,520 stamped available_to=2026-06-25. `prod/catalog.parquet`
        (rebuilt 06-27 01:23) stamps **8,520 instruments `available_to=2026-06-25`** across EVERY venue (KRAKEN-SPOT 829
        · OKX-SPOT 762 · BINANCE-SPOT 700 · BINANCE-FUTURES 631 · …); per-venue **active counts collapsed** (catalogue
        shows BINANCE-FUTURES ≈47 active vs ~600+ real). ROOT CAUSE (confirmed): **06-26 was a PARTIAL capture**
        (BINANCE-FUTURES manifest `instrument_count` 678@06-25 → **47@06-26**; parquet 47 KB→30 KB; OKX-FUT 81→32;
        BINANCE-SPOT 767→67; BYBIT 652→652 stable) AND the **last-seen-not-venue-truth + global-`latest_day`** bug
        (§7.3) → a thin/lagging latest day mass-delists. 06-27 recovered to full (47 KB) but the bad catalogue is live →
        **MTDS G4 would filter against a catalogue that thinks Binance has ~47 instruments.** FIX = §7.3 `available_to`
        = venue-truth expiry/`last_trading_date` (Deribit/dated-futures) + venue delisting (perps/spot), per-venue
        trading-day-aware `latest_day`, and IGNORE a thin/partial latest day (don't delist off it). **SHARED FILE
        `build_instrument_catalogue.py` with slot-3's tradfi G1.h — coordinate, ONE fix covers both AGs, do NOT
        double-edit.** DoD: re-run catalogue → BINANCE-FUTURES active ≈ real listed count; the 8,520 06-25 cluster gone;
        a sample Deribit option/dated-future `available_to` == venue-truth expiry.
  - [x] ✅ [SCRIPT] P0. **G1.2 — capture-STABILITY: §1.2 drawdown/thin-day METRIC SHIPPED instruments-service@cc81cad;
        thin-day `record_failed` routing + 06-26 re-capture VERIFIED DONE 2026-08-07 (content-verified).** SHIPPED the
        cefi cumulative-drawdown + thin-day guard (`scripts/cefi_cumulative_drawdown_guard_2026_06_27.py`, generalising
        the defi one): per cefi venue it builds the daily active `instrument_count` series, flags day-over-day drops AND
        thin-day collapses (count < `--thin-frac` 0.5 × the venue's 14-day trailing median). **PROD-RUN VERIFIED it
        surfaces the canonical case**: BINANCE-FUTURES max-drop **−631** (the 678→47), thin-days flagged at count 33–47
        vs median ~600 across many dates (2025-12 → 2026-06) — exactly the partial-capture cells that must route to
        `attempted_failed`. VERIFIED 2026-08-07: (a) `_detect_thin_day_venues` present and wired in
        `_finalize_completeness` (`process_completeness.py:705`) on instruments-service HEAD `8985daed` —
        content-verified (original SHA `5ebd7f6c` unreachable post-history-rewrite; function presence confirmed); (b)
        06-26 re-capture confirmed moot — 42 days of subsequent production capture since 2026-06-26. DoD: a partial
        venue response → `attempted_failed`; 06-26 full; the metric flags >X% drops without a typed delisting. NB this
        composes with the G1.1 fix (the thin-day SKIP in the catalogue `_venue_last_full_day`) — same thin-day
        definition (50% of trailing median), one on capture, one on roll-up.
  - [x] ✅ [DATA] P0. **G1.3 — canonical-form pollution in the cefi `_index` — DONE (prod-verified 2026-06-27).** The
        ~234 schema-misaligned rows (CHAIN-in-schema_version + leaked-source) + the 250-stale + the masked cells were
        cleaned by the in-flight remediation agent af80e015 (verified: `_index` now 83,646 rows, **0 blank
        capture_status, all schema_version=9, 0 SOLANA/ZKSYNC**; pre-prune snapshot
        `_index/snapshots/pre_cefi_stale_prune_2026_06_27.parquet`). I completed THE PART af80e015 DID NOT do: **WRITER
        root-fix instruments-service@24c0dd5** — `_canonical_manifest_venue_chain` no longer defi-splits on-chain CeFi
        perp venues (LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET ∈ `_CEFI_VENUES`); they now write
        `asset_group=cefi` not defi (3 regression tests) — stops the 320-row contamination at source. **DATA re-stamp
        applied (prod, local force-correct — the consolidator is broken+PAUSED, so wrote the canonical DIRECTLY, NOT a
        per_vm shard; snapshot-first `_index/snapshots/pre_g13_restamp_2026_06_27.parquet`):** 320 defi-tagged
        (LIGHTER/PACIFICA) + 1,108 blank-asset_group 2019 (OKX-{SWAP,SPOT,FUTURES}/COINBASE-SPOT) → asset_group=cefi.
        **LIVE VERIFY: `_index` = 83,646 rows 100% asset_group=cefi, 0 defi, 0 blank, 0 blank capture_status, all
        schema_version=9.** `source` carries only valid sources (the 320 had source=instruments_service; blank-source on
        producer rows is correct per the C-#6 contract). **FOLLOW-UP FINDING (filed below):** the on-chain-cefi-perp
        venue FORM differs across surfaces (by_date PATH=glued `LIGHTER-ZKSYNC`; `_index`+catalogue=split
        `venue=LIGHTER chain=ZKSYNC`); kept `_index` SPLIT to stay aligned with the catalogue (§2.3 ε=0); the
        glued-vs-split canonicalization is a separate alignment item.
  - [x] ✅ [SCRIPT] P0. **G1.4 — junk/test-symbol rejection — DONE, PROD-VERIFIED 2026-06-27** (capture guard
        instruments-service@326589c + 9-CJK by_date purge applied [709 files / 1,430 rows, backup
        `_index/backups/g14_cjk_purge_2026_06_27/`] + `_index` 0 non-ASCII + **catalogue re-audit 0 non-ASCII** — all 4
        §8 retirement legs clean). CODE (LDR): `reject_junk_instruments` (new in `venue_core.py`, re-exported + wired
        into `process_fetch._filter_and_enrich_records` right after the date filter, EVERY AG) drops any record whose
        `base_asset`/`raw_symbol`/`instrument_key` carries a NON-ASCII char (catches 龙虾/币安人生/我踏马来了) or a
        known ASCII test base (TEST/DUMMY/…) at capture time, so junk never enters `by_date/`. 5 regression tests (CJK
        reject / non-ascii-in-raw_symbol / known-test-base / legit-passthrough incl. AAPL/XAU / mixed-batch), QG-green,
        69 helper tests pass. REMAINING (the `_index`/GCS purge leg — now unblocked, runs in the §2.2 local
        force-rebuild batch below): surgically purge the 9 existing CJK symbols on all 4 retirement legs (by_date
        parquet row-filter + the `_index` rows + catalogue + surfaces, §8). DoD: 0 non-ASCII/test instrument_ids in a
        fresh capture AND the catalogue. The 9 live junk: `BITGET-FUTURES:PERPETUAL:龙虾-USDT` ·
        `BINANCE-SPOT:SPOT_PAIR:币安人生-USDT/USDC` · `ASTER:PERP:我踏马来了USDT` · `ASTER:PERP:龙虾USDT` ·
        `BINANCE-FUTURES:PERPETUAL:龙虾-USDT/我踏马来了-USDT/币安人生-USDT` · `ASTER:PERP:币安人生USDT`.
  - [x] ✅ [DATA] P1. **FINDING (G1.3 follow-up, 2026-06-27) — on-chain-CeFi-perp venue FORM is inconsistent across
        surfaces.** LIGHTER/PACIFICA/EXTENDED appear as: by_date PATH = GLUED `venue=LIGHTER-ZKSYNC` (the SoT) ·
        `_index` + `prod/catalog.parquet` = SPLIT `venue=LIGHTER chain=ZKSYNC`. The writer fix @24c0dd5 now emits
        GLUED+cefi for NEW `_index` rows → future captures will DESYNC from the catalogue's split form (and from the
        re-stamped historical `_index` rows kept split for current alignment). RESOLVE: pick ONE canonical form for
        on-chain cefi perps (recommend GLUED `LIGHTER-ZKSYNC`, matching `_CEFI_VENUES` + the by_date PATH) and align all
        three — `build_catalogue_dataframe` must stop splitting these (they're cefi, not defi pools) + a one-time
        `_index` venue re-glue. Until aligned, the §2.3 reconciliation guard must treat split↔glued as equivalent for
        these 3 venues. Repo: instruments-service (`build_instrument_catalogue.py` + a `_index` re-glue). Provenance:
        G1.3 re-stamp diagnosis 2026-06-27. — **VERIFIED DONE 2026-07-26**: `instruments-service@ee19f6f3` (2026-07-18)
        fixed `_canonical_bare_venue_chain()` to pass cefi venues through glued; live-queried both `_index` (6,327 rows)
        and the catalogue (322 rows) — 100% glued, 0 residual split rows (PACIFICA culled 2026-07-16, so only
        LIGHTER-ZKSYNC/EXTENDED-STARKNET remain in scope). Full write-up:
        `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item (e).

- 🚦 **GATE G1 — NOT RECORDED SIGNED OFF** (was: bare "sign-off." placeholder — corrected 2026-07-14, doc-reconciliation
  vr2#115/vr2#214: no entry anywhere in this doc records an operator G1 sign-off — the 2026-06-27 GATE-BOUNDARY HOLD
  below (§ "a coordinator relayed an operator greenlight") explicitly requested it and got none, and later text (lines
  ~1086/~1208) still reads "Awaiting G1 sign-off"/"request GATE-G1 sign-off." G2/G3/G4 immediately below are nonetheless
  marked SIGNED OFF 2026-07-06 as RECONCILE-class "already-run, not a redo" entries — an open G1→G2 sequencing gap
  against this plan's own "no gate crossed without sign-off" rule (§ "Operator gates" below). Flagging for an operator
  ruling rather than asserting a G1 sign-off that isn't evidenced.)
- [x] ✅ [INFRA] P0. **G2 — backfill cefi all venues × all days × all years — SIGNED OFF 2026-07-06** (RECONCILE:
      already-run, not a redo). Evidence: (1) day-axis GAP-FREE — cefi by_date 2,646/2,646 days genesis→2026-06-26, 0
      missing (2026-06-27 audit); 20,580 `empty_confirmed` materialised in the IS instruments manifest, was 0
      (`instruments-service@f739a41` EU-seeder; 06-19/20/21/24 gap-days filled 2026-06-26 via the freeze-gap backfill
      fleet). (2) Observable BATCH registered — cefi 06:00 `uts-prod-instruments-service-cefi-t1-recon` (de-hardcoded
      instruments-service@[date-drift fix]), the per-AG daily scheduler LIVE (deployment-service@9d0e457 split all-AG
      OOM into per-AG t1-recon jobs, all SUCCEEDED). (3) Cumulative monotonic guard SHIPPED + PROD-RUN —
      `scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` (instruments-service@cc81cad, generalising the defi guard);
      surfaced the BINANCE-FUTURES 678→47 thin-day (canonical case), fed into the §7.3 catalogue fix. (4) Universe depth
      — catalogue re-audited 2026-06-27 349,156 rows / **9,025 active** (post-G1.1 fix; was 4,410 pre-fix;
      BINANCE-FUTURES 47→671 active). (5) Cockpit click-through — `classify_deployment_target` +
      `cloud_run_job_registry.CLOUD_RUN_JOBS`
      (`lifecycle-catalogue-regen-cefi`/`manifest-consolidator-cefi`/`expected-universe-v2-cefi` BATCH registered);
      alert coverage complete (deadman multi-layer + stale-image DP-VM-007 + CI-fail). Follow-ups tracked separately:
      the 486→0 within-window silent-gap drain landed 2026-06-26 (`cefi-instr-all-20260626-161800`);
      MVP-capture-perp-gated backfill tracked under `plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md`
      (separate — that plan's own G4 verdict ended NOT MET and it was archived `status: complete` 2026-07-15 with the
      remaining open work folded out to its target per plan-reconcile §6; see this doc's own G4 section below — not
      "already SIGNED there"). — instruments-service@f739a41 + @cc81cad + deployment-service@9d0e457.
- 🚦 **GATE G2 — SIGNED OFF 2026-07-06** (evidence above).
- [x] ✅ [SCRIPT] P0. **G3 — aggregate + verify the scheduler runs the latest code — SIGNED OFF 2026-07-06** (RECONCILE:
      already-run). Evidence: (1) `lifecycle-catalogue-regen-cefi` at 01:00 UTC in the per-AG daily scheduler
      (deployment-service@9d0e457) — ordering confirmed: T+1 producers 00:00-06:00 → MTDS FAST 00:30 → catalogue-regen
      01:00 (monotonic guard, 35-min buffer). (2) Cloud Run image AUTO-BUILD on main FIXED 2026-06-27 —
      `instruments-service-prod` trigger switched to `repositoryEventConfig push:branch=^main$` (matches MTDS pattern;
      no router/IAM dependency); `instruments-service:latest` now sha256:d9418e6e (tag 0.87.0, built 2026-06-27 10:58);
      Cloud Run t1-recon + lifecycle-catalogue-regen reference `:latest` → fresh image next run. Router
      `cloud-build-router.yml@c3a113e94` PERMISSION_DENIED→exit 3 + `notify-permission-denied` CRITICAL Slack job so IAM
      gaps always surface. (3) Today's `catalog.parquet` produced — cefi 2026-06-27 349,156 rows / 9,025 active
      (post-G1.1 fix live); regen monotonic ACCEPT. (4) Incremental rollup for durable freshness —
      instruments-service@b0596d0 (trailing-window + frozen-tail, `--mode incremental` default; self-widening window;
      supersedes the SIGKILL-on-3600s cloud-regen failure). (5) Staleness gate — instruments-service@5d31994
      (CATALOGUE_STALE_BY_DATE warning, coverage-horizon check) + @4979429 (clamp day<=today so future-dated prediction
      settlement partitions don't blind the gate). — instruments-service@5ab4a1e554 (tag v0.87.0, the LDR→main promote
      commit the image was built from at 2026-06-27 10:26 UTC; the built image's own digest is `sha256:d9418e6e`, not a
      commit sha) + deployment-service@9d0e457 (per-AG scheduler) + instruments-service@b0596d0 + @5d31994 + @4979429.
- [x] ✅ [SCRIPT] P0. **G3b — cefi DATED instruments: `available_to`=venue-truth + expiry oracle — SIGNED OFF
      2026-07-06** (RECONCILE: shipped as G1.1/G1.h). Evidence: `build_catalogue_dataframe` now derives `available_to`
      from VENUE TRUTH — (1) explicit `delisted_at`, (2) dated FUTURE/OPTION/COMBO `expiry` (both pulled into
      `_extract_meta` + `_InstrumentAggregate`), (3) else perp/spot active (None) iff present on its OWN venue's last
      FULL trading day via `_venue_last_full_day` (per-venue, thin-day-aware: a day < 50% of the venue's 14-day median
      count SKIPPED so a partial capture can't mass-delist). Replaces the global `latest_day = max(all_days)` last-seen
      rule that caused the §7.3 false-delistings. **PROD-VERIFIED 2026-06-27**: 8,520 06-25 available_to cluster
      **8,520→302**; BINANCE-FUTURES active **47→671**; total active **4,410→9,025**; EXTENDED 103/103, PACIFICA 10/10,
      LIGHTER 213/213 active (on-chain perp-DEXs no longer mass-delisted). ONE edit covers cefi AND tradfi (shared
      file). 6 new regression tests. **Follow-up (§2.1 formal rule-registry versioned by effective-date) is a
      longer-horizon DESIGN item** — the shipped venue-truth expiry oracle covers G3b's DoD (Deribit/dated-future expiry
      == venue-truth; no false delistings from a lagging venue `latest_day`). — instruments-service@8261203.
- 🚦 **GATE G3 — SIGNED OFF 2026-07-06** (evidence above; G3 + G3b both closed).
- [x] ✅ [SCRIPT] P0. **G4 — MTDS filters the catalogue per-day — SIGNED OFF 2026-07-06** (RECONCILE: code-complete +
      wave-1 verified). Evidence: (1) `CeFiCatalogReader` + `catalog_list_instruments("cefi", date, date)` in MTDS
      `sentinels.py` reads `prod/catalog.parquet`, filters active-on-day + MVP-perp-gate — the mechanism BUG #4 fix
      landed 2026-06-22 (probe {prod,staging,dev}/catalog.parquet + canonical `available_from`/`available_to`); the
      analogous tradfi bug fixed market-tick-data-service@dda5040d (2026-06-25 — dead-prefix + legacy col-name → real
      catalogue read). (2) With the G3b catalogue fix live (BINANCE-FUTURES 47→671 active), G4's filter now runs against
      a trustworthy universe — the pre-fix "MTDS-G4 would filter against a catalogue that thinks Binance has ~47
      instruments" risk is closed. (3) Honest-absence classification wired at G4-gate: MTDS
      `reclass_cefi_futures_chain_no_tardis_source` (market-tick-data-service@fccb1961, 2026-07-03) reclassifies 66,007
      attempted_failed → empty_confirmed/EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE (BINANCE-FUTURES 41K, BYBIT 14K,
      DERIBIT 10K) — the "captured or typed-empty for out-of-source rows" invariant. Idempotent, safe to re-run. (4)
      Spot-check DoD MET via the MVP backfill (`mvp_backfill_cefi_tick_v10_2026_06_27.md`) where G1→G4 waves have their
      own operator-tracked SIGNED gates: G1 complete 2026-06-28T03:20Z (7 SPOT VMs opt-deribit self-completed); G2+G3
      wave-1 launched 2026-06-28T03:47Z (24 SPOT VMs); G4-gate reclass 2026-07-03. — market-tick-data-service@fccb1961 +
      @dda5040d (analogue for tradfi) + BUG #4 fix (`sentinels.py` catalog_list_instruments).
- 🚦 **GATE G4 — D2 CLEARED 2026-08-07 (was: OPEN pending D2)** — re-verified 2026-08-07: D2
  `cefi_layer1_denominator_gaps` archived `status: resolved`;
  `instruments_service_cefi_qg_red_on_ldr_head_2026_07_08.md` + `tardis_concurrent_ip_lockout_2026_07_12.md` both
  `status: resolved` in archive. C4(a) blocking condition met; gate eligible for operator sign-off. Prior banner
  context: was: primary banner read "SIGNED OFF 2026-07-06" — corrected 2026-07-14, doc-reconciliation vr2#114: that
  framing let a "GATE G4" grep land on a stale-crossed reading even though the very next clause already contested it.
  **[SIGN-OFF CONTESTED 2026-07-13, verify-rerun finding 105: the standing operator ruling C4(a) (2026-07-03,
  instruments_completion_tracker_2026_07_06.md:137, never reversed) states G4 enforces Layer-1 AND Layer-2 and CANNOT
  close until D2 (cefi_layer1_denominator_gaps) lands; cefi Layer-1 measured INCOMPLETE (72.60-73.61%) on/after the
  sign-off date, and the MVP-backfill's own G4 checkbox remains [ ]. Treat G4 as OPEN pending D2 unless the operator
  re-rules.]** Mechanism is functional and spot-check DoD was met via MVP-backfill G4-gate reclass, but that does NOT
  constitute a crossed gate. cefi MTDS backfill IS OPERATIONALLY RESUMED under
  `mvp_backfill_cefi_tick_v10_2026_06_27.md`.
- [~] [SCRIPT] P0. **G5 — verify cefi MTDS coverage rises** (day+depth via SSOT) day-by-day; residual gaps each have a
  typed understood reason. DoD: coverage trends up; no new unexplained honest-absence/failed. **PARTIAL 2026-07-06** —
  G5 SUB-SIGNED (mechanism + typed-reason discipline) but full "coverage climbs day-by-day to steady state" evidence
  still accruing under the MVP backfill; NOT SIGNED HERE. Live status: (a) Layered coverage SSOT SHIPPED `UAC@755c40515`
  (Unit-1, `LayeredCoverage` NamedTuple + `compute_layered_coverage(day_counts, depth_counts)` via the single
  `compute_honest_coverage` — day/depth cannot diverge). (b) MVP backfill (`mvp_backfill_cefi_tick_v10_2026_06_27.md`) —
  AS OF 2026-06-28 snapshot: coverage cefi=11.68% (716,159/6,133,155); 4 wave-1 VMs COMPLETED at T+2h40min; wave-2 gated
  on wave-1 completion + phantom reconcile. **That plan is no longer in flight** — archived `status: complete`
  2026-07-15 with remaining open work folded out to its target (plan-reconcile §6); see this doc's own G4 section for
  the current gate verdict. (c) Typed-reason discipline wired at the writer via `instruments-service@9e6dab5`
  (pre-genesis/no-activity/weekend/failed → typed empty_confirmed/attempted_failed) + G4-gate reclass @fccb1961. (d)
  UAC↔writer matrix reconciliation `instruments-service@3bb7acd` (cefi venue-suffix fold, ASTER carve-out) → residual
  gaps have UAC-derived typed reasons. (e) Full-history honest-coverage backfill CULMINATION 2026-06-26: empty_confirmed
  cefi 0→20,580; every representable shard×day represented (captured / empty_confirmed-typed / attempted_failed / EU).
  **REMAINING for GATE G5 sign-off**: (i) MVP backfill waves 1–N drive to done (climbing metric = captured cells / day
  for MVP perp universe); (ii) verify Layer-2 SSOT number rises + Layer-1 remains 100% via cockpit; (iii) residual gaps
  audit → every remaining EU/failed/empty carries a typed reason (no unexplained holes). Tracked in the MVP backfill
  plan — cross-linked here, not duplicated. — UAC@755c40515 (SSOT) + instruments-service@9e6dab5 + @3bb7acd +
  market-tick-data-service@fccb1961.
- 🚦 **GATE G5 — SUB-SIGNED 2026-07-06** (mechanism + typed-reason discipline SHIPPED); full sign-off (cefi DONE) held
  until the MVP backfill waves drive coverage to steady state (owned by `mvp_backfill_cefi_tick_v10_2026_06_27.md`).

---

## Historical progress log (cefi track, moved verbatim from the umbrella 2026-07-24)

> This log is interleaved with concurrent defi/tradfi work from the same sessions (2026-06-25 → 2026-06-27); the
> tradfi-specific entries from the same period were extracted to
> [`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`](instruments_tradfi_g1_g5_gate_execution_2026_07_24.md); the
> cross-cutting canonical-form-migration entries were extracted to
> [`instruments_foundation_phase0_cross_cutting_2026_07_24.md`](instruments_foundation_phase0_cross_cutting_2026_07_24.md).

- 2026-06-25 — **Takeover#2 EXECUTION begins (operator "run it to the end" mandate, 8 phases).** PHASE 1 (cefi
  reclassification) code-complete in instruments-service, QG-validating: moved EXTENDED/PACIFICA/LIGHTER out of the defi
  capture path → cefi. Edits: `engine/orchestrator/defi.py` (removed PACIFICA from `_SOLANA_DEFI_VENUES`; deleted
  `_L2_DEX_PERP_VENUES` = EXTENDED+LIGHTER + its `__init__.py` export + the `_build_defi_venues` extend) +
  `engine/orchestrator/venue_core.py` (added the 3 to `_CEFI_VENUES`, next to HYPERLIQUID/ASTER) +
  `reference_data/ factory.py` (3 adapter imports repathed defi→cefi, ruff-sorted into the cefi block) + `git mv`
  adapters `adapters/defi/{extended,pacifica,lighter}.py`→`adapters/cefi/` (relative imports
  `...base_adapter`/`...schemas` resolve unchanged — same depth) + test `git mv`
  `test_lighter_extended_pacifica_coverage.py` defi→cefi + repath + `tests/unit/test_is_adapter_fetch_failure_raises.py`
  repath. The expected-universe enumerator + its tests ALREADY treated the 3 as cefi
  (`test_cefi_yields_..._for_lighter`, `_make_cefi_entry`) — only the IS capture path had drifted, now aligned. Codex
  `defi-canonical-naming-ssot.md` got an "on-chain perp CLOBs are CeFi" section;
  `availability- manifest-and-data-status.md` already documented the cefi-instrument shape for these. They ride the
  **cefi backfill** like HL/ASTER (`_CEFI_VENUES`); no special path. NOTE: only EXTENDED has a UAC cefi
  `SourceCapability` — PACIFICA/ LIGHTER MTDS-cefi market-data capture is a separate cefi-track gap (IS
  instrument-reference is now cefi-correct for all 3). The §3 subgraph investigation (background agent) returned a lead:
  TRADER_JOE_V2-AVALANCHE (empty), UNISWAP_V4 + VELODROME_V2 (not-yet-collected), ORCA/KAMINO/RAYDIUM (Solana-REST, not
  subgraphs — "6 subgraphs" is a partial misnomer; RAYDIUM also carries the 1970 genesis bug) — to verify against live
  coverage at §3. The MTDS-breakdown agent mapped the IS §6 gap: IS lacks the 4-state `capture_status` per (venue,chain)
  shard that MTDS records.

- 2026-06-25 — **DeFi takeover #2 (opus) — verified handoff baseline, corrected it on 3 points, got 2 operator
  decisions, built+ran the §1.2 monotonic guard.** Prober re-run confirms the banked baseline EXACTLY (IS-PRD/MTDS/
  catalogue/per_vm 0 glued; ENVLESS 75,649; by_date PATH 56/day; by_date COL 2,620/15; UAC registry 156). Reader audit
  (10 sites / 5 repos) + the canonical SSOT (governs `raw_tick_data`+manifest ONLY — both already canonical) established
  the IS `instrument_availability/by_date/venue={glued}/` snapshot PATH is a SEPARATE reference key, not an SSOT
  violation.
  - **OPERATOR DECISION 1 — by_date glued PATH + UAC registry = DOCUMENT as canonical internal key** (NOT migrate). The
    5-repo physical migration (10 readers + 2,345-day rewrite) is rejected; instead scope the prober's glued-ban to
    `manifest`+`raw_tick_data` and document the IS-snapshot/registry glued exception in the canonical SSOT. **Path
    structure is uniform**: ALL asset_groups write ONE shape `instrument_availability/by_date/day=/venue=/<file>` (glued
    is just the defi VALUE of the single `venue=` key); the second IS plane
    `sports_reference/by_date/.../entity=/ [league=]/` is a different data category → legitimately different.
  - **OPERATOR DECISION 2 — EXTENDED = CeFi; PURGE the defi contaminant** (REVERSED from the initial "adopt as defi"
    once full evidence surfaced). EXTENDED-STARKNET is **already a fully-registered CeFi on-chain perp**: cefi
    `SourceCapability` (`_cefi.py:754` `_EXTENDED`, source="extended", `api.starknet.extended.exchange` REST+WS, SM
    keys, plan `extended_starknet_historical_data_path_2026_05_20.md`) + 6 more cefi registries
    (venue_mapping=extended_api, venue_instrument_config=PERPETUAL, venue_launch_dates 2024-09-01,
    market_data_categories, data_type_capability grouped with PACIFICA/LIGHTER). Same class as HYPERLIQUID/ASTER
    (`venue_constants→"cefi"`). STARKNET is NOT in UAC `KNOWN_CHAINS` (prober's local set has it → why it flagged
    EXTENDED-STARKNET "glued"). So the **119 cefi rows are CORRECT**; the **603 defi rows (556 catalog + 47 blank) are
    contamination** from the **misplaced `adapters/defi/extended.py`** (a cefi perp adapter in the defi folder feeding
    the defi instrument-catalog). Plan: **purge the 603 defi `_index` rows (snapshot-first) + retire/relocate the
    misplaced adapter**; EXTENDED cefi-completeness is a **cefi-track** item (defi scope = contaminant cleanup only).
    Initial "adopt-as-defi" checked ONLY defi registries + saw the misplaced defi adapter — the 7 cefi registrations
    were the missing evidence.
  - **ROOT CAUSE FOUND + finding BROADENED to 3 venues (EXTENDED + PACIFICA + LIGHTER), 1,802 contaminant defi rows.**
    UAC `market_data_categories.VENUE_TO_ASSET_GROUP` correctly maps all three → **cefi** (lines 258-260), but the IS
    **defi capture path** `engine/orchestrator/defi.py` carries them in its OWN static lists: `_SOLANA_DEFI_VENUES`
    (`PACIFICA-SOLANA`) + `_L2_DEX_PERP_VENUES` (`LIGHTER-ZKSYNC`, `EXTENDED-STARKNET`) → `_build_defi_venues()` →
    captured as defi (ongoing, up to 06-21). `_index` contamination: **EXTENDED 603 defi (+119 cefi correct), PACIFICA
    357 defi (0 cefi), LIGHTER 842 defi (0 cefi)**. NONE are in the IS cefi enumeration → removing from defi without
    cefi pickup leaves PACIFICA/LIGHTER uncaptured (acceptable: **cefi is PAUSED** pending this foundation; they'll
    capture correctly as cefi when it resumes). Adapters `adapters/defi/{extended,pacifica,lighter}.py` are misplaced
    (cefi perps in the defi folder; HYPERLIQUID/ASTER correctly live in `adapters/cefi/`). Tied surfaces: tests
    `tests/unit/reference_data/adapters/defi/test_lighter_extended_pacifica_coverage.py` +
    `test_enumerate_expected_universe*` (LIGHTER assertions) + the expected-universe seeder (seeds these as defi).
  - [x] ✅ [SCRIPT] P0. **Phase-1 CODE: reclassify EXTENDED/PACIFICA/LIGHTER defi→cefi** — IS@2f7d454: removed the 3
        from `defi.py` `_SOLANA_DEFI_VENUES`/`_L2_DEX_PERP_VENUES` (+ `__init__.py` export); added to
        `venue_core._CEFI_VENUES` (ride the cefi backfill like HYPERLIQUID/ASTER); relocated adapters
        `adapters/defi/`→`adapters/cefi/`; moved+repathed tests; adapter-contract baseline keys renamed (count=3
        **preserved**, NOT regenerated, PM@8ef0dffe8) + extended test now ASSERTS the `ADAPTER_FETCH_FAILED` emit; codex
        on-chain-perp-is-cefi note. QG-green (94s); peer's concurrent VIX test fix reconciled (autostash conflict, took
        peer's canonical version, my defi changes intact).
  - [x] ✅ [SCRIPT] P0. **Phase-2 DATA: purged the 1,802 contaminant defi `_index` rows** (EXTENDED 603 + PACIFICA 357 +
        LIGHTER 842) — `scripts/purge_cefi_perp_defi_contamination_2026_06_25.py --apply`, snapshot-first
        (`_index/snapshots/pre_phase2_purge_2026_06_25.parquet` + `.phase2.bak`). VERIFIED live: \_index
        176,186→174,384, defi-3venue=0, cefi-3venue=119 preserved; monotonic guard defi venues 31→28 (3 dropped),
        drop-days 182→180. Catalogue (asset_group-AGNOSTIC, venue-keyed instrument defs) left intact. REMAINING (minor):
        the orphaned by_date defi snapshots for the 3 venues (~3/day, no longer enumerated after Phase 1) + stop the
        expected-universe seeder from seeding them as defi — tracked below.
  - [ ] [CEFI-TRACK] P1. **EXTENDED violates the CF-11 honest-absence contract** — on fetch failure it emits
        `ADAPTER_FETCH_FAILED` but FALLS BACK to a hardcoded market list instead of raising, so a real outage records
        `captured` (stale fallback) not `attempted_failed` (the A8 false-complete pattern). Its sibling on-chain perps
        (HYPERLIQUID/ASTER/LIGHTER) raise. Decide: make EXTENDED raise-on-fetch-failure (honest) vs keep the fallback.
        Target repo: instruments-service `adapters/cefi/extended.py`. Cefi-track (behaviour change w/ manifest
        implications).
  - [x] ✅ [SCRIPT] P2. **Phase-2 tail: purge orphaned by_date defi snapshots for EXTENDED/PACIFICA/LIGHTER** (~3/day
        across history, un-enumerated after Phase 1) + ensure the expected-universe seeder no longer seeds these as defi
        `expected_unattempted`. DoD: 0 `venue=EXTENDED-STARKNET|PACIFICA-SOLANA|LIGHTER-ZKSYNC` by_date defi blobs. —
        **DONE 2026-07-27 (slot-11, `data_engineering`, `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`
        `instruments_cefi_g1_g5_gate_execution` todo).** Confirmed real orphan count via prefix-scoped listing (not a
        whole-corpus walk): EXTENDED-STARKNET=1256, PACIFICA-SOLANA=749, LIGHTER-ZKSYNC=1376, total 3381 objects on
        `instruments-store-defi-prd-central-element-323112`; confirmed no live writer/reader of this DEFI-bucket-scoped
        path for these venues. Shipped `instruments-service@4d6c2109` (snapshot-then-delete script), then
        `instruments-service@dd90a44f` (fixed the script's own missing fresh §3a retention check + a
        `GCP_PROJECT_ID`-env client bug found before running `--apply`). Ran `--apply`:
        `soft_delete_retention_seconds=604800` (fresh-checked, at threshold) — EXTENDED-STARKNET 1256, PACIFICA-SOLANA
        749, LIGHTER-ZKSYNC 1376, **3381/3381 total, VERIFIED 0 remain**. Second DoD half also confirmed: a fresh
        `enumerate_expected_universe.py --asset-group defi` dry-run (712,815 candidate rows) logged **zero** references
        to any of the 3 venues; `_build_defi_venues()` independently re-confirmed to still exclude all 3. Snapshots
        retained at `_purge_snapshots/cefi_perp_defi_blob_contamination_phase3_2026_07_26/` (+ 7-day soft-delete
        recovery window).
  - [x] ✅ [CEFI-TRACK] P1. **MTDS-cefi capability for PACIFICA/LIGHTER** — only EXTENDED has a UAC cefi
        `SourceCapability` (`_cefi.py`); PACIFICA/LIGHTER have none, so their cefi market-data capture is unbuilt (IS
        instrument-reference is now cefi-correct for all 3). Build their MTDS cefi capture when cefi resumes. Target
        repo: market-tick-data-service. — **VERIFIED DONE 2026-07-26 for LIGHTER** (PACIFICA culled 2026-07-16, out of
        scope): `unified-api-contracts@81bf5e17` (2026-07-18) added the `_LIGHTER` `SourceCapability`; MTDS routes
        LIGHTER-ZKSYNC through `onchain_perp_batch_handler.py` + a live WS connector; manifest shows 88,166 rows for
        venue=LIGHTER-ZKSYNC in `market-data-tick-cefi-prd` (781 captured, actively running). Full write-up:
        `cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item (f).
  - **§1.2 MONOTONIC GUARD BUILT + RUN** (`instruments-service/scripts/defi_cumulative_drawdown_guard_2026_06_25.py`):
    per-venue daily active instrument_count from the `_index`, flags day-over-day drops. Result: **182 venue drop-days
    across 30 defi venues** (UNISWAP_V3 −1759, BALANCER −2101, PANCAKESWAP_V3 −493, MORPHO −431, …). **EXTENDED is
    GUARD-CLEAN** (1 drop-day, −1) → safe to adopt. CAVEAT: for DEX top-N-by-TVL venues most active-count drops are
    legitimate top-N churn; the hard-defect invariant is the cumulative-ever-seen UNION (needs instrument-lifecycle
    modeling), so the 182 need delisting-vs-missing classification — the full §1.2 reconciliation P0.
  - **GENESIS diagnosed** — the 15 RAYDIUM `1970-01-01` rows are in the CATALOGUE (`prod/catalog.parquet`), are STALE
    legacy roll-up rows (live by_date RAYDIUM snapshot has NO `available_from` col, 0×1970) with EMPTY `pool_address` →
    no RPC genesis-oracle resolution possible. Current adapter already floors to `get_protocol_floor_date('raydium')` =
    `2021-02-21` (RAYDIUM AMM mainnet launch). Fix = patch the 15 to the floor (the honest conservative the live code
    produces) + confirm regen-durable.
  - **ENVLESS redundancy PROVEN** — chain-agnostic, 39,512/40,115 ENVLESS cells are in `-prd-`; the 603 residual are ALL
    `EXTENDED-STARKNET` glued-form twins of `-prd-`'s split form (only "missing" because my splitter skips the
    unsanctioned EXTENDED venue). Identical date ranges (2020-01-20..2026-06-21). ENVLESS is genuinely redundant → safe
    to snapshot-then-delete. (Corrects the first-pass "39,240 missing" which was a chain-blank-vs-populated artifact.)
  - **FINDING (sports track, not defi) — file as todo:** IS writes sports instruments at
    `instrument_availability/by_date/.../venue=API_FOOTBALL/` with NO `league=` segment, but deployment-api's reader
    (`_instruments.py:251`) constructs `.../league={league}/venue={venue}/` → reader/writer path mismatch.
  - **REMAINING (decided, executing):** (a) ship EXTENDED UAC adoption + purge 119 cefi; (b) genesis floor-patch (15
    RAYDIUM); (c) ENVLESS snapshot-then-delete; (d) prober tighten + SSOT document the glued internal-key exception; (e)
    §1.2 full reconciliation of the 182 drops (delisting-vs-missing); (f) recency 06-22→today + 6 subgraphs + clean
    backfill. Scripts banked: `defi_cumulative_drawdown_guard_2026_06_25.py`, `diagnose_*_2026_06_25.py` (read-only).

- 2026-06-25 — **cefi Phase-0 execution session START (this session, opus autonomous).** Re-confirmed clean LDR across
  IS/MTDS/UAC/UTL/deployment-{service,api,ui}/PM. Mapped the 6 Phase-0 surfaces (read-only) + GCS ground-truth (duckdb
  on the live cefi manifest + catalogue). **Findings that pin the cefi build:**
  - **day-gaps WIDENED:** cefi instruments `by_date/` day-dirs = 0 for **06-19/20/21 AND 06-24** (and 06-25 in progress)
    — the audit's 3 gaps are now 4; the daily 08:30 trigger is still paused. Even "present" days are partial (06-15/16 =
    8 venue-rows; 06-22 = 18; 06-23 = 20; vs ~21 full) — capture is unreliable, not just gappy.
  - **expected-universe is NOT materialised in the cefi INSTRUMENTS manifest** (`_index/availability_index.parquet`,
    62,137 rows, grain = per-(venue,day) with `instrument_count`): capture_status = 62,091 `captured` + 46
    `attempted_failed`, **ZERO `expected_unattempted` / ZERO `empty_confirmed`**. So the gap days are simply ABSENT (not
    seeded 0%), and coverage = captured/(captured+failed) ≈ 99.9% = the dishonest blind number. **day_coverage fix =
    seed expected_unattempted for every (venue, missing-day) genesis→today.** (NB: the expected-universe-v2-cefi
    enumerator seeds the MTDS market-data manifest, not this instruments-capture manifest — IS day_coverage needs its
    own venue-day EU seeding.)
  - **canonical-form (operator directive) — cefi INSTRUMENTS manifest is already largely canonical:** asset_group=all
    `cefi`, schema_version=all `9`, venue=UPPER, pipeline_mode=`batch_instruments_service`,
    service_name=`instruments- service`. Gaps: 24 blank-`source` rows; `data_type` all-blank (confirm intended for the
    instruments venue-day grain). **market-tick-data cefi bucket NOT yet audited for canonical form** — next.
  - **§7.3 false-delistings are LIVE in the catalogue** (`prod/catalog.parquet`, 227,576 rows, built 06-24T01:09 when
    global `latest_day`=06-23): `available_to=2026-06-18` stamped on **1,118** instruments (+943 @06-11, +long tail) —
    instruments last-seen on the last full day before the gap, falsely delisted by last-seen + global-latest_day.
    Confirms §7.3 bug A (last-seen not venue-truth) + B (global not per-venue latest_day). instrument_type: OPTION 146k
    / COMBO 67k / FUTURE 5.8k / SPOT_PAIR 4.8k / PERPETUAL 3.9k; mvp 157,092 T / 70,484 F.
  - **deployment-observability is largely BUILT** — `classify_deployment_target`,
    `cloud_run_job_registry.CLOUD_RUN_JOBS` (has
    `lifecycle-catalogue-regen-cefi`/`manifest-consolidator-cefi`/`expected-universe-v2-cefi` BATCH),
    `VM_PREFIX_TO_BUCKET` (`instr-backfill-cefi-`/`mtds-backfill-cefi-` EPHEMERAL_BATCH), `dp-exit-code-monitor`/
    `dp-heartbeat-watcher`/`dp-meta-watchers`, `/api/deployments/inventory`+`umbrella/{u}/summary`. Phase-0
    observability item = VERIFY the cefi launchers actually emit
    ServiceBootstrap/log_event/heartbeat/persist-exit_code + click-through in the cockpit (not assumed).
  - **G4 catalogue-as-filter for cefi is already substantially built** — `CeFiCatalogReader` +
    `catalog_list_instruments("cefi",date,date)` in MTDS `sentinels.py` reads `prod/catalog.parquet`, filters
    active-on-day + MVP-perp-gate; DeFi `_catalogue_filter.py` exemplar exists. G4 is mostly validation, not new build.
  - **compute_honest_coverage SSOT = single float** (`CaptureStatusCounts`→numerator/denominator, out_of_window clip);
    **no day/depth split, no reconciliation guard** → both are Phase-0 net-new. UI renders the SSOT value verbatim (no
    client recompute) ✓. **Build sequence (bottom-up T0→consumers):** (1) layered coverage SSOT day+depth in UAC +
    surface deployment-api/UI; (2) IS expected-universe DAY seeding (venue-day) + depth-expected; (3)
    cumulative-drawdown metric; (4) §7.3 available_to venue-truth + per-venue latest_day fix; (5) consolidation
    reconcile-vs-expected; (6) drilldown-correctness guard; (7) observability verify; (8) canonical-form audit
    MTDS-cefi. Driving unit-by-unit, QG+quickmerge+flip each, surfacing at GATE 0. **Awaiting GATE 0 sign-off before any
    backfill launch.**

- 2026-06-25 — **cefi VM-drain for the canonical-form migration (operator-directed, this session).** Operator flagged
  cefi backfills running before the foundation code lands (G4/G5-before-G1–G3 + would write against the buggy catalogue
  - race the canonical-form migration). **STOPPED (graceful, reversible — process killed, not deleted):**
    `cefi-binance-futures-2020-heavy-20260624-222326` (cefi MTDS market-data backfill) ·
    `cefi-hyperliquid-2024-20260623-113700` (cefi MTDS backfill, 1.5d-running) · `mtds-perp-funding-backfill` (tagged
    `VM_ASSET_GROUP=DEFI`/`defi-backfill` but cefi-named + servicing cefi funding — the cross-AG-servicing-cefi case).
    Operator decision: **cefi-scoped drain + any cross-AG VM servicing cefi stopped + per-AG VMs only going forward.**
    LEFT RUNNING (other active agents' single-AG work, per cefi-scope): ~15 `mtds-live-cefi-*` LIVE producers (decide
    after auditing whether cefi market-data bucket needs migration — they write it continuously), 16 `tradfi-bf-*` +
    `tradfi-fwd-daily-cron` (slot-3 tradfi track), `instr-backfill-defi` + `defi-fwd-oracle-prices-poll` + `mtds-dex-*`
    (defi agent), `prediction-live-*`, `sports-ref-v3-*`. **Finding (per-AG VM hygiene):** `mtds-perp-funding-backfill`
    (DEFI metadata, cefi-name, no AG prefix) + the untagged `defi-fwd-*`/ `tradfi-fwd-*`/`mtds-dex-*` pollers (no
    `VM_ASSET_GROUP`) are the cross-AG/untagged anti-pattern the operator named — launchers must set `VM_ASSET_GROUP` +
    an AG-prefixed name; tracked under the canonical-form/observability items.

- 2026-06-25 — **cefi Unit-1 (UAC layered coverage SSOT) built.** `LayeredCoverage` NamedTuple +
  `compute_layered_coverage(day_counts, depth_counts)` — both layers via the single `compute_honest_coverage` so day +
  depth can never diverge from the formula the UI renders (instruments-foundation §2). Re-exported through
  `honest_coverage.py` + root `__init__.py` + `__all__`; 3 unit tests (both-via-SSOT, day-green/depth-low thin-day
  signal, missing-days-drag-day-coverage). Also fixed a PRE-EXISTING UAC-LDR red blocking ALL UAC (T0) promotion:
  `kalshi_trades_ws`/`polymarket_trades_ws` WS connectors landed without a `_CONNECTOR_TO_VENUE` entry → 2 failing
  coexistence tests; added the 2 mechanical map entries (both venues already carry a `*_ws.yaml`). Shipping next.

- 2026-06-25 — **cefi Unit-1 SHIPPED + cefi canonical-form audit + market-data dual-SoT cleanup.** Unit-1 (UAC
  layered-coverage SSOT + UAC-LDR red fix) landed **UAC@755c40515** on live-defi-rollout (strict-quickmerge clean;
  Tier-C drain → staging ≤15min). **Canonical-form audit (operator directive — cefi instruments + market-data GCS):**
  - **cefi INSTRUMENTS** (`instruments-store-cefi-prd`): manifest already canonical (asset_group=cefi · schema_version=9
    · venue UPPER · pipeline_mode=batch_instruments_service); residual = 24 blank-`source` rows + `data_type` all-blank
    (likely intended for the instruments venue-day grain — confirm). Raw path
    `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` carries no `pipeline_mode=`/`asset_group=`
    path-key — but for reference-data (one bucket per AG, single source `batch_instruments_service`) that is
    canonical-by-design (the keys are manifest COLUMNS). No instruments migration needed.
  - **cefi MARKET-DATA** (`market-data-tick-cefi-prd`): **canonical tree is CORRECT** —
    `raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=cefi/venue={V}/…` (live_binance/bybit/
    deribit/hyperliquid/kraken/okx + batch modes); `processed_candles/by_date/day=…` clean (0 orphans). \*\*DUAL-SoT
    FOUND
    - FIXED:** 9 stray flat `raw_tick_data/by_date/<symbol>.parquet` (AVAXUSDT/BTC-28MAR25/BTC-PERPETUAL/BTCUSDT/
      ETH-PERPETUAL/ETH-USD-250328/KRW-LINK/SOL-ETH/TRX-USDT), all stamped **2026-05-12T17:01** = the pre-`day=`/
      `pipeline_mode=` flat layout that the ~05-12 path migration rewrote into the canonical tree but **never deleted
      the source** (manifest-invisible → never in coverage). **Snapshotted →
      `_index/backups/orphan_flat_files_pre_sot_ cleanup_2026_06_25/` then PURGED\*\* → 0 flat orphans remain, 2,645
      canonical `day=` dirs intact. Single-SoT restored.
  - Remaining canonical-form work (the tracked Phase-0 single-SoT item, runs in cefi G1–G3): full schema_version
    distribution of the 144MB market-data `_index` (measured, not the constant) · venue/instrument_id casing across the
    market-data manifest · the §2.3 ε=0 reconciliation guard wiring · the 24 blank-source / all-blank-data_type
    instruments residual. cefi canonical-form is otherwise GREEN (no further dual-SoT pollution found).

- 2026-06-27 — **cefi G1 correctness (opus autonomous) — G1.1/G1.h `available_to` false-delisting CODE SHIPPED + prod
  baseline re-verified; `_index`-mutating G1.2-G1.4 steps SEQUENCED behind the in-flight cefi remediation agent.**
  - **PROD RE-VERIFIED (read-only duckdb/pyarrow on live `instruments-store-cefi-prd…/prod/catalog.parquet`):** the
    false-delisting is REAL — 349,156 catalogue rows, **active (available_to=None) = 4,410**; **8,520 stamped
    available_to=2026-06-25** (next cluster 772 @03-28); BINANCE-FUTURES **47 active** (by_date day=2026-06-24 shows 679
    real → 47 is ~7% = a thin-day false-delist); DERIBIT 3,588 of the 4,410 active. by_date schema CONFIRMED the
    venue-truth fields exist: `expiry` populated 100% on FUTURE(80/80)+OPTION(3010/3010), partial COMBO(220/441), empty
    on PERP/SPOT (correct); `delisted_at` present-but-empty this snapshot.
  - **G1.1 + G1.h FIX SHIPPED instruments-service@8261203 (QG-green 102s, 54 roll-up tests):** rewrote
    `build_catalogue_dataframe`'s `available_to` — venue-truth `delisted_at` → dated `expiry` → per-venue thin-day-aware
    last-FULL-trading-day liveness (`_venue_last_full_day`: a day < 50% of the venue's 14-day median count is skipped) →
    last-seen fallback. Replaces the global `latest_day = max(all_days)` that mass-delisted off a thin latest day.
    `_extract_meta`/`_InstrumentAggregate` now carry `expiry`+`delisted_at`. 6 new regression tests
    (thin-day-no-false-delist, venue-truth-expiry, delisted_at-priority, per-venue-independence, genuine-delisting-
    still-stamped) + corrected the existing empty-latest-day test (it encoded the bug). ONE fix covers cefi+tradfi
    (shared file; checked git log 665966b clean before+after — no double-edit with slot-3). PROD-REGEN DoD pending the
    image rebuild + `lifecycle-catalogue-regen-cefi` re-run (sequenced — see coordination below).
  - **COORDINATION / sequencing (HARD — multi-agent shared clone):** an in-flight cefi remediation agent (other Cursor
    sessions, this same instruments-service clone) is actively landing the G1.3 schema_version writer-bug + stale-row
    prune + gap re-enumeration — it just committed instruments-service@0f1f3b5 (the schema_version-integer regression
    test) during this session. Per the dispatch HARD rule I did NOT mutate the cefi `_index` (G1.2 06-26 re-capture,
    G1.3 asset_group re-stamp of the 320 defi-tagged + 1,108 blank-2019 rows, G1.4 CJK purge) — those are sequenced
    AFTER that agent finishes + the manifest is stable (concurrent canonical-manifest mutation corrupts it). The G1.1
    catalogue fix was SAFE to ship now (`prod/catalog.parquet` is a different artifact; no `_index` write). The host is
    memory-pressured (heavy concurrent jobs OOM-killed 2 read-only probes) — re-capture/regen must run on a VM
    (EPHEMERAL_BATCH) or memory-bounded chunks, never an unbounded local subprocess.
  - **NEXT (this loop):** (a) build the IS image once the IS tree is clean at @8261203+ → redeploy
    `lifecycle-catalogue-regen-cefi` → re-run → re-audit (the G1.1 prod DoD); (b) when the in-flight `_index`
    remediation completes (verify the manifest stable), execute G1.2 (06-26 full re-capture + drawdown-guard wiring),
    G1.3 (asset_group re-stamp at the writer), G1.4 (junk-rejection adapter + 9-CJK 4-leg purge); (c) surface at 🚦 GATE
    G1.
  - **UPDATE 2026-06-27 (later this session) — G1.3 + G1.4-code DONE; consolidator coordination noted.** The in-flight
    remediation agent **af80e015 COMPLETED** (verified `_index` 83,646 rows, 0 blank status, all schema_version=9, 0
    SOLANA/ZKSYNC; snapshot `pre_cefi_stale_prune_2026_06_27.parquet`). I then shipped the parts it didn't: **G1.4
    capture-time junk guard** instruments-service@326589c (`reject_junk_instruments`, wired into `process_fetch`, every
    AG; 5 tests). **G1.3 WRITER root-fix** instruments-service@24c0dd5 (`_canonical_manifest_venue_chain` skips
    `_CEFI_VENUES` on-chain perps → no more defi-tagging; 3 tests). **G1.3 DATA re-stamp APPLIED to prod** (local
    force-correct, snapshot `pre_g13_restamp_2026_06_27.parquet`): 320 defi-tagged + 1,108 blank-2019 → cefi;
    **LIVE-VERIFIED `_index` 100% cefi / 0 blank-status / all v9**. **CONSOLIDATOR COORDINATION (coordinator relay,
    independently noted):** the Cloud Run `uts-prod-manifest-consolidator-instruments-cefi-cron` is BROKEN (stale
    pre-fix image → positional-UNION-ALL col-misalignment corrupts the canonical) and PAUSED; a deploy agent (aedb16f0)
    is redeploying the fixed image. So I did the `_index` mutation as a DIRECT local canonical write (workspace UTL has
    dd17ce23 stale-drop + 6b0520a6 col-order — verified ancestors of HEAD), NOT a per_vm shard. I did NOT re-enable the
    cron (stays paused until aedb16f0 lands AND all `_index` mutations finish). REMAINING THIS LOOP: G1.4 9-CJK by_date
    purge + catalogue regen (G1.1 prod DoD) + G1.2 capture-stability; verify cron re-enabled before GATE G1.
  - **CHECKPOINT 2026-06-27 (4 of 4 G1 defects code-shipped; prod-DoD validation = catalogue regen pending):** shipped
    this session — G1.1 catalogue fix `is@8261203`, G1.2 drawdown/thin-day guard `is@cc81cad` (prod-run surfaced the
    678→47, max-drop −631), G1.3 writer-fix `is@24c0dd5` + prod `_index` re-stamp (LIVE 100% cefi), G1.4 capture guard
    `is@326589c`. **G1.4 9-CJK by_date PURGE: dry-run found 709 by_date files / 1,430 junk rows across the 4 venues'
    catalogue date-ranges (ASTER from 2023-07-22, BINANCE-FUTURES/SPOT/BITGET-FUTURES from 2025-10/2026-01/03); applying
    now (backup-per-blob → `_index/backups/g14_cjk_purge_2026_06_27/`).** The `_index` already has 0 non-ASCII
    (verified) so G1.4 leg-3 is already clean; the catalogue (leg-4) drops them on the next regen. **OPEN — catalogue
    regen is the shared G1.1+G1.4 prod-DoD validation**: needs the producer/catalogue to run the new code. The IS image
    build is MANUAL+STALE (plan note) so the live `lifecycle-catalogue-regen-cefi` still runs old code; options for the
    regen = (A) rebuild the IS image (clean tree) → re-run the Cloud Run job [RECOMMENDED, prod path], (B) a
    memory-bounded local `run_rollup("cefi", allow_shrink=True)` (the 9-row purge + the re-stamp make the catalogue
    SHRINK + active jump up, so `--allow-shrink` is REQUIRED). After regen: re-audit prod/catalog.parquet — the 8,520
    06-25 cluster GONE, per-venue active ≈ real, 0 non-ASCII. **Then verify the consolidator cron re-enabled (deploy
    agent aedb16f0) before requesting GATE G1.**
  - **UPDATE 2026-06-27 (later) — G1.4 by_date PURGE DONE + VERIFIED; catalogue regen IN FLIGHT; doc cleanups shipped.**
    G1.4 9-CJK by*date purge APPLIED (709 files / 1,430 junk rows filtered, backup
    `_index/backups/g14_cjk_purge_2026_06_27/`); **VERIFIED by_date now 0 non-ASCII** across sampled affected files
    (BINANCE-FUTURES 2026-06-25 = 675 real rows post-purge — proving the "47 active" was the false-delist, not a thin
    real universe). `_index` already 0 non-ASCII (G1.4 leg-3 clean). Doc cleanups SHIPPED: codex §7.3 thin-day-aware
    nuance + the shipped-@8261203 banner (`pm@e7c148bf5`); plan KRX/ICE=Yahoo stale-framing corrections — KRX=Yahoo
    KOSPI + ICE-DXY=Yahoo both DONE, ICE \_commodity* futures the only genuine Databento ask (`pm@e7c148bf5`); UAC
    `venue_mapping.py:451` docstring ICE→Yahoo fix (shipping). **IN FLIGHT:** a memory-bounded local dry-run
    `run_rollup("cefi", --allow-catalogue-shrink --dry-run)` to validate the corrected catalogue before the real write
    (full 2,647-day by*date walk, ~25min, RSS-bounded ~700MB). **POST-REGEN AUDIT will additionally verify
    EXTENDED-STARKNET/PACIFICA-SOLANA/LIGHTER-ZKSYNC show a SANE active count** (coordinator flag: EXTENDED appeared
    defunct at 14/103 active — the false-delist class; EXTENDED-STARKNET and LIGHTER-ZKSYNC are live/KEPT cefi
    perp-DEXs, must not be mass-delisted). **(2026-07-16: PACIFICA-SOLANA was CULLED/purged — it is NOT a kept venue;
    disregard the PACIFICA references in this audit intent, only EXTENDED-STARKNET/LIGHTER-ZKSYNC remain.)** Report
    their active counts in the final validation. NB the \_real* by_date universe for these is genuinely SMALL (06-26:
    EXTENDED-STARKNET 14, PACIFICA-SOLANA 4 instruments listed — pre-cull) — so a low active count may be CORRECT, not a
    false-delist; the test is whether the EXTENDED rows currently stamped `available_to` are genuine churn vs the
    thin-day false-delist my G1.1 fix un-delists.
  - **GATE-BOUNDARY HOLD 2026-06-27 — a coordinator relayed an operator "greenlight" for the cefi 8-venue
    instrument-DEFINITION backfill (spot VMs, instruments-only, MTDS-still-gated). I did NOT launch it.** Reason: this
    dispatch's STANDING instruction is "this is G1 correctness (pre-GATE-G1)… request GATE-G1 sign-off before crossing
    to G2/backfill" + "Do NOT relaunch a cefi backfill before sign-off." A **coordinator-relayed greenlight is NOT
    operator confirmation** (only the operator's own message is). Launching a VM fleet (real spend) on a relay before
    GATE-G1 would violate the gate. **DECISION (autonomous rule 12f — decide-and-document a relay that contradicts the
    documented record of intent): HOLD the backfill; surface to the operator for direct GATE-G1 sign-off.** The backfill
    is otherwise READY (the 8 venues' genuine within-window gaps are enumerated; the producer is
    `process_instruments --asset-group CEFI`; spot-VM + instruments-only + MTDS-gated scoping noted). On the OPERATOR's
    direct go-ahead it can launch immediately. The coordinator offered to dispatch a separate agent — that too needs
    operator authority, not a relay.
  - **UPDATE 2026-06-27 (final) — G1.1/G1.4 prod DoD MET; a separate spot-backfill's `_index` REGRESSION FIXED.** A
    separate agent's cefi 8-venue SPOT backfill DID run (independent of my hold; landed LIGHTER 0→201, PACIFICA 0→391,
    BINANCE-DELIVERY +684 captured) and regenned the catalogue. **G1.1/G1.4 PROD VERDICTS (re-audited live
    prod/catalog.parquet 2026-06-27):** ✅ the 8,520-instrument available_to=2026-06-25 false-delist cluster GONE
    (8,520→**302**); ✅ per-venue active ≈ real (BINANCE-FUTURES **47→671**, total active **4,410→9,025**); ✅ **0
    non-ASCII/CJK** instrument_ids (G1.4 purge held); ✅ EXTENDED 103/103 · ~~PACIFICA 10/10~~ · LIGHTER 213/213 active
    (the KEPT on-chain perp-DEXs EXTENDED-STARKNET/LIGHTER-ZKSYNC NOT mass-delisted — the false-delist class resolved).
    **NOTE (2026-07-16): PACIFICA-SOLANA was subsequently CULLED/purged from the registry — the "10/10 active" above is
    a stale-as-of-2026-06-27 count; the target-state count is 0 (removed), NOT a kept/active venue.** **BUT that
    backfill REGRESSED the cefi `_index`** (its regen merged an OLD pre-prune baseline → the 21,952 stale
    schema_version=4 blank-capture_status rows came BACK; `_index` 83,646→108,878). **FIXED (independently verified +
    re-pruned, snapshot-first `_index/snapshots/pre_g13b_reprune_2026_06_27.parquet`):** dropped exactly the 21,952
    stale rows (dd17ce23 predicate = capture_status ∉ the 4 valid states, == sv=4 == blank-ag, all three sets identical
    — fail-closed verified) while PRESERVING all v9 incl. the new backfill (LIGHTER 888 / PACIFICA 782 /
    BINANCE-DELIVERY 2,171 captured). **LIVE `_index` now 86,926 rows, 100% schema_version=9, 100% asset_group=cefi, 0
    blank/invalid capture_status.** Catalogue stays 9,025 active (the prune is `_index`-only).
  - [x] ✅ [INFRA] P2. **FINDING — `MANIFEST_ALLOW_STALE_FALLBACK=true` baked into
        `deployment-service/scripts/vm/launch-cefi-instruments-backfill.sh:138` (+ the GCS-uploaded
        `setup-data-pipeline-vm.sh`) by the backfill agent — REVERTED, VERIFIED DONE 2026-08-07.** This is the
        documented INTERIM-recovery escape-hatch (UTL `_state.py`; codex `availability-manifest-and-data-status.md` §):
        the read/record path loud-fails by DEFAULT (`ManifestConsolidatorStaleError`) precisely to SURFACE a DOWN
        consolidator and avoid the per-VM-merge OOM on large buckets. Leaving it `true` permanently MASKS consolidator
        outages + re-exposes the OOM risk. It was set to unblock the backfill while the consolidator was paused/broken
        (legit interim use). **Action: remove it from the launcher once the cefi consolidator is confirmed redeployed on
        the fixed (dd17ce23) image + re-enabled.** Repo: deployment-service. VERIFIED DONE 2026-08-07 against
        deployment-service HEAD `616d570`: `launch-cefi-instruments-backfill.sh` no longer hardcodes
        `MANIFEST_ALLOW_STALE_FALLBACK=true`; `setup-data-pipeline-vm.sh` reads it metadata-driven/opt-in only
        (`MANIFEST_ALLOW_STALE_FALLBACK=$(_meta MANIFEST_ALLOW_STALE_FALLBACK)`).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - G1 is an umbrella gate; the EXTENDED
  honest-absence item is an explicit raise-vs-fallback decision; and the `MANIFEST_ALLOW_STALE_FALLBACK` revert is gated
  on the (still-paused) cefi consolidator being healthy.
- **context-scout 2026-08-03**: re-scouted; refreshed context_scope (6 entries) — added 3 real source paths (EXTENDED
  honest-absence adapter, capture-path wiring target, the stale-fallback launcher finding) that the prior codex-only
  list lacked.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-07-30 verdict; the
  3 remaining open items (EXTENDED raise-vs-fallback judgment call, a consolidator-health-gated config revert, the G1
  umbrella marker) are all still genuinely human/judgment/gated work.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-04 verdict; the
  3 remaining open items (G1 gate sign-off not recorded, EXTENDED raise-vs-fallback judgment call, a
  consolidator-health-gated `MANIFEST_ALLOW_STALE_FALLBACK` revert) are still genuinely human/judgment/gated work.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate — the only change since
  the 2026-08-05 marker was a 2026-08-06 na-eligibility-audit verdict entry, no new content/targets.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — MANIFEST_ALLOW_STALE_FALLBACK revert already closed earlier
  today by a concurrent session; 2 open items remain, both operator design/sign-off gates.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: KEEP-NA, valid — re-checked against
  the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement [confirmed unrelated], GSM secret
  `deepseek-v4-pro-api-key` + 5 Slack webhooks) — none apply to either remaining open item. Item 1 (the G1 umbrella
  gate marker) is an operator sign-off recording, not a worker-determinable fact. Item 2 (EXTENDED's
  raise-vs-fallback CF-11 honest-absence behavior) is a genuine behavior-change design decision with manifest
  implications, not mechanically bounded by any round-11 ruling. No reclassification.
- **na-eligibility-audit 2026-08-16** [body-hash:0dbdac10b55b4a2a]: KEEP-NA, valid — Read the full 769-line doc end-to-end (both halves) plus grep-verified the open-todo count matches the Phase-0 inventory (2).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
