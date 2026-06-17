# R3 ⑬–⑲ verdict packs — 2026-06-17 (G3.5 pre-apply, regenerated on current LDR HEAD)

> **Purpose.** The CITADEL decision-#3 pre-apply gate set: per-AG **projected-v9 manifest** + **manifest_diff report**
> (projected vs current/live `_index`) + a **VERDICT line**, regenerated on **current LDR HEAD** (mtds/is/uac at
> 2026-06-17). Supersedes the `r3_beta_renders_2026_06_11/` packs (the corpus baseline + defi rebuild moved since).
> **This is operator-eyeball-ready AGENT PREP. It does NOT fire `G4 --apply`** (operator hard-stop).

## Verdict summary

| AG             | GATE (raw)              | Adjudicated verdict                                                                     | captured Δ (current→projected)       | schema   | pipeline_mode            |
| -------------- | ----------------------- | --------------------------------------------------------------------------------------- | ------------------------------------ | -------- | ------------------------ |
| **sports**     | GREEN 0/0               | **GREEN**                                                                               | 202,087 → 202,087 (flat)             | →v9 100% | →`batch_odds_api`        |
| **defi**       | removed=39,867 reg=105  | **GREEN** (additive; downgrades=phantom)                                                | 348,211 → 440,217 (+92,006)          | →v9 100% | blank→source-aware       |
| **cefi**       | removed=733 reg=375     | **GREEN** (additive; garbage+phantom justified)                                         | 1,332,922 → 2,491,437 (+1.16M)       | →v9 100% | blank→`batch_tardis`     |
| **tradfi**     | removed=4,374 reg=2,902 | **GREEN** (massively additive; phantom spot-verified)                                   | 100,787 → 902,878 (+802,091)         | →v9 100% | blank→`batch_massive`    |
| **prediction** | removed=3,588 reg=4     | **GREEN** (by-design raw→cqg-bundle grain; **75.3% coverage** on the expanded registry) | 16,968 raw cells → 7,116 cqg bundles | →v9 100% | →`batch_polymarket_clob` |

**Operator readout:** **clear to V6-eyeball + fire G4 `--apply` on ALL FIVE AGs** (defi, cefi, tradfi, sports,
prediction). No operator decision is outstanding.

> **Prediction correction (operator-prompted).** A first pass against the **06-11** projection showed prediction at 0.2%
> canonical coverage (542,170 `attempted_failed[ClassifierConfidenceLow]`) and was provisionally flagged
> BLOCKED-OPERATOR-DECISION. That was a **stale-projection artifact**: the cqg classifier lives in UAC, and the registry
> was expanded under **decision 338** in 3 UAC commits _after_ the 06-11 projection. Re-projecting on **HEAD** (against
> the expanded registry): **0.2% → 75.3% coverage, and 542,170 ClassifierConfidenceLow → 1.** The "frozen corpus →
> projection valid" shortcut held for defi/cefi/tradfi/sports (none has a moved UAC projection dependency) but NOT for
> prediction, whose rebuild calls the UAC cqg classifier. See `verdict_prediction.md`.

## How each pack was produced (reproducible)

```bash
# env (read/projection only — never writes prod _index)
export GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 \
       DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp MANIFEST_ALLOW_STALE_FALLBACK=true

# projection (HEAD) — defi only (its rebuild changed mtds@89807b4 2026-06-16; the other 4 rebuilds are
# unchanged since their 06-11 projection AND the market-data corpus is DRAINED/frozen since 06-08, so their
# existing projected_index_<ag>.parquet are HEAD-equivalent):
cd market-tick-data-service && .venv/bin/python market_tick_data_service/scripts/rebuild_defi_manifest.py \
  --dry-run --start-date 2020-01-01 --end-date 2026-06-17 \
  --beta-manifest-out gs://market-data-tick-defi-prd-central-element-323112/_index/audit/projected_index_defi_head20260617.parquet

# manifest_diff (projected vs live _index), per AG:
cd instruments-service && .venv/bin/python scripts/manifest_diff.py --asset-group <ag> \
  --projected gs://market-data-tick-<tag>-prd-…/_index/audit/projected_index_<ag>[ _head20260617].parquet \
  --current   gs://market-data-tick-<tag>-prd-…/_index/availability_index.parquet \
  --out manifest_diff_<ag>.json

# adjudication (respelling/data_type-supersession vs genuine regression):
python analyze_diff.py manifest_diff_<ag>.json
```

## Operator live dev render (the V6 eyeball — run by the operator)

The beta-render recipe is live (smoke-verified 2026-06-11). The projected indices are at the beta-blob path the
data-status views read:

```bash
DATA_STATUS_BETA_MANIFEST_BLOB='_index/audit/projected_index_{asset_group}.parquet' \
  bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api
#  (defi: projected_index_defi_head20260617.parquet — point the blob var at the _head file for defi)
#  → deployment-ui data-status tab shows the PROJECTED v9 coverage per AG (BETA); unset the env for the LIVE view.
```

Each `verdict_<ag>.md` embeds the **textual coverage render** (status distribution + coverage% + schema_version +
pipeline_mode/source distribution of the projected vs current `_index`) — the same numbers the data-status UI renders —
so the verdict is eyeball-complete without a browser.

## Inputs in this directory

- `manifest_diff_<ag>.json` — machine-readable projected-vs-current diff (cells add/remove/change, status-transition
  matrix, per-(ag,data_type,venue) row deltas).
- `analyze_diff.py` — the adjudication helper (respelling/data_type reconciliation + downgrade flagging).
- `verdict_<ag>.md` — the per-AG ⑬–⑲ verdict (render + diff + adjudication + verdict line).
- `pred_migrator_dryplan.txt` — R8 prediction migrator (`migrate_prediction_to_pred_prd_v9.py`) dry-plan on HEAD.

Full adjudication narrative also journaled in
`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` Progress Log (2026-06-17).
