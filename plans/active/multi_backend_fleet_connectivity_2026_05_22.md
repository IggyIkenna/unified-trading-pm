---
name: multi_backend_fleet_connectivity
title:
  "Multi-backend fleet connectivity — direct UI↔all-backends, GCS registry, shared→asymmetric auth, GCS health
  heartbeat, per-VM TLS"
type: active
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
estimate_class: infra
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 5.5
status: active
priority: P1
created: 2026-05-22
last_updated: 2026-05-22
locked_by: live-defi-rollout
source:
  design discussion with operator (Harsh) 2026-05-22 — agent-orchestrator dashboard 401 triage → fleet-connectivity
  redesign
gate:
  Phase 1 (auth model) + Phase 2 (per-VM TLS) must both be green before Phase 5 (UI rewire); Landing.tsx unblock (Phase
  0) ships immediately, independent of all later phases
related_plans:
  - plans/epics/orchestrator_master.md
---

# Multi-backend fleet connectivity

One UI (Firebase Hosting, HTTPS) with **full, direct, bidirectional API access to every orchestrator backend** in the
fleet — spawn, chat, reload, control, monitor — across ~12 backends, with a single login and a self-describing registry.
This is **not** a read-only aggregator: interactive control stays direct fan-out (browser → each backend). Only
**liveness/resource health** is decoupled to a push model, because a process cannot reliably report its own death.

## Operating constraints (operator-confirmed 2026-05-22)

- **Compute = AWS only.** All new VMs provisioned on AWS (account `427895769566`); GCP credits expired ~2 months ago.
  Existing GCP VM (`api.agent-orchestrator.odum-research.com`) stays as the always-on bootstrap host until retired.
- **Storage = GCS only** (`central-element-323112`, cheap, all data already there). **No S3 in this plan** — deferred to
  a named successor (see `## Temporary states + their canonical follow-up plans`).
- **Every AWS VM gets a static (elastic) IP** at provision. Harsh's PC has a static IP and is in-fleet. **Ikenna's
  laptop has no static IP → excluded from interactive reach** (may still appear monitor-only via the GCS heartbeat,
  Phase 4).
- **Provision flow (target):** create VM → assign elastic IP → add `<id>.agent-orchestrator.odum-research.com` A-record
  → fetch JWT secret + TLS material from GCS → start backend + TLS terminator → backend **self-registers** its hostname
  in the GCS registry → UI sees it on next `/api/backends`.

## Design decisions (closed)

1. **Connectivity:** direct browser→backend fan-out (NOT a hub). Static IPs make every backend directly reachable, so no
   tunnel/mesh needed.
2. **HTTPS (mixed-content fix):** terminate TLS on each backend on its own subdomain via **Caddy** (`:443 → :8026`). A
   browser cannot call `http://<ip>:8026` from an HTTPS page, and a CA will not issue for a bare IP — so each VM needs a
   DNS name. Default to **per-host automatic Let's Encrypt certs** (no shared private key sprayed across the fleet);
   wildcard-cert-in-GCS is the convenience fallback only (Phase 2 records the trade-off).
3. **Auth:** single login, fleet-wide token. **v1 = shared HS256 secret read from GCS** (simplest, removes the
   per-backend-token hack). auth.py is structured so **HS256→RS256 asymmetric is a config swap, not a rewrite** — the
   hardening (sign-on-one-issuer, verify-with-public-key-everywhere) is a follow-up, not a v1 blocker. Blast-radius of
   the shared secret is the WHOLE fleet (these backends spawn agents next to live-trading surfaces) — documented,
   accepted for v1.
4. **Registry:** the backend list lives as a single object in GCS, served by any backend via `/api/backends`. Backends
   **self-register on startup** (after their own health check passes) using an **etag-guarded read-modify-write**
   (`ifGenerationMatch`) to avoid concurrent-boot races. Stored entries are **hostnames, not IPs**.
5. **Health:** every backend writes a heartbeat + `psutil` metrics blob to GCS **every 60s** from a side-channel
   (systemd timer, separate from the main process so it survives a hang). The monitoring UI page reads from GCS — never
   polls a possibly-dead process for its own liveness.

## Coordination note (HARD — read before any code)

This direction **deletes** the other agent's recent per-backend-token work (`tokensByBase` / `setAuthTokenFor` in
`dashboard/src/api.ts`, commits `b6ebd58`, `dab57f0`, `b848193`). Per workspace "delete deprecated code — no parallel
paths", that machinery is removed in Phase 5, not extended. **Align with the other agent + Ikenna before starting Phase
1/5.** No silent revert of their commits.

