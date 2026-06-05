---
title:
  QG commit-quality-boundary + slot FF-push to LDR (aggregation of uv-determinism + governor-macOS-fix + commit-gate
  design)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-03
locked_by: live-defi-rollout
related_plans:
  - plans/active/uv_lockfile_determinism_2026_06_02.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
source:
  - operator design discussion 2026-06-02/03 (slot tab/ikennaigboaka/4)
  - plans/active/uv_lockfile_determinism_2026_06_02.md (parent effort, shipped)
---

# QG commit-quality-boundary + slot FF-push to LDR

> Aggregates the 2026-06-02/03 session: the shipped uv.lock-determinism + QG-host-governor-macOS-fix work, the discovery
> it produced, and the design decisions that follow — then aligns the canonical rule/flow docs. **doc → plan → code**:
> this plan enumerates the doc/rule/codex edits so they're reviewable before they ship.

## Shipped this session (on LDR — evidence)

All on `origin/live-defi-rollout`; full detail in
[uv_lockfile_determinism_2026_06_02.md](uv_lockfile_determinism_2026_06_02.md).

- [x] [INFRA] uv.lock determinism Phases 1–5 — read-only QG verifier (`uv lock --check`, not mutating `uv lock`), pin
      `uv==0.10.8` at all install sites (setup.sh, base-service/library bootstraps, CI workflow, UTL Dockerfile),
      ratchet verifier to blocking-on-pinned-uv, codex 3-role model (writer=quickmerge / verifier=QG / determinism=pin).
- [x] [INFRA] **QG host-governor macOS fix** — `qg-host-governor.sh` used bash≥4.1 `exec {fd}>`; macOS bash 3.2 parsed
      it as a command and CRASHED `quality-gates.sh` at stage [2] (no sentinel → quickmerge blocked from any Mac slot).
      Fixed: degrade to ungoverned on bash <4.1 (acquire + `--status`). **This unblocks local QG on every Mac slot.**
- [x] [INFRA] PM codex empty-fallback excludes + `.code-workspace`/manifest drift fix (greeks/fund-admin
      `future`→`scaffolded`). PM QG fully green (exit 0, all 6 stages + drift guard).
- [x] [DEPS] Re-lock-all sweep: **13/14** stale repos re-locked to LDR (uv 0.10.8, 0 resolved-version moves); UTL
      pinned. (`unified-trading-api` re-lock = 1 straggler, see below.)
- [x] [INFRA] Slot-branch reconciliation: 16 touched slot branches brought current with LDR (14 → 0↑/0↓; PM + uta →
      1↑/0↓).

## Key discovery (cross-cuts cicd_contract_hardening Phase 6)

- [ ] [SCRIPT] P1. **Self-counting `until ≤1 pgrep 'bash scripts/quality-gates.sh'` drain-gate DEADLOCKS fleet-wide
      (slot-6 discovery 2026-06-03).** The common ad-hoc shared-host QG drain-gate
      (`until [ "$(pgrep -f 'bash scripts/quality-gates.sh' | wc -l)" -le 1 ]; do sleep; done; bash scripts/quality-gates.sh ...`)
      is self-defeating: the WAITER's own command line contains the literal `bash scripts/quality-gates.sh`, so
      `pgrep     -f` counts every slot's waiter (including itself). With N slots each spinning a waiter, the count is
      always ≥N → never ≤1 → **all slots spin forever, zero QGs run** (observed: ~10 "QG" procs host-wide, memory 34%
      free = they were spinning waiters, not real load; the whole fleet's shipping stalled). FIX: the drain-gate MUST
      gate on a signal that excludes waiters — gate on **memory pressure** (run if free >~20%) and/or count only ACTUAL
      executions via a marker the waiter doesn't share (e.g. `pgrep -f 'quality-gates.sh --no-fix'` won't help since the
      waiter has it too; use a lock-file/`flock` or a tmpdir token, OR gate on `pytest`/`basedpyright` proc count). Make
      it a shared helper (`scripts/dev/qg-host-gate.sh`) so slots stop hand-rolling the broken pattern. Cross-cuts the
      "≤1-2 full QGs host-wide" QG-sweep rule — the rule is right, the ad-hoc IMPLEMENTATION is the bug. Repo:
      unified-trading-pm (helper) + the QG-sweep SSOT note. parent: this plan.

- [ ] [INFRA] P1. **The governor bash-3.2 crash had been MASKING pre-existing per-repo QG debt workspace-wide** — every
      macOS `quality-gates.sh` died at stage [2], so no repo's stage-5+ failures (codex baselines, cloudbuild-schema,
      size/import) were visible locally. Fixing the governor makes local QG run fully and **surfaces** that debt
      (observed: PM 3 issues cleared; UTL within-baseline; trading-agent-service STEP-5.17 cloudbuild-schema FAILS).
      **This is the same per-repo-debt that
      [cicd_contract_hardening_2026_06_01.md](cicd_contract_hardening_2026_06_01.md) Phase 6 greens** — that plan
      attributed surfacing to the v2 rollout; the governor crash was a second masking layer on the _local_ gate
      specifically. Cross-link, don't duplicate: the debt-greening lives in cicd Phase 6; this plan owns the
      governor-fix that exposed it. **DEFERRED to the cicd Phase-6 per-repo sweep.**

- [ ] [SCRIPT] P2. **QG sentinels not gitignored fleet-wide → per-QG-run drift (TWO failure modes)** —
      `.qg_last_passed_sha` (and `.qg_content_sentinel`) are local caches written by `quality-gates.sh`. (a)
      **untracked** in most repos → reappear as `??` after every QG run; (b) **already committed/tracked** in some repos
      (found: `agent-orchestrator`, `unified-api-contracts` — a machine-specific HEAD SHA was committed) → **gitignore
      alone does NOTHING, needs `git rm --cached`**. Both re-dirty slot trees + jam `slot-cron-ff-pull.sh` (observed:
      alerting-service, 2026-06-03). Fix: add both patterns to the **canonical `.gitignore` template**
      (`scripts/templates/`, the workspace SSOT) + roll out to all repos; AND for each repo run
      `git ls-files | grep -E 'qg_last_passed_sha|qg_content_sentinel'` → `git rm --cached` any tracked instance. **Done
      this session (slot branches)**: `alerting-service` (gitignore — was untracked), `agent-orchestrator` +
      `unified-api-contracts` (`rm --cached` + gitignore — were tracked); **`unified-trading-pm` `.qg_content_sentinel`
      gitignored (local, PM@7b6a46b48, 2026-06-03)** — alongside the already-present `/.qg_last_passed_sha`. **STILL
      PENDING**: the canonical `.gitignore` template (`scripts/propagation/templates/gitignore-python.txt` — verified
      2026-06-03 it carries NEITHER sentinel) + roll-out to the remaining ~22 service repos. Repo: unified-trading-pm
      (template) + remaining ~22 service repos. Provenance: alerting drift triage + slot-4 PM dirty-tree audit this
      session.

## Design decisions (this session)

