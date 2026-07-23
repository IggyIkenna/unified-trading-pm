---
title: "VM Deployment Registry Reaper + Path SSOT"
priority: P1
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: mixed
epic: none
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-service
    code: C2
    deployment: D0
  - repo: deployment-api
    code: C2
    deployment: D0
  - repo: unified-trading-pm
    code: C0
    business: B0
depends_on:
  - vm_observability_codex_update_2026_04_21
isProject: false
---

## Context

Plan 8 (`vm_observability_codex_update_2026_04_21`) landed 2026-04-21 and documented the three guarantees shipped by
`deployment-service` commits **`cc07649`** (daemon download) + **`beaa2e5`** (`VM_SHUTDOWN_ON_COMPLETION` self-delete):
streaming GCS log + `/api/vm-deployments` registry + self-delete on completion. Plan 8's scope was tight — document what
shipped — and it is correctly complete (7/7 todos `[x]`).

While executing Phase 2 VM monitoring on 2026-04-21, the orchestrator reported:

1. `gs://deployment-scripts-central-element-323112/vm-deployments/registry.json` **does not exist**.
2. `gcloud pubsub topics list --filter='name~vm-lifecycle OR name~unified-lifecycle'` returned nothing.
3. GCS log tails are the only surface that works.

On-disk investigation reveals those findings are based on **wrong paths/names** — the surfaces exist, just under
different identifiers — but the investigation ALSO uncovered a genuine code-level gap: **stale active entries are never
reaped**. Both problems are orthogonal to Plan 8 (which was doc-only), so this plan is a new follow-up rather than a
Plan-8 reopen.

### What actually exists (verified 2026-04-21)

| Orchestrator probe                                    | Real surface                                                                                                                        |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `gs://.../vm-deployments/registry.json` (missing)     | `gs://deployment-scripts-central-element-323112/deployments/{active,archive/<day>}/<uuid>.json` (per-VM file)                       |
| `vm-lifecycle` / `unified-lifecycle` pubsub (missing) | `projects/central-element-323112/topics/deployment-events` (also `deployment-status`, `deployment-alerts`, `deployment-api-events`) |
| GCS log tails                                         | `gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log` (correct, works)                                         |

### The real gap — stale active entries

`gcloud compute instances list --filter=status=RUNNING` on 2026-04-21 returned **7** VMs. `gs://.../deployments/active/`
contains **30** JSON entries. **~23 orphans**. Inspecting them:

- Stopped heartbeating `2026-04-19T17:18..20:14Z` and `2026-04-19..20T00:38..01:26Z` — all from the window **before**
  `cc07649` made the daemon file mandatory, so the wrapper fell into the `DAEMON_PID=""` branch at
  `vm-exec-with-gcs-tee.sh:96` ("`heartbeat daemon missing → observability disabled`"), registered the entry via the
  fallback `deployment_heartbeat.py register` path, then had no daemon process to SIGTERM at workload exit →
  `complete()` was never called → entry stays in `active/` forever.
- Post-`cc07649` VMs archive correctly (daemon SIGTERM path invokes `HeartbeatDaemon.complete()` at
  `unified-trading-library/unified_trading_library/lifecycle/daemon.py:223..254`, which calls `store.complete(entry)` →
  `DeploymentsRegistry.complete()` moves ACTIVE → `archive/<YYYY-MM-DD>/`).

However, even post-fix, **hard-kill paths still orphan entries**:

