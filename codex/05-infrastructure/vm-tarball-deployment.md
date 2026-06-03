---
scope: [engineer, admin]
last_reviewed: 2026-05-17
owner: deployment-platform
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

0. **`lifecycle_class` MANDATORY (Phase A.2)**: every non-`None` entry in `VM_PREFIX_TO_BUCKET` in
   `vm_zombie_watchdog.py` MUST be a `VmPrefixSpec(bucket=..., lifecycle_class=LifecycleClass.<MEMBER>)`. The four valid
   `LifecycleClass` members are:
   - `EPHEMERAL_BATCH` — short-lived data pipeline VM (backfill, migration, smoke); self-deletes on completion
   - `EPHEMERAL_EXPERIMENT` — experiment VM with run_id in name: `{prefix}{run_id}-{ts}` (e.g.
     `exp-ml-{uuidv7}-{yyyymmdd}`); reserved prefixes: `exp-ml-`, `exp-strategy-`, `exp-execution-`
   - `SCHEDULED_RECURRING` — VM launched by a cron (forward-poll, scheduled backfill sweeps)
   - `LONG_LIVED_LIVE` — daemon VM with no expected self-termination (orchestrator, zombie-watchdog, cron-scheduler)

   Missing or bare-string entries are caught by `validate_vm_prefix_mapping.py` and are review-blocking.

1. **Two valid startup patterns** (codified O-18, 2026-05-21):
   - **Pattern A — canonical tarball (data pipeline VMs)**: launcher passes
     `startup-script-url=gs://deployment-scripts-.../vm/setup-data-pipeline-vm.sh` in its metadata.
     `setup-data-pipeline-vm.sh` installs Python 3.13 via `uv`, fetches code tarballs, and routes to the workload CLI
     via `VM_TASK`. Used for: backfill, migration, forward-poll, smoke VMs. This is the default pattern for any VM that
     writes manifest rows or runs a service CLI.
   - **Pattern B — inline startup (daemon / orchestrator / validator VMs)**: launcher writes an inline `STARTUP_FILE`
     heredoc and passes it via `--metadata-from-file=startup-script=`. Used ONLY for VMs that install cron jobs, run
     long-lived FastAPI daemons, or perform heartbeat-only validation without manifest writes (e.g.
     `launch-cefi-fwd-daily-cron-vm.sh`, `launch-planning-vm.sh`, `launch-aave-lending-rate-validation-vm.sh`). These
     VMs do NOT fetch tarballs or use `VM_TASK` routing.

   **Both patterns MUST guarantee** the shard-isolation + observability invariants (2, 7–9). Pattern A satisfies them
   via `setup-data-pipeline-vm.sh`'s built-in machinery. Pattern B launchers wire them explicitly via
   `lib/launcher_common.sh` helpers. Using Pattern B for a data pipeline VM without explicit justification in the
   launcher header is off-pattern. See § "Launcher pattern decision matrix" below.

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
   `uv python install 3.13` (updated 2026-05-21 — the deadsnakes PPA path is stale and must not be used). `apt` still
   installs `build-essential` + `python3.13-dev` before the `uv` step for C-extension builds (`ckzg`, `lru-dict` for
   web3). Pattern B inline launchers that install Python independently must use the same `uv`-based path.
6. **Venv at `/home/ikennaigboaka/venv`**: all `nohup` invocations use the full venv path. `nohup python` without the
   full path fails on Ubuntu 24.04.
7. **Observability + lifecycle — two tiers** (matches the two startup patterns):
   - **Pattern A (canonical)**: `setup-data-pipeline-vm.sh` routes every workload through `_launch_with_tee` →
     [`vm-exec-with-gcs-tee.sh`](../../../deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh), providing: streaming
     GCS log + EXIT_STATUS file, deployment-registry heartbeats via
     [`heartbeat_cli.py`](../../../deployment-service/deployment_service/vm/heartbeat_cli.py), stall watchdog, and
     self-delete on `VM_SHUTDOWN_ON_COMPLETION=true`. Full lifecycle visibility without SSH (see § Observability &
     Lifecycle).
   - **Pattern B (inline)**: launcher sources `lib/launcher_common.sh` and includes `lc_log_upload_trap_block` for
     lightweight GCS log upload on EXIT. No heartbeat daemon, no deployment-registry rows. Pattern B VMs are either
     `LONG_LIVED_LIVE` daemons (monitored by the zombie watchdog) or heartbeat-only validators with no manifest writes.

   **Do not** assume SSH or manual instance delete for Pattern A runs.

