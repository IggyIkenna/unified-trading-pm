---
name: agent_orchestrator_backlog_state_alignment_2026_05_29
title: "agent-orchestrator backlog state alignment — prune zombies, fix never-deletes regen, codify CI-safe rollout"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P0
status: active
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
created: 2026-05-29
last_updated: 2026-05-29
locked_by: live-defi-rollout
locked_since: 2026-05-29
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md
related_plans:
  - plans/active/api_host_chronic_impairment_2026_05_29.md
  - plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md
  - plans/active/cross_operator_auth_failover_2026_05_29.md
---

## Why this exists

A 2026-05-29 sweep (operator + slot-1 main) discovered the agent-orchestrator backlog counters reported by every fleet
host are **95% lies**. The dashboard says "vm-cefi queued = 6783"; SQL says **271 tasks in current yaml + 6513 zombie
state.db rows from past regen ticks**.

The root cause is a documented intentional choice in `agent-orchestrator/server/regen_backlog_from_plan.py`:

```python
# line 12 + 206 of regen_backlog_from_plan.py
# - Never deletes existing tasks.
# Never deletes existing tasks. Only adds new ones.
```

Months of plan-flips have accumulated ~55,000 zombie SQL rows fleet-wide. Side effects:

1. **Heartbeat-driven dispatch decisions are wrong** — the dispatcher sees fake huge queues.
2. **Spawn-decision logic is wrong** — operators see "5 idle VMs with 6000+ queued" and conclude "spawn workers" when
   the real per-VM canonical queue is ~270.
3. **vm-ml and vm-trading-core's `backlog.yaml` is 21× the canonical** — 142,108 / 136,659 lines respectively vs 6,397
   lines on the 7 aligned VMs. Their regen is producing 6,595 / 6,347 task entries vs the 271 the others produce. Root
   cause TBD (likely per-VM plan scope or wider epic fan-out).
4. **api-host's yaml is essentially empty (19 lines)** but its state.db has 5,609 stale rows. The central host's regen
   never updates the yaml.
5. **Workers picking up tasks that no longer exist** — wasted cycles.

## What the fix looks like

Three layers, each shippable independently. **Layered to be safe for CI/CD + autonomous-worker race**:

| Layer | What | CI affected? | Race risk | Worker collision_group |
|---|---|---|---|---|
| **L1** — DB zombie prune | One-shot SQLite DELETE on each VM | NO (per-VM SSM action, no PR) | None | n/a (operator-side) |
| **L2** — regen code: `--prune-stale` flag | New flag in `regen_backlog_from_plan.py` that deletes (a) yaml entries not in current plans + (b) state.db rows not in new yaml. Default OFF; enabled per-VM via systemd env | YES (PR against agent-orchestrator, must pass QG) | One PR at a time on agent-orchestrator | `ao_regen_prune_code` |
| **L3** — per-VM rollout of prune flag | Systemd drop-in env `ORCHESTRATOR_REGEN_PRUNE_STALE=true` on each VM. Restart orchestrator. Wait one tick. Verify yaml + db shrink. | NO (SSM action) | One VM at a time | n/a (operator-side) |
| **L4** — root-cause vm-ml + vm-trading-core 21× yaml bloat | Investigate why regen picks up 6,595/6,347 vs 271 tasks. Likely per-VM plan-scope logic in regen treats them as workspace-aggregator role. | YES (likely a PR) | One PR at a time | `ao_regen_scope_code` |
| **L5** — codify in CLAUDE.md | New HARD RULE: "regen is authoritative — yaml + db must match plans. No zombies." + pointer to runbook | YES (PR against unified-trading-pm; uses docs-fast-path) | None | n/a (small docs change) |

## CI-safety contract (HARD)

Every code-change phase below MUST:

1. **Pass quality-gates.sh exit 0** in the touched repo BEFORE push (per workspace HARD RULE `Quality Gates Are A Merge Prerequisite`).
2. **Write `.qg_last_passed_sha` sentinel** then immediately run `bash scripts/quickmerge.sh "msg" --agent` (per Two-pass discipline in CLAUDE.md).
3. **Use Commit + Push + Flip same-turn**: code commit + plan-flip commit MUST land in the same agent turn (`docs(plans):` prefix on the flip).
4. **Honor `collision_group`** in each task so only ONE worker at a time picks it up (avoids two workers PR'ing the same flag).
5. **No `--no-verify`** unless the prek-auto-restore symptom is observed (per foot-gun #4).

## Phases

### Phase 0 — Audit baseline (DONE 2026-05-29)

Per-VM zombie count + yaml size sweep already captured. Snapshot is in this plan's preamble. No further work.

- [x] [DIAG] P0. Per-VM zombie audit complete — table embedded in this plan body — slot-1-main@2026-05-29

### Phase 1 — L1 DB zombie prune (one-shot, per-VM)

Each VM runs a SQLite script that deletes ONLY:

- `status = 'queued'` AND
- `dispatched_to IS NULL` AND
- `task_id NOT IN (SELECT id FROM current backlog.yaml)`

Done-zombies (status='done') and dispatched-zombies (worker may be running) are PRESERVED for audit history + safety.

- [x] ✅ [SCRIPT] [AGENT-AUTO] P0. Write `unified-trading-pm/scripts/orchestrator/prune_state_db_zombies.py` — reads `backlog.yaml`, scans `state.db` `tasks` table, prints (current count, zombie count, safe-to-delete count). Default DRY-RUN; `--exec` to actually delete. Affinity: any slot. Collision group: none. Estimate: 0.1 AI-day. **DONE 2026-05-29** (slot-9). Dry-run against api-host confirms: 5,474 zombie rows identified (backlog.yaml has 0 tasks on this host). Usage: `python3 scripts/orchestrator/prune_state_db_zombies.py [--exec] [--db PATH] [--backlog PATH]`. Chunked DELETE (500/batch) stays under SQLite 999-var limit. Never touches done/dispatched rows.
- [x] ✅ [SCRIPT] [AGENT-AUTO + OPERATOR-SSM] P0. Deploy + run prune script on all 11 orchestrator hosts via parallel SSM `bash scripts/orchestrator/prune_state_db_zombies.py --exec`. Verify before/after counts. Affinity: vm-orchestrator owner. Collision group: `ao_prune_l1_rollout`. Estimate: 0.1 AI-day. **DONE 2026-05-29** — two-part rollout: (a) slot-9 worker ran prune on api-host locally (5,474 zombies → 0). (b) Operator (slot-1-laptop, admin SSM creds) fired `prune_state_db_zombies.py --exec` via inline AWS SSM SendCommand on the 10 remote VMs in parallel; all returned Success. Total fleet zombies eliminated: **45,762**. Per-VM evidence: vm-orchestrator 6,667 deleted (6956→289 total); vm-defi 6,481 (6773→292); vm-cefi 6,510 (6799→289); vm-tradfi 6,518 (6807→289); vm-sports 6,015 (6304→289); vm-prediction 1,365 (6711→5346, mostly done/dispatched preserved); vm-ml 3,306 (9979→6673); vm-trading-core 1,183 (9733→8550); vm-operator-ops 1,187 (6112→4925); vm-cross-cutting 6,530 (6819→289). Every VM's done + dispatched counts preserved bit-perfect (safety contract honored).
- [x] ✅ [VERIFY] [OPERATOR-SSM] P0. Confirm fleet/summary `backlog_queued` per VM drops post-prune — done by direct SQLite COUNT BEFORE/AFTER on each VM rather than waiting for heartbeat refresh (faster + authoritative). Post-prune queued counts: api-host=0, vm-orchestrator=288, vm-defi=289, vm-cefi=288, vm-tradfi=288, vm-sports=288, vm-prediction=93 (large yaml + many done), vm-ml=6,591 (canonical large scope — flagged for L4 investigation), vm-trading-core=6,154 (canonical large scope — flagged for L4 investigation), vm-operator-ops=273, vm-cross-cutting=289. Numbers now match yaml content within ±5 (regen-tick lag). Fleet summary will catch up on next heartbeat. **45,762 zombies eliminated. ~270 canonical per VM confirmed.** vm-ml + vm-trading-core 21× anomaly remains (per Phase 4 design) — needs codebase fix, not data fix.

### Phase 2 — L2 add `--prune-stale` flag to regen code (single PR)

Code change in `agent-orchestrator/server/regen_backlog_from_plan.py`:

1. Add `--prune-stale` CLI flag (default `False` for backwards compatibility).
2. When set: after computing new task set from plans, DELETE yaml entries whose IDs are not in the new set + DELETE state.db rows where `task_id NOT IN new_set AND status='queued' AND dispatched_to IS NULL`.
3. Always emit summary metric: `regen_pruned_yaml=N regen_pruned_db=M` to journal.
4. Add `ORCHESTRATOR_REGEN_PRUNE_STALE` env var read on PlanRegenLoop init.

- [ ] [CODE] P0. Add `--prune-stale` flag implementation in `regen_backlog_from_plan.py`. Unit tests + idempotency check (re-run on already-pruned state → no-op). Affinity: agent-orchestrator-familiar slot. Collision group: `ao_regen_prune_code`. Estimate: 0.3 AI-day.
- [ ] [TEST] P0. Unit test for regen with `--prune-stale=true`: seed yaml + state.db with 1 current task + 3 zombies → run → assert 0 zombies + current task preserved. Test runs via `pytest agent-orchestrator/tests/` in QG. Collision group: `ao_regen_prune_code`. Estimate: 0.1 AI-day.
- [ ] [QG] P0. `bash scripts/quality-gates.sh` exit 0 in agent-orchestrator. Sentinel sha written. Then `bash scripts/quickmerge.sh "feat(regen): --prune-stale flag — kill zombie backlog rows" --agent`. PR merges to staging then to LDR. Collision group: `ao_regen_prune_code`. Estimate: 0.1 AI-day.

### Phase 3 — L3 per-VM rollout of prune flag (post-merge)

After Phase 2 PR lands on LDR, autonomous pm-pull.timer propagates the new agent-orchestrator HEAD to all 11 VMs.
Then per-VM enable the flag via systemd drop-in + restart orchestrator. SSM-driven, one VM at a time (so a bug in
Phase 2 doesn't melt the fleet).

- [ ] [SCRIPT] P0. Write `unified-trading-pm/scripts/orchestrator/enable_prune_stale.sh` — SSM script that writes `/etc/systemd/system/orchestrator.service.d/prune-stale.conf` with `Environment=ORCHESTRATOR_REGEN_PRUNE_STALE=true` then `systemctl daemon-reload + restart orchestrator`. Collision group: none. Estimate: 0.05 AI-day.
- [ ] [SCRIPT] P0. Roll the flag to all 11 VMs **sequentially** (NOT parallel): vm-orchestrator first → wait 1 regen cycle → verify counts drop → vm-cefi → … → vm-cross-cutting last. Document each VM's pre/post numbers in this plan. Collision group: `ao_prune_l3_rollout`. Estimate: 0.2 AI-day.
- [ ] [VERIFY] P0. After all 11 VMs rolled: fleet/summary `backlog_queued` for each VM matches `/api/backlog` total (no drift). Numbers should stabilize at ~270 (small VMs) or whatever the canonical scope produces for vm-ml/vm-trading-core post-L4. Collision group: none. Estimate: 0.1 AI-day.

### Phase 4 — L4 investigate vm-ml + vm-trading-core 21× yaml bloat (research-then-fix)

vm-ml backlog.yaml = 142,108 lines (6,595 tasks).
vm-trading-core backlog.yaml = 136,659 lines (6,347 tasks).
All other VMs = 6,397 lines (271 tasks).

Either (a) per-VM plan-scope logic in regen treats these two as workspace-aggregator roles, or (b) the same plan
gets imported 24×.

- [ ] [RESEARCH] P1. Read `regen_backlog_from_plan.py` to find per-VM scope logic. Capture: where does it decide "which plans does this VM own"? Is there an `assigned_vm` filter? If so why does it produce 21× for these two VMs? Compare regen output on vm-cefi vs vm-ml side-by-side. Affinity: agent-orchestrator-familiar slot. Collision group: `ao_regen_scope_code`. Estimate: 0.3 AI-day.
- [ ] [CODE] P1. Fix the per-VM scope bug surfaced in research phase. Could be filter logic, dedup logic, or epic-fan-out logic. Write a unit test reproducing the 21× bloat with current plan set. Then fix + verify. QG green + quickmerge. Collision group: `ao_regen_scope_code`. Estimate: 0.5 AI-day.
- [ ] [VERIFY] P1. After fix lands + propagates via pm-pull: vm-ml backlog.yaml line count drops from 142k to ~6k (matching the other VMs). vm-trading-core similar. Same canonical task count visible on all 11 VMs. Collision group: none. Estimate: 0.1 AI-day.

### Phase 5 — L5 codify in CLAUDE.md (small docs PR, fast-path)

- [ ] [DOCS] P0. Add to `unified-trading-pm/.claude/CLAUDE.md` under `### Other key rules`: **"Orchestrator regen is authoritative — yaml + state.db must match current plans. No zombies. `ORCHESTRATOR_REGEN_PRUNE_STALE=true` is the default everywhere."** Cross-link this plan. Collision group: none. Estimate: 0.05 AI-day.
- [ ] [DOCS] P1. Add codex doc `codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` — the full architecture: regen lifecycle, yaml⇆state.db invariants, audit recipe, recovery if drift detected. Collision group: none. Estimate: 0.1 AI-day.
- [ ] [QG] P0. PM PR via fast-path (docs change → targets `main`). Verify `gh run list --branch main` shows PR-trigger CI run; if checks fail, fix root cause. Collision group: none. Estimate: 0.05 AI-day.

## What NOT to do

- **Do NOT delete done-zombies** — they are audit history.
- **Do NOT delete dispatched-zombies** — a worker may be running them. Mark `lost_workers` for dispatched rows where `dispatched_at < 24h ago` and add a separate cleanup pass after Phase 3 stabilizes.
- **Do NOT roll Phase 3 in parallel across all 11 VMs** — one bad regen tick + 11 broken hosts = self-inflicted outage. Sequential rollout is required.
- **Do NOT skip the unit test** on Phase 2 — a regression here destroys real task data on every VM.
- **Do NOT bypass `quickmerge --agent`** — the SHA sentinel is the only safety net against CI race conditions.

## Verification — fleet honesty post-rollout

Captured at plan-completion (final ✅):

- All 11 VMs report `fleet/summary backlog_queued` matching their `/api/backlog` count within ±5 tasks (regen tick lag).
- vm-ml + vm-trading-core yaml line count drops from 142k/136k to ~6k.
- api-host yaml regenerates from 19 lines to a non-empty canonical scope (or removed from the regen loop if api-host is a non-executing planning host).
- Fleet dashboard shows realistic queue depths. Operators stop seeing fake "30,000 queued" numbers.

## Continuous verification

Add to every PR review: if PR touches backlog.yaml or regen code, reviewer MUST verify the `regen_pruned_yaml=N
regen_pruned_db=M` line appeared in journal on at least one VM with N+M > 0 since merge. No drift in fleet/summary
since merge.

## Closing condition

This plan closes when:

1. All Phase 1 + Phase 2 + Phase 3 + Phase 5 items are ✅
2. Phase 4 items are either ✅ or surfaced into a follow-up plan named `ao_regen_per_vm_scope_*.md`
3. CLAUDE.md HARD RULE shipped
4. The fleet/summary numbers match `/api/backlog` numbers within tolerance, for 7 consecutive days

After closing, the issue doc `plans/active/issues/vm_trading_core_orphan_commits_2026_05_29.md` should also be revisited
to confirm the orphan archive branch was reviewed.
