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
2. **Metadata-driven workload**: `VM_TASK=<cefi-backfill|sports-forward-poll|...>` routes to a specific CLI assembly
   inside `setup-data-pipeline-vm.sh`. Other metadata keys (`VM_SERVICE`, `VM_OPERATION`, `VM_CATEGORY`, `VM_VENUE`,
   `VM_START_DATE`, `VM_END_DATE`, `VM_DATA_TYPES`, `VM_INSTRUMENT_IDS`) feed the CLI.
3. **Tarball fleet in one bucket**: `gs://deployment-scripts-central-element-323112/code/<repo>-code.tar.gz`. One
   tarball per repo. VMs download the tarballs they need based on `VM_SERVICE`.
4. **CORE always present, services opt-in**: `unified-api-contracts`, `unified-trading-library`,
   `market-tick-data-service` (aliased as `mtds-code.tar.gz`), `deployment-service` are always re-tarred. Service repos
   (instruments-service, MDPS, features-\*, etc.) are opt-in via `--category` / `--include` / `--all` flags on
   `create-code-tarballs.sh`.
5. **Python 3.13 mandated**: UAC requires `>=3.13`. Ubuntu 24.04 ships 3.12. The setup script installs 3.13 via
   `deadsnakes` PPA + `python3.13-dev` + `build-essential` (C extensions: `ckzg`, `lru-dict` for web3).
6. **Venv at `/home/ikennaigboaka/venv`**: all `nohup` invocations use the full venv path. `nohup python` without the
   full path fails on Ubuntu 24.04.
7. **Logs tee'd to GCS**: `vm-exec-with-gcs-tee.sh` wraps the workload so stdout/stderr land at
   `gs://deployment-scripts-.../vm-logs/<vm-name>/run.log` for post-mortem. Applies to most (not all) launchers — see
   per-launcher notes.
8. **Same region as GCS data**: `ZONE=asia-northeast1-c` for all data-pipeline VMs. Cross-region transfer cost + latency
   makes this non-negotiable.
9. **`cloud-platform` scope required**: for GCS + Secret Manager access. Every launcher sets this.

Violating any of these means you're doing something off-pattern — document why in the launcher script header.

---

## The tarball fleet — tranche model

`create-code-tarballs.sh` supports four mutually-compatible scopes:

| Flag                                                | Scope                                              | Typical use                                                |
| --------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------- |
| (none)                                              | CORE only — UAC / UTL / MTDS / deployment-service  | UTL-only changes, CORE-only smoke                          |
| `--all`                                             | CORE + every service repo (14+)                    | Multi-repo feature rollouts (e.g. honest-coverage Phase B) |
| `--category CEFI\|TRADFI\|DEFI\|SPORTS\|PREDICTION` | CORE + that category's pipeline repos              | Category-specific rollout                                  |
| `--ml-training`                                     | CORE + ml-training-service + features-\* consumers | ML training runs (any category)                            |
| `--include <repo>`                                  | CORE + the named repo (repeatable)                 | Surgical addition                                          |

**Category-to-repo mappings** are in `create-code-tarballs.sh` as bash arrays (`CEFI_REPOS`, `TRADFI_REPOS`,
`DEFI_REPOS`, `SPORTS_REPOS`, `PREDICTION_REPOS`). Edit the script if you add a new service repo to a category.

**Lesson learned (2026-04-19)**: the bare invocation (no flags) only re-tars CORE. If a change touches any service repo
beyond CORE, **you must use `--all` or a category flag** — forgetting means stale code runs on VMs with no error signal.
The README now calls this out in bold.

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
  --category TRADFI --instruments ES_FRONT \
  --target-types 'swing_high;swing_low' --timeframes 1m \
  --start-date 2022-01-01 --end-date 2025-12-31 \
  --machine high
```

---

## How to debug a failed VM run

```
1. gcloud compute instances list --filter='name~"<vm-name-prefix>"' --format='table(name,status,creationTimestamp.date())'

2. gsutil cat gs://deployment-scripts-.../vm-logs/<vm-name>/run.log | tail -50
   (if the GCS log is empty, VM crashed before vm-exec-with-gcs-tee started — check serial console)

3. gcloud compute instances get-serial-port-output <vm-name> --zone=<zone> | tail -100
   (startup-script boot output; look for apt / uv pip install errors, metadata parsing issues)

4. gcloud compute ssh <vm-name> --zone=<zone> --command="tail -50 /home/ikennaigboaka/logs/backfill.log"
   (local log when GCS log is blocked by IAM)

5. Manifest check (for ingestion VMs):
   gsutil cp gs://<bucket>/_index/availability_index.parquet /tmp/p.parquet
   python -c "import pandas as pd; df = pd.read_parquet('/tmp/p.parquet'); print(df['capture_status'].value_counts())"
```

Honest-coverage schema v5 (see `02-data/availability-manifest-and-data-status.md`) means every attempted shard has a
manifest row: `captured` (data written), `empty_confirmed` (attempted, zero rows), or `attempted_failed` (attempted,
raised — with `error_reason` populated).

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
  `plans/active/proper_coverage_roadmap_2026_04_20.plan.md`
