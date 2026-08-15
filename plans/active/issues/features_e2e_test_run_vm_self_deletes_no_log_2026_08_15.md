---
doc_type: issue
title: >-
  features-e2e-* `--sink-bucket`/test-run VM launches self-delete within ~250-320s with NO run.log/EXIT_STATUS ever
  written — blocks the TRADFI:volatility benchmark relaunch (and likely every pipeline_e2e_check test-run VM)
summary: >-
  Relaunching the TRADFI:volatility benchmark (features-service pipeline_e2e_check.py --day 2026-08-14 --asset-group
  TRADFI --family volatility --legs benchmark --benchmark-days 7) failed 3/3 times. Each attempt: the launcher
  auto-republish tarball-freshness guard failed twice (known race, see related doc) before succeeding on a 3rd
  sub-attempt; the resulting VM (features-e2e-tradfi-*) then vanished from `aggregated_list_instances` within ~250-320s
  with ZERO objects written to `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/` — no `run.log`, no
  `EXIT_STATUS`. `exit_status=null` in the pipeline_e2e_check result (the launcher engine's
  self-deleted-with-no-exit-status path). A fresh manual `create-code-tarballs.sh --include features-service --include
  deployment-service --force` (which also republished `vm/setup-data-pipeline-vm.sh`) did NOT change the outcome on a
  4th... 3rd retry — same result. Leading unconfirmed hypothesis: this specific launch shape passes `--env staging` +
  `--sink-bucket features-tradfi-test-...`, which resolves the VM's runtime service account to `uts-test-sa` (DP-VM-002
  fix, `launcher_common.sh:165-177`) instead of the default tier SA — if `uts-test-sa` lacks read access to the
  CODE_BUCKET's `vm/setup-data-pipeline-vm.sh` object or write access to `vm-logs/`, the VM would fail to fetch or
  execute its startup script (or execute it but be unable to write ANY log), exactly matching the observed symptom.
  Could not confirm via bucket IAM-policy inspection in this session (the sanctioned UTL `GCSBucketHandle` has no
  `get_iam_policy` method, and a raw `gcloud storage buckets get-iam-policy`/`gsutil` inspection is hook-blocked as an
  object-op pattern match).
status: open
nature: issue
asset_group: [tradfi, infrastructure]
stage: [meta]
repos: [deployment-service, features-service]
scope: [engineer, admin]
tags: [vm-launcher, test-run, service-account, iam, silent-failure, pipeline-e2e-check, benchmark]
related:
  [
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/active/issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md,
    /plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-15
author: slot-6 (backend_engineer)
last_updated: 2026-08-15
priority: P1
parent_epic: infrastructure_master
source: >-
  Relaunching the TRADFI:volatility benchmark per tradfi_satellite_ao_dispatch_batch13_2026_08_13.md's "Todo 2: relaunch
  TRADFI:volatility benchmark once todo 1 lands" (slot-6, backend_engineer, 2026-08-15).
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
resolved_by:
context_scope:
  [
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/launcher.py,
  ]
---

# features-e2e test-run VM self-deletes with no log/exit-status (2026-08-15)

## What I found

Ran
`features-service/scripts/pipeline_e2e_check.py --day 2026-08-14 --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`
three times (`uv run python scripts/pipeline_e2e_check.py ...`), each a fresh end-to-end launch attempt:

| Attempt                                                                                                    | VM name                                      | Tarball-freshness sub-retries                                            | Result               | wall_clock | objects |
| ---------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------ | -------------------- | ---------- | ------- |
| 1                                                                                                          | `features-e2e-tradfi-20260815-093837-679e08` | 2 failed (`auto-republish completed but tarball(s) still stale`), 3rd OK | self-deleted, no log | 271s       | 0       |
| 2                                                                                                          | `features-e2e-tradfi-20260815-094610-679e08` | 2 failed, 3rd OK                                                         | self-deleted, no log | 250s       | 0       |
| 3 (after manual `create-code-tarballs.sh --include features-service --include deployment-service --force`) | `features-e2e-tradfi-20260815-095346-679e08` | 2 failed, 3rd OK                                                         | self-deleted, no log | 317s       | 0       |

For all 3, confirmed directly (not inferred from the report alone):

- `gcloud compute instances describe <vm> --zone=asia-northeast1-c` → `NOT FOUND` (instance already gone by the time the
  driver returned).
- `gcs_describe_object(uri='gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log')` → `None`.
- `gcs_describe_object(uri='gs://deployment-scripts-central-element-323112/vm-logs/<vm>/EXIT_STATUS')` → `None`.
- JSON result: `"exit_status": null, "parquet_count": 0, "write_verified": false`.

Per `unified_trading_library/pipeline_e2e_check/launcher.py`'s `_poll_until_terminal` (per a prior agent's read of that
function this session — not independently re-verified line-by-line here), `exit_status=None` after a real elapsed
duration (not an immediate 0s failure) is the **self-deleted-with-no-exit-status** path: the VM vanished from
`aggregated_list_instances` before ever writing `EXIT_STATUS`, and a 10s grace re-read also found nothing. Since NEITHER
`run.log` NOR `EXIT_STATUS` ever appeared, the crash happened before `vm-exec-with-gcs-tee.sh`'s log-upload trap block
was even installed — i.e. very early in `setup-data-pipeline-vm.sh`'s own boot sequence, or before that script even
started running.

