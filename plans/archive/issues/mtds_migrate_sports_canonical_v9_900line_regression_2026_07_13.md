---
doc_type: issue
title: market-tick-data-service QG RED — migrate_sports_canonical_v9.py crossed the 900-line ceiling
summary: >
  bash scripts/quality-gates.sh fails repo-wide on market-tick-data-service (STEP "Files exceed 900 lines" + "Codex
  compliance FAILED: 1 violations") because market_tick_data_service/scripts/migrate_sports_canonical_v9.py grew from
  896 to 934 lines in commit 13c53dfa ("feat(mtds): add explicit legacy-vs-canonical reconciliation to MDPS
  raw_tick_data migration", authored by slot-3, unrelated to my task). Verified pre-existing: the parent commit
  (13c53dfa^) has the file at 896 lines (under the 900 ceiling); 13c53dfa itself added 41 lines / removed 3, pushing it
  to 934. My own unrelated change (a new, separate audit script for aster_cefi_data_defi_bucket_migration_2026_07_13.md)
  cannot ship via quickmerge --agent while this repo-wide gate is red, since the green-tree rule blocks ANY commit until
  the full quality-gates.sh passes.
status: resolved
nature: notes
asset_group: [cefi, sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [qg-red, file-size, repo-blocker, codex-compliance]
related: [plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  aster_cefi_data_defi_bucket_migration-001 dispatch, slot 14, 2026-07-13 (blocked while shipping an unrelated audit
  script)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
  slot-9, 2026-07-13, market-tick-data-service@01f23b8c (verified quality-gates.sh green; fix already shipped by another
  slot as e284ad63)
---

# market-tick-data-service QG RED — migrate_sports_canonical_v9.py file-size regression

## What I found

`bash scripts/quality-gates.sh --no-fix` on `market-tick-data-service` at HEAD (`c2244d5f`, my own unrelated commit on
top of `13c53dfa`) fails with:

```
❌ Files exceed 900 lines:
  ./market_tick_data_service/scripts/migrate_sports_canonical_v9.py: 934 L
❌ Codex compliance FAILED: 1 violations (max allowed: 0)
```

Verified this is genuinely pre-existing, not caused by my commit — my only change is a new, separate file
(`scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`, ~230 lines) that does not touch
`migrate_sports_canonical_v9.py` at all:

```
$ git show 13c53dfa:market_tick_data_service/scripts/migrate_sports_canonical_v9.py | wc -l
934
$ git show 13c53dfa^:market_tick_data_service/scripts/migrate_sports_canonical_v9.py | wc -l
896
$ git show 13c53dfa --stat -- market_tick_data_service/scripts/migrate_sports_canonical_v9.py
 .../scripts/migrate_sports_canonical_v9.py | 44 ++++++++++++++++++++--
 1 file changed, 41 insertions(+), 3 deletions(-)
```

`13c53dfa` ("feat(mtds): add explicit legacy-vs-canonical reconciliation to MDPS raw_tick_data migration", authored by
slot-3/laptop, landed 2026-07-13 15:58 UTC+1) pushed the file from 896 → 934 lines, crossing the 900-line ceiling. This
was not caught before merge (presumably that slot's own QG run either predates this file reaching 900+ lines in their
local state, or the CODEX_MAX_VIOLATIONS ratchet only fires on a subsequent full run against the merged tree — not
investigated further, out of scope here).

## Why it matters

- Blocks EVERY subsequent commit to `market-tick-data-service` from any slot until fixed — the repo-wide green-tree rule
  means no one can ship via `quickmerge --agent` while `quality-gates.sh` is red, regardless of how unrelated their
  change is.
- I hit this while trying to ship `scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`
  (`aster_cefi_data_defi_bucket_migration_2026_07_13.md` Phase 1 Todo 1) — that work is DONE and committed locally
  (`c2244d5f`) but cannot land until this clears.

## Recommended decision

Split `migrate_sports_canonical_v9.py` back under 900 lines (the standard fix for this class of violation elsewhere in
the codebase — see `codex_violations_ratchet_to_five_2026_06_10.md` for the established split pattern/precedent). I did
not attempt this myself — it's the author's (or any data_engineering worker's) unrelated fix, out of my task's scope per
findings-triage ("outside-plan small+clear → ≤30 min" does not obviously apply here since a 934→<900 split of a
migration script needs domain understanding of what's safe to extract, not a mechanical trim).

## Todos

- [x] ✅ [REFACTOR] P1. Split `market_tick_data_service/scripts/migrate_sports_canonical_v9.py` (934 lines) back under
      the 900-line ceiling — extract a cohesive helper module (e.g. the "legacy-vs-canonical reconciliation" logic
      `13c53dfa` added, if it's separable) rather than an arbitrary line-count trim. Verify
      `bash scripts/quality-gates.sh` is green afterward. (repo: market-tick-data-service) — **DONE, slot 9,
      market-tick-data-service@`01f23b8c`.** Found the split already shipped by another slot (`e284ad63`, "fix(mtds):
      shrink migrate_sports_canonical_v9.py under the 900-line file-size gate") — `migrate_sports_canonical_v9.py` is
      now exactly 900 lines. Verified (did not just trust the line count): ran `bash scripts/quality-gates.sh --no-fix`
      fresh against current HEAD (`01f23b8c`, clean tree, no local changes) — **`✅ ALL QUALITY GATES PASSED (362s)`**,
      sentinel `.qg_last_passed_sha=01f23b8c...` written matching HEAD exactly, confirming the file-size gate + full
      codex-compliance sweep are genuinely green, not just the single file under the ceiling. No further code change
      needed.
