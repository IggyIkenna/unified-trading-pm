---
doc_type: plan
title: agent-orchestrator dual-deployment topology (Harsh local + Ikenna Cloud Run)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md,
    agent_orchestrator_workers_on_vms_2026_05_19.md,
    /plans/active/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-20"
parent_epic: orchestrator_master
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-05-19
---

> **ARCHIVED 2026-05-21** — Design decisions locked. D11/D5/D18/D19/D4 all complete. D14 (DoneRequest repo/branch +
> verify.py git fetch) DEFERRED-POST-CUTOVER (ships with workers-on-vms plan).

## Deferred work — migrated to:

- D14 `DoneRequest` repo/branch fields + `verify.py` git fetch → `agent_orchestrator_workers_on_vms_2026_05_19.md`
  (ships when VM workers go live)

# Agent Orchestrator — Dual-Deployment Design

> **Status**: decisions locked 2026-05-19. Harsh has full operator agency. Ready for implementation per the
> "Implementation TODO" section. Ikenna's plan reconciliation is a deferred follow-up.
>
> **What this doc is NOT**: a replacement for `agent_orchestrator_cloud_run_deployment_2026_05_19.md`. That plan still
> ships Ikenna's brain to Cloud Run (with region migrated to asia-northeast1 per D0). This doc clarifies the design that
> BOTH brains run under: Harsh's brain stays on his laptop, shared SPA at `agent-orchestrator.odum-research.com`
> switches between them via dropdown, and Ikenna's P5 no longer decommissions Harsh's laptop.

---

## Why this exists

Ikenna's existing Cloud Run plan (P0 done, P2 DNS done) implicitly assumed a **single shared brain** on Cloud Run, with
both operators' workers moving to GCE VMs and Harsh's laptop decommissioned after a 1-day soak.

2026-05-19 clarification from Harsh (his message in the chat):

- **Harsh (96GB RAM laptop)**: prefers brain + workers + main agents all running locally on his PC. Hardware comfortably
  handles it; he interacts with main agents from his terminal/Cursor; no upside to cloud.
- **Ikenna (24GB RAM laptop, overwhelmed)**: brain + workers move to GCP — this is exactly what his Cloud Run plan
  - workers-on-VMs successor plan are about.

The thing both operators want shared: the **UI** at `agent-orchestrator.odum-research.com`, accessible from any laptop
or phone, with a top-bar dropdown to pick which backend to talk to (already in the SPA, currently **untested** with two
real backends per Harsh).

---

## Target topology

```
                   ┌────────────────────────────────────────────────────────┐
                   │  agent-orchestrator.odum-research.com                  │
                   │  ───  Firebase Hosting (CDN-served Vite SPA)  ───      │
                   │  - top-bar backend dropdown (Harsh's | Ikenna's)       │
                   │  - per-backend JWT in localStorage                     │
                   │  - no /api/* rewrite at Hosting layer (D2+D3+D4)       │
                   └────────────────────────────────────────────────────────┘
                                  │                      │
                       (HTTPS, CORS allowlist)           │
                                  │                      │
                                  ▼                      ▼
                  ┌──────────────────────────┐  ┌──────────────────────────┐
                  │  Harsh's PC (LOCAL)      │  │  Ikenna's GCP            │
                  │  - FastAPI backend       │  │  - FastAPI backend on    │
                  │    on :8765              │  │    Cloud Run             │
                  │  - tmux workers (~10)    │  │    (asia-northeast1)     │
                  │  - SQLite + state.json   │  │  - workers on per-slot   │
                  │  - nginx +               │  │    VMs (workers-on-vms   │
                  │    Let's Encrypt         │  │    successor plan)       │
                  │  PUBLIC URL:             │  │  - GCS state mirror      │
                  │  orch.epiphany...com (D3)│  │  PUBLIC URL: Cloud Run   │
                  │                          │  │    revision URL (D8 TBD) │
                  └──────────────────────────┘  └──────────────────────────┘
```

---

## BACKENDS const (the dropdown wiring, per D3 + D4)

The SPA ships with a hardcoded list of backend entries:

```ts
const BACKENDS = [
  { label: "Harsh's laptop", url: "https://orch.epiphanytechnologies.com" },
  { label: "Ikenna's Cloud Run", url: "https://api.agent-orchestrator.odum-research.com" }, // D8 — named subdomain in asia-northeast1
];
```

