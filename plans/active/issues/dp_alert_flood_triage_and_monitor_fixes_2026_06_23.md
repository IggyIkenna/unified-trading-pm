---
doc_type: issue
title: DP
summary:
  "`alerts.log` is **5 alert classes** (de-duping grep artifacts). Live GCS/Cloud-Run direct-checks (ADC, 2026-06-23
  ~20:50Z) classify each as a **monitor-signal false-positive** vs a **REAL outage th..."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-api, deployment-service, deployment-ui, instruments-service]
scope: [engineer, admin]
tags: [monitoring, alerting, data-pipeline, observability, self-healing, tradfi, spot-vm]
related:
  [
    /codex/05-infrastructure/deployment-observability.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    plans/active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md,
    plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md,
  ]
created: 2026-06-23
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    "alerts.log (830 lines, 2026-06-23",
    aggregated AG-agent prompts (deadman crash / tradfi fleet-monitor false-positives / alert-lifecycle gaps),
  ]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-06-23
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

`alerts.log` is **5 alert classes** (de-duping grep artifacts). Live GCS/Cloud-Run direct-checks (ADC, 2026-06-23
~20:50Z) classify each as a **monitor-signal false-positive** vs a **REAL outage the monitor correctly reports** — they
are a MIX, so blanket "fix the monitors" would have HIDDEN real problems:

| Class                                        | n   | Verdict                                                  | Live evidence (2026-06-23)                                                                                                                                                                                                                                                                                                                                                                   | Action                                                                                                                                        |
| -------------------------------------------- | --- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `DP_VM_STALL`                                | 115 | **REAL hang + a separate monitor weakness** (both fixed) | CORRECTED 2026-06-24 (tradfi-agent investigation, supersedes the original "FALSE/lagging-tee" read): the 18:00 wave was GENUINELY HUNG on the unbounded DBN chunk-decode (sidecar stale 184m + run.log frozen 2.5-3h). SEPARATELY the monitor mis-classified healthy-SLOW VMs via the 42-78m GCS-tee lag AND its (already-on) 45-min auto-kill keyed on that laggy signal (a live foot-gun). | hang → mtds@`afd5296`; monitor signal + safe kill → deployment-service@`7b070fb` (sidecar-authoritative); earlier shard-mtime pass @`6b76244` |
| `DP_CRON_DID_NOT_FIRE` [consolidator-tradfi] | 28  | **FALSE / transient**                                    | scheduler ENABLED `*/1`, last attempt 20:50:04; Cloud Run exec completed 20:49:40; `_index/availability_index.parquet` updated 20:51:56 (fresh)                                                                                                                                                                                                                                              | alert-lifecycle hardening (below)                                                                                                             |
| `DP_VM_GONE_NO_CAPTURE`                      | 26  | **likely REAL**                                          | `tradfi-es-2024-futures` "drained, captured 0→0, no rows written" — the silent-0-row tradfi class (`--source` not forwarded → `TickDataHandler` raises)                                                                                                                                                                                                                                      | investigate (below)                                                                                                                           |
| `DP_CATALOG_NOT_RUNNING` [tradfi]            | 18  | **REAL**                                                 | regen `lifecycle-catalogue-regen-tradfi` SUCCEEDS (17:19/17:06/…, re-ran `ncct7` 20:51 → succeeded) but `instruments-store-tradfi-prd/prod/catalog.parquet` is FROZEN at **2026-06-17** (6d; budget 24h). Monitor is CORRECT.                                                                                                                                                                | regen write-path bug (below)                                                                                                                  |
| `DP_ZOMBIE_WATCHDOG_DOWN`                    | 4   | **FALSE / transient**                                    | `vm-zombie-watchdog-…171612` RUNNING; census `gs://deployment-scripts-…/vm-census/watchdog-census.json` fresh (20:46, 4m). Monitor reads the CORRECT bucket (`_log_bucket()` = `deployment-scripts-<proj>`) — it was briefly stale at fire-time                                                                                                                                              | alert-lifecycle hardening (below)                                                                                                             |

