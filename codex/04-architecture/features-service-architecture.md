---
scope: [engineer, ml-engineer, admin]
---

# features-service architecture

## What "features-service" is

Single workspace repo `features-service` consolidating the previously-separate `features-onchain-service`,
`features-volatility-service`, `features-cross-instrument-service`, `features-sports-service`,
`features-prediction-service` and friends. The consolidation collapses 5–6 repos into one with sub-packages, a single
CLI surface, a single deployment topology, and a single launcher script per asset_group.

## Sub-package layout

```
features-service/
├── features_service/
│   ├── onchain/         (DeFi onchain features)
│   ├── volatility/      (cross-asset realized + implied vol features)
│   ├── cross_instrument/(cross-asset / cross-venue features)
│   ├── sports/          (sports features)
│   ├── prediction/      (prediction-market features)
│   └── shared/          (BaseCalculator, ManifestWriter wrappers, lookahead-bias guard)
├── api/                  (health router, /metrics)
└── scripts/              (CLI entry-points, smoke matrices)
```

Each sub-package owns its calculators. The shared `BaseCalculator` enforces:

- Lookahead-bias guard via UAC `availability_semantics` (every input row consumed must satisfy `input.available_at <=
  target_ts - horizon`; raises `LookaheadBiasError` strict-mode).
- 4-pillar write-gate validation per `record_captured` (row count > 0, NaN ratio per column under threshold, schema
  matches contract, cluster coverage ≥ expected for bundled shards).
- ServiceBootstrap lifecycle (STARTED / STOPPED / FAILED + per-instrument progress with row counts).

## CLI surface

Single CLI codepath with the workspace-standard axes:

```bash
features-service \
  --operation compute \
  --mode batch|live \
  --asset-group cefi|defi|tradfi|sports|prediction \
  --feature-family <family> \
  [--shard-key '...']
```

`--feature-family` is a UAC enum. The CLI dispatches to the right sub-package + calculator. Live-mode dispatch follows
the same pattern as MTDS / MDPS — no separate live-only entry-point.

CLI convention: [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md).

## feature_family axis

Every feature group declares its `feature_family` (UAC enum). The data-status drilldown surfaces feature_family as a
first-class shard axis — see
[`../02-data/data-status-drilldown-hierarchy.md`](../02-data/data-status-drilldown-hierarchy.md). This collapses what
used to be N per-repo silos into one feature catalog with N families.

## Deployment topology

| Cluster                   | What runs there                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------ |
| features-asset-scoped     | One instance per (asset_group, region) — colocated with MDPS for that asset_group (live pipeline)|
| features-cross-cutting    | Separate instance for cross-asset / cross-venue features that span asset_groups                  |

Topology SSOT: [`../05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md).

## Launcher

Single launcher per cluster shape:
`deployment-service/scripts/vm/launch-features-{asset_group_or_cross_cutting}-vm.sh`. Replaces the 8 prior
features-*-service launchers. Registered in `_SERVICE_LAUNCHER_SCRIPTS` and `VM_PREFIX_TO_BUCKET`.

## Live = batch

Same code, same calculator, same CLI, same deployment shape. Only `--mode` differs at the entry point; the calculator
core does not branch on mode.

## Cross-references

- Feature service pattern (calculator standard):
  [`../06-coding-standards/feature-service-pattern.md`](../06-coding-standards/feature-service-pattern.md)
- CLI convention: [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md)
- Data-status drilldown (feature_family axis):
  [`../02-data/data-status-drilldown-hierarchy.md`](../02-data/data-status-drilldown-hierarchy.md)
- Manifest write-gate: [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Launcher SSOT: [`../05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md)
- Live = batch: [`batch-live-symmetry.md`](batch-live-symmetry.md)
- ML lifecycle (downstream of features): [`ml-experiment-lifecycle.md`](ml-experiment-lifecycle.md)
