---
pair: agent-orchestrator → all services
auditor: ikenna-slot-4
audit_date: 2026-05-20
audit_file: plans/audit/orchestrator_service_contract_audit_2026_05_20.md
feeds_ordering_step: D0 (orchestrator migration plan)
status: complete
upstream_sha: 0c2e32a66e3b82fb3685678439d529e09b8ad762
---

# C11 — Contract Audit: agent-orchestrator → all services

> **Scope note**: agent-orchestrator is operator tooling, NOT a trading service. The codex explicitly documents this in
> `/codex/04-architecture/agent-orchestrator-overview.md` § "Difference vs trading services". Standard trading-service
> contract patterns (Pattern 2–7 as written in the B1 template) do NOT apply to the orchestrator's own handlers.
> However, several structural concerns specific to the orchestrator→services relationship exist and are audited here via
> adapted patterns.

---

## 0. Audit context

```
upstream repo:   agent-orchestrator (IggyIkenna/agent-orchestrator)
upstream sha:    0c2e32a66e3b82fb3685678439d529e09b8ad762
downstream:      all services (the orchestrator dispatches work to service repos via worker agents)
audit date:      2026-05-20
auditor:         ikenna-slot-4
```

**Key architectural fact**: agent-orchestrator does NOT call any service API or health endpoint directly. It coordinates
Claude Code worker agents via a REST API (`/boot`, `/heartbeat`, `/progress`, `/done`, `/blocked`). Workers operate on
the service repos locally (git, tmux sessions). The orchestrator's relationship to "all services" is therefore:

1. **Topology correctness** — does the backlog/config correctly reference service names that exist?
2. **Port/URL governance** — are hardcoded ports/URLs consistent with the workspace port registry?
3. **Service bootstrap compliance** — does the orchestrator itself meet QG 5.61/5.62 standards?
4. **Legacy topology gap** — are there remnants of the pre-consolidation 3-service topology?
5. **GCS/bucket-SSOT adherence** — does orchestrator's own GCS usage follow workspace rules?

---

## 4-dimensional audit matrix (adapted for orchestrator)

| Dim   | What it measures                                                                | Status        |
| ----- | ------------------------------------------------------------------------------- | ------------- |
| Dim 1 | Orchestrator service-topology correctness (no legacy names, no stale endpoints) | See Pattern 1 |
| Dim 2 | Port/URL governance — hardcoded vs config-driven                                | See Pattern 2 |
| Dim 3 | Service bootstrap compliance (QG 5.61/5.62)                                     | See Pattern 3 |
| Dim 4 | GCS/bucket SSOT adherence                                                       | See Pattern 4 |

---

## Pattern 1 — Service-topology correctness

### What this pattern governs

Does the orchestrator reference the correct consolidated service names? Pre-consolidation topology split into
`risk-and-exposure-service`, `position-balance-service`, `pnl-attribution-service` as separate repos. Post-consolidation
these merged into `strategy-service`.

### Audit evidence

```bash
rg 'risk-and-exposure\|position-balance\|pnl-attribution' agent-orchestrator/ --glob '*.py'
# → (no output)

rg 'risk-and-exposure\|position-balance\|pnl-attribution' agent-orchestrator/ --glob '*.yaml'
# → (no output)

rg 'risk-and-exposure\|position-balance\|pnl-attribution' agent-orchestrator/ --glob '*.json'
# → (no output)
```

### Dim 1 — Service topology per backlog/config

| Legacy name           | Occurrences                               | Status |
| --------------------- | ----------------------------------------- | ------ |
| `risk-and-exposure`   | 0                                         | CLEAN  |
| `position-balance`    | 0                                         | CLEAN  |
| `pnl-attribution`     | 0                                         | CLEAN  |
| `strategy-service`    | mentioned in backlog tasks (correct name) | CLEAN  |
| `instruments-service` | mentioned in backlog tasks (correct name) | CLEAN  |
| `deployment-service`  | mentioned in backlog tasks (correct name) | CLEAN  |

**Verdict: CLEAN.** No legacy pre-consolidation service names found in Python, YAML, or JSON config files. The
orchestrator uses task titles and brief text in `backlog.yaml` to reference services; these use the correct consolidated
names.

**Note**: orchestrator dispatches work by repo-name (e.g. `repos: ["strategy-service"]` in backlog tasks). This is
purely a string label used for collision-detection — not a URL or health endpoint lookup. No direct service API calls
exist.

---

## Pattern 2 — Port/URL governance

### What this pattern governs

Hardcoded ports and localhost URLs in code should match the workspace port registry
(`unified-trading-pm/scripts/dev/ui-api-mapping.json`). Hardcoded CORS origins should cover the actual dev/prod URLs.

