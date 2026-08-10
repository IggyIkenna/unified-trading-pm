---
doc_type: plan
title: quality-gates.sh / quickmerge.sh timing baseline (PM repo) — single-host vs planning-vm
summary:
  Measure wall-clock + per-phase timing of `quality-gates.sh` (across its mode/scope flags) and `quickmerge.sh` on
  unified-trading-pm — first a single-agent baseline on this host, then the same measurements on the planning-vm where
  ~15 concurrent agents are suspected to be causing contention/slowdown. This is the diagnostic baseline the improvement
  work will compare against.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, quickmerge, timing, performance, ci-cd, orchestrator, benchmarking]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/06-coding-standards/quality-gates.md]
created: "2026-07-31"
last_updated: 2026-07-31
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    scripts/quality-gates.sh,
    scripts/quickmerge.sh,
    scripts/quality_gates/profile_qg_resources.py,
    scripts/quality_gates/check_pm_script_path_refs.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# quality-gates.sh / quickmerge.sh timing baseline (PM repo)

## Why

Suspected slowdown running `quality-gates.sh` / `quickmerge.sh` on the planning-vm, where ~15 agents can be working
concurrently (CPU/IO contention, shared-host QG concurrency cap in CLAUDE.md: `max(2, floor(cores/4))`). Before
optimizing anything we need real numbers: (1) a clean single-agent baseline on this host (Phase 1), (2) the same
measurements captured on planning-vm under real concurrent load (Phase 2), so any improvement work has a documented
before/after.

All test changes used to trigger these runs are transient (a comment appended to
`/plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md` + a scratch
`/plans/audit/results/qg_timing_test_2026_07_31.yaml`) — reverted once measurement is done, never shipped as real
content changes.

## Progress Log

- **2026-07-31**: Plan created (human/local track per operator — this host is the baseline, planning-vm is the actual
  target once baseline numbers exist). Phase 1 todos below measure this host.
- **2026-07-31 — real bug found + fixed, not just contention**: the first full-default `quality-gates.sh` timing run did
  not finish in the expected seconds-to-a-few-minutes window; it ran 52+ minutes at 0% CPU before being killed manually.
  Root cause: `scripts/quality_gates/check_workflow_yaml_valid.py`'s workflow-lint phase ran
  `subprocess.run(["actionlint", *workflows], capture_output=True, text=True)` with **no timeout**. `actionlint` v1.7.12
  (built from source, go1.25.1) **deterministically deadlocks** (confirmed via bisection across the 59
  `.github/workflows/*.yml` files — not intermittent slowness, a reproducible `futex_do_wait` stall at 0% CPU with no
  child processes) linting `.github/workflows/ldr-to-main-promote-fleet.yml`'s ~1041-line embedded bash (functions,
  `process_repo &`/`wait` backgrounding, several `python3 - <<'PYEOF'` heredocs) through its shellcheck integration.
  Isolated the exact cause: `actionlint -shellcheck=` (integration disabled) → 19ms clean over all 59 files; the same
  script's `run:` block extracted to a standalone `.sh` and fed to `shellcheck` **directly** (bypassing actionlint) →
  0.4s, 3 minor warnings, no hang — so `shellcheck` itself is fine, the deadlock is in actionlint's own subprocess
  stdin/stdout pipe handling of this one large script (classic Go `os/exec` pipe-buffer-deadlock class). This means the
  "PM repo quality-gates is slow" symptom that motivated Phase 2 (planning-vm, 15 concurrent agents) can reproduce on an
  **idle single-agent host** with zero contention — concurrency may still make things worse, but it is not the root
  cause of an unbounded hang. **Fixed**: added `timeout=20` to that `subprocess.run` call, catching
  `subprocess.TimeoutExpired` and treating it as informational/non-blocking, same as any other actionlint finding
  (matches the check's existing documented philosophy that actionlint output never fails the gate — only the YAML-parse
  check does). Verified: `python3 scripts/quality_gates/check_workflow_yaml_valid.py` now returns exit 0 in ~20.5s
  instead of hanging indefinitely.
- **2026-07-31 — first fix was a coarse timeout, tightened to a real per-file fix (operator pushback: "if it times out
  every run, how is that a fix?").** The single-batch 20s timeout was correct-but-lazy: it fires deterministically on
  EVERY run (the stall is 100% reproducible on this one file) and, worse, discarded actionlint's real informational
  output for all 59 files — not just the one that hangs. Replaced with `_run_actionlint_per_file()`: runs actionlint one
  file at a time (5s timeout each) so the stall is isolated to `ldr-to-main-promote-fleet.yml` alone; the other 58 files
  lint at full fidelity with real findings surfaced. The stalled file is retried with `-shellcheck=` (confirmed instant,
  no hang) so it still contributes its non-shellcheck findings instead of being skipped outright, and the printed
  warning names the exact file that stalled instead of a generic timeout message. Verified:
  `python3 scripts/quality_gates/check_workflow_yaml_valid.py` now completes in ~7.2s, exit 0, "59 workflows parse +
  actionlint clean" — real signal recovered, not just a bigger timeout.
- **2026-07-31 — actual root cause fixed (operator: "fix the root cause rather than excluding it").** The per-file
  isolation above was still a workaround, not a fix — it made the checker robust to a hang, but
  `ldr-to-main-promote-fleet.yml` itself was still the one file actionlint could never lint cleanly. Bisected the real
  trigger by feeding actionlint synthetic workflows containing increasing prefix-length slices of the exact script
  content: a 985-line prefix lints clean in <1s; a 990-line prefix (5 more lines, an ordinary `echo`) hangs — so the
  trigger is **script size crossing a threshold inside one `run:` step**, not any specific bash construct. Ruled out
  version-pinning as the fix: downloaded the CI-pinned `actionlint v1.7.4` (local had v1.7.12) and the CI-pinned
  `shellcheck v0.10.0` (local had v0.11.0) and tested all combinations directly against the real file — every
  combination hangs identically. Confirmed via `ps`/`wchan` inspection this is a genuine blocked wait
  (`ep_poll`/`futex_do_wait`, 0% CPU, no live child process — consistent with a Go `os/exec` pipe-descriptor-leak
  deadlock), not slow computation that would eventually finish. **Real fix**: extracted the ~1041-line embedded script
  verbatim (no logic changes) out of the YAML `run: |` block into a checked-in
  `scripts/cicd/ldr_to_main_fleet_promote.sh` (matches the repo's existing `scripts/cicd/*.sh` convention for CI
  automation), and reduced the workflow step to `run: bash scripts/cicd/ldr_to_main_fleet_promote.sh`. Verified:
  `actionlint .github/workflows/ldr-to-main-promote-fleet.yml` alone now runs in **8ms** (was: indefinite hang); the
  full 59-file batch in **0.42s** with zero findings; `check_workflow_yaml_valid.py`'s per-file fallback path (kept as a
  general defensive measure for any _future_ oversized embedded script, not relied on here) never triggers anymore — no
  stall warning printed. `shellcheck` directly on the extracted file: same 3 pre-existing minor warnings as before
  extraction (SC2034/SC2016×2/SC2097+SC2098), nothing new introduced. Full-default `quality-gates.sh` dropped from 61.3s
  (per-file-fallback state) to **50.8s** (root-cause-fixed state) — see results table below.
