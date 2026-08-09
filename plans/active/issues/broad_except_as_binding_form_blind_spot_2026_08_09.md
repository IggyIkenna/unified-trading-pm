---
doc_type: issue
title: >-
  QG "No broad except Exception" check is blind to the `except Exception as X:` binding form — 77 real occurrences
  across 31 unified-trading-pm scripts/ files never trip the zero-tolerance gate
summary: >-
  While shipping the fix for `pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md` (narrowing all 21 literal
  `except Exception:` occurrences the gate DOES catch), found a THIRD occurrence in
  `scripts/repo-management/ci_failure_watcher.py` (`_write_firestore_ci_watcher()`, line ~1999) that was never in that
  doc's 21-item inventory: `except Exception as exc:`. The gate's check (`scripts/quality-gates-base/base-service.sh`
  STEP ~5.5, `codex_rg "except Exception:"`) is a literal-substring regex requiring the colon immediately after
  `Exception` — `except Exception as exc:` does not match it at all, so this form is COMPLETELY INVISIBLE to the
  zero-tolerance ratchet, not merely bypassed via `BE_EXCLUDE_GLOBS` (which would at least be documented/tracked). A
  corpus-wide sweep (`rg "except Exception as" --type py --glob "!tests/**" scripts/`) found 77 more real occurrences
  across 31 files, none excluded, none narrowed, none visible to the gate. Fixed the one instance found in-file
  (ci_failure_watcher.py, same Firestore best-effort-write pattern as the literal-colon sibling in
  promotion_lag_monitor.py); the other 76 are out of scope for this session and filed here.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, codex-compliance, qg-blind-spot, broad-except, regex-gap]
related:
  [/plans/active/issues/pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md, /QUALITY_GATE_BYPASS_AUDIT.md]
created: 2026-08-09
author: slot-24 (backend_engineer)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
drift_direction: advance-code
sequential: false
locked_by:
context_scope: [/QUALITY_GATE_BYPASS_AUDIT.md, scripts/quality-gates-base/base-service.sh, scripts/quality-gates.sh]
resolved_by:
source: >-
  Discovered 2026-08-09 (slot-24) as a drive-by while fixing the 21 literal `except Exception:` occurrences
  `pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md` tracks — cross-referencing that doc's inventory
  against `ci_failure_watcher.py`'s actual content surfaced a 22nd, undocumented occurrence using the `as X:` binding
  form, which led to the corpus-wide sweep below.
depends_on: []
---

# `except Exception as X:` is invisible to the broad-except QG gate — 77 occurrences across 31 files

## What I found

`scripts/quality-gates-base/base-service.sh`'s "No broad except Exception" check runs
`codex_rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/"` — a literal substring
match requiring `Exception:` (colon immediately after the class name, no space). Python's `except Exception as exc:` /
`except Exception as e:` / `except Exception as _exc:` forms put ` as <name>:` between `Exception` and the colon, so the
regex never matches them — the check has ZERO visibility into this form, not "excluded and documented" but genuinely
blind.

Found while narrowing the sibling issue's 21 tracked occurrences: `scripts/repo-management/ci_failure_watcher.py`'s
`_write_firestore_ci_watcher()` (line ~1999) has
`except Exception as exc:  # Firestore unavailable → best-effort write; but make it VISIBLE` — same
Firestore-best-effort-write pattern as the file's own already-tracked occurrence and as `promotion_lag_monitor.py`'s
(both already fixed this session), but this one was never in the original 21-item inventory because the gate never saw
it. **Fixed in-file** as part of this session's ci_failure_watcher.py work: narrowed to
`except (ImportError, GoogleAPICallError) as exc:`.

Corpus-wide sweep (`rg "except Exception as" --type py --glob "!tests/**" scripts/`, 2026-08-09): **77 occurrences
across 31 files**, none excluded via `BE_EXCLUDE_GLOBS`, none narrowed, all currently invisible to the gate:

```
scripts/openapi/generate_ui_reference_data.py   (26×)
scripts/plan-hygiene/fix_frontmatter.py          (4×)
scripts/sports/migrate_sports_gcs_to_hive.py     (4×)
scripts/cicd/ci_status_store.py                  (3×)
scripts/migration/backfill_pipeline_mode.py      (3×)
scripts/openapi/audit_venue_coverage.py          (3×)
scripts/qg/honest_coverage_ratchet.py            (3×)
scripts/cicd/version_registry_store.py           (2×)
scripts/openapi/audit_prospectus_vs_codex.py     (2×)
scripts/openapi/generate_system_topology.py      (2×)
scripts/openapi/generate_strategy_prospectus.py  (2×)
scripts/validation/validate-buildspec.py         (1×)
scripts/validation/validate-cloudbuild.py        (1×)
... (18 more files, 1× each — full list via the rg command above)
```

