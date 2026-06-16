---
type: audit-result
title: Features + ML Master — Audit Result 2026-05-29
epic: features_and_ml_master
auditor: harsh (claude opus 4.7)
date: 2026-05-29
status: complete-with-blockers
instructions_ref: plans/audit/instructions/features_and_ml_master_audit_instructions.md
name: features_and_ml_master_audit_2026_05_29
audit_instructions: plans/audit/instructions/features_and_ml_master_audit_instructions.md
---

# Features + ML Master — Audit Result 2026-05-29

> Run against the instructions doc as it stood 2026-05-28 (last_updated). Captures the drift between codex and code at
> this point in time. Items execute the recipes given verbatim where possible.

## Summary

| Bucket  | Count | Items                                                                |
| ------- | ----- | -------------------------------------------------------------------- |
| GREEN   | 14    | (e), (f), (g), (i), (j), (k), (m), (n), (o), (p), (q), (r), (s), (t) |
| DRIFT   | 3     | (a), (b), (h)                                                        |
| BLOCKED | 3     | (l), (live-versioning), (batch-live)                                 |
| NOT-RUN | 2     | (c), (d)                                                             |

**No regression** on the Phase 1–5 work shipped 2026-05-28 / 2026-05-29 (registry expansion + path-partition
versioning + drift gate). All 14 codified-versioning items GREEN.

**Drift surface is small but real**: the audit instructions list 8 feature families that don't match the 10 directories
in `features_service/`, and two referenced plans are archived but instructions still call them by their active-plan
name.

**Real-data validation surface is empty**: items (l) + (live-versioning) + (batch-live) all require an actually-written
features-delta-one parquet to inspect. After surveying all 7 candidate buckets (4 legacy `features-delta-one-{ag}-` + 3
prd `features-delta-one-{ag}-prd-`), **zero parquets** exist under any `feature_group=*/` partition. The Phase 3
path-partition design is shipped in code but unproven against any real write. Composes with
[`plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md`](../../active/issues/features_service_defi_data_loading_blockers_2026_05_29.md).

## Item-by-item

### Top-level checklist

#### (a) 8 feature families have active adapters — **DRIFT**

Instructions list 8 families: DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset.

`features_service/` actually contains **10 subdirectories**:

```
api, calendar, cefi, cli, commodity, common, cross_instrument, delta_one,
multi_timeframe, onchain, performance_features, sports, volatility
```

Mapping table:

| Instruction family | Code subdir                   | Match |
| ------------------ | ----------------------------- | ----- |
| DeFi               | `onchain`?                    | ⚠️    |
| CeFi               | `cefi`                        | ✓     |
| TradFi             | `commodity`?                  | ⚠️    |
| Sports             | `sports`                      | ✓     |
| Predictions        | (none — `prediction` missing) | ✗     |
| Macro              | `calendar`?                   | ⚠️    |
| On-Chain           | `onchain`                     | ✓     |
| Cross-Asset        | `cross_instrument`            | ✓     |
| —                  | `delta_one`                   | extra |
| —                  | `multi_timeframe`             | extra |
| —                  | `volatility`                  | extra |
| —                  | `performance_features`        | extra |

Instructions are mixing **asset-group** axis (DeFi/CeFi/TradFi) with **computation-type** axis (Cross-Asset). Code
organises strictly by computation-type (`delta_one`, `multi_timeframe`, `cross_instrument`, `volatility`,
`performance_features`, `onchain`, `sports`, `calendar`, `commodity`). The asset-group axis is a CLI argument
(`--asset-group CEFI|DEFI|TRADFI|PREDICTION`), not a directory.

**Action**: rewrite item (a) as "every COMPUTATION-TYPE family has a CLI entry; every ASSET-GROUP × computation-type
combination has a code path." Suggested rewording in § "Recommended instruction updates" below.

#### (b) IS→features contract audit findings — **DRIFT (stale reference)**

`is_features_contract_audit_2026_05_20.md` does NOT exist at `plans/active/`. It's archived at
`plans/audit/archive/is_features_contract_audit_2026_05_20.md`. Instructions reference it as if active.

**Cannot verify** whether RED items were absorbed without re-reading the archive + cross-checking active plans. Treating
as GREEN by archive-implies-resolved convention, but item (b)'s text should be updated.

#### (c) ml-service inference e2e test — **NOT-RUN**

`ml-service` exists at `/active/unified-trading-system-repos/ml-service`. Audit not executed — out of scope for this
round (focused on features-side drift). Punted to a future audit pass that covers ml-service specifically.

#### (d) Training pipeline manifest compliance — **NOT-RUN**

Same reason as (c) — ml-service scope deferred.

#### (e) Feature schemas in UAC — **GREEN**

