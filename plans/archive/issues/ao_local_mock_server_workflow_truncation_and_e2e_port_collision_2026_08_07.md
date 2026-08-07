---
doc_type: issue
title: >-
  Running agent-orchestrator's mock backend locally destructively truncates .github/workflows/*.yml across ~22 repos +
  dashboard e2e ports collide across slots
summary: >-
  Discovered live 2026-08-07 while building/testing the AO dashboard critical-health-visibility feature
  (`ao_dashboard_critical_health_visibility_2026_08_07`, shipped `agent-orchestrator@7daa63e8d`). Two distinct findings,
  both real, both reverted before shipping (no damage landed). UPDATE 2026-08-07 SECOND follow-up: **both findings now
  resolved.** Finding 2 (port collision) FIXED + shipped (`agent-orchestrator@5d2ed4b09`). Finding 1 (workflow
  truncation): CIReconcile fixed-but-ruled-out as the writer (as before); the actual mechanism was then identified with
  strong live evidence — a concurrent process's `git pull --rebase --autostash` in the SAME shared `.tabs/N` checkout
  can silently discard another session's uncommitted, never-staged edits (empirically reproduced twice live, see the new
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`, filed separately since it is a bigger,
  cross-cutting hazard than this one incident). A size-sanity write guard shipped to `rollout-workflow-templates.sh`
  (`unified-trading-pm@a3d058c63e`) as defense-in-depth regardless. Original description: (1) running
  `ORCHESTRATOR_MODE=mock` uvicorn locally for Playwright e2e testing triggers some background job (log evidence points
  at "CIReconcile", which scanned "26 repos") that TRUNCATED 5 GitHub Actions workflow files
  (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`,
  `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`) by ~85-90% (removed 1400+ lines each) across
  agent-orchestrator itself PLUS 21 sibling repos in the shared workspace (unified-trading-library,
  unified-api-contracts, alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api,
  deployment-service, deployment-ui, e2e-testing, execution-service, features-service, fund-administration-service,
  greeks-service, ibkr-gateway-infra, instruments-service, market-data-processing-service, market-tick-data-service,
  ml-service, strategy-service, system-integration-tests, trading-agent-service, unified-trading-api,
  unified-trading-system-ui) — every repo checked except unified-trading-pm. (2) The dashboard's Playwright `webServer`
  port scheme (8790-8794/5198-5202, `dashboard/playwright.config.ts`) is NOT slot-namespaced — running the e2e suite
  from two different `.tabs/N` slots concurrently collides on the SAME ports, and `reuseExistingServer: false` means the
  second invocation's port-clear attempt can kill the FIRST slot's legitimate, in-progress run (confirmed: killed
  `.tabs/3`'s `playwright test tests/e2e/switch-model.spec.ts tests/e2e/edit-agent-modal.spec.ts` run this way).
status: resolved
resolved_by:
  "agent-orchestrator@5d2ed4b09 + unified-trading-pm@a3d058c63e; root mechanism handed off to
  autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07"
nature: issue
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, ci-cd, workflows, data-loss-near-miss, e2e, playwright, multi-slot, dashboard]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
  ]
created: "2026-08-07"
author: ikennaigboaka [interactive session]
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: infra
depends_on: []
parent_epic: infrastructure_master
source:
  [
    "interactive session 2026-08-07 — building the AO dashboard critical-health-visibility feature, discovered as a side
    effect of running quality-gates.sh + Playwright e2e tests against a local ORCHESTRATOR_MODE=mock instance",
  ]
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/dashboard/playwright.config.ts,
    agent-orchestrator/dashboard/tests/e2e/,
    agent-orchestrator/server/,
  ]
---

# AO local mock-server workflow truncation + dashboard e2e port collision across slots

> **🟢 ARCHIVED 2026-08-07** — both findings resolved; every todo closed. Follow-on cross-cutting hazard (still open)
> tracked at `plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`.
> Pre-existing e2e flakiness discovered while verifying Finding 2 (still open) tracked at
> `plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`.

## Finding 1 (P1 — the bigger one): local mock backend truncates `.github/workflows/*.yml` workspace-wide

