---
title:
  "Bucket-name SSOT drift is workspace-wide — `resolve_bucket_name` has zero callsites; everything uses legacy
  `get_bucket_name` (no env)"
created: 2026-05-28
author: harsh-main
source:
  - unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py
  - unified-trading-library/unified_trading_library/core/cloud_constants.py
  - unified-trading-library/unified_trading_library/instrument_lifecycle_loader.py
  - market-tick-data-service/market_tick_data_service/config/service_config.py
  - deployment-service/configs/cloud-providers.yaml
  - plans/active/cefi_venue_backfill_coverage_remediation_2026_05_27.md
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md
locked_by: live-defi-rollout
---

## What I found

While investigating `cefi_venue_backfill_coverage_remediation_2026_05_27.md` § 6I.A (_"Env-tiered bucket cutover
incomplete — writers still dual-write to the legacy no-env bucket"_), I expected to find one writer omitting `env=` from
`resolve_bucket_name()`. Instead I found the architectural drift goes much deeper:

### Fact 1 — the canonical SSOT helper has zero callsites

`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud, kind, asset_group)` (at
[bucket_naming.py:295](../../../unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py#L295))
reads `deployment-service/configs/cloud-providers.yaml` which carries the env-tiered templates:

```yaml
market-data:
  CEFI: "market-data-tick-cefi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"
  DEFI: "market-data-tick-defi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"
  TRADFI: "market-data-tick-tradfi-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"
  SPORTS: "market-data-tick-sports-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}"
```

Per `unified-trading-pm/cursor-configs/CLAUDE.md` § "Bucket-name SSOT": _"Every bucket lookup via
`resolve_bucket_name(...)` — never inline `gs://` f-string. `deployment-service/configs/cloud-providers.yaml` is
canonical. QG STEP 5.69 enforces."_

**Workspace-wide grep** (`rg -nE 'resolve_bucket_name\(' --type py --glob '!.venv*'`) returned **0 hits**. The SSOT
helper is wired up and tested but no production code invokes it.

### Fact 2 — everyone uses the legacy helper which has no env at all

`unified_trading_library.core.cloud_constants.get_bucket_name(domain, asset_group)` at
[cloud_constants.py:174](../../../unified-trading-library/unified_trading_library/core/cloud_constants.py#L174) returns
`{prefix}-{category}-{project_id}` — the LEGACY no-env shape — using the `BUCKET_PREFIXES` dict at
[cloud_constants.py:130](../../../unified-trading-library/unified_trading_library/core/cloud_constants.py#L130) that
defines per-cloud per-domain prefixes but never references `DEPLOYMENT_ENV_SHORT`.

MTDS makes this explicit in its config docstring at
[`config/service_config.py:4`](../../../market-tick-data-service/market_tick_data_service/config/service_config.py#L4):

> _"Bucket names: UTL cloud_constants.get_bucket_name(\"market-data-tick\", category) constructs
> market-data-tick-{category}-{gcp_project_id} automatically."_

So MTDS — by design — uses the legacy helper that omits env. The `tick_data_bucket_prefix` field default at line 37 is
`"market-data-tick"` (no env suffix), and the docstring at line 39 says _"full name:
{prefix}-{category}-{gcp_project_id}"_ — legacy shape, by design.

### Fact 3 — UTL has at least one more hardcoded legacy-shape source

[instrument_lifecycle_loader.py:43](../../../unified-trading-library/unified_trading_library/instrument_lifecycle_loader.py#L43)
hardcodes a `_BUCKETS` dict:

```python
_BUCKETS: Final[dict[str, str]] = {
    "cefi": "market-data-tick-cefi-{pid}",
    "defi": "market-data-tick-defi-{pid}",
    "tradfi": "market-data-tick-tradfi-{pid}",
    "sports": "instruments-store-sports-{pid}",
    "prediction": "market-data-tick-prediction-{pid}",
}
```

No `${DEPLOYMENT_ENV_SHORT}` placeholder. Pure legacy shape.

### Fact 4 — GCS evidence matches the architecture (legacy bucket is fresh, canonical is stale)

From `cefi_venue_backfill_coverage_remediation_2026_05_27.md` § 6I (ikenna 2026-05-27 spot-check):

- Canonical: `market-data-tick-cefi-prd-central-element-323112` — latest captured **2026-05-07**
- Legacy: `market-data-tick-cefi-central-element-323112` — latest captured **2026-05-24** (17 days fresher)

That's not "a writer accidentally hit the legacy path" — that's "every writer hits the legacy path; the canonical bucket
has only the data from whatever brief experiment populated it back in May".

## Why it matters

1. **Data correctness across 5 asset_groups.** This isn't cefi-specific. defi, tradfi, sports, prediction all use the
   same UTL helper that returns the legacy no-env shape. Any reader that resolves to the canonical env-tiered bucket
   sees stale-or-empty data — looks like a coverage gap, triggers spurious re-fetches (Tardis cost) or false-alarm
   alerts.

2. **May-23 gate-3 blocker.** The DeFi cutover assumes batch and live read/write the same canonical bucket. If live
   writes go to `market-data-tick-defi-{pid}` (legacy) and a batch reconciler reads `market-data-tick-defi-prd-{pid}`
   (canonical) you get phantom drift on every date.

3. **The Phase 2.6 migration plan is blocked.**
   [`bucket_name_ssot_canonicalisation_2026_05_10.md`](../bucket_name_ssot_canonicalisation_2026_05_10.md) was the
   workspace-wide migration to env-tiered buckets. The yaml was updated but the consumer migration didn't happen (or
   stalled). The plan probably needs a Phase 3 / re-baseline.

4. **QG STEP 5.69 is not catching this.** The STEP greps for inline `f"gs://..."` URI construction. The legacy helper
   `get_bucket_name()` is a _function call_, not an inline f-string, so the QG doesn't trip on the legacy-shape return.
   The architecture drift is invisible to the existing ratchet.

5. **§ 6I.A in the cefi remediation plan understated the scope.** The plan item says "find the launcher/config not going
   through `resolve_bucket_name(..., env=DEPLOYMENT_ENV_SHORT)`" — but `resolve_bucket_name` has zero callers, so this
   isn't a single-writer find-and-fix; it's the whole architecture.

## Recommended decision

Closed-set options for Ikenna (owns MTDS / data-pipeline migration):

### A — workspace-wide migration to `resolve_bucket_name` (the canonical fix)

Re-open / restart `bucket_name_ssot_canonicalisation_2026_05_10.md`. Identify every callsite of `get_bucket_name`
workspace-wide; migrate each to `resolve_bucket_name`. Update UTL's `instrument_lifecycle_loader._BUCKETS` to read from
yaml via the new helper. Deprecate the legacy helper (or wire it to delegate to the new helper). QG STEP 5.69 extended
to grep for the legacy helper name as well.

**Effort**: multi-day across MTDS / MDPS / UTL / instruments-service / features-service. **Risk**: large blast radius;
needs pre-migration drain (per the HARD RULE). Coordinated with the AWS↔GCP parity work.

### B — env-aware shim on the legacy helper

Make `get_bucket_name(domain, asset_group)` itself env-aware: read `DEPLOYMENT_ENV_SHORT` from `UnifiedCloudConfig` and
append it to the returned string. Update all callsites implicitly (no caller changes needed).

**Effort**: 4-8 hrs. **Risk**: smaller blast radius but breaks current test fixtures that mock the legacy shape. Also
leaves the architectural drift (two helpers, same purpose) — just patches the symptom.

### C — targeted writer-only patch (cefi-specific)

Find whatever ultimately decides the cefi MTDS write bucket and force it to read the yaml via `resolve_bucket_name`.
Other asset_groups stay broken.

**Effort**: 2-4 hrs. **Risk**: low for cefi, but doesn't fix defi (May-23 critical path), tradfi, sports, prediction.
Creates per-asset_group inconsistency.

### D — declare batch↔live use legacy bucket only (de-canonical the env-tiered path)

Accept the legacy no-env shape as canonical post-cutover; remove env-tiered yaml templates

- `resolve_bucket_name` helper; update `bucket_name_ssot_canonicalisation_2026_05_10.md` to SUPERSEDED. Clean up the
  dual-path drift by deleting the unused path.

**Effort**: 1-2 days (mostly plan rewrites + helper deletion + QG STEP 5.69 removal). **Risk**: contradicts the
workspace HARD RULE; locks us into single-env operation; would need operator sign-off on the architectural reversal.

**My lean**: A is the workspace-correct answer but it's big. **B** seems like a reasonable bridge — get env awareness
into the legacy helper _now_, then drive the full A migration as post-cutover work. But this is Ikenna's call as MTDS /
data-pipeline owner.

## Cross-references

- Cefi remediation §6I.A item that surfaced this (now to be marked `[BLOCKED-DEPENDENCY]`):
  [`cefi_venue_backfill_coverage_remediation_2026_05_27.md` § 6I](../cefi_venue_backfill_coverage_remediation_2026_05_27.md)
- Original bucket migration plan (likely stalled / partially shipped):
  [`bucket_name_ssot_canonicalisation_2026_05_10.md`](../bucket_name_ssot_canonicalisation_2026_05_10.md)
- Hardcoded legacy-shape consumers (incomplete list — search reveals more in MDPS + scripts):
  - `unified-trading-library/unified_trading_library/instrument_lifecycle_loader.py:43`
  - `unified-trading-library/unified_trading_library/emission_publisher.py:301`
  - `unified-trading-library/unified_trading_library/io/streaming_shard_finalizer.py:31`
  - `unified-trading-library/unified_trading_library/core/cloud_constants.py:130`
  - `unified-trading-library/unified_trading_library/core/config.py:278`
  - `unified-trading-library/unified_trading_library/core/cloud_data_provider.py:430`
  - `market-tick-data-service/market_tick_data_service/config/service_config.py:36`
  - `market-data-processing-service/market_data_processing_service/config.py:497-498`
  - (workspace grep for `market-data-tick` returned ~30 hits — full list available on request)

## Status log

- 2026-05-28 harsh-main filed this issue doc during §6I.A investigation; cross-pinged ikenna-main; cefi §6I.A item
  marked `[BLOCKED-DEPENDENCY]` pending Ikenna's scope decision.