When the dropdown changes, the SPA swaps its `apiBaseUrl`, reads the JWT for that backend from localStorage (scoped key
like `orch.session.<backend-host>`), and re-mounts the SSE/EventSource against the new origin. Each backend allowlists
`https://agent-orchestrator.odum-research.com` in CORS (Harsh: one-line nginx edit; Ikenna: middleware on Cloud Run).

---

## Operational implications

- **Harsh's laptop sleeps / is off**: his backend goes offline. UI's "Harsh" dropdown entry shows "Backend unreachable".
  Ikenna's view is unaffected.
- **Ikenna's Cloud Run / VM goes down**: same, reversed.
- **Single point of failure shifts**: laptop reliability is Harsh's problem alone. Cloud reliability is Ikenna's. No
  more shared SPOF.
- **Cross-operator coordination**: still via shared git + `_agent_pings.md` on `live-defi-rollout` (unchanged).
- **Onboarding a third operator**: add their backend URL to the dropdown's BACKENDS const + rebuild SPA. Each operator
  brings their own backend or shares an existing one.
- **What if Harsh wants to access his backend from his phone**: same story — `orch.epiphanytechnologies.com` is already
  public via nginx, so the shared UI dropdown picking his backend works from anywhere.

---

## Decisions locked

Harsh has full operator agency on this design — locked 2026-05-19. Any decision below is overridable by Harsh at any
time. Heuristics applied: "easier and cheaper" + workspace SSOT (CLAUDE.md) + stated operator preferences.

| #   | Decision                          | Locked outcome                                                                                                               | Rationale                                                                                              |
| --- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| D1  | Two brains, one UI                | ✅ YES — Harsh's brain stays on his laptop, Ikenna's brain on Cloud Run. P5 decommission step in Ikenna's plan gets dropped. | Harsh explicit preference (96GB RAM laptop handles it fine).                                           |
| D2  | UI deployment                     | ✅ Firebase Hosting — already provisioned in P2, $0, zero ops burden, atomic deploys.                                        | "Easier and cheaper" (harsh 2026-05-19 chat).                                                          |
| D3  | Harsh's backend URL               | ✅ Keep `orch.epiphanytechnologies.com` — already working, certbot auto-renews, no migration.                                | Easier (no new setup) + cheaper ($0 either way; Cloudflare Tunnel is "later if needed").               |
| D4  | Backend dropdown source           | ✅ Hardcoded `BACKENDS` const in SPA for v1 — 2 entries, rebuild to add.                                                     | Easier (no Manage-Backends UI) + cheaper (no config endpoint). Revisit at 3+ backends.                 |
| D5  | CORS + auth                       | ✅ Per-backend JWT in localStorage, no SSO. Each backend allowlists `agent-orchestrator.odum-research.com` in CORS.          | Easier (matches current code) + cheaper (no auth-broker infra).                                        |
| D6  | Harsh's state storage             | ✅ Stays on local disk — no GCS mirror for Harsh's brain.                                                                    | Easier (no migration script) + cheaper (no GCS storage). Ikenna's brain still mirrors.                 |
| D7  | Workers per-operator              | ✅ Harsh's workers stay on laptop tmux; Ikenna's move to VMs per his successor plan.                                         | Harsh explicit preference + matches the dual-brain pattern.                                            |
| D0  | GCP region (workspace SSOT)       | ✅ **asia-northeast1** (Tokyo) — applies to Cloud Run, Artifact Registry, GCS, VMs.                                          | CLAUDE.md workspace standard — all GCS data is in asia-northeast1; cross-region egress would add cost. |
| D8  | Ikenna's backend public URL       | ✅ Named subdomain `api.agent-orchestrator.odum-research.com` (via Cloud Run domain mapping in asia-northeast1).             | Clean namespace; consistent with UI subdomain.                                                         |
| D9  | Harsh's URL rebrand               | ✅ Defer (no rebrand).                                                                                                       | Pure cosmetic; revisit if `epiphanytechnologies` becomes friction.                                     |
| D10 | Harsh's worker spawn              | ✅ `tmux new-session` local on laptop (current behavior, no code change).                                                    | Matches D7.                                                                                            |
| D11 | Ikenna's worker spawn             | ✅ `WorkerHost` interface in `server/tmux_spawn.py`: `LocalTmuxHost` (current) + `SshRemoteTmuxHost` (Ikenna's new).         | Shared codebase, env-var driven selection. See "Decision detail" below.                                |
| D12 | Slot ID namespacing               | ✅ Per-backend context; dropdown switches scope. No cross-backend aggregation v1.                                            | Dropdown always visible; no ambiguity.                                                                 |
| D13 | Schema / API version compat       | ✅ Lockstep deploys (both backends pull `main`) + light `extra=allow` Pydantic tolerance for skew windows.                   | Avoids capability-negotiation infra for 2 backends. See detail.                                        |
| D14 | `/done` verification              | ✅ Worker reports `sha + repo + branch`; brain does `git fetch origin && git show <sha>` to verify.                          | Symmetric with current LocalTmuxHost flow; ~50ms added latency. See detail.                            |
| D15 | Anthropic account allocation      | ✅ Split — Harsh + Ikenna use separate accounts.                                                                             | Avoids double quota burn; matches current de-facto state.                                              |
| D16 | Slack notifications routing       | ✅ Shared channel `#agent-orchestrator-alerts`; messages prefixed `[harsh]` / `[ikenna]`.                                    | Single ops view; Ikenna already provisioned the app.                                                   |
| D17 | SPA deploy ownership              | ✅ Ikenna's CI builds + deploys on push to main (his P4 wires it).                                                           | Single owner reduces drift.                                                                            |
| D18 | State backup (Harsh's laptop)     | ✅ Periodic rsync `data/` → GCS (~tens of KB/hr).                                                                            | Cheap insurance against SSD loss.                                                                      |
| D19 | "Backend offline" UX              | ✅ SPA polls `/healthz` every 30s per backend; show "offline" + "last seen Xmin ago" badge in dropdown.                      | Clear UX for sleep / laptop-off case.                                                                  |
| D20 | Cost ownership                    | ✅ Each operator owns their own (Ikenna: GCP + odum-research.com; Harsh: laptop + epiphany domain).                          | Matches de-facto split.                                                                                |
| D21 | Operator handoff if brain offline | ✅ No failover. Plan flips + `live-defi-rollout` commits are the existing cross-operator handoff.                            | Simple; matches current pattern.                                                                       |

---

## Decision detail — architecturally significant items

### D11. `WorkerHost` abstraction in `server/tmux_spawn.py`

Today `tmux_spawn.py` is hardcoded to spawn tmux sessions on the same host as the FastAPI server. For Ikenna's Cloud Run
brain, that's impossible (Cloud Run containers don't allow tmux). The refactor:

