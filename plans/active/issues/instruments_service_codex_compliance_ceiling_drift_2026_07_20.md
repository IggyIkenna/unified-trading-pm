---
doc_type: issue
title:
  "instruments-service codex-compliance ceiling drifted (3→4) — 3 oversized sports-orchestrator functions regrew past
  the 200L gate"
summary: >-
  Discovered incidentally while shipping an unrelated DeFi fix: instruments-service `quality-gates.sh`'s
  `CODEX_MAX_VIOLATIONS=3` ceiling was being exceeded (measured 4) with a DIFFERENT violation composition than the
  2026-06-11 ratchet comment documents. Root cause: `sports_reference_core.py`/`sports_reference_fixtures.py` were
  decomposed out of `FUNCTION_SIZE_EXTRA_EXCLUDES` on 2026-06-11 because every function passed the 200L method / 900L
  file gates post-split — but by 2026-07-20 three functions had regrown past the limit (`_fetch_teams_and_standings`
  205L, `_write_per_fixture_entities` 253L, `emit_empty_gaps_for_entity` 89L, the last via a class-context method gate).
  Re-excluded both files (documented in `QUALITY_GATE_BYPASS_AUDIT.md`) to restore the ceiling and unblock shipping —
  this is a WORKAROUND, not a fix. The other 2 tolerated violations (`Empty dict/list fallback`, `Hardcoded prod project
  ID`, both in `tests/unit/test_smoke_matrix.py`) were left as-is (already within the historical ceiling, out of scope
  for this fix).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [codex-compliance, tech-debt, function-size, ratchet, sports, orchestrator]
related: [codex_violations_ratchet_to_five_2026_06_10]
created: 2026-07-20
priority: P2
parent_epic: instruments_master
source:
  "Discovered during defi_catalogue_available_to_false_delisting_2026_07_20 close-out (slot-3, 2026-07-20) — a full
  quality-gates.sh run for an unrelated DeFi fix surfaced this pre-existing, unrelated drift."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# instruments-service codex-compliance ceiling drift

## Why this exists (provenance, 2026-07-20)

