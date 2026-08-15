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

**CONFIRMED 2026-08-15 (slot-6, infra craft, todo 1) — the hypothesis was correct.**
`gcloud projects get-iam-policy central-element-323112 --format=json` (a project-level IAM read, does NOT trip the
object-op hook) shows: `uts-test-sa` holds `roles/storage.objectViewer` **UNCONDITIONED** (project-wide read — confirms
it CAN fetch `vm/setup-data-pipeline-vm.sh`), but its `roles/storage.objectAdmin` (write) grants are BOTH
IAM-conditioned to `-test-`-suffixed DATA-tier buckets only (`group-a-test-tier-only` / `group-b-test-tier-only`
conditions — `resource.name.startsWith("projects/_/buckets/features-*-test-")` etc.) —
**`deployment-scripts-central-element-323112` matches NEITHER condition**, so `uts-test-sa` has zero write access to it.
Exactly the observed symptom: the VM can read its startup script but can never write `vm-logs/<vm>/run.log` or
`EXIT_STATUS`.

## Todos

- [x] ✅ [INFRA] P1. Confirm or refute the `uts-test-sa` IAM hypothesis above: check `uts-test-sa`'s actual bucket-level
      IAM bindings on `deployment-scripts-central-element-323112` (both the `vm/` prefix read path and the `vm-logs/`
      prefix write path) via `gcloud projects get-iam-policy central-element-323112` or the IAM Admin API (not a
      bucket-object CLI call, per the hook note above). If confirmed, grant the missing role (least-privilege — the
      specific role that closes the specific gap, self-service per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) and re-verify with one real
      `features-e2e-tradfi-*` launch, checking for a real `run.log` this time. (repo: deployment-service / infra — live
      GCP IAM change, not code)

          **PROVEN 2026-08-15 (slot 5, infra craft) — the fix works, todo DONE.** Picked up todo 2 below (dispatched
              independently by the backlog) and found todo 1 already in-flight; continued monitoring its verification VM
              instead of duplicating work. `features-e2e-tradfi-20260815-100817-679e08` progressed through the FULL real
              lifecycle for the first time across 4 total attempts on this launch shape: `EXIT_STATUS=RUNNING` written at
              ~10:14Z (the early sentinel `vm-exec-with-gcs-tee.sh` writes at start — never written on any of the 3 prior
              failures), then `run.log` appeared, then `EXIT_STATUS=0` at 10:15:07Z with a clean `DEPLOYMENT_COMPLETED
              exit_code=0` — the VM ran its full command and self-deleted normally, not the silent self-delete-with-zero-objects
              crash this whole doc tracks. Confirms the `uts-test-sa` write-access gap really was the sole cause of the
              self-delete/no-log symptom. **Independently corroborated 2026-08-15 (slot-6, infra craft)** via
              `gcs_describe_object`/`gcs_read_object_with_generation` on the same VM: `run.log` = 27,656 bytes
              (`last_modified=2026-08-15T10:15:16Z`), `EXIT_STATUS` = `b'0\n'` (generation `1786788913139745`) — matches
              slot-5's finding exactly; see the SCRIPT P2 todo below for a related poll-loop bug this cross-check also
              surfaced.

- [x] ✅ [INFRA] P1. If the IAM hypothesis is refuted, get real evidence of what actually kills the VM in its first
      ~30-60s of boot — **N/A, not executed: the hypothesis was CONFIRMED (todo 1 above), not refuted**, so this
      diagnostic branch's own precondition never applies. Checking it off as resolved-by-the-other-branch rather than
      leaving it dangling — see todo 1's "PROVEN" note for the evidence. (repo: deployment-service)
