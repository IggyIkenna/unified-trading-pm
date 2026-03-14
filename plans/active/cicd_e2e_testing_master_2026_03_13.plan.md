---
name: cicd-e2e-testing-master-2026-03-13
overview: |
  Comprehensive E2E testing plan for the full CI/CD pipeline stack. Validates every workflow path using instruments-service as the primary guinea pig (leaf service, 9 library deps, zero downstream dependents) and unified-events-interface for cascade testing (T0, many downstream dependents). 8 phases: static validation, repo flow, cascade, staging/SIT, agent validation, failure modes, codex/documentation, and a golden path end-to-end test. Every test has a type tag ([SCRIPT], [AGENT], [HUMAN]), expected outcome, and verification command. Milestone-gated.
todos:
  - id: static-actionlint
    content: |
      - [ ] [SCRIPT] P0. Run `actionlint` on all 25 PM workflows + all 7 instruments-service workflows. Verify: exit 0, zero errors. Command: `actionlint .github/workflows/*.yml`. Note: 25 not 23 — sit-debounce-trigger.yml and sit-starvation-detector.yml were added.
    status: pending
  - id: static-action-ref-consistency
    content: |
      - [ ] [SCRIPT] P0. For every repo in manifest, check that `quality-gates.yml` references the same composite action ref. All 67 repos should point to the same version. Script: `scripts/propagation/rollout-quality-gates-ci-workflows.py --check-only` or equivalent.
    status: pending
  - id: static-manifest-schema
    content: |
      - [ ] [SCRIPT] P0. Validate `workspace-manifest.json` against schema. Check: all repos have required fields, `versions` map matches `repositories` keys, version in manifest matches `pyproject.toml` for every repo. Known issue: instruments-service `0.1.22` vs `0.1.117`. Command: `python3 scripts/validate-manifest-dag.py --manifest workspace-manifest.json`. Verify: exit 0, zero mismatches, no DAG cycles.
    status: pending
  - id: static-telegram-guard-scan
    content: |
      - [ ] [SCRIPT] P1. Scan all 23 workflow files for broken patterns: (a) `if: always() && env.TELEGRAM_BOT_TOKEN` in GHA `if:` context, (b) `secrets.TELEGRAM_CHAT_ID` instead of `vars.TELEGRAM_CHAT_ID`. After Plan 1 Phase 0 fixes: expect zero violations. Known pre-fix locations: `semver-agent.yml:435`, `rules-alignment-agent.yml:197`, `plan-health-agent.yml:89`, `conflict-resolution-merged.yml:68`.
    status: pending
  - id: static-concurrency-group-audit
    content: |
      - [ ] [SCRIPT] P1. All manifest-mutating workflows must use `concurrency: { group: manifest-update, cancel-in-progress: false }`. Check: `update-repo-version.yml`, `staging-to-main.yml`, `sit-gate.yml`, `sit-unlock.yml`, `hotfix-mode.yml`. Verify: 5/5 confirmed.
    status: pending
  - id: static-trigger-correctness
    content: |
      - [ ] [SCRIPT] P1. Verify workflow triggers: semver-agent on `workflow_run: branches: [staging]`, manifest-sync on `push: branches: [main], paths: [workspace-manifest.json, "plans/**"]`, cloud-build-router on `repository_dispatch: types: [qg-passed]`. Verify instruments-service QG dispatches `qg-passed` only on `push` to `main` (not on PR).
    status: pending
  - id: static-debounce-pending-repos
    content: |
      - [ ] [SCRIPT] P0. Verify `staging_status.pending_repos` field exists in workspace-manifest.json and is populated by sit-gate.yml when repos merge to staging. sit-debounce-trigger.yml reads this field — if missing, debounce is a silent no-op. Verify: jq '.staging_status.pending_repos' workspace-manifest.json returns array (not null).
    status: pending
  - id: static-cloud-build-concurrency
    content: |
      - [ ] [SCRIPT] P0. Verify cloud-build-router.yml is in the `manifest-update` concurrency group. It writes `deployed_versions` to manifest but currently has NO concurrency section. Two concurrent builds racing to write deployed_versions cause lost updates. After Plan 1 fix: verify concurrency group present.
    status: pending
  - id: static-version-bump-loop-guard
    content: |
      - [ ] [SCRIPT] P1. Verify all repos' update-dependency-version.yml properly uses [skip ci] in commit messages. If any omits it: QG→qg-passed→version-bump→more dispatches = infinite loop. Also check for dispatch chain depth counter in version-bump payloads (max 3).
    status: pending
  - id: static-idempotency-empty-history
    content: |
      - [ ] [SCRIPT] P1. Test staging-to-main.yml idempotency check when main_commits.history is empty (currently an empty object in manifest). The idempotency logic compares staging_commits to main_commits.history[0].commits. If history is empty or has unexpected structure, idempotency check always returns "proceed" — it never blocks duplicates. Create specific test for this edge case.
    status: pending
  - id: static-baseline-pending-coverage
    content: |
      - [ ] [SCRIPT] P1. Verify rollout-promote-ci-status handles BASELINE_PENDING repos (5 repos: batch-audit-api, batch-live-reconciliation-service, ml-inference-api, ml-training-api, trading-analytics-api). These would be silently skipped if only BASELINE_RECORDED is checked.
    status: pending
  - id: flow-local-qg
    content: |
      - [ ] [SCRIPT] P0. Run local QG: `cd instruments-service && bash scripts/quality-gates.sh`. Verify: exit 0, coverage >= 70% (MIN_COVERAGE in script). Verify base-service.sh sources correctly from `WORKSPACE_ROOT/unified-trading-pm/scripts/quality-gates-base/`.
    status: pending
  - id: flow-feature-commit
    content: |
      - [ ] [HUMAN] P0. Create trivial `fix:` commit on `live-defi-rollout` branch in instruments-service. Push to GitHub. Verify: no CI fires (feat branch push without PR does not trigger QG).
    status: pending
  - id: flow-pr-creation-qg
    content: |
      - [ ] [HUMAN+AGENT] P0. Create PR from `live-defi-rollout` to `main` in instruments-service. Command: `gh pr create --base main --head live-defi-rollout --title "fix: e2e canary"`. Verify: `quality-gates.yml` fires on `pull_request` event. QG job installs Python 3.13.9, clones PM + all deps, runs `quality-gates.sh`. `qg-passed` dispatch does NOT fire (PR, not push).
    status: pending
  - id: flow-merge-dispatch
    content: |
      - [ ] [HUMAN+AGENT] P0. Merge the PR to main. Verify: `quality-gates.yml` fires on `push` to `main`. On success: `qg-passed` dispatched to PM with payload `{repo: "instruments-service", branch: "main", version: "<current>", repo_type: "service"}`. `ci-status-update` dispatched to PM. PM `cloud-build-router.yml` fires and routes to `uts-prod-ikenna`.
    status: pending
  - id: cascade-library-bump
    content: |
      - [ ] [HUMAN+AGENT] P0. Push `fix:` commit to unified-events-interface main (or merge PR). After version-bump fires, verify PM `update-repo-version.yml` run: (a) `workspace-manifest.json` updated with new UEI version, (b) PM pyproject.toml patch bumped, (c) `validate-manifest-dag.py` cycle check passes, (d) downstream dependents computed from manifest — instruments-service IS a UEI dependent, (e) `dependency-update` dispatched to instruments-service and all UEI-dependent repos, (f) repos that DON'T depend on UEI receive NO dispatch. Command: `gh run list --repo IggyIkenna/unified-trading-pm --workflow update-repo-version.yml --limit 1`.
    status: pending
  - id: cascade-concurrent-bumps
    content: |
      - [ ] [HUMAN+AGENT] P0. Simultaneously trigger version-bump dispatches from 3 repos (UEI, UCI, UTL). Verify: `concurrency: manifest-update` serializes all 3. Each manifest commit is sequential (no race conditions, no lost writes). Final manifest state has all 3 version updates. Command: 3x `gh api repos/IggyIkenna/unified-trading-pm/dispatches -X POST -f event_type="version-bump"`.
    status: pending
  - id: cascade-instruments-receives-update
    content: |
      - [ ] [AGENT] P1. After cascade-library-bump, verify instruments-service received `dependency-update` dispatch. `update-dependency-version.yml` in instruments-service fires. pyproject.toml constraint updated with `[skip ci]` commit.
    status: pending
  - id: staging-breaking-change
    content: |
      - [ ] [HUMAN+AGENT] P0. Push `feat!:` commit to instruments-service staging branch. Verify: (a) `staging-lock-check.yml` reads `staging_status.locked` from manifest, (b) semver-agent fires after QG passes on staging, (c) semver-agent computes MINOR bump (pre-1.0.0 override: feat! on 0.x.x = MINOR not MAJOR), (d) version-bump dispatched to PM with `branch: "staging"`, (e) PM `update-repo-version.yml` sets `staging_versions["instruments-service"]` and records in `staging_commits`.
    status: pending
  - id: staging-sit-lock-cycle
    content: |
      - [ ] [HUMAN+AGENT] P0. Manually dispatch `sit-lock` to PM: `gh api repos/IggyIkenna/unified-trading-pm/dispatches -X POST -f event_type="sit-lock" -f client_payload='{"repos":["instruments-service"],"commit_shas":{"instruments-service":"<sha>"}}'`. Verify: (a) `staging_status.locked=true` in manifest, (b) `staging_commits["instruments-service"]` contains SHA, (c) `staging-locked` dispatched to all repos, (d) Telegram "SIT locked" received. Then dispatch `sit-failed`. Verify: (e) `staging_status.locked=false`, (f) GH issue with `sit-failure` label, (g) Telegram "SIT failed" received, (h) `staging-unlocked` dispatched.
    status: pending
  - id: staging-promotion
    content: |
      - [ ] [HUMAN+AGENT] P0. Manually dispatch `staging-validated` to PM. Verify: (a) `staging-to-main.yml` fires, (b) idempotency: 2nd dispatch of same staging_commits = no-op, (c) readiness gate checks codex YAML, (d) SHA pinning verifies staging HEADs match staging_commits, (e) PR staging->main created for each repo, (f) `staging_versions` promoted to `versions`, (g) `staging_status.locked=false`, (h) dependency-update cascade dispatched, (i) `staging-unlocked` dispatched.
    status: pending
  - id: agent-semver-label-analysis
    content: |
      - [ ] [HUMAN+AGENT] P0. Test semver-agent with 3 commit types on instruments-service staging: (1) `fix: patch test` -> expect PATCH, (2) `feat: minor test` -> expect MINOR, (3) `feat!: breaking test` -> expect MINOR (pre-1.0.0 override). Also test label mismatch: commit says `fix:` but `__init__.py` has removed exports -> agent should post FAILING status.
    status: pending
  - id: agent-conflict-resolution
    content: |
      - [ ] [HUMAN+AGENT] P0. Create deliberate conflict: edit same line differently on `feat/e2e-test` and `staging` in instruments-service. Trigger merge. Verify: (a) `merge-conflict-detected` dispatched, (b) conflict-resolution-agent.yml fires, (c) Telegram "working" received, (d) agent clones repo+PM+codex, (e) Claude resolves conflicts, (f) output validated (no `<<<<<<<` markers), (g) resolution branch pushed, (h) QG runs (advisory), (i) PR created with `AUTO_RETRY_PROMOTION: true`, (j) Telegram "done" with PR URL, (k) agent does NOT self-merge.
    status: pending
  - id: agent-overnight-dry-run
    content: |
      - [ ] [HUMAN+AGENT] P1. Trigger overnight orchestrator dry run: `gh workflow run overnight-agent-orchestrator.yml -f dry_run=true -f tiers=0`. Verify: (a) T0 repos dispatched to `agent-audit.yml`, (b) dry_run=true skips polling, (c) T1/T2/T3 NOT triggered, (d) Telegram summary fires.
    status: pending
  - id: agent-rules-alignment
    content: |
      - [ ] [HUMAN+AGENT] P1. Push plan change to PM main with new architectural constraint. Verify: `rules-alignment-agent.yml` fires, Claude checks cursor-rules coverage, Telegram notification.
    status: pending
  - id: agent-plan-health
    content: |
      - [ ] [HUMAN+AGENT] P1. Trigger: `gh workflow run plan-health-agent.yml -f dry_run=true`. Verify: Claude reads all active plans, checks contradictions, `dry_run=true` means no git mv. Telegram fires.
    status: pending
  - id: failure-sit-rollback
    content: |
      - [ ] [HUMAN+AGENT] P0. Dispatch `sit-failed` to PM. Verify: `sit-unlock.yml` sets `staging_status.locked=false`, GH issue created with `sit-failure` label, Telegram alert fires, `staging-unlocked` dispatched to all repos.
    status: pending
  - id: failure-cloud-build-timeout
    content: |
      - [ ] [AGENT] P1. Inspect `cloud-build-router.yml` polling logic. Verify: `MAX_POLLS=60` with 30s sleep = 30 min timeout. On timeout, status reported as non-SUCCESS, Telegram alert sent. `TIMEOUT` in terminal statuses list. Static verification — actual timeout requires GCP infra.
    status: pending
  - id: failure-claude-api-down
    content: |
      - [ ] [HUMAN+AGENT] P1. Trigger `claude-api-health-monitor.yml`. Test state-transition: healthy->degraded sends alert, degraded->degraded does NOT repeat. Set invalid `ANTHROPIC_API_KEY_SYSHEALTH` to simulate. Verify: error classified correctly (auth_error), single Telegram alert.
    status: pending
  - id: failure-manifest-corruption
    content: |
      - [ ] [SCRIPT] P1. Scan all 6 manifest-mutating workflows for corruption guards: JSON validation with rollback (`git checkout -- workspace-manifest.json`), atomic write (`.json.tmp` + rename). Workflows: update-repo-version.yml, staging-to-main.yml, sit-gate.yml, sit-unlock.yml, hotfix-mode.yml, cloud-build-router.yml. Verify all 6 have both patterns.
    status: pending
  - id: failure-telegram-inventory
    content: |
      - [ ] [HUMAN+AGENT] P0. Enumerate and verify all 19 Telegram alert types across all workflows: (1) Overnight summary, (2) T0 failure escalation, (3) Conflict detected+working, (4) Conflict resolved/failed, (5) Conflict merged retry, (6) Codex sync, (7) Rules alignment, (8) Plan health, (9) Plan notification, (10) Plan approval, (11) SIT locked (gap? verify), (12) SIT failed, (13) MAJOR bump pending (opens issue, check Telegram), (14) MAJOR bump approved, (15) Cloud Build failure, (16) Claude API state change, (17) Cassette drift, (18) Readiness verifier, (19) Semver agent result. For each: verify fires with correct content.
    status: pending
  - id: failure-market-hours-guard
    content: |
      - [ ] [HUMAN+AGENT] P0. Test market hours deployment guard: trigger Cloud Build for execution-service during simulated market hours. Verify: build is rejected with "market hours active — use force_deploy: true to override" message. Then trigger with force_deploy=true and verify it proceeds.
    status: pending
  - id: failure-tier-deploy-ordering
    content: |
      - [ ] [HUMAN+AGENT] P0. Test tier-ordered deployment: simultaneously trigger Cloud Build for execution-service (T4) and unified-market-interface (T2). Verify: T2 deploys first, T4 waits until T2 deployment confirmed. If T2 fails, T4 should not deploy.
    status: pending
  - id: failure-partial-staging-promotion
    content: |
      - [ ] [HUMAN+AGENT] P1. Test partial staging→main promotion: set up 3 repos for promotion, then break the 2nd (e.g., set its branch protection to reject). Verify: promotion fails at repo 2, repos 1 already on main, repos 2-3 still on staging. Verify Telegram alert shows partial state. Verify retry-from-failure dispatch resumes from repo 2 without re-promoting repo 1.
    status: pending
  - id: failure-overnight-dead-man-switch
    content: |
      - [ ] [HUMAN+AGENT] P1. Test dead man's switch: verify the 03:00 UTC scheduled check runs and can detect a missing overnight run. Simulate by checking if the workflow correctly reports "no overnight run in last 24 hours" when the overnight orchestrator hasn't fired.
    status: pending
  - id: failure-post-deploy-health-check
    content: |
      - [ ] [HUMAN+AGENT] P1. Test post-deploy health check: after Cloud Build success, verify the workflow polls the service /health endpoint before marking deployment as successful. If health check fails, verify deployed_versions is NOT updated and Telegram alert fires.
    status: pending
  - id: failure-canary-traffic-split
    content: |
      - [ ] [HUMAN+AGENT] P1. Test canary deployment: trigger prod deploy of instruments-service with canary_mode=true. Verify: (a) Cloud Run creates new revision with 5% traffic split (not 100%), (b) health metrics collected for 5 min, (c) on healthy: auto-promote to 100%, (d) simulate unhealthy canary: auto-rollback to old revision (instant, no rebuild). Also test shard-based canary: route 2 venue shards to new version, verify data processed correctly before full promotion.
    status: pending
  - id: failure-position-reconciliation
    content: |
      - [ ] [HUMAN+AGENT] P0. Test position reconciliation gate: before execution-service prod deploy, verify the workflow snapshots open positions, deploys, re-queries, and diffs. Simulate a position mismatch (mock /positions to return different data) and verify auto-rollback fires with Telegram "position reconciliation failed".
    status: pending
  - id: failure-kill-switch
    content: |
      - [ ] [HUMAN+AGENT] P0. Test trading kill switch: trigger execution-service prod deploy. Verify: (a) halt-order-flow dispatched, (b) execution-service enters drain mode (verify via /readiness returning 503), (c) deploy completes, (d) resume-order-flow dispatched, (e) /readiness returns 200. Also test failure case: deploy fails, verify order flow stays halted + Telegram fires.
    status: pending
  - id: failure-manifest-audit-log
    content: |
      - [ ] [SCRIPT] P1. After Plan 1 implements manifest audit log: verify every manifest mutation appends to `manifest_audit_log[]`. Run 3 manifest-mutating operations (version-bump, sit-lock, staging-to-main) and verify each produces an audit entry with {timestamp, workflow, actor, field_changed, old_value, new_value}. Verify entries are append-only (no deletions).
    status: pending
  - id: failure-sit-chaos-load
    content: |
      - [ ] [HUMAN+AGENT] P1. SIT currently tests happy paths and some failure modes but no: (a) latency regression — run SIT with injected 200ms network delay on inter-service calls, verify no timeout cascades, (b) chaos — randomly kill 1 service pod during SIT, verify remaining services degrade gracefully (not cascade fail), (c) market stress — replay 1000x normal tick rate, verify no message drops or OOM. Use instruments-service + market-tick-data-service as chaos targets.
    status: pending
  - id: failure-change-freeze-blocks-autonomous
    content: |
      - [ ] [SCRIPT] P1. Verify change-freeze-check blocks overnight-agent-orchestrator during an active freeze window. Method: mock current UTC time to NFP window (first Friday of month, 13:30 UTC) by overriding the time-check step in change-freeze-check.yml using a workflow_dispatch input `override_utc_time` (test-only). Trigger overnight-agent-orchestrator.yml manually during the mock window. Expected: job 0 (change-freeze-check) outputs blocked=true, reason="NFP window — US Non-Farm Payrolls 13:25–14:00 UTC", orchestration jobs are skipped, Telegram message "not running — change freeze active: NFP window". Also test with mock time outside all windows: verify blocked=false and orchestration proceeds normally. Verify with: `gh run view --log | grep -E "blocked|change freeze"`.
    status: pending
  - id: failure-change-freeze-blocks-prod-deploy
    content: |
      - [ ] [SCRIPT] P1. Verify change-freeze-check blocks cloud-build-router prod path during a MACRO freeze window. Method: trigger cloud-build-router.yml manually with `branch=main` and `override_utc_time` set to FOMC decision time (18:00 UTC on a known Fed meeting date). Expected: prod Cloud Build trigger is skipped, Telegram message "prod deploy blocked — change freeze: FOMC rate decision 18:00–19:00 UTC. Next window ends: 19:00 UTC". Dev and staging paths must NOT be blocked (MACRO rows block_prod_deploy=true but session rows block_prod_deploy=false for staging — verify correct flag filtering). Verify: `gh run view --log | grep -E "PROD_DEPLOY|blocked|FOMC"`.
    status: pending
  - id: failure-change-freeze-crypto-nfp
    content: |
      - [ ] [SCRIPT] P1. Verify that crypto/DeFi/sports/Polymarket prod deploys are also blocked during MACRO events (not just equities). NFP and FOMC rows have affects_venues=all — enforcement must apply regardless of service type. Method: trigger cloud-build-router.yml with branch=main, repo=hyperliquid-gateway (DeFi venue), override_utc_time=NFP window. Expected: blocked=true. DeFi deploy does NOT proceed during NFP. Also test SESSION windows (e.g. US open 13:30 UTC) with block_prod_deploy=false on session rows: Expected: blocked=false for prod deploy check (session windows only block autonomous agents, not deploys). Verify the distinction is correctly enforced based on check_type input (AUTONOMOUS vs PROD_DEPLOY).
    status: pending
  - id: failure-change-freeze-dst-transition
    content: |
      - [ ] [SCRIPT] P2. Verify DST transition handling in change-freeze-check. European session open shifts from 07:00 UTC to 08:00 UTC when BST ends (last Sunday October). Mock time to 07:15 UTC on the day after UK DST ends — without DST adjustment this would be inside European session open window; with correct DST adjustment it should be outside. Expected: blocked=false after DST end (07:15 UTC is no longer inside EU session open window post-BST). Also test US EDT→EST transition: US open shifts from 14:30 UTC to 13:30 UTC when US DST ends. Ensures change-freeze-calendar.csv DST companion data + enforcement logic are correct.
    status: pending
  - id: codex-manifest-sync
    content: |
      - [ ] [HUMAN+AGENT] P0. Push change to `workspace-manifest.json` or `plans/**` on PM main. Verify: `manifest-sync.yml` fires, `repository_dispatch: manifest-updated` sent to unified-trading-codex. Command: `gh run list --repo IggyIkenna/unified-trading-pm --workflow manifest-sync.yml --limit 1`.
    status: pending
  - id: codex-sync-agent
    content: |
      - [ ] [AGENT] P1. Verify `codex-sync-agent.yml` in unified-trading-codex fires on `repository_dispatch: manifest-updated`. Claude Haiku processes manifest + active plans. Telegram notification.
    status: pending
  - id: codex-readiness-verifier
    content: |
      - [ ] [HUMAN+AGENT] P1. Trigger: `gh workflow run readiness-verifier.yml -f repo_filter=instruments-service`. Verify: codex YAML for instruments-service read and checked. Readiness report generated.
    status: pending
  - id: codex-diagram-accuracy
    content: |
      - [ ] [AGENT] P1. Compare CI/CD diagram YAML (`docs/repo-management/cicd-pipeline-definition.yaml`) nodes vs actually deployed workflows. Every workflow should have a corresponding node. Every connection should reflect a real dispatch/trigger relationship. Zero missing nodes or connections.
    status: pending
  - id: golden-path
    content: |
      - [ ] [HUMAN+AGENT] P0. Full instruments-service golden path: (1) `fix: golden path test` commit, (2) push + PR to main, (3) QG fires, (4) merge PR, (5) QG fires on push, (6) `qg-passed` dispatched to PM, (7) Cloud Build routes to `uts-prod-ikenna`, (8) `ci-status-update` dispatched, manifest updated, (9) `manifest-sync.yml` fires, codex dispatch, (10) total wall-clock < 30 min. Every Telegram alert at each stage verified.
    status: pending