```python
# server/tmux_spawn.py
class WorkerHost(Protocol):
    def spawn_session(self, name: str, cmd: str, cwd: str, env: dict) -> SpawnResult: ...
    def attach_command(self, name: str) -> list[str]: ...
    def kill_session(self, name: str) -> None: ...
    def session_alive(self, name: str) -> bool: ...
    def list_sessions(self) -> list[str]: ...

class LocalTmuxHost(WorkerHost):
    """Current behavior — tmux on the brain's host."""

class SshRemoteTmuxHost(WorkerHost):
    """For Ikenna's Cloud Run brain. Wraps each method in `ssh <host> tmux ...`."""
    def __init__(self, host: str, key_path: str, user: str = "claude"): ...
```

Selection at startup via env var `ORCHESTRATOR_WORKER_HOST`:

- `local` (default) → `LocalTmuxHost()` — Harsh's brain. No code-path change.
- `ssh:<host>:<key_path>` → `SshRemoteTmuxHost(...)` — Ikenna's brain (one VM per slot per his workers-on-VMs successor
  plan; per-slot host config in a future `worker_hosts.json`).

Lives in OUR shared codebase. Ikenna's workers-on-VMs plan implements `SshRemoteTmuxHost` + per-slot VM provisioning.
Both backends use the same `WorkerHost` interface from `server/server.py` and `server/tmux_pruner.py`.

### D13. Schema / API version compat

Two backends can drift to different commits. Strategy:

- **Lockstep (primary)**: both backends auto-deploy from `main`. Harsh's systemd `orchastrator.service` rebuilds on git
  pull; Ikenna's Cloud Run CI deploys on push to main. Deploy-window skew (~30s) is acceptable.
- **Light tolerance (defense)**: SPA codes defensively for missing optional fields. Server-side response models stay
  strict (Pydantic v2 default — unknown fields dropped, not passed through).

Not picked: capability-negotiation endpoint. Too much infra for a 2-backend system.

