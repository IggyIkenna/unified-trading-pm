---
title: "workspace-manifest.json: 10 repos in manifest but absent from disk"
created: 2026-05-18
resolved: 2026-05-20
author: slot-8
resolved_by: slot-1
source:
  - "work_split_2026_05_18_harsh.md item 11 (semver-agent label audit)"
locked_by: live-defi-rollout
---

## RESOLVED 2026-05-20 — unified-trading-pm@3ac7be47b

**Outcome**: 9 of 10 listed repos confirmed archived on GitHub (`gh api .archived = true`) and annotated
with `archived: true` in `workspace-manifest.json`. `fund-administration-service` was a false positive — it
IS present on disk and NOT archived on GitHub. 0 repos moved to `removedEntries` (all 9 still exist on
GitHub; manifest retains them for historical-commit resolution).

**Structural fix**: added disk-presence assertion to
`scripts/manifest/check-dependency-alignment.py` (lines 33-50 + 117-143 + 158-191). Exempt statuses:
`{archived, deprecated, deleted, future}` + prefixes `{consolidated-into-, merged-into-,
pending-archive-into-}` + entries with `archived: true` boolean. Future drift fails CI.

**Verification**: `python3 scripts/manifest/check-dependency-alignment.py --json` →
`aligned: true, disk_absent_count: 0`. Negative-path test (flipped one entry to status=active) correctly
surfaced disk_absent.

| Repo                                | GitHub `archived` | On disk | Cleanup applied        |
| ----------------------------------- | ----------------- | ------- | ---------------------- |
| `features-calendar-service`         | true              | absent  | `archived: true` added |
| `features-commodity-service`        | true              | absent  | `archived: true` added |
| `features-cross-instrument-service` | true              | absent  | `archived: true` added |
| `features-delta-one-service`        | true              | absent  | `archived: true` added |
| `features-multi-timeframe-service`  | true              | absent  | `archived: true` added |
| `features-onchain-service`          | true              | absent  | `archived: true` added |
| `features-sports-service`           | true              | absent  | `archived: true` added |
| `features-volatility-service`       | true              | absent  | `archived: true` added |
| `fund-administration-service`       | false             | present | none (false positive)  |
| `user-management-ui`                | true              | absent  | `archived: true` added |

---

## What I found

Running `check-dependency-alignment.py --json` returned `aligned: True` (dependency graph clean), but a secondary
disk-presence check found **10 repos** listed in `workspace-manifest.json` under `repositories:` that have no
corresponding directory under the workspace root:

| Repo                                | Expected path                            | Status |
| ----------------------------------- | ---------------------------------------- | ------ |
| `features-calendar-service`         | `$WS/features-calendar-service/`         | ABSENT |
| `features-commodity-service`        | `$WS/features-commodity-service/`        | ABSENT |
| `features-cross-instrument-service` | `$WS/features-cross-instrument-service/` | ABSENT |
| `features-delta-one-service`        | `$WS/features-delta-one-service/`        | ABSENT |
| `features-multi-timeframe-service`  | `$WS/features-multi-timeframe-service/`  | ABSENT |
| `features-onchain-service`          | `$WS/features-onchain-service/`          | ABSENT |
| `features-sports-service`           | `$WS/features-sports-service/`           | ABSENT |
| `features-volatility-service`       | `$WS/features-volatility-service/`       | ABSENT |
| `fund-administration-service`       | `$WS/fund-administration-service/`       | ABSENT |
| `user-management-ui`                | `$WS/user-management-ui/`                | ABSENT |

The `features-*-service` repos appear to be pre-consolidation entries (before they were merged into `features-service`).
`user-management-ui` was archived 2026-04-20 per the manifest tier rules note. `fund-administration-service` status
unclear.

## Why it matters

- `rollout-workflow-templates.sh` and `run-all-setup.sh` iterate manifest repos. Absent repos cause silent skips with no
  error — potential for workflow/template drift to go undetected.
- The `check-dependency-alignment.py` script passes (aligned=True) because it only checks dep versions, not disk
  presence — this is a blind spot.
- If any of these repos are re-cloned in future, they will inherit no semver-agent workflow (item 11 root cause class).

## Recommended decision

1. **Operator confirms**: are these repos permanently archived (remove from manifest) or temporarily absent (re-clone +
   setup)?
2. If archived → add `"status": "archived"` to each entry OR move to `removedEntries` block in manifest. The tier-rules
   note already states `user-management-ui` as archived; apply consistently.
3. If temporarily absent → re-run `bash unified-trading-pm/scripts/dev/run-all-setup.sh` to re-clone.
4. Add a disk-presence check to `check-dependency-alignment.py` to surface this class of drift proactively.
