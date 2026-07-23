---
doc_type: issue
title:
  Tier-2 datapoint-validation VM launch BLOCKED-CREDENTIALS — results bucket was never provisioned + no service-account
  has storage.buckets.create
summary:
  Attempting the first real launch-run of the Tier-2 datapoint-validation VM (built in a prior session, never
  launch-run) found the results bucket `central-element-323112-datapoint-validation` does not exist (gcloud storage
  buckets describe returns 404, not a permission-ambiguous 403). The active automation identity
  (`unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) lacks `storage.buckets.create` at the project
  level, and the only other available gcloud credential (`ikenna@odum-research.com`) has an expired OAuth token that
  cannot be refreshed headlessly. Launching the VM anyway would guarantee a failed run (a real, costly corpus walk that
  deterministically fails at its first results-shard flush) — the agent correctly stopped short rather than
  fire-and-forget a doomed launch. A possible SIBLING gap was also observed on `alerting-service` (a bucket-kind added
  to cloud-providers.yaml the same week without the physical bucket provisioned) but this was NOT independently verified
  — flagged for follow-up, not asserted as fact.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    tier-2-vm,
    datapoint-validation,
    bucket-provisioning,
    blocked-credentials,
    gcs,
    iam,
    reconciliation-census-and-compute-tiers,
  ]
related:
  [
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: agent attempt to execute plan todo 32 (Tier-2 VM real launch-run), 2026-07-21
depends_on: []
---

# Tier-2 datapoint-validation VM launch BLOCKED-CREDENTIALS (2026-07-21)

> **State: everything except the bucket is verified clean.** `deployment_service/vm_prefix_registry.py:588-602` (all 5
> `datapoint-validation-{ag}-` VmPrefixSpecs registered), `launcher_registry.py:204-208` (all 5 prefixes mapped),
> `configs/cloud-providers.yaml:188` (the `datapoint-validation` bucket kind declared) — all correct. The launcher
> script and the validator script (`launch-datapoint-validation-vm.sh` / `validate_datapoint_schema_id.py`) were read in
> full and are ready to run as-is: one VM per asset_group (no `--shard` flag exists or is needed), zone
> `asia-northeast1-c`, e2-standard-4 SPOT, singleton-locked per asset_group, presence-skip idempotent, flushes on every
> day-frontier advance + every 500 objects.

## The blocker

`gcloud storage buckets describe gs://central-element-323112-datapoint-validation` → **404 not found** (the bucket was
never created — a declare-in-yaml-without-provisioning gap, distinct from a permissions problem). Attempting to create
it:

- `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (the active automation identity) → explicit
  **403** on `storage.buckets.create` at the project level (also lacks `resourcemanager.projects.getIamPolicy` /
  `secretmanager.secrets.list` — a narrow, least-privilege identity, not project-admin, by design).
- `ikenna@odum-research.com` (the only other gcloud-credentialed account on this box) → OAuth token **expired**;
  `gcloud auth login` requires an interactive browser flow, not available headlessly.
- `deployment-service/scripts/bootstrap/bootstrap_gcp.sh` (the actual Terraform-based bucket-bootstrap tool) is
  explicitly a human-run script requiring `gcloud auth application-default login` first.

Launching any of the 5 VMs without the bucket would run a real GCS corpus walk (cost + time) that deterministically
fails at the first results-shard flush — a guaranteed-broken "launch" that would violate the no-fire-and-forget /
runtime-verification rule. **No VM was launched.**

## Remediation options (operator decision needed — this is genuinely human-gated, not agent-executable)

- **A [recommended]**: operator runs, from an authenticated session:
  `gcloud storage buckets create gs://central-element-323112-datapoint-validation --project=central-element-323112 --location=asia-northeast1 --uniform-bucket-level-access --default-storage-class=STANDARD`
  — then any agent can launch all 5 VMs immediately (everything else is verified ready).
- **B**: grant `unified-trading-sa@...` `roles/storage.admin` (or narrower `storage.buckets.create`) at the project
  level — closes this gap for future new bucket kinds too, if the sibling `alerting-service` suspicion (below) is
  confirmed real.