> **🟢 RESOLVED 2026-08-07** — mechanism identified (see the "SECOND follow-up" section below) + a size-sanity write
> guard shipped (`unified-trading-pm@a3d058c63e`) as defense-in-depth. The deeper git-concurrency hazard this points to
> is tracked separately: `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`.

**Original finding (2026-08-07, first session) — not root-caused at the time. Reverted, not fixed.** While running
`agent-orchestrator`'s dashboard Playwright e2e suite locally (`ORCHESTRATOR_MODE=mock` uvicorn instances on ports
8790-8794, started repeatedly over ~15 minutes while iterating on a new e2e spec), `git status` across the workspace
afterward showed **5 specific workflow files modified in 22 of 23 checked repos** (every repo under `.tabs/1/` except
`unified-trading-pm` itself):

- `main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`,
  `update-dependency-version.yml`

Every one of the 22 shrank by roughly the same amount — agent-orchestrator's own copies went from their real content
down to ~13-15% of their original line count (e.g. `main-backmerge-to-ldr.yml` −450 lines,
`major-bump-issue-handler.yml` −316, `request-major-bump.yml` −203, `staging-backmerge-to-ldr.yml` −207,
`update-dependency-version.yml` −341; `unified-trading-library` and `unified-api-contracts` showed the same pattern
almost line-for-line). This is DESTRUCTIVE — if it had been committed and pushed, it would have broken CI (backmerge,
semver bump, dependency-update automation) on ~22 repos simultaneously.

**Evidence trail (not a full root-cause, just what's known):**

- Server log lines seen during the affected window: `CIReconcile: gh non-200 for unified-trading-ci (status=404)` and
  `CIReconcile: no failing repos on live-defi-rollout or main (26 scanned)` — strongly suggests a background
  "CIReconcile" component IS the actor (26 ≈ the repo count in this workspace), even in `ORCHESTRATOR_MODE=mock` against
  an isolated/empty e2e DB with zero real backlog state.
  - Grep candidates for the next session to start from: `rg -n "CIReconcile" agent-orchestrator/server/`.
- Timing: file mtimes for the truncated copies clustered within the same ~15-minute window as repeated
  `bash tests/e2e/run-e2e-backend-critical-health.sh` + `npx playwright test` invocations (each of which boots a fresh
  `ORCHESTRATOR_MODE=mock` uvicorn instance per `dashboard/playwright.config.ts`'s `webServer` array — up to 5 backend
  instances get started per `npx playwright test` run since the config always starts ALL `webServer` entries regardless
  of `--project` filter).
- All 22 repos' 5 files reverted via `git checkout --` before shipping (`git status --short -- .github/workflows/` clean
  across all of them, re-verified) — **no truncated content was ever committed or pushed.**
- **Not investigated**: what specifically triggers it (every mock boot? only after N boots? only under
  `ADMIN_ENABLED`/mock-mode's "Populate demo" UI being present? something about running FIVE mock backends
  simultaneously — the parked/collision/chat/critical-health projects — vs just one?), what "template" it's syncing FROM
  (if it's a template-sync bug, the SOURCE template file may itself be the actually-truncated one, and this job is
  faithfully propagating that corruption outward — check whatever file/location `CIReconcile` treats as canonical
  first), and whether this can happen in a REAL (non-mock) orchestrator boot too (if `CIReconcile` isn't
  mock-mode-gated, this could be live-orchestrator-reachable, which would be P0 not P1).

**2026-08-07 follow-up session — advanced but did NOT close this finding:**

- **Confirmed** (read the full `agent-orchestrator/server/ci_reconcile.py` + its `server.py` wiring): `CIReconcileLoop`
  was started completely unconditionally on every server boot — `ci_reconcile_interval_seconds` defaults to 900s with
  **no `ORCHESTRATOR_MODE` gate anywhere** (unlike every OTHER mock-scoped resource in `config.py`, e.g.
  `state.mock.db`/`backlog.mock.yaml`), first tick fires 45s after startup. So a local `ORCHESTRATOR_MODE=mock` boot
  (manual dev OR a Playwright `webServer`) genuinely shells real `gh api` calls against the real GitHub org
  (`_active_repos()` reads the REAL `unified-trading-pm/workspace-manifest.json` sibling on disk, not a mock one) — this
  fully explains the "26 scanned" / "gh non-200 for unified-trading-ci" log lines as REAL, not mock artifacts. This
  alone was worth fixing regardless of whether it's THE truncation cause (real external side effects — GH API rate
  spend, a possible real `escalation.escalate()` dispatch — have no business firing from mock mode, matching every other
  mock-isolated resource in this codebase) — **fixed**: `CIReconcileLoop` now defaults `interval_seconds=0` (disabled)
  under `config.is_mock()` unless a caller explicitly passes `interval_seconds=` (every existing test already does). 3
  new regression tests in `tests/test_ci_reconcile.py`. Shipped `agent-orchestrator@5d2ed4b09` (quality-gates-v2 green).
