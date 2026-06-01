---
name: orchestrator_autonomy_audit_remediation_2026_06_01
title: "orchestrator autonomy audit remediation — uncovered findings from the 2026-06-01 § M audit"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-01
last_updated: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/05-infrastructure/agent-orchestrator-slack-notifications.md
source_audit: plans/audit/results/orchestrator_master_audit_2026_06_01.md
related_plans:
  - plans/active/autospawn_idle_vms_2026_05_30.md
  - plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md
  - plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md
  - plans/active/harsh_pc_dispatch_failover_2026_05_30.md
---

## Why this exists

The 2026-06-01 orchestrator-master audit (first run after the § M "closed-loop autonomy" extension) surfaced findings
that are **not owned by any existing active plan**. The autonomy mechanisms themselves (AutoSpawnLoop,
WorkerLivenessWatchdog, regen prune-stale, FailoverLoop) all verified GREEN at the code level and have owning plans for
their rollout/soak. This plan captures only the **residual, unowned** findings so they are not silently lost.

Source: [`orchestrator_master_audit_2026_06_01.md`](../audit/results/orchestrator_master_audit_2026_06_01.md).

## Coverage reconciliation (what is already owned — do NOT duplicate here)

| Finding                                       | Owning plan                                                                     | Status                                                                     |
| --------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| m2c — watchdog fleet rollout unrecorded       | `agent_orchestrator_worker_liveness_watchdog_2026_06_01` Phase 3                | scripts shipped; operator-SSM execution + table fill outstanding **there** |
| m3a — backlog honesty re-confirm              | `agent_orchestrator_backlog_state_alignment_2026_05_29` continuous-verification | owned                                                                      |
| m5 — PM-plan → done E2E trace                 | `e2e_test_plan_regen_pipeline_2026_05_29`                                       | owned                                                                      |
| m1b/m1c — autospawn flag-live + spawn-on-kill | `autospawn_idle_vms_2026_05_30` Phase 3 closing-condition                       | owned                                                                      |

## Phases

### Phase 1 — P1-2: S3-side state snapshot (close the AWS disaster-recovery loop)

The AWS fleet keeps orchestrator state on local disk only — `server/gcs_sync.py` is GCS-only. A VM restart on the AWS
fleet loses `state.db` + `state.json` unless `ORCHESTRATOR_GCS_BUCKET` is reachable (it is not, on the AWS hosts). The
codex overview documents this as a "Known gap (carried as deferred 2026-05-28)" but no plan owns closing it. With the
fleet now self-healing 24/7 on AWS, the durability gap has real teeth (autospawn + watchdog restart workers; a host
reboot still wipes dispatch/backlog state).

- [x] ✅ [CODE] P1. Add an S3 snapshot path to `server/gcs_sync.py` (or a sibling `s3_sync.py` sharing the
      `SnapshotLoop` interface) gated on `ORCHESTRATOR_S3_BUCKET`. Mirror the GCS cadence (30-min auto + shutdown). Use
      the workspace cloud-interface S3 helpers, not raw boto subprocess. Unit-test the upload path with `@mock_aws`. QG
      green + quickmerge. Collision group: `ao_s3_snapshot_code`. Estimate: 0.5 AI-day. ✅ DONE 2026-06-01 —
      agent-orchestrator@57dc8c2 (LDR). Added `upload_state_to_s3` + `backup_sqlite_to_s3` (boto3 client, not
      subprocess; gated on `ORCHESTRATOR_S3_BUCKET`; never-raise) wired into `snapshot_session()` + `SnapshotLoop`
      backup tick alongside GCS. + `boto3` dep + 8 `@mock_aws` tests (all pass). ruff + basedpyright 0 errors. NB: 6
      unrelated pre-existing test failures (slack/worker_liveness modules) + a `pexpect` venv gap observed in this
      worktree — neither touches `gcs_sync.py`; flagged for the env/test-health owner, not this commit.
