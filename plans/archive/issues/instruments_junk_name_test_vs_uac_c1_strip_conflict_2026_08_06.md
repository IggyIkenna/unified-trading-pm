---
doc_type: issue
title: >-
  instruments-service QG red — test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run asserts JunkSymbolError
  for "JeleÅ\x84" but UAC b3db68b5 strips C1 controls, so the junk row survives as "JELEA" and alignment is blocked
summary: >-
  instruments-service's quality-gates.sh fails `test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run`
  (added 2026-08-06 07:36 by instruments-service@497c4f5e) with `assert not any("JELE" in instrument_id)`. The test was
  authored against the OLD unified-api-contracts behavior where `_reject_junk_symbols` RAISED JunkSymbolError for the C1
  control char `\x84` in "JeleÅ\x84" (a UTF-8-as-Latin-1 mojibake of "Jeleń"). But UAC@b3db68b5 (landed 08:21, "strip C1
  control chars in canonical IDs instead of crashing catalogue") deliberately STRIPS U+0080-U+009F instead of raising —
  so "JeleÅ\x84" → "JeleÅ" → team_id "JELEA", the junk row survives in the rollup output, and the test's `not any("JELE"
  ...)` assertion fails. This is a cross-repo behavior mismatch between the newer UAC C1-strip decision and the older
  instruments test, NOT a defect in the aiohttp floor propagation. It blocks instruments-service from shipping its
  aiohttp pyproject bump, which in turn blocks the canonical-manifest regen (quickmerge STAGE 1.5 requires fleet
  alignment).
status: resolved
nature: issue
asset_group: [sports, infrastructure]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [qg-red, test-conflict, junk-symbol, canonical-ids, cross-repo, repo-blocker]
related:
  [
    /plans/active/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/archive/issues/aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md,
  ]
created: 2026-08-06
author: slot-4 (aiohttp propagation task)
priority: P1
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "instruments-service local QG during aiohttp floor propagation (aiohttp_canonical_floor_stale_vs_mtds_cve_fix-002),
    2026-08-06 09:5x UTC",
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Both todos done - test reconciled to UAC C1-strip behavior (instruments-service@a147b12a) and
> QG green (exit 0) unblocking the aiohttp floor propagation; no prose open question. Moved by the 2026-08-06 AO
> issue-doc archive sweep.

## What I found

- `instruments-service` local `quality-gates.sh` fails 1 test:
  `tests/unit/scripts/test_build_instrument_catalogue.py::test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run`.
- Failure: `assert not any("JELE" in str(row["instrument_id"]) for row in df.to_dict("records"))` → True.
- Root cause chain:
  1. The test (added by `instruments-service@497c4f5e`, 2026-08-06 07:36) feeds `"JeleÅ\x84"` (mojibake of "Jeleń") as a
     player/team name and expects `build_team_id`/`build_player_id` to raise `JunkSymbolError` (caught by the 497c4f5e
     try/except) so the row is skipped.
  2. But `unified-api-contracts@b3db68b5` (2026-08-06 08:21, "strip C1 control chars in canonical IDs instead of
     crashing catalogue") changed `_reject_junk_symbols` to STRIP C1 controls (U+0080-U+009F) rather than raise. `\x84`
     is U+0084 → stripped → `"JeleÅ"` → `build_team_id` returns `"JELEA"`.
  3. The junk row therefore survives with instrument_id containing "JELE" → the test assertion fails.
- The 497c4f5e try/except still works for the U+FFFD replacement char and C0 controls (which still raise); only the
  C1-strip case makes the test's premise stale.
- Verified NOT caused by the aiohttp floor bump: my diff is pyproject.toml only; the failing test file is byte-identical
  between origin/live-defi-rollout and my HEAD; the test has zero aiohttp references.

## Why it matters

- It makes instruments-service QG red at the current origin tip (the newer UAC behavior + the older test coexist), so
  instruments-service cannot ship ANY commit through quickmerge.
- It transitively blocks the aiohttp canonical-floor propagation (the aligned manifest regen cannot land while
  instruments-service stays at the old floor — quickmerge STAGE 1.5 requires fleet alignment).

## Recommended decision

Two ways to reconcile; pick the one that reflects the intended UAC behavior:

- **Option A (align test to UAC C1-strip)**: update the instruments test's third assertion to reflect that a C1 control
  char is stripped (row survives as a sanitized "JELEA" id) rather than raising. The 497c4f5e try/except stays as
  defense for U+FFFD/C0. Keep the test's core intent (no whole-rollup crash).
- **Option B (make UAC raise on C1 again)**: revert b3db68b5's strip decision to raise JunkSymbolError for C1, which
  restores the test's premise but reintroduces the catalogue-crash-on-mojibake failure mode that b3db68b5 fixed.

Recommendation: **Option A** — b3db68b5's C1-strip is the newer, deliberate design (matches the `_slug` ASCII-ignore
drop anyway) and the 497c4f5e fix's real goal (don't crash the whole rollup) is preserved either way.

## Todos

- [x] ✅ [TEST] P1. Update `instruments-service` `test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run` so
      its assertions match UAC b3db68b5's C1-strip behavior (Option A) — C1 chars strip (row survives as sanitized id),
      while U+FFFD/C0 still raise and are skipped. — instruments-service@a147b12a (fixture switched to U+FFFD junk
      marker; docstring documents the C1-strip behavior)
- [x] ✅ [DATA] P2. After the test is reconciled, re-run instruments-service `quality-gates.sh` and confirm green, so
      the aiohttp floor propagation (`aiohttp_canonical_floor_stale_vs_mtds_cve_fix_2026_08_03.md` todos 2-3) can land.
      — instruments-service@a147b12a QG green (exit 0); aiohttp bump d07b24b8 + test fix both verified on origin
