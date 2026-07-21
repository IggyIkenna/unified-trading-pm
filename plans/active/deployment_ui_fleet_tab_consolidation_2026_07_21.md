---
doc_type: plan
title: deployment-ui — Fleet tab consolidation (strip to git-health, merge orphans + VM census into Deployments)
summary: >-
  The Fleet tab (/fleet) is one overloaded page stacking five sections built before the dedicated Deployments tab
  existed. Audit 2026-07-21 classified every section: the VM-census embed and FleetInfra (infra tiles + orchestrator/
  slots panel) duplicate or are superseded, the reconciliation cards are largely redundant, and the Stopped & orphaned
  VMs (idle disk spend) view is genuinely useful but only its VISIBILITY exists on Deployments — the reap/delete
  actions, verdict/grace classification, stopped-age, and idle-spend rollup cards do not. Plan: remove FleetInfra
  entirely (AO owns orchestrator health), remove the census embed + reconciliation cards, MERGE the orphan idle-spend
  capability and the standalone /vm-deployments history into the Deployments tab (retiring /vm-deployments), and leave
  Fleet as ONLY fleet git health + slot-wise dirty repos.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, deployment-api]
scope: [engineer]
tags: [deployment-ui, fleet, consolidation, cleanup, observability, idle-spend]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
  - deployment_ui_vm_log_viewer_2026_07_20.md
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: ui_developer
drift_direction: advance-code
sequential: true
depends_on:
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator audit session 2026-07-21 (Fleet-tab audit + consolidation decisions)
---

# deployment-ui — Fleet tab consolidation

> **🟢 Activated gated (operator 2026-07-21)** — `status: active` + `gate_on_depends: true`. Authored in the tabs-3
> worktree per operator instruction (keep new work off the root repo where other agents are active).
>
> **⚠️ Same-file coordination — `Deployments.tsx`.** This plan edits `src/pages/Deployments.tsx` (merging orphan
> actions/cards + census history) and so does
> [`deployment_ui_date_range_filter_and_search_2026_07_20.md`](deployment_ui_date_range_filter_and_search_2026_07_20.md)
> (filters + shared-primitive extraction). `gate_on_depends: true` now **machine-holds** every task in this plan until
> that plan's tasks all complete — the backlog enforces the ordering, so no same-file collision (multi-agent safety) and
> no reliance on manual activation timing. (The shared-primitive extraction has already landed at
> `deployment-ui@1cf191b`; the gate additionally waits on the date-range plan's remaining tail before this plan
> dispatches.)

## Context — Fleet-tab audit findings (2026-07-21, read-only)

Fleet (`/fleet` → `CockpitFleet` → `FleetTab` in `Cockpit.tsx`) is ONE page stacking five sections. Locate each by its
component/section name — grep, do NOT trust line numbers:

| #   | Section                                                              | where                                | Verdict                                                            |
| --- | -------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------ |
| a   | Reconciliation cards (Accounted / Unknown / Expected-missing)        | inline in `FleetTab` (`Cockpit.tsx`) | REMOVE (redundant; keep only the "expected-missing" idea if cheap) |
| b   | VM census embed (compact `VmDeployments`)                            | `VmDeployments.tsx`                  | REMOVE embed; merge unique bits to Deployments                     |
| c   | Stopped & orphaned VMs (idle disk spend)                             | `FleetOrphans.tsx`                   | **MERGE into Deployments** (actions/cards/verdict missing there)   |
| d   | Infra & orchestrator health (tiles + VM census + orchestrator/slots) | `FleetInfra.tsx`                     | **REMOVE ENTIRELY** (operator: AO owns orchestrator health)        |
| e   | Fleet git health + slot-wise dirty repos                             | `FleetGit.tsx`                       | **KEEP** — becomes the entire Fleet tab                            |

Key audit facts driving the merges:

- **Deployments already SEES idle spend** — `DISK`/`STATIC_IP` orphan rows (kind filter "disk (orphaned)" / "static IP
  (orphaned)" in `Deployments.tsx`), per-row `LeakedBadge` ("N leaked ·
  ~$X/mo"), estate-wide `StrandedCostBadge`, a
  `stopped` status filter, and Resources sortable by leaked $/mo. **But it
  lacks** FleetOrphans' (1) reap/delete ACTIONS (`VmControls` is pause/resume/stop/restart only; FleetOrphans has the
  dry-run bulk `reapOrphans` handler + a per-instance delete-with-boot-disk handler), (2) the reap-verdict/grace
  classification helper (grep `FleetOrphans.tsx` for the verdict/grace logic), (3) the idle-spend rollup cards (Stopped
  VMs · Reapable · Idle disk $/mo · Reclaimable
  $/mo) + stopped-age, and (4) it defaults `status=running` so orphans
  are hidden until you switch the filter.
- **Idle-disk cost is an ESTIMATE on BOTH surfaces** — FleetOrphans' `monthly_disk_usd` is "asia-northeast1 list rate ×
  GB" (grep the api client for the `monthly_disk_usd` estimator), not real billing; Deployments' leaked-$/mo is the same
  class of estimate. Real-billing idle spend (WS-1-style) is a possible later enhancement, NOT in scope here — preserve
  the estimate for parity.
- **FleetOrphans is self-contained** — depends only on `/api/fleet/orphans`, `/api/fleet/reap`,
  `DELETE /api/fleet/instances/{name}`. But the reap-verdict / grace / stopped-age / disk-rollup fields do NOT exist on
  the `DeploymentItem` type (in `deploymentApi.ts`) — merging them needs either Deployments consuming
  `/api/fleet/orphans` or new inventory fields (backend todo below).
- **`/vm-deployments` is a SEPARATE canonical tab** (its route in `App.tsx` + nav entry in `NavMenu.tsx`), not legacy —
  Fleet only embeds a compact copy. Operator decision: consolidate it into Deployments and retire it. Its unique content
  vs Deployments: the archive/history table (Outcome, Duration, Rows Captured, Completed, archive log links) +
  `rows_error` (Errors) + throughput (`rows_in`/`events_emitted`). The archive **log links overlap WS-4** (the run.log
  viewer) — do NOT build a second log renderer; defer log display to WS-4's viewer.
- **KEEP-set correction** — the slot-wise dirty-repo data is populated by **`slot-git-status-report.sh`** (repo classify
  → POST AO `/api/slots/{N}/git-status`), NOT `slot-cron-ff-pull.sh` (which populates the ff-pull _liveness_ fields).
  Both are cron-driven and land in the same `/api/fleet/git-health` → `/api/repo-ci/fleet-git-health` surface
  `FleetGit.tsx` reads. FleetGit is unaffected by removing the other sections.
