---
scope: [engineer, admin]
---

# Monitoring control plane — CI dashboard + fleet git-health

> SSOT for the monitoring read surfaces (codified 2026-06-10). Plans:
> `plans/active/monitoring_control_plane_master_2026_06_10.md` (master) + `ci_dashboard_deployment_ui_2026_06_10.md` +
> `fleet_git_health_orchestrator_2026_06_10.md`.

## Alert-parity principle (operator, 2026-06-10)

**Anything we alert on generically must be a continuously observable STATE in the UI.** An alert is the transition of a
state the dashboard always shows — never the only way to see it. Slack pages on transitions; the dashboard answers "what
is the state right now" (SIT run state with per-repo jobs, promotion lock, stuck PRs, promotion lag, git-health / cron
liveness). New watcher alert classes MUST land with a paired dashboard state element — review gate for alerting changes.

## Division of surfaces

| Surface              | Home                           | Question it answers                                                                     |
| -------------------- | ------------------------------ | --------------------------------------------------------------------------------------- |
| CI/CD repo dashboard | deployment-ui + deployment-api | Where is each repo in LDR→staging→SIT→main→image? SHA history, QG status, promotion PRs |
| Fleet git-health     | agent-orchestrator dashboard   | Which host/slot/repo worktrees are dirty/behind/diverged vs LDR? Are the crons alive?   |
| Slack                | alerting only                  | Something FAILED / RECOVERED — actionable transitions, no steady-state monitoring       |

## CI dashboard (deployment-ui `/repos` "Repos CI" + deployment-api `/api/repo-ci/*`)

**Endpoints**: `GET /api/repo-ci/overview` (fleet matrix — one response drives the page) +
`GET /api/repo-ci/{repo}/detail` (per-branch SHA history with `quality-gates-v2` conclusions, PR cards, SIT, image).
Code: `deployment_api/routes/repo_ci.py` + `_repo_ci_{types,stuck,manifest,github}.py`; UI
`deployment-ui/src/pages/RepoCi.tsx` + `src/lib/repoCi.ts`.

**Data architecture (HYBRID — operator decision 2026-06-10)**:

- **GitHub API live** (aiohttp; `GH_PAT` from Secret Manager via `get_secret_client()`; per-URL TTL cache 90 s; honest
  rate-limit → 503 + `retry_after`, never silent-stale): branch heads, 3-way compare (content delta = changed-file
  count, never squash-skewed commit counts), commit history, check runs, open PRs (+ per-PR `mergeable_state`).
- **workspace-manifest.json** (PM `main` via contents API, TTL 120 s) through ONE accessor —
  `_repo_ci_manifest.ManifestView`: repo registry, `ci_status` (9-state), `staging_status.breaking_pending` + lock,
  `deployed_versions`. **`ManifestView.ci_status_for` is THE Firestore swap point** for
  `ci_status_firestore_side_store_2026_06_10.md` Phase 2 — no other consumer changes at cutover.
- **Cloud builds** (image-level deploy signal v1): reuses `_cloud_builds_*` plumbing; `image_stale` = main HEAD sha ≠
  last successful build sha; honest-unknown (None) when build data unavailable; AWS/CodeBuild parity tracked in the
  sub-plan (cloud-toggle).

**Stuck-PR classification** (`_repo_ci_stuck.py`) is a PORT of `scripts/repo-management/ci_failure_watcher.py`
signatures — the watcher remains the SSOT; never fork semantics. Closed set: `conflicting` (CONFLICTING/DIRTY wall),
`failing_check`, `skip_ci_jammed` ([skip ci] head + v2 absent), `v2_never_reported` (auto-recoverable),
`automerge_stuck`. The overview carries a fleet-wide `stuck_prs[]` triage queue + `stuck_in_sit[]`.

**Live SIT-run panel** (alert-parity): `sit_last_run {url,status,conclusion,age_min,jobs[]}` from the newest
`cascade-qg-ordering` run's jobs API — which repos were in the last SIT/cascade run, pass/fail/in-progress, always
visible.

**Failure semantics**: shard-level isolation — a per-repo GitHub error degrades that row/field (logged), never the
response; ONLY rate-limit (503) propagates. Checks-API 403 (PAT missing `Checks: read` — credential ask filed
2026-06-10) degrades v2 conclusions to unknown.

