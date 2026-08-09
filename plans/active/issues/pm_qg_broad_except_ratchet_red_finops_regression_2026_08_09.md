---
doc_type: issue
title: >-
  unified-trading-pm quality-gates.sh "No broad except Exception" gate is RED on a pristine committed tree — 21
  pre-existing `except Exception:` occurrences across 12 scripts/ files, plus 1 new offender from a same-day commit
summary: >-
  `scripts/quality-gates-base/base-library.sh`'s codex-compliance "broad except Exception" check (STEP ~5.20-ish,
  `SOURCE_DIR="scripts"` for this repo) is a hard zero-tolerance gate (`CODEX_MAX_VIOLATIONS=0` for unified-trading-pm)
  that fails the instant ANY `except Exception:` exists anywhere under `scripts/` (excluding `tests/`) — not
  diff-scoped, not baseline-tolerant, unlike the shrinking-ratchet checks in `scripts/plan-hygiene/`. Confirmed on a
  fully clean, fully-committed `live-defi-rollout` HEAD (nothing staged/unstaged) that `bash scripts/quality-gates.sh`
  fails with `❌ Codex compliance FAILED: 1 violations (max allowed: 0)` purely from this check — meaning a genuine,
  full (non-`--skip-*`) Pass-1 quality-gates.sh run cannot currently pass for ANY commit to this repo, blocking every
  worker's ship path until fixed.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, quality-gates, codex-compliance, qg-red, broad-except, repo-blocker]
