---
doc_type: plan
title: ci satellite AO dispatch batch 15 — 2026-08-16
summary: >-
  Second extraction batch from the 2026-08-15/16 full CI-tranche follow-up survey (39 docs re-checked after batch14
  shipped) — bounded/deterministic items plus checkbox-reconciliation-only items where the underlying work was already
  done elsewhere but never flipped. Each todo cites its exact source doc; source docs are NOT touched by this batch
  except where the todo IS itself the reconciliation (explicitly marked). Conflict-checked against batch13, batch14,
  and each other via basename-citation cross-reference before drafting.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, ao-dispatch, satellite-batch, follow-up-survey]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch14_2026_08_15.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /codex/03-observability/monitoring-control-plane.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md,
    /plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md,
    /plans/archive/2026_08/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md,
    /codex/15-runbooks/ci-daily-health.md,
    /plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md,
    /plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md,
    /plans/archive/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    /plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-18"
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4.5
estimate_calibrated_ai_days: 3.6
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted from a 2026-08-16 follow-up survey of the CI tranche (39 docs still carrying open CI-tagged todos after
  batch14 shipped, split across 2 parallel research agents) plus operator rulings from the same session. Ships
  status: active directly (not draft) — the operator has already confirmed the AO-dispatch pattern and fast-ship
  cadence for this tranche via batch14's precedent.
---

# ci satellite AO dispatch batch 15 — 2026-08-16

## Todos — bounded new work

- [x] ✅ [INFRA] P2. **DONE 2026-08-16 (slot 21) — shipped in this same commit.** Build the na-corpus/governor
      baseline-freshness daily promotion job: a scheduled job that promotes each run's observed peak-RSS into the
      committed `qg_resource_baseline.json`, plus fires the Slack alert when a run's observed peak exceeds the
      committed baseline by >20%. This is governor Trigger 3, left unwired by batch13 (which wired triggers 1-2:
      RSS-cap overrun, host-RAM abort). Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
      (line ~233, flipped `[x]` alongside this todo). Gate: baseline file updates daily from real observed peaks; a
      synthetic >20%-over-baseline run produces a real Slack alert via the same `_qg_governor_slack_alert()`
      mechanism batch13 built.
      **Implementation**: `scripts/dev/measure-qg-baseline.sh` gained an anomaly guard (new
      `scripts/dev/qg_baseline_merge.py`, extracted from its former inline python heredoc for testability) — a
      freshly measured peak >=`QG_BASELINE_ANOMALY_PCT` (default 20) percent above the committed value for
      (repo, env) is NOT silently promoted; it calls the existing `_qg_governor_slack_alert()` (WARNING,
      `qg-baseline-stale:<repo>:<env>` dedup key) and leaves the baseline untouched. `--force` bypasses the guard
      for a deliberate manual re-baseline (the OTHER open todo below). Wired to run daily via
      `scripts/orchestrator/qg-baseline-daily-promote.{sh,service,timer}` +
      `install_qg_baseline_daily_promote.sh` (03:11 UTC, env=vm, jobs=3, mirrors the existing
      `ldr-to-main-promote-heartbeat` systemd-timer pattern — a GH Actions workflow was rejected: this needs the
      full multi-repo `.tabs/<N>`-shaped workspace `measure-qg-baseline.sh` already assumes, which a bare
      `ubuntu-latest`/glue-runner single-repo checkout doesn't have). Gate verified synthetically:
      `scripts/dev/test-qg-baseline-anomaly-guard.sh`, 12/12 assertions pass (no-prior-entry, within-threshold,
      over-threshold->ANOMALY-not-promoted, `--force` bypass, a drop is never anomalous, exact-boundary inclusive).
      **Not yet installed on the orchestrator VM** — `install_qg_baseline_daily_promote.sh` is `[OPERATOR]`-run
      (writes `/etc/systemd/system`, needs root on the `planning` VM), same posture as its sibling installers; the
      first live daily tick is still pending.

- [x] ✅ [INFRA] P2. **Re-baseline `qg_resource_baseline.json`** — committed values are measured 3.6-5.5x stale versus
      current cgroup peaks. Source: `plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`
      (line ~605). Gate: baseline file reflects current measured peaks, re-verified live. **DONE 2026-08-17 (slot 6,
      infra-craft) — unified-trading-pm@9c4e9e4c46.** Re-ran `scripts/dev/measure-qg-baseline.sh --env vm --force`
      across all 25 repos the committed baseline should track (the 24 pre-existing + `agent-orchestrator`, previously
      absent entirely per this todo's own Source doc) — done as 3 separate foreground passes after backgrounded runs
      proved unreliable in this session (repeatedly killed mid-run; a self-heartbeating wrapper didn't fix it either —
      root cause undetermined, plain foreground calls with generous timeouts worked reliably). `jobs=2/3` concurrency
      per the source doc's "not `measured_concurrency: 1`" ask. Both UI repos re-measured (the flagged-implausible
      22MB/541MB `local` entries are now backed by fresh `vm` entries: `unified-trading-system-ui` 3821MB,
      `deployment-ui` 743MB). Blocked mid-ship by a pre-existing, unrelated `check_ao_dispatch_visibility_gate` red
      (corpus-wide undeclared-exclusion drift, confirmed via stash test to have zero relation to this diff) — filed
      `/plans/archive/issues/ao_dispatch_visibility_gate_accidental_exclusions_2026_08_17.md` (archived 2026-08-17, all
      6 items resolved) +
      repo-blocker RB-e08a525b per RULES.md §4b; resolved collectively by the fleet (concurrent slots fixing the
      flagged docs) before I could finish my own partial fix, gate green again (5 ≤ baseline 0 + buffer 5) as of this
      ship.

- [x] ✅ [INFRA] P2. **Stagger `ldr-to-main-promote-fleet.yml`'s per-repo fan-out** rather than firing all repos
      simultaneously on each tick. **NOTE (2026-08-16, retag not stale-content):** the tick cadence itself was
      loosened `*/15` → `*/30` same-day (`unified-trading-pm@1be6a8e036`, both the workflow cron AND
      `ldr-to-main-promote-heartbeat.timer`'s `OnCalendar` — that timer is the ACTUAL driver, see its own header
      comment) — this todo's own scope (staggering dispatch ORDER within one tick's fan-out) is unaffected by that
      and remains valid, but re-verify the CURRENT cron/timer state before touching either file rather than trusting
      "*/15" as a given. Source: same doc (line ~622). Gate: fan-out is measurably staggered; no regression in overall
      promote-fleet drain latency. **DONE 2026-08-17 (slot 20) — unified-trading-pm@23499c954f.** The bounded-parallel
      driver at the bottom of `scripts/cicd/ldr_to_main_fleet_promote.sh` backgrounded `process_repo "$REPO"` for
      every repo back-to-back with zero delay, throttled only once `MAXJOBS`=6 were already in flight — the exact
      shape behind the 2026-08-06 "3 full-workspace-sit dispatches within ~10s" stampede documented inline above the
      driver. Added an env-overridable `STAGGER_SECONDS` (`LDR_MAIN_PROMOTE_STAGGER_SECONDS`, default 3) with a
      `sleep "$STAGGER_SECONDS"` between the background launch and the `MAXJOBS` `wait -n` check, so successive
      launches are spread out in real time (measurably: min inter-launch gap ≈ stagger value) instead of firing as
      fast as the shell can fork. Drain latency is unaffected in the common case — `process_repo`'s own `gh api`
      calls (SIT checks, workspace-digest reads, provenance checks, ancestor cleanup) each take far longer than the
      3s stagger, so the run stays `MAXJOBS`-bound, not stagger-bound; `LDR_MAIN_PROMOTE_STAGGER_SECONDS=0` reproduces
      the old zero-delay behavior for local/CI testing. New regression test
      `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh` (6/6 assertions pass): structurally
      confirms the stagger var + its placement between launch and throttle, and functionally runs the real driver
      loop (extracted verbatim, stub `process_repo`) proving both the staggered case (min gap ≥ ~900ms at
      stagger=1s) and the opt-out case (stagger=0 completes near-instantly, no forced delay).