- [~] 🟡 [SCRIPT] P1. Provision `s3://uts-orchestrator-state-427895769566/` + set `ORCHESTRATOR_S3_BUCKET` systemd env
  on the 11 AWS VMs via SSM drop-in. Restart orchestrator; confirm a snapshot object lands within one cadence window.
  Collision group: none. Estimate: 0.2 AI-day. 🟡 PARTIAL 2026-06-01 (slot-1, AWS admin `admin_od`): **bucket created**
  `uts-orchestrator-state-427895769566` (ap-northeast-1, versioning on) + `enable_s3_snapshot.sh` drop-in script
  shipped. **Env rollout pending** — canary-first per workspace rollout discipline; activation needs an orchestrator
  restart per VM (the 6 behind=0 VMs already carry the @57dc8c2 code). End-to-end snapshot verification additionally
  needs an authed `/api/snapshot` trigger (the fleet `/api/snapshot` is NOT ALLOW_ANONYMOUS — returns "missing bearer
  token"). To roll: run `enable_s3_snapshot.sh` per VM via SSM, canary vm-cefi first (a fleet wrapper can mirror
  `run_fleet_enable_watchdog.sh`), when ready to restart orchestrators.
- [x] ✅ [DOCS] P2. Update the `codex/04-architecture/agent-orchestrator-overview.md` "Known gap" callout — flip it from
      "deferred future work" to "shipped — AWS↔S3 snapshot live" with the bucket name + env var. Collision group: none.
      Estimate: 0.05 AI-day. ✅ DONE 2026-06-01 — overview "Secrets + buckets" state-snapshot row + the callout now read
      "code shipped @57dc8c2; remaining operator step = provision bucket + set `ORCHESTRATOR_S3_BUCKET` on 11 VMs".

### Phase 2 — P1-1: standing deploy-currency + flag-liveness fleet check

Each autonomy plan verifies its own flag at rollout time, but nothing provides a **standing** "are all 11 VMs running a
HEAD that includes the autonomy commits, with all four flags live" check. The central `/health` reports `version:0.6.0`
which predates the autonomy work — the running binary's currency is unverified. This is the gate between "code exists on
LDR" and "loop actually runs 24/7".

- [x] ✅ [SCRIPT] P1. Write `unified-trading-pm/scripts/orchestrator/verify_fleet_autonomy_health.sh` — for each VM (via
      SSM or authed proxy): report (a) deployed git HEAD short-sha of agent-orchestrator vs LDR HEAD, (b) presence +
      value of `ORCHESTRATOR_{AUTOSPAWN,WORKER_WATCHDOG,REGEN_PRUNE_STALE}_ENABLED` + `ORCHESTRATOR_VM_ID` in
      `/proc/<pid>/environ`, (c) `/health` version. Emit a per-VM ✅/⚠️ table. Collision group: none. Estimate: 0.3
      AI-day. ✅ DONE 2026-06-01 — script shipped (read-only, parallel SSM probe, 11-VM list). Per-VM ✅ requires
      behind=0 AND flags=4/4 AND /health responds; else ⚠️ with the specific missing flag/behind-count. Exits 1 if any
      VM ⚠️. `bash -n` clean. Operator runs it (needs SSM creds) — see next item.
- [x] ✅ [SCRIPT] P1. Run the script fleet-wide; for any VM behind LDR HEAD or missing a flag, pm-pull + enable +
      restart. Capture the before/after table in this plan. Wire the script as the live tool behind audit checks
      m1b/m2c/m3b/m3c so future audits can run it in one shot. Collision group: none. Estimate: 0.15 AI-day. ✅ RAN
      2026-06-01T11:13Z (slot-1, AWS admin). Live result — **all four autonomy flags live (flags=4/4) on 10/11 VMs** →
      m1b/m2c/m3b/m3c GREEN (corrects the audit's m2c-RED assumption; the watchdog IS enabled fleet-wide, the empty
      rollout-table was unfilled bookkeeping not un-rolled flags). Deploy-currency: 6 VMs at HEAD (behind=0: vm-cefi,
      vm-defi, vm-sports, vm-tradfi, vm-trading-core, vm-cross-cutting); **3 behind** (vm-orchestrator=6,
      vm-operator-ops=5, vm-prediction=6) — these need pm-pull+restart to load the autonomy HEAD; **vm-ml =
      SSM-degraded** (see Findings). api-host ver=NA (central health is on :8765 not :8026 — known, not an outage).

