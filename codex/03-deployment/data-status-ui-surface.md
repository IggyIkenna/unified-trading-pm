---
scope: [engineer, admin]
---

# Data-Status UI Surface — Honest Coverage

> Codex SSOT for the per-asset-group honest-coverage % UI surface in the deployment-ui data-status tab. Created:
> 2026-05-12 · Plan: `plans/active/cross_asset_group_catalogue_audit_2026_05_10.md` Phase 2F.

## What is this

The deployment-ui `/data-status` tab includes a `HonestCoverageCard` component that shows at a glance how complete the
manifest data capture is across all five asset groups (cefi / defi / tradfi / sports / prediction). It is driven by a
daily-written GCS JSON blob and served through a thin deployment-api endpoint.

## Data contract

### Backend — GCS blob

Written daily by `instruments-service/scripts/measure_honest_coverage.py` (cron VM at midnight UTC):

```
gs://central-element-323112-honest-coverage/{YYYY-MM-DD}/coverage.json
```

Top-level keys:

| Key                  | Type                                                           | Description                         |
| -------------------- | -------------------------------------------------------------- | ----------------------------------- |
| `generated_at`       | ISO timestamp string                                           | UTC write time                      |
| `date`               | `YYYY-MM-DD` string                                            | The manifest snapshot date          |
| `by_asset_group`     | `Record<string, StatusCounts>`                                 | One entry per asset_group measured  |
| `by_venue`           | `Record<string, Record<string, StatusCounts>>`                 | Per-venue breakdown per asset_group |
| `by_venue_data_type` | `Record<string, Record<string, Record<string, StatusCounts>>>` | Per data_type per venue             |

`StatusCounts` shape (per capture_status bucket):

```json
{
  "captured": 1234,
  "empty_confirmed": 56,
  "attempted_failed": 7,
  "expected_unattempted": 89,
  "total": 1386,
  "coverage_pct": 89.03
}
```

`coverage_pct = captured / total × 100` where
`total = captured + empty_confirmed + attempted_failed + expected_unattempted`.

### API endpoint

```
GET /api/data-status/honest-coverage?date=YYYY-MM-DD
```

- Query param `date` defaults to today UTC.
- Returns raw JSON blob as-is (passthrough `Response`).
- 404 when the blob hasn't been written yet for the requested date.
- 500 if the blob exists but contains malformed JSON.

Source: `deployment-api/deployment_api/routes/data_status.py` → `get_honest_coverage()`.

## UI component

**`deployment-ui/src/components/HonestCoverageCard.tsx`**

- Fetches `getHonestCoverage(date?)` from `src/api/client.ts`.
- Renders a `Card` with one row per asset_group from `by_asset_group`.
- Each row: asset_group badge + stacked progress bar (captured=green / empty_confirmed=yellow / attempted_failed=red /
  expected_unattempted=gray) + coverage % label.
- Handles loading, 404 (no data for today yet — renders a muted "not yet measured" note), and error states.
- Placed at the top of `DataStatusTab`'s return (after the `UpcomingFixtures` gate, before the Coverage Summary Card).

## Styling conventions

- `captured` → `bg-emerald-500` / `text-emerald-600`
- `empty_confirmed` → `bg-yellow-400` / `text-yellow-600`
- `attempted_failed` → `bg-red-500` / `text-red-600`
- `expected_unattempted` → `bg-gray-300` / `text-gray-500`

## Operational notes

- Card silently hides itself when the API returns 404 (cron VM hasn't run yet for today).
- The cron VM runs once per day at midnight UTC; data for today is available by ~00:05 UTC.
- Re-run manually: `bash deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh`.
- Monitor events at `gs://central-element-323112-events/events/measure-honest-coverage/`.

## Cross-references

- `codex/02-data/availability-manifest-and-data-status.md` § "Honest-coverage measurement script + UI surface"
- `instruments-service/scripts/measure_honest_coverage.py` — the measurement script
- `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` — cron VM launcher
- `deployment-api/deployment_api/routes/data_status.py` → `get_honest_coverage()`
- `deployment-ui/src/components/HonestCoverageCard.tsx` — UI component
- `deployment-ui/src/api/client.ts` → `getHonestCoverage()`