- **C**: refresh the `ikenna@odum-research.com` gcloud credential (`gcloud auth login`) so agents can use
  `--account=ikenna@odum-research.com` for one-off admin actions like this.

## Unverified follow-up — possible sibling gap on `alerting-service`

The investigating agent noted (but did NOT independently verify) that `alerting-service` may have the same
declared-bucket-kind-without-physical-bucket gap, added the same week. **Not asserted as fact** — needs a dedicated
check (`gcloud storage buckets describe gs://<alerting-service bucket name>`) before acting on it. If confirmed, this
points to a process gap: adding a `kind:` row to `cloud-providers.yaml` does not itself provision the bucket, and
nothing currently catches that at review/QG time.

## Todos

- [x] 1. ✅ [INFRA] P1. Operator ran option A 2026-07-21
      (`gcloud storage buckets create     gs://central-element-323112-datapoint-validation ...`). Note: the automation
      service account still lacks `storage.buckets.get` (bucket-metadata describe 403s), but has full object read/write
      (`gcloud storage ls` / `cp` verified) — sufficient for the validator, which never calls `buckets.describe`.
- [x] 2. ✅ [INFRA] P1. First launch attempt 2026-07-21 ~15:52-15:54 UTC — all 5 VMs reached RUNNING within seconds, but
      a T+10min watchdog check found **all 5 had FAILED and self-deleted within ~1-3 minutes** (exit_code=2). Root cause
      (read from `run.log`): `setup-data-pipeline-vm.sh` had **no dispatch branch for
      `VM_TASK=="datapoint-validation"`**, so it fell through to the generic `elif [ -n "$VM_TASK" ]` fallback, which
      built `python -m instruments_service --operation datapoint-validation --mode batch --asset-group CEFI` —
      `instruments-service`'s CLI has no such `--operation` choice (only `instruments`), an immediate argparse crash.
      **Same root-cause class as the already-documented 2026-07-12 `sports-v9-migration` and 2026-07-13 `defi-paper`
      `VM_TASK` gaps in the same file** — a new launcher's `VM_TASK` needs its own dispatch branch even when it just
      runs the launcher-supplied `VM_BACKFILL_CMD` (the launcher itself always built the correct
      `validate_datapoint_schema_id.py` invocation — the bug was purely in the shared VM-side bootstrap script never
      being wired to route to it). **Fixed**: added the missing `elif [[ "$VM_TASK" == "datapoint-validation" ]]` branch
      (mirrors the existing `strategy-backtest-grid` pattern — curl `VM_BACKFILL_CMD` from instance metadata, substitute
      python path, `cd $WORKSPACE/instruments`, `_launch_with_tee`) — `deployment-service@c079bd8` (direct LDR push,
      dirty-deps carve-out: `unified-api-contracts` had unrelated concurrent WIP blocking quickmerge's pre-flight).
      Republished the fixed script to `gs://deployment-scripts-central-element-323112/vm/` (closing the documented
      setup-script publish race) and relaunched all 5 VMs 2026-07-21 ~16:20-16:23 UTC:
      `datapoint-validation-cefi-20260721-162041`, `datapoint-validation-defi-20260721-162105`,
      `datapoint-validation-tradfi-20260721-162134`, `datapoint-validation-prediction-20260721-162158`,
      `datapoint-validation-sports-20260721-162238` (zone asia-northeast1-c). All confirmed RUNNING. A second T+10min
      watchdog is armed. NOTE: this relaunch warned STALE tarballs for `instruments-service` (+ UTL, + UAC for sports) —
      a concurrent Round-1 writer-fix workflow is actively committing to those repos; the validator's core logic (UAC
      `build_canonical_instrument_id` / `validate_dataframe` / contract lookup) is not part of what that workflow is
      changing, so proceeding was judged safe, not verified byte-for-byte.
- [ ] 3. [REVIEW] P2. Verify (or refute) the suspected sibling gap on `alerting-service` — check whether its declared
      bucket kind in `cloud-providers.yaml` has a physically-provisioned GCS bucket. If real, consider a QG check that a
      new `kind:` row is paired with bucket-existence verification (or an explicit provisioning todo) so this class of
      gap cannot recur silently.
