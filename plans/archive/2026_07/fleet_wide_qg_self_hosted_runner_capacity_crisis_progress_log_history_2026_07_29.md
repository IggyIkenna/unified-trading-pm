---
doc_type: issue
title: Fleet-wide QG self-hosted-runner capacity crisis — Progress Log history (2026-07-28 corroboration wave)
summary:
  Line-cap remediation extraction from
  plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md's Progress Log — every per-repo
  corroboration + fix entry from 2026-07-28 (batch-live-reconciliation-service, alerting-service,
  market-data-processing-service, agent-orchestrator, trading-agent-service, instruments-service, execution-service,
  deployment-api, and others), moved verbatim so the live doc stays under the 1000-line hard cap. Fully superseded by
  the live doc's Evidence/Follow-up sections; read this only if a deeper citation on a specific repo's corroboration
  entry is needed.
status: archived
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, incident, history, line-cap-remediation]
related: [/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md]
created: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-07-29
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source:
  [plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md, line-cap remediation 2026-07-29]
assigned_role: project_management
drift_direction: none
---

# Fleet-wide QG self-hosted-runner capacity crisis — Progress Log history

> Extracted verbatim 2026-07-29 (line-cap remediation, doc was at 1015/1000 lines) from
> `/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s Progress Log. This covers
> every 2026-07-28 corroboration/fix entry through the last one (`instruments-service`#1007, ~23:26 UTC). The live doc's
> Progress Log continues from any entry logged after this extraction.

## Progress Log

- 2026-07-28 (cicd agent, slot-4, escalation `agt-70dbed`, `ldr_qg_failure` on `batch-live-reconciliation-service`#255
  LDR→main promotion PR): **2nd corroboration + per-repo fix**, same pattern as execution-service. Failing run
  `30305786014` ran **51m18s** (vs normal 8-15min): `QG slice (checks)` typecheck hit a hard `timeout` (exit=124) after
  being admitted, then `lint-codex` got `Terminated`; `QG slice (tests)` queued behind `[qg-governor] all 4 tokens busy`
  for 6+ minutes and never started before also being `Terminated`. Confirmed NOT a code regression: a clean local
  `quality-gates.sh` run at the same HEAD (`806fba72`) passed in 58s. This repo's flip landed via `1c2b5ba` ("Phase 7 +
  quality-gates-v2 self-host rollout for batch-live-reconciliation-service"), same ~21:40-21:55 UTC 2026-07-27 window as
  the other 18. Applied the same fix as execution-service: reverted `self_hosted_runner_labels` to empty (→
  `ubuntu-latest`) via hand-edit (documented per-repo override field, not templated-identical content) +
  `quickmerge --agent` — `batch-live-reconciliation-service@2f591901160e2edbadf250f11a2256c25f2540c7`. Did not touch the
  shared allowlist file, any other repo, or the VM — same scope boundary as the execution-service fix. This repo is also
  independently named in `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`'s P2 todo
  (its SIT `cross-repo-invariants` dispatch blew a 90s poll budget same window) — one shared root cause (oversubscribed
  `i-0c9b283b31d6b5ca7`) manifesting across multiple symptoms for this repo.

- 2026-07-28 (cicd agent, slot-2, escalation `agt-b195a8`, `ldr_qg_failure` on `alerting-service`, no PR): **3rd
  corroboration + per-repo fix**, same pattern. This repo is one of the two named directly in
  `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`'s live diagnosis ("long-running
  pytest processes for `alerting-service` and `fund-administration-service` (~2h wall-clock)"). Failing run
  `30306788671` (at `d6dfb30f`, the repo's own Phase-7 rollout commit) ran **2h44m27s** before failing —
  `QG slice (tests)` sat on step "Run quality gates (leg tests)" for 64+ min with no completion recorded, consistent
  with the job being killed mid-hang rather than failing on its merits. A same-config auto-retry (`30310510143`) then
  queued/ran for **2h22m47s** and actually went GREEN (self-recovered once shared-VM iowait eased from the documented
  66-93% peak down to ~24% by the time I checked — confirmed live on `i-172-31-5-118` itself: `uptime`/`top` showed load
  avg ~21, iowait 24.3%, plus the actual `alerting-service` `quality-gates.sh` PID visible mid-run in the process
  table). Since the wall had already self-resolved by the time I started, I canceled the redundant still-queued 3rd
  retry (`30317509169`) to free the sole shared runner, then applied the same precedented fix regardless (the underlying
  capacity issue is still open per this doc's own P2/VERIFY findings, so leaving the flip in place would just hang the
  next commit): reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern +
  `quickmerge --agent` — `alerting-service@0fc5cab` (local `quality-gates.sh` passed in 57s). Verified live: triggered a
  fresh run (`30318470827`) post-fix, confirmed via `gh api .../jobs/<id>` it ran on `labels: ["ubuntu-latest"]` (not
  self-hosted), and it completed **green in 2m33s total** (`QG slice (tests)` 1m40s) — back to normal, no contention.
  Did not touch the shared allowlist file, any other repo, or the VM — same scope boundary as the prior two fixes. No
  open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-3, escalation `agt-5b9083`, `ldr_qg_failure` on `client-reporting-api`, no PR): **4th
  corroboration + per-repo fix**, same pattern, detected by `ldr-ci-monitor` at commit `ab32fba4` (the repo's own "Phase
  7 + quality-gates-v2 self-host rollout for client-reporting-api" commit). Failing run `30306795757` ran **2h54m8s**:
  `QG slice (checks)`'s "Run quality gates (leg checks)" step sat `in_progress` from 22:33:34 to 23:29:06 (55m32s)
  before being marked `cancelled` — not a genuine assertion failure. Two further `workflow_dispatch` retries had already
  auto-queued behind it on the sole shared runner before I picked up the escalation: `30310512581` (its
  `QG slice (tests)` alone took 25m3s; `checks` was still `in_progress` when I checked) and `30317512237` (still
  `pending`, never got a runner). Confirmed NOT a code regression: a clean local `quality-gates.sh` run at HEAD
  (`0881465`) passed in 69s. Canceled both stuck/queued retries to free the sole runner, then applied the same
  precedented fix: reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern +
  `quickmerge --agent` — `client-reporting-api@4a4ba6e`. Verified live: triggered a fresh run (`30319083342`) post-fix,
  confirmed via `gh api .../jobs` both `QG slice (checks)` and `QG slice (tests)` ran on `labels: ["ubuntu-latest"]`
  (not self-hosted), and it completed **green in ~2m total** (`checks` 1m40s, `tests` 1m56s) — back to normal, no
  contention. Did not touch the shared allowlist file, any other repo, or the VM — same scope boundary as the prior
  three fixes. No open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-8, escalation `agt-71f135`, `ldr_qg_failure` on `e2e-testing`, no PR): **5th
  corroboration + per-repo fix**, same pattern, detected by `ldr-ci-monitor` at commit `12846a43` (the repo's own "Phase
  7 + quality-gates-v2 self-host rollout for e2e-testing" commit). The escalating run `30306809955` failed on the
  classic signature (`git status` subprocess `TimeoutExpired` (40s) mid-build of the `unified-api-contracts` editable
  dep). A later retry (`30314443597`, after the reusable workflow's independent
  `SETUPTOOLS_SCM_SUBPROCESS_TIMEOUT`/`VCS_VERSIONING_SUBPROCESS_TIMEOUT=180` mitigation had already landed) got past
  the timeout but still queued **712s** on `[qg-governor] all 4 tokens busy` before failing on an unrelated genuine STEP
  5.105 GCS-CLI-baseline break that a separate commit (`420e834`) fixed independently — confirms the runner-capacity
  symptom and a real code issue can coexist in the same window without one masking the other. This repo's own runner
  pool showed only 1 registered runner (`glue-ip-172-31-5-118-1`), and a subsequent `workflow_dispatch` run
  (`30317519815`) sat `pending` 16+min with zero jobs materialized while that sole runner was busy elsewhere — canceled
  to free it. Applied the same precedented fix: reverted `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via
  the same hand-edit pattern + `quickmerge --agent` — `e2e-testing@a881a43`. (Mid-fix, this worker's own session was
  reaped by the WorkerLivenessWatchdog for going heartbeat-silent >15min while babysitting the quickmerge subprocess via
  repeated `ScheduleWakeup` calls instead of the AO `/api/slots/N/progress` endpoint — worth flagging as a recurring
  trap for any one-shot agent backgrounding a long-running shell command: `ScheduleWakeup` paces the _skill loop_, it
  does not itself satisfy the liveness watchdog. The backend's dead-session recovery correctly preserved the
  committed-but-unpushed fix on `origin/wip-preserve/orchestrator-slot-8-5e97b9e` rather than losing it; recovered by
  cherry-picking the real fix commit — skipping an unrelated auto-committed cache-artifact commit stacked on top — back
  onto a fresh `live-defi-rollout` and re-shipping with a self-heartbeating wrapper script.) Verified live: triggered a
  fresh run (`30326015026`) post-fix, confirmed via `gh api .../jobs` every job ran on `labels: ["ubuntu-latest"]` (not
  self-hosted), and it completed **green in ~3m02s** (`checks` 1m54s, `tests` 2m24s) — back to normal, no contention;
  GH's own "QG Recovered" Slack step fired automatically. Did not touch the shared allowlist file, any other repo, or
  the VM — same scope boundary as the prior four fixes. No open repo-blockers existed for this repo at the time.

- 2026-07-28 (cicd agent, slot-2, escalation `agt-f11cae`, `ldr_qg_failure` on `unified-trading-library`, originally
  filed against promotion PR #674): **6th corroboration + per-repo fix**, same pattern. This repo's own Phase-7 rollout
  commit `5f48d47f` ("feat(ci): Phase 7 + quality-gates-v2 self-host rollout for unified-trading-library") landed in the
  same ~21:40-21:55 UTC 2026-07-27 window as the other 18. PR #674 (pinned to `5f48d47f`) failed `QG slice (tests)` with
  3 genuine `pytest-timeout` failures on otherwise-fast tests
  (`test_utc_aligned_scheduler.py::test_first_callback_fires_at_aligned_boundary_plus_grace` >60s,
  `test_streaming_writer.py::TestDynamicFlush::test_flush_triggered_by_memory_pressure` >60s,
  `synthetic/test_synthetic_harness.py::test_harness_auto_resolves_params_from_specs` >300s; 6801 passed, 3 failed) —
  consistent with CPU contention rather than a code regression. #674 was auto-superseded by #675 (pinned to a later LDR
  commit `080a84a0`, an unrelated consolidator fix already landed) before I could act on it; #675's own `pull_request`
  quality-gates-v2 run (`30318034158`) hit the identical `QG slice (tests)` timeout failure at the SAME LDR head,
  confirming the flakiness was runner-capacity, not the intervening commit. Runner check
  (`gh api repos/IggyIkenna/unified-trading-library/actions/runners`) showed exactly 1 registered runner
  (`glue-ip-172-31-5-118-1`), same shared-VM signature as the other 5. Applied the same precedented fix: reverted
  `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` —
  `unified-trading-library@7677ff71`. Verified live: triggered a fresh run (`30326782451`) post-fix; both
  `QG slice (tests)` and `QG slice (checks)` completed green, aggregate `quality-gates-v2` succeeded in ~6m38s total —
  back to normal, no contention. Did not touch the shared allowlist file, any other repo, or the VM — same scope
  boundary as the prior five fixes. No open repo-blockers existed for this repo at the time (`GET /api/repo-blockers` →
  `{"open":[]}`).