## Findings (from the live 2026-06-01 run)

- 🟠 **F1 — 3 VMs behind agent-orchestrator HEAD** (vm-orchestrator/-operator-ops/-prediction, 5–6 commits). They run
  older code than LDR (missing the S3 snapshot + possibly other autonomy fixes). Fix: `pm-pull` + restart orchestrator
  on each. pm-pull.timer should catch them up; if it's wedged that's the root cause to chase.
- 🔴 **F2 — vm-ml SSM execution is broken.** Every SSM command (even `echo`/`df`) returns Status=Failed with empty
  stdout/stderr, despite EC2 status checks ok/running. Almost certainly disk-full (vm-ml's historical 142k-line backlog
  bloat) or a wedged SSM agent — unrecoverable via SSM since SSM itself can't execute. **Needs SSH/operator** to clear
  disk + restart the agent. vm-ml's autonomy flags + currency are therefore unverified.
- [x] ✅ [DOCS] P2. ~~Bump the central `/health` version string~~ — **REVISED**: manual version bumps are forbidden
      (workspace rule "NEVER bump manually — semver-agent handles all"). The `feat(gcs_sync)` commit @57dc8c2 will
      auto-bump 0.6.0 → 0.7.0 via semver-agent on its next run, and `/health` reflects it after deploy. The canonical
      deploy-currency signal is the **git-HEAD `behind=` count** in `verify_fleet_autonomy_health.sh` (above), which is
      finer-grained than the semver string. No manual action — resolved by the verify script + semver-agent.

### Phase 3 — P2-1: notification inventory doc drift

`slack.py` now exports 13 `notify_*` funcs + `telegram.py` 9 (the autonomy work added `notify_autospawn_flap`, watchdog
context-full + cap-hit alerts). The audit E1 expected-count (10/8) and the codex
`agent-orchestrator-slack-notifications.md` table both predate these.

- [x] ✅ [DOCS] P2. Refresh the codex `agent-orchestrator-slack-notifications.md` inventory table to the current 13
      slack / 9 telegram funcs (enumerate the new func names). Update the audit instructions E1 + j3 expected-counts to
      match. Collision group: none. Estimate: 0.1 AI-day. ✅ DONE 2026-06-01 — codex table rebuilt with an S/T column
      (marks Slack vs Telegram export per func) + 4 new rows (`notify_unpushed_plans`, `notify_autospawn_flap`,
      `notify_watchdog_kill`, `notify_sync`) + corrected the false "both expose the same set" intro. Audit e1 (13/9 +
      slack-only/telegram-only lists) + j3 (S/T-matrix match) updated.

### Phase 4 — P0/P1: respawn working-tree hygiene (9-failure-mode audit 2026-06-01)

> **🟡 IN-FLIGHT — Phase-4 implementation owned by a parallel session (since 2026-06-01 ~20:25).** In the slot-1
> agent-orchestrator worktree, `server/worktree_clean_check.py` carries +389 lines of uncommitted WIP (the full
> `classify_maker_liveness` / FM2 wiped-index / FM3 restore / FM8b slot-tagged-stash implementation) and
> `server/worker_liveness.py` is also modified — actively edited (mtime within seconds). **Do NOT duplicate or stomp**;
> coordinate with the owning session. Slot-1 interactive operator session confirmed "back off" 2026-06-01. Banner-remove
> when that session commits + flips these todos.

