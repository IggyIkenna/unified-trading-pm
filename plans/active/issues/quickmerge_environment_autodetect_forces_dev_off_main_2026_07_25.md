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
asset_group: [ci]
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
author: unknown
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
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md,
    /plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md,
    unified-trading-pm/scripts/quickmerge.sh,
    unified-trading-library/unified_trading_library/config_interface/base_config.py,
    unified-trading-library/unified_trading_library/core/config.py,
  ]
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
2. [INFRA] P2. ✅ **DONE — corrected 2026-08-07, this item was stale.** Align `UnifiedCloudServicesConfig.environment`'s
   alias with `BaseConfig.environment`'s (add `populate_by_name` and the bare `"environment"` entry to `AliasChoices`)
   so the real constructor's `environment=` kwarg isn't silently dropped in favour of ambient env — confirmed root cause
   in Resolution above. Per the Todos section below (corrected 2026-08-07 by na-eligibility-audit): shipped
   `unified-trading-library@dc1dc7df`. This numbered list was not updated at the time; the Todos section is
   authoritative — see there for the evidence citation.
3. [INFRA] P2. ONLY once (2) is done (or confirmed non-breaking): revisit whether `scripts/quickmerge.sh`'s branch check
   should ALSO be broadened to recognise `live-defi-rollout`/`staging` — blast radius is now safer for the 7 sites fixed
   here, but (2) is a separate latent risk the broadening would still expose if any other in-repo caller relies on the
   silently-dropped-kwarg behavior in a way this issue didn't probe.
4. [INFRA] P3. ✅ **DONE — corrected 2026-08-07, this item was stale.** Grep the other ~20 repos for the same
   ambient-default-reliant test pattern before assuming this is unique to `unified-trading-library`. Per the Todos
   section below: fleet grep result was "none found — fleet is clean." This numbered list was not updated at the time;
   the Todos section is authoritative — see there for the evidence citation.

## Todos