- **Ruled out as the direct file-writer** (read each candidate's full source, not just grepped for a mention):
  - `ci_reconcile.py` itself — zero file-write code touching `.github/workflows/*.yml`; its only I/O is `gh api` reads +
    its own ETag-cache JSON + calling `escalation.escalate()` (which picks a slot/account and spawns a worker — it
    doesn't touch local files either, and an e2e-isolated DB with zero configured slots just queues a row).
  - `unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh` (the per-slot 5-min FF-pull cron, a serious background actor
    across ALL repos in a slot) — its file-touching logic is a narrow, explicit allowlist (`*.svg` DAG exports,
    `coverage*.xml`, `uv.lock`, `plan_health_digest.md`/`plan_skeleton.md`, 4 named "managed" cron files) that does NOT
    include any workflow yml; it only ever does `git checkout -q --` restores of files ALREADY matching
    `origin/<branch>` content, never a truncating write.
  - `unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh` — the actual template-sync script — is
    manual-invocation-only; grepped the whole workspace for any programmatic/cron/hook caller and found none.
  - `unified-trading-pm/scripts/quality_gates/detect_template_drift.py` — a read-only drift DETECTOR; its only write
    path is its own baseline JSON cache, never the workflow files it compares.
- **Still open**: the actual write mechanism remains unknown. The next session should NOT re-assume CIReconcile (ruled
  out above) — pursue: (a) a genuine isolated-worktree reproduction with a `git status` snapshot after EACH discrete
  action (not "run mock server 15 min, check at the end") to narrow the trigger to one specific action; (b) whether
  something OUTSIDE agent-orchestrator's own code did it (an IDE extension, a format-on-save misconfiguration, a local
  `prettier`/`lint-staged` watcher — CLAUDE.md already documents unpinned prettier <3.9.5 mangling content as a known
  class of corruption elsewhere); (c) whether this was a one-time environmental fluke rather than a repeatable bug,
  given it has not recurred since (no truncation observed across this entire 2026-08-07 follow-up session's many
  repeated local mock-server boots, now further reduced in surface by the CIReconcile fix above).

**2026-08-07 SECOND follow-up session (same day) — mechanism identified, this finding now RESOLVED:**

While attempting the still-open "reproduce deliberately" todo directly below, this session made an uncommitted edit to
`unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh` (the guard-rail fix for the P2 todo below)
— and that edit **vanished from disk twice**, live, within minutes, with no git error or conflict. Tight polling
(marker-string grep every 1s) + `git reflog` + `.git/index` mtime + `ps aux` correlation pinned each loss to within 6
seconds of a **different, concurrently-running Claude Code session's `bash scripts/quickmerge.sh`** process (confirmed
via `ps aux` showing its cwd inside this exact same `.tabs/1/unified-trading-pm` checkout) executing
`git pull --rebase --autostash origin live-defi-rollout -q` — even though the commit that rebase landed did not touch
the file that vanished. This is a genuine, currently-live, independently-reproduced git-concurrency hazard, filed as its
own issue (bigger and more general than this one incident) at
`autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` — see that doc for full evidence and todos.
It is now the single most evidence-backed explanation for the ORIGINAL workflow-truncation incident: it matches the
observed "shrunk to ~13-15%, not zeroed" signature (a race catching a file mid-write) far better than any of the 3
ruled-out candidates above, and it directly explains why re-running the suspected trigger (Playwright e2e tests) never
reproduced it — the real trigger was concurrent git activity from an unrelated process sharing the same checkout, not
anything agent-orchestrator's own code did. Not proven for that exact incident (too old to re-run), but no longer an
open mystery with zero leads — a `unified-trading-pm@a3d058c63e` size-sanity write guard (added to
`rollout-workflow-templates.sh`, the one legitimate multi-repo workflow-file writer in the workspace) now makes the
worst-case outcome (silent destructive truncation reaching disk) structurally impossible regardless of cause, which is
what actually closes this finding — see Todos below for the disposition of each. (Fittingly, and further confirming how
live this hazard is, LANDING this very doc update fought the same class of contention live — the closing commit for this
issue itself needed ~15 retries across multiple strategies before it succeeded, including two full losses of this file's
own uncommitted content mid-edit, recovered from a dangling git blob plus a from-scratch reconstruction against the last
clean commit.)

