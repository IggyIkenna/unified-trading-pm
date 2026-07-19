---
doc_type: issue
title:
  "features-service quality-gates.sh RED — STEP 5.104 asset-group parity gate's check_asset_group_parity.py
  _KIND_TO_FAMILY mapping is stale post-bucket-fold, blocking every ship from the repo"
summary:
  "Dispatched onto api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007 (fix
  features-service's _filter_completed_before H2H status filter — unrelated). Full quality-gates.sh run is RED at STEP
  5.104 (ASSET-GROUP PARITY GATE), verified byte-identical on a clean tree with my diff stashed per RULES.md § 4b. 5
  families (features-delta-one, features-mtf, features-onchain, features-volatility, features-xinstrument) are reported
  as declared on NO cloud in unified-api-contracts/config/cloud-providers.yaml while their CLIs still accept
  asset_group_choices. This is a known side-effect of the Wave-3 bucket fold
  (plans/active/bucket_fold_features_2026_07_17.md, plans/active/bucket_fold_closeout_2026_07_17.md) that folded these 5
  per-family cloud-providers.yaml keys into a single 'features' key — the closeout doc's Alias-Sunset-Part-A entry
  explicitly lists check_asset_group_parity's _KIND_TO_FAMILY mapping-dict as a site 'correctly LEFT (legitimate,
  non-breaking)' at the time (2026-07-19), but the gate is now actively RED, blocking quality-gates.sh (and therefore
  quickmerge --agent's sentinel) for EVERY task in features-service, not just this one."
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer, admin]
tags: [features-service, quality-gates, asset-group-parity, bucket-fold, repo-blocker, qg-red]
related:
  [
    plans/active/bucket_fold_features_2026_07_17.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    plans/active/issues/features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md,
    plans/active/issues/api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md,
  ]
created: "2026-07-19"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# features-service quality-gates.sh RED at STEP 5.104 (asset-group parity gate) — stale post-fold kind mapping

## What I found

Dispatched onto `api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency-007` (fix
`features-service/features_service/sports/exporters/derived_features_helpers.py::_filter_completed_before` — entirely
unrelated to buckets/asset-groups). After landing that fix + tests, ran the full `bash scripts/quality-gates.sh` in
`features-service`: green through STEP 5.92 (17702 passed, 0 failed, 209 skipped), then **STEP 5.104 ASSET-GROUP PARITY
GATE fails** with 5 violations:

```
FAIL: 5 asset-group parity violation(s) between unified_api_contracts/config/cloud-providers.yaml and features-service:
  • 'features-delta-one' is declared on NO cloud (gcp/aws), but features_service/delta_one/cli/ still accepts
    asset_group_choices — every resolve_bucket(kind='features-delta-one', …) raises BucketNamingError.
  • 'features-mtf' — same pattern (features_service/multi_timeframe/cli/)
  • 'features-onchain' — same pattern (features_service/onchain/cli/)
  • 'features-volatility' — same pattern (features_service/volatility/cli/)
  • 'features-xinstrument' — same pattern (features_service/cross_instrument/cli/)
```

**Verified pre-existing per RULES.md § 4b**: `git stash push -u`, re-ran
`.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` directly on the clean tree at LDR HEAD —
byte-identical 5 violations — then `git stash pop` to restore my diff. This is not caused by my change (I touched only
`features_service/sports/exporters/derived_features_helpers.py` and its test file).

