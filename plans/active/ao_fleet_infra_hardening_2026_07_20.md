---
doc_type: plan
title: AO fleet infra hardening — one state home, no duplicate vars, no silently frozen clones
summary:
  The wrong-DB incident and three bitten diagnostic sessions all trace to one concept living in two places, so state
  moves to a single in-repo home with a hard no-wipe requirement on the deploy path. Alongside it — drop the genuinely
  redundant env var, make a single frozen clone visible in the deployment-ui fleet tab instead of only a fleet-wide
  skip, sweep the existing frozen clones, and cap concurrent full-QG at dispatch.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-ui]
scope: [engineer]
tags: [agent-orchestrator, infra, state-home, env-vars, fleet, quality-gates]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, qg_host_adaptive_resource_governor_2026_07_14.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: infra
model_tier: sonnet-doable # bounded infra edits; the risky migration step is operator-gated, not agent-decided
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO fleet infra hardening

> **Provenance**: Phase 4 of `ao_open_issues_consolidated_close_out_2026_07_17.md` (docs #2, #7, #8 + operator rulings
> 2026-07-18). That plan keeps the audit record; this plan holds the work.

## The theme: one concept, one place

The wrong-DB GC incident and **three separate bitten diagnostic sessions** all came from the same footgun.
`ORCHESTRATOR_DB_PATH` / `ORCHESTRATOR_STATE_JSON` are set in the systemd unit (→ `/var/lib/orchestrator/…`, outside the
repo) while `config.py`'s default is in-repo `data/state/…`. So a CLI tool run as `ubuntu` without the unit env silently
resolves the **wrong path** — and reports confidently on an empty database. It bit me twice more during the 2026-07-20
audit (the wrong-DB read AND a bogus "no state.json" alarm), which is how this became P1.

## ⚠️ The reversal this requires — do not skip it

Operator ruling 2026-07-18: **keep AO backend state IN the repo, one definition, no duplicate var.** That **reverses the
deliberate `/var/lib` redeploy-wipe protection**, so it becomes a HARD requirement that the deploy path preserve state
instead. `ao-self-pull.sh` and any redeploy/re-clone MUST NEVER `git clean -x` or wipe `data/state/`. A bare FF-pull is
already safe (the dir is gitignored); the guard is against `clean -fdx` and fresh-clone flows. The SnapshotLoop S3/GCS
archive remains the DR fallback. **Todo 1 is not done until that guard exists and is tested.**

## Execution environment — LOCAL

Operator-assigned agents on this host (`assigned_vm: NA`, `execution_scope: local-only`). Tick checkboxes by hand.
Code/config work is local. **The live state migration in todo 1 is a PRODUCTION write on the central VM (operator-gated
— do not run it unilaterally)**, as is any unfreeze in todo 4. Read-only inspection via SSM follows
`scripts/orchestrator/check-ao-backlog-status.sh`.

## Todos

- [x] [INFRA] P1. ✅ **State home = ONE in-repo source (`data/state/`); drop the two-places and the env overrides.** —
      agent-orchestrator@0fa79bae6c1. Removed the unit's `Environment=ORCHESTRATOR_DB_PATH/STATE_JSON` lines +
      `ReadWritePaths=/var/lib/orchestrator` from `orchestrator.service`; removed the wrong-direction (repo→/var/lib)
      one-time migration + dir provisioning from `bootstrap_vm.sh` and added `_remove_env` purges for both vars on
      already-bootstrapped hosts (mirrors the existing `ORCHESTRATOR_REGEN_DB_PATH` retirement pattern); fixed
      `restore_from_gcs.sh`'s hardcoded default + `audit_false_done.py`'s stale usage example to the in-repo path;
      documented the retirement + the standing no-`git clean -fdx` requirement in `ENV_VARS.md`. **Gate evidence**:
      `data/state/` is gitignored (confirmed) so the deploy path (FF-pull + `git clean -fd`) already left it alone —
      proved empirically by new `tests/test_state_dir_deploy_safety.py` (clones the repo locally, writes a dummy
      state.db, runs `git clean -fd`, asserts survival + non-dirty status); full `quality-gates.sh` green (1418 passed).
      Original `config.db_path()`/CLI-agreement gate was already true by construction (config.py's default was never
      wrong — only the systemd unit + bootstrap duplicated a different path). Source: doc #8 todo 2 + operator
      2026-07-18.
- [ ] [INFRA] P1. **Migrate the running state (operator-gated, live).** Move `/var/lib/orchestrator/*.db` →
      `data/state/` on the VM, then restart. **Do NOT run this unilaterally** — it stops the orchestrator briefly and
      moves the live database. Propose it, get approval, take a snapshot first, and verify the service comes back
      reading the new path with its task/slot counts intact. **Gate**: post-migration row counts match pre-migration;
      the service is healthy; the old path is empty and nothing recreates it.