While shipping `defi_catalogue_available_to_false_delisting_2026_07_20` (unrelated), a full local
`quality-gates.sh --no-fix` run failed on `Codex compliance FAILED: 4 violations (max allowed: 3)`. Investigation
established with certainty that **none of the 4 violations touch any file this session modified** — confirmed by
`git log --oneline c37d4f96..origin/live-defi-rollout -- <all 7 candidate files>` returning zero commits, and by the
fact my very first QG run immediately after shipping `c37d4f96` (before any other agent's work landed) already showed "3
violations (within tolerance of 3)" with the SAME `CODEX_MAX_VIOLATIONS=3` ceiling.

## The four violations (measured 2026-07-20)

1. **`Empty dict/list fallback — fail fast`** — `tests/unit/test_smoke_matrix.py` (hardcoded prediction-bucket string
   literals).
2. **`Hardcoded prod project ID in tests`** — same file, `central-element-323112` literal in test assertions.
3. **`broad except Exception:`** — many pre-existing sites across
   `engine/orchestrator/{sports_fixtures,sfi, transfermarkt,weather}.py` +
   `reference_data/utils/{evm_creation_resolver,block_resolver}.py` + `reference_data/adapters/defi/_solana_utils.py`.
   This is a single boolean check (any hit anywhere in `$SOURCE_DIR` outside `tests/`), so partial exclusion does not
   clear it — NOT addressed here (too many pre-existing sites to audit individually under this session's time budget;
   left as the pre-existing tolerated violation).
4. **`Function/class/method size exceeded`** — `sports_reference_core.py:140`
   `_AfManifestHooks. emit_empty_gaps_for_entity()` 89L, `sports_reference_core.py:340` `_fetch_teams_and_standings()`
   205L, `sports_reference_fixtures.py:584` `_write_per_fixture_entities()` 253L. **This is the one addressed here**
   (see Root cause).

## Root cause

`scripts/quality-gates.sh`'s `FUNCTION_SIZE_EXTRA_EXCLUDES` array comment (2026-06-11) states:

> `process.py` (`process_instruments` 1,931L → staged `process_*` sibling modules) and `sports_reference.py`
> (`_fetch_sports_reference_data` 882L → `sports_reference_core`/`_fixtures` sibling modules) were decomposed and
> **REMOVED from this list** — they now pass the 900-line/200-line gates directly.

That was true in 2026-06-11. By 2026-07-20 it no longer is — the AST-based size checker
(`scripts/quality-gates-base/ base-library.sh`, `FSIZES` block) measures the 3 functions above exceeding their
respective gates. Since neither file appears in `git log c37d4f96..origin/live-defi-rollout`, this regrowth happened via
commits that landed **before** `c37d4f96` (i.e., pre-existing drift this session's `git log` window doesn't cover) —
sometime between 2026-06-11 and whenever `c37d4f96`'s parent was cut. No one has re-audited the ceiling since.

## What was done (workaround, not a fix)

Re-added both files to `FUNCTION_SIZE_EXTRA_EXCLUDES` in `scripts/quality-gates.sh` (mirroring the exact 2026-06-11
exclusion style) + documented in `QUALITY_GATE_BYPASS_AUDIT.md`. This restores `V=3` (broad-except + the 2
`test_smoke_matrix.py` violations), matching the ceiling — **unblocks shipping**, does **not** fix the underlying
function-size debt.

## Follow-on work (tracked)

- [x] [BACKEND] P2. **Decompose the 3 regrown functions** back under the 200L/class-method gate, same staged-sibling-
      module pattern as the 2026-06-11 split (`_fetch_teams_and_standings` → helper extraction;
      `_write_per_fixture_entities` → helper extraction; `emit_empty_gaps_for_entity` → helper extraction). Then remove
      both files from `FUNCTION_SIZE_EXTRA_EXCLUDES` again (mirroring the 2026-06-11 precedent) and drop this row from
      `QUALITY_GATE_BYPASS_AUDIT.md`. — `instruments-service@ac22305c` (2026-07-21). Operator decision
      (AskUserQuestion): "Dispatch it now" rather than defer. 9 new named helpers across both files; both files pass the
      200L/50L gates directly again; `QUALITY_GATE_BYPASS_AUDIT.md` row dropped in the same close-out pass. Evidence:
      `quality-gates.sh --no-fix` green (3 violations, back within tolerance — the other 2 pre-existing tolerated
      violations below are untouched), sentinel==HEAD.
- [ ] [DATA] P3. **Audit the other 2 tolerated violations** (`tests/unit/test_smoke_matrix.py` — empty dict/list
      fallback + hardcoded prod project ID) — determine if `"test-project"` (the check's own suggested literal) is a
      safe drop-in replacement without breaking the test's actual intent (verifying `resolve_test_bucket()`'s behavior
      when given a real project-id-shaped string).
- [ ] [DECISION] P3. **Audit the `broad except Exception:` sites** (`evm_creation_resolver.py` ×4, `block_resolver.py`,
      `_solana_utils.py` ×3, plus the 4 orchestrator files) — narrow each to a specific exception type where the actual
      failure mode is known (mirrors the fix already applied to the NEW
      `instruments_service/oracle/defi_removal_probe.py` module in the same session: `blob_exists()` pre-check +
      `except (json.JSONDecodeError, UnicodeDecodeError, OSError)` instead of bare `except Exception:`).

## Note (2026-07-23, found via a sports issue-doc re-triage sweep)

`sports_reference_function_size_qg_regression_2026_07_16.md` describes the SAME 3 functions/line-counts and was
independently re-verified today as fully resolved by this same commit (`instruments-service@ac22305c`) — that doc's
`status:` has been flipped to `resolved`. `status:` here intentionally left `open` (not flipped) — the size-regrowth
todo above is done, but the other 2 follow-on todos (test_smoke_matrix audit, broad-except audit) are still `[ ]` and
genuinely unstarted, so this doc as a whole is not fully resolved.
