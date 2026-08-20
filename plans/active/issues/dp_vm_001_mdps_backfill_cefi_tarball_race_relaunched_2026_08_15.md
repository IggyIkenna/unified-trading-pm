---
doc_type: issue
title:
  DP-VM-001 exit_code=1 on mdps-backfill-cefi-20260814-014809 — root-caused to a transient UTL/UAC tarball cross-repo
  staleness race, relaunched successfully; a SEPARATE lc_verify_tarball_freshness auto-mode race found + worked around
  in the process
summary: >-
  A data-pipeline fleet monitor (exit-code-aware,
  `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py`) detected VM
  `mdps-backfill-cefi-20260814-014809` (cefi liquidations MDPS backfill, 2022-03-03→2026-01-31) terminated with
  exit_code=1. Unlike the two same-day sibling DP-VM-001 findings
  (`dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md`,
  `dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md`, both correctly declined to relaunch —
  exhausted family bound, no diagnosis attempted), this worker pulled `run.log` via the GCS SDK helpers and found a
  deterministic root cause: the VM's process crashed at IMPORT TIME with `AttributeError: type object 'PipelineMode' has
  no attribute 'BATCH_MORPHO'` inside `unified_trading_library.pipeline_mode_resolver` — the tarball pairing this VM
  launched with carried a `unified-trading-library` snapshot whose `pipeline_mode_resolver.py` already referenced
  `PipelineMode.BATCH_MORPHO` paired with an `unified-api-contracts` snapshot that did not yet define that enum member
  (both repos are confirmed MUTUALLY CONSISTENT at current HEAD — `BATCH_MORPHO` exists in UAC's `PipelineMode` and is
  referenced correctly by UTL). This is a 100%-deterministic import-time crash (not a flake/OOM/preemption) — every
  invocation of that exact tarball pairing fails identically. The `mdps-backfill-cefi-` family's relaunch-dispatch
  budget was NOT exhausted (confirmed by the escalation's own dispatch context, which carried a plain `RELAUNCH vm=...`
  instruction, not the `DO NOT RELAUNCH` form used when a family's `≤2/(vm-prefix,day)` bound is spent), the OOM
  auto-recover actuator (`RelaunchBackfillVm.relaunch`) explicitly SKIPS non-137 exit codes by design ("the page tier
  owns a non-OOM crash"), no suppression marker existed at
  `vm-census/relaunch-paged/vm/mdps-backfill-cefi-20260814-014809.json`, no live duplicate VM existed, and
  `PROGRESS.json` showed zero progress (`last_completed_date` == the original `RESUME_START_DATE`) — so the shard's data
  was genuinely still fully outstanding. Given the diagnosed root cause was already resolved at current HEAD, this
  worker relaunched via `launch-mdps-backfill-vm.sh` with the RESUME_* env fallback (mirrors `RelaunchPreemptedVm`'s own
  re-invocation pattern). The FIRST relaunch attempt hit a SEPARATE, previously-undocumented bug:
  `lc_verify_tarball_freshness`'s `auto` mode republished all 5 stale tarballs successfully (confirmed via the
  create-code-tarballs.sh upload log — every repo's SHA-pinned tarball uploaded matching this worker's THEN-current
  workspace HEAD) but its post-republish re-verify still reported 4 of 5 repos stale and aborted the launch. Root cause:
  `live-defi-rollout` is a very high-commit-velocity shared branch for
  `unified-trading-library`/`unified-api-contracts`/`market-tick-data-service`/`deployment-service` — this worker's own
  `.tabs/7` workspace clones auto-fast-forward via the standing 5-min `slot-cron-ff-pull.sh`, so by the time
  `create-code-tarballs.sh` finished uploading a tarball pinned to the workspace's HEAD-at-republish-time, the workspace
  HEAD had ALREADY moved again (confirmed directly: re-running `lc_verify_tarball_freshness` in `enforce` mode moments
  later showed the `expected_sha` for those 4 repos had changed since the original republish). A SECOND relaunch attempt
  (run within ~90s of the first) succeeded cleanly once the branch briefly settled —
  `mdps-backfill-cefi-20260815-155830` is RUNNING (SPOT). This is a treadmill/high-churn race, the same class already
  documented for quickmerge (`quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md`) applied to
  the tarball-freshness guard instead — filed as a follow-up P2, not blocking (the guard fails CLOSED/safe, it just cost
  one wasted retry here). A smaller cosmetic P3 was also found in the same code path: the final "still stale" error
  message names the ORIGINAL full stale-repo set rather than just the repos that actually failed re-verification (this
  worker's log showed `market-data-processing-service` individually verified fresh on re-verify yet was still listed in
  the aggregate error).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service, market-data-processing-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    dp-vm-001,
    exit-code-monitor,
    mdps-backfill-cefi,
    tarball-freshness,
    cross-repo-staleness,
    relaunch,
    data-pipeline-monitors,
  ]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md,
    /plans/archive/issues/mdps_vm_stale_uac_contract_propagation_2026_07_20.md,
    /plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md,
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
  ]
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/scripts/vm/launch-mdps-backfill-vm.sh,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    unified-trading-library/unified_trading_library/pipeline_mode_resolver.py,
  ]
created: "2026-08-15"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-7651f8 (wall_type=data_pipeline_failure, dispatched to slot 7, 2026-08-15) carried the finding directly
  ("Filed issue: (none — alert carries the details)"). All evidence below is from direct GCS SDK reads
  (`deployment_service.data_pipeline_monitors._gcs`) and two live launcher invocations this session, not inferred.
---

# DP-VM-001 — mdps-backfill-cefi-20260814-014809 exit_code=1, root-caused + relaunched

## What happened

- VM: `mdps-backfill-cefi-20260814-014809` (asset_group=cefi, launcher-family prefix `mdps-backfill-cefi-` →
  `launch-mdps-backfill-vm.sh` per `launcher_registry.py` — a DIFFERENT launcher family from the `mdps-cefi-` prefix the
  two sibling 2026-08-14 issues cover; a different daily relaunch-dispatch budget).
- `LAUNCH_PARAMS.json`:
  `RESUME_ASSET_GROUP=cefi RESUME_START_DATE=2022-03-03 RESUME_END_DATE=2026-01-31 RESUME_MODE=full MDPS_DATA_TYPES=liquidations DEPLOYMENT_ENV=prod`.
- `PROGRESS.json`: `{"last_completed_date": "2022-03-03", "monotonic": "true"}` — identical to `RESUME_START_DATE`, i.e.
  ZERO progress; the VM crashed before processing a single date.
- Terminal state: `exit_code=1`.

## Root cause (confirmed via `run.log`, pulled through `_gcs.read_text`)

```
Traceback (most recent call last):
  ...
  File ".../utl/unified_trading_library/pipeline_mode_resolver.py", line 171, in <module>
    ("MORPHO", "oracle_prices"): PipelineMode.BATCH_MORPHO,
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: type object 'PipelineMode' has no attribute 'BATCH_MORPHO'
```

Both the main MDPS entrypoint AND the heartbeat_daemon.py sidecar hit this at import time — the whole VM was
non-functional from boot. Confirmed at this worker's session time (2026-08-15):

- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:112` DOES define
  `BATCH_MORPHO = "batch_morpho"`.