- 2026-07-28 (cicd agent, slot-2, escalation `agt-2942ad`, `ldr_qg_failure` on `ml-service`, no PR): **7th corroboration
  - per-repo fix, plus an unrelated second issue it unmasked.** Detected at `ml-service`'s own Phase-7 rollout window
    (`e6002499`, "feat(ci): Phase 7 + quality-gates-v2 self-host rollout for ml-service"); the flagged failing run
    (`30310600633`) died in `QG slice (checks)` at the `Set up Python` step (9 min then failed) — same signature class
    as the prior six (self-hosted-runner contention), confirmed via `gh api .../runners` showing the same shared
    `glue-ip-172-31-5-118-1` single-runner registration. A same-config retry (`30311878707`) had already self-recovered
    green by the time I picked this up — no open repo-blocker existed. Applied the same precedented fix regardless (the
    underlying capacity issue is still open, so leaving the flip in place would just hang the next commit): reverted
    `self_hosted_runner_labels` to empty (→ `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` —
    `ml-service@08a2514`. **Verifying this fix surfaced a SECOND, unrelated, genuinely-live break**: the first post-fix
    run (`30327865658`) confirmed `Set up Python` now succeeds on `ubuntu-latest`, but `QG slice (tests)` then failed
    for real — `ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'` (raised inside
    `opentelemetry-instrumentation-fastapi==0.63b0`, which needs a fastapi symbol only present >=0.137). Root cause:
    `unified-trading-library@3b99d19d` had bumped its own fastapi/starlette floor to `>=0.137.0`/`>=1.3.1`,
    contradicting `canonical-dependency-manifest.json` (still `<0.137.0`) — a genuine cross-repo SSOT contradiction,
    already tracked P0 in `/plans/archive/issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md` (filed
    by slot-3). The self-hosted runner's PERSISTENT cached venv had been masking this fleet-wide for ml-service
    specifically — a completely fresh `ubuntu-latest` runner's `uv sync --frozen` was the first thing to actually
    exercise the stale lock against UTL's new floor. While I was locally verifying my own lock-refresh fix for this, a
    different `cicd` worker (slot-7, escalation `agt-db0abf`) independently hit the same wall on ml-service's promotion
    PR and shipped the fuller fix first (`ml-service@8914d555`: `pyproject.toml` fastapi ceiling raised to match UTL's
    floor + `uv lock` regenerated to fastapi 0.140.7, full `quality-gates.sh --no-fix` verified green locally, 2111
    passed). My own narrower lock-only fix hit a real git conflict against their already-pushed commit during
    quickmerge's autostash rebase (git's own conflict markers landed IN `uv.lock` — caught before commit, not shipped);
    resolved by discarding my superseded diff and keeping theirs. Triggered a final fresh run (`30328459417`) at the
    combined HEAD (my `08a2514` + their `8914d555`) to close the loop: **fully green** — `QG slice (tests)` 3m19s,
    `QG slice (checks)` 1m49s, both confirmed on `labels: ["ubuntu-latest"]`, aggregate `quality-gates-v2` succeeded,
    GH's own "QG Recovered" Slack step fired. **Worth flagging for whoever works the fastapi-SSOT doc's `[OPERATOR]`
    todo**: this self-hosted → ubuntu-latest migration is itself an active _discovery mechanism_ for the UTL-floor drift
    — every OTHER repo still in `scripts/workflow-templates/self-hosted-qg-repos.txt` with a persistent self-hosted venv
    may be silently masking the same `iter_route_contexts` break until its own runner-capacity fix (or any other trigger
    for a clean `.venv` rebuild) exposes it, same as happened here. Did not touch the shared allowlist file, any other
    repo, or the VM — same scope boundary as the prior six fixes.

- 2026-07-28 (cicd agent, slot-8, escalation `agt-b03e9f`, `ldr_qg_failure` on `deployment-api`, promotion PR #413 LDR
  to main): **8th corroboration + per-repo fix, plus a new secondary symptom.** Failing run `30330086289` (PR #413, head
  `promote/deployment-api/2c1d446f5090`) showed the same signature: `QG slice (checks)` `TYPE CHECK` step hit a hard
  `timeout` (Type check FAILED/timeout, exit=124) after `basedpyright` initialized fine, not a genuine type error.
  Confirmed the repo's own Phase-7 rollout commit `c19edcc` ("feat(ci): Phase 7 + quality-gates-v2 self-host rollout for
  deployment-api") and exactly 1 registered runner (`glue-ip-172-31-5-118-1`, `online`, shared with the rest of the
  fleet) via `gh api .../actions/runners`. Applied the same precedented fix: reverted `self_hosted_runner_labels` to
  `""` (to `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` - `deployment-api@3df07f9`; local
  `quality-gates.sh` passed in 129s. Verified live: since PR #413's own head is an IMMUTABLE per-SHA promote ref frozen
  at the pre-fix commit (so re-running on that exact head could never pick up the fix), triggered a direct
  `gh workflow run quality-gates-v2.yml --ref live-defi-rollout` instead - run `30332079351` completed fully green
  (`QG slice (tests)` 5m14s, `QG slice (checks)` 2m24s, all jobs confirmed on `labels: ["ubuntu-latest"]`), GH's own "QG
  Recovered" Slack step fired. **Corroborates a second, concurrently-filed bug**: PR #413 itself never got superseded by
  a fresh promote ref/PR carrying the fix. Manually dispatched `ldr-to-main-promote-fleet.yml`
  (`only_repo=deployment-api`) twice (runs `30331728195`, `30331954123`) expecting a new
  `promote/deployment-api/3df07f9...` ref per STEP 1's frozen-head design - both runs completed `success` at the job
  level, both logged `TIER A PASS`/`CONTENT GATE PASS`/`SIT GATE PASS`/`LABEL-CHECK PASS` for `deployment-api` then went
  silent (no `frozen-head:`/`PR:`/`WARN` line, no new ref created, repo counted in NEITHER `Promoted`/`Blocked`/
  `Conflicted`) - the exact same symptom independently found by slot-11 on `deployment-service`#576 in the same window;
  see `/plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md` for the
  full analysis + the `[OPERATOR]`/`[SCRIPT]` follow-up todos (not duplicating here). Applied their precedented
  workaround: closed the stale PR #413 by hand (`gh pr close 413`, comment references that doc) so the next tick's
  `gh pr create` (which only fires when no existing open PR is found) has a clear path - did not touch the ref, the
  allowlist file, any other repo, or the VM.

- 2026-07-28 (cicd agent, slot-4, escalation `agt-a7fb1c`, `main_ci_red` on `market-data-processing-service`, no PR —
  post-promotion `push:[main]` failure, not a promotion-PR wall): **9th corroboration + per-repo fix.** Failing run
  `30336297316` (main HEAD `8a6947a`, a `chore(promote): LDR → main` merge) showed a variant signature of the same
  class: `QG slice (tests)` progressed normally to 88% (`pytest-xdist`, dot-progress) then hit an `INTERNALERROR` — a
  worker crashed inside `pytest_runtest_logfinish` while flushing its execnet channel, root-caused to
  `pytest_timeout.py`'s SIGALRM handler firing (`Failed: Timeout (>60.0s) from pytest-timeout`) mid-flush — an
  otherwise-fast test starved past its 60s budget by CPU/IO contention, not a genuine hang or code regression (the LDR
  commit this promoted, `034c1df`, is a real fix already verified green on `live-defi-rollout` before promotion).
  Confirmed the repo's own Phase-7 rollout commit `446a9d4` ("feat(ci): Phase 7 + quality-gates-v2 self-host rollout for
  market-data-processing-service", landed 2026-07-27 22:20 UTC — same wave as the other 8) and exactly 1 registered
  runner (`glue-ip-172-31-5-118-1`, `online`, `busy`, shared with the rest of the fleet) via
  `gh api .../actions/runners`. No open repo-blocker existed for this repo. Applied the same precedented fix: reverted
  `self_hosted_runner_labels` to `""` (to `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` —
  `market-data-processing-service@17ab96a2`; local `quality-gates.sh` (run inside quickmerge) passed in 68s. Verified
  live: triggered a fresh run (`30337347465`) on `live-defi-rollout`, confirmed via `gh api .../jobs` every job ran on
  `labels: ["ubuntu-latest"]` (not self-hosted), and it completed fully green (`quality-gates-v2` conclusion=success).
  Did not touch the shared allowlist file, any other repo, or the VM — same scope boundary as the prior eight fixes.
  Distinct from all 8 prior entries in one respect: this wall surfaced on the **post-merge `push:[main]`** trigger
  (dispatched by `escalation.py` as `wall_type=main_ci_red`, a repo-health-watcher classification, not the standard
  `ldr_qg_failure` promotion-PR path) rather than a promotion PR itself — worth noting for whoever eventually resolves
  this doc's `[SCRIPT]` P0 allowlist-cleanup todo, since a fix landed on `live-defi-rollout` only reaches `main` on the
  next LDR→main promotion cycle (the failing `main` push itself cannot be re-run against the fix).

- 2026-07-28 (cicd agent, slot-3, escalation `agt-b57f74`, `main_ci_red` on `market-data-processing-service`, no PR —
  follow-up wall on the SAME `main` red state slot-4 diagnosed above): **propagation-gap close, not a new root cause.**
  Confirmed slot-4's fix (`market-data-processing-service@17ab96a2`, `self_hosted_runner_labels` reverted to `""`) was
  already live-green on `live-defi-rollout` (jobs on `labels: ["ubuntu-latest"]`, run `30337347465` success) — nothing
  to re-fix there. The open problem was purely propagation: `main` HEAD (`8a6947a`, the promote-PR-#528 merge that
  predates the fix) stayed red because the automated `ldr-to-main-promote-fleet.yml` (`*/15` schedule) was not advancing
  `market-data-processing-service` — two consecutive ticks (`30339657932` at 07:46, `30340884923` at 08:04) show the
  SAME symptom already tracked in
  `/plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md`: the 07:46
  tick printed an explicit `GATE BLOCK ... ci_status=FAILING (cached='FAILING', live='FEATURE_GREEN')` (the
  hourly-consolidator manifest cache lagging the real green LDR), and the 08:04 tick — by which point the PM-main
  manifest's cached `ci_status` had already caught up to `SIT_VALIDATED` — produced **no** `TIER A PASS` / `GATE BLOCK`
  / `SIT GATE BLOCK` line for the repo at all (silently absent from `Promoted`/`Blocked`/`Conflicted`, same signature as
  the deployment-service case in the linked doc, third corroboration of that automation gap). **Third-party evidence
  this self-resolves on a fresh dispatch, not a permanent stuck state**: manually re-firing
  `gh workflow run ldr-to-main-promote-fleet.yml --ref main -f only_repo=market-data-processing-service` (run
  `30341624830`) worked cleanly on the very next attempt — `TIER A PASS`, `CONTENT GATE PASS`, `sit-gate/fleet-green`
  posted, `SIT GATE PASS` (non-breaking delta), opened PR #529 (`promote/market-data-processing-service/17ab96a22b32` →
  `main`) with auto-merge armed, PR's own `quality-gates-v2` went green in ~a few minutes (now on `ubuntu-latest`,
  confirming the fix rides along), and it auto-merged at 08:16:23Z. Verified `main` tree SHA == `live-defi-rollout` tree
  SHA post-merge (`7e5aa192...`, fully caught up, not just the one file) and the post-merge `push:[main]`
  `quality-gates-v2` run (`30341718322`) completed green. Separately, the ORIGINAL failing run `30336297316` was also
  observed to have been re-run and turned green on its own (`conclusion=success`, `updatedAt` 08:12:41Z) sometime
  between my two checks — unclear which actor re-ran it; noting in case it double-counts as a second, independent
  self-heal signal for the promote-fleet automation gap rather than something I triggered. Did not touch the shared
  allowlist file, `self-hosted-qg-repos.txt`, any other repo, or the VM. No open repo-blocker existed for this repo
  (`GET /api/repo-blockers` → `{"open": []}`). **Net effect on the linked automation-gap doc's open `[OPERATOR]` P2
  todo**: this is a THIRD observed instance of the silent-skip symptom (after deployment-api and deployment-service),
  and a third instance of it resolving cleanly on a manual re-dispatch with no code change — weak evidence toward
  "eventual-consistency/timing artifact" over "hard bug in `process_repo`", but not conclusive (three manual
  interventions, zero confirmed unassisted self-heals within a few ticks as that todo asks for).

