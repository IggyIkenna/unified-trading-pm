---
scope: [engineer, admin, on-call]
---

# Smoke Testing Playbook — Institutional Smoke Matrix

**Purpose:** Operational SSOT for running, reading, and recovering from the institutional smoke matrix. Every (service ×
category × data_type × venue) cell is executed against TEST buckets with `IS_TEST_RUN=true` + `--max-results 1` on a
nightly cadence (02:00 UTC) and on-demand. Pass/fail of the most recent run gates production deployments.

**Plan SSOT:** `unified-trading-pm/plans/active/institutional_smoke_matrix_2026_04_20.plan.md`

**Orchestrator:** `deployment-service/scripts/run-smoke-matrix.sh` (commit `df7e716`). Per-service smoke scripts live at
`<service>/scripts/smoke_matrix.py` (see § Related documents).

---

## 1. When to run

| Trigger                                    | How                                                                                                              | Why                                                                                                              |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Daily (automated)                          | GHA `nightly-smoke-matrix.yml` at 02:00 UTC                                                                      | Catches overnight venue API breakage, schema drift, silent path regressions.                                     |
| Pre-release (before prod merge)            | Manual `workflow_dispatch` of `nightly-smoke-matrix.yml`                                                         | Gates promotion of a PR batch from staging → main. A red smoke matrix MUST block the merge.                      |
| Post-incident (sev1 or data corruption)    | Local: `bash deployment-service/scripts/run-smoke-matrix.sh`                                                     | Verifies recovery is clean before un-pausing the pipeline. Pair with `--cleanup` to wipe stale TEST state first. |
| After schema change (UAC/UTL/UCI/UEI bump) | Local or GHA dispatch                                                                                            | Smoke exercises canonical schemas end-to-end via real adapters; unit tests cannot catch wire-format drift.       |
| On-demand for one cell                     | `bash deployment-service/scripts/run-smoke-matrix.sh --service X --category Y --venue Z --data-type W --no-deps` | Triage a single failing cell without re-running the full 510-cell matrix.                                        |

---

## 2. How to read the output

### 2.1 Tiered summary (stdout)

The orchestrator prints a per-tier breakdown followed by TOTAL:

```
Tier 0 (instruments-service): 510 cells -> 489 PASS, 0 FAIL, 21 SKIP
Tier 1 (market-tick-data-service): 510 cells -> 498 PASS, 2 FAIL, 10 SKIP
Tier 2 (market-data-processing-service): 109 cells -> 103 PASS, 0 FAIL, 6 SKIP
Tier 3 parallel:
  features-delta-one-service: 4 cells -> 4 PASS, 0 FAIL, 0 SKIP
  features-volatility-service: 2 cells -> 2 PASS, 0 FAIL, 0 SKIP
  ...
=========================
TOTAL: 1146 cells | 1125 PASS | 2 FAIL | 19 SKIP
Exit: 1
```

### 2.2 summary.json schema

The orchestrator writes `${REPORT_DIR}/summary.json`:

```json
{
  "services": [
    { "service": "instruments-service", "total": 510, "passed": 489, "failed": 0, "skipped": 21 },
    { "service": "market-tick-data-service", "total": 510, "passed": 498, "failed": 2, "skipped": 10 }
  ],
  "total": 1146,
  "passed": 1125,
  "failed": 2,
  "skipped": 19,
  "exit_code": 1
}
```

Per-service per-cell details live alongside in `${REPORT_DIR}/<service>.json` using one of two schemas (both aggregated
transparently by the orchestrator):

- **Schema A** — instruments / MTDS / MDPS:
  `{service, total_cells, passed, failed, skipped, results: [{category, venue, data_type, status, ...}]}`
- **Schema B** — features-\*: `{service, cells: [{category, data_type, status, ...}]}`

Per-cell `status` is always one of `PASS`, `FAIL`, `SKIP`.

### 2.3 PASS vs FAIL vs SKIP semantics