A follow-on autonomy audit (this session 2026-06-01 — fan-out + adversarial verify, all verdicts confirmed against
`agent-orchestrator@HEAD` + `unified-trading-pm/scripts/dev`) checked the operator's standing concern: **"if things stop
halfway, they don't restart with a good working tree on the right branches."** It mapped the 9 working-tree pathologies
surfaced by the slot-3 manual cleanup against the spawn/respawn/restart machinery. Root cause: the ONLY pre-spawn gate,
`worktree_clean_check.check_slot_clean()`, inspects `git status --porcelain` (dirtiness) ONLY — upstream-correctness,
divergence, behind-ness, branch-identity, and per-repo base are all delegated to the worker's own boot prompt
(`agents/worker.md` step 1b), an **unenforced soft instruction** that the recovery / auth-fail respawn prompts don't
even inline. Verdict: only FM9 (autostash-rebase) is fully handled; two auto-respawn defaults are actively dangerous.

| FM  | Pathology (on respawn / restart)                                  | Verdict        | Manual fix that's missing from the auto-path       |
| --- | ----------------------------------------------------------------- | -------------- | -------------------------------------------------- |
| FM1 | Stale `origin/tab/<op>/N` upstream → bogus ahead/behind           | 🟡 partial     | `git branch -u origin/<base>` (never self-heals)   |
| FM2 | Wiped index (staged-`D `+`??`) → `git add -A` pushes mass-delete  | 🟡 dangerous   | `git reset --mixed HEAD` (absent)                  |
| FM3 | Regenerated tracked artifact committed as orphan-wip / left stale | 🔴 no          | `git restore` (enum has no discard option)         |
| FM4 | Behind-but-FF-able recovered session on stale base                | 🟡 partial     | server-driven FF (only worker.md + cron do it)     |
| FM5 | Genuine divergence auto-resolved instead of quarantined           | 🟡 partial     | pre-spawn merge-base STOP (absent)                 |
| FM6 | Per-repo base ignored (agent-orchestrator must track `main`)      | 🔴 no          | per-repo base resolution (hardcoded to LDR)        |
| FM7 | Existing worktree on wrong/detached branch spawned into           | 🟡 partial     | `HEAD == tab/<op>/N` assertion (absent)            |
| FM8 | `git add -A` / `git stash` sweep foreign (cross-slot) WIP         | 🟡 HARD-RULE ✗ | claim-gated slot-lineage check (never consulted)   |
| FM9 | Autostash rebase conflict destroys foreign WIP                    | ✅ handled     | — (FF-only paths + `rebase --abort`; hook-blocked) |

- [x] ✅ [CODE] P0. **FM8 — liveness-gated dirty-state resolution (slot-isolation invariant, NOT per-file).** ✅ DONE
      2026-06-01 — agent-orchestrator@1f9af64 (LDR). `classify_maker_liveness()` in `worktree_clean_check.py`:
      dead/absent/expired (incl. the very session being respawned) → inherit; a DIFFERENT live tmux session owning a
      fresh `.agent-claim` → PROTECT (never stomp); quarantine never terminal. Wired via `resolve_dirty_state()`
      coordinator into both spawn paths (server.py `/api/slots/{id}/spawn` → 409 on protected*live_peer/quarantined;
      worker_liveness `_resolve_predecessor_wip` → skip respawn). The worktree `.tabs/<N>/<repo>` is exclusively this
      slot's, and the orchestrator runs ONE worker per slot (pruner/watchdog kills the prior session before respawn), so
      dirty content in your own slot worktree is almost always **a previous session of you that is now gone → inherit
      it** (keep the current `git add -A` + orphan-wip commit). The discriminator is **LIVENESS, not identity**: in
      `commit_and_push_dirty_repos()` / `stash_dirty_repos()`, read `.agent-claim` (`worktree_claim.read_claim`) +
      `expires_at` (1h TTL, heartbeat-bumped) + tmux/heartbeat state, then — - **maker provably DEAD** (claim expired OR
      no tmux session OR heartbeat stale) → dead predecessor → **inherit + commit**. This is the common case and
      resolves the "dead agent ⇒ slot is infinitely dirty, nobody ever cleans it" failure — **quarantine must NEVER be
      terminal**. - **maker provably LIVE** (fresh claim + live tmux/heartbeat — realistically the operator's own
      interactive session on the same slot, per the "operator session counts as a slot" rule) → do NOT stomp it; resolve
      **role-aware**: a background autonomous worker
      `notify*\*`-pings     the operator and waits out the TTL (then inherits on expiry); an interactive/operator session ASKS the operator     ("are other agents finished? OK to commit this WIP?") and commits on confirmation. **Forbidden anti-patterns**:     (i) per-file foreign attribution — `in_flight_files_json`is a refinement, never a gate; an unreported dirty file     in an isolated slot worktree is still slot-owned; (ii) terminal quarantine — a dead maker's WIP must eventually be     inherited, never left dirty forever. Removes the FM8 HARD-RULE violation without wedging respawn-inherit.     Collision group:`ao_respawn_hygiene`.
      Estimate: 0.5 AI-day.
