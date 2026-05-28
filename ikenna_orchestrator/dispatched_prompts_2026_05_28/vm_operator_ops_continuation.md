You are an orchestrator worker on vm-operator-ops (epic VM owning dart_and_promote_master +
deployment_and_user_management_master). Model tier: sonnet-doable, thinking: medium. AUTONOMOUS background run —
operator's laptop is offline; you complete the bundle alone.

STEP 0 — read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` + `unified-trading-pm/CLAUDE.md` HARD
RULES — especially the **UI playwright gate** (any UI checkbox tick requires `pw:L2 ✓` + regression spec evidence).

STEP 1 — SYNC FRESH in `deployment-ui`, `deployment-service`, `unified-trading-pm`: git fetch origin live-defi-rollout
&& git rebase origin/live-defi-rollout

STEP 2 — BUNDLE (continuation of laptop slot 3):

Plan — `plans/active/deployment_ui_vm_and_venue_coverage_visibility_2026_05_27.md`.

Already done (commits already on live-defi-rollout): §1.1 + §1.2 (diagnose empty VM page + render running VMs).

Continue with:

- §2.1 P0 — diagnose + fix the broken History tab.
- §2.2 P1 — show completed/failed/reaped deployments.
- §3.1 P1 — per-venue credential-status panel (secret NAME + STATUS from Secrets Manager).

Data-dependent items (§3.2, §4.1, §4.2) wait on cefi coverage-map SSOT (being shipped by the vm-ml worker as part of
cefi §3). Pick those up if coverage map lands in time; otherwise leave.

UI HARD RULE: every UI todo tick MUST carry `[UI]` tag + `pw:L2 ✓`
(`npx playwright test --project=chromium tests/smoke/` exits 0) + a regression spec path. Evidence format:
`— deployment-ui@<sha> | pw:L2 ✓ | regression: tests/path/spec.ts`. You can run a dev server on this VM (`npm run dev`).

STEP 3 — SHIP DISCIPLINE (HARD RULE): QG green per repo before merge; commit + push HEAD:live-defi-rollout per shippable
unit; flip plan checkbox same-turn with `docs(plans):` commit + UI evidence. Side-discoveries → todos. Operator gates →
ping.

Begin with STEP 0.
