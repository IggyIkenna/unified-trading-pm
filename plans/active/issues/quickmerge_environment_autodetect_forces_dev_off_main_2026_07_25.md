---
doc_type: issue
title:
  quickmerge.sh's ENVIRONMENT auto-detect only recognises branch `main` as production — forces `ENVIRONMENT=development`
  on every quickmerge run on `live-defi-rollout`, the branch quickmerge itself documents as the normal target. A naive
  branch-name fix trades one test-failure class for another — the REAL fix is test isolation, not broader env-forcing.
summary: >
  `scripts/quickmerge.sh`'s "ENVIRONMENT AUTO-DETECT" block (~L1214) sets `ENVIRONMENT=production` only when `git branch
  --show-current` is literally `main`; every other branch — including `live-defi-rollout`, which quickmerge lands on by
  design (LDR-is-SSOT, /codex/08-workflows/ci-cd-flow.md) — falls through to `ENVIRONMENT=development` +
  `GCP_PROJECT_ID_DEV`. This predates the LDR-is-SSOT model (or never accounted for it). CONFIRMED root cause (not
  test-order pollution, see "What was verified"): `unified-trading-library`'s
  `tests/cloud_interface/unit/test_constants.py` (5 tests) assert the DOCUMENTED prod default of
  `resolve_bucket_name`/`get_environment` ("defaulting to prod when unset" per the function's own docstring) and only
  fail when run through quickmerge's own re-gate — never in isolation, never via a direct `pytest` invocation matching
  the exact same test set. BUT: a same-repo TRIAL FIX (broadening the branch check to also treat `live-defi-rollout` +
  `staging` as production) was built, applied locally, and re-gated — it eliminated those 5 failures but immediately
  surfaced 2 DIFFERENT failures elsewhere in the SAME repo
  (`tests/unit/test_config.py::TestUnifiedCloudServicesConfig::test_is_development`,
  `tests/config_interface/integration/test_unified_cloud_config.py::TestUnifiedCloudConfigDefaults::test_environment_defaults_to_development`),
  because `UnifiedCloudServicesConfig` (a DIFFERENT config surface in the same repo) has the OPPOSITE documented default
  (no-override => "development"), and — more surprising — its env-var read takes PRECEDENCE over an explicit
  `environment="development"` constructor kwarg (see the captured assertion:
  `UnifiedCloudServicesConfig(environment='development', ...).is_development` evaluates to `False` because the ambient
  `ENVIRONMENT=production` won). So this ONE repo alone has two config surfaces with genuinely OPPOSITE "nothing set"
  defaults, and quickmerge forcing EITHER value ambient-wide breaks whichever surface disagrees. The trial fix was
  **reverted** rather than shipped, because its blast radius (every repo's quickmerge run) was not verifiable in the
  time available — swapping 5 known failures for 2 different ones in the ONE repo actually tested does not prove it is a
  net improvement fleet-wide, and this script gates every repo in the workspace.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer]
tags: [ci-cd, quickmerge, environment, ldr-is-ssot, false-flaky, quickmerge-blocker, config-defaults-conflict]
related:
  [
    /plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md,
    /plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md,
  ]
created: 2026-07-25
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
drift_direction: NA
source:
  found while shipping a cloudbuild.yaml + publish-package.yml fix to unified-trading-library, 2026-07-25 — quickmerge's
  own re-gate blocked the ship 3x with 5 unrelated-looking bucket-naming test failures; the trial fix's own re-gate then
  surfaced the second, conflicting-default class
resolved_by:
  PARTIAL (2026-07-25, continued session) — suggested-next-step 1 (test isolation) implemented + verified in
  unified-trading-library, shipping via quickmerge. quickmerge.sh itself is UNCHANGED (still reverted to original);
  steps 2-4 (pydantic-settings alias-vs-kwarg precedence flag, revisiting the branch check, fleet-wide grep) remain open
  — see "Resolution" section below.
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## What was verified

- `unified_trading_library/tests/cloud_interface/unit/test_constants.py::test_get_bucket_name_gcp` (+4 siblings) assert
  the env-tiered `-prd-` bucket suffix with no explicit env override, relying on `resolve_bucket_name`'s documented
  `prod` default.
- `git stash` (clean UTL tree) -> full `quickmerge.sh` re-gate -> same 5 failures (`'X-dev-Y' == 'X-prd-Y'`), reproduced
  3x — ruled out as caused by the actual change being shipped in that session.
- `pytest tests/cloud_interface/unit/test_constants.py::test_get_bucket_name_gcp` alone: passes.
- Reconstructed `quality-gates.sh`'s EXACT pytest invocation by hand (`PYTEST_WORKERS=4`, the full `PYTEST_UNIT_DIR`
  list from `unified-trading-library/scripts/quality-gates.sh`, PLUS the whole `tests/integration/` dir that
  `base-library.sh:379` appends unconditionally when it exists) and ran it directly with `python3 -m pytest ...`: **6716
  collected, 0 failures** — same exact test set quickmerge runs, zero repro outside quickmerge's own process.
- Traced to `scripts/quickmerge.sh` "ENVIRONMENT AUTO-DETECT" (~L1214): `CURRENT_BRANCH != "main"` on
  `live-defi-rollout` -> `export ENVIRONMENT="development"` -> inherited by the pytest subprocess -> the resolver's
  `os.environ.get("DEPLOYMENT_ENV") or os.environ.get("ENVIRONMENT") or "prod"` chain picks up `"development"` instead
  of falling through to the documented `"prod"` default.
- **Trial fix** (broaden the branch check to `main` / `live-defi-rollout` / `staging`): applied, re-gated locally —
  eliminated the 5 original failures, but exposed:
  - `tests/unit/test_config.py::TestUnifiedCloudServicesConfig::test_is_development` — constructs
    `UnifiedCloudServicesConfig(environment="development")` and asserts `.is_development is True`; got `False` because
    the resulting `.environment` was `'production'` — the ambient `ENVIRONMENT` env var overrode the EXPLICIT
    constructor kwarg.
  - `tests/config_interface/integration/test_unified_cloud_config.py::TestUnifiedCloudConfigDefaults::test_environment_defaults_to_development`
    — asserts `cfg.environment == "development"` with no override, expecting `UnifiedCloudServicesConfig`'s OWN
    no-env-set default to be `"development"` (the opposite of `resolve_bucket_name`'s documented `"prod"` default).
- **Reverted** the trial fix (`scripts/quickmerge.sh` is back to its original, unmodified state) rather than ship it —
  see summary for why.

## Why this is genuinely open, not a quick fix

Two real, opposite, apparently-both-intentional conventions coexist in `unified-trading-library`:

1. `resolve_bucket_name`/`get_environment` (bucket-naming/cloud_interface layer): no-override default is documented as
   `"prod"` — "so the bucket-name resolution stays consistent with the rest of the config-bootstrap layer."
2. `UnifiedCloudServicesConfig` (config_interface layer): no-override default is tested as `"development"`, and its
   env-var read wins over an explicit constructor kwarg (a separate, possibly-also-worth-flagging pydantic-settings
   precedence surprise: env should not normally outrank an explicit `__init__` value).

A branch-name-only fix to quickmerge.sh cannot satisfy both without also fixing (1) and (2) never being exercised under
a false ambient default in the first place. The properly correct fix is almost certainly: tests asserting a DEFAULT
behavior should not depend on the CI-runner's ambient environment at all — `test_get_bucket_name_gcp` and
`test_environment_defaults_to_development` should each explicitly isolate (`monkeypatch.delenv("DEPLOYMENT_ENV")`,
`monkeypatch.delenv("ENVIRONMENT")`, or `patch.dict(os.environ, ..., clear=True)`) before asserting their respective
"nothing set" default — exactly like the properly-isolated tests elsewhere in this same repo already do (see
`test_sports_fixtures_bucket.py`, `test_bucket_naming_cell_sweep.py`) — rather than relying on whatever quickmerge.sh
happens to export. That is real, if small, work across (at minimum) these 2-7 test sites, not a one-line branch check.

## Resolution (2026-07-25, continued session)

Implemented suggested-next-step 1. Three sites, all in `unified-trading-library`:

- `tests/cloud_interface/unit/test_constants.py` — the file's existing autouse `_clear_cache` fixture now also
  `monkeypatch.delenv("DEPLOYMENT_ENV")` / `monkeypatch.delenv("ENVIRONMENT")` (matching the established idiom in
  `test_sports_fixtures_bucket.py`/`test_bucket_naming_cell_sweep.py`), fixing `test_get_bucket_name_gcp` +4 siblings in
  one place rather than per-test.
- `tests/unit/test_config.py::test_is_development` — was the ONE test in its 6-sibling cluster using the real
  `UnifiedCloudServicesConfig(...)` constructor instead of `.model_construct(...)`; switched to match its siblings
  (`test_is_production`, `test_is_testing`, `test_is_testing_mode`, all already `model_construct` + "no env merge").
- `tests/config_interface/integration/test_unified_cloud_config.py::test_environment_defaults_to_development` — added
  `monkeypatch.delenv("ENVIRONMENT"/"ENV")`, matching the sibling `test_default_construction` immediately above it in
  the same class (which already does this for `CLOUD_MOCK_MODE`/`DATA_MODE`).

**Verified ambient-independent**: ran the 3 affected test files directly with `ENVIRONMENT` unset / `development` /
`production` / `staging` — 38/38 pass in every case. Ran the FULL local unit+integration suite (quality-gates.sh's exact
`PYTEST_UNIT_DIR` set, `PYTEST_WORKERS=4`) under `ENVIRONMENT=development` (current quickmerge behavior on this branch)
and again under `ENVIRONMENT=production` (the trial-fix scenario): **6692 passed, 14 skipped, 10 xfailed, 0 failures**,
identical both times. Shipped alongside the `publish-package.yml` dispatcher fix.

**Step 2 answered, not just flagged**: confirmed via direct repro
(`UnifiedCloudServicesConfig(environment='development')` with ambient `ENVIRONMENT=production` set →
`.environment == 'production'`) that this is NOT a pydantic-settings value-precedence surprise — it's a real
inconsistency between two config base classes in this repo. `config_interface/base_config.py`'s `BaseConfig.environment`
has `validation_alias=AliasChoices("ENVIRONMENT", "ENV", "environment")` (bare name included) AND
`model_config.populate_by_name=True`, so `environment=` kwargs are honoured. `core/config.py`'s
`UnifiedCloudServicesConfig.environment` has `validation_alias=AliasChoices("ENVIRONMENT", "ENV")` (bare name OMITTED)
and no `populate_by_name` — so passing `environment=` to the real constructor is SILENTLY DROPPED (not merely outranked)
and the field resolves from env instead. Confirmed via
`tests/config_interface/integration/test_unified_cloud_config.py`'s own file-level docstring, which already documents
this exact quirk for `UnifiedCloudConfig`'s OTHER aliased fields. Not fixed this session (a `core/config.py` field
change needs a caller audit across the repo before touching it — out of scope for a test-isolation fix); tracked as step
2 below.

## Suggested next steps

1. [INFRA] P1. ✅ DONE 2026-07-25 — see Resolution above.
2. [INFRA] P2. Align `UnifiedCloudServicesConfig.environment`'s alias with `BaseConfig.environment`'s (add
   `populate_by_name` and the bare `"environment"` entry to `AliasChoices`) so the real constructor's `environment=`
   kwarg isn't silently dropped in favour of ambient env — confirmed root cause in Resolution above, not yet fixed
   (needs a caller audit: anywhere in the repo passing `environment=` to `UnifiedCloudServicesConfig(...)` expecting it
   to win is currently silently getting the ambient value instead, which is worth auditing FOR before changing the
   precedence).
3. [INFRA] P2. ONLY once (2) is done (or confirmed non-breaking): revisit whether `scripts/quickmerge.sh`'s branch check
   should ALSO be broadened to recognise `live-defi-rollout`/`staging` — blast radius is now safer for the 7 sites fixed
   here, but (2) is a separate latent risk the broadening would still expose if any other in-repo caller relies on the
   silently-dropped-kwarg behavior in a way this issue didn't probe.
4. [INFRA] P3. Grep the other ~20 repos for the same ambient-default-reliant test pattern before assuming this is unique
   to `unified-trading-library` — not done this session.