related:
  [
    /plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
author: slot-18 (backend_engineer)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered 2026-08-09 (slot-18, backend_engineer) while shipping an unrelated diff-base ratchet extension
  (plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md's P2 follow-up todo) — Pass-1
  `quality-gates.sh` failed on this unrelated check; verified pre-existing by stashing all local changes and re-running
  on a pristine committed HEAD, which failed identically.
---

# unified-trading-pm codex-compliance "broad except Exception" gate is RED — blocks every commit

## What was found

`scripts/quality-gates-base/base-library.sh` (~line 1005-1007) runs, unconditionally, on every `quality-gates.sh`
invocation for this repo (docs-only-changeset mode does NOT skip it — verified live):

```bash
BE=$(codex_rg "except Exception:" --type py --glob "!tests/**" "${_be_extra_globs[@]}" "$SOURCE_DIR/" 2>/dev/null || :)
[[ -n "$BE" ]] && { log_warn "broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md"; echo "$BE" | head -5; V=$(( V + 1 )); } || log_success "No broad except Exception"
```

`SOURCE_DIR="scripts"` for `unified-trading-pm` (`QUALITY_GATE_BYPASS_AUDIT.md` §1's own documented PM exception).
`CODEX_MAX_VIOLATIONS` is unset in `scripts/quality-gates.sh` for this repo → default `0`
(`_max_v=${CODEX_MAX_VIOLATIONS:-0}`). So `V>=1` (any hit at all, corpus-wide, not diff-scoped) hard-fails the whole
codex-compliance section, printing only the first 5 hits and NOT counting per occurrence — the check is boolean, not a
shrinking ratchet like the `scripts/plan-hygiene/*.py` checks in the sibling doc above.

**Verified pre-existing, not caused by any in-flight work**: `git stash`'d every local change and ran
`bash scripts/quality-gates.sh` on the pristine, fully-committed `live-defi-rollout` HEAD (`ce9b6e794` at verification
time) — failed identically: `❌ Codex compliance FAILED: 1 violations (max allowed: 0)`.

**Full violation inventory** (`rg "except Exception:" --type py --glob "!tests/**" scripts/`, run 2026-08-09): 22 raw
hits, 21 real (1 false-positive — `scripts/openapi/audit_dead_code.py:665` is a string literal inside a generated-code
template, not executable code) across 12 files:

| File                                                              | count                                                                    |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------ |
| `scripts/repo-management/pin_branch_protection_rulesets.py`       | 3                                                                        |
| `scripts/openapi/generate_unified_spec.py`                        | 3                                                                        |
| `scripts/repo-management/cron_liveness_watchdog.py`               | 2                                                                        |
| `scripts/repo-management/ci_failure_watcher.py`                   | 2                                                                        |
| `scripts/migration/verify_env_tiered_buckets_provisioned.py`      | 2                                                                        |
| `scripts/manifest/validate-import-deps.py`                        | 2                                                                        |
| `scripts/validation/check-integration-dep-coverage.py`            | 1                                                                        |
| `scripts/sports/migrate_sports_gcs_to_hive.py`                    | 1                                                                        |
| `scripts/quality_gates/qg_audit.py`                               | 1                                                                        |
| `scripts/quality_gates/check_emission_policy_paired_callsites.py` | 1                                                                        |
| `scripts/orchestrator/reap_stale_blockers.py`                     | 1                                                                        |
| `scripts/openapi/generate_ui_reference_data.py`                   | 1                                                                        |
| `scripts/cicd/promotion_lag_monitor.py`                           | 1 (has an inline comment: `# Firestore unavailable → best-effort write`) |
| `scripts/openapi/audit_dead_code.py`                              | 1 (FALSE POSITIVE — string literal, not code)                            |

**Trigger commit**: `unified-trading-pm@0f6087516`
(`docs(finops): three-year tapering GCP proposal + DART-led restructure + finops tooling`, landed
2026-08-09T15:57:35+01:00) added `scripts/finops/measure_agent_fleet_tokens.py` with 2 of its own `except Exception:` —
the most RECENT addition to an already-latent problem, not the sole cause (the other 12 files/21 occurrences predate it
and were apparently never caught by a genuine full, uncached Pass-1 run since whenever each landed). **Already fixed as
a drive-by** (this session, unrelated primary task): the 2 occurrences in `measure_agent_fleet_tokens.py` narrowed to
`except json.JSONDecodeError:` / `except (ValueError, AttributeError):` — the specific exceptions the surrounding code
actually expects. This does NOT clear the gate (21 other real occurrences remain); shipped alongside this issue doc
rather than held back, since it's a genuine, harmless, already-verified improvement.

## Why it matters

- **Every worker's Pass-1 `quality-gates.sh` for this repo currently fails** the instant it reaches codex-compliance
  (assuming a real, non-`--skip-codex` run) — this is not a corner case, it is the MANDATORY ship gate (RULES.md § 2 /
  worker.md "a2) SHIP via the v2 canonical quality-gate flow (MANDATORY — two passes)"). Confirmed independently by this
  session (pristine-HEAD repro).
- Workers who have NOT hit this yet are likely relying on `QG_FAST`/`--skip-codex`/partial runs, or simply haven't
  landed a commit to this repo since `0f6087516` yet — this will surface for every subsequent worker the moment they run
  a genuine full gate.
- This is a DIFFERENT failure mode from the
  `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_ velocity_2026_08_09.md` doc's own subject (that doc is about
  `scripts/plan-hygiene/*.py`'s shrinking-ratchet checks racing concurrent commits) — this is a hard zero-tolerance gate
  with NO ratchet/diff-scoping mechanism at all, corpus-wide, unconditional.

## Recommended decision

Two independent tracks, either or both:

1. **Fix the 21 real occurrences** — narrow each `except Exception:` to the specific exception(s) the surrounding code
   actually handles (same pattern as this session's `measure_agent_fleet_ tokens.py` fix). Needs per-file review (what
   does THIS try-block actually expect to fail?), not a blind `except (Exception,):` reformat — genuine backend_engineer
   craft work, ~12 files.
2. **Fix the false positive** — `scripts/openapi/audit_dead_code.py`'s hit is a string literal; the `codex_rg` check has
   no way to distinguish source code from a string containing similar text. Either accept it as permanent noise (it
   never blocks anything ELSE since the OTHER 21 already trip the gate first) or teach the check to skip string-literal
   matches — lower priority, only matters once the 21 real ones are fixed.

Left to the operator/main for `[BACKEND]` dispatch scoping (bounded, deterministic-outcome per-file fixes — AO-eligible
per `task_template.md`'s dispatch-scope bar) rather than fixed by this session, which is mid an unrelated primary task.

## Todos

- [ ] [BACKEND] P1. Narrow all 21 real `except Exception:` occurrences (table above, excludes the `audit_dead_code.py`
      string-literal false positive) to the specific exception type(s) each surrounding try-block actually expects —
      same approach as this doc's own drive-by fix to `scripts/finops/measure_agent_fleet_tokens.py` (already shipped).
      Re-run `rg "except Exception:" --type py --glob "!tests/**" scripts/` after to confirm only the 1 known false
      positive remains, then confirm `bash scripts/quality-gates.sh` passes the "No broad except Exception" check on a
      pristine tree. Repo: unified-trading-pm.
- [ ] [BACKEND] P3. Optional: teach the `codex_rg "except Exception:"` check
      (`scripts/quality-gates-base/base-library.sh` ~line 1005) to skip matches inside string literals (e.g. a
      lightweight AST-based scan instead of a raw regex) so a generated-code template string (like
      `audit_dead_code.py`'s) can never trip it — only worth doing once the P1 above is clear, since right now the false
      positive is masked by 21 real hits anyway. Repo: unified-trading-pm (`scripts/quality-gates-base/`).
- [ ] [BACKEND] P1. **NEW FACET, 2026-08-09 (slot 18): the check produced a FALSE-NEGATIVE green once, on a tree that
      demonstrably still had all 21 violations.** A `bash scripts/quality-gates.sh` run on commit `204bb3c0bd89` (the
      exact SHA `.qg_last_passed_sha` recorded as fully green) printed `✅ No broad except Exception` and exited 0 — but
      `git show 204bb3c0bd89:<any of the 12 flagged files>` confirms every one of the 21 real occurrences was PRESENT in
      that exact tree (verified directly, table-by-table, all 13 non-false-positive files unchanged from this doc's
      original inventory). Immediately re-running the identical
      `rg "except Exception:" --type py --glob     "!tests/**" scripts/` command by hand on the SAME tree finds all 21
      hits without issue — so this isn't a corpus change between the two checks, it's the SAME content producing
      different verdicts from (nominally) the same command. No caching mechanism explains it (only `bandit`/`pip-audit`
      have `qg_cache_hit`/`qg_cache_store` calls; the broad-except check and the whole codex-compliance section have
      none; the green-content-sentinel fast path only skips TESTS/TYPECHECK, not codex-compliance, per its own guard
      flags). Root cause NOT identified this session — flagging as its own P1 since a corpus-wide zero-tolerance CI gate
      that can silently false-negative is a more serious problem than the 21 violations themselves (a gate nobody can
      trust to actually catch a NEW broad except is worse than no gate — it gives false confidence). Whoever picks up
      the P1 fix-the-21 todo above should first try to reproduce this (rerun `quality-gates.sh` 2-3x on an unchanged
      tree, compare outputs) before assuming the check is reliable once the corpus is clean. Repo: unified-trading-pm
      (`scripts/quality-gates-base/base-library.sh`).

## Progress Log

- **2026-08-09 (slot-18, backend_engineer)**: Filed after Pass-1 `quality-gates.sh` failed on an unrelated code change
  (`plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md`'s diff-base extension). Verified
  pre-existing via a stash-and-rerun on pristine HEAD (`ce9b6e794`) — identical failure. Fixed the 2 occurrences in the
  triggering commit's own file (`measure_agent_fleet_tokens.py`) as a harmless drive-by; the other 21 across 12 files
  are out-of-scope for this session's primary task (genuine per-file review work, not a quick fix) — filed as its own
  `[BACKEND]` todo per findings-triage. Declared repo-blocker `qg_red` for `unified-trading-pm` so this session's own
  unrelated shippable work doesn't spin waiting/retrying on a wall it can't clear alone.
- **2026-08-09 (slot-18, resolution + new finding)**: `RB-a1b3b316` resolved green ~1h50m after declaring (repo-health
  watcher reporter path). Re-verified against the exact resolved-green SHA (`204bb3c0bd89` — `.qg_last_passed_sha`'s
  recorded value) before trusting the signal, per RULES.md § 4b's own caveat: found ALL 21 violations still present in
  that exact tree's content (`git show <sha>:<file>` for every one of the 13 non-false-positive files listed above,
  unchanged from this doc's original inventory). Yet `bash scripts/quality-gates.sh` on that same SHA printed
  `✅ No broad except Exception` and exited 0. Immediately re-running the raw `rg` command by hand on identical content
  finds all 21 hits. This is a NEW, more serious finding than the original 21-violation debt — added as its own P1 todo
  above (a gate that can silently false-negative undermines trust in the whole zero-tolerance ratchet more than the debt
  itself does). Did not block this session's own ship: my 3 local commits (which don't add or remove any broad-except
  occurrence — my own drive-by fix to `measure_agent_fleet_tokens.py` became a no-op once rebased onto `204bb3c0bd89`,
  which already carried an equivalent independent fix) shipped clean via `quickmerge --agent`:
  `unified-trading-pm@b12d43618` + `@3fffb345b`, both verified `git merge-base --is-ancestor` of
  `origin/live-defi-rollout`.