**Manually republishing did not change the outcome.** Between attempts 2 and 3, ran
`bash scripts/vm/create-code-tarballs.sh --include features-service --include deployment-service --force` from a clean,
up-to-date (`ahead=0 behind=0`) `.tabs/6` checkout — this also republished `vm/setup-data-pipeline-vm.sh` (confirmed via
the command's own listing output, `Update time` seconds before the retry). Attempt 3 still hit the identical
2-failed-then-3rd-OK tarball-freshness pattern AND the identical self-deleted-no-log VM crash. This rules out "my local
checkout was simply behind" as the sole explanation for either symptom.

**These are two distinct, stacked problems, not one:**

1. **The tarball-freshness auto-republish race** (2/3 sub-attempts fail with
   `auto-republish completed but tarball(s) still stale (republish skipped? dirty working tree?)`) — this matches the
   ALREADY-TRACKED, well-documented fleet-wide concurrent-republish race in
   `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` (multiple corroborating findings,
   same error text). Not re-diagnosing that mechanism here — just confirming it's still live and hit 6/6 times across 3
   attempts today (2026-08-15), well after that doc's `auto`-mode default flip shipped (`deployment-service@c1e0481`,
   2026-08-06). `.tabs/6`'s own checkout was confirmed clean both times I checked, so this is a genuinely
   concurrent-fleet race, not my own local dirty state.
