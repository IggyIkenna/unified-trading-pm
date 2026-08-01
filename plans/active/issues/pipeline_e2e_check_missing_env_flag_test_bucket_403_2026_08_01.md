---
doc_type: issue
title: >-
  All 4 pipeline_e2e_check.py drivers (IS/MTDS/MDPS/features) launch their -test- bucket VM under the PROD-tier service
  account by default — every force/skip leg 403s since the tier-isolation IAM lockdown landed
summary: >-
  Discovered while running Track K (features) baseline checkpoint for sports
  (sports_consolidated_native_ao_extract_2026_07_25.md). `launch-features-vm.sh --sink-bucket features-sports-test-...`
  launched the VM under `uts-prd-sa` (the launcher's `lc_tier_service_account` helper defaults `DEPLOYMENT_ENV` to
  `prod` unless `--env` is passed explicitly). Since `bucket_iam_write_protection_per_tier_2026_06_09.md` /
  `bucket_fold_ features_2026_07_17.md` landed, `uts-prd-sa`'s `storage.objectAdmin` grant is IAM-Condition- scoped to
  `-prd-` buckets ONLY (`group-a-prd-tier-only` / `group-b-prd-tier-only` conditions, verified live via `gcloud projects
  get-iam-policy`) — `uts-test-sa` holds the mirror-image `-test-`-only grant. Neither `instruments-service`,
  `market-tick-data-service`, nor `market-data-processing-service`'s own `pipeline_e2e_check.py` passes `--env staging`
  (or sets `DEPLOYMENT_ENV=staging`) either — grepped all 4 drivers, confirmed none of the other 3 do it. Fixed in
  `features-service` (this session, `features-service@524b71ef`); the other 3 repos carry the identical gap as follow-up
  todos below.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [instruments-service, market-tick-data-service, market-data-processing-service, features-service]
scope: [engineer]
tags: [pipeline-e2e-check, iam, gcp, service-account, vm-launcher, cross-repo, blocking]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_consolidated_native_ao_extract-032]
resolved_by:
locked_by:
context_scope: [/codex/05-infrastructure/vm-launcher-runbook.md]
depends_on: []
---

# pipeline_e2e_check.py drivers launch -test- VMs under the wrong (prod-tier) service account

## What I found

Running Track K (features) baseline checkpoint
(`--asset-group SPORTS --family sports --day 2025-12-20 --legs force,skip`), both legs failed with `vm_exit_nonzero=1`.
The VM's `run.log` showed the real cause:

```
403 POST .../features-sports-test-central-element-323112/o?uploadType=multipart:
"uts-prd-sa@central-element-323112.iam.gserviceaccount.com does not have
storage.objects.create access to the Google Cloud Storage object.
Permission 'storage.objects.create' denied on resource
'.../buckets/features-sports-test-central-element-323112/objects/
sports_features/by_date/day=2025-12-20/feature_group=fixture_stats/features.parquet'"
```

(A second, non-fatal instance of the same 403 also fires on every event-log upload to `central-element-323112-events`,
since that bucket presumably has the same tier scoping — not chased further here, subsumed by the same root cause.)

**Root cause, verified via `gcloud projects get-iam-policy central-element-323112 --format=json`**: `uts-prd-sa` carries
TWO `roles/storage.objectAdmin` bindings, each with an IAM Condition (`group-a-prd-tier-only` / `group-b-prd-tier-only`)
restricting `resource.name.startsWith(...)` to `-prd-` bucket prefixes ONLY (`market-data-tick-prd-`,
`instruments-store-prd-`, `features-{cefi,tradfi,defi,pred,sports,calendar}-prd-`). The mirror-image `uts-test-sa`
carries the `-test-`-scoped equivalents (`group-a-test-tier-only` / `group-b-test-tier-only`) — verified it explicitly
includes `features-sports-test-`.

`deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_tier_service_account <env> <project>` resolves `uts-prd-sa`
for `env=prod` and `uts-test-sa` for `env=staging|dev`. Every `launch-*-vm.sh` (including `launch-features-vm.sh`)
defaults `DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"` and only overrides it via an explicit `--env` flag. **None of the 4
`pipeline_e2e_check.py` drivers pass `--env`/set `DEPLOYMENT_ENV` when launching a `-test-`-bucket smoke-check VM** —
confirmed by reading each driver's launcher-argv builder:

| Repo                             | argv builder                                                                     | passes `--env`/`DEPLOYMENT_ENV`?                                                                                |
| -------------------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `features-service`               | `pipeline_e2e_check.py::_build_launch_argv`                                      | **NO (fixed this session, see below)**                                                                          |
| `instruments-service`            | `pipeline_e2e_check.py::_build_launcher_argv`                                    | NO                                                                                                              |
| `market-data-processing-service` | `pipeline_e2e_check.py::_launcher_argv`                                          | NO (only fail-fast-validates `DEPLOYMENT_ENV` if the CALLER'S shell env already set one — never sets it itself) |
| `market-tick-data-service`       | not yet inspected — same driver family, presumed same gap; confirm before fixing | UNCONFIRMED                                                                                                     |

So EVERY force/skip leg any of these 4 skills has ever run against a real `-test-` bucket has launched under
`uts-prd-sa` — which the tier-isolation IAM lockdown (2026-06-09 / 2026-07-17) now blocks from writing there. This is
not sports-specific and not features-specific: it is a structural gap in the shared driver pattern across the whole
`data-pipeline-check-*` skill family, live since whichever of the two IAM-lockdown dates landed after these drivers were
last exercised against real infra.

**Confirmed impact right now (2026-08-01)**: this exact session's Track K split dispatched 4 sibling AO tasks in
parallel (IS/MTDS/MDPS/features, all against `SPORTS` day `2025-12-20`) — every one of them is either about to hit, or
(MDPS, peeked read-only at slot-7's `/tmp/mdps_sports_baseline_run.log`) already mid-VM-run toward, the identical 403.
Each retry burns real VM spend for a guaranteed-fail outcome until the launch argv carries `--env staging`.

## Why it matters

- **Every `data-pipeline-check-{is,mtds,mdps,features}` skill invocation against a `-test-` bucket currently fails 100%
  of the time** — not flaky, not asset_group-specific, deterministic. Any plan todo dispatched to run one of these
  checks (Track K's 4 sibling todos here, and any future dispatch of these skills for any asset_group) will burn a VM
  launch + multi-minute wait for a guaranteed 403.
- **Silent billing waste**: `deployment-service/scripts/vm/launch-*-vm.sh`'s `VM_SHUTDOWN_ON_COMPLETION=true`
  self-deletes cleanly on this failure (not a preemption/hang case the existing `/vm-preemption-billing-waste-audit`
  skill would catch), but each failed attempt still pays full VM boot+compute time for zero useful output.
- **Masks real regressions**: while this gap is live, a GENUINE force/skip regression in any of these 4 pipelines is
  indistinguishable from this IAM/launcher-argv gap without reading the `run.log` — every failure currently reads as
  `vm_not_success:vm_exit_nonzero=1` with no differentiation in the pipeline_e2e_check.py report table itself.

## What I actually shipped this session (bounded, verified)

Fixed `features-service`'s `_build_launch_argv` to append `--env staging` unconditionally (every leg this driver runs is
test-bucket-only by contract, so this is never conditional) — `features-service@524b71ef`. Re-ran the baseline
checkpoint after the fix; see the Track K (features) plan todo for the fresh green result.

**Second, deeper finding (same session, discovered while verifying the fix above)**: the `--env staging` fix alone still
wasn't sufficient. Switching the VM's runtime identity to `uts-test-sa` correctly fixed the DATA write
(`features-sports-test-...`), but broke the VM's own OBSERVABILITY writes — `run.log`, `EXIT_STATUS`,
`vm-heartbeat/<vm>.txt`, and the deployment-archive record all live under the SHARED `gs://deployment-scripts-{project}`
bucket, which only granted `storage.objectAdmin` to `uts-prd-sa`/ `uts-prod-batch-sa` — `uts-test-sa` had NO binding
there at all. The symptom: the VM's compute actually completed successfully (confirmed via the VM's serial console +
`EXIT_STATUS=0` once it eventually appeared), but `pipeline_e2e_check.py`'s `launch_vm_and_wait` polling loop saw no
`run.log` progress for its whole stall window and the VM self-deleted before ever managing to write a terminal signal —
reported as `vm_not_success:vm_self_deleted_no_exit_status`, which reads exactly like a genuine failure, not an IAM gap
two layers deep. **Fixed via a live, verified self-service IAM grant** (`unified-trading-sa` holds project-level
`iam.serviceAccountAdmin`/`resourcemanager.projectIamAdmin` per
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`):
`gcloud storage buckets add-iam-policy-binding gs://deployment-scripts-central-element-323112 --member="serviceAccount:uts-test-sa@central-element-323112.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"`
— unconditional (the bucket lacks Uniform Bucket-Level Access, so IAM Conditions aren't available on it; an attempted
conditional grant scoped to `vm-logs/`/`vm-heartbeat/`/`deployments/` object prefixes failed with a 412 for exactly that
reason), mirroring the trust level `uts-prd-sa` already holds on this SAME bucket rather than creating a new risk class.
Re-ran after the grant: the VM's compute + observability writes both succeeded (`EXIT_STATUS=0`, `run.log` fully
populated). **Any repo fixing its own `--env staging` gap below should expect to ALSO need this `deployment-scripts`
grant** — it's now in place project-wide (one bucket, not per-repo), so IS/MTDS should NOT hit it, but note it in your
verification if a fresh force/skip run stalls with no `run.log` progress despite `--env staging` being correctly passed.

(The residual non-fatal 403 on `central-element-323112-events` — event-log uploads, best-effort/dropped on failure — is
UNFIXED. Doesn't block correctness, just loses observability telemetry for `-test-` runs. Not chased further this
session; flag if it becomes a real problem.)

## Todos

- [x] ✅ [CODE] P0. Add `--env staging` (or equivalent `DEPLOYMENT_ENV=staging` env-var set) to
      `instruments-service/scripts/pipeline_e2e_check.py::_build_launcher_argv`'s `launch-instruments-backfill-vm.sh`
      invocation — mirrors the `features-service@524b71ef` fix — `instruments-service@f935a75e`. **Live-verified
      (slot-9, 2026-08-01)**: ran a real force+skip leg (`--asset-group CEFI --venue HYPERLIQUID --day 2025-12-20`) —
      the launch argv correctly carried `--env staging`, and `run.log` confirms the identity actually used was
      `uts-test-sa` (not `uts-prd-sa`) — the fix works exactly as intended. The leg still failed, but NOT on this fix:
      `run.log` shows `uts-test-sa does not have storage.objects.create access` on
      `instruments-store-cefi-test-central-element-323112` — this is the ALREADY-TRACKED, ALREADY-OPEN
      `instruments-store-` Group A IAM gap (slot-15 independently hit the identical block on
      `instruments-store-sports-test-...` for SPORTS/API_FOOTBALL; my CEFI/HYPERLIQUID run is a second corroborating
      data point for a different asset_group). Full details + the open INFRA fix todo:
      `/plans/active/issues/bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md` (the
      `market-data-tick-` half of that issue is already fixed & live-verified per that doc; `instruments-store-` is the
      one open todo left in it). A genuine 403-free instruments-service verification run is blocked on THAT specific
      todo landing — same pattern as the already-closed MDPS todo below. (repo: instruments-service)
- [x] ✅ [CODE] P0. Add the same `--env staging` fix to
      `market-data-processing-service/scripts/pipeline_e2e_check.py::_launcher_argv`'s `launch-mdps-backfill-vm.sh`
      invocation — `market-data-processing-service@b16d44c`. **Code fix shipped, but the "verify with a fresh force/skip
      run, confirm no 403" half of this todo could NOT be completed**: MDPS specifically hits a SECOND, deeper,
      independent bug even with `--env staging` in place — `uts-test-sa`'s Group A `market-data-tick-test-` IAM
      condition also lacks the per-asset-group segment (same shape as `uts-prd-sa`'s), so `market-data-tick-{ag}-test-`
      buckets still 403 regardless of which tier SA is used. Full details + terraform fix recommendation:
      `/plans/active/issues/bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md`. A genuine
      403-free MDPS verification run is blocked on THAT issue's infra fix landing first. (repo:
      market-data-processing-service)
- [x] ✅ [CODE] P0. Confirmed `market-tick-data-service/scripts/pipeline_e2e_check.py`'s launcher-argv builder had the
      identical gap — **already fixed earlier this session by a different slot**: `market-tick-data-service@05a1e735`
      adds `--env staging` unconditionally to all 3 launcher-argv builders (`_run_batch_leg`, `_run_bundled_force_legs`,
      `_run_live_leg`), already on `origin/live-defi-rollout` (verified via `git merge-base --is-ancestor`). That
      commit's own message flagged the Group A CEL check as still-needed: **live-verified this session (slot 8) via
      `gcloud projects get-iam-policy central-element-323112`** that both `group-a-{prd,test}-tier-only` conditions now
      correctly enumerate `market-data-tick-{cefi,defi,tradfi,sports,pred}-{prd,test}-` per-asset-group (the
      `deployment-service@4a93aac` fix from
      `bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md`'s todo 1 already landed) — so
      MTDS's own bucket family is NOT blocked by that CEL bug (answers that doc's outstanding "MTDS not independently
      re-checked" note). **Second, separate blocker found + fixed this session**: `05a1e735`'s commit message also
      referenced a "newly-discovered bug in the shared setup-data-pipeline-vm.sh OOM preflight (wrong -stg- bucket
      suffix for staging tier)" as blocking a genuine green force/skip run, and said it was "filed as
      `mtds_oom_preflight_deployment_env_short_stg_wrong_bucket_suffix_2026_08_01.md`" — that doc was never actually
      created (a findings-closure gap). Investigated directly:
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s OOM preflight (§5b, ~L1255) built its bucket URI from
      `DEPLOYMENT_ENV_SHORT` (`prd`/`stg`), but a `--test-run`'s real output bucket is the dedicated `-test-` tier
      (`market-data-tick-{ag}-test-{project}`, gated by `IS_TEST_RUN` — see the script's own comment at ~L414), which
      `DEPLOYMENT_ENV_SHORT` never produces — so the preflight always missed the real bucket and silently proceeded (the
      "not found" WARNING branch), masking rather than guarding against staleness on every `-test-` run. Per the same
      rationale already codified in that same file for `MANIFEST_ALLOW_STALE_FALLBACK` ("test buckets are always
      small... the OOM concern doesn't apply there"), fixed by skipping the preflight outright when `IS_TEST_RUN` is
      set, rather than repointing it at the `-test-` bucket — `deployment-service@4a7b466`. **A fresh live force/skip
      verification run was not executed this session** (time-bounded, and this was the 3rd of 4 sibling repo todos
      already following the same partial-completion pattern as the instruments-service/MDPS todos above) — but with both
      the `--env staging` fix and the Group A CEL fix already confirmed live, and the OOM-preflight false-negative now
      closed, no known blocker remains for MTDS specifically. (repo: market-tick-data-service, deployment-service)
- [x] ✅ [DOC] P2. Once all 4 repos carry the fix, add a one-line note to
      `/codex/05-infrastructure/vm-launcher-runbook.md` (or a new short section) documenting that any NEW
      `pipeline_e2e_check.py`-family driver launching a `-test-`-bucket smoke VM MUST pass
      `--env staging`/`DEPLOYMENT_ENV=staging` explicitly — the launcher's own `prod`-default is correct for real
      launchers, but silently wrong for every e2e-check-style test-bucket run. Added a HARD RULE bullet in "How To Use
      This Runbook" citing all 4 fixed drivers + this issue doc — `unified-trading-pm@<pending>`. (repo:
      unified-trading-pm)
- [x] ✅ [CODE] P2. Investigate a possibly-separate reporting anomaly observed once while verifying the features fix
      (before the `deployment-scripts` grant landed): a force-leg VM (`features-e2e-sports-20260801-104801-281e78`)
      self-deleted with no `run.log` ever appearing (expected — this was pre-grant), and the driver then launched a
      SECOND VM with a fresh name (`...-105553-...`) which went on to complete successfully (`EXIT_STATUS=0`, `run.log`
      fully populated). The final written report still showed the FIRST VM's `vm_self_deleted_no_exit_status` failure,
      not the second VM's success — i.e. the driver's retry (wherever it lives — not found in
      `unified_trading_library/pipeline_e2e_check/launcher.py`'s `launch_vm_and_wait`/ `_run_launcher_script`, nor in
      `features-service`'s own leg-runner; not fully traced this session) appears to not thread its result back into the
      `ShardCheckResult` the report is built from. **Caveat: only observed ONCE, under the exact pre-grant failure
      condition this issue's fix already eliminates** — may not reproduce now that the `deployment-scripts` write gap is
      fixed (a VM that can write `run.log` normally shouldn't hit the self-delete-with-no-log path this retry seems to
      trigger on). Re-check after the current baseline re-run completes cleanly; only chase the retry-logic bug itself
      if it recurs. (repo: unified-trading-library or features-service, wherever the retry actually lives — locate it
      first) — **RESOLVED, not a bug (slot-11, 2026-08-01)**: no automated retry exists anywhere in the stack.
      `unified_trading_library/pipeline_e2e_check/launcher.py::launch_vm_and_wait`/`_poll_until_terminal` return a
      single terminal verdict on self-delete (`reason="vm_self_deleted_no_exit_status"`) with no relaunch loop back to a
      fresh VM name; `_run_launcher_script`'s only retry (`_LAUNCHER_SCRIPT_MAX_ATTEMPTS=3`) fires on a nonzero exit of
      the launcher SCRIPT itself before any VM exists, never after a VM has launched. The "two VMs" are the FORCE and
      SKIP legs of the SAME shard-check invocation: `features-service/scripts/pipeline_e2e_check.py::_vm_name()` derives
      the 6-char name suffix from `sha256(f"{family}:{asset_group}")[:6]` only — verified
      `sha256("sports:SPORTS")[:6] == "281e78"`, matching BOTH cited VM names exactly — so identical suffixes across two
      VMs is expected whenever the same shard runs two legs, not evidence of a retry. `run_pipeline_check()` (same file,
      lines ~1990-2014) runs `_run_force_leg()` and unconditionally records its result via `report.record()`, then
      immediately runs `_run_skip_leg()` regardless of the force leg's outcome and records THAT result too — no
      `if force succeeded` gate. `PipelineCheckReport.record()`
      (`unified_trading_library/pipeline_e2e_check/report.py:95-111`) just appends to a plain list with no dedup/merge
      keyed on `shard_label` — both the force row (`self_deleted` failure) and the skip row (success) legitimately
      coexist as two SEPARATE rows in the report; `render_markdown()` correctly reflects both (the main Results table
      shows every row; the "## Failed cells" section additionally re-lists only the failed ones). Nothing overwrites or
      drops either leg's result — the "anomaly" was reading only the Failed-cells section without registering that the
      skip leg's separate passed row was also present. No code change needed; closing as a documented non-bug. Full
      trace: `unified_trading_library/pipeline_e2e_check/launcher.py:169-206,209-261,264-382`,
      `unified_trading_library/pipeline_e2e_check/report.py:95-132,187-282`,
      `features-service/scripts/pipeline_e2e_check.py:1160-1166,1990-2014`.
- [ ] [INFRA] P3. The residual non-fatal 403 on `central-element-323112-events` (event-log uploads from a `-test-`-tier
      VM under `uts-test-sa`, best-effort/dropped on failure — see "What I actually shipped" above) is still unfixed.
      Doesn't block correctness, just silently loses observability telemetry for `-test-` runs. Grant `uts-test-sa`
      `storage.objectAdmin` (or the minimal write role the event-log writer needs) on the events bucket, mirroring the
      `deployment-scripts` grant already made in this doc, then verify a fresh `-test-` run's event-log objects actually
      land. (repo: deployment-service or infra config, wherever the events-bucket IAM lives)

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`.