`generate_ui_reference_data.py` (26×) dominates — that file's `except Exception as e:` pattern repeats per UAC/UIC
registry-extraction block (each one degrades to a per-field `"EXTRACTION_ERROR"` marker rather than crashing the whole
spec generation, same shape as the ONE occurrence this session already narrowed in that file at line ~141, which used
the literal-colon form and so WAS caught).

## Why it matters

This is the same class of finding as `pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md`'s "NEW FACET" (a
zero-tolerance gate that can't be trusted) — except that finding's root cause turned out to be _documented_
`BE_EXCLUDE_GLOBS` bypasses (traceable, if under-documented), while this one is a genuine regex gap with NO bypass
mechanism involved at all. A worker introducing a brand-new `except Exception as exc:` anywhere in `scripts/` today gets
a clean, green "✅ No broad except Exception" — the gate is not just tolerant of this pattern, it cannot see it exist.
77 pre-existing occurrences is the current debt; the ongoing risk is that this pattern accumulates freely going forward
with the gate offering zero signal.

## Recommended decision

Two independent tracks:

1. **Fix the regex gap first** (cheap, high-leverage — closes the gate hole for every future commit): change
   `codex_rg "except Exception:"` to also match the binding form, e.g. `codex_rg 'except Exception(\s+as\s+\w+)?:'` (or
   equivalent ripgrep `-P`/PCRE pattern), OR migrate to an AST-based scan like
   `scripts/quality_gates/check_no_fallback_imports.py`/`check_imports_inside_functions.py` already do for their own
   checks (more robust, catches both forms plus multi-except tuples, immune to string-literal false positives like
   `audit_dead_code.py`'s). Re-baseline `CODEX_MAX_VIOLATIONS`/`BE_EXCLUDE_GLOBS` once the corpus is swept — a hard
   `V=0` cutover the moment the regex widens will immediately re-red the gate on all 77 sites, so this needs to land
   AFTER (or atomically with) track 2, or as a ratchet-baselined count like `check_no_fallback_imports.py` uses, not a
   boolean zero-tolerance flip.
2. **Narrow the 76 remaining occurrences** (ci_failure_watcher.py's is already done) — same per-file review discipline
   as the sibling issue's P3 todo, file-by-file judgment on what each try-block actually expects to fail. Start with
   `generate_ui_reference_data.py` (26× in one file, mechanically similar per-block — likely the highest-leverage single
   file).

## Todos

- [ ] [BACKEND] P2. Widen `scripts/quality-gates-base/base-service.sh`'s broad-except detection
      (`codex_rg "except Exception:"`) to also catch the `except Exception as X:` binding form — either a widened regex
      or an AST-based rewrite (mirror `check_no_fallback_imports.py`'s approach). Convert `CODEX_MAX_VIOLATIONS` for
      this specific check to a ratchet-baselined count (seed baseline = current corpus count) rather than a hard `0`, so
      widening the regex doesn't instantly red every repo the moment it lands — narrow the baseline down as track-2
      todos below land. Repo: unified-trading-pm (`scripts/quality-gates-base/`).
- [ ] [BACKEND] P2. Narrow all `except Exception as X:` occurrences in `scripts/openapi/generate_ui_reference_data.py`
      (26×) to the specific exception type(s) each UAC/UIC registry-extraction block actually expects (mirror the
      pattern already used for that file's one literal-colon occurrence, fixed 2026-08-09). Repo: unified-trading-pm.
- [ ] [BACKEND] P3. Narrow the remaining ~50 `except Exception as X:` occurrences across the other 29 files (full
      inventory: `rg -n "except Exception as" --type py --glob "!tests/**" scripts/`), same per-file review discipline
      as `pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md`'s P3 todo. Repo: unified-trading-pm.

## Progress Log

- **2026-08-09 (slot-24, backend_engineer)**: Filed after finding + fixing a 22nd broad-except occurrence in
  `ci_failure_watcher.py` that was invisible to the gate's literal-colon regex; corpus sweep found 77 more. Fixed the
  one found in-file; the rest tracked here per findings-triage (outside my primary task's scope, genuinely new per-file
  review work).