2. **The post-launch silent VM crash** (this doc's primary new finding) — happens on EVERY successful 3rd-sub-attempt
   launch, i.e. it is independent of whether the tarball race fired first. 3/3 reproduction rate.

## Why it matters

This blocks `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Todo 2: relaunch TRADFI:volatility benchmark"
directly — the fix landed in `_resolve_spot_perp` (features-service@f441638932, done 2026-08-15) but its throughput
cannot be measured because the verification VM itself never runs. More broadly, if the root cause is the `uts-test-sa`
IAM hypothesis below, this would block **every** `pipeline_e2e_check.py --sink-bucket`/test-run VM launch across every
service that uses this shared engine (features-service, market-data-processing-service, and any future adopter) — a P1,
not scoped to TRADFI:volatility alone.

## Leading hypothesis (unconfirmed)

`_build_launch_argv` passes `--sink-bucket features-tradfi-test-central-element-323112` and the driver passes
`--env staging`, which — per `IS_TEST_RUN_FLAG="true"` in `launch-features-vm.sh` — routes
`lc_tier_service_account(env, project, is_test_run=true)` to force `uts-test-sa` regardless of `--env`
(`launcher_common.sh:165-177`, the DP-VM-002 fix, dated 2026-08-01). The VM's `startup-script-url` metadata still points
at the SAME `CODE_BUCKET` (`deployment-scripts-central-element-323112`) that hosts the code tarballs — a bucket whose
primary write-protected tier historically favored `uts-prd-sa`/`uts-test-sa` split by DATA bucket, not necessarily the
shared deployment-scripts bucket. If `uts-test-sa` cannot READ
`gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh` (the metadata-server-fetched startup
script) or cannot WRITE to `vm-logs/`, the VM would either never execute its startup script at all, or execute it but
die on its very first authenticated GCS call — before any tee/log-upload logic runs. This is consistent with every
observed symptom (no run.log, no EXIT_STATUS, short ~250-320s lifetime — consistent with boot + a fast permission
failure + `VM_SHUTDOWN_ON_COMPLETION` or a startup-script-level failure triggering shutdown).

**Not confirmed this session** — bucket IAM-policy inspection was attempted via the sanctioned UTL path
(`get_storage_client().bucket(...).get_iam_policy(...)`) but `GCSBucketHandle` has no such method; a raw
`gcloud storage buckets get-iam-policy`/`gsutil` fallback is hook-blocked (`block_destructive_commands.py`, "subprocess
`gcloud storage` object operation" — treats even a read-only IAM-policy read as an object op under its current pattern
match). Whoever picks up todo 1 below should use `gcloud projects get-iam-policy`/the GCP Console/an IAM Admin API call
(not a bucket-object-shaped CLI command) to avoid re-tripping the guard, or extend the guard's allowlist if
`get-iam-policy` genuinely needs a carve-out (a policy READ, not an object read/write — worth a design note, not assumed
safe to just bypass).

## Todos

- [ ] [INFRA] P1. Confirm or refute the `uts-test-sa` IAM hypothesis above: check `uts-test-sa`'s actual bucket-level
      IAM bindings on `deployment-scripts-central-element-323112` (both the `vm/` prefix read path and the `vm-logs/`
      prefix write path) via `gcloud projects get-iam-policy central-element-323112` or the IAM Admin API (not a
      bucket-object CLI call, per the hook note above). If confirmed, grant the missing role (least-privilege — the
      specific role that closes the specific gap, self-service per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) and re-verify with one real
      `features-e2e-tradfi-*` launch, checking for a real `run.log` this time. (repo: deployment-service / infra — live
      GCP IAM change, not code)
- [ ] [INFRA] P1. If the IAM hypothesis is refuted, get real evidence of what actually kills the VM in its first ~30-60s
      of boot: (a) check GCP Cloud Logging for the instance's serial-port output — NOT enabled by default on this
      launcher (`serial-port-logging-enable` metadata not set in `launch-features-vm.sh`); confirm whether enabling it
      (even temporarily for one diagnostic launch) is acceptable, or (b) SSH into a freshly-launched VM of this exact
      shape IMMEDIATELY after creation (before it can self-delete) to observe `setup-data-pipeline-vm.sh`'s live
      execution — may require racing the ~250s window or temporarily disabling
      `VM_SHUTDOWN_ON_COMPLETION`/`--instance-termination-action` for one diagnostic run. (repo: deployment-service)
- [ ] [SCRIPT] P2. Once root-caused, add a regression signal for this specific failure mode: `launch_vm_and_wait`/the
      pipeline_e2e_check engine already distinguishes `vm_self_deleted_no_exit_status` from `timeout_no_exit_status` in
      its `reason` field (per a prior agent's read this session) but the shard-result `reason` string surfaced in the
      `.md`/`.json` report currently does NOT include that distinction (both attempts' reports show the same generic
      `window=... wall_clock=...Ns ... objects=0` text) — thread the launcher's self-delete/timeout distinction into the
      report's `reason` field so a future reader doesn't have to re-derive it from the raw JSON `exit_status`/duration
      the way this doc's author had to. (repo: unified-trading-library or features-service, wherever the report-writer
      lives)
- [ ] [DATA] P1. Once fixed, relaunch `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Todo 2: relaunch
      TRADFI:volatility benchmark once todo 1 lands"
      (`pipeline_e2e_check.py --day <fresh> --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`)
      and flip that todo's checkbox with the real throughput numbers this doc's author was trying to capture. (repo:
      features-service)

## Progress Log

- **2026-08-15 (slot-6, backend_engineer)**: filed after 3/3 reproduction while working
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s benchmark-relaunch todo. Left that todo's checkbox UNCHECKED
  (done_definition — "capture real throughput" — not met; 0 objects captured in all 3 attempts) and cited this doc in
  its Progress Log rather than silently marking it done or retrying indefinitely (VM-launcher-runbook "no
  fire-and-forget" + cost-consciousness — 3 real billable VM launches already spent chasing this with zero throughput
  data produced).
