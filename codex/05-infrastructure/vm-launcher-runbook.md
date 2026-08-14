---
doc_type: codex-ssot
title: VM Launcher Runbook
summary: >-
  Per-launcher usage runbook for the ~83 `deployment-service/scripts/vm/launch-*.sh` VM launchers — when-to-use,
  required args, expected duration, and common failures for each, grouped by category (infra/cron, MTDS backfill,
  forward-poll, features, strategy, validation, instruments, sports, ML, admin/migration).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service]
scope: [engineer, admin]
tags: [infrastructure, runbook, spot-vm, backfill, mtds, scripts]
related:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/vm-log-archival.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/06-coding-standards/quality-gates-memory-governance.md,
    /plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md,
    /plans/archive/issues/features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md,
  ]
created: 2026-05-15
authoritative_for:
  [
    VM launcher per-script usage runbook,
    heavy-compute-on-shared-host ad-hoc-script rule,
    "heavy-compute-on-shared-host rule scope (production code, not just ad-hoc scripts)",
    "before a --force whole-corpus refetch, check for an existing surgical column-filler rule",
  ]
referenced_by:
  [
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-log-archival.md,
    plans/audit/results/vm_security_audit_2026_05_15.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
owner:
last_reviewed: 2026-08-10
code_refs:
type: infrastructure
execution:
  {
    owner: deployment-platform,
    cadence: per VM-launcher add/change,
    verifier:
      bash deployment-service/scripts/vm/launch-*.sh --help (per-launcher); reference existing examples in
      deployment-service/scripts/vm/launch-*.sh,
    last_executed: 2026-05-17 (slot-8 frontmatter codification),
  }
---

# VM Launcher Runbook

**Author**: slot-2 agent **Date**: 2026-05-15 **Scope**: All `deployment-service/scripts/vm/launch-*.sh` (83 launchers)
**Owner**: Harsh (infra/ops) / Ikenna (strategy/DeFi gate decisions) **Verifier**: QG STEP 5.69 (bucket naming) +
shellcheck (security) **Last executed**: 2026-05-15 (slot-2 security audit sweep)

---

## How To Use This Runbook

Every section below: **When to use → Required args → Expected duration → Common failures**.

For VM naming rules see `/codex/05-infrastructure/launcher-script-ssot.md`. For event emission see
`plans/audit/results/vm_event_emission_audit_2026_05_15.md`. For tarball creation see
`/codex/05-infrastructure/vm-tarball-deployment.md`. For log backup, archival, and kill/teardown runbook see
`/codex/05-infrastructure/vm-log-archival.md`. **Provisioning (HARD RULE): backfill VMs default to Spot**
(`--provisioning-model=SPOT`, `--on-demand` opt-out; live VMs stay on-demand) — see
`/codex/05-infrastructure/spot-vms-for-backfill.md`.

**HARD RULE — never hand-roll a VM name; verify the registry FIRST, before launch, not after a failure.**
`VM_PREFIX_TO_BUCKET` (`deployment-service/scripts/vm/vm_zombie_watchdog.py`) is the SSOT `classify_deployment_target()`
longest-prefix-matches every VM name against; an unregistered prefix does **not** fail loudly at launch time — it just
silently never appears in deployment-ui `/deployments`, `/cockpit`, Slack, or `/api/fleet/reconciliation` (surfaces as
`UNKNOWN`, a classify-or-kill candidate) until someone goes looking. Real incident, 2026-07-09: an agent invented an ad
hoc one-off migration VM name instead of reusing `launch-canonical-migration-vm.sh` (the existing
`canonical-migration-{cefi,tradfi,defi,prediction,legacy}-` launcher for exactly this job class) — the VM ran and
finished before the gap was caught, but it was invisible to every monitoring surface the whole time. **Before launching
ANY new one-off/migration VM**: (1) check whether an existing `launch-*.sh` in this doc already covers the job —
reuse/extend it, don't hand-roll; (2) if a genuinely new prefix is needed,
`grep VM_PREFIX_TO_BUCKET deployment-service/scripts/vm/vm_zombie_watchdog.py` first and add a real `VmPrefixSpec` entry
(shipped via quickmerge) before using that prefix — never launch first and register later. Full incident write-up:
`plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md` Progress Log, 2026-07-09 "real gap found in
the VM launch itself" entry.

**HARD RULE — before launching a `--force` whole-corpus refetch to fix ONE column, check whether a surgical
column-filler script already exists** (codified 2026-08-10; precedent: § N of
`/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`). A full
`--force --entity <X>` backfill re-fetches and re-writes the ENTIRE corpus to fix one missing/blank field, at per-DATE
call volume. Measured precedent (populating `round` on api-football FIXTURES): the `--force --entity FIXTURES` backfill
over 2019-01-01..2026-07-17 runs **~527 calls/date x 2,390 dates ~= 1,260,000 api-football calls**, while the surgical
`backfill_sports_fixture_round_2026_07_17.py` (round-only, single-walk, idempotent, snapshots each parquet to
`*.pre_round_backfill.bak`) completes in **~600-700 TOTAL calls** (one bulk `GET /fixtures?league&season`, cached) — a
**~1,800x call-volume reduction to populate ONE field**. At the 450,000/day key quota the full re-fetch needs ~2.8 days
of pure quota (~76h paced); no rate tuning or extra VMs raise that ceiling. `--force` also forfeits presence-skip resume
(a preempted `--force` run is not replayable from progress). **Before launching any `--force` whole-corpus refetch, grep
for an existing surgical column-filler first** (e.g. `rg -l "backfill_.*(round|column|fill)" <repo>/scripts/`).

**HARD RULE — heavy I/O NEVER runs from the operator's local machine; it runs on a VM in-region, always, not just when
the operator happens to mention bandwidth.** "Heavy" = any full/near-full corpus GCS discovery walk, a manifest-index
read-transform-write over the whole `_index`, or a rename/backfill touching more than a few hundred objects. "Local
machine" = an interactive per-tab worktree session on the operator's own laptop
(`/codex/05-infrastructure/per-tab-worktrees.md`) — it has no in-region GCS network path, its bandwidth is
metered/costly (roaming, tethering, etc.), and its uptime isn't guaranteed mid-task. **Does NOT apply to the
human-planning VM or the AO central-orchestrator `planning` VM**
(`/codex/04-architecture/runtime-deployment-topology.md`) — both are already cloud-hosted with fast/cheap internet, so
heavy I/O from either is fine; the rule targets the operator's own hardware specifically, not "any non-designated-VM
session." Real incident, 2026-07-24: a corpus-wide Script-2 discovery walk (2,674 days, no `--start-date` scoping) was
launched directly in a local per-tab session and measured at ~65–90s/day — an ETA of 48–67 **hours** — before the
operator separately flagged they were on paid roaming data, at which point it became clear the same run had already been
pulling that volume through the operator's own connection the whole time, unnoticed until the ETA math was done.
**Applies unconditionally on a local machine, independent of any stated connectivity/cost constraint** — reuse an
existing `launch-*.sh` per the rule above (`launch-canonical-migration-vm.sh` for one-off migrations; the generic
`canonical-migration` `VM_TASK` dispatch in `setup-data-pipeline-vm.sh` runs any `VM_MIGRATION_CMD` verbatim, so it fits
scripts with no dedicated launcher yet). A local session may only: launch/poll a VM (control-plane calls + small log
tails), read/write git and plan docs, and do single-object `gsutil stat`/small-file reads for a quick health check. SSOT
for VM selection/naming: this doc's rule above; for Spot provisioning:
`/codex/05-infrastructure/spot-vms-for-backfill.md`.

**HARD RULE — a killed local launcher process does NOT mean the VM create call was cancelled; verify before assuming
failure OR before retrying.** `gcloud compute instances create` is issued as one HTTP call inside the launcher's local
bash process; if that local process is killed (a tool-call timeout, Ctrl-C, a background-job cutoff) AFTER the call was
already sent but BEFORE the launcher printed its own success confirmation, the create request itself keeps executing
server-side and the VM is very likely to come up anyway — the kill only stopped the WATCHER, not the launch. Real
instance, 2026-07-30 (`cefi_content_migration_fleet_half_incomplete_2026_07_26.md`): a foreground batch of 21 sequential
launches hit a 120s tool timeout mid-launch; re-running the launcher for the in-flight shard immediately after produced
`ERROR: ... already exists` — the VM the timeout appeared to have killed had, in fact, already been created. **Before
treating a timed-out/killed launch as failed-and-safe-to-retry**, check
`gcloud compute instances describe <name> --zone=<zone>` (or `instances list --filter="name~<prefix>"`) for the exact
name the launcher was about to use — a `RUNNING` result means it succeeded despite the local kill; only retry with the
SAME name if it genuinely does not exist (an `already exists` retry error is itself the confirmation, not a new problem
— no action needed beyond verifying the existing instance is healthy).

**HARD RULE — a `pipeline_e2e_check.py`-family driver launching a `-test-`-bucket smoke VM MUST pass `--env staging` (or
set `DEPLOYMENT_ENV=staging`) explicitly.** Every `launch-*.sh` defaults `DEPLOYMENT_ENV` to `prod`, which resolves
`uts-prd-sa` — correct for a real launcher, but wrong for an e2e-check-style test-bucket run: since the tier-isolation
IAM lockdown, `uts-prd-sa`'s `storage.objectAdmin` grant is IAM-Condition-scoped to `-prd-` buckets only, so an
unmodified driver 403s on every force/skip leg against a `-test-` bucket. Fixed 2026-08-01 in all 4 existing drivers
(`features-service`, `instruments-service`, `market-data-processing-service`, `market-tick-data-service`); any NEW
`pipeline_e2e_check.py`-family driver must carry the same `--env staging` fix from the start. Full incident + fix
details: `/plans/archive/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`.

## Heavy COMPUTE/MEMORY on the shared planning-vm (HARD RULE, added 2026-07-27)

> **Scope correction (2026-08-12): this ALSO applies to the operator's own laptop, not just the shared planning-vm/AO-
> orchestrator VM.** The rule as originally titled names only "the shared planning-vm" — but the laptop is ITSELF a
> shared host in this workspace's per-tab-worktrees model (multiple concurrent interactive tab sessions, each able to
> dispatch its own sub-agents doing ad-hoc analysis). Real incident, 2026-08-12: several sub-agents investigating a
> TradFi backfill each independently downloaded the full tradfi consolidated manifest
> (`_index/availability_index.parquet`, ~14.29M rows) to the laptop for coverage checks, concurrent with other tabs
> doing similar large pandas/pyarrow reads — the resulting host-wide RAM pressure triggered `quality-gates.sh`'s own
> governor-watchdog to SIGTERM an unrelated, legitimate QG run in a different repo/tab. Separately found the same
> session that `scripts/dev/run-bounded-analysis.sh` — the designated fix for exactly this — had ZERO actual enforcement
> on macOS: `setsid` (used for process-group isolation) doesn't exist there at all, so the RSS-poll fallback's launch
> line failed silently and every run degraded to "fully UNWRAPPED, advisory only." **Both fixed 2026-08-12**: the
> wrapper now uses bash job control (`set -m`) instead of `setsid` (portable, no external binary), and reads RSS via
> `ps -o rss=` when `/proc` is absent (macOS/BSD) — verified end-to-end on a real macOS host, new regression test
> `scripts/dev/test-run-bounded-analysis.sh`. The remedies below now apply identically on the shared planning-vm OR a
> laptop session with other tabs open, and "cap it" actually enforces on both platforms.
>
> **Scope correction (2026-08-01): this is NOT limited to throwaway "ad-hoc scratchpad" scripts.** The original wording
> below (and its own incident) made it read that way, and that reading is exactly why the rule didn't stop the next two
> occurrences: `instruments-service/scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py` (43.6GB RSS, real
> tracked catalogue-backfill code, not a scratchpad file) caused a full agent-orchestrator outage on 2026-07-31, and
> `features_service.cross_instrument`'s batch compute (38.8GB RSS, also real service code, additionally outliving its
> own `timeout 150` wrapper entirely) caused a SECOND full outage on 2026-08-01. **The rule below applies to ANY
> subprocess run directly on this VM that could plausibly load a nontrivial dataset into memory — production module code
> and one-off scratchpad files alike.** Full incident + agent-facing restatement: `unified-trading-pm/agents/RULES.md`
> § 1.

