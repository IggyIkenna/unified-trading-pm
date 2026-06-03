---
title: "Workspace-wide git stash pile audit + cleanup — per-host runbook"
created: 2026-06-03
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P3
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
source:
  - plans/active/issues/shared_stash_pile_archive_cleanup_2026_06_01.md
  - "git stash list across all repos on the planning host (59 stashes / 16 repos, 2026-06-03)"
locked_by: live-defi-rollout
locked_since: 2026-06-03
---

# Workspace-wide git stash pile — audit + cleanup (per-host runbook)

## Why this plan

The 2026-06-01 cleanup (`shared_stash_pile_archive_cleanup_2026_06_01.md`) archived + cleared a **91-deep** stash pile
in `unified-trading-pm` on one host. Two days later that same repo's pile is **back to 31**, and a host-wide scan shows
**59 stashes across 16 repos on the planning host alone** — so this is (a) workspace-wide, not PM-only, and (b)
continuous, not one-shot. We need a **reusable, archive-first, conservative tool** that any host owner runs locally,
plus a fan-out so every host (VMs + operator laptops) gets swept once.

### Mental model — the visibility boundary is the HOST, not the person

`git stash` writes to `refs/stash` and is **never pushed**. Git worktrees on one host share a single common `.git`, so
all of a host's slot worktrees see the same `refs/stash` per repo. **You cannot reach a teammate's stashes from your
machine.** Therefore the unit of work is **(host × repo)**, and the plan fans out **one todo per host**; each host owner
runs the identical script locally.

### Snapshot — planning host, 2026-06-03 (grounds the plan; not authoritative for other hosts)

| Repo                                                                                                                     | Stashes |     | Repo                           | Stashes |
| ------------------------------------------------------------------------------------------------------------------------ | ------- | --- | ------------------------------ | ------- |
| unified-trading-pm                                                                                                       | 31      |     | features-service               | 2       |
| execution-service                                                                                                        | 5       |     | client-reporting-api           | 2       |
| instruments-service                                                                                                      | 3       |     | deployment-api                 | 2       |
| alerting-service                                                                                                         | 2       |     | market-data-processing-service | 2       |
| trading-agent-service                                                                                                    | 2       |     | unified-trading-system-ui      | 2       |
| agent-orchestrator / ibkr-gateway-infra / ml-service / strategy-service / system-integration-tests / unified-trading-api | 1 each  |     |                                |         |

**TOTAL: 59 / 16 repos.** Other hosts (10 epic VMs + orchestrator VM + Ikenna laptop + Harsh laptop) are unknown until
each runs the audit.

## Safety spine (non-negotiable — inherited from the 2026-06-01 doc)

1. **Archive before touching anything** — the proven 3-way archive: gc-proof refs `refs/stash-archive/*`, a portable
   `.bundle`, and a `manifest.txt` (index → sha → label). Per repo, per host.
2. **Dry-run by default** — the script prints classifications and drops nothing unless `--apply` is passed. Smoke-test
   the classifier on one repo before sweeping the host (per smoke-test-before-scale).
3. **Conservative auto-drop only** — auto-drop is limited to the three provably-safe classes below. **All genuine WIP is
   surfaced to its owner**, never auto-dropped or auto-applied (per no-blind-edits / no-unconditional-stash-pop).
4. **Confirmation window before purge** — archives stay ~1 week after the sweep; purge only if nobody asked to restore.

## Triage taxonomy (the classifier)

Per stash, compute: index, sha, **branch-of-origin** (parsed from `WIP on <branch>` / `On <branch>`), **age** (stash
commit date), file count, `.py` count, and a class:

| Class                                | Mechanical test                                                                                                                                                | Action                                                                                                  |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **empty**                            | `git stash show --stat <ref>` lists 0 files                                                                                                                    | **auto-drop**                                                                                           |
| **redundant**                        | stash's tree diffed against the repo base (`origin/live-defi-rollout`, or `origin/main` for agent-orchestrator) has **no net change** — content already merged | **auto-drop**                                                                                           |
| **foreign-park / autostash residue** | label matches `foreign-*` / autostash pattern **AND** tree is already an ancestor of base (no unique content)                                                  | **auto-drop**                                                                                           |
| **genuine-WIP**                      | net diff vs base exists and is not attributable to an empty/redundant/park class                                                                               | **surface in report → owner confirms** (drop, or inherit-and-commit onto its own `tab/<op>/<N>` branch) |

> **Conservative scope chosen 2026-06-03:** even genuine WIP from an apparently-dead local session is **surfaced, not
> auto-inherited**. The owner (or operator) decides drop-vs-inherit. The script never auto-commits another slot's WIP.