**Root cause (traced, not fixed — outside my task's craft/scope)**: `plans/active/bucket_fold_closeout_2026_07_17.md`'s
"ALIAS SUNSET Phase 2 Part A" entry (2026-07-19) already documents that the Wave-3 bucket fold
(`plans/active/bucket_fold_features_2026_07_17.md`) collapsed the 5 per-family `cloud-providers.yaml` keys
(`features-delta-one`/`features-mtf`/`features-onchain`/`features-volatility`/`features-xinstrument`) into a single
folded `features` key, and every live `resolve_bucket_name(kind=...)` caller was repointed to the folded kind. That same
entry explicitly calls out `check_asset_group_parity`'s `_KIND_TO_FAMILY` kind→family mapping-dict as a site that was
**"correctly LEFT (legitimate, non-breaking)"** at the time. That assumption is now invalidated: the gate script itself
(`scripts/quality_gates/check_asset_group_parity.py`) still expects the 5 OLD per-family keys to exist in
`cloud-providers.yaml`, and since the fold removed them, every run now fails. The gate's own error message names both
options: **(a)** restore the 5 per-family cloud-providers.yaml declarations, or **(b)** the families are genuinely
retired (folded into `features`) — drop them from `_KIND_TO_FAMILY` in the gate script and update the CLIs'
`asset_group_choices` accordingly if they're also stale.

**I did not make this judgment call** — it requires reading the Fold design doc
(`plans/active/bucket_estate_fold_design_2026_07_13.md`) + the actual current CLI/cloud-providers.yaml state to
determine whether (a) or (b) is correct, which is out of scope for this dispatch (data_engineering craft, a
features-service sports-fixture status-filter fix, not bucket-fold/infra work).

## Why it matters

- **Blocks every ship from features-service** — `quickmerge --agent` refuses whenever `scripts/quality-gates.sh` cannot
  write a fresh `.qg_last_passed_sha` sentinel, and it can't while STEP 5.104 is red. My own fix (green in isolation:
  full suite 17702 passed / 0 failed, new tests for the NS-status fix included) cannot ship via the mandated quickmerge
  flow until this repo goes green.
- This is the SAME class of "fold-closeout follow-up assumed non-breaking, turned out to actually break something"
  pattern already seen once in `features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md` (Cluster A) — a second
  independent instance suggests the Wave-3 bucket-fold closeout's "correctly LEFT" sites should get a fresh sweep rather
  than being assumed still-safe.

## Recommended decision / next steps

- [ ] [INFRA] P1. Determine the correct current state for the 5 folded families
      (features-delta-one/mtf/onchain/volatility/xinstrument): read
      `plans/active/bucket_estate_fold_design_2026_07_13.md` + current `cloud-providers.yaml` `features:` folded key +
      each CLI's `asset_group_choices` to decide whether these 5 families are genuinely retired (folded into `features`)
      or whether cloud-providers.yaml lost declarations it should still carry. (repo: unified-api-contracts /
      features-service)
- [ ] [INFRA] P1. Apply the determined fix: either (a) restore the 5 per-family `cloud-providers.yaml` declarations, or
      (b) drop the 5 retired families from `check_asset_group_parity.py`'s `_KIND_TO_FAMILY` dict AND remove/update the
      corresponding `asset_group_choices` entries in
      `features_service/{delta_one,multi_timeframe,onchain,volatility,cross_instrument}/cli/` so the CLIs no longer
      accept an asset_group with nowhere to write. Re-run `bash scripts/quality-gates.sh` end to end to confirm STEP
      5.104 (and the rest of the gate) goes green and a fresh sentinel is written. (repo: features-service,
      unified-api-contracts)
- [ ] [PROCESS] P3. Once fixed, re-check `plans/active/bucket_fold_closeout_2026_07_17.md`'s other "correctly LEFT
      (legitimate, non-breaking)" sites listed in the same Alias-Sunset-Part-A entry (the features e2e harness,
      `upgrade_manifest_to_v8.py`, `cloud_constants` legacy "positions" map, inference-config comments) for the same
      assumed-safe-but-now-broken pattern, given this is the second such instance found post-fold.

## Evidence

- Full run: `bash scripts/quality-gates.sh` in `.tabs/3/features-service` — green through STEP 5.92 (17702 passed, 0
  failed, 209 skipped, ~206s), FAILS at STEP 5.104 with 5 asset-group parity violations.
- Pre-existing verification: `git stash push -u -m "wip-check-preexisting-red"` (removed my sports-only diff) →
  `.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` on clean LDR HEAD → byte-identical 5 violations →
  `git stash pop` (restored my diff).
- My own scope (features-service sports `_filter_completed_before` NS-status fix): full `tests/` suite green in
  isolation (17702 passed / 0 failed / 209 skipped, including 3 new tests: `test_ns_status_with_goals_is_included`,
  `test_ns_status_without_goals_still_excluded`, `test_cancelled_status_with_goals_still_excluded`).

## Slot-3 action

Declared repo-blocker `qg_red` for `features-service` via `/api/repo-blockers` and continuing to `/blocked` or idle per
the RULES.md § 4b protocol — my task's own code is finished and correct but cannot ship until this gate is green.
