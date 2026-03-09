# Tested and Deployable Gate Criteria

**Canonical reference:** plans_to_deployable_unified_audit.plan.md **Sprint:** Pre-first-deployment (batch → live →
testnet → real)

---

## Phase 9: Tested Gate

**Definition:** Code is Tested when quality gates and integration tests pass. CI is green.

### Explicit Criteria

| Criterion                                                  | Where                                             | Blocking        |
| ---------------------------------------------------------- | ------------------------------------------------- | --------------- |
| `bash scripts/quality-gates.sh --no-fix` passes            | Per repo                                          | Yes             |
| Unit tests pass (pytest tests/unit/)                       | Per repo                                          | Yes             |
| Layer 0: Contract alignment (AC↔UIC schemas)               | unified-api-contracts, unified-internal-contracts | Yes             |
| Layer 1: Schema robustness (test_schema_robustness.py)     | Per-service                                       | Yes             |
| Integration tests (if RUN_INTEGRATION=true)                | tests/integration/                                | Per-repo config |
| No blocking lint/type violations                           | ruff, basedpyright                                | Yes             |
| Required test files: test_event_logging.py, test_config.py | Services                                          | Yes             |

### Out of Scope (Post-Deploy)

- Layer 2: Infrastructure verification (GCP buckets, PubSub, IAM)
- Layer 3a: Smoke tests (system-integration-tests)
- Layer 3b: Full E2E (system-integration-tests)

---

## Phase 10: Deployable Gate

**Definition:** Code is Deployable when checklist is complete. Data availability verified, deployment stages passed,
data catalogue filled, recovery documented, security audit trails.

### Explicit Criteria (Checklist Phases 1–7)

| Phase | Name                      | Key Items                                                    |
| ----- | ------------------------- | ------------------------------------------------------------ |
| 1     | Repository Foundation     | pyproject, uv.lock, UnifiedCloudConfig, Dockerfile, setup.sh |
| 2     | Testing & Quality         | Unit tests, quality gates pass, cloudbuild.yaml              |
| 3     | Deployment Infrastructure | sharding config, dependencies.yaml, terraform, buckets       |
| 4     | Local Validation          | Runs locally, schema, timestamp/date alignment               |
| 5     | Production Deployment     | Image build, deployment, data completeness                   |
| 6     | Documentation             | README, architecture, schema, GCS paths                      |
| 7     | Data Catalogue            | data-catalogue.yaml, pipeline dependency chain               |

### Additional Items (per canonical plan)

| Item                 | Description                                     |
| -------------------- | ----------------------------------------------- |
| Data availability    | Input/output buckets exist; data paths verified |
| Gap-filling          | Empty gaps documented; recovery process defined |
| Recovery             | Recovery processes documented                   |
| Security audit trail | Audit trail for security-relevant actions       |

### SSOT

- **Checklists:** deployment-service/configs/checklist.{service}.yaml
- **Topology:** deployment-service/configs/runtime-topology.yaml
- **Decisions:** deployment-service/configs/RUNTIME_TOPOLOGY_DECISIONS.md

---

## Gate Order

Plans → Code → **Tested** → **Deployable** → Audit (A+)