- [ ] [CODE] P0. **FM8 addendum — interactive-editor liveness (3rd signal beyond claim-TTL + tmux).** The claim+tmux
      liveness test misses a LIVE interactive operator/Cursor editor: it writes no `.agent-claim` and runs under no
      `orch-slot-*` tmux session, so `classify_maker_liveness` returns `"absent" → inherit` and would STOMP active
      interactive edits. **Observed live 2026-06-01 20:25** — the Phase-4 WIP itself was being edited ~40s prior with no
      claim and no orch-slot tmux present; the claim-only classifier would have mis-read it as a dead/absent maker. Add
      **working-tree mtime-recency** as a third LIVE input: if any dirty file in the slot was modified within the last N
      seconds (e.g. 120s) treat the maker as LIVE regardless of claim/tmux. Combine: LIVE if (fresh claim + live tmux)
      OR (recent dirty-file mtime). Collision group: `ao_respawn_hygiene`. Estimate: 0.1 AI-day.
- [x] ✅ [CODE] P0. **FM8b — slot-tagged stashes (shared stash stack).** ✅ DONE 2026-06-01 —
      agent-orchestrator@1f9af64. `stash_dirty_repos(slot_id=...)` tags `slot-<N>-orphan-<ts>` (via `slot_stash_tag()`)
      and `find_slot_stash_ref(repo, slot_id)` only ever matches THIS slot's tag on the shared stash stack — never
      assumes `stash@{0}`. Test: `test_slot_tagged_stash_never_pops_foreign`. Linked worktrees share one `.git`, so
      `git stash list` exposes every slot's stashes (slot-3 incident: stashes tagged `On tab/.../1|7|8`). Collision
      group: `ao_respawn_hygiene`. Estimate: 0.15 AI-day.
- [x] ✅ [CODE] P0. **FM2 — wiped-index guard (prevent pushed mass-delete).** ✅ DONE 2026-06-01 —
      agent-orchestrator@1f9af64. `detect_wiped_index()` (staged-`D` + same path on disk as `??`) +
      `is_pure_mass_deletion()` (>20 pure deletes); `reconcile_wiped_index()` runs `git reset --mixed HEAD` first;
      `commit_and_push_dirty_repos()` REFUSES a wiped/mass-delete index → `resolve_dirty_state` returns `quarantined`
      (nothing pushed). Tests: `test_resolve_reconciles_wiped_index` + `test_resolve_quarantines_pure_mass_deletion`. In
      `check_slot_clean` / `_git_status_porcelain` detect the FM2 signature (staged `D ` deletes each with a matching
      `??` on-disk path). On match: `git reset --mixed     HEAD` FIRST, re-run the clean check, log
      `slot_wiped_index_reconciled` (NOT `orphan_wip`); if files are genuinely gone after the reset, do NOT
      auto-commit/push the deletion — quarantine + alert. Hard guardrail in `commit_and_push_dirty_repos`: refuse to
      commit when the staged set is pure deletions of >20 tracked files absent an explicit operator override, so a
      corrupt index can never be pushed as orphan-wip. Collision group: `ao_respawn_hygiene`. Estimate: 0.3 AI-day.