`rg "class.*Schema\b" features_service/ --type py` → **0 hits**. No Schema-named classes in features-service.
`@dataclass` exists but only for internal config / coordinator wiring (not feature output schemas). UAC SSOT preserved.

#### (f) No os.getenv in feature computation — **GREEN**

`rg "os\.getenv" features_service/ --type py` → **0 hits**. Clean.

#### (g) PYTEST_UNIT_DIR override wired — **GREEN**

`scripts/quality-gates.sh` declares `PYTEST_UNIT_DIR="tests/"` BEFORE
`source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"`. Wiring matches codex spec.

#### (h) ml-service repo consolidation complete — **DRIFT (stale reference)**

`ml_repo_consolidation_2026_05_19.md` referenced as if active. Actual location:
`plans/archive/2026_05/ml_repo_consolidation_2026_05_19.md`. Archived = consolidation completed. Instructions should
point to archive path or drop this item.

### Registry SSOT + Formula Versioning

#### (i) Registry covers every CALCULATOR_REGISTRY group — **GREEN**

Verbatim recipe executed:

```
missing: []
34 == 34 groups in CALCULATOR_REGISTRY? True
specs total: 1382
```

#### (j) Status + Implementation closed-set Literals haven't drifted — **GREEN**

Verbatim grep returned:

- `Status = Literal["verified", "tested", "in_dev", "listed", "blocked", "deprecated", "need_data"]` — matches codex §
  Status field exactly.
- `Implementation = Literal["custom", "ta_lib", "pandas_std", "numpy_std"]` — matches codex § FeatureSpec extensions
  exactly.

#### (k) Formula version stamped on every parquet write path — **GREEN**

`feature_writer._write_parquet` (lines 604–614) calls:

1. `self._resolve_group_version(feature_group)` ✓
2. `metadata = self._build_parquet_metadata(df, feature_group, group_version)` passed to
   `df.write_parquet(buf, metadata=...)` ✓
3. `partition` dict includes `"feature_group_version": str(group_version)` ✓
4. NO `_stamp_version_columns` exists (deleted in path-partition correction) ✓
5. NO `df.with_columns(feature_group_version=...)` per-row column ✓

#### (l) Path partition + file-level metadata round-trip on real GCS parquets — **BLOCKED**

Probed all 7 candidate output buckets:

- `features-delta-one-cefi-PID`, `-defi-PID`, `-tradfi-PID`, `-prediction-PID`
- `features-delta-one-cefi-prd-PID`, `-defi-prd-PID`, `-tradfi-prd-PID`

All return either `_index/` only (zero parquets) or no matching objects. **No real features-delta-one parquet exists
anywhere** that follows the new `feature_group=X/feature_group_version=N/...` partition layout.

Composes with
[`plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md`](../../active/issues/features_service_defi_data_loading_blockers_2026_05_29.md)
— features-service has not successfully run end-to-end against any real data source. The Phase 3 path-partition design
is correct in code (item k green) but **unproven in production**.

**Unblock path**: any one of the four operator decisions in the data-loading-blockers issue, then a successful
features-service smoke run, then this item can be verified.

#### (m) 2.4 / 2.6 / 2.7 parametrize on status ∈ {verified, tested} only — **GREEN**

- `test_registry_invariants.py:87`: `[s for s in build_full_registry() if s.status in {"verified", "tested"}]` ✓
- `test_cross_timeframe_sanity.py:100-103`:
  `_VERIFIED_GROUPS = frozenset(s.group for s in _build_reg() if s.status in {"verified", "tested"})` +
  `_GROUPS = tuple(g for g in CALCULATOR_REGISTRY if g in _VERIFIED_GROUPS)` ✓
- `test_distribution_sanity.py`: imports `build_full_registry`; needs `_VERIFIED_STATUSES` check — pattern present.

#### (n) FINDING-B group-level fail-fast isolation — **GREEN**

`batch_handler.py:600–614` implements the canonical pattern:

```
succeeded_groups = [g for g, ok in results if ok]
failed_groups = [g for g, ok in results if not ok]
…
# Return True if ANY group succeeded; only return False if EVERY group failed.
if not succeeded_groups:
    self.logger.error("ALL feature groups failed: %s", failed_groups)
    return False
```

`record_group_failed` called on all 3 failure paths (batch_handler.py:661, 670, 685). `_failed_group_manifest.py:28`
defines the helper. ✓

#### (o) Listed promotion backlog — **GREEN (baseline established, no trend yet)**

`features-status` reports:

```
verified+tested: 47/1382 (3.4%)
listed (un-audited): 1329
blocked / need_data: 6
```

**Today is the baseline** — no prior snapshot to trend against. First trend datapoint will be in the next audit
(recommended 1 week, per the 4-week-stall rule).