- **KEEP-set enhancement (operator 2026-07-21)** — FleetGit renders the derived `reporter_stale` "reporter dead" boolean
  but NOT the actual snapshot time. The `reported_at` timestamp is already stored server-side (the
  `SlotRow.git_status_reported_at` field, posted as `reported_at`) AND already on the wire type (grep `client.ts` for
  `reported_at`) — it's simply not rendered. Surfacing it is a pure UI add (see todo). Context: each host's reporter
  POSTs to ITS OWN local orchestrator; a laptop running a local standalone AO instance shows only its own slots (the "no
  `ORCHESTRATOR_VM_ID` ⇒ standalone/isolated" rule, `is_standalone()` in `vms.py`), so the snapshot time also tells the
  operator which local instance's clock produced the row.

## Decisions (operator, 2026-07-21)

1. **FleetInfra — remove entirely** (tiles + VM-census panel + orchestrator/slots panel). AO's own dashboard owns
   slots/backlog/watchdog health; the CI tile is redundant with `/repo-ci`; the git tile is redundant with FleetGit.
2. **/vm-deployments — consolidate into Deployments** and retire the standalone tab (fold history + `rows_error` +
   throughput; defer log links to WS-4).
3. **FleetOrphans — merge into Deployments**, not remove: bring the rollup cards, verdict/stopped-age, and the
   reap/delete actions over so idle spend is actionable there.
4. **Fleet end-state = ONLY fleet git health + slot-wise dirty repos** (the FleetGit section).

## Todos

- [x] [BACKEND] P0. ✅ **Orphan/idle data on the Deployments surface** — deployment-api@aa6dbff. Added
      `reap_verdict`/`grace_hours`/`stopped_age_hours`/`monthly_disk_usd` to `DeploymentItem`
      (`deployments_inventory.py`), populated inside `build_inventory` via a name-joined
      `build_orphan_inventory(vm_details_by_name, disk_details, now, DEFAULT_GRACE_HOURS)` call — the SAME orphans SSOT
      `/api/fleet/orphans` uses (`_fleet_inventory.py`), computed once per census cycle from data already fetched (no
      new GCE call, no second cost estimator). Fields populate only for VM rows currently STOPPED/SUSPENDED/TERMINATED
      (the orphan candidate set); a running VM honestly reports all four as `None`. Added `DEFAULT_GRACE_HOURS = 24.0`
      to `_fleet_inventory.py` for this new call site (existing `/orphans`+`/reap` endpoint defaults left untouched —
      unrelated blast radius). 2 new unit tests (`test_build_inventory_surfaces_orphan_reap_verdict_on_stopped_vm`,
      `test_build_inventory_running_vm_has_no_orphan_fields`) plus the existing 105-test file all green; full
      `quality-gates.sh` clean (basedpyright error count unchanged vs pre-edit baseline — verified by diffing
      before/after). Next: the UI-facing todos below (rollup cards, verdict badges, reap/ delete actions) consume these
      new fields. (repo: deployment-api)
- [x] [UI] P1. ✅ **Idle-spend rollup cards on Deployments** — deployment-ui@d12843e. Ported the four FleetOrphans
      rollup cards (Stopped VMs · Reapable · Idle disk $/mo · Reclaimable $/mo) verbatim (same markup/formatting) into
      `Deployments.tsx`, right below `StrandedCostBadge` in the page header. Fetches `GET /api/fleet/orphans`
      independently of the main inventory load (own `useVisibilityPausedInterval` cadence, same as the rest of the page)
      — honest `"—"` placeholders on fetch failure, never stale/fabricated data. tsc/ESLint clean; 2 new Vitest tests
      (cards render the rollup figures; cards degrade to `"—"` on fetch failure) + full existing suite green (1042
      tests); full `quality-gates.sh` (base-ui.sh v2.0) green. Playwright verification is bundled into the plan's
      consolidated `[REVIEW] P1. Playwright specs` todo below (covers this + the remaining UI todos together, per the
      plan's own structure — not a separate spec per card). (repo: deployment-ui)
- [ ] [UI] P1. **Reap-verdict + stopped-age on orphan rows** — surface the verdict badge (reapable / within-grace /
      retained / no-stop-time) and stopped-age on the relevant Deployments rows.
- [ ] [UI] P1. **Reap/delete actions on Deployments** — port FleetOrphans' dry-run-first bulk reap (`reapOrphans` →
      `/api/fleet/reap`) and per-instance delete-with-boot-disk (`DELETE /api/fleet/instances/{name}`), keeping the
      confirm-dialog + dry-run-preview safety pattern. Destructive actions stay behind explicit confirm.
- [ ] [UI] P2. **Idle-spend discoverability** — since Deployments defaults `status=running`, add a quick entry point (an
      "idle spend" filter/chip or a rollup-card click that applies `status=stopped`/orphan filters) so idle resources
      aren't hidden.
- [ ] [UI] P1. **Fold /vm-deployments history into Deployments** — bring the archive/history table (Outcome, Duration,
      Rows Captured, Completed) into the Deployments detail view / a history section. For the archive **log links**,
      link to WS-4's run.log viewer (`deployment_ui_vm_log_viewer_2026_07_20.md`) — do NOT build a second log renderer.
- [ ] [UI] P1. **Cheap merged columns** — add `rows_error` (Errors) and throughput (`rows_in`/`events_emitted`) to
      Deployments where useful; the data already exists on `DeploymentItem`, no backend work.
- [ ] [UI] P1. **Retire /vm-deployments** — remove the `/vm-deployments` route (`App.tsx`) + its nav entry
      (`NavMenu.tsx`) once its content is folded in; add a redirect `/vm-deployments → /deployments`.
- [ ] [UI] P1. **Remove FleetInfra** — delete the FleetInfra section from `FleetTab` and its imports; remove any nav/
      route pointing at it. Confirm nothing else depends on its endpoints (`/api/fleet/vm-census`,
      `/api/fleet/infra-vm-health`) in the UI; leave the backend endpoints intact (out of scope).
- [ ] [UI] P1. **Remove the VM-census embed + reconciliation cards** from `FleetTab` (in `Cockpit.tsx`) — after the
      merges above land. Optionally preserve the "expected-missing" (registered-but-not-running) count as a small
      Deployments summary if cheap; otherwise drop.
- [ ] [UI] P1. **Fleet = FleetGit only** — `FleetTab` renders only `FleetGitContent`; update the page title + the Fleet
      nav description in `NavMenu.tsx` ("Census · orphans · git · infra" → "git health · dirty repos"). Verify FleetGit
      renders standalone (reads only `/api/repo-ci/fleet-git-health`).
- [ ] [UI] P1. **Show the snapshot timestamp per slot in FleetGit** — render the `reported_at` field (already on the
      wire type in `client.ts`; already stored server-side as `SlotRow.git_status_reported_at`) next to each slot in
      `FleetGit.tsx`, so the operator can see WHEN the status snapshot was taken, not just the derived `reporter_stale`
      "reporter dead" boolean. Show both an absolute time and a relative age (e.g. "3m ago") so freshness reads at a
      glance and pairs with the existing stale badge. Pure UI — NO backend change (the timestamp already reaches the
      frontend).
- [ ] [REVIEW] P1. **Playwright specs** — new: Deployments idle-spend cards + reap-confirm/dry-run flow + folded
      history; Fleet shows ONLY git health + dirty repos + the per-slot snapshot timestamp; `/vm-deployments` redirects
      to `/deployments`. Keep existing Deployments + Fleet regression specs green. `pw:L2 ✓` + cited specs. No tick
      without them.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across deployment-ui + deployment-api if
      touched) + flip todos same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the consolidated contract (Deployments owns VM inventory + idle
      spend + reap actions + history; Fleet = git-health-only; `/vm-deployments` retired) in
      `codex/05-infrastructure/deployment-observability.md`.

