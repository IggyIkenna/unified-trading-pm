---
doc_type: issue
title: >-
  setup-data-pipeline-vm.sh's OOM preflight resolves DEPLOYMENT_ENV=staging to a `-stg-` bucket suffix that doesn't
  exist (real tier suffix is `-test-`) — crashes every MTDS backfill/download VM launched with --env staging
summary: >-
  Discovered verifying the `--env staging` fix for `market-tick-data-service/scripts/pipeline_e2e_check.py`
  (`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`, MTDS todo). With the SA-identity fix correctly
  in place (VM metadata shows `DEPLOYMENT_ENV=staging`, confirmed), both force and skip legs still failed —
  `vm_exit_nonzero=1` on BOTH — because `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s OOM preflight (§5b,
  ~line 1262) constructs `market-data-tick-cefi-stg-central-element-323112` (via `DEPLOYMENT_ENV_SHORT`, mapped
  `staging -> "stg"` at line 457) — that bucket does NOT exist (`gcloud storage ls` 404s on it); the real staging-tier
  bucket is `market-data-tick-cefi-test-central-element-323112` (`-test-`, confirmed present via `gcloud storage
  buckets list`). `gsutil ls -L` against the nonexistent BUCKET (not just a missing object inside it) fails hard, and
  under this script's error handling that aborts VM setup entirely (`SETUP FAILED rc=1`, self-delete) BEFORE the
  Python test-run task ever starts — so this is a total, silent block on any MTDS backfill/download VM launched with
  `DEPLOYMENT_ENV=staging`, not a partial degradation.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [pipeline-e2e-check, iam, gcp, vm-launcher, bucket-naming, cross-repo, blocking]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [pipeline_e2e_check_missing_env_flag_test_bucket_403-003]
resolved_by:
locked_by:
context_scope: [/codex/05-infrastructure/vm-launcher-runbook.md]
depends_on: []
---

# `DEPLOYMENT_ENV_SHORT` staging→"stg" mapping doesn't match real `-test-` bucket suffix, breaks MTDS download VMs

## What I found

Ran a real force/skip verification of the `--env staging` fix (`market-tick-data-service@<pending>`) against
`CEFI:HYPERLIQUID:liquidations` day `2025-12-20`. The launch argv correctly carried `--env staging` (confirmed in the
local driver's log), and the VM's own `vm-setup.log` confirmed the metadata landed: `VM metadata: ... DEPLOYMENT_ENV=staging`.
Both legs still failed with `vm_exit_nonzero=1` — no `run.log` was ever written (setup itself crashed):

```
2026-08-01 11:12:01 OOM preflight: checking gs://market-data-tick-cefi-stg-central-element-323112/_index/availability_index.parquet mtime against budget 86400s
2026-08-01 11:12:04 SETUP FAILED rc=1 — uploading log + EXIT_STATUS, scheduling self-delete
```

**Root cause**: `setup-data-pipeline-vm.sh` line 456-458:

```bash
case "$DEPLOYMENT_ENV" in
  prod)    DEPLOYMENT_ENV_SHORT="prd" ;;
  staging) DEPLOYMENT_ENV_SHORT="stg" ;;
  *)       DEPLOYMENT_ENV_SHORT="$DEPLOYMENT_ENV" ;;