**The Heavy I/O exemption above is I/O-only — it is NOT a blanket pass for heavy COMPUTE/MEMORY.** The rule above
governs GCS _bandwidth_ from the operator's own laptop and explicitly exempts the human-planning/AO-orchestrator VMs
because they have fast/cheap in-region networking. It says nothing about memory or CPU, and it was never meant to. A
second, separately-scoped guardrail — `QG_MEM_CAP` (`/codex/06-coding-standards/quality-gates-memory-governance.md`) —
caps `pytest`/`basedpyright` subprocesses launched _through_ `quality-gates.sh`, but it does **not** wrap an
agent-authored ad-hoc script run directly (`python3 script.py &`). Neither rule covers that combination, and that gap is
what actually caused an incident.

**Real incident, 2026-07-27**: an ad-hoc scratchpad script (`candle_coverage_gap.py`, a whole-corpus candle-coverage
analysis) was run directly on the shared planning-vm host — not via `quality-gates.sh`, not via any registered VM
launcher. It loaded its working set entirely in memory and grew to **15.8GB RSS over 21 minutes**, driving the shared
host to 24/30GB used with 0GB free and load average 50, which degraded the AO orchestrator's own `/api/state` poll loop
for every slot on the box. It was SIGTERM-killed as a protective action; no worker session or git state was lost, but
the host was one slow poller away from a much worse fleet-wide outage. Two people independently believed a rule already
prevented this (one recalling the I/O rule above, one recalling the QG memory governor) — neither actually did, for the
reasons above; this section closes that specific gap rather than relying on either being stretched to cover it.