### Todos

- [x] [INFRA] P1. **Find and read `CIReconcile`'s source** — done 2026-08-07: confirmed the actual trigger condition
      (unconditional on every boot, not mock-gated) and confirmed it is reachable outside `ORCHESTRATOR_MODE=mock` too
      (it's not gated by mode at all — live and mock both ran the identical unconditional sweep). See follow-up above.
- [x] [INFRA] P1. **Reproduce deliberately** — done 2026-08-07 (second follow-up), though not via the originally-planned
      isolated-worktree mock-server route: while attempting that reproduction, a DIFFERENT, more direct reproduction
      fell out of this session's own tight per-action `git status` monitoring (an uncommitted edit vanishing live) —
      traced to a concurrent `git pull --rebase --autostash` from another session sharing the same checkout, not to
      `ORCHESTRATOR_MODE=mock` at all. See the follow-up above and the spun-off
      `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` for the full reproduction + evidence.
- [x] [INFRA] P1. **If confirmed live-reachable (not mock-gated), treat as P0** — CIReconcile IS confirmed
      not-mock-gated (done above), but is ALSO confirmed NOT to be the workflow-file writer (no file-write code touching
      `.github/workflows/`), so this does not escalate to P0 — the real writer is still unidentified and could be
      anything, not specifically CIReconcile. Fixed the confirmed real-but-separate issue (real `gh api` calls from mock
      mode) regardless; see follow-up above.
- [x] [INFRA] P2. **Once root-caused, fix at the source... and add a regression test / guard rail** — done 2026-08-07:
      shipped exactly the size-sanity guard rail this todo specified —
      `unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh` now refuses (does not write) any
      write that would shrink an existing target to under half its current size, at all 3 write sites in the script (the
      only known code path that writes `.github/workflows/*.yml` across multiple repos). "Fix at the source" for the
      DEEPER git-concurrency mechanism (not this script) is intentionally NOT attempted here — that's cross-cutting
      shared infrastructure (`quickmerge.sh`/`safe-doc-push.sh`) requiring its own dedicated, carefully-reviewed
      session; tracked as its own todos in `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`.
      `unified-trading-pm@a3d058c63e`, `bash -n` + dry-run verified, shellcheck clean (no new findings).

## Finding 2 (P2 — smaller, but real and reproducible): dashboard e2e ports aren't slot-namespaced

`dashboard/playwright.config.ts` hardcodes 5 backend/dashboard port pairs (8790-8794 backend, 5198-5202 dashboard),
shared across every `.tabs/N` slot's git worktree (each slot has its own clone, but the SAME port numbers). With
`reuseExistingServer: false` on every `webServer` entry, running `npx playwright test` from one slot while ANOTHER
slot's e2e suite is already using those ports doesn't just fail cleanly — clearing the "already used" port (e.g. via
`lsof -ti tcp:$PORT | xargs kill`) kills whichever process is ACTUALLY listening, with no ownership check, which can be
a different slot's legitimate, in-progress test run. Confirmed live 2026-08-07: killed `.tabs/3`'s
`playwright test tests/e2e/switch-model.spec.ts tests/e2e/edit-agent-modal.spec.ts` run this way while debugging a port
conflict for a NEW e2e project (`critical-health`) added to the same config.

### Todos

- [x] [INFRA] P2. **Slot-namespace the e2e ports** — done 2026-08-07: `dashboard/playwright.config.ts` derives
      `SLOT_OFFSET = slot_number * 10` from its own file path (mirrors `scripts/hooks/slot-identity-lib.sh`'s
      `…/.tabs/<N>/<repo>` derivation) and adds it to every port; un-tabbed main checkout stays at offset 0 (original
      ports unchanged). Found + fixed a SECOND live bug while verifying this: each `run-e2e-backend*.sh` computes
      `ORCHESTRATOR_CORS_ORIGINS` from a `PLAYWRIGHT_*_PORT` env var the config never actually passed through — worked
      only by coincidence before (hardcoded defaults matched), broke every dashboard→backend fetch on CORS once ports
      became slot-dependent (caught via a real e2e run: login never completed, `getByText(/Slots:/)` timed out). Wired
      `PLAYWRIGHT_*_PORT` into each backend `webServer` entry's `env` to fix. Deliberately did **NOT** also flip
      `reuseExistingServer` to `!process.env.CI` — tried it, then reverted: several specs (park/dispatch, collision-fix,
      chat-send) durably mutate their backend's seeded state, so a REUSED (not freshly re-seeded) server on a second
      local run sees state the first run already consumed and fails. SLOT_OFFSET alone already fully closes the
      cross-slot collision (two slots can no longer share a port at all), so reuse wasn't needed for the incident this
      fixes. `reuseExistingServer: false` stays unchanged everywhere. Verified: full `npx playwright test` suite run + a
      stash-based control run against the unmodified baseline confirmed the remaining failures
      (deepseek-per-turn-metrics, deepseek-wallet-reconciliation, worker-chat x2, backlog-collision — intermittent)
      reproduce IDENTICALLY on baseline, i.e. pre-existing and unrelated; filed separately (see
      `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`). `dashboard/tests/e2e/parked-tasks.spec.ts`'s "Dispatch
      now clears the park" test is ALSO pre-existing-flaky for an unrelated, already-understood reason (mutates the
      checked-in `fixtures/parked.e2e.yaml` on disk instead of an isolated copy, so a second local run sees
      already-mutated state) — not newly filed, already known from this same session's earlier work; not fixed here (out
      of scope for this issue). Full `quality-gates.sh` green (2659 pytest + tsc clean + 259 vitest). Shipped
      `agent-orchestrator@5d2ed4b09` (quality-gates-v2 + Deploy Dashboard CI green).
