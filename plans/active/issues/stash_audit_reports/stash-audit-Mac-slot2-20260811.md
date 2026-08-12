---
doc_type: issue
title: "Stash audit — host Mac-slot2 — 2026-08-11"
summary: >-
  Auto-generated dry-run stash-audit output (34 stashes across 10 repos, 33 genuine-WIP, 1 auto-droppable foreign-park),
  read before touching any stash per the collision-warning handoff this session inherited. Diagnostic input for the
  standing stash_pile_workspace_cleanup_2026_06_03.md effort.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [admin]
tags: [stash-audit, workspace-hygiene, generated-report]
related: [stash_pile_workspace_cleanup_2026_06_03]
created: 2026-08-11
author: claude-agent
source: "Auto-generated dry-run stash audit, 2026-08-11 interactive session, slot 2"
priority: P3
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# Stash audit — host `Mac-slot2` — 20260811

- Mode: **DRY-RUN (no drops)**
- Workspace: `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/2`
- Archive root: `/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/2/.stash-archive-Mac-slot2-20260811` (+
  `refs/stash-archive/*` inside each repo's .git)
- Classifier: strict / conservative (see plan stash_pile_workspace_cleanup_2026_06_03.md)

## Workspace summary

| repo                     | stashes | auto-droppable | genuine-WIP | base-verified |
| ------------------------ | ------- | -------------- | ----------- | ------------- |
| agent-orchestrator       | 1       | 0              | 1           | yes           |
| alerting-service         | 1       | 0              | 1           | yes           |
| deployment-api           | 1       | 0              | 1           | yes           |
| deployment-service       | 2       | 0              | 2           | yes           |
| features-service         | 1       | 0              | 1           | yes           |
| greeks-service           | 1       | 0              | 1           | yes           |
| market-tick-data-service | 7       | 0              | 7           | yes           |
| system-integration-tests | 1       | 0              | 1           | yes           |
| unified-trading-library  | 1       | 0              | 1           | yes           |
| unified-trading-pm       | 18      | 1              | 17          | yes           |
| **TOTAL**                | **34**  | **1**          | **33**      |               |

## agent-orchestrator

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/main` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age        | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ---------- | ----- | --- |
| stash@{0} | `7d2ca39d4` | genuine-WIP | surface | `autostash`  | 3 days ago | 5     | 4   |

## alerting-service

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age        | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ---------- | ----- | --- |
| stash@{0} | `26d550589` | genuine-WIP | surface | `autostash`  | 2 days ago | 2     | 0   |

## deployment-api

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age        | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ---------- | ----- | --- |
| stash@{0} | `4fdd189b6` | genuine-WIP | surface | `autostash`  | 2 days ago | 4     | 3   |

## deployment-service

- stashes: **2** · auto-droppable: **0** · genuine-WIP survivors: **2**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age         | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ----------- | ----- | --- |
| stash@{0} | `3abaa30fd` | genuine-WIP | surface | `autostash`  | 2 days ago  | 3     | 0   |
| stash@{1} | `099cb06c3` | genuine-WIP | surface | `autostash`  | 2 weeks ago | 1     | 0   |

## features-service

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age         | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ----------- | ----- | --- |
| stash@{0} | `61867c3d0` | genuine-WIP | surface | `autostash`  | 13 days ago | 10    | 10  |

## greeks-service

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age          | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ------------ | ----- | --- |
| stash@{0} | `2aa5f8afe` | genuine-WIP | surface | `autostash`  | 17 hours ago | 2     | 0   |

## market-tick-data-service

- stashes: **7** · auto-droppable: **0** · genuine-WIP survivors: **7**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch        | age          | files | .py |
| --------- | ----------- | ----------- | ------- | ------------------- | ------------ | ----- | --- |
| stash@{0} | `191340a93` | genuine-WIP | surface | `autostash`         | 34 hours ago | 11    | 11  |
| stash@{1} | `ef3a706b6` | genuine-WIP | surface | `live-defi-rollout` | 3 days ago   | 1     | 0   |
| stash@{2} | `fb10b0849` | genuine-WIP | surface | `autostash`         | 6 days ago   | 4     | 1   |
| stash@{3} | `326b2fc45` | genuine-WIP | surface | `autostash`         | 12 days ago  | 7     | 7   |
| stash@{4} | `bd254bc48` | genuine-WIP | surface | `autostash`         | 12 days ago  | 6     | 6   |
| stash@{5} | `c673ffc05` | genuine-WIP | surface | `live-defi-rollout` | 13 days ago  | 5     | 5   |
| stash@{6} | `452dfe7e4` | genuine-WIP | surface | `live-defi-rollout` | 2 weeks ago  | 1     | 1   |

## system-integration-tests

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch | age        | files | .py |
| --------- | ----------- | ----------- | ------- | ------------ | ---------- | ----- | --- |
| stash@{0} | `623b08b5a` | genuine-WIP | surface | `autostash`  | 3 days ago | 1     | 0   |

## unified-trading-library

- stashes: **1** · auto-droppable: **0** · genuine-WIP survivors: **1**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash     | sha         | class       | action  | owner-branch        | age        | files | .py |
| --------- | ----------- | ----------- | ------- | ------------------- | ---------- | ----- | --- |
| stash@{0} | `ed67ecabd` | genuine-WIP | surface | `live-defi-rollout` | 3 days ago | 1     | 0   |

## unified-trading-pm

- stashes: **18** · auto-droppable: **1** · genuine-WIP survivors: **17**
- base ref: `origin/live-defi-rollout` · base-verified: yes

| stash      | sha         | class        | action    | owner-branch        | age          | files | .py |
| ---------- | ----------- | ------------ | --------- | ------------------- | ------------ | ----- | --- |
| stash@{0}  | `1072690a2` | genuine-WIP  | surface   | `autostash`         | 6 hours ago  | 1     | 0   |
| stash@{1}  | `03ed99794` | genuine-WIP  | surface   | `live-defi-rollout` | 10 hours ago | 4     | 0   |
| stash@{2}  | `f9e63cf8a` | genuine-WIP  | surface   | `live-defi-rollout` | 10 hours ago | 3     | 0   |
| stash@{3}  | `2ef15e5e3` | foreign-park | auto-drop | `live-defi-rollout` | 10 hours ago | 4     | 1   |
| stash@{4}  | `3883ba381` | genuine-WIP  | surface   | `live-defi-rollout` | 10 hours ago | 3     | 1   |
| stash@{5}  | `31050e237` | genuine-WIP  | surface   | `live-defi-rollout` | 10 hours ago | 10    | 2   |
| stash@{6}  | `fb0b238bb` | genuine-WIP  | surface   | `live-defi-rollout` | 11 hours ago | 9     | 3   |
| stash@{7}  | `046d8c08f` | genuine-WIP  | surface   | `live-defi-rollout` | 11 hours ago | 10    | 3   |
| stash@{8}  | `45ba70a3f` | genuine-WIP  | surface   | `autostash`         | 14 hours ago | 12    | 1   |
| stash@{9}  | `c0cf2d942` | genuine-WIP  | surface   | `autostash`         | 20 hours ago | 11    | 1   |
| stash@{10} | `3cb905817` | genuine-WIP  | surface   | `autostash`         | 21 hours ago | 6     | 0   |
| stash@{11} | `19f594182` | genuine-WIP  | surface   | `autostash`         | 23 hours ago | 7     | 0   |
| stash@{12} | `3c4c85fd3` | genuine-WIP  | surface   | `autostash`         | 34 hours ago | 17    | 1   |
| stash@{13} | `eb9462514` | genuine-WIP  | surface   | `autostash`         | 34 hours ago | 19    | 1   |
| stash@{14} | `a68cac08e` | genuine-WIP  | surface   | `autostash`         | 2 days ago   | 22    | 0   |
| stash@{15} | `b82b5998e` | genuine-WIP  | surface   | `autostash`         | 2 days ago   | 5     | 0   |
| stash@{16} | `b233fbc29` | genuine-WIP  | surface   | `autostash`         | 2 days ago   | 1     | 0   |
| stash@{17} | `d5e1aa24c` | genuine-WIP  | surface   | `autostash`         | 2 days ago   | 8     | 0   |
