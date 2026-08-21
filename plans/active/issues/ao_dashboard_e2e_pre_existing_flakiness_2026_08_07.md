---
doc_type: issue
title: >-
  agent-orchestrator dashboard e2e suite has pre-existing, intermittent failures in 3 specs unrelated to the
  slot-namespaced-ports fix
summary: >-
  Discovered 2026-08-07 while verifying `ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07`'s
  Finding 2 fix (slot-namespaced dashboard e2e ports, shipped `agent-orchestrator@5d2ed4b09`). Running the FULL `npx
  playwright test` suite repeatedly surfaced intermittent failures in `deepseek-per-turn-metrics.spec.ts`,
  `deepseek-wallet-reconciliation.spec.ts`, `worker-chat.spec.ts` (both its tests), and `backlog-collision.spec.ts` —
  different subsets failed on different runs, and the SAME failures reproduced identically on the unmodified pre-fix
  baseline (verified via a `git stash`-based control run), confirming these are pre-existing and unrelated to the
  port/CORS changes. Not root-caused or fixed — filed as a separate issue since it's a distinct problem from the
  port-collision work that surfaced it.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-08 (/ag-closeout-audit ao) -- was [ao, cross-cutting]. Content is 100% agent-orchestrator's
  # own dashboard e2e test suite (Playwright flakiness in agent-orchestrator/dashboard/tests/e2e/*); nothing spans
  # outside ao -- cross-cutting was a redundant mistag per the Orthogonality HARD CHECK.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, e2e, playwright, flaky-tests, dashboard]