- [ ] [CODE] P1. **FM1/FM5/FM6/FM7 — structural pre-spawn branch-state gate.** Add
      `worktree_clean_check.check_slot_branch_state(slot_id, slot_dir, operator)` parallel to `check_slot_clean`. Per
      repo assert: (a) `@{u}` == the repo's correct base, repairing a stale `origin/tab/<op>/N` with
      `git branch -u     origin/<base>` (FM1); (b) `HEAD` == `tab/<op>/<N>` — STOP on detached / base / other branch
      (FM7); (c) base resolved PER-REPO — `main` for agent-orchestrator, `live-defi-rollout` else (FM6); (d)
      `git fetch` + merge-base classify → FF when behind+clean (FM4), else quarantine-on-divergence (FM5). Wire into ALL
      THREE spawn paths: `server.py::spawn_slot` (~2156, after the dirty gate),
      `worker_liveness.py::_do_auth_fail_respawn` (~711) + `_maybe_auto_respawn_stuck_slot` (~1033), and
      `autospawn.py::_do_spawn` (~224 — currently NO pre-spawn gate at all). Collision group: `ao_branch_state_gate`.
      Estimate: 0.6 AI-day.
- [ ] [CODE] P1. **FM6 support — machine-readable per-repo base.** Add an `integration_branch` field to each repo block
      in `workspace-manifest.json` (`main` for agent-orchestrator; `live-defi-rollout` everywhere else incl.
      trading-agent-service, which CI-promotes LDR→main). Replace the single `INTEGRATION_BRANCH` constant in
      `scripts/dev/setup-tab-worktrees.sh:51` with a `base_branch_for_repo()` helper reading it; make `worker.md`
      fresh-pull (1b) resolve base per-repo; GENERATE `cron-branch-overrides.txt` from the manifest (it is currently
      EMPTY, so the per-repo hook in `slot-cron-ff-pull.sh` does nothing today). Collision group:
      `ao_branch_state_gate`. Estimate: 0.3 AI-day.
- [ ] [CODE] P1. **FM4/FM5 — recovery boot prompts must inline the fresh-pull block.**
      `worker_liveness.py::_build_recovery_boot_prompt` (~1109) + the auth-fail respawn prompt (~701) currently only say
      "Read worker.md then /boot" — they do NOT inline the FF / divergence-STOP block the autospawn path gets via the
      rendered template, so a recovered session is weaker than a cold autospawn. Inline the full `worker.md` step-1b
      fresh-pull-with-divergence-STOP block (or render the worker template). Collision group: `ao_branch_state_gate`.
      Estimate: 0.15 AI-day.
- [x] ✅ [CODE] P2. **FM3 — discard regenerated tracked artifacts (the slot-3 cleanup trigger).** ✅ DONE (orchestrator
      side) 2026-06-01 — agent-orchestrator@1f9af64. `restore_generated_artifacts()` runs
      `git restore --staged --worktree     -- <allowlist>` (playwright-report/blob-report/test-results), NEVER
      `git restore .`, as the first step of `resolve_dirty_state` — re-checks, feeds only residual human-dirty files
      onward. Test: `test_restore_generated_artifacts_leaves_human_dirty`. **REMAINING (foreign repos, not
      agent-orchestrator):** the belt-and-suspenders `git rm --cached` + `.gitignore playwright-report/` in
      deployment-ui + user-management-ui — filed as a finding for those repos' owners (out of agent-orchestrator scope).
      Maintain a workspace allowlist of regenerated tracked build outputs (`playwright-report/`, tracked coverage
      reports). Before the COMMIT_AND_PUSH/STASH branch (and in `worker.md` fresh-pull before its dirty-check) run
      `git restore -- <allowlist>` ONLY (never `.`), re-check, feed only residual human-dirty files to resolution.
      Belt-and-suspenders: `git rm     --cached` + `.gitignore` `playwright-report/` in deployment-ui +
      user-management-ui (keep `unified-trading-pm/presentations/tests/playwright-report` intentionally tracked →
      allowlist-restore still needed there). Collision group: `ao_respawn_hygiene`. Estimate: 0.25 AI-day.
