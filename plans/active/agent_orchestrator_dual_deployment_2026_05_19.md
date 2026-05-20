---
name: agent-orchestrator-dual-deployment-2026-05-19
overview:
  Dual-brain + shared-UI deployment topology for agent-orchestrator. Harsh's backend + workers stay local on his laptop;
  Ikenna's brain runs on Cloud Run in asia-northeast1 + his workers move to VMs (his successor plan). Shared SPA on
  Firebase Hosting at agent-orchestrator.odum-research.com switches between backends via top-bar dropdown. All decisions
  locked 2026-05-19 (Harsh has full operator agency); Ikenna's plan diff is a deferred follow-up.

type: design
status: active
epic: epic-infra

estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6

locked_by: live-defi-rollout
locked_since: 2026-05-19

related_plans:
  - plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - plans/active/agent_orchestrator_slack_notifications_2026_05_19.md
  - plans/active/agent_orchestrator_workers_on_vms_2026_05_XX.md (not yet written)

owner: harsh
verifier: harsh
last_executed: not-yet-run
---

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

- [ ] **D11 refactor**: extract `WorkerHost` protocol + `LocalTmuxHost` from `server/tmux_spawn.py`. Preserves current
      behavior verbatim for Harsh; no functional change. Ikenna's `SshRemoteTmuxHost` lands later in his successor plan.
- [ ] **D11 wiring**: add `ORCHESTRATOR_WORKER_HOST=local` to `scripts/orchastrator.service` + `.env.example` default;
      `WorkerHost` instance created at FastAPI app startup from this env var.
- [ ] **D5 / D14 CORS**: add `https://agent-orchestrator.odum-research.com` to nginx CORS allowlist on
      `/etc/nginx/sites-enabled/orch.epiphanytechnologies.com`.
- [ ] **D14**: extend `/done` request body with `repo` + `branch` fields; brain `git fetch origin <branch>` before
      `git show <sha>`. Backwards-compatible (missing fields = current worktree-path fallback).
- [ ] **D18**: cron + systemd timer rsyncing `data/` → `gs://harsh-orchestrator-backup/` (~tens of KB/hr).
- [ ] **D19**: `/healthz` enriched with `last_heartbeat_seconds_ago`; SPA dropdown polls every 30s + shows "offline" /
      "last seen Xmin ago" badge.
- [ ] **D4 smoke test**: verify the 5 multi-backend dropdown concerns end-to-end on staging — base-URL switch,
      JWT-per-backend localStorage isolation, scoped logout, SSE reconnect on backend change, CORS smoke from
      `agent-orchestrator.odum-research.com` to both backends.