- `vm-exec-with-gcs-tee.sh:212` SIGKILLs the daemon if it doesn't exit within 30s → `complete()` skipped.
- Watchdog at `vm-exec-with-gcs-tee.sh:137..186` can kill the VM's workload via `pkill -KILL` — the daemon's SIGTERM
  still runs, but a second-order failure (OOM / VM pre-emption / panic before the daemon's cleanup finishes) leaves the
  entry in `active/`.
- `VM_SHUTDOWN_ON_COMPLETION=true` self-delete (beaa2e5) is a detached
  `nohup setsid bash -c "sleep 10 && gcloud compute instances delete ..."` — if the daemon's final upload takes > ~10s
  the VM can tear down mid-flight leaving a torn write. **No `complete()` confirmation gate** exists before the delete
  fires.

There is **no reaper** — `deployments_registry.py` has no `reap_stale` / `reconcile_against_gcp` method; no cron; no
`/api/vm-deployments/reap` admin endpoint. Operators must `gsutil rm` orphans by hand, which nobody does.

### Additional micro-bug in Plan 8 output

`/codex/05-infrastructure/vm-tarball-deployment.md:74` says "Firestore-backed `/api/vm-deployments` registration" — the
registry is actually **GCS-backed** (per `deployment-service/deployment_service/deployments_registry.py:7..11`). This
mis-attribution misleads any future toucher.

## Why a new plan (not Plan 8 reopen)

- Plan 8 is `type: business`, `B1`, doc-only. Its scope was "write codex that documents the three guarantees cc07649 +
  beaa2e5 shipped." That work is done and accurate in substance.
- This plan introduces **new code** (reaper method + /api/vm-deployments/reap endpoint + optional scheduled reap + CI
  integration test) + **new infra** (GHA or cron job that runs the reaper periodically) + **new docs** (corrected
  Firestore→GCS line + path/topic SSOT section).
- Per PM plan-format-rules §9a, Plan 8 is `locked_by: live-defi-rollout` and cannot be mutated without `[unlock-plan]`.
  Reopening it would also inflate its scope from `B1` doc to `C5/D3 mixed` — a different shape entirely.

## Blast radius (pre-audit manifest)

| Repo                    | File                                                 | Lines   | Action                                                                                    |
| ----------------------- | ---------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------- |
| deployment-service      | `deployment_service/deployments_registry.py`         | +60..80 | Add `reap_stale(max_age_hours, running_vm_names=...)` method                              |
| deployment-service      | `deployment_service/deployments_registry.py`         | +20     | Add `is_entry_stale(entry, now, max_age_hours)` classifier                                |
| deployment-service      | `deployment_service/vm/gcp_instance_lister.py` (NEW) | +30     | Wrap `google.cloud.compute_v1.InstancesClient.aggregated_list` for reaper                 |
| deployment-service      | `tests/unit/test_deployments_registry_reap.py` (NEW) | +120    | Cover 3 reap paths: stale+gone / fresh+running / stale+running                            |
| deployment-api          | `deployment_api/routes/vm_deployments.py`            | +40     | POST `/vm-deployments/reap?dry_run=true/false` handler (admin-gated)                      |
| deployment-api          | `tests/unit/test_vm_deployments_reap.py` (NEW)       | +80     | Mock-mode passthrough + real-mode mocked registry                                         |
| deployment-service      | `scripts/vm/vm-exec-with-gcs-tee.sh`                 | ±15     | Gate self-delete on "daemon final_upload returned 0" breadcrumb                           |
| unified-trading-library | `unified_trading_library/lifecycle/daemon.py`        | +3      | Write breadcrumb on `complete()` success — new `complete_breadcrumb` param                |
| unified-trading-pm      | `/codex/05-infrastructure/vm-tarball-deployment.md`  | ±5      | Fix "Firestore-backed" → "GCS-backed" at line 74                                          |
| unified-trading-pm      | `/codex/05-infrastructure/vm-tarball-deployment.md`  | +30     | NEW § "Registry Layout SSOT" — exact GCS paths + topic names + reaper invocation          |
| unified-trading-pm      | `/codex/05-infrastructure/vm-tarball-deployment.md`  | +15     | NEW § "Registry Reconciliation" — reaper cadence + operator runbook                       |
| deployment-service      | `.github/workflows/reap-vm-registry.yml` (NEW)       | +40     | Scheduled GHA: daily `curl -XPOST <deployment-api>/api/vm-deployments/reap?dry_run=false` |

### Not in blast radius

- `heartbeat_cli.py` / `deployment_heartbeat.py` — these are correct; the gap is downstream (no reaper consumes the
  `running` state).
- `setup-data-pipeline-vm.sh` daemon download (cc07649 already shipped).

## Execution DAG

```
Phase 1 (library primitives — PARALLEL)
    1a. deployments_registry.reap_stale() + is_entry_stale()
    1b. gcp_instance_lister.py (new file)
    1c. unit test suite
         │
         ▼
Phase 2 (API wiring — SEQUENTIAL on Phase 1) — deployment-api POST reap
         │
         ▼
Phase 3 (hard-kill protection — PARALLEL)
    3a. UTL daemon complete_breadcrumb param
    3b. vm-exec-with-gcs-tee.sh gates self-delete on breadcrumb
    3c. test coverage for breadcrumb path
         │
         ▼
Phase 4 (operational rollout — PARALLEL)
    4a. PM codex doc fixes (Firestore→GCS + Registry Layout SSOT + Reconciliation)
    4b. GHA scheduled reaper workflow
    4c. Backfill one-shot: reap the 23 current orphans via dry-run then live
         │
         ▼
Phase 5 (QG + acceptance)
```

## Phases

### Phase 1: Library primitives [PARALLEL within phase]

- [ ] [AGENT] P0. Add
      `DeploymentsRegistry.reap_stale(max_age_hours: int = 6, running_vm_names: set[str] | None =     None) -> list[DeploymentRegistryEntry]`
      — returns the archived entries. An entry is stale if: `now - last_heartbeat_at > max_age_hours` AND
      (`running_vm_names is None` OR `entry.vm_name not in     running_vm_names`). Each reaped entry is archived with
      `status="failed"`, `exit_code=125`, `completed_at=now`,
      `extras={"reap_reason": "heartbeat_stale" | "vm_not_running"}`.
- [ ] [AGENT] P0. Add `deployment_service/vm/gcp_instance_lister.py` — wraps
      `google.cloud.compute_v1.InstancesClient.aggregated_list(project=...)` into
      `list_running_vm_names(project_id: str) -> set[str]`. Read-only, failure-isolated (log + return empty set on any
      API error, per shard-level failure isolation rule).
- [ ] [AGENT] P0. Add `tests/unit/test_deployments_registry_reap.py` covering: (a) stale entry + VM gone → archived with
      reap_reason=vm_not_running; (b) fresh entry + VM running → untouched; (c) stale entry + VM running → archived with
      reap_reason=heartbeat_stale (heartbeat-thread died); (d) `running_vm_names=None` → fall-back to heartbeat-age
      only; (e) clock-skew tolerance — heartbeat < now within 5 min is never stale.
- [ ] [SCRIPT] P0. QG gate: `cd deployment-service && bash scripts/quality-gates.sh`.

### Phase 2: API endpoint [SEQUENTIAL on Phase 1]

- [ ] [AGENT] P0. Add `POST /api/vm-deployments/reap?dry_run=<bool>&max_age_hours=<int>` to
      `deployment_api/routes/vm_deployments.py`. Admin-gated via existing auth (mock mode bypasses auth). Returns
      `{"reaped": [<deployment_id>, ...], "dry_run": <bool>, "running_vm_count": <int>}`. In `dry_run=true` returns the
      same list without writing.
- [ ] [AGENT] P0. Add `tests/unit/test_vm_deployments_reap.py` — mock-mode returns a fixed list of two fake reapings;
      real-mode uses a `DeploymentsRegistry` backed by `InMemoryStorageClient` + a stub `list_running_vm_names`
      callable.
- [ ] [SCRIPT] P0. QG gate: `cd deployment-api && bash scripts/quality-gates.sh`.

### Phase 3: Hard-kill protection [PARALLEL within phase]

- [ ] [AGENT] P1. Add `complete_breadcrumb: pathlib.Path | None = None` keyword param to `HeartbeatDaemon.__init__` —
      written (touch-file with `completed_at` timestamp) at the END of `HeartbeatDaemon.complete()` AFTER
      `store.complete(entry)` returns. Keeps the public API additive; existing callers unaffected.
- [ ] [AGENT] P1. `scripts/vm/vm-exec-with-gcs-tee.sh` — pass `--complete-breadcrumb /tmp/vm-exec-$$.complete` to
      `heartbeat_daemon.py` launch; gate the self-delete block on `[[ -f "$COMPLETE_BREADCRUMB" ]]`. If the daemon was
      SIGKILLed (line 212) the breadcrumb will not exist, so the VM stays up for operator post-mortem. Replace the 30s
      daemon-wait with a check-and-wait loop that returns early once the breadcrumb appears.
- [ ] [AGENT] P1. Add `tests/unit/test_daemon_complete_breadcrumb.py` in UTL — exercise write-on-success and
      no-write-on-exception (patch `store.complete` to raise).
- [ ] [SCRIPT] P1. QG gate: `cd unified-trading-library && bash scripts/quality-gates.sh` +
      `cd deployment-service && bash scripts/quality-gates.sh`.

### Phase 4: Operational rollout [PARALLEL within phase]

- [ ] [AGENT] P2. Fix `/codex/05-infrastructure/vm-tarball-deployment.md:74` — replace "Firestore-backed" with
      "GCS-backed (`gs://deployment-scripts-central-element-323112/deployments/{active,archive}/`)".
- [ ] [AGENT] P2. Add new § "Registry Layout SSOT" section in `vm-tarball-deployment.md` after the existing
      "Observability & Lifecycle" section. Must cover: (a) exact GCS layout
      `gs://<bucket>/deployments/active/<uuid>.json` + `archive/<YYYY-MM-DD>/<uuid>.json`; (b) the four pubsub topics
      (`deployment-events` is the SSOT; `deployment-status` / `deployment-alerts` / `deployment-api-events` are
      secondary); (c) the GCS log path `gs://<bucket>/vm-logs/<vm-name>/run.log`; (d) explicit statement that
      `registry.json` (single-file) does **NOT** exist — files are per-VM.
- [ ] [AGENT] P2. Add new § "Registry Reconciliation" — documents the reaper: when it runs (GHA daily at 04:00 UTC), how
      to invoke manually
      (`curl -XPOST -H "Authorization: Bearer $TOKEN"     'https://<host>/api/vm-deployments/reap?dry_run=true'`), what
      `reap_reason` values mean, and the hard-kill scenario that `complete_breadcrumb` guards against.
- [ ] [AGENT] P2. Create `deployment-service/.github/workflows/reap-vm-registry.yml` — cron `0 4 * * *`,
      workflow_dispatch, calls reap endpoint with `dry_run=false`. Stores the response JSON as a workflow artefact.
- [ ] [AGENT] P2. One-shot backfill: after Phase 2 lands, call `/api/vm-deployments/reap?dry_run=true` to validate the
      23 existing orphans are correctly detected; then `dry_run=false` to archive them. Record the reaped IDs in the
      plan's "Completion Notes" section below.

### Phase 5: QG + acceptance [SEQUENTIAL]

- [ ] [SCRIPT] P0. Workspace QG sweep — deployment-service + deployment-api + unified-trading-library +
      unified-trading-pm all green.
- [ ] [AGENT] P0. Real-mode end-to-end: fire a short-lived sentinel VM (e.g. `launch-canonical-smoke-vm.sh`); confirm it
      appears in `deployments/active/`, heartbeats, self-deletes, and archives. Then force-orphan one (skip the daemon
      SIGTERM manually) and confirm the next reaper run archives it.
- [ ] [AGENT] P0. After all todos flip `done`, ASK the human to unlock Plan 8 AND this plan (two-plan unlock) with
      `[unlock-plan]`.

## Success criteria

- `/api/vm-deployments?status=running` returns exactly the set of RUNNING GCE VMs (± the heartbeat-window race) — not 30
  when only 7 VMs are running.
- Hard-kill paths (SIGKILL daemon / watchdog termination / VM pre-emption) leave the entry in `active/` but the next
  reaper run archives it with a structured `reap_reason`.
- Codex doc unambiguously states GCS paths + topic names; no reference to "registry.json" single-file or Firestore.
- GHA daily reaper runs green for 3 consecutive days.
- Basedpyright + ruff + bandit + plan-health all clean on every touched repo.

## Dependency graph

```
depends_on Plan 8 (codex/05/vm-tarball-deployment.md Observability & Lifecycle section must exist)
    │
    ▼
Phase 1 registry primitives (deployment-service)
    │
    ▼
Phase 2 API endpoint (deployment-api consumes Phase 1)
    │
    ▼
Phase 3 hard-kill protection (UTL + deployment-service wrapper, independent of API)
    │
    ▼
Phase 4 operational rollout (codex docs + GHA + backfill)
    │
    ▼
Phase 5 QG + acceptance
```

## Out of scope

- Replacing the GCS per-VM-file layout with a single `registry.json` or with Firestore. The per-VM layout is correct
  (atomic writes, easy archive-by-day, no read-modify-write races); the orchestrator's expectation was wrong.
- Replacing `deployment-events` with a new `vm-lifecycle` / `unified-lifecycle` topic. The existing topic is correct;
  the name is just surprising.
- Dashboard / UI — deployment-ui already consumes `/api/vm-deployments` via `src/pages/VmDeployments.tsx`; no UI work
  required once the API returns clean data.
- Refactoring `HeartbeatDaemon` to survive SIGKILL — out of scope; reaper is the agreed compensating control.

## Completion notes

_(filled in by executing agent — reaped deployment_ids, one-shot backfill output, GHA workflow run IDs)_