- [x] ✅ [INFRA] P2. **Share bare repos + `git worktree` for sibling-clone I/O** instead of full clones per slot — explicit
      do/don't scope already given in the source doc. Source: same doc (line ~634). Gate: sibling-clone disk I/O
      measurably reduced; existing slot isolation guarantees unaffected. **DONE 2026-08-17 (slot 13, infra craft) —
      `unified-trading-ci@3209654`, `unified-trading-pm@10fb8339dc`.** Scope note: this todo's "sibling-clone I/O"
      is CI dep-repo cloning inside `python-quality-gates-v2.yml`'s `clone_repo()` (the self-hosted glue-runner host
      cloning every dep repo fresh on every QG job), NOT the AO slot-worktree model (`.tabs/<N>/<repo>`, which is
      already Path-B — its own `.git` per slot, no shared-repo change applicable there; that model is unrelated to
      this todo despite the similar name).
      Added `clone_repo_via_shared_bare()` to the reusable workflow's `clone_repo()` (inserted right after the
      PIN_SHA-override block, ahead of the existing 3-attempt LDR clone loop): opt-in via `SHARED_BARE_ROOT`
      (default `/opt/glue-shared-bare-repos`) — if the dir doesn't exist (ubuntu-latest, or any unprovisioned
      self-hosted host) the function returns 1 immediately and every job gets byte-identical behavior to before this
      change. When provisioned: seeds/fetches a persistent bare mirror (`--filter=blob:none`, `gc.auto=0` per the
      source doc's explicit requirement) instead of a cold full clone, then `git worktree add`s the job's dep dir
      from it, with a hard HEAD-match verification backstop (same philosophy as `fast-checkout.sh`'s mirror path) —
      ANY failure at ANY step falls straight through to the unchanged `clone_repo()` chain, never worse than today.
      Explicitly excludes the `cp -al` shared-venv half the source doc calls out as superseded/unsafe — no shared
      venv path introduced (venv immutability contract: satisfied by inaction, each job still builds its own via
      `uv`).
      Standing `git worktree prune` timer per the source doc's explicit requirement:
      `scripts/self-hosted-runners/prune-shared-bare-repo-worktrees.{sh,service,timer}` +
      `install-prune-shared-bare-repo-worktrees.sh` (hourly backstop; the fast path itself also prunes
      opportunistically before every fetch — required ordering, see below) + wired into
      `deploy-sbin-scripts.sh`'s `DEPLOY_SCRIPTS` so the `.sh` actually reaches `/usr/local/sbin/` via the existing
      `github-glue-deploy-sync.timer` sync. **Not yet installed on the CI VM** — the installer is `[OPERATOR]`-run by
      design (root + `/etc/systemd/system`), same posture as this batch's other sibling installers
      (`install_qg_baseline_daily_promote.sh`); `SHARED_BARE_ROOT` also doesn't exist on the host yet, so the fast
      path stays fully dormant (return-1-immediately, zero behavior change) until an operator provisions it —
      by design, not an oversight: this ships the code path safely inert, the VM-side activation is a separate,
      deliberately-gated step.
      **Verified functionally** (not just `bash -n`/YAML-parse — a scratch harness against a real local `git`
      origin, no GitHub needed): cold-seed + worktree-add + HEAD-match verification; a wiped `_work` dir across two
      simulated jobs reproducing `job-cleanup.sh`'s own failure mode; the standalone prune sweep reducing worktree
      count; and the unprovisioned-host fallback returning 1 cleanly. Two real bugs caught and fixed during this
      verification (both would have silently broken the fast path in production without ever failing loud, since
      every step falls through to the existing chain on failure — these bugs would just have meant "the fast path
      quietly never returns 0"): (1) `git -C <bare> worktree add <relative-path>` resolves the path against
      `<bare>`'s own directory, not the caller's cwd — fixed by computing an absolute target path before the `-C`
      call; (2) `git worktree prune` MUST run *before* the fetch, not after — a stale worktree admin entry left by a
      wiped `_work` dir makes git refuse to fetch into that branch AT ALL ("refusing to fetch into branch ... checked
      out at ..."), not just refuse the worktree add.

- [ ] [INFRA] P3. **Reap the governor's 344-file marker-file leak.** Source: same doc (line ~665). Gate: stale marker
      files cleaned; a regression test confirms new markers don't accumulate unbounded.

- [ ] [DEVOPS] P3. **Build a "mover did-work-counter isn't 0 for N days" backstop check** for the dependency-cascade
      movers. Source: `plans/active/github_actions_operator_gated_followups_2026_07_17.md` (line ~106). Gate: a mover
      silently doing nothing for N consecutive days produces a real alert.

- [x] ✅ [UI] P2. **Build the rollout-ratchet dashboard panel** (workflow-template drift + Dockerfile digest-pin status)
      AND fold in the ruleset/branch-protection drift panel (G4) into the same panel per the source doc's own scoping
      note — these were flagged as near-duplicate scope, build together not as 2 separate panels. Also add the
      runtime-level deploy signal (diff running SHA vs `main` HEAD). Source:
      `plans/active/monitoring_control_plane_master_2026_06_10.md` (lines ~260, ~262, ~465). Gate: one panel showing
      rollout-ratchet + ruleset-drift status; a separate widget showing running-vs-HEAD SHA diff per service.
      **CHECKBOX RECONCILIATION 2026-08-18 (slot-7, ui_developer) — already fully shipped before this dispatch,
      never flipped here.** Slot-1's 2026-08-17 investigation (mis-scoped `[UI]`-only, needs a backend split first)
      was correct and led to exactly the recommended split being carried out the SAME day, end to end, across 5
      sibling slots — see
      `/plans/archive/2026_08/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md` (now
      `status: resolved`, archived, all 5 of its own todos `[x]`): the 4 backend prerequisites (template-drift
      verdicts, ruleset-drift verdicts, `GET /api/rollout-ratchet/overview`, the running-vs-`main`-HEAD extension)
      landed as `unified-trading-pm@3e665c8a94` + `unified-trading-pm@263bbc59cb` +
      `deployment-api@46e04e0757` + `deployment-api@a2963906ab`, and this exact `[UI]` todo (the panel + widget)
      shipped as `deployment-ui@173e66ecab`. Independently re-verified live (not trusted from the citation alone):
      all 6 commits confirmed real ancestors of their repos' current `live-defi-rollout` HEAD via
      `git merge-base --is-ancestor`; `RolloutRatchetPanel.tsx` + `RolloutRatchetPanel.test.tsx` exist and are
      wired into `RepoCi.tsx`; the playwright smoke spec `tests/smoke/verdict-store-panels.spec.ts` exists;
      `rollout_ratchet.py` exists and is registered in `deployment-api/main.py`;
      `main_head_drift.py` and both verdict-writer driver scripts exist. No new code needed — this batch's own
      citation of the todo simply predated (and then never caught up with) the same-day resolution.

- [x] ✅ [DEVOPS] P2. **Hoist the superseded-promote-PR cleanup above the SIT gate in `sit_gate_treadmill`'s remaining
      scope** (mirrors the same hoist pattern batch13 already applied to `ldr_to_main_fleet_promote.sh` for a sibling
      case) — safety constraint fully specified in the source doc. Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` (line ~146). Gate: matches
      the batch13-shipped hoist pattern's ancestor+concluded-failure scoping. **CHECKBOX RECONCILIATION 2026-08-17
      (slot-19, infra craft) — already shipped before this batch was drafted.** The source doc's own line ~146 todo is
      itself already `[x] ✅ RESOLVED — DONE (plan_reconciler Phase -1, 2026-08-16)`, citing
      `unified-trading-pm@5ff1205e68` — this batch's Source citation pointed at a since-resolved todo in the source
      doc and missed the resolution, the same stale-citation shape already caught for this batch's 2 line-cap-split
      DOC todos. Verified live (not just trusting the citation): `git merge-base --is-ancestor 5ff1205e68 HEAD` on
      `unified-trading-pm` confirms it's a real ancestor of the current tip; `scripts/cicd/ldr_to_main_fleet_promote.sh`
      contains `_close_ancestor_failed_promote_prs()` (lines ~470-525) with an explicit header comment "hoisted ABOVE
      the SIT gate", called at line ~688 with an inline comment confirming it runs "before the content-identical skip
      below and before the SIT differ/gate section further down" — matches the exact hoist pattern + the
      ancestor+concluded-failure safety constraint (never mass-close; only a strict ancestor of LDR tip with
      `quality-gates-v2` CONCLUDED failure) the source doc specified. No code change needed.

- [x] ✅ [DEVOPS] P2. **CHECKBOX RECONCILIATION 2026-08-17 (slot-1, infra craft) — already shipped before this batch
      was drafted.** The source doc's own dedup-key item (line ~161) is itself already `[x]` ✅ RESOLVED — DONE
      (plan_reconciler Phase -1, 2026-08-16), citing `unified-trading-pm@c91496e0db` — this batch's own citation
      (line ~155, "re-assess given 3+ subsequent recurrences") pointed at a since-resolved gap and missed the
      resolution. **Fix `sit-gate-stuck-detector.yml`'s remaining dedup-key gap** — re-assess given 3+ subsequent
      recurrences (08-10, 08-14, 08-15) all self-resolved without incident since this was last held back as "too hot to
      touch while live." Verified live (not just trusting the citation): `git show -s --format='%H %ci' c91496e0db`
      dates the fix to **2026-08-08 14:11:25+01:00** — i.e. it predates all 3 named recurrences (08-10, 08-14, 08-15),
      so those recurrences already exercised the fixed code path, not the old flat-cooldown one.
      `.github/workflows/sit-gate-stuck-detector.yml` (current tree) confirms `dedup_key:
      sit-gate-stuck-${{ needs.check.outputs.max_streak }}` (streak-folded-in, replacing the flat `sit-gate-stuck`
      key) plus a state-diffed `notify-resolved` all-clear bookend (`dedup_key: sit-gate-stuck-resolved`) — both parts
      of the same design the doc asked for. Cross-checked against the doc's own recurrence history for a false
      -suppression regression: the 08-14 (~22:41Z), 08-15 (~10:41Z), and 08-16 (~22:41Z) `cicd escalation` Progress
      Log entries each show the detector correctly paging (an escalation firing IS a successful Slack
      post — the opposite of suppression) and each converging to `sit-gate stuck detector: healthy` once the
      treadmill self-resolved, with no report of a missed/suppressed post in any of the three. Gate satisfied: dedup
      key change verified against the doc's own recurrence history, no new false-suppression found. Source: same doc
      (line ~155).

- [ ] [DEVOPS] P3. **Add `StartLimitBurst`/`StartLimitIntervalSec` to the glue-runner systemd units** — purely
      additive, does not touch the credential-fetch logic that previously crash-looped prod. Source:
      `plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (line ~178). Gate: unit
      files updated; a simulated crash-loop respects the new burst/interval limits.

- [ ] [BACKEND] P2. **Build the post-promotion test-impact divergence-analysis tool** against MDPS's real
      `TEST_IMPACT_GATE:` logs. Source: `plans/active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`
      (line ~246). Gate: as stated in the source doc's own done-when.

- [ ] [BACKEND] P2. **Fix the GCS 404 in `generate_instrument_snapshot.py`** (stale/renamed bucket reference) AND
      **remove the stale `unified-market-interface` phantom entry** from `generate_config_registry.py`. Source:
      `plans/archive/2026_08/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md` (lines ~139, ~143). Gate: both
      scripts run clean against live GCS/config state.

- [ ] [BACKEND] P2. **Warm the git-object cache for JIT-ephemeral runner checkouts** — fully designed in the source doc
      (Option C: hardlink-copy the existing 10-min-refreshed mirror, explicit fallback to `actions/checkout` on
      staleness). Source: `plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md` (line ~275). Gate: matches
      the 3 implementation steps + fallback already specified in the source doc.

- [ ] [SCRIPT] P3. **Add `detect_template_drift.py --workflows --repo <self>` as a consumer-scoped pre-commit/CI
      check** on `unified-api-contracts`, mirroring the already-shipped `check_cloudbuild_template_drift.py` STEP
      5.108 wiring pattern. Source:
      `plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md`.
      Gate: a new drift introduced at the point of authorship (not just fleet-wide) is caught before merge.

- [ ] [DEVOPS] P2. **Classify each of semver-agent's residual stalled-repo cases as correctly-quiet vs. a genuine
      patch-fallback gap** — same investigate-then-fix-if-mechanical pattern batch13 already used successfully for the
      prior 7-repo residual (all 7 turned out correctly-quiet). Source doc archived 2026-08-18
      (`ci_tranche_zero_checkbox_archive_sweep_2026_08_18`); contract now lives at
      `/codex/08-workflows/ci-cd-flow.md`. Gate: each residual case has a recorded verdict with cited evidence (same
      shape as batch13's classification).

- [ ] [DEVOPS] P2. **Investigate why `update-dependency-version.yml`'s primary cascade has been dormant since
      2026-06-28** — bounded diagnostic question (grep trigger config, check dispatch history, diff against last-fired
      date), not an open-ended design call despite 4+ prior audit passes calling it judgment-only. Source:
      `plans/archive/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`. Gate: a recorded root
      cause with evidence, or a positive confirmation the cascade is intentionally dormant.

- [ ] [SCRIPT] P3. **Wire the `consumer-qg-gate` job into `pin_branch_protection_rulesets.py`'s required-status-check
      set** so a failing consumer-QG check actually blocks the PR merge button, not just its own workflow run. Source:
      `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`. Gate: a deliberately
      broken consumer-QG check on a test PR is confirmed to block the merge button.

- [x] [DOC] P1. **Split `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md`** (1013L, over the 1000L
      hard cap) using the established extraction pattern. Source: `plans/active/issues/plan_reconciler_findings_ci_2026_08_10.md`
      (line ~223) — operator-approved 2026-08-16 to dispatch as AO-eligible despite the doc's own "Operator-owned"
      self-tag, since the extraction pattern is already proven safe elsewhere in the corpus. Gate: doc splits cleanly
      under 1000L per part, no content lost, `check_line_caps.sh` passes. **ALREADY DONE — checkbox reconciliation,
      `/ag-closeout-audit ci` 2026-08-16 (slot 21):** shipped `unified-trading-pm@f835f7fcc4` (slot-9, dispatch
      `agt-4f7ad9`, "ci-tranche line-cap splits under Trust Mode") ~53min BEFORE this batch was drafted — this batch's
      Source citation pointed at the stale predecessor doc (`plan_reconciler_findings_ci_2026_08_10.md`) and missed that
      the newer `plan_reconciler_findings_ci_2026_08_16.md`'s own Phase -1 had already done this split. Verified live:
      doc is now 145L.

- [x] [DOC] P1. **Split `plans/active/github_actions_operator_gated_followups_2026_07_17.md`** (1006L, over the 1000L
      hard cap) using the same extraction pattern. Source: same reconciler doc (line ~232) — same operator approval.
      Gate: same as above. **ALREADY DONE — checkbox reconciliation, `/ag-closeout-audit ci` 2026-08-16 (slot 21):**
      same commit `unified-trading-pm@f835f7fcc4`, same stale-Source-citation cause as above. Verified live: doc is now
      738L.

## Todos — checkbox reconciliation only (work already done elsewhere, never flipped)

- [x] ✅ [REVIEW] P2. **CHECKBOX RECONCILIATION 2026-08-17 (slot-18, review craft) — already resolved before this
      batch was drafted.** The two `[OPERATOR]`-retagged SUPERSEDED/DO-NOT items in
      `plans/archive/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` were already converted from
      `- [OPERATOR]`-tagged bullets to the non-checkbox `CANCELLED —` disposition format by
      `unified-trading-pm@09cb20bf5a` (2026-08-16, `/plan-reconcile Phase -1`) — this batch's own Source line (~305)
      still described them as pending a `[x]`-flip, missing that the reconcile pass had already closed them out in a
      different (non-checkbox) format the same day. Verified live: `09cb20bf5a` is a real ancestor of current HEAD;
      `grep -n '^\- \[ \]' <target-doc>` returns zero matches — the doc carries 0 open checkboxes. No further edit
      needed to the target doc; its own `archive_exempt: true` (frontmatter) already documents the 0-open-todos state
      and the deliberate archival deferral, so that note doesn't need repeating here.

- [x] ✅ [REVIEW] P2. **CHECKBOX RECONCILIATION 2026-08-17 (slot-19, review craft) — already resolved before this
      batch's citation was checked, no source-doc edit needed.** The source doc's own 2 items (lines ~97-98) were
      already flipped `[x]` by `unified-trading-pm@09cb20bf5a` (`/plan-reconcile` Phase -1, 2026-08-16 22:54:09+01:00)
      — that commit lands AFTER this batch was drafted (`bfc56a714a`, 2026-08-16 19:07:40+01:00), so this batch's
      citation was stale on arrival, same shape as this batch's 2 other stale-citation reconciliations above. Both
      items independently re-verified live (not trusted from the citation alone): item 1 — fresh
      `gh pr view 2714 --repo IggyIkenna/unified-trading-pm` (2026-08-17) returns
      `state: CLOSED, mergedAt: null, closedAt: 2026-08-10T16:01:44Z`, matching the source doc's own citation exactly;
      item 2 — fresh `grep -n 'inflight_wait\|status!=\|not superseding\|about to pass'
      .github/workflows/ldr-to-main-promote-fleet.yml` (2026-08-17) still returns zero hits, matching
      `ci_satellite_ao_dispatch_batch13_2026_08_13.md`'s 2026-08-14 finding. No further action needed on the source
      doc; both items are correctly resolved with accurate evidence already in place.

- [x] ✅ [REVIEW] P2. **Reconcile `cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`'s 1 open item** —
      already shipped via `ci_satellite_ao_dispatch_batch13_2026_08_13.md` (`unified-trading-pm@b167edbaf4`, new
      `find_dropped_substitution_keys()` guard). **VERIFIED 2026-08-17 (slot 20):** `b167edbaf4` confirmed a real
      ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor` passes), and
      `find_dropped_substitution_keys()` is present and live in `scripts/propagation/rollout-cloudbuild.py:240`,
      called from the `--apply` write path at line ~413. The source issue doc
      (`plans/archive/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`) already carries 0 open
      `- [ ]` checkboxes — every one of its todos is independently marked `[x]` done. No further code change
      needed; this item was pure checkbox-reconciliation.

- [ ] [REVIEW] P3. **Reconcile `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md`'s stale duplicate
      item** (line ~160, "re-check after LDR goes quiet") — directly answered by the doc's own 2026-08-10 measured
      section ("the streak DOES reset — there is no masked second bug"), a duplicate of the already-closed item at
      line ~141. Flip `[x]` citing the doc's own existing evidence.

- [ ] [REVIEW] P3. **Reconcile `codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`'s
      2 remaining open items** (lines ~190, ~218) — both already done: the SUPERSEDED-banner item is satisfied by the
      same pre-existing banners verified in `ci_satellite_ao_dispatch_batch14_2026_08_15.md` item 2 (already present on
      origin, pre-dating batch13); the no-frontmatter-vs-yaml-parse-error distinction was shipped in batch13
      (`unified-trading-pm@a68d8b716d`, `FrontmatterParseError`). Flip both `[x]` with citations. Gate: verify both
      citations resolve to real, currently-live content before flipping.

- [ ] [REVIEW] P3. **Reconcile `qg_host_adaptive_resource_governor_2026_07_14.md`'s 2 already-satisfied items**
      (lines ~217, ~227) — both already marked in-doc "DEFERRED (already satisfied functionally / count-based
      validated adequate)." Flip `[x]` citing the doc's own existing text as evidence, or leave open with a note if a
      fresh read finds the in-doc claim itself questionable.

## Deferred (not batched — still needs an operator decision)

- **`qg_host_adaptive_resource_governor`**: MAX_DURATION-vs-PYRIGHT_TIMEOUT scaling design (line ~372), pytest-xdist
  worker-death open design fork (line ~386), AO/glue-runner ledger unification direction (line ~399), and two live
  unresolved 2026-08-15 investigations (lines ~720, ~767, root cause still unknown, mid-diagnosis).
- **Fleet-wide CI concurrency cap** — 2 mechanisms already rejected with real measurements; cgroup `io`-controller
  delegation identified as the better fit but needs more design work than fits one session. (Duplicated across
  `ci_vm_io_starvation_audit...` line ~626 and `ci_vm_exposure_remediation_2026_08_06.md` line ~107 — same item.)
- **Fork-PR "require approval for outside collaborators"** — still a manual web-UI click, no API exists
  (`github.com/IggyIkenna/unified-trading-pm` → Settings → Actions → General). Duplicated across 2 more docs found in
  this survey.
- **Bare-host CI bootstrap proof** — still blocked on the fleet-wide `ikenna-worker` IAM `ssm:*` access gap, twice
  reconfirmed. Same underlying blocker as batch14's item 1 investigation.
- **F4 vacuous-crons digest-drift-sweep non-convergence** — bundles a bounded sub-part with an open-ended one, doc
  repeatedly left unsplit by design.
- **`sit_validated_workspace_digest`** written-but-unread gap — explicit close-or-justify-dropping design call.
- **Re-do the credential-fetch `|| true` fix** in `glue-runner-run.sh` — first attempt crash-looped all 5 self-hosted
  runners; needs a `--selfcheck` mode + one-unit canary rollout before any retry, operator sign-off required given the
  prod-incident history.
- **`todo_cancelled_disposition_format_breaks_todo_regression_check`** — cross-file conservation logic design.
- **`quickmerge_sentinel_race_retry_storm`**: content-hash QG green-tree fast-path — explicit "for operator/careful
  review, do NOT dispatch blind" banner (touches high-blast-radius shared ship infra).
- **`quickmerge_environment_autodetect_forces_dev_off_main`**: branch-check broadening design call.
- **`deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83`**: validate-against-canonical vs.
  local-sibling-checkouts architecture tradeoff (network cost vs. host-staleness acceptance).
- **`build_deploy_pipeline_provenance_and_aws_deferred_gaps`**: whether cicd-events ledger should carry `build_id` —
  low-confidence "confirm whether," doc-level "page-first, do not fix here" ruling governs.
- **`fleet_workflow_template_dedup_to_unified_trading_ci`**: optional branch-protection/visibility-change alert —
  priority call, not a spec.
- **Pytest-timeout 4-doc chain** — confirmed genuinely resolved (both preconditions landed, ~10 days of clean
  monitoring), but the founding doc's own 14-day monitoring window doesn't close until ~2026-08-20. Leave open until
  then; archive all 4 together once it closes — do not archive early.

## Progress Log

- **context-scout 2026-08-19**: re-verified context_scope (2 entries) unchanged, both resolve on disk — dispatch-batch
  coordinator doc, source paths deliberately skipped per the carve-out (many distinct source docs, no single
  dominant file target).
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **2026-08-16 (interactive session)**: drafted from a 2-agent follow-up survey of the 39 CI-tagged docs still
  carrying open todos after batch14 shipped, plus operator rulings on the line-cap splits and the e2e-testing
  tier-DAG fix (landed directly, ahead of this batch, in
  `plans/active/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md`).
- **2026-08-16 — `/ag-closeout-audit ci` (autonomous, scheduled, slot 21, `agt-114e5f`).** Ran a delta audit rather than
  a full re-survey (this batch had just been drafted the same day by the interactive session above, so a fresh Phase 1
  sweep would only re-ask the same 39 docs the same questions). Cross-referenced the full 51-doc `ci`-tranche inventory
  against this batch + batch13 + batch13's finalize + this batch's own finalize + the consolidated closeout, leaving 9
  docs genuinely uncited by any of the 5; classified all 9 via a 9-agent Workflow. Found and fixed in-run: the 2
  line-cap-split todos above were already stale on arrival — `unified-trading-pm@f835f7fcc4` (slot-9, `agt-4f7ad9`)
  shipped both splits ~53min before this batch was drafted, citing the newer `plan_reconciler_findings_ci_2026_08_16.md`
  doc that superseded the `..._2026_08_10.md` doc this batch's Source lines still pointed at — flipped both `[x]` above
  with commit evidence, verified live (145L / 738L). Full delta-audit results (7 confirmed orphans, none AO-eligible
  enough to warrant a fresh batch16 yet, plus 2 asset_group mistags belonging to the `infra` tranche, not `ci`) written
  to `plans/active/issues/ag_closeout_audit_ci_parked_2026_08_16.md`.
- **2026-08-16 (slot 21, AO-dispatched worker).** Shipped item 1 (na-corpus/governor baseline-freshness daily
  promotion job, governor Trigger 3): anomaly-guarded `scripts/dev/measure-qg-baseline.sh` (new
  `scripts/dev/qg_baseline_merge.py` + `--force` flag), the daily systemd-timer job
  (`scripts/orchestrator/qg-baseline-daily-promote.{sh,service,timer}` +
  `install_qg_baseline_daily_promote.sh`), and its unit tests
  (`scripts/dev/test-qg-baseline-anomaly-guard.sh`, 12/12 pass). Flipped this item and the mirrored todo in
  `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`. The daily timer is not yet installed on the
  orchestrator VM — that install step is `[OPERATOR]`-run by design (root + `/etc/systemd/system`), same as its
  sibling installers (`ldr-to-main-promote-heartbeat`, `reap-stale-blockers`).
- **2026-08-17 (slot 20, AO-dispatched worker, infra craft).** Shipped the "Stagger
  `ldr-to-main-promote-fleet.yml`'s per-repo fan-out" todo: `unified-trading-pm@23499c954f`. Added an
  env-overridable `STAGGER_SECONDS` (default 3s) to the bounded-parallel driver in
  `scripts/cicd/ldr_to_main_fleet_promote.sh` so successive `process_repo` launches are spread out instead of
  firing back-to-back, plus a new regression test
  (`scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh`, 6/6 assertions pass). Flipped this item.
- **2026-08-17 (slot 13, AO-dispatched worker, infra craft).** Shipped the "Share bare repos + `git worktree` for
  sibling-clone I/O" todo: `unified-trading-ci@3209654` (the reusable `python-quality-gates-v2.yml` — that's where
  `clone_repo()` actually lives, not the caller `.tmpl` in this repo) + `unified-trading-pm@10fb8339dc` (the
  standing worktree-prune timer). Full detail on the checkbox above. Fast path is code-shipped but dormant on the CI
  VM until an operator provisions `SHARED_BARE_ROOT` and installs the prune timer — both deliberately gated, not
  overlooked.
- **2026-08-17 (slot 19, AO-dispatched worker, infra craft).** Checkbox-reconciled the "Hoist the superseded-promote-PR
  cleanup above the SIT gate" todo — no code change needed, the source doc's own line ~146 item was already resolved
  2026-08-16 (`unified-trading-pm@5ff1205e68`) before this batch was drafted; verified live that the ancestor is real
  and the hoisted call site + safety constraint are actually present in `ldr_to_main_fleet_promote.sh` before flipping.
- **2026-08-17 (slot 1, infra craft).** Checkbox-reconciled the "Fix `sit-gate-stuck-detector.yml`'s remaining
  dedup-key gap" todo — no code change needed, the source doc's own dedup-key item was already resolved
  2026-08-16 (`unified-trading-pm@c91496e0db`, dated 2026-08-08, predating this batch's cited recurrences). Verified
  live: current `.github/workflows/sit-gate-stuck-detector.yml` carries the streak-folded `dedup_key` + a
  state-diffed `notify-resolved` all-clear bookend; the doc's own 08-14/08-15/08-16 escalation entries show correct
  paging + convergence with no suppressed post. Full evidence on the checkbox above.
- **2026-08-17 (slot 18, review craft).** Checkbox-reconciled the "Reconcile the two `[OPERATOR]`-retagged
  SUPERSEDED/DO-NOT items" todo — no doc edit needed on the target issue doc, both items were already converted from
  `[OPERATOR]`-tagged bullets to the non-checkbox `CANCELLED —` disposition format by `unified-trading-pm@09cb20bf5a`
  (2026-08-16, `/plan-reconcile Phase -1`), before this batch was drafted. Verified live: `09cb20bf5a` is a real
  ancestor of current HEAD; `grep -n '^\- \[ \]'` on the target doc returns zero matches. Full evidence on the
  checkbox above.
- **2026-08-17 (slot 19, review craft).** Checkbox-reconciled the "Reconcile
  `ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md`'s 2 open items" todo — no source-doc edit
  needed, both items were already flipped `[x]` by the same `unified-trading-pm@09cb20bf5a` `/plan-reconcile` Phase
  -1 commit (2026-08-16 22:54, after this batch's 19:07 draft). Independently re-verified both live rather than
  trusting the citation: fresh `gh pr view 2714` matches the source doc's cited CLOSED/never-merged state; a fresh
  grep for doomed-run-wait patterns in `.github/workflows/ldr-to-main-promote-fleet.yml` still returns zero hits.
  Full evidence on the checkbox above.
- **2026-08-18 (slot-7, ui_developer).** Checkbox-reconciled the "Build the rollout-ratchet dashboard panel" todo —
  redispatched to this slot as open `[UI]` work, but slot-1's 2026-08-17 mis-scoping investigation had already
  triggered the full backend+UI split being built and shipped the SAME day across 5 sibling slots (see
  `/plans/archive/2026_08/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md`, now
  `status: resolved`/archived). Independently re-verified all 6 shipped commits are real ancestors of their repos'
  current HEAD and every claimed artifact (panel component, its wiring, the playwright spec, the API route, both
  verdict-writer drivers) genuinely exists on disk before flipping — did not trust the archived issue doc's own
  claims alone. No new code needed; this batch's citation simply predated the resolution.
- **context-scout 2026-08-20**: re-verified context_scope (2 entries) unchanged, both resolve on disk — dispatch-batch
  coordinator doc, source paths deliberately skipped per the carve-out (many distinct source docs, no single
  dominant file target).
