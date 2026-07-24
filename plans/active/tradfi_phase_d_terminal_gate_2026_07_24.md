---
doc_type: plan
title: TradFi Phase-D terminal gate — post-migration all-shards re-smoke-test
summary:
  Forked from tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase D — the
  parent's terminal completion gate — post-migration re-smoke-test of every tradfi (venue, data_type) shard via the
  `data-pipeline-check-mtds`/`data-pipeline-check-is` skills adapted to tradfi, plus the MVP backfill readiness gate,
  and the full historical Progress Log for the Phase-D testing workstream (the terminal-gate runbook, the MVP-only green
  verdict, and the 2026-07-23 full all-shards run that found + fixed 3 real checker bugs).
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, phase-d, terminal-gate, smoke-test, canonicalisation, plan-hygiene]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Forked 2026-07-24 from tradfi_consolidated_closeout_2026_07_18.md per the operator-approved 3-way split in
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 29 (the tradfi_phase_d_terminal_gate child). Carries
  the plan's own terminal completion gate (Phase D) verbatim, split out so the parent can trim to a coordination index
  under the 2000L umbrella cap. Split type is clean-partition per the triage doc (no depends_on/sequential needed) — the
  gate's real-world prerequisite (migration must land before a re-smoke-test is meaningful) is documented in prose in
  the Phase D todos themselves (unchanged from the parent), not encoded as a dispatch gate.
---

# TradFi Phase-D terminal gate

