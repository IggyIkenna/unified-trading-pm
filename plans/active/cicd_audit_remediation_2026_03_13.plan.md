---
name: cicd-audit-remediation-2026-03-13
overview: >
  Remediates all P0/P1/P2 issues identified in the 2026-03-13 CI/CD pipeline audit. Adds diagram auto-regeneration to PM
  quickmerge so the YAML remains the SSOT and the SVG/HTML are always current. Extends the diagram and CI-CD-FLOW.md to
  show the active-plan-driven agent context cascade: plan → codex → cursor rules → agent context → implementation → dual
  TG approval gates (plan sign-off + merge sign-off). Adds E2E tests for every fix, exercised via admin sync scripts
  where GHA trigger is needed.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C4
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C4
    deployment: none
    business: none
    readiness_note: "DR N/A: infra-only. BR N/A: internal tooling."
  - repo: system-integration-tests
    code: C3
    deployment: none
    business: none
    readiness_note: "P0 rollback + SHA-pinning tests live here."

depends_on:
  - cicd_e2e_test_plan_2026_03_13
  - conflict_resolution_agent_2026_03_13
  - full_autonomous_agent_ci

todos:
  # ── Diagram SSOT (do first — unblocked) ──────────────────────────────────

  - id: diagram-regen-in-quickmerge
    content: >
      Make the CI/CD diagram regenerate automatically as part of PM quality gates so it can never drift from the YAML
      SSOT. Steps: (1) In scripts/quality-gates.sh, after the final `source` line, add:
          echo "Regenerating CI/CD pipeline diagram..."
          python3 "${REPO_ROOT}/scripts/generate-cicd-diagram.py"
      (2) Add generate-cicd-diagram.py to all codex EXCLUDE_GLOBS arrays in
          quality-gates.sh so basedpyright/codex checks skip it.
      (3) Verify: run bash scripts/quality-gates.sh, confirm SVG/HTML updated. Acceptance: every PM quickmerge that
      touches cicd-pipeline-definition.yaml or generate-cicd-diagram.py auto-regenerates the outputs.
    status: pending

  - id: fix-conflict-node-semantics
    content: >
      The 'conflict detected?' diamond has inverted YES/NO visual semantics: red NO badge goes to staging_to_main
      (proceed), confusing readers. Fix in cicd-pipeline-definition.yaml: (1) Rename node label to "merge\nconflict?"
      (shorter, unambiguous). (2) Connection conflict_detected → staging_to_main: change outcome to
          "yes" (green — "yes, conflict free, proceed") and label "clean".
          Wait — actually flip: rename label to "conflict\nfree?" so:
          YES (green) → staging_to_main (no conflict, proceed)
          NO (red)    → conflict_agent + tg_conflict_detected (conflict exists)
      (3) Update all connection labels and outcomes accordingly. (4) Regenerate diagram. Acceptance: green YES goes to
      staging_to_main, red NO goes to conflict agent.
    status: pending

  - id: fix-staging-locked-swimlane
    content: >
      staging_locked_decision is in 'developer' swimlane but the decision is made by GHA (reads staging_status.locked
      from workspace-manifest.json via staging-lock-gate required status check). Move to 'gha_repo' swimlane. Check col
      spacing against gha_repo neighbours after move. Regenerate diagram.
    status: pending

  - id: add-missing-connections
    content: >
      Add connections that are real but missing from the diagram: (1) staging_to_main → manifest_sync  (implicit PM push
      triggers it; make
          it explicit so codex sync on SIT path is visible).
      (2) plan_alignment annotation: add to annotations section —
          text "advisory: no merge gate" position below.
      (3) Add 'no SIT path' annotation near breaking_decision for PM/codex. Regenerate.
    status: pending

  - id: add-plan-cascade-nodes
    content: >
      Add the plan-driven agent context cascade to the diagram. This is the central governance model: plans are the
      canonical context for all agent decisions. New nodes:

      plan_lifecycle (gha_pm, col 1.5, branch agent):
        "Plan created/updated\nactive plans/\nagent or human"
        actor: "Human or agent writes plan;\nPM main push fires cascade"

      tg_plan_ready (telegram, col 3.5, branch agent):
        "📋 Plan ready\nfor human\nreview"
        tooltip: "Telegram notification on plan creation. Human must sign off
          before agent begins implementation. Only two human gates in the
          system: (1) plan approval, (2) merge approval."

      tg_merge_ready (telegram, col 6.0, branch agent):
        "🔀 Agent PR ready\nhuman review\n& TG merge gate"
        tooltip: "Second and final human gate. Agent-opened PRs require
          explicit human approval in TG before auto-merge fires. Ensures
          human oversight on all agent-driven changes."

      tg_cloud_build_fail (telegram, col 4.8, branch both):
        "🔴 Build failed\n$REPO $BRANCH\nCloud Build"
        tooltip: "Sent when GCP Cloud Build returns non-zero exit. Currently
          NOT IMPLEMENTED — tracked in add-cloud-build-fail-alert todo.
          Marked ⚠️ pending in diagram."

      New connections:
        plan_lifecycle → rules_alignment   (cascades to cursor rules)
        plan_lifecycle → manifest_sync     (cascades to codex)
        plan_lifecycle → tg_plan_ready     (human review notification)
        conflict_agent → tg_merge_ready   (agent PR → second TG gate)
        build_dev → tg_cloud_build_fail    (dashed, pending impl)
        build_staging → tg_cloud_build_fail (dashed, pending impl)
        build_prod → tg_cloud_build_fail   (dashed, pending impl)

      Add annotation on conflict_agent:
        "Context: active plans + codex\n+ AGENTS.md + cursor rules\n
         Human approves plan first"

      Regenerate diagram.
    status: pending

  # ── P0 code fixes ──────────────────────────────────────────────────────────

  - id: fix-semver-staging-trigger
    content: >
      Blocked on: full_autonomous_agent_ci plan § fix-semver-agent-template- staging-trigger. The semver-agent.yml
      template currently fires on 'main' push. Must be fixed to fire on 'staging' push only. Also: atomically disable
      version-bump.yml (set if: false) when semver- agent rolls out to prevent double-bump. Test: push feat: commit to a
      T2 repo, verify ONLY one version bump fires, verify it fires on staging push not main push.
    status: pending
    blocks: fix-semver-agent-template-staging-trigger (full_autonomous_agent_ci)

  - id: add-sit-rollback
    content: >
      When SIT fails, sit-unlock.yml clears the lock but leaves broken code in staging with no automated recovery
      signal. Add: (1) In sit-unlock.yml, after clearing the lock, create a GH Issue
          "SIT failed: staging needs fix or revert — $LOCK_VERSION" with label
          'sit-failure' and assignee the last PR author.
      (2) Optionally: open a revert PR to last_known_good_sha (the SHA before
          the failing commit set). Record last_known_good_sha in
          staging_status when sit-gate.yml fires.
      (3) Update diagram: add sit_rollback_issue node in gha_pm, connection
          from sit_unlock_fail → sit_rollback_issue.
      Test: force a SIT failure via admin sync, verify issue is opened. Acceptance: engineers know immediately what
      broke and can act without checking GHA logs manually.
    status: pending

  - id: add-cascade-cycle-guard
    content: >
      update-repo-version.yml dispatches dependency-update to all direct dependents per manifest DAG. A cycle (repo A
      depends B depends A) causes infinite dispatch. Fix: (1) Before dispatching in update-repo-version.yml, run a DFS
      cycle check
          on the dependency subgraph for the triggering repo.
      (2) If cycle detected: send Telegram alert "⚠️ Dependency cycle detected
          involving $REPO — cascade aborted. Check workspace-manifest.json."
          and exit 1 (do NOT dispatch).
      (3) Add cycle-check to validate-alignment.py or a new
          validate-manifest-dag.py script, run in quality-gates.sh.
      Test: introduce a deliberate cycle in a test manifest branch, verify cascade aborts and Telegram fires.
      Acceptance: no infinite dispatch loops possible.
    status: pending

  - id: fix-sha-pinning-toctou
    content: >
      Current flow: staging push → 10-min debounce → sit-gate.yml fires → records staging_commits SHAs. But if a [skip
      ci] constraint commit lands during the debounce, it's in staging but not in the tested SHA set. staging_to_main
      promotes the full current staging (including untested [skip ci] commits), creating a gap between tested and
      deployed state. Fix: (1) Record staging_commits SHAs at END of smoke-test-gate.yml debounce
          (immediately before dispatching to SIT), not when sit-gate.yml fires.
          This captures the full staging state at the moment testing begins.
      (2) In staging-to-main.yml, verify that current staging HEAD is within
          the tested SHA set (or is a [skip ci] descendant of a tested SHA).
          If not, re-trigger SIT before promoting.
      Test: push a [skip ci] commit during SIT run, verify it gets included in the next SIT set or blocked from
      promotion.
    status: pending

  # ── P1 silent failure fixes ───────────────────────────────────────────────

  - id: add-cloud-build-fail-alert
    content: >
      Cloud Build failures are currently silent — GHA dispatches fire-and-forget. Fix options (in priority order): (1)
      Configure Cloud Build to publish build results to a GCP Pub/Sub topic.
          Create a GHA workflow cloud-build-status.yml that subscribes via
          Cloud Build webhook (or polls the Cloud Build API) and fires Telegram
          on non-SUCCESS status.
      (2) Alternative (simpler): Add a polling step in cloud-build-router.yml
          after each trigger — poll gcloud builds list --filter="id=$BUILD_ID"
          every 30s until COMPLETE or FAILURE, then send Telegram.
      Preferred: option (2) is simpler, no new GCP infra needed. Telegram format: "🔴 Cloud Build FAILED\nRepo:
      $REPO\nBranch: $BRANCH\n
        Build: $BUILD_URL\nTriggered by: $SHA"
      Update diagram: add tg_cloud_build_fail connections from build nodes. Test: introduce a deliberate Docker build
      failure, verify alert fires.
    status: pending

  - id: add-major-bump-approval-handler
    content: >
      MAJOR bump creates a GitHub Issue and fires Telegram but there is no workflow listening for human /approve or
      /reject. This means MAJOR bumps are permanently blocked. Fix: Create .github/workflows/major-bump-approval.yml in
      PM:
        - trigger: issue_comment (created)
        - filter: issue has label 'major-bump-pending'
        - if comment body starts with '/approve':
            update manifest.versions[$REPO] to MAJOR version,
            dispatch version-updated to $REPO,
            close issue, Telegram "✅ MAJOR bump approved: $REPO v$VERSION"
        - if comment body starts with '/reject':
            close issue with 'rejected' label,
            Telegram "❌ MAJOR bump rejected: $REPO — staying at $CURRENT"
      Test: manually trigger request-major-bump.yml, comment /approve, verify version promoted and issue closed.
    status: pending

  - id: add-conflict-agent-timeout
    content: >
      conflict-resolution-agent.yml has no timeout. If Claude API is degraded the job hangs indefinitely, team sees
      "working on it..." forever. Fix: (1) Add 'timeout-minutes: 30' to the conflict-resolution-agent job. (2) Add a
      final step with 'if: failure()' that sends Telegram:
          "⏰ Conflict agent timed out on $REPO — resolve manually. Branch:
           $BRANCH. Conflicting files: $FILES_LIST."
      (3) Set the Telegram message from step (a) (the "working" message) to
          include an ETA: "agent active, ~10 min, will notify when done."
      Test: mock a long-running agent by adding sleep 2000 in a test workflow, verify timeout fires and Telegram message
      is sent.
    status: pending

  - id: add-overnight-t0-escalation
    content: >
      Overnight orchestrator currently sends one Telegram summary at end. If T0 (core libraries) has any failures, the
      whole system may be running against broken interfaces — but this isn't surfaced until someone reads the morning
      message. Fix in overnight-agent-orchestrator.yml: (1) After T0 tier completes, check if any T0 repos failed. (2)
      If any T0 failures: immediately send a PRIORITY Telegram alert
          (separate from morning summary): "🚨 T0 FAILURE — overnight audit.
           Core libraries failing: $FAILING_REPOS. T1-T3 results unreliable.
           Immediate action required."
      (3) Open a GitHub Issue in PM: "Overnight T0 failure: $DATE — $REPOS"
          with label 'critical-audit-failure'.
      (4) Morning summary still fires (with all tier results). Test: force a T0 repo to fail in overnight audit (set
      exit 1 in test job), verify priority Telegram fires before T1 runs.
    status: pending

  # ── Bot tier isolation & Claude availability ─────────────────────────────
  # Three bot tiers, each with a dedicated API key (separate Anthropic project):
  #   CICD bots      — conflict-resolution, semver, rules-alignment, codex-sync
  #                    (critical path, triggered by human actions, must never be rate-limited)
  #   SysHealth bots — overnight-agent-orchestrator, agent-audit, health-monitor, cassette-drift
  #                    (scheduled/batch, high volume, can be deferred without blocking humans)
  #   Analysis bots  — trading quality, performance, scenario analysis (FUTURE PHASE)
  #                    (separate concern — PnL loss ≠ code quality; deployment decisions manual)

  - id: add-three-tier-bot-api-keys
    content: >
      All agent workflows share a single ANTHROPIC_API_KEY. When overnight audit (65 repos in parallel) exhausts the
      rate limit it blocks conflict-resolution agent — which the team needs immediately to unblock a stuck staging
      merge. Three bot tiers map cleanly to three separate Anthropic project keys:
        ANTHROPIC_API_KEY_CICD      — conflict-resolution-agent.yml,
                                       rules-alignment-agent.yml, codex-sync-agent.yml,
                                       semver-agent.yml. Critical path, low volume,
                                       must never be rate-limited by batch work.
        ANTHROPIC_API_KEY_SYSHEALTH — overnight-agent-orchestrator.yml,
                                       agent-audit.yml (all 65 repos via propagate),
                                       claude-api-health-monitor.yml,
                                       cassette-drift-check.yml. Scheduled/batch.
                                       Rate limits here are deferrable; conflicts are not.
        ANTHROPIC_API_KEY_ANALYSIS  — FUTURE: trading-quality-agent, performance-analysis,
                                       scenario-analysis. Separate Anthropic project so
                                       analysis quota never touches CI/CD or health.
                                       Not wired yet — placeholder secret only.
      Fix: (1) Create and register the three GH secrets (PM repo + propagate SYSHEALTH to
          all 65 service repos via propagate-github-secrets.sh).
      (2) Update each workflow env block with fallback to shared key:
            ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_CICD
                                  || secrets.ANTHROPIC_API_KEY }}
          Fallback enables gradual rollout without breaking existing workflows.
      (3) Document in docs/repo-management/agent-api-keys.md:
          tier → key → workflows → quota budget → rotation cadence.
      (4) Update diagram annotations (done: overnight=SYSHEALTH, conflict=CICD). Acceptance: overnight audit rate-limit
      does not affect conflict-resolution or semver agents in the same time window.
    status: pending

  - id: add-api-failure-classification
    content: >
      All agent workflows treat any Claude API error identically — job fails, timeout fires, no context. Different error
      modes need different responses:
        401/403 → key invalid/expired: NEVER retry. Open GH Issue
                  "ANTHROPIC_API_KEY_<TIER> invalid — rotate immediately."
                  Telegram "⛔ Auth error — {tier} key needs rotation."
        429/529 → rate limited / model overloaded: retry 3× with 15s/60s/300s
                  backoff. If still failing after 3 attempts: graceful skip +
                  Telegram "⚠️ {tier} rate limited — deferred to next cycle."
        503 / connection refused → Claude infra down: no retry. Telegram
                  "⛔ Claude unreachable — check status.anthropic.com. {tier}
                  agents skipped; will retry at next scheduled run." Exit 0.
        Timeout → job exceeded timeout-minutes: Telegram with repo + branch
                  + CLAUDE_ERROR_CLASS=timeout. Exit 1.
        Unknown → Telegram with first 200 chars of stderr for triage.
      Fix: (1) Create unified-trading-pm/scripts/claude-helpers.sh:
          Function classify_claude_error(stderr_file, tier, repo, branch):
            - Grep stderr for "401"/"403"/"unauthorized", "429"/"529"/"rate",
              "503"/"unavailable"/"connection refused", to set CLAUDE_ERROR_CLASS.
            - Export CLAUDE_ERROR_CLASS + CLAUDE_ERROR_MSG.
            - Send typed Telegram alert (emoji + class + tier + repo + branch).
            - Return 0 on service_down; 1 on auth_error; 2 on rate_limited.
      (2) Create composite action .github/actions/handle-claude-api-error/action.yml:
          Inputs: stderr_path, tier (cicd|syshealth|analysis), agent_name.
          Calls classify_claude_error; outputs error_type + should_retry + retry_delay_s.
      (3) Source claude-helpers.sh in all CICD and SYSHEALTH agent workflows.
          agent-audit.yml retry loop already exists — just classify before re-dispatch.
      (4) conflict-resolution-agent.yml already has timeout-minutes: 30;
          add 'if: failure()' final step calling classify_claude_error with
          CLAUDE_ERROR_CLASS=timeout.
      Test: run workflow with invalid key (wrong last char) — verify exactly one Telegram "⛔ Auth error — cicd key
      needs rotation" fires, job exits, no retry.
    status: pending

  - id: add-claude-api-health-preflight
    content: >
      Agents begin cloning repos and installing Claude CLI before discovering the API is unreachable — wasting 3–5 min
      per job and producing uninformative failures. Two-layer fix:

      Layer A — Per-agent pre-flight (first step in every agent workflow):
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY_CICD || secrets.ANTHROPIC_API_KEY }}
        run: |
          timeout 30 claude --print "ping: respond with OK" 2>preflight_err.txt \
            | grep -qi "ok" && echo "Claude API: healthy" \
            || { source unified-trading-pm/scripts/claude-helpers.sh
                 classify_claude_error preflight_err.txt cicd $(basename $PWD) preflight
                 exit $?; }
        On service_down (exit 0): skip gracefully, no pipeline failure.
        On key_invalid (exit 1): alert + fail job so key rotation is visible.
        Overnight orchestrator: runs health check ONCE before dispatching T0
        to prevent 65 agent-audit.yml jobs all failing silently. On failure:
        Telegram "🔴 Overnight audit SKIPPED — Claude unreachable at <UTC>.
        Next cron: 01:00 UTC. No T0–T3 runs fired." and exit 0.

      Layer B — Dedicated health monitor cron (state-transition alerts only):
        File: .github/workflows/claude-api-health-monitor.yml
        Schedule: "*/15 * * * *"  (every 15 min, uses ANTHROPIC_API_KEY_SYSHEALTH)
        timeout-minutes: 2
        Logic:
          - Run 30s preflight ping.
          - Read previous state from GH Actions cache key "claude-health-state".
          - If state CHANGED (healthy→degraded or degraded→healthy): send Telegram.
            "⚠️ Claude API degraded at 14:30 UTC — 429 on SYSHEALTH key." or
            "✅ Claude API recovered at 14:45 UTC."
          - Do NOT send Telegram if state unchanged (no spam every 15 min).
          - Write new state to cache.
        This gives proactive alerting BEFORE the overnight cron fires.
        Also covers: can Claude itself be pinged to check for issues? Yes —
        this workflow IS that check, running independently of all agent work.
      Diagram: api_health_preflight + tg_api_key_failure nodes already added (2026-03-13). Annotations updated to show
      tier key assignments. Acceptance: Anthropic incident → no agent wastes >30s, clear Telegram fires once, all
      SYSHEALTH skips gracefully, CICD agents unaffected.
    status: pending

  # ── Plan-driven agent context (new governance model) ─────────────────────

  - id: add-conflict-plan-context
    content: >
      conflict-resolution-agent.yml currently reads AGENTS.md + plans in its prompt. Strengthen this to ensure plans are
      the PRIMARY context: (1) In the agent prompt, add explicit instruction: "Read ALL files in
          active plans/ directory. The active plans define WHAT should be
          implemented and WHY. When resolving a conflict, determine which
          resolution is consistent with the relevant active plan's intent.
          If the conflict touches a planned feature, preserve the plan's
          design. Reference the plan in your PR description."
      (2) Clone PM repo in agent workflow (already done), ensure
          plans/active/*.plan.md are read in the prompt construction step.
      (3) Add plan context to the PR body template: "Resolution guided by
          plan: [plan-name] §[relevant-todo-id]"
      This is the core of plan-driven conflict resolution — the plan is the tie-breaker when two changes conflict.
    status: pending

  - id: add-tg-plan-approval-gate
    content: >
      Currently there is no Telegram notification when a new plan is created or updated in PM active plans/. Human
      review of plans happens out-of-band. Fix: add a new step to rules-alignment-agent.yml or create a separate
      plan-notification.yml that fires when plans/active/*.plan.md changes: (1) Trigger: push to PM main touching
      plans/active/*.plan.md. (2) Read the changed plan file, extract name + overview + first 3 todos. (3) Send
      Telegram: "📋 Plan ready for review: [plan-name]\n
          Overview: [first 200 chars]\nTodos: [count] pending\n
          Review: [link to file on GitHub]\nApprove with: /approve-plan [name]"
      (4) Human replies /approve-plan [name] → plan-approval.yml marks plan
          status: approved in frontmatter. Agents check status: approved before
          implementing plan todos.
      This closes the governance loop: no agent starts implementing until human has explicitly reviewed the plan.
    status: pending

  - id: add-tg-merge-approval-gate
    content: >
      Second human gate: all agent-opened PRs currently can auto-merge once quality gates pass. For conflict resolution
      PRs, humans must review. But for other agent PRs (codex sync, rules alignment, semver bumps) there is no explicit
      approval gate. Fix: (1) For conflict-resolution PRs: tg_conflict_done already fires with PR
          URL. Explicitly note in the Telegram message: "PR will NOT auto-merge.
          Review and approve in GitHub."
      (2) For other agent PRs (codex-sync-agent, rules-alignment-agent): add a
          Telegram message on PR creation: "🔀 Agent PR opened: [title]\n
          [PR URL]\nApprove merge with: /approve-merge [PR#]"
      (3) Implement /approve-merge handler (PR comment workflow) that sets
          auto-merge on the PR when human sends this.
      Net effect: two mandatory human touchpoints for any agent-driven change:
        Gate 1: /approve-plan [name] — before implementation starts
        Gate 2: review PR in GitHub or /approve-merge [PR#] — before code lands
    status: pending

  # ── Testing ──────────────────────────────────────────────────────────────

  - id: test-p0-remediation
    content: >
      E2E test each P0 fix using admin sync scripts or workflow_dispatch: (a) Rollback: Force a SIT failure using admin
      script (push known-bad
          commit to staging). Verify GH Issue opened. Verify staging unlocked.
      (b) Cascade cycle: Edit workspace-manifest.json on a test branch to add
          a cycle (repo A → B → A). Run validate-manifest-dag.py, verify it
          exits non-zero with cycle description.
      (c) SHA pinning: Push a [skip ci] constraint commit during a running SIT
          (using admin merge script). Verify staging_commits captures the full
          SHA set including the constraint commit, or that promotion is deferred.
      (d) Semver trigger: After fix, push feat: to a T2 staging. Verify version
          bump fires on staging push, not on subsequent main push. Verify only
          one bump (not two).
      Acceptance: all 4 scenarios behave correctly with no manual recovery needed.
    status: pending

  - id: test-plan-cascade
    content: >
      E2E test the full plan-driven governance loop: (1) Create a new test plan in plans/active/ (minimal, 1 todo). (2)
      Verify: push to PM main → manifest-sync fires → codex updated. (3) Verify: rules-alignment-agent fires → cursor
      rule created for the
          new plan constraint.
      (4) Verify: Telegram plan-ready notification received with correct content. (5) Send /approve-plan
      [test-plan-name] via Telegram → verify plan
          frontmatter updated to status: approved.
      (6) Create a deliberate merge conflict in a test repo. (7) Verify: conflict-resolution-agent fires, reads active
      plans,
          references the test plan in its resolution PR body.
      (8) Verify: tg_merge_ready notification fires with PR URL. (9) Send /approve-merge [PR#] → verify PR auto-merges.
      Acceptance: full loop works end-to-end with exactly two human TG actions.
    status: pending

  - id: register-ssot-index
    content: >
      Add this plan to unified-trading-codex/00-SSOT-INDEX.md in the Plans section (after cicd_e2e_test_plan_2026_03_13
      row). Entry format: | cicd_audit_remediation_2026_03_13.plan.md | CI/CD audit P0/P1/P2 remediation + plan-driven
      governance | unified-trading-pm/plans/active/ |
    status: pending

isProject: false
---

# CI/CD Pipeline Audit Remediation

**Context:** Full audit performed 2026-03-13 against the live pipeline implementation. 22 issues found across P0/P1/P2.
This plan drives remediation of all critical and major issues, plus adds the plan-driven governance model to close the
human oversight loop.

## Governance Model (the central insight)

The pipeline's correctness depends on agents having the RIGHT context. That context is the **active plans**:

```
Plan created (human or agent)
  → codex-sync-agent updates unified-trading-codex (source of truth)
  → rules-alignment-agent creates cursor rules from plan constraints
  → Telegram: "📋 Plan ready for review" [Gate 1: human approves plan]
  → Agent reads: active plans + codex + AGENTS.md + cursor rules
  → Agent implements → opens PR
  → Telegram: "🔀 Agent PR ready" [Gate 2: human approves merge]
  → PR merges → staging → SIT → main
```

**Only two human actions in the entire flow:** approve plan + approve merge. Everything else is automated, but nothing
agent-driven bypasses these gates.

## Audit Findings Summary

| Priority                    | Count | Status                                      |
| --------------------------- | ----- | ------------------------------------------- |
| P0 (production correctness) | 5     | all pending                                 |
| P1 (silent failures)        | 4     | all pending                                 |
| P2 (logic/design)           | 8     | diagram fixes immediate, code fixes tracked |
| Diagram SSOT                | 5     | immediate (unblocked)                       |

See full audit in session notes (2026-03-13). Top risk: workspace-manifest.json as a git-committed distributed state
store — concurrent writes create race conditions. Long-term mitigation: move to a proper distributed lock (tracked
separately).

## Diagram Auto-Regeneration

After `diagram-regen-in-quickmerge` is complete, the following is guaranteed:

- `cicd-pipeline-definition.yaml` = canonical SSOT (human-edited)
- `CI-CD-PIPELINE.svg` + `CI-CD-PIPELINE.html` = generated, never hand-edited
- Regeneration happens on every PM `quickmerge` pass that changes `.yaml` or `.py`
- The diagram is therefore always in sync with the documented pipeline

## References

- `plans/active/cicd_e2e_test_plan_2026_03_13.plan.md` — test plan for all fixes
- `plans/active/conflict_resolution_agent_2026_03_13.plan.md` — agent implementation
- `plans/active/full_autonomous_agent_ci.plan.md` — semver-agent fix (dependency)
- `docs/repo-management/cicd-pipeline-definition.yaml` — diagram SSOT
- `scripts/generate-cicd-diagram.py` — diagram generator
- `docs/repo-management/CI-CD-PIPELINE.html` — live interactive diagram