- 2026-07-28 (`/autonomous`, responding to an operator Slack-alert dump covering 2:06-8:13 AM BST — sit-unlock
  double-FAIL, ldr-ci-monitor RED/GREEN flapping across ~10 repos, repeated `python-quality-gates-v2` slice
  FAILED/RECOVERED pairs, `ci-status-update` CI REGRESSIONs on main, branch-health promotion-lag warnings): **traced the
  entire storm to this one already-open doc** rather than treating each alert as a separate problem. Live cross-check
  against the 9 corroborations above confirmed: `sit-unlock`'s two FAILEDs (01:04/01:32 UTC) were the designed self-heal
  mechanism firing as intended (`staging_status.locked` gates a `breaking_pending` block, not the git `staging` branch —
  SIT went green again at 04:14 UTC and stayed green every check since); the QG FAILED→RECOVERED flapping and
  `ci-status-update` regressions are the direct, expected symptom of this doc's own root cause playing out repo-by-repo
  overnight. Found and fixed two things this doc's own todos hadn't closed yet: **(1)** found a 10th,
  previously-uncorroborated instance on `deployment-service` (self-hosted revert commit `ed2691f` at 05:21 UTC,
  `agt-7ea8ad`, PR #576 pytest-timeout on two pure file-I/O tests) that had never been logged here. **(2)**
  `deployment-service`'s LDR→main pipeline was independently and additionally stuck on a REAL, separate bug
  (`quickmerge-provenance`: commit `9d0ee9e` — a genuine direct-pushed code change to `escalation.py`, mid-history, not
  a carve-out) — root-caused via `check_strict_quickmerge.py --range <marker>..origin/live-defi-rollout --block`, fixed
  via the documented `scripts/cicd/reprovenance_bypass.sh 9d0ee9e148a1441794b9c6e6d49ef5c79af56a21 --push` remedy, then
  manually re-dispatched `ldr-to-main-promote-fleet.yml --only_repo=deployment-service` — PR #580 merged clean at
  08:05:47 UTC (this is unrelated to the self-hosted-runner root cause but was blocking the same repo's pipeline and is
  documented here rather than a new doc since it surfaced mid-investigation of this one). Applied this doc's own
  precedented fix to the remaining exposed repos: features-service, fund-administration-service, greeks-service,
  ibkr-gateway-infra (all 4 clean `quality-gates.sh --no-fix` first try), instruments-service (clean),
  market-tick-data-service (clean) — 6 repos, verified live post-fix on `ubuntu-latest` via `gh api .../actions/runs`.
  Attempted strategy-service and system-integration-tests via sub-agents; both found the same one-line fix but hit an
  UNRELATED blocker in a **different, stale, non-`.tabs/1` sibling clone** (`unified-api-contracts` 3 weeks stale,
  missing `CanonicalViolationClass`) neither agent had the scope to fix — both correctly left the edit uncommitted
  rather than force a red-tree commit; **flagging for whoever next touches that stray clone** (path:
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/{strategy-service,system-integration-tests}`, no `.tabs/1` — a
  workspace layout question outside this doc's scope, not investigated further). Shipped the [SCRIPT] P0 allowlist trim
  (`unified-trading-pm`, down to the 2 verified pools) as the systemic fix this doc's own todos called for. **Operator
  intervened live mid-session** ("you can't just take everything off the self-hosted box, it's freed up a lot now in
  terms of resource, put it back") — this is a REAL operator-present correction, not an autonomous-mode decision, and
  takes precedence: per the operator's explicit scoping choice (asked via structured options, chose "just what I touched
  today"), reverted the 6 just-fixed repos back to self-hosted (clean QG + quickmerge each, same pattern in reverse) and
  restored the allowlist to include them + the 5 untouched-and-still-self-hosted repos, while leaving the ~10 repos
  other agents settled on `ubuntu-latest` overnight alone. See the "Recommended fix path" checkboxes above for the final
  decision record. **Final state**: 12 caller repos self-hosted (agent-orchestrator + 11 others, all sharing the same
  box at whatever load it's currently carrying, per the operator's live call, NOT a capacity-planned allocation) +
  `unified-trading-pm` itself; ~10 repos on `ubuntu-latest` (settled, not touched); 2 repos (strategy-service,
  system-integration-tests) untouched throughout (their revert never shipped). This doc's underlying capacity-planning
  question ((b)'s "real per-repo pool sizing") remains genuinely open if the box gets hot again — the operator's call
  was a live-conditions judgment, not a permanent capacity plan, and this doc should be the first place a future
  flare-up gets logged rather than starting a new whack-a-mole cycle.

- 2026-07-28, same session, ~1h later: **the "flare-up" predicted above happened almost immediately** — operator asked
  to bring ALL repos onto the box, "just managed properly," which prompted actually closing the open capacity-planning
  gap instead of another whack-a-mole round. **Two live findings first, both confirmed with real evidence, not
  assumed**: (1) **renewed contention right after the 6-repo restore**: `instruments-service` hit the identical
  `pytest-timeout`→`INTERNALERROR`→`"Unexpectedly no active workers available"` crash at 12:20-12:28 UTC (same signature
  as every prior corroboration), and `unified-api-contracts` (never touched, always self-hosted) sat 16 minutes with
  `runner_name: ""` — queued, unassigned — before its own QG got cancelled at 11:33-11:49 UTC. A live SSM pull off
  `i-0c9b283b31d6b5ca7` at 12:35 UTC showed `load average 22.36, 21.34, 23.02` on 16 vCPU, 4GB already swapped, only
  2.4GB genuinely free, 34 `Runner.Listener` processes, **and ~13 concurrent `claude` agent-orchestrator slot-worker
  sessions co-resident on the SAME box** (this box is not a dedicated CI runner host — it's the AO orchestrator VM
  itself, self-hosted runners were installed alongside it). (2) **the box's RAM was halved TODAY, mid-incident, by a
  DIFFERENT session**: CloudTrail shows `i-0c9b283b31d6b5ca7` went `m8i.4xlarge` (16 vCPU/64GB) → `c7i.4xlarge` (16
  vCPU/**32GB**) via Stop→Modify→Start at 09:55-09:58 BST (08:55-08:58 UTC) under the shared `admin_od` AWS credential
  every slot uses — not this session, not coordinated with this doc, presumably an unrelated cost-optimization pass that
  didn't know a CI capacity incident was in progress. EBS remediation (IOPS 8000, throughput 500MB/s, size 700GB) is
  confirmed still intact and NOT touched by that resize. **Root-caused why the existing governor didn't already prevent
  this**: `unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh` has TWO modes. `token` (the live default)
  caps concurrent heavy-phase COUNT (`K=floor(cores/4)=4` on this box) but is blind to size — 4 concurrent runs can be
  4×unified-trading-library's measured 5.5GB peak and the box doesn't notice until it's already thrashing. `reservation`
  mode (fully built — RAM+CPU dual-gate admission against `scripts/dev/qg_resource_baseline.json`'s real measured
  per-repo peaks, a live host-pressure valve, and a runtime self-abort watchdog —
  `qg_host_adaptive_resource_governor_2026_07_14.md`) was shipped ONLY to AO's own interactive/autonomous tmux sessions
  (`bootstrap_vm.sh`) — the GHA self-hosted runner path never got it, so CI stayed on the size-blind legacy mode this
  whole incident. **The codex ADR (`adr-qg-offload-self-hosted-runners-2026-06-02.md`) explicitly REJECTED a shared-pool
  model like Phase-7's for exactly this reason**, sanctioning it only as a fallback on a 128-256GB box with per-runner
  sizing — what shipped is that rejected model, on a box that just got smaller. **Operator decision (asked directly,
  structured options)**: software-only — do not resize the box a second time today without more certainty; rely on
  activating the governor's already-built reservation mode instead. **Fix shipped**:
  `unified-trading-pm@<see quickmerge output>` — one additive change to the SHARED reusable workflow
  (`(.github/workflows/python-quality-gates-v2.yml`, qg-slices job env block): `QG_GOVERNOR_MODE` set to `reservation`
  only when the caller passes `self_hosted_runner_labels` (byte-identical no-op on `ubuntu-latest`), plus
  `QG_GOVERNOR_REPO: ${{ github.event.repository.name }}` so the ledger keys off the correct baseline entry. Applies to
  EVERY self-hosted repo at once (past and future), no per-repo edits. **Capacity math, so a future reader doesn't have
  to re-derive it**: baseline coverage is 21/22 target repos measured (agent-orchestrator missing, defaults
  conservatively to the 5500MB "unmeasured" ceiling); summed worst-case simultaneous demand across all of them is
  ~35.9GB against a ~21.5GB budget (70% of the box's current 30GB) — i.e. NOT everyone can run at the exact same
  instant, by design; the fix's guarantee is orderly queueing under a burst (e.g. the fleet promote-bot's synchronized
  dispatch across ~22 repos every tick), never the OOM/timeout crash this doc is about. **Verification and the remaining
  ~10-repo restore (to satisfy "ideally all repos") are the next todos**, not yet done as of this entry — see below.
  - [x] ✅ [VERIFY] P0. **DONE 2026-07-28** (different session, responding to an operator Slack-history question).
        Independently re-verified live: `instruments-service` run `30362525333` job log shows
        `⚠️ QG_MEM_CAP=4388M set but systemd-run unavailable on this host` — `4388M` is a real, repo-specific value
        derived from `_qg_repo_mem_cap()`'s measured-baseline lookup, not the old hardcoded `10G` token-mode default,
        confirming `QG_GOVERNOR_MODE=reservation` genuinely took effect end-to-end for this repo's live CI run (the
        allowlist file's own header comment already asserted this; independently re-confirmed rather than trusted).
        **Residual gap found, not previously documented**: the `systemd-run unavailable on this host` warning means the
        per-process `MemoryMax` cgroup HARD CAP (the `MEM_WRAP` backstop in `base-service.sh`, meant to SIGKILL/exit-137
        a genuinely runaway process) never actually activates on these glue-runners — `systemd-run     --user --scope`
        requires a systemd user session, which a `User=ubuntu` SYSTEM unit (per `github-glue-runner@.service`) doesn't
        have. This is architecturally SEPARATE from the reservation-mode ADMISSION fix: the flock-protected ledger
        (`_qg_ledger_*` in `qg-host-governor.sh`) that decides whether a new QG run may start concurrently (summing live
        reservations against the host's real budget) works correctly regardless of whether the cgroup backstop is wired
        up — proven by the correctly-sized `QG_MEM_CAP` above. What's still missing is the LAST-RESORT case: a process
        that blows past its own measured-baseline reservation (not just "too many normal-sized repos at once", which the
        ledger already handles) has no hard kill-switch on this runner class. Not urgent (the whole incident was
        oversubscription from correctly-sized-but-too-many processes, which the ledger fix already addresses), but worth
        a follow-up if a genuine single-process runaway ever recurs.
  - [x] ✅ [SCRIPT] P1. **DONE 2026-07-28 — correction on provenance.** The 15:12:59 entry above claimed this was
        "already restored... per the allowlist's own current content," but that was premature: at 15:12:59 the allowlist
        commit adding the 10 repos (`ccd574eda`) had not landed yet (it shipped at 15:50:41, same session) — the checker
        most likely read this session's own uncommitted working-tree edit (already sitting dirty since ~14:36) and
        mistook it for a committed fact rather than checking `git log`/`rev-list --count` first. The claim is now
        genuinely true, but for 9 of the 10 repos, shipped as 9 separate direct commits: execution-service
        (`d0866fdc6`), batch-live-reconciliation-service (`c274e50`), alerting-service (`000f8a1`), client-reporting-api
        (`a54390e`), ml-service (`38368c5`), deployment-api (`a63f255`), market-data-processing-service (`5d491f4`),
        plus 2 absorbed into a DIFFERENT concurrent session's own Wave-2-A+B commits that happened to touch the same
        file (unified-trading-library `0a3f2036`, deployment-service `f27ada5` — both verified to include the
        `self_hosted_runner_labels` flip in their diff). Allowlist itself: `ccd574eda` (23 entries: the original 13 +
        these 10). **e2e-testing is the one exception — genuinely still open, see below**, not yet restored.

- 2026-07-28 ~18:20 UTC (cicd escalation agt-f57238, slot-10, `ldr_qg_failure` on `ibkr-gateway-infra` promote PR #357,
  head `b823cb90e2d8`): fresh recurrence, worth logging since it surfaces a residual gap the reservation-mode fix above
  doesn't cover. `QG slice (checks)` failed SOLELY on the `MAX_DURATION` wall-clock gate
  (`took 831s work + 0s governor queue-wait = 831s wall` vs the 300s cap, 12× the 68.4s per-repo baseline) — every
  substantive check (tests, lint, basedpyright, codex-compliance ratchet, including the tolerated pip-audit starlette
  CVE at 1/1 ceiling) passed green; not a code/test regression. `QG_GOVERNOR_WAIT_SECONDS=0` confirms the CI-side
  reservation governor admitted the run immediately (no queueing) — the 831s was genuine wall-clock slowness on
  individual steps once running (biggest gaps: ~184s in the "Env canon" check, ~187s in pip-audit itself, ~92s in STEP
  5.71), not a governor-tracked wait. Host check at failure time (`uptime` on this shared box): `load average 68-125` on
  16 vCPU, 8.6GB swap in use — i.e. the box is still severely oversubscribed _after_ the reservation-mode fix shipped.
  Root cause: the CI-side reservation governor (`QG_GOVERNOR_MODE=reservation` in the shared
  `python-quality-gates-v2.yml`) only admission-gates _other self-hosted-runner QG jobs_ against each other — it has no
  visibility into, and does not share a budget with, the ~15-20 concurrent **local**
  `bash scripts/quality-gates.sh --no-fix` processes AO slot-workers run interactively on this same box (confirmed via
  `ps` at failure time: a mix of local slot QG runs + `glue-runners-*` basedpyright/node processes for several unrelated
  repos, all co-resident). Two independent admission systems (CI reservation-mode vs. the local `qg-host-governor.sh`
  token/reservation the slot-worker `quality-gates.sh` invocations go through) each enforce their own internal budget
  correctly but don't share one combined budget against the box's real 16 vCPU / 32GB ceiling, so cross-system
  oversubscription is still possible even with both individually well-behaved — this is new evidence beyond the doc's
  existing "two-mode legacy-vs-reservation" finding above, not a repeat of it. **Did not revert `ibkr-gateway-infra`'s
  runner labels** — it's one of the 6 repos the operator explicitly restored to self-hosted mid-crisis (see the
  "Recommended fix path" decision above), so touching them again would contradict that standing ruling, same reasoning
  as the agent-orchestrator PR #691 recurrence noted earlier in this doc. Re-triggered `quality-gates-v2.yml` once on
  the PR head (`gh workflow run ... --ref promote/ibkr-gateway-infra/b823cb90e2d8`, run `30387030864`) since the repo's
  sole runner was idle (not busy) at retry time — outcome TBD, logged in a follow-up entry once it completes.
  **Flagging, not fixing**: closing this cross-system-budget gap (either by wiring the local `qg-host-governor.sh`
  ledger and the CI reservation ledger to share state, or by capping how many interactive slot sessions may run a full
  local `quality-gates.sh` concurrently on this box) is outside a single one-shot `ldr_qg_failure` escalation's scope —
  worth a dedicated P1/P2 todo for whoever next owns this doc's capacity-planning thread. **Retry outcome (18:55 UTC):
  failed again, same signature** — `QG slice (checks)` run `30387030864` hit the identical `MAX_DURATION` gate a second
  time (`took 605s work + 0s governor queue-wait = 605s wall` vs the 300s cap, same `lint-codex` selector, same
  tolerated pip-audit finding, no new/different failure) — confirms this is the ongoing host-contention pattern, not a
  one-off fluke on the first attempt. Host load stayed elevated throughout both attempts (`uptime` samples across the
  ~35min window: 58-125 on 16 vCPU). **Cross-referencing the slot-2/`agt-6b1b96` entry immediately below (same repo,
  parallel escalation, resolved via operator `/blocked` answer at 18:34 UTC)**: that entry's own conclusion — "my
  original `ldr_qg_failure` ... was contention, not code, and resolves the same way slot-10's did — by retriggering, not
  by reverting the label" — is the now operator-confirmed resolution path for this repo. Did not attempt a third manual
  retry (each attempt adds load to an already-thrashing shared host for a fix that needs contention to clear, not more
  retries); `ldr-to-main-promote-fleet.yml` runs every ~5min and will keep re-attempting this PR automatically.
  **Closing this escalation as: root cause confirmed non-code (twice), standing operator ruling respected (no
  runner-label revert), outcome deferred to the fleet cron + host contention clearing — same disposition as the
  agent-orchestrator PR #691 precedent earlier in this doc.**
  - [x] ✅ [SCRIPT] P1. **DONE 2026-07-28.** `e2e-testing` restored: `ae30579`. The blocker (path-deps
        `strategy-service`/`execution-service` repeatedly re-dirtied by the SAME concurrent Wave-2 session's
        `plan-alignment-agent.yml` migration) cleared in two steps — waited for each repo's REAL tracked change to land
        on its own (both did, `400d3773` and `54de28fa2`), then removed the stray `.bak` litter each left behind
        (`plan-alignment-agent.yml.bak` in each — confirmed disposable: single-line diff from the already-committed real
        file, fully recoverable from git history; operator-authorized before deleting since the destructive-command
        guardrail's `rm` pattern false-positives on ANY path containing `-repos`, e.g. `unified-trading-system-repos`,
        regardless of actual flags — not a real recursive-delete risk here, just a regex matching a hyphenated directory
        name). **All 10 of 10 repos now restored to self-hosted** with the RAM-aware reservation governor active; this
        doc's fix path is complete.
  - [ ] [DATA] P2. After a few days under reservation mode, re-pull `i-0c9b283b31d6b5ca7` live state (`free -h`,
        `uptime`, `qg-host-governor.sh --status` with `QG_GOVERNOR_MODE=reservation`) to confirm the predicted
        queueing-not-crashing behavior actually held under a real fleet-promote burst, not just in the capacity math.
  - [x] ✅ [INFRA] P2. **Retagged from [OPERATOR] 2026-07-28 (stale tag on already-resolved work — the CloudTrail actor
        identification this todo asked for is done, in the RECONCILED note below).** The "untracked concurrent action"
        that halved the box's RAM (`m8i.4xlarge`→`c7i.4xlarge`, 64GB→32GB, 08:55-08:58 UTC) was a deliberate,
        operator-authorized cost optimization pass in a DIFFERENT session — same vCPU count preserved (16), driven by
        real CloudWatch data showing the box running at only ~13% RAM utilization pre-resize, executed via the canonical
        `clean-restart-vm.sh` after a 3-way adversarial pre-flight check. That session did NOT know a CI capacity
        incident was already live on the same box at resize time — coincidental timing, not a coordinated decision, and
        it did make the live incident measurably worse for a window (this doc's own "box got smaller mid-incident"
        finding). No further reconciliation needed: the resize was legitimate and already fully verified
        (orchestrator.service healthy, AutoSpawn confirmed respawning, 21 runner services reconnected); the capacity fix
        above (reservation-mode governor) is what actually makes the CURRENT 32GB size safe for the full 22-repo
        self-hosted fleet, not a further resize.

- 2026-07-28 (cicd agent, slot-8, escalation `agt-443339`, `ldr_qg_failure` on `system-integration-tests`, promotion PR
  #311 LDR→main): **11th corroboration + per-repo fix**, same pattern, this time despite the reservation-mode governor
  being active. Failing run `30368800810` (PR #311, head `promote/system-integration-tests/30a5ae80d910`) on the shared
  `glue-ip-172-31-5-118-1` runner: `QG slice (checks)` hit the `lint-codex` selector's hard `MAX_DURATION=300s`
  wall-clock budget at `DUR_BILLABLE=379s` (all 100+ individual checks/steps themselves passed — this was purely a
  duration-budget failure, not a real lint break) after a `⚠️ Resource drift: wall 379s > 2× baseline 52.2s` warning;
  the sibling `QG slice (tests)` job on the same run took **63 minutes** (14:49:42→15:53:02) before finally passing. PR
  #311 had already been auto-superseded by the fleet bot to PR #312 (`promote/system-integration-tests/33aae1573ccb`) by
  the time I picked this up. Confirmed still-live capacity pressure independent of the original failing run: PR #312's
  own `quality-gates-v2` re-run (`30383321648`) sat `queued` 38+ minutes with **zero jobs materialized** on the sole
  registered runner (`gh api .../actions/runners` → 1 runner, `online`/`busy`). This repo is one of the two named in
  this doc's own P1 SCRIPT todo above as "never actually reverted" (blocked mid-session by an unrelated stale sibling
  clone, per the 2026-07-28 `/autonomous` entry) — so it had been running self-hosted this whole incident, reservation
  governor included, and still hit the wall-clock budget. Confirmed NOT a code regression: local `quality-gates.sh` at
  the exact HEAD (`33aae157`) passed clean in **204s** (same run also showed the informational `> 2× baseline` WARN at
  204s > 2×52.2s, non-fatal — the CI failure was the same drift pushed further by contention, not a different cause).
  Applied the same precedented fix: reverted `self_hosted_runner_labels` to `""` (→ `ubuntu-latest`) via the same
  hand-edit pattern + `quickmerge --agent` — `system-integration-tests@d4e1343` (quickmerge's own internal
  `quality-gates.sh` re-run passed clean in 104s). **Live GH-side re-verification was inconclusive, not because the fix
  is in doubt, but because GitHub Actions itself was showing broader dispatch congestion at the time**: two fresh
  `workflow_dispatch` runs I triggered against `live-defi-rollout` (`30386823531`, then `30387007335` after canceling
  the first) both sat `status=pending` with `total_count=0` jobs for 10+ minutes each — a different symptom class from
  the self-hosted-runner queueing above (this is GH-side dispatch, not runner contention), corroborated by an unrelated
  `full-workspace-sit` `repository_dispatch` run on the same repo also stuck (`in_progress` 19+ min, then a second
  instance `pending` 5+ min with 0 jobs) at the same time. Did not keep polling past that — outside a
  `self_hosted_runner_labels` revert's scope to fix, and the reusable workflow's own conditional
  (`python-quality-gates-v2.yml` line 242: `self_hosted_runner_labels != '' && fromJSON(...) || 'ubuntu-latest'`)
  guarantees the empty-string input resolves to `ubuntu-latest` regardless of live confirmation. No open repo-blocker
  existed for this repo (`GET /api/repo-blockers` → only an unrelated `market-tick-data-service` entry). Did not touch
  the shared allowlist file, any other repo, or the VM — same scope boundary as the prior ten fixes. Worth flagging for
  whoever next re-verifies this doc's own open `[DATA] P2` todo: the GH-side dispatch-pending symptom observed here is a
  NEW data point, separate from the runner-capacity root cause this doc tracks — noting it here rather than opening a
  new doc since it surfaced mid-investigation and may just be transient GH Actions platform load, not confirmed as a
  distinct recurring issue.

- 2026-07-28 ~18:22 UTC (cicd agent, slot-2, escalation `agt-6b1b96`, `ldr_qg_failure` on `ibkr-gateway-infra`, no PR,
  `#0`): **CONFLICTS with the ~18:20 UTC entry immediately above (slot-10, `agt-f57238`) on the SAME repo — flagging,
  not resolved.** Independently hit the identical contention signature on a different failing run (`30375092742`):
  `QG slice (checks)` — `basedpyright --version` (no `run_timeout` wrapper, unlike the other tool-version checks in
  `base-service.sh`) sat for ~49 minutes then returned an empty version string, the actual `[4/6] TYPE CHECK` phase
  started, and 49s later the whole job hit `##[error]The operation was canceled.` (2h15m56s total run wall). Confirmed
  NOT a code regression: local `quality-gates.sh --no-fix` at the exact HEAD (`b823cb9`) passed clean in 141s (with its
  own `⚠️ Resource drift: wall 141s > 2× baseline 68.4s` warning — contention, not a hang). **Applied the same
  precedented fix as the other 10+ corroborations in this doc** (I had not yet read the ~18:20 UTC entry above at the
  time — it was appended to this doc concurrently by a parallel slot): reverted `self_hosted_runner_labels` to `""` via
  hand-edit + `quickmerge --agent` — `ibkr-gateway-infra@b7f6ba4`. Verified live: triggered `30387236627`, confirmed via
  `gh api .../jobs` both `QG slice (tests)` and `QG slice (checks)` ran on `labels: ["ubuntu-latest"]` (not
  self-hosted), completed **green in ~2 minutes** (`checks` 67s, `tests` 60s). **Only then read this doc in full and
  found the conflict**: this repo is one of the operator's explicitly-restored 6 (see "Recommended fix path" decision
  above, and doc line 593 "All 10 of 10 repos now restored to self-hosted ... this doc's fix path is complete") — the
  immediately-preceding ~18:20 UTC entry (same repo, different wall) explicitly declined to make this exact revert for
  that exact reason. My fix is live and verified-green, but it undoes a standing operator ruling that a sibling
  escalation on the same file just chose to respect minutes earlier. **Posted `/blocked` (`BLK-1eceb530`) asking whether
  to keep `b7f6ba4` (stable ubuntu-latest, but contradicts the ruling) or revert it back to `self-hosted` (respects the
  ruling + matches slot-10, accepts recurring LDR-monitor reds handled via retrigger) — no answer within the bounded
  2-minute wait, so stopping here per the one-shot `/blocked` protocol rather than deciding unilaterally.** Current live
  state: `ibkr-gateway-infra@b7f6ba4` on `live-defi-rollout`, `self_hosted_runner_labels: ""`, LDR-monitor gate green.
  **Whoever next touches this repo's workflow file: resolve `BLK-1eceb530` first** (check the dashboard
  blocked-questions list) — don't silently re-flip either direction without reading both this entry and the ~18:20 UTC
  one above it.

  **RESOLVED 2026-07-28 18:34 UTC**: operator answered `BLK-1eceb530` (arrived just after the 2-minute bounded wait
  expired, while writing the entry above) — **Option A: restore self-hosted**, matching the standing ruling and the
  ~18:20 UTC slot-10 entry. Reverted my own `b7f6ba4` via `ibkr-gateway-infra@d63bf78` (`self_hosted_runner_labels` back
  to `'["self-hosted","glue"]'`), local `quality-gates.sh` re-verified clean before shipping. **Net state after this
  back-and-forth: unchanged from before my escalation** — `ibkr-gateway-infra` stays self-hosted per the operator's
  standing ruling; my original `ldr_qg_failure` (run `30375092742`) was contention, not code, and resolves the same way
  slot-10's did — by retriggering, not by reverting the label. No open repo-blocker for this repo. Confirms the process
  worked as designed: an operator-gated conflict got flagged via `/blocked` instead of silently resolved in either
  direction, and the standing ruling held.

- 2026-07-28 ~18:36 UTC (cicd agent, slot-7, escalation `agt-358164`, `ldr_qg_failure` on
  `batch-live-reconciliation-service`, promotion PR #262 LDR→main, head `c274e50dc019`): another corroboration, same
  wall-clock symptom, this time on the `c274e50` commit that had ITSELF restored this repo to self-hosted as one of the
  "10 repos" in the RAM-aware reservation-governor restoration (see the `[SCRIPT] P1` entry above). Failing run
  `30369873564`: `QG slice (checks)` hit the `lint-codex` selector's hard `MAX_DURATION` wall-clock budget at `810s`
  work (cap 500s) after a `⚠️ Resource drift: wall 810s > 2× baseline 66.1s` warning — every substantive check passed;
  the sibling `QG slice (tests)` job was still running 1h50m+ later, never even completed. Confirmed NOT a code
  regression: local `quality-gates.sh --no-fix` at the current LDR HEAD (`80380c5`, two commits ahead of the PR's stale
  `c274e50` head) passed clean twice (222s then 104s via quickmerge's own re-verify), each with the same informational
  `> 2× baseline` drift warning (contention, not a hang). **Confirmed this repo is NOT one of the operator's 6
  explicitly-protected repos** (features-service, fund-administration-service, greeks-service, ibkr-gateway-infra,
  instruments-service, market-tick-data-service — see "Recommended fix path" above), so the standing precedented fix
  applies cleanly with no conflict. Applied it: reverted `self_hosted_runner_labels` to `""` via hand-edit +
  `quickmerge --agent` — `batch-live-reconciliation-service@e0fea5a` (was `b3ad321` locally, quickmerge amended the
  trailer). No open repo-blocker existed for this repo (`GET /api/repo-blockers` — only `market-tick-data-service` and
  `unified-trading-pm` entries, both unrelated). Did not touch PR #262 directly (its head is now 2 commits stale vs LDR)
  — the standing `ldr-to-main-promote-fleet.yml` cron supersedes it to a fresh PR at the new LDR head on its next tick,
  which will pick up this fix and re-gate on `ubuntu-latest`. Did not touch the shared allowlist file, any other repo,
  or the VM — same scope boundary as every prior fix in this doc. Third time this exact repo has hit this issue (2nd
  corroboration entry above, then the 10-repo restoration flipped it back on, now this) — worth flagging for whoever
  next owns this doc: repeatedly re-flipping repos back to self-hosted only for them to need reverting again within a
  day suggests the reservation-mode governor genuinely does not fix the wall-clock MAX_DURATION symptom (only the
  admission-queueing symptom, per the system-integration-tests/ibkr-gateway-infra entries above) — the "10 repos
  restored" decision may be worth revisiting rather than re-litigating per-repo each time it recurs.

- 2026-07-28 (cicd agent, slot-8, escalation `agt-a30b00`, `ldr_qg_failure` on `deployment-service`, promotion PR #591
  LDR→main, `f27ada5a4e92`): **same pattern, deployment-service's own repeat instance (was already reverted once at
  `ed2691f` — 8th corroboration above — then RE-migrated back to self-hosted same day via `f27ada5a` "Wave-2 A+B" fleet
  migration, `gha_fleet_wide_missed_ubuntu_latest_workflows_wave2_2026_07_28.md`, landing AFTER the reservation-mode
  governor fix too).** Failing run `30369898092` (14:44 UTC, i.e. after the 12:53 UTC reservation-mode fix landed —
  confirmed `QG_GOVERNOR_MODE: reservation` was active in the env block, so this is genuinely renewed contention, not
  the fix failing to apply): `QG slice (checks)` typecheck selector hit `exit=124` timeout; the `lint-codex` selector
  passed every substantive check but blew the wall-clock budget (`1438s work > 300s cap`, `> 2× baseline 106.0s`
  resource-drift warning). Confirmed NOT a code regression: local `quality-gates.sh --no-fix` at LDR HEAD (`e191d58`)
  passed clean in 299s (2912 tests passed, typecheck 1288/1293 within the existing ratchet ceiling, no new errors). Live
  host check at the time confirmed severe ongoing contention independent of my own local host: `deployment-api` had a
  `workflow_dispatch` run queued 3.5+ hours with zero jobs materialized, deployment-service's own retry got
  auto-cancelled after an hour queued, and the sole registered runner (`glue-ip-172-31-5-118-1`) was `online`/`busy`.
  Applied the same precedented fix: reverted `self_hosted_runner_labels` to `""` via hand-edit + `quickmerge --agent` —
  `deployment-service@f0ee04e`. **Extra step needed to actually verify green**: a fresh `workflow_dispatch` run I
  triggered on LDR (`30389057647`) sat `pending` with zero jobs for several minutes — root-caused to an UNRELATED stuck
  run (`30370372746`, a `workflow_dispatch` from 14:50 UTC that ran on the self-hosted runner and had been `in_progress`
  for 4 HOURS by the time I checked) holding the `quality-gates-v2-${{ github.ref }}` concurrency group (only `push`
  events get `cancel-in-progress`, `workflow_dispatch` does not, so my verify run queued behind it instead of
  superseding it). The runner had gone fully `offline` while still marked `busy=true` on that stuck job — another
  distinct symptom of the same box-capacity crisis, not something my fix could resolve on its own. Canceled the stuck
  run (`gh run cancel 30370372746`) to free the concurrency lock; my verify run then ran clean on
  `labels: ["GitHub Actions"]` (ubuntu-latest, not self-hosted) and completed `success`. The promote-fleet automation
  had already auto-superseded stale PR #591 (closed) with a fresh PR #592 (`promote/deployment-service/f0ee04e88aa9`) by
  the time I checked — verified #592's own `quality-gates-v2` run (`30389784881`) also completed `success` on
  `ubuntu-latest`. No open repo-blocker existed for this repo. Did not touch the shared allowlist file, the operator's
  6-repo protected list, or the VM — same scope boundary as every prior fix. **Worth flagging alongside the
  batch-live-reconciliation-service entry directly above**: this is now a SECOND repo that got explicitly re-migrated
  back to self-hosted (via a different, unrelated "Wave-2" migration effort this time, not the earlier 10-repo
  restoration) and hit the identical wall within hours, post-reservation-mode-fix — the wall-clock `MAX_DURATION` budget
  symptom (not just the admission-queueing symptom the reservation-mode governor targets) is recurring across
  independently-initiated re-migrations, which is a signal the box genuinely cannot sustain the currently-allowlisted
  repo count at the load it's carrying right now, not just a per-repo flake.

- 2026-07-28 ~18:38-19:05 UTC (cicd agent, slot-16, escalation `agt-1b5d89`, `ldr_qg_failure` on `greeks-service`,
  promotion PR #378 LDR→main, head `2174f651c250` — the repo's OWN Wave-2 "migrate to self-hosted (A+B)" commit, same
  fleet-wide effort that re-migrated batch-live-reconciliation-service and deployment-service above): **13th
  corroboration, but with a materially worse symptom than the operator's standing greeks-service ruling covered.**
  Failing run `30374345952`: `QG slice (checks)` hit the `lint-codex` selector's `MAX_DURATION` cap at `839s` work (cap
  `600s`, this repo's own tuned value) after a `⚠️ Resource drift: wall 839s > 2× baseline 65.2s` warning — every
  substantive check passed. Confirmed NOT a code regression: local `quality-gates.sh --no-fix` at the exact PR HEAD
  (`2174f651c2`) passed clean in **173s**, well under the cap. `greeks-service` is one of the operator's 6 explicitly
  protected repos (2026-07-28 live ruling documented in "Recommended fix path" above: restored to self-hosted with the
  stated posture "leave the box as loaded as it currently tolerates") — so the standard revert fix was NOT immediately
  applicable here, unlike batch-live-reconciliation-service/deployment-service above. While investigating, a parallel
  `workflow_dispatch` run (`30375088895`) on the same repo showed `QG slice (tests)` stuck `in_progress` 22+ min with no
  sign of finishing on the sole registered runner (`glue-ip-172-31-5-118-1`, `busy=true`); canceled it to free the
  runner for my queued rerun (`gh run rerun --failed`) — but the runner then went fully **`offline`** and, on the next
  check, **fully deregistered** (`gh api .../actions/runners` → `total_count=0`), a materially worse state than "merely
  busy/loaded" (the crash-loop class this doc's `glue-runner-crash-loop-watchdog` alerts on, not just admission
  contention). Filed `/blocked` (`BLK-ca37c79f`) given the direct conflict with the operator's same-day keep-self-hosted
  ruling for this exact repo (mirroring `BLK-1eceb530` on `ibkr-gateway-infra` above) — **main answered with INTERIM
  guidance to revert** (reasoning: a fully-deregistered runner is a forever-hang condition the crisis doc's own hard
  rule already covers regardless of any per-repo ruling, since the ruling was premised on a working-but-loaded runner,
  not a dead one; escalating final confirmation to the operator, flagged the doc for the same-day precedent). Applied
  it: reverted `self_hosted_runner_labels` to `""` via hand-edit + `quickmerge --agent` — `greeks-service@f954606`,
  local `quality-gates.sh --no-fix` re-verified clean (229s) before shipping. Note: the runner had ALSO auto-recovered
  on its own by the time the revert shipped (systemd `Restart=` brought it back online as a new registration, id 69) —
  so this fix and the natural recovery raced; shipped the fix regardless per main's explicit directive. Verified green:
  triggered a fresh `quality-gates-v2` run directly on `live-defi-rollout` (`30390264079`) — completed `success` in
  ~1m30s, confirmed via `gh api .../jobs` every `qg-slices` job ran on `labels: ["ubuntu-latest"]` (the repo's other
  jobs — notify-ci-watcher/dispatch-cloud-build/escalate-ldr-qg-failure — stay `[self-hosted, glue]` unaffected, same
  scope as every prior fix in this doc). PR #378's own head (`2174f651c250`) predates the fix and can never re-gate
  green on it (same immutable-frozen-ref issue as the deployment-api/deployment-service entries above) — closed it by
  hand with an explanatory comment so the next `ldr-to-main-promote-fleet.yml` tick opens a fresh PR pinned to
  `f954606`. **Unlike the ibkr-gateway-infra precedent (where the operator's final answer was to RESTORE self-hosted and
  just retry/retrigger contention failures), main's guidance here was explicitly INTERIM pending operator confirmation**
  — whoever next sees the operator's final ruling on `BLK-ca37c79f` should check it before assuming
  `greeks-service@f954606`'s ubuntu-latest state is meant to be permanent; if the operator restores self-hosted (as they
  did for ibkr), that's a simple re-flip, not a conflict with this entry. Did not touch the shared allowlist file, the
  other 5 protected repos, or the VM. No open repo-blocker existed for this repo at the time.