- [ ] [SCRIPT] P2. Once root-caused, add a regression signal for this specific failure mode: `launch_vm_and_wait`/the
      pipeline_e2e_check engine already distinguishes `vm_self_deleted_no_exit_status` from `timeout_no_exit_status` in
      its `reason` field (per a prior agent's read this session) but the shard-result `reason` string surfaced in the
      `.md`/`.json` report currently does NOT include that distinction (both attempts' reports show the same generic
      `window=... wall_clock=...Ns ... objects=0` text) — thread the launcher's self-delete/timeout distinction into the
      report's `reason` field so a future reader doesn't have to re-derive it from the raw JSON `exit_status`/duration
      the way this doc's author had to. (repo: unified-trading-library or features-service, wherever the report-writer
      lives)

      **NEW related finding, same verification run (2026-08-15, slot-6, infra craft):** `_poll_until_terminal` has a
          separate false-negative bug, distinct from the reason-field gap above. The VM's `EXIT_STATUS` object goes through
          an intermediate state — content literal `"RUNNING"` — written early and overwritten with the real numeric code
          (`"0\n"`) only once the deployment actually finishes. The poller's tick-5 log line proves it hit this window mid-flight:
          `EXIT_STATUS present but unreadable/unparsable: invalid literal for int() with base 10: 'RUNNING'` — and instead of
          treating an unparsable-but-present `EXIT_STATUS` as "not yet terminal, keep polling," it gave up immediately and the
          report was written with `exit=-1, failed, objects=0`. Ground truth (checked ~1 minute later, same run, no new
          launch): `EXIT_STATUS` had already flipped to `0` and `run.log` existed complete — i.e. **the run actually
          succeeded but was reported as failed** because the poller read it at exactly the wrong moment and did not retry.
          This is a real, reproducible false-negative in the terminal-detection logic, not a flaky one-off — add explicit
          handling for the `RUNNING` sentinel (treat as non-terminal, continue polling) alongside the reason-field work above.

- [ ] [DATA] P1. Once fixed, relaunch `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s "Todo 2: relaunch
      TRADFI:volatility benchmark once todo 1 lands"
      (`pipeline_e2e_check.py --day <fresh> --asset-group TRADFI --family volatility --legs benchmark --benchmark-days 7`)
      and flip that todo's checkbox with the real throughput numbers this doc's author was trying to capture. (repo:
      features-service) **NOT satisfied by the 2026-08-15 slot 5 verification launch** — that launch proved the
      IAM/self-delete fix (todo 1) but reported `Completed 0/11 groups`, a genuine ZERO-throughput result, not real
      numbers to cite. Still needs a real successful relaunch once the new [DATA] P1 finding below is resolved.
- [ ] [DATA] P1. **NEW (found 2026-08-15 slot 5).** The verification VM's `run.log` shows every one of the 11 feature
      groups failing identically: `No data for VX on <date>` (VIX/variance-risk-premium/vol_greeks_features all depend
      on a captured VX perp that's absent) immediately followed by
      `empty_confirmed manifest write failed ...     record_empty(reason=SOURCE_RETURNED_ZERO) requires FetchEvidence proving a clean 200+empty fetch ... The     supplied evidence does NOT prove honest absence ... most likely an auth / rate-limit / 5xx / timeout /     exception / missing-credential path masquerading as honest absence — call record_failed instead`.
      This is a DISTINCT bug from the IAM/self-delete issue this doc otherwise tracks — the VM now runs to completion
      cleanly (`exit_code=0`), but the underlying feature-compute path can't tell a genuine data gap from a masked fetch
      failure and is being refused (correctly, per the guard's own honest-absence contract) rather than silently
      recording a false empty. Root-cause whether VX perp data is genuinely uncaptured for 2026-08-07..14 (a real gap,
      in which case the benchmark needs a day range that actually has data) or whether the fetch itself is silently
      failing (auth/rate-limit/etc., in which case that's the real bug to fix). Full evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-tradfi-20260815-100817-679e08/run.log`.
      (repo: features-service)

      **Independently corroborated 2026-08-15 (slot-6, infra craft)** via a direct `run.log` read of the same VM —
          identical `Completed 0/11 groups` result, same `No captured perp for VX` / `No data for VX` /
          `empty_confirmed manifest write failed` pattern across every group and date. One addition to the guidance above:
          relaunching with the SAME recent window will reproduce this 0/11 result — check the manifest for a window with
          confirmed VX captures before spending another billable VM launch on this todo, don't retry blind.

## Progress Log

- **2026-08-15 (slot-6, backend_engineer)**: filed after 3/3 reproduction while working
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s benchmark-relaunch todo. Left that todo's checkbox UNCHECKED
  (done_definition — "capture real throughput" — not met; 0 objects captured in all 3 attempts) and cited this doc in
  its Progress Log rather than silently marking it done or retrying indefinitely (VM-launcher-runbook "no
  fire-and-forget" + cost-consciousness — 3 real billable VM launches already spent chasing this with zero throughput
  data produced).