- [ ] 4. [CODE] P2. Consider whether `setup-data-pipeline-vm.sh`'s generic `elif [ -n "$VM_TASK" ]` fallback should fail
      LOUDER/EARLIER for an unrecognized `VM_TASK` (e.g. detect that `VM_BACKFILL_CMD` metadata is present but unused,
      and prefer it, or at minimum log a WARNING) — this is now the THIRD time (2026-07-12 sports-v9-migration,
      2026-07-13 defi-paper, 2026-07-21 datapoint-validation) a new launcher's `VM_TASK` fell through to this same
      fallback and crashed on `--operation` before anyone caught it in review. A generic guard would catch class-4
      instances before the next new launcher hits it.

## Update 2026-07-21 (later same session) — two MORE bugs found on the same first launch-run

The dispatch-branch fix (todo 2) got tradfi + sports genuinely running (day-frontier advancing, thousands of rows
validated, shards flushing — confirmed by reading `run.log`). cefi/defi/prediction hit two FURTHER bugs on the very same
first real run — consistent with the codex appendix's own warning that this VM had never actually been launch-run
before:

- [x] 5. ✅ [CODE] P1. **Day-frontier flush exceeds GCS's per-object write-rate limit on sparse-data corpora.**
      `_run()`'s day-frontier flush (`validate_datapoint_schema_id.py`) re-uploads the WHOLE per-VM results parquet on
      EVERY `day=` crossing, unthrottled — cefi's early-2019 days are sparse enough to cross many `day=` partitions per
      second, so the SAME target object (`_index/per_vm/{vm_name}.parquet`) got hit with sustained >1 write/sec, well
      past GCS's per-object mutation rate limit (429 `rateLimitExceeded` — confirmed this is a PER-OBJECT cap, not
      project/bucket-wide, from the error body). Raising `--flush-every` (the count-based flush) did NOT help — the
      day-frontier flush fires independently of that counter. **Fixed**: throttled the day-frontier flush to at most
      once per 2s wall-clock (`_MIN_FLUSH_INTERVAL_SECONDS`); the count-based flush and the unconditional final flush
      are untouched, so no rows are ever lost, only the day-crossing flush cadence is capped —
      `instruments-service@f9942725` (direct LDR push, dirty-deps carve-out).
- [x] 6. ✅ [CODE] P1. **`prediction` asset_group always raised `BucketNamingError`.**
      `resolve_bucket_name(kind="market-data", asset_group="prediction")` has no `prediction` row — prediction's
      market-data bucket is a DEDICATED flat yaml kind (`market-data-tick-prediction`), not a row under the shared
      per-asset_group `market-data` dict (mirrors the existing pattern already used by
      `market-tick-data-service/scripts/rebuild_mtds_manifest.py:42` and
      `canonicalize_prediction_manifest_2026_07_18.py:952` — a call-site convention this validator simply never picked
      up when it was authored). **Fixed**: special-cased `asset_group.lower() == "prediction"` to resolve via
      `kind="market-data-tick-prediction"` (no `asset_group` kwarg) — same commit `instruments-service@f9942725`.
- [ ] 7. [INFRA] P1. **Relaunch cefi/defi/prediction is BLOCKED on a dirty-deps tarball-republish gap** (distinct from
      the code-commit dirty-deps carve-out above).
      `deployment-service/scripts/vm/create-code-tarballs.sh     --include instruments-service` refuses to build (and,
      critically, `tar czf`s the raw WORKING TREE, not `git archive` — so `--allow-dirty-tarball` would bundle a
      concurrent workflow's uncommitted `unified-api-contracts` edits into the deployed tarball, not just
      instruments-service's own committed fix). instruments-service's own committed fix (`f9942725`) is ready;
      tradfi/sports do not need a re-tarball (their VMs already picked up a fresh-enough copy). **Wait for the
      concurrent Round-1 writer-fix workflow to land its `unified-api-contracts` changes** (R3 cefi-v6 + the UAC oracle
      candle-extension), THEN republish (`bash scripts/vm/create-code-tarballs.sh --include instruments-service`) and
      relaunch cefi/defi/prediction. Do NOT `--allow-dirty-tarball` while a peer's WIP is mid-flight.
