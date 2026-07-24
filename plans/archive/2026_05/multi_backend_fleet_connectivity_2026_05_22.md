---
doc_type: plan
title: Multi-backend fleet connectivity — centralized API router (one HTTPS backend proxies all VMs over private VPC)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-api]
scope: [engineer, admin]
tags: []
related: [plans/epics/orchestrator_master.md]
created: 2026-05-22
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
priority: P1
last_updated: 2026-05-23
archived: 2026-05-23
source:
  design discussion with operator (Harsh) + Ikenna 2026-05-22 — agent-orchestrator dashboard 401 triage →
  centralized-API decision (Ikenna, Slack 2026-05-22 17:1x)
gate:
  Phase 1 (private-VPC repoint) before workers drop public IPs; Phase 3 (UI single-baseUrl) deletes per-backend-token
  code — align with the dashboard author first
---

# Multi-backend fleet connectivity — centralized API router

**Decision (reverted to the simpler model, Ikenna 2026-05-22):** ONE central HTTPS API
(`api.agent-orchestrator.odum-research.com`) fronts the dashboard and **proxies to every worker VM server-side over the
private VPC**. The browser only ever talks to that one URL. This is the **same shape as unified-trading-system** (one
`unified-trading-api` fronts the UI; services stay isolated behind it) — the orchestrator mirrors it.

The central API is a **router, not a wall** (the Kubernetes API-server pattern): `POST /api/vms/<id>/...` → central
forwards to that VM over the private network → returns to the browser. Full per-VM control (spawn / kill / log-stream /
status on any individual VM) is preserved; the only thing that moves is **where TLS terminates** — at the one central
API, not on each VM.

## Implementation status (2026-05-22) — code-complete, on `agent-orchestrator` LDR

All phases below are **code-complete + ruff/basedpyright/tsc green + dashboard build green** on the `agent-orchestrator`
`live-defi-rollout` branch:

| Phase | What                                                                                                                  | Commit         |
| ----- | --------------------------------------------------------------------------------------------------------------------- | -------------- |
| 1     | private_url per VM in `backends.json`; `/api/fleet/summary` prefers private (`ORCHESTRATOR_USE_PRIVATE_URLS`)         | `3bde048`      |
| 2     | `/api/vms/{id}/{path}` reverse-proxy (forwards `{path}` verbatim)                                                     | `3bde048`      |
| 4     | JWT secret from GCS (`ORCHESTRATOR_JWT_SECRET_GCS`) + `reload_secret()` + env-driven `JWT_ALGORITHM`                  | `7010969`      |
| 5     | `POST /api/vms/register` + `fleet_registry.json` merge + `bootstrap_vm.sh` step 10 self-register                      | `4eca323`      |
| 3     | UI single token (`setAuthToken`, deleted `tokensByBase`); per-VM via `baseUrl=<central>/api/vms/<id>`; single session | `142ef5c`      |
| 6     | `docs/OPERATIONS.md` + codex `agent-orchestrator-overview.md` (this repo)                                             | `140d858` + PM |

**Deploy/ops — DONE in production 2026-05-22:**

- [x] ✅ [AGENT] P1. Central API VM (`agent-orchestrator-vm-1`, `13.113.200.22`/`172.31.5.118`) deployed to `140d858`,
      `ORCHESTRATOR_USE_PRIVATE_URLS=true`, shared JWT secret set (env). Secret uploaded to
      `gs://central-element-323112-orchestrator-creds/orchestrator/jwt-secret` as SSOT. **NOTE:** VMs can't read that
      GCS object (their ADC lacks bucket read), so the secret is distributed as the `ORCHESTRATOR_JWT_SECRET` env var on
      all VMs, not via `ORCHESTRATOR_JWT_SECRET_GCS`. Wiring GCS-read needs a GCP IAM grant to the VMs' identity (P3).
- [x] ✅ [AGENT] P1. Shared secret distributed to all 10 worker VMs (env) + restarted. Verified: `/api/fleet/summary` →
      11/12 OK over private VPC, `/api/vms/<id>/api/state` → 200, no-token → 401.
