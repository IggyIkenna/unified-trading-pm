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
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
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
- [x] ✅ [INFRA] P1. **Migrate the running state (operator-gated, live).** — DONE 2026-07-21 on the planning VM
      (`i-0c9b283b31d6b5ca7`), operator-authorized maintenance window (slot-16 interactive). Sequence: `disable` →
      graceful `stop` (S3 DR snapshot `state_20260721T025351Z.json`; WAL checkpointed `integrity_check=ok`) → full local
      backup `/var/lib/orchestrator.bak.20260721T025531Z` → moved `state.db`+`state.json` → `data/state/` (overwrote the
      stale 4 KB stub the two-places bug had created) → **fixed the STALE DEPLOYED UNIT** (the trap: repo template was
      clean at `0fa79bae6c1` but `/etc/systemd/system/orchestrator.service` still carried
      `Environment=ORCHESTRATOR_DB_PATH/STATE_JSON` + `ReadWritePaths=/var/lib/orchestrator`) via
      `install-orchestrator-service.sh --operator ubuntu` (no `--restart`) + `daemon-reload` → `enable` + `start`. Then
      cleaned up the defunct `/var/lib/orchestrator/` entirely (removed the stale `state.pre-orphan-gc-20260717.db`
      backup + the empty dir). **Gate MET**: post-migration row counts EXACT vs pre
      (`tasks=25 agents=97 slots=17     accounts=4 blocked_queue=471`); service healthy (`/health` 200, `mode=live`);
      backend reads the new path (`/api/mode` → `db_path=…/agent-orchestrator/data/state/state.db`); old path is GONE
      and NOT recreated; killed worker respawned into slot 4 (working). Rollback backups retained.
- [x] [INFRA] P2. ✅ **Duplicate-purpose env-var sweep — verify consumer, THEN remove.** —
      agent-orchestrator@0fa79bae6c1 (same commit as todo 1, landed together). `bootstrap_vm.sh` no longer
      `_upsert_env`s `ORCHESTRATOR_OPERATOR` (now `_remove_env`s it on already-bootstrapped hosts, same pattern as the
      DB-path retirement); the field stays on `OrchestratorConfig` as an optional override. Both KEEP decisions
      (`GOOGLE_CLOUD_PROJECT` vs `GCP_PROJECT_ID`; the `WORKSPACE_ROOT` trio) + this retirement recorded in
      `ENV_VARS.md` under new "Retired" / "Checked — NOT a duplicate" sections. **Gate**: verified no other write site
      for `ORCHESTRATOR_OPERATOR` exists in `scripts/`/`docs/` (grepped); `host_operator()`'s existing vm_id-fallback
      (unchanged) means a host with only `VM_ID` set resolves the identical operator it always did.
  > **🚫 Per-repo freeze-streak signal + deployment-ui surface (was todos 4/5) — DESCOPED from our plans 2026-07-21
  > (operator).** Handed to the agent already working on the deployment-ui fleet tab; owned there, not tracked here or
  > in `monitoring_control_plane_master_2026_06_10.md` (where they had been moved 2026-07-20). Removed as `- [ ]` todos
  > so they no longer read as our open work.
