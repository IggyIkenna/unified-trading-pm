# Documentation Gap Report — 2026-03-08

Audit scope: S5.1 (service-canonical) and S5.2 (library-canonical) required documentation. Audit date: 2026-03-09.
Auditor: Claude Code (automated check via file existence + line-count stub detection).

Legend: **P** = Present | **M** = Missing | **S(n)** = Stub (n lines or fewer)

---

## Service Repos (S5.1 — 8 required docs)

| Repo                              | README | ARCHITECTURE | CONFIGURATION | GCS_PATHS | DEPLOYMENT | TESTING | SCHEMA_VAL | BYPASS_AUDIT |
| --------------------------------- | ------ | ------------ | ------------- | --------- | ---------- | ------- | ---------- | ------------ |
| alerting-service                  | P      | P            | P             | P         | P          | P       | P          | P            |
| client-reporting-api              | P      | P            | P             | P         | P          | P       | P          | P            |
| deployment-api                    | P      | P            | P             | P         | P          | P       | P          | P            |
| deployment-service                | P      | P            | P             | P         | P          | P       | P          | P            |
| execution-results-api             | P      | P            | P             | P         | P          | P       | P          | P            |
| execution-service                 | P      | P            | P             | P         | P          | P       | P          | P            |
| features-calendar-service         | P      | P            | P             | P         | P          | P       | P          | P            |
| features-commodity-service        | P      | P            | P             | P         | P          | P       | P          | P            |
| features-cross-instrument-service | P      | P            | P             | P         | P          | P       | P          | P            |
| features-delta-one-service        | P      | P            | P             | P         | P          | P       | P          | P            |
| features-multi-timeframe-service  | P      | P            | P             | P         | P          | P       | P          | P            |
| features-onchain-service          | P      | P            | P             | P         | P          | P       | P          | P            |
| features-sports-service           | P      | P            | P             | P         | P          | P       | P          | P            |
| features-volatility-service       | P      | P            | P             | P         | P          | P       | P          | P            |
| instruments-service               | P      | P            | P             | P         | P          | P       | P          | P            |
| market-data-api                   | P      | P            | P             | P         | P          | P       | P          | P            |
| market-data-processing-service    | P      | P            | P             | P         | P          | P       | P          | P            |
| market-tick-data-service          | P      | P            | P             | P         | P          | P       | P          | P            |
| ml-inference-service              | P      | P            | P             | P         | P          | P       | P          | P            |
| ml-training-service               | P      | P            | P             | P         | P          | P       | P          | P            |
| pnl-attribution-service           | P      | P            | P             | P         | P          | P       | P          | P            |
| position-balance-monitor-service  | P      | P            | P             | P         | P          | P       | P          | P            |
| risk-and-exposure-service         | P      | P            | P             | P         | P          | P       | P          | P            |
| strategy-service                  | P      | P            | P             | P         | P          | P       | P          | P            |
| strategy-validation-service       | P      | P            | P             | P         | P          | P       | P          | P            |
| trading-agent-service             | P      | P            | P             | P         | P          | P       | P          | P            |

**Service repos total:** 26 audited | **0 missing files** | **0 stub files**

All 26 service repos are fully compliant with S5.1 requirements.

---

## Library Repos (S5.2 — 5 required docs)

| Repo                               | README | ARCHITECTURE | CONFIGURATION | TESTING | BYPASS_AUDIT |
| ---------------------------------- | ------ | ------------ | ------------- | ------- | ------------ |
| execution-algo-library             | P      | **M**        | **M**         | **M**   | P            |
| matching-engine-library            | P      | P            | P             | P       | P            |
| unified-api-contracts              | P      | P            | P             | P       | P            |
| unified-cloud-interface            | P      | P            | P             | P       | P            |
| unified-config-interface           | P      | P            | P             | P       | P            |
| unified-defi-execution-interface   | P      | P            | P             | P       | P            |
| unified-domain-client              | P      | P            | P             | P       | P            |
| unified-events-interface           | P      | P            | P             | P       | P            |
| unified-feature-calculator-library | P      | P            | P             | P       | P            |
| unified-internal-contracts         | P      | P            | P             | P       | P            |
| unified-market-interface           | P      | P            | P             | P       | P            |
| unified-ml-interface               | P      | P            | P             | P       | P            |
| unified-position-interface         | P      | P            | P             | P       | P            |
| unified-reference-data-interface   | P      | P            | P             | P       | P            |
| unified-sports-execution-interface | P      | **M**        | **M**         | **M**   | P            |
| unified-trade-execution-interface  | P      | P            | P             | P       | P            |
| unified-trading-library            | P      | P            | P             | P       | P            |

**Library repos total:** 17 audited | **6 missing files** across 2 repos | **0 stub files**

### Library gap detail

| Repo                               | Missing docs                                                 |
| ---------------------------------- | ------------------------------------------------------------ |
| execution-algo-library             | docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/TESTING.md |
| unified-sports-execution-interface | docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/TESTING.md |

---

## Summary

| Category             | Repos Audited | Fully Compliant | Repos With Gaps | Total Missing Files |
| -------------------- | ------------- | --------------- | --------------- | ------------------- |
| Service repos (S5.1) | 26            | 26 (100%)       | 0               | 0                   |
| Library repos (S5.2) | 17            | 15 (88%)        | 2               | 6                   |
| **Total**            | **43**        | **41 (95%)**    | **2**           | **6**               |

### Critical gaps (missing from >5 service repos)

**None.** All service repos are fully compliant. No doc type is missing from more than zero service repos.

### High-priority library gaps

The following library repos are missing 3 of 5 required docs each. Stub files have been created:

- `execution-algo-library` — docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/TESTING.md
- `unified-sports-execution-interface` — docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/TESTING.md

Stub files created at paths listed above. These stubs count as in-progress (not yet PRESENT for audit gate S5.4
purposes). Full content must be authored before these repos pass the library-canonical gate.

---

## Next Steps

1. Author real content for 6 stub files in execution-algo-library and unified-sports-execution-interface (todo:
   `docs-fill-library-gaps`)
2. Run stub-expansion pass (todo: `docs-stub-check`) to verify all existing PRESENT docs meet minimum content standards
3. Run hardcoded-ID scan (todo: `docs-no-hardcoded-ids`) across all docs/ directories
