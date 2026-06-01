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
migrated_from: "orchestrator_master P2 deferred backlog (multi_backend_fleet_connectivity_2026_05_22) — operator go-ahead 2026-06-01"
---

## Why this exists

Operator gave the go-ahead 2026-06-01 to start the fleet-wide auth migration deferred from
`multi_backend_fleet_connectivity_2026_05_22`. Today the central↔worker proxy token auth is **HS256 with a single
fleet-shared secret** (`ORCHESTRATOR_INTERNAL_SECRET`, distributed via `gs://central-element-323112-orchestrator-creds/orchestrator/internal-secret`).
The shared-secret model means **every worker VM holds the signing key** — a single compromised VM can mint valid
internal tokens for the whole fleet. The Phase-4 connectivity work left an explicit seam for asymmetric auth.

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

### Phase 1 — Design + key provisioning
- [ ] [DESIGN] P2. Decide RS256 vs ES256 (ES256 = smaller keys/faster; RS256 = ubiquitous). Document key lifecycle:
      generation, storage (GCP KMS asymmetric key + S3/SM mirror for AWS fleet), rotation, and the dual-accept rollout
      window. Update `codex/04-architecture/agent-orchestrator-overview.md` § two-secret model. Collision group:
      `ao_asym_auth_design`. Est 0.4 AI-day.
- [ ] [SCRIPT] [OPERATOR] P2. Provision the asymmetric keypair: GCP KMS asymmetric-sign key (private, central-only) +
      publish the PUBLIC key to `gs://…/orchestrator/internal-public.pem` (+ S3 mirror). Est 0.2 AI-day.

### Phase 2 — Code: dual-accept verify + RS256 sign (single PR)
- [ ] [CODE] P2. `server/auth.py`: add RS256/ES256 signing (central, private key) + verification (public key). Verifier
      accepts BOTH HS256 (legacy) and RS256 during the window (try RS256, fall back to HS256). Env:
      `ORCHESTRATOR_INTERNAL_ALG` (HS256|RS256), `ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS`,
      `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS`. Unit tests: sign-RS256→verify-RS256, legacy-HS256 still verifies,
      worker-with-only-public-key CANNOT mint. QG green + quickmerge --agent. Collision group: `ao_asym_auth_code`.
      Est 0.7 AI-day.

### Phase 3 — Rollout (canary-first)
- [ ] [SCRIPT] P2. Per-VM systemd drop-in: workers get `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS` + `ALG=RS256`; central
      gets the private key + `ALG=RS256`. Canary central + one worker first; verify proxy calls succeed; then fleet.
      Reuse the `verify_fleet_autonomy_health.sh` pattern for confirmation. Collision group: `ao_asym_auth_rollout`.
      Est 0.3 AI-day.

### Phase 4 — Retire HS256
- [ ] [CODE] P2. After ≥48h of all-RS256 traffic with zero HS256-fallback hits (log-confirmed), drop the HS256 accept
      path + delete the shared `internal-secret` object. Update codex. Collision group: `ao_asym_auth_code`. Est 0.2
      AI-day.

## Closing condition
All proxy auth is RS256/ES256; no worker holds a signing key; HS256 shared-secret path removed; codex two-secret-model
doc updated; ≥48h clean RS256 traffic.

## Composes with
`codex/04-architecture/agent-orchestrator-overview.md` § "two-secret model" + the Phase-4 connectivity seam in
`server.py::proxy_to_vm`.