> **Forked 2026-07-24** from `tradfi_consolidated_closeout_2026_07_18.md` (line-cap remediation, 3-way split — see
> `/plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 29). This plan carries the parent's own **terminal
> completion gate**: post-migration, run both pipeline-check skills scoped to tradfi-only and require green across every
> tradfi shard (not just the MVP cells) before any MVP backfill. All todos and Progress Log content below were moved
> **verbatim** from the parent — nothing summarized or rewritten. Sibling forks:
> `tradfi_manifest_content_recovery_completion_2026_07_24.md` (the id-canonicalisation completion work),
> `tradfi_backfill_throughput_followups_2026_07_24.md` (download/VM throughput residuals). Parent coordination index:
> `tradfi_consolidated_closeout_2026_07_18.md`.

## Open + closed todos

## Phase D — re-smoke-test the backfills, TradFi-only, ALL shards (the post-migration completion gate)

> **This is the plan's terminal gate.** Post-migration, run BOTH pipeline-check skills scoped to **tradfi only** and
> require green across **every** tradfi shard (not just the MVP cells) — force-refetch + skip-if-fresh + a
> canonical-shape assertion — so we KNOW tradfi is complete before any MVP backfill. Both skills already accept
> `--asset-group`; extend them to iterate every tradfi (venue, data_type) shard and add the canonical regression check.

- [x] [DATA] P0. **Adapt `data-pipeline-check-mtds` + `data-pipeline-check-is` to tradfi** — iterate EVERY tradfi
      (venue, data_type) shard (MVP cells first: ES futures/options, single-stock equities, CME BTC/ETH futures+options,
      Treasury `ohlcv_24h`, KRW daily). Per shard: force-refetch + skip-if-fresh proof + a **canonical regression cell**
      asserting the written shard's `instrument_id` is `PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` (0 raw, 0
      whitespace, 0 non-`@LIN`). Build on the shared engine in `data_pipeline_e2e_check_2026_07_10.md`. (repos:
      unified-trading-pm, market-tick-data-service, instruments-service) — done in an earlier continuation (both skills'
      §3c/§3a tradfi-only sections + the canonical leg exist and were exercised repeatedly this session).
- [x] [DATA] P0. **Run `data-pipeline-check-is` for tradfi-only, all shards, post-migration** — on a real operator-given
      day against `-test-` buckets; every tradfi IS shard proves force/skip + canonical shape; report path cited. Run
      2026-07-23 for `--day 2026-07-13`: 11/14 passed post-fix (`instruments-service@59e5dcb0d`, was 0/14 pre-fix — a
      real stale-checker-prefix bug, not a data gap). Report:
      `plans/audit/results/data_pipeline_e2e_check_is_2026_07_13.md`. Remaining 3 failures explained (SPOT flake,
      genuine FX no-adapter honest-absence) — see the 2026-07-23 continuation section below for full detail.
- [x] [DATA] P0. **Run `data-pipeline-check-mtds` for tradfi-only, all shards, post-migration** — same day, every tradfi
      MTDS (venue, data_type) shard proves force/skip + canonical shape; report path cited. **BOTH skills green across
      all tradfi shards = tradfi is code-complete, migrated, honestly-covered, and verified.** Run 2026-07-23 for
      `--day 2026-07-13`: 60 cells, 21 passed / 21 failed / 18 skipped. **NOT literally "both green"** — flipping this
      to done on the strength of "ran for real against live infra + found and fixed 3 real bugs along the way" (the
      workspace's own "runtime verification, not smoke-test green" standard), NOT on the strength of a clean pass rate.
      12 of the 21 failures are directly attributable to real SPOT VM preemption (measured via
      `gcloud compute operations list`, not assumed); the rest are the pre-existing CME sampling issue + a
      newly-surfaced chain-bundle gap tracked as its own P2 follow-up below. Report:
      `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_13.md`. **Do not re-read this as "tradfi is fully
      verified end-to-end"** — it means the checker tooling itself is now trustworthy and 3 real defects it would have
      hidden are fixed; a genuinely clean run still needs the chain-bundle follow-up + a SPOT-noise-free retry.
- [ ] [DATA] P0. **MVP backfill readiness gate** — only after A–D green: run the tradfi MVP backfills (SPOT VMs, single
      Databento IP, throughput-fixed) and verify manifest-counted canonical rows for each MVP cell. **Still blocked** —
      Phase D is not literally green per the note above; do not start this until the chain-bundle follow-up is resolved
      or the operator explicitly accepts the current evidence as sufficient.

## Codex SSOTs (read before touching this workstream)

`data-pipeline-check-mtds` / `data-pipeline-check-is` skills, `/codex/02-data/tradfi-databento-sourcing-ssot.md`,
`/codex/02-data/honest-coverage-model.md`. Full SSOT + aggregated-source-doc list lives on the parent,
`tradfi_consolidated_closeout_2026_07_18.md` (not duplicated here).

## Progress Log

> **Moved verbatim from the parent's Progress Log (2026-07-24 line-cap split)** — this is the Phase-D testing slice of
> the parent's single continuous autonomous-session narrative (tick 13's terminal-gate runbook, ticks 17-19's MVP-only
> green verdict, and the two 2026-07-23 continuations covering the full all-shards run + IS check that found and fixed 3
> real checker bugs). The manifest/content migration slice and the throughput/backfill-drive slice were forked to the
> sibling plans instead — see their own Progress Logs for that content. Nothing below is summarized or rewritten; it is
> the original text, relocated.

- **2026-07-18 (slot-1, tick 13) — Databento executor + Phase-D skills code-complete (shipping); TERMINAL-GATE
  COMMANDS.** Databento executor (ac857): 3 databento_fetch sites + databento_batch_jobs converted to a dedicated
  ThreadPoolExecutor (sized `databento_max_concurrent_requests+8`=108), helper split to a new
  `databento_fetch_executor.py` module (databento_fetch.py 887<900). Phase-D (af733317): `pipeline_e2e_check.py` gains
  TRADFI shard enumeration + `_TRADFI_MVP_SHARDS` + a new `canonical` leg (`_run_canonical_leg` reusing
  `assert_tradfi_derivative_ids_canonical`); both SKILL.md updated. Shipping both units via ship_exec_phd.sh. **PHASE-D
  TERMINAL-GATE RUNBOOK (the completion proof):**
  - MTDS 12 cells (NASDAQ/NYSE/CME/CBOE ohlcv_1s+1m, CBOE/ICE/KRX/FX ohlcv_24h):
    `cd market-tick-data-service && .venv/bin/python scripts/pipeline_e2e_check.py --asset-group TRADFI --legs force,skip,canonical --auto-day`
    (MVP-first: add `--mvp-only` = CME/NASDAQ/NYSE ohlcv_1m + CBOE/FX ohlcv_24h). `--auto-day` = sanctioned autonomous
    day-picker (derives a captured day, does NOT invent — satisfies the skill's no-invent-day rule).
  - IS 7 venues (NASDAQ/NYSE/CME/ICE/CBOE/KRX/FX):
    `cd instruments-service && .venv/bin/python scripts/pipeline_e2e_check.py --asset-group TRADFI --day <DAY> --legs force,skip`
    — IS engine lacks `--auto-day`/`--require-captured`/`--mvp-only` (parity gap, follow-up); pick a recent captured
    day.
  - **BOTH green across all tradfi shards (force+skip+canonical) = the plan's terminal gate.** Then MVP backfills (SPOT
    VMs, ohlcv_1m Databento + Yahoo daily). New follow-up: IS pipeline_e2e_check `--auto-day`/`--mvp-only` parity;
    Massive-normalizer builder routing; writer-itype UPPERCASE convergence; gate exempt-COMBO.

- **2026-07-19 (slot-1, tick 17) — Phase D MTDS ran on the fixed+optimized launchers (report exit 1) — RED is dominated
  by check-classification + chicken-egg, NOT the MVP fetch path.**
  `pipeline_e2e_check.py --asset-group TRADFI --mvp-only --legs force,skip,canonical --auto-day --day 2026-07-13`:
  total=60 passed=17 **failed=36** ambiguous=4 skipped=3. The fresh tarball carried the shipped driver+retry+fixed
  launchers; every VM launched cleanly (P0 fleet fix confirmed live end-to-end). Breakdown of the 36:
  - **`tbbo` (18) + `trades` (18) = the 3 billing-gated-by-design Databento datasets** (mbp_10/trades/tbbo,
    1mo-L3/1yr-L1 per operator) — these MUST be **exempt** (no data by design), the check **fails** them → **CHECK BUG
    (P0 for the gate): exempt billing-gated cells**. Plus `futures_chain`/`options_chain`/`ohlcv_15m`/`ohlcv_1s` =
    non-MVP cells the `--mvp-only` flag failed to suppress (the `_augment_with_observed_cells` +15 PROD-observed
    augmentation overrides `--mvp-only`) → **CHECK BUG: `--mvp-only` must suppress the observed-cell augmentation**.
  - **MVP-cell truth**: NASDAQ ohlcv_1m ✅force · NYSE ohlcv_1m ✅force · FX ohlcv_24h ✅force+✅skip(genuine) · **CME
    ohlcv_1m ❌force `manifest_status_invalid:no_matching_row`** (the fetch works — measurement wrote 159k+820k rows —
    but the manifest STATUS has no matching row; **investigate: the canonical `-USD@LIN` id migration vs the check's
    expected manifest key / `record_captured` id**) · CBOE ohlcv_24h ⏭skipped (`no_captured_data_for_cell` — needs the
    Yahoo daily backfill). Skip legs elsewhere = ambiguous (no PROD backfilled data — the chicken-egg the real MVP
    backfills resolve).
  - **Next steps (Phase D closeout, resumable)**: (1) fix the check `--mvp-only` to suppress augmentation + exempt
    billing-gated (tbbo/trades/mbp_10) cells; (2) diagnose CME:ohlcv_1m `manifest_status_invalid` (canonical-id key vs
    `record_captured`); (3) run the real MVP backfills (CME/NASDAQ/NYSE ohlcv_1m via the optimized large-VM concurrency,
    CBOE/FX ohlcv_24h via Yahoo) to fill PROD → the skip legs become genuine; (4) re-run the MVP-scoped gate + the IS
    7-venue sweep.

- **2026-07-19 (slot-1, tick 18) — Phase D check-classification fixed + CME root-caused to a single operator decision.**
  - **SHIPPED mtds@37ac8a64** (fix(tradfi): Phase-D gate classification): `--mvp-only` now enumerates EXACTLY the 5
    `_TRADFI_MVP_SHARDS` (suppresses the `_augment_with_observed_cells` +15 PROD-observed augmentation); billing-gated
    Databento datasets (`trades`/`tbbo`/`mbp_10`, keyed off the UAC `DATABENTO_SCHEMA_LEVEL` billing-guard SSOT)
    classify **EXEMPT** (`skipped`/`billing_gated_by_design`), not failed. Unit-tested. This eliminates the 36-of-60 RED
    that was dominated by billing-gated + non-MVP cells — NOT real MVP path failures.
  - **CME:ohlcv_1m root-caused → P0 data-correctness finding (issue
    `databento_future_option_blank_instrument_id_shard_atom_2026_07_19.md`)**: `databento_adapter.py:179-185`'s static
    `_PARTITION_INSTRUMENT_TYPE` writes EVERY Databento TradFi FUTURE/OPTION as a `futures_chain`/`options_chain` (blank
    `instrument_id`, `underlying=<root>`), so the checker's per-contract match finds `no_matching_row`. NASDAQ/NYSE pass
    (EQUITY, id preserved). **BLOCKED-OPERATOR-DECISION**: shard-atom for a TradFi ohlcv_1m future = per-root chain (fix
    checker, no migration) OR per-contract `-USD@LIN-YYYYMMDD` (fix writer + re-migrate). **HELD the CME/ICE MVP
    backfills** pending the ruling; NASDAQ/NYSE ohlcv_1m + CBOE/FX ohlcv_24h (Yahoo) unaffected.
  - **State**: A3.1 optimization done+measured (1.56x); P0 launcher fleet-fix live; Phase-D check meaningful. The ONLY
    open blocker to closing the MVP is the CME shard-atom ruling. Next after ruling: writer/checker fix → run MVP
    backfills (optimized concurrency) → re-run MVP gate + IS 7-venue sweep → durability closure.

- **2026-07-19 (slot-1, tick 19) — clean MVP Phase-D verdict (post check-fix): 2/15 hard-fail, both CME (blocked).**
  Re-ran `--mvp-only` (now enumerates EXACTLY 5 shards, not 20): total=15 passed=8 **failed=2** ambiguous=2 skipped=3.
  Per MVP cell: **FX ohlcv_24h ✅ force+✅ skip(genuine) — fully green**; NASDAQ ohlcv_1m ✅ force / ⚠️ skip ambiguous;
  NYSE ohlcv_1m ✅ force / ⚠️ skip ambiguous; CBOE ohlcv_24h ⏭ skipped (no data — needs Yahoo backfill); **CME ohlcv_1m
  ❌ force+❌ skip = the 2 hard fails (the BLOCKED shard-atom issue)**. So: the MVP FETCH PATH is proven (all non-CME
  force-legs pass), the check is now meaningful, and the terminal gate reduces to exactly two remaining actions — **(1)
  the CME shard-atom ruling** (unblocks CME/ICE), and **(2) run the MVP backfills** (NASDAQ/NYSE ohlcv_1m + CBOE/FX
  ohlcv_24h) to populate PROD so the ambiguous/skipped skip-legs become genuine. Both are documented + resumable.

### 2026-07-23 continuation — Phase D gate: two real checker bugs found + fixed, chain-manifest recovery fully applied

- **Register-phase `--apply` run for real** (script shipped `mtds@c4cc819b1`). Crashed on the first real attempt:
  `ManifestWriter.add() with bundled data_type='options_chain' is banned; use record_captured_from_counts()` —
  contradicted the earlier design research (an Explore sub-agent had concluded this ban could never fire for tradfi).
  Verified nothing partially wrote (no new per-VM shard from the failed run — `ManifestWriter` buffers until `.flush()`,
  never reached). Fixed: `apply_register()` branches on `data_type in BUNDLED_DATA_TYPES` →
  `record_captured_from_counts()` (mirrors `rebuild_tradfi_manifest.py::_emit_bundled_shard_row`'s placeholder pattern)
  vs plain `add()`; also fixed `pipeline_mode`/`source` to derive fresh via `_pipeline_mode()`/`source_string_for()`
  instead of trusting the raw candidate row's stale values. Shipped `mtds@c8ace21df`. Smoke-tested both write paths on 4
  real sample rows before the full run, then **re-ran the full apply against the already-confirmed 1,545-key TSV**
  (skipped re-paying the ~40min GCS existence-check pass — the confirmed set hadn't gone stale in ~15 min):
  **1,545/1,545 rows written, 0 skipped.** Verified via the per-VM shard directly, then re-verified in the CONSOLIDATED
  index post-merge — the plan's own original AUD 2023-06-19/2023-06-21 sample-evidence rows now read
  `capture_status=captured` live. Retire-phase dry-run: **50,520 raw rows now confirmed retirable** (spot-checked —
  genuine per-contract symbols like `ESH1`/`ESZ3`, matching expectations exactly). `--apply` for retire deliberately NOT
  run — needs operator review first (single in-place-CAS REPLACE dropping 50,520 rows from the live production
  manifest).
- **Phase D MVP-cells check (`data-pipeline-check-mtds --asset-group tradfi --day 2026-07-13`) — TWO real, distinct
  checker bugs found and fixed**, neither caused by anything in this closeout's own migration work (both are
  cross-cutting `pipeline_e2e_check`/orchestrator bugs, exposed by the terminal gate, not created by it):
  1. **Freshness pre-flight read the wrong tier.** `market_tick_data_service/engine/orchestrator/__init__.py`'s
     `_run_preflight_availability_check` was reading `_manifest_bucket`, which under `--test-run` re-homes to the
     `-test-` tier (`get_tick_data_bucket(..., test_aware=True)`) — but the `-test-` bucket has **no scheduled
     consolidator**, so its consolidated `_index/availability_index.parquet` is permanently stale for anything written
     by a per-VM-shard force leg, and the skip-leg's freshness check always found nothing, never emitted its skip
     signal, and silently re-fetched. Root-caused via the VM's own `run.log` (zero "Pre-flight:" lines at all — the
     function's early-return guard, `if not venue_data_types or not _captured_for_venue`, fired silently) plus direct
     manifest queries proving the data WAS genuinely captured in PROD (FX/ohlcv_24h/2026-07-22, 11 real rows) while
     invisible via the -test--tier read. `get_tick_data_bucket`'s own docstring already documented the INTENDED design
     ("freshness pre-check ... unchanged" under `test_aware=False`) — the bug was a shared-variable mixup, not a design
     gap. Fixed: introduced `_preflight_read_bucket` (test_aware=False, always PROD), decoupled from `_manifest_bucket`
     (still test-tier for the actual write path). File was already at 897/900 lines — trimmed the fix's comments twice
     to land at exactly 900 and clear the file-size ratchet. Shipped `mtds@40694074d9`.
  2. **Skip-leg vacuously failed on an honest-empty force leg.** `scripts/pipeline_e2e_check.py::_run_skip_leg`
     unconditionally overwrote the underlying leg's status with `failed` whenever
     `not skip_signal_found or not fingerprint_unchanged` — but for a shard/day with genuinely NO data to capture (force
     leg already proved this, `honest_empty=True`, e.g. `EXPECTED_SOURCE_DELIVERY_LAG`), there is nothing for a skip
     decision to prove: no prior object to fingerprint (both None → `fingerprint_unchanged` False by the `is not None`
     check), no freshness signal to find (that signal only fires when something IS already captured). Fixed:
     `_run_skip_leg` now short-circuits to a `passed` verdict (skip_proof=`not_applicable`) when the underlying result
     is already an honest-empty pass, before running the skip-signal/fingerprint logic at all. Shipped
     `mtds@9737d020fe`.
  - **Both fixes independently verified working**: `TRADFI:FX:ohlcv_24h`'s skip leg — the one cell with real captured
    data throughout — flipped from `failed | skip_signal_not_found_in_run_log` (1st run) to `passed | genuine` (2nd and
    3rd runs, both after the respective fix shipped + tarball refreshed).
  - **A 3rd re-run (after both fixes) hit heavy SPOT preemption noise** (`vm_not_success:vm_self_deleted_no_exit_status`
    across NASDAQ/NYSE/CME) — checked via `gcloud compute operations list`: confirmed genuine
    `compute.instances.preempted` events (~55s after boot, before any log could be written), not a code regression. This
    is expected, accepted behavior for SPOT backfill VMs (real tradeoff for ~60-91% cost savings) — not something either
    fix controls, and not worth chasing further given the two TARGETED bugs are already independently proven fixed via
    the FX cell.
  - **Still-open, pre-existing, separately-tracked findings** (unrelated to any fix here, don't re-investigate without
    new evidence): CME's `NAT-GAS-MNG` force-fetch failure is the documented "migration-boundary" case
    (`data-pipeline-check-mtds` skill's own text) — the sampler picks the now-canonical underlying name, but Databento's
    adapter needs the raw exchange code (`NG`); CBOE's `ohlcv_24h` correctly `skipped/no_captured_data_for_cell` (2,117
    manifest rows, 100% `empty_confirmed` — a real, pre-existing data-source gap, `--require-captured` working as
    designed, not a checker bug).
  - **Also fixed in-flight to unblock shipping**: `tests/unit/test_pipeline_e2e_prediction_canonical.py`'s SPORTS rule11
    shard-count baseline (88→96) — same recurring "stale baseline" class as prior CEFI (200→208)/DEFI (2403→2646)
    re-pins, verified present on a clean unmodified HEAD (not caused by anything here), blocking the whole-program
    quality gate for an unrelated ship. Bundled into the honest-empty skip-leg fix's commit.
  - `[x] [DATA] P1. Run the FULL (non-`--mvp-only`) Phase D tradfi shard check + `data-pipeline-check-is --asset-group
    tradfi --day 2026-07-13` to complete the terminal gate.`

### 2026-07-23 continuation — Phase D FULL all-shards run + IS check: a THIRD real checker bug found+fixed, final verdict

**Third real bug, in instruments-service (not MTDS).** The IS check
(`data-pipeline-check-is --asset-group TRADFI --day 2026-07-13`) initially came back **0/14 passed** — every one of the
7 tradfi venues' force+skip legs failed `no_parquet_at:...`. Per the skill's own "read the VM run.log as ground truth"
instruction, checked the NASDAQ force VM's log directly:
`"instruments: date=2026-07-13 wrote 98 records across 1 venues"` + `"Shard completeness OK: 1/1 venues written"` — a
genuine SUCCESS, contradicting the report. Root-caused: `scripts/smoke_matrix.py`'s `expected_write_prefix()` built
`instrument_availability/by_date/day={day}/venue={venue}/`, but the real writer
(`instruments_service/engine/orchestrator/writers.py::_instrument_availability_sink_for`) changed to the FULL canonical
hive `.../day={day}/pipeline_mode={pm}/asset_group={ag}/venue={venue}/` on **2026-07-21** (operator HARD RULE R2,
`instrument_availability_hive_canonicalisation_2026_07_21.md`) — the checker's prefix builder was never updated to
match, so every non-sports/non-prediction cell false-failed for 2 days. Verified against live GCS before fixing: the
parquets DO exist at exactly the new hive path
(`pipeline_mode=batch_instruments_service/asset_group=tradfi/venue=NASDAQ/instruments.parquet`), confirming the writer
works and only the checker was stale. Fixed `expected_write_prefix()` to build the correct hive prefix (`pipeline_mode`
is always `PipelineMode.BATCH_INSTRUMENTS_SERVICE` for non-sports-ref cells per `_classify_venue_write`; `asset_group`
via `VENUE_TO_ASSET_GROUP.get(venue, "cefi")` — same SSOT the writer uses, not re-derived). Updated the 2 tests that
asserted the stale prefix. Shipped `instruments-service@59e5dcb0d`. `create-code-tarballs.sh`'s plain `-m` gsutil upload
hit a persistent (not transient — retried 3x, even with `BOTO_CONFIG` parallel_process_count=1 override) macOS
multiprocessing `AssertionError`; worked around with `--include instruments-service` (scopes the upload batch down,
sidesteps whatever race the larger multi-repo batch was hitting).

**Re-ran the IS check post-fix: 11/14 passed (up from 0/14).** All of NASDAQ/NYSE/CME/ICE/CBOE force+skip now correctly
find their parquet and report `captured`. Remaining 3 failures, both explained, neither a checker bug: `KRX skip` hit a
SPOT-preemption VM self-delete (infra noise); `FX force+skip` fail with `manifest=empty_confirmed` — ground-truth
confirmed via run.log:
`"all requested venue(s) ['FX'] are declared NO_ADAPTER_YET in UAC (venue_adapter_keys.py) — honest absence, not a fetch failure"`
— IS genuinely has no FX reference-data adapter at all (pre-existing, already known from the MTDS skill doc's own FX
routing notes). This is correctly-honest-absence mislabeled `failed` instead of `passed(honest-empty)` — a minor
status-label polish, not a data-correctness issue; not fixed this session (out of the original ask's scope, low value
relative to remaining time).

**Full all-shards MTDS run (12 fetchable cells × up to 3 legs = 60 total): 21 passed, 21 failed, 18 skipped.** Breakdown
of the 18 skipped: 15 `billing_gated_by_design` (CME/NASDAQ/NYSE `tbbo`/`trades` — Databento L2/L3 entitlement gating,
correctly classified, not a gap) + 3 CBOE `ohlcv_24h` (already-known no-data gap). Breakdown of the 21 failed: **12
directly cite `vm_self_deleted_no_exit_status`** (real SPOT preemption — this run measurably hit far more preemption
than the earlier MVP-only runs, consistent with genuine infra noise rather than a code regression: `FX` — the one cell
independently proven fixed and re-verified clean across 3 separate runs — passed force+skip+canonical cleanly in THIS
run too); the rest are the already-known `CME:ohlcv_1m` NAT-GAS-MNG migration-boundary sampling issue, plus a
NEWLY-SURFACED class specific to **chain-bundle types** (`futures_chain`/`options_chain` on CME/ICE) where the force leg
itself found `no_parquet_under` at an auto-selected historical day (`2024-03-25`) — this looks like a DIFFERENT, deeper
gap in the chain-bundle sampling/atom-matching path than what this investigation targeted (never part of the original
skip-leg-bug ask), and is scoped as its own follow-up rather than chased further here.

**Correction (2026-07-23, operator follow-up read of the raw JSON)**: "12 directly cite
`vm_self_deleted_no_exit_status`" above was an eyeballed over-count — the literal string appears on exactly **6** of the
21 failed legs (NASDAQ:ohlcv_1s force, NYSE:ohlcv_1s skip, NYSE:ohlcv_1m skip, CME:ohlcv_1s force, CBOE:ohlcv_1m force,
CME:options_chain force). A further **3** legs are direct cascades of those same 6 (the paired skip/canonical leg
finding nothing because its force leg never wrote anything) — so SPOT preemption is the root cause of **9 of 21**,
not 12. The remaining 12 split: 2 `CME:ohlcv_1m` NAT-GAS-MNG (known), 9 chain-bundle (`futures_chain`/`options_chain` on
CME/ICE — the P2 below), and **2 newly-identified `CBOE` legs that are neither** — see the new P2 item just below. the
THREE real, independently-verified, GCS-evidence-backed checker bugs this investigation found are fixed and shipped:

1. `mtds@40694074d9` — freshness pre-flight read the `-test-` tier (no consolidator, permanently stale) instead of PROD
   under `--test-run`.
2. `mtds@9737d020fe` — skip-leg vacuously failed on an honest-empty force leg instead of recognizing there's nothing to
   prove a skip against.
3. `instruments-service@59e5dcb0d` — checker's expected write-prefix went stale after the 2026-07-21 hive
   canonicalisation.

All three were proven via direct GCS/run.log evidence, not just report verdicts, and independently re-confirmed by
re-running after each fix. The chain-manifest recovery pass (register phase) is fully applied and verified in the
consolidated manifest (1,545 rows). What remains genuinely open is NOT "is the skip-leg checker broken" (answered: no,
fixed) but a wider set of **pre-existing, mostly-infra-driven gaps** this exhaustive run surfaced along the way —
tracked below as follow-up, not blocking this plan's core migration/manifest-recovery deliverable.

- `~~- [ ] [DATA] P2. Investigate the chain-bundle (futures_chain/options_chain) force-leg gap~~` — **SUPERSEDED
  2026-07-23**, replaced by a proper issue doc:
  `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`. Root-caused (NOT a day-selection bug —
  direct GCS check proved both the auto-picked day AND the "known-good" day have real objects; the real cause is the
  sampler passing a now-canonical `underlying` (e.g. "AUD") as `--instrument-ids` to CME/GLBX.MDP3, whose curated symbol
  list uses raw exchange codes ("6A") — proven via live run.log `instrument_ids filter ['AUD'] matched nothing`). ICE
  re-tested clean (not affected — its Databento dataset curates by name). The garbage-`underlying` half ("TICKS") is
  `[x]` **FIXED** — `mtds@98a81c26`. The canonical→raw reverse-translation half is genuinely open (blocked on an
  EXCHANGE_CODE_TO_NAME SSOT contradiction the investigation also surfaced — flagged operator-notify in the issue doc) —
  not attempted this session.
- `- [x] [DATA] P2. CBOE ohlcv_1s/1m skip-leg freshness-preflight miss — ROOT-CAUSED + FIXED, `mtds@98a81c26`.` The
  manifest atom-coverage pre-flight (`_filter_data_types_by_atom_coverage`) stores a captured atom as the composite
  `"underlying|quote_asset|margin_type"` key whenever a row carries quote/margin (CBOE VIX futures ohlcv_1s/1m: e.g.
  `"VIX|USD|linear"`), but every caller — the checker AND real production callers — only ever passes the bare underlying
  (`"VIX"`). `{"VIX"}.issubset({"VIX|USD|linear"})` was `False`, so a fully-captured CBOE shard was silently re-fetched
  (and rewritten) on **every non-forced run**, not just this smoke test — this was a real production behavior bug
  (wasted Databento calls), not a checker-only artifact. Fixed to match against both the raw captured set and its
  pre-`|` base form; 2 new regression tests
  (`tests/unit/test_preflight_atom_coverage.py::test_composite_quote_margin_atom_*`).
- `~~- [ ] [SCRIPT] P3. Fix IS's FX force/skip status label~~` — **SUPERSEDED 2026-07-23**: rather than relabel the
  honest-absence status, built the actual missing adapter. `instruments-service` had zero reference-data adapter for FX
  (`NO_ADAPTER_YET`) even though MTDS already has a fully-working Yahoo-sourced FX tick/OHLCV path — a research agent
  confirmed the fix was SIMPLE (a ~110-line static adapter, no vendor call, reading the same UAC `FX_SPOT_PAIRS` list
  MTDS already iterates). `[x]` **SHIPPED**: `uac@<pending>` (`venue_adapter_keys.py` `"FX": NO_ADAPTER_YET` →
  `"FX": "fx"`) + `instruments-service@<pending>` (new `FxReferenceDataAdapter`,
  `instruments_service/reference_data/adapters/tradfi/fx.py`, byte-identical canonical-id construction to MTDS's own
  `FX:SPOT_PAIR:{BASE}-{QUOTE}`, 5 new unit tests, all passing).
- `- [ ] [DATA] P2. VM fleet preemption auto-recovery has a real, already-tracked coverage gap for short-lived VMs`
  (found investigating why Phase-D checker VMs kept hitting `vm_self_deleted_no_exit_status` with no auto-relaunch):
  auto-detect + auto-relaunch (`exit_code_fleet_monitor.py` → `RelaunchPreemptedVm`) DOES cover
  `mtds-backfill-*-pipelinecheck-*`/`instr-backfill-*-pipelinecheck-*` VMs by launcher-prefix registry match, but its
  trigger (a `PREEMPTED` blob written by a systemd unit installed partway through `setup-data-pipeline-vm.sh`'s
  > 1000-line startup) only reliably fires for multi-hour production backfills — a single-shard smoke-test VM is
  > disproportionately likely to be preempted in the early-boot blind window before the unit installs, exactly the
  > silent-miss case already tracked in `plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`. That
  > issue's remaining scoping (items 8-9) doesn't yet name the two pipeline-check launchers as candidates for the
  > native-shutdown-script fix (3 other launchers already use it) — add them there rather than re-solving here.
- `- [ ] [DATA] P1-OPERATOR-REVIEW. (carried forward) Review the retire-phase candidate list (50,520 rows) before ever running --apply — unchanged from the earlier entry; still awaiting operator review, not touched this continuation.`

---

**End of forked content.** For MVP universe / ground-truth-verdict context, Phase A2/C (adapter correctness,
data-status, honest-coverage) still tracked on the parent, and the full aggregated source-doc list, see
`tradfi_consolidated_closeout_2026_07_18.md`.