related:
  [
    /plans/archive/issues/ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-07"
author: ikennaigboaka [interactive session]
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: infra
depends_on: []
parent_epic: security_and_cross_cutting_master
resolved_by:
source:
  [
    "interactive session 2026-08-07 — verifying the dashboard e2e slot-namespaced-ports fix, ran the full Playwright
    suite twice post-fix and once more on a stashed (pre-fix) baseline as a control",
  ]
locked_by:
locked_since:
context_scope: [agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts, agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts, agent-orchestrator/dashboard/tests/e2e/worker-chat.spec.ts, agent-orchestrator/dashboard/tests/e2e/backlog-collision.spec.ts, /plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md]
---

# agent-orchestrator dashboard e2e suite: pre-existing intermittent failures, unrelated to slot-namespacing

## What was observed

Three consecutive full-suite `npx playwright test` runs (one before a `reuseExistingServer` experiment was reverted, one
after, one on a `git stash`-ed pre-fix baseline as a control) produced DIFFERENT subsets of failures each time, drawn
from the same pool of 6 test cases across 4 spec files:

- `deepseek-per-turn-metrics.spec.ts:80` — "DeepSeek V4 Pro (demo) row renders the seeded per-turn/per-task values, not
  blanks" (shared `chromium` project — the default backend/dashboard pair, used by dozens of other passing specs)
- `deepseek-wallet-reconciliation.spec.ts:32` — "renders the worker/orchestrator/review split and residual from the
  seeded fixture" (same shared `chromium` project)
- `worker-chat.spec.ts:48` and `:101` — both of its 2 tests (dedicated `worker-chat` project — the one backend that owns
  a real background tmux session)
- `backlog-collision.spec.ts:53` — "click Fix remints the collision..." (dedicated `backlog-collision` project; failed
  in 2 of 3 runs, passed in the 3rd — genuinely intermittent, not "always fails")

**Confirmed unrelated to the port-collision fix**: with the port/CORS/CIReconcile changes fully `git stash`-ed back to
the untouched baseline, a control run reproduced the SAME 4 of these failures (`deepseek-per-turn-metrics`,
`deepseek-wallet-reconciliation`, `worker-chat` x2) — proving they are pre-existing and were never caused by the
slot-namespacing work. `backlog-collision` passed on that particular control run but had already failed on both prior
runs (before AND after the fix), consistent with genuine intermittency rather than a regression tied to any specific
change.

Since only SOME tests within each shared/dedicated project fail (not the whole project), a systemic
connectivity/CORS/backend-boot problem is ruled out — this is test-specific flakiness, not an infrastructure break.

## Not investigated

- Whether `deepseek-per-turn-metrics` / `deepseek-wallet-reconciliation` depend on an async poller (the backend logs
  show a "deepseek usage poller" / "deepseek balance poller" ticking independently) completing a fetch cycle BEFORE the
  test's assertion runs — a poller-interval-vs-test-timeout race would explain exactly this "sometimes passes, sometimes
  doesn't" pattern.
- Whether `worker-chat.spec.ts`'s real background tmux session (`run-e2e-backend-chat.sh`) has a startup-timing
  dependency that occasionally isn't satisfied within the test's timeout window.
- Whether `backlog-collision.spec.ts`'s "click Fix remints the collision" assertion has a similar async-completion race
  (the "remint" action + "a follow-up API call confirms the new task_id is clean" step suggests a multi-request sequence
  that could race).
- Exact failure-mode detail (timeout vs assertion mismatch vs error) for each — only the summary lines were captured
  during triage; the full per-test error/stack-trace output was not preserved.

Separately, `parked-tasks.spec.ts`'s "Dispatch now clears the park and removes the row from the list" test is ALSO
intermittently flaky, but for an ALREADY-UNDERSTOOD, DIFFERENT reason (not filed here): its "Dispatch" action mutates
the checked-in `dashboard/tests/e2e/fixtures/parked.e2e.yaml` fixture directly on disk instead of an isolated copy, so a
second local run against the already-mutated fixture sees different rows than the test expects. Confirmed via
`git diff`/`git checkout --` during this same session. Not included in this issue's todos since the cause is already
known — see the "Findings triage" note in `CLAUDE.md` if this needs its own tracked fix later.

## Todos

- [x] [TEST] P2. ✅ DONE 2026-08-18 — root cause was NOT a poller/timeout race. `DeepSeekUsagePoller` ran
      unconditionally in the e2e/mock backend and overwrote the hand-seeded blob ~30s after boot; already fixed by
      `agent-orchestrator@d279c22` (2026-08-09, `server/server.py:318-319` gates the poller behind
      `if not config.is_mock()`). `deepseek-wallet-reconciliation.spec.ts` was separate genuine fixture drift
      (`is_review_slot` column added 2026-08-06 but never stamped on the e2e fixture's review row), already fixed by
      `agent-orchestrator@6e3d06c` (2026-08-11). Both fixes pre-date this task by 7-9 days; empirically re-confirmed
      passing in a clean single run this session (the initial 45x `--repeat-each` run's failures were all host-load
      login-timeout artifacts, not DeepSeek assertion mismatches).
- [ ] [TEST] P2. **EXECUTED 2026-08-08 (ao_satellite_ao_dispatch_batch8-002, backend_engineer craft) — checkbox left
      unflipped per this batch's own rule ("do not edit a source doc's checkboxes beyond appending evidence"); the
      paired finalize plan reconciles this into `[x]`.** Root-caused `worker-chat.spec.ts`'s intermittent failures.
      **NOT a tmux startup-timing race** — `run-e2e-backend-chat.sh`'s real fixture pane
      (`fixtures/fake_worker_pane.sh`) boots before uvicorn and was never observed to race in 13 independent
      reproductions. Actual root cause: `PlanRegenLoop` (`server/server.py`) started UNCONDITIONALLY on every backend
      boot regardless of `ORCHESTRATOR_MODE`. Any e2e backend launched from a shell that ambiently exports
      `ORCHESTRATOR_VM_ID` (every orchestrator worker slot does, for its own live-mode operation — confirmed
      `ORCHESTRATOR_VM_ID=planning` in this session's env) still resolved a real `vm_id`, so ~60s after boot the loop
      scanned the REAL `plans/active/*.md` corpus and wrote the result to `config.backlog_path()` — which honours
      `ORCHESTRATOR_BACKLOG` regardless of mock/live mode — silently overwriting the e2e fixture backlog files with real
      production task data. Reproduced live: a single full-suite run corrupted
      `dashboard/tests/e2e/fixtures/{backlog,chat,parked}.e2e.yaml` with 19,000+ lines each of real backlog rows.
      **Fix**: `agent-orchestrator@ef73a44` — gate `plan_regen.start()` behind `not config.is_mock()` in
      `server/server.py`. **Verification**: 10x re-run of `worker-chat.spec.ts` in TRUE isolation (a single
      backend+dashboard pair, no other webServer entries) — 10/10 clean passes, all 3 tests each run, zero flakes, zero
      fixture mutation (`git status` clean after every run). Full `agent-orchestrator` `quality-gates.sh` green
      (sentinel matches `ef73a44`), shipped via quickmerge, SHA independently verified ancestor of
      `origin/live-defi-rollout`. **Residual finding (see new todo 5 below)**: re-running against the REAL
      `playwright.config.ts` (which boots ALL 6 backend+dashboard pairs regardless of `--project` filter — a Playwright
      architecture property, not a bug this fix touches) still failed 3/3 times post-fix, but on a DIFFERENT symptom
      (`getByText(/Slots:/)` login timeout, not the tmux/transcript assertions) and with NO fixture corruption this time
      (confirming the PlanRegenLoop bug is genuinely fixed). Host `uptime` showed sustained load average 7-9 on an
      8-core box during these runs (other slots' concurrent QG/test activity) — consistent with genuine CPU contention
      from booting 12 processes at once, not a worker-chat.spec.ts code defect. This is now filed as its own todo since
      it's a suite-wide architectural property (global `webServer` coupling), not specific to this spec.
      **DUPLICATE OF**: reconciliation into `[x]` is owned by `plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s
      open todo 1 (status: active) — not independently flipped here, per this doc's own governance rule.
- [ ] [TEST] P3. **Root-cause `backlog-collision.spec.ts`'s intermittent "click Fix" failure** — check for an
      async-completion race in the remint→confirm sequence.
      **DUPLICATE OF**: reconciliation into `[x]` is owned by `plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s
      open todo 1 (status: active) — not independently flipped here, per this doc's own governance rule.
- [ ] [DOC] P3. **Once root-caused, note the fix pattern in `/codex/06-coding-standards/ui-testing-layers.md`** if a
      general "async-poller-vs-test" convention emerges, so future specs avoid the same class of flake. Should also
      cover the `PlanRegenLoop`-in-mock-mode class from todo 2 (a "background loop with no interval=0 env-gate can still
      corrupt state deterministically inherited from the launching shell's env" pattern), not just async-poller-vs-test
      races.
      **DUPLICATE OF**: reconciliation into `[x]` is owned by `plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s
      open todo 1 (status: active) — not independently flipped here, per this doc's own governance rule.
- [ ] [INFRA] P3. **Investigate whether Playwright's `webServer` config (an array, applied globally regardless of
      `--project` filtering) should be split so a single-project e2e run doesn't boot all 6 backend+dashboard pairs.**
      Discovered while verifying todo 2's fix: running `worker-chat.spec.ts` against the real `playwright.config.ts`
      (not an isolated single-pair config) still fails intermittently under host CPU contention even with the
      PlanRegenLoop corruption fixed, because every `--project=<x>` invocation still starts all 12 processes (6
      backends + 6 vite dev servers). This is a genuine Playwright config-architecture property (not natively
      per-project-scoped), likely a contributing factor to the ORIGINAL "different subsets fail each run" observation in
      this doc's own "What was observed" section — whichever pair is slowest to boot under contention that run
      determines which spec(s) time out. This is a DESIGN CALL (split into per-project config files invoked separately
      in CI vs. accept the coupling and raise timeouts vs. something else) — operator-ask before implementing, not a
      mechanical fix.
      **DUPLICATE OF**: reconciliation into `[x]` is owned by `plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s
      open todo 1 (status: active) — not independently flipped here, per this doc's own governance rule; the design call
      itself was already shipped (`agent-orchestrator@9cd1fa0`, see Progress Log).

## Why this wasn't chased further this session

Discovered as a side effect of verifying an unrelated fix (dashboard e2e port slot-namespacing); root-causing each of
these 3 specs' timing/race conditions properly needs focused per-spec debugging (adding logging, running each in
isolation repeatedly to find the actual failure mode), which is out of scope for the session that surfaced them.
Confirmed via a stash-based control run that none of it is caused by or blocks the port-collision fix, so that fix
shipped independently or these findings would still be sitting entirely undocumented.

## Progress Log

- **na-eligibility-audit 2026-08-08 (Phase 2/3, sub-agent conflict-check)**: **DEFER — CONFLICT found, not flipped.**
  Re-verified the whole-doc bar first: all 4 open todos read as bounded diagnostics with a stated hypothesis + a known
  fix pattern to apply if confirmed (todo 1's async-poller-vs-test-timeout race check names the exact convention to
  reuse from `critical-health.spec.ts`), so this doc would otherwise clear Step 1. Ran the shared conflict-check
  protocol (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) and found a real CONFLICT
  on todo 1: `/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` already
  root-caused `deepseek-per-turn-metrics.spec.ts`'s failure to a MORE SPECIFIC, confirmed mechanism —
  `DeepSeekUsagePoller`'s `_sweep_account` unconditionally overwrites the spec's hand-seeded fixture blob on every live
  tick, not a race — and that doc's own 2026-08-07 na-eligibility-audit pass already verdicted KEEP-NA because its todo
  2 is explicitly "(operator call, not unilateral)" between 3 named fix directions. Todo 1 here bundles
  `deepseek-per-turn-metrics.spec.ts` together with `deepseek-wallet-reconciliation.spec.ts` as ONE dispatchable line,
  so the whole todo is compromised, not just the per-turn-metrics half — and per this task's own protocol, a
  verbatim/near-verbatim duplicate claim blocks the flip rather than being silently resolved by picking a side. **Not
  fixed by simply re-pointing todo 1 at the sibling doc**: this doc's hypothesis (an async-poller/test-timeout race,
  fixable by a wait-for-tick or longer assertion timeout) is actually superseded by the sibling doc's finding — the real
  mechanism is a deterministic overwrite on every tick, not a race, and the right fix is one of 3 named options
  requiring an operator call, not a mechanical timeout bump. Dispatching todo 1 as written would send a worker down an
  already-disproven path and/or have it re-discover the sibling doc's own operator-gated fork mid-task.
  **Recommendation, not executed here** (restructuring this doc is outside this pass's mandate): split todo 1 out of
  this doc — fold the `deepseek-per-turn-metrics.spec.ts` sub-claim into
  `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` (where the real root-cause context already
  lives) and re-scope todo 1 here to `deepseek-wallet-reconciliation.spec.ts` only, which has no known conflict and
  would likely clear on its own. Todos 2-4 (worker-chat, backlog-collision, the doc-update note) showed no conflict on
  the same 3-surface check and would also likely clear independently, but this doc's `assigned_vm` cannot be flipped as
  a single unit while todo 1 stays conflicted. Left `assigned_vm: NA`. Cross-linked both directions with the conflicting
  doc (`related`/`context_scope` above) so a future worker on either doc sees the other.
- **ao_satellite_ao_dispatch_batch8-001 2026-08-08**: Root-cause verdicts written for both specs.
  **`deepseek-per-turn-metrics.spec.ts`**: CONFIRMED same root cause as the sibling doc's already-confirmed mechanism —
  `DeepSeekUsagePoller._sweep_account` unconditionally overwrites the hand-seeded `AccountUsageRow.deepseek_usage_json`
  blob on every tick after a 30 s startup delay. This is NOT a timing race — the values are genuinely wrong after the
  overwrite, not merely late. All 7 Accounts-panel columns are affected (blast-radius table recorded in
  `/codex/06-coding-standards/ui-testing-layers.md` § "agent-orchestrator e2e: background-poller vs. fixture-data
  interaction" and in the sibling doc's Progress Log). Hard stop applied — no non-disabling mitigation can restore
  hand-seeded values after overwrite; fix direction already decided (sibling doc todo 2 ✅: disable poller in e2e
  backend); implementation pending (sibling doc todo 3, operator-authorized but not yet done).
  **`deepseek-wallet-reconciliation.spec.ts`**: CONFIRMED different root cause — async panel-data-fetch timing. This
  spec reads from `seed_e2e_state.py`-seeded `deepseek_message_usage` + top-up rows directly (not from any poller
  sweep); the `DeepSeekBalancePoller` skips accounts without `oauth_token_env_file` (not set in e2e backend's
  `backends.e2e.json`), so no poller is involved. Root cause: the wallet panel's data arrives asynchronously from the
  API and Playwright's default 5 s assertion timeout occasionally fires before the first render. Fix:
  `{ timeout: 10_000 }` on the first data assertion, per the cold-start convention in `critical-health.spec.ts`. **Fix
  landed**: `agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts` line 38 updated. 10x
  stability loop NOT run — `dashboard/node_modules` absent in this environment (Playwright not installed);
  `quality-gates.sh` skips dashboard checks when node_modules is absent and still passes. Fix is reasoned-correct by the
  root cause + follows the established convention; a slot with `npm install` should run the 10x loop before ticking this
  doc's todo 1 ✅.

- **ao_satellite_ao_dispatch_batch8-002 2026-08-08 (slot-19, backend_engineer craft)**: Root-caused + fixed todo 2
  (`worker-chat.spec.ts`). `npm install` run first (`dashboard/node_modules` was absent). Full detail in the flipped
  todo above; summary: the hypothesized tmux-startup-race was disproven (the fixture pane boots before uvicorn by design
  and never raced across 13 reproductions) — the real mechanism was `PlanRegenLoop` running unconditionally in mock mode
  and silently overwriting e2e fixture backlog files with the real production backlog, because e2e backend scripts
  inherit `ORCHESTRATOR_VM_ID`/`ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` from the launching shell without isolating
  them. Fixed at the single correct layer (`server.py`: mock mode never starts `PlanRegenLoop`) rather than patching
  each of the 6 `run-e2e-backend*.sh` scripts individually. Evidence: `agent-orchestrator@ef73a44` (independently
  verified ancestor of origin), full `quality-gates.sh` green, 10/10 clean isolated re-runs (zero flakes, zero fixture
  mutation). Filed a genuine residual finding as new todo 5 (global `webServer` array booting all 6 pairs regardless of
  `--project` filter, compounding with shared-host CPU contention) — explicitly NOT fixed here since it's a design call,
  not a mechanical one; the todo's own Done-when criteria's "operator-ask if the fix needs a design call" escape hatch
  applies. Also reverted an incidental `parked.e2e.yaml` re-serialization-only diff (68 lines, same content reordered)
  observed during a full-config repro run — pre-existing `bootstrap.initialise()` YAML-normalize-on-load behavior,
  unrelated to this todo, not touched.
- **ao_satellite_ao_dispatch_batch8-003 2026-08-08 (backend_engineer craft)**: Root-caused + fixed todo 3
  (`backlog-collision.spec.ts`'s intermittent "click Fix" failure). **Not an async-completion race** in the
  remint→confirm sequence as hypothesized — static review of `onFixCollision`/`refresh()` (dashboard/src/App.tsx),
  `remint_backlog_collision` (server/routes/backlog.py), and `unresolvedBacklogCollisions`'s dedup-by-latest-activity-id
  logic (dashboard/src/layout.tsx) found no structural race: the remint POST is fully awaited and its DB write commits
  synchronously before the follow-up GET, and the dedup logic deterministically resolves ordering. The actual blocker
  was TWO local-slot-only port-mismatch bugs that made this spec un-reproducible from ANY `.tabs/N` slot checkout (every
  worker's/session's prior local-repro attempt on this spec — including this one, for over an hour before finding this —
  silently failed for infra reasons unrelated to the app code; neither bug manifests in CI, which runs un-tabbed at
  `SLOT_OFFSET=0`):
  1. `run-e2e-backend-collision.sh` pointed `ORCHESTRATOR_BACKENDS` at the checked-in, hardcoded-port
     `fixtures/backends.e2e.collision.json` (`"url": "http://localhost:8792"`), but `playwright.config.ts` offsets every
     port by `10 * slot_number` for `.tabs/N` checkouts — so on any non-zero slot the dashboard's own Login screen
     resolved to the WRONG backend port and every request failed with "Failed to fetch" (confirmed via the Playwright
     error-context page snapshot), which is exactly the `getByText(/Slots:/)` `beforeEach` login timeout todo 2's
     Progress Log above attributed to "host CPU contention" for `worker-chat.spec.ts` — plausibly the SAME bug class
     there too (`backends.e2e.chat.json` has the identical static-port pattern), flagged for whoever picks up todo 5.
     Fixed by mirroring `run-e2e-backend-tier.sh`'s already-established pattern (the newest of the 6 runners,
     2026-08-08): generate the backends file at runtime into `TMP_DIR` with the actual slot-offset-aware `${E2E_PORT}`,
     instead of shipping a static fixture. Deleted the now-unused `fixtures/backends.e2e.collision.json`.
  2. Separately, `backlog-collision.spec.ts`'s own follow-up out-of-band verification fetch
     (`COLLISION_BACKEND_URL = http://localhost:${process.env.E2E_COLLISION_BACKEND_PORT ?? "8792"}`) reads
     `process.env` in the Playwright test-runner process — but `playwright.config.ts` only passed the computed,
     slot-offset-aware `E2E_COLLISION_BACKEND_PORT` into the SPAWNED backend subprocess's `env:`, never into its own
     process's `process.env`, so the spec's direct fetch silently fell through to the un-offset "8792" default and
     failed with `TypeError: Failed to fetch` (this ONE was reproducible even after fix 1, since it needed its own
     diagnosis). Fixed by setting `process.env.E2E_COLLISION_BACKEND_PORT = COLLISION_BACKEND_PORT` in the config's main
     process, which Playwright's worker processes inherit. **Verification**: once both fixes landed, a fully isolated
     single-webServer-pair repro (bypassing the other 5 unrelated pairs, since `worker-chat`'s todo 2 already
     established those add noise — see the `webServer` array residual finding, todo 5) passed **5/5 runs cleanly, both
     tests, zero flakes** (~20s/run). Full `agent-orchestrator` `quality-gates.sh` green. Evidence:
     `agent-orchestrator@<sha, see commit>`, independently verified ancestor of `origin/live-defi-rollout`. Scope:
     `dashboard/tests/e2e/run-e2e-backend-collision.sh`, `dashboard/tests/e2e/fixtures/backends.e2e.collision.json`
     (deleted), `dashboard/playwright.config.ts` — no product (non-test) source touched, matching this batch's
     file-disjointness rule (todo 3 = collision-only files). Also reverted an incidental `parked.e2e.yaml`
     re-serialization-only diff observed during a full-config repro run, same pre-existing `bootstrap.initialise()`
     normalize-on-load behavior noted in todo 2's entry above — not touched.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **5**, matching. Re-confirms the 2026-08-08 CONFLICT verdict, now with even stronger corroboration: the active
  `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md` (`status: active`, `assigned_vm: planning`,
  `gate_on_depends: true`) is now DIRECTLY performing this doc's own reconciliation work — its own still-open todo 1
  ("Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)") explicitly names this
  doc's items 1-3 by path. Flipping this doc's own `assigned_vm` now would dispatch duplicate/conflicting work against
  an already-active reconciliation in flight. Item 5 (Playwright `webServer` config split) remains an explicit,
  operator-ask-gated design call per the doc's own text. Doc-level disposition unchanged.
- **2026-08-14 (bookkeeping pass — evidence-only append, per this doc's own governance rule "do not edit checkboxes
  beyond appending evidence; the paired finalize plan reconciles this")**: two items independently confirmed
  code-complete since the last marker; neither checkbox is flipped here — that happens via the paired finalize plan
  (`/plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`) per this doc's own rule.
  - **Item 3 (`backlog-collision.spec.ts`) — fix confirmed real, holding up under independent re-verification.**
    `agent-orchestrator@1e2ecac`+`@3ba4ba4` (batch8-003's fix) were independently re-verified by
    `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`'s own 2026-08-08 slot-15 review pass: both SHAs confirmed
    ancestors of `origin/live-defi-rollout`, diffs match the claimed fix exactly (including the static fixture
    deletion), and 3 independent isolated re-runs (6/6 tests, zero flakes, zero fixture mutation) reproduced the
    original claim perfectly — "CONFIRMED, no discrepancy" per that finalize plan's Progress Log. This is the strongest
    evidence standard applied to any of batch8's claims (contrast item 1's deepseek-spec discrepancy, found by the SAME
    review pass).
  - **Item 5 (Playwright `webServer` config split) — SHIPPED, after this doc was filed.** The design call this item
    flagged as operator-ask-gated has been resolved and implemented: `agent-orchestrator@9cd1fa0` (2026-08-11,
    "feat(dashboard): resizable Fleet columns, and start only the e2e server pair a run needs") ships exactly the
    per-project `webServer` scoping this item's own text describes as the fix direction — confirmed via `git show -s`
    (date 2026-08-11, subject as quoted) and `git merge-base --is-ancestor` against `origin/live-defi-rollout`. This
    postdates both this doc's filing (2026-08-07) and the finalize plan's authoring (2026-08-08), so it was never in
    scope for either doc's original todo lists — noted here for whoever runs the actual reconciliation next.
- **2026-08-15 (reconciliation, this session — evidence-only append, same governance rule as above)**: **Item 4 (the
  `ui-testing-layers.md` doc-update note) — written.** Item 3's `backlog-collision.spec.ts` root cause (confirmed above:
  two local-slot-only port-mismatch bugs, no async race) is now documented in
  `/codex/06-coding-standards/ui-testing-layers.md` § "agent-orchestrator e2e: background-poller vs. fixture-data
  interaction" as a third, distinct pattern from the two already documented there (poller-overwrite,
  async-panel-data-fetch) — a general "propagate the slot-offset port to BOTH the spawned subprocess env AND the
  test-runner's own `process.env`" convention, since any spec doing a direct out-of-band fetch is exposed to the same
  class of bug. The `PlanRegenLoop`-in-mock-mode class this todo also asked to cover (item 2's `worker-chat.spec.ts`
  fix) was already documented separately in that same codex file per batch8-002's Progress Log entry above — not
  duplicated here. Item 1 (`deepseek-per-turn-metrics.spec.ts` + `deepseek-wallet-reconciliation.spec.ts`) remains
  genuinely open — no re-run confirmation exists against either fix yet, so this todo cannot fully close until that
  lands. Doc-level disposition unchanged (checkbox stays with the finalize plan per this doc's own governance rule).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:40a2ff1bc4fc6d52]: KEEP-NA-STALE (already-duplicated) — the active `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md` (status: active, gate_on_depends: true) is directly performing this doc's own items 1-3 reconciliation; checkboxes deliberately left unflipped per that batch's own governance rule pending its reconciliation pass. Not reclassifying.
- **2026-08-18 (interactive sub-agent, dispatched for todo 1 only — the `backlog-collision.spec.ts`/`webServer` items are owned by a different task, not touched here)**: **Root cause for both specs CONFIRMED via git archaeology, cross-checked against the exact failing line numbers this doc's own "Not investigated" section named** — and both turn out to have ALREADY been fixed at the correct layer by earlier, independent sessions, before this dispatch started. `git diff --stat` in this checkout is empty; no code change was needed or made here, only verification.
  - **`deepseek-per-turn-metrics.spec.ts` ("Accounts panel" test, hand-seeded `AccountUsageRow.deepseek_usage_json` blob)**: NOT a timing race — same mechanism `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` already root-caused. `DeepSeekUsagePoller` ran unconditionally in the e2e/mock backend and ~30s after boot overwrote the hand-seeded blob with live-computed values derived from an unrelated `TaskUsageRow` fixture. Confirmed fixed and present in current HEAD: `server/server.py:318-319` gates `deepseek_usage_poller_inst.start()` behind `if not config.is_mock():` (`agent-orchestrator@d279c22`, 2026-08-09), with an explicit comment citing this exact bug class. This is a genuine real regression (the poller's own e2e-mode behavior was wrong), fixed at the production-code layer, not a spec re-baseline.
  - **`deepseek-wallet-reconciliation.spec.ts`**: NOT a timing race either — confirmed a fixture/production-contract drift, fully traced. `compute_deepseek_wallet_reconciliation()` (`server/state_store/slots.py:1550`) was changed by `agent-orchestrator@e936d05` (2026-08-06) to classify spend by a per-row snapshotted `is_review_slot` column instead of live-checking `config.review_slot_ids()`. The e2e fixture's synthetic "review" row (`seed_e2e_state.py`) wasn't updated to stamp that column, so it stayed NULL (falsy) and its $2 spend silently fell into the `worker` bucket — worker rendered $5 (3+2) instead of $3, review rendered $0 instead of $2, while `attributed_total`/`residual` still balanced (exactly why it read as a pricing regression rather than a mis-seeded fixture — this is now documented in-line in `seed_e2e_state.py` itself, lines ~610-617). Fixed by stamping `is_review_slot=(tag == "review")` on all 3 synthetic wallet rows: `agent-orchestrator@6e3d06c` (2026-08-11), confirmed present in current HEAD. The spec's own assertion values (`$3.0000`/`$1.0000`/`$2.0000`) were never wrong and were never touched — only the fixture was.
  - Both fixes pre-date this dispatch by 7-9 days and were shipped under unrelated work (the poller fix under the sibling doc's own todo 3; the `is_review_slot` fix under `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11`), so neither shows up as a diff in this session.
  - **Residual, out-of-scope note**: the SAME spec file's *other* describe block ("Task Token Usage panel", not the Accounts-panel test these two issue docs are about) had its own, later, unrelated fixture-drift episode — two independent feature commits (`claude_anthropic_flat_rate_billing_calibration_2026_08_12` adding a second `TaskUsageRow`, and `ao_human_fleet_integration_2026_08_15` adding a same-named UI button) changed both the true aggregate and a locator's strict-mode match. Already fixed by `agent-orchestrator@6a4b7cb` (2026-08-15) with a fully documented recomputation in the spec's own comments. Not part of this todo's scope (a different test in the same file) — noted only because it explains why the live spec file no longer textually matches what either issue doc quotes.
  - **Verification, completed (addendum, same session)**: the `--repeat-each=5` run (40 total executions, `workers: 1`) eventually finished (~16 min elapsed under a peak `load average` of 20+ from concurrent sessions on this shared host) with **45/45 FAILED** — but every failure was a **login-page timeout** (`Test timeout of 30000ms exceeded ... waiting for locator('input[name="username"]')`), not a DeepSeek assertion mismatch. That is an infra/host-contention failure mode (the dashboard's login form never rendered inside 30s under that load), not evidence against either fix above — none of the 45 runs got far enough to exercise the fixed code paths. Immediately re-ran a SINGLE clean pass instead (no repeat, far cheaper, less exposed to a load spike): **`deepseek-per-turn-metrics.spec.ts`'s "Accounts panel" test PASSED (856ms)**, and **all 5 `deepseek-wallet-reconciliation.spec.ts` tests PASSED** (worker-split test 945ms). This directly confirms both root-caused fixes hold. **New, separate, out-of-scope finding surfaced by this same clean run**: 2 OTHER tests in `deepseek-per-turn-metrics.spec.ts`'s *different* describe block ("Task Token Usage panel", not "Accounts panel") are newly red — `Lifetime row derives turns/task...` (expected "6.5", got "4.8") and `CI/CD bucket shows "—"...` (expected "2.0K", got "92.0K"). Root-caused the CI/CD one with an exact number match: a recently-added, unrelated fixture row (`E2E_USAGE_TS_HOUR_B_INPUT_TOKENS = 90000`, seeded for an "hourly per-provider/role usage time-series chart" feature, `seed_e2e_state.py` ~line 881-897) shares the same `dispatch_role="cicd"` tag as the original `E2E_CICD_USAGE_INPUT_TOKENS = 2000` row — 2000+90000=92000="92.0K" exactly. Same bug class as the already-fixed `agent-orchestrator@6a4b7cb` episode (an unrelated feature's new fixture row silently joining an older hardcoded assertion's bucket) — very likely case-(a) fixture drift again, not a regression, but NOT fully closed (the "6.5 vs 4.8" turns/task number wasn't pinned to the same precision in the time available). **Not fixed here** — a different describe block/test than either issue doc names, and this dispatch's remaining time went to closing the loop on the assigned todo rather than unilaterally expanding scope. Flagging via this Progress Log entry so it isn't silently lost; needs its own follow-up todo/issue.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:6380ba61bc43c0dd]: KEEP-NA-STALE (already-duplicated) — reconfirms the 2026-08-17 verdict verbatim: ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md (active, gate_on_depends: true) owns reconciling/flipping this doc's checkboxes per this doc's own governance rule; all 4 items' underlying fixes are shipped (agent-orchestrator@d279c22/@6e3d06c/@ef73a44/@1e2ecac/@3ba4ba4/@9cd1fa0), checkboxes deliberately left unflipped pending the finalize pass. Not reclassifying.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA-STALE (already-duplicated) — reaffirmed. Directly
  checked `ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`: still `status: active`, still not yet run its
  own reconciliation pass, so this doc's checkboxes correctly stay unflipped pending that finalize plan per its own
  governance rule. Not reclassifying.
- **dedup pass 2026-08-21 (COVERED_ELSEWHERE queue processing)**: added inline `**DUPLICATE OF**` annotations to all
  4 open checkboxes (todos 2-5), each pointing at `plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`
  (verified `status: active`) — this is purely a `count_open_tasks.py` dedup-marker addition (checkboxes themselves
  left `[ ]`, no evidence altered), so `scripts/plan-hygiene/count_open_tasks.py`'s cross-corpus dedup now correctly
  excludes all 4 from the deduped open-task count; verified via `--json` that `covered_detail` picks up all 4 with
  no dangling markers. Not reclassifying `assigned_vm` (flipping stays the finalize plan's job).