**Tests**: deployment-api `tests/unit/test_repo_ci_{stuck,manifest,routes}.py` (mock fixtures cover EVERY stuck class —
pinned against the UI contract); deployment-ui `src/lib/repoCi.test.ts` + playwright `tests/smoke/repos-tab.spec.ts` +
`tests/e2e/repos-stuck-panel.spec.ts` (regression: all five stuck classes + stuck-in-SIT + SIT-run jobs).

## Fleet git-health (agent-orchestrator) — SHIPPED 2026-06-10

Extends the existing per-slot ingestion (`POST/GET /api/slots/{id}/git-status`, 5-min `slot-git-status-report.sh` cron)
with a fleet surface (`fleet_git_health_orchestrator_2026_06_10.md`, agent-orchestrator@0ab7c84):

- **Backend** `GET /api/fleet/git-health?scope=fleet|local` (`server/server.py`) — aggregates every slot's stored
  `SlotGitStatus` into hosts → slots → repos; `scope=fleet` fans out to registered VMs via the existing
  `/api/vms/<id>/*` proxy (each VM answers `scope=local`); honest per-VM `vm_errors[]` on a proxy failure (never a
  silent gap). Per-slot `reporter_stale` (reported_at > 10 min) + `ff_cron_stale` (ff_pull_last_run > 15 min, **only
  when attested** — un-attested = honest-unknown, never falsely "dead") + per-repo `drift_violation` (Path-B invariant:
  state `ahead`/`diverged` vs LDR; rolled up to `drift_violations[]`). Summary block + 14 pytest
  (`tests/test_fleet_git_health.py`).
- **Cron-liveness ingestion**: `GitStatusPostRequest.ff_pull_last_run`/`ff_pull_last_result` (optional,
  backward-compat); `slot-cron-ff-pull.sh` writes a host-global `${TMPDIR}/slot-cron-ff-pull.result.json` each sweep
  (per-repo ok/skip:dirty/conflict/fail tokens, worst-of, atomic tmp+mv); `slot-git-status-report.sh` reads it + posts
  it.
- **Orchestrator dashboard** `/fleet-git` page (`dashboard/src/FleetGit.tsx`) — summary chips, per-host slot rows with
  worst-first badges (reporter-dead / ff-pull-dead / N drift / N dirty / N behind), expandable per-repo detail.
- **Single-pane (operator decision v2)**: deployment-api `GET /api/repo-ci/fleet-git-health` (`_repo_ci_fleet.py`,
  deployment-api@2b6b424) proxies the orchestrator endpoint server-side (SM token `ORCHESTRATOR_API_TOKEN`; honest
  degradation `available=False`+reason+`orchestrator_url` deep-link when unreachable/untokened) → deployment-ui `/fleet`
  Fleet Git landing tab (deployment-ui@8a9d1bd). The orchestrator dashboard keeps its own `/fleet-git` page for
  worker-ops use.

## Click-through to the existing UIs (operator add 2026-06-10)

Every status atom is a deep-link to the authoritative existing UI — never a dead-end label (the monitor is roll-up/
triage; detail lives in GitHub + the AO UI). **GitHub-authoritative atoms → GitHub**: SHA → `…/commit/<sha>`,
`quality-gates-v2`/v2 conclusion ("feature green") → `…/commit/<sha>/checks`, PR → `…/pull/<n>`, branch →
`…/tree/<branch>` (`deployment-ui/src/lib/repoCi.ts` `githubCommitUrl`/`githubChecksUrl`/`githubBranchUrl`,
vitest-covered). **Fleet/ git-health atoms → the agent-orchestrator UI**: dirty/behind/diverged/reporter/ff-cron → the
orchestrator Fleet Git-Health page (the Fleet Git tab's "Open in Agent-Orchestrator" deep-link). A status chip with no
click-through is review-blocking for these surfaces.

## Cross-links (P2)

Repo row ⇄ fleet git-health filtered by repo ("is this repo in anyone's worktree"); repo detail deep-links the EXISTING
data-status / deployments-monitor / VM-logs tabs — never redo those surfaces. (Repo-detail → existing-tab cross-links
are the remaining P2 in `ci_dashboard_deployment_ui_2026_06_10.md`.)
