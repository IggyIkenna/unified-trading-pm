---
doc_type: issue
title:
  "deployment-api CI is FAILING on live-defi-rollout — 8 tests hardcode onchain feature_family/AAVE-registry
  expectations that UAC's WRITER-vocabulary reconciliation just changed"
summary: >-
  Found incidentally while verifying CI after shipping unrelated DeFi honest-coverage work this session.
  deployment-api's `quality-gates-v2` on `live-defi-rollout` is currently FAILING (run 29793522960, headSha
  `ea56fff4d086c9bc5b18bfde6d37087947fa74a2`, `qg_red_reason=pytest`). 8 tests across
  `test_feature_group_breakdown_uac.py`, `test_data_status_hierarchical.py::TestFeatureFamilyAxis`, and
  `test_shard_detail_service.py::TestResolveInstrumentTypeAuto` fail with mismatched dates/counts/booleans/strings (e.g.
  `assert '2020-01-01' == '2022-03-16'`, `assert 87 == 86`, `assert '' == 'onchain'`). Root cause: UAC commit `e9faf32e`
  ("fix(features): reconcile the onchain feature_group registry to the WRITER vocabulary", landed 2026-07-21 01:28:23
  UTC — after this session's own UAC push `d4d85854` at 00:58:05 UTC, before deployment-api's CI dispatched at 01:35:17
  UTC) changed the live onchain feature_group/AAVE registry values that these deployment-api tests hardcode as fixtures.
  Not caused by this session's work — this session's only UAC touch was the unrelated
  `EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH` enum addition, and deployment-api's own commits this session
  (`8691f29`/`ea56fff`) are unrelated data-status/distinct-values changes that pass locally (`quality-gates.sh --no-fix`
  green, 4755 passed/0 failed, confirmed 3x including once against this exact HEAD).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, unified-api-contracts]
scope: [engineer]
tags: [ci, feature-family, onchain, uac-registry, test-fixture-drift, deployment-api]
related: []
created: 2026-07-21
priority: P1
parent_epic: features_and_ml_master
source:
  "Discovered during CI verification sweep for defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20
  close-out (slot-3, 2026-07-21) — unrelated to that session's work."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# deployment-api feature_family tests drifted from UAC onchain registry

## Why this exists (provenance, 2026-07-21)

While verifying CI status after shipping unrelated DeFi honest-coverage work,
`gh run list --branch live-defi-rollout --repo IggyIkenna/deployment-api` showed the latest `quality-gates-v2` run
FAILING on the exact HEAD this session pushed (`ea56fff4d086c9bc5b18bfde6d37087947fa74a2`). Investigation confirmed the
failure is caused by a DIFFERENT, concurrent agent's UAC commit landing in the ~7-minute window between this session's
UAC push and deployment-api's CI dispatch — not by anything this session shipped.

## The 8 failing tests (run 29793522960, `qg_red_reason=pytest`)

```
FAILED tests/unit/test_feature_group_breakdown_uac.py::test_clip_registered_aave_lending_rates_pushes_start_forward
  AssertionError: assert '2020-01-01' == '2022-03-16'
FAILED tests/unit/test_feature_group_breakdown_uac.py::test_uac_breakdown_registered_service_uses_uac_denominator
  AssertionError: assert 87 == 86
FAILED tests/unit/test_feature_group_breakdown_uac.py::test_uac_breakdown_pre_floor_dates_clipped
  assert 1 == 2
FAILED tests/unit/test_feature_group_breakdown_uac.py::test_uac_breakdown_observed_but_unexpected_group_surfaces_as_drift
  assert False is True
FAILED tests/unit/test_data_status_hierarchical.py::TestFeatureFamilyAxis::test_stamper_fills_blank_feature_family_via_uac
  AssertionError: assert '' == 'onchain'
FAILED tests/unit/test_data_status_hierarchical.py::TestFeatureFamilyAxis::test_filter_by_feature_family_narrows_to_one_family
  assert 1 == 2
FAILED tests/unit/test_shard_detail_service.py::TestResolveInstrumentTypeAuto::test_feature_family_resolved_from_uac_when_path_unresolved
  AssertionError: assert None == 'onchain'
FAILED tests/unit/test_shard_detail_service.py::TestResolveInstrumentTypeAuto::test_feature_family_drift_in_parquet_logged_returns_none
  AssertionError: assert None == 'onchain'
```

## Root cause

`unified-api-contracts@e9faf32e` —
`fix(features): reconcile the onchain feature_group registry to the WRITER vocabulary` — landed 2026-07-21 01:28:23 UTC.
deployment-api's `quality-gates-v2` clones a FRESH copy of UAC's `live-defi-rollout` HEAD at dispatch time (01:35:17
UTC), so it picked up `e9faf32e`'s registry change. The 8 tests above hardcode specific dates (`2022-03-16`), counts
(`86`/`2`), and the literal string `'onchain'` as expected `feature_family`/registry-resolution outputs — values that
`e9faf32e` apparently changed as part of its "reconcile to WRITER vocabulary" fix.

## Why this is NOT this session's fault

- This session's only UAC commit (`d4d85854`) added a single new `EmptyConfirmedReason` enum member
  (`EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH`) — no touch to onchain feature_group/AAVE registries.
- This session's deployment-api commits (`8691f29`, `ea56fff`) are unrelated: EMPTY_REASON_KEYS taxonomy sync + a
  distinct-values defi-venue canonical-set grain fix (D1b).
- Local `quality-gates.sh --no-fix` against this EXACT HEAD (`ea56fff`) passed clean 3 consecutive times this session
  (final run: 4755 passed, 0 failed, `ALL QUALITY GATES PASSED`) — using this session's OWN local UAC editable-install
  path, which had NOT yet picked up `e9faf32e` (a different agent's concurrent push) at test time. CI's fresh clone did
  pick it up, 7-16 minutes later.

## Follow-on work (tracked)

- [ ] [DECISION] P1. Whoever owns `unified-api-contracts@e9faf32e`'s "reconcile onchain feature_group registry to the
      WRITER vocabulary" intent should update the 8 deployment-api test fixtures above to match the new registry values
      (dates/counts/`feature_family` string), OR confirm the registry change itself needs a follow-up fix if the NEW
      values are wrong. Needs the `e9faf32e` author's context on what the "WRITER vocabulary" reconciliation was
      supposed to produce.
- [ ] [BACKEND] P2. Re-run deployment-api's `quality-gates-v2` after the fixture update lands, to confirm CI goes green
      again on `live-defi-rollout`.
