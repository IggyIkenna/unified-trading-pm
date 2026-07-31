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
`/plans/active/ao_fleet_observability_kpis_2026_07_20.md` + a scratch
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

## Phase 1 — this host baseline

**Results table (this host, single agent, idle otherwise):**

| Run                                                     | Wall-clock (`real`)                                        | Notes                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full default, actionlint hanging (pre-fix)              | never finished (killed at 52+ min)                         | root cause: no `subprocess` timeout on actionlint                                                                                                                                                                                                                                                                                                                             |
| Full default, coarse 20s-timeout fix                    | ~69.9s (real 1m9.941s)                                     | still hit the timeout every run; exits 1 at TESTS (6 pre-existing failures, unrelated — see below)                                                                                                                                                                                                                                                                            |
| Full default, per-file actionlint fix, pre-extraction   | 61.3s (real 1m1.263s)                                      | exits 1 at TESTS phase (same 6 unrelated failures)                                                                                                                                                                                                                                                                                                                            |
| Full default, **root-cause fix (script extracted)**     | **50.8s (real 0m50.794s)**                                 | exits 1 at TESTS phase (same 6 unrelated failures) — current best full-default number                                                                                                                                                                                                                                                                                         |
| `check_workflow_yaml_valid.py` alone, root-cause fixed  | ~2.0s (59 per-file actionlint calls, no stalls)            | was: indefinite hang → 20.5s (coarse fix) → 7.2s (per-file fix, 1 stall+retry) → now no stall at all                                                                                                                                                                                                                                                                          |
| `--skip-tests` (env→lint→typecheck→codex→version-align) | **64.2s (real 1m4.207s), exit 0**                          | full green — first run to reach every phase; base-image digest drift WARN only (non-blocking, pre-existing)                                                                                                                                                                                                                                                                   |
| `quickmerge.sh` (real run, `--agent --files`)           | **84.8s (real 1m24.824s) through Stage 3, then hard FAIL** | Stage 0→1→1.5→2 all passed; Stage 3 re-gate hit the same pre-existing test failures (tracked issue, see below) — Stage 4 (act sim) / Stage 5 (PR) never ran, unmeasured                                                                                                                                                                                                       |
| `--quick`                                               | **30.7s (real 0m30.694s), exit 1**                         | skips version-alignment/merge-sentinel + runs a lighter test subset (1555 vs 1571 tests) — same 6 pre-existing failures                                                                                                                                                                                                                                                       |
| `--fast`                                                | 49.0s (real 0m48.982s), exit 1                             | change-scoped codex-grep tier — does NOT skip tests; hit the same 6 pre-existing failures, 1571 tests still ran                                                                                                                                                                                                                                                               |
| `--lint`                                                | 96.5s (real 1m36.464s), exit 0                             | lint-only (tests genuinely skipped, no FAILED lines) — but slower than `--skip-tests`'s 64.2s despite doing less; a slot-1 `quality-gates.sh` process was independently running concurrently on this host during this specific run (confirmed via `ps`, different `.tabs/1` checkout) — likely CPU-contended, not representative of an idle-host number; worth a clean re-run |
| `--test`                                                | 49.1s (real 0m49.118s), exit 1                             | test-only (skips lint) — same 6 pre-existing failures, full 1571-test count                                                                                                                                                                                                                                                                                                   |
| `--skip-lint`                                           | 52.5s (real 0m52.537s), exit 1                             | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-typecheck`                                      | 49.2s (real 0m49.220s), exit 1                             | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-codex`                                          | 48.9s (real 0m48.931s), exit 1                             | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |
| `--skip-version-alignment`                              | 46.7s (real 0m46.681s), exit 1                             | same 6 pre-existing failures                                                                                                                                                                                                                                                                                                                                                  |

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

- [x] 1. ✅ [INFRA] P1. Time a full default `bash scripts/quality-gates.sh` run (no flags → implicit `--no-fix`) on
      unified-trading-pm; record wall-clock total. Done: see results table above — 50.8s post-root-cause-fix (exits 1 at
      TESTS due to 6 pre-existing unrelated failures; env/lint/tests phases only). — unified-trading-pm@(uncommitted,
      slot-2 working tree)