**The rule**: before running ANY ad-hoc script directly on the shared planning-vm or AO-orchestrator VM (i.e. not going
through `quality-gates.sh`, and not a registered VM launcher), pick one:

1. **Bound the read.** Use a streamed/chunked/DuckDB-style partial read instead of materializing a whole corpus in
   memory — see `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s DuckDB-over-pandas precedent (the pandas
   concat/sort/dedup OOM'd a 16GiB Cloud Run job the exact same way; DuckDB's out-of-core execution didn't).
2. **Cap it.** If the analysis is genuinely one-off and can't be bounded easily, run it under
   `scripts/dev/run-bounded-analysis.sh` (this repo) — it reuses the exact
   `systemd-run --user --scope -p MemoryMax=... -p MemorySwapMax=0` cgroup mechanism `QG_MEM_CAP` already uses,
   generalized to any command. A process that exceeds the cap dies with exit 137 (verified 2026-07-27 against a live
   planning-vm instance: a 200M cap SIGKILLed a 500MB allocation cleanly, host otherwise unaffected) instead of taking
   the shared host down with it. Default cap is 4G — deliberately smaller than QG's 10G default, since an ad-hoc
   scratchpad script needing more than a few GB is itself a signal it should be option 1 or option 3, not a bigger cap.
3. **Dispatch it.** If it's genuinely corpus-scale and long-running, it isn't an "ad-hoc script" at all — it's exactly
   the class of work the Heavy I/O rule above and the Parallelization Threshold rule below already require on a
   dedicated VM (reuse `launch-canonical-migration-vm.sh` or the generic `VM_MIGRATION_CMD` dispatch; never hand-roll a
   VM name — see the registry rule at the top of this doc).

**What this does NOT change**: the Heavy I/O rule's I/O exemption for the planning/AO-orchestrator VMs stands — GCS
bandwidth from those VMs is still fine. This section adds a second, independent axis (compute/memory), it does not
narrow the first.

**HARD RULE — `canonical-migration-` VMs require ALL THREE liveness signals before any `gcloud compute instances delete`
(codified 2026-08-07, incident:
`/plans/active/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md`).** The standard
two-heuristic check (heartbeat blob stale AND run.log frozen) is INSUFFICIENT for this prefix class. Root cause, proven
in ≥5 kills: the vm-life-emitter heartbeat sidecar is a shell subshell that writes to the stdout/tee pipe; when the GCS
log uploader closes that pipe (typical on a 60-second flush boundary), the next `echo` gets SIGPIPE and the sidecar dies
silently — the heartbeat blob goes stale even though the main Python process is fully alive. Simultaneously, a
`blob.download_as_bytes(timeout=900)` call produces **no log output for its entire duration** (minutes to hours), so
`run.log` is also genuinely frozen — but that frozen state is EXPECTED, not evidence of failure. This combination makes
a live, actively-downloading `canonical-migration-` VM look identically stale to a truly dead one. Fix
`deployment-service@3b25aae4` adds a `trap '' SIGPIPE` guard to the sidecar so future runs survive the pipe close, but
the nuance must be understood for any liveness audit of in-flight VMs.

Before running `gcloud compute instances delete` on any `canonical-migration-*` VM, verify **ALL THREE** signals:

1. **Heartbeat blob mtime** — `vm-heartbeat/<vm>.txt` age vs. the per-prefix threshold (90 min for
   `canonical-migration-` VMs, configured in `heartbeat_stall_watcher.py`'s `PREFIX_KILL_MINUTES`)
2. **run.log mtime** — recent writes = alive; but a **frozen run.log is NOT dispositive** for this prefix class —
   SIGPIPE kills the sidecar AND the download phase produces no output, so frozen-log is expected during a legitimate
   multi-GB GCS download
3. **Manifest generation ID** — is the generation ADVANCING? A generation unchanged for <90 min is EXPECTED during the
   download phase (writes happen only after the full download + filter completes)

**If all three signals read stale AND the manifest generation has been unchanged for >90 min**: do NOT delete
autonomously — escalate for human confirmation. Even with all three stale, the frozen-run.log/sidecar-SIGPIPE failure
mode makes this VM class ambiguous in a way that other prefixes are not. The `agents/infra.md` STEP 0.65 /
`agents/data_engineering.md` STEP 0.55 VM-delete guardrail (the canonical 3-signal rule) applies here as the baseline;
this section adds the `canonical-migration-`-specific nuance that frozen signals are systematically expected in the
large download window.

---

## 1. Infrastructure / Cron VMs

### `launch-vm-zombie-watchdog.sh`

- **When**: Re-deploy after editing `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`. Run once; VM self-perpetuates.
- **Required**: none (uses defaults: `PROJECT_ID`, `ZONE`)
- **Duration**: ~2 min launch + permanent running
- **Failures**: `vm-zombie-watchdog-*` already RUNNING → delete old first. Watchdog has no singleton lock.

### `launch-qg-snapshot-vm.sh`

- **When**: Daily QG snapshot collection (cron). Manual trigger for ad-hoc baseline.
- **Required**: none (env via `DEPLOYMENT_ENV`)
- **Duration**: ~10-15 min
- **Failures**: VM prefix `qg-snapshot-` must be in `VM_PREFIX_TO_BUCKET`. GCS write fails → check bucket
  `deployment-scripts-${PROJECT}` exists.

### `launch-measure-honest-coverage-vm.sh`

- **When**: On-demand honest-coverage measurement. Cloud Scheduler triggers daily (pending IAM for
  `cloudscheduler.jobs.create`).
- **Required**: none
- **Duration**: ~10-15 min
- **Failures**: Coverage JSON not written → check `gs://central-element-323112-honest-coverage/` bucket exists (created
  2026-05-15). Bucket creation: `gsutil mb -l asia-northeast1 gs://central-element-323112-honest-coverage`.