---

## Pre-audit (workspace-wide, before execution)

- [ ] [AGENT] P0. `rg` every consumer of the symbols this plan removes/renames and embed the manifest here:
      `tokensByBase`, `setAuthTokenFor`, `clearAuthTokens`, `backendSessionKey`, `loadSessionFor`,
      `ORCHESTRATOR_JWT_SECRET` (env path), and the `http://<ip>:8026` URLs in `config/backends.json`. 0 hits ≠ safe —
      open `App.tsx` + `Login.tsx` consumers and confirm.
- [ ] [AGENT] P0. Confirm where the `odum-research.com` DNS zone is hosted (Squarespace vs Cloud DNS). Per
      `docs/OPERATIONS.md` it was "Squarespace → Firebase CNAME". If not API-scriptable, Phase 2 must first delegate the
      `agent-orchestrator.odum-research.com` subzone to Cloud DNS so provisioning can auto-create A-records.
- [ ] [AGENT] P0. Read `scripts/bootstrap_vm.sh` (the VM provisioner) end-to-end — it is the integration point for
      Phases 1–4 (cert fetch, JWT-secret fetch, Caddy install, self-register). Note current GCS-fetch steps to extend
      rather than duplicate.
- [ ] [AGENT] P0. Read `server/gcs_sync.py` `upload_state_to_gcs` — the health heartbeat (Phase 4) extends this, not a
      new module. Confirm the bucket/credentials path it uses (`ORCHESTRATOR_GCS_BUCKET`).

---

## Phase 0 — Immediate unblock (P0) — ✅ DONE (other agent, 2026-05-22)

The currently-reachable backend (`api.agent-orchestrator.odum-research.com`) rendered as a blank "Fleet Overview"
because `Landing.tsx:42` fetched `/api/backends` with **no token**, but the prod backend is strict
(`ALLOW_ANONYMOUS=false`) → 401. One-line consistency fix (mirror `refreshOne`, which already sends the token).

- [x] ✅ [AGENT] P0. `dashboard/src/Landing.tsx` — attach the bearer token to the `/api/backends` fetch. **Shipped by
      the other agent, merged to main, and deployed to Firebase Hosting (2026-05-22).**
- [x] ✅ [AGENT] P0. Build + deploy via CI; fleet card renders against the live backend. **Done — live.**

**Success:** ✅ `https://agent-orchestrator.odum-research.com` shows the GCP backend's VM card; `/api/backends` returns
200 with the token.

---

## Phase 1 — Shared JWT secret from GCS, asymmetric-ready (P1) — PARALLEL with Phase 2

- [ ] [AGENT] P1. `server/auth.py` — load `JWT_SECRET` from GCS (object path via `ORCHESTRATOR_JWT_SECRET_GCS_PATH` or
      similar) instead of per-VM env. Keep an env fallback for local dev only.
- [ ] [AGENT] P1. Wire JWT-secret **hot-reload** via the existing `CredsEnvPoller` machinery (the
      `runtime setup-token     rotation` commit) so rotation = overwrite the GCS object, no fleet redeploy.
- [ ] [AGENT] P1. Refactor `mint`/`verify` so the algorithm + key source are pluggable: `HS256` (shared secret) today,
      `RS256/ES256` (private-key issuer + public-key verifiers) later — a config swap, not a rewrite. Add a
      `JWT_ALGORITHM`-driven branch + key-loader abstraction. Do **not** implement RS256 now (follow-up plan), but leave
      the seam.
- [ ] [AGENT] P1. Provision the shared secret into GCS (least-privilege secrets bucket, per-VM SA read-only). Document
      the rotation runbook (owner/cadence/verifier/last_executed per the runbook SSOT rule).

**Success:** a token minted by logging into backend A validates on backend B (both reading the same GCS secret);
overwriting the GCS secret invalidates old tokens fleet-wide within the poller interval without a restart.

**Full-execution criterion:**

- ✅ Two real AWS backends, each reading the shared secret from GCS, accept the same operator token.
  - **What ran**: login on VM-1, replay token against VM-2 `/api/state` — both 200.
  - **Verification**: `curl -H "Authorization: Bearer <tok>" https://<vm2>/api/state` → 200; rotate GCS object → same
    call → 401 within poller interval.

