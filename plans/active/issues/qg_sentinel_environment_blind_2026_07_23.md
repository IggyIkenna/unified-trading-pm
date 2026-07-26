---
doc_type: issue
title:
  QG sentinel is ENVIRONMENT-blind — quickmerge runs gates as ENVIRONMENT=development, standalone runs default to prod,
  and the standalone pass launders the failure green
summary: >-
  quickmerge exports `ENVIRONMENT=development` for any non-`main` branch (scripts/quickmerge.sh:1216-1222) — which is
  EVERY slot, since every slot lives on live-defi-rollout. UTL's bucket resolver defaults to **prod** when ENVIRONMENT
  is unset (unified_trading_library/cloud_interface/bucket_naming.py:162), and three repos hardcode prod bucket names in
  tests. Net: those tests FAIL DETERMINISTICALLY under quickmerge and PASS standalone. That alone is only an annoyance —
  the real problem is the documented recovery. Re-running `bash scripts/quality-gates.sh --no-fix` standalone passes
  (prod default) and WRITES THE SENTINEL; quickmerge then matches the sentinel hash and SKIPS the gate entirely, so a
  suite that genuinely fails in quickmerge's environment ships green. The sentinel is a bare sha256 of tree content with
  NO environment dimension, so it cannot distinguish "verified in dev" from "verified in prod". Same class as the
  2026-07-18 deployment-ui incident already documented at quickmerge.sh:1288-1300 (sentinel satisfied → Pass 2 skipped →
  tsc-red tree landed on LDR); that fix closed the tree-drift dimension but not the environment dimension.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library, deployment-api, strategy-service, market-tick-data-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, quality-gates, sentinel, test-isolation, environment, gate-bypass]
related:
  - /plans/archive/issues/staging_workflow_shutdown_2026_07_23.md
  - /plans/active/github_actions_ci_cost_reduction_2026_07_15.md
  - /plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md
created: 2026-07-23
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
locked_by:
resolved_by:
depends_on: []
source:
  - "observed twice during the 25-unit staging-shutdown rollout 2026-07-23 (unified-trading-library,
    market-tick-data-service)"
  - "reproduced deterministically: ENVIRONMENT unset => pass, ENVIRONMENT=development => fail, same tree/machine"
---

# The QG sentinel cannot tell which environment verified the tree

## How it was found

During the 25-repo staging-shutdown rollout (2026-07-23), two ship agents hit "unrelated test failures" and both
reported them as **transient flakes under parallel xdist**. That diagnosis was repeated up the chain unverified. It is
**wrong** — the failures are deterministic and have nothing to do with xdist.

## The actual mechanism (reproduced, not inferred)

1. **quickmerge forces dev mode.** `scripts/quickmerge.sh:1216-1222`:

   ```bash
   if [ "$CURRENT_BRANCH" = "main" ] || [ "${PROD_FLAG:-false}" = "true" ]; then
     export ENVIRONMENT="production"
   else
     export ENVIRONMENT="development"      # ← every slot, always (all slots are on live-defi-rollout)
   ```

2. **The bucket resolver defaults to prod when unset.** `unified_trading_library/cloud_interface/bucket_naming.py:162` —
   reads `DEPLOYMENT_ENV`, then `ENVIRONMENT`, "defaulting to `prod` when unset".

3. **Three repos hardcode prod bucket names in tests** (`-prd-p`): `unified-trading-library`
   (`tests/cloud_interface/unit/test_constants.py`), `deployment-api`, `strategy-service`. market-tick-data-service
   fails the same family via `test_prediction_stays_prod_without_is_test_run` /
   `test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`.

4. **Proof** — same tree, same machine, xdist disabled:

   ```
   ENVIRONMENT=            pytest -k instruments_bucket -p no:xdist  →  1 passed
   ENVIRONMENT=development pytest -k instruments_bucket -p no:xdist  →  1 failed
   ```

   Deterministic. Not flaky, not a race, not worker leakage.

## Why this is a gate-BYPASS, not just noise

