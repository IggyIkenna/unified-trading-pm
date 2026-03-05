# E2E and Smoke Test Plan (Pre-Deployment)

**Reference:** [E2E_TESTING_GUIDE_2026-02-17.md](../archive/E2E_TESTING_GUIDE_2026-02-17.md) (archived)
**SSOT:** system-integration-tests/README.md, unified-trading-codex integration-testing-layers.md

---

## Integration Layers

| Layer | Where                                 | Credentials   | In quickmerge? | Blocks             |
| ----- | ------------------------------------- | ------------- | -------------- | ------------------ |
| 0     | AC, UIC                               | None          | Yes            | Contract alignment |
| 1     | Per-service test_schema_robustness.py | None          | Yes            | Schema robustness  |
| 2     | deployment-service verify_infra.py    | GCP read-only | Post-deploy    | First deployment   |
| 3a    | system-integration-tests/tests/smoke/ | GCP sandbox   | Post-deploy    | First deployment   |
| 3b    | system-integration-tests/tests/e2e/   | GCP sandbox   | Post-deploy    | First deployment   |

**Layer 0–1 block quickmerge.** Layer 2–3 block first deployment.

---

## Internal Contracts Only

**Rule:** system-integration-tests uses **internal contracts (UIC)** only. No external API keys. Tests hit services via HTTP; validate responses against UIC schemas where applicable.

| Allowed                       | Not allowed                                 |
| ----------------------------- | ------------------------------------------- |
| HTTP to service endpoints     | Direct API keys for Tardis, Databento, etc. |
| UIC schema validation         | VCR replay (lives in interfaces)            |
| GCP sandbox (buckets, PubSub) | Live external API calls                     |

---

## Current system-integration-tests Structure

```
tests/
  smoke/           # Layer 3a — happy path, health checks
  e2e/             # Layer 3b — full e2e, auth, multi-date
```

**Run:** `pytest -m smoke -v` (Layer 3a), `pytest -m full_e2e -v` (Layer 3b)

---

## Sprint Scope

1. **Expand Layer 3a:** Add schema round-trip test using UIC (e.g. validate instruments response against UIC schema)
2. **cloudbuild.yaml:** Add if missing (per workspace-completion-plan)
3. **Document:** Layer 0–1 in quickmerge; Layer 2–3 as pre-deployment gate