8. **Same region as GCS data**: `ZONE=asia-northeast1-c` (default) for all data-pipeline VMs. Cross-region transfer
   cost + latency makes this non-negotiable. **STOCKOUT fallback**: if `-c` reports STOCKOUT, retry in
   `asia-northeast1-b` or `asia-northeast1-a` — same region, zero cross-region egress. NEVER fall back to a different
   region (e.g. `us-central1`). Incident: 2026-05-19 defi-2022 was briefly created in `us-central1-a` before being
   caught and moved back to `asia-northeast1-b`.
9. **`cloud-platform` scope required**: for GCS + Secret Manager access. Every launcher sets this.

10. **Per-shard cleanup discipline for multi-shard VMs** (HARD RULE, codified 2026-05-28). An `EPHEMERAL_BATCH` VM does
    **not** mean "one shard per VM". It means the VM is short-lived (self-deletes on completion) — but inside its Python
    process, the service CLI may iterate many shards (a date range, a venue list, a data_type list) before exit. A
    16-day narrow-scope backfill on one `EPHEMERAL_BATCH` VM processes 16 (or more) atomic shards in one process; an
    asset-group-wide sharded backfill VM processes thousands. Every service that runs on a multi-shard VM MUST wire a
    per-shard cleanup hook in its orchestrator that fires on **every exit path** of per-shard work (success, skip,
    raised exception). Without this, per-shard state (caches, lazy reference DataFrames, manifest buffers) compounds
    shard-over-shard and the VM swap-deadlocks long before its work completes.

    The implementation contract for the per-shard cleanup hook lives in
    [`codex/06-coding-standards/service-orchestration-patterns.md`](../06-coding-standards/service-orchestration-patterns.md)
    § 15 "Batch Service Lifecycle: Setup, Work, Cleanup". The contract is enforced at code-review time, not VM-launch
    time — the launcher cannot tell whether the service it runs has its cleanup hook wired. **Reference incident**:
    2026-05-28 MDPS 7-day backfill on `e2-standard-8` — the `_cleanup_after_day` hook existed but was only wired into
    the early-exit branch; day 1 completed, day 2 OOM'd at the date-boundary because the day-1 candle/sampling caches
    were still pinned. 25 GB per-day floor measured empirically. Plan:
    [`plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](../../plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md)
    § "Finding A" + § "Finding C".

    **Granularity note (composes with `cli-convention.md` § "Instrument Identity and CLI Granularity")**: the atomic
    shard is `(asset_group, venue, instrument_type, data_type, symbol, date)`. A multi-shard VM may iterate any subset
    of those axes inside its process. The cleanup hook attaches at whichever axis the service's per-shard orchestrator
    wraps — typically per (date, asset_group) for daily backfills, per (date, asset_group, data_type) for finer-grain
    services. The single-shard drilldown case (one date × one instrument × one data_type) MUST still call cleanup on
    exit; the cleanup path being silently dead in the most-restricted invocation is exactly how the MDPS incident
    landed.

Violating any of these means you're doing something off-pattern — document why in the launcher script header.

---

## Launcher pattern decision matrix (O-18, 2026-05-21)

Use this table to decide which startup pattern to use when writing a new `launch-*.sh` launcher:

| Workload type                                                      | Pattern | Rationale                                                                                     |
| ------------------------------------------------------------------ | ------- | --------------------------------------------------------------------------------------------- |
| Backfill VM (service CLI, writes manifest rows)                    | A       | Needs tarball install + `VM_TASK` routing + full observability via `vm-exec-with-gcs-tee.sh`. |
| Migration VM (runs a migration script, writes manifest rows)       | A       | Same as backfill; `VM_TASK=canonical-migration` or custom handler.                            |
| Forward-poll VM (recurring ingestion, writes manifest rows)        | A       | Same as backfill.                                                                             |
| Smoke / ad-hoc data VM (runs a service CLI, writes manifest rows)  | A       | Same as backfill.                                                                             |
| Cron scheduler VM (installs crontab, fires launchers periodically) | B       | No manifest writes; startup wires cron job, not a service CLI. Long-lived daemon.             |
| Orchestrator VM (runs FastAPI dashboard, LONG_LIVED_LIVE)          | B       | Clones agent-orchestrator, starts server — not a tarball workflow.                            |
| Validation VM (heartbeat-only, no manifest writes)                 | B       | No tarballs needed; validates external data but doesn't write to instruments-store.           |
| Zombie watchdog VM (reads manifests, no writes)                    | B       | Long-lived daemon; reads GCS/manifest but doesn't write.                                      |

**Pattern B invariants (what every inline launcher MUST wire manually):**

- `MANIFEST_PER_VM_SHARDS=true` in `--metadata` (omit ONLY if VM provably makes zero manifest writes — document this).
- `VM_NAME=${VM_NAME}` in `--metadata` for per-VM log identity.
- `VM_SHUTDOWN_ON_COMPLETION` set appropriately (`true` for one-shot, `false` for LONG_LIVED_LIVE daemons).
- Source `lib/launcher_common.sh` and call `lc_log_upload_trap_block` for GCS log upload on EXIT.
- Header comment MUST document: why Pattern B is used + which of the above invariants are intentionally absent + reason.

**Pattern B known exceptions (intentionally missing invariants, documented at script header):**

| Launcher                                         | Missing invariant        | Reason                                                                       |
| ------------------------------------------------ | ------------------------ | ---------------------------------------------------------------------------- |
| `launch-aave-lending-rate-validation-vm.sh`      | `MANIFEST_PER_VM_SHARDS` | Heartbeat-only; no manifest writes                                           |
| `launch-amm-golden-fixture-validation-vm.sh`     | `MANIFEST_PER_VM_SHARDS` | Heartbeat-only; no manifest writes                                           |
| `launch-cefi-fwd-daily-cron-vm.sh`               | `MANIFEST_PER_VM_SHARDS` | Cron daemon; no direct manifest writes                                       |
| `launch-tradfi-fwd-daily-cron-vm.sh`             | `MANIFEST_PER_VM_SHARDS` | Cron daemon; no direct manifest writes                                       |
| `launch-planning-vm.sh`                          | `MANIFEST_PER_VM_SHARDS` | Orchestrator daemon; no manifest writes                                      |
| `launch-epic-vm.sh`                              | startup-script-url       | Agent-orchestrator epic VM; boots long-lived orchestrator service            |
| `launch-vm-zombie-watchdog.sh`                   | startup-script-url       | Always-on daemon; polls GCS heartbeats every 5 min                           |
| `launch-prediction-features-vm.sh`               | startup-script-url       | SUPERSEDED by Pattern-A `launch-features-vm.sh`; keep until archived         |
| `launch-features-sports-parallel-backfill-vm.sh` | startup-script-url       | SUPERSEDED by Pattern-A `launch-features-vm.sh`; keep until archived         |
| `launch-prediction-pipeline-vm.sh`               | startup-script-url       | 3-service sequential pipeline; multi-stage handler exceeds complexity budget |
| `launch-gcs-migration-bundle-vm.sh`              | startup-script-url       | Per-run GCS script staging; PM migration script not in any service tarball   |

---

## The tarball fleet — tranche model

`create-code-tarballs.sh` supports four mutually-compatible scopes:

| Flag                                                   | Scope                                             | Typical use                                                |
| ------------------------------------------------------ | ------------------------------------------------- | ---------------------------------------------------------- |
| (none)                                                 | CORE only — UAC / UTL / MTDS / deployment-service | UTL-only changes, CORE-only smoke                          |
| `--all`                                                | CORE + every service repo (14+)                   | Multi-repo feature rollouts (e.g. honest-coverage Phase B) |
| `--asset-group CEFI\|TRADFI\|DEFI\|SPORTS\|PREDICTION` | CORE + that category's pipeline repos             | Category-specific rollout                                  |
| `--ml-training`                                        | CORE + ml-service + features-\* consumers         | ML training runs (any category)                            |
| `--include <repo>`                                     | CORE + the named repo (repeatable)                | Surgical addition                                          |

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

## Singleton-locked launchers (2026-04-20; extended 2026-05-12)

The singleton-lock pattern grew from 3 anchor launchers (2026-04-20) to **~36 launchers as of 2026-05-12** (grep
`grep -l singleton deployment-service/scripts/vm/launch-*.sh | wc -l`). The pattern is now the workspace default for
**any** launcher whose adapter shares API keys / per-IP rate-limits / consumer-group identity / per-AG WS feeds.

**Original 3 anchors** (rate-limit thundering herd protection):

- `launch-sfi-forward-poll.sh` — SFI/RapidAPI rate-limits per-key; 10 concurrent VMs thrash on 429 backoffs and produce
  no useful data. Lock: refuses launch if any `sfi-fwd-*` VM is RUNNING in the zone. `--force` bypass.
- `launch-mtds-prediction-backfill-vm.sh` — Polymarket gamma rate-limits per-IP; concurrent VMs share the project egress
  NAT. Same lock pattern. `--force` bypass.
- `launch-tradfi-backfill-vm.sh` (2026-04-20, CME Tier 1 Phase A) — Databento account is shared across the team;
  concurrent VMs on wide windows risk contract-exceeded errors. Lock: refuses launch if any `tradfi-bf-*` VM is RUNNING
  in the zone. `--force` bypass. Shards CME ES expiries year-by-year 2022-2026 (4 quarterly contracts per year on
  `CME:FUTURE:ES-YYYYMMDD`). Default `VM_DATA_TYPES=ohlcv_1m;trades`; override with `--data-types`. Override instruments
  with `--instrument-ids 'CME:FUTURE:ES-20260619;...'`. Machine `e2-standard-4` per shard.

**Extended coverage (2026-05-12)** — singleton-locking is now applied across these categories:

- **Live-pipeline producers**: `launch-mtds-live.sh` + `launch-mdps-features-live.sh` — per-asset-group lock
  (`mtds-live-{asset_group}-*` / `mdps-features-live-{asset_group}-*`). Two concurrent producers for the same
  asset_group thrash on the WS feed + race on the Redis Stream consumer group.
- **Forward-poll launchers**: `launch-cefi-forward-poll.sh` / `launch-defi-forward-poll.sh` /
  `launch-aster-forward-poll.sh` + per-source-provider variants.
- **Backfill workers** with shared API quotas: features-service backfills (`launch-features-*`), instruments-service
  backfills (`launch-cefi-instruments-backfill.sh`, `launch-api-football-backfill-vm.sh`).
- **Single-resource daemons**: ~~`launch-manifest-consolidator-vm.sh`~~ DELETED 2026-05-20 — consolidator now runs on
  Cloud Run + Cloud Scheduler (10 jobs, `*/1 * * * *`). Do NOT re-launch the GCE VM. See
  [`manifest-consolidator-ssot.md`](manifest-consolidator-ssot.md).
- **Reconciliation / audit one-shots**: `launch-cross-asset-rescan-vm.sh`, `launch-blank-reason-recon-vm.sh`,
  `launch-defi-phantom-recon-vm.sh`, `launch-fixtures-truthset-audit-vm.sh` — singleton prevents double-counting of
  manifest flips.

Incident reference: `memory/project_session_handover_2026_04_19.md` + the 2026-04-19 SFI herd that produced ~4
successful writes across 10 VMs in 6 hours.

**If you build a new launcher for a rate-limited / shared-quota / shared-feed adapter**: copy the singleton-lock pattern
from any of the above (the closest-shape anchor is the best starting point), not just the
`gcloud compute instances create` boilerplate.

---

## ML launcher (non-singleton, consolidated 2026-05-20)

`launch-ml-vm.sh` (consolidated from `launch-ml-training-vm.sh` per `ml_repo_consolidation_2026_05_19`) — runs training,
inference, or evaluation for a single ml-service instrument×target×timeframe combination on GCE, writing artefacts to
the ml model_registry in GCS. VM prefix: `ml-{instrument}-{ts}`.

- **Not singleton-locked** — parallel training is expected (different instruments, different target types, different
  hyper-param grids). ml-service does not share a rate-limited API key; it reads feature parquet + fits models locally.
- **`--operation` required** — selects sub-mode: `train|infer|evaluate|grid-search|pipeline`.
- Machine choice via `--machine cpu|high|gpu`:
  - `cpu` (default) → `n2-highmem-8` (64 GB RAM). Enough for LightGBM / XGBoost / CatBoost on 5-year 1-minute data.
  - `high` → `n2-highmem-16` (128 GB RAM). For larger hyper-param grids / Optuna multi-trial runs.
  - `gpu` → `n1-standard-8` + 1×T4 (~$0.35/h). Only when the harness config uses a GPU-enabled booster.
- Tarballs: prep with `bash create-code-tarballs.sh --ml-training` (CORE + ml-service + features-\* consumers).
- Routing: launcher passes `VM_TASK=features-backfill` + `VM_BACKFILL_CMD="python -m ml_service ..."`, reusing the
  features-backfill branch of `setup-data-pipeline-vm.sh` which already handles verbatim command execution.
- Observability: inherits the `STALL_TIMEOUT_SEC=600` log-mtime watchdog + `timeout 30s` run_heartbeat + py-spy stack
  dump + pkill-by-name fallback from `vm-exec-with-gcs-tee.sh` (deployed 2026-04-19 after the VM silent-hang class bug).

Typical CME S&P 500 ML Tier 1 MVP invocation:

```bash
bash launch-ml-vm.sh \
  --operation train \
  --asset-group TRADFI --instruments ES_FRONT \
  --target-types 'swing_high;swing_low' --timeframes 1m \
  --start-date 2022-01-01 --end-date 2025-12-31 \
  --machine high
```

---

## GCS path scanning — `gsutil ls` vs `gcloud storage ls` (HARD RULE, 2026-05-19)

**Rule**: when scanning for parquets under hive-partition prefixes (e.g. `day=2019-`, `asset_group=sports/`), use
`gsutil ls -r` with a `**` glob wildcard — NOT `gcloud storage ls --recursive`.

### The failure mode

`gcloud storage ls --recursive gs://bucket/path/day=2019-06-` exits with rc=1 even when matching objects exist. The
storage CLI treats a prefix that doesn't exactly match a GCS "directory" delimiter boundary as not-found. This is
**silent data loss from the VM's perspective**: the ingestion handler receives an empty file list, skips all shards,
emits `empty_confirmed` manifest rows, and self-deletes cleanly — zero error signal.

**Production incident (2026-05-19 GCS migration run):** 31 VMs went idle. All emitted `DEPLOYMENT_COMPLETED`. Manifest
showed 31 × N `empty_confirmed` rows. Root cause: `gcloud storage ls --recursive` was used against
`gs://instruments-store-sports-prod/asset_group=sports/data_type=match/fixtures/day=2019-*` — the hive-partition prefix
didn't anchor at a delimiter boundary so GCS returned 0 objects with rc=1. Bug fixes:

- PM@`726a3bf` — switched all prefix scans to `gsutil ls -r gs://bucket/prefix**`
- deployment-service@`5b917c1` — added `always-shutdown-on-failure` guard so VMs don't silently idle

### Correct pattern

```python
import subprocess, shlex

def gcs_ls_prefix(prefix: str) -> list[str]:
    """Scan GCS under a hive-partition prefix. Returns list of gs:// paths."""
    cmd = ["gsutil", "ls", "-r", f"{prefix}**"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 1 and not result.stdout.strip():
        return []  # empty prefix — not an error
    result.check_returncode()  # re-raise for any other non-zero exit
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".parquet")]
```

Key points:

- `gsutil ls -r prefix**` — the `**` wildcard anchors glob matching at any depth after the literal prefix
- `check=False` + treat rc=1 with empty stdout as empty list (GCS returns rc=1 for zero-match, not as an error)
- Any other non-zero rc (auth failure, bucket not found) should re-raise

### Wrong pattern

```bash
# WRONG — exits 1 on partial hive-partition prefix match; silent empty result
gcloud storage ls --recursive gs://bucket/path/day=2019-06-

# WRONG — subprocess(..., check=True) will raise on legitimate empty prefixes
subprocess.run(["gsutil", "ls", "-r", prefix], check=True)
```

### Scope

This applies to any code in instruments-service, MTDS, features-service, or deployment scripts that walks GCS to
discover parquets by date-range prefix scan. It does NOT apply to listing a complete known path (no prefix matching
needed) — those can use `gcloud storage ls` safely.

---

## How to debug a failed VM run

> **Cross-ref (O-12, added 2026-05-13)**: when sizing the next VM after an OOM or memory-pressure failure, use the
> `recommended_machine_type` runbook in
> `market-tick-data-service/market_tick_data_service/engine/shard_memory_profile.py` — it reads the per-shard memory
> profile from past runs and recommends `e2-standard-N` / `e2-highmem-N` tiers based on observed peak RSS. Referenced
> from rc=137 row in the Exit codes table below.

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

> **Three guarantees are NOT sufficient for honest-coverage observability (2026-05-12)** — the trio above answers "did
> the VM run + complete + clean up?" but does NOT answer "did the VM produce real captured rows, or empty placeholders?"
> Reference incident 2026-05-05: 21 MDPS VMs all emitted STARTED+STOPPED+self-deleted cleanly, but output was 1440 NaN
> OHLC bars per day for years (caught only by hand-inspection). The correlated-validation guarantee is supplied by the
> alerting-service / `unified-events-interface` UI: a STARTED+STOPPED pair MUST be correlated against a manifest
> spot-check (sample parquet OHLC populated; cluster validation passing per writegate Phase 1A) before the run is
> treated as operationally complete. See CLAUDE.md "No fire-and-forget VM launches"
>
> - `codex/02-data/honest-absence-downstream-handling.md` (the 1440-NaN incident framing) — both are part of the
>   observability contract, not in addition to it.

### Post-launch verification — T+10min check (codified 2026-05-18)

**Rule (from CLAUDE.md "No fire-and-forget VM launches"):** A VM is not "launched" until it has been verified at T+10
minutes post-`gcloud instances create`. A successful `gcloud` API response only means GCP accepted the create request —
it does not confirm the VM booted, the startup script ran, or the workload is emitting heartbeats.

**Required check at T+10min:**

```bash
# 1. Confirm VM is RUNNING (not STAGING / TERMINATED)
gcloud compute instances describe <vm-name> --zone=<zone> --format='value(status)'
# Expected: RUNNING

# 2. Confirm STARTED heartbeat emitted
gsutil cat gs://deployment-scripts-central-element-323112/deployments/active/<deployment_id>.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status'), d.get('last_heartbeat'))"
# Expected: status=running, last_heartbeat within last 90s

# 3. (Optional) Tail the GCS log for the first evidence of real work
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log | head -40
```

**What counts as verified:**

1. `gcloud instances describe` returns `status=RUNNING`.
2. Deployment registry JSON shows `status=running` with a heartbeat timestamp within 90s of now.
3. No `ERROR` / `Exception` in the first 40 lines of `run.log`.

**If the T+10min check fails:**

- STAGING → VM never booted (startup script silently rejected, quota issue, zone capacity). Check
  `gcloud compute operations list --filter="targetLink~<vm-name>"`.
- Registry missing → heartbeat daemon not started (startup script fault). SSH in, check
  `/var/log/syslog | grep startup-script`.
- `TERMINATED` within 10min → workload crashed at startup. Read `EXIT_STATUS` + full `run.log`.

**Why 10 minutes:** startup script installs Python, pulls tarballs, and starts the workload. On a standard
`n1-standard-4` with a cold image and a 120MB tarball, boot-to-first-heartbeat is typically 4-7 minutes. 10 minutes
provides margin for slow GCS pulls without burning excessive agent turn time.

**Enforcement:** CLAUDE.md § "No fire-and-forget VM launches (CRITICAL)" prohibits declaring a VM launched without this
check. Agent turns that post `gcloud instances create` and immediately report "VM launched" without a T+10min
verification step are non-compliant — the operator is expected to reopen the agent turn and demand the check.

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

## Manifest consolidator — SUPERSEDED (GCE VM deleted 2026-05-20)

> **[DELTA 2026-05-22]** **Current state:** Manifest consolidator runs on **Cloud Run + Cloud Scheduler** (10 jobs,
> `*/1 * * * *` UTC). Legacy GCE VM (`manifest-consolidator-20260511-190513`) was deleted 2026-05-20. Launcher script
> `launch-manifest-consolidator-vm.sh` was also deleted. **Planned delta:** slot 5 to extend to all 16 service buckets
> (R-NEW-1) and consolidate 10 → 5 jobs per operator direction. **Target architecture:** 5 Cloud Run jobs, one per
> asset_group, each consolidating all service buckets for that asset_group. Terraform:
> `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`.
>
> **FULL SSOT: [`manifest-consolidator-ssot.md`](manifest-consolidator-ssot.md)** — do NOT re-derive from this section.

The **original architecture** (documented for historical context):

- VMs writing to the manifest write to `_index/per_vm/<vm_name>.parquet` shards (avoids canonical write contention).
- A consolidator periodically reads canonical + all per_vm shards, dedups on the row-key tuple, writes back to
  canonical.
- The UTL reader has a 120s freshness threshold — if canonical is stale, falls back to per_vm shards only.

This architecture is **unchanged** — only the runtime changed from GCE VM to Cloud Run.

**Do NOT:**

- Re-launch `launch-manifest-consolidator-vm.sh` (deleted; script no longer exists)
- Run `gcloud compute instances create manifest-consolidator-*` (would re-introduce the deprecated pattern)
- Reference `VM_TASK=manifest-consolidator-poll` (no longer a valid VM task)

**Instead:** consult [`manifest-consolidator-ssot.md`](manifest-consolidator-ssot.md) for the canonical Cloud Run
verification recipe + coverage gap status + operational invariants.

**SSOT cross-refs:**

- [`manifest-consolidator-ssot.md`](manifest-consolidator-ssot.md) — canonical runtime SSOT
- [`02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) "Manifest
  consolidator + per_vm shard merge mechanics"
- UTL CLI: `python -m unified_trading_library.manifest_consolidator --bucket <X> --once`

---

## VM launcher template DRY audit (2026-05-15)

As of 2026-05-15, `deployment-service/scripts/vm/` contains **~83 `launch-*.sh` launchers**. Audit findings from B-011
blindspot sweep + post-B-011 consolidation work:

### CODE_BUCKET pattern split

| Pattern                                                               | Count | Status                                    |
| --------------------------------------------------------------------- | ----- | ----------------------------------------- |
| `CODE_BUCKET="deployment-scripts-${PROJECT}"` (variable)              | 12    | Post-B-011 canonical form                 |
| `CODE_BUCKET="deployment-scripts-central-element-323112"` (hardcoded) | 48    | Pre-B-011 legacy — functional but brittle |
| No CODE_BUCKET reference                                              | 23    | Use inline `gs://` or no GCS reads        |

**Consolidation opportunity**: the 48 hardcoded launchers could be migrated to `"deployment-scripts-${PROJECT}"`. This
was deferred (pre-B-011 fleet sweep is large scope; no operator direction for full-fleet sweep as of 2026-05-15). File a
new plan if full migration is approved.

### Common boilerplate repeated across all launchers

These ~6 lines appear near-identically in every launcher — a future shared function or sourced helper could DRY them,
but doing so requires a sourced-file deployment strategy (the helper would need to land on the VM or be inlined at
`gcloud` call time):

```bash
--image-family=ubuntu-2404-lts-amd64
--image-project=ubuntu-os-cloud
--scopes=cloud-platform
startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh
VM_SHUTDOWN_ON_COMPLETION=true
VM_NAME=${VM_NAME}
```

### Singleton lock pattern

~36 launchers implement the singleton lock via
`gcloud compute instances list --filter='name~"^PREFIX" AND status=RUNNING'`. The pattern is correct and uniform — no
consolidation needed.

---

## VM admin + cost tooling (Phase 8.A, 2026-05-15)

Three one-shot admin scripts live under `deployment-service/scripts/vm/` for fleet-wide operations. All are `--dry-run`
safe.

### `analyze_vm_costs.py` — VM spend by type / asset_group / week

```bash
python deployment-service/scripts/vm/analyze_vm_costs.py \
    [--days N] [--project PROJECT_ID] [--output-csv PATH]
```

Two `gsutil ls -l` calls (no per-VM round trips) — fast on large fleets. Outputs spend-by-`machine_type`, by
`asset_group` label, and by week. Useful for cutover-week budgeting. **Smoke (2026-05-15)**: 81 VMs / 7 days / 105.8
VM-hrs / $13.98 total. CSV written to `/tmp/vm_costs_7d.csv`. Shipped: deployment-service@920ff18.

### `cleanup_old_tarballs.py` — prune stale deployment tarballs from GCS

```bash
python deployment-service/scripts/vm/cleanup_old_tarballs.py \
    [--keep-n N] [--noncurrent-days D] [--dry-run] [--project PROJECT_ID]
```

Two cleanup modes:

- `--keep-n N` (default 5): for name-versioned tarball naming (`<repo>@<sha>.tar.gz`), keeps the N most-recent per
  service and deletes the rest.
- `--noncurrent-days D` (GCS object versioning): deletes noncurrent GCS object versions older than D days.

**Note**: current production naming uses simple per-service files without SHA accumulation; `--noncurrent-days` is the
active path until SHA-versioned naming (see § "Tarball naming + manifest" above) is adopted. Dry-run smoke confirmed 0
deletions on the live bucket. Shipped: deployment-service@3c42df5.

> **WARNING — SHA-pin fan-out race (2026-06-01 incident)**: if you upload `<repo>@<sha>.tar.gz` files and then
> immediately launch a large fan-out (e.g. 20 shards), `cleanup_old_tarballs.py` can prune the just-uploaded SHA-pinned
> tarball **within seconds** of the upload (before any VM has fetched it). The 2026-06-01 20-shard launch resulted in
> all 20 VMs failing with exit code 2 (tarball not found at boot) because the SHA-pinned file was pruned between upload
> and first VM fetch.
>
> **Mitigations before relying on SHA-pins for fan-out**:
>
> 1. Use a **no-prune bucket** (a separate GCS bucket or prefix that `cleanup_old_tarballs.py` is not pointed at) for
>    SHA-versioned fan-out tarballs.
> 2. Tune `--keep-n` to a value ≥ the number of concurrent VMs that need to fetch the tarball before the next prune
>    cycle.
> 3. Verify the tarball is present before firing launchers: `gsutil stat gs://.../code/<repo>@<sha>.tar.gz`.

### `validate_vm_prefix_mapping.py` — prod audit: `VM_PREFIX_TO_BUCKET` vs live GCS buckets

```bash
python deployment-service/scripts/vm/validate_vm_prefix_mapping.py \
    [--project PROJECT_ID] [--dry-run]
```

Walks every non-`None` bucket entry in `VM_PREFIX_TO_BUCKET` and verifies the GCS bucket exists. Reports orphan prefixes
(bucket in dict, not in GCS) and missing-prefix entries. **Prod run (2026-05-15)**: 88 OK, 56 heartbeat-only (`None`), 0
orphans. 6 legacy string entries in dict (pre-`VmPrefixSpec`; script handles both transparently). Shipped:
deployment-service@29eb7ad.

---

## UTL-on-a-VM staging checklist (crash-cascade prevention)

`pip install`-ing `unified-trading-library` on a VM is necessary but NOT sufficient — UTL resolves cloud config, project
identity, and the deployment-service log-backup path at import/runtime. Miss any of the four below and the VM crashes in
a cascade (the watchdog can't back up logs → it looks like a silent VM death). Codified from a recurring incident. All
four must hold:

1. **`cloud-providers.yaml` is on disk + pointed at by its env var.** The bucket-name SSOT resolver reads it; absent →
   `resolve_bucket_name()` fails on first use. Stage the file in the tarball / startup and export the path env.
2. **Project + env vars exported**: `GCP_PROJECT_ID` (and `PROJECT_ID`) + `DEPLOYMENT_ENV_SHORT` (`prod`→`prd` /
   `staging`→`stg` / `dev`→`dev`). UTL uses `GCP_PROJECT_ID` (never `GOOGLE_CLOUD_PROJECT`/`GCP_PROJECT`).
3. **`deployment_service` is importable** on the VM — the watchdog's log-backup path imports it; missing → the backup
   step throws and the watchdog itself dies.
4. **No backticks inside the `STARTUP="..."` heredoc.** Backticks trigger shell command-substitution at launch time
   (before the script runs), corrupting the startup script. Use `$(...)` only where substitution is intended; avoid
   backticks in any embedded documentation strings.

Symptom when violated: VM reaches `RUNNING` but produces no heartbeat / no progress and the zombie watchdog reports it
as silent. Verify all four at the T+10min post-launch check.

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