The recovery everyone uses (and that this rollout's agent instructions explicitly taught) is:

> re-run `bash scripts/quality-gates.sh --no-fix`, then retry quickmerge

Standalone, `ENVIRONMENT` is unset → resolver returns prod → the suite passes → **the sentinel is written**. quickmerge
then finds a sentinel matching the tree hash and prints `✅ SHA sentinel verified — skipping Pass 2 QG re-runs` — **the
failing tests never run again.** The tree ships green having never passed in the environment quickmerge actually uses.

`.qg_content_sentinel` is a **bare sha256 of tree content**:

```
5442c1c262be8627cd3c4ae064ebd4e34f428518f36db48b2bbcdfdad146bbc2
```

No environment, no toolchain, no config dimension. It answers "was THIS TREE verified?" but not "verified under WHICH
configuration?" — so a pass in one environment is silently redeemable in another.

This is the **same class** as the incident already recorded at `scripts/quickmerge.sh:1288-1300` (deployment-ui
2026-07-18: sentinel satisfied → Pass 2 skipped → tsc-red tree landed on LDR). That fix hardened the **tree-drift**
dimension (ancestor-only + byte-identical tree). The **environment** dimension is still open.

## Which side is actually wrong?

Both readings are defensible and the operator should pick — they lead to different fixes:

- **The tests are wrong.** A unit test asserting a literal `-prd-p` name encodes an environment it does not control. It
  should either set the env explicitly (`monkeypatch.setenv("ENVIRONMENT", ...)`) or assert via the resolver's own
  contract rather than a hardcoded string. → smallest change, fixes 3-4 repos.
- **The gate is wrong.** If quickmerge's gate is the per-repo quality boundary, it should run in the environment the
  code actually ships to, not silently in `development`. → bigger blast radius, needs care.
- **The sentinel is wrong (independent of the above, and the real hazard).** It must bind the configuration it was
  produced under — e.g. hash `ENVIRONMENT` (+ any other gate-affecting env) into the sentinel so a dev-verified sentinel
  cannot satisfy a prod-context run, or vice-versa. **This one should be fixed regardless of the other two**, because it
  is what converts a loud failure into a silent pass.

## Resolution checklist

- [ ] [OPERATOR] P1. Decide the split: fix the tests, the gate's environment, or both — and confirm the sentinel
      hardening below proceeds independently.
- [ ] [INFRA] P1. **Bind configuration into the sentinel** (`scripts/base-service.sh` / `scripts/quickmerge.sh`): mix
      `ENVIRONMENT` (and any other gate-affecting env var) into the sentinel hash so a sentinel produced under one
      configuration cannot satisfy a run under another. Add a regression test that a dev-written sentinel does NOT
      satisfy a prod-context quickmerge.
- [ ] [INFRA] P2. Fix the env-coupled tests in `unified-trading-library`
      (`tests/cloud_interface/unit/test_constants.py`), `deployment-api`, `strategy-service`, and the two
      `market-tick-data-service` cases — set the environment explicitly per-test instead of relying on the ambient
      default. **PARTIAL 2026-07-25 — 1 of 4 repos done; box stays open** (`/plan-reconcile ci`, 2026-07-26): the
      **`unified-trading-library` half is SHIPPED and verified live at the cited path** —
      `tests/cloud_interface/unit/test_constants.py:32-37`'s autouse `_clear_cache` fixture now does
      `monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)` + `monkeypatch.delenv("ENVIRONMENT", raising=False)` with
      the in-file comment _"Isolate from ambient DEPLOYMENT_ENV/ENVIRONMENT (e.g. quickmerge.sh's branch-based …)"_,
      fixing `test_get_bucket_name_gcp` +4 siblings in one place. Full write-up + the 2 sibling test sites also fixed in
      that repo:
      [/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md](/plans/active/issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md)
      § Resolution. **DEFERRED — still open**: `deployment-api` and `strategy-service` (not verified this pass), and the
      two `market-tick-data-service` cases, which are demonstrably NOT fixed — they were still failing intermittently as
      late as 2026-07-24 per
      [/plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md](/plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md)
      (5 consecutive quickmerge re-gate hits, `1/1 worker` serial).
- [ ] [DOC] P2. Correct the "re-run quality-gates.sh --no-fix then retry" guidance wherever it is taught (agent prompts,
      runbooks): as written it is a sentinel-laundering step, not a fix. It is only safe once the sentinel binds
      configuration.