| Status | Meaning                                                                                                                                                                                                                                          |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PASS   | The 3-step assertion contract held: (1) CLI ran, (2) parquet written to the TEST bucket, (3) TEST manifest row exists with `capture_status ∈ {captured, empty_confirmed}`. `empty_confirmed` (legitimate-zero-rows shard) IS a pass, not a skip. |
| FAIL   | A real error occurred. Expect non-empty `error_reason` on the manifest row (`capture_status=attempted_failed`). Investigate per § 3.                                                                                                             |
| SKIP   | Deliberately skipped. Sub-reasons (see per-cell JSON):                                                                                                                                                                                           |
|        | - `dry_run` — the matrix was run with `--dry-run`; no CLI invoked.                                                                                                                                                                               |
|        | - `upstream_missing` — prior tier's TEST bucket is empty (run the matrix top-down without `--no-deps`).                                                                                                                                          |
|        | - `api_football_missing` — a sports T1 cell ran before `api-football` T0 populated the date; Phase 3 enforcement. Remediation is printed in the per-cell error (see § 3 below).                                                                  |
|        | - `architecturally_unsupported` — UAC declares this (category × venue × data_type) cell invalid; the cell exists only to surface gaps in the CLI plan.                                                                                           |

A SKIP is **not** a pass. Floor enforcement (`enforce-smoke-coverage-floor.py`) counts only `passed`, never `skipped`.

---

## 3. Common failure modes + recipes

### 3.1 TEST bucket not provisioned

**Symptom:** FAIL with `error_reason` containing `404`, `BucketNotFoundError`, or `Forbidden` against
`gs://<service>-store-<cat>-test-<project-id>/`.

**Fix:**

```bash
bash deployment-service/scripts/provision-test-buckets.sh
bash deployment-service/scripts/verify-test-bucket-lifecycle.sh
```

Both scripts are idempotent. `verify-test-bucket-lifecycle.sh` confirms the 7-day auto-delete policy is in place (see
`configs/test-bucket-lifecycle.json`).

### 3.2 IS_TEST_RUN not propagated

**Symptom:** FAIL or — worse — data written to PROD bucket during a smoke run. Per-cell log contains a write URL without
`-test-` in the bucket name.

**Fix:** Audit the service config. Every config object MUST expose `is_test_run()` (or equivalent) wired to the
`IS_TEST_RUN` env var, and the GCS resolver MUST route to the `-test-` suffix when true. SSOT for which services were
audited + fixed: `codex/02-data/is-test-run-audit-2026-04-20.md` (Phase 1 of the institutional-smoke-matrix plan — 11
services propagated 2026-04-20; MTDS pre-existing).

Common root causes:

- Service config uses a hard-coded bucket name (not templated on category).
- `env_substitutor` misses the test-suffix branch.
- Dep-checker bypassed the test_mode (auto-triggered from `IS_TEST_RUN=true` since
  `market-data-processing-service@9e7cfa8`; if MDPS still writes to PROD, audit `cli/parser.py` + `DependencyChecker`).

### 3.3 Dep cascade broken (upstream_missing)

**Symptom:** A downstream tier reports bulk `skipped=upstream_missing`. MDPS can't run because MTDS didn't write.
features-\* can't run because MDPS didn't write. The matrix cannot make progress because one tier is wedged.

**Fix:** Run from Tier 0 in isolation, inspect, then re-cascade:

```bash
# Step 1: Tier 0 alone
bash deployment-service/scripts/run-smoke-matrix.sh \
    --service instruments-service \
    --no-deps --report-dir /tmp/smoke-t0

# Step 2: Verify parquet landed in -test- buckets
gsutil ls gs://instruments-store-cefi-test-<project-id>/instrument_availability/

# Step 3: Tier 1
bash deployment-service/scripts/run-smoke-matrix.sh \
    --service market-tick-data-service --no-deps --report-dir /tmp/smoke-t1

# ... etc per tier. Full matrix resumes once each tier is clean.
```