## Success criteria

- Fleet tab shows ONLY fleet git health + slot-wise dirty repos; every deployment/VM/orphan/infra section is gone.
- The idle-disk-spend capability (rollup cards, verdict, stopped-age, dry-run reap + delete) is fully usable from the
  Deployments tab, and idle resources are discoverable despite the default running filter.
- `/vm-deployments` is retired; its history + Errors + throughput live on Deployments; a redirect preserves old links.
- No second log renderer built — archive log links defer to WS-4's run.log viewer.
- No same-file collision with the date-range plan (this plan executed after it).
- All existing Deployments + Fleet Playwright regressions stay green.

## Progress Log

- **2026-07-21** — Authored from the operator's Fleet-tab audit session (two parallel read-only audits: Fleet full
  column inventory + Deployments idle-resource cross-check). Operator decisions: remove FleetInfra entirely (AO owns
  orchestrator health), consolidate `/vm-deployments` into Deployments and retire it, merge FleetOrphans' idle-spend
  capability (cards + verdict + reap/delete actions) into Deployments rather than removing it, leave Fleet as
  git-health-only. Key finding: Deployments already SEES idle spend (orphan rows + leaked/stranded badges) but lacks the
  ACTIONS and rollups — so the orphan view is a merge, not a delete. Both surfaces' idle cost is a list-rate estimate,
  not real billing (real-billing idle spend noted as a possible future enhancement, out of scope). Corrected the
  keep-set attribution: dirty-repo data comes from `slot-git-status-report.sh`, not `slot-cron-ff-pull.sh`. Flagged the
  `Deployments.tsx` same-file collision with the date-range plan → `depends_on` + activate-after ordering. Kept `draft`.
- **2026-07-21 (continued)** — Operator clarified the multi-host git-health model (each host reports to its own local AO
  instance; central proxies registered fleet VMs by private IP; laptops are standalone/isolated — the extra IP the
  operator saw was their own locally-run AO backend). Added a keep-set enhancement todo: surface the per-slot
  `reported_at` snapshot timestamp in FleetGit (pure UI — data already stored + on the wire type, just unrendered).

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the consolidated
  Deployments-owns-everything / Fleet-is-git-health-only contract.
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec) for every `[UI]` todo.
- `codex/05-infrastructure/per-tab-worktrees.md` — the slot/dirty-repo model behind the FleetGit keep-set
  (`slot-git-status-report.sh` + `slot-cron-ff-pull.sh` → AO `/api/fleet/git-health`).
