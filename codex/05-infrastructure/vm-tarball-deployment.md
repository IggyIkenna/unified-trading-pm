---
scope: [engineer, admin]
---

# VM Tarball Deployment — SSOT

**Status**: canonical. All backfill, migration, forward-poll, and smoke VMs in GCE use this pattern. Docker images are
reserved for long-lived production batch workloads (see `runtime-tiers-and-deployment.md` § Cloud Tiers).

**Operational howto SSOT**:
[`deployment-service/scripts/vm/README.md`](../../../deployment-service/scripts/vm/README.md) — this document explains
the **architecture**, **invariants**, and **decision boundaries**; the operational README tells you how to actually run
it.

---

## Why tarballs

The unified trading system uses three deployment patterns:

| Pattern          | When                                          | Startup                        | Code source                                 |
| ---------------- | --------------------------------------------- | ------------------------------ | ------------------------------------------- |
| **Tarball**      | Backfills, migrations, ad-hoc smokes, dev VMs | ~3-5 min (install from source) | `gs://deployment-scripts-.../code/*.tar.gz` |
| **Docker image** | Production batch, auto-scaling                | ~1-2 min (pull image)          | Artifact Registry                           |
| **SSH manual**   | One-off debugging                             | Immediate (existing venv)      | `scp` / `rsync`                             |

**Tarballs beat Docker for backfills** because:

- Backfills iterate faster than a full image build (minutes not tens of minutes)
- They share core dependencies (UAC + UTL + MTDS) across every VM in the fleet, so a single tarball refresh updates 95
  concurrent backfill VMs
- They don't require Artifact Registry permissions / image versioning / pull-rate-limits
- The `setup-data-pipeline-vm.sh` startup script is the one thing VMs fetch — everything else is derived from metadata
  and the tarball fleet

**Tarballs lose to Docker for production** because:

- Each VM runs `uv pip install` at boot — slower cold start
- Ubuntu base image + apt install adds ~2-3 min per VM before any code runs
- No image signing / provenance attestation out-of-the-box

Result: the platform uses tarballs for **ingestion and data pipeline VMs** (backfill, migration, forward-poll, smoke)
and Docker images for **long-lived production services** (strategy-service, execution-service, etc.).

---

## The invariants

Every VM spawned via `launch-*.sh` in `deployment-service/scripts/vm/` obeys these:

1. **One setup script**: every launcher passes
   `startup-script-url=gs://deployment-scripts-.../vm/setup-data-pipeline-vm.sh` in its metadata. This is the **only**
   script that knows how to bring up a VM.
2. **Metadata-driven workload**:
   `VM_TASK=<cefi-backfill|sports-forward-poll|canonical-migration|sports-manifest-rescan|...>` routes to a specific CLI
   assembly inside `setup-data-pipeline-vm.sh`. Other metadata keys (`VM_SERVICE`, `VM_OPERATION`, `VM_CATEGORY`,
   `VM_VENUE`, `VM_START_DATE`, `VM_END_DATE`, `VM_DATA_TYPES`, `VM_INSTRUMENT_IDS`, `VM_MIGRATION_CMD`) feed the CLI.
   `VM_TASK=sports-manifest-rescan` (added 2026-04-21) cd's to `$WORKSPACE/instruments` and runs whatever Python command
   `VM_MIGRATION_CMD` carries — used by `launch-sports-manifest-rescan-vm.sh` to invoke
   `scripts/rescan_sports_fixtures_canonical.py` for the SPORTS FIXTURES per-league index rebuild (see
   `codex/02-data/sports-data-source-coverage-matrix.md` §8, Wave 5 follow-up).
3. **Tarball fleet in one bucket**: `gs://deployment-scripts-central-element-323112/code/<repo>-code.tar.gz`. One
   tarball per repo. VMs download the tarballs they need based on `VM_SERVICE`.
4. **CORE always present, services opt-in**: `unified-api-contracts`, `unified-trading-library`,
   `market-tick-data-service` (aliased as `mtds-code.tar.gz`), `deployment-service` are always re-tarred. Service repos
   (instruments-service, MDPS, features-\*, etc.) are opt-in via `--asset-group` / `--include` / `--all` flags on
   `create-code-tarballs.sh`.
5. **Python 3.13 mandated**: UAC requires `>=3.13`. Ubuntu 24.04 ships 3.12. The setup script installs 3.13 via
   `deadsnakes` PPA + `python3.13-dev` + `build-essential` (C extensions: `ckzg`, `lru-dict` for web3).
