---
doc_type: issue
title:
  check_reference_paths --only reports exit 0 for a file it never opened, and --quiet prints the violation count without
  the filename
summary: >-
  Two defects in the reference-path gate combined to cost seven failed `safe-doc-push` attempts on a single one-line
  violation, and to produce false evidence that anchored six wrong diagnoses. (1) `_run_only()` does `if not
  p.is_file(): continue` on every path passed to `--only`, so a path that does not resolve from the current working
  directory is silently skipped and the function then prints "0 violation(s)" and returns exit 0 — a clean bill of
  health for a file with violations, and a textbook proxy-vs-property failure where exit 0 means "nothing was checked",
  not "nothing is wrong". (2) `run_hygiene_sweep.sh` invokes the checker with `--quiet --only`, which suppresses the
  violation text but keeps the count, so a precommit failure says "1 violation(s) in staged files" and never names the
  offending reference. `find_moved_doc_referrers.sh` already documents defect (2) in its own header comment, so it has
  now cost time at least twice. The offending reference was found in one shot by checking out a throwaway worktree at
  origin/live-defi-rollout and running the checker WITHOUT --quiet.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, plan-hygiene, false-green, measurement-discipline, developer-experience]
related:
  [
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
context_scope:
  - scripts/plan-hygiene/check_reference_paths.py
  - scripts/plan-hygiene/run_hygiene_sweep.sh
  - scripts/plan-hygiene/find_moved_doc_referrers.sh
  - /plans/active/ao_satellite_ao_dispatch_batch23_2026_08_17.md
created: 2026-08-12
last_updated: 2026-08-22
archive_exempt: true
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found 2026-08-12 while pushing sections H/H.5 of the Elysium October delivery plan. Seven identical `safe-doc-push`
  failures, six wrong diagnoses, all anchored on a false negative produced by defect (1).
---

# `check_reference_paths.py` hides which reference is wrong, and passes files it never read

## Why this is worth fixing rather than remembering

The gate is correct about the corpus and wrong about the developer loop. It **detected** a genuine violation every time
— a bare `codex/...` reference missing its leading slash — and it never once said which reference or which line. Seven
push attempts, six wrong hypotheses (dangling-at-origin, prettier mangling, section-scoped links, worktree sync), and
the diagnosis only converged when the checker was run outside the gate with `--quiet` removed.

**The more serious of the two defects is the false negative**, because a wrong FAIL only wastes time whereas a wrong
PASS gets believed. The "same checker returns 0 violations locally" measurement that made the failure look like a
worktree artefact was itself the bug: run from the repo root the relative path resolves and the file is checked; run
from one directory up it does not, and `_run_only()` skips it and reports success.

## Defect 1 — `_run_only()` silently skips unresolvable paths, then reports exit 0

```python
for raw in paths:
    p = Path(raw)
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.is_file():
        continue          # <-- silently drops the file
    ...
n = len(format_violations) + len(existence_violations)
print(f"{'✅' if n == 0 else '❌'} check_reference_paths (--only): {n} violation(s) in staged files")
return 0 if n == 0 else 1
```

A path explicitly named on the command line that does not resolve is **not** the same condition as a file with no
violations, and the two must not share an exit code. `--only` is a caller asserting "check exactly these"; silently
checking none of them and returning success violates that contract.

**Fix:** a path passed to `--only` that does not resolve is an ERROR — print the path it tried (including the resolved
absolute form, so a cwd mistake is obvious) and exit non-zero. If some caller legitimately passes paths that may not
exist, that caller should filter them, or opt in explicitly via a `--skip-missing` flag; the default must not be silent.

**Test to add:** invoke `--only` with a path that does not exist and assert a non-zero exit. There is currently no test
that would catch this, which is why it survived.

## Defect 2 — `--quiet` suppresses the evidence and keeps the number

`run_hygiene_sweep.sh` calls the checker with `--quiet --only` for both staged plans and staged codex. `--quiet` gates
the per-violation `FORMAT` / `DANGLING` lines but not the summary, giving the least useful pairing available: the
developer learns a violation exists and nothing about where.

**Fix:** print offending references on FAILURE regardless of `--quiet`. Quiet should suppress noise on success, never
evidence on failure. This is a two-line change and it retires the workaround documented in
`find_moved_doc_referrers.sh`'s header, whose stated reason for existing is precisely that the sweep runs the checker
with `--quiet`.

## Sharp edge worth keeping either way

The checker scans **fenced code blocks**, so a shell example containing a literal repo-relative `codex/NN-name/....md`
path is a FORMAT violation even though it is a command rather than a reference. A leading slash would make the command
wrong, so the workaround is a glob that cannot match the pattern (`codex/14-*/...`). Whether that should be an exemption
is a separate judgement call — worth a deliberate decision rather than leaving each author to rediscover it.

## Todos

- [x] ✅ [SCRIPT] P1. **Make an unresolvable `--only` path a hard error** in `_run_only()` — extracted (conflict-checked,
      clear) to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` item 3. Track dispatch/completion there, not here.
- [x] ✅ [SCRIPT] P2. **Print offending references on failure even under `--quiet`** — extracted (conflict-checked,
      clear) to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` item 4. Track dispatch/completion there, not here.
- [x] ✅ [SCRIPT] P3. **Retire the `--quiet`-workaround rationale in `find_moved_doc_referrers.sh`'s header** —
      extracted (conflict-checked, clear) to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` item 5. Track
      dispatch/completion there, not here.
- [x] ✅ [SCRIPT] P3. Per D47 ruling (2026-08-21, autonomous-dispatch authority): add the exemption — a fenced-code-block
      exemption to `check_reference_paths.py`'s `BARE_CODEX_RE` scan, so a shell example containing a literal
      repo-relative `codex/NN-name/...md` path inside a fenced code block is not flagged as a FORMAT violation — this
      removes a recurring false-positive class without weakening enforcement. Record the ruling in
      [cross-reference-path-convention](/codex/11-project-management/cross-reference-path-convention.md). Repo:
      unified-trading-pm. Done when: the exemption ships with a regression test (a fenced-code-block bare-codex-path
      does NOT flag) and the convention doc states the ruling. — Implemented via `_fenced_code_spans()`/`_in_any_span()`
      in `check_reference_paths.py` (span-based skip of `BARE_CODEX_RE` matches inside fenced blocks); 2 regression
      tests added to `test_check_reference_paths.py` (inside-fence not flagged; outside-fence still flagged); D47
      ruling + implementation pointer recorded in cross-reference-path-convention.md's new "Fenced-code-block
      exemption" section. Verified: full pytest suite green (2157 passed) incl. the 2 new tests; ruff/basedpyright
      clean. `unified-trading-pm@<pending>` (see commit trailer).

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (2 entries).
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:63676f449612beab]: RECLASSIFY (per-todo split) — 3 well-specified deterministic script fixes (hard-error on unresolvable --only path; print offending refs under --quiet; retire the --quiet workaround rationale) are conflict-checked clear and extracted to `ao_satellite_ao_dispatch_batch23_2026_08_17.md` items 3-5. The 4th item (fenced-code-block BARE_CODEX_RE exemption decision) stays KEEP-NA, an open design-judgment call.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added `find_moved_doc_referrers.sh` (the doc's
  own P3 todo's fix target) and `ao_satellite_ao_dispatch_batch23_2026_08_17.md` (where the 3 extracted script fixes
  are now tracked for dispatch/completion, per this same audit pass's own retag above).

**2026-08-21 — ruling D47 (Fenced-code path exemption)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
AUTONOMOUS_AGENT_RULES rule 2): Add the exemption — removes a recurring false-positive class without weakening
enforcement. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

- **worker slot-16, 2026-08-22**: shipped the D47 fenced-code-block exemption (final open todo, flipped above). All 4
  todos are now done, which trips `check_archive_candidates`'s 0-open-todos gate. Setting `archive_exempt: true`
  rather than performing the full 6-step archival ritual inline: this doc is a live referrer target for at least 7
  in-flight docs (`elysium_october_delivery_and_code_disclosure_readiness_2026_08_11.md`,
  `ao_satellite_ao_dispatch_batch23_2026_08_17.md` + its `_finalize` companion,
  `issues_corpus_completion_dispatch_2026_08_21.md`, `issues_corpus_executable_queue_2026_08_21.md`,
  `plan_reconciler_findings_agent_operating_framework_master_2026_08_19.md`,
  `cross-reference-path-convention.md`), and the archival ritual's step 5 ("update every referrer's path
  corpus-wide") is genuine judgment work — deciding which references should repoint at the archived path vs. have
  their cited fact migrated into a codex SSOT — that does not belong inside an unrelated P3 script-fix task. Leaving
  this for `/archive-candidates-audit` or a dedicated follow-up to do properly.