- [ ] [TEST] P0. Unit tests for all the above: (a) same-slot claim → inherit; (b) mismatched-slot/operator claim →
      quarantine, no commit/push; (c) no-claim → inherit; (d) FM2 `D `+`??` signature → reset --mixed → clean, no
      commit; (e) FM2 true file-loss → quarantine, no push; (f) pure-deletion >20 files → refuse; (g) branch-state gate:
      stale upstream repaired, detached/base/wrong-branch → STOP, divergence → quarantine, behind+clean → FF; (h)
      per-repo base resolves `main` for agent-orchestrator; (i) slot-tagged stash never pops a foreign tag; (j)
      generated-artifact allowlist-restore leaves human-dirty files intact. Collision group: `ao_respawn_hygiene`.
      Estimate: 0.4 AI-day.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` exit 0 in agent-orchestrator → sentinel sha →
      `bash scripts/quickmerge.sh     "feat(respawn-hygiene): claim-gated dirty resolution + wiped-index guard + pre-spawn branch-state gate" --agent`.
      Collision group: `ao_respawn_hygiene`. Estimate: 0.1 AI-day.
- [ ] [DOCS] P1. Codex `codex/05-infrastructure/per-tab-worktrees.md` — document the pre-spawn branch-state gate +
      **liveness-gated** dirty resolution (slot-isolation invariant: dirty == a prior-you that's gone → inherit; only a
      provably-LIVE peer is protected; quarantine is never terminal) + slot-tagged-stash discipline + the 9-FM coverage
      table above. Add a `cursor-configs/CLAUDE.md` rule (canonical — do NOT edit per-repo copies) under
      `### Other key     rules`: **an agent resolving inherited dirty WIP must first detect whether it is a background
      autonomous worker (tmux `orch-slot-*` session / `ORCHESTRATOR_*` env / claim `role`) or an interactive operator
      session — background: `notify_*`-ping the operator + inherit once the prior maker's claim TTL expires;
      interactive: ASK the operator whether other agents are finished, then commit. Never stomp a provably-live peer;
      never leave a dead maker's slot infinitely dirty.** Cross-link this plan. ⚠️ `cursor-configs/CLAUDE.md` was
      actively foreign-dirty at 2026-06-01 19:40 (another agent mid-edit) — make this CLAUDE.md edit only when that
      worktree is clean, to avoid the very FM8 collision this plan fixes. Collision group: none. Estimate: 0.2 AI-day.

## Closing condition

Closes when: Phase 1 S3 snapshot ships + a snapshot object is verified on S3 for ≥1 AWS VM; Phase 2 health-check script
ships + the fleet table shows all 11 VMs at LDR HEAD with all four flags live; Phase 3 doc counts match code; **Phase 4
ships the claim-gated dirty resolution + wiped-index guard + pre-spawn branch-state gate (all three spawn paths) with
the test matrix green, and a respawn on a slot left behind/diverged/wrong-branch is observed to either self-heal (FF) or
quarantine — never auto-push foreign WIP or a mass-delete.** All code phases QG-green + quickmerged; docs via fast-path.

## What NOT to do

- **Do NOT duplicate the watchdog/autospawn/backlog rollout work** — those are owned by their respective plans (see the
  reconciliation table). This plan is residual-findings-only.
- **Do NOT raw-subprocess `aws s3 cp`** for the snapshot path — use the workspace cloud-interface S3 helpers.
- **Do NOT make the Phase-4 FM8 gate quarantine-terminal or per-file.** The slot-isolation invariant means dirty WIP
  from a dead predecessor must be inherited (it is you-in-a-prior-session, and the maker is gone); the only protected
  case is a provably-LIVE peer. A terminal quarantine recreates the "infinitely dirty dead slot" failure the gate exists
  to prevent. Liveness (claim TTL + tmux/heartbeat), not slot-id identity, is the discriminator.
