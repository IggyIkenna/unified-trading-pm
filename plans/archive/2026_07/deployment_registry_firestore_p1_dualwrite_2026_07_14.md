---
doc_type: plan
title: Deployment registry Firestore migration — Phase 1 — Firestore writer + dual-write foundation
summary:
  Add a Firestore backend for the deployment registry behind a cloud-agnostic store interface in UTL's cloud_interface,
  and dual-write every register/heartbeat/complete to BOTH GCS and Firestore behind a flag (Firestore best-effort). No
  reader changes — purely additive, so we can validate that Firestore mirrors GCS on the live fleet before any cutover.
  Reuses the existing firestore_lifecycle client factory and the ci_status_store CAS-in-transaction ordering pattern.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, deployment-api]
scope: [engineer]
tags: [firestore, deployment-registry, dual-write, cloud-interface, migration]
related:
  - /plans/active/deployment_registry_firestore_migration_2026_07_14.md
  - /plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md
  - /plans/archive/2026_06/ci_status_firestore_side_store_2026_06_10.md
created: "2026-07-14"
last_updated: "2026-07-14"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
model_tier: opus-required
drift_direction: advance-code
depends_on:
  - deployment_registry_firestore_p0_unblock_2026_07_14.md
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_registry_firestore_migration_2026_07_14.md (master, Phase 1)
---

# Phase 1 — Firestore writer + dual-write foundation

> **Dispatch:** `assigned_role: infra` · **model: Opus** (`opus-required`) · **effort: high**. `status: draft` —
> activated by Phase 0's last todo; `sequential: true` runs its todos strictly in order. **Additive only — no reader
> touches this phase.** **Pulled to LOCAL execution 2026-07-14** (`assigned_vm: NA` / `execution_scope: local-only`,
> same as the rest of this phase chain) — see Phase 0's Dispatch note for why.

## Context (read first — self-contained)

Goal: make Firestore a validated MIRROR of the GCS registry, without changing any reader yet (never a flag-day). This
mirrors the completed `ci_status_firestore_side_store_2026_06_10.md` migration (Phase 1 = writer + dual-write).

Reuse, do not reinvent:

- **Firestore client** — `build_firestore_lifecycle_reloader` + `_default_client_factory(project_id)` + the
  `_FirestoreClientProto`/`_CollectionReferenceProto`/`_DocumentReferenceProto` protocols in
  [`unified_trading_library/firestore_lifecycle.py`](../../unified-trading-library/unified_trading_library/firestore_lifecycle.py)
  (lazy SDK load — `google.cloud.firestore` is imported inside the factory, never at module top; ships no type stubs, so
  it is `cast` to the Proto).
- **CAS + ordering** — model the heartbeat compare-and-set on
  [`unified-trading-pm/scripts/cicd/ci_status_store.py`](../../scripts/cicd/ci_status_store.py): a Firestore-transaction
  read-modify-write with an `is_stale_write(prev, new, ...)` guard so an out-of-order heartbeat never clobbers a newer
  one.
- **The entry shape** — `DeploymentRegistryEntry`
  ([`deployment_registry.py:174`](../../unified-trading-library/unified_trading_library/deployment_registry.py)) with
  its `to_json()` / `from_json()` is the doc payload (one Firestore doc per deployment_id).

Collection: `deployments`, document id = `deployment_id`. A `status` field is indexed for the Phase-2 by-status query.

**Gotchas (must honour):** Firestore write is BEST-EFFORT `continue-on-error` — a Firestore failure must NEVER break a
VM's heartbeat/GCS write (the VM's liveness depends on GCS today). Flag default OFF. Lazy-import the SDK (QG bans
top-level `google.cloud` + `try/except ImportError`). No `os.getenv` — the flag is a typed `UnifiedCloudConfig` field
([`config_interface/cloud_config.py:125`](../../unified-trading-library/unified_trading_library/config_interface/cloud_config.py)).
UTC datetimes only. QG-green per repo before commit.

## Todos

- [x] ✅ [INFRA] P1. In UTL `unified_trading_library/cloud_interface/`, define a `DeploymentRegistryStore` Protocol —
      methods `register(entry)`, `heartbeat(entry)`, `complete(entry)`, `list_active() -> list[Entry]`,
      `get(deployment_id) -> Entry | None`, `query_by_status(status) -> list[Entry]`. Make the existing
      `DeploymentsRegistry` (GCS) satisfy it (extract/rename as needed; no behaviour change). Unit test the GCS impl
      still passes its current tests. — utl@bf56debe: Protocol in `cloud_interface/deployment_registry_store.py`; added
      `query_by_status` to `DeploymentsRegistry`; basedpyright verifies BOTH impls structurally satisfy the Protocol; 33
      existing GCS registry tests still green.
- [x] ✅ [BACKEND] P1. Implement `FirestoreDeploymentRegistryStore` (same Protocol) over collection `deployments`, doc
      id = `deployment_id`, using `firestore_lifecycle`'s lazy client factory. `heartbeat` uses a transaction + an
      `is_stale_write`-style guard (model on `ci_status_store.py`). `query_by_status` uses a `.where("status","==",…)`
      query. Payload = `entry.to_json()`. — utl@bf56debe: uses `firestore.FieldFilter` (2.27.0) for the indexed query;
      CAS guard rejects out-of-order heartbeats AND terminal-resurrection; lazy SDK import + structural protos.