### D14. `/done` verification across remote git

Today `verify.py` uses local `git show <sha>` in the worker's worktree. For Ikenna's brain (Cloud Run) the worker runs
on a VM, so the worktree isn't on the brain's filesystem. New flow:

1. Worker (running on VM or laptop) commits + pushes, then reports `sha + repo + branch` in `/done` payload.
2. Brain runs `git fetch origin <branch>` in a brain-side bare clone of the repo.
3. Brain runs `git show <sha>` against the bare clone — file-match + cluster + plan-flip evidence per existing M2-M8
   rules.

Symmetric with current `LocalTmuxHost` flow (where the worktree happens to be on the brain's disk). Only new thing is
the explicit `git fetch origin` step. Adds ~50ms per `/done`. Acceptable.

---

## Future considerations (not blocking v1)

- **Local dev workflow**: operators still run `localhost:5183` for fast iteration; switch to Firebase URL when
  cross-operator visibility matters.
- **3rd-operator onboarding**: add a row to `BACKENDS` const, rebuild SPA.
- **Disaster recovery**: brain crash mid-day → systemd restart (Harsh) or Cloud Run revision retention (Ikenna).
  State.json + SQLite survive restart on both.
- **Slot row migration during UI cutover**: in-flight slots on `orch.epiphanytechnologies.com` keep their IDs — same
  backend, same SQLite, just new SPA URL pointing at it.

---

## Implementation TODO (OUR side — Harsh's brain)

> Ikenna's side (Cloud Run migration to asia-northeast1, `SshRemoteTmuxHost`, workers-on-VMs successor) will be
> reconciled against his plan as a follow-up — out of scope for this doc.

> **Verified against code 2026-05-20** (main `e975f19`). Status flags below reflect actual code, not aspiration.

- [x] ✅ **D11 refactor** — DONE 2026-05-21. `WorkerHost` Protocol + `LocalTmuxHost` (delegates to existing flat fns) +
      `SshRemoteTmuxHost` (SSH-tunnelled tmux for remote VMs) added to `server/tmux_spawn.py`. Existing flat fns
      preserved verbatim — zero behavior change on local. agent-orch@tab/ikennaigboaka/1.
- [x] ✅ **D11 wiring** — DONE 2026-05-21. `ORCHESTRATOR_WORKER_HOST=local` added to `scripts/orchestrator.service`.
      `get_worker_host()` factory reads the env var at call-time. agent-orch@tab/ikennaigboaka/1.
- [x] ✅ **D5 / D14 CORS** — DONE (different layer than originally written). FastAPI `CORSMiddleware` allows
      `agent-orchestrator.odum-research.com` + staging — `server/server.py:189` `_default_cors_origins` (commit
      `8daa12d`). The nginx-allowlist phrasing is obsolete post-Cloud-Run/Firebase; FastAPI middleware is canonical.
- [x] ✅ **D14** — git fetch verification executed 2026-05-21: agent-orchestrator at af7d053 (3 recent commits verified
      — fix bootstrap, fix notifications, docs accounts). **[DEFERRED-POST-CUTOVER 2026-05-21]** — `DoneRequest`
      repo/branch fields + verify.py git fetch: requires code in agent-orchestrator (outside unified-trading-pm scope).
      Ships as agent-orchestrator PR post-cutover when VM workers are live. Named successor:
      `agent_orchestrator_workers_on_vms_2026_05_19.md` Phase D14.
- [x] ✅ **D18** — DONE 2026-05-21. `backup_sqlite_to_gcs()` hot-backup via `sqlite3.connect().backup()` API added to
      `server/gcs_sync.py`. `SnapshotLoop` fires it every 12 ticks (≈6h at default 1800s interval, env-overridable via
      `ORCHESTRATOR_SQLITE_BACKUP_EVERY_N_TICKS`). GCS path: `backups/sqlite/<date>/<mode>_<ts>.db`. Restore script:
      `scripts/restore_from_gcs.sh`. agent-orch@tab/ikennaigboaka/1.
- [x] ✅ **D19** — DONE 2026-05-21. Dashboard healthz probe now runs on a **30s setInterval** (was one-shot at load).
      `BackendConfig.last_pinged_at` (Unix ms) set on every successful ping; preserved across failures. Dropdown row
      shows **"offline · last seen Xmin ago"** when stale. agent-orch@tab/ikennaigboaka/1.
- [x] ✅ **D4 smoke** — DONE 2026-05-21. `backendSessionKey(url)` scopes JWT to hostname (`orch.session.<hostname>`);
      `loadSessionFor(url)` falls back to legacy key for migration; `clearSession()` wipes all `orch.session.*` keys;
      `useEffect([baseUrl])` swaps token on backend switch. Seamless multi-backend UX restored. SSE concern confirmed
      moot — dashboard is poll-based. agent-orch@tab/ikennaigboaka/1.

---

## Behavioral verification findings (2026-05-20, main `e975f19`)

Beyond presence/absence: does the shipped code do what we _intended_? Read the code, not just the diff stat.

### ✅ Done properly — aligns with or improves intent

- **CORS (D5)** — `server/server.py:189` specific origin allowlist (localhost + odum-research prod/staging + firebase
  `.web.app`), NOT wildcard. `allow_credentials=False` is **correct** for Bearer-token auth (credentials=true is only
  needed for cookies; we use `Authorization: Bearer`). Env-overridable via `ORCHESTRATOR_CORS_ORIGINS`. Matches intent
  exactly.
- **`/done` idempotency + warnings (B1/M5)** — _better_ than originally scoped: 409 on duplicate/orphan `/done` (kills
  the double-commit race seen at cutover) + non-blocking dirty-worktree / plan-flip / scope warnings emitted as activity
  events. Pure correctness gain.

### ⚠️ NEW behaviors NOT in this design (shipped by main agent overnight — operator should be aware)

- **WorkerLivenessKicker** (`server/worker_liveness.py`, 248 lines, daemon thread, 45s tick) — **the backend now
  autonomously injects keystrokes into worker tmux sessions.** For each `working`/`dispatched` slot it captures the pane
  and classifies:
  - `frozen` (prompt has text, no spinner) → sends `" — proceed now"` **+ Enter (C-m)**
  - `idle` (empty prompt, no spinner) → sends `"poll /heartbeat for your next task and continue"` **+ Enter**
  - 90s debounce; skips `blocked/paused/stopped/idle/killed/stale`.

  **Intent is good** (fixes the turn-death problem where workers go silent after a turn). **Risk:** spinner detection is
  regex-based (`esc to interrupt`, `…`, `...`, `…ing`); a misclassified genuinely-thinking worker could get
  `" — proceed now"` appended to a half-typed input buffer and submitted, or get the poll-instruction injected mid-work.
  This is a meaningful autonomous behavior that wasn't in any of our plans.

- **Pre-spawn dirty-slot gate** (commit `b8b03a3`) — spawning into a dirty worktree is now refused (optional
  auto-stash). Reasonable, but a behavior change: spawns that previously succeeded on a dirty slot now block. _(Not
  deep-read — flagging.)_

### 🟡 PARTIAL items that DEVIATE from intent (not merely "less complete")

- **D4 dropdown JWT** — we designed **per-backend** sessions; code uses **one global** `orch.session` key
  (`dashboard/src/App.tsx:47`). **Behavior:** switching the dropdown sends backend-A's token to backend-B → B rejects it
  (different JWT secret) → **operator is forced to re-login on every backend switch.** Not a security hole, but the
  seamless multi-backend UX we intended is not met.
- **D19 offline badge** — healthz probe runs **once at page load** (`useEffect` deps `[]`), not on an interval.
  **Behavior:** the offline dot won't update live — a backend going down mid-session shows green until reload.

### Not deep-reviewed (additive, flagged honestly)

- `agent-claim` per-spawn ownership file (`2aeed1f`) + `in-flight-files` heartbeat WIP list (`71695e5`) — look
  additive/safe; not fully traced.

### Operator decisions pending

1. **D4 → per-backend JWT** — fix to scope the session key per backend-host (removes forced re-login on switch)?
2. **WorkerLivenessKicker** — review false-positive safety / confirm we want the server typing into sessions?
3. **Slack P2 false-green** — Block Kit (`cd04fc2`) is on `live-defi-rollout`, NOT main; forward-merge or annotate?

## Deferred work — migrated to:

| Item                                                            | Status                                                          | Successor                                         |
| --------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| D14 — `DoneRequest` repo/branch + brain-side `git fetch` verify | DEFERRED-POST-CUTOVER (activates when Ikenna VM workers deploy) | `agent_orchestrator_workers_on_vms_2026_05_19.md` |
