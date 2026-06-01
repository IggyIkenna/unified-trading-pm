---
name: orchestrator_asymmetric_auth_2026_06_01
title: "orchestrator RS256/ES256 asymmetric auth — central signs, workers verify (retire HS256 shared secret)"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P2
status: active
model_tier: opus-required
thinking_tier: max
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.8
created: 2026-06-01
last_updated: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/12-agent-workflow/orchestrator-multi-vm-topology.md
migrated_from:
  "orchestrator_master P2 deferred backlog (multi_backend_fleet_connectivity_2026_05_22) — operator go-ahead 2026-06-01"
---

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

### Phase 4 — Retire HS256 (PENDING — 48h soak)

- [ ] [CODE] P2. After ≥48h of all-ES256 traffic with zero HS256-fallback hits (log-confirmed), drop the HS256 accept
      path + ~~delete the shared `internal-secret` object~~ **RETAIN the object** (see re-scope below). Update codex.
      Collision group: `ao_asym_auth_code`. Est 0.2 AI-day. **Soak started 2026-06-01 ~14:00Z.**

  **🟢 STAGED 2026-06-01 — ready to merge on/after 2026-06-03 (DO NOT merge before the gate):**
  - **Code change is written + green** on branch `staged/hs256-retire-2026-06-03` (agent-orchestrator@3257199):
    `decode_token` drops the legacy HS256 internal-token accept path; `_issue_internal_token` drops the HS256 signing
    fallback (raises without an ES256/RS256 private key); 2 tests updated (HS256 signing now raises; legacy HS256 token now
    rejected). Verified: ruff + basedpyright + full pytest (344 passed).
  - **⚠️ RE-SCOPE — do NOT delete the `internal-secret` object.** The raw `_internal_secret` is now also the pre-shared key
    for `verify_internal_secret()` → `POST /api/escalate` (the GHA→orchestrator dispatch added in
    `cicd_contract_hardening_2026_06_01` P1 #7, agent-orchestrator@93b46c6). Deleting it would break escalation auth. Only
    the HS256 *JWT accept/sign* paths are retired; the object stays.
  - **MERGE GATE (run 2026-06-03 ~14:00Z+):** (1) confirm zero HS256-fallback hits in the soak window —
    `journalctl -u orchestrator --since '2026-06-01 14:00' | grep -c 'internal HS256 secret'` should be 0 on every VM
    (the debug line was removed in the staged change; check the pre-staging logs); (2) confirm every VM has an ES256/RS256
    private key configured (`ORCHESTRATOR_INTERNAL_PRIVATE_KEY[_FILE|_GCS]` + `INTERNAL_ALG=ES256`); (3) then
    `git merge --ff-only` / cherry-pick `staged/hs256-retire-2026-06-03` onto LDR + `ao-self-pull` deploys it; (4) update
    the codex asymmetric-auth section. If ANY VM still lacks the private key, do NOT merge (would break its internal-token
    signing).

## Closing condition

All proxy auth is RS256/ES256; no worker holds a signing key; HS256 shared-secret path removed; codex two-secret-model
doc updated; ≥48h clean RS256 traffic.

## Composes with

`codex/04-architecture/agent-orchestrator-overview.md` § "two-secret model" + the Phase-4 connectivity seam in
`server.py::proxy_to_vm`.