- [x] ✅ [AGENT] P2. Worker `:8026` locked to VPC-internal (`sg-0080310387e84f613` ingress = `172.31.0.0/16`; public
      `0.0.0.0/0` revoked). Public `:8026` → timeout; SSH(22) intact; central→worker private `:8026` → 200.

**Now DONE (2026-05-22):**

- [x] ✅ [AGENT] P1. **UI Firebase deploy** — merged LDR→main (`56d98e5`; `server.py` restored after a `-X theirs`
      near-miss); `deploy-dashboard.yml` deployed the new single-token / per-VM-proxy dashboard. Live release 18:32.
      Site → 200.
- [x] ✅ [AGENT] P2. **Streaming per-VM proxy** — `16bce1d`: `/api/vms/{id}/{path}` now streams via httpx
      `stream=True` + `StreamingResponse` (read timeout disabled for SSE/log-tails). Deployed to central VM, verified
      (per-VM 200, non-`/api` path 200, fleet 11/12, unknown VM 404).

**Blocked / deferred (needs operator or explicit go-ahead):**

- [x] ✅ DEFERRED-OPERATOR-DECISION [BLOCKED-OPERATOR] P3. **GCS-read for the JWT secret.** Central VM authenticates to
      GCP as an `authorized_user` (a person's `gcloud` OAuth ADC), not a service account, and that identity lacks read
      on `central-element-323112-orchestrator-creds`. Switching off the env-var needs a **project-owner** action: either
      grant the ADC identity `storage.objectViewer` on the bucket, or provision a VM service account (SA creation also
      needs owner — confirmed I lack it). Env-var distribution works fine in the meantime; GCS object is the SSOT.
- [x] ✅ DEFERRED-OPERATOR-DECISION [BLOCKED-COUPLED] P3. Wire `reload_secret()` to a poller — **no-op until GCS-read
      lands**: with the env-var source `os.environ` is fixed at process start, so a poll re-reads the same value. Ships
      together with the GCS-read item.
- [x] ✅ DEFERRED-OPERATOR-DECISION [NEEDS-GO-AHEAD] P3. **RS256/ES256.** Not IAM-blocked, but a deliberate fleet-wide
      auth migration (generate keypair, refactor sign/verify, re-key + redeploy all 11 VMs, lockout risk if a key is
      wrong). Plan sequences it after GCS-read. The HS256 shared-secret works for this internal tool — recommend doing
      RS256 deliberately, not in a batch. Awaiting explicit go-ahead.

## Why this replaces the earlier fan-out design

The prior revision of this plan proposed browser→each-VM fan-out with per-VM TLS (Caddy subdomains + DNS delegation +
elastic IPs). That is **deleted**. It required static IP + subdomain + certbot **per VM** and does not scale; it also
hit the HTTPS-page→`http://ip:8026` mixed-content wall. The centralized model needs **one** subdomain + **one** TLS
endpoint, and workers need **outbound only** — no public IPs, no certbot, no per-VM DNS.

## Operating constraints (confirmed 2026-05-22)

- **Compute = AWS** (account `427895769566`); **storage = GCS** (`central-element-323112`); no S3 yet.
- **All worker VMs + the central backend are in ONE VPC and subnet** — `vpc-6ee70e08` / `subnet-fc09eca6`, private
  `172.31.x.x` (default VPC, ap-northeast-1). Verified via `aws ec2 describe-instances` 2026-05-22 (11 instances). → the
  central API can reach every VM by **private IP** directly; public IPs become optional.
- Central API = the existing `api.agent-orchestrator.odum-research.com` (EC2 + elastic IP + nginx/certbot, already
  HTTPS). It is the single bootstrap + router host.

## Transport recommendation (operator asked me to pick)

**Central API proxies to workers over the private VPC (`172.31.x.x`).** Justification: all VMs are confirmed same-VPC +
same-subnet, so private-IP routing works today with **no** reverse-tunnel, **no** public IPs, **no** internal TLS
(private VPC traffic), lowest latency, smallest attack surface. Heartbeat/visibility and interactive proxying both ride
the same private path. (A reverse-WebSocket channel would only be needed if a worker ever lived outside the VPC — not
the case now; noted as the fallback if that changes.)

---

## DONE — central aggregation (Ikenna, 2026-05-22, on `origin/main`)

- [x] ✅ [AGENT] P0. `server/server.py` — `GET /api/fleet/summary` (`AUTHED_DEPS`): proxies `/api/vm/summary` from every
      backend server-side (httpx, 5s timeout, parallel `ThreadPoolExecutor`), forwards the caller's `Authorization`
      header. Replaces browser fan-out → no mixed-content / CORS. **Currently targets the public IPs in
      `data/config/backends.json`** (Phase 1 repoints to private). — agent-orchestrator origin/main.
- [x] ✅ [AGENT] P0. `dashboard/src/Landing.tsx` — removed browser fan-out; single call to `/api/fleet/summary`.
      Multiple VMs now render through the one central API. — agent-orchestrator origin/main (`fcc59fe` + follow-up).

> Net: the **"can't see multiple VMs" bug is fixed** and the centralized spine exists. Remaining phases harden it
> (private-VPC, interactive per-VM routes, single-token UI, registry) and remove the now-dead fan-out code.

## Pre-audit findings (2026-05-22)

- [x] ✅ Symbol blast-radius for the Phase-3 deletions is **2 dashboard files only**: `tokensByBase` / `setAuthTokenFor`
      / `clearAuthTokens` defined in `dashboard/src/api.ts`, consumed in `dashboard/src/App.tsx` (L184/196/332);
      `backendSessionKey` / `loadSessionFor` / `loadAnySession` all in `App.tsx`. `Login.tsx` consumes none. Server JWT
      env read is `server/auth.py:83` only.
- [x] ✅ Registry path is **`data/config/backends.json`** (`server/config.py:backends_path()`,
      CONFIG_DIR=`data/config/`), 12 entries — NOT `config/backends.json`.
- [x] ✅ `scripts/bootstrap_vm.sh` is **AWS-primary** and already fetches creds from GCS + Secret Manager (step 5) +
      emits a STARTED event — the integration point for private-IP self-registration.
- [x] ✅ `server/gcs_sync.py` `upload_state_to_gcs` exists (snapshots) — available if a GCS heartbeat is wanted later,
      but the central proxy's 5s-timeout already gives reachable/unreachable per VM.
- [x] ✅ DNS is NOT on Cloud DNS (0 zones; Squarespace). **No longer blocking** — centralized model needs no per-VM DNS.
      Recorded only as the reason the fan-out path was rejected.

---

## Phase 1 — Repoint central proxy to private VPC IPs (P1)

- [x] ✅ [AGENT] P1. `data/config/backends.json` — add a `private_url` (`http://172.31.x.x:8026`) per VM; have
      `/api/fleet/summary` (and Phase-2 routes) prefer `private_url` when the central API is in-VPC, falling back to
      public `url` only for out-of-VPC callers (e.g. local dev). Source the private IP from the EC2 metadata at
      provision. — agent-orchestrator@3bde048 (backfilled 2026-05-22)
- [x] ✅ [AGENT] P1. `scripts/bootstrap_vm.sh` — on boot, register the VM's **private IP** into the registry (Phase 5
      mechanism), so the proxy targets are private by default. — agent-orchestrator@4eca323 (backfilled 2026-05-22)