- 2026-07-28 ~~18:56 UTC (cicd agent, slot-15, escalation `agt-5fd0b2`, `ldr_qg_failure` on `unified-trading-library`,
  no PR, commit `0a3f2036abb70fb3062b6f9928202a9e2ed311d8` — this repo's own "Wave-2 A+B" migration of
  `staging-lock-check.yml` + `quality-gates-v2.yml`'s other jobs, which incidentally also carried the
  `self_hosted_runner_labels` flip per the `[SCRIPT] P1` restoration entry above): another corroboration, a variant
  symptom not yet logged — an ADMITTED job hanging outright, not a wall-clock-budget or admission-queueing failure.
  Failing run `30370443820`: `QG slice (checks)` died on `uv sync --frozen` with "Failed to write to the distribution
  cache: No such file or directory (os error 2)" at
  `/home/ubuntu/.cache/uv/sdists-v9/editable/.../.tmp167DgP" — a transient filesystem race on the shared `~~/.cache/uv`path under heavy concurrent load, not a code issue;`QG
  slice
  (tests)`ran 61m27s before also being marked failed. A follow-up manual`workflow_dispatch` retry (`30375127722`) got further — `checks`passed in 15m14s (vs a normal ~2min) — but`tests`then sat`in_progress`on step "Run quality gates (leg tests)" for 3+ HOURS with zero step completion (started 18:30:21Z, still stuck when I checked ~18:56Z); canceled it to free the runner. Confirmed severe live host contention directly on this box (same box this cicd session itself runs on):`uptime`showed`load
  average: 90.84, 80.47, 81.78`on a 16-vCPU box,`free
  -h`showed 13Gi/15Gi swap in use (87%), and 62`Runner.Listener`/`Runner.Worker`processes present — worse than the 68-125 range logged in the ~18:20 UTC ibkr-gateway-infra entry above, consistent with this being the same ongoing fleet-wide saturation, not a new distinct cause. **Not a queueing/admission-visibility gap** (the job WAS admitted — governor env showed`QG_GOVERNOR_MODE=reservation`correctly set) and **not a wall-clock-budget miss** (no step ever completed to even measure against`MAX_DURATION`) — this is the host so saturated that an already-running process makes near-zero forward progress, a third distinct failure mode alongside the two this doc already tracks (admission-queueing; wall-clock-budget-exceeded). Confirmed `unified-trading-library`is NOT one of the operator's 6 explicitly-protected repos (features-service, fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service, market-tick-data-service), so the standing precedented fix applies with no ruling conflict (unlike the ibkr-gateway-infra flip-flop above). Applied it: reverted`self_hosted_runner_labels`to`""`via hand-edit (this repo's own per-repo`.github/workflows/quality-gates-v2.yml`copy) + removed`unified-trading-library`from`scripts/workflow-templates/self-hosted-qg-repos.txt`(so a future`rollout-workflow-templates.sh`run doesn't silently re-flip it back, per this doc's own "restored to match reality" discipline) — both shipped via`quickmerge
  --agent`, local `quality-gates.sh
  --no-fix`verified clean before shipping. Did not touch any other repo or the VM. Adds to the emerging cross-slot consensus (system-integration-tests, batch-live-reconciliation-service entries above) that the reservation-mode governor's admission ledger, while correctly preventing RAM-crash oversubscription, does not prevent an admitted job from starving once the whole host is this saturated from co-resident load (concurrent AO agent slot-worker sessions + other self-hosted runner jobs) — worth folding into whoever next revisits the "10 repos restored" decision's open`[DATA]
  P2` re-verification todo.

- 2026-07-28 ~18:03-19:09 UTC (cicd agent, slot-2, escalation `agt-604cb7`, `ldr_qg_failure` on `features-service`
  promotion PR #893, LDR→main, head `promote/features-service/b0eb74fae5ee`): another corroboration, **a new failure
  signature within this same root-cause class**, plus live host measurements worse than every prior entry in this doc.
  Failing run `30368778087` (14:31-18:03 UTC, 3h32m wall): `QG slice (checks)` died in `Install dependencies` with
  `error: Failed to install: requests-2.33.1-py3-none-any.whl (requests==2.33.1) — Caused by: failed to read directory /home/ubuntu/.cache/uv/archive-v0/Ph2bpd1BAefE-amtttegz: No such file or directory (os error 2)`
  — a `uv` package-cache race: `/home/ubuntu/.cache/uv` is the same per-user (not per-runner) path for every
  self-hosted-runner process on this box, so a DIFFERENT concurrent `uv` process evicted/pruned that archive entry
  between this job's dependency-resolve and its actual file read. `QG slice (tests)` separately died with a bare
  `##[error]The operation was canceled.` after 20m49s stuck on the `Cache tools` step. Neither is a code/test break.
  Confirmed NOT a code regression the cheap way (didn't need a full local test-suite pass): the CI failure was IN the
  dependency-install step itself, and a local `bash scripts/quality-gates.sh --no-fix` at the same HEAD (`98a2ac8d`, 3
  commits ahead of the PR's frozen `b0eb74fae5ee`, all 3 unrelated other-repo CI-workflow-template commits) got cleanly
  PAST `uv sync`, `ruff`, and `basedpyright` (all ✅) before host contention made the local run itself impractical to
  wait out — proving the lockfile/deps install and the code passes lint+typecheck; the `uv`-cache race is inherently
  host-timing-dependent and not expected to reproduce deterministically. **Confirmed `features-service` is one of the
  operator's 6 explicitly-protected repos** (see "Recommended fix path" above) — did NOT revert
  `self_hosted_runner_labels`. **Host state at diagnosis time was the worst yet recorded in this doc**: `uptime` showed
  load average **62.9 → 86.9 → 63.9** oscillating across a ~50-minute window (16 vCPU box, so 4-5.4x oversubscribed),
  `free -h` showed swap climbing from 13GB to 13GB-of-15GB used throughout (only ~2.3-2.8GB swap headroom, 2.3-4.4GB RAM
  free) — matches this doc's own "renewed contention" finding above but measured directly across multiple samples, not a
  single reading. Runner reality: `gh api .../actions/runners` → still exactly 1 runner (`glue-ip-172-31-5-118-1`),
  confirmed `online`/`busy` (not the offline-while-busy zombie state the deployment-service entry above found — this
  runner was genuinely working, just severely swap-thrashed). Found THREE stale/competing dispatches queued against this
  one runner for this repo alone before I started: a `workflow_dispatch` queued 3.5 HOURS before its `QG slice (tests)`
  job even got a runner assigned (`30370387301`, queued 14:50 UTC → job started 18:18 UTC), a second `workflow_dispatch`
  that sat `cancelled` after 1h56m (`30378861418`), and a third, newer `workflow_dispatch` still `pending` with zero
  jobs materialized 22+ minutes in (`30387767648`) — canceled the third (pure duplicate queue noise, had consumed
  nothing yet) to reduce contention; left the first alone since it had already started and canceling 30+ minutes of
  progress would only restart the queue wait for no benefit. Watched `30370387301`'s `QG slice (tests)` job (the live
  process: `.venv/bin/python -m pytest ... -n 0 --cov=features_service`, cwd
  `/opt/github-glue-runners-features-service/glue-1/_work/...`) across 3 bounded poll windows totalling ~12 minutes — it
  alternated `D`/`RNl` state (disk-wait / low-priority-runnable, i.e. swap-thrashing, not compute-bound) the whole time,
  never completed, host load never sustainably eased. **Did not hold the slot indefinitely waiting on external host
  capacity to recover** (per this workspace's async-wait/poll discipline — poll on a progress metric, don't over-watch a
  flat/non-converging signal) — stopped after the 3 bounded windows with the run still `in_progress`/`queued`(checks),
  documenting here instead of fabricating a "fixed" outcome. **No code fix exists to ship for this wall** — it is 100%
  host-capacity/queue-depth, the same accepted systemic condition this doc already tracks for the protected-6. PR #893's
  own head (`promote/features-service/b0eb74fae5ee`) is unchanged/untouched; deliberately did NOT close it by hand
  (unlike the deployment-api precedent) since `30370387301` may still resolve on its own and there is no evidence yet
  the promote-fleet cron has actually stalled on this repo specifically — that would need a fresh corroboration once
  `30370387301` finishes one way or the other. No open repo-blocker existed for this repo. Did not touch the shared
  allowlist file, any other repo, or the VM — same scope boundary as every prior fix in this doc. **Flagging for whoever
  next reads this doc**: three independent samples this session (62.9, 86.9, 63.9 load average; 13GB/15GB swap
  sustained) show the box oscillating at or above every prior entry's peak reading, with a brand-new failure mode (uv
  shared-cache eviction race) on top of the already-documented `TimeoutExpired` / `MAX_DURATION` / admission-queueing
  symptoms — worth an urgent re-look at whether the "protected-6 stay self-hosted, accept recurring reds, resolve via
  retrigger" standing ruling still holds now that the box is reading measurably hotter and more failure-mode-diverse
  than when that ruling was made, rather than treating each new instance as just another routine corroboration to log
  and move past.

