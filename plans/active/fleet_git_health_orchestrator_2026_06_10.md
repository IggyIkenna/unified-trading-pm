---
title: "Fleet git-health surface — hosts×slots×repos dirty/drift matrix + cron liveness on the orchestrator dashboard"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-10
source:
  - operator direction 2026-06-10 (parent: plans/active/monitoring_control_plane_master_2026_06_10.md) — "crumbs from
    each machine — my hashes, the AWS VMs — dirty local worktrees vs the LDR remote, on the agent-orchestrator website"
related_plans:
  - plans/active/monitoring_control_plane_master_2026_06_10.md
locked_by: live-defi-rollout
locked_since: 2026-06-10
---

# Fleet git-health (agent-orchestrator)

## Scope

**Repo: `agent-orchestrator`** (+ a small reporter addition in `unified-trading-pm/scripts/dev/`). The per-slot
ingestion already exists (`POST/GET /api/slots/{id}/git-status`, `SlotGitStatus`/`RepoStatus` models, per-slot
`GitStatusBadge` in `dashboard/src/layout.tsx:37-186`, reporter `slot-git-status-report.sh` on a 5-min cron). This plan
adds the FLEET view: every host (operator laptops + AWS/GCP VMs) × slot × repo in one page, plus cron-liveness so a dead
reporter/FF-pull is itself visible. Read-only; no new auth layer (`AUTHED_DEPS` on new endpoints).

**Cold-start context for workers**: read `SUB_AGENT_MANDATORY_RULES.md` first. Key files: `server/server.py:1972-2020`
(existing git-status endpoints), `server/models.py:350-390` (RepoStatus/SlotGitStatus/ RepoGitState),
`unified-trading-pm/scripts/dev/slot-git-status-report.sh` (reporter; posts per-slot JSON every 5 min, FF-starvation
watchdog at lines 322-385), `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` (FF-pull cron),
`scripts/cicd/slot_drift_check.py` (Path-B drift invariant: slot HEAD ancestor-or-equal of origin/live-defi-rollout).
Orchestrator dashboard is Vite+React TS strict, NOT in the playwright-gate repo set → tests are pytest (server) +
vitest/tsc (dashboard).

## Phase 1 — backend fleet aggregation (repo: agent-orchestrator)

- [ ] [CODE] P1. `GET /api/fleet/git-health` — aggregate every slot's stored `SlotGitStatus` across ALL hosts (central +
      proxied VMs via the existing `/api/vms/<vm_id>/*` pattern): grouped by host → slot → repos, each repo with state
      (`dirty|ahead|behind|diverged|clean|...`), dirty-file count, ahead/behind, `not_clean_since`, unpushed plans.
      Include per-slot `reporter_stale: reported_at older than 10 min` (the existing stale threshold) so a dead reporter
      cron is a first-class state, not a silent gap. Summary block: counts per state, worst offenders (oldest
      `not_clean_since`, biggest behind).
- [ ] [CODE] P1. **Drift invariant surface** — per repo, derive `drift_violation: true` when state is `diverged` or
      `ahead` vs `origin/live-defi-rollout` (the Path-B invariant from `slot_drift_check.py`: slot HEAD must be
      ancestor-or-equal of LDR); roll up to a fleet `drift_violations[]` list.
- [ ] [CODE] P2. **Cron-liveness ingestion** — extend `GitStatusPostRequest` (optional fields, backward-compatible) with
      `ff_pull_last_run`/`ff_pull_last_result` so the reporter can attest the FF-pull cron; expose in the fleet payload
      (`ff_cron_stale` per slot). Pair with the reporter change in Phase 3.
- [ ] [TEST] P1. pytest: fleet aggregation over multi-slot/multi-host fixtures (SQLite), stale-reporter derivation,
      drift-violation derivation, backward-compat POST without the new optional fields.

## Phase 2 — dashboard fleet page (repo: agent-orchestrator)

- [ ] [CODE] P1. `dashboard/src/` new "Fleet Git" view (nav alongside existing panels): hosts×slots matrix, each cell
      expandable to the repo table (reuse `GitStatusDetails` row rendering); summary strip (dirty / behind / diverged /
      stale-reporter counts); filters (host, state, repo); red badges for `drift_violation`, `reporter_stale`,
      `ff_cron_stale`, and `not_clean_since` > 60 min (existing dirty-red threshold).
- [ ] [TEST] P1. vitest for the grouping/derivation mappers + `tsc --noEmit` strict + zero ESLint warnings.

## Phase 3 — reporter additions (repo: unified-trading-pm)

- [ ] [SCRIPT] P2. `slot-git-status-report.sh`: include `ff_pull_last_run`/`ff_pull_last_result` in the POST payload
      (read from a result file `slot-cron-ff-pull.sh` writes per run — add that write too, atomic tmp+mv). Keep the
      payload backward-compatible (server accepts both shapes).
- [ ] [VERIFY] P2. One full cron cycle on the laptop + one AWS VM: fleet page shows both hosts, states match
      `git status` ground truth on 3 spot-checked repos, killing the reporter cron flips `reporter_stale` within 15 min.

## Phase 4 — ship + docs

- [ ] [DOCS] P2. `codex/04-architecture/agent-orchestrator-overview.md` § new "Fleet git-health page"; contribute the
      fleet-surface section to `codex/03-observability/monitoring-control-plane.md` (master obligation).

## Success criteria

- One page answers "which worktrees anywhere in the fleet are dirty/behind/diverged vs LDR, and are the reporter +
  FF-pull crons alive" across laptops + VMs.
- Dead reporter / dead FF-pull cron is itself a visible red state (no silent gaps).
- All new endpoints behind `AUTHED_DEPS`; pytest + vitest + tsc green; agent-orchestrator QG green.

## Out of scope (named successors)

- Cross-links to the CI dashboard (master plan P2 extra).
- Any write/remediation action (auto-commit, kill-cron) — the existing sync-nudge stays the only actuation.