esac
```

The §5b OOM preflight (line ~1262, gated to `VM_SERVICE=market_tick_data_service && VM_OPERATION=download` — the
latter is `_meta VM_OPERATION download`'s own DEFAULT, so it fires on every MTDS backfill VM that doesn't explicitly
override it, which is all of them) builds:

```bash
_BUCKET="market-data-tick-${_AG_LOWER}-${DEPLOYMENT_ENV_SHORT:-prd}-${GCP_PROJECT_ID:-central-element-323112}"
```

For `DEPLOYMENT_ENV=staging` this is `market-data-tick-cefi-stg-central-element-323112` — **confirmed 404, does not
exist** (`gcloud storage ls` on it 404s). The real staging/test-tier bucket is `market-data-tick-cefi-test-central-element-323112`
(confirmed present via `gcloud storage buckets list`) — the whole codebase's tier-bucket convention is `-prd-`/`-test-`,
not `-prd-`/`-stg-` (see `bucket_iam_write_protection_per_tier_2026_06_09.md`'s IAM conditions, which scope to `-test-`
prefixes explicitly, and every real bucket enumerated: only `-prd-` and `-test-` variants exist, no `-stg-` bucket
exists anywhere in the project).

`gsutil ls -L` against a **bucket that doesn't exist at all** (not just a missing object inside an existing bucket)
returns a hard error; the preflight's `2>/dev/null` only suppresses gsutil's own stderr, it doesn't stop the script's
own error trap from firing on the nonzero exit — so VM setup aborts completely (`SETUP FAILED rc=1`, self-delete)
**before Python or the actual test-run task ever starts**. This is silent from the caller's perspective: the local
`pipeline_e2e_check.py` driver just sees `vm_exit_nonzero=1`, identical to any other generic VM failure, with no
distinguishing signal.

Confirmed this is gated to MTDS `download`-operation VMs specifically (`VM_SERVICE=market_tick_data_service &&
VM_OPERATION=download`) — `launch-mtds-live.sh`'s launches set a different `VM_OPERATION` (`live_websocket`), so
`_run_live_leg`'s identical `--env staging` fix (same session, same repo) should NOT hit this specific gate; not
independently verified in this session (a live leg needs a registered WS connector + a bounded real-time run, deferred
per scope/cost — see the source issue doc's MTDS todo).

## Why it matters

- **Every real MTDS backfill/download VM launched with `DEPLOYMENT_ENV=staging` (`--env staging`) fails 100% of the
  time**, not just the `pipeline_e2e_check.py` smoke driver this was found through. This is the SAME class of gap as
  the source issue (a `-test-`-bucket-only workflow silently 100%-failing since some prior date) but one layer deeper
  — my SA-identity fix for the source issue's MTDS todo is CORRECT and necessary, but insufficient alone to reach a
  green run for MTDS's batch/bundled legs specifically.
- Any FUTURE genuine staging-tier MTDS backfill (not just this smoke-check tool) would hit the identical crash.
- Silent/misleading failure mode: the crash reads as a generic `vm_exit_nonzero=1`/`launcher_script_nonzero_rc=1`, with
  no hint that the actual cause is a bucket-name typo three layers down in a shared VM startup script — matches the
  exact "masks real regressions" risk flagged in the source issue doc.

## Recommended decision

Fix `setup-data-pipeline-vm.sh` line 457: `staging) DEPLOYMENT_ENV_SHORT="stg" ;;` → `staging) DEPLOYMENT_ENV_SHORT="test" ;;`
to match the real bucket-naming convention. Before shipping, audit the OTHER `DEPLOYMENT_ENV_SHORT` consumers in the
same file (lines ~1470-1483, a `BUCKETS_RAW` list spanning `instruments-store-*`, `market-data-tick-*`, `features-*`,
`strategy-store-*` for every asset_group) for the same assumption — if they're built the same way, they carry the
identical latent bug, just not yet triggered because no current caller has passed `DEPLOYMENT_ENV=staging` into a code
path that reaches them (this session's fixes across features-service/MDPS/MTDS are the FIRST callers to ever do so).
Not fixed inline here: this is a shared script serving `deployment-service`, a different repo than the one my current
task is scoped to, and touching it safely requires that broader audit rather than a one-line drive-by edit.

## Todos

- [ ] [CODE] P1. Fix `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` line 457: map `staging` to
      `DEPLOYMENT_ENV_SHORT="test"` (not `"stg"`) to match the real bucket-naming convention
      (`market-data-tick-{ag}-test-{project}`, confirmed via `gcloud storage buckets list` — no `-stg-` bucket exists
      anywhere in the project). Also audit lines ~1470-1483's `BUCKETS_RAW` construction (same
      `DEPLOYMENT_ENV_SHORT`-driven pattern across `instruments-store-*`/`market-data-tick-*`/`features-*`/
      `strategy-store-*`) for the identical assumption and fix if present. (repo: deployment-service)
- [ ] [CODE] P2. Once the above lands, re-run the MTDS force/skip verification
      (`--asset-group CEFI --venue HYPERLIQUID --data-types liquidations --day 2025-12-20 --legs force,skip --auto-day
      --project central-element-323112`) and confirm both legs pass with no `vm_exit_nonzero`/403 — completes the
      "verify with a fresh run" half of `pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`'s MTDS
      todo. (repo: market-tick-data-service)

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md`.