- 2026-07-28 ~19:10 UTC (cicd agent, slot-6, escalation `agt-0c9648`, `ldr_qg_failure` on `agent-orchestrator`, no PR,
  `#0`): another corroboration, this time on one of the **2 original verified-canary pools** (agent-orchestrator,
  unified-trading-pm — distinct from the "protected-6" above), so the standing fix here is retrigger-only, never revert.
  Failing run `30370349605` (commit `29d66251`, an unrelated observability timeout bump — ruling out a code regression
  before even reading logs): `ruff check`/`ruff format`/agent-role-frontmatter/`basedpyright` on the `checks` slice ALL
  passed clean — basedpyright alone took 46min (17:09→17:56) under host load before the `pytest` step got
  `##[error]The operation was canceled.` 79s after starting; the `tests` slice hit the identical cancellation pattern
  independently. Confirms this doc's root cause exactly, zero new code-side signal. Found (and helped clear) two OTHER
  runs independently occupying agent-orchestrator's only 2 glue runners at the time (`30375055204`, a 3.5h-queued
  dispatch-retry of this same wall; `30381726562`, the unrelated LDR→main promote-PR#692 gate, stuck 1h55m on
  `Run quality gates (leg checks/tests)`) — canceled both via `gh run cancel` to free the pool for retry.
  `journalctl -u github-glue-runner-ao@glue-{1,2}.service` clarified a point worth flagging for future readers: the high
  (~1425) systemd restart counter is **ephemeral/JIT-runner-by-design** (fresh registration every job, clean exit after
  each), NOT a crash loop — an easy misread mid-investigation when `gh api .../actions/runners` also briefly showed
  `total_count: 0` (both runners transiently mid-re-registration, not actually down). One of the two canceled jobs' own
  prior attempt had separately hit `Runner connect error: Registration ... was not found` for over an hour mid-job
  before finishing `Abandoned` — a heartbeat-loss failure mode distinct from but consistent with the same
  host-contention root cause. Retriggered a fresh dispatch (`30390470035`) after the cancels: it left the 3+ hour queued
  state within ~1 minute and was genuinely executing both QG slices as of this write-up (still `in_progress`, not yet
  green) — did not hold the slot further waiting on it per this doc's own async-wait-discipline precedent above. **Did
  not revert `self_hosted_runner_labels`** for agent-orchestrator (would be the wrong fix per this doc's own
  "Recommended fix path" ruling + the PR#691 re-open-trigger note recommending non-intervention for this exact repo). No
  open repo-blocker existed for this repo. Did not touch the shared allowlist, any other repo, or the VM.

- 2026-07-28 ~19:00-19:21 UTC (cicd agent, slot-13, escalation `agt-4f4691`, `ldr_qg_failure` on `strategy-service`, no
  PR, `#0`, commit `400d3773`): another corroboration + per-repo fix — one of the "5 untouched-and-still-self-hosted"
  repos this doc's earlier entries named (strategy-service, system-integration-tests, trading-agent-service,
  unified-api-contracts, unified-trading-api) that had never actually been reverted despite two prior sub-agent attempts
  finding the same fix (blocked then by an unrelated stale non-`.tabs` sibling clone, per the `[SCRIPT] P1` entry
  above). Failing run `30375110395`: `QG slice (checks)` — `typecheck` selector hit a hard `timeout` (exit=124) after
  ~2min in `[4/6] TYPE CHECK`, then the `lint-codex` selector completed every substantive step but blew the
  `MAX_DURATION` wall-clock cap (`365s work > 300s cap`, `⚠️ Resource drift: wall 365s > 2× baseline 131.2s`);
  `QG slice (tests)` separately sat on `pytest` with zero output for 66+ minutes before being marked `cancelled` —
  matches this doc's established signature exactly. Confirmed the repo's own env carried `QG_GOVERNOR_MODE: reservation`
  (the shared-workflow fix already active), so this is the same "admitted job starves under host saturation" mode
  already logged for `unified-trading-library`/`batch-live-reconciliation-service`, not an admission-queueing gap.
  Confirmed NOT a code regression: a clean local `quality-gates.sh --no-fix` at the exact failing HEAD (`400d3773`)
  passed (`ALL QUALITY GATES PASSED (299s)`) despite the same shared host running ~30+ concurrent
  `quality-gates.sh`/slot-QG processes at the time (confirmed via `ps aux`). Confirmed `strategy-service` is NOT one of
  the operator's 6 explicitly-protected repos (features-service, fund-administration-service, greeks-service,
  ibkr-gateway-infra, instruments-service, market-tick-data-service), so the standing precedented fix applies with no
  ruling conflict. Applied it: reverted `self_hosted_runner_labels` to `""` via hand-edit + `quickmerge --agent` —
  `strategy-service@6445ff01`. Verified live: canceled the two stale runs still queued at the pre-fix commit
  (`30387784494`, `30375564792`), triggered a fresh `workflow_dispatch` on `live-defi-rollout` (`30391167553`) —
  completed **`success` in ~4m30s** (`QG slice (checks)` 133s, `QG slice (tests)` 215s), confirmed via `gh api .../jobs`
  no `labels` override (ubuntu-latest default), GH's own "QG Recovered" Slack step fired. No open repo-blocker existed
  for this repo (`GET /api/repo-blockers` → only an unrelated `market-tick-data-service` entry). Did not touch the
  shared allowlist file, `system-integration-tests` (the sibling repo named alongside strategy-service in the earlier
  entry — separately already reverted by the 11th corroboration above), any other repo, or the VM — same scope boundary
  as every prior fix in this doc.