6. **Venv at `/home/ikennaigboaka/venv`**: all `nohup` invocations use the full venv path. `nohup python` without the
   full path fails on Ubuntu 24.04.
7. **Observability + lifecycle via wrapper**: Every launcher that routes the workload through `_launch_with_tee` →
   [`vm-exec-with-gcs-tee.sh`](../../../deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh) gets the same guarantees:
   streaming GCS log upload, Firestore-backed `/api/vm-deployments` registration via
   [`heartbeat_cli.py`](../../../deployment-service/deployment_service/vm/heartbeat_cli.py), and optional self-delete
   when `VM_SHUTDOWN_ON_COMPLETION=true` (see § Observability & Lifecycle). **Do not** assume SSH or manual instance
   delete for routine runs.
8. **Same region as GCS data**: `ZONE=asia-northeast1-c` for all data-pipeline VMs. Cross-region transfer cost + latency
   makes this non-negotiable.
9. **`cloud-platform` scope required**: for GCS + Secret Manager access. Every launcher sets this.

Violating any of these means you're doing something off-pattern — document why in the launcher script header.

---

## The tarball fleet — tranche model

`create-code-tarballs.sh` supports four mutually-compatible scopes:

| Flag                                                   | Scope                                              | Typical use                                                |
| ------------------------------------------------------ | -------------------------------------------------- | ---------------------------------------------------------- |
| (none)                                                 | CORE only — UAC / UTL / MTDS / deployment-service  | UTL-only changes, CORE-only smoke                          |
| `--all`                                                | CORE + every service repo (14+)                    | Multi-repo feature rollouts (e.g. honest-coverage Phase B) |
| `--asset-group CEFI\|TRADFI\|DEFI\|SPORTS\|PREDICTION` | CORE + that category's pipeline repos              | Category-specific rollout                                  |
| `--ml-training`                                        | CORE + ml-training-service + features-\* consumers | ML training runs (any category)                            |
| `--include <repo>`                                     | CORE + the named repo (repeatable)                 | Surgical addition                                          |

**Category-to-repo mappings** are in `create-code-tarballs.sh` as bash arrays (`CEFI_REPOS`, `TRADFI_REPOS`,
`DEFI_REPOS`, `SPORTS_REPOS`, `PREDICTION_REPOS`). Edit the script if you add a new service repo to a category.

**Lesson learned (2026-04-19)**: the bare invocation (no flags) only re-tars CORE. If a change touches any service repo
beyond CORE, **you must use `--all` or a category flag** — forgetting means stale code runs on VMs with no error signal.
The README now calls this out in bold.

**features-service consolidation (2026-05-08)**: the 8 prior `features-*-service` repos collapse to a single
[`features-service`](../../../features-service/) repo (sub-packages per family). Tarball implications:

- `--asset-group CEFI|DEFI|TRADFI|SPORTS|PREDICTION` now includes the single `features-service/` repo (rather than the 8
  prior `features-*-service` repos). The category-to-repo bash arrays in `create-code-tarballs.sh` reflect this on Phase
  8A landing.
- VM boot invocation changes from `python -m features_<X>_service ...` (8 distinct entry-points) to
  `python -m features_service --feature-family <X> ...` (single CLI dispatcher).
- The `features-` VM prefix in `VM_PREFIX_TO_BUCKET` is registered ONCE for the consolidated launcher (replacing 8
  per-family prefixes that would otherwise drift).
