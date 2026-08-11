---
doc_type: issue
title:
  agent-orchestrator dashboard e2e harness — unmeetable webServer boot budget, tracked-fixture write-back, and
  slot-blind hardcoded backend ports
summary: >-
  Four harness-level defects in agent-orchestrator/dashboard's Playwright setup, found 2026-08-10 while adding the Fleet
  Account column. (1) Playwright starts ALL SIX backend+vite webServer pairs on every run — even `--project=chromium`
  for one spec — but each backend entry had a hardcoded `timeout: 60_000`, while ONE backend alone measured 55s to serve
  /api/healthz 200; the suite died before a single test ran, reproduced on an untouched spec. FIXED: budget is now a
  constant (300s backend / 120s vite, env-overridable). (2) Four of six launchers pointed ORCHESTRATOR_BACKLOG/ACCOUNTS
  at COMMITTED files that the backend writes back to, so every run left a dirty tracked fixture. FIXED STRUCTURALLY: all
  six now stage copies via a shared `e2e_export_staged` helper, and `check_e2e_fixture_staging.py` fails the gate if a
  seventh launcher ever reintroduces the class. (3) The parked and critical-health pairs read COMMITTED backends
  fixtures pinning :8791/:8794 — correct only in the un-tabbed checkout, so both specs died with "Failed to fetch" in
  every .tabs/N slot. FIXED: both now generate a slot-offset-aware backends file, matching what run-e2e-backend.sh
  already did. (4) STILL OPEN — fleet-typed-agent-work.spec.ts fails on the MAIN pair, whose backends file was already
  generated correctly; it fails AFTER authentication on the dashboard state fetch, not at login as first reported.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, playwright, e2e, fixtures, ui-testing]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
author: slot-2 (interactive)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: devops
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by: agent-orchestrator dashboard e2e harness repair (slot 2, 2026-08-10/11)
source: >-
  Operator request to add an Account column to the FleetView Fleet table (slot 2, 2026-08-10) — the pw:L2 gate for that
  change could not run until the boot budget was raised, and running it dirtied a tracked fixture.
---

# Dashboard e2e harness: boot budget, fixture write-back, slot-blind ports

## 1. The 60s webServer boot budget was under-provisioned by construction — FIXED

`playwright.config.ts` declares six backend+vite pairs (main, parked, collision, chat, critical-health, tier).
Playwright starts **every** `webServer` entry on **any** run — `--project=chromium <one-spec>` does not narrow it — so
all six backends boot concurrently and contend for the same host.

Measured on the operator's laptop 2026-08-10, ONE backend started alone:

| elapsed | `curl -s -o /dev/null -w '%{http_code}' localhost:8810/api/healthz` |
| ------- | ------------------------------------------------------------------- |
| 5s–50s  | `000` (connection refused)                                          |
| 55s     | `200`                                                               |

Against a hardcoded `timeout: 60_000`, six concurrent boots can never fit. Every invocation failed with
`Error: Timed out waiting 60000ms from config.webServer` before running a test — reproduced on an untouched spec
(`fleet-token-cache-badge`), so this was not caused by any spec change.

Fixed: `BACKEND_BOOT_TIMEOUT_MS` (default 300s, `E2E_WEBSERVER_TIMEOUT_MS`) and `VITE_BOOT_TIMEOUT_MS` (default 120s,
`E2E_VITE_TIMEOUT_MS`) replace the twelve hardcoded literals. A single spec file then runs end-to-end in ~9 minutes,
nearly all of it boot.

## 2. Four of six launchers handed the backend TRACKED config files — FIXED STRUCTURALLY

The backend WRITES to what it is configured with: `ORCHESTRATOR_BACKLOG` is rewritten by the auto-park pass
(`auto_park: parked E2E-PARKED-GATED after 3 GATED skips` in the run log), `ORCHESTRATOR_ACCOUNTS` by the tier editor
and any account disable/rate-limit mutation. After a suite run `git status` showed
`M dashboard/tests/e2e/fixtures/parked.e2e.yaml` — a 68-deletion/68-insertion reordering of the same rows.

The hazard was already known and already written down. `run-e2e-backend-tier.sh`'s header says, of pointing at the
committed accounts file:

> Pointing this suite at it (**as every other e2e runner does**) would leave a dirty tracked fixture behind after every
> run and silently change the tiers provider-badge.spec.ts and critical-health.spec.ts boot from.

…and then fixed only its own accounts file. Two launchers staged copies; four did not.

The fix is structural rather than four one-off patches, because patching the four leaves the seventh launcher to
rediscover this:

- `dashboard/tests/e2e/e2e-backend-lib.sh` — new shared `e2e_export_staged VAR SRC TMP_DIR`, which copies the fixture
  into the launcher's own `TMP_DIR` and exports the copy. It exports from the **caller's** shell rather than echoing a
  path for `export VAR="$(...)"`: that form runs in a subshell and `export` always exits 0, so a missing fixture would
  sail past `set -e` and hand the backend an empty path.
- All six launchers routed through it.
- `scripts/quality_gates/check_e2e_fixture_staging.py` — wired into `quality-gates.sh`; fails if any
  `run-e2e-backend*.sh` exports a writable config var from a path that does not resolve under its `TMP_DIR`. Verified in
  both directions: green on the fixed tree, and red (exit 1, correct file + var named) when one launcher's staging is
  reverted.

## 3. Committed backends fixtures pinned ports that are wrong in every slot — FIXED