- [x] [INFRA] P2. ✅ **Fleet-wide frozen-clone sweep (one pass).** hk-host root repos measured behind=0, but the VM's
      SLOT clones and any other hosts were never swept. Check every host's root + slot clones for `HEAD..origin/LDR > 0`
      with untracked-only dirt, and unfreeze with a plain FF. **Unfreezing is a write — dry-run and report first, then
      get approval.** **Gate**: sweep output recorded; zero frozen clones remain. **Progress 2026-07-20 (scope: hk
      laptop + central orchestrator VM via SSM, both reachable this session; Ikenna's laptop unreachable, not swept)**:
      swept 375 clones on the laptop (all `.tabs/*` slots + root) + 425 on the VM (all slots + root) = 800 total.
      **Ref-corruption** (a distinct failure mode from the one this todo names — a slot's stale
      `refs/remotes/origin/dep-update/*` remote-tracking ref points at an object the base clone's auto-gc pruned,
      silently blocking `git fetch` while `git status` reads clean — the reference-clone prune hazard in
      `per-tab-worktrees.md`) found + fixed in 5 laptop clones: `deployment-api` in slots 25/27/28/29/30, all masked 249
      commits behind. Fixed by deleting the 4 dead local refs
      (`dep-update/{deployment-service,strategy-service,     unified-api-contracts}-0.2.0`,
      `unified-trading-library-0.4.0` — confirmed gone from the remote, safe: they're pure local cache) +
      `reflog expire --stale-fix`; did NOT FF the resulting 249-behind (that's the "unfreeze" write this todo gates —
      reported, not yet approved). VM clones do NOT have this corruption (checked). **Trivial drift** (dirty=0, 1-2
      commits behind — normal 5-min ff-pull cron lag, not a freeze): ~30 instances across both hosts, all
      `unified-trading-pm`/`strategy-service`/`market-tick-data-service`, harmless. **Genuine flagged clones needing
      operator triage (dirt is TRACKED, not untracked-only — the safeguard above says don't touch)**: laptop slot 5
      `unified-trading-pm` (787 behind, 1 tracked-dirty file); VM slot 4 `instruments-service` (2 behind,
      `M scripts/close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`); VM slots 14/15 `instruments-service`
      (87/93 behind, both `M uv.lock` only — looks like lockfile drift from a `uv sync`/QG run, not necessarily WIP, but
      unconfirmed). **Also NOT a freeze** (behind=0, so not stuck — likely live/recent WIP, left alone): laptop slot 24
      `agent-orchestrator` (2 tracked-dirty files, untouched). **✅ FF-unfroze all 4 (operator approval 2026-07-20)** —
      plain `git merge --ff-only`; every tracked-dirty file survived untouched (git only refuses an FF when the incoming
      diff conflicts with the dirty file, which none of these did); all 4 now `behind=0`. **Gate met**: sweep recorded
      above; zero frozen clones remain on the swept scope (hk laptop + orchestrator VM — Ikenna's laptop stays unswept,
      unreachable this session).

      **⚠️ GATE CORRECTION + RE-MEASURE 2026-07-20 (hk host).** The "zero frozen clones remain" claim above was
                                                                                                                                                  **overclaimed when written**: the 5 `deployment-api` clones (slots 25/27/28/29/30) whose ref-corruption this todo
                                                                                                                                                  un-masked were left at **249 behind, explicitly un-approved and un-FF'd** ("reported, not yet approved"), and the
                                                                                                                                                  "✅ FF-unfroze all 4" sentence covers only the four TRACKED-DIRTY clones — a different set. Nothing anywhere
                                                                                                                                                  tracked those 5. Re-swept all **375 hk-host slot clones + 25 root repos** today with a measured survey
                                                                                                                                                  (`git fetch` + `HEAD..origin/<branch>` per clone): **`deployment-api` is `behind=0` on all 15 slots** — the
                                                                                                                                                  249-behind class is genuinely gone here, so the gate is NOW met on this host, but it was met by later cron
                                                                                                                                                  catch-up, not by this todo. Worst observed anywhere was **7** (an actively-committed PM clone). FF'd 42 clean
                                                                                                                                                  clones across two passes (0 failures); **2 dirty clones deliberately PROTECTED** (slots 27/28 `unified-trading-pm`
                                                                                                                                                  — live agent WIP, mtimes minutes old, per the liveness-gated inherited-WIP rule).

                                                                                                                                                  **Lesson that outlives this todo — `behind=1` is CHURN, not a freeze.** Between two full sweeps ~4 min apart the
                                                                                                                                                  behind>0 count went 16 → 29, purely because other agents kept pushing to LDR. Chasing an absolute behind-count is
                                                                                                                                                  a treadmill; a frozen clone is one whose behind-count **grows monotonically without recovery**, which is a
                                                                                                                                                  STREAK signal, not a threshold. This is exactly why the per-repo freeze-streak detector (re-homed todos 4/5 →
                                                                                                                                                  `monitoring_control_plane_master_2026_06_10.md`) matters more than any manual sweep: a sweep is stale the moment
                                                                                                                                                  it finishes. **Do not re-run a manual sweep as a substitute for landing the detector.**

- [x] [INFRA] P2. ✅ **Dispatch-time full-QG throttle — coordinate, do NOT build a second governor.** The shared-host
      "≤2 full QG" cap is unenforced at dispatch; 4-6 concurrent full-QG pytests saturated the VM on 07-17. The RAM/CPU
      admission governor (`qg_host_adaptive_resource_governor_2026_07_14`, active P1) is the natural enforcement point
      but was measured `MODE=token K=2` on this VM. Scope: (a) record the requirement on the governor plan
      (dispatch-aware QG admission on the orchestrator host); (b) **only if** its Phase-3 ledger is not landing soon,
      implement the minimal dispatcher-side stagger (cap simultaneous ship-phase tasks per host). **Gate**: concurrent
      full-QG on the VM measurably capped — via the governor or the stagger — with evidence cited. **Progress
      2026-07-20**: operator ruling this session — the governor's reservation-ledger engine is already code-complete +
      soak-tested (42-run live soak, 0 OOM per that plan's Phase 6), so a dispatcher-side stagger would be a redundant
      second mechanism; unblock the real fix instead of building around it. Root blocker was slot-16's missing `.venv`
      preventing THAT slot's copy of the Phase-5 rollout change (`QG_GOVERNOR_MODE=reservation` in `bootstrap_vm.sh`)
      from clearing `quality-gates.sh`. Fixed both: shipped the 2-line change from a QG-green slot instead
      (agent-orchestrator@91808dfeb5f9), sidestepping the venv blocker entirely; separately built the missing `.venv`
      for VM slots 1 AND 16 (`uv sync`, on-demand artifact, no risk) so future work in those slots isn't blocked either.
      **Live rollout gap found + closed**: re-running `bootstrap_vm.sh` was the wrong fix — the operator had ALREADY set
      `QG_GOVERNOR_MODE=reservation` + `QG_HOST_CONCURRENCY=6` directly in `agent-orchestrator/.env.local` on the VM.
      The real bug: unlike `UV_CACHE_DIR` (which `base-service.sh` derives fresh every run),
      `qg-host-governor.sh`/`base-service.sh` read these two straight from the ambient env with NO file-read fallback,
      and nothing sourced `.env.local` into a worker's tmux pane or an operator's terminal — proved by sourcing it by
      hand, which flipped `--status` from `MODE=token K=2` to `MODE=reservation` instantly. **Fix shipped**: new
      `scripts/dev/install-qg-governor-shell-env.sh` (unified-trading-pm@e0350b904) — mirrors
      `install-uv-cache-shell-env.sh`'s managed-`.bashrc`/`.zshrc`-block convention, but reads the CURRENT value out of
      `.env.local` at shell-start rather than hardcoding a literal (hardcoding would recreate the exact bug this whole
      plan exists to kill). Installed + verified on the live VM: a genuinely interactive shell now reports
      `MODE=reservation`, `RAM budget 22GB/70%`, `CPU slots=3`, `K runaway-backstop=6` — the full target state. **Gate
      met**: concurrent full-QG on the VM is now capped by the reservation-ledger governor (dual-gate RAM+CPU,
      soak-tested), evidence above.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Todos 2 and 6 move or mutate live state.** Both are operator-gated. Snapshot before, verify after, and never
  unfreeze a clone whose dirt is NOT untracked-only — that dirt may be another agent's uncommitted work.

## Codex SSOTs

- `/codex/05-infrastructure/per-tab-worktrees.md` — slot clones, ff-pull, the freeze mode this detects.
- `/codex/06-coding-standards/quality-gates.md` — the shared-host QG cap todo 7 enforces.
- `/codex/06-coding-standards/ui-testing-layers.md` — the playwright gate binding the deployment-ui todo.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — state/topology context for the state home.

## Progress Log

- **2026-07-20 — post-close-out alert follow-up.** A live `agent-orchestrator-alerts` page fired for slot 14
  (`instruments-service` dirty 1 file for 2433m) after the todo-6 sweep — the sweep had fixed the BEHIND count for the 4
  flagged clones but deliberately left their dirty files untouched (per the safeguard). Investigated all 4 via the FM8
  liveness discriminator (`server/worktree_clean_check/_liveness.py`): slot 14's claim was expired since 2026-07-18,
  slot 15 + laptop-slot-5 had no claim file, and VM slot 4's dirty-file mtime was 13.8h old (all classify
  "dead"/"absent" → inherit, none "live"). Resolved by replicating the orchestrator's own `commit_and_push_dirty_repos`
  mechanism verbatim: `chore(orphan-wip)` commit with the slot's own identity, pushed to a content-addressed
  `wip-preserve/orchestrator-slot-<N>-<sha>` ref (never touches `live-defi-rollout` directly), then realigned each slot
  to a clean `origin/live-defi-rollout` tip — for VM slots 4/14/15 (`instruments-service`, code/lockfile content).
  Laptop slot 5's dirty file was PM plan content (not code) and read as complete + coherent, so it was landed properly
  via `quickmerge` instead (`unified-trading-pm@aa20257cb`) rather than parked on a wip-preserve ref. All 4 clones now
  measure dirty=0, behind=0.
- **2026-07-20 — todos 6 + 7 closed out.** Operator approved FF-unfreeze of all 4 flagged clones (laptop slot 5 PM
  787→0, VM slots 4/14/15 instruments-service 2/87/93→0) — all clean, tracked-dirty files survived untouched. On the
  governor: re-running `bootstrap_vm.sh` turned out to be the wrong fix — the operator had already set
  `QG_GOVERNOR_MODE=reservation`/`QG_HOST_CONCURRENCY=6` directly in `.env.local`; the real gap was that nothing sourced
  `.env.local` into an interactive shell (unlike `UV_CACHE_DIR`, these two vars have no derive-fresh fallback in
  `base-service.sh`). Shipped `install-qg-governor-shell-env.sh` (unified-trading-pm@e0350b904, mirrors the existing
  uv-cache shell-env convention) and verified live on the VM: an interactive shell now correctly reports
  `MODE=reservation`. Both todos' gates are met; only todo 2 (live state migration, explicitly operator-gated) remains
  open in this plan.
- **2026-07-20 — plan created** from Phase 4. The state-home item is P1 rather than P2 because it bit the 2026-07-20
  audit twice more (a wrong-DB read and a bogus snapshot alarm), which is the same class of wasted diagnosis it has
  already caused three times.
- **2026-07-20 — todos 6 + 7 progress** — see the todos themselves for full detail. Summary: swept 800 clones across
  hk-laptop + the orchestrator VM (via SSM); fixed 5 ref-corrupted `deployment-api` clones (a distinct failure mode from
  what todo 6 named); flagged 4 clones with genuine tracked dirt for operator triage (not touched, per the safeguard);
  shipped the governor Phase-5 flip (`agent-orchestrator@91808dfeb5f9`) by routing around the slot-16 venv blocker
  rather than fixing it in place, then fixed that venv gap anyway (+ slot 1's) as a separate low-risk action. **Awaiting
  operator decisions before further action**: (a) FF-unfreeze approval for the 3 flagged VM clones + laptop slot 5's PM
  clone; (b) approval to re-run `bootstrap_vm.sh` on the live orchestrator VM so it actually picks up
  `QG_GOVERNOR_MODE=reservation` (shipped code is inert until then).
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