1. **Commit = the per-repo quality boundary.** A commit may only be made from a `quality-gates.sh`-green tree (lint +
   codex + unit + types), so any committed work is already per-repo-validated. Today this holds for the quickmerge path
   (Pass-1 QG → Pass-2 quickmerge commits) but NOT for direct `git commit` (Commit+Push+Flip), which only gets the light
   prek hook (ruff/format/gitleaks/conventional-commit). Decision: unify — **all** commits require full-QG-green first,
   leaning on the existing **QG-sweep batching** rule so it isn't per-commit-expensive.
2. **Staging/SIT stays the cross-repo integration gate** (unchanged). The commit-gate covers per-repo correctness only;
   a locally-green commit can still break a downstream repo — that's what staging/SIT catches. Layering preserved.
3. **FF-push to LDR = NARROW LAST-RESORT, not a routine path (operator framing 2026-06-03).** Primary stays: agents
   **quickmerge** finished units → staging PR (gated); for substantial work, always a PR. The **alert→auto-PR /
   auto-merge / promotion automation is already substantially built** in PM `.github/workflows/`:
   `ldr-to-staging-promote.yml` (Tier C — drains committed-LDR → staging), `ci-failure-watcher.yml` (stuck-PR poller +
   alerts, cron `*/15`), `escalate-to-orchestrator.yml` + `conflict-resolution-agent.yml` (auto-triage/resolve),
   `auto-merge-minor-fixes.yml`, `main-backmerge-to-ldr.yml`. The cron FF-push fills only the remaining gap — a
   **QG-green** commit an agent made but didn't quickmerge, sat clean >1h → FF-push to LDR, where the **existing Tier C
   bot then promotes it to staging** (still gated). So the HARD-RULE carve-out is NARROW (last-resort drain of QG-green
   stranded commits), **not** a routine direct-push loosening — only ahead-only/clean/aged, FF-only (lossless). Still
   NEEDS-RATIFICATION for the carve-out wording, but small blast radius. The auto-PR automation's remaining wiring is
   owned by cicd_contract_hardening (escalate @127/929, auto-merge @1138) — cross-link, don't duplicate.

## Action items — doc/rule/codex alignment (precise edits)

### Reconcile the QG-timing inconsistency (commit-prereq) — SAFE (tightening; fixes existing drift)

- [x] ✅ [DOC] P1. **DONE — unified-trading-pm@5dbe60407.** `cursor-configs/CLAUDE.md` "Quality gates BEFORE quickmerge"
      → reframed "Quality gates BEFORE **COMMIT** — the commit IS the per-repo quality boundary"; scoped to code commits
      (doc/plan-flip/markdown take prek only); realized via QG-sweep batching (per-batch not per-commit). Also
      reconciled the "Quality Gates Are A Merge Prerequisite" block → "Commit + Merge Prerequisite".
- [x] ✅ [DOC] P1. **DONE — @5dbe60407.** `codex/08-workflows/ci-cd-flow.md` § "Two-Pass Workflow Model" blockquote
      reframed (QG before commit, not just quickmerge; commit = per-repo quality boundary; QG-sweep batching; doc-commit
      scope carve-out).
- [x] ✅ [DOC] P2. **DONE — unified-trading-pm@7c3643236.** Added the commit-as-quality-boundary framing to
      `SUB_AGENT_MANDATORY_RULES.md` Pass-1 bullet (binds every code commit incl direct Commit+Push+Flip, not just the
      quickmerge ship; prek=LIGHT gate / full QG=commit-prereq; QG-sweep batching; doc/plan-flip/markdown commits take
      prek only). Applied AFTER the concurrent plan-hygiene session finished + committed (`f98182875` — its
      `check_claude_subagent_parity.sh` CLAUDE↔SUB_AGENT drift check now landed), so no collision; this mirror also
      satisfies that parity check vs the CLAUDE.md reframe (@8fd3dced5). All 4 [DOC] commit-prereq items now done.
- [x] ✅ [DOC] P2. **DONE — @5dbe60407.** `codex/06-coding-standards/quality-gates.md` § "Two-Pass Workflow Model" —
      added the commit-as-quality-boundary callout (prek = LIGHT gate; full QG = commit-prereq; QG-sweep batching;
      doc-commit carve-out).

### FF-push slot→LDR — PROPOSED, ratify before shipping (loosens a HARD RULE)