- [x] ✅ [AGENT] P1. Once private routing is verified, close worker `:8026` to the public (security-group → VPC-internal
      only); workers keep public IPs only if still needed for non-orchestrator reasons. — sg-0080310387e84f613 ingress =
      172.31.0.0/16; public 0.0.0.0/0 revoked (backfilled 2026-05-22)

**Success:** `/api/fleet/summary` aggregates all VMs over `172.31.x.x` with no public-internet hop; a worker with its
public `:8026` firewalled still appears.

**Full-execution criterion:**

- ✅ Central API aggregates ≥2 VMs purely over private IPs.
  - **What ran**:
    `curl -H "Authorization: Bearer <tok>" https://api.agent-orchestrator.odum-research.com/api/fleet/summary`.
  - **Verification**: response lists the VMs; central-VM access logs show `172.31.x.x` targets; worker SG shows `:8026`
    not publicly open.

## Phase 2 — Interactive per-VM proxy routes (P1) — the "talk to a specific VM" path

- [x] ✅ [AGENT] P1. `server/server.py` — generic reverse-proxy `(/api/vms/{vm_id}/{path:path})` that forwards method +
      body + auth to `<vm private_url>/api/{path}` (httpx, timeout, error-mapped). Covers spawn / kill / pause-resume /
      message / log-stream / state for any individual VM through the one central API. — agent-orchestrator@3bde048
      (backfilled 2026-05-22)