- [x] 2. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --skip-tests` to get past the pre-existing unrelated test
      failures and record typecheck / codex-compliance / version-alignment phase timing. Done: 64.2s, exit 0, full green
      — see results table above.
- [x] 3. ⚠️ [INFRA] P1. Time `bash scripts/quickmerge.sh "<real fix message>" --agent --files '<the real fix files>'`.
      Done (partially): Stage 0→3 timed at 84.8s before a hard FAIL — blocked on the pre-existing, already-tracked
      `cve_affected_pinned_deps_remediation_2026_06_18.md` test breakage (unrelated to this plan), so Stage 4 (act
      simulation) / Stage 5 (PR creation) remain unmeasured. Real fixes intentionally left as local uncommitted changes
      — re-run this todo once that CVE issue clears to get the remaining stages + an actual ship.
      BLOCKED-UPSTREAM-OUTAGE on `cve_affected_pinned_deps_remediation_2026_06_18.md` for full completion.
- [ ] [INFRA] P1. BLOCKED-UPSTREAM-OUTAGE (same `cve_affected_pinned_deps_remediation_2026_06_18.md` gate as todo 3
      above). Investigate + measure the `_QG_DOCS_ONLY` auto-detection in
      `scripts/quality-gates-base/base-     service.sh`/`base-library.sh`/`base-ui.sh` (operator-flagged 2026-07-31;
      code-cited: triggers when `git diff HEAD` + `git diff --cached` + untracked files are ALL
      `.md/.mdc/.rst/.txt/.svg/.png/.jpe?g/.gif/.ico` — notably **not** `.yaml`/`.yml` — and skips
      `RUN_TESTS`/`SKIP_TYPECHECK`/codex-code-body while lint/format + doc-validators still run; server v2 always runs
      the full gate since a committed PR has no working-tree diff). Retry the isolated timing measurement AFTER the
      quickmerge todo above lands (so the tree is clean-and-fixed at rest, not mid-stash) — single-file `.md`-only edit,
      run default `quality-gates.sh`, confirm the "DOCS-ONLY changeset" log line fires, record wall-clock, revert.
      Done-when: a doc-only-changeset timing number is in the results table alongside the flag-based numbers.
- [x] 4. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --quick`. Done: 30.7s, exit 1 — see results table above.
- [x] 5. ✅ [INFRA] P1. Time `bash scripts/quality-gates.sh --fast`. Done: 49.0s, exit 1 — see results table above.
- [x] 6. ✅ [INFRA] P1. Time each single-phase scope flag separately: `--lint`, `--test`, `--skip-lint`,
      `--skip-typecheck`, `--skip-codex`, `--skip-version-alignment`. Done: all 6 recorded in results table above
      (batched sequentially, one combined background run). Important caveat also recorded: 4 of the 6 don't reach the
      phase they nominally skip because TESTS fails first — see the results-table nuance note.
- [x] 7. ✅ [DOC] P2. Revert the transient test-trigger edits. Done: `git checkout --` the HTML-comment marker in
      `plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md`; moved the scratch
      `plans/audit/results/qg_timing_test_2026_07_31.yaml` out of the repo. `git status` now shows exactly 4 pending
      items: the 2 real-fix modified files, the new `scripts/cicd/ldr_to_main_fleet_promote.sh`, and this plan doc —
      nothing else.

**Phase 1 status**: every todo done or explicitly blocked on the same external, already-tracked, non-this-plan issue
(`cve_affected_pinned_deps_remediation_2026_06_18.md`). Remaining before this plan can fully close: (a) that CVE issue
clears → re-run quickmerge for real stage 4/5 numbers + an actual ship, (b) the docs-only isolated timing retest (same
blocker), (c) Phase 2 (planning-vm) needs an operator decision on how to reach that VM.

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
