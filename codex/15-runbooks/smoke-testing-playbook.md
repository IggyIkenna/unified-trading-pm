---
doc_type: codex-runbook
title: Smoke Testing Playbook
summary:
  Operational SSOT distinguishing the two smoke tools — the authoritative SIT gate
  (system-integration-tests/tests/smoke, HTTP-only, blocks staging->main via sit-lock) vs the dev-local per-service
  scripts/smoke_matrix.py (not a gate). Both enforce the same 3-step assertion (trigger clean, GCS parquet written,
  manifest row capture_status in captured/empty_confirmed); there is deliberately NO nightly cron.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    system-integration-tests,
  ]
scope: [engineer, admin]
tags: [runbook, smoke-test, integration-testing, manifest, quality-gates, data-status]
related:
  [
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/sports-adapter-dependency-order.md,
  ]
created: 2026-04-20
owner: on-call engineer (slot-1 main)
cadence: on-demand (triggered by staging→main promotion gate)
verifier: slot-1 orchestrator reviews SIT smoke results in CI
last_executed:
code_refs:
type: runbook
execution:
  {
    owner: on-call engineer (slot-1 main),
    cadence: on-demand (triggered by staging→main promotion gate),
    verifier: slot-1 orchestrator reviews SIT smoke results in CI,
    last_executed: 2026-05-19,
  }
---

# Smoke Testing Playbook

**Purpose:** Operational SSOT for smoke tests across the trading system. Two distinct tools with two distinct roles —
authoritative promotion gate vs. developer-local debugging helper. Do not conflate them.

---

## 1. Architecture at a glance

| Tool                                    | Repo                       | When it runs                                                                       | What it does                                                                                                                                                                                                                               | Authoritative?                          |
| --------------------------------------- | -------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| `system-integration-tests/tests/smoke/` | `system-integration-tests` | `staging-to-main.yml` promotion gate (triggered by `sit-lock` repository_dispatch) | HTTP-only pytest against running services + GCS/PubSub state assertions. `@pytest.mark.smoke` layer 3a (<5 min), `@pytest.mark.full_e2e` layer 3b (15-30 min).                                                                             | **Yes** — blocks staging → main merges. |
| `<service>/scripts/smoke_matrix.py`     | each data-service repo     | Manually, locally, when debugging                                                  | Enumerates (category × venue × data_type) cells and runs the service CLI under `IS_TEST_RUN=true` against `-test-` GCS buckets. 3-step assertion: CLI rc=0, parquet written, manifest row `capture_status in {captured, empty_confirmed}`. | **No** — developer tool only.           |

**Key rule:** there is **no nightly cron**. Smokes run when staging→main fires, not on a schedule. Daily cron was the
wrong trigger model — "nobody owns nightly failures" and cost without benefit. SSOT for SIT cadence:
`system-integration-tests/README.md` + `/codex/06-coding-standards/integration-testing-layers.md`.

---

## 2. Authoritative gate — SIT smoke tests

Canonical layer for institutional-grade smoke. Lives in `system-integration-tests/tests/smoke/`, shipped as part of
staging→main promotion. **No service imports** — tests talk to live services via HTTP and verify downstream state in
GCS + Pub/Sub.

### 2.1 What SIT gates

Full list of SIT-included repos in `system-integration-tests/README.md §SIT Scope`. Summary:

- All data services (instruments, MDPS, 8 features-\*)
- All T4 services (ml-inference, strategy, execution, position, risk, pnl-attribution)
- All T5 APIs and alerting
- **Excluded**: MTDS (separate feed validation suite), ml-training (async jobs), UIs (Playwright in their own CI),
  library repos (unit-tested).

### 2.2 Running SIT smokes locally

```bash
cd system-integration-tests

# Bring up the services SIT will hit (tier 2 = full fleet).
bash ../unified-trading-system-ui/scripts/dev-tiers.sh --tier 2

# Layer 3a smoke only (<5 min)
pytest -m smoke -v

# Layer 3b full e2e (15-30 min, after 3a passes)
pytest -m full_e2e -v
```

### 2.3 CI invocation

`staging-to-main.yml` sends a `sit-lock` repository_dispatch to trigger `sit-gate.yml`, which locks `staging_status` in
`workspace-manifest.json` and waits for `ci_status=STAGING_GREEN` on every included repo. Gate fires only when all
included repos have passed `@pytest.mark.smoke` AND `@pytest.mark.full_e2e`. Excluded repos are not awaited.

### 2.4 Coverage matrix smoke

`tests/smoke/test_coverage_matrix_smoke.py` parametrises over representative `(service × category × venue × data_type)`
cells and enforces Steps 2 + 3 of the 3-step assertion (parquet exists under the category-specific prefix; manifest row
has `capture_status in {captured, empty_confirmed}`). Step 1 (trigger) is a pre-condition — seed TEST buckets via
per-service `scripts/smoke_matrix.py` first.

Opt-in via `GCS_TEST_BUCKET_ENABLED=1`; skips cleanly in unit-only CI mode. One representative cell per distinct
partition shape keeps this smoke <5 min even when fully wired. Add more cells by appending to `CELLS` in
`tests/smoke/coverage_matrix_cells.py` — the pure-function helpers there are unit-tested independently (19 tests).