---

## Phase 2 — Per-VM TLS termination (P1) — PARALLEL with Phase 1

- [ ] [AGENT] P1. (If Pre-audit found non-scriptable DNS) delegate `agent-orchestrator.odum-research.com` subzone to
      Cloud DNS; otherwise script A-record creation against the existing provider API.
- [ ] [AGENT] P1. Add **Caddy** to `scripts/bootstrap_vm.sh`: reverse-proxy `:443 → 127.0.0.1:8026`, automatic Let's
      Encrypt per-host cert for `<id>.agent-orchestrator.odum-research.com`. Open ports 80+443 in the AWS security
      group; close direct `:8026` to the public (localhost-only).
- [ ] [AGENT] P1. Document the cert trade-off in `docs/OPERATIONS.md`: per-host auto-cert (default, no shared key) vs
      wildcard-in-GCS (fallback, concentrates one private key across the fleet → only with a least-privilege secrets
      bucket).
- [ ] [AGENT] P1. Update CORS allow-list handling so each backend admits the Firebase UI origin
      (`ORCHESTRATOR_CORS_ORIGINS`) — confirm it covers the prod + any custom domains.

**Success:** `https://<id>.agent-orchestrator.odum-research.com/healthz` returns 200 with a valid CA cert; the HTTPS
Firebase UI can XHR it with no mixed-content block.

**Full-execution criterion:**