### `launch-honest-coverage-vm.sh`

- **When**: B-018 cron pattern. Same as `launch-measure-honest-coverage-vm.sh` but uses `honest-coverage-` prefix
  (heartbeat-only watchdog registration).
- **Required**: none
- **Duration**: ~10-15 min
- **Failures**: Same as `launch-measure-honest-coverage-vm.sh`.

### `launch-disaster-drill-cron-vm.sh` / `launch-dr-drill-cutover-vm.sh`

- **When**: Disaster recovery drill (quarterly). Human-initiated with explicit operator confirmation.
- **Required**: `--confirm-dr-drill` flag
- **Duration**: ~30-60 min (full failover simulation)
- **Failures**: IAM insufficient → needs `compute.instances.create` + `storage.buckets.*` on DR project.

---

## 2. MTDS (Market Tick Data) Backfill VMs

All MTDS launchers follow the same pattern. `CODE_BUCKET` resolves to `deployment-scripts-${PROJECT}`.

### `launch-mtds-backfill-vm.sh`

- **When**: Backfill market tick data for a date range across all asset groups.
- **Required**: `--asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION>` `--start-date YYYY-MM-DD` `--end-date YYYY-MM-DD`
- **Duration**: 30 min – 4 hours depending on date range + asset group
- **Failures**: Tarballs stale → run `create-code-tarballs.sh --asset-group X` first. BQ quota exceeded → reduce date
  range.
- **⚠️ Not for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET with `--data-types` scoping**: for CeFi on-chain-perp
  venues this launcher's `--operation download` path does NOT honor per-data-type filtering — it silently fetches the
  handler's full data_type set regardless of `--data-types` (confirmed 2026-07-28: a `--data-types trades`-scoped
  HYPERLIQUID run still fetched `book_snapshot_5` + `derivative_ticker`). Use
  `launch-cefi-hl-aster-historical-backfill.sh` instead — see below.

### `launch-cefi-hl-aster-historical-backfill.sh`

- **When**: Backfill CeFi on-chain-perp venues (HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/EXTENDED-STARKNET), especially when
  scoping to specific `DATA_TYPES` — this is the launcher that actually honors per-data-type filtering for these venues
  (via `--operation collect-onchain-perp-batch --onchain-perp-data-types`, purpose-sharded for this workload).