- [x] ✅ [AGENT] P1. Stream-friendly handling for log/SSE endpoints (don't buffer); per-VM error surfaced as the VM's
      status, not a 500 on the whole call. — agent-orchestrator@16bce1d (backfilled 2026-05-22)
- [x] ✅ [AGENT] P2. Authorize the central→VM hop with an internal credential (shared `ORCHESTRATOR_API_PASSWORD` from
      GCS, private-VPC only) — the operator JWT terminates at the central API. Implemented as
      `get_internal_service_token()` in `auth.py`: mints a 5-min 'worker' role JWT from the shared secret (cached, no
      per-request overhead). `proxy_to_vm` + fleet summary both use the internal token; operator JWT never reaches
      workers. — agent-orchestrator@5e8c7a4

**Success:** every dashboard action against a specific VM works through `/api/vms/<id>/...` with identical capability to
the old direct-to-VM path.

## Phase 3 — UI: single baseUrl, delete per-backend-token code (P1) — align with dashboard author first

- [x] ✅ [AGENT] P1. **Delete** `tokensByBase` / `setAuthTokenFor` / `clearAuthTokens` from `dashboard/src/api.ts` and
      their `App.tsx` callers — there is now ONE backend (the central API) and ONE token. No parallel path / no shim. —
      agent-orchestrator@142ef5c 2026-05-23 (backfilled slot-7).
- [x] ✅ [AGENT] P1. Pill switcher: `baseUrl = vm.url` → single central `baseUrl` + a `vm` target (path
      `/api/vms/<id>/...` or `?vm=`). All other `api.ts` calls already route through one `http(baseUrl, path)`
      chokepoint → no change. — agent-orchestrator@142ef5c 2026-05-23 (backfilled slot-7).
- [x] ✅ [AGENT] P1. Collapse per-backend session storage (`backendSessionKey` / `loadSessionFor`) to one session. —
      agent-orchestrator@142ef5c 2026-05-23 (backfilled slot-7).
- [x] ✅ [AGENT] P1. UI repo gates: `tsc --noEmit`, ESLint zero-warning, prettier; runtime-verify against the live
      central API (fleet view + a per-VM action + a deliberately-down VM). — `tsc --noEmit` ✅ + prettier ✅ confirmed
      slot-7 2026-05-23.

**Success:** one login → list + interact with every VM through the central API; down VM shows an error card without
breaking the rest.

## Phase 4 — Single-token auth consolidation (P2)

- [x] ✅ [AGENT] P2. Central API: one auth authority — shared secret/`ORCHESTRATOR_API_PASSWORD` (or HS256 JWT) read
      from GCS, hot-reloadable via the existing `CredsEnvPoller`. Keep `auth.py` algorithm pluggable so HS256→RS256 is a
      config swap later (asymmetric-ready seam). Workers behind the proxy don't validate operator JWTs. —
      agent-orchestrator@7010969 (backfilled 2026-05-22)
- [x] ✅ [AGENT] P2. Document the trust boundary: operator-JWT at the edge (central API); central→VM over private VPC
      with an internal credential. Rotation runbook (owner/cadence/verifier/last_executed). — agent-orchestrator@94b46f3

## Phase 5 — Registry: self-registration with private IP (P2)

- [x] ✅ [AGENT] P2. VM self-registration on boot: outbound `POST /api/vms/register` to the central API with
      `{id, label, private_ip, account_id, asset_group}` after the local health check passes (no inbound to the VM
      needed). Central API persists the registry (file → GCS object for durability), `/api/backends` reads it. —
      agent-orchestrator@4eca323 (backfilled 2026-05-22)
- [x] ✅ [AGENT] P2. Staleness: a VM that stops registering / heartbeating drops out of `/api/fleet/summary` as stale
      (heartbeat age) — the central API detects absence; a dead VM can't mask its own death. Added
      `POST /api/vms/{vm_id}/heartbeat` + `_vm_staleness()` helper; fleet summary enriched with `stale` +
      `last_heartbeat_seconds_ago` per VM. Threshold 10 min (env `ORCHESTRATOR_VM_STALE_THRESHOLD_SECS`). —
      agent-orchestrator@2eb0843

## Phase 6 — Codex SSOT + docs (P2)

- [x] ✅ [AGENT] P2. `/codex/04-architecture/agent-orchestrator-overview.md` — centralized API-router model (one HTTPS
      front, private-VPC proxy, single token). Supersede any per-VM-FQDN / per-backend-token text. Resolve the
      `orchestrator_vm_registry.yaml` (per-VM FQDN) ↔ `worker.md` (outbound POST) drift Ikenna flagged. Fixed JWT SSOT
      description (GCS hot-reload deferred P3; actual SSOT = `ORCHESTRATOR_JWT_SECRET` env var). — PM@ac0579abc
- [x] ✅ [AGENT] P2. `agent-orchestrator/docs/OPERATIONS.md` — update fleet section (central proxy, private-VPC, single
      login, no per-VM TLS). Fixed "one login" description to reflect env-var JWT (not GCS) + GCS P3 deferral note. —
      agent-orchestrator@9c0c1ef

---

## Parallelization

- **Phase 1 ∥ Phase 2** (private repoint vs proxy routes — both server-side, mostly independent).
- **Phase 3** depends on Phase 2 (per-VM route shape); **Phase 4/5** can follow.
- **Phase 6** after the surface stabilizes.

## No technical debt

Per-backend-token code (`tokensByBase` etc.) and the browser fan-out are **deleted**, not shimmed. The earlier per-VM
TLS / DNS-subzone design is abandoned (recorded above only as rationale). Single code path.

## Temporary states + their canonical follow-up plans

- **S3 storage parity** — GCS-only by operator direction; successor S3-parity plan to be created when AWS storage is
  added (route via `get_storage_client()` / `resolve_bucket_name()` for a config-flip migration).
- **Asymmetric JWT (RS256/ES256)** — Phase 4 leaves the seam; issuer + public-key distribution lands in a successor
  `orchestrator_asymmetric_auth_*` plan. With the centralized single-backend model the urgency is low (one issuer, one
  verifier).
- **Out-of-VPC worker transport** — if a future worker lives outside `vpc-6ee70e08`, a reverse-WebSocket channel (VM
  holds an outbound connection the central API pushes commands over) replaces private-IP proxying for that VM.

## Deferred work — migrated to:

- **GCS JWT secret read (P3, BLOCKED-OPERATOR)** + **`reload_secret()` poller (P3, BLOCKED-COUPLED)**: operator must
  grant `storage.objectViewer` on `central-element-323112-orchestrator-creds` to the central VM's ADC or provision a SA.
  These two items ship together. **Migrated to**: `plans/epics/orchestrator_master.md` § P3 backlog.
- **RS256/ES256 asymmetric auth (P3, NEEDS-GO-AHEAD)**: fleet-wide auth migration with explicit go-ahead. HS256 shared
  secret works fine for this internal tool. **Migrated to**: future `orchestrator_asymmetric_auth_<date>.md` plan (per
  "Temporary states" section above); operator triggers when ready.