- `unified-trading-library/unified_trading_library/pipeline_mode_resolver.py:171` references `PipelineMode.BATCH_MORPHO`
  consistently.

I.e. this is NOT a live code defect — both repos are mutually consistent at current HEAD. The VM launched (2026-08-14
01:48Z) with a `UTL_TARBALL_SHA`/`UAC_TARBALL_SHA` pairing (each auto-resolved independently to "latest in the code
bucket" per `lc_resolve_tarball_sha`) that was NOT mutually consistent at that moment — the UTL side had already landed
a commit referencing `BATCH_MORPHO` while the UAC side's floating tarball had not yet been republished with the enum
member (a cross-repo landing-order/republish-timing race, same CLASS as the MORPHO `lc_verify_tarball_freshness` guard
was built to catch — see `defi_morpho_lending_indices_never_wired_2026_07_12.md` — but that guard only compares each
repo's tarball against ITS OWN workspace HEAD; it cannot catch "repo A's fresh code references something repo B's fresh
code doesn't yet have", a genuinely different failure shape).

## Why this warranted a relaunch (unlike the two sibling 2026-08-14 findings)

Per `rb_infra_relaunch.md`'s bounds + the OOM-relaunch actuator's own design:

1. `RelaunchBackfillVm.relaunch()` explicitly returns `SKIPPED/not_oom` for any `exit_code != 137` — "the page tier owns
   a non-OOM crash" — so no automated actuator ever attempted this relaunch; it was purely a human-equivalent judgment
   call, exactly the model `rb_infra_relaunch.md` describes.
2. The `mdps-backfill-cefi-` family's relaunch-dispatch budget was NOT exhausted (the escalation's dispatch context
   carried a plain `RELAUNCH vm=...` instruction, not `DO NOT RELAUNCH... already hit N/2 relaunch dispatches today` —
   the form `escalation.py:_dispatch_to_orchestrator` emits when `escalation_dedup.check_relaunch_dispatch_budget`
   reports `bounded=True`).
3. No suppression marker at `vm-census/relaunch-paged/vm/mdps-backfill-cefi-20260814-014809.json`.
4. Live fleet had zero VMs matching `mdps-backfill-cefi-*` (`gcloud compute instances list`) — no already-running
   replacement, no risk of a duplicate concurrent shard.
5. Root cause was positively diagnosed (not blind retry) and confirmed already resolved at current HEAD — a fresh launch
   resolves BOTH repos' tarballs to their current (now mutually consistent) HEAD independently.
6. `PROGRESS.json` confirmed the shard's data (cefi liquidations, 2022-03-03→2026-01-31) is genuinely still fully
   outstanding.

## What this worker did

1. Pulled `run.log`/`LAUNCH_PARAMS.json`/`PROGRESS.json`/the suppression marker via the GCS SDK helpers (never
   subprocess `gsutil`/`gcloud storage`) — see `context_scope` script paths.
2. Diagnosed the `BATCH_MORPHO` AttributeError root cause; confirmed both `unified-trading-library` and
   `unified-api-contracts` are consistent at current HEAD (i.e. nothing to fix in either repo's code).
3. Relaunched via
   `RESUME_ASSET_GROUP=cefi RESUME_START_DATE=2022-03-03 RESUME_END_DATE=2026-01-31 RESUME_MODE=full MDPS_DATA_TYPES=liquidations DEPLOYMENT_ENV=prod bash scripts/vm/launch-mdps-backfill-vm.sh`
   (zero positional args — the RESUME_* env fallback, mirroring `RelaunchPreemptedVm`'s own re-invocation pattern).
4. First attempt aborted on `lc_verify_tarball_freshness`'s post-republish re-verify (see Follow-ups P2 below) despite
   the republish itself succeeding (confirmed via the create-code-tarballs.sh upload log matching SHA-pinned copies for
   all 5 repos). Re-ran the launcher ~90s later; it succeeded cleanly
   (`lc_verify_tarball_freshness: all 4 tarball(s) current.`).
5. `mdps-backfill-cefi-20260815-155830` confirmed `RUNNING` (SPOT) via the launcher's own post-create
   `gcloud compute instances list` echo — STARTED verified at T+0.
6. A backgrounded T+10min check (PROGRESS.json + run.log tail) was armed this session; if this doc is picked up before
   that completes, re-check `PROGRESS.json` for `mdps-backfill-cefi-20260815-155830` directly.

## Todos

- [x] ✅ [SCRIPT] P2. `lc_verify_tarball_freshness`'s `auto` mode (deployment-service `scripts/vm/lib/launcher_common.sh`)
      races under high branch churn: it republishes stale tarballs pinned to the workspace's CURRENT HEAD, then
      re-verifies against a FRESH read of that same HEAD — on a fast-moving shared branch (confirmed here for
      `unified-trading-library`/`unified-api-contracts`/`market-tick-data-service`/`deployment-service`, all
      auto-fast-forwarded by the standing 5-min `slot-cron-ff-pull.sh`), the workspace HEAD can move again between
      republish and re-verify, producing a false "still stale" abort even though the just-uploaded tarball WAS correct
      for the HEAD it was built against. Same class as
      `quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md`. Fix: capture `expected_sha` ONCE
      before republish and re-verify against that CAPTURED value (not a fresh `git rev-parse HEAD`), or accept a
      recently-uploaded tarball whose manifest sha matches the sha the republish step itself just built against. —
      **deployment-service@fb55e8ac35**: refactored the auto-mode re-verify to capture `expected_sha` once per repo
      during the initial scan and reuse those captured values (never a fresh `git rev-parse`/`fetch` HEAD read) for
      the post-republish re-verify; factored the manifest-compare logic into `_lc_tarball_manifest_matches` so both
      the initial scan and the re-verify share one comparison path. 25/25 tarball/freshness unit tests green, full
      `quality-gates.sh` green (280s), landed via quickmerge.
- [x] ✅ [SCRIPT] P3. Same function's final "still stale" error message (the `auto`-mode branch, `launcher_common.sh`
      ~line 1149) names the ORIGINAL full `$stale_repos` set rather than just the repos that actually failed the
      post-republish re-verify — confirmed live this session: `market-data-processing-service` individually printed
      `tarball fresh` on re-verify yet was still listed in the aggregate "auto-republish completed but tarball(s) still
      stale" error. Cosmetic (doesn't change the abort/proceed decision) but misleads whoever reads the error into
      re-investigating an already-fine repo. — **deployment-service@fb55e8ac35**: fixed incidentally by the P2 refactor
      above — the re-verify now tracks a `still_stale` set built per-repo from actual re-verify results, so the final
      error names only the repos that genuinely failed re-verify, not the original full `stale_repos` set.
- [ ] [OPERATOR] P3. Consider whether `lc_resolve_tarball_sha`/the tarball-publish pipeline should gate a cross-repo
      symbol reference (a UTL commit landing a new `PipelineMode.<X>` reference) on the corresponding UAC commit already
      being tarball-published, closing the failure CLASS this incident hit (not just this one VM) — out of scope for a
      one-shot relaunch worker to design; flagging per the two prior MORPHO-adjacent incidents
      (`mdps_vm_stale_uac_contract_propagation_2026_07_20.md`, `defi_morpho_lending_indices_never_wired_2026_07_12.md`)
      suggesting this is a recurring MORPHO-rollout-specific pain point, not a one-off (note: that doc has since been
      archived — `/plans/archive/issues/mdps_vm_stale_uac_contract_propagation_2026_07_20.md` — while
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh:173` and `.../lib/launcher_common.sh:917` still cite the
      stale pre-archive `plans/active/issues/...` path; fixed via `deployment-service@c409887930`).

## Progress Log

- 2026-08-15 (slot 7, data_pipeline_failure escalation agt-7651f8): Pulled run.log/LAUNCH_PARAMS.json/PROGRESS.json for
  `mdps-backfill-cefi-20260814-014809` via GCS SDK helpers. Diagnosed root cause (`PipelineMode.BATCH_MORPHO`
  AttributeError, cross-repo UTL/UAC tarball staleness race, confirmed resolved at current HEAD in both repos).
  Confirmed relaunch was warranted (non-OOM SKIPPED by the auto actuator by design, budget not exhausted, no suppression
  marker, no live duplicate, zero progress made). Relaunched via `launch-mdps-backfill-vm.sh` RESUME_* env fallback;
  first attempt hit a separate `lc_verify_tarball_freshness` auto-mode re-verify race under branch churn (filed as P2
  below), second attempt (~90s later) succeeded — `mdps-backfill-cefi-20260815-155830` confirmed RUNNING (SPOT). Filed
  this issue doc with the diagnosis + the two freshness-guard follow-ups (`unified-trading-pm@65edd7c550`).
- 2026-08-15 (same session, ~T+13min): Directly verified progress via the GCS SDK (the backgrounded shell monitor armed
  earlier did not survive across tool turns and produced no output — noted for future sessions: use the harness's own
  `run_in_background` mechanism, not a raw trailing `&`, for anything that must outlive a single Bash call).
  `PROGRESS.json` for `mdps-backfill-cefi-20260815-155830` had advanced to `{"last_completed_date": "2022-03-05", ...}`
  (past the original crash point, genuine forward progress) with `exit_code=None` (still running) and `run.log` showing
  live candle-aggregation output timestamped within the same minute as the check — relaunch confirmed healthy. Fixed +
  shipped the two stale doc-path comment references found in `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh`
  and `.../lib/launcher_common.sh` (QG green, quickmerge landed `deployment-service@c409887930`). `/done` posted with
  `one_shot_complete: true`.
- 2026-08-15 (slot 12, data_pipeline_failure escalation agt-870c6b): A SECOND `relaunch_vm` dispatch for the SAME
  `mdps-backfill-cefi-20260814-014809` finding reached slot 12 (duplicate dispatch of the finding this doc already
  resolved above — same VM name, same `exit_code=1`). Per `rb_infra_relaunch.md`'s "check for an already-running
  replacement before relaunching" step: `gcloud compute instances list --filter="name~mdps-backfill-cefi"` showed
  `mdps-backfill-cefi-20260815-155830` (the relaunch this doc already documents) is **no longer in the live fleet**
  (`terminal exit_code=None` in GCS — no terminal marker written, ambiguous rather than a clean finish) and has been
  superseded by `mdps-backfill-cefi-20260815-181733`, currently `RUNNING`, with `LAUNCH_PARAMS`
  `RESUME_START_DATE=2020-01-01 RESUME_END_DATE=2026-01-31 MDPS_DATA_TYPES=liquidations RESUME_ASSET_GROUP=cefi` — a
  strict superset of the original crashed VM's outstanding range (`2022-03-03→2026-01-31`) — actively progressing
  (`run.log` live output at `2026-08-15T17:48Z`, currently processing `cefi/2020-02-13`). No suppression marker exists
  at `vm-census/relaunch-paged/vm/mdps-backfill-cefi-20260814-014809.json`. This worker did **not** determine the exact
  lineage from `155830` to `181733` (whether `155830` completed cleanly, was itself relaunched by a supervising
  mechanism, or crashed again) — flagging as an open question rather than asserting it, since it wasn't directly
  evidenced. Given a live, healthy, actively-advancing replacement already fully covers the original shard's data,
  launching a further VM here would duplicate the shard — **no relaunch action taken**; this dispatch is a no-op.
  `/done` posted with `one_shot_complete: true`. Open question for a future pass: why did this escalation re-dispatch
  for an already-resolved finding (possible re-fire of the original DP_VM_EXIT_NONZERO event before the first worker's
  relaunch/close registered, or a dedup-window gap in the DP_\* cooldown-map mechanism per
  `/codex/05-infrastructure/data-pipeline-alerts.md` § "Wiring caveat") — not diagnosed further here, one-shot scope.
- 2026-08-16 (slot-6, infra, dispatched via the gated sports P3 diag task
  `sports_mdps_forcevm_timeframe_ceiling_crash_untracked_2026_08_16.md`): Fixed both `[SCRIPT]` todos above —
  `deployment-service@fb55e8ac35` refactors `lc_verify_tarball_freshness`'s auto-mode to capture each repo's
  `expected_sha` once during the initial scan and re-verify the post-republish state against that CAPTURED value
  (never a fresh `git rev-parse`/`fetch` HEAD read), closing the republish/re-verify race; factored the manifest
  compare into `_lc_tarball_manifest_matches` so the initial scan and the re-verify share one comparison path. This
  incidentally fixes the P3 "still stale" error-message todo too, since the re-verify now tracks per-repo failures
  directly instead of re-running the whole check against the original `stale_repos` set. 25/25 tarball/freshness unit
  tests green (`tests/unit/test_vm_launcher_scripts.py -k "tarball or fresh"`), full `deployment-service`
  `quality-gates.sh` green (280s), shipped via quickmerge. Only the P3 `[OPERATOR]` todo remains open on this doc.
- **na-eligibility-audit 2026-08-16** [body-hash:5e1df6c0e9a5d4cc]: KEEP-NA, valid — Doc read end-to-end (frontmatter, root-cause narrative, todos, 4 Progress Log entries 2026-08-15→2026-08-16).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
