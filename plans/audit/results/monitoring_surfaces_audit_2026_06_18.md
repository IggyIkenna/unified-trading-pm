---
title: Monitoring Surfaces Audit — agent-orchestrator dashboard + deployment-ui monitoring pane
name: monitoring_surfaces_audit_2026_06_18
type: audit-result
epic: infrastructure_master
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
created: 2026-06-18
date: 2026-06-18
author: ikenna [autonomous audit — Opus background agents]
auditor: ikennaigboaka
status: in-progress
assigned_vm: planning
source:
  - agent-orchestrator/dashboard/src/{App,layout,api,types}.tsx
  - agent-orchestrator/server/routes/*.py
  - deployment-ui/src/{pages,components,api,hooks}/
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/04-architecture/runtime-deployment-topology.md
---

# Monitoring Surfaces Audit (Class 2 of 2)

> **Status: IN PROGRESS** — skeleton captures the operator's full requirement set (2026-06-18); findings are being
> filled from two background Opus audit agents (agent-orchestrator dashboard + deployment-ui monitoring pane). Update as
> findings land, then derive the wrapper sub-plan(s).

## Division of surfaces (the standing contract — operator reaffirmed 2026-06-18)

- **agent-orchestrator dashboard** = everything about AGENTS + the orchestrator (the operator's & Ikenna's preferred
  lens for agent/orchestrator state).
- **deployment-ui monitoring pane** = everything about CI/CD + codebase/repos + fleet (VMs) + container IMAGES.
- An alert (Class-1 audit) is an error pointer you **click through** to the relevant surface for full detail.

## Operator requirements (2026-06-18 design session — verbatim intent, do NOT drop any)

### A. agent-orchestrator dashboard (operator: "add more detail — it's not that much")

1. **Agents view — add the missing types.** Today only `main` + `review` show. Must also show `escalate`,
   `conflict-resolver`, `plan-health`, `plan-reconciler`, `monitor` — **current AND past**. Either extend the agents
   view or add **ONE new separate tab** (workers already have their own fleet tab — that's fine, leave it). NOTE: the
   just-finished `orchestrator_agent_type_oversight_coverage` branch now registers these as AgentRows with
   `agent_kind` + `lifecycle` and surfaces them on `/api/agents` — the DATA exists; this is rendering it.
2. **Activity feed — denoise + see history + filter.** ~90% of what shows is repeating alerts (useless); there is NO way
   to see activities older than the last ~50. → add **filtering** + **pagination** + reduce the repeat noise.
3. **Conditions tab — collapsible.** Show top ~5 (or next 5), collapse/expand the rest.
4. **Human↔agent messaging layer.** The ~1-min poll cadence is a concern; the operator wants a better way to
   communicate with agents. Mechanism is OPEN — audit current path + propose options.

### B. deployment-ui monitoring pane (operator: "most of the work is on the deployment-ui side")

5. Surface ALL of **CI/CD status + codebase/repo health + fleet/VM state + container images** so an alert → click → full
   picture. This is the larger rework.

## Findings — agent-orchestrator dashboard — COMPLETE (Opus agent, 2026-06-18)

**Foundation:** `agent_kind`/`lifecycle` plumbing is COMPLETE end-to-end (enums `_types.py:23-36`; persisted
`models/agents.py:28-29`; served `routes/agents.py:218-219`; frontend receives `types.ts:405-408` + already renders
chips in `RoleHolders` `layout.tsx:2134-2155`). The gap is rendering/navigation, not data.

**Ask 1 — agents view (escalate/conflict-resolver/plan-health/plan-reconciler/monitor, running AND past):**

- Tabs are ROLE-only, 4 fixed (`ROLES_ORDER=["main","review","backup","custom"]`, `layout.tsx:1785`). Task-agents all
  register `role="custom"` (by design) → they collapse into ONE "custom" tab, distinguished only by the small kind chip.
- **THE LOAD-BEARING BLOCKER: "past ones" are impossible today** — finished one-shot/scheduled agents are HARD-DELETED
  (`DELETE /api/agents/{id}` `routes/agents.py:703-726`; `delete_agent` removes the row
  `state_store/agents.py:282-288`), so past escalate/plan-health runs have NO durable record on the agents surface (only
  activity-log lines). **P0: stop hard-deleting; transition to a terminal status (`finished`/`finished_at`/`exit_reason`
  on AgentRow) + a retention prune.**
- `GET /api/agents` ignores its own documented `?status` param (dead contract `agents.py:587`) — add `status`/`kind`/
  `lifecycle`/`include_finished`/`limit` filters pushed into the store query.
- Frontend: add `KINDS_ORDER` + a NEW `AgentTypesPanel` keyed on `agent_kind` (sibling of `AgentsPanel`, reuse
  `RoleHolders` + `AGENT_KIND_LABEL`), as ONE new tab (workers' fleet tab stays). Keep role chat (`main/review/backup`)
  clean — don't overload it.

**Ask 2 — activity feed (filter + pagination + denoise):**

- Backend caps at 50, orders+limits only, NO offset/cursor; `slot`/`type` filters are applied **POST-fetch on the
  already-limited 50 rows** (`routes/state.py:91-111`) → filtering for a rare type over a 90%-alert window returns
  near-nothing. Frontend fetches a fixed 50, no load-more anywhere (`App.tsx:48,394`). Alert/ops classification is a
  hardcoded incomplete client set (`layout.tsx:1258-1268`).
- Fix: push `slot`/`type`/category filters into SQL BEFORE the limit; add cursor pagination (`before_id`/offset) +
  envelope; add a **denoise rollup** (`GROUP BY event_type[,slot] within window` → "`slot_stale` ×12 in last 1h" — the
  `count_recent_activity` helper `activity.py:90-110` is the precedent). Frontend: "Load older", server-driven filter
  tabs, collapse duplicate rows with ×N badge, smaller live poll (~25). **This denoise rollup is the highest-leverage
  fix for the "90% repeating" complaint.**

**Ask 3 — conditions collapsible (pure frontend):** `ConditionsPanel` renders ALL conditions flat
(`layout.tsx:1218-1248`), no slice/collapse. Fix: `COLLAPSED_COUNT=5`, sort OFF+`gates_queued>0` first, slice with a
"Show N more ▾"/"Collapse ▴" toggle, keep the `onCount/total` chip. No backend change.

**Ask 4 — human↔agent messaging:** the ~1-min latency is the **agent-side `/loop` poll** (outbox→agent), NOT the
dashboard (dashboard already shows replies within 10s; `pending_count` exists but only as a number). Options (design
fork — discuss in prose, don't auto-pick): **(1) tmux "deliver now" nudge** — `POST /api/agents/{id}/nudge` pastes into
the agent's tmux session to trigger an immediate poll (server already drives tmux; ~instant; zero steady-state cost;
only works for spawned agents w/ known `tmux_session`) [lowest effort, recommend now]; **(2) adaptive cadence** — agent
shortens its own `/loop` for a window after receiving a message (`AgentPollResponse` could carry
`suggested_next_interval`) [cheap-idle, responsive-active]; **(3) long-poll/SSE** `/api/agents/{id}/poll?wait=25`
[near-instant, biggest change, end-state]; **(4) UI cadence override** live. Recommend 1+2 now, 3 later; + a
"queued/delivered" chip from `pending_count`.

All four are `[UI]` → playwright/vitest gate (`PLAN_FORMAT.md` §9); the dashboard is Vite (vitest `FleetGit.test.ts`
idiom) — confirm whether a Playwright smoke layer exists. Backend-paired asks (#1 retention, #2 pagination/denoise, #4
transport) ride agent-orchestrator's own QG (mid-migration: no staging/quickmerge, lands on LDR, main lags by design).

## Findings — deployment-ui monitoring pane — COMPLETE (Opus agent, 2026-06-18)

**Reframe of the operator's premise:** the "deployment-ui needs the biggest rework" feeling is **mostly already built
and already planned** under the monitoring master. CI/CD + image-build are mature; the REAL gaps are fleet-runtime +
alert-unification.

**What EXISTS (mature ≈90% — CI/CD + images):** Repos CI overview (`pages/RepoCi.tsx:447`: 25-repo matrix, 9-state CI,
LDR/staging/main SHAs, last-green-sha+age, LDR→main lag chip, SIT state, PR count, image cell) + repo drill-down (SHA
history, promotion pipeline strip, SIT lock, open-PR v2 chips, GitHub+AO+/fleet click-throughs); stuck-PR panel (5
classes); promotion-blocked (G1); promotion-drain; semver-health (G2); image cell + Cloud Builds tab (GCP+AWS); alert
ledger (`pages/Alerts.tsx` ← `gs://…/cicd/alerts`); Fleet-Git page (`pages/FleetGit.tsx`); VM Deployments / Live Ops /
VM Detail (batch-job health, heartbeat, reconcile); daily costs; services-overview; safety-ops scaffold; chaos.

**The REAL gaps (genuinely NEW unless flagged):**

- **Fleet RUNTIME state (biggest gap).** Fleet _git_ state is shipped (`FleetGit.tsx`) but **degrades to unavailable**
  because `ORCHESTRATOR_API_TOKEN` is unminted (`BLOCKED-CREDENTIALS`, master L162-167) — **the single cheapest
  high-value unblock: mint the token → a fully-built surface goes live.** Fleet _runtime_ (VMs up/down/OOM): batch jobs
  covered, but **NO central/infra-VM health tile** (the two LIVE VMs — central `i-0c9b283b…` + human-planning — have no
  monitoring tile; the vm-0 OOM class is invisible), **NO VM census/zombie surface** (`vm_zombie_watchdog.py` output
  unrendered), **NO unified single-glance "is the whole system healthy" landing** (operator opens 4 tabs).
- **Alerts ledger is CI/CD-ONLY** (`/alerts` ingests only `gs://…/cicd/alerts`) → VM-down, consolidator-down,
  git-health-guard, worker-liveness, data-pipeline alerts have NO row → "open deployment-ui to see any alert's full
  picture" breaks for ~half the alert classes. **NEW: unify the alert ledger across domains.**
- **Codebase-health lens missing** — repo health is only the green/red CI chip; no fleet-wide coverage% / QG-red-reason
  / file-size-debt matrix column (only per-service tabs). NEW.
- **Runtime deploy signal (v2, PLANNED master L212)** — `image_stale` answers "is main built into an image", NOT "what
  SHA is actually RUNNING in Cloud Run / on the VM vs main HEAD". Filed, unshipped.
- Already-filed/blocked (do NOT reimplement inline — master's own warning): version-coherence panel (L200),
  rollout-ratchet panels (template-drift + Dockerfile digest-pin, L210), G4 ruleset-drift, G5 change-freeze banner — all
  blocked on a Firestore verdict-store. Consolidator-health (G3) IN PROGRESS (slot-3).

**Alert→surface click-through map (where an alert should land + does it exist):** stuck-PR/branch-lag/CI-red/SIT/
promotion-quarantine/semver/image-build/image-stale → `/repos` ✅; fleet worktree dirty + reporter/cron-dead → `/fleet`
⚠️ BLOCKED on token; VM batch stalled/OOM → `/vm-deployments` ✅; **central/infra-VM down → NO surface ❌**;
consolidator- down → data-status (G3, not yet); ruleset-drift (G4)/change-freeze (G5) → NO surface ❌. Click-through
discipline is otherwise honored (ShaLink→GitHub, check→runs, repo→fleet).

**Change list — frontend:** [NEW] unified fleet/infra health landing tile (6th LandingTab; N VMs running·central-VM up·
consolidator fresh·fleet-git clean·CI green, each click-through); [NEW] central/infra-VM status chip (reads AO
`/api/fleet/summary`, click-through to AO — chip not rebuild, honors division-of-surfaces); [NEW] VM census/zombie
surface; [NEW] unify `/alerts` across alert domains; [NEW] codebase-health matrix column on `/repos`; [PLANNED] runtime
deploy-signal v2; [PLANNED, blocked] version-coherence/ratchet/G4/G5 panels; [IN-PROGRESS] consolidator-health (G3);
[NEW small] confirm `GhRateBudget` is placed on `/repos`. **Backend:** [NEW] `GET /api/fleet/vm-census`; [NEW] unified
alert ledger + `GET /api/alerts` superset; [NEW] `GET /api/fleet/infra-vm-health` (proxy AO summary); [PLANNED] runtime
deploy-signal resolver; **[UNBLOCK] mint `ORCHESTRATOR_API_TOKEN` into Secret Manager (both clouds) — lights up the
already-built Fleet-Git page (cheapest high-value fix in the whole fleet domain).**

## Recommended decisions / scoping — audit DONE 2026-06-18

Split into ONE wrapper plan with two per-repo tracks (`plans/active/monitoring_surfaces_overhaul_2026_06_18.md`):

**Track A — agent-orchestrator dashboard** (repo: agent-orchestrator; all `[UI]` → playwright/vitest gate):

- **P0 (load-bearing): retain finished one-shot/scheduled agents** (terminal status + `finished_at`/`exit_reason`, stop
  hard-deleting) — without it "show past escalate/plan-health runs" is impossible.
- P1: new `AgentTypesPanel` (one tab, keyed on `agent_kind`, running+past) + filterable `GET /api/agents`
  (`status`/`kind`/`lifecycle`).
- P1: activity feed — SQL filters before limit + cursor pagination + **denoise rollup** (×N collapse) = the "90%
  repeats" fix.
- P2: conditions tab collapsible (frontend-only, top-5 + expand).
- P2 (design fork — discuss in prose): human↔agent messaging — ship tmux "deliver now" nudge + adaptive cadence;
  long-poll/SSE as end-state; + a queued/delivered chip.

**Track B — deployment-ui monitoring pane** (repos: deployment-ui + deployment-api):

- **P0 (cheapest high-value): mint `ORCHESTRATOR_API_TOKEN` into Secret Manager (both clouds)** → lights up the
  already-built Fleet-Git page (BLOCKED-CREDENTIALS → file the operator ask).
- P1: central/infra-VM health tile + VM census/zombie surface (`GET /api/fleet/infra-vm-health` + `/vm-census`).
- P1: unify the `/alerts` ledger across alert domains (VM/consolidator/git-health/data, not just CI/CD) +
  `GET /api/alerts` superset — this is what makes "alert → open deployment-ui → full picture" actually work.
- P2: unified single-glance fleet/infra landing tile; codebase-health matrix column on `/repos`; runtime deploy-signal
  v2.
- DO-NOT-REIMPLEMENT (already filed/blocked on the Firestore verdict-store): version-coherence, rollout-ratchet, G4
  ruleset-drift, G5 freeze; consolidator-health (G3) is IN-PROGRESS (slot-3) — coordinate, don't duplicate.

**Cross-audit link:** Audit-1's surface-routing contract (CI/CD→deployment-ui, escalation/slot→AO, SHA/PR→GitHub) is the
click-through target that Track B's unified alert ledger must honor.
