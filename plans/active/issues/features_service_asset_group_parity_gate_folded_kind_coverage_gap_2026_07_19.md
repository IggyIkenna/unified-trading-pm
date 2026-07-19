---
doc_type: issue
title:
  "check_asset_group_parity.py has zero coverage for the folded 'features' bucket kind post Wave-3 fold — a per-family
  asset_group_choices drift, or an orphan yaml asset_group key, would now pass silently"
summary:
  "Fixed the RB-00065170 repo-blocker (STEP 5.104 red on live-defi-rollout) by emptying the stale _KIND_TO_FAMILY dict
  in features-service/scripts/quality_gates/check_asset_group_parity.py — the 5 per-family kinds it referenced
  (features-delta-one/mtf/onchain/volatility/xinstrument) were removed from cloud-providers.yaml by the Wave-3
  bucket-fold's Alias-Sunset Part-B yaml-mirror-sync (UAC@a8e7f46d), and every live resolve_bucket_name() caller in
  those families already writes kind='features' (the folded per-asset_group key), verified by grep. That fix is
  correct and sufficient to un-block the gate. But it leaves the gate with NO check at all for the folded 'features'
  key — the exact drift-prevention purpose the gate exists for (module docstring) now has a blind spot for the busiest
  bucket kind in the repo. While investigating whether to instead extend the gate to check the folded key, I found
  cloud-providers.yaml declares a SPORTS asset_group under the folded 'features' key on both clouds, but grep found no
  features-service family that ever calls resolve_bucket(kind='features', asset_group='sports') — sports writes to its
  own separate flat 'features-sports' key instead. That SPORTS entry may be a genuine orphan (same class of bug the
  2026-07-17 sweep found and this gate was built to catch), or intentional headroom for a not-yet-landed producer — I
  did not chase it down; it's a discovery, not a diagnosed root cause."
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer, admin]
tags: [features-service, quality-gates, asset-group-parity, bucket-fold, gate-coverage-gap]
related:
  [
    plans/active/bucket_fold_features_2026_07_17.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    plans/active/issues/features_service_qg_red_asset_group_parity_stale_kind_mapping_2026_07_19.md,
  ]
created: "2026-07-19"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
source: [agt-f86c6d]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

# check_asset_group_parity.py: no coverage for the folded 'features' kind + a possible orphan SPORTS key

## What I found

Resolving repo-blocker RB-00065170 (`ldr_qg_failure` escalation `agt-f86c6d`, STEP 5.104 ASSET-GROUP PARITY GATE red on
`features-service` `live-defi-rollout`). Confirmed via grep that the 5 families named in the stale `_KIND_TO_FAMILY`
dict (`delta_one`, `multi_timeframe`, `onchain`, `volatility`, `cross_instrument`) all now call
`resolve_bucket(kind="features", ...)` — the folded per-asset_group key — not their old retired per-family kind. The 5
old yaml keys are genuinely gone from `cloud-providers.yaml` (grep-clean, only comments referencing them remain),
removed by the Wave-3 bucket fold's Alias-Sunset Part-B yaml-mirror-sync
(`plans/active/bucket_fold_closeout_2026_07_17.md`, `UAC@a8e7f46d`). So the correct fix was to empty
`_KIND_TO_FAMILY` (shipped: `features-service@<see resolution commit>`), not to restore the old keys or touch any
CLI's `asset_group_choices` (which remain accurate — the families are NOT retired, only their per-family bucket key
is).

That fix is correct but leaves a gap: the gate's whole purpose (per its own docstring) is catching yaml↔code drift for
per-asset-group feature buckets, and the folded `features` key is now the SHARED, busiest bucket for 5+ families with
zero gate coverage. A future PR that adds a new `asset_group_choices` entry to one of these families' CLIs without a
matching `cloud-providers.yaml` declaration (or vice versa) would now pass STEP 5.104 silently — the exact
`BucketNamingError`-at-runtime / orphan-bucket-at-provision-time failure modes the gate exists to prevent.

While scoping whether to extend the gate inline (a union-of-invocable-asset-groups check across the families sharing
the folded key), I computed each family's invocable set:

```
delta_one:        CEFI, DEFI, PREDICTION, TRADFI
multi_timeframe:   CEFI, DEFI, TRADFI
onchain:           DEFI
volatility:        CEFI, TRADFI
cross_instrument:  CEFI, DEFI, PREDICTION, TRADFI
union:             CEFI, DEFI, PREDICTION, TRADFI
```

`cloud-providers.yaml`'s folded `features:` key declares `CEFI, TRADFI, DEFI, PREDICTION, SPORTS` on both GCP and AWS
— i.e. the union above is a full subset (no MISSING violation), but the yaml's `SPORTS` entry has no match in the
union (a potential EXTRA/orphan). Grepping every `features_service/*` family for
`resolve_bucket(kind="features", asset_group="sports"...)` found nothing — the sports family uses its own separate
flat `features-sports` key instead (`cloud-providers.yaml:80`), not the folded per-AG `features` dict. I did not
determine whether `features:SPORTS` is a genuine orphan (same bug class the gate exists to catch) or deliberate
headroom for a producer that doesn't exist yet — that determination + the gate extension are out of scope for this
one-shot CICD wall-clear.

There's also a `cefi` family (`features_service/cefi/`) that writes
`resolve_bucket(kind="features", asset_group="defi")` with a hardcoded literal, not a CLI `asset_group_choices` list —
it was never in `_KIND_TO_FAMILY` before the fold either, so it's pre-existing gate scope, not a fold regression, but
any redesign of the gate for the folded key needs to account for it (the current AST-based
`_invocable_asset_groups()` authority model assumes either a CLI list or a `_CONSTANT_AUTHORITY` module constant —
`cefi`'s inline literal is neither).

## Why it matters

- The parity gate's entire value proposition (preventing the exact class of orphan-bucket / mid-run `BucketNamingError`
  bugs the 2026-07-17 sweep found) is currently zero for the folded `features` kind, which is the bucket the majority
  of features-service families write through post-fold.
- This is the THIRD instance of the "fold-closeout follow-up assumed non-breaking, turned out to need attention"
  pattern in as many days (see `features_service_qg_red_bucket_symbol_ssot_drift_2026_07_18.md` and
  `features_service_qg_red_asset_group_parity_stale_kind_mapping_2026_07_19.md`'s own P3 recommendation to re-sweep
  the other "correctly LEFT" sites) — worth weighting when that re-sweep happens.

## Recommended decision / next steps

- [ ] [INFRA] P2. Design + implement a folded-kind parity check in `check_asset_group_parity.py`: for the shared
      `features` yaml key, verify the UNION of every contributing family's invocable `asset_group_choices` is exactly
      covered (both directions — MISSING and EXTRA) by the yaml's declared asset_group keys. Needs a documented
      registry of "which families write into the folded `features` kind" (at minimum: `delta_one`,
      `multi_timeframe`, `onchain`, `volatility`, `cross_instrument`; decide whether to also model `cefi`'s
      hardcoded-literal case, extending `_CONSTANT_AUTHORITY` or a new authority class for inline literals not bound
      to a module-level name). (repo: features-service)
- [ ] [DATA] P2. Determine whether `cloud-providers.yaml`'s `features:SPORTS` entry (GCP + AWS) is a genuine orphan
      (no current producer — same bug class as the 2026-07-17 sweep) or intentional headroom, and either wire up a
      real producer, drop the key, or document the deliberate reservation inline in the yaml. (repo:
      unified-api-contracts)

## Evidence

- `agt-f86c6d` resolution: `.venv/bin/python scripts/quality_gates/check_asset_group_parity.py` — RED (5 violations)
  before the `_KIND_TO_FAMILY` fix, `OK` after, on `features-service` at `live-defi-rollout` HEAD.
- Grep confirming all 5 families call `resolve_bucket(kind="features", ...)`:
  `features_service/{delta_one,multi_timeframe,onchain,volatility,cross_instrument}/**/*.py`.
- Grep confirming the 5 old per-family yaml keys are absent from `unified_api_contracts/config/cloud-providers.yaml`
  (comment-only references remain).
- Invocable-set computation via `_invocable_asset_groups()` (the gate's own authority function) for all 5 families,
  shown above.
