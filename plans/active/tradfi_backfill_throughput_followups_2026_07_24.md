---
doc_type: plan
title: TradFi backfill-throughput follow-ups — download/VM throughput residuals + T+1 job hardening
summary:
  Forked from tradfi_consolidated_closeout_2026_07_18.md's 2026-07-24 line-cap remediation split. Carries Phase A3
  (download/backfill throughput — DNS-starvation executor, T+1 forward-fill job, OOM/SIGKILL hardening, phantom-row
  retirement) + Phase A3.1 (the Databento e2e throughput optimization — date-concurrency driver, disk sizing,
  concurrency-cap raise, equity re-sharding) + the 3 open follow-up todos the tick-26 throughput re-analysis surfaced,
  plus the full historical Progress Log for the throughput/backfill-drive workstream (ticks 14, 16, 22, 26-ETA, the
  T+1/yfinance restore, the Backfill-drive + Databento-free-entitlement sections).
status: active
nature: process
asset_group: [tradfi]
stage: [meta]
repos:
  [market-tick-data-service, deployment-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, backfill, throughput, vm, databento, plan-hygiene]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: xhigh
context_scope:
  [
    /plans/archive/2026_08/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  Forked 2026-07-24 from tradfi_consolidated_closeout_2026_07_18.md per the operator-approved 3-way split in
  plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 29 (the tradfi_backfill_throughput_followups child).
  Carries the download/backfill-throughput workstream (Phase A3 + A3.1) verbatim, split out so the parent can trim to a
  coordination index under the 2000L umbrella cap.
---

# TradFi backfill-throughput follow-ups

> **Forked 2026-07-24** from `tradfi_consolidated_closeout_2026_07_18.md` (line-cap remediation, 3-way split — see
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` row 29). This plan carries the download/backfill
> THROUGHPUT workstream: Phase A3 (DNS-starvation executor, T+1 forward-fill job, OOM/SIGKILL hardening, phantom-row
> retirement) and Phase A3.1 (the Databento e2e throughput optimization — gated concurrent-date driver, disk sizing,
> concurrency-cap raise, equity re-sharding). All todos and Progress Log content below were moved **verbatim** from the
> parent — nothing summarized or rewritten. Sibling forks: `tradfi_manifest_content_recovery_completion_2026_07_24.md`
> (the id-canonicalisation completion work), `tradfi_phase_d_terminal_gate_2026_07_24.md` (the post-migration all-shards
> re-smoke-test terminal gate). Parent coordination index: `tradfi_consolidated_closeout_2026_07_18.md`.

## Open + closed todos

### A3 — Download / backfill THROUGHPUT (so Phase-D re-backfill is fast + reliable)

- [x] ✅ [BACKEND] P0. **Databento DNS-starvation executor risk — FIXED (mtds@ac857, `databento_fetch_executor.py`).**
      The 3 `databento_fetch` call sites + the `_next_dbn_chunk` DBN decode now run on a dedicated
      `ThreadPoolExecutor(thread_name_prefix="databento-fetch")` sized `databento_max_concurrent_requests+8` (=108) —
      never the asyncio default pool (which aiohttp's `getaddrinfo` needs), the exact anti-pattern that wedged the CeFi
      Tardis backfill ~350x. Helper split to a new `databento_fetch_executor.py` (databento_fetch.py 887<900). Confirmed
      live 2026-07-18 (research: 3 wired sites). Tracking issue
      `databento_default_executor_dns_starvation_risk_2026_07_17.md` is now STALE (fix landed) → doc-hygiene flip
      pending. (repo: market-tick-data-service)
- [ ] [INFRA] P1. ~~**Backfill-VM startup OOM rc137** (`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, open)~~ **←
      this leg is DISCHARGED (see below)** + **OOM remediation baked default**
      (`tradfi_backfill_oom_remediation_2026_06_24.md`, e2-highmem-4, verify) + **consolidator throughput/backlog
      monitor** (`consolidator_throughput_backlog_monitor_2026_07_09.md`). (repos: deployment-service,
      market-tick-data-service) **STALE-CITATION FIX (na-eligibility-audit 2026-08-02, tradfi tranche)**: the rc137
      leg's "(open)" annotation was stale — that doc reached zero open todos and was ARCHIVED 2026-08-02 (`651bc8b39`)
      to `/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`, `status: complete`, under the
      operator's 2026-07-30 line-cap-does-not-block-archival ruling; both of its own "real open items" were discharged
      at archival, not dropped (consolidator cron un-pause = MOOT/verified ENABLED; Morpho `lending_indices` live-verify
      migrated to a tracked todo in `/plans/archive/2026_08/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`).
      This checkbox stays `- [ ]` because the OTHER two legs are still genuinely open — verified live this pass:
      `/plans/archive/2026_08/issues/tradfi_backfill_oom_remediation_2026_06_24.md` was `status: open` with 1 open todo
      at the time (path corrected 2026-08-16 — see citation-refresh entry below), and
      `/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md` is `status: active` with 3 open todos.
      **(2026-08-08 na-eligibility-audit citation refresh)**: `tradfi_backfill_oom_remediation_2026_06_24.md` is now
      `assigned_vm: planning` (already actively AO-dispatched, a stronger duplication claim than "just still open");
      `consolidator_throughput_backlog_monitor_2026_07_09.md`'s open-todo count has drifted 3→2 (one item closed
      2026-08-07 by a concurrent audit pass in that doc's own `[ui]` tranche). Neither change affects this checkbox's
      umbrella-pointer verdict.
      **(2026-08-16 na-eligibility-audit citation refresh)**: `tradfi_backfill_oom_remediation_2026_06_24.md` now
      measures **0 open todos** (still `status: open`, not yet archived by its own owner — not this doc's action to
      take), a stronger claim than "actively dispatched." `consolidator_throughput_backlog_monitor_2026_07_09.md` still
      has 2 open todos, unchanged — that leg keeps this checkbox open as an umbrella pointer.
      **(2026-08-16 plan_reconciler Phase -1 citation refresh, same day)**: `tradfi_backfill_oom_remediation_2026_06_24.md`
      has now been archived (`plans/archive/2026_08/issues/tradfi_backfill_oom_remediation_2026_06_24.md`) — the
      leading-slash reference above is repointed. Does not change this checkbox's verdict: the umbrella pointer stays
      open on the `consolidator_throughput_backlog_monitor_2026_07_09.md` leg alone (2 open todos, unchanged).
- [x] ✅ [INFRA] P1. **TradFi has NO working T+1 forward-fill job** (`tradfi_t1_no_working_mtds_job_2026_07_17.md`) —
      add source-scoped `…-tradfi-databento-t1-recon` Cloud Run job; live coverage erodes daily without it. (repos:
      deployment-service, market-tick-data-service) **INFRA SHIPPED + APPLIED 2026-07-20 — deployment-service@11bed3c;
      execution BLOCKED on a fleet-wide image bug (NOT this job's defect).** Terraform landed + `tofu apply [prod]`
      clean (**2 add / 0 change / 0 destroy**): Cloud Run job
      `uts-prod-market-tick-data-service-tradfi-databento-t1-recon`
      (`--operation download --mode batch --asset-group TRADFI --source databento --data-types ohlcv_1m ohlcv_1s`,
      2cpu/8Gi) + scheduler `uts-prod-market-tick-data-tradfi-databento-t1-schedule` (`35 0 * * *`, ENABLED) — both
      verified present via `gcloud run jobs list` / `gcloud scheduler jobs list`. **The inherited WIP's
      `--source massive` job + scheduler entry were REMOVED, not shipped**: the WIP predated the 2026-07-19 Massive
      removal, and `--source` is now `choices=["databento"]` (`mtds cli/main.py:197`) with `umi_tick_provider` failing
      closed on non-databento and a `source='massive'` manifest write raising — so it would have failed argparse on
      EVERY run. Databento covers everything Massive served (DBEQ.BASIC equities, GLBX.MDP3 CME) plus CBOE/VX and
      ohlcv_1s, so ZERO coverage gap. SSOT: `/codex/02-data/tradfi-databento-sourcing-ssot.md`. **Still `- [ ]` because
      rows-written is UNPROVEN**: two real executions exited 1 at interpreter start —
      `ImportError: cannot import name 'is_recognized_tradfi_underlying' from 'unified_api_contracts'`. Root cause is a
      stale UAC bundled in the MTDS image, which kills **every** MTDS Cloud Run job (cefi-t1-recon failing since
      ≥2026-07-19, fast-t1-recon 4× today) — filed P0
      `issues/mtds_image_uac_dep_skew_breaks_all_cloud_run_jobs_2026_07_20.md`. Tick this todo once that image is
      rebuilt and one execution writes T-1 rows. **UPDATE 2026-07-20: image REBUILT + FIXED
      (`cloudbuild=2bb2c71c-c43c-4e97-9613-cacdf81b6976` SUCCESS) and rows ARE now proven — execution `…-9c9nb` wrote
      **6,782 rows** for 2026-07-17 and `…-8hfw7` wrote **5,189 rows** (CBOE/VIX ohlcv_1m) for 2026-07-16, both at
      canonical `…/pipeline_mode=batch_databento/…/ticks.parquet` with `Manifest updated`. STILL `- [ ]` for a DIFFERENT
      reason than before. **FINAL 2026-07-20 state: a trading-day execution now reaches `exit(0)` AND writes rows —
      `…-nbbkx`, date=2026-07-17, `exit(0)` + 288,958 rows / 590 shards / 4 venues (NYSE 241,821 across 522 partitions,
      CME 2,391, + NASDAQ/CBOE), `Manifest updated`.** Still `- [ ]` because that run required `--force` and the
      **scheduled** invocation does not pass it: the nightly cron takes the un-forced path, which now dies in
      `check_shard_freshness` with `TypeError: '<' not supported between instances of 'str' and 'int'` because all
      5,208,844 rows of the tradfi availability index carry a STRING `schema_version` (new P0 todo above). 3/7 venues
      (ICE/FX/KRX) also still fail on `No module named 'yfinance'`. So the job is PROVEN CAPABLE but not yet
      operationally green. Tick once the un-forced nightly path exits 0 with all 7 venues attempted — i.e. after the
      `schema_version` P0 and the yfinance P1 land.** **RESOLVED — RE-VERIFIED LIVE 2026-07-25.** Queried the job's
      execution history directly
      (`gcloud run jobs executions list --job=uts-prod-market-tick-data-service-tradfi-databento-t1-recon --region=asia-northeast1 --project=central-element-323112`):
      the un-forced SCHEDULED nightly invocation (`35 0 * * *` cron) has completed `SUCCEEDED_COUNT=1` for 4 consecutive
      nights (2026-07-21, 07-22, 07-23, 07-24) plus one in-flight at query time (07-25). Read the full Cloud Logging
      output for the 2026-07-24T00:35Z execution (`uts-prod-market-tick-data-service-tradfi-databento-t1-recoqwggf`):
      execution condition `'Execution completed successfully in 19m34.6s.'` (genuine exit 0); pre-flight correctly
      attempted every venue needing processing (`Pre-flight: 4/7 venues have captured shards for date=2026-07-23`, the
      other 3 correctly skipped as already-fully-covered — proving the un-forced SKIP path works too, not just force);
      real parquet rows written + manifest updates for ICE (1 row), FX (11 rows across 11 spot pairs), and KRX (equity
      `ohlcv_24h`, confirming the yfinance fix holds in production). The `schema_version` and yfinance blockers cited
      above are independently confirmed fixed elsewhere in this doc and hold live across 4+ consecutive days — the job
      is operationally green, not just proven-capable.
- [x] [INFRA] P0. **MTDS image ships a stale unified-api-contracts — ALL MTDS Cloud Run jobs fail at import**
      (`issues/mtds_image_uac_dep_skew_breaks_all_cloud_run_jobs_2026_07_20.md`). **RESOLVED 2026-07-20 —
      market-tick-data-service@21733255 + `Evidence: cloudbuild=316b0733-42e8-4b8e-82ab-4ad8f1695a84` SUCCESS (all 14
      steps, built from the COMMITTED LDR source so the fix is proven reproducible from the branch).** Root cause was
      NOT the MTDS build staging a stale UAC — it staged NONE. `Dockerfile:115` is
      `FROM unified-trading-library@${BASE_IMAGE_DIGEST}` and the UTL BASE IMAGE bakes
      `/app/.deps/unified-api-contracts` (UTL `cloudbuild.yaml:92` `clone-uac-source`), so UAC/UTL were frozen at the
      base image's build instant, and a UAC-only commit never triggers a UTL rebuild — which is why hand-bumping
      `BASE_IMAGE_DIGEST` (done ~9× per the Dockerfile header, incl. the identical 2026-07-16
      `venue_data_type_has_batch_source` outage) never actually fixed it. Fixed at the root: new `stage-workspace-deps`
      cloudbuild step clones UAC+UTL at LDR tip; Dockerfile installs them over the base copies (UTL first, UAC last,
      before the SCM-version ENV). **Durable guard**: new REQUIRED `image-import-smoke` step gating `push` imports
      `market_tick_data_service.__main__` in the built image — it also exposed that the "REQUIRED" in-image
      `quality-gates` step was a **silent no-op on every build** (`quality-gates.sh:141-145` `exit 0` when the PM base
      script is absent), the direct reason a 2-day fleet outage shipped unnoticed. **Tradfi verified live (the in-lane
      criterion): execution `…-nbbkx` `exit(0)` + 288,958 rows / 590 shards / 4 venues** for date=2026-07-17 (NYSE
      241,821 rows across 522 partitions; CME 2,391; + NASDAQ/CBOE), `Manifest updated`. Per the operator scope
      correction, `cefi-t1-recon` was deliberately NOT run (Tardis hard cap 1 — a full CeFi backfill VM held the
      single-IP budget; forcing it risks the measured 37,212-false-row manifest corruption) and non-tradfi verification
      is left to the owning workstreams; `fast-t1-recon` had been run once BEFORE that correction and incidentally came
      back exit 0 + 969,536 rows / 2,494 shards. (repos: market-tick-data-service, unified-api-contracts,
      deployment-service)
- [x] ✅ [INFRA] P1. **`yfinance` missing from the MTDS image** — RESOLVED `mtds@d8dc04e1` (Dockerfile pinned
      `yfinance==0.2.66` install after `-e . --no-deps` + image-import-smoke extended to `import yfinance`; Evidence:
      `cloudbuild=ce814d53-1648-4cf4-b2dc-7ac6bffefecd` SUCCESS, in-image smoke printed `YFINANCE OK 0.2.66`; issue doc
      status:resolved). (repos: market-tick-data-service)
- [x] ✅ [BACKEND] P0. **tradfi availability index `schema_version` typed as STRING** — RESOLVED `mtds@ac051bfe`
      (restamp writer now stamps int `MANIFEST_SCHEMA_VERSION` + regression test, QG-green) + live `_index` re-stamped
      int64 (held across consolidator merge, `384f0345a`) + verified un-forced (`_apply_freshness_skip(_force=False)`
      returns PARTIAL verdicts, not `TypeError`); P2 consolidator `TRY_CAST` hardening
      `unified-trading-library@02fc4661`; issue doc status:resolved. (repos: market-tick-data-service,
      unified-trading-library, instruments-service)
- [x] ✅ [INFRA] P1. **`tradfi-databento-t1-recon` SIGKILLs (signal 9) at 2cpu/8Gi on a real trading day, AFTER writing
      rows — RE-VERIFIED LIVE 2026-07-25, NOT REPRODUCING.** Both 2026-07-20 trading-day executions wrote parquet +
      manifest, then idled cpu≈0% / rss≈5,475 MiB for ~2 min and were killed — data lands but the job self-reported
      FAILED every trading day at the time. **Checked the full execution history for the 5 consecutive trading-day runs
      since (2026-07-21 through 2026-07-25, `gcloud run jobs executions list`): every one shows `SUCCEEDED_COUNT=1`,
      `FAILED_COUNT` empty (0), genuine `'Execution completed successfully'` completion conditions (e.g. the 2026-07-25
      run: `46m28.5s`, no SIGKILL).** Resource allocation is unchanged (still 2cpu/8Gi) — the fix was NOT a resource
      right-sizing; the SIGKILL appears to have been a transient/date-specific condition (2026-07-20 specifically)
      rather than a standing defect, likely resolved as a side effect of one of the many other tradfi fixes shipped
      2026-07-21 through 2026-07-25 (writer canonicalization, manifest CAS stability, etc.) rather than a targeted fix
      for this exact symptom. **No further action taken** — re-diagnosing a non-reproducing issue from re-reading old
      2026-07-20 logs was judged lower value than the confirmed-clean 5-day live re-verification; if it recurs, the
      original diagnosis hint (honest-absence re-emit / per-VM shard fallback after
      `consolidated blob age > 120s threshold`) remains the starting point. (repos: market-tick-data-service,
      deployment-service)
- ~~[BACKEND] P1. **Massive dual-source shape parity + consolidator dedup-key omits `source`**
  (`tradfi_massive_dual_source_2026_05_28.md` Phase 4b — a silent last-write-wins loss risk the moment a cell goes
  dual-source).~~ **MOOT 2026-07-21** — Massive was removed as a tradfi source 2026-07-19 (`--source` now
  `choices=["databento"]`; a `source='massive'` write raises — L226-229) and fully PURGED at tick 26 (`batch_massive` →
  0, 1,701,422 objects, 0 collateral — L1530-1536), under operator Option-C accepted-permanent- loss with the
  subscription terminated. No tradfi cell can ever go Massive-dual-source, so shape-parity and the consolidator
  dedup-key-omits-source loss risk are dead work. (repos: unified-trading-library, market-tick-data-service)

#### A3.1 — Databento e2e throughput optimization (operator 2026-07-18: "optimize like cefi/tardis — large VM doing MORE not wasting; MEASURE the full e2e chain: download + processing + upload + disk-write")

> Two research agents mapped (a) the full CeFi/Tardis throughput playbook (20 hacks: disk, SINGLE_VM_QUEUE bundling,
> TARDIS_MAX_CONCURRENT semaphores, dedicated executors, DataFrame-native finalise, the date-serial barrier, rotation,
> stall-regex, 429-retry, machine-sizing) and (b) the Databento current-state + exact change surface. **Key facts:**
> Databento limits are **per-IP not per-key** (100 concurrent conn / 100 req/s timeseries × 0.8 target-util ≈ **80
> effective**). Current tradfi path = **one VM per (venue,root,year)** (~350+ VMs for a full CME backfill), each doing
> ONE root over a **sequential subprocess-per-7day-chunk** loop, with the shared orchestrator processing dates
> **serially** → each VM uses ~1 of the 80 budget. The concurrency axis for tradfi ohlcv is **DATES** (one
> server-batched `download_batch(symbols=[...])` per date). Disk (pd-balanced 250GB) + dedicated executor are already
> done.

- [x] ✅ [BACKEND] P0. **Gated concurrent-date driver (UTL — the saturation lever) — SHIPPED utl@7b4ed95d.**
      `service_framework/_adapter.py` `run()` now dispatches on `--batch-date-concurrency` (ServiceCLI arg, default
      **1** = `_drive_serial`, a byte-identical extraction of the old loop). When >1, `_drive_concurrent` runs up to N
      dates in flight via a semaphore acquired-before-task / released-on-completion (bounded, lazy pull — no
      task-per-date explosion), all funnelling through the **process-global Databento semaphore** (≤80).
      Determinism-safe (each date independent, own partition); regression test proves concurrent==serial results+counts
      incl a failing date + bounded in-flight. Default-off ⇒ zero change for CeFi/sports/defi. **Both MTDS and IS get
      the flag for free** (both use ServiceCLI `add_date_args`). (repo: unified-trading-library)
- [x] ✅ [BACKEND] P0. **Concurrency knob plumbing (metadata → env → CLI) — SHIPPED dep@ac5d166 + utl@7b4ed95d.**
      `setup-data-pipeline-vm.sh` reads `DATABENTO_MAX_CONCURRENT_REQUESTS` + `DATABENTO_RATE_LIMIT_TARGET_UTILIZATION`
      (metadata→env, mirrors the TARDIS_* block) + appends `--batch-date-concurrency $VM_BATCH_DATE_CONCURRENCY` to the
      mtds-backfill BASE_CLI when set; `launch-mtds-backfill-vm.sh` (+`_tradfi-ohlcv-launcher-lib.sh`) stamp the
      metadata (opt-in/default-off). CLI flag itself is free via ServiceCLI (no per-CLI change needed — the driver ship
      provides it to MTDS **and** IS). (repos: deployment-service, market-tick-data-service, instruments-service)
- [x] ✅ [INFRA] P2. **CLOSED 2026-07-27 (na-eligibility-audit) — ~~Collapse `mtds_chunk_loop.sh`~~ SUPERSEDED by a
      safer refinement (2026-07-18), nothing left to dispatch.** The 7-day chunk is a **deliberate** per-IP-429/
      memory-bound safety (`setup-data-pipeline-vm.sh:~L1276` comment), so collapsing it is risky. The shipped path
      instead adds date-concurrency **within** each chunk via `--batch-date-concurrency` (each request is still a 1-day
      span, just more in flight, bounded by the Databento semaphore) + tunes chunk width via `--chunk-size`. The
      remaining "full single-process collapse" is explicitly conditional ("optional future work IF measurement shows
      chunk cold-start is a material fraction") — a stretch marker, not a committed open task; closing rather than
      leaving it open indefinitely. Re-open as a fresh, precisely-scoped todo if that measurement ever actually shows
      the condition. (repo: deployment-service)
- [x] ✅ [INFRA] P0. **Equity OHLCV launchers re-sharded by (ticker-group × year) — SHIPPED
      deployment-service@d85d06e.** Equity — not CME — was the binding constraint on the tradfi MVP backfill ETA:
      `launch-tradfi-bf-{nasdaq,nyse}` created ONE VM PER YEAR carrying ALL ~622 tickers, so 207,856 equity cells (46%
      of remaining work) compressed onto ~4 year-shards/venue and the longest NASDAQ VM carried ~30,106 cells = a
      12.5–33 hr critical path (CME by contrast shards 47 roots × 7 years and is embarrassingly parallel). New
      `ohlcv_split_ticker_groups` splits the sorted universe into N contiguous equal-sized groups (`--ticker-groups`,
      default 5) → **NASDAQ 622 tickers → 5×4 = 20 VMs; NYSE 581 → 5×4 = 20 VMs; 40 equity VMs total** (was 8). Critical
      path **12.5–33 hr → ~2.5–6.6 hr (÷5)**. Verified by dry-run on both launchers + a partition proof (no ticker
      lost/duplicated at N=1,3,5,7,10,622, 700; group sizes differ by ≤1; over-request clamps to one-ticker groups).
      More VMs is SAFE here and is NOT the Tardis case: Databento's 100-conn/100-rps limits are **per-IP**, and
      `ohlcv_create_vm` gives every VM its own ephemeral external IP (no `--no-address`/NAT), so the budget is PER VM —
      adding VMs adds budget rather than dividing one. SPOT default, `--batch-date-concurrency` (dep@4eb50a4) and
      PROGRESS.json monotonic resume all preserved. **No separate `-1s` launcher exists or is needed** — the `-1m`
      wrappers already fetch BOTH data types (`TRADFI_OHLCV_DATA_TYPES` defaults to `ohlcv_1m;ohlcv_1s`), so the
      re-shard covers the 1s leg automatically. (repo: deployment-service)
- [x] ✅ [INFRA] P1. **`OHLCV_FLEET_CONCURRENCY_CAP` 20 → 60 — SHIPPED deployment-service@d85d06e.** The cap is a
      COURTESY limit, not a safety one (per-IP budget, see above); at 20 it would have refused the second equity venue
      mid-rollout now that the fan-out is ~40 equity VMs. 60 leaves headroom for a concurrent CME/ICE/CFE wave.
      Rationale comment now states explicitly that Tardis cap-1 reasoning does NOT transfer. (repo: deployment-service)
- [x] ✅ [INFRA] P1. **`STALL_PROGRESS_REGEX` set on the tradfi launchers — SHIPPED deployment-service@d85d06e.** TradFi
      was the last family still on the weak log-not-grown fallback (cefi/mdps/sfi/gas-fees all set it), which the
      `PIPELINE_HEARTBEAT` emitter defeats forever — a cefi VM hung 7+ days undetected exactly this way
      (cefi_bf_2021_heavy_vm_stalled_2026_07_12). Markers verified EMPIRICALLY against a real run.log
      (`tradfi-bf-nasdaq-ohlcv-1m-2024-20260719-112444`): `uploaded|streamed` — per-shard StreamingParquetWriter
      finalize + per-chunk DatabentoAdapter fetch. Both needed: `uploaded` alone false-trips during a long fetch phase
      on a heavy CME expiry date. (repo: deployment-service)
- [x] ✅ [BACKEND] P0. **A–C `attempted_failed` truncation ROOT-CAUSED + FIXED — SHIPPED
      unified-api-contracts@6cc7b547 + market-tick-data-service@05f0ab17.** 56 NASDAQ + 50 NYSE instruments carried ~770
      `attempted_failed` days each, all `WithinBoundsTradfiSourceZero`, clustered alphabetically A–C. NOT vendor absence
      — a **silent truncation**: `get_expected_instruments_for_venue` applied `resolved = resolved[:cap]`
      (`market_data_categories.py`) to the caller-supplied `--instrument-ids` list, and since the launchers pass
      `sorted()` tickers with the MVP `_DEFAULT_PER_INSTRUMENT_SENTINEL_CAP = 50` (`preflight.py:236`), the Tier-3
      denominator was cut to a pure alphabetical prefix `A..BKNG`. **Production proof**: the 2026-07-19 NASDAQ VM
      run.log logs `Tier-3 …: expected_instruments=50 captured=58` — a denominator SMALLER than its own numerator.
      Implicated tickers are mega-cap (AAPL, AMZN, AMD, AVGO, BAC, BRK.B, C, CAT, ABBV, BKNG), which refutes genuine
      absence outright. Fix: new `explicit_scope` flag — a caller-NAMED scope is never capped (the cap remains a real
      guard-rail for an unbounded DISCOVERED universe); MTDS passes `explicit_scope=bool(instrument_ids)`. This is NOT a
      sentinel tier promotion (those stay operator-gated per `/codex/02-data/per-instrument-sentinel-rollout.md` §3) —
      it only stops the cap applying where it never bounded anything. Regression tests in BOTH repos assert an explicit
      scope survives whole and that tail-of-alphabet instruments are present. **A blind backfill re-run would have
      re-failed on exactly these instruments.** (repos: unified-api-contracts, market-tick-data-service)
- [x] ✅ [DATA] P1. **Retire the 104,623 residual phantom `attempted_failed` rows — market-tick-data-service@ccbac784
      (PR #712, `worktree-wf_9dc68885-289-4` → `live-defi-rollout`).** The live emitter was already fixed for
      NASDAQ/NYSE (`sentinels.py` → `EXPECTED_SOURCE_DELIVERY_LAG`, operator BLK-d385496b answer B, 2026-06-28); the
      surviving rows are historical residue written by a single CF-11 rebuild run on 2026-07-07 06:39–07:29 UTC
      (`_rebuild_tradfi_cf11.py` `_handle_srz_tradfi_row` reclassifies any SRZ on a trading day to `attempted_failed`,
      converting a correct cross-venue absence — a NYSE-listed ticker on a NASDAQ run — into a phantom failure). They
      also use the BARE `instrument_id` (`AAPL`) vs the canonical `NASDAQ:EQUITY:AAPL-USD` the current enumerator
      writes, so they double-count the denominator. Shipped `scripts/retire_tradfi_cf11_phantom_srz_2026_07_25.py` + 16
      regression tests: routes cross-venue absence to `EXPECTED_INSTRUMENT_NOT_LISTED`, same-venue delivery-lag gaps to
      `EXPECTED_SOURCE_DELIVERY_LAG` (matching the live-emitter fix, never a false "not listed" claim for a ticker that
      trades there), and drops a bare row whose canonical-id counterpart already exists; instrument type (EQUITY/ETF)
      resolved via a 9-day instruments-service catalogue sample (SPOT_PAIR excluded as known contamination), 100%
      resolution/0 conflicts measured. **Live evidence**: a 2026-07-25 02:44 UTC read found 104,338 matching rows
      (matches this bullet's ~104,623 within normal live-manifest drift); before this tool's own `--apply` could run,
      two independent fresh re-reads (~03:00/~03:03 UTC, distinct GCS object generations confirming genuine intervening
      writes — not a caching artifact) found the NASDAQ/NYSE population already at 0, while the CME/CBOE/FX population
      (a different, out-of-scope defect — futures/options per-contract codes) stayed unchanged at 202,172, i.e.
      venue-selective precision matching this exact defect scope, not a generic rebuild. Could not identify the specific
      external actor; the tool ships regardless as the durable, tested, git-tracked fix design and a safe (idempotent,
      0-candidate no-op) re-run path. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. **70% of `captured` cells carry `row_count` = 0/null — RE-MEASURED LIVE 2026-07-25 as instructed
      ("re-measure on a quiesced bucket first").** →
      `plans/active/issues/tradfi_captured_cells_zero_or_null_row_count_2026_07_20.md` (P1). **New live numbers: 310,591
      of 1,421,463 captured cells (21.9%)** — a large real improvement from the originally-snapshotted 70.3%
      (1,135,339/1,615,859), most likely a downstream effect of this session's migrations changing which rows exist
      /count as captured (phantom-retirement alone dropped 75,252 rows + re-keyed 29,086 others) rather than any direct
      row_count fix — no script this session touched `row_count` itself. **The FX `ohlcv_24h` slice is UNCHANGED and
      still the clearest evidence of a real writer bug, not just a stale-denominator artifact: 4,266 of 4,313 captured
      FX `ohlcv_24h` cells (98.9%) are STILL zero, essentially identical to the original 4,266/4,266 finding** — this
      specific (venue, data_type) writer path has never actually stamped `row_count`, unrelated to anything migrated
      this session. Original disposition question stands unresolved: is `row_count` not stamped at the shard atom
      (coverage numbers lie) or is this the banned "empty rows that look populated" honest-absence violation? Needs a
      code-level look at the FX Yahoo-daily writer path specifically (not a data migration — a writer-code fix) as the
      concrete next step; the broader 21.9% residual across other venues/types may resolve further once the chain-bundle
      content migration (item above) actually applies at scale. (repo: mtds)
- [x] ✅ [DATA] P2. **DONE 2026-07-28 (slot-2) — same ground as `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s
      todo, resolved there in full.** →
      `plans/archive/issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` (now `status: resolved`, all 5
      todos done). Ran the corrective `--apply` reclassification: 182,407 below-floor cells (NASDAQ/NYSE/CME) flipped
      `expected_unattempted`(blank)→`empty_confirmed(EXPECTED_PRE_SOURCE_COVERAGE_START)`, writer-side, verified
      420,438→238,031 todo cells (exact delta), 0 below-floor cells remaining on re-check. The original candidate's
      `sentinels.py` target was already corrected (2026-07-25, plan-reconcile) to the actual gap:
      `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_tradfi` (write-time fix already shipped
      `instruments-service@31cf3952`) + the one-off reclassification script
      `scripts/reclassify_tradfi_below_floor_expected_unattempted_2026_07_27.py` (this session's `--apply` run) — not
      `mtds`. Regression-guard test `instruments-service@5104befc`. (repo: instruments-service, not mtds — corrected per
      the above)
- [x] ✅ [INFRA] P1. **Bundle roots into fewer larger VMs — SHIPPED `deployment-service@60b9d37`** (2026-07-30, via
      `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s "Bundle CME roots into fewer larger
      VMs" todo, which extracted this exact item verbatim per the NOTE below). `_tradfi-ohlcv-launcher-lib.sh` spawned
      one VM per (venue,root,year); added `ohlcv_split_root_groups` (the SINGLE_VM_QUEUE-analog) + an
      `OHLCV_ROOT_GROUPS`/`--root-groups` knob (default 10) that accumulates multiple roots' symbol-sets into one VM's
      `VM_INSTRUMENT_IDS` per year-shard. `launch-tradfi-bf-cme-ohlcv-1m.sh` now loops (root-group x year-shard) —
      default groups collapse 406 VMs (58 roots x 7 years) to 70. Dry-run verified no root/symbol lost or duplicated
      across the bundled groups. The pd-balanced 250GB `TRADFI_OHLCV_BOOT_TYPE` disk default was already committed +
      wired into `ohlcv_create_vm` (`ac5d1660`, 2026-07-18) — the CME launcher already calls it, so no separate disk
      change was needed (this item's "staged locally... never wired" framing was stale). (repo: deployment-service)
      **NOTE (na-eligibility-audit 2026-07-30, tradfi tranche)**: this exact item was extracted VERBATIM as
      `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s "Bundle CME roots into fewer larger
      VMs" todo (which cites this doc's own then-still-open item as its source, via
      `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s 2026-07-30 Deferred
      re-check). batch5 was activated 2026-07-30 (`5a6bbefc3`) and its todo dispatched + shipped as above.
- [x] ✅ [BACKEND] P1. **Real retry-on-429 in the Databento fetch path — SHIPPED mtds@73c286a2 (`databento_retry.py`).**
      The fetch previously recorded ANY exception (incl. `RATE_LIMIT`/429) as a per-schema shard failure with no retry
      (config `max_retries`/`backoff_factor` were log-only). Now `fetch_timeseries_range_with_retry` wraps the
      timeseries fetch in a bounded `backoff_factor*2^attempt` (capped) loop that retries ONLY the transient whitelist
      (429/`RATE_LIMIT`/`SERVER_ERROR`/connection/timeout via the existing `_classify_databento_exception`);
      billing/400/auth/symbology fail FAST on attempt 1 (the 3 billing-gated datasets stay fail-closed by design).
      Unit-tested (retryable retried N× / non-retryable once). (repo: market-tick-data-service)
- [x] ✅ [BACKEND] P1. **TradFi data-pipeline skill documents the concurrency knobs — SHIPPED pm@027dd7e10.**
      `data-pipeline-check-mtds/SKILL.md` §3c gained a note on `--batch-date-concurrency` +
      `DATABENTO_MAX_CONCURRENT_REQUESTS` (opt-in/default-off, per-IP ~80 effective, dates are the concurrency axis)
      pointing at the RX-counter e2e measurement method. (repo: unified-trading-pm)
- [x] ✅ [DATA] P0. **MEASURED the full e2e chain before/after on REAL Databento VMs (operator acceptance bar) —
      concurrency = 1.56x on a realistic large-VM workload, "doing more not wasting" confirmed.** Two runs, CME
      ohlcv_1m, --test-run, fetch/write wall-clock from persisted run.logs: - **run-2 (the clean isolation: 16 vCPU
      e2-highmem-16, 6 heavy roots ES;NQ;CL;GC;ZN;6E, Jan-2024, pd-balanced, conc=1 vs conc=20)**: serial **27.3 min**
      vs concurrent **17.5 min** for the same 820,639 rows = **1.56x**. Mechanism is measured directly: serial CPU is
      idle **18/56** samples (~32% of the time WAITING on the Databento fetch = wasting), concurrent CPU idle **0/36**
      (fully saturated) — the date-fanout overlaps one date's fetch latency with another's parse/write, exactly the
      operator's "large VM doing MORE not wasting." - **run-1 (small: 4 vCPU, 1 root ES, 30d)**: only ~4% +
      pd-standard≈pd-balanced — because ohlcv_1m's download is a tiny 0.65 GB burst, the bottleneck is per-date
      processing overhead (freshness/manifest × dates) not download/disk, and 20-way concurrency was CPU-bound on 4
      vCPU. **The win scales with workload size + vCPU** (run-1→run-2). - **Full picture**: disk pd-balanced = 4.7x on
      write-heavy download-bound data (cefi Tardis, peer-measured), ~neutral on small ohlcv_1m; dedicated executor
      prevents the ~350x DNS-starvation collapse; date-fanout = 1.56x on a large VM; retry-on-429 = reliability at
      concurrency. **Follow-up (the real ohlcv_1m lever): batch the per-date freshness/manifest ops** — that overhead,
      not download, dominates small-candle e2e. (repo: deployment-service)

### Follow-ups surfaced by the tick-26 throughput re-analysis (promoted from Progress Log prose, 2026-07-24 hygiene pass)

> These 3 were open `- [ ]` checkboxes sitting inline in the Progress Log narrative below (not in the todo list where
> PLAN_FORMAT.md's structural-order rule expects them) — moved here verbatim, unedited, as part of this split.

- [x] ✅ [INFRA] P1. **Re-shard equity OHLCV by DATE-RANGE instead of ticker-group — SHIPPED
      deployment-service@872ac2f.** Replaced `ohlcv_split_ticker_groups` fan-out with a new `ohlcv_split_date_slices` (N
      contiguous DATE-range slices per year-shard, all tickers per VM) in `_tradfi-ohlcv-launcher-lib.sh`, wired into
      both `launch-tradfi-bf-{nasdaq,nyse}-ohlcv-1m.sh` as the new default (`OHLCV_SHARD_MODE=date-range`,
      `--date-slices N`, default 5/year-shard). The legacy ticker-group path stays reachable via
      `--shard-mode ticker-group` for the pathological single-VM-memory-ceiling case. Dry-run verified both launchers:
      NASDAQ/NYSE each produce 20 date-range VMs across the 4 year-shards (2023-04-15..today), all tickers per VM, with
      no calendar day lost or duplicated (unit-verified the slicer's day accounting plus a full-window dry-run trace).
      Quality-gates green in deployment-service. (repo: deployment-service)
- [x] ✅ [INFRA] P1. **Raise `OHLCV_FLEET_CONCURRENCY_CAP` 60 → 150 and default `TRADFI_OHLCV_MACHINE=e2-highmem-16`.**
      The corrected ETA is THROUGHPUT-bound (~999 VM-h against a cap of 60), not critical-path-bound, so the cap is the
      single highest-leverage knob: 60 → 150 takes expected ~22 h → ~9 h. Safe for the same reason `d85d06e` gave for 20
      → 60 (Databento limits are per-IP and every VM gets its own ephemeral IP). Shipped `deployment-service@545ff76`:
      `_tradfi-ohlcv-launcher-lib.sh:35` `TRADFI_OHLCV_MACHINE` default `e2-highmem-4` → `e2-highmem-16`,
      `_tradfi-ohlcv-launcher-lib.sh:172` `OHLCV_FLEET_CONCURRENCY_CAP` default `60` → `150`, both verified present at
      their call sites (`bash -n` clean). (repo: deployment-service)
- [x] ✅ [DATA] P2. **Re-measure CME per-root-date cost — 4 of 6 named roots measured (ES, NQ, GC, PL); 6E and CT have
      NO run.log at all (never launched) — honestly reported, not fabricated.** Read the existing
      `vm-logs/tradfi-bf-cme-ohlcv-1m-<root>-2025-*/run.log` for each root's clean (`rc=0`, all 53 weekly chunks
      complete) 2025 full-year run, computing wall-clock (first heartbeat → last `chunk=53/53` PROGRESS line) / 365
      calendar days: **ES 2.972 min/date** (14,313,572 rows, 13,197 rows/min) · **NQ 2.693 min/date** (13,827,457 rows,
      14,068 rows/min) · **GC 2.725 min/date** (12,128,848 rows, 12,192 rows/min) · **PL 1.454 min/date** (2,801,597
      rows, 5,279 rows/min). **This widens the heavy end of the spread**: ES/NQ/GC (2.69–2.97 min/date) are now the
      heaviest measured CME roots — heavier than the prior sole heavy anchor CL (2.59 min/date) — while PL sits between
      CL and the light anchor SI (0.10 min/date). The heavy/light spread across all 6 measured/anchor points is now
      ~~30× (2.97 vs 0.10), slightly wider than the original 26× (2.59 vs 0.10) estimate, so the 15–30 h ETA band's
      upper bound should be read as marginally under-, not over-, estimated. **6E and CT recommendation**: no
      `vm-logs/tradfi-bf-cme-ohlcv-1m-{6e,ct}-*` prefix exists in `gs://deployment-scripts-central-element-323112/` at
      all — these 2 roots have never been launched, so "read existing logs, no new VM launch" cannot produce a
      measurement for them; if tighter (~~±15%) ETA precision is wanted, launching just those 2 roots (or reading their
      logs once any other in-flight CME wave reaches them) would close the remaining gap. (repo: unified-trading-pm)

## Codex SSOTs (read before touching this workstream)

`/codex/05-infrastructure/vm-launcher-runbook.md`, `/codex/05-infrastructure/spot-vms-for-backfill.md`,
`/codex/02-data/tradfi-databento-sourcing-ssot.md`. Full SSOT + aggregated-source-doc list lives on the parent,
`tradfi_consolidated_closeout_2026_07_18.md` (not duplicated here).

## Progress Log

- **na-eligibility-audit 2026-07-27**: KEEP-NA, stale items — closed 1 (`mtds_chunk_loop.sh` collapse, superseded); 2
  items (date-range re-shard, CME re-measure) confirmed already claimed via
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`, noted inline, not reclassified (would duplicate live dispatched
  work). Remaining open items are genuinely NA (bundle-into-fewer-VMs design call, vendor-discovery-floor
  reclassification, OOM/consolidator monitor cross-doc tracking).
- **tradfi_satellite_ao_dispatch_batch2-003, 2026-07-27**: the date-range re-shard + CME re-measure items claimed above
  landed. **Date-range re-shard**: `deployment-service@872ac2f` — `ohlcv_split_date_slices` replaces
  `ohlcv_split_ticker_groups` as the default equity shard axis (NASDAQ/NYSE), legacy ticker-group kept behind
  `--shard-mode ticker-group`; dry-run-verified 20 date-range VMs/venue across the 4 year-shards, no day lost/dup. **CME
  re-measure**: read `vm-logs/tradfi-bf-cme-ohlcv-1m-{es,nq,gc,pl}-2025-*/run.log` (clean rc=0 full-year runs) — ES
  2.972 / NQ 2.693 / GC 2.725 / PL 1.454 min/date, all from real Databento row counts / wall-clock, no fabrication. 6E
  and CT have **zero** `vm-logs/tradfi-bf-cme-ohlcv-1m-{6e,ct}-*` objects in the bucket — never launched — so they could
  not be measured from existing logs per the todo's own "no new VM launch" constraint; recommendation filed above
  (launch just those 2, or wait for their next in-flight wave, to close the last gap). **Net ETA-band read**: the heavy
  end of the CME spread is measured WORSE than the prior CL-only anchor (ES/NQ/GC all exceed CL's 2.59 min/date), so the
  15–30h band's upper bound should not be revised down on this data — if anything the 26× spread widened to ~30×. Also
  fixed the stale SSOT header comment in `launch-tradfi-bf-cme-ohlcv-1m.sh` + the shared lib (cited the archived
  `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`; now points at this doc). quality-gates.sh green in deployment-service.
  Both checkboxes above flipped in the same commit as this entry per the todo's own Done-when.

- **na-eligibility-audit 2026-08-07** (tradfi tranche): **KEEP-NA-STALE (already-duplicated) -- re-verified,
  unchanged.** Sole open todo (the OOM rc137 cross-link) re-read end-to-end; count reconciled (1/1). Its two remaining
  legs are still genuinely open in their own owning docs -- verified live:
  `tradfi_backfill_oom_remediation_2026_06_24.md` is `status: open` (1 open todo) and
  `consolidator_throughput_backlog_monitor_2026_07_09.md` is `status: active` (3 open todos). This doc's checkbox
  correctly stays open as a cross-link, not independent work; nothing to reclassify.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA-STALE-DUPLICATED, confirmed --
  re-verified, 2 minor citation refinements applied (see the checkbox note above).** Sole open todo re-read end-to-end;
  count reconciled (1/1). Live-confirmed both cross-linked targets: `tradfi_backfill_oom_remediation_2026_06_24.md` is
  now `assigned_vm: planning` (already actively AO-dispatched, not merely "still open");
  `consolidator_throughput_backlog_monitor_2026_07_09.md`'s open-todo count drifted 3->2 since 08-07 (one item closed by
  a concurrent `[ui]`-tranche audit pass). Neither changes the umbrella-pointer verdict -- this doc's checkbox has no
  independent worker-determinable content of its own. Nothing to reclassify.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA-STALE-DUPLICATED, re-confirmed,
  citation refreshed (see checkbox note above).** Sole open todo re-read end-to-end. `tradfi_backfill_oom_remediation_2026_06_24.md`
  now measures 0 open todos (not yet archived by its owner); `consolidator_throughput_backlog_monitor_2026_07_09.md`
  still has 2 open todos, unchanged. Checkbox correctly stays open as an umbrella pointer. `assigned_vm` unchanged.

> **Moved verbatim from the parent's Progress Log (2026-07-24 line-cap split)** — this is the download/backfill-
> throughput slice of the parent's single continuous autonomous-session narrative (ticks 14, 16, 22, the tick-26 ETA
> re-analysis, the P0 T+1-job restore + P1 yfinance disposition, the Backfill-drive section, and the Databento-free-
> entitlement nice-to-have). The manifest/content migration slice and the Phase-D testing slice were forked to the
> sibling plans instead — see their own Progress Logs for that content. Nothing below is summarized or rewritten; it is
> the original text, relocated.

- **2026-07-18 (slot-1, tick 14) — operator pivot to Databento e2e throughput optimization; disk fix; research.**
  Operator asked (mid-session) to (1) fix the backfill-VM boot disk (cefi write-slowdown), (2) port the full CeFi/Tardis
  throughput playbook to Databento ("large VM doing MORE not wasting"), (3) make the tradfi data-pipeline skill + MTDS
  and IS CLIs accept the concurrency config, and (4) MEASURE the full e2e chain (download+processing+upload+disk) like
  cefi did. New A3.1 section captures the design.
  - **Disk fix**: confirmed live the tradfi/mtds backfill VMs ran `pd-standard` 50GB (GCP default when
    `--boot-disk-type` omitted). A peer independently shipped the identical fix + a QG gate
    (`check_tardis_vm_disk_provisioning.py` → generalized to `check_backfill_vm_disk_provisioning.py`:
    Tardis/Databento/`*backfill*`/`*forward-poll*` launchers must be non-pd-standard ≥250GB; measured cefi 2.36→11.1
    MB/s = 4.7x) and fleet-swept ~57 launchers. Resolved the resulting merge conflicts (took peer's canonical version
    for the shared launchers). My **net-new** contribution: the pd-balanced 250GB default on
    `_tradfi-ohlcv-launcher-lib.sh` (the tradfi OHLCV MVP launcher — a gate blind-spot, lib-sourced so the gate's
    inline-`--boot-disk-size` glob skips it) — folding into the A3.1 lib rewrite. Dropped a redundant `lc_gcloud_create`
    wrapper edit (peer's active disk-policy workstream; the ~80-wrapper-user blind-spot flagged for them).
  - **Research (2 agents)**: full CeFi playbook (20 hacks) + Databento current-state/change-surface — see the A3.1
    header. Databento per-IP ~80 effective; tradfi = one-VM-per-(venue,root,year) with serial dates → ~1/80 utilized.
    Databento dedicated executor + disk already done; the lever is date-concurrency (gated UTL driver) + plumbing +
    chunk-loop collapse + 429-retry, then a measured before/after.
  - **In flight**: gated concurrent-date driver (UTL `_adapter.py`, default off, determinism-tested) being implemented.
    Killed the stale one-VM-per-shard Phase-D check (pre-`_TRADFI_MVP_SHARDS` code, exit 144) — Phase D re-runs on the
    optimized bundled path.

- **2026-07-18 (slot-1, tick 16) — A3.1 Databento optimization SHIPPED + MEASURED (1.56x) + a P0 fleet incident fixed.**
  - **Shipped**: gated concurrent-date driver `utl@7b4ed95d` (byte-identical serial default; `_drive_concurrent`
    bounded-in-flight fan-out; determinism-tested; MTDS+IS get `--batch-date-concurrency` free via ServiceCLI);
    concurrency plumbing + tradfi-ohlcv pd-balanced `dep@ac5d166`; MTDS retry-on-429 (`databento_retry.py`,
    billing-fail-fast) re-shipping; skill knobs `pm@027dd7e10`.
  - **MEASURED (acceptance bar)**: date-fanout = **1.56x** on 16-vCPU / 6-root / conc=20 (27.3→17.5 min, 820,639 rows),
    with serial CPU idle ~32% (fetch-wait) vs concurrent 0% — "large VM doing more, not wasting" confirmed directly.
    ohlcv_1m/1-root/4-vCPU showed only ~4% (download is a tiny burst, per-date overhead dominates, CPU-bound at 4 vCPU)
    — the win scales with workload + vCPU. See the A3.1 MEASURE todo for the full breakdown + the per-date-overhead
    follow-up.
  - **P0 fleet incident (found mid-measurement, fixed, shipped `dep@ac5d166`)**: the pd-balanced disk-policy sweep
    inserted the rationale comment block INSIDE the `\`-continued `gcloud compute instances create` in **88 launchers**,
    silently truncating the command (metadata-less VMs, no backfills; forward-poll launchers eroding live coverage);
    `bash -n`+shellcheck miss it so it passed QG. Diagnosed + fixed all 88 (bash-n clean, 0 remaining) + issue doc
    `launcher_gcloud_continuation_broken_by_disk_sweep_2026_07_18.md` with a QG-gate-gap follow-up.
  - **Next**: Phase D terminal gate on the optimized path (MVP ohlcv_1m + ohlcv_24h); MVP backfills; durability closure.

- **2026-07-20 (slot-1, tick 22) — ✅ MVP BACKFILL READINESS + ETA DELIVERED (operator deliverable); 1 readiness gap
  FIXED; 2 assumptions CORRECTED; 3 findings raised.**
  - **ETA to backfill all remaining tradfi MVP** (measured anchor: 820,639 rows / 17.5 min on 16-vCPU `e2-highmem-16`
    conc=20 ≈ 46.9k rows/min/VM): **optimistic 4–7 h** (equity re-sharded + fleet cap ~40 + all `e2-highmem-16`) ·
    **expected ~13–33 h, centre ~20 h** (launchers as-shipped) · **with SPOT preemption ~26–45 h**. On the DEFAULT
    `e2-highmem-4` multiply ×3–4 → 60–130 h, so **machine size dominates the ETA more than any other choice — launch
    with `TRADFI_OHLCV_MACHINE=e2-highmem-16`.**
  - **READINESS GAP FIXED — `deployment-service@4eb50a4`:** the 1.56× `--batch-date-concurrency` lever existed in UTL
    but was **OFF** for the tradfi launchers (`_tradfi-ohlcv-launcher-lib.sh:88` defaulted empty). Now defaults ON for
    databento-sourced tradfi, machine-derived (~1.25 dates in flight per vCPU, clamped [2,80]): `e2-highmem-4`→5,
    **`e2-highmem-16`→20 (exactly the config the 1.56× was measured on)**, `e2-standard-96`→80. FX/Yahoo untouched.
    SPOT + PROGRESS.json monotonic resume + retry-429 + dedicated Databento executor + OOM sizing all verified OK.
    **Still OPEN:** per-date freshness/manifest op batching is not implemented anywhere (known dominant small-candle
    cost).
  - **CORRECTION 1 — Databento is rate-limited PER-IP, not per-key** (`databento_key_cache.py:152-180`,
    `MAX_CONCURRENT=100`, ~80 effective) and every backfill VM gets its OWN ephemeral external IP (no
    `--no-address`/NAT). The ~80 budget is **per-VM, not fleet-wide** — **structurally UNLIKE the Tardis cap-1 storm**
    (one shared contended IP). `OHLCV_FLEET_CONCURRENCY_CAP=20` is a courtesy cap, not a rate-limit guard; 18 concurrent
    VMs empirically ran with zero 429s. **More VMs is SAFE here.**
  - **CORRECTION 2 — the binding constraint is EQUITY SHARD GRANULARITY, not API concurrency or VM count.**
    `launch-tradfi-bf-{nasdaq,nyse}-ohlcv-1m.sh` create ONE VM PER YEAR covering ALL tickers, so 207,856 equity cells
    (46% of remaining work) compress onto ~4 year-shards/venue → **~30,106 cells on the single longest NASDAQ VM**
    (12.5–33 h critical path). CME shards 47 roots × 7 years (~329 VMs) and is embarrassingly parallel. **Splitting the
    equity launchers by ticker-group is worth MORE than the 1.56× lever** — dispatched. NOTE: this is the OPPOSITE
    direction to the open P1 "bundle roots into fewer larger VMs" (right for CME, wrong for equities).
  - **REMAINING WORK:** 638,440 todo cells, of which **182,407 (29%) are BELOW the vendor discovery floor** (Databento
    XNAS.ITCH/XNYS.PILLAR have no pre-2023-04-15 data; launchers already clamp) → permanently unfillable. **456,033
    genuinely backfillable**: CME ohlcv_1s 168,045 · NASDAQ ohlcv_1m 80,390 · NYSE ohlcv_1m 64,817 · CME ohlcv_1m 60,210
    · NASDAQ ohlcv_1s 40,034 · NYSE ohlcv_1s 22,615 · NASDAQ/NYSE ohlcv_24h 8,968 · KRX ohlcv_24h 8,318 · CBOE 2,489 ·
    FX/KRX 147.
  - **FINDINGS RAISED (issue docs dispatched):** (a) **P1 DATA-CORRECTNESS — 1,135,339 of 1,615,859 `captured` cells
    (70%) carry `row_count` = 0 or null** (CME/NYSE/NASDAQ ohlcv; **ALL 4,266 FX `ohlcv_24h` captured cells are zero**)
    — either `row_count` is not stamped at the per-instrument atom, or these are the banned
    "empty-rows-that-look-populated" honest-absence violation; re-measure post-migration before concluding. (b) P2 —
    reclassify the 182,407 below-floor cells as `expected_unattempted` so dashboards stop showing unchaseable gaps. (c)
    **`attempted_failed` on equities is ALPHABETICALLY CLUSTERED A–C** (56 NASDAQ + 50 NYSE, ~770 failure-days each, all
    `WithinBoundsTradfiSourceZero`) — a **TRUNCATION signature, not data absence**; a blind re-run will re-fail until
    root-caused (dispatched). Minor: tradfi launchers don't set `STALL_PROGRESS_REGEX`.

- **2026-07-20 (slot-1, tick 26) — 🔴 THE tick-22 ETA (~13–33 h expected / 4–7 h re-sharded) IS SUPERSEDED. Corrected:
  15–30 h, expected ~22 h. The NUMBER barely moved; the REASONING was wrong in three places, and the two "levers" the
  old estimate was sold on buy almost nothing.** Manifest snapshot **T1 = 2026-07-20T14:47:40Z**, re-measured at **T2 =
  2026-07-20T15:09:03Z** after the peer force-rebuild landed mid-analysis — **all inventory figures IDENTICAL across
  both** (638,446 todo / 182,407 below-floor / 456,039 backfillable), so the rebuild does not move any conclusion here.
  - **INVALIDATOR 2 DOES NOT APPLY — the tick-22 inventory already used `capture_status`, never `row_count`.** Verified
    by re-running the original derivation (`mvp_gap7.py`): predicate is
    `capture_status ∈ {expected_unattempted, attempted_failed}`. Reproduced 638,446 / 182,407 / **456,039** vs the
    reported 638,440 / 182,407 / 456,033 (delta **+6 cells**, intervening writes). **The 182,407 below-floor figure
    re-verifies EXACTLY.** Separately re-measured the row_count defect on MVP data types: **680,088 of 919,180
    `captured` MVP cells (74.0%) carry `row_count` 0/null** — real, still P1, but it never touched this ETA.
  - **INVALIDATOR 1 IS REAL AND MUCH BIGGER THAN 4× IN CELLS — and costs ~1.2× in WALL-CLOCK.** Smoking gun: the
    **median resolved tickers/date for NASDAQ `ohlcv_1m` is exactly 50** (of a 622 candidate universe) — the
    `resolved[:cap]` signature. Corrected equity remaining = **3,685,617 cells vs 216,824 (17.0×)**; grand total
    **456,033 → 3,924,832 (8.6×)**. **But only 1,563,611 of the equity cells are DATA-PRODUCING**; the other 2,122,006
    are denominator rows for tickers not listed on that venue (`empty_confirmed`, no vendor fetch). Work in
    data-producing terms = **4.0×** — matching the ~4× hypothesis — and in wall-clock terms only **~1.2×**, because the
    Databento fetch is ONE bulk request per (date, schema) that **already covered the full universe** before the fix
    (proven: the 2026-07-19 NASDAQ run.log uploads WDC/VRTX/TSLA/TXN — deep past the `A..BKNG` cap).
  - **MEASURED cells/min — replaces the tick-22 unmeasured 15–40 band.** Five real equity backfill VMs (2026-07-19,
    `vm-logs/tradfi-bf-{nasdaq,nyse}-ohlcv-1m-{2023,2024,2025}-*/run.log`), counting `StreamingParquetWriter: uploaded`
    (= exactly one cell): **NASDAQ 37.9 / 39.3 / 54.1 cells/min · NYSE 253.3 / 288.1 cells/min.** Rows/cell measured per
    venue×type: NASDAQ 1m **713** / 1s **3,151**; NYSE 1m **598** / 1s **1,713**; CME 1m **5,385** / 1s **18,179**.
    **The tick-22 15–40 band was right for NASDAQ and ~7× too low for NYSE.**
  - **🔴 THE REAL FINDING — equity cost is PER-CALENDAR-DATE, essentially INVARIANT to ticker count.** Normalising the
    same five runs to calendar-days gives a startlingly tight constant: **NASDAQ 1.506 / 1.508 / 1.514 min/date · NYSE
    1.807 / 1.814 min/date.** NASDAQ-2023 carries **38% more cells/day** than NASDAQ-2025 at **identical** wall-clock.
    Fitting across the venue gap: **fixed ≈ 1.46 min/date, variable ≈ 7.1e-4 min/cell** → **~97% of NASDAQ and ~81% of
    NYSE per-date cost is ticker-count-independent overhead.**
  - **🔴 CONSEQUENCE — the `d85d06e` ticker-group re-shard buys ~1.0–1.2×, NOT the claimed ÷5.** Five ticker-groups each
    re-walk the SAME 1,193 dates and each re-pays the ~1.46 min/date fixed overhead in full, so the critical path falls
    only from 1.81 to ~1.53 min/date while total compute **rises 5×** (46 → 231 equity VM-h). The re-shard is not
    harmful to wall-clock, but it was justified by a ÷5 that the measurement does not support. **The correct axis is
    DATE-sharding**: 20 date-slices/venue (all tickers per VM) pays the per-date overhead ONCE → equity critical path
    **7.1 h → 1.2 h** AND equity compute **231 → 46 VM-h**. Filed as a P1 todo below.
  - **CORRECTED ETA — binding constraint is TOTAL VM-HOURS vs `OHLCV_FLEET_CONCURRENCY_CAP=60`, not any critical path.**
    Equity as-shipped **231 VM-h** · **CME 758 VM-h (76% of all work)** · KRX/CBOE/FX/ICE ~10 → **~999 VM-h**. Critical
    path is only **7.1 h** (equity 366-date year-shard) / 6.7 h (heaviest CME root-year) — **not binding**. →
    **OPTIMISTIC ~15 h** (date-sharded, all `e2-highmem-16`, 90% packing) · **EXPECTED ~22 h** (as-shipped, 75% packing)
    · **WITH SPOT PREEMPTION ~30 h** (+35% requeue). CME is anchored on two real run.logs — `cme-cl-2025` (heavy: 947
    min for 365 dates = **2.59 min/date**, 29.6M rows @ 31.3k rows/min) and `cme-si-2025` (light: 36.4 min = **0.10
    min/date**) — with 15 heavy / 54 light roots over 96,924 remaining root-dates.
  - **TOP 2 LEVERS (both act on the throughput bound, not the critical path):** **(1) raise
    `OHLCV_FLEET_CONCURRENCY_CAP` 60 → 150** — it is a courtesy cap and the Databento budget is per-IP-per-VM (tick-22
    CORRECTION 1), so this is nearly linear: ~22 h → ~9 h. **(2) force `TRADFI_OHLCV_MACHINE=e2-highmem-16`** — the
    default is still `e2-highmem-4`; the measured 31.3k → 46.9k rows/min is a 1.5× on the CME 76%.
  - **HONEST UNCERTAINTY — the band is ±40% and CME owns all of it.** CME is 76% of total VM-hours but rests on **two**
    per-root anchors spanning a **26× spread** (CL 2.59 vs SI 0.10 min/date), with 69 roots bucketed heavy/light by
    name. **The single measurement that would most tighten this: per-root-date cost for ~6 more CME roots across the
    liquidity spectrum (e.g. ES, NQ, GC, 6E, PL, CT)** — that alone would collapse the 15–30 h band to roughly ±15%.
    Equity is now well-measured (5 VMs, 3 year-shards, two venues, σ<1% on min/date) and contributes little error.
  - **Machine-class caveat:** the five equity run.logs report `mem_pct` consistent with a **~128 GB** host
    (`e2-highmem-16`), not the `e2-highmem-4` launcher default — the per-date constants above should be read as
    e2-highmem-16 numbers. Both `--batch-date-concurrency` (dep@4eb50a4) and the re-shard (dep@d85d06e) landed
    **2026-07-20**, i.e. AFTER these 2026-07-19 runs, so the 1.56× is applied on top and is not double-counted.

**(3 open todos surfaced by this tick's re-analysis — promoted to the "Open todos" list at the top of this plan rather
than left buried here per PLAN_FORMAT.md's structural-order rule: re-shard equity OHLCV by date-range, raise
`OHLCV_FLEET_CONCURRENCY_CAP` 60→150 + default `e2-highmem-16`, re-measure CME per-root-date cost for ~6 more roots.)**

- **2026-07-20 (slot-1·laptop) — P0 nightly tradfi T+1 collection RESTORED (schema_version string regression) + P1
  yfinance disposition.** The live tradfi `_index/availability_index.parquet` carried `schema_version` as the STRING
  `"9"` across all 5,209,585 rows (arrow `string`, dtype object), so UTL `check_shard_freshness`
  (`manifest_writer/_queries.py:130/165`) hit `"9" < 9` → `TypeError`, crash-looping every UN-FORCED T+1 run (a
  `--force` run bypasses the freshness skip, which masked it).
  - **Root cause (proven, not timing):** writer
    `market-tick-data-service/scripts/restamp_tradfi_schema_v9_tail_2026_07_16.py:427`
    (`shard_df["schema_version"] = "9"`, a str) → the consolidator's DuckDB `read_parquet(union_by_name=true)` merge
    promotes an int64∪VARCHAR column to VARCHAR for the WHOLE corpus. Same class as
    `tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12` (row_count VARCHAR). Proof: the pre-restamp
    snapshot `_index/snapshots/pre_tradfi_schema_v9_tail_restamp_20260716T070255Z.parquet` ALREADY shows
    `schema_version` as arrow `string` — a direct causal artifact of the string-stamping writer. Ruled out:
    `migrate_tradfi_manifest_usd_lin` (never touches schema_version), the `tradfi-catalogue-canon` VM (instruments-store
    only, never the tick `_index`), `_rebuild_tradfi_cf11` (stamps int via record_empty/failed).
  - **Writer fix + regression test:** `market-tick-data-service@ac051bfe` — `restamp:427` now stamps int
    `MANIFEST_SCHEMA_VERSION` via new `stamp_v9_shard` helper;
    `tests/unit/scripts/test_restamp_tradfi_schema_v9_tail.py` asserts integer dtype + non-string arrow roundtrip.
    QG-green (`6550 passed`).
  - **Data repair (route: targeted in-place CAS re-stamp, NOT waiting on the blocked force-rebuild peer):** re-stamped
    the live `_index` schema_version → int64 (pre-snapshot
    `_index/snapshots/pre_schema_version_int64_restamp_20260720T184042Z.parquet`; gen `...840535586`→`...895173237`).
    **Held** across the next consolidator merge (post-merge gen `...598529744`, arrow int64, all rows int 9).
    **COORDINATION:** the `_index` is the shared object the manifest force-rebuild peer also targets — the re-stamp is a
    dtype-only change (0 rows added/dropped), so their subsequent object-scan rebuild (writes int schema_version via the
    manifest writer) is compatible + idempotent.
  - **Verified un-forced:** `check_shard_freshness` returns clean tuples on the int64 index; the exact nightly caller
    `TickDataHandler._apply_freshness_skip(date, ["tradfi"], None)` (`_force=False`) completes with real verdicts
    (`PARTIAL date=2026-07-19: 6/7 venues need processing … [CBOE, NASDAQ, NYSE, ICE, FX, KRX]`), not a TypeError.
  - **P1 yfinance:** ICE/FX/KRX fail every run because `Dockerfile:189 uv pip install -e . --no-deps` skips MTDS's
    declared deps and the base image lacks `yfinance` (lazy import in `yahoo_finance_adapter.py` dodges the import
    smoke). Ruled TOO RISKY to co-ship with the P0 (removing `--no-deps` re-resolves the whole image; a targeted install
    needs a Cloud Build to verify, and gcloud CLI reauth was broken this session). Filed with a concrete targeted-fix
    recommendation → `issues/mtds_image_missing_yfinance_no_deps_2026_07_20.md`.
  - Full write-up: `issues/tradfi_schema_version_string_regression_2026_07_20.md` (incl. a P2 consolidator
    `TRY_CAST(schema_version AS BIGINT)` defense-in-depth recommendation).

- **2026-07-20 (slot-1) — P1 yfinance MVP coverage gap RESOLVED + verified.** The MTDS image lacked `yfinance` so the
  Yahoo-routed tradfi MVP venues (ICE / FX / KRX — KRX is an operator deliverable) failed data collection every run. Fix
  (targeted, low blast-radius, per the issue doc): added a pinned
  `RUN uv pip install --system --no-cache-dir "yfinance==0.2.66"` (== uv.lock resolution / pyproject floor) **after**
  the `-e . --no-deps` line in the Dockerfile (kept `--no-deps`; did NOT `--no-deps` the yfinance install so its small
  new transitive deps — beautifulsoup4/curl-cffi/frozendict/multitasking/peewee — come along, rest are
  base-image-provided). Extended the cloudbuild `image-import-smoke` with `import yfinance` so a missing lazily-imported
  dep now FAILS THE BUILD instead of silently degrading a venue. **Other-absent-deps audit:** `yfinance` is the ONLY
  silently-absent declared runtime dep — the other lazily-imported venue deps (databento/web3/ccxt) are
  UTL-base-image-provided (their venues collect fine); `ib_insync` is undeclared (non-MVP IBKR), `polars` is
  benchmark-only. Shipped `market-tick-data-service@d8dc04e1` (Dockerfile + cloudbuild.yaml, quickmerge → LDR).
  **Runtime-verified:** `Evidence: cloudbuild=ce814d53-1648-4cf4-b2dc-7ac6bffefecd` (SUCCESS, built shipped sha
  `d8dc04e1`) — in-image smoke printed `YFINANCE OK 0.2.66` +
  `IMPORT SMOKE OK: market_tick_data_service.__main__ imported cleanly`; the smoke gates `push`, so the image cannot
  ship without yfinance. Live KRX/ICE/FX fetch deliberately not run (prod tick bucket + manifest under concurrent-agent
  contention); in-image import proof is the closing evidence. Issue doc →
  `issues/mtds_image_missing_yfinance_no_deps_2026_07_20.md` flipped `status: resolved`. (Un-blocked while shipping: the
  MTDS gate was red at the origin tip on an unrelated concurrent-agent regression — the durability `fail-on-raw`
  canonical-stem guard rejecting an un-updated `book_microstructure` CEFI test fixture; the peer's fix `mtds@953679de`
  landed mid-session and I rebased onto it, then the gate went green.)

- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still accurate, no changes needed.
- **context-scout 2026-08-03 (re-scout)**: refreshed context_scope (6 entries) -- swapped the parent closeout-doc
  pointer for the 2 docs actually holding the doc's one remaining genuinely open todo's real work
  (`tradfi_backfill_oom_remediation_2026_06_24.md`, `consolidator_throughput_backlog_monitor_2026_07_09.md`) plus the
  central shipped launcher-lib source file.

## Backfill drive — Progress Log (2026-07-21, autonomous session)

Live MVP OHLCV backfill fills the migrated canonical structure (the Phase D data prerequisite). Fleet driven at cap 60,
SPOT, per-VM shards.

- **Shipped**: MVP def expanded (`uac@afa2dd46`→`afa2dd64`: +409 = VIX FUTURE / treasury INDEX / KRW / crypto
  BTC-ETH-MBT-MET futures). CME crypto recognized-root fix (`uac@22e6a534`) — write-guard was quarantining
  `underlying=BTC/ETH` (in MVP scope but not `is_recognized_tradfi_underlying`); VALIDATED on real infra (BTC writes
  canonical `underlying=BTC`, futures-only). Launchers (`deployment-service@552d9de`): new CBOE-indices treasuries
  launcher (Yahoo daily, 5 tenors, registered `tradfi-bf-` prefix) + CME crypto set futures-only (operator "no cme
  option for btc and eth").
- **Launched + healthy** (449M+ records, 0 real errors, 0 quarantine): NYSE g01-g05 (20) + NASDAQ g01-g02 (7) equities;
  CME ES (SP500 fut+opt, canonical `underlying=SP500 options_chain`, the 69,822-option bulk) + GC + BTC + ETH; CFE VIX
  (canonical, completing fast); FX KRW (already-captured, skip-if-fresh).
- **Remaining (gated on slots at cap 60)**: CME MBT/MET + NQ/CL/SI/HG/NG/PA/PL; treasuries (8 VMs); NASDAQ g03-g05.
- **FINAL STEP (gated on backfill completion)**: rebuild+promote served catalogue so `mvp=True` reflects +409 (currently
  still old 70,930 set; new groups not yet flagged). Then Phase D gate: `/data-pipeline-check-mtds` + `-is` scoped
  tradfi, all shards.
- **Cleanup note — RESOLVED 2026-07-27, deployment-service@872ac2f**: CME launcher SSOT header cited archived
  `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` — fixed to point at this doc. (Live grep at fix-time found no
  `tradfi_mvp_set_expansion_2026_07_21.md` reference in this specific launcher; that non-existent-doc reference lives in
  a different launcher — `launch-tradfi-bf-cboe-indices-ohlcv-24h.sh` — out of this todo's scope.)

---

## Nice-to-have / deferred — Databento free L1/L2/L3 entitlement window (NOT MVP; operator 2026-07-21)

MVP intraday capture is `ohlcv_1m` + `ohlcv_1s` (both Databento **L0 = free ~16-year full history**), plus Yahoo
`ohlcv_24h` for the daily cells (Treasuries, KRW). Databento's tiered free-history entitlement additionally lets us
capture limited trade/order-book microstructure for the MVP instrument universe **at no extra cost within the free
window**:

- **`trades` / `tbbo`** (L1) — free **~1-year** history → capture the last ~1 year.
- **`mbp_10`** (L2) — free **~1-month** history → capture the last ~1 month.
- **`mbo`** (L3, market-by-order) — same short (~1-month) free window as L2, if wanted.

**This is a nice-to-have, NOT MVP** (operator 2026-07-21: "not even mvp, more a nice-have; no need to do it now, just
document"). The Phase-D gate already classifies these `(venue, data_type)` cells EXEMPT (`billing_gated_by_design`) —
leaving them un-captured is **not** a failure. To capture later: scope a separate short-window backfill over the MVP
instrument universe with `OHLCV_DATA_TYPES=trades,tbbo,mbp_10` (and `mbo`) and a `--start-floor` set to the entitlement
window (~today-1yr for L1, ~today-1mo for L2/L3), reusing the existing OHLCV launcher fleet.

**SSOTs**: `market-tick-data-service/scripts/pipeline_e2e_check.py` (`_TRADFI_BILLING_GATED_DATA_TYPES`,
`DATABENTO_SCHEMA_LEVEL` — the billing-guard oracle) + `/codex/02-data/tradfi-databento-sourcing-ssot.md` "Schema
allowlist" table.

---

**End of forked content.** For MVP universe / ground-truth-verdict context, Phase A2/C (adapter correctness,
data-status, honest-coverage) still tracked on the parent, and the full aggregated source-doc list, see
`tradfi_consolidated_closeout_2026_07_18.md`.

- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid + 1 stale citation fixed.** Both open todos
  read end-to-end. The "Bundle CME roots into fewer larger VMs" item is already extracted verbatim into
  `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` — citation added inline, not reclassified
  (conflict-check CONFLICT). The other open item is an umbrella pointer bundling three separately-owned docs
  (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`, `tradfi_backfill_oom_remediation_2026_06_24`,
  `consolidator_throughput_backlog_monitor_2026_07_09`) rather than worker-determinable work of its own, so the doc
  stays NA. **Observation for the next pass (not actioned here):** the first of those three now has 0 open checkboxes
  and is itself flagged as an over-line-cap prose-trap by
  `/plans/archive/issues/archive_candidate_docs_over_line_cap_blocks_edit_2026_07_29.md` (now archived, resolved
  2026-08-02 — both target docs archived, no split needed), so this umbrella todo's citation is drifting.
- **na-eligibility-audit 2026-08-02** (tradfi tranche): **KEEP-NA, stale items — 1 citation corrected.** In scope this
  run (not incrementally skipped) because the 2026-07-30 marker was followed by a substantive content edit: the "Bundle
  CME roots into fewer larger VMs" todo was flipped `- [x]` (`deployment-service@60b9d37`, via
  `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`). Re-read the doc's remaining open work end
  to end; exactly 1 open checkbox remains and the previous pass's own "citation is drifting" observation has now come
  true — actioned above: the rc137 leg is archived/complete, struck with evidence. Doc **stays NA**: the surviving todo
  is an umbrella pointer bundling two separately-owned, still-open docs rather than worker-determinable work of its own,
  so flipping `assigned_vm` would dispatch a tracking pointer, not a bounded task.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:c473b643442339c3]:
  **KEEP-NA-STALE-DUPLICATED, confirmed -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08
  marker" (git-date fallback), but `git diff <08-08-marker-sha>..HEAD` shows the intervening changes are an unrelated
  `effort: xhigh` frontmatter bump (already hash-excluded by `strip_frontmatter()`) plus the context-scout line directly
  above -- zero todo/verdict content changed. Reaffirming the 08-08 verdict without a fresh full re-read; see
  `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying false-positive class
  this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:dc0b82dc402b9bb2]:
  **KEEP-NA-STALE (already-duplicated), re-confirmed.** Fresh full read. Sole open todo bundles the rc137 leg
  (discharged/archived, struck inline) with 2 independently-owned legs: `tradfi_backfill_oom_remediation_2026_06_24.md`
  (now `assigned_vm: planning`, actively AO-dispatched) and `consolidator_throughput_backlog_monitor_2026_07_09.md`
  (`status: active` with its own open todos) -- both cited inline in the checkbox's own note. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