- [x] [INFRA] P2. ✅ **Duplicate-purpose env-var sweep — verify consumer, THEN remove.** —
      agent-orchestrator@0fa79bae6c1 (same commit as todo 1, landed together). `bootstrap_vm.sh` no longer
      `_upsert_env`s `ORCHESTRATOR_OPERATOR` (now `_remove_env`s it on already-bootstrapped hosts, same pattern as the
      DB-path retirement); the field stays on `OrchestratorConfig` as an optional override. Both KEEP decisions
      (`GOOGLE_CLOUD_PROJECT` vs `GCP_PROJECT_ID`; the `WORKSPACE_ROOT` trio) + this retirement recorded in
      `ENV_VARS.md` under new "Retired" / "Checked — NOT a duplicate" sections. **Gate**: verified no other write site
      for `ORCHESTRATOR_OPERATOR` exists in `scripts/`/`docs/` (grepped); `host_operator()`'s existing vm_id-fallback
      (unchanged) means a host with only `VM_ID` set resolves the identical operator it always did.
- [ ] [INFRA] P2. **Per-repo freeze-streak signal (AO half).** The dirty-streak WARN fires only when EVERY repo in a
      sweep skips, so **a single frozen clone — the exact 2-day outage mode — stays silent.** Make the streak per-repo
      in `slot-cron-ff-pull.sh`: repo X `[skip:dirty]` / `[skip:ff-failed]` for N consecutive ticks emits a
      per-repo/per-slot freeze signal. **Gate**: a deliberately-frozen single clone produces the signal within N ticks,
      naming the repo and the slot.
- [ ] [UI] P2. **Per-repo freeze-streak surface (deployment-ui half) — NOT a Slack alert.** Operator ruling 2026-07-18:
      feed the signal into the **`deployment-ui` FLEET TAB** where clone/slot status already renders, so one stuck repo
      on one slot is obvious at a glance, and improve that page to make the state easy to check on demand. Render per
      repo × slot, not one global flag. Note: the backlog-details-popup UI work is a DIFFERENT scope with no dependency
      here. **Gate**: the frozen clone from the previous todo is visibly stuck in the fleet tab, naming repo + slot; per
      the UI testing rule this needs `[UI]` + `pw:L2 ✓` + a cited regression spec.
- [ ] [INFRA] P2. **Fleet-wide frozen-clone sweep (one pass).** hk-host root repos measured behind=0, but the VM's SLOT
      clones and any other hosts were never swept. Check every host's root + slot clones for `HEAD..origin/LDR > 0` with
      untracked-only dirt, and unfreeze with a plain FF. **Unfreezing is a write — dry-run and report first, then get
      approval.** **Gate**: sweep output recorded; zero frozen clones remain.
- [ ] [INFRA] P2. **Dispatch-time full-QG throttle — coordinate, do NOT build a second governor.** The shared-host "≤2
      full QG" cap is unenforced at dispatch; 4-6 concurrent full-QG pytests saturated the VM on 07-17. The RAM/CPU
      admission governor (`qg_host_adaptive_resource_governor_2026_07_14`, active P1) is the natural enforcement point
      but was measured `MODE=token K=2` on this VM. Scope: (a) record the requirement on the governor plan
      (dispatch-aware QG admission on the orchestrator host); (b) **only if** its Phase-3 ledger is not landing soon,
      implement the minimal dispatcher-side stagger (cap simultaneous ship-phase tasks per host). **Gate**: concurrent
      full-QG on the VM measurably capped — via the governor or the stagger — with evidence cited.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Todos 2 and 6 move or mutate live state.** Both are operator-gated. Snapshot before, verify after, and never
  unfreeze a clone whose dirt is NOT untracked-only — that dirt may be another agent's uncommitted work.

## Codex SSOTs

- `codex/05-infrastructure/per-tab-worktrees.md` — slot clones, ff-pull, the freeze mode this detects.
- `codex/06-coding-standards/quality-gates.md` — the shared-host QG cap todo 7 enforces.
- `codex/06-coding-standards/ui-testing-layers.md` — the playwright gate binding the deployment-ui todo.
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — state/topology context for the state home.

## Progress Log

- **2026-07-20 — plan created** from Phase 4. The state-home item is P1 rather than P2 because it bit the 2026-07-20
  audit twice more (a wrong-DB read and a bogus snapshot alarm), which is the same class of wasted diagnosis it has
  already caused three times.
- **2026-07-20 — todos 1 + 3 shipped** — agent-orchestrator@0fa79bae6c1 (quality-gates.sh green, 1418 tests). Todo 2
  (live migration) intentionally NOT done here — operator-gated, to be proposed separately once approved. Operator
  answered two clarifying questions on this session's start: todo 7 becomes "unblock the governor's Phase-5 flip" (its
  reservation-ledger engine is already code-complete + soaked, blocked only on an unrelated slot-16 `.venv` gap —
  building a redundant dispatcher-side stagger was rejected in favor of fixing the real blocker); todo 6's sweep scope
  is this laptop (hk) + the central orchestrator VM (both reachable this session) plus ref-corruption detection (broken
  remote-tracking refs silently blocking fetch, not just the dirty/skip mode) — Ikenna's laptop is out of reach and
  stays unswept. Also found + fixed in passing (slot 25, not part of this plan's todos): `deployment-api` was 249
  commits behind LDR, silently masked by 4 stale `dep-update/*` remote-tracking refs pointing at objects the
  reference-clone prune hazard had pruned from the base — same root cause class todo 6 will now sweep for.