`fixtures/backends.e2e.parked.json` hardcoded `http://localhost:8791` and `fixtures/backends.e2e.critical-health.json`
hardcoded `http://localhost:8794`. `playwright.config.ts` offsets every port by slot (`SLOT_OFFSET = <N> * 10`), so on
`.tabs/2` those backends actually listen on **8811** and **8814**.

This is a known, already-diagnosed class — `run-e2e-backend.sh`'s own header records it:

> The Login screen REPLACES the dashboard's default self-URL entry with whatever GET /api/backends returns, so a stale
> port here silently misdirects login (confirmed root cause of a "Failed to fetch" login stall when run from any .tabs/N
> slot checkout)

Main/chat/collision/tier were converted to generate the file at runtime; parked and critical-health were left behind, so
`parked-tasks.spec.ts` and `critical-health.spec.ts` cannot have passed in any slot checkout since `SLOT_OFFSET` landed.
Fixed: both now generate a slot-offset-aware backends file, and the two committed fixtures are deleted.

## 4. `fleet-typed-agent-work.spec.ts` — RESOLVED: it was the same contention

Correcting an earlier statement in this doc's own history: it never failed at login. The saved `error-context.md` showed
the session authenticated (account menu renders `E e2e`) and the page rendering **"Could not load dashboard state —
Failed to fetch"** — the timing-out assertion was simply the first one needing loaded state.

Root cause is finding 1's, one layer down. Booting six backends against a laptop already running the agent fleet starved
the main backend badly enough that the dashboard's own fetch failed at the network layer. Nothing was wrong with the
spec, the CORS wiring, or orphan-reaping (all three were investigated and cleared). Once `serversForThisRun()` boots
only the pair a run needs, it passes **3/3 in 15s**, repeatedly.

The measured contrast, same tree, same host:

| run                                      | result                |
| ---------------------------------------- | --------------------- |
| `npx playwright test` (all six pairs up) | 78 passed, 5 failed   |
| `npm run test:e2e:all` (one pair a time) | 81 passed, 1 + 1 left |

The 4 failures that vanish between those rows — `fleet-typed-agent-work` ×2 and `worker-chat` ×2 — each pass in
isolation, which is the signature of starvation rather than a defect. The 2 that remain are genuine and are NOT harness
issues; they moved to `/plans/archive/2026_08/issues/ao_dashboard_e2e_failures_exposed_by_repaired_harness_2026_08_11.md`.

## 5. The original evidence for "55s", corrected

The 55s single-backend boot this doc opened with is not a fixed cost — it was measured while the host was saturated.
Re-measured on a quiet host, the same backend serves `/api/healthz` **200 in ~4s** (and answers in 27ms once up). So the
honest framing is: boot time is contention-dependent, the 60s budget was fine for one backend and impossible for six,
and raising the budget to 300s was a workaround. Starting fewer servers is the fix; the raised budget stays only as
headroom for a genuinely loaded host.

## Todos

- [x] ✅ [SCRIPT] P2. Stage every backend-owned config through a shared helper so no launcher can hand the backend a
      tracked path — `e2e-backend-lib.sh` + all six launchers converted.
- [x] ✅ [SCRIPT] P2. Enforce it so a new launcher cannot regress the class — `check_e2e_fixture_staging.py`, wired into
      `quality-gates.sh`, verified red-then-green against a deliberately reverted launcher.
- [x] ✅ [SCRIPT] P2. Generate the parked + critical-health backends files slot-offset-aware; delete the two committed
      fixtures pinning :8791/:8794.
- [x] ✅ [UI] P2. Diagnosed `fleet-typed-agent-work.spec.ts`'s "Failed to fetch" — NOT a spec, CORS or reaping bug:
      backend starvation from booting six pairs at once. With per-project server scoping it passes 3/3 in 15s.
- [x] ✅ [SCRIPT] P2. Verified finding 3's fix from this `.tabs/2` checkout — `parked-tasks` 5/5, `critical-health` 2/2.
- [x] ✅ [SCRIPT] P3. Cut the boot cost at the root: `serversForThisRun()` starts only the pair(s) a run needs. Measured
      on `fleet-account-column`: **9.3 min → 14.4 s**. Plus `npm run test:e2e:all` for the whole suite as one invocation
      per project, which is what removes the contention rather than tolerating it.

## Progress Log

- **2026-08-10** — Found while adding the Fleet table's Account column (slot 2, interactive). Findings 1-3 fixed in the
  same change; finding 4 left open with its evidence recorded. The dirtied `parked.e2e.yaml` was restored with
  `git checkout --` after verifying the diff was a pure mechanical reordering.
- **2026-08-10** — Separately deleted `scripts/deploy-dashboard.sh`: unreferenced anywhere in the repo, and its header
  described an rsync-to-`/var/www` topology on "the human-planning VM or a dedicated static-files host" — a VM
  terminated 2026-08-03. The real path is `.github/workflows/deploy-dashboard.yml` → Firebase Hosting on every push to
  `live-defi-rollout`. That stale header caused a wrong answer to the operator ("you'll need to deploy manually") in
  this very session, which is what surfaced it.
- **2026-08-11** — CLOSED. All five findings resolved and measured, not asserted: per-project server scoping
  (`serversForThisRun()`) took a single-spec run from 9.3 min to 14.4 s and made finding 4 evaporate;
  `npm run test:e2e:all` runs the suite one project at a time (81 passed). Two genuine non-harness failures the working
  suite exposed were handed to
  `/plans/archive/2026_08/issues/ao_dashboard_e2e_failures_exposed_by_repaired_harness_2026_08_11.md` rather than papered over.
  Also corrected this doc's own opening claim: the "55s boot" was a contention artefact, not a fixed cost (~4s on a
  quiet host).