## Phases

### Phase 1 — build + smoke-test the script (this host)

- [ ] [INFRA] P3. Write `unified-trading-pm/scripts/dev/audit-stash-pile.sh` (home: alongside the other per-host
      slot-hygiene scripts — `slot-cron-ff-pull.sh`, `verify-slot-host-symmetry.sh`). Behaviour: iterate every repo
      under `$WORKSPACE_ROOT` with a non-empty `refs/stash`; per repo → archive 3-way under
      `.stash-archive-<host>-<date>/` + `refs/stash-archive/*`; classify each stash per the taxonomy; in `--apply` mode
      auto-drop only empty/redundant/foreign-park; always write a per-host markdown report
      `.stash-audit-<host>-<date>.md` listing every genuine-WIP survivor with owner branch + diffstat + age. **Default =
      dry-run** (classify + report, drop nothing). Flags: `--apply`, `--repo <name>` (single-repo smoke), `--base <ref>`
      override. Base ref resolves per-repo: `origin/main` for agent-orchestrator, `origin/live-defi-rollout` otherwise.
      — owner: planning-host
- [ ] [INFRA] P3. Smoke-test: run `--dry-run --repo unified-trading-pm` on this host; eyeball the 31-stash
      classification; hand-verify 2-3 "redundant" calls actually have no net diff vs LDR before trusting the auto-drop
      class. — owner: planning-host

### Phase 2 — sweep this host

- [ ] [INFRA] P3. Run `audit-stash-pile.sh --apply` across all repos on the planning host; commit the generated
      `.stash-audit-<host>-2026_06_03.md` report (path under PM repo, or attach to this plan). Auto-drop count +
      survivor count recorded in the report. Do NOT purge archives yet. — owner: planning-host

### Phase 3 — fan out to every other host (the todo IS the dispatch)

Each host owner runs the identical script locally and commits its report. Cold-start context for the worker: read
`SUB_AGENT_MANDATORY_RULES.md`; the script is dry-run by default; never `--apply` without eyeballing the dry-run first;
surface — do not auto-drop — genuine WIP.

- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-defi**; commit report. — owner: vm-defi
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-cefi**; commit report. — owner: vm-cefi
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-tradfi**; commit report. — owner: vm-tradfi
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-sports**; commit report. — owner: vm-sports
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-prediction**; commit report. — owner: vm-prediction
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-ml**; commit report. — owner: vm-ml
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-trading-core**; commit report. — owner: vm-trading-core
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-operator-ops**; commit report. — owner: vm-operator-ops
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-cross-cutting**; commit report. — owner: vm-cross-cutting
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **vm-orchestrator**; commit report. — owner: vm-orchestrator
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **Ikenna laptop**; commit report. — owner: ikenna-laptop
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **Harsh laptop**; commit report. — owner: harsh-laptop

### Phase 4 — owner review of genuine-WIP survivors + final purge

- [ ] [INFRA] P3. Aggregate all per-host reports; for each genuine-WIP survivor, ping its branch owner to decide drop vs
      inherit-and-commit (`chore(orphan-wip)` onto its own `tab/<op>/<N>` branch). Owners resolve within the
      confirmation window. — owner: planning-host
- [ ] [INFRA] P3. After the ~1-week confirmation window (target **2026-06-10**), per host: if no restore was requested,
      purge that host's archive —
      `git for-each-ref refs/stash-archive/ --format='%(refname)' | xargs -n1 git update-ref -d` then
      `rm -rf .stash-archive-<host>-<date>/`. — owner: each host

### Phase 5 — prevent regrowth (codify)

- [ ] [INFRA] P3. **NICE-TO-HAVE.** The pile regrew 0→31 in PM in 2 days, so the autostash/foreign-park churn is
      structural. Investigate folding a `--max-stash-age` warning into `slot-git-status-report.sh` (or a weekly cron) so
      a host pings its inbox when `refs/stash` exceeds N or a stash ages past M days, instead of relying on manual
      sweeps. Capture decision in `codex/05-infrastructure/per-tab-worktrees.md`. — owner: planning-host

## Relationship to the 2026-06-01 issue doc

`shared_stash_pile_archive_cleanup_2026_06_01.md` covered ONLY `unified-trading-pm` on ONE host and has its own
2026-06-08 purge window — it proceeds independently. This plan generalises its proven archive-first pattern to all repos
× all hosts and supersedes it as the canonical recurring runbook once the script lands. Do not duplicate the PM-specific
purge here.