- [ ] [INFRA] P2. **[NEEDS-RATIFICATION]** Extend `scripts/dev/slot-cron-ff-pull.sh` to FF-push clean / >1h-old /
      ahead-only (0-behind) slot commits to LDR (generalize the ping-flush block; FF-only; retry-on-race). Makes the
      uta-style straggler self-resolve. **Placement = the symmetric slot-host cron stack** (per the "Local slot host =
      VM slot host" HARD RULE): one SSOT script in PM, run every 5 min on EVERY slot host — the agent-orchestrator's VM
      worker slots, the operator laptop, Harsh's laptop — so each host drains its OWN slots' stranded QG-green commits
      (no central pusher; symmetric, verified by `verify-slot-host-symmetry.sh`). Composes with agent_orchestrator_e2e
      (worker-slot model) + the per-tab-worktrees SSOT. **Makes the slot-host cron bidirectional**: today it is
      pull-only (`slot-cron-ff-pull.sh` FF-pulls incoming); background/spawned worker agents need the PUSH side too —
      FF-pull to stay current AND FF-push the QG-green work they commit, else their commits strand on the worker's tab
      branch exactly like the uta re-lock did. A background worker that finishes + moves on (no interactive operator to
      quickmerge) is the canonical strander this closes.
- [ ] [DOC] P2. **[NEEDS-RATIFICATION]** Reconcile the "Never raw `git push` for CODE" HARD RULE in CLAUDE.md +
      SUB_AGENT_MANDATORY_RULES.md + ci-cd-flow.md to carve out the cron FF-push of QG-green committed work (exact
      wording drafted; gap-analysis line anchors in the session notes). **Do NOT edit the HARD RULE until operator
      ratifies decision 3.**

### Remote tab branch stays current with LDR — server-side `LDR→tab` FF mirror (operator-chosen 2026-06-04, host-independent)

> **Driver (operator + slot-5 audit 2026-06-04):** a repo a slot DIDN'T commit to this session has its **local** tab
> branch kept current by `slot-cron-ff-pull.sh` (FF-pull LDR→local), but its **remote** tab branch
> (`origin/tab/<op>/<N>`) drifts BEHIND LDR because nothing pushes it (the cron is pull-only; the agent only pushes
> after a commit). Incident: slot-5 UAC remote tab stuck at `0abbdf86`, 3 commits behind LDR (peer slot-2/slot-3 commits
> the cron had already FF'd into local) → VS Code showed a misleading `0↓ 3↑` because the worktree upstream was ALSO
> mis-set to `origin/tab/...` (the `git push -u` footgun). **`behind`-only is BENIGN** (the `tab→LDR` mirror no-ops, the
> next commit FFs forward) — the only thing that's ever dangerous is **DIVERGENCE** (tab has own commits AND is behind),
> which is the alert in cicd (below). This is hygiene + a headless-fleet visibility fix, NOT a correctness gap.

> **PRECONDITION (operator 2026-06-04): the fleet-wide `tab/*` mirror + divergence monitor below are only SAFE if every
> tab branch name is globally unique.** Both operate by globbing `tab/*` across the whole fleet (laptop + every AWS/GCP
> VM), so two hosts sharing one branch name = the mirror FFs host-A's remote with host-B's commits (silent stomp) and
> the divergence alert mis-attributes. Today names are NOT guaranteed unique: `setup-tab-worktrees.sh` derives the
> prefix from `$USER`/`--operator` ([setup-tab-worktrees.sh:130-137](../../scripts/dev/setup-tab-worktrees.sh#L130)), so
> any VM running as `root` collapses to `tab/rootm/<N>` — every root VM collides on the same name (confirmed live:
> `tab/rootm/1..8` alongside the correctly-named `tab/vm-0/10`). Fix it FIRST (todo below), then the glob is sound.

- [~] [INFRA] P1. **Make tab branch names globally unique via the VM naming convention (PRECONDITION for the fleet-wide
  mirror + divergence monitor).** CODE SHIPPED 2026-06-04 (unified-trading-pm@35f6fb051, PM PR #130 merged to main): (a)
  ✅ `setup-tab-worktrees.sh` now bases the prefix on `PREFIX_BASE="${VM_NAME:-${OPERATOR}}"` — `$VM_NAME` on a fleet VM
  (globally unique by the VM naming convention), `OPERATOR` only on a laptop; verified a root VM now yields
  `tab/<vm>m/3` / `tab/<vm>/21` instead of the colliding `tab/rootm/<N>`, laptop unchanged. (b) ✅
  `verify-slot-host-symmetry.sh` check #11 asserts every slot branch is globally-unique-named (VM-scoped on a VM, never
  generic `root`/`rootm`); verified both directions (passes on laptop's 275 `tab/ikennaigboaka/*`, flags every branch
  when run with a mismatched `VM_NAME`). HARD invariant: a tab branch name is a global key — one host, fleet-wide.
  **REMAINING (c) — `BLOCKED-OPERATOR` (dead root VMs):** migrate the live mis-named `tab/rootm/1..8` branches to
  VM-scoped names — do NOT rename; re-provision the owning VM's worktrees with `VM_NAME` set
  (`setup-tab-worktrees.sh --reset-slot N`) using the now-fixed script, then delete each stale `tab/rootm/<N>` once
  empty. Can't action from this host (those VMs are down per operator 2026-06-04); the fix lands automatically on their
  next re-provision. Repos: `unified-trading-pm` (`scripts/dev/setup-tab-worktrees.sh` +
  `scripts/verify-slot-host-symmetry.sh`). parent_epic: (per-tab-worktrees / cicd master).
- [x] ✅ [INFRA] P1. **Make the VM-scoped prefix DURABLE across bare re-runs + align it on `ORCHESTRATOR_VM_ID` (closes
      the residual `rootm`-regression hole left by item above).** SHIPPED 2026-06-05 — `unified-trading-pm@852040bb9`:
      (a) `setup-tab-worktrees.sh` now resolves `HOST_ID="${ORCHESTRATOR_VM_ID:-${VM_NAME:-}}"` (== bootstrap `VM_ID`)
      for both prefix + commit host; (b) persists `OPERATOR`/`HOST_ID`/`MAIN_PREFIX`/`WORKER_PREFIX` to
      `${TABS_DIR}/.worktree-identity.conf` at `--init`/`--add-slot` and reads it back on a bare re-run; (c)
      `fix-commit-identity.sh` host now `ORCHESTRATOR_VM_ID`-first. **Verified (isolated resolution harness, 3
      scenarios):** laptop init+bare-reset → `tab/ikennaigboaka/N` (host=laptop, unchanged); VM bootstrap →
      `tab/vm-cefi/N`; **VM bare `--reset-slot` with the ambient env LOST (USER=root, no VM vars) → recovers
      `tab/vm-cefi/N`, NOT `tab/rootm/N`** — the regression closed. `bash -n` + `shellcheck -S error` clean on both
      scripts. Residual `tab/rootm/<N>` now only possible on a VM never provisioned with ANY VM env (= remaining-(c)
      operator re-provision). Provenance: session audit 2026-06-05 (slot-1). The 2026-06-04 fix only covers `--init`; a
      bare `--reset-slot N` / `--add-slot N` re-derives the prefix from the **ambient** env, so the `rootm` collision is
      NOT actually closed — two live gaps: **(1) ambient-loss regression** — a manual SSH session that didn't source the
      VM's startup env has no `$VM_NAME`, so `PREFIX_BASE="${VM_NAME:-${OPERATOR}}"` falls back to `$USER`=`root` →
      re-writes `tab/rootm/<N>` (exactly the branch the init fix was meant to prevent); **(2) `VM_NAME` ≠
      `ORCHESTRATOR_VM_ID` fork** — `bootstrap_vm.sh:110` brands branches from
      `VM_ID="${ORCHESTRATOR_VM_ID:-${VM_NAME}}"` (the short registry id, e.g. `vm-cefi`), but
      `setup-tab-worktrees.sh` + `fix-commit-identity.sh` key off raw `VM_NAME`; when they differ a re-run forks
      `tab/<long-instance-name>/<N>` divergent from the init's `tab/<vm-id>/<N>`. **Fix (CODE, this repo):** (a) prefer
      `ORCHESTRATOR_VM_ID` over `VM_NAME` in `setup-tab-worktrees.sh` (`HOST_ID="${ORCHESTRATOR_VM_ID:-${VM_NAME:-}}"`)
      so its prefix + commit host agree with bootstrap's `VM_ID`; (b) **persist** the resolved
      `OPERATOR`/`HOST_ID`/`MAIN_PREFIX`/`WORKER_PREFIX` to `${TABS_DIR}/.worktree-identity.conf` at provision time and
      **read it back** on a bare re-run (no `--operator`, no `ORCHESTRATOR_VM_ID`/`VM_NAME`, no `MAIN/WORKER_PREFIX`
      env) so the prefix can never regress to `$USER`; (c) mirror the `ORCHESTRATOR_VM_ID`-first preference into
      `fix-commit-identity.sh` so the commit host matches the branch host. Explicit overrides (incl. bootstrap's
      `--operator`/`MAIN_PREFIX`/`WORKER_PREFIX`) still win; laptop behaviour unchanged (no
      `VM_NAME`/`ORCHESTRATOR_VM_ID` → `HOST_ID` empty → `PREFIX_BASE=OPERATOR`). Repos: `unified-trading-pm`
      (`scripts/dev/setup-tab-worktrees.sh` + `scripts/hooks/fix-commit-identity.sh`). parent_epic: (per-tab-worktrees /
      cicd master).
- [x] ✅ [INFRA] P2. **Server-side `LDR→tab` FF mirror — make the existing tab-mirror BIDIRECTIONAL (FF-or-alert, never
      force).** SHIPPED 2026-06-04 (PM PR #132 + #134; rolled out to all 24 repos). Added a `ldr_to_tabs` job to
      `tab-mirror-to-ldr.yml` that FFs every behind-only `tab/*` up to LDR. **Cadence (operator-chosen 2026-06-04):**
      NOT push-triggered — runs on a `*/15 * * * *` schedule and FFs each tab only up to the latest LDR commit **older
      than 15 min** (settle window, so a just-landed commit isn't propagated onto remote tabs until it stabilizes).
      FF/alert-only; never force-pushes a tab; GITHUB*TOKEN push so no recursive leg-A trigger. Diverged tab → never
      touched → escalates to the divergence monitor (cicd item below). DEPENDS on the global-uniqueness precondition
      above (✅ shipped). Parity guarded by `detect_template_drift.py --workflows` (PM PR #133). **Original spec
      (push-triggered):** Extend the `tab-mirror-to-ldr` GHA (SSOT: `unified-trading-pm/scripts/workflow-templates/`,
      runs on push to LDR) so that, in addition to `tab→LDR` (FF LDR from an ahead-only tab — existing), it also does
      \*\*`LDR→tab`: FF every
      `tab/*` branch that is purely BEHIND LDR** (ancestor) up to LDR. **HARD invariants:**     FF-only, **never force-push**, never auto-merge. A tab that is BOTH ahead+behind (DIVERGED) → **do NOT touch it**     → emit the divergence alert (cicd item below); the one safe auto-resolution is the existing "rebase diverged tab     onto LDR" path (`e21ca439`— preserves the tab's own commits + pulls LDR in), reuse it, don't re-invent. **Why     server-side not the cron**: host-independent — refreshes a slot's remote tab branch whether the owning host     (laptop / AWS VM) is online or not (the headless-fleet gap the cron can't cover). **Operates over EVERY`tab/_`
      branch fleet-wide\*\* (all operators, all slots, every host) — DEPENDS on the global-uniqueness precondition above
      (without it the glob can FF one host's remote with another host's commits). Composes with — does NOT replace — the
      cron FF-push of QG-green \_committed_ agent work above (that's the `ahead`/push-agent-work-up leg; this is the
      `behind`/keep-tabs- current-down leg). Repo: `unified-trading-pm` (workflow-templates →
      `rollout-workflow-templates.sh`). parent_epic: (cicd master — cross-link `cicd_contract_hardening_2026_06_01.md`).
- [ ] [INFRA] P2. **Pin every tab worktree's upstream to `origin/live-defi-rollout` + assert it in
      `verify-slot-host-symmetry.sh`.** Root cause of the misleading `N↑` display: a `git push -u` (or
      `branch --set-upstream-to=origin/tab/...`) re-points a worktree's upstream to its (stale) remote tab branch, so VS
      Code's ahead/behind reads against the stale tab instead of LDR (phantom-ahead footgun, already documented in
      CLAUDE.md § "Upstream tracking"). `setup-tab-worktrees.sh --track` sets it correctly; add a guard in
      `verify-slot-host-symmetry.sh` that asserts `git rev-parse --abbrev-ref @{upstream} == origin/live-defi-rollout`
      for every worktree (fix + warn on mismatch) so the only thing the arrows ever show fleet-wide is genuine LDR
      drift. Repos: `unified-trading-pm` (`scripts/verify-slot-host-symmetry.sh` +
      `scripts/dev/setup-tab-worktrees.sh`). parent_epic: (per-tab-worktrees / cicd master).

### Quickmerge behind/diverge error contract — agents self-serve recovery (operator design 2026-06-03; many-parallel-agents driver)

> **Driver (operator)**: with dozens of agents running, the behind-remote-LDR + uncommitted-same-file reconcile must be
> a self-describing error the agent already knows how to act on — NOT an operator paste per agent. quickmerge STAGE 0.4
> already does the SAFE mechanical half (auto-ff → auto-rebase-autostash → `rebase --abort` + exit 1 on real conflict;
> never overwrites, never blind-merges — [`quickmerge.sh`](../../scripts/quickmerge.sh) STAGE 0.4). The gap is (1) the
> block is human prose, not an agent-actionable contract; (2) the uncommitted-same-file autostash-pop edge (the
> "Applying autostash resulted in conflicts" foot-gun) isn't trapped distinctly. PM-as-a-repo is COVERED by the same
> gate (it keys off the current branch's upstream), so no PM-specific code — one template change rolled fleet-wide.

- [ ] [INFRA] P1. **quickmerge STAGE 0.4 — structured error contract.** Replace the prose block with a machine-parseable
      sentinel + recovery block:
      `QUICKMERGE_BLOCKED code=BEHIND_DIVERGED_CONFLICT repo=<r> branch=<b> behind=<n>     ahead=<m> conflicts="<files>"`
      followed by a `RECOVERY:` line pointing at the SUB_AGENT_MANDATORY_RULES recipe. Add a DISTINCT
      `code=AUTOSTASH_POP_CONFLICT` trap: after `git pull --rebase --autostash` detect a leftover `git stash list` entry
      / conflict markers and emit that code instead of silently continuing. Preserve exit 1 + the
      `QUICKMERGE_ALLOW_BEHIND=1` override. Edit the **canonical PM template** `scripts/quickmerge.sh`, then
      `rollout-workflow-templates.sh` to all repos (never per-repo). Regression: shell unit asserting both codes fire on
      a synthesized behind+diverge + autostash-pop fixture.
- [x] ✅ [INFRA] P1. **FIXED (PM `scripts/quickmerge.sh`, this batch — live fleet-wide via the per-repo symlinks).**
      STAGE 0.4 now resolves the comparison ref from `git rev-parse --abbrev-ref @{u}` (configured upstream) when set,
      falling back to `origin/<branch-name>` only if no upstream. Verified: `@{u}` → `origin/live-defi-rollout` on a
      slot branch. **quickmerge STAGE 0.4 — reconcile against the configured UPSTREAM, not `origin/<branch-name>` (BUG,
      LIVE incident 2026-06-03 slot-2).** STAGE 0.4 sets `_QM_BRANCH=$(git branch --show-current)` and compares against
      `origin/$_QM_BRANCH`. For a slot worktree on `tab/<op>/<N>` whose **upstream is `origin/live-defi-rollout`** (the
      base for every repo) but whose `origin/tab/<op>/<N>` is STALE (the FF-push-back half of the slot cron isn't
      running — see decision 3 / the FF-push item below), this makes quickmerge attempt a 500+-commit autostash-rebase
      against a dead branch → conflict → BLOCKED, even though HEAD is **behind 0 / ahead 0 vs the real upstream LDR**.
      Incident: slot-2 was exactly at LDR tip + QG-green, but quickmerge tried to rebase 556 commits onto
      `origin/tab/ikennaigboaka/2` (frozen 2026-06-01) and blocked. **Fix**: STAGE 0.4 must resolve the comparison ref
      from `git rev-parse --abbrev-ref @{u}` (the configured upstream) when it exists, falling back to
      `origin/<branch-name>` only if no upstream is set. PM template → rollout. (Workaround used 2026-06-03: ship from a
      fresh branch with no `origin/` counterpart so STAGE 0.4 auto-skips.)
- [x] ✅ [INFRA] P1. **FIXED (PM `scripts/quickmerge.sh`, this batch — live fleet-wide via symlinks).** The STAGE 1.5
      `source` is now guarded:
      `if [ -f .venv-workspace/bin/activate ]; then source …; elif [ -f ../.venv-workspace/…];     then source …; fi`
      (tests before sourcing → no special-builtin exit; also finds the venv at the true repos-root for slot worktrees).
      Verified standalone with the slot symlink REMOVED: block survives + `python` resolves to the top-level workspace
      venv. **quickmerge STAGE 1.5 — `source .venv-workspace/bin/activate` KILLS quickmerge in a slot worktree (BUG,
      LIVE incident 2026-06-03 slot-2).** Line ~702 `source .venv-workspace/bin/activate 2>/dev/null || true` runs after
      `cd "$WORKSPACE_ROOT"`. For a slot worktree, `WORKSPACE_ROOT=$REPO_ROOT/..` = `.tabs/<N>`, where `.venv-workspace`
      does NOT exist (it lives at the true top-level `unified-trading-system-repos/.venv-workspace`). `source`/`.` is a
      POSIX **special builtin** → a not-found file under `set -e` exits the non-interactive shell **immediately,
      bypassing `|| true`** (confirmed: `bash -ec 'source missing 2>/dev/null || true; echo X'` prints nothing, exits
      1). So quickmerge dies silently at the dep-align stage with NO ❌ printed. **Fix**: guard with
      `[ -f .venv-workspace/bin/activate ] && source ...` (test before sourcing — a test failing under `set -e` inside
      `&&` is safe), and/or resolve the venv at the true workspace root not the slot `WORKSPACE_ROOT`. PM template →
      rollout. (Workaround used 2026-06-03: `ln -s <top-level>/.venv-workspace .tabs/2/.venv-workspace`.)
- [ ] [INFRA] P2. **OBSERVED CASCADE RESOLVED by the STAGE 1.5 `source`-guard fix above; the standalone hardening below
      remains open.** With the venv now activating, line ~703 `generate-derived-manifest.py` runs and re-creates the
      manifest, so the absent-manifest checker error no longer fires in the normal path. STILL TODO (defence-in-depth):
      make generate hard-required (not `|| true`-swallowed) OR have the checker auto-generate when absent. **quickmerge
      STAGE 1.5 dep-align hard-errors when `derived-dependency-manifest.json` is ABSENT (BUG, slot-2 2026-06-03).** The
      item-H generated-artifact untracking (LDR) deletes `derived-dependency-manifest.json`; after an FF a slot has no
      local copy, and `check-dependency-alignment.py` exits with "Run generate-derived-manifest.py first" → quickmerge
      dep-align fails. quickmerge line ~703 DOES call `generate-derived-manifest.py` first, but only
      `2>/dev/null || true` — so if the generate step itself is the thing that died (it shares the same venv/PATH the
      `source` bug above broke), the stale/missing manifest cascades. **Fix**: the dep-align stage should hard-require a
      successful generate (not `|| true`-swallow it) OR the checker should auto-generate when absent. PM template →
      rollout. (Workaround used 2026-06-03: ran `generate-derived-manifest.py` manually pre-quickmerge.)
- [x] ✅ [DOC] P1. **SUB_AGENT_MANDATORY_RULES.md** — added the behind-remote recovery recipe keyed on the
      `QUICKMERGE_BLOCKED` block (operative today against the existing exit-1; structured codes land with the INFRA
      item). — PM@pending (this batch).
- [x] ✅ [DOC] P1. **codex/08-workflows/ci-cd-flow.md** § "STAGE 0.4 Not-Behind Gate" — documented the gate (ff →
      rebase-autostash → abort+exit-1, never overwrites) + recovery recipe + PM-as-a-repo coverage + forward
      structured-contract note. — PM@pending (this batch).
- [x] ✅ [DOC] P2. **CLAUDE.md** git-discipline — one-line pointer to the gate + recovery recipe + the tracked
      structured contract. — PM@pending (this batch).

### Residual

- [ ] [DEPS] P3. **unified-trading-api** re-lock commit (1 trivial metadata-sync, 0 version moves) — race-blocked by the
      ci_status bot on uta's LDR; lands via the FF-push cron (once shipped) or a quiet-window FF push.

## Cron-executor staleness → e2e self-pull rollout (operator design 2026-06-05)

> **Root cause (2026-06-05 incident):** slot-1's instruments-service + mtds showed `1 ahead / 6(5) behind LDR` —
> duplicate tab-mirror commits the FF-pull cron's `[adopt-rebase]` (Step 5) + upstream self-heal (Step 0) already fix
> automatically. They never ran because **the cron executes its script from the workspace-root PM clone, which was 195
> commits behind + dirty** (one uncommitted plan file) → its own FF self-skipped `[skip:dirty]` → it ran pre-self-heal
> code. Same failure mode the script's own comment records ("stranded the top-level PM clone 1164 commits behind"). The
> drift is **planted at bootstrap**: `setup-tab-worktrees.sh` `worktree add --track origin/<tab-branch>` sets
> `@{upstream}` = remote tab branch for any repo whose tab branch already exists (UTL/UAC/mtds/mdps cluster). It is
> **machine-only** — GHA workflows run from a fresh remote checkout each time, so they are immune by design.

### Phase A — auto-heal NOW (laptop) — DONE 2026-06-05

- [x] ✅ [OPS] P0. Unstuck laptop root PM clone: rescued slot-2's uncommitted plan edit (`stash@{0}` +
      `/tmp/rescue_slot2_defi_provenance_2026_06_05.patch`), FF'd root clone 195 commits → current code, ran one manual
      tick → `[adopt-rebase]` healed slot-1 IS (`51de1ce4`) + mtds (`76d650f0`) to LDR (0/0); `[upstream-fix]` reset all
      drifted upstreams (UTL/UAC/mtds/mdps, tabs 1·3·4·5·6·7) → `origin/live-defi-rollout`.
- [ ] [PLAN] P1. **Land slot-2's rescued edit** (DeFi provenance `A12c ✅` flip + `A12a` remaining-handlers todo, in
      `plans/active/data_source_provenance_all_asset_groups_2026_06_01.md`) onto LDR via a slot quickmerge
      `docs(plans):` — it currently lives ONLY in `stash@{0}` + the `/tmp` patch on the laptop root clone (unique, not
      on LDR).

### Phase B — permanent executor self-pull (the core fix) — `unified-trading-pm/scripts/dev/`

- [ ] [SCRIPT] P0. **Cron line self-pulls its own script from LDR before running** — so a stale/dirty PM clone never
      starves the cron of current code (kills the chicken-and-egg). Pattern (in the crontab line = immutable anchor, NOT
      inside the script):
      `cd <ROOT_PM> && git fetch -q origin live-defi-rollout 2>/dev/null; git checkout -q     origin/live-defi-rollout -- <script> <tracked-sibling-deps> 2>/dev/null; cd <CWD> && bash <ROOT_PM>/<script> <args>`.
      Use `git checkout origin/LDR -- <file>` (lands at real path → `BASH_SOURCE`-relative sibling + `--help` still
      work); NOT `git show | bash -s`. Offline-safe via `|| true` (falls back to last-good local copy, never skips a
      tick). For `slot-cron-ff-pull.sh` pull BOTH it + `scripts/dev/cron-branch-overrides.txt` (tracked sibling dep,
      line 47).
- [ ] [SCRIPT] P1. Factor the self-pull into a shared helper sourced by every cron-installer so the pattern is DRY in
      source even though each emitted crontab line is self-contained.

### Phase C — apply self-pull to EVERY machine-run PM cron (audit 2026-06-05)

These all run PM-repo scripts from the root clone (= identical staleness exposure). GHA workflows excluded (current by
design).

- [ ] [SCRIPT] P0. `slot-cron-ff-pull` (root clone, \*/5) — self-pull.
- [ ] [SCRIPT] P0. `slot-host-symmetry-verify` (root clone) — self-pull **+ fix cadence drift** (installed `*/30`,
      install script wants `*/15` per 2026-06-04 — proof the installer wasn't re-run since the clone went stale).
- [ ] [SCRIPT] P1. `slot-git-status-report` (root clone, \*/5) — self-pull (`scripts/dev/slot-git-status-report.sh`).
- [ ] [SCRIPT] P1. `orphan-ping-audit` (root clone, every 4h, `scripts/agents/audit_ping_orphans.sh`) — self-pull;
      update its self-installer.
- [ ] [SCRIPT] P2. `refresh-manifest-dag` (`scripts/manifest/refresh-manifest-dag.sh`, \*/30) — runs from the slot-1
      worktree (FF-managed, lower risk) — add self-pull for consistency OR document why exempt.

### Phase D — bootstrap enforcement so drift never re-plants

- [ ] [SCRIPT] P0. `setup-tab-worktrees.sh:258-261` — after `worktree add --track … origin/${branch}`, force
      `git -C <slot_dir> branch --set-upstream-to=origin/live-defi-rollout ${branch}` so upstream = LDR even when the
      worktree is created from an existing remote tab branch (closes the drift-at-source gap).
- [ ] [SCRIPT] P1. Install scripts (`install-slot-cron-ff-pull.sh` + siblings) — abort if `WORKSPACE_ROOT` resolves
      inside `/.tabs/` (install MUST run from the root clone, else it bakes wrong `ROOT_PM`/`SLOT_DIR` absolute paths —
      protects Harsh + VM installs).

### Phase E — debounced upstream auto-fix + escalation (operator refinement 2026-06-05)

- [ ] [SCRIPT] P1. `slot-cron-ff-pull.sh` Step 0 — replace the IMMEDIATE upstream reset with a **10-min grace**: marker
      `$TMPDIR/slot-upstream-drift/<host>-<slot>-<repo>` records first-seen; `--set-upstream-to=LDR` only once the
      marker is ≥10 min old (room for intentional temporary switches); clear marker when aligned.
- [ ] [SCRIPT] P1. `verify-slot-host-symmetry.sh` — **Slack-alert if a drift marker is ≥15 min old** (auto-fix-failed
      signal; expected no-op since the 10-min fix clears it). Reuses the same marker dir.

### Phase F — fleet rollout + verification (Harsh + VM)

- [ ] [OPS] P0. Re-run `install-slot-cron-ff-pull.sh` on THIS laptop after B–E land (installs self-pull lines + corrects
      the `*/30`→`*/15` verify cadence).
- [ ] [OPS] P0. Verify `ROOT_PM`/`SLOT_DIR` correctness on **Harsh's laptop + the AWS VM** (`crontab -l` host-correct
      absolute paths) + re-run install there + one-time root-clone unstick if stranded
      (`git -C <host>/unified-trading-pm rev-list --count HEAD..origin/live-defi-rollout`). Dispatch via orchestrator.
- [ ] [DOCS] P1. `codex/05-infrastructure/per-tab-worktrees.md` § "Cron-based FF puller" — document the
      self-pull-executor principle + the rule "every machine-run PM cron self-pulls its script from LDR before running;
      GHA exempt (current by design)". + one-liner in canonical `CLAUDE.md`.

### Phase G — LATER (June): crons on a gated hot-fix path

- [ ] [DESIGN] P3. **LATER (June).** Crons currently self-pull from `live-defi-rollout` (the integration/hot-fix axis) —
      so a cron-script change reaches every machine the moment it's on LDR, on the implicit assumption the author ran QG
      before pushing. Mature this into an **enforced** hot-fix path: cron scripts self-pull from a branch whose changes
      are **forced through `quality-gates-v2`** (e.g. promote cron-script changes to `main` and have crons pull `main`,
      or a dedicated gated `cron-release` ref). Makes "QG ran before this cron changed" a guarantee, not a convention.
      Not urgent — the self-pull (Phase B) already removes the staleness foot-gun; this only adds the gate. Successor
      framing, not a blocker.

### Phase H — single-source-of-truth audit (operator 2026-06-05) — no contradictions across docs

- [ ] [DOCS] P0. **Full contradiction sweep** so codex + canonical `CLAUDE.md` + `SUB_AGENT_MANDATORY_RULES.md` + cursor
      `.mdc` rules + the scripts' own header comments all agree on: (P1) slot `@{upstream}` is ALWAYS
      `origin/live-defi-rollout`; (P2) FF-pull is FF-only EXCEPT the bounded `[adopt-rebase]` that drops patch-id-dup
      commits on a clean tree — so any "never rebase / never destructive" wording is now stale; (P3) machine-run PM
      crons self-pull their script from LDR before running, GHA exempt (fresh checkout per run); (P4) crons pull the LDR
      hot-fix axis today (Phase G matures this); (P5) upstream drift auto-heals debounced (10-min grace). Fix every
      divergent/ duplicate statement in place; one SSOT per rule.

## Stuck promotion-PR remediation — 12 wedged LDR→staging PRs (2026-06-05)

> Triggered by the CI-watcher alert: 12 promotion PRs BLOCKED/DIRTY 6–65h + 3 failing PM@main monitors. Diagnosed: NOT
> one shared cause — **per-repo heterogeneous v2 debt** (= cicd Phase-6 territory) + a CI-mechanism gap. Fixed via a
> 7-repo fix-agent fan-out (2026-06-05).

### Results (7 BLOCKED repos)

- [x] ✅ **batch-live-reconciliation #16** — STALE check (F811 dup-dataclass fix already on LDR @2137791; promotion PR's
      v2 was frozen on the pre-fix SHA). Re-triggered via close+reopen → v2 green → CLEAN/merging.
- [x] ✅ **client-reporting-api #14** — REAL: pip-audit CVE (`aiohttp 3.13.5` → CVE-2026-34993) from a **stale
      uv.lock**. Bumped `aiohttp>=3.14.0` + `uv lock` → shipped (LDR @7ac0624) → MERGED to staging.
- [x] ✅ **trading-agent-service #10** — REAL: pip-audit CVE (`starlette 0.52.1` → PYSEC-2026-161) from a **stale
      uv.lock**. `uv lock` → starlette 1.1.0 → shipped (LDR @5555cca) → MERGED to staging.
- [x] ✅ **execution-service #211** — STALE (LDR v2 was green @06-04); re-triggered → v2 in_progress → will unblock.
- [ ] [QG] P1. **instruments-service #396 — FOLLOW-UP (not shipped).** Agent applied IMDS test-isolation fix
      (`tests/conftest.py` default `CLOUD_PROVIDER=local` + per-test `_sports_ref_sink_for` mock) for the one CI socket
      failure. BUT local QG shows **80 unrelated failures** vs CI's "1 failed, 3140 passed" → ambiguous: local env-rot
      OR the _global_ conftest change regressed bucket-sensitive tests. **Resolve**: determine regression-vs-env; prefer
      the NARROW fix (per-test mock only, drop the global conftest change → zero blast radius), re-validate, ship. Fix
      preserved UNCOMMITTED in `.tabs/1/instruments-service` worktree.
- [ ] [QG] P0. **strategy-service #67 — REAL multi-day type-debt (KEYSTONE).** STEP 5.12b URI = 1 false-positive (fixed,
      `evidence_router.py:59` noqa, staged). STEP 5.21 = pyright config drift: flipping `reportUnknown*` none→error
      surfaces **628 errors / ~60 files** (hotspots: `batch_handler.py` 124, `pnl_monitor.py` 69, `risk_monitor.py` 66,
      `exposure_monitor.py` 48); zero-baseline policy → none suppressible. **Needs a dedicated typed-code remediation
      (multi-day).** Blocks deployment-api too (dep-tier). URI fix staged UNCOMMITTED in worktree.
- [ ] [QG] P1. **deployment-api #17 — BLOCKED by dep-tier ordering, own issues resolved.** Editable-metadata TOML
      dup-key already fixed on LDR (deployment-service @5734823); brittle `-prd`-hardcoded test fixed + QG-green (staged
      UNCOMMITTED). Can't ship: quickmerge dep-tier gate refuses promotion ahead of `deployment-service` (770 ahead of
      staging) + `strategy-service` (57 ahead), both FEATURE_GREEN not STAGING_GREEN; `--skip-dep-tier-gate` is
      human-only. **Resolve**: sequence — green+promote strategy-service (keystone) + deployment-service to staging
      first, then deployment-api promotes; OR operator `--skip-dep-tier-gate` for this test-only hotfix.

### DIRTY conflicts (5 PRs) — step 3

- [ ] [QG] P1. **LDR→staging merge conflicts**: deployment-service #21, mtds #91, system-integration-tests #21 — resolve
      `live-defi-rollout`↔`staging` conflicts per repo (after the BLOCKED fixes settle; LDR is moving).
- [ ] [QG] P2. **Stale tab→staging PRs** (likely close, not resolve): deployment-service #15 (tab/hkm/3, ~65h —
      **Harsh's**, confirm before closing), mtds #94 (tab/ikennaigboaka/3) — superseded by the LDR→staging promotion.

### CI-mechanism findings (permanent fixes worth landing)

- [ ] [SCRIPT] P1. **Promotion PRs don't re-run `quality-gates-v2` when LDR advances** — the required check freezes on
      the PR-open SHA, so a fix landing on LDR leaves the PR BLOCKED on a stale red/green check until a manual
      close+reopen (hit on batch-live-recon #16, execution #211). Make `ldr-to-staging-promote` (or a small watcher)
      re-trigger v2 on head advance. This is the dominant cause of "wedged for hours" PRs.
- [ ] [DEPS] P0. **Fleet-wide aiohttp on the CVE-vulnerable floor `>=3.13.4` (CVE-2026-34993 RCE) — SECURITY + PM-gate
      blocker (2026-06-05).** 17 repos + `canonical-dependency-manifest.json` all pin `aiohttp>=3.13.4,<4.0.0`
      (vulnerable; fix = 3.14.0). The fan-out's client-reporting CVE bump to `>=3.14.0` was correct but **half-applied**
      (canonical + the other 17 not bumped) → client-reporting is now the lone dep-alignment outlier → **PM
      `check-dependency-alignment` FAILS → blocks ALL PM quickmerges** (Phase B + plan stuck behind it). FIX (security
      direction, bump UP not down): set `canonical-dependency-manifest.json` aiohttp → `>=3.14.0,<4.0.0`, bump all 17
      repos' pyproject to match, `uv     lock` each, ship. Repos: batch-live-reconciliation, deployment-api, alerting,
      instruments, fund-administration, market-tick-data, execution, strategy, features, unified-api-contracts,
      unified-trading-api, unified-trading-pm, trading-agent, unified-trading-library, market-data-processing,
      deployment-service, ml-service. Lesson: a CVE dep bump MUST also bump the canonical manifest (else it self-blocks
      the PM gate).
- [ ] [DEPS] P1. **Stale `uv.lock` → pip-audit CVE failures fleet-wide** — 2 of the BLOCKED repos failed codex pip-audit
      purely from stale locks resolving vulnerable transitive deps (aiohttp, starlette). Sweep `uv lock` across repos
      (composes with `uv_lockfile_determinism_2026_06_02.md`); audit for more lurking stale locks.

### Temporary states (uncommitted fixes preserved in slot-1 worktrees)

- `.tabs/1/strategy-service` (URI noqa), `.tabs/1/instruments-service` (IMDS isolation), `.tabs/1/deployment-api`
  (`-prd` test fix) — left UNCOMMITTED for the follow-up remediations above; the ff-pull cron will `[skip:dirty]` them
  until resolved. Successor: the three FOLLOW-UP todos above.

## Cross-links (do NOT duplicate — these items live in the named plans)

- **cicd_contract_hardening_2026_06_01.md**: per-repo QG-debt greening (Phase 6) ← amplified by the governor fix here;
  `pyjwt`→2.13.0 fleet bump (its line ~350) composes with the uv re-lock sweep; manifest/DAG worktree-dirty churn (its
  lines ~678 / ~1109 / ~1201) is the same prettier/regen churn this session worked around — its structural fix (untrack
  generated SVG + ci_status sidecar) would remove the churn that complicated reconciliation here.
- **agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md**: G6 (AO staging branch + standard
  tab→LDR→staging→main flow) shares the commit/push model; the commit-as-quality-boundary rule applies to AO too once G6
  lands its quickmerge path.

## LDR-protection resolution (2026-06-03) — docs reconciled

- [x] [DOC] **RESOLVED + reconciled across docs**: LDR is the **unprotected integration axis** (no required-check
      ruleset) — best practice. The enforced `quality-gates-v2` check fires at the **staging/main PR** (promotion
      boundary); **local QG + sentinel is the agent + quickmerge pre-flight** (fail-fast), not a server gate.
      Reconciled: `cicd_contract_hardening` goal-line ("runs+green across branches; required ruleset on main, LDR
      unprotected") + its reconcile-todo marked RESOLVED; canonical `CLAUDE.md` "Merge Prerequisite" rule clarified
      (local pre-flight vs staging/main server gate; default-branch must be `main`); `ci-cd-flow.md` reinforced.
      **Root-cause code fix shipped**: `verify_branch_protection_check_names.py` now asserts `default_branch == main`
      fleet-wide (uta+greeks were `live-defi-rollout` → fixed to `main`; `~DEFAULT_BRANCH` ruleset no longer lands on
      LDR). ⇒ **the FF-push design (decision 3) holds** — raw/FF-push to the unprotected LDR is viable.

## Success criteria

- Canonical docs agree: commit is the per-repo quality boundary (no more merge-vs-commit-prereq drift).
- (If ratified) slot FF-push cron drains clean/aged/ahead-only commits to LDR; no more uta-style stranding.
- The governor-unmasked per-repo QG debt is tracked + greened via cicd Phase 6 (cross-linked, not duplicated).

## Conflict-resolution + convergence model — Option-B follow-on (design locked 2026-06-03)

> **Convergence model (confirmed — mostly already built).** LDR = fast live integration (agents work here, allowed
> temporarily inconsistent); the gated **main PR is the reconciliation point** (under Option B, PM's main does for plans
> what staging does for service repos); `main-backmerge-to-ldr.yml` feeds reconciled main→LDR on every main push
> (additive merge, never force/drop) → FF-pull cron (≤5 min) converges every host (other VMs + laptops). **Three
> conflict layers, no race:** TEXTUAL merge = conflict-resolution-agent; SEMANTIC = per-VM `review.md` + the new
> cross-plan detector; HYGIENE = plan-health-agent (scripted + Haiku, report-only).

- [x] ✅ [SCRIPT] **P0 — escalation bridge UN-BROKEN (done+verified 2026-06-03).** `ORCHESTRATOR_INTERNAL_SECRET` was
      missing from PM Actions → `escalate-to-orchestrator` auth-died (only run FAILED: "secret not set — cannot
      authenticate"). Read the canonical 64-char value off the **api-host** `i-0c9b283b31d6b5ca7` (live server process
      env — NOT on the central VM, NOT in GCP/AWS SM) via SSM + set it on PM Actions (value never printed).
      **Verified:** escalate re-run `26877427868` → **SUCCESS** ("dispatched to orchestrator — Max worker resolving on
      LDR"). The GHA→orchestrator bridge is ALIVE; ci-failure-watcher's conflict escalations now actually land.
- [x] ✅ [SCRIPT] P1. **conflict-resolution-agent cut over to the Max-plan worker (in-GHA API DROPPED)** —
      unified-trading-pm@df841daaf. Replaced the 700-line `ANTHROPIC_API_KEY_CICD` + `claude-code` in-GHA resolver with
      a clean 84-line **escalate-relay**: on `merge-conflict-detected` it `repository_dispatch`es
      `escalate-to-orchestrator` (`wall_type=merge_conflict`, `model=opus`) via `GH_PAT` → orchestrator spawns a
      setup-token Max worker that resolves ON live-defi-rollout + re-gates via quality-gates-v2. Trigger contract
      preserved (repo_name/source_branch/target_branch/original_pr_url); 3 callers (staging-to-main /
      ldr-to-staging-promote / feature-branch-to-staging) unchanged. YAML validated; no active API ref.
      Verified-by-construction (uses the same escalate interface proven green this session); a real conflict exercises
      it end-to-end.
- [x] ✅ [SCRIPT] P1. **Every Slack-alert event ALSO pings the orchestrator → it delegates.** (a)
      `main-backmerge-to-ldr.yml` conflict → escalates escalate-to-orchestrator (opus) via GH_PAT alongside the human PR
      (unified-trading-pm@c1fa002b1). (b) `ci_failure_watcher.py` escalates CONFLICT stuck-PRs as merge_conflict
      (verified live — deployment-service#15) **AND now BLOCKED-with-failed-check stuck-PRs as sit_failure**
      (unified-trading-pm@783b28153 + tests @b4dd80fed) — guarded on `statusCheckRollup` so transient staging-locks
      don't spawn workers; reuses the per-PR label idempotency. So conflict, CI-RED, and backmerge-conflict alerts all
      reach the orchestrator. (Raw non-PR workflow-run failures stay Slack-only by design — escalating those needs a
      non-PR idempotency mechanism; the actionable cases all surface as stuck PRs, which are now covered.)
- [ ] [SCRIPT] P2. **Semantic cross-plan/cross-slot conflict DETECTOR (scripted-first + epic-VM decides).** Catches "two
      individually-valid plans whose WORK conflicts, no textual overlap" — which no existing layer does. (1) scripted
      overlap-detector: parse active-plan todos for declared **target surface** (repo/file/symbol), flag cross-slot
      overlaps, feed to plan-health-agent like the hygiene scripts. (2) on flag → ping the OWNING epic-VM orchestrator →
      auto-reconcile (worker) or post proposed solution + operator-block (VM chat / laptop). Reuses
      escalate-to-orchestrator + reviewer→worker→main — no new escalation path. repo: unified-trading-pm +
      agent-orchestrator.
- [x] ✅ [DOC] P1. **Lock the convergence + 3-layer-conflict + Option-B model in canonical docs** —
      unified-trading-pm@706fe8170: ci-cd-flow.md (new "PM/codex main-direct (Option B)" + "Convergence +
      conflict-resolution model" sections), CLAUDE.md (PM/codex→main directive + pointer), SUB_AGENT_MANDATORY_RULES
      (target-surface declaration + 3-layer model + check overlapping open claims). setup-workspace codex-clone removed
      in same commit.
- [ ] [SCRIPT] P2. **Finish codex-not-a-separate-repo cleanup.** Live SSOT (`workflow-templates/`) + deployed fleet
      already correct. Fixed: `scripts/templates/semver-agent.yml` (c10463f69),
      `scripts/propagation/templates/semver-agent.yml` (0ca9dc657). Remaining:
      `propagation/templates/major-bump-approval.yml` (checkout + 3 consumers + a write-back
      `cd ../unified-trading-codex` that commits BR8 → redirect to PM/codex + commit-to-PM),
      `setup-workspace-from-manifest.sh` (optional clone of the ARCHIVED codex repo → remove), + a few doc mentions
      (readiness-verifier.yml, setup.sh, \_workspace-lib.sh, compute-epic-readiness.py, check-repo-readiness.py,
      workspace-bootstrap.sh, auto-populate-tags.py — verify benign-vs-broken). repo: unified-trading-pm.