- **2026-08-15 (slot-6, infra craft, todo 1, IN PROGRESS — root cause confirmed + fix applied, verification pending)**:
  dispatcher immediately offered this doc's own todo 1 back to the same slot after the filing above. Adopted infra craft
  (was backend_engineer for the prior todo). Confirmed the IAM hypothesis live via `gcloud projects get-iam-policy`
  (project-level read, not object-scoped — avoids the hook block that stopped bucket-level inspection earlier):
  `uts-test-sa` has unconditioned project-wide `storage.objectViewer` but its `storage.objectAdmin` grants are
  conditioned to `-test-`-suffixed DATA-tier buckets only, excluding `deployment-scripts-central-element-323112`
  entirely. Self-granted a narrow, bucket-scoped IAM condition (title `deployment-scripts-bucket-test-sa-vm-logs`)
  rather than widening `uts-test-sa` project-wide — verified live in a fresh policy read. Launched a real verification
  VM (`features-e2e-tradfi-20260815-100817-679e08`) to prove the fix closes the gap (not just that the policy read looks
  right) — **still running when this session ended; the next session/agent should check
  `gs://deployment-scripts-central-element-323112/vm-logs/ features-e2e-tradfi-20260815-100817-679e08/run.log` for
  existence before doing anything else with this todo.** See todo 1's own note above for the exact next-step branching
  (fix proven vs. hypothesis needs revisiting).

- **2026-08-15 (slot 5, infra craft)**: dispatched todo 2 (the "if refuted" diagnostic branch) independently of slot-6's
  todo 1 work; on picking it up found todo 1 already in-flight with a verification VM running, so continued monitoring
  that VM to terminal state instead of duplicating a second diagnostic launch.
  `features-e2e-tradfi-20260815-100817-679e08` reached `EXIT_STATUS=0` / clean `DEPLOYMENT_COMPLETED` — the FIRST time
  in 4 total attempts on this launch shape that ANY object (let alone a real `run.log` + non-`RUNNING` `EXIT_STATUS`)
  was ever written. **Flipped todo 1 (proven) and todo 2 (N/A — hypothesis confirmed, not refuted, so its own diagnostic
  precondition never applies).** The VM's `run.log` also surfaced a genuinely NEW, distinct bug: all 11 feature groups
  reported `Completed 0/11 groups` — every group hit `No data for VX` then an `empty_confirmed manifest write failed`
  guard rejection (the write correctly refuses to record a masked failure as honest absence). Filed as a new [DATA] P1
  todo above and annotated todo 4 (the "capture real throughput" relaunch) as NOT YET satisfied — the launch mechanism
  works now, but zero real throughput numbers exist to cite. Did not attempt to root-cause the
  VX-data-gap-vs-masked-failure question itself — genuinely distinct domain (features-service data correctness) from
  this doc's IAM/infra scope, out of proportion for this already-large infra todo to absorb inline.

- **2026-08-15 (slot-6, infra craft, todo 1, DONE — independently corroborated slot-5's result)**: re-checked the same
  verification VM's GCS objects directly (`run.log` 27,656 bytes, `EXIT_STATUS=b'0\n'`) and reached the identical
  conclusion as slot-5 above before seeing their push — both sessions confirmed the IAM fix from the same live evidence.
  Adds one finding slot-5's entry doesn't cover: while re-reading the driver's own poll log
  (`launch_vm_and_wait(...): poll tick 5 ... WARNING ... EXIT_STATUS present but unreadable/unparsable: invalid literal for int() with base 10: 'RUNNING'`),
  confirmed the pipeline_e2e_check REPORT for this run was written as `failed, exit=-1, objects=0` — i.e. **the
  automated report says this run failed, even though it actually succeeded** (this doc, and slot-5's own note, only know
  that from manually re-reading `EXIT_STATUS` after the report already wrote `-1`). Added this as a second, distinct
  amendment to the `[SCRIPT] P2` reason-field todo above: `RUNNING` is a valid non-terminal `EXIT_STATUS` value that
  `_poll_until_terminal` currently treats as an unparsable failure instead of "keep polling." Also updated
  `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s todo 2 with a matching infra-fixed/now-data-blocked note +
  Progress Log entry (unconflicted, shipped in the same commit as this doc). Calling `/done` on the AO task scoped to
  this doc's todo 1 (`features_e2e_test_run_vm_self_deletes_no_log-d63cea8bbc07`) since that specific scope is complete
  and doubly verified; the remaining todos (poll-loop fix, VX-data-gap root cause, benchmark relaunch) are separate
  follow-on work already tracked above for a future dispatch.