### Audit evidence

```bash
# Hardcoded ports/localhost references in server code:
grep -n 'localhost\|127\.' server/server.py
# → Line 158-161: CORS allow_origins hardcoded to localhost:5173 and localhost:8765

grep -n 'port=8765' server/server.py
# → Line 2269: uvicorn.run(..., port=8765, ...)

# Workspace port registry for agent-orchestrator:
cat unified-trading-pm/scripts/dev/ui-api-mapping.json | grep -A5 'agent-orchestrator'
# → "port": 8026
```

### Dim 2 — Hardcoded port/URL findings

| Location                                           | Value                              | Status     | Notes                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------- | ---------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `server/server.py:2269` — `uvicorn.run(port=8765)` | `8765`                             | P2 GAP     | Workspace port registry says `8026`. Dockerfile comment notes both: "Local dev uses uvicorn directly (port 8765 in scripts/dev.sh, or 8026 per ui-api-mapping.json)". The `main()` function is rarely called (uvicorn is invoked directly in all deployment scripts). Low severity since `main()` is a fallback, not the production path.                                   |
| `server/server.py:157-162` — CORS `allow_origins`  | `localhost:5173`, `localhost:8765` | P2 GAP     | Production domains `agent-orchestrator.odum-research.com` and `agent-orchestrator.staging.odum-research.com` are MISSING from CORS. Firebase Hosting proxies the dashboard and API on the same origin in production (no cross-origin request needed), so the missing prod domains are currently harmless — but this is architecturally fragile if deployment shape changes. |
| `scripts/dev.sh:61,139,151,171`                    | `8765`                             | ACCEPTABLE | Dev script explicitly uses 8765; comment in Dockerfile explains the dual-port situation. Operationally consistent.                                                                                                                                                                                                                                                          |
| `data/config/backends.mock.json:backend.url`       | `http://localhost:8765`            | ACCEPTABLE | Only used in mock/dev mode; labeled "mock".                                                                                                                                                                                                                                                                                                                                 |
| `data/config/backends.json:demo.url`               | `/demo`                            | CLEAN      | Same-origin path, not hardcoded host.                                                                                                                                                                                                                                                                                                                                       |

**Verdict: 2 GAPS (P2 severity, not P0).**

1. `uvicorn.run(port=8765)` in `main()` diverges from workspace port registry `8026`. Should either use
   `int(os.environ.get("PORT", 8026))` or update the registry. The registry wins as SSOT per CLAUDE.md.

2. CORS `allow_origins` misses production + staging Firebase Hosting domains. Harmless today due to same-origin Firebase
   proxy but should be added for correctness.

---

## Pattern 3 — Service bootstrap compliance

### What this pattern governs

QG STEP 5.61 (`ServiceBootstrap`) and QG STEP 5.62 (`make_health_router`) compliance.

### Audit evidence

```bash
rg 'ServiceBootstrap' agent-orchestrator/ --glob '*.py'
# → (no output) — not used

rg 'make_health_router' agent-orchestrator/ --glob '*.py'
# → server/server.py:26: from unified_trading_library import make_health_router
# → server/server.py:205: make_health_router(...)
```

From `server/server.py:204-212`:

```python
app.include_router(
    make_health_router(
        service_name="agent-orchestrator",
        version="0.6.0",
        readiness_check=_readiness_check,
        data_freshness=_data_freshness,
        mock_mode=config.is_mock(),
    )
)
```

### Dim 3 — Bootstrap compliance

| QG step                            | Required   | Status            | Notes                                                                                                            |
| ---------------------------------- | ---------- | ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| STEP 5.61 — ServiceBootstrap       | ❌ Exempt  | OPERATOR-EXEMPTED | Documented exemption in codex. Orchestrator has no `--asset-group`/`--mode` trading CLI.                         |
| STEP 5.62 — make_health_router     | ✅ Applied | COMPLIANT         | `make_health_router` from UTL with `data_freshness` + `readiness_check` callbacks.                               |
| STEP 5.34 — typed config_reloaders | ❌ Exempt  | OPERATOR-EXEMPTED | Documented exemption. `server/config.py` uses env-driven functions; config-class refactor deferred post-cutover. |

**Verdict: COMPLIANT (with documented exemptions).**

`/health` and `/readiness` endpoints are live. The `_data_freshness` callback reports state.json mtime + DB/backlog
checks. The `_readiness_check` callback probes SQLite + backlog. Both per QG STEP 5.62 requirements.

ServiceBootstrap exemption is correctly documented in:

- `/codex/04-architecture/agent-orchestrator-overview.md` § "Service bootstrap exemptions"
- `/codex/04-architecture/agent-orchestrator-overview.md` table § "Difference vs trading services"

