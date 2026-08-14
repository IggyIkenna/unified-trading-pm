---
doc_type: codex-ssot
title: Host-scoped shipping concurrency governance + commit-time Quickmerge provenance
summary: >-
  SSOT for the 2026-08-09 hardening of the shared-checkout shipping path: per-repo + host-wide concurrency caps on
  quality-gates.sh (qg-host-governor.sh's total-instance gate, now repo-aware), a separate host-wide concurrency cap on
  the docs fast path (push-host-governor.sh, safe-doc-push.sh), a true per-repo+branch push mutex for the actual git-
  remote critical section, and a commit-msg hook that catches a raw source commit missing the Quickmerge trailer at
  COMMIT time rather than only at push time. Root-caused a live, multi-hour shipping incident this doc documents in
  full.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, safe-doc-push, quality-gates, concurrency, git-discipline, host-governor, provenance]
related:
  [
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-09
authoritative_for:
  [QG host-concurrency governance, safe-doc-push.sh concurrency, commit-time Quickmerge provenance enforcement]
referenced_by: []
owner:
last_reviewed: 2026-08-12
code_refs:
  [
    scripts/quality-gates-base/qg-host-governor.sh,
    scripts/dev/push-host-governor.sh,
    scripts/quickmerge.sh,
    scripts/dev/safe-doc-push.sh,
    scripts/hooks/check-quickmerge-provenance.sh,
    scripts/cicd/check_strict_quickmerge.py,
    .pre-commit-config.yaml,
    scripts/pre-commit-templates/,
  ]
---

# Host-scoped shipping concurrency governance + commit-time Quickmerge provenance

## The incident this fixes

Live, 2026-08-09: a single 5-file `scripts/**` fix (portable `UV_VERSION` parsing + a new push governor) took dozens of
attempts and several hours to land on a shared dev-host checkout. Root causes, all independently confirmed:

1. **~24+ distinct AO-dispatched slot identities** committing/pulling/pushing on `unified-trading-pm`
   `live-defi-rollout` concurrently, with **zero cross-slot coordination** — each slot is a separate
   `git clone --reference` (see `/codex/05-infrastructure/per-tab-worktrees.md`), so a flock scoped to "this checkout's
   `.git` dir" (the pre-existing `_qm_locked_git_commit` / `locked_git_commit` per-checkout locks) provides zero
   protection against a DIFFERENT clone's concurrent commit/pull.
2. **`.git/index.lock` churn** from that same concurrent load — sampled continuously HELD for 60s straight at one point,
   with `lsof` confirming no live holder (a crashed/killed process's abandoned lock, not real contention) at least twice
   during the same incident.
3. **`git commit`/`git pull --rebase --autostash` racing prek's own stash-save/restore cycle** — a well-known,
   previously-documented class (`autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`,
   `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`) that this incident re-confirmed live multiple
   times: staged content silently reverting to match HEAD between one shell command and the next, with no error.
4. **A raw `git commit` retry-loop**, built mid-incident specifically to get UNSTUCK from (1)-(3), was ITSELF an
   instance of the exact problem section 3 below now closes: it bypassed `quickmerge.sh` entirely, so none of the
   governance in this doc applied to it.
5. A separate, pre-existing bug (`grep -oP` — a GNU/PCRE-only flag — silently killing `scripts/setup.sh` under `set -e`
   on macOS's BSD `grep`) made `quickmerge.sh` itself appear to hang/loop on this host for unrelated reasons,
   compounding the diagnosis. Fixed with `sed -E` (POSIX-portable) in `setup.sh` and
   `quality-gates-base/base-library.sh`.

## 1. QG concurrency is RESOURCE-based, not a fixed count (default since 2026-08-10)

**Read this before quoting any cap number.** `QG_GOVERNOR_MODE` defaults to `reservation`; the fixed-count caps that
used to be the whole of this section are now the LEGACY `token` path, reachable only by setting
`QG_GOVERNOR_MODE=token`. Quoting "PM ≤ 4, others ≤ 1, host ≤ 6" as current is wrong on any un-overridden host.

**How admission actually works.** `qg-host-governor.sh`'s `_qg_try_reserve` sweeps dead PIDs, reads the host-shared
ledger, decides and reserves — all under ONE flock, so N simultaneous acquirers serialize and can never over-admit. The
decision is `_qg_admit_check`, a pure function (every input explicit, so every branch is unit-testable), evaluated in
this order:

| Clause          | Condition                  | Decision                                             |
| --------------- | -------------------------- | ---------------------------------------------------- |
| host pressure   | `avail < 20% of MemTotal`  | `WAIT_HOST_PRESSURE` (catches non-QG load)           |
| oversize        | `this_peak > budget`       | `SOLO_ADMIT` if nothing running, else `SOLO_WAIT`    |
| RAM reservation | `reserved + this > budget` | `WAIT_RAM_RESERVATION` (the 6×UTL stacking cap)      |
| RAM live        | `avail < this + floor`     | `WAIT_RAM_LIVE` (external pressure + climb headroom) |
| CPU             | `running + 1 > slots`      | `WAIT_CPU`                                           |
| —               | else                       | `ADMIT`                                              |

- `this_peak` = **this repo's MEASURED peak RSS** from `scripts/dev/qg_resource_baseline.json` (`max(local, vm)`,
  conservative + host-portable). An unmeasured repo takes `QG_UNMEASURED_PEAK_MB` (default 5500 = treat as heaviest;
  never a low guess that would under-reserve).
- `budget` = `QG_MEM_SAFETY_FRAC` (0.70) × MemTotal · `slots` = `QG_CPU_FRAC` (0.80) × physical cores, min 1 · `floor` =
  max(MemTotal/10, 2048) MB.
- `QG_MEM_CAP` is set to 1.2 × the baseline peak as a per-run cgroup cap, so a run that outgrows its baseline is
  OOM-killed in its OWN scope rather than taking the host down.

The practical rule for an agent is unchanged and simpler than any number: **just invoke `quality-gates.sh` normally — it
queues.** Do not hand-tune concurrency, and never bulk-kill a peer's `pytest`/QG to make room.

Evidence behind the default flip (deferred six times by successive audits as "operator-aware, not an autonomous flip"):
Phase 3c cutover PM@6e818079a, Phase 4 abort-monitor + trap-release PM@aca6a2fcf, Phase 5 fleet rollout via
`bootstrap_vm.sh` AO@91808dfeb5, live on the orchestrator VM since 2026-07-22, a 93-minute soak (42 runs, maxconc=3, 0
OOM), cross-host tests at 16/24/61/96/128 GB, and independent re-verification 2026-08-10 (all 8 governor suites green; 6
simultaneous acquirers on one heavy repo admit exactly 3).

### 1a. The legacy `token` path (only when `QG_GOVERNOR_MODE=token`)

Composed two fixed caps, both still in the code as the fallback:

- **Per-repo sub-cap** (`QG_REPO_INSTANCE_CAP`): PM ≤ 4 concurrent QG runs host-wide; every OTHER (service) repo ≤ 1 —
  never two concurrent QG runs on the SAME service repo on one host, since those virtually always collide on the same
  git ref.
- **Host-wide flat cap** (`QG_TOTAL_INSTANCE_CAP`): `max(6, floor(physical_cores × 0.75))`. **6 is the FLOOR, not the
  value** — a 10-core Mac resolves to **7**, not 6; an 8-core host to 6. Quoting a flat "≤ 6" understates it on any host
  with more than 8 cores.
- **Heavy-phase token** (`QG_HOST_CONCURRENCY`): `K = max(2, floor(physical_cores / 4))` — 2 on a 10-core Mac.

Admission required BOTH caps to have room, checked together each cycle (never hold one while blocked on the other — that
would let a repo's own slot sit idle mid-wait, starving same-repo peers for no reason).

**Why the flip mattered on laptops.** Hosts already overridden to reservation (the AO VM, CI glue-runners — set durably
by `bootstrap_vm.sh`/`.env.local`) were unaffected. Un-bootstrapped operator laptops silently ran the fixed-K bucket:
measured K=2 on a 24 GB / 10-core Mac that the ledger admits **8** concurrent service-repo runs on — a 4× throughput
loss purely from an unset env var.

**Implementation trap already hit and fixed while building this**: the first version's acquire helper captured its
result via `$(...)` command substitution — which forks a subshell, and an `flock` held on an FD opened inside that
subshell is released the INSTANT the subshell exits (closing the FD), before the caller ever gets to use it. A
contention test (two processes on the same repo, cap=1) caught this immediately — the second process sailed through
instead of queueing. Fixed by inlining the `exec`+`flock` pair directly in the caller's own shell (no
command-substitution wrapper around the actual lock acquisition) — see `_qg_try_repo_token` / `_qg_try_global_token` in
`qg-host-governor.sh`. **Any future addition to this file must keep flock acquisition out of a `$()` capture.**

## 1b. PM is the fleet's single write hotspot — why the same gate livelocks in PM and not AO

Measured 2026-08-10 (`plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`,
F1):

| Quantity                                                 | Measured value                  | How                                                   |
| -------------------------------------------------------- | ------------------------------- | ----------------------------------------------------- |
| `run_hygiene_sweep.sh --precommit` on ONE staged file    | **118s** (loaded main checkout) | `time bash …/run_hygiene_sweep.sh --precommit <file>` |
| Same, IDLE isolated worktree (no concurrent hook chains) | **18.6s**                       | per-check timestamp profiling, same day               |
| `origin/live-defi-rollout` commits, preceding hour       | **60** (mean interval 60s)      | `git log --since='1 hour ago' --oneline origin/…`     |
| unified-trading-pm commits / 24h                         | **1318**                        | `git log --since='24 hours ago' --oneline origin/…`   |
| agent-orchestrator commits / 24h                         | **59** (22x fewer than PM)      | same                                                  |
| market-tick-data-service commits / 24h                   | **152**                         | same                                                  |

**Why PM and not AO.** It is not that AO is better engineered — the same scripts, the same hooks, and the same drift
gate run in both repos. PM is the fleet's single write hotspot BY DESIGN: every agent working in every repo commits its
plan-checkbox flips here (the Commit+Push+Flip HARD RULE, `/codex/12-agent-workflow/commit-push-flip-rule.md`), while a
code repo is normally written by one agent at a time. AO's own repo sees a commit roughly every 24 minutes — comfortably
longer than a hook run — so the hook chain never has to race a moving `origin` there. A fixed ~2-minute critical section
is safe at one commit per 24 minutes and structurally unsafe at one per 60 seconds: the 118s figure above is not an
intrinsic cost of the sweep (the idle-worktree 18.6s figure is), it is a **~6x contention inflation** from multiple
concurrent hook chains competing for the same host's CPU while PM's commit rate keeps origin moving under all of them at
once.

**Structural consequence**: the problem gets monotonically worse as fleet concurrency grows on PM specifically, and no
amount of per-run retry tuning fixes it — retries lengthen the critical section, which is the thing that has to shrink
or move out of PM's contended path. Two mitigations landed against this: `check-branch-drift.sh`'s
`DRIFT_GATE_ADVISORY=1` mode (a reconciling wrapper's own commit call WARNs on drift instead of hard-blocking, since the
wrapper's post-commit rebase enforces the same invariant afterwards for seconds instead of 118s) and
isolated-worktree-by-default in `safe-doc-push.sh` (each commit stages in a private throwaway worktree at `origin/HEAD`,
so the drift gate starts satisfied and prek's stash save/restore cycle never collides with a peer's foreign WIP). Both
are detailed in `/plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`; do
not re-derive throughput limits assuming AO's commit-rate profile applies to PM.

**Isolated venv cache refresh is guaranteed by `base-service.sh`, not by `quickmerge.sh`'s own provisioning check
(verified 2026-08-14, execution-service, 581-test suite).** `quickmerge.sh`'s `~/.cache/qm-iso-venv/<repo>` provisioning
is gated `if [ ! -x "$_qm_iso_venv/bin/python" ]` — first-run-only; it does NOT re-sync an already-populated cache. The
reason a stale cache never actually ships stale dependencies is a SEPARATE mechanism: `base-service.sh` runs
`UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --quiet` unconditionally on every QG invocation (the isolated worktree's
`.venv` is a symlink into the cache), which reconciles the cache to whatever lock file is present in the tree it runs
against — confirmed directly (bumped a package via `uv lock --upgrade-package`, re-ran the sync against the same cache
dir, installed version moved to match; reverted and re-confirmed). Don't reason about cache freshness from quickmerge's
provisioning check alone — the refresh guarantee lives in the QG step that runs after it.

## 2. `safe-doc-push.sh`'s own concurrency budget

`push-host-governor.sh`'s `push_gov_acquire_validate` (K=8 default, `PUSH_GOV_VALIDATE_CONCURRENCY` override) now
brackets `safe-doc-push.sh`'s ENTIRE run (acquired near the top of the script, released after the retry loop) — not just
the commit-hook-chain call the way `quickmerge.sh`'s own (narrower, unchanged) use of this same function still does.
This is a SEPARATE, independent budget from the QG caps in section 1 — the docs fast path is deliberately lighter-weight
(no heavy tests) so it tolerates more real concurrency, and it must never compete with quality-gates' budget for the
same tokens.

## 3. Never commit/push behind remote

Both `quickmerge.sh` (STAGE 0.4, `PRECOMMIT_WORKING_TREE_CONFLICT` / `AUTOSTASH_POP_CONFLICT` / etc. structured codes)
and `safe-doc-push.sh` (its own fetch → reconcile → commit → push retry loop) fetch and reconcile against origin BEFORE
every commit attempt, and hard-fail (`QUICKMERGE_BLOCKED ...` / a non-zero exit with a printed recovery line) rather
than silently proceeding when a genuine unresolvable conflict is hit. **HARD RULE: an agent must never work around one
of these structured failures by dropping to a raw, unscoped `git commit`/ `git push` — that bypasses every governance
mechanism in this doc**, including section 4 below (which now catches exactly that bypass at commit time).

### 3a. `ahead=0` and a clean tree do NOT mean your work landed

Both states are equally consistent with the work having been **destroyed**. Four measured instances on 2026-08-10, on
one host in about an hour (SSOT:
`/plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`, finding F8):

1. A staged, passing comment edit was dropped by quickmerge's reconcile — the run reported SUCCESS and pushed the OTHER
   named files; the edit survived in neither worktree nor HEAD.
2. A scoped `--files` run pushed a commit containing NEITHER named file — only a peer's untracked test file — while both
   named files stayed dirty on disk. Post-push ancestry verified. Exit 0.
3. A todo written and pushed; afterwards CLEAN with `ahead=0`, present in neither worktree nor HEAD, unrecoverable from
   any of four live stashes.
4. The same todo again: `safe-doc-push.sh` exited **0** reporting
   `✅ Named files already match HEAD (a concurrent session landed identical content)`. It had not landed — the edit was
   reverted BEFORE the script hashed the file, so "matches HEAD" was true for the opposite reason to the one reported.

**Two distinct failure modes, only one of which any revert-detection can see.** "Your file was reverted on disk" is
detectable by fingerprinting at entry. "Your file never got committed" leaves the worktree untouched, so a fingerprint
check passes and the run reports success. Instance 2 is the second shape; it is invisible by construction to every check
that looks only at the working tree.

**What the ship scripts now assert** (`_qm_assert_entry_change_landed` / `_sdp_certify_success`): record HEAD's blob per
named path AT ENTRY; after the push, any path that had a real diff at entry whose HEAD blob is STILL the entry one
carries none of your work.

- Deliberately NOT "HEAD must equal your entry blob": the prek hook chain rewrites files legitimately (prosewrap,
  prettier, autofixers), so a landed change routinely differs from what you handed over. "Still identical to the PRE-RUN
  HEAD" is the precise statement of "nothing of yours landed", and is immune to that.
- Exit codes: **quickmerge 10** · **safe-doc-push 12** (every named file was already identical to HEAD at entry, so the
  run had nothing of yours to ship and cannot certify what is in HEAD is what you intended — `SDP_ALLOW_NOOP=1` accepts
  it as a deliberate idempotent re-run) · **safe-doc-push 13** (push landed, your change absent). All mean RECOVER from
  the printed ref, never a plain re-run.
- Instance 4's shape is the reason 12 exists as a refusal rather than a smarter heuristic: "a peer landed your content"
  and "your content was destroyed" are indistinguishable from inside the process, so it resolves to neither and prints
  the `git log -1 -- <path>` command that tells them apart. A heuristic that can be wrong in the destructive direction
  is what produced the incident.

**Agent-side rules that follow from this**: verify content is in HEAD (`git show HEAD:<file>`), never that the tree is
clean; and Write + `git add` in ONE step on a shared checkout — every one of the four losses happened in the window
between writing the file and staging it. `_qm_unstage_foreign_paths` (@bde0cc4a) does NOT cover this class: it stops
FOREIGN work being committed under your message, not YOUR work being reverted. Separate failure modes.

Regression tests: `tests/test_quickmerge_landed_content_assertion.bats`,
`tests/test_safe_doc_push_landed_content_certification.bats`.

## 4. Commit-time Quickmerge provenance (new — catches what push-time enforcement misses)

`check_strict_quickmerge.py` has long enforced, at PRE-PUSH time, that any commit touching a SOURCE file
(`.py`/`.ts`/`.tsx`, outside `scripts/`/`tests/`/`test/`/`.github/` — see its `SOURCE_EXT`/`NONSOURCE_DIR`) must carry a
`Quickmerge:` trailer (added by `quickmerge.sh`'s own commit call) or be a merge/bot/carve-out-only commit. The gap: a
raw local `git commit` bypassing `quickmerge.sh` was invisible to this until PUSH time — long enough to sit in a shared
checkout racing every other concurrent session's pulls/rebases/autostashes (see the incident above, cause 4).

**`scripts/hooks/check-quickmerge-provenance.sh`** closes this — a NEW `commit-msg`-stage local hook (installed via
`.pre-commit-config.yaml` and all three `scripts/pre-commit-templates/*.yaml` — docs, python-service, python-library)
that runs the identical carve-out logic at commit time: reads the about-to-be-created commit message (git passes its
file path as `$1` for a `commit-msg` hook), checks staged files against the same `SOURCE_EXT`/`NONSOURCE_DIR` shape
(duplicated by hand from `check_strict_quickmerge.py`, kept in sync via cross-reference comment in both files — a bash
hook and a Python CLI can't share an import), and exits 0 with a printed warning (not a failure) if a source file is
staged with no `Quickmerge:` trailer present.

**Rollout is WARN-only by default**, mirroring `check_strict_quickmerge.py`'s own `STRICT_QUICKMERGE_BLOCK` precedent
exactly (land unblocking, observe real fleet traffic for false positives, THEN flip to enforcing — never ship a new
fleet-wide commit-blocking gate pre-armed). Override to enforce: `QUICKMERGE_PROVENANCE_BLOCK=1`.

**Known gap**: husky-managed JS/TS repos (`deployment-ui`, `unified-trading-system-ui`) don't run prek at all — their
pre-push guard is a committed `.husky/pre-push` delegate file, not this hook chain, so this new commit-msg check does
not currently reach them. A husky-side equivalent is tracked as future work, not yet built.

## 5. Parallel sub-agents parallelise AUTHORING ONLY — gating and shipping stay SERIAL

**Scope: laptop multi-agent fan-out only** (an interactive Ikenna/Harsh session spawning `Task` sub-agents). AO never
fans out this way — it dispatches per-repo workers serially — so this section is a local-session design rule, not an
orchestrator one.

Measured 2026-08-10, a 6-agent fan-out across 6 repos: every agent authored its change successfully and in parallel;
**every downstream step then serialised anyway**, and two of the three ship failures were _caused_ by the parallelism.
Four structural reasons, none of which file-level partitioning prevents:

1. **The QG governor caps concurrent gates at 2 HOST-WIDE**, shared with every peer slot on the machine. Launching a
   second gate while your own ship is queued starves your own merge — measured: a `quickmerge` re-gate queued **810s**
   behind its own session's other gate plus 4 peer-slot gates. More concurrency here is strictly negative.
2. **The ship gate is TREE-WIDE, not file-scoped.** `quickmerge` re-gates the whole repo, so a peer agent's concurrent
   edits fail _your_ merge. Partitioning by file prevents edit collisions but NOT **ratchet** collisions: three agents
   each added ~100-180 lines to different files, none individually alarming, and collectively broke the repo's file-size
   ratchet (853→998, 926→1008, 891→992 against a 960 cap) — a class of failure that is invisible to every agent locally
   and only appears at the tree-wide gate.
3. **Dependency repos cannot be edited concurrently with their dependents.** `quickmerge`'s pre-flight refuses to ship
   any repo whose path-dependencies are dirty (`❌ <dep>: HAS UNCOMMITTED CHANGES`), and a dependency mid-refactor
   _transiently breaks its dependents' imports_ (observed: UTL's `_state.py` split made `deployment-service` un-
   importable for minutes). So `unified-trading-library`/`unified-api-contracts` must reach a clean, shipped state
   BEFORE any service repo can gate or ship.
4. **Sub-agents structurally cannot self-verify.** Because of (1) they must be told to run targeted tests only, so the
   codex-compliance checks that run ONLY in the full gate (file-size ratchet, banned-token scan, hardcoded-project-id)
   are invisible to them. Every such violation surfaces at the parent's gate, after the fact.

**Fan-out width is capped at 5, not 10 (operator ruling 2026-08-10).** The cap is per-SLOT but the constraint is
per-HOST: ~4 slots share one operator laptop (~10 physical cores), so a 10-wide fan-out in each slot is up to 40
concurrent agents on 10 cores. 5 keeps the worst case to ~20 — still oversubscribed, deliberately, because agents are
mostly I/O-blocked on tool calls rather than CPU-bound, but within a factor the box can absorb.

Sizing intuition for the gate queue behind them — the governor's own limit is DERIVED, not fixed
(`scripts/quality-gates-base/qg-host-governor.sh`):

- `K = max(2, floor(physical_cores / 4))`, overridable via `QG_HOST_CONCURRENCY`.
- Detection order is `lscpu -p=core` (Linux physical) → `sysctl -n hw.physicalcpu` (macOS physical) → `nproc` (logical)
  → 4. **The macOS branch was ADDED 2026-08-10**: before it, `lscpu` AND `nproc` are both absent on macOS, so `cores`
  fell through to the hardcoded 4 → `floor(4/4)=1` → min-2 floor → **K=2 on every Mac regardless of size**. It went
  unnoticed because a 10-physical-core operator laptop lands on `floor(10/4)=2` anyway — the same answer — but a 24-core
  Mac Studio was silently capped at 2 instead of 6. Note `hw.physicalcpu`, NOT `hw.ncpu`/`hw.logicalcpu`, which
  over-count on SMT Intel Macs.
- **`K` is the TOKEN-mode cap, and token mode is no longer the default.** `QG_GOVERNOR_MODE` was flipped
  `token → reservation` fleet-wide on 2026-08-10, so `K` now serves only as a runaway backstop; real admission is the
  RAM/CPU reservation ledger (§ above). Under reservation the same 24 GB/10-core laptop admits **8 concurrent
  service-repo gates** (RAM budget 17.2 GB, CPU slots 8), not 2. An earlier revision of this section claimed a laptop
  "grants 2 gate slots no matter what" — that was true only of token mode, and only of un-bootstrapped hosts, which is
  precisely the condition the flip removed. Do not re-derive throughput limits from `K` without first checking
  `qg-host-governor.sh --status` for the live `MODE=`.
- On **Linux** (the AO VM) `lscpu` resolves, so it gets its real `floor(cores/4)` (e.g. 24-core → 6).
- Separately `QG_TOTAL_INSTANCE_CAP` (total-instance gate) defaults to `floor(cores × 0.75)`, floored at 6.

**The shape that works**: fan out authoring → collect ALL agents → ship dependency repos FIRST → then ONE full gate per
dependent repo (QG-sweep batching: gate once over the combined tree, then per-unit commits) → ship serially. Never run
two gates concurrently yourself, and never bulk-kill a peer slot's gate to free a token (banned) — patience is the
sanctioned response to contention.

**Corollary for fix shape**: when a cap breach is the blocker, fix it by EXTRACTION along a real seam, never by
compressing logic or deleting docstrings. The 2026-08-10 batch produced four genuinely better modules that way
(`_durable_state.py`, `_preemption_signal.py`, `_captured_reader.py`, `_classify.py`). Extraction has one recurring
second-order cost to check: a moved function takes its imports with it, so any test that monkeypatched
`<old_module>.<symbol>` must be repointed at the new module.

## Operator/agent takeaways

- Don't hand-roll a raw `git commit`/`git push` retry loop to escape contention on a shared checkout — that bypasses
  every gate in this doc. If `quickmerge.sh`/`safe-doc-push.sh` themselves are stuck on host contention, the fix is
  patience (both have their own bounded, backed-off retry logic) or an isolated `git worktree` (shares the same object
  database, so a commit made there is immediately valid from the main checkout too — see this doc's own shipping
  incident for the exact recovery sequence used).
- A stale `.git/index.lock` (confirmed via `lsof <path>` showing NO holder) is safe to remove — it is an abandoned
  marker from a crashed process, not live work; removing it is infrastructure hygiene, not a destructive operation on
  anyone's WIP.
- `QUICKMERGE_PROVENANCE_BLOCK=1` and `QG_REPO_INSTANCE_CAP`/`QG_TOTAL_INSTANCE_CAP`/ `PUSH_GOV_VALIDATE_CONCURRENCY`
  are operator-facing tuning knobs, not agent-facing overrides — an agent hitting a WARN from the new hook should switch
  to the sanctioned ship path, not adjust the env var to silence it.