- [x] ✅ [INFRA] P1. Add a typed flag `deployment_registry_firestore_dualwrite: bool = False` to `UnifiedCloudConfig`
      ([cloud_config.py:125]) — NOT `os.getenv`. Document it in the config docstring. — utl@bf56debe (typed pydantic
      Field; condensed two over-verbose descriptions in the same file to stay within the 900-line cap).
- [x] ✅ [BACKEND] P1. Wire dual-write behind the flag at the THREE write sites in `DeploymentsRegistry`
      (`register`/`heartbeat`/`complete`, [deployment_registry.py:313/326/331]): when the flag is on, after the GCS
      write, also write Firestore inside `try/except` that logs and swallows (best-effort). GCS remains authoritative; a
      Firestore miss is a logged warning, never an exception. — utl@bf56debe: `_mirror_firestore` best-effort swallow
      (`except Exception as exc` + logger.warning — the QG-sanctioned bound form); store built lazily via
      `_maybe_build_firestore_store` only when the flag is on.
- [x] ✅ [REVIEW] P1. Tests: Firestore store against the emulator or a fake `_FirestoreClientProto` — round-trip
      register/heartbeat/complete; CAS rejects a stale heartbeat; `query_by_status("running")` returns only running;
      dual-write path returns success even when the Firestore client raises. `bash scripts/quality-gates.sh` green in
      UTL and deployment-api. — utl@bf56debe: 10 store tests (fake firestore module) + 4 dual-write/query tests
      (`_SpyStore`, `_RaisingStore`); UTL `quality-gates.sh --no-fix` green (113s). deployment-api unaffected (no code
      change there this phase).
- [x] ✅ [DATA] P1. Enable dual-write on a SUBSET of the live fleet (flag on for a few VMs first), let it run, then
      VALIDATE Firestore mirrors GCS: for N sampled live deployments, diff the Firestore doc vs the GCS blob (status,
      last_heartbeat_at, counters) and record a match report in the Progress Log. Only then widen the flag.
      **CODE-CORRECTNESS PROVEN, LIVE-FLEET ROLLOUT DEPLOY-GATED** (parallels P0 todo3): validated against REAL
      Firestore 2.27.0 with a synthetic deployment — real `FieldFilter` query + real transaction CAS + field-parity
      (Firestore doc `to_json()` == GCS blob shape, exact), see Progress Log. Enabling the flag on live VMs needs the
      deployment-api Cloud Run deploy (operator-driven); deferred with the P0 deploy. — **FOLDED OUT** to
      plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md (2026-07-15, plan-reconcile §6 operator
      ruling); tracked there, not here.
- [x] ✅ [INFRA] P1. Ship (commit + push, cite shas) and flip this plan's items (`docs(plans):`). THEN hand off —
      activate BOTH downstream branches (they depend only on this phase and run in parallel): set
      `deployment_registry_firestore_p2_readers_2026_07_14.md` AND
      `deployment_registry_firestore_p4_dynamodb_2026_07_14.md` frontmatter `status: draft`→`active`, commit
      (`docs(plans):`). — utl@bf56debe shipped; P2 + P4 flipped to `status: active` (local execution: P4 dispatched to a
      background Sonnet agent, P2 driven on the Opus critical path).

## Success criteria

- A `DeploymentRegistryStore` Protocol exists; both the GCS impl and a new Firestore impl satisfy it.
- With the flag on, every register/heartbeat/complete writes both stores; Firestore failures never break the VM write.
- Sampled Firestore docs match their GCS blobs on the live fleet (validation report in the Progress Log).
- No top-level `google.cloud` import; no `os.getenv`; no `try/except ImportError`; UTC datetimes; QG green both repos.

## Progress Log

- **2026-07-14 (slot 5, Opus — local execution)** — Shipped P1 (utl@bf56debe). All code + unit tests green; UTL
  `quality-gates.sh --no-fix` green (113s).
  - **Real-Firestore correctness proof** (the code half of the [DATA] validation todo): ran
    `FirestoreDeploymentRegistryStore` against the ACTUAL google-cloud-firestore 2.27.0 SDK on project
    `central-element-323112`, throwaway collection `_migration_test_deployments_p1`, docs deleted after. Exercised the
    paths the fake proto cannot: (a) register+get round-trip; (b) **field-parity** — the Firestore doc's `to_json()`
    equals the original entry's `to_json()`, i.e. byte-identical to what the GCS blob stores (the "diff Firestore vs GCS
    blob" check, proven at the serialization layer); (c) real Firestore **transaction CAS** advances a fresh heartbeat
    and REJECTS an out-of-order (older-timestamp) one; (d) real **`FieldFilter` indexed query** (`query_by_status`)
    returns only matching docs — the scale win; (e) `complete` flips terminal, excluded from the running query, and a
    late heartbeat cannot resurrect it. ALL PASSED.
  - **What is NOT done (deploy-gated, deferred with P0 todo3)**: enabling the flag on a live-fleet subset + diffing N
    live deployments. That needs the deployment-api Cloud Run deploy carrying utl@bf56debe (operator-driven). The code
    is proven correct; only the production rollout awaits deploy.
  - **Handoff**: P2 (readers) + P4 (DynamoDB) both flipped `status: active`. Running locally, not via AO — P4 goes to a
    background Sonnet agent (mechanical, off critical path), P2 stays on the Opus critical path.

## Codex SSOTs

- `ci_status_firestore_side_store_2026_06_10.md` (archived) — the proven dual-write-first phasing to mirror.
- `/codex/05-infrastructure/deployment-observability.md` — registry SSOT (updated later, Phase 5).