---

## Pattern 4 — GCS / bucket-SSOT adherence

### What this pattern governs

QG STEP 5.69 (`resolve_bucket_name`). Every GCS bucket reference should go through
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`. Inline `gs://` f-strings are banned.

### Audit evidence

```bash
rg '"gs://' agent-orchestrator/ --glob '*.py'
# → server/gcs_sync.py:97: gs_uri = f"gs://{bucket_name}/{blob_path}"

rg 'resolve_bucket_name' agent-orchestrator/ --glob '*.py'
# → (no output)
```

From `server/gcs_sync.py:82-97`:

```python
def gcs_bucket_name() -> str | None:
    return os.environ.get("ORCHESTRATOR_GCS_BUCKET")

def upload_state_to_gcs(state: dict[str, Any]) -> str | None:
    bucket_name = gcs_bucket_name()
    if not bucket_name:
        return None
    ...
    gs_uri = f"gs://{bucket_name}/{blob_path}"
    ...
    return gs_uri
```

### Dim 4 — Bucket-SSOT status

| Location                                                       | Finding                                                            | Status         |
| -------------------------------------------------------------- | ------------------------------------------------------------------ | -------------- |
| `gcs_sync.py:82` — `os.environ.get("ORCHESTRATOR_GCS_BUCKET")` | Bucket name from env var, not from `resolve_bucket_name(...)`      | P3 GAP         |
| `gcs_sync.py:97` — `f"gs://{bucket_name}/{blob_path}"`         | f-string URI construction (log message only — not a bucket lookup) | ACCEPTABLE-LOG |

**Verdict: 1 P3 GAP.**

The orchestrator GCS bucket is sourced from `os.environ.get("ORCHESTRATOR_GCS_BUCKET")` rather than
`resolve_bucket_name(...)`. Per workspace rules, every bucket lookup must go through `resolve_bucket_name(...)` with
`deployment-service/configs/cloud-providers.yaml` as canonical.

**Mitigating context**: the orchestrator is operator tooling, not a trading service. It has a single GCS bucket (session
state backup), not the multi-bucket, multi-asset-group pattern that `resolve_bucket_name()` was designed for. The
current pattern is architecturally simpler and lower-risk than the trading service case. The `f"gs://..."` string on
line 97 is only used to construct a log message after the upload — not for bucket lookup.

**Recommendation**: add `agent-orchestrator-state-prod` to `cloud-providers.yaml` under a new `agent-orchestrator`
namespace and wire `resolve_bucket_name("agent-orchestrator", "state")`. This makes the bucket registry exhaustive (all
GCS buckets in one place) and satisfies QG STEP 5.69. Medium priority — not blocking May-23 gate.

---

## QG-ratchet phase

### Phase Q — gaps that need QG enforcement

| Pattern                        | Current gap                                                            | Recommended QG action                                                                             | Priority |
| ------------------------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | -------- |
| P2 — Port governance           | `uvicorn.run(port=8765)` vs port registry `8026`                       | Wire `PORT` env var check into `scripts/check.sh`                                                 | P3       |
| P2 — CORS missing prod domains | `allow_origins` lacks `*.odum-research.com`                            | Add to `allow_origins` list; no QG gate needed                                                    | P2       |
| P4 — Bucket SSOT               | `os.environ.get("ORCHESTRATOR_GCS_BUCKET")` vs `resolve_bucket_name()` | Add bucket to `cloud-providers.yaml` + wire `resolve_bucket_name`; QG STEP 5.69 will auto-enforce | P3       |

**No P0 findings.** The 3 gaps are P2/P3 correctness improvements, not blocking issues.

---

## Continuous-verification column

| Pattern                       | Continuous-verification path                                                               | Cadence                  | Last verified    |
| ----------------------------- | ------------------------------------------------------------------------------------------ | ------------------------ | ---------------- |
| P1 — Topology correctness     | `backlog.yaml` has no service-name refs that need URL lookup — no QG step needed           | n/a                      | 2026-05-20 audit |
| P2 — Port governance          | Manual review on port registry changes                                                     | per port-registry update | 2026-05-20       |
| P3 — Service bootstrap (5.62) | `/health` + `/readiness` probes in Cloud Run (heartbeat)                                   | Cloud Run uptime check   | live             |
| P4 — Bucket SSOT              | `check_inline_bucket_uri.py` (STEP 5.69) will enforce once cloud-providers.yaml is updated | every push               | not wired yet    |

---

## Scope exclusions (verified clean)

The following B1 template patterns are **NOT APPLICABLE** to the orchestrator→services pair and are documented as clean:

- **Pattern 2 (Manifest emission discipline)**: agent-orchestrator is not a data pipeline service. It does not write
  market-data manifests. No `record_captured`/`record_empty` calls exist or should exist.

- **Pattern 3 (Schema-version compliance)**: no manifest index parquets. Not applicable.

- **Pattern 4 (Honest-absence reason taxonomy)**: no `record_empty()` calls. Not applicable.

- **Pattern 5 (expected_coverage() preflight)**: no data coverage logic. Not applicable.

- **Pattern 6 (Error classification at boundary)**: the orchestrator uses a custom health-monitor with a `HealthMonitor`
  background thread (not UAC `classify_venue_error()`). This is correct for operator tooling — it monitors Claude Code
  worker liveness, not venue API calls.

---

## Summary of findings

| Severity | Finding                                                                                                                          | File                 | Line    | Action                                                                                                     |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| P0       | None                                                                                                                             | —                    | —       | —                                                                                                          |
| P1       | None                                                                                                                             | —                    | —       | —                                                                                                          |
| P2       | CORS `allow_origins` missing prod/staging Firebase Hosting domains                                                               | `server/server.py`   | 157-162 | Add `https://agent-orchestrator.odum-research.com`, `https://agent-orchestrator.staging.odum-research.com` |
| P2       | `uvicorn.run(port=8765)` diverges from workspace port registry (`8026`)                                                          | `server/server.py`   | 2269    | Read `int(os.environ.get("PORT", 8026))` — Dockerfile already sets PORT=8080 for Cloud Run                 |
| P3       | GCS bucket sourced from `os.environ.get()` not `resolve_bucket_name()`                                                           | `server/gcs_sync.py` | 82      | Add to `cloud-providers.yaml`; wire `resolve_bucket_name()`                                                |
| INFO     | Dual-port convention (8765 dev / 8026 registry / 8080 Cloud Run) documented in Dockerfile but not surfaced in `server/server.py` | `server/server.py`   | 3       | Docstring clarification                                                                                    |

**Total P0 findings: 0** **Total P1 findings: 0** **Total P2 findings: 2** **Total P3 findings: 1**

---

## Phased remediation DAG

```
Phase 1 — CORS + port hardening (P2 items — low effort)
   server/server.py:
     - allow_origins += prod/staging Firebase Hosting domains
     - uvicorn.run port=8765 → int(os.environ.get("PORT", 8026))

Phase 2 — Bucket SSOT (P3 item — requires cloud-providers.yaml update)
   deployment-service/configs/cloud-providers.yaml:
     - add agent-orchestrator namespace + state bucket
   agent-orchestrator/server/gcs_sync.py:
     - replace os.environ.get("ORCHESTRATOR_GCS_BUCKET") with resolve_bucket_name(...)

Phase Q — QG enforcement
   - Once Phase 2 lands, STEP 5.69 auto-enforces via check_inline_bucket_uri.py
   - Port divergence: optional inline check in scripts/check.sh
```

Foundation-completion-gate: Phases 1 and 2 are independent of all trading-service data gates. They may ship at any time
— no blocking dependency on DeFi/TradFi pipeline work.

---

## Temporary states + canonical follow-up plans

- **Dual-port convention (8765/8026/8080)**: documented in Dockerfile comment. Permanent state until a dev-start wrapper
  fully reads `PORT` env. Named successor: `Phase 1` above.
- **CORS localhost-only**: safe while Firebase Hosting is the production delivery mechanism (same-origin proxy
  eliminates browser CORS check). Named successor: `Phase 1` above.
- **`ORCHESTRATOR_GCS_BUCKET` env var**: current operational state; bucket is set in Cloud Run `--set-env-vars` at
  deploy time. Named successor: `Phase 2` above.

---

## D0 feed — migration plan seed

The following items feed the D0 orchestrator migration plan:

- [ ] **D0.1** P2. Add prod/staging Firebase Hosting origins to CORS `allow_origins` in `server/server.py`. Files:
      `agent-orchestrator/server/server.py`.

- [ ] **D0.2** P2. Fix `uvicorn.run(port=8765)` to read `PORT` env var with fallback matching workspace port registry.
      Files: `agent-orchestrator/server/server.py`.

- [ ] **D0.3** P3. Register orchestrator GCS state bucket in `deployment-service/configs/cloud-providers.yaml`
  - wire `resolve_bucket_name()` in `gcs_sync.py`. Files: `deployment-service/configs/cloud-providers.yaml`,
    `agent-orchestrator/server/gcs_sync.py`.

- [ ] **D0.4** INFO. Add port clarification comment to `server/server.py` module docstring (8765 dev / 8026 registry /
      8080 Cloud Run). Files: `agent-orchestrator/server/server.py`.