- **2026-07-31 — operator flagged an existing docs-only fast path worth using.**
  `scripts/quality-gates-base/base- service.sh` (+ `base-library.sh`, `base-ui.sh`) already has a `_QG_DOCS_ONLY`
  auto-detection: if every changed file in the diff is a doc extension, it sets `_QG_DOCS_ONLY=true`, which appears to
  scope/skip heavier Python lint/test/typecheck phases while still running codex/frontmatter checks. This is NOT a
  manual `--docs` flag — it's automatic based on the changed-file-set. Not yet measured how it's triggered (diff base:
  staged files? merge-base? `HEAD~1`?) or exactly what it skips vs. `--fast`/`--quick` — added as a Phase-1 todo below
  since a plan/doc-only change (like this session's own test edits) is exactly the scenario it should speed up.
- **2026-07-31 — session interrupted mid-run; recovered cleanly.** A background `--skip-tests` timing run (result:
  **64.2s, exit 0, full green through version-alignment**) completed fine, but a separate attempt to isolate a docs-only
  test got killed mid-flight by an external Claude Code session restart (SIGTERM right after the ENVIRONMENT phase).
  This left an orphaned `README.md` test-marker edit and an un-popped `git stash` (holding the real fixes). Recovered
  fully: reverted the orphaned marker, `git stash pop`'d the real fixes back, verified nothing lost. Lesson: prefer
  bundling an edit+run+revert as ONE atomic backgrounded command over separate sequential steps, though an external
  session interruption can still land between any two commands regardless.
- **2026-07-31 — two failed attempts at isolating the docs-only test; a real methodology bug, not bad luck.** Attempt A:
  ran the test in a fresh `git worktree` outside `.tabs/2/` to avoid touching the main tree at all — failed differently:
  `quality-gates.sh`/`base-service.sh` **hardcode sibling-repo paths assuming the literal directory name
  `unified-trading-pm`** under a workspace root one level up (e.g. constructs
  `$WORKSPACE_ROOT/unified-trading-pm/scripts/quality-gates-base/base-service.sh` even when `$REPO_ROOT` is already the
  correct self-path) — a worktree living anywhere else, under any other name, breaks ~10 unrelated checks
  (plan-discipline, doc-retrieval-parity, `.code-workspace` drift, capability-manifest lookups, etc.) that assume the
  full multi-repo `.tabs/2/`-style layout. Not fixable without literally colliding with the real checkout's path, so
  abandoned. Attempt B: `git stash push -u` the real fixes inside the main tree to isolate a doc-only diff — this **also
  reverted `check_workflow_yaml_valid.py` and `ldr-to-main-promote-fleet.yml` back to their ORIGINAL unfixed state**, so
  the "docs-only" run hit the exact same actionlint deadlock this whole plan exists to fix (2-minute foreground timeout,
  stuck after ENVIRONMENT, same signature as the original bug) — a false-positive reproduction caused by testing against
  a known-broken baseline, not a docs-only-path defect. Recovered cleanly (reverted the test marker, `git stash pop`).
  **Correct sequencing**: ship the real fixes via `quickmerge` FIRST (already operator- authorized), so the working tree
  is clean-and-fixed at rest; a docs-only isolation test can then use a trivial stash/worktree-free single-file edit
  without ever reverting the fixes it depends on. Re-ordered the todos below accordingly — quickmerge now runs before
  the docs-only re-attempt.
- **2026-07-31 — real `quickmerge.sh` run FAILED at Stage 3; root cause is a known, already-tracked, unrelated issue —
  not something to fix here.** Ran `bash scripts/quickmerge.sh "..." --agent --files '<the 4 real fix files>'` for real
  (operator-authorized). It progressed through Stage 0 (cascade/not-behind-pull/semver-advisory/manifest- staleness) →
  Stage 1 (dependency validation) → Stage 1.5 (dependency alignment + DAG regen) → Stage 2 (pre-flight audit) → into
  Stage 3 (local quality gates), where a first fast sentinel-verification pass rejected (`ENVIRONMENT`/`DEPLOYMENT_ENV`
  mismatch vs. the cached sentinel), forcing a full re-gate — which hit the exact same 6 pre-existing `strategy-service`
  `iter_route_contexts` test failures seen in every prior run, and quickmerge correctly hard-failed rather than ship on
  a red re-gate. **Total: 1m24.824s (real) before the hard failure**; Stage 4 (act simulation) and Stage 5 (PR creation)
  never ran, so no number exists for those yet. Grepped the corpus before assuming this was new (pre-task plan/issue
  conflict check): it's already tracked — `/plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md`
  (`status: open`, P2, `assigned_vm: planning`, `locked_by: live-defi-rollout`) — a CVE-remediation
  dependency-version-cap bump broke `fastapi.routing.iter_route_contexts` fleet-wide across several repos
  (`market-tick-data-service` hit the identical error live per that doc's 2026-07-28 entry); unified-trading-pm's
  capability-schema tests probe `strategy-service/.venv` directly so they inherit the break. **Not this plan's issue to
  fix** — already owned, already in-flight elsewhere. **Practical consequence**: `quickmerge.sh` cannot ship ANYTHING on
  unified-trading-pm right now, not just this plan's fix — there is no skip-tests escape hatch for quickmerge by design
  (`--skip-tests`/`--skip-typecheck`/`--skip-codex` are hard-disabled there, WS-L #1014). The real fixes stay as local
  uncommitted changes for now (safe — nothing lost) until that CVE issue clears; re-attempt quickmerge then to get the
  Stage 4/5 numbers and a real ship.
- **2026-07-31 — docs-only retest deferred, not just quickmerge.** Since quickmerge didn't land, the 3 real fix files
  (`.py`/`.yml`/`.sh`, all non-doc extensions) are STILL uncommitted diffs in the working tree — and `_QG_DOCS_ONLY`
  requires the ENTIRE changeset to be doc-extension files. Stashing them away again (as before) would just reintroduce
  the original actionlint hang, same as the earlier failed attempt — there is no way to isolate a pure-doc diff without
  either the real fixes being committed (blocked on the same CVE issue) or a throwaway local-only commit (rejected as
  unnecessary risk for one benchmark data point). Deferred alongside the quickmerge todo; both unblock together.
- **2026-07-31 — the CVE blocker was actually a stale local venv, not an unresolved fleet issue; fixed + shipped.**
  Traced it fully: `strategy-service/pyproject.toml` + `uv.lock` on THIS slot already required `fastapi==0.140.7` (the
  fix shipped fleet-wide 2026-07-28, per `cve_affected_pinned_deps_remediation_2026_06_18.md`), but
  `strategy-service/.venv` on slot 2 had `fastapi==0.135.1` actually installed — never `uv sync`'d since. Ran `uv sync`
  in `strategy-service`; re-ran the 2 previously-failing test files directly: **13/13 pass**, all 6 original failures
  gone. Documented this as a general, self-service troubleshooting entry (operator-directed) in
  `/codex/05-infrastructure/per-tab-worktrees.md` § Troubleshooting + a 1-line `CLAUDE.md` pointer (fit exactly within
  the 40,960-byte hard cap — was 40,900B, addition measured to 58B, landed at 40,958B), so any agent hitting this class
  of cross-repo `ImportError` fixes it themselves instead of escalating. **Shipped in two commits per operator
  direction** (doc first, standalone; then the real fixes together in one commit — not the same commit as the doc, since
  the doc had already landed by the time that request came in):
  - `unified-trading-pm@32e3e494d` — docs-only (`CLAUDE.md` + `per-tab-worktrees.md`), quickmerge real wall-clock
    **2m53.977s (173.977s)**, exit 0, landed directly on `live-defi-rollout` (LDR trunk — PM's quickmerge model lands
    there directly, no PR step, per the 2026-07-27 churn fix; drains to `main` via `ldr-to-main-promote.yml` on a
    ~15-30min SLA).
  - `unified-trading-pm@468e9413e` — the real actionlint/workflow-extraction fix (all 4 files:
    `check_workflow_yaml_valid.py`, `ldr-to-main-promote-fleet.yml`, `scripts/cicd/ldr_to_main_fleet_promote.sh`, this
    plan doc), quickmerge real wall-clock **2m30.436s (150.436s)**, exit 0, same LDR-direct landing. **This is the first
    quickmerge run in this whole session to reach every stage and actually ship** — Stage 0→1→1.5→2→3→ land, all green,
    no bypass. Working tree fully clean afterward (`git status` empty). Both confirmed present at the tip of
    `origin/live-defi-rollout` via `git fetch` + `git log`. Todo 3 below upgraded from partial/blocked to fully done
    with a real number.

## Phase 1 — this host baseline

**Results table (this host, single agent, idle otherwise):**

| Run                                                     | Wall-clock (`real`)                                    | Notes                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full default, actionlint hanging (pre-fix)              | never finished (killed at 52+ min)                     | root cause: no `subprocess` timeout on actionlint                                                                                                                                                                                                                                                                                                                             |
| Full default, coarse 20s-timeout fix                    | ~69.9s (real 1m9.941s)                                 | still hit the timeout every run; exits 1 at TESTS (6 pre-existing failures, unrelated — see below)                                                                                                                                                                                                                                                                            |
| Full default, per-file actionlint fix, pre-extraction   | 61.3s (real 1m1.263s)                                  | exits 1 at TESTS phase (same 6 unrelated failures)                                                                                                                                                                                                                                                                                                                            |
| Full default, **root-cause fix (script extracted)**     | **50.8s (real 0m50.794s)**                             | exits 1 at TESTS phase (same 6 unrelated failures) — current best full-default number                                                                                                                                                                                                                                                                                         |
| `check_workflow_yaml_valid.py` alone, root-cause fixed  | ~2.0s (59 per-file actionlint calls, no stalls)        | was: indefinite hang → 20.5s (coarse fix) → 7.2s (per-file fix, 1 stall+retry) → now no stall at all                                                                                                                                                                                                                                                                          |
| `--skip-tests` (env→lint→typecheck→codex→version-align) | **64.2s (real 1m4.207s), exit 0**                      | full green — first run to reach every phase; base-image digest drift WARN only (non-blocking, pre-existing)                                                                                                                                                                                                                                                                   |
| `quickmerge.sh`, CVE-blocked attempt (partial)          | 84.8s (real 1m24.824s) through Stage 3, then hard FAIL | Stage 0→1→1.5→2 all passed; Stage 3 re-gate hit the pre-existing (stale-venv) test failures — Stage 4/5 unmeasured                                                                                                                                                                                                                                                            |
| `quickmerge.sh`, **doc-only push (real, complete)**     | **174.0s (real 2m53.977s), exit 0**                    | `CLAUDE.md` + `per-tab-worktrees.md` only — full pipeline, landed on LDR trunk — `unified-trading-pm@32e3e494d`                                                                                                                                                                                                                                                               |
| `quickmerge.sh`, **real fix push (real, complete)**     | **150.4s (real 2m30.436s), exit 0**                    | all 4 real-fix files, one commit — full pipeline, landed on LDR trunk — `unified-trading-pm@468e9413e` — **first fully-green, no-bypass, complete quickmerge run this session**                                                                                                                                                                                               |
| `--quick`                                               | **30.7s (real 0m30.694s), exit 1**                     | skips version-alignment/merge-sentinel + runs a lighter test subset (1555 vs 1571 tests) — same 6 pre-existing failures                                                                                                                                                                                                                                                       |
| `--fast`                                                | 49.0s (real 0m48.982s), exit 1                         | change-scoped codex-grep tier — does NOT skip tests; hit the same 6 pre-existing failures, 1571 tests still ran                                                                                                                                                                                                                                                               |
| `--lint`                                                | 96.5s (real 1m36.464s), exit 0                         | lint-only (tests genuinely skipped, no FAILED lines) — but slower than `--skip-tests`'s 64.2s despite doing less; a slot-1 `quality-gates.sh` process was independently running concurrently on this host during this specific run (confirmed via `ps`, different `.tabs/1` checkout) — likely CPU-contended, not representative of an idle-host number; worth a clean re-run |
| `--test`                                                | 49.1s (real 0m49.118s), exit 1                         | test-only (skips lint) — same 6 pre-existing failures, full 1571-test count                                                                                                                                                                                                                                                                                                   |
| `--skip-lint`                                           | 52.5s (real 0m52.537s), exit 1                         | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-typecheck`                                      | 49.2s (real 0m49.220s), exit 1                         | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-codex`                                          | 48.9s (real 0m48.931s), exit 1                         | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-version-alignment`                              | 46.7s (real 0m46.681s), exit 1                         | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |

**Caveat on every full-default number above**: `quality-gates.sh` stops at the first red phase. All runs so far exit 1
at TESTS (env → lint → tests reached; typecheck/codex-compliance/version-alignment never reached) due to 6 pre-existing,
unrelated test failures rooted in one cross-repo import error —
`cannot import name 'iter_route_contexts' from 'fastapi.routing'` in `strategy-service/.venv` — reproduces identically
in both the root-level and slot-2 checkouts, so it's an environment/dependency issue, not something this session's edits
caused. `--skip-tests` is needed to time the remaining phases; see todos below.

**Important nuance on `--skip-lint`/`--skip-typecheck`/`--skip-codex`/`--skip-version-alignment`/`--test`'s numbers**:
phase order is ENV → LINT → TESTS → TYPECHECK → CODEX-COMPLIANCE → VERSION-ALIGNMENT (confirmed by `--skip-tests`
reaching every later phase). Since TESTS runs BEFORE typecheck/codex/version-alignment and is unconditionally red right
now, none of these 4 skip-flags actually get far enough to skip the phase they name — they all just measure "time to hit
the already-broken TESTS phase," landing within the same ~47-53s band regardless of which later phase is nominally
skipped. **Not a real per-phase time-saved number** — to measure that honestly needs `--skip-tests --skip-<X>` vs. plain
`--skip-tests`, deltaed, once the CVE blocker clears (not run this session — flagged as a follow-up, not launched, to
avoid scope creep on an already-long session).

### Results table 2 — clean tree, all fixes shipped, genuinely all-green (2026-07-31, post `unified-trading-pm@468e9413e`)

Everything above predates the `strategy-service` venv fix — every run that touched TESTS hit the same 6 pre-existing
failures and exited 1, so those numbers measure "time to the first red phase," not a genuine full-pipeline pass. Once
the real fixes shipped (see Progress Log), re-ran the full flag suite in one batch on a fully clean, fully-shipped tree.
**Every single run below is `exit 0` — no bypass, no pre-existing failure, real full-pipeline numbers:**

| Run                        | Wall-clock (`real`)   | Exit | Notes                                                                                                                                                                                                                                                              |
| -------------------------- | --------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Full default (no flags)    | **59.6s (0m59.556s)** | 0    | env→lint→tests→typecheck→codex→version-align, all green — the true apples-to-apples baseline number                                                                                                                                                                |
| Docs-only auto-path        | **56.3s (0m56.315s)** | 0    | `_QG_DOCS_ONLY` fired: "DOCS-ONLY changeset (2 file(s)...) → skipping TESTS + TYPECHECK + codex code-body"; lint/format + doc-validators still ran. Not much faster than full default here — lint+doc-validators dominate this repo's runtime, not tests/typecheck |
| `--quick`                  | 77.5s (1m17.508s)     | 0    | skips version-alignment/merge-sentinel; lighter test subset — slower than full default this run, likely shared-host variance (other slots' concurrent QG activity all session)                                                                                     |
| `--fast`                   | 100.9s (1m40.909s)    | 0    | change-scoped codex tier — does NOT skip tests, runs the full test suite; slowest of the bunch                                                                                                                                                                     |
| `--lint`                   | **56.6s (0m56.596s)** | 0    | lint-only, tests genuinely skipped — matches docs-only's ~56s, confirms lint+doc-validators (not tests) are this repo's real floor                                                                                                                                 |
| `--test`                   | 99.3s (1m39.295s)     | 0    | test-only, skips lint — full test suite runs                                                                                                                                                                                                                       |
| `--skip-lint`              | 101.1s (1m41.057s)    | 0    |                                                                                                                                                                                                                                                                    |
| `--skip-typecheck`         | 99.0s (1m39.017s)     | 0    |                                                                                                                                                                                                                                                                    |
| `--skip-codex`             | 105.8s (1m45.762s)    | 0    |                                                                                                                                                                                                                                                                    |
| `--skip-version-alignment` | **53.1s (0m53.136s)** | 0    | fastest of the 8 flags — version-alignment is genuinely one of the heavier phases to skip                                                                                                                                                                          |

**Reading these honestly**: variance across nominally-similar runs (e.g. `--quick` at 77.5s vs. full-default's 59.6s,
which should never be slower) is almost certainly shared-host noise — other slots ran their own quality-gates.sh
concurrently throughout this session (confirmed via `ps` more than once). These are single-sample numbers on a shared,
busy host, not a controlled benchmark — good enough to see the shape (tests dominate; lint+codex-compliance floor is
~55-60s; version-alignment is the single most expensive individually-skippable phase), not precise enough for a
scientific per-phase delta. A clean re-run on an idle host (or 3+ samples averaged) would tighten this if more precision
is needed later.

- [x] 1. ✅ [INFRA] P1. Time a full default `bash scripts/quality-gates.sh` run (no flags → implicit `--no-fix`) on
      unified-trading-pm; record wall-clock total. Done: see results table above — 50.8s post-root-cause-fix (exits 1 at
      TESTS due to 6 pre-existing unrelated failures; env/lint/tests phases only). — unified-trading-pm@(uncommitted,
      slot-2 working tree)
- [x] 2. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --skip-tests` to get past the pre-existing unrelated test
      failures and record typecheck / codex-compliance / version-alignment phase timing. Done: 64.2s, exit 0, full green
      — see results table above.
- [x] 3. ✅ [INFRA] P1. Time `bash scripts/quickmerge.sh "<real fix message>" --agent --files '<the real fix files>'`.
      Done for real: the CVE-looking blocker was a stale `strategy-service/.venv` on this slot (fixed via `uv sync`, see
      Progress Log) — not a genuine open fleet issue. Ran two real quickmerges: docs-only
      (`unified-trading-pm@32e3e494d`, 174.0s, exit 0) then the real fix files (`unified-trading-pm@468e9413e`, 150.4s,
      exit 0) — both landed on `live-defi-rollout`, full pipeline, no bypass. Working tree fully clean after.
- [x] 4. ✅ [INFRA] P1. Investigate + measure the `_QG_DOCS_ONLY` auto-detection in
      `scripts/quality-gates-base/base-service.sh`/`base-library.sh`/`base-ui.sh` (operator-flagged 2026-07-31;
      code-cited: triggers when `git diff HEAD` + `git diff --cached` + untracked files are ALL
      `.md/.mdc/.rst/.txt/.svg/.png/.jpe?g/.gif/.ico` — notably **not** `.yaml`/`.yml` — and skips
      `RUN_TESTS`/`SKIP_TYPECHECK`/codex-code-body while lint/format + doc-validators still run; server v2 always runs
      the full gate since a committed PR has no working-tree diff). Done: ran it clean on the now-fixed tree —
      "DOCS-ONLY changeset (2 file(s), all documentation) → skipping TESTS + TYPECHECK + codex code-body" fired
      correctly, **56.3s, exit 0** — see Results table 2 above.
- [x] 5. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --quick`. Done twice: 30.7s/exit 1 pre-fix (Results table
      1), **77.5s/exit 0** clean (Results table 2).
- [x] 6. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --fast`. Done twice: 49.0s/exit 1 pre-fix, **100.9s/exit 0**
      clean — does NOT skip tests, runs the full suite, slowest of the 8 flags on the clean tree.
- [x] 7. ✅ [INFRA] P1. Time each single-phase scope flag separately: `--lint`, `--test`, `--skip-lint`,
      `--skip-typecheck`, `--skip-codex`, `--skip-version-alignment`. Done twice: pre-fix numbers in Results table 1
      (caveat: 4 of 6 never reached the phase they nominally skip, TESTS failed first) superseded by real, all-`exit 0`
      numbers in Results table 2 — every flag genuinely ran to completion this time.
- [x] 8. ✅ [DOC] P2. Revert the transient test-trigger edits. Done: `git checkout --` the HTML-comment marker in
      `plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md`; moved the scratch
      `plans/audit/results/qg_timing_test_2026_07_31.yaml` out of the repo; the second-round docs-only test's own
      `README.md` marker also auto-reverted cleanly. `git status` is clean except for this plan doc's own edits.

**Phase 1 status: COMPLETE.** Every todo done with real, all-green numbers — the CVE-looking blocker turned out to be a
stale `strategy-service/.venv` on this slot, fixed via `uv sync`, and both the doc fix (`unified-trading-pm@32e3e494d`)
and the real actionlint/workflow-extraction fix (`unified-trading-pm@468e9413e`) are shipped and live on
`origin/live-defi-rollout`. Two results tables exist by design: table 1 (pre-fix, tests failing) and table 2 (post-fix,
genuinely all-green) — keep both, table 2 supersedes table 1 for "how fast is quality-gates really," table 1 stays as
the record of what the actionlint-hang bug cost before it was fixed. Remaining: Phase 2 (planning-vm) needs an operator
decision on how to reach that VM interactively.

### Results table 2 rigor follow-up (2026-07-31, post-Phase-1-complete) — operator pushback + the real root cause

Operator pushback on Results table 2: on a 12-core/24-thread 4.7GHz host with 96GB RAM + NVMe, with only ~3 local agents
(and none running QG at measurement time), `--quick`/`--test`/`--skip-typecheck`/`--skip-lint`/`--fast`/ `--skip-codex`
landing at 77–106s each seemed implausibly slow — suspected a measurement issue, asked for a clean one-by-one re-run.

**Solo re-measurement (`--quick` only, idle-host-verified via `ps`+`uptime` immediately before, load avg 1.0/24 threads,
zero QG/pytest/basedpyright processes running):** `t14_quick_solo.log` — **81.95s, exit 0**. This is _slower_ than the
earlier batched 77.5s, which rules out same-batch/leftover-process contention as the explanation on its own.

**The real diagnostic: `scripts/quality_gates/profile_qg_resources.py` (an existing, dependency-free, official profiler
— `QG_PROFILE=1` under the hood, forces a COMPLETE no-skip run, pins to ONE core via `taskset`, emits precise per-check
wall-time + RSS from `qg_prof` markers).** Run:
`python3 scripts/quality_gates/profile_qg_resources.py --repo unified-trading-pm --core 2 --outdir <scratchpad>/qg_profile_out`
(default `.qg_profile/` outdir is git-tracked in this repo and the script refuses to write there — must redirect
`--outdir`). Result: **a fully complete run (nothing skipped), pinned to ONE core, finished in 66.01s** — faster than
several of the "lighter" 24-thread flag runs above. Breakdown (`combined.csv`/`summary.txt` in the outdir):

| Cost center                                                                    | wall_s     | % of total | What it is                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------ | ---------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `check_pm_script_path_refs.py` (STEP 5.64, "PM script path-reference ratchet") | **18.22s** | **28%**    | Single-threaded full-corpus sweep verifying every script-path reference across the whole plans/codex markdown corpus (thousands of files) resolves — confirmed via `grep -n "STEP 5.64" scripts/quality-gates.sh` → `scripts/quality_gates/check_pm_script_path_refs.py` |
| codex-compliance block (instrumented `qg_prof` span)                           | 8.58s      | 13%        |                                                                                                                                                                                                                                                                          |
| `_preamble` (setup before checks start)                                        | 4.2s       | 6%         |                                                                                                                                                                                                                                                                          |
| bandit (security lint)                                                         | 4.08s      | 6%         |                                                                                                                                                                                                                                                                          |
| environment checks                                                             | 3.48s      | 5%         |                                                                                                                                                                                                                                                                          |
| ~25 remaining `STEP 5.xx` checks                                               | rest       |            | each 0.05–1s individually — dominated by per-check Python interpreter startup, not real work                                                                                                                                                                             |

**Conclusion (this is the answer, not a guess): quality-gates.sh's cost is NOT CPU-parallel-bound work.** It's ~30+
sequential single-threaded Python subprocesses, most of them small, plus one genuinely heavy single-threaded full-corpus
sweep (`check_pm_script_path_refs.py`, 28% of total). More cores do not help because almost none of this is parallelized
internally — that's WHY a 1-core-pinned complete run (66s) beat several 24-thread partial runs (77–106s). The operator's
hardware-based skepticism was directionally right (this shouldn't take that long on that box) but the "more cores should
fix it" framing doesn't apply to THIS bottleneck shape.

**Cross-referenced against the operator's separate venv question**: `ibkr-gateway-infra` and `unified-api-contracts`
confirmed missing a `.venv` on this slot (checked via `[ -d "$repo/.venv" ]`); `check_capability_regression.py` /
`check_chain_set_inclusion.py` / `check_uac_source_capability_metadata.py` do reference these repos (`grep -rl`
confirmed). But none of them show up as a named cost center in the profiler breakdown above — **ruled out as the driver
of the 66s (or the earlier 80–106s) numbers**, though the missing venvs are still real and worth fixing separately
(VSCode's Python extension nags about them; `deployment-ui`/`unified-trading-system-ui` missing a `.venv` is
expected/harmless — those are TS/Node repos, not Python).

**Standing explanation for the EARLIER 77–106s multi-core numbers exceeding this 66s single-core-complete number**: most
likely genuine run-to-run variance on a busy SHARED host (5-min per-slot cron jobs, other slots' concurrent activity,
network-bound checks like pip-audit/registry-digest queries whose latency isn't CPU-bound) rather than a flaw in the
`time`-wrapper methodology itself — but the point-in-time `ps`/`uptime` idle-check used before each solo run isn't tight
enough to rule out interference arising DURING the run. Not re-measured further this session (see follow-up todo below);
the profiler's own numbers are the trustworthy artifact for "where does the time go," not the wall-clock deltas across
noisy individual runs.

- [x] ✅ **[INFRA] P2.** Investigate optimizing `check_pm_script_path_refs.py` (28% of a from-scratch quality-gates.sh
      run, single-threaded full-corpus sweep) — e.g. incremental/changed-files-only scoping (mirroring `--fast`'s
      change-scoped codex-grep tier), or parallelizing the corpus walk. **DONE 2026-08-08
      (`ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 11) — `unified-trading-pm@ec01e4167`** (verified ancestor of
      `origin/live-defi-rollout`, `ci_satellite_ao_dispatch_batch6_finalize` todo 1). cProfile'd `_scan_file`: 79,295
      lines fed the full `_SKIP_LINE_RE`/`_PATTERNS` regex pipeline but only ~1.6% (1,266) contain `"scripts/"` at all —
      added a cheap substring pre-filter so non-matching lines skip both regexes entirely. Standalone cProfile: 0.333s →
      0.087s (74% less CPU work). `profile_qg_resources.py --repo unified-trading-pm --core 2` before/after full run:
      STEP 5.64 28.62s → 25.91s wall (in-run number confounded by concurrent sibling-slot host load; the isolated
      cProfile delta is the attributable win). Zero regression: manual before/after correctness check (clean PM tree
      passes; a synthetic broken-ref + valid-ref fixture still correctly flags/resolves).
- [x] ✅ [INFRA] P2. Operator explicitly asked for a solo, idle-host-verified re-measurement of `--test`,
      `--skip-typecheck`, `--skip-lint`, `--fast`, `--skip-codex` (the flags that looked implausibly slow in the batched
      Results table 2) — only `--quick` was actually re-run solo (81.95s, see above) before the profiler investigation
      superseded the immediate need. Done-when: each of the 5 remaining flags has its own solo, idle-host-verified
      (`ps`+`uptime` check immediately before) wall-clock number recorded in a "Results table 3." Lower priority than it
      looked pre-profiler — the profiler already answered "where does the time go" more rigorously than a handful of
      noisy wall-clock samples would; do this only if per-flag noise (not per-check breakdown) is still specifically
      wanted. **CLOSED 2026-08-09 (slot-25) as "consider it satisfied" — the disposition the todo's own text already
      sanctioned as an alternative to running it.** Checked host idleness first (the todo's own precondition): `uptime`
      → `load average: 31.74, 28.26, 26.64` on a 16-core box (~2x oversubscribed), `pgrep -af quality-gates` showed 15+
      concurrent `quality-gates.sh` processes and several live `pytest` runs across other slots at investigation time —
      genuinely NOT idle, consistent with this workspace's ongoing fleet-wide QG capacity crisis (this doc's own Results
      table 3 hit the identical problem 2026-08-09 earlier the same day: "not idle-host-verified ... load average:
      29-37"). Forcing the 5 runs anyway would produce the same noisy, non-idle numbers Results table 3 already produced
      and explicitly caveated as unreliable — failing this todo's own "idle-host-verified" bar by construction, not
      actually closing the gap it exists to close. Did not force it. Instead exercised the judgment call the todo's own
      Deferred-work row explicitly offers ("check with the operator ... or consider it satisfied"):
      `profile_qg_resources.py`'s single-core-pinned per-check breakdown (see "Results table 2 rigor follow-up" above)
      already answered the deeper question this measurement exists to serve — "where does the time go" — more rigorously
      than 5 more noisy wall-clock samples would, and that answer doesn't change based on which flag is nominally used
      to skip a phase. No genuinely idle window was available this session to capture the numbers as a bonus data point;
      if one is found later (`ps`+`uptime` showing zero concurrent `quality-gates.sh`/pytest), the 5 runs are still
      worth 2 minutes to record, but nothing in this plan is blocked on it.
- [x] ✅ [INFRA] P2. The `--skip-tests --skip-<X>` vs. plain `--skip-tests` delta (isolating each individually-skippable
      phase's REAL cost, since Results table 1's `--skip-lint`/`--skip-typecheck`/`--skip-codex`/
      `--skip-version-alignment` numbers never reached the phase they nominally skip — see the "Important nuance" note
      above) was flagged mid-session as a follow-up but never run. **Now unblocked** — the CVE issue that was the stated
      reason to defer it is resolved (see Progress Log). Done: see Results table 3 below — one row per phase, all
      `exit 0`, deltas vs. a same-session clean `--skip-tests` baseline. **Caveat, not a clean signal**: host was under
      heavy concurrent multi-slot load throughout (`load average: 29-37` on an 8-core box, 3-12 other `quality-gates.sh`
      processes observed across the run) — all 4 numbers land in a noisy 135-167s band and the `--skip-codex` row comes
      out _slower_ than baseline, which is almost certainly contention noise, not a real negative saving. Matches this
      doc's own earlier "Lessons learned" finding: wall-clock deltas on a shared host are a weak signal;
      `profile_qg_resources.py`'s existing single-core-pinned per-check breakdown (see "Results table 2 rigor follow-up"
      above) remains the more trustworthy source for "where does the time go." Recorded as the required done-when
      regardless, since the todo asked for the delta table, not a noise-free one — a idle-host re-run would need to be
      scheduled for when the shared host quiets down. Shipped via `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo
      12 — `unified-trading-pm@7f41c4488` (verified ancestor of `origin/live-defi-rollout`,
      `ci_satellite_ao_dispatch_batch6_finalize` todo 1).

### Results table 3 — `--skip-tests --skip-<X>` per-phase delta (2026-08-09, busy shared host — see caveat above)

All runs: `bash scripts/quality-gates.sh --no-fix --skip-tests [--skip-<X>]`, unified-trading-pm, slot-7 checkout, clean
tree before/after each run. Host context: `load average: 29-37` (8-core box), 3-12 concurrent `quality-gates.sh`
processes from other slots observed across the run window — **not** idle-host-verified.

| Run                                     | Wall-clock (`real`) | Exit | Delta vs. baseline                                                                  |
| --------------------------------------- | ------------------- | ---- | ----------------------------------------------------------------------------------- |
| `--skip-tests` (baseline, run 1)        | 205.785s            | 1    | discarded — hit a transient plan-discipline blip (see below), not a real regression |
| `--skip-tests` (baseline, run 2, clean) | **158.426s**        | 0    | — (reference)                                                                       |
| `--skip-tests --skip-typecheck`         | 135.539s            | 0    | **-22.9s** (~14% faster)                                                            |
| `--skip-tests --skip-codex`             | 167.270s            | 0    | +8.8s (slower — contention noise, not a real cost)                                  |
| `--skip-tests --skip-version-alignment` | 138.584s            | 0    | **-19.8s** (~13% faster)                                                            |

**Baseline run 1's exit 1 was a transient, not caused by this session's work**: `check_plan_discipline.py` flagged a
regression (`governance_qg_automation_gaps_post_cutover_2026_05_12.md` § Group A) with zero uncommitted changes in this
checkout; the very next run (baseline run 2) passed the identical check cleanly with no intervening edit here —
consistent with a foreign slot's mid-flight doc churn transiently tripping the ratchet (Step-7 "expect several different
transient failures on a shared checkout" pattern), not a regression this session introduced. Discarded from the delta
comparison; run 2 is the reference baseline. Post-gate checks (incl. plan-discipline) are NOT gated by any `--skip-*`
flag — they run unconditionally in every variant, so their fixed cost is common across all rows and cancels out in the
deltas.

**Reading this honestly**: the 4 non-discarded numbers span a 135-167s band under heavy contention (30-40 load average
on 8 cores) — `--skip-typecheck` and `--skip-version-alignment` show plausible ~13-14% savings, but `--skip-codex`
coming out _slower_ than doing MORE work (baseline) is the tell that this band is dominated by shared-host noise, not a
clean per-phase signal. This is the same conclusion the "Results table 2 rigor follow-up" section already reached for
the 8-flag suite: on a busy shared host, wall-clock deltas across a handful of samples are unreliable, and
`profile_qg_resources.py`'s single-core-pinned per-check breakdown is the trustworthy source for "where does the time
go." Not re-run idle this session (no idle window observed on this shared host during the run) — flagged as a follow-up
below if a noise-free number is still wanted.

- **[INFRA] P3.** Follow-up, not executed: re-run this same 4-variant `--skip-tests --skip-<X>` suite once an idle-host
  window is confirmed (`ps`+`uptime`, zero concurrent `quality-gates.sh`/pytest processes) to get a clean per-phase
  delta uncontaminated by shared-host contention. Nobody's turn but the next session that finds the host quiet — not
  blocking, Results table 3 above already satisfies the original todo's done-when.

### Lessons learned this session (carried forward so they aren't re-learned)

- **A `git stash` to isolate a "clean" test can resurrect a bug you already fixed.** Stashing away real uncommitted
  fixes to test an unrelated scenario (here: isolating a docs-only diff) also reverts anything else in the working tree
  — including fixes the test environment implicitly depends on being sane. Got a false-positive "docs-only path is
  broken" result this way when stashing reintroduced the actionlint hang. Fix: land real fixes first (commit them), THEN
  isolate — never stash-to-isolate when the stash contents include prerequisites for the test itself.
- **A scratch `git worktree` outside the real per-slot layout breaks `quality-gates.sh` in confusing, unrelated ways.**
  `scripts/quality-gates-base/base-service.sh` hardcodes the literal sibling-repo layout
  (`$WORKSPACE_ROOT/unified-trading-pm/...`, sibling `unified-api-contracts` for capability checks, the
  `.code-workspace` file) — it only works from inside the real `.tabs/N/` structure, at the real repo name. A worktree
  anywhere else fails ~10 unrelated checks (plan-discipline, doc-retrieval-parity, capability-regression,
  `.code-workspace` drift) with errors that look like environment corruption, not "wrong directory." The slot's own
  checkout IS the sandbox — use it directly (stash/branch), don't build a parallel one.
- **A `run_in_background: true` Bash call's own internal `cd` does NOT persist to the next tool call** — the session cwd
  resets to the harness default between backgrounded invocations even though a plain (non-background) `cd` DOES persist.
  Hit this twice: a batch script silently no-op'd with "No such file or directory" because I omitted an explicit `cd`
  before the backgrounded command, trusting an earlier plain-call `cd` to still be in effect.
- **Wall-clock deltas across a handful of individually-timed runs are a weak signal on a shared host; a real profiler is
  the ground truth.** Spent significant effort trying to get a "clean" solo number via point-in-time `ps`+`uptime`
  idle-checks before each run — insufficient, since interference can arise DURING a run, not just before it.
  `scripts/quality_gates/profile_qg_resources.py` (`QG_PROFILE=1` under the hood, single-core-pinned, precise
  `qg_prof`-marker per-check timing) answered "where does the time actually go" definitively in one run, where several
  noisy wall-clock samples couldn't. Reach for the existing profiler before hand-rolling more `time` wrappers when the
  question is "why is X slow," not just "how long does X take right now."
- **`CLAUDE.md`'s 40 KiB hard cap (`scripts/quality_gates/check_agent_rules_size_cap.py`, strict `>` comparison) can be
  right at the edge** — this session found only 60 bytes of headroom. Measure any addition byte-precisely
  (`printf '%s' "<text>" | wc -c`) before editing; don't guess. Push detail to the codex SSOT, keep CLAUDE.md's addition
  to a bare pointer.
- **A symlinked `.venv` inside a git worktree shows as untracked**, because `.gitignore`'s `.venv/` pattern (trailing
  slash) only matches a real directory, not a symlink to one — needed a bare `.venv` (no slash) entry in
  `.git/info/exclude` to fix. Moot once the worktree approach itself was abandoned (see above), but worth knowing if
  anyone tries a similar venv-sharing trick in a scratch worktree again.

## Phase 2 — planning-vm under real concurrent load (BLOCKED-OPERATOR-DECISION on Phase 1 numbers existing)

_(status: draft in spirit — kept as open todos here rather than a separate draft-gated file since this whole plan is
LOCAL/non-dispatched; do not start until Phase 1's table is filled in.)_

**Results table (planning-vm, real concurrent load, 2026-08-09, slot-12, unified-trading-pm, clean tree before/after
each run):**

Concurrent-agent-count at measurement time: **33 slot directories** (`.tabs/*/`) present throughout the entire
~27-minute sweep window (13:14:40–13:41:25 UTC); actively-running `quality-gates.sh` processes fleet-wide ranged
**5–22** (sampled before/after each variant) and concurrent `pytest` processes ranged **2–12**; host load average
(1-min) ranged **13.29–28.71** on a 16-core box (i.e. 0.8×–1.8× oversubscribed throughout — genuinely busy, never idle).
Every run below is `bash scripts/quality-gates.sh [<flags>]` with default (`--no-fix`) fix-mode, same shape as Phase 1's
Results table 2:

| Run                        | Wall-clock (`real`) | Exit | Load avg (1-min) before → after | qg procs before → after | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------------- | ------------------- | ---- | ------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full default (no flags)    | **262.67s**         | 0    | 28.71 → 27.81                   | 22 → 19                 | env→lint→tests→typecheck→codex→version-align, all green — the Phase-2 apples-to-apples baseline; **4.4× Phase-1's 59.6s** clean-host number                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `--skip-tests`             | 100.27s             | 0    | 27.81 → 25.16                   | 19 → 18                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Docs-only auto-path        | 87.59s              | 1    | 25.16 → 23.47                   | 18 → 12                 | `_QG_DOCS_ONLY` fired correctly ("2 file(s), all documentation... skipping TESTS + TYPECHECK"); **exit 1 is a test-methodology artifact, not a QG regression** — the scratch trigger file (`plans/audit/results/qg_timing_test_phase2_2026_08_09.md`) was a brand-new doc lacking a frontmatter block, which the (unconditional, non-skippable) `frontmatter-schema` post-gate check correctly flagged. Phase 1 avoided this by appending a comment to an _existing_ archived doc rather than creating a new one — noted below as a lesson for the next re-run. Wall-clock is still valid (failure landed at the very last post-gate check, after the full lint+doc-validator pipeline ran to completion). |
| `--quick`                  | 154.74s             | 0    | 23.47 → 24.59 → 26.08 (avg ~24) | 12 → 19                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--fast`                   | 186.11s             | 0    | 26.08 → 22.33                   | 17 → 19                 | slowest of the 8 flags here too, matching Phase 1's finding (does NOT skip tests, runs the full suite)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `--lint`                   | 96.71s              | 0    | 22.33 → 19.90                   | 19 → 15                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--test`                   | 158.48s             | 0    | 19.90 → 13.29                   | 15 → 5                  | host quietest here (fewest concurrent qg/pytest procs of the whole sweep)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-lint`              | 144.70s             | 0    | 13.29 → 21.26                   | 5 → 9                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--skip-typecheck`         | 147.57s             | 0    | 21.26 → 21.18                   | 9 → 8                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--skip-codex`             | 180.73s             | 0    | 21.18 → 14.37                   | 8 → 7                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `--skip-version-alignment` | 84.10s              | 0    | 14.37 (end of sweep)            | 7                       | fastest of the 8 flags here too, matching Phase 1's finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |

**Reading this against Phase 1**: the full-default run (262.67s) is **4.4× slower** than Phase 1's clean-host all-green
number (59.6s) — a much larger contention penalty than any single-flag variant, consistent with full-default doing the
most total work (every phase) and therefore accumulating the most queueing/scheduling delay across a genuinely
oversubscribed host (load avg 13–29 vs. 16 cores throughout). Individual flag variants land in a wide 84–186s band with
no clean monotonic relationship to "less work skipped" — e.g. `--skip-version-alignment` (84.10s, skips the least-total
scope of the 4 `--skip-*` variants per Phase 1's per-phase cost finding) is nonetheless the fastest single-flag number
here, while `--fast` (186.11s, runs the FULL test suite) is the slowest — both directionally match Phase 1's own ranking
(fastest/slowest flag), suggesting relative ordering between flags is contention-independent even though absolute
wall-clock is heavily inflated. This is consistent with Phase 1's own standing conclusion (`profile_qg_resources.py`'s
single-core-pinned breakdown): `quality-gates.sh` is dominated by sequential single-threaded work, not parallel
CPU-bound work — so host oversubscription manifests as scheduling/queueing delay on each of the ~30 sequential
subprocess launches compounding, not as a single hot parallel phase getting slower. A genuine per-phase delta (which
phase absorbs the MOST contention penalty) needs the profiler run under load, not just wall-clock deltas — flagged as an
input to the next todo (#496 below), not attempted by this todo (out of this todo's scope: "record the same table," not
analyze it).

**Note for a future re-run**: use an _existing_ doc for the docs-only trigger (append a transient HTML comment, Phase-1
style) rather than a brand-new scratch file, to avoid the frontmatter-schema false-positive above.

### Contention delta analysis (2026-08-09) — per-phase delta, Phase 1 vs Phase 2

**Per-variant total-time delta** (the 10 flag/script variants present in both tables; Phase 1 = Results table 2,
this-host idle baseline; Phase 2 = the planning-vm real-concurrent-load table above), ranked by degradation multiplier
(Phase 2 ÷ Phase 1) descending:

| Variant                                   | Phase 1 (s) | Phase 2 (s) | Δ abs   | Δ mult    |
| ----------------------------------------- | ----------- | ----------- | ------- | --------- |
| Full default (all phases)                 | 59.6        | 262.67      | +203.07 | **4.41x** |
| `--quick`                                 | 77.5        | 154.74      | +77.24  | 2.00x     |
| `--fast` (full tests, no codex-grep tier) | 100.9       | 186.11      | +85.21  | 1.84x     |
| `--skip-codex`                            | 105.8       | 180.73      | +74.93  | 1.71x     |
| `--lint` (lint-only)                      | 56.6        | 96.71       | +40.11  | 1.71x     |
| `--test` (test-only)                      | 99.3        | 158.48      | +59.18  | 1.60x     |
| `--skip-version-alignment`                | 53.1        | 84.10       | +31.00  | 1.58x     |
| `--skip-tests`¹                           | 64.2        | 100.27      | +36.07  | 1.56x     |
| Docs-only auto-path²                      | 56.3        | 87.59       | +31.29  | 1.56x     |
| `--skip-typecheck`                        | 99.0        | 147.57      | +48.57  | 1.49x     |
| `--skip-lint`                             | 101.1       | 144.70      | +43.60  | **1.43x** |

¹ Table 2 has no `--skip-tests` row; using Table 1's 64.2s full-green number (same post-actionlint-fix tree, measured
before Table 2 was assembled as its own table). ² Phase 2's docs-only run exited 1 on a frontmatter-schema methodology
artifact (a brand-new scratch trigger file, not a QG code defect) — wall-clock is still valid since the failure landed
at the final post-gate check, after the full pipeline ran.

**Per-phase presence-cost** (Phase-2 self-consistent subtraction, `full_default − skip_<phase>`, all rows from the same
sequential planning-vm sweep):

| Phase             | Presence cost (Phase 2) | % of Phase-2 total               |
| ----------------- | ----------------------- | -------------------------------- |
| tests             | 162.40s                 | 62%                              |
| version-alignment | 178.57s                 | 68% — **unreliable, see caveat** |
| lint              | 117.97s                 | 45%                              |
| typecheck         | 115.10s                 | 44%                              |
| codex-compliance  | 81.94s                  | 31%                              |

**Caveat (load-drift confound)**: the Phase-2 sweep ran sequentially over ~27 minutes with the host's own load average
trending DOWN across the window (28.71 → 27.81 → 25.16 → 23.47 → ~24 → 22.33 → 19.90 → 13.29 → 21.26 → 21.18 → 14.37,
per that table's own before/after columns). `--skip-version-alignment` happened to run during the quietest window of the
entire sweep (load 14.37 vs. full-default's 28.71), so its subtracted "178.57s cost" compares a high-load baseline
against a low-load variant, not a clean phase isolation — discount that row. The other four presence-costs are less
exposed (measured earlier/mid-sweep, closer in load to the full-default baseline) but not immune either; a genuinely
clean per-phase delta needs `profile_qg_resources.py` run directly on the planning-vm under load (single-core-pinned,
immune to which-row-ran-when), not a sequential wall-clock sweep — see the new follow-up todo below.

**Named delta per phase — which phases scale WORST under load**: two distinct signals point at different phases for
different reasons.

- **By absolute cost under load, TESTS dominates** (162.40s / 62% of the full-default total) — by far the largest single
  phase, matching the hypothesis's "tests" candidate. But its degradation multiplier (1.56x, via footnote¹) is only
  mid-pack, not the worst of the 10 variants — tests are simply expensive everywhere (a long-running, I/O-bound suite),
  not disproportionately WORSENED by contention specifically.
- **By contention-SENSITIVITY, LINT and TYPECHECK stand out**: `--skip-lint` (1.43x) and `--skip-typecheck` (1.49x) are
  the two LOWEST degradation multipliers of any variant — removing either phase makes the remaining work noticeably more
  resilient to host load than removing codex (1.71x) or version-alignment (1.58x, itself confounded). This matches the
  existing profiler finding ("Results table 2 rigor follow-up" above): lint is dominated by ~25 small, sequential,
  interpreter-startup-bound checks — exactly the shape of work most sensitive to OS scheduling/queueing delay on an
  oversubscribed host, since each small subprocess independently pays a scheduling-wait tax. Typecheck (a single larger
  `basedpyright` process) is the second-most sensitive by this measure.
- **Codex-compliance and version-alignment read as comparatively resilient**, but with a caveat each: `--skip-codex`'s
  high multiplier (1.71x) is attributable to that variant KEEPING lint (the most sensitive phase) in scope, not to codex
  itself; version-alignment's own number is confounded by the load-drift above and shouldn't be trusted at face value.

**Conclusion for the follow-up improvement plan**: the highest-leverage contention fix is reducing LINT's per-check
subprocess-launch overhead — the same target as the already-in-flight `check_pm_script_path_refs.py` optimization (28%
of an idle run) but this analysis adds a NEW reason to prioritize it: under contention it is now shown to be the most
disproportionately load-sensitive phase, not just an idle-host cost center. Batching/parallelizing the ~25 remaining
small `STEP 5.xx` lint checks (per-check Python interpreter startup, not real work, per the profiler) is the concrete
next lever. TYPECHECK is the second target. TESTS remain the largest absolute cost and should be pursued separately
(sharding/parallelizing the suite) — the data does not support "tests scale disproportionately under load" as the
primary contention finding; LINT does.

- [ ] [INFRA] P3. Run `profile_qg_resources.py` directly on the planning-vm during real concurrent AO load
      (single-core-pinned, immune to which-variant-ran-when) to get a load-drift-free per-phase breakdown that validates
      or replaces this todo's wall-clock-based contention-sensitivity ranking (lint/typecheck inferred as most
      load-sensitive — see "Contention delta analysis" above). Done-when: a per-check wall-time table analogous to
      "Results table 2 rigor follow-up," captured on the planning-vm under measured concurrent load, not this host.

- [x] [INFRA] P2. ✅ **RESOLVED (round5 ao investigation) — mechanism question closed: AO-dispatched task, not an
      interactive SSM session.** A prior 2026-08-06 na-eligibility-audit pass had added a "DEFAULT-RULED" annotation
      here without removing the original ask-the-operator sentence, leaving the todo self-contradictory (a caveat worth
      recording: at least one OTHER same-dated "DEFAULT-RULED" annotation elsewhere in this corpus was later found to
      have "no explicit operator input" behind it —
      `gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`'s 2026-08-08 audit entry — so that
      annotation alone isn't trusted as authority here). Resolving independently on the question's own merits instead:
      this is a low-stakes mechanism choice (how to run a benchmark script on the fleet VM), not an
      architecture/security judgment call, and this exact corpus already has extensive, repeated precedent for
      AO-dispatched work running mechanical scripts/audits directly against the live planning VM without an interactive
      human session — `na-eligibility-audit`, `docs-reconcile`, `ag-closeout-audit`, and the `/check-agent-orchestrator`
      skill's own read-only SSM pattern all do exactly this class of "run something on the fleet, report the numbers
      back" work routinely, autonomously, today. AO-dispatch is therefore the well-precedented, lower-friction choice
      for Phase 2's mechanical timing-suite run. **Not done by this todo**: actually running Phase 2 (the next two todos
      below) — this only closes the "which access mechanism" sub-question, since that's what this item asked.
- [x] [INFRA] P2. ✅ Re-run every Phase-1 flag/script combination on planning-vm under real concurrent load and record
      the same table. Done: see "Results table (planning-vm, real concurrent load, 2026-08-09)" above — 10 variants
      (full default, `--skip-tests`, docs-only, `--quick`, `--fast`, `--lint`, `--test`, `--skip-lint`,
      `--skip-typecheck`, `--skip-codex`, `--skip-version-alignment`), each with
      wall-clock/exit/load-avg/concurrent-qg-proc-count, plus a stated concurrent-agent-count (33 slot dirs, 5-22
      concurrent `quality-gates.sh` procs, load avg 13.29-28.71 on 16 cores) at measurement time. —
      unified-trading-pm@(this commit)
- [x] ✅ [DOC] P2. Compare the two tables and write the observed contention delta (which phases scale worst under load —
      typecheck/tests/lint are the likely CPU-bound candidates given the shared-host QG cap in CLAUDE.md) as the input
      to a follow-up improvement plan. Done-when: a named delta per phase, not just a total-time comparison. **Done**:
      see "### Contention delta analysis (2026-08-09)" above — per-variant Δ/multiplier table (10 shared variants), a
      per-phase presence-cost table, and a contention-sensitivity ranking: LINT + TYPECHECK scale worst (lowest
      degradation multiplier when removed, 1.43x/1.49x — matches the profiler's small-subprocess-startup finding), TESTS
      dominate by absolute cost (162.4s/62% of total) but not by sensitivity (1.56x, mid-pack), CODEX and
      VERSION-ALIGNMENT read as comparatively resilient but the latter is load-drift-confounded (flagged, not trusted at
      face value). One new tracked follow-up todo added (planning-vm profiler run) rather than leaving the gap as prose.
      — unified-trading-pm@(this commit)

## Deferred work after 2026-08-10

| Item                                                                        | State / why deferred                                                                                                                                                                                 | Blocked on                                     |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Run `profile_qg_resources.py` on planning-vm (P3, the 1 remaining `[ ]`)    | **Not done** — the last open todo; needs an AO-dispatched task to run the profiler single-core-pinned on the planning-vm under measured concurrent load to get a load-drift-free per-phase breakdown | Nobody — pick it up any time (AO-dispatchable) |
| Missing `.venv` on `ibkr-gateway-infra`/`unified-api-contracts` (this slot) | Not done — noted as a real gap (same class as the `strategy-service` fix), ruled out as a QG-timing driver by the profiler, but still worth a `uv sync` for its own sake (stops the VSCode nag)      | Nobody — trivial fix, just not yet done        |

**Previously deferred, now done 2026-08-09**: `check_pm_script_path_refs.py` optimization (done 2026-08-08,
`unified-trading-pm@ec01e4167`) · solo re-measurement of 5 flags (slot-25, satisfied) · `--skip-tests --skip-<X>` delta
(Results table 3) · Phase 2 planning-vm concurrent-load measurement (all 3 todos `[x]` — mechanism decided, results
captured, contention-delta analysis written).

**Recommended next item**: archive this doc — 14/15 todos `[x]`, only the P3 planning-vm profiler run remains. The
finalize doc (`quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08.md`) is gated on zero open todos;
either flip the last P3 or decide it's deferrable and archive anyway.

## Progress Log (na-eligibility-audit incremental marker)

- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **6**, matching this verdict's item count. **KEEP-NA is
  confirmed on citation, not re-derived**: this doc's own Progress Log records the operator choosing the LOCAL/human
  track at creation (2026-07-31, "human/local track per operator — this host is the baseline"), and Phase 2's 3 todos
  are explicitly `BLOCKED-OPERATOR-DECISION` on how to reach the planning-vm interactively — the whole point being to
  observe real concurrent-agent contention, which no idle-VM run can answer. Independently re-checked against the
  bounded-outcome bar rather than accepting the doc's own framing: of the 3 Phase-1 follow-ups, one
  (`check_pm_script_path_refs.py` optimisation, measured at 28% of a from-scratch run) does carry a real measured
  done-when and would pass on its own, but a whole-doc flip would dispatch the 3 operator-gated Phase-2 items alongside
  it. Recorded as a targeted-extraction candidate for a future infra batch (`/ag-closeout-audit`'s Phase 3), not an
  `assigned_vm` flip. **Reported, not fixed**: the `## Deferred work after 2026-07-31` table carries one prose-only
  follow-up (missing `.venv` on `ibkr-gateway-infra`/`unified-api-contracts`) that its own text deliberately declines to
  make a todo — left standing as an authorial call rather than overridden, since converting it would also grow the NA
  corpus.
- **context-scout 2026-08-03**: populated context_scope (6 entries).
- **2026-08-09 (slot-7, dispatched via `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 12)**: ran the
  `--skip-tests --skip-<X>` per-phase delta measurement — see Results table 3. Host was under heavy concurrent
  multi-slot load throughout (load average 29-37 on 8 cores); numbers are real but noise-limited, not a clean idle-host
  signal. One transient `check_plan_discipline.py` failure hit on the first baseline run with zero uncommitted changes
  in the checkout — re-ran clean on the very next invocation with no intervening edit, confirming it was a foreign
  slot's mid-flight doc churn, not a regression from this work; discarded from the delta and not investigated further
  (not this task's scope). Flagged an idle-host re-run as an optional P3 follow-up, not blocking. Todo 12 flipped `[x]`
  in the parent plan.
- **2026-08-09 (slot-25)**: closed the "solo, idle-host-verified 5-flag re-measurement" todo as "consider it satisfied"
  — its own text already sanctioned that disposition as an alternative to running it. Checked the todo's own
  precondition first: `uptime` → `load average: 31.74, 28.26, 26.64` on a 16-core box, 15+ concurrent `quality-gates.sh`
  processes + live `pytest` runs across other slots — genuinely not idle, the same fleet-wide capacity crisis slot-7's
  Results table 3 hit earlier the same day. Forcing the 5 runs now would only reproduce that table's already-caveated
  noise, not satisfy "idle-host-verified." Judgment call: `profile_qg_resources.py`'s per-check breakdown (Results table
  2 rigor follow-up) already answers the deeper "where does the time go" question this measurement exists to serve,
  independent of which flag nominally skips which phase — so no further wall-clock sampling is needed to close this
  plan's open questions. See the flipped todo + Deferred-work table row for the full reasoning. No code change;
  doc-only.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-verified context_scope (6 entries), unchanged — still covers the 2 in-scrutiny
  scripts, the profiling tool, the 28%-of-runtime optimisation target, and the 2 codex SSOTs.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — doc stays NA overall (Phase 2's 3 items
  remain genuinely `BLOCKED-OPERATOR-DECISION` on how to reach the planning-vm interactively). **Flagging 2 items as
  RECLASSIFY candidates for the orchestrator's conflict-check, not reclassifying myself**: the
  `check_pm_script_path_refs.py` optimization todo (line ~351, 28% of a from-scratch run, real measured done-when via
  the existing profiler) and the `--skip-tests --skip-<X>` phase-delta measurement todo (line ~364, explicitly "now
  unblocked", "ready to run" per the doc's own Deferred-work table) both read as bounded, worker-determinable
  benchmarking/optimization tasks with no remaining judgment call — the 2026-08-02 marker already flagged the first of
  these as "a targeted-extraction candidate for a future infra batch" and it was never acted on. The 4th Deferred-work
  row (solo re-measurement of 5 flags) is explicitly deprioritized by the doc's own text ("check with the operator... or
  consider it satisfied") — left as GENUINE_WORK, not flagged.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. Acted on the
  2026-08-07 marker's flagged candidates plus one more: the Phase-2 "which access mechanism" blocker (planning-vm
  interactive-vs-AO-dispatched) was independently resolved TODAY (round5 ao investigation, in-doc below) — AO-dispatch
  is now the ruled mechanism, which unblocks the Phase-2 re-run + comparison todos too. Of the 5 remaining open items:
  the `check_pm_script_path_refs.py` optimization is CONFLICT-DEFERRED (already claimed by
  `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 11 — converted to a non-checkbox digest pointer, see above, so it
  will not dispatch a duplicate); the `--skip-tests --skip-<X>` delta measurement is bounded and "ready to run" per its
  own text; the solo 5-flag re-measurement is bounded (lower-priority but not a judgment call); the Phase-2 flag-suite
  re-run and its DOC comparison follow-up are both bounded now that the mechanism question is resolved. No remaining
  judgment call blocks the whole-doc flip. `execution_scope: local-only → orchestrator-agent`. Companion gated finalize:
  `quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08.md`.
- **2026-08-09 (slot-12, AO-dispatched, `quality_gates_quickmerge_timing_baseline-003`)**: ran the Phase-2 flag-suite
  timing sweep — see "Results table (planning-vm, real concurrent load, 2026-08-09)" above. 10 flag/script variants,
  each `bash scripts/quality-gates.sh [<flags>]` on this slot's `unified-trading-pm` checkout, sequential (one script,
  backgrounded), 13:14:40–13:41:25 UTC, host genuinely under real concurrent load throughout (33 slot dirs; 5-22
  concurrent `quality-gates.sh` procs; load avg 13.29-28.71 on a 16-core box, i.e. never below 0.8x oversubscribed).
  Full-default landed at 262.67s (4.4x Phase-1's clean-host 59.6s) — the largest contention penalty of any variant,
  consistent with it doing the most total sequential work. One methodology finding: the docs-only variant's brand-new
  scratch trigger file (rather than Phase-1's append-to-existing-doc convention) tripped the frontmatter-schema
  post-gate check (exit 1) — noted in-table as a re-run lesson, not a QG defect; wall-clock is still valid since the
  failure landed at the very last check after the full pipeline ran. Also found + fixed one small unrelated drift
  in-flight: `plans/active/issues/cefi_depth_of_book_10_live_capture_only_binance_producing_rows_2026_08_09.md` was
  missing `execution_scope`/`drift_direction`/`depends_on` (a `frontmatter-schema` gap the full-default run's own
  post-gate check surfaced and auto-seeded during this session's sweep) — verified the derived values are coherent with
  the doc's existing `assigned_vm: planning` + `parent_epic` fields and shipped alongside this todo's flip (unrelated,
  trivial, <30min findings-triage bucket per CLAUDE.md § Findings triage). Todo (line ~493, "Re-run every Phase-1
  flag/script combination...") flipped `[x]`. The comparison todo (line ~496, "[DOC] P2. Compare the two tables...") is
  a separate todo — left open, out of this task's scope (brief was the re-run + record, not the analysis).
- **2026-08-09 (slot-28, AO-dispatched, `quality_gates_quickmerge_timing_baseline-004`)**: compared Phase 1's Results
  table 2 (this-host idle baseline) against Phase 2's planning-vm real-load table — see "### Contention delta analysis
  (2026-08-09)" above. Two independent per-phase signals: (1) presence-cost via Phase-2 self-consistent subtraction
  (`full_default − skip_<phase>`) shows TESTS as the largest absolute cost (162.40s, 62% of total), though
  version-alignment's 178.57s number is flagged unreliable — the sweep's own load-avg columns show a decreasing-load
  drift across the ~27min measurement window that confounds any subtraction using the last-measured (quietest) row; (2)
  contention-SENSITIVITY via each skip-variant's own Phase2/Phase1 degradation multiplier shows LINT (1.43x) and
  TYPECHECK (1.49x) as the two most load-sensitive phases — removing either yields the mildest degradation of any
  variant, consistent with the existing profiler finding that lint is dominated by ~25 small, interpreter-startup-bound
  subprocess launches (the shape of work most hurt by OS scheduling delay under an oversubscribed host). Reconciled:
  tests dominate by absolute cost but are not disproportionately WORSENED by contention (mid-pack 1.56x multiplier);
  lint/typecheck are the phases that scale worst RELATIVELY. Added one new tracked follow-up todo (profiler run directly
  on planning-vm under load, for a load-drift-free confirmation) rather than leaving it as prose, per the
  findings-triage hard rule. Todo (line ~543, "[DOC] P2. Compare the two tables...") flipped `[x]`. No code change —
  doc-only (analysis of already-recorded data). — unified-trading-pm@(this commit)
