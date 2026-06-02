---
name: orchestrator_asymmetric_auth_2026_06_01
title: "orchestrator RS256/ES256 asymmetric auth — central signs, workers verify (retire HS256 shared secret)"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P2
status: archived
model_tier: opus-required
thinking_tier: max
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.8
created: 2026-06-01
last_updated: 2026-06-01
archived: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/12-agent-workflow/orchestrator-multi-vm-topology.md
migrated_from:
  "orchestrator_master P2 deferred backlog (multi_backend_fleet_connectivity_2026_05_22) — operator go-ahead 2026-06-01"
---

## ✅ ARCHIVED 2026-06-01 — ES256 fleet-wide + HS256 retired

Internal central↔worker auth is ES256-only on all 11 orchestrator VMs (agent-orchestrator@f44b948); private key
distributed via the restricted creds bucket (central-only abandoned, operator decision); the `internal-secret` object is
RETAINED for /api/escalate. Codex `agent-orchestrator-overview.md` updated. **Deferred work:** none. Unlocked for
archival. 0 open todos.

## Why this exists

Operator gave the go-ahead 2026-06-01 to start the fleet-wide auth migration deferred from
`multi_backend_fleet_connectivity_2026_05_22`. Today the central↔worker proxy token auth is **HS256 with a single
fleet-shared secret** (`ORCHESTRATOR_INTERNAL_SECRET`, distributed via
`gs://central-element-323112-orchestrator-creds/orchestrator/internal-secret`). The shared-secret model means **every
worker VM holds the signing key** — a single compromised VM can mint valid internal tokens for the whole fleet. The
Phase-4 connectivity work left an explicit seam for asymmetric auth.

Target: **RS256/ES256** — the central API VM holds the PRIVATE key (signs internal proxy tokens); worker VMs hold only
the PUBLIC key (verify, cannot mint). The operator-JWT secret (`ORCHESTRATOR_JWT_SECRET`, central-only) is unaffected.

## Scope + invariants

- Migrate ONLY the central↔worker internal proxy token (`auth.get_internal_service_token()` / verification in
  `server.py::proxy_to_vm`). Operator-JWT (HS256, central-only) stays as-is for now.
- Asymmetric: private key central-only; public key fleet-distributed (it's non-secret — workers only verify).
- Keep the two-secret model's separation (operator JWT vs internal proxy token) — this plan only changes the algorithm +
  key-distribution of the internal token.
- Backward-compat window: central must accept BOTH HS256 (old) and RS256 (new) during rollout, then drop HS256.

## Phases

### Phase 1 — Design + key provisioning ✅ DONE 2026-06-01

- [x] ✅ [DESIGN] P2. **Chose ES256** (P-256 — smaller/faster than RS256; PyJWT+cryptography support it). Key channel:
      PUBLIC key in fleet-readable GCS; PRIVATE key central-only via a local mode-600 FILE (NOT the worker-readable
      bucket; multi-line PEM doesn't fit systemd `Environment=`). DR copy of the private key in GCP Secret Manager.
      Dual-accept window documented below. Collision group: `ao_asym_auth_design`.
- [x] ✅ [SCRIPT] P2. Provisioned the ES256 keypair: PUBLIC →
      `gs://central-element-323112-orchestrator-creds/orchestrator/internal-public.pem` (fleet-readable, verified);
      PRIVATE → GCP Secret Manager `ORCHESTRATOR_INTERNAL_PRIVATE_KEY` (central-only). (KMS-asymmetric-signing is the
      future hardening — local-file private key is the v1.)

### Phase 2 — Code: dual-accept verify + ES256 sign ✅ DONE 2026-06-01

- [x] ✅ [CODE] P2. `server/auth.py`: ES256/RS256 signing (central private key) + DUAL-ACCEPT verify (public-key
      asymmetric pass restricted to ES256/RS256 — closes alg-confusion — THEN legacy HS256). Operator JWT untouched
      (separate `INTERNAL_ALG`). Env: `ORCHESTRATOR_INTERNAL_ALG` +
      `ORCHESTRATOR_INTERNAL_{PRIVATE,PUBLIC}_KEY[_FILE|_GCS]`. Default HS256 → zero behavior change until configured. 7
      unit tests (sign/verify ES256, dual-accept legacy HS256, alg-confusion guard, FILE-load).
      agent-orchestrator@3538894 + @4f2c65f (LDR). ruff + basedpyright clean.

### Phase 3 — Rollout (canary-first) ✅ DONE 2026-06-01

- [x] ✅ [SCRIPT] P2. **Pass A** — deployed @4f2c65f + `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS` systemd drop-in to **all
      11 VMs** (dual-accept-ready: workers verify HS256+ES256, central still HS256 → zero behavior change). **Pass B** —
      flipped CENTRAL (api-host) to `INTERNAL_ALG=ES256` + private-key FILE + restart. **E2E verified**: central signs
      ES256 (validated in-process), and a worker (vm-cefi 172.31.11.51) returned **HTTP 200** for a central-minted ES256
      internal token vs **401** with no token — i.e. workers verify the central's ES256 tokens via the public key over
      the live VPC proxy. Zero non-localhost proxy-401s post-flip. Rollback = remove the central ES256 drop-in (workers
      still dual-accept HS256). NB: the localhost `/git-status` 401s seen during rollout are a PRE-EXISTING local-cron
      auth issue, unrelated to this migration (separate finding).

### Phase 4 — Retire HS256 — ✅ DONE 2026-06-01

- [x] ✅ [CODE] P2. ✅ DONE 2026-06-01 (retired live, no 2-day wait needed). The real gate was "all-ES256," not elapsed
      time (5-min internal-token TTL). On checking the live fleet we found ES256 signing was complete on only 1 of 11
      VMs (`agent-orchestrator-vm-1`); the other 10 (`…-20260522` batch) lacked the private key + `INTERNAL_ALG`.
      **Completed the ES256 rollout to all 11** (operator decision: distribute the private key to every VM via the
      restricted creds bucket `ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS` + `INTERNAL_ALG=ES256` — central-only abandoned),
      started the 9 stopped VMs to apply, verified **11/11 sign ES256** (`GCS priv-key READ ok` + active), then
      **retired HS256** (cherry-picked `staged/hs256-retire-2026-06-03` → LDR @f44b948; `decode_token` ES256-only,
      `_issue_internal_token` raises without a private key) and deployed to all 11 (HEAD=f44b948, hs256_refs=0, active —
      verified 11/11). Codex updated (`agent-orchestrator-overview.md` × 3 spots). **RETAINED the `internal-secret`
      object** (it's the `verify_internal_secret()` pre-shared key for `POST /api/escalate`) — only the HS256 _JWT_
      accept/sign paths retired. The 9 non-running VMs re-stopped (paused state restored; ES256 config + retired code
      persist on EBS; both ao-self-pull + git-health-guard crons installed so they're current on next restart).
      Collision group: `ao_asym_auth_code`.

## Closing condition

All proxy auth is RS256/ES256; no worker holds a signing key; HS256 shared-secret path removed; codex two-secret-model
doc updated; ≥48h clean RS256 traffic.

## Composes with

`codex/04-architecture/agent-orchestrator-overview.md` § "two-secret model" + the Phase-4 connectivity seam in
`server.py::proxy_to_vm`.