Dep graph SSOT: `deployment-service/configs/dependencies.yaml` (execution order is hard-coded in the orchestrator
mirroring this file).

### 3.4 api-football missing for SPORTS cells

**Symptom:** Sports T1 adapters (footystats / SFI / Understat / transfermarkt / open_meteo / betfair) fail with
`DependencyError: api-football reference data missing for date X`. Phase 3 of the plan makes this a pre-flight raise,
not a silent empty result.

**Fix:** Run the remediation CLI printed in the error message verbatim:

```bash
python -m instruments_service \
    --operation instruments --mode batch \
    --category SPORTS --sports-provider API_FOOTBALL \
    --start-date <date> --end-date <date>
```

Then re-run the failing cell. Sports internal-ordering SSOT: `codex/02-data/sports-adapter-dependency-order.md`.
Enforcement lives in `instruments-service/instruments_service/reference_data/sports_dependency.py`.

### 3.5 Rate limit on venue API

**Symptom:** Repeated FAIL with `error_code` like `RATE_LIMIT_EXCEEDED`, `429`, or venue-specific quota errors (Tardis,
RapidAPI, SFI, etc.). Often clusters at the same wall-clock time.

**Fix:**

1. Check `classify_venue_error()` in UAC for the mapped `error_code` + `action` (`retry_safe?`, backoff).
2. For Tardis specifically: `--max-results 1` should not be hitting per-IP quota; if it is, another agent is running
   concurrently (singleton-lock pattern for launchers — see SFI launcher / MTDS prediction launcher).
3. For SFI: the 2026-04-19 thundering-herd incident is the canonical reference — 10 VMs sharing one API key. Smoke
   matrix uses only 1 request per cell, but if nightly smoke overlaps with a prod backfill, rate-limit contention is
   possible. Stagger the nightly or throttle the matrix to 1 concurrent Tier-N service via `--fail-fast` + manual
   re-runs.
4. For api-football: the paid plan has generous headroom; if you see 429 here, credentials expired — check Secret
   Manager.

### 3.6 VM-only path difference

**Symptom:** Smoke runs green locally but the same cell FAILs on a backfill VM. Typically a path layout mismatch (local
uses macOS temp paths, VM uses `/tmp`; or local reads a cached parquet, VM reads fresh from GCS).

**Fix:** Cross-reference `codex/02-data/per-category-bucket-layouts.md` (SSOT for every upstream/downstream GCS path per
market category) and `safe_iterate_blobs` pattern (required for every new `list_blobs` caller). The playbook + Phase-C
Data Status heatmap (see § Related documents) flags category-specific path divergences — SPORTS
`sports_reference/.../entity=` vs CEFI/PREDICTION `instrument_availability/.../venue=` is the most common.

---

## 4. How to retry a single cell

```bash
# Tight loop on one cell — skip the full matrix, skip deps.
bash deployment-service/scripts/run-smoke-matrix.sh \
    --service market-tick-data-service \
    --category CEFI --venue binance --data-type trades \
    --no-deps \
    --report-dir /tmp/smoke-retry
```

The orchestrator still logs a note when `--service` is used without `--no-deps` — upstream tiers are silently skipped,
which is usually fine when prior TEST-bucket state is intact.

---

## 5. How to clean up TEST bucket data

Two mechanisms, in order of safety:

### 5.1 Automatic (default)

GCS lifecycle policies wipe TEST objects at 7 days. Enforced by
`deployment-service/configs/test-bucket-lifecycle.json` + `scripts/verify-test-bucket-lifecycle.sh`. No manual action
needed unless you suspect the policy was reverted.

### 5.2 On-demand via `--cleanup`

```bash
bash deployment-service/scripts/run-smoke-matrix.sh --cleanup
```

Iterates every `-test-` bucket in the current project and runs `gsutil -m rm -r <bucket>/*`. Best-effort; missing/empty
buckets are logged and skipped. Use this after an aborted smoke where stale state could poison the next run.