**`monitoring-deadman` (separate channel, not the #data-pipeline-alerts flood):** the `uts-prod-monitoring-deadman`
Cloud Run job FAILED every `*/15` run (X/X, 0/1). Root cause: `deadman_poster.py:343` entered
`run_lifecycle(service_name="monitoring-deadman")` → UTL `run_lifecycle` calls `log_event` WITHOUT `setup_events()` →
`RuntimeError("Event logging not initialized")`. The deadman is the **out-of-band** watcher whose own docstring forbids
`log_event`/PubSub (it must be independent of the path it monitors), and GCP-native execution-absence alerting is its
bedrock — so the fix is to REMOVE `run_lifecycle` (its sibling out-of-band monitors use none) + honor "never raises,
exits 0 always". **SHIPPED** deployment-service@`9b32ea5`.

## Why it matters

The flood reads as "monitoring tools broken/unconfigured" (operator). Most classes are monitors reading a signal that's
fresh-but-they-mis-time, OR a genuinely stale artifact — but DP_CATALOG-tradfi + DP_VM_GONE are REAL data outages the
monitor correctly pages. Silencing them would mask a 6-day-stale tradfi instrument catalogue. The data pipeline is the
heartbeat — real issues get fixed, not hushed.

## Shipped (this pass, all QG-green + tested, draining LDR→staging)

1. **Deadman crash** — `deadman_poster.py` drop `run_lifecycle` + exit-0 contract — deployment-service@`9b32ea5`.
2. **DP_VM_STALL authoritative signal** — `heartbeat_stall_watcher.classify_vm_liveness` + `is_vm_progressing` now key
   on the **per-VM manifest-shard mtime** (`_index/per_vm/{vm}.parquet`, written DIRECTLY to GCS as the worker captures,
   ~60s, low-lag): a fresh shard OVERRIDES a stale tee'd `PIPELINE_HEARTBEAT` → a capturing VM never false-stalls AND is
   never auto-killed; fail-safe `None` ⇒ heartbeat/run.log signals still catch a non-writing VM. Wired in `cli.py`
   (`_make_shard_mtime_reader` via `_gcs.blob_age_minutes`). +3 unit tests. deployment-service@`6b76244`.
3. **cefi backfill venues** — `launch-cefi-sharded-backfill.sh` default += `BYBIT-SPOT`, `COINBASE-FUTURES`.
4. **Deadman JSON-sentinel freshness bug (the REAL "missing (never ran)" root cause — deeper than the OOM)** —
   deployment-service@`b1fbc92`. After the OOM fix the deadman STILL paged all 3 fleet monitors + the watchdog census
   "sentinel stale: missing (never ran)" on EVERY run despite the sweeps writing FRESH sentinels. Root cause:
   `_gcs.blob_age_minutes` → on `deployment-scripts-*` the storage-client `last_modified` reads **bare/None** (the
   documented 2026-06-22 quirk) → it falls back to `_content_epoch_age_minutes`, which only handled the
   heartbeat-sidecar shape (first line = Unix epoch int). The `{mode}-last-run.json` + `watchdog-census.json` sentinels
   are **JSON** (`{"ts":"<ISO>",...}`) → `int("{...")` raises → `age=None` → `probe_freshness` reads stale → "missing".
   It surfaced ONLY now because the deadman previously CRASHED (run_lifecycle) before reaching
   `check_monitor_sentinels`. Fix: `_content_epoch_age_minutes` now reads the JSON `ts` field when the epoch parse fails
   (additive — epoch sidecar unchanged). +3 regression tests
   (`test_blob_age_minutes_reads_json_ts_when_last_modified_bare` / `test_monitor_sentinel_fresh_json_not_stale` /
   `test_blob_age_minutes_still_reads_epoch_sidecar`). This also fixes the freshly-added `check_critical_infra`
   watchdog-census probe (same JSON path → would have false-paged `DP_ZOMBIE_WATCHDOG_DOWN`).
5. **Sidecar-authoritative heartbeat + safely-enabled auto-kill + host-cron sentinel (FIX 1/1b/2, tradfi-agent
   dispatch)** — deployment-service@`7b070fb`. The DP_VM_STALL keystone (#2) used the per-VM shard mtime, which only
   protects a VM while CAPTURING; a healthy-but-between-captures VM still false-STALLed on the 42-78m GCS-tee lag, AND
   the (already-on) 45-min auto-kill keyed on that laggy run.log → a live foot-gun. **FIX 1**:
   `heartbeat_stall_watcher.sweep` now reads the FRESH infra **sidecar blob** (`vm-heartbeat/{vm}.txt`, direct 60s GCS
   channel, via `cli._make_sidecar_age_reader` → `_gcs.heartbeat_blob_age_minutes`) as the authoritative
   `heartbeat_age_min`. The sidecar goes stale ONLY when the host/network wedges — the tradfi agent confirmed the 18:00
   hung wave had **sidecar blobs stale 184m**, while a healthy-slow VM's is <2m. This REVISES BUG2 (which went
   run.log-primary for worker-death-on-live-host): that case is now the run.log-frozen **alert-only** corroborator at a
   generous **90m** bound (`DEFAULT_RUN_LOG_STALL_MINUTES` 45→90, above the 78m max tee-lag). **FIX 1b**: the auto-kill
   (already default-on) is now **sidecar-gated** — a fresh sidecar ⇒ `is_vm_progressing` True ⇒ never reaped; only a
   sidecar stale ≥ `kill_minutes` (host wedged) is reaped. **FIX 2**: `wave_launcher.py` writes a
   `vm-census/wave-launcher-last-run.json` host-cron sentinel each tick; the meta sweep probes its freshness (budget
   360m) with NO Cloud-Run-history cross-check (a HOST cron is invisible to Cloud Run) → no false
   `DP_CRON_DID_NOT_FIRE`, while a genuinely-dead wave-launcher still pages. +6 unit tests
   (sidecar-fresh-overrides-laggy / sidecar-stale-stalls-and-kills / fresh-sidecar-never-kills / stale-sidecar-kills /
   host-cron-sentinel-fresh).

## Open work (tracked todos)

- [x] ✅ [DEPLOY] P0. **DONE + VERIFIED 2026-06-23 ~22:00Z.** The deployment-api image CLONES
      deployment-service@live-defi-rollout (cloudbuild `clone_dep`), so the "ahead of main" never mattered — built
      `deployment-api:latest` from LDR (Cloud Build `0c9af143` SUCCESS) → re-pinned the 4 dp-_ monitor jobs to the fresh
      digest → executed: **deadman 1/1 GREEN (exit 0, was exit 1 every run); heartbeat-watcher 1/1 GREEN.** All 3 fixes
      (deadman + keystone + RESOLVED bookend) are live on the dp-_ jobs.
- [x] ✅ [MONITOR] P0. **dp-\* monitor OOM (newly surfaced by the now-working deadman) FIXED.** With the deadman alive,
      it paged "dp-exit-code-monitor / dp-heartbeat-monitor / dp-meta-monitor — sentinel stale: never ran". Root cause:
      exit-code + meta Cloud Run jobs were **OOM-killed (signal 9) every run at 2Gi** (heartbeat was already bumped to
      8Gi for the same 2026-06-23 incident; the tf comment wrongly assumed exit-code/meta "stay green at 2Gi"). Bumped
      both to **8Gi/cpu2** (runtime via `gcloud run jobs update` + durable in
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`); verified both execute 1/1 green on 8Gi.
- [x] ✅ [MONITOR] P1. **Deadman now verifies the vm-zombie-watchdog census OUT-OF-BAND** (`check_critical_infra`, +2
      tests) — previously the deadman only checked the 3 fleet-monitor sentinels, so a dead watchdog was only caught
      in-band (unreliable when the meta sweep is down). deployment-service (shipped with the OOM tf bump).
- [x] ✅ [MONITOR] P0. **CRITICAL-SERVICE LIVENESS — 5 GCP uptime checks + alert policies are now LIVE (applied
      2026-06-24).** `terraform/gcp/critical_service_uptime.tf` (deployment-service@`b1fbc92`+) creates a
      `google_monitoring_uptime_check_config` + `google_monitoring_alert_policy` per critical service —
      `deployment-api`, `agent-orchestrator` (central VM/nginx), `alerting-service` (403-accept = alive-but-auth-gated),
      `deployment-dashboard`, and `unified-trading-system-ui` (odum-research.com) — every 5 min from GCP external
      probers → the deadman EMAIL channel (`monitoring_deadman_email`, id 15957…), fully **independent of the Slack
      relay / alerting-service** (so it pages even when the alerting SPOF is down — the keystone out-of-band guard).
      `tofu apply` ran (5 uptime + 5 policies added, 0 changed/destroyed); the `notification_rate_limit` block was
      dropped (API rejects it for metric-threshold policies). `/health` endpoints: deployment-ui nginx `/health` added;
      unified-trading-system-ui `app/health` already 200; alerting-service auth-gated 403-accept. NOTE: there is **no
      terraform-apply pipeline** for `terraform/gcp/` — future infra in that dir needs a deliberate `tofu apply` (remote
      GCS state, targeted apply is safe). Codex SSOT update `/codex/05-infrastructure/deployment-observability.md`
      pending (P1 below).
- [x] ✅ [MONITOR] P0. **FIX 1/1b/2 DEPLOYED + VERIFIED LIVE 2026-06-24 ~05:15Z** (deployment-service@`7b070fb`, image
      `deployment-api@56f2060e`, dp-heartbeat + dp-meta jobs re-pinned). Live fleet probe with the deployed classify:
      healthy capturing 6e (sidecar 0.9m) → **ALIVE** (flood killed); hung 6z/6l (sidecar 33-93m) → **STALL** (real, not
      silenced); auto-kill **AUTO_KILL=False** for both (6z < 45m window; 6l sidecar recovered to 1m → host alive →
      hung-worker alert-only, never reaped) — proves the sidecar-gated kill never reaps a live host. FIX 2: meta probe
      of the wave-launcher sentinel = age 3.7m, stale=False (seeded; wave-launcher re-pinned to the fresh image → its
      06:00Z `0 */3` tick refreshes it).
- [ ] [MONITOR] P2. **deployment-service:latest carries the new wave_launcher.py** — the wave-launcher Cloud Run job was
      runtime-re-pinned to `deployment-api@56f2060e` (which has `_write_last_run_sentinel`), but its terraform default
      is `deployment-service:latest` (a SEPARATE image, still old). A `tofu apply` would revert the pin → the
      wave-launcher would stop writing the host-cron sentinel → false `DP_CRON_DID_NOT_FIRE` after the 6h seed budget.
      Trigger the `deployment-service-jobs-image-build` from LDR (or let it rebuild on the next LDR push) so
      `deployment-service:latest` carries the sentinel writer, then the terraform default is correct and the runtime pin
      can revert harmlessly.
- [x] ✅ [DOCS] P1. **Codex SSOT update — DONE 2026-06-24.** Added the "Out-of-band liveness + data-pipeline
      self-monitoring (2026-06-24)" section to `/codex/05-infrastructure/deployment-observability.md`: the 3 independent
      layers (Layer-1 dp-\* fleet monitors incl. the sidecar-authoritative heartbeat + sidecar-gated auto-kill +
      host-cron sentinel + the per-mode RESOLVED bookend; Layer-2 out-of-band deadman with the content-`ts` freshness
      contract for the bare-`last_modified` quirk; Layer-3 the 5 critical-service GCP uptime checks → the email channel
      independent of the alerting-service SPOF) + the **no-terraform-apply-pipeline** gap for `terraform/gcp/`.
- [x] ✅ [DATA] P1. **DP_CATALOG-tradfi — DONE + VERIFIED 2026-06-24.** Root cause was NOT a write-path/bucket
      divergence: `lifecycle-catalogue-regen-tradfi` OOM-died at **32Gi** ("configured memory limit reached", exec
      `ncct7` 21:34Z) because `_iter_by_date_snapshots` used `ThreadPoolExecutor.map` (submission-order yield) and
      buffered the whole 11.6k-frame by_date corpus in RAM; the monotonic guard then kept the 2026-06-17 catalogue. Fix:
      `instruments-service@b84cc4f` (`_bounded_parallel_load` completion-order sliding window, peak O(max_workers), +4
      regression tests, QG-green) + `deployment-service@9b74416` (tf 32Gi→16Gi/cpu4, timeout 1800→3600) + regen job
      image rebuilt (Cloud Build `c0b6772a`, digest `614f9446`) + live job pinned. **Verified:** regen completed
      **37m29s with NO OOM**; `instruments-store-tradfi-prd/prod/catalog.parquet` refreshed to **2026-06-24T00:36:46Z**
      (was frozen 2026-06-17).
- [x] ✅ [MONITOR] P1. **Alert-lifecycle hardening — DONE 2026-06-24** (deployment-service@`a19bbda` meta + @`2763578`
      heartbeat/exit-code). (b) **RESOLVED bookend now spans ALL 3 sweeps**: `meta_watchers.reconcile_resolved` is
      generalized (per-mode active-alert blob `vm-census/active-dp-alerts-{mode}.json` + injected emitted set); the
      heartbeat + exit-code sweeps record fired findings via a `finding_sink` and the cli reconciles each → a recovered/
      reaped VM (`DP_VM_STALL`) or captured/relaunched cell (`DP_VM_GONE`) posts a `:white_check_mark: RESOLVED` INFO
      instead of a permanent RED. +2 tests. (a) The "re-probe immediately before firing" is **subsumed** by the existing
      KEY #4 Cloud-Run execution-history cross-check (a stale artifact + a recent SUCCEEDED job is already suppressed) +
      the now-fleet-wide bookend — the within-tick re-probe window is microseconds, so it adds nothing the cross-check +
      bookend don't already cover. Goal met: transient flood → zero WITHOUT silencing a real persistent stall (a
      persistent condition re-fires every sweep → never resolved → still pages).
- [x] ✅ [DATA] P1. **DP_VM_GONE-tradfi — DONE 2026-06-24.** Confirmed via run.log: `tradfi-es-2024-futures-*` genuinely
      captured 0 — but the root cause was NOT the `--source`-not-forwarded class. These VMs were launched by
      `launch-cefi-sharded-backfill.sh::launch_tradfi_shard` running `task=cefi-backfill --venues CME-FUTURES`
      (non-canonical) → `WARNING No active venues … TRADFI` every date → 0 rows → `exit_code=0` self-delete. The
      canonical `tradfi-bf-*` Databento path captures fine (verified 51087 rows/VM). Fix: `deployment-service@04942d5`
      removes `launch_tradfi_shard` + the tradfi loop from both sharded launchers → the 0-capture class is eliminated at
      source (nothing to relaunch; TradFi OHLCV served only by the capturing Databento `tradfi-bf-*` launchers).
- [x] ✅ [MONITOR] P2. **TRADFI HTTP-hang defensive hardening** (market-tick-data-service): bound every outbound
      Databento/HTTP call (`timeout=`) + wrap the per-shard fetch in `asyncio.wait_for` so a stall fails the shard
      (attempted_failed + `classify_venue_error`), never the VM. **CORRECTION 2026-06-24:** the DP_VM_STALL flood was
      NOT a lagging-tee false-positive — the 18:00 wave was GENUINELY HUNG on the unbounded DBN chunk-decode (sidecar
      blobs stale 184m + run.log frozen 2.5–3h, far beyond any tee-lag). The live hang is FIXED + CONFIRMED:
      `market-tick-data-service@afd5296` wraps the chunk-decode in `asyncio.wait_for` (`MTDS_DATABENTO_CHUNK_TIMEOUT_S`)
      so a stalled chunk fails the shard, not the VM (hardened VMs verified alive past 74m where the pre-fix wave hung
      by ~70m). The lagging-tee IS a real but SEPARATE secondary issue (heartbeat_stall_watcher reads run.log not the
      fresh `deployment-scripts-{pid}/vm-heartbeat/{vm}.txt` sidecar blob — handed to the monitor/infra agent; it also
      blocks safely enabling the 45-min auto-kill). **DONE 2026-06-24 — market-tick-data-service@2410e712 | QG exit 0:**
      every REMAINING outbound Databento SDK call is now bounded (the live chunk-decode site was already done @afd5296).
      Audited all 12 databento files; the `Historical(key, gateway)` SDK 0.73 constructor accepts NO timeout kwarg
      (hardcodes a 100 s per-read socket timeout, untunable), so each blocking call is wrapped in executor +
      `asyncio.wait_for` (async sites) / `ThreadPoolExecutor.result(timeout=)` (sync sites, **`shutdown(wait=False)` on
      timeout** so a `with`-block exit can't re-introduce the hang on the hung worker). **New env knob
      `MTDS_DATABENTO_REQUEST_TIMEOUT_S` (default 180 s)** for short calls; large get_range keeps `_FETCH_TIMEOUT_S`
      (3600 s) + chunk-decode keeps `MTDS_DATABENTO_CHUNK_TIMEOUT_S`. **Call sites bounded:** (1) symbology/DEFINITION
      `timeseries.get_range`+`to_df` (`databento_symbology._fetch_definition_df_for_stype`) → stall emits
      ADAPTER_FETCH_FAILED + returns empty df, the per-stype loop continues (shard isolation); (2) `metadata.get_cost`
      (`databento_fetch._emit_payg_spend`) → records `cost_lookup_error=TimeoutError`, never blocks; (3)+(4)
      `batch.list_jobs` ×2 (`databento_batch_jobs._query_key_for_matching_job` parallel-scan + `_lookup_job_in_list`
      poll) → key skipped / retry next poll; (5) `batch.download` (`_execute_batch_download`, bounded by
      `timeout_minutes`≥600s floor) → raises TimeoutError to the async executor caller; (6) live WS connect/subscribe
      **handshake** (`_open_subscriptions` + `_start_streaming`) → bounded (steady-state `stream()` consume loop
      intentionally LEFT unbounded — runs forever). Already-bounded (no change): the streaming `get_range` fetch
      (`_fetch_timeseries_range`, @afd5296 predecessor) + `metadata.list_datasets` warmup (ThreadPoolExecutor.result).
      Shard-isolation verified: the symbology stype loop + the per-date fetch loop both swallow the new TimeoutError (no
      `raise` escapes the per-shard boundary). +6 focused unit tests (`tests/unit/test_databento_outbound_timeouts.py`,
      mocked SDK / no live creds — each simulates a `threading.Event`-blocked stall and asserts the wrapper
      RETURNS/raises within a generous outer `wait_for` instead of hanging). SSOT:
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`.
- [ ] [TRADFI] P1. **Root-cause + close the 06:00-UTC tradfi-bf OHLCV hang loop** (target repo:
      `market-tick-data-service`; `parent_epic: tradfi_master`). **🔴 ROOT CAUSE CORRECTED 2026-06-24 (tradfi-agent) —
      it is an OOM crash-loop, NOT a hang, NOT a stale tarball, NOT a databento call** (so afd5296/2410e712 are
      irrelevant to it). Serial console on every stale VM (gc=60 / es=30 / nyse-2024=22 / 6j=many
      `Out of memory: Killed process (python)`, anon-rss ~15.3 GB on e2-standard-4/16 GB): each chunk's fresh python
      balloons to ~15 GB in ~3 min, OOM-killed; the `mtds_chunk_loop.sh` wrapper advances and the next process re-OOMs —
      externally indistinguishable from a hang (sidecar/run.log/shard all stale, VM `RUNNING`). **Cause:** the per-date
      sentinel fan-out re-downloads + re-parses the date-INDEPENDENT `catalog.parquet` (cefi=227,576 rows, 2×/date +
      defi + tradfi) with NO caching → pyarrow/pandas churn never returned to the OS. **FIX SHIPPED + VERIFIED (mtds
      working tree, green in isolation):** instance-level catalogue memoisation on the cefi/defi/tradfi readers +
      regression `tests/unit/engine/test_catalog_reader_cache.py`. **BLOCKED ON LAND:** a LIVE concurrent agent is
      mid-edit on the UAC+UTL dep clones (Barchart-removal/databento-first close-out; UAC commit `137d1f8a`
      unpushed+dirty, UTL still refs retired `BATCH_BARCHART`) → breaks the shared local QG (11 unrelated
      `batch_massive`→`batch_databento` skew failures) AND makes a safe tarball rebuild impossible (would bake half-done
      deps → VM import-crash). Land + tarball + relaunch + run-to-completion pending that dep WIP settling. Full
      detail + sub-todos: `tradfi_backfill_oom_remediation_2026_06_24.md`. DISPATCH for the tradfi agent — context below
      is cold-start-complete (worker reads `SUB_AGENT_MANDATORY_RULES.md` first). env:
      `GCP_PROJECT_ID=central-element-323112     DEPLOYMENT_ENV=prod CLOUD_PROVIDER=gcp`, ADC admin. **These were REAL
      hangs, not monitor false-positives** — on 2026-06-24 the dp-heartbeat-watcher correctly fired DP_VM_STALL for 7
      `tradfi-bf` OHLCV VMs whose sidecar blob (`vm-heartbeat/{vm}.txt`) + GCS-tee'd run.log + per-VM manifest shard
      were ALL stale 66–223 min and capturing nothing (shard `None`), e.g.
      `tradfi-bf-cme-ohlcv-1m-6z-2025-20260623-230709` (sidecar 223m / runlog 219m / shard None),
      `…-cl-2025-20260624-000107` (163m/160m/None), `…-nasdaq-ohlcv-1m-2024-20260624-060102` (170m), plus 6a/6c/6s
      (127–156m) and `…-es-2020` (66m). All 7 manually REAPED (monitor side handled — the auto-kill import bug is
      fixed + deployed, so future genuine hangs auto-reap within ~one `*/5` sweep; you will NOT get a DP_VM_STALL flood
      while you fix the root cause). But reap+wave-launcher-relaunch is a band-aid: a persistently-hanging VM
      reap→relaunch→rehang loops forever and the tradfi backfill never progresses — fix at the source. **Why the
      chunk-timeout hardening may not have covered these:** live VMs bake code from a GCS tarball
      (`create-code-tarballs.sh`), so they run whatever was in the tarball AT LAUNCH, not live LDR/main. The 06:00 wave
      may predate `market-tick-data-service@afd5296` (the `asyncio.wait_for(MTDS_DATABENTO_CHUNK_TIMEOUT_S)`
      chunk-decode wrap). Two hypotheses: (a) **stale tarball** — rebuild from clean LDR
      (`bash     deployment-service/scripts/vm/create-code-tarballs.sh`) + ensure the wave-launcher's launchers pull the
      fresh one before the next wave; (b) **a different unbounded outbound call** the chunk-decode wrap doesn't cover
      (initial timeseries/metadata fetch, auth/connector setup, DNS/socket stall) — note `@2410e712` since bounded all
      12 remaining Databento call-sites, so verify whether the hung tarball had it. **Diagnose:** SSH/serial-console a
      hung VM (or relaunch one + let it hang), capture the on-VM `/tmp/vm-exec-*.log` tip + a py-spy stack of the worker
      to see the exact block point, and check the tarball's baked git sha vs `afd5296`/`2410e712`. Fix the side that's
      wrong, run the backfill to ACTUAL completion (manifest-verified rows, not "VM launched"), and flip the [MONITOR]
      P2 defence-in-depth hardening item above to confirm full shard-isolation coverage. **NOTE 2026-06-24:** the
      CURRENT wave (12 RUNNING tradfi-bf VMs) all have FRESH sidecars (0–31m) → the fix IS reaching new VMs and the live
      hang appears resolved; this todo confirms root cause (stale-tarball vs different-call) + runs the backfill to
      completion so it doesn't recur.

## Recommended decision

Land the shipped fixes to `main` (drain the deployment-service promotion backlog OR manual image rebuild) → re-execute
the deadman + confirm green. Treat DP_CATALOG-tradfi + DP_VM_GONE as REAL data issues (do NOT silence). Build the
re-probe+RESOLVED-bookend alert-lifecycle hardening as the systemic fix for transient false-positives.
