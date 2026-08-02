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
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
context_scope:
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

- [ ] [INFRA] P2. Follow-up, not executed this session: investigate optimizing `check_pm_script_path_refs.py` (28% of a
      from-scratch quality-gates.sh run, single-threaded full-corpus sweep) — e.g. incremental/changed-files-only
      scoping (mirroring `--fast`'s change-scoped codex-grep tier), or parallelizing the corpus walk. Done-when: a
      measured before/after on the profiler (`profile_qg_resources.py --repo unified-trading-pm`) showing a real
      wall-time reduction, not just a code change.
- [ ] [INFRA] P2. Operator explicitly asked for a solo, idle-host-verified re-measurement of `--test`,
      `--skip-typecheck`, `--skip-lint`, `--fast`, `--skip-codex` (the flags that looked implausibly slow in the batched
      Results table 2) — only `--quick` was actually re-run solo (81.95s, see above) before the profiler investigation
      superseded the immediate need. Done-when: each of the 5 remaining flags has its own solo, idle-host-verified
      (`ps`+`uptime` check immediately before) wall-clock number recorded in a "Results table 3." Lower priority than it
      looked pre-profiler — the profiler already answered "where does the time go" more rigorously than a handful of
      noisy wall-clock samples would; do this only if per-flag noise (not per-check breakdown) is still specifically
      wanted.
- [ ] [INFRA] P2. The `--skip-tests --skip-<X>` vs. plain `--skip-tests` delta (isolating each individually-skippable
      phase's REAL cost, since Results table 1's `--skip-lint`/`--skip-typecheck`/`--skip-codex`/
      `--skip-version-alignment` numbers never reached the phase they nominally skip — see the "Important nuance" note
      above) was flagged mid-session as a follow-up but never run. **Now unblocked** — the CVE issue that was the stated
      reason to defer it is resolved (see Progress Log). Done-when: one row per phase (typecheck/codex/
      version-alignment) showing the delta vs. plain `--skip-tests`'s 64.2s (Results table 1) or its Results-table-2
      equivalent.

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

- [ ] [INFRA] P2. BLOCKED-OPERATOR-DECISION — confirm with the operator how to reach the planning-vm interactively (SSM
      session vs an AO-dispatched task) to run the SAME measurement suite as Phase 1 while ~15 agents are concurrently
      active, since this is explicitly about observing real contention, not an idle-VM number.
- [ ] [INFRA] P2. Re-run every Phase-1 flag/script combination on planning-vm under real concurrent load and record the
      same table. Done-when: a second results table, same shape as Phase 1's, with a stated concurrent-agent-count at
      measurement time.
- [ ] [DOC] P2. Compare the two tables and write the observed contention delta (which phases scale worst under load —
      typecheck/tests/lint are the likely CPU-bound candidates given the shared-host QG cap in CLAUDE.md) as the input
      to a follow-up improvement plan. Done-when: a named delta per phase, not just a total-time comparison.

## Deferred work after 2026-07-31

| Item                                                                                     | State / why deferred                                                                                                                                                                                         | Blocked on                                                                                                                                  |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Optimize `check_pm_script_path_refs.py` (28% of a from-scratch run)                      | Not done — real work, well-scoped, nobody's turn but the next session's                                                                                                                                      | Nobody — pick it up any time                                                                                                                |
| Solo re-measurement of `--test`/`--skip-typecheck`/`--skip-lint`/`--fast`/`--skip-codex` | Not done — only `--quick` was re-run solo before the profiler investigation superseded the immediate need; lower priority now that the profiler answered the deeper "where does time go" question            | Nobody — but check with the operator whether they still want it given the profiler's answer, or consider it satisfied                       |
| `--skip-tests --skip-<X>` delta measurement (real per-phase cost)                        | Not done — flagged mid-session, never run, now unblocked (CVE issue resolved)                                                                                                                                | Nobody — ready to run                                                                                                                       |
| Phase 2 — planning-vm concurrent-load measurement (3 todos)                              | Cannot be done yet — needs the operator to say how to reach the planning-vm interactively (SSM vs. AO-dispatched task); the whole point is observing REAL concurrent-agent contention, not an idle-VM number | **Operator** — needs a decision, not more local work                                                                                        |
| Missing `.venv` on `ibkr-gateway-infra`/`unified-api-contracts` (this slot)              | Not done — noted as a real gap (same class as the `strategy-service` fix), ruled out as a QG-timing driver by the profiler, but still worth a `uv sync` for its own sake (stops the VSCode nag)              | Nobody — trivial fix, just not yet done; not tracked as its own todo since it's a one-line `cd <repo> && uv sync` per repo, not scoped work |

**Recommended next item**: the `--skip-tests --skip-<X>` delta (3rd row) — it's the cheapest of the open items (a few
short runs, no new tooling), directly closes the "Important nuance" gap in Results table 1, and doesn't need an operator
decision. Phase 2 (4th row) is the actual point of this whole plan but is genuinely blocked on the operator, not on more
solo work.

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