- [ ] [INFRA] P2. **Finish the quickmerge environment auto-detect follow-up.** **Steps 2+4 are DONE, only step 3
      remains** — corrected 2026-08-07 (na-eligibility-audit; the text below was stale, see marker below for why): step
      3 (revisit whether `scripts/quickmerge.sh`'s branch check should broaden to `live-defi-rollout`/`staging`) is the
      only genuinely open sub-item — tracked in `ci_satellite_ao_dispatch_batch4_2026_07_31.md` as Deferred **D4-1**
      (`status: active`, but D4-1 itself sits in the Conflict-gated/Deferred section, not currently dispatched by any
      active todo — gated on `scripts/quickmerge.sh` ownership contention with that batch's own todo 1). It is a
      design/judgment call on the fleet-wide shipping-pipeline gate every repo depends on — appropriately stays NA even
      with steps 2/4's risk reduced.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — conflict-gated as
`/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E5**: steps 2-4 touch
`scripts/quickmerge.sh`, which that batch's todo 1 owns this round, and E5 further notes the item's own internal step-2
precondition (the `UnifiedCloudServicesConfig` caller audit) was not re-verified. Step 3 is explicitly gated on step 2
by this doc's own text.

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, valid — re-confirmed, not re-litigated (E5
citation verified real). **`locked_by` ANOMALY flagged, no action taken**: this doc's frontmatter carries
`locked_by: live-defi-rollout` / `locked_since: 2026-05-21` — a branch name, not a slot/agent claim token, and
`locked_since` predates this doc's own `created: 2026-07-25` by two months. A sibling corpus doc
(`ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md`) documents this exact value elsewhere
as "the known stale branch-name artifact," cleared there per a cited precedent
(`/plans/archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`) — but that precedent was applied to a
DIFFERENT doc; per the HARD RULE that archival/reclassification never proceeds on a non-empty `locked_by` without
`[unlock-plan]` operator confirmation, this pass took no action on the lock field itself. Recommend the operator either
confirm this is the same stale artifact (and clear it per the cited precedent) or clarify what it actually locks here.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): KEEP-NA-STALE (already-duplicated) —
citation correction. The 2026-07-30/08-01 citation to archived `ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred
E5 is now stale (batch2 is archived/superseded). Verified live: steps 2+4 are now extracted verbatim as todo 2 in
`/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (lines 143-167, `Source:` cites this doc's
Suggested next steps 2+4), with step 3 tracked there as Deferred **D4-1** (still gated on todo 2 landing +
`quickmerge.sh` being free). Batch4 is `status: draft` — not yet dispatched — so this is a citation fix, not a
reclassification; flipping this doc directly would race/duplicate-dispatch onto the same `unified-trading-library`
config files batch4 already owns once activated. `locked_by` anomaly (flagged 2026-08-01) unchanged, still unactioned
pending operator.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 6 entries resolve on disk (SSOT + 2
  related issue docs + quickmerge.sh + the 2 opposite-default config files at the bug's core) — no changes.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA-STALE — steps 2+4 extracted to
ci_satellite_ao_dispatch_batch4_2026_07_31.md todo 2 (draft)

- **worker slot-15 2026-08-06**: Completed steps 2+4 (ci_satellite_ao_dispatch_batch4-002).
  - **Caller audit**: Grep of all `UnifiedCloudServicesConfig(` instantiations in UTL — zero callers pass `environment=`
    kwarg to the real constructor (only `model_construct` callers, which bypass alias resolution). Fix is safe: no
    caller currently relies on the silently-dropped-kwarg behavior.
  - **Fix shipped**: `unified_trading_library/core/config.py` — added `populate_by_name=True` to `model_config` and
    `"environment"` to `AliasChoices("ENVIRONMENT", "ENV")`. Matches `BaseConfig.environment`'s pattern exactly.
    Regression test `test_environment_kwarg_wins_over_ambient` added to `tests/unit/test_config.py` proving
    `environment=` kwarg wins when ambient `ENVIRONMENT=production` is set. Quality gates green (147s). Shipped
    `unified-trading-library@dc1dc7df`.
  - **Fleet grep (step 4)**: Grepped 23 repos for ambient-default-reliant test pattern (tests asserting
    `is_development`/`environment==development` defaults without `monkeypatch.delenv("ENVIRONMENT"/"DEPLOYMENT_ENV")`).
    Result: **none found** — no other repo carries the risky pattern. All checked repos either use `model_construct`,
    `monkeypatch`/`setdefault` to set env explicitly, accept flexible multi-value assertions, or mock settings objects
    directly. Fleet is clean.

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, stale checkbox text fixed — the
doc's own Progress Log already recorded steps 2+4 as done (`worker slot-15 2026-08-06`,
`unified-trading-library@dc1dc7df`) but the todo checkbox itself still described all of steps 2-4 as "unstarted" and
cited `ci_satellite_ao_dispatch_batch4_2026_07_31.md` as `status: draft` (it has been `status: active` since creation,
same stale-wording class found elsewhere in this tranche today). Rewrote the checkbox to name step 3 as the sole
remaining item. Step 3 itself (D4-1, `scripts/quickmerge.sh` branch-check broadening) stays a genuine design/judgment
call — no `assigned_vm` change. `locked_by` anomaly (flagged 2026-08-01, still unactioned) unchanged.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:dcf6e0dda6134bac]: KEEP-NA,
valid — the sole open item (step 3, quickmerge.sh branch-check broadening, D4-1) remains a genuine design/judgment call,
gated on `scripts/quickmerge.sh` ownership contention. `locked_by: live-defi-rollout` anomaly (flagged 2026-08-01, still
unactioned) unchanged — not this run's to clear autonomously. No `assigned_vm` change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:003eb4f7e5a28a06]: KEEP-NA,
valid — Steps 2 and 4 of the suggested-next-steps are done (shipped unified-trading-library@dc1dc7df + fleet grep found
no other repo carries the risky pattern). The sole remaining open sub-item is step 3: revisit whether quickmerge.sh's
branch check should broaden to recognise live-defi-rollout/staging as production. The doc's own body documents a
same-repo TRIAL FIX that was built, applied, and locally re-gated -- it eliminated the 5 originally-failing tests but
immediately surfaced 2 DIFFERENT failures elsewhere in the same repo, because a second config surface
(UnifiedCloudServicesConfig) has the OPPOSITE documented default from the first (resolve_bucket_name).