- ✅ A freshly-provisioned AWS VM serves HTTPS on its subdomain end-to-end.
  - **What ran**: `bash scripts/bootstrap_vm.sh` on a real AWS VM + A-record creation.
  - **Verification**: `curl -v https://<id>.agent-orchestrator.odum-research.com/api/backends` → 200, cert chain valid
    (`openssl s_client` shows Let's Encrypt issuer); browser DevTools shows the XHR succeeding from the HTTPS UI.

---

## Phase 3 — GCS-backed self-registering registry (P1) — depends on Phase 2 (stores hostnames)

- [ ] [AGENT] P1. `config/backends.json` → migrate the canonical list to a GCS object
      (`gs://<bucket>/fleet/registry.json`); `/api/backends` reads it (mode-aware: keep mock variant local). Entries
      keyed by `id`, store **hostname** (not IP), `label`, `account_id`, `asset_group`/role.
- [ ] [AGENT] P1. Backend **self-registration on startup**: after the local health check passes, read-modify-write its
      own entry into the GCS registry with `ifGenerationMatch` (retry on generation mismatch). Idempotent — updates its
      own entry, never clobbers siblings.
- [ ] [AGENT] P1. Backend **deregistration / staleness**: entry carries `last_registered`; the registry read filters or
      flags entries with no heartbeat (ties to Phase 4) so dead VMs don't linger as live.
- [ ] [AGENT] P1. UI bootstrap hardening: pin 2–3 always-on bootstrap hosts (the GCP VM + one stable AWS VM) so one dead
      VM can't blind the registry fetch.

**Success:** booting a new backend makes it appear in `/api/backends` from every other backend within one registration
cycle, with zero manual file edits and no race when two boot simultaneously.

**Full-execution criterion:**

- ✅ Two backends booted concurrently both appear in the GCS registry with no lost writes.
  - **What ran**: parallel `bootstrap_vm.sh` on two AWS VMs.
  - **Verification**: `gcloud storage cat gs://<bucket>/fleet/registry.json` shows both entries; generation history
    shows no overwrite-loss; `GET /api/backends` on a third backend lists both.

---

## Phase 4 — GCS health heartbeat + monitoring page (P1) — depends on nothing hard (write side); UI part pairs with Phase 5

- [ ] [AGENT] P1. Extend `server/gcs_sync.py`: write `gs://<bucket>/fleet/health/<id>.json` **every 60s** with `psutil`
      CPU/mem/disk + process uptime + `last_heartbeat` (UTC). Run from a **systemd timer separate from the main
      process** (survives a hung backend) — add the unit to `scripts/`.
- [ ] [AGENT] P1. `server/server.py` — new `/api/fleet/health` on the bootstrap backend that reads all
      `fleet/health/*.json` from GCS and returns the aggregate (this is liveness telemetry, NOT interactive control —
      does not route control through a hub).
- [ ] [AGENT] P1. Dashboard: new **Fleet Health** page/tab that renders the aggregate — per-VM up/stale (heartbeat age >
      90s = stale), CPU/mem/disk bars. Minimal first; extend later.
- [ ] [AGENT] P2. Ikenna's-laptop monitor-only path: if it pushes a heartbeat to GCS, it shows on the health page even
      though it's excluded from interactive reach. (Nice-to-have.)

**Success:** killing a backend (or its VM) flips its health card to "stale (no heartbeat 90s+)" within ~2 minutes; a
hung-but-running process is distinguishable from a downed VM.

**Full-execution criterion:**

- ✅ Real AWS VM writes a health blob every 60s; killing the process still leaves the last blob, and the page shows
  stale.
  - **What ran**: backend + health timer on a real AWS VM; then `systemctl stop` the backend.
  - **Verification**: `gcloud storage ls gs://<bucket>/fleet/health/` shows fresh `<id>.json` (mtime < 60s while up);
    after stop, blob stops updating and the UI flips to stale.

---

## Phase 5 — UI rewire to single-token direct fan-out (P1) — depends on Phases 1, 2, 3

- [ ] [AGENT] P1. **Delete** the per-backend-token machinery in `dashboard/src/api.ts` (`tokensByBase`,
      `setAuthTokenFor`, `clearAuthTokens`, per-backend session keys) — single token, sent to all backends (now valid
      everywhere via the shared secret). No re-export stubs, no parallel path.
- [ ] [AGENT] P1. `dashboard/src/App.tsx` — `BOOTSTRAP_URL` reads the registry from a pinned bootstrap host; all backend
      URLs become HTTPS hostnames from the registry (no `http://IP`). Direct fan-out preserved.
- [ ] [AGENT] P1. Simplify `Login.tsx` / session storage to one session (drop the per-backend persistence added in
      `b848193`).
- [ ] [AGENT] P1. Full type-check + lint + build (UI repo rules: `tsc --noEmit`, ESLint zero-warning, prettier);
      runtime-verify against ≥2 live AWS backends (golden path + a deliberately-down backend).

**Success:** one login → the UI lists and **interacts** (state, chat, spawn, reload) with every live AWS backend over
HTTPS, with a single token; a down backend shows an error card without breaking the rest.

---

## Phase 6 — Codex SSOT updates + docs (P2)

- [ ] [AGENT] P2. `codex/04-architecture/agent-orchestrator-overview.md` — document the multi-backend connectivity model
      (direct fan-out + GCS registry + GCS health heartbeat + shared/asymmetric auth). Supersede any prior per-backend-
      token description.
- [ ] [AGENT] P2. `codex/05-infrastructure/` — new doc: AWS VM provisioning for orchestrator backends (elastic IP →
      A-record → JWT+cert from GCS → Caddy → self-register). Cross-link `scripts/bootstrap_vm.sh`.
- [ ] [AGENT] P2. `agent-orchestrator/docs/OPERATIONS.md` — update fleet/backends section (TLS, registry-in-GCS, health
      page, single login). Remove the stale mixed-content caveat once Phase 2 lands.
- [ ] [AGENT] P2. Add the runbook fields (owner/cadence/verifier/last_executed) for: JWT-secret rotation, cert renewal
      monitoring, registry hygiene (stale-entry pruning).

---

## Parallelization

- **Phase 1 ∥ Phase 2** — independent (auth vs TLS). Different files; safe to run concurrently.
- **Phase 4 write-side** can start anytime (independent of auth/TLS).
- **Phase 3** depends on Phase 2 (stores hostnames); **Phase 5** depends on 1+2+3; **Phase 4 UI** pairs with Phase 5.
- **Phase 0** ships immediately, blocks nothing.

## No technical debt

Clean breaks only: per-backend-token code is **deleted** (Phase 5), not shimmed; `http://IP` URLs are **removed** from
the registry once TLS lands; `backends.json` stops being the SSOT (GCS object is). Safe rollback = git history.

## Temporary states + their canonical follow-up plans

- **S3 storage parity** — this plan is GCS-only by operator direction. Successor: `plans/active/` S3-parity plan (to be
  created when AWS storage is added) — route all fleet objects through `get_storage_client()`/`resolve_bucket_name()` so
  the GCS→add-S3 step is a config flip, not a rewrite.
- **Asymmetric JWT (RS256/ES256)** — Phase 1 leaves the seam; the actual issuer + public-key distribution lands in a
  successor `orchestrator_asymmetric_auth_*` plan. Until then the shared-secret blast-radius caveat stands.