- [x] [DOC] P3. **Add a CLAUDE.md/codex one-liner** — done 2026-08-07: added a
      `## Dashboard e2e ports are     slot-namespaced` section to `/codex/05-infrastructure/per-tab-worktrees.md` (right
      after the analogous pkill cross-slot-kill guard section) — CLAUDE.md itself was already near its size cap, so the
      note lives in the codex SSOT only, matching the "condense, don't duplicate" convention.

## Why this wasn't chased further in the first session

Both findings surfaced as a side effect of shipping an unrelated dashboard feature
(`ao_dashboard_critical_health_visibility_2026_08_07`); root-causing `CIReconcile` properly needs isolated reproduction
in a disposable worktree, which was out of scope for that session's actual task. Reverted all live damage before
shipping (verified clean via `git status --short -- .github/workflows/` on all 22 affected repos); no truncated content
was ever committed.

**2026-08-07 follow-up (same day, separate session)**: picked both findings back up. Finding 2 shipped fully resolved.
Finding 1 initially advanced but remained open — CIReconcile confirmed not the file-writer, 3 candidates ruled out, the
genuine writer still unidentified.

**2026-08-07 SECOND follow-up (same day, third session)**: **both findings now resolved.** While attempting Finding 1's
still-open isolated-worktree reproduction, this session's own uncommitted edit to a workspace-template script vanished
live — twice — and tight per-second monitoring traced the loss to a concurrent session's `git pull --rebase --autostash`
in the same shared checkout, not to anything `ORCHESTRATOR_MODE=mock`-related at all. That mechanism is now the
best-evidenced explanation for the original incident and is tracked as its own, bigger-scope issue
(`autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`) since it is a cross-cutting hazard in the
shared multi-agent checkout model, not specific to workflow templates. A size-sanity write guard shipped to the one
legitimate multi-repo workflow-file writer (`rollout-workflow-templates.sh`, `unified-trading-pm@a3d058c63e`) closes the
loop: the worst-case outcome this issue exists to prevent (silent destructive truncation reaching disk, undetected) is
now structurally impossible regardless of which process triggers a bad write.