- Architecture SSOT:
  [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

---

## The tarball refresh cycle

Every time service code is committed to `live-defi-rollout`:

```
1. git push (commit + hooks + push)
2. bash deployment-service/scripts/vm/create-code-tarballs.sh <scope flag>
   ├─ Creates tar.gz per repo in local TMP_DIR (excludes .git, .venv, node_modules, __pycache__, coverage, .terraform, etc.)
   ├─ Uploads to gs://.../code/<repo>-code.tar.gz (gsutil -m cp, parallel)
   └─ Re-uploads gs://.../vm/setup-data-pipeline-vm.sh (so launchers fetch the latest boot script)
3. Subsequent `launch-*.sh` invocations launch VMs that fetch the fresh tarballs at boot
```

VMs launched **before** step 2 still run the stale code. Check the tarball timestamp
(`gsutil ls -l gs://.../code/<repo>-code.tar.gz`) against your commit time before firing a smoke.

---

## Singleton-locked launchers (2026-04-20)

Three launchers enforce singleton locks to prevent rate-limit thundering herds against shared API keys / quotas:

- `launch-sfi-forward-poll.sh` — SFI/RapidAPI rate-limits per-key; 10 concurrent VMs thrash on 429 backoffs and produce
  no useful data. Lock: refuses launch if any `sfi-fwd-*` VM is RUNNING in the zone. `--force` bypass.
- `launch-mtds-prediction-backfill-vm.sh` — Polymarket gamma rate-limits per-IP; concurrent VMs share the project egress
  NAT. Same lock pattern. `--force` bypass.
- `launch-tradfi-backfill-vm.sh` (2026-04-20, CME Tier 1 Phase A) — Databento account is shared across the team;
  concurrent VMs on wide windows risk contract-exceeded errors. Lock: refuses launch if any `tradfi-bf-*` VM is RUNNING
  in the zone. `--force` bypass. Shards CME ES expiries year-by-year 2022-2026 (4 quarterly contracts per year on
  `CME:FUTURE:ES-YYYYMMDD`). Default `VM_DATA_TYPES=ohlcv_1m;trades`; override with `--data-types`. Override instruments
  with `--instrument-ids 'CME:FUTURE:ES-20260619;...'`. Machine `e2-standard-4` per shard.

Incident reference: `memory/project_session_handover_2026_04_19.md` + the 2026-04-19 SFI herd that produced ~4
successful writes across 10 VMs in 6 hours.

**If you build a new launcher for a rate-limited adapter**: copy the singleton-lock pattern from the three above, not
just the `gcloud compute instances create` boilerplate.

---

## ML training launcher (non-singleton, 2026-04-20)

`launch-ml-training-vm.sh` (CME Tier 1 Phase A) — trains a single ml-training-service
instrument×target×timeframe×model-family combination on GCE, writing the artefact to the ml model_registry in GCS.

- **Not singleton-locked** — parallel training is expected (different instruments, different target types, different
  hyper-param grids). ml-training-service does not share a rate-limited API key; it reads feature parquet + fits models
  locally.
- Machine choice via `--machine cpu|high|gpu`:
  - `cpu` (default) → `n2-highmem-8` (64 GB RAM). Enough for LightGBM / XGBoost / CatBoost on 5-year 1-minute data.
  - `high` → `n2-highmem-16` (128 GB RAM). For larger hyper-param grids / Optuna multi-trial runs.
  - `gpu` → `n1-standard-8` + 1×T4 (~$0.35/h). Only when the harness config uses a GPU-enabled booster. Most
    `swing_high` / `swing_low` models are fine on CPU.
- Tarballs: prep with `bash create-code-tarballs.sh --ml-training` (CORE + ml-training-service + features-\* consumers).
- Routing: launcher passes `VM_TASK=features-backfill` + `VM_BACKFILL_CMD="python -m ml_training_service ..."`, reusing
  the features-backfill branch of `setup-data-pipeline-vm.sh` which already handles verbatim command execution (Phase B
  will add a dedicated `VM_TASK=ml-training` branch).
- Observability: inherits the `STALL_TIMEOUT_SEC=600` log-mtime watchdog + `timeout 30s` run_heartbeat + py-spy stack
  dump + pkill-by-name fallback from `vm-exec-with-gcs-tee.sh` (deployed 2026-04-19 after the VM silent-hang class bug).

Typical CME S&P 500 ML Tier 1 MVP invocation (once Phase B stitches the continuous ES series):

```bash
bash launch-ml-training-vm.sh \
  --asset-group TRADFI --instruments ES_FRONT \
  --target-types 'swing_high;swing_low' --timeframes 1m \
  --start-date 2022-01-01 --end-date 2025-12-31 \
  --machine high
```

---

## How to debug a failed VM run

```
1. gcloud compute instances list --filter='name~"<vm-name-prefix>"' --format='table(name,status,creationTimestamp.date())'

2. gsutil cat gs://deployment-scripts-.../vm-logs/<vm-name>/EXIT_STATUS
   (one-line file: "[vm-exec] command exited rc=<N>". Absent ⇒ VM still running OR crashed before
   vm-exec-with-gcs-tee captured rc. See "Exit codes" below for rc semantics.)

3. gsutil cat gs://deployment-scripts-.../vm-logs/<vm-name>/run.log | tail -50
   (if the GCS log is empty, VM crashed before vm-exec-with-gcs-tee started — check serial console)

4. gcloud compute instances get-serial-port-output <vm-name> --zone=<zone> | tail -100
   (startup-script boot output; look for apt / uv pip install errors, metadata parsing issues)

5. gcloud compute instances describe <vm-name> --zone=<zone> --format='yaml(metadata.items)'
   (resolve VM name → workload: VM_START_DATE / VM_END_DATE / VM_TASK / VM_OPERATION /
   VM_ASSET_GROUP. The launcher injects these; they are the SSOT for what the VM was assigned.)

6. Kernel-side OOM signal (rc=137 root cause):
   gcloud logging read 'resource.type="gce_instance"
       AND labels."compute.googleapis.com/resource_name"=~"<vm-name-prefix>"
       AND textPayload=~"OOM"' --limit=20 --freshness=4h
   (systemd OOM-killer messages are kernel-level — they do NOT appear in run.log because
   atexit / signal handlers don't fire on SIGKILL. Cloud Logging is the only place to see them.)

7. gcloud compute ssh <vm-name> --zone=<zone> --command="tail -50 /home/ikennaigboaka/logs/backfill.log"
   (local log when GCS log is blocked by IAM, or VM has VM_SHUTDOWN_ON_COMPLETION=false for
   post-mortem SSH)

8. Manifest check (for ingestion VMs):
   gsutil cp gs://<bucket>/_index/availability_index.parquet /tmp/p.parquet
   python -c "import pandas as pd; df = pd.read_parquet('/tmp/p.parquet'); print(df['capture_status'].value_counts())"
```

Honest-coverage `capture_status` taxonomy (introduced at schema v5; current schema v7 — see
`02-data/availability-manifest-and-data-status.md`) means every attempted shard has a manifest row: `captured` (data
written), `empty_confirmed` (attempted, zero rows), or `attempted_failed` (attempted, raised — with `error_reason`
populated).

### Exit codes

The `EXIT_STATUS` file written by `vm-exec-with-gcs-tee.sh` carries the workload's return code. Standard POSIX rc
semantics — useful subset for diagnosing CeFi / TradFi backfill VMs:

| `rc=` | Cause                                                                                                                                                                                                | Where to look                                                                                                                             |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `0`   | Clean exit. Workload returned successfully (real backfill done OR future-week skip OR full skip-existing).                                                                                           | `run.log` last 30 lines + `DEPLOYMENT_COMPLETED` event                                                                                    |
| `1`   | Generic Python exception that escaped the orchestrator.                                                                                                                                              | `run.log` traceback                                                                                                                       |
| `130` | SIGINT (operator Ctrl-C or `gcloud compute instances stop`).                                                                                                                                         | Operator action — usually intentional                                                                                                     |
| `137` | **SIGKILL — almost always systemd OOM-killer.** The Python process never gets a signal handler chance, so `atexit` flush + `DEPLOYMENT_FAILED` archive **do NOT fire**. `run.log` ends mid-sentence. | Step 6 above (kernel logs). Then size the next VM via `market_tick_data_service/engine/shard_memory_profile.py::recommended_machine_type` |
| `143` | SIGTERM (`gcloud compute instances delete` or shutdown initiated).                                                                                                                                   | Cloud Logging instance lifecycle                                                                                                          |
| `124` | Timeout (script-side `timeout` wrapper exceeded).                                                                                                                                                    | Bump timeout or split shard                                                                                                               |

A rc=137 with no `OOM` line in `run.log` and no `DEPLOYMENT_FAILED` event in the deployment registry is the canonical
signature of a memory-blown shard — diagnose via kernel logs, not the workload log.

---

## Observability & Lifecycle

**Provenance:** `deployment-service` commits `cc07649` (startup script downloads `heartbeat_daemon.py` to `/tmp/` — the
daemon was previously missing, so Pub/Sub, GCS log streaming, and registry writes never started) and `beaa2e5`
(`vm-exec-with-gcs-tee.sh` reads `VM_SHUTDOWN_ON_COMPLETION` and self-deletes the VM after the workload exits).
Together, every VM launched via `launch-*.sh` inherits full lifecycle observability **without SSH** through the shared
wrapper — not per-launcher one-offs.

### Three guarantees

1. **Streaming GCS log + EXIT_STATUS** — The heartbeat daemon uploads the task log under
   `/home/ikennaigboaka/logs/<task>.log` to `gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log`
   on a ~30s cadence. Operators inspect progress by re-fetching the object (GCS is not a live `tail -f` — diff
   successive `gsutil cat` pulls). On workload exit, `vm-exec-with-gcs-tee.sh` writes a sibling
   `gs://.../vm-logs/<vm-name>/EXIT_STATUS` containing one line `[vm-exec] command exited rc=<N>` — the cheapest way to
   bulk-classify completed VMs without reading every full log. Note: rc=137 (SIGKILL/OOM) **does not produce an
   EXIT_STATUS file** — the Python process is killed before the wrapper captures rc. Absent EXIT_STATUS + truncated
   run.log = OOM signature.

2. **Deployment registry** — At boot, the heartbeat CLI emits a REGISTER event; heartbeats every ~60s keep
   `status=running`; exit archives `DEPLOYMENT_COMPLETED` or `DEPLOYMENT_FAILED`. The registry lives in GCS at
   `gs://deployment-scripts-central-element-323112/deployments/active/<deployment_id>.json` (live VMs) and
   `deployments/archive/<YYYY-MM-DD>/<deployment_id>.json` (terminated). Query via deployment-api route
   [`vm_deployments.py`](../../../deployment-api/deployment_api/routes/vm_deployments.py): e.g.
   `curl -sS 'https://<deployment-api-host>/api/vm-deployments?status=running' | jq` — the API surface IS the
   programmatic canonical. The raw GCS JSONs are inspectable but the API is what dashboards consume.

3. **Self-delete on completion** — VM metadata `VM_SHUTDOWN_ON_COMPLETION=true` triggers
   `gcloud compute instances delete --self --delete-disks=all` in a detached subshell after the workload return code is
   captured. Launchers set this by default; omit it only for post-mortem SSH (rare).

### Workload identity — VM metadata keys

The launcher injects identity via GCE instance metadata (visible to the VM as
`/computeMetadata/v1/instance/attributes/`, visible to operators via
`gcloud compute instances describe ... --format='yaml(metadata.items)'`). For ingestion VMs:

| Key                             | Meaning                                                 | Example                                                                  |
| ------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------ |
| `VM_TASK`                       | Workload identifier — drives setup-script branching     | `cefi-backfill`, `tradfi-backfill`, `mdps-backfill`, `mtds-forward-poll` |
| `VM_OPERATION`                  | Service CLI `--operation` value                         | `download`, `process`, `forward-poll`                                    |
| `VM_ASSET_GROUP`                | Service CLI `--asset-group` value (uppercase canonical) | `CEFI`, `TRADFI`, `DEFI`, `SPORTS`, `PREDICTION`                         |
| `VM_START_DATE` / `VM_END_DATE` | Date range (ISO format) the VM was assigned             | `2020-01-06` / `2020-01-12`                                              |
| `VM_SHUTDOWN_ON_COMPLETION`     | If `true`, self-delete after rc captured                | `true` (default) / `false` (post-mortem mode)                            |
| `MANIFEST_PER_VM_SHARDS`        | Legacy flag — should be `true` for all new launchers    | `true`                                                                   |

These metadata keys are the SSOT for "what was this VM assigned to do" — the run.log can be inspected for what it
_actually_ did, but the metadata says what it was _supposed_ to do.

### How it works

```
Launcher (launch-*.sh)
    │
    └── gcloud compute instances create
            └── startup-script-url=gs://.../vm/setup-data-pipeline-vm.sh
                    │
                    ├── installs Python + tarballs (this doc, above)
                    ├── downloads /tmp/vm-exec-with-gcs-tee.sh (cc07649)
                    ├── downloads /tmp/deployment_heartbeat.py
                    ├── downloads /tmp/heartbeat_daemon.py (cc07649)
                    └── _launch_with_tee <cmd>
                            │
                            └── vm-exec-with-gcs-tee.sh
                                    ├── forks heartbeat_daemon.py (~60s heartbeat + ~30s GCS log)
                                    ├── runs <cmd>, captures rc
                                    ├── daemon archives DEPLOYMENT_COMPLETED | FAILED
                                    └── self-delete if VM_SHUTDOWN_ON_COMPLETION=true (beaa2e5)
```

### What this replaced

Before 2026-04-21, the daemon file was not present on the VM: wrappers logged that observability was disabled, **no**
`/api/vm-deployments` rows appeared, **no** streaming GCS log landed, and **`VM_SHUTDOWN_ON_COMPLETION` was never read**
— instances stayed RUNNING after rc=0 until manual `gcloud compute instances delete`. Operators relied on SSH + local
tail

- manual cleanup.

### Implementation references

- Wrapper (uploaded to `gs://.../vm/`):
  [`deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`](../../../deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh)
- Heartbeat / daemon:
  [`deployment-service/deployment_service/vm/heartbeat_cli.py`](../../../deployment-service/deployment_service/vm/heartbeat_cli.py)

---

## Manifest consolidator daemon (2026-04-29)

**Launcher:**
[`deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh`](../../../deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh)

A long-lived `e2-small` daemon (~$12/mo) that polls the UTL manifest consolidator on every asset_group bucket every 60s.
Purpose: keep `_index/availability_index.parquet` fresh in each `instruments-store-*` bucket so the UTL reader's 120s
freshness fallback doesn't truncate readers (deployment-api data-status, FSS reader, downstream services) to a
per-VM-shards-only view.

**Architecture (manifest-429 phase 6/7):**

- VMs writing to the manifest write to `_index/per_vm/<vm_name>.parquet` shards (avoids canonical write contention).
- A consolidator periodically reads canonical + all per_vm shards, dedups on the row-key tuple, writes back to
  canonical.
- The UTL reader has a 120s freshness threshold — if canonical is stale, falls back to per_vm shards only. So if the
  consolidator stops running, readers see a partial view.

**Why VM not Cloud Run Job:** Plans 12 + 13 blockers on deployment-service image build + UTL base image. VM uses the
tarball infra (UAC + UTL + deployment-service already on GCS) and runs the consolidator's CLI in a bash poll loop.

**In-VM command shape** (assembled by `setup-data-pipeline-vm.sh` from `VM_TASK=manifest-consolidator-poll`):

```bash
while true; do
  for bucket in $BUCKETS; do
    python -m unified_trading_library.manifest_consolidator --bucket $bucket --once
  done
  sleep $POLL_INTERVAL
done
```

Default buckets: `instruments-store-{sports,cefi,defi,tradfi,prediction}-PROJECT_ID`. Default poll: 60s.

**Singleton lock:** the launcher refuses to start if any `manifest-consolidator-*` VM is RUNNING in the zone (multiple
would race on the consolidator's sentinel-lock and waste API calls). One daemon per zone is sufficient.

**Metadata encoding gotcha:** the launcher encodes the buckets list with `:` separator (not `,`) because gcloud's
`--metadata=KEY=VAL,KEY2=VAL2` parser splits top-level pairs on commas. The setup script converts `:` back to spaces for
the bash loop.

**UTL bug fix prerequisite (2026-04-29):** the consolidator had a `BlobMetadata` filter bug in `_read_per_vm_shards`
(filtered with `isinstance(p, str)` against `list_blobs` results which are `BlobMetadata` objects) → silently reported
`shards_scanned: 0`. Fixed in `unified-trading-library/unified_trading_library/manifest_consolidator.py` — extract
`.name` attribute from BlobMetadata before path filter. The daemon needs the post-fix UTL tarball to actually do work.

**Operations:**

```bash
bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh                    # all 5 asset_group buckets, 60s poll
bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh --interval 30      # 30s poll
bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh --buckets BUCKET1,BUCKET2  # custom subset
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/manifest-consolidator-<TS>/run.log  # tail logs
gcloud compute instances delete manifest-consolidator-<TS> --zone=asia-northeast1-c --quiet  # stop
```

**SSOT cross-refs:**

- [`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) "Manifest
  consolidator + per_vm shard merge mechanics"
- UTL CLI: `python -m unified_trading_library.manifest_consolidator --bucket <X> --once`

---

## Cross-references

- Operational howto: [`deployment-service/scripts/vm/README.md`](../../../deployment-service/scripts/vm/README.md)
- Runtime topology tiers: [`runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md)
- Setup script source:
  [`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`](../../../deployment-service/scripts/vm/setup-data-pipeline-vm.sh)
- Tarball bucket: `gs://deployment-scripts-central-element-323112/code/`
- Setup script bucket: `gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh`
- Honest-coverage manifest schema (what VMs write on success/empty/failure):
  [`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Shard-level failure isolation (why VMs don't raise inside per-venue loops):
  [`04-architecture/shard-level-failure-isolation.md`](../04-architecture/shard-level-failure-isolation.md)
- Coverage roadmap (how to use VM tarball deployment to reach ~100% honest coverage):
  `plans/archive/proper_coverage_roadmap_2026_04_20.plan.md`