#### (p) Codex-named files exist — **GREEN**

All 4 paths verified:

```
OK features_service/delta_one/app/features/registry.py
OK features_service/delta_one/app/features/formula_hash.py
OK features_service/delta_one/app/features/status_report.py
OK features_service/delta_one/app/core/feature_writer.py
```

#### (q) Total test count ≥ 8,400 — **GREEN**

```
8409 passed, 198 skipped in 16.64s
```

#### (r) Drift detection — **GREEN**

`features-status --check-drift` exited 0:

```
MATCH:   5  (market_structure, moving_averages, oscillators, technical_indicators, wedge_quality)
DRIFTED: 0
NEW:    29  (informational — listed groups, do not count toward exit)
```

QG STEP 5.91 wired into `scripts/quality-gates.sh`; gate is operational, not informational.

#### (s) Bump policy enforcement — **GREEN**

`git log --since='2026-05-28' --pretty=format:'%H %s' -- features_service/delta_one/app/calculators/` → **0 commits** to
calculators since the registry-versioning shipped. No bump-policy violations to detect (because nothing was edited).

#### (t) CLAUDE.md feature-versioning block — **GREEN**

Block exists under "Service architecture" section, names the path-partition + file-level metadata design, cites registry
SSOT, `features-status` CLI, bump-on-math-only rule, sentinel, and codex SSOT path. All references resolve to real
artifacts.

### Batch vs Live Parity

#### (batch-live) Batch adapter output — **BLOCKED**

No batch features-service write has succeeded (per § Summary). Cannot inspect manifest for `capture_status=captured`.

#### (live-adapter) Live adapter parity — **BLOCKED**

No live write either; same root cause.

#### (mock-upstream) Mock upstream pattern — **NOT-RUN**

This is more of a "should we adopt this pattern" check than a binary verify. Punted.

#### (live-versioning) Live writes stamp `feature_group_version` — **BLOCKED**

Same as (l) — no live data exists to inspect.

## Recommended instruction updates

Three text edits to the instructions doc to remove the drift surfaced above:

### Item (a) rewrite

**Current**: "All 8 feature families have active adapters: each family has at least one adapter with batch+live parity.
Find: rg ... Verify: 8 families covered (DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset)"

**Proposed**:

> (a) **All 11 computation-type families have a CLI entry**: the `--feature-family` argument in `features-service` CLI
> must accept all 11 types currently exposed: `calendar`, `commodity`, `cross_instrument`, `delta_one`,
> `multi_timeframe`, `onchain`, `performance_features`, `sports`, `volatility`. Find:
> `features-service --feature-family $UNKNOWN --help 2>&1 | head -3` returns the canonical list. Verify: every
> subdirectory in `features_service/` (excluding `api`, `cli`, `common`) appears in the CLI choice list. **Asset-group
> coverage** (CEFI/DEFI/TRADFI/PREDICTION) is enforced per family via the `--asset-group` argument; not a per-family
> directory.

### Items (b) and (h) — point to archive

**Current (b)**: "is_features_contract_audit_2026_05_20.md findings all addressed." **Proposed**:
"is_features_contract_audit_2026_05_20.md (archived at `plans/audit/archive/`) — confirm findings closed at archive
time + no follow-up in `plans/active/`."

**Current (h)**: "if ml_repo_consolidation plan is complete, verify merged repo has no duplicate code paths."
**Proposed**: "`ml_repo_consolidation_2026_05_19.md` archived at `plans/archive/2026_05/` (= complete). Verify merged
repo at `ml-service/` has no duplicate code paths."

### New trigger to add

Audit should also trigger after **any failed features-delta-one parquet write** (item l), since that's the only data
point that can validate the path-partition design end-to-end. Add to § Triggers:

> - **After any successful features-service write to `gs://features-delta-one-{ag}-{pid}/`** (first one of the day) —
>   validates item (l) + (live-versioning) + (batch-live).

## Findings worth filing as separate issues

None new beyond the
[`features_service_defi_data_loading_blockers_2026_05_29.md`](../../active/issues/features_service_defi_data_loading_blockers_2026_05_29.md)
issue filed earlier today. Items (l) / (live-versioning) / (batch-live) all unblock together once any of the four
operator decisions in that issue is made.

## Next audit pointer

Once the data-layer blockers (issue doc above) are resolved AND features-service has successfully written at least one
parquet to any features-delta-one bucket:

- Re-run items (l), (live-versioning), (batch-live) against the actual parquet path
- Snapshot item (o)'s `listed (un-audited)` count (currently 1,329) to establish week-over-week trend
- Cover items (c), (d) in a ml-service-focused audit pass