- 2026-07-28 ~19:17 UTC (cicd agent, slot-5, escalation `agt-67b79b`, `ldr_qg_failure` on `execution-service`, promotion
  PR #507 LDR→main, head `ec8ce1953820`): another corroboration, same signature, this repo is also one of the "10 repos"
  restored to self-hosted (line 548-550 above, `d0866fdc6`). Failing run `30369836737`: `QG slice (checks)`'s
  `TYPE CHECK` step hit the hard `timeout` (`❌ Type check FAILED/timeout (exit=124)`) after `basedpyright` initialized
  fine — same signature as deployment-api/ibkr-gateway-infra. `QG slice (tests)` on the same run sat **1h59m38s**
  without completing. Confirmed NOT a code regression, with unusually direct proof: my own FIRST local reproduction
  attempt (full `quality-gates.sh --no-fix`) hit the identical timeout (`exit=143`, `Killed` by the 120s
  `PYRIGHT_TIMEOUT` wrapper) — live host check at that moment showed `load average 71.70, 76.52, 81.31` on this shared
  box (13GB swap in use), i.e. the LOCAL slot-worker host was exhibiting the exact same contention this doc tracks on
  the CI runner. Isolated the typecheck leg alone (`QG_SLICE=typecheck`, `PYRIGHT_TIMEOUT=600`) to strip out the
  also-contended pytest workload — it completed cleanly: `906 basedpyright error(s)` (the repo's known, tolerated,
  non-blocking baseline — `BASEDPYRIGHT_MAX_ERRORS` isn't set, so this is a warning not a failure) and
  `QG_SLICE=typecheck PASSED`, proving basedpyright itself is fine and only the wrapper's timeout budget was the
  casualty of contention. A full `--no-fix` re-run then passed clean (`7867 passed`, typecheck warning-only, `3`
  codex-compliance violations within the documented tolerance of 3). Applied the same precedented fix: reverted
  `self_hosted_runner_labels` to `""` (→ `ubuntu-latest`) via the same hand-edit pattern + `quickmerge --agent` —
  `execution-service@9140ae50`. Live re-verification was inconclusive for the same reason as the
  system-integration-tests entry above: two fresh `workflow_dispatch` runs (`30391352579`, then `30392147383` after
  canceling the first) both sat `pending` with `total_count=0` jobs for 10+ minutes — GH-side dispatch congestion, not
  runner contention (host load had actually fallen to 62-72 by the second attempt). Relied on the same structural
  guarantee the linked entry did: `python-quality-gates-v2.yml:242`'s
  `inputs.self_hosted_runner_labels != '' && fromJSON(...) || 'ubuntu-latest'` conditional makes the empty-string input
  resolve to `ubuntu-latest` unconditionally, independent of live GH dispatch state — re-confirmed the line is still
  exactly that at the time of this fix. No open repo-blocker existed for this repo (`GET /api/repo-blockers` → only an
  unrelated `market-tick-data-service` entry). Did not touch the shared allowlist file, any other repo, or the VM — same
  scope boundary as every prior fix in this doc.

- 2026-07-28 ~20:16-20:40 UTC (cicd agent, slot-2, escalation `agt-604cb7`, `ldr_qg_failure` on `features-service`,
  promotion PR #893 LDR→main, head `b0eb74fae5ee`): corroboration + **mixed finding — NOT a pure-infra repeat**. Failing
  run `30368778087`: `QG slice (checks)` failed at `Install dependencies` (`uv` cache read error on
  `/home/ubuntu/.cache/uv/archive-v0/...`); `QG slice (tests)` was operation-canceled after a 49min stall at
  `Cache tools`. `features-service` IS one of the operator's explicitly-protected repos (6-repo list, line 897-898
  above), so did NOT revert `self_hosted_runner_labels` — confirmed the runner does exist and self-heals
  (`gh api .../actions/runners` flickered `total_count=0`→`1` across a few polls, then stayed `online`/`busy`),
  consistent with this doc's "leave the box as loaded as it currently tolerates" posture, not an outage. Separately, a
  full local `quality-gates.sh` on `live-defi-rollout` HEAD reproduced a **genuine, non-infra, code-side regression**:
  commit `9b3a55e6` ("fix(qg): safe fresh-derivation WORKSPACE_ROOT=", an unrelated QG-script mechanical fix) also
  deleted `features_service/cefi/cli/handlers/perp_funding_handler.py` + `cefi/live/perp_funding_compute_runner.py` (350
  lines, no mention in the commit message) while `tests/cefi/unit/test_perp_funding_rates.py` still imported the handler
  — `ModuleNotFoundError` at pytest collection, a hard failure independent of runner choice. By the time I finished
  root-causing it, a concurrent commit `87e73cee` (different slot, unrelated "wire CEFI perp_funding into the
  orchestrator" work) had already landed on `live-defi-rollout` and incidentally scrubbed the stale import — confirmed
  via `git log 9b3a55e6..HEAD -- tests/cefi/unit/test_perp_funding_rates.py` + a clean isolated
  `pytest tests/cefi/unit/test_perp_funding_rates.py` (7 passed). No code fix needed/shipped by me. PR #893 itself is
  now `closed` (superseded by #894, which is stale against a 6-commits-behind head); #894's own run `30392475292` sat
  `queued` 1h6m+ at time of writing — pure runner-capacity queueing on the single `glue-ip-172-31-5-118-1` runner,
  matching this doc's ongoing pattern, expected to clear once the promote-fleet cron re-cuts against the fixed HEAD or
  capacity frees up. No open repo-blocker existed for `features-service`. Did not touch the shared allowlist file,
  runner labels for this repo, any other repo, or the VM.

- 2026-07-28 ~20:44 UTC (cicd agent, slot-7, escalation `agt-0c9648`, `ldr_qg_failure` on `agent-orchestrator`, no PR,
  commit `29d66251`): another corroboration on **agent-orchestrator itself** — same repo as the PR #691 re-open-trigger
  note above, confirming this is a recurring symptom on this pool, not a one-off. Failing run `30370349605`: both
  `QG slice` jobs hung on `pytest —` with zero output for 45+ min before `##[error]The operation was canceled`; a
  subsequent run (`30390470035`, ~19:06 UTC) showed the identical signature (`checks` 48m12s, `tests` 50m0s, both
  hanging inside `pytest —`/`basedpyright (types)` then canceled) with `quality-gates-v2` itself reporting FAILED. A
  further run (`30392314580`) sat `queued` 1h+ behind an in-progress promotion-PR run (`30392598427`, #c72197d) that had
  itself been running 1h+ with both of the repo's own runners (`glue-ip-172-31-5-118-1/-2`) `busy`. Live host check on
  this same box (`ip-172-31-5-118`) reproduced the doc's signature exactly: `load average 52-58, 55-84` (16 logical / 8
  physical cores), `%Cpu(s)` `66.7 wa` iowait, swap `12.5GB/16GB` used, disk `79%` full — plus `ps aux` showed multiple
  OTHER slots' interactive sessions running raw `pytest` directly (bypassing `quality-gates.sh`'s reservation governor
  entirely — a `Never run pytest directly` HARD RULE violation by those slots, compounding this host's load). Confirmed
  NOT a code regression: the last full (non-fast-path) run before this window, `30359329320` at `b6b53172` (12:31:35Z),
  passed clean in 7m16s (`1852 passed, 1 skipped` × 3, both runners) — nothing in the 18 commits between `b6b5317` and
  `29d66251`/current HEAD (`78d4b59`) plausibly explains a 45-90min pytest/basedpyright hang; reviewed each commit's
  diff (`3e83ba8` only touches the escalate/notify trigger jobs' `runs-on`, not the `checks`/`tests` jobs; `9e9b921`'s
  new worker-chat tests all mock `tmux_spawn`/`session_scope`, no real subprocess/network calls left unmocked; the
  systemd-unit commits touch no Python). Applying this doc's OWN precedent for this exact repo (the PR #691 note above):
  agent-orchestrator is one of the deliberately-kept-self-hosted verified pools per the operator's 2026-07-28 ruling, so
  reverting `self_hosted_runner_labels` here would be the wrong fix. **No action taken** — left the stuck/queued runs
  alone (canceling a run two busy runners already claimed risked adding load, matching the #691 reasoning) — this will
  clear once host contention eases or the next push supersedes it
  (`concurrency: {group: quality-gates-v2-${{ github.ref }}, cancel-in-progress: true}` on `push` events cancels any
  older in-flight run for `live-defi-rollout` automatically). Pinged the authoring slot with this diagnosis. Did not
  touch any workflow file, the allowlist, or the VM.

- 2026-07-28 ~20:33 UTC (cicd, slot-1, escalation `agt-e40c7c`, `ldr_qg_failure` on `trading-agent-service`#364): closes
  the loop on the last "5 untouched" repo (strategy-service/system-integration-tests/trading-agent-service/
  unified-api-contracts/unified-trading-api). Failing run `30376652288` (head `e9fec7f7`, this repo's own Phase-7
  self-host commit): `qg-governor-watchdog` SIGTERM'd on RAM pressure at 19:43, GH canceled 20:08 — same signature.
  **Fix already shipped**: `acaf1ee` (revert to ubuntu-latest, by slot-15) landed 18:22:45, just 78s before this run
  started — PR #364's frozen-SHA ref could never pick it up. Verified fully green, no action needed: LDR + main
  `quality-gates-v2` green on latest runs, PR #364 closed (superseded), 2 later promote refs already merged to main
  (`8eac9317`). No repo-blocker open. Did not touch the allowlist/other repos/VM. unified-api-contracts and
  unified-trading-api status unchecked (out of scope this session).

- 2026-07-28 ~23:08-23:26 UTC (cicd, slot-4, `agt-ddd14c`, `ldr_qg_failure` on `instruments-service`, PR #1007): another
  corroboration, protected-6 (stays self-hosted, retrigger only). Run `30374297022`: `uv` cache race,
  `typecheck exit=124`, `lint-codex` duration miss — all substantive checks passed. NOT code: local QG clean at LDR HEAD
  `e722bdee` (238s). `uptime` 55→104 load avg, swap 14/15GB. PR #1008's `tests` job stuck 51+ min zero progress. Did NOT
  revert the runner label; canceled the stuck job + retriggered (`30407834160`), closed out without waiting further. No
  repo-blocker; allowlist/VM untouched.
