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
  - 'operator direction 2026-06-10 (parent: plans/active/monitoring_control_plane_master_2026_06_10.md) — "crumbs from
    each machine — my hashes, the AWS VMs — dirty local worktrees vs the LDR remote, on the agent-orchestrator website"'
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

- [x] ✅ [CODE] P1. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (`get_fleet_git_health` + `_build_local_git_health` +
      `_group_slots_by_host` + `_summarise_git_health`; `scope=fleet` fans out to registered VMs via the existing proxy,
      `scope=local` is the per-VM leaf). Was: `GET /api/fleet/git-health` — aggregate every slot's stored
      `SlotGitStatus` across ALL hosts (central + proxied VMs via the existing `/api/vms/<vm_id>/*` pattern): grouped by
      host → slot → repos, each repo with state, dirty-file count, ahead/behind, `not_clean_since`, unpushed plans.
      Per-slot `reporter_stale: reported_at older than 10 min` so a dead reporter cron is a first-class state, not a
      silent gap. Summary block: counts per state + drift_violations roll-up.
- [x] ✅ [CODE] P1. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (`_DRIFT_VIOLATION_STATES = {ahead, diverged}` per
      repo; rolled up to `FleetGitHealthResponse.drift_violations[]` with host/slot/repo/state/ahead/behind). Was:
      **Drift invariant surface** — per repo derive `drift_violation` when state is `diverged`/`ahead` vs LDR (Path-B
      `slot_drift_check.py` invariant: slot HEAD ancestor-or-equal of LDR); fleet `drift_violations[]` list.
- [x] ✅ [CODE] P2. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (`GitStatusPostRequest.ff_pull_last_run/result`
      optional; ORM cols `git_status_ff_pull_last_run/result` + bootstrap migration; `set_slot_git_status` overwrites
      only when provided; `ff_cron_stale` derived only when attested — honest-unknown otherwise). Was: **Cron-liveness
      ingestion** — extend `GitStatusPostRequest` (optional, backward-compatible) so the reporter can attest the FF-pull
      cron; expose `ff_cron_stale` per slot. Pairs with the Phase 3 reporter change.
- [x] ✅ [TEST] P1. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (tests/test_fleet_git_health.py, 14 tests: drift
      ahead/diverged/behind, reporter_stale, ff_cron_stale attested/recent/unknown, host grouping, summary roll-up +
      drift_violations[], GitStatusPostRequest old+new shapes; QG green 428 passed). Was: pytest fleet aggregation +
      stale/drift derivation + backward-compat POST.

## Phase 2 — dashboard fleet page (repo: agent-orchestrator)

- [x] ✅ [CODE] P1. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (`dashboard/src/FleetGit.tsx` — `/fleet-git` route in
      Router + "Fleet Git-Health →" link on Landing; summary chips strip with red alert chips for dirty/drift/
      reporter-dead/ff-pull-dead; per-host Panel → per-slot rows with worst-first badges (reporter dead / ff-pull dead /
      N drift / N dirty / N behind) → expandable per-repo detail; `vm_errors[]` unreachable-VM panel; 30s poll). Was:
      `dashboard/src/` new "Fleet Git" view: hosts/slots matrix, summary strip, red badges for `drift_violation`,
      `reporter_stale`, `ff_cron_stale`.
- [x] ✅ [TEST] P1. DONE 2026-06-10 — agent-orchestrator@0ab7c84 (`tsc --noEmit` exit 0 + `vite build` exit 0 +
      prettier; pure mappers `repoStateColor`/`slotBadges`/`summaryChips` exported test-ready). **vitest NOT run — the
      orchestrator dashboard has NO vitest/eslint harness installed** (only tsc + prettier + build in package.json);
      adding a vitest harness is a separate infra unit → see Phase 4 deferred todo below. tsc strict + build are the
      repo's actual gate and both pass.

## Phase 3 — reporter additions (repo: unified-trading-pm)

- [x] ✅ [SCRIPT] P2. DONE 2026-06-10 — unified-trading-pm (this commit; scripts/dev/) (`slot-cron-ff-pull.sh` writes a
      host-global `${TMPDIR:-/tmp}/slot-cron-ff-pull.result.json` each sweep — `_ff_record` per-repo tokens
      (ok/skip:dirty/conflict/ fail) aggregated worst-of, atomic tmp+mv via `_write_ff_result` in BOTH single-slot +
      all-slots paths; `slot-git-status-report.sh` reads it + adds `ff_pull_last_run`/`ff_pull_last_result` to the POST
      only when present — payload stays backward-compatible). Smoke-verified: dry-run sweep wrote
      `{"ff_pull_last_run":...,     "ff_pull_last_result":"skip:dirty"}`, reporter round-trip emits the enriched
      payload. `bash -n` clean both.
- [ ] [VERIFY] P2. **PARTIAL** — laptop single-slot smoke done 2026-06-10 (result write + reporter read round-trip
      verified). Remaining: one full `*/5` cron cycle on the laptop + one AWS VM with the orchestrator live — fleet page
      shows both hosts, states match `git status` ground truth on 3 spot-checked repos, killing the reporter cron flips
      `reporter_stale` within 15 min, killing the FF-pull cron flips `ff_cron_stale`. (Needs the orchestrator running +
      a second host; do on the live orchestrator VM.)

## Phase 4 — ship + docs

- [x] ✅ [DOCS] P2. DONE 2026-06-10 — `codex/04-architecture/agent-orchestrator-overview.md` § "Fleet git-health page
      (shipped 2026-06-10)" (endpoint + scope fan-out + reporter_stale/ff_cron_stale/drift derivations + vm_errors +
      `/fleet-git` page + deployment-ui single-pane mirror) + `codex/03-observability/monitoring-control-plane.md` §
      "Fleet git-health (agent-orchestrator) — SHIPPED" + § "Click-through to the existing UIs" (operator click-through
      rule: GitHub + AO deep-links).
- [ ] [TEST] P3. **NICE-TO-HAVE — add a vitest harness to the orchestrator dashboard** (provenance: slot-3 2026-06-10
      fleet-git-health ship). The `agent-orchestrator/dashboard` repo has NO vitest/eslint installed (only
      `tsc`+`vite     build`+prettier), so the FleetGit pure mappers (`repoStateColor`/`slotBadges`/`summaryChips`,
      written test-ready) have tsc+build coverage but no unit tests. Adding vitest (+ jsdom-free for pure fns) is its
      own infra unit; do it once and backfill specs for FleetGit + any future mapper. Repo: agent-orchestrator
      (dashboard).

## Success criteria

- One page answers "which worktrees anywhere in the fleet are dirty/behind/diverged vs LDR, and are the reporter +
  FF-pull crons alive" across laptops + VMs.
- Dead reporter / dead FF-pull cron is itself a visible red state (no silent gaps).
- All new endpoints behind `AUTHED_DEPS`; pytest + vitest + tsc green; agent-orchestrator QG green.

## Out of scope (named successors)

- Cross-links to the CI dashboard (master plan P2 extra).
- Any write/remediation action (auto-commit, kill-cron) — the existing sync-nudge stays the only actuation.