- **Required**: none strictly (`VENUES` defaults to all four; `DATA_TYPES` defaults to
  `trades;book_snapshot_5;derivative_ticker`, env-overridable — the handler auto-excludes per-venue live-only/dropped
  types, e.g. ASTER book/liq are WS-live-only, HL liquidations have no feed at all). Optional finer sharding:
  `SHARD_DAYS=N` (sub-divide each venue's date range into N-day VMs), `OVERRIDE_START_DATE=` / `OVERRIDE_END_DATE=`
  (clamp the window), `YEARS="2025 2026"` (skip already-resolved year-shards on a re-run).
- **Duration**: ~30 min – 3.5h per venue-year on one VM; `SHARD_DAYS` parallelizes across VMs (e.g. the full HL trades
  universe in ~30 min via 21-day shards instead of ~3.5h unsharded).
- **Failures**: HYPERLIQUID auth via `aws-hyperliquid-s3` Secret Manager key (requester-pays S3). Otherwise same pattern
  as other MTDS launchers — see "Other MTDS launchers" below.

### `launch-mtds-perp-funding-backfill-vm.sh`

- **When**: Backfill perp funding rates (CeFi venues).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min/week of data
- **Failures**: Venue API rate limit → reduce date range. Hyperliquid/Bybit credential expiry → Secret Manager check.

### `launch-mtds-dex-pools-backfill-vm.sh`

- **When**: Backfill DeFi DEX pool data (Uniswap, Curve, Balancer).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~1-2 hours/week (on-chain RPC intensive)
- **Failures**: RPC rate limit → verify Alchemy API key via Secret Manager. Pool not found → check UAC DEX registry.

### `launch-mtds-eigenlayer-rewards-backfill-vm.sh`

- **When**: Backfill EigenLayer restaking rewards.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~20-40 min
- **Failures**: EigenLayer API unavailable → check `EIGENLAYER_API_KEY` in Secret Manager.

### `launch-mtds-liquidations-backfill-vm.sh`

- **When**: Backfill on-chain liquidation events.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: RPC node timeout → retry with smaller date range.

### `launch-mtds-pyth-archive-backfill-vm.sh` / `launch-mtds-pyth-lst-backfill-vm.sh`

- **When**: Backfill Pyth price oracle data (Solana). Pyth UNBANNED 2026-05-06.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: Pyth archive endpoint rate limit → uses `PYTH_ARCHIVE_API_KEY` from Secret Manager.

### Other MTDS launchers (same pattern)

`launch-mtds-gas-fees-backfill-vm.sh`, `launch-mtds-gas-fees-fleet-vm.sh`, `launch-mtds-lending-indices-backfill-vm.sh`,
`launch-mtds-lst-rates-backfill-vm.sh`, `launch-mtds-prediction-backfill-vm.sh`,
`launch-mtds-solana-drift-backfill-vm.sh`, `launch-mtds-solana-gas-backfill-vm.sh`,
`launch-mtds-sports-odds-backfill-vm.sh`, `launch-mtds-vault-share-price-backfill-vm.sh`

All: `--start-date` `--end-date` required. Duration 20-90 min. Failure: see MTDS launcher SSOT.

---

## 3. Forward-Poll VMs (Live Mode)

Forward-poll VMs run continuously (no end date). Self-delete on shutdown.

### `launch-cefi-forward-poll.sh`

- **When**: Start live CeFi market data streaming (Binance, Bybit, OKX, etc.).
- **Required**: `--asset-group CEFI`
- **Duration**: Continuous until terminated or VM deleted
- **Failures**: Singleton lock — refuses if `cefi-fwd-*` already RUNNING. Use `--force` to bypass.

### `launch-defi-forward-poll.sh`

- **When**: Start live DeFi data streaming (DEX events, on-chain prices).
- **Required**: `--asset-group DEFI` + Alchemy key in Secret Manager
- **Duration**: Continuous
- **Failures**: RPC provider down → check `WEB3_PROVIDER_URI` derivation from Secret Manager.

### `launch-footystats-forward-poll.sh` / `launch-sfi-forward-poll.sh`

- **When**: Live sports data polling.
- **Required**: API credentials in Secret Manager
- **Duration**: Continuous (match-day driven — typically 4-6 hours/day of active data)
- **Failures**: API key expired → credential rotation required.

### `launch-prediction-forward-poll.sh` / `launch-tradfi-forward-poll.sh`

- **When**: Live prediction markets / TradFi data polling.
- **Required**: Venue credentials in Secret Manager
- **Duration**: Continuous
- **Failures**: Market hours affect data volume (TradFi: NYSE/LSE hours).

---

## 4. Features Backfill VMs

### `launch-features-backfill-vm.sh`

- **When**: Backfill computed features for any asset group.
- **Required**: `--asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION>` `--start-date` `--end-date`
- **Duration**: 1-3 hours/month of data
- **Failures**: Missing MTDS data → run MTDS backfill first. Schema drift → UAC contract check.

### `launch-features-onchain-backfill-vm.sh`

- **When**: Backfill on-chain DeFi features (EigenLayer, LST, DEX).
- **Required**: `--start-date` `--end-date` + Alchemy key
- **Duration**: 2-4 hours/month
- **Failures**: RPC rate limit → reduce parallelism via `--max-workers`.

### `launch-features-sports-backfill-vm.sh` / `launch-features-sports-parallel-backfill-vm.sh`

- **When**: Backfill sports features. Parallel variant fans out per fixture.
- **Required**: `--start-date` `--end-date`
- **Duration**: 1-2 hours for parallel, 4-8 hours for serial
- **Failures**: Footystats API gaps → check manifest `empty_confirmed` entries first.

### `launch-features-vm.sh --feature-family cross_instrument --asset-group PREDICTION`

- **When**: Backfill prediction market features. Formerly `launch-prediction-features-vm.sh` — DELETED 2026-08-09
  (`deployment-service@4150c6c2`; the old script packaged the removed `features-cross-instrument-service` repo and could
  never succeed). `launcher_registry.py`'s `"prediction-features-"` self-heal key now maps to `launch-features-vm.sh`.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~30-60 min
- **Failures**: Polymarket/Kalshi API rate limit → check API key in Secret Manager.

---

## 5. Strategy VMs

### `launch-strategy-test-vm.sh`

- **When**: Full L1-L7 pipeline backtest for a strategy.
- **Required**: `--asset-group` `--strategy <ID>` `--start-date` `--end-date`
- **Optional**: `--mode batch|backtest|paper|live` `--dry-run` `--skip-tarballs`
- **Duration**: 30 min – 4 hours (date range + strategy complexity)
- **Failures**: No backfill-cluster.sh → falls back to e2e script. Coverage: DEPLOYMENT_STARTED/COMPLETED now emitted
  (fixed 2026-05-15 setup-data-pipeline-vm.sh restructure).

### `launch-strategy-live-vm.sh`

- **When**: Live DeFi strategy execution. **Requires `--dry-run-live-cutover-passed` OR `--force-live`**.
- **Required**: `--archetype <carry_staked_basis|arbitrage_price_dispersion>` `--dry-run-live-cutover-passed`
- **Duration**: Continuous until terminated
- **Failures**: Phase 8 dry-run gate not passed → use `--force-live` only with full operator awareness. Wallet key
  required (human-only hard-stop).

### `launch-strategy-paper-vm.sh`

- **When**: Paper trading — live signals, simulated fills.
- **Required**: `--archetype` `--start-date`
- **Duration**: Continuous
- **Failures**: Missing live data → ensure forward-poll VMs running.

### `launch-strategy-backtest-grid-vm.sh`

- **When**: Grid search over strategy parameters.
- **Required**: `--archetype` `--param-grid <json-file>` `--start-date` `--end-date`
- **Duration**: Hours to days depending on grid size
- **Failures**: Grid size exceeds VM memory → use `--shard-index` / `--shard-count` to split.

---

## 6. Validation / Recon VMs

### `launch-amm-golden-fixture-validation-vm.sh`

- **When**: Phase 2 AMM fixture validation. Validates DEX swap fixtures against real on-chain data.
- **Required**: `--shape <UNISWAP_V3|UNISWAP_V4|CURVE_STABLE|...>` OR `--all-shapes`
- **Optional**: `--capture` (fresh RPC capture) `--force` (bypass singleton lock) `--dry-run`
- **Duration**: ~5-15 min/shape; ~45 min for `--all-shapes`
- **Failures**: Alchemy key required for `--capture`. Results:
  `gs://{pid}-defi-validation/results/amm/{date}/{shape}/...`

### `launch-aave-lending-rate-validation-vm.sh`

- **When**: Validate Aave lending rate calculations against on-chain truth.
- **Required**: Alchemy key in Secret Manager
- **Duration**: ~10-20 min
- **Failures**: RPC timeout → retry. Results in `gs://{pid}-defi-validation/results/aave/...`

### `launch-manifest-recon-all-vm.sh` / `launch-manifest-recon-apply-vm.sh`

- **When**: Detect and optionally fix phantom manifest rows.
- **Required**: `--asset-group X` (recon-all) or `--asset-group X --apply` (recon-apply)
- **Duration**: 15-30 min (recon-all); 30-60 min (recon-apply)
- **Failures**: Do NOT apply without recon-all dry-run first. Phantom rows → see
  `reconcile_phantom_manifest_rows_all.py`.

### `launch-defi-phantom-recon-vm.sh`

- **When**: DeFi-specific manifest phantom reconciliation.
- **Required**: `--dry-run` first; then `--apply` once verified
- **Duration**: ~20-40 min
- **Failures**: Same as manifest-recon-apply.

### `launch-batch-live-recon-cron-vm.sh`

- **When**: Daily batch vs live consistency check (cron).
- **Required**: none
- **Duration**: ~15 min
- **Failures**: Mismatches → check batch/live pipeline parity per CLAUDE.md "Live = batch (CRITICAL)".

---

## 7. Instruments / Reference Data VMs

### `launch-instruments-backfill-vm.sh`

- **When**: Backfill instrument reference data (universe, metadata, OHLCV).
- **Required**: `--asset-group` `--start-date` `--end-date`
- **Duration**: 20-60 min
- **Failures**: instruments-service not deployed → deploy first.

### `launch-instruments-smoke-vm.sh`

- **When**: Post-deploy smoke test for instruments-service.
- **Required**: none
- **Duration**: ~10 min
- **Failures**: Schema drift → check UAC instrument contracts.

### `launch-cefi-instruments-backfill.sh`

- **When**: CeFi-specific instrument backfill (exchange listings, contract specs).
- **Required**: `--start-date` `--end-date`
- **Duration**: ~20 min
- **Failures**: Venue API changes → check venue SDK version.

---

## 8. Sports VMs

### `launch-footystats-backfill-vm.sh`

- **When**: Backfill Footystats historical fixture data.
- **Required**: `--start-date` `--end-date` + Footystats API key
- **Duration**: 1-3 hours/season
- **Failures**: API quota → check tier (free = 500 req/day; paid = unlimited). Gaps in known seasons →
  `is_in_known_gap()` check.

### `launch-sports-full-sweep-vm.sh` / `launch-sports-entity-sweep-vm.sh`

- **When**: Full sweep of sports entities (teams, leagues, fixtures).
- **Required**: `--asset-group SPORTS`
- **Duration**: 2-4 hours (full sweep)
- **Failures**: Entity ID drift → reconcile with Transfermarkt/Footystats source IDs.

### `launch-sports-manifest-rescan-vm.sh`

- **When**: Rescan sports manifest for coverage gaps.
- **Required**: `--start-date` `--end-date`
- **Duration**: ~15-30 min
- **Failures**: Phantom rows from old failed runs → run `launch-defi-phantom-recon-vm.sh` first.

### `launch-transfermarkt-backfill-vm.sh` / `launch-understat-backfill-vm.sh`

- **When**: Backfill additional sports data sources.
- **Required**: `--start-date` `--end-date`
- **Duration**: 30-90 min
- **Failures**: Rate limit → use `--delay-ms` parameter.

---

## 9. ML Training VMs

### `launch-ml-training-vm.sh`

- **When**: Train ML models (CatBoost, LightGBM) for signal generation.
- **Required**: `--asset-group` `--model-type <catboost|lightgbm>` `--start-date` `--end-date`
- **Optional**: `--n-trials <N>` for hyperparameter search
- **Duration**: 30 min – 4 hours (model complexity + date range)
- **Failures**: OOM → upgrade to `n2-highmem-8`. catboost_info artifacts → in .gitignore (do not commit).

---

## 10. Admin / Migration VMs

### `launch-canonical-migration-vm.sh`

- **When**: Schema migration across GCS parquet files.
- **Required**: `--asset-group` `--migration-version`
- **Duration**: 1-6 hours (data volume dependent)
- **Failures**: Schema drift detected mid-run → VM reports mismatch to GCS; inspect log before re-running.

### `launch-canonical-smoke-vm.sh`

- **When**: Smoke test canonical schema after migration.
- **Required**: none
- **Duration**: ~10 min
- **Failures**: Schema mismatch → run canonical-migration-vm first.

### `launch-cefi-sharded-backfill.sh`

- **When**: Large CeFi backfill split across multiple VMs (sharded by venue/date).
- **Required**: `--shard-index` `--shard-count` `--start-date` `--end-date`
- **Duration**: 1-3 hours/shard
- **Failures**: Shard count mismatch → all shards must use same `--shard-count`.

### `launch-execution-alpha-vm.sh`

- **When**: Execution alpha testing (latency, fill rate analysis).
- **Required**: `--archetype` `--start-date` `--end-date`
- **Duration**: ~30 min
- **Failures**: Requires execution-service tarball current.

---

## Tardis Concurrent-VM Cap (HARD RULE — operator, 2026-07-16: cap is 1)

**Which VMs count (self-declaring, 2026-07-16)**: a launcher that opens an AUTHENTICATED Tardis (`datasets.tardis.dev`)
connection stamps `VM_TARDIS_CONSUMER=1` into VM metadata and `tardis-concurrency-guard.sh` counts THAT (name patterns
are a rollout fallback only). **Exempt — do NOT stamp, they never consume the licensed slot** (code-verified
2026-07-16): live MTDS `tardis-machine` (a LOCAL `ws://localhost:8002` sidecar over exchanges' own public feeds, no
auth) and instruments-service Tardis (public `api.tardis.dev/v1/exchanges/*` metadata). **Counted**: the cefi sharded
backfill launchers, `launch-mtds-backfill-vm.sh --asset-group CEFI`, and `launch-cefi-forward-poll.sh` — the T+1
forward-poll is `--operation backfill --mode batch` and therefore QUEUES behind a running long backfill (asymmetric by
design: the backfill's own range already covers the recent days the T+1 would fill, so waiting costs nothing, whereas
preempting the multi-day backfill would mean it never finishes).

**Preemption + the cap**: a preempted backfill VM is auto-relaunched by `RelaunchPreemptedVm` **through this guard**, so
a relaunch can never breach the cap — see `spot-vms-for-backfill.md` § "Re-runs cleanly requires a relauncher". **Not
universal**: the cefi sharded backfill launcher specifically has NO working auto-relaunch — measured 5 preemptions
across 8 days, 0 automatic relaunches each time, requiring manual `[INFRA]` relaunch every time (corrected 2026-08-09
per `plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`). Verify `RelaunchPreemptedVm`
actually covers a given launcher before citing this section as proof it self-heals.

**At most 1 Tardis-consuming VM runs at a time, across BOTH clouds (one shared key). The lease does NOT lift the cap —
it AMPLIFIES the failure** (its fail-open path releases every waiting VM to fetch unlocked simultaneously). **This
SUPERSEDES the 2026-07-14 cap of 3**, which was measured while VMs re-walked already-captured 2020 data — skip-scans
barely touch Tardis, so contention looked survivable. It never held for real fetching. Before launching ANY VM that
touches Tardis (cefi sharded backfills, `cefi-queue-*` combined VMs, `mtds-backfill-cefi-*` backfill/pipelinecheck), the
launcher MUST count the running fleet — the shared guard `deployment-service/scripts/vm/tardis-concurrency-guard.sh`
does this (GCP + best-effort AWS) and refuses when `running + planned > 1` (the `TARDIS_MAX_CONCURRENT_VMS` default).
Agents launching manually MUST run the same check.

Empirical basis (2026-07-16, SSOT: `plans/archive/2026_07/cefi_completion_program_2026_07_15.md`): every N>1 datapoint
is a mutual-403 storm once VMs do REAL fetching. N=6 lease-OFF (2026-07-13): all six starved below the 1800s stall
watchdog, zero progress. **N=3 lease-ON in the real gap (2026-07-16): 10,300×403 / 912 ok on one VM, 15,034×403 / ZERO
ok on another, +37,212 FALSE `attempted_failed` rows in 8h, coverage BACKWARD 52.13→48.38.** N=1 (2026-07-16): ZERO
403s, cpu 104%/1600%, rss 7.8GB/128GB. **The false-af rows matter beyond throughput — self-inflicted 403s are recorded
as if the venue refused the data, corrupting the manifest** (cleanup = the 403 re-capture sweep). Scale THROUGHPUT on
the single IP: `SINGLE_VM_QUEUE=1` bundling + `TARDIS_MAX_CONCURRENT_DOWNLOADS` / `TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT`
(defaults 16/4 leave the box ~93% idle; Tardis tolerates ~100-200 concurrent connections, not ~2k) — NEVER more VMs.

Overrides: `FORCE=1` on the sharded launchers (operator-only, accepts collapse risk); `TARDIS_MAX_CONCURRENT_VMS=<n>`
env raises/lowers the cap explicitly. Intra-VM stream concurrency is a separate axis (`TARDIS_MAX_CONCURRENT_DOWNLOADS`,
default 16/VM + `TARDIS_BOOK_SNAPSHOT_MAX_CONCURRENT` 4/VM) — keep the fleet total ≲60 streams (operator guidance
2026-07-14: bundle more shards per VM rather than more VMs).

## Parallelization Threshold for Long-Running VMs (generic rule, 2026-07-24)

**Any VM run expected or observed to exceed a few hours wall-clock must be cross-machine-sharded and/or
intra-machine-parallelized**, unless it is genuinely I/O-bound against a single shared external resource that itself
caps concurrency (the Tardis exception above, generalized — bundling more shards onto fewer VMs beats adding VMs when
the bottleneck is a shared upstream connection limit, not local CPU/GCS-write throughput). This closes a real gap: prior
to this rule, the parallelization obligation only showed up as size-triggered or reactive-to-a-hang callouts on specific
launchers (tradfi/defi both have concrete, measured-but-unapplied parallelization todos — see their consolidated
closeouts), never as a standing runbook-level expectation. A launcher whose typical run exceeds this threshold and has
no sharded/parallel variant is a gap — file it against the owning consolidated-closeout plan (see
`data_pipeline_e2e_milestones_gate_2026_07_24.md` §6 for the per-AG audit todos this rule was written to satisfy).

## Concurrent VMs Sharing a GCS Bucket (HARD RULE, measured 2026-08-10)

**Before launching a VM, check whether another VM is already actively writing to the SAME target bucket**
(`gcloud compute instances list --filter="name~<prefix>"` + a quick `run.log` tail for each hit) — concurrent GCS I/O
against a shared bucket is not free, and the cost lands asymmetrically, not evenly across the fleet.

Real measurement (`defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10`, follow-up I/O-contention test): a
long-running incumbent VM (24 workers, already mid-run against `market-data-tick-defi-prd-*`) held **~227 shards/sec
solo vs. ~209 shards/sec once two more VMs joined the same bucket** — an ~8% dip, within normal noise. The two NEW
8-worker VMs, by contrast, measured **~1,054 shards/sec running solo** (identical settings, isolated same-bucket run)
**vs. only ~120-151 shards/sec running concurrently** with the incumbent + each other — a **~7-9x throughput drop**,
almost certainly GCS per-prefix/API-QPS smoothing under contention.

**Practical rule**: an already-running VM is largely insulated from a newcomer joining its bucket, but each newcomer
absorbs nearly all the contention cost. Horizontal parallel-shard scaling ("N VMs = N x speedup, same total cost") does
**NOT** hold once those VMs share a bucket — a launch plan built on that assumption needs re-costing before you trust
its ETA.

**If launching alongside a co-tenant is unavoidable** (e.g. genuinely separate, non-urgent work), measure the ACTUAL
marginal impact rather than assuming either "no effect" or "linear slowdown": read each VM's own
`date=X: N shards scanned` log-timestamp cadence directly
(`gsutil cat gs://deployment-scripts-.../vm-logs/<vm>/run.log`) for a same-session, low-lag throughput signal. BigQuery
`deployment_operational_data.resource_samples` (`net_recv_rate_bytes_sec` / `io_write_rate_bytes_sec`) carries the same
telemetry but with meaningful ingestion lag (tens of minutes observed) — fine for a post-hoc audit, not for a
same-session live read.

## Common Failure Patterns (All Launchers)

| Failure                                                                                                                                                                   | Diagnosis                                                                                                                                                                                                                                                                                                                              | Fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ERROR: No code tarball found`                                                                                                                                            | Tarballs not uploaded                                                                                                                                                                                                                                                                                                                  | `bash create-code-tarballs.sh --asset-group X`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| VM spins up then immediately exits                                                                                                                                        | Startup script error                                                                                                                                                                                                                                                                                                                   | `gsutil cat gs://.../vm-logs/{VM_NAME}/run.log`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `PERMISSION_DENIED` on GCS write                                                                                                                                          | Missing IAM binding                                                                                                                                                                                                                                                                                                                    | Check VM service account has `storage.objectCreator`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| DEPLOYMENT_STARTED not emitted within 60s                                                                                                                                 | Heartbeat sidecar failed                                                                                                                                                                                                                                                                                                               | Check vm-exec-with-gcs-tee.sh download from GCS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `Unknown VM prefix` in watchdog                                                                                                                                           | New launcher not registered                                                                                                                                                                                                                                                                                                            | Add prefix to `VM_PREFIX_TO_BUCKET` in vm_zombie_watchdog.py                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| VM invisible in deployment-ui/cockpit/Slack (no error at launch)                                                                                                          | Ad hoc name doesn't match any `VM_PREFIX_TO_BUCKET` prefix — silent, not a loud failure                                                                                                                                                                                                                                                | grep the registry BEFORE naming; reuse an existing launcher instead of hand-rolling one                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| VM running >4h (zombie)                                                                                                                                                   | Pipeline hung                                                                                                                                                                                                                                                                                                                          | `gcloud compute instances delete {VM_NAME} --zone={ZONE} --quiet`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Bucket name hardcoded (pre-B-011)                                                                                                                                         | Old launcher style                                                                                                                                                                                                                                                                                                                     | Refactor to `${PROJECT}` pattern per `launcher-script-ssot.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| SC2046 shellcheck warning                                                                                                                                                 | Unquoted flag substitution                                                                                                                                                                                                                                                                                                             | Use `EXTRA_FLAGS=()` array pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `gcloud compute` call fails: "Unable to retrieve Identity Pool subject token" / active account is `github-actions-deploy@…`/`github-deploy@…`, not `unified-trading-sa@…` | The orchestrator VM's shared `~/.config/gcloud` active-account got poisoned by a self-hosted CI job's `google-github-actions/auth` step sharing the same `ubuntu` OS user (see `/plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`) — an authentication failure, not an IAM gap; do NOT grant roles. | Sanctioned stopgap, per-command, no shared-state repoint needed: `gcloud compute … --account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, or for calls that reject `--account=`: prefix with `CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)`. A bare `gcloud config set account unified-trading-sa@…` also works if the ambient pointer flipped but the credential itself is still valid. AO's own Python/ADC-based GCP calls are unaffected regardless (pinned to a dedicated non-shared credential file, `agent-orchestrator/scripts/bootstrap_vm.sh` STEP 5.5, `GOOGLE_APPLICATION_CREDENTIALS=/etc/orchestrator/gcp-sa.json`) — this row is for bare interactive `gcloud`/`gsutil` CLI calls only. |

---

## References

- `/codex/05-infrastructure/launcher-script-ssot.md` — naming, CODE_BUCKET, tarball patterns
- `/codex/05-infrastructure/vm-tarball-deployment.md` — tarball creation + deployment
- `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` — regular preemption + `attempted_failed`
  billing-waste audit contract (`/vm-preemption-billing-waste-audit` skill); run it against every VM class this runbook
  launches
- `plans/audit/results/vm_event_emission_audit_2026_05_15.md` — event emission chain
- `plans/audit/results/vm_security_audit_2026_05_15.md` — shellcheck security audit
- `deployment-service/deployment_service/vm/vm_zombie_watchdog.py` — VM_PREFIX_TO_BUCKET registry