isProject: false
---

## Notes

### SIT Architecture (Build Source, Gates, Race Protection)

**Build source (Option A):** SIT uses build-from-source — clones v1 repos from the **staging** branch before compose,
then builds Docker images locally. SIT does not pull pre-built images from Artifact Registry. Ensures SIT tests exactly
what will be promoted to main.

**build-smoke vs SIT deployment-tests:**

- `build-smoke-all-repos.yml`: Per-repo build verification — each repo builds (Docker or wheel) in isolation. No
  integration.
- SIT deployment-tests: Integration tests against the staged stack — services talk to each other, contracts validated,
  E2E flows.

**Staging, debounce, Cloud Build interaction:**

- Flow: merge to staging → sit-gate → debounce (5 min quiet) → smoke-test-gate → staging-validated → staging-to-main.
- Cloud Build fires on `qg-passed` (merge to main or QG success on staging), not on every PR or feat/ push.

**Race-condition protection:**

- Debounce: 5-minute quiet window; timer resets on every new merge to staging. Prevents queue storms and SIT starvation.
- sit-staging concurrency group: All SIT-related workflows use
  `concurrency: { group: sit-staging, cancel-in-progress: false }` so only one SIT run executes at a time.

### Guinea Pig Selection Rationale

**instruments-service:**

- Leaf service (zero downstream dependents) — changes won't cascade and break other repos
- 9 library dependencies spanning T0-T3 — exercises the full dependency graph
- Highest version among services (0.1.22 in manifest) — most iteration history
- Pure service type (no UI, no batch) — canonical execution path
- MIN_COVERAGE=70, RUN_INTEGRATION=false — simpler QG, faster feedback

**unified-events-interface (for cascade):**

- T0 library with many downstream dependents
- Version-bump here triggers `dependency-update` to most of the workspace
- Tests the selective DAG dispatch (only direct dependents, not transitive)

### Key Finding: instruments-service Version Mismatch

Manifest says `0.1.22`, pyproject.toml says `0.1.117`. This is BUG-7 in the Rollout plan and itself a test case for the
static validation phase.

## Coordination: ui-api-alerting-observability plan

The ui-api-alerting-observability-2026-03-14 plan creates a notify-telegram.yml reusable workflow that centralizes all
Telegram notifications. E2E validation of Telegram patterns should test this reusable workflow rather than inline curl
patterns in individual workflows.