### 5.3 Manual nuclear option

```bash
# Full wipe of one TEST bucket
gsutil -m rm -r gs://instruments-store-cefi-test-<project-id>/
```

Rebuild by re-running the matrix. Never run this against a PROD bucket — there is no `-test-` suffix on PROD by design.

---

## 6. Runbook: nightly failure

When the GHA nightly workflow posts a Telegram alert:

1. Open the workflow run linked in the alert. Download `summary.json` + per-service JSON artifacts.
2. Identify the failing `(service, category, venue, data_type)` tuples.
3. Cross-reference against § 3 failure recipes.
4. Open a one-off run locally (or via `workflow_dispatch`) targeting the failing service to confirm the fix:
   `bash deployment-service/scripts/run-smoke-matrix.sh --service X --no-deps`
5. Once green locally, push the fix via quickmerge. The next scheduled nightly picks it up automatically — or force a
   re-run via `workflow_dispatch` before unblocking a pending prod merge.

If the failure is a genuine upstream outage (venue down, not our code):

- Mark the incident in ops Telegram.
- Do NOT lower the smoke-coverage floor. Mark the cell as expected-SKIP by pushing the floor YAML to `null` for that
  (service, category) only if the outage is permanent (vendor sunset, etc.).

---

## 7. Production deployment gate

`nightly-smoke-matrix.yml` exposes a `workflow_call` output `smoke_green` (bool). Downstream promotion workflows
(staging → main) MUST consume this output and refuse to merge if `smoke_green == false` for the most recent run. This is
the operational mechanism that turns the smoke matrix into a deployment gate rather than a passive signal.

If the gate blocks a genuine hotfix (sev1 fix that cannot wait for smoke recovery), the admin-override path is the same
as for quality-gate coverage regressions — see `unified-trading-pm/ops/coverage-override-policy.md` § smoke-coverage,
audited via `ops/coverage-override-audit.log`.

---

## 8. Smoke-coverage floor

`deployment-service/configs/smoke-coverage-floor.yaml` declares the minimum number of green cells per
`(service, category)` pair. The enforcer (`deployment-service/scripts/enforce-smoke-coverage-floor.py`) runs after every
nightly smoke matrix and fails the build if any pair regresses.

- Floor is a LOWER BOUND. Actual target is 100% green per the coverage roadmap plan.
- `null` = architecturally unsupported (skipped).
- `0` = baseline not yet established (the first green nightly ratchets up).
- Ratchet PRs use `chore(smoke): ratchet smoke-coverage floor to <run-id>`.
- Never lower the floor without an admin-override audit entry.

---

## 9. Related documents

- Plan SSOT: `plans/active/institutional_smoke_matrix_2026_04_20.plan.md`
- Phase 3 data-status / honest-coverage: `plans/active/proper_coverage_roadmap_2026_04_20.plan.md`
- Per-category bucket + path layouts: `codex/02-data/per-category-bucket-layouts.md`
- Availability manifest v5: `codex/02-data/availability-manifest-and-data-status.md`
- Sports adapter dependency order: `codex/02-data/sports-adapter-dependency-order.md`
- IS_TEST_RUN audit (Phase 1): `codex/02-data/is-test-run-audit-2026-04-20.md`
- VM tarball deployment: `codex/05-infrastructure/vm-tarball-deployment.md`
- Service CLI convention: `codex/06-coding-standards/cli-convention.md`
- Dependency DAG: `deployment-service/configs/dependencies.yaml`
- Coverage ratchet policy (pattern): `plans/active/coverage_ratchet_policy_2026_04_19.plan.md`

## 10. Change log

| Date       | Change                                                                 | Commit |
| ---------- | ---------------------------------------------------------------------- | ------ |
| 2026-04-20 | Initial playbook shipped (Phase 5 of institutional-smoke-matrix plan). | this   |