Reuses the canonical SSOTs:

- `/codex/02-data/per-asset-group-bucket-layouts.md` for prefix derivation (SPORTS `sports_reference/.../entity=` vs
  CEFI/TRADFI/DEFI/PREDICTION `instrument_availability/.../venue=`).
- `/codex/02-data/availability-manifest-and-data-status.md` for the `capture_status` semantics (`empty_confirmed` is
  PASS, `attempted_failed` is FAIL).

### 2.5 Adding a new smoke case

Edit `system-integration-tests/tests/smoke/test_*.py`. Pattern:

```python
@pytest.mark.smoke
def test_<surface>_<behaviour>(http_client, base_urls, gcs_client) -> None:
    # 1. Pre-condition: service is up (skip if not — don't fail).
    try:
        r = http_client.get(f"{base_urls['my_service']}/health")
    except httpx.ConnectError:
        pytest.skip("my-service not running")
    assert r.status_code == 200

    # 2. Trigger the behaviour via HTTP (not subprocess).
    r = http_client.post(f"{base_urls['my_service']}/trigger-batch", json={...})
    assert r.status_code == 202

    # 3. Verify downstream state — GCS parquet + manifest row.
    blobs = list(gcs_client.list_blobs("my-test-bucket", prefix="..."))
    assert any(b.name.endswith(".parquet") for b in blobs), "no parquet"
```

Zero service imports. Fail fast on assertion, skip on missing pre-condition.

---

## 3. Dev-local helper — per-service `scripts/smoke_matrix.py`

Each data service ships a standalone matrix runner for fast local debugging when you're developing a new venue adapter,
data type, or category. **Not a gate** — SIT is the gate.

### 3.1 When to use

- You just added a new venue adapter. Run the smoke for that service + category
  - venue to confirm end-to-end writes land in GCS.
- You're debugging a specific cell that SIT flagged as red. Reproduce locally faster than waiting for the next staging
  cycle.
- You changed shared infrastructure (UAC manifest schema, GCS path conventions) and want to smoke every cell in a
  service before pushing.

### 3.2 Running one

```bash
cd <service>
IS_TEST_RUN=true python scripts/smoke_matrix.py --execute --asset-group CEFI \
    --report /tmp/smoke.json
```

Enumerate without running:

```bash
python scripts/smoke_matrix.py  # defaults to dry enumeration
```

All scripts support `--asset-group X`, most support `--venue Y` and `--data-type Z`. Read the script's `--help` for the
service-specific shape.

### 3.3 What `IS_TEST_RUN=true` does

Routes every GCS write to a `<name>-test-<project>` bucket (7-day lifecycle, auto-delete) instead of production.
Manifest writes go to the test bucket's `_index/availability_index.parquet`. SSOT for bucket naming and lifecycle:
`deployment-service/configs/test-bucket-lifecycle.json` + `/codex/02-data/per-asset-group-bucket-layouts.md`.

### 3.4 Services with matrix runners

- `instruments-service` — reference data (~510 cells across 5 categories)
- `market-tick-data-service` — tick ingest
- `market-data-processing-service` — candles (~109 cells)
- `features-service (delta-one family)`, `features-service (volatility family)`, `features-service (calendar family)`,
  `features-service (onchain family)`, `features-service (sports family)`, `features-service (commodity family)`,
  `features-service (multi-timeframe family)`, `features-service (cross-instrument family)`

No orchestrator runs these in parallel — each is invoked locally, one at a time, by the developer.

---

## 4. 3-step assertion contract (both tools)

Every smoke cell, whether in SIT or per-service, asserts the same three things:

1. **Trigger ran clean** — CLI rc=0 (per-service) or HTTP 2xx (SIT).
2. **GCS parquet written** — at least one `.parquet` exists under the category's expected prefix (see
   `/codex/02-data/per-asset-group-bucket-layouts.md` — SPORTS uses `sports_reference/.../entity=`, others use
   `instrument_availability/.../venue=`, MTDS-SPORTS adds `league=` partition).
3. **Manifest row captured** — the test bucket's `_index/availability_index.parquet` has a row for the (date, category,
   venue, data_type) tuple with `capture_status in {captured, empty_confirmed}`. `empty_confirmed` is a **PASS**, not a
   skip — "we tried, venue legitimately returned zero rows" is valuable signal. `attempted_failed` is FAIL.

Manifest v5 schema SSOT: `/codex/02-data/availability-manifest-and-data-status.md`.

---

## 5. Telegram notifications

SIT failures route through the existing SIT alerting chain (same one used for staging→main locks — see
`sit-starvation-detector.yml` and `notify-telegram.yml`). No new workflow needed.

Per-service scripts do not send Telegram — they are interactive developer tools.

---

## 6. Related documents

- `system-integration-tests/README.md` — SIT scope + layer model
- `/codex/06-coding-standards/integration-testing-layers.md` — canonical test layering
- `/codex/02-data/per-asset-group-bucket-layouts.md` — bucket layout per category
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest v5 schema
- `/codex/02-data/sports-adapter-dependency-order.md` — T0/T1 sports ordering
- `deployment-service/configs/test-bucket-lifecycle.json` — TEST bucket lifecycle rules
- `deployment-service/scripts/provision-test-buckets.sh` — provisioning helper
