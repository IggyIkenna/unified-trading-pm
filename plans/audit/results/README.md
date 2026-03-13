# Audit Results Directory

Machine-readable audit results. One JSON file per repo per date.

## File naming

```
{repo}_{YYYY-MM-DD}.json
```

Example: `unified-trading-library_2026-03-13.json`

## JSON schema

```json
{
  "repo": "unified-trading-library",
  "date": "2026-03-13",
  "grade": "PASS",
  "pass_count": 12,
  "fail_count": 0,
  "warn_count": 3,
  "sections": [
    {
      "id": "s01",
      "title": "Governance",
      "result": "PASS",
      "details": "All governance checks passed."
    },
    {
      "id": "s02",
      "title": "Code Quality",
      "result": "WARN",
      "details": "basedpyright baseline has 4 suppressions."
    }
  ]
}
```

## Grade logic

- **PASS**: zero FAILs, zero or more WARNs
- **FAIL**: one or more section FAILs
- **WARN**: not used as top-level grade (PASS with warnings is still PASS)

## Produced by

- `scripts/audit/write-audit-result.sh` -- writes a single repo result
- `scripts/audit/aggregate-audit-summary.sh` -- aggregates all results for a date

## Consumed by

- `scripts/audit/run-audit-scriptable.sh` -- full audit runner
- CI workflows (read-only) for Telegram summaries and PR checks
